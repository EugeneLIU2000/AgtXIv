# AgtXIv governance

## Purpose

This document governs repository decisions and the separation of authority in
AgtXIv V2. It does not grant a copyright license and does not replace the
normative scientific and machine-contract specifications.

The remote repository is administered by `@EugeneLIU2000`, who is therefore the
default code-review route in `CODEOWNERS`. Repository administration does not by
itself establish copyright ownership, scientific-review qualification, or
release-signing authority.

## Governing principles

1. Exact records and released bytes are immutable; corrections use new revisions
   and explicit supersession.
2. Source fidelity, formal validity, and scientific applicability are separate
   judgments.
3. A producer cannot satisfy an independent review role for its own output.
4. Unknown, blocked, failed, rejected, and conflicting results remain visible.
5. Public rationale, evidence, uncertainty, and non-implications are recorded;
   private chain-of-thought is neither requested nor stored.
6. A query may trigger work but cannot narrow a canonical whole-paper scope.
7. Legal permission, cryptographic integrity, code quality, and scientific
   acceptance are different gates.

## Three independent state changes

| State change | Object changed | Required authority | What it does not imply |
|---|---|---|---|
| Code pull-request merge | Git repository | Code owner, relevant specialist reviewers, and `ci-required` | No paper was audited, archived, or scientifically accepted. |
| Paper Agent package archive | Immutable replay bundle and archive receipt | V2 Root Agent audit followed by an independent mechanical certifier and archive service | No package entry was admitted to reusable knowledge. |
| Knowledge Base admission | Exact domain snapshot and admission receipt | Independent per-entry scientific review plus policy-computed atomic transaction | No whole-paper truth claim and no deletion of rejected or conflicting entries. |

These state changes use different records and must never be collapsed into one
“approved” flag. A mixed-status package may be archived while admitting zero
entries.

## Roles

### Repository owner and maintainers

The repository owner controls GitHub administration. Maintainers triage issues,
review code, protect release processes, and document decisions. They may
delegate a role in a versioned policy. A GitHub permission alone does not grant
scientific or cryptographic authority.

### Code owner

A code owner reviews correctness, maintainability, tests, compatibility, and
repository policy for a changed path. `CODEOWNERS` routes pull requests; it is
not an authorship statement or a scientific-admission roster.

### Contract and migration reviewer

Changes to canonicalization, JSON Schemas, cross-record validators, artifact
catalogs, database migrations, or compatibility adapters require a reviewer who
checks immutability, versioning, positive and negative fixtures, migration
behavior, and status non-promotion.

### Security and rights reviewer

Security-sensitive changes require threat-model and regression-test review.
Source redistribution or model-use decisions require exact rights evidence and
a rights disposition. Neither role may infer permission merely from public
availability.

### Agentization Coordinator

The Coordinator schedules producers and assembles a candidate manifest. It has
no authority to audit, certify, archive, or admit its own output.

### V2 Root Agent

The Root Agent performs the accountable, ordered paper-level audit over exact
artifacts and their unresolved frontier. It does not generate evidence it then
audits and does not mechanically certify or publish its own package.

### Release Certifier

The certifier checks exact bindings, policy conformance, role separation, and
the Root Agent recommendation. It is mechanical and cannot change scientific
judgment or unresolved frontier.

### Scientific admission reviewer

The scientific reviewer assesses one exact candidate entry, its source and
formal evidence, assumptions, approximation, physical applicability,
uncertainty, and conflicts. Code approval does not grant this role. The identity,
qualification, conflict-of-interest rules, quorum, and attestation for this role
remain unresolved; production admission is blocked until they are adopted.

## Pull-request decisions

Normal code changes require the protected-branch settings in
[`docs/governance/repository-settings.md`](docs/governance/repository-settings.md).
The following changes also require an Architecture Decision Record and explicit
specialist approval:

- authority boundaries, role independence, or review policy;
- canonical serialization, hashing, signatures, or trust policy;
- schema compatibility, database immutability, migration, or admission
  transaction semantics;
- source acquisition, sandbox, external network, credentials, or rights policy;
- release, archive, withdrawal, revocation, or supersession behavior; and
- any change that may promote or suppress scientific status, conflict, or
  unresolved evidence.

Review decisions must cite public evidence and affected exact versions. A stale
approval is dismissed after relevant bytes, contracts, policy, environment, or
scope change.

## Conflict of interest and separation of duties

The exact, versioned D7 separation matrix is the authority for every decision.
At minimum, the producer of an assessed candidate, V2 Root Agent auditor,
Release Certifier, and scientific admission reviewer are pairwise distinct for
that candidate. The Agentization Coordinator is distinct from the Root Agent and
Certifier. A scope-freeze reviewer is distinct from the discovery producer and
from every additional actor forbidden by the applicable freeze policy. A policy
may require stronger separation, but it cannot weaken these minima. If required
identity, independence, conflict, or qualification evidence is absent, the
decision is blocked; another reviewer is selected or no final state is created.

No role may bypass a failed gate by editing the result record, deleting a
frontier item, or relabeling a code review as a scientific review.

## Open governance blockers

The following are real unresolved decisions as of 2026-08-31. They have no
placeholder defaults.

| Blocker | Decision still required | Blocked outcome |
|---|---|---|
| Root license | Select and add the actual repository license after rights review. | The repository must not call itself open source or claim that the public may reuse, modify, or redistribute the code. A stable public software release is blocked. |
| Copyright ownership | Identify the copyright holder or holders and the treatment of existing contributions. | Copyright notices and relicensing authority cannot be asserted. |
| DCO, CLA, or alternative | Choose the Developer Certificate of Origin, Contributor License Agreement, or another explicit inbound-contribution policy. | External contributions may be reviewed but must not be merged without a documented lawful acceptance path. |
| Independent code-review capacity | Appoint at least one additional qualified code owner and the required specialist reviewers, then test the resulting ruleset. | The full target branch-protection rules cannot be enabled without deadlocking owner-authored changes or silently waiving independent specialist review. |
| Verified private security intake | Enable and verify private vulnerability reporting, or publish and verify another confidential channel controlled by the project. | `SECURITY.md` cannot promise confidential intake; undisclosed vulnerabilities may have no safe project contact. |
| Scientific reviewer policy | Name or define the qualified reviewer pool, identity verification, conflicts, quorum, evidence standard, appeal, and attestation. | Production scientific admission and claims of reviewed Knowledge Base content are blocked. |
| Signature mechanism | Decide the canonical signed payload, algorithm, key custody, role authorization, trust roots, historical validation, rotation, expiry, compromise, and revocation. | Production cryptographically certified Paper Agent releases and signed software artifacts are blocked. Hash-only fixtures must not be described as signed. |

Only the repository owner or a formally delegated maintainer may merge the
change that closes one of these blockers. For a license, copyright, or inbound-
contribution decision, repository administration is not sufficient: the actual
rights holder or holders, or their documented authorized representative, must
supply the required authority. Every closing change must contain the actual
decision, evidence, and effective version. Removing the table without resolving
the decision does not unblock anything.

## Amendments and disputes

Governance changes use a pull request, public rationale, code-owner review, and
the relevant specialist review. Security-sensitive discussion may begin in a
private advisory, with a public decision recorded when disclosure is safe.

Disputed code decisions may be reconsidered by the repository owner with the
reasons recorded. A scientific rejection or conflict is handled by a new
immutable assessment or appeal record under the applicable future policy; it is
not resolved by rewriting the original assessment.
