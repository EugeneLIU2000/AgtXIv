# AgtXIv Paper Source Acquisition

**Status:** Normative MVP specification

**Schema version:** `agtxiv.paper-source/0.1`

**Scope:** Paper queries and canonical full-text acquisition

## 1. Purpose

This specification defines the first step after a user submits a paper query. The purpose of this step is to obtain one authoritative full-text artifact, extract its content, and record source locations that later claim-processing steps can cite.

This step does not assess whether the paper is correct. It only answers:

1. Which paper does the query identify?
2. What is the highest-priority full-text artifact currently available?
3. Where does each extracted passage occur in that artifact?

## 2. Supported Query

AgtXIv v0.1 supports only `PAPER` queries. A `PAPER` query requests complete ingestion and processing of one paper. It does not ask the acquisition or analysis stages to answer a research question.

A query may identify a paper by:

1. DOI;
2. arXiv identifier;
3. publisher article URL; or
4. title search.

DOI and arXiv identifiers are preferred because they identify papers more reliably than titles. A title search must first resolve to a single paper record before source acquisition begins.

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

A user may include a question about the paper. AgtXIv stores that question verbatim but does not use it to guide paper processing:

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

While the pipeline is running, the deferred question must not influence:

- canonical-source selection;
- content extraction;
- anchor generation;
- claim extraction;
- dependency construction;
- verification scope or outcome.

The complete paper is processed in the same way whether the deferred question is present or absent. This prevents the question from causing selective reading, omitted assumptions, confirmation bias, or premature summarization.

The question is considered only after the paper has completed the configured AgtXIv pipeline. Pipeline completion means that every configured stage has produced an explicit result, including blocked, unresolved, or not-applicable results; it does not mean that every claim is fully verified.

A deferred question has the following lifecycle:

```text
DEFERRED
ANSWERED
BLOCKED
```

`ANSWERED` means that the final claims, source anchors, dependencies, and verification records produced by the completed configured pipeline support a grounded response. The response must be derived only from those final records; intermediate records and outside knowledge must not supply the answer. `BLOCKED` means that the completed final records do not support a reliable answer. A blocked question must not be answered by guessing. The final answer record is produced by the end-of-pipeline query-response stage; its detailed format is outside the scope of this source-acquisition specification.

## 3. Canonical Artifact

A canonical artifact is the full-text object from which AgtXIv treats the paper's content as authoritative. Canonical status concerns the identity and content of the paper, not its scientific correctness.

AgtXIv v0.1 uses the following strict priority order:

1. **Publisher PDF.** If the publisher-provided PDF can be obtained, it is the canonical artifact.
2. **Latest arXiv source.** If the publisher PDF cannot be obtained, the source bundle of the latest available arXiv version is the canonical artifact.
3. **Unavailable.** If neither source can be obtained, canonical resolution is unavailable.

The MVP does not compare the publisher PDF against the arXiv source and does not maintain separate authority and extraction artifacts.

When an arXiv source bundle is canonical, the bundle is the canonical artifact. The manifest also records the root LaTeX entry point used to read the manuscript.

## 4. Canonical Resolution Status

Canonical resolution has exactly two states:

```text
RESOLVED
UNAVAILABLE
```

### 4.1 `RESOLVED`

`RESOLVED` means that AgtXIv obtained either:

- the publisher PDF; or
- if that PDF was unavailable, the latest arXiv source bundle.

Only a resolved paper may proceed to content extraction and anchor generation.

### 4.2 `UNAVAILABLE`

`UNAVAILABLE` means that AgtXIv could obtain neither the publisher PDF nor an arXiv source bundle. No canonical artifact or authoritative anchors are produced in this state.

## 5. Content Extraction

Content extraction is the process of reading the canonical artifact. The extraction method does not change which artifact is canonical.

For a publisher PDF, AgtXIv may use:

```text
PDF_TEXT
OCR
```

`PDF_TEXT` reads an existing text layer. `OCR` uses an available OCR skill when the PDF has no reliable text layer or when mathematical or layout content requires image-based recognition. OCR output is derived text; the publisher PDF remains canonical.

For an arXiv source bundle, AgtXIv uses:

```text
LATEX_SOURCE
```

The extractor identifies the root LaTeX file, follows its included source files, and preserves enough file and line information to return to the original text.

The MVP prioritizes recovery of usable scientific content. It does not prescribe one universal PDF parser or OCR implementation.

## 6. Replacement Policy

AgtXIv v0.1 keeps only the current canonical version in its active source package.

A canonical artifact is replaced when:

1. a publisher PDF becomes available for a paper currently represented by arXiv source; or
2. a newer arXiv source version becomes available while arXiv remains the highest available source.

The MVP does not retain the previous artifact as an active historical version. Replacement must trigger:

```text
replace canonical artifact
→ recompute the artifact hash
→ regenerate extracted content
→ regenerate anchors
→ invalidate and regenerate all derived claims and relations
```

Old anchors must never be reused after replacement because pages, files, line numbers, labels, and wording may have changed.

## 7. Source Package

Each resolved paper source is represented by two files:

```text
source/
├── manifest.json
└── anchors.jsonl
```

`manifest.json` records paper identity, query provenance, canonical resolution, the canonical artifact, and the extraction method. `anchors.jsonl` records individual source passages and their locations.

The original PDF or arXiv source bundle is stored separately under the project's existing reference-material directory. The manifest points to that artifact rather than duplicating it.

## 8. `manifest.json`

### 8.1 Resolved publisher PDF

```json
{
  "schema_version": "agtxiv.paper-source/0.1",
  "paper_id": "doi:10.xxxx/example",
  "document_type": "PAPER",
  "query": {
    "query_type": "PAPER",
    "identifier_type": "DOI",
    "identifier": "10.xxxx/example",
    "submitted_at": "2026-08-21T14:00:00Z",
    "deferred_question": null
  },
  "metadata": {
    "title": "Example Paper",
    "authors": ["First Author", "Second Author"],
    "doi": "10.xxxx/example",
    "arxiv_id": "1609.07488"
  },
  "canonical_resolution": {
    "status": "RESOLVED",
    "source_type": "PUBLISHER_PDF",
    "resolved_at": "2026-08-21T10:00:00Z"
  },
  "canonical_artifact": {
    "path": "Reference/example-paper/publisher.pdf",
    "media_type": "application/pdf",
    "source_url": "https://publisher.example/paper.pdf",
    "sha256": "48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d"
  },
  "extraction": {
    "method": "PDF_TEXT",
    "tool": "pdf-extraction-skill",
    "generated_at": "2026-08-21T10:05:00Z"
  }
}
```

If OCR is used, `extraction.method` is `OCR` and `extraction.tool` identifies the OCR skill.

### 8.2 Resolved arXiv source

```json
{
  "schema_version": "agtxiv.paper-source/0.1",
  "paper_id": "arxiv:1609.07488v3",
  "document_type": "PAPER",
  "query": {
    "query_type": "PAPER",
    "identifier_type": "ARXIV",
    "identifier": "1609.07488",
    "submitted_at": "2026-08-21T14:00:00Z",
    "deferred_question": null
  },
  "metadata": {
    "title": "Example Paper",
    "authors": ["First Author", "Second Author"],
    "doi": null,
    "arxiv_id": "1609.07488"
  },
  "canonical_resolution": {
    "status": "RESOLVED",
    "source_type": "ARXIV_SOURCE",
    "resolved_at": "2026-08-21T10:00:00Z"
  },
  "canonical_artifact": {
    "path": "Reference/example-paper/arxiv-source.tar",
    "media_type": "application/x-tar",
    "source_url": "https://arxiv.org/e-print/1609.07488v3",
    "arxiv_version": 3,
    "entrypoint": "main.tex",
    "sha256": "48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d"
  },
  "extraction": {
    "method": "LATEX_SOURCE",
    "tool": "agtxiv-latex-reader",
    "generated_at": "2026-08-21T10:05:00Z"
  }
}
```

### 8.3 Unavailable source

```json
{
  "schema_version": "agtxiv.paper-source/0.1",
  "paper_id": "doi:10.xxxx/example",
  "document_type": "PAPER",
  "query": {
    "query_type": "PAPER",
    "identifier_type": "DOI",
    "identifier": "10.xxxx/example",
    "submitted_at": "2026-08-21T14:00:00Z",
    "deferred_question": null
  },
  "canonical_resolution": {
    "status": "UNAVAILABLE",
    "resolved_at": "2026-08-21T10:00:00Z",
    "reason": "Publisher PDF and arXiv source could not be obtained."
  },
  "canonical_artifact": null,
  "extraction": null
}
```

## 9. `anchors.jsonl`

Each line of `anchors.jsonl` is one JSON object. An anchor connects an extracted passage to a location in the current canonical artifact.

### 9.1 PDF anchor

```json
{"anchor_id":"anchor:example-paper:001","paper_id":"doi:10.xxxx/example","artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","location":{"type":"PDF_PAGE","page":5},"text":"The central result of this paper is ...","text_sha256":"7eff4a6f84a6341409c8cbbf93c2013f96d443f2bc8cc5589246aa36216dd858"}
```

If the extraction skill reports page coordinates, the location may be more precise:

```json
{"anchor_id":"anchor:example-paper:001","paper_id":"doi:10.xxxx/example","artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","location":{"type":"PDF_REGION","page":5,"bounding_box":[72,214,510,328]},"text":"The central result of this paper is ...","text_sha256":"7eff4a6f84a6341409c8cbbf93c2013f96d443f2bc8cc5589246aa36216dd858"}
```

### 9.2 LaTeX anchor

```json
{"anchor_id":"anchor:example-paper:001","paper_id":"arxiv:1609.07488v3","artifact_sha256":"48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d","location":{"type":"LATEX_LINES","file":"main.tex","line_start":120,"line_end":128,"section":"Main Result","label":"thm:main"},"text":"The central result of this paper is ...","text_sha256":"7eff4a6f84a6341409c8cbbf93c2013f96d443f2bc8cc5589246aa36216dd858"}
```

The `artifact_sha256` field ties every anchor to the current canonical file. The `text_sha256` field allows the stored passage to be checked for accidental changes. These hashes establish content identity; they do not establish scientific correctness.

## 10. Minimum Validation Rules

A source package is valid only if:

1. `query.query_type` is `PAPER`;
2. `query.deferred_question` is either `null` or a verbatim question with status `DEFERRED` during acquisition;
3. the deferred question does not influence any paper-processing stage;
4. `document_type` is `PAPER`;
5. `canonical_resolution.status` is `RESOLVED` or `UNAVAILABLE`;
6. a resolved record has exactly one `canonical_artifact`;
7. `canonical_resolution.source_type` is `PUBLISHER_PDF` or `ARXIV_SOURCE`;
8. the canonical artifact has a path, source URL, media type, and SHA-256 hash;
9. publisher PDF extraction uses `PDF_TEXT` or `OCR`;
10. arXiv source extraction uses `LATEX_SOURCE` and records an entry point;
11. every anchor refers to the hash of the current canonical artifact;
12. no anchors are present for an unavailable source; and
13. replacement of the canonical artifact invalidates all previous anchors and derived content.

## 11. MVP Boundary

AgtXIv v0.1 deliberately does not:

- support thesis, book, dataset, or software queries;
- preserve an active archive of earlier canonical versions;
- compare publisher and arXiv text for discrepancies;
- assess scientific correctness during source acquisition;
- prescribe a single OCR or PDF extraction implementation;
- extract claims before canonical resolution succeeds;
- answer or use a deferred question before the configured pipeline completes; or
- treat OCR output as a canonical artifact.

The next pipeline stage begins only after a resolved source package and its anchors are available. Any deferred question remains stored and inactive until all configured AgtXIv stages have returned explicit results.
