"""Tests for live MCP discovery against the registry contract."""
from __future__ import annotations

import pytest

from biomcp import contracts


def test_validate_server_reports_missing_and_unexpected_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        contracts,
        "discover_tools",
        lambda _, transport="stdio": [{"name": "inspect_image"}, {"name": "new_tool"}],
    )

    result = contracts.validate_server("bioimage")

    assert result["declared_tools"] == [
        "inspect_image",
        "intensity_summary",
        "threshold_image",
    ]
    assert result["live_tools"] == ["inspect_image", "new_tool"]
    assert result["missing_tools"] == ["intensity_summary", "threshold_image"]
    assert result["unexpected_tools"] == ["new_tool"]
    assert result["ok"] is False


def test_validate_server_forwards_declared_stdio_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    def fake_discover(server: str, *, transport: str = "stdio"):
        seen.update(server=server, transport=transport)
        return [
            {"name": "inspect_image"},
            {"name": "intensity_summary"},
            {"name": "threshold_image"},
        ]

    monkeypatch.setattr(contracts, "discover_tools", fake_discover)

    result = contracts.validate_server("bioimage", transport="stdio")

    assert seen == {"server": "bioimage", "transport": "stdio"}
    assert result["transport"] == "stdio"
    assert result["declared_transports"] == ["stdio"]
    assert result["ok"] is True


def test_validate_server_resolves_registry_transport_when_unspecified(monkeypatch: pytest.MonkeyPatch) -> None:
    entry = {
        "name": "http-demo",
        "installable": True,
        "status": "experimental",
        "transport": ["streamable-http"],
        "tools": ["ping"],
    }
    seen = {}

    monkeypatch.setattr(contracts, "get_server", lambda _: entry)

    def fake_discover(server: str, *, transport: str = "stdio"):
        seen.update(server=server, transport=transport)
        return [{"name": "ping"}]

    monkeypatch.setattr(contracts, "discover_tools", fake_discover)

    result = contracts.validate_server("http-demo")

    assert seen == {"server": "http-demo", "transport": "streamable-http"}
    assert result["transport"] == "streamable-http"
    assert result["declared_transports"] == ["streamable-http"]
    assert result["ok"] is True


def test_validate_server_rejects_undeclared_transport_before_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_discover(*args, **kwargs):
        raise AssertionError("live discovery must not run for an undeclared transport")

    monkeypatch.setattr(contracts, "discover_tools", fail_discover)

    with pytest.raises(ValueError, match="cannot be validated over streamable-http"):
        contracts.validate_server("bioimage", transport="streamable-http")


def test_validate_bioimage_against_live_stdio_server() -> None:
    result = contracts.validate_server("bioimage")

    assert result["ok"] is True
    assert result["status"] == "experimental"
    assert result["transport"] == "stdio"
    assert result["declared_transports"] == ["stdio"]
    assert result["missing_tools"] == []
    assert result["unexpected_tools"] == []
