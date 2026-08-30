# ADR 0004: Accounting, archive, and per-entry admission

- Decision status: Accepted
- Implementation status: Planned across M1, M2, and M6
- Milestone: M0
- Date: 2026-08-31
- Roadmap decisions: D4, D5, D7
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## Context

"The pipeline finished," "the package is safe to preserve," and "this theorem is
eligible for reuse" answer different questions. Collapsing them into one green
status would hide blocked artifacts, make a successful Lean build look like
scientific acceptance, and allow one acceptable entry to launder an entire mixed
package. Git pull-request merge is yet another unrelated event.

The intuition is a research archive and a curated reference handbook. An archive
keeps the complete evidence bag, including failed experiments. The handbook
admits particular reviewed results. Archiving a bag does not endorse every item;
rejecting an entry does not justify destroying its provenance.

## Decision

The release and reuse path is:

```text
ACCOUNTING_COMPLETE
  -> V2 Root Agent audit
  -> independent mechanical certification
  -> CERTIFIED_RELEASE
  -> immutable archive + ArchiveReceipt
  -> independent per-entry review and eligibility decision
  -> atomic knowledge-admission transaction
```

### Artifact accounting

An exact, profile-bound `ArtifactFamilyCatalog` defines each family, its
applicability, cardinality, producer role, success record, allowed terminal
results, review policy, persistence mapping, and gates. The catalog is part of
the contract bundle. An applicable obligation is accounted only by a valid
artifact or a policy-allowed, evidence-bearing terminal result.

Catalog maturity is tracked independently as
`CONTRACTED -> PRODUCED -> PERSISTED -> REVIEWED -> EXPOSED`. A V1 adapter is
required only when a real legacy counterpart exists. A dedicated UI panel is
required only for user-facing families; every record remains retrievable through
the generic artifact explorer. At `v2.0.0`, `UNSUPPORTED` cannot satisfy any
required core-profile obligation, and every required core family has at least
one positive producer case in the release corpus.

`ACCOUNTING_COMPLETE` may contain `BLOCKED`, `FAILED`, `REFUTED`, and
`NOT_APPLICABLE`. It means that no obligation disappeared, not that every result
succeeded.

### Archive and admission

A certified mixed-status package may be archived with zero reusable entries.
Admission happens only after archive and is computed per candidate entry. The
review and transaction exact-bind the immutable archive root; they do not modify
the release bundle. Accepted, rejected, and blocked candidates all remain
traceable.

Admission is one append-only atomic transaction with exact before/after snapshot
hashes. A rejected or blocked candidate adds no knowledge entry. Failure aborts
the complete transaction rather than leaving partial mutation. Withdrawal,
revocation, correction, and supersession append records and do not erase earlier
snapshots.

### Roles and evidence

Actors declare `actor_kind = HUMAN | AGENT | MECHANICAL_SERVICE`, exact identity,
role, applicable policy, and independence evidence. The producer, scope-freeze
reviewer, V2 Root Agent auditor, mechanical certifier, and scientific admission
reviewer obey the separation-of-duty policy in both application logic and
database constraints. Clients submit review, certification, or admission
requests; they cannot author a final certified or admitted state directly.

Reviews exact-bind the bytes, records, contract, policy, scope, and environment
they assessed. Any change makes the review stale. Only public rationale,
findings, evidence, uncertainty, non-implications, and signed attestation are
stored; private chain-of-thought is neither requested nor persisted.

Git pull-request merge remains code governance and carries no scientific,
archival, certification, or admission meaning.

## Consequences

### Positive

- Failed or blocked science remains inspectable without being presented as
  reusable truth.
- Fine-grained admission prevents package-level status laundering.
- Archive and knowledge snapshots are reproducible, reviewable, and recoverable.
- Role separation makes the accountable scientific judgment distinguishable from
  mechanical integrity checking.

### Costs and constraints

- The system needs separate state machines, queues, permissions, signatures, and
  user-interface labels for audit, certification, archive, and admission.
- Review changes require new immutable decisions instead of row updates.
- Catalog coverage needs both contract-level and operational producer tests.
- Concurrency and stale-input handling must be enforced transactionally.

## Invariants

1. Accounting completion never implies formal success, scientific acceptance,
   certification, archive, or admission.
2. Root audit and certification precede release/archive; per-entry admission
   branches only after an immutable archive receipt exists.
3. Root audit is accountable scientific/profile judgment; certification is an
   independent mechanical check and cannot change the selected evidence or
   frontier.
4. Producer, Root Agent, certifier, and admission reviewer satisfy exact identity
   and conflict-of-interest separation.
5. Every applicable catalog obligation has exactly one valid artifact or terminal
   disposition for the frozen scope and profile.
6. Every admitted entry has its own eligible review and exact provenance to the
   archived root; package certification is insufficient.
7. Admission is atomic, append-only, idempotent, and binds before/after snapshot
   hashes.
8. Rejected and blocked candidates remain addressable and add no knowledge entry.
9. No review survives a change to any reviewed byte, record, contract, policy,
   environment, or scope.
10. Git merge has no automatic effect on these states.

## Acceptance tests

| Test | Expected result |
|---|---|
| Complete every catalog obligation with a mixture of valid artifacts and allowed blockers | `ACCOUNTING_COMPLETE` may pass; scientific success and admission remain unchanged. |
| Return `UNSUPPORTED` for every required core family | Operational coverage gate fails even if each result is schema-valid. |
| Root Agent attempts to certify its own audit or producer attempts to perform the Root audit | Application policy and database constraints reject the operation. |
| Certifier changes the unresolved frontier or scientific recommendation | Certification record is invalid; the certifier may only accept/reject exact mechanical checks. |
| Archive a certified package with no eligible entries | Archive succeeds and receipt exists; knowledge snapshot is unchanged. |
| Admit two eligible and one rejected candidate from one archive | Only the two eligible entries appear atomically in the new snapshot; the rejected candidate remains in the receipt. |
| Cause a transaction failure after staging one entry | Entire admission aborts; before and after snapshot refs are identical. |
| Change one reviewed record after review | Review becomes stale and cannot authorize certification or admission. |
| Merge code in Git | No Paper Agent release, archive receipt, or knowledge entry is created automatically. |

## Related records

- `docs/roadmaps/v2-end-to-end-implementation-plan.md`, decisions D4, D5, D7
- ADR 0001 for authority and replay bundles
- ADR 0003 for the frozen accounting denominator
- ADR 0005 for independent mathematical evidence axes
- `docs/security/v2-threat-model.md` for role, signature, and transaction threats
