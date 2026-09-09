"""BioMCP diagnostics."""
from __future__ import annotations

import shutil

from .registry import installable_servers


def run_doctor(name: str | None = None) -> int:
    entries = installable_servers()
    if name:
        entries = [entry for entry in entries if entry["name"] == name]
        if not entries:
            raise SystemExit(f"Unknown or non-installable server: {name}")
    failures = 0
    for entry in entries:
        command = str(entry["command"])
        found = shutil.which(command)
        status = "OK" if found else "MISSING"
        print(f"{entry['name']:18} {status:8} {command}")
        failures += int(found is None)
    return 1 if failures else 0
