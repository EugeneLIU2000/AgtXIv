# AgtXIv V2 paper agentization

**Status:** normative architecture and contract specification; implementation coverage is stated in Section 14.
**Version:** 2.0.0
**Authority:** this document is authoritative for V2 paper-agent construction, release, downstream queries, and migration. V1 remains authoritative only for its frozen bounded `ClaimMathBridge` / `BridgeAssessment` compatibility surface.

## 1. Normative objective

A V2 construction MUST produce a query-independent, release-centered Paper Agent package for one exact paper release. Its primary success criterion is complete disposition accounting relative to an exact `AgentizationProfile` and `InventoryScope`. Completion MUST NOT be represented as whole-paper truth, aggregate verification, scientific acceptance, or absence of unresolved entries.

The canonical order is:

```text
Exact Paper Release + AgentizationProfile + InventoryScope
→ profile-scoped whole-paper analysis
→ ScientificClaim and MathClaimIR records
→ formalization, evidence, alignment, and assessment records
→ independent release audit
→ certified Paper Agent Release
→ derived verification-aware Knowledge Base
→ read-only query resolution
```

Query-relative V1 bridge and mathematics-DAG workflows are downstream compatibility or retrieval workflows in V2; they are not canonical package construction.

## 2. Exact inputs

Construction MUST pin all three inputs before analysis:

1. an exact paper release identified by paper ID, release ID, source URI, resolvable local byte-artifact path, and SHA-256 hash of those exact bytes;
2. one exact `AgentizationProfile` revision and content hash;
3. one exact `InventoryScope` revision and content hash that references that profile and the same paper release.

Changing any pinned input creates a new construction and release identity. A title, mutable URL, query, or latest-version alias is insufficient.

## 3. Profile and inventory scope

`AgentizationProfile` defines required inventory classes, required artifact classes, and allowed dispositions. `InventoryScope` enumerates the source-bound entries for that exact profile and release. Each inventory entry MUST have a stable ID, class, source locator, resolvable component-byte path, and SHA-256 hash of those exact component bytes. The profile and scope MUST bind the same resolvable paper-release byte artifact. Profile conformance is evaluated only against these exact records; it makes no claim about obligations outside them.

## 4. Canonical construction

An `AgentizationCoordinator` performs profile-scoped analysis of the whole exact release, independent of any query. Canonical claim extraction MUST preserve source identities and anchors. `MathClaimIR` represents normalized mathematics but MUST NOT erase residual scientific semantics. Formalization, evidence, alignment, and assessment are separate record families with exact references; no family may silently promote another family's authority.

Every canonical artifact MUST identify its schema version, record revision, exact upstream references, and content hash. Canonical records MUST NOT reside only in a query-scoped namespace or be created as an unrecorded side effect of query execution. Every JSON record in a V2 release family MUST have a known 2.0.0 discriminator and pass its strict schema; unknown discriminators are invalid.

### 4.1 Canonical JSON and integrity projections

V2 reuses the compatible integer-only subset of `agtxiv.record-canonical-json/1.0.0` defined by `schemas/record-canonical-json-v1.profile.json`: UTF-8, CRLF/CR normalization to LF, Unicode NFC normalization of keys and strings, rejection of normalized duplicate keys, Unicode code-point key order, compact RFC-8785-compatible JSON literals, and SHA-256. V2 arrays preserve their declared order; non-integral numbers are outside this contract.

For every V2 record $r$, the authoritative record hash is

$$
\operatorname{RecordHash}(r)=\texttt{sha256:}\operatorname{SHA256}\bigl(\operatorname{CanonicalJSON}(r\setminus\{\texttt{content_hash}\})\bigr).
$$

Only the top-level `content_hash` is excluded. Validators MUST recompute it, reject stale values, reject duplicate `(id, record_revision)` identities, and resolve every exact reference by expected record type, ID, revision, and recomputed hash.

The release hash is acyclic. For manifest $m$,

$$
\operatorname{ReleaseHash}(m)=\texttt{sha256:}\operatorname{SHA256}\bigl(\operatorname{CanonicalJSON}(m\setminus\{\texttt{content_hash},\texttt{release_hash}\})\bigr).
$$

Construction first computes `release_hash` from that projection, inserts it, and then computes the manifest `content_hash` by the ordinary record rule. Audit, certificate, index, and query references are recomputed transitively.

Manifest artifacts have disjoint categories. A `RECORD` artifact is allowed only for an explicitly defined record class, and its path bytes MUST parse as the exact known typed JSON record whose class, schema `$id`, ID, revision, and recomputed content hash the artifact declares; file extensions have no authority. A `BYTE` artifact is allowed only for an explicitly defined byte class and MUST satisfy that class's ID, media type, path, and exact byte-hash binding. A Lean or arbitrary byte blob therefore cannot satisfy `MATH_CLAIM_IR` or `FORMALIZATION_RECORD`, even if renamed with a `.json` extension. Generated artifacts likewise use SHA-256 over exact file bytes. A manifest MUST NOT hash itself as a disposition-ledger artifact; the ledger is intrinsic to the acyclic manifest projection unless a separately hashed detached ledger is introduced.

The V1 legacy Root Agent is not reused as the V2 coordinator, auditor, certifier, or package authority.

## 5. Completion and dispositions

For inventory set $I$ and disposition ledger $D$, profile-relative completion is:

$$
\operatorname{Complete}(I,D) \iff \forall i\in I,\;\exists!d\in D\text{ with }d.\operatorname{entry}=i.
$$

Every in-scope entry MUST receive exactly one allowed disposition. No out-of-scope entry may occur. Mixed dispositions—including `ADMITTED`, `CONDITIONAL`, `BLOCKED`, `DEFERRED`, `NOT_APPLICABLE`, and `FAILED`—are permitted in one certified package. A release MUST NOT contain an aggregate `verified` Boolean or equivalent whole-package truth claim.

## 6. Formalization boundary

Autoformalization is represented only as `mode: AUTOMATED` on `FormalizationRequest`. The request pins an exact target component, a source boundary naming one exact in-scope `FORMALIZATION_TARGET` entry and its component-byte hash, requested artifacts, and a formal environment descriptor path plus SHA-256 byte hash. The descriptor MUST be valid UTF-8 TOML, repeat the request's environment ID, pin the Lean toolchain and commits, name the build command, and bind its project lock manifest by path and exact byte hash. `FormalizationRecord` MUST repeat those bindings, MUST name the same inventory entry as its release/admission identity, and owns only generated outcomes, artifacts, and generation diagnostics. Coordinated request/result equality cannot substitute for matching the independently scoped component bytes, environment descriptor bytes, or descriptor-bound project-manifest bytes.

Generation outcomes have mechanical artifact-accounting semantics. `SUCCEEDED` MUST contain exactly one byte-hash-valid artifact for every requested artifact kind. `PARTIAL` MUST contain a nonempty proper subset of requested kinds and nonempty diagnostics explaining the remainder. `FAILED` MUST contain no generated artifacts and nonempty diagnostics. No outcome may contain duplicate artifact kinds or an unrequested artifact.

A successful generation outcome does not imply kernel checking, proof validity, source alignment, applicability, acceptance, contract admission, or Knowledge Base admission. Verification, alignment, and acceptance fields are forbidden in `FormalizationRecord`; those conclusions belong to independent records and gates.

## 7. Role separation and release authority

The `AgentizationCoordinator`, `ReleaseAuditor`, and `ReleaseCertifier` MUST be three distinct actor identities. Self-audit, self-certification, or auditor/certifier identity overlap is invalid.

A passing audit contains exactly one passing instance of each mandatory check: `EXACT_INPUTS`, `TOTAL_DISPOSITION_ACCOUNTING`, `ARTIFACT_INTEGRITY`, `PROFILE_CONFORMANCE`, and `ROLE_SEPARATION`. Duplicate or omitted checks are invalid. The certifier binds one passing audit to the identical manifest and release hash. A `Paper Agent Release` certifies package integrity and profile/scope conformance only. It does not certify every entry as true or verified.

## 8. Package release and knowledge admission

Package certification and per-entry knowledge admission are separate gates. Certification may include blocked or failed entries. The Knowledge Base is a derived, verification-aware index over exact released records and their independent statuses. Its snapshot MUST bind the exact manifest and certificate; every admitted record MUST resolve by ID, revision, and content hash to an exact artifact in that manifest, retain that record's exact in-scope inventory-entry binding, and match the corresponding admissible ledger disposition. Reassigning a released record to another inventory entry is invalid. A snapshot MUST NOT admit the same exact record more than once or repeat an inventory-entry/record pair. It MUST preserve source release, record, environment, verification, alignment, blocker, and admission references. It MUST NOT flatten mixed states into package-level truth or admit an entry solely because its package is certified.

## 9. Query modes

`PACKAGE_BACKED` is the standard mode. It MUST use a certified release, perform read-only retrieval, and return exact record references from the release and derived index. It MUST NOT mutate or publish canonical records.

`PROVISIONAL_FAST_PATH` is explicitly non-authoritative. It may return provisional candidates, but every receipt MUST include an `agentization_trigger` with a stable intake ID and registration/running status, exact references to the `AgentizationProfile` and `InventoryScope` for the same exact paper release, and `scope_control: QUERY_INDEPENDENT`. The trigger starts or links the same standard canonical agentization process that would run without the query; the query MUST NOT narrow, replace, or otherwise control that profile or scope. The fast-path answer MUST NOT mutate canonical records, publish a release, admit an accepted contract, promote a Knowledge Base entry, or be cited as release evidence. Only the separately running query-independent construction and release cycle may produce those canonical effects.

## 10. V1 migration

Migration is dual-read/new-write:

- V1 `ClaimMathBridge` and `BridgeAssessment` remain immutable and readable under their V1 schemas.
- Existing query-relative mathematics graphs and Root Agent outputs remain legacy/downstream inputs with their original authority.
- All newly canonical paper-agentization records use V2 schemas and release identities.
- A V2 adapter may reference a V1 record by exact revision and hash, but MUST NOT rewrite it, infer V2 completion from it, or elevate its bounded conclusion.
- V1 schemas and discriminators MUST NOT be modified to emulate V2.

## 11. Machine-checkable invariants

A conforming validator MUST reject:

1. a manifest missing an exact profile or scope reference, or whose references do not resolve by ID, revision, and hash;
2. profile, scope, and manifest paper-release mismatch;
3. missing, duplicate, or out-of-scope ledger dispositions;
4. dispositions or artifact classes not allowed or required by the exact profile;
5. any aggregate field named `verified` at any depth in a V2 record;
6. coordinator self-audit, self-certification, or any overlap among the three release roles;
7. audit, manifest, certificate, or release-hash mismatch;
8. a `FormalizationRecord` containing verification, alignment, acceptance, admission, or promotion fields;
9. request/result target, boundary, mode, environment, revision, or hash mismatch;
10. package-backed query mutation/publication fields or non-read-only access;
11. a provisional receipt without an exact matching profile/scope agentization trigger, with query-controlled scope, or attempting accepted-contract admission or Knowledge Base promotion;
12. a package-backed query whose manifest/certificate/index references do not resolve exactly, or whose returned records are not admitted by that exact index and release;
13. a stale canonical record hash, stale byte-artifact hash, stale release hash, duplicate record identity, or unknown discriminator;
14. an unresolved or mistyped exact reference, absent formalization target component, malformed or duplicate manifest record-artifact identity, or knowledge admission outside the exact manifest;
15. a releasable record bound to an absent or wrong-class inventory entry, a Knowledge Index reassignment or duplicate admission, a scope entry class outside the exact profile, a missing required artifact class, or an incomplete/duplicate passing audit checklist.

Schema validation is necessary but not sufficient; cross-record checks are mandatory.

## 12. Contract locations

V2 JSON Schemas are under `schemas/v2/`. The positive contract family is under `fixtures/v2-paper-agentization/`. `tools/validate_v2_paper_agentization.py` validates schemas, exact references, local artifact paths, role separation, total accounting, formalization boundaries, release binding, and query authority.

## 13. Non-implications

Neither profile completion nor release certification implies whole-paper understanding, whole-paper truth, aggregate verification, scientific acceptance, correctness of every generated artifact, or Knowledge Base admission of every entry. Query success does not retroactively alter the package.

## 14. Implemented versus target

**Implemented in this repository:** ten strict V2 schemas covering profile, scope, MathClaimIR, manifest, audit, certificate, formalization, knowledge index, and query records; canonical record/release/byte hashing; a deterministic mixed-status fixture; transitive typed-reference and cross-record validation; adversarial tests; compatibility authority notes; and the V2 paper-first architecture artifact.

**Remaining V2 targets:** production whole-paper inventory extraction, canonical claim/evidence/alignment/assessment V2 registries beyond the fixture contract, cryptographic hashing/signing in a release service, independent operational actor authentication, production per-entry Knowledge Base admission, and end-to-end migration adapters for all V1 stores. These are targets, not implied capabilities of the present contract slice.
