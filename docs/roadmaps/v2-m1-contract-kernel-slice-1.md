# AgtXIv V2 M1 contract-kernel slice 1

- Document status: implementation candidate; not implemented
- Milestone status: proposed first slice of M1; M1 remains incomplete
- Adoption status: requires implementation, tests, review, and a later exact
  `ContractBundleRelease` candidate
- User work-in-progress (WIP) status: no modified or untracked V2 WIP is adopted
  by this document
- Architecture basis: ADR 0001 through ADR 0006
- Parent roadmap: `docs/roadmaps/v2-end-to-end-implementation-plan.md`
- Date: 2026-08-31

This document defines the smallest safe M1 contract slice that can be built
without modifying or silently adopting the existing dirty V2 schemas, fixtures,
validator, tests, specification, demos, database prototype, or architecture
renderings. It is a design and commit plan, not implementation evidence. Passing
the future tests described here will establish only this contract-kernel slice;
it will not by itself complete M1, produce a Paper Agent release, certify an
archive, admit knowledge, or make the current static demo a real end-to-end
system.

## 1. Intuition

The contract kernel is the type system and lock file for the paper compiler.
Before a compiler accepts a program, it must know the exact language version,
headers, compiler rules, and target. Likewise, before AgtXIv produces a Plan or
claims whole-paper coverage, it must bind the exact schemas, canonicalization
rules, profile, catalog, policies, validators, and source snapshot that give
those records meaning.

The Plan-to-Freeze sequence has a second physical picture: inspecting a
building. The Plan identifies the building and the inspection standard. The
discovery producer surveys every room, including locked or ambiguous rooms. An
independent reviewer freezes the accepted floor plan. Only that frozen floor
plan is the denominator for later statements such as “all required rooms have a
disposition.” An ambiguous room can remain in the plan and be marked blocked;
it must not disappear merely because it is difficult to inspect.

The kernel therefore establishes two different orders:

```text
contract build order:
  canonicalization + schemas + policies + profile + validators
    -> ArtifactFamilyCatalog
    -> ContractBundleRelease candidate

runtime record order:
  exact source snapshot + exact contract bundle
    -> AgentizationPlan
    -> InventoryDiscoveryResult
    -> independent ScopeFreezeDecision
    -> FrozenInventoryScope
    -> artifact or TypedTerminalResult for each applicable obligation
```

The first order fixes what the rules mean. The second applies those fixed rules
to one exact paper release. Neither order may be reversed.

## 2. Isolation boundary and proposed new paths

Slice 1 uses a new versioned namespace. It does not edit the existing flat
`schemas/v2/*.schema.json` files or any file inventoried in
`docs/audits/v2-uncommitted-wip-reconciliation-2026-08-31.md`.

The proposed additions are:

```text
schemas/v2/contract-kernel/
  common/
    digest/1.0.0.schema.json
    exact-asset-ref/1.0.0.schema.json
    exact-record-ref/1.0.0.schema.json
    exact-component-ref/1.0.0.schema.json
    actor-identity/1.0.0.schema.json
    producer-context/1.0.0.schema.json
    immutable-record-envelope/1.0.0.schema.json
    resource-budget/1.0.0.schema.json
  terminal/typed-terminal-result/1.0.0.schema.json
  contract/
    agentization-profile-release/1.0.0.schema.json
    artifact-family-catalog/1.0.0.schema.json
    contract-bundle-release/1.0.0.schema.json
    contract-bundle-build-receipt/1.0.0.schema.json
    signature-policy/1.0.0.schema.json
  source/paper-source-snapshot/1.0.0.schema.json
  planning/
    agentization-plan/1.0.0.schema.json
    inventory-discovery-result/1.0.0.schema.json
    scope-freeze-decision/1.0.0.schema.json
    frozen-inventory-scope/1.0.0.schema.json

contracts/v2/contract-kernel/releases/0.1.0-candidate.1/
  canonicalization/record-json.profile.json
  errors/error-codes.json
  policies/kernel-validation.policy.json
  policies/signature-policy.json
  profiles/kernel-walking.profile.json
  catalogs/kernel-slice.catalog.json
  requirements/m1-required-families.json
  build/builder-input-manifest.json
contracts/v2/compatibility/prototype-2.0.0/
  quarantine-disposition.json

src/agtxiv_v2/contracts/
  __init__.py
  canonical.py
  diagnostics.py
  references.py
  registry.py
  schema_validation.py
  bundle_validation.py
  catalog_validation.py
  planning_validation.py

fixtures/v2-contract-kernel/releases/0.1.0-candidate.1/
  positive/walking/
  negative/<case-id>/
fixtures/v2-contract-kernel/normative/0.1.0-candidate.1/
  family-vectors/<family-id>/
fixtures/v2-contract-kernel/canonicalization-profile/2.0.0-candidate.1/
  golden-vectors.jsonl
  provenance.json

tests/unit/contracts/
tests/contract/v2_contract_kernel/
tools/validate_v2_contract_kernel.py
tools/generate_v2_contract_coverage.py
docs/contracts/v2-contract-kernel-0.1.0-candidate.1.md
docs/generated/v2-m1-contract-coverage.json
docs/generated/v2-m1-contract-coverage.md
```

The exact implementation may add `pyproject.toml` and `uv.lock` changes in the
first focused commit so that `src/agtxiv_v2` is installed as a real package.
Those files are not dirty V2 WIP at the time of this design. Slice 1 must not
wire itself into a concurrently modified aggregate validator; its standalone
command-line interface (CLI) and automatically discovered pytest tests are
sufficient until that
boundary is cleanly reconciled.

No existing V2 schema, fixture, validator, test, specification, architecture
file, demo, or database file is moved, reformatted, copied over, staged, or
treated as accepted by this plan.

## 3. Independent version strategy

AgtXIv has several independent version axes. They must not be collapsed into
the product name “V2”:

- software release, for example `v2.0.0-alpha.1`;
- contract-bundle release and revision;
- contract-kernel release train, beginning here at
  `0.1.0-candidate.1`;
- each schema family version;
- canonicalization-profile version;
- artifact-family-catalog revision;
- policy and stable-error-catalog revisions;
- record identity and immutable revision;
- paper work and exact arXiv version;
- run, attempt, source snapshot, plan, discovery, freeze decision, and frozen
  scope revisions.

The two version axes have different meanings:

- a **family schema version** answers “what is the shape and meaning of this one
  type?”;
- a **contract-kernel release version** answers “which exact collection of
  family schema versions, profiles, policies, validators, and catalogs is bound
  together?”

They are not required to advance together. New record families introduced by
this slice may start at `1.0.0`, for example:

```text
agtxiv.contract-bundle-release/1.0.0
agtxiv.agentization-plan/1.0.0
agtxiv.inventory-discovery-result/1.0.0
agtxiv.scope-freeze-decision/1.0.0
agtxiv.frozen-inventory-scope/1.0.0
agtxiv.typed-terminal-result/1.0.0
```

Their schema identifiers use an immutable namespace such as:

```text
https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0
```

A family path contains that family's version, while a contract instance path is
under `contracts/v2/contract-kernel/releases/<release-version>/`. A contract
release may therefore bind `AgentizationPlan/1.0.0` and a future
`MathClaimIR/2.1.0` without implying that either family has the release version
`0.1.0-candidate.1`. Conversely, changing one family to `1.1.0` requires a new
contract release even if every other family stays at `1.0.0`.

A schema byte change after inclusion in a contract bundle requires a new family
schema identity and a new bundle; it never replaces the old bytes under the same
URI. The software release number does not force all schema families to share the
same major version, and a common directory version never silently versions all
families as a unit.

## 4. Canonical JSON profile

The first contract asset is an exact canonicalization profile. It applies to
record semantics, not arbitrary paper bytes. It is intentionally a small,
project-specific profile rather than an imprecise claim of compatibility with a
larger canonical-JSON standard.

Its identity is exactly
`agtxiv.record-canonical-json/2.0.0-candidate.1`, mirrored by the single code
constant `PROFILE_ID` and the fixture directory
`canonicalization-profile/2.0.0-candidate.1`. The clean committed
`agtxiv.record-canonical-json/1.0.0` profile retains its original identity and
bytes; this breaking candidate neither overwrites it nor reuses its fixture
namespace.

### 4.1 Accepted input and parsing

1. The input is a byte string decoded with strict UTF-8. A byte-order mark,
   overlong/invalid UTF-8 sequence, or trailing non-whitespace byte after the
   single top-level JSON value is rejected.
2. The JSON parser retains object pairs in source order long enough to reject
   duplicate decoded keys before constructing a map. It must not let the host
   language silently keep the first or last duplicate.
3. A decoded key or string containing an unpaired UTF-16 surrogate is rejected;
   all accepted strings are sequences of Unicode scalar values.
4. The only accepted number token grammar is
   `0|-?[1-9][0-9]*`. Thus `-0`, leading-zero forms, a decimal point, and an
   exponent such as `1.0` or `1e0` are rejected at parse time even if a host
   parser would convert them to an integer-valued number.
5. An integer is accepted only in the Internet JSON (I-JSON) interoperable range
   `[-9007199254740991, 9007199254740991]`. There are no floating-point values,
   NaN values, or infinities in the record profile. A scientific quantity that
   needs a decimal, uncertainty, unit, or exact lexical form uses a typed
   string/object representation.

### 4.2 Semantic normalization

After parsing, normalization recursively produces a new value:

1. In every key and string value, each CRLF pair is replaced by LF and each
   remaining CR is replaced by LF.
2. The result is normalized with Unicode Normalization Form C (NFC).
3. Object keys are normalized by the same operation. If two distinct parsed
   keys become equal after normalization, the object is rejected.
4. `null`, booleans, and integers are unchanged. Array order is preserved.
5. The canonicalizer never guesses that an array is a set from a field name. A
   schema that assigns set semantics must declare a deterministic member key and
   ordering rule; its cross-validator rejects duplicate or out-of-order members.

### 4.3 Exact serialization

The normalized value is serialized without a byte-order mark, indentation,
insignificant whitespace, or a trailing newline:

1. `null`, `true`, and `false` use those exact lowercase ASCII spellings.
2. Integers use minimal base-10 ASCII with a leading minus only for negative
   values and no leading zeroes.
3. Arrays use `[` and `]`, commas between members, and preserve their declared
   order.
4. Object keys are sorted lexicographically by their sequence of Unicode scalar
   values after NFC normalization. Sorting occurs before JSON escaping and does
   not use locale, UTF-16 code-unit order, escaped spelling, or insertion order.
5. Objects use `{` and `}`, a colon between each key and value, and commas
   between members.
6. Strings are enclosed in ASCII double quotes. Quote and reverse solidus are
   escaped as `\"` and `\\`. U+0008, U+0009, U+000A, and U+000C use `\b`,
   `\t`, `\n`, and `\f`. Every other U+0000 through U+001F code point uses a
   six-byte lowercase escape `\u00xx`. Solidus is not escaped. All remaining
   Unicode scalar values are emitted directly as UTF-8, not as `\u` surrogate
   pairs or ASCII-only escapes.

### 4.4 Hash projections

An immutable record content hash is:

   ```text
   sha256(canonical_json({"envelope": ..., "payload": ...}))
   ```

The outer `content_hash` field is the only excluded field. No recursive search
removes a nested field with the same name. The envelope's schema, contract,
identity, revision, time, and provenance fields therefore remain committed by
the hash. A `content_hash` value is the lowercase string `sha256:` followed by 64
lowercase hexadecimal characters.

An `ExactAssetRef` hashes original asset bytes without JSON normalization. An
`ExactRecordRef` hashes the canonical record projection above. The two hashes
have different meanings and may not substitute for one another. Human-readable
Git JSON may be indented, but a replay bundle stores the canonical record bytes
defined by the profile. An artifact ledger may bind the pretty-printed source
bytes separately.

### 4.5 Mandatory golden vectors

`fixtures/v2-contract-kernel/canonicalization-profile/2.0.0-candidate.1/golden-vectors.jsonl`
stores each raw test input as base64-encoded UTF-8 bytes so duplicate keys and
lexical number forms survive the fixture loader. A positive row contains the
vector ID, input bytes, expected canonical UTF-8 bytes, and expected SHA-256. A
negative row contains the vector ID, input bytes, and exact stable error code.

The minimum positive vectors cover empty arrays/objects; `null` and booleans;
minimum, maximum, negative, zero, and multi-digit integers; ordered arrays;
object scalar-value key ordering; quote, reverse-solidus, control-character,
and solidus handling; raw non-ASCII output; CRLF/CR normalization; canonically
equivalent composed/decomposed Unicode; and the exact record hash projection.
The minimum negative vectors cover a byte-order mark, malformed UTF-8, trailing
data, duplicate decoded keys, a post-NFC key collision, an unpaired surrogate,
`-0`, leading zero, decimal/exponent forms, and both out-of-range integers.

`provenance.json` records the clean reference commit and exact clean blob hashes
from which any compatibility examples were minimally extracted. Those examples
contain only the smallest primitive values needed to test shared historical
behavior. They are not copies or adoptions of the original record semantics.
No byte from the current dirty WIP is an input to the golden vectors. New
profile-specific edge cases are authored independently and labelled as such.

The profile itself is a byte-addressed contract asset. A verifier has a small,
versioned bootstrap implementation of this exact profile and checks the profile
asset digest before loading the rest of the bundle. It does not resolve a
mutable “current profile.”

## 5. Immutable envelope and exact references

### 5.1 Record shape

Runtime records use a uniform shape:

```json
{
  "envelope": {
    "record_type": "agtxiv.agentization-plan/1.0.0",
    "schema_ref": {
      "asset_id": "schema:agentization-plan:1.0.0",
      "media_type": "application/schema+json",
      "byte_size": 1234,
      "sha256": "sha256:..."
    },
    "record_id": "agentization-plan:...",
    "record_revision": 1,
    "contract_bundle_ref": {
      "record_type": "agtxiv.contract-bundle-release/1.0.0",
      "record_id": "contract-bundle-release:...",
      "record_revision": 1,
      "schema_ref": {
        "asset_id": "schema:contract-bundle-release:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": 1234,
        "sha256": "sha256:..."
      },
      "content_hash": "sha256:..."
    },
    "created_at": "2026-08-31T00:00:00Z"
  },
  "payload": {},
  "content_hash": "sha256:..."
}
```

The common schema defines a base envelope and a contract-bound envelope.
`ContractBundleRelease` uses the base envelope because it cannot exact-reference
itself. Runtime records use the contract-bound envelope. A correction or new
interpretation produces a new immutable revision and an exact `supersedes_ref`;
an earlier revision is never updated.

### 5.2 Reference types

`ExactAssetRef` contains at least:

- stable asset ID;
- media type;
- byte size;
- raw-byte SHA-256;
- optional non-authoritative path hint or stable schema URI.

`ExactRecordRef` contains exactly the fields needed to resolve and type-check a
record:

- record type;
- record ID;
- record revision;
- exact schema asset ref;
- canonical content hash.

An `ExactComponentRef` extends an exact record ref with a stable component ID and
JSON Pointer. Component information is not an optional ad hoc property on the
base record ref.

Reference validation resolves a unique target and then checks type, schema
asset, revision, and hash. It never infers a target type from the parent field
name, substitutes a file found at the same path, resolves `latest`, fetches a
schema from the Internet, or follows a floating Git branch.

## 6. Contract bundle and catalog bootstrap boundary

Contract schemas, canonicalization profiles, policies, validators, human
specifications, error catalogs, migrations, and profiles are contract assets.
They are identified by raw byte hashes. The catalog is also a contract asset;
it does not exact-reference the bundle that contains it, which would create a
hash cycle.

The `ContractBundleRelease` manifest is built last and commits to:

- the canonicalization profile;
- every schema and its declared `$id`;
- the selected agentization profile and artifact-family catalog;
- policy and stable-error-code assets;
- cross-record validator and relevant adapter/migration bytes;
- catalog-referenced normative family conformance vectors;
- the locked M1 denominator and prototype-quarantine disposition;
- environment and dependency locks that affect interpretation;
- Git blob IDs and SHA-256 byte hashes for normative specifications;
- the signature-policy asset;
- the exact source Git commit, builder implementation asset, and pre-build
  builder-input manifest used to assemble the bundle.

The manifest does not include its own Git commit hash, because committing a file
that contains its containing commit hash is circular. The focused-commit plan in
Section 15 first commits all interpretation assets, then creates the bundle in a
later commit that points to that already fixed implementation commit and its
blob hashes.

The post-build `ContractBundleBuildReceipt` is deliberately outside the bundle
it reports on. Its schema and builder-input manifest are fixed in commit 1; the
receipt created in commit 2 exact-references the completed candidate, its content
hash, the pre-build input manifest, and the builder implementation. The candidate
does not reference that receipt. The hash graph is therefore one-way:

```text
candidate -> builder implementation + pre-build input manifest
post-build receipt -> candidate
```

This receipt can prove what the builder emitted without asking the output to
contain a hash of evidence that itself contains the output hash.

The initial manifest is a `CANDIDATE`, not a production-authorized release. It
may exercise structural and cross-record validation, but production mode must
reject it under the exact signature policy below. The schema must not make an
unsigned candidate appear equivalent to a signed production bundle.

### 6.1 Normative signature policy asset

`schemas/v2/contract-kernel/contract/signature-policy/1.0.0.schema.json`
defines the shape of a signature policy, and
`contracts/v2/contract-kernel/releases/0.1.0-candidate.1/policies/signature-policy.json`
is a mandatory normative asset of this candidate. The bundle exact-refers to its
raw bytes. The validator does not supply a default policy.

The schema has two disjoint modes:

1. `CANDIDATE_ONLY_UNSIGNED` requires `algorithm = NONE`, threshold zero, no
   trust roots, no signature envelope, `production_authorized = false`, and
   `allowed_bundle_lifecycles = [CANDIDATE]`.
2. `SIGNED_PRODUCTION` forbids `algorithm = NONE` and requires an exact signature
   envelope schema, algorithm/suite identifier, canonical signed-payload rule,
   domain-separation bytes, signature encoding, threshold/quorum, actor-role and
   key-usage rules, exact trust-root set, issuance/expiry policy, rotation policy,
   revocation and compromise evidence rules, historical verification time rule,
   and exact offline-verifier implementation asset.

The signed payload in a future production policy is an exact
`ContractBundleRelease` content hash plus the policy ID/version and domain
separator. The signature envelope is a separate immutable attestation that
binds that record ref; it is not inserted into the content whose hash it signs.
This avoids a signature/hash cycle. The production attestation family and the
choice of production cryptographic suite remain later M1 work and must receive
their own review.

The first candidate uses the first mode. Consequently, unsigned candidate
validation is a positive structural case, while every request for release,
runtime production authority, certification, archive, or admission returns the
stable failure `AGTXIV.CONTRACT.NOT_PRODUCTION_AUTHORIZED`. Replacing this asset
with a production policy necessarily creates a different bundle hash and
contract release.

### 6.2 Initial catalog scope

The first catalog declares `M1_KERNEL_SLICE_1` and covers only:

- `CONTRACT_BUNDLE_RELEASE`;
- `ARTIFACT_FAMILY_CATALOG`;
- `AGENTIZATION_PROFILE_RELEASE`;
- `PAPER_SOURCE_SNAPSHOT`;
- `AGENTIZATION_PLAN`;
- `INVENTORY_DISCOVERY_RESULT`;
- `SCOPE_FREEZE_DECISION`;
- `FROZEN_INVENTORY_SCOPE`.

`TypedTerminalResult` is a common way to account for another family's failed,
blocked, or not-applicable obligation; making it a recursively self-fulfilling
catalog obligation would be an error.

Each catalog family row declares:

- family ID, version, group, and exact schema asset;
- applicability policy and accounting unit;
- minimum/maximum cardinality;
- allowed producer role;
- successful record type;
- allowed terminal outcomes and reason codes;
- validator and positive/negative fixture refs;
- persistence mapping and retrieval route;
- review policy and visible surface, where applicable;
- maturity on the independent
  `CONTRACTED -> PRODUCED -> PERSISTED -> REVIEWED -> EXPOSED` scale;
- whether the family is required by the core profile.

### 6.3 Locked M1 coverage denominator

The slice catalog is not allowed to define the denominator by which M1 is judged.
The independent asset
`contracts/v2/contract-kernel/releases/0.1.0-candidate.1/requirements/m1-required-families.json`
has `denominator_id = agtxiv.m1-contract-denominator/1.0.0`, exact-refers to the
Git blob and SHA-256 of Section 6 of the parent roadmap, and stores an explicit
item list. The selection rule is “every row whose target-milestone cell contains
the exact milestone token `M1`”; the token `M1.5` does not match. Compound prose
is split as recorded below. Items may be record families, normative contract
assets, or named cross-record rules. A generator may not silently infer a
smaller set from the current catalog or selected profile.

The locked mapping is:

| Parent-roadmap Section 6 row | Exact denominator items | New unique count |
|---|---|---:|
| Contract | `CONTRACT_BUNDLE_RELEASE`, `AGENTIZATION_PROFILE_RELEASE`, `ARTIFACT_FAMILY_CATALOG`, `CANONICALIZATION_PROFILE`, `VALIDATION_POLICY`, `SIGNATURE_POLICY`, `STABLE_ERROR_CODE_CATALOG` | 7 |
| Intake | `PAPER_QUERY`, `WORK_RESOLUTION`, `SOURCE_ACQUISITION_REQUEST`, `SOURCE_ACQUISITION_RESULT` | 4 |
| Planning | `AGENTIZATION_PLAN`, `INVENTORY_DISCOVERY_RESULT`, `SCOPE_FREEZE_DECISION`, `FROZEN_INVENTORY_SCOPE` | 4 |
| Claims | `SCIENTIFIC_CLAIM`, `CLAIM_DECOMPOSITION`, `CLAIM_ATTRIBUTION_EVIDENCE`, `CLAIM_RECONSTRUCTION_EVIDENCE` | 4 |
| Mathematics | `NATIVE_MATH_CLAIM_IR`, `MATH_CLAIM_IR_BINDING`, `MATH_CLAIM_COMMON_READ_PROJECTION`, `MATH_COMPONENT_INDEX`, `RESIDUAL_SEMANTICS` | 5 |
| Reasoning | `INFERENCE_STEP`, `CLAIM_INFERENCE_GRAPH`, `MATH_CLAIM_DEPENDENCY_GRAPH`, `DEPENDENCY_FRONTIER_BLOCKER` | 4 |
| Formalization | `FORMALIZATION_REQUEST`, `GENERATED_FORMAL_PACKAGE`, `FORMAL_BUILD_RESULT`, `FORMAL_DECLARATION_GRAPH` | 4 |
| Assessment | `ASSESSMENT_RECORD`, `REVIEW_DECISION`, `SIGNED_ATTESTATION`; assessor, method, evidence, rationale, uncertainty, and independence are mandatory `ASSESSMENT_RECORD` facets | 3 |
| Release | `PAPER_AGENT_RELEASE_MANIFEST`, `ROOT_AUDIT`, `MECHANICAL_CERTIFICATE`, `REPLAY_BUNDLE`, `ARCHIVE_RECEIPT` | 5 |
| Knowledge | `KNOWLEDGE_CANDIDATE_ENTRY`, `KNOWLEDGE_RELATION`, `PER_ENTRY_ELIGIBILITY`, `ADMISSION_TRANSACTION`, `KNOWLEDGE_SNAPSHOT`, `KNOWLEDGE_INGESTION_RECEIPT` | 6 |
| Query | `QUERY_RESOLUTION`, `QUERY_EXACT_SNAPSHOT_BINDING_RULE`, `QUERY_CONFLICT_PRESERVATION_RULE` | 3 |
| Compatibility | shared `MATH_CLAIM_IR_BINDING`, plus `V1_MIGRATION_IMPORT_RECEIPT`, `V1_RECONCILIATION_REPORT` | 2 |
| Terminal | `TYPED_STAGE_FAMILY_TERMINAL_RESULT` | 1 |
| **Unique total** | `MATH_CLAIM_IR_BINDING` is counted once despite two roadmap mappings | **52** |

`PaperSourceSnapshot` is a slice-supporting source contract whose parent-roadmap
Source row is assigned to M1.5/M3, so it is reported separately and cannot
replace any of the 52 M1 items. `AgentizationProfileRelease` is both an explicit
catalog row and one of the 52 M1 denominator items; it cannot disappear into a
generic word such as “profile.”

An item counts as `CONTRACTED` only when its exact schema or normative rule,
stable diagnostics, positive fixture, negative fixture, and cross-record policy
are all in the bundle. Shared items count once. Profile applicability affects
runtime operational obligations, not this contract-coverage denominator. A
denominator revision requires a reviewed new requirements version, exact roadmap
mapping diff, and regenerated report; deleting an item to make the ratio green
is a coverage failure.

With the scope proposed here, the report is expected to distinguish all three
numbers:

```text
slice catalog rows: 8/8 contracted
whole-M1 locked denominator: 12/52 contracted; 40 listed gaps
supporting future-milestone contracts: PaperSourceSnapshot 1/1
```

A local 8/8 result must never be displayed as M1 completion. The expected 12
consists of the seven Contract items, four Planning items, and one Terminal item;
the generator must derive and verify this membership rather than accept the
number as a hard-coded success value.

## 7. `PaperSourceSnapshot` boundary

`PaperSourceSnapshot/1.0.0` is the immutable, consumer-facing input boundary for
the planning slice. It says which already frozen source bytes and promoted
source-tree entries the Plan sees. It is not an acquisition request, proof that
an arXiv endpoint was contacted, extraction-security audit, rights decision, or
replacement for the richer M1.5 source manifests.

### 7.1 Required payload

The payload contains:

- `paper_identity`: provider namespace, work ID, exact versioned ID, and numeric
  version where the provider has versions. An arXiv production value is the
  normalized versioned identifier such as `arxiv:2608.00001v1`; an omitted
  version is forbidden at this boundary because resolution must already have
  occurred.
- `source_mode`: exactly `SYNTHETIC_FIXTURE` or `ACQUIRED_SOURCE`.
- `production_eligible`: false for every synthetic snapshot; for an acquired
  snapshot it is policy-computed rather than caller-authored.
- `source_package_ref`: an `ExactAssetRef` to the raw downloaded archive, PDF
  fallback, or synthetic package, including media type, byte length, and
  raw-byte SHA-256.
- `source_tree`: the promoted safe tree, its tree-hash algorithm/version, root
  hash, and ordered entries.
- `extraction_policy_ref` and `execution_environment_ref`: exact assets that
  define how the promoted tree was produced.
- `rights_disposition_ref`: exact evidence governing retention, processing, and
  redistribution of the bytes.
- `provenance`: one of the two modes defined below.

The snapshot record's canonical `content_hash` commits all these fields. A URL,
original filename, or path hint is navigation metadata and never source
identity.

### 7.2 Source-package and tree hashes

`source_package_ref.sha256` is SHA-256 over the raw package bytes, before
decompression or normalization. In M1.5 those bytes live in content-addressed
storage (CAS); in this slice they are a small exact fixture asset.

Only regular, promoted, read-only files occur in `source_tree.entries`.
Directories are implied by paths. Absolute paths, empty segments, `.`, `..`,
backslashes, NUL, control characters, symlinks, hardlinks, devices, sockets,
case-fold collisions, and paths that are not valid UTF-8 NFC are not promoted.
The later extraction audit records each rejected archive member; omission from
the promoted tree does not erase it from acquisition evidence.

Each promoted entry contains exactly:

```text
path                 normalized relative POSIX path
entry_kind           FILE
byte_size            non-negative safe integer
sha256               hash of the exact file bytes
media_type           detected/declared media type
normalized_mode      REGULAR_READ_ONLY
```

Entries are sorted by the UTF-8 bytes of `path` after path validation. Duplicate
paths are rejected. `AGTXIV_SOURCE_TREE_V1` defines the root as:

```text
sha256(canonical_json([
  {path, entry_kind, byte_size, sha256, media_type, normalized_mode},
  ... in the required path order ...
]))
```

Filesystem inode numbers, ownership, host permissions, timestamps, directory
iteration order, and extraction location are not inputs. The validator
recomputes every available file hash and the root. If rights policy withholds
bytes, it reports that byte verification requires authorized bytes; it never
pretends that locator metadata reverified them.

### 7.3 Provenance modes

For `SYNTHETIC_FIXTURE`, provenance exact-refers to the fixture definition,
fixture-package bytes, and deterministic fixture builder. It must declare
`production_eligible = false`, uses the fixture provider namespace rather than a
fake arXiv identifier, and cannot authorize release, archive, or admission.

For `ACQUIRED_SOURCE`, provenance requires exact refs to the future M1.5
`WorkResolution`, `SourceAcquisitionResult`, `SourcePackageRecord`,
`PaperSourceManifest`, extraction audit, and rights disposition. It also binds
the acquisition endpoint policy and source-promotion decision. Production mode
accepts a snapshot only when those refs resolve under the same contract and the
source was safely promoted.

The acquired branch is schema-defined in slice 1 but has no fabricated positive
producer fixture. Its positive and adversarial producer coverage belongs to
M1.5. Until those upstream contracts exist, only the non-production synthetic
branch can pass this slice's walking tests.

### 7.4 Relationship to M1.5

M1.5 source records remain the authority for resolution, network acquisition,
quarantine, extraction decisions, source manifests, and rights. The snapshot is
a deterministic projection that exact-binds those records and exposes the
stable minimum consumed by `AgentizationPlan`; it never replaces or weakens
them. Changing any upstream source byte, exact version, manifest, extraction
policy, or rights disposition creates a new snapshot revision and makes prior
plans stale for the new revision.

## 8. Plan, discovery, decision, and frozen-scope contracts

### 8.1 `AgentizationPlan`

The plan freezes, before whole-paper analysis:

- the exact paper work, arXiv version, and `PaperSourceSnapshot`;
- exact contract bundle, profile, and catalog;
- query-independent discovery obligations;
- required source-unit, semantic-region, and component classes;
- required artifact families;
- resource and producer policies;
- producer identity and execution context;
- the source-tree root and its exact source-unit manifest.

An end-user query may schedule a new plan or stronger profile. It cannot remove
obligations from this canonical plan.

### 8.2 `InventoryDiscoveryResult`

The discovery result exact-references its plan and records:

- the observed source-tree root;
- every classified, ambiguous, unclassified, or rejected source component;
- coverage evidence for every source unit and required semantic region;
- extraction and discovery errors without deleting their targets;
- exact producer, tool, environment, resource-limit, and resource-consumption
  information;
- the producer's `COMPLETE`, `INCOMPLETE`, or `UNKNOWN` claim.

The producer's completeness claim is evidence. It does not authorize a frozen
scope.

### 8.3 `ScopeFreezeDecision`

The freeze decision exact-binds:

- plan, discovery result, source tree, profile, catalog, and policy;
- reviewer identity, actor kind, role, and qualification claim;
- producer/reviewer identity comparison;
- declared conflicts and independence evidence;
- findings, evidence, rationale, uncertainty, and non-implications;
- decision `ACCEPT`, `REJECT`, or `BLOCK`;
- review time and the attestation requirement/status.

The application validator rejects the discovery producer reviewing its own
result and rejects missing conflict/independence declarations. These fields do
not by themselves prove real-world independence; later authenticated identity,
authorization, and database constraints must enforce the production policy.

### 8.4 `FrozenInventoryScope`

A frozen scope may be issued only from an `ACCEPT` decision. It exact-references
the plan, discovery, and decision and assigns stable scope-entry identities.
Every profile-required discovery component appears exactly once, including
ambiguous and unclassified components. A stable entry identity is derived from
the plan ref, source locator, and discovery component identity rather than list
position.

This record is the only denominator for downstream family cardinality and
whole-paper accounting. A newly discovered component creates a new discovery,
decision, and scope revision. Old scopes and releases remain addressable, while
artifacts affected under the new scope become stale and must be regenerated or
receive explicit terminal dispositions.

### 8.5 Cross-record invariants

The pure validator enforces at least:

1. plan precedes and exact-binds discovery;
2. discovery observes the exact plan source tree;
3. every plan-required source unit/region is explicitly covered;
4. discovery producer and freeze reviewer satisfy the slice's identity and
   declared-conflict policy;
5. a frozen scope resolves to one accepted decision over the same exact plan,
   discovery, source, profile, catalog, and contract;
6. every required discovered component maps exactly once into the frozen scope;
7. ambiguity, rejection, and discovery errors cannot vanish at freeze;
8. all downstream targets exact-bind one frozen-scope revision;
9. a stale decision or mutated source/discovery cannot authorize a new scope;
10. completeness remains profile-relative and query-independent.

## 9. Typed terminal result

A terminal result is an evidence-bearing record, not an empty stand-in artifact.
It contains:

- exact target, stage, family, and obligation key;
- `terminal_for_attempt: true` and the attempt identity;
- outcome and stable reason code;
- non-empty evidence refs;
- retryability and the condition required for a new attempt;
- responsible actor and role;
- next action;
- resource limit and observed consumption;
- deadline when a pending external action has one;
- exact plan, scope, profile, catalog, and contract refs applicable at that
  stage.

The initial outcome vocabulary may include:

```text
UNAVAILABLE
RETRY_REQUIRED
REVIEW_REQUIRED
BLOCKED
FAILED
NOT_APPLICABLE
REFUTED
UNSUPPORTED
```

The cross-validator rejects:

- a family absent from the exact catalog;
- an outcome or reason not allowed for that family;
- a reason absent from the exact error catalog;
- `NOT_APPLICABLE` without applicability evidence;
- a terminal result without evidence, retryability, responsible actor, or next
  action;
- `UNSUPPORTED` as satisfaction of a required core obligation in production;
- interpreting `terminal_for_attempt` as a permanent scientific conclusion.

## 10. Walking contract example

The walking fixture uses an offline synthetic `PaperSourceSnapshot`, not a live
arXiv download and not an M1.5 acquisition claim. It uses the fixture provider
namespace, never a fabricated arXiv identity. Its exact source tree contains:

```text
main.tex          -> one theorem is discovered
appendix.tex      -> one supporting assumption is discovered
figure-1.pdf      -> semantic content remains ambiguous
```

`agent:discovery-A` produces the discovery result. `human:reviewer-B` reviews it.
The reviewer may accept the discovery as a complete profile-relative inventory
because `figure-1.pdf` has not disappeared: it is retained explicitly as an
ambiguous component.

The resulting `FrozenInventoryScope` has stable entries for all three units. A
later mathematical intermediate representation (IR) obligation for the figure
receives a terminal result:

```text
outcome: BLOCKED
reason: AMBIGUOUS_SOURCE_COMPONENT
evidence: exact figure/source/discovery refs
next action: named manual source-fidelity review
```

This fixture demonstrates the intended meaning of accounting completeness:
every room is present and receives a disposition; not every inspection
succeeds. It does not claim that a scientific assertion was verified, that a
formal proof exists, or that an entry is admissible to the knowledge base.

## 11. Positive and negative fixtures

Every contracted record family has at least one positive and one negative
fixture. Cross-record failures use a directory containing the complete minimal
record set plus `expected-error-codes.json`. Tests assert stable codes and JSON
Pointers, not fragile full English messages.

Positive fixtures include:

- standalone valid instances for every schema;
- an exact candidate bundle whose supplied assets all match;
- the complete bundle-to-plan-to-discovery-to-decision-to-scope chain;
- an ambiguous source component preserved into scope;
- the evidence-bearing terminal disposition described in Section 10.

Negative fixtures include at least:

| Case | Required failure |
|---|---|
| duplicate keys after NFC normalization | canonicalization rejects the object |
| non-integral JSON number | canonicalization rejects the value |
| stale asset or record hash | exact resolution fails |
| schema/type mismatch | reference type check fails |
| unresolved exact ref | no path/URI fallback occurs |
| `latest`, branch, or digest-free authoritative ref | contract validation fails |
| missing, changed, or duplicate bundle asset | bundle validation fails |
| candidate signature policy claims production authority | signature-policy validation fails |
| production mode receives the candidate-only policy | authorization fails closed |
| catalog row points outside the bundle | catalog validation fails |
| unknown family, outcome, or reason | terminal/catalog validation fails |
| required core family permits unrestricted `UNSUPPORTED` | policy validation fails |
| denominator omits, renames, or silently merges a locked M1 item | coverage generation fails |
| denominator roadmap blob differs without a reviewed denominator revision | coverage generation fails |
| synthetic source snapshot claims production eligibility | source validation fails |
| acquired source snapshot omits an M1.5 upstream ref | source validation fails |
| source package/file/tree hash differs | source validation fails |
| promoted tree contains traversal, link, collision, or non-canonical path | source validation fails |
| discovery omits `appendix.tex` | freeze cannot be accepted |
| discovery source root differs from the plan | discovery is stale/invalid |
| discovery producer reviews the freeze | independence policy fails |
| `REJECT` or `BLOCK` decision produces a scope | scope issuance fails |
| scope drops the ambiguous figure | coverage validation fails |
| source/discovery changes after review | prior decision becomes stale |
| terminal result lacks evidence/retryability/actor/action | terminal schema or policy fails |
| unsigned candidate used in production mode | authorization fails closed |

## 12. Pure validator package seam

The reusable package separates deterministic semantic validation from file and
command-line adapters. Its core functions are conceptually:

```python
parse_canonical_json(raw_utf8_bytes, profile) -> ParsedCanonicalValue | Diagnostic
canonical_bytes(parsed_value, profile) -> bytes
record_content_hash(parsed_record, profile) -> str
build_registry(schema_assets) -> ContractRegistry
validate_record(record, registry) -> ValidationReport
resolve_exact_ref(ref, record_index) -> record | Diagnostic
validate_contract_bundle(bundle, supplied_assets, mode) -> ValidationReport
validate_catalog(catalog, registry) -> ValidationReport
validate_planning_chain(records, contract_set) -> ValidationReport
```

Only `parse_canonical_json` accepts untrusted JSON bytes. It preserves the raw
pair and number-token information needed to enforce Section 4 before returning
an opaque `ParsedCanonicalValue`. `canonical_bytes` does not accept an arbitrary
host-language dictionary whose parser may already have discarded a duplicate
key or converted `1.0` to `1`. Internal programmatically constructed values pass
the same scalar/range/normalization checks through a separately named typed
builder before hashing.

The pure layer:

- performs no filesystem, network, clock, environment, database, or process
  access;
- does not mutate its inputs;
- receives all schema, policy, profile, catalog, record, and asset bytes
  explicitly;
- creates a JSON Schema registry only from supplied bundle assets and disables
  remote retrieval;
- rejects unknown schema IDs and duplicate IDs;
- returns user-data errors as deterministic diagnostics rather than uncaught
  exceptions;
- sorts diagnostics by stable code, subject identity, and JSON Pointer.

`tools/validate_v2_contract_kernel.py` is an I/O adapter. It safely loads an
allowlisted fixture/bundle directory, rejects traversal and symlink escapes,
calls the pure package, emits human-readable or JSON output, and returns a stable
exit code. It does not duplicate semantic checks.

The first compatibility tests use only the provenance-declared minimal clean
subset in the Section 4.5 golden vectors. They do not import the current dirty
V2 validator, copy its changed fixtures, or adopt its record semantics. Full
old/new validator agreement is a later M1 gate after the user WIP receives an
authorized disposition.

## 13. Stable diagnostic minimum

The exact error catalog is a contract asset. The initial stable codes should
cover at least these classes:

```text
AGTXIV.CANON.BOM_FORBIDDEN
AGTXIV.CANON.INVALID_UTF8
AGTXIV.CANON.INVALID_JSON
AGTXIV.CANON.DUPLICATE_KEY
AGTXIV.CANON.NORMALIZED_KEY_COLLISION
AGTXIV.CANON.UNPAIRED_SURROGATE
AGTXIV.CANON.UNSUPPORTED_NUMBER
AGTXIV.CANON.INTEGER_OUT_OF_RANGE
AGTXIV.REF.UNRESOLVED
AGTXIV.REF.HASH_MISMATCH
AGTXIV.REF.TYPE_MISMATCH
AGTXIV.CONTRACT.MISSING_ASSET
AGTXIV.CONTRACT.ASSET_HASH_MISMATCH
AGTXIV.CONTRACT.MUTABLE_REF
AGTXIV.CONTRACT.NOT_PRODUCTION_AUTHORIZED
AGTXIV.SIGNATURE.POLICY_INVALID
AGTXIV.CATALOG.UNKNOWN_FAMILY
AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED
AGTXIV.COVERAGE.DENOMINATOR_DRIFT
AGTXIV.SOURCE.PACKAGE_HASH_MISMATCH
AGTXIV.SOURCE.TREE_HASH_MISMATCH
AGTXIV.SOURCE.UNSAFE_PROMOTED_PATH
AGTXIV.SOURCE.PROVENANCE_INCOMPLETE
AGTXIV.PLAN.SOURCE_MISMATCH
AGTXIV.DISCOVERY.OMITTED_SOURCE_UNIT
AGTXIV.FREEZE.SELF_REVIEW
AGTXIV.FREEZE.NOT_ACCEPTED
AGTXIV.SCOPE.COVERAGE_MISMATCH
AGTXIV.SCOPE.STALE_DECISION
AGTXIV.TERMINAL.MISSING_EVIDENCE
```

Messages may become clearer without changing these meanings. Changing a code's
meaning requires a new error-catalog revision and contract bundle.

## 14. Existing `2.0.0` prototype quarantine

The current repository has flat V2 schemas and fixtures using `2.0.0` IDs. No
Git tag was observed in the M0 audit, but those IDs and bytes are already in Git,
and several working-tree files now have different bytes under the same IDs. It
is therefore unsafe to assume either that the IDs can be silently reused or that
the dirty bytes are authorized replacements.

Slice 1 applies this conservative policy:

1. Preserve the clean committed prototype bytes and Git blob identities from the
   audited reference commit. Never replace them in place.
2. Do not include current dirty or untracked V2 bytes in the new contract bundle.
3. Add a future, newly pathed compatibility asset at
   `contracts/v2/compatibility/prototype-2.0.0/quarantine-disposition.json` with
   initial status `AUTHORIZATION_PENDING`.
4. Until an authorized decision is recorded, old records are readable only
   through the legacy validator and cannot authorize new V2 runtime, release,
   archive, certification, or knowledge-admission state.
5. `agtxiv.inventory-scope/2.0.0` may at most seed a discovery proposal. It
   cannot become `FrozenInventoryScope` without a new discovery and independent
   freeze decision.
6. Old manifest values named `ADMITTED` or `CONDITIONAL` are conservatively
   treated as pre-archive accounting labels. They do not map to post-archive
   knowledge admission.
7. Old `MathClaimIR` may enter the future common projection only through ADR
   0005's exact, non-promoting binding.
8. An old audit or certificate without an exact contract bundle, replay root,
   signature/trust evidence, and required role separation cannot be promoted to
   a new certified release.
9. If the project later authorizes the old set as an unpublished prototype, its
   bytes and IDs still remain immutable and are superseded rather than reused.
   If evidence instead shows external release, the project must recover its
   exact contract inputs and provide an explicit migration/replay path.

This quarantine is a compatibility and safety boundary, not a judgment that the
prototype's scientific content is wrong.

## 15. Three focused commits

The split is determined by the hash graph, not only by topic. All bytes that can
change contract interpretation must exist in one already committed source
revision before a bundle can name that source revision. Files added after the
bundle are conformance evidence only and cannot be silently pulled into its
authority.

The three commits below are **sealing boundaries**, not a ban on smaller reviewed
implementation checkpoints before Boundary 1. For example, the canonicalizer
and its golden vectors may land first as an explicitly incomplete checkpoint.
Such a checkpoint has no bundle, release, production, archive, or admission
authority. Boundary 1 is reached only when the complete normative asset closure
listed below exists in one exact source revision; Boundary 2 may bind only that
closure revision. This preserves reviewable version history without weakening
the one-way hash graph.

### Commit 1: complete normative asset closure

Suggested message:

```text
Define isolated V2 M1 contract assets
```

Contents:

- all common, contract, source, planning, and typed-terminal family schemas;
- canonicalization, error catalog, validation policy, candidate-only signature
  policy, agentization profile, locked M1 requirements, kernel catalog, and
  prototype-quarantine normative assets;
- the exact pre-build builder-input manifest and the build-receipt schema;
- `src/agtxiv_v2/contracts` canonical, diagnostic, reference, registry, bundle,
  catalog, and planning-validation code;
- standalone CLI and deterministic candidate-builder code;
- schema/family-level positive and negative conformance vectors referenced by
  the catalog; these use explicit template inputs and do not pretend to be the
  later candidate-bound walking record set;
- package metadata/lock updates needed to install the `src` package;
- unit and golden tests for canonical bytes, hashes, exact refs, offline registry
  isolation, signature-policy modes, source-tree hashing, planning invariants,
  locked-denominator parsing, and stable diagnostics.

Commit 1's verification boundary is the normative asset set itself: every schema
is meta-valid, every catalog/requirements/profile/policy ref resolves within the
explicit supplied byte map, all asset SHA-256 values recompute, every pure test
passes, and the candidate builder can build and validate a temporary manifest
when given an explicit synthetic source-revision value. No committed
`ContractBundleRelease` candidate exists yet, and no test may skip merely because
that candidate is absent. The commit does not modify any existing V2 WIP path.

### Commit 2: exact contract-bundle candidate

Suggested message:

```text
Seal the first V2 contract-kernel candidate
```

Contents:

- one generated `ContractBundleRelease` candidate exact-binding the commit 1 Git
  commit, each normative asset's Git blob ID, and each raw-byte SHA-256;
- the candidate's canonical content-hash record;
- one external deterministic `ContractBundleBuildReceipt` exact-referencing the
  completed candidate/hash, commit 1 builder implementation, and pre-build input
  manifest; the candidate does not contain or reference this receipt;
- a candidate-verification test and expected machine report;
- no new or changed normative schema, canonicalizer, validator, profile, policy,
  catalog, requirement, migration/quarantine, or error-catalog byte.

Commit 2's verification boundary is the actual candidate: a clean checkout
rebuilds the same manifest/content hash from commit 1, verifies complete asset
closure without network access, accepts `CANDIDATE_ONLY_UNSIGNED` structural
validation, and rejects the same object in production mode. Because the bundle
points backward to commit 1 rather than to its containing commit, and only the
post-build receipt points forward to the completed candidate, there is neither a
Git-commit self-reference nor a candidate/receipt hash cycle.

### Commit 3: candidate-bound conformance evidence

Suggested message:

```text
Add V2 contract-kernel walking evidence
```

Contents:

- the complete walking contract record set exact-binding the commit 2 candidate;
- candidate-bound adversarial integration cases and expected stable codes;
- generated slice-versus-whole-M1 coverage reports;
- end-to-end fixture tests that invoke the already committed pure validators and
  CLI;
- the human-readable contract-kernel reference generated from the same assets.

Commit 3's verification boundary is conformance evidence: the walking chain and
all adversarial cases reach their exact expected results, the catalog reports
8/8, and the independently locked M1 denominator reports 12/52 with the 40 gaps
listed. Commit 3 must not change any byte named by the candidate. Tests,
generated reports, and explanatory documentation added here are not retroactive
contract assets. If they expose a defect in a normative validator or schema,
the defect is fixed in a new normative-asset commit followed by a new
superseding candidate; commit 2 is not rewritten.

Before every commit, staging uses an explicit path allowlist and checks
`git diff --cached --name-only`. No path inventoried as user WIP may appear.

## 16. Fail-closed exit criteria for slice 1

Slice 1 is implemented only when all of the following hold from a clean checkout:

1. package bootstrap, the focused unit/contract suites, and the repository's
   aggregate fast validation pass;
2. all new JSON Schemas are Draft 2020-12 meta-valid and resolve only through the
   supplied offline registry;
3. every mandatory Section 4.5 positive and negative golden-vector class is
   present, its provenance binds the minimal clean subset, and its canonical
   bytes/hash or stable rejection code is byte-stable across repeated runs;
4. every exact ref checks target type, schema bytes, identity, revision, and
   content hash;
5. missing, changed, duplicate, mutable, or remotely unresolved contract assets
   fail closed with stable codes;
6. family schema versions and the `0.1.0-candidate.1` release version are
   independently represented and no common directory implies a false shared
   family version;
7. the exact candidate-only signature policy is inside the bundle, validates as
   unsigned only for `CANDIDATE`, and deterministically rejects every production
   authorization request;
8. every slice catalog family has positive and negative fixtures;
9. the synthetic `PaperSourceSnapshot` package/file/tree hashes recompute, its
   unsafe-path cases fail, and it cannot claim production eligibility; the
   acquired branch cannot pass without all named M1.5 upstream refs;
10. the Plan→Discovery→Decision→Scope ordering and coverage invariants pass for
    the walking fixture;
11. omitted source units, producer self-review, stale decisions, scope mutation,
    unknown families, and evidence-free terminal results are rejected;
12. commit 1 verifies without a committed bundle, commit 2 reproducibly binds
    only commit 1 normative bytes, and commit 3 changes none of those bytes;
13. the generated report verifies the locked roadmap blob/mapping, reports slice
    catalog `8/8`, whole-M1 `12/52`, all 40 named M1 gaps, and the separately
    labelled `PaperSourceSnapshot` support contract;
14. no denominator/profile/catalog edit can reduce the 52-item M1 set without a
    new reviewed requirements revision and mapping diff;
15. no existing dirty V2 file is edited, staged, reformatted, or adopted;
16. a versioned checkpoint records exact commit, commands, test inventory,
    candidate bundle hash, known blockers, and the next M1 gap.

These criteria do not mark M1 complete. M1 still requires the remaining Section
6 families, rich native `MathClaimIR/2` and conservative V1 binding, graph and
`InferenceStep` kernel, complete assessment/review contracts, release/replay/
archive/admission state machines, validator compatibility across authorized V1
and V2 cases, full catalog coverage, and independent review. M1.5 then remains
responsible for the real-paper filesystem-CAS walking slice, safe acquisition,
offline replay, thin API/CLI/web surfaces, and production-shaped application
seams.
