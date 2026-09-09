"""Persistent BioMCP configuration."""
from __future__ import annotations

import json
import os
import stat
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
    CONFIG_PATH.parent.chmod(stat.S_IRWXU)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.chmod(stat.S_IRUSR | stat.S_IWUSR)
    os.replace(tmp, CONFIG_PATH)
    CONFIG_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)


def set_value(section: str, key: str, value: str) -> None:
    if section not in {"servers", "clients"}:
        raise ValueError("section must be servers or clients")
    data = load()
    data[section][key] = value
    save(data)


def show() -> str:
    return json.dumps(load(), indent=2)
