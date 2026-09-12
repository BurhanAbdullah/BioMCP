import json
from pathlib import Path

import biomcp.cli as cli
from biomcp.cli import main


def test_install_writes_generic_and_claude_configs(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)

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
