# AgtXIv V2 M1 contract-kernel Checkpoint A implementation audit

- Audit status: PASS WITH EXPLICIT NON-AUTHORITY
- Checkpoint A scoped implementation result: PASS
- M0 status: NOT COMPLETE
- M1 and AgtXIv V2 status: NOT COMPLETE
- Audit date: 2026-08-31
- Implementation commit: `7734fe5187651251f02624c418012630ccfbc5ae`
- Baseline-only commit: `b470ac23b7ecc5a76bae50aadc4f17162b6c539d`
- Parent plan: `docs/roadmaps/v2-m1-contract-kernel-checkpoint-a.md`
- Release, archive, certification, merge, and knowledge-admission authority:
  none

## 1. Executive finding

Checkpoint A implements the smallest registry-first M1 contract slice. It can
construct one recursively frozen, fully offline registry from explicitly
supplied schema bytes and exact asset references. It can then validate one
generic immutable record against the exact family schema selected by its
envelope, including the record type, payload, and canonical content hash.

The physical picture is a ruler kept in a closed instrument cabinet:

- a schema is the ruler that defines what a record means;
- the raw SHA-256 digest is the ruler's byte-level fingerprint;
- the registry is a cabinet whose complete contents are supplied before use;
- an HTTPS-looking schema identifier is a label, not a door to the network;
- containment and `$ref` edges form a map that must have no cycle; and
- a missing instrument stops validation instead of triggering a search for a
  similar substitute.

This result says that the named bytes and the measured record agree. It does not
say that the scientific claim is true, that a reviewer is independent, or that
the record may be merged, released, archived, certified, or admitted to the
knowledge database.

## 2. Version and change boundary

Implementation commit `7734fe5187651251f02624c418012630ccfbc5ae`
changes exactly the six paths authorized by Checkpoint A:

| Path | Change |
|---|---|
| `src/agtxiv_v2/contracts/registry.py` | New offline schema-registry implementation |
| `src/agtxiv_v2/contracts/schema_validation.py` | New generic immutable-record payload validator |
| `src/agtxiv_v2/contracts/diagnostics.py` | Stable schema/record codes and canonical diagnostic context |
| `src/agtxiv_v2/contracts/__init__.py` | Public Checkpoint A exports |
| `tests/unit/contracts/test_registry.py` | Registry, closure, determinism, and adversarial tests |
| `tests/unit/contracts/test_schema_validation.py` | Generic record, format, gate, and hostile-input tests |

It does not adopt or modify the dirty flat V2 schemas, fixtures, aggregate
validator, demos, database prototype, specifications, presentations, paper
sources, or other user work in progress.

The later commit `b470ac23b7ecc5a76bae50aadc4f17162b6c539d`
changes only
`baselines/repository-validation/pytest/test-identity-v1.json`. Separating that
baseline update from the implementation keeps the test-identity evidence from
being hidden inside the feature commit.

## 3. Implemented contract

The public seam is deliberately small:

```python
build_schema_registry(
    bindings: tuple[SchemaAssetBinding, ...],
) -> ContractSchemaRegistry | tuple[Diagnostic, ...]

validate_immutable_record_payload(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]
```

The implementation provides:

- exact tuple/member/runtime-type gates and detached input snapshots;
- raw byte-length and SHA-256 verification before schema parsing;
- strict canonical JSON parsing, exact top-level `$id`, and exact Draft 2020-12
  dialect binding;
- a closed schema language with a typed walker that does not mistake data under
  `const`, `enum`, `examples`, or `default` for schemas;
- fixed `uri` and `date-time` checks isolated from the process-global format
  table;
- literal local or already-supplied `$ref` resolution with exact schema-location
  closure and no filesystem or network fallback;
- deterministic strongly connected component checks over containment and
  reference edges, rejecting recursive cycles;
- immutable registry snapshots with fail-closed integrity checks;
- phase-gated, totally ordered diagnostics that preserve distinct binding
  observations and collapse only exact duplicates; and
- envelope, exact schema binding, record-type binding, family payload, and
  canonical content-hash checks with the documented dependency gates.

The payload validator resolves through a complete in-memory registry. It does
not detach a payload subschema from its family `$id`, and diagnostics retain the
actual schema identity and schema pointer after local or cross-schema
references.

## 4. Validation evidence and its boundaries

### 4.1 Focused implementation evidence

The frozen six-file implementation candidate, subsequently committed without a
change to those files as `7734fe5187651251f02624c418012630ccfbc5ae`, produced:

```text
tests/unit/contracts/test_registry.py
tests/unit/contracts/test_schema_validation.py
148 passed

tests/unit/contracts/
311 passed
```

The implementation and tests also passed Python bytecode compilation and
tracked/untracked whitespace diff checks. Independent adversarial and reader
reviews reported zero open Priority 0 findings and zero open Priority 1
findings.

### 4.2 Post-baseline exact collection check

After the baseline-only commit, the exact pytest identity operation reported:

```text
operation: CHECK
outcome: PASS
collected/selected: 782/782
deselected: 0
collection skips: 0
```

This is collection-identity evidence, not a claim that 782 tests executed. Its
reviewed identities are:

| Identity | SHA-256 |
|---|---|
| Raw baseline JSON bytes | `2f5fd32cc0cc77334b0709300428c9df8cb77efc4808e57ecf1ca58bf4a3ac6a` |
| Domain-separated test identity | `4b18dbbfac3dee2cf31bba9c7cb716651e33bbf298ef350bb323086f9ea2f682` |
| Full collected node set | `373ea1c346f637f4184fa6f494370be98a40f0e0a282d6156653573487a20b91` |
| Selected execution order | `3cfb4e233eff2fe57459f3e7c4b04fd0af335e71eb1991ae66575102bfadce61` |

### 4.3 Dirty-working-tree observations

The primary working tree, which contained pre-existing modified and untracked
user work outside Checkpoint A, produced:

```text
full pytest: 824 passed

fast aggregate:
  PASS=9
  FAIL=0
  KNOWN_STALE=1
  EXPECTED_BLOCKED=1
```

The 824 result is explicitly a dirty-working-tree observation. It is not an
execution result for exact commit `7734fe5187651251f02624c418012630ccfbc5ae`
or baseline-only commit `b470ac23b7ecc5a76bae50aadc4f17162b6c539d`, and
it must not be presented as clean-commit or branch-admission evidence.

The fast aggregate's sole `KNOWN_STALE` result is the retained historical
Shellworld V1 run. Its sole `EXPECTED_BLOCKED` result records that pytest
identity matched but collection did not run under operating-system-enforced
filesystem and network isolation. Overall `PASS` therefore does not upgrade
either limitation or make the dirty working tree release evidence.

## 5. Diagnostic codes added

Checkpoint A adds these stable code meanings:

| Code | Meaning |
|---|---|
| `AGTXIV.SCHEMA.EMPTY_REGISTRY` | No schema binding was supplied |
| `AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH` | A public input has the wrong exact runtime type or is forged |
| `AGTXIV.SCHEMA.INVALID_DOCUMENT` | Parsed schema content is not one top-level object |
| `AGTXIV.SCHEMA.DIALECT_MISMATCH` | The exact Draft 2020-12 declaration is absent or different |
| `AGTXIV.SCHEMA.ID_MISMATCH` | Schema identity is absent, mutable, invalid, nested, or binding-mismatched |
| `AGTXIV.SCHEMA.DUPLICATE_ID` | An asset or schema identity is not unique |
| `AGTXIV.SCHEMA.META_INVALID` | Closed-language, format, regular-expression, or meta-schema validation failed |
| `AGTXIV.SCHEMA.UNRESOLVED_REF` | An admitted literal reference has no exact supplied schema location |
| `AGTXIV.SCHEMA.REFERENCE_CYCLE` | Typed containment and reference edges contain a cycle |
| `AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN` | A reference is outside the three exact offline literal forms |
| `AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH` | The envelope record type disagrees with the exact family schema |
| `AGTXIV.RECORD.PAYLOAD_INVALID` | The payload fails the exact family schema |

Existing canonical, exact-reference, envelope, and content-hash codes retain
their prior meanings.

## 6. Determinism boundary

There are two intentionally different promises.

Within the same implementation bytes, dependency lock, canonicalization
profile, and inputs, the complete ordered diagnostic serialization is
byte-identical across repetitions and input-order permutations. Ordering uses
phase, subject identity, instance JSON Pointer, schema JSON Pointer, code, and
canonical machine-readable context before the human message. Exact duplicates
alone are collapsed.

Across later compatible implementation versions, only these fields are stable:

- diagnostic phase;
- diagnostic-code meaning;
- subject identity;
- instance JSON Pointer;
- schema JSON Pointer; and
- byte offset, when present.

Human messages, optional machine-readable details, and the complete serialized
bytes may improve in a later compatible version. A same-build full-byte promise
must therefore not be misrepresented as a permanent cross-version byte
identity.

## 7. Review finding and threat boundary

The final independent reviews found no open Priority 0 or Priority 1 issue. One
non-blocking Priority 2 limitation remains explicit: the registry's private,
unkeyed seal is an integrity sentinel for accidental corruption or ordinary
public-API misuse. It is not a cryptographic signature, authenticator, or
defense against arbitrary malicious code in the same Python interpreter.

The useful physical distinction is that this registry is a locked and counted
instrument cabinet, not a signed vault. Future authenticity requires a reviewed
signature design and/or a stronger process-isolation boundary; Checkpoint A
does not claim either.

## 8. Non-authority and remaining milestone state

Checkpoint A exposes no `seal`, `release`, `archive`, `certify`, `admit`, or
lifecycle-transition API. A successful registry build or record validation:

- does not approve a contract bundle;
- does not prove scientific correctness or formalization fidelity;
- does not authorize merge, release, archive, certification, or knowledge
  admission;
- does not establish reviewer independence, rights clearance, signatures, or
  operating-system isolation; and
- does not prove the arbitrary-arXiv pipeline, Paper Agent directed acyclic
  graph, complete V2 file set, database, or web demo.

M0 remains **NOT COMPLETE** with its previously recorded governance, isolation,
toolchain, formal-revalidation, rights, signing, and repository-policy blockers.
Checkpoint A also does not complete M1 or AgtXIv V2.

The next implementation checkpoint is Checkpoint B,
`TypedTerminalResult`. It adds the first concrete payload family on top of this
registry so a producer can account for an expected artifact that could not be
produced without pretending that artifact exists. It still grants no release or
knowledge-admission authority; catalog and profile binding remain later work.
