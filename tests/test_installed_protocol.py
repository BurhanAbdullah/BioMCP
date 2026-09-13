"""Protocol smoke test intended to run from an installed consumer environment."""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np
import tifffile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _tools(command: str, env: dict[str, str] | None = None) -> list[str]:
    params = StdioServerParameters(command=command, args=[], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


async def _call(command: str, name: str, arguments: dict, env: dict[str, str] | None = None) -> object:
    params = StdioServerParameters(command=command, args=[], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            assert not result.is_error
            return result.structured_content


def _llm_server() -> tuple[HTTPServer, str]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            assert payload["model"] == "test-model"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": "installed-resp", "output": []}).encode())

        def log_message(self, format, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server._biomcp_thread = thread  # type: ignore[attr-defined]
    return server, f"http://127.0.0.1:{server.server_port}/v1"


def main() -> None:
    assert asyncio.run(_tools("biomcp-bioimage")) == [
        "inspect_image",
        "intensity_summary",
        "threshold_image",
    ]
    assert asyncio.run(_tools("biomcp-imagej")) == ["imagej_status", "run_macro"]
    assert asyncio.run(_tools("biomcp-llm")) == ["list_models", "complete"]

    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "consumer.tif"
        tifffile.imwrite(image, np.array([[0, 1], [2, 3]], dtype=np.uint8))
        result = asyncio.run(
            _call("biomcp-bioimage", "inspect_image", {"path": str(image)})
        )
        assert result["shape"] == [2, 2]
        assert result["dtype"] == "uint8"

    status = asyncio.run(_call("biomcp-imagej", "imagej_status", {}))
    assert status == {"configured": False, "executable": None}

    server, base_url = _llm_server()
    env = {
        **os.environ,
        "BIOMCP_LLM_BASE_URL": base_url,
        "BIOMCP_LLM_API_KEY": "test-key",
    }
    try:
        result = asyncio.run(
            _call(
                "biomcp-llm",
                "complete",
                {"prompt": "hello", "model": "test-model"},
                env=env,
            )
        )
        assert result == {"id": "installed-resp", "output": []}
    finally:
        server.shutdown()
        server.server_close()
        server._biomcp_thread.join(timeout=2)  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
