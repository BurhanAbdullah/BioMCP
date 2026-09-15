# BioMCP

<p align="center">
  <img src="1.jpeg" alt="BioMCP scientific software interoperability" width="100%">
</p>

<p align="center">
  <strong>Open scientific software interoperability through MCP.</strong>
</p>

<p align="center">
  Connect scientific applications, command-line tools, model runtimes, and external MCP services through one consistent interface.
</p>

<p align="center">
  <a href="https://github.com/BurhanAbdullah/BioMCP">GitHub</a> ·
  <a href="https://burhanabdullah.github.io/BioNuclei-DomainRobust/biomcp.html">Documentation</a> ·
  <a href="https://modelcontextprotocol.io/">Model Context Protocol</a>
</p>

---

## Overview

**BioMCP** is an open-source interoperability layer for scientific computing built around the **Model Context Protocol (MCP)**.

Scientific workflows often span Python packages, command-line programs, desktop applications, model endpoints, and independent MCP servers. BioMCP provides a consistent interface for discovering, configuring, validating, and invoking these systems without reimplementing their scientific algorithms.

BioMCP is designed around a registry and adapter model, with explicit execution boundaries, structured tool contracts, and executable validation.

### What BioMCP provides

- MCP servers for scientific software and services
- Registry-driven integration metadata
- Capability and tool discovery
- Input and argument validation
- Controlled local process execution
- External MCP client integration
- LLM provider integration
- CLI-based installation and configuration
- MCP client configuration generation
- Bounded timeouts and result sizes
- Credential and environment isolation
- Package and installed-consumer validation

BioMCP is an interoperability layer. Scientific computation remains in the scientific software being integrated.

## Installation

```bash
pip install biomcp
```

Verify the installation:

```bash
biomcp doctor
```

List available integrations:

```bash
biomcp list
```

## Quick Start

### List integrations

```bash
biomcp list
```

### Diagnose an integration

```bash
biomcp doctor
biomcp doctor --server bioimage
```

### Run an MCP server

```bash
biomcp run bioimage
```

Other registered servers can be launched in the same way:

```bash
biomcp run imagej
biomcp run llm
```

### Configure an MCP client

```bash
biomcp install --servers bioimage,imagej,llm --clients claude-desktop
```

Preview changes without modifying configuration:

```bash
biomcp install --servers bioimage,llm --clients generic --dry-run
```

Supported client configuration targets include generic MCP configuration as well as supported desktop and coding clients exposed by the CLI.

## CLI

| Command | Description |
|---|---|
| `biomcp list` | List registered integrations and lifecycle state |
| `biomcp tools` | Inspect tools exposed by a registered server |
| `biomcp call` | Invoke a registered MCP tool |
| `biomcp install` | Install integrations and configure MCP clients |
| `biomcp doctor` | Check dependencies, executables, and configuration |
| `biomcp run <server>` | Launch a registered MCP server |
| `biomcp config` | Inspect and manage supported configuration |

Examples:

```bash
biomcp list
biomcp tools bioimage
biomcp doctor --server imagej
biomcp run llm
```

## Current Integrations

BioMCP keeps the supported integration surface deliberately small until implementations have executable validation.

| Integration | Scope | Status |
|---|---|---|
| **BioImage** | Image inspection, intensity summaries, thresholding | Experimental |
| **ImageJ / Fiji** | Controlled bridge to a configured local runtime | Experimental |
| **LLM Gateway** | OpenAI-compatible model endpoint integration | Experimental |
| **BioNuclei** | External MCP service integration | Validated / External |

Lifecycle terminology is intentionally conservative:

- **Planned** — roadmap scope without an installable implementation.
- **Experimental** — executable integration exists, but the complete validation gate has not been satisfied.
- **Validated** — implementation and project checks provide sufficient evidence for the stated capability.
- **External** — the scientific system is maintained outside this repository.

## MCP Support

BioMCP uses MCP as the interoperability boundary rather than creating a separate protocol for every integration.

The platform supports controlled MCP client/server interactions, including:

- MCP capability discovery
- Tool discovery
- Tool schema inspection
- Argument validation
- Controlled tool invocation
- Structured results
- Timeout enforcement
- Result-size limits
- Restricted child environments
- Sanitized configuration and execution errors

Where practical, interoperability is tested through actual MCP client sessions instead of relying only on imports or isolated unit tests.

## LLM Gateway

BioMCP includes an experimental LLM Gateway for connecting MCP workflows to model endpoints.

The gateway currently provides an OpenAI-compatible HTTP interface with provider-oriented configuration and capability metadata.

Supported provider profiles currently include:

- OpenAI-compatible endpoints
- Ollama
- vLLM

The gateway includes controls for:

- Provider configuration
- Model discovery
- Provider capability discovery
- Chat/completions requests
- Responses API requests
- Streaming transport
- Structured-output controls
- Tool-calling controls
- Request timeouts
- Response-size limits
- Bounded retries
- Redirect protection
- Credential isolation
- Sanitized transport errors

Not every capability is enabled for every provider. Provider capabilities are explicitly advertised and enforced by the gateway.

### LLM configuration

```bash
export BIOMCP_LLM_PROVIDER=openai-compatible
export BIOMCP_LLM_BASE_URL=https://api.openai.com/v1
export BIOMCP_LLM_API_KEY=...
export BIOMCP_LLM_MODEL=...
```

Optional transport controls:

```bash
export BIOMCP_LLM_TIMEOUT_SECONDS=60
export BIOMCP_LLM_MAX_RESPONSE_BYTES=16777216
```

Credentials are supplied through the environment and are not stored in registry metadata.

## Registry

BioMCP is registry-driven. The registry describes integrations and their executable requirements without embedding scientific implementation logic.

Registry metadata can describe:

- Integration identity
- Lifecycle state
- Server command
- MCP transport
- Tools
- Dependencies
- Installation requirements
- Environment variables
- Provider configuration
- Runtime requirements

This allows the CLI and client configuration layer to work from the same machine-readable integration definition.

## Scientific Integrations

BioMCP is intended to provide a common integration surface for scientific software across multiple domains.

Planned integration areas include:

| Software | Intended scope |
|---|---|
| PyMOL | Molecular visualization and structural biology |
| CellProfiler | Reproducible bioimage analysis |
| BLAST+ | Local sequence similarity analysis |
| napari | Interactive bioimage analysis and visualization |
| QuPath | Digital pathology |
| Cellpose | Cell and object segmentation |
| RDKit | Cheminformatics |
| GROMACS | Molecular dynamics |
| HMMER | Sequence homology analysis |
| samtools / bcftools | Genomic data processing |
| Nextflow / Snakemake | Reproducible workflow orchestration |

Planned entries are roadmap items and do not imply that adapters are already implemented.

## Scientific Execution Boundary

BioMCP does not replace or duplicate the scientific software it integrates.

The upstream scientific application remains responsible for its algorithms, models, measurements, simulations, and scientific interpretation. BioMCP is responsible for interoperability, execution control, protocol exposure, configuration, and result transport.

This separation is particularly important for scientific reproducibility: an adapter should never turn a failed execution into a plausible-looking scientific result.

## Tool Contracts

BioMCP tools are intended to behave as typed scientific APIs.

A robust integration should define:

| Contract | Requirement |
|---|---|
| Capability | Scientific purpose of the operation |
| Inputs | Types, ranges, units, and file requirements where applicable |
| Outputs | Result schema and artifact semantics |
| Dependencies | Libraries, executables, models, or datasets |
| Execution | Process, network, and resource requirements |
| Failure | Expected errors and incomplete-result behavior |
| Provenance | Software identity, versions, and relevant parameters |
| Validation | Evidence supporting the integration lifecycle state |

## Security

Scientific integrations can execute local processes and communicate with external services, so execution boundaries are part of the platform design.

BioMCP applies controls such as:

- Input and argument validation
- Executable allowlisting
- Tool allowlisting
- Path and configuration validation
- Controlled subprocess environments
- Timeout enforcement
- Output-size limits
- Restricted credential inheritance
- Endpoint validation
- Redirect protection
- Sanitized errors
- Explicit network requirements

Controls are applied according to the integration and execution model rather than assuming that every scientific backend has the same security requirements.

## Validation

BioMCP treats interoperability as an executable property.

Validation includes, where applicable:

- Unit tests
- Integration tests
- MCP protocol tests
- Real MCP client/server exchanges
- Security regression tests
- Wheel builds
- Source-distribution builds
- Installed-package consumer tests
- CI validation across supported Python versions

Source-tree imports alone are not considered sufficient evidence for a packaged integration.

A capability is described conservatively according to the implementation and validation evidence available for that capability.

## Package Structure

```text
BioMCP/
├── src/
│   ├── biomcp/
│   │   ├── cli.py
│   │   ├── doctor.py
│   │   ├── llm.py
│   │   ├── registry.py
│   │   └── registry.json
│   └── biomcp_servers/
│       ├── bioimage.py
│       ├── imagej.py
│       └── llm.py
├── tests/
├── docs/
├── pyproject.toml
└── .github/
    └── workflows/
```

Console entry points include:

```text
biomcp
biomcp-bioimage
biomcp-imagej
biomcp-llm
```

Optional dependency groups are available for integration families and testing.

## Development

Clone the repository and create an isolated environment:

```bash
git clone https://github.com/BurhanAbdullah/BioMCP.git
cd BioMCP
python -m venv .venv
```

Activate the environment and install the test dependencies:

```bash
python -m pip install --upgrade pip
pip install -e '.[test]'
```

Run the test suite:

```bash
pytest
```

BioImage support:

```bash
pip install 'biomcp[bioimage]'
```

ImageJ/Fiji requires an explicitly configured local installation.

## Contributing

New integrations should provide:

1. A clearly defined scientific use case.
2. Registry metadata describing the integration.
3. A documented MCP tool contract.
4. A controlled adapter or execution implementation.
5. Input and output validation.
6. Failure handling that preserves scientific correctness.
7. Relevant protocol and integration tests.
8. Packaging and installed-consumer validation where applicable.
9. Documentation for dependencies, configuration, and runtime requirements.

Integration lifecycle state should reflect evidence rather than roadmap intent.

## Roadmap

### Platform

- Formal registry schema and versioning
- Stronger capability discovery
- Expanded MCP protocol regression coverage
- Broader package-consumer validation
- Additional execution controls
- More reproducible integration environments

### LLM Gateway

- Expanded provider abstraction
- Provider and model discovery
- Capability metadata
- Streaming improvements
- Structured outputs and JSON Schema
- Tool calling
- Controlled MCP discovery and execution
- Context and session limits
- Usage metadata
- Provider interoperability tests

### Scientific Ecosystem

- PyMOL
- CellProfiler
- BLAST+
- napari
- QuPath
- Cellpose
- RDKit
- GROMACS
- HMMER
- samtools / bcftools
- Nextflow / Snakemake

## Design Principles

- Scientific algorithms remain in the scientific software that owns them.
- BioMCP provides interoperability rather than duplicate scientific implementations.
- Registry state reflects executable reality.
- MCP interoperability should be tested through real protocol paths.
- Installed artifacts should be validated independently of the source tree.
- Execution environments should be explicitly bounded.
- Scientific outputs should be structured and inspectable.
- Provenance should be retained where available.
- Planned, experimental, validated, and external states remain distinct.
- Integration quality matters more than integration count.

## Status

BioMCP is under active development.

The project currently provides the platform foundation and a small set of executable integrations. Additional scientific systems are added as their interfaces, adapters, tests, packaging paths, and validation evidence become available.

Capability claims are intentionally conservative. The presence of an upstream scientific application does not imply that a BioMCP adapter exists, and an adapter is not automatically considered validated merely because it is documented.

## Links

- [Repository](https://github.com/BurhanAbdullah/BioMCP)
- [Technical documentation](https://burhanabdullah.github.io/BioNuclei-DomainRobust/biomcp.html)
- [Community](https://burhanabdullah.github.io/BioNuclei-DomainRobust/community.html)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## License

BioMCP is released under the MIT License.
