# BioMCP LLM Gateway

The LLM Gateway is an interoperability component. It does not implement scientific algorithms and does not replace independent scientific engines such as BioNuclei.

## Provider transport

The gateway currently uses an OpenAI-compatible transport abstraction for `openai-compatible`, `ollama`, `vllm`, and custom HTTP(S) endpoints through `BIOMCP_LLM_BASE_URL`. Provider profiles declare model discovery, chat, Responses, streaming, structured output, and tool-calling capabilities. Unsupported capabilities are rejected before a provider request is sent.

Transport controls include HTTP(S)-only endpoints, rejection of embedded endpoint credentials, disabled redirects, bounded request timeout, bounded response size, bounded transient retries, sanitized HTTP/network errors, and provider credentials supplied from environment variables rather than registry metadata.

## MCP tool broker

The gateway exposes `mcp_capabilities` and `mcp_call_tool` when a downstream MCP server is explicitly configured. The broker uses the official MCP `ClientSession` and `stdio_client` interfaces and does not import downstream scientific implementations directly.

Downstream execution requires all of `BIOMCP_MCP_SERVER_COMMAND`, `BIOMCP_MCP_ALLOWED_EXECUTABLES`, and `BIOMCP_MCP_ALLOWED_TOOLS`. Optional controls are `BIOMCP_MCP_TOOL_TIMEOUT_SECONDS`, `BIOMCP_MCP_MAX_RESULT_BYTES`, and `BIOMCP_MCP_SERVER_ENV_JSON`. The command is a JSON string array; its resolved executable must be in the executable allowlist. Tool names are checked against the tool allowlist before invocation.

The broker enforces operation timeouts and serialized result-size limits. Child process environment is restricted to `PATH` plus explicitly supplied variables; `PATH`, `PYTHONPATH`, and `PYTHONHOME` cannot be overridden.

## Validation

The broker is covered by deterministic security tests and a real MCP protocol round trip using `ClientSession` and `stdio_client`. External OpenAI, Ollama, vLLM, custom-provider, and scientific-engine deployments require separate environment-specific validation and are not implied by repository tests.
