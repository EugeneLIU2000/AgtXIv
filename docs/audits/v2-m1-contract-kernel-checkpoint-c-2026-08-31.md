# AgtXIv V2 M1 contract-kernel Checkpoint C implementation audit

- Audit status: INDEPENDENT READER REVIEW PASSED; CHECKPOINT C COMPLETE WITHIN PLAN-DEFINED SCOPE
- Checkpoint C scoped implementation result: COMPLETE WITH EXPLICIT LIMITS
- M1 status: **NOT COMPLETE**
- AgtXIv V2 status: **NOT COMPLETE**
- Audit date: 2026-08-31
- Plan commit: `521d17164d448613519b09dbbcc837755749dd6a`
- Intervening paper-lifecycle commit: `fad69a26c800e0cd433b30690d7c1378b46fea6e`
- Pre-C baseline catch-up commit: `ea807db076cd253c86cbc7104bf4e5334051cf32`
- Implementation commit: `89e2d1969c9065cc73fd94e210ff9c8754e27438`
- Baseline-only commit: `2f449e2d986e3f54c8cf376c36d0598b483be991`
- Parent roadmap source commit: `9d84dad47b7a92225686158f7bfc512f39332f2c`
- Runtime, release, protected-branch merge, archive, certification, database,
  knowledge-admission, and M1/V2 completion authority: none

## 1. Executive finding

Checkpoint C freezes an ordered 52-item M1 contract-requirement floor and adds
closed schemas plus pure offline cross-validation for an
`ArtifactFamilyCatalog` document and an `AgentizationProfileRelease` document.
A non-normative synthetic fixture demonstrates one-way exact-byte linkage:
Catalog binds already fixed schemas, validator sources, and vector-index bytes;
Profile binds the exact Catalog; a separate manifest binds all three root
assets without becoming a contract document or creating a hash cycle.

The scoped implementation and its exact committed tests pass. This does not
mean that a runtime Catalog or Profile has been published. In the type name
`AgentizationProfileRelease`, `Release` identifies a document type; it does not
assert that the synthetic instance has been released. The synthetic Catalog
and Profile must be read together with
`linkage.integration-fixture.json`, whose declarations are
`normative_status = NON_NORMATIVE`,
`fixture_purpose = STRUCTURAL_INTEGRATION_ONLY`,
`runtime_authority = NONE`, and `coverage_claim = NONE`.
They are not a production profile, coverage evidence, or runtime, merge,
release, review, or admission authority.

This audit deliberately makes no percentage or progress-numerator claim. The
52 items are a locked requirement set, not a count of completed contracts.
Independent reader review passed with `P0=0` and `P1=0`, so Checkpoint C is
complete within its plan-defined scope. Strong operating-system filesystem and
network isolation was not implemented for the recorded validation runs; that is
an explicitly reported assurance limit, not evidence of M1 or V2 completion.

## 2. Exact history and change boundary

The reviewed history is a linear chain:

| Commit | Exact parent | Role |
|---|---|---|
| `521d17164d448613519b09dbbcc837755749dd6a` | `9d84dad47b7a92225686158f7bfc512f39332f2c` | Checkpoint C plan only |
| `fad69a26c800e0cd433b30690d7c1378b46fea6e` | `521d17164d448613519b09dbbcc837755749dd6a` | Intervening paper-level audit and knowledge-lifecycle work |
| `ea807db076cd253c86cbc7104bf4e5334051cf32` | `fad69a26c800e0cd433b30690d7c1378b46fea6e` | Pre-C pytest-identity baseline catch-up only |
| `89e2d1969c9065cc73fd94e210ff9c8754e27438` | `ea807db076cd253c86cbc7104bf4e5334051cf32` | Checkpoint C implementation only |
| `2f449e2d986e3f54c8cf376c36d0598b483be991` | `89e2d1969c9065cc73fd94e210ff9c8754e27438` | Checkpoint C pytest-identity baseline only |

`fad69a2` is not part of the Checkpoint C implementation. It is a distinct,
intervening commit with 28 paper-lifecycle paths under the flat V2 schemas,
fixtures, specification, architecture, validator, and paper-agentization test.
None is in C's 14-path implementation allowlist. The subsequent `ea807db`
freezes those intervening test additions as the pre-C comparison baseline, so
C's test-identity delta is measured from that state rather than attributing
paper-lifecycle tests to C.

The implementation commit changes exactly these 14 authorized paths:

| Path | Change |
|---|---|
| `schemas/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0.schema.json` | add |
| `schemas/v2/contract-kernel/contract/artifact-family-catalog/1.0.0.schema.json` | add |
| `schemas/v2/contract-kernel/contract/agentization-profile-release/1.0.0.schema.json` | add |
| `contracts/v2/contract-kernel/requirements/m1-contract-requirement-set/1.0.0.json` | add |
| `fixtures/v2-contract-kernel/catalog-profile/1.0.0/linkage.integration-fixture.json` | add |
| `fixtures/v2-contract-kernel/catalog-profile/1.0.0/catalog.synthetic.json` | add |
| `fixtures/v2-contract-kernel/catalog-profile/1.0.0/profile.synthetic.json` | add |
| `fixtures/v2-contract-kernel/catalog-profile/1.0.0/family-conformance-vectors.json` | add |
| `fixtures/v2-contract-kernel/catalog-profile/1.0.0/synthetic-immutable-record/1.0.0.schema.json` | add |
| `src/agtxiv_v2/contracts/catalog_validation.py` | add |
| `src/agtxiv_v2/contracts/diagnostics.py` | modify |
| `src/agtxiv_v2/contracts/__init__.py` | modify |
| `tests/unit/contracts/test_catalog_profile_schemas.py` | add |
| `tests/unit/contracts/test_catalog_profile_validation.py` | add |

The implementation commit does not modify the plan, baseline, aggregate
validator, demo, database, roadmap, flat V2 paper-lifecycle work, or this audit.
The baseline-only commit changes exactly
`baselines/repository-validation/pytest/test-identity-v1.json` and no test or
contract asset. The current untracked `tests/test_demo_intake.py` is not in any
of these commits, is excluded from C's exact identity, and was not modified.
No stash or clean operation was used.

## 3. Mechanically recomputed raw-byte identities

The following sizes and SHA-256 digests were recomputed from raw blobs in the
exact implementation commit, not copied from an implementation report:

| Asset | Raw bytes | Raw SHA-256 |
|---|---:|---|
| M1 requirement-set schema | 5,365 | `sha256:b5a78cbe8502b1155d57b5cc7882d615f9db7bfa4fd63f5e4fd70508efd6416a` |
| ArtifactFamilyCatalog schema | 7,488 | `sha256:0f8d0f437759bff749b9402c5d02ffdb44efaa726104590b09acea23f5a1cd13` |
| AgentizationProfileRelease schema | 5,312 | `sha256:aa31a09ff70e62b4d162f0fee2d5cd8c30bf29fc34149e4ca414532a1db7d9fb` |
| Synthetic immutable-record schema | 1,578 | `sha256:7d589c3ff1227ef3c3d0545f2c9a6fe6594e4a10f2782aca297d494c679551d3` |
| Normative M1 requirement set | 12,775 | `sha256:b8c14e570f94934b56b0a0447c856d9d37eb2db9ede6aa6c191280ff618058f9` |
| Family-conformance vector index | 5,131 | `sha256:bb38f9c0df15ce9b1343ec1e33235f3d570bfe15ad68da32d8ee6f2fabb433e8` |
| Synthetic Catalog | 3,889 | `sha256:86958f085abf04e382c262d3e8aa9181039a565947b7dfd8e2153d39c4903be0` |
| Synthetic Profile | 1,770 | `sha256:e794945c8ca6c2c85d5da899f1e9773134c1b33e9a541b7550007f3167c2f8c9` |
| Non-normative linkage manifest | 757 | `sha256:54ef38d9cfe2dfc92d145f11a83786b0fca6df9ab41aadc6cb0a6956faba8071` |
| Checkpoint C Catalog/Profile validator source | 51,893 | `sha256:cf0835ce330e0f1b9468e30bd97f8d6160cb6c8e3382db6356210540e5ccb960` |

The raw-family Catalog row binds the C validator as asset
`validator:checkpoint-c-contract-documents:1.0.0`, media type
`text/x-python`, with entry point
`agtxiv_v2.contracts.catalog_validation.validate_m1_contract_requirement_set_intrinsic`.
The synthetic record row separately binds the inherited generic immutable-
record validator: 20,377 raw bytes,
`sha256:771b5758ef6a2425d0a03c73b7b57ee84063c890b156a21be1effd8dd3a5f1cb`,
and entry point
`agtxiv_v2.contracts.schema_validation.validate_immutable_record_payload`.
These validator roles are not interchangeable.

### 3.1 Roadmap source binding and requirement-set shape

The requirement floor binds the raw file
`docs/roadmaps/v2-end-to-end-implementation-plan.md` at commit
`9d84dad47b7a92225686158f7bfc512f39332f2c`. Independent Git-object and byte
recomputation produced:

| Source fact | Recomputed value |
|---|---|
| Git blob object | `sha1:782eb493c1ee28c6f61d5a07af30449b83183e08` |
| Full raw roadmap bytes | 50,302 |
| Full raw roadmap SHA-256 | `sha256:7419bc340471943b1e525974b558eb508d0deaf12455d5e12949db8a7d2be2f4` |
| Start heading | `## 6. Required artifact families\n` |
| End heading | `## 7. Mathematical formalization chain\n` |
| Selected LF byte slice | 3,136 bytes |
| Selected slice SHA-256 | `sha256:e50d851df655302106f3c1b5ec3f8462b9dc2dd0d12143c1b4e68bde483e4437` |

Exact-token selection of `M1` from 13 source rows yields 53 source occurrences.
One identifier, `MATH_CLAIM_IR_BINDING`, occurs in both Mathematics and
Compatibility, so the locked ordered set contains 52 unique items. Its kinds
are 6 raw contract assets, 43 immutable-record families, and 3 cross-record
rules. These are requirement-floor facts only; they are not a coverage
numerator, completion rate, contract-production result, or evidence that any of
the named families has been published.

## 4. Implemented validation boundary

The public C surface validates the requirement set, builds a sealed detached
Catalog/Profile constraint snapshot, and applies those constraints only after
Checkpoint B intrinsic terminal validation. The builder uses exact-type
preflight, raw size/hash binding, canonical direct-root schema validation,
closed reference resolution, requirement-floor comparison, Catalog coherence,
and Profile key/monotonicity checks. Every recognized byte enters through
explicit supplied assets; `path_hint` is display text, not a locator.

The synthetic graph demonstrates:

1. the requirement floor is a sibling root bound to fixed roadmap bytes;
2. Catalog binds fixed schema, validator, and vector-index assets;
3. Profile exact-binds Catalog; and
4. the manifest is built last, is not an API input, and is not referenced back
   by Catalog or Profile.

The vector document is a non-normative test-ID index. Production validation
checks its closed ID/target partition but does not execute test-only templates
or mutations. It is not self-contained production conformance evidence.

Tests include the schema-derived upper family boundary of 256 families, the
corresponding accepted support closure of 513 assets (one shared schema plus
two support assets for each family), and rejection of the 514th support asset.
Those are structural count boundaries. They do not turn the fixture into a
production Catalog and do not establish resource safety.

## 5. Exact pytest identity

Candidate generation was rerun twice against raw verified Git blobs from the
exact implementation commit. The two evaluation envelopes and the two
normalized `test_identity` objects were byte-identical. Recomputed evidence is:

| Evidence | Value |
|---|---|
| Normalized raw identity bytes | 368,791 |
| Normalized raw identity SHA-256 | `b163c6b245a8821f3e61490bb02027e0a9962d5f6cbd17fe6cc1cbe0adc5dbfe` |
| Domain-separated identity SHA-256 | `4fd491ab53bf246a3882471a1769d90c3718033be5dc047e25a4881172735143` |
| Full node-set SHA-256 | `fb5452e4d252a3b6691422f72cab745217215d1853bc6b8367b110dd6634a5e2` |
| Selected-order SHA-256 | `13febdc986cbfd07bfe4ed74333b1dd915197f81460594c242b17911cf5b4af9` |
| Collected / selected | `1210 / 1210` |
| Deselected / collection-skipped | `0 / 0` |
| Marker declarations | 20 |

Comparison with the exact pre-C baseline at `ea807db` found 197 additions, no
removals, and no reordering of the 1,013 old nodes:

| Only allowed new test file | Added nodes |
|---|---:|
| `tests/unit/contracts/test_catalog_profile_schemas.py` | 53 |
| `tests/unit/contracts/test_catalog_profile_validation.py` | 144 |

There are no additions outside those two files. The raw baseline digest in the
baseline-only commit is the same `b163…` value above, and that commit contains
only the baseline file. Runtime lock/distribution qualification reported
`LOCKED_RUNTIME_MATCHED`, but this is environment qualification, not branch,
review, merge, or release evidence. Its qualification scope explicitly excludes
operating-system filesystem and network isolation.

The untracked `tests/test_demo_intake.py` cannot enter this source-ref identity:
the identity collector reads verified committed blobs from `89e2d19`. Its tests
are visible only in the later dirty-worktree observation in Section 7.

## 6. Independent adversarial and reader review record

Only review outcomes, externally checkable changes, test probes, and finding
dispositions are recorded here; private reviewer reasoning is not.

| Review pass | Public result and disposition |
|---|---|
| Initial adversarial pass | Review-session-reported disposition: 3 Priority 1 and 3 Priority 2 findings; implementation was not accepted. These intermediate counts are not independently recomputable from committed blobs. |
| First correction pass | Review-session-reported disposition: 2 Priority 1 and 1 Priority 2 findings remained; implementation was still not accepted. These intermediate counts are not independently recomputable from committed blobs. |
| Final adversarial pass | `P0=0`, `P1=0`; all blocking findings were closed before `89e2d19`. |
| Final focused verification | 197 tests passed in the two allowed test files. |
| Final contract-unit verification | 685 tests passed. |
| Boundary review | The 256-family acceptance probe, 513-support-asset acceptance probe, and plus-one rejection probe passed. |

The remaining Priority 2 limitation is retained rather than promoted away:
the contracts do not freeze per-role byte budgets. The current implementation
also accepts a correctly exact-referenced validator source larger than 4 MiB.
Purity and totality on the finite, supplied in-memory values covered by the API
and tests do not imply bounded resource use for arbitrary input sizes, nor do
they defend against operating-system memory, CPU, file-descriptor, or other
resource exhaustion.

Reader feedback retained a Priority 3 interpretation guard: the `*Release`
suffix denotes a document type, not evidence that an instance has been
published. The synthetic Catalog and Profile are meaningful only together with
the `NON_NORMATIVE` linkage manifest. They are not a production Profile,
coverage evidence, runtime authority, merge authority, release authority,
review approval, or database/knowledge-admission credential.

Independent reader review passed with `P0=0` and `P1=0`. Its Priority 2 status
correction and two Priority 3 wording clarifications are incorporated in this
audit.

## 7. Re-execution evidence

### 7.1 Exact committed snapshots

Tests were run in temporary Git clones checked out at the exact commits, with
all locked dependency groups installed. These clones contained Git metadata so
Git-dependent tests exercised committed history; they were removed afterward.
No user working-tree file was copied into the snapshots.

At implementation commit `89e2d1969c9065cc73fd94e210ff9c8754e27438`:

```text
pytest -q tests/unit/contracts/test_catalog_profile_schemas.py \
  tests/unit/contracts/test_catalog_profile_validation.py
197 passed

pytest -q tests/unit/contracts
685 passed

pytest -q
1210 passed
```

An initial tar-only archive run also produced 197 focused passes, but its full
suite had 18 setup errors because `tests/test_provisional_claim_extractor.py`
requires a Git repository to read historical blobs. That unsuitable isolation
attempt is not represented as a product failure and is not used as full-suite
evidence. Re-running in an exact temporary Git clone fixed the missing
execution prerequisite without changing code and produced the 1,210-pass result
above.

At baseline-only commit `2f449e2d986e3f54c8cf376c36d0598b483be991`:

```text
python tools/validate_repo.py --profile fast
outcome=PASS
PASS=9 KNOWN_STALE=1 EXPECTED_BLOCKED=1 FAIL=0 MISSING_TOOL=0 SKIPPED=0
```

The retained `KNOWN_STALE` result is the historical immutable Shellworld V1
run. It must be superseded by a V2 contract-bound run rather than rewritten.
The `EXPECTED_BLOCKED` result states that pytest identity matched but collection
was not run with operating-system-enforced filesystem or network isolation.
The aggregate describes network as `offline-intended/preloaded` and
`OS-network-blocking=not-enforced`.

### 7.2 Dirty-worktree observations

The current working tree contains pre-existing modified and untracked user
work. Without modifying it, the following observations were made:

```text
full pytest: 1214 passed

fast aggregate:
  outcome=PASS
  PASS=9
  KNOWN_STALE=1
  EXPECTED_BLOCKED=1
  FAIL=0
  MISSING_TOOL=0
  SKIPPED=0
```

The four-node difference from the exact 1,210-node snapshot comes from current
untracked test work, including `tests/test_demo_intake.py`; it is not C identity
evidence and is not attributed to C. Dirty-worktree results are regression
observations only. They do not alter the exact implementation or baseline
claims.

## 8. Purity, totality, and threat/resource boundary

Tests place sentinels around filesystem, socket/DNS, subprocess, time,
environment, random, database, plugin, URL, Git, and mutable global-registry
access during the C APIs. Hostile exact-type, malformed, cyclic, deeply nested,
noncanonical, duplicate-key, same-ID/different-byte, and permuted-support cases
return deterministic diagnostics in the tested finite domain. Constraints are
recursively frozen, detached from supplied values, and sealed against
accidental mutation.

These facts establish a pure explicit-byte API under the tested in-process
boundary. They do not establish:

- per-role or aggregate byte budgets;
- termination or bounded memory/CPU consumption for arbitrary-size values;
- resistance to operating-system resource exhaustion;
- protection from arbitrary malicious code already executing in the same
  interpreter;
- a signature, authorization decision, or trusted execution environment; or
- OS-enforced filesystem or network isolation for the recorded commands.

Consequently, “pure” and “total” in this checkpoint must be read as behavior on
finite supplied in-memory values within the tested contract, not as a universal
bounded-resource guarantee.

## 9. Definition-of-Done evidence and limits

| DoD item | Evidence | Audit disposition |
|---:|---|---|
| 1. Plan precedes implementation | `521d171` is an ancestor of `89e2d19`, with the exact parent chain in Section 2. | Met. |
| 2. Implementation equals allowlist and preserves unrelated work | `89e2d19` changes exactly the 14 paths in Section 2; unrelated paper lifecycle and user WIP are outside it. | Met. |
| 3. Four schemas closed, meta-valid, registry-resolvable, and exactly pinned | Raw identities are recomputed in Section 3; focused schema and substitution tests pass. | Met for scoped schemas. |
| 4. Requirement floor exactly binds parent roadmap and yields reviewed ordered set | Exact commit/blob/full-file/section binding, 13 rows, 53 occurrences, and 52 unique items recomputed in Section 3.1. | Met as requirement-set integrity, not progress. |
| 5. One-way Catalog/Profile fixture graph uses real locally supplied bytes | Exact root and support identities plus manifest linkage recomputed; no reverse manifest edge. | Met for the synthetic graph only. |
| 6. Catalog family/stage/terminal policy passes vectors | Focused suite and final adversarial review pass, including artifact-kind and terminal boundaries. | Met for C's structural fixture; vectors are non-normative test metadata. |
| 7. Profile closure and monotonic rules pass matrix boundaries | Focused suite covers required/optional/not-selected, cardinality, role, outcome, and context rules. | Met for scoped validation. |
| 8. Reason registration remains deferred | Policy literal remains `DEFERRED_TO_EXACT_ERROR_CATALOG`; no ErrorCatalog path is added. | Met; stable reason meaning is still absent. |
| 9. Builder and terminal API enforce complete sealed snapshot and B-first validation | Constraint sealing, no-partial-return, mutation isolation, intrinsic hard-stop, and terminal-policy tests pass. | Met within the in-process threat boundary. |
| 10. APIs pure, total, deterministic, and non-authoritative | Ambient-I/O sentinels, hostile finite-input tests, repeated diagnostics, and no authority-like projection pass. | Scoped evidence met; arbitrary-size bounded resources and OS exhaustion are not proved. |
| 11. Focused, contract, full, and fast checks introduce no failure; environment limits reported | Exact results are 197, 685, 1,210, and aggregate PASS; dirty observations also pass. OS filesystem/network isolation was not enforced and is reported as an assurance limit. | Met. The plan requires honest environment-limit reporting, not stronger isolation as a completion prerequisite. |
| 12. Exact implementation identity generated twice and baseline-only committed | Two normalized identities are byte-identical; 1,210 nodes; exactly 53 + 144 additions; `2f449e2` changes only baseline. | Met; lock qualification is not branch evidence. |
| 13. Independent adversarial review has no open P0/P1 | Final review reports `P0=0`, `P1=0`; blocking findings were closed. | Met; retained P2 resource limitation remains explicit. |
| 14. Independent reader confirms interpretation and terminology | Independent reader review passed with `P0=0`, `P1=0`; its P2 status correction and P3 interpretation guard are incorporated. | Met. |
| 15. Audit preserves M1 incompleteness and non-authority | Header and Sections 1, 10, and 11 preserve `M1: NOT COMPLETE` and deny all listed authority. | Met. |

All 15 plan-defined DoD items are met. This scoped completion does not change
the explicitly weaker environment-assurance tier, complete M1 or V2, or grant
runtime, release, merge, database, or knowledge-admission authority.

## 10. Non-authority and remaining milestone state

Checkpoint C does not prove that any real Catalog or Profile is published or
selected. It does not prove Plan or frozen-scope applicability, actual
cardinality, obligation satisfaction, evidence relevance, actor authorization,
resource authenticity, successful-artifact non-conflict, reviewer
independence, scientific truth, signatures, release, merge, archive,
certification, or database/knowledge admission.

It does not grant authority to execute an arbitrary-arXiv runtime, merge to a
protected branch, release a Paper Agent, admit records to the standard database,
or treat terminal records as satisfied obligations. The arbitrary-arXiv demo,
Paper Agent DAG, complete V2 file generation, reviewed standard database, and
verifiable mathematical formalization chain remain future work.

**M1: NOT COMPLETE.**

## 11. Next checkpoint remains unselected

The roadmap leaves two candidate directions from which the next principle
review must select the smallest dependency-complete step:

1. design the exact stable-error catalog and validation policy needed before
   reason meanings can be registered; or
2. design `AgentizationPlan -> InventoryDiscoveryResult ->
   ScopeFreezeDecision -> FrozenInventoryScope` to create a paper-specific
   frozen denominator from reusable Catalog/Profile policy.

This audit does not choose between them. Selection requires the next design and
principle review; neither path is authorized merely by this scoped completion.
