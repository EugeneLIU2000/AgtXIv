# Schema v0.3 release preparation

> **Update 2026-10-07.** This text was integrated into `main`, which is now the public line. The owner has since decided the licences (code MIT, documentation and data CC BY 4.0; [LICENSING.md](../../LICENSING.md)), the copyright holder and a DCO-based inbound policy ([governance](../../GOVERNANCE.md#resolved-governance-decisions)). The rest of this document is kept as prepared on 2026-10-05.

Date: 2026-10-05. Status: local documentation candidate; not a new published
release, tag, or validation result.

**The appropriate current publication is an experimental research-framework
preview.** Its public presentation should explain the project purpose, provide
a usable reading path, document execution prerequisites, and state exactly
what the evidence supports. A stable product or completed autonomous scientific
pipeline would exceed the present implementation and evidence.

## Publication baseline

This preparation starts from the published `schema-v0.3-framework` branch at
`b389e9c9391882b6af132b56a58eba3e072f80e5`. The local development checkout
reviewed alongside it is `11fcd99998c2fb1b2e5283d44f2e06ce9819f825`.
Static Git comparison found the same schema v0.3 host, schemas, Lean source
and STATUS document in those two snapshots. Their histories and published
artifact sets differ; the public branch includes its own English workflow
guide and deliberately excludes local run records.

The GitHub releases API returned no AgtXIv releases during this review. A
pushed branch is therefore the publication baseline, not an existing tagged
software release. These documentation changes are prepared on
`codex/schema-v03-release`, based on that public baseline. They do not import
the development branch's research archive or unrelated presentation changes.

## What the TeXRA comparison means

TeXRA provides a useful example of a clear front page: purpose, release status,
installation, first use, capabilities, requirements, documentation, support and
license. Its current `main` explicitly describes unreleased 1.0 development.
The separately published extension and CLI releases inspected here are
`v0.40.10` and `cli-v0.40.10`, dated 2026-09-06. Neither inspected GitHub release
has uploaded asset attachments; its installation channels are a separate
distribution mechanism. Sources: [pinned README](https://github.com/LionSR/TeXRA/blob/85f782e7c3dc3b47ebca70468b836c1b57b77f50/README.md),
[extension release](https://github.com/LionSR/TeXRA/releases/tag/v0.40.10),
[CLI release](https://github.com/LionSR/TeXRA/releases/tag/cli-v0.40.10).

Its release workflow also separates preview and stable channels and binds
publication to version, tag and CI conditions. That is a useful process
reference, not evidence that AgtXIv has passed those gates. See the
[pinned TeXRA workflow](https://github.com/LionSR/TeXRA/blob/85f782e7c3dc3b47ebca70468b836c1b57b77f50/.github/workflows/release.yml).

The comparison informs presentation and release discipline. AgtXIv's scope
continues to follow its own design: exact sources, explicit dependencies,
separate assessments and reusable knowledge. It does not require copying
TeXRA's editor extension, agent teams, distribution channels or license.

| Release dimension | Change prepared here | Remaining boundary |
|---|---|---|
| Purpose | English [vision](../VISION.md) connects the framework to the wider project. | Query research does not replace full-paper assessment or knowledge admission. |
| Front page | [README](../../README.md) leads with schema v0.3, its workflow, status and reading paths. | No stable-release, open-source-license or end-to-end-success badge is added. |
| Onboarding | [Getting started](../../schema%20v0.3/GETTING_STARTED.md) explains public source setup, bounded calls, outputs and recovery limits. | Fresh-checkout execution is untested; proof environment construction is still specialized. |
| Evidence | [Progress analysis](schema-v0.3-progress.md) covers major phases, components, mathematics and remaining gaps. | Local historical receipts are not a public reproducibility bundle. |
| Changes | [Release notes](schema-v0.3-notes.md) distinguish existing framework work from this documentation revision. | No version tag or release date is invented. |
| Participation | Contribution and security entry points identify the active framework and execution policy. | Existing ownership, license, review and private-intake decisions remain open. |
| Citation | [Citation guidance](../CITING.md) identifies exact repository snapshots. | Author metadata and a publication DOI are not fabricated. |

## Publication boundary

This is documentation and source-framework preparation. No runtime code,
schema identity, historical proof receipt, assessment or acceptance state is
changed by this work. Existing Chinese design and historical evidence records
remain intact; the public release reading path and new summaries are English.
The English summaries are explanatory documents, not replacement authorities.

The public baseline omits `schema v0.3/runs/` and
`schema v0.3/epoch-migration/runs/20260919-full-case/query-gap-report.json`.
Those materials include paper-source bytes or verbatim excerpts for which the
branch does not establish redistribution permission. This preparation keeps
the exclusions and adds ignore rules to discourage accidental staging of new
research output into the public framework branch.

This is a narrow boundary, **not a completed rights audit of the repository or
its Git history**. Older `Reference/`, `References/`, pilot artifacts,
presentations, vendored components and remaining migration records need their
own inventory and rights decisions before a distributable release is approved.
An ignore rule does not remove already tracked content or past commits. Do not
merge the development branch wholesale or publish a development-tree archive
as the framework package.

For any future downloadable artifact, retain its exact source commit, included
paths, exclusions, dependency identities, artifact digest and provenance. A
sanitized or synthetic example must identify its derivation and limits; it
cannot silently replace original evidence. The existing root
`release-manifest.json` belongs to an earlier pilot and must not be presented
as the schema v0.3 release manifest.

## Decisions before publication

The repository's [release policy](../../RELEASES.md) and
[governance](../../GOVERNANCE.md#open-governance-blockers) already define these
boundaries. This work records them without selecting policies on the owner's
behalf.

| Decision or gate | Why it matters | Current status |
|---|---|---|
| Release identity and content | Select the reviewed commit, publication channel and any future software tag independently of the schema number. | Proposed content is concrete; no new tag or GitHub release created. |
| License, ownership and inbound contributions | Establish the project's permissions and lawful contribution path. | Undecided; stable public software release and open-source claims remain blocked. |
| Distribution inventory | Establish which source, excerpt, vendor and evidence bytes can be distributed. | Existing v0.3 exclusions preserved; repository-wide determination remains open. |
| Authorized release checks | Establish behavior and documentation for the exact release candidate. | Not executed; affected scenarios are in the central pending-tests record. |
| Review and security intake | Establish independent review capacity and a verified confidential reporting route. | Existing governance blockers remain open. |
| Scientific review and signing | Establish production Knowledge Base admission and cryptographically signed artifacts. | Separate production outcomes remain blocked; a framework preview does not claim them. |

The pending execution record is
[`schema v0.1/PENDING_TESTS.md`](../../schema%20v0.1/PENDING_TESTS.md), including
V03-221–V03-223 for this preparation and the existing research/proof items.
No second test checklist is created here. Repository CI triggers on pushes to
`codex/**` and pull requests; publishing this working branch or opening a PR
would therefore also start checks. This preparation stops before that step
under the current no-execution instruction.

## Recommended next release step

Review this documentation candidate as a **framework preview**. Resolve the
owner-controlled publication decisions, then authorize a precise check scope
for the candidate commit, including any CI triggered by publication. Record
the resulting evidence before assigning a tag or announcing a tested release.

For scientific progress, the next milestone remains a real bounded query
proof walk with explicit source/declaration alignment and retained unresolved
premises. It is separate from publishing better documentation. The current
release language must continue to state `CHAIN_INCOMPLETE` until the relevant
evidence supports a stronger, precisely scoped claim.
