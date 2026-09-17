# Host: The Minimum Path for Real Execution

This is an execution contract awaiting implementation, not a running service. The host is not a model Agent. Preserve v0.1's separation of responsibilities, reuse input-checking and accounting experience from handoff and model-call boundaries from host_reference, and avoid duplicating disconnected runtime systems.

## 1. Every research task must call a model

All four research operations must call a configured model during normal execution. Pure programmatic scans, copied responses, and manual seed replays do not satisfy this requirement. They may serve as mechanical preprocessing or explicitly labeled historical inputs, but are not new model artifacts.

Caching may reuse exact committed artifacts without inventing new runs. A newly requested research execution makes a new real call; resubmission of the same Task looks up the existing attempt rather than paying twice. Missing inputs or authorization do not justify an empty model call merely to satisfy the rule: record NOT_STARTED or waiting work.

Pydantic AI is an optional model-adapter implementation, not a reason to change the protocol. v0.1 adapter code cannot directly process the new Task/Output and needs explicit adaptation. This delivery does not install dependencies, select providers, or introduce a staged-draft success path that bypasses real calls.

## 2. Seven program-controlled steps

1. **Prepare sources and the plan.** Register actual local/remote source bytes and transformation provenance. The parent plan fixes paper count, depth, cumulative calls/time/cost, no-progress limits, and allowed sources. A missing tarball is valid. Build the macro table here, from the preamble and the main file
together, and register it as a context input alongside the sources it was read from; report every
control sequence used but defined nowhere supplied instead of interpreting it. Do not start
before plan, authorization, and input registration are implemented.
2. **Pin the Task.** Select operation, existing inputs, target, purpose, and interface version. Input aliases must be unique; verify all references against source bytes and authorization. Future outputs must not masquerade as existing inputs.
3. **Claim work and persist call intent.** Through one write entry point, reserve parent budget, obtain a generation-bound lease, and save the Task and a lossless description of actual model-visible content. Private authorization data and secrets stay out of model context.
4. **Call the model once.** The adapter uses the shared task/output contract and records the actual model, provider request identifier when available, response, duration, and usage. By default, one attempt issues at most one model request. Output repair requires another attempt, and transport retries are also accounted for.
5. **Check and stage.** Preserve the original response. Parse JSON strictly and reject duplicate keys, unknown fields, and exceeded bounds. Check operation, reference types, component correspondence, and target binding. The host resolves source_locator items. Instructions inside source files are always data.
6. **Commit candidates.** After fixing the output blob, register the run, item indexes, input dependencies, and pending projection messages in one SQL transaction. Do not change the model's mathematical payload. Preserve available responses and failure reasons without manufacturing empty candidate records.
7. **Continue.** Retrieval and acquisition of new sources occur between tasks. Register new explicit inputs before another model call; report unresolved gaps. Neo4j and Git are downstream consumers, not prerequisites for committing the main workflow.

A missing port is not an implemented feature awaiting parameters. This delivery defines the contract only; actual claiming transactions, calls, storage, retrieval, and checkers remain to be developed.

## 3. Source visibility and size checks

Count input bytes as actually rendered to the SDK, not just source-file sizes. Include JSON escaping, specifications, and tool/output schemas. Check provider token limits separately from byte limits. Replan smaller batches when limits are exceeded; do not truncate the tail and claim whole-paper completion.

An item input is a selector, not authorization to read all contents of its containing blob. The host may verify the entire blob hash for reproducibility, but may show the model only selected items and separately listed context. Dependencies within references establish identity and must not implicitly expand model visibility.

Interpret input/local references inside an input item in its producing Task/output context, not in the current task's alias space. During rendering, use a separate correspondence description to map authorized dependencies to current input aliases. Mark unavailable content as not visible without expanding or disclosing it through the mapping. New output may use only current input aliases or its own local IDs; do not rewrite original input blobs.

Preserve requests as lossless, reconstructible descriptions: a pinned renderer version, ordered message roles/text blobs/input selectors, complete generation parameters, and **the hash of the actual request content passed to the SDK**. Do not permanently duplicate source text or specifications in every request. A reconstruction mismatch invalidates a reproducibility claim. This description does not prove raw HTTP bytes or provider-internal prompts.

## 4. Checks that simplification must not remove

- Every non-Paper target must resolve to one committed math_claim. Changing target conditions creates a new MathClaim rather than overwriting the old object.
- A non-null Dependency upstream must resolve to a supplied actual upstream mathematical target or definition. Preserve citation when only bibliographic information exists; do not manufacture nodes. Candidate relationships remain candidates.
- Lamport artifacts bind the same target. Lean's lamport must reference a **previously committed** lamport_proof with the same target version. A string authored in the current call is not a pinned intermediate layer.
- Lean's environment must reference a host-registered environment descriptor fixing the toolchain, actual package identities, and axiom/trust-mechanism policy. Models cannot expand permissions. Environment checking remains unimplemented.
- Output item.id values, component IDs, input aliases, and check layers must each be unique in their respective scopes. Complete root fields do not establish real references or source code.
- Report generation, source resolution, Lamport structure, actual builds, and semantic alignment separately. A candidate graph does not provide independent review or scientific approval.
- A MathClaim's declared relation to its source is the model's statement and must be checked for consistency, not for honesty: VERBATIM with two differing wordings is a mislabel, and so is a declared departure that changed nothing. Whether the declared step is the *right* one is a reading judgement and belongs to review, not to the host. Macro expansion is the host's own mechanical output and is never taken from the model.

Source, definition, scientific, and mathematical items may use local references within one batch. This is a bounded atomic candidate batch, not permission for cross-task future references or direct conversion to a v0.0 RecordSet.

## 5. Failure, recovery, and actual savings

Workers with expired leases must not overwrite newer attempts. Recheck task cancellation, parent-budget exhaustion, and prior commits inside the write transaction. An SDK timeout does not establish that the provider charged nothing. Retain reserved funds when costs are unknown and reconcile before deciding whether to retry.

Persist intent before calling and pin response bytes before committing. If commit is interrupted, look up existing outputs by task/attempt. A missing success response is not permission to call the model again. Staged drafts may resume mechanical checking and commit; such recovery is not a new Agent execution.

Keep ongoing state in the execution ledger. run.json is an immutable attempt checkpoint or final receipt; revisions create new versions and retain predecessors rather than overwrite history. Recovering UNKNOWN must not rewrite an old error receipt into fabricated success.

Real model calls are required for research execution, not for every hash, save, source retrieval, or Lean build. Mechanical operations require actual program receipts distinct from research runs. Do not construct shell commands or Cypher from model text.

## 6. Implementation order

First implement independent v0.2 schema registration, cross-object checks, source resolution, and a minimal blob/index write entry point. Then connect a real model adapter and complete a small-scope Paper task. Next connect Dependency retrieval handoff, followed by the single-claim Lamport/Lean module. Development and testing remain separate: do not run acceptance checks without user authorization.

Do not begin with a full microservice suite, whole-paper certification workflow, or whole-graph formalization, and do not ask models to guess machine facts. All prerequisite gaps and future acceptance criteria belong only in [PENDING_TESTS](../schema%20v0.1/PENDING_TESTS.md), V02-*.
