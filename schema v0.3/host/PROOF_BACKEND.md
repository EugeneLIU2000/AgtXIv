# Actual model and Lean proof worker

`proof_walk.py` consumes a previously pruned graph, frozen paper sources, an
audited common Lean environment, explicit candidate root-library bindings, and
optionally library root audits and human review records.
It calls `scheduler.bottom_up_walk` with `ModelProofBackend` callbacks. It does
not change support groups, erase blocked roots, accept source alignment, or
accept the paper's chain; its certificate is at most a conditional implication
(below).

The root bindings are reviewable host inputs. Strict mode blocks these
uncalibrated bindings. Explicit candidate exploration may fund attempts while
preserving the review markers on every descendant. Library search is lexical
(below); semantic retrieval and scientific acceptance are not supplied.

## Execution and evidence

1. `freeze_environment` checks the completed common-epoch layers and audits
   specifically named library declarations. The environment records the actual
   Lean executable, search order, standard library, all base `.olean*` and
   `.ir/.ir.sig` bytes, and the trusted runtime sources. Compiled runtime
   companions and library audit receipts are separate hashed artifacts.
2. The scheduler reserves each proof or premise attempt in SQLite. Each actual
   model call reserves a separate model quota slot before dispatch. Failures
   and timeouts retain their reservations and receipts.
3. The model receives complete frozen paper text, the source-bound node,
   audited library types, available predecessors, and previous failures. It
   returns reasoning steps, one Lean type term, one Lean value term, and
   unresolved alignment notes. It cannot supply host status fields.
4. `GeneratedProofDriver.lean` parses each generated field as one Lean term.
   The host selects declaration names and imports. A conservative lexical
   filter rejects placeholders and several effectful constructs; it is not
   presented as a complete security boundary.
5. On macOS, `sandbox-exec` permits writing only the attempt's compiled-object
   and temporary directories, denies network and child processes, and leaves
   inputs read-only. Lean has a memory, heartbeat, wall-time, and captured-output
   bound. An unavailable sandbox yields failure; it never silently falls back
   to unrestricted generated-code execution. An outer sandbox may need an
   authorized launcher to start this inner sandbox.
6. The host reads declaration kind, actual type, explicit and structure-packed
   premises, axioms, and proof-term dependencies from Lean. Standard permitted
   axioms are `propext`, `Classical.choice`, and `Quot.sound`. The original input
   fingerprint is checked again after execution.
7. Ordinary predecessor edges require the predecessor's declaration in the
   elaborated proof body. Explicit Prop fallback edges from the
   original protocol remain `NOT_COMPOSED`. The V2 driver records the actual
   proof-value binder index and compares its type with the required proposition
   using Lean `isDefEq`; names are never joined to statement binders. The new
   runtime compiles, but a real fallback-composition run has not yet executed.
   See the central pending list for the uncovered positive/negative paths.

A failure classification is a separate uncalibrated decision-model output.
The actual compilation result is saved before requesting that classification,
so lack of remaining quota cannot erase the compilation evidence. A Prop
fallback preserves its parent imports and is a condition, never a proof.

Every successful attempt remains a kernel-checked **candidate**. Nonvacuity is
unknown unless an actual witness has separately been supplied; this worker
does not manufacture one. The selected graph may remain blocked;
`bottom_up_walk`'s `result.chain_state` remains `CHAIN_INCOMPLETE`, and the
separate chain certificate may be `EMITTED` only as a conditional implication
(below).

## Library index and root audits

`library.py index --environment E --output O` runs `lean/LibraryIndex.lean` once
inside the frozen environment and writes the Lean-produced rows
(`compiled/library-index.jsonl`: name, kind, type, module) plus a small manifest
`library-index.json` pinning rows, program source, receipt and environment. The
prop-v2 proof environment gives 19,078 rows; Physlib, QuantumInfo and Quantumlib
contribute 0 rows there. `library.py roots --graph G --index O/library-index.json
--environment E --output root-audits.json` writes, for every non-placeholder
root, a `LIBRARY_SEARCHED` audit with the top-k candidates of
`LEXICAL_IDF_TOKEN_OVERLAP_V1` and `binding_accepted: false`. Placeholder roots
are skipped.

A request may reference that file as `root_audits`; it must name the request's
graph and environment, and `proof_walk` refuses it if it audits a root that the
request also binds in `candidate_root_bindings`. Every entry must match
`$defs.RootAudit` (`LIBRARY_SEARCHED` only); `LIBRARY_BOUND` arises only from
`candidate_root_bindings`, and an input graph that already carries a
`root_audit` is refused. Each audit adds
`unreviewed-root-search:<id>` (plus `CANDIDATE_ROOT_SEARCH_REVIEW_REQUIRED` in
strict mode). With it, such a root is no longer `ROOT_LIBRARY_AUDIT_REQUIRED`
and can be attempted in candidate exploration unless another hard blocker
remains. Candidates are lexical matches on TeX and often weak; a search is
never a binding or an alignment.

The model payload then carries `retrieved_library_candidates` for audited roots
and, when an earlier attempt's hash-checked Lean log reports unknown
identifiers, `library_search_for_unknown_identifiers` (those names looked up in
the same index). An index built for another
environment is rejected.

## Statement triviality probe

After a THEOREM candidate is kernel-checked, `triviality/Triviality.lean` runs
one probe per tactic in `TRIVIALITY_TACTICS` (`trivial`, `rfl`, `decide`, `simp`,
`norm_num`), each with its own 20,000-heartbeat budget, on the candidate's type.
`statement_trivially_provable` is `true` if any probe closes it, `false` if all
ran and failed, `null` otherwise. `true` or `null` keeps the node
`AWAITING_REVIEW` and out of available dependencies. `false` only means this
tactic set failed; it is not a strength check against the source. For results
that carry the probe or a `triviality/` directory, `audit_proof_walk.py`
rebuilds its source from its own frozen copy of `TRIVIALITY_TACTICS`, checks
source, receipt and log hashes, and recomputes the flag from the log's audit
rows.

## Human review and chain certificate

`review.py template --graph G [--ledger <run>/ledger.json] --output R` lists
every reviewable subject with `decision: null`: support groups before a walk;
after a walk also, from its ledger, `FAILURE_CLASSIFICATION` for failed proof
attempts that carry a `failure_kind` (node, attempt, result digest, the recorded
failure kind and reason, model- or host-assigned, and the Lean source and log
reference when Lean ran), `PREMISE_ALIGNMENT` for premise
attempts (plus source text and `lean_prop`) and `STATEMENT_ALIGNMENT` for
kernel-checked attempts (plus source text and Lean type, null when the result
has no `audit_record`). A
human fills `decision` (ACCEPT/REJECT), `reviewer`, `basis`, `reviewed_at`
(`$defs.HumanReview`, `schemas/human-review.schema.json`); the host never does.
Records that are malformed, name an unknown subject, or whose subject changed
since review (`subject_sha256`) are rejected; any REJECT withdraws ACCEPTs.
`proof_walk.py --reviews R` applies accepted support groups only.

Every walk writes `chain-certificate.json` (`certify.py`); `summary.chain_state`
is its state, while the walk's own `result.chain_state` stays `CHAIN_INCOMPLETE`.
`CHAIN_CERTIFICATE_EMITTED` means only that every query has a kernel-checked
Lean candidate whose triviality probe (theorems) ran and did not close it; an
unprobed theorem query (by the graph's node kind) is
`QUERY_STATEMENT_TRIVIALITY_UNPROBED` and blocks emission. It is stated as `<query> holds
CONDITIONAL ON {P1, ..., Pk}` with the premises read from Lean. It is a formal
implication conditional on those listed premises, not the paper's truth; open
reviews and `VACUITY_UNKNOWN` stay listed.
`human_accepted` becomes true only when every review blocker and every query
and explicit-premise alignment has an accepted review:
`certify.py --run <walk> --reviews R --output O` re-certifies a recorded walk
after verifying its pinned files, and only if `audit_proof_walk` passes on it
(which also checks the attestation state and hypotheses that the certificate
reads); the audit report is written beside `O` as `<O stem>.run-audit.json`. In strict mode this is not reachable inside
`proof_walk` (searched or bound roots keep a hard review blocker; a policy
decision is pending). No review records exist yet. An accepted `SUPPORT_GROUP`
review lifts that group's blocker inside `proof_walk` only; it does not change
the graph disposition, so research `accepted_support_edges` stays 0.

## Request and command

A request contains `paper_id`, `source_sha256`, hashed `graph` and `environment`
references, `paper_sources` mapping paper IDs to a frozen `extraction` reference
and source `directory`, and `candidate_root_bindings` mapping graph root IDs to
audited declaration names. Optional `selected_group_ids` selects one OR route;
the scheduler enforces the existing graph constraints. Optional `root_audits`
references a `library.py roots` output.

```
.venv/bin/python 'schema v0.3/host/proof_walk.py' \
  --request /absolute/path/to/request.json \
  --output /absolute/path/to/fresh-run \
  --max-model-calls 3 --max-proof-attempts 2 \
  --max-node-attempts 1 --max-call-seconds 180 \
  --candidate-exploration [--reviews /absolute/path/to/reviews.json]
```

The entry point always exits 2, including when `chain-certificate.json` is
`CHAIN_CERTIFICATE_EMITTED`, because no paper chain is accepted. It uses a new
immutable plan; crash recovery or continuation of a busy worker requires the existing explicit recovery protocol
and is not automatically inferred from elapsed time. All execution coverage
and remaining adversarial cases belong in `schema v0.1/PENDING_TESTS.md`.
