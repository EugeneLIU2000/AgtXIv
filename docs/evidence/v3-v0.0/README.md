# V3 0.0.0 local verification evidence

These files record engineering checks and read-only local source observations on 2026-09-07 local time. They do not certify a scientific claim, run a paper demo, or establish a release/admission decision. UTC timestamps may fall on 2026-09-06 in the late evening.

## Original local checkpoint

The following four artifacts describe the earlier checkpoint, not the latest resumed implementation.

- [contracts.junit.xml](contracts.junit.xml): the actual result of `.venv/bin/python -m pytest tests/v3 -q --junitxml=docs/evidence/v3-v0.0/contracts.junit.xml`. **425 passed**, with no failed, errored or skipped tests. This is the V3 targeted suite, not the repository-wide test suite.
- [verification.json](verification.json): command scope, test summary, bundle identity and exact implementation/test file hashes associated with this local check.
- [corpus-asset-integrity.20260906T230120813375Z.json](corpus-asset-integrity.20260906T230120813375Z.json): all **106/106** pinned input assets matched their recorded raw SHA-256 and byte size. It also binds each saved source report by byte hash and size.
- [source-inspections](source-inspections/): five actual local-directory inspection reports, totaling **32 files and 4,968,008 bytes**. The 26 non-TeX files were inventoried as bytes only; no paper code, TeX, Lean or vibefeld was executed.

The static parser retained 16,948 unsupported or uncertain syntax occurrences across those sources. **This is not a count of errors in the papers.** Repeated macros can produce many occurrences; only one literal include relationship was recognized by this conservative parser. All published-rendering participation remains unassessed, and source-fidelity/scientific assessments remain `NOT_PERFORMED`. No source-completeness or scientific pass rate is derived from this report.

## Resumed implementation observations

- **Final:** [resume-final.junit.xml](resume-final.junit.xml) records **648 passed, zero failures/errors/skips**, after the residual review fixes. This adds 153 cases to the recovered 495-case baseline and repairs its two failures. [resume-verification.json](resume-verification.json) binds commands, bundle identity and 30 implementation/test/evidence files. Schema generation, the pinned upstream profile, offline bundle validation and Python compilation also passed. Repository-wide checks and prohibited scientific/upstream executions were not run.
- [resume-baseline.junit.xml](resume-baseline.junit.xml): **493 passed, 2 failed** before repairs. Both initial failures were interrupted-test interface errors; correcting them also exposed an incorrect event-field name in a fixture.
- [resume-intermediate.junit.xml](resume-intermediate.junit.xml): **624 passed** at an intermediate checkpoint. Independent re-review subsequently found a counterexample-witness closure gap and a malformed-reference cache bypass. This green run is not the final correctness claim.
- [resume-corpus-intermediate-mismatch.json](resume-corpus-intermediate-mismatch.json): records **105/106** matches while a proposed maintenance edit changed the byte-pinned integration-design input. Only those newly made documentation edits were reverted; the pinned manifest was not rewritten.
- [resume-corpus-integrity.json](resume-corpus-integrity.json): the subsequent local check reports **106/106** matches. Current implementation notes live in a new [bilingual mechanism guide](../../architecture/v3-local-mechanisms.md), leaving that historical input unchanged.

Storage recovery tests use disposable local databases and genuine subprocess exits, before and after commit. They establish the tested process-restart behavior, not power-loss resilience, independent archival integrity, or formal admission. The new dependency report is potential declared impact, with `ORACLE_PROPOSED` / `UNVERIFIED` status; stored queries remain `PROVISIONAL`.

Tests using `SYNTHETIC` records check whether the program rejects inconsistent or overclaiming records. Local identity test contexts are fabricated test inputs, not real authorizations. The independent code review supplied adversarial cases; it was not a scientific review of the five papers.

All evidence here is locally writable and has no independently held signature or checkpoint. The recorded hashes support comparison to these bytes; they do not establish independent archival integrity. Future runs must be treated as new observations, not replacements for a formally published immutable scientific record.

中文说明：这里有两类事实——程序边界检查的结果，以及本地文件实际读到了哪些字节。它们都不等于“论文已通过验证”。静态解析器无法理解的宏被如实列为未知，不算作者犯错。
