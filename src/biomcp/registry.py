"""Machine-readable BioMCP server registry with installed-package fallback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_REGISTRY = Path(__file__).resolve().parents[2] / "biomcp" / "registry.json"
_PACKAGED_REGISTRY = Path(__file__).with_name("registry.json")
REGISTRY_PATH = _REPO_REGISTRY if _REPO_REGISTRY.is_file() else _PACKAGED_REGISTRY


def load_registry(path: Path | None = None) -> dict[str, Any]:
    target = path or REGISTRY_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("product") != "BioMCP" or not isinstance(data.get("servers"), list):
        raise ValueError("BioMCP registry must contain product=BioMCP and a servers list")
    names: list[str] = []
    for entry in data["servers"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str) or not entry["name"].strip():
            raise ValueError("BioMCP registry server entries require a non-empty name")
        name = entry["name"]
        if name in names:
            raise ValueError(f"BioMCP registry contains duplicate server name: {name}")
        names.append(name)

        installable = entry.get("installable") is True
        external = entry.get("external") is True
        command = entry.get("command")
        if installable and external:
            raise ValueError(f"Server {name} cannot be both installable and external")
        if installable and (not isinstance(command, str) or not command.strip()):
            raise ValueError(f"Installable server {name} requires a non-empty command")

        # Installable and explicitly external entries describe an executable
        # MCP boundary and therefore must declare at least one transport.
        # Planned/non-installable entries may intentionally omit transport
        # until their adapter contract is defined; they must not be made
        # executable merely to satisfy registry validation.
        transport = entry.get("transport")
        if (installable or external) and (
            not isinstance(transport, list)
            or not transport
            or not all(isinstance(x, str) and x.strip() for x in transport)
        ):
            raise ValueError(f"Server {name} requires a non-empty transport list")
    return data


def get_server(name: str) -> dict[str, Any]:
    for entry in load_registry()["servers"]:
        if entry.get("name") == name:
            return entry
    raise KeyError(f"Unknown BioMCP server: {name}")


def installable_servers() -> list[dict[str, Any]]:
    return [x for x in load_registry()["servers"] if x.get("installable") is True]
