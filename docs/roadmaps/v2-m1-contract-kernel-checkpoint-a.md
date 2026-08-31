# AgtXIv V2 M1 contract kernel — Checkpoint A: offline schema registry

- Document status: implementation plan; not implementation evidence
- Document version: 1.0
- Checkpoint status: proposed and intentionally incomplete
- Committed basis reviewed: `f18f66a` and its parent history. The two newer M0
  pytest-inventory commits do not add contract-registry capability.
- Parent design: `docs/roadmaps/v2-m1-contract-kernel-slice-1.md`
- Date: 2026-08-31
- Authority: none for sealing, release, archive, certification, or knowledge
  admission

This checkpoint replaces the overly broad idea of implementing terminal results,
the artifact catalog, planning records, and a contract bundle at once. It defines
the next smallest reviewable step: build an offline registry from explicitly
supplied schema bytes, then use that registry to validate one generic immutable
record's envelope, payload, and canonical content hash.

Nothing in this document adopts the modified or untracked flat V2 schemas,
fixtures, validator, tests, specification, demos, or database prototype in the
working tree. All statements about current capability are based on committed
bytes only.

## Terms used

- **Raw asset:** the original bytes as supplied, before JSON normalization.
- **Exact asset reference:** identity, media type, byte length, and SHA-256 that
  together name one raw asset without using its path.
- **SHA-256:** the fixed 256-bit cryptographic fingerprint used here to detect
  any raw-byte change; it is identity evidence, not scientific approval.
- **Draft 2020-12:** the exact JSON Schema rulebook version admitted by this
  checkpoint.
- **Dialect:** the declared rulebook version used to interpret a schema; here it
  must be exactly Draft 2020-12.
- **Meta-schema / meta-validation:** the schema that checks whether another
  schema is itself well formed—checking the ruler before using it to measure.
- **URI:** a Uniform Resource Identifier. In this checkpoint it is an exact
  name, never an instruction to download anything.
- **RFC:** a public technical specification published as a “Request for
  Comments”; RFC 6901 defines JSON Pointer, RFC 3986 defines URI syntax, and RFC
  3339 defines date-time syntax.
- **Monkeypatch:** a test deliberately replaces shared program state to imitate
  third-party interference. The production result must remain unchanged.
- **Process-global registry:** one mutable table shared by all code in a running
  Python process; Checkpoint A must not trust it for contract meaning.
- **`$id`:** a schema's immutable, versioned identity label.
- **`$ref`:** a schema edge that points to an exact admitted schema or one exact
  JSON Pointer within it.
- **Schema registry:** a complete frozen in-memory map from exact schema
  identities to verified schema bytes; it is not a website or mutable service.
- **Payload:** the family-specific scientific or workflow content inside the
  common immutable-record envelope.
- **JSON Pointer:** the RFC 6901 `/field/child` notation used to address one
  location in a JSON value.
- **Fail closed:** reject missing or ambiguous evidence instead of guessing a
  substitute.
- **Directed acyclic graph:** a one-way reference graph with no path that loops
  back to its starting point.

## 1. Intuition: inspect the ruler before measuring the paper

A schema is a ruler: it says which fields exist and what they mean. A content
hash is the tamper seal on the measurement record. If AgtXIv validates a
terminal result or catalog before checking which exact ruler was used, a caller
can silently swap the ruler and still obtain a superficially valid result.

The offline registry is therefore like a sealed instrument cabinet:

1. receive a fixed set of byte strings, not paths or web addresses;
2. check each asset's label, byte length, and raw-byte fingerprint;
3. open each schema, check its declared identity and rulebook version;
4. connect references only to other instruments already in the cabinet; and
5. lock the cabinet into an immutable in-memory map before measuring a record.

An address beginning with `https://` is only an immutable name on a label. The
validator never treats it as permission to visit the Internet. This gives the
physical picture for fail-closed behavior: a missing instrument stops the
measurement; the system does not leave the room to find a similar-looking one.

Checkpoint A is the foundation under every later record family. It proves that
the exact schema named by an immutable record is present and that the record
matches it. It does **not** prove that a scientific claim is correct or that the
record is authorized for any lifecycle transition.

## 2. What is already committed

The committed package `src/agtxiv_v2/contracts/` currently provides:

- strict canonical JSON parsing and serialization under
  `agtxiv.record-canonical-json/2.0.0-candidate.1`;
- canonical immutable-record hash projection;
- eight versioned common Draft 2020-12 JSON Schemas: digest, exact asset,
  record and component references, actor identity, producer context, immutable
  record envelope, and resource budget;
- exact raw-asset, record, and component reference checks over explicitly
  supplied in-memory values;
- base-versus-contract-bound envelope checks, revision/supersession checks, and
  immutable-record content-hash recomputation;
- frozen diagnostic objects and stable canonical/reference/envelope/hash codes;
- focused tests for those capabilities.

The reference module states its boundary explicitly: direct record resolution
does not inspect schema `$id`, validate a payload against a family schema,
resolve an embedded schema reference, or walk transitive contract closure. The
filesystem-loading registry inside `test_common_schemas.py` is test setup, not a
reusable production boundary.

## 3. The exact gap closed by Checkpoint A

Checkpoint A adds only these capabilities:

1. Construct an immutable schema registry from caller-supplied raw assets and
   their exact asset references.
2. Verify raw byte length and SHA-256 before parsing a schema.
3. Parse schema JSON without losing duplicate keys or invalid number forms.
4. Require one valid, immutable, top-level `$id` per schema and globally unique
   asset IDs and schema IDs.
5. Require the exact Draft 2020-12 dialect declaration and meta-validate each
   schema using the already locked library implementation.
6. Resolve every non-fragment `$ref` only from the completed supplied registry.
   A missing reference, unsupported reference form, or possible remote lookup
   is an error.
7. Reject a cyclic schema-reference graph; the admitted exact-asset graph is a
   directed acyclic graph rather than a resolver-dependent recursion.
8. Validate a generic immutable record in three layers: common envelope rules,
   family payload rules from the exact registered schema, and canonical content
   hash equality.
9. Return deterministic diagnostics instead of leaking library exceptions.

Checkpoint A does not add a concrete payload family. Tests use small synthetic
schemas passed as bytes so that the generic mechanism is proven without
inventing `TypedTerminalResult` early.

## 4. Why this must precede terminal and catalog records

`TypedTerminalResult` answers why an expected artifact could not be produced.
That answer is safe only if its exact schema, permitted reason fields, evidence
shape, and content hash have already been fixed. Otherwise a producer could
change the terminal schema to make missing evidence appear acceptable.

The artifact-family catalog is a table of obligations. It is even more
sensitive: a changed catalog can remove an obligation from the denominator or
point to a substitute schema. Before the catalog can be trusted, the system
must be able to prove that every schema reference in it resolves to one exact,
offline byte target.

The dependency order is therefore:

```text
canonical bytes + exact raw references        [already committed]
                  |
                  v
offline registry + generic record validation  [Checkpoint A]
                  |
                  v
TypedTerminalResult                           [Checkpoint B]
                  |
                  v
artifact catalog + agentization profile       [Checkpoint C]
                  |
                  v
Plan -> Discovery -> independent Freeze       [Checkpoint D]
```

Building in this order prevents later domain records from depending on an
unreviewed test helper or on implicit filesystem/network behavior.

## 5. Exact implementation allowlist

The implementation commit for Checkpoint A may change only:

```text
src/agtxiv_v2/contracts/registry.py                         (new)
src/agtxiv_v2/contracts/schema_validation.py                (new)
src/agtxiv_v2/contracts/diagnostics.py                      (modify)
src/agtxiv_v2/contracts/__init__.py                         (modify)
tests/unit/contracts/test_registry.py                       (new)
tests/unit/contracts/test_schema_validation.py              (new)
```

No schema, fixture, command-line tool, package lock, aggregate validator,
roadmap denominator, demo, database file, or existing unit test is in the
allowlist. The already committed `jsonschema` and `referencing` dependency
versions are sufficient. If implementation proves otherwise, Checkpoint A
stops for a reviewed plan revision instead of expanding its staging set.

In particular, the implementation must not read, copy, normalize, reformat, or
infer semantics from dirty flat paths such as `schemas/v2/*.schema.json`,
`fixtures/v2-paper-agentization/`, `tools/validate_v2_paper_agentization.py`,
`tests/test_v2_paper_agentization.py`, the changed V2 specification, demos, or
database prototype.

Before commit, staging is by this explicit path list and
`git diff --cached --name-only` must equal the intended subset.

## 6. Pure functional boundary

The public seam and return contract are fixed for this checkpoint:

```python
@dataclass(frozen=True, slots=True)
class SchemaAssetBinding:
    exact_ref: ParsedCanonicalValue
    supplied_asset: SuppliedAsset

build_schema_registry(
    bindings: tuple[SchemaAssetBinding, ...],
) -> ContractSchemaRegistry | tuple[Diagnostic, ...]

validate_immutable_record_payload(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]
```

`SchemaAssetBinding` and `ContractSchemaRegistry` live in `registry.py`.
`ContractSchemaRegistry` is recursively frozen, cannot be constructed directly
by a caller, exposes no mutable mapping, and contains a detached snapshot of
every accepted schema and lookup index. It never retains a caller-owned
container or a live view of `SuppliedAsset`.

The builder result is an exclusive choice:

- success is one complete `ContractSchemaRegistry`; or
- failure is a nonempty, deterministically sorted tuple of `Diagnostic`.

It never returns an empty diagnostic tuple, a registry plus warnings, or a
partly usable registry. The record validator uses the ordinary convention that
an empty tuple means valid and a nonempty tuple means invalid.

`bindings` must have the exact runtime type `tuple`, and every member must have
the exact runtime type `SchemaAssetBinding`. An empty tuple returns
`AGTXIV.SCHEMA.EMPTY_REGISTRY`. A list, subclass, malformed member, wrong
`exact_ref` type, wrong `supplied_asset` type, forged opaque value, or wrong
registry/record argument returns `AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH`; it does
not raise an untrusted-data exception. Each reference enters through the
existing opaque `ParsedCanonicalValue` boundary.

Both functions must be deterministic and perform no:

- filesystem access;
- network or name-service access;
- clock, timezone, random-number, or environment access;
- Git, shell, child-process, database, or plugin access;
- mutation of inputs or module-global registry state.

All public input failures return diagnostics. An unexpected internal invariant
exception is an implementation defect, never an allowed input-dependent result.

### 6.1 Diagnostic aggregation and dependency gates

Registry construction uses these fixed phases:

1. input container/member types and nonempty input;
2. exact reference shape, media type, byte length, and raw hash;
3. strict JSON parsing and top-level object shape;
4. dialect, identity, closed-language, allowed-format, and meta-schema checks;
5. global asset-ID and schema-ID uniqueness;
6. exact reference closure and cycle detection;
7. frozen registry construction.

Any phase-1 diagnostic stops the whole build before an asset is inspected.

Each asset advances independently through phases 2–4. All independent problems
at its first failing phase are collected, but downstream diagnostics for that
asset are suppressed. Other assets still complete phases 2–4. Global phases 5
and 6 run only if every asset passes phase 4. Any diagnostic prevents phase 7.
This avoids misleading cascades such as reporting an unresolved `$ref` from
bytes that did not contain a valid schema.

Within phase 4, dialect and identity are prerequisites for closed-language
validation; closed-language and format validation are prerequisites for the
locked Draft 2020-12 meta-schema call. Diagnostics sort by phase rank, subject
identity, instance JSON Pointer, schema JSON Pointer, code, canonical bytes of
all remaining machine-readable fields, and finally UTF-8 message bytes. This is
a total order independent of stable-sort input position. No binding index,
input ordinal, path hint, or caller iteration order may be a tie-breaker.

Conflicts under one identity include the observed byte sizes, hashes, and schema
IDs (when available) in a canonical machine-readable `details` value, so
different conflicting bindings have a deterministic order. After sorting,
diagnostics with identical complete canonical serialization are collapsed to
one diagnostic. These ordering and deduplication rules are part of the
Checkpoint A contract.

Record validation first checks top-level shape and envelope. Envelope failure
gates schema binding, type binding, and payload validation. Exact schema-binding
failure gates type and payload validation; type-binding failure gates payload
validation. Content-hash recomputation is independent once the top-level record
shape is safe, so a payload error and a hash error may both be reported. No
failure authorizes a best-effort substitute.

## 7. Registry invariants

### 7.1 Exact bytes before meaning

For every schema asset, validation proceeds in this order:

1. Validate the exact reference shape using the committed reference rules.
   Registry use tightens the general `ExactAssetRef`: its `schema_uri` field is
   mandatory, not optional.
2. Resolve exactly one supplied asset by `asset_id`. Its
   `SuppliedAsset.schema_uri` must also be present; omission is invalid for a
   registry schema even though the general-purpose class permits omission.
   Either omission produces `AGTXIV.SCHEMA.ID_MISMATCH`.
3. Require media type `application/schema+json`.
4. Recompute raw byte length and `sha256:<64 lowercase hex>` over the original
   bytes; canonical JSON bytes are not substituted for this digest.
5. Strictly parse one JSON object and reject duplicate decoded keys,
   normalization collisions, malformed UTF-8, unsupported numbers, and trailing
   data.
6. Check schema identity, dialect, and meta-schema validity.
7. Only after all assets pass, construct the immutable registry and resolve its
   reference closure.

A path hint and schema URI are assertions or display metadata, never locators.
The implementation must not call the current filesystem test helper.

### 7.2 Identity and dialect

Each admitted schema must satisfy all of the following:

- `$schema` is exactly `https://json-schema.org/draft/2020-12/schema`;
- `$id` is a top-level string in the immutable, versioned AgtXIv contract-kernel
  namespace;
- `$id`, the exact reference's mandatory `schema_uri`, and the supplied asset's
  mandatory `schema_uri` are the same literal string;
- `asset_id` is unique across the input set;
- `$id` is unique across the input set, even when duplicate entries have
  identical bytes;
- nested `$id` values are rejected in this checkpoint rather than creating
  hidden sub-resources;
- unsupported dynamic or recursive reference features are rejected until a
  later version gives them explicit deterministic semantics;
- `Draft202012Validator.check_schema` or its locked equivalent accepts the
  schema.

This is intentionally narrower than every feature permitted by the general
JSON Schema standard. A smaller explicit language is safer than accidentally
changing behavior when a library learns a new resolver feature.

### 7.3 Closed schema language and exact traversal

Checkpoint A admits a closed subset of Draft 2020-12. At a schema-object node,
only these keywords are allowed:

```text
root identity:      $schema $id
reference/defs:     $ref $defs
annotations:        $comment title description default examples
                    deprecated readOnly writeOnly
applicators:        allOf anyOf oneOf not if then else
                    dependentSchemas prefixItems items contains
                    properties patternProperties additionalProperties
                    propertyNames unevaluatedItems unevaluatedProperties
validation:         type enum const multipleOf maximum exclusiveMaximum
                    minimum exclusiveMinimum maxLength minLength pattern
                    maxItems minItems uniqueItems maxContains minContains
                    maxProperties minProperties required dependentRequired
                    format
```

`$schema` and `$id` are allowed only on the top-level schema object. Boolean
schemas are allowed in schema-valued positions. Any other keyword at a schema
node fails with `AGTXIV.SCHEMA.META_INVALID`; this includes `$vocabulary`,
`$anchor`, `$dynamicAnchor`, `$dynamicRef`, `$recursiveAnchor`, and
`$recursiveRef`. A nested `$id` uses the more specific
`AGTXIV.SCHEMA.ID_MISMATCH`.

The walker knows which values are schemas instead of recursively scanning every
JSON object:

- `$defs`, `properties`, `patternProperties`, and `dependentSchemas` are maps
  whose values are schemas;
- `allOf`, `anyOf`, `oneOf`, and `prefixItems` are arrays of schemas;
- `not`, `if`, `then`, `else`, `items`, `contains`, `additionalProperties`,
  `propertyNames`, `unevaluatedItems`, and `unevaluatedProperties` contain one
  schema or boolean schema;
- all other allowed keyword values are ordinary data or scalar constraints.

In particular, objects or strings stored inside `const`, `enum`, `examples`, or
`default` are instance data. A key named `$ref`, `$id`, `format`, or any other
schema keyword inside that data is not traversed, resolved, or rejected.
Property names and `$defs` member names are also names, not keywords; only their
mapped values are traversed as schemas. This prevents both false references and
hidden traversal behavior.

Before resolving any `$ref`, the walker mechanically builds the complete set of
schema locations: the root plus exactly the object or boolean descendants
reached through the schema-valued positions listed above. Every local or
external fragment target must be a member of that set in its target resource.
Pointer existence and an object-looking value are not enough. For example,
`"const":{"type":"string"}` is ordinary instance data, so `$ref: "#/const"`
fails with `AGTXIV.SCHEMA.UNRESOLVED_REF` even though the pointer exists and its
value resembles a schema. The same rule rejects pointers into scalar or boolean
ordinary data. A boolean reached through a genuine schema-valued position is,
by contrast, a valid boolean schema location.

### 7.4 Fixed format vocabulary

The only allowed `format` strings are exactly `uri` and `date-time`. Any other
value, non-string value, or format supplied by a machine-local plugin fails
registry construction with `AGTXIV.SCHEMA.META_INVALID`, even when no test
instance reaches that schema branch.

`schema_validation.py` owns a private immutable checker containing only two
project predicates: a fixed RFC 3986 URI-syntax predicate and a fixed RFC 3339
date-time predicate. Accepted and rejected boundary vectors are locked in
`test_schema_validation.py`. The checker does not copy, consult, or extend
`jsonschema.FormatChecker`'s process-global registry, entry points, or plugins.
Format checking is an assertion, not normalization: it never rewrites a value.

An adversarial test monkeypatches the process-global jsonschema format table
before importing/reloading `schema_validation.py`, and again before validation.
The accepted values, rejected values, diagnostic tuple, and order must remain
unchanged. This test proves that a third-party plugin cannot silently change
contract meaning.

### 7.5 References stay offline

Every `$ref` string must have exactly one of these three literal forms:

```text
#/<RFC-6901-pointer-tokens>
<exact-supplied-$id>
<exact-supplied-$id>#/<RFC-6901-pointer-tokens>
```

Pointer tokens use only RFC 6901 `~0` and `~1` escapes; a stray `~` is invalid.
Bare `#`, relative references, queries, percent-encoded aliases, dot segments,
case changes, default-port insertion/removal, Unicode/host normalization, and
trailing-slash aliases are not accepted. The implementation does not call a URI
joiner, parser-based canonicalizer, percent decoder, or normalizer. It compares
the schema-ID prefix as a literal string against the supplied registry and then
resolves the literal JSON Pointer. Resolution succeeds only when the pointer is
in the precomputed schema-location set from Section 7.3. An HTTPS-looking ID is
still only a key.

The closure walker tracks resource-plus-fragment nodes. It rejects a real
reference cycle with a stable diagnostic. A one-way local reference from a
property to a leaf in `$defs` is not a cycle, but recursive references back to
an active node are. Cross-schema edges must form a directed acyclic graph.

The following fail closed:

- an absent target, including an AgtXIv-looking HTTPS name;
- a floating, relative, `latest`, branch, file, data, or non-AgtXIv URI;
- a target that exists only under a path hint;
- a duplicate target ID;
- a reference that the underlying library proposes to retrieve remotely;
- an unresolved or invalid JSON Pointer fragment.

Registry construction verifies the full reference graph, including references
inside conditionals and definitions, before any instance is validated. An
unused bad reference in a schema-valued location is still a bad contract asset.
The walker never scans ordinary data held by `const`, `enum`, `examples`, or
`default` for reference-looking strings or keys.

## 8. Generic immutable-record validation

The validator receives one parsed record and the already complete registry. It
performs these independent checks and reports all safely collectable failures
in stable order:

1. **Envelope:** reuse the committed common envelope and supersession rules.
2. **Schema binding:** resolve `envelope.schema_ref` to exactly one registered
   raw schema and require its `$id`, type, byte size, and digest to agree.
3. **Type binding:** require the schema's declared record-family identity to
   agree with `envelope.record_type`; no inference from a filename is allowed.
4. **Payload:** validate `payload` through the family schema's explicit payload
   entry point.
5. **Hash:** recompute the committed canonical projection over `envelope` and
   `payload`, excluding only the outer `content_hash`, then require equality
   with the stored lowercase SHA-256 value.

For Checkpoint A, a schema used as a record-family schema declares those two
bindings explicitly:

```json
{
  "$defs": {
    "recordType": {"const": "agtxiv.example-family/1.0.0"},
    "payload": {"type": "object"}
  }
}
```

The actual payload schema may of course be stricter. A schema lacking exactly
one string `#/$defs/recordType/const` or one `#/$defs/payload` entry can remain a
registered component schema, but it cannot validate an immutable record. This
convention makes the binding explicit without a filename guess or a new custom
JSON Schema keyword.

Schema shape validation cannot replace steps 1, 2, 3, or 5. Conversely, a
matching hash proves byte identity, not payload conformance. Both are required.
The output must be independent of schema input order, dictionary insertion
order, locale, current directory, and network availability.

Checkpoint A validates one record in isolation. It does not recursively approve
the referenced contract bundle, producer implementation, environment, earlier
revision, or any scientific evidence. Those remain exact references awaiting
later closure validators.

## 9. Stable diagnostics added in Checkpoint A

Existing exact-reference and record codes remain unchanged. Checkpoint A adds
and locks only the minimum new meanings:

| Code | Stable meaning |
| --- | --- |
| `AGTXIV.SCHEMA.EMPTY_REGISTRY` | Registry construction received no schema bindings. |
| `AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH` | A public registry/record-validation argument has the wrong exact runtime type or a forged typed value. |
| `AGTXIV.SCHEMA.INVALID_DOCUMENT` | Strict parsing succeeded, but the supplied schema is not one top-level JSON object. |
| `AGTXIV.SCHEMA.DIALECT_MISMATCH` | `$schema` is absent or is not the exact Draft 2020-12 dialect. |
| `AGTXIV.SCHEMA.ID_MISMATCH` | `$id` is absent, mutable/invalid, nested, or disagrees with the exact asset binding. |
| `AGTXIV.SCHEMA.DUPLICATE_ID` | More than one supplied schema claims the same asset ID or schema ID. |
| `AGTXIV.SCHEMA.META_INVALID` | The schema fails the locked meta-schema, uses an unknown/forbidden keyword, or names a format outside `{uri, date-time}`. |
| `AGTXIV.SCHEMA.UNRESOLVED_REF` | A `$ref` or fragment cannot resolve uniquely within the supplied registry. |
| `AGTXIV.SCHEMA.REFERENCE_CYCLE` | The resource-plus-fragment reference graph contains a cycle. |
| `AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN` | A reference would require, or could trigger, lookup outside the supplied registry. |
| `AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH` | The record type does not agree with the exactly bound family schema. |
| `AGTXIV.RECORD.PAYLOAD_INVALID` | The payload fails the exactly bound family schema. |

Raw length/digest/media mismatches continue to use the existing reference
codes, and canonical content mismatch continues to use
`AGTXIV.RECORD.HASH_MISMATCH`. No new code is allowed to blur these distinct
causes. A `$ref` outside the three literal forms in Section 7.5 uses
`REMOTE_REF_FORBIDDEN`; an admitted literal form whose exact ID or pointer is
absent uses `UNRESOLVED_REF`.

There are two different determinism promises:

- With the same implementation bytes, dependency lock, canonicalization
  profile, and inputs, the complete ordered diagnostic serialization is
  byte-identical across repetitions and input-order permutations.
- Across later compatible implementation versions, only diagnostic phase,
  code meaning, subject identity, instance JSON Pointer, schema JSON Pointer,
  and byte offset (when applicable) are stable. Human-readable messages and the
  complete serialized bytes may improve and are not cross-version identity.

Host library exception text is never a stable interface. `Diagnostic` may gain
optional phase, subject-identity, schema-pointer, and canonical machine-readable
`details` fields with backward-compatible defaults; existing constructor
behavior, codes, JSON Pointer meaning, and serialized fields remain unchanged
for existing callers. The total phase-first order and exact-duplicate collapse
fixed in Section 6.1 apply to all new diagnostics.

## 10. One-way bootstrap graph: no hash cycles

Schemas, a future catalog, a future profile, policies, and an error catalog are
raw contract assets. They are not contract-bound runtime records. Their
identity comes from `ExactAssetRef`: asset ID, media type, byte size, and raw
SHA-256.

The one-way dependency graph is:

```text
bootstrap canonicalizer + registry implementation
    -> ExactAssetRef -> supplied raw schema bytes -> declared schema $id
    -> validated immutable record -> exact family schema

future ContractBundleRelease
    -> schema assets
    -> profile asset
    -> catalog asset
    -> policy and error-catalog assets
```

The arrows mean “contains an exact reference to.” The reverse arrows are
forbidden:

- a schema must not reference its containing contract bundle;
- the catalog and profile must not contain `contract_bundle_ref`;
- the bundle must not contain or hash itself;
- a catalog/profile path must not be used as identity;
- no `latest`, branch name, current working tree, or mutable registry alias may
  close a missing edge.

The bundle is built last from already fixed raw assets. A later post-build
receipt may point to the bundle, but the bundle cannot point back to that
receipt. Checkpoint A establishes only the lower registry edges; it creates no
bundle candidate.

## 11. Required adversarial tests

Priority 0 means a correctness or safety failure that blocks this checkpoint.
Priority 1 means a major determinism or diagnosability failure that also blocks
merge until fixed.

### 11.1 Priority 0: identity, substitution, and authority attacks

Tests must prove rejection of:

- empty input and every wrong container/member/record/registry runtime type,
  always as the exact diagnostic-only branch of the public result;
- stale byte size, stale raw hash, wrong media type, or a digest calculated from
  canonicalized rather than original bytes;
- omission or mismatch of `schema_uri` on either the registry exact reference
  or its `SuppliedAsset`;
- duplicate asset IDs and duplicate `$id` values, including byte-identical
  duplicates and order permutations;
- missing, malformed, nested, mutable, unversioned, or binding-mismatched `$id`;
- an absent/wrong `$schema`, invalid meta-schema, an unknown schema-node
  keyword, `$anchor`, any `$dynamic*`/`$recursive*` keyword, and every other
  feature outside the Section 7.3 language;
- every schema-valued container in Section 7.3 hiding an invalid descendant,
  while reference-looking keys and strings inside `const`, `enum`, `examples`,
  and `default` remain ordinary data;
- `$ref` pointers into object, boolean, and scalar ordinary-data targets,
  including `#/const`, while pointers to object and boolean values in genuine
  schema locations succeed;
- any `$ref` target not already supplied, a path-hint substitute, remote
  fallback, an invalid fragment, a nonliteral/normalized alias, or an
  unused-but-unresolved reference;
- an unknown/non-string `format`, with positive and negative vectors for the
  fixed `uri` and `date-time` checkers;
- a caller dictionary that bypasses strict parsed-value boundaries;
- a schema or supplied asset mutated after registry construction;
- an envelope schema reference swapped to equal-shape bytes with a different
  identity or hash;
- record type/schema mismatch, payload mismatch, and content-hash mismatch;
- treating a registry pass as bundle, release, archive, certification, or
  admission authority.

Network and filesystem sentinels must make the test fail if production code
attempts `open`, socket/name resolution, URL retrieval, Git, or a subprocess.
The format test also monkeypatches the process-global jsonschema checker before
module load and before validation; results must remain unchanged.

### 11.2 Priority 1: determinism and total failure behavior

Tests must also cover:

- input schema order and record object insertion-order permutations;
- repeated construction and validation producing byte-identical diagnostics;
- every permutation of three bindings with the same asset/schema identity but
  different raw sizes/hashes, proving the full tie-break order and exact-
  duplicate collapse without using an input index;
- multiple payload errors sorted by phase, identity, pointers, and code rather
  than host library iteration order;
- phase-gating matrices proving that binding failure suppresses parse/identity/
  reference noise, parse failure suppresses identity/reference noise, any
  preflight failure suppresses global closure, and record schema/type failures
  suppress only their dependent payload check;
- duplicate JSON keys, invalid UTF-8, normalization collisions, deep nesting,
  unsupported number forms, and forged opaque values without uncaught library
  exceptions;
- local or cross-schema `$ref` cycles rejected with
  `AGTXIV.SCHEMA.REFERENCE_CYCLE`, never resolved by the network or allowed to
  reach a recursion crash;
- unknown formats and format-checker behavior fixed explicitly rather than
  inherited from machine-local plugins, including global-checker monkeypatches;
- empty asset sets, wrong tuple/member runtime types, and very large pointer
  indexes without integer-conversion or resource leaks;
- repeated calls in the same build keep complete message bytes stable, while a
  simulated compatible message-only revision preserves the cross-version fields
  listed in Section 9;
- success returns only a complete non-constructible frozen registry, failure
  returns only a nonempty tuple, and mutating every original input after either
  result cannot alter a later lookup or validation.

Positive tests include all eight committed common schemas as one offline graph
and at least two synthetic payload families sharing a common definition. They
must validate without reading those schemas from disk inside the pure package.

## 12. Explicit non-authority boundary

A Checkpoint A pass means only:

> These explicitly supplied schema bytes form one internally valid offline
> registry, and this immutable record matches its exact family schema and
> canonical content hash.

It does not mean:

- the schema set is a complete contract bundle;
- a terminal result is scientifically adequate;
- the artifact-family denominator is complete;
- producer/reviewer role labels prove independence or authorization;
- a source package, Plan, discovery result, or frozen scope is valid;
- a Paper Agent release is sealed, signed, reproducible, archived, certified,
  or admitted to the knowledge database;
- M1, M1.5, or any later milestone is complete.

The registry exposes no `seal`, `release`, `archive`, `certify`, `admit`, or
state-transition API. Neither a boolean field nor a caller-supplied role may
promote its result.

## 13. Definition of Done

Checkpoint A is complete only when all of the following are true:

1. The staged implementation diff is a subset of the six-path allowlist in
   Section 5, with no dirty flat V2 working-tree path adopted.
2. The registry API is immutable, order-independent, and accepts only explicit
   in-memory exact asset bindings; it returns exactly a complete frozen registry
   or a nonempty diagnostic tuple.
3. Every admitted schema has verified raw bytes, exact unique identity, exact
   mandatory `schema_uri` agreement on all three representations, exact Draft
   2020-12 dialect, valid closed-language/meta-schema checks, fixed formats, and
   a fully offline acyclic reference closure whose fragments land only on the
   mechanically derived schema-location set.
4. Registry construction is atomic: one invalid asset yields diagnostics and no
   usable partial registry; diagnostic aggregation has a total input-order-
   independent sort and collapses only exact duplicates.
5. Generic validation checks envelope, exact schema/type binding, payload, and
   canonical content hash as separate gates.
6. Every Priority 0 and Priority 1 case has a deterministic focused test; no
   user-data case escapes as an uncaught `jsonschema` or `referencing`
   exception.
7. Existing canonical, common-schema, and exact-reference tests still pass.
8. The focused new tests, the full pytest suite, and the repository fast
   validation complete without a new failure. A pre-existing repository
   evidence blocker is reported separately and is not reclassified as M1
   success.
9. An independent adversarial review reports zero open Priority 0 or Priority 1
   findings.
10. The implementation checkpoint records the exact Git commit, commands,
    counts, diagnostic-code set, same-build versus cross-version determinism
    boundary, known limitations, and the next checkpoint.

Completion of this list authorizes only Checkpoint B design/implementation. It
does not authorize sealing a bundle or changing lifecycle state.

## 14. Ordered follow-up checkpoints

### Checkpoint B — `TypedTerminalResult`

Add the first concrete family schema and validator on top of Checkpoint A. Lock
terminal outcome/reason/evidence semantics and prove that a terminal result can
account for failure without pretending the missing artifact exists. It remains
non-authoritative until catalog/profile binding exists.

### Checkpoint C — artifact catalog and agentization profile

Add the raw-byte-addressed artifact-family catalog and profile, their schemas,
and cross-validation. Lock the denominator outside producer control. Keep both
as raw exact assets so neither references its future containing bundle.

### Checkpoint D — Plan, discovery, and independent freeze

Add `AgentizationPlan`, `InventoryDiscoveryResult`, `ScopeFreezeDecision`, and
`FrozenInventoryScope` in that order. Separate source observation from producer
proposal and reviewer acceptance. A role string is only a label; independent
review requires exact identity and provenance checks.

Only after A through D and the remaining normative asset closure are reviewed
may a later checkpoint build a one-way `ContractBundleRelease` candidate. That
later candidate still begins without production, archive, or admission
authority.
