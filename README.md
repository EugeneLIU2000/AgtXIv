# AgtXIv

AgtXIv is a verification-aware protocol and pilot implementation for resolving scientific claims into source-grounded, reusable contracts and query-relative dependency graphs. Each traced work is assigned one public Git repository, and each citable publication instance is identified by that repository plus an exact release.

## Start here

| Document or project | Role |
|---|---|
| [`AgtXIv.md`](AgtXIv.md) | **Current system specification** (v0.6); the single canonical design entry point |
| [`docs/specifications/mathematics-pipeline.md`](docs/specifications/mathematics-pipeline.md) | Normative detail for mathematical claim decomposition, Oracle search, Lean construction, DAG optimization, and reuse |
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
python3 tools/validate_claim_dag.py
python3 tools/validate_root_partitions.py
python3 tools/validate_pilot.py
python3 tools/validate_lean_formalization.py
python3 tools/validate_varela_formalization.py
python3 tools/validate_pages_site.py _site
```

The GitHub Pages workflow assembles the release with:

```bash
bash tools/build_pages_site.sh _site
```
