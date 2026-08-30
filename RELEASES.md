# Release and version policy

## Scope

AgtXIv has several independent kinds of versioned objects. This policy prevents
a Git tag, schema number, database revision, or paper version from being
mistaken for another kind of release.

There is no stable AgtXIv V2 software release yet. Planned names in the roadmap
are targets, not claims that those releases already exist.

## Release events are not one approval

1. **Code merge** places reviewed repository changes on the protected default
   branch after `ci-required` and required code-owner review.
2. **Software release** packages an exact Git commit, changelog, dependency lock,
   build provenance, and release artifacts under a version tag.
3. **Paper Agent package archive** stores an exact replay bundle only after its
   V2 Root Agent audit and independent mechanical certification pass.
4. **Knowledge Base admission** reviews and admits eligible entries from an
   archived package in a later atomic transaction.

No event automatically causes the next one. In particular, code merge has no
scientific meaning, and package archive does not admit reusable knowledge.

## Independent version axes

| Axis | Identifier and rule | When it changes |
|---|---|---|
| Software | Semantic Versioning tag `vMAJOR.MINOR.PATCH`, with standard pre-release suffixes such as `-alpha.1` | User-visible software compatibility or a release build changes. |
| Contract bundle | Exact bundle identity, Semantic Versioning value, content hash, and release root | Any bound schema, canonicalization rule, profile, catalog, validator, policy, adapter, environment manifest, or authoritative specification blob changes. |
| JSON Schema | Exact `$id` and discriminator ending in `MAJOR.MINOR.PATCH`; published bytes at one identifier never change | Major: incompatible instance meaning. Minor: an additive contract revision. Patch: a behavior-preserving clarification or correction. Every case receives a new exact identifier and impact note. |
| Database | Immutable migration revision and ordered parent revision; application records its supported range | Tables, constraints, indexes, policies, or data transformations change. Migration revisions are not Semantic Versions and are never reused. |
| Paper source | Exact arXiv work and explicit source version, source locator, and byte/tree hashes | A new paper version or a different canonical byte tree is selected. An omitted URL version is resolved once and frozen. |
| Paper Agent | Exact source release, profile and scope references, manifest record revision, release hash, and replay-bundle root | Any source, scope, artifact, assessment selection, audit, certificate, rights disposition, or bound contract changes. An old release is never overwritten. |
| Producer environment | Producer version plus exact dependency, model, toolchain, and environment hashes | Producer behavior or executable environment changes. |
| Knowledge view | Domain, immutable snapshot revision/root, and admission transaction | An independently reviewed entry or relation is atomically admitted, withdrawn, or superseded. |
| API | Major path such as `/v2` plus published OpenAPI contract revision | Transport compatibility changes; API version does not replace record-schema versions. |

Semantic Versioning describes compatibility; exact hashes establish identity.
Two objects with the same human-readable version but different required hashes
are not the same release and must be rejected.

### Schema compatibility rule

Old records remain bound to their original exact schema. A new validator must
not silently reinterpret them under the current schema. Because older strict
validators can reject even an additive field, a minor schema release still
requires a new URI, fixtures, compatibility statement, and migration impact
assessment. A correction that changes the accepted instance set or meaning is
not a patch merely because it fixes a bug. A patch version never authorizes
changing already published bytes.

### Database migration rule

Database upgrades run only through committed migration revisions. Each migration
declares upgrade behavior, whether downgrade is safe, backup requirements, and
the forward-repair path when append-only data makes downgrade inappropriate.
Release tests cover a clean database and the oldest supported upgrade path.

### Paper Agent release rule

A Paper Agent release is not versioned by software Semantic Versioning. Its
identity is content- and context-bound. A correction creates a new manifest,
audit, certificate, bundle root, and explicit supersession relation. Scientific
`CORRECTS` or `REFUTES` relations require their own assessments; operational
supersession does not imply either.

## Software release flow

1. Freeze the intended commit and confirm the working tree is clean.
2. Update `CHANGELOG.md` with user-visible changes, compatibility, migrations,
   security notes, known blockers, and upgrade instructions.
3. Reproduce the locked environment and pass the required fast, full, release,
   migration, generated-drift, security, and artifact checks applicable to the
   milestone.
4. Verify that every action and dependency used for the build is pinned and that
   generated artifacts bind exact inputs and producer versions.
5. Build from the exact reviewed commit; record digests and provenance for every
   distributed artifact.
6. Create an annotated version tag and release notes only after required
   approvals. A tag is not itself a cryptographic signature.
7. Verify downloadable artifacts independently and retain the release evidence.
8. If a fault is found, publish a new patch or pre-release and an explicit
   supersession, withdrawal, or security advisory. Do not replace release bytes.

## Current release blockers

The root license, copyright holders, and inbound contributor mechanism are not
decided, so a stable public software release and a claim of professional
open-source readiness remain blocked.

The production signature suite and key governance are also undecided. Therefore
the project must not label current Git tags, hashes, certificates, or bundles as
cryptographically signed production releases. The scientific-reviewer policy is
undecided, so no production Knowledge Base admission may be represented as
independently scientifically reviewed. See
[`GOVERNANCE.md`](GOVERNANCE.md#open-governance-blockers).

## Planned V2 sequence

Subject to all milestone and governance gates, the roadmap plans:

- `v2.0.0-alpha.1` for the M0–M1 contract kernel;
- `v2.0.0-alpha.2` for the local real-paper vertical slice;
- later alpha releases for persistence, intake, graph, and formalization work;
- beta only after release, archive, review, and admission invariants exist;
- a release candidate after the integrated public demo and offline verifier; and
- `v2.0.0` only after migration, security, governance, legal, and public-project
  gates pass.

These entries are forecasts. `CHANGELOG.md` records only work actually present
and must not turn a planned name into a released version.
