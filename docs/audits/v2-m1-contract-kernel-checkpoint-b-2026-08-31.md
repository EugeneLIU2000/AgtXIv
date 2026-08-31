# AgtXIv V2 M1 contract-kernel Checkpoint B implementation audit

- Audit status: PASS WITH EXPLICIT NON-AUTHORITY
- Checkpoint B scoped result: PASS
- M0 status: NOT COMPLETE
- M1 and AgtXIv V2 status: NOT COMPLETE
- Audit date: 2026-08-31
- Plan commit: `38040b0157a055f5317cbf7b0b9f6134d68dab5a`
- Implementation commit: `750fa0d091b548cd5d8bcdc26324bc79b2cb79ed`
- Baseline-only commit: `c95c355c8ea1104872a97badc33e80b99bfea326`
- Parent plan: `docs/roadmaps/v2-m1-contract-kernel-checkpoint-b.md`
- Merge, release, archive, certification, and knowledge-admission authority:
  none

## 1. Executive finding

Checkpoint B adds the first concrete record family on top of Checkpoint A's
offline schema registry. `TypedTerminalResult/1.0.0` records that one attempt
ended without producing one expected artifact. It binds that attempt to an
obligation, exact evidence references, a retry disposition, a next action, and
declared resource observations.

The physical picture is an exception card attached to an empty delivery slot:

- the card explains why this attempt stopped;
- the empty slot remains empty and remains in the accounting denominator;
- the card cannot use a syntactically terminal-typed record/component
  reference, or a direct record/component self-reference, as evidence;
- the card cannot claim that the expected artifact was produced;
- the card cannot claim that the obligation was satisfied; and
- the card cannot approve review, release, merge, or database admission.

An empty result from
`validate_typed_terminal_result_intrinsic(record, registry)` therefore means
only that this one exception card is mechanically self-consistent under the
exact official schema bytes. It does not prove that a referenced object exists,
that evidence is relevant or true, that an actor is authorized, or that a later
catalog policy may count the disposition.

## 2. Version and change boundary

The plan was committed before implementation. The implementation commit changes
exactly the six paths authorized by that plan:

| Path | Change |
|---|---|
| `schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json` | Complete closed family schema and standalone immutable-record root |
| `src/agtxiv_v2/contracts/terminal_validation.py` | Pure intrinsic validator and compiled official schema reference |
| `src/agtxiv_v2/contracts/diagnostics.py` | Seven stable terminal diagnostic codes |
| `src/agtxiv_v2/contracts/__init__.py` | Public intrinsic-validator export |
| `tests/unit/contracts/test_typed_terminal_result.py` | Exact schema, offline registry, and standalone-root tests |
| `tests/unit/contracts/test_terminal_validation.py` | Intrinsic, adversarial, totality, and determinism tests |

The implementation commit contains 3,211 insertions. It does not include a
baseline or audit update. It does not adopt or modify the dirty flat V2 schemas,
fixtures, aggregate validator, demos, database prototype, specifications,
presentations, references, or other user work in progress.

The separate baseline-only commit changes only:

```text
baselines/repository-validation/pytest/test-identity-v1.json
```

## 3. Exact family ruler

The official schema binding is:

| Field | Exact value |
|---|---|
| Asset ID | `schema:typed-terminal-result:1.0.0` |
| Media type | `application/schema+json` |
| Schema URI | `https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0` |
| Raw byte size | `16054` |
| Raw SHA-256 | `sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6` |
| Record type | `agtxiv.typed-terminal-result/1.0.0` |

The raw byte size and digest are compiled into the production validator. Tests
mechanically recompute both from the schema file. The terminal schema plus the
eight committed common schemas form a nine-schema offline, closed, acyclic
Checkpoint A registry.

The intrinsic validator uses three hard prerequisite gates:

1. safely inspect exact public types, registry integrity, opaque record
   integrity, the outer three-key shape, and the minimum envelope/schema-ref
   shape;
2. require all five compiled official schema-ref fields and the presence of
   `producer_context`; and
3. run Checkpoint A's generic envelope, exact schema, record type, payload, and
   canonical content-hash validation.

No terminal payload field is interpreted before all three gates pass. A schema
with the same `$id` but different raw bytes therefore cannot act as a looser
ruler.

The standalone JSON Schema root and the intrinsic API have deliberately
different mechanical powers. The standalone root checks the complete structural
shape, including the envelope, producer context, payload, and digest spelling.
It cannot recompute the record content hash and cannot embed its own raw-byte
digest without creating a self-reference. Exact raw-schema pinning and content-
hash recomputation are intrinsic-API checks. This clarifies the otherwise
ambiguous rejection wording in the implementation plan's test section.

## 4. Implemented intrinsic invariants

After the three prerequisite gates, the validator checks, in fixed order:

- payload and producer-context attempt IDs are identical;
- the context branch is exactly profile-, plan-, or frozen-scope-bound;
- plan- and frozen-scope-bound obligations use a component basis whose record
  projection equals the declared plan or scope;
- the target names an obligation rather than an invented missing artifact or a
  terminal family;
- terminal record/component bases, syntactically terminal-typed
  record/component evidence, direct record/component self-evidence, duplicate
  evidence IDs, duplicate authoritative references, and unordered evidence are
  rejected;
- the five operational outcomes obey their exact retry and next-action matrix;
- retry and deadline tagged unions are closed and contain no permanent state;
- every declared resource limit is represented exactly once as observed or
  unobserved, using the fixed six-key mapping and order; and
- the submitted resource relation equals the deterministic comparison rule.

The authoritative reference projection removes `path_hint` only from exact
asset-reference locations, including a record/component reference's nested
`schema_ref`. Every other field, including `schema_uri`, remains part of
identity. The original record content hash still commits the submitted
`path_hint`, so changing that navigation hint changes the record hash even
though it does not change which referenced object is meant.

Resource comparison gives a known exceedance priority over an unobserved second
dimension. A submitted exceedance is a mechanical relation between submitted
numbers, not proof that monitoring was authentic or that resource use caused
the terminal outcome.

## 5. Stable diagnostics

Checkpoint B adds exactly these stable meanings:

| Code | Meaning |
|---|---|
| `AGTXIV.TERMINAL.SCHEMA_MISMATCH` | Envelope schema ref differs from the compiled official raw schema binding |
| `AGTXIV.TERMINAL.ATTEMPT_MISMATCH` | Attempt binding or required producer context is inconsistent |
| `AGTXIV.TERMINAL.CONTEXT_INVALID` | Context mode or plan/scope basis binding is inconsistent |
| `AGTXIV.TERMINAL.TARGET_INVALID` | Target names a terminal family or terminal record basis instead of an obligation |
| `AGTXIV.TERMINAL.EVIDENCE_INVALID` | Evidence identity, order, uniqueness, self-reference, or terminal type is invalid |
| `AGTXIV.TERMINAL.DISPOSITION_INVALID` | Outcome, retry, or next action violates the closed matrix |
| `AGTXIV.TERMINAL.RESOURCE_INVALID` | Resource partition, order, or relation violates the mechanical rule |

Ordinary structural failures continue to use Checkpoint A's generic payload or
record diagnostics. The public API docstring explicitly says that an empty
diagnostic result proves intrinsic conformance only, not obligation
satisfaction, review approval, or knowledge admission.

## 6. Validation evidence

### 6.1 Focused and regression tests

The frozen implementation candidate produced:

```text
tests/unit/contracts/test_typed_terminal_result.py
tests/unit/contracts/test_terminal_validation.py
177 passed

tests/unit/contracts/
488 passed
```

The focused suite covers all 21 allowed outcome/retry/action combinations, all
three context modes, both deadline branches, all four fixed non-authority
constants as present-but-wrong and missing, every retry branch, every real
matrix row through at least one real prohibited edge, all six resource
mappings, mixed exceedance/unobserved priority, Unicode code-point boundaries,
the exact Internet JSON (I-JSON) compatible integer maximum, same-`$id` schema
substitution, global format-checker pollution, hostile/cyclic/deep opaque
values, no ambient I/O, and cross-gate diagnostic ordering.

Python bytecode compilation and tracked/untracked whitespace checks passed.

### 6.2 Dirty-working-tree observations

The primary working tree contains pre-existing modified and untracked user work
outside Checkpoint B. In that working tree:

```text
full pytest: 1001 passed

fast aggregate:
  PASS=9
  FAIL=0
  KNOWN_STALE=1
  EXPECTED_BLOCKED=1
```

The full-suite result is a dirty-working-tree observation, not a clean-checkout
execution result for either Checkpoint B commit. The retained `KNOWN_STALE`
item is the historical Shellworld V1 run. The `EXPECTED_BLOCKED` item says that
the reviewed pytest identity matched but collection did not run with operating-
system-enforced filesystem and network isolation.

### 6.3 Exact pytest identity

The candidate identity was generated twice from the exact implementation commit
`750fa0d091b548cd5d8bcdc26324bc79b2cb79ed`. The two normalized identity files
were byte-identical:

| Evidence | Value |
|---|---|
| Candidate raw bytes | `301947` |
| Candidate raw SHA-256 | `48f7801103d6ae8104dcf0342aed348602a06a18d353764a60e7103bd504a578` |
| Domain-separated identity SHA-256 | `3312943d5766eecef0d3a6670b6473c8df384764ae8d4b49462c2563f870d85e` |
| Full node-set SHA-256 | `aa089080edb923a800b1ad6f9c569d63feb329d304419ff0751cc1b1c509be77` |
| Selected-order SHA-256 | `47617648aafb92ef1b9878e6db7e2da873028fd88b50a86425821ab0cec67252` |
| Collected/selected | `959 / 959` |
| Deselected/skipped | `0 / 0` |
| Marker declarations | `20` |

Review against the previous 782-node baseline found exactly 177 additions and
zero removals or changed old nodes:

| Allowed test file | Added nodes |
|---|---:|
| `tests/unit/contracts/test_terminal_validation.py` | 173 |
| `tests/unit/contracts/test_typed_terminal_result.py` | 4 |

There were no additions outside those two files. Old `node_ids` and
`selected_node_ids` retained their relative order. The collection contract,
schema, evidence scope, three input bindings, 20 marker declarations,
collection skips, and deselection remained unchanged.

After the baseline-only commit, a source-backed check against
`c95c355c8ea1104872a97badc33e80b99bfea326` returned `PASS`, bound the frozen
baseline bytes to the exact Git blob, and reproduced all identities above. Its
assurance tier is `COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC`; filesystem and
network isolation are both explicitly false.

A check against the implementation commit before the baseline commit correctly
reported `PYTEST_INVENTORY_BASELINE_BINDING_MISMATCH`, because that earlier
commit did not contain the new baseline bytes. Candidate generation from that
implementation commit passed; the later source-backed check is the operation
that binds both tests and baseline into one exact commit snapshot.

## 7. Independent review and corrected finding

The adversarial reviewer found one Priority 1 issue during implementation:
when `unobserved_metrics` order and the declared resource relation were both
wrong, the first implementation returned after the order error and suppressed
the independently computable relation error. The implementation now separates
partition-blocking failures from an order-only failure, recomputes the relation
when safe, and returns both diagnostics in a locked order. A dedicated test
prevents regression.

After correction, the final adversarial review reported:

```text
READY
P0=0
P1=0
P2=0
```

The reader review reported `READY`, with zero Priority 0 or Priority 1 issues.
Its first non-blocking expression suggestion was adopted before the
implementation commit by expanding the public function docstring. Its second
suggestion—the standalone-root versus intrinsic-API distinction—is recorded in
Section 3 of this audit. The final reader interpretation remains: the record is
an exception card on an empty slot, not the missing artifact and not an
admission credential.

## 8. Purity, totality, and threat boundary

Production validation performs no filesystem, network, DNS, URL, clock,
timezone, environment, Git, shell, subprocess, database, plugin, or random
access. Every schema and record byte string enters through the explicit
Checkpoint A opaque value and registry boundaries.

Hostile public inputs return diagnostics rather than escaping as attribute,
comparison, recursion, serialization, `jsonschema`, or `referencing`
exceptions. Diagnostic ordering is fixed by gate, subject, JSON Pointer, schema
pointer, code, and canonical machine context.

The same Checkpoint A threat boundary still applies: the in-process registry
seal and private compiled constants defend against ordinary API misuse and
accidental corruption, not arbitrary malicious code already executing in the
same Python interpreter. They are not signatures or authorization evidence.

## 9. Non-authority and remaining milestone state

Checkpoint B does not resolve profile, catalog, plan, scope, basis, target, or
evidence references. It does not establish reviewer independence, scientific
truth, evidence relevance, measurement authenticity, actor authorization,
rights, signatures, release, merge, archive, certification, or per-entry
knowledge admission.

An exact asset reference has no record-type field. Checkpoint B therefore
cannot determine whether referenced asset bytes serialize a terminal record or
the current record. Resolving those bytes and checking their content type is a
later context-closure responsibility.

It also does not make the locked M1 denominator's terminal-result item
`CONTRACTED`. Exact catalog and profile assets, registered outcomes/reasons,
normative vectors, and context closure are still absent. M0, M1, the arbitrary-
arXiv pipeline, Paper Agent DAG, mathematical formalization chain, standard
reviewed database, and web demo all remain incomplete.

The next authorized step is Checkpoint C design: exact raw-byte-addressed
artifact-family catalog and agentization profile assets with one-way bootstrap
validation. That design must preserve the denominator and cannot reinterpret a
Checkpoint B intrinsic pass as satisfaction or admission.
