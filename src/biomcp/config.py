"""Persistent BioMCP configuration."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".biomcp" / "config.json"
_SECTIONS = {"servers", "clients"}


def _validate(data: Any) -> dict[str, Any]:
    """Validate the persisted configuration shape without interpreting secrets."""
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid BioMCP config: {CONFIG_PATH}")
    for section in _SECTIONS:
        value = data.get(section, {})
        if not isinstance(value, dict):
            raise RuntimeError(f"Invalid BioMCP config section: {section}")
    return data


def load() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"servers": {}, "clients": {}}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read BioMCP config: {CONFIG_PATH}") from exc
    return _validate(data)


def save(data: dict[str, Any]) -> None:
    data = _validate(data)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.chmod(stat.S_IRWXU)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        tmp.chmod(stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp, CONFIG_PATH)
    finally:
        if tmp.exists():
            tmp.unlink()
    CONFIG_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)


def set_value(section: str, key: str, value: str) -> None:
    if section not in _SECTIONS:
        raise ValueError("section must be servers or clients")
    if not key.strip():
        raise ValueError("key must not be empty")
    data = load()
    data[section][key] = value
    save(data)


def show() -> str:
    return json.dumps(load(), indent=2)
