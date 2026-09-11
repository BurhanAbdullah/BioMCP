import asyncio
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _list_tools(module: str) -> list[str]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", module],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


async def _call_tool(module: str, name: str, arguments: dict) -> object:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", module],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            assert not result.is_error
            return result.structuredContent


def test_bioimage_stdio_protocol_exposes_tools():
    names = asyncio.run(_list_tools("biomcp_servers.bioimage"))
    assert names == ["inspect_image", "intensity_summary", "threshold_image"]


def test_bioimage_stdio_protocol_calls_tool(tmp_path):
    import numpy as np
    import tifffile

    image = tmp_path / "protocol.tif"
    tifffile.imwrite(image, np.array([[0, 1], [2, 3]], dtype=np.uint8))
    result = asyncio.run(
        _call_tool("biomcp_servers.bioimage", "inspect_image", {"path": str(image)})
    )
    assert result["shape"] == [2, 2]
    assert result["dtype"] == "uint8"


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
    assert names == ["list_models", "complete"]


def test_llm_stdio_protocol_calls_tool_against_local_endpoint(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            assert payload["model"] == "test-model"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": "resp-test", "output": []}).encode())

        def log_message(self, format, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("BIOMCP_LLM_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("BIOMCP_LLM_API_KEY", "test-key")
    try:
        result = asyncio.run(
            _call_tool(
                "biomcp_servers.llm",
                "complete",
                {"prompt": "hello", "model": "test-model"},
            )
        )
        assert result == {"id": "resp-test", "output": []}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
