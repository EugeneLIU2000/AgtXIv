# AgtXIv V3 schema v0.0 — complete contract reference

Status: experimental contract **0.0.0**, implementing the **V3 architecture**. The folder name is the user-selected `schema v0.0`; it is not a historical V0 architecture. JSON Schema dialect: Draft 2020-12. Schema titles, fields, enumerations and descriptions are English. The field-complete Chinese companion is [SCHEMA.zh-CN.md](SCHEMA.zh-CN.md).

Read the model as: exact paper → source claims and scientific context → revisable mathematical argument and fixed MathClaimIR → optional profile-required formal checking → six distinct evidence assessments → baseline-relative contributions and use-specific reuse → independently audited release → individually admitted knowledge → read-only queries and incremental review.

Schema validity establishes **shape only**. Exact bytes, references, complete frozen obligations, scope discharge, review independence, scientific alignment, real execution, conflict preservation and atomic transactions require cross-record validation or independent evidence. Every implementation report must distinguish contract coverage, tested mechanism, and scientific/operational acceptance. No fixture is a scientific approval.

## Shared envelope and identity

All records use a closed envelope and closed payload. Unknown properties and unknown record types are rejected; extension requires a new schema version. `record_id` identifies a lineage, `revision` fixes its version, and `content_hash` binds the complete record except that field. Reused canonicalization is NFC/LF normalized, integer-only JSON with exact safe-integer bounds, duplicate-key rejection and sorted keys. Floating-point scientific quantities are represented as exact strings with explicit units and interpretation. Raw source bytes are never normalized before artifact hashing.

The record discriminator selects an exact schema from the offline bundle manifest. `schema_bundle_hash` binds that manifest; `policy_ref` binds a supplied immutable AuthorityPolicy, except its explicit bootstrap case. Schema lookup never fetches the network. `input_refs` and all payload references form a supplied immutable record graph; unresolved or mismatched identities cannot be substituted by names or paths.

`data_class` records evidence origin: SYNTHETIC examples, RESEARCH experimental material or OBSERVED real input/run records. OBSERVED does not mean scientifically accepted. Actor identity fields are assertions until independently checked against a trusted runtime context. Local role separation is not institutional independence.

## Six independent questions

1. source_fidelity — whether the representation matches the exact source assertion;
2. mathematical_correctness — whether the exact conclusion follows from its explicit mathematical premises;
3. formal_alignment — whether the formal statement preserves the intended target;
4. semantic_applicability — whether objects, models, approximations and observables correspond to the intended scientific system;
5. empirical_support — what observations support or oppose the scientific assertion;
6. computational_reproducibility — whether the specified load-bearing computation can be regenerated.

Applicability, assessed result, and execution disposition are separate. An unsuccessful program is not a mathematical counterexample. An unattempted check is not automatically inapplicable. A passed formal statement does not itself support a source claim without explicit alignment. Conflicting assessments remain independently available.

## Public record dependency order

SourceSnapshot → SourceSpan / PaperStructure → ScientificClaim / SemanticContext / MathClaimIR → argument nodes, contexts and inferences → ArgumentSnapshot → review and FormalizationPacket → evidence and assessments → baseline-relative relations, contribution and reuse → release manifest → audit → certificate → release → admission decision → new knowledge snapshot → ingestion receipt.

A baseline may point to an earlier knowledge snapshot. A new snapshot points only to already-created admission decisions. Decisions bind the prior snapshot, never their unknown future snapshot. This avoids circular identity hashing. Later challenges, revised assessments and impact records append new records; they do not rewrite their targets.

## Common value structures


### RecordRef

An exact immutable record reference, never a latest-version selector.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `record_type` | `agtxiv.v3.processing-profile/0.0.0` / `agtxiv.v3.authority-policy/0.0.0` / `agtxiv.v3.source-snapshot/0.0.0` / `agtxiv.v3.source-span/0.0.0` / `agtxiv.v3.source-transformation/0.0.0` / `agtxiv.v3.paper-structure/0.0.0` / `agtxiv.v3.agentization-plan/0.0.0` / `agtxiv.v3.inventory-discovery/0.0.0` / `agtxiv.v3.scope-decision/0.0.0` / `agtxiv.v3.frozen-scope/0.0.0` / `agtxiv.v3.obligation-disposition/0.0.0` / `agtxiv.v3.scientific-claim/0.0.0` / `agtxiv.v3.derived-claim/0.0.0` / `agtxiv.v3.claim-component-map/0.0.0` / `agtxiv.v3.semantic-context/0.0.0` / `agtxiv.v3.definition/0.0.0` / `agtxiv.v3.math-claim/0.0.0` / `agtxiv.v3.assumption-context/0.0.0` / `agtxiv.v3.argument-node/0.0.0` / `agtxiv.v3.inference-step/0.0.0` / `agtxiv.v3.proof-plan/0.0.0` / `agtxiv.v3.dependency-binding/0.0.0` / `agtxiv.v3.challenge/0.0.0` / `agtxiv.v3.challenge-disposition/0.0.0` / `agtxiv.v3.argument-snapshot/0.0.0` / `agtxiv.v3.argument-review/0.0.0` / `agtxiv.v3.upstream-import/0.0.0` / `agtxiv.v3.work-attempt/0.0.0` / `agtxiv.v3.formal-environment/0.0.0` / `agtxiv.v3.formalization-packet/0.0.0` / `agtxiv.v3.formalization-attempt/0.0.0` / `agtxiv.v3.formal-check/0.0.0` / `agtxiv.v3.backtranslation/0.0.0` / `agtxiv.v3.alignment-assessment/0.0.0` / `agtxiv.v3.empirical-evidence/0.0.0` / `agtxiv.v3.reproduction-record/0.0.0` / `agtxiv.v3.axis-assessment/0.0.0` / `agtxiv.v3.status-view/0.0.0` / `agtxiv.v3.baseline-snapshot/0.0.0` / `agtxiv.v3.relation-assessment/0.0.0` / `agtxiv.v3.contribution-delta/0.0.0` / `agtxiv.v3.reuse-decision/0.0.0` / `agtxiv.v3.environment-check/0.0.0` / `agtxiv.v3.frontier-item/0.0.0` / `agtxiv.v3.release-manifest/0.0.0` / `agtxiv.v3.release-audit/0.0.0` / `agtxiv.v3.release-certificate/0.0.0` / `agtxiv.v3.paper-release/0.0.0` / `agtxiv.v3.archive-receipt/0.0.0` / `agtxiv.v3.admission-decision/0.0.0` / `agtxiv.v3.knowledge-snapshot/0.0.0` / `agtxiv.v3.ingestion-receipt/0.0.0` / `agtxiv.v3.event/0.0.0` / `agtxiv.v3.event-checkpoint/0.0.0` / `agtxiv.v3.impact-analysis/0.0.0` / `agtxiv.v3.revision-record/0.0.0` / `agtxiv.v3.legacy-binding/0.0.0` / `agtxiv.v3.query-receipt/0.0.0` / `agtxiv.v3.evaluation-report/0.0.0` / `agtxiv.v3.source-request/0.0.0` / `agtxiv.v3.source-acquisition/0.0.0` / `agtxiv.v3.evidence-protocol/0.0.0` / `agtxiv.v3.work-completion/0.0.0` / `agtxiv.v3.counterexample/0.0.0` | yes | Exact registered record discriminator. |
| `record_id` | string | yes | Stable record lineage identity. |
| `revision` | integer | yes | Exact immutable revision. |
| `content_hash` | string | yes | Canonical complete-record hash excluding only content_hash. |

### ArtifactRef

Identity of supplied raw bytes; a locator is not integrity evidence.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `artifact_id` | string | yes | Stable artifact identity. |
| `sha256` | string | yes | SHA-256 of unmodified raw bytes. |
| `byte_size` | integer | yes | Exact byte length. |
| `media_type` | string | yes | Declared media type. |
| `path_hint` | string | no | Relative display locator, never an authority selector. |

### Producer

Attributed producer and its visible execution boundary.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `principal_id` | string | yes | Actual principal identity asserted by the execution record. |
| `role` | `SOURCE_PRODUCER` / `CLAIM_PRODUCER` / `ARGUMENT_PRODUCER` / `ARGUMENT_REVIEWER` / `FORMALIZER` / `FORMAL_CHECKER` / `BACKTRANSLATOR` / `ALIGNMENT_REVIEWER` / `SCIENTIFIC_REVIEWER` / `SCOPE_REVIEWER` / `PAPER_AUDITOR` / `CERTIFIER` / `ARCHIVE_SERVICE` / `ADMISSION_REVIEWER` / `KNOWLEDGE_SERVICE` / `QUERY_SERVICE` / `COORDINATOR` / `MAINTAINER` / `MIGRATION_SERVICE` | yes | Role used for this operation. |
| `actor_kind` | `HUMAN` / `AGENT` / `MECHANICAL_SERVICE` | yes | Producer class, not an assurance level. |
| `identity_assurance` | `DECLARED` / `LOCALLY_ATTESTED` / `EXTERNALLY_ATTESTED` | yes | How identity was established; strings alone are not authentication. |
| `execution_id` | string | yes | Exact attributed execution. |
| `model` | string | no | Model identifier when an agent is used. |
| `visible_input_refs` | array<RecordRef> | yes | Exact records visible to the actor. |
| `identity_evidence` | array<ArtifactRef> | yes | Independently supplied identity evidence. |

### ReviewContext

Declared independence plus exact reviewed input; a runtime must verify it.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `reviewed_refs` | array<RecordRef> | yes | Exact records assessed by this decision. |
| `producer_principal_ids` | array<string> | yes | All actual producers of the reviewed content. |
| `independence` | `UNESTABLISHED` / `ROLE_SEPARATED` / `INDEPENDENTLY_ATTESTED` | yes | Review boundary, not a truth guarantee. |
| `conflicts` | array<string> | yes | Known conflicts of interest or shared-model limitations. |
| `method` | string | yes | Public review procedure. |
| `evidence_refs` | array<RecordRef> | yes | Evidence supporting the review. |

### Condition

A material condition with provenance and interpretation.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `condition_id` | string | yes | Stable condition identity within its parent record. |
| `statement` | string | yes | Complete condition including range and quantifiers. |
| `origin` | `SOURCE_EXPLICIT` / `SOURCE_RECONSTRUCTED` / `AGENT_ADDED` / `IMPORTED` | yes | Attribution of the condition. |
| `source_span_refs` | array<RecordRef → source-span> | yes | Exact supporting source spans. |

### SourceUnit

An inventoried source object and its activity in the selected rendering.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `unit_id` | string | yes | Source inventory item identity. |
| `relative_path` | string | yes | Canonical relative path. |
| `artifact` | ArtifactRef | yes | Exact unmodified source bytes. |
| `activity` | `ACTIVE` / `DORMANT` / `UNKNOWN` | yes | Participation in the designated rendering. |
| `kind` | `TEX` / `PDF` / `BIBLIOGRAPHY` / `FIGURE` / `TABLE` / `CODE` / `DATA` / `OTHER` | yes | Source object role. |

### StructureEdge

Document structure only, not mathematical inference.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_unit_id` | string | yes | Including or containing source unit. |
| `target_unit_id` | string | yes | Included or contained source unit. |
| `relation` | `INCLUDES` / `CONTAINS` / `REFERENCES` / `CAPTION_OF` | yes | Document relation. |
| `activity` | `ACTIVE` / `DORMANT` / `UNKNOWN` | yes | Static activity observation. |
| `locator` | string | yes | Location of the relation in the source. |

### Obligation

One immutable processing obligation in a frozen denominator.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `obligation_id` | string | yes | Identity preserved across attempts. |
| `target_refs` | array<RecordRef> | yes | Exact known targets; empty only for unresolved discovery items. |
| `source_unit_ids` | array<string> | yes | Source units covered by the obligation. |
| `stage` | `SOURCE` / `INVENTORY` / `CLAIM` / `ARGUMENT` / `FORMAL` / `ALIGNMENT` / `SEMANTICS` / `EMPIRICAL` / `COMPUTATION` / `CONTRIBUTION` / `RELEASE` | yes | Required work stage. |
| `requirement` | `ACCOUNT_FOR` / `SUCCESS_REQUIRED` | yes | Accounting versus a required successful result. |
| `applicable_axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | yes | Axes to which this work is relevant. |
| `reason` | string | yes | Why this obligation belongs in scope. |

### Component

An independently attributable part of a source proposition.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `component_id` | string | yes | Component identity within the claim. |
| `text` | string | yes | Complete component meaning. |
| `role` | `CONCLUSION` / `ASSUMPTION` / `DEFINITION` / `MODEL` / `APPROXIMATION` / `EVIDENCE` / `ATTRIBUTION` / `LIMITATION` | yes | Semantic role. |
| `source_span_refs` | array<RecordRef → source-span> | yes | Exact source anchors. |

### ComponentMapping

Total mathematical, semantic and unresolved accounting for one component.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `component_id` | string | yes | Exact component in the source claim. |
| `math_refs` | array<RecordRef → math-claim> | yes | Mathematical representations. |
| `semantic_refs` | array<RecordRef → semantic-context> | yes | Scientific meanings retained separately. |
| `evidence_refs` | array<RecordRef> | yes | Evidence associated with this component. |
| `disposition` | `MAPPED` / `RESIDUAL` / `UNRESOLVED` / `NON_CLAIM` | yes | Component disposition. |
| `residual` | string | yes | Exact meaning still outside the mapped representations. |

### MathObject

A mathematical carrier with definitions, units and conventions.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `symbol` | string | yes | Fully scoped symbol. |
| `object_type` | string | yes | Mathematical carrier or type. |
| `definition_refs` | array<RecordRef → definition> | yes | Exact imported definitions. |
| `unit` | string | yes | Unit, or empty for a dimensionless object. |
| `convention` | string | yes | Normalization and interpretation convention. |

### Quantifier

Ordered binder; order is semantically significant.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `kind` | `FORALL` / `EXISTS` / `UNIQUE_EXISTS` | yes | Quantifier kind. |
| `variable` | string | yes | Bound variable name. |
| `domain` | string | yes | Quantified domain with restrictions. |

### FormalDeclaration

An exact declaration observed in one formal environment.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | Fully qualified declaration name. |
| `statement` | string | yes | Elaborated or inspected declaration type. |
| `source_artifact` | ArtifactRef | yes | Exact declaration source bytes. |
| `is_axiom` | boolean | yes | Whether the declaration itself is an axiom. |
| `axioms` | array<string> | yes | Transitive axiom names reported by the checker. |
| `dependencies` | array<string> | yes | Exact declaration dependency names in the fixed environment. |

### ParameterComparison

Explicit comparison of a reusable result with its target use.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `dimension` | `OBJECT` / `DEFINITION` / `QUANTIFIER` / `ASSUMPTION` / `CONCLUSION` / `UNIT` / `CONVENTION` / `REGIME` / `EVIDENCE` / `ENVIRONMENT` | yes | Compared dimension. |
| `source_value` | string | yes | Meaning on the reusable side. |
| `target_value` | string | yes | Meaning required by the target. |
| `relation` | `EQUIVALENT` / `SOURCE_STRONGER` / `TARGET_STRONGER` / `INCOMPARABLE` / `UNKNOWN` | yes | Assessed comparison, not text similarity. |
| `witness_refs` | array<RecordRef> | yes | Evidence for the comparison. |

### AdmissionItem

One exact candidate and its admission decision.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `candidate_ref` | RecordRef | yes | Exact proposed knowledge record. |
| `decision` | `ACCEPT` / `REJECT` / `BLOCK` | yes | Admission disposition, not truth. |
| `assessment_refs` | array<RecordRef → axis-assessment, relation-assessment, argument-review> | yes | Relevant exact assessments. |
| `reason` | string | yes | Public admission rationale and conditions. |

### ImpactTarget

One affected target with a typed and axis-limited reason.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_ref` | RecordRef | yes | Exact affected target. |
| `axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | yes | Axes needing review. |
| `proof_plan_ref` | nullable RecordRef → proof-plan | yes | Affected proof route, if applicable. |
| `reason` | string | yes | Why this target needs re-evaluation. |

### QueryAssertion

Public answer text backed by exact records.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `text` | string | yes | One load-bearing assertion in the answer. |
| `support_refs` | array<RecordRef> | yes | Exact records supporting the wording. |
| `limitations` | array<string> | yes | Scope and unresolved qualifications. |

### Metric

A measured value with a frozen denominator and comparison scope.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | Metric name, never a paper truth or quality score. |
| `measurement_status` | `NOT_MEASURED` / `MEASURED` / `UNDEFINED` | yes | Whether a value was observed and a ratio can be defined. |
| `numerator` | nullable integer | yes | Observed count; null when not measured. |
| `denominator` | nullable integer | yes | Frozen eligible count; null when unknown and zero only for a measured empty set. |
| `unit` | string | yes | Measurement unit. |
| `method` | string | yes | Measurement protocol and scope. |

### PdfRegion

A page-local locator in an exact PDF, not a fabricated raw-byte text span.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `page_index` | integer | yes | Zero-based page index. |
| `x0` | string | yes | Exact decimal left coordinate in normalized page units. |
| `y0` | string | yes | Exact decimal top coordinate. |
| `x1` | string | yes | Exact decimal right coordinate. |
| `y1` | string | yes | Exact decimal bottom coordinate. |

## Record envelope

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `record_type` | string | yes | Exact discriminator of the selected record family. |
| `record_id` | string | yes | Stable identity; semantic changes may require a new lineage. |
| `revision` | integer | yes | Exact immutable version within the lineage. |
| `created_at` | string | yes | Attributable creation time in UTC. |
| `data_class` | `RESEARCH` / `OBSERVED` / `SYNTHETIC` | yes | Evidence origin, not an authority status. |
| `schema_bundle_hash` | string | yes | Exact manifest hash of the schema bundle. |
| `producer` | Producer | yes | Actual attributed producer and execution boundary. |
| `policy_ref` | nullable RecordRef → authority-policy | yes | Exact authority policy; null only for its bootstrap record. |
| `input_refs` | array<RecordRef> | yes | Explicit exact inputs used to construct this record. |
| `content_hash` | string | yes | Canonical record hash excluding this one field only. |
| `payload` | object | yes | Closed family-specific fields documented below. |

## ProcessingProfile

Versioned work obligations, including required success and permitted unresolved work.

Schema: [processing-profile.schema.json](processing-profile.schema.json). Roadmap: P0.2, P1.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `name` | `V3_SOURCE_MAP` / `V3_ARGUMENT_AUDIT` / `V3_FORMAL_SUPPORT` | yes | Named V3 processing profile. |
| `required_stages` | array<string> | yes | Stages every applicable scope must account for. |
| `success_required_stages` | array<string> | yes | Stages whose required targets must actually succeed. |
| `required_axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | yes | Applicable axes whose assessments are required. |
| `allowed_terminal_outcomes` | array<string> | yes | Explicit permitted unresolved execution outcomes. |
| `empirical_requirement` | `ACCOUNT_FOR` / `REVIEW_REQUIRED` | yes | Empirical work obligation. |
| `computation_requirement` | `ACCOUNT_FOR` / `REPRODUCTION_REQUIRED` | yes | Computational work obligation. |
| `non_implications` | array<string> | yes | What completion of this profile does not establish. |

## AuthorityPolicy

Versioned authority, separation and review requirements.

Schema: [authority-policy.schema.json](authority-policy.schema.json). Roadmap: P0.1, P0.3, P1.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `charter_identity` | `AgtXIv-Charter/1.0` | yes | Charter identity used as the design basis. |
| `charter_state` | `PROPOSED` / `ADOPTED` | yes | Actual ratification state under governance. |
| `ratification_commit` | nullable string | yes | Qualifying adoption commit only after ratification. |
| `minimum_identity_assurance` | `LOCALLY_ATTESTED` / `EXTERNALLY_ATTESTED` | yes | Minimum runtime identity evidence for authoritative decisions. |
| `separated_role_pairs` | array<string> | yes | Explicit incompatible roles on the same assessed artifact. |
| `human_review_triggers` | array<string> | yes | Scientific or governance conditions requiring a human reviewer. |
| `allowed_principal_ids` | array<string> | yes | Principals authorized in this exact policy scope. |

## SourceSnapshot

Immutable source bytes and acquisition boundary for one paper version.

Schema: [source-snapshot.schema.json](source-snapshot.schema.json). Roadmap: P2.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `paper_id` | string | yes | Exact bibliographic work identifier. |
| `paper_version` | string | yes | Explicit source version, never latest. |
| `source_uri` | string | yes | Acquisition location retained as provenance. |
| `acquired_at` | string | yes | Time the bytes were acquired. |
| `acquisition_ref` | nullable RecordRef → source-acquisition | yes | Exact acquisition report when available; local legacy inputs may have no such history. |
| `acquisition_method` | `ARXIV_SOURCE` / `ARXIV_PDF` / `LOCAL_IMPORT` / `OTHER_EXACT_SOURCE` | yes | How these bytes were obtained. |
| `units` | array<SourceUnit> | yes | Complete supplied source inventory. |
| `archive` | nullable ArtifactRef | yes | Original source archive if available. |
| `missing_material` | array<string> | yes | Source material known to be absent. |
| `rights_status` | `KNOWN` / `UNRESOLVED` / `RESTRICTED` | yes | Recorded availability and reuse-rights boundary. |
| `rights_note` | string | yes | Public source and redistribution conditions. |

## SourceSpan

Exact source occurrence used to attribute a proposition or condition.

Schema: [source-span.schema.json](source-span.schema.json). Roadmap: P2.2, P2.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | yes | Exact source snapshot containing this occurrence. |
| `artifact` | ArtifactRef | yes | Raw source bytes containing the occurrence. |
| `locator_kind` | `RAW_TEXT_BYTES` / `PDF_REGION` / `TRANSFORMED_TEXT` | yes | Exact source occurrence representation. |
| `byte_start` | nullable integer | yes | Inclusive zero-based byte offset; null for a PDF page region. |
| `byte_end` | nullable integer | yes | Exclusive byte offset, null for a PDF page region. |
| `span_sha256` | nullable string | yes | Exact selected text-byte digest; null for a PDF page region. |
| `pdf_region` | nullable PdfRegion | yes | Page and box for a PDF occurrence. |
| `transformation_ref` | nullable RecordRef → source-transformation | yes | Exact mapping when using derived text. |
| `locator` | string | yes | Human-readable page, line or label. |
| `activity` | `ACTIVE` / `DORMANT` / `UNKNOWN` | yes | Occurrence participation in the chosen source rendering. |

## SourceTransformation

An auditable mapping from raw material to a derived representation.

Schema: [source-transformation.schema.json](source-transformation.schema.json). Roadmap: P2.2.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | yes | Exact source input. |
| `inputs` | array<ArtifactRef> | yes | Unmodified input bytes. |
| `outputs` | array<ArtifactRef> | yes | Derived bytes with distinct identities. |
| `method` | string | yes | Extraction, expansion or rendering procedure. |
| `environment` | string | yes | Fixed tool and configuration identity. |
| `mapping_artifact` | ArtifactRef | yes | Explicit source-to-output location map. |
| `limitations` | array<string> | yes | Unresolved rendering or decoding ambiguity. |

## PaperStructure

Source containment and activity, distinct from mathematical dependence.

Schema: [paper-structure.schema.json](paper-structure.schema.json). Roadmap: P2.2.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | yes | Exact source inventory. |
| `main_unit_id` | string | yes | Explicit chosen document entry point. |
| `edges` | array<StructureEdge> | yes | Document structure relations. |
| `unclassified_unit_ids` | array<string> | yes | Units whose activity or role could not be established. |
| `blockers` | array<string> | yes | Parsing or source-activity limitations. |

## AgentizationPlan

Query-independent plan fixed before detailed discovery.

Schema: [agentization-plan.schema.json](agentization-plan.schema.json). Roadmap: P1.3, P2.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | yes | Exact planned paper source. |
| `profile_ref` | RecordRef → processing-profile | yes | Exact work requirements. |
| `baseline_ref` | nullable RecordRef → baseline-snapshot | yes | Prior knowledge selected for later comparison. |
| `source_unit_ids` | array<string> | yes | Fixed source denominator for discovery. |
| `max_steps` | integer | yes | Maximum bounded work steps. |
| `max_seconds` | integer | yes | Maximum wall-clock work budget. |
| `max_cost_units` | integer | yes | Declared integer resource budget. |
| `no_progress_limit` | integer | yes | Consecutive unproductive attempts before deferral. |
| `trigger_note` | string | yes | Why work began; it does not define canonical scope. |

## InventoryDiscovery

All source units classified before an independent scope decision.

Schema: [inventory-discovery.schema.json](inventory-discovery.schema.json). Roadmap: P2.3, P2.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `plan_ref` | RecordRef → agentization-plan | yes | Exact discovery plan. |
| `structure_ref` | RecordRef → paper-structure | yes | Source structure used for discovery. |
| `classified_unit_ids` | array<string> | yes | Units assigned an explicit role. |
| `unclassified_unit_ids` | array<string> | yes | Units still unresolved but retained in the denominator. |
| `obligations` | array<Obligation> | yes | Proposed complete work denominator. |
| `claim_refs` | array<RecordRef → scientific-claim> | yes | Candidate or attributed source propositions. |
| `coverage_rationale` | string | yes | Public account of completeness and exclusions. |

## ScopeFreezeDecision

Independent acceptance or blocking of an exact discovery.

Schema: [scope-decision.schema.json](scope-decision.schema.json). Roadmap: P2.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `discovery_ref` | RecordRef → inventory-discovery | yes | Exact discovery under review. |
| `review` | ReviewContext | yes | Independent review boundary. |
| `decision` | `BLOCK` / `ACCEPT` | yes | Freeze decision, not scientific acceptance. |
| `reason` | string | yes | Public decision rationale. |

## FrozenInventoryScope

Immutable work denominator after an independent freeze decision.

Schema: [frozen-scope.schema.json](frozen-scope.schema.json). Roadmap: P1.3, P2.5.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `plan_ref` | RecordRef → agentization-plan | yes | Exact governing plan. |
| `discovery_ref` | RecordRef → inventory-discovery | yes | Exact inventoried obligations. |
| `decision_ref` | RecordRef → scope-decision | yes | Accepting independent freeze decision. |
| `obligations` | array<Obligation> | yes | Exact obligations retained for total accounting. |
| `predecessor_ref` | nullable RecordRef → frozen-scope | yes | Previous immutable scope, if revised. |
| `change_reason` | string | yes | Genesis reason or explicit scope extension/correction rationale. |
| `removed_obligation_dispositions` | array<RecordRef> | yes | Explicit reviewed accounting for every removed prior obligation. |

## ObligationDisposition

Current disposition of one frozen obligation, retaining all attempts.

Schema: [obligation-disposition.schema.json](obligation-disposition.schema.json). Roadmap: P1.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | yes | Exact frozen denominator. |
| `obligation_id` | string | yes | Exact obligation being accounted for. |
| `outcome` | `BLOCKED` / `DEFERRED` / `FAILED` / `COMPLETED` / `NOT_APPLICABLE` | yes | Execution accounting only. |
| `result_refs` | array<RecordRef> | yes | Actual produced records, not invented placeholders. |
| `attempt_refs` | array<RecordRef → work-attempt> | yes | Exact work attempts. |
| `reason` | string | yes | Outcome explanation and remaining boundary. |
| `previous_ref` | nullable RecordRef → obligation-disposition | yes | Prior immutable disposition. |

## ScientificClaim

Source-faithful proposition preserving conditions, attribution and scientific scope.

Schema: [scientific-claim.schema.json](scientific-claim.schema.json). Roadmap: P2.4, P2.5.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `statement` | string | yes | Complete independently revisable source proposition. |
| `source_span_refs` | array<RecordRef → source-span> | yes | Exact source occurrences supporting every material part. |
| `components` | array<Component> | yes | Independently addressable statement parts. |
| `conditions` | array<Condition> | yes | All truth-relevant source conditions. |
| `modality` | `ASSERTED` / `CONJECTURED` / `OBSERVED` / `APPROXIMATE` / `CONDITIONAL` / `INTERPRETIVE` | yes | Source strength and modality. |
| `attribution` | string | yes | Who asserts which part. |
| `system` | string | yes | Model, physical system or mathematical domain. |
| `comparison_baseline` | string | yes | Source comparison baseline when asserted. |

## DerivedClaim

New proposition with explicit transformation and no fabricated source attribution.

Schema: [derived-claim.schema.json](derived-claim.schema.json). Roadmap: P2.5, P4.5.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `statement` | string | yes | Complete new proposition. |
| `origin` | `SYSTEM_DERIVATION` / `CONDITIONALIZATION` / `REPAIR` / `INDEPENDENT_PROPOSITION` | yes | Why a separate proposition exists. |
| `parent_refs` | array<RecordRef → scientific-claim, derived-claim, math-claim> | yes | Exact propositions from which it was derived or distinguished. |
| `added_conditions` | array<Condition> | yes | Conditions absent from the original proposition. |
| `relation` | `DERIVES` / `SPECIALIZES` / `CORRECTS` / `ALTERNATIVE` / `INDEPENDENT` | yes | Declared relation requiring separate assessment. |
| `rationale` | string | yes | Public reason for the transformation. |

## ClaimComponentMap

Complete mapped-or-residual accounting without scientific promotion.

Schema: [claim-component-map.schema.json](claim-component-map.schema.json). Roadmap: P2.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `claim_ref` | RecordRef → scientific-claim | yes | Exact original claim. |
| `mappings` | array<ComponentMapping> | yes | Exactly one accounting row for each source component. |
| `review` | ReviewContext | yes | Source-to-representation review. |
| `coverage` | `PARTIAL` / `COMPLETE` | yes | Mathematical/semantic accounting coverage, not truth. |

## SemanticContext

Scientific meaning, approximation and observable retained outside formal proof.

Schema: [semantic-context.schema.json](semantic-context.schema.json). Roadmap: P4.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `claim_ref` | RecordRef → scientific-claim, derived-claim | yes | Exact interpreted proposition. |
| `physical_system` | string | yes | Intended physical or modeled system. |
| `object_mapping` | array<ParameterComparison> | yes | Mathematical-to-scientific object correspondence. |
| `assumptions` | array<Condition> | yes | Scientific model assumptions. |
| `approximation_regime` | string | yes | Range of validity and approximation conditions. |
| `error_bound` | string | yes | Source-supported uncertainty or explicit unknown wording. |
| `observables` | array<string> | yes | Operational definitions of observed quantities. |
| `limitations` | array<string> | yes | Unresolved scientific meaning or applicability. |

## MathematicalDefinition

Exact definition with carrier, convention and provenance.

Schema: [definition.schema.json](definition.schema.json). Roadmap: P1.4, P3.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | Definition name. |
| `statement` | string | yes | Complete mathematical definition. |
| `objects` | array<MathObject> | yes | Defined objects and carriers. |
| `source_span_refs` | array<RecordRef → source-span> | yes | Source anchors; empty only for explicit system definitions. |
| `origin` | `SOURCE` / `IMPORTED` / `SYSTEM` | yes | Definition attribution. |

## MathClaimIR

Exact mathematical target without mutable verification status.

Schema: [math-claim.schema.json](math-claim.schema.json). Roadmap: P1.4, P4.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `claim_ref` | RecordRef → scientific-claim, derived-claim | yes | Exact source or independently derived proposition. |
| `component_ids` | array<string> | yes | Mathematical components represented by this target. |
| `objects` | array<MathObject> | yes | Carriers, units and conventions. |
| `quantifiers` | array<Quantifier> | yes | Ordered quantifiers. |
| `assumptions` | array<Condition> | yes | Complete explicit mathematical premises. |
| `conclusion` | string | yes | Exact mathematical conclusion. |
| `exactness` | `EXACT` / `APPROXIMATE` / `ASYMPTOTIC` | yes | Strength of the target. |
| `approximation_error` | string | yes | Error and regime when nonexact. |
| `definition_refs` | array<RecordRef → definition> | yes | Exact mathematical definitions. |
| `semantic_refs` | array<RecordRef → semantic-context> | yes | Scientific residual meaning. |
| `normalization` | string | yes | Symbol and convention normalization with no scope change. |

## AssumptionContext

Local assumptions and their nesting; discharge is an explicit inference.

Schema: [assumption-context.schema.json](assumption-context.schema.json). Roadmap: P3.3, P3.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `parent_ref` | nullable RecordRef → assumption-context | yes | Enclosing context, never a cyclic parent. |
| `assumptions` | array<Condition> | yes | Assumptions introduced in this context. |
| `introduction_reason` | string | yes | Where and why these local premises enter. |
| `allowed_use` | string | yes | Boundaries of valid use. |

## ArgumentNode

One attributed statement in a mathematical argument.

Schema: [argument-node.schema.json](argument-node.schema.json). Roadmap: P3.2, P3.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `statement` | string | yes | Complete node proposition. |
| `kind` | `CLAIM` / `DEFINITION` / `ASSUMPTION` / `LEMMA` / `CONSTRUCTION` / `CONCLUSION` | yes | Mathematical role. |
| `origin` | `SOURCE` / `RECONSTRUCTED` / `REPAIRED` / `ALTERNATIVE` / `IMPORTED` | yes | Attribution of this argument content. |
| `claim_refs` | array<RecordRef → scientific-claim, derived-claim, math-claim> | yes | Exact claim correspondence. |
| `context_ref` | nullable RecordRef → assumption-context | yes | Local assumption scope. |
| `definition_refs` | array<RecordRef → definition> | yes | Definitions used by the node. |
| `source_span_refs` | array<RecordRef → source-span> | yes | Exact source support where applicable. |

## InferenceStep

Joint-premise inference distinct from document containment.

Schema: [inference-step.schema.json](inference-step.schema.json). Roadmap: P1.4, P3.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `premise_refs` | array<RecordRef → argument-node> | yes | Jointly required premises, not separate entailments. |
| `conclusion_ref` | RecordRef → argument-node | yes | Exact concluded node. |
| `rule` | `DIRECT` / `MODUS_PONENS` / `DEFINITIONAL` / `CONTRADICTION` / `INDUCTION` / `CASE_SPLIT` / `ASSUMPTION_DISCHARGE` / `EXTERNAL_RESULT` | yes | Explicit inference rule. |
| `justification` | string | yes | Public mathematical justification. |
| `context_ref` | nullable RecordRef → assumption-context | yes | Scope in which the inference is valid. |
| `discharged_context_refs` | array<RecordRef → assumption-context> | yes | Exact contexts discharged by this step. |
| `rule_evidence_refs` | array<RecordRef> | yes | Witnesses for rule-specific conditions. |

## ProofPlan

One independent route supporting a conclusion.

Schema: [proof-plan.schema.json](proof-plan.schema.json). Roadmap: P3.3, P4.5.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | yes | Exact frozen source of required proof obligations. |
| `conclusion_ref` | RecordRef → argument-node | yes | Exact target conclusion. |
| `route` | `ORIGINAL` / `RECONSTRUCTED` / `REPAIRED` / `ALTERNATIVE` | yes | Attribution of the proof method. |
| `node_refs` | array<RecordRef → argument-node> | yes | Nodes participating in this route. |
| `inference_refs` | array<RecordRef → inference-step> | yes | Exact joint-premise steps. |
| `required_obligation_ids` | array<string> | yes | Frozen proof obligations that cannot disappear on deletion. |
| `open_obligation_ids` | array<string> | yes | Obligations still not discharged. |

## DependencyBinding

Exact use of a premise, definition or external result.

Schema: [dependency-binding.schema.json](dependency-binding.schema.json). Roadmap: P3.6, P5.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `dependent_ref` | RecordRef | yes | Exact object that needs the dependency. |
| `prerequisite_ref` | RecordRef | yes | Exact required input. |
| `kind` | `MATHEMATICAL` / `DEFINITION` / `SCOPE` / `FORMAL_ENVIRONMENT` / `SEMANTIC` / `EMPIRICAL` / `COMPUTATIONAL` / `VALIDATION` | yes | Type governing review propagation. |
| `affected_axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | yes | Axes affected by this dependency. |
| `proof_plan_ref` | nullable RecordRef → proof-plan | yes | Proof route requiring this input. |
| `comparison` | array<ParameterComparison> | yes | Exact assumption and object compatibility. |
| `reuse_decision_ref` | nullable RecordRef → reuse-decision | yes | Separate authorization for the intended use. |

## Challenge

Precisely targeted objection; a response does not resolve it.

Schema: [challenge.schema.json](challenge.schema.json). Roadmap: P3.5.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_ref` | RecordRef | yes | Exact questioned node, inference or binding. |
| `category` | `INFERENCE` / `SCOPE` / `DEFINITION` / `PROVENANCE` / `COUNTEREXAMPLE` / `ALIGNMENT` / `DEPENDENCY` / `AUTHORITY` | yes | Question category. |
| `severity` | `CRITICAL` / `MAJOR` / `MINOR` / `NOTE` | yes | Review priority, not probability of error. |
| `statement` | string | yes | Public concrete objection. |
| `evidence_refs` | array<RecordRef> | yes | Supporting evidence for the objection. |

## ChallengeDisposition

Independent disposition of an exact objection and response.

Schema: [challenge-disposition.schema.json](challenge-disposition.schema.json). Roadmap: P3.5, P3.7.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `challenge_ref` | RecordRef → challenge | yes | Exact original objection. |
| `response` | string | yes | Public response without private model reasoning. |
| `response_refs` | array<RecordRef> | yes | Revised or additional mathematical evidence. |
| `review` | ReviewContext | yes | Independent review of whether the objection is answered. |
| `outcome` | `OPEN` / `RESOLVED` / `WITHDRAWN` / `SUPERSEDED` / `DISPUTED` | yes | Disposition retaining the original challenge. |
| `replacement_ref` | nullable RecordRef → challenge | yes | New objection if superseded. |
| `reason` | string | yes | Why the disposition applies to this exact revision. |

## ArgumentSnapshot

Full fixed argument, not merely the upstream graph projection.

Schema: [argument-snapshot.schema.json](argument-snapshot.schema.json). Roadmap: P3.2.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | yes | Exact query-independent argument work scope. |
| `source_claim_refs` | array<RecordRef → scientific-claim, derived-claim> | yes | Exact argument targets. |
| `math_refs` | array<RecordRef → math-claim> | yes | Fixed mathematical targets associated with the argument. |
| `node_refs` | array<RecordRef → argument-node> | yes | Full node inventory. |
| `inference_refs` | array<RecordRef → inference-step> | yes | Joint-premise inferences. |
| `context_refs` | array<RecordRef → assumption-context> | yes | All local assumption scopes. |
| `proof_plan_refs` | array<RecordRef → proof-plan> | yes | Distinct proof routes. |
| `dependency_refs` | array<RecordRef → dependency-binding> | yes | Full reference and definition dependencies. |
| `challenge_refs` | array<RecordRef → challenge> | yes | All objections including archived paths. |
| `challenge_disposition_refs` | array<RecordRef → challenge-disposition> | yes | Complete known objection history. |
| `upstream_import_ref` | nullable RecordRef → upstream-import | yes | Exact preserved engine input; null for native arguments. |
| `missing_items` | array<string> | yes | Explicit incompleteness of this snapshot. |

## ArgumentReview

Independent argument assessment with explicit open obligations.

Schema: [argument-review.schema.json](argument-review.schema.json). Roadmap: P3.8.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `snapshot_ref` | RecordRef → argument-snapshot | yes | Exact complete review context. |
| `proof_plan_refs` | array<RecordRef → proof-plan> | yes | Routes actually reviewed. |
| `review` | ReviewContext | yes | Actual review identity and procedure. |
| `outcome` | `INCONCLUSIVE` / `CONDITIONAL` / `SUPPORTED` / `COUNTEREVIDENCE` | yes | Scoped argument result, not kernel proof. |
| `open_obligation_ids` | array<string> | yes | Remaining load-bearing obligations. |
| `open_challenge_refs` | array<RecordRef → challenge> | yes | Unresolved relevant objections. |
| `conditions` | array<Condition> | yes | Conditions retained with the conclusion. |

## UpstreamImport

Preserved engine report and independently checked import boundary.

Schema: [upstream-import.schema.json](upstream-import.schema.json). Roadmap: P3.1, P3.2, P3.8.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `engine` | `vibefeld` | yes | Upstream engine identity. |
| `commit` | string | yes | Exact source commit. |
| `protocol_version` | string | yes | Exact supported export protocol. |
| `adapter_version` | string | yes | Exact AgtXIv importer version. |
| `ledger` | nullable ArtifactRef | yes | Raw event ledger, or null when unavailable. |
| `graph` | nullable ArtifactRef | yes | Raw graph projection, or null when unavailable. |
| `context_artifacts` | array<ArtifactRef> | yes | Available scope, definitions, externals, identity and full objections. |
| `identity_map` | nullable ArtifactRef | yes | Exact identity mapping, null if unavailable. |
| `reported_states` | nullable ArtifactRef | yes | Original reported states, null if unavailable. |
| `import_checks` | array<string> | yes | Explicit checks that actually ran. |
| `outcome` | `INCOMPLETE` / `REJECTED` / `STRUCTURALLY_IMPORTED` | yes | Import result, never scientific support. |
| `missing_items` | array<string> | yes | Required upstream information absent. |

## WorkAttempt

Bounded attributable execution with measured resource use.

Schema: [work-attempt.schema.json](work-attempt.schema.json). Roadmap: P3.5, P8.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `plan_ref` | RecordRef → agentization-plan | yes | Governing work budget. |
| `operation` | string | yes | Executed operation. |
| `target_refs` | array<RecordRef> | yes | Exact inputs or targets. |
| `started_at` | string | yes | Execution start time. |
| `finished_at` | string | yes | Execution stop time. |
| `outcome` | `FAILED` / `BLOCKED` / `DEFERRED` / `SUCCEEDED` | yes | Execution outcome without scientific promotion. |
| `output_refs` | array<RecordRef> | yes | Already-created outputs only; records referring back to this attempt are listed by a later completion receipt. |
| `logs` | array<ArtifactRef> | yes | Preserved public execution logs. |
| `cost_units` | integer | yes | Observed resource units. |
| `progress_observed` | boolean | yes | Whether a new result or actionable diagnosis was obtained. |

## FormalEnvironment

Exact toolchain, packages, build inputs and permitted trust policy.

Schema: [formal-environment.schema.json](formal-environment.schema.json). Roadmap: P4.2, P4.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `prover` | `Lean4` | yes | Formal checker family. |
| `toolchain` | string | yes | Exact Lean toolchain identifier. |
| `package_manifest` | ArtifactRef | yes | Exact package commit lock. |
| `source_artifacts` | array<ArtifactRef> | yes | All supplied formal build inputs. |
| `allowed_axioms` | array<string> | yes | Explicit permitted axiom names. |
| `allowed_trust_mechanisms` | array<string> | yes | Explicit additional accepted checker mechanisms. |
| `command` | array<string> | yes | Argument-vector command, never an interpolated shell string. |
| `network_access` | `DISABLED` / `CONTROLLED_ACQUISITION` | yes | Declared execution network boundary. |

## FormalizationPacket

Fixed mathematical target, argument route, semantics and environment.

Schema: [formalization-packet.schema.json](formalization-packet.schema.json). Roadmap: P4.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | yes | Exact source of handoff obligations. |
| `math_ref` | RecordRef → math-claim | yes | Exact mathematical target. |
| `argument_ref` | RecordRef → argument-snapshot | yes | Exact complete argument snapshot. |
| `proof_plan_ref` | RecordRef → proof-plan | yes | Selected proof route. |
| `source_claim_refs` | array<RecordRef → scientific-claim, derived-claim> | yes | Exact original or derived targets. |
| `semantic_refs` | array<RecordRef → semantic-context> | yes | Residual scientific meaning. |
| `environment_ref` | RecordRef → formal-environment | yes | Fixed checker environment. |
| `expected_declarations` | array<string> | yes | Required fully qualified output declarations. |
| `open_obligation_ids` | array<string> | yes | Explicit unproved obligations at handoff. |
| `mode` | `EXPLORATORY` / `RELEASE_CANDIDATE` | yes | Work purpose; neither value grants authority. |

## FormalizationAttempt

Generated formal files and diagnostics, distinct from independent checking.

Schema: [formalization-attempt.schema.json](formalization-attempt.schema.json). Roadmap: P4.1, P4.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `packet_ref` | RecordRef → formalization-packet | yes | Exact handoff. |
| `attempt_ref` | RecordRef → work-attempt | yes | Exact generation run. |
| `outcome` | `FAILED` / `PARTIAL` / `GENERATED` | yes | File-generation result only. |
| `artifacts` | array<ArtifactRef> | yes | Actual generated source files. |
| `diagnostics` | array<string> | yes | Public errors and unresolved work. |

## FormalCheckRecord

Independent target-level kernel and transitive axiom evidence.

Schema: [formal-check.schema.json](formal-check.schema.json). Roadmap: P4.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `packet_ref` | RecordRef → formalization-packet | yes | Exact target handoff. |
| `attempt_ref` | RecordRef → formalization-attempt | yes | Files actually checked. |
| `environment_ref` | RecordRef → formal-environment | yes | Exact checker environment. |
| `review` | ReviewContext | yes | Independence from formal source generation. |
| `outcome` | `FAILED` / `BLOCKED` / `KERNEL_CHECKED` | yes | Scoped observed checker result. |
| `built_declarations` | array<FormalDeclaration> | yes | Declarations actually inspected in the environment. |
| `placeholder_findings` | array<string> | yes | Detected unresolved placeholders or forbidden mechanisms. |
| `logs` | array<ArtifactRef> | yes | Independent checker and axiom-audit logs. |
| `exit_code` | integer | yes | Actual process exit code represented as a nonnegative integer. |

## BacktranslationRecord

Formal statement interpretation with disclosed input visibility.

Schema: [backtranslation.schema.json](backtranslation.schema.json). Roadmap: P4.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `packet_ref` | RecordRef → formalization-packet | yes | Exact target packet identity, not permission to read source text. |
| `formal_artifacts` | array<ArtifactRef> | yes | Formal statements and required definitions actually visible. |
| `visible_record_refs` | array<RecordRef> | yes | Exact records visible to the interpreter. |
| `source_blind` | boolean | yes | Declared source blindness requiring execution evidence. |
| `interpretation` | string | yes | What the formal statement means including assumptions. |
| `conditions` | array<Condition> | yes | Conditions found in the declaration. |
| `visibility_evidence` | array<ArtifactRef> | yes | Independent input-visibility evidence. |

## AlignmentAssessment

One explicit semantic comparison with exact endpoints and independent review.

Schema: [alignment-assessment.schema.json](alignment-assessment.schema.json). Roadmap: P4.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `comparison_kind` | `SOURCE_TO_ARGUMENT` / `SOURCE_TO_MATH` / `MATH_TO_FORMAL` / `SOURCE_TO_FORMAL` | yes | Which alignment boundary was checked. |
| `source_refs` | array<RecordRef> | yes | Exact source-side objects. |
| `target_refs` | array<RecordRef> | yes | Exact target-side objects. |
| `review` | ReviewContext | yes | Independent semantic review. |
| `comparisons` | array<ParameterComparison> | yes | Quantifiers, types, assumptions, meaning and strength comparisons. |
| `outcome` | `UNKNOWN` / `PARTIAL` / `MISALIGNED` / `ALIGNED` | yes | Scoped alignment only, not proof correctness. |
| `backtranslation_refs` | array<RecordRef → backtranslation> | yes | Independently generated formal interpretations. |

## EmpiricalEvidence

Observations, uncertainty and methods tied to exact scientific targets.

Schema: [empirical-evidence.schema.json](empirical-evidence.schema.json). Roadmap: P4.7.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_refs` | array<RecordRef → scientific-claim, derived-claim, semantic-context> | yes | Exact scientific assumptions or conclusions examined. |
| `data` | array<ArtifactRef> | yes | Exact observation data. |
| `method` | string | yes | Data collection and analysis method. |
| `population_regime` | string | yes | Population, system and applicable regime. |
| `uncertainty` | string | yes | Error model and uncertainty reporting. |
| `limitations` | array<string> | yes | Bias, missingness and generalization limits. |
| `role` | `ILLUSTRATIVE` / `SUPPORTING` / `LOAD_BEARING` | yes | Evidence importance to the stated conclusion. |

## ReproductionRecord

Observed reproduction result under a fixed procedure and comparison rule.

Schema: [reproduction-record.schema.json](reproduction-record.schema.json). Roadmap: P4.7.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `protocol_ref` | RecordRef → evidence-protocol | yes | Exact comparison and input policy frozen before execution. |
| `attempt_ref` | RecordRef → work-attempt | yes | Execution whose fixed inputs included the protocol. |
| `target_refs` | array<RecordRef> | yes | Exact computational claims or artifacts. |
| `code` | array<ArtifactRef> | yes | Exact executed code. |
| `inputs` | array<ArtifactRef> | yes | Exact data and parameter inputs. |
| `environment` | ArtifactRef | yes | Exact environment and dependency description. |
| `command` | array<string> | yes | Executed argument-vector command. |
| `seeds` | array<integer> | yes | Random seeds or an empty list for a deterministic procedure. |
| `comparison_rule` | string | yes | Predetermined tolerance or statistical comparison method. |
| `outcome` | `FAILED` / `BLOCKED` / `DISAGREEMENT` / `REPRODUCED` | yes | Reproduction result, not scientific validity. |
| `outputs` | array<ArtifactRef> | yes | Actual produced numerical outputs. |
| `logs` | array<ArtifactRef> | yes | Exact independent execution evidence. |

## AxisAssessment

Exactly one of the six Charter questions with bounded evidence.

Schema: [axis-assessment.schema.json](axis-assessment.schema.json). Roadmap: P1.2, P4.8.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_refs` | array<RecordRef> | yes | Exact objects assessed on this axis. |
| `axis` | `source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility` | yes | One independent Charter verification axis. |
| `applicability` | `UNDETERMINED` / `APPLICABLE` / `NOT_APPLICABLE` | yes | Whether this question applies to these targets. |
| `result` | `NOT_ASSESSED` / `INCONCLUSIVE` / `PARTIALLY_SUPPORTED` / `SUPPORTED` / `COUNTEREVIDENCE` | yes | Evidence conclusion, independent of execution success. |
| `execution` | `DEFERRED` / `BLOCKED` / `FAILED` / `COMPLETED` | yes | What assessment work actually completed. |
| `method` | `SOURCE_REVIEW` / `ARGUMENT_REVIEW` / `KERNEL_AND_ALIGNMENT` / `FORMAL_ALIGNMENT` / `SEMANTIC_REVIEW` / `EMPIRICAL_REVIEW` / `REPRODUCTION_REVIEW` / `COUNTEREXAMPLE_REVIEW` / `UNASSESSED` | yes | Evidence method and strength. |
| `review` | ReviewContext | yes | Attributable independent assessment boundary. |
| `support_refs` | array<RecordRef> | yes | Exact supporting evidence. |
| `counterevidence_refs` | array<RecordRef> | yes | Exact relevant contrary evidence. |
| `conditions` | array<Condition> | yes | Conditions retained with this assessment. |
| `frontier_refs` | array<RecordRef → frontier-item> | yes | Relevant unresolved problems. |
| `rationale` | string | yes | Public scoped conclusion including non-applicability reasons. |

## StatusView

Rebuildable six-axis view preserving all exact and conflicting assessments.

Schema: [status-view.schema.json](status-view.schema.json). Roadmap: P4.8, P7.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_ref` | RecordRef | yes | Exact queried subject. |
| `assessment_refs` | array<RecordRef → axis-assessment> | yes | Full selected assessment evidence. |
| `conflicting_assessment_refs` | array<RecordRef → axis-assessment> | yes | Independently inspectable disagreements. |
| `axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | yes | Exactly the six axes, each appearing once. |
| `frontier_refs` | array<RecordRef → frontier-item> | yes | Unresolved boundaries. |
| `projection_method` | string | yes | Deterministic view policy, never a truth-score aggregation. |

## BaselineSnapshot

Fixed prior knowledge and search coverage for a contribution comparison.

Schema: [baseline-snapshot.schema.json](baseline-snapshot.schema.json). Roadmap: P5.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `knowledge_ref` | nullable RecordRef → knowledge-snapshot | yes | Exact previous knowledge snapshot, if available. |
| `entry_refs` | array<RecordRef> | yes | Exact prior entries included in the comparison. |
| `domain` | string | yes | Scientific and mathematical comparison domain. |
| `selection_method` | string | yes | How the prior knowledge was chosen. |
| `search_coverage` | string | yes | Bounded retrieval sources, queries and coverage. |
| `limitations` | array<string> | yes | Known missing knowledge and non-priority implications. |

## RelationAssessment

Witness-backed relation between exact claims or knowledge records.

Schema: [relation-assessment.schema.json](relation-assessment.schema.json). Roadmap: P5.2.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef | yes | Source endpoint; read source relation target. |
| `target_ref` | RecordRef | yes | Target endpoint, distinct from the source. |
| `relation` | `EQUIVALENT` / `SPECIALIZES` / `GENERALIZES` / `CORRECTS` / `QUALIFIES` / `REFUTES` / `SUPPORTS` / `INCOMPARABLE` / `CONFLICTING` / `SAME_OCCURRENCE` / `MATH_EQUIVALENT_SEMANTICS_DISTINCT` | yes | Exact typed relation. |
| `review` | ReviewContext | yes | Independent relation assessment. |
| `comparisons` | array<ParameterComparison> | yes | Domain, assumption and semantic alignment witnesses. |
| `outcome` | `PROPOSED` / `BLOCKED` / `DISPUTED` / `ACCEPTED` / `REJECTED` | yes | Relation assessment state, not endpoint truth. |
| `witness_refs` | array<RecordRef> | yes | Mathematical and scientific support. |

## ContributionDelta

Attributable knowledge change relative to one fixed baseline.

Schema: [contribution-delta.schema.json](contribution-delta.schema.json). Roadmap: P5.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `baseline_ref` | RecordRef → baseline-snapshot | yes | Exact comparison baseline, not the later transaction snapshot. |
| `current_refs` | array<RecordRef> | yes | This paper's exact result, method or evidence. |
| `prior_refs` | array<RecordRef> | yes | Prior objects compared. |
| `operation` | `INTRODUCES` / `DERIVES` / `REPROVES` / `GENERALIZES` / `SPECIALIZES` / `WEAKENS_ASSUMPTIONS` / `CORRECTS` / `QUALIFIES` / `REFUTES` / `REPRODUCES` / `INDEPENDENTLY_VERIFIES` / `UNIFIES` / `APPLIES` | yes | Attributable type of change, not an importance score. |
| `relation_refs` | array<RecordRef → relation-assessment> | yes | Assessed comparison relations. |
| `author_declaration` | string | yes | The paper's own novelty statement, attributed separately. |
| `review` | ReviewContext | yes | Independent contribution evaluation. |
| `outcome` | `PROPOSED` / `BLOCKED` / `DISPUTED` / `SUPPORTED` / `REJECTED` | yes | Bounded delta assessment. |
| `qualifications` | array<string> | yes | Baseline coverage and unresolved limitations. |

## ReuseDecision

Permission to reuse an exact result for one specified target and evidence standard.

Schema: [reuse-decision.schema.json](reuse-decision.schema.json). Roadmap: P5.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef | yes | Exact reusable result. |
| `target_ref` | RecordRef | yes | Exact proposed target use. |
| `profile_ref` | RecordRef → processing-profile | yes | Evidence standard required by this use. |
| `comparisons` | array<ParameterComparison> | yes | Required object, premise, scope, evidence and environment matching. |
| `assessment_refs` | array<RecordRef> | yes | Evidence and relation decisions supporting reuse. |
| `review` | ReviewContext | yes | Independent use-specific review. |
| `outcome` | `UNKNOWN` / `REJECT` / `CONDITIONAL` / `ALLOW` | yes | Use permission, not a new theorem proof. |
| `conditions` | array<Condition> | yes | Remaining conditions required at the target. |
| `conflict_refs` | array<RecordRef → relation-assessment> | yes | Relevant contradictory or limiting relations. |
| `environment_check_ref` | nullable RecordRef → environment-check | yes | Exact formal import compatibility when relevant. |

## EnvironmentCompatibility

Observed exact formal import compatibility, never text matching.

Schema: [environment-check.schema.json](environment-check.schema.json). Roadmap: P4.2, P5.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_environment_ref` | RecordRef → formal-environment | yes | Original environment. |
| `target_environment_ref` | RecordRef → formal-environment | yes | Intended use environment. |
| `declarations` | array<string> | yes | Exact declarations imported. |
| `outcome` | `INCOMPATIBLE` / `BLOCKED` / `COMPATIBLE` | yes | Observed compatibility result. |
| `logs` | array<ArtifactRef> | yes | Actual build/import evidence. |
| `assumption_comparison` | array<ParameterComparison> | yes | Assumptions and definition correspondence. |

## FrontierItem

Durable unresolved question and the precise next evidence needed.

Schema: [frontier-item.schema.json](frontier-item.schema.json). Roadmap: P5.5, P7.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_refs` | array<RecordRef> | yes | Exact affected targets. |
| `kind` | `MISSING_SOURCE` / `UNPROVED_LEMMA` / `SCOPE_AMBIGUITY` / `ALIGNMENT_GAP` / `MODEL_ASSUMPTION` / `DATA_MISSING` / `CONFLICT` / `ENVIRONMENT` / `RESOURCE_LIMIT` | yes | Type of unresolved boundary. |
| `axes` | array<`source_fidelity` / `mathematical_correctness` / `formal_alignment` / `semantic_applicability` / `empirical_support` / `computational_reproducibility`> | yes | Applicable affected axes. |
| `statement` | string | yes | Concrete unresolved issue. |
| `next_evidence` | string | yes | What could resolve or narrow the issue. |
| `attempt_refs` | array<RecordRef → work-attempt> | yes | Exact previous attempts. |
| `state` | `OPEN` / `BLOCKED` / `DEFERRED` / `RESOLVED` / `SUPERSEDED` | yes | Frontier lifecycle, preserving history. |
| `resolution_refs` | array<RecordRef> | yes | Evidence when resolved or superseded. |

## PaperAgentManifest

Exact candidate contents fixed before independent paper audit.

Schema: [release-manifest.schema.json](release-manifest.schema.json). Roadmap: P6.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `source_ref` | RecordRef → source-snapshot | yes | Exact paper source. |
| `scope_ref` | RecordRef → frozen-scope | yes | Exact fixed work denominator. |
| `profile_ref` | RecordRef → processing-profile | yes | Exact completion requirements. |
| `record_refs` | array<RecordRef> | yes | All packaged structured records. |
| `artifacts` | array<ArtifactRef> | yes | Exact byte artifacts. |
| `disposition_refs` | array<RecordRef → obligation-disposition> | yes | One current disposition per frozen obligation. |
| `frontier_refs` | array<RecordRef → frontier-item> | yes | All relevant unresolved boundaries. |
| `contribution_refs` | array<RecordRef → contribution-delta> | yes | At least one assessed, provisional or blocked knowledge delta. |
| `non_implications` | array<string> | yes | Explicit boundaries of package completion. |

## ReleaseAudit

Independent paper-level review of the exact candidate and its scope.

Schema: [release-audit.schema.json](release-audit.schema.json). Roadmap: P6.2.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `manifest_ref` | RecordRef → release-manifest | yes | Exact fixed candidate under audit. |
| `review` | ReviewContext | yes | Actual independent paper auditor. |
| `ordered_target_refs` | array<RecordRef> | yes | Targets audited in dependency order. |
| `assessment_refs` | array<RecordRef → axis-assessment> | yes | Exact assessments selected without changing them. |
| `frontier_refs` | array<RecordRef → frontier-item> | yes | Complete retained frontier. |
| `recommendation` | `DO_NOT_RELEASE` / `RECOMMEND_PROFILE_RELEASE` | yes | Profile-scoped recommendation, not paper truth. |
| `findings` | array<string> | yes | Public audit findings and limits. |

## ReleaseCertificate

Mechanical binding of the exact candidate, audit and authority policy.

Schema: [release-certificate.schema.json](release-certificate.schema.json). Roadmap: P6.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `manifest_ref` | RecordRef → release-manifest | yes | Exact candidate certified or rejected. |
| `audit_ref` | RecordRef → release-audit | yes | Exact independent audit. |
| `checks` | array<string> | yes | Mechanical checks actually performed. |
| `outcome` | `REJECTED` / `CERTIFIED` | yes | Mechanical result only. |
| `failed_checks` | array<string> | yes | Every failed required check. |

## PaperAgentRelease

Immutable aggregate created after manifest, audit and certificate.

Schema: [paper-release.schema.json](paper-release.schema.json). Roadmap: P6.1, P6.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `manifest_ref` | RecordRef → release-manifest | yes | Exact content manifest. |
| `audit_ref` | RecordRef → release-audit | yes | Exact paper audit. |
| `certificate_ref` | RecordRef → release-certificate | yes | Exact successful certificate. |
| `release_name` | string | yes | Human-readable publication version. |
| `publication_uri` | nullable string | yes | Actual public release location, null for local unpublished packages. |

## ArchiveReceipt

Actual persistence receipt independent of knowledge admission.

Schema: [archive-receipt.schema.json](archive-receipt.schema.json). Roadmap: P6.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `release_ref` | RecordRef → paper-release | yes | Exact package archived. |
| `objects` | array<ArtifactRef> | yes | Bytes whose persistence was checked. |
| `checkpoint_ref` | nullable RecordRef → event-checkpoint | yes | Independent history anchor if available. |
| `assurance` | `LOCAL_PERSISTENCE` / `INDEPENDENTLY_ANCHORED` | yes | Actual archive integrity boundary. |
| `location` | string | yes | Actual archive location. |

## AdmissionDecision

Independent disposition of an exact candidate set for one domain snapshot.

Schema: [admission-decision.schema.json](admission-decision.schema.json). Roadmap: P6.5.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `release_ref` | RecordRef → paper-release | yes | Exact source package. |
| `before_ref` | RecordRef → knowledge-snapshot | yes | Exact intended transaction input snapshot. |
| `review` | ReviewContext | yes | Independent admission review. |
| `items` | array<AdmissionItem> | yes | Total disjoint dispositions of the proposed candidates. |
| `domain` | string | yes | Scientific reuse domain. |

## KnowledgeSnapshot

Immutable domain knowledge retaining exact records, relationships and conflicts.

Schema: [knowledge-snapshot.schema.json](knowledge-snapshot.schema.json). Roadmap: P6.6, P6.7.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `domain` | string | yes | Domain and interpretation scope. |
| `predecessor_ref` | nullable RecordRef → knowledge-snapshot | yes | Previous immutable snapshot; null for genesis. |
| `entry_refs` | array<RecordRef> | yes | Admitted source, evidence, theorem or frontier records. |
| `relation_refs` | array<RecordRef → relation-assessment> | yes | Assessed relations, including conflicts. |
| `release_refs` | array<RecordRef → paper-release> | yes | Exact backing paper packages. |
| `admission_refs` | array<RecordRef → admission-decision> | yes | Decisions authorizing additions. |

## KnowledgeIngestionReceipt

Atomic before/after transaction with a total candidate partition.

Schema: [ingestion-receipt.schema.json](ingestion-receipt.schema.json). Roadmap: P6.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `before_ref` | RecordRef → knowledge-snapshot | yes | Exact snapshot compared before mutation. |
| `after_ref` | RecordRef → knowledge-snapshot | yes | Exact resulting snapshot, identical on abort. |
| `decision_ref` | RecordRef → admission-decision | yes | Exact accepted/rejected/blocked partition. |
| `candidate_refs` | array<RecordRef> | yes | Complete transaction candidate universe. |
| `accepted_refs` | array<RecordRef> | yes | All and only authorized additions. |
| `rejected_refs` | array<RecordRef> | yes | Rejected candidates. |
| `blocked_refs` | array<RecordRef> | yes | Candidates still blocked. |
| `outcome` | `ABORTED` / `COMMITTED` | yes | Actual atomic transaction result. |

## EventRecord

Append-only state transition with exact actor and previous-event binding.

Schema: [event.schema.json](event.schema.json). Roadmap: P3.4, P6.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `stream_id` | string | yes | Exact event stream. |
| `sequence` | integer | yes | Monotonic contiguous stream position. |
| `previous_ref` | nullable RecordRef → event | yes | Exact predecessor; null only for first event. |
| `operation` | string | yes | Attributed state transition. |
| `target_refs` | array<RecordRef> | yes | Exact affected records. |
| `receipt_artifacts` | array<ArtifactRef> | yes | Actual external execution evidence. |

## EventCheckpoint

Separately held history anchor with explicit assurance limitations.

Schema: [event-checkpoint.schema.json](event-checkpoint.schema.json). Roadmap: P6.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `event_ref` | RecordRef → event | yes | Exact anchored event. |
| `anchor_artifact` | ArtifactRef | yes | Actual checkpoint or signed attestation bytes. |
| `holder_principal_id` | string | yes | Principal retaining the checkpoint outside the worker. |
| `assurance` | `LOCAL_COPY` / `INDEPENDENTLY_HELD` / `SIGNATURE_VERIFIED` | yes | Observed anchoring assurance, not inferred from hashes. |
| `verification_method` | string | yes | How the anchor was independently checked. |

## ImpactAnalysis

Typed dependency impact without silently rewriting historical assessments.

Schema: [impact-analysis.schema.json](impact-analysis.schema.json). Roadmap: P7.2.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `trigger_refs` | array<RecordRef> | yes | New source, evidence, policy or adopted version triggering review. |
| `dependency_refs` | array<RecordRef → dependency-binding> | yes | Complete graph inputs used in impact traversal. |
| `affected` | array<ImpactTarget> | yes | Precisely affected targets and axes. |
| `unaffected_proof_plan_refs` | array<RecordRef → proof-plan> | yes | Independent routes explicitly retained. |
| `algorithm` | string | yes | Versioned deterministic traversal. |

## RevisionRecord

Explicit semantic or representational change with preserved old identity.

Schema: [revision-record.schema.json](revision-record.schema.json). Roadmap: P2.5, P7.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `old_ref` | RecordRef | yes | Exact preceding object. |
| `new_ref` | RecordRef | yes | Exact replacement or derived object. |
| `change_kind` | `REPRESENTATION_CORRECTION` / `NEW_PROPOSITION` / `SCOPE_EXTENSION` / `ENVIRONMENT_CHANGE` / `ASSESSMENT_UPDATE` | yes | Semantic type of change. |
| `reason` | string | yes | Public difference and why identity was retained or changed. |
| `impact_ref` | nullable RecordRef → impact-analysis | yes | Exact affected-set analysis. |
| `review` | ReviewContext | yes | Independent identity and scope review. |

## LegacyBinding

Exact legacy evidence without fabricated history or stronger V3 status.

Schema: [legacy-binding.schema.json](legacy-binding.schema.json). Roadmap: P8.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `legacy_contract` | string | yes | Original V1/V2 or research contract identity. |
| `legacy_artifact` | ArtifactRef | yes | Unmodified legacy bytes. |
| `original_identity` | string | yes | Original IDs, revisions and bound authority. |
| `original_status` | string | yes | Original meaning preserved literally with context. |
| `v3_target_ref` | nullable RecordRef | yes | Optional separately evaluated V3 object. |
| `missing_information` | array<string> | yes | Missing identity, review, axes or events. |
| `non_promotion` | `LEGACY_STATUS_PRESERVED` | yes | No automatic status upgrade. |

## QueryReceipt

Read-only answer over exact knowledge with visible relevant conflict.

Schema: [query-receipt.schema.json](query-receipt.schema.json). Roadmap: P7.4, P7.6.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `query` | string | yes | User request used for retrieval, not canonical mutation. |
| `knowledge_ref` | RecordRef → knowledge-snapshot | yes | Exact queried knowledge snapshot. |
| `mode` | `PACKAGE_BACKED` / `PROVISIONAL` | yes | Authority boundary of the response. |
| `returned_refs` | array<RecordRef> | yes | Exact returned records. |
| `relation_refs` | array<RecordRef → relation-assessment> | yes | Relevant returned relations including opposing endpoints. |
| `assertions` | array<QueryAssertion> | yes | Public text with exact supporting records. |
| `frontier_refs` | array<RecordRef → frontier-item> | yes | Relevant unresolved issues. |
| `work_request_ref` | nullable RecordRef → agentization-plan | yes | A separately authorized work plan, if triggered. |
| `canonical_mutation` | `FORBIDDEN` | yes | A query cannot change authoritative knowledge. |

## EvaluationReport

Measured comparisons under fixed tasks, profiles and resource boundaries.

Schema: [evaluation-report.schema.json](evaluation-report.schema.json). Roadmap: P8.3, P8.4.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `corpus` | ArtifactRef | yes | Exact fixed evaluation set. |
| `profile_ref` | RecordRef → processing-profile | yes | Identical work standard used for comparison. |
| `methods` | array<string> | yes | Compared processing methods. |
| `attempt_refs` | array<RecordRef → work-attempt> | yes | Actual runs providing measurements. |
| `metrics` | array<Metric> | yes | Measured outcomes with denominators. |
| `limitations` | array<string> | yes | Missing controls and uncertainty preventing stronger claims. |

## SourceRequest

A bibliographic acquisition request that exists before any source bytes are available.

Schema: [source-request.schema.json](source-request.schema.json). Roadmap: P2.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `paper_id` | string | yes | Requested exact work identity. |
| `paper_version` | string | yes | Explicit version, never a latest alias. |
| `source_uri` | string | yes | Requested source location. |
| `allowed_hosts` | array<string> | yes | Explicit acquisition host allowlist. |
| `max_bytes` | integer | yes | Maximum response bytes. |
| `timeout_seconds` | integer | yes | Maximum request duration. |

## SourceAcquisition

Observed acquisition success or failure, including failures before a snapshot exists.

Schema: [source-acquisition.schema.json](source-acquisition.schema.json). Roadmap: P2.1.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `request_ref` | RecordRef → source-request | yes | Exact request and acquisition policy. |
| `outcome` | `FAILED` / `BLOCKED` / `ACQUIRED` | yes | Actual acquisition outcome, not source fidelity. |
| `started_at` | string | yes | Actual request start. |
| `finished_at` | string | yes | Actual request completion. |
| `artifacts` | array<ArtifactRef> | yes | Actual returned source bytes. |
| `final_uri` | nullable string | yes | Final observed URL, null if unavailable. |
| `transport_evidence` | array<ArtifactRef> | yes | Retained transport evidence. |
| `reason` | string | yes | Failure or success conditions and limitations. |

## EvidenceProtocol

Evidence targets, inputs and comparison rules frozen before execution.

Schema: [evidence-protocol.schema.json](evidence-protocol.schema.json). Roadmap: P4.7, P8.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `scope_ref` | RecordRef → frozen-scope | yes | Exact work obligation denominator. |
| `obligation_ids` | array<string> | yes | Evidence work obligations under this protocol. |
| `target_refs` | array<RecordRef> | yes | Exact claims or evidence targets. |
| `method` | `COMPUTATION` / `EMPIRICAL_ANALYSIS` / `CONTROLLED_COMPARISON` | yes | Evidence production method. |
| `inputs` | array<ArtifactRef> | yes | Data, code and configuration fixed before execution. |
| `environment` | ArtifactRef | yes | Frozen execution environment. |
| `comparison_rule` | string | yes | Predetermined tolerance or statistical decision rule. |
| `required_outcome` | `ACCOUNT_FOR` / `SUCCESS_REQUIRED` | yes | Required evidence obligation. |

## WorkCompletion

Post-execution reference to results that themselves refer to the attempt.

Schema: [work-completion.schema.json](work-completion.schema.json). Roadmap: P3.5, P4.3.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `attempt_ref` | RecordRef → work-attempt | yes | Exact earlier execution record. |
| `result_refs` | array<RecordRef> | yes | Later created results referring to that execution. |
| `limitations` | array<string> | yes | Remaining production or evidence limitations. |

## CounterexampleRecord

A concrete counterexample against one exact quantified proposition.

Schema: [counterexample.schema.json](counterexample.schema.json). Roadmap: P3.5, P4.8.

| Field | Type / values | Required | Meaning |
|---|---|---|---|
| `target_ref` | RecordRef → scientific-claim, derived-claim, math-claim, argument-node | yes | Exact proposition challenged. |
| `construction` | string | yes | Explicit mathematical instance or scientific observation. |
| `premise_checks` | array<ParameterComparison> | yes | Why the instance satisfies the target premises and domain. |
| `violated_conclusion` | string | yes | Exact target conclusion contradicted by the instance. |
| `evidence_refs` | array<RecordRef> | yes | Derivation, checked calculation or observational support. |
| `limitations` | array<string> | yes | Conditions still needing independent review. |

## Cross-record validation and implementation evidence

See [INVARIANTS.md](INVARIANTS.md) for checks that shape validation cannot perform, [README.md](README.md) for commands, and [the execution status](../docs/roadmaps/v3-execution-status.md) for evidence-backed implementation progress. The contract directory is a versioned experimental package; do not interpret schemas as already operationalized services.

