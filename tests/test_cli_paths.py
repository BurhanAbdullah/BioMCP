from pathlib import Path

import pytest

import biomcp.cli as cli


@pytest.mark.parametrize(
    ("platform", "os_name", "expected"),
    [
        ("linux", "posix", (".config", "Claude", "claude_desktop_config.json")),
        ("darwin", "posix", ("Library", "Application Support", "Claude", "claude_desktop_config.json")),
    ],
)
def test_claude_desktop_path_is_platform_specific(monkeypatch, tmp_path, platform, os_name, expected):
    monkeypatch.setattr(cli.sys, "platform", platform)
    monkeypatch.setattr(cli.os, "name", os_name)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    path = cli._client_paths()["claude-desktop"]
    assert path == tmp_path.joinpath(*expected)


def test_claude_desktop_windows_uses_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys, "platform", "win32")
    monkeypatch.setattr(cli.os, "name", "nt")
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "Home")

    path = cli._client_paths()["claude-desktop"]
    assert path == tmp_path / "AppData" / "Claude" / "claude_desktop_config.json"


def test_claude_desktop_windows_requires_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys, "platform", "win32")
    monkeypatch.setattr(cli.os, "name", "nt")
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(RuntimeError, match="APPDATA is required"):
        cli._client_paths()


def test_generic_path_honors_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys, "platform", "linux")
    monkeypatch.setattr(cli.os, "name", "posix")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "Home")

    assert cli._client_paths()["generic"] == tmp_path / "xdg" / "biomcp" / "mcp.json"
