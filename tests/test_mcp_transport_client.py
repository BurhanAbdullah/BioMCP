import pytest

import biomcp.mcp_client as mcp_client


def test_http_client_uses_registry_declared_endpoint(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, target):
            captured["target"] = target

    entry = {
        "name": "fixture",
        "external": True,
        "transport": ["streamable-http"],
        "endpoint": "https://example.invalid/mcp",
    }
    monkeypatch.setattr(mcp_client, "Client", FakeClient)

    client = mcp_client._client("fixture", entry, transport="streamable-http")

    assert isinstance(client, FakeClient)
    assert captured["target"] == "https://example.invalid/mcp"


def test_http_client_rejects_missing_registry_endpoint():
    entry = {
        "name": "fixture",
        "external": True,
        "transport": ["streamable-http"],
    }

    with pytest.raises(ValueError, match="does not declare an HTTP MCP endpoint"):
        mcp_client._client("fixture", entry, transport="streamable-http")


def test_http_client_does_not_silently_select_sse(monkeypatch):
    entry = {
        "name": "fixture",
        "external": True,
        "transport": ["streamable-http", "sse"],
        "endpoint": "https://example.invalid/mcp",
    }
    monkeypatch.setattr(mcp_client, "Client", lambda target: target)

    with pytest.raises(ValueError, match="multiple transports"):
        mcp_client._client("fixture", entry, transport="streamable-http")
