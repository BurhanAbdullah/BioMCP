"""Production-oriented Streamable HTTP deployment helpers for BioMCP."""
from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings


def _csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def transport_security_from_environment() -> TransportSecuritySettings:
    """Build an explicit Host/Origin allowlist for remote deployments.

    Production deployments must set BIOMCP_HTTP_ALLOWED_HOSTS. Keeping this
    explicit avoids silently disabling DNS-rebinding protection behind a
    reverse proxy or load balancer.
    """
    allowed_hosts = _csv_env("BIOMCP_HTTP_ALLOWED_HOSTS")
    if not allowed_hosts:
        raise ValueError(
            "BIOMCP_HTTP_ALLOWED_HOSTS must contain at least one allowed host"
        )
    allowed_origins = _csv_env("BIOMCP_HTTP_ALLOWED_ORIGINS")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def create_streamable_http_app(
    server: MCPServer,
    *,
    allowed_hosts: list[str] | None = None,
    allowed_origins: list[str] | None = None,
    stateless_http: bool = True,
) -> Any:
    """Return an ASGI app suitable for horizontally scaled MCP deployment.

    The default stateless mode removes in-process legacy session affinity.
    Modern 2026-07-28 MCP requests are stateless at the protocol layer; the
    explicit flag also keeps legacy clients from creating per-worker sessions.
    TLS termination, worker count, autoscaling, rate limiting, and load
    balancing remain deployment concerns outside this library.
    """
    if allowed_hosts is None:
        security = transport_security_from_environment()
    else:
        if not allowed_hosts:
            raise ValueError("allowed_hosts must contain at least one host")
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins or [],
        )
    return server.streamable_http_app(
        host="0.0.0.0",
        stateless_http=stateless_http,
        transport_security=security,
    )


__all__ = ["create_streamable_http_app", "transport_security_from_environment"]
