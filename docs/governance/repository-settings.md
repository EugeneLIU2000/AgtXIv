# Required repository settings

## Status and scope

This file specifies the target GitHub settings for AgtXIv. It is not evidence
that the settings are currently enabled. The repository owner must verify them
in GitHub and record dated evidence before M0 governance is called complete.

`CODEOWNERS` and branch rules govern code changes only. They do not designate a
scientific reviewer, perform a V2 Root Agent audit, certify a package, or admit a
Knowledge Base entry.

## Default branch

Set `main` as the default branch and protect it with a branch ruleset:

- require a pull request before merge;
- require at least one approving review;
- require review from `CODEOWNERS` for owned paths;
- dismiss stale approvals when new commits change reviewed bytes;
- require approval after the most recent push by someone other than the pusher;
- require all review conversations to be resolved;
- require the exact status check **`ci-required`**;
- block force pushes and branch deletion;
- apply the rules to administrators and disallow routine bypass;
- retain a linear, auditable history; and
- require the branch to be up to date, or use a merge queue, once either mode has
  been tested with the aggregate check.

The aggregate `ci-required` job must fail when any required M0 job fails or is
cancelled. Branch protection should require that stable aggregate name rather
than coupling policy to every internal matrix job.

If an emergency bypass is technically unavoidable, the repository owner records
who used it, why, the exact commit, the failed or skipped controls, remediation,
and a follow-up pull request. A bypass cannot create a scientific release or
admission decision.

## Merge and branch policy

- Development occurs on short-lived topic branches, including `codex/<topic>`
  for Codex work.
- Prefer squash merge for a pull request whose internal commits are not each
  independently meaningful; preserve separate commits when they are deliberate
  migration or provenance boundaries.
- Disable merge commits if the chosen history policy requires linear history.
- Automatically delete merged topic branches where recovery remains available
  through Git history.
- Do not reuse a protected release tag or published version name.

External pull requests remain subject to the unresolved license and inbound-
contribution decision in `GOVERNANCE.md`. Technical approval does not cure that
legal blocker.

## Review routing

The default code owner is `@EugeneLIU2000`, derived from the repository remote.
The same account currently routes specialist paths until additional maintainers
are formally appointed. This single-owner file is only an honest routing
baseline: combined with required code-owner review and approval-after-last-push,
it would deadlock an owner-authored pull request and cannot supply independent
specialist review. Do not mark the target ruleset implemented until at least one
additional qualified code owner and the necessary specialist reviewers are
appointed, documented, and tested. Add teams or individuals only after their
scope and authority are documented.

For high-risk changes, repository settings must make these reviews non-bypassable
where GitHub supports it:

| Path or change | Required review concern |
|---|---|
| `.github/`, `SECURITY.md`, `docs/security/` | Workflow permissions, secrets, supply chain, disclosure, and threat model |
| `schemas/`, validators, canonicalization profiles | Contract compatibility, exact hashes, positive and negative fixtures |
| `database/`, migrations, admission code | Append-only behavior, atomicity, upgrade and recovery |
| release, archive, signature, or policy code | Role separation, exact binding, trust and revocation |
| generated outputs and their producers | Determinism, provenance, drift and rights disposition |

The future scientific-reviewer roster must not be implemented by adding a name
to `CODEOWNERS`. It needs its own identity, qualification, conflict, quorum, and
attestation policy.

## Actions and deployment

- Set the default GitHub Actions token permission to read-only.
- Grant write permissions only to the specific job that needs them.
- Do not expose repository or environment secrets to untrusted pull requests.
- Pin third-party actions to full commit hashes and review updates.
- Permit only required actions and reusable workflows.
- Configure concurrency so a superseded build cannot publish after a newer one.
- Build deployment artifacts from the exact commit that passed CI, not from a
  later mutable branch head.
- Protect production environments and Pages deployment with explicit branch and
  workflow restrictions.
- Keep acquisition, model-gateway, release-signing, and Knowledge Base
  credentials in distinct environments with least privilege.

The current Pages workflow is documentation/demo deployment. A successful Pages
deployment is not a software release, Paper Agent archive, or scientific
admission.

## Repository security features

Enable and monitor, where available:

- private vulnerability reporting and GitHub Security Advisories;
- dependency graph and dependency-update alerts;
- secret scanning and push protection;
- code scanning for the supported languages;
- protected tags for software and contract release namespaces; and
- immutable release-asset or external provenance retention appropriate to the
  future signing policy.

Private vulnerability reporting must be opened in an unauthenticated or test
reporter session and its successful confidential routing recorded. Until that
evidence exists, the advisory URL in `SECURITY.md` is a planned channel, not an
availability promise. If GitHub cannot supply it, the repository owner must
publish and verify another confidential channel before M0 governance completes.

Automated findings require triage. Enabling a checkbox is not evidence that a
vulnerability is fixed.

## Verification record

Before declaring these settings enforced, capture a dated, non-secret record
containing:

- repository and default branch;
- ruleset identifier and exported settings or screenshots;
- required status-check name;
- required review count and stale-review behavior;
- force-push, deletion, bypass, and administrator settings;
- Actions default permissions and allowed-action policy;
- enabled security features;
- protected environments and tag patterns; and
- verifier identity and review date.

The record must list any setting unavailable on the current GitHub plan as a
named residual blocker with a compensating control. It must not mark an intended
setting as active without evidence.
