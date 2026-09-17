# Autoformalization Agent - research/0.2.0

## Fixed interface, evolvable internals

**One Task targets one fixed version of one MathClaim.** Do not process an entire paper or require formalization of the full upstream chain. See [CONTRACT](../CONTRACT.md) for the shared interface. Task.module must reference a host-registered module version; this specification is not a complete proof engine.

Both operations make real model calls and use the shared four-field output. Report missing target conditions rather than modifying the input proposition to achieve success. A changed target requires a new MathClaim and Task.

## First operation: autoformalization.lamport

Inputs are the single target, sources and definitions needed to interpret it, and explicitly supplied proof material or upstream candidates. Output at most one `lamport_proof`; if no draft can be formed, return items=[] and explain the issues.

The fixed outer fields are target, format_version, text, premises, and open_steps. The initial intermediate version is `lamport-text/0.1`. text uses the following public proof structure:

- Begin with the target proposition and its original assumptions. Use hierarchical step numbers such as `<1>1` and `<2>1`, identifiable within their scopes.
- Each step states a proposition, the assumptions or earlier steps it uses, and the mathematical justification. Nested subproofs explicitly introduce and discharge local assumptions.
- Use jointly required premises as AND, omitting none. Distinguish alternative proof routes rather than combining them into circular dependencies.
- QED references the steps establishing the current-level conclusion. List unfinished work in open_steps and explicitly state when the final QED has not been established; do not present it as a completed proof.

This requires reader-checkable mathematical arguments, not private reasoning traces. Host structural checking remains to be implemented; passing structural checks would not establish proof correctness.

premises references existing inputs and explains their uses. PROPOSED denotes an unchecked dependency. EXPLICIT_ASSUMPTION denotes an additional explicit condition and does not establish the original target unconditionally. CHECK_EVIDENCE_PROVIDED means only that the Task also contains check evidence the host can verify; the model cannot grant itself a trusted identity. Missing actual evidence requires rejecting that qualification or opening another task, not replacing verification with a string.

## Second operation: autoformalization.lean

Inputs must include the same MathClaim, a **previously committed Lamport artifact bound to that target**, and a host-pinned environment. Existing upstream Lean modules may also be supplied. Output at most one `lean_source` with target, lamport, environment, files, and target_declarations.

- Code may be constructed independently or reuse supplied upstream code or packages allowed by the environment. Reuse does not change the single-target boundary.
- The environment descriptor fixes the Lean toolchain, package identities/versions, and trust-mechanism policy. Report missing packages, interfaces, or version mismatches for the host to handle; do not independently install anything over the network.
- Files contain only relative `.lean` paths and source drafts. They do not grant shell, build-script, or arbitrary write-path permissions. The host rejects duplicate names, case aliases, out-of-bounds paths, and symlink targets, and builds separately in an isolated workspace.
- Explicitly identify unresolved premises, sorry, additional axioms, or added assumptions. A successful build does not establish the original MathClaim; the environment, axioms, target declarations, and correspondence to the original proposition still need checking.

## Iteration and delivery boundary

Lamport drafts with gaps may be saved. Lean drafts consuming them may also fail or remain incomplete, but must not be promoted to verified results. Generation, Lamport structure, actual Lean builds, and mathematical alignment are separate check layers.

If the module later adopts a structured Lamport step tree, different search strategies, or more repair rounds, update module/format_version and state compatibility explicitly. Paper and Dependency need not change their outputs. This document does not duplicate the complete v0.1 packet, independent-review, and scope-admission workflow. Formal admission still requires explicit adaptation satisfying those requirements; they cannot be bypassed.
