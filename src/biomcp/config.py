"""Persistent BioMCP configuration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".biomcp" / "config.json"


def load() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"servers": {}, "clients": {}}
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid BioMCP config: {CONFIG_PATH}")
    data.setdefault("servers", {})
    data.setdefault("clients", {})
    return data


def save(data: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_value(section: str, key: str, value: str) -> None:
    if section not in {"servers", "clients"}:
        raise ValueError("section must be servers or clients")
    data = load()
    data[section][key] = value
    save(data)


def show() -> str:
    return json.dumps(load(), indent=2)
