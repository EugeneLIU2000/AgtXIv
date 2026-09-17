# Schema v0.2: Real Model Execution, Compact Candidates, Single-Claim Formalization

Version: research/0.2.0. Date: 2026-09-16. **This delivery contains the converged specifications, JSON Schemas, and a hand-authored teaching example. No v0.2 host has been implemented or run, and no tests are claimed to have passed.**

## The core idea

**A paper enters a real model call and produces research candidates in a shared format. Programs resolve source locations, check references, and save incremental results. The optional Lamport-to-Lean branch operates on one selected MathClaim only.**

This is not a reduced scientific certification system. Extracted candidates, citation leads, proof drafts, and code drafts may be saved without automatically becoming proven propositions or approved reuse relationships.

## Three non-negotiable principles

1. **Every executed research task calls a model.** Replaying a manual seed, copying an old result, or scanning citations alone does not constitute a new Agent execution. Missing inputs may prevent a task from starting; hashing, retrieval, storage, and builds do not require additional model calls.
2. **The format is shared; content may differ.** Different models use the same Task, output fields, and checking rules. Node counts, wording, and research judgments need not match, and semantic differences must not be concealed.
3. **Store the minimum sufficient information.** Keep original sources, specifications, and artifacts once and use exact references elsewhere. Preserve mathematical conditions, quantifiers, sources, and gaps. Autoformalization always operates on one fixed version of one MathClaim.

## Specification language

All specification documents, Agent instructions, schema descriptions, comments, and bundled examples under this directory MUST be written in English and MUST NOT contain Chinese text. File and directory names must also remain English. Mathematical notation and existing machine identifiers are preserved; English-only does not mean ASCII-only.

This documentation rule does not authorize translating or modifying external source bytes, exact source markers, or historical evidence consumed at runtime. Such material retains its original identity and is not rewritten as part of maintaining these specifications.

## Reading guide

| Question | Entry point |
|---|---|
| What does one task receive and return, and what belongs to the model? | [CONTRACT.md](CONTRACT.md) |
| How do we prevent files and content from growing unnecessarily? | [STORAGE.md](STORAGE.md) |
| How do real calls, scheduling, and recovery connect? | [HOST.md](HOST.md) |
| What carries over from v0.1, what changes, and which report recommendations are accepted or rejected? | [MIGRATION.md](MIGRATION.md) |
| What are the minimum responsibilities of each Agent? | [Paper](<Paper Agent/AGENT.md>), [Dependency](<Dependency Agent/AGENT.md>), [Autoformalization](<Autoformalization Agent/AGENT.md>) |
| What does a short output look like? | [examples/paper-minimal](examples/paper-minimal/README.md), hand-authored rather than executed |
| What still needs implementation or testing? | [Central pending-test list](../schema%20v0.1/PENDING_TESTS.md), V02-* |

## Only four active research operations

- **paper.extract**: Extract source locators, definitions, ScientificClaim candidates, and MathClaim candidates.
- **dependency.search**: Propose historical searches for one MathClaim, compare available upstream material, and save relationship candidates. The host performs actual retrieval between tasks.
- **autoformalization.lamport**: Produce a Lamport proof intermediate artifact for one MathClaim.
- **autoformalization.lean**: Consume a previously saved Lamport artifact and a fixed environment for the same MathClaim, then generate Lean source drafts.

The last two operations belong to the same Autoformalization module. They are separated to pin the intermediate artifact and support independent iteration, not to add two resident Agents. There is no whole-paper autoformalization operation or recursive formalization of every upstream node.

The v0.1 Review, Planner, Delta, and Reader specifications remain available, but are not copied into the mandatory v0.2 startup path. Introduce versioned adapters when needed; v0.2 does not thereby acquire formal review or admission authority.

## Files and completion boundary

Five machine schemas cover common definitions, host tasks, candidate items, model outputs, and host run receipts. The schemas govern JSON shape; CONTRACT and HOST govern cross-object rules, source bytes, real calls, and task semantics. The corresponding checkers still need implementation.

This is a **new research-candidate protocol**, not a version-label change to a v0.1 Task or v0.0 domain record. The 64 v0.0 domain record types and their formal checking system remain intact. v0.2 objects cannot be written directly into the old LocalStore.records or passed to old checkers. Conversion into the formal domain layer must meet its existing evidence and authorization requirements; missing requirements block conversion rather than justify fabricated independent review.

The convergence work does not change v0.1 implementations, historical examples, or old domain schemas. The only exception is appending v0.2 entries to the existing PENDING_TESTS file. The next minimum acceptance case is a small section of a new paper, one real model call, a shared output format, checkable sources, persistence, and continuation, not another manually assembled directory that merely looks complete.
