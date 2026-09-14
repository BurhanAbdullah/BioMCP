"""BioMCP diagnostics.

The doctor checks the same registry metadata used by installation and launch.
It reports executable entry points, Python dependencies and declared runtime
configuration without executing scientific workloads.
"""
from __future__ import annotations

import importlib.util
import os
import shutil

from .registry import get_server, installable_servers


def _missing_dependencies(entry: dict) -> list[str]:
    missing: list[str] = []
    for module in entry.get("dependencies", []):
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def _missing_configuration(entry: dict) -> list[str]:
    return [key for key in entry.get("config", []) if not os.getenv(key)]


def diagnose(name: str | None = None) -> list[dict[str, object]]:
    entries = installable_servers()
    if name:
        entries = [get_server(name)]
        if not entries[0].get("installable"):
            raise SystemExit(f"Unknown or non-installable server: {name}")

    results: list[dict[str, object]] = []
    for entry in entries:
        command = str(entry["command"])
        command_path = shutil.which(command)
        missing_dependencies = _missing_dependencies(entry)
        missing_configuration = _missing_configuration(entry)
        results.append(
            {
                "name": entry["name"],
                "command": command,
                "command_path": command_path,
                "missing_dependencies": missing_dependencies,
                "missing_configuration": missing_configuration,
                "ok": bool(command_path) and not missing_dependencies,
            }
        )
    return results


def run_doctor(name: str | None = None) -> int:
    failures = 0
    for result in diagnose(name):
        ok = bool(result["ok"])
        status = "OK" if ok else "MISSING"
        detail = str(result["command"])
        missing = list(result["missing_dependencies"])
        config = list(result["missing_configuration"])
        if missing:
            detail += f" | dependencies: {', '.join(missing)}"
        if config:
            detail += f" | config: {', '.join(config)}"
        print(f"{str(result['name']):18} {status:8} {detail}")
        failures += int(not ok)
    return 1 if failures else 0
