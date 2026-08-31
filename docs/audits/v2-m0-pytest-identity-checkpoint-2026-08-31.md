# AgtXIv V2 M0 pytest identity checkpoint

- Date: 2026-08-31
- Branch: `codex/agtxiv-v2`
- Checkpoint result: exact collection identity `PASS`; aggregate
  `EXPECTED_BLOCKED`
- M0 exit status: **NOT COMPLETE**
- Scope: deterministic pytest collection identity and its local runtime
  qualification only

## 1. Intuition and boundary

This checkpoint freezes a ruler for the committed pytest suite. The ruler says
which test nodes exist, their execution order, which nodes are selected or
deselected, which collection skips and control markers exist, and which pinned
inputs define collection. A later collection can be compared with that ruler
byte for byte and digest for digest.

The ruler does **not** say that the tests passed. Test collection identity and
test execution are different questions:

- collection identity asks, “Did we collect the same tests under the same
  collection contract?”;
- test execution asks, “Did those tests run and pass?”

The checkpoint also qualifies the Python/pytest runtime against the locked
environment. That is not an operating-system sandbox. It does not prove that
network access was blocked, inputs were mounted read-only, credentials were
removed, or writes were confined. For this reason, the exact standalone check
passes while the repository aggregate deliberately remains
`EXPECTED_BLOCKED`.

## 2. Version chain

| Commit | Role |
|---|---|
| `b5fc9793bcf5b21207ab6c38f11ebd8f64b057a8` | Added the dormant aggregate gate, exact classifier, current-Git-commit (`HEAD`) source and baseline binding, and regression tests. No baseline was present yet. |
| `e44eea165ac21f974f9f1a21d6fbb1c83d2c77e2` | Baseline-only activation commit. It added only `baselines/repository-validation/pytest/test-identity-v1.json`. |
| `f18f66a8e4a54ea3816eafb5c435024b7f810bba` | Corrected the aggregate classifier so a backslash is forbidden in the repository path, but allowed in pytest's escaped parameter suffix. Existing test nodes were retained. |

The baseline was derived from the exact `b5fc979...` source snapshot. Adding
the baseline at `e44eea...` did not change `tests/`, `.python-version`,
`pyproject.toml`, or `uv.lock`. The `f18f66a...` regression changed existing
test bodies and a toy report fixture without adding or renaming a pytest node or
marker. Therefore the three commits reproduce the same portable test identity.

## 3. Baseline generation and reproduction

The abbreviated source commit was first resolved to its full object identifier:

```bash
git rev-parse b5fc979^{commit}
```

The candidate was then collected twice by the validator from verified raw Git
blobs of that exact commit:

```bash
.venv/bin/python tools/validate_pytest_inventory.py \
  --candidate \
  --source-ref b5fc9793bcf5b21207ab6c38f11ebd8f64b057a8
```

Only the emitted `test_identity` object became the baseline. The evaluation
envelope, host runtime, platform, installed distributions, source commit, and
manifest digests were deliberately excluded. The object was serialized with
sorted keys, ASCII JSON escaping, compact separators, and exactly one terminal
line feed. A second exact-source candidate was generated independently and was
both semantically and byte-for-byte equal after the same serialization. The
baseline also passed its Draft 2020-12 JSON Schema.

This separation avoids self-reference. The baseline does not contain the hash
or commit that contains itself; the later evaluation envelope binds the frozen
baseline bytes to the source commit instead.

After activation and classifier correction, the real source-backed comparison
was:

```bash
.venv/bin/python tools/validate_pytest_inventory.py \
  --check baselines/repository-validation/pytest/test-identity-v1.json \
  --source-ref f18f66a8e4a54ea3816eafb5c435024b7f810bba
```

Observed result: exit `0`, operation `CHECK`, outcome `PASS`, and no errors. The
report bound the raw baseline to Git blob
`bcdd171560b9cf22080aa578de3da8198491a7dc` and bound the validator bytes to the
same source commit. Its assurance tier remained
`COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC`.

## 4. Reviewed identity

### Digests

| Item | SHA-256 |
|---|---|
| Raw baseline JSON bytes | `bb3b4e7830066ad2ba1d25e1cb5e71f5ac1987a5d2d8b05cc26d711efcc491c8` |
| Domain-separated test identity | `b5dd6a9b905d17a8922ec72894698943daa71c1ac24cbec583504364ad2e8824` |
| Full collected node set | `743ef3a88c928141f4f9cf9b4ad3d13c54a47f96daf974b5421cdc13fb76f68a` |
| Selected execution order | `ba32be3fb7a9834bf9bf5bc4b277227c6e11c77d330ac174fbd1ec59c6f7f182` |

### Counts

- collected: 634;
- selected: 634;
- deselected: 0;
- collection skips: 0;
- recorded control-marker declarations: 20.

The marker declarations are part of identity, not proof that every host will
take the same branch. If a recorded platform-dependent condition evaluates
differently, comparison fails closed instead of silently changing the suite.

### Exact input bindings

| Input | Bytes | SHA-256 |
|---|---:|---|
| `.python-version` | 7 | `657062bd6c016c431fe7658173ba3611697eeb21357fd82faef0b7d21a491c3f` |
| `pyproject.toml` | 485 | `9efdd10f5600f6f1e8c6a53ddd7d611ca3d2c2df99f5e849fef17dd4529c42b7` |
| `uv.lock` | 26,899 | `7b00fca95f0dc383b4061934c58d8a1d05ef790d5b96ab80cbca15a6f5a4fba7` |

## 5. Test-execution observations

These are separate observations and are not fields in the collection baseline:

```bash
.venv/bin/python -m pytest -q \
  tests/test_validate_pytest_inventory.py tests/test_validate_repo.py
# 248 passed

.venv/bin/python -m pytest -q
# 676 passed
```

The targeted result covers the two validators and their adversarial tests. The
676-pass result was observed in the primary working tree, which also contained
pre-existing user work in progress. It is useful local execution evidence, but
it is not presented as a clean `f18f66a...` branch test result. The reviewed
exact commit identity contains 634 collected nodes; the different number is not
a contradiction because the two figures have different source boundaries and
because “collected identity” and “passed executions” are distinct evidence.

## 6. Runtime qualification is not isolation

The real report returned `LOCKED_RUNTIME_MATCHED` with qualification scope
`VERSION_LOCK_AND_INSTALLED_DISTRIBUTION_MATCH_NOT_OS_OR_NETWORK_ISOLATION`.
It checked the locked Python, pytest, pluggy, uv, and installed distribution
versions, and it recorded a complete platform record. The platform record is an
observation, not a cross-machine platform lock. This runtime qualification is a
required check; excluding host details from the portable baseline does not
waive it.

The same report also stated:

- `filesystem_isolation_enforced: false`;
- `network_isolation_enforced: false`;
- `branch_evidence_eligible: false`.

The repository-level command was:

```bash
.venv/bin/python tools/validate_repo.py \
  --profile fast \
  --only pytest-test-identity \
  --json-report -
```

At `f18f66a...`, its child exited `0` with outcome `PASS`, every exact-report
predicate matched, and the aggregate result was intentionally:

```text
EXPECTED_BLOCKED
UNSANDBOXED_PYTEST_COLLECTION_NOT_BRANCH_EVIDENCE
```

The aggregate recorded `admission_eligible: false`,
`security_gate_eligible: false`, `branch_evidence_eligible: false`, and
`m0_completion_effect: NONE`.

## 7. Real-report classifier defect and repair

The first real aggregate run at `e44eea...` exposed a classifier defect. The
standalone child exited `0` with outcome `PASS`, but the aggregate returned
`FAIL` with `exact_diagnostic_report: false`.

The cause was narrow and reproducible. The aggregate helper
`_is_exact_node_id` rejected a backslash anywhere in a node ID. In the reviewed
identity, 32 selected parameterized nodes contain pytest's stable literal
escapes such as `\\n`, `\\r`, `\\u...`, or `\\x...` after the first `::` node
separator, in the test or parameter suffix. The normative standalone validator
and schema forbid backslashes in the repository file path, but allow them in
this suffix. Every other
identity, runtime, source, baseline, validator, HEAD, and protected-hash
predicate passed.

Commit `f18f66a...` moved the backslash restriction to the path portion only.
It retained rejection of a backslash in the path, real carriage returns and
line feeds, a zero byte (`NUL`), non-normalized Unicode, absolute paths, empty
components, and `.` or `..` path components. Its regression coverage reused
existing test nodes, so the approved baseline identity did not need to change.

Independent reader results were:

Here P0, P1, and P2 mean critical, major, and minor review findings,
respectively.

- baseline artifact review: P0 = 0, P1 = 0, P2 = 0;
- `e44eea...` real-report diagnosis: P0 = 0, P1 = 1, P2 = 0, with the sole P1
  being the suffix-backslash classifier mismatch;
- `f18f66a...` repair review: P0 = 0, P1 = 0, P2 = 0; targeted 248 tests passed,
  standalone `CHECK` passed with unchanged identity, and the aggregate returned
  the intended `EXPECTED_BLOCKED` with `exact_diagnostic_report: true`.

## 8. Non-implications and remaining work

M0 remains incomplete. This checkpoint supplies a reviewed, deterministic test
collection identity and a fail-closed local comparison. It grants no authority
for:

- database or knowledge admission;
- security approval or merge approval;
- branch evidence or release certification;
- scientific acceptance or correctness of mathematical claims;
- completeness of the V2 architecture, migration, database, Paper Agent DAG,
  web demo, or arbitrary-arXiv pipeline.

This slice did not perform a Lean rebuild, typecheck, axiom audit, or theorem
revalidation. It therefore makes no claim that Lean or the Stabilizerness
formalization passed. M0 still requires its remaining governance, isolation,
toolchain, formal-revalidation, and repository-policy exit evidence.
