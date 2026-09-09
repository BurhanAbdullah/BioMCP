# BioMCP

**The open MCP platform for biology, bioinformatics, bioimaging, and scientific AI.**

BioMCP follows the PowerMCP model: one installable distribution, one machine-readable registry, independent MCP servers, simple client configuration, diagnostics, tests, and a public documentation site. The registry is the source of truth for what is installable versus planned or externally provided. fileciteturn923file0L15-L59

## What is included

### Bioimage
Local image inspection, intensity summaries, and thresholding primitives.

### ImageJ / Fiji
A local-process bridge for explicitly configured ImageJ/Fiji installations.

### LLM
An OpenAI-compatible model bridge using environment-provided credentials.

### BioNuclei
A validated external scientific MCP server adapter. BioMCP does not duplicate BioNuclei's scientific implementation; it provides interoperability.

## Install

```bash
pip install biomcp
biomcp list
biomcp install --servers bioimage,imagej,llm --clients generic
biomcp doctor
```

For image analysis dependencies:

```bash
pip install 'biomcp[bioimage]'
```

## Run a server

```bash
biomcp run bioimage
biomcp run imagej
biomcp run llm
```

Each server is independently launchable over stdio, matching the modular server-factory pattern used in PowerMCP. fileciteturn943file0L7-L31

## Configure AI clients

```bash
biomcp install --servers bioimage --clients claude-desktop
biomcp install --servers bioimage,llm --clients codex
```

Use `--dry-run` to inspect generated configuration before writing it.

## Environment

`BIOMCP_IMAGEJ_EXECUTABLE` configures the ImageJ/Fiji executable.

`BIOMCP_LLM_BASE_URL`, `BIOMCP_LLM_API_KEY`, and `BIOMCP_LLM_MODEL` configure the LLM bridge. `OPENAI_API_KEY` is accepted as a fallback API-key variable.

## Scientific boundary

BioMCP is an interoperability layer. It routes typed calls to scientific software and returns structured results. It does not invent benchmark results or silently change a model's weights. A server's validation state is explicit in `biomcp/registry.json`.

## Website

The public site is in `docs/` and is deployed by the Pages workflow.

## Contributing

A new integration should ship as an independently testable server, be registered in the machine-readable catalog, document installation/configuration, and declare its real validation status. PowerMCP follows the same server-per-domain and CI-import/startup discipline. fileciteturn932file0L1-L6

## License

MIT.
