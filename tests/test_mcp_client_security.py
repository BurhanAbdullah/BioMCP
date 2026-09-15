import asyncio
import json

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from biomcp.mcp_client import _server_parameters


ENV_PROBE_SERVER_CODE = """
import os
from mcp.server.mcpserver import MCPServer
mcp = MCPServer('client-env-probe')
@mcp.tool()
def env_present(name: str) -> dict:
    return {'present': name in os.environ}
mcp.run()
"""


def test_server_parameters_allow_only_registered_configuration(monkeypatch):
    monkeypatch.setenv("BIOMCP_TEST_PARENT_SECRET", "must-not-cross-process-boundary")
    monkeypatch.setenv("BIOMCP_ALLOWED_SETTING", "allowed")
    monkeypatch.setattr(
        "biomcp.mcp_client.get_server",
        lambda _: {
            "installable": True,
            "command": "python",
            "args": [],
            "config": ["BIOMCP_ALLOWED_SETTING"],
        },
    )
    params = _server_parameters("fixture")
    assert params.env["BIOMCP_ALLOWED_SETTING"] == "allowed"
    assert "BIOMCP_TEST_PARENT_SECRET" not in params.env
    assert "PATH" in params.env


def test_mcp_stdio_child_does_not_receive_parent_secret(monkeypatch):
    monkeypatch.setenv("BIOMCP_TEST_PARENT_SECRET", "must-not-cross-process-boundary")
    monkeypatch.setattr(
        "biomcp.mcp_client.get_server",
        lambda _: {
            "installable": True,
            "command": "python",
            "args": ["-c", ENV_PROBE_SERVER_CODE],
            "config": [],
            "tools": ["env_present"],
        },
    )

    async def run_probe():
        params = _server_parameters("fixture")
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "env_present", {"name": "BIOMCP_TEST_PARENT_SECRET"}
                )
                return json.loads(result.content[0].text)["present"]

    assert asyncio.run(run_probe()) is False
