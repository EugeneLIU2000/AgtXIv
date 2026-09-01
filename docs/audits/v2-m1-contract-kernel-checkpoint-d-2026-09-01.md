# AgtXIv V2 M1 contract-kernel Checkpoint D implementation audit

- Audit status: INDEPENDENT ADVERSARIAL AND READER REVIEW PASSED; CHECKPOINT D COMPLETE WITHIN PLAN-DEFINED SCOPE
- Checkpoint D scoped implementation result: COMPLETE WITH EXPLICIT LIMITS
- M1 status: **NOT COMPLETE**
- AgtXIv V2 status: **NOT COMPLETE**
- Audit date: 2026-09-01
- Plan commit: `aec0e12ca2ae3dd2764259706941e72c72f39b24`
- Implementation commit: `194e8d8703acda0a5fa3b2f187c3236d65e90ffc`
- Baseline-only commit: `b0b283e501e5acdb6bb46fc610e793b4650ed2c2`
- Predecessor audit commit: `81824846591d00f014e8f88ddefbda034ea3db01`
- Runtime, release, protected-branch merge, bundle, CAS, intake, archive,
  certification, database admission, knowledge admission, and M1/V2 completion
  authority: none

## 1. Executive finding and reader-facing boundary

Checkpoint D implements the narrow stable-code prerequisite selected by its plan:
one immutable genesis stable-code catalog, one genesis kernel-validation-policy
candidate, and one final composition gate that checks terminal-reason registration
after the existing Checkpoint C public structural gate succeeds. The exact
implementation and baseline commits pass the focused, contract-unit, full, and
fast repository checks recorded below. Final independent review reports
`P0=0` and `P1=0`.

The names of these documents must not be over-read. The stable-code catalog is a
**genesis candidate dictionary** for machine-code identity and stable meaning.
The kernel policy is a **candidate, non-authoritative wiring document**. The
linkage manifest and conformance-vector index are **non-normative test metadata**.
None is a selected runtime policy, production Catalog/Profile, release, merge
approval, bundle, CAS object, intake decision, database credential, admission
transaction, or evidence of obligation satisfaction. No public D projection
contains an approval, release, coverage, satisfaction, admission, or runtime-
selection flag.

Checkpoint C remains structurally **reason-unaware**. Its unchanged public entry
validates typed-terminal Checkpoint B intrinsic rules and C Catalog/Profile
family, stage, selection, producer, context, and outcome structure, but accepts
two otherwise valid reason strings equally. D does not reinterpret C as complete
reason validation. D registers only the synthetic literal
`AGTXIV.TERMINAL.EXAMPLE`, and only against the synthetic C fixture target. It
does not register a real planning, discovery, scope-freeze, intake, scientific,
formalization, review, or release reason.

The planning-contract option called proposed Checkpoint E is not implemented.
`AgentizationPlan`, `InventoryDiscoveryResult`, `ScopeFreezeDecision`, and
`FrozenInventoryScope` remain absent from D. The arbitrary-arXiv runtime, Paper
Agent DAG production, all-file V2 demo, reviewed standard database, and
verifiable mathematical formalization chain remain future work.

## 2. Exact history and eleven-path implementation boundary

The mechanically inspected history is linear:

| Commit | Exact parent | Role |
|---|---|---|
| `aec0e12ca2ae3dd2764259706941e72c72f39b24` | `81824846591d00f014e8f88ddefbda034ea3db01` | Checkpoint D plan only |
| `194e8d8703acda0a5fa3b2f187c3236d65e90ffc` | `aec0e12ca2ae3dd2764259706941e72c72f39b24` | Checkpoint D implementation only |
| `b0b283e501e5acdb6bb46fc610e793b4650ed2c2` | `194e8d8703acda0a5fa3b2f187c3236d65e90ffc` | pytest identity baseline only |

Git ancestry checks confirm that the plan is an ancestor of the implementation
and the implementation is an ancestor of the baseline commit. The implementation
commit changes exactly the frozen eleven paths and no others:

| Path | Change |
|---|---|
| `schemas/v2/contract-kernel/contract/stable-code-catalog/1.0.0.schema.json` | add |
| `schemas/v2/contract-kernel/contract/kernel-validation-policy/1.0.0.schema.json` | add |
| `contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json` | add |
| `contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.0.0.json` | add |
| `fixtures/v2-contract-kernel/code-policy/1.0.0/code-policy-conformance-vectors.json` | add |
| `fixtures/v2-contract-kernel/code-policy/1.0.0/linkage.non-normative.json` | add |
| `src/agtxiv_v2/contracts/code_policy_validation.py` | add |
| `src/agtxiv_v2/contracts/diagnostics.py` | modify |
| `src/agtxiv_v2/contracts/__init__.py` | modify |
| `tests/unit/contracts/test_code_policy_schemas.py` | add |
| `tests/unit/contracts/test_code_policy_validation.py` | add |

The baseline-only commit changes exactly
`baselines/repository-validation/pytest/test-identity-v1.json`. Neither commit
changes the D plan, Checkpoint B or C contracts, aggregate validator, demo,
database, intake, bundle, CAS, or unrelated working-tree work. In particular,
current untracked `tests/test_demo_intake.py` is not in either exact commit and
was not modified or included in D's committed identity.

## 3. Mechanically recomputed exact blob identities

The following sizes and SHA-256 digests were recomputed from raw Git blobs at
`194e8d8703acda0a5fa3b2f187c3236d65e90ffc`; they were not copied from path
contents in the dirty working tree.

| Exact implementation blob | Raw bytes | Raw SHA-256 |
|---|---:|---|
| StableCodeCatalog schema | 4,899 | `sha256:ced539ac5326b14a0e00acfcff35442960347563ed10d9dcb185947b5e085d70` |
| KernelValidationPolicy schema | 10,329 | `sha256:ab7963b01ac0a4a00b7c9e2851199dc7b38bddeddb96f629b6f20d41d09647aa` |
| StableCodeCatalog genesis asset | 21,173 | `sha256:57d1e8a421cbb713a798a2e2d1d9abca2df122a43098271f678c5cfa4749e9d2` |
| KernelValidationPolicy genesis candidate | 3,912 | `sha256:ef59cf42984764731bd8a2836bb4305251cfb77a088f337584784ff4c23922e8` |
| Code-policy conformance-vector index | 2,776 | `sha256:f3879958da67bc6d4c63e45e12335d274f7574273838d13bf0fdd380a8b3e366` |
| Non-normative linkage manifest | 1,204 | `sha256:21edfe05e0ee952a38f602b3e007ab6054dde2d9e40b1cf953714af0de1ea53a` |
| D code-policy validator source | 44,586 | `sha256:bb29c1d269f32945e558e861511e51f491896fdeaba02548a289fe94a4610ad9` |
| Final diagnostics source | 11,811 | `sha256:18c9479731460ce616a80ff9ce0ee9ce344c4fe3a613d8b28330a6d3f46aa24a` |
| Contract package exports | 2,616 | `sha256:4694827d2c94933419ad5283b7edbcda515dbda8973f91b56d1e5f9f98483076` |
| Focused schema tests | 5,981 | `sha256:4b7561cd48f0b9516da5fafa788dc639d529e169b170afebbf56f7afef0842e5` |
| Focused validator tests | 40,864 | `sha256:8328cc773c9a505a86a383d9e5b969f6add0da129c20f42700d72a25dee76efc` |

The exact inherited Checkpoint B/C roots referenced by D recompute as:

| Inherited blob | Raw bytes | Raw SHA-256 |
|---|---:|---|
| C normative M1 requirement set | 12,775 | `sha256:b8c14e570f94934b56b0a0447c856d9d37eb2db9ede6aa6c191280ff618058f9` |
| C synthetic Catalog | 3,889 | `sha256:86958f085abf04e382c262d3e8aa9181039a565947b7dfd8e2153d39c4903be0` |
| C synthetic Profile | 1,770 | `sha256:e794945c8ca6c2c85d5da899f1e9773134c1b33e9a541b7550007f3167c2f8c9` |
| Frozen typed-terminal Checkpoint B schema | 16,054 | `sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6` |

These C values agree with the predecessor audit's exact refs. D does not modify
those bytes.

## 4. Exact references and acyclic byte/hash DAG

The stable catalog's official schema ref is exactly:

```text
asset_id   schema:stable-code-catalog:1.0.0
media_type application/schema+json
byte_size  4899
sha256     sha256:ced539ac5326b14a0e00acfcff35442960347563ed10d9dcb185947b5e085d70
schema_uri https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.0.0
```

The policy's direct exact refs are:

| Role | Asset ID | Bytes | SHA-256 |
|---|---|---:|---|
| policy schema | `schema:kernel-validation-policy:1.0.0` | 10,329 | `sha256:ab7963b01ac0a4a00b7c9e2851199dc7b38bddeddb96f629b6f20d41d09647aa` |
| stable-code catalog | `code-catalog:agtxiv-contract-kernel/1.0.0` | 21,173 | `sha256:57d1e8a421cbb713a798a2e2d1d9abca2df122a43098271f678c5cfa4749e9d2` |
| C requirements | `requirements:m1-contract-requirement-set:1.0.0` | 12,775 | `sha256:b8c14e570f94934b56b0a0447c856d9d37eb2db9ede6aa6c191280ff618058f9` |
| C Catalog | `fixture-catalog:checkpoint-c-linkage/1.0.0` | 3,889 | `sha256:86958f085abf04e382c262d3e8aa9181039a565947b7dfd8e2153d39c4903be0` |
| C Profile | `fixture-profile:checkpoint-c-linkage/1.0.0` | 1,770 | `sha256:e794945c8ca6c2c85d5da899f1e9773134c1b33e9a541b7550007f3167c2f8c9` |
| terminal schema | `schema:typed-terminal-result:1.0.0` | 16,054 | `sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6` |
| D validator | `validator:checkpoint-d-code-policy:1.0.0` | 44,586 | `sha256:bb29c1d269f32945e558e861511e51f491896fdeaba02548a289fe94a4610ad9` |
| vectors | `vectors:checkpoint-d-code-policy/1.0.0` | 2,776 | `sha256:f3879958da67bc6d4c63e45e12335d274f7574273838d13bf0fdd380a8b3e366` |

Every D root exact ref is closed and has no `path_hint`. A path, URI, branch,
`latest`, environment, or process-global registry is not an authoritative
resolver. The URI on a schema ref is identity metadata, not a fetch instruction.

The recomputed construction/freeze dependency DAG is one-way:

```text
D schema bytes ----------------------> D genesis roots
final diagnostics + D validator -----> stable catalog / policy
C requirements + Catalog + Profile --> policy
Checkpoint B terminal schema --------> policy
stable catalog ----------------------> vector index -----------------> policy
policy + stable catalog + C roots -----------------> linkage manifest
```

This is a construction and byte-freeze ordering diagram; not every arrow denotes
a reference serialized in the child document. In particular, final diagnostics
source informs the catalog projection, and the catalog precedes the vector index,
but those construction dependencies are not invented as serialized exact refs.

The actual serialized direct exact-ref graph is:

- stable catalog -> its one official stable-catalog schema ref;
- policy -> exactly eight refs: its official policy schema, stable catalog, C
  requirements, C Catalog, C Profile, typed-terminal Checkpoint B schema, D
  validator source, and vector index; and
- linkage manifest -> exactly five refs: C requirements, C Catalog, C Profile,
  stable catalog, and policy.

The vector index contains no serialized catalog ref and follows the catalog only
in the freeze order. The linkage manifest is built last; no catalog or policy
root references it. The catalog does not reference the policy, and no document
contains its own or a future document's hash. The 11-vector index contains 4
positive and 7 negative rows partitioned as 3 catalog, 3 policy, 3 diagnostic-
registration, and 2 terminal-composition vectors. It is test metadata, not a
certificate.

The linkage manifest fixes `normative_status = NON_NORMATIVE`,
`runtime_authority = NONE`, `coverage_claim = NONE`, and
`fixture_purpose = CONTRACT_KERNEL_CODE_POLICY_LINKAGE_ONLY`. It is not accepted
by a public validator API.

## 5. Catalog projection: 78 diagnostics plus one reason

Mechanical parsing finds exactly 79 rows: 78 `VALIDATION_DIAGNOSTIC` rows in
final Python enum declaration order and one separate `TERMINAL_REASON`. The
reason has its own kind ordinal 1 and is not a `DiagnosticCode`. Rows 72--78 are
the only enum additions relative to C. Messages and terminal summaries remain
non-normative and are not cataloged; the table below records the stable meanings
from the exact catalog bytes.

| Kind ordinal | Kind | Exact code | Stable meaning |
|---:|---|---|---|
| 1 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.BOM_FORBIDDEN` | Input begins with a forbidden UTF-8 byte-order mark. |
| 2 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.INVALID_UTF8` | Input bytes are not valid strict UTF-8. |
| 3 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.INVALID_JSON` | UTF-8 input is not one complete syntactically valid JSON value. |
| 4 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.DUPLICATE_KEY` | A JSON object contains the same member name more than once before normalization. |
| 5 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.NORMALIZED_KEY_COLLISION` | Distinct object member names collide after required Unicode normalization. |
| 6 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.UNPAIRED_SURROGATE` | A string contains an unpaired Unicode surrogate code point. |
| 7 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.UNSUPPORTED_NUMBER` | A JSON number uses a numeric form outside the canonical profile. |
| 8 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.INTEGER_OUT_OF_RANGE` | An integer lies outside the permitted I-JSON exact-integer range. |
| 9 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.NESTING_TOO_DEEP` | A submitted value exceeds the canonical maximum nesting depth. |
| 10 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.UNSUPPORTED_PROGRAMMATIC_TYPE` | A programmatic input contains a value whose exact Python type is outside the canonical JSON model. |
| 11 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.NON_STRING_OBJECT_KEY` | A programmatic object has a member key whose exact type is not string. |
| 12 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.CYCLIC_PROGRAMMATIC_VALUE` | A programmatic array or object contains an identity cycle. |
| 13 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.INVALID_RECORD_SHAPE` | A value submitted for record hashing lacks the exact required record projection shape. |
| 14 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CANON.INVALID_INTERNAL_VALUE` | An opaque canonical value fails its internal integrity invariant. |
| 15 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REF.UNRESOLVED` | An exact asset, record, or component reference has no uniquely supplied target. |
| 16 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REF.HASH_MISMATCH` | Supplied target bytes, byte size, or canonical content hash differ from the exact reference. |
| 17 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REF.TYPE_MISMATCH` | A resolved target has the wrong declared media, schema, record, or component type for the reference. |
| 18 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CONTRACT.MUTABLE_REF` | A contract-bound authoritative reference contains mutable or non-exact identity. |
| 19 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.RECORD.INVALID_ENVELOPE` | An immutable record envelope is absent, open, malformed, or inconsistent with its required closed shape. |
| 20 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.RECORD.SUPERSESSION_MISMATCH` | A record revision or supersession relation is inconsistent with immutable revision rules. |
| 21 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.RECORD.HASH_MISMATCH` | A record's declared content hash differs from its canonical record-hash projection. |
| 22 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.EMPTY_REGISTRY` | Schema-registry construction received no schema bindings. |
| 23 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH` | A schema or validator API received an input with an invalid exact type or failed opaque/sealed integrity. |
| 24 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.INVALID_DOCUMENT` | Strict parsing succeeded, but the supplied schema is not one top-level JSON object. |
| 25 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.DIALECT_MISMATCH` | A schema does not declare the required JSON Schema Draft 2020-12 dialect. |
| 26 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.ID_MISMATCH` | A schema's `$id`, schema URI, or exact binding identities disagree. |
| 27 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.DUPLICATE_ID` | More than one supplied schema claims the same authoritative schema identity. |
| 28 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.META_INVALID` | A schema fails the supported dialect's meta-schema or closed-keyword constraints. |
| 29 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.UNRESOLVED_REF` | A schema `$ref` does not resolve inside the explicit offline registry. |
| 30 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.REFERENCE_CYCLE` | The admitted schema-reference graph contains a forbidden cycle. |
| 31 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN` | A schema reference would require remote or non-registry resolution. |
| 32 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH` | A record's declared record type differs from the exact family schema's record-type declaration. |
| 33 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.RECORD.PAYLOAD_INVALID` | A record payload violates its exact family schema. |
| 34 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.SCHEMA_MISMATCH` | A typed terminal record does not bind the compiled official terminal schema bytes. |
| 35 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.ATTEMPT_MISMATCH` | Terminal payload attempt identity or producer context is absent or differs from the envelope attempt. |
| 36 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.CONTEXT_INVALID` | A terminal binding context and its target basis have an intrinsically inconsistent shape or identity. |
| 37 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.TARGET_INVALID` | A terminal target is intrinsically recursive or otherwise forbidden as a terminal obligation target. |
| 38 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.EVIDENCE_INVALID` | Terminal evidence has duplicate IDs/references, noncanonical order, or a forbidden terminal/self reference. |
| 39 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.DISPOSITION_INVALID` | Terminal outcome, retry disposition, or next action violates the intrinsic compatibility matrix. |
| 40 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.TERMINAL.RESOURCE_INVALID` | Declared resource dimensions, ordering, partition, or observed-limit relation is mechanically inconsistent. |
| 41 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CONTRACT.ASSET_SCHEMA_MISMATCH` | A raw contract document's official schema ref or registry schema bytes differ from the compiled ruler. |
| 42 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CONTRACT.ASSET_INVALID` | A correctly bound raw contract document is noncanonical or violates its exact official schema. |
| 43 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REQUIREMENTS.SOURCE_BINDING_MISMATCH` | Requirement-set roadmap bytes, Git blob identity, bounded section, or exact source ref differs from the frozen source. |
| 44 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REQUIREMENTS.ITEM_SET_MISMATCH` | Requirement item membership or uniqueness differs from the compiled 52-item floor. |
| 45 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REQUIREMENTS.ITEM_ORDER_MISMATCH` | Requirement item order, kind, or source occurrence differs from the compiled floor. |
| 46 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REQUIREMENTS.MAPPING_MISMATCH` | Selected roadmap rows or their reviewed requirement expansion differs from the frozen mapping. |
| 47 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REQUIREMENTS.SELECTION_RULE_MISMATCH` | Requirement milestone selection differs from the exact M1-token rule. |
| 48 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.REFERENCE_INVALID` | A Catalog/Profile root or support reference is unresolved, aliased, excessive, or invalid for its declared graph role. |
| 49 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.EXACT_REF_CYCLE` | The recognized Catalog/Profile exact-reference graph contains a root alias or cycle. |
| 50 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.DUPLICATE_FAMILY` | Catalog family identity is duplicated under the v1 global-family rule. |
| 51 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.DUPLICATE_STAGE` | Catalog stage identity is duplicated. |
| 52 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.STRUCTURE_INVALID` | Catalog ordering, uniqueness, applicability, cardinality, vector, or stage-coverage structure is invalid. |
| 53 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.FAMILY_BINDING_INVALID` | A family successful-artifact kind, schema, or record-type binding is inconsistent. |
| 54 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.SUPPORT_ASSET_ROLE_INVALID` | Catalog validator or vector bytes do not resolve in the exact declared support role or target partition. |
| 55 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.TERMINAL_POLICY_INVALID` | Catalog terminal recursion, outcome order, context minimum, or accounting-unit terminal policy is invalid. |
| 56 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.CATALOG_MISMATCH` | A Profile does not exact-bind the supplied Catalog bytes. |
| 57 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.FAMILY_SET_INVALID` | Profile stage or family-stage keys do not exactly mirror Catalog membership and order. |
| 58 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.REQUIREMENT_WEAKENING` | A Profile weakens or deselects a Catalog core requirement. |
| 59 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.CARDINALITY_WEAKENING` | Profile cardinality weakens Catalog bounds or contradicts its selected adjustment. |
| 60 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.PRODUCER_EXPANSION` | Profile producer roles are reordered or expand beyond the Catalog role set. |
| 61 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.TERMINAL_POLICY_MISMATCH` | Profile terminal-permission mode differs from the Catalog mode. |
| 62 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.OUTCOME_EXPANSION` | Profile terminal outcomes are reordered or expand beyond Catalog outcomes. |
| 63 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.PROFILE.CONTEXT_WEAKENING` | Profile stage or family terminal context is weaker than the effective Catalog minimum. |
| 64 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.CONTEXT_BINDING_MISMATCH` | A terminal context's exact Catalog/Profile refs differ from the sealed C constraints. |
| 65 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.UNKNOWN_FAMILY` | A terminal target family is absent from the exact Catalog constraints. |
| 66 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.UNKNOWN_STAGE` | A terminal target stage is absent for the resolved Catalog family. |
| 67 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.OBLIGATION_NOT_SELECTED` | A terminal record targets a Profile branch explicitly marked `NOT_SELECTED`. |
| 68 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED` | Effective Catalog/Profile policy forbids a terminal card for the target. |
| 69 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.PRODUCER_ROLE_NOT_ALLOWED` | Terminal producer role is outside the effective Profile role subset. |
| 70 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.CONTEXT_MODE_INSUFFICIENT` | Terminal context mode is weaker than the effective Profile minimum. |
| 71 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CATALOG.OUTCOME_NOT_ALLOWED` | Terminal outcome is outside the effective Profile outcome subset. |
| 72 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CODE.CATALOG_INVALID` | A correctly bound genesis stable-code document violates code identity, kind, order, exact version, stable meaning, or declared resource rules. |
| 73 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CODE.ENUM_PROJECTION_MISMATCH` | The catalog `VALIDATION_DIAGNOSTIC` projection and final compiled `DiagnosticCode` enum are not equal in membership, ordinal, and declaration order. |
| 74 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CODE.POLICY_REFERENCE_INVALID` | A policy exact reference, official schema pin, validator/vector binding, or sealed C-constraint root differs from the supplied fixed bytes. |
| 75 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CODE.POLICY_INVALID` | A correctly bound genesis policy violates its closed gate, registration, canonical order, exact target, or declared resource rules. |
| 76 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.CODE.EMITTED_DIAGNOSTIC_UNREGISTERED` | An emitted diagnostic is absent from the trusted catalog's `VALIDATION_DIAGNOSTIC` projection. |
| 77 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REASON.UNREGISTERED` | An intrinsically and structurally valid terminal record declares a code that is absent, not an active `TERMINAL_REASON`, or not registered by the exact policy. |
| 78 | `VALIDATION_DIAGNOSTIC` | `AGTXIV.REASON.CONSTRAINT_MISMATCH` | A registered terminal reason is used outside its policy outcome, retry, context, or exact family-version-stage constraints. |
| 1 | `TERMINAL_REASON` | `AGTXIV.TERMINAL.EXAMPLE` | a synthetic terminal reason used only to demonstrate contract-kernel registration and composition; it makes no domain, production, satisfaction, review, or release claim. |

The catalog freezes `NEVER_REUSE_EXISTING_CODE`,
`NEVER_CHANGE_EXISTING_KIND`, `NEVER_CHANGE_MEANING_CREATE_NEW_CODE`,
`VALIDATION_DIAGNOSTIC_THEN_TERMINAL_REASON`,
`NON_NORMATIVE_NOT_CATALOGED`, and
`VALIDATION_DIAGNOSTIC_BIJECTION_IN_ENUM_ORDER`. It is exactly version `1.0.0`,
`revision_kind = GENESIS`; its schema exposes no predecessor, successor,
supersession, inheritance, replacement, or version-range field.

## 6. Policy registration, gate order, and C linkage

The sole registration is:

```text
reason_code        AGTXIV.TERMINAL.EXAMPLE
registration_kind  SYNTHETIC_COMPOSITION_ONLY
family_id          CHECKPOINT_C_SYNTHETIC_RECORD
family_version     1.0.0
stage_id            SYNTHETIC_ANALYSIS
outcomes            RETRY_REQUIRED, REVIEW_REQUIRED, BLOCKED, FAILED
retry dispositions RETRY_AFTER_CONDITION, NO_RETRY_IN_CURRENT_CONTEXT,
                   REVIEW_DECIDES
context             FROZEN_SCOPE_BOUND
```

No reason for proposed Checkpoint E is pre-registered. The policy gate order is
exactly:

```text
CODE_CATALOG_INTRINSIC
PYTHON_DIAGNOSTIC_BIJECTION
POLICY_INTRINSIC_AND_EXACT_BINDING
EMITTED_DIAGNOSTIC_REGISTRATION
TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC
TERMINAL_D_REASON_POLICY
```

The final terminal seam calls C's unchanged public
`validate_typed_terminal_result_catalog_constraints` exactly once. That call
runs typed-terminal Checkpoint B intrinsic validation once and then C structural
validation. Any B or C diagnostic hard-stops D and is returned unchanged. Only
after C succeeds does D check its constraint seal, C-root equality, code kind,
active registration, target, context, outcome, and retry disposition. D does not
call the B intrinsic entry directly and cannot use its retry ceiling to legalize
a pair forbidden by B's stricter matrix.

The sealed D snapshot is detached and recursively frozen, is complete-or-error,
and exposes only exact refs, cataloged code projections, and gate order. Its seal
protects against accidental mutation, not arbitrary malicious code executing in
the same interpreter; it is not a signature or authorization credential.

## 7. Resource literals, formulas, and assurance limits

The catalog repeats this complete compiled map:

```text
exact_code_entries                79
maximum_code_utf8_bytes          256
maximum_meaning_utf8_bytes      4096
maximum_code_entry_bytes        4880
maximum_root_metadata_bytes    16384
maximum_catalog_root_bytes     401904
```

The per-entry bound is $256 + 4{,}096 + 16 + 512 = 4{,}880$ bytes. The catalog
root bound is $79 \times 4{,}880 + 16{,}384 = 401{,}904$ bytes.

The policy repeats this complete compiled map:

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

The closed policy-root derivation is
$8 \times 2{,}048 + 4 \times 512 + 10 \times 128 + 3{,}264 + 4{,}096 =
27{,}072$. The vector bound is $512 \times 2{,}048 + 16{,}384 = 1{,}064{,}960$.
Thus root aggregate is $401{,}904 + 27{,}072 = 428{,}976$, support aggregate is
$1{,}048{,}576 + 1{,}064{,}960 = 2{,}113{,}536$, and all D-controlled input is
$428{,}976 + 2{,}113{,}536 = 2{,}542{,}512$ bytes. Focused probes accept each
applicable exact limit and reject limit plus one, including 512/513 vectors,
2,048/2,049-byte vector entries and exact refs, 4,096/4,097 emitted diagnostics,
raw role budgets, and root/support/all-input aggregates.

The limits above apply to D's two roots and two support assets; they do not
retroactively resource-admit construction of the already built
`ContractSchemaRegistry`. D invokes the inherited exact-type and seal-integrity
check. That inherited check **traverses, hashes, thaws, and reparses every
registry entry**, and D supplies no byte, memory, CPU, or traversal bound for
that work. After the inherited traversal, D adds no second semantic-validation
or indexing pass over unrelated entries and locates only the two required D
schema pins.

The APIs are pure over explicitly supplied finite in-memory values in the tested
in-process boundary: sentinels cover filesystem, network, DNS, URL, Git, clock,
environment, process, subprocess, database, plugin, random, dynamic import, and
mutable global-registry access. This does not establish termination under
arbitrary ambient memory pressure, OS-enforced availability, filesystem or
network isolation, resistance to OS resource exhaustion, or protection against
arbitrary same-interpreter code. The recorded commands used exact Git snapshots
but did not use an OS sandbox.

## 8. Exact pytest identity and environment qualification

The baseline-only blob contains 1,312 collected and selected nodes, zero
deselected nodes, zero collection skips, and 20 marker declarations. Mechanical
comparison against the pre-D 1,210-node baseline finds exactly 102 additions,
zero removals, and unchanged order for all 1,210 inherited nodes:

| Only allowed new test file | Added nodes |
|---|---:|
| `tests/unit/contracts/test_code_policy_schemas.py` | 26 |
| `tests/unit/contracts/test_code_policy_validation.py` | 76 |

The committed identity excludes current demo-intake WIP. Candidate generation
was rerun twice from the exact implementation commit
`194e8d8703acda0a5fa3b2f187c3236d65e90ffc`. Both candidate evaluations
returned `PASS`; their normalized `test_identity` objects and canonical JSON
bytes were byte-identical. Both canonical byte sequences were 395,384 bytes,
with SHA-256
`37f4373ecf4283c8eee7424a362273f85ea8ef16c4e6d2726986c9b982d85b6f`;
both domain-separated identity digests were
`4fe8e1df1db2c4295a4f354c4220478fe4a07a81722dc99d11e62ccbc4f75283`.
Exact recomputation of the baseline-only blob and normalized identity gives:

| Evidence | Recomputed value |
|---|---|
| Baseline file raw bytes | 395,385 |
| Baseline file raw SHA-256 | `8e2b93292bb10a36b0366289b26cac8ecf2f4a8fa50ce00d37e03ca9ba9dd42f` |
| Normalized canonical identity bytes | 395,384 |
| Normalized canonical identity SHA-256 | `37f4373ecf4283c8eee7424a362273f85ea8ef16c4e6d2726986c9b982d85b6f` |
| Domain-separated identity SHA-256 | `4fe8e1df1db2c4295a4f354c4220478fe4a07a81722dc99d11e62ccbc4f75283` |
| Full node-set SHA-256 | `b0a5ffa86615742da479b26cdde2bedc0cb9fe44e1f969f20e02b395ab6f1f62` |
| Selected-order SHA-256 | `ec9d8d1858769e90bf02892eead8b8920d0033e037d3d789d2f50387916fc06b` |

A fresh baseline-bound identity run at `b0b283e` returned `PASS` and the same
domain-separated digest. It reported `LOCKED_RUNTIME_MATCHED` with qualification
scope
`VERSION_LOCK_AND_INSTALLED_DISTRIBUTION_MATCH_NOT_OS_OR_NETWORK_ISOLATION`:
CPython 3.12.2 on Darwin arm64, pytest 7.4.4, pluggy 1.6.0, and uv 0.10.0, with
all installed distributions checked against the lock. The source assurance tier
was `COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC`; branch-evidence eligibility was
false; filesystem and network isolation were both false. Lock qualification is
environment qualification, not review, merge, release, admission, or branch
evidence.

## 9. Independent adversarial and reader review record

Only review-session-reported findings, their externally visible dispositions,
and public probes are recorded. Intermediate review text and private reviewer
reasoning are not repository blobs and are not claimed as independently
reconstructible from Git.

| Review pass | Review-session-reported finding disposition |
|---|---|
| Pre-freeze adversarial pass | Findings concerning complete preflight hard stops, C-seal-before-D-input ordering, complete asset-ID alias classes, and fail-closed registration of policy diagnostics were reported. Disposition: closed in the final implementation and covered by named focused probes. |
| Follow-up adversarial pass | Findings concerning exact per-role/aggregate limit reachability, inherited registry traversal wording, and reader-facing non-authority/synthetic-only interpretation were reported. Disposition: limit probes pass; traversal and OS-isolation limits are retained explicitly in this audit; authority wording was corrected rather than promoted. |
| Final adversarial pass | Review-session-reported final result: `P0=0`, `P1=0`; no blocking finding remains. |
| Final reader pass | Review-session-reported final result: `P0=0`, `P1=0`; catalog/policy/linkage are understandable as genesis candidate/non-normative artifacts, C is reason-unaware, and only the synthetic reason is registered. |

The key public probes include:

- exact ordered enum/catalog bijection and all 78 stable meanings;
- same-identity substituted bytes and `path_hint` rejection for every D ref role;
- exactly two support roles, alias rejection, support permutation stability, and
  complete namespace collision classes;
- preflight hard-stop instrumentation before root materialization, hashing,
  parsing, enum work, or vector expansion;
- C constraint type/seal failure before D inputs, registry, or namespace work;
- exactly one inherited sealed-registry traversal per public D API;
- 512/513 vectors, 2,048/2,049-byte vector entries and exact refs, exact raw-role
  limits, and aggregate sums;
- unknown emitted diagnostic and terminal-reason-as-diagnostic rejection;
- C public terminal entry called once, B not directly called, C failure returned
  unchanged, registered reason accepted, and unknown reason rejected; and
- deterministic output, ambient-I/O sentinels, exact non-normative linkage, and
  no authority-like projection.

The intermediate pass descriptions above are explicitly
**review-session-reported**; only the final committed bytes and executable probes
are mechanically reproducible here.

## 10. Re-execution evidence

### 10.1 Exact committed snapshots

Temporary Git clones were created from repository objects and checked out at the
exact commits. They retained Git metadata for Git-dependent tests, used the
locked project environment, did not copy user working-tree files, and were
removed after execution.

At implementation commit `194e8d8703acda0a5fa3b2f187c3236d65e90ffc`:

```text
python -m pytest -q \
  tests/unit/contracts/test_code_policy_schemas.py \
  tests/unit/contracts/test_code_policy_validation.py
102 passed in 32.24s

python -m pytest -q tests/unit/contracts
787 passed in 93.15s

python -m pytest -q
1312 passed in 133.99s

editor diagnostics for the committed D validator, diagnostics source, and both
focused test files: no issues
```

The current, not-yet-committed audit document was separately inspected read-only;
its editor diagnostics reported no issues. That observation is not represented
as evidence from the exact implementation snapshot.

At baseline-only commit `b0b283e501e5acdb6bb46fc610e793b4650ed2c2`:

```text
python tools/validate_repo.py --profile fast
outcome=PASS
PASS=9 KNOWN_STALE=1 EXPECTED_BLOCKED=1 FAIL=0 MISSING_TOOL=0 SKIPPED=0
```

The retained `KNOWN_STALE` item is the immutable historical Shellworld V1 run;
it must be superseded by a V2 contract-bound run, not rewritten. The
`EXPECTED_BLOCKED` item says the reviewed pytest identity matched but collection
lacked OS-enforced filesystem and network isolation. The aggregate reports
`network=offline-intended/preloaded` and `OS-network-blocking=not-enforced`.
This is a stated assurance boundary, not a Checkpoint D product failure.

### 10.2 Dirty-working-tree observations

Without modifying existing demo or WIP files, the current dirty working tree was
also observed:

```text
full pytest: 1316 passed in 101.80s

fast aggregate:
  outcome=PASS
  PASS=9
  KNOWN_STALE=1
  EXPECTED_BLOCKED=1
  FAIL=0
  MISSING_TOOL=0
  SKIPPED=0
```

The four-test difference from the exact 1,312-node D snapshot comes from current
untracked demo intake work, including `tests/test_demo_intake.py`. Those tests
are a dirty-tree regression observation only: they are excluded from the D
identity, were not touched by this audit work, and are not attributed to D.

## 11. Definition-of-Done evidence

| DoD item | Evidence and disposition |
|---:|---|
| 1. Plan committed alone before implementation | Exact parent chain in Section 2. **Met.** |
| 2. Exactly eleven implementation paths; unrelated work preserved | Git diff-tree equals the frozen eleven-path set; demo/intake/database/WIP absent. **Met.** |
| 3. Two closed, meta-valid, registry-resolvable, exactly pinned schemas | Raw identities in Section 3 and 26 focused schema nodes, including substitution and closure probes. **Met.** |
| 4. Canonical roots within explicit bounds and acyclic DAG | Exact root bytes, direct refs, one-way graph, and limit probes in Sections 3, 4, and 7. **Met.** |
| 5. 78-row diagnostic projection plus one separate reason | Complete exact table in Section 5 and ordered two-way bijection probe. **Met.** |
| 6. Only rows 72--78 added; meanings fixed; messages non-normative | Git/catalog comparison and catalog compatibility literals. **Met.** |
| 7. Immutable `1.0.0` genesis only; revision semantics deferred | Both closed schemas reject revision/locator/version alternatives; no ancestor API exists. **Met.** |
| 8. Policy exact-binds D catalog, B schema, and C roots without cycle | Recomputed refs and DAG in Sections 3--4; substitution/alias/cycle probes pass. **Met.** |
| 9. Synthetic reason only; no E reason | Exact sole registration in Section 6 and catalog count. **Met.** |
| 10. Bootstrap ordering | Catalog intrinsic precedes bijection and emitted-registration gate; fail-closed registration probes pass. **Met.** |
| 11. B then C once, then D; C unchanged and reason-unaware | Terminal composition probes and gate description in Section 6. **Met.** |
| 12. Detached, immutable, pure, deterministic, non-authoritative constraints | Seal/mutation/determinism/ambient-I/O probes; explicit same-interpreter limit. **Met within stated boundary.** |
| 13. Complete resource map and limit/plus-one coverage | Literals, formulas, and public boundary probes in Section 7; `path_hint` forbidden. **Met for D-controlled inputs; inherited registry traversal and OS availability remain unbounded.** |
| 14. Focused, contract, full, diagnostics, and fast checks pass | 102, 787, 1,312, final review `P0=0/P1=0`, and aggregate PASS in Sections 9--10. **Met with unsandboxed environment limit.** |
| 15. Identity generated deterministically and baseline-only committed | Section 8 records two exact-implementation candidate generations with byte-identical normalized canonical `test_identity` bytes and identical canonical/domain digests; 1,312 nodes; exactly 26 + 76 additions; zero removals; set/order hashes; baseline-only diff. **Met.** |
| 16. Independent adversarial and reader review has no P0/P1 | Review-session-reported final `P0=0`, `P1=0`; dispositions and key probes in Section 9. **Met.** |
| 17. Preserve milestone incompleteness and non-authority | Header, Sections 1 and 12 deny all listed authority and completion. **Met.** |

All 17 plan-defined DoD items are met within Checkpoint D's narrow scope and
explicit assurance limits. This scoped result does not complete M1 or V2 and
does not authorize merge or production use.

## 12. Non-authority, deferred work, and milestone state

Checkpoint D does not prove a real Catalog/Profile is published or selected. It
does not prove plan or frozen-scope applicability, source acquisition,
plan/scope membership, component cardinality, evidence resolution or relevance,
resource-observation authenticity, successful-artifact non-conflict, terminal
satisfaction, actor authorization, reviewer independence, signatures,
scientific truth, formal correctness, coverage, release, archive, merge,
database admission, or knowledge admission.

It contains no runtime, release, merge, bundle, CAS, intake, database, admission,
or arbitrary-arXiv authority. The catalog and policy are immutable genesis
candidate bytes; the vectors and linkage are non-normative fixtures. No pass
turns a synthetic terminal reason into a domain fact or satisfied obligation.

**M1: NOT COMPLETE.**

**AgtXIv V2: NOT COMPLETE.**

## 13. Next step

The only next step selected here is a **plan-only principle review of the
planning-contract option / proposed Checkpoint E**. That review should preserve
the dependency direction from planning through discovery to scope freeze and
should define a verifiable contract boundary before any implementation. This
audit does not preselect schemas, reason codes, storage layout, runtime behavior,
or other implementation details, and it does not authorize implementation in
advance of that reviewed plan.
