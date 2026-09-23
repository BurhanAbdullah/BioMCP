"""BioMCP diagnostics.

The doctor checks the same registry metadata used by installation and launch.
It reports executable entry points, Python dependencies and declared runtime
configuration without executing scientific workloads.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import os
import shutil
from pathlib import Path

from .registry import get_server, installable_servers
from .transport import resolve_transport_entry


def _missing_dependencies(entry: dict) -> list[str]:
    missing: list[str] = []
    for module in entry.get("dependencies", []):
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def _missing_configuration(entry: dict) -> list[str]:
    return [key for key in entry.get("config", []) if not os.getenv(key)]


def _installed_artifact(entry: dict, command_path: str | None) -> dict[str, object]:
    """Verify that the registry command resolves to a real installed entry point."""
    distribution_name = str(entry.get("distribution", "biomcp"))
    command = str(entry["command"])
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return {
            "distribution": distribution_name,
            "version": None,
            "entry_point": False,
            "entry_point_value": None,
            "module_importable": False,
            "command_path": command_path,
            "ok": False,
        }

    console_scripts = {
        item.name: item.value
        for item in distribution.entry_points
        if item.group == "console_scripts"
    }
    entry_point_value = console_scripts.get(command)
    module_importable = False
    if isinstance(entry_point_value, str) and ":" in entry_point_value:
        module_name = entry_point_value.split(":", 1)[0].strip()
        if module_name:
            try:
                module_importable = importlib.util.find_spec(module_name) is not None
            except (ImportError, ModuleNotFoundError, ValueError):
                module_importable = False

    return {
        "distribution": distribution.metadata["Name"] or distribution_name,
        "version": distribution.version,
        "entry_point": command in console_scripts,
        "entry_point_value": entry_point_value,
        "module_importable": module_importable,
        "command_path": command_path,
        "ok": bool(command_path) and command in console_scripts and module_importable,
    }


def _client_config_status(entry: dict) -> dict[str, object]:
    """Check an existing generic client config against current registry truth.

    A missing config is informational because ``doctor`` is also used before
    installation. Once a generic config exists, however, drift is a readiness
    failure: the client would otherwise launch a stale registry configuration.
    """
    path = Path.home() / ".config" / "biomcp" / "mcp.json"
    if not path.exists():
        return {"path": str(path), "status": "missing", "ok": True}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"path": str(path), "status": "invalid", "error": str(exc), "ok": False}

    block = data.get("mcpServers") if isinstance(data, dict) else None
    key = f"biomcp_{entry['name']}"
    if not isinstance(block, dict) or key not in block:
        return {"path": str(path), "status": "missing-entry", "server": key, "ok": True}

    transport = resolve_transport_entry(entry, client="default")
    if transport == "stdio":
        expected = {"command": entry["command"], "args": list(entry.get("args", []))}
    elif transport == "streamable-http":
        endpoint = entry.get("endpoint")
        expected = {"url": endpoint.strip()} if isinstance(endpoint, str) and endpoint.strip() else None
    else:
        expected = None

    if expected is None:
        return {"path": str(path), "status": "unsupported", "transport": transport, "ok": False}
    if block.get(key) != expected:
        return {"path": str(path), "status": "drift", "server": key, "expected": expected, "actual": block.get(key), "ok": False}
    return {"path": str(path), "status": "match", "server": key, "transport": transport, "ok": True}


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
        transport_error: str | None = None
        try:
            resolved_transport = resolve_transport_entry(entry, client="default")
        except ValueError as exc:
            resolved_transport = None
            transport_error = str(exc)
        client_config = _client_config_status(entry)
        results.append(
            {
                "name": entry["name"],
                "lifecycle_status": entry["status"],
                "transport": resolved_transport,
                "transport_error": transport_error,
                "endpoint": entry.get("endpoint"),
                "command": command,
                "command_path": command_path,
                "missing_dependencies": missing_dependencies,
                "missing_configuration": missing_configuration,
                "artifact": artifact,
                "client_config": client_config,
                "ok": bool(artifact["ok"])
                and not missing_dependencies
                and not missing_configuration
                and transport_error is None
                and bool(client_config["ok"]),
            }
        )
    return results


def run_doctor(name: str | None = None) -> int:
    failures = 0
    for result in diagnose(name):
        ok = bool(result["ok"])
        status = "OK" if ok else "MISSING"
        lifecycle = str(result["lifecycle_status"])
        transport = str(result["transport"] or "invalid")
        detail = f"{result['command']} | lifecycle: {lifecycle} | transport: {transport}"
        endpoint = result.get("endpoint")
        if endpoint:
            detail += f" | endpoint: {endpoint}"
        if result.get("transport_error"):
            detail += f" | transport error: {result['transport_error']}"
        artifact = dict(result["artifact"])
        if not artifact["ok"]:
            detail += " | artifact: distribution/entry point unavailable"
        client_config = dict(result["client_config"])
        if client_config["status"] in {"drift", "invalid", "unsupported"}:
            detail += f" | client config: {client_config['status']}"
        missing = list(result["missing_dependencies"])
        config = list(result["missing_configuration"])
        if missing:
            detail += f" | dependencies: {', '.join(missing)}"
        if config:
            detail += f" | config: {', '.join(config)}"
        print(f"{str(result['name']):18} {status:8} {detail}")
        failures += int(not ok)
    return 1 if failures else 0
