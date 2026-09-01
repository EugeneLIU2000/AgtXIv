# AgtXIv V2 M1 contract kernel — Checkpoint D: stable code catalog and kernel validation policy

- Document status: plan only; not implementation or audit evidence
- Document version: 1.0
- Checkpoint status: proposed and intentionally incomplete
- Committed basis: `81824846591d00f014e8f88ddefbda034ea3db01`
- Predecessor: `docs/roadmaps/v2-m1-contract-kernel-checkpoint-c.md`
- Predecessor audit: `docs/audits/v2-m1-contract-kernel-checkpoint-c-2026-08-31.md`
- Governing ADRs: `docs/adr/0002-contract-bundle-binding.md` and `docs/adr/0003-plan-discovery-scope-freeze.md`
- Date: 2026-09-01
- Authority: none for production/runtime selection, obligation satisfaction,
  coverage, merge, release, archive, certification, database admission, or
  knowledge admission

Checkpoint D implements only the narrowed A0/A-mini prerequisite selected by two
external principle reviews: one stable machine-code catalog, one kernel
validation-policy candidate, and one composition gate that proves a terminal
reason is registered before it is accepted. This is the minimum prerequisite on
the direct path to the planning contracts. It is not permission to expand the
complete error/policy design into a long-running side branch.

The two reviews were external, non-repository review inputs received on
2026-09-01. Their shared conclusion was: implement narrowed A0 first, then move
directly to Plan -> Discovery -> ScopeFreeze. Their raw review text is not a
committed blob and this plan does not claim that it is archived or independently
reconstructible from Git. The repository-internal normative decision is this plan
itself once reviewed and committed.

Immediately after D is audited, the default next checkpoint is a **plan-only
principle review for the planning-contract option / proposed Checkpoint E**:
`AgentizationPlan -> InventoryDiscoveryResult -> ScopeFreezeDecision ->
FrozenInventoryScope`. Proposed Checkpoint E is wholly distinct from the already
audited typed-terminal Checkpoint B. D neither defines nor implements those
planning records and never modifies typed-terminal Checkpoint B bytes or code.

## 1. Intuition and terms

A stable code catalog is a dictionary, not a log message file. It says which
machine token exists, what kind of token it is, and the meaning that compatible
software must preserve. A kernel validation policy is a wiring diagram. It says
which exact dictionary, structural Catalog/Profile constraints, validator bytes,
and terminal-reason registrations compose for this candidate. The composition
gate checks the wiring after the existing structural checks have succeeded.

The distinction below is normative:

- **`VALIDATION_DIAGNOSTIC`** is a code emitted by contract-validation software
  about invalid or nonconforming input. Python `DiagnosticCode` is exactly the
  compiled projection of this kind, in both directions and in declaration order.
- **`TERMINAL_REASON`** is a reason declared inside an intrinsically valid
  `TypedTerminalResult`. It describes why an operational attempt stopped. It is
  not a validator diagnostic and must never be inserted into `DiagnosticCode`.
- **Stable code meaning** is the normative compatibility statement attached to a
  code. Reusing a code with a changed meaning is forbidden.
- **Message** is human-facing explanatory text attached to one diagnostic or
  terminal record. Messages and terminal summaries are non-normative and may be
  improved without changing code identity or meaning.
- **Reason registration** is a policy row allowing one `TERMINAL_REASON` for
  exact outcomes, retry dispositions, context modes, and Catalog family-stage
  targets. Registration does not prove that the reason is true or sufficient.
- **Composition gate** is one call to C's public terminal gate—which internally
  runs typed-terminal Checkpoint B intrinsic validation and then C structural
  validation—followed by D reason policy. It grants no obligation-satisfaction or
  lifecycle authority.
- **Policy candidate** means structurally valid bytes suitable for later bundle
  consideration. It is not a production policy and cannot select itself.

The only terminal reason registered in D is the already used synthetic test
literal:

```text
AGTXIV.TERMINAL.EXAMPLE
```

The committed typed-terminal Checkpoint B and Checkpoint C tests use those exact ASCII bytes. Their summaries include
`The dependency is not ready.` and `One operational attempt stopped.`; those
summaries are intentionally not the reason's stable meaning. D freezes the code's
meaning as: **a synthetic terminal reason used only to demonstrate contract-kernel
registration and composition; it makes no domain, production, satisfaction,
review, or release claim.**

No reason for the planning-contract option / proposed Checkpoint E is guessed or
pre-registered. Proposed Checkpoint E must introduce only reasons it actually
uses through a newly planned catalog and policy schema/version; it must not
overwrite D's `1.0.0` bytes or modify typed-terminal Checkpoint B bytes or code.

## 2. Scope and authority boundary

### 2.1 In scope

D adds exactly:

1. a closed `StableCodeCatalog/1.0.0` raw-document schema and canonical genesis
   asset;
2. a closed `KernelValidationPolicy/1.0.0` raw-document schema and canonical
   candidate asset;
3. pure offline validators and sealed policy constraints;
4. exact equality between the catalog's `VALIDATION_DIAGNOSTIC` projection and
   the final compiled Python enum;
5. registration of `AGTXIV.TERMINAL.EXAMPLE` against the existing C synthetic
   family-stage constraints;
6. a final terminal-validation entry point that calls C once—thereby running
   typed-terminal Checkpoint B intrinsic then C structural validation once—and
   runs D reason validation only after that call succeeds;
7. a non-normative vector index and linkage manifest; and
8. focused schema and adversarial tests.

### 2.2 Explicitly out of scope

D contains no planning records, source snapshot, source acquisition, bundle,
contract-bundle release, CAS, intake, runner, API, database, demo, archive,
certificate, admission transaction, signature policy, coverage numerator, or
runtime policy. It does not modify the frozen terminal, Catalog, Profile, common,
or requirement-set `1.0.0` bytes.

In particular, D does not implement:

- `AgentizationPlan`, `InventoryDiscoveryResult`, `ScopeFreezeDecision`, or
  `FrozenInventoryScope`;
- plan/scope membership, component cardinality, evidence resolution/relevance,
  resource-observation authenticity, successful-artifact conflict, or terminal
  satisfaction;
- actor authorization, reviewer independence, signatures, release, archive,
  certification, merge, database admission, or knowledge admission; or
- arbitrary-arXiv execution, Paper Agent DAG production, or the mathematical
  formalization chain.

`validate_typed_terminal_result_catalog_constraints` remains C's
**reason-unaware structural validator**. Its name and semantics are preserved.
It must not be documented as complete validation and must not silently acquire D
behavior. Callers wanting the final D composition must use the new D entry point.

## 3. Authority and dependency graph

The stable-code catalog defines code identity and meaning. The policy selects an
exact catalog and exact C structural constraints. Neither document authorizes
itself. A future `ContractBundleRelease`, outside D, may bind them after its own
review and release process.

The recognized byte/hash DAG is one-way:

```text
frozen common + terminal + C official schemas
frozen C requirement/Catalog/Profile raw roots
                    |
D official schemas  |  final diagnostics.py + code_policy_validation.py
        |            |                 |
        +------------+-----------------+
                     |
       StableCodeCatalog/1.0.0 raw bytes
                     |
       non-normative conformance-vector index
                     |
       KernelValidationPolicy/1.0.0 raw bytes
                     |
       non-normative linkage manifest
```

More precisely:

- both D raw documents exact-reference their official schema bytes;
- the policy exact-references the D stable-code catalog, C normative requirement
  set, C synthetic Catalog, C synthetic Profile, the frozen typed-terminal Checkpoint B schema,
  the final D validator source, and the vector index;
- the policy's family-stage registrations are checked against a valid sealed C
  `CatalogProfileConstraints` snapshot built from those exact C roots;
- the code catalog does not reference the policy;
- neither root references the linkage manifest;
- no document contains its own hash, a future hash, a receipt about itself, or a
  reference to a future bundle; and
- validator source compiles official D schema pins but not the final catalog or
  policy raw hash, avoiding a validator/document cycle.

Existing C projections continue to treat any already committed `path_hint` as
display-only, but every exact reference serialized inside either D root forbids a
`path_hint` field. No path, URI, `latest`, branch, environment, or process-global
registry may resolve an authoritative reference.

## 4. Exact schemas and document identities

Both D schemas are standalone closed Draft 2020-12 documents. They inline a
D-specific closed exact-asset-ref shape and use only local `#/$defs` references;
they do not add a remote or common-schema edge. The D-specific shape requires the
four authoritative fields and `schema_uri` only where the role requires it, and
**forbids `path_hint` in every D catalog, policy, validator, vector, terminal,
requirement, Catalog, and Profile ref**. Each exact ref's canonical JSON encoding
must be at most `maximum_exact_ref_bytes = 2048`: the schema proves per-field
string maxima and closed membership, while the semantic validator recomputes
`len(canonical_bytes(ref)) <= 2048`. This avoids inheriting the existing common
ref's independently permitted 4,096-character display hint. The Draft URI is a
dialect identifier, not a fetch instruction. Consequently D needs to locate and
pin only these two D schema entries in the already sealed registry.

### 4.1 Stable code catalog

Official schema path:

```text
schemas/v2/contract-kernel/contract/
  stable-code-catalog/1.0.0.schema.json
```

Exact schema identity and asset label:

```text
schema URI  https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.0.0
asset ID    schema:stable-code-catalog:1.0.0
media type  application/schema+json
```

Canonical document path and identity:

```text
contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json
asset ID         code-catalog:agtxiv-contract-kernel/1.0.0
document_type    AGTXIV_STABLE_CODE_CATALOG
catalog_id       code-catalog:agtxiv-contract-kernel
catalog_version  1.0.0
catalog_kind     CONTRACT_KERNEL_MACHINE_CODES
revision_kind    GENESIS
```

The root is closed and contains exactly:

```text
document_type
document_schema_ref
catalog_id
catalog_version
catalog_kind
revision_kind = GENESIS
compatibility_rules
resource_limits
codes
```

D defines only immutable genesis catalog `1.0.0`. Its schema has no predecessor,
successor, parent, supersession, or inherited-catalog field, and the D APIs accept
no ancestor-catalog input. A future catalog revision must be designed by a future
plan and schema version. The only forward-compatibility commitments frozen here
are that the `1.0.0` bytes are never overwritten and an existing code is never
reused with a different kind or meaning.

`compatibility_rules` contains exactly these frozen literals:

```text
code_identity_rule       NEVER_REUSE_EXISTING_CODE
kind_rule                NEVER_CHANGE_EXISTING_KIND
meaning_rule             NEVER_CHANGE_MEANING_CREATE_NEW_CODE
kind_order_rule          VALIDATION_DIAGNOSTIC_THEN_TERMINAL_REASON
message_rule             NON_NORMATIVE_NOT_CATALOGED
python_projection_rule   VALIDATION_DIAGNOSTIC_BIJECTION_IN_ENUM_ORDER
```

`resource_limits` contains exactly:

```text
exact_code_entries                79
maximum_code_utf8_bytes          256
maximum_meaning_utf8_bytes      4096
maximum_code_entry_bytes        4880
maximum_root_metadata_bytes    16384
maximum_catalog_root_bytes     401904
```

The catalog has exactly 78 diagnostic rows and one reason row. The per-entry bound
is conservatively derived as $256 + 4096 + 16 + 512 = 4{,}880$ bytes: code,
meaning, semantic-version literal, and all fixed keys/discriminators/JSON syntax.
The root bound is exactly $79 \times 4{,}880 + 16{,}384 = 401{,}904$ bytes.
Schema field limits, the canonical raw asset, and compiled preflight constants
repeat these values. The exact root byte count is checked against
`maximum_catalog_root_bytes` before copying, hashing, parsing, or enum work. Tests
exercise every field boundary and the root limit/limit+1. An implementation-only
hidden byte limit is forbidden.

Each member of `codes` is a closed union with common fields:

```text
code
code_kind
kind_ordinal
meaning
introduced_in_catalog_version
status
```

D permits exactly two `code_kind` literals in fixed kind order:

```text
VALIDATION_DIAGNOSTIC
TERMINAL_REASON
```

`status` is exactly `ACTIVE` in the genesis asset. No deprecation or replacement
shape is invented in D. Codes match the existing terminal-code grammar,
meanings are nonblank NFC strings with 1–4096 UTF-8 bytes, ordinals are positive
I-JSON integers, and introduced versions are strict three-part semantic versions.
Unknown fields and unknown code kinds fail closed.

Canonical order is normative:

1. all `VALIDATION_DIAGNOSTIC` rows appear first, with contiguous
   `kind_ordinal` values starting at 1 and exact order equal to Python
   `DiagnosticCode` declaration order;
2. all `TERMINAL_REASON` rows follow, with an independent contiguous ordinal
   sequence and strict UTF-8 byte order by code; and
3. no code may occur twice, even across kinds.

The final D catalog contains every member of the **post-D** `DiagnosticCode` enum
exactly once as `VALIDATION_DIAGNOSTIC`, plus exactly one `TERMINAL_REASON`,
`AGTXIV.TERMINAL.EXAMPLE`. The terminal reason is not an enum member.

### 4.2 Kernel validation policy

Official schema path:

```text
schemas/v2/contract-kernel/contract/
  kernel-validation-policy/1.0.0.schema.json
```

Exact schema identity and asset label:

```text
schema URI  https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.0.0
asset ID    schema:kernel-validation-policy:1.0.0
media type  application/schema+json
```

Canonical document path and identity:

```text
contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.0.0.json
asset ID        validation-policy:checkpoint-d-kernel-candidate/1.0.0
document_type   AGTXIV_KERNEL_VALIDATION_POLICY
policy_id       validation-policy:checkpoint-d-kernel-candidate
policy_version  1.0.0
policy_kind     CONTRACT_KERNEL_COMPOSITION
policy_status   CANDIDATE_NON_AUTHORITY
revision_kind   GENESIS
```

The root is closed and contains exactly:

```text
document_type
document_schema_ref
policy_id
policy_version
policy_kind
policy_status
revision_kind
code_catalog_ref
structural_constraints_ref
terminal_schema_ref
validator_ref
validator_entry_points
conformance_vector_ref
gate_order
resource_limits
terminal_reason_registrations
```

`structural_constraints_ref` is closed and contains exactly:

```text
requirements_ref
catalog_ref
profile_ref
constraint_source = CHECKPOINT_C_SEALED_CONSTRAINTS
```

The exact inherited refs are:

```text
requirements
  asset_id   requirements:m1-contract-requirement-set:1.0.0
  media_type application/json
  byte_size  12775
  sha256     sha256:b8c14e570f94934b56b0a0447c856d9d37eb2db9ede6aa6c191280ff618058f9

Catalog
  asset_id   fixture-catalog:checkpoint-c-linkage/1.0.0
  media_type application/json
  byte_size  3889
  sha256     sha256:86958f085abf04e382c262d3e8aa9181039a565947b7dfd8e2153d39c4903be0

Profile
  asset_id   fixture-profile:checkpoint-c-linkage/1.0.0
  media_type application/json
  byte_size  1770
  sha256     sha256:e794945c8ca6c2c85d5da899f1e9773134c1b33e9a541b7550007f3167c2f8c9

terminal schema
  asset_id   schema:typed-terminal-result:1.0.0
  media_type application/schema+json
  byte_size  16054
  sha256     sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6
  schema_uri https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0
```

The D code-catalog, validator, vector, and policy-schema sizes/hashes are computed
only after their source bytes are frozen. Tests recompute every compiled value
from raw committed bytes. Same-ID or same-URI substituted bytes fail.

`validator_entry_points` is closed and contains exactly these strings:

```text
catalog_intrinsic
  agtxiv_v2.contracts.code_policy_validation.validate_stable_code_catalog_intrinsic
policy_builder
  agtxiv_v2.contracts.code_policy_validation.build_kernel_validation_policy_constraints
diagnostic_registration
  agtxiv_v2.contracts.code_policy_validation.validate_emitted_diagnostic_registration
terminal_composition
  agtxiv_v2.contracts.code_policy_validation.validate_typed_terminal_result_kernel_constraints
```

The fixed `gate_order` is:

```text
CODE_CATALOG_INTRINSIC
PYTHON_DIAGNOSTIC_BIJECTION
POLICY_INTRINSIC_AND_EXACT_BINDING
EMITTED_DIAGNOSTIC_REGISTRATION
TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC
TERMINAL_D_REASON_POLICY
```

`resource_limits` contains exactly:

```text
exact_policy_roots                         2
exact_support_assets                       2
maximum_catalog_root_bytes            401904
maximum_exact_ref_bytes                  2048
maximum_policy_root_bytes              27072
maximum_total_root_bytes               428976
maximum_validator_source_bytes        1048576
maximum_vectors                           512
maximum_vector_entry_bytes               2048
maximum_vector_index_bytes            1064960
maximum_total_support_bytes           2113536
maximum_total_d_input_bytes           2542512
exact_code_entries                         79
exact_reason_registrations                   1
exact_targets_per_registration               1
exact_total_reason_targets                   1
maximum_emitted_diagnostics                4096
```

The policy-root bound is derived from the closed shape, not chosen invisibly:
$8 \times 2{,}048$ bytes for its official and exact asset refs,
$4 \times 512$ for entry-point strings, $10 \times 128$ for fixed gate/identity/
resource-limit literals, 3,264 for the sole closed registration and target at
their field maxima, and 4,096 for remaining fixed keys and JSON syntax, totaling
27,072. The increase from seven to ten fixed literals accounts exactly for the
new `maximum_exact_ref_bytes`, `maximum_vectors`, and
`maximum_vector_entry_bytes` fields: $3 \times 128 = 384$ bytes. The vector index
permits at most 512 closed vectors at 2,048 bytes each plus 16,384 root bytes,
totaling 1,064,960. The validator role permits 1,048,576 source bytes. Thus roots
are exactly bounded by $401{,}904 + 27{,}072 = 428{,}976$, supports by
$1{,}048{,}576 + 1{,}064{,}960 = 2{,}113{,}536$, and all D-controlled input bytes
by 2,542,512.

The schema fixes exactly 79 catalog entries, one synthetic reason registration,
and one exact C family-stage target; D does not admit the full C Cartesian space.
Every listed resource-limit field is required by the closed policy schema, has the
exact integer value above, and is repeated in compiled constants. Policy
validation requires field-for-field equality with that complete compiled map;
omission, addition, or mutation of any limit fails closed. Preflight checks outer
counts and `len(raw_bytes)` for both roots and exactly two support assets before
any copy, hash, parse, enum projection, or vector expansion. After canonical
parse, semantic validation enforces the exact 79-entry and one-registration shape,
the 2,048-byte canonical-ref limit, and vector count/entry limits. Tests cover
every per-item and aggregate limit and limit+1.

Each terminal reason registration is a closed object containing exactly:

```text
reason_code
registration_kind = SYNTHETIC_COMPOSITION_ONLY
allowed_outcomes
allowed_retry_dispositions
allowed_context_modes
targets
```

Each closed target contains exactly:

```text
family_id
family_version
stage_id
```

Registration arrays use these fixed canonical orders:

- outcomes: `UNAVAILABLE`, `RETRY_REQUIRED`, `REVIEW_REQUIRED`, `BLOCKED`,
  `FAILED`;
- retry dispositions: `RETRY_AFTER_CONDITION`,
  `NO_RETRY_IN_CURRENT_CONTEXT`, `REVIEW_DECIDES`;
- contexts: `PROFILE_BOUND`, `PLAN_BOUND`, `FROZEN_SCOPE_BOUND`;
- registrations: strict UTF-8 order by reason code; and
- targets: C Catalog family order, then C stage ordinal.

Unknown code, code kind, outcome, retry disposition, context mode, family, family
version, or stage fails closed. Every reason code must resolve to one active
`TERMINAL_REASON`; it may not resolve to a `VALIDATION_DIAGNOSTIC`. Every target
must resolve to one selected, terminal-permitted C policy. Empty registrations,
empty constraints, duplicate values, reordered values, and broad wildcard
strings are forbidden.

The sole D registration targets:

```text
reason_code       AGTXIV.TERMINAL.EXAMPLE
family_id         CHECKPOINT_C_SYNTHETIC_RECORD
family_version    1.0.0
stage_id          SYNTHETIC_ANALYSIS
outcomes          RETRY_REQUIRED, REVIEW_REQUIRED, BLOCKED, FAILED
retry dispositions RETRY_AFTER_CONDITION,
                   NO_RETRY_IN_CURRENT_CONTEXT,
                   REVIEW_DECIDES
contexts          FROZEN_SCOPE_BOUND
```

The outcomes and context are exactly the effective C synthetic Profile subset.
The retry set is a registration ceiling; typed-terminal Checkpoint B's intrinsic
outcome/retry matrix runs inside the C public gate and remains stricter for each
individual outcome. No registration can legalize a pair invalid under
typed-terminal Checkpoint B or a C-forbidden target.

## 5. Genesis immutability and deferred revision semantics

D defines exactly two genesis documents: stable-code catalog `1.0.0` and kernel
validation policy `1.0.0`. Both schemas require their exact version and
`GENESIS`; neither schema accepts a predecessor, successor, inherited state,
supersession, or version-range field. Neither D public API accepts predecessor or
ancestor assets. Consequently D makes no claim that it can mechanically validate
a future policy or catalog version transition.

The `1.0.0` bytes are immutable. Existing code identity, kind, ordinal, and stable
meaning must not be changed in place; a changed meaning requires a new code under
a future reviewed design. Human messages remain outside the catalog and are not
part of this compatibility statement.

Successor catalog inheritance, policy revision, version increments, deprecation,
replacement, and supersession are all deferred to a future plan and schema
version. The planning-contract option / proposed Checkpoint E may not assume a
revision format from D: it must first plan the exact new catalog/policy schema and
mechanical inputs for reasons it actually uses. It must not overwrite D `1.0.0`
or modify typed-terminal Checkpoint B bytes or code. These immutability rules
grant no release or runtime selection authority.

## 6. Stable validation diagnostics and bootstrap

The following table is the complete normative `VALIDATION_DIAGNOSTIC` projection.
Its 78 rows, ordinals, exact code bytes, and stable meanings are implementation
inputs, not implementation choices. “Existing A, typed-terminal Checkpoint B, or
C contract” means the meaning is consolidated from the named committed validator
and its checkpoint plan;
“frozen by D” means this plan is the first normative source. The canonical asset
must copy these meanings byte-for-byte after NFC normalization.

| Ordinal | Code | Stable meaning | Normative source |
|---:|---|---|---|
| 1 | `AGTXIV.CANON.BOM_FORBIDDEN` | Input begins with a forbidden UTF-8 byte-order mark. | Existing A contract (`canonical.py`). |
| 2 | `AGTXIV.CANON.INVALID_UTF8` | Input bytes are not valid strict UTF-8. | Existing A contract (`canonical.py`). |
| 3 | `AGTXIV.CANON.INVALID_JSON` | UTF-8 input is not one complete syntactically valid JSON value. | Existing A contract (`canonical.py`). |
| 4 | `AGTXIV.CANON.DUPLICATE_KEY` | A JSON object contains the same member name more than once before normalization. | Existing A contract (`canonical.py`). |
| 5 | `AGTXIV.CANON.NORMALIZED_KEY_COLLISION` | Distinct object member names collide after required Unicode normalization. | Existing A contract (`canonical.py`). |
| 6 | `AGTXIV.CANON.UNPAIRED_SURROGATE` | A string contains an unpaired Unicode surrogate code point. | Existing A contract (`canonical.py`). |
| 7 | `AGTXIV.CANON.UNSUPPORTED_NUMBER` | A JSON number uses a numeric form outside the canonical profile. | Existing A contract (`canonical.py`). |
| 8 | `AGTXIV.CANON.INTEGER_OUT_OF_RANGE` | An integer lies outside the permitted I-JSON exact-integer range. | Existing A contract (`canonical.py`). |
| 9 | `AGTXIV.CANON.NESTING_TOO_DEEP` | A submitted value exceeds the canonical maximum nesting depth. | Existing A contract (`canonical.py`). |
| 10 | `AGTXIV.CANON.UNSUPPORTED_PROGRAMMATIC_TYPE` | A programmatic input contains a value whose exact Python type is outside the canonical JSON model. | Existing A contract (`canonical.py`). |
| 11 | `AGTXIV.CANON.NON_STRING_OBJECT_KEY` | A programmatic object has a member key whose exact type is not string. | Existing A contract (`canonical.py`). |
| 12 | `AGTXIV.CANON.CYCLIC_PROGRAMMATIC_VALUE` | A programmatic array or object contains an identity cycle. | Existing A contract (`canonical.py`). |
| 13 | `AGTXIV.CANON.INVALID_RECORD_SHAPE` | A value submitted for record hashing lacks the exact required record projection shape. | Existing A contract (`canonical.py`). |
| 14 | `AGTXIV.CANON.INVALID_INTERNAL_VALUE` | An opaque canonical value fails its internal integrity invariant. | Existing A contract (`canonical.py`). |
| 15 | `AGTXIV.REF.UNRESOLVED` | An exact asset, record, or component reference has no uniquely supplied target. | Existing A contract (`references.py`). |
| 16 | `AGTXIV.REF.HASH_MISMATCH` | Supplied target bytes, byte size, or canonical content hash differ from the exact reference. | Existing A contract (`references.py`). |
| 17 | `AGTXIV.REF.TYPE_MISMATCH` | A resolved target has the wrong declared media, schema, record, or component type for the reference. | Existing A contract (`references.py`). |
| 18 | `AGTXIV.CONTRACT.MUTABLE_REF` | A contract-bound authoritative reference contains mutable or non-exact identity. | Existing A contract (`references.py`). |
| 19 | `AGTXIV.RECORD.INVALID_ENVELOPE` | An immutable record envelope is absent, open, malformed, or inconsistent with its required closed shape. | Existing A contract (`references.py`). |
| 20 | `AGTXIV.RECORD.SUPERSESSION_MISMATCH` | A record revision or supersession relation is inconsistent with immutable revision rules. | Existing A contract (`references.py`). |
| 21 | `AGTXIV.RECORD.HASH_MISMATCH` | A record's declared content hash differs from its canonical record-hash projection. | Existing A contract (`references.py`). |
| 22 | `AGTXIV.SCHEMA.EMPTY_REGISTRY` | Schema-registry construction received no schema bindings. | Existing A contract (`registry.py`). |
| 23 | `AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH` | A schema or validator API received an input with an invalid exact type or failed opaque/sealed integrity. | Existing A, typed-terminal Checkpoint B, and C contracts (`registry.py` and validators). |
| 24 | `AGTXIV.SCHEMA.INVALID_DOCUMENT` | Strict parsing succeeded, but the supplied schema is not one top-level JSON object. | Existing Checkpoint A contract (`registry.py`). |
| 25 | `AGTXIV.SCHEMA.DIALECT_MISMATCH` | A schema does not declare the required JSON Schema Draft 2020-12 dialect. | Existing A contract (`registry.py`). |
| 26 | `AGTXIV.SCHEMA.ID_MISMATCH` | A schema's `$id`, schema URI, or exact binding identities disagree. | Existing A contract (`registry.py`). |
| 27 | `AGTXIV.SCHEMA.DUPLICATE_ID` | More than one supplied schema claims the same authoritative schema identity. | Existing A contract (`registry.py`). |
| 28 | `AGTXIV.SCHEMA.META_INVALID` | A schema fails the supported dialect's meta-schema or closed-keyword constraints. | Existing A contract (`registry.py`). |
| 29 | `AGTXIV.SCHEMA.UNRESOLVED_REF` | A schema `$ref` does not resolve inside the explicit offline registry. | Existing A contract (`registry.py`). |
| 30 | `AGTXIV.SCHEMA.REFERENCE_CYCLE` | The admitted schema-reference graph contains a forbidden cycle. | Existing A contract (`registry.py`). |
| 31 | `AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN` | A schema reference would require remote or non-registry resolution. | Existing A contract (`registry.py`). |
| 32 | `AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH` | A record's declared record type differs from the exact family schema's record-type declaration. | Existing A contract (`schema_validation.py`). |
| 33 | `AGTXIV.RECORD.PAYLOAD_INVALID` | A record payload violates its exact family schema. | Existing A contract (`schema_validation.py`). |
| 34 | `AGTXIV.TERMINAL.SCHEMA_MISMATCH` | A typed terminal record does not bind the compiled official terminal schema bytes. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 35 | `AGTXIV.TERMINAL.ATTEMPT_MISMATCH` | Terminal payload attempt identity or producer context is absent or differs from the envelope attempt. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 36 | `AGTXIV.TERMINAL.CONTEXT_INVALID` | A terminal binding context and its target basis have an intrinsically inconsistent shape or identity. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 37 | `AGTXIV.TERMINAL.TARGET_INVALID` | A terminal target is intrinsically recursive or otherwise forbidden as a terminal obligation target. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 38 | `AGTXIV.TERMINAL.EVIDENCE_INVALID` | Terminal evidence has duplicate IDs/references, noncanonical order, or a forbidden terminal/self reference. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 39 | `AGTXIV.TERMINAL.DISPOSITION_INVALID` | Terminal outcome, retry disposition, or next action violates the intrinsic compatibility matrix. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 40 | `AGTXIV.TERMINAL.RESOURCE_INVALID` | Declared resource dimensions, ordering, partition, or observed-limit relation is mechanically inconsistent. | Existing typed-terminal Checkpoint B contract (`terminal_validation.py`). |
| 41 | `AGTXIV.CONTRACT.ASSET_SCHEMA_MISMATCH` | A raw contract document's official schema ref or registry schema bytes differ from the compiled ruler. | Existing C contract (`catalog_validation.py`). |
| 42 | `AGTXIV.CONTRACT.ASSET_INVALID` | A correctly bound raw contract document is noncanonical or violates its exact official schema. | Existing C contract (`catalog_validation.py`). |
| 43 | `AGTXIV.REQUIREMENTS.SOURCE_BINDING_MISMATCH` | Requirement-set roadmap bytes, Git blob identity, bounded section, or exact source ref differs from the frozen source. | Existing C contract (`catalog_validation.py`). |
| 44 | `AGTXIV.REQUIREMENTS.ITEM_SET_MISMATCH` | Requirement item membership or uniqueness differs from the compiled 52-item floor. | Existing C contract (`catalog_validation.py`). |
| 45 | `AGTXIV.REQUIREMENTS.ITEM_ORDER_MISMATCH` | Requirement item order, kind, or source occurrence differs from the compiled floor. | Existing C contract (`catalog_validation.py`). |
| 46 | `AGTXIV.REQUIREMENTS.MAPPING_MISMATCH` | Selected roadmap rows or their reviewed requirement expansion differs from the frozen mapping. | Existing C contract (`catalog_validation.py`). |
| 47 | `AGTXIV.REQUIREMENTS.SELECTION_RULE_MISMATCH` | Requirement milestone selection differs from the exact M1-token rule. | Existing C contract (`catalog_validation.py`). |
| 48 | `AGTXIV.CATALOG.REFERENCE_INVALID` | A Catalog/Profile root or support reference is unresolved, aliased, excessive, or invalid for its declared graph role. | Existing C contract (`catalog_validation.py`). |
| 49 | `AGTXIV.CATALOG.EXACT_REF_CYCLE` | The recognized Catalog/Profile exact-reference graph contains a root alias or cycle. | Existing C contract (`catalog_validation.py`). |
| 50 | `AGTXIV.CATALOG.DUPLICATE_FAMILY` | Catalog family identity is duplicated under the v1 global-family rule. | Existing C contract (`catalog_validation.py`). |
| 51 | `AGTXIV.CATALOG.DUPLICATE_STAGE` | Catalog stage identity is duplicated. | Existing C contract (`catalog_validation.py`). |
| 52 | `AGTXIV.CATALOG.STRUCTURE_INVALID` | Catalog ordering, uniqueness, applicability, cardinality, vector, or stage-coverage structure is invalid. | Existing C contract (`catalog_validation.py`). |
| 53 | `AGTXIV.CATALOG.FAMILY_BINDING_INVALID` | A family successful-artifact kind, schema, or record-type binding is inconsistent. | Existing C contract (`catalog_validation.py`). |
| 54 | `AGTXIV.CATALOG.SUPPORT_ASSET_ROLE_INVALID` | Catalog validator or vector bytes do not resolve in the exact declared support role or target partition. | Existing C contract (`catalog_validation.py`). |
| 55 | `AGTXIV.CATALOG.TERMINAL_POLICY_INVALID` | Catalog terminal recursion, outcome order, context minimum, or accounting-unit terminal policy is invalid. | Existing C contract (`catalog_validation.py`). |
| 56 | `AGTXIV.PROFILE.CATALOG_MISMATCH` | A Profile does not exact-bind the supplied Catalog bytes. | Existing C contract (`catalog_validation.py`). |
| 57 | `AGTXIV.PROFILE.FAMILY_SET_INVALID` | Profile stage or family-stage keys do not exactly mirror Catalog membership and order. | Existing C contract (`catalog_validation.py`). |
| 58 | `AGTXIV.PROFILE.REQUIREMENT_WEAKENING` | A Profile weakens or deselects a Catalog core requirement. | Existing C contract (`catalog_validation.py`). |
| 59 | `AGTXIV.PROFILE.CARDINALITY_WEAKENING` | Profile cardinality weakens Catalog bounds or contradicts its selected adjustment. | Existing C contract (`catalog_validation.py`). |
| 60 | `AGTXIV.PROFILE.PRODUCER_EXPANSION` | Profile producer roles are reordered or expand beyond the Catalog role set. | Existing C contract (`catalog_validation.py`). |
| 61 | `AGTXIV.PROFILE.TERMINAL_POLICY_MISMATCH` | Profile terminal-permission mode differs from the Catalog mode. | Existing C contract (`catalog_validation.py`). |
| 62 | `AGTXIV.PROFILE.OUTCOME_EXPANSION` | Profile terminal outcomes are reordered or expand beyond Catalog outcomes. | Existing C contract (`catalog_validation.py`). |
| 63 | `AGTXIV.PROFILE.CONTEXT_WEAKENING` | Profile stage or family terminal context is weaker than the effective Catalog minimum. | Existing C contract (`catalog_validation.py`). |
| 64 | `AGTXIV.CATALOG.CONTEXT_BINDING_MISMATCH` | A terminal context's exact Catalog/Profile refs differ from the sealed C constraints. | Existing C contract (`catalog_validation.py`). |
| 65 | `AGTXIV.CATALOG.UNKNOWN_FAMILY` | A terminal target family is absent from the exact Catalog constraints. | Existing C contract (`catalog_validation.py`). |
| 66 | `AGTXIV.CATALOG.UNKNOWN_STAGE` | A terminal target stage is absent for the resolved Catalog family. | Existing C contract (`catalog_validation.py`). |
| 67 | `AGTXIV.CATALOG.OBLIGATION_NOT_SELECTED` | A terminal record targets a Profile branch explicitly marked `NOT_SELECTED`. | Existing C contract (`catalog_validation.py`). |
| 68 | `AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED` | Effective Catalog/Profile policy forbids a terminal card for the target. | Existing C contract (`catalog_validation.py`). |
| 69 | `AGTXIV.CATALOG.PRODUCER_ROLE_NOT_ALLOWED` | Terminal producer role is outside the effective Profile role subset. | Existing C contract (`catalog_validation.py`). |
| 70 | `AGTXIV.CATALOG.CONTEXT_MODE_INSUFFICIENT` | Terminal context mode is weaker than the effective Profile minimum. | Existing C contract (`catalog_validation.py`). |
| 71 | `AGTXIV.CATALOG.OUTCOME_NOT_ALLOWED` | Terminal outcome is outside the effective Profile outcome subset. | Existing C contract (`catalog_validation.py`). |
| 72 | `AGTXIV.CODE.CATALOG_INVALID` | A correctly bound genesis stable-code document violates code identity, kind, order, exact version, stable meaning, or declared resource rules. | Frozen by D. |
| 73 | `AGTXIV.CODE.ENUM_PROJECTION_MISMATCH` | The catalog `VALIDATION_DIAGNOSTIC` projection and final compiled `DiagnosticCode` enum are not equal in membership, ordinal, and declaration order. | Frozen by D. |
| 74 | `AGTXIV.CODE.POLICY_REFERENCE_INVALID` | A policy exact reference, official schema pin, validator/vector binding, or sealed C-constraint root differs from the supplied fixed bytes. | Frozen by D. |
| 75 | `AGTXIV.CODE.POLICY_INVALID` | A correctly bound genesis policy violates its closed gate, registration, canonical order, exact target, or declared resource rules. | Frozen by D. |
| 76 | `AGTXIV.CODE.EMITTED_DIAGNOSTIC_UNREGISTERED` | An emitted diagnostic is absent from the trusted catalog's `VALIDATION_DIAGNOSTIC` projection. | Frozen by D. |
| 77 | `AGTXIV.REASON.UNREGISTERED` | An intrinsically and structurally valid terminal record declares a code that is absent, not an active `TERMINAL_REASON`, or not registered by the exact policy. | Frozen by D. |
| 78 | `AGTXIV.REASON.CONSTRAINT_MISMATCH` | A registered terminal reason is used outside its policy outcome, retry, context, or exact family-version-stage constraints. | Frozen by D. |

D adds exactly rows 72–78, appending only these seven enum members in that exact
order. It does not create a second diagnostic class or string-only shadow enum.
The catalog then adds one non-enum `TERMINAL_REASON` as its 79th total row, with
reason-kind ordinal 1 and the exact meaning frozen in Section 1. Final plan review
rechecked the other 77 meanings against their named checkpoint plans and current
emit conditions and found no other obvious semantic broadening or narrowing;
ordinal 24 is deliberately restored to Checkpoint A's exact literal rather than a
broader schema-validity paraphrase.

Bootstrap is explicit:

1. implementation appends the seven enum members;
2. the canonical asset copies all 78 table rows, ordinals, and meanings exactly;
3. mechanical tests compare the enum and catalog diagnostic projection in both
   directions and exact order, and compare every catalog meaning to this table;
4. catalog intrinsic validation may emit compiled enum diagnostics before the
   submitted catalog has been trusted;
5. only after catalog intrinsic validation and enum bijection succeed may the
   emitted-diagnostic registration gate run; and
6. all later D gates verify every emitted `Diagnostic.code` is a registered
   `VALIDATION_DIAGNOSTIC` in that valid catalog.

This ordering avoids circularly trusting an invalid catalog while still proving
that accepted validator output is cataloged. Diagnostic messages remain
non-normative; all 78 codes, ordinals, kinds, order, and stable meanings are
normative. An implementer may not invent, paraphrase, or derive a replacement
meaning from a current message.

## 7. Pure public APIs and sealed constraints

The implementation reuses C's existing `RawContractAssetBinding` rather than
creating a parallel root-binding type, and exports exactly these new public
seams:

```python
validate_stable_code_catalog_intrinsic(
    catalog_binding: RawContractAssetBinding,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]

build_kernel_validation_policy_constraints(
    code_catalog_binding: RawContractAssetBinding,
    policy_binding: RawContractAssetBinding,
    catalog_profile_constraints: CatalogProfileConstraints,
    support_assets: tuple[SuppliedAsset, ...],
    registry: ContractSchemaRegistry,
) -> KernelValidationPolicyConstraints | tuple[Diagnostic, ...]

validate_emitted_diagnostic_registration(
    diagnostics: tuple[Diagnostic, ...],
    constraints: KernelValidationPolicyConstraints,
) -> tuple[Diagnostic, ...]

validate_typed_terminal_result_kernel_constraints(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
    catalog_profile_constraints: CatalogProfileConstraints,
    constraints: KernelValidationPolicyConstraints,
) -> tuple[Diagnostic, ...]
```

`support_assets` contains exactly the final D validator source and vector index;
all schemas come from the explicit registry, and the C roots are represented by
the sealed C snapshot plus their exact refs. Extra support assets fail closed.
The two root bindings and two support assets are the complete D-controlled raw
input set and are admitted under Section 4 limits before byte observation.

`ContractSchemaRegistry` is already constructed and sealed before either D API is
called. Its current public API does not expose pre-construction resource admission,
so D cannot retroactively bound the memory, CPU, or bytes consumed to build it.
D inherits C audit's finite-memory and no-OS-availability assurance limitation.
D invokes the existing registry exact-type/seal integrity check and then locates
the two required official D schema IDs/pins. The inherited seal check **does
traverse, hash, thaw, and reparse every registry entry**; D provides no resource
bound for that inherited work and does not claim otherwise. After that inherited
check, D adds no second semantic-validation or indexing pass over unrelated
entries: its own schema work is limited to the two required D entries. This honest
boundary requires no `registry.py` change and keeps the implementation allowlist
at eleven paths.

`KernelValidationPolicyConstraints` has a private constructor, exact type check,
recursive frozen state, detached copies, and an accidental-tamper seal. Read-only
public projections are limited to:

```text
code_catalog_ref
policy_ref
requirements_ref
catalog_ref
profile_ref
terminal_schema_ref
validation_diagnostic_codes
terminal_reason_codes
gate_order
```

Private frozen maps hold reason registrations. The snapshot exposes no
`approved`, `released`, `complete`, `covered`, `satisfied`, `admitted`, or runtime
selection flag. Its seal is not a signature and does not defend against arbitrary
code in the same interpreter.

All APIs are pure over explicitly supplied finite in-memory values. They perform
no filesystem, network, DNS, URL, Git, clock, environment, process, subprocess,
database, plugin, random, dynamic import, or mutable process-global registry
access. `raw_bytes == canonical_bytes(parsed)` is mandatory. Success returns an
empty diagnostic tuple or one complete sealed snapshot; failure returns a
nonempty deterministically sorted tuple, never partial constraints. This purity
claim does not bound construction or whole-seal verification of the already built
`ContractSchemaRegistry`, does not promise termination for arbitrary ambient
memory pressure, and does not imply OS-enforced availability or isolation.

## 8. Gate order and fail-closed behavior

### 8.1 Catalog/policy builder gates

The builder stops at the first failing gate while aggregating independent safe
findings within that gate:

0. **Exact-type and D-resource preflight.** Inspect exact outer/member types and
   opaque integrity; require exactly two roots and exactly two role-typed supports;
   enforce every per-item and aggregate bound from Section 4 before copying,
   hashing, parsing, enum comparison, or vector expansion. For the already sealed
   registry, perform only its inherited exact-type/integrity check; do not claim
   retroactive registry-construction admission.
1. **Raw exact binding.** Snapshot only the admitted D roots/supports; require
   their asset-ID uniqueness; verify IDs, roles, media types, sizes, and SHA-256;
   reject same-ID/different-byte and role aliases.
2. **Canonical parse and official schema pin.** Require canonical JSON, exact
   five-field D schema refs, fixed format checker, direct-root closed-schema
   validation, and no remote resolution. Locate and compare only the two required
   official schema entries/pins after the inherited registry seal check; add no
   second semantic-validation or indexing pass over unrelated registry entries.
3. **Genesis catalog intrinsic.** Check exact `1.0.0`/`GENESIS`, root vocabulary,
   all resource literals, exactly 79 entries, code grammar/kinds/uniqueness/order,
   all 78 diagnostic ordinals and meanings from Section 6, and the one reason.
4. **Python diagnostic bijection.** Compare catalog diagnostic code strings to
   the final enum in both directions and in declaration order; ensure terminal
   reasons are absent from the enum.
5. **Policy exact graph.** Exact-bind D catalog, C requirement/Catalog/Profile
   refs, typed-terminal Checkpoint B schema, D validator and vectors; verify C
   snapshot type/seal and ref equality; reject reverse edges, aliases, extra
   support, and cycles.
6. **Genesis policy registration.** Check exact `1.0.0`/`GENESIS`, fixed gate list,
   resource literals, code kind, canonical array order, uniqueness, and exact
   resolution of the sole registration/target against selected
   terminal-permitted C constraints.
7. **Emitted-diagnostic registration.** Only now verify diagnostics produced by
   applicable completed gates against the trusted diagnostic projection.
8. **Seal.** Build one detached complete constraint snapshot.

Any unknown discriminator or vocabulary value fails; no default branch interprets
it as a known code, kind, outcome, retry, context, family, stage, or version.

### 8.2 Final terminal composition

The final public terminal API has exactly this hard-stop order:

1. call C `validate_typed_terminal_result_catalog_constraints` exactly once; that
   existing public entry internally calls typed-terminal Checkpoint B intrinsic
   validation exactly once, hard-stops on any typed-terminal Checkpoint B
   diagnostic, and otherwise applies C structural constraints;
2. return the C public entry's diagnostics byte-for-byte unchanged if nonempty;
3. only after the single C call succeeds, validate the D constraints seal and
   exact D-to-C root equality;
4. resolve the declared reason in the D code catalog and policy;
5. require `TERMINAL_REASON`, active status, exact family/version/stage target,
   effective context, outcome, and retry disposition; and
6. run emitted-diagnostic registration on any D diagnostic before returning it.

The D API must not call `validate_typed_terminal_result_intrinsic` directly,
because doing so and then calling C would execute typed-terminal Checkpoint B
twice. The real order is therefore
`C public gate [typed-terminal Checkpoint B intrinsic -> C structural] -> D reason
gate`, with typed-terminal Checkpoint B executed once. Typed-terminal Checkpoint B owns intrinsic schema,
attempt, evidence, outcome/retry/action, and resource partition rules. C owns
reason-unaware Catalog/Profile family, stage, selection, producer, context, and
outcome structure. D owns only cataloged reason identity and registration
constraints. A later gate cannot mask, translate, duplicate, or weaken an earlier
diagnostic.

## 9. Fixture design and exact hash construction

The non-normative fixture directory is:

```text
fixtures/v2-contract-kernel/code-policy/1.0.0/
```

It contains exactly:

```text
code-policy-conformance-vectors.json
linkage.non-normative.json
```

The vector index is canonical JSON with a closed root:

```text
vector_set_id = vectors:checkpoint-d-code-policy/1.0.0
vector_set_version = 1.0.0
fixture_purpose = CONTRACT_KERNEL_CODE_POLICY_TEST_ONLY
vectors
```

Each vector is a closed positive or negative branch with `vector_id`, `polarity`,
`vector_kind`, `template_id`, `expected_diagnostic_codes`, and, for negative
vectors, `mutation_id`. Kinds are `CODE_CATALOG`, `POLICY`,
`DIAGNOSTIC_REGISTRATION`, or `TERMINAL_COMPOSITION`. The test harness owns
mutation expansion; production validation parses only the closed ID/target/code
partition. Expected diagnostic codes must be sorted, unique, and members of the
final enum. The index is test metadata, not release evidence or a conformance
certificate.

The linkage manifest is canonical, closed, non-normative test metadata containing
exactly:

```text
fixture_purpose = CONTRACT_KERNEL_CODE_POLICY_LINKAGE_ONLY
normative_status = NON_NORMATIVE
runtime_authority = NONE
coverage_claim = NONE
requirements_ref
catalog_ref
profile_ref
code_catalog_ref
validation_policy_ref
```

It is built last and is not accepted by any public validator API. Scoped PASS
text must say: `Checkpoint D code/policy composition fixture: PASS; synthetic
reason registration only; no runtime, release, merge, coverage, or admission
authority.`

Bytes freeze in this dependency order:

```text
two official D schemas
  -> diagnostics.py final enum
  -> code_policy_validation.py final source
  -> StableCodeCatalog canonical bytes
  -> conformance-vector index
  -> KernelValidationPolicy canonical bytes
  -> linkage manifest
  -> tests
```

If diagnostics or validator source changes, all downstream refs are regenerated.
No hand-written placeholder digest is allowed. Tests recompute schema, source,
root, support, C refs, and typed-terminal Checkpoint B schema ref from committed raw bytes.

## 10. Adversarial test matrix

### 10.1 Schemas, canonical bytes, and resources

Test both official schemas for meta-validity, exact `$id`, closed roots and
branches, registry closure, fixed format checker, and exact five-field pins.
Reject duplicate JSON keys, noncanonical JSON, BOM, invalid UTF-8, unpaired
surrogates, over-nesting, wrong exact types/subclasses, forged opaque values,
same-URI substituted schemas, stale size/hash, path-hint lookup, remote refs, and
unknown fields. Test catalog root, policy root, validator support, vector support,
root aggregate, support aggregate, and all-input aggregate at limit and limit+1;
also test 79/80 entries, 4096/4097 emitted diagnostics, 2048/2049 canonical
exact-ref bytes, 512/513 vectors, 2048/2049 canonical vector-entry bytes, and
exactly two/three supports. Remove, add, and mutate each closed `resource_limits`
field and require compiled-map inequality failure. Insert `path_hint` into every
D exact-ref role and require schema failure even when the ref would otherwise be
below 2,048 bytes. Instrument bytes so no copy, hash, parse, enum comparison, or
vector expansion occurs while any D-controlled outer type, role, count, per-item
raw byte, or aggregate raw budget is invalid. Separately document that a prebuilt
registry is not retroactively resource-admitted: the inherited integrity check
still traverses, hashes, thaws, and reparses all entries, while D adds no second
semantic-validation/indexing pass and claims no bound on registry work or OS
availability.

### 10.2 Code kinds, ordering, and compatibility

Mechanically materialize Section 6 as an expected tuple and compare all 78 enum
rows for exact ordinal, code bytes, stable meaning bytes, and enum declaration
order, plus the separate reason row. Reject missing, extra, duplicate, reordered,
renamed, or paraphrased rows; terminal reason inserted into the enum; diagnostic
mislabeled as reason; reason mislabeled as diagnostic; unknown kind;
noncontiguous ordinal; wrong kind order; meaning mutation; introduced-version
mutation; invalid code grammar; empty/oversized meaning; and duplicate code
across kinds. The test expected tuple must come from a reviewed literal table,
not messages or an algorithm that could reproduce the same implementation bug.
The ordinal-24 expected literal is exactly `Strict parsing succeeded, but the
supplied schema is not one top-level JSON object.`. The same literal comparison is
performed for every other row.

Both schemas reject every predecessor, successor, inheritance, supersession,
deprecation, replacement, version-range, non-`1.0.0`, or non-`GENESIS` field.
There are no ancestry or policy-version-increment vectors because D exposes no
mechanical input for those semantics; future revision behavior remains deferred.

### 10.3 Policy and exact graph

Cover exact D catalog and C requirement/Catalog/Profile refs, path-hint-only
projection equality, terminal schema pin, validator source and every entry-point
string, vector role, support alias, extra support, direct/reverse cycle,
same-ID/different-byte input, and sealed C snapshot mutation/type failure. Reject
unknown or reordered gate names and every hidden/changed resource limit.

For registrations, cover empty/duplicate/reordered arrays; diagnostic used as a
reason; absent/unknown/inactive reason; unknown kind/outcome/retry/context/family/
version/stage; wildcard; NOT_SELECTED and terminal-forbidden targets; wrong C
family/stage order; a second target or registration; and registration of an
invented reason for the planning-contract option / proposed Checkpoint E. Confirm
the sole valid target and the exact C Profile outcome/context subset.

### 10.4 Diagnostic bootstrap and terminal composition

Prove catalog intrinsic diagnostics are available before catalog trust, but the
registration gate does not run on an invalid catalog. After a valid catalog,
reject an emitted unknown code and a terminal-reason code masquerading as a
`Diagnostic.code`. Prove every D-emittable diagnostic is in the final catalog.

Terminal tests prove:

- the D entry calls C's public entry exactly once and never directly calls the
  typed-terminal Checkpoint B intrinsic entry;
- a typed-terminal Checkpoint B failure inside that C call hard-stops C and D and
  is returned unchanged, once and without duplicate diagnostics;
- valid typed-terminal Checkpoint B input plus a C structural failure hard-stops D
  and is returned unchanged;
- C's existing entry accepts two syntactically valid reason strings equally,
  preserving its reason-unaware semantics;
- the D entry accepts the exact registered synthetic reason only for the exact C
  target, allowed outcome/retry pair, and `FROZEN_SCOPE_BOUND` context;
- unknown reason yields `AGTXIV.REASON.UNREGISTERED`;
- wrong kind, family version, target, outcome, retry, or context yields the
  deterministic D code specified above;
- typed-terminal Checkpoint B's stricter outcome/retry matrix cannot be broadened by D;
- messages and summaries may differ without changing the result; and
- no pass infers evidence relevance, satisfaction, review, release, or authority.

### 10.5 Purity, determinism, and repository regression

Sentinels forbid filesystem, network, DNS, URL, Git, time, environment,
subprocess, database, plugin, random, dynamic import, and mutable global-registry
access. Permute the exactly two supplied support assets and repeat hostile finite
inputs to prove byte-identical diagnostics and order independence where order is
not normative. Run focused tests, all contract unit tests, full pytest, diagnostics,
and fast repository validation. Report OS-isolation limitations honestly rather
than upgrading assurance claims.

## 11. Exact implementation allowlist

The implementation-only commit is restricted to exactly these eleven paths:

```text
schemas/v2/contract-kernel/contract/stable-code-catalog/1.0.0.schema.json
schemas/v2/contract-kernel/contract/kernel-validation-policy/1.0.0.schema.json
contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json
contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.0.0.json
fixtures/v2-contract-kernel/code-policy/1.0.0/code-policy-conformance-vectors.json
fixtures/v2-contract-kernel/code-policy/1.0.0/linkage.non-normative.json
src/agtxiv_v2/contracts/code_policy_validation.py
src/agtxiv_v2/contracts/diagnostics.py
src/agtxiv_v2/contracts/__init__.py
tests/unit/contracts/test_code_policy_schemas.py
tests/unit/contracts/test_code_policy_validation.py
```

The list above contains eleven paths; that count and path set are frozen. The
implementation stages exactly these names and compares the cached path set to
this list.

No implementation commit may modify the D plan, Checkpoint C or typed-terminal
Checkpoint B schemas or validators,
terminal/Catalog/Profile/common/requirement bytes, baseline, audit, aggregate
validator, demo, database, source/intake/CAS/bundle work, flat V2 WIP, or current
unrelated user changes.

## 12. Commit and independent-review sequence

D uses five separated review surfaces:

1. **Plan-only:** add only this roadmap; commit before implementation.
2. **Implementation-only:** change exactly the eleven-path allowlist; no baseline
   or audit.
3. **Baseline-only:** update only
   `baselines/repository-validation/pytest/test-identity-v1.json` from the exact
   implementation commit.
4. **Independent adversarial and reader review:** review exact implementation and
   baseline commits; close all Priority 0 and Priority 1 findings without mixing
   an audit into corrections. Any correction requires a new implementation-only
   commit and regenerated baseline-only commit.
5. **Audit-only:** add only
   `docs/audits/v2-m1-contract-kernel-checkpoint-d-2026-09-01.md`, recording exact
   commits, bytes, diagnostics projection, commands, review dispositions,
   assurance limits, deferred work, and next checkpoint.

No commit is authorized to stage pre-existing demo, database, slide, reference,
or other working-tree WIP.

## 13. Pytest identity and verification flow

From the exact implementation commit:

1. collect the committed test inventory using the repository's locked identity
   workflow, not dirty-tree source;
2. generate the candidate twice and require byte-identical normalized identities;
3. compare to the pre-D baseline and require additions only from
   `test_code_policy_schemas.py` and `test_code_policy_validation.py`;
4. record collected, selected, deselected, skipped, marker, normalized-byte,
   domain-separated, full-node-set, and selected-order identities;
5. commit only the reviewed baseline file;
6. run focused tests, `pytest -q tests/unit/contracts`, `pytest -q`, and
   `python tools/validate_repo.py --profile fast` in an exact Git checkout with
   locked dependencies; and
7. separately report dirty-working-tree observations without treating them as
   exact implementation evidence.

Any unrelated collection delta blocks the baseline commit. Existing known stale
Shellworld evidence remains named and is not rewritten.

## 14. Definition of Done

Checkpoint D is complete only when:

1. this plan is committed alone before implementation;
2. implementation changes exactly the eleven frozen paths and preserves every
   unrelated user file;
3. both D schemas are closed, meta-valid, registry-resolvable, and pinned by full
   exact raw refs;
4. both canonical roots are byte-canonical, exact-bound, within their explicit
   per-role and aggregate resource limits, and connected by the acyclic hash DAG;
5. the stable catalog mechanically matches all 78 Section 6 rows for ordinal,
   exact code, exact stable meaning, and enum declaration order in both directions,
   and contains exactly one separate terminal reason as its 79th row;
6. rows 72–78 are the only new enum codes, all messages remain explicitly
   non-normative, and no implementer-authored meaning enters the asset;
7. both schemas accept only immutable `1.0.0` genesis documents and reject every
   predecessor/successor/revision field; future catalog/policy revision semantics
   remain explicitly deferred;
8. the policy exact-binds D catalog, frozen typed-terminal Checkpoint B schema, and
   the exact C requirement/Catalog/Profile sealed constraints without a cycle;
9. only `AGTXIV.TERMINAL.EXAMPLE` is registered, only for the exact synthetic C
   target and effective constraints, with no reason for the planning-contract
   option / proposed Checkpoint E pre-registered;
10. bootstrap ordering permits intrinsic catalog diagnostics but runs emitted-code
    registration only after a valid catalog and enum bijection;
11. the final terminal entry point calls C's public entry once—executing
    typed-terminal Checkpoint B intrinsic then C structural validation once—and
    runs D only after success; typed-terminal Checkpoint B and C diagnostics
    hard-stop D unchanged and are not duplicated, while the existing C entry
    remains unchanged and reason-unaware;
12. sealed constraints are detached, immutable, complete-or-error, pure,
    deterministic, and expose no authority-like property;
13. the closed policy schema, compiled constants, canonical policy, and tests have
    the same complete resource map, including exact-ref 2,048, vector-count 512,
    vector-entry 2,048, policy-root 27,072, root-aggregate 428,976,
    support-aggregate 2,113,536, and all-D-input 2,542,512 limits; all applicable
    limit/limit+1 cases pass, `path_hint` is forbidden in D refs, and the audit
    states that inherited registry seal traversal/hash/thaw/reparse and OS
    availability are unbounded by D;
14. focused, contract, full, diagnostics, and fast repository checks pass from the
    exact reviewed commits, with assurance limitations reported faithfully;
15. test identity is generated twice byte-identically, contains changes only from
    the two allowlisted tests, and is committed baseline-only;
16. independent adversarial and reader review has zero open Priority 0 or Priority
    1 findings and confirms that code kinds, bootstrap, non-authority, and the
    synthetic-only reason are understandable; and
17. the audit preserves **M1: NOT COMPLETE** and **AgtXIv V2: NOT COMPLETE**, and
    grants no runtime, bundle, CAS, intake, merge, release, archive,
    certification, database, or knowledge-admission authority.

Completion authorizes only the next plan-only contract-kernel design review. It
does not authorize protected-branch merge or any production/release action.

## 15. Deferred work and next checkpoint

Deferred beyond D:

- every real planning, source, intake, formalization, assessment, release,
  knowledge, and query reason;
- every catalog/policy successor, inheritance, version-increment, deprecation,
  replacement, and supersession shape;
- a production Catalog/Profile and `ContractBundleRelease`;
- signatures, trust roots, policy selection, runtime execution, CAS, bundle,
  database, demo, archive, and admission;
- terminal satisfaction, evidence relevance, actual cardinality, and resource
  authenticity; and
- coverage numerators and any M1 completion claim.

The two external, non-repository principle reviews' combined choice is recorded
only as an input summary: A0 proceeds first because stable code identity and
reason registration are the smallest necessary prerequisite for the
planning-contract option, not because complete policy engineering should become
a parallel product line. Their raw reviews are not claimed as committed evidence;
this plan is the repository's normative decision. Once D has implementation,
baseline, independent review, and audit evidence, the next checkpoint defaults to
a **plan-only principle review for the planning-contract option / proposed
Checkpoint E** covering Plan -> Discovery -> ScopeFreeze. Proposed Checkpoint E is
not typed-terminal Checkpoint B, must first plan any actually used reason under a
new schema/version, and must not modify typed-terminal Checkpoint B or D `1.0.0`
bytes. D must not implement proposed Checkpoint E in advance.
