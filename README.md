# BioMCP

**The open MCP platform for biology, bioinformatics, bioimaging, and scientific AI.**

BioMCP follows a PowerMCP-style architecture: one installable distribution, one machine-readable registry, independent MCP servers, client configuration, diagnostics, tests, and a documentation site. The registry states what is installable, experimental, planned, or externally provided.

## Server families

**BioImage** — local image inspection, intensity summaries, and thresholding primitives.

**ImageJ / Fiji** — bridge to an explicitly configured local ImageJ/Fiji installation.

**LLM** — OpenAI-compatible model access for agent workflows using environment-provided credentials.

**BioNuclei** — validated external scientific MCP adapter; BioMCP does not duplicate its scientific engine.

**CellProfiler** — planned adapter; not advertised as installable until an executable, tested integration exists.

## Quick start

```bash
pip install biomcp
biomcp list
biomcp install --servers bioimage --clients generic
biomcp doctor
```

Image-analysis dependencies:

```bash
pip install 'biomcp[bioimage]'
```

## Launch servers

```bash
biomcp run bioimage
biomcp run imagej
biomcp run llm
```

Each server is independently launchable over stdio, following the modular server-factory pattern used by PowerMCP.

## Configure AI hosts

```bash
biomcp install --servers bioimage,imagej,llm --clients claude-desktop
biomcp install --servers bioimage,llm --clients codex
```

Use `--dry-run` to inspect changes before writing client configuration.

## Local configuration

`BIOMCP_IMAGEJ_EXECUTABLE` points to ImageJ/Fiji.

`BIOMCP_LLM_BASE_URL`, `BIOMCP_LLM_API_KEY`, and `BIOMCP_LLM_MODEL` configure the LLM bridge. `OPENAI_API_KEY` is accepted as an API-key fallback.

## Scientific boundary

BioMCP transports typed tool calls. It does not invent scientific measurements, benchmarks, or validation claims. Scientific computation remains under the authority of the underlying server.

## Website

The product site lives in `docs/` and is published by GitHub Pages.

## Contributing

A new integration needs an executable server, registry metadata, tests, documentation, client configuration, and an explicit validation state before being promoted to installable or validated.

## License

MIT.
