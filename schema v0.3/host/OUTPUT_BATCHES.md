# Bounded output scopes for long papers

`research.py` now defaults to 8,192-byte output scopes for newly generated
paper candidates. Every call still receives the complete frozen source context,
including proofs, other sections, bibliography files and recorded source issues.
This avoids requesting a long paper's complete output in one model response.

`--extract-focus-bytes 0` selects the earlier single-output operation. Positive
values must be 1,024–131,072. `--max-extract-batches` bounds per-paper batches
(default 128); the existing global model-call quota remains authoritative.
Previously saved candidate imports retain their own evidence and scopes. The
2026-09-20 revision also accepts `extraction_batches` in `--imports`: success rows
are retained as `CANDIDATE_REUSED`, only missing/failed scopes are eligible for new
calls, and the per-paper limit counts new dispatch attempts. The source identity
and focus ranges must be unchanged. See [model routing and reuse](MODEL_ROUTING.md).

The planner covers all frozen text files except `.bib` and `.bbl`, which remain
context-only. It prefers newline boundaries, falling back to a UTF-8 codepoint
boundary for very long lines. Scope boundaries never truncate the supplied
context. A claim's statement must have an occurrence or unique quotation whose
first byte is in its assigned scope. This is a location constraint; determining
whether the quotation actually states that claim still requires review.

Each returned batch retains its prompt, source scope, response, model receipt,
usage (when exposed), candidate-location result and a dispatch checkpoint before
the next call. Failed outputs, undispatched ranges and budget stops are retained.
Only successful candidates enter the retained-batch combiner. It collapses only
identical complete candidate rows; conflicting rows with the same claim identity
are omitted pending reconciliation. It performs no semantic deduplication.

`dispatch.json` reports supplied output ranges separately from reading coverage.
A successful response does not establish that every byte was read or every claim
found. The combiner consequently reports zero verified/reported read bytes for
these automatic dispatch batches. Partial output is explicitly described in the
combined response, paper scope and research issues. The root query binds only the
actual retained candidates; it is never a claim of semantic exhaustiveness.

`audit_research.py` additionally reconciles batch ranges with frozen source bytes,
successful responses with their receipts and ledger call IDs, combined inputs,
and all omitted scopes. This is an artifact audit, not mathematical acceptance.

Crash recovery of a BUSY worker remains explicit. This dispatcher does not adopt
an interrupted process or refund its quota automatically. PDF page-region reading
is a separate, still-unconnected source adapter; sending TeX is not PDF rendering.

Actual execution and all pending boundary scenarios are tracked only in
`schema v0.1/PENDING_TESTS.md` (V03-54 and later scoped results).
