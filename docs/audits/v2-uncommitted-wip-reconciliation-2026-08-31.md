# AgtXIv V2 uncommitted WIP reconciliation

- Document status: inventory only; user work in progress not adopted
- Project adoption status: not authorized
- Scientific review status: not performed
- Release, archive, and knowledge-admission effect: none
- Date: 2026-08-31
- Reference clean commit: `f86b98f`
- Branch observed: `codex/agtxiv-v2`
- Roadmap: `docs/roadmaps/v2-end-to-end-implementation-plan.md`
- Architecture decisions: `docs/adr/0001-*.md` through `0006-*.md`

This document records a read-only inventory of pre-existing modified and
untracked user material. It does not take custody of that material, publish it,
approve it, grant it scientific or legal status, or make it part of an AgtXIv
release. Each item remains uncommitted work in progress (WIP) unless a later,
independently reviewed, authorized project decision assigns it a disposition
and a focused commit records that decision.

## 1. Scope and method

The inventory was captured against the clean M0 reference commit `f86b98f`.
The later M0 checkpoint commit records the clean reproduction of that commit;
it does not adopt the WIP listed here. Files introduced or changed concurrently
by the M0 execution work, including the aggregate-repository and dynamic
Stabilizerness validators, are outside this reconciliation. No WIP file was
edited, staged, reset, reformatted, moved, or committed while collecting this
evidence.

The scoped tracked WIP consists of 20 modified files with the following diff
against `f86b98f`:

| File group | Files | Insertions | Deletions |
|---|---:|---:|---:|
| `AgtXIv.md` | 1 | 2 | 2 |
| `demo_design/` | 6 | 787 | 332 |
| architecture JSON and HTML | 2 | 620 | 325 |
| V2 paper-agentization specification | 1 | 187 | 84 |
| modified V2 fixtures | 4 | 481 | 38 |
| modified V2 schemas | 4 | 1,116 | 182 |
| V2 contract tests | 1 | 392 | 34 |
| V2 cross-record validator | 1 | 251 | 25 |
| **Total** | **20** | **3,836** | **1,022** |

The exact tracked diff inventory is:

| Path | Insertions | Deletions |
|---|---:|---:|
| `AgtXIv.md` | 2 | 2 |
| `demo_design/README.md` | 22 | 5 |
| `demo_design/app.js` | 210 | 49 |
| `demo_design/index.html` | 187 | 91 |
| `demo_design/scientific_claims/index.html` | 10 | 0 |
| `demo_design/scientific_claims/styles.css` | 16 | 0 |
| `demo_design/styles.css` | 342 | 187 |
| `docs/architecture/agtxiv-paper-first-layered.architecture.html` | 273 | 175 |
| `docs/architecture/agtxiv-paper-first-layered.architecture.json` | 347 | 150 |
| `docs/specifications/v2-paper-agentization.md` | 187 | 84 |
| `fixtures/v2-paper-agentization/knowledge-index-snapshot.json` | 158 | 14 |
| `fixtures/v2-paper-agentization/query-resolution-package-backed.json` | 4 | 3 |
| `fixtures/v2-paper-agentization/release-audit-record.json` | 294 | 15 |
| `fixtures/v2-paper-agentization/release-certification-record.json` | 25 | 6 |
| `schemas/v2/knowledge-index-snapshot.schema.json` | 400 | 15 |
| `schemas/v2/query-resolution.schema.json` | 226 | 16 |
| `schemas/v2/release-audit-record.schema.json` | 28 | 135 |
| `schemas/v2/release-certification-record.schema.json` | 462 | 16 |
| `tests/test_v2_paper_agentization.py` | 392 | 34 |
| `tools/validate_v2_paper_agentization.py` | 251 | 25 |

Untracked material has no committed baseline from which a meaningful line diff
can be computed. It includes two new V2 schemas, two new V2 fixture records,
the static-demo tests, `database/`, `demo_design_minimal/`, two downloaded arXiv
source trees, and presentation, logo, PDF, and slide-build material. The status
of those paths is recorded below; their presence is not implementation evidence.

The exact scoped untracked paths or path groups are:

- `schemas/v2/assessment-record.schema.json`;
- `schemas/v2/knowledge-ingestion-receipt.schema.json`;
- `fixtures/v2-paper-agentization/knowledge-index-snapshot-genesis.json`;
- `fixtures/v2-paper-agentization/knowledge-ingestion-receipt.json`;
- `tests/test_demo_intake.py`;
- `database/`;
- `demo_design_minimal/`;
- `References/2511.13531/` and `References/2606.25363/`;
- `AgtXIv_v1_overview_1to1.pptx` and
  `AgtXIv_v1_overview_editable.pptx`;
- `draft/main.bbl` and `draft/main.pdf`;
- `logo/`;
- `slide_demo.pdf` and `slide_demo.pptx`; and
- `slides/`.

## 2. Test observations and the baseline-count distinction

Three different test observations must not be collapsed into one baseline:

1. The reproducible clean fast-profile result at `f86b98f` is **202 passed**
   under the locked Python M0 environment. This is the current versioned clean
   Python baseline, as recorded in
   `docs/audits/v2-m0-execution-checkpoint-2026-08-31.md:36-58`; it is not a
   clean formal-toolchain bootstrap result.
2. The historical audit observed **234 passed** in the dirty primary worktree on
   2026-08-30. That was a useful workstation observation, not a clean,
   commit-defined baseline. It included user WIP and predates the ten M0
   aggregate-runner tests; see the checkpoint's explanation at lines 78-97.
3. The scoped tests inspected for this reconciliation contribute **42 dirty
   pytest cases** beyond their corresponding committed test content:
   - committed `tests/test_v2_paper_agentization.py` collects 60 cases;
   - the modified file collects 98, a net increase of 38 cases;
   - untracked `tests/test_demo_intake.py` contributes 4 cases;
   - therefore the scoped WIP increment is 38 + 4 = 42 cases.

The V2 test file contains 51 committed test functions and 77 WIP test functions;
parameterization accounts for the difference between function and case counts.
The scoped V2 plus demo command collected 102 cases and they passed in the
observed worktree. The V2 validator also accepted 13 top-level JSON records
against 12 schemas. These are diagnostic facts about the current file set, not
branch or release evidence.

The numbers 202, 234, and 42 describe different repository states and test
inventories. They must not be combined arithmetically to infer an unobserved
clean-suite total.

### Roadmap correction in this documentation slice

The accompanying roadmap diff replaces the mutable fixed `234-test` M0 exit
wording with a gate based on:

- the exact baseline commit and dependency lock;
- an exact versioned test inventory or deterministically generated node-ID list;
- the command and selection policy, including skip and deselection handling;
- the observed count recorded in the baseline report; and
- a reviewed inventory diff for any later addition, removal, rename, skip, or
  parameterization change.

For the current clean baseline, the observed count is 202 at `f86b98f`. The 234
figure remains a historical dirty-worktree observation. The 42 scoped WIP cases
remain pending independent review and an authorized focused commit.

This is a stronger gate, not a reduction: a fixed count cannot detect deleting
one test and adding an unrelated replacement, while an exact inventory can.
The wording correction becomes versioned with this reviewed documentation
slice; producing and reviewing the deterministic inventory remains open M0 work.

## 3. Specification and architecture WIP

### 3.1 Root document and V2 specification

`AgtXIv.md` adds a clearer distinction between the accountable V2 Root Agent and
the independent mechanical `ReleaseCertifier`. That distinction agrees with ADR
0004, but the abstract still begins from a preselected `InventoryScope`.

`docs/specifications/v2-paper-agentization.md` expands the paper-first lifecycle:

- lines 13-28 give the proposed release-to-query order;
- lines 64-83 distinguish coordinator, Root Agent, and certifier;
- lines 89-103 define a thirteen-state profile-relative lifecycle;
- lines 113-124 define the ten ordered Root Agent audit stages and frontier;
- lines 126-136 separate source fidelity, formal verification, and scientific
  acceptance;
- lines 138-142 distinguish package archive from entry admission while stating
  that no production archive-receipt schema exists in this slice;
- lines 177-181 describe atomic before/after knowledge snapshots; and
- lines 245-251 distinguish claimed contract coverage from production targets.

The proposed specification partially implements the audit and status-boundary
ideas in ADR 0004. It does not yet conform to the accepted architecture as a
whole:

- the canonical sequence starts with a preselected `InventoryScope` at lines
  13-15 and 40-46 rather than ADR 0003's Plan, Discovery, independent Freeze
  Decision, and `FrozenInventoryScope`;
- it does not bind a `ContractBundleRelease` required by ADR 0002;
- it has no replay bundle, Merkle root, signature, content-addressed storage
  (CAS), or `ArchiveReceipt` required by ADRs 0001, 0002, and 0004;
- the native mathematical intermediate representation remains thinner than ADR
  0005; and
- it does not implement ADR 0006's controlled acquisition and model-egress
  boundaries.

The wording "implemented here" at lines 237-249 describes intended WIP coverage.
It is not evidence that those records are committed, released, or authorized.

### 3.2 Architecture representations

The modified architecture JSON contains 19 components, 18 connections, two
boundaries, and four guided views, compared with 12 components, 11 connections,
one boundary, and four views in the clean commit. It separates dependency and
inference production, formalization, formal verification, alignment,
residual semantics, assessment selection, package archive, and reusable-entry
admission.

Evidence in
`docs/architecture/agtxiv-paper-first-layered.architecture.json` includes:

- `package_archive` tagged `V2 target service` near lines 261-275; and
- `reusable_entry_admission` tagged `implemented contract` near lines 276-290.

The first label is appropriately limited. The second is premature because the
current contracts do not include archive receipt, independent entry review, or
eligibility decisions. The JSON and compiled HTML are checked for synchronized
nodes, edges, and guided views by the WIP tests, so they should be treated as one
generated-artifact boundary. An authorized project decision must identify the
source of truth and deterministic generation/drift procedure before adoption.

## 4. Schema, fixture, validator, and test WIP

### 4.1 Modified and new schemas

The four modified schemas are:

| Path | Proposed function | Principal reconciliation issue |
|---|---|---|
| `schemas/v2/knowledge-index-snapshot.schema.json` | Domain-qualified immutable view with package bindings, independent axes, relations, and environment receipts | Binds manifest/certificate/audit but no archive root, entry review, or eligibility decision |
| `schemas/v2/query-resolution.schema.json` | Package-backed and provisional query outputs, including relation IDs | "all snapshot relations" versus query-relevant closure is not yet defined clearly |
| `schemas/v2/release-audit-record.schema.json` | Ordered Root Agent audit, exact target sets, unresolved frontier, recommendation | Stage outcomes omit `FAILED`, while the specification permits a failed formalization disposition |
| `schemas/v2/release-certification-record.schema.json` | Independent mechanical certification or rejection | Has no production signature/trust-root binding |

The two untracked schemas are:

- `schemas/v2/assessment-record.schema.json`, which types assessment kind, axis,
  relation, targets, endpoints, and outcome; and
- `schemas/v2/knowledge-ingestion-receipt.schema.json`, which types an atomic
  domain transaction and before/after snapshots.

The assessment record's required properties at lines 8-20 do not include
assessor identity, `actor_kind`, qualification, independence or conflict
evidence, method, evidence references, rationale, uncertainty, policy,
timestamp, or signed attestation. Its description therefore asserts more
independence than its fields can demonstrate.

The ingestion receipt's required properties at lines 7-24 do not include an
archive root or `ArchiveReceipt`, a per-entry review decision, an eligibility
decision, reviewer identity, or attestation. Atomic mutation alone is not
scientific admission authorization.

All four modified committed schemas retain exactly the same `2.0.0` `$id` and
discriminator while substantially changing their bytes and meaning. Before any
adoption, an authorized project decision must determine whether the committed
2.0.0 contracts were never released drafts or whether these changes require new
exact schema versions and migrations. Silent replacement under one immutable
identifier would conflict with ADRs 0001 and 0002.

### 4.2 Mathematical representation dependency

The committed `schemas/v2/math-claim-ir.schema.json:7-20` currently contains only
the scope/source inventory binding and components whose fields are ID, path,
kind, and normalized statement. The WIP does not change that schema.

ADR 0005 requires native typed objects, domains, quantifiers, assumptions,
conclusion, units, conventions, approximations, normalization, residual
semantics, native/V1 binding, typed `InferenceStep`, and distinct graph
ontologies. The admission and query WIP therefore depends on a mathematical core
that has not yet been implemented.

### 4.3 Fixture semantics

The modified release-audit fixture records ten ordered stages:

- three `PASSED` stages;
- six `BLOCKED` stages;
- one `UNKNOWN` stage; and
- seven retained frontier items.

It recommends `RECOMMEND_PROFILE_RELEASE` with
`MIXED_DISPOSITIONS_ACCOUNTED`. The certificate fixture records all four
mechanical checks as passed and returns `CERTIFIED`. This can be a valid example
of certifying complete accounting with unresolved scientific work; certification
still cannot authorize reusable-entry admission.

The proposed knowledge snapshot nevertheless contains:

- a MathClaimIR-derived entry marked `ADMITTED` while source fidelity is
  `UNKNOWN`, formal verification is `NOT_APPLICABLE`, and scientific acceptance
  is `NOT_ASSESSED`, at
  `fixtures/v2-paper-agentization/knowledge-index-snapshot.json:37-71`; and
- a formalization-derived entry marked `CONDITIONAL` while all applicable axes
  remain unknown or not assessed, at lines 104-143.

The untracked ingestion receipt accepts both candidates and records `COMMITTED`
at `fixtures/v2-paper-agentization/knowledge-ingestion-receipt.json:43-70`. It
contains no independently reviewed entry decisions.

The central conflict is visible at
`tools/validate_v2_paper_agentization.py:571-573`: the validator requires each
knowledge `admission_status` to equal the manifest disposition. The manifest
uses `ADMITTED` and `CONDITIONAL` as pre-archive accounting dispositions. This
collapses artifact accounting into post-archive admission, contrary to ADR 0004
and roadmap decisions D4 and D7.

The required semantic split is:

```text
artifact accounting disposition
  -> Root Agent audit
  -> independent mechanical certificate
  -> immutable replay bundle and ArchiveReceipt
  -> independently reviewed per-entry decision
  -> policy-computed eligibility
  -> atomic knowledge-admission transaction
```

### 4.4 Validator strengths and limits

The WIP validator adds useful checks for canonical hashes, exact references,
pairwise role separation, fixed audit order, exact frontier target sets,
non-promotion across assessment axes, relation endpoints, and atomic snapshot
mutation. The adversarial tests exercise those invariants.

It remains a fixture-oriented prototype because it has no:

- `ContractBundleRelease`, `ArtifactFamilyCatalog`, or Plan/Discovery/Freeze;
- CAS, replay tree, Merkle root, signature, or offline verifier;
- `ArchiveReceipt`, independent review, or eligibility object;
- dynamic Lean build or kernel verification for the fixture;
- reusable package/application service boundary; or
- complete containment validation for arbitrary fixture paths.

Passing the 102 scoped cases establishes internal WIP consistency only.

## 5. Static demo reconciliation

### 5.1 `demo_design/`

The modified landing page adds an arXiv input, four timer-driven stages, a pilot
outcome, accessible status text, and updated styling. It is intentionally static:

- `demo_design/README.md:7-14` says only `arXiv:2607.26154v1` is supported and
  that the interaction replays precomputed artifacts;
- `demo_design/app.js:121-127` hard-codes the pilot and report;
- `demo_design/app.js:130-155` accepts modern numeric `abs` and `pdf` forms but
  not legacy IDs or `e-print`, and treats an omitted version as v1 rather than
  resolving and freezing the observed version;
- `demo_design/app.js:174-204` advances with `setTimeout` and redirects to the
  static ScientificClaim view; and
- `demo_design/scientific_claims/app.js:4,755` loads one local JSON payload.

The payload is `agtxiv.scientific-claim-demo/4.0.0` and contains V1
`ScientificClaim/1.1.0` and `MathClaimIR/1.0.0` records. It is not coupled to the
V2 fixtures, the database prototype, an API, a runner, or durable events.

The four untracked demo tests verify accessible markup, equivalent pilot input
forms, timer and duplicate-submit behavior, reduced-motion timing, relative
links, and honest outcome copy. They test a labelled static replay, not arbitrary
arXiv processing.

### 5.2 `demo_design_minimal/`

The untracked minimal demo is another approximately 2.3 MB full copy. Byte
comparison found the following shared files identical between the two demos:

- root `app.js`;
- ScientificClaim `app.js`;
- `data/graph-theoretic-scientific-claims.json`;
- the logo; and
- the bundled MathJax license, manifest, and JavaScript.

The README, HTML, and CSS provide an alternative visual theme. Both copies have
the same one-paper timer workflow and V1 data dependency. Keeping both as
independent applications would create predictable code, data, and vendor drift.
An authorized project decision should select one canonical application or
extract shared logic, data, and vendor assets before either theme is adopted.

## 6. Database prototype reconciliation

The untracked `database/` tree contains 14 files:

- a format and lifecycle README plus a database manifest;
- one `agtxiv.query-run-dataset/0.1.0` JSON Schema;
- one SQLite migration;
- query-run and knowledge-record templates;
- source, run, knowledge, and derived-directory guidance;
- a Stabilizerness legacy example manifest; and
- structural validator and catalog-builder scripts.

`database/README.md:3-6` labels it a file-contract prototype, data format 0.1.0,
based on AgtXIv v0.5 and commit `095f160`. Lines 10-24 describe a query-first
Paper + Query -> Run -> Artifact -> promoted knowledge chain. Lines 60-70 make
Git-reviewed files authoritative and SQLite a rebuildable index. Lines 288-300
mention independent promotion in prose.

The SQLite migration defines datasets, paper works and versions, queries, runs,
artifacts, provenance edges, knowledge records, and audit findings. It has no
archive, review, eligibility, signature, policy-attestation, append-only event,
or PostgreSQL/Alembic semantics. The structural validator checks identities,
paths, hashes, locators, supersession, and provenance, but not independent
scientific admission. At `database/scripts/validate_database.py:580-587`, release
acceptance is a Boolean.

The catalog builder has explicit local side effects:

- `--output` is required;
- existing files are refused unless `--replace` is provided;
- replacement is allowed only after checking the SQLite header;
- it creates the output directory and database;
- it removes a partial output on failure; and
- the generated SQLite files are ignored under `database/derived/`.

The builder was not run during this read-only inventory. The structural validator
was run and reported one manifest, five papers, nineteen artifacts, and twelve
provenance edges. The example run is `COMPLETED/BLOCKED`, has two knowledge
records, records `accepted_release=false`, and retains warnings for missing query
output, incomplete identity crosswalk, stale derived status, source-anchor gaps,
and an incomplete source bundle.

This prototype aligns with the exact-hash/provenance and disposable-SQLite parts
of ADR 0001. It conflicts with the current V2 authority model because it is
query-first, treats repository data directories as authoritative arbitrary
storage, and lacks CAS, replay bundle, contract binding, archive, independent
review, and production transaction semantics.

An authorized project decision should first preserve and isolate the prototype
as a byte-identical legacy migration fixture or historical design artifact. The
project should then stabilize the ADR-compliant native V2 contracts before
building a compatibility adapter. The adapter must emit explicit bindings and
migration reports, retain unknown, provisional, residual, and blocked status,
and never rewrite V1 records. Implementing the adapter against this v0.5
prototype first would risk freezing obsolete authority and admission semantics
into V2.

## 7. References, presentations, and media

Two untracked arXiv source trees are present:

- `References/2511.13531/`, containing the TeX source and figures for
  *Simultaneous variances of Pauli strings, weighted independence numbers, and a
  new kind of perfection of graphs*; and
- `References/2606.25363/`, containing the TeX source and figures for
  *TheoremGraph: Bridging Formal and Informal Mathematics*.

Their `00README.json` files record TeX build inputs but do not record the exact
paper version, acquisition receipt, source hash, license, or redistribution
disposition. The current `References/<id>` paths also differ from the requested
future research-source convention `Reference/<paper title>/`. The TheoremGraph
source itself notes at
`References/2606.25363/sections/limitations-conclusion/limitations.tex:10` that
arXiv's default license does not necessarily grant third-party redistribution.

These trees may be useful research inputs, but they cannot be published or
included in a release corpus without an authorized source/version/rights
disposition and any independently required legal review. Their presence is not
an acquisition, CAS, or replay-bundle implementation.

Other untracked material includes two V1 overview presentations, `slide_demo.pdf`
and `.pptx`, `draft/main.pdf` and `.bbl`, `logo/`, and `slides/`. The slides tree
is approximately 38 MB and includes LaTeX build caches, auxiliary files,
`.DS_Store`, and an office temporary file. These should remain separate from
contracts and runtime code. An authorized project decision must classify source,
generated deliverable, reproducible build output, temporary file, third-party
asset, and redistribution status before any focused media commit.

## 8. Reconciliation against ADR 0001-0006

| ADR | Compatible WIP elements | Conflict or missing implementation |
|---|---|---|
| 0001, released-content authority | Exact hashes, immutable snapshot intent, rebuildable SQLite concept | No CAS, signed Merkle replay bundle, archive-root binding, or PostgreSQL authority; database prototype treats Git data directories as authority |
| 0002, immutable contract bundle | Canonical JSON and transitive hash checks | No `ContractBundleRelease`, signature suite, trust policy, or pinned human-readable spec blobs; same 2.0.0 schema IDs have changed bytes |
| 0003, plan/discovery/freeze | Query is stated not to narrow canonical work | Lifecycle starts from preselected `InventoryScope`; no plan, discovery evidence, independent freeze decision, or frozen-scope revision |
| 0004, archive and entry admission | Ordered Root audit, mechanical certifier, mixed frontier, atomic before/after snapshot | No `ArchiveReceipt` or independently reviewed per-entry eligibility; accounting dispositions are reused as admission statuses |
| 0005, native MathClaimIR and V1 binding | Source/formal/scientific axes are kept distinct | Thin IR, no native rich core, V1 binding, residual mapping, `InferenceStep`, or distinct graph contracts |
| 0006, controlled external egress | Static demo itself performs no acquisition | No acquisition worker, model gateway, quarantine, rights-aware egress policy, offline worker sandbox, or runtime enforcement |

## 9. Dependency order and focused commits

The semantic dependency order is:

```text
ContractBundleRelease + ArtifactFamilyCatalog
  -> AgentizationPlan
  -> InventoryDiscoveryResult
  -> independently reviewed ScopeFreezeDecision
  -> FrozenInventoryScope
  -> source/CAS and producer attempts
  -> claims, rich MathClaimIR, inference and graph records
  -> formalization, verification, alignment and assessments
  -> candidate manifest and accounting ledger
  -> Root Agent audit
  -> independent mechanical certification
  -> replay bundle, archive and ArchiveReceipt
  -> independently reviewed entry decisions and eligibility
  -> atomic knowledge admission and immutable snapshot
  -> read-only query resolution
```

The current WIP begins in the middle of this chain and jumps from certification
to admission. It should not be committed as one aggregate change.

Subject to authorized project decisions and independent review, the recommended
focused sequence is:

1. **Reconcile normative documents.** Update `AgtXIv.md`, the V2 specification,
   and architecture JSON/HTML to match ADRs 0001-0006 and label implemented
   versus target surfaces accurately.
2. **Freeze contract identity policy.** Decide whether existing 2.0.0 contracts
   are unpublished drafts or require new exact versions and migrations.
3. **Land the M1 common kernel.** Contract bundle, catalog, immutable envelopes,
   typed terminal results, Plan/Discovery/Freeze, rich MathClaimIR, V1 binding,
   assessment identity/evidence/attestation, and graph kernel.
4. **Land Root audit and mechanical certification.** Keep schemas, positive and
   negative fixtures, validator code, and their tests in the same focused commit.
5. **Land replay/archive/review/admission.** Add replay root, ArchiveReceipt,
   independently reviewed entry decisions, eligibility, and separated
   accounting/admission states before snapshot, ingestion, and query contracts.
6. **Retain one labelled static demo fixture.** Commit the honest one-paper replay
   and its four tests separately from V2 runtime claims; consolidate the minimal
   theme through shared assets if it is authorized for retention.
7. **Quarantine the legacy database prototype.** Preserve it as a migration
   fixture or historical design input, then build an ADR-compliant compatibility
   adapter after the native target contracts are stable.
8. **Handle research sources and media separately.** Complete source/version,
   generated-artifact, temporary-file, and rights dispositions before any
   reference or presentation commit.

## 10. Walking-slice determination

The current WIP is **not** the first M1.5 walking slice. At most, after resolving
the contract conflicts above, part of it could become a pre-slice contract
fixture.

The M1.5 requirements at
`docs/roadmaps/v2-end-to-end-implementation-plan.md:434-449` include filesystem
CAS, canonical replay bundle, an in-process runner, thin API and command-line
interfaces, a web stage ledger and artifact explorer, exact acquisition, safe
extraction, anchors, structure, initial claim/IR output, lineage, typed failures,
two or three differently shaped version-pinned papers, and byte-identical offline
replay. None of those end-to-end seams is present in this WIP.

Additional missing dependencies include a published arXiv input grammar,
Plan/Discovery/Freeze, a machine artifact catalog, producer attempts and events,
dynamic Lean evidence exact-bound to this V2 fixture and produced in a qualified
clean/no-egress environment, archive and independent entry review, one shared
API payload across command line and browser, and adversarial acquisition tests.
The static timer demo and legacy SQLite prototype are disconnected from the V2
fixture and cannot fill those gaps.

## 11. Required authorized decisions before adoption

The WIP remains isolated until authorized project decisions and the applicable
independent reviews resolve at least:

1. immutable schema-version and migration treatment for changed 2.0.0 bytes;
2. Plan/Discovery/Freeze and `ContractBundleRelease` prerequisites;
3. complete assessment actor, qualification, evidence, conflict, policy, and
   attestation contracts;
4. archive receipt, per-entry independent review, eligibility, and separation of
   accounting disposition from admission status;
5. whether query relation closure means the complete snapshot set or an exact
   query-relevant closure;
6. the canonical architecture source and generated HTML drift procedure;
7. one canonical demo application and any retained theme structure;
8. quarantine location and semantics for the v0.1 database prototype;
9. exact source/version/hash and rights disposition for downloaded arXiv trees;
10. generated, temporary, third-party, and redistributable status for media; and
11. production and review of the exact baseline test inventory, skip/deselection
    policy, and observed count required by the now-corrected M0 roadmap gate,
    with the 42 dirty cases remaining pending review.

This audit neither takes control of, publishes, approves, certifies, archives,
nor admits any inventoried user material. It grants no scientific, legal,
copyright, licensing, provenance, release, or knowledge status. A later commit
may use this document as reconciliation evidence only after the relevant material
has received an authorized project disposition and the required independent
review; until then, every inventoried path remains uncommitted user WIP.
