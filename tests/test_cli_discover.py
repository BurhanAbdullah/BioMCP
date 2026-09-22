import json

import biomcp.cli as cli
from biomcp.cli import main


def test_discover_command_emits_live_provenance_snapshot(monkeypatch, capsys):
    snapshot = {
        "server": "fixture",
        "transport": "stdio",
        "registry_status": "validated",
        "registry_provenance": {
            "source": "canonical_registry",
            "schema_version": "1.3",
            "sha256": "a" * 64,
            "server_count": 1,
        },
        "tools": [
            {
                "name": "inspect_image",
                "description": "Inspect an image",
                "input_schema": {"type": "object"},
            }
        ],
    }
    monkeypatch.setattr(cli, "discovery_snapshot", lambda server, *, transport=None: snapshot)

    assert main(["discover", "fixture"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output == snapshot


def test_discover_command_passes_explicit_transport(monkeypatch, capsys):
    calls = []

    def fake_discover(server, *, transport=None):
        calls.append((server, transport))
        return {"server": server, "transport": transport, "tools": []}

    monkeypatch.setattr(cli, "discovery_snapshot", fake_discover)

    assert main(["discover", "fixture", "--transport", "streamable-http"]) == 0
    assert calls == [("fixture", "streamable-http")]
    assert json.loads(capsys.readouterr().out)["transport"] == "streamable-http"
