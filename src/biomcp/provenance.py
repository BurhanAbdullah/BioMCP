"""Provenance helpers for registry-derived BioMCP metadata."""
from __future__ import annotations

import hashlib
from typing import Any

from .registry import REGISTRY_PATH


def registry_provenance(registry: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic identity metadata for the canonical registry."""
    digest = hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest()
    return {
        "source": "canonical_registry",
        "schema_version": registry["schema_version"],
        "sha256": digest,
        "server_count": len(registry["servers"]),
    }
