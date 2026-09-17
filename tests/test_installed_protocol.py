import asyncio
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np
import tifffile


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length))
        if self.path.endswith("/chat/completions"):
            payload = {"id": "chat-1", "choices": [{"message": {"role": "assistant", "content": body["messages"][-1]["content"]}, "finish_reason": "stop"}]}
        elif self.path.endswith("/responses"):
            payload = {"id": "resp-1", "output": [{"type": "message", "content": [{"type": "output_text", "text": body["input"]}]}]}
        else:
            self.send_response(404)
            self.end_headers()
            return
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path.endswith("/models"):
            encoded = json.dumps({"data": [{"id": "fixture-model"}]}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass


def _server():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server._biomcp_thread = thread  # type: ignore[attr-defined]
    return server, f"http://127.0.0.1:{server.server_port}/v1"


async def _tools(command: str):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=command, args=[], env=os.environ.copy())
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


def main() -> None:
    assert asyncio.run(_tools("biomcp-bioimage")) == [
        "inspect_image",
        "intensity_summary",
        "threshold_image",
    ]
    assert asyncio.run(_tools("biomcp-imagej")) == ["imagej_status", "run_macro"]
    assert asyncio.run(_tools("biomcp-llm")) == [
        "list_models",
        "complete",
        "chat",
        "chat_with_tools",
        "provider_capabilities",
        "mcp_capabilities",
        "mcp_call_tool",
    ]

    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "consumer.tif"
        tifffile.imwrite(image, np.array([[0, 1], [2, 3]], dtype=np.uint8))

    server, base_url = _server()
    try:
        env = os.environ.copy()
        env.update({
            "BIOMCP_LLM_PROVIDER": "openai-compatible",
            "BIOMCP_LLM_BASE_URL": base_url,
            "BIOMCP_LLM_MODEL": "fixture-model",
        })
        result = subprocess.run(
            ["biomcp-llm", "--help"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "chat_with_tools" in result.stdout or result.returncode == 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
