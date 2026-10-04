# Schema contract ladder v0.3 — research/0.3.0 candidate framework

**New here? Read [WORKFLOW.md](WORKFLOW.md) first.** It walks through the pipeline stage by stage (forward crawl →
backward prune → bottom-up Lean formalization), with the commands and how far each stage has run. This public version
omits the run records under `runs/`, which contain paper sources and verbatim extracted text (see
[What this public version leaves out](WORKFLOW.md#what-this-public-version-leaves-out)); `runs/` paths below refer to
that local archive.

This directory advances the **schema contract ladder**, separately from the older AgtXIv protocol version numbers. It implements source ingestion, candidate graph selection, durable run accounting, actual model-call receipts, Lean-environment evidence, library root audits, human review records and chain certificates. It does **not yet** implement a completed autonomous paper-to-proof loop: every stage exists, but no automated model→Lean run has covered a real query graph.

Read [STATUS.md](STATUS.md) for the current evidence and limits. The recursive controller has connected up to four papers (latest: `runs/research-doi-available-20260922`, 683 nodes, 0 accepted support edges). The 2026-09-24 revision adds a single-theorem query (`--query-label`), compact graphs and a new claim-reference policy; on `thm:solvable`, with library root audits, a stubbed proof walk (no model or Lean) reaches 5 attemptable nodes where the legacy graph gave 0. Separately, the 60-module Lean branch for that theorem compiles in one common environment. Source alignment is unreviewed, and these audits do not establish mathematical completeness.

The active case is [arXiv:2607.26154](https://arxiv.org/abs/2607.26154). The controller binds either every extracted target-paper candidate or, with `--query-label`, the claims at named source labels as queries, then repeatedly prunes the upstream graph to those queries. The older `pipeline.py` is a separate historical-DAG migration case; it is not the new semantic runner. No inventory is presented as a proven enumeration of all mathematical claims.

## Run and read

From the repository root, with the repository Python environment:

```sh
.venv/bin/python 'schema v0.3/host/research.py' \
  --paper 2607.26154v1 --query-label thm:solvable --candidate-exploration \
  --output 'schema v0.3/runs/my-new-run' \
  --max-papers 5 --max-model-calls 12
```

Each new plan needs a new output directory. Without explicit evidence imports, the controller uses real bounded Codex CLI calls and existing account authentication; requested engine classes do not assert measured model-tier savings. `--imports` reuses frozen prior candidate evidence with provenance, and `--network-sources` enables bounded version-pinned arXiv acquisition. [SEMANTIC.md](host/SEMANTIC.md) explains imported evidence, query binding, strict versus exploratory decisions, and resumption limits. Lean proof work is the separate `host/proof_walk.py` stage on a published graph ([PROOF_BACKEND.md](host/PROOF_BACKEND.md)). Case execution is authorized by the 2026-09-19 user request; unrelated test suites remain unexecuted under the repository policy.

Exit **2** means `CHAIN_INCOMPLETE`, even when implemented research operations succeed. This runner currently cannot emit a completed chain certificate. Its artifact audit is separate:

```sh
.venv/bin/python 'schema v0.3/host/audit_research.py' \
  --run 'schema v0.3/runs/my-new-run' \
  --output 'schema v0.3/runs/my-new-run/integrity-report.json'
```

Read `summary.json`, then `checkpoint.json`, `frontier.json` and `ledger.json`; immutable graph/checkpoint histories sit alongside them. The older migration command `pipeline.py` still supports `--lean --network --model`, emits its own `REPORT.md` and incomplete `chain-certificate.json`, and uses `validate.py` for that older case. `runs/latest.json` refers to that registered migration result, not the newer semantic recursion. Earlier failures and audits are retained. Neo4j files remain projection artifacts, not a running database service.

## Implemented boundaries

| Part | Implementation | What it does not establish |
|---|---|---|
| Frozen extraction | Reuses `tools/extract_provisional_claims.py`; literal includes, UTF-8 byte anchors, macro inventory, bibliography parsing, occurrence/curated overlap bridges | Semantic completeness, TeX expansion, correctness of overlap as claim identity |
| Source acquisition | Bounded exact-version arXiv source download and existing safe archive extraction | A unique entry file when upstream source is ambiguous |
| Internal references | Every reference is resolved or receives an explicit unresolved result | A citation/reference alone is not support; a pending classification is not a final exclusion |
| External identifiers | Explicit arXiv/DOI identifiers and bounded Crossref fallback with raw evidence | Fuzzy identity, subject support, exhaustive earliest-origin search; ADS adapter remains pending |
| Graph | SCC condensation, ancestors, AND/OR routes with shared costs, ties/bounds, mandatory bridges, blocked propagation, deletion sensitivity; lossless `COMPACT_V1` output (47.1 MB → 7.0 MB on the 4-paper graph) | Promotion of candidate edges or an optimum when costs are unknown |
| State and accounting | Host-only state derivation, SQLite plan/call/issue ledger, reservations, no-progress counters | Calibrated decisions without a registered held-out calibration curve |
| Lean | Current types, Prop hypotheses including structure fields, axiom audit, direct term-constant composition; the 60-module query branch compiles in one common environment (`runs/candidate-compile-20260923`) | Source alignment, inhabited scientific premises, or transitive composition through unaudited intermediates; the branch was agent-written, not produced by the proof worker |
| Historical case driver | Explicit migration replay and source ingestion of selected existing upstream papers; report/certificate artifacts | Does not substitute for new semantic extraction or recursive model work |
| New semantic graph | `host/candidates.py` binds actual response bytes, resolves occurrence mappings, records external statement requests; `CLAIM_REFERENCE_V1` adds claim-index support, a separate mentions table and occurrence expansion that never adds a cycle | A citation is not an upstream theorem; untyped uncertainty prose is a blocker; no extraction with the new fields has run yet |
| Recursive research controller | `host/research.py` connects extraction, cached/live matches, paper admission, repeated pruning, label or all-claim query binding, persistent budgets and failure classification; up to four-paper runs recorded | Recursion needs explicit arXiv identifiers or imported PDF sources; earliest-origin search is unchanged; source truth and completeness are unaccepted |
| Proof scheduler and worker | `host/scheduler.py`, `PlanLedger` and `proof_walk.py` reserve and run model→Lean attempts bottom-up with a statement-triviality probe; one real single-node run recorded | No real walk over a query graph yet; live worker supervision and crash recovery remain limited |
| Library retrieval | `host/library.py` + `lean/LibraryIndex.lean` index a frozen environment and write `LIBRARY_SEARCHED` root audits; unknown-identifier lookup feeds retries | Lexical and weak; a search result is never a binding or alignment |
| Review and certificate | `host/review.py` HumanReview templates/records; `host/certify.py` writes a ChainCertificate for every walk | An emitted certificate is a kernel-checked implication conditional on its listed premises, not the paper's truth; no review records exist yet; accepted support edges are 0, and a HumanReview ACCEPT only lifts a walk blocker, it does not set `SOURCE_FROZEN_HUMAN_SIGNED` |

## Design decisions and corrections

The supplied design is input to the implementation; the user's current request remains authoritative. PhysLib remains a requested dependency. A local PhysLib checkout has Pauli infrastructure, correcting the design's zero-Pauli statement. Its Lean/mathlib epoch differs from the existing AgtXIv projects. Separate audits record that difference and cannot be silently combined.

Historical graph edges lack AND/OR grouping. The migration imports all incoming support edges jointly, marking that assumption as an unreviewed candidate. It does not infer that each single edge is an independently sufficient route. The source's known false fixed-window monotonicity claim retains its own counterexample blocker.

An automatic model emits candidates and self-reported confidence. The host owns states, blockers, coverage, and gates. Only a registered calibrated confidence can advance an automatic gate; self-reports remain awaiting review. A threshold without a calibration curve is an anecdote. Promotion of a candidate edge to a load-bearing premise is a checked judgement, never a graph property.

Frozen plans may explicitly choose `decision_policy: CANDIDATE_EXPLORATION` to schedule unreviewed search/proof work. This does not grant scientific acceptance: review blockers propagate, `promotion_allowed` stays false, and OR routes remain explicit. Omitted policy is strict. Proof dispatch additionally requires `limits.max_proof_attempts` and a frozen `environment.lean_environment_sha256`; callbacks receive a durable reservation and must independently reserve model/money quotas. Interrupted reservations remain locked until worker termination is established.

The root tags remain `FRONTIER` unless an exhausted-search record justifies `ORIGIN`. A root with no incoming graph edge is not evidence that the earliest literature has been found. Bibliography membership alone does not admit another paper.

Definitions and theorem proofs have separate coverage rows. A definition elaborating, or a package building, never supplies a missing source-alignment judgement. A successful final chain would establish only a kernel-checked implication from explicit, environment-extracted premises to the formalized query. `research.py` issues no certificate and `pipeline.py`'s stays incomplete; a `proof_walk` certificate can print such a conditional conclusion, for its own queries only.

## Contracts and pending work

The Draft 2020-12 contracts are in `schemas/`. `host/core.py::derive_state` is the published state function. `host/graph.py` and [GRAPH.md](host/GRAPH.md) describe route semantics. [lean/README.md](lean/README.md) describes formal evidence and remaining mathematical gaps.

All added or affected test scenarios are tracked only in [`schema v0.1/PENDING_TESTS.md`](../schema%20v0.1/PENDING_TESTS.md). The unit suite (no model, no Lean by default; `AGTXIV_LEAN_TESTS=1` enables one real-Lean probe) runs, when authorized, as `.venv/bin/python -m pytest 'schema v0.3/tests' 'schema v0.3/host/test_clause_evidence.py' -q`. Current case execution does not replace unrun adversarial, concurrency, fresh-paper, calibration or full proof-loop tests.
