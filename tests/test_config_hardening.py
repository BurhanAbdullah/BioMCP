import json

import pytest

from biomcp import config


def test_load_rejects_invalid_json(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    with pytest.raises(RuntimeError, match="Unable to read BioMCP config"):
        config.load()


def test_load_rejects_invalid_section_shape(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"servers": [], "clients": {}}), encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    with pytest.raises(RuntimeError, match="Invalid BioMCP config section: servers"):
        config.load()


def test_save_rejects_invalid_section_shape(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    with pytest.raises(RuntimeError, match="Invalid BioMCP config section: clients"):
        config.save({"servers": {}, "clients": []})
    assert not path.exists()


def test_set_value_rejects_empty_key(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    with pytest.raises(ValueError, match="key must not be empty"):
        config.set_value("servers", "   ", "value")


def test_save_uses_private_file_permissions_and_round_trips(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    config.save({"servers": {"demo": "command"}, "clients": {}})
    assert config.load() == {"servers": {"demo": "command"}, "clients": {}}
    assert path.stat().st_mode & 0o777 == 0o600
    assert not path.with_suffix(".tmp").exists()
