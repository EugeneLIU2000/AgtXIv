# ADR 0005: Native MathClaimIR/2 with conservative V1 binding

- Decision status: Accepted
- Implementation status: Planned across M1, M4b, and M5
- Milestone: M0
- Date: 2026-08-31
- Roadmap decisions: D6, with D5 and D8 representation consequences
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## Context

The existing V1 `MathClaimIR` contains richer mathematical semantics than the
current V2 work-in-progress record. Replacing it with the thinner V2 shape would
lose typed objects, quantifiers, assumptions, normalization, component structure,
and residual information. Treating a legacy migration as fresh V2 evidence would
also risk promoting provisional or study-only states.

The intuition is a compiler intermediate representation. A good intermediate
form preserves enough structure to check what the symbols mean and how the result
depends on its premises. A compatibility adapter may label the wires from an old
circuit, but relabeling cannot make an untested component verified. The formal
proof, source alignment, and scientific applicability remain separate tests of
the represented statement.

## Decision

1. V2 defines a rich native `MathClaimIR/2` as the forward format. It binds exact
   paper release, source anchor, ScientificClaim, frozen scope, agentization
   profile, producer attempt, contract bundle, and producer execution-environment
   receipt when applicable. A downstream formal proof environment belongs to its
   `FormalizationRequest` and evidence; it is not an IR truth field.
2. Its semantic core includes typed mathematical objects, domains, quantifiers,
   assumptions, conclusion, units, conventions, approximations, normalization,
   semantic hashes, component identities, and residual/non-mathematical semantics
   where applicable.
3. A `MathClaimIR` records the structured meaning attributed to the exact source.
   It is not by itself evidence that the claim is true, formally proved, aligned,
   or scientifically accepted.
4. A legacy V1 record remains byte-identical under its original identity and
   hash. `MathClaimIRBinding/2` exact-refers to it and records V2 provenance,
   scope, component mapping, residual mapping, losses/ambiguities, and mapping
   evidence. The binding never rewrites the V1 record.
5. Downstream producers consume one common read projection over native V2 and
   bound V1 records. The projection exposes origin and mapping quality and cannot
   hide residual or unknown fields.
6. No migration or projection may promote `ASSUMED_VERIFIED_FOR_STUDY`,
   provisional, unknown, blocked, refuted, residual, or not-assessed information
   into stronger evidence. Verification and assessment records remain external,
   independently referenced objects.
7. Mathematical reasoning uses typed `InferenceStep` objects so multi-premise
   inference is not flattened into ambiguous pairwise claim edges.
8. Graph artifacts follow D8's distinct ontologies:
   `ArtifactProvenanceGraph`, `PaperStructureGraph`, `PaperInteractionGraph`,
   `ClaimInferenceGraph`, `MathClaimDependencyGraph`,
   `FormalDeclarationDependencyGraph`, `PaperBuildDAG`, and read-only
   `QueryProjection`. Only a projection that proves acyclicity is called a DAG.

Every graph snapshot states its kind, ontology revision, direction convention,
exact source/scope/profile refs, lifecycle states, reconstruction algorithm, and
canonical hash. Candidate, accepted, rejected, conditional, and blocked
dependencies remain distinguishable. Cross-paper cycles are preserved in the
interaction graph and condensed into strongly connected components only for
build ordering.

## Consequences

### Positive

- V2 does not regress the mathematical expressiveness already present in V1.
- Legacy evidence is reusable without rewriting its history or silently
  strengthening its status.
- Multi-premise reasoning and different graph meanings remain auditable.
- Source fidelity, formal validity, and scientific applicability can disagree
  without corrupting the IR.

### Costs and constraints

- Native records and legacy bindings need separate schemas, fixtures, validators,
  and migration reports.
- The common read projection must be mechanically checked against JSON Schema and
  tested for information loss.
- Graph producers and UI views must declare ontology rather than sharing one vague
  `edge` type.
- Some V1 records will remain quarantined or partial when their semantics cannot
  be mapped conservatively.

## Invariants

1. Every native or bound IR value has exact source, claim, scope, profile,
   producer, and contract provenance.
2. V1 content, identity, hash, and original status are immutable.
3. A binding or projection cannot create evidence, assessments, source alignment,
   kernel success, or scientific acceptance.
4. Unknown, ambiguous, residual, approximation, unit, convention, and assumption
   information is preserved or explicitly reported as mapping loss.
5. Mathematical components have stable identities so formalization requests and
   evidence bind an exact component rather than prose similarity.
6. Claim inference is multi-premise through `InferenceStep`; a pairwise edge does
   not falsely claim the same semantics.
7. Each graph snapshot declares one ontology and lifecycle policy. Graph kinds
   that permit cycles are not labeled DAGs.
8. Accepted build projections pass independent root, closure, direction, and
   cycle checks; rejected/candidate edges are not silently deleted.

## Acceptance tests

| Test | Expected result |
|---|---|
| Round-trip a rich V1 record through `MathClaimIRBinding/2` and the common projection | Typed objects, quantifiers, assumptions, residuals, origin, and original status are preserved. |
| Bind a V1 `ASSUMED_VERIFIED_FOR_STUDY` record | Projection retains that exact status and contains no new verification or acceptance evidence. |
| Omit a quantifier, assumption, unit, approximation, or residual during mapping | Validator requires an explicit loss/ambiguity disposition; silent loss fails. |
| Present a native IR as proof or scientific acceptance | Cross-record validation rejects the unsupported status. |
| Encode a two-premise inference as two untyped pairwise edges | Claim-inference validation fails; an `InferenceStep` with both premises is required. |
| Put a cross-paper cycle in `PaperInteractionGraph` | Graph remains valid and visible; `PaperBuildDAG` contains the corresponding condensed component. |
| Put a cycle in an accepted mathematical build projection without a typed cycle disposition | DAG validation fails closed. |
| Compare CLI, API, and UI closure for one exact graph snapshot | All return the same nodes, edges, statuses, and canonical snapshot hash. |

## Related records

- `docs/roadmaps/v2-end-to-end-implementation-plan.md`, decisions D5, D6, D8
- `docs/specifications/mathematics-pipeline.md`
- `docs/specifications/v1-bridge.md`
- `docs/specifications/v2-paper-agentization.md`
- ADR 0004 for catalog and admission boundaries
