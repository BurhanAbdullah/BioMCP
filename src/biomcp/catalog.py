"""Machine-readable registry discovery for BioMCP clients."""
from __future__ import annotations

from typing import Any

from .provenance import registry_provenance
from .registry import load_registry


def catalog(server: str | None = None) -> dict[str, Any]:
    """Return a deterministic, registry-authoritative server catalog.

    This is a discovery view only: values are copied from the canonical registry
    and no readiness, compatibility, transport, or provider claims are inferred.
    """
    registry = load_registry()
    entries = registry["servers"]
    if server is not None:
        entries = [entry for entry in entries if entry["name"] == server]
        if not entries:
            raise ValueError(f"Unknown BioMCP server: {server}")

    servers: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item["name"]):
        item: dict[str, Any] = {
            "name": entry["name"],
            "display_name": entry["display_name"],
            "category": entry["category"],
            "kind": entry["kind"],
            "status": entry["status"],
            "installable": bool(entry.get("installable", False)),
            "external": bool(entry.get("external", False)),
            "transport": list(entry.get("transport", [])),
            "tools": list(entry.get("tools", [])),
            "description": entry["description"],
        }
        for key in ("distribution", "package_extra", "endpoint"):
            if key in entry:
                item[key] = entry[key]
        servers.append(item)

    return {
        "product": registry["product"],
        "schema_version": registry["schema_version"],
        "server_count": len(servers),
        "servers": servers,
        "provenance": registry_provenance(registry),
    }
