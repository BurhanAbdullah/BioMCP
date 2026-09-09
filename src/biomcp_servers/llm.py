"""OpenAI-compatible LLM bridge for BioMCP."""
from __future__ import annotations
import json, os, urllib.error, urllib.request
from typing import Any
from mcp.server.mcpserver import MCPServer

def _base() -> str: return os.getenv("BIOMCP_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
def _headers() -> dict[str,str]:
    key = os.getenv("BIOMCP_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key: raise RuntimeError("Set BIOMCP_LLM_API_KEY or OPENAI_API_KEY")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
def _request(path: str, payload: dict[str,Any]|None=None) -> dict[str,Any]:
    raw = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(f"{_base()}/{path.lstrip('/')}", data=raw, headers=_headers(), method="POST" if raw else "GET")
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc: raise RuntimeError(f"LLM HTTP {exc.code}: {exc.read().decode(errors='replace')[:2000]}") from exc
    except urllib.error.URLError as exc: raise RuntimeError(f"LLM endpoint unavailable: {exc.reason}") from exc

def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-LLM")
    @mcp.tool()
    def list_models() -> dict[str,Any]:
        """List models exposed by the configured OpenAI-compatible endpoint."""
        return _request("models")
    @mcp.tool()
    def complete(prompt: str, model: str|None=None, system: str="You are a careful scientific assistant.") -> dict[str,Any]:
        """Generate a text response through the configured LLM endpoint."""
        chosen = model or os.getenv("BIOMCP_LLM_MODEL")
        if not chosen: raise ValueError("Provide model or set BIOMCP_LLM_MODEL")
        return _request("responses", {"model": chosen, "input":[{"role":"system","content":system},{"role":"user","content":prompt}]})
    return mcp

def main() -> None: create_server().run()
if __name__ == "__main__": main()
