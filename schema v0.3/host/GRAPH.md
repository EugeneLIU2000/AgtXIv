# Candidate support-graph engine

`graph.py` is on the **research schema** v0.3 ladder. Its public API is
`prune_graph(nodes, support_groups, query_ids, *, graph_format=None) -> dict`. It
derives graph selection and scheduling facts. It does not accept scientific
dependencies on its own. `graph_format` selects the output layout (see
[Output formats](#output-formats)).

The caller is a host adapter, not a model response. Before calling, reject model
state with `core.reject_model_state` and derive the host evidence. Graph input
rejects the fields `state`, `derived_state`, `included_by`,
`weakest_disposition_on_path`, `formalization_state`, `coverage` and `selected`.
The supplied `disposition`, `blocked_by`, discharge flags and origin references
must already be host-owned. Neither an input disposition nor a graph path is an
attestation that a theorem was proved.

## Inputs

Nodes require `id` and `kind`. Optional fields used by the engine are:

- `disposition`: defaults to `CANDIDATE`; admissible values and their conservative
  propagation order are published as `DISPOSITIONS` and in every result.
- `blocked_by`: a list of blocker identifiers; defaults to `[]`. A blocked source
  remains in the selected graph. `BLOCKED`, `SOURCE_UNREACHABLE` and
  `SOURCE_READ_DEFECTIVE` also create a blocker even if the identifier list is empty.
- `bridging_claims`: host-recorded claim identifiers required for statement
  alignment. Each bridge is inserted as a mandatory AND member into every target
  alternative, or into a generated bridge group when none exists. Missing bridge
  identifiers fail. Their dispositions propagate into the target's own effective
  disposition; a bridge cannot vanish through selection of an alternative route.
- `cost_microusd`: nonnegative integer, or missing/null for an unknown cost.
  `cost_error_microusd` is a nonnegative integer absolute error bound, default 0.
- `statement_discharged` and `proof_discharged`: boolean evidence supplied by the
  host. A definition may not set `proof_discharged=true`.
- `upstream_search`, `origin_evidence`, `terminal_kind`, `library_binding`: root
  audit metadata. `ORIGIN` requires an `origin_evidence` object containing
  `search_status: SEARCH_EXHAUSTED` and a nonempty `references` list. This checks
  presence and shape; reference validity remains the caller's evidence audit.

Support groups require `id`, `target`, a nonempty list of upstream `members`, and
`relation`. Members of one group are joint premises (AND); groups for one target
are alternatives (OR). Relation values are:

- `DEFINITION_DEPENDENCY`
- `SCIENTIFIC_CLAIM_DEPENDENCY`
- `SCOPE_DEPENDENCY`
- `PROOF_DEPENDENCY`
- `BRIDGING_DEPENDENCY`

Mentions such as `CITES`, `SIMILAR` and `UNKNOWN` are rejected; keep them in a
separate table. Group disposition defaults to `CANDIDATE`. Group cost and error
default to 0 because they represent additional cost beyond the member nodes.
Duplicate identifiers, duplicate members, dangling references and unknown enum
values fail at the boundary.

## Selection and costs

The engine first runs iterative Tarjan SCC condensation over all support
memberships, then finds query ancestors. It never reads legacy `layer` fields.
An unresolved SCC is an atomic `ROUTE_UNDETERMINED` component. The union of its
external prerequisites is retained conservatively; it is not reinterpreted as
alternative ways to prove the cycle. The component and every dependent are kept
out of `formalization_order`. Original member nodes and edges remain inspectable.

When every relevant node is priced, a deterministic search enumerates globally
consistent support-group choices. Every selected node and group is charged only
once. Consequently two branches sharing an expensive prerequisite share its cost;
independently choosing each branch's cheapest local route is not the algorithm.
Nonnegative partial lower costs give a safe branch-and-bound cutoff.

Each complete route has nominal, lower and upper costs. The result keeps every
route whose lower cost is no greater than the minimum upper cost of any route.
These are all routes that could tie for optimum under the supplied error bounds.
The selection is their union. Exactness concerns this supplied cost model and
candidate graph, not scientific support or measured real-world cost.

Search stops after 100,000 states or 2,048 stored tied routes. On a bound, or when
any relevant node cost is unknown, **all ancestors and their groups are retained**.
The result reports `BOUNDED` or `UNPRICED`, retains any observed route witnesses,
and explicitly declines an optimality claim. A bound never silently selects an
arbitrary route or discards unexplored ties. Output route summaries include the
bounds and the search status. Results containing SCCs explicitly say so per route.

## Ordering, disposition and roots

`condensation_order` is support-first and includes unresolved SCC identifiers.
`topological_order` contains its acyclic original node IDs. It is descriptive;
execution uses `formalization_order`, which also removes every blocked or
cycle-dependent node. `conditional_nodes` retains all excluded nodes and their
propagated blocker IDs. Blocking gates ordering, never selection.

When tied routes are retained, blocking is conservatively propagated over their
union. A blocked alternative can therefore postpone a node even if an unblocked
alternative exists; this result is not a route-specific proof scheduler. A caller
may inspect the individually recorded routes before a later evidence-backed
choice. No model output may suppress the blocked alternative.

Each node carries a canonical shortest support path to every reachable query in
`included_by`. `weakest_disposition_on_path` covers the node, selected edges and
downstream nodes across all retained paths, rather than just the displayed
shortest witness. An orphan is an explicit issue. Roots are actual input nodes
with no support groups, not nodes whose prerequisite was pruned away. They remain
`FRONTIER` unless exhausted-search evidence is present. Root status never implies
that the earliest historical source has been reached.

`effective_disposition` first combines a node's own disposition, any known
statement-alignment classification, and its mandatory bridges. This computation
precedes propagation along paths. An unreviewed domain widening thus cannot gain
a stronger effective disposition merely because its Lean rendering compiles.

## Diagnostics and coverage

For each selected membership edge the engine reports two different questions:

1. **Omission sensitivity:** remove that membership from the selected graph and
   recompute structural ancestors. Report removed nodes and resulting coverage.
   This deliberately models a missing anchor. The result is explicitly marked
   `omission_is_valid_proof_route: false`; deleting one AND premise does not make
   the reduced set a legitimate proof route.
2. **Support withdrawal:** invalidate the entire AND group containing the removed
   premise, and compute which queries still have a candidate support route among
   all input alternatives. A target that loses every group does not become a new
   justified root. Roots still represent undischargeable premises and cycles do
   not bootstrap their own support.

Counts carry scope data and a digest of their node set. Theorem proof discharge
and definition statement discharge remain separate coverage rows. They are never
summed into a success percentage. The blocker diagnostic distinguishes all
blocked nodes, including sources, from nodes inheriting a blocker upstream.

## Output formats

`graph_format=None` is the legacy layout, byte-identical to earlier runs: every
nested scope record repeats the full `query_ids` list, and every edge's support
withdrawal lists all unsupported queries. `COMPACT_V1` (`GRAPH_FORMATS`) carries
the same information without the repetition:

- `query_ids` appears once at top level, with `query_set_sha256`; nested scopes
  name the query set only by that digest.
- `support_withdrawal_baseline` stores, once, the queries already unsupported
  with no edge withdrawn. Each edge's `support_withdrawal` then holds
  `unsupported_query_count` and `newly_unsupported_query_ids`. The legacy list is
  baseline ∪ newly unsupported, so nothing is lost.

The format travels with the assembly (`assembly["graph_format"]`, set by
`CLAIM_REFERENCE_V1`; see [SEMANTIC.md](SEMANTIC.md)) through
`select_candidate_graph`, recursive joins and PDF support joins. Assemblies
without the field produce the legacy graph. Measured on the recorded 4-paper
graph (`runs/research-doi-available-20260922/graphs/00033-7eb94ecd`): 47,063,313 B
legacy against 7,009,523 B compact, and all 138 historical graph/assembly pairs
rebuild byte-identically in legacy mode. Per-node `included_by` witnesses are
not yet compacted.

The actual 2607 case execution artifacts live under
`schema v0.3/runs/graph-development/`. They are case evidence, not a synthetic
algorithm test suite. Additional pending scenarios belong only in the shared
`schema v0.1/PENDING_TESTS.md` list.
