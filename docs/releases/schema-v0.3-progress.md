# Schema v0.3: progress and evidence boundaries

Date: 2026-10-05. Review method: static reading of the current source, design, change history, and retained local reports. No tests, validators, example replays, model calls, or Lean builds were run for this review.

**AgtXIv schema v0.3 is a research framework for constructing and inspecting candidate mathematical dependency chains.** Its source-ingestion, graph, accounting, proof-worker, review, and certificate components exist. Historical runs demonstrate recursive source work, a real single-step model-to-Lean result, and a separately constructed mathematical branch compiled in one environment. They do not demonstrate an autonomous paper-to-proof run over a real query graph. The current research case remains `CHAIN_INCOMPLETE`, with zero accepted support edges.

This document is an English reading guide to the implementation and its progress. It does not replace the contracts or retroactively change historical records. Start with the [schema package](../../schema%20v0.3/README.md), then use the capability map below to find the relevant implementation.

## 1. What this version contributes to the project

The project's long-term objective is to let new research start from an auditable, reusable knowledge frontier. A paper's claims, assumptions, dependencies, evidence, disagreements, and unresolved questions should remain attributable as knowledge accumulates. The [V3 design proposal](../../AgtXIv.md) expresses that wider objective; the [Charter](../../CHARTER.md) remains marked pending ratification.

Schema v0.3 implements a narrower mathematical research workflow:

1. Freeze an identifiable paper version and extract candidate mathematical claims.
2. Trace internal support and relevant external sources, retaining unresolved requests.
3. Repeatedly select the dependency branches needed by the chosen query.
4. Search the frozen Lean environment and attempt formalization from prerequisites toward the query.
5. Preserve explicit premises, source-alignment questions, proof evidence, review decisions, and remaining blockers.

This is the design's **forward crawl → backward prune → bottom-up formalization** pattern. Pruning bounds the expensive proof work. Deterministic host programs own bookkeeping and state; models propose candidates. The [schema v0.3 design](../superpowers/specs/2026-09-19-schema-v03-design.md) and [state implementation](../../schema%20v0.3/host/core.py) define that boundary.

Three names must remain separate:

| Name | Meaning |
| --- | --- |
| **Schema v0.3 / `research/0.3.0`** | This package's research-contract version. |
| **AgtXIv V3** | The wider design for Paper Agents, separate assessment axes, knowledge accumulation, and contribution records. |
| **Historical AgtXIv protocol v0.3** | An older protocol specification, on a different version ladder. |

A label-specific proof query is a bounded work selection. It does not redefine the canonical paper inventory or establish a query-independent Paper Agent release. Likewise, this schema package does not establish complete implementation of the wider V3 knowledge base, all six assessment axes, or incremental knowledge reuse.

## 2. How to read the evidence

The public framework branch and the development checkout have different artifact scopes. The public `schema-v0.3-framework` branch excludes `schema v0.3/runs/`; the local reports cited below are retained development evidence, not downloadable evidence bundles included by this document. Their identifiers are given as code so they are not mistaken for public links. Maintained source and explanatory documents are linked normally.

Consequently, historical numerical results here are **reported from inspected local records**. A public reader can inspect the implementation and reported boundaries, but cannot independently reconstruct those results from the slim framework checkout alone. Local records also contain machine-specific paths and external environment references. Publishing this guide does not establish portable reproduction.

| Term used here | What it establishes | What it leaves open |
| --- | --- | --- |
| **Implemented** | The mechanism is present in source. | Whether the relevant execution path has been exercised. |
| **Historical run** | A retained report records an operation on specific inputs and source bytes. | Whether current or changed code still behaves that way. |
| **Artifact audit** | A particular audit checks hashes, bindings, receipts, or reconstruction within its scope. | Mathematical correctness, semantic completeness, and source alignment. |
| **Kernel-checked theorem candidate** | Lean accepted a proof of the recorded formal statement in a specified environment. | Whether it is the paper's intended statement or its premises describe the intended scientific situation. |
| **Elaborated definition** | Lean accepted a definition's type and value. | Whether the definition captures the intended meaning or avoids an inappropriate domain. |
| **Human acceptance** | An explicit review decision over an identified subject and scope. | Automatic promotion of unrelated graph records or whole-paper truth. |

Source alignment means comparing the original assertion and its conditions with the formal statement. Nonvacuity means establishing that the assumptions can actually hold. Composition evidence means that an audited proof term uses the required predecessor declaration; a shared import alone does not show that use. These distinctions motivate the [Lean evidence interface](../../schema%20v0.3/lean/README.md).

## 3. Major phases of development

**September 19: contracts and an executable candidate workflow.** The framework added program and model receipts, host-derived states, persistent budgets, source ingestion, support groups, recursive admission, pruning, isolated proof attempts, and Lean-environment audits. Early research runs connected multiple papers. A separate source-bound normalization step produced one real model-generated Lean theorem candidate. The [September 19 review](../../schema%20v0.3/REVIEW-2026-09-19.md) also documented graph-size failures, provider-quota handling gaps, and the missing integrated proof chain.

**September 20: explicit model routing and retained-work continuation.** New plans freeze operation-specific model and effort choices. Successful output batches can be reused; provider quota, authentication, and rate failures persistently stop new dispatches. A bounded graph reader addresses the earlier generic JSON size mismatch. In the recorded target continuation, Luna reused 17 successful output ranges and attempted 22 more; Terra subsequently filled the remaining two failed ranges. All 39 target output ranges then had candidate responses, yielding 240 candidates. This is output-range completion, not evidence that every mathematical claim was found. See the [routing and reuse contract](../../schema%20v0.3/host/MODEL_ROUTING.md) and [September 20 review](../../schema%20v0.3/REVIEW-2026-09-20.md).

**September 22: incremental upstream joins and source-boundary work.** Existing matches were recovered and reused, Xu's appendix candidates were integrated, and further matches were retained individually. The recorded four-paper graph reached 683 nodes and 269 support groups, with 37 unreviewed judgments, two rejected joins, and zero accepted support edges. DOI source availability, PDF inputs, premise and clause evidence, corrections, and source-reading amendments gained explicit interfaces. Several of those new interfaces remained unexecuted. The [September 22 review](../../schema%20v0.3/REVIEW-2026-09-22.md) preserves the incremental sequence.

**September 22–24: mathematical construction and a common environment.** Work progressed from normalized reduced robustness of magic (RoM), context reconstruction, and graph duality to weighted perfect-graph duality, a closed form, a square-root bound, and an attaining state. Additional chains addressed capacity, dimension bounds, explicit Jordan–Wigner windows, and historical Hurwitz constructions. The September 23/24 compilation bundle records 60 compiled modules and an audit of 54 selected declarations. These were agent-written and repaired modules, not an automatically generated research-controller proof chain. See [candidate integration](../../schema%20v0.3/lean/CANDIDATE_INTEGRATION.md).

**September 24: a single query reaches proof dispatch.** `--query-label thm:solvable`, `CLAIM_REFERENCE_V1`, compact graph output, library-root audits, review records, certificate generation, and statement-triviality probes were connected. A retained-data demonstration with a stub backend reached five target-only attempts and six attempts after upstream joins; the legacy graphs reached zero. The demonstration made no model calls and ran no Lean proofs. The latest section of [STATUS.md](../../schema%20v0.3/STATUS.md) describes this revision and explicitly supersedes earlier statements about missing compilation or interfaces.

## 4. Capability map

| Component | Present capability | Release boundary |
| --- | --- | --- |
| [Contracts and state](../../schema%20v0.3/schemas/research.schema.json) | Typed plans, receipts, support groups, declaration bindings, premise and coverage records, issues, reviews, certificates; host-owned state derivation. | Models cannot write acceptance or coverage. No registered calibration evidence establishes autonomous scientific acceptance. |
| [Source ingestion](../../schema%20v0.3/host/INGEST.md) | Versioned source freezing, UTF-8 byte anchors, literal includes, macro inventory, bibliography parsing, bounded acquisition and identifier lookup. | No TeX execution or semantic-exhaustiveness claim. Citation identity and claim support are separate judgments. |
| [Semantic candidates](../../schema%20v0.3/host/SEMANTIC.md) | Source-bound model rows, new exact quotations, explicit external statement requests, scoped batching, incremental imports and matches. | Full context supplied to a model is not evidence of complete reading. Exact-row deduplication is not semantic deduplication. |
| [Reference policy](../../schema%20v0.3/host/SEMANTIC.md#claim-references-claim_reference_v1) | Direct intra-response claim indexes; mentions separated from support; shared occurrences conservatively expanded with cycle protection. | No new extraction has exercised the added response fields. Recursive joins do not yet merge mentions tables across papers. |
| [Graph engine](../../schema%20v0.3/host/GRAPH.md) | Joint premises within groups (AND), alternative groups (OR), cycle condensation, query ancestors, required bridges, shared costs, blocker propagation and sensitivity diagnostics. | Unknown costs or bounded search retain alternatives; graph structure cannot accept a scientific dependency or prove an optimum outside the supplied cost model. |
| [Accounting](../../schema%20v0.3/host/core.py) | Frozen SQLite plans, durable model and proof reservations, receipts, issue records and provider-failure circuit. | Unknown monetary costs remain unknown; interrupted workers are not automatically adopted or refunded. |
| [Research controller](../../schema%20v0.3/host/research.py) | Repeated extraction, source matching, admission and pruning, all-candidate or source-label queries, typed failure reporting. | Explicit identifiers or imported PDF sources are still needed; earliest-origin search remains incomplete. This entry point does not emit a completed proof certificate. |
| [Library retrieval](../../schema%20v0.3/host/library.py) | Environment-bound declaration index, lexical retrieval, root-search audit records and retry hints for unknown identifiers. | Search results are unaccepted candidates. The recorded prop-v2 index has 19,078 rows but no Physlib, QuantumInfo or Quantumlib rows. |
| [Proof worker](../../schema%20v0.3/host/PROOF_BACKEND.md) | Reserved bottom-up attempts, frozen source context, bounded generated Lean terms, declaration/premise/axiom/proof-term evidence. | One real single-step run exists; no real proof-worker walk over the paper's query graph has completed. Source alignment and nonvacuity require separate evidence. |
| [Reviews and certificates](../../schema%20v0.3/host/PROOF_BACKEND.md#human-review-and-chain-certificate) | HumanReview templates, subject-hash binding, conditional ChainCertificate generation and audit-before-recertification. | No recorded human reviews yet. Support-group ACCEPT lifts a walk blocker, without changing research-graph disposition. Strict-mode human acceptance still has an unresolved policy boundary. |
| [PDF sources](../../schema%20v0.3/host/PDF_REGIONS.md) | Retained PDFs, ordered page images, region anchors, separate local proof contexts, recovery and amendment interfaces. | Region binding is not exact TeX quotation. The multimodal proof path and retained-PDF recursive admission lack recorded execution coverage. |

`COMPACT_V1` reduces repeated query-set data. The September 24 record reports 47,063,313 bytes becoming 7,009,523 bytes for the four-paper graph and byte-identical legacy reconstruction of 138 historical graph/assembly pairs. This is an artifact-size and compatibility result, not a larger scientific coverage claim.

The proof worker's statement-triviality probe rejects a candidate as an available dependency when a small tactic set immediately proves its type, or when the probe is inconclusive. Failure of those tactics is only a limited filter; it does not establish that the candidate is as strong as the source.

## 5. What the mathematical branch now establishes

The central case is arXiv:2607.26154v1. Its `thm:solvable` branch relates reduced RoM to a graph quantity under no-active-dependency and perfect-graph assumptions. RoM is an optimization over signed stabilizer decompositions; the graph captures incompatibility among the measured Pauli observables.

The [integration note](../../schema%20v0.3/lean/CANDIDATE_INTEGRATION.md) explains how the candidate branch joins these pieces:

- **Faithful optimization objects:** augmented atoms retain the normalization constraint; feasibility, an attained minimum, finite strong duality, and convex-generator invariance support the actual reduced-RoM definition.
- **Pauli/context construction:** no active dependencies yield the required sign domain; frame extension, physical context states, projected coordinates, and atom refinement construct the representation bridges.
- **Graph optimization:** clique-cover attainment, weak duality, perfect-graph replication, integer cover arguments, and real-weight approximation lead to weighted duality and the candidate closed form.
- **Bound and attainment:** the concrete Physlib bridge connects matrix expectations; normalized clique involutions and a positive clique state give the square-root bound and an attaining state.
- **Capacity and dimension:** binary Gram and general anticommuting-matrix routes support dimension ceilings; explicit Jordan–Wigner families support an extremal-window construction. Hurwitz identities are an additional historical-source branch, not acceptance of that literature's full exclusion argument.

The local bundle `runs/candidate-compile-20260923/SUMMARY.json` records:

| Recorded scope | Result |
| --- | --- |
| Candidate import closure | 60 modules; 60 successful compilation receipts. |
| Environment | Lean v4.33.0, Physlib's mathlib revision `db584cd6`, and migrated AgtXIv/Quantumlib layers. |
| Selected declaration audit | 54 declarations: 44 theorems and 10 definitions. |
| Selected composition evidence | 65 direct proof-term witnesses. |
| Axiom union | `propext`, `Classical.choice`, `Quot.sound`. |
| Remaining audit-scope qualification | 2,563 term dependencies reported as unaudited; selected witnesses do not constitute a complete transitive composition audit. |
| Source acceptance | `source_alignment_accepted=false`. |

The terminal candidate `AgtXIv.ReducedRoM.perfect_window_closed_form_bound_and_attainment` gives the closed form and square-root bound for every density matrix, together with existence of a state attaining the bound. It retains `hNoActive`, `hPerfect`, and the `MeasurementWindow` fields: a nonempty window, involutive observables, nonidentity support, and distinct phase classes. The [query feasibility analysis](../../schema%20v0.3/lean/QUERY-FEASIBILITY.md) explains why these conditions and the source-to-formal comparison matter.

This terminal declaration is not yet bound to the research graph's query node: `query_declaration` remains null. Its accepted Lean implication and the paper's accepted claim are therefore separate unfinished work products.

Earlier common-environment migrations have their own scopes, including an 82-module historical closure and subsequent extensions. Their declaration totals overlap and must not be added to the 54 selected targets above. Old module comments saying “uncompiled” predate the later frozen compilation bundle; [the Lean README](../../schema%20v0.3/lean/README.md) explains why those source bytes were preserved. Historical success receipts apply to their recorded snapshots, not automatically to later edits.

## 6. Current case results and unresolved work

The local `runs/research-doi-available-20260922/summary.json` is the retained multi-paper research result:

| Metric | Recorded value |
| --- | ---: |
| Papers with extraction artifacts | 4 |
| Target-paper candidate claims | 240 |
| Query graph nodes / support groups | 683 / 269 |
| Unreviewed match judgments / rejected joins | 37 / 2 |
| Accepted support edges | 0 |

That result explicitly records `proof_backend=NOT_CONNECTED`, `source_completeness_asserted=false`, and `CHAIN_INCOMPLETE`. Node counts include requests and unresolved occurrence placeholders, so they are not paper-claim or theorem counts. The subsequent single-query stub demonstration is a separate artifact, not a completed continuation of this research result.

The real normalization-step result in `runs/proof-worker-normalization-attempt02-20260919` records one model call and one Lean theorem candidate using the audited `normalized_l1` declaration. The actual normalization assumption remains explicit; its nonvacuity and source alignment were not accepted. It demonstrates a real automatic step, without establishing a multi-node query proof.

Several issues remain substantive:

- **Source and dependency acceptance:** exact byte or region anchors do not decide support, joint assumptions, or source completeness. Bibliographic access is not an accepted claim-to-claim connection.
- **Origins and corrections:** Lovász/Berge and anticommuting-matrix provenance still have open source and statement links. Newman has a recorded erratum lead; Hurwitz reading amendments distinguish contradiction assumptions from asserted conclusions. No earliest-origin completion is claimed.
- **Recovery and PDF execution:** a Hurwitz model response with 26 raw candidate rows was retained after local postprocessing failed. Recovery and amendment code do not themselves establish a successful recovered run or accepted graph.
- **Source-domain questions:** the nonempty measurement condition is used in the source proof even though it is not explicit in the main theorem heading. The later domain-review addendum narrows the earlier objection; the intended nonempty theorem must not be dismissed using an empty-domain case.
- **Unchanged counterevidence:** the historical fixed-window monotonicity counterexample remains relevant to its original statement. Compiling a different branch does not remove it.
- **Integration and evaluation:** a real selected-query model-to-Lean walk, reviewed declaration binding, source-premise and clause coverage, calibration, library retrieval quality, worker recovery, and portable reproduction remain unfinished or insufficiently exercised.

The wider vision also requires keeping source fidelity, mathematical correctness, formal alignment, semantic applicability, empirical support, and computational reproducibility separate. This version supplies mechanisms and evidence for parts of that work. It does not supply one combined whole-paper success score.

## 7. Release claims supported by this review

The appropriate release description is:

> AgtXIv schema v0.3 is an experimental, source-grounded framework for recursive mathematical-claim research and conditional Lean proof evidence. It implements candidate dependency graphs, persistent execution accounting, review boundaries, and proof-worker interfaces. Retained development records include four-paper research, one real model-to-Lean step, and a separately constructed 60-module mathematical branch. End-to-end autonomous query proof and source-aligned scientific acceptance remain incomplete.

An emitted ChainCertificate, when its gates are satisfied, expresses a **kernel-checked formal implication conditional on its listed premises**. It is distinct from accepted source alignment and from the research graph's accepted support-edge count. This review does not claim that the case has such a completed accepted certificate.

Do not advertise complete extraction of all mathematics, arrival at the earliest literature, proof of the whole paper, measured model-tier savings, production readiness, or independent reproducibility from the slim public checkout. Each would exceed the retained evidence.

Historical September 24 records report 77 unit tests passed and one skipped, one real-Lean triviality probe passed, and passing audits of three earlier runs. These are preserved historical results, not tests of this documentation change. All new or affected execution scenarios belong in the single [pending-test ledger](../../schema%20v0.1/PENDING_TESTS.md); this guide creates no competing checklist. Any subsequent execution must follow the repository's explicit authorization policy.
