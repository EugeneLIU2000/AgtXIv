# AgtXIv

**Trace scientific claims through their sources, assumptions and proof dependencies.**

AgtXIv develops auditable Paper Agents and reusable scientific knowledge. The
aim is to let each new investigation build on earlier evidence while keeping
its sources, conditions, disagreements and unfinished work visible. Read the
[project vision](docs/VISION.md) for the wider direction.

The research line has two current rungs:

- **schema v0.3**, an experimental framework that takes one query claim of one
  arXiv paper, extracts mathematical claim candidates, follows dependencies
  across papers, selects the query's upstream branch, and attempts Lean 4
  formalization from the bottom up;
- **schema v0.4** (in development), its corpus-scale successor: one dependency
  graph over a random sample of papers, built so that "which results do many
  papers rest on" becomes a measurement. Its first real runs, on 50 random
  quant-ph papers, are recorded with their limits.

**Where the project stands and what is planned:** [project state](docs/PROJECT-STATE.md).

**Release status:** public framework preview, with no tagged software release.
The recorded case remains `CHAIN_INCOMPLETE`. There is no completed autonomous
paper-to-proof run, and source alignment remains unreviewed. See the
[progress analysis](docs/releases/schema-v0.3-progress.md) and
[release scope](docs/releases/schema-v0.3-release.md).

[Project state](docs/PROJECT-STATE.md) ·
[Workflow](schema%20v0.3/WORKFLOW.md) ·
[Getting started](schema%20v0.3/GETTING_STARTED.md) ·
[Schema v0.4](schema%20v0.4/README.md) ·
[Evidence and limits](docs/releases/schema-v0.3-progress.md) ·
[Contributing](CONTRIBUTING.md)

## What the framework does

| Stage | What it produces |
|---|---|
| Freeze sources | Exact paper versions and source locations, with content identities and acquisition records. |
| Extract and connect | Candidate statements, internal dependencies and cross-paper matches; citations that only mention a work remain separate from support. |
| Select a query | A bounded upstream graph, with joint premises, alternative routes, unresolved roots and explicit blockers. |
| Attempt formalization | Library-search records and scheduled model-to-Lean attempts, with the actual formal types, premises and proof dependencies. |
| Retain the evidence | Plans, model receipts, budgets, checkpoints, review records and conditional chain-certificate machinery. |

Models propose candidates. The host program derives states and enforces gates.
Exploration does not accept a claim, and a compiled theorem does not establish
that its statement faithfully represents a paper. These boundaries are part of
the [schema v0.3 design](docs/superpowers/specs/2026-09-19-schema-v03-design.md).

## Start here

You can read the [workflow](schema%20v0.3/WORKFLOW.md) and
[progress analysis](docs/releases/schema-v0.3-progress.md) without installing
anything. The public `main` branch contains framework code and documentation;
historical research receipts and paper-source files remain in a local archive
and are not included in a public checkout.

For a source checkout:

```sh
git clone https://github.com/EugeneLIU2000/AgtXIv.git
cd AgtXIv
```

The repository pins Python 3.12.2 and uv 0.10.0. With that uv version
available, `uv sync --locked --no-default-groups --python 3.12.2` installs the
locked runtime environment. [Contributor setup](CONTRIBUTING.md#development-setup)
also installs development dependency groups. This is a source-checkout
workflow; no published `pip` package or standalone AgtXIv command is claimed.

The [getting-started guide](schema%20v0.3/GETTING_STARTED.md) explains the
separate prerequisites for live research and Lean work. Research can call a
model using the configured Codex CLI account; source downloads require an
explicit option. A proof walk requires a prepared, frozen Lean environment
and request. Read the guide before starting a run.

## What the existing evidence supports

The following are **historical results reported in the retained local
records**, summarized in [STATUS.md](schema%20v0.3/STATUS.md). They are not
fresh validation of this release preparation or a public replay bundle.

| Recorded result | Its boundary |
|---|---|
| Recursive investigation across four papers: 240 target-paper candidates, 683 graph nodes and 269 support groups. | Accepted support edges remain **0**; the counts do not establish complete extraction or correctness. |
| Single-theorem scheduling reaches 5 attempts on the target graph and 6 after an upstream join. | This demonstration used a stub that called neither a model nor Lean. |
| One real single-node model-to-Lean proof attempt succeeded. | No real proof-worker walk over an entire query graph has completed. |
| A 60-module Lean branch compiled in one common environment; 54 selected declarations were audited. | An agent wrote and repaired it. Its terminal theorem is not bound to the graph query, and source alignment is unreviewed. |

A chain certificate concerns a formal implication under its listed premises.
It does not certify a paper's truth, the applicability of a physical model or
the existence of instances satisfying every premise. The wider project keeps
[six assessment axes separate](docs/VISION.md#six-questions-remain-separate).

## Documentation

| I want to understand… | Read |
|---|---|
| Where the project stands: results, limits and plan | [Project state](docs/PROJECT-STATE.md) |
| The project purpose and the role of this version | [Vision](docs/VISION.md) |
| The three-stage research workflow | [Workflow](schema%20v0.3/WORKFLOW.md) |
| Requirements, commands, outputs and limitations | [Getting started](schema%20v0.3/GETTING_STARTED.md) |
| All major v0.3 changes and their evidence | [Progress analysis](docs/releases/schema-v0.3-progress.md) |
| Release contents, TeXRA comparison and remaining decisions | [Release preparation](docs/releases/schema-v0.3-release.md) |
| Graph semantics, model routing and proof execution | [Schema implementation map](schema%20v0.3/README.md) |
| What changed for this preview | [Release notes](docs/releases/schema-v0.3-notes.md) and [changelog](CHANGELOG.md) |
| The corpus-scale successor and its first runs | [Schema v0.4](schema%20v0.4/README.md) and its [design](docs/superpowers/specs/2026-09-25-schema-v04-design.md) |
| The papers the project studies (not distributed here) | [References](docs/REFERENCES.md) |
| What you may reuse, and on which terms | [Licensing](LICENSING.md) |

## Repository map

- [`schema v0.3/`](schema%20v0.3/README.md): the published research framework,
  JSON contracts, host code, Lean modules and technical documentation.
- [`schema v0.4/`](schema%20v0.4/README.md): the corpus-scale dependency graph in
  development: contracts, host code, Neo4j projection, a claim viewer and the
  records of its first runs.
- [`schema v0.0/`](schema%20v0.0/README.md),
  [`schema v0.1/`](schema%20v0.1/README.md) and
  [`schema v0.2/`](schema%20v0.2/README.md): earlier contract work, interpreted
  under their original scope.
- [`formal/`](formal/) and [`Stabilizerness/`](Stabilizerness/): earlier
  mathematical projects and pilot artifacts used by the research line.
- [`web/`](web/README.md): a separate V3 reader and source-intake service;
  its results do not demonstrate completion of the v0.3 proof workflow.
- [`docs/`](docs/): design, governance, release documentation and historical
  records. [`AgtXIv.md`](AgtXIv.md) remains the broader V3 design entry point.

Schema version, protocol version and software release version are independent.
`research/0.3.0` is a contract-family identity, not a software release tag.
See the [version policy](RELEASES.md).

## Development and participation

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes. Under the
current [repository policy](AGENTS.md), tests, validators, example replays and
Lean builds require explicit user authorization. New or affected scenarios
belong in the single [pending-tests record](schema%20v0.1/PENDING_TESTS.md).
Historical successful runs are not evidence that a new revision passed.

Use [GitHub issues](https://github.com/EugeneLIU2000/AgtXIv/issues) for ordinary
questions and bug reports. Include the exact commit, expected behavior and
minimal shareable context. Follow [SECURITY.md](SECURITY.md) for sensitive
reports. [Citing this work](docs/CITING.md) explains how to identify a snapshot
without inventing a publication or DOI.

## License and project authority

Code is licensed under the [MIT License](LICENSE); documentation, figures,
slides and data under [CC BY 4.0](LICENSE-docs). Third-party material keeps its
own terms: vendored web components, excerpts of other people's papers, and the
papers listed in [References](docs/REFERENCES.md), which are not distributed
here. [LICENSING.md](LICENSING.md) gives the scope. Contributions are accepted
on the same terms with a Developer Certificate of Origin sign-off
([CONTRIBUTING.md](CONTRIBUTING.md#licensing-of-contributions)). The owner made
these decisions on 2026-10-07 ([governance](GOVERNANCE.md#resolved-governance-decisions));
other governance questions stay [open](GOVERNANCE.md#open-governance-blockers).

The [Charter](CHARTER.md) remains a pending proposal under
[ADR 0007](docs/adr/0007-adopt-project-charter.md). This preview neither ratifies
it nor changes the authority of historical records.
