"""BioMCP bioimage server: deterministic local-image primitives."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from mcp.server.mcpserver import MCPServer

def _require_path(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Image file not found: {p}")
    limit = int(os.getenv("BIOMCP_MAX_INPUT_BYTES", str(2 * 1024**3)))
    if p.stat().st_size > limit:
        raise ValueError("Input image exceeds BIOMCP_MAX_INPUT_BYTES")
    return p

def _load_image(path: Path):
    try:
        import numpy as np
        import tifffile
    except ImportError as exc:
        raise RuntimeError("Install with: pip install 'biomcp[bioimage]'") from exc
    return np.asarray(tifffile.imread(path))

def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-BioImage")

    @mcp.tool()
    def inspect_image(path: str) -> dict[str, Any]:
        """Inspect a local TIFF image without modifying it."""
        p = _require_path(path); a = _load_image(p)
        return {"path": str(p), "shape": list(a.shape), "dtype": str(a.dtype), "ndim": int(a.ndim), "min": float(a.min()), "max": float(a.max()), "mean": float(a.mean()), "std": float(a.std())}

    @mcp.tool()
    def intensity_summary(path: str) -> dict[str, Any]:
        """Return robust intensity percentiles for local image QA."""
        p = _require_path(path); a = _load_image(p)
        import numpy as np
        values = np.percentile(a.astype(np.float64, copy=False).ravel(), [1,5,25,50,75,95,99])
        return {"path": str(p), "percentiles": {str(k): float(v) for k,v in zip([1,5,25,50,75,95,99], values)}}

    @mcp.tool()
    def threshold_image(path: str, method: str = "otsu") -> dict[str, Any]:
        """Compute an Otsu threshold summary without persisting data."""
        if method.lower() != "otsu":
            raise ValueError("Only method='otsu' is currently implemented")
        p = _require_path(path); a = _load_image(p)
        try:
            from skimage.filters import threshold_otsu
        except ImportError as exc:
            raise RuntimeError("Install with: pip install 'biomcp[bioimage]'") from exc
        import numpy as np
        t = float(threshold_otsu(a)); mask = np.asarray(a) > t
        return {"path": str(p), "method": "otsu", "threshold": t, "foreground_fraction": float(mask.mean()), "shape": list(mask.shape)}
    return mcp

def main() -> None:
    create_server().run()

if __name__ == "__main__":
    main()
