"""Dependency-light scientific artifact and provenance contracts for BioIO."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ALLOWED_STATUSES = {"succeeded", "failed", "cancelled", "partial"}


def _json_value(value: Any, *, label: str) -> Any:
    """Return a detached JSON-compatible value, rejecting NaN and custom objects."""
    try:
        encoded = json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))
        return json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain only finite JSON-compatible values") from exc


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be 1-128 characters using letters, digits, '.', '_', ':', or '-'")
    return value


def _require_timestamp(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    return value


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
    """Return (sha256, byte_size) using bounded-memory streaming."""
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer")
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Artifact file does not exist: {source}")
    digest = hashlib.sha256()
    size = 0
    with source.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


@dataclass(frozen=True)
class ScientificArtifact:
    """Reference to a scientific file or dataset; payload bytes remain external."""

    artifact_id: str
    media_type: str
    uri: str
    sha256: str
    size_bytes: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.artifact_id, "artifact_id")
        if not isinstance(self.media_type, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*",
            self.media_type,
        ):
            raise ValueError("media_type must be a valid type/subtype")
        if not isinstance(self.uri, str) or not self.uri.strip():
            raise ValueError("uri must be a non-empty string")
        parsed = urlparse(self.uri)
        if parsed.scheme and parsed.scheme not in {"file", "https", "http", "s3", "gs", "ome-zarr"}:
            raise ValueError(f"unsupported artifact URI scheme: {parsed.scheme}")
        if not _SHA256_RE.fullmatch(self.sha256 or ""):
            raise ValueError("sha256 must be a lowercase 64-character hexadecimal digest")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int) or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        object.__setattr__(self, "metadata", _json_value(dict(self.metadata), label="metadata"))

    @classmethod
    def from_file(
        cls,
        artifact_id: str,
        path: str | Path,
        media_type: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ScientificArtifact":
        source = Path(path).expanduser().resolve()
        digest, size = sha256_file(source)
        return cls(
            artifact_id=artifact_id,
            media_type=media_type,
            uri=source.as_uri(),
            sha256=digest,
            size_bytes=size,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "media_type": self.media_type,
            "uri": self.uri,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "metadata": _json_value(dict(self.metadata), label="metadata"),
        }


@dataclass(frozen=True)
class ExecutionProvenance:
    """Auditable record of one scientific operation and its artifact lineage."""

    execution_id: str
    server: str
    tool: str
    software_version: str
    started_at: str
    finished_at: str
    status: str
    input_artifacts: tuple[str, ...] = ()
    output_artifacts: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)
    random_seed: int | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.execution_id, "execution_id")
        _require_id(self.server, "server")
        _require_id(self.tool, "tool")
        if not isinstance(self.software_version, str) or not self.software_version.strip():
            raise ValueError("software_version must be a non-empty string")
        _require_timestamp(self.started_at, "started_at")
        _require_timestamp(self.finished_at, "finished_at")
        start = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        finish = datetime.fromisoformat(self.finished_at.replace("Z", "+00:00"))
        if finish < start:
            raise ValueError("finished_at cannot precede started_at")
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError(f"status must be one of {sorted(_ALLOWED_STATUSES)}")
        for label, values in (("input_artifacts", self.input_artifacts), ("output_artifacts", self.output_artifacts)):
            if not isinstance(values, (tuple, list)):
                raise ValueError(f"{label} must be a sequence of artifact IDs")
            for value in values:
                _require_id(value, f"{label} item")
        if self.random_seed is not None and (
            isinstance(self.random_seed, bool) or not isinstance(self.random_seed, int) or self.random_seed < 0
        ):
            raise ValueError("random_seed must be a non-negative integer or None")
        if not isinstance(self.parameters, Mapping):
            raise ValueError("parameters must be a mapping")
        if not isinstance(self.warnings, (tuple, list)) or not all(isinstance(x, str) for x in self.warnings):
            raise ValueError("warnings must be a sequence of strings")
        object.__setattr__(self, "parameters", _json_value(dict(self.parameters), label="parameters"))
        object.__setattr__(self, "input_artifacts", tuple(self.input_artifacts))
        object.__setattr__(self, "output_artifacts", tuple(self.output_artifacts))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "server": self.server,
            "tool": self.tool,
            "software_version": self.software_version,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "input_artifacts": list(self.input_artifacts),
            "output_artifacts": list(self.output_artifacts),
            "parameters": _json_value(dict(self.parameters), label="parameters"),
            "random_seed": self.random_seed,
            "warnings": list(self.warnings),
        }
