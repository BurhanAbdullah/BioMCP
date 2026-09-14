import json
import os
import sys

import pytest

from biomcp.mcp_broker import MCPBrokerConfig, MCPToolBroker, broker_config_from_environment


SERVER_CODE = """
from mcp.server.mcpserver import MCPServer
mcp = MCPServer('broker-fixture')
@mcp.tool()
def echo(value: str) -> dict:
    return {'value': value}
@mcp.tool()
def hidden(value: str) -> dict:
    return {'value': value}
mcp.run()
"""


def _config(*tools: str) -> MCPBrokerConfig:
    return MCPBrokerConfig(
        command=(sys.executable, "-c", SERVER_CODE),
        allowed_executables=frozenset({os.path.realpath(sys.executable)}),
        allowed_tools=frozenset(tools),
        timeout_seconds=10,
        max_result_bytes=1024 * 1024,
    )


def test_real_mcp_client_session_discovers_and_calls_allowlisted_tool():
    broker = MCPToolBroker(_config("echo"))
    tools = broker.list_tools()
    assert [tool["name"] for tool in tools] == ["echo"]
    assert tools[0]["inputSchema"]
    result = broker.call_tool("echo", {"value": "scientific"})
    assert result["is_error"] is False
    assert result["structured_content"]["value"] == "scientific"


def test_tool_allowlist_blocks_execution():
    broker = MCPToolBroker(_config("echo"))
    with pytest.raises(RuntimeError, match="not allowlisted"):
        broker.call_tool("hidden", {"value": "blocked"})


def test_environment_requires_explicit_command_executable_and_tool_allowlists(monkeypatch):
    monkeypatch.setenv("BIOMCP_MCP_SERVER_COMMAND", json.dumps([sys.executable, "-c", SERVER_CODE]))
    monkeypatch.delenv("BIOMCP_MCP_ALLOWED_EXECUTABLES", raising=False)
    monkeypatch.setenv("BIOMCP_MCP_ALLOWED_TOOLS", json.dumps(["echo"]))
    with pytest.raises(RuntimeError, match="ALLOWED_EXECUTABLES"):
        broker_config_from_environment()


def test_environment_rejects_unallowlisted_executable(monkeypatch):
    monkeypatch.setenv("BIOMCP_MCP_SERVER_COMMAND", json.dumps([sys.executable, "-c", SERVER_CODE]))
    monkeypatch.setenv("BIOMCP_MCP_ALLOWED_EXECUTABLES", json.dumps(["/bin/false"]))
    monkeypatch.setenv("BIOMCP_MCP_ALLOWED_TOOLS", json.dumps(["echo"]))
    with pytest.raises(RuntimeError, match="not in BIOMCP_MCP_ALLOWED_EXECUTABLES"):
        broker_config_from_environment()


def test_environment_rejects_invalid_limits(monkeypatch):
    monkeypatch.setenv("BIOMCP_MCP_SERVER_COMMAND", json.dumps([sys.executable]))
    monkeypatch.setenv("BIOMCP_MCP_ALLOWED_EXECUTABLES", json.dumps([sys.executable]))
    monkeypatch.setenv("BIOMCP_MCP_ALLOWED_TOOLS", json.dumps(["echo"]))
    monkeypatch.setenv("BIOMCP_MCP_TOOL_TIMEOUT_SECONDS", "301")
    with pytest.raises(RuntimeError, match="must be 1..300"):
        broker_config_from_environment()


def test_config_rejects_environment_path_override():
    with pytest.raises(ValueError, match="cannot override PATH"):
        MCPBrokerConfig(
            command=(sys.executable,),
            allowed_executables=frozenset({os.path.realpath(sys.executable)}),
            allowed_tools=frozenset({"echo"}),
            child_env=(("PATH", "/unsafe"),),
        )


def test_config_rejects_empty_policy():
    with pytest.raises(ValueError, match="allowed executable"):
        MCPBrokerConfig(command=(sys.executable,), allowed_executables=frozenset(), allowed_tools=frozenset({"echo"}))
    with pytest.raises(ValueError, match="allowed tool"):
        MCPBrokerConfig(command=(sys.executable,), allowed_executables=frozenset({sys.executable}), allowed_tools=frozenset())
