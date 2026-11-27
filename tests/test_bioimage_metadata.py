"""Integration tests for OME microscopy metadata extraction."""
import numpy as np
import pytest
import tifffile

from biomcp_servers.bioimage import (
    _ome_tiff_metadata,
    _ome_zarr_metadata,
    _require_image_path,
)


def test_ome_tiff_metadata_preserves_axes_channels_and_pixel_size(tmp_path):
    path = tmp_path / "channels.ome.tif"
    tifffile.imwrite(
        path,
        np.zeros((2, 16, 20), dtype=np.uint16),
        ome=True,
        metadata={
            "axes": "CYX",
            "Channel": {"Name": ["DAPI", "GFP"]},
            "PhysicalSizeX": 0.25,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": 0.25,
            "PhysicalSizeYUnit": "µm",
        },
    )

    metadata = _ome_tiff_metadata(path)

    assert metadata.axes == "CYX"
    assert metadata.shape == (2, 16, 20)
    assert metadata.dtype == "uint16"
    assert metadata.channel_names == ("DAPI", "GFP")
    assert metadata.physical_sizes["X"].value == pytest.approx(0.25)
    assert metadata.physical_sizes["Y"].unit == "µm"
    assert metadata.acquisition["ome"] is True


def test_ome_zarr_metadata_reads_ngff_axes_and_scale(tmp_path):
    zarr = pytest.importorskip("zarr")
    path = tmp_path / "sample.ome.zarr"
    group = zarr.open_group(str(path), mode="w")
    group.create_dataset(
        "0",
        data=np.zeros((2, 16, 20), dtype=np.uint16),
        shape=(2, 16, 20),
    )
    group.attrs["multiscales"] = [{
        "version": "0.4",
        "axes": [
            {"name": "c"},
            {"name": "y", "unit": "micrometer"},
            {"name": "x", "unit": "micrometer"},
        ],
        "datasets": [{
            "path": "0",
            "coordinateTransformations": [
                {"type": "scale", "scale": [1.0, 0.5, 0.25]}
            ],
        }],
    }]
    group.attrs["omero"] = {
        "channels": [
            {"label": {"name": "DAPI"}},
            {"label": {"name": "GFP"}},
        ]
    }

    metadata = _ome_zarr_metadata(path)

    assert metadata.axes == "CYX"
    assert metadata.shape == (2, 16, 20)
    assert metadata.channel_names == ("DAPI", "GFP")
    assert metadata.physical_sizes["Y"].value == pytest.approx(0.5)
    assert metadata.physical_sizes["X"].unit == "micrometer"
    assert metadata.acquisition["format"] == "ome-zarr"


def test_image_dataset_path_enforces_size_limit(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset.zarr"
    dataset.mkdir()
    (dataset / ".zattrs").write_text("12345", encoding="utf-8")
    monkeypatch.setenv("BIOMCP_MAX_INPUT_BYTES", "4")

    with pytest.raises(ValueError, match="exceeds BIOMCP_MAX_INPUT_BYTES"):
        _require_image_path(str(dataset))
