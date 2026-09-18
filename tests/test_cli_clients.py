import json
from pathlib import Path

import biomcp.cli as cli
from biomcp.cli import main


def test_install_writes_generic_and_claude_configs(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    # The test exercises the documented fallback to $HOME/.config.  CI hosts
    # may define XDG_CONFIG_HOME independently of the patched home directory.
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    assert main(
        [
            "install",
            "--servers",
            "bioimage",
            "--clients",
            "generic,claude-desktop",
        ]
    ) == 0

    for relative in [
        Path(".config/biomcp/mcp.json"),
        Path(".config/Claude/claude_desktop_config.json"),
    ]:
        config = json.loads((tmp_path / relative).read_text(encoding="utf-8"))
        assert config["mcpServers"]["biomcp_bioimage"]["command"]
        assert config["mcpServers"]["biomcp_bioimage"]["args"] == []


def test_install_writes_idempotent_codex_config(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)

    assert main(
        ["install", "--servers", "bioimage", "--clients", "codex"]
    ) == 0
    first = (tmp_path / ".codex/config.toml").read_text(encoding="utf-8")

    assert main(
        ["install", "--servers", "bioimage", "--clients", "codex"]
    ) == 0
    second = (tmp_path / ".codex/config.toml").read_text(encoding="utf-8")

    assert second == first
    assert second.count("[mcp_servers.biomcp_bioimage]") == 1
    assert 'command = "biomcp-bioimage"' in second
    assert "args = []" in second


def test_install_rejects_unknown_client_before_writing(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    try:
        main(["install", "--servers", "bioimage", "--clients", "generic,unknown"])
    except SystemExit as exc:
        assert str(exc) == "Unsupported client: unknown"
    else:
        raise AssertionError("unsupported client must fail before configuration")

    assert not (tmp_path / ".config/biomcp/mcp.json").exists()


def test_install_rolls_back_prior_client_when_later_write_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    generic = tmp_path / ".config/biomcp/mcp.json"
    generic.parent.mkdir(parents=True)
    original = '{"mcpServers": {"existing": {"command": "keep"}}}\n'
    generic.write_text(original, encoding="utf-8")

    real_write_json = cli._write_json
    calls = {"count": 0}

    def fail_second(path, servers):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("simulated client write failure")
        return real_write_json(path, servers)

    monkeypatch.setattr(cli, "_write_json", fail_second)
    try:
        main(["install", "--servers", "bioimage", "--clients", "generic,claude-desktop"])
    except RuntimeError as exc:
        assert str(exc) == "simulated client write failure"
    else:
        raise AssertionError("later client failure must abort installation")

    assert generic.read_text(encoding="utf-8") == original
    assert not (tmp_path / ".config/Claude/claude_desktop_config.json").exists()


def test_install_rejects_unknown_server_before_dependency_install(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "_install_extra", lambda entry: calls.append(entry["name"]))

    try:
        main(["install", "--servers", "bioimage,unknown", "--clients", "none"])
    except SystemExit as exc:
        assert str(exc) == "Unknown BioMCP server: unknown"
    else:
        raise AssertionError("unknown server must fail before dependency installation")

    assert calls == []
