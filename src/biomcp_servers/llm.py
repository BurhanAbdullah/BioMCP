"""BioMCP model runtime MCP server.

The MCP surface remains deliberately small while the transport and provider
logic moves into ``biomcp.gateway``. This keeps protocol handling separate from
provider transport and makes the gateway independently testable.
"""
from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from biomcp.gateway import OpenAICompatibleProvider


def create_server() -> MCPServer:
    mcp = MCPServer("BioMCP-LLM")
    provider = OpenAICompatibleProvider()

    @mcp.tool()
    def list_models() -> dict[str, Any]:
        """List models exposed by the configured OpenAI compatible endpoint."""
        return provider.list_models()

    @mcp.tool()
    def complete(
        prompt: str,
        model: str | None = None,
        system: str = "You are a careful scientific assistant.",
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate a response through the configured model provider.

        ``response_format`` and ``tools`` are passed through only when the
        configured provider supports the corresponding OpenAI compatible
        interface. BioMCP does not execute returned tool calls in this layer.
        """
        return provider.complete(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_format=response_format,
            tools=tools,
        )

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
