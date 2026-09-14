# BioMCP Open-Source Integration Roadmap

BioMCP is intended to become a common MCP interoperability layer for open scientific software. The platform will grow by **validated adapters**, not by copying the scientific implementations of the projects it connects to.

## Versioned rollout

### v0.3 — first three new open-source adapters

The first expansion targets three complementary tools:

| Integration | Domain | Initial MCP role | Status |
|---|---|---|---|
| **PyMOL** | Molecular visualization / structural biology | Load structures, execute constrained commands, export selected artifacts | Planned |
| **CellProfiler** | Bioimage analysis | Execute explicitly selected pipelines and expose structured outputs | Planned |
| **BLAST+** | Sequence analysis | Run local sequence similarity searches with bounded inputs/outputs | Planned |

These three are deliberately different: visualization, quantitative image-analysis workflow execution, and sequence analysis. Each adapter must have an executable implementation, bounded inputs, safe subprocess behavior, deterministic metadata where applicable, tests, documentation, and an explicit registry state before it becomes installable.

### v0.4+ — additional open-source ecosystem

The following projects are candidates for later adapters. They are **catalogued as future scope only** until implemented and validated:

- **Napari** — interactive bioimage visualization
- **QuPath** — digital pathology and whole-slide image analysis
- **Cellpose** — cell segmentation
- **ilastik** — interactive machine-learning image analysis
- **UCSF ChimeraX** — molecular visualization and analysis
- **VMD** — molecular visualization and molecular-dynamics analysis
- **RDKit** — cheminformatics
- **OpenMM** — molecular simulation
- **GROMACS** — molecular dynamics
- **Biopython** — biological sequence and structure utilities
- **HMMER** — profile-HMM sequence analysis
- **samtools / bcftools** — sequencing alignment and variant-file processing
- **BWA** — sequence alignment
- **Bowtie2** — sequence alignment
- **STAR** — RNA-seq alignment
- **FreeBayes** — variant calling
- **Nextflow** — reproducible workflow execution
- **Snakemake** — reproducible workflow execution

This list is a roadmap, not a claim that these integrations currently exist in BioMCP.

## Adapter contract

Every new integration should follow the same lifecycle:

```text
Candidate software
      |
      v
Interface design
      |
      v
Minimal adapter + explicit executable discovery
      |
      v
Unit + MCP protocol + installed-artifact tests
      |
      v
Security/resource limits + failure handling
      |
      v
Documentation + client configuration
      |
      v
Registry status: experimental
      |
      v
Evidence review
      |
      v
Registry status: validated
```

### Scientific boundary

BioMCP does not reimplement the algorithms of these projects. The upstream scientific software remains responsible for scientific computation. BioMCP is responsible for:

- MCP tool schemas and transport;
- discovery and configuration;
- input validation and resource limits;
- safe process execution where a local executable is used;
- structured results and provenance metadata;
- compatibility and regression testing.

### Versioning rule

Adding a project to this roadmap does **not** make it installable. The registry is authoritative. A project becomes installable only after its adapter, tests, packaging, documentation, and security controls are present and verified in CI.

This staged approach lets BioMCP expand rapidly while keeping scientific claims auditable and preventing the registry, installer, documentation, and actual runtime capabilities from drifting apart.
