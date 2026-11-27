"""BioMCP bioimage server: bounded local microscopy inspection primitives."""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from bioio.image import ImageMetadata, PhysicalSize
from biomcp.http import create_streamable_http_app


def _require_path(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Image file not found: {p}")
    limit = int(os.getenv("BIOMCP_MAX_INPUT_BYTES", str(512 * 1024**2)))
    if limit <= 0:
        raise ValueError("BIOMCP_MAX_INPUT_BYTES must be positive")
    if p.stat().st_size > limit:
        raise ValueError("Input image exceeds BIOMCP_MAX_INPUT_BYTES")
    return p


def _require_image_path(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file() and not p.is_dir():
        raise FileNotFoundError(f"Image dataset not found: {p}")
    limit = int(os.getenv("BIOMCP_MAX_INPUT_BYTES", str(512 * 1024**2)))
    if limit <= 0:
        raise ValueError("BIOMCP_MAX_INPUT_BYTES must be positive")
    if p.is_file():
        total = p.stat().st_size
    else:
        total = 0
        for child in p.rglob("*"):
            if child.is_symlink():
                raise ValueError("Image dataset must not contain symbolic links")
            if child.is_file():
                total += child.stat().st_size
                if total > limit:
                    raise ValueError("Input image dataset exceeds BIOMCP_MAX_INPUT_BYTES")
    if total > limit:
        raise ValueError("Input image exceeds BIOMCP_MAX_INPUT_BYTES")
    return p


def _load_image(path: Path):
    try:
        import numpy as np
        import tifffile
    except ImportError as exc:
        raise RuntimeError("Install with: pip install 'biomcp[bioimage]'") from exc

    max_elements = int(os.getenv("BIOMCP_MAX_IMAGE_ELEMENTS", str(100_000_000)))
    if max_elements <= 0:
        raise ValueError("BIOMCP_MAX_IMAGE_ELEMENTS must be positive")
    max_decoded_bytes = int(
        os.getenv("BIOMCP_MAX_DECODED_BYTES", str(512 * 1024**2))
    )
    if max_decoded_bytes <= 0:
        raise ValueError("BIOMCP_MAX_DECODED_BYTES must be positive")

    with tifffile.TiffFile(path) as tif:
        series = tif.series[0]
        shape = series.shape
        elements = 1
        for dimension in shape:
            elements *= int(dimension)
        if elements > max_elements:
            raise ValueError(
                f"Image contains {elements} elements; exceeds "
                "BIOMCP_MAX_IMAGE_ELEMENTS"
            )
        dtype = np.dtype(series.dtype)
        decoded_bytes = elements * dtype.itemsize
        if decoded_bytes > max_decoded_bytes:
            raise ValueError(
                f"Decoded image requires {decoded_bytes} bytes; exceeds "
                "BIOMCP_MAX_DECODED_BYTES"
            )

    return np.asarray(tifffile.imread(path))


def _ome_tiff_metadata(path: Path) -> ImageMetadata:
    try:
        import tifffile
    except ImportError as exc:
        raise RuntimeError("Install with: pip install 'biomcp[bioimage]'") from exc

    with tifffile.TiffFile(path) as tif:
        series = tif.series[0]
        axes = str(series.axes)
        shape = tuple(int(value) for value in series.shape)
        dtype = str(series.dtype)
        channels: list[str] = []
        sizes: dict[str, PhysicalSize] = {}
        acquisition: dict[str, Any] = {"format": "tiff", "ome": bool(tif.ome_metadata)}
        if tif.ome_metadata:
            root = ET.fromstring(tif.ome_metadata)
            pixels = next((node for node in root.iter() if node.tag.endswith("Pixels")), None)
            if pixels is not None:
                for axis in "XYZ":
                    value = pixels.attrib.get(f"PhysicalSize{axis}")
                    if value is not None:
                        unit = pixels.attrib.get(f"PhysicalSize{axis}Unit", "µm")
                        sizes[axis] = PhysicalSize(float(value), unit)
                channels = [
                    node.attrib["Name"]
                    for node in pixels
                    if node.tag.endswith("Channel") and node.attrib.get("Name")
                ]
                acquisition.update({
                    key: pixels.attrib[key]
                    for key in ("DimensionOrder", "Type", "SignificantBits")
                    if key in pixels.attrib
                })
        return ImageMetadata(
            axes=axes,
            shape=shape,
            dtype=dtype,
            channel_names=tuple(channels),
            physical_sizes=sizes,
            acquisition=acquisition,
        )


def _ome_zarr_metadata(path: Path) -> ImageMetadata:
    try:
        import zarr
    except ImportError as exc:
        raise RuntimeError(
            "Install OME-Zarr support with: pip install 'biomcp[bioimage]'"
        ) from exc

    group = zarr.open_group(str(path), mode="r")
    attrs = dict(group.attrs)
    multiscales = attrs.get("multiscales")
    if not isinstance(multiscales, list) or not multiscales:
        raise ValueError("OME-Zarr dataset is missing multiscales metadata")
    scale = multiscales[0]
    datasets = scale.get("datasets", [])
    if not datasets:
        raise ValueError("OME-Zarr multiscales metadata has no datasets")
    dataset_path = datasets[0].get("path")
    if not isinstance(dataset_path, str) or not dataset_path:
        raise ValueError("OME-Zarr dataset path is invalid")
    array = group[dataset_path]
    raw_axes = scale.get("axes", [])
    axes = "".join(
        item if isinstance(item, str) else item.get("name", "")
        for item in raw_axes
    )
    transformations = datasets[0].get("coordinateTransformations", [])
    scale_values = next(
        (item.get("scale") for item in transformations if item.get("type") == "scale"),
        None,
    )
    sizes: dict[str, PhysicalSize] = {}
    if isinstance(scale_values, list) and len(scale_values) == len(axes):
        for axis, value, axis_meta in zip(axes, scale_values, raw_axes):
            if axis in "XYZ" and value is not None:
                unit = axis_meta.get("unit", "pixel") if isinstance(axis_meta, dict) else "pixel"
                sizes[axis] = PhysicalSize(float(value), unit)
    omero = attrs.get("omero", {})
    channels = tuple(
        item.get("label", {}).get("name", "")
        for item in omero.get("channels", [])
        if item.get("label", {}).get("name")
    )
    return ImageMetadata(
        axes=axes,
        shape=tuple(int(value) for value in array.shape),
        dtype=str(array.dtype),
        channel_names=channels,
        physical_sizes=sizes,
        acquisition={"format": "ome-zarr", "version": scale.get("version")},
    )


def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-BioImage")

    @mcp.tool()
    def inspect_image(path: str) -> dict[str, Any]:
        """Inspect a local TIFF image without modifying it."""
        p = _require_path(path)
        a = _load_image(p)
        return {
            "path": str(p),
            "shape": list(a.shape),
            "dtype": str(a.dtype),
            "ndim": int(a.ndim),
            "min": float(a.min()),
            "max": float(a.max()),
            "mean": float(a.mean()),
            "std": float(a.std()),
        }

    @mcp.tool()
    def inspect_image_metadata(path: str) -> dict[str, Any]:
        """Read axes, channels and physical calibration from TIFF or OME-Zarr."""
        p = _require_image_path(path)
        metadata = _ome_zarr_metadata(p) if p.is_dir() else _ome_tiff_metadata(p)
        return {"path": str(p), **metadata.to_dict()}

    @mcp.tool()
    def intensity_summary(path: str) -> dict[str, Any]:
        """Return robust intensity percentiles for local image QA."""
        p = _require_path(path)
        a = _load_image(p)
        import numpy as np

        values = np.percentile(
            a.astype(np.float64, copy=False).ravel(),
            [1, 5, 25, 50, 75, 95, 99],
        )
        return {
            "path": str(p),
            "percentiles": {
                str(k): float(v)
                for k, v in zip([1, 5, 25, 50, 75, 95, 99], values)
            },
        }

    @mcp.tool()
    def threshold_image(path: str, method: str = "otsu") -> dict[str, Any]:
        """Compute an Otsu threshold summary without persisting data."""
        if method.lower() != "otsu":
            raise ValueError("Only method='otsu' is currently implemented")
        p = _require_path(path)
        a = _load_image(p)
        try:
            from skimage.filters import threshold_otsu
        except ImportError as exc:
            raise RuntimeError("Install with: pip install 'biomcp[bioimage]'") from exc
        import numpy as np

        t = float(threshold_otsu(a))
        mask = np.asarray(a) > t
        return {
            "path": str(p),
            "method": "otsu",
            "threshold": t,
            "foreground_fraction": float(mask.mean()),
            "shape": list(mask.shape),
        }
    return mcp


def create_http_app() -> Any:
    """Create the hardened Streamable HTTP app for this server."""
    return create_streamable_http_app(create_server())


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
