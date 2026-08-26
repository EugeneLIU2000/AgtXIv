# AgtXIv Paper Source Acquisition

**Status:** Normative MVP specification

**Schema version:** `agtxiv.paper-source/0.2`

**Scope:** PAPER queries, stable work and publication-repository resolution, canonical full-text acquisition, LaTeX preprocessing, source anchoring, and publisher-witness alignment

## 1. Purpose

This specification defines the first stage after a user submits a paper query. The stage resolves a stable intellectual work, allocates or resolves its single public publication repository, obtains one exact highest-priority source occurrence, extracts source-grounded content, expands paper-defined mathematical macros when LaTeX source is available, and records locations that later pipeline stages can cite. Acquisition prepares content for a future repository release; it does not by itself create an accepted scientific publication.

Source resolution, macro expansion, and publisher alignment establish content identity and source fidelity. They do not establish scientific correctness.

This stage answers:

1. Which stable `work_id` does the query identify?
2. Which single public publication repository is assigned to that work?
3. Which exact `source_version_id` and canonical source artifact are selected at the recorded observation boundary?
4. Which additional publisher artifact, if any, serves as a witness?
5. Where does each extracted passage occur?
6. Which mathematical passages have been expanded into the approved standard LaTeX vocabulary?
7. Which publisher differences were matched, applied to derived content, deferred for review, or superseded by a later arXiv version?

## 2. Supported Query

This acquisition profile supports only `PAPER` queries. A `PAPER` query requests complete ingestion and processing of one paper. It does not ask the acquisition, extraction, claim-processing, dependency, or verification stages to answer a research question.

A query may identify a paper by:

1. DOI;
2. arXiv identifier;
3. publisher article URL; or
4. title search.

DOI and arXiv identifiers are preferred because they identify papers more reliably than titles. A title search must resolve to one paper record before source acquisition begins.

A minimal query record is:

```json
{
  "query_type": "PAPER",
  "identifier_type": "DOI",
  "identifier": "10.xxxx/example",
  "submitted_at": "2026-08-21T14:00:00Z",
  "deferred_question": null
}
```

The allowed `identifier_type` values are:

```text
DOI
ARXIV
PUBLISHER_URL
TITLE
```

### 2.1 Optional deferred question

A user may include a question about the paper:

```json
{
  "query_type": "PAPER",
  "identifier_type": "ARXIV",
  "identifier": "1609.07488",
  "submitted_at": "2026-08-21T14:00:00Z",
  "deferred_question": {
    "text": "What is the definition of robustness of magic and which properties are proved?",
    "status": "DEFERRED"
  }
}
```

AgtXIv stores the question verbatim in the query service. The question text must be physically excluded from every input supplied to:

- paper resolution;
- canonical-source selection;
- source extraction;
- macro classification and expansion;
- anchor generation and alignment;
- claim detection and classification;
- class-specific normalization;
- claim merging and pruning;
- dependency construction;
- verification planning, scope, and execution.

The processing projection of the query contains only paper-identification fields and an indication that a deferred question exists:

```json
{
  "query_type": "PAPER",
  "identifier_type": "ARXIV",
  "identifier": "1609.07488",
  "submitted_at": "2026-08-21T14:00:00Z",
  "deferred_question_present": true
}
```

Pipeline components must not retrieve the deferred-question text from the query service. The source manifest records only whether a deferred question exists and its lifecycle status; it does not copy the question text into the source package.

The paper is processed in the same way whether a deferred question is present or absent. This isolation prevents selective reading, omitted assumptions, confirmation bias, and question-driven verification.

The question is considered only after every configured pipeline stage has produced a final explicit result. A blocked, unresolved, failed, or not-applicable result is explicit and final for this purpose. Pipeline completion does not mean that every claim is verified.

A deferred question has the lifecycle:

```text
DEFERRED
ANSWERED
BLOCKED
```

`ANSWERED` means that final claims, anchors, dependencies, and verification records support a grounded response. The response may use only final pipeline records. It must not use intermediate records, direct rereading of source artifacts, or outside knowledge.

`BLOCKED` means that the final records do not support a reliable answer. A blocked question must not be answered by guessing. The final answer record belongs to the end-of-pipeline query-response stage and is outside the scope of this specification.

## 3. Canonical Source Artifact and Publisher Witness

A canonical source artifact is the full-text object from which AgtXIv derives the work's active structured content for one acquisition boundary and eventual publication release. Canonical-source status concerns source identity and content, not scientific correctness. ``Latest'' below means latest as resolved from authoritative metadata at `latest_version_resolution.observed_at`; after publication, the selected `source_version_id` is fixed for that release.

This acquisition profile uses this strict priority order:

1. **Latest arXiv source bundle.** If an arXiv source bundle exists, the latest available version is canonical, including when a publisher PDF also exists.
2. **Publisher PDF fallback.** Only after authoritative evidence establishes that no arXiv record or source bundle exists, a publisher PDF may become canonical.
3. **Blocked.** A transient failure or unresolved source-candidate conflict blocks canonical activation rather than lowering artifact priority.
4. **Unavailable.** Only deterministic absence of both arXiv source and publisher PDF makes canonical resolution unavailable.

When arXiv source is canonical:

- the complete source bundle is the canonical artifact;
- the manifest records the arXiv version and submission date;
- the extractor identifies the root LaTeX entry point;
- relevant macro, environment, and package context is extracted into `head.tex`;
- a publisher PDF, when available, is stored as a `publisher_witness`.

A publisher witness provides evidence for locating and comparing the published presentation. It is not canonical while arXiv source is available. Alignment must not modify the arXiv bundle or publisher PDF.

When only a publisher PDF is available, it is canonical and is read using `PDF_TEXT` or `OCR`. OCR output is derived evidence and never replaces the original PDF.

The active acquisition workspace does not introduce authority-conflict or multi-canonical states. Published repository releases are nevertheless immutable historical instances and remain replayable.

### 3.1 Work and publication-repository assignment

A resolved query produces one stable `work_id` and resolves the unique eligible `WorkRepositoryBinding` containing provider, stable provider repository identity, and canonical URL. The repository belongs to the work, not to one arXiv version. A newer `source_version_id` reuses the same repository and may later produce a new release. Repository allocation failure blocks publication packaging but does not change the scientific source-selection priority.

The source manifest records repository identity but not a future release commit. The exact commit, tree, tag, provider release, and release assets are bound after the tree is committed by the AgtXIv `ReleaseManifest`. A mutable branch or unresolved ``latest'' repository URL never identifies a publication instance.

### 3.2 Retrieval backend policy

Retrieval backend selection does not change canonical authority. A configured arXiv Kaggle dataset and the official arXiv e-print/source endpoint are transports for obtaining `ARXIV_SOURCE`; neither is a new canonical source type. A metadata-only Kaggle dataset is not a source backend: the configured dataset must contain source archives.

Acquisition first resolves the paper arXiv identifier and exact latest version from authoritative arXiv metadata. `latest_version_resolution` records the authority and URL, observation time, resolved identifier and version, and status. Its status is `RESOLVED`, `NOT_FOUND`, or `TRANSIENT_FAILURE`. Timeout, rate limiting, service unavailability, or temporarily unavailable metadata produces `TRANSIENT_FAILURE`, not evidence of absence.

For a resolved arXiv record, retrieval proceeds in this order:

1. attempt the configured Kaggle source dataset for the exact resolved version;
2. if that attempt is `NOT_FOUND` or `INVALID_CANDIDATE`, attempt the official arXiv e-print/source endpoint for the same exact version; and
3. enter publisher-PDF fallback only when no valid exact-version arXiv candidate exists and the official endpoint deterministically returns `NOT_FOUND` for that source, or when authoritative metadata deterministically establishes that no arXiv record exists.

Every entry in the ordered `retrieval.attempts` array has one result:

```text
SUCCEEDED
NOT_FOUND
INVALID_CANDIDATE
TRANSIENT_FAILURE
NOT_APPLICABLE
NOT_ATTEMPTED
```

`NOT_FOUND` means a deterministic negative response from the named backend. Kaggle `NOT_FOUND` alone never proves that arXiv source does not exist. `INVALID_CANDIDATE` is reserved for deterministic identity, version, content, or safety validation failure. Suspected truncation, transport corruption, incomplete download, or another plausibly retryable validation failure is `TRANSIENT_FAILURE`, not `INVALID_CANDIDATE`. `TRANSIENT_FAILURE` also includes timeout, rate limiting, temporary service or metadata failure, and indeterminate responses; it requires retry and blocks publisher fallback. `NOT_APPLICABLE` and `NOT_ATTEMPTED` must include reasons.

A Kaggle `INVALID_CANDIDATE` triggers the official endpoint, which may resolve that lower-priority candidate failure by succeeding. An official `INVALID_CANDIDATE` never permits publisher fallback: deterministic official identity, version, or content conflict produces canonical `REVIEW_REQUIRED`, while suspected transport damage is classified as `TRANSIENT_FAILURE` and produces `RETRY_REQUIRED`. Publisher fallback remains permitted only at the deterministic `NOT_FOUND` boundary above.

Every arXiv candidate must match the resolved paper identifier and exact requested version. A Kaggle attempt records `version_evidence`; unproved version identity makes the candidate invalid. The archive must be readable and extractable, contain a non-empty source payload, reject absolute paths and `..` traversal, and reject every symbolic link and hard link. Every attempt that obtains any bytes, including an invalid or partial candidate, records a retained `candidate_path`. Invalid, partial, conflicting, or not-yet-validated bytes remain quarantined and are never committed to the public publication tree. When redistribution rights do not permit public inclusion, the repository stores exact hashes, metadata, and stable locators rather than the restricted bytes. `redistribution_dispositions` is exhaustive per obtained object: the canonical source, publisher witness, every supplement, and every successful, invalid, partial, or conflicting retrieval candidate each receive their own disposition and decision evidence.

Each obtained archive records a locally computed `archive_sha256` for transport provenance and a deterministic `source_tree_sha256` for content comparison after successful extraction. The MVP source-tree manifest is an array containing only regular files; directories and all links are excluded because links are rejected. Each object has exactly `path`, `type`, and `sha256`, where `type` is `file`, `path` is a relative POSIX path encoded as valid UTF-8, and `sha256` is the file-byte SHA-256. Paths must not undergo Unicode normalization or case folding. Sort objects by the UTF-8 bytes of `path`, encode the array as UTF-8 using the RFC 8785 JSON Canonicalization Scheme, and SHA-256 those bytes. Outer compression, tar ordering, timestamps, ownership, or other container metadata can change `archive_sha256` without creating a source-content conflict.

By default, a successful Kaggle attempt may be selected without calling the official endpoint. `official_cross_check.mode` is `DISABLED`, `ALWAYS`, or `FIRST_SEEN_DATASET_REVISION`; the latter two call the official endpoint after Kaggle `SUCCEEDED` for configured audit. The official attempt records its cross-check trigger and reason. When both backends succeed for the exact version, equal `source_tree_sha256` values produce comparison status `MATCHED`, even if archive hashes differ, and selection may follow backend order. Different tree hashes produce canonical `REVIEW_REQUIRED`; the comparison records both attempt identifiers, candidate paths, and hashes, no attempt is selected, and canonical activation remains blocked. If the cross-check returns `NOT_FOUND` after Kaggle produced a valid exact-version candidate, the validated Kaggle candidate remains selected and the publisher PDF cannot become canonical; the negative cross-check is retained as provenance.

A Kaggle locator must contain either an immutable dataset version or revision, or a locally retained snapshot path and SHA-256. A mutable dataset slug plus a date is not reproducible. Dataset identifier, member path, and version-evidence values are dataset-specific and must not assume a universal Kaggle layout.

## 4. Canonical Resolution Status

Canonical resolution has exactly four states:

```text
RESOLVED
UNAVAILABLE
RETRY_REQUIRED
REVIEW_REQUIRED
```

### 4.1 `RESOLVED`

`RESOLVED` means that AgtXIv obtained exactly one active canonical artifact: the latest arXiv source bundle, or a publisher PDF after the fallback boundary in Section 3.2 was satisfied. Only a resolved paper may proceed to preprocessing, content extraction, and anchor generation.

### 4.2 `UNAVAILABLE`

`UNAVAILABLE` means deterministic results established that neither an arXiv source bundle nor a publisher PDF is available. No canonical artifact, preprocessing output, or anchors are produced.

### 4.3 `RETRY_REQUIRED`

`RETRY_REQUIRED` means latest-version resolution or an acquisition attempt had a transient failure, including timeout, rate limiting, temporary service unavailability, or indeterminate metadata. `canonical_artifact`, `source_preprocessing`, and `alignment` are `null`; no anchors are produced. Attempts and candidate provenance remain in the manifest, and acquisition must be retried rather than falling back to a publisher PDF.

### 4.4 `REVIEW_REQUIRED`

Canonical-resolution `REVIEW_REQUIRED` means valid candidates for the same exact arXiv version have different source-tree hashes or another acquisition conflict prevents safe selection. `canonical_artifact`, `source_preprocessing`, and `alignment` are `null`; no anchors are produced. Candidate paths, hashes, validation, and comparison provenance remain available for review. This state is distinct from preprocessing review and anchor-alignment `REVIEW_REQUIRED`.

## 5. LaTeX Source Preprocessing

### 5.1 Root document

When arXiv source is canonical, the extractor must identify the root LaTeX document and follow the manuscript's included source files. The manifest records the root entry point.

If no unique root document can be identified, canonical resolution remains `RESOLVED`, but `source_preprocessing.status` is `REVIEW_REQUIRED`, `canonical_artifact.entrypoint` and `source_preprocessing.head_file` are `null`, and anchor generation is blocked. No anchor may be emitted until review identifies the active root and preprocessing is rerun with status `READY`. This review state does not permit downstream claim processing.

### 5.2 Source-derived `head.tex`

When source preprocessing reaches `READY`, the extractor creates a source-derived `head.tex` containing the definitions and package context needed to interpret the paper's mathematical content. Relevant material includes:

- `\newcommand`;
- `\renewcommand`;
- `\def`;
- `\DeclareMathOperator`;
- custom theorem environments;
- relevant package imports and options;
- relevant notation and environment configuration.

The extractor must preserve provenance for each copied definition, including its source file and lines. This provenance may be stored as comments in `head.tex` or in a linked source map. Definitions unrelated to mathematical interpretation may be omitted.

`head.tex` is preprocessing and audit material. It is not canonical paper content, must not modify the original source bundle, and must not be required by downstream claim or verification stages.

The source-derived file remains in the existing reference or source structure. `manifest.json` records its path and SHA-256 hash.

### 5.3 Macro classes

Every nonstandard command relevant to extracted content is classified as one of:

```text
SEMANTIC_MATH
FORMATTING
DOCUMENT_CONTROL
UNRESOLVED
```

`SEMANTIC_MATH` macros encode mathematical objects, operators, relations, delimiters, or structured expressions. They must be recursively expanded.

`FORMATTING` macros alter presentation without changing the retained content. Their wrappers are removed while their arguments are preserved.

`DOCUMENT_CONTROL` macros control layout, headings, counters, references, floats, or manuscript structure. They must not be converted into scientific claims.

`UNRESOLVED` macros cannot be interpreted safely from the available source and context. The system must preserve them and must not guess their meaning.

### 5.4 Expansion output

Every arXiv-derived mathematical anchor preserves:

- `raw_latex`, copied exactly from the canonical source span;
- `raw_latex_sha256`;
- the macro-expansion status;
- `expanded_latex` and `expanded_latex_sha256` for successful expansion;
- partial-expansion audit fields when expansion is incomplete.

Macro expansion has the status:

```text
EXPANDED
PARTIALLY_EXPANDED
EXPANSION_FAILED
```

For `EXPANDED`, `expanded_latex` is non-null, is derived recursively from `raw_latex` and `head.tex`, and uses only the approved vocabulary. `expanded_latex_sha256` is the SHA-256 of that exact UTF-8 string. `partial_expansion_latex` and `unresolved_macros` are empty or `null`.

For `PARTIALLY_EXPANDED`, `expanded_latex` and `expanded_latex_sha256` are `null`. `partial_expansion_latex` preserves the best faithful intermediate representation, including every unresolved author-defined command or environment, and `unresolved_macros` lists those unresolved names. Partial output is audit evidence and must not be supplied as approved-vocabulary mathematical input downstream.

For `EXPANSION_FAILED`, `expanded_latex`, `expanded_latex_sha256`, and `partial_expansion_latex` are `null`; `unresolved_macros` lists known blockers when available. `raw_latex` remains the complete source representation.

The minimum approved vocabulary consists of standard mathematical LaTeX tokens and control sequences whose meaning is fixed without the paper's preamble, including grouping, superscripts, subscripts, standard symbols and relations, standard delimiter commands, `\frac`, `\sqrt`, `\mathcal`, `\mathrm`, `\mathbf`, `\operatorname`, and standard display structures. It excludes every author-defined command and environment and every construct whose meaning depends on `head.tex`. Implementations may support a larger versioned vocabulary, but the manifest identifier must resolve to a fixed list with the same no-preamble property.

Custom theorem and proof wrappers are structural metadata, not mathematical macro output. Their type, label, and source extent remain in anchor metadata; the `\begin{theorem}` or other author-defined wrapper need not survive in `expanded_latex`. Removing a wrapper must not remove or reorder its mathematical body.

Expansion may remove formatting wrappers, but it must preserve mathematical meaning and source order. Only `EXPANDED` mathematical anchors are eligible for automatic math-claim normalization. `PARTIALLY_EXPANDED` and `EXPANSION_FAILED` anchors require preprocessing review, independently of source-witness alignment. Mathematical content obtained only from a PDF also requires review before math-claim normalization unless a reviewed transcription later produces an approved standard-LaTeX representation.

The system must never discard or overwrite `raw_latex`.

### 5.5 Downstream boundary

Downstream claim detection, classification, class-specific normalization, merging, pruning, dependency construction, and verification consume `aligned_content` and its linked expanded representation. These stages must not require:

- `head.tex`;
- author-defined macros;
- direct interpretation of the source preamble.

The original source, `head.tex`, and `raw_latex` remain available for provenance and audit.

## 6. Publisher-PDF Extraction and Alignment

### 6.1 PDF extraction

A publisher PDF is read using:

```text
PDF_TEXT
OCR
```

`PDF_TEXT` reads the PDF's text layer. `OCR` is used when the text layer is absent or unreliable, or when image-based recognition is needed for mathematical or layout content.

The PDF remains unchanged. Extracted text and OCR output are derived evidence. Every PDF location must retain the artifact hash, extraction method, page, and region when available.

### 6.2 Derived aligned content

`aligned_content` is the derived representation supplied to downstream processing when its content is non-null. It must remain linked to:

- the canonical artifact;
- the canonical source span or PDF location;
- macro-expanded content when available;
- the publisher-witness location when available;
- the alignment decision and its basis.

Corrections are stored only in `aligned_content`. The system must not edit the canonical arXiv source, publisher PDF, `raw_latex`, `expanded_latex`, or witness extraction.

### 6.3 Temporal alignment policy

Let the latest arXiv submission time be $d_{\mathrm{arXiv}}$ and the publisher publication time be $d_{\mathrm{pub}}$. The manifest field `alignment.temporal_policy` has exactly one of these values:

```text
ARXIV_NEWER
ARXIV_NOT_LATER
ORDER_UNRESOLVED
NO_PUBLISHER_WITNESS
PDF_ONLY
```

`ARXIV_NEWER` means $d_{\mathrm{arXiv}} > d_{\mathrm{pub}}$. `ARXIV_NOT_LATER` means $d_{\mathrm{arXiv}} \leq d_{\mathrm{pub}}$. `ORDER_UNRESOLVED` means that both artifacts exist but their order cannot be established safely. `NO_PUBLISHER_WITNESS` means arXiv source is canonical and no publisher PDF is available. `PDF_ONLY` means no arXiv source exists.

#### Later arXiv source

If $d_{\mathrm{arXiv}} > d_{\mathrm{pub}}$, the latest arXiv expanded content is used directly. The publisher PDF may be linked as a witness, but it must not override the later arXiv content.

Differences must be recorded. The system must not correct the later arXiv version back to the older publication.

#### ArXiv source not later than publication

If $d_{\mathrm{arXiv}} \leq d_{\mathrm{pub}}$, corresponding arXiv and publisher passages are compared.

A clear and unambiguous publication change may be applied only to derived `aligned_content`. The source and witness representations remain unchanged.

An ambiguous, mathematically substantial, or poorly aligned difference must receive `REVIEW_REQUIRED`. It must not be resolved automatically.

If either timestamp is unavailable or too imprecise to establish the ordering, the system must not apply a PDF correction automatically unless independent metadata establishes that the publisher artifact is later. Otherwise, discrepancies require review.

#### Publisher-PDF-only source

If no arXiv source exists, `aligned_content` is derived from `PDF_TEXT` or `OCR` and remains tied to page or region evidence. OCR uncertainty must remain visible.

## 7. Anchor-Alignment Status

Each anchor has exactly one alignment status:

```text
SOURCE_ONLY
MATCHED
PDF_CORRECTION_APPLIED
ARXIV_NEWER_PREFERRED
PDF_ONLY
REVIEW_REQUIRED
```

`SOURCE_ONLY` means that the anchor comes from canonical arXiv source and has no corresponding publisher-witness passage. This includes cases in which no publisher PDF exists or no reliable witness match was found and no material discrepancy is known.

`MATCHED` means that the arXiv-derived content and publisher-witness passage clearly correspond and contain no material content difference.

`PDF_CORRECTION_APPLIED` means that the arXiv version is not later than publication and a clear, unambiguous publication change was applied to derived `aligned_content`.

`ARXIV_NEWER_PREFERRED` means that the latest arXiv version postdates publication. The arXiv-derived content is retained even though the publisher witness differs.

`PDF_ONLY` means that no arXiv source exists and the anchor was extracted from the canonical publisher PDF.

`REVIEW_REQUIRED` is restricted to source-versus-witness alignment: the passages may correspond, but their relationship or discrepancy cannot be resolved safely. It does not report root detection, macro expansion, or PDF transcription quality; those concerns retain their own preprocessing, expansion, and extraction fields.

Alignment status is chosen independently of macro-expansion status, in this precedence order: `PDF_ONLY` when no arXiv source exists; `SOURCE_ONLY` when no corresponding witness passage is available; `MATCHED` when corresponding passages have no material difference; `ARXIV_NEWER_PREFERRED` when they differ and arXiv is later; `PDF_CORRECTION_APPLIED` when arXiv is not later and the publication change is clear and unambiguous; otherwise `REVIEW_REQUIRED`. A failed or partial macro expansion does not change that alignment result.

For `SOURCE_ONLY`, `MATCHED`, and `ARXIV_NEWER_PREFERRED`, `aligned_content.content` contains the unchanged canonical representation when a downstream-safe representation exists. For `PDF_CORRECTION_APPLIED`, it contains only the clear publication correction derived from the unchanged source and witness representations. For `PDF_ONLY`, it contains the PDF extraction or a reviewed transcription. If no downstream-safe representation exists because preprocessing, expansion, or transcription is incomplete, `aligned_content.content`, `content_format`, and `content_sha256` are `null` until that separate review is complete. For alignment status `REVIEW_REQUIRED`, those three fields are always `null` until alignment review resolves the discrepancy; the canonical arXiv representation remains preserved but is not silently presented as aligned content.

These statuses describe individual anchor alignment. They do not replace canonical resolution status, preprocessing status, macro-expansion status, or extraction confidence.

## 8. Active-Source Replacement and Published-Release Preservation

The acquisition service exposes one current active canonical source artifact per work. A newer source occurrence may replace that active input, but it never rewrites a published repository release.

The active artifact changes when:

1. a newer arXiv source version becomes available;
2. arXiv source becomes available for a work currently represented by a publisher PDF; or
3. a corrected retrieval replaces a corrupt or incorrectly identified active artifact.

If arXiv source becomes available for a PDF-only work, the arXiv source becomes active and the existing publisher PDF becomes a publisher witness.

An active-source change must trigger:

```text
acquire and validate a new exact source occurrence
→ recompute artifact hashes
→ identify the root LaTeX document when applicable
→ regenerate head.tex, macro classification, and expansion
→ regenerate anchors, publisher-witness alignment, and aligned content
→ invalidate and supersede affected derived claims and relations
→ prepare a new repository commit
→ create a new tag, public Git release, and AgtXIv ReleaseManifest
```

No anchor is reused across source versions merely because a path, line, page, or label appears unchanged. The active workspace need not expose several source versions simultaneously, but every published release retains its exact source manifest, anchors, records, and registry snapshot and remains replayable.

## 9. Source Package

Each work release candidate uses the canonical `source/` subtree of its publication repository:

```text
source/
├── manifest.json
└── anchors.jsonl
```

`manifest.json` records stable work and publication-repository identity, exact source version, sanitized query provenance, latest-version resolution, canonical resolution, ordered retrieval attempts, stable locators, candidate validation and hashes, selected-attempt or comparison decisions, dates, extraction tools, macro-expansion policy, and alignment policy. Retrieval provenance must locate retained objects without treating a transport backend as a canonical source type.

`anchors.jsonl` records source passages, expanded mathematical content, publisher-witness locations, and derived aligned content. It is empty or absent unless canonical resolution is `RESOLVED`; unresolved-root preprocessing with status `REVIEW_REQUIRED` also produces no anchors.

Redistributable exact inputs may appear once under `source/upstream/`. Restricted artifacts remain external and are represented under `source/locators/` by stable retrieval metadata and independent hashes. Source-derived `head.tex` is audit material and has one canonical path. The manifest references these objects rather than creating parallel copies.

### 9.1 Registry wrapping and canonical references

After the repository tree is committed, `SourceRegistry` wraps the canonical payload in an immutable record:

```yaml
source_package_record:
  schema: agtxiv.source-package-record/1.0.0
  id: source-package:work-slug:source-version-slug
  record_revision: 1
  supersedes: null
  work_id: work:stable-id
  source_version_id: arxiv:xxxx.xxxxxvN
  work_repository_binding_ref: <exact WorkRepositoryBinding TargetRef>
  manifest_artifact:
    target_commit_oid: <full Git commit object ID>
    commit_path: source/manifest.json
    type_schema: agtxiv.paper-source/0.2
    serialization_profile: {id: rfc8785-json/1.0.0, content_hash: 'sha256:...'}
    artifact_hash: sha256:...
  canonical_source_artifact_ref: <exact registered source-artifact TargetRef>
  source_anchor_refs: [<canonically sorted exact SourceAnchor TargetRefs>]
  content_hash: sha256:...
```

This `SourcePackageRecord`, not the repository path alone, is the post-commit source target used by `ReleaseManifest`. An in-tree `PaperAgentManifest` records only source payload paths, schemas, and artifact hashes so that it does not depend indirectly on its own target commit. Each `anchors.jsonl` row is registered as an `agtxiv.source-anchor/1.1.0` record with immutable-envelope `id`, `record_revision`, `supersedes`, `work_id`, `source_version_id`, artifact address and hash, location, and `content_hash`. The committed `anchors.jsonl` file is a derived registry export carrying `derived_from` metadata; it is not a second authority. Registration fails if the payload work, source version, repository binding, commit, schema, or hashes disagree.

## 10. `manifest.json`

### 10.1 Canonical arXiv source with publisher witness

```json
{
  "schema_version": "agtxiv.paper-source/0.2",
  "work_id": "work:1609.07488",
  "source_version_id": "arxiv:1609.07488v3",
  "work_repository_binding_ref": {"id": "work-repository-binding:stable-id", "record_revision": 1, "content_hash": "sha256:..."},
  "redistribution_dispositions": [
    {
      "artifact_or_attempt_id": "attempt:kaggle:1",
      "artifact_sha256": "48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d",
      "rights_status": "REDISTRIBUTABLE",
      "decision_basis": "The recorded source license permits redistribution.",
      "public_tree_inclusion": "INCLUDED",
      "public_path": "source/upstream/arxiv-source-v3.tar",
      "local_quarantine_path": null
    },
    {
      "artifact_or_attempt_id": "publisher-witness:example-paper",
      "artifact_sha256": "93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135",
      "rights_status": "RESTRICTED",
      "decision_basis": "Publisher terms permit verification access but not public redistribution.",
      "public_tree_inclusion": "LOCATOR_ONLY",
      "public_path": null,
      "local_quarantine_path": "quarantine/example-paper/publisher.pdf"
    }
  ],
  "document_type": "PAPER",
  "query": {
    "query_type": "PAPER",
    "identifier_type": "ARXIV",
    "identifier": "1609.07488",
    "submitted_at": "2026-08-21T14:00:00Z",
    "deferred_question_present": true,
    "deferred_question_status": "DEFERRED"
  },
  "metadata": {
    "title": "Example Paper",
    "authors": [
      "First Author",
      "Second Author"
    ],
    "doi": "10.xxxx/example",
    "arxiv_id": "1609.07488",
    "publisher_publication_date": "2017-03-15"
  },
  "latest_version_resolution": {
    "authority": "ARXIV_METADATA",
    "source_url": "https://export.arxiv.org/api/query?id_list=1609.07488",
    "observed_at": "2026-08-21T09:55:00Z",
    "resolved_arxiv_id": "1609.07488",
    "resolved_arxiv_version": "v3",
    "status": "RESOLVED"
  },
  "canonical_resolution": {
    "status": "RESOLVED",
    "source_type": "ARXIV_SOURCE",
    "resolved_at": "2026-08-21T10:00:00Z"
  },
  "canonical_artifact": {
    "path": "source/upstream/arxiv-source-v3.tar",
    "media_type": "application/x-tar",
    "arxiv_version": 3,
    "arxiv_submitted_at": "2017-06-02T11:30:00Z",
    "entrypoint": "main.tex",
    "sha256": "48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d",
    "source_tree_sha256": "2ff8b234e1a86351c3c2c3529b94083bb08bd559cc4988b217e5fb9bb7d48e38"
  },
  "retrieval": {
    "official_cross_check": {
      "mode": "DISABLED",
      "trigger": null,
      "reason": "The default retrieval path accepts a validated dataset candidate."
    },
    "attempts": [
      {
        "attempt_id": "attempt:kaggle:1",
        "backend": "ARXIV_KAGGLE_DATASET",
        "locator": {
          "dataset_identifier": "<configured-source-dataset>",
          "dataset_revision": "<immutable-dataset-revision>",
          "snapshot_path": null,
          "snapshot_sha256": null,
          "member_path": "<member-for-1609.07488v3>",
          "source_url": null
        },
        "requested_arxiv_version": "v3",
        "attempted_at": "2026-08-21T09:58:00Z",
        "result": "SUCCEEDED",
        "candidate_path": "quarantine/example-paper/candidates/kaggle-v3.tar",
        "version_evidence": {
          "arxiv_id": "1609.07488",
          "arxiv_version": "v3",
          "basis": "<dataset-specific-version-evidence>"
        },
        "validation": {
          "status": "PASSED",
          "paper_arxiv_id": "MATCH",
          "arxiv_version": "MATCH",
          "archive_readable": true,
          "archive_extractable": true,
          "safe_paths": true,
          "source_payload_nonempty": true,
          "archive_sha256": "48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d",
          "source_tree_sha256": "2ff8b234e1a86351c3c2c3529b94083bb08bd559cc4988b217e5fb9bb7d48e38"
        }
      },
      {
        "attempt_id": "attempt:arxiv:2",
        "backend": "ARXIV_OFFICIAL_EPRINT",
        "locator": {
          "source_url": "https://arxiv.org/e-print/1609.07488v3"
        },
        "requested_arxiv_version": "v3",
        "attempted_at": null,
        "result": "NOT_ATTEMPTED",
        "reason": "The preferred dataset attempt succeeded.",
        "version_evidence": null,
        "validation": null
      }
    ],
    "selected_attempt": "attempt:kaggle:1",
    "comparison": null
  },
  "source_preprocessing": {
    "status": "READY",
    "method": "LATEX_SOURCE",
    "tool": "agtxiv-latex-reader",
    "generated_at": "2026-08-21T10:05:00Z",
    "head_file": {
      "path": "source/audit/head.tex",
      "sha256": "dcad2aeb52798a585f8f15d72d1bffceb911b4e91a54104d71f5f955632f0f85",
      "role": "PREPROCESSING_AND_AUDIT_ONLY"
    },
    "macro_expansion": {
      "tool": "agtxiv-latex-expander",
      "approved_vocabulary": "agtxiv-standard-latex/0.1",
      "semantic_math": "RECURSIVELY_EXPAND",
      "formatting": "REMOVE_WRAPPER_RETAIN_CONTENT",
      "document_control": "EXCLUDE_FROM_CLAIMS",
      "unresolved": "PRESERVE_AND_REQUIRE_REVIEW"
    }
  },
  "publisher_witness": {
    "path": "quarantine/example-paper/publisher.pdf",
    "media_type": "application/pdf",
    "source_url": "https://publisher.example/paper.pdf",
    "publication_date": "2017-03-15",
    "sha256": "93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135",
    "extraction": {
      "method": "PDF_TEXT",
      "tool": "pdf-extraction-skill",
      "generated_at": "2026-08-21T10:07:00Z"
    }
  },
  "alignment": {
    "tool": "agtxiv-source-aligner",
    "generated_at": "2026-08-21T10:10:00Z",
    "temporal_policy": "ARXIV_NEWER",
    "corrections_target": "ALIGNED_CONTENT_ONLY",
    "anchor_statuses_present": [
      "SOURCE_ONLY",
      "MATCHED",
      "ARXIV_NEWER_PREFERRED"
    ],
    "status_vocabulary": [
      "SOURCE_ONLY",
      "MATCHED",
      "PDF_CORRECTION_APPLIED",
      "ARXIV_NEWER_PREFERRED",
      "PDF_ONLY",
      "REVIEW_REQUIRED"
    ]
  }
}
```

For the clear-publication-correction branch, the same arXiv-canonical manifest structure records the following complete temporal and alignment decision. The publisher remains a witness, and only derived aligned content may change:

```json
{
  "canonical_artifact": {
    "arxiv_submitted_at": "2023-01-10T09:00:00Z"
  },
  "metadata": {
    "publisher_publication_date": "2023-04-20"
  },
  "alignment": {
    "tool": "agtxiv-source-aligner",
    "generated_at": "2026-08-21T10:10:00Z",
    "temporal_policy": "ARXIV_NOT_LATER",
    "corrections_target": "ALIGNED_CONTENT_ONLY",
    "anchor_statuses_present": [
      "MATCHED",
      "PDF_CORRECTION_APPLIED"
    ],
    "status_vocabulary": [
      "SOURCE_ONLY",
      "MATCHED",
      "PDF_CORRECTION_APPLIED",
      "ARXIV_NEWER_PREFERRED",
      "PDF_ONLY",
      "REVIEW_REQUIRED"
    ]
  }
}
```

### 10.2 Publisher-PDF-only fallback

```json
{
  "schema_version": "agtxiv.paper-source/0.2",
  "work_id": "work:doi:10.xxxx/example",
  "source_version_id": "publisher-pdf:sha256:93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135",
  "work_repository_binding_ref": {"id": "work-repository-binding:stable-id", "record_revision": 1, "content_hash": "sha256:..."},
  "redistribution_dispositions": [
    {
      "artifact_or_attempt_id": "attempt:publisher:3",
      "artifact_sha256": "93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135",
      "rights_status": "RESTRICTED",
      "decision_basis": "Publisher terms permit verification access but not public redistribution.",
      "public_tree_inclusion": "LOCATOR_ONLY",
      "public_path": null,
      "local_quarantine_path": "quarantine/example-paper/candidates/publisher.pdf"
    }
  ],
  "document_type": "PAPER",
  "query": {
    "query_type": "PAPER",
    "identifier_type": "DOI",
    "identifier": "10.xxxx/example",
    "submitted_at": "2026-08-21T14:00:00Z",
    "deferred_question_present": false,
    "deferred_question_status": null
  },
  "metadata": {
    "title": "Example Paper",
    "authors": ["First Author", "Second Author"],
    "doi": "10.xxxx/example",
    "arxiv_id": "<arxiv-id>",
    "publisher_publication_date": "2024-05-17"
  },
  "latest_version_resolution": {
    "authority": "ARXIV_METADATA",
    "source_url": "<authoritative-arxiv-metadata-url>",
    "observed_at": "2026-08-21T09:55:00Z",
    "resolved_arxiv_id": "<arxiv-id>",
    "resolved_arxiv_version": "v2",
    "status": "RESOLVED"
  },
  "canonical_resolution": {
    "status": "RESOLVED",
    "source_type": "PUBLISHER_PDF",
    "resolved_at": "2026-08-21T10:00:00Z"
  },
  "canonical_artifact": {
    "path": "quarantine/example-paper/publisher.pdf",
    "media_type": "application/pdf",
    "source_url": "https://publisher.example/paper.pdf",
    "publication_date": "2024-05-17",
    "sha256": "93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135"
  },
  "retrieval": {
    "attempts": [
      {
        "attempt_id": "attempt:kaggle:1",
        "backend": "ARXIV_KAGGLE_DATASET",
        "locator": {
          "dataset_identifier": "<configured-source-dataset>",
          "dataset_revision": "<immutable-dataset-revision>",
          "snapshot_path": null,
          "snapshot_sha256": null,
          "member_path": "<member-for-requested-version>",
          "source_url": null
        },
        "requested_arxiv_version": "v2",
        "attempted_at": "2026-08-21T09:56:00Z",
        "result": "NOT_FOUND",
        "reason": "The immutable dataset revision contains no member for the exact version.",
        "version_evidence": null,
        "validation": null
      },
      {
        "attempt_id": "attempt:arxiv:2",
        "backend": "ARXIV_OFFICIAL_EPRINT",
        "locator": {"source_url": "<official-eprint-url-for-v2>"},
        "requested_arxiv_version": "v2",
        "attempted_at": "2026-08-21T09:57:00Z",
        "result": "NOT_FOUND",
        "reason": "The official endpoint deterministically reported no source for the exact version.",
        "version_evidence": null,
        "validation": null
      },
      {
        "attempt_id": "attempt:publisher:3",
        "backend": "PUBLISHER_URL",
        "locator": {"source_url": "https://publisher.example/paper.pdf"},
        "requested_arxiv_version": null,
        "attempted_at": "2026-08-21T09:58:00Z",
        "result": "SUCCEEDED",
        "candidate_path": "quarantine/example-paper/candidates/publisher.pdf",
        "version_evidence": null,
        "validation": {
          "status": "PASSED",
          "document_readable": true,
          "payload_nonempty": true,
          "document_sha256": "93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135"
        }
      }
    ],
    "selected_attempt": "attempt:publisher:3",
    "comparison": null
  },
  "source_preprocessing": {
    "status": "READY",
    "method": "OCR",
    "tool": "existing-ocr-skill",
    "generated_at": "2026-08-21T10:05:00Z",
    "head_file": null,
    "macro_expansion": null
  },
  "publisher_witness": null,
  "alignment": {
    "tool": null,
    "generated_at": "2026-08-21T10:05:00Z",
    "temporal_policy": "PDF_ONLY",
    "corrections_target": "ALIGNED_CONTENT_ONLY",
    "anchor_statuses_present": ["PDF_ONLY"],
    "status_vocabulary": [
      "SOURCE_ONLY",
      "MATCHED",
      "PDF_CORRECTION_APPLIED",
      "ARXIV_NEWER_PREFERRED",
      "PDF_ONLY",
      "REVIEW_REQUIRED"
    ]
  }
}
```

If the PDF has a reliable text layer, `source_preprocessing.method` is `PDF_TEXT`. OCR use must identify the OCR tool and must not replace the canonical PDF.

`retrieval.attempts` is ordered and includes successful, failed, inapplicable, and skipped attempts. Each attempt records a backend, stable locator, requested version when applicable, time, result, and validation and hashes when bytes were obtained. An attempt that obtains bytes also records `candidate_path`. `selected_attempt` is the successful attempt that supplied the canonical artifact; it is `null` for blocked and unavailable states. `comparison` references attempt identifiers rather than copying implicit backend state. `official_cross_check` records whether post-success official verification is disabled or enabled and why.

For Kaggle, either `locator.dataset_revision` is an immutable dataset version or revision, or both `snapshot_path` and `snapshot_sha256` identify a retained local snapshot. At least one of those alternatives must be complete. Angle-bracket strings in these examples are neutral placeholders, not claims about a real dataset identifier, member layout, or URL. A mutable slug and observation date alone are insufficient.

For arXiv source, `validation.archive_sha256` is locally computed over retrieved archive bytes and `validation.source_tree_sha256` is the basis for backend comparison. Publisher attempts instead record a local `document_sha256`. These fields do not imply a Kaggle-provided checksum or real-time dataset freshness. Publisher retrieval uses `PUBLISHER_URL` and may proceed only after the ordered arXiv evidence satisfies Section 3.2.

### 10.3 Unavailable source

```json
{
  "schema_version": "agtxiv.paper-source/0.2",
  "work_id": "work:doi:10.xxxx/example",
  "source_version_id": null,
  "work_repository_binding_ref": {"id": "work-repository-binding:stable-id", "record_revision": 1, "content_hash": "sha256:..."},
  "redistribution_dispositions": [],
  "document_type": "PAPER",
  "query": {
    "query_type": "PAPER",
    "identifier_type": "DOI",
    "identifier": "10.xxxx/example",
    "submitted_at": "2026-08-21T14:00:00Z",
    "deferred_question_present": false,
    "deferred_question_status": null
  },
  "metadata": {
    "title": "Example Paper",
    "authors": [],
    "doi": "10.xxxx/example",
    "arxiv_id": null,
    "publisher_publication_date": null
  },
  "latest_version_resolution": {
    "authority": "ARXIV_METADATA",
    "source_url": "<authoritative-arxiv-metadata-url>",
    "observed_at": "2026-08-21T09:55:00Z",
    "resolved_arxiv_id": null,
    "resolved_arxiv_version": null,
    "status": "NOT_FOUND"
  },
  "canonical_resolution": {
    "status": "UNAVAILABLE",
    "resolved_at": "2026-08-21T10:00:00Z",
    "reason": "Authoritative metadata found no arXiv record, and no publisher PDF was available."
  },
  "canonical_artifact": null,
  "retrieval": {
    "attempts": [
      {
        "attempt_id": "attempt:kaggle:1",
        "backend": "ARXIV_KAGGLE_DATASET",
        "locator": null,
        "requested_arxiv_version": null,
        "attempted_at": null,
        "result": "NOT_APPLICABLE",
        "reason": "Authoritative metadata found no arXiv record.",
        "version_evidence": null,
        "validation": null
      },
      {
        "attempt_id": "attempt:arxiv:2",
        "backend": "ARXIV_OFFICIAL_EPRINT",
        "locator": null,
        "requested_arxiv_version": null,
        "attempted_at": null,
        "result": "NOT_APPLICABLE",
        "reason": "Authoritative metadata found no arXiv record.",
        "version_evidence": null,
        "validation": null
      },
      {
        "attempt_id": "attempt:publisher:3",
        "backend": "PUBLISHER_URL",
        "locator": {"source_url": "https://publisher.example/paper.pdf"},
        "requested_arxiv_version": null,
        "attempted_at": "2026-08-21T09:58:00Z",
        "result": "NOT_FOUND",
        "reason": "The publisher deterministically reported no PDF at the resolved article location.",
        "version_evidence": null,
        "validation": null
      }
    ],
    "selected_attempt": null,
    "comparison": null
  },
  "source_preprocessing": null,
  "publisher_witness": null,
  "alignment": null
}
```

### 10.4 Blocked acquisition branches

A transient metadata or backend failure blocks fallback and produces a retryable manifest branch:

```json
{
  "latest_version_resolution": {
    "authority": "ARXIV_METADATA",
    "source_url": "<authoritative-arxiv-metadata-url>",
    "observed_at": "2026-08-21T09:55:00Z",
    "resolved_arxiv_id": null,
    "resolved_arxiv_version": null,
    "status": "TRANSIENT_FAILURE"
  },
  "canonical_resolution": {"status": "RETRY_REQUIRED", "reason": "Authoritative arXiv metadata timed out."},
  "canonical_artifact": null,
  "retrieval": {
    "attempts": [
      {"attempt_id": "attempt:kaggle:1", "backend": "ARXIV_KAGGLE_DATASET", "locator": null, "requested_arxiv_version": null, "attempted_at": null, "result": "NOT_ATTEMPTED", "reason": "Latest-version resolution must be retried.", "version_evidence": null, "validation": null}
    ],
    "selected_attempt": null,
    "comparison": null
  },
  "source_preprocessing": null,
  "alignment": null
}
```

Different source trees for the same exact version require review. This branch is reachable when an enabled official cross-check follows a successful Kaggle attempt:

```json
{
  "latest_version_resolution": {
    "authority": "ARXIV_METADATA",
    "source_url": "<authoritative-arxiv-metadata-url>",
    "observed_at": "2026-08-21T09:55:00Z",
    "resolved_arxiv_id": "<arxiv-id>",
    "resolved_arxiv_version": "v2",
    "status": "RESOLVED"
  },
  "canonical_resolution": {"status": "REVIEW_REQUIRED", "reason": "Cross-checked exact-version candidates have different source trees."},
  "canonical_artifact": null,
  "retrieval": {
    "official_cross_check": {
      "mode": "FIRST_SEEN_DATASET_REVISION",
      "trigger": "FIRST_CANDIDATE_FROM_REVISION",
      "reason": "Audit the first successful candidate from this immutable dataset revision."
    },
    "attempts": [
      {
        "attempt_id": "attempt:kaggle:1",
        "backend": "ARXIV_KAGGLE_DATASET",
        "locator": {"dataset_identifier": "<configured-source-dataset>", "dataset_revision": "<immutable-dataset-revision>", "snapshot_path": null, "snapshot_sha256": null, "member_path": "<member-for-requested-version>", "source_url": null},
        "requested_arxiv_version": "v2",
        "attempted_at": "2026-08-21T09:56:00Z",
        "result": "SUCCEEDED",
        "candidate_path": "quarantine/example-paper/candidates/kaggle-v2.tar",
        "version_evidence": {"arxiv_id": "<arxiv-id>", "arxiv_version": "v2", "basis": "<dataset-specific-version-evidence>"},
        "validation": {
          "status": "PASSED",
          "paper_arxiv_id": "MATCH",
          "arxiv_version": "MATCH",
          "archive_readable": true,
          "archive_extractable": true,
          "safe_paths": true,
          "source_payload_nonempty": true,
          "archive_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "source_tree_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        }
      },
      {
        "attempt_id": "attempt:arxiv:2",
        "backend": "ARXIV_OFFICIAL_EPRINT",
        "locator": {"source_url": "<official-eprint-url-for-v2>"},
        "requested_arxiv_version": "v2",
        "attempted_at": "2026-08-21T09:57:00Z",
        "result": "SUCCEEDED",
        "trigger": "OFFICIAL_CROSS_CHECK",
        "reason": "The configured mode cross-checks the first candidate from this dataset revision.",
        "candidate_path": "quarantine/example-paper/candidates/official-v2.tar",
        "version_evidence": {"arxiv_id": "<arxiv-id>", "arxiv_version": "v2", "basis": "OFFICIAL_VERSIONED_ENDPOINT"},
        "validation": {
          "status": "PASSED",
          "paper_arxiv_id": "MATCH",
          "arxiv_version": "MATCH",
          "archive_readable": true,
          "archive_extractable": true,
          "safe_paths": true,
          "source_payload_nonempty": true,
          "archive_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "source_tree_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
        }
      }
    ],
    "selected_attempt": null,
    "comparison": {
      "status": "REVIEW_REQUIRED",
      "candidates": [
        {"attempt_id": "attempt:kaggle:1", "candidate_path": "quarantine/example-paper/candidates/kaggle-v2.tar", "archive_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "source_tree_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
        {"attempt_id": "attempt:arxiv:2", "candidate_path": "quarantine/example-paper/candidates/official-v2.tar", "archive_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "source_tree_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"}
      ]
    }
  },
  "source_preprocessing": null,
  "publisher_witness": null,
  "alignment": null
}
```

### 10.5 Official endpoint succeeds after dataset miss

The following complete retrieval and canonical fragment shows the official endpoint becoming the selected transport after deterministic Kaggle `NOT_FOUND`. The same structure applies after a deterministic Kaggle `INVALID_CANDIDATE`, with its retained candidate and validation evidence added to the first attempt.

```json
{
  "latest_version_resolution": {
    "authority": "ARXIV_METADATA",
    "source_url": "<authoritative-arxiv-metadata-url>",
    "observed_at": "2026-08-21T09:55:00Z",
    "resolved_arxiv_id": "<arxiv-id>",
    "resolved_arxiv_version": "v2",
    "status": "RESOLVED"
  },
  "canonical_resolution": {
    "status": "RESOLVED",
    "source_type": "ARXIV_SOURCE",
    "resolved_at": "2026-08-21T10:00:00Z"
  },
  "canonical_artifact": {
    "path": "source/upstream/arxiv-source-v2.tar",
    "media_type": "application/x-tar",
    "arxiv_version": 2,
    "arxiv_submitted_at": "2024-05-01T12:00:00Z",
    "entrypoint": "main.tex",
    "sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "source_tree_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  },
  "retrieval": {
    "official_cross_check": {"mode": "DISABLED", "trigger": null, "reason": "The official request is required fallback, not a post-success cross-check."},
    "attempts": [
      {
        "attempt_id": "attempt:kaggle:1",
        "backend": "ARXIV_KAGGLE_DATASET",
        "locator": {"dataset_identifier": "<configured-source-dataset>", "dataset_revision": "<immutable-dataset-revision>", "snapshot_path": null, "snapshot_sha256": null, "member_path": "<member-for-requested-version>", "source_url": null},
        "requested_arxiv_version": "v2",
        "attempted_at": "2026-08-21T09:56:00Z",
        "result": "NOT_FOUND",
        "reason": "The immutable dataset revision contains no member for the exact version.",
        "version_evidence": null,
        "validation": null
      },
      {
        "attempt_id": "attempt:arxiv:2",
        "backend": "ARXIV_OFFICIAL_EPRINT",
        "locator": {"source_url": "<official-eprint-url-for-v2>"},
        "requested_arxiv_version": "v2",
        "attempted_at": "2026-08-21T09:57:00Z",
        "result": "SUCCEEDED",
        "trigger": "FALLBACK_AFTER_KAGGLE_NOT_FOUND",
        "reason": "The dataset had no exact-version member.",
        "candidate_path": "quarantine/example-paper/candidates/official-v2.tar",
        "version_evidence": {"arxiv_id": "<arxiv-id>", "arxiv_version": "v2", "basis": "OFFICIAL_VERSIONED_ENDPOINT"},
        "validation": {
          "status": "PASSED",
          "paper_arxiv_id": "MATCH",
          "arxiv_version": "MATCH",
          "archive_readable": true,
          "archive_extractable": true,
          "safe_paths": true,
          "source_payload_nonempty": true,
          "archive_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
          "source_tree_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        }
      }
    ],
    "selected_attempt": "attempt:arxiv:2",
    "comparison": null
  }
}
```

## 11. `anchors.jsonl`

Each line of `anchors.jsonl` is one JSON object. An anchor connects derived content to exact evidence in the current canonical artifact and, when available, the publisher witness.

Every anchor must contain:

- a stable anchor identifier within the current source package;
- the paper identifier;
- the current canonical artifact hash;
- a canonical location;
- a content kind;
- derived aligned content and its alignment status;
- hashes for stored content representations;
- publisher-witness evidence when used.

ArXiv-derived mathematical anchors must also contain exact `raw_latex` and a macro-expansion object. `expanded_latex` is non-null only for `EXPANDED`; partial and failed cases use the fields defined in Section 5.4. PDF-only anchors do not have source LaTeX; their `raw_latex` and macro-expansion fields are `null`.

### 11.1 Matched arXiv and publisher content

```json
{"anchor_id":"anchor:example-paper:001","work_id":"work:1609.07488","source_version_id":"arxiv:1609.07488v3","canonical_artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","content_kind":"MATHEMATICS","source_location":{"type":"LATEX_LINES","file":"main.tex","line_start":120,"line_end":124,"section":"Main Result","structural_type":"theorem","label":"thm:main"},"raw_latex":"\\begin{theorem}\\label{thm:main} For every $\\rho\\in\\Dens(\\cH)$, $\\RoM(\\rho)\\geq 1$. \\end{theorem}","raw_latex_sha256":"8a8e84652117d16d3fc821cf33139fd4b7bb7952327a979955d28f22fc98180e","macro_expansion":{"status":"EXPANDED","approved_vocabulary":"agtxiv-standard-latex/0.1","expanded_latex":"For every $\\rho\\in\\mathcal{D}(\\mathcal{H})$, $\\operatorname{RoM}(\\rho)\\geq 1$.","expanded_latex_sha256":"b378095fd4c67e1d42e062806268152e8f635db0d4a2552f1fc83df965ea2532","partial_expansion_latex":null,"unresolved_macros":[]},"publisher_witness":{"artifact_sha256":"93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135","location":{"type":"PDF_REGION","page":5,"bounding_box":[72,214,510,328]},"extraction_method":"PDF_TEXT","extracted_text":"Theorem 1. For every rho in D(H), RoM(rho) is at least 1.","extracted_text_sha256":"40ea2b694d7b795260e216115249703e391abbeb2b32fad72390f860efdc9e0d"},"aligned_content":{"status":"MATCHED","content_format":"STANDARD_LATEX","content":"For every $\\rho\\in\\mathcal{D}(\\mathcal{H})$, $\\operatorname{RoM}(\\rho)\\geq 1$.","content_sha256":"b378095fd4c67e1d42e062806268152e8f635db0d4a2552f1fc83df965ea2532","resolution_basis":"The arXiv source and publisher witness state the same mathematical claim."},"automatic_math_normalization_eligible":true}
```

### 11.2 Later arXiv content preferred

```json
{"anchor_id":"anchor:example-paper:002","work_id":"work:1609.07488","source_version_id":"arxiv:1609.07488v3","canonical_artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","content_kind":"MATHEMATICS","source_location":{"type":"LATEX_LINES","file":"appendix.tex","line_start":42,"line_end":46,"section":"Corrections","structural_type":"lemma","label":"lem:corrected-bound"},"raw_latex":"\\begin{lemma}\\label{lem:corrected-bound} If $n\\geq 2$, then $f(n)\\leq n^2+1$. \\end{lemma}","raw_latex_sha256":"6924e8d4dd97238a47bcf1352db872ecca05b07637d51f85603b9f5120ec776d","macro_expansion":{"status":"EXPANDED","approved_vocabulary":"agtxiv-standard-latex/0.1","expanded_latex":"If $n\\geq 2$, then $f(n)\\leq n^2+1$.","expanded_latex_sha256":"21851044eb05bded444b3ac10f86007da27e20fb08c3aea7be8ce788fcc31ebb","partial_expansion_latex":null,"unresolved_macros":[]},"publisher_witness":{"artifact_sha256":"93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135","location":{"type":"PDF_REGION","page":11,"bounding_box":[70,180,515,260]},"extraction_method":"PDF_TEXT","extracted_text":"Lemma 4. If n is at least 1, then f(n) is at most n squared.","extracted_text_sha256":"6cad1e57978ef22c616080741e1c5f3614969c537e0c1e77e7d721898b73fd85"},"aligned_content":{"status":"ARXIV_NEWER_PREFERRED","content_format":"STANDARD_LATEX","content":"If $n\\geq 2$, then $f(n)\\leq n^2+1$.","content_sha256":"21851044eb05bded444b3ac10f86007da27e20fb08c3aea7be8ce788fcc31ebb","resolution_basis":"The canonical arXiv version was submitted after publication; the older publisher wording does not override it."},"automatic_math_normalization_eligible":true}
```

### 11.3 Clear publisher correction applied to derived content

```json
{"anchor_id":"anchor:example-paper:003","work_id":"work:example","source_version_id":"arxiv:examplev1","canonical_artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","content_kind":"MATHEMATICS","source_location":{"type":"LATEX_LINES","file":"main.tex","line_start":210,"line_end":214,"section":"Bounds","structural_type":"lemma","label":"lem:published-bound"},"raw_latex":"\\begin{lemma}\\label{lem:published-bound} If $n\\geq 2$, then $f(n)\\leq n^2$. \\end{lemma}","raw_latex_sha256":"347f5ac8c0c5a8abb016bd83b6ee80d33c59d5c14937ff55fc81b1338157bac9","macro_expansion":{"status":"EXPANDED","approved_vocabulary":"agtxiv-standard-latex/0.1","expanded_latex":"If $n\\geq 2$, then $f(n)\\leq n^2$.","expanded_latex_sha256":"e2fe75db00794480221d612689e7b69ae5cd275cea21ca46d57ad5b1e81e207c","partial_expansion_latex":null,"unresolved_macros":[]},"publisher_witness":{"artifact_sha256":"93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135","location":{"type":"PDF_REGION","page":8,"bounding_box":[70,180,515,260]},"extraction_method":"PDF_TEXT","extracted_text":"Lemma 3. If n is at least 2, then f(n) is at most n squared plus 1.","extracted_text_sha256":"e79afe926010c028c2765501db0d385fb4a7f0d55549290c2871ba589804c0ba"},"aligned_content":{"status":"PDF_CORRECTION_APPLIED","content_format":"STANDARD_LATEX","content":"If $n\\geq 2$, then $f(n)\\leq n^2+1$.","content_sha256":"21851044eb05bded444b3ac10f86007da27e20fb08c3aea7be8ce788fcc31ebb","resolution_basis":"The arXiv source predates publication, and the publisher witness unambiguously adds the term +1 to the bound; only aligned_content applies that change."},"automatic_math_normalization_eligible":true}
```

The manifest branch for this anchor uses `ARXIV_NOT_LATER`. The canonical arXiv source, its `raw_latex`, its expanded source representation, and the publisher witness remain unchanged.

### 11.4 ArXiv source without a matched witness passage

```json
{"anchor_id":"anchor:example-paper:004","work_id":"work:1609.07488","source_version_id":"arxiv:1609.07488v3","canonical_artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","content_kind":"MATHEMATICS","source_location":{"type":"LATEX_LINES","file":"supplement.tex","line_start":88,"line_end":91,"section":"Supplementary Lemmas","structural_type":"lemma","label":"lem:aux"},"raw_latex":"\\begin{lemma}\\label{lem:aux} $g(0)=0$. \\end{lemma}","raw_latex_sha256":"2c82d1b9356e84182a7a184dac8a377f508a234f6f8061a16929102aacc9cb10","macro_expansion":{"status":"EXPANDED","approved_vocabulary":"agtxiv-standard-latex/0.1","expanded_latex":"$g(0)=0$.","expanded_latex_sha256":"6e8d4ad71b4f72804e82bfb07ed1e6e9b25895fa55d0d87812da2be73738ddce","partial_expansion_latex":null,"unresolved_macros":[]},"publisher_witness":null,"aligned_content":{"status":"SOURCE_ONLY","content_format":"STANDARD_LATEX","content":"$g(0)=0$.","content_sha256":"6e8d4ad71b4f72804e82bfb07ed1e6e9b25895fa55d0d87812da2be73738ddce","resolution_basis":"The canonical arXiv source contains the passage, and no corresponding publisher-witness passage is available."},"automatic_math_normalization_eligible":true}
```

### 11.5 Publisher-PDF-only content

```json
{"anchor_id":"anchor:example-paper:005","work_id":"work:doi:10.xxxx/example","source_version_id":"publisher-pdf:sha256:93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135","canonical_artifact_sha256":"93fb61d8b94fd76116428bdcc44ea396ea5a4caad62a42353486c007541f9135","content_kind":"MATHEMATICS","source_location":{"type":"PDF_REGION","page":7,"bounding_box":[72,214,510,328]},"raw_latex":null,"raw_latex_sha256":null,"macro_expansion":null,"pdf_extraction":{"method":"OCR","tool":"existing-ocr-skill","extracted_text":"For every state rho, F of rho is less than or equal to g of n.","extracted_text_sha256":"85020f1d94b670fc6252bdefe4a78cf40ddcb110362a8b76f2f894bb06d9fe87","confidence":0.97},"publisher_witness":null,"aligned_content":{"status":"PDF_ONLY","content_format":"EXTRACTED_TEXT","content":"For every state rho, F of rho is less than or equal to g of n.","content_sha256":"85020f1d94b670fc6252bdefe4a78cf40ddcb110362a8b76f2f894bb06d9fe87","resolution_basis":"No arXiv source exists; content was extracted from the canonical publisher PDF."},"automatic_math_normalization_eligible":false}
```

A `PDF_CORRECTION_APPLIED` anchor contains both arXiv and publisher evidence. Its `aligned_content.content` contains the clear publication correction, and its `resolution_basis` records the exact difference and why automatic application was unambiguous.

An alignment-`REVIEW_REQUIRED` anchor preserves every available representation, sets the aligned content fields to `null`, and sets `automatic_math_normalization_eligible` to `false` until alignment review completes.

## 12. Minimum Validation Rules

A source package is valid only if:

1. `query.query_type` and `document_type` are `PAPER`, and processing inputs exclude deferred-question text;
2. `canonical_resolution.status` is `RESOLVED`, `UNAVAILABLE`, `RETRY_REQUIRED`, or `REVIEW_REQUIRED`;
3. only `RESOLVED` has exactly one active `canonical_artifact` and a non-null `retrieval.selected_attempt`;
4. `UNAVAILABLE`, canonical `RETRY_REQUIRED`, and canonical `REVIEW_REQUIRED` have null canonical artifact, preprocessing, and alignment and produce no anchors;
5. `latest_version_resolution` records authority, URL, observation time, resolved arXiv identity and exact version when found, and `RESOLVED`, `NOT_FOUND`, or `TRANSIENT_FAILURE` status;
6. metadata or backend `TRANSIENT_FAILURE`, including suspected truncation, transport corruption, or retryable validation failure, produces `RETRY_REQUIRED`, blocks publisher fallback, and preserves attempt provenance;
7. every retrieval attempt uses `SUCCEEDED`, `NOT_FOUND`, `INVALID_CANDIDATE`, `TRANSIENT_FAILURE`, `NOT_APPLICABLE`, or `NOT_ATTEMPTED` and records a reason when it does not succeed;
8. an official `INVALID_CANDIDATE` never permits publisher fallback: deterministic official identity, version, or content conflict produces canonical `REVIEW_REQUIRED`, while suspected transport damage is `TRANSIENT_FAILURE`;
9. arXiv source remains canonical regardless of transport, and a configured Kaggle source backend actually contains source archives rather than metadata alone;
10. each Kaggle attempt that is actually requested or obtains a candidate has an immutable dataset revision, or a retained snapshot path and SHA-256, plus its dataset-specific member location; `NOT_APPLICABLE` and `NOT_ATTEMPTED` may have null locator and version evidence but must have a reason;
11. a mutable dataset slug and date alone are not accepted as a stable locator, and each obtained Kaggle candidate records version evidence;
12. every attempt that obtains any bytes records a retained `candidate_path`; canonical `REVIEW_REQUIRED` preserves all conflicting candidate paths;
13. each valid arXiv candidate matches the paper identifier and exact requested latest version, is readable and extractable, contains a non-empty source payload, rejects absolute and traversing paths, and rejects every symbolic and hard link;
14. each obtained arXiv archive records local `archive_sha256`, and each successfully extracted archive records deterministic `source_tree_sha256`;
15. the source-tree manifest contains only regular files as fixed `path`/`type: "file"`/`sha256` objects; paths are relative POSIX, valid UTF-8, neither normalized nor case-folded, and sorted by UTF-8 bytes before RFC 8785 canonical JSON encoding and SHA-256;
16. same-version comparison uses source-tree hashes: equal trees are `MATCHED`, while different trees are canonical `REVIEW_REQUIRED`; archive-byte differences alone are not a conflict;
17. `official_cross_check` may cause an official attempt after Kaggle `SUCCEEDED`; its mode and trigger are recorded, and the official attempt records its trigger and reason;
18. Kaggle `NOT_FOUND` or deterministic `INVALID_CANDIDATE` triggers the official endpoint and never independently permits publisher fallback;
19. publisher fallback is allowed only if no valid exact-version arXiv candidate exists and either authoritative metadata confirms no arXiv record or the official endpoint deterministically returns `NOT_FOUND`; a cross-check `NOT_FOUND` never displaces a validated Kaggle candidate;
20. a resolved canonical artifact records its path, media type, locally computed SHA-256, and selected-attempt locator; canonical arXiv source also records version, submission date, and source-tree hash matching the selected attempt;
21. canonical arXiv preprocessing is `READY` or `REVIEW_REQUIRED`; `READY` records a root entry point and source-derived `head.tex`, while unresolved-root review has null entry point and head file and no anchors;
22. `head.tex` is preprocessing and audit material, not canonical content;
23. every arXiv-derived mathematical anchor preserves exact `raw_latex`; only `EXPANDED` approved-vocabulary mathematics is automatically eligible for math-claim normalization;
24. unresolved macros are preserved and never guessed, and partial or failed expansion has null `expanded_latex`;
25. publisher PDF extraction uses `PDF_TEXT` or `OCR`, and OCR remains derived evidence tied to the PDF hash;
26. a publisher PDF accompanying canonical arXiv source is a publisher witness, not a second canonical artifact;
27. alignment changes appear only in derived `aligned_content`; later arXiv content is not overwritten by an older witness, and ambiguous source-witness discrepancies receive alignment `REVIEW_REQUIRED` with null aligned content;
28. every anchor and witness location refers to the current corresponding artifact hash;
29. `work_id` is stable across source versions, `work_repository_binding_ref` resolves to the unique eligible `WorkRegistry` binding head, and the payload work ID agrees with that binding;
30. `source_version_id` identifies one exact source occurrence and is never a floating ``latest'' value; it is null exactly when no canonical source occurrence has been resolved;
31. no branch, mutable tag name, or repository path substitutes for a full release binding, independent artifact hash, or canonical `TargetRef`;
32. `redistribution_dispositions` has exactly one entry for every obtained canonical source, publisher witness, supplement, and retrieval candidate; each entry records its byte hash, rights status, decision basis, public-tree inclusion mode, and mutually consistent public or quarantine paths. The package-level summary, if emitted, is derived from these entries. Quarantined or restricted bytes are excluded from the public tree, with omitted restricted artifacts represented by exact hashes and stable locators; and
33. active-source replacement invalidates and supersedes affected current outputs without changing any previously published release binding.

## 13. MVP Boundary

This acquisition profile deliberately does not:

- support thesis, book, dataset, or software queries;
- expose several source versions as simultaneously active acquisition inputs, although every published release remains immutable and replayable;
- maintain multiple canonical artifacts;
- treat a retrieval backend, including the arXiv Kaggle dataset, as a canonical source type or authority;
- treat publisher presentation as automatically authoritative over arXiv source;
- modify an original arXiv bundle or publisher PDF;
- guess unresolved macro meanings;
- treat `head.tex` as canonical paper content;
- require downstream stages to interpret author-defined commands;
- apply ambiguous or substantial publication differences automatically;
- assess scientific correctness during source acquisition or alignment;
- prescribe one universal PDF parser or OCR implementation;
- extract claims before canonical resolution succeeds;
- use or answer a deferred question before every configured stage has produced a final explicit result; or
- treat OCR output as a replacement for the source PDF.

The next pipeline stage begins only after a resolved source package and its anchors are available. Downstream processing uses derived aligned content while retaining links to stable work identity, publication repository, exact source version, canonical source, raw LaTeX, macro expansion, publisher-witness evidence, and alignment decisions. Any deferred question remains isolated until the completed pipeline exposes final records to the query-response stage.
