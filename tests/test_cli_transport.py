import json

import biomcp.cli as cli
from biomcp.cli import main


def test_tools_command_passes_selected_transport(monkeypatch, capsys):
    seen = {}

    def fake_discover(server, *, transport="stdio"):
        seen.update(server=server, transport=transport)
        return [{"name": "inspect_image"}]

    monkeypatch.setattr(cli, "discover_tools", fake_discover)

    assert main(["tools", "fixture-http", "--transport", "streamable-http"]) == 0
    assert seen == {"server": "fixture-http", "transport": "streamable-http"}
    assert json.loads(capsys.readouterr().out)[0]["name"] == "inspect_image"


def test_call_command_passes_selected_transport(monkeypatch, capsys):
    seen = {}

    def fake_call(server, tool, arguments, *, transport="stdio"):
        seen.update(server=server, tool=tool, arguments=arguments, transport=transport)
        return {"is_error": False, "structured_content": {"ok": True}}

    monkeypatch.setattr(cli, "call_tool", fake_call)

    assert main([
        "call", "fixture-http", "inspect_image",
        "--arguments", '{"path":"sample.tif"}',
        "--transport", "streamable-http",
    ]) == 0
    assert seen == {
        "server": "fixture-http",
        "tool": "inspect_image",
        "arguments": {"path": "sample.tif"},
        "transport": "streamable-http",
    }
    assert json.loads(capsys.readouterr().out)["structured_content"]["ok"] is True


def test_call_command_defaults_to_registry_transport(monkeypatch, capsys):
    seen = {}

    def fake_call(server, tool, arguments, *, transport=None):
        seen.update(server=server, tool=tool, arguments=arguments, transport=transport)
        return {"is_error": False}

    monkeypatch.setattr(cli, "call_tool", fake_call)

    assert main(["call", "fixture-http", "inspect_image"]) == 0
    assert seen == {
        "server": "fixture-http",
        "tool": "inspect_image",
        "arguments": {},
        "transport": None,
    }
    assert json.loads(capsys.readouterr().out)["is_error"] is False


def test_transport_defaults_to_stdio(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli,
        "discover_tools",
        lambda server, *, transport="stdio": seen.update(server=server, transport=transport) or [],
    )

    assert main(["tools", "bioimage"]) == 0
    assert seen == {"server": "bioimage", "transport": "stdio"}
