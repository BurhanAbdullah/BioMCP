"""BioMCP model runtime MCP server.

The MCP surface exposes model discovery, generation, and an explicitly
allowlisted downstream MCP tool broker. Provider transport and capability
metadata remain in ``biomcp.llm`` while downstream scientific engines stay
independent from the gateway.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import MCPServer

from biomcp.http import create_streamable_http_app
from biomcp.llm import OpenAICompatibleProvider
from biomcp.mcp_broker import MCPToolBroker, broker_config_from_environment


def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-LLM")
    provider_name = os.getenv("BIOMCP_LLM_PROVIDER", "openai-compatible")
    provider = OpenAICompatibleProvider.from_environment(provider_name)
    default_model = os.getenv("BIOMCP_LLM_MODEL")

    @mcp.tool()
    def list_models() -> dict[str, Any]:
        """List models exposed by the configured provider endpoint."""
        return provider.list_models()

    @mcp.tool()
    def complete(prompt: str, model: str | None = None, system: str = "You are a careful scientific assistant.", temperature: float | None = None, max_output_tokens: int | None = None, response_format: dict[str, Any] | None = None, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Generate through the configured provider; returned tool calls are not executed automatically."""
        chosen = model or default_model
        if not chosen:
            raise ValueError("Provide model or set BIOMCP_LLM_MODEL")
        return provider.complete(model=chosen, input=[{"role": "system", "content": system}, {"role": "user", "content": prompt}], response_format=response_format, tools=tools, temperature=temperature, max_output_tokens=max_output_tokens)

    @mcp.tool()
    def provider_capabilities() -> dict[str, Any]:
        """Return the configured provider identity and advertised capabilities."""
        capabilities = provider.config.capabilities
        return {
            "provider": provider.config.name,
            "base_url": provider.config.base_url,
            "capabilities": {
                "model_discovery": capabilities.model_discovery,
                "chat": capabilities.chat,
                "responses": capabilities.responses,
                "streaming": capabilities.streaming,
                "structured_output": capabilities.structured_output,
                "tool_calling": capabilities.tool_calling,
            },
        }

    @mcp.tool()
    def mcp_capabilities() -> dict[str, Any]:
        """Discover the downstream MCP server and explicitly allowlisted tools."""
        broker = MCPToolBroker(broker_config_from_environment())
        return {
            "server": broker.server_metadata(),
            "tools": broker.list_tools(),
        }

    @mcp.tool()
    def mcp_call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke one explicitly allowlisted downstream MCP tool."""
        broker = MCPToolBroker(broker_config_from_environment())
        return broker.call_tool(name, arguments)

    return mcp


def create_http_app() -> Any:
    """Create the LLM MCP ASGI app for horizontally scaled deployment.

    Configure ``BIOMCP_HTTP_ALLOWED_HOSTS`` before starting the app and use
    an ASGI process manager such as Uvicorn to provide multiple workers.
    """
    return create_streamable_http_app(create_server())


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
