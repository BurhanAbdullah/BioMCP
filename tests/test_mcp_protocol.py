from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _server_parameters(module: str) -> StdioServerParameters:
    return StdioServerParameters(command="python", args=["-m", module])


async def _list_tools(module: str) -> list[str]:
    async with stdio_client(_server_parameters(module)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


async def _call_tool(module: str, name: str, arguments: dict) -> dict:
    async with stdio_client(_server_parameters(module)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            return result.structured_content


def test_imagej_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.imagej"))
    assert names == ["imagej_status", "run_macro"]


def test_imagej_stdio_protocol_calls_status_tool():
    result = asyncio.run(
        _call_tool("biomcp_servers.imagej", "imagej_status", {})
    )
    assert result == {"configured": False, "executable": None}


def test_llm_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.llm"))
    assert names == ["list_models", "complete", "mcp_capabilities", "mcp_call_tool"]


def test_llm_stdio_protocol_calls_tool_against_local_endpoint(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            assert payload["model"] == "test-model"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "id": "test",
                        "object": "chat.completion",
                        "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    }
                ).encode()
            )

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    try:
        monkeypatch.setenv("BIOMCP_LLM_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
        monkeypatch.setenv("BIOMCP_LLM_MODEL", "test-model")
        import threading

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        result = asyncio.run(_call_tool("biomcp_servers.llm", "complete", {"prompt": "hello"}))
        assert result["content"] == "ok"
    finally:
        server.shutdown()
