# Dependency Agent - research/0.2.0

## Sole responsibility

Find or compare historical dependencies for one saved MathClaim and output **search requests and dependency candidates**. Do not approve mathematical reuse or produce a proven DAG.

See [CONTRACT](../CONTRACT.md) for shared rules and [items.schema.json](../schemas/items.schema.json) for fields. operation is `dependency.search`; target_ids contains exactly one entry resolving to a supplied MathClaim.

## Work performed in this call

1. Read the target, conditions, citation leads, and existing retrieval material explicitly supplied as inputs. Report missing sources. Bibliographic scanning is input preparation, not a substitute for this model call.
2. If material is insufficient, return a `search_request` with target, a specific query, and desired sources. sources names search providers or scopes; it does not authorize arbitrary URL access, commands, or spending.
3. When material is available, return a `dependency_candidate` with target, upstream, citation, relation, basis, differences, and evidence. If only a bibliographic entry is available and no upstream node has been supplied, use upstream=null. Otherwise, upstream must exactly reference a supplied upstream MathClaim or definition. upstream and citation cannot both be null.
4. basis explains the candidate's supporting rationale; differences identifies mismatches in objects, quantifiers, assumptions, conclusions, and applicability. When reuse sufficiency is unclear, report UNKNOWN or a gap. Similar wording alone does not establish USES_LEMMA.

Only `source_locator`, `search_request`, and `dependency_candidate` items are allowed. evidence references source_locator items in this batch or supplied inputs. New locators may locate only supplied sources. Return the shared four-field JSON output.

## Continuing the search

The host reviews requested sources and remaining parent budget before retrieving material. It then pins the sources, calls Paper to extract upstream nodes when necessary, and creates a new Dependency Task. Do not inject new search results into this already-frozen task.

Not finding an upstream result does not establish that none exists or that the target is novel. Preserve search boundaries imposed by budgets, unavailable sources, or cycles. Stop repeated dispatch when the same lead yields no new material; changing query wording does not reset the budget.

## Boundaries

- CITES denotes citation; SIMILAR denotes a similarity lead. USES_LEMMA and USES_DEFINITION are still mathematical dependency candidates awaiting checks.
- If A and B jointly support the target, state their joint role explicitly in basis. The host must not treat two separate candidates as two independently sufficient proofs. This lightweight format does not carry formal inference hyperedges.
- Do not manufacture MathClaims from bibliography titles, modify the target, execute upstream Lean, or recursively formalize the historical chain.
- A cross-paper candidate graph may contain citation cycles. A DAG for a particular proof requires subsequent checks of explicit inference units and scopes. A path in Neo4j is not evidence that a proof holds.
