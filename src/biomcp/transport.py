"""Registry-authoritative MCP transport resolution."""
from __future__ import annotations

from typing import Any

from .registry import get_server


_SUPPORTED_CLIENT_TRANSPORTS = {"stdio", "streamable-http", "sse"}


def resolve_transport_entry(entry: dict[str, Any], *, client: str = "default") -> str:
    """Resolve one registry-declared transport for a client class."""
    server = entry.get("name", "<unknown>")
    if not entry.get("installable") and not entry.get("external"):
        raise ValueError(f"{server} is not installable or external")
    declared = entry.get("transport", [])
    if not isinstance(declared, list) or not declared:
        raise ValueError(f"Server {server} does not declare an MCP transport")
    if not all(isinstance(value, str) and value in _SUPPORTED_CLIENT_TRANSPORTS for value in declared):
        raise ValueError(f"Server {server} declares an unsupported MCP transport")

    if client == "stdio":
        allowed = {"stdio"}
    elif client == "http":
        # Streamable HTTP is the current MCP HTTP transport. Prefer it when a
        # registry entry advertises both it and legacy SSE; fall back to SSE
        # only when Streamable HTTP is not declared.
        if "streamable-http" in declared:
            return "streamable-http"
        allowed = {"sse"}
    elif client == "default":
        allowed = set(_SUPPORTED_CLIENT_TRANSPORTS)
    else:
        raise ValueError(f"Unknown MCP transport client: {client}")

    matches = [value for value in declared if value in allowed]
    if len(matches) != 1:
        if not matches:
            raise ValueError(f"Server {server} does not declare a transport supported by {client}")
        raise ValueError(f"Server {server} declares multiple transports supported by {client}: {', '.join(matches)}")
    return matches[0]


def resolve_transport(server: str, *, client: str = "default") -> str:
    """Resolve one transport declared by the authoritative registry."""
    return resolve_transport_entry(get_server(server), client=client)
