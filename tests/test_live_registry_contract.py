"""Tests for live MCP discovery against the registry contract."""
from __future__ import annotations

import pytest

from biomcp import contracts


def test_validate_server_reports_missing_and_unexpected_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        contracts,
        "discover_tools",
        lambda _: [{"name": "inspect_image"}, {"name": "new_tool"}],
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


def test_validate_bioimage_against_live_stdio_server() -> None:
    result = contracts.validate_server("bioimage")

    assert result["ok"] is True
    assert result["status"] == "experimental"
    assert result["transport"] == ["stdio"]
    assert result["missing_tools"] == []
    assert result["unexpected_tools"] == []
