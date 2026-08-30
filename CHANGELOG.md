# Changelog

All notable repository changes will be recorded here. Entries describe software
and contract work; they do not imply Paper Agent archival or scientific
Knowledge Base admission.

The project intends to follow Semantic Versioning for software releases. No
stable version has been released and no historical release is reconstructed
from commit messages alone.

## Unreleased

### Added

- The audited V2 end-to-end roadmap, M0 architecture decision records,
  historical baseline audit, and threat model.
- A locked Python 3.12 environment, pinned Node version, `make` entry points,
  and the offline aggregate repository validator with explicit
  `KNOWN_STALE`/`EXPECTED_BLOCKED` states.
- Pull-request CI with immutable action pins and Pages deployment gated on the
  exact commit that passed `ci-required`.
- M0 contribution, security, governance, release, generated-artifact, and
  repository-settings policies.
- Default code-review routing and a pull-request evidence template.
- Explicit separation of code merge, Paper Agent package archive, and per-entry
  Knowledge Base admission.
- Independent software, contract, schema, database, paper-source, Paper Agent,
  environment, knowledge-view, and API version axes.

### Known blockers

- The root license and copyright holder or holders are undecided.
- The inbound contribution mechanism (DCO, CLA, or an explicit alternative) is
  undecided.
- Scientific-reviewer identity, qualification, independence, quorum, and
  attestation are undecided.
- The production signature suite, key custody, trust roots, rotation, and
  revocation policy are undecided.

These blockers prevent claims of stable open-source readiness, production signed
Paper Agent releases, and production independently reviewed Knowledge Base
admission. They are not release-note placeholders.

## Changelog rules

- Move `Unreleased` entries under an exact version and date only when that
  software release is actually published.
- Use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security` as
  applicable.
- Link schema and database compatibility notes to their exact versions and
  migration revisions.
- Record breaking changes, data migrations, superseded artifacts, and known
  limitations explicitly.
- Keep embargoed vulnerability details private until coordinated disclosure is
  safe; then add a concise `Security` entry and advisory link.
