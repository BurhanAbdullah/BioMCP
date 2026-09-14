"""Controlled MCP client operations for registered BioMCP servers.

The client uses the machine readable registry as a policy boundary. Only
installable servers may be launched and only tools declared by the registry
may be invoked through this module.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .registry import get_server


def _server_parameters(server: str) -> StdioServerParameters:
    entry = get_server(server)
    if not entry.get("installable"):
        raise ValueError(f"{server} is not installable and cannot be launched by the BioMCP client")
    command = entry.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"Server {server} has no executable command")
    args = entry.get("args", [])
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ValueError(f"Server {server} has invalid command arguments")
    return StdioServerParameters(command=command, args=args, env=dict(os.environ))


def _declared_tool(server: str, tool: str) -> None:
    entry = get_server(server)
    declared = entry.get("tools", [])
    if tool not in declared:
        raise ValueError(f"Tool {tool!r} is not declared for registered server {server!r}")


async def _discover_tools(server: str) -> list[dict[str, Any]]:
    params = _server_parameters(server)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in result.tools
            ]


async def _call_tool(server: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    _declared_tool(server, tool)
    params = _server_parameters(server)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)
            response: dict[str, Any] = {"is_error": bool(result.is_error)}
            if result.structured_content is not None:
                response["structured_content"] = result.structured_content
            response["content"] = [item.model_dump(mode="json") for item in result.content]
            return response


def discover_tools(server: str) -> list[dict[str, Any]]:
    """Discover tools from a registered local MCP server."""
    return asyncio.run(_discover_tools(server))


def call_tool(server: str, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Invoke a registry-declared tool on a registered local MCP server."""
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a JSON object")
    return asyncio.run(_call_tool(server, tool, arguments))


def json_arguments(value: str) -> dict[str, Any]:
    """Parse CLI JSON arguments and require an object."""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON arguments: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("tool arguments must be a JSON object")
    return parsed
