"""BioMCP model runtime MCP server.

The MCP surface exposes model discovery and generation while provider
transport, capability metadata and request validation live in
``biomcp.llm``.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import MCPServer

from biomcp.llm import OpenAICompatibleProvider


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

        Structured output and tool definitions are passed through to providers
        that support the OpenAI compatible Responses interface. Returned tool
        calls are data at this layer and are not executed automatically.
        """
        chosen = model or default_model
        if not chosen:
            raise ValueError("Provide model or set BIOMCP_LLM_MODEL")
        return provider.complete(
            model=chosen,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format=response_format,
            tools=tools,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
