"""Runtime validation of registered MCP server contracts."""
from __future__ import annotations

from typing import Any

from .mcp_client import discover_tools
from .registry import get_server
from .transport import resolve_transport_entry


def validate_server(server: str, *, transport: str | None = None) -> dict[str, Any]:
    """Compare registry-declared tools with the live MCP advertisement.

    The validator is intentionally read-only: it performs MCP discovery but
    never executes a scientific tool. A mismatch is reported as a failed
    contract so registry drift cannot be mistaken for a valid integration.
    When no transport is requested, the validator resolves the single
    registry-declared transport instead of assuming stdio.
    """
    entry = get_server(server)
    if not entry.get("installable"):
        raise ValueError(
            f"{server} is not installable and cannot be live-validated by BioMCP"
        )

    declared = sorted(set(entry.get("tools", [])))
    requested = transport
    try:
        resolved = resolve_transport_entry(entry, client="default" if requested is None else ("stdio" if requested == "stdio" else "http"))
    except ValueError as exc:
        if requested is None:
            raise ValueError(f"Server {server} cannot be validated using its registry transport: {exc}") from exc
        raise ValueError(f"Server {server} cannot be validated over {requested}: {exc}") from exc
    if requested is not None and resolved != requested:
        raise ValueError(f"Server {server} resolved transport {resolved}, not requested {requested}")
    transport = resolved

    discovered = discover_tools(server, transport=transport)
    live = sorted({str(tool["name"]) for tool in discovered})
    missing = sorted(set(declared) - set(live))
    unexpected = sorted(set(live) - set(declared))

    return {
        "server": server,
        "status": entry.get("status"),
        "transport": transport,
        "declared_transports": list(entry.get("transport", [])),
        "declared_tools": declared,
        "live_tools": live,
        "missing_tools": missing,
        "unexpected_tools": unexpected,
        "ok": not missing and not unexpected,
    }
