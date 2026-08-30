# ADR 0001: Released content authority

- Decision status: Accepted
- Implementation status: Planned across M1, M1.5, M2, and M6
- Milestone: M0
- Date: 2026-08-31
- Roadmap decisions: D1, with D4 and D10 boundary consequences
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## Context

AgtXIv produces several very different kinds of state: reviewed source code and
schemas, arbitrary paper bytes, generated artifacts, a certified Paper Agent
release, operational job state, and reusable knowledge entries. Treating all of
them as "the database" would create competing authorities. In particular, Git is
well suited to reviewable contracts but not to an unbounded collection of paper
archives, while a mutable relational row is not sufficient evidence for a
released scientific object.

The physical intuition is a laboratory sample and its chain of custody. Git holds
the protocol used by the laboratory. Content-addressed storage holds the sealed
samples. A release bundle is the signed evidence bag. PostgreSQL is the custody
ledger and query index. An index may be rebuilt; it must never become more
authoritative than the sealed evidence it describes.

## Decision

1. **Git is authoritative for reviewed repository material.** Code, schemas,
   migrations, fixtures, architecture decision records, human-readable
   specifications, policy, validators, and versioned contract releases are
   reviewed and versioned in Git.
2. **Git is not the production byte store.** Arbitrary acquired paper bytes and
   generated binary artifacts are stored by cryptographic digest in
   content-addressed storage (CAS). A mutable filename or URL is metadata, not an
   object identity.
3. **The canonical released semantic object is a replay bundle.** A certified
   Paper Agent release is sealed under one signed Merkle root. The sealed bundle
   contains or exactly binds the producer records, selected pre-release
   assessments, Root Agent audit, mechanical certificate, artifact ledger,
   artifacts or authorized byte locators, rights dispositions, contract bundle,
   and environment receipts needed for offline verification.
4. **Later knowledge decisions do not rewrite the bundle.** Archive receipts,
   per-entry admission reviews, eligibility decisions, ingestion transactions,
   knowledge snapshots, withdrawals, and supersessions are separate immutable
   records that bind the archived root.
5. **PostgreSQL is the operational transaction authority.** It is append-only for
   jobs, attempts, events, reviews, releases, archive transactions, admission
   transactions, exact references, and query projections. Released projections
   must be reconstructible from the replay bundle and separately bound
   post-release records.
6. **SQLite is a disposable projection.** It may support development and offline
   browsing, but it is rebuilt from canonical records and is never an alternate
   source of truth.
7. **The M1.5 walking slice uses the same authority model.** Filesystem CAS and an
   in-process runner implement the production-shaped repository interfaces. M2
   replaces adapters with object storage and PostgreSQL; it does not invent new
   semantic objects or state transitions.

## Consequences

### Positive

- A release remains verifiable even if the operational database is rebuilt.
- A changed URL, filename, web projection, or database row cannot silently
  change the bytes or semantics of an existing release.
- Local development is simple without making SQLite a second production model.
- Rights-restricted bytes can be withheld while their digest, immutable locator,
  and rights disposition remain auditable.

### Costs and constraints

- Release construction requires canonical serialization, a Merkle-tree format,
  signature policy, and an offline verifier.
- Operators must back up both CAS and the append-only registry and test their
  reconciliation.
- A projection bug is repaired by producing a corrected projection or new
  immutable record; released evidence is not edited in place.
- A bundle can be larger than a conventional database response because it is
  designed for replay and audit, not only serving.

## Invariants

1. No released object is identified only by a path, URL, database primary key, or
   the word `latest`.
2. Every byte-bearing manifest entry has a cryptographic digest and a rights
   disposition; when bytes are present, the verifier recomputes the digest.
3. One release root commits to the complete canonical tree and exact contract and
   environment bindings.
4. A released bundle is immutable. Corrections, withdrawals, and supersessions
   append records that bind the earlier root.
5. Every released PostgreSQL projection is reproducible from canonical bundles
   plus immutable post-release transactions.
6. SQLite loss or deletion cannot destroy canonical scientific evidence.
7. Git pull-request merge, release certification, package archive, and knowledge
   admission remain distinct events.

## Acceptance tests

| Test | Expected result |
|---|---|
| Change one artifact byte after manifest creation | Merkle/bundle verification fails closed. |
| Rename an artifact without changing its declared canonical path | Bundle verification detects tree drift; a filename cannot substitute for a typed object. |
| Delete and rebuild released, knowledge, and query projections from bundles plus immutable post-release transactions | Exact record identities, release roots, decisions, and query results reconcile. Operational job/lease history is recovered from the PostgreSQL append-only backup/recovery path, not inferred from release bundles. |
| Delete the local SQLite projection | Canonical bundles and PostgreSQL authority are unaffected; the projection can be rebuilt byte-equivalently at the record level. |
| Archive a rights-restricted source without redistributable bytes | Offline verifier validates the digest, locator, and rights record and reports that authorized bytes are required for byte verification. |
| Attempt to update an archived bundle or append a later admission review inside it | Operation is rejected; a new immutable transaction binding the archive root is required. |
| Run the same replay/contract suite against filesystem and production adapters | Both adapters produce the same canonical record hashes and bundle root. |

## Related records

- `docs/roadmaps/v2-end-to-end-implementation-plan.md`, decisions D1, D4, D10
- ADR 0002 for exact contract and signature binding
- ADR 0004 for archive and per-entry admission
- `docs/security/v2-threat-model.md` for CAS, signature, and rights controls
