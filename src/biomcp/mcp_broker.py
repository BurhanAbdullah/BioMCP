"""Controlled downstream MCP tool discovery and execution.

The broker is intentionally opt-in. A server command, executable allowlist,
and tool allowlist must all be configured before a downstream MCP server can
be reached. The broker uses the official MCP ClientSession/stdio_client
transport rather than invoking tool implementations directly.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass(frozen=True)
class MCPBrokerConfig:
    command: tuple[str, ...]
    allowed_executables: frozenset[str]
    allowed_tools: frozenset[str]
    timeout_seconds: float = 30.0
    max_result_bytes: int = 2 * 1024 * 1024
    child_env: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.command or not all(isinstance(item, str) and item for item in self.command):
            raise ValueError("MCP broker command must be a non-empty string tuple")
        if not self.allowed_executables:
            raise ValueError("MCP broker requires at least one allowed executable")
        if not self.allowed_tools:
            raise ValueError("MCP broker requires at least one allowed tool")
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("MCP broker timeout_seconds must be 1..300")
        if not 1 <= self.max_result_bytes <= 64 * 1024 * 1024:
            raise ValueError("MCP broker max_result_bytes must be 1..67108864")
        for key, value in self.child_env:
            if not isinstance(key, str) or not isinstance(value, str) or not key:
                raise ValueError("MCP broker child_env must contain string key/value pairs")
            if key in {"PATH", "PYTHONPATH", "PYTHONHOME"}:
                raise ValueError(f"MCP broker child_env cannot override {key}")


def _json_list(name: str) -> list[Any]:
    raw = os.getenv(name)
    if not raw:
        raise RuntimeError(f"Set {name} to enable controlled MCP execution")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} must contain a JSON array") from exc
    if not isinstance(value, list):
        raise RuntimeError(f"{name} must contain a JSON array")
    return value


def broker_config_from_environment() -> MCPBrokerConfig:
    command = _json_list("BIOMCP_MCP_SERVER_COMMAND")
    if not command or not all(isinstance(item, str) and item for item in command):
        raise RuntimeError("BIOMCP_MCP_SERVER_COMMAND must be a non-empty JSON string array")

    allowed = _json_list("BIOMCP_MCP_ALLOWED_EXECUTABLES")
    if not allowed or not all(isinstance(item, str) and item for item in allowed):
        raise RuntimeError("BIOMCP_MCP_ALLOWED_EXECUTABLES must be a non-empty JSON string array")

    tools = _json_list("BIOMCP_MCP_ALLOWED_TOOLS")
    if not tools or not all(isinstance(item, str) and item for item in tools):
        raise RuntimeError("BIOMCP_MCP_ALLOWED_TOOLS must be a non-empty JSON string array")

    try:
        timeout = float(os.getenv("BIOMCP_MCP_TOOL_TIMEOUT_SECONDS", "30"))
        max_bytes = int(os.getenv("BIOMCP_MCP_MAX_RESULT_BYTES", str(2 * 1024 * 1024)))
    except ValueError as exc:
        raise RuntimeError("MCP broker limits must be numeric") from exc
    if not 1 <= timeout <= 300:
        raise RuntimeError("BIOMCP_MCP_TOOL_TIMEOUT_SECONDS must be 1..300")
    if not 1 <= max_bytes <= 64 * 1024 * 1024:
        raise RuntimeError("BIOMCP_MCP_MAX_RESULT_BYTES must be 1..67108864")

    child_env: tuple[tuple[str, str], ...] = ()
    raw_env = os.getenv("BIOMCP_MCP_SERVER_ENV_JSON")
    if raw_env:
        try:
            value = json.loads(raw_env)
        except json.JSONDecodeError as exc:
            raise RuntimeError("BIOMCP_MCP_SERVER_ENV_JSON must contain a JSON object") from exc
        if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            raise RuntimeError("BIOMCP_MCP_SERVER_ENV_JSON must contain a string-to-string JSON object")
        child_env = tuple(sorted(value.items()))

    executable = shutil.which(command[0])
    if executable is None:
        raise RuntimeError("configured MCP server executable was not found on PATH")
    resolved = os.path.realpath(executable)
    allowed_resolved = {os.path.realpath(path) for path in allowed}
    if resolved not in allowed_resolved:
        raise RuntimeError("configured MCP server executable is not in BIOMCP_MCP_ALLOWED_EXECUTABLES")

    return MCPBrokerConfig(
        command=tuple(command),
        allowed_executables=frozenset(allowed_resolved),
        allowed_tools=frozenset(tools),
        timeout_seconds=timeout,
        max_result_bytes=max_bytes,
        child_env=child_env,
    )


def _run(coro):
    """Run one async MCP operation from a synchronous MCP tool handler."""
    return asyncio.run(coro)


class MCPToolBroker:
    """Discover and invoke an explicitly allowlisted downstream MCP server."""

    def __init__(self, config: MCPBrokerConfig):
        self.config = config

    def _parameters(self) -> StdioServerParameters:
        env = {"PATH": os.environ.get("PATH", "")}
        env.update(dict(self.config.child_env))
        return StdioServerParameters(
            command=self.config.command[0],
            args=list(self.config.command[1:]),
            env=env,
        )

    async def _list_tools(self) -> list[dict[str, Any]]:
        async with stdio_client(self._parameters()) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=self.config.timeout_seconds)
                result = await asyncio.wait_for(session.list_tools(), timeout=self.config.timeout_seconds)
                tools = []
                for tool in result.tools:
                    if tool.name in self.config.allowed_tools:
                        schema = getattr(tool, "input_schema", None)
                        if schema is None:
                            schema = getattr(tool, "inputSchema", None)
                        if hasattr(schema, "model_dump"):
                            schema = schema.model_dump(mode="json")
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": schema,
                        })
                return tools

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.config.allowed_tools:
            raise RuntimeError("MCP tool is not allowlisted")
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be an object")
        async with stdio_client(self._parameters()) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=self.config.timeout_seconds)
                result = await asyncio.wait_for(session.call_tool(name, arguments), timeout=self.config.timeout_seconds)
                structured = result.structured_content
                if hasattr(structured, "model_dump"):
                    structured = structured.model_dump(mode="json")
                payload = {
                    "is_error": bool(result.is_error),
                    "content": [item.model_dump(mode="json") if hasattr(item, "model_dump") else str(item) for item in result.content],
                    "structured_content": structured,
                }
                encoded = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                if len(encoded) > self.config.max_result_bytes:
                    raise RuntimeError("MCP tool result exceeds configured result limit")
                return payload

    def list_tools(self) -> list[dict[str, Any]]:
        return _run(self._list_tools())

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return _run(self._call_tool(name, arguments))
