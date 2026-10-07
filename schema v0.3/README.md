# Schema contract ladder v0.3 — research/0.3.0 candidate framework

Schema v0.3 provides source ingestion, candidate dependency graphs, persistent execution accounting, Lean proof attempts, human-review records, and conditional chain certificates. Its workflow is **forward crawl → backward prune → bottom-up formalization**: collect relevant source evidence, select the branches needed by a query, then attempt their mathematical prerequisites first.

**Status: experimental; the research case remains `CHAIN_INCOMPLETE`.** Historical records demonstrate four-paper research, one real model-to-Lean step, and a separately constructed mathematical branch compiled in one environment. No automated model-to-Lean run has covered a real paper query graph. Source alignment remains unreviewed and accepted support edges remain zero.

This is the **schema contract ladder**, numbered separately from the older AgtXIv protocol versions and the wider AgtXIv V3 design.

## Start here

- [Getting started](GETTING_STARTED.md): prerequisites, public-checkout limitations, and execution instructions.
- [Workflow](WORKFLOW.md): stages, entry points, artifacts, and their evidence boundaries.
- [Progress and evidence boundaries](../docs/releases/schema-v0.3-progress.md): English analysis of the September changes, mathematical progress, and unfinished work.
- [Design](../docs/superpowers/specs/2026-09-19-schema-v03-design.md): contract rationale and dated revisions. [STATUS.md](STATUS.md) preserves the detailed historical record, primarily in Chinese.

## What the retained development records show

These figures describe historical scopes; they are not current test results or percentages of the paper proved.

| Scope | Recorded result | Remaining boundary |
| --- | --- | --- |
| Recursive research | Four papers; 240 target-paper candidates; 683 graph nodes and 269 support groups. | Zero accepted support edges; source completeness is not asserted. |
| Real proof worker | One model call produced one Lean theorem candidate for a source-bound normalization step. | Premise nonvacuity and source alignment remain unaccepted; no multi-node query proof. |
| Mathematical branch | 60 modules compiled in a common Lean v4.33.0 / mathlib / Physlib environment; 54 selected declarations audited: 44 theorems and 10 definitions. | Agents wrote and repaired the branch. Its terminal theorem is not yet bound to the research graph's query node. |
| Single-query dispatch | A retained-data stub demonstration reached five target-only attempts and six after upstream joins, compared with zero on the legacy graph. | The stub called neither a model nor Lean; it establishes dispatch reachability only. |

The active case is arXiv:2607.26154v1. Archive identifiers include `runs/research-doi-available-20260922`, `runs/proof-worker-normalization-attempt02-20260919`, `runs/candidate-compile-20260923`, and `runs/v03-revision-evidence-20260924`. **The public framework checkout omits `runs/`.** These identifiers refer to retained local evidence, not bundled downloadable examples. Some profiles and historical tools therefore require inputs absent from this checkout; the source release alone does not reproduce the reported results. See the [public artifact boundary](WORKFLOW.md#what-this-public-version-leaves-out).

## Implementation and boundaries

| Component | Present implementation | What it does not establish |
| --- | --- | --- |
| [Sources](host/INGEST.md) | Exact-version acquisition, frozen bytes, literal includes, UTF-8 spans, macro inventory, bibliography and identifier parsing. | Complete mathematical extraction, TeX expansion, bibliographic identity acceptance, or earliest origins. |
| [Candidates](host/SEMANTIC.md) | Bound response bytes and quotations, external statement requests, claim-index support, a separate mentions table, and conservative occurrence expansion. | A citation is not a supporting theorem. The new claim-reference response fields have no recorded live extraction yet. |
| [Graph](host/GRAPH.md) | Joint premises within groups (AND), alternative groups (OR), cycle handling, ancestor selection, shared costs, required bridges, blocker propagation, sensitivity diagnostics, and `COMPACT_V1`. | Scientific acceptance or optimality when costs are unknown or search is bounded. |
| [State and accounting](host/core.py) | Host-derived state, frozen SQLite plans, model/proof reservations, receipts, issues, and persistent provider-failure handling. | Calibrated decisions, known monetary cost when the provider does not report it, or automatic worker recovery. |
| [Research controller](host/SEMANTIC.md#recursive-controller) | Extraction, evidence reuse, source matching, admission, repeated pruning, all-candidate or source-label query selection. | A completed automatic proof chain; recursion still needs explicit arXiv identifiers or imported PDF sources. |
| [Proof worker and library search](host/PROOF_BACKEND.md) | Environment-bound lexical retrieval, root audits, bounded model-to-Lean attempts, actual declaration types, structure-held premises, axiom and direct proof-term evidence. | A search hit is not a binding. Compilation does not establish source alignment, nonvacuity, or full transitive composition. |
| [Review and certificate](host/PROOF_BACKEND.md#human-review-and-chain-certificate) | HumanReview templates and scoped decisions; ChainCertificate generation and audited recertification. | No recorded human reviews yet. ACCEPT lifts a support-group blocker inside a walk without rewriting research-graph disposition. |
| [PDF path](host/PDF_REGIONS.md) | Retained page images, region anchors, proof-context and recovery interfaces. | A page region is not an exact text quotation. Multimodal proof and retained-PDF recursive admission lack recorded execution coverage. |

## Execution and interpreting results

Use [Getting started](GETTING_STARTED.md) before running a command. `host/research.py` is the semantic research entry point; `host/proof_walk.py` separately consumes a prepared graph, frozen sources, a Lean environment, and root bindings or audits. `host/pipeline.py` and `host/validate.py` serve the older historical-DAG migration case. The archived `runs/latest.json` names that migration result, not the latest semantic recursion.

Each new research plan needs a fresh output directory. Without imported evidence, research can make real Codex CLI model calls using configured account authentication. `--network-sources` enables bounded source acquisition; `--imports` reuses explicitly identified evidence. Plans freeze their [model routing](host/MODEL_ROUTING.md), budgets, environment, and decision policy. The configured engine tiers do not imply measured quality equivalence or cost savings.

The default policy is strict. Explicit `CANDIDATE_EXPLORATION` allows unreviewed search and proof attempts while preserving review blockers and preventing scientific promotion. Source-label queries such as `--query-label thm:solvable` select bounded work; they do not establish complete paper coverage or change canonical source claims.

Start reading an actual run at `summary.json`, then inspect `checkpoint.json`, `frontier.json`, and `ledger.json`. Graph and checkpoint histories retain earlier states. Normal research completion exits **2** for `CHAIN_INCOMPLETE`; argument errors can also exit 2. Read stderr and the actual artifacts together rather than interpreting that code alone as success.

`research.py` emits no completed chain certificate. A proof walk's `CHAIN_CERTIFICATE_EMITTED`, when its gates are satisfied, means a **kernel-checked formal implication conditional on the premises read from Lean**. Open reviews and unknown nonvacuity remain visible. It does not mean that the paper is correct or that the formalization faithfully represents it. Definitions and theorem proofs have separate coverage; their counts must not be combined into a success rate.

## Contracts, authority, and further work

The [Draft 2020-12 contracts](schemas/research.schema.json) and [`host/core.py::derive_state`](host/core.py) define the machine-facing records and state derivation. Models propose candidates; the host owns state, blockers, and coverage. Only registered calibrated confidence can advance an automatic decision gate. Human acceptance is a separate scoped judgment. A graph root remains `FRONTIER` unless an exhausted-search record justifies `ORIGIN`.

Read the design together with its dated revisions and implementation corrections. Physlib remains part of the requested scope; separate Lean environments cannot be silently combined. [Lean evidence](lean/README.md), [candidate integration](lean/CANDIDATE_INTEGRATION.md), and [epoch migration](epoch-migration/README.md) distinguish historical environments, compilation scopes, and conditional mathematical statements. Historical source objections and the fixed-window monotonicity counterexample remain preserved.

This package serves the wider [AgtXIv vision](../AgtXIv.md), while implementing a bounded mathematical workflow. It does not change the [Charter's pending ratification](../CHARTER.md), replace the contracts governing older records, or establish completion of the wider V3 knowledge system.

Execution follows [AGENTS.md](../AGENTS.md): tests, validators, example replays, audits, and Lean builds require explicit authorization for the requested scope. Historical case authorization does not authorize a new run. All added or affected execution scenarios are tracked only in [`schema v0.1/PENDING_TESTS.md`](../schema%20v0.1/PENDING_TESTS.md). No test or build was run for this documentation revision.
