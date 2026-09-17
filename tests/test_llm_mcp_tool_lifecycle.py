import json

import pytest

from biomcp.llm import chat_with_mcp_tools


class _Provider:
    def __init__(self):
        self.calls = []
        self._responses = [
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "echo", "arguments": json.dumps({"value": "hello"})},
                        }],
                    },
                    "finish_reason": "tool_calls",
                }]
            },
            {
                "choices": [{
                    "message": {"role": "assistant", "content": "The tool returned hello."},
                    "finish_reason": "stop",
                }]
            },
        ]

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _Broker:
    def __init__(self):
        self.calls = []

    def list_tools(self):
        return [{
            "name": "echo",
            "description": "Echo a value.",
            "inputSchema": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
        }]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"is_error": False, "content": [{"text": json.dumps(arguments)}], "structured_content": arguments}


def test_llm_tool_call_executes_only_through_broker_and_continues():
    provider = _Provider()
    broker = _Broker()

    result = chat_with_mcp_tools(
        provider,
        broker,
        model="test-model",
        messages=[{"role": "user", "content": "say hello"}],
    )

    assert result["choices"][0]["message"]["content"] == "The tool returned hello."
    assert broker.calls == [("echo", {"value": "hello"})]
    assert len(provider.calls) == 2
    assert provider.calls[0]["tools"][0]["function"]["name"] == "echo"
    assert provider.calls[1]["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": json.dumps({
            "is_error": False,
            "content": [{"text": json.dumps({"value": "hello"})}],
            "structured_content": {"value": "hello"},
        }),
    }
    assert result["_biomcp"]["mcp_tool_calls"] == [{"id": "call-1", "name": "echo"}]


def test_llm_tool_call_rejects_unadvertised_tool_before_execution():
    provider = _Provider()
    broker = _Broker()
    provider._responses[0]["choices"][0]["message"]["tool_calls"][0]["function"]["name"] = "hidden"

    with pytest.raises(RuntimeError, match="not authorized"):
        chat_with_mcp_tools(
            provider,
            broker,
            model="test-model",
            messages=[{"role": "user", "content": "do it"}],
        )

    assert broker.calls == []


def test_llm_tool_call_loop_is_bounded():
    provider = _Provider()
    broker = _Broker()
    provider._responses = [provider._responses[0], provider._responses[0]]

    with pytest.raises(RuntimeError, match="exceeded max_tool_rounds"):
        chat_with_mcp_tools(
            provider,
            broker,
            model="test-model",
            messages=[{"role": "user", "content": "loop"}],
            max_tool_rounds=2,
        )

    assert len(broker.calls) == 2
