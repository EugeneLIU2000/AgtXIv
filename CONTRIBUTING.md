# Contributing to AgtXIv

Thank you for helping improve AgtXIv. This repository is developing a
verification-aware paper-agent protocol and its reference implementation. A
pull request can improve code or research infrastructure, but merging it does
not certify a paper, archive a Paper Agent release, or admit scientific content
to the Knowledge Base.

## Before contributing

The repository does not yet have a root license or a decided contributor
attestation mechanism. The copyright holder or holders have also not been
recorded. Until the repository owner resolves those questions and chooses a
Developer Certificate of Origin (DCO), a Contributor License Agreement (CLA),
or an explicitly documented alternative, external contributions may be
discussed and reviewed but must not be merged. Opening an issue does not grant
the project a license to incorporate attached code or other copyrighted
material.

This is an explicit release blocker, not template text. See
[`GOVERNANCE.md`](GOVERNANCE.md#open-governance-blockers) for the complete list
of unresolved governance decisions.

Do not use a public issue for a suspected vulnerability. Follow
[`SECURITY.md`](SECURITY.md) instead.

## Development setup

AgtXIv uses one pinned Python environment and a repository-level validation
entry point:

```bash
make bootstrap
make check
```

`make check` is the offline, fast profile used by the required continuous
integration check. The broader local profiles are:

```bash
make list-checks
make check-full
make check-nightly
```

Some full or nightly checks require the pinned Node.js or Lean toolchain. A
missing tool must be reported explicitly; it must not be treated as a passing
test. The known historical Shellworld manifest mismatch is intentionally
reported rather than silently rewritten.

## Choose the correct change path

1. Search existing issues and pull requests before starting substantial work.
2. For a user-visible change, explain the problem and the expected behavior in
   an issue or draft pull request.
3. For architecture, authority, canonicalization, security, persistence, or
   compatibility changes, add or update an Architecture Decision Record in
   `docs/adr/` before implementation becomes difficult to reverse.
4. Work on a focused branch. Codex-created branches use `codex/<topic>`; human
   contributors may use a similarly descriptive prefix.
5. Keep commits reviewable. Do not mix generated output, schema changes,
   migrations, and unrelated cleanup without explaining why they are atomic.
6. Complete the pull-request template and run the checks relevant to every
   changed layer.

## Contract and data changes

JSON Schema is the persistent contract authority for V2. A published schema,
record, release bundle, or database migration is immutable.

When changing a schema or a cross-record invariant:

- create a new exact schema version instead of replacing published bytes under
  an existing identifier;
- include positive and negative fixtures;
- update cross-record validators and stable error behavior;
- describe compatibility, migration, and rollback or supersession behavior;
- update the artifact-family coverage when the change adds or removes an
  obligation;
- preserve old records and their original meaning; and
- never promote `UNKNOWN`, `BLOCKED`, provisional, or assumed evidence during
  migration.

Database changes require an immutable migration revision, clean-database tests,
and an explicit rollback or forward-repair policy. A database migration number
is not a software, schema, or Paper Agent release version. See
[`RELEASES.md`](RELEASES.md#independent-version-axes).

## Generated artifacts

Do not hand-edit a tracked generated file. Regenerate it with the recorded
producer, run its drift check, and commit the source and generated change
together. Temporary builds, downloaded source caches, and arbitrary-paper bytes
do not belong in Git merely because a tool produced them.

Every generated artifact must follow
[`docs/governance/generated-artifacts.md`](docs/governance/generated-artifacts.md),
including its provenance, reproducibility, and arXiv-rights rules.

## Scientific and formal claims

Keep these three questions separate in code, records, documentation, and user
interfaces:

1. What does the exact paper source assert?
2. Does a formal theorem follow from the encoded assumptions in the pinned
   formal environment?
3. Is the claim scientifically applicable under the stated model, physical
   assumptions, approximations, units, and evidence?

A successful Lean build answers only the second question. It cannot silently
upgrade source alignment or scientific acceptance. Preserve limitations,
uncertainty, counterevidence, conflicts, and unresolved dependencies.

The scientific-reviewer identity, qualification, conflict-of-interest policy,
and any quorum are not yet decided. Consequently, a pull request cannot claim
to perform production scientific admission. `CODEOWNERS` approval is code
review only.

## Source material and rights

Public availability on arXiv does not by itself grant permission to redistribute
an archive, extracted tree, figure, or generated derivative. For every external
artifact:

- pin the exact source version and byte hash;
- record origin and the observed license or terms;
- record an explicit redistribution disposition and its evidence;
- keep restricted or unresolved bytes out of the public Git tree; and
- expose only policy-permitted metadata, hashes, and stable locators when bytes
  cannot be served.

Do not add secrets, personal data, confidential reviews, credentials, or private
reasoning traces. Store public rationale, evidence, findings, and
non-implications instead.

## Pull-request gates

Before requesting review:

- the exact `ci-required` status check passes;
- the working tree has no unintentional generated drift;
- tests cover success and failure paths in proportion to the change;
- schema, database, security, and rights impacts are declared;
- documentation describes visible behavior and known limitations; and
- the requested reviewers match the affected paths.

At least one code-owner approval is required on the protected default branch.
Changes affecting schemas, migrations, release policy, security controls, or
scientific admission require the specialized review described in
[`GOVERNANCE.md`](GOVERNANCE.md). Those roles may be held by different people;
no one should approve a decision for which the governing policy requires their
independence.

## Review outcomes

Review may request changes, approve code merge, or reject a proposal. Code merge
has no automatic effect on a Paper Agent package or the Knowledge Base:

- **code merge** changes the repository after code review and CI;
- **package archive** preserves an exact independently audited and mechanically
  certified Paper Agent bundle; and
- **Knowledge Base admission** is a later, per-entry scientific decision in an
  atomic transaction.

Rejected and blocked scientific candidates remain traceable. They are not
deleted merely to make a release appear complete.
