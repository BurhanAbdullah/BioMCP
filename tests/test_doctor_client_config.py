import json
from pathlib import Path

import biomcp.doctor as doctor


def _entry():
    return {
        "name": "bioimage",
        "status": "experimental",
        "installable": True,
        "command": "biomcp-bioimage",
        "args": [],
        "transport": ["stdio"],
    }


def test_client_config_missing_is_nonblocking(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    result = doctor._client_config_status(_entry())

    assert result["status"] == "missing"
    assert result["ok"] is True


def test_client_config_match_is_healthy(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / ".config/biomcp/mcp.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({
            "mcpServers": {
                "biomcp_bioimage": {
                    "command": "biomcp-bioimage",
                    "args": [],
                }
            }
        }),
        encoding="utf-8",
    )

    result = doctor._client_config_status(_entry())

    assert result["status"] == "match"
    assert result["transport"] == "stdio"
    assert result["ok"] is True


def test_client_config_drift_blocks_readiness(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / ".config/biomcp/mcp.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({
            "mcpServers": {
                "biomcp_bioimage": {
                    "command": "tampered-command",
                    "args": [],
                }
            }
        }),
        encoding="utf-8",
    )

    result = doctor._client_config_status(_entry())

    assert result["status"] == "drift"
    assert result["ok"] is False
    assert result["expected"]["command"] == "biomcp-bioimage"


def test_client_config_invalid_json_blocks_readiness(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / ".config/biomcp/mcp.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    result = doctor._client_config_status(_entry())

    assert result["status"] == "invalid"
    assert result["ok"] is False
