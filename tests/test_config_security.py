from biomcp import config


def test_save_uses_private_permissions(tmp_path, monkeypatch):
    path = tmp_path / ".biomcp" / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    config.save({"servers": {}, "clients": {}})
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
