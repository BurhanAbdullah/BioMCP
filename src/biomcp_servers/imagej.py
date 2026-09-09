"""ImageJ/Fiji bridge for BioMCP."""
from __future__ import annotations
import os, subprocess
from pathlib import Path
from typing import Any
from mcp.server.mcpserver import MCPServer

def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-ImageJ")
    exe = lambda: os.getenv("BIOMCP_IMAGEJ_EXECUTABLE") or os.getenv("IMAGEJ_EXECUTABLE")
    @mcp.tool()
    def imagej_status() -> dict[str, Any]:
        """Return ImageJ/Fiji local configuration status."""
        path = exe(); return {"configured": bool(path), "executable": path}
    @mcp.tool()
    def run_macro(image_path: str, macro_path: str, timeout_seconds: int = 120) -> dict[str, Any]:
        """Run an explicitly supplied ImageJ macro without invoking a shell."""
        binary = exe()
        if not binary: raise RuntimeError("Set BIOMCP_IMAGEJ_EXECUTABLE")
        image = Path(image_path).expanduser().resolve(); macro = Path(macro_path).expanduser().resolve()
        if not image.is_file(): raise FileNotFoundError(str(image))
        if not macro.is_file(): raise FileNotFoundError(str(macro))
        if not 1 <= timeout_seconds <= 900: raise ValueError("timeout_seconds must be 1..900")
        p = subprocess.run([binary, "--headless", "--run", str(macro), str(image)], capture_output=True, text=True, timeout=timeout_seconds, check=False)
        return {"returncode": p.returncode, "stdout": p.stdout[-12000:], "stderr": p.stderr[-12000:]}
    return mcp

def main() -> None:
    create_server().run()

if __name__ == "__main__": main()
