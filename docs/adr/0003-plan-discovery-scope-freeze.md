# ADR 0003: Plan, discovery, and independent scope freeze

- Decision status: Accepted
- Implementation status: Planned across M1 and M4a
- Milestone: M0
- Date: 2026-08-31
- Roadmap decision: D3
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## Context

Whole-paper completeness cannot be measured against an inventory that is chosen
after extraction. A producer could otherwise appear complete by not discovering
the hard appendix, an included TeX file, a figure claim, or an ambiguous formula.
The current V2 slice has a preselected `InventoryScope`; it does not yet represent
the discovery process or an independent completeness decision.

The intuition is surveying a building before inspecting it. First define which
building and inspection standard apply. Then survey every room, including locked
and ambiguous rooms. A different inspector freezes the floor plan. Only then can
we say whether every room received a disposition. Discovering a hidden room later
does not redraw the old signed plan; it triggers a new survey revision.

## Decision

V2 separates four immutable objects in this order:

1. **`AgentizationPlan`** freezes the exact paper release, agentization profile,
   artifact-family catalog, discovery obligations, resource policy, and producer
   policy before whole-paper analysis begins.
2. **`InventoryDiscoveryResult`** records classified, unclassified, and ambiguous
   source components; coverage evidence; extraction/discovery errors; exact tool
   and environment versions; resource limits; and the producer's completeness
   claim. It is evidence, not authority to freeze the scope.
3. **`ScopeFreezeDecision`** is an independent review of discovery completeness.
   It binds the exact plan, discovery result, source tree, reviewer identity,
   independence evidence, policy, rationale, findings, and signed decision when
   production policy requires it.
4. **`FrozenInventoryScope`** is the only inventory against which downstream
   family cardinality and whole-paper accounting are measured. It binds the
   accepted freeze decision and assigns stable inventory-entry identities.

An unresolved or ambiguous component remains an explicit scope entry and receives
a typed terminal disposition; it is not dropped. If later evidence discovers a
new component or changes classification, the system creates a new discovery,
freeze decision, and scope revision. Every downstream artifact whose inputs or
coverage claim are affected is stale for the new revision and must be regenerated
or explicitly dispositioned. The older scope and its releases remain addressable.

Queries may trigger a new plan but may not narrow a canonical plan, discovery
obligation, or frozen scope to match the query.

## Consequences

### Positive

- "Complete" means complete against an independently reviewed denominator.
- Hidden, malformed, ambiguous, and unclassified material remains visible.
- Post-freeze discoveries cannot silently alter already released coverage.
- Query-driven work can add a stronger profile without rewriting a prior Paper
  Agent as though it always had that scope.

### Costs and constraints

- Discovery becomes a reviewable stage with its own records and user interface.
- A new source component can invalidate substantial downstream work.
- Scope revision logic must compute affected artifacts and gates by exact lineage.
- The project needs fixtures where discovery is incomplete, ambiguous, malicious,
  or later superseded.

## Invariants

1. Plan precedes discovery; discovery precedes freeze review; freeze review
   precedes `FrozenInventoryScope` and downstream accounting.
2. The discovery producer cannot approve its own `ScopeFreezeDecision`.
3. Every source-tree unit and every semantic component class or region required
   by the exact `AgentizationPlan` and profile is classified, ambiguous,
   unclassified, or rejected with evidence; absence from the inventory is not a
   disposition. Independent freeze review supports a profile-relative
   completeness claim, not proof that no unknown claim exists.
4. Every downstream record exact-refers to one frozen scope revision.
5. Scope entries and their source-byte bindings are immutable after freeze.
6. A later discovery creates a new revision and invalidates affected new-scope
   gates; it does not mutate an older scope or release.
7. Completeness is profile-relative and query-independent.

## Acceptance tests

| Test | Expected result |
|---|---|
| Discovery omits an included appendix found by an independent reviewer | Freeze is rejected or blocked; no `FrozenInventoryScope` is issued. |
| Discovery reports an undecodable component | The component remains explicit as unclassified/ambiguous with evidence and a terminal handling obligation. |
| Producer and scope-freeze reviewer have the same identity or forbidden conflict | Policy and database constraints reject the decision. |
| A new source component appears after freeze | A new scope revision is created; dependent artifacts and gates for that revision become stale, while the old release remains immutable. |
| A query requests only one theorem from a larger paper profile | The query may schedule work but cannot remove the other profile-required components. |
| Attempt to count accounting completeness against `InventoryDiscoveryResult` rather than `FrozenInventoryScope` | Cross-record validation rejects the release. |
| Every frozen entry receives exactly one family disposition | Accounting check passes even when some dispositions are evidence-backed `BLOCKED`, `FAILED`, or `NOT_APPLICABLE`. |

## Related records

- `docs/roadmaps/v2-end-to-end-implementation-plan.md`, decision D3
- ADR 0004 for accounting and release gates
- `docs/security/v2-threat-model.md` for hostile or ambiguous source components
