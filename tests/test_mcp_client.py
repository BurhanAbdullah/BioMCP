import json

import pytest

from biomcp.mcp_client import call_tool, discover_tools, json_arguments


def test_discover_tools_uses_live_mcp_protocol():
    tools = discover_tools("llm")
    assert [tool["name"] for tool in tools] == ["list_models", "complete"]
    assert all("input_schema" in tool for tool in tools)


def test_call_tool_rejects_undeclared_tool_before_launch():
    with pytest.raises(ValueError, match="not declared"):
        call_tool("llm", "not_registered", {})


def test_call_tool_rejects_non_installable_server_before_launch():
    with pytest.raises(ValueError, match="not installable"):
        call_tool("bionuclei", "inspect_image", {})


def test_call_tool_executes_registered_tool_over_mcp_stdio(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_BASE_URL", "http://127.0.0.1:1/v1")
    result = call_tool("llm", "list_models", {})
    assert result["is_error"] is True
    assert "content" in result


def test_json_arguments_requires_object():
    assert json_arguments('{"path":"sample.tif"}') == {"path": "sample.tif"}
    with pytest.raises(ValueError, match="JSON object"):
        json_arguments("[]")
    with pytest.raises(ValueError, match="invalid JSON"):
        json_arguments("{")
