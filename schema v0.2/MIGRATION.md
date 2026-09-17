# Converging v0.1 into v0.2: Preserve Meaning, Change the Research Execution Interface

## 1. Basis and decision priority

Priority: the user's three principles of 2026-09-16, then the current convergence design, then short-term recommendations in the analysis record. The report is not adopted wholesale.

The reference is [framework-gap-analysis-record](../.claude/worktrees/schema-0-1-delivery-plan-82425f/docs/superpowers/specs/2026-09-16-framework-gap-analysis-record.md), workflow wf_4fc5564a-84f. It contains six investigations and five rebuttals; the Autoformalization rebuttal and final synthesis were not completed. Effort estimates cannot simply be summed and are not commitments for this delivery. The original record may exist only in a local worktree. Its recommendations are summarized below; that path is not a runtime dependency.

The record repeatedly uses September 23 as a deadline, while the user's existing deadline is September 22. This version does not extend it or substitute the report's two offline steps for the requested real-model workflow.

## 2. What is retained

- [Paper R1-R8](../schema%20v0.1/Paper%20Agent/AGENT.md): Original assertion boundaries, shared premises, strength and attribution, direct sources for conditions, and no silent repair of the original proposition.
- [Dependency](../schema%20v0.1/Dependency%20Agent/AGENT.md): Citations are not mathematical dependencies; compare definitions, conditions, and intended uses; do not invent an upstream MathClaim without obtaining it.
- [Autoformalization invariants](../schema%20v0.1/Autoformalization%20Agent/AGENT.md): Fixed targets, host-owned execution facts, compilation distinct from semantic alignment, and local assumptions confined to their scopes.
- [handoff](../schema%20v0.1/handoff/README.md): Exact-byte reading, execution accounting, idempotency, and recovery experience. Its citation-only handler may serve as preprocessing, not v0.2 model execution.
- [host_reference](../schema%20v0.1/host_reference/README.md): Pinned inputs, controlled model adapters, original output retention, and reconciliation before retrying uncertain commits. Its Protocol backends still require implementation.
- [Graph and storage boundaries](../schema%20v0.1/GRAPH-INTERFACE.md): SQL/content storage as the source of truth, rebuildable Neo4j, retrieval between tasks, and Git not blocking authorized local research.

## 3. Intentional incompatibilities

| v0.1 | v0.2 decision |
|---|---|
| Different Agents have different draft root fields | One Output root; operation determines allowed items. Each content type retains explicit fields rather than becoming arbitrary JSON. |
| Model-authored source-span payloads require actual offsets/hashes | Models output source_locator; the host computes actual ranges/hashes and stores resolution mappings in run. |
| An output cannot reference future formal RecordRefs, requiring many registration rounds | One bounded candidate batch may use local references and commit atomically after whole-batch checks. Cross-task inputs still require existing exact identities. |
| Domain records require full producer/policy/review envelopes | Candidate production provenance is stored per run. ScientificClaim/MathClaim correspondence remains a candidate mapping, without fabricated independent review for claim-component-map. |
| Existing Task and formalization-packet prerequisites | A new research Task pins one MathClaim, Lamport, and environment. It is not the old formalization.generate and does not claim to satisfy the old packet. |
| Lamport is a reading view over existing argument records | A versioned Lamport intermediate artifact becomes the module boundary. The initial lightweight text format is neither the old lamport-view schema nor a machine proof. |
| Each round accumulates records, claims, and specification copies | Save this round's output and host run; reference other content through shared storage and generate views on demand. |
| Utility has a separate Agent operation directory | Fixed services perform acquisition, parsing, storage, and builds. All four research operations make real model calls. |

These changes use a new research/0.2.0 namespace. Do not insert candidate items into a v0.0 RecordSet, map COMMITTED to formal EVIDENCE, or substitute this version into the old five-schema loader. v0.1 files and historical failures remain intact.

## 4. Decisions on report recommendations

| Report finding or recommendation | Decision and destination |
|---|---|
| HOST missed gap: Models directly output source-span hashes; seed conventions are unspecified | Accept the problem and define locator/host-resolution interfaces. Do not retain paper-specific seeds as the normal entry point. |
| PA-02 / HOST-03 / G-U8: Assembly primitives already exist; not everything needs rewriting | Reuse mechanical capabilities without copying 2608-specific filenames, claim allowlists, or whole-paper replay scripts. |
| PA / D / U: null archive, .bbl, head.tex, and verify.py hardcoding | Cover these in source-adapter acceptance work. Output defaults cannot conceal source-format differences. |
| D missed: The model sees only fragments inside the target closure | Require a pinned source-coverage ledger and actual visible inputs. Local scans cannot be reported as exhaustive paper or historical searches. |
| D / GR: Different manifests coexist in one directory | Use shared research run/output formats, not mixed Agent-specific manifests. Old formats require explicit adapters. |
| G-U7: Duplicate numbering in depends_on escapes the single-item checker | New Tasks do not predeclare future nodes; actual inputs establish dependencies. The old defect is not dismissed merely because a check was missing. |
| PA-07 / HOST-01 / D-G5: Bypass the SDK and manually import drafts to deliver a case | Reject as a research execution strategy. Real model calls are required. Old material and diagnostic replay cannot create fictitious new runs. |
| HOST-05 / G-U1: A complete packet needs additional Scope/Proof/environment chains | Accept the finding. Define the single-claim research branch as a new protocol rather than claim old prerequisites are met or remove old guards. |
| AF-G2: EXPLORATORY can bypass missing scope | Reject. The old schema still requires scope_ref; the new candidate protocol cannot stand in for the old formal packet. |
| G-U5 / G-U12: Payload checks omit root conditions; request/receipt bindings are not real | Preserve layered checks and actual-call requirements. Formal conversion must run complete old schema/RecordSet checks rather than reuse candidate PASS states. |
| GR: Defer Neo4j deployment and begin with reference reads | Accept. Prioritize node data and replaceable query backends; do not add provenance.json that duplicates a manifest. |
| AF: Begin with an existing local lemma rather than the paper's central hard problem | Consistent with the single-MathClaim unit. Do not adopt unchallenged effort estimates or present a conditional lemma as a complete proof of the paper. |

## 5. Conversion into the old formal domain system

Preserve the original Task, model response, candidate identity, source mappings, and conversion version while explicitly assembling v0.0 envelopes and references. Retain physical systems, comparison baselines, strength, quantifiers, sources, and residual scientific meaning. Similar field names do not establish lossless mechanical conversion.

Formal scope-decision, frozen-scope, argument-snapshot, formalization-packet, formal-check, alignment, and related records still require actual content and evidence under their existing rules. A candidate's eligibility for storage in v0.2 does not justify inventing an ACCEPT reviewer or fake check logs.

An automatic converter is not implemented. There is no claim that all candidates can pass old validation. Some v0.2 scientific information is embedded in statement/residual; extracting it into old fields may require a new source-grounded model task and review rather than field copying.

Do not add database migrations, move old paper directories, or rewrite historical SELF_REVIEW results at this stage. Further development should focus on the real single-claim path. All pending design, implementation, and acceptance work remains in the central V02-* list.
