"""OpenAI-compatible LLM bridge for BioMCP."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from mcp.server.mcpserver import MCPServer


def _base() -> str:
    base = os.getenv("BIOMCP_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("BIOMCP_LLM_BASE_URL must be an HTTP(S) URL without embedded credentials")
    return base


def _limits() -> tuple[int, int]:
    timeout = int(os.getenv("BIOMCP_LLM_TIMEOUT_SECONDS", "120"))
    max_bytes = int(os.getenv("BIOMCP_LLM_MAX_RESPONSE_BYTES", str(8 * 1024 * 1024)))
    if not 1 <= timeout <= 900:
        raise ValueError("BIOMCP_LLM_TIMEOUT_SECONDS must be 1..900")
    if not 1 <= max_bytes <= 64 * 1024 * 1024:
        raise ValueError("BIOMCP_LLM_MAX_RESPONSE_BYTES must be 1..67108864")
    return timeout, max_bytes


def _headers() -> dict[str, str]:
    key = os.getenv("BIOMCP_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set BIOMCP_LLM_API_KEY or OPENAI_API_KEY")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("LLM endpoint redirects are disabled to protect API credentials")


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirect())


def _request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = None if payload is None else json.dumps(payload).encode("utf-8")
    timeout, max_bytes = _limits()
    req = urllib.request.Request(
        f"{_base()}/{path.lstrip('/')}",
        data=raw,
        headers=_headers(),
        method="POST" if raw else "GET",
    )
    try:
        with _NO_REDIRECT_OPENER.open(req, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise RuntimeError("LLM response exceeds BIOMCP_LLM_MAX_RESPONSE_BYTES")
            return json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(2001).decode(errors="replace")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail[:2000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM endpoint unavailable: {exc.reason}") from exc


def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-LLM")

    @mcp.tool()
    def list_models() -> dict[str, Any]:
        """List models exposed by the configured OpenAI-compatible endpoint."""
        return _request("models")

    @mcp.tool()
    def complete(
        prompt: str,
        model: str | None = None,
        system: str = "You are a careful scientific assistant.",
    ) -> dict[str, Any]:
        """Generate a text response through the configured LLM endpoint."""
        chosen = model or os.getenv("BIOMCP_LLM_MODEL")
        if not chosen:
            raise ValueError("Provide model or set BIOMCP_LLM_MODEL")
        return _request(
            "responses",
            {
                "model": chosen,
                "input": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
