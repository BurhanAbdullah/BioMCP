"""Deterministic digests for BioMCP readiness evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def evidence_digest(evidence: dict[str, Any]) -> str:
    """Return a stable SHA-256 digest of JSON-serializable evidence.

    Canonical JSON makes the digest independent of dictionary insertion order.
    The digest is an integrity identifier, not a signature or proof of truth.
    """
    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a JSON object")
    try:
        payload = json.dumps(
            evidence,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TypeError("evidence must contain only JSON-serializable values") from exc
    return hashlib.sha256(payload).hexdigest()
