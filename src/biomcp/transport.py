"""Registry-authoritative MCP transport resolution."""
from __future__ import annotations

from .registry import get_server


_SUPPORTED_CLIENT_TRANSPORTS = {"stdio", "streamable-http", "sse"}


def resolve_transport(server: str, *, client: str = "default") -> str:
    """Resolve one unambiguous transport declared by the registry.

    The resolver never infers a transport from command availability or runtime
    behavior.  A client may explicitly restrict the transports it supports.
    """
    entry = get_server(server)
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
        allowed = {"streamable-http", "sse"}
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
