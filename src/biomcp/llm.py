"""Provider-neutral primitives and transport for the BioMCP LLM Gateway.

The gateway keeps provider metadata separate from credentials and exposes one
transport implementation for OpenAI compatible endpoints. This covers hosted
OpenAI compatible services and local runtimes such as Ollama and vLLM when they
expose the same API surface.
"""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
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
    """Provider address and capability metadata; credentials are never stored here."""
    name: str
    base_url: str
    api_key_env: str | None = None
    capabilities: ProviderCapabilities = ProviderCapabilities()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("LLM endpoint redirects are disabled to protect API credentials")


class OpenAICompatibleProvider:
    """OpenAI compatible transport plus provider-neutral request construction."""

    def __init__(self, config: ProviderConfig, *, api_key: str | None = None, timeout_seconds: int = 120, max_response_bytes: int = 8 * 1024 * 1024) -> None:
        parsed = urllib.parse.urlsplit(config.base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("provider base_url must be an HTTP(S) URL without embedded credentials")
        if not 1 <= timeout_seconds <= 900:
            raise ValueError("timeout_seconds must be 1..900")
        if not 1 <= max_response_bytes <= 64 * 1024 * 1024:
            raise ValueError("max_response_bytes must be 1..67108864")
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self._api_key = api_key
        self._opener = urllib.request.build_opener(_NoRedirect())

    @classmethod
    def from_environment(cls, provider: str = "openai-compatible") -> "OpenAICompatibleProvider":
        profiles = builtin_providers()
        if provider not in profiles:
            raise ValueError(f"unknown LLM provider: {provider}")
        profile = profiles[provider]
        base_url = os.getenv("BIOMCP_LLM_BASE_URL", profile.base_url).rstrip("/")
        api_key = os.getenv(profile.api_key_env) if profile.api_key_env else None
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY") if profile.api_key_env else None
        timeout = int(os.getenv("BIOMCP_LLM_TIMEOUT_SECONDS", "120"))
        max_bytes = int(os.getenv("BIOMCP_LLM_MAX_RESPONSE_BYTES", str(8 * 1024 * 1024)))
        return cls(
            ProviderConfig(profile.name, base_url, profile.api_key_env, profile.capabilities),
            api_key=api_key,
            timeout_seconds=timeout,
            max_response_bytes=max_bytes,
        )

    def build_request(
        self,
        *,
        model: str,
        input: Any,
        stream: bool = False,
        response_format: Mapping[str, Any] | None = None,
        tools: list[Mapping[str, Any]] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Build a Responses style request payload without performing I/O."""
        if not model:
            raise ValueError("model is required")
        if temperature is not None and not 0 <= temperature <= 2:
            raise ValueError("temperature must be 0..2")
        if max_output_tokens is not None and not 1 <= max_output_tokens <= 1_000_000:
            raise ValueError("max_output_tokens must be 1..1000000")
        payload: dict[str, Any] = {"model": model, "input": input}
        if stream:
            payload["stream"] = True
        if response_format is not None:
            payload["response_format"] = dict(response_format)
        if tools is not None:
            payload["tools"] = [dict(tool) for tool in tools]
        if temperature is not None:
            payload["temperature"] = temperature
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        return payload

    def _headers(self) -> dict[str, str]:
        if self.config.api_key_env:
            if not self._api_key:
                raise RuntimeError(f"Set {self.config.api_key_env} or OPENAI_API_KEY")
            return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}

    def request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        raw = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.config.base_url}/{path.lstrip('/')}",
            data=raw,
            headers=self._headers(),
            method="POST" if raw else "GET",
        )
        try:
            with self._opener.open(req, timeout=self.timeout_seconds) as response:
                body = response.read(self.max_response_bytes + 1)
                if len(body) > self.max_response_bytes:
                    raise RuntimeError("LLM response exceeds configured response limit")
                result = json.loads(body.decode("utf-8"))
                if not isinstance(result, dict):
                    raise RuntimeError("LLM provider returned a non-object JSON response")
                return result
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"LLM HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise RuntimeError("LLM endpoint unavailable or request timed out") from exc

    def list_models(self) -> dict[str, Any]:
        return self.request("models")

    def complete(
        self,
        *,
        model: str,
        input: Any,
        stream: bool = False,
        response_format: Mapping[str, Any] | None = None,
        tools: list[Mapping[str, Any]] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload = self.build_request(
            model=model,
            input=input,
            stream=stream,
            response_format=response_format,
            tools=tools,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        return self.request("responses", payload)


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
