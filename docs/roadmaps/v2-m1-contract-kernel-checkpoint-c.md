# AgtXIv V2 M1 contract kernel — Checkpoint C: locked requirements and Catalog/Profile linkage

- Document status: implementation plan; not implementation evidence
- Document version: 1.0
- Checkpoint status: proposed and intentionally incomplete
- Committed basis: `9d84dad47b7a92225686158f7bfc512f39332f2c`
- Parent design: `docs/roadmaps/v2-m1-contract-kernel-slice-1.md`
- Predecessor: `docs/roadmaps/v2-m1-contract-kernel-checkpoint-b.md`
- Date: 2026-08-31
- Authority: none for runtime selection, obligation satisfaction, coverage
  promotion, merge, release, archive, certification, database admission, or
  knowledge admission

Checkpoint C freezes the independent 52-item M1 contract-requirements floor,
defines the first closed `ArtifactFamilyCatalog` and
`AgentizationProfileRelease` document schemas, and implements pure offline
cross-validation over explicitly supplied bytes. A raw-byte-addressed synthetic
integration fixture proves that one Catalog and one reusable Profile can be
linked without a hash cycle, that no Catalog minimum can be weakened, and that
an optional row can be explicitly left unselected without disappearing.

Checkpoint C does **not** publish a partial runtime Catalog or Profile. The six
planned Plan/Discovery/Freeze family contracts do not yet exist, so reporting
the future eight-row slice as `8/8` would require invented hashes or would
misrepresent a synthetic sample as contract coverage. The only normative data
asset introduced here is the locked M1 requirement set. Catalog/Profile sample
bytes live under `fixtures/`, state that they are structural integration data,
and change no M1 completion numerator.

This is a deliberate refinement of Checkpoint B Section 14. Outcomes and
minimum declared context shapes can be constrained now. Globally registered
reason meanings cannot: the exact stable-error catalog is not yet implemented.
Checkpoint C therefore fixes reason handling to
`DEFERRED_TO_EXACT_ERROR_CATALOG` instead of creating a shadow reason registry.

Nothing in this plan adopts the modified or untracked flat V2 schemas,
fixtures, validator, specification, demos, database prototype, or other user
work already present in the working tree.

## 1. Intuition: three different checklists

The three documents answer different questions:

1. The **locked M1 requirement set** is the project's frozen 52-box
   acceptance sheet. It states what the M1 software project must eventually
   contract. A Catalog or Profile cannot erase a box from this sheet.
2. The **ArtifactFamilyCatalog** is the warehouse's product-and-inspection
   manual. For each declared artifact family and stage, it identifies the exact
   successful-output ruler, accounting unit, producer roles, cardinality, and
   structurally permitted attempt outcomes.
3. The **AgentizationProfile** is a reusable inspection-policy template. It
   selects or strengthens Catalog policy. It is not the actual checklist for a
   particular paper.

Checkpoint D will add `AgentizationPlan` and `FrozenInventoryScope`. Those are
the plan and independently frozen room-by-room checklist for one exact paper.
Keeping the reusable Profile separate from a paper-specific frozen scope avoids
two dangerous substitutions: a query cannot silently rewrite project scope,
and a producer cannot omit a difficult component by choosing a smaller
Profile.

The physical hash graph is one-way:

```text
fixed parent-roadmap bytes <- locked M1 requirement set

fixed schema + validator + vector bytes <- synthetic Catalog fixture
synthetic Catalog fixture               <- synthetic Profile fixture

requirement set + real Catalog + real Profile <- future ContractBundleRelease
```

The requirement set is a sibling of Catalog and Profile, not their child.
Catalog never exact-references a Profile or a future bundle. Profile
exact-references Catalog. No document contains its own hash, the hash of a
receipt about itself, or a future placeholder hash.

## 2. Terms and proof boundary

- **Requirement item:** one versioned M1 project-acceptance obligation. It may
  be a record family, a raw contract asset, or a named cross-record rule. It is
  not automatically an operational artifact family.
- **Artifact family:** one Catalog-declared kind of successful output. Family
  identity, record type, schema identity, and requirement identity are separate
  namespaces and cannot be substituted for one another.
- **Stage policy:** Catalog policy for one exact `(family_id, family_version,
  stage_id)` key.
- **Raw contract asset:** canonical bytes such as a Catalog, Profile, policy, or
  requirement set. It is not an immutable record and must not invent a
  `record_type`.
- **Immutable record:** an envelope/payload/content-hash object whose exact
  family schema declares `$defs/recordType/const`.
- **Minimum runtime obligation:** the weakest selection allowed by a Catalog
  stage policy: `CORE_REQUIRED` or `OPTIONAL_ALLOWED`.
- **Profile requirement adjustment:** the Profile's explicit selection for one
  Catalog stage policy: `REQUIRED`, `OPTIONAL`, or `NOT_SELECTED`.
- **Minimum declared context mode:** the weakest terminal-card reference shape
  permitted for a stage. It does not prove that the references resolve or are
  relevant.
- **Structural integration conformance:** exact bytes, schema conformance,
  closed references, and monotone policy agree. It is not runtime authority,
  operational coverage, review, release, or admission.

Requirement and terminal validation success return an empty diagnostic tuple;
builder success returns one sealed constraints snapshot. All three mean only
that the submitted isolated contract documents satisfy this mechanical
boundary. Public names and documentation must not shorten any result to
“released,” “contracted,” “complete,” “approved,” “covered,” or “admitted.”

## 3. Normative locked M1 requirement set

### 3.1 Identity and exact source binding

The single normative raw data asset in this checkpoint is:

```text
contracts/v2/contract-kernel/requirements/
  m1-contract-requirement-set/1.0.0.json
```

Its asset ID is `requirements:m1-contract-requirement-set:1.0.0`. Its schema
identity is:

```text
https://agtxiv.org/schema/v2/contract-kernel/contract/
  m1-contract-requirement-set/1.0.0
```

The raw canonical document contains exactly:

```text
document_type = AGTXIV_M1_CONTRACT_REQUIREMENT_SET
document_schema_ref
denominator_id = agtxiv.m1-contract-denominator/1.0.0
denominator_version = 1.0.0
source_binding
selection_rule
selected_source_rows
item_count = 52
items
```

`document_schema_ref` is the full five-field exact reference to the official
requirement-set schema bytes. `source_binding` contains exactly:

```text
roadmap_ref
source_git_commit
source_git_blob_object_id
section_start_heading
section_end_heading
section_byte_size
section_sha256
```

The authoritative `roadmap_ref` has no `path_hint` or `schema_uri` and is fixed
to all four required exact-asset fields:

```text
asset_id   roadmap:v2-end-to-end-implementation-plan:2026-08-31
media_type text/markdown
byte_size  50302
sha256     sha256:7419bc340471943b1e525974b558eb508d0deaf12455d5e12949db8a7d2be2f4
```

The remaining source facts are:

```text
source Git commit          9d84dad47b7a92225686158f7bfc512f39332f2c
Git blob object ID         sha1:782eb493c1ee28c6f61d5a07af30449b83183e08
section start line-feed (LF) bytes "## 6. Required artifact families\n"
section end LF bytes                "## 7. Mathematical formalization chain\n"
section byte size          3136
section SHA-256            sha256:e50d851df655302106f3c1b5ec3f8462b9dc2dd0d12143c1b4e68bde483e4437
```

“Git object ID” is the expanded meaning of OID. SHA-1 here identifies the
already committed Git blob; the raw SHA-256 exact reference remains the primary
byte-integrity check. The pure validator receives the roadmap as a
`SuppliedAsset`, checks its exact reference, and recomputes the Git blob ID from
`b"blob " + decimal_length + b"\\0" + raw_bytes`. It requires one start heading
and one later end heading, extracts the inclusive-start/exclusive-end byte
slice, and recomputes the section size and digest. It performs no live Git,
filesystem, or Markdown lookup.

`selection_rule` contains exactly:

```text
selection_rule_id = agtxiv.roadmap-exact-milestone-token/1.0.0
target_milestone_token = M1
token_separator = /
match_mode = EXACT_TOKEN
```

`M1.5` alone therefore does not match `M1`. The C validator does not invent a
general Markdown parser. It pins the reviewed mapping below to the exact source
section bytes. A later generator may mechanically reproduce the same mapping,
but cannot reinterpret different roadmap bytes under this requirement-set
version.

### 3.2 Closed source rows and item records

`selected_source_rows` is an array of 13 closed objects in parent-table order:

```text
source_table_row_ordinal
source_group
source_required_families_cell
source_target_milestone_cell
requirement_ordinals
```

The selected parent-table row ordinals are exactly
`[1, 2, 4, 6, 7, 8, 10, 13, 14, 15, 16, 17, 18]`. The exact cell strings and
their reviewed expansions are:

```text
Contract      | ContractBundleRelease, profile, ArtifactFamilyCatalog, canonicalization and policy refs                                      | M1
Intake        | PaperQuery, WorkResolution, SourceAcquisitionRequest/Result                                                                  | M1/M1.5
Planning      | AgentizationPlan, InventoryDiscoveryResult, ScopeFreezeDecision, FrozenInventoryScope                                        | M1
Claims        | ScientificClaim, ClaimDecomposition, attribution and reconstruction evidence                                                 | M1/M4a
Mathematics   | native MathClaimIR/2, MathClaimIRBinding/2, component index, residual semantics                                               | M1/M4b
Reasoning     | InferenceStep, claim inference graph, mathematical dependency graph, frontier/blocker                                        | M1/M4b
Formalization | FormalizationRequest, generated package, build result, formal declaration graph                                              | M1/M5
Assessment    | assessor/method/evidence/rationale/uncertainty/attestation, ReviewDecision                                                    | M1/M5/M6
Release       | release manifest, Root audit, certificate, replay bundle, ArchiveReceipt                                                     | M1/M6
Knowledge     | candidate entry, relation, per-entry eligibility, admission transaction, snapshot, ingestion receipt                         | M1/M6
Query         | QueryResolution, exact snapshot projection, conflict preservation                                                            | M1/M6
Compatibility | V1 binding, migration/import receipt, reconciliation report                                                                  | M1/M8
Terminal      | typed stage/family result with reason, evidence, retryability, responsible actor, next action                                | M1
```

The three columns above are respectively `source_group`, the exact
`source_required_families_cell`, and the exact
`source_target_milestone_cell`. The requirement expansion is:

| Source group | Requirement IDs | Unique additions |
|---|---|---:|
| Contract | `CONTRACT_BUNDLE_RELEASE`, `AGENTIZATION_PROFILE_RELEASE`, `ARTIFACT_FAMILY_CATALOG`, `CANONICALIZATION_PROFILE`, `VALIDATION_POLICY`, `SIGNATURE_POLICY`, `STABLE_ERROR_CODE_CATALOG` | 7 |
| Intake | `PAPER_QUERY`, `WORK_RESOLUTION`, `SOURCE_ACQUISITION_REQUEST`, `SOURCE_ACQUISITION_RESULT` | 4 |
| Planning | `AGENTIZATION_PLAN`, `INVENTORY_DISCOVERY_RESULT`, `SCOPE_FREEZE_DECISION`, `FROZEN_INVENTORY_SCOPE` | 4 |
| Claims | `SCIENTIFIC_CLAIM`, `CLAIM_DECOMPOSITION`, `CLAIM_ATTRIBUTION_EVIDENCE`, `CLAIM_RECONSTRUCTION_EVIDENCE` | 4 |
| Mathematics | `NATIVE_MATH_CLAIM_IR`, `MATH_CLAIM_IR_BINDING`, `MATH_CLAIM_COMMON_READ_PROJECTION`, `MATH_COMPONENT_INDEX`, `RESIDUAL_SEMANTICS` | 5 |
| Reasoning | `INFERENCE_STEP`, `CLAIM_INFERENCE_GRAPH`, `MATH_CLAIM_DEPENDENCY_GRAPH`, `DEPENDENCY_FRONTIER_BLOCKER` | 4 |
| Formalization | `FORMALIZATION_REQUEST`, `GENERATED_FORMAL_PACKAGE`, `FORMAL_BUILD_RESULT`, `FORMAL_DECLARATION_GRAPH` | 4 |
| Assessment | `ASSESSMENT_RECORD`, `REVIEW_DECISION`, `SIGNED_ATTESTATION` | 3 |
| Release | `PAPER_AGENT_RELEASE_MANIFEST`, `ROOT_AUDIT`, `MECHANICAL_CERTIFICATE`, `REPLAY_BUNDLE`, `ARCHIVE_RECEIPT` | 5 |
| Knowledge | `KNOWLEDGE_CANDIDATE_ENTRY`, `KNOWLEDGE_RELATION`, `PER_ENTRY_ELIGIBILITY`, `ADMISSION_TRANSACTION`, `KNOWLEDGE_SNAPSHOT`, `KNOWLEDGE_INGESTION_RECEIPT` | 6 |
| Query | `QUERY_RESOLUTION`, `QUERY_EXACT_SNAPSHOT_BINDING_RULE`, `QUERY_CONFLICT_PRESERVATION_RULE` | 3 |
| Compatibility | shared `MATH_CLAIM_IR_BINDING`, `V1_MIGRATION_IMPORT_RECEIPT`, `V1_RECONCILIATION_REPORT` | 2 |
| Terminal | `TYPED_STAGE_FAMILY_TERMINAL_RESULT` | 1 |
| **Unique total** | the shared binding is counted once | **52** |

Every member of `items` contains exactly:

```text
ordinal
item_id
item_kind
source_occurrences
```

Ordinals are contiguous integers 1 through 52. `item_id` matches
`^[A-Z][A-Z0-9_]{2,127}$`. `item_kind` is exactly
`IMMUTABLE_RECORD_FAMILY`, `RAW_CONTRACT_ASSET`, or `CROSS_RECORD_RULE`.
Every source occurrence contains exactly `source_group` and the one-based
`source_position` inside that group's expansion. All items have one occurrence
except `MATH_CLAIM_IR_BINDING`, which has Mathematics position 2 and
Compatibility position 1. There are 53 occurrences and 52 unique item IDs.

The six `RAW_CONTRACT_ASSET` items are:

```text
AGENTIZATION_PROFILE_RELEASE
ARTIFACT_FAMILY_CATALOG
CANONICALIZATION_PROFILE
VALIDATION_POLICY
SIGNATURE_POLICY
STABLE_ERROR_CODE_CATALOG
```

The three `CROSS_RECORD_RULE` items are:

```text
PER_ENTRY_ELIGIBILITY
QUERY_EXACT_SNAPSHOT_BINDING_RULE
QUERY_CONFLICT_PRESERVATION_RULE
```

The remaining 43 IDs in the ordered table are
`IMMUTABLE_RECORD_FAMILY`. The validator compiles the complete ordered tuple of
ordinal, ID, kind, and source occurrences. It does not trust caller counts,
Catalog/Profile membership, or a different 52-name set. `PAPER_SOURCE_SNAPSHOT`
is excluded; Profile and terminal requirements remain explicit.

After the normative requirement-set bytes are frozen, the implementation
compiles their complete four-field root exact reference—asset ID, media type,
byte size, and SHA-256. The document cannot contain its own hash. This one-way
compiled pin ensures that a second schema-valid byte representation is not
silently treated as the official floor.

The closed schema has no numerator, percent, coverage status, maturity,
`CONTRACTED`, gap, runtime-authority, signature, bundle-membership, release,
admission, or completion field. A future coverage observation is a different
typed document that exact-references these requirement bytes.

## 4. ArtifactFamilyCatalog document schema

### 4.1 Root vocabulary, limits, and canonical order

The schema identity is:

```text
https://agtxiv.org/schema/v2/contract-kernel/contract/
  artifact-family-catalog/1.0.0
```

The raw canonical document contains exactly:

```text
document_type = AGTXIV_ARTIFACT_FAMILY_CATALOG
document_schema_ref
catalog_id
catalog_version
stages
family_policy_rows
```

It contains no Profile, requirement set, bundle, receipt, signature, coverage,
maturity, production-authority, release-effect, review-effect, or admission
field. Authority comes only from a later bundle; a Catalog cannot authorize
itself.

Namespaced document IDs use the existing 3–256 character AgtXIv pattern.
Versions use exact three-part nonnegative semantic versions without aliases.
Family, group, stage, and producer-role literals match
`^[A-Z][A-Z0-9_]{2,127}$`. Limits are: 1–64 stages, 1–256 families, 1–64 stage
policies per family, 1–64 producer roles, 1–5 outcomes, and 1–256 positive and
negative vector IDs per family. All ID and role lists are unique.

`stages` contains exactly `stage_id`, `ordinal`, and
`minimum_declared_context_mode`. Ordinals are contiguous from 1 and define the
array order. `family_policy_rows` is strictly sorted by `family_id`, and v1
requires `family_id` to be globally unique even across versions because
Checkpoint B's terminal target carries no family version. Each row's stage
policies follow Catalog stage ordinal. Roles and vector IDs are lexicographically
sorted. Outcome subsets preserve the fixed order listed in Section 4.3. These
rules give one semantic ordering rather than multiple hashes for permutations.
Every declared stage must appear in at least one family stage policy.

Every family row contains exactly:

```text
family_id
family_version
family_group
successful_artifact
stage_policies
validator_ref
validator_entry_point
conformance_vector_ref
positive_vector_ids
negative_vector_ids
```

### 4.2 Successful-artifact and support-asset roles

`successful_artifact` is exactly one of:

```text
RAW_CONTRACT_ASSET
  artifact_kind
  schema_ref
  media_type

IMMUTABLE_RECORD
  artifact_kind
  schema_ref
  record_type
```

Every `schema_ref` is a five-field `application/schema+json` reference with an
exact `schema_uri` and resolves to the offline registry. The raw branch's schema
must not declare `$defs/recordType/const`. The record branch must declare it,
and the declaration must equal `record_type`. Family ID, schema `$id`, record
type, and raw media type are separate namespaces.

`validator_ref` uses media type `text/x-python`; `validator_entry_point` is a
3–512 character dotted Python identifier naming the pure callable in those
exact source bytes. The builder exact-binds the source asset and entry-point
string but does not import code dynamically.
`conformance_vector_ref` uses `application/json`. Both resolve only from the
explicit support tuple. The positive and negative vector ID lists are nonempty,
mutually disjoint, and name entries in that exact vector asset. No support
asset may share an asset ID or raw SHA-256 digest with the requirement-set,
Catalog, or Profile root. Schema, validator, and vector roles cannot be swapped.

Catalog cannot reference its current bytes, Profile, fixture manifest, a future
bundle, or a future receipt, even through a different asset ID that supplies
identical root bytes. `latest`, `current`, a path hint, a URI fetch, or a future
digest is never a fallback. The recognized typed graph is checked for a cycle.
Validator source is an opaque leaf. Vector metadata is a typed-graph leaf: its
closed ID/target partition is parsed, but templates are not executed and it
contributes no further reference edge.

`TYPED_STAGE_FAMILY_TERMINAL_RESULT` and `TYPED_TERMINAL_RESULT` are forbidden
family IDs, and the terminal record type is forbidden as a successful artifact.
A missing terminal card must not recursively require another terminal card.

### 4.3 Stage and terminal policy

One stage policy contains exactly:

```text
stage_id
applicability
minimum_runtime_obligation
accounting_unit
cardinality
allowed_producer_roles
terminal_disposition_policy
```

V1 permits exactly this applicability/obligation matrix:

| Applicability | Minimum runtime obligation |
|---|---|
| `ALWAYS` | `CORE_REQUIRED` |
| `PROFILE_SELECTED` | `OPTIONAL_ALLOWED` |

The accounting units are `CONTRACT_ASSET_INSTANCE`, `PAPER_ATTEMPT`, and
`FROZEN_SCOPE_COMPONENT`. `cardinality` contains exactly `minimum_count` and
`maximum_count`, where maximum is a nonnegative integer or `null` for unbounded.
Core minimum is at least one; optional minimum is exactly zero; a bounded maximum
cannot be smaller than minimum. Counts are meaningful only in their declared
accounting unit.

`terminal_disposition_policy` is a closed union:

```text
FORBIDDEN
  terminal_policy_mode = FORBIDDEN

STRUCTURALLY_PERMITTED
  terminal_policy_mode = STRUCTURALLY_PERMITTED
  structurally_permitted_outcomes
  minimum_declared_context_mode
  declared_reason_policy = DEFERRED_TO_EXACT_ERROR_CATALOG
```

`CONTRACT_ASSET_INSTANCE` requires `FORBIDDEN`, avoiding a bootstrap terminal
card before its Catalog/Profile context exists. The other units may use either
mode. A permitted minimum context must be at least the parent stage minimum.

The outcome order and complete vocabulary are:

```text
UNAVAILABLE
RETRY_REQUIRED
REVIEW_REQUIRED
BLOCKED
FAILED
```

`NOT_APPLICABLE`, `UNSUPPORTED`, and `REFUTED` remain forbidden. `FAILED` is an
attempt failure, not scientific refutation; `REVIEW_REQUIRED` is a request, not
approval. Context rank is
`PROFILE_BOUND < PLAN_BOUND < FROZEN_SCOPE_BOUND`. It proves only a declared
reference shape. Reason registration remains deferred; there is no local
reason-code list.

## 5. AgentizationProfileRelease document schema

The schema identity is:

```text
https://agtxiv.org/schema/v2/contract-kernel/contract/
  agentization-profile-release/1.0.0
```

The Checkpoint C instance is fixture data, not a released Profile. The raw
canonical document contains exactly:

```text
document_type = AGTXIV_AGENTIZATION_PROFILE_RELEASE
document_schema_ref
profile_id
profile_version
profile_kind = REUSABLE_OBLIGATION_POLICY
catalog_ref
stage_rules
family_stage_rules
```

It has no requirement-set, bundle, query, paper, Plan, scope, authority,
coverage, maturity, release-effect, or admission field. `catalog_ref` is the
full exact reference to the supplied Catalog bytes. Its authoritative
projection ignores only `path_hint`; raw Profile bytes still commit a supplied
display hint.

`stage_rules` exactly mirrors Catalog stages in ordinal order. Each rule
contains only `stage_id` and `minimum_declared_context_mode`; the Profile value
may equal or strengthen the Catalog value.

`family_stage_rules` exactly mirrors every Catalog
`(family_id, family_version, stage_id)` key in family/stage order. No omission,
extra, duplicate, case alias, or renamed key is accepted. Each rule begins with
those three identity fields and `profile_requirement_adjustment`.

| Catalog policy | Allowed Profile adjustment |
|---|---|
| `ALWAYS` + `CORE_REQUIRED` | `REQUIRED` |
| `PROFILE_SELECTED` + `OPTIONAL_ALLOWED` | `REQUIRED`, `OPTIONAL`, `NOT_SELECTED` |

`NOT_SELECTED` is an explicit Profile choice, not a policy-strength comparison.
It is a closed branch without cardinality, producer, context, or terminal fields
and remains visibly present in the rule array. The terminal cross-validator
rejects a terminal result targeting this branch.

`REQUIRED` and `OPTIONAL` additionally contain exactly:

```text
cardinality
allowed_producer_roles
terminal_disposition_policy
```

They obey all of these rules:

- Profile minimum is no smaller than Catalog minimum;
- Profile maximum is no larger than a bounded Catalog maximum; a finite
  maximum may tighten an unbounded Catalog maximum;
- `REQUIRED` minimum is at least one and `OPTIONAL` minimum is exactly zero;
- allowed producer roles are a nonempty subset of Catalog roles;
- terminal mode equals the Catalog mode in both directions;
- if permitted, outcomes are a nonempty ordered subset of Catalog outcomes;
- permitted minimum context is at least the Profile stage minimum and the
  Catalog family-stage minimum; and
- reason policy remains exactly `DEFERRED_TO_EXACT_ERROR_CATALOG`.

Profile cannot repeat or change accounting unit, family kind, success schema,
record type, stage identity, or Catalog identity because those are not Profile
override fields.

## 6. Pure offline constraints and terminal application

### 6.1 Public seams

```python
@dataclass(frozen=True, slots=True)
class RawContractAssetBinding:
    exact_ref: ParsedCanonicalValue
    supplied_asset: SuppliedAsset

validate_m1_contract_requirement_set_intrinsic(
    requirements_binding: RawContractAssetBinding,
    support_assets: tuple[SuppliedAsset, ...],
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]

build_catalog_profile_constraints(
    requirements_binding: RawContractAssetBinding,
    catalog_binding: RawContractAssetBinding,
    profile_binding: RawContractAssetBinding,
    support_assets: tuple[SuppliedAsset, ...],
    registry: ContractSchemaRegistry,
) -> CatalogProfileConstraints | tuple[Diagnostic, ...]

validate_typed_terminal_result_catalog_constraints(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
    constraints: CatalogProfileConstraints,
) -> tuple[Diagnostic, ...]
```

`CatalogProfileConstraints` is a detached, recursively frozen snapshot with a
private constructor and an accidental-tamper seal like the schema registry. Its
read-only public projections are the three root exact refs, the ordered 52
requirement IDs, Catalog family IDs, and stage IDs. Private frozen policy maps
support terminal checks. It exposes no approved, released, admitted,
contracted, coverage, or maturity flag. Its integrity seal is not a signature
or defense against arbitrary code in the same interpreter.

Raw contract documents must satisfy `raw_bytes == canonical_bytes(parsed)`;
accept-then-normalize is forbidden because it would change exact asset identity.
Success from the builder is one complete snapshot; failure is a nonempty
deterministically sorted diagnostic tuple. It never returns partial constraints.

All three APIs receive every byte explicitly and perform no filesystem, network,
name service, URL, clock, environment, Git, shell, child process, database,
plugin, random, or process-global registry access. `path_hint` is display text,
never a locator.

### 6.2 Builder gates

The builder uses these hard gates:

0. **Exact-type preflight:** inspect only exact Python container/member types
   and opaque-value integrity for all inputs. If any member fails, stop before
   raw length, hashing, parsing, or semantic work.
1. **Raw binding:** snapshot all typed metadata and bytes, require unique asset
   IDs, then check exact IDs, media types, byte sizes, and raw SHA-256. Safe
   observations contain raw size/hash but no unsafe string or path hint.
2. **Canonical parse and official schema pin:** strictly parse the three roots,
   require canonical raw JSON, compare each `document_schema_ref` with the
   compiled five-field official ref, independently require the registry's
   actual schema bytes to match that compiled pin, then perform direct-root
   closed schema validation with the fixed local format checker.
3. **Reference closure:** resolve schema, validator, vector, roadmap, and exact
   Catalog refs; enforce support media roles and disjointness; reject roots as
   support aliases, self/reverse links, and cycles in the recognized typed
   graph.
4. **Requirement floor:** check source binding, selected rows, rule literal,
   complete compiled item tuple, ordering, classifications, and 53-to-52 shared
   occurrence rule.
5. **Catalog coherence:** check canonical order, global family/stage uniqueness,
   family union/schema binding, record type, applicability matrix, cardinality,
   support vector IDs, terminal recursion, outcomes, and context ranks.
6. **Profile linkage and monotonicity:** exact-bind Catalog, require stage and
   family-stage closure/order, then enforce selection, count, producer,
   terminal-mode, outcome, and context rules.

The first failing gate stops later gates. Each gate aggregates all independent
safe findings and sorts them deterministically. Type preflight is two-pass and
permutation-independent: no raw member is hashed while any input member still
has an invalid exact type. Same-declared-ID/different-byte failures remain
distinguishable by safe raw observations.

The public requirement-set validator runs the applicable requirements-only
projection of gates 0–4. The constraints builder calls the same internal logic;
the two entry points cannot reinterpret the floor differently.

### 6.3 Terminal cross-validation

The terminal API first calls Checkpoint B's
`validate_typed_terminal_result_intrinsic`; any B diagnostic hard-stops C
interpretation. It then:

1. verifies the constraints snapshot's exact type and seal;
2. exact-matches terminal `profile_ref` and `catalog_ref` after authoritative
   path-hint projection;
3. resolves the globally unique `family_id` and exact `stage_id`;
4. rejects a `NOT_SELECTED` Profile branch or a `FORBIDDEN` terminal policy;
5. checks the declared producer-context role against the Profile subset;
6. checks terminal context rank against the effective Profile minimum; and
7. checks the outcome against the Profile outcome subset.

It does not inspect reason registration, Plan/scope membership, basis/evidence
existence or relevance, resource authenticity, satisfaction, successful-output
conflict, review, or authority. Two intrinsically valid terminal records that
differ only in a syntactically valid declared reason receive the same C result.

## 7. Exact stable diagnostic additions

Checkpoint C adds exactly these `DiagnosticCode` members:

```text
AGTXIV.CONTRACT.ASSET_SCHEMA_MISMATCH
AGTXIV.CONTRACT.ASSET_INVALID

AGTXIV.REQUIREMENTS.SOURCE_BINDING_MISMATCH
AGTXIV.REQUIREMENTS.ITEM_SET_MISMATCH
AGTXIV.REQUIREMENTS.ITEM_ORDER_MISMATCH
AGTXIV.REQUIREMENTS.MAPPING_MISMATCH
AGTXIV.REQUIREMENTS.SELECTION_RULE_MISMATCH

AGTXIV.CATALOG.REFERENCE_INVALID
AGTXIV.CATALOG.EXACT_REF_CYCLE
AGTXIV.CATALOG.DUPLICATE_FAMILY
AGTXIV.CATALOG.DUPLICATE_STAGE
AGTXIV.CATALOG.STRUCTURE_INVALID
AGTXIV.CATALOG.FAMILY_BINDING_INVALID
AGTXIV.CATALOG.SUPPORT_ASSET_ROLE_INVALID
AGTXIV.CATALOG.TERMINAL_POLICY_INVALID

AGTXIV.PROFILE.CATALOG_MISMATCH
AGTXIV.PROFILE.FAMILY_SET_INVALID
AGTXIV.PROFILE.REQUIREMENT_WEAKENING
AGTXIV.PROFILE.CARDINALITY_WEAKENING
AGTXIV.PROFILE.PRODUCER_EXPANSION
AGTXIV.PROFILE.TERMINAL_POLICY_MISMATCH
AGTXIV.PROFILE.OUTCOME_EXPANSION
AGTXIV.PROFILE.CONTEXT_WEAKENING

AGTXIV.CATALOG.CONTEXT_BINDING_MISMATCH
AGTXIV.CATALOG.UNKNOWN_FAMILY
AGTXIV.CATALOG.UNKNOWN_STAGE
AGTXIV.CATALOG.OBLIGATION_NOT_SELECTED
AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED
AGTXIV.CATALOG.PRODUCER_ROLE_NOT_ALLOWED
AGTXIV.CATALOG.CONTEXT_MODE_INSUFFICIENT
AGTXIV.CATALOG.OUTCOME_NOT_ALLOWED
```

`ASSET_SCHEMA_MISMATCH` means the submitted official schema ref or registry
bytes differ from the compiled ruler. `ASSET_INVALID` means the correctly bound
raw document fails canonical/direct-root schema validation. Existing `CANON_*`,
`REF_*`, and registry codes retain their earlier meanings. No C diagnostic
claims that a reason is registered, unknown, or stable.

## 8. Frozen synthetic linkage fixture

### 8.1 Exact schema and validator assets

The four schema labels are fixed before any raw size or hash is computed:

| Role | Exact asset ID | Exact schema URI |
|---|---|---|
| requirement set | `schema:m1-contract-requirement-set:1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0` |
| Catalog | `schema:artifact-family-catalog:1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/contract/artifact-family-catalog/1.0.0` |
| Profile | `schema:agentization-profile-release:1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/contract/agentization-profile-release/1.0.0` |
| synthetic record | `schema:fixture:checkpoint-c-synthetic-record:1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/fixture/checkpoint-c-synthetic-record/1.0.0` |

Every row uses media type `application/schema+json`. After each schema file is
frozen, the implementation mechanically computes its raw byte size and
lowercase `sha256:<64 hex>` digest. It compiles the complete five-field refs for
the three official schemas into `catalog_validation.py`; the Catalog fixture
contains the synthetic schema's complete five-field ref. Tests recompute every
constant from the committed bytes. Same-URI substituted bytes fail even when
they remain valid JSON Schema.

The new contract module is supplied under asset ID
`validator:checkpoint-c-contract-documents:1.0.0`, media type
`text/x-python`, with entry point
`agtxiv_v2.contracts.catalog_validation.validate_m1_contract_requirement_set_intrinsic`
for the raw family. Its final size/hash is computed after the source file is
frozen and before Catalog bytes are assembled.

The record family instead uses the already committed generic validator:

```text
asset_id     validator:checkpoint-a-immutable-record-payload:1.0.0
media_type   text/x-python
byte_size    20377
sha256       sha256:771b5758ef6a2425d0a03c73b7b57ee84063c890b156a21be1effd8dd3a5f1cb
entry_point  agtxiv_v2.contracts.schema_validation.validate_immutable_record_payload
```

Thus `validator_ref` means the exact successful-artifact validation source,
while `validator_entry_point` identifies the callable. It does not ambiguously
mean “the Catalog linkage validator.” The builder exact-binds these
declarations; the tests actually call both operations on their vectors.

### 8.2 Complete synthetic record contract

The synthetic schema is a standalone Draft 2020-12 family schema. Its root is a
closed object requiring exactly `envelope`, `payload`, and `content_hash`:

```text
envelope
  allOf common immutable-record-envelope#/$defs/contractBoundEnvelope
  required record_type and producer_context
  record_type -> #/$defs/recordType
payload      -> #/$defs/payload
content_hash -> common digest/1.0.0
```

Its `$defs/recordType/const` is exactly
`agtxiv.checkpoint-c-synthetic-record/1.0.0`. Its `$defs/payload` is a closed
object requiring exactly:

```text
fixture_purpose = STRUCTURAL_INTEGRATION_ONLY
synthetic_artifact_id
synthetic_value
```

`synthetic_artifact_id` uses the existing 3–256 character namespaced-ID
pattern. `synthetic_value` is a 1–256 character string containing at least one
non-whitespace character. The schema exposes both `$defs/recordType` and
`$defs/payload`, so Checkpoint A's generic immutable-record validator can check
record type, payload, envelope, and canonical content hash. Standalone positive
and negative tests cover the closed root, contract-bound envelope,
producer-context requirement, payload fields, record-type mismatch, and hash
mismatch.

### 8.3 Exact fixture identities and policy

The exact root asset and document IDs are:

```text
requirements asset  requirements:m1-contract-requirement-set:1.0.0
Catalog asset       fixture-catalog:checkpoint-c-linkage/1.0.0
Catalog document    catalog:checkpoint-c-synthetic-linkage/1.0.0
Profile asset       fixture-profile:checkpoint-c-linkage/1.0.0
Profile document    profile:checkpoint-c-synthetic-linkage/1.0.0
vector asset        vectors:catalog-profile-linkage:checkpoint-c/1.0.0
```

The fixture vocabulary is fixed:

| Kind | Exact literals |
|---|---|
| stages | `CONTRACT_BOOTSTRAP` ordinal 1 / `PROFILE_BOUND`; `SYNTHETIC_ANALYSIS` ordinal 2 / `PLAN_BOUND` |
| raw family | `CHECKPOINT_C_SYNTHETIC_RAW_ASSET/1.0.0`, group `FIXTURE`, stage 1, `PROFILE_SELECTED`, `OPTIONAL_ALLOWED`, `CONTRACT_ASSET_INSTANCE`, min 0, max 1, role `CONTRACT_FIXTURE_BUILDER`, terminal forbidden, Checkpoint C requirement-set validator/entry point from Section 8.1 |
| record family | `CHECKPOINT_C_SYNTHETIC_RECORD/1.0.0`, group `FIXTURE`, stage 2, `ALWAYS`, `CORE_REQUIRED`, `PAPER_ATTEMPT`, min 1, max 1, role `SYNTHETIC_RECORD_PRODUCER`, all five outcomes, `PLAN_BOUND`, reason deferred, Checkpoint A immutable-record validator/entry point from Section 8.1 |
| Profile raw rule | `OPTIONAL`, min 0, max 1, same role, terminal forbidden |
| Profile record rule | `REQUIRED`, min 1, max 1, same role, outcomes `RETRY_REQUIRED`, `REVIEW_REQUIRED`, `BLOCKED`, `FAILED`, context strengthened to `FROZEN_SCOPE_BOUND` |

The raw family uses the official requirement-set schema as its exact successful
asset schema and `application/json` as its successful media type. The record
family uses only the dedicated non-normative schema
`https://agtxiv.org/schema/v2/contract-kernel/fixture/checkpoint-c-synthetic-record/1.0.0`
with record type `agtxiv.checkpoint-c-synthetic-record/1.0.0`. That schema is
fixture data, not a denominator item or runtime family.

The vector asset is canonical `application/json` containing exactly
`vector_set_id`, `vector_set_version`, `fixture_purpose`, and `vectors`. Every
vector contains `vector_id`, `polarity`, `vector_kind`, `template_id`, and
`expected_diagnostic_codes`. Negative vectors additionally require
`mutation_id`; positive vectors forbid it and require an empty expected-code
list. Negative vectors require at least one expected code.

`vector_kind = FAMILY_CONFORMANCE` additionally requires a closed target with
`family_id`, `family_version`, `stage_id`, and `artifact_kind`. The builder
requires every Catalog-listed positive/negative ID to have the matching
polarity and exact family/version/stage/artifact kind, and requires each family
stage to have at least one ID of each polarity. Other test-only entries use
`vector_kind = CROSS_CONTRACT_TEST` and a `cross_test_kind` of
`CATALOG_POLICY`, `PROFILE_POLICY`, or `TERMINAL_CONSTRAINT`; family rows cannot
claim those IDs as family evidence.

The production builder treats the vector document as a typed-graph leaf: it
canonical-parses its closed envelope and ID/target partition, but never expands
or executes a template or mutation. The test harness performs that expansion
and proves the expected result.

The vector set contains 1–512 entries. Vector, template, and mutation IDs use
the existing 3–256 character namespaced-ID pattern. Expected codes are sorted,
unique strings from the complete `DiagnosticCode` enum: either a pre-existing
code or one of the exact Section 7 additions. A vector has at most 32 expected
codes. The fixture purpose is exactly
`STRUCTURAL_CONFORMANCE_ONLY`; version is exactly `1.0.0`. These bounds and the
closed positive/negative branches are checked by the fixture test harness
before any template is expanded.

This asset is a non-normative fixture test-ID index. Because template expansion
is implemented only by the test source and is not exact-referenced by the
Catalog, these entries do **not** count as complete family conformance-vector
closure and cannot contribute to a `CONTRACTED` numerator. A future real
Catalog must point to self-contained vector inputs or an exact template
expander asset.

`linkage.integration-fixture.json` is explicitly test metadata, not a fourth
contract document and not an API input. Tests require canonical raw JSON and
this exact seven-field closed skeleton:

```text
fixture_purpose = STRUCTURAL_INTEGRATION_ONLY
normative_status = NON_NORMATIVE
runtime_authority = NONE
coverage_claim = NONE
requirements_ref
catalog_ref
profile_ref
```

The three refs resolve to the exact roots. Profile exact-references Catalog;
Catalog references only already fixed schema, validator, and vector bytes.
Neither root references this manifest. The scoped PASS text is:
“Catalog/Profile linkage integration fixture: PASS; this fixture changes no M1
completion count and grants no runtime authority.” It never displays `8/8`,
`12/52`, a percentage, `CONTRACTED`, `RELEASED`, `EXPOSED`, or “production
ready.”

## 9. Exact 14-path implementation allowlist

```text
schemas/v2/contract-kernel/contract/
  m1-contract-requirement-set/1.0.0.schema.json             (new)
schemas/v2/contract-kernel/contract/
  artifact-family-catalog/1.0.0.schema.json                 (new)
schemas/v2/contract-kernel/contract/
  agentization-profile-release/1.0.0.schema.json            (new)
contracts/v2/contract-kernel/requirements/
  m1-contract-requirement-set/1.0.0.json                    (new)
fixtures/v2-contract-kernel/catalog-profile/1.0.0/
  linkage.integration-fixture.json                         (new)
fixtures/v2-contract-kernel/catalog-profile/1.0.0/
  catalog.synthetic.json                                   (new)
fixtures/v2-contract-kernel/catalog-profile/1.0.0/
  profile.synthetic.json                                   (new)
fixtures/v2-contract-kernel/catalog-profile/1.0.0/
  family-conformance-vectors.json                          (new)
fixtures/v2-contract-kernel/catalog-profile/1.0.0/
  synthetic-immutable-record/1.0.0.schema.json             (new)
src/agtxiv_v2/contracts/catalog_validation.py               (new)
src/agtxiv_v2/contracts/diagnostics.py                      (modify)
src/agtxiv_v2/contracts/__init__.py                         (modify)
tests/unit/contracts/test_catalog_profile_schemas.py        (new)
tests/unit/contracts/test_catalog_profile_validation.py     (new)
```

The synthetic schema and manifest are fixture-only. No implementation commit
may modify parent roadmaps, the pytest identity baseline, aggregate validator,
demo, database, flat V2 WIP, or audit file. Staging uses only these exact paths;
the cached name set must equal the reviewed subset.

Within the implementation work, bytes are frozen in dependency order:

```text
three official schemas + synthetic schema
  -> normative requirement-set bytes
  -> diagnostics + APIs + validator source
  -> vector test-ID index
  -> Catalog fixture
  -> Profile fixture
  -> linkage manifest
  -> tests
```

The validator compiles schema and official requirement-set pins but never the
Catalog/Profile/manifest hashes. Catalog exact-references already frozen schema,
validator, and vector bytes; Profile then exact-references Catalog; manifest is
built last. If validator bytes change during testing, Catalog, Profile, and
manifest refs are regenerated before commit.

## 10. Required test matrix

### 10.1 Exact schemas and requirement floor

Tests cover all three official schema size/hash pins, same-`$id` substituted
bytes, direct-root schema validation, offline registry closure, and hostile
process-global `FormatChecker` pollution. They verify the full roadmap ref,
commit/blob identities, unique headings, LF byte slice, digest, selection-rule
literals, all selected rows, every compiled item kind/source occurrence, and
all 52 remove/rename/reorder/regroup/duplicate/add mutations. They specifically
reject a second unique Math binding, `PAPER_SOURCE_SNAPSHOT`, `M1.5` selection,
and removal of Profile or terminal requirements. Closed schemas reject every
coverage, authority, maturity, completion, release, and admission field.
The fourth synthetic schema label and full exact ref are also recomputed; its
standalone root and Checkpoint A generic record validation have positive and
closed-root/payload/type/hash negative cases. The official requirement-set root
exact ref is checked independently of its internal contents.

### 10.2 Catalog, Profile, and exact graph

Tests cover both artifact-kind branches; raw/record confusion; record-type
binding; every ID/order/limit boundary; same family ID with a second version;
stage/applicability matrix; bounded/unbounded cardinality; terminal recursion;
all five outcomes and three contexts; schema/validator/vector role swaps;
both declared validator source/entry-point pairs; empty, overlapping, unknown,
wrong-target, wrong-polarity, or reordered vector IDs; root aliases; direct and
typed cycles; stale hash; same-ID/different-byte input; and path-hint-only
identity equality. Catalog/Profile official-schema substitution fails before
coherence. All `CORE_REQUIRED` and `OPTIONAL_ALLOWED` Profile branches are
covered, including equality, valid tightening, `NOT_SELECTED`, optional min
zero, core weakening, max expansion, producer/outcome expansion, both terminal
mode toggles, and weaker context.

### 10.3 Constraints snapshot and terminal application

Tests prove private construction, detached frozen state, seal failure, input
mutation isolation, no authority-like properties, and deterministic public
projections. Terminal tests cover: B intrinsic hard-stop; exact Catalog/Profile
binding; path-hint equality; unknown family/stage; globally unique family
selection; selected/optional/not-selected rules; producer-role membership;
forbidden/permitted terminal mode; every outcome; every context boundary; and
same C result for different syntactically valid reasons. They explicitly prove
that Plan/scope/evidence/satisfaction and actor authorization are not inferred.

### 10.4 Purity, totality, and repository gates

Before any raw scan, wrong exact types, subclasses, forged opaque values, and
incomplete bindings stop at preflight. Later tests cover unpaired surrogates,
duplicate keys, noncanonical raw JSON, over-nesting, malformed assets, supplied
asset permutations, and repeated byte-identical diagnostics. Sentinels forbid
filesystem, network, DNS, URL, clock, environment, Git, subprocess, database,
plugin, random, and mutable global-registry access.

The focused suite, all `tests/unit/contracts`, the full dirty-worktree pytest
suite, and fast repository validation must pass. Dirty-tree execution is an
observation, not clean exact-commit evidence.

## 11. What C proves and what it defers

Checkpoint C can prove only:

- the exact normative 52-item requirement floor matches the pinned parent
  roadmap source and reviewed mapping;
- a submitted raw Catalog/Profile document uses the exact official schemas;
- every recognized exact ref resolves to explicitly supplied bytes in the
  closed C graph;
- Catalog family/stage policy is structurally coherent; and
- one Profile mirrors the Catalog keys, makes only Catalog-permitted optional
  selections, and cannot weaken any Catalog minimum; and
- an intrinsically valid terminal card is bound to the exact fixture
  Catalog/Profile and obeys the selected producer, family, stage, context, and
  outcome policy.

It does not prove:

- that any real runtime Catalog/Profile is published or selected;
- that any requirement is `CONTRACTED`, produced, persisted, reviewed, exposed,
  or complete;
- a ContractBundleRelease membership, signature, or production authority;
- plan/scope applicability, actual cardinality, terminal satisfaction, evidence
  relevance, role authorization, resource authenticity, or non-conflict with a
  successful artifact;
- stable reason registration or meaning;
- `NOT_APPLICABLE` or `UNSUPPORTED` policy;
- database constraints, merge review, release, archive, certification, or
  knowledge admission; or
- the arbitrary-arXiv demo, Paper Agent DAG, or mathematical formalization
  chain requested by the overall V2 goal.

Those remain visible future milestones; this checkpoint establishes only the
contract floor and one safe linkage primitive needed to reach them.

## 12. Versioned commit sequence

Checkpoint C uses four separate review surfaces:

1. **Plan-only commit:** this document.
2. **Implementation commit:** exactly the reviewed implementation allowlist.
3. **Baseline-only commit:** update only the reviewed pytest test-identity
   baseline from the exact implementation commit.
4. **Audit-only commit:** record exact commits, raw hashes, source binding,
   counts, commands, reviews, known limitations, and next blockers.

The implementation commit cannot include a baseline or audit update. The
baseline-only commit cannot rewrite tests or contract assets. The audit-only
commit cannot change normative bytes.

## 13. Definition of Done

Checkpoint C is complete only when:

1. this plan is committed before implementation;
2. the implementation diff equals the final reviewed allowlist and preserves
   all unrelated user work;
3. the three official schemas and the synthetic fixture schema are closed,
   meta-valid, registry-resolvable, and pinned by full exact raw refs;
4. the normative floor binds the exact parent-roadmap bytes and mechanically
   yields the exact reviewed 52-item ordered unique set;
5. Catalog/Profile fixture refs form the one-way graph and all referenced bytes
   are real, fixed, and locally supplied;
6. Catalog family kinds, stage policies, terminal outcome/context policy, and
   terminal-recursion exclusion pass every positive and adversarial vector;
7. Profile key equality and monotonic selection/cardinality/producer/outcome/
   context rules pass every matrix boundary;
8. reason registration remains explicitly deferred and no shadow ErrorCatalog
   is introduced;
9. the builder returns only a sealed complete snapshot or diagnostics, and the
   terminal API applies B intrinsic validation before exact C constraints;
10. all three APIs are pure, total, deterministic, and documented as
    non-authority;
11. focused, contract, full working-tree, and fast repository checks introduce
    no failure, with environment-assurance limits reported honestly;
12. the exact implementation test identity is generated twice byte-identically,
    reviewed as additions only from the two allowed new test files, and committed
    in a baseline-only commit;
13. independent adversarial review has zero open Priority 0 or Priority 1
    findings;
14. reader review confirms the three-checklist intuition, expands unfamiliar
    terms, avoids unnecessary abbreviations, and cannot mistake the integration
    fixture for a released Catalog/Profile; and
15. the audit preserves `M1: NOT COMPLETE`, makes no percentage or numerator
    claim, and grants no runtime, release, merge, or admission authority.

Completion authorizes only the next contract-kernel design checkpoint. It does
not authorize merge to a protected branch or any release/database admission.

## 14. Next checkpoint

The next checkpoint must choose the smallest dependency-complete step between:

- the exact stable-error catalog and validation policy required before reasons
  can be registered; and
- `AgentizationPlan -> InventoryDiscoveryResult -> independent
  ScopeFreezeDecision -> FrozenInventoryScope`, which turns reusable Catalog/
  Profile rules into a paper-specific frozen denominator.

That choice requires a new multi-agent principle review. A real eight-row
Catalog is published only after every referenced family schema, validator,
positive vector, negative vector, and cross-record policy exists as fixed bytes.
Only a later bundle/coverage checkpoint may compute scoped contract progress;
it must always display the whole 52-item M1 floor and all named gaps beside any
local slice result.
