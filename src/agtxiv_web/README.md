# New-paper source intake

`intake.mjs` uses only standard Web APIs and runs unchanged in Node 22+ and Cloudflare Workers. It imports no Node module and never executes TeX, macros, shell commands, source code, or a PDF renderer. Its JSON output is a **source-intake report**, not an admitted V3 scientific claim, verification, or assessment record.

```js
import { analyzeArxiv, fetchArxivSource, analyzeSource, parseArxivId } from './intake.mjs';

const report = await analyzeArxiv('1706.03762');
// An unversioned ID is resolved through the arXiv Atom API to an exact version.

const source = await fetchArxivSource('1706.03762v7');
const sameReport = await analyzeSource(source.bytes, {
  arxiv: source.arxiv,
  metadata: source.metadata,
  sourceUrl: source.url,
  fetchedAt: source.fetchedAt,
});
```

## Interface

- `parseArxivId(string)` returns `{id, version, canonical, sourceUrl, abstractUrl}`. `version` is `null` if unresolved. Supported inputs are modern IDs, legacy archive IDs, `arXiv:ID`, and HTTPS arXiv abstract/PDF/source URLs. Invalid dates, archive prefixes, sequence lengths, version zero, query strings, fragments, credentials, and non-arXiv hosts are rejected.
- `fetchArxivSource(input, options?)` resolves an exact version, fetches only its source endpoint, and returns `{bytes, arxiv, requested, metadata, fetchedAt, url, contentType}`. `metadata` is optional Atom title/authors/abstract data used only as a fallback. The host allowlist is `arxiv.org` and `export.arxiv.org`; redirects cannot change the paper version or source endpoint class. Input URLs are not fetched directly.
- `analyzeSource(Uint8Array | ArrayBuffer | string, options?)` returns the report below. Input can be plain TeX, gzip-compressed TeX, tar, or tar.gz. `options.main` can explicitly select a relative main TeX path. Optional provenance values are `arxiv`, `metadata`, `sourceUrl`, and `fetchedAt`.
- `analyzeArxiv(input, options?)` composes the preceding operations. Fetch-related options are `fetchImpl` (for tests), `signal`, and `limits`. Limits may only **reduce** defaults.
- Errors are `IntakeError` instances with `{name: 'IntakeError', code, message}`. Callers should expose the bounded error message and keep a failed job state; they must not substitute a cached paper when a new submission fails.

The result has these stable top-level fields:

| Field | Meaning |
|---|---|
| `schemaVersion`, `analysisId` | Engine version and content-derived analysis identity. Observed fetch time does not change identity. |
| `status` | Always `SOURCE_LINKED_CANDIDATES`, never scientific approval. |
| `paper` | Bounded readable title, author names, abstract, exact arXiv identity, and original-source metadata anchors where available. |
| `main`, `sources` | Selected document root and full archive file inventory with SHA-256 hashes, byte sizes, extension-derived role, static activity, and unsupported-content status. |
| `candidates` | Theorem-like environments, equations, and assertion-cue paragraphs discovered in the submitted bytes. |
| `includes` | Literal TeX include directives, bounded original-byte evidence, possible target, static activity, and unresolved/ambiguous state. |
| `counts` | Source files, TeX files, discovered/returned/omitted candidates, and local reference count. |
| `frontier` | Syntax issues; omitted candidates; byte ranges outside returned candidate envelopes; unclassified files; unsupported resources; inactive/uncertain candidates; macro and completeness limits. |
| `provenance` | Engine method, source and manifest SHA-256 hashes, format, archive byte count, exact source URL/version, fetch time, byte-offset convention, and whether the engine retained source bytes. |
| `limits` | Effective, machine-readable resource limits. |

Each candidate includes `id`, `type`, `environment`, readable `text`, bounded original `latex`, `excerptTruncated`, full `anchor`, `excerptAnchor`, `labels`, `activity`, `interpretation`, `dependencies`, `citationCues`, and `assessments`. The original envelope and excerpt have separate SHA-256 hashes. Anchors use zero-based, half-open original byte ranges `[startByte, endByte)` and one-based source line numbers. UTF-8 BOMs and multibyte characters are included in offsets; invalid UTF-8 uses an explicitly uncertain byte-preserving Latin-1 display fallback.

The six assessment fields are `source_fidelity`, `mathematical_correctness`, `formal_alignment`, `semantic_applicability`, `empirical_support`, and `computational_reproducibility`. **All six always equal `NO_ASSESSMENT`.** A `LOCAL_REFERENCE` means a `\ref`-like cue was observed, not that the source supports or proves the target. Citation keys are not verified bibliographic identities. Ambiguous labels are retained and never arbitrarily resolved.

## Bounds and fail-closed behavior

Defaults: 8 MiB downloaded bytes, 16 MiB expanded bytes, 2 MiB per file, 4 MiB total TeX bytes, 1,024 archive entries, 512 files, 512 UTF-8 path bytes, 240 returned candidates, 1,800 characters per candidate excerpt, 512 include directives, 50,000 TeX commands, 4,096 discovered structural spans, 1,024 reference cues, 1,024 citation keys, 1,024 candidate labels, 256 syntax issues, 32 MiB cumulative bytes hashed for anchors, 30 seconds per fetch/decompression phase, and 3 redirects. Environment and conditional nesting are independently capped at 128. Readable titles are limited to 500 characters; authors to 30 names of 500 characters; abstracts to 3,000 characters.

Archives require valid tar header checksums and zero-block termination. Paths cannot be absolute, contain parent traversal, backslashes, controls, drive prefixes, or collide after normalization. Symbolic links, hard links, sparse files, special entries, file/directory collisions, duplicate paths, unused path metadata, malformed PAX metadata, and truncated archives are rejected. Bounded PAX per-entry paths/sizes and GNU long path records are supported. No file is extracted to the filesystem.

Increasing source size cannot silently turn a partial scan into a complete analysis: archive/parse limits fail the job. The candidate display cap is the sole truncating limit; omitted counts and exact remaining unclassified byte ranges remain in `frontier`. Unsupported non-TeX files are inventoried and hashed, not interpreted. Macro bodies, comments, and verbatim environments are masked. An undelimited macro makes the remainder opaque. Literal `\iffalse` content is inactive; arbitrary conditions remain unknown. Include paths that depend on macros or that match multiple plausible files are unresolved. No claim is made about which bytes participated in the published rendering.

## Source retention

The module itself retains no archive after returning its report, so `provenance.sourceStored` defaults to `false`. A hosting adapter that successfully stores source bytes privately should update that value and its source-retention explanation, and should bind stored-object identity to `archiveSha256`. Storage keys and analysis-access tokens must not be inserted into public source metadata. This module's resource bounds do not replace service-level rate limits, job expiry, access control, or recovery of interrupted jobs.

## Verification

```sh
node --test tests/web/intake.test.mjs
.venv/bin/python -m pytest -q tests/web/test_intake_schema.py
```

The tests cover positive extraction, changed-input identity, multibyte and BOM byte anchors, six unassessed axes, supported archive formats, unsafe archives and decompression limits, PAX and GNU names, include activity/ambiguity, hidden macro/comment/verbatim content, duplicate labels, display truncation, and exact-version network behavior with injected fetch responses. The Python tests validate actual JavaScript output against `analysis.schema.json` and reject invented approval flags, promoted assessment states, malformed hashes, unsafe paths, missing assessments, inconsistent reference cardinality, and oversized limits. JSON Schema checks structure; cross-record identity and byte-hash consistency are established by engine construction and the byte-level tests, not by JSON Schema alone.

A live network check on 2026-09-07 successfully resolved `1706.03762` to `1706.03762v7` (Attention Is All You Need), fetched 1,150,988 bytes, inventoried 23 files including 10 TeX files, and returned 11 source candidates with no omitted candidates. Source archive SHA-256: `2e7a7d9ee2520d22eb23dae0cb148e167be02a30d6cb3f11b1c67723194339c6`. The Node observation took approximately 609 ms and used about 11 MiB JavaScript heap plus 5 MiB array buffers; it is a smoke test, not a Cloudflare memory certification or evidence of scientific correctness.
