# BioMCP documentation

BioMCP is an open-source MCP platform for connecting LLM hosts to biology, bioinformatics, and bioimaging software.

## Product map

- **Home** — what BioMCP is and why it exists.
- **Install** — package installation and setup.
- **Servers** — the live server registry and validation states.
- **Clients** — Claude Desktop, Claude Code, Codex, and generic MCP configuration.
- **Architecture** — registry, server, transport, and provenance boundaries.
- **Examples** — representative agent-to-scientific-tool workflows.
- **Contributing** — requirements for new scientific integrations.

## Current implementation

- **BioImage Tools** — experimental and installable through the BioMCP package.
- **ImageJ / Fiji** — experimental and installable when a local ImageJ/Fiji runtime is available.
- **LLM Bridge** — experimental and installable; uses an OpenAI-compatible endpoint with credentials supplied through the environment.
- **BioNuclei** — validated external adapter. BioMCP does not copy or reimplement the BioNuclei scientific engine; users obtain the external `bionuclei-mcp` server through its own release channel.
- **CellProfiler** — planned; it remains non-installable until an executable adapter and validation suite exist.

The machine-readable registry is authoritative for installation and validation state. External adapters are integration boundaries, not duplicated implementations.
