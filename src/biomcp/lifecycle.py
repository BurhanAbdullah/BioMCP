"""Registry-authoritative lifecycle inspection for BioMCP servers."""
from __future__ import annotations

from typing import Any

from .registry import load_registry


def snapshot(server: str | None = None) -> dict[str, Any]:
    """Return lifecycle state from the registry without probing or mutating servers.

    The registry remains the sole source of lifecycle truth. This helper deliberately
    does not infer readiness from process state, dependency availability, or live MCP
    discovery; those concerns belong to ``assess`` and ``doctor``.
    """
    registry = load_registry()
    entries = registry["servers"]
    if server is not None:
        entries = [entry for entry in entries if entry["name"] == server]
        if not entries:
            raise ValueError(f"Unknown BioMCP server: {server}")

    states = {"planned": 0, "experimental": 0, "validated": 0, "deprecated": 0}
    installable: list[str] = []
    external: list[str] = []
    servers: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item["name"]):
        status = entry["status"]
        states[status] += 1
        name = entry["name"]
        is_installable = entry.get("installable") is True
        is_external = entry.get("external") is True
        if is_installable:
            installable.append(name)
        if is_external:
            external.append(name)
        servers.append(
            {
                "name": name,
                "status": status,
                "installable": is_installable,
                "external": is_external,
            }
        )

    return {
        "product": registry["product"],
        "schema_version": registry["schema_version"],
        "server_count": len(servers),
        "states": states,
        "installable_servers": installable,
        "external_servers": external,
        "servers": servers,
    }
