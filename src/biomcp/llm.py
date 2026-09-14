"""Provider-neutral primitives for the BioMCP LLM Gateway."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProviderCapabilities:
    """Declared capabilities of an LLM provider endpoint."""
    model_discovery: bool = True
    chat: bool = True
    responses: bool = True
    streaming: bool = False
    structured_output: bool = False
    tool_calling: bool = False


@dataclass(frozen=True)
class ProviderConfig:
    """Provider address and capability metadata; no credentials are stored."""
    name: str
    base_url: str
    api_key_env: str | None = None
    capabilities: ProviderCapabilities = ProviderCapabilities()


class OpenAICompatibleProvider:
    """Provider profile and request construction for OpenAI-compatible APIs."""
    def __init__(self, config: ProviderConfig) -> None:
        if not config.base_url.startswith(("http://", "https://")):
            raise ValueError("provider base_url must use HTTP(S)")
        self.config = config

    def build_request(
        self,
        *,
        model: str,
        input: Any,
        stream: bool = False,
        response_format: Mapping[str, Any] | None = None,
        tools: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build a provider-neutral Responses-style request payload."""
        payload: dict[str, Any] = {"model": model, "input": input}
        if stream:
            payload["stream"] = True
        if response_format is not None:
            payload["response_format"] = dict(response_format)
        if tools is not None:
            payload["tools"] = [dict(tool) for tool in tools]
        return payload


def builtin_providers() -> dict[str, ProviderConfig]:
    """Return supported provider profiles without reading credential values."""
    return {
        "openai-compatible": ProviderConfig(
            "openai-compatible", "https://api.openai.com/v1", "BIOMCP_LLM_API_KEY",
            ProviderCapabilities(streaming=True, structured_output=True, tool_calling=True),
        ),
        "ollama": ProviderConfig(
            "ollama", "http://127.0.0.1:11434/v1", None,
            ProviderCapabilities(streaming=True),
        ),
        "vllm": ProviderConfig(
            "vllm", "http://127.0.0.1:8000/v1", "BIOMCP_LLM_API_KEY",
            ProviderCapabilities(streaming=True, structured_output=True, tool_calling=True),
        ),
    }
