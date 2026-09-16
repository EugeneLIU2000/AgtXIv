# V3 local mechanisms / 本地机制使用边界

This guide covers offline engineering mechanisms, not scientific acceptance, publication, or knowledge-admission authority. Contract version: `0.0.0`. The complete [English schema reference](../../schema%20v0.0/SCHEMA.md) and [中文逐字段说明](../../schema%20v0.0/SCHEMA.zh-CN.md) remain the authoritative field inventories for this experimental bundle.

The earlier [vibefeld integration design](v3-vibefeld-integration.md) is byte-pinned as an evaluation input and is preserved unchanged. Its design-time implementation statements are historical; this guide and the execution status describe the current local implementation.

## Frozen obligations / 冻结义务

`agtxiv_v3.obligations.check_obligations(store, scope_ref, disposition_refs, universe_refs=..., enforce_success=True)` checks an explicit historical universe, not every record that happens to exist elsewhere in a store.

- Every frozen obligation needs one selected current disposition. A fork cannot be hidden by selecting one branch; predecessor history must remain in the supplied universe.
- Candidate accounting (`enforce_success=False`) can retain deferred required work. It does not permit arbitrary records to stand in for evidence of completed work.
- Positive audit accounting also enforces `SUCCESS_REQUIRED`. Evidence must match the exact target, required axes and conditions; processing source bytes is not scientific source fidelity.
- Unsupported `CONTRIBUTION` and `RELEASE` completion stages fail closed. A successful local report never supplies a missing domain review or runtime attestation.
- Callers must separately validate the complete `RecordSet` and any applicable independently supplied authority context. A universe supplied by an untrusted caller does not prove that no external history exists.

中文：这里解决的是“在明确给出的历史截面中，每项义务现在由谁处置、依据是什么”。它不是自动审论文，也不能证明调用者没有漏交外部记录。失败或不确定的检查可以如实记账，但不能冒充必须成功的工作。

## Pinned upstream capture / 固定上游离线输入

`agtxiv_v3.vibefeld.inspect_capture(files, commit=..., workspace_key=...)` accepts an explicit mapping of relative paths to original bytes. It does not run upstream commands or read an arbitrary directory implicitly. The supported commit is `392b2da3bee5766cca1a201f28e0255056baaba4`.

The maintained profile contains three schemas and 35 event types. Regeneration checks 35 byte-pinned upstream source files. Unknown versions/events, malformed inputs and disagreement between replay and graph are not silently accepted. Missing capture members remain explicit. A stable caller-selected workspace key separates semantic identity from the location of a copied directory; raw relocated bytes are still preserved as different raw bytes where applicable.

`build_import_candidate` returns an attributed `UpstreamImport` record and retained artifacts, not an argument review, theorem, assessment, release or admission. `STRUCTURALLY_IMPORTED` means agreement within the supplied capture boundary. Declared identity maps do not authenticate actors. Upstream `validated`, `admitted`, `closed` and `clean` remain reported labels.

中文：可以离线核对“所交事件与导出是否一致”，但没有执行真实 vibefeld，也没有获得独立身份凭据。改写后的一整套自洽历史仍须外部检查点才能识别；本地哈希不提供这种独立保证。

## Potential dependency impact / 潜在依赖影响

`agtxiv_v3.dependencies.inspect_dependencies(store, trigger_refs)` validates supplied record contracts without requiring artifact bytes, then returns a deterministic report binding the exact input universe and trigger references.

It follows declared dependency bindings and route-local inference uses, not generic display containment or provenance links. Joint premises remain jointly represented. Exact old revisions are not replaced by a floating latest version. The report retains unreached proof routes relative to the supplied declarations; it does not certify their independence or validity.

Outputs are explicitly `ORACLE_PROPOSED` / `UNVERIFIED`. Affected axes are potential output impacts: the schema does not encode a prerequisite-axis transfer function. The analysis neither revises scientific assessments nor proves that all dependencies have been declared. Raw artifact integrity and identity authority are separate checks.

中文：影响分析提示“哪些确切对象或证明路线可能需要重新检查”，不是自动撤销科学结论。没有走到某条路线，只能说明提供的依赖声明没有连到它，不能因此宣布它已被证明独立或正确。

## Local persistence and queries / 本地持久化与查询

`agtxiv_v3.storage.LocalStore(path, bundle)` stores canonical records and original artifact bytes in SQLite. `ingest(records, artifacts)` validates the resulting complete local record set before committing; immutable identity/revision or artifact-ID conflicts, missing references, invalid hashes and validation failures roll the transaction back. Identical object retries are idempotent.

An optional `snapshot_ref` with `expected_head` updates a **provisional** domain pointer by compare-and-swap in the same transaction. `expected_head=None` means the head must be absent. A successor must extend that exact expected snapshot. Stale writers must retry with a newly constructed successor; they cannot partially overwrite old knowledge. Historical objects remain resolvable by exact reference.

`LocalStore(path, bundle, readonly=True)` opens a read-only connection. `query(snapshot_ref, references=None)` selects entries from the exact snapshot and retains relevant limiting relations and opposing endpoints. Responses always say `PROVISIONAL`, including when stored records contain positive decisions. Queries do not generate an admission decision, ingestion receipt, query receipt, scientific assessment or reuse permission.

The database is pinned to its exact schema bundle. This is bounded local storage, not a production archive: complete-set validation retains the 10,000-record limit; each thread uses its own connection; the filesystem and integrating caller are trusted. Database triggers are not independently held checkpoints or protection from an administrator replacing the file. Local subprocess interruption/restart is tested, including rollback before commit and retention after commit. This is not a power-loss guarantee; access-control separation, adopted admission policy and production durability/performance still need dedicated operational evidence.

中文：已实现候选记录“不覆盖、一起提交或一起回滚、并发时核对旧快照”的本地机制，并可按确切历史快照读取。保存成功不代表科学准入；本地快照指针不是正式知识索引。冲突两端不能因查询只选了一边就消失，但没有宣称发现了输入之外的全部冲突。

## Reproducible checks / 可重复检查

```bash
.venv/bin/python tools/generate_v3_schema_v00.py --check
.venv/bin/python tools/generate_vibefeld_protocol.py --check
.venv/bin/python tools/validate_v3.py --bundle-only
.venv/bin/python -m pytest tests/v3 -q
```

These are local contract, parser and transaction tests. They do not run a paper demo, upstream executable, Lean, or a scientific reproduction. Synthetic test records exercise rejection boundaries and never substitute for real scientific evidence. The [execution status](../roadmaps/v3-execution-status.md) records exact counts and remaining roadmap work.
