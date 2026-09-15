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

## 🌟 What is BioMCP?

**BioMCP** is an open-source scientific interoperability platform built around the **Model Context Protocol (MCP)**.

Scientific computing is spread across Python libraries, command-line programs, desktop applications, image-analysis tools, model runtimes, and independent MCP services. BioMCP provides a common way to discover, configure, validate, and invoke these systems from MCP-compatible clients.

BioMCP focuses on interoperability rather than reimplementing scientific software. The scientific application remains responsible for its algorithms and scientific computation; BioMCP provides the integration, execution boundary, protocol interface, configuration, and result transport.

### BioMCP provides

- MCP servers for scientific applications and services
- Registry-driven integration discovery
- MCP capability and tool discovery
- Typed tool contracts and argument validation
- Controlled local process execution
- External MCP server integration
- LLM provider integration
- CLI-based installation and configuration
- MCP client configuration generation
- Execution timeouts and bounded results
- Credential and environment isolation
- Package and installed-consumer validation

## 🤝 Scientific Interoperability Vision

BioMCP is intended to make scientific software easier to use from modern AI applications without requiring every scientific project to build its own MCP integration from scratch.

The project is built around a few practical goals:

- **Interoperability**: Connect different scientific systems through MCP.
- **Reproducibility**: Make integrations, dependencies, configuration, and execution requirements explicit.
- **Safety**: Bound local execution, network access, credentials, timeouts, and outputs where appropriate.
- **Extensibility**: Add scientific applications through explicit adapters and registry definitions.
- **Validation**: Treat protocol compatibility and package usability as executable properties.
- **Scientific integrity**: Preserve the distinction between interoperability software and the scientific software performing the computation.

## 🚀 Getting Started

### 📖 Quick start

> **🚀 New to BioMCP? Start here!**

Install the package:

```bash
pip install biomcp
```

Check the installation:

```bash
biomcp doctor
```

See the available integrations:

```bash
biomcp list
```

Launch an MCP server:

```bash
biomcp run bioimage
```

Other registered servers can be launched with the same command:

```bash
biomcp run imagej
biomcp run llm
```

### Configure an MCP client

BioMCP can generate configuration for supported MCP clients:

```bash
biomcp install --servers bioimage,imagej,llm --clients claude-desktop
```

Preview the changes first:

```bash
biomcp install --servers bioimage,llm --clients generic --dry-run
```

For non-interactive installation of selected integrations:

```bash
biomcp install --servers bioimage,llm --clients generic --yes
```

The installer uses the BioMCP registry to determine the server command, dependencies, configuration requirements, and supported integration metadata.

## 🧬 Current Integrations

| Integration | Description | Status |
|---|---|---|
| **BioImage** | Image inspection, intensity summaries, and thresholding tools | Experimental |
| **ImageJ / Fiji** | Controlled bridge to a configured local ImageJ/Fiji runtime | Experimental |
| **LLM Gateway** | Provider-oriented integration for OpenAI-compatible model endpoints | Experimental |
| **BioNuclei** | External scientific MCP service integration | Validated / External |

BioMCP uses conservative lifecycle states:

- **Planned** — proposed integration without an installable implementation.
- **Experimental** — executable implementation exists but the complete validation gate is not yet satisfied.
- **Validated** — implementation and project checks provide sufficient evidence for the stated capability.
- **External** — the scientific system is maintained outside this repository.

The presence of a planned software project in the roadmap does not mean that an adapter has already been implemented.

## 🧠 MCP

The **Model Context Protocol** provides the common protocol boundary used by BioMCP.

MCP allows AI applications to work with external tools and services through standardized interfaces for capabilities, tools, resources, prompts, and structured results.

BioMCP currently uses MCP for:

- Tool discovery
- Capability discovery
- Tool schema inspection
- Argument validation
- Controlled tool execution
- Structured results
- MCP client/server interoperability
- External MCP service integration

Where practical, BioMCP validates integrations using actual MCP client sessions rather than relying only on imports or isolated Python unit tests.

Useful MCP resources:

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP documentation](https://modelcontextprotocol.io/docs)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## 📦 Installation

BioMCP is distributed as a Python package.

```bash
pip install biomcp
```

Python 3.10+ is required.

### Optional integrations

Integration families can be installed through optional dependencies when required:

```bash
pip install 'biomcp[bioimage]'
```

Testing dependencies:

```bash
pip install 'biomcp[test]'
```

The core package does not require every scientific application to be installed. Integrations that depend on local software, executables, models, or other runtime assets document those requirements separately.

## 🛠️ CLI Commands

| Command | Description |
|---|---|
| `biomcp install` | Install selected integrations and configure MCP clients |
| `biomcp list` | List registered integrations and lifecycle state |
| `biomcp tools <server>` | Inspect tools exposed by a registered server |
| `biomcp call <server> <tool>` | Invoke a registered MCP tool |
| `biomcp run <server>` | Launch a registered MCP server |
| `biomcp doctor` | Check dependencies, executables, and configuration |
| `biomcp config` | Inspect and manage supported configuration |

Examples:

```bash
biomcp list
biomcp tools bioimage
biomcp doctor --server bioimage
biomcp run bioimage
biomcp run llm
```

### Installation options

```bash
biomcp install --servers bioimage,llm --clients generic
biomcp install --servers bioimage,llm --clients codex
biomcp install --servers bioimage --clients claude-desktop --dry-run
```

## 🤖 LLM Gateway

BioMCP includes an experimental **LLM Gateway** for connecting model endpoints to MCP-based workflows.

The gateway is designed around provider configuration and explicit capability metadata rather than assuming that every provider implements the same API surface.

### Provider profiles

Current provider profiles include:

- OpenAI-compatible endpoints
- Ollama
- vLLM

### Gateway capabilities

The gateway currently provides infrastructure for:

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
- Controlled MCP capability discovery
- Controlled MCP tool execution

Capabilities are explicitly advertised and enforced by the provider configuration. A provider is not assumed to support a feature simply because another provider does.

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

## 🔌 Registry

BioMCP is registry-driven. Integration metadata is kept separate from the scientific implementation so that the CLI, installer, discovery layer, and client configuration system can work from the same source of truth.

Registry entries can describe:

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

This also makes it possible to distinguish a documented roadmap item from an executable integration.

## 🔬 Scientific Software

BioMCP is intended to provide MCP interfaces for scientific software across multiple disciplines.

### Planned integration areas

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

These entries describe intended scope only. They do not imply that the corresponding adapters are already available.

## 🧪 Scientific Tool Contracts

BioMCP integrations are intended to expose scientific operations as explicit, inspectable tool contracts.

A mature integration should document:

| Area | Requirement |
|---|---|
| Capability | Scientific purpose of the operation |
| Inputs | Types, ranges, units, and file requirements |
| Outputs | Result schema and artifact semantics |
| Dependencies | Libraries, executables, models, or datasets |
| Execution | Process, network, and resource requirements |
| Failure | Expected errors and incomplete-result behavior |
| Provenance | Software identity, versions, and relevant parameters |
| Validation | Evidence supporting the integration lifecycle state |

An execution failure must remain an execution failure. An adapter should never convert an unsuccessful scientific operation into a plausible-looking scientific result.

## 🔐 Security and Execution

Scientific integrations may execute local programs or communicate with external services. BioMCP therefore treats execution boundaries as part of the integration contract.

Current controls include, where applicable:

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

The controls applied depend on the integration and its execution model.

## 🧫 Validation and Testing

BioMCP is developed around executable validation rather than source-tree assumptions.

Validation can include:

- Unit tests
- Integration tests
- MCP protocol tests
- Real MCP client/server sessions
- Security regression tests
- Wheel builds
- Source-distribution builds
- Installed-package consumer tests
- CI testing across supported Python versions

A source import succeeding is not sufficient evidence that a packaged integration works.

For integrations that expose MCP servers, protocol-level tests are used to verify tool discovery and invocation through the actual MCP interface where practical.

## 💻 Development

Clone the repository:

```bash
git clone https://github.com/BurhanAbdullah/BioMCP.git
cd BioMCP
python -m venv .venv
```

Activate the environment and install development dependencies:

```bash
python -m pip install --upgrade pip
pip install -e '.[test]'
```

Run the test suite:

```bash
pytest
```

For BioImage development:

```bash
pip install -e '.[bioimage]'
```

ImageJ/Fiji integrations require an explicitly configured local installation.

## 🧩 Package Structure

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

## 🧑‍💻 Contributing

Contributions are welcome.

For a new scientific integration, please provide:

1. A clearly defined scientific use case.
2. Registry metadata for the integration.
3. A documented MCP tool contract.
4. A controlled adapter or execution implementation.
5. Input and output validation.
6. Appropriate failure handling.
7. Relevant protocol and integration tests.
8. Packaging and installed-consumer validation where applicable.
9. Documentation for dependencies, configuration, and runtime requirements.

Before an integration is described as validated, its implementation and validation evidence should support the stated capability.

## 🗺️ Roadmap

### Platform

- Formal registry schema and versioning
- Expanded capability discovery
- Broader MCP protocol regression coverage
- More package-consumer validation
- Additional execution controls
- Reproducible integration environments

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

## 📚 Documentation

- [BioMCP technical documentation](https://burhanabdullah.github.io/BioNuclei-DomainRobust/biomcp.html)
- [BioMCP community](https://burhanabdullah.github.io/BioNuclei-DomainRobust/community.html)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## 📄 License

BioMCP is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

BioMCP builds on the open scientific software ecosystem and the Model Context Protocol community.

Special thanks to the developers and maintainers of the scientific tools, libraries, model runtimes, and open protocols that make interoperable scientific computing possible.

## About

BioMCP is an open-source scientific interoperability platform for connecting scientific applications, tools, model runtimes, and MCP services through a consistent protocol and execution layer.
