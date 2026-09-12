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
def test_claude_desktop_path_is_platform_specific(tmp_path, platform, os_name, expected):
    path = cli._client_paths(platform=platform, os_name=os_name, home=tmp_path)["claude-desktop"]
    assert path == tmp_path.joinpath(*expected)


def test_claude_desktop_windows_uses_appdata(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))

    path = cli._client_paths(
        platform="win32",
        os_name="nt",
        home=tmp_path / "Home",
        path_cls=Path,
    )["claude-desktop"]
    assert path == tmp_path / "AppData" / "Claude" / "claude_desktop_config.json"


def test_claude_desktop_windows_requires_appdata(monkeypatch, tmp_path):
    monkeypatch.delenv("APPDATA", raising=False)

    with pytest.raises(RuntimeError, match="APPDATA is required"):
        cli._client_paths(platform="win32", os_name="nt", home=tmp_path)


def test_generic_path_honors_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    assert cli._client_paths(
        platform="linux", os_name="posix", home=tmp_path / "Home"
    )["generic"] == tmp_path / "xdg" / "biomcp" / "mcp.json"
