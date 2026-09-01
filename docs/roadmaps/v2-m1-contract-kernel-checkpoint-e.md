# AgtXIv V2 M1 contract kernel — Checkpoint E: query-independent planning and frozen inventory scope

- Document status: plan only; not implementation or audit evidence
- Document version: 1.0
- Checkpoint status: proposed and intentionally incomplete
- Committed basis: `e774125bd8bb6dbf809914cb044b5ada0cf244dd`
- Predecessor: `docs/roadmaps/v2-m1-contract-kernel-checkpoint-d.md`
- Predecessor audit: `docs/audits/v2-m1-contract-kernel-checkpoint-d-2026-09-01.md`
- Governing ADR: `docs/adr/0003-plan-discovery-scope-freeze.md`
- Date: 2026-09-01
- Authority: none for acquisition, runtime execution, merge, release, archive,
  certification, database admission, or knowledge admission

Checkpoint E freezes the first dependency-complete planning denominator:

```text
supplied source bytes
  -> PaperSourceSnapshot
  -> query-independent AgentizationPlan
  -> total-accounted InventoryDiscoveryResult
  -> independent ScopeFreezeDecision
  -> FrozenInventoryScope
```

It also creates one real, non-production `ContractBundleRelease` immutable-record
candidate so every later candidate record envelope can resolve its exact
contract-bundle record reference. “Real” means canonical record bytes, a normal
record-hash projection, complete exact references, and passing pure validation;
it does not mean released, signed, selected by a runtime, or production-authoritative.

Checkpoint E preserves **M1: NOT COMPLETE**, **M1.5: NOT COMPLETE**, and
**AgtXIv V2: NOT COMPLETE**. It proves no arXiv acquisition, CAS, runner, API,
SQLite or other database, demo, release, archive, certification, or knowledge
admission. It does not fetch, unpack, compile, analyze, persist, publish, sign,
or admit a paper. The tracked real-paper case is local deterministic planning
evidence only.

## 1. Terms, authority, and dependency graph

- **Source unit** is one caller-supplied regular-file byte string with one
  already-canonical relative path. E does not discover it on a filesystem.
- **Source snapshot** is a closed ordered table of all supplied source units and
  a domain-separated tree root. It is not an acquisition or archive receipt.
- **Plan** freezes the snapshot, exact contract/configuration inputs, expected
  source-unit denominator, profile obligations, and admission limits before
  discovery. It contains no query or query-derived selector.
- **Discovery** is a producer claim whose three component partitions and
  obligation dispositions are mechanically total and reconciled. It is not
  authority to freeze scope.
- **Freeze decision** is an independent ACCEPT or BLOCK review of one exact
  discovery. Structural inequality and declared conflicts are checkable;
  real-world identity, conflict-of-interest truth, and signature validity are not.
- **Frozen scope** exists only after ACCEPT and is the immutable denominator for
  later accounting. Ambiguous and unclassified entries remain in it.
- **Revision impact** is a pure transitive affected-set calculation over supplied
  old/new scopes and supplied downstream lineage. It does not mutate or revoke
  old records.
- **Candidate** means non-production contract data. No `latest` selector exists.
- **Discovery obligation policy** is a raw, exact-bound support contract that
  projects the richer discovery denominator which C Profile 1.0 cannot express.
  It is not a Catalog family and does not mutate the C Profile schema.

The exact acyclic authority graph is:

```text
common/B/C/D schema bytes + E schema bytes + canonicalization/validator/vector bytes
  -> E StableCodeCatalog 1.1 candidate
  -> E ArtifactFamilyCatalog candidate
  -> E AgentizationProfileRelease candidate
  -> final DiscoveryObligationPolicy candidate
  -> final E KernelValidationPolicy 1.1 candidate
  -> ContractBundleRelease candidate
  -> candidate PaperSourceSnapshot
  -> candidate AgentizationPlan
  -> candidate InventoryDiscoveryResult
  -> candidate ScopeFreezeDecision
  -> candidate FrozenInventoryScope (ACCEPT branch only)
```

The bundle candidate binds contract assets but not fixture records or source
bytes. Candidate record envelopes point one way to the already-built bundle.
This ordering prevents a bundle/record hash cycle.

## 2. Exact family identities and registry boundary

E adds these closed Draft 2020-12 families and exact schema identities:

| Family | schema URI | schema path |
|---|---|---|
| `agtxiv.contract-bundle-release/1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/contract/contract-bundle-release/1.0.0` | `schemas/v2/contract-kernel/contract/contract-bundle-release/1.0.0.schema.json` |
| `agtxiv.paper-source-snapshot/1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/source/paper-source-snapshot/1.0.0` | `schemas/v2/contract-kernel/source/paper-source-snapshot/1.0.0.schema.json` |
| `agtxiv.agentization-plan/1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0` | `schemas/v2/contract-kernel/planning/agentization-plan/1.0.0.schema.json` |
| `agtxiv.inventory-discovery-result/1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0` | `schemas/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0.schema.json` |
| `agtxiv.scope-freeze-decision/1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/review/scope-freeze-decision/1.0.0` | `schemas/v2/contract-kernel/review/scope-freeze-decision/1.0.0.schema.json` |
| `agtxiv.frozen-inventory-scope/1.0.0` | `https://agtxiv.org/schema/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0` | `schemas/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0.schema.json` |

The five post-bootstrap record families use the existing
`immutable-record-envelope/1.0.0#/$defs/contractBoundEnvelope`. Their envelopes
exact-bind the record schema and E bundle candidate. E does not fork or weaken
the envelope.

`ContractBundleRelease` is also an immutable record, but uses the existing
`immutable-record-envelope/1.0.0#/$defs/baseEnvelope` bootstrap branch exactly as
that schema requires. Its envelope has `record_type =
agtxiv.contract-bundle-release/1.0.0`, full `schema_ref`, `record_id`,
`record_revision`, and `created_at`, and has no `contract_bundle_ref`. The record
root is the normal closed `envelope`, `payload`, `content_hash` shape. Its
`content_hash` is computed by the existing canonical record-hash projection over
the complete record excluding only `content_hash`; it is not the asset-manifest
hash. This gives later envelopes a resolvable exact-record ref containing
`record_id`, `record_revision`, `record_type`, `content_hash`, and `schema_ref`.
The bootstrap branch avoids self-reference without making the bundle a
standalone non-record. It has no signature, production release status,
runtime-selection flag, or production authority.

For every E family, payload/envelope identity is mechanically projected; no
schema leaves two authorities:

| family | payload/envelope equality | envelope producer |
|---|---|---|
| bundle | `bundle_id = record_id`; candidate version and revision 1 | forbidden by E bootstrap profile |
| snapshot | `snapshot_id = record_id`; `snapshot_version = record_revision = 1` | `SOURCE_SNAPSHOT_BUILDER` |
| Plan | `plan_id = record_id`; `plan_revision = record_revision = 1` | `PLANNING_PRODUCER` |
| Discovery | `discovery_id = record_id`; `discovery_revision = record_revision = 1`; payload producer context byte-equals envelope producer context | `DISCOVERY_PRODUCER` |
| Decision | `decision_id = record_id`; `decision_revision = record_revision = 1`; payload reviewer actor/role equals envelope producer actor/role | `SCOPE_FREEZE_REVIEWER` |
| Scope | logical `scope_id` differs as specified; `scope_revision = record_revision`; genesis/successor refs agree | `SCOPE_FREEZE_ISSUER` |

Every post-bootstrap family schema requires envelope `producer_context`; its
role, attempt, implementation, and environment are exact-bound by Plan/bundle
policy. Snapshot, Plan, Discovery, and Decision revision 1 forbid supersession.
Frozen scope genesis forbids it; a scope successor requires
`envelope.supersedes_ref` equal `payload.predecessor_scope_ref`. Bundle revision 1
forbids it; future bundle succession is outside E. Logical `payload.scope_id` is
intentionally distinct from scope record ID: record IDs name immutable revisions,
while `scope_id` names their lineage. The record ID is exactly
`inventory-scope-record:sha256:<64-lower-hex>/revision/<canonical-decimal>`.

The sealed E registry/catalog/bundle and every E validator explicitly reject the
legacy flat family and URI:

```text
agtxiv.inventory-scope/2.0.0
https://agtxiv.org/schema/v2/inventory-scope/2.0.0
```

That legacy schema's bytes are not changed or deleted. It is not an alias,
predecessor, migration input, fixture target, support asset, or accepted record
under E.

## 3. Pure boundary and common admission limits

Every public E function accepts exact built-in `bytes`, sealed registry/policy
objects, and explicitly supplied maps or tuples. It performs no filesystem,
network, Git, environment-variable, clock, locale, subprocess, import hook, DNS,
archive, database, or global-registry lookup. `str`, `bytearray`, `memoryview`,
subclasses of `bytes`, subclasses of sealed types, booleans in integer fields,
cyclic containers, and forged sealed objects fail closed with existing stable
validation diagnostics.

The same constants appear in this plan, schemas, compiled constants, candidate
policy, and tests:

| limit | exact value |
|---|---:|
| maximum source files | 4,096 |
| maximum normalized path UTF-8 bytes | 1,024 |
| maximum single source file bytes | 33,554,432 |
| maximum total source bytes | 67,108,864 |
| maximum discovery obligations | 256 |
| maximum discovery components | 8,192 |
| maximum canonical component entry bytes | 4,096 |
| maximum review findings | 4,096 |
| maximum frozen scope entries | 16,384 |
| maximum predecessor scope-chain declarations | 256 |
| maximum raw bytes per E record | 41,943,040 |
| maximum aggregate supplied E input bytes per call | 134,217,728 |
| maximum canonical exact-ref bytes | 2,048 |

These are pure-validation admission limits, not acquisition, archive, CAS,
runner, worker, sandbox, API, storage, or runtime quotas. The aggregate counts
all supplied raw record, schema, contract, source, and lineage bytes once by
argument occurrence before parsing or copying. A shared Python object supplied
in two argument slots counts twice. Preflight rejects limit+1 before hash,
decode, parse, canonicalization, schema traversal, or graph construction.

Schema maxima and semantic byte checks agree. Exact refs use D's closed shape,
forbid `path_hint`, and satisfy `len(canonical_bytes(ref)) <= 2048`.

## 4. PaperSourceSnapshot and exact source identity

### 4.1 Builder input and closed file rows

`validate_paper_source_snapshot` receives:

```text
snapshot_raw: exact bytes
source_bytes_by_path: exact built-in dict[str, bytes]
registry: sealed ContractSchemaRegistry
bundle_raw: exact bytes
```

The map is caller-supplied evidence, not a path instruction. Its key set must
equal the snapshot row `normalized_path` set exactly. No row may be checked by
opening that path.

The payload root contains exactly:

```text
snapshot_id
snapshot_version = 1
source_origin_kind = CALLER_SUPPLIED_LOCAL_FIXTURE
source_label
source_tree_algorithm = AGTXIV_SOURCE_TREE_V1
source_tree_root
source_file_count
source_total_bytes
source_files
```

`source_files` is strictly sorted by UTF-8 bytes of `normalized_path`. Each row
contains exactly:

```text
normalized_path
source_row_id
source_unit_id
sha256
byte_size
media_type
content_kind = TEXT | BINARY
```

`media_type` is declarative and does not affect the supplied-byte
`source_unit_id`; that is the byte-content identity from which media type is
excluded. It does affect the complete canonical row, tree leaf/root,
snapshot record/hash, and descendant exact bindings/content hashes. The stable `source_row_id` remains stable when media metadata or unrelated tree
membership changes. Component, anchor, and scope-entry IDs include media type and
therefore change on a media-type mutation, but remain stable when only an
unrelated path is added; validators also reject stale descendant row/tree
bindings. `content_kind=TEXT` does not authorize
decoding and does not make text validity part of the snapshot.
`source_file_count`, total bytes, each size, and each digest are recomputed from
the supplied byte map.

For exact raw file bytes $b$:

```text
sha256       = lowercase_hex(SHA-256(b))
source_unit_id = "source-unit:sha256:" + sha256
```

Thus `source_unit_id` is supplied-byte-only SHA-256 identity. It contains no path,
mtime, inode, filesystem metadata, Git object, URL, archive member, or normalized
text. Equal bytes intentionally have equal source-unit IDs; distinct paths remain
distinct rows. Row uniqueness is by path, not by source-unit ID.

Each row receives a path-sensitive stable locator independent of unrelated tree
membership:

```text
source_row_id = "source-row:sha256:" + H(
  b"AGTXIV_SOURCE_ROW_V1\x00" ||
  u64(len(normalized_path_utf8)) || normalized_path_utf8 ||
  u64(len(source_unit_id_utf8)) || source_unit_id_utf8
).hex()
```

Only canonical normalized path and supplied-byte `source_unit_id` enter this
identifier. `source_tree_root`, snapshot ID, row order/count, media type, and
other rows do not.

The validator recomputes it. All later source locators use `source_row_id` plus
path bytes; `source_unit_id` alone is never a row locator. Identical bytes at two
paths therefore share a byte identity but cannot alias coverage, components,
anchors, or scope entries.

### 4.2 Path profile

A submitted path is accepted only if it is already its canonical spelling; E
never repairs or silently normalizes it. It must:

1. be a built-in `str`, valid Unicode scalar text, NFC-normalized, and 1–1,024
   bytes in strict UTF-8;
2. use `/` separators, be relative, and have no leading or trailing `/`;
3. contain at least one nonempty segment and no empty, `.` or `..` segment;
4. contain no `\\`, NUL, C0/C1 control, DEL, surrogate, colon, or Unicode
   separator/control/format character;
5. contain no segment ending in space or `.`, and no segment equal under ASCII
   case-folding to `.`, `..`, a Windows device name (`CON`, `PRN`, `AUX`, `NUL`,
   `COM1`–`COM9`, `LPT1`–`LPT9`) with or without an extension; and
6. be unique both as exact NFC text and under the collision key
   `NFC(path).casefold()` encoded in UTF-8.

Absolute POSIX paths, drive paths, UNC paths, traversal, mixed separators,
percent-encoded traversal (the percent sign is data and does not get decoded),
overlong paths, non-NFC spellings, and case/Unicode-fold collisions are rejected.
No symlink, hardlink, device, or directory semantics are inferred because only
supplied regular-file bytes cross the pure boundary.

### 4.3 Domain-separated tree root

Rows are sorted by strict UTF-8 path bytes. Define `u64(n)` as an unsigned
8-byte big-endian integer and `H` as SHA-256 over bytes. For row path bytes `p`,
raw bytes `b`, digest bytes `d = H(b)`, and UTF-8 bytes `m` of the exact media
type:

```text
leaf = H(
  b"AGTXIV_SOURCE_TREE_V1_LEAF\x00" ||
  u64(len(p)) || p ||
  u64(len(b)) || d ||
  u64(len(m)) || m
)
```

The snapshot root is:

```text
H(
  b"AGTXIV_SOURCE_TREE_V1_ROOT\x00" ||
  u64(number_of_rows) ||
  leaf_1 || ... || leaf_n
)
```

and is rendered `sha256:<lowercase hex>`. Empty snapshots are forbidden. Path,
size, bytes, media type, addition, omission, and ordering therefore affect the
recomputed root; caller row reordering is rejected even when a sorted recompute
would have the same root.

## 5. DiscoveryObligationPolicy support contract

C's immutable `AgentizationProfileRelease/1.0.0` remains unchanged and continues
to select family/stage/cardinality/role/terminal constraints. It cannot encode
region selectors, component kinds, or matching rules. E therefore adds the
closed raw support-contract schema and candidate:

```text
schema URI  https://agtxiv.org/schema/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0
schema path schemas/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0.schema.json
asset path  contracts/v2/contract-kernel/planning/discovery-obligation-policy/1.0.0-candidate.1.json
asset ID    discovery-policy:checkpoint-e/1.0.0-candidate.1
```

It is a bundle support contract, **not** an ArtifactFamilyCatalog family: it
configures projection of selected Catalog/Profile rows rather than creating a
paper artifact obligation. Consequently it has no terminal policy and needs no
family conformance-vector row. Its root contains exactly `document_type`,
`document_schema_ref`, `policy_id`, `policy_version`, `policy_status =
NON_PRODUCTION_CANDIDATE`, `catalog_ref`, `profile_ref`, `projection_algorithm =
AGTXIV_DISCOVERY_OBLIGATIONS_V1`, `applicability_vocabulary`,
`component_matching_rules`, `resource_limits`, and `obligations`.

Each closed obligation contains exactly `obligation_id`, `family_id`, `stage_id`,
`region_selector`, `required_component_kinds`, `minimum_cardinality`, and
`applicability_rule`. Obligations are unique and sorted by Catalog family order,
Catalog stage ordinal, then UTF-8 obligation ID. Selectable region literals are
exactly `WHOLE_SOURCE_TREE`, `EVERY_SOURCE_ROW`, `TEX_DOCUMENT_BODY`,
`TEX_APPENDIX`, `BIBLIOGRAPHY`, and `OPAQUE_BINARY`; kinds are exactly
`DOCUMENT_TEXT`, `APPENDIX_TEXT`, `BIBLIOGRAPHY_TEXT`, `FIGURE_BINARY`,
`ARCHIVE_BINARY`, and `UNRESOLVED_SOURCE_REGION`. Applicability is one of
`ALWAYS`, `IF_MATCHING_SOURCE_MEDIA_TYPE`, or `IF_MATCHING_PATH_SUFFIX`, with a
closed ordered operand where applicable.

The candidate has exactly these six obligation rows; obligations are not expanded
per source row, so the 256-obligation bound is independent of the 4,096-row
source bound. `EVERY_SOURCE_ROW` means the minimum applies separately to every
matched row:

| obligation_id | family/stage | region | kinds | minimum | applicability/matching |
|---|---|---|---|---:|---|
| `obligation:checkpoint-e/source-row-accounting` | `INVENTORY_DISCOVERY_RESULT/INVENTORY_DISCOVERY` | `EVERY_SOURCE_ROW` | all six kinds | 1 per row | `ALWAYS`; same source row |
| `obligation:checkpoint-e/tex-body` | same | `TEX_DOCUMENT_BODY` | `DOCUMENT_TEXT` or `UNRESOLVED_SOURCE_REGION` | 1 | path suffix `.tex`; same row/range |
| `obligation:checkpoint-e/tex-appendix` | same | `TEX_APPENDIX` | `APPENDIX_TEXT` or `UNRESOLVED_SOURCE_REGION` | 1 | path suffix `.tex`; region matcher requires basename contains `appendix` after casefold; same row/range |
| `obligation:checkpoint-e/bibliography` | same | `BIBLIOGRAPHY` | `BIBLIOGRAPHY_TEXT` or `UNRESOLVED_SOURCE_REGION` | 1 | suffix `.bbl` or `.bib`; same row/range |
| `obligation:checkpoint-e/opaque-binary` | same | `OPAQUE_BINARY` | `FIGURE_BINARY`, `ARCHIVE_BINARY`, or `UNRESOLVED_SOURCE_REGION` | 1 | media is not `text/x-tex`/`text/plain`; same row/range |
| `obligation:checkpoint-e/frozen-inventory-scope` | `FROZEN_INVENTORY_SCOPE/SCOPE_FREEZE` | `WHOLE_SOURCE_TREE` | all six kinds | 1 | `ALWAYS`; union of all applicable components |

“Contains” and suffix matching operate on NFC path code points after ASCII
casefold only; no locale, regex, MIME sniff, or file read occurs. An inapplicable
conditional base row emits no obligation and its absence is recomputed. The
whole-scope row is the exact terminal `obligation_key`.

`AGTXIV_DISCOVERY_OBLIGATIONS_V1` takes the exact selected C Profile rules and
these policy rows; emits only obligations whose family/stage is selected;
evaluates applicability over the complete Plan expected-source table; records the
ordered matched source-row IDs inside each emitted obligation; applies
`EVERY_SOURCE_ROW` cardinality per matched row without creating new obligations;
and sorts by the order above. Component
matching requires source-row equality, region predicate, allowed kind, and anchor
range; one component may satisfy multiple obligations only when each rule
matches. The result—including obligation IDs, order, applicability decisions,
required kinds, and minima—is recomputed exactly and capped at 256. No Plan may
supply hand-authored obligations. The policy exact-binds the candidate Catalog
and Profile, appears in the bundle manifest, and is supplied explicitly to every
Plan/Discovery validator.

## 6. Query-independent AgentizationPlan

The closed plan payload contains exactly:

```text
plan_id
plan_revision = 1
source_snapshot_ref
source_tree_root
contract_bundle_ref
artifact_family_catalog_ref
agentization_profile_ref
stable_code_catalog_ref
kernel_validation_policy_ref
discovery_policy_ref
resource_policy_ref = kernel_validation_policy_ref
expected_source_units
profile_obligations
planning_context = QUERY_INDEPENDENT
```

Every ref is exact and supplied to the validator as raw bytes. The plan validator
requires:

- snapshot ref, source root, and expected source units exactly equal the validated
  snapshot, in snapshot order;
- bundle ref equals the envelope bundle and bundle candidate bytes;
- Catalog and Profile equal the C/E candidate bytes, the Profile exact-refers to
  that Catalog, and every selected obligation is permitted by both;
- code catalog and policy equal E 1.1 candidates;
- `discovery_policy_ref` resolves the final DiscoveryObligationPolicy and
  `resource_policy_ref` is an exact second occurrence of the final 1.1
  `kernel_validation_policy_ref`—all five authoritative exact-ref fields are
  literally equal and no separate resource-policy bytes exist;
- `profile_obligations` exactly equals `AGTXIV_DISCOVERY_OBLIGATIONS_V1`
  projected from the unchanged supplied C Profile plus exact
  DiscoveryObligationPolicy, ordered by Catalog family/stage then obligation ID;
  and
- resource values equal Section 3 and the final 1.1 policy projection, never a
  weaker caller-selected subset.

E Plan has no `environment_ref`, `tool_refs`, tool selector, or runtime execution
manifest. Runtime environment and tool semantics are explicitly deferred. The
existing mandatory envelope `producer_context` remains structural: candidate
records bind `implementation_ref` to exact `planning_validation.py` bytes and
`environment_ref` to the already committed canonicalization-profile provenance
asset, both bundle-bound; these refs do not enter Plan payload or claim a runtime
environment/toolchain.

An expected-source-unit row contains exactly `source_row_id`, `normalized_path`,
`source_unit_id`, `sha256`, `byte_size`, `media_type`, and `content_kind`. An obligation is the exact closed projection from Section 5 and contains
`obligation_id`, `family_id`, `stage_id`, `region_selector`,
`minimum_cardinality`, `required_component_kinds`, applicability result, and its
matched source-row IDs. `region_selector` is closed policy vocabulary, not free
text or a query selector.

No key named or semantically serving `query`, `query_ref`, `query_text`,
`requested_claim`, `requested_theorem`, `search`, `filter`, `include_only`,
`exclude`, `path_subset`, `family_subset`, `region_subset`, or dynamic selector is
permitted at any depth. Unknown keys are already rejected by closed schemas; a
semantic recursive forbidden-key gate rejects disguised nested injection in
extension-like values. E defines no extension map.

A query may cause a future service to schedule a plan, but it cannot enter plan
bytes, remove a source unit, weaken the Profile, reduce an obligation, or narrow
discovery. E validates only query-independent `PLAN_BOUND` context.

## 7. Total-accounted InventoryDiscoveryResult

The discovery payload contains exactly:

```text
discovery_id
discovery_revision = 1
plan_ref
source_snapshot_ref
source_tree_root
producer_context
observed_resource_limits
source_unit_coverage
classified_components
ambiguous_components
unclassified_components
obligation_dispositions
discovery_errors
completeness_claim = TOTAL_ACCOUNTED_PROFILE_RELATIVE
```

### 6.1 Source-unit closure

`source_unit_coverage` has exactly one row per plan expected source row, in plan
order. Each row contains the same `source_row_id`/path/unit/digest/size/media/content-kind binding plus nonempty
`component_ids` and `coverage_status = COMPONENTS_RECORDED | BLOCKED_WITH_EVIDENCE`. A zero-length file
still requires one component spanning `[0,0)`.

Bidirectional reconciliation requires:

- coverage rows equal expected rows with no omission, addition, substitution, or
  reordering;
- every coverage `component_id` exists exactly once in one partition;
- every component is named exactly once by its bound source coverage row; and
- every component's immutable source binding equals that row.

### 6.2 Disjoint total component partition

Each component entry contains exactly:

```text
component_id
source_row_id
source_unit_id
normalized_path
byte_start
byte_end
component_kind
source_anchor_hash
classification_state
classification_or_issue_code
evidence_refs
```

Offsets are I-JSON integers with `0 <= byte_start <= byte_end <= byte_size`.
`source_anchor_hash` is rendered `sha256:<hex>` and computed exactly as:

```text
H(b"AGTXIV_SOURCE_ANCHOR_V1\x00" ||
  u64(len(source_row_id_utf8)) || source_row_id_utf8 ||
  u64(len(normalized_path_utf8)) || normalized_path_utf8 ||
  u64(len(media_type_utf8)) || media_type_utf8 ||
  source_digest_bytes || u64(byte_start) || u64(byte_end) ||
  H(exact_supplied_slice))
```

It is recomputed from supplied source bytes. Entries are
ordered by `(normalized_path UTF-8, byte_start, byte_end, component_id)` and each
canonical entry is at most 4,096 bytes.

The three arrays are pairwise disjoint by `component_id` and their union equals
the component IDs in coverage. Their tagged states are fixed:

```text
classified_components   -> CLASSIFIED
ambiguous_components    -> AMBIGUOUS
unclassified_components -> UNCLASSIFIED
```

No component is ignored, rejected out of the denominator, or represented only by
an error. Ambiguous and unclassified material remains explicit.

`component_id` is stable for an unchanged source anchor and kind:

```text
"component:sha256:" + H(
  b"AGTXIV_COMPONENT_V1\x00" ||
  u64(len(source_row_id_utf8)) || source_row_id_utf8 ||
  u64(len(normalized_path_utf8)) || normalized_path_utf8 ||
  u64(len(media_type_utf8)) || media_type_utf8 ||
  source_digest_bytes || u64(byte_start) || u64(byte_end) ||
  u64(len(kind_utf8)) || kind_utf8 || H(exact_slice)
).hex()
```

Classification state is intentionally absent from identity, so later
classification can preserve the component ID while recording a revision delta.
Overlapping components are allowed only when their distinct profile kinds permit
it; exact duplicate anchors/kinds are rejected.

### 6.3 Obligation closure

There is exactly one disposition per plan profile obligation, in plan order:

```text
obligation_id
status = SATISFIED | AMBIGUOUS | UNCLASSIFIED | BLOCKED
component_ids
finding_or_error_refs
```

Every listed component exists. `SATISFIED` has at least the plan minimum number of
classified components of an allowed kind. `AMBIGUOUS` names at least one
ambiguous component; `UNCLASSIFIED` names at least one unclassified component;
`BLOCKED` cannot be empty: it names nonempty exact evidence and at least one
affected coverage row whose status is `BLOCKED_WITH_EVIDENCE`. Every such row
names at least one component in the ambiguous or unclassified partition with
`component_kind = UNRESOLVED_SOURCE_REGION`; that fallback component matches the
blocked obligation's source-row/region applicability and appears in the
BLOCKED disposition's `component_ids`. Conversely, every fallback component
listed by the disposition occurs in one of its affected coverage rows. The row,
fallback component, disposition, and exact `discovery_errors`/evidence form a
bidirectional closed set: the row/component names the exact error/evidence, the
disposition names the same error/evidence and component, and each named error is
referenced back by at least one affected row/component and that disposition.
Empty affected-row, component, relevant-error, or evidence sets cannot satisfy
BLOCKED. `BLOCKED` cannot claim satisfaction. Every component whose kind or
unresolved state is relevant to an obligation appears in that disposition, and
every profile obligation appears once. Dangling discovery errors are rejected.

“Total accounted” means mechanical closure against the supplied snapshot and
Profile. It is not proof that no semantic component exists beyond the discovery
method and is not a scientific completeness claim. A source row whose detailed
discovery is blocked remains schema-valid and reviewable only through exactly one
coverage row with `coverage_status = BLOCKED_WITH_EVIDENCE`, at least one fallback
`UNRESOLVED_SOURCE_REGION` component in the ambiguous or unclassified partition,
and nonempty exact error/evidence linked to its obligation dispositions. A truly
omitted source row is an invalid discovery: it cannot be passed to decision
validation and cannot support a valid BLOCK decision. BLOCK always binds a
semantically valid, total-accounted discovery; it expresses non-acceptance, not a
way to bypass discovery closure.

## 8. Independent ScopeFreezeDecision and typed BLOCK

The decision payload contains exactly:

```text
decision_id
decision_revision = 1
plan_ref
discovery_ref
source_snapshot_ref
source_tree_root
reviewer
reviewer_role = SCOPE_FREEZE_REVIEWER
producer_actor_ref
independence_declaration
conflict_declarations
review_policy_ref = plan.kernel_validation_policy_ref
findings
decision = ACCEPT | BLOCK
terminal_requirement
```

`terminal_requirement` is forbidden for ACCEPT. For BLOCK it is required and
contains exactly the expected obligation key, reason code, family, stage, outcome,
and PLAN_BOUND context literals; it is not an exact terminal record ref. Findings
are ordered, closed, and capped at 4,096. Every finding binds one plan,
discovery, source unit, component, obligation, or actor declaration by exact ID.

The structural gate enforces built-in string inequality between the discovery
producer `actor_id` and reviewer `actor_id`, different producer/reviewer roles,
and a closed declaration for every listed actor-pair conflict category. ACCEPT
requires all declarations `NO_CONFLICT_DECLARED`; BLOCK permits declared
conflicts and requires a finding for each. Missing declarations fail closed.

These checks establish only structural inequality and internally consistent
conflict declarations. E does **not** verify legal or real-world identity,
organizational control, beneficial ownership, conflict-of-interest truth,
credential authority, signatures, keys, trust roots, attestations, or reviewer
competence. Production identity and signature policy remain deferred.

ACCEPT requires all discovery closure gates, no blocking finding, no declared
conflict, and exact current refs. BLOCK requires at least one blocking finding.
The individual decision validator proves only intrinsic semantics; absence or
cardinality of terminal/scope records is proved only by the aggregate complete-set
seam. The decision does not exact-refer to the terminal. The later terminal may
exact-refer to the already frozen BLOCK decision as evidence, so the edge is
one-way and creates no record-hash cycle.

The BLOCK terminal is an intrinsically valid unchanged Checkpoint B
`TypedTerminalResult` with exactly:

```text
target.family_id = FROZEN_INVENTORY_SCOPE
target.stage = SCOPE_FREEZE
outcome = BLOCKED
reason_code = AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED
binding_context.context_mode = PLAN_BOUND
binding_context.plan_ref = exact rejected plan
```

The complete frozen terminal binding is:

- terminal envelope producer role is exactly `SCOPE_FREEZE_ISSUER`, which is the
  C Profile allowed-producer subset for the target family/stage; its producer
  actor is the declared issuer, and payload `attempt_id` equals that envelope
  producer context's attempt ID. It is not the Discovery producer or reviewer
  attempt;
- context Profile/Catalog refs equal the Plan refs and `plan_ref` equals the
  rejected Plan exact-record ref;
- `target_obligation.obligation_key` equals
  `obligation:checkpoint-e/frozen-inventory-scope`; family/stage are the literals
  above; and `basis` is exactly `COMPONENT`. Its `component_ref` has record type,
  ID, revision, schema ref, and content hash byte-equal to `plan_ref`,
  `component_id = obligation:checkpoint-e/frozen-inventory-scope`, and
  `json_pointer = /payload/profile_obligations/0`; Catalog-family ordering places
  the frozen-scope obligation first, and the validator recomputes that exact
  location. This is the
  B-required PLAN_BOUND component whose record projection equals `plan_ref`;
- outcome is `BLOCKED`; declared reason is
  `AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED`; evidence contains, in UTF-8 evidence-ID
  order, exactly `evidence:scope-freeze/discovery` as a RECORD ref to the valid
  Discovery and `evidence:scope-freeze/block-decision` as a RECORD ref to the
  frozen BLOCK decision. A third blocked-component COMPONENT evidence item is
  present only for `BLOCKED_WITH_EVIDENCE` and exact-refers to that component in
  the Discovery. Decision has no terminal ref, so these one-way evidence refs are
  acyclic;
- retry is exactly `NO_RETRY_IN_CURRENT_CONTEXT` with a nonblank context-change
  requirement; next action is exactly B-compatible `ESCALATE`, responsible actor
  equals the BLOCK decision reviewer, responsible role is
  `SCOPE_FREEZE_REVIEWER`, and deadline is `NO_DEADLINE`; and
- `resources.limit` is the separate closed B `ResourceBudget` projection below;
  it does not reuse KernelValidationPolicy admission-limit keys. Resource evidence
  is already included in the exact Discovery/Decision evidence records.

The blocked-appendix fixture freezes one complete B-schema-valid vector. At the
root it has exactly `envelope`, `payload`, and computed `content_hash`. Envelope
has record type `agtxiv.typed-terminal-result/1.0.0`, record ID
`terminal:checkpoint-e/scope-freeze-blocked-appendix/1`, revision 1, exact B
schema ref, exact E bundle record ref, `created_at = 2026-09-01T00:00:00Z`, no
supersedes ref, and this complete producer context:

```text
producer.actor_kind = MECHANICAL_SERVICE
producer.actor_id   = actor:checkpoint-e/scope-freeze-issuer
role                = SCOPE_FREEZE_ISSUER
attempt_id          = attempt:checkpoint-e/scope-freeze-issuer/blocked-appendix/1
implementation_ref  = exact bundle validator: planning_validation.py
environment_ref        = exact bundle canonicalization-profile provenance asset
```

The payload is exactly:

```text
terminal_for_attempt          true
terminal_scope                ATTEMPT_ONLY
successful_artifact_produced false
satisfaction_claim            NONE
attempt_id                    attempt:checkpoint-e/scope-freeze-issuer/blocked-appendix/1
binding_context               PLAN_BOUND with exact E Profile, Catalog, and blocked Plan refs
target_obligation.obligation_key obligation:checkpoint-e/frozen-inventory-scope
target_obligation.stage_id    SCOPE_FREEZE
target_obligation.family_id   FROZEN_INVENTORY_SCOPE
target_obligation.basis.basis_kind COMPONENT
target_obligation.basis.component_ref exact blocked Plan ref projection plus:
  component_id obligation:checkpoint-e/frozen-inventory-scope
  json_pointer /payload/profile_obligations/0
outcome                       BLOCKED
declared_reason.declared_reason_code AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED
declared_reason.summary       Scope freeze was not accepted for the exact plan-bound discovery; no FrozenInventoryScope was issued.
retry.retry_disposition       NO_RETRY_IN_CURRENT_CONTEXT
retry.context_change_required A new independently reviewed scope-freeze attempt is required before scope issuance.
next_action.action_code       ESCALATE
next_action.description       Escalate the blocked scope-freeze decision for an independently authorized new attempt.
next_action.responsible_actor {actor_kind: HUMAN, actor_id: actor:checkpoint-e/scope-freeze-reviewer}
next_action.responsible_role  SCOPE_FREEZE_REVIEWER
next_action.deadline          {deadline_kind: NO_DEADLINE,
                               no_deadline_reason: No production review schedule is authorized by Checkpoint E.}
```

Evidence is exactly three rows in strict UTF-8 `evidence_id` order:

```text
1 evidence:scope-freeze/block-decision
  evidence_role POLICY_OBSERVATION; evidence_kind RECORD;
  record_ref exact frozen BLOCK ScopeFreezeDecision
2 evidence:scope-freeze/blocked-component
  evidence_role TOOL_DIAGNOSTIC; evidence_kind COMPONENT;
  component_ref exact unresolved appendix component in the valid Discovery
3 evidence:scope-freeze/discovery
  evidence_role INPUT_STATE; evidence_kind RECORD;
  record_ref exact valid total-accounted Discovery
```

The BLOCK decision has no terminal ref, so row 1 does not form a reverse edge.
The Discovery RECORD and component authoritative projections are distinct, so B's
duplicate-evidence projection check passes.

`resources` uses all six exact `ResourceBudget/1.0.0` dimensions, each a
nonnegative I-JSON integer:

```text
limit.max_wall_time_ms       60000
limit.max_cpu_time_ms        60000
limit.max_peak_memory_bytes  134217728
limit.max_input_bytes        134217728
limit.max_output_bytes       41943040
limit.max_network_requests   0
observed                     {network_requests: 0}
unobserved_metrics           [wall_time_ms, cpu_time_ms, peak_memory_bytes,
                              input_bytes, output_bytes]
relation                     INDETERMINATE
```

The unobserved array follows B's fixed metric order; every limited dimension
appears exactly once in observed or unobserved, the sets are disjoint, observed
network requests do not exceed zero, and at least one metric is unobserved, so B
mechanically requires `INDETERMINATE`. These values are a declarative validation-
attempt budget, not OS enforcement, acquisition quota, runtime guarantee, or a
claim that the unobserved resources stayed within budget. Every exact ref above
has the closed five-field asset or record/component projection required by B and
resolves from explicitly supplied candidate bytes.

`validate_planning_terminal_constraints` receives a builder-created sealed
`KernelValidationPolicyV11Constraints` whose refs were checked against the exact
bundle-bound 1.0/1.1 roots/supports. It calls C's existing public
`validate_typed_terminal_result_catalog_constraints` exactly once; C intrinsically
calls B exactly once and E never calls B separately. Only after C succeeds does E
call the 1.1 gate once to enforce the actual sealed registration row, then exact
planning bindings. Hard-coded reason/target constants are test or bootstrap
expectations, never a substitute for the supplied policy constraint.
The terminal cannot target the absent scope record or use Discovery as basis; it
targets the Plan obligation through the exact Plan component basis required by
B. ACCEPT forbids a BLOCK terminal, and
BLOCK forbids issuance or validation of a scope.

## 9. FrozenInventoryScope, identity, and revisions

The scope payload contains exactly:

```text
scope_id
scope_revision
plan_ref
discovery_ref
accept_decision_ref
source_snapshot_ref
source_tree_root
predecessor_scope_ref
revision_delta
scope_entries
```

Genesis has `scope_revision = 1`, no predecessor, and
`revision_delta.kind = GENESIS`. A successor has revision exactly predecessor + 1,
one exact predecessor ref, the same logical `scope_id`, and
`revision_delta.kind = SUCCESSOR`.

Every discovery component—including ambiguous and unclassified components—maps
to exactly one scope entry. The entry contains exactly:

```text
scope_entry_id
component_id
source_row_id
source_unit_id
normalized_path
byte_start
byte_end
component_kind
scope_state = CLASSIFIED | AMBIGUOUS | UNCLASSIFIED
source_anchor_hash
```

Entries are ordered by `(normalized_path UTF-8, byte_start, byte_end,
component_id)`. Stable identity is:

```text
scope_id = "inventory-scope:sha256:" + H(
  b"AGTXIV_SCOPE_ID_V1\x00" || logical_plan_lineage_seed
).hex()

scope_entry_id = "scope-entry:sha256:" + H(
  b"AGTXIV_SCOPE_ENTRY_V1\x00" ||
  u64(len(scope_id_utf8)) || scope_id_utf8 ||
  u64(len(source_row_id_utf8)) || source_row_id_utf8 ||
  u64(len(normalized_path_utf8)) || normalized_path_utf8 ||
  u64(len(component_id_utf8)) || component_id_utf8
).hex()
```

For genesis, `logical_plan_lineage_seed` is the exact first plan ID and source
snapshot ID with length prefixes. A successor carries that same seed through the
predecessor; it is never recomputed from the new plan. Unchanged component IDs
therefore preserve entry IDs. Changed anchors/kinds create new component and
entry IDs. Classification-only changes preserve IDs.

The successor delta contains strictly ordered, disjoint sets:

```text
added_entry_ids
removed_entry_ids
classification_changed_entry_ids
source_binding_changed_entry_ids
```

It must equal the mechanical old/new diff. `source_binding_changed_entry_ids` is
normally empty because source binding is part of component identity; any attempt
to keep an entry ID while changing source unit, path, offsets, anchor, or kind is
rejected rather than accepted as a delta. Old plan, snapshot, discovery,
decision, source, component, entry, and downstream bindings remain immutable and
addressable.

### 9.1 Explicit predecessor-chain declaration

No successor validator accepts only `predecessor_scope_raw`. E adds the sealed,
detached `PlanningScopeChainDeclaration`, constructed only by the pure public
`build_planning_scope_chain_declaration` seam from exactly:

```text
snapshot_raw: bytes
source_bytes_by_path: dict[str, bytes]
plan_raw: bytes
discovery_raw: bytes
decision_raw: bytes
scope_raw: bytes
supplied_contract_assets: tuple[SuppliedAsset, ...]
bundle_raw: bytes
```

The declaration snapshots exact built-in values behind a private construction
token and tamper seal; it carries no prevalidated/accepted flag and grants no
authority. Constraints are not caller-fabricated fields: validation rebuilds C,
D 1.0, and E 1.1 sealed constraints from each declaration's exact bundle-bound
roots/supports and the supplied registry. Every declaration must describe an
ACCEPT chain with zero terminals and exactly one scope.

All successor-facing public calls require
`predecessor_history: tuple[PlanningScopeChainDeclaration, ...]`. The tuple is
oldest-to-newest, has at most 256 declarations, uses exact tuple/declaration
classes with no subclasses, and has no duplicate scope record identity. Genesis
requires exactly `()`, revision 1, no predecessor/supersedes ref, and a GENESIS
delta. Successor revision $r>1$ requires exactly $r-1$ declarations; declaration
1 is a genesis chain, each later declaration is validated as the next successor,
and the last declaration's scope exact-record ref equals the current
`predecessor_scope_ref` and envelope `supersedes_ref`. Plan, snapshot, discovery,
ACCEPT decision, scope, bundle, assets, and rebuilt constraints are therefore
validated for every predecessor, not inferred from the predecessor scope's
`plan_ref` or accepted from intrinsic shape.

`validate_frozen_inventory_scope` is frozen as:

```text
validate_frozen_inventory_scope(
  scope_raw: bytes,
  decision_raw: bytes,
  discovery_raw: bytes,
  plan_raw: bytes,
  snapshot_raw: bytes,
  source_bytes_by_path: dict[str, bytes],
  supplied_contract_assets: tuple[SuppliedAsset, ...],
  registry: ContractSchemaRegistry,
  bundle_raw: bytes,
  predecessor_history: tuple[PlanningScopeChainDeclaration, ...],
) -> FrozenInventoryScopeView | tuple[Diagnostic, ...]
```

It validates history iteratively through the same semantic implementation behind
`validate_planning_scope_chain`; there is no weaker intrinsic predecessor path.
Every raw record remains subject to 41,943,040 bytes, each source map to the
Section 3 file/single/total limits, history to 256 entries, and the sum of current
plus every declaration's records, sources, bundle, and supplied assets to the
unchanged 134,217,728-byte E aggregate limit. Preflight counts every argument
occurrence before parsing or copying. All values are caller-supplied bytes; no
filesystem, bundle registry, Git, network, cache, or other ambient lookup fills a
missing predecessor.

## 10. Transitive revision impact

The exact public seam is:

```text
compute_scope_revision_impact(
  predecessor_history: tuple[PlanningScopeChainDeclaration, ...],
  successor_declaration: PlanningScopeChainDeclaration,
  downstream_records: tuple[bytes, ...],
  lineage_projection: ScopeRevisionLineageProjection,
  registry: ContractSchemaRegistry,
) -> ScopeRevisionImpact | tuple[Diagnostic, ...]
```

`predecessor_history` is the complete oldest-to-immediate-predecessor ACCEPT
history from Section 9.1; it is nonempty for impact. `successor_declaration` is
the complete new ACCEPT chain and is not already a member of that tuple. Impact
first validates every old declaration through the public chain semantics, then
validates the successor with exactly that history, and only then compares the
validated old/new scopes and computes delta/closure. A forged old Plan ref,
intrinsically valid but semantically invalid predecessor, stale predecessor
bundle/policy, BLOCK predecessor, missing ancestor, or invalid new chain hard-
stops before graph work. Thus both full old and new semantic chains are checked;
raw scope shape alone is never an impact input.

`ScopeRevisionLineageProjection` is a sealed, detached programmatic shape with a
private token/tamper seal, not an additional persistent family. Its public builder
accepts exact built-in tuples only and freezes exactly:

```text
nodes: (record_id, record_type, scope_ref, coverage_mode,
        exact_input_entry_ids, exact_output_entry_ids)
edges: (producer_record_id, consumer_record_id, relation = DERIVED_FROM)
```

Supported downstream record types in E are exactly
`agtxiv.checkpoint-e-entry-output/1.0.0`,
`agtxiv.checkpoint-e-whole-scope-output/1.0.0`, and
`agtxiv.checkpoint-e-derived-output/1.0.0`; their closed fixture schemas live in
the fixture tree, are registry/bundle support schemas only, and are never Catalog
families. For each supplied downstream immutable record the validator extracts
node ID from `envelope.record_id`, type from `envelope.record_type`, old scope
exact-ref from payload, and exact input/output entry IDs from the closed payload.
The projection must equal that extraction byte-for-byte; caller-invented nodes or
refs fail. Every downstream record appears exactly once, including isolated
nodes. Every edge endpoint resolves to that complete node set; duplicate,
self-loop, dangling, and **all directed cycles** are rejected, whether or not the
cycle would be affected.

`coverage_mode` is exactly `ENTRY_SET` or `WHOLE_SCOPE`. `ENTRY_SET` requires a
nonempty exact input-entry set and is directly affected when an input is removed,
classification-changed, or source-replaced. `WHOLE_SCOPE` requires an empty
input-entry set and is directly affected by any nonempty delta, including added
entries. Output entry IDs must be in the bound old scope unless the fixture is an
explicit derived non-scope output with an empty output-entry set. Isolated nodes
are classified affected/unaffected by their own coverage only and have no
transitive descendants.

`ScopeRevisionImpact` is a detached immutable non-record result containing old and
new exact scope refs, direct changed entry IDs, directly affected record IDs,
transitively affected record IDs, affected whole-scope output IDs, unaffected
record IDs, and deterministic topological order. Direct effect is computed by
the rules above; transitive effect is the least fixed point following
`DERIVED_FROM` edges from every directly affected node. No edge is inferred from
filenames, IDs, ambient registries, or undeclared content. Ordering of supplied
records/edges cannot change the canonical UTF-8-sorted result.

The allowlisted fixtures include three closed downstream fixture schemas, entry,
whole-scope and derived record vectors, an exact lineage projection vector, and
expected impact. Tests cover isolated nodes, all-cycle rejection, duplicate and
dangling endpoints, wrong extracted refs, whole-scope addition, entry removal,
branches, multi-parent descendants, stale claimed sets, and unaffected siblings.
Old records retain old scope refs and are never rewritten.

## 11. D evolution: exact 1.0 predecessor compatibility

E must not mutate either D `1.0.0` schema/root,
`src/agtxiv_v2/contracts/code_policy_validation.py`, Checkpoint B schema/validator,
or `DiagnosticCode`. It adds:

```text
schemas/v2/contract-kernel/contract/stable-code-catalog/1.1.0.schema.json
schemas/v2/contract-kernel/contract/kernel-validation-policy/1.1.0.schema.json
schemas/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0.schema.json
contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.1.0.json
contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.1.0.json
src/agtxiv_v2/contracts/code_policy_v1_1_validation.py
```

The 1.1 catalog field-by-field projection is exact. `document_type`, `catalog_id`,
`catalog_kind`, and compatibility semantics remain equal to 1.0. The successor
recomputes `document_schema_ref` for the 1.1 schema, sets `catalog_version =
1.1.0`, `revision_kind = SUCCESSOR`, and adds exact `predecessor_ref` and
`predecessor_version = 1.0.0`. `codes[0:79]` is an immutable prefix: every
`code`, `code_kind`, `kind_ordinal`, `meaning`, `status`,
`introduced_in_catalog_version`, and array position equals 1.0 byte-for-byte.
Code row 80 is the sole append. Root resources are recomputed as:

```text
exact_code_entries             80
maximum_code_utf8_bytes       256
maximum_meaning_utf8_bytes   4096
maximum_code_entry_bytes     4880
maximum_root_metadata_bytes 18432
maximum_catalog_root_bytes  408832
```

The last equality is $80 * 4,880 + 18,432 = 408,832$. No claim is made that the
1.0 root version, revision, schema ref, count, or root limit stays unchanged.

The one appended reason row is exactly:

```text
code       AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED
code_kind  TERMINAL_REASON
kind_ordinal 2
meaning    Independent scope-freeze review did not accept the exact plan-bound discovery, so no FrozenInventoryScope was issued.
introduced_in_catalog_version 1.1.0
status     ACTIVE
```

The 1.1 policy preserves its 1.0 semantic identity and every 1.0 registration as
an exact prefix, but deliberately recomputes successor fields. It sets the 1.1
schema/policy version and successor/predecessor refs; changes `code_catalog_ref`
to the exact 1.1 catalog; retains the exact B terminal schema; retains the old C
constraint refs under `inherited_registration_context_ref`; sets active
`structural_constraints_ref` to the E Catalog/Profile plus exact
DiscoveryObligationPolicy; sets `validator_ref` to the new 1.1 module; extends
entry points with all seven planning seams and aggregate seam; sets
`conformance_vector_ref` to the exact E vector asset; and extends gate order only
with `TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC_ONCE`,
`TERMINAL_E_1_1_REASON_POLICY`, and `TERMINAL_E_EXACT_PLANNING_BINDINGS` after
record/chain validation. The old D registration remains checked against its
inherited old C constraints; the new registration is checked against active E
constraints.

The complete successor resource map is:

```text
exact_policy_roots                              4
exact_support_assets                            3
maximum_predecessor_total_root_bytes       428976
maximum_catalog_root_bytes                 408832
maximum_policy_root_bytes                   49152
maximum_successor_total_root_bytes          457984
maximum_total_root_bytes                    886960
maximum_exact_ref_bytes                       2048
maximum_validator_source_bytes             1048576
maximum_vectors                                512
maximum_vector_entry_bytes                    2048
maximum_vector_index_bytes                 1064960
maximum_obligation_policy_root_bytes       41943040
maximum_total_support_bytes                44056576
maximum_total_code_policy_input_bytes      44943536
exact_code_entries                              80
exact_reason_registrations                       2
exact_targets_per_registration                   1
exact_total_reason_targets                       2
maximum_emitted_diagnostics                   4096
```

The code-policy support tuple has exactly three assets and no hidden fourth role:

| role | exact asset | individual maximum bytes |
|---|---|---:|
| successor validator source | `src/agtxiv_v2/contracts/code_policy_v1_1_validation.py` / `text/x-python` | 1,048,576 |
| E conformance-vector asset | `vectors:checkpoint-e-planning-families/1.0.0` / `application/json` | 1,064,960 |
| final DiscoveryObligationPolicy root | `discovery-policy:checkpoint-e/1.0.0-candidate.1` / `application/json` | 41,943,040 |

Catalog/Profile and predecessor constraints are validated root/constraint inputs,
not members of this support tuple; bundle admission counts their bytes separately
under the overall E aggregate. All maxima/counts occur identically in schema,
compiled constants, candidate roots, and exact/limit+1 tests.
`maximum_successor_total_root_bytes = 408,832 + 49,152`;
`maximum_total_root_bytes` adds D's fixed 428,976;
`maximum_total_support_bytes = 1,048,576 + 1,064,960 + 41,943,040 =
44,056,576`; the final input bound is `44,056,576 + 886,960 = 44,943,536`. These code-policy preflights remain under the overall E
134,217,728-byte call bound.

The complete new registration row is:

```text
reason_code                 AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED
registration_kind           PLANNING_SCOPE_BLOCK_ONLY
allowed_outcomes            [BLOCKED]
allowed_retry_dispositions  [NO_RETRY_IN_CURRENT_CONTEXT]
allowed_context_modes       [PLAN_BOUND]
targets                     [{family_id: FROZEN_INVENTORY_SCOPE,
                              family_version: 1.0.0,
                              stage_id: SCOPE_FREEZE}]
```

No wildcard or additional target/outcome/retry/context is permitted. No E failure
adds a `DiagnosticCode`; malformed E input uses existing diagnostics with stable
phases/details. Tests mutate independently every immutable predecessor row field
and order, and independently test every permitted successor field/ref/count,
wrong predecessor, same-ID/different-byte substitution, extra row/registration,
and each exact resource value.

## 12. ContractBundleRelease candidate and bootstrap order

The bundle record candidate path is:

```text
contracts/v2/contract-kernel/bundles/checkpoint-e/1.0.0-candidate.1.json
```

Its `baseEnvelope` is frozen as:

```text
record_type     agtxiv.contract-bundle-release/1.0.0
record_id       contract-bundle:checkpoint-e/1.0.0-candidate.1
record_revision 1
schema_ref      exact ContractBundleRelease schema
contract_bundle_ref FORBIDDEN
producer_context FORBIDDEN
supersedes_ref  FORBIDDEN
```

Its closed payload contains exactly:

```text
bundle_id = contract-bundle:checkpoint-e/1.0.0-candidate.1
bundle_version = 1.0.0-candidate.1
bundle_status = NON_PRODUCTION_CANDIDATE
canonicalization_profile_ref
schema_assets
contract_assets
validator_assets
specification_assets
bundle_manifest_hash
```

`payload.bundle_id == envelope.record_id`.
`canonicalization_profile_ref` is an exact alias of the golden-vector profile
entry in `contract_assets`; its five authoritative fields must be literally equal
and it does not add a second unique manifest asset. `bundle_manifest_hash` is
`sha256:H(b"AGTXIV_BUNDLE_ASSET_MANIFEST_V1\x00" || canonical_bytes(ordered
schema/contract/validator/specification ref arrays))`; it covers only the ordered
asset manifest and excludes envelope fields, payload identity/status, itself, and
record `content_hash`. The normal immutable-record canonical projection computes
`content_hash` over the full envelope and payload, including
`bundle_manifest_hash`, excluding only root `content_hash`.

Construction order is normative and contains no preliminary/final rebuild:

1. freeze and registry-validate all common/E/support schemas, then freeze exact
   `planning_validation.py`, `code_policy_v1_1_validation.py`, existing generic
   `schema_validation.py`, and the closed E family conformance-vector bytes;
2. build the final E 1.1 StableCodeCatalog against exact D 1.0 predecessor bytes;
3. build the final E ArtifactFamilyCatalog against frozen schema, validator, and
   vector bytes; it has no Profile, obligation-policy, kernel-policy, or bundle
   ref;
4. build the final E AgentizationProfileRelease exact-binding that Catalog;
5. build the one and only final DiscoveryObligationPolicy exact-binding the final
   Catalog and Profile;
6. build the final 1.1 KernelValidationPolicy **last among contract roots**, so it
   exact-binds the final StableCodeCatalog, Catalog, Profile,
   DiscoveryObligationPolicy, vector, validators, inherited D context, and B
   terminal schema;
7. build and validate the bundle base-envelope record from those fixed bytes; and
8. build fixture records whose contract-bound envelopes exact-refer to that
   bundle record.

Commit 3 may add all six support/root paths atomically, but its construction
script executes steps 1–6 in that order and recomputes no earlier root after a
later one. The dependency graph is acyclic: StableCodeCatalog has only predecessor
schema/root edges; Catalog points only to frozen schemas/validators/vector;
Profile points to Catalog; obligation policy points to Catalog/Profile; Kernel
policy points to all final roots; bundle points to all assets. Vector and
validator leaves point to none of these roots.

The bundle exact-binds the dependency closure by asset identity, role, byte size,
and SHA-256. Inherited C/D roots are not opaque: every direct exact ref needed to
resolve and independently validate them is present.

The 27 schema assets are exactly:

- all eight common schemas;
- B `typed-terminal-result/1.0.0`;
- C `m1-contract-requirement-set/1.0.0`,
  `artifact-family-catalog/1.0.0`, `agentization-profile-release/1.0.0`, and the
  directly referenced fixture schema
  `fixtures/v2-contract-kernel/catalog-profile/1.0.0/synthetic-immutable-record/1.0.0.schema.json`;
- D 1.0 StableCodeCatalog and KernelValidationPolicy schemas;
- E 1.1 StableCodeCatalog and KernelValidationPolicy schemas;
- all six required E family schemas and the DiscoveryObligationPolicy schema; and
- exactly the three downstream support schemas
  `fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/entry-output/1.0.0.schema.json`,
  `fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/whole-scope-output/1.0.0.schema.json`, and
  `fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/derived-output/1.0.0.schema.json`.

The 15 contract/support assets are exactly:

1. C requirement root
   `contracts/v2/contract-kernel/requirements/m1-contract-requirement-set/1.0.0.json`;
2. inherited C Catalog root
   `fixtures/v2-contract-kernel/catalog-profile/1.0.0/catalog.synthetic.json`;
3. inherited C Profile root
   `fixtures/v2-contract-kernel/catalog-profile/1.0.0/profile.synthetic.json`;
4. inherited C vector leaf
   `fixtures/v2-contract-kernel/catalog-profile/1.0.0/family-conformance-vectors.json`;
5. D 1.0 StableCodeCatalog root;
6. D 1.0 KernelValidationPolicy root;
7. D's directly referenced vector leaf
   `fixtures/v2-contract-kernel/code-policy/1.0.0/code-policy-conformance-vectors.json`;
8. E 1.1 StableCodeCatalog root;
9. final E Catalog root;
10. final E Profile root;
11. final DiscoveryObligationPolicy root;
12. final E 1.1 KernelValidationPolicy root;
13. E family conformance-vector leaf;
14. canonicalization candidate golden vectors
    `fixtures/v2-contract-kernel/canonicalization-profile/2.0.0-candidate.1/golden-vectors.jsonl`; and
15. canonicalization provenance
    `fixtures/v2-contract-kernel/canonicalization-profile/2.0.0-candidate.1/provenance.json`,
    also used by mandatory fixture producer contexts.

Items 1–7 are the full inherited root/support closure: D policy points to D
catalog, D vector, C requirement/Catalog/Profile, B schema, and D validator; C
Catalog points to its vector, requirement schema, fixture schema, C validator,
and generic immutable-record validator; C Profile points to C Catalog; the
requirement root points to its schema and the inherited roadmap below. C and D
linkage metadata files are not referenced by a normative root and are therefore
not smuggled into the closure.

The 11 validator/source assets are exactly:

```text
src/agtxiv_v2/contracts/__init__.py
src/agtxiv_v2/contracts/canonical.py
src/agtxiv_v2/contracts/catalog_validation.py
src/agtxiv_v2/contracts/code_policy_validation.py
src/agtxiv_v2/contracts/code_policy_v1_1_validation.py
src/agtxiv_v2/contracts/diagnostics.py
src/agtxiv_v2/contracts/planning_validation.py
src/agtxiv_v2/contracts/references.py
src/agtxiv_v2/contracts/registry.py
src/agtxiv_v2/contracts/schema_validation.py
src/agtxiv_v2/contracts/terminal_validation.py
```

This explicitly includes B's terminal validator, C's validator, D's validator,
and the generic `schema_validation.py` directly named by C's synthetic family and
E's bundle Catalog row. The 3 specification assets are exactly the inherited
`docs/roadmaps/v2-end-to-end-implementation-plan.md` named by C's requirement
root, `docs/adr/0003-plan-discovery-scope-freeze.md`, and this committed plan.
Each carries exact Git commit/blob identity, raw byte size, and raw SHA-256 where
the specification-ref role requires it.

Manifest arrays are unique by `asset_id`. If an asset is reached through multiple
edges—C vector from two family rows, C Catalog from D policy and C Profile, B
schema from D and E policies, or one common schema from many family schemas—it is
listed once in its single role. Same bytes under a different asset ID do not
deduplicate and are rejected as an alias where C/D role rules forbid that alias.
A repeated asset ID with different bytes is a hard exact-ref conflict.

The exact candidate cardinality is therefore
$27 + 15 + 11 + 3 = 56$ unique asset refs. This is distinct from a byte ceiling.
Every canonical ref is at most 2,048 bytes; the bundle schema/constants/tests
freeze `exact_bundle_asset_refs = 56` and
`maximum_bundle_manifest_bytes = 131072`, derived as
$56 * 2,048 + 16,384 = 131,072$ for closed array keys/syntax. The actual
candidate's recomputed canonical manifest size must be **less than or equal to**
131,072 bytes; it is not required or expected to equal the ceiling. All manifest
bytes count within the 41,943,040 record and 134,217,728 aggregate limits. Every
inherited closure asset above is already committed before E, so none adds an
implementation path.

The bundle does **not** bind fixture records, synthetic source bytes, tracked
real-paper bytes, baseline, audit, demos, databases, or mutable paths. The plan
commit must exist before bundle construction so its Git blob and raw hash are
stable. Later records resolve their `contract_bundle_ref` to the bundle's full
exact-record identity and supplied raw bytes.

## 13. Candidate Catalog/Profile and fixtures

### 13.1 Candidate Catalog/Profile and conformance vectors

The non-production C/E roots are:

```text
contracts/v2/contract-kernel/catalog-profile/checkpoint-e/
  artifact-family-catalog/1.0.0-candidate.1.json
  agentization-profile-release/1.0.0-candidate.1.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/e-family-conformance-vectors.json
```

The vector asset identity is exactly:

```text
asset_id           vectors:checkpoint-e-planning-families/1.0.0
vector_set_id      vectors:checkpoint-e-planning-families/1.0.0
vector_set_version 1.0.0
fixture_purpose    STRUCTURAL_CONFORMANCE_ONLY
media_type         application/json
```

C requires `vector_set_id` to equal the supplied vector asset's `asset_id` byte
for byte; both are the exact versioned value above. They are not distinct logical
and asset namespaces.

The committed E requirement/Catalog/Profile/vector assets are authoritative input
bytes to C. Tests construct ordinary `RawContractAssetBinding` values for those
exact bytes and call `build_catalog_profile_constraints` directly with the exact
support tuple and registry. Success must be the builder-produced sealed
`CatalogProfileConstraints`. Rewriting vector metadata, substituting a surrogate
Catalog/Profile/vector, bypassing the public builder, constructing a private-token
object, or fabricating sealed constraints is forbidden.

It uses C's closed vector-set/row shapes. For every table row below it contains a
nonempty positive ID
`vector:checkpoint-e/<lower-family>/<lower-stage>/positive-valid` and a nonempty
negative ID
`vector:checkpoint-e/<lower-family>/<lower-stage>/negative-closed-or-binding`,
each with exact `FAMILY_CONFORMANCE` target family/version/stage/artifact kind.
The 12 exact IDs are:

| target | positive ID | negative ID |
|---|---|---|
| bundle/bootstrap | `vector:checkpoint-e/contract-bundle-release/contract-bootstrap/positive-valid` | `vector:checkpoint-e/contract-bundle-release/contract-bootstrap/negative-closed-or-binding` |
| snapshot/source-freeze | `vector:checkpoint-e/paper-source-snapshot/source-freeze/positive-valid` | `vector:checkpoint-e/paper-source-snapshot/source-freeze/negative-closed-or-binding` |
| Plan/planning | `vector:checkpoint-e/agentization-plan/planning/positive-valid` | `vector:checkpoint-e/agentization-plan/planning/negative-closed-or-binding` |
| Discovery/inventory-discovery | `vector:checkpoint-e/inventory-discovery-result/inventory-discovery/positive-valid` | `vector:checkpoint-e/inventory-discovery-result/inventory-discovery/negative-closed-or-binding` |
| Decision/scope-freeze | `vector:checkpoint-e/scope-freeze-decision/scope-freeze/positive-valid` | `vector:checkpoint-e/scope-freeze-decision/scope-freeze/negative-closed-or-binding` |
| Scope/scope-freeze | `vector:checkpoint-e/frozen-inventory-scope/scope-freeze/positive-valid` | `vector:checkpoint-e/frozen-inventory-scope/scope-freeze/negative-closed-or-binding` |

Every positive closed row contains exactly `vector_id`, `polarity = POSITIVE`,
`vector_kind = FAMILY_CONFORMANCE`, its exact target
`{family_id,family_version,stage_id,artifact_kind=IMMUTABLE_RECORD}`,
`template_id = template:checkpoint-e/<lower-family>/valid-record`, and
`expected_diagnostic_codes = []`. Every negative row has the same closed fields
with `polarity = NEGATIVE`, plus `mutation_id =
mutation:closed-or-exact-binding` and
`expected_diagnostic_codes = [AGTXIV.RECORD.PAYLOAD_INVALID]`. The six exact
template IDs follow the displayed family literal substitution and resolve in the
fixture test harness; IDs are sorted and disjoint. The candidate Catalog lists exactly those IDs and exact-refers to this
one asset for every family. Tests prove every listed ID resolves with correct
polarity/target and execute both vectors. The vector leaf has no Catalog/Profile,
policy, bundle, or fixture-record ref and therefore creates no cycle.

The Catalog has exactly these normative rows; every successful branch is
`IMMUTABLE_RECORD` and uses the corresponding required family record type/schema:

| family_id / version | group | stage | accounting unit | applicability / obligation | cardinality | producer roles | terminal policy |
|---|---|---|---|---|---|---|---|
| `CONTRACT_BUNDLE_RELEASE/1.0.0` | `CONTRACT` | `CONTRACT_BOOTSTRAP` | `CONTRACT_ASSET_INSTANCE` | `ALWAYS / CORE_REQUIRED` | 1..1 | `CONTRACT_BUNDLE_BUILDER` | `FORBIDDEN` |
| `PAPER_SOURCE_SNAPSHOT/1.0.0` | `SOURCE` | `SOURCE_FREEZE` | `PAPER_ATTEMPT` | `ALWAYS / CORE_REQUIRED` | 1..1 | `SOURCE_SNAPSHOT_BUILDER` | `FORBIDDEN` |
| `AGENTIZATION_PLAN/1.0.0` | `PLANNING` | `PLANNING` | `PAPER_ATTEMPT` | `ALWAYS / CORE_REQUIRED` | 1..1 | `PLANNING_PRODUCER` | `FORBIDDEN` |
| `INVENTORY_DISCOVERY_RESULT/1.0.0` | `INVENTORY` | `INVENTORY_DISCOVERY` | `PAPER_ATTEMPT` | `ALWAYS / CORE_REQUIRED` | 1..1 | `DISCOVERY_PRODUCER` | `FORBIDDEN` |
| `SCOPE_FREEZE_DECISION/1.0.0` | `REVIEW` | `SCOPE_FREEZE` | `PAPER_ATTEMPT` | `ALWAYS / CORE_REQUIRED` | 1..1 | `SCOPE_FREEZE_REVIEWER` | `FORBIDDEN` |
| `FROZEN_INVENTORY_SCOPE/1.0.0` | `INVENTORY` | `SCOPE_FREEZE` | `PAPER_ATTEMPT` | `ALWAYS / CORE_REQUIRED` | 1..1 | `SCOPE_FREEZE_ISSUER` | `STRUCTURALLY_PERMITTED: BLOCKED; PLAN_BOUND; reason deferred` |

Catalog stages are exactly `CONTRACT_BOOTSTRAP` ordinal 1/`PROFILE_BOUND`,
`SOURCE_FREEZE` 2/`PROFILE_BOUND`, `PLANNING` 3/`PLAN_BOUND`,
`INVENTORY_DISCOVERY` 4/`PLAN_BOUND`, and `SCOPE_FREEZE` 5/`PLAN_BOUND`.
The Catalog record type for each row is the lower-case family URI in Section 2;
validator ref is exact E `planning_validation.py` for the five planning records;
the bundle row uses the existing exact generic
`schema_validation.validate_immutable_record_payload` entry point plus E private
manifest cross-checking during bundle construction. The Profile mirrors all six rows as
`REQUIRED`, exact 1..1 cardinality, same role, and same terminal mode; it cannot
carry richer discovery obligations. `DiscoveryObligationPolicy` is deliberately
a support contract, not a seventh family. ContractBundleRelease is deliberately
a Catalog artifact because it is a successful immutable contract record.

### 13.2 Synthetic fixture

Synthetic raw source contains exactly:

```text
fixtures/v2-contract-kernel/planning-scope/1.0.0/source/main.tex
fixtures/v2-contract-kernel/planning-scope/1.0.0/source/appendix.tex
fixtures/v2-contract-kernel/planning-scope/1.0.0/source/binary.bin
```

The candidate fixture records include:

1. a complete snapshot and query-independent plan;
2. discovery with at least one classified, one ambiguous, and one unclassified
   component across the three files;
3. an ACCEPT decision and genesis scope retaining all three states;
4. a blocked-appendix discovery that still contains the appendix coverage row,
   a fallback `UNRESOLVED_SOURCE_REGION` component in the unclassified partition,
   `BLOCKED_WITH_EVIDENCE` coverage status, exact discovery error/evidence and a
   blocked obligation disposition, followed by BLOCK decision and typed terminal
   with no scope; and
5. revision-2 snapshot/plan/discovery/ACCEPT/scope plus supplied lineage and
   expected impact, exercising added, removed, classification-changed,
   whole-scope, direct, and transitive effects while preserving old bindings.

### 13.3 Tracked real-paper fixture

The real-paper fixture supplies exactly these nine already tracked files and no
archive expansion or ambient directory scan:

```text
Reference/The Resource Theory of Stabilizer Computation/source.tar
Reference/The Resource Theory of Stabilizer Computation/stab_resource_theory_021.tex
Reference/The Resource Theory of Stabilizer Computation/stab_resource_theory_021.bbl
Reference/The Resource Theory of Stabilizer Computation/Figures/4_1_2_total_mana_in_vs_expected_mana_out_standardized.png
Reference/The Resource Theory of Stabilizer Computation/Figures/5_1_3_total_mana_in_vs_expected_mana_out_standardized.png
Reference/The Resource Theory of Stabilizer Computation/Figures/8_1_3_total_mana_in_vs_expected_mana_out_standardized.png
Reference/The Resource Theory of Stabilizer Computation/Figures/norrell_state_labels_no_heatmap.png
Reference/The Resource Theory of Stabilizer Computation/Figures/slice_mana_heat_map_revised_color.png
Reference/The Resource Theory of Stabilizer Computation/Figures/strange_state_labels_no_heatmap.png
```

The fixture has snapshot, plan, discovery, ACCEPT decision, and frozen scope
records. Tests read those nine explicit paths only as test inputs; validators
receive bytes and never paths to open. `source.tar` is treated as one opaque
binary unit and is not unpacked. This proves only deterministic local planning
accounting over tracked bytes. It is not evidence or a claim of arXiv acquisition,
source authenticity, CAS insertion, archive safety, redistribution authority,
scientific completeness, runtime operation, or release.

## 14. Pure public seams and gate order

The exact public seams exported from `src/agtxiv_v2/contracts/__init__.py` are:

```text
validate_paper_source_snapshot
validate_agentization_plan
validate_inventory_discovery_result
validate_scope_freeze_decision
validate_frozen_inventory_scope
build_planning_scope_chain_declaration
validate_planning_scope_chain
compute_scope_revision_impact
validate_planning_terminal_constraints
```

No alternate permissive entry point is public. The aggregate seam is exactly:

```text
validate_planning_scope_chain(
  snapshot_raw: bytes,
  source_bytes_by_path: dict[str, bytes],
  plan_raw: bytes,
  discovery_raw: bytes,
  decision_raw: bytes,
  terminal_records_raw: tuple[bytes, ...],
  scope_records_raw: tuple[bytes, ...],
  predecessor_history: tuple[PlanningScopeChainDeclaration, ...],
  supplied_contract_assets: tuple[SuppliedAsset, ...],
  registry: ContractSchemaRegistry,
  bundle_raw: bytes,
) -> PlanningScopeChain | tuple[Diagnostic, ...]
```

The supplied terminal/scope tuples are complete-set declarations for this exact
plan/discovery/decision, not optional lookup pools. After validating each member
and rejecting duplicate record IDs or duplicate exact refs, BLOCK requires
exactly one matching terminal and zero scopes; ACCEPT requires zero terminals and
exactly one matching scope. Extra, stale, cross-plan, duplicate-byte/different-ID,
or duplicate-ID scope/terminal members fail. Genesis or BLOCK requires empty
`predecessor_history`; an ACCEPT successor requires the exact complete history
from Section 9.1 and validates it before the current chain. Only this aggregate
seam proves issuance cardinality, predecessor semantics, and branch consistency;
individual validators never claim absence from an unsupplied universe.

Each successful validator returns a detached sealed view; each failure returns a
nonempty deterministically sorted tuple of existing `Diagnostic` values. It never
returns a partially authoritative object.

The exact terminal seam is:

```text
validate_planning_terminal_constraints(
  record: ParsedCanonicalValue,
  registry: ContractSchemaRegistry,
  catalog_profile_constraints: CatalogProfileConstraints,
  kernel_policy_v1_1_constraints: KernelValidationPolicyV11Constraints,
  plan_raw: bytes,
  discovery_raw: bytes,
  decision_raw: bytes,
  supplied_contract_assets: tuple[SuppliedAsset, ...],
  bundle_raw: bytes,
) -> tuple[Diagnostic, ...]
```

A standalone caller obtains both sealed constraints only through
`build_catalog_profile_constraints`, the unchanged D 1.0 builder, and
`build_kernel_validation_policy_v1_1_constraints` over exact roots/supports from
`supplied_contract_assets`. The terminal seam checks exact class/token/seal and
requires each constraint's frozen refs to equal the supplied bundle manifest and
Plan Catalog/Profile/Kernel refs. It never constructs or accepts a private-token
surrogate.

`validate_planning_scope_chain` resolves the authoritative requirement,
C Catalog/Profile/vector/support, D 1.0 roots/support, and E 1.1 roots/support
from the exact bundle-bound tuple; calls the public C builder, D builder, and E
1.1 builder once each; and passes the resulting sealed objects through all
current/predecessor/terminal gates. It does not rewrite authoritative bytes.

The fail-closed order is:

1. exact host type, sealed-object integrity, per-input and aggregate byte
   preflight;
2. strict UTF-8/I-JSON parse: BOM, duplicate key, Unicode normalization collision,
   unsupported number, and nesting gates;
3. canonical-byte equality and closed schema/meta/registry validation;
4. immutable envelope, content hash, schema ref, and bundle ref;
5. exact-ref resolution against explicitly supplied bundle assets;
6. direct public C constraints from authoritative roots, then sealed D 1.0/E 1.1
   constraints from exact bundle-bound roots/supports;
7. record-local lexical, order, count, and resource checks;
8. source-byte digest/path/tree reconciliation;
9. plan exact binding and no-query/no-narrowing gate;
10. discovery source/component/obligation closure;
11. decision actor/declaration/finding and ACCEPT/BLOCK consistency;
12. complete predecessor-history semantic chains, then current scope issuance,
    identity, predecessor, and mechanical delta;
13. aggregate complete-set ACCEPT/BLOCK issuance consistency;
14. optional full old/new chain validation, lineage closure, and revision impact;
    and
15. C public terminal validation once (including its intrinsic B call), then the
    sealed 1.1 registration gate once, then exact planning bindings.

A failed earlier gate hard-stops dependent gates. After sealed-constraint and
bundle-ref checks, `validate_planning_terminal_constraints` calls the existing C
public terminal validator exactly once; C intrinsically calls B exactly once and
E never calls B directly. On C success it calls the 1.1 reason-policy gate exactly
once. That gate reads the actual registration row, allowed outcome/retry/context,
target, and reason from the sealed `KernelValidationPolicyV11Constraints`; it does
not compare only hard-coded `SCOPE_REASON`/target literals. Exact Plan/Discovery/
Decision bindings run last. Neither aggregate nor terminal code repeats C/B, the
1.1 builder, or the 1.1 reason gate for the same terminal.

## 15. Comprehensive test and adversarial matrix

### 15.1 Positive and exact-binding cases

- bundle validates as a `baseEnvelope` immutable record with normal content hash,
  manifest-only manifest hash, no self-ref, and a full resolvable exact-record ref;
- authoritative committed E Catalog/Profile/vector bytes, with versioned
  `vector_set_id == asset_id`, pass `build_catalog_profile_constraints` directly
  and return its genuine sealed constraints; all 12 vector IDs resolve and
  execute with correct polarity, family/stage target, template, mutation, and
  expected code;
- synthetic ACCEPT chain resolves every envelope, schema, bundle, Catalog,
  Profile, obligation policy, aliased resource policy, Plan, discovery, decision,
  and source ref;
- synthetic blocked-appendix BLOCK produces the exact registered terminal and no
  scope;
- revision 2 computes exact direct/transitive/whole-scope effects and leaves old
  bindings byte-identical;
- the nine-file tracked fixture validates twice with identical diagnostics,
  records, IDs, tree root, and scope;
- same bytes at two distinct valid paths share source-unit ID but have distinct
  `source_row_id`, component/anchor IDs, coverage rows, and scope-entry IDs;
- adding an unrelated canonical path in revision 2 changes the tree/snapshot/Plan
  refs but preserves every unchanged row's `source_row_id`, component ID,
  source-anchor hash, and scope-entry ID; only whole-scope outputs and genuinely
  affected lineage become stale;
- array and graph results are byte-identical under repeated validation.

### 15.2 Source identity and path attacks

Reject same-ID/different-bytes substitution; same `source_row_id` at different
paths; path-insensitive component/anchor/entry identity; source omission, addition,
reordering, mutation, truncation, extension, wrong size, digest, media type, count,
or root; duplicate path; absolute, drive, UNC, traversal, empty/dot segments,
backslash, NUL/control/format, trailing space/dot, device name, invalid UTF-8,
non-NFC, canonically equivalent Unicode, case-fold/Unicode-fold collision,
unpaired surrogate, and 1,024-byte path plus one. Verify root domain separation,
length framing, row order, empty-snapshot rejection, binary/NUL bytes, and the
unrelated-path stability vector. Mutating media type preserves byte-only `source_unit_id` and path/unit
`source_row_id`, but changes canonical row/tree/snapshot, component/anchor/entry
IDs, and descendant record bindings/hashes.

### 15.3 Plan independence and stale refs

Reject every named query field at every depth, synonym/nested selector injection,
path/family/region subset, added source unit, omitted expected unit, reordered
unit, reduced obligation, weakened cardinality, changed Catalog/Profile/policy,
wrong producer-context implementation/provenance role, `latest`, unresolved ref, same asset ID with changed
bytes, stale snapshot/tree/bundle, cross-bundle substitution, and legacy flat
`agtxiv.inventory-scope/2.0.0` in registry, Catalog, Profile, bundle, fixture, or
validator input.

### 15.4 Discovery closure

Reject missing/extra/reordered/duplicate coverage; component absent from coverage,
coverage ID absent from partitions, component in multiple partitions, duplicate
component ID, wrong tagged state, stale path/unit/digest/offset/slice/anchor,
out-of-range or boolean offset, duplicate anchor/kind, forbidden overlap,
dangling error/evidence, missing/extra/reordered obligation, insufficient
SATISFIED cardinality, wrong component kind, empty AMBIGUOUS/UNCLASSIFIED/BLOCKED,
and completeness claim without bidirectional closure. Specifically reject a
BLOCKED disposition with zero affected rows, zero relevant components, no
`BLOCKED_WITH_EVIDENCE` coverage row, a classified/non-UNRESOLVED fallback,
unmatched source row/region, one-way row/component/disposition/error links, or an
empty relevant error/evidence set. Confirm ambiguous and unclassified components
cannot be omitted or converted to ignored.

### 15.5 Decision and issuance consistency

Accept reviewable blocked-appendix fallback coverage, but reject a truly omitted
appendix coverage row before decision validation. Reject same actor ID, same or
forbidden role, missing actor-pair declaration,
undeclared conflict, conflict without finding, forged independence field,
stale plan/discovery/source/policy refs, >4,096 findings, ACCEPT with blocking
finding/conflict/terminal/incomplete discovery, or BLOCK without blocking finding.
For the terminal reject RECORD/Discovery basis, component projection unequal to
`plan_ref`, stale/wrong Plan obligation pointer, Discovery-producer or reviewer
attempt, role outside the C Profile issuer subset, `MANUAL_REVIEW` for BLOCKED,
missing/reordered Discovery and BLOCK-decision evidence, a decision back-ref to
the terminal, and wrong target/stage/outcome/reason/context/Plan/resources. At the
aggregate seam reject BLOCK without exactly one terminal, BLOCK with any scope,
ACCEPT with a terminal, ACCEPT without exactly one scope, duplicate IDs/refs,
cross-plan members, scope issued from BLOCK, and two scopes from one decision.
A standalone B fixture test runs the complete Section 8 vector through B
intrinsic. Separately, the E composition calls only C exactly once (therefore B
indirectly once),
with `SCOPE_FREEZE_ISSUER`, Plan COMPONENT basis, exact reason summary, three
ordered evidence rows/roles, `NO_RETRY_IN_CURRENT_CONTEXT`, `ESCALATE`, exact
description/responsible actor/role, `NO_DEADLINE` reason, and acyclic refs.
Resource tests independently delete/mutate each of the six `max_*` dimensions,
use a Kernel-policy key illegally, reorder/overlap/omit observed dimensions,
change observed `network_requests` to 1 over its zero limit, claim
`WITHIN_OBSERVED_LIMITS` with unobserved metrics, remove all unobserved metrics
without adding observations, and mutate every fixed budget value. Only
`observed={network_requests:0}` plus the five ordered unobserved metrics and
`relation=INDETERMINATE` passes. Lexical tests enforce the actual B namespaced-ID,
uppercase-role, dotted-reason, nonblank 1–2,048 text, and UTC/no-deadline branch
constraints for every frozen literal. Mutate the bundled 1.1 policy registration,
reason, target, outcome, retry/context set, predecessor ref, or support hash while
leaving hard-coded terminal literals unchanged; constraint building or the actual
1.1 gate must reject it. Forged/tampered `KernelValidationPolicyV11Constraints`
and constraints built from assets outside the exact bundle also fail before C.
Passing structural checks does not prove
identity, COI, signature, resource truth, or competence truth.

### 15.6 1.1 compatibility and bootstrap

Set E `vector_set_id` to the old unversioned value while keeping asset ID
versioned: direct `build_catalog_profile_constraints` must fail. Reject any
rewritten/surrogate vector or fabricated C constraint object. Reject each
immutable 1.0 predecessor-row mutation independently: code, meaning,
kind, ordinal, status, introduced version, deletion, insertion, or reorder; reject
wrong successor schema/version/revision/predecessor, code count/root maxima,
compatibility semantics, active/inherited exact refs, validator entry points,
vector refs, resource count/maxima, and inherited/new terminal registrations.
Reject wrong/missing predecessor, 1.1 row inserted before the end, extra reason,
reason in `DiagnosticCode`, unregistered reason, registration for another family,
stage, outcome, or context, `exact_support_assets != 3`, any individual support
maximum/sum mismatch, preliminary obligation-policy bytes, Kernel policy bound to
a stale Catalog/Profile/policy hash, wrong root construction order, and
bundle/reference cycles. Accept only the exact append-only reason and the
single-pass vector -> Stable catalog -> Catalog -> Profile -> obligation policy ->
Kernel policy -> bundle order. Reject bundle manifest count 55/57, manifest byte size 131,073, omission or role swap of any downstream schema, omission/substitution of
pre-existing `schema_validation.py`, and mismatch between manifest-only hash and
normal record content hash. Reject canonicalization-profile alias mismatch,
duplicate asset IDs across role arrays, same ID/different bytes, and counting a
multi-edge inherited asset more than once. The full pre-existing D test module must pass with
all original node IDs and assertions; removing either E mapping reproduces the
legacy helper failure, while adding unknown mappings, changing expected D values,
or admitting a non-1.0 schema fails the compatibility review.

### 15.7 Scope identity, revision, and affected sets

Reject missing/duplicate/reordered scope entry; omitted ambiguous/unclassified
entry; changed source binding under old entry ID; unstable unchanged entry ID;
wrong scope lineage seed; successor without predecessor; wrong revision number;
changed logical scope ID; stale predecessor; incorrect added/removed/classification
sets; overlapping delta sets; mutation of old plan/scope/entry bindings; omitted
whole-scope output; missing/extra direct or transitive descendant; dangling or
cyclic lineage; record with stale scope ref; and order-dependent closure. Cover
no-op successor rejection, classification-only preservation, source mutation new
ID, added-entry whole-scope impact, removed-entry direct impact, branched and
multi-parent transitive closure, and unaffected siblings. Reject a predecessor
scope whose intrinsic shape/hash is valid but whose embedded `plan_ref` is forged,
a predecessor declaration with mismatched snapshot/discovery/ACCEPT decision or
bundle, missing/reordered ancestry, genesis with nonempty history, successor with
empty/truncated history, history over 256, aggregate bytes over 134,217,728, and
impact attempted before both complete old and new chains pass the public semantic
gates.

### 15.8 Every limit and parser/host hostility

For every Section 3 limit, test exact limit reaches the next gate (and is accepted
where all cross-record invariants permit) while limit+1 is rejected before
expensive work: source files, path bytes,
single and total source bytes, obligations, components, component entry bytes,
findings, scope entries, record raw bytes, aggregate E input bytes, and exact ref
bytes. Boundary generators use structurally valid records rather than relying on
an earlier unrelated failure. The 16,384 scope-entry admission ceiling is
intentionally looser than this checkpoint's 8,192-component one-entry-per-
component closure: a 16,384-entry local shape must pass the scope-count preflight
then fail the later closure gate, while 16,385 fails preflight. E does not falsely
claim a valid 16,384-entry end-to-end chain.

For every public seam test `str`, `bytearray`, `memoryview`, custom subclasses,
bool-as-int, cyclic programmatic containers, forged sealed values, mutated private
slots, duplicate JSON keys, BOM, malformed UTF-8, noncanonical JSON, normalized
key collisions, excessive nesting, hostile `__iter__`/`__len__`/`__bytes__`, and
exception-raising objects. Exact built-in-type gates must prevent user code from
executing.

Monkeypatch filesystem open/stat/glob/walk, sockets/DNS/HTTP, subprocess, Git,
database connectors, environment, locale, and clock to raise sentinels; every
pure validator must still pass valid supplied inputs and return diagnostics for
invalid inputs without touching a sentinel. Repeat each representative valid and
invalid validation at least 100 times and require byte-identical results and no
input mutation.

## 16. Exact implementation allowlists

Only the paths below are authorized after this plan. Existing dirty/untracked
paths outside these lists are never staged.

### 16.1 Schemas and pure source implementation

```text
schemas/v2/contract-kernel/contract/contract-bundle-release/1.0.0.schema.json
schemas/v2/contract-kernel/contract/stable-code-catalog/1.1.0.schema.json
schemas/v2/contract-kernel/contract/kernel-validation-policy/1.1.0.schema.json
schemas/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0.schema.json
schemas/v2/contract-kernel/source/paper-source-snapshot/1.0.0.schema.json
schemas/v2/contract-kernel/planning/agentization-plan/1.0.0.schema.json
schemas/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0.schema.json
schemas/v2/contract-kernel/review/scope-freeze-decision/1.0.0.schema.json
schemas/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0.schema.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/entry-output/1.0.0.schema.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/whole-scope-output/1.0.0.schema.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/derived-output/1.0.0.schema.json
src/agtxiv_v2/contracts/planning_validation.py
src/agtxiv_v2/contracts/code_policy_v1_1_validation.py
src/agtxiv_v2/contracts/__init__.py
tests/unit/contracts/test_planning_schemas.py
tests/unit/contracts/test_planning_validation.py
tests/unit/contracts/test_code_policy_v1_1_validation.py
tests/unit/contracts/test_code_policy_validation.py
```

The existing `test_code_policy_validation.py` path is a compatibility-only test
exception. Its local `_registry()` helper currently globs every contract
`*/1.0.0.schema.json` but hard-codes only the five pre-E directory-to-asset-ID
mappings. The only authorized semantic edit is to add:

```text
contract-bundle-release       -> schema:contract-bundle-release:1.0.0
discovery-obligation-policy   -> schema:discovery-obligation-policy:1.0.0
```

If the helper is mechanically generalized, it may additionally ignore schema
filenames whose version is not exactly `1.0.0`, in sorted deterministic order;
the current exact-version glob makes that optional filter unnecessary. It may not
change imports, fixtures, D root/support bytes, assertions, parametrization,
expected diagnostics, test names/markers/order, or any D semantics. No D
production source, D schema/root/vector, `DiagnosticCode`, or C/B asset is
modified. The edit exists only so the legacy D test registry can coexist with the
two new E 1.0 contract-schema directories.

### 16.2 Candidate contract roots

```text
fixtures/v2-contract-kernel/planning-scope/1.0.0/e-family-conformance-vectors.json
contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.1.0.json
contracts/v2/contract-kernel/catalog-profile/checkpoint-e/artifact-family-catalog/1.0.0-candidate.1.json
contracts/v2/contract-kernel/catalog-profile/checkpoint-e/agentization-profile-release/1.0.0-candidate.1.json
contracts/v2/contract-kernel/planning/discovery-obligation-policy/1.0.0-candidate.1.json
contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.1.0.json
```

### 16.3 Bundle only

```text
contracts/v2/contract-kernel/bundles/checkpoint-e/1.0.0-candidate.1.json
```

### 16.4 Candidate records, fixture bytes, and fixture tests

```text
fixtures/v2-contract-kernel/planning-scope/1.0.0/source/main.tex
fixtures/v2-contract-kernel/planning-scope/1.0.0/source/appendix.tex
fixtures/v2-contract-kernel/planning-scope/1.0.0/source/binary.bin
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/snapshot-v1.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/plan-v1.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/discovery-v1.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/decision-accept-v1.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/scope-v1.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/discovery-blocked-appendix.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/decision-block-appendix.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/terminal-block-appendix.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/snapshot-v2.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/plan-v2.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/discovery-v2.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/decision-accept-v2.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/scope-v2.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/downstream-entry-output.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/downstream-whole-scope-output.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/downstream-derived-output.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/revision-lineage.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/synthetic/revision-impact.expected.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/real-paper/snapshot.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/real-paper/plan.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/real-paper/discovery.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/real-paper/decision-accept.json
fixtures/v2-contract-kernel/planning-scope/1.0.0/real-paper/scope.json
tests/unit/contracts/test_planning_fixtures.py
```

The tracked nine real-paper source paths are read-only fixture inputs and are not
in an implementation diff. No bundle bootstrap fixture/schema is implicit: the
bundle and downstream support schemas are in 16.1, all candidate contract roots
and the vector leaf are in 16.2, and the bundle root is the sole path in 16.3.
Except for the explicitly bounded legacy D test-helper path above, the allowlists
exclude D 1.0 production code/assets, B, `diagnostics.py`, registry/common/C
assets, legacy flat schemas, aggregate
validator, Reference bytes, demos, databases, slides, acquisition, CAS, runner,
API, archive, release, and knowledge code.

## 17. Seven-commit and independent-audit sequence

1. **Plan only:** add exactly
   `docs/roadmaps/v2-m1-contract-kernel-checkpoint-e.md`.
2. **Schemas/pure source:** change exactly the 19 paths in Section 16.1,
   including the three declared downstream support schemas and the narrowly scoped
   legacy D test-helper compatibility edit; no candidate roots, source/record
   fixtures, baseline, or audit.
3. **Candidate contract roots:** add exactly the six paths in Section 16.2,
   generated from commit 2 in the internal order vector -> StableCodeCatalog ->
   Catalog -> Profile -> DiscoveryObligationPolicy -> KernelValidationPolicy;
   no preliminary root is retained or rebuilt.
4. **Bundle only:** add exactly the one path in Section 16.3 after replacing plan
   and ADR refs with exact Git blob/raw hashes from committed bytes.
5. **Candidate records/tests:** add exactly the 27 paths in Section 16.4; fixture
   envelopes resolve the commit-4 bundle. Corrections to earlier assets require a
   new commit in that earlier category and a rebuilt downstream commit, never an
   audit rewrite.
6. **Pytest identity only:** update exactly
   `baselines/repository-validation/pytest/test-identity-v1.json`; collect twice
   byte-identically from the exact candidate-record commit and permit additions
   only from the three newly added Section 16.1 test modules and the one newly
   added Section 16.4 test module. The pre-existing
   `test_code_policy_validation.py` node IDs, markers, parametrizations, and
   collected order must remain byte-identical to the pre-E identity; any identity
   addition, deletion, rename, or reorder attributed to that compatibility edit
   blocks the baseline commit.
7. **Independent audit only:** add exactly
   `docs/audits/v2-m1-contract-kernel-checkpoint-e-2026-09-01.md` after independent
   adversarial and reader review has zero open Priority 0 or Priority 1 findings.

Implementation review occurred after the exact 19-path commit
`f75ba6f01f682b043e9d0dde6484ced0a8498a5a`. The corrective order is therefore
frozen without rewriting history:

1. a new plan-correction commit changes only this roadmap with message
   `docs(roadmap): correct planning scope composition`;
2. the immediately following implementation-fix commit changes only the minimal
   subset of paths already listed in Sections 16.1–16.4 needed for the four
   corrections; it adds no path and changes none of the 19/6/1/27 allowlist
   cardinalities; and
3. candidate-root, bundle, candidate-record, baseline, independent review, and
   audit completion proceeds only after that fix passes the corrected tests.

This correction commit precedes the final implementation-fix commit. It is not an
implementation or audit commit and does not retroactively amend the earlier plan
or implementation commits.

Before every commit, compare `git diff --cached --name-only` to that commit's
exact allowlist. Never use broad staging. No commit stages, rewrites, moves,
deletes, stashes, resets, or cleans unrelated user work.

## 18. Validation, review, and measurable Definition of Done

Validation is run in this order from exact commits with locked dependencies:

1. meta-validate and registry-resolve all E schemas;
2. run focused schema, planning, 1.1 policy, and fixture tests;
3. run `pytest -q tests/unit/contracts`;
4. generate pytest identity twice and compare bytes;
5. run `pytest -q`;
6. run `python tools/validate_repo.py --profile fast`;
7. run the ambient-I/O sentinel and deterministic repetition lanes;
8. independently inspect exact refs, hashes, closure algorithms, limit tests,
   allowlist diffs, and non-authority language; and
9. record exact commits, commands, counts, failures/skips, resource observations,
   known limitations, and review dispositions in the audit-only commit.

Checkpoint E is complete only when all are true:

1. the plan was committed alone before implementation;
2. each implementation commit equals its exact allowlist—commit 2 is exactly 19
   paths—and unrelated dirty or untracked paths are unchanged; the sole legacy D
   test edit only extends `_registry()` with the two exact E asset-ID mappings (or
   deterministic non-1.0 filtering) and changes no D assertion or semantics;
3. all six required family URIs are exact, closed, meta-valid, registry-resolved,
   and legacy flat `inventory-scope/2.0.0` is rejected without byte changes;
4. the bundle is a normal immutable record using existing `baseEnvelope`, normal
   record content hash, manifest-only `bundle_manifest_hash`, and no self-ref;
   every later record uses existing `contractBoundEnvelope` and resolves the
   bundle exact-record identity;
5. the non-production bundle candidate has exactly 56 unique refs, actual
   canonical manifest size no greater than the distinct 131,072-byte ceiling, and
   exact-binds the complete Section 12 inherited/E closure—including inherited
   roadmap, C fixture schema/vector/roots, D vector/roots, all validators, all
   three downstream schemas, and no candidate fixture record;
6. source rows, path profile, supplied-byte SHA-256 IDs,
   path/unit-only `source_row_id`, media-sensitive descendant IDs, and
   `AGTXIV_SOURCE_TREE_V1` vectors pass mutation, unrelated-addition stability,
   and limit tests without ambient lookup;
7. authoritative E requirement/Catalog/Profile/vector bytes—including exact
   versioned vector-set/asset-ID equality—pass
   `build_catalog_profile_constraints` directly with genuine builder-sealed
   constraints; the unchanged C Profile plus exact DiscoveryObligationPolicy
   deterministically project all obligations; the Plan exact-binds snapshot, Catalog/Profile,
   policy/resources with resource policy exactly aliasing final Kernel policy,
   expected source rows, and that projection; Plan environment/tools remain
   absent and deferred, and every query/narrowing case fails;
8. discovery source coverage, component partition, and obligation dispositions
   are bidirectionally total, with ambiguous/unclassified entries retained; every
   BLOCKED obligation has a nonempty affected `BLOCKED_WITH_EVIDENCE` row set,
   matched unresolved fallback components, and bidirectional exact error/evidence
   closure;
9. ACCEPT/BLOCK actor, conflict, terminal, and aggregate complete-set issuance
   rules pass—including ACCEPT exactly one scope, BLOCK zero scopes/one terminal,
   and duplicate rejection—while audit language explicitly disclaims
   identity/COI/signature truth;
10. BLOCK uses only `AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED` for
    `FROZEN_INVENTORY_SCOPE/SCOPE_FREEZE/BLOCKED/PLAN_BOUND`, is intrinsically B/C
    valid with issuer attempt, Plan COMPONENT basis, exact Discovery/Decision
    evidence, `ESCALATE`, complete six-dimension B ResourceBudget,
    observed/unobserved partition and `INDETERMINATE`, is checked against a
    genuine bundle-bound sealed 1.1 registration rather than hard-coded constants,
    and issues no scope;
11. D 1.0, B, D validator, C public validator, and `DiagnosticCode` bytes are
    unchanged; C is called once and intrinsically calls B once; the field-by-field
    1.1 successor projection, 80-entry/root-limit constants, registration, and all
    predecessor/successor mutation cases pass through the new module; the support
    tuple is exactly three enumerated assets totaling 44,056,576 bytes, and roots
    follow the one-pass Stable -> Catalog -> Profile -> obligation -> Kernel order;
12. path-sensitive source-row/component/anchor/entry IDs, stable scope lineage,
    predecessor/delta, and immutable old bindings match exact vectors; genesis
    takes empty history, successors take a complete sealed history of at most 256
    full ACCEPT declarations, and impact validates both old and new semantic
    chains before sealed lineage extraction, all-cycle rejection, whole-scope and
    least-fixed-point affected sets;
13. every Section 3 limit and limit+1 case, exact-hostile type, duplicate JSON,
    BOM/UTF-8, sealed-forgery, ambient-I/O, and repeated-determinism test passes;
14. the synthetic ACCEPT, blocked-appendix BLOCK, revision-2 impact, and exactly
    nine-file tracked real-paper fixtures validate and all candidate envelope refs
    resolve;
15. this plan-correction commit precedes a final implementation-fix commit whose
    path set is a subset of the unchanged allowlists, and focused, contract, full,
    and fast repository validation pass from the exact commits, or the audit faithfully identifies a pre-existing unrelated failure
    without treating E as complete;
16. pytest identity additions come only from the four newly added E test modules;
    the compatibility-edited legacy D test module has exactly its pre-E node set,
    markers, parametrizations, and order, and the baseline is committed alone;
17. independent adversarial and reader review has zero open Priority 0/Priority 1
    findings; and
18. the audit states **M1: NOT COMPLETE**, **M1.5: NOT COMPLETE**, and
    **AgtXIv V2: NOT COMPLETE**, with no acquisition, CAS, runner, API,
    SQLite/database, demo, release/archive/certification, merge, or knowledge-
    admission claim.

Completion authorizes only the next reviewed plan-only checkpoint. It does not
authorize production selection or protected-branch merge.

## 19. Assurance limits and deferred work

Pure validators can prove exact-byte, schema, reference, ordering, closure,
structural actor inequality, declared-conflict, and deterministic graph
properties over supplied inputs. Python monkeypatch sentinels are useful evidence
but do not prove OS-level isolation. Production sandboxing, syscall/network
containment, acquisition safety, signature/trust validation, real identity and
COI verification, and runtime quotas remain deferred.

Exact-limit vectors establish admission behavior, but CI-sized tests do not by
themselves establish acceptable CPU or peak memory at every 40 MiB record,
64 MiB source tree, 128 MiB aggregate, 4,096-file, 8,192-component, or
16,384-entry combination. Large exact-limit CPU/memory characterization remains
an assurance limitation and must be measured in a separately declared resource
environment before production use.

Also deferred are arXiv grammar and acquisition, safe archive extraction, CAS,
runner/workers, API, SQLite/PostgreSQL or any database, demo/UI, full paper
structure and claim production, formalization, signatures, release/archive,
certification, knowledge admission, migration of the legacy flat scope, and all
M1 families outside this checkpoint. No percentage-complete or coverage-numerator
claim follows from E.
