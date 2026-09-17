# Compact Storage: Two Logical Deliverables, One Copy of Shared Content

## 1. What each attempt retains

A normally completed research attempt has two **logical delivery files**:

- output.json: The model's original JSON content, containing this call's new items and issues.
- run.json: The host receipt referencing the pinned Task, request description, response, output, necessary check evidence, and artifacts.

Tasks, request descriptions, responses, sources, specifications, and attachments still require storage, but belong in a shared content store rather than complete copies in every paper/round directory. Two logical files do not mean only two physical files or permission to omit reproducibility evidence. A failed call may have no output; retain actual responses and errors.

Store the original SDK/provider response and extracted JSON output only once if their bytes are identical. Otherwise, keep both and distinguish the response from the original content extracted from it. Do not call reserialized content original JSON, or erase rejected outputs or feedback merely to reduce size.

## 2. Three content categories and responsibilities

The **shared content store** holds immutable blobs addressed by SHA-256 of their original bytes, with length and media type in references. Register sources and specifications once. Do not normalize JSON Unicode or whitespace before computing an original-byte identity. Compression does not change logical identity: hash the original bytes recovered after decompression.

The **SQL index and execution ledger** hold tasks, attempts, call intent, budgets, state, coverage, item locations, and input dependencies. Global candidate identity is (producer_task_sha256, output_sha256, item_id). Index kind, producing-run associations, targets, and necessary relationships without copying entire payloads. The producing Task fixes input-alias meanings: identical output bytes may share storage, but nodes with different source contexts do not merge. Verify actual bytes even when hashes match; never silently overwrite conflicts.

**Derived views** include human-readable explanations, paper summaries, graphs, and Git exports. They are not another editable source of truth. Source-object changes require new identities. Neo4j projects only committed candidates with explicit state and must not turn candidate edges into approved reuse.

This delivery creates no database, directory runner, or migration script. Start single-machine development with one transaction owner and a shared blob store; this is not a claim that the current LocalStore supports the protocol.

## 3. Avoid copying entire chains as the collection grows

When a paper uses an upstream claim, save the exact reference and this comparison's rationale rather than embedding every upstream paper record. Multiple papers sharing a source, definition, or code artifact share the actual blob.

Use short local references within one output batch. Save source bindings and production provenance at batch level instead of repeating a full host envelope for every node. Mathematical assumptions with distinct roles in different propositions remain necessary content; similar wording alone does not justify merging them.

By default, do not save cumulative records.json files, full claims.md files, AGENT.md copies for every round, individual files for every edge, or self-contained snapshots of the whole collection. Generate presentation views from fixed versions when needed. Portable exports collect the reference closure and deduplicate it separately.

Use HOST.md's reconstructible content references for actual requests so logs do not copy full source text again. Preserve necessary visible model responses without requiring hidden reasoning. Specifications, model configurations, original responses, and consumed intermediate versions must still be retained.

## 4. Size control is not truncation

The protocol sets per-output safety ceilings of 1 MiB and 256 items; individual Tasks may set smaller limits. These are neither targets to fill nor limits on the total claims in a paper. Initial development may observe batches of a few tens of KiB, but no fixed per-paper size is promised without measurement.

Split long papers into Tasks along source-unit and assertion boundaries while preserving the parent coverage ledger and unread ranges. Do not drop conditions, abbreviate away formulas, or incorrectly separate joint existential quantifiers to fit a limit. A long proof may retain the same claim while using additional versioned module stages; this must not become bulk formalization of the upstream chain.

Lean source is produced once in output; build workspaces are controlled derived copies. Bind build evidence to actual file bytes. Look up reusable compiled artifacts or model intermediates by fixed content identity and purpose, not by selecting the latest file with a matching name.

## 5. Commit and lifecycle

Pin immutable blobs first, then register the run, item indexes, coverage progress, and outbox in one SQL transaction. Unreferenced blobs left by failed SQL transactions may be handled by a retention policy; committed indexes must never point to unpinned or unchecked bytes. If a request was paid for but staging failed, retain an uncertain attempt and reconcile during recovery.

COMMITTED means only that the candidate transaction completed. Storage state must not conceal unread text, unavailable code, missing review, or failed builds. Each check result binds a specific version; a historical pass cannot carry over to new code.

Git is an on-demand archival export, not a queue for millions of runs. File-based blobs are an initial small-scale backend. At capacity limits, a packed or object-storage backend may replace them while preserving logical identity. Neo4j alone does not solve blob count, source-store capacity, or transaction problems.

Retention policy must not delete blobs still referenced by inputs, check evidence, or archives. Compressing or cleaning unused staged failures requires an explicit policy and reference-reachability checks. This delivery does not automatically clean historical files.
