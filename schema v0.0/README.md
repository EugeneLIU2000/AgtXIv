# AgtXIv V3 experimental schema package, version 0.0.0

This directory contains the complete first English contract package for the V3 architecture: **64 record families, 19 shared value structures, an offline union schema, and a byte-pinned manifest**. V3 names the architecture; `0.0.0` names this experimental contract revision. The directory name `schema v0.0` is intentional.

The package covers the entire planned record lifecycle. It does **not** mean that every producer, reviewer, formal worker, archive, or knowledge service is implemented. The [execution status](../docs/roadmaps/v3-execution-status.md) tracks that distinction against every roadmap task. The Charter remains pending ratification.

Read these files in order:

1. [完整中文说明](SCHEMA.zh-CN.md): the intuition, all common types, the envelope, and every record field in Chinese.
2. [Complete English reference](SCHEMA.md): the same field tables in English.
3. [Cross-record invariants](INVARIANTS.md): implemented checks, trust boundaries, and checks that require additional implementation or actual scientific evidence.
4. [catalog.json](catalog.json): record discriminator, schema file, title, and associated roadmap tasks.
5. [manifest.json](manifest.json): exact schema URIs and raw byte hashes. Schema URIs are identifiers; validation resolves them locally and never downloads them.

`evaluation-corpus.json` is a separate input manifest covering existing research materials. It is neither a V3 scientific assessment nor part of the record union. Its historical outcomes are not reviewed V3 ground truth.

## Working commands

Run from the repository root using the existing Python 3.12 environment and pinned dependencies in `pyproject.toml` / `uv.lock`:

```bash
.venv/bin/python tools/generate_v3_schema_v00.py --check
.venv/bin/python tools/validate_v3.py --bundle-only
.venv/bin/python -m pytest tests/v3 -q
```

These commands check contracts and local mechanisms. They do not run a paper demo, vibefeld, a Lean build, a reproduction experiment, or a scientific review.

The separately pinned upstream profile can also be checked against the existing local source checkout, without executing upstream code:

```bash
.venv/bin/python tools/generate_vibefeld_protocol.py --check
```

This covers 35 event types, three generated protocol schemas, and 35 pinned source files. Runtime import uses the generated profile; it does not require the upstream checkout. The profile supplements, rather than changes, the 64-family V3 record union.

To validate an explicitly supplied set of records and original artifact bytes:

```bash
.venv/bin/python tools/validate_v3.py \
  --records /absolute/input/records.json \
  --artifacts /absolute/input/artifacts.json
```

`records.json` contains one sealed record or an array of sealed records. Repeat `--records` for several files. Every referenced record must be supplied, including the exact policy and required predecessor records. Duplicate record identities are rejected.

The artifact-location manifest is a JSON array of objects with exactly `artifact_id`, `media_type`, and `path`. Paths are relative to that manifest, cannot escape its directory, and cannot traverse symlinks. The caller controls this input directory. The record's raw hash, byte size and media type are checked against supplied bytes; the path itself is not identity evidence. The CLI currently bounds one artifact to 64 MiB and the set to 256 MiB.

The opt-in `--without-artifact-bytes` mode performs weaker checks and reports `byte_artifacts_checked: false`. A successful exit reports the scope of checks; it does not establish scientific acceptance. The CLI always reports `authority_checked: false`: it never treats an identity file supplied alongside untrusted records as independent authentication.

To inspect a local source directory without executing TeX:

```bash
.venv/bin/python tools/inspect_v3_source.py /absolute/source --main main.tex
```

This inventories actual local bytes and static include relationships. Unresolved macros, inactive branches, missing files and unknown publication activity remain visible. The command cannot establish what an author published or whether an extracted claim is source-faithful. See its `--help` for resource bounds and output options.

## Python entry points

- `agtxiv_v3.contracts.SchemaBundle`: verifies the package, resolves schemas offline, constructs candidate envelopes, and checks schema/content identity.
- `agtxiv_v3.contracts.RecordSet`: checks supplied record and artifact closure plus the implemented cross-record invariants. Public record access returns detached copies.
- `agtxiv_v3.contracts.AuthorityContext`: an explicit capability supplied by a trusted integrating caller, containing execution attestations, principal aliases and authorized policy hashes. It is not a production identity provider, signature verifier, or mechanism for granting scientific qualifications.
- `agtxiv_v3.source`: bounded atomic tar extraction, original byte-span checks, and conservative static TeX structure analysis.
- `agtxiv_v3.intake`: bounded local-directory inspection and candidate source/structure record construction with caller-provided attribution.
- `agtxiv_v3.projections.project_axes`: a read-only six-axis view retaining every assessment of the exact target in the supplied set, with conditions and apparent disagreements. `render_axes_markdown` provides a Chinese reader view. This is not itself a knowledge query service.
- `agtxiv_v3.obligations.check_obligations`: checks one current disposition per frozen obligation within an explicitly supplied historical record universe, retained predecessor history, and typed exact-target completion witnesses. A positive release audit additionally enforces `SUCCESS_REQUIRED`; unsupported completion stages fail closed. Full record-graph and authority validation remain separate obligations of the caller.
- `agtxiv_v3.vibefeld.inspect_capture`: bounded, read-only inspection of supplied bytes for the pinned upstream commit, including ledger replay and graph comparison. `build_import_candidate` preserves original bytes and produces only an attributed import candidate. Declared identities are not authenticated, and upstream `validated`, `admitted`, `closed` and `clean` never become V3 scientific approval.

- `agtxiv_v3.dependencies.inspect_dependencies`: deterministic potential impact over declared exact dependencies and proof-route inference uses; outputs remain `ORACLE_PROPOSED` / `UNVERIFIED` and never change assessments.
- `agtxiv_v3.storage.LocalStore`: bounded SQLite candidate storage, immutable records/artifacts, atomic ingest, provisional snapshot compare-and-swap, and exact historical read-only queries retaining relevant conflicts. Persistence is not admission; query responses remain `PROVISIONAL`.

- `agtxiv_v3.candidates`: bounded full-directory candidate artifacts, exact text spans, tentative lexical claim cues, explicit proposed argument/obligation records and historical queries. `tools/inspect_v3_candidates.py` supplies the offline CLI. Candidate artifacts are not new authoritative knowledge snapshots; local opt-in context remains unadopted.

See the bilingual [local mechanism guide](../docs/architecture/v3-local-mechanisms.md) for API and trust boundaries, and the [real-paper candidate loop](../docs/architecture/v3-real-candidate-loop.md) for a source-grounded, replayable example with unresolved work.

Add `src` to the Python import path when using these APIs outside the installed workspace environment. Creating a candidate with `make_record` checks its shape and identity only; use `RecordSet` for supplied graph validation. Passing `AuthorityContext` adds bounded identity checks. Neither operation supplies missing scientific evidence.

## Maintaining the contract

The maintained source is [tools/generate_v3_schema_v00.py](../tools/generate_v3_schema_v00.py). English and Chinese descriptions are declared together. Regeneration writes 66 JSON Schema files, the manifest, the catalog and two complete field references. `--check` verifies that all 70 generated files match; it does not overwrite them. The README, invariant ledger, evaluation corpus and execution report are maintained separately.

Schema files use JSON Schema Draft 2020-12. Root and nested record objects reject extra properties. Record identities contain an exact discriminator, lineage ID, positive revision and content hash. The record hash includes every field except the root `content_hash`; artifact hashes always use original bytes. Canonical JSON uses the existing V2 NFC/LF and integer-safe parser, but V3 hashes its own flat envelope and does not reuse the V2 envelope-specific hash function.

During this unpublished `0.0.0` development phase, regeneration changes the manifest hash. Any candidate sealed under earlier bytes retains that older bundle identity and cannot be silently resealed as the same historical record. Once distributed or adopted, further field/meaning changes require a new contract version with an explicit migration policy.

所有测试中的 `SYNTHETIC` 记录都是人工构造的边界检查材料。它们可以说明程序拒绝了哪一种错误，不能说明某篇论文已经被证明、发布或准入知识库。
