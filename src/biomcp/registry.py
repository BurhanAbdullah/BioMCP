"""Machine readable BioMCP server registry and contract validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_REGISTRY = Path(__file__).resolve().parents[2] / "biomcp" / "registry.json"
_PACKAGED_REGISTRY = Path(__file__).with_name("registry.json")
REGISTRY_PATH = _REPO_REGISTRY if _REPO_REGISTRY.is_file() else _PACKAGED_REGISTRY

_ALLOWED_STATUS = {"planned", "experimental", "validated", "deprecated"}
_ALLOWED_TRANSPORTS = {"stdio", "streamable-http", "sse"}


def load_registry(path: Path | None = None) -> dict[str, Any]:
    target = path or REGISTRY_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("product") != "BioMCP" or not isinstance(data.get("servers"), list):
        raise ValueError("BioMCP registry must contain product=BioMCP and a servers list")
    if not isinstance(data.get("schema_version"), str):
        raise ValueError("BioMCP registry requires a string schema_version")

    names: set[str] = set()
    for entry in data["servers"]:
        if not isinstance(entry, dict):
            raise ValueError("BioMCP registry entries must be objects")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("BioMCP registry server entries require a non-empty name")
        if name in names:
            raise ValueError(f"BioMCP registry contains duplicate server name: {name}")
        names.add(name)

        status = entry.get("status")
        if status not in _ALLOWED_STATUS:
            raise ValueError(f"Server {name} has invalid lifecycle status: {status!r}")

        installable = entry.get("installable") is True
        external = entry.get("external") is True
        command = entry.get("command")
        if installable and external:
            raise ValueError(f"Server {name} cannot be both installable and external")
        if installable and (not isinstance(command, str) or not command.strip()):
            raise ValueError(f"Installable server {name} requires a non-empty command")
        if installable and status not in {"experimental", "validated"}:
            raise ValueError(f"Installable server {name} must be experimental or validated")
        if external and status != "validated":
            raise ValueError(f"External server {name} must be validated")
        if status == "planned" and installable:
            raise ValueError(f"Planned server {name} cannot be installable")

        transport = entry.get("transport")
        if installable or external:
            if not isinstance(transport, list) or not transport:
                raise ValueError(f"Server {name} requires a non-empty transport list")
            if not all(isinstance(x, str) and x in _ALLOWED_TRANSPORTS for x in transport):
                raise ValueError(f"Server {name} contains an unsupported transport")

        tools = entry.get("tools", [])
        if not isinstance(tools, list) or not all(isinstance(tool, str) and tool.strip() for tool in tools):
            raise ValueError(f"Server {name} tools must be a list of non-empty strings")

        dependencies = entry.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(isinstance(dep, str) and dep.strip() for dep in dependencies):
            raise ValueError(f"Server {name} dependencies must be a list of import names")

        config = entry.get("config", [])
        if not isinstance(config, list) or not all(isinstance(key, str) and key.strip() for key in config):
            raise ValueError(f"Server {name} config must be a list of environment/config keys")

        if installable:
            extra = entry.get("package_extra")
            distribution = entry.get("distribution", data.get("distribution", "biomcp"))
            if not isinstance(extra, str) or not extra.strip():
                raise ValueError(f"Installable server {name} requires package_extra")
            if not isinstance(distribution, str) or not distribution.strip():
                raise ValueError(f"Installable server {name} requires distribution")

    return data


def get_server(name: str) -> dict[str, Any]:
    for entry in load_registry()["servers"]:
        if entry.get("name") == name:
            return entry
    raise KeyError(f"Unknown BioMCP server: {name}")


def installable_servers() -> list[dict[str, Any]]:
    return [entry for entry in load_registry()["servers"] if entry.get("installable") is True]
