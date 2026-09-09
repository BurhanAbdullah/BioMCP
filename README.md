# BioMCP

**The MCP platform for biology, bioinformatics, and bioimaging.**

BioMCP gives LLM applications a clean, installable way to discover and use validated open-science tools. It is designed around the same principle as a good software toolkit: one package, one registry, simple client configuration, and explicit boundaries between AI orchestration and scientific computation.

## Why BioMCP

AI should be able to work with scientific software without every researcher hand-editing MCP configuration files or learning each server's internals.

BioMCP provides:

- a machine-readable registry of scientific MCP servers;
- one CLI for discovery, installation, configuration, and diagnostics;
- generated configuration for common MCP clients;
- stdio and remote-server support where the registered server provides it;
- scientific provenance and validation status at the server boundary;
- a clear distinction between **planned**, **experimental**, and **validated** integrations.

## Quick start

```bash
pip install biomcp
biomcp list
biomcp doctor
biomcp install --yes
```

The installer can configure the registered BioMCP servers for supported clients without requiring users to hand-edit JSON or TOML.

## First server pack

The first validated pack is **BioNuclei**, exposing deterministic bioimage-analysis tools through MCP. BioMCP does not replace BioNuclei's scientific implementation: it provides interoperability between an LLM host and the scientific server.

## What an LLM sees

```text
Research question
      ↓
LLM / agent
      ↓
BioMCP discovery
      ↓
validated MCP server
      ↓
typed tool call
      ↓
scientific result + provenance
```

## CLI

```text
biomcp list
biomcp install [--servers ...] [--clients ...] [--dry-run]
biomcp run <server>
biomcp doctor
biomcp config show
biomcp config set <section.key> <value>
```

## Repository layout

```text
src/biomcp/        platform CLI, registry, clients, runner
src/bionuclei/     BioNuclei scientific engine and MCP server
biomcp/            machine-readable registry and example configuration
docs/              website and full product documentation
tests/             automated validation
```

## Scientific boundary

BioMCP routes and transports tool calls. It does not invent measurements, benchmarks, or scientific conclusions. Each registered server remains responsible for its own executable scientific computation and provenance.

## Website

Open the BioMCP product site from `docs/index.html` after enabling GitHub Pages for the `docs/` directory.

## Contributing

See `docs/contributing.html` and the repository issue/PR templates. A new scientific integration must include a runnable server, machine-readable metadata, tests, documentation, and an explicit validation state before being promoted to `validated`.

## License

MIT. See `LICENSE`.
