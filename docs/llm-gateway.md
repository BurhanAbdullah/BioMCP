# BioMCP LLM Gateway

The LLM Gateway is an interoperability component. It does not implement scientific algorithms and does not replace independent scientific engines such as BioNuclei.

## Provider transport

The gateway currently uses an OpenAI-compatible transport abstraction for `openai-compatible`, `ollama`, `vllm`, and custom HTTP(S) endpoints through `BIOMCP_LLM_BASE_URL`. Provider profiles declare model discovery, chat, Responses, streaming, structured output, and tool-calling capabilities. Unsupported capabilities are rejected before a provider request is sent.

## Bounded transport controls

Transport controls include HTTP(S)-only endpoints, rejection of embedded endpoint credentials, disabled redirects, bounded request timeout, bounded response size, bounded transient retries, sanitized HTTP/network errors, and provider credentials supplied from environment variables rather than registry metadata.

The retry controls can be configured with:

```bash
export BIOMCP_LLM_TIMEOUT_SECONDS=120
export BIOMCP_LLM_MAX_RESPONSE_BYTES=8388608
export BIOMCP_LLM_MAX_RETRIES=1
export BIOMCP_LLM_RETRY_BACKOFF_SECONDS=0
```

`BIOMCP_LLM_MAX_RETRIES` is bounded to `0..3`. `BIOMCP_LLM_RETRY_BACKOFF_SECONDS` is bounded to `0..30` seconds and uses bounded exponential progression. Numeric provider `Retry-After` hints are honored and capped at 30 seconds; malformed or negative hints fall back to configured exponential backoff.

Retries are limited to transient HTTP statuses (`408`, `429`, `500`, `502`, `503`, `504`) and transient transport failures. For streaming requests, retry is allowed only before the first event is delivered. After output has been yielded, reconnecting could duplicate generated output, so later failures are surfaced instead.

Per-call retry overrides remain bounded to `0..3` and take precedence over the configured default.

## Response and usage normalization

The gateway preserves provider response payloads while adding provider-neutral `_biomcp.usage` metadata when token usage is available. Common Chat Completions and Responses usage field names are normalized without replacing the original provider payload. Streaming events receive the same normalization when usage information is present.

## Credential boundary

API credentials are read from environment variables and kept outside provider configuration metadata. Endpoint URLs containing embedded username/password credentials are rejected. HTTP redirects are disabled so an authenticated request cannot be transparently redirected to another endpoint.

## MCP tool broker

The gateway exposes `mcp_capabilities` and `mcp_call_tool` when a downstream MCP server is explicitly configured. The broker uses the official MCP `ClientSession` and `stdio_client` interfaces and does not import downstream scientific implementations directly.

Downstream execution requires all of `BIOMCP_MCP_SERVER_COMMAND`, `BIOMCP_MCP_ALLOWED_EXECUTABLES`, and `BIOMCP_MCP_ALLOWED_TOOLS`. Optional controls are `BIOMCP_MCP_TOOL_TIMEOUT_SECONDS`, `BIOMCP_MCP_MAX_RESULT_BYTES`, and `BIOMCP_MCP_SERVER_ENV_JSON`. The command is a JSON string array; its resolved executable must be in the executable allowlist. Tool names are checked against the tool allowlist before invocation.

The broker enforces operation timeouts and serialized result-size limits. Child process environment is restricted to `PATH` plus explicitly supplied variables; `PATH`, `PYTHONPATH`, and `PYTHONHOME` cannot be overridden.

## Validation

Gateway behavior is covered by deterministic tests for capability enforcement, request construction, response and usage normalization, streaming semantics, response-size limits, retry bounds, exponential backoff, provider `Retry-After` handling, and credential/endpoint protections. The broker is also covered by deterministic security tests and a real MCP protocol round trip using `ClientSession` and `stdio_client`. Package-consumer CI exercises installed wheel and source-distribution artifacts.

External OpenAI, Ollama, vLLM, custom-provider, and scientific-engine deployments require separate environment-specific validation and are not implied by repository tests.
