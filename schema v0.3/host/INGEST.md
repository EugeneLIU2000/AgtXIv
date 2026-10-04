The ingestion adapter belongs to the **schema research-contract ladder**, version 0.3.

`extract_paper(repo: Path, paper_id: str, output_dir: Path) -> dict` reads one registered,
versioned paper, calls the existing `tools/extract_provisional_claims.py` segmenter, and
writes `extraction.json` with immutable content-addressed source blobs. It never executes
TeX. Reusing an output directory with different report bytes is rejected; use a fresh run
directory when source or implementation changes.

`discover_sources(repo)` reads the current PaperAgentRegistry manifests and source
metadata on the shipped claim DAG. Additional acquired sources can be registered in
`schema v0.3/sources.json` as follows:

```json
{"papers": [{"paper_id": "arxiv:2607.26154v1", "artifact": "Stabilizerness/arXiv-2607.26154v1/draft.tex", "artifact_hash": "sha256:4a84425a4d56efe5b5bee4814a09c99996ab7a6bd279574d567979c248f81c1d"}]}
```

Source registration must carry a version. Unknown sources return a typed
`SOURCE_UNREACHABLE` frontier result. A source without a registered prior hash is frozen
at ingestion but is not independently authenticated as the published version.

The report contains:

- `paper` / `papers`: pinned source identity and discovery evidence.
- `claims`: automatic occurrences with the original extractor's IDs, exact source text,
  half-open byte offsets, source/span SHA-256, and syntactically adjacent proof bodies.
- `curated_claims` and `bridge_candidates`: current MathClaimIR records and source-span
  overlap candidates. Overlap does not establish semantic identity or promotion.
- `anchors`: literal reference/citation occurrences, automatic and curated owner
  candidates, candidate targets, and typed exclusions from the support graph. A pending
  exclusion means the semantic decision is missing; it is not a reviewed non-support verdict.
- `bibliography`: inline/compiled `.bbl` entries and literal `.bib` resources, exact identifiers and local paper
  candidates. Local title matching retains its source evidence and remains a candidate.
- `macro_table`: source-backed literal macro declarations without executing expansion.
- `coverage`: separate scoped observations for theorem environments, automatic
  occurrences, curated records, reference anchors, and bibliography entries. None is a
  percentage of all mathematical claims.
- `issues`: missing inputs, unreadable encodings, unbound curated anchors, unresolved
  labels, unowned proof bodies, and other explicit gaps.

`resolve_external_identifiers(extraction, output_dir, enable_network=False,
max_requests=50)` provides bounded Crossref DOI or title/journal/year fallback. Network
access is opt-in. Raw responses and reports are retained; cached responses can be reused.
Bibliographic search candidates require the decision layer's identity/subject assessment.
ADS remains an explicit authenticated-adapter requirement. A timeout, budget stop, or empty
result never becomes `ORIGIN` or an exhausted earliest-source search.

The adapter preserves the existing segmenter's fixed environment vocabulary and prose
heuristics. Literal includes are followed, but macro execution, conditional participation,
implicit prose references, BibTeX macro/inheritance expansion, PDF extraction, and semantic completeness
remain unresolved. A full source claim/dependency pass must account for these gaps rather
than reading the deterministic occurrence count as a complete claim list.

No terminal state or proof attestation is produced by this module. Test execution and
pending scenarios are recorded centrally in `schema v0.1/PENDING_TESTS.md` by the host task.

Literal `\bibliography{...}`, `\addbibresource{...}`, and `\putbib[...]` resource names
are read in their bibliography unit. `host/bibtex.py` retains original byte spans,
nested literal values and literal concatenation; it does not execute directives or
expand macros, crossref, or xdata. Duplicate keys remain separate entries; duplicate
fields become null, and unresolved values retain diagnostics. Compiled entries take
precedence for the same unit/key, with an explicit unassessed-agreement issue and the
BibTeX bytes retained. Nothing in this precedence establishes scientific identity.

Downloaded source descriptors carry `source_root` and `source_archive`. Includes and
bibliography resources must resolve inside that extracted source tree, including after
symlink resolution. Older acquired descriptors with an archive infer its adjacent
`source/` directory; trusted legacy repository sources retain the repository boundary.
File size, total bytes and file count remain bounded. No TeX or bibliography program runs.

`audit_ingest.py --extraction ... --output ...` checks one extraction's frozen blobs,
all recorded byte spans, row texts and citation-target bookkeeping. A PASS is a byte
integrity result, not a claim of parsing completeness, source support or mathematical
acceptance. The actual Xu dependency run is in `runs/source-xu2511-bibtex-extraction-20260919`;
parser adversarial cases and path-escape scenarios remain pending in the central list.
