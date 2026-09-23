"""BioMCP diagnostics.

The doctor checks the same registry metadata used by installation and launch.
It reports executable entry points, Python dependencies and declared runtime
configuration without executing scientific workloads.
"""
from __future__ import annotations

import importlib.metadata
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


def _installed_artifact(entry: dict, command_path: str | None) -> dict[str, object]:
    """Verify that the registry command belongs to the installed distribution."""
    distribution_name = str(entry.get("distribution", "biomcp"))
    command = str(entry["command"])
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return {
            "distribution": distribution_name,
            "version": None,
            "entry_point": False,
            "command_path": command_path,
            "ok": False,
        }

    console_scripts = {
        item.name: item.value
        for item in distribution.entry_points
        if item.group == "console_scripts"
    }
    return {
        "distribution": distribution.metadata["Name"] or distribution_name,
        "version": distribution.version,
        "entry_point": command in console_scripts,
        "command_path": command_path,
        "ok": bool(command_path) and command in console_scripts,
    }


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
        artifact = _installed_artifact(entry, command_path)
        results.append(
            {
                "name": entry["name"],
                "lifecycle_status": entry["status"],
                "command": command,
                "command_path": command_path,
                "missing_dependencies": missing_dependencies,
                "missing_configuration": missing_configuration,
                "artifact": artifact,
                "ok": bool(artifact["ok"]) and not missing_dependencies and not missing_configuration,
            }
        )
    return results


def run_doctor(name: str | None = None) -> int:
    failures = 0
    for result in diagnose(name):
        ok = bool(result["ok"])
        status = "OK" if ok else "MISSING"
        lifecycle = str(result["lifecycle_status"])
        detail = f"{result['command']} | lifecycle: {lifecycle}"
        artifact = dict(result["artifact"])
        if not artifact["ok"]:
            detail += " | artifact: distribution/entry point unavailable"
        missing = list(result["missing_dependencies"])
        config = list(result["missing_configuration"])
        if missing:
            detail += f" | dependencies: {', '.join(missing)}"
        if config:
            detail += f" | config: {', '.join(config)}"
        print(f"{str(result['name']):18} {status:8} {detail}")
        failures += int(not ok)
    return 1 if failures else 0
