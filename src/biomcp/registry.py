"""Machine-readable BioMCP server registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "biomcp" / "registry.json"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("servers"), list):
        raise ValueError("registry.json must contain a servers list")
    return data


def get_server(name: str) -> dict[str, Any]:
    for entry in load_registry()["servers"]:
        if entry.get("name") == name:
            return entry
    raise KeyError(f"Unknown BioMCP server: {name}")


def installable_servers() -> list[dict[str, Any]]:
    return [entry for entry in load_registry()["servers"] if entry.get("installable") is True]
