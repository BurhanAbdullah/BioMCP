import json
import os
import sys

import pytest

from biomcp.llm import OpenAICompatibleProvider, ProviderCapabilities, ProviderConfig
from biomcp.mcp_broker import MCPBrokerConfig, MCPToolBroker


SERVER_CODE = """
from mcp.server.mcpserver import MCPServer
mcp = MCPServer('tool-call-fixture')
@mcp.tool()
def echo(value: str) -> dict:
    return {'value': value}
mcp.run()
"""


class _JsonResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.body


class _Opener:
    def __init__(self, body: bytes):
        self.body = body
        self.request = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return _JsonResponse(self.body)


def test_chat_preserves_provider_tool_call_without_executing_it():
    opener = _Opener(json.dumps({
        "id": "chat-tool-1",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "echo",
                        "arguments": json.dumps({"value": "from-model"}),
                    },
                }],
            },
            "finish_reason": "tool_calls",
        }],
    }).encode("utf-8"))
    provider = OpenAICompatibleProvider(ProviderConfig(
        "test",
        "http://127.0.0.1:9000/v1",
        capabilities=ProviderCapabilities(tool_calling=True),
    ))
    provider._opener = opener

    result = provider.chat(
        model="m",
        messages=[{"role": "user", "content": "use echo"}],
        tools=[{"type": "function", "function": {"name": "echo"}}],
        retries=0,
    )

    assert result["choices"][0]["finish_reason"] == "tool_calls"
    call = result["choices"][0]["message"]["tool_calls"][0]
    assert call["id"] == "call-1"
    assert call["function"]["name"] == "echo"
    assert json.loads(call["function"]["arguments"]) == {"value": "from-model"}
    assert opener.request.full_url.endswith("/chat/completions")


def _broker() -> MCPToolBroker:
    config = MCPBrokerConfig(
        command=(sys.executable, "-c", SERVER_CODE),
        allowed_executables=frozenset({os.path.realpath(sys.executable)}),
        allowed_tools=frozenset({"echo"}),
        timeout_seconds=10,
        max_result_bytes=1024 * 1024,
    )
    return MCPToolBroker(config)


def test_explicit_tool_call_can_cross_only_the_mcp_allowlist():
    broker = _broker()
    result = broker.call_tool("echo", {"value": "authorized"})
    assert json.loads(result["content"][0]["text"])["value"] == "authorized"

    with pytest.raises(RuntimeError, match="not allowlisted"):
        broker.call_tool("hidden", {"value": "blocked"})
