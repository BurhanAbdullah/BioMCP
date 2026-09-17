"""Read-only live metadata discovery for registered BioMCP servers."""
from __future__ import annotations

import asyncio
from typing import Any

from mcp import Client, StdioServerParameters

from .registry import get_server


def _parameters(server: str) -> StdioServerParameters:
    entry = get_server(server)
    if not entry.get("installable"):
        raise ValueError(f"{server} is not installable and cannot be inspected")
    command = entry.get("command")
    args = entry.get("args", [])
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"Server {server} has no executable command")
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ValueError(f"Server {server} has invalid command arguments")
    configured = entry.get("config", [])
    if not isinstance(configured, list) or not all(isinstance(name, str) for name in configured):
        raise ValueError(f"Server {server} has invalid environment configuration")
    import os
    env = {"PATH": os.environ.get("PATH", "")}
    for name in configured:
        if name in os.environ:
            env[name] = os.environ[name]
    return StdioServerParameters(command=command, args=args, env=env)


async def _discover(server: str) -> dict[str, Any]:
    async with Client(_parameters(server)) as client:
        return {
            "protocol_version": client.protocol_version,
            "server_info": client.server_info.model_dump(mode="json") if client.server_info else None,
            "capabilities": client.server_capabilities.model_dump(mode="json") if client.server_capabilities else None,
            "instructions": client.instructions,
        }


def discover_server_metadata(server: str) -> dict[str, Any]:
    """Perform a live MCP initialization handshake and return server metadata.

    This operation is read-only: it does not list or execute scientific tools and
    does not modify the downstream server or local configuration.
    """
    return asyncio.run(_discover(server))
