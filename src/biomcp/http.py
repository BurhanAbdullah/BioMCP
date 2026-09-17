"""Production-oriented Streamable HTTP deployment helpers for BioMCP."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Awaitable, Callable

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings


ASGIApp = Callable[
    [dict[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[None]]],
    Awaitable[None],
]


def _validate_allowlist(name: str, entries: list[str], *, required: bool = False) -> list[str]:
    if required and not entries:
        raise ValueError(f"{name} must contain at least one allowed host")
    normalized = [item.strip() for item in entries]
    if any(not item for item in normalized):
        raise ValueError(f"{name} must not contain empty allowlist entries")
    if any(item == "*" for item in normalized):
        raise ValueError(f"{name} must not contain a wildcard allowlist entry")
    return normalized


def _csv_env(name: str) -> list[str]:
    value = os.getenv(name, "")
    if not value.strip():
        return []
    return _validate_allowlist(name, value.split(","))


def _optional_positive_int_env(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


class ConcurrencyLimitMiddleware:
    """Bound in-flight HTTP requests within one ASGI process.

    This is local backpressure, not a distributed rate limiter. When the
    process is saturated, requests receive a retryable 503 response rather
    than being allowed to grow an unbounded in-process queue.
    """

    def __init__(self, app: ASGIApp, max_concurrent_requests: int | None) -> None:
        if max_concurrent_requests is not None and max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be a positive integer")
        self.app = app
        self.max_concurrent_requests = max_concurrent_requests
        self._active_requests = 0
        self._admission_lock = asyncio.Lock()

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        if self.max_concurrent_requests is None or scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        async with self._admission_lock:
            if self._active_requests >= self.max_concurrent_requests:
                admitted = False
            else:
                self._active_requests += 1
                admitted = True

        if not admitted:
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"retry-after", b"1"),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"BioMCP HTTP concurrency limit reached; retry later.",
                }
            )
            return

        try:
            await self.app(scope, receive, send)
        finally:
            async with self._admission_lock:
                self._active_requests -= 1


def transport_security_from_environment() -> TransportSecuritySettings:
    """Build an explicit Host/Origin allowlist for remote deployments.

    Production deployments must set BIOMCP_HTTP_ALLOWED_HOSTS. Keeping this
    explicit avoids silently disabling DNS-rebinding protection behind a
    reverse proxy or load balancer.
    """
    allowed_hosts = _validate_allowlist(
        "BIOMCP_HTTP_ALLOWED_HOSTS",
        _csv_env("BIOMCP_HTTP_ALLOWED_HOSTS"),
        required=True,
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
    max_concurrent_requests: int | None = None,
) -> Any:
    """Return an ASGI app suitable for horizontally scaled MCP deployment.

    ``max_concurrent_requests`` bounds work per ASGI process. If omitted, the
    existing unbounded application behavior is preserved. The environment
    variable ``BIOMCP_HTTP_MAX_CONCURRENCY`` can provide the same setting.
    This limit is intentionally process-local; distributed rate limiting is a
    separate deployment concern.
    """
    if allowed_hosts is None:
        security = transport_security_from_environment()
    else:
        allowed_hosts = _validate_allowlist("allowed_hosts", allowed_hosts, required=True)
        allowed_origins = _validate_allowlist("allowed_origins", allowed_origins or [])
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )
    app = server.streamable_http_app(
        host="0.0.0.0",
        stateless_http=stateless_http,
        transport_security=security,
    )
    limit = max_concurrent_requests
    if limit is None:
        limit = _optional_positive_int_env("BIOMCP_HTTP_MAX_CONCURRENCY")
    if limit is not None:
        app = ConcurrencyLimitMiddleware(app, limit)
    return app


__all__ = [
    "ConcurrencyLimitMiddleware",
    "create_streamable_http_app",
    "transport_security_from_environment",
]
