import asyncio
import json
import os
import sys
from argparse import Namespace

import pytest

from biomcp import cli
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

ENV_PROBE_SERVER_CODE = """
import os
from mcp.server.mcpserver import MCPServer
mcp = MCPServer('broker-env-fixture')
@mcp.tool()
def env_present(name: str) -> dict:
    return {'present': name in os.environ}
mcp.run()
"""

SECRET_ECHO_SERVER_CODE = """
from mcp.server.mcpserver import MCPServer
mcp = MCPServer('broker-secret-fixture')
@mcp.tool()
def reveal(value: str) -> dict:
    return {'value': value}
mcp.run()
"""


def _config(*tools: str) -> MCPBrokerConfig:
    return MCPBrokerConfig(command=(sys.executable, "-c", SERVER_CODE), allowed_executables=frozenset({os.path.realpath(sys.executable)}), allowed_tools=frozenset(tools), timeout_seconds=10, max_result_bytes=1024 * 1024)


def test_real_mcp_client_session_discovers_and_calls_allowlisted_tool():
    broker = MCPToolBroker(_config("echo"))
    tools = broker.list_tools()
    assert [tool["name"] for tool in tools] == ["echo"]
    assert tools[0]["inputSchema"]
    result = broker.call_tool("echo", {"value": "scientific"})
    assert result["is_error"] is False
    assert result["content"]
    assert result["content"][0]["type"] == "text"
    assert json.loads(result["content"][0]["text"])["value"] == "scientific"


def test_real_mcp_client_exposes_negotiated_server_metadata():
    broker = MCPToolBroker(_config("echo"))
    metadata = broker.server_metadata()
    assert metadata["protocol_version"]
    assert metadata["server_info"]["name"] == "broker-fixture"
    assert isinstance(metadata["capabilities"], dict)
    assert metadata["instructions"] is None


def test_server_metadata_is_bounded_by_broker_result_limit():
    broker = MCPToolBroker(_config("echo"))
    broker.config = MCPBrokerConfig(
        command=broker.config.command,
        allowed_executables=broker.config.allowed_executables,
        allowed_tools=broker.config.allowed_tools,
        timeout_seconds=broker.config.timeout_seconds,
        max_result_bytes=1,
        child_env=broker.config.child_env,
    )
    with pytest.raises(RuntimeError, match="server metadata exceeds"):
        broker.server_metadata()


def test_tool_catalog_is_bounded_by_broker_result_limit():
    broker = MCPToolBroker(_config("echo"))
    broker.config = MCPBrokerConfig(
        command=broker.config.command,
        allowed_executables=broker.config.allowed_executables,
        allowed_tools=broker.config.allowed_tools,
        timeout_seconds=broker.config.timeout_seconds,
        max_result_bytes=1,
        child_env=broker.config.child_env,
    )
    with pytest.raises(RuntimeError, match="tool catalog exceeds"):
        broker.list_tools()


def test_server_metadata_is_bounded_by_broker_timeout(monkeypatch: pytest.MonkeyPatch):
    broker = MCPToolBroker(_config("echo"))

    async def slow_metadata():
        await asyncio.sleep(2)
        return {}

    monkeypatch.setattr(broker, "_server_metadata", slow_metadata)
    broker.config = MCPBrokerConfig(
        command=broker.config.command,
        allowed_executables=broker.config.allowed_executables,
        allowed_tools=broker.config.allowed_tools,
        timeout_seconds=1,
        max_result_bytes=broker.config.max_result_bytes,
        child_env=broker.config.child_env,
    )

    with pytest.raises((TimeoutError, asyncio.TimeoutError)):
        broker.server_metadata()


def test_live_schema_rejects_invalid_arguments():
    broker = MCPToolBroker(_config("echo"))
    with pytest.raises(ValueError, match="schema validation"):
        broker.call_tool("echo", {"unexpected": "blocked"})


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


@pytest.mark.parametrize("key", ["PATH", "PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "PYTHONINSPECT", "PYTHONSTARTUP", "PYTHONBREAKPOINT", "PYTHONWARNINGS", "NODE_OPTIONS", "NODE_PATH", "RUBYOPT", "PERL5OPT", "BASH_ENV", "ENV"])
def test_config_rejects_child_environment_security_overrides(key):
    with pytest.raises(ValueError, match=f"cannot override {key}"):
        MCPBrokerConfig(command=(sys.executable,), allowed_executables=frozenset({os.path.realpath(sys.executable)}), allowed_tools=frozenset({"echo"}), child_env=((key, "/unsafe"),))


def test_config_rejects_command_not_in_allowlist():
    with pytest.raises(ValueError, match="command executable is not allowlisted"):
        MCPToolBroker(MCPBrokerConfig(command=(sys.executable,), allowed_executables=frozenset({os.path.realpath("/bin/false")}), allowed_tools=frozenset({"echo"})))


def test_config_rejects_empty_policy():
    with pytest.raises(ValueError, match="allowed executable"):
        MCPBrokerConfig(command=(sys.executable,), allowed_executables=frozenset(), allowed_tools=frozenset({"echo"}))
    with pytest.raises(ValueError, match="allowed tool"):
        MCPBrokerConfig(command=(sys.executable,), allowed_executables=frozenset({os.path.realpath(sys.executable)}), allowed_tools=frozenset())


def test_downstream_mcp_child_does_not_inherit_parent_environment_secrets(monkeypatch):
    monkeypatch.setenv("BIOMCP_TEST_PARENT_SECRET", "must-not-cross-process-boundary")
    config = MCPBrokerConfig(command=(sys.executable, "-c", ENV_PROBE_SERVER_CODE), allowed_executables=frozenset({os.path.realpath(sys.executable)}), allowed_tools=frozenset({"env_present"}), timeout_seconds=10, max_result_bytes=1024 * 1024)
    broker = MCPToolBroker(config)
    result = broker.call_tool("env_present", {"name": "BIOMCP_TEST_PARENT_SECRET"})
    assert json.loads(result["content"][0]["text"])["present"] is False


def test_child_environment_secret_is_redacted_even_when_short():
    config = MCPBrokerConfig(
        command=(sys.executable, "-c", SECRET_ECHO_SERVER_CODE),
        allowed_executables=frozenset({os.path.realpath(sys.executable)}),
        allowed_tools=frozenset({"reveal"}),
        child_env=(("BIOMCP_TEST_SECRET", "short"),),
        timeout_seconds=10,
        max_result_bytes=1024 * 1024,
    )
    broker = MCPToolBroker(config)
    result = broker.call_tool("reveal", {"value": "short"})
    assert "short" not in json.dumps(result)
    assert "[REDACTED]" in json.dumps(result)


def test_install_verify_blocks_client_configuration_when_readiness_fails(monkeypatch):
    events: list[str] = []
    monkeypatch.setattr(cli, "_install_selected", lambda names, dry_run=False: events.append("install"))
    monkeypatch.setattr(cli, "_verify_installed", lambda names: events.append("verify") or 1)
    monkeypatch.setattr(cli, "_server_configs", lambda names: events.append("configs") or {})
    args = Namespace(all=False, servers="bioimage", clients="none", dry_run=False, verify=True)

    assert cli.cmd_install(args) == 1
    assert events == ["install", "verify"]


def test_install_verify_allows_client_configuration_after_readiness_passes(monkeypatch):
    events: list[str] = []
    monkeypatch.setattr(cli, "_install_selected", lambda names, dry_run=False: events.append("install"))
    monkeypatch.setattr(cli, "_verify_installed", lambda names: events.append("verify") or 0)
    monkeypatch.setattr(cli, "_server_configs", lambda names: events.append("configs") or {})
    args = Namespace(all=False, servers="bioimage", clients="none", dry_run=False, verify=True)

    assert cli.cmd_install(args) == 0
    assert events == ["install", "verify", "configs"]
