# AgtXIv V2 M1 contract kernel — Checkpoint B: typed terminal result

- Document status: implementation plan; not implementation evidence
- Document version: 1.0
- Checkpoint status: proposed and intentionally incomplete
- Committed basis: `10cdcf1566d344cb0498961195a4b87b0b563bb8`
- Parent design: `docs/roadmaps/v2-m1-contract-kernel-slice-1.md`
- Predecessor: `docs/roadmaps/v2-m1-contract-kernel-checkpoint-a.md`
- Date: 2026-08-31
- Authority: none for obligation satisfaction, merge, release, archive,
  certification, or knowledge admission

Checkpoint B adds the first concrete record family on top of the offline schema
registry built in Checkpoint A. It records why one expected artifact was not
successfully produced in one attempt, which exact evidence supports that
operational disposition, and what must change before another attempt.

It does not add an artifact catalog, agentization profile, plan, frozen scope,
contract bundle, release workflow, demo, or database admission rule. Those
dependencies remain later checkpoints. Nothing in this plan adopts the modified
or untracked flat V2 schemas, fixtures, validator, specification, demos, or
database prototype in the working tree.

## 1. Intuition: an exception card on an empty delivery slot

`TypedTerminalResult` is an exception card attached to an empty delivery slot.
The card says which previously declared obligation was being attempted, which
attempt stopped, why it stopped, which evidence already exists, what resources
were observed, and who owns the next action.

The card is not the missing delivery. It cannot cite itself as evidence, cannot
create a second exception card as its target, and cannot say that the obligation
was satisfied. In particular:

- `terminal_for_attempt = true` means only that this attempt has ended;
- `terminal_scope = ATTEMPT_ONLY` forbids a permanent interpretation;
- `successful_artifact_produced = false` says the expected successful artifact
  is absent; and
- `satisfaction_claim = NONE` leaves accounting policy to a later catalog and
  profile validator.

This distinction supplies the physical picture for fail-closed accounting. A
missing artifact remains visibly missing, but its slot does not disappear from
the denominator merely because production failed.

## 2. Terms and boundaries

- **Intrinsic conformance:** the terminal record has the exact family schema,
  canonical hash, closed payload shape, and internally consistent declarations
  defined here.
- **Context closure:** every profile, catalog, plan, scope, target, and evidence
  reference resolves to the right object under one exact contract chain.
- **Basis reference:** an exact reference declared as the source of an
  obligation identity. In Checkpoint B, its shape and same-record fields can be
  checked; its existence, pointer target, and semantic relevance cannot.
- **Operational outcome:** a statement about one execution attempt, not about
  scientific truth or permanent applicability.
- **Declared reason code:** a bounded machine-shaped code supplied by the
  producer. It is not a registered stable error until a later exact error
  catalog accepts it.
- **Observed resource:** a caller-declared measurement. Checkpoint B can compare
  the declared number with the declared limit but cannot prove that a monitor
  measured it faithfully.

An empty diagnostic tuple from the Checkpoint B API means only **intrinsic
conformance**. Public documentation and API names must never shorten this to
“verified,” “satisfied,” “approved,” or “admitted.”

## 3. Exact family identity

The schema identity is exactly:

```text
https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0
```

The record type is exactly:

```text
agtxiv.typed-terminal-result/1.0.0
```

Its exact asset label is:

```text
asset_id    schema:typed-terminal-result:1.0.0
media_type  application/schema+json
schema_uri  https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0
```

After the schema file is frozen, the implementation mechanically computes its
raw byte size and lowercase `sha256:<64 hex>` digest and records all five exact
asset-ref fields as private constants in `terminal_validation.py`. A focused
test reads the schema only as test setup, recomputes the raw size and digest,
and requires those constants to match. Production validation performs no file
read.

The terminal envelope `schema_ref` must contain those five authoritative keys;
the common type may additionally carry `path_hint`. Every Checkpoint B identity,
equality, self-reference, and deduplication comparison uses an authoritative
projection that recursively removes `path_hint` from asset refs, including a
record/component ref's nested `schema_ref`. It retains every other field,
including `schema_uri`. The record content hash still commits any supplied path
hint, but a locator-only difference cannot change which schema, context, basis,
or evidence target the validator believes was named.

The schema is a raw exact asset. It references only already committed common
schemas and has no reverse reference to a catalog, profile, bundle, fixture, or
runtime record. The reference direction is therefore one-way and cannot create
a bootstrap hash cycle.

The family schema exposes the two Checkpoint A entry points:

```text
#/$defs/recordType/const = agtxiv.typed-terminal-result/1.0.0
#/$defs/payload          = the closed payload schema
```

It also describes the complete immutable record at its root. The root requires
exactly `envelope`, `payload`, and `content_hash`; binds `envelope` to the common
`contractBoundEnvelope` plus the terminal record-type constant and an explicit
`producer_context` requirement; binds `payload` to `#/$defs/payload`; and binds
`content_hash` to the common digest schema. This makes the asset usable as an
ordinary standalone family schema as well as through the Checkpoint A generic
entry points.

The intrinsic validator requires the authoritative projection of envelope
`schema_ref` to equal the full compiled exact asset reference, not merely its
`$id`. Checkpoint A then proves that the registry contains those exact raw
bytes. A different schema with the same `$id` or record-type string is rejected
as a swapped ruler.

## 4. Closed payload

The payload is an object with no undeclared properties. It requires exactly the
following conceptual fields:

```text
terminal_for_attempt
terminal_scope
successful_artifact_produced
satisfaction_claim
attempt_id
binding_context
target_obligation
outcome
declared_reason
evidence
retry
next_action
resources
```

The first four values are fixed:

```text
terminal_for_attempt              true
terminal_scope                    ATTEMPT_ONLY
successful_artifact_produced      false
satisfaction_claim                NONE
```

No `success`, `permanent`, `verified`, `approved`, `released`, `admitted`, or
equivalent field is allowed.

Every nested object also has `additionalProperties: false`. The normative key
and discriminator spellings are locked by this minimal skeleton. Empty object
placeholders stand for referenced shapes defined below, so this is a spelling
oracle rather than a valid positive fixture:

```json
{
  "terminal_for_attempt": true,
  "terminal_scope": "ATTEMPT_ONLY",
  "successful_artifact_produced": false,
  "satisfaction_claim": "NONE",
  "attempt_id": "attempt:example-1",
  "binding_context": {
    "context_mode": "PROFILE_BOUND",
    "profile_ref": {},
    "catalog_ref": {}
  },
  "target_obligation": {
    "obligation_key": "obligation:example-1",
    "stage_id": "EXAMPLE_STAGE",
    "family_id": "EXAMPLE_FAMILY",
    "basis": {
      "basis_kind": "ASSET",
      "asset_ref": {}
    }
  },
  "outcome": "RETRY_REQUIRED",
  "declared_reason": {
    "declared_reason_code": "AGTXIV.TERMINAL.EXAMPLE",
    "summary": "Bounded non-blank explanation"
  },
  "evidence": [
    {
      "evidence_id": "evidence:example-1",
      "evidence_role": "TOOL_DIAGNOSTIC",
      "evidence_kind": "ASSET",
      "asset_ref": {}
    }
  ],
  "retry": {
    "retry_disposition": "RETRY_AFTER_CONDITION",
    "retry_condition": "Bounded non-blank condition"
  },
  "next_action": {
    "action_code": "RETRY",
    "description": "Bounded non-blank action",
    "responsible_actor": {},
    "responsible_role": "TERMINAL_ACTION_OWNER",
    "deadline": {
      "deadline_kind": "NO_DEADLINE",
      "no_deadline_reason": "Bounded non-blank reason"
    }
  },
  "resources": {
    "limit": {},
    "observed": {},
    "unobserved_metrics": [],
    "relation": "INDETERMINATE"
  }
}
```

The closed tagged branches use these exact fields and literals:

| Object | Tag field and literal | Other required field | Fields forbidden in that branch |
|---|---|---|---|
| context | `context_mode: PROFILE_BOUND` | `profile_ref`, `catalog_ref` | `plan_ref`, `scope_ref` |
| context | `context_mode: PLAN_BOUND` | `profile_ref`, `catalog_ref`, `plan_ref` | `scope_ref` |
| context | `context_mode: FROZEN_SCOPE_BOUND` | `profile_ref`, `catalog_ref`, `plan_ref`, `scope_ref` | none |
| basis | `basis_kind: ASSET` | `asset_ref` | `record_ref`, `component_ref` |
| basis | `basis_kind: RECORD` | `record_ref` | `asset_ref`, `component_ref` |
| basis | `basis_kind: COMPONENT` | `component_ref` | `asset_ref`, `record_ref` |
| evidence | `evidence_kind: ASSET` | `evidence_id`, `evidence_role`, `asset_ref` | `record_ref`, `component_ref` |
| evidence | `evidence_kind: RECORD` | `evidence_id`, `evidence_role`, `record_ref` | `asset_ref`, `component_ref` |
| evidence | `evidence_kind: COMPONENT` | `evidence_id`, `evidence_role`, `component_ref` | `asset_ref`, `record_ref` |
| retry | `retry_disposition: RETRY_AFTER_CONDITION` | `retry_condition` | `context_change_required`, `review_condition` |
| retry | `retry_disposition: NO_RETRY_IN_CURRENT_CONTEXT` | `context_change_required` | `retry_condition`, `review_condition` |
| retry | `retry_disposition: REVIEW_DECIDES` | `review_condition` | `retry_condition`, `context_change_required` |
| deadline | `deadline_kind: NO_DEADLINE` | `no_deadline_reason` | `deadline_at` |
| deadline | `deadline_kind: FIXED_DEADLINE` | `deadline_at` | `no_deadline_reason` |

### 4.1 One producer context and one attempt identity

The immutable envelope must contain `producer_context`. That common object is
the sole producer identity, role, implementation, and environment source. The
payload contains only `attempt_id`, and the intrinsic validator requires it to
equal `envelope.producer_context.attempt_id` literally.

Version 1 therefore permits only the producer of the stopped attempt to emit
its terminal result. A supervisor, reviewer, or monitor recording a result on
someone else's behalf requires a future schema version with separate recorder
and attempt contexts; it must not overload this field.

### 4.2 Binding context is a tagged union, not optional soup

`binding_context` is exactly one of three disjoint modes. Every branch has
`additionalProperties: false` and explicitly requires or forbids its fields.

| Mode | Required exact references | Forbidden references |
|---|---|---|
| `PROFILE_BOUND` | `profile_ref`, `catalog_ref` | `plan_ref`, `scope_ref` |
| `PLAN_BOUND` | `profile_ref`, `catalog_ref`, `plan_ref` | `scope_ref` |
| `FROZEN_SCOPE_BOUND` | `profile_ref`, `catalog_ref`, `plan_ref`, `scope_ref` | none |

`profile_ref` and `catalog_ref` are exact asset references because those
bootstrap assets must not point back to a future containing bundle. `plan_ref`
and `scope_ref` are exact record references whose record types are fixed to
`agtxiv.agentization-plan/1.0.0` and
`agtxiv.frozen-inventory-scope/1.0.0`, respectively.

The contract bundle reference appears only in the common envelope. Repeating it
inside the payload would create two possible sources of truth.

The mode name is a declared structural state, not proof that the referenced
objects exist or that the mode is legal for the declared stage. Checkpoints C
and D resolve those references and enforce the minimum mode for each catalog
family and pipeline stage.

### 4.3 Target an obligation, never a missing artifact

`target_obligation` contains:

- `obligation_key`: a stable namespaced identity;
- `stage_id`: a bounded uppercase stage label;
- `family_id`: a bounded uppercase artifact-family label; and
- `basis`: a tagged exact asset, record, or component reference.

The basis wrapper uses exactly `basis_kind` plus one corresponding field:
`asset_ref`, `record_ref`, or `component_ref`. Every branch forbids the other
two reference fields.

There is deliberately no `target_artifact_ref`: the successful artifact does
not exist. The basis identifies the declared source of the obligation, not its
missing output.

For `PLAN_BOUND`, the basis must be an exact component reference whose exact
record-ref projection equals `plan_ref`. For `FROZEN_SCOPE_BOUND`, it must be an
exact component reference whose record-ref projection equals `scope_ref`.
`PROFILE_BOUND` may use an exact asset, record, or component basis.

These comparisons prove only literal field equality inside the submitted
record. They do not prove that a component pointer resolves or denotes a real
obligation. That is a Checkpoint C/D closure rule.

The exact `family_id` values `TYPED_STAGE_FAMILY_TERMINAL_RESULT` and the
reserved short alias `TYPED_TERMINAL_RESULT` are forbidden. The terminal record
type is forbidden in a record/component basis. A terminal result is not itself
an artifact-family obligation.

### 4.4 Operational outcomes only

Version 1 admits exactly five outcomes:

```text
UNAVAILABLE
RETRY_REQUIRED
REVIEW_REQUIRED
BLOCKED
FAILED
```

The following are deliberately excluded:

- `NOT_APPLICABLE`, because applicability belongs to the exact catalog and
  profile;
- `UNSUPPORTED`, because only the exact catalog can decide whether that is an
  allowed disposition for a non-core family; and
- `REFUTED`, because scientific refutation is an assessment conclusion, not an
  execution-terminal outcome.

`declared_reason` contains `declared_reason_code` and a nonempty bounded
`summary`. The code uses one exact uppercase dotted-code grammar and length
bound. Checkpoint B validates only that grammar. Registration, meaning,
family/outcome compatibility, and stability require the future exact error
catalog.

### 4.5 Evidence is nonempty, exact, ordered, and non-recursive

`evidence` is a nonempty array of closed wrapper objects. Each wrapper contains:

- a stable `evidence_id`;
- one closed evidence role;
- a discriminator `ASSET`, `RECORD`, or `COMPONENT`; and
- exactly one corresponding exact reference.

The wrapper uses exactly `evidence_kind` plus one corresponding field:
`asset_ref`, `record_ref`, or `component_ref`. The allowed role literals are
exactly `INPUT_STATE`, `TOOL_DIAGNOSTIC`, `RESOURCE_OBSERVATION`,
`POLICY_OBSERVATION`, and `REVIEW_REQUEST`.

Evidence entries are strictly ordered by the UTF-8 bytes of `evidence_id`; IDs
are unique, and the canonical bytes of the underlying authoritative reference
projections are also unique. Thus two evidence refs that differ only by a
`path_hint`, including one nested in `schema_ref`, are duplicates. The order is
checked after canonical string normalization and never uses list insertion
order as a tie-breaker.

Any syntactically identifiable terminal record or terminal component reference
is forbidden. A reference to the current terminal record is also forbidden by
exact record type, ID, and revision comparison. This v1 rule intentionally
forbids terminal-to-terminal evidence chains. If a later design needs failure
propagation, it requires a new schema version and whole-graph cycle validation.

An exact asset reference has no record type. Checkpoint B therefore cannot
prove that arbitrary asset bytes are not a serialized terminal record, nor that
any evidence exists or is relevant. Later closure performs content resolution
and type checking; Checkpoint B must not describe exact-reference shape as
resolved evidence.

### 4.6 Retry has no hidden permanent state

`retry` is exactly one of three tagged branches:

| Disposition | Required explanation |
|---|---|
| `RETRY_AFTER_CONDITION` | nonempty `retry_condition` |
| `NO_RETRY_IN_CURRENT_CONTEXT` | nonempty `context_change_required` |
| `REVIEW_DECIDES` | nonempty `review_condition` |

No `NEVER`, `PERMANENT`, or unqualified `retryable: false` value is admitted.
Every branch says what must be true before a new attempt can be considered.

### 4.7 Next action and outcome compatibility

`next_action` requires a closed action code, bounded description, responsible
actor identity, responsible role label, and deadline branch. A role label is
not authorization.

The allowed compatibility matrix is:

| Outcome | Retry disposition | Next-action codes |
|---|---|---|
| `UNAVAILABLE` | `RETRY_AFTER_CONDITION` or `NO_RETRY_IN_CURRENT_CONTEXT` | `PROVIDE_INPUT`, `RESOLVE_DEPENDENCY` |
| `RETRY_REQUIRED` | `RETRY_AFTER_CONDITION` | `RETRY` |
| `REVIEW_REQUIRED` | `REVIEW_DECIDES` | `MANUAL_REVIEW` |
| `BLOCKED` | `RETRY_AFTER_CONDITION` or `NO_RETRY_IN_CURRENT_CONTEXT` | `RESOLVE_DEPENDENCY`, `RESOLVE_POLICY`, `ESCALATE` |
| `FAILED` | any of the three dispositions | `FIX_IMPLEMENTATION`, `MANUAL_REVIEW`, `ESCALATE` |

The schema locks the closed vocabularies. The intrinsic validator enforces the
cross-field matrix with deterministic pointers.

The deadline is a disjoint tagged union:

- `NO_DEADLINE` requires a nonempty `no_deadline_reason` and forbids a
  timestamp; or
- `FIXED_DEADLINE` requires one strict UTC RFC 3339 `deadline_at` timestamp and
  forbids a no-deadline reason.

Checkpoint B performs no clock read and never labels the deadline overdue.

### 4.8 Resource observations preserve missing measurements

`resources` contains:

- `limit`, validated by the committed common `ResourceBudget` schema;
- `observed`, a closed object of nonnegative measured values;
- `unobserved_metrics`, an ordered unique array of metric names; and
- `relation`, one of the three values below.

The metric mapping is fixed:

| Limit key | Observation key |
|---|---|
| `max_wall_time_ms` | `wall_time_ms` |
| `max_cpu_time_ms` | `cpu_time_ms` |
| `max_peak_memory_bytes` | `peak_memory_bytes` |
| `max_input_bytes` | `input_bytes` |
| `max_output_bytes` | `output_bytes` |
| `max_network_requests` | `network_requests` |

Every limit dimension must occur exactly once in either `observed` or
`unobserved_metrics`. Neither collection may name a dimension absent from the
limit, and the two collections may not overlap. This prevents a missing
measurement from silently becoming zero.

Both `observed` and `unobserved_metrics` use the observation-key literals in the
right column of the table, never the `max_*` limit keys. The array is sorted by
the fixed table order shown above: wall time, CPU time, peak memory, input
bytes, output bytes, then network requests. An empty array is allowed only when
every limited metric is observed.

The intrinsic validator recomputes `relation` mechanically:

1. any observed value greater than its declared limit gives
   `EXCEEDED_OBSERVED_LIMIT`;
2. otherwise any unobserved limited metric gives `INDETERMINATE`;
3. otherwise the result is `WITHIN_OBSERVED_LIMITS`.

This is a relation between submitted values, not evidence that a measurement is
true and not proof that resource use caused the terminal outcome.

### 4.9 Locked lexical profiles

Checkpoint B does not leave identifier or prose bounds to implementation
judgment. The schema reuses these exact profiles:

| Use | Exact constraint |
|---|---|
| `attempt_id`, `obligation_key`, `evidence_id` | length 3–512 and `^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:/-]*(?![\\s\\S])` |
| `stage_id`, `family_id`, responsible role | length 1–128 and `^[A-Z][A-Z0-9_]*(?![\\s\\S])` |
| `declared_reason_code` | length 10–256 and `^AGTXIV\\.[A-Z][A-Z0-9_]*(?:\\.[A-Z][A-Z0-9_]*)+(?![\\s\\S])` |
| summary, retry condition, context change, review condition, action description, no-deadline reason | length 1–2048 and pattern `[^\\s]` so at least one non-whitespace character exists |
| fixed deadline | `format: date-time` plus `^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]{1,9})?Z(?![\\s\\S])` |

Lengths are Unicode-code-point lengths after the committed canonical profile's
normalization. Exact enumerations in Sections 4.4 through 4.8 are literals, not
values accepted merely by the uppercase-label pattern.

## 5. Public API and validation gates

Checkpoint B adds one deliberately explicit API:

```python
validate_typed_terminal_result_intrinsic(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]
```

The name retains `intrinsic` so callers cannot mistake it for future context or
catalog closure.

Validation uses these hard dependency gates:

1. **Safe outer preflight:** check exact public runtime types, registry
   integrity, opaque record integrity, the three-key outer record shape, and
   only enough envelope/schema-ref shape to read the exact binding. Unsafe
   outer input returns existing Checkpoint A input/envelope diagnostics and no
   terminal interpretation.
2. **Official-ruler gate:** require the authoritative schema-ref projection to
   equal the five compiled official fields and require `producer_context` to be
   present. An optional `path_hint` is ignored only by this identity comparison.
   The two independent failures may both be reported, but any failure returns
   immediately.
3. **Checkpoint A generic validation:** only after gate 2 pins the official raw
   schema bytes, validate the immutable envelope, exact registered schema and
   record type, closed payload, and content hash. Any failure returns before
   terminal cross-field interpretation.
4. bind the payload attempt to the envelope attempt and check the tagged context
   plus basis equality rules;
5. reject terminal targets, terminal/self evidence, duplicate or unordered
   evidence;
6. enforce outcome/retry/action/deadline compatibility; and
7. check the resource partition and recomputed relation.

Gates 1 through 3 are hard prerequisites. In particular, a same-`$id` schema
with different bytes cannot make a lax payload safe: it fails gate 2 and gates
3–7 are not run. After gate 3 succeeds, independent terminal problems are
collected in the fixed gate and field order above. Loops use fixed metric order
or already validated canonical ordering, so no host dictionary or set
iteration order becomes observable.

All public input failures return diagnostics. No untrusted input may escape as a
`jsonschema`, `referencing`, attribute, comparison, recursion, or serialization
exception.

## 6. Stable diagnostics added

The implementation may add only these meanings:

| Code | Stable meaning |
|---|---|
| `AGTXIV.TERMINAL.SCHEMA_MISMATCH` | The envelope schema ref differs from any compiled exact official terminal schema field |
| `AGTXIV.TERMINAL.ATTEMPT_MISMATCH` | Payload and envelope do not name the same attempt or producer context is absent |
| `AGTXIV.TERMINAL.CONTEXT_INVALID` | A context mode or basis-to-plan/scope field binding is inconsistent |
| `AGTXIV.TERMINAL.TARGET_INVALID` | The target describes an output artifact or terminal family instead of an obligation basis |
| `AGTXIV.TERMINAL.EVIDENCE_INVALID` | Evidence is empty, unordered, duplicated, self-referential, or terminal-typed |
| `AGTXIV.TERMINAL.DISPOSITION_INVALID` | Outcome, retry, action, or deadline fields contradict the closed matrix |
| `AGTXIV.TERMINAL.RESOURCE_INVALID` | Resource dimensions or the declared relation disagree with the mechanical rule |

Ordinary JSON Schema shape failures continue to use
`AGTXIV.RECORD.PAYLOAD_INVALID`. Existing Checkpoint A codes retain their
meaning. English messages may improve; codes and exact JSON Pointers remain the
machine interface.

## 7. Exact implementation allowlist

After this plan is committed and reviewed, the Checkpoint B implementation
commit may change only:

```text
schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json  (new)
src/agtxiv_v2/contracts/terminal_validation.py                              (new)
src/agtxiv_v2/contracts/diagnostics.py                                      (modify)
src/agtxiv_v2/contracts/__init__.py                                         (modify)
tests/unit/contracts/test_typed_terminal_result.py                          (new)
tests/unit/contracts/test_terminal_validation.py                            (new)
```

The implementation must not modify Checkpoint A's registry or generic schema
validator. It must not add or adopt a catalog, profile, error catalog, plan,
scope, bundle, normative fixture, command-line tool, aggregate validator, demo,
or database file. Focused tests construct explicitly labelled synthetic
structural records in memory; those values are test evidence, not bundle assets
or resolved runtime context.

Staging uses this exact list. `git diff --cached --name-only` must equal the
intended subset before commit.

## 8. Pure deterministic boundary

Production code performs no filesystem, network, DNS, URL, clock, timezone,
environment, Git, shell, subprocess, database, plugin, or random access. Every
schema byte string and record enters explicitly through the Checkpoint A opaque
canonical-value and registry boundaries.

With the same implementation bytes, dependency lock, registry, and record, the
ordered diagnostic serialization is byte-identical. Across later compatible
versions, the diagnostic code meaning, phase, subject, instance pointer, schema
pointer, and byte offset remain stable; human messages and optional detail may
improve.

No module-global mutable registry, machine-local format registration, input
path, input ordinal, or wall-clock state may affect the result.

## 9. Required tests

### 9.1 Positive cases

Tests must cover:

- the terminal schema plus all eight common schemas forming one offline,
  acyclic Checkpoint A registry;
- the schema file's raw byte size and SHA-256 matching the compiled exact-ref
  constants;
- direct standalone validation through the family-schema root, including exact
  envelope, payload, and content-hash fields, and agreement with the generic
  `#/$defs/payload` entry-point result;
- one valid immutable terminal record for each of the three context modes;
- all five outcomes through every allowed retry/action combination;
- both deadline branches;
- all-observed, partly unobserved, and exceeded resource examples; and
- schema, context, and PLAN/FROZEN basis refs whose authoritative fields match
  while a top-level or nested `path_hint` differs, proving identity equality
  ignores the hint even though the terminal record content hash still commits
  that submitted metadata; and
- repeated construction and validation with byte-identical results.

### 9.2 Priority 0 rejection cases

Tests must reject:

- a swapped terminal schema, including different raw bytes with the same `$id`,
  reused record type under another schema, invalid record hash, wrong record
  type, or missing producer context at both standalone-schema and intrinsic-API
  boundaries;
- an extra family-root field or any mismatch between root validation and the
  generic payload entry point;
- false/missing attempt binding or any fixed boundary constant changed;
- a context branch with a missing, extra, or independently optional reference;
- PLAN/FROZEN basis fields that do not equal the declared plan/scope record;
- a target artifact reference, terminal target family, terminal record basis,
  or direct self-reference;
- empty evidence, duplicate evidence IDs, duplicate underlying refs, unordered
  evidence, and any terminal record/component evidence;
- two evidence entries whose refs differ only by a top-level or nested
  `path_hint`, proving authoritative-reference uniqueness rejects them as a
  duplicate target;
- every excluded or unknown outcome and every forbidden permanent/satisfaction
  field;
- malformed reason codes, retry branches without their required condition,
  outcome/retry/action conflicts, and malformed deadline unions;
- every one-code-point-below/at/above lexical length boundary, including
  multi-byte Unicode cases, and every literal outside the locked evidence-role,
  family, outcome, retry, action, deadline, and resource vocabularies;
- missing, overlapping, extra, or unordered resource dimensions and every
  incorrect relation value; and
- treating an intrinsic pass as obligation satisfaction, review approval,
  release, archive, certification, or knowledge admission.

### 9.3 Priority 1 determinism and totality cases

Tests must cover:

- record object insertion-order and evidence construction-order permutations;
- stable diagnostic ordering for multiple independent terminal failures;
- malformed, forged, cyclic, or excessively deep opaque record/registry
  values returning diagnostics rather than exceptions;
- very long bounded strings, maximum Internet JSON (I-JSON) compatible resource
  values, and hostile Unicode at every public string seam;
- filesystem, socket/name resolution, URL, subprocess, Git, environment,
  random, and time sentinels; and
- a test proving that Checkpoint B does not resolve catalog/profile/plan/scope
  or evidence refs and therefore does not claim context closure.

## 10. What B proves and what it defers

Checkpoint B can prove only:

- the exact terminal schema bytes and record type were used;
- the envelope, closed payload, and canonical content hash agree;
- one complete context shape was declared;
- the attempt-local target, evidence, retry, action, deadline, and resource
  fields satisfy the mechanical rules in this plan; and
- the record makes no success, satisfaction, or permanent-scientific claim.

Checkpoint C or D must still prove:

- profile, catalog, plan, scope, basis, target, and evidence refs exist and
  resolve with the required type and pointer;
- the family, stage, obligation, outcome, and reason are registered and allowed;
- the context mode is sufficient for that stage;
- the target belongs to the exact plan/scope and contract chain;
- the declared resource limit equals the applicable Plan/profile budget;
- the evidence is relevant, the measurements are authentic, and the actor is
  authorized;
- a catalog policy permits the terminal result to count as an accounted
  disposition; and
- no successful artifact conflicts with this terminal result.

Scientific assessment, reviewer independence, signatures, rights, release,
archive, merge, and per-entry knowledge admission remain still later policies.
Checkpoint B alone also does not make the locked M1 denominator's terminal item
`CONTRACTED`: catalog/error-policy binding, normative vectors, and context
closure are still absent.

## 11. Versioned commit sequence

Checkpoint B uses separate review surfaces:

1. **Plan-only commit:** this document.
2. **Implementation commit:** exactly the six-file allowlist in Section 7.
3. **Baseline-only commit:** update only the reviewed pytest test-identity
   baseline from the exact implementation commit.
4. **Audit-only commit:** record exact commits, commands, counts, hashes,
   diagnostic set, reviews, known limitations, and remaining blockers.

No implementation commit may silently include a baseline or audit update. No
baseline commit may rewrite a test.

## 12. Definition of Done

Checkpoint B is complete only when:

1. the plan is committed before implementation;
2. the implementation diff is an exact subset of the six-path allowlist;
3. the schema registry containing the common and terminal schemas is exact,
   offline, immutable, and acyclic;
4. the validator's compiled schema exact-ref constants match the committed raw
   schema bytes, and same-`$id` substituted bytes fail closed;
5. valid results exist for all three context modes without claiming reference
   resolution;
6. every fixed non-authority constant, outcome, evidence, retry, deadline,
   target, and resource invariant has positive and adversarial coverage;
7. all input failures are deterministic diagnostics and production code
   performs none of the forbidden I/O or ambient-state operations;
8. focused tests, all contract tests, the full working-tree suite, and fast
   repository validation introduce no new failure, with dirty-tree and OS
   isolation evidence boundaries reported separately;
9. independent adversarial review reports zero open Priority 0 or Priority 1
   findings;
10. a reader review confirms that “intrinsic conformance” cannot be mistaken for
   artifact production or obligation satisfaction;
11. the exact implementation test identity is generated twice with
    byte-identical results and reviewed against the old baseline: only nodes
    from the two allowed Checkpoint B test files may be added, with zero removed
    or changed old nodes and no marker, input-binding, evidence-scope, or
    collection-contract drift; the baseline-only commit changes only that
    baseline; and
12. an audit-only commit records all evidence and preserves M0/M1/V2 as
    incomplete.

Completion authorizes only Checkpoint C design. It grants no merge, release,
archive, certification, or admission authority.

## 13. Known evolution boundaries

Three non-blocking version boundaries are explicit:

1. supervisor or monitor recording on behalf of another attempt needs separate
   recorder and attempt contexts in a future family version;
2. allowing terminal results as evidence for propagated failures needs a future
   family version plus whole-graph cycle and provenance validation; and
3. interpreting a declared basis/evidence reference as existing or relevant
   requires later context closure, not a reinterpretation of Checkpoint B.

## 14. Next checkpoint

Checkpoint C adds raw-byte-addressed artifact-family catalog and agentization
profile assets, their schemas, and cross-validation. It locks which families,
stages, outcomes, reasons, context modes, and terminal dispositions are allowed
without letting a producer shrink the denominator. It remains one-way bootstrap
data and still does not create a production-authorized contract bundle.
