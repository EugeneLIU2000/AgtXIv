# AgtXIv V2 paper agentization

**Status:** normative architecture and contract specification; implemented coverage and targets are stated in Section 17.
**Version:** 2.0.0
**Authority:** authoritative for V2 paper-agent construction, Root Agent verification, release, knowledge ingestion, downstream queries, and migration. V1 remains authoritative for its frozen bounded, query-relative `ClaimMathBridge` / `BridgeAssessment` / legacy Root Agent compatibility surface.

## 1. Objective and authority boundary

V2 standardizes one exact theoretical-paper release as a query-independent Paper Agent. Its primary result is not a conversational answer and not a claim that the system “understood” the paper. It is an immutable, profile-relative package whose paper structure, claims, mathematical IR, dependencies, formalization dispositions, verification evidence, alignments, residual semantics, assessments, and unresolved frontier can be audited step by step.

The canonical order is:

```text
Exact Paper Release + AgentizationProfile + InventoryScope
→ source inventory and paper structure
→ claim inventory/decomposition and MathClaimIR
→ dependency and inference ordering
→ formalization disposition
→ formal verification and source/IR/formal alignment
→ residual/non-mathematical semantics and exact assessment selection
→ V2 Root Agent paper-level verification and release recommendation
→ independent mechanical ReleaseCertifier
→ Paper Agent Release
→ archival package ingestion
→ per-entry reusable admission
→ domain-qualified verification-aware Knowledge Base
→ downstream read-only query resolution
```

A query MAY trigger missing work, but MUST NOT define or narrow canonical profile, inventory, paper, claim, or verification scope.

## 2. V1 compatibility is frozen

V1 artifacts, schemas, bounded Root Agent outputs, and query-relative meaning are immutable compatibility inputs. In V1, a Root Agent conclusion remains a conservative answer for one bounded claim and query-relative dependency view. V2 does not reinterpret, rename, or upgrade that authority. A V2 adapter MAY reference a V1 record by exact revision and hash, but MUST NOT rewrite it, infer paper-level completion from it, or promote its status.

All new paper-level authority described below exists only in the V2 major namespace.

## 3. Exact inputs and canonical integrity

Construction MUST pin:

1. paper ID, exact source release ID, URI, local source-byte path, and SHA-256;
2. one exact `AgentizationProfile` revision and content hash;
3. one exact `InventoryScope` revision and hash, bound to the same release.

Every inventory entry has a stable ID, type, locator, source-component path, and exact byte hash. A title, mutable latest-version URL, embedding match, query, or prose description is not an exact input.

V2 uses the integer-only canonical JSON subset in `schemas/record-canonical-json-v1.profile.json`. Strings and keys are normalized to Unicode NFC and LF, normalized duplicate keys are rejected, object keys use Unicode code-point order, arrays preserve declared order, and SHA-256 is computed over compact UTF-8 JSON. For record $r$,

$$
\operatorname{RecordHash}(r)=\texttt{sha256:}\operatorname{SHA256}(\operatorname{CanonicalJSON}(r\setminus\{\texttt{content_hash}\})).
$$

For manifest $m$,

$$
\operatorname{ReleaseHash}(m)=\texttt{sha256:}\operatorname{SHA256}(\operatorname{CanonicalJSON}(m\setminus\{\texttt{content_hash},\texttt{release_hash}\})).
$$

Audit, certification, snapshots, ingestion receipts, and queries MUST bind exact IDs, revisions, content hashes, and release hashes transitively. Byte artifacts MUST be checked against real bytes; a renamed Lean or arbitrary file cannot satisfy a typed JSON record class.

## 4. Roles and non-self-certification

### 4.1 AgentizationCoordinator

The `AgentizationCoordinator` schedules construction and assembles an exact candidate manifest. It MAY invoke extraction, graph, formalization, verification, alignment, and assessment producers. It is not the V2 Root Agent and has no audit or certification authority.

### 4.2 V2 Root Agent

`Root Agent` in V2 means the accountable paper-level verification and audit authority. It is not a conversational answer generator. It consumes, without silently changing:

- the exact candidate `PaperAgentReleaseManifest`;
- exact profile, scope, source, artifact, dependency, and inference ordering;
- immutable evidence and assessment snapshots;
- terminal producer dispositions and unresolved blockers.

The Root Agent verifies in mandatory dependency order, selects exact assessment revisions when they exist, preserves `UNKNOWN`, `BLOCKED`, and `REFUTED`, records non-implications, and issues the scientific/profile release recommendation. Its immutable `ReleaseAuditRecord/2.0.0` is the accountable record.

The Root Agent MUST NOT generate claims, MathClaimIR, dependency/inference records, evidence, alignments, or assessments that it audits. It MUST NOT mechanically publish, sign, or certify its own package. Where a production record family is absent, it MUST record an explicit terminal frontier instead of manufacturing evidence or an assessment reference.

### 4.3 ReleaseCertifier

The `ReleaseCertifier` is an independent mechanical actor. It checks only the exact Root Agent audit and recommendation, manifest/audit hashes, policy conformance, role separation, and release binding. It does not repeat scientific judgment and cannot change frontier or assessment selection. `CERTIFIED` is valid only when the exact bound Root Agent audit says `RECOMMEND_PROFILE_RELEASE`, all four required mechanical checks pass, the release hash matches, and rejection reasons are empty. Otherwise certification is `REJECTED`, carries no certified release hash, preserves at least one failed check, and states one or more rejection reasons. Accountability therefore belongs to the Root Agent's immutable audit; certification is mechanical. Pairwise-distinct Coordinator, Root Agent, and Certifier identities prevent coordinator self-audit and Root Agent self-certification.

## 5. Profile-relative state machine

There is no paper truth Boolean. State is a vector of profile-relative gates, and a package may terminate with mixed dispositions.

| Order | State/gate | Completion condition | Permitted terminal result |
|---:|---|---|---|
| 1 | `SOURCE_INVENTORY` | exact paper and component bytes inventoried | passed or explicit blocker |
| 2 | `PAPER_STRUCTURE` | sections, appendices, statements, and source anchors accounted | passed, blocked, unknown |
| 3 | `CLAIM_INVENTORY_DECOMPOSITION` | required claim classes inventoried and decomposed | passed, blocked, refuted |
| 4 | `MATHCLAIM_EXTRACTION_IR` | applicable MathClaims have exact IR or terminal disposition | passed, blocked, not applicable |
| 5 | `DEPENDENCY_INFERENCE_GRAPH` | load-bearing dependencies and multi-premise inference order explicit | passed, blocked, unknown |
| 6 | `FORMALIZATION_DISPOSITION` | every formalization target has an exact request/result or terminal disposition | passed, blocked, failed, not applicable |
| 7 | `FORMAL_VERIFICATION` | kernel/build evidence independently recorded where required | passed, unknown, blocked, refuted |
| 8 | `SOURCE_IR_FORMAL_ALIGNMENT` | source↔IR↔formal↔backtranslation alignment assessed | passed, unknown, blocked, refuted |
| 9 | `RESIDUAL_NON_MATHEMATICAL_SEMANTICS` | physical, empirical, approximation, and prose residuals retained and assessed | passed, unknown, blocked, not applicable |
| 10 | `ASSESSMENT_SELECTION` | exact assessment revisions selected, or their absence is frontier | passed, unknown, blocked, refuted |
| 11 | `ROOT_AGENT_AUDIT` | ordered steps, exact refs, outcomes, frontier, non-implications, recommendation sealed | recommend or do not release |
| 12 | `CERTIFICATION` | independent mechanical checks bind the exact audit and release | certified or rejected |
| 13 | `RELEASE` | immutable package and ledger published by release service | released or not released |

For inventory $I$ and ledger $D$:

$$
\operatorname{Complete}(I,D)\iff \forall i\in I,\;\exists!d\in D\text{ with }d.\operatorname{entry}=i.
$$

Completion means exact accounting under the selected profile, not that all outcomes pass. `ADMITTED`, `CONDITIONAL`, `BLOCKED`, `DEFERRED`, `NOT_APPLICABLE`, and `FAILED` may coexist.

## 6. Root Agent verification record

`ReleaseAuditRecord/2.0.0` is extended rather than duplicated. Its `auditor.role` is exactly `V2_ROOT_AGENT`. It contains exactly the ten ordered producer-verification stages in Section 5. Every step carries:

- sequence and stage;
- one or more exact target refs;
- exact selected assessment refs, if any;
- exact evidence refs, if any;
- outcome;
- linked frontier IDs for `UNKNOWN`, `BLOCKED`, or `REFUTED` outcomes.

The unresolved frontier repeats stage, exact targets, disposition, and reason. Every linked frontier item's exact target-ref set MUST equal its step's target-ref set; partial equality is insufficient even for a multi-target step. The release recommendation MUST retain the complete unresolved frontier. Reordering, omission, duplication, target-set drift, or silent frontier deletion is invalid. The fixture deliberately marks paper structure, typed ScientificClaim inventory/decomposition, dependency/inference graph, kernel verification, alignment/backtranslation, residual semantics, and assessment selection as blocked or unknown frontier because those producer records are absent; it does not infer claim decomposition from MathClaimIR or fabricate missing evidence.

## 7. Formalization boundary and independent axes

`FormalizationRequest` pins one exact MathClaimIR component, in-scope source boundary and byte hash, requested artifacts, and formal environment descriptor. `FormalizationRecord` owns generation output only. `SUCCEEDED` means exactly the requested artifact kinds were generated with valid byte hashes; `PARTIAL` and `FAILED` have strict artifact/diagnostic rules.

These three statements are different and MUST NOT inherit status from one another:

1. **source-faithful paper assertion:** what the exact source asserts and whether an alignment assessment supports the representation;
2. **kernel-checked formal theorem:** what follows in one exact formal environment from encoded assumptions;
3. **scientific acceptance:** whether the claim is accepted for its stated scientific scope, model, approximation, evidence, and semantics.

Kernel success cannot promote source fidelity or scientific acceptance. Source preservation cannot imply theorem validity. Scientific acceptance cannot rewrite source text. `AssessmentRecord/2.0.0` is the only typed authority accepted by fields named `selected_assessment_refs`, axis `assessment_refs`, or `relation_assessment_ref`. Its assessment kind, axis or relation, exact target set, endpoints where applicable, and outcome MUST match the status it supports. `MathClaimIR` and `FormalizationRecord` can be assessment targets or evidence but can never satisfy an assessment reference. Every positive or negative assessed axis status—including source aligned/misaligned, kernel checked/rejected, and scientifically accepted/rejected—requires at least one compatible exact AssessmentRecord. `UNKNOWN`, `NOT_ASSESSED`, and `NOT_APPLICABLE` carry no assessment refs. The positive fixture manifests and admits one source-alignment AssessmentRecord; axes for which no typed assessment exists remain unknown, not assessed, or not applicable.

## 8. Release package and archival ingestion

Certification makes an immutable release eligible for archival ingestion. **Package Archive** stores the exact manifest, Root Agent audit, certificate, artifacts, ledger, and byte bindings as a package. Archival success does not admit any reusable entry. The Package Archive is a V2 target service in this repository: no production archive-receipt schema is claimed by the current contract slice.

**Reusable Entry Admission** is a separate, policy-governed transaction into a domain view. `KnowledgeIngestionReceipt/2.0.0` records this admission transaction, not archival storage. A package with mixed dispositions can be archived; only individually eligible candidates are admitted. Rejected and blocked candidates remain listed in the ingestion receipt and source package archive.

## 9. Admitted knowledge entry families

Entry-family vocabulary is not admission authority. This slice admits only the combinations in the following normative compatibility table; the validator checks the record discriminator, manifest artifact class, record-to-inventory binding field, inventory component kind, and entry family together.

| Typed record schema | Manifest artifact class | Exact record binding | Required inventory component kind | Admissible `entry_family` | Current status |
|---|---|---|---|---|---|
| `MathClaimIR/2.0.0` | `MATH_CLAIM_IR` | `source_inventory_entry_id` | `MATH_CLAIM` | `CONTRACT` | admissible |
| `FormalizationRecord/2.0.0` | `FORMALIZATION_RECORD` | `inventory_entry_id` | `FORMALIZATION_TARGET` | `FORMAL_ARTIFACT` | admissible |
| `AssessmentRecord/2.0.0` | `ASSESSMENT_RECORD` | `source_inventory_entry_id` | `MATH_CLAIM` | `ASSESSMENT` | admissible |
| no typed record class in this slice | none | none | not defined | `SOURCE_CLAIM`, `DEFINITION`, `INFERENCE_EDGE`, `EVIDENCE` | reserved future vocabulary; not currently admissible |

An admissible AssessmentRecord is therefore a real manifest `RECORD` artifact with its exact schema URI, ID, revision, content hash, path, inventory binding, ledger disposition, ingestion candidate, and resulting `ASSESSMENT` entry. `MathClaimIR` and `FormalizationRecord` MUST NOT be relabelled to another family. Adding a future family requires a typed record schema and an explicit new compatibility-table row; an enum label alone is insufficient.

Every entry MUST retain:

- exact manifest, certificate, Root Agent audit, inventory scope, record, paper release, source locator, component path, and source hashes;
- `domain_id`, typed family, inventory component, scope text, and assumptions;
- formal environment descriptor when applicable;
- exact alignment refs when applicable;
- independent source-assertion, formal-verification, and scientific-acceptance axes, each with its own assessment refs;
- entry admission status.

No package-level, formal, source, or acceptance status may be flattened into another.

## 10. Domain-qualified immutable views and cross-paper relations

A `KnowledgeIndexSnapshot` is an immutable view identified by `domain_id`, revision, and content hash. It binds all exact source packages and inventory scopes represented by the view. Its policy preserves all assessed conflicts and permits semantic deduplication only through exact assessed relations.

Cross-paper reuse is represented by separately assessed exact relations such as `EQUIVALENT`, `SPECIAL_CASE`, `GENERALIZES`, `INCOMPARABLE`, `CONFLICTING`, `CORRECTS`, `SUPPORTS`, `QUALIFIES`, and `REFUTES`. Every relation has a `relation_id` unique across the snapshot independently of whole-object uniqueness, names two distinct endpoint entries, and binds an exact compatible relation-assessment revision whose endpoints and exact target-record set match. The endpoints' exact provenance MUST identify different `(paper_id, release_id)` pairs; a same-entry or same-paper-release edge is not a cross-paper relation. Query closure compares relation-ID multiplicities and MUST NOT hide duplicate IDs by converting them to a set. Text equality, normalized text, vector proximity, citation, shared theorem names, or embeddings MUST NOT establish equivalence, correction, conflict, or deduplication.

Record/package supersession means a newer immutable record or release replaces an earlier operational version for a declared purpose. It does not scientifically correct or refute the earlier claim. `CORRECTS` and `REFUTES` are scientific relations requiring separate assessments; old records remain addressable.

Formal cross-paper reuse additionally requires an exact environment-compatibility or import receipt: toolchain, dependency commits, declarations, namespaces, assumptions, and build result. Matching theorem text is insufficient.

## 11. Atomic knowledge ingestion receipt

`KnowledgeIngestionReceipt/2.0.0` binds transaction identity, domain, exact profile, manifest, Root Agent audit, certificate, before snapshot, after snapshot, and policy. Its explicit `candidate_set` is the deterministic transaction universe: every item binds one candidate ID, supported family, exact manifested record reference, and exact record-bound inventory entry. Accepted, rejected, and blocked lists are dispositions over that universe; accepted candidates additionally bind the resulting knowledge entry.

Candidate IDs MUST be unique in `candidate_set` and globally unique and disjoint across accepted, rejected, and blocked lists. Projecting every disposition to `(candidate_id, entry_family, record_ref, inventory_entry_id)` MUST produce an exact exhaustive partition of `candidate_set`: omission, invention, or changed binding is invalid. Under `atomicity: REQUIRED` and `partial_mutation: FORBIDDEN`, `COMMITTED` means the after snapshot is exactly the before snapshot plus all and only accepted entry additions and, when additions exist, the exact package and scope bindings. Every prior entry, package binding, scope ref, relation, environment receipt, domain, and view policy is preserved byte-for-byte at record level; rejected and blocked candidates add nothing. `ABORTED` still partitions the same exact universe, requires an empty accepted list, and binds the identical exact before/after snapshot reference; every candidate must therefore be rejected or blocked. The vertical fixture commits from an exact empty genesis snapshot, while the contract and validator also support nonempty before snapshots. A receipt not bound to the exact manifest/certificate/audit/snapshots or exact candidate universe is invalid.

## 12. Conflict-preserving queries and incremental lifecycle

`PACKAGE_BACKED` queries are read-only over exact certified releases and exact knowledge snapshots. They MUST return `returned_relation_ids` equal to the complete relation set relevant to that exact snapshot. For `CONFLICTING`, `INCOMPARABLE`, `CORRECTS`, `QUALIFIES`, and `REFUTES`, both endpoint entries' exact records MUST also remain in `returned_record_refs`; returning only the relation label or preferred endpoint is invalid. Query ranking MAY order results but MUST NOT suppress conflict records or collapse independent axes.

`PROVISIONAL_FAST_PATH` is non-authoritative. It may produce candidates and register or link a canonical intake, but all mutation, publication, admission, and promotion effects are forbidden.

A query may reveal a knowledge gap, request a stronger profile, encounter environment incompatibility, or target a changed source version. These events MAY trigger incremental, query-independent agentization and a new release/index revision. The resulting canonical work uses the complete selected profile and scope; the triggering query never narrows them.

## 13. Non-implications

Neither profile completion, Root Agent recommendation, mechanical certification, archival ingestion, nor entry admission implies whole-paper truth, whole-paper understanding, scientific acceptance of every claim, kernel verification of every formal artifact, source/formal alignment, absence of conflict, or admission of every package artifact.

## 14. Machine-checkable invariants

A conforming validator MUST reject at least:

1. stale canonical, release, or byte hashes; unresolved/mistyped exact refs; duplicate record identities;
2. query-controlled canonical scope, unknown V2 discriminators, or aggregate `verified` fields;
3. `Root Agent = AgentizationCoordinator`, `Root Agent = ReleaseCertifier`, or any role/identity overlap;
4. out-of-order, duplicate, or missing Root Agent stages;
5. unresolved step outcomes without matching frontier, or a recommendation that drops frontier;
6. a certificate not binding the exact Root Agent audit/recommendation and release;
7. formal-generation success presented as kernel verification, source fidelity, or scientific acceptance;
8. an index not bound to exact manifest/certificate/audit/inventory records;
9. non-atomic or partial mutation under required atomicity, or a candidate disposition that omits, invents, duplicates, or changes an exact `candidate_set` member;
10. entries lacking domain, family, exact provenance, scope/assumptions, component, environment/alignment where applicable, or separated status axes; any record-schema/artifact-class/component/family mismatch;
11. a duplicate-ID, self, same-paper-release, untyped, or incompatible cross-paper relation or semantic deduplication;
12. package supersession presented as scientific correction/refutation;
13. environment reuse without an exact compatibility/import receipt;
14. query conflict suppression;
15. a query returning records not admitted by its exact snapshot.

Schema validation is necessary but not sufficient; cross-record validation is mandatory.

## 15. Object decision table

| Object | Decision in V2 | Reason |
|---|---|---|
| V1 `ScientificClaim`, `ClaimMathBridge`, `BridgeAssessment` | **keep/freeze** in V1 namespace | preserve bounded query-relative semantics |
| V1 Root Agent output | **keep/freeze** as legacy downstream input | not paper-level V2 authority |
| V2 `AgentizationCoordinator` | **keep distinct** | schedules/proposes but cannot audit |
| `ReleaseAuditRecord/2.0.0` | **extend/rename semantically** to Root Agent verification record; keep schema name | avoids duplicate audit authority |
| standalone `ReleaseAuditor` role | **remove from V2 role model** | V2 Root Agent owns accountable scientific/profile audit |
| `ReleaseCertifier` | **keep/narrow** | independent mechanical certification only |
| `PaperAgentReleaseManifest` | **keep** as exact candidate/release package projection | package identity and disposition ledger |
| `FormalizationRecord` | **keep/narrow** to generation | prevents status inheritance |
| `KnowledgeIndexSnapshot` | **extend/move** to domain-qualified immutable view | cross-paper provenance and independent axes |
| Package Archive | **add as target service** | stores exact certified packages; no archive receipt is implemented in this slice |
| `KnowledgeIngestionReceipt` | **add for reusable admission** | records atomic entry admission, not package archival storage |
| query-time canonical writes | **remove/forbid** | query is downstream and read-only |
| embedding/text dedup authority | **remove/forbid** | exact assessed relations are required |

## 16. Phased implementation blueprint

1. **Contract slice (implemented here):** strict schemas, canonical hashes, exact fixture chain, Root Agent ordered audit, mechanical certificate, domain snapshot, genesis, atomic ingestion receipt, adversarial validator tests, and architecture artifact.
2. **Whole-paper producers (target):** production source inventory, paper structure, ScientificClaim/decomposition, dependency/inference graph, residual semantics, evidence, alignment, assessment, and formal-verification registries.
3. **Operational release service (target):** authenticated role separation, immutable storage, cryptographic signing, release publication, archival package service, and atomic transaction backend.
4. **Cross-paper lifecycle (target):** relation-assessment workflows, domain governance, environment compatibility/import receipts, conflict-preserving retrieval, supersession/correction policies, and incremental revision triggers.
5. **Migration and scale (target):** exact V1 adapters, multi-domain views, production profile catalog, telemetry, and independently reviewed release/ingestion operations.

Each phase MUST preserve earlier immutable artifacts and MUST NOT infer completion of a later phase.

## 17. Contract locations and implementation status

Schemas live under `schemas/v2/`; the vertical family is under `fixtures/v2-paper-agentization/`; `tools/validate_v2_paper_agentization.py` performs strict schema, hash, byte, role, audit-order, frontier, provenance, axis, atomic-ingestion, and query checks.

**Implemented:** twelve V2 schema discriminators, including typed AssessmentRecord authority; fourteen fixture records including a manifested/admitted source-alignment assessment, an empty domain genesis, and an atomic ingestion receipt with an exact candidate universe; ordered Root Agent audit and mixed unresolved frontier; mechanical certification; domain-qualified index entries with independent axes and strict entry-family compatibility; cross-paper relation integrity checks; canonical/transitive hashing; adversarial tests; and synchronized architecture JSON/HTML.

**V2 targets, not claimed production capabilities:** whole-paper extraction and graph producers; independent formal verification, backtranslation, source/IR/formal alignment, scientific and residual-semantics assessments; authenticated release operations and signing; archival storage and transactional knowledge services; cross-paper relation assessment; environment compatibility/import receipts; conflict-preserving production query engine; and complete V1 migration adapters.
