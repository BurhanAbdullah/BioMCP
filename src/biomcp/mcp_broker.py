"""Controlled downstream MCP tool discovery and execution."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from mcp import Client, StdioServerParameters


_BLOCKED_CHILD_ENV_KEYS = frozenset(
    {
        "PATH",
        "PYTHONPATH",
        "PYTHONHOME",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "DYLD_INSERT_LIBRARIES",
        "DYLD_LIBRARY_PATH",
    }
)


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
            if key in _BLOCKED_CHILD_ENV_KEYS:
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
    return MCPBrokerConfig(tuple(command), frozenset(allowed_resolved), frozenset(tools), timeout, max_bytes, child_env)


def _run(coro):
    return asyncio.run(coro)


def _model_field(value: Any, *names: str) -> Any:
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _redact_child_secrets(value: Any, secrets: frozenset[str]) -> Any:
    """Recursively remove configured child-environment secret values from results."""
    if not secrets:
        return value
    if isinstance(value, str):
        redacted = value
        for secret in secrets:
            if len(secret) >= 8 and secret in redacted:
                redacted = redacted.replace(secret, "[REDACTED]")
        return redacted
    if isinstance(value, list):
        return [_redact_child_secrets(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_child_secrets(item, secrets) for item in value)
    if isinstance(value, dict):
        return {key: _redact_child_secrets(item, secrets) for key, item in value.items()}
    return value


class MCPToolBroker:
    """Discover and invoke an explicitly allowlisted downstream MCP server."""
    def __init__(self, config: MCPBrokerConfig):
        self.config = config
        resolved = os.path.realpath(shutil.which(config.command[0]) or config.command[0])
        allowed = {os.path.realpath(path) for path in config.allowed_executables}
        if resolved not in allowed:
            raise ValueError("MCP broker command executable is not allowlisted")

    def _parameters(self) -> StdioServerParameters:
        env = {"PATH": os.environ.get("PATH", "")}
        env.update(dict(self.config.child_env))
        return StdioServerParameters(command=self.config.command[0], args=list(self.config.command[1:]), env=env)

    @staticmethod
    def _schema(tool: Any) -> dict[str, Any]:
        schema = _model_field(tool, "input_schema", "inputSchema")
        schema = _json_safe(schema)
        if not isinstance(schema, dict):
            raise RuntimeError("MCP server returned an invalid input schema")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise RuntimeError("MCP server returned an invalid input schema") from exc
        return schema

    async def _server_metadata(self) -> dict[str, Any]:
        async with Client(self._parameters()) as client:
            return {
                "protocol_version": client.protocol_version,
                "capabilities": _json_safe(client.server_capabilities),
                "server_info": _json_safe(client.server_info),
                "instructions": client.instructions,
            }

    async def _list_tools(self) -> list[dict[str, Any]]:
        async with Client(self._parameters()) as client:
            result = await asyncio.wait_for(client.session.list_tools(), timeout=self.config.timeout_seconds)
            tools = []
            for tool in result.tools:
                if tool.name in self.config.allowed_tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": self._schema(tool),
                    })
            return tools

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.config.allowed_tools:
            raise RuntimeError("MCP tool is not allowlisted")
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be an object")

        validation_error: Exception | None = None
        payload: dict[str, Any] | None = None
        async with Client(self._parameters()) as client:
            result = await asyncio.wait_for(client.session.list_tools(), timeout=self.config.timeout_seconds)
            advertised = next((tool for tool in result.tools if tool.name == name), None)
            if advertised is None:
                validation_error = RuntimeError("MCP tool is not advertised by the downstream server")
            else:
                schema = self._schema(advertised)
                validator = Draft202012Validator(schema)
                errors = sorted(validator.iter_errors(arguments), key=lambda error: list(error.path))
                if errors:
                    detail = "; ".join(error.message for error in errors[:3])
                    validation_error = ValueError(f"MCP tool arguments failed schema validation: {detail}")
                else:
                    result = await asyncio.wait_for(client.session.call_tool(name, arguments), timeout=self.config.timeout_seconds)
                    structured = _model_field(result, "structured_content", "structuredContent")
                    structured = _json_safe(structured)
                    content = [_json_safe(item) for item in result.content]
                    secrets = frozenset(value for _, value in self.config.child_env if value)
                    structured = _redact_child_secrets(structured, secrets)
                    content = _redact_child_secrets(content, secrets)
                    payload = {
                        "is_error": bool(result.is_error),
                        "content": content,
                        "structured_content": structured,
                    }
                    encoded = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
                    if len(encoded) > self.config.max_result_bytes:
                        validation_error = RuntimeError("MCP tool result exceeds configured result limit")

        if validation_error is not None:
            raise validation_error
        assert payload is not None
        return payload

    def server_metadata(self) -> dict[str, Any]:
        return _run(asyncio.wait_for(self._server_metadata(), timeout=self.config.timeout_seconds))

    def list_tools(self) -> list[dict[str, Any]]:
        return _run(self._list_tools())

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return _run(self._call_tool(name, arguments))
