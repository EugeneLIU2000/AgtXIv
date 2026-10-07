# schema v0.4 Neo4j projection

**Status (2026-09-26):** written and unit-tested on synthetic rows with a fake client, and executed once on a real
server: in the quant-ph test run (`../runs/quant-ph-sample-20260926/`) Neo4j Community 2026.09.0 applied
`schema.cypher`, took the full load, returned zero rows for every audit in `audits.cypher` and ran every template in
`browse.cypher` (`browse-check.json`). Not yet exercised: re-load idempotency, fault injection, Neo4j 5.26 LTS,
the CSV import and the compose file.

Neo4j holds a **projection**: a pure function of one `DeltaSetManifest` plus one review set (spec §9.1,
I-12). It is never the authority and never writes back. If it is lost or doubtful, rebuild it.

## Files

| File | What it is |
|---|---|
| `schema.cypher` | Uniqueness constraints on `:Entity(id)`, on `id` for each projected label and relationship type, and the eight §9.3 range indexes. Every statement uses `IF NOT EXISTS`. |
| `audits.cypher` | One read-only query per auditable invariant (G1–G5, G7–G15). Each returns rows `(invariant, id)`; zero rows means the invariant holds. |
| `browse.cypher` | Browsing templates. Each takes `$id`, names relationship types and directions, goes at most 8 junctions deep, and has a `LIMIT`. |
| `compose.example.yaml` | A local Neo4j Community container, bound to localhost. |
| `../host/projection.py` | Builds the rows, holds the fixed templates, runs the load protocol, and contains the Query API client and the CSV export. |

The text is meant for Neo4j 5.26 LTS and 2026.x Community. It uses no `CYPHER` version prefix, no
APOC, and no `CALL {} IN TRANSACTIONS`. Both versions should accept this text, but neither has run it.

## What is projected

- **Node labels.** Every node carries `:Entity`, and claims and placeholders also carry `:Logical`.
  A placeholder also carries `:ExternalRequest` or `:UnresolvedOccurrence`. A `:Corpus` node is derived
  from `DeltaSetManifest.corpus_id` when some `INCLUDES` edge exists; its `asserted_by` is the union of
  the deltas asserting those edges.
- **Not projected in v0.4.** `Review`, `AnalysisRun` and `Nomination` nodes and the `REVIEWS`, `IN_RUN`
  and `NOMINATES` relationships. Reviews act only through the derived `disposition`; nominations stay
  immutable analysis artifacts. The top-K overlay is deferred.
- **Properties.** Every property is a scalar or a non-empty list of scalars. A nested map is flattened
  into `a_b` keys (for example `locator_start_byte`). A list of maps is stored as a JSON string under
  `a_json`. `None` and empty lists are left out, so a direct load and a CSV import give the same graph.
  Every node and relationship also carries `asserted_by` (delta ids) and `methods`, both from the view;
  a derived relationship takes them from its junction. A delta's edge `props` may not set `id`,
  `content_sha256`, `asserted_by`, `methods` or `disposition`; `project()` refuses such a row.
- **Derived relationships.** `PREMISE_OF {position, role, use_site, flags}` and `CONCLUDES` are built
  from `Junction.legs` by `ids.logical_edges`; deltas never assert them. The ids are:
  - `rel:` + digest of `{type: PREMISE_OF, end_id: <junction>, position}` for `PREMISE_OF`
  - `rel:` + digest of `{type: CONCLUDES, start_id, end_id}` for `CONCLUDES`
- **Legs on the junction node.** A junction node keeps `leg_count` and does not keep its legs.
- **Dispositions.** `disposition` comes only from `reviews.derive_dispositions` and is `UNREVIEWED` or
  `SOURCE_FROZEN_HUMAN_SIGNED`. A LEG review's subject id is its `PREMISE_OF` relationship id, so it
  applies to that relationship.
- **Verbatim text (I-13).** A `VERBATIM` `display_text` is kept only when the stating paper version
  has `redistribution = OPEN`.

## Load protocol (`projection.load`, spec §9.4)

`project()` first requires that the view was merged from exactly the manifest's deltas. The
projection names its delta set by `delta_set_digest` = `sha256:` + the hex of `manifest_id` (the digest
of the manifest body without `manifest_id` and `created_at`), so remaking a manifest keeps the projection
id. `review_set_digest` is `reviews.review_set_digest`: the digest of the filled review rows in canonical
order.

1. Apply `schema.cypher`.
2. Refuse to go on if the database holds a `ProjectionManifest` with a different id; rebuild from
   empty instead. v0.4 always rebuilds from empty; incremental loading is deferred. A client error in
   steps 1–2 raises `LoadError` without writing a manifest.
3. Set `ProjectionManifest.state = BUILDING`.
4. Preflight every node and relationship id against its `content_sha256`. Any mismatch aborts before
   anything is written.
5. Write node batches, then relationship batches. Each batch has at most 5,000 rows, is one
   auto-commit request, and uses `MERGE … ON CREATE SET`. If the returned count differs from the batch
   size, the load aborts.
6. Run every audit, each with only the parameters it names. Any row aborts.
7. Set the state to `READY`, with the row count per label and type and the count per audit.

When anything fails from step 3 on, a client or server error included, the manifest is set to `FAILED`
(if the server still answers) and `LoadError` is raised, chained to the original error. Readers require `READY`;
every browse template checks for it first. Every request sends
`txMetadata {id, delta_set_digest, review_set_digest}`.

Before loading, run `invariants.check` on the view. The audits only re-check, after the load, what the
host has already checked.

## Using it

The quant-ph test run used a portable server instead of the container: Neo4j Community 2026.09.0 and a Temurin 21 JRE
unpacked under the git-ignored `local-archive/tools/`, listening on 127.0.0.1 only with login disabled, loaded by
`QueryClient` without an `Authorization` header (`../runs/quant-ph-sample-20260926/INDEX.md` has the commands). With
login enabled, as below, the password stays in the environment and is never committed.

**One claim in the chain-build encoding.** Neo4j Browser styles nodes per label (colour, size, caption) but cannot
draw shapes, junction ⊕ symbols or a paper boundary. `../viewer/claim-view.html` reads one claim's backward closure
through the Query API, with the same READY check and junction-only walk as `browse.cypher`, and draws it as the
chain-build frontend does: shape = kind, colour = source paper, ⊕ = junction, a dashed box = the claim's paper, so a
curve that crosses the box is a cross-paper leg. Serve the repository over http (the preview server on port 8765
does) and open `schema%20v0.4/viewer/claim-view.html#<claim id>`. Untested (PENDING_TESTS V04-37).

```sh
export NEO4J_PASSWORD=...        # never committed
docker compose -f "schema v0.4/neo4j/compose.example.yaml" up -d
```

```python
from projection import QueryClient, load, project, projection_manifest
rows = project(view, delta_set_manifest, dispositions)       # view = delta.merge(...)
manifest = projection_manifest(delta_set_manifest, review_set_digest)
load(QueryClient("http://127.0.0.1:7474", "neo4j", "neo4j", password), rows, manifest)
```

**Rebuild from empty.** Run `docker compose … down -v`, which deletes the data volume, then load again.

**Faster first load.** `projection.export_csv(rows, dir)` writes the input for
`neo4j-admin database import full` and returns the command line. This path is outside the contract.
After the import, run `load()`, which preflights, finds every `MERGE` already satisfied, runs the
audits and sets `READY`.

## Limits

- **G6 is host-only.** It checks that an id equals the digest of its identity fields. So is the digest
  half of G15. Cypher has no sha256 function.
- **G7 uses the widest work class.** The audit admits every `SAME_WORK` basis. A row it returns is
  therefore a violation under every loading policy. The exact check for one policy runs in the host.
- **G5 is driven by the contracts.** `projection.ENUMS` lists every enumerated field of each label and
  relationship type, read from the contract schemas and keyed as the flattened properties are. Values
  inside a list of maps (stored as JSON) are not re-checked.
- **G9 needs the manifest's deltas as a parameter.** `ProjectionManifest` does not store the delta
  list.
- **G11 receives the whole disposition map** in one request. At corpus scale this is large; a batched
  form is an open item.
- **G13 is per reading.** At most one `statement` junction per (conclusion, reading method, method
  version); analysis joins the admitted readings' statement junctions by the establishment reading
  policy.
- **G14 follows the host's rule.** A junction names no reading, so every reading of its conclusion
  with the same method and method version counts as its basis. If any of them is superseded, the
  junction is flagged. A correction therefore needs a new method or method version.
- **Graph Data Science is not the reference.** It can be used for exploration only. Its topological
  sort drops nodes on or below a cycle.
