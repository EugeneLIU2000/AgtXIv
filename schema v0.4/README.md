# Schema contract ladder v0.4 — corpus dependency graph and foundation analysis

This is the **schema contract ladder** v0.4 (`$id` prefix `https://agtxiv.org/schema/research/0.4.0/`). It is not
the superseded AgtXIv *protocol* v0.4 of `docs/specifications/v0.3-to-v0.4-architecture-changes.md`.

**Status (2026-09-26, Revision 3):** contracts and host code are written and unit-tested offline on small synthetic
fixtures. One real test has run: 50 random quant-ph theory papers through the deterministic tier (S1–S5, no model),
loaded into a local Neo4j Community 2026.09.0 with every audit at zero rows
([runs/quant-ph-sample-20260926](runs/quant-ph-sample-20260926/INDEX.md)). No model has been called, so S6/S7, AUTO_EVAL_V1
and the P0 gate have not run. Read [STATUS.md](STATUS.md) for the evidence and what is still open. A clickable walk-through of the framework is
[`slides/chain-build/schema_v0.4_framework.html`](../slides/chain-build/schema_v0.4_framework.html).

Revision 3 (the owner's corpus and cost decisions): every accepted paper gets the same extraction (`EQUAL_FULL`, no
prioritized or audit arm); derivation papers without theorem environments are eligible; cited (EXPANSION) and
model-discovered (DISCOVERY) papers are admitted and counted apart from the random sample; extraction quality is
judged automatically by a blinded panel of model judges calibrated with decoys (AUTO_EVAL_V1); every stage gate is
a rule frozen at S0 and applied by the host; a WHOLE_PAPER_FOCUS extraction mode keeps the paper as one
cache-stable prompt prefix, and `host/cost.py` projects the money and time of a run from a dated price file. Two
independent static reviews of that code were then answered (2026-09-26; spec, end of Revision 3): the P0 gate
recomputes every stored estimate and checks every input's digest, strata carry the producing method version, decoys
match the premise's kind and are counted per rule, and the cost projection is tied to the run.

## What it is for

v0.3 follows one query paper into Lean, and most of its graph is unresolved requests. v0.4 orders the work by
cost: first build a cheap, typed claim dependency graph over many same-field papers, then use graph analysis to
*nominate* early, widely depended-upon claims and works, and only then spend Stage 3 (v0.3) effort on them.
Nominations are never status (I-10), and nothing here writes a VERIFIED state (I-1).

```
Stage 1  CORPUS GRAPH    papers → typed claim dependency graph (immutable deltas; Neo4j is a projection)
Stage 2  FOUNDATIONS     graph analysis → metrics and FOUNDATION_V1 nominations
Stage 3  KNOWLEDGE BASE  nominations → v0.3 library audit, human review, proof walk (via export_v03)
```

Design: [spec](../docs/superpowers/specs/2026-09-25-schema-v04-design.md) (normative; §2 invariants,
§7 stages S1–S9, §11 measurement gates, §15 open decisions, Appendix A row shapes).
Background: [theory-level autoformalization assessment](../docs/literature/2026-09-25-theory-level-autoformalization.md).

## Layout

| Path | Contents |
|---|---|
| `schemas/corpus.schema.json` | All v0.4 contract objects as `$defs` (Draft 2020-12; every record is closed except the open maps `Edge.props`, `CorpusManifest.size_limits` and the count map `ProjectionManifest.audit_counts`). v0.3 defs are reused by relative `$ref` to `../0.3.0/…`. |
| `schemas/*.schema.json` (16 more) | Thin wrappers for the top-level records (GraphDelta, DeltaSetManifest, ProjectionManifest, CorpusManifest, SamplingRecord, AnalysisPolicy, NodeMetrics, FoundationNomination, ReviewSample, HumanReviewV4, EvaluationPlan, Judgement, EvaluationReport, GateDecision, PricingProfile, CostProjection). |
| `host/contracts.py` | Offline schema registry (v0.4 + frozen v0.3 files); `validate(def, row)`. |
| `host/ids.py` | Every id except PaperVersion (`arxiv:<base>v<n>`) is `<prefix>:<64 hex>` of v0.3 `core.digest(core.canonical(identity))`; derivation ids keep `sha256:`; `seal`, `edge`, `make_delta`. |
| `host/anchors.py`, `works.py` | S3 deterministic anchor graph (+ its RESTATES host-rule delta); S4 works, `RESOLVES_TO`, `SAME_WORK`, `VERSION_OF`. |
| `host/extraction.py`, `matching.py` | S6 (WHOLE_PAPER_FOCUS: `plan_foci`, `build_focus_prompts`, `focus_response_to_delta`; LOCAL_BATCH: `build_local_prompt`, `response_to_delta`) and S7 prompt builders and response → delta converters. They never call a model. |
| `host/eligibility.py` | `THEOREM_OR_DERIVATION_V1`: theorem-like environments ≥ k or display equations ≥ m; the P-1 eligibility grid. |
| `host/autoeval.py` | AUTO_EVAL_V1: frozen EvaluationPlan, stratified samples, blinded cards, positive and decoy controls, judgement binding, the unanimous panel, the conservative precision bound, recall estimators, the EvaluationReport. No model call. |
| `host/gates.py` | Automatic gates: `p_minus_1` (S5), `p0`, `primary_policy`, `require_equal_coverage`. |
| `host/cost.py`, `profiles/pricing-mimo-20260922.json` | Cost projection of the corpus S6 policy and per-call cost from a dated PricingProfile (MiMo-V2.6-Flash/Pro, official pages of 2026-09-21/22). |
| `host/delta.py`, `invariants.py`, `reviews.py` | Delta store, manifests and merge; host checks G1–G15 before load; human-review templates and dispositions. |
| `host/projection.py`, `neo4j/` | Neo4j rows, fixed load templates and protocol, Query API client, CSV export; constraints, audits, browse templates, local compose example ([neo4j/README.md](neo4j/README.md)). |
| `host/analysis.py`, `review_sample.py` | S9 layers, importance brackets, count basis and dependent topics, FOUNDATION_V1, bootstrap over counted papers, edge precision, the PRIMARY admission check; seeded review samples and Wilson intervals. |
| `host/acquire.py` | S1 from a frozen metadata snapshot: the frame (primary category, v1 window) read with DuckDB from the Kaggle arXiv snapshot's Parquet copy, the version rule, rate-limited e-print acquisition from export.arxiv.org unpacked by the v0.3 bounded adapter, v0.3 parsing and the candidate outcome; snapshot lookups by arXiv id and by DOI (for EXPANSION). |
| `host/corpus.py`, `ledger.py`, `routing.py`, `profiles/engines-v2*.json` | Corpus manifest, seeded SAMPLE, EXPANSION and DISCOVERY rounds, S1 delta (PaperVersion rows + `INCLUDES`), the EQUAL_FULL coverage account; SQLite work ledger (also judge and discovery calls); `operation-routing-v2` with a GPT profile and a MiMo candidate profile. |
| `host/export_v03.py` | Stage 3 hand-off: a claim nomination's backward closure as a v0.3 graph. |
| `tests/` | Offline unit tests; `conftest.py` puts `schema v0.4/host` and `schema v0.3/host` on `sys.path`. |
| `runs/offline-checks-20260925/`, `runs/offline-checks-20260925-rev3/` | Saved outputs of the offline checks cited in STATUS.md (first build; Revision 3). |
| `snapshot/` | The pinned arXiv metadata snapshot: `fetch_arxiv_metadata.py` downloads the commit the runs used and checks it against the recorded manifest; `arxiv-metadata-2026-09-21/` keeps the original script, log and manifest of the 2026-09-25 download. |
| `viewer/claim-view.html` | One claim's backward closure, read live from Neo4j and drawn in the chain-build encoding (shape = kind, colour = source paper, ⊕ = junction, dashed box = the claim's paper). Untested (V04-37). |
| `runs/quant-ph-sample-20260926/` | The first real run: 50 random quant-ph theory papers through the deterministic tier, the P-1 gate, and a load into a local Neo4j 2026.09.0 (`INDEX.md`). |
| `runs/quant-ph-claude-agent-20260926/` | Run 2 on the same sample: S6, EXPANSION and S7 with the session's Claude model as a separate agent instead of an external model API. Paused by the owner after the first paper (`INDEX.md`). |

v0.3 is reused by import (`core`, `ingest`, `model`, `graph`, `model_routing`, …) and is never edited.
v0.4 host modules must not reuse a v0.3 module name, because `schema v0.4/host` comes first on the path.

## How the pieces connect

1. **Corpus (S0–S1).** `corpus.freeze_corpus_manifest` → `sample_record` (seeded order, host-set outcomes) →
   `includes_delta(record, manifest, metadata)` (the S1 HOST_RULE delta: the PaperVersion row of every ACCEPTED
   paper, with parser_sha256 from the manifest, plus Corpus → PaperVersion `INCLUDES`; later stages never
   re-assert PaperVersion, and the contract refuses a non-S1 delta that does).
2. **Build (S2–S7).** v0.3 `ingest.extract_paper` parses a frozen source;
   `anchors.build_anchor_delta(extraction, sources, parents=[s1["delta_id"]])` (S3; deterministic_yield goes in
   the delta `measurements`) and `build_restates_delta`; `works.build_work_delta(s3, extraction)` (S4); S6
   `extraction.response_to_delta` and S7 `matching.match_rows_to_delta` turn model responses into deltas. Every delta is validated by `contracts`.
3. **Manifest.** `delta.DeltaStore.put` stores each delta once by id; `make_manifest` → `check_manifest` returns the
   merged view (closed under parents and endpoints; one id with two different rows is refused).
4. **Check and review.** The caller must get `[]` from `invariants.check(view, work_identity, accepted)` before
   any load (`project`/`load` do not call it).
   `reviews.template` lists reviewable subjects; only a human ACCEPT yields `SOURCE_FROZEN_HUMAN_SIGNED`.
5. **Load (S8).** `projection.project(view, manifest, dispositions)` → `projection_manifest` →
   `load(QueryClient(...), rows, pm)`: schema, refuse another projection (v0.4 always rebuilds from empty),
   BUILDING, preflight, batched MERGE, audits, READY. Every failure raises LoadError; the manifest is set FAILED
   only once BUILDING was written.
6. **Gates and judgement.** `gates.p_minus_1` decides after S1–S4 (no model; yields from the anchor S3 deltas the
   view includes). The pilot's S6/S7 legs are judged by `autoeval`: `freeze_plan` (with the `producers` of each judge
   operation) → `draw_leg_sample` / `draw_match_sample` on the plan's manifest view → `leg_card` / `match_card`,
   `positive_controls`, `negative_controls` / `match_decoys` (decoys of the premise's kind) → `judgement` (with the
   call's receipt) → `panel_labels` → `precision_estimates` (per full stratum, worst decoy rule), `anchor_recall`,
   `union_legs` / `union_recall` → `report_inputs` → `report`. `cost.project` projects the full run from the pricing
   file (optionally from `cost.focus_plan` plans measured by the prompt builder, with reserves for the other stages);
   `gates.p0` recomputes every precision row (`autoeval.recheck`), ties the projection to the run and decides;
   `gates.primary_policy` derives the PRIMARY policy (importance methods cut to the admitted ones).
7. **Analyze (S9).** `analysis.analyze(view, manifest, policy, dispositions, admission=p0_decision, corpus=corpus_manifest,
   coverage=corpus.coverage_report(...))` returns metrics and nominations keyed by `policy_id` and `manifest_id`; a
   PRIMARY policy needs its P0 GO, the corpus manifest and a complete coverage report, and a view whose
   MODEL_EXTRACTION rows are all of the corpus extraction version; it writes nothing and sets no status.
8. **Hand-off.** `export_v03.export_v03(nomination, view, manifest, policy, dispositions)` gives a v0.3 graph that
   v0.3 `graph.prune_graph` accepts.

`tests/test_end_to_end.py` runs steps 1–5, 7 and 8 on a synthetic three-paper corpus (fake Neo4j client, synthetic model
responses); it then adds a HUMAN_ENTRY PrimitiveAssertion delta in a corrected manifest and checks the
PRIMITIVE-basis THEOREM_LIKE nomination. `tests/test_autoeval.py` covers step 6 and the Revision 3 builders on
synthetic papers (a theorem paper, its upstream paper with one S7 match to it, a three-equation derivation paper,
and a paper with a nested equation and a TeX comment).

## Offline test command

From the repository root (the worktree), with the repository Python (`.venv` lives in the main checkout, so a
worktree uses its absolute path):

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/Yingjian/Documents/GitHub/AgtXIv/.venv/bin/python -m pytest 'schema v0.4/tests' -q -p no:cacheprovider
```

Only offline checks on synthetic fixtures are authorized (repository policy: `AGENTS.md`); the tests use no
network, model, Neo4j server or Lean. Items still to be tested are in
[`schema v0.1/PENDING_TESTS.md`](../schema%20v0.1/PENDING_TESTS.md) §13 (V04-*).

## Built vs not run

| Built and unit-tested offline | Written but never run | Not built |
|---|---|---|
| Contracts; ids; S3/S4 builders; S6 (both modes)/S7 prompt and response converters; eligibility; delta store, manifests, invariants, reviews; projection rows and load protocol; analysis, review samples; corpus sampling, discovery, coverage account, ledger, routing; AUTO_EVAL_V1 host side; P-1 and P0 gates; cost projection; v0.3 export. Run on real data (`runs/quant-ph-sample-20260926/`): S1 acquisition (`acquire.py`), S3/S4, invariants, exploratory analysis, P-1, and the load, schema and audits on Neo4j Community 2026.09.0 | The Query API client against a server other than the local test one; `neo4j-admin` import of the CSVs `export_csv` writes (CSV writing tested); `compose.example.yaml`; re-load idempotency and fault injection on a real server (V04-11) | Metadata adapters (Crossref, OpenAlex); model dispatch for S6/S7, judges and discovery (MiMo or GPT); a general command-line runner; v0.4.1 statement clusters (§12) |

No result here says anything about real papers: P-1 and P0 (spec §11) have not been run.
