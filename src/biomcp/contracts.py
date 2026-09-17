"""Runtime validation of registered MCP server contracts."""
from __future__ import annotations

from typing import Any

from .mcp_client import discover_tools
from .registry import get_server


def validate_server(server: str) -> dict[str, Any]:
    """Compare registry-declared tools with the live MCP advertisement.

    The validator is intentionally read-only: it performs MCP discovery but
    never executes a scientific tool. A mismatch is reported as a failed
    contract so registry drift cannot be mistaken for a valid integration.
    """
    entry = get_server(server)
    if not entry.get("installable"):
        raise ValueError(
            f"{server} is not installable and cannot be live-validated by BioMCP"
        )

    declared = sorted(set(entry.get("tools", [])))
    discovered = discover_tools(server)
    live = sorted({str(tool["name"]) for tool in discovered})
    missing = sorted(set(declared) - set(live))
    unexpected = sorted(set(live) - set(declared))

    return {
        "server": server,
        "status": entry.get("status"),
        "transport": list(entry.get("transport", [])),
        "declared_tools": declared,
        "live_tools": live,
        "missing_tools": missing,
        "unexpected_tools": unexpected,
        "ok": not missing and not unexpected,
    }
