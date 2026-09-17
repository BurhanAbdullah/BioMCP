"""Lifecycle-aware readiness assessment for registered MCP servers."""
from __future__ import annotations

from typing import Any

from .contracts import validate_server
from .doctor import diagnose
from .evidence import evidence_digest


def assess_server(server: str) -> dict[str, Any]:
    """Return a read-only go/no-go assessment backed by registry evidence.

    ``ready`` means local launch prerequisites and the live MCP tool contract
    both pass. ``blocked`` means local prerequisites are incomplete, while
    ``drift`` means prerequisites pass but the live MCP advertisement differs
    from the registry. Unexpected runtime failures are surfaced as ``error``;
    they are never converted into readiness. The evidence digest identifies
    the exact JSON evidence returned by this assessment.
    """
    diagnosis = diagnose(server)[0]
    result: dict[str, Any] = {
        "server": server,
        "status": "blocked",
        "evidence": {"doctor": diagnosis},
    }

    if not bool(diagnosis["ok"]):
        result["evidence_digest"] = evidence_digest(result["evidence"])
        return result

    try:
        contract = validate_server(server)
    except Exception as exc:
        result["status"] = "error"
        result["evidence"]["contract_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        result["evidence_digest"] = evidence_digest(result["evidence"])
        return result

    result["evidence"]["contract"] = contract
    result["status"] = "ready" if bool(contract["ok"]) else "drift"
    result["evidence_digest"] = evidence_digest(result["evidence"])
    return result
