# BioMCP

<p align="center">
  <img src="1.jpeg" alt="BioMCP — Open Scientific Software Interoperability for Biology" width="100%">
</p>

<p align="center">
  <strong>The open MCP platform for biology, bioinformatics, bioimaging, and scientific AI.</strong><br>
  <em>AI orchestrates. Scientific software measures.</em>
</p>

BioMCP is a modular, open-source interoperability platform that lets AI agents discover and invoke real scientific software through the Model Context Protocol (MCP). It is designed as scientific infrastructure: **BioMCP connects, routes, validates, and documents scientific capabilities; the underlying scientific software remains responsible for computation and measurement.**

At the core is a registry-driven MCP layer between the AI host/agent and scientific software.

The intended execution flow is:

**Researcher → AI host / agent → BioMCP → scientific software → structured result + provenance/evidence**

![BioMCP architecture and scientific software interoperability](2as.png)

The architecture above represents the BioMCP platform vision: a registry-driven interoperability layer through which AI hosts and agents can discover, select, configure, and invoke scientific capabilities using MCP.

BioMCP separates the interoperability layer from the scientific computation itself:

- **AI host / agent** — plans the task, discovers available capabilities, and selects appropriate tools.
- **BioMCP** — provides registry-driven discovery, typed schemas, routing, validation, configuration, and MCP transport.
- **Scientific software** — performs the actual domain-specific computation or measurement.
- **Structured results** — return machine-readable scientific outputs to the calling agent.
- **Provenance / evidence** — preserves the information needed to understand and reproduce how a result was produced.

The initial BioMCP implementation focuses on three installable server families:

- **BioImage**
- **ImageJ/Fiji**
- **LLM**

Additional open-source scientific software integrations will be introduced incrementally in later versions. The detailed ecosystem shown in `2as.png` therefore represents the **long-term BioMCP platform vision**, not a claim that every depicted software package is currently implemented.

BioMCP deliberately distinguishes **implemented**, **experimental**, **validated**, **planned**, and **external** capabilities so that the registry and documentation do not advertise unsupported software as available.
## Why BioMCP?

Biology already has a large ecosystem of capable open-source scientific tools. The problem is often not the absence of software, but the absence of a standard, auditable bridge between those tools and modern AI agents.

BioMCP is intended to provide that bridge:

- **AI hosts/agents** plan, discover, select, and explain.
- **BioMCP** provides interoperability, typed tool contracts, routing, configuration, validation, and integration lifecycle metadata.
- **Scientific software** performs domain-specific computation and measurement.
- **Structured outputs and provenance** make results easier to inspect, reproduce, and audit.

> **A generated explanation is not a scientific measurement.**

## What is implemented today?

The current installable server families are intentionally small and testable:

| Integration | Role | Current state |
|---|---|---|
| **BioImage** | Local image inspection, intensity summaries, thresholding primitives | Experimental · installable |
| **ImageJ / Fiji** | Controlled bridge to an explicitly configured local runtime | Experimental · installable |
| **LLM Bridge** | OpenAI-compatible model endpoint integration | Experimental · installable |
| **BioNuclei** | Independent validated external MCP server | Validated · external · not bundled |

The machine-readable registry in `src/biomcp/registry.json` is the source of truth for integration status, installation metadata, transport and capabilities.

## Open-source scientific software ecosystem

BioMCP is being developed as a **registry-driven adapter ecosystem**. We will progressively add open scientific software rather than claiming support for everything at once.

### Version 0.3 — first three new integrations

The initial ecosystem expansion targets:

1. **PyMOL** — molecular visualization and structural-biology workflows.
2. **CellProfiler** — reproducible bioimage-analysis pipelines.
3. **BLAST+** — local sequence-similarity analysis.

These integrations begin as **planned**. An integration moves to `experimental` only after executable implementation and focused tests exist; it moves to `validated` only after the complete project validation gates pass.

### Later versions

Candidate integrations include, among others:

- **Bioimaging:** napari, QuPath, ilastik, Cellpose, DeepCell, StarDist.
- **Molecular/structural:** ChimeraX, VMD, RDKit, OpenMM, GROMACS.
- **Sequence/genomics:** BLAST+, HMMER, BWA, Bowtie2, STAR, samtools, bcftools, GATK and other established command-line tools.
- **Proteomics/omics:** domain-specific open tools selected by technical fit and community demand.
- **Workflow engines:** Nextflow, Snakemake and reproducible pipeline tooling.

The goal is not to wrap software indiscriminately. Every adapter must have a clear scientific use case, safe invocation model, typed MCP contract, documentation, tests, packaging support, and reproducibility/provenance considerations.

## Quick start

```bash
pip install biomcp
biomcp list
biomcp doctor
biomcp install --servers bioimage --clients generic
```

For image-analysis dependencies:

```bash
pip install 'biomcp[bioimage]'
```

Launch the current local server families:

```bash
biomcp run bioimage
biomcp run imagej
biomcp run llm
```

Preview generated client configuration before writing it:

```bash
biomcp install --servers bioimage --clients generic --dry-run
```

## Configure AI hosts

Supported configuration workflows currently include generic MCP configuration, Claude Desktop, and Codex-oriented configuration.

```bash
biomcp install --servers bioimage,imagej,llm --clients claude-desktop
biomcp install --servers bioimage,llm --clients codex
```

BioMCP keeps host configuration separate from scientific implementation. A client configuration entry should point to a concrete BioMCP server command and should not silently claim support for an integration that is only planned.

## Local configuration

ImageJ/Fiji:

```text
BIOMCP_IMAGEJ_EXECUTABLE=/path/to/ImageJ-or-Fiji
```

LLM bridge:

```text
BIOMCP_LLM_BASE_URL=...
BIOMCP_LLM_API_KEY=...
BIOMCP_LLM_MODEL=...
```

`OPENAI_API_KEY` is accepted as an API-key fallback by the LLM bridge.

## Registry-first lifecycle

The registry separates **what exists** from **what is planned**. Current lifecycle states are:

- **Planned** — roadmap item; not installable.
- **Experimental** — executable integration under active validation.
- **Validated** — executable integration with documented evidence and passing project gates.
- **Deprecated** — retained for compatibility/history but not recommended.
- **External** — maintained outside this repository; BioMCP may describe or connect to it without duplicating its scientific implementation.

For an adapter to become an installable BioMCP integration, the minimum expectation is:

1. Executable implementation.
2. Typed MCP tools and clear input/output contracts.
3. Validation of user inputs, paths, parameters, and environment assumptions.
4. Safe process execution and bounded resources where subprocesses are used.
5. Unit and integration tests.
6. Real MCP protocol/client-server interoperability tests where applicable.
7. Installed-wheel and source-distribution consumer validation.
8. Documentation and client configuration examples.
9. Registry metadata that matches the implementation.
10. CI evidence for the supported environments.

## Scientific tool contract

A BioMCP tool should behave like a scientific API, not like an unconstrained prompt. Where applicable, its contract should make explicit:

- capability and intended scientific purpose;
- accepted inputs, units, dimensions, file types, and parameter ranges;
- output schema and artifact semantics;
- deterministic versus stochastic behavior;
- software identity and version information;
- required external executables or model/data assets;
- provenance and evidence fields;
- expected failure modes;
- resource and timeout boundaries;
- limitations and validation state.

BioMCP should never silently invent a scientific result when the underlying operation failed, produced incomplete output, or cannot substantiate a claim.

## BioNuclei boundary

BioNuclei is intentionally treated as an **external validated scientific system**. BioMCP may provide interoperability to a BioNuclei MCP server, but this repository does not copy or reimplement the BioNuclei scientific engine.

This separation preserves a clean division:

```text
BioNuclei  → scientific computation, measurements, validation, artifacts
BioMCP     → MCP interoperability, discovery, routing, configuration
```

## Contributing to BioMCP

We welcome developers, computational biologists, imaging scientists, bioinformaticians, workflow engineers, and scientific-software users.

### Add a new open-source software adapter

Before opening a pull request, choose one concrete scientific workflow and document:

- the upstream open-source project and version/interface you are integrating;
- why MCP interoperability materially helps the scientific workflow;
- what executable/library is required locally;
- the intended BioMCP tool names and typed input/output contracts;
- how paths, credentials, network access, and subprocesses are controlled;
- what validation and resource limits are required;
- what provenance/evidence the adapter will expose;
- what platforms and external dependencies are supported.

Then implement the smallest useful adapter rather than a large speculative wrapper.

### Repository contribution workflow

```bash
git clone https://github.com/BurhanAbdullah/BioMCP.git
cd BioMCP
python -m venv .venv
# Activate .venv for your shell
python -m pip install --upgrade pip
pip install -e '.[test]'
pytest
```

Create a feature branch, make focused commits, update tests and documentation together, and open a pull request against `main`.

For a new scientific integration, the normal path is:

```text
Idea
  ↓
Planned registry entry
  ↓
Adapter implementation
  ↓
Unit + integration tests
  ↓
MCP interoperability validation
  ↓
Packaging / installed-artifact validation
  ↓
Documentation + client configuration
  ↓
Experimental
  ↓
CI / security / reproducibility evidence
  ↓
Validated
```

Do not mark a planned integration as installable merely because the upstream software exists.

### Community and collaboration

The wider scientific-AI ecosystem around this project is also documented through the BioNuclei community hub:

**Join the community:** https://burhanabdullah.github.io/BioNuclei-DomainRobust/community.html

That community page is the place to find the broader research/project community and collaboration entry points. BioMCP remains an independently maintained interoperability repository.

## Development principles

BioMCP follows a few strict principles:

- **Scientific software remains the source of scientific computation.**
- **Registry state must reflect executable reality.**
- **Security boundaries are part of the adapter design, not an afterthought.**
- **Tests should exercise the real MCP path where practical.**
- **Installed artifacts must be validated, not only source-tree imports.**
- **Documentation must distinguish implemented, experimental, validated, planned, and external capabilities.**
- **Provenance and evidence are first-class concerns for scientific outputs.**

## Roadmap

### Near term

- strengthen image-resource and decompression limits;
- harden ImageJ/Fiji timeout and environment isolation;
- strengthen LLM endpoint validation and response bounds;
- formalize registry schema/versioning and capability metadata;
- expand Linux/macOS/Windows coverage and end-to-end tests;
- implement and validate the first three new open-source adapters: PyMOL, CellProfiler, and BLAST+.

### Long-term ecosystem

BioMCP aims to provide a common MCP interoperability layer for a broad, carefully curated ecosystem of open scientific software spanning microscopy, structural biology, sequence analysis, omics, simulation, visualization, AI inference, and workflow execution.

Expansion will be driven by scientific utility, upstream project health, reproducibility, security, maintainability, and community demand—not by the number of integrations claimed.

## Documentation

The project documentation is maintained in [`docs/`](docs/). Start with:

- [`docs/install.html`](docs/install.html) — installation and configuration.
- [`docs/servers.html`](docs/servers.html) — server families and lifecycle status.
- [`docs/clients.html`](docs/clients.html) — AI-host configuration.
- [`docs/integrations.md`](docs/integrations.md) — adapter lifecycle and contribution contract.

## License

BioMCP is released under the MIT License.
