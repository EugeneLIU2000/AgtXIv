# Project state — October 2026

This page is for collaborators. It says what AgtXIv is trying to do, what has actually been measured, what has not
been established, which decisions are open, and what is planned. Every result below links to its record. Dates are
2026; "MEASURED" figures come from recorded runs, and estimates are labelled as estimates.

## In one minute

- **Purpose.** Make claims in theoretical physics behave like measurements rather than anecdotes: every result should
  state its conditions, be traceable to its sources and be independently checkable. Concretely: build the dependency
  graph of mathematical results across papers, find which results a field actually rests on, and check chains of them
  in Lean 4.
- **Two current rungs.** *Schema v0.3* follows one query claim of one paper down through the papers it relies on and
  tries to formalize that branch in Lean (published framework). *Schema v0.4* builds one dependency graph over a
  random sample of papers, so that "which results do many papers rest on" becomes a measured quantity (in
  development).
- **What works.** Source acquisition with exact versions and byte anchors, deterministic dependency extraction,
  cross-paper graph assembly and pruning, budgets and ledgers, a Neo4j projection with audits, Lean compilation and
  axiom audits in one pinned environment.
- **What does not work yet.** No run has gone automatically from a paper to a Lean-checked query. The v0.4 sample's
  papers are not yet connected to each other, because the model stages that create cross-paper links have not run at
  scale.
- **Next.** Decide how the model extraction stage (S6) should run, then run S6, EXPANSION and S7 on the sample.

## How the work is organised

AgtXIv has a *schema ladder*, numbered separately from its older protocol versions:

| Rung | What it is | State |
|---|---|---|
| v0.0 | Record types behind the web intake service (`web/`) | Runs end to end; scientific assessment axes are not implemented |
| v0.1 | Agent contracts: 8 modules, 23 operations, offline checkers | Contracts only |
| v0.2 | Compaction to 4 operations and 3 modules, with a provider-neutral host probe | Probe runs; no model called |
| [v0.3](../schema%20v0.3/WORKFLOW.md) | One query claim → cross-paper dependency branch → bottom-up Lean | Framework published; see below |
| [v0.4](../schema%20v0.4/README.md) | One dependency graph over a random corpus → foundation analysis | First real runs; see below |

The design documents are [v0.3](superpowers/specs/2026-09-19-schema-v03-design.md) and
[v0.4](superpowers/specs/2026-09-25-schema-v04-design.md). The two rungs fit together: v0.4 nominates the results
many papers rest on, and v0.3 builds and formalizes the chain for one of them (v0.4 §10).

## What has been measured

### Schema v0.3 (one query, case arXiv:2607.26154)

Recorded in [schema v0.3/STATUS.md](../schema%20v0.3/STATUS.md) (Chinese) and summarized in
[WORKFLOW.md](../schema%20v0.3/WORKFLOW.md#what-has-actually-been-run). The run records themselves stay in the
owner's local archive.

| Result | Limit |
|---|---|
| The recursive controller connected up to four papers: 240 claim candidates in the target paper, a 683-node query graph with 269 support groups. | 37 match judgements await review, 2 links were rejected, and **0** support edges are accepted. |
| A single-theorem query (`thm:solvable`) with library root audits reaches 5 attemptable nodes on the target graph and 6 after joining upstream papers (the legacy graph: 0). | Shown with a stub that calls neither a model nor Lean. |
| The 60 Lean modules behind that theorem compile in one environment; 54 declarations audit with only `propext`, `Classical.choice` and `Quot.sound`. | An agent wrote and repaired them; they are not yet bound to the graph's query node, and their fidelity to the paper is unreviewed. |
| One real single-node model→Lean attempt succeeded. | No real proof walk over a whole query graph has run. |

### Schema v0.4 (corpus graph)

| Result | Record |
|---|---|
| Contracts, host and gates pass their offline checks on synthetic data (no network, no model, no Neo4j server). | [offline checks](../schema%20v0.4/runs/offline-checks-20260925-rev3/) |
| **Sampling.** Frame: 76,946 quant-ph papers (v1 2015–2025) in a pinned arXiv metadata snapshot. In seeded random order, 80 were examined to accept 50 under the eligibility rule (≥ 1 theorem-like environment or ≥ 10 display equations): 17 ineligible, 13 undetermined (7 ambiguous main file, 3 PDF only, 3 non-UTF-8). | [run 1](../schema%20v0.4/runs/quant-ph-sample-20260926/INDEX.md) |
| **Deterministic tier** (from `\ref`/`\cite` alone, no model): 151 deltas; 0 invariant findings. Only 14 of the 50 papers have theorem-like environments and 11 yield dependencies: 135 junctions with 502 legs (107 claim→claim, 338 references to equations, 57 citations of other works inside proofs). | run 1 |
| **Cross-paper links: 0.** A link from a citation to a claim in another paper is made only by the S7 matching stage, after the cited paper has been acquired (EXPANSION) and read (S6); none of these has run at scale. The P-1 gate therefore decided `GO_WITH_EXPANSION`. | run 1, [P-1 record](../schema%20v0.4/runs/quant-ph-sample-20260926/p-minus-1.json) |
| **Neo4j.** The projection loads into Neo4j Community 2026.09.0 with all 14 audits at 0 rows; a [claim viewer](../schema%20v0.4/viewer/claim-view.html) draws one claim's chain from the live database. | run 1, [neo4j/README](../schema%20v0.4/neo4j/README.md) |
| **S6 pilot with the session's Claude model** (one subagent per paper, no external API): on paper 1, 3 windows took 32 minutes and gave 47 claims; the host accepted 1 window and rejected 2 under a shared-occurrence rule that the extraction instruction states only in half. | [run 2](../schema%20v0.4/runs/quant-ph-claude-agent-20260926/INDEX.md) |
| **Scale of S6 on the sample:** 511 windows over 8,874 occurrences (4,190 prose paragraphs, 3,013 display equations, 187 theorem or definition environments). At paper 1's pace one agent at a time would need about 90–110 hours (ESTIMATED). The owner paused the run to redesign this stage. | run 2 |

## What has not been established

- No chain from a paper's theorem down to its foundations has been checked end to end; every v0.3 run ends
  `CHAIN_INCOMPLETE`, and a successful chain would still prove only an implication from listed premises.
- No foundation nomination exists yet: the v0.4 graph has no cross-paper links.
- The quality of model extraction and matching has not been measured. The automatic judgement of v0.4 (AUTO_EVAL_V1:
  a blinded panel of model judges calibrated with decoys, and the pre-registered P0 gate) has not run.
- Model self-reported confidence is uncalibrated everywhere.
- Statement fidelity (Lean statement versus the paper's sentence) is unreviewed for every formal result.

## Open decisions

1. **How S6 runs.** (a) Keep full extraction as frozen, with every host check stated in the task (prepared as
   package V2). (b) A typed variant that keeps the same full coverage of every paper but changes the output: the model
   answers per occurrence whether it is a claim, its kind, the occurrences and citations it uses, and the host takes
   the statement text from the source. ESTIMATED to cut S6 output by 5–10×, at the cost of one claim per occurrence
   and no model-written conditions. A pilot on about 5 papers would measure both.
2. **Which model and how many at once**: the session's Claude model as subagents (one at a time or several in
   parallel), or an external route (MiMo-V2.6-Flash is the metered candidate; GPT routes exist).
3. **EXPANSION scope.** The prepared rule takes up to 25 cited works with an arXiv source, ordered by how many sample
   papers cite them inside proofs.
4. **Stabilizerness excerpts.** The earlier pilot keeps 1,648 verbatim excerpts from five papers, four of which are
   not licensed for redistribution; decide whether they stay public.

## Plan

| # | Milestone | Needs |
|---|---|---|
| 1 | S6 pilot on about 5 papers: full versus typed extraction, measuring time, tokens, accepted claims and legs | Decision 1; a model route |
| 2 | S6 on all 50 sample papers under one frozen policy | Pilot result; Decision 2 |
| 3 | EXPANSION: acquire and read the cited works; S7 matching | Network downloads (export.arxiv.org, one request per 3 s); Decision 3 |
| 4 | Rebuild, load Neo4j, first exploratory foundation analysis | Steps 2–3 |
| 5 | AUTO_EVAL_V1 and the P0 gate on the extraction | A judge panel route |
| 6 | v0.3: a real model→Lean proof walk on `thm:solvable` with root audits | Model and Lean authorization |
| 7 | Hand a v0.4 nomination to v0.3 for a chain build | Steps 4–6 |

## Reproducing and where things are

- **Public (this repository):** code, contracts, documentation, slides, and run records without paper text.
- **Local only (`local-archive/`, ignored by Git):** paper sources and PDFs, extraction records and deltas holding
  verbatim text, the v0.3 run archive, the Neo4j database, and a third-party talk's recovered slides.
- **Rebuilding:** the arXiv metadata snapshot is pinned
  ([fetch script](../schema%20v0.4/snapshot/fetch_arxiv_metadata.py), about 3 GB, verified file by file); e-prints come
  from export.arxiv.org by id; sampling is seeded and the deterministic tier is reproducible. Model stages cost money
  or quota to rerun. The run scripts under `schema v0.4/runs/` are records of specific runs and name the owner's
  checkout path; adjust it before reusing one.
- **Papers studied but not distributed:** [REFERENCES.md](REFERENCES.md).
- **Licences:** code MIT, documentation and data CC BY 4.0 ([LICENSING.md](../LICENSING.md)).

## Taking part

Read [CONTRIBUTING.md](../CONTRIBUTING.md): work on a branch, open a pull request into `main`, sign off every commit
(DCO), keep paper text out of the repository, and record test scenarios in
[`schema v0.1/PENDING_TESTS.md`](../schema%20v0.1/PENDING_TESTS.md); tests run only when explicitly decided.
