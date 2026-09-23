# Shared Contract: Models Produce Content; the Host Records Execution Facts

Applies to research/0.2.0. All objects are candidates without scientific approval by default. Models must not author producer metadata, execution times, costs, hashes, verified states, or review approvals. Machine shapes are defined in [schemas](schemas/). The cross-object rules in this document do not yet have an execution implementation.

## 1. Task: One bounded research operation, not an entire recursive task tree

The host writes task.json and pins its original bytes before calling the model:

- task_id / plan_id: Identify this task and its shared parent plan. Retries and child tasks do not reset parent budgets.
- operation / purpose: Fix the operation, processing scope, search boundary, or intended target use. purpose does not grant permissions.
- inputs: Each entry has a local id, kind, and actual blob identity. An item input also supplies item_id and the producer_task blob that generated it; these two fields are null for other input kinds. Models use aliases rather than computing content hashes.
- target_ids: Empty for Paper; exactly one entry for each of the other three operations, resolving to an input **math_claim**. A paper, ScientificClaim, proof plan, or multiple claims cannot substitute for it.
- spec / policy / model_profile: Shared specification index, host policy, and provider configuration descriptors pinned by actual bytes. Do not write credentials into these files. The host accepts only registered, supported descriptors; arbitrary JSON is not authorization.
- module: Both Autoformalization operations must pin a module descriptor; Paper and Dependency use null.
- limits: Bounds on input bytes, output bytes, output tokens, duration, attempts, lack of progress, and cost. Apply the smaller of these bounds and the parent plan's remaining allowance. Costs use integer micro-USD; unknown costs must not be recorded as zero.

The spec index must cover the specifications actually read, all five schemas, applicable Agent documents, and implementation identity. Model configuration must cover the model, provider, generation parameters, transport retries, and SDK/dependency versions. Host descriptor registration and checking still require implementation; no default-allow configuration is provided.

Do not prepopulate depends_on with unknown future artifacts. Work without existing inputs is only a waiting proposal. Create a formal Task only after inputs are committed and authorized. Trace dependencies through actual input artifacts and their producing runs. This simplification must not remove ordering history, cancellation, or budget controls from the execution ledger.

Resubmitting the same task_id requires byte-identical content. Changes to sources, targets, purpose, policy, module, or model configuration require a new Task. Infrastructure retries of the same Task use new attempt_ids. A revision that adds an earlier draft or feedback to the inputs also requires a new Task.

## 2. Output: Four fixed fields

A model returns exactly one JSON object: contract_version, operation, items, and issues. No Markdown fences are allowed; reject unknown fields. operation must match the Task.

items contains this call's increments, not the accumulated history. operation determines the allowed types:

- Paper: source_locator, definition, scientific_claim, math_claim.
- Dependency: source_locator, dependency_candidate, search_request.
- Lamport: At most one lamport_proof.
- Lean: At most one lean_source, which may include a small number of auxiliary files or declarations for the same target.

items may be empty only when issues explains the gaps. An empty result can account for a gap but cannot fulfill the substantive objective. The host sets delivery criteria for purpose before calling the model and must not lower them after receiving a result. Advancing past a Lamport or Lean stage requires its corresponding artifact; diagnostics alone cannot substitute for the intermediate layer.

A nonempty array does not establish complete coverage. Paper's purpose must bind a fixed source scope, with unread content explicitly disclosed through UNREAD_SCOPE issues. The host's scope ledger distinguishes processed, explicitly blocked, and unprocessed material. Committing one batch does not mean the whole paper has been inventoried.

## 3. Two reference forms, resolved in one commit

An **input reference** uses {"input": "current_input_alias"} and must identify an entry in Task.inputs that was actually shown. A **local reference** uses {"local": "current_item_id"} and must identify a unique item in the current output.items; forward references within that output are allowed. Models must not use current IDs to guess future objects.

Persistent identity is **the producer_task's original-byte hash + the output's original JSON-byte hash + item.id**. The producing task is essential: identical input aliases in different Tasks may bind different sources, so identical output bytes do not necessarily identify the same node. After checking the whole batch, the host atomically registers item indexes without modifying model payloads or replacing local references and saving another complete record set.

The next Task pins identity with producer_task, the output blob, and item_id, and verifies a real COMMITTED run binding that Task/output pair. The producing task provides context for interpreting the old item's input/local references; it does not authorize showing all old task material to the new model. Show only approved selected items and explicitly registered necessary context. Retain separate retry evidence for the same Task/output without creating duplicate nodes.

Reference types must match their uses: sources points to resolved source_locator items; definitions points to definition items; MathClaim.source_claim points to a ScientificClaim containing component_id; and component math_refs agrees with each MathClaim's reverse ownership. Every conclusion component requires a mathematical target or a nonempty residual, and components with mathematical targets may still retain uncovered scientific meaning. Revising a mapping creates a new ScientificClaim/MathClaim batch; do not append reverse references to immutable old components.

Structural correspondence may contain cycles, such as mutual ScientificClaim/MathClaim references. These are not proof cycles; do not treat every reference as a mathematical DAG edge. The Lamport module preserves joint premises, proof routes, and scopes. Historical relationship candidates do not automatically become proven edges.

Reject commits containing duplicate item.id values, dangling references, type mismatches, invisible inputs, or duplicate component IDs; retain the original output as diagnostics. Identical short IDs from different model runs do not establish shared identity. Compare by source location and meaning, not by forcing merges based on array order or text hashes.

## 4. Programs resolve original source locations

A model-authored source_locator specifies only the source input alias and verbatim start_marker/end_marker. The input must be a supplied complete UTF-8 text unit. Do not ask the model to produce byte_start, byte_end, or span_sha256.

The host applies the following exact-byte convention: UTF-8 encode both markers; require a unique start match; search for end from start onward and require a unique match there too; extract [start, end-of-end-marker), including both markers. Do not guess when the range is empty, reversed, missing, or ambiguous. Mark STAGED/OUTPUT_REJECTED and return the issue for revision in a new Task. Identical start/end markers are allowed only when unique within the relevant range.

The host records locator_id, source_sha256, byte range, and the actual span hash in run.source_bindings, rather than adding these fields to model output. Inputs referencing existing source locators also require reading their producing committed runs' location evidence. Resolving bytes establishes location correctness, not that the passage supports the claim.

The host also publishes the paper's own macro table. A preprocessing pass reads every
`\newcommand`, `\renewcommand`, `\providecommand` and `\def` out of the supplied sources -
the preamble **and the main file, since a paper may define its shorthand there** - and records
the table, the sources it was read from, the outcome, and any control sequence used but defined
nowhere supplied. This is mechanical work with a deterministic result, so a program does it and
the model never authors the table.

**Expansion supplies a table; it does not rewrite the source.** Byte offsets in
`run.source_bindings` remain offsets into the original source bytes, and `source_locator` markers
are still copied verbatim from the text the model was shown. The table travels as a separate
context input, so the model can write out `\mathcal{M}` where the paper wrote `\Mcal` without
anyone having to guess what `\Mcal` means. A macro defined nowhere supplied is reported in
`unresolved_macros` and never interpreted from memory.

A source need not have a downloaded tarball. Preserve actual local-file provenance without inventing downloads. Register TeX macros, main text, appendices, and .bbl files as actual source units; do not interpret unavailable macros from memory. PDF-to-text conversion, chunking, and similar transformations must first preserve their input/output relationships. Locations in transformed text must not be presented as original PDF byte positions.

## 5. Run: Host facts and separate checking layers

The host writes run.json according to run.schema.json; the model must not generate it. The receipt preserves the Task blob, actual call, output reference, layered checks, source bindings, and necessary artifacts.

- NOT_STARTED: Prerequisites are missing and no model call occurred; this is not a completed Agent execution.
- FAILED / CANCELLED / OUTPUT_REJECTED: A call was attempted but failed, was cancelled, or produced a rejected output.
- STAGED: The response and draft are preserved, but commit requirements are incomplete.
- COMMITTED: This batch's candidates and indexes were atomically saved; **not a declaration of proof, review, or whole-paper completion**.
- UNKNOWN: Call or commit outcome is uncertain; reconcile before retrying blindly.

Every state except NOT_STARTED requires a real call record. STAGED and COMMITTED require response and output bytes. provider_request_id may be null when the provider supplies none, but trusted host execution binding and actual request/response evidence are still required. A self-authored nonempty string is not a real call.

Record each of these seven check layers exactly once: SHAPE, TASK_BINDING, REFERENCES, SOURCES, LAMPORT_STRUCTURE, FORMAL_BUILD, and ALIGNMENT. Unperformed checks use NOT_RUN and report=null. PASS/FAIL must reference actual check reports; multiple layers may share one report blob. COMMITTED requires PASS in the first four layers, traceable to actual check inputs and implementations. Failed formal builds or unperformed alignment checks do not prevent saving honest code candidates, but cannot support claims of successful proof.

JSON Schema cannot establish real calls, authentic checks, unique IDs across items, cross-object bindings, valid source ranges, or cumulative budgets. Host semantic checks must be implemented before claiming v0.2 conformance; schema-valid JSON alone is insufficient for execution or delivery.
