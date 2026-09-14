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

## What is BioMCP?

BioMCP is an open-source interoperability layer for scientific computing.

Scientific software is fragmented across Python libraries, desktop applications, command-line programs, model servers, and independent MCP services. Each system has its own APIs, configuration rules, file formats, execution model, and failure modes.

BioMCP provides a common MCP boundary between these systems and MCP clients.

```text
                         MCP Client
                             |
                             v
                    +------------------+
                    |      BioMCP      |
                    |------------------|
                    | Registry         |
                    | Discovery        |
                    | Validation       |
                    | Configuration    |
                    | Execution        |
                    | Result handling  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
          BioImage       ImageJ/Fiji    LLM Gateway
              |              |              |
              v              v              v
        Scientific      Scientific       Model
        processing      software        endpoint
```

BioMCP does not replace scientific software and does not reimplement its algorithms. The upstream scientific system remains responsible for computation. BioMCP provides the protocol, integration, execution, and interoperability boundary.

## Why BioMCP?

BioMCP is designed for situations where an MCP client needs to work with more than one scientific system without learning a different integration mechanism for every backend.

The same platform can accommodate:

- Python scientific libraries
- Local command-line tools
- Desktop scientific applications
- Machine-learning model runtimes
- HTTP model endpoints
- External MCP servers

The integration model is adapter-based:

```text
MCP request
    |
    v
Typed tool contract
    |
    v
Validation
    |
    v
Registry resolution
    |
    v
Adapter
    |
    v
Scientific backend
    |
    v
Structured result
```

## Quick start

### Install

```bash
pip install biomcp
```

### Inspect available integrations

```bash
biomcp list
```

### Check the environment

```bash
biomcp doctor
```

### Run a server

```bash
biomcp run bioimage
```

or:

```bash
biomcp run imagej
biomcp run llm
```

### Generate MCP client configuration

```bash
biomcp install --servers bioimage,imagej,llm --clients claude-desktop
```

Preview changes first with:

```bash
biomcp install --servers bioimage,llm --clients generic --dry-run
```

## Current integrations

BioMCP intentionally keeps its supported surface small until integrations have executable validation.

| Integration | Current capability | Status |
|---|---|---|
| **BioImage** | Image inspection, intensity summaries, thresholding | Experimental, installable |
| **ImageJ / Fiji** | Controlled bridge to a configured local runtime | Experimental, installable |
| **LLM Gateway** | OpenAI-compatible model endpoint bridge | Experimental, installable |
| **BioNuclei** | External MCP service integration | Validated, external |

Lifecycle states are deliberately conservative:

- `Planned` means roadmap scope without an installable implementation.
- `Experimental` means executable integration work exists but the complete validation gate has not been satisfied.
- `Validated` means documented evidence supports the stated lifecycle status.
- `External` means the scientific system is maintained outside this repository.

## MCP interoperability

BioMCP is built around the Model Context Protocol rather than a collection of unrelated wrapper APIs.

A typical interaction is:

```text
Client
  |
  | MCP
  v
BioMCP server
  |
  | adapter invocation
  v
Scientific software
  |
  | result
  v
Structured MCP response
```

The project validates interoperability through actual MCP client/server exchanges where practical rather than relying only on Python imports or unit tests.

## LLM Gateway

BioMCP includes an experimental LLM integration for model access and orchestration. It is not a scientific computation engine.

The current implementation provides an OpenAI-compatible bridge with provider-oriented configuration. The architecture is intended to support multiple hosted and local model endpoints:

```text
             LLM Gateway
                  |
      +-----------+-----------+
      |           |           |
      v           v           v
    OpenAI      Ollama       vLLM
  compatible     local      endpoint
```

The broader gateway architecture is intended to support model discovery, streaming, structured output, tool calling, MCP capability discovery, controlled MCP execution, provider metadata, context limits, response limits, credential isolation, and normalized errors.

These capabilities are not all considered validated in the current release.

Current experimental bridge configuration:

```text
BIOMCP_LLM_PROVIDER=...
BIOMCP_LLM_BASE_URL=...
BIOMCP_LLM_API_KEY=...
BIOMCP_LLM_MODEL=...
BIOMCP_LLM_TIMEOUT_SECONDS=...
BIOMCP_LLM_MAX_RESPONSE_BYTES=...
```

The gateway keeps provider credentials out of registry metadata and applies endpoint, timeout, response-size, redirect, and error-handling controls at the HTTP boundary.

## Architecture

BioMCP is organized around four core responsibilities.

### Registry

The registry provides machine-readable metadata describing integrations, lifecycle state, installation information, transport, tools, dependencies, providers, and configuration.

### Runtime

The runtime resolves an integration, validates the environment, applies configuration, and starts or connects to the corresponding MCP server.

### Adapters

Adapters translate the MCP tool contract into the native execution model of the backend.

### Results

Results are returned through structured MCP responses. Where supported, execution metadata, artifacts, software identity, parameters, and provenance can accompany the result.

## Registry-driven integration model

BioMCP grows through explicit adapters rather than duplicated scientific implementations.

```text
MCP Tool
   |
   +--> Input schema
   |
   +--> Validation
   |
   +--> Execution preparation
   |
   +--> Backend invocation
   |
   +--> Result normalization
   |
   +--> Metadata / provenance
```

A new integration should identify the upstream project, supported interface, executable requirements, input and output contract, execution model, security boundary, and validation requirements.

### Planned scientific integrations

| Software | Intended scope |
|---|---|
| **PyMOL** | Molecular visualization and structural biology workflows |
| **CellProfiler** | Reproducible bioimage analysis pipelines |
| **BLAST+** | Local sequence similarity analysis |
| napari | Interactive bioimage analysis and visualization |
| QuPath | Digital pathology workflows |
| Cellpose | Cell and object segmentation |
| RDKit | Cheminformatics workflows |
| GROMACS | Molecular dynamics workflows |
| HMMER | Sequence homology analysis |
| samtools / bcftools | Genomic data processing |
| Nextflow / Snakemake | Reproducible workflow orchestration |

Planned entries are roadmap items. They do not imply that adapters already exist.

## Scientific execution boundary

BioMCP intentionally separates interoperability from scientific computation.

```text
                    BioMCP
                       |
        +--------------+--------------+
        |              |              |
    protocol       execution       metadata
        |           control           |
        +--------------+--------------+
                       |
                       v
             Scientific software
                       |
        +--------------+--------------+
        |              |              |
     compute       infer/measure    artifacts
                       |
                       v
                    BioMCP
                       |
                       v
              Structured result
```

When a language model participates in a workflow, model output is an orchestration or interpretation layer. The scientific backend remains responsible for the underlying scientific result.

BioMCP does not copy or reimplement the BioNuclei scientific engine. BioNuclei remains responsible for its scientific computation, models, measurements, evaluation, artifacts, and provenance.

## Scientific tool contract

A BioMCP tool should behave as a typed scientific API.

| Contract element | Requirement |
|---|---|
| Capability | Scientific purpose of the operation |
| Inputs | Types, units, ranges, and file requirements |
| Outputs | Result schema and artifact semantics |
| Dependencies | Executables, libraries, models, or data assets |
| Execution | Process, network, and resource requirements |
| Failure | Expected errors and incomplete-result behavior |
| Provenance | Software identity, versions, and relevant parameters |
| Validation | Lifecycle state and validation evidence |

A failed operation remains a failed operation. An adapter must not convert an execution failure into a plausible-looking scientific result.

## Security and execution controls

Scientific integrations may execute local processes, external programs, and network services. Execution boundaries are therefore part of adapter design.

Relevant controls include:

- Input and parameter validation
- Path validation
- Bounded file handling and decompression
- Controlled subprocess environments
- Timeout enforcement
- Bounded output sizes
- Restricted credential inheritance
- Endpoint validation
- Sanitized provider and subprocess errors
- Explicit network requirements
- Reproducible configuration

The exact controls depend on the backend and are validated at the adapter level.

## Validation and engineering

BioMCP treats interoperability as an executable property.

```text
Implementation
      |
      v
Unit tests
      |
      v
Integration tests
      |
      v
Actual MCP client / server exchange
      |
      v
Wheel build
      |
      v
Installed wheel test
      |
      v
Source distribution test
      |
      v
CI evidence
```

The package validation path includes actual MCP client sessions for installable server families, installed-wheel consumer checks, source-distribution consumer checks, and security regression coverage for selected subprocess integrations.

Source-tree imports alone are not sufficient evidence for a packaged integration.

A capability should be described as validated only when the corresponding implementation, protocol path, packaging path, and project-specific checks provide sufficient evidence.

## Command line interface

| Command | Purpose |
|---|---|
| `biomcp list` | List registry integrations and lifecycle state |
| `biomcp doctor` | Diagnose commands, dependencies, and configuration |
| `biomcp install` | Install selected registry integrations and configure clients |
| `biomcp install --dry-run` | Preview installation/configuration changes |
| `biomcp run <server>` | Launch a registered MCP server |
| `biomcp config show` | Show resolved configuration |
| `biomcp config set <key> <value>` | Set supported configuration values |

Examples:

```bash
biomcp install --servers bioimage,imagej,llm --clients generic
biomcp install --servers bioimage,llm --clients codex
biomcp doctor --server bioimage
biomcp run bioimage
```

Generating client configuration does not make a planned integration executable.

## Package structure

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

Current console entry points include:

```text
biomcp
biomcp-bioimage
biomcp-imagej
biomcp-llm
```

Optional dependency groups are provided for integration families and testing.

## Development

```bash
git clone https://github.com/BurhanAbdullah/BioMCP.git
cd BioMCP
python -m venv .venv
```

Activate the environment and install development dependencies:

```bash
python -m pip install --upgrade pip
pip install -e '.[test]'
pytest
```

For BioImage support:

```bash
pip install 'biomcp[bioimage]'
```

ImageJ/Fiji requires an explicitly configured local installation.

## Contributing

A new integration should follow the complete path:

```text
Scientific use case
        |
        v
Upstream software
        |
        v
Registry definition
        |
        v
Adapter
        |
        v
MCP tool contract
        |
        v
Tests
        |
        v
Protocol validation
        |
        v
Packaging validation
        |
        v
Documentation
        |
        v
Experimental
        |
        v
Security / CI / reproducibility evidence
        |
        v
Validated
```

Contributions should document why MCP interoperability is useful, how the upstream software is invoked, how inputs and outputs are represented, what resources and credentials are required, and how execution is validated.

## Roadmap

### Platform

- Formal registry schema and versioning
- Stronger capability discovery
- Expanded protocol-level regression tests
- Broader wheel and source-distribution validation
- Additional resource and execution controls
- More reproducible integration environments

### LLM Gateway

- Provider abstraction
- Model discovery
- Provider capability metadata
- Streaming
- Structured outputs and JSON schema
- Tool calling
- Controlled MCP capability discovery and execution
- Context and session limits
- Usage metadata
- Credential isolation
- Endpoint validation
- Error normalization
- Provider interoperability tests

### Scientific ecosystem

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

## Design principles

1. Scientific algorithms remain in scientific software.
2. BioMCP provides interoperability rather than duplicate implementations.
3. Registry state reflects executable reality.
4. MCP interoperability should be tested through actual protocol paths.
5. Installed artifacts should be validated independently of the source tree.
6. Execution environments should be explicitly bounded.
7. Scientific outputs should be structured and inspectable.
8. Provenance should be retained where available.
9. Planned, experimental, validated, and external states remain distinct.
10. Integration quality matters more than integration count.

## Status

BioMCP is under active development.

The current release provides the platform foundation and a small number of executable integrations. Additional scientific systems are being added only as their adapters, interfaces, tests, packaging paths, and validation evidence become available.

The project is conservative about capability claims. An upstream application being available does not imply that a BioMCP adapter exists. A documented adapter does not automatically imply validation. Lifecycle state is tied to implementation and test evidence.

## Links

- Repository: https://github.com/BurhanAbdullah/BioMCP
- Technical documentation: https://burhanabdullah.github.io/BioNuclei-DomainRobust/biomcp.html
- Community: https://burhanabdullah.github.io/BioNuclei-DomainRobust/community.html
- Model Context Protocol: https://modelcontextprotocol.io/

## License

BioMCP is released under the MIT License.
