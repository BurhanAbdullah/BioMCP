import pytest

import biomcp.transport as transport


def test_stdio_transport_resolution_is_registry_authoritative(monkeypatch):
    monkeypatch.setattr(
        transport,
        "get_server",
        lambda name: {
            "name": name,
            "installable": True,
            "transport": ["stdio"],
        },
    )

    assert transport.resolve_transport("fixture", client="stdio") == "stdio"


def test_http_transport_resolution_accepts_streamable_http(monkeypatch):
    monkeypatch.setattr(
        transport,
        "get_server",
        lambda name: {
            "name": name,
            "external": True,
            "transport": ["streamable-http"],
        },
    )

    assert transport.resolve_transport("fixture", client="http") == "streamable-http"


def test_http_transport_resolution_prefers_streamable_http_over_legacy_sse(monkeypatch):
    monkeypatch.setattr(
        transport,
        "get_server",
        lambda name: {
            "name": name,
            "external": True,
            "transport": ["streamable-http", "sse"],
        },
    )

    assert transport.resolve_transport("fixture", client="http") == "streamable-http"


def test_default_transport_resolution_rejects_ambiguous_metadata(monkeypatch):
    monkeypatch.setattr(
        transport,
        "get_server",
        lambda name: {
            "name": name,
            "external": True,
            "transport": ["streamable-http", "sse"],
        },
    )

    with pytest.raises(ValueError, match="multiple transports"):
        transport.resolve_transport("fixture", client="default")
