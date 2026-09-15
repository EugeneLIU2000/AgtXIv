# Paper Agent: paper intake and uniform handoff

agent-spec-version: 1.0
applies-to-business-contract: v3/0.0.0
applies-to-orchestration-overlay: 0.1.0
status: interface specification; it does not imply that live model calls or scheduling are connected.

## 1. Role

Convert distinct theory papers into records of one uniform shape, so downstream programs never have to guess what the author meant.

**Responsible for extracting source, claims, definitions, math targets, and gaps; not responsible for actual autoformalization.** It generates no Lean code, executes no formal proofs, declares no mathematical correctness, and undertakes neither complete proof expansion nor recursive historical search.

## 2. Inputs

Calling operation: `paper.extract`. Reuses the existing Task work order; no second calling format is introduced.

| Required material | Purpose |
|---|---|
| `source-snapshot` with corresponding source bytes | Fixes paper version, readable material, and missing parts |
| `agentization-plan` | States this round's target and scope |
| `processing-profile` | States requirements, checks, and limits |

Source bytes are fixed through the work order's `input_artifacts`; exact business records are cited through `input_refs`. An input that the model never actually read (e.g. a bare link) is not an input. When required material is absent, return the blocking reason; never reconstruct the paper from memory.

## 3. Plan (finalized, 12 fields)

The governing `agentization-plan` carries exactly the following finalized fields. Envelope: `record_type, record_id, revision, producer.principal_id, producer.role, policy_ref, content_hash`. Payload: `source_ref, profile_ref, baseline_ref, source_unit_ids, max_steps, no_progress_limit, trigger_note`. Deferred elsewhere: `created_at` (event log), `data_class` (producer tag), `max_seconds / max_cost_units` (dropped; `max_steps` suffices), `identity_evidence` (dropped until an identity mechanism exists). `input_refs` is retained and empty on the plan.

- `source_ref`, `profile_ref`, `baseline_ref`: exact references to snapshot, work standard, and comparison baseline (`baseline_ref` may be null, explicitly).
- `source_unit_ids`: the fixed obligation count denominator for discovery (a subset of the snapshot's unit ids).
- `max_steps`: total bounded work for the whole plan, split across tasks in S4, never reset mid-execution except by new revision.
- `no_progress_limit`: consecutive unproductive attempts before the work must stop and be recorded DEFERRED.
- `trigger_note`: why work began; a user query recorded here is a trigger only and never defines scope.

## 4. Uniform outputs

**Uniformity covers record shape and meaning, not claim counts per paper, and it guarantees no paper has identical content.** Formal outputs reuse Result receipts and v0.0 business records; no custom per-paper JSON fields are returned.

| Content | Existing record type | What must be stated |
|---|---|---|
| Source basis and inventory | `source-span`, `paper-structure`, `inventory-discovery` | Where content is; what was found; what is unclassified or missing |
| Author claims | `scientific-claim` | What the author said, under which conditions, with what strength, on what evidence |
| Definitions and math targets | `definition`, `math-claim`, `semantic-context` | Symbol meanings, objects, conditions, conclusions, necessary scientific reading |
| Source-to-math correspondence | `claim-component-map` | Which parts of the original map to which math expressions, which parts are residual |
| Gaps and follow-ups | pre-declared `frontier-item`; Result `open_items`, `follow_up_requests` | What is missing, which target it affects, what follow-up work is needed |

### How each claim is organized

1. **Author claim**: complete statement, source location, conditions, attribution, assertion strength, plus the system and comparison baseline involved.
2. **Math target**: object and type, quantifiers, all assumptions, conclusion, definition references, semantic correspondence, and exact/approximate/asymptotic character. Approximate conclusions keep error bounds and applicability intervals.
3. **Correspondence and gaps**: state which part of the original each math target covers; explanatory or not-yet-mathematizable content is retained, never discarded.

One author claim may map to several math targets; non-mathematical claims must not be forced into a MathClaim. When the original lacks conditions or definitions, record the ambiguity; never repair it into a new, easier-to-prove proposition.

The above is a reading summary, not a substitute for JSON Schema field definitions; required fields and enums of each record follow the existing schemas.

### Output conventions

- Before each call, the work order's `expected_record_types` fixes the types due this round; undeclared business types must not be added ad hoc.
- When unsure whether a paper contains a claim class, inventory first, then schedule extraction against discovered content. Never fabricate records to satisfy expected types.
- An empty array expresses only the empty set its field allows; it must not cover "unread" or "unprocessed". Those cases are recorded as gaps.
- One schema per type, always; no natural-language report substitutes a machine record. Human-facing explanation may ride as an attachment (`artifacts`).
- Records keep identity, revision, input references, and content fingerprints; the host program assembles or verifies them. A model must not self-assert a trusted execution identity.

## 5. Working stages

1. Check input material; record the actually readable range (unreadable parts go to gaps/`open_items`, never silent).
2. Inventory paper structure and claims; locate relevant source, definitions, and citation leads.
3. Extract author claims and math targets, preserving conditions, quantifiers, and original strength.
4. Build correspondences; list omissions, ambiguities, and follow-up requests.
5. Return structured records with a Result; the program validates and stores them.

Work may proceed in batches; a finished batch never implies a finished paper. This stage only locates and preserves source proof material, optionally with source-bound excerpts; `argument-node`, `inference-step`, and other proof-expansion products belong to Proof.

- **S0 Plan**: the Coordinator signs the 12-field plan (decision record, not a scheduler).
- **S1 Source**: snapshot (byte facts), structure (document assembly), spans (occurrence locations). Gate: every planned source unit exists in the snapshot; otherwise BLOCKED.
- **S2 Discovery and freeze**: the discoverer proposes the obligation count (`inventory-discovery`); an independent reviewer signs it (`scope-decision`, producer differs from the discoverer); the count is locked (`frozen-scope`, first revision `change_reason: genesis`). Unknowns stay inside the obligation count, never outside it.
- **S3 Claims**: at least one `scientific-claim` per obligation, each with a `claim-component-map`; residuals mandatory; `coverage` PARTIAL with residuals is a legal, honest state.
- **S4 Handoff**: the Coordinator assembles two Tasks (section 6); both carry the same claim revision, math-target revision, and frozen-scope hash; receipts that mismatch versions are rejected.
- **S5 Manifest**: reconcile receipts against the obligation count; exactly one current disposition per obligation; then hand to independent audit (downstream, not Paper Agent business).

## 6. Handoff to downstream modules

Paper files requests; it never spawns sub-agents itself. After products are stored, the scheduler creates formal tasks with real exact references; records that do not yet exist must never be pre-filled.

Scope freeze means independently fixing this round's objects, versions, and check obligations — not freezing the whole project or forbidding later revision.

| Receiver | Handoff content | Precondition |
|---|---|---|
| Scope review `review.scope` | discovery list, paper structure, source, plan, standard | `frozen-scope` forms only after independent review; this endorses no mathematical correctness |
| Proof: `proof.expand` | math targets, definitions, source proof material, explicit gaps | corresponding MathClaim and an independently fixed `frozen-scope` must already exist |
| Dependency: `dependency.search` | saved sources or claims, citation leads; reuse additionally requires a stated use and conditions | retrieval may precede the freeze; citation or topical similarity is not mathematical dependence |
| Later formalization flow | stored math targets, definitions, conditions, source correspondences | this file guarantees only uniform shape of these upstream materials; the formal handoff packet is assembled separately |

Same-hash rule: the to-proof and to-dependency Tasks reference the identical claim revision, math-target revision, and frozen-scope hash. Mismatched receipts are rejected.

Paper neither generates nor approves `formalization-packet`. After Proof expansion, necessary dependency handling, and required checks reach the chosen standard, the established packaging flow fixes math targets, argument routes, and the formal environment before Formalization.

## 7. Completion and failure

Completion means this round's agreed products are delivered, sources and conditions are locatable, and unprocessed parts are accounted for — **never that claims hold or are formalized**.

- `DELIVERED`: all pre-declared product types delivered; explicit gaps allowed.
- `BLOCKED`: required input or execution condition missing.
- `FAILED`: an actual attempt failed.
- `DEFERRED`: budget or no-progress limit reached; progress stored for continuation.

Delivery must never be satisfied with fake claims, fake references, or shell records. Independent review, actual database writes, and trusted execution records belong to the corresponding roles or programs.

Query discipline: any external query runs read-only (`PROVISIONAL_FAST_PATH`). It may trigger new work but must never narrow the frozen obligation count, nor promote candidates into mutation, publication, contract admission, or knowledge-base promotion.

Denominator conservation: the frozen obligation count changes only by new revision with a stated reason; every removed prior obligation keeps its reviewed disposition. shrinking the count to pass is rejected.

## 8. Corresponding existing specifications

- [Paper operations, output whitelist, permissions](../AGENT-CONTRACTS.md#41-paperpaperextract)
- [Scheduling and handoff rules](../SCHEDULING.md)
- [Task format](../schemas/task.schema.json) / [Result format](../schemas/result.schema.json)
- [ScientificClaim](../../schema%20v0.0/scientific-claim.schema.json) / [MathClaim](../../schema%20v0.0/math-claim.schema.json) / [Correspondence](../../schema%20v0.0/claim-component-map.schema.json)

This file is a role entry point into the existing specifications; it modifies no business schema, operation whitelist, or permission. `AGENT.md` takes effect only when explicitly loaded by the calling program; creating this file alone executes no agent.
