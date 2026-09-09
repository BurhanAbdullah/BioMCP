"""Launch BioMCP registered servers over stdio."""
from __future__ import annotations

import shutil
import subprocess

from .registry import get_server


def launch(name: str, extra: list[str] | None = None) -> int:
    entry = get_server(name)
    if not entry.get("installable"):
        raise RuntimeError(f"{name} is not installable (status: {entry.get('status')})")
    command = str(entry["command"])
    if shutil.which(command) is None:
        raise RuntimeError(f"Command not found: {command}")
    return subprocess.run([command, *(extra or [])], check=False).returncode
