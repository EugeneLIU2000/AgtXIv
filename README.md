# AgtXIv

AgtXIv is a verification-aware protocol and pilot implementation for turning source-faithful scientific claims into bounded, evidence-backed assessments. Its V1 bridge aligns claim components with mathematical claims and projects verification results back without erasing physical meaning; query-relative dependency graphs remain supporting infrastructure. Each traced work is assigned one public Git repository, and each citable publication instance is identified by that repository plus an exact release.

## Start here

| Document or project | Role |
|---|---|
| [`docs/specifications/v2-paper-agentization.md`](docs/specifications/v2-paper-agentization.md) | **V2 normative architecture:** paper-first agentization, release, certification, and knowledge ingestion |
| [`docs/roadmaps/v2-end-to-end-implementation-plan.md`](docs/roadmaps/v2-end-to-end-implementation-plan.md) | **V2 execution baseline:** audited decisions, artifact coverage, M0--M8 milestones, and exit gates |
| [`AgtXIv.md`](AgtXIv.md) | **Current system specification** (v0.6); the single canonical design entry point |
| [`docs/specifications/v1-bridge.md`](docs/specifications/v1-bridge.md) | **V1 normative slice:** ScientificClaim--MathClaim alignment, conservative verification projection, and bounded Root Agent assessment |
| [`docs/specifications/mathematics-pipeline.md`](docs/specifications/mathematics-pipeline.md) | Mathematical decomposition and verification detail; graph optimization and reuse are post-V1 capabilities |
| [`docs/specifications/v0.3-to-v0.4-architecture-changes.md`](docs/specifications/v0.3-to-v0.4-architecture-changes.md) | Historical explanation of the v0.3-to-v0.4 architectural revision |
| [`docs/roadmaps/v1-implementation-checklist.md`](docs/roadmaps/v1-implementation-checklist.md) | Product-v1 implementation and release checklist for the Stabilizerness vertical slice |
| [`Stabilizerness/`](Stabilizerness/) | Active pilot artifacts, registry, claim DAGs, readers, and domain implementation |
| [`formal/`](formal/) | Lean 4 projects used by the pilot |
| [`pages/`](pages/) and [`tools/build_pages_site.sh`](tools/build_pages_site.sh) | Static site source and release assembly |
| [`Reference/`](Reference/) | Local implementation cache for frozen upstream sources; not a default per-work public-release path |

## AgtXIv protocol and pilot repository map

This monorepository develops the protocol, registries, and pilot. It is not the normative per-work publication layout defined in `AgtXIv.md` Section 10.1.

- `agents/`: source-bounded Paper Agent artifacts.
- `foundations/`: external mathematical foundation records.
- `graph/`: claim and paper dependency data.
- `schemas/`: machine-readable contract schemas.
- `figures/`: maintainable figure sources and publication exports.
- `docs/`: specifications, roadmaps, research notes, assets, and non-normative archives.
- `tools/`: validation and site-building scripts.

## Document policy

1. `AgtXIv.md` is the only unversioned canonical system specification.
2. A specification version is recorded in document metadata and Git history; files named `AgtXIv_v1.md` or `AgtXIv_v2.md` are not parallel authorities.
3. Product release `v1` is an implementation milestone, not the specification version.
4. Superseded documents and visual drafts under `docs/archive/` are retained only for provenance and are non-normative.
5. Generated site and inspection output (`_site/`, `tmp/`) is not versioned.

## Validation

Run the repository checks from the project root:

```bash
make bootstrap
make check
```

The project pins Python and its validation dependencies in `.python-version`,
`pyproject.toml`, and `uv.lock`. `make check` runs the offline fast profile through
the repository's aggregate validator. Use `make list-checks`, `make check-full`,
or `make check-nightly` to inspect or run the broader profiles. The full and
nightly profiles also require their declared Node, Lean, Bash, and `rsync`
toolchains; missing tools are reported explicitly rather than silently skipped.

The GitHub Pages workflow assembles the release with:

```bash
bash tools/build_pages_site.sh _site
```
