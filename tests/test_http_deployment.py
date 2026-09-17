from __future__ import annotations

import pytest
from mcp.server.mcpserver import MCPServer

from biomcp.http import create_streamable_http_app, transport_security_from_environment
from biomcp_servers.llm import create_http_app as create_llm_http_app


def test_http_security_requires_explicit_host_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BIOMCP_HTTP_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("BIOMCP_HTTP_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(ValueError, match="BIOMCP_HTTP_ALLOWED_HOSTS"):
        transport_security_from_environment()


def test_http_security_reads_host_and_origin_allowlists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "mcp.example.org,mcp.example.org:*")
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_ORIGINS", "https://app.example.org")

    settings = transport_security_from_environment()

    assert settings.enable_dns_rebinding_protection is True
    assert settings.allowed_hosts == ["mcp.example.org", "mcp.example.org:*"]
    assert settings.allowed_origins == ["https://app.example.org"]


def test_http_security_rejects_wildcard_host_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "*")
    monkeypatch.delenv("BIOMCP_HTTP_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(ValueError, match="wildcard"):
        transport_security_from_environment()


def test_http_security_rejects_wildcard_origin_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "mcp.example.org:*")
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_ORIGINS", "*")

    with pytest.raises(ValueError, match="wildcard"):
        transport_security_from_environment()


def test_http_security_rejects_blank_allowlist_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "mcp.example.org,,mcp2.example.org")
    monkeypatch.delenv("BIOMCP_HTTP_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(ValueError, match="empty"):
        transport_security_from_environment()


def test_http_app_rejects_wildcard_direct_host_allowlist() -> None:
    server = MCPServer("BioMCP-Test")

    with pytest.raises(ValueError, match="wildcard"):
        create_streamable_http_app(server, allowed_hosts=["*"])


def test_http_app_rejects_wildcard_direct_origin_allowlist() -> None:
    server = MCPServer("BioMCP-Test")

    with pytest.raises(ValueError, match="wildcard"):
        create_streamable_http_app(
            server,
            allowed_hosts=["mcp.example.org"],
            allowed_origins=["*"],
        )


def test_http_app_rejects_blank_or_non_string_direct_allowlist_entries() -> None:
    server = MCPServer("BioMCP-Test")

    with pytest.raises(ValueError, match="empty or non-string"):
        create_streamable_http_app(
            server,
            allowed_hosts=["mcp.example.org", ""],
        )

    with pytest.raises(ValueError, match="empty or non-string"):
        create_streamable_http_app(
            server,
            allowed_hosts=["mcp.example.org", 42],  # type: ignore[list-item]
        )


def test_streamable_http_app_is_real_asgi_app() -> None:
    server = MCPServer("BioMCP-Test")

    @server.tool()
    def ping() -> str:
        return "pong"

    app = create_streamable_http_app(
        server,
        allowed_hosts=["mcp.example.org", "mcp.example.org:*"]
    )

    assert callable(app)
    assert any(getattr(route, "path", None) == "/mcp" for route in app.routes)
    assert server.session_manager is not None


def test_llm_http_factory_builds_asgi_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOMCP_HTTP_ALLOWED_HOSTS", "mcp.example.org:*")
    monkeypatch.delenv("BIOMCP_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    app = create_llm_http_app()

    assert callable(app)
    assert any(getattr(route, "path", None) == "/mcp" for route in app.routes)
