# PDF page-region candidates

`pdf_candidates.py` consumes a retained visual-reading report and mathematical candidate rows. It freezes the original PDF, derived text and all ordered page images, records an actual `pdfinfo` page-inventory receipt, and emits a candidate assembly plus its pruned support graph. Claim identities depend on source content hashes and regions, not output directories.

A `PDF_PAGE_REGION` anchor binds document bytes, page number, retained image bytes and normalized top-left rectangle. It is not an exact quotation, OCR verification or mathematical acceptance. Page-image correspondence and visual reading remain attributed to the retained reading report; the adapter does not rerender the source. Contradiction contexts remain separate from query assertions. Local proof claims retain their scope blockers. External citation labels become unresolved frontier requests, never invented paper identities.

```
.venv/bin/python 'schema v0.3/host/pdf_candidates.py' \
  --reading /absolute/reading-provenance.json \
  --candidates /absolute/claim-candidates.json \
  --output /absolute/fresh-run
.venv/bin/python 'schema v0.3/host/audit_pdf_candidates.py' \
  --run /absolute/fresh-run --output /absolute/fresh-audit.json
```

The separate integrity audit checks input snapshots, asset hashes, retained page-count receipt, candidate roles and support graph reconstruction without accepting mathematical content. The Lovász 1972 four-page case is recorded in `runs/semantic-lovasz-pdf-regions-attempt02-20260919`; the preceding run is retained. Its 10 reading rows yield nine query candidates, one nonasserted proof context and one unresolved Berge 1961 request. Source alignment and earliest origins remain unestablished.

The proof worker now has an unexecuted multimodal adapter. A proof request may supply `paper_sources[paper_id] = {"pdf_run": <content reference to summary.json>}` instead of the TeX extraction/directory entry. The retained summary and assembly must identify that paper, and the node's statement, conditions, kind, reading ID and regions must match its assembly row. Scheduler annotations may differ. This binds attributed provenance, not bibliographic truth or mathematical acceptance.

The worker supplies all retained pages in order (at most 32 pages and 32 MiB of image bytes), retains image snapshots through the model transport, and labels derived text as non-authoritative. The proof audit reconstructs the context and checks the ordered original image references against the task; image evidence separately binds task and receipt to snapshot bytes. No model call, audit or Lean execution has yet exercised this PDF proof path. Historical UTF-8 runs retain their original evidence. The recursive controller reuses a retained PDF run only through an explicit `RetainedPDFSourceBinding` import (`research.py`; no recorded run has used it yet); it does not discover or extract PDF sources itself. PDF support joins (`pdf_support_join.py`) now keep the base assembly's `graph_format`. Remaining execution coverage is recorded only in `schema v0.1/PENDING_TESTS.md`.
