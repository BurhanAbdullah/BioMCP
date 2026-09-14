"""Provider layer for OpenAI compatible and local model endpoints.

The provider is deliberately transport focused. It does not decide which
scientific tools a model may call. That policy belongs to the BioMCP gateway
and MCP execution layer.
"""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GatewayConfig:
    """Validated runtime configuration for an OpenAI compatible endpoint."""

    base_url: str
    api_key: str | None
    model: str | None
    timeout_seconds: int = 120
    max_response_bytes: int = 8 * 1024 * 1024

    @classmethod
    def from_environment(cls) -> "GatewayConfig":
        base = os.getenv("BIOMCP_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("BIOMCP_LLM_BASE_URL must be an HTTP(S) URL without embedded credentials")

        timeout = int(os.getenv("BIOMCP_LLM_TIMEOUT_SECONDS", "120"))
        max_bytes = int(os.getenv("BIOMCP_LLM_MAX_RESPONSE_BYTES", str(8 * 1024 * 1024)))
        if not 1 <= timeout <= 900:
            raise ValueError("BIOMCP_LLM_TIMEOUT_SECONDS must be 1..900")
        if not 1 <= max_bytes <= 64 * 1024 * 1024:
            raise ValueError("BIOMCP_LLM_MAX_RESPONSE_BYTES must be 1..67108864")

        return cls(
            base_url=base,
            api_key=os.getenv("BIOMCP_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            model=os.getenv("BIOMCP_LLM_MODEL"),
            timeout_seconds=timeout,
            max_response_bytes=max_bytes,
        )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("LLM endpoint redirects are disabled to protect API credentials")


class OpenAICompatibleProvider:
    """HTTP provider for OpenAI compatible APIs.

    The same transport is usable with hosted endpoints and local runtimes such
    as Ollama and vLLM when they expose the OpenAI compatible API surface.
    """

    name = "openai-compatible"

    def __init__(self, config: GatewayConfig | None = None) -> None:
        self.config = config or GatewayConfig.from_environment()
        self._opener = urllib.request.build_opener(_NoRedirect())

    def _headers(self) -> dict[str, str]:
        if not self.config.api_key:
            raise RuntimeError("Set BIOMCP_LLM_API_KEY or OPENAI_API_KEY")
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        raw = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}/{path.lstrip('/')}",
            data=raw,
            headers=self._headers(),
            method="POST" if raw else "GET",
        )
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                body = response.read(self.config.max_response_bytes + 1)
                if len(body) > self.config.max_response_bytes:
                    raise RuntimeError("LLM response exceeds configured response limit")
                decoded = json.loads(body.decode("utf-8"))
                if not isinstance(decoded, dict):
                    raise RuntimeError("LLM provider returned a non-object JSON response")
                return decoded
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"LLM HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise RuntimeError("LLM endpoint unavailable or request timed out") from exc

    def list_models(self) -> dict[str, Any]:
        return self.request("models")

    def complete(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str = "You are a careful scientific assistant.",
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        chosen = model or self.config.model
        if not chosen:
            raise ValueError("Provide model or set BIOMCP_LLM_MODEL")
        if temperature is not None and not 0 <= temperature <= 2:
            raise ValueError("temperature must be 0..2")
        if max_output_tokens is not None and not 1 <= max_output_tokens <= 1_000_000:
            raise ValueError("max_output_tokens must be 1..1000000")

        payload: dict[str, Any] = {
            "model": chosen,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        if response_format is not None:
            payload["text"] = {"format": response_format}
        if tools:
            payload["tools"] = tools
        return self.request("responses", payload)
