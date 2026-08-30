# AgtXIv V2 end-to-end implementation plan

- Status: execution baseline
- Plan version: 0.1.0
- Date: 2026-08-31
- Normative architecture: `docs/specifications/v2-paper-agentization.md`
- Compatibility authority: `AgtXIv.md`, `docs/specifications/v1-bridge.md`, and `docs/specifications/mathematics-pipeline.md`

## 1. Outcome

AgtXIv V2 will turn every input accepted by its published, versioned arXiv-input grammar into an immutable, inspectable agentization attempt. Only an attempt that passes the release gates becomes a Paper Agent Release. For every stage required by the selected agentization profile, the attempt must contain either:

1. a schema-valid artifact with exact source, producer, environment, and lineage references; or
2. a typed terminal result that explains why the artifact is unavailable, whether this attempt can be retried, what evidence supports the result, and who or what must act next.

The product promise is **complete, auditable accounting**, not automatic success for every theorem. A paper with unavailable source, ambiguous mathematics, an unprovable target, or an unresolved scientific assumption still reaches an honest and inspectable state. It must never be presented as formally or scientifically verified merely because the pipeline finished.

The completed V2 demo must accept every form covered by that input grammar, show the live stage ledger, and expose every artifact's metadata. When access and redistribution policy permit, it also exposes the bytes; otherwise it exposes the exact hash, immutable locator, rights disposition, and reason the bytes are withheld. It must render the relevant graph views, trace every derived claim back to source anchors and producer attempts, show the mathematical formalization and its independent checks, and make archive and knowledge-admission decisions visible. Every published, redistributable release bundle must be downloadable and verifiable offline. For restricted content, the offline verifier validates the recorded locator, digest, and rights disposition; it validates the underlying artifact bytes only when the user supplies authorized bytes.

## 2. Intuition and trust model

The simplest mental model is a **paper compiler with independent inspection**:

- the frozen arXiv release is the source program;
- source anchors, scientific claims, and `MathClaimIR` are intermediate representations;
- inference and dependency graphs are the load-bearing map of the argument;
- a Lean build checks whether a stated formal theorem follows from its formal premises;
- backtranslation and alignment check whether the formal theorem still means what the paper said;
- scientific assessment checks whether the premises, approximations, conventions, and domain of use are justified;
- the Root Agent audits the complete release, while a separate certifier verifies mechanical integrity;
- the immutable archive preserves the whole attempt, including failures;
- only independently reviewed individual entries may enter the reusable knowledge base.

Three questions therefore remain separate:

1. **Source fidelity:** did the paper actually say this?
2. **Formal validity:** does the formal conclusion follow from the exact formal assumptions?
3. **Scientific applicability:** are those assumptions, approximations, units, and regimes defensible for the claimed use?

A successful proof answers only the second question. V2 must not collapse these axes into one `VERIFIED` Boolean.

### 2.1 Short glossary

- **IR (intermediate representation):** a structured form between source text and formal code.
- **DAG (directed acyclic graph):** a directed graph with no directed cycle; only graph views that prove this property are called DAGs.
- **ADR (Architecture Decision Record):** a versioned explanation of an important design choice.
- **CAS (content-addressed storage):** storage where bytes are addressed by their cryptographic digest rather than a mutable filename.
- **Merkle root:** one digest that commits to the complete tree of records and artifacts in a bundle.
- **API / CLI / UI:** service interface, command-line interface, and user interface.
- **CI (continuous integration):** automated checks run for proposed repository changes.
- **E2E (end to end):** a test that crosses the complete user-visible workflow.
- **SCC (strongly connected component):** a maximal cyclic region of a directed graph, condensed to one build-order node.
- **SSRF (server-side request forgery):** abuse that tricks a service into fetching an unintended network location.
- **SBOM (software bill of materials):** a machine-readable inventory of software dependencies.
- **WORM (write once, read many):** storage policy that prevents an archived object from being overwritten.

## 3. Current repository baseline

The repository is not starting from zero. It currently contains a healthy V2 contract slice plus substantial V1 implementations, but not an arbitrary-paper production pipeline.

### 3.1 Implemented and reusable

- 12 V2 JSON Schemas, 13 V2 top-level fixture records, a cross-record validator, and tests for the current paper-agentization contract slice.
- V1 ScientificClaim extraction and validation, rich `MathClaimIR` records and migrations, source anchors, claim/dependency graph validation, root partitioning, blocker/frontier concepts, and query closure logic.
- Pilot records containing paper agents, anchors, artifacts, reasoning, verification, and blocker records.
- Dynamic Lean build, placeholder, declaration, and axiom audits for the RootMath and Varela examples.
- A static landing experience, a ScientificClaim graph, a MathContract graph, and an interactive V2 architecture visualization.
- A Git-backed/SQLite-derived database prototype whose vocabulary and offline-index idea are reusable.

### 3.2 Verified baseline on 2026-08-30

- Full test suite with the repository-capable Python environment: `234 passed`.
- V2 paper-agentization validation: 13 JSON records against 12 schemas, passed.
- V1 claim, DAG, pilot, root-partition, interface-study, semantic-contribution, and database structural validators: passed.
- RootMath dynamic Lean rebuild: passed; 43 declarations; placeholder and axiom audits passed.
- Varela dynamic Lean rebuild: passed; 6 declarations; placeholder and axiom audits passed; scientific acceptance remains intentionally absent.
- Static site build and page validation: passed.

### 3.3 Material gaps and one known regression

- The current landing page accepts only the precomputed `2607.26154v1` example and advances via timers. It is not a live arbitrary-arXiv pipeline.
- The current Pages build exposes an older V1 MathContract experience rather than the full V2 workflow.
- The current V2 release fixture proves artifact accounting for a mixed-disposition package; it does not prove whole-paper scientific or formal completion.
- Machine contracts and producers are still missing for source acquisition, paper structure, V2 ScientificClaim decomposition, inference/dependency graphs, formal evidence, backtranslation, alignment, residual semantics, production blockers, archive receipts, and V1 migration.
- The current V2 `MathClaimIR` is materially poorer than the existing V1 semantic representation and must not replace it as written.
- A published Shellworld V1 run currently fails only its immutable-manifest check because it hashes the mutable path `docs/specifications/v1-bridge.md`. The document changed after the run was recorded. V2 must bind runs to an immutable contract release, not to the current working-tree contents.
- There is no complete production dependency lock, migration system, service API, durable worker, production transaction store, threat model, contributor policy, or release policy.

## 4. Frozen architecture decisions

These decisions close ambiguities that would otherwise create multiple authorities or misleading completion states. Changes require an Architecture Decision Record (ADR), migration impact analysis, and updated fixtures.

### D1. Released content authority

Git is authoritative for reviewed code, schemas, migrations, fixtures, ADRs, and contract releases. It is not the production store for arbitrary-paper bytes.

Raw and generated bytes use content-addressed storage (CAS). A certified Paper Agent release is sealed as a replay bundle containing the producer records, selected pre-release assessments, Root audit, certificate, artifacts, rights dispositions, and byte references under one signed Merkle root. That bundle is the canonical released semantic object.

Post-archive entry-admission reviews, eligibility decisions, withdrawal/supersession records, ingestion receipts, and knowledge snapshots are separate immutable transaction records that bind the archive root. They are never inserted retroactively into the release bundle.

PostgreSQL is the append-only operational registry and transaction authority for jobs, attempts, reviews, admission transactions, exact bundle references, and query projections. Every released projection must be rebuildable from the canonical replay bundle. SQLite remains a disposable offline/development projection, never a competing truth source.

### D2. Immutable contract binding

Every run binds an exact `ContractBundleRelease`, not mutable documentation paths. It includes hashes for:

- schemas and canonicalization rules;
- agentization profiles and the artifact-family catalog;
- validators and policy code;
- relevant adapters and migrations;
- environment manifests;
- Git commit and blob identifiers for human-readable specifications.

No authoritative reference may mean `latest`.

The release policy also pins the signature scheme, actor/key identity, trust roots, verification algorithm, and rules for key rotation, compromise, and revocation. Offline verification must be able to determine whether a signature was valid under the policy and trust state applicable when it was issued.

### D3. Plan, discovery, and scope freeze

Whole-paper accounting uses four separate objects:

1. `AgentizationPlan`: exact source release, profile, catalog, discovery obligations, and resource policy, frozen before analysis.
2. `InventoryDiscoveryResult`: classified, unclassified, and ambiguous source components; coverage evidence; errors; tool versions; and a completeness claim.
3. `ScopeFreezeDecision`: an independent review of discovery completeness.
4. `FrozenInventoryScope`: the only inventory against which downstream accounting is measured.

A producer cannot obtain completeness merely by failing to discover difficult content. A new post-freeze discovery creates a new scope revision and invalidates affected downstream gates; it never mutates the old scope.

### D4. Completion, archive, and admission are different

The release path is:

```text
ACCOUNTING_COMPLETE
  -> Root audit
  -> mechanical certification
  -> CERTIFIED_RELEASE
  -> immutable archive + ArchiveReceipt
  -> per-entry review/eligibility decisions
  -> atomic knowledge admission transaction
```

`ACCOUNTING_COMPLETE` allows explicit `BLOCKED`, `FAILED`, and `NOT_APPLICABLE` outcomes. It means every obligation is accounted for, not that every artifact succeeded.

An entire mixed-status package may be certified and archived with zero reusable entries admitted. Admission eligibility is per entry and branches after archive; it is not a package-level third green light.

Post-archive admission reviews and transactions bind the immutable archive root. They do not rewrite or expand the archived release.

Git pull-request merge is a separate code-governance event and has no scientific meaning.

### D5. Artifact obligations are catalog driven

An exact, profile-bound `ArtifactFamilyCatalog` defines each family, its applicability, cardinality, allowed producer role, success record, allowed terminal results, review policy, and gates. The catalog is part of the `ContractBundleRelease`.

Its implementation maturity is tracked separately:

```text
CONTRACTED -> PRODUCED -> PERSISTED -> REVIEWED -> EXPOSED
```

Not every family requires a V1 adapter or a UI panel. A V1 adapter is required only when a real legacy counterpart exists; direct UI exposure is required only for user-facing families. All records remain retrievable through the generic artifact explorer.

`UNSUPPORTED` cannot satisfy a core-profile obligation indefinitely. Required core families must have positive producer coverage in the release test corpus.

### D6. `MathClaimIR` uses native core plus compatibility binding

V2 will define a rich native `MathClaimIR/2` with immutable source/claim/scope/profile bindings, typed mathematical objects, quantifiers, assumptions, normalization, semantic hashes, and component indexing.

Legacy V1 records retain their original identity and hash. `MathClaimIRBinding/2` exact-refers to the V1 record and adds V2 provenance, scope, and mapping evidence without upgrading its status. A common read projection serves downstream producers. No migration may turn `ASSUMED_VERIFIED_FOR_STUDY`, provisional, unknown, or residual information into stronger evidence.

### D7. Review and certification enforce separation of duties

Review endpoints create immutable requests or decisions; clients cannot submit a final certified or admitted state. Every actor declares `actor_kind = HUMAN | AGENT | MECHANICAL_SERVICE`. The `ScopeFreezeDecision`, V2 Root Agent audit, mechanical certification, and scientific admission review each declare the exact actor, role, independence evidence, and policy that authorize them. Application policy and database constraints both enforce:

- producer, V2 Root Agent auditor, mechanical certifier, and scientific reviewer identity separation;
- conflict-of-interest and role policy;
- exact artifact-set, contract, policy, and environment hashes;
- signed attestations where production policy requires them;
- append-only supersession rather than update;
- atomic admission with before/after snapshot hashes;
- rejection of stale reviews after any reviewed byte or record changes.

Only public rationale, findings, evidence, and non-implications are stored. Private chain-of-thought is neither requested nor persisted.

### D8. Graphs have distinct ontologies

V2 will not call every relation set a DAG.

- `ArtifactProvenanceGraph`: derivation lineage; released projection must be acyclic.
- `PaperStructureGraph`: document containment/include structure; may not be a pure tree.
- `PaperInteractionGraph`: cross-paper relation graph; may contain cycles.
- `ClaimInferenceGraph`: bipartite Claim↔InferenceStep representation preserving multi-premise reasoning; accepted dependency projection must be acyclic within a frozen scope unless a typed cycle disposition exists.
- `MathClaimDependencyGraph`: candidate, accepted, rejected, conditional, and blocked mathematical dependencies; only the accepted build projection is a DAG.
- `FormalDeclarationDependencyGraph`: dependencies extracted from a pinned formal environment; a build DAG under declared conditions.
- `PaperBuildDAG`: strongly connected component (SCC) condensation used for build ordering.
- `QueryProjection`: a read-only closure/highlight over an exact snapshot; it does not mutate canonical graphs and need not itself be a DAG.

Every graph snapshot declares its kind, node and edge ontology revisions, direction convention, exact scope/profile/source refs, lifecycle states, reconstruction algorithm, and canonical hash.

### D9. Controlled outbound network boundaries

Only two components may initiate outbound network requests:

1. the acquisition worker may access allowlisted source endpoints; it has no release-signing or knowledge-write credentials and writes only quarantine objects;
2. an optional model gateway may call a configured hosted model when the exact profile and data-use policy permit it.

The model gateway receives only the minimum approved payload, has no storage, signing, review, or knowledge-admission credentials, and records provider, model/version, policy, request digest, response digest, retention setting, and attempt identity. A local-model adapter uses the same interface without network access. Extraction, TeX/PDF handling, general analysis workers, generated code, and formal builds run without network access and with explicit CPU, memory, byte, file-count, and time limits. Papers and generated content never receive network or tool authority.

### D10. Walking slices precede production infrastructure

Before PostgreSQL and the durable queue freeze operational semantics, the same domain contracts and repository interfaces will run 2–3 real version-pinned papers using filesystem CAS and an in-process runner. SQLite, if used, is a rebuildable projection only.

This is not a third persistence model: the replay bundle format, exact references, application services, event types, and repository interfaces are identical. The production milestone replaces adapters, then runs the same contract and replay tests against PostgreSQL and object storage.

## 5. Target implementation shape

V2 begins as a modular monolith. Microservices, a graph database, and a vector database are deferred until measured load or isolation needs justify them.

### 5.1 Runtime

- Python 3.12 or newer; one locked project environment.
- JSON Schema is the persistent contract authority. Runtime transport models must be generated from or mechanically checked against it.
- FastAPI/OpenAPI for the service boundary.
- PostgreSQL 16 and Alembic for production transactions and projections.
- S3-compatible content-addressed object storage with conditional writes, versioning, and production WORM/object-lock policy.
- PostgreSQL-backed leased job queue using transactional claiming; independent worker processes.
- Lean toolchains pinned per formal package; builds run in offline sandboxes.
- The existing web graph renderers are progressively connected to the real API rather than replaced wholesale.

### 5.2 Proposed repository layout

```text
pyproject.toml
src/agtxiv_v2/
  contracts/              # generated/checked runtime views of JSON Schema
  domain/                 # immutable objects and policies
  application/            # use cases and state transitions
  adapters/
    arxiv/
    filesystem_cas/
    object_store/
    sqlite_projection/
    postgres/
    formal/
    model/
    v1/
  api/
  workers/
  cli/
  validation/
schemas/v2/
  common/ source/ inventory/ claim/ graph/
  formal/ assessment/ release/ knowledge/ query/
fixtures/v2/
  toy-lean/ stabilizerness/ shellworld/ negative/ adversarial/
database/
  alembic/ imports/ derived/
apps/web/
tests/
  unit/ contract/ integration/ e2e/ adversarial/
docs/
  adr/ roadmaps/ runbooks/ threat-model/
```

Existing V1 paths remain readable and immutable during migration. Current command-line validators remain compatibility wrappers while shared pure validation functions move into the package.

### 5.3 API and job boundary

Initial public API:

- `POST /v2/intakes`: arXiv ID/URL, exact profile ref, optional version policy, and idempotency key.
- `GET /v2/intakes/{id}` and `GET /v2/runs/{id}`: current attempt, terminal semantics, and exact refs.
- `GET /v2/runs/{id}/events`: server-sent stage events.
- `GET /v2/releases/{id}` and `/artifacts`: manifest, artifact ledger, schemas, hashes, rights dispositions, lineage, and bytes only when access policy permits.
- `GET /v2/releases/{id}/graphs/{graph_kind}`: exact graph snapshot or derived query projection.
- `GET /v2/records/{id}/revisions/{revision}`: immutable record retrieval.
- `POST /v2/review-requests`, `POST /v2/certification-requests`, and `POST /v2/admission-requests`: commands, never caller-authored final states.
- `POST /v2/queries`: read-only resolution against an exact knowledge snapshot; provisional results are clearly non-authoritative and may only trigger query-independent intake.

The HTTP process never performs long work. Each worker attempt consumes exact refs, writes immutable outputs or a typed attempt result, and emits an append-only event. Lease expiry and retry create new attempts; they do not rewrite earlier evidence. The CLI calls the same application services and cannot bypass policy by writing files directly.

## 6. Required artifact families

The machine-readable catalog will be the source for a generated coverage report. Each applicable family instance must declare schema, producer, exact inputs, cardinality, allowed terminal results, validator, fixtures, persistence mapping, retrieval route, review policy, and visible surface where applicable.

| Group | Required families | Current state | Target milestone |
|---|---|---|---|
| Contract | ContractBundleRelease, profile, ArtifactFamilyCatalog, canonicalization and policy refs | profile exists; bundle/catalog missing | M1 |
| Intake | PaperQuery, WorkResolution, SourceAcquisitionRequest/Result | prose specification only | M1/M1.5 |
| Source | PaperSourceManifest, SourcePackageRecord, SourceAnchor, extraction audit, redistribution disposition | V1/prose examples exist | M1.5/M3 |
| Planning | AgentizationPlan, InventoryDiscoveryResult, ScopeFreezeDecision, FrozenInventoryScope | one preselected InventoryScope fixture exists; discovery and independent freeze review are missing | M1 |
| Structure | PaperStructureRecord/Graph and component inventory | missing | M1.5/M4a |
| Claims | ScientificClaim, ClaimDecomposition, attribution and reconstruction evidence | rich V1 data exists | M1/M4a |
| Mathematics | native MathClaimIR/2, MathClaimIRBinding/2, component index, residual semantics | rich V1 + thin V2 exist | M1/M4b |
| Reasoning | InferenceStep, claim inference graph, mathematical dependency graph, frontier/blocker | V1 subsets exist | M1/M4b |
| Provenance | Run/Attempt/Event, ArtifactProvenanceGraph, producer and environment receipts | partial in V1 | M1.5/M2 |
| Formalization | FormalizationRequest, generated package, build result, formal declaration graph | request/result slice exists | M1/M5 |
| Formal evidence | kernel evidence, placeholder/axiom audit, exact declaration binding | validators exist; records missing | M5 |
| Meaning checks | source-blind backtranslation, alignment assessment, assumption/units/approximation audit | missing | M5 |
| Assessment | assessor/method/evidence/rationale/uncertainty/attestation, ReviewDecision | thin WIP schema | M1/M5/M6 |
| Release | release manifest, Root audit, certificate, replay bundle, ArchiveReceipt | partial WIP | M1/M6 |
| Knowledge | candidate entry, relation, per-entry eligibility, admission transaction, snapshot, ingestion receipt | small WIP snapshot | M1/M6 |
| Query | QueryResolution, exact snapshot projection, conflict preservation | partial WIP | M1/M6 |
| Compatibility | V1 binding, migration/import receipt, reconciliation report | V1 bridge prose/data exist | M1/M8 |
| Terminal | typed stage/family result with reason, evidence, retryability, responsible actor, next action | scattered states | M1 |

The catalog has two independent checks:

1. **Contract coverage:** every catalog row has a valid contract and policy.
2. **Operational coverage:** every core-profile obligation in the E2E corpus has a real positive producer result or a policy-allowed, evidence-backed terminal result.

This prevents a pipeline from appearing complete by returning `UNSUPPORTED` for everything.

## 7. Mathematical formalization chain

The auditable chain for an applicable mathematical target is:

```text
exact PaperVersion + source bytes
  -> SourceAnchor
  -> ScientificClaim + decomposition/reconstruction evidence
  -> native MathClaimIR or exact V1 binding
  -> assumptions, quantifiers, domains, units, conventions, approximations
  -> Claim↔InferenceStep graph + dependency frontier
  -> FormalizationRequest + pinned environment
  -> generated formal package + build log
  -> kernel/declaration/placeholder/axiom evidence
  -> independent source-blind backtranslation
  -> source <-> claim <-> IR <-> formal alignment assessment
  -> scientific applicability assessment
  -> Root audit, certification, archive, and optional per-entry admission
```

Formal evidence is recorded on independent axes rather than one monotonic status chain:

| Axis | Minimum states |
|---|---|
| Generation | `REQUESTED`, `GENERATED`, `PARTIAL`, `FAILED`, `NOT_APPLICABLE` |
| Kernel build | `NOT_RUN`, `PASSED`, `FAILED`, `BLOCKED` |
| Placeholder and axiom audit | `NOT_RUN`, `PASSED`, `FAILED`, `BLOCKED` |
| Declaration binding | `NOT_ASSESSED`, `BOUND`, `MISMATCHED`, `BLOCKED` |
| Source/IR/formal alignment | `NOT_ASSESSED`, `ALIGNED`, `MISALIGNED`, `BLOCKED` |
| Scientific applicability | `NOT_ASSESSED`, `ACCEPTED`, `REJECTED`, `BLOCKED`, `NOT_APPLICABLE` |

Each axis is evidence-bearing and none inherits success from another. Build success cannot imply alignment, source fidelity, scientific applicability, or admission. A build that passes must have clean pinned-environment and kernel evidence; alignment or scientific assessment may still fail or remain blocked. Formal packages must reject placeholders such as `sorry`, report unexpected axioms, bind exact declarations back to the target `MathClaimIR`, and expose independent alignment evidence when that assessment is performed.

## 8. Input and terminal-state semantics

An exact, versioned `ArxivInputGrammar` defines supported modern and legacy arXiv IDs, `abs`, `pdf`, and `e-print` URLs, explicit or omitted versions, normalization, and stable rejection codes. The parser must be total over arbitrary input strings: it returns one normalized supported identifier or one typed rejection, never an unhandled case. An omitted version is resolved once and frozen to the exact observed version. Redirects and network endpoints are constructed by the service from the normalized identifier; arbitrary caller-supplied fetch URLs are not followed.

Acquisition outcomes:

- `RESOLVED`: exact version and source package are frozen.
- `UNAVAILABLE`: evidence indicates no usable source under the current policy.
- `RETRY_REQUIRED`: this attempt is terminal, but a new attempt may be scheduled.
- `REVIEW_REQUIRED`: automated processing stops pending a named external decision.

Downstream terminal results distinguish `terminal_for_attempt` from a permanent policy conclusion. They include exact target, stage and family, reason code, evidence refs, retryability, responsible actor, next action, resource budget, and deadline. `NOT_APPLICABLE` creates one explicit disposition rather than empty placeholder artifacts.

## 9. Security and legal boundary

The acquisition and source-processing design treats paper archives, TeX, PDFs, bibliographies, and generated formal code as untrusted input.

Mandatory controls include:

- allowlisted arXiv/publisher endpoints, redirect validation, rate limiting, and SSRF prevention;
- byte, file-count, path-length, decompression-ratio, CPU, memory, and time limits;
- rejection of absolute paths, traversal, symlinks, hardlinks, devices, and duplicate case-insensitive paths;
- quarantine and tree-hash verification before promotion to canonical source objects;
- offline, read-only sandboxes for extraction, TeX/PDF handling, local-model execution, and Lean; hosted-model calls may occur only through the audited gateway in D9;
- no credentials in paper-visible tools, logs, artifacts, or replay bundles;
- license and redistribution dispositions for every retained source/package;
- secret, dependency, container, and software-bill-of-materials scans;
- explicit public-evidence records without private reasoning traces.

## 10. Milestones and exit gates

Milestones are walking slices. The web shell, V1 compatibility, security, and contributor baseline grow throughout rather than appearing only at the end.

| Milestone | User-visible outcome | Definitive gate artifact or command | Current state | Principal blocker |
|---|---|---|---|---|
| M0 | One reproducible validation entry point and public project policy | M0 baseline report + aggregate validation command | In progress | no locked project environment; known stale V1 run |
| M1 | Exact contracts explain every obligation, actor, result, and review | first `ContractBundleRelease` candidate + contract suite | Not started | missing common authority/catalog/review contracts |
| M1.5 | Several real papers run locally to auditable replay bundles | content-addressed local bundle roots + offline replay command | Not started | no intake/CAS/runner seam |
| M2 | Durable API, events, storage, retries, and policy enforcement | storage conformance + crash/atomicity integration report | Not started | contracts must survive M1.5 first |
| M3 | Every input in the published grammar reaches an intake result | grammar property/fuzz report + acquisition security report | Not started | source rules are prose, not machine contracts |
| M4a | Reviewed paper coverage, anchors, and ScientificClaims are visible | scope-freeze and M4a accounting reports | Partial V1 only | no V2 discovery/freeze producer |
| M4b | Mathematical objects and distinct graph views are inspectable | graph/lineage/accounting report on real corpus | Partial V1 only | thin V2 IR; graph ontologies missing |
| M5 | Formal build, meaning alignment, and scientific assessment are visibly separate | pinned rebuild + independent-axis evidence report | Partial examples only | evidence/backtranslation/alignment records missing |
| M6 | Certified archive and independently reviewed per-entry admission work | archive/admission adversarial transaction report | Contract slice only | no production identity, archive, or KB transaction |
| M7 | One real API-backed public demo and offline verifier | browser/accessibility E2E + downloaded-bundle verification | Static fixtures only | landing is timer-driven and single-paper |
| M8 | Conservative V1 migration and public OSS release are operable | reconciliation, benchmark, recovery, and release reports | Not started | depends on stable V2 contracts and runtime |

A milestone is marked `DONE` only when every listed Deliver item exists, every Exit condition passes, and its versioned baseline report records the exact commit, contract bundle, commands, results, produced roots, known residual risks, and next gap.

### M0. Reproducible and versioned baseline

Deliver:

- V2 branch and commit policy; baseline report containing the passing tests and known stale Shellworld run;
- Python 3.12 project metadata, locked dependencies, one bootstrap command, and one aggregate validation command;
- ADRs for D1–D10, initial threat model, LICENSE decision, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CITATION, changelog and release policy;
- CI baseline for formatting, static analysis, tests, schemas, current validators, secret/dependency scan, and generated-file drift;
- a policy for superseding the stale V1 run without rewriting its historical record.

Exit:

- clean checkout bootstraps reproducibly and runs the existing 234-test baseline;
- every baseline validator has a named result, including the intentional stale-run failure;
- no unrelated dirty working-tree files are included in V2 commits.

### M1. Contract kernel and governance invariants

Deliver:

- `ContractBundleRelease`, catalog, common immutable envelope/exact refs, typed terminal result, Plan→Discovery→ScopeFreeze contracts;
- native `MathClaimIR/2`, V1 binding, common read projection, residual semantics, graph snapshot/InferenceStep kernel;
- full assessment/review identity, evidence, attestation and supersession contracts;
- release/replay/archive/admission state machines and per-entry admission semantics;
- initial source/intake contracts, informed by a small real-source security spike;
- validators refactored into pure package functions with current CLI wrappers retained;
- machine catalog plus generated coverage report.

Exit:

- the catalog contains every family assigned to M1 by Section 6, and the generated roadmap-to-catalog coverage report has zero missing or extra required families;
- every contracted family has positive and negative contract fixtures;
- old and refactored validators agree on canonical hashes, accepted fixtures, rejected fixtures, and stable error codes;
- curated V1 success, residual/unknown, and blocked cases round-trip without status promotion;
- producer self-review, Root=certifier, stale review, unknown family, and scope mutation fixtures fail closed.

### M1.5. Local real-paper vertical slice

Deliver:

- filesystem CAS, canonical replay bundle, in-process runner, and optional rebuildable SQLite projection behind production-shaped interfaces;
- a thin API/CLI and web stage-ledger/artifact-explorer shell;
- exact acquisition, safe extraction, anchors, structure, initial claim/IR outputs, lineage, and typed failure results for 2–3 version-pinned papers with different source shapes;
- byte-identical offline replay after source freeze.

Exit:

- at least one single/multi-file TeX paper, one macro/image/bibliography-heavy source, and one unavailable or PDF-fallback path reach fully accounted attempt states;
- every non-source artifact has a provenance path to exact source bytes and a producer attempt;
- repeated idempotent submission returns the same logical intake; retry creates a new immutable attempt;
- traversal, link, archive-bomb, version-confusion, redirect, and size-limit fixtures produce evidence-bearing terminal results;
- replay on a disconnected machine validates the same bundle bytes and root hash.

### M2. Production persistence and control plane

Deliver:

- PostgreSQL/Alembic append-only registry, record/revision, refs/edges, run/job/lease/event, review, release, archive and admission tables;
- object-store CAS adapter with conditional writes, integrity verification, versioning and recovery checks;
- durable job claiming, lease expiry, retries, idempotency, role policy, and audit log;
- FastAPI/OpenAPI service and independent acquisition/offline worker processes;
- real web display of jobs, events, files, and terminal results.
- a versioned reference benchmark profile with its hardware/container limits and numerical budgets for query latency at the 95th percentile, job/event propagation latency, bundle-verification throughput, supported concurrency, and per-attempt resource/cost ceilings.

Exit:

- empty-database upgrade and downgrade policy tests pass;
- filesystem and production adapters pass the same replay/contract suite;
- crash, lease expiry, duplicate submit, concurrent admission, atomic rollback, CAS/DB mismatch, and recovery tests pass;
- immutable rows cannot be updated/deleted through application or direct constrained transactions;
- no HTTP request executes long-running analysis.

### M3. Hardened grammar-complete arXiv intake

Deliver:

- a versioned `ArxivInputGrammar` and stable normalized/rejection result contract;
- complete URL/ID normalization and exact-version resolution;
- safe source acquisition, quarantine, extraction, macro preprocessing, PDF fallback, anchor alignment, source replacement, licensing, and source-package validation;
- implementation of the minimum rules in `paper-source-acquisition.md` as cross-record validators;
- visible source tree, acquisition evidence, anchors, and version history in the web demo.

Exit:

- modern/legacy IDs and `abs`/`pdf`/`e-print` forms resolve equivalently to an exact version;
- property-based and fuzz tests show parser totality over arbitrary strings, equivalence normalization, explicit/implicit version behavior, and stable rejection codes; live arXiv remains a separate smoke test;
- explicit version, omitted version, version upgrade, withdrawal, unavailable source, dataset miss, network failure, and PDF-only cases have tested semantics;
- the security corpus passes and canonical source packages replay without network access;
- every input accepted by the exact grammar revision produces a terminal intake attempt.

### M4a. Whole-paper structure and ScientificClaim production

Deliver:

- profile-required structure/component inventory with unclassified and ambiguous queues and a reviewed completeness claim;
- independent scope-freeze review;
- ScientificClaim extraction, attribution, decomposition, reconstruction evidence, and claim-level source lineage;
- real UI views for structure, coverage, source anchors, claims, and unresolved discovery.

Exit:

- post-freeze discoveries create new scope revisions and invalidate affected outputs;
- every frozen component has exactly one classified, ambiguous, ignored-with-policy, or blocked disposition;
- every generated claim reconstructs to its source span or is explicitly blocked, and every claim class/region required by the selected profile is discovered, ambiguous, ignored with policy, or blocked;
- the Stabilizerness and Shellworld fixtures are total-accounted for the M4a profile.

### M4b. Mathematical IR, residual semantics, and graph production

Deliver:

- native `MathClaimIR/2` producers and conservative V1 bindings;
- typed objects, quantifiers, domains, assumptions, units, approximations, conventions, normalization, and residual semantics;
- InferenceStep and multi-premise reasoning; candidate/accepted/rejected/conditional edges; blockers and unresolved frontier;
- canonical graph artifacts plus the distinct structure, provenance, interaction, claim-inference, dependency, and build projections;
- real UI graph switching, evidence panels, deep links, and exact snapshot pinning.

Exit:

- every graph node and edge has a schema-valid ontology type, producer, evidence, lifecycle state, and exact snapshot;
- each claimed DAG projection independently passes cycle/root/closure rules;
- command line, API, and UI return the same closure for a pinned snapshot;
- cross-paper cycles are preserved in the interaction graph and condensed, not silently deleted, for build order.

### M5. Formalization and independent verification axes

Deliver:

- sandboxed formal generation/build with pinned Lean environments;
- formal request/result, source/package/build hashes, declaration dependency, kernel, placeholder and axiom evidence;
- source-blind backtranslation, source↔claim↔IR↔formal alignment, assumption/units/approximation audit, and scientific assessment;
- dynamic validation for the existing formal examples, including Stabilizerness;
- UI comparison panes for source, IR, formal declaration, backtranslation, alignment, and assessment.

Exit:

- a toy paper succeeds from exact source through every M5 formal-generation and independent-axis record in a clean isolated toolchain; release, archive, and admission remain M6;
- a non-mathematical target yields `NOT_APPLICABLE` without fake proof artifacts;
- build failure, unresolved dependency, alignment failure, and scientific blocker each yield distinct complete terminal evidence;
- `sorry`, placeholders, undeclared axioms, stale environments, and target mismatches fail closed;
- formal build success never upgrades alignment or scientific status automatically.

### M6. Release, archive, review, and knowledge admission

Deliver:

- Root audit, mechanical certification, signed replay bundle, immutable archive, and ArchiveReceipt;
- independent per-entry review and policy-computed eligibility;
- atomic knowledge admission, conflict-preserving relations, snapshots, ingestion receipts, append-only withdrawal/revocation or supersession records, and exact query resolution; earlier releases and snapshots remain addressable;
- review queue, role/identity display, audit/certificate/archive views, and knowledge snapshot diff in the web demo.

Exit:

- a mixed package can be archived with zero admitted entries;
- selected entries can be admitted while rejected and blocked entries remain traceable;
- self-review, stale audit, changed bytes after review, invalid signature, partial transaction, conflicting concurrent admission, and policy mismatch cannot modify the knowledge snapshot;
- key rotation, key compromise/revocation, old-signature offline verification, review qualification, public rationale, and any policy-required quorum have passing positive and negative cases;
- every admitted entry traces to exact archive, review, contract, environment, source, and producer evidence;
- rejected knowledge and conflicting claims are preserved rather than erased.

### M7. Integrated public demo and offline verifier

Deliver:

- one production-shaped web surface: intake, stage ledger, artifact explorer, source tree, multiple graph views, formal/alignment panels, release/archive, review, and knowledge-query views;
- offline fixture mode using the same API payload schemas, not timers or page-specific mock formats;
- downloadable replay bundles and a standalone verifier;
- accessibility, responsive layout, browser E2E tests, and user-facing explanations of abbreviations and status semantics.

Exit:

- any E2E corpus release can be opened from a fresh browser and inspected down to exact refs, hashes, rights dispositions, and permitted bytes; every redistributable bundle can be downloaded and independently revalidated offline;
- no supported input is silently replaced with the precomputed demo paper;
- the UI distinguishes formal proof, alignment, scientific assessment, archive, and knowledge admission;
- the production deployment exposes the live API-backed V2 surface; GitHub Pages, if retained, exposes only clearly labelled offline fixtures/documentation and links to the live service.

### M8. Bulk V1 migration, performance, and public release

Deliver:

- dual-read/new-write rollout, dry-run inventories, quarantine for ambiguous IDs, shadow-read comparisons, migration/import receipts, and hash reconciliation;
- bulk import of eligible V1/pilot content without rewriting historical records;
- measured query/index performance, backup/restore and disaster-recovery runbooks;
- contributor developer environment, CODEOWNERS/branch protection guidance, release tags, signed artifacts, SBOM, compatibility and deprecation policy.

Exit:

- migration counts and hashes reconcile or have explicit quarantined exceptions;
- V1 and V2 shadow reads agree under the documented conservative projection;
- clean install, local compose deployment, backup/restore, and contributor pull-request workflow pass;
- the reference benchmark satisfies every numerical latency, throughput, concurrency, resource, and cost budget frozen in M2, or a reviewed budget revision explains and versions the change;
- the release candidate satisfies the Definition of Done below.

## 11. E2E and adversarial corpus

The acceptance corpus must include:

- the existing toy Lean and V2 contract fixture;
- Stabilizerness and Shellworld real repository cases;
- modern single-file and multi-file arXiv source packages;
- macro-, image-, and bibliography-heavy source;
- legacy arXiv ID and explicit/implicit version forms;
- later-version replacement and source/PDF temporal mismatch;
- unavailable source and PDF-only fallback;
- non-mathematical or non-formalizable content;
- a proof build failure and an alignment failure;
- an unresolved premise and a counterexample/conflict;
- a cross-paper cycle requiring SCC condensation;
- malicious traversal, symlink/hardlink, archive bomb, oversized input, redirect/SSRF, malformed encoding, and duplicate-path archives.

Online smoke tests are separate from deterministic offline fixtures. CI must not depend on live arXiv availability for its core pass.

## 12. CI and quality gates

Required checks, introduced as their owning milestone lands:

- format/lint, type checks, unit and contract tests;
- JSON Schema meta-validation, canonical hash tests, cross-record invariants, positive/negative fixtures;
- generated runtime-model, coverage-report, OpenAPI, and documentation drift checks;
- Alembic clean upgrade, integration tests, append-only constraints, crash/retry/idempotency/atomicity tests;
- deterministic replay and Merkle/CAS integrity tests;
- acquisition security corpus and sandbox policy tests;
- pinned Lean quick checks on pull requests and full clean rebuilds on a scheduled lane;
- browser, accessibility, API/CLI equivalence, and downloadable-bundle verification;
- secret, dependency, container and SBOM scans.

Code merge requires the relevant schema and implementation owners. Scientific knowledge admission additionally requires an independent scientific reviewer under the exact policy revision. A code reviewer is not automatically a scientific reviewer.

## 13. Version and change management

V2 work uses a dedicated `codex/` branch and small commits aligned with milestones. Only files intentionally produced by this plan are staged; pre-existing user changes remain untouched.

Independent version axes are recorded explicitly:

- paper work and exact paper version;
- contract bundle, schema, canonicalization, profile, policy and artifact catalog revisions;
- record identity and revision;
- plan, discovery, scope and scope-freeze decision;
- run and attempt;
- environment and producer version;
- Paper Agent release and replay-bundle root;
- knowledge snapshot and admission transaction;
- API version and database migration revision.

Planned release sequence:

- `v2.0.0-alpha.1`: M0–M1 contract kernel;
- `v2.0.0-alpha.2`: M1.5 local vertical slice;
- subsequent alpha tags for M2–M5;
- beta after M6 governance and admission invariants;
- release candidate after M7 public demo and offline verification;
- `v2.0.0` only after M8 migration and public-project gates.

Every milestone ends with a baseline report containing commit, contract bundle, test commands/results, known blockers, demo URLs or local commands, produced release roots, and the next acceptance gap.

## 14. Definition of Done for AgtXIv V2

V2 is complete only when all of the following are true:

1. Every input accepted by an exact published `ArxivInputGrammar` revision reaches a visible terminal intake attempt; every other string receives a stable typed rejection.
2. Every successfully frozen paper/profile has a reviewed `FrozenInventoryScope`.
3. Every required scope/family instance has exactly one valid artifact or policy-allowed typed terminal result. At `v2.0.0`, no required core-profile obligation may be satisfied by `UNSUPPORTED`, and every required core family has at least one positive producer case in the release corpus.
4. Every derived artifact and graph edge traces through immutable producer attempts to exact source bytes.
5. Every applicable formal target has independent generation, kernel-build, placeholder/axiom-audit, declaration-binding, alignment, and scientific-applicability results or terminal dispositions. A passed build has clean kernel evidence; alignment and scientific applicability may independently pass, fail, or remain blocked.
6. Root audit and mechanical certification cannot be self-issued, and the archive is independently replayable.
7. Knowledge admission is per entry, independently reviewed, atomic, conflict preserving, and traceable to an exact archive.
8. Release projections rebuild from canonical released bundles; knowledge and query projections rebuild from those bundles plus immutable admission/review transaction logs and snapshots, without changing hashes.
9. The API, CLI, web UI, and offline verifier agree on exact records, statuses, graph closures, and bundle roots.
10. The real grammar-driven input demo replaces timer-driven behavior while preserving legacy examples as labelled fixtures.
11. The E2E, adversarial, formal, migration, browser, accessibility, integrity, and recovery suites pass from a clean checkout.
12. The repository has the governance, security, licensing, contribution, release, and operational material expected of a professional open-source project.

## 15. Immediate execution slice

Execution begins with M0, then the smallest M1 contract kernel needed for M1.5. The first commits will:

1. record this roadmap and the audited baseline without modifying existing dirty V2 work;
2. add the reproducible Python project/validation entry point and CI baseline;
3. add ADRs for released authority, contract binding, Plan→Discovery→ScopeFreeze, split archive/admission gates, and native-core-plus-V1-binding `MathClaimIR`;
4. introduce the common exact-ref/immutable-envelope/typed-terminal contracts and the first machine-readable artifact catalog;
5. preserve current validator behavior behind compatibility tests;
6. implement the local CAS/replay-bundle seam and one exact-version intake walking slice before committing to the production database layout.

The stale Shellworld manifest is retained as evidence of the mutable-spec problem until a superseding immutable contract/run record is introduced. It will not be silently rewritten to make the old run appear reproducible.
