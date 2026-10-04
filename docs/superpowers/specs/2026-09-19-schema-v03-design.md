# AgtXIv schema v0.3 — Design

**2026-09-20 implementation revision:** The original baseline below describes the
project at design time. Schema v0.3 and its host now exist. The user's subsequent
instruction selects explicit Luna/Terra routes for repeated source work and reserves
the expensive proof model for Lean/Lamport construction. §4.3 records that revision;
§4.9 records the 2026-09-24 contract revision (root audits, review records, reachable
certificates, claim references, compact graphs, label queries); current execution
evidence and remaining boundaries are in `schema v0.3/STATUS.md`.

**Date:** 2026-09-19
**Status:** Design, approved in conversation. No `schema v0.3/` directory exists yet and no code
has been written. This document is the thing to review before either is created.
**Builds on:** `schema v0.2/` (research/0.2.0), which is specification-complete and whose
`host_probe/` executes but has never called a model.
**Related:** `2026-09-17-schema-v0.2-talk-delivery-design.md`,
`2026-09-16-framework-gap-analysis-record.md`, `docs/IDEAS-BACKLOG.md` items 1–5.

Every number in this document was obtained by running something or by reading a file, and says
which. Where an estimate remains an estimate, it is labelled ESTIMATED. Three findings in
section 2 were re-verified by hand after the agents reported them, and one agent overstatement
is corrected there.

A naming note, because it was checked and is not a conflict:
`docs/archive/specifications/AgtXIv-v0.3-2026-08-17.md` sits on the **AgtXIv protocol ladder**
(superseded by `AgtXIv.md` = AgtXIv v0.4). `schema v0.0 / v0.1 / v0.2` is a **separate contract
ladder**. `schema v0.3/` is the next rung of the second ladder and collides with nothing. The
directory README must say in its first line which ladder it is on.

---

## 1. What v0.3 is for

The brief, in the owner's words:

> Input one arXiv paper, extract all its math claims, and obtain each math claim's internal and
> external dependencies. Apply the same treatment to the externally-depended papers, recursively,
> until reaching the earliest literature / origin. To avoid infinite extension, afterwards focus
> only on the branch subgraph that ultimately yields the query's arXiv math claims.
> Auto-formalize the earliest starting points of that branch graph in Lean 4 against the mathlib
> and physlib packages, then complete the formalization step by step along the chain, and finally
> verify up to the query's arXiv math claims.

Plus a second instruction, which governs the whole design as much as the first:

> Make the project more systematic framework code rather than mostly prompt engineering —
> programmatise every part that can be programmatised. v0.3 must itself distinguish cost:
> autoformalization needs the larger, more expensive models; the rest can use lightweight models,
> potentially down to a System One model.

The shape is therefore: **forward crawl → backward prune → bottom-up formalization**, executed by
programs wherever a program can do the work, and priced by decision type rather than by stage.

The economics of that shape are sound and this is the first thing worth stating, because it is
what makes the ordering non-arbitrary: the forward crawl is the cheap tier and the formalization
is the expensive tier, so **the prune falls exactly before the expensive step**. Pruning after
the crawl wastes crawl money (ESTIMATED $8.59–$258 depending on strategy) in order to save
formalization money (MEASURED $9.85 per claim, so $147.60 for the 29-node closure at the
unvalidated 4-attempt constant). That is the right way round.

---

## 2. Three defects found in the repository's own kernel-checked artifacts

These are reported first because they are the evidence for most of section 7, and because they
are true of the repository today regardless of whether v0.3 is ever built. All three were
re-verified by reading the files directly after the audit agents reported them.

### 2.1 `IsPerfect` does not enforce the finiteness its own docstring claims

`formal/AgtXIvVarela/AgtXIvVarela/ExternalPerfectGraphFoundation.lean:49`

```lean
/-- A finite graph is perfect when every induced subgraph has matching
chromatic and clique numbers. -/
def IsPerfect {V : Type*} (G : SimpleGraph V) : Prop :=
  ∀ S : Set V, (G.induce S).chromaticNumber = (G.induce S).cliqueNum
```

The docstring says *a finite graph*. The signature carries no `[Fintype V]`. Every other
definition in the same file does carry it — `IsFractionalCliqueCover`,
`fractionalCliqueCoverValue`, `WeightedPerfectDualityCertificate` are all
`[Fintype V] [DecidableEq V]`. `IsPerfect` is the only one that is not.

mathlib's `cliqueNum` is an `sSup` that takes a junk value on an unbounded set, and
`chromaticNumber : ℕ∞` sits on the other side of the equation. For a `V` carrying an infinite
induced subgraph, the definition therefore demands a chromatic number the graph does not have.

**Correction to the audit.** The agent reported this as the currently promoted meaning of the
paper's definition and implied active breakage. Both use sites in that file —
`WeightedPerfectGraphFoundation` and `weighted_duality_of_foundation` — supply `[Fintype V]` in
their own binders, so nothing downstream is presently wrong. This is a **latent** defect, not an
active one. What is true without qualification is that the declaration compiles, audits clean,
is marked `KERNEL_CHECKED` in `schema v0.2/host_probe/evidence/closure.json`, and means less than
its docstring says.

The general lesson is the one that matters for v0.3: **a `def` carries no proof obligation, so
`#print axioms` on it certifies nothing.** Two of the three `KERNEL_CHECKED` nodes in the 29-node
closure are definitions. Theorem-grade coverage of that closure is therefore 1/29 = 3.4%
(MEASURED), not the 10.3% the node count suggests.

### 2.2 `max_abs_signed_sum` is a different proposition from the paper's sentence

`formal/AgtXIvStabilizerness/AgtXIvStabilizerness/LocalDelta.lean:86`

```lean
theorem max_abs_signed_sum
    {ι : Type*} [Fintype ι] (y : ι → ℝ) (μ : ℝ) :
    IsGreatest
      {z : ℝ | ∃ f : ι → ℝ,
        (∀ i, IsSign (f i)) ∧ z = |(∑ i, f i * y i) + μ|}
      ((∑ i, |y i|) + |μ|)
```

This maximizes over **every** `f` with `IsSign (f i)` — the full ±1 hypercube over an abstract
`Fintype ι`. There is no graph, no Pauli operator and no commutation relation in the statement.

The paper maximizes over `f ∈ Sign(S)`, the **admissible** sign set of a commuting context, cut
out by parity checks. The two ranges coincide exactly under the paper's own Lemma
`lem:collapse` — `𝓜` has no active dependencies iff `B_S = Sign(S)` for every commuting context
— which appears in the graph as `statement:2607.26154v1:sign-set-collapse`, state CANDIDATE,
unformalized.

So the Lean theorem is true, kernel-checked and audit-clean, and it is not the paper's statement.
The bridge between them is the paper's own lemma, and that lemma has not been proved.

This gap is **not machine-detectable**. LeanBlueprint-style `checkdecls` tooling verifies that a
declaration name exists, nothing more.

### 2.3 The three kernel-checked nodes do not compose

`max_abs_signed_sum` mentions no graph quantity. `maxWeightIndependent` mentions no sign or Pauli
quantity. The only thing linking them is an `import` line in `LocalDelta.lean`. `lake build`
succeeding on a package containing N declarations asserts nothing about any relation among them.

### 2.4 Why these three matter together

`#print axioms` on a **conditional** theorem whose hypothesis nobody inhabits reports
`propext, Classical.choice, Quot.sound` — byte-identical to what it reports on an unconditional
theorem. Nothing in `formal/` inhabits `VRepRepairObligations`; nothing supplies
`WeightedPerfectGraphFoundation`. All three `verification-result.json` files nonetheless read
`axiom_audit: PASSED`.

> The repository's entire automated honesty gate — `lake build`, `#print axioms`, and the
> `sorry`/`admit`/`native_decide` scan — is structurally blind to the one distinction this whole
> loop depends on.

That is what v0.3 exists to fix, and section 7 names the four gaps precisely.

---

## 3. Posture

Decided by the owner: **fully automatic, candidates only, never closes the case.** The pipeline
runs unattended; no node may reach a terminal success state on its own; a successful
formalization records an attestation, never "proved". Human judgement enters at exactly one
action: promoting some subgraph to accepted.

Two mechanical consequences, both binding on every phase below.

**INVARIANT-0 — who may write state.** No model output may set a node's state, disposition,
coverage figure or blocked flag. Models emit candidates and typed classifications; the host
derives state from them by a published total function and refuses on mismatch.

This is not hypothetical hygiene. `closure.json` carries hand-typed `state`, `declaration` and
`blocker` fields, and grep over the repository shows **no program reads, writes or validates
them** — the only references anywhere are `slides/2026-09-22-talk.html`, the slide plan, and
`schema v0.2/host_probe/README.md`. Renaming a Lean declaration would leave every check in the
repository passing while the page kept rendering the node green.

**No terminal `VERIFIED`.** The token must not appear in any state enum, projection, page or
ledger field. The loop's terminal artifact is a chain certificate, and the only headline sentence
it may emit is:

> `<query claim>` holds **CONDITIONAL ON** {P₁ … Pₖ}

Nothing weaker and nothing stronger. Once the word cannot be written, no aggregator, dashboard or
slide can produce it by summing something.

---

## 4. Three engine tiers

The split is by **decision type**, not by stage. It is a factoring of something already in the
v0.2 contract rather than a new idea: `READ-INTERFACE.md` §3 rule 2 already says *"Closed choices
are closed. Enumerate the admissible values rather than accepting free text,"* and the write side
already does this throughout. What is missing today is that these closed choices are made inside
a generative call and carry no confidence.

| Tier | Work | Engine |
|---|---|---|
| **HOST** | hashing, byte offsets, macro tables, coverage arithmetic, bibliography parsing, SCC and topological order, Neo4j projection, Lean builds, retry bookkeeping | none — deterministic program, `ProgramReceipt` |
| **DECISION** | closed-choice classification with confidence | lightweight model constrained to the enum; see §12 for the System One branch |
| **LIGHT** | generative extraction and comparison — `paper.extract`, `dependency.search` | lightweight generative model |
| **HEAVY** | generative proof construction — `autoformalization.lamport`, `autoformalization.lean` | large model, high effort |

The DECISION points already enumerated by the v0.2 contract: `relation_to_source`, `modality`,
`attribution`, `origin`, `exactness`, dependency `relation`. Added by v0.3: is this span a claim
site, is retrieved upstream material relevant, does a Lean build need another attempt, is a fuzzy
bibliography match the same paper, is this support edge AND or OR, what is a terminal's kind.

### 4.1 Confidence must carry its provenance

Because a lightweight model's self-reported confidence is not a calibrated one, and recording
them in the same field would launder an anecdote into a measurement:

```
confidence: {
  value:           0.87,
  source:          SELF_REPORTED | CALIBRATED,
  calibration_ref: null | <calibration curve blob hash + epoch>
}
```

**Gate rule: only `CALIBRATED` permits a gate to auto-advance a node to the next queue.
`SELF_REPORTED` always routes to the human queue.**

This makes adopting a calibrated engine a measurable upgrade rather than a taste: the day a
curve exists, throughput changes by a number that can be shown. It is also isomorphic to
IDEAS-BACKLOG item 3 — the calibration curve is an attestation and the epoch is its calibration.
Write the consequence into the specification in plain words: **a threshold without a calibration
curve is an anecdote.**

### 4.2 Effort tiering is currently an unvalidated literal

`schema v0.2/host_probe/cost.py` already encodes an effort tier per operation — `"low / medium"`,
`"medium"`, `"high"`, `"xhigh / max"` — as strings in a Python dict that no run has validated.
v0.3 promotes the engine class to a pinned `Task` field, records the **actual** engine in the
receipt, and runs downgrade experiments: the same pinned Task re-run one tier lower, comparing
agreement rate and cost. Only then is "which parts need a big model" a table lookup rather than a
preference.

### 4.3 Frozen operation routing and incremental continuation (2026-09-20)

Choose the model before dispatch from a host-owned operation table. Do not spend
another model call deciding which model to use. `profiles/engines.json` supplies
the defaults below; new plans embed the complete table and its digest. Dispatch
uses that frozen table, never the account's ambient model or a source instruction.

| Work | Current operation / executor | Default |
|---|---|---|
| Source acquisition, citation/ref lookup, byte spans, exact deduplication, graph pruning, quotas | HOST | No model |
| Repeated whole-source claim extraction and normalization, with bounded output scopes | `paper.extract` / LIGHT | `gpt-5.6-luna`, medium |
| Compare cited statements, implicit support, hypotheses and joint premises across sources | `dependency.match` / DECISION | `gpt-5.6-terra`, medium |
| Classify an already retained formalization failure | `autoformalization.failure_classify` / DECISION | `gpt-5.6-luna`, low |
| Lean statement/proof terms and structured Lamport proof reasoning | `autoformalization.lean`, `.lamport`, `.premise` / HEAVY | `gpt-6-astra`, high |

`autoformalization.premise` constructs Lean proof material; it is not a license to
use HEAVY for citation classification. The present worker returns Lamport steps
within its Lean candidate response; a separate Lamport operation is reserved in
the routing contract, not claimed as another implemented execution stage.

Graph construction has two evidence layers: citation/ref locates candidate sources;
semantic comparison determines the proposed support relationship and conditions.
A citation, semantic similarity, absent citation, or model confidence cannot establish
proof, independence, completeness or earliest origin. Missing implicit steps remain
unresolved dependencies. Joint premises form AND groups; alternative routes require
explicit grouping. Exact byte binding verifies location, not the mathematical meaning.

`Task` and `ModelReceipt` retain requested model, effort, operation, reason, policy
version and digest. Auditors compare both artifacts against the frozen plan. Requested
model identity is distinct from provider-attested identity; unavailable costs remain
null. These defaults are a resource policy, not measured quality calibration or a
claim of savings. Quality failures remain explicit; no automatic escalation to HEAVY
is permitted outside proof operations. A changed route requires a new frozen plan.
Research defaults to Luna (`--extraction-profile LIGHT`); a new plan may explicitly
select `LIGHT_TERRA` for difficult or previously failed extraction scopes. Resume
cannot change the frozen profile. Successful scopes retain their original evidence.

Successful evidence is reused with its original model identity. New continuation
plans may import a prior output dispatch through `evidence_imports.extraction_batches`:
same source bytes and scope plan, immutable successful result/receipt/response chains,
only missing or failed scopes eligible for new model calls. Historical calls do not
consume the new plan's call quota. Never change the old query binding or rerun completed
claims to measure cheaper models. The downgrade experiments in §4.2 are deferred and
require separately authorized scope; they are not prerequisites for continuation.

Explicit quota/authentication/rate-limit failures open a persistent circuit for the
plan. Preserve the failed call and undispatched ranges, stop new model dispatch, and
continue retaining already successful batches. Do not automatically create another
plan, change account or switch model to work around a provider limit.

This revision first received static review, then the authorized target-paper goal
continued with 22 Luna calls for missing scopes: 20 new successes, 2 retained source
location failures and 17 reused successes. The controller retained a 227-candidate,
35,099,488-byte graph and completed finalization, still `CHAIN_INCOMPLETE`. This is
not an independent test, quality calibration or a claim of all math claims. Current
execution results and pending scenarios are recorded in `schema v0.3/STATUS.md` and
the single `schema v0.1/PENDING_TESTS.md` ledger.

---

### 4.4 Incremental evidence and failure boundaries (2026-09-22)

The following implementation contracts extend §4.3 without changing the full-chain
objective or treating candidate evidence as mathematical acceptance:

- Declaration bindings may carry `premise_comparison` rows. Record explicit Lean
  binders and restrictions inside structure fields, with source roles
  `THEOREM_STATEMENT`, `PROOF_USED`, `GLOBAL_CONVENTION` or `NOT_LOCATED`.
  Located roles require source spans; a missing premise must not receive an
  invented location. Record candidate equivalence, strengthening, weakening or
  unresolved status separately from textual provenance. Finding a premise in a
  proof does not silently rewrite the theorem statement or establish semantic
  equivalence. Legacy bindings without this optional field remain unrecorded,
  not automatically aligned. This schema records evidence; semantic acceptance
  and composition enforcement remain separate gates.
- `evidence_imports.dependency_gaps` may retain attributed PDF gap reviews after
  source availability binding. Each active request must match the frozen source
  binding, originating paper, downstream claim ID and exact candidate statement.
  Missing obligations are exposed individually in `assembly.dependency_gaps`
  and the issue ledger. These records block unresolved requests; they neither
  create proof-support edges nor certify that a proposed bridge is sufficient.
  Citation availability alone must never authorize bottom-up proof composition.
- `evidence_imports.extraction_scopes` freezes explicit output-range manifests for
  a versioned paper. Source identity, bytes, UTF-8 boundaries, range limits and
  ordering are bound before dispatch. Complete frozen source text remains context;
  only selected ranges produce new output. A selected-range result is not a
  whole-paper replacement. Earlier text and successful ranges are reused explicitly.
- A match batch with only quotation-local errors may retain unaffected rows in a
  separate `PartialMatchSelection`. The original failed receipt stays failed;
  selected/excluded row indices and original response hash are preserved. Unknown
  identities, duplicate requests, incomplete request scope, schema failures and
  source-only violations reject the complete response. Historical recovery uses
  explicit imports rather than changing old receipts.
- Source-reading or structural amendments are distinct evidence artifacts carrying
  the original response/result references, before/after fields and rationale.
  They must not masquerade as original successful model output. Normal graph
  binding requirements still apply to amended candidates.
- New research checkpoints record per-request outcomes separately from attempted
  pairs. Dispatch failure, missing model response, unpublished join, rejected join
  and recorded unreviewed judgement are distinct. No such outcome resolves a
  mathematical dependency. Old attempts without outcomes remain unknown; failed
  calls are not automatically retried within the same plan.
- New join plans may use explicit claim IDs to disambiguate shared source
  occurrences. Multiple required claims need `JOINT_SUPPORT`; source quotations
  must bind the selected claims. Old plans retain their frozen join policy.
- Provider input ceilings apply to the complete prompt before reservation.
  Repeated location metadata may be compacted while preserving every original
  source byte, claim, hypothesis, file path and byte endpoint. File hashes remain
  in full-source entries. No silent source truncation or uncalibrated tier savings
  claim is permitted.

Actual case results, including partial failures, remain in the dated execution
reports. Pending independent tests and audits remain in the single pending-tests
ledger. Successful extraction, joining or artifact assembly alone cannot establish
all-claim completeness, earliest-source closure, semantic alignment or Lean proof.

### 4.5 Corrections are source dependencies, not proof-support edges (2026-09-22)

The capacity-origin investigation found an explicit publisher correction to
Newman (1932), DOI `10.1112/jlms/s1-7.2.93`, with correction DOI
`10.1112/jlms/s1-7.4.272-s`. The correction concerns Theorem 2; its impact on the
particular cardinality bound remains unreviewed. This is a concrete counterexample
to treating an old citation with a readable source as a closed origin.

The following defines the required extension. Discovery-only blocking is now wired
into candidate publication and replay reconstruction, but remains unexecuted.
Impact adjudication, automatic discovery and promotion enforcement remain unimplemented:

1. Preserve each original version and each correction as separate source artifacts.
   Record a directed `CORRECTS` relation from correction to original, backed by
   publisher evidence. `CORRECTS` must never count as a mathematical support edge.
   Discovery from a landing page is sufficient to open a review obligation, but
   insufficient to claim that the original theorem or correction has been extracted.
2. Bind an impact review to original source digest, correction source digest, exact
   claim/clause IDs, reviewer provenance and evidence locations. Until both source
   texts are acquired and the affected scope is reviewed, record `UNREVIEWED`.
   A later candidate review can report `AFFECTED`, `UNAFFECTED` or `UNRESOLVED`;
   these classifications alone never grant source alignment or promotion.
3. Retain both old and corrected statements when a clause changes. A successful Lean
   proof of the old statement is still evidence about that exact statement, not
   evidence for the corrected one. Require an explicit new binding or bridge; never
   overwrite historical extraction, compilation or acceptance receipts.
4. Query pruning must retain correction obligations attached to every retained source
   clause, even when correction documents are not mathematical ancestors in the
   proof-support graph. An unresolved correction blocks that clause's source closure
   and every query whose chosen proof branch uses it. Unrelated clauses are not
   automatically refuted or invalidated; their unaffected status needs scoped evidence.
5. Discovering a correction invalidates the affected *current projection* and schedules
   incremental review; it does not erase historical evidence or rerun whole papers.
   Reuse unchanged extraction scopes and Lean declarations by frozen source/environment
   identity. Run Luna for missing source normalization, Terra for clause impact
   candidates, and the proof tier only for necessary Lamport/Lean changes, under §4.3.
6. Oldest retrieved publication is only the current frontier. `earliest_origin` cannot
   close while referenced predecessors, version correspondence or correction impact
   remain unresolved. Budget/depth/access stops must retain explicit frontier items.

Current implementation boundary: `profiles/query-capacity-origin-discovery.json`
retains the Newman discovery and its unresolved impact. The research controller now accepts frozen `source_corrections` imports and attaches
unreviewed obligations to exact paper-ID/statement/conditions/source-span matches
before query pruning. `SourceCorrectionNotice` and `SourceCorrectionTarget` in
`research.schema.json` describe this discovery-only import shape. DOI/preprint
identity bridges must be reviewed separately; aliases are not silently substituted;
the replay auditor reconstructs the same decoration. No notice has been executed
against the real case, and no impact acceptance or promotion integration exists.
Their integration and negative scenarios are pending as V03-173 in the central ledger.

---

### 4.6 Reuse model output after local postprocessing failure (2026-09-22)

A successful provider process can leave a usable response even when local host
processing fails. Preserve the original failure receipt and recover from the
retained response before considering another model call. A recovery is a separate
artifact, with zero new model calls, not a retroactive success in the original ledger.

The first PDF implementation permits only the retained missing-`jsonschema`
failure after process exit 0. It binds the original run, plan, frozen model routing,
task, prompt, schema, response, event log and ordered page-image snapshots. It
checks the retained page-count receipt without rerunning PDF tools. Both the
document-to-image correspondence and visual reading remain attributed evidence;
byte consistency does not independently establish either fact.

`PDFModelExtractionRecoveryRun` retains its own candidate report, assembly, graph
and host source snapshots. Proof-source lookup and the PDF integrity auditor must
reconstruct these outputs from the original response, preserving unresolved
dependencies and unreviewed support groups. They must not admit it merely by
changing its kind to the older `PDFRegionCandidateRun`. Reconstruction uses shared
adapters and is not an independent semantic review.

Normal `PDFModelExtractionRun` success has a separate binding path using the same
source reconstruction. It requires a `CANDIDATE_RECORDED` receipt with no errors,
identical raw and retained result candidates, an identical derived report and
graph, and runtime snapshots bound to the original plan. A failed run cannot enter
this path through a summary status edit. The proof node must retain the bound
statement, conditions, source spans and unresolved dependencies. Both types remain
candidate evidence; their shared integrity audit does not audit the full SQLite
execution history, independently review source meaning or run Lean.

This implementation is unexecuted pending authorization for validation. Recovery
does not assert all-claim coverage, earliest origin, source alignment, support
sufficiency or any Lean result. Historical outputs and successfully completed
model scopes are not rerun for this change.

### 4.7 PDF candidate support uses region evidence (2026-09-22)

Cross-paper PDF support cannot reuse the TeX exact-quotation contract by inventing
text offsets. `PDFSupportMatchProposal` binds an existing downstream request snapshot
to explicit upstream claim IDs and their already retained page regions. It records
the proposed semantic reason, extra conditions, proof issues, joint premises and
alternative-route semantics. The host reconstructs the PDF source assembly before
joining; contradiction contexts and external-request nodes are not upstream claims.

The join preserves the original query set, retains all unresolved boundaries and
prunes the resulting ancestor graph. Source identity and support alignment remain
unreviewed even when every region binds. PDF bibliography strings without identifiers
remain unresolved requests; no DOI or arXiv identity is synthesized from them.

`pdf_match.match_pdf_candidates` supplies both retained full sources to the frozen
`dependency.match` / DECISION route (Terra by default). Downstream input may be TeX
or PDF. Combined images carry explicit offsets and must fit the shared call limits;
overflow is rejected before model reservation, never silently truncated. The model
selects existing claim IDs; the host fills immutable request snapshots and regions.
Each requested boundary receives one judgement, with explicitly joint or alternative
support routes. MISMATCH and UNCERTAIN have no support routes and do not close the
boundary. All original outcomes and the call receipt must be persisted, including
negative judgements, rather than saving only the positive proposal projection.

`pdf_match_run.run_pdf_match` retains the complete model result and per-request
outcomes before joining a support proposal. It receives the controller's existing
ledger, stores plan/runtime/schema snapshots in a fresh attempt directory, retains
failures and interruptions, and refuses oversized graph publication. A join failure
does not erase the completed model judgement. Non-support judgements remain visible
without manufacturing a successful graph; the caller must admit both papers against
its paper budget before dispatch.

The recursive controller accepts `evidence_imports.pdf_sources`, a list of retained
`RetainedPDFSourceBinding` references. Each binds exact existing request snapshots
to one candidate paper identity and PDF run. This is explicit source reuse, not
automatic source discovery or accepted bibliographic identity. Only requests in the
current query ancestor graph are eligible. An already extracted PDF consumes a
paper slot in the same transactional frontier as the query and arXiv sources;
additional requests for the same frozen PDF do not consume another slot. Strict
calibrated policy does not silently admit these unreviewed bindings.

The controller dispatches the matcher using the existing ledger, records normal
failures as attempted, retains interruption recovery boundaries, and distinguishes
a locally recorded candidate join from a graph actually published by the controller.
Later TeX joins preserve retained PDF support provenance. PDF→TeX matching remains
explicitly unsupported; opaque PDF identifiers must never be sent to the arXiv reader.

`audit_pdf_match` reconstructs one normally completed attempt using the shared
`prepare_pdf_match`: complete prompt, ordered images, frozen routing, raw response,
all judgements, proposal, join and per-request outcomes. It does not dispatch a
model or execute retained Python. Its PASS is scoped to this local integrity
reconstruction; it does not establish semantics, the entire SQLite history, paper
admission or controller publication. Failed and interrupted attempts are outside
this normal-completion audit and are explicitly refused.

`audit_pdf_research` integrates normally completed attempts with the recursive
auditor. It binds imported request/source snapshots to transactional admissions,
checks admission precedes the ledger's call reservation, requires each receipt to
belong uniquely to the same plan, and reconstructs the matching BUSY→READY checkpoint
transition. Published graphs join the same reachability reconstruction as TeX joins.
Attempt directories, calls, outcomes and attempted-request history cannot be omitted
or duplicated. A locally completed join and an actually published graph remain
distinct. Failed/interrupted attempt reconstruction is still unsupported and must
fail explicitly; a PASS may not be obtained by excluding those attempts.

These paths remain unexecuted and have produced no new audit evidence. Automatic
source discovery and long-document input still require implementation. The join adapter's zero new model
calls describe reuse only, not a free Terra matching call, free original extraction
or accepted mathematical dependencies.

### 4.8 Source-reading amendments and contradiction contexts

A correction or split of an extracted row must not mutate its original model
response or inherit that response's receipt as authorship of the correction.
`pdf_amendments.prepare_amendment` is an unexecuted local preparation API. Its
proposal binds the original candidate artifact and records each replaced row,
reason and nonempty set of replacement rows. Replacement IDs are fresh; incoming
references require explicit migration, with no suffix aliases or automatic
one-to-many rewiring. Unchanged rows retain their original content.

`proof_contexts` associates revised asserted conclusions with local assumptions
and local proof steps as reading provenance. These associations are not support
groups and do not attest assumption discharge. An asserted node may not depend
on a contradiction assumption through permanent internal support, including
indirect paths through local steps. Changed rows retain a source-review blocker;
associated conclusions also retain an unverified-discharge obligation. Field
restrictions added during modernization must be identified as added conditions,
not silently attributed to the source.

Preparation is not a new accepted extraction run. `pdf_amendment_run` now provides
unexecuted persistence and reconstruction APIs for one normally completed revision
of a successful model extraction or recovery run. It binds the original report to
the reconstructed source assembly, writes into a fresh independent directory, and
retains the proposal reference, revised report, preparation provenance, assembly
and runtime snapshots. Reconstruction repeats source binding and amendment
preparation, compares every output and refuses current-code drift rather than
executing retained Python. Failures and interruptions cannot use the completed-run
audit. Local integrity reconstruction does not establish source semantics or
assumption discharge.

`amendment_proof_context` provides a separate, unexecuted reading-review context
after reconstructing the amendment run. It binds the requested node, retains all
source pages, includes replaced original rows and the revision proposal, and maps
recorded conclusion/local-context associations to their actual candidate nodes.
These associations remain outside support groups. The PDF audit entry point now
recognizes this separate run type and delegates to its local reconstruction;
neither path has produced execution evidence.

Recursive source admission, publication, chained amendments and their audits
remain unsupported. In particular, `pdf_source_binding` still refuses amendment
runs; access to review context must not silently enable matching or admission.
The prepared candidate cannot be passed off as a
successful original or recovery run. No revised Hurwitz candidate graph has yet
been generated or published, and these APIs have not been executed.

### 4.9 2026-09-24 revision

Six contract changes; each is a host mechanism, not a mathematical result.

- **Root audit producer.** `library.py` indexes a frozen Lean environment and writes
  `LIBRARY_SEARCHED` root audits (`$defs.RootAudit`, `binding_accepted: false`), which
  remove the `ROOT_LIBRARY_AUDIT_REQUIRED` gate for unbound non-placeholder roots in
  exploration (§5 Phase 7; other hard blockers still apply). The search is lexical;
  it establishes neither a binding nor alignment.
- **HumanReview.** `$defs.HumanReview` records (template from `review.py`) are the only
  human input the host trusts; each binds the digest of the exact content reviewed.
  None exist yet; an ACCEPT lifts walk blockers but does not produce
  `SOURCE_FROZEN_HUMAN_SIGNED` groups.
- **Reachable ChainCertificate.** Every proof walk writes one; `CHAIN_CERTIFICATE_EMITTED`
  is a kernel-checked implication conditional on its listed Lean premises (§7), not the
  paper's truth. Strict-mode `human_accepted` inside `proof_walk` is still unreachable.
- **CLAIM_REFERENCE_V1.** Claim-index support, a separate mentions table, and
  shared-occurrence expansion that never closes a cycle. Not yet exercised by a real
  extraction; expansion is an over-approximation, not a finding of proof use.
- **COMPACT_V1.** Lossless graph layout without repeated query lists; legacy output is
  unchanged. It changes size, not selection.
- **SOURCE_LABELS.** `--query-label` binds a query to the claims at named source labels.
  It narrows the query; it does not check that the extraction found every claim there.

Evidence: `schema v0.3/runs/v03-revision-evidence-20260924/`.

## 5. The central loop

Twelve phases. Each names its tier, its inputs, its outputs and its typed failures.

```
 0 FREEZE         HOST          pin query byte span + environment fingerprint + budget; open plan
 1 EXTRACT        LIGHT+DECISION whole-paper claims; the three extractor counts recorded side by side
 2 INTERNAL DEP   HOST+L+D      deterministic \ref/\cite pass first; prose refs second; support groups
 3 EXTERNAL CITE  HOST+DECISION .bbl → arXiv/DOI, mandatory Crossref/ADS fallback; TERMINAL_KIND
 4 ADMIT          DECISION      load-bearing test; no depth parameter
 5 RECURSE                      re-run 1–4 per admitted paper
 6 PRUNE          HOST          SCC → ancestors → AND/OR minimum-cost route → topological order
 7 ROOT AUDIT     HOST+DECISION bind each root to a library declaration — BEFORE funding any proof
 8 PREMISE        HEAVY+DEC     render unsupported roots as Lean Props; junk-value lint
 9 FORMALIZE      HEAVY+DEC     walk the order; classify each build failure into a closed enum
10 COMPOSE        HOST          composition witnesses from the elaborator, never from prose
11 CERTIFY        HOST          chain certificate; premise list read out of the Lean environment
```

### Phase 1 — Claim extraction

Two deterministic extractors already exist and have run on real papers:
`tools/extract_provisional_claims.py` (789 lines, 5 papers, 1,648 occurrences, 81 tests, a
byte-determinism test and source-hash-before-write guards — MEASURED) and
`src/agtxiv_web/intake.mjs` (6 papers, `\newtheorem` discovery, byte anchors, content-addressed
ids, `\label`/`\ref` resolution with `RESOLVED_CANDIDATE`/`AMBIGUOUS_LABEL`/`UNRESOLVED_LABEL`,
`STRUCTURE_LIMIT` rather than silent truncation — MEASURED).

They share **zero identifiers** with the 43 hand-written MathClaimIR records that everything
downstream consumes, and the 1,645 → 43 compression has no recorded promotion path. Building
that bridge is the substance of Phase 1, not writing a third extractor.

On arXiv:2607.26154v1 the three counts are 9 theorem-like LaTeX environments, 25 curated
MathClaimIR records, and 180 automatic occurrences — a 7.2× spread (MEASURED). **The spread is an
output, not a defect to reconcile silently.** Do not ship an operation named "produce the whole
paper's claim list"; that phrasing is a completeness claim, and v0.2 spent a paragraph refusing to
let one be asserted.

### Phase 2 — Internal dependencies, and the anchor-recall audit

HOST first: extract every `\ref`, `\eqref` and `\cite` inside each claim's own proof-body byte
span and resolve it to a claim id. LIGHT second, and only for anchors the deterministic pass did
not resolve. DECISION third: partition each target's incoming candidates into **support groups**
— AND inside a group, OR across groups — using a support-only vocabulary. `CITES`, `SIMILAR` and
`UNKNOWN` are not support relations and must not appear on an edge the pruner will traverse; they
go to a separate mention table.

HOST last, and this is the phase's point: **every resolved anchor must have either a support edge
or a typed exclusion.** An anchor with neither is a hard failure, not a silence.

The reason this audit exists, MEASURED on the shipped graph: omitting exactly **2 of the 129
edges** collapses the query closure from 29 nodes with 2 BLOCKED roots to **3 nodes with 0 BLOCKED
roots whose sole root is a Lean-checked declaration**, raising apparent kernel coverage from 10%
to 33%. An under-produced crawl leaves no artifact, no issue and no null record, so it is
byte-indistinguishable from a complete one — **and it is the one that looks cleaner.**

### Phase 3 — External citation resolution

Bibliography identifier coverage is 42/42 at hop 0 but **133/261 missing at hop 1 (51.0%)**, with
one bibliography at 49/50 missing (MEASURED). APS-style `.bbl` suppresses the eprint field
whenever a journal reference is present, so "no eprint field" is never "no arXiv version exists"
and must not be recorded as such. A Crossref/ADS title+journal resolution stage is therefore
mandatory, not optional.

`TERMINAL_KIND` is a closed enum: `ARXIV_SOURCE_AVAILABLE`, `PREARXIV_DOI_NO_SOURCE`,
`MONOGRAPH`, `FOLKLORE_NO_PRIMARY_SOURCE`, `FREE_TEXT_UNRESOLVED`, `IN_LIBRARY`.
`upstream_search` is `ORIGIN` (searched and exhausted) or `FRONTIER` (never searched) — without
it, "reaching the earliest literature" is unverifiable.

**Forbidden termination.** `FOLKLORE_NO_PRIMARY_SOURCE` may not be returned unless the record
names a source that actually states the theorem, checked by a subject-match. The shipped
counterexample: `foundation:finite-lp-strong-duality`, root class
`declared_standard_background`, whose citation anchor is `hamaguchi2024handbook` — a 2024 quantum
handbook standing in for finite LP strong duality, which mathlib c1e30e17 does not contain.
Declaring a node standard is the cheapest possible termination and therefore the one the loop
must make expensive.

### Phase 4 — Frontier admission

Admit a paper only if it is the upstream of at least one support edge lying on a path to the
query under the current edge set, the plan has budget for one crawl unit, and the lead has not
tripped `no_progress_limit`.

**There is no depth parameter. Depth is a consequence, not a control.** Measured, the
load-bearing test takes the target paper's 62 bibliography entries down to **6**.

### Phase 6 — Backward prune, run continuously rather than once

1. Restrict to support-vocabulary edges, by schema rather than by an agent's judgement.
2. Tarjan SCC condensation **before** reachability. Each nontrivial SCC becomes one
   `ROUTE_UNDETERMINED` node.
3. Ancestors of the query in the condensation.
4. Read support groups: AND inside, OR across.
5. Minimum-cost AND/OR solution rooted at the query. Where routes tie within measurement error,
   keep all and report the spread.
6. Roots = nodes with no support group; tag each `ORIGIN` or `FRONTIER`.
7. Emit per node `included_by` (the witness edge path) and `weakest_disposition_on_path`. This
   replaces the single global `graph_view: ORACLE_CANDIDATE` string that today applies identically
   to all 29 shipped nodes and cannot distinguish a node held in by one unreviewed edge from one
   held in by seven.
8. Topological order from the pruned edge set. **Do not use the `layer` field:** 10 of 129 shipped
   edges violate strict layer increase and one runs backwards
   (`claim:witness-capacity` layer 10 → `claim:rotated-closed-form` layer 9) — MEASURED.
9. Diagnostics, which are deliverables and not debug output:
   - **edge criticality** — the node-set delta from deleting each edge singly. MEASURED: one edge
     (`claim:exact-graph-program → claim:closed-form-rom`) decides 25 of 29 nodes; 18 of 45 edges
     change the node set and 27 do not, yet all 45 are required hypotheses.
   - **blocked-descendant count** — MEASURED: 13 of 29 pruned nodes (45%), query included, are
     downstream of a BLOCKED root, while deleting either blocked root loses **zero** nodes.
     Reachability is structurally blind to blocking.
   - **root tags** — MEASURED: the full graph has 18 in-degree-0 nodes but only 12 layer-0 nodes;
     3 of the 9 pruned roots are in-paper definitions that are in-degree-0 only because nothing
     searched above them.
   - **review budget** — 28 edge reviews justify the node set; 45 justify the proof.
10. **BLOCKED gates the ordering, never the selection.** Formalize everything not downstream of a
    blocked root; emit the rest as `CONDITIONAL_ON_BLOCKED_ROOT` carrying the blocker id.
11. Continuous invariant: every non-terminal node in the pruned set must have positive out-degree
    toward the query. An orphan is the footprint of a drifting agent and is reported the round it
    appears, not after a depth-3 crawl has been paid for.

Cycle fragility, MEASURED: the shipped graph is acyclic, but adding the reverse of any single one
of the 129 edges produces SCCs of up to 10 nodes, and 9 of the 129 single-back-edge perturbations
put the query itself inside a nontrivial SCC. Reachability survives cycles; the topological order
does not, and today it would fail silently.

Referential integrity, MEASURED: both shipped blockers' `affects` arrays point at
`contract:2607.26154v1:closed-form-equality`, which is not the id of any node in `closure.json`,
so the blocked query renders with `blocker: null`.

### Phase 7 — Root coverage audit, before any formalization is funded

Per root, return `{library, revision, declaration}` or `NO_LIBRARY_PROVIDES_THIS`.

**PhysLib is struck from the pinned set and must not appear in the specification.** MEASURED:
`leanprover-community/physlib`'s 925 `.lean` files contain **zero** occurrences of *stabilizer*,
*frustration*, *perfect graph*, *independent set*, *linear program*, *robustness* or *magic*; its
QuantumInfo library contains **zero** occurrences of *Pauli*; and **no physlib revision exists at
v4.30.0-rc2 + mathlib c1e30e17** — the nearest tag is 1035 mathlib commits ahead and master is
2811 ahead. Adopting it is an epoch migration of all three `formal/` projects, not an incremental
`require`. The pinned set is mathlib c1e30e17 + LeanQuantum/Quantumlib 44fc4eb1.

mathlib itself is also incomplete for this paper. MEASURED across its 7,944 files: it supplies
`IsIndepSet`, `IsNIndepSet`, `indepNum`, `cliqueNum`, but has **0 perfect-graph declarations, 0
files under `Combinatorics/SimpleGraph` mentioning vertex weights, and 0 LP-duality
declarations** — its own `Convex/Cone/Basic.lean` TODO says LP duality is still to be done.

Consequence: **3 of the 12 layer-0 roots bind to nothing.** "Auto-formalize the earliest starting
points against mathlib and physlib" has no referent for a quarter of this paper's roots, and the
loop must say so in a field rather than discover it inside a $9.85 proof attempt.

### Phase 8 — Premise rendering

Unsupported roots become explicit Lean `Prop` premises using the repository's own working
pattern: `ExternalPerfectGraphFoundation.lean` states Chvátal's weighted duality as
`def WeightedPerfectGraphFoundation : Prop`, and the only theorem in the file applies its own
hypothesis in one line. Its header says in so many words that it does not assert the theorem as a
Lean axiom. Copy this exactly; project axioms remain forbidden.

HOST runs a **junk-value lint**: flag any `sSup`/`sInf` over a set not proven nonempty and
bounded, any ℕ-vs-ℕ∞ comparison across a coercion, and any missing `Fintype` the source statement
requires. §2.1 is this lint's first true positive.

### Phase 9 — Bottom-up formalization

Walk the topological order. Per node the required outputs are a `LamportProof`, a `LeanSource`, a
`DeclarationBinding` array, a `NonvacuityWitness` and a `ProgramReceipt`; a node missing any one
of them cannot be reported as discharged. DECISION triages each build failure into a closed enum
— `SYNTAX | MISSING_LEMMA | STATEMENT_WRONG | TIMEOUT | HEARTBEAT | UNPROVABLE_AS_STATED` — and
that classification, not the model's prose, selects the retry strategy.

A node that exhausts its attempt cap **becomes an explicit Lean `Prop` premise of everything above
it**, and the walk continues past it. This is the only rule that lets an unattended bottom-up walk
complete without either lying or stalling, and it is needed because the bottom-up order inverts
the difficulty: the earliest starting points are exactly the nodes this project already declined
to formalize.

---

## 6. Termination rules

| Rule | Basis (MEASURED unless noted) |
|---|---|
| **Typed-terminal halt** — a branch stops at any upstream whose `TERMINAL_KIND` is not `ARXIV_SOURCE_AVAILABLE`. The other five values are ordinary expected terminals, not failures. | The target paper is **one hop** from non-crawlable objects. Of its 42 unique bibliography keys, 10 (23.8%) are pre-1991 and cannot have an arXiv id and 4 (9.5%) are monographs. Across the whole 74-node DAG only 16 distinct external sources appear; 6 (37.5%) have retrievable arXiv source and 4 (25%) are bare author-year free text. |
| **Library halt** — a node resolving to a declaration in the pinned library set is terminal, recording library + revision + declaration. | Distinguishes a root genuinely discharged from one axiomatized because no library provides it. Without the field they are indistinguishable. |
| **Load-bearing halt** — a citation is admitted only if it is upstream of a support edge on a path to the query. Bibliography membership never admits a paper. | 62 bibliography entries → 6 load-bearing upstream papers. The measured $4,136 and $24,915 depth-2/3 figures price a crawl this loop does not need to perform. |
| **Budget halt** — at budget, the plan flips to HALTED, unexpanded nodes are tagged FRONTIER, the certificate and ledger are emitted. | `limits.max_cost_microusd` is required by `task.schema.json` and enforced nowhere. `store.py`'s run table is `(attempt_id, task_sha256, state, principal, operation, output_sha256, receipt_sha256)` — no cost column, no `plan_id`, no timestamps. Per-plan spend cannot be summed by any SQL query today. |
| **No-progress halt** — after `no_progress_limit` consecutive COMMITTED runs producing zero new items. The counter is keyed on `(plan_id, lead)`, not on the query string, so rewording does not reset it. | The Dependency Agent states this rule in prose with no field, counter or code behind it. |
| **Node attempt halt** — an exhausted node becomes a Prop premise of everything above it. | 3 of 12 layer-0 roots have no library to land on; the repository's own answer to its two hardest roots was a `Prop` premise, not a proof. |
| **SCC halt** — a nontrivial SCC becomes one `ROUTE_UNDETERMINED` node; reachability proceeds, ordering does not start for that component and says so. | See the cycle-fragility measurement in Phase 6. |
| **Terminal state** — `CHAIN_CERTIFICATE_EMITTED` or `CHAIN_INCOMPLETE`. Never `VERIFIED`. | See §3. |

---

## 7. What a completed chain does and does not prove

A completed chain produces one Lean declaration whose statement is the formalized query claim,
whose explicit hypotheses are the enumerated terminal premises P₁…Pₖ, and whose proof term the
kernel accepts.

**That establishes exactly one thing:** the implication P₁ → … → Pₖ → Q(formalized) has a proof
term the kernel accepts in environment E. Not Q. Not the paper's theorem. Not that the premises
hold.

| # | Gap | What is recorded | Program-detectable |
|---|---|---|---|
| 1 | **Premise inhabitation** — a conditional theorem compiles whether or not its hypothesis is inhabited, and `#print axioms` reports the same three constants either way | `nonvacuity_witness`: a Lean term inhabiting the hypothesis at a concrete instance, or literal `NONE`, which downgrades the node to `KERNEL_CHECKED_VACUITY_UNKNOWN` and propagates to every descendant | **Yes** — extend `Audit.lean` to emit each audited declaration's non-instance hypothesis types |
| 2 | **Faithfulness of Q to the paper's sentence** — the kernel certifies the rendering's provability, never its fidelity (§2.2) | `statement_alignment` ∈ {`SOURCE_FROZEN_HUMAN_SIGNED`, `AGENT_NORMALIZED_UNREVIEWED`, `DOMAIN_WIDENED`, `DOMAIN_NARROWED`} plus `bridging_claims`; effective disposition is the **weakest** over the node and its bridging claims | **No.** Propagation is a program; the judgement is not. Route to a human sign-off slot rather than pretend to close it |
| 3 | **Definitional correctness** — a `def` has no proof obligation and junk-value semantics let a wrong definition compile, audit clean, and become the downstream meaning (§2.1) | `statement_discharged` and `proof_discharged` as two fields that may never be summed; a `def` reaches at most `DEFINITION_ELABORATED`; every promoted definition carries `total_on` and at least one kernel-checked non-degeneracy example | **Partly** — the junk-value lint |
| 4 | **Composition** — N declarations elaborating in one build asserts nothing about any relation among them (§2.3) | `composition_witness` per edge whose endpoints both carry declarations, extracted from the elaborator (constant dependencies / `.ilean` reference tables), never from prose. An edge with two green endpoints and no witness is `NOT_COMPOSED` | **Yes** — and no published system runs it; Theo (arXiv:2606.31134) names it "paper chaining" and defers it |

**Six required outputs**, all generated, none hand-maintained, all validated in
`tools/validate_repo.py`'s fast profile:

1. the composed premise list, read out of the Lean environment rather than the JSON graph,
   printed as the first line of the result;
2. each premise's `TERMINAL_KIND` — the **vector of counts by kind**, not a percentage, is the
   honest measure of how much of the paper was verified;
3. theorems proof-discharged and definitions statement-discharged as **two rows that may never be
   added together**;
4. per node, `included_by` and `weakest_disposition_on_path`;
5. coverage under deletion of each critical edge, never a point figure — MEASURED, the shipped
   10% becomes 25% if one edge is never proposed and 33% if two are;
6. an explicit `scope` key as **data** on every count, with counts of different scopes forbidden
   in the same object. Today `coverage.json` puts `kernel_checked: 0` beside
   `root_declarations_kernel_checked: 43` in one block, guarded only by a prose scope note that
   no program reads.

**One sentence.** A compiled chain proves that a formalized implication holds in a pinned
environment. A verified query claim would additionally require that every premise is inhabited,
that the formalization is faithful to the paper's sentence, that the definitions denote what the
paper's words denote, and that the declarations actually compose. The loop can establish the first
mechanically and can only **record** the other three. That is precisely why the pipeline has no
terminal verified state: the three things it cannot establish are the three a reader would assume
it had.

---

## 8. New contract objects

Five schema additions unblock everything else and must be settled **before** the segmenter is
written, because every programmatised stage inherits the receipt shape.

| Object | Why v0.2 cannot express it |
|---|---|
| **ProgramReceipt** | `run.schema.json` forces `call` to be non-null for every state except `NOT_STARTED`, and `NOT_STARTED` is forbidden from carrying output, source bindings or consumed items. A deterministic stage can therefore only record nothing or invent a provider. `HOST.md:81` promises "actual program receipts distinct from research runs"; no such schema exists |
| **Coverage ledger** | Named in three specification documents and present in **zero** of the five schemas (grep-verified). Without it, "whole paper" rests on the model self-reporting gaps |
| **PlanLedger** | `plan_id` is a bare string with no object behind it and appears in the host probe exactly once, in an `e2e.py` fixture literal. All recursion bounds are assigned to "the parent plan" in prose |
| **External identifier** on `DependencyCandidate` | No arXiv-id field, no DOI field. The recursion driver has nothing to dispatch on |
| **DecisionReceipt + confidence provenance** | §4.1 |

Seven more, required by the loop:

| Object | Purpose |
|---|---|
| **SupportGroup** (`support_group_id` + `route_id`) | Makes joint premises representable: AND inside a group, OR across. Every one of the 129 shipped edges has the key set `{from,to,type,reason,evidence}` and nothing else, so the same 45 edge records are consistent with a 29-node AND reading and a 2-node OR reading — **a 14.5× cost swing that no field can currently distinguish, and the single largest cost lever in the loop** |
| **TerminalRecord** (`terminal_kind` + `upstream_search` + `library_binding`) | Gives the crawl a typed halt in place of an arbitrary depth budget |
| **PremiseClosure** (`SEARCH_EXHAUSTED`/`SEARCH_PARTIAL`/`SEARCH_NOT_RUN`) | Makes a **missing** edge representable. See the 2-of-129 measurement in Phase 2 |
| **DeclarationBinding** (array with role) + **NonvacuityWitness** | The projection carries a single scalar `declaration` and drops the rest; shipped consequence, verified: `claim:mwis-definition` is bound to `independentFinsets`, the *family* of independent sets, while the value declaration `maxWeightIndependent` sits six lines below |
| **CompositionWitness** | §7 gap 4 |
| **StatementAlignment** + `bridging_claims` | §7 gap 2 |
| **IssueIndex** | The `Issue` object exists with a closed seven-value enum and the honesty mechanism depends on it, but issues live only inside the output blob. `store.py` has no issue table; `check_output.py` prints a count and discards it; `verify_phase.py` never looks at one. **The ledger can currently certify a store as internally sound while every run in it disclosed that it read nothing** |
| **ChainCertificate** | There is no object whose scope is a chain, so there is nothing to attach a cross-package environment fingerprint to |
| **DerivedState** (closed enum + published derivation function) | `validate_claim_dag.py` checks `kind` and `type` against enums but accepts any string for `status`; **44 distinct status strings exist across 74 nodes, 33 appearing exactly once**. The only mechanical blocked-detector is the substring test `'FALSE' in status or 'BLOCK' in status`, which catches 14 nodes and misses 16 — including `root:perfect-graph-weighted-duality` (`PRIMARY_SOURCE_ALIGNMENT_PENDING`), one of the two roots the reader-facing page renders in red. The enum must at minimum split `BLOCKED` into `SOURCE_UNREACHABLE` and `SOURCE_READ_DEFECTIVE`, because the two shipped blocked roots need opposite remedies |

---

## 9. Cost

Rate card from `cost.py`: $5.00/MTok input, $25.00/MTok output, "Anthropic Claude Opus 5 rate
card, as cached 2026-06-24 — RE-CHECK ON THE DAY". Every figure inherits that caveat.

| Strategy | Depth | Papers | Total | Basis |
|---|---:|---:|---:|---|
| full bibliography | 1 | 63 | $673 / $343 cached | MEASURED |
| full bibliography | 2 | ~390 | $4,136 / $2,109 | MEASURED |
| full bibliography | 3 | ~2,350 | $24,915 / $12,704 | MEASURED |
| **load-bearing** | 0 | 1 | $45–156 | ESTIMATED |
| **load-bearing** | 1 | 7 | $208 | ESTIMATED |
| **load-bearing** | 2 | 21 | $328 | ESTIMATED |
| **load-bearing** | 3 | 30 | $405 | ESTIMATED |

**The honest reading:** every cell of the expensive rows is measured and every cell of the cheap
rows is estimated — and the expensive rows price a crawl this loop does not need to perform. That
asymmetry is itself the argument for running M1 before funding any crawl.

Free parameters the loop must overwrite with receipts: 4 attempts per Lean claim (>half of the
all-claims bill); 2 attempts per Lamport proof (never measured at all); 4 characters per token;
the 0.51 cache factor, back-derived from $343/$673 rather than from a cache-read receipt; the
load-bearing paper counts at hops 2 and 3; the 2-per-claim dependency-search count.

For contrast, MerLean reports a measured **22.4 compile attempts** — 5.6× the literal. And this
repository **structurally cannot validate the constant**: all three `formal/` projects are one
squashed commit dated 2026-08-17 with zero failed attempts stored.

---

## 10. Milestones

```
M0  contracts          five schema additions + engine-class field    pure contract, zero model
M1  measurement        replay against ground truth (§11)             ~$12, ~1 hour, HEAVY
M2  Tier P             merge the two extractors, wire the macro table,
                       locator pre-pass, .bbl parser, coverage arithmetic   zero model calls
M3  DECISION layer     implement the interface with a light model, then the
                       bake-off on the 25 labelled claims → first calibration curve
M4  close the loop     queue+gate walker, 29-node closure, node-by-node Lean,
                       hand-selected chain — no automatic DAG selection yet
M5  index + recursion  Neo4j projection as a pure function of the ledger;
                       recursion driver under the typed-terminal rules
```

M1 is placed before M2 deliberately: it is the cheapest run that converts the most unvalidated
constants into measurements, and it is the project's first real model call.

**Automatic DAG selection is deferred past M4.** A `dependency_candidate` is a single binary pair
and joint support is recordable only in a free-prose `basis` field no checker can read; the
shipped 29-node closure has already flattened joint premises into 45 independent edges, which
silently converts "A and B jointly support C" into "A alone suffices and B alone suffices". Ship
the node-by-node walker against a hand-selected chain first — that violates nothing and proves the
scheduler — and add the route object with explicit joint-premise grouping before any automatic
selection feeds Lean.

Write one constraint into the specification in plain words: **promotion of a candidate edge to a
load-bearing premise is a checked judgement, never a graph property.**

---

## 11. M1 — the first measurement

Run Phase 9 alone, on the three claim-DAG nodes that already have hand-written Lean on disk, with
the attempt cap raised to 30 and `ProgramReceipt` recording on. No crawl, no prune, no new paper.
The reference Lean is withheld from the model and used only as the grader.

| Target | Reference | Kind |
|---|---|---|
| `claim:perfect-graph-definition` | `AgtXIv.GraphFoundation.IsPerfect` | def, 3 lines |
| `claim:mwis-definition` | `AgtXIv.GraphFoundation.maxWeightIndependent` | def, 8 lines |
| `claim:sign-alignment-identity` | `AgtXIv.Stabilizerness.max_abs_signed_sum` | theorem, 11 lines, 3 prerequisite declarations, 13 distinct mathlib lemmas |

Environment: the existing pin, reusing RootMath's 11 GB cache via `packagesDir`. No new build
epoch, zero marginal storage.

**Cost** (ESTIMATED): worst case, all three exhausting 30 attempts, 96 calls ≈ **$20.01**
uncached, ≈ $10.20 at the modelled cache factor. Expected ≈ $12.
**Duration**: ~90 s per `lake build` against a warm cache; three targets in parallel, under 1 hour.

It converts into measurements: `attempts_to_first_compile` and `attempts_to_close` separately for
a def and for a theorem; the definition-vs-theorem bimodality on the exact two populations the
closure mixes; real input/output token counts, retiring the 4-characters-per-token estimate; and
the prefix-cache hit rate, retiring the back-derived 0.51 factor.

---

## 12. The System One branch

`https://typesafe.ai/` proposes System One models: *"a new class of AI model built for decisions
inside software"*, taking structured questions and returning **typed decisions with calibrated
probabilities**, trained by RLCD (Reinforcement Learning for Calibrated Decisions). Its first
public model, Jev, is in early access at $42 per billion input tokens, claiming 238× lower input
price than Claude Fable 5.1 and 193.6×/244.6× faster/cheaper on System One tasks. It states it is
not good at System 2 tasks, specialized domains or anything generative. **These are vendor
claims, unverified here. No open-source component exists.**

The owner's decision: **v0.3 lands first; System One gets a branch off it, contingent on whether
the community supports it.** v0.3 therefore builds the DECISION tier as a cost contract with a
fixed interface, implemented by a constrained lightweight model, and the branch swaps only the
implementation.

The fit is real and worth recording. The DECISION tier's inputs are already closed enums by v0.2's
own rule; confidence-gated routing is exactly the mechanism that makes "fully automatic but only
ever produces candidates" operational at scale; and the vendor's own guidance — run it on your own
data, plot confidence against accuracy, set thresholds from there — is the calibration discipline
of IDEAS-BACKLOG item 4.

Two further notes. High-volume DECISION calls take a structured question rather than the 62,486-byte
protocol prefix that is 83% of all input today, so the seam attacks the prefix problem for exactly
the calls that scale with corpus size. And the branch's success criterion is **not** "it ran" — it
is M3's calibration curve redrawn on the new engine, with both curves shown together.

---

## 13. Open questions

1. **The three defects in §2 — fix now or as part of v0.3?** Adding `[Fintype V]` to `IsPerfect`
   is a one-line change. §2.2 and §2.3 are recording problems that v0.3's `statement_alignment`
   and `composition_witness` are designed to solve; they cannot be fixed by editing Lean.
2. **Does M1 run before or after the specification is written?** Running it first rewrites §9.
3. **Whether the deterministic extractor should be consolidated in Python or JavaScript.** Two
   working implementations exist in two languages, sharing zero identifiers. Consolidating is
   Phase 1's real work and the language choice has not been made.
4. **What the coverage denominator is.** Three defensible answers exist for one paper and they
   differ by 7.2×. The byte-coverage denominator counts figures, whitespace and the bibliography
   as unprocessed unless classified, and a reader will read a high byte-coverage number as a high
   claim-coverage number, which it is not.
5. **Whether v0.3 candidates ever enter the v0.0 formal layer, and by what operation.** The v0.0
   layer mechanically blocks a producer from reviewing its own output, which currently blocks all
   82 correspondence records of the one real whole-paper extraction, and there is no legal
   producer for them because no review operation exists. The recommendation in this design is that
   v0.3 stays entirely in the candidate layer and never emits a formal record.

---

## 14. Provenance

The audit behind this document ran as two workflows over the repository: ten area surveys plus
three adversarial lenses plus a synthesis (14 agents), then six technical probes plus two
adversarial passes plus a specification pass (9 agents). Agents were instructed to run things
rather than quote documents, and to mark every number MEASURED, CITED or ESTIMATED.

Numbers corrected against `schema v0.2/host_probe/README.md`, which is stale relative to the code
that produces it: `$ref`s walked 121 (README says 109); spec prefix 62,486 bytes ≈ 15.6k tokens
(58,155 ≈ 14.5k); spec index 20 entries, 9 rendered / 11 identity-only (16 / 9 / 7); scope-A cost
$9.85 and repeated prefix 83% ($9.5, 82%).

Also found and not yet fixed: `e2e.py` fails schema validation on both its Task and its
`NOT_STARTED` receipt while printing FAIL and exiting 0; 11 of the 13 negative fixtures now
short-circuit at the SHAPE layer for one shared reason, so the cross-object checks they exist to
prove never execute; `READ-INTERFACE.md` claims `host_probe/` holds a query backend that does not
exist; and `HOST.md` §5's 3/3/6 retry table is implemented nowhere.
