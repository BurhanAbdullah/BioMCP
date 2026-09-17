"""Controlled MCP client operations for registered BioMCP servers."""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from mcp import Client, StdioServerParameters

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
    configured = entry.get("config", [])
    if not isinstance(configured, list) or not all(isinstance(name, str) for name in configured):
        raise ValueError(f"Server {server} has invalid environment configuration")
    env = {"PATH": os.environ.get("PATH", "")}
    for name in configured:
        if name in os.environ:
            env[name] = os.environ[name]
    return StdioServerParameters(command=command, args=args, env=env)


def _declared_tool(server: str, tool: str) -> None:
    entry = get_server(server)
    declared = entry.get("tools", [])
    if tool not in declared:
        raise ValueError(f"Tool {tool!r} is not declared for registered server {server!r}")


def _tool_schema(tool: Any) -> dict[str, Any]:
    schema = getattr(tool, "inputSchema", None)
    if schema is None:
        schema = getattr(tool, "input_schema", None)
    if not isinstance(schema, dict):
        raise ValueError(f"MCP tool {tool.name!r} did not provide a valid input schema")
    return schema


def _validate_tool_arguments(tool: Any, arguments: dict[str, Any]) -> None:
    schema = _tool_schema(tool)
    try:
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(arguments), key=lambda error: list(error.path))
    except SchemaError as exc:
        raise ValueError(f"MCP tool {tool.name!r} advertised an invalid input schema") from exc
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "$"
        raise ValueError(f"invalid arguments for tool {tool.name!r} at {path}: {error.message}")


async def _discover_tools(server: str) -> list[dict[str, Any]]:
    params = _server_parameters(server)
    async with Client(params) as client:
        result = await client.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": _tool_schema(tool),
            }
            for tool in result.tools
        ]


async def _call_tool(server: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    _declared_tool(server, tool)
    params = _server_parameters(server)
    async with Client(params) as client:
        listed = await client.list_tools()
        live_tool = next((item for item in listed.tools if item.name == tool), None)
        if live_tool is None:
            raise ValueError(f"Tool {tool!r} is not advertised by registered server {server!r}")
        _validate_tool_arguments(live_tool, arguments)
        result = await client.call_tool(tool, arguments)
        response: dict[str, Any] = {"is_error": bool(result.is_error)}
        if result.structured_content is not None:
            response["structured_content"] = result.structured_content
        response["content"] = [item.model_dump(mode="json") for item in result.content]
        return response


def discover_tools(server: str) -> list[dict[str, Any]]:
    return asyncio.run(_discover_tools(server))


def call_tool(server: str, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a JSON object")
    return asyncio.run(_call_tool(server, tool, arguments))


def json_arguments(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON arguments: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("tool arguments must be a JSON object")
    return parsed
