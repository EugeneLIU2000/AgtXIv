# Changelog

All notable repository changes will be recorded here. Entries describe software
and contract work; they do not imply Paper Agent archival or scientific
Knowledge Base admission.

The project intends to follow Semantic Versioning for software releases. No
stable version has been released and no historical release is reconstructed
from commit messages alone.

## Unreleased

### Project organization (2026-10-07)

- `main` now carries the whole public line: the schema v0.3 framework preview,
  the schema v0.4 work, the slide decks and the release documentation. Earlier
  branches (`codex/agtxiv-v2`, `schema-v0.3-framework`) are ancestors of it.
- Licences: code under MIT, documentation, figures, slides and data under
  CC BY 4.0, third-party material on its own terms ([LICENSING.md](LICENSING.md)).
  Contributions are accepted on the same terms with a DCO sign-off.
- Schema v0.4 added: the corpus-scale dependency-graph contracts, host, Neo4j
  projection and claim viewer, the records of the first two quant-ph runs, and a
  pinned fetch script for the arXiv metadata snapshot.
- [docs/PROJECT-STATE.md](docs/PROJECT-STATE.md) summarizes results, limits and
  the plan for collaborators.
- The sources of 20 third-party papers (`Reference/`, `References/`) left the
  repository; [docs/REFERENCES.md](docs/REFERENCES.md) lists them.
- Unpublished slide work from 2026-09-17 to 2026-09-23 is included; a
  third-party talk's recovered slides stay in the owner's local archive.
- No test, validator or build ran; the push to `main` carried `[skip ci]` at the
  owner's decision.

### Schema v0.3 research framework

The public framework baseline is `b389e9c9391882b6af132b56a58eba3e072f80e5`
on `schema-v0.3-framework`. It is a branch snapshot, not a tagged software
release. The following records the framework work already present there:

- Source-bound mathematical candidates, recursive cross-paper matching,
  query-focused AND/OR graphs and persistent execution accounting.
- Frozen model routing, incremental reuse, compact graphs and label-specific
  queries with separate support and mention records.
- Library-root audits, bottom-up proof-worker interfaces, statement-triviality
  probes, human-review records and conditional chain-certificate machinery.
- Lean source for the separately constructed query branch, with historical
  common-environment compilation described in retained reports.
- PDF-region, recovery and amendment interfaces with remaining execution gaps.

Release preparation dated 2026-10-05 adds English vision, onboarding, progress,
release and citation guides; replaces the stale root entry point; corrects
workflow instructions; and updates contribution/security scope. Public archive
exclusions are documented and added to the branch's ignore rules. No runtime
code, contract identity or historical evidence is changed by this preparation.

The recorded case remains `CHAIN_INCOMPLETE`, with zero accepted support edges,
unreviewed source alignment and no completed autonomous query-graph proof.
No new checks ran. See [draft release notes](docs/releases/schema-v0.3-notes.md)
and [the release boundary](docs/releases/schema-v0.3-release.md).

### Earlier V2 infrastructure

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

- The root license, copyright holder and inbound contribution mechanism were
  decided on 2026-10-07 (see Project organization above).
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
