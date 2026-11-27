# BioMCP development plan: five milestones

## Product direction
Build BioMCP into a modular scientific-computing MCP platform inspired by PowerMCP. BioMCP remains the platform and execution boundary; BioIO provides shared scientific data contracts; specialist adapters remain independently testable. The registry is the source of truth. Planned integrations must never be presented as implemented or validated.

## Milestone 1 — Scientific foundation (current)
**Objective:** establish BioIO's stable, dependency-light scientific artifact and provenance contracts before adding more adapters.

Scope:
- Add a small bioio package with immutable artifact and execution-provenance models.
- Support deterministic SHA-256 identity for local artifacts without loading scientific payloads into memory.
- Validate metadata and parameters as JSON-compatible values.
- Provide serialization contracts that adapters can share.
- Add deterministic unit tests and document the contract.
- Preserve the existing BioMCP registry, CLI, broker, and MCP server interfaces.

Exit criteria:
- Core package imports on Python 3.10+ without optional scientific dependencies.
- Artifact checksums are streamed and stable.
- Invalid identifiers, digests, sizes, timestamps, and non-JSON metadata are rejected.
- Provenance records serialize deterministically and preserve input/output artifact references.
- New tests pass alongside the existing test suite.

## Milestone 2 — Bioimaging interoperability
**Objective:** turn the current TIFF primitives into an interoperable microscopy stack.

Scope:
- Extend BioIO image metadata and axes/channel/pixel-size representation.
- Add OME-TIFF and OME-Zarr support with explicit optional dependencies.
- Improve BioImage QC, metadata inspection, preprocessing and measurement operations.
- Implement CellProfiler and Cellpose adapters with typed inputs, outputs, resource limits and provenance.
- Add real, small microscopy fixtures and reference-based tests.

Exit criteria:
- Image artifacts preserve axes, physical units, channels and acquisition metadata where available.
- Each shipped adapter passes live MCP discovery and invocation tests.
- Segmentation metrics are tested against defined reference masks.
- Optional dependencies remain isolated from the core install.

## Milestone 3 — Sequence and molecular biology
**Objective:** provide reliable sequence, molecular and structural-biology capabilities.

Scope:
- Add BioIO contracts for FASTA, FASTQ, GFF/GTF, VCF and molecular structures.
- Implement Biopython and BLAST+ adapters.
- Implement RDKit and PyMOL adapters.
- Add validated format conversion and typed scientific result schemas.
- Record tool versions, reference databases and parameters in provenance.

Exit criteria:
- Representative sequence and structure workflows run end to end.
- Input format errors and reference-database mismatches fail clearly.
- Results are reproducible from recorded inputs and parameters.

## Milestone 4 — Workflow orchestration and computational biology
**Objective:** let agents execute approved multi-step scientific workflows without hiding execution state.

Scope:
- Add workflow definitions, typed step inputs/outputs and dependency graphs.
- Add execution state, cancellation, timeouts, bounded resources and resumable artifact references.
- Add Scanpy and Squidpy integrations.
- Add GROMACS, HMMER, samtools/bcftools and Nextflow/Snakemake bridges where runtime requirements can be validated.
- Make provenance link every workflow step and artifact.

Exit criteria:
- At least one microscopy, one sequence and one single-cell workflow execute end to end.
- Failed or cancelled steps cannot be reported as successful.
- Workflow outputs are traceable to inputs, parameters and software versions.

## Milestone 5 — Ecosystem, certification and release
**Objective:** make BioMCP dependable for external contributors and research teams.

Scope:
- Publish an adapter development kit and integration certification rules.
- Add integration compatibility and security test matrices.
- Add benchmark protocols and reproducibility reports using public reference datasets.
- Expand documentation, executable examples and deployment guidance.
- Verify wheel and source-distribution installs outside the checkout.
- Establish release automation and a transparent lifecycle policy.

Exit criteria:
- External contributors can build and validate an adapter without changing BioMCP core.
- Every advertised integration has a lifecycle state backed by executable evidence.
- Supported Python versions and optional runtime combinations are tested.
- Release artifacts and examples are reproducible.

## Cross-milestone engineering rules
1. Do not rewrite the working registry, MCP client, broker or CLI without a demonstrated defect.
2. Keep core installation free of heavy scientific and GPU dependencies.
3. Prefer typed domain operations over arbitrary shell-command wrappers.
4. Enforce input, output, timeout, memory and path boundaries at execution edges.
5. Distinguish platform validation from scientific validation.
6. Never promote an integration to validated solely because its MCP server starts.
7. Require exact-head CI before merging changes.
