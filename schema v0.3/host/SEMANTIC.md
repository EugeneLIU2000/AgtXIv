# New semantic candidates and recursive source matching

These entry points build graphs from actual new extraction responses. They do not read the historical DAG. They are candidate evidence stages, not a complete autonomous proof runner.

## Extract and bind

`model.extract_candidates` reads frozen source blobs and checks byte spans before calling the model. Complete TeX and bibliography text is supplied once; redundant host metadata is omitted. `focus_occurrence_ids` optionally restricts output scope while retaining source context. The output schema allows exact `source_locators` for claims missed by the heuristic extractor. The model gives a path and unique verbatim quotation; the host computes the offset and hash.

The current target-paper response also has a collaboration-agent provenance record. It is not represented as a successful CLI call, and unavailable provider identity, tokens and price remain unknown.

Run the graph assembler with a new directory:

```sh
.venv/bin/python 'schema v0.3/host/candidates.py' \
  --extraction /absolute/path/to/extraction.json \
  --candidate /absolute/path/to/response.json \
  --source-directory /absolute/path/to/frozen-paper-directory \
  --output /absolute/path/to/new-run
```

The response may be a plain extraction object or a model-result envelope containing `candidate`. The assembler verifies actual response bytes, schema, source IDs, citation keys and new quotations. Unique occurrence-to-claim mappings become proposed internal support. Missing or ambiguous mappings remain requests. Bibliography entries become `external_claim_request` boundaries, never invented upstream mathematical statements. Untyped free-text uncertainties become issues and blockers; they do not become mathematical AND premises.

All claims stay unreviewed. All graph roots stay `FRONTIER`. The inventory metric describes supplied heuristic occurrences, not all mathematics in the paper.

## Claim references (`CLAIM_REFERENCE_V1`)

The model-facing schema now requires two fields per claim:

- `internal_support_claim_indexes`: zero-based positions of other claims in the same response that this claim's proof uses (schema `minimum: 0`; the host also rejects self-reference, out-of-range and non-integer values as `MODEL_CLAIM_INDEX_INVALID`).
- `external_mention_citation_keys`: bibliography keys that are only mentioned (attribution, context, comparison). `external_citation_keys` keeps its meaning of cited results that are used; a key in both lists is `MODEL_CITATION_ROLE_CONFLICT`.

Stored responses without these fields still validate through `CLAIM_RESPONSE_COMPAT_SCHEMA` and assemble exactly as before (legacy policy). The policy switches on when passed explicitly or when any claim carries a new field. Under V1:

- Claim indexes resolve directly to claim nodes. When batches are combined, the host rewrites batch-local indexes to combined positions.
- A reference to the claim's own occurrence, with no sibling claim there, is dropped (`SELF_OCCURRENCE_REFERENCE`).
- A reference to another occurrence holding several claims makes them joint AND members (`MULTI_CLAIM_OCCURRENCE_EXPANDED`). This is a conservative over-approximation, not a finding of which claim the proof uses.
- Expansion never introduces a support cycle. A pre-pass runs SCC detection on the fully expanded claim graph; each expanded membership inside the target's nontrivial SCC (and not already a direct reference) reverts to the typed placeholder with reason `SHARED_OCCURRENCE_EXPANSION_CYCLIC`, keeping the other members. Cycles made only of the model's direct references remain.
- The own occurrence shared with siblings, and not-yet-extracted occurrences, keep the placeholder and its blocker.
- Mention keys go only to `assembly["mentions"]` (`relation: MENTION_NOT_SUPPORT`); they never become members or requests. Recursive joins do not yet merge these tables across papers.
- A V1 assembly also sets `graph_format: COMPACT_V1` ([GRAPH.md](GRAPH.md)).

On `thm:solvable` of the target paper (retained response, no model call), the cycle revert reduced SCC sizes from [25, 4, 2] to [4, 2, 2]. No extraction with the new fields has been run yet; none of this is a review, alignment or proof.

## Classify references and audit artifacts

`audit_candidates.py` can check the generated artifacts and a separate `anchor-classifications.json` file. It checks schema, query IDs, exact frozen sources, quotation positions and deterministic reconstruction. Candidate reference roles are `SUPPORT`, `MENTION` or `UNCERTAIN`. A location PASS leaves all three roles awaiting semantic review: it accepts no support edge and creates no final exclusion.

## Match a new upstream paper

First ingest and extract the upstream paper using the same source-binding path. Then provide a `matches` array. Each match has a `target_request_id`, `upstream_occurrence_ids` (or explicit host-generated `upstream_claim_ids`), a relation (`CANDIDATE_SUPPORT`, `MISMATCH` or `UNCERTAIN`) and `source_quotes` containing exact `{path, exact_text}` evidence. Keep extra conditions and proof issues separate.

Several distinct upstream claims require `combination: JOINT_SUPPORT`. Several candidate support rows for the same request require explicit `route_semantics: EXPLICIT_CANDIDATE_ALTERNATIVE`; otherwise no alternative sufficiency is inferred. Citation-version mismatches and conflicting bibliography identities remain unresolved.

`recursive_graph.py` checks quotes against the mapped source occurrences, adds candidate support into the existing external-request boundary, preserves that boundary's blockers, and re-prunes to the original query IDs. It retains prior join history and evidence. Merely retrieving and matching a source does not discharge the boundary or prove the downstream theorem.

```sh
.venv/bin/python 'schema v0.3/host/recursive_graph.py' \
  --base /absolute/path/to/target/assembly.json \
  --upstream /absolute/path/to/upstream/assembly.json \
  --matches /absolute/path/to/candidate-matches.json \
  --upstream-extraction /absolute/path/to/upstream/extraction.json \
  --source-directory /absolute/path/to/upstream/frozen-sources \
  --output /absolute/path/to/new-recursive-run
```

This command records one explicit recursion step. The controller described below supplies repeated source dispatch and matching. Bounded bottom-up proof callbacks still require a complete proof worker.

All pending scenarios are maintained in `schema v0.1/PENDING_TESTS.md`; no separate testing checklist is defined here.

## Recursive controller

`research.py` now connects source extraction, real `paper.extract` / `dependency.match` calls, candidate assembly, versioned-paper admission and repeated query pruning under one frozen `PlanLedger`. The initial query paper consumes one paper slot. The frozen query selector is bound once to actual extracted IDs by a host ledger event; its source assembly and query scope are checked on resumption. Without `--query-label`, the legacy `ALL_EXTRACTED_MATH_CLAIMS` selector makes every extracted claim a query. `--query-label LABEL` (repeatable, new plans only) freezes `{kind: SOURCE_LABELS, paper_id, labels}`: each label selects the claims of its recorded occurrence, falling back to claims whose source span contains the label's byte position. A label absent from the source is refused before any model call; a label that binds no claim fails with `QUERY_LABEL_UNMATCHED` and publishes no graph. `thm:solvable` binds exactly one claim (`claim:candidate:6f4ac803e231732edaa22544`). New plans also freeze `claim_reference_policy: CLAIM_REFERENCE_V1` and `proof_backend: SEPARATE_STAGE_PROOF_WALK`. `query_ids: []` in this controller's plan means the selector was frozen before extraction, not that it has an empty query.

```sh
.venv/bin/python 'schema v0.3/host/research.py' \
  --paper 'arxiv:2607.26154v1' --query-label thm:solvable \
  --output 'schema v0.3/runs/choose-a-new-run' \
  --max-papers 5 --max-model-calls 12 --candidate-exploration
```

`--imports` can reference prior candidate responses with their frozen extraction files and prior source matches. Such reuse has explicit provenance and consumes no new model-call slot; historical cost stays outside this plan. Missing evidence calls the real CLI within the shared quota. `--network-sources` enables bounded source acquisition only for already pinned identities. Unversioned input uses a unique registered local version if available; it does not assert that version is latest. DOI-only or unresolved-version boundaries remain visible.

`--resume` uses the existing plan and never resets its budgets. A nonblocking OS lock prevents two controllers owning one run. Unexplained outstanding reservations or a BUSY checkpoint stop resumption until host recovery has established the former worker's status; automatic crash recovery is not implemented. Runtime changes require a new plan. These concurrency and interruption paths have been statically reviewed, not fault-injection tested.

The actual three-paper run is `runs/research-three-paper-20260919`: three extracted papers, two joins, 72 queries, 132 selected nodes and 84 support groups. It reused saved candidate evidence, made zero new model calls and stopped at its paper budget. `research-live-match-20260919` then exercised one uncached boundary through a real 46-second model call under the same controller; normal resumption retained three admitted papers and one total call without repetition. `audit_research.py` reconstructed the source-bound candidates, each join and graph, the query binding, and SQLite projections. This normal restart was executed; concurrency/crash fault paths were not. The mathematical result is still `CHAIN_INCOMPLETE`. The controller issues no certificate: Lean work is the separate `proof_walk.py` stage ([PROOF_BACKEND.md](PROOF_BACKEND.md)).

Summaries now compute `accepted_support_edges` (only `SOURCE_FROZEN_HUMAN_SIGNED` groups count; 0 in every run so far) and `frontier_terminal_kinds`, a scheduling label from bibliography fields, not an identity or support judgement. A failed paper is classified `SOURCE_UNREACHABLE`, `SOURCE_READ_DEFECTIVE` or `HOST_PROCESSING_FAILED`; the classification is kept in the issue evidence and the `FrontierRecorded` event even when the frontier row shows `NO_PROGRESS_LIMIT`.
# Version metadata extension

With `--network-sources`, an unversioned query without a unique local version can
be pinned from the official arXiv Atom API. Selected external requests with explicit
unversioned arXiv IDs use the same adapter after resolved source work is exhausted.
`--max-identity-requests` (default 8, range 0–64) freezes the request budget; a query
bootstrap call counts too. Requests are reserved as ledger events before I/O, their
raw Atom bytes and result receipts are retained, and failures consume a slot.
No version is inferred from a date or a bare identifier. API failure remains FRONTIER.
The chosen current version does not establish alignment with the version actually
used by an older citing paper. DOI-only and conflicting identities remain unresolved.

`arxiv_metadata.py` serializes its API calls and spaces their starts by three seconds,
following the [official API guidance](https://info.arxiv.org/help/api/user-manual.html).
The actual Xu dependency call in `runs/source-xu2511-api-version-20260919` returned
an explicit `2511.13531v1`. Controller-side network dispatch, metadata crash windows,
malformed XML, mismatching versions, and competing processes remain unexecuted.
The refreshed four-paper run `research-bibtex-four-paper-20260919` exercises the
new ingestion/metadata bookkeeping with zero metadata/model calls; its PASS does
not cover those unexecuted network and failure paths.
