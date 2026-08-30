# Security policy

AgtXIv processes untrusted paper archives, TeX, PDFs, bibliographies, images,
metadata, and generated formal code. A paper or generated artifact is data; it
must never acquire network, credential, review, signing, or Knowledge Base write
authority.

The detailed V2 threat model is in
[`docs/security/v2-threat-model.md`](docs/security/v2-threat-model.md).

## Supported versions

There is no production or stable software release yet. Security reports about
the current `main` branch and the active V2 development line are accepted on a
best-effort basis. Historical commits, local research artifacts, and abandoned
branches do not receive a support guarantee.

This table will be replaced with explicit release ranges when the first public
software release is made.

| Version | Security support |
|---|---|
| `main` and active V2 pre-release work | Best-effort during development |
| Historical snapshots and unmaintained branches | Not supported |

## Planned private reporting channel

The intended channel is a [private GitHub security advisory](https://github.com/EugeneLIU2000/AgtXIv/security/advisories/new),
but this repository has not yet recorded evidence that private vulnerability
reporting is enabled and reachable. If GitHub presents the private report form,
use it. If it does not, do not put an undisclosed vulnerability, exploit, secret,
or restricted byte in a public issue or pull request. The project currently has
no verified confidential fallback; enabling and testing one is an explicit M0
governance blocker in `GOVERNANCE.md`.

Include, when available:

- the affected commit, component, and configuration;
- a minimal reproduction that does not contain secrets or restricted paper
  bytes;
- expected and observed behavior;
- security impact and plausible attack path;
- whether the issue has been disclosed elsewhere; and
- any suggested mitigation.

Never send live credentials, private keys, personal data, or content that you
are not permitted to share. Replace them with exact digests or a minimal
synthetic fixture.

## What to report

Examples include:

- archive traversal, symlink or hardlink escape, archive bombs, unsafe TeX/PDF
  execution, or sandbox escape;
- server-side request forgery, redirect or version confusion, unexpected
  outbound network access, or prompt-driven tool use;
- credential exposure, authorization bypass, role confusion, forged review,
  stale certification, or signature-validation errors;
- content-addressed storage, canonical-hash, release-bundle, or provenance
  substitution;
- append-only database violations, cross-domain data exposure, non-atomic
  admission, or conflict suppression;
- unauthorized distribution of restricted source bytes or sending them to an
  unapproved model provider; and
- dependency, workflow, build, or release supply-chain compromise.

A disagreement about a paper's scientific conclusion is normally a scientific
review matter, not a security vulnerability. Report it as security-sensitive
when an attacker can use it to bypass an authority boundary, forge evidence, or
obtain an unauthorized release or admission state.

## Response process

Maintainers will acknowledge and triage reports as capacity permits. No fixed
response or remediation service-level agreement is claimed during the
pre-release phase. The response should:

1. reproduce and scope the issue without exposing restricted data;
2. identify affected immutable releases, records, snapshots, or keys;
3. contain active exploitation and disable unsafe byte serving where needed;
4. develop a fix and regression test on a private branch;
5. append revocation, withdrawal, tombstone, or supersession records rather than
   rewriting released history; and
6. coordinate disclosure after affected users have a practical mitigation.

Credit is offered when the reporter wants it and disclosure is safe. The project
does not currently promise a bounty.

## Security-sensitive release blockers

The production signature mechanism is undecided. The project has not selected
the signed payload, algorithm, key custody, actor-to-key authorization, trust
roots, historical verification rule, rotation process, or compromise and
revocation procedure. Current hashes and mechanical certificate fixtures are
integrity contracts; they are not a claim of deployed cryptographic signing.

Production signed Paper Agent releases and production admission therefore remain
blocked until that decision is reviewed, implemented, and tested. The root
license, copyright ownership record, contributor attestation mechanism, and
scientific-reviewer identity policy are separate unresolved governance blockers
listed in [`GOVERNANCE.md`](GOVERNANCE.md#open-governance-blockers).

## Safe research practices

- Keep acquired archives in quarantine until bounded extraction and validation
  succeed.
- Run parsing, TeX, PDF, model output, and formal builds without external
  network access and with CPU, memory, file-count, byte, and time limits.
- Give acquisition workers no signing, review, archive-admission, or knowledge-
  write credentials.
- Keep secrets out of logs, fixtures, bundles, generated sites, and browser
  payloads.
- Verify exact bytes, canonical hashes, roles, policy revisions, and environment
  bindings before trusting a record.
- Treat rights to inspect metadata, process bytes, redistribute bytes, and send
  bytes to a hosted model as four distinct permissions.
