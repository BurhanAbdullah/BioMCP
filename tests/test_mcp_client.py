import pytest

from biomcp.mcp_client import (
    _validate_tool_arguments,
    call_tool,
    discover_tools,
    discovery_snapshot,
    json_arguments,
)


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


def test_live_stdio_discovery_uses_modern_mcp_protocol():
    snapshot = discovery_snapshot("llm")
    assert snapshot["transport"] == "stdio"
    assert snapshot["protocol_version"] == "2026-07-28"
    assert snapshot["registry_status"] == "experimental"
    assert snapshot["tools"]


def test_discovery_snapshot_preserves_registry_transport_and_protocol_provenance(monkeypatch):
    import biomcp.mcp_client as mcp_client

    entry = {
        "name": "sample",
        "installable": True,
        "external": False,
        "status": "verified",
        "transport": ["stdio"],
        "command": "sample-server",
        "tools": ["sample"],
    }

    class _FakeResult:
        tools = [_Tool()]

    class _FakeClient:
        protocol_version = "2026-07-28"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def list_tools(self):
            return _FakeResult()

    monkeypatch.setattr(mcp_client, "get_server", lambda server: entry)
    monkeypatch.setattr(mcp_client, "_client", lambda server, entry, transport=None: _FakeClient())
    monkeypatch.setattr(mcp_client, "load_registry", lambda: {"schema_version": "test", "servers": [entry]})
    monkeypatch.setattr(
        mcp_client,
        "registry_provenance",
        lambda registry: {"source": "canonical_registry", "schema_version": registry["schema_version"], "sha256": "a" * 64, "server_count": 1},
    )

    assert discovery_snapshot("sample") == {
        "server": "sample",
        "transport": "stdio",
        "protocol_version": "2026-07-28",
        "registry_status": "verified",
        "registry_provenance": {
            "source": "canonical_registry",
            "schema_version": "test",
            "sha256": "a" * 64,
            "server_count": 1,
        },
        "tools": [{"name": "sample", "description": None, "input_schema": _Tool.input_schema}],
    }


def test_deprecated_server_is_blocked_before_discovery(monkeypatch):
    import biomcp.mcp_client as mcp_client

    entry = {
        "name": "retired",
        "installable": True,
        "external": False,
        "status": "deprecated",
        "transport": ["stdio"],
        "command": "must-not-launch",
        "tools": ["sample"],
    }
    monkeypatch.setattr(mcp_client, "get_server", lambda server: entry)

    with pytest.raises(ValueError, match="deprecated and cannot be launched or called"):
        discover_tools("retired")


def test_deprecated_server_is_blocked_before_tool_call(monkeypatch):
    import biomcp.mcp_client as mcp_client

    entry = {
        "name": "retired",
        "installable": True,
        "external": False,
        "status": "deprecated",
        "transport": ["stdio"],
        "command": "must-not-launch",
        "tools": ["sample"],
    }
    monkeypatch.setattr(mcp_client, "get_server", lambda server: entry)

    with pytest.raises(ValueError, match="deprecated and cannot be launched or called"):
        call_tool("retired", "sample", {})


def test_planned_server_is_blocked_before_discovery(monkeypatch):
    import biomcp.mcp_client as mcp_client

    entry = {
        "name": "planned-server",
        "installable": True,
        "external": False,
        "status": "planned",
        "transport": ["stdio"],
        "command": "must-not-launch",
        "tools": ["sample"],
    }
    monkeypatch.setattr(mcp_client, "get_server", lambda server: entry)

    with pytest.raises(ValueError, match="planned and cannot be launched or called"):
        discover_tools("planned-server")


def test_planned_server_is_blocked_before_tool_call(monkeypatch):
    import biomcp.mcp_client as mcp_client

    entry = {
        "name": "planned-server",
        "installable": True,
        "external": False,
        "status": "planned",
        "transport": ["stdio"],
        "command": "must-not-launch",
        "tools": ["sample"],
    }
    monkeypatch.setattr(mcp_client, "get_server", lambda server: entry)

    with pytest.raises(ValueError, match="planned and cannot be launched or called"):
        call_tool("planned-server", "sample", {})


def test_call_tool_rejects_undeclared_tool_before_launch():
    with pytest.raises(ValueError, match="not declared"):
        call_tool("llm", "not_registered", {})


def test_call_tool_rejects_non_installable_non_external_server_before_launch(monkeypatch):
    import biomcp.mcp_client as mcp_client

    entry = {
        "name": "local-only",
        "installable": False,
        "external": False,
        "transport": ["stdio"],
        "command": "should-not-launch",
        "tools": ["inspect_image"],
    }
    monkeypatch.setattr(mcp_client, "get_server", lambda server: entry)

    with pytest.raises(ValueError, match="not installable or external"):
        call_tool("local-only", "inspect_image", {})


def test_call_tool_executes_registered_tool_over_mcp_stdio(monkeypatch):
    monkeypatch.setenv("BIOMCP_LLM_BASE_URL", "http://127.0.0.1:1/v1")
    result = call_tool("llm", "list_models", {})
    assert result["is_error"] is True
    assert "content" in result
    assert "protocol_version" in result["provenance"]


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
