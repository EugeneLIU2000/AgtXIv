# Schema v0.3 research framework preview notes

Status: draft release text prepared on 2026-10-05. No software version tag or
new GitHub release has been created. Contract family: `research/0.3.0`.

AgtXIv schema v0.3 develops a source-grounded workflow for following the
dependencies of mathematical claims and attempting conditional Lean proofs.
Its stages are forward source research, backward query selection and
bottom-up formalization. Models propose candidates; host programs preserve
source identities, derive states, control budgets and retain evidence.

## Framework capabilities in the public baseline

- Exact-version source ingestion, source-bound candidate extraction, internal
  references and explicit cross-paper matching requests.
- Recursive paper admission, joint premises and alternative routes,
  query-focused pruning, compact graphs and unresolved-frontier records.
- Persistent plans, budgets, model-call receipts and incremental evidence
  reuse with frozen operation-specific model routing.
- A separate proof scheduler and model-to-Lean worker, library-root searches,
  statement-triviality probes, declaration and premise extraction, and
  direct proof-term composition evidence.
- Human-review records and conditional chain-certificate machinery, with
  distinct boundaries for source alignment and premise satisfiability.
- PDF source-region, matching, recovery and amendment interfaces, some still
  awaiting recorded execution.

These capabilities were already present in the public baseline
`b389e9c9391882b6af132b56a58eba3e072f80e5`. This release preparation adds an
English front page, vision overview, onboarding, progress analysis, citation
guidance and release boundaries. It also corrects workflow instructions and
aligns contribution and security documentation with the active framework.
It introduces no new runtime behavior or schema migration.

## Evidence and limits

Retained local records describe a four-paper investigation with 240 target
candidates, 683 graph nodes and 269 support groups. Accepted support edges
remain zero. One real single-node model-to-Lean result exists. A separate
60-module branch compiled in a common Lean environment, with 54 selected
declarations audited; agents wrote and repaired that branch.

The single-query scheduling demonstration used a stub backend. No completed
autonomous proof-worker run over a real query graph is demonstrated. The
compiled branch's terminal declaration is not bound to the graph query;
source alignment is unreviewed. Earlier successful checks apply to their
recorded snapshots and were not rerun for this preparation.

The framework remains `CHAIN_INCOMPLETE`. A certificate, when emitted within
its stated scope, expresses a formal implication conditional on listed
premises. It does not establish whole-paper truth, scientific applicability
or admission to a reviewed knowledge base. See the
[progress analysis](schema-v0.3-progress.md) for exact scopes.

## Requirements and compatibility

Use a source checkout with the repository's Python 3.12 environment and
uv 0.10.0. Live research additionally needs a compatible authenticated Codex
CLI and access to the models selected by the frozen profile. The controller
uses POSIX file locking. Generated Lean execution currently requires the
macOS sandbox and a separately prepared compatible Lean environment.

The historical common-environment result used Lean v4.33.0 and Physlib's
mathlib revision `db584cd6`; it is not a universal toolchain declaration for
every older formal project. Do not combine environment receipts from
different epochs. Read [getting started](../../schema%20v0.3/GETTING_STARTED.md)
before attempting fresh research or proof work.

The schema contract ladder is separate from historical protocol versions and
the Python metadata version `2.0.0.dev0`. Existing records keep their original
contracts and provenance. This documentation revision does not migrate data,
alter frozen plans or make old run profiles portable.

## Distribution and participation

The public framework omits the local `schema v0.3/runs/` archive and one
quotation-bearing migration report. Historical counts are therefore reported
results, not an independently replayable public evidence package. Source
acquisition and account-backed model execution are explicit user actions.

The root license, copyright ownership and inbound-contribution mechanism
remain undecided. This preview is not a claim of stable open-source readiness.
See [release preparation](schema-v0.3-release.md), [contributing](../../CONTRIBUTING.md)
and [security](../../SECURITY.md) before publication or participation.

No tests, validators, example replays, model calls or Lean builds were executed
for this preparation. Affected scenarios remain in the single
[pending-tests record](../../schema%20v0.1/PENDING_TESTS.md).
