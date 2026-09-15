from __future__ import annotations

import pytest
from mcp.server.mcpserver import MCPServer

from biomcp.http import create_streamable_http_app, transport_security_from_environment


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
