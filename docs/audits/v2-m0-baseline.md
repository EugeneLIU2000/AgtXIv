# AgtXIv V2 M0 baseline audit

- Audit document status: Accepted
- M0 exit status: NOT COMPLETE
- Document type: historical baseline audit
- Milestone: M0
- Observation date: 2026-08-30
- Recorded date: 2026-08-31
- Roadmap decisions: D1-D10
- Scope: repository state inspected for the V2 end-to-end implementation plan
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## 1. Executive finding

The repository does **not** start from zero. It has a healthy V2 contract slice,
substantial V1 mathematical and provenance machinery, three Lean projects with
recorded outputs, and polished static visualizations. It does not yet have the
production path that accepts an arbitrary supported arXiv input and constructs a
complete V2 replay bundle, durable review transaction, database projection, and
live web view.

The most important interpretation is that the green checks observed in this
historical snapshot establish different scopes:

- `234 passed` records the initial dirty-worktree Python observation; it is not
  a clean, commit-defined test baseline;
- 12 schemas and 13 V2 records establish one cross-record contract fixture;
- RootMath's 43 declarations and Varela's 6 declarations establish the audited
  mathematical interfaces in those pinned Lean projects;
- none of those facts establishes whole-paper scientific acceptance or the
  completion of the arbitrary-paper V2 pipeline.

This audit is a historical baseline, not a release certificate. The M0
execution checkpoint has partially superseded its operational snapshot, and
future immutable reports may supersede it further, but they must not edit these
observations to make later checks appear retroactively green.

## 2. Environment observed

| Item | Observation | M0 disposition |
|---|---|---|
| System `/usr/bin/python3` | Python 3.9.6 | Unsupported for V2 target runtime; do not use as the reproducible project interpreter. |
| Repository-capable Python | `/opt/anaconda3/bin/python`, Python 3.12.2 | Used for the Python baseline; M0 must replace the machine-specific path with locked project metadata and one bootstrap command. |
| Target runtime | Python 3.12 or newer | Frozen by roadmap Section 5.1. |
| Formal toolchains | Project-local Lean toolchain/manifests | Keep pinned and independently rebuilt; build success remains separate from source alignment and scientific acceptance. |

The mismatch matters because a passing workstation command is not yet a clean
checkout recipe. M0 exits only after a Python 3.12+ environment can be reproduced
from versioned project metadata and locked dependencies.

## 3. Checks and results

| Area | Baseline command or evidence | Result | Meaning and limit |
|---|---|---|---|
| Full Python suite | `/opt/anaconda3/bin/python -m pytest -q` | **PASS: 234 passed** | The observed dirty-worktree suite passed in the repository-capable environment; this is not a locked clean-checkout result. |
| V2 contract slice | `/opt/anaconda3/bin/python tools/validate_v2_paper_agentization.py` | **PASS: 13 JSON records / 12 schemas** | Validates the current mixed-disposition paper-agentization fixture and cross-record invariants; does not prove whole-paper producer coverage. |
| ScientificClaim | `tools/validate_scientific_claims.py` plus its tests | **PASS** | V1 claim structures are reusable inputs, not V2 whole-paper authority. |
| Claim DAG | `tools/validate_claim_dag.py` | **PASS** | Validates the existing graph contract; its Oracle/candidate edges are not thereby accepted scientific dependencies. |
| Pilot | `tools/validate_pilot.py` | **PASS** | Pilot structure passes while published scientific blockers remain intentional. |
| Root partitions | `tools/validate_root_partitions.py` | **PASS** | Preserves distinct mathematical, semantic, and blocker routes. |
| Claim-interface study | `tools/validate_claim_interface_study.py` plus tests | **PASS** | Research/fixture validation, not a production V2 producer. |
| Semantic-contribution study | `tools/validate_semantic_contribution_study.py` plus tests | **PASS** | Research fixtures remain explicitly non-production evidence. |
| Database prototype | `database/scripts/validate_database.py` | **PASS (structural)** | The Git/SQLite prototype is reusable design input; it is not the D1 PostgreSQL transaction authority. |
| RootMath dynamic Lean validator | `python3 tools/validate_lean_formalization.py` | **PASS: 43 declarations** | Clean build, placeholder scan, and declaration-level axiom audit passed for the selected Root mathematical interfaces; scientific acceptance effect is none. |
| Varela dynamic Lean validator | `python3 tools/validate_varela_formalization.py` | **PASS: 6 declarations** | Clean build, placeholder scan, and axiom audit passed for a conditional/local interface; source repair premises and scientific acceptance remain open. |
| Static Pages build and validation | repository site build plus `tools/validate_pages_site.py` | **PASS** | Current static site is internally valid; it publishes the older V1 MathContract experience, not the complete V2 workflow. |
| Shellworld query run | `/opt/anaconda3/bin/python agents/bouncing-shellworld-charged-ads/queries/query-001/validate_run.py` | **INTENTIONAL FAIL: `run_manifest_hashes_and_self_hash`** | Shows a mutable specification-path binding defect; all other observed run checks passed. Preserve and supersede, do not rewrite. |

## 4. Shellworld immutable-manifest mismatch

The historical run manifest records:

```text
path: docs/specifications/v1-bridge.md
expected sha256: c9c7b46732d56c862f77b64304b5a24f312b36386e643f0c204949c426cd6b54
current sha256:  0c8fcd49dca17c0f6f547182cc6143c466d90a343b9703bd0aaec67690233d13
```

This is evidence for ADR 0002. The old manifest must remain unchanged. A valid
resolution is either to recover the exact expected specification blob and bind
it through a compatibility `ContractBundleRelease`, or to create a new replay or
superseding run under a new contract release. Replacing the expected hash in the
historical manifest would erase the evidence and is forbidden.

M0 aggregate validation must report this result by a stable check name and mark it
as an acknowledged historical failure. It may not omit the validator or report
the overall baseline as unconditionally green.

## 5. Formalization coverage and gap

### Dynamically revalidated

- `formal/AgtXIvRootMath`: 43 audited declarations; kernel build, placeholder
  scan, and axiom audit passed. Reported standard dependencies include
  `Classical.choice`, `Quot.sound`, and `propext`; the selected interfaces do not
  imply source/physical-semantic acceptance.
- `formal/AgtXIvVarela`: 6 audited declarations; kernel build, placeholder scan,
  and axiom audit passed. The central result remains conditional on explicit
  reconstruction/foundation premises and does not prove the target paper's full
  theorem.

### Stabilizerness dynamic-validator gap

`formal/AgtXIvStabilizerness/verification-result.json` records four target-local
declarations and three imported graph-foundation declarations, a passed build,
placeholder scan, and axiom audit dated 2026-08-16. Unlike RootMath and Varela,
the repository has **no dedicated dynamic validator** that independently
recomputes its source hashes, toolchain/import bindings, clean build, placeholder
policy, declaration list, and axiom results in the aggregate validation path.

Therefore this M0 audit treats the Stabilizerness JSON as an existing recorded
artifact, not a newly reproduced pass. Roadmap M5 requires a dynamic validator.
Until then, the local-delta record cannot inherit the stronger confidence of the
two dynamically revalidated projects, and in any event it explicitly does not
prove the closed-form theorem or confer scientific acceptance.

## 6. V2 contract slice: implemented and missing

### Implemented baseline

- 12 V2 JSON Schemas and 13 top-level V2 fixture records;
- canonical/transitive hash and exact-reference checks;
- a profile-relative artifact ledger with mixed dispositions;
- ordered Root Agent audit and unresolved frontier;
- independent mechanical certification in the fixture;
- domain-qualified knowledge snapshot and atomic-ingestion fixture;
- adversarial validator tests for the current slice.

The fixture demonstrates that artifacts can be accounted without turning
`BLOCKED`, `UNKNOWN`, or `NOT_APPLICABLE` into success. It does not show that the
missing producer stages exist.

### Principal production gaps

- immutable `ContractBundleRelease`, artifact-family catalog, common envelopes,
  and typed terminal-result kernel;
- machine-readable source acquisition/package, safe extraction, structure,
  discovery, independent freeze, and source inventory;
- V2 ScientificClaim decomposition and whole-paper reconstruction;
- rich native `MathClaimIR/2`, conservative V1 binding, residual semantics,
  `InferenceStep`, and graph-ontology contracts;
- formal build evidence, declaration graph, backtranslation, alignment, and
  scientific applicability records;
- durable attempts/events, replay bundles, archive receipts, per-entry reviews,
  production admission transactions, and migration receipts;
- production API, runner/queue, CAS, PostgreSQL/Alembic registry, role policy,
  signatures, and offline verifier.

## 7. Visualization baseline

The repository contains visually polished static assets:

- `demo_design/` landing and four-stage paper route;
- a ScientificClaim graph result;
- a MathContract graph experience;
- the interactive layered V2 architecture visualization.

The landing is not a live arbitrary-paper pipeline. Its JavaScript accepts only
the precomputed `2607.26154v1` pilot, advances through four timer-driven messages,
then redirects to a static result. It reports zero new database records. Other
well-formed arXiv inputs are rejected as unsupported. The current Pages entry
redirects to the older Stabilizerness MathContract demo rather than the V2 stage
ledger.

This is valuable reusable presentation work, but M7 must connect it to exact API
events, artifacts, terminal results, review state, graph snapshots, and an
offline-verifiable bundle. A timer must never be displayed as producer progress.

## 8. Decision coverage and M0 residual risks

| Decision | Baseline implication |
|---|---|
| D1 | Existing Git/SQLite prototype is not declared production authority; replay bundle/CAS/PostgreSQL contracts remain to be implemented. |
| D2 | Shellworld exposes the mutable-path problem; ADR 0002 freezes the repair policy. |
| D3 | Current preselected inventory is insufficient; plan/discovery/independent freeze contracts are M1. |
| D4 | Current package fixture distinguishes mixed dispositions, but archive and entry admission services are absent. |
| D5 | A complete machine catalog and positive operational coverage report do not yet exist. |
| D6 | V2 must preserve rich V1 IR through native core plus conservative binding. |
| D7 | Fixture role separation exists; production identity, authorization, signing, stale-review, and database constraints do not. |
| D8 | Existing graphs are reusable but require distinct V2 ontologies and lifecycle rules. |
| D9 | Network and sandbox boundaries are design requirements, not yet enforced production controls. |
| D10 | M1.5 must prove semantics on real pinned papers with filesystem CAS/in-process runner before M2 infrastructure freeze. |

At the time of this historical audit, open M0 risks included the unlocked Python
environment, absence of one aggregate validation command, the acknowledged stale
V1 run, missing Stabilizerness dynamic validator, missing public-project
governance/security files, and incomplete CI coverage. Later commits and
`docs/audits/v2-m0-execution-checkpoint-2026-08-31.md` supersede parts of that
snapshot while retaining its evidence. These facts are not permission to weaken
later gates.

## 9. M0 exit evidence required

M0 can be declared complete only when a superseding versioned report records:

1. a clean-checkout Python 3.12+ bootstrap from locked project metadata;
2. one aggregate command with named results for the exact test inventory
   determined by the baseline commit and dependency lock, V1/V2 validators,
   Pages, Lean lanes, and the intentional Shellworld failure; the report must
   record the deterministic inventory or node-identity digest (a deterministic
   hash of the complete test-name list), selection policy, skips/deselections,
   and observed count rather than treating `234` as a mutable invariant;
3. generated-file and contract drift checks;
4. ADRs, threat model, public governance/license/release files, and CI baseline;
5. the non-destructive stale-run supersession policy and an explicit status for
   its implementation;
6. confirmation that no unrelated dirty working-tree files entered the V2 commit.

## 10. Non-implications

This baseline does not certify a V2 release, endorse any scientific claim, prove
that all source material was discovered, prove source-to-formal alignment, or
admit any new knowledge entry. Passing a structural validator or Lean build
cannot be cited as evidence for those independent questions without the exact
records and reviews required by the selected V2 profile.
