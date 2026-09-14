# BioMCP LLM Gateway

The LLM Gateway is an interoperability component. It does not implement scientific algorithms and does not replace independent scientific engines such as BioNuclei.

## Provider transport

The gateway currently uses an OpenAI-compatible transport abstraction for:

- `openai-compatible`
- `ollama`
- `vllm`
- custom HTTP(S) endpoints through `BIOMCP_LLM_BASE_URL`

Provider profiles declare model discovery, chat, Responses, streaming, structured output, and tool-calling capabilities. Unsupported capabilities are rejected before a provider request is sent.

Transport controls include:

- HTTP(S)-only endpoints
- rejection of embedded endpoint credentials
- disabled redirects
- bounded request timeout
- bounded response size
- bounded transient retries
- sanitized HTTP and network errors
- provider credentials supplied from environment variables rather than registry metadata

## MCP tool broker

The gateway exposes two additional MCP tools when a downstream MCP server is explicitly configured:

- `mcp_capabilities`
- `mcp_call_tool`

The broker uses the official MCP `ClientSession` and `stdio_client` interfaces. It does not import or invoke downstream scientific implementations directly.

Downstream execution is disabled unless all of the following are configured:

```text
BIOMCP_MCP_SERVER_COMMAND
BIOMCP_MCP_ALLOWED_EXECUTABLES
BIOMCP_MCP_ALLOWED_TOOLS
```

Optional controls are:

```text
BIOMCP_MCP_TOOL_TIMEOUT_SECONDS
BIOMCP_MCP_MAX_RESULT_BYTES
BIOMCP_MCP_SERVER_ENV_JSON
```

`BIOMCP_MCP_SERVER_COMMAND` is a JSON string array. The first element must resolve on `PATH` and its real path must be present in `BIOMCP_MCP_ALLOWED_EXECUTABLES`. Tool names are checked against `BIOMCP_MCP_ALLOWED_TOOLS` before invocation.

The broker also enforces an operation timeout and a maximum serialized result size. Child process environment is restricted to `PATH` plus the explicitly supplied `BIOMCP_MCP_SERVER_ENV_JSON` entries.

This design makes downstream MCP execution an explicit policy decision rather than an automatic consequence of an LLM returning a tool call.

## Example configuration

A local test server can be exposed through an explicitly allowlisted executable:

```text
BIOMCP_MCP_SERVER_COMMAND=["/absolute/path/to/server", "--stdio"]
BIOMCP_MCP_ALLOWED_EXECUTABLES=["/absolute/path/to/server"]
BIOMCP_MCP_ALLOWED_TOOLS=["inspect_image", "read_provenance"]
BIOMCP_MCP_TOOL_TIMEOUT_SECONDS=30
BIOMCP_MCP_MAX_RESULT_BYTES=2097152
```

Credentials for the model provider and credentials needed by a downstream scientific server should not be placed in registry metadata. They should be supplied through the runtime environment appropriate to that server.

## Validation

The broker has deterministic security tests and an actual MCP protocol round trip using `ClientSession` and `stdio_client`. Repository CI additionally validates the package, registry, and installed-artifact paths before a change is merged.

No external OpenAI, Ollama, vLLM, or scientific-engine deployment is implied by these tests. External integrations require separate environment-specific validation.
