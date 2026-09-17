import pytest

from biomcp.mcp_client import _validate_tool_arguments, call_tool, discover_tools, json_arguments


class _Tool:
    name = "sample"
    description = None
    input_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
        "additionalProperties": False,
    }


def test_validate_tool_arguments_accepts_valid_schema():
    _validate_tool_arguments(_Tool(), {"path": "sample.tif"})


def test_validate_tool_arguments_rejects_missing_required_field():
    with pytest.raises(ValueError, match="required property"):
        _validate_tool_arguments(_Tool(), {})


def test_validate_tool_arguments_rejects_wrong_type():
    with pytest.raises(ValueError, match="is not of type 'string'"):
        _validate_tool_arguments(_Tool(), {"path": 123})


def test_validate_tool_arguments_rejects_extra_properties():
    with pytest.raises(ValueError, match="Additional properties are not allowed"):
        _validate_tool_arguments(_Tool(), {"path": "sample.tif", "secret": "x"})


def test_discover_tools_uses_live_mcp_protocol():
    tools = discover_tools("llm")
    assert [tool["name"] for tool in tools] == [
        "list_models",
        "complete",
        "chat",
        "chat_with_tools",
        "provider_capabilities",
        "mcp_capabilities",
        "mcp_call_tool",
    ]
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


def test_discover_tools_uses_sdk_v2_client(monkeypatch):
    import biomcp.mcp_client as mcp_client

    class _FakeResult:
        tools = [_Tool()]

    class _FakeClient:
        def __init__(self, params):
            self.params = params
            self.entered = False

        async def __aenter__(self):
            self.entered = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def list_tools(self):
            assert self.entered
            return _FakeResult()

    monkeypatch.setattr(mcp_client, "Client", _FakeClient)
    monkeypatch.setattr(mcp_client, "_server_parameters", lambda server: object())

    assert discover_tools("llm") == [
        {
            "name": "sample",
            "description": None,
            "input_schema": _Tool.input_schema,
        }
    ]


def test_call_verify_rejects_non_ready_server(monkeypatch):
    import biomcp.cli as cli

    monkeypatch.setattr(cli, "assess_server", lambda server: {"server": server, "status": "drift"})
    monkeypatch.setattr(cli, "call_tool", lambda *args: pytest.fail("call_tool must not run"))

    with pytest.raises(AssertionError):
        cli.cmd_call(
            type("Args", (), {"server": "llm", "tool": "list_models", "arguments": "{}", "verify": True})()
        )


def test_call_verify_allows_ready_server(monkeypatch):
    import biomcp.cli as cli

    monkeypatch.setattr(cli, "assess_server", lambda server: {"server": server, "status": "ready"})
    monkeypatch.setattr(cli, "call_tool", lambda *args: {"is_error": False, "content": []})

    assert cli.cmd_call(
        type("Args", (), {"server": "llm", "tool": "list_models", "arguments": "{}", "verify": True})()
    ) == 0
