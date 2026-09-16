# AgtXIv

AgtXIv turns scientific literature into auditable and reusable knowledge, preserving each claim's sources, assumptions, evidence, applicability, conflicts, and unresolved questions. The current [V3 design proposal](AgtXIv.md) connects query-independent Paper Agents to an accumulating knowledge base, with vibefeld as a mathematical argument layer between source claims and Lean, six separate assessment axes, and contribution records relative to an explicit knowledge baseline.

V3 implementation has begun with an experimental [schema v0.0 package](schema%20v0.0/README.md), offline contract checks, bounded local source inspection, and a six-axis reader. It is not a completed scientific pipeline; [the execution status](docs/roadmaps/v3-execution-status.md) records coverage and remaining work. Existing V1/V2 code, fixtures, pilot results, and records retain their original scope and authority. The proposed Charter remains pending ratification.

## Start here

The [research website](web/README.md) is the primary V3 reader and live arXiv
submission service. It retrieves real source bytes, produces source-linked
candidates and retains the result. The [release plan](docs/roadmaps/publishable-release-plan.md),
[schema audit](docs/audits/schema-release-audit.md) and
[TeX technical report](docs/technical-report/README.md) document the release
requirements, exact contract coverage and scientific boundaries. Source analysis
does not perform any of the six scientific assessments.

To run the website with Node.js 26.7.0:

```bash
cd web
npm run build
npm test
npm run dev
```

Open `http://127.0.0.1:8787`, submit a new arXiv identifier, and follow the retained
job to its result. Existing `pages/` and `demo_*` surfaces keep their historical or
research roles; they are not the new submission service.

| Document or project | Role |
|---|---|
| [`CHARTER.md`](CHARTER.md) | **Pending Charter proposal:** `AgtXIv-Charter/1.0`; highest-level normative authority only after authorized ratification on canonical `main` |
| [`ADR 0007`](docs/adr/0007-adopt-project-charter.md) | **Pending Charter-adoption decision:** rationale, authorization conditions, ratification commit, and effective-time rule |
| [`AgtXIv.md`](AgtXIv.md) | **Current V3 design proposal:** goals, full framework, argument layer, six-axis assessment, contribution, reuse, migration, and acceptance boundaries; subordinate to an adopted Charter only after ratification |
| [`docs/roadmaps/v3-implementation-plan.md`](docs/roadmaps/v3-implementation-plan.md) | **V3 implementation plan:** P0–P8 tasks, dependencies, responsible roles, deliverables, and acceptance criteria |
| [`schema v0.0`](schema%20v0.0/README.md) | **Experimental V3 contracts:** 64 English record schemas and a complete Chinese field reference |
| [`V3 execution status`](docs/roadmaps/v3-execution-status.md) | **Implementation evidence:** task-by-task progress, commands, checks, remaining scientific and service boundaries |
| [`docs/architecture/v3-vibefeld-integration.md`](docs/architecture/v3-vibefeld-integration.md) | **V3 integration design:** fixed-commit upstream findings, full argument snapshot, trust boundaries, and proposed acceptance cases |
| [`docs/specifications/v2-paper-agentization.md`](docs/specifications/v2-paper-agentization.md) | **V2 normative architecture:** paper-first agentization, release, certification, and knowledge ingestion; subordinate to the Charter after ratification |
| [`docs/governance/v2-charter-conformance.md`](docs/governance/v2-charter-conformance.md) | **Prospective V2 Charter conformance:** principle-by-principle status, known six-axis conflict, and post-adoption binding requirements |
| [`docs/roadmaps/v2-end-to-end-implementation-plan.md`](docs/roadmaps/v2-end-to-end-implementation-plan.md) | **V2 execution baseline:** audited decisions, artifact coverage, M0--M8 milestones, and exit gates |
| [`v0.6 pre-V3 archive`](docs/archive/specifications/AgtXIv-v0.6-pre-v3-2026-09-05.md) | Historical cross-version design reading copy; original bytes remain in Git history |
| [`docs/specifications/v1-bridge.md`](docs/specifications/v1-bridge.md) | **V1 normative slice:** ScientificClaim--MathClaim alignment, conservative verification projection, and bounded Root Agent assessment |
| [`docs/specifications/mathematics-pipeline.md`](docs/specifications/mathematics-pipeline.md) | Mathematical decomposition and verification detail; graph optimization and reuse are post-V1 capabilities |
| [`docs/specifications/v0.3-to-v0.4-architecture-changes.md`](docs/specifications/v0.3-to-v0.4-architecture-changes.md) | Historical explanation of the v0.3-to-v0.4 architectural revision |
| [`docs/roadmaps/v1-implementation-checklist.md`](docs/roadmaps/v1-implementation-checklist.md) | Product-v1 implementation and release checklist for the Stabilizerness vertical slice |
| [`Stabilizerness/`](Stabilizerness/) | Active pilot artifacts, registry, claim DAGs, readers, and domain implementation |
| [`formal/`](formal/) | Lean 4 projects used by the pilot |
| [`web/`](web/README.md) | Primary V3 reader, actual arXiv intake, versioned HTTP API and standalone Worker build |
| [`pages/`](pages/) and [`tools/build_pages_site.sh`](tools/build_pages_site.sh) | Legacy static pilot site source and release assembly |
| [`Reference/`](Reference/) | Local implementation cache for frozen upstream sources; not a default per-work public-release path |

## AgtXIv protocol and pilot repository map

This monorepository develops the protocol, registries, and pilot. Historical per-work publication rules remain in the [v0.6 archive, Section 10.1](docs/archive/specifications/AgtXIv-v0.6-pre-v3-2026-09-05.md#101-per-publication-repository-and-canonical-referencing); the proposed V3 module and storage layout is described in `AgtXIv.md` Sections 11–12.

- `agents/`: source-bounded Paper Agent artifacts.
- `foundations/`: external mathematical foundation records.
- `graph/`: claim and paper dependency data.
- `schemas/`: machine-readable contract schemas.
- `schema v0.0/`: experimental V3 contracts; separate from historical V1/V2 schemas.
- `figures/`: maintainable figure sources and publication exports.
- `docs/`: specifications, roadmaps, research notes, assets, and non-normative archives.
- `tools/`: validation and site-building scripts.
- `web/`: the maintained V3 website and live source-analysis service; generated public copies are checked against their maintained inputs.
- `src/agtxiv_web/`: bounded arXiv source extractor and its strict analysis response schema.
- `local-archive/`: ignored preservation copies of unique historical local evidence, indexed by the archive manifest.

## Document policy

1. `CHARTER.md` (`AgtXIv-Charter/1.0`) is pending ratification. Only after the qualifying canonical-`main` commit exists does it become the highest-level normative authority, with the hierarchy Charter > version specifications and governance > ADRs, contracts, schemas, and plans > implementation and generated outputs.
2. `AgtXIv.md` is the current cross-version design entry point, now carrying the V3 proposal. It does not change Charter ratification, replace V1/V2 authority over historical records, or establish completed V3 implementation. Older section references resolve against the applicable archived or Git version.
3. A specification version is recorded in document metadata and Git history; files named `AgtXIv_v1.md` or `AgtXIv_v2.md` are not parallel authorities.
4. Product release `v1` is an implementation milestone, not the specification version.
5. Superseded documents and visual drafts under `docs/archive/` are retained only for provenance and are non-normative. The v0.6 reading archive identifies the original file hash and commit and only adjusts relative links for relocation. Pre-Charter immutable records retain the exact contracts and authority boundaries they originally bound; adoption does not silently rewrite or promote them.
6. Generated site and inspection output (`_site/`, `tmp/`) is not versioned.

## Validation

For this release's schema inventory, web projection and technical report:

```bash
.venv/bin/python tools/audit_schemas.py --check
.venv/bin/python tools/export_web_library.py --check
node --test tests/web/intake.test.mjs
.venv/bin/python -m pytest tests/web tests/test_schema_audit.py -q
.venv/bin/python docs/technical-report/generate_appendix.py --check
bash docs/technical-report/build.sh
```

These checks complement the repository validation below. The complete live HTTP
receipt for a newly submitted paper is retained under
[`docs/evidence/publishable-release/`](docs/evidence/publishable-release/).

For the new V3 experimental contracts and local mechanisms only:

```bash
.venv/bin/python tools/generate_v3_schema_v00.py --check
.venv/bin/python tools/validate_v3.py --bundle-only
.venv/bin/python -m pytest tests/v3 -q
```

These checks do not run a paper demo, vibefeld, Lean or a scientific experiment. They do not replace the repository-wide check below.

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
