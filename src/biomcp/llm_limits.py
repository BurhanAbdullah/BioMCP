"""Deterministic resource limits for LLM conversation inputs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LLMContextLimits:
    """Bounds applied before an LLM conversation is sent to a provider."""

    max_messages: int = 64
    max_context_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if not 1 <= self.max_messages <= 4096:
            raise ValueError("max_messages must be 1..4096")
        if not 1024 <= self.max_context_bytes <= 16 * 1024 * 1024:
            raise ValueError("max_context_bytes must be 1024..16777216")


def validate_context(messages: list[Mapping[str, Any]], limits: LLMContextLimits) -> list[dict[str, Any]]:
    """Validate and copy a message sequence under explicit resource bounds."""
    if not messages:
        raise ValueError("messages must not be empty")
    if len(messages) > limits.max_messages:
        raise ValueError("LLM conversation exceeds configured message limit")
    copied: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, Mapping):
            raise ValueError("LLM conversation messages must be objects")
        copied.append(dict(message))
    try:
        encoded = json.dumps(copied, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("LLM conversation contains non-serializable content") from exc
    if len(encoded) > limits.max_context_bytes:
        raise ValueError("LLM conversation exceeds configured context size limit")
    return copied


def limits_from_environment(environ: Mapping[str, str]) -> LLMContextLimits:
    """Read bounded context limits without accessing credentials."""
    try:
        max_messages = int(environ.get("BIOMCP_LLM_MAX_CONTEXT_MESSAGES", "64"))
        max_bytes = int(environ.get("BIOMCP_LLM_MAX_CONTEXT_BYTES", str(1_048_576)))
    except ValueError as exc:
        raise ValueError("LLM context limits must be integers") from exc
    return LLMContextLimits(max_messages=max_messages, max_context_bytes=max_bytes)
