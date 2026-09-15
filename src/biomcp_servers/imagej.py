"""ImageJ/Fiji bridge for BioMCP."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from biomcp.http import create_streamable_http_app


def _executable() -> str | None:
    return os.getenv("BIOMCP_IMAGEJ_EXECUTABLE") or os.getenv("IMAGEJ_EXECUTABLE")


def _child_env() -> dict[str, str]:
    """Build a minimal child environment without inheriting host state."""
    allowed = {
        "PATH",
        "HOME",
        "TMPDIR",
        "TMP",
        "TEMP",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "USER",
        "LOGNAME",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "JAVA_HOME",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def _run_macro(binary: str, image: Path, macro: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        p = subprocess.run(
            [binary, "--headless", "--run", str(macro), str(image)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=_child_env(),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return {
            "returncode": None,
            "timed_out": True,
            "stdout": str(stdout)[-12000:],
            "stderr": str(stderr)[-12000:],
        }
    return {
        "returncode": p.returncode,
        "timed_out": False,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-12000:],
    }


def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-ImageJ")

    @mcp.tool()
    def imagej_status() -> dict[str, Any]:
        """Return ImageJ/Fiji local configuration status."""
        path = _executable()
        return {"configured": bool(path), "executable": path}

    @mcp.tool()
    def run_macro(image_path: str, macro_path: str, timeout_seconds: int = 120) -> dict[str, Any]:
        """Run an explicitly supplied ImageJ macro without invoking a shell."""
        binary = _executable()
        if not binary:
            raise RuntimeError("Set BIOMCP_IMAGEJ_EXECUTABLE")
        image = Path(image_path).expanduser().resolve()
        macro = Path(macro_path).expanduser().resolve()
        if not image.is_file():
            raise FileNotFoundError(str(image))
        if not macro.is_file():
            raise FileNotFoundError(str(macro))
        if not 1 <= timeout_seconds <= 900:
            raise ValueError("timeout_seconds must be 1..900")
        return _run_macro(binary, image, macro, timeout_seconds)
    return mcp


def create_http_app() -> Any:
    """Create the hardened Streamable HTTP app for this server."""
    return create_streamable_http_app(create_server())


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
