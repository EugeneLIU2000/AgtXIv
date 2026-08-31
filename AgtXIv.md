# AgtXIv: Standardized Paper Agentization and Verification-Aware Knowledge

**Status:** V1 compatibility body with V2 primary architecture
**Version:** 0.6 compatibility text; V2 contracts are version 2.0.0
**Date:** 2026-08-28
**Primary target:** Mathematical claims in theoretical physics and mathematically structured sciences
**Normative V2 paper agentization:** [AgtXIv V2 Paper Agentization](docs/specifications/v2-paper-agentization.md)
**Normative paper-source acquisition:** [AgtXIv Paper Source Acquisition](docs/specifications/paper-source-acquisition.md)
**Normative V1 bridge:** [AgtXIv V1 Claim--Mathematics Bridge](docs/specifications/v1-bridge.md)
**Normative mathematics detail:** [AgtXIv Mathematics Pipeline](docs/specifications/mathematics-pipeline.md)
**Implementation roadmap:** [AgtXIv v1 vertical-slice checklist](docs/roadmaps/v1-implementation-checklist.md)
**Revision note:** [Architecture changes from v0.3 to v0.4](docs/specifications/v0.3-to-v0.4-architecture-changes.md)

The [V2 paper-agentization specification](docs/specifications/v2-paper-agentization.md) establishes the primary release-centered, query-independent architecture and is authoritative for V2 construction, completion, roles, releases, and query modes. In that namespace, the **V2 Root Agent is the accountable paper-level verification/audit authority**: it verifies the exact candidate package in dependency order, preserves unresolved states, and issues the release recommendation. The distinct **ReleaseCertifier is independent and mechanical**: it may certify only an exact `RECOMMEND_PROFILE_RELEASE` audit for which every required mechanical check passes; otherwise it records rejection. This binds the immutable Root Agent audit, hashes, policy, and release identity without self-certification. The current body of `AgtXIv.md` preserves V1 compatibility semantics for bounded query-relative `ClaimMathBridge` / `BridgeAssessment` workflows; it must not be read as making those workflows canonical V2 package construction. The paper-source acquisition specification governs canonical full-text acquisition, and the mathematics pipeline documents legacy/downstream mathematics workflows. Safety and non-promotion rules remain mandatory across versions.

## Abstract

AgtXIv V2 is a paper-agentization framework. It begins from one exact paper release and an exact `AgentizationProfile` / `InventoryScope`, performs query-independent profile-scoped analysis of the whole release, and produces a `Paper Agent Release`. Its Root Agent is not a conversational answer generator: it is accountable for the immutable, stepwise paper-level audit and scientific/profile release recommendation. A separate ReleaseCertifier mechanically binds that audit to the release; it does not redo scientific judgment. Claims, `MathClaimIR`, dependencies and inferences, generated formalization artifacts, formal verification, evidence, alignments, assessments, blockers, and mixed per-entry dispositions remain separately inspectable rather than being collapsed into a fluent summary or an aggregate truth label.

A certified package feeds a derived verification-aware Knowledge Base through per-entry admission gates. Standard queries are downstream, read-only retrieval over the exact certified release and index. Release completion means total profile/scope-relative disposition accounting; it does not mean whole-paper truth, aggregate verification, scientific acceptance, or admission of every packaged entry.

**V1 compatibility paragraph.** The remainder of this document preserves the earlier bounded, query-relative claim-assessment design rather than silently rewriting it. Under that frozen path, `ScientificClaim`, `ClaimMathBridge`, `MathClaimIR`, and `BridgeAssessment` support a conservative Root Agent conclusion for one bounded claim. Those records and query-relative dependency views remain readable downstream in V2, but they are not canonical V2 package construction, and the V1 Root Agent is not a V2 release role.

AgtXIv does not require a dedicated hypergraph data structure in the pilot. A multi-premise inference is represented by an explicit `InferenceStep` node: several claims point to the step, and the step points to its conclusion. This retains the joint-premise semantics while allowing the implementation to use an ordinary typed directed graph.

Candidate claims and relations are generated through a constrained extraction pipeline:

```text
LLM extraction
→ constrained schema
→ source grounding
→ relation validation
→ candidate graph
→ verification-guided refinement
```

Candidate retrieval, symbolic algebra, theorem search, and language-model generation are treated as Oracles. They may propose statements, edges, decompositions, Lean code, or certificates, but they cannot promote a claim or relation to an accepted contract without the configured checks.

The formalization loop is designed for high automation. It uses a structured `MathClaimIR`, package and declaration retrieval, a formalizer or blueprint agent, Lean kernel checking, a source-blind backtranslation agent, an alignment auditor, and a source-aware refiner. Round-trip consistency is evidence of stability but not by itself proof of source fidelity; the system therefore compares quantifiers, object types, assumptions, domains, exactness, approximation status, and conclusion strength across the source claim, `MathClaimIR`, Lean declaration, and backtranslation.

Physical interpretation, model assumptions, approximation regimes, operational definitions, and empirical support are represented in one `SemanticContract`. They share a natural-language interface but produce evidence for distinct externally derived axes, especially `semantic_alignment`, `approximation_regime`, and `empirical_support`. Numerical reproduction is an optional claim-attached `ReproductionRecord`; the pilot does not require a computational DAG or Lean verification of numerical software.

Verification proceeds backward and forward. A target is traced backward to query-relative Root Agents or reusable root contracts. Verification then runs forward, proving only the residual local deltas. Failed proof construction, semantic misalignment, or missing foundations trigger local graph refinement. The resulting registry is intended to reduce marginal formalization cost as accepted contracts are reused across later targets; the pilot records reuse and repair telemetry even before cost-aware scheduling is introduced.

AgtXIv distinguishes the following questions and does not collapse them into one Boolean label:

1. **Source fidelity:** What did the frozen paper actually state?
2. **Mathematical correctness:** Does the formal conclusion follow from the encoded formal assumptions?
3. **Formal alignment:** Does the Lean declaration preserve the intended mathematical claim?
4. **Semantic alignment:** Does the formal or computational object represent the intended physical system, approximation, and observable?
5. **Empirical support:** What evidence supports the physical assumptions or modeled regime?
6. **Computational reproducibility:** Can a load-bearing numerical result be independently regenerated when reproduction is attempted?

Lean 4 and pinned formal packages provide a trusted mathematical kernel. They are not treated as a complete ground-truth oracle for physics. Physical applicability, approximation validity, experimental relevance, and source-to-formal meaning remain explicit contract dimensions.

---

## 1. Goal and Boundaries

### 1.1 Goal

The V1 goal is one bounded, auditable scientific assessment. AgtXIv freezes the source, reconstructs a source-faithful `ScientificClaim`, aligns each relevant source component with the mathematical claims, assumptions, and dependencies that represent it, and then projects verification results back to the original claim without dropping physical meaning. The final Root Agent answer states exactly what the evidence establishes and leaves unsupported parts `UNKNOWN` or `BLOCKED`.

The bridge in this path is an alignment-and-projection boundary. It does not discover research directions, decide novelty, score contributions, or prune scientific claims. Generation provenance, evidence completeness, and scientific acceptance remain separate.

For a narrowly selected scientific topic, AgtXIv may also construct two connected graph views.

The literature-facing view is a typed directed graph:

\[
G_{\mathrm{paper}}
=
\texttt{PaperInteractionGraph}.
\]

Its nodes are frozen PaperAgents. Its edges record claim-backed relations such as theorem import, model reuse, methodological dependence, extension, qualification, or refutation. The graph may contain cycles at paper level because different claims in companion papers may point in opposite directions.

For a target query \(q\), the verification-facing view is:

\[
G_{\mathrm{math}}(q)
=
\texttt{MathClaimDependencyDAG}(q).
\]

Its nodes are mathematical definitions, assumptions, lemmas, theorems, constructions, and explicit external foundations. Its edges encode only load-bearing mathematical dependence for the selected target. This graph must be acyclic after duplicate claims and equivalent contracts have been resolved.

The corresponding PaperAgent build order is derived rather than asserted globally:

\[
\texttt{PaperBuildDAG}(q)
=
\operatorname{CondenseSCC}
\bigl(
\operatorname{ProjectToPapers}(G_{\mathrm{math}}(q))
\bigr).
\]

Each exported claim should be supported by a public path

\[
\text{immutable source}
\rightarrow
\text{normalized claim}
\rightarrow
\text{assumptions and imports}
\rightarrow
\text{inference steps}
\rightarrow
\text{verification records}
\rightarrow
\text{scoped contract}.
\]

The resulting knowledge base is **reasoning-centric**, not merely paper-centric or citation-centric.

### 1.2 Immediate objective

The first implementation should complete one small bridge-to-assessment path:

- one exact source version and one source-faithful `ScientificClaim`;
- one component-complete `ClaimMathBridge`, in which every relevant source component is either mapped to exact `MathClaimIR` records or retained as residual scientific semantics;
- explicit mathematical assumptions, dependencies, and physical applicability conditions;
- existing verification evidence referenced rather than copied into the bridge;
- one separate `BridgeAssessment` that keeps evidence completeness and scientific acceptance distinct;
- one bounded Root Agent answer that preserves `UNKNOWN` and `BLOCKED` and does not strengthen the weakest load-bearing result;
- one adversarial physics review, including a negative case in which formal or mathematical evidence must not be overgeneralized.

Lean reconstruction is preferred for a selected load-bearing result when feasible, but graph optimization, root minimization, contribution modeling, and global closure are not V1 acceptance gates.

### 1.3 Non-goals of the pilot

The pilot does not attempt to:

- formalize an entire paper in Lean;
- cover an entire research field;
- infer scientific truth from citation counts;
- replace expert physical judgment;
- require human review of every root claim before any automated progress can occur;
- treat automated alignment as identical to human semantic review;
- convert every paragraph into a graph node;
- assign a single scalar trust score to a paper;
- publish private model chain-of-thought;
- treat every cited paper as a dependency;
- require a dedicated hypergraph database;
- require a computational dependency DAG;
- formally verify arbitrary numerical packages or datasets;
- regard a successful Lean build as proof that the encoded theorem matches the intended physics;
- regard a frozen PaperAgent as an axiom or an automatically trusted source;
- discover or rank new research directions;
- score novelty, importance, priority, impact, or paper contribution;
- hide or delete source-faithful claims through semantic pruning;
- require contribution-role classification before a claim can enter the V1 bridge;
- treat DAG reachability, navigation coverage, or source provenance as scientific acceptance.

### 1.4 Graph and profile boundaries

The pilot uses four principal objects.

#### PaperInteractionGraph

A global typed directed graph of frozen PaperAgents. It is used for literature archaeology, Agent navigation, and claim-backed inter-paper relations. It may contain cycles.

Initial relation families are:

```text
DEPENDENCY
  imports_definition
  imports_theorem
  uses_assumption
  uses_model
  uses_approximation
  uses_numerical_result
  uses_method

EPISTEMIC
  supports
  extends
  qualifies
  refutes
  supersedes
  contrasts_with
  background_to
```

A refutation is stored directionally:

```text
newer_claim --refutes--> earlier_claim
```

An undirected `conflicts_with` view may be derived for visualization, but it is not the authoritative provenance relation.

#### MathClaimDependencyDAG(q)

The primary graph of the math-first pilot. Its build-order edge vocabulary is deliberately narrow:

```text
definition_dependency
assumption_dependency
theorem_import
scope_dependency
derived_by
```

Registry relations such as

```text
specializes
equivalent_under_assumptions
candidate_same_as
```

are stored beside the DAG but are not themselves topological build edges. Only accepted or explicitly conditional mathematical dependencies are used by the Lean build scheduler. Candidate, equivalence, and specialization relations remain visible without being allowed to create an artificial proof cycle.

#### PaperBuildDAG(q)

A query-relative projection of the mathematical claim DAG to PaperAgents. If the projection creates a paper-level cycle, the involved papers are grouped into a `CompanionBundle`. The condensation graph of these bundles is the actual build DAG. Construction uses only the normative `PaperBuildDAG` request, result, mapping snapshot, SCC algorithm, and artifact interface in Section 5.11.

#### InferenceStep nodes

A joint inference

\[
A\land B\land C\Rightarrow D
\]

is represented as

\[
A,B,C\longrightarrow I\longrightarrow D,
\]

where \(I\) is an explicit `InferenceStep`. This preserves multi-premise semantics without requiring a separate hypergraph implementation.

### 1.5 Profile policy

A paper may initially be represented by:

```yaml
paper_package:
  work_id: work:stable-id
  source_version_id: arxiv:...vN
  work_repository_binding_ref: <exact WorkRepositoryBinding TargetRef>
  source_bundle: source/...
  math_contracts:
    - math-contract:...
  semantic_contracts:
    - semantic-contract:...
  reproduction_records:
    - reproduction:...
  profile_association_refs: []
  unmodeled_profile_kinds:
    - semantics
    - computation
```

`unmodeled_profile_kinds` means that the pilot has not modeled those interfaces. It must not be interpreted as `PASSED` or `NOT_APPLICABLE`.

Cross-profile relations include:

```text
normalizes_to
formalizes_as
operationalizes
assumes_under_regime
empirically_supports
numerically_checks
reproduces
reproduces_with_tolerance
```

AgtXIv standardizes identity, provenance, status propagation, and contract boundaries. It does not force mathematical proof, physical interpretation, experimental support, and numerical reproduction into one proof notion.

### 1.6 Publication identity and version domains

AgtXIv adopts the repository-centered publication principle of the [Agentic Publication Protocol](https://github.com/LionSR/AgenticPublicationProtocol/blob/712c11b5290de184256166fc63e81d7331c15800/PROTOCOL.md): the repository is part of the publication object, not merely a place to store a PDF. One traced intellectual work has one public publication repository. A **publication instance** is that repository together with one exact release. Internally, AgtXIv resolves the human-facing release tag to the full target commit and tree identifiers and records the release-asset hashes; neither a branch nor a tag name alone is an immutable address.

The repository belongs to a stable `work_id`. An exact arXiv version, publisher edition, or other frozen source is a `source_version_id`. A newer source version normally produces a new commit and publication release in the same repository, not a new repository and not a rewrite of an earlier release.

The following version domains are independent:

| Version domain | Meaning | Normative owner |
|---|---|---|
| `work_id` | stable identity of the traced intellectual work | `WorkRegistry` and `WorkRepositoryBinding` |
| `source_version_id` | exact upstream source occurrence, such as an arXiv version | source manifest |
| Git commit and tree identifiers | exact repository bytes | Git object database |
| publication release | public distribution coordinate: repository, tag, resolved commit and tree, and release assets | Git provider plus AgtXIv `ReleaseManifest` binding |
| `record_revision` and `supersedes` | semantic or evidential lineage of one logical AgtXIv record | authoritative AgtXIv registry |
| schema or serialization version | interpretation of record bytes | `SchemaRegistry` |
| `CompositeRegistrySnapshot` | atomic multi-registry read boundary | `SnapshotRegistry` |

No row substitutes for another. One commit may contain many record revisions; a byte-only edit may create a commit without a semantic revision; one record revision may be cited by several releases. `CompositeRegistrySnapshot` is not a Git snapshot, and the AgtXIv `ReleaseManifest` is not the Git release itself.

Repository assignment is owned by one immutable `WorkRepositoryBinding` in `WorkRegistry`:

```yaml
work_repository_binding:
  schema: agtxiv.work-repository-binding/1.0.0
  id: work-repository-binding:stable-id
  record_revision: 1
  supersedes: null
  work_id: work:stable-id
  repository:
    provider: github
    repository_id: provider-stable-repository-id
    canonical_url: https://github.com/owner/repository
  assignment_basis: <exact work-resolution record ref>
  content_hash: sha256:...
```

At one composite registry boundary, each `work_id` has exactly one eligible binding head and each provider-stable repository identity is bound to at most one `work_id`. A repository rename or transfer preserves `repository_id` and creates a new binding revision when its canonical URL changes. A genuine repository migration requires a superseding binding with an explicit migration record; concurrent bindings or forks block acquisition and publication.

Git supplies byte-level history, diffs, blame, branching, merging, distributed storage, commit-addressed paths, and tags. A Git provider may add pull requests, issues, reviews, releases, immutable-release enforcement, signatures, attestations, and continuous integration. AgtXIv reuses these capabilities instead of duplicating them, but treats provider events only as provenance or candidate evidence. A merged pull request, closed issue, green continuous-integration check, fork, submodule, or repository link never creates an accepted scientific relation or verification status by itself.

AgtXIv retains semantic identity, canonical `TargetRef`, source-span semantics, append-only record revisions, registry transactions, claim-level evidence and status, and cross-repository dependency graphs. Published tags are never retargeted, release assets are never overwritten, and corrections create a new release and a new AgtXIv `ReleaseManifest` whose `supersedes_publication_ref` points to the earlier publication instance. Immutable provider releases are preferred; durable scholarly releases should also use independent archival identifiers when available.

---

## 2. Core Architecture

### 2.1 Two opposite directions

AgtXIv uses two complementary passes.

#### Backward pass: dependency archaeology

Starting from a selected target claim, trace load-bearing dependencies backward:

\[
\text{Target claim}
\rightarrow
\text{imported theorem, definition, model, or numerical premise}
\rightarrow
\cdots
\rightarrow
\text{query-relative root contracts or Root Agents}.
\]

This pass asks:

- Which earlier result is actually used?
- Which exact claim in the cited paper is imported?
- Are the hypotheses compatible?
- Is the citation load-bearing, methodological, evidential, contrastive, or background?
- Does the target use a theorem, a definition, a model, or only terminology?
- Where should backward expansion stop for this query?

#### Forward pass: verification build

After roots have been selected, rebuild the closure forward:

\[
\text{accepted root exports}
\rightarrow
\text{verified intermediate local deltas}
\rightarrow
\text{verified target local delta}.
\]

This pass asks:

- Which root contracts are already reusable?
- Does the importer satisfy their assumptions?
- How are notation, conventions, object representations, and parameter regimes translated?
- Which part of the proof is imported and which part is new?
- Which target branches remain conditional or blocked?

### 2.2 Graph model

AgtXIv does not impose one graph semantics on every relation.

#### Paper-level graph

\[
G_{\mathrm{paper}}=(V_P,E_P)
\]

is a directed typed graph. A directed cycle does not automatically imply circular proof. It may mean that two papers use different claims from one another, as commonly occurs in companion theoretical and numerical works.

#### Claim-level mathematical graph

\[
G_{\mathrm{math}}(q)=(V_C,E_C)
\]

is a strict query-relative dependency DAG. A cycle here indicates at least one of:

- duplicate or equivalent claims not yet merged;
- circular theorem import;
- an incorrectly oriented edge;
- a proof step being confused with an epistemic relation;
- an unresolved definitional recursion requiring a different representation.

Such a cycle is a graph-audit failure and must be repaired before the graph is used as a build order.

#### Paper build graph

Projecting a claim DAG to papers can produce a cycle even when the claim DAG is acyclic. Therefore AgtXIv uses the normative `PaperBuildDAG` construction interface in Section 5.11, computes strongly connected components after projection, and publishes each multi-agent component using the immutable `CompanionBundle` schema there. The condensation graph of these bundles is acyclic.

#### Crosswalk to the mathematics-pipeline graph views

The [mathematics-pipeline specification](docs/specifications/mathematics-pipeline.md) uses four evidence and lifecycle views that cut across the three system-level graphs above. They are related as follows:

| Mathematics-pipeline view | System-level role |
|---|---|
| Oracle candidate graph $G^{O}$ | Claim-level proposals emitted by extraction and search Oracles. It is not the `PaperInteractionGraph`, and its edges are not accepted dependencies. |
| Registered semantic graph $G^{S}$ | The registry-wide claim graph after normalization and evidence recording. For a query $q$, accepted load-bearing mathematical edges in its required closure induce `MathClaimDependencyDAG(q)`. |
| Lean support graph $G^{L}$ | Kernel-checked declaration dependencies and source-to-formal bindings used as evidence. It supports, but does not replace, source fidelity or semantic alignment. |
| Optimized query graph $G^{Q}$ | The proof-guided, query-relative mathematical view after reversible rejection, redundancy marking, reuse, splitting, or premise expansion. |

`PaperBuildDAG(q)` is a separate paper-level projection of the accepted query-relative claim DAG, followed by strongly connected-component condensation through the exact interface in Section 5.11. No candidate, paper-level, or Lean-support edge is silently promoted into that build order.

### 2.3 Architecture diagram

```text
                  FROZEN PAPERS / TEX / CODE / DATA
                                  │
                                  ▼
                        candidate extraction
                                  │
                  constrained schema + source anchors
                                  │
                                  ▼
                        relation validation
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
       PaperInteractionGraph              claim candidate store
       directed, typed, cyclic            candidate/accepted split
                 │                                 │
                 └──────────────┬──────────────────┘
                                ▼
                         target query q
                                │
                                ▼
                 MathClaimDependencyDAG(q)
                      strict mathematical DAG
                                │
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
          Lean packages     SemanticContract   ReproductionRecord
          + MathContracts   + evidence records optional claim record
                │               │                │
                └───────────────┼────────────────┘
                                ▼
                 verification-guided refinement
                                │
                  accepted / conditional closure
                                │
                                ▼
                    PaperBuildDAG(q) + receipt
```

A publication-oriented overview of the same paper-to-verification flow is maintained as an [SVG figure](docs/assets/agtxiv-paper-to-verification-flowchart.svg). Historical visual alternatives are non-normative and live under `docs/archive/diagram-drafts/`.

### 2.4 Candidate extraction pipeline

AgtXIv separates extraction from validation.

```text
LLM extraction
→ constrained schema
→ source grounding
→ relation validation
→ candidate graph
→ verification feedback
```

#### Extraction

The extractor proposes atomic claims, source anchors, symbols, assumptions, and typed relations. It is not allowed to emit an accepted edge.

V1 extraction begins from the exact source span needed for one selected question. It reconstructs a source-faithful `ScientificClaim`; it does not first decide whether the sentence is a contribution or search the paper for novelty. The bridge then accounts for every relevant source component:

```text
source-faithful ScientificClaim
→ exact source components
→ mapped MathClaimIR definitions, assumptions, dependencies, and conclusions
→ residual physical or empirical semantics retained verbatim
→ independent mathematical evidence and blockers
→ conservative BridgeAssessment
→ bounded Root Agent answer
```

`ClaimMathBridge` contains alignment and generation provenance only. It has no truth, verification, acceptance, novelty, contribution, or aggregate coverage field. `BridgeAssessment` is separate and references exact evidence; it reports mathematical disposition, assumption and object matching, residual-semantics review, evidence completeness, and scientific acceptance on separate axes. A result can be mathematically verified while its physical interpretation remains `UNKNOWN` or `BLOCKED`.

Existing contribution-role `ScientificClaim` records and facet-aware `ClaimSupportAssociation` records remain immutable experimental/navigation artifacts. They may supply candidate source components or mappings, but contribution classification is not a V1 prerequisite, `COMPLETE` navigation coverage is not verification, and a `NONE` mapping never authorizes dropping source semantics. Broad discourse discovery, contribution modeling, and semantic pruning are post-V1 research. A generic ScientificClaim TargetRef or any `claim:` ID remains invalid in `MathClaimDependencyDAG(q)` node slots; only resolved `MathClaimIR` and `MathematicalPropositionIR` targets may enter the mathematical DAG.

#### Constrained schema

Every candidate claim and relation must satisfy a machine-checkable schema. Free-form prose may be stored as notes, but not used as the only representation of quantifiers, assumptions, or relation direction.

#### Source grounding

Every candidate must point to one or more frozen source spans. A relation without supporting source or derivation anchors remains `UNGROUNDED_CANDIDATE` and cannot enter the query build graph.

#### Relation validation

A validator receives the source claim, target claim, citation context, local derivation, and proposed relation. Its initial verdict vocabulary is:

```text
VALID
INVALID
AMBIGUOUS
WRONG_DIRECTION
WRONG_RELATION_TYPE
INSUFFICIENT_SOURCE_SUPPORT
```

The validator does not regenerate the entire graph. It audits one proposed relation at a time.

#### Verification feedback

Corrections discovered through source audit or Lean construction are preserved as training data:

```yaml
relation_correction:
  proposed: imports_theorem
  corrected: uses_definition
  reason: >
    The cited paper supplies the definition, while the theorem used in the
    target is derived locally.
```

Fine-tuning is deferred until the claim granularity, relation ontology, and grounding policy are stable.

Discourse-level epistemic relations and verification dependencies use separate namespaces and evidence. A citation context may propose that one paper supports, extends, qualifies, or refutes another claim, but that relation does not establish theorem import, logical implication, or contradiction. Conversely, an accepted mathematical dependency need not be presented rhetorically as support. `background_to` is retained as a literature observation and never enters `MathClaimDependencyDAG(q)`.

Candidate relation discovery should inspect the cited claim, citing claim, and local citation context together. When available, it should also inspect the cited theorem or definition context. The extractor may propose several independent facets—evidential stance, scope change, method reuse, and logical relation—rather than forcing one mutually exclusive label. Each proposed facet becomes a separate `CandidateRelation` record with one `relation_type`, or remains extractor audit metadata; every candidate follows the existing validation and acceptance path independently.

### 2.5 Search, registry, and incremental build

AgtXIv should be implemented as a search engine combined with a package manager and an incremental build system.

The expensive offline path is:

```text
freeze sources
→ discover contribution-role ScientificClaim candidates in Abstract / Introduction / Conclusion / Discussion
→ calibrate repeated narrative realizations to exact source spans
→ locate explicit body support
→ classify support kinds and coverage without implying verification
→ query-relative FORMAL_ATOMIC decomposition
→ align with canonical reusable theory objects
→ verify only load-bearing mathematics and semantics
→ persist PaperTheoryDelta and QueryResolution records
→ publish accepted contracts and cache verified query closures
```

The online query path is:

```text
normalize query
→ resolve target claim
→ retrieve accepted and candidate contracts
→ load previous QueryResolution records
→ check versions, assumptions, and formal environments
→ reuse compatible accepted closure
→ identify minimal blocked frontier
→ build or refine only the local delta
→ cache the extended path
```

The global store is not required to be a single DAG. It contains:

- a directed `PaperInteractionGraph`;
- versioned claim and contract registries;
- query-relative `MathClaimDependencyDAG` objects;
- query-relative `PaperBuildDAG` objects;
- semantic and reproduction records;
- graph-repair and verification records.

Search and verification remain separate. Theorem search, premise retrieval, informal/formal matching, symbolic inference, and LLM generation may propose candidates. Only exact checking in the pinned environment, source alignment, relation validation, and the configured contract gates can promote them.

### 2.6 QueryResolution, DependencyManifest, and invalidation

```yaml
query_resolution_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.query-resolution-request/1.0.0
  normalized_query_artifact_hash: sha256:...
  requested_target: <TargetRef or null>
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  required_scope: {id: verification-scope:query, revision: 1, content_hash: 'sha256:...'}
  acceptance_profile: KERNEL_CHECKED_ALIGNED
```

```yaml
query_resolution_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.query-resolution-result/1.0.0
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  query_resolution: null
  candidate_targets: []
```

`SUCCEEDED` requires one immutable resolution; ambiguity or unresolved target is `BLOCKED`, invalid query/scope/profile is `REJECTED`, and execution failure emits none.

```yaml
dependency_manifest:
  schema: agtxiv.dependency-manifest/1.0.0
  id: dependency-manifest:resolution-id
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  policies:
    - {id: status-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  verification_scope: {id: verification-scope:query, revision: 1, content_hash: 'sha256:...'}
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  evidence_snapshot: {id: evidence-index:snapshot-7, record_revision: 1, content_hash: 'sha256:...'}
  blocker_snapshot: {id: blocker-index:snapshot-4, record_revision: 1, content_hash: 'sha256:...'}
  schema_artifacts:
    - {schema_uri: 'https://agtxiv.org/schema/math-claimir/1.0.0', schema_version: 1.0.0, artifact_hash: 'sha256:...'}
  graph_inputs:
    root_set: [<TargetRef values>]
    accepted_relation_snapshot: {id: relation-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
    node_manifest: {id: dependency-node-manifest:..., record_revision: 1, content_hash: 'sha256:...'}
    import_receipt_snapshot: {id: import-receipt-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
    build_policy: {id: graph-build-policy:math-dag/1.0.0, record_revision: 1, content_hash: 'sha256:...'}
    algorithm: {id: agtxiv.reverse-dependency-fixed-point/1.0.0, content_hash: 'sha256:...'}
  formal_environment: {id: formal-env:..., record_revision: 1, content_hash: 'sha256:...', artifact_hash: 'sha256:...'}
  contracts: []
  import_receipts: []
  outputs:
    graph_artifacts: []
    closure_artifacts: []
    status_views: []
    export_artifacts: []
  snapshot_expansions:
    - snapshot_ref: {id: evidence-index:snapshot-7, record_revision: 1, content_hash: 'sha256:...'}
      snapshot_role: evidence_snapshot
      manifest_ref: {id: index-entry-manifest:evidence-7, record_revision: 1, content_hash: 'sha256:...'}
      consumed_record_refs: []
      expansion_hash: sha256:...
  expanded_consumed_refs: []
  dependency_edges:
    - edge_type: INPUT_CONSUMED_BY_OUTPUT
      from_ref: <exact consumed record, snapshot, policy, schema artifact, environment, or TargetRef>
      to_ref: <exact produced output record or TargetRef>
    - edge_type: OUTPUT_CONSUMED_BY_OUTPUT
      from_ref: <exact upstream output record or TargetRef>
      to_ref: <exact downstream output record or TargetRef>
  content_hash: sha256:...
```

Every reference is exact. Set-valued arrays are sorted by canonical bytes and reject duplicates. Evidence, blocker, relation, receipt, and other index snapshots must derive from the same composite snapshot. `acceptance_profile` must equal the pinned scope profile. This manifest is the complete cache key and transitive invalidation basis.

`expanded_consumed_refs` is the sorted, duplicate-free union of every direct input reference, every snapshot container and manifest reference, and every individual immutable record reference obtained from `snapshot_expansions`. Expansion resolves the pinned composite snapshot first, verifies the index snapshot's registry manifest revision, append-log prefix and content hash, then emits visible exact member references in ascending canonical-reference bytes. It never follows a floating head. Each expansion stores the hash of this ordered sequence. `dependency_edges` is complete: it contains one `INPUT_CONSUMED_BY_OUTPUT` edge from every expanded consumed reference to every output that directly consumed it, and one `OUTPUT_CONSUMED_BY_OUTPUT` edge for every produced output consumed by a downstream output. Edges are sorted by `(edge_type, canonical(from_ref), canonical(to_ref))`; duplicates, self-edges, unresolved refs, omitted direct inputs, and output-edge cycles invalidate the manifest. These typed edges, not prose or directory scans, define the computable reverse dependency relation.

```yaml
query_resolution:
  schema: agtxiv.query-resolution/1.0.0
  id: resolution:...
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  resolved_target: <TargetRef>
  dependency_manifest: {id: dependency-manifest:resolution-id, record_revision: 1, content_hash: 'sha256:...'}
  reused_from: []
  content_hash: sha256:...
```

```yaml
query_invalidation_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.query-invalidation-request/1.0.0
  applies_to: <exact QueryResolution TargetRef>
  old_dependency_manifest: {id: dependency-manifest:resolution-id, record_revision: 1, content_hash: 'sha256:...'}
  new_composite_registry_snapshot: {id: composite-snapshot:registry-boundary-18, record_revision: 1, content_hash: 'sha256:...'}
  proposed_changed_refs:
    - ref: <exact old or new record, snapshot, or TargetRef>
      change_kind: SUPERSEDED | REMOVED | ADDED | CONTENT_CHANGED
      old_hash: sha256:... | null
      new_hash: sha256:... | null
  invalidation_policy: {id: query-invalidation-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  snapshot_diff_algorithm: {id: agtxiv.snapshot-manifest-diff/1.0.0, content_hash: 'sha256:...'}
  algorithm: {id: agtxiv.transitive-query-invalidation/1.0.0, content_hash: 'sha256:...'}
```

```yaml
query_invalidation_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.query-invalidation-result/1.0.0
  applies_to: <same QueryResolution TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  computed_changed_refs: []
  invalidated_refs: []
  invalidation_trace_hash: null
  superseding_resolution: null
```

The invalidation algorithm expands the old manifest's composite and index snapshots and the corresponding snapshots selected from the new composite snapshot by the same `snapshot_role`. It compares the two sorted exact member-reference sequences by canonical merge: an old-only tuple is `REMOVED`, a new-only tuple is `ADDED`, equal logical IDs with different revisions or hashes are `SUPERSEDED` or `CONTENT_CHANGED` according to registry lineage, and identical tuples are unchanged. It also compares each old/new snapshot container and manifest reference. `computed_changed_refs` is the sorted, duplicate-free result. If `proposed_changed_refs` is nonempty, it must equal that result exactly.

The traversal seeds a canonical FIFO queue with every changed exact reference and, for an addition or replacement, the old snapshot and manifest refs for the affected role. It then follows the old `DependencyManifest.dependency_edges` in reverse-dependency direction, from each `from_ref` to its `to_ref`, including `OUTPUT_CONSUMED_BY_OUTPUT` edges. Each reached output is invalidated exactly once; outgoing edges are visited in canonical order. This snapshot-role seeding ensures that a newly added record invalidates an output whose earlier computation consumed the old complete snapshot even though that record did not yet occur in the old member set. The result sorts invalidated refs, hashes the complete change-detection and traversal trace, recomputes only the affected closure, and emits a new resolution whose `supersedes` pins the old one. A stale or incomplete proposed change set, incomplete expansion, or incomplete edge set is `BLOCKED`; invalid refs or policies are `REJECTED`; execution failure emits no superseding resolution. Old resolutions remain replayable.

### 2.7 Progressive standardization

A contract need not reach full acceptance in one pass:

```text
INDEXED
→ SOURCE_GROUNDED
→ NORMALIZED
→ RELATION_VALIDATED
→ DEPENDENCY_MAPPED
→ PARTIALLY_VERIFIED
→ AUTO_ALIGNMENT_PASSED
→ MATH_CLOSED
```

`semantic_alignment: HUMAN_REVIEWED` together with `human_review: PERFORMED` is additional evidence-derived review state, not a mandatory predecessor of every automated profile. Automated acceptance must not be labeled as human-reviewed.

The query planner upgrades only load-bearing frontier nodes. Broad extraction can remain candidate-level. Formalization and review effort are reserved for claims that block the selected query or have high expected reuse.

### 2.8 Verification-guided graph refinement

The initial graph is intentionally shallow:

\[
G_0=\text{coarse candidate dependency graph}.
\]

At iteration \(k\), one blocked frontier node \(v_k\) is selected. A local diagnostic \(d_k\) determines a repair operation:

\[
G_{k+1}
=
\operatorname{Repair}(G_k,v_k,d_k).
\]

The system does not reconstruct the entire paper after each failure. It expands, rewires, rescopes, or blocks only the affected local region.

The pilot uses three top-level failure classes:

```text
LOCAL_BUILD_FAILURE
ALIGNMENT_FAILURE
SOURCE_OR_FOUNDATION_GAP
```

and three corresponding repair families:

```text
EXPAND_LOCAL
REWIRE_OR_RESCOPE
ESCALATE_OR_BLOCK
```

Detailed compiler messages and natural-language diagnoses are stored as tags rather than proliferating top-level lifecycle states.

### 2.9 Cost and reuse telemetry

Cost-aware scheduling is deferred, but every build records data needed for later optimization:

```yaml
build_metrics:
  new_lean_declarations: 0
  reused_registry_contracts: 0
  reused_external_declarations: 0
  local_bridge_declarations: 0
  formalizer_agent_calls: 0
  backtranslator_agent_calls: 0
  alignment_auditor_calls: 0
  repair_rounds: 0
  source_expansions: 0
  blocked_claims_unlocked: 0
  downstream_targets_reusing_export: 0
  human_review_minutes: 0
```

A later scheduler may estimate

\[
C_{\mathrm{marginal}}(q)
=
C_{\mathrm{extraction}}
+
C_{\mathrm{alignment}}
+
C_{\mathrm{local\ Lean\ delta}}
+
C_{\mathrm{repair}},
\]

and

\[
\operatorname{ReuseGain}(q)
=
1-
\frac{C_{\mathrm{with\ registry}}(q)}
     {C_{\mathrm{cold\ start}}(q)}.
\]

The project records both expected and observed reuse. The number of verified Root Agents alone is not a valid reuse metric.

---

## 3. Trusted Verification Layers

AgtXIv uses several verification layers. They answer different questions and supply evidence to separate externally derived status axes.

### 3.1 Source and provenance layer

This layer establishes what the authors actually stated.

It records:

- stable work identifier and exact frozen source version;
- public publication repository and exact release binding;
- full Git commit and tree identifiers, release-asset hashes, and signatures or attestations when available;
- file and content hashes;
- exact theorem, equation, figure, table, and paragraph anchors;
- cited source versions;
- whether a normalized statement is explicit, implicit, reported from a citation, inferred, or independently derived;
- the source spans supporting each candidate relation.

A source check establishes fidelity to a source. It does not establish truth.

### 3.2 Mathematical kernel

For formalizable mathematical cores, AgtXIv uses:

- Lean 4;
- the Lean kernel;
- pinned Mathlib and domain-package versions;
- explicit project and toolchain files;
- kernel-checked theorem declarations;
- a no-unresolved-placeholder policy for accepted exports;
- declaration-level dependency and axiom audits.

The mathematical kernel answers:

> Under the definitions and assumptions encoded in Lean, does the conclusion follow?

It does not by itself answer:

- whether the Lean theorem matches the source claim;
- whether a source object was mapped to the correct formal type;
- whether a physical assumption is reasonable;
- whether an approximation is valid in the claimed regime;
- whether the modeled observable corresponds to the experimental quantity;
- whether the selected model adequately represents the physical system.

### 3.3 Formal-alignment layer

This layer compares:

```text
frozen source span
↔ normalized MathClaimIR
↔ Lean declaration
↔ source-blind backtranslation
```

It checks at least:

- quantifiers;
- object types and carriers;
- assumptions and scopes;
- domains and codomains;
- equality, inequality, implication, and equivalence modes;
- exact versus approximate status;
- finite versus asymptotic status;
- normalization and convention choices;
- conclusion strength;
- lost or newly introduced edge cases.

Round-trip consistency is useful but insufficient. In general,

\[
F_2(B(F_1(S)))\equiv F_1(S)
\]

does not imply

\[
F_1(S)\equiv S.
\]

A formalizer and backtranslator may share the same abstraction error. Therefore AgtXIv requires a structured source-to-formal alignment audit in addition to Lean compilation.

### 3.4 Semantic layer

Physical interpretation and empirical support are represented in one `SemanticContract` because they are commonly extracted from the same natural-language and experimental context. The contract records:

- physical systems and degrees of freedom;
- preparation and measurement procedures;
- states, observables, and effective variables;
- model assumptions;
- conventions and normalization choices;
- gauge or basis dependence;
- approximation regimes and perturbative orders;
- operational definitions;
- limiting cases and dimensional checks;
- physical interpretation of formal claims;
- evidence records linked to assumptions, regimes, or conclusions.

The object is unified, but external status views derive separate axes:

```text
semantic_alignment
approximation_regime
empirical_support
```

A correct interpretation can have weak empirical support. Strong empirical agreement can coexist with an ambiguous mapping between the measured quantity and the formal observable.

Human review is represented explicitly when it occurs. Automated semantic alignment is allowed as a pilot output, but it must not be mislabeled as expert review.

### 3.5 Computational reproduction layer

The pilot treats numerical work as an optional claim-attached record rather than a separate DAG. A `ReproductionRecord` is organized around six repository-addressable layers: source, data, environment, execution, output, and evidence. It may contain:

- authoritative code or an independent implementation;
- code commit and data hashes;
- inputs and parameters;
- software environment;
- random seeds;
- precision and tolerance;
- generated outputs;
- logs and hashes;
- comparison with reported values or figures.

No Lean proof of the numerical package is required. A reproduction may be exact, tolerance-based, qualitative, failed, blocked, or not attempted.

A numerical record is classified by its role:

```text
ILLUSTRATIVE
SUPPORTING
LOAD_BEARING
```

Failure to reproduce an illustrative result does not automatically block a mathematical theorem. Failure to reproduce a load-bearing numerical claim prevents the corresponding scientific claim from being computationally closed.

### 3.6 No global Boolean verification

No claim or contract stores a Boolean or aggregate verification vector. A consumer requests an immutable `StatusView` for an exact `TargetRef`, policy, required scope, evidence snapshot, and blocker snapshot. For example, a ClaimIR-target view may derive the separate axes `source_fidelity`, `relation_validation`, `dependency_closure`, `mathematics`, `formal_alignment`, `semantic_alignment`, `approximation_regime`, `empirical_support`, `computation`, and `human_review`. The values and every overall label belong only to that external view. A downstream system must pin the exact view or `ClaimImportReceipt` on which it relies.

---

## 4. Paper Agents, Root Agents, and Build Units

### 4.1 Paper Agent

A **PaperAgent** is a source-bounded scientific software object representing one exact source occurrence of a stable traced work and its reconstructed local contribution. The work has one public publication repository; each published PaperAgent revision is bound externally to one exact repository release by an AgtXIv `ReleaseManifest`.

It is not merely a chatbot persona. Its answers and actions are constrained by its release-bound source objects, accepted imports, candidate and accepted reasoning relations, verification records, and unresolved blockers. Repository coordinates locate the package; they do not establish source fidelity, scientific truth, or relation acceptance.

A PaperAgent is modeled as

\[
\mathcal A_i
=
(S_i,I_i,\Delta_i,R_i,V_i,E_i,U_i),
\]

where:

- \(S_i\): immutable source bundle and anchors;
- \(I_i\): imported claim contracts;
- \(\Delta_i\): the paper's local scientific delta;
- \(R_i\): candidate and accepted inference relations;
- \(V_i\): formal, semantic, and computational verification records;
- \(E_i\): exported claim contracts;
- \(U_i\): unresolved questions, blockers, disputes, and superseded statements.

### 4.2 Local scientific delta

A PaperAgent primarily represents what its paper adds beyond imported results:

- new definitions;
- new assumptions;
- new theorems;
- new derivations;
- new approximations;
- new algorithms or numerical results;
- new physical interpretations;
- new limitations, corrections, or counterexamples.

Conceptually,

\[
\text{PaperAgent}
=
\text{frozen source}
+
\text{versioned imports}
+
\text{reconstructed local delta}
+
\text{visible unresolved frontier}.
\]

### 4.3 Root Agent and root contract

A **Root Agent** is a PaperAgent at which backward expansion stops for a specified query and project scope.

Root status is not absolute. A paper may be a root for one claim and an intermediate agent for another. A root is not necessarily:

- the chronologically earliest paper;
- the first paper to introduce a term;
- a paper with no citations;
- a universally foundational work;
- a trusted axiom.

The reusable object imported downstream is the root's accepted `ClaimContract` or `MathContract`, not the authority of the paper as a whole.

A query may also stop directly at:

- a Mathlib declaration;
- a declaration in a pinned domain package;
- an accepted shared `MathContract` with multiple source manifestations;
- an explicit external foundation;
- a blocked unresolved claim.

Such a root contract does not require creating a historical PaperAgent unless source archaeology is useful.

### 4.4 Paper-level cycles and CompanionBundles

Two frozen papers may point to one another through different claims. This does not automatically create a circular mathematical proof. The `PaperInteractionGraph` preserves both directed relations.

For a query build, any strongly connected component in the paper projection is represented as a `CompanionBundle`. The internal claim dependencies remain explicit, while the bundle is treated as one node in `PaperBuildDAG(q)`.

This rule preserves a simple DAG build order without asserting that the full literature graph is globally acyclic.

### 4.5 Root-selection principle

A practical root should satisfy most of the following:

- it contains a load-bearing result actually imported by the target chain;
- it is a primary or near-primary source for that result;
- its core statement can be identified precisely;
- its mathematical core is small enough to reconstruct or connect to an existing package;
- its physical assumptions can be stated explicitly;
- its numerical evidence, if load-bearing, can at least be recorded and scoped;
- further backward expansion would add little value relative to the pilot;
- the expected export is likely to be reusable.

Every stop must have a recorded reason. Root status never suppresses source, proof, or alignment failures.

---

## 5. Minimal Data Model

The math-first pilot treats `ScientificClaim`, `MathClaimIR`, `MathContract`, `ClaimContract`, and `QueryResolution` as primary reusable objects. `AttributionRecord`, `FormalizationRecord`, `BacktranslationRecord`, `VerificationEvidenceRecord`, `AlignmentRecord`, `BlockerRecord`, index snapshots, `StatusPolicy`, `StatusView`, and `ClaimImportReceipt` are independently versioned external records around those stable objects. PaperAgents, semantic records, reproduction records, package-capability records, and graph-repair records provide additional provenance and lifecycle context.

### 5.0 ScientificClaim

A `ScientificClaim` is the stable cross-profile identity of a `FORMAL_ATOMIC` or `NARRATIVE_ATOMIC` source-grounded claim, derived claim, or source-independent proposition. `FORMAL_ATOMIC` remains the default interpretation of legacy `agtxiv.scientific-claim/1.0.0` records; schema `1.1.0` separates stable `work_id` from exact `source_version_id`. Source anchors are mandatory only for `origin.class: SOURCE_OCCURRENCE`; the record never owns aggregate status or a mutable profile map.

```yaml
schema: agtxiv.scientific-claim/1.1.0
id: claim:paper-id:main-bound
record_revision: 1
supersedes: null
produced_at: 2026-08-26T00:00:00Z
work_id: work:stable-id
source_version_id: arxiv:xxxx.xxxxxv2
kind: theorem
text: >
  For every finite-dimensional complex Hilbert space H of dimension n and every
  density operator rho on H, define F(rho) as tr(rho^2) and g(n) as 1; then
  F(rho) is at most g(n).
source_anchors:
  - id: anchor:paper-id:theorem-2
    record_revision: 1
    content_hash: sha256:...
origin:
  class: SOURCE_OCCURRENCE
  assertion_mode: SOURCE_EXPLICIT
content_hash: sha256:...
```

The following contribution profile is an immutable experimental profile retained for compatibility and post-V1 research. It is not part of the minimum V1 `ScientificClaim` identity, is not required to enter `ClaimMathBridge`, and cannot determine claim selection, verification, pruning, or scientific acceptance.

The contribution profile is a constrained ScientificClaim role/profile selected by `claim_role: CONTRIBUTION`, not a parallel entity, target kind, identity ontology, or registry. It uses broad namespaced contribution kinds (`result`, `method`, `construction`, `model`, `empirical_finding`, `computational_finding`, `synthesis`, `qualification`, or `limitation`) and orthogonal namespaced source speech-act, formality, and conditionality fields. Fixture-specific cautions remain record data and validation policy rather than general ontology values.

Its semantic hash covers normalized contribution meaning: stable work and exact source occurrence, role and granularity, broad contribution kind and tags, source characterization, normalized statement, canonical set-valued scope hints, and ordered narrative facets. Serialization uses the schema-pinned `agtxiv.record-canonical-json/1.0.0` profile: UTF-8; Unicode NFC and LF normalization; normalized map keys in Unicode code-point order; RFC-8785-compatible literals for the implemented `null`/Boolean/integer/string subset; schema-declared ordered arrays; and canonical-byte sorting with duplicate rejection for declared set arrays. Non-integral numbers are outside this slice, so this implementation does not claim full RFC 8785 number support. Occurrences and provenance, revisions and timestamps, and serialization metadata are excluded from semantic identity. `artifact_hash` detects those fields and omits its own slot plus the subsequently derived record `content_hash`; record `content_hash` then covers the complete record with only its own slot omitted.

Profile association is an immutable external record. A new semantic or computational profile creates another association revision and does not mutate the `ScientificClaim`.

```yaml
schema: agtxiv.profile-association/1.0.0
id: profile-association:paper-id:main-bound:mathematics
record_revision: 1
supersedes: null
produced_at: 2026-08-18T00:00:00Z
applies_to: <exact ScientificClaim TargetRef; no governing ClaimIR before association>
profile_kind: mathematics
profile_target: <exact ClaimIR TargetRef with semantic_content_hash>
content_hash: sha256:...
```

Calibration and support for a contribution-role ScientificClaim are immutable external records rather than fields of the ScientificClaim. Every inward and supersession reference uses the canonical TargetRef of Section 5.1.2, including namespaced `target_kind`, pinned `type_schema`, exact content and artifact addresses, `component_path`, and governing-ClaimIR fields.

```yaml
scientific_claim_calibration_record:
  scientific_claim_ref: <canonical artifact-bearing contribution-role ScientificClaim TargetRef>
  relation_direction: SOURCE_RELATIVE_TO_NORMALIZED_CLAIM
  primary_to_normalized_relation: EQUIVALENT | CONSERVATIVE_PARAPHRASE | BROADER_THAN | NARROWER_THAN | PARTIAL_OVERLAP | UNRESOLVED
  body_to_normalized_relation: EQUIVALENT | CONSERVATIVE_PARAPHRASE | BROADER_THAN | NARROWER_THAN | PARTIAL_OVERLAP | UNRESOLVED
  calibration_stage: NARRATIVE_CALIBRATED | BODY_LOCATED | SUPPORT_CLASSIFIED | ATOMIC_AUDIT_COMPLETED

claim_support_association:
  association_scope: IMMUTABLE_FACET_NAVIGATION_NOT_QUERY_COVERAGE
  scientific_claim_ref: <canonical artifact-bearing contribution-role ScientificClaim TargetRef>
  navigation_basis_ref: <semantic-only TargetRef to /facets of the same immutable revision>
  facet_outcomes:
    - {facet_id: facet:..., coverage: COMPLETE | PARTIAL | NONE}
  provisional_facet_coverage: COMPLETE | PARTIAL | NONE
  links:
    - facet_id: facet:...
      target_ref: <canonical artifact-bearing MathClaimIR or MathematicalPropositionIR TargetRef>
      facet_coverage: COMPLETE | PARTIAL | NONE
      relationship: DIRECT_ATOMIC_SUPPORT | SUPPORTING_ASSUMPTION | FRAMEWORK_SUPPORT | TOPICAL_NAVIGATION_ONLY
```

The relation direction is normative. Let $S$ be the proposition expressed by the cited source occurrence (or the conjunction of the grouped source spans) and $N$ the normalized contribution-role ScientificClaim. `SOURCE_RELATIVE_TO_NORMALIZED_CLAIM` always classifies $S$ relative to $N$: `EQUIVALENT` requires $S \models N$ and $N \models S$ with the same asserted facets; `CONSERVATIVE_PARAPHRASE` requires that $N$ preserve the source assertion without adding an independently asserted facet, allowing only terminology normalization or an explicit conservative weakening ($S \models N$); `BROADER_THAN` means $S \models N$ but $N \not\models S$ because the source asserts additional cases or scope; `NARROWER_THAN` means $N \models S$ but $S \not\models N$ because the source is restricted to fewer cases or stronger conditions; and `PARTIAL_OVERLAP` means neither straightforwardly entails the other, including when $S$ and $N$ assert different facets. `UNRESOLVED` records that no such judgment is yet justified. Thus an abstract occurrence and a body-enriched normalized narrative use `PARTIAL_OVERLAP` whenever each contains a facet absent from the other; surface phrasing or relative text length does not determine the ordering. Calibration stage records process maturation independently of coverage outcome: a completed atomic audit may conclude `NONE`, `PARTIAL`, or `COMPLETE`. `TOPICAL_NAVIGATION_ONLY` links have facet coverage `NONE`; in particular, technical MathClaimIR coexistence cannot promote a synthesis contribution-role ScientificClaim. Final coverage is query-relative and belongs to a future decomposition/snapshot-scoped `QueryResolution`, not this navigation association. None of these fields is truth or verification status, and there is no `contribution_verified` Boolean.

All three vertical-slice record types are append-only. Their global record key is `(id, record_revision)`, so successive revisions retain one stable identity and coexist in registry history; revision $r>1$ must supersede the exact immutable TargetRef for revision $r-1$. Occurrence IDs, by contrast, are globally unique event IDs and cannot be reused by another record revision. For each contribution-role ScientificClaim `(id, record_revision)` there is exactly one calibration record and one support association whose own `record_revision` equals the pinned claim revision. A calibration or support association identity remains attached to the same ScientificClaim identity across all of its revisions and cannot switch `scientific_claim_ref.target_id`. Historical association generations remain present and continue to reference their historical claim revisions rather than being rewritten to the latest revision.

Verification and lifecycle labels are not stored in either identity record. They are derived in external status views.

Recommended `kind` values are:

```text
definition
assumption
convention
equation
claim
theorem
approximation
numerical_result
physical_interpretation
empirical_observation
limitation
correction
counterexample
```

### 5.1 MathClaimIR

`IR` means **intermediate representation**. `MathClaimIR` is the immutable, prover-independent record of what one frozen source occurrence mathematically asserts. It contains no formalization artifact, backtranslation, verification evidence, alignment result, intellectual-priority judgment, blocker, or policy-derived status.

The normative boundary is:

```text
frozen source occurrence and SourceAnchor
→ source preprocessing and macro expansion
→ immutable MathClaimIR revision
→ immutable, independently versioned external records
→ immutable policy-versioned StatusView
```

Only a change in represented mathematical meaning creates a semantic ClaimIR revision. A new attribution judgment, formalization, verification run, blocker resolution, index snapshot, or status policy never revises ClaimIR.

#### 5.1.1 Layer ownership

| Layer | Authoritative object | Owns | Must not own |
|---|---|---|---|
| 0. Frozen source | `SourceAnchor`, raw and expanded source artifacts | exact occurrence, source location, raw and expanded LaTeX, artifact hashes | normalized meaning, intellectual priority, proof status |
| 1. Stable mathematical meaning | `MathClaimIR` | source statement, typed objects, quantifiers, assumptions, one atomic conclusion, conventions | attribution priority, prover syntax, graph edges, evidence, blockers, statuses |
| 2. External interpretation and artifacts | `AttributionRecord`, `FormalizationRecord`, `BacktranslationRecord`, adapter records | one versioned outward interpretation or artifact | authority to mutate ClaimIR |
| 3. Check evidence | `VerificationEvidenceRecord`, `AlignmentRecord`, `BlockerRecord` | one scoped observation or workflow event | aggregate truth or silent ClaimIR correction |
| 4. Derived presentation | `StatusView` under `StatusPolicy` | deterministic aggregation over pinned snapshots | new evidence or source meaning |

External records point inward through the canonical `TargetRef`; authoritative reverse links are never embedded in their targets.

#### 5.1.2 Immutable envelopes and canonical `TargetRef`

Every normative request inherits `RequestEnvelope`; every normative result inherits `ResultEnvelope`. ``Inherits'' means that all fields below are required in the serialized object and are validated before operation-specific fields. Examples may write `extends` to avoid repetition, but conforming wire objects contain the inherited fields after schema expansion.

```yaml
request_envelope:
  schema: agtxiv.request-envelope/1.0.0
  id: request:<operation>:...
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  producer:
    implementation: ...
    version: ...
    implementation_hash: sha256:...
  content_hash: sha256:...
```

```yaml
result_envelope:
  schema: agtxiv.result-envelope/1.0.0
  id: result:<operation>:...
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  producer:
    implementation: ...
    version: ...
    implementation_hash: sha256:...
  request_ref:
    id: request:<operation>:...
    record_revision: 1
    content_hash: sha256:...
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  reason_codes: []
  content_hash: sha256:...
```

Envelope `content_hash` uses `agtxiv.record-canonical-json/1.0.0`: Unicode NFC, LF line endings, RFC 8785 canonical JSON, schema-declared array order, and SHA-256 over the entire UTF-8 record with only the envelope `content_hash` field omitted. Requests and results are immutable. A corrected request or result increments `record_revision`, pins the previous ID, revision, and hash in `supersedes`, and never overwrites it. `REJECTED` means valid execution found an inadmissible proposal; `BLOCKED` means execution completed but a declared prerequisite is unresolved; `FAILED_TO_RUN` means no domain verdict was produced.

Only target-bearing requests and records require `applies_to`. Policies, registry snapshots, manifests, and other non-target objects use immutable envelopes without a fabricated target.

Normative object types without a specialized construction operation use the generic interface below. It covers ScientificClaims, work-repository bindings, source-package records, anchors, contracts, inference steps, blueprint nodes, semantic contracts, reproductions, package capabilities, and manifests.

```yaml
object_construction_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.object-construction-request/1.0.0
  applies_to: <parent TargetRef; omitted when the object has no target>
  object_type_schema: {uri: 'https://agtxiv.org/schema/...', content_hash: 'sha256:...'}
  candidate_artifact_hash: sha256:...
  authoritative_registry: ...
  validation_policy: {id: object-validation-policy:..., record_revision: 1, content_hash: 'sha256:...'}
```

```yaml
object_construction_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.object-construction-result/1.0.0
  applies_to: <same parent TargetRef; omitted when absent in request>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  constructed_object: null
  validation_findings: []
```

`SUCCEEDED` requires an exact object ID, revision, content hash, artifact hash, and pending registry-transaction write. Schema or policy invalidity is `REJECTED`; unresolved references are `BLOCKED`; execution failure creates no object. Visibility still requires the atomic transaction in Section 10.2.

In examples, `<... TargetRef>` is a schema macro requiring the complete object below; it is never a literal wire value. `TargetRef` is extensible. `target_kind` is a namespaced identifier, not a closed enum, and `type_schema` pins its interpretation.

```yaml
target_ref:
  target_kind: org.agtxiv.claim_ir
  type_schema:
    uri: https://agtxiv.org/schema/math-claimir/1.0.0
    content_hash: sha256:...
  target_id: math-claim-ir:paper-id:main-bound
  target_revision: 1
  target_content_hash: sha256:<semantic-content-hash>
  target_artifact:
    schema_uri: https://agtxiv.org/schema/math-claimir/1.0.0
    schema_version: 1.0.0
    serialization_profile:
      id: agtxiv.canonical-yaml/1.0.0
      content_hash: sha256:...
    artifact_hash: sha256:...
  component_path: null
  claim_ir:
    id: math-claim-ir:paper-id:main-bound
    revision: 1
    semantic_content_hash: sha256:...
  claim_ir_members: []
```

`target_content_hash` is the target record's canonical content hash, except for `org.agtxiv.claim_ir`, where it is `semantic_content_hash`. For a ClaimIR target, `target_artifact` is the separate exact serialization address and never substitutes for mathematical identity. It is mandatory whenever an operation parses, migrates, formalizes, backtranslates from, aligns against, exports, or otherwise consumes serialized ClaimIR bytes. It may be `null` only for semantic-only identity operations such as equality grouping, graph membership, dependency traversal, attribution to mathematical content, or index lookup that neither reads nor emits ClaimIR serialization. For a multi-ClaimIR operation that consumes serialized members, every `claim_ir_members` entry carries its own `artifact` subobject with the same four artifact fields. Other target kinds use `target_artifact` when their type schema requires serialized bytes. `component_path` is either `null` or an RFC 6901 JSON Pointer interpreted under `type_schema`. A semantic assumption, approximation regime, or conclusion is targeted as `target_kind: org.agtxiv.semantic_contract.component`, with the parent semantic-contract ID, revision, content hash, and a component path such as `/assumptions/0`, `/approximations/0`, or `/conclusion`.

The governing-ClaimIR rules are mechanical:

1. If exactly one ClaimIR governs the target, `claim_ir` is mandatory and `claim_ir_members` is empty.
2. If two or more ClaimIR revisions govern it, `claim_ir: null` and nonempty `claim_ir_members` are mandatory.
3. If no ClaimIR exists or governs the target, `claim_ir: null` and `claim_ir_members: []` are mandatory. Preprocessing and failed pre-ClaimIR construction use this case.
4. `claim_ir_members` is sorted lexicographically by `(id, revision, semantic_content_hash)`, contains no duplicate tuple, and must contain every governing ClaimIR.
5. A single ClaimIR must never be duplicated in `claim_ir_members`. Relations, chains, graph closures, exports, and query resolutions use the singular or member form according to their exact membership.
6. An artifact-bearing ClaimIR reference is valid only when registry resolution finds exactly one immutable artifact matching `(id, revision, semantic_content_hash, schema_uri, schema_version, serialization_profile.id, serialization_profile.content_hash, artifact_hash)`. A semantic-only reference cannot be passed to a serialized-content consumer.

A `PublicationRef` is a separate distribution and localization reference. It binds a stable provider repository identity and human-facing URL to a release tag, full target commit, tree, provider release identity, release URL, release-asset hashes, and exact AgtXIv `ReleaseManifest` reference:

```yaml
publication_ref:
  schema: agtxiv.publication-ref/1.0.0
  work_repository_binding:
    id: work-repository-binding:stable-id
    record_revision: 1
    content_hash: sha256:...
  git_release:
    tag_name: agtxiv-v1
    tag_object_oid: <full annotated-tag object ID or null>
    target_commit_oid: <full commit object ID>
    target_tree_oid: <full tree object ID>
    provider_release_id: <stable provider release ID>
    release_url: https://github.com/owner/repository/releases/tag/agtxiv-v1
    payload_release_asset_hashes: []
  agtxiv_release_manifest:
    id: agtxiv-release-manifest:work-slug:release-tag
    record_revision: 1
    content_hash: sha256:...
```

It may locate a source artifact or PaperAgent package, but it never replaces `TargetRef`: repository paths identify bytes at one commit, whereas `TargetRef` identifies a schema-governed scientific object, revision, semantic content, artifact serialization, or component. Branch names and unresolved ``latest'' URLs are invalid `PublicationRef` coordinates.

The target commit cannot be embedded directly or indirectly in a manifest committed inside that same target tree without creating a self-reference. Therefore `PaperAgentManifest` records the source payload path, schema, and artifact hashes but not a `SourcePackageRecord` whose hash depends on the target commit. The post-commit AgtXIv `ReleaseManifest` binds the exact PaperAgent manifest, `SourcePackageRecord`, tag, commit, tree, provider release, and assets.

#### 5.1.3 Canonical ClaimIR semantic hashing

ClaimIR distinguishes mathematical identity from serialization:

```yaml
hashes:
  semantic_content_hash: sha256:...
  artifact:
    schema_uri: https://agtxiv.org/schema/math-claimir/1.0.0
    schema_version: 1.0.0
    serialization_profile:
      id: agtxiv.canonical-yaml/1.0.0
      content_hash: sha256:...
    artifact_hash: sha256:...
```

The normative `agtxiv.claimir-semantic-canonical/1.0.0` profile computes `semantic_content_hash` as follows:

- include `statement_kind`, source occurrence identity and anchor content hashes, normalized expanded-LaTeX statement, structured typed objects, quantifiers, assumptions, local binders, conclusion, mathematical mode, conventions, and normalization relation to source;
- exclude schema URI, serialization metadata, record IDs, semantic revision number, `produced_at`, `supersedes`, producer, artifact paths, migration records, and all external attribution, evidence, status, and blocker data;
- encode UTF-8 after Unicode NFC normalization and LF line-ending normalization;
- sort map keys by Unicode code-point order;
- preserve order for semantically ordered arrays, including quantifiers, binders, assumptions, expression operands, and source spans; sort set-valued arrays by their canonical encoded bytes and reject duplicates;
- encode `null` as JSON `null`, booleans as JSON lowercase literals, integers in minimal base-10 form, and non-integral numbers using RFC 8785 JSON number serialization; NaN and infinities are forbidden;
- normalize expanded LaTeX by LF line endings, NFC text, removal of comments outside verbatim contexts, collapse of non-significant whitespace to one ASCII space, no whitespace adjacent to braces where insignificant, and preservation of token, brace, environment, and expression order; author macros are forbidden;
- hash the resulting RFC 8785 canonical JSON bytes with SHA-256.

`artifact_hash` hashes the complete canonical serialization under its named schema and serialization profile. A meaning-preserving migration preserves `semantic_content_hash` but creates a new schema-pinned `artifact_hash`. Registry resolution of serialized ClaimIR requires ClaimIR ID, semantic revision, `semantic_content_hash`, schema URI and version, serialization-profile ID and hash, and exact `artifact_hash`; ambiguity or absence is a failed resolution, never a ``latest artifact'' fallback. Migration consumes an artifact-bearing TargetRef and emits a new artifact address with the same semantic identity; semantic-only TargetRefs are insufficient migration inputs.

#### 5.1.4 Stable core schema

The following ClaimIR is self-contained. Expanded LaTeX fields are normative mathematical text; structured fields make binder scope and types machine-checkable.

```yaml
schema: agtxiv.math-claimir/1.0.0
id: math-claim-ir:paper-id:main-bound
revision: 1
supersedes: null
produced_at: 2026-08-18T00:00:00Z
claim:
  id: claim:paper-id:main-bound
  record_revision: 1
  content_hash: sha256:...
source:
  statement_anchors:
    - id: anchor:paper-id:theorem-2
      record_revision: 1
      content_hash: sha256:...
  proof_anchors:
    - id: anchor:paper-id:proof-of-theorem-2
      record_revision: 1
      content_hash: sha256:...
  occurrence_work: arxiv:xxxx.xxxxxv2
  source_statement_expanded_latex: >
    Let $H$ be a finite-dimensional complex Hilbert space with
    $n=\dim_{\mathbb{C}}H$. Define $F(\sigma)=\operatorname{tr}(\sigma^2)$
    for density operators $\sigma$ on $H$, and define $g(k)=1$ for
    $k\in\mathbb{N}$. For every density operator $\rho$ on $H$,
    $F(\rho)\leq g(n)$.
statement_kind: theorem
normalized_statement_expanded_latex: >
  For every finite-dimensional complex Hilbert space $H$, every natural number
  $n$ satisfying $n=\dim_{\mathbb{C}}H$, and every density operator $\rho$ on
  $H$, define $F(\sigma)=\operatorname{tr}(\sigma^2)$ for every density
  operator $\sigma$ on $H$ and define $g(k)=1$ for every $k\in\mathbb{N}$.
  Then $F(\rho)\leq g(n)$.
structured_statement:
  typed_objects:
    - symbol_latex: H
      semantic_type: finite_dimensional_complex_hilbert_space
    - symbol_latex: n
      semantic_type: natural_number
    - symbol_latex: \rho
      semantic_type: density_operator
      carrier_latex: H
    - symbol_latex: F
      semantic_type: function
      domain_latex: \{\sigma\mid\sigma\text{ is a density operator on }H\}
      codomain_latex: \mathbb{R}
    - symbol_latex: g
      semantic_type: function
      domain_latex: \mathbb{N}
      codomain_latex: \mathbb{R}
  quantifiers:
    - binder: forall
      variable_latex: H
      domain_latex: \{K\mid K\text{ is a finite-dimensional complex Hilbert space}\}
    - binder: forall
      variable_latex: n
      domain_latex: \mathbb{N}
    - binder: forall
      variable_latex: \rho
      domain_latex: \{\sigma\mid\sigma\text{ is a density operator on }H\}
  assumptions:
    explicit:
      - expression_latex: n=\dim_{\mathbb{C}}H
    source_implicit: []
  local_binders:
    - binder: let
      variable_latex: F
      value_latex: \left(\sigma\mapsto\operatorname{tr}(\sigma^2)\right)
      scope: conclusion
    - binder: let
      variable_latex: g
      value_latex: \left(k\mapsto 1\right)
      scope: conclusion
  conclusion:
    relation: less_than_or_equal
    left_expression_latex: F(\rho)
    right_expression_latex: g(n)
  mathematical_mode:
    exactness: exact
    finite_or_asymptotic: finite
  conventions:
    - density_operator_means_positive_semidefinite_trace_one_operator
normalization:
  profile: agtxiv.expanded-standard-latex/1.0.0
  relation_to_source: LOGICAL_FORM_EXPANDED
  unresolved_symbols: []
hashes:
  semantic_content_hash: sha256:...
  artifact:
    schema_uri: https://agtxiv.org/schema/math-claimir/1.0.0
    schema_version: 1.0.0
    serialization_profile:
      id: agtxiv.canonical-yaml/1.0.0
      content_hash: sha256:...
    artifact_hash: sha256:...
```

`id` is stable across semantic revisions; `revision` selects one immutable source interpretation. `source` fixes the occurrence, while intellectual priority is external. Unknown types, binders, assumptions, or conventions are represented explicitly as unknown only where the schema permits it; otherwise construction fails.

#### 5.1.5 Attribution interface

Attribution is external, scoped, and may remain ambiguous or disputed.

```yaml
attribution_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.attribution-request/1.0.0
  applies_to: <exact ClaimIR TargetRef>
  candidate_attributions:
    - work_ref: work:earlier-primary-source@1
      priority_scope:
        component_path: /structured_statement/conclusion
        statement: mathematical conclusion
      evidence_anchors: [anchor:paper-id:priority-note]
  comparison_policy:
    id: attribution-policy:priority/1.0.0
    record_revision: 1
    content_hash: sha256:...
```

```yaml
attribution_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.attribution-result/1.0.0
  applies_to: <same exact ClaimIR TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  attribution_record: null
  alternatives: []
```

On `SUCCEEDED`, `attribution_record` is mandatory and the immutable record contains one or more entries of `(work_ref, priority_scope, evidence_anchors, position)`, where `position` is `ATTRIBUTED | CO_ATTRIBUTED | AMBIGUOUS | DISPUTED`. Scopes may overlap; overlapping incompatible entries must be `DISPUTED`, while unresolved alternatives are `AMBIGUOUS`. Multiple works are permitted and no artificial single winner is selected. On `BLOCKED`, the record is null and `alternatives` plus missing-evidence reasons are mandatory. `REJECTED` means the proposed scope or evidence is invalid. `FAILED_TO_RUN` contains no attribution disposition. A correction creates a new `AttributionRecord` revision. The ClaimIR source occurrence and semantic revision remain unchanged unless a separate semantic-revision operation changes the mathematical statement.

```yaml
attribution_record:
  schema: agtxiv.attribution/1.0.0
  id: attribution:paper-id:main-bound
  record_revision: 2
  supersedes:
    id: attribution:paper-id:main-bound
    record_revision: 1
    content_hash: sha256:...
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <exact ClaimIR TargetRef>
  entries:
    - work_ref: work:earlier-primary-source@1
      priority_scope:
        component_path: /structured_statement/conclusion
      evidence_anchors: [anchor:paper-id:priority-note]
      position: ATTRIBUTED
  producer:
    implementation: attribution-auditor
    version: 1.0.0
    implementation_hash: sha256:...
  content_hash: sha256:...
```

#### 5.1.6 Source preprocessing

All mathematical text uses recursively expanded standard LaTeX. Raw and expanded artifacts are immutable and use `artifact_hash`.

```yaml
source_preprocessing_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.source-preprocessing-request/1.0.0
  applies_to: <source-artifact TargetRef with no governing ClaimIR>
  target_anchors: [anchor:...]
  preprocessing_context:
    manifest_ref: source-context:...@1
    manifest_artifact_hash: sha256:...
  expansion_profile:
    id: agtxiv.macro-expansion/1.0.0
    content_hash: sha256:...
```

```yaml
source_preprocessing_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.source-preprocessing-result/1.0.0
  applies_to: <same source-artifact TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  raw_artifact: null
  expanded_artifact: null
  partial_audit_artifact: null
  unresolved_macros: []
```

`SUCCEEDED` requires both raw and expanded artifact IDs and `artifact_hash` values and an empty unresolved list. `BLOCKED` requires the raw artifact when readable, `expanded_artifact: null`, unresolved macros, and a partial audit artifact when any output exists. `REJECTED` identifies invalid anchors or context. `FAILED_TO_RUN` has no expanded artifact and reports execution diagnostics. No outcome fabricates a ClaimIR.

#### 5.1.7 Atomicity and ClaimIR construction

One ClaimIR revision has one principal conclusion. Compound source statements decompose through immutable, independently versioned `DecompositionRecord` objects.

```yaml
claim_ir_build_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.claim-ir-build-request/1.0.0
  applies_to: <successful source-preprocessing-result TargetRef with no ClaimIR>
  scientific_claim_ref:
    id: claim:paper-id:main-bound
    record_revision: 1
    content_hash: sha256:...
  expanded_source_artifact:
    id: source:expanded:...
    artifact_hash: sha256:...
  context_refs: []
  normalization_profile:
    id: agtxiv.expanded-standard-latex/1.0.0
    content_hash: sha256:...
```

```yaml
claim_ir_build_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.claim-ir-build-result/1.0.0
  applies_to: <same preprocessing-result TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  claim_ir: null
  normalization_record: null
  decomposition_records: []
  attempt_artifact: null
```

`SUCCEEDED` requires the exact new ClaimIR ID, semantic revision, `semantic_content_hash`, schema URI, `artifact_hash`, normalization record, and any decomposition records. `BLOCKED` requires no ClaimIR and identifies unresolved symbols, types, binders, or assumptions in the immutable attempt artifact. `REJECTED` means the proposed extraction is non-atomic or unsupported by the source. `FAILED_TO_RUN` produces no ClaimIR. Authoritative success records publish atomically to `MathClaimIRRegistry`; Agent directories retain only payloads and transaction references.

#### 5.1.8 Semantic revision and schema migration

```yaml
claim_ir_revision_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.claim-ir-revision-request/1.0.0
  applies_to: <exact artifact-bearing ClaimIR TargetRef>
  proposed_semantic_artifact:
    id: revision-candidate:...
    artifact_hash: sha256:...
  change_reason: SOURCE_MEANING_CORRECTION
  changed_fields: [structured_statement.assumptions]
```

```yaml
claim_ir_revision_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.claim-ir-revision-result/1.0.0
  applies_to: <old exact ClaimIR TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  new_claim_ir: null
  semantic_diff_artifact: null
```

`SUCCEEDED` requires a new semantic revision, new `semantic_content_hash`, artifact reference, and semantic diff. Attribution-only and evidence-only proposals are `REJECTED`. Missing source support is `BLOCKED`; execution failure emits no new ClaimIR.

```yaml
schema_migration_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.schema-migration-request/1.0.0
  applies_to: <exact artifact-bearing ClaimIR TargetRef>
  source_artifact:
    schema_uri: https://agtxiv.org/schema/math-claimir/1.0.0
    schema_version: 1.0.0
    serialization_profile: {id: agtxiv.canonical-yaml/1.0.0, content_hash: 'sha256:...'}
    artifact_hash: sha256:...
  target_schema_uri: https://agtxiv.org/schema/math-claimir/1.1.0
  migration_implementation:
    id: migration:math-claimir-1.0-to-1.1
    version: 1.0.0
    implementation_hash: sha256:...
```

```yaml
schema_migration_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.schema-migration-result/1.0.0
  applies_to: <same exact ClaimIR TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  source_artifact_hash: sha256:...
  target_artifact: null
  semantic_equivalence_evidence: null
```

`SUCCEEDED` requires unchanged ClaimIR ID, semantic revision, and `semantic_content_hash`, plus target schema URI and new `artifact_hash`. A required meaning change is `REJECTED` and must use semantic revision. Missing migration fixtures or undecidable equivalence is `BLOCKED`. `FAILED_TO_RUN` produces no target artifact. Older artifacts remain resolvable by exact schema URI and artifact hash.

#### 5.1.9 Formalization and independent backtranslation

```yaml
formal_environment:
  schema: agtxiv.formal-environment/1.0.0
  id: formal-env:project
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  prover: lean4
  toolchain_artifact_hash: sha256:...
  package_lock_artifact_hash: sha256:...
  project_manifest_artifact_hash: sha256:...
  imported_modules: []
  environment_artifact_hash: sha256:...
  content_hash: sha256:...
```

Module arrays are canonical sorted sets. `environment_artifact_hash` hashes the complete build environment archive; `content_hash` hashes the metadata record.

```yaml
formalization_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.formalization-request/1.0.0
  applies_to: <exact artifact-bearing ClaimIR or MathematicalPropositionIR TargetRef>
  target_system:
    prover: lean4
    adapter: agtxiv.autoformalizer.lean4
    adapter_version: 1.0.0
  environment:
    id: formal-env:...
    record_revision: 1
    content_hash: sha256:...
    artifact_hash: sha256:...
  allowed_imports: []
  formalization_boundary:
    included_claim_components: [structured_statement]
    excluded_claim_components: []
    excluded_semantics: [physical_interpretation]
    required_preservations: [quantifiers, object_types, assumptions, exactness, conclusion_strength]
```

```yaml
formalization_record:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.formalization.lean4/1.0.0
  applies_to: <same exact ClaimIR or MathematicalPropositionIR TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  formalization_boundary: <exact frozen boundary from request>
  generation_state: GENERATED | PARTIAL | null
  declaration_candidates:
    - candidate_id: declaration-candidate:Namespace.mainBound
      declaration_name: Namespace.mainBound
      declaration_kind: theorem
      source_artifact:
        id: formal-source:Namespace.MainBound.lean
        artifact_hash: sha256:...
        byte_start: 0
        byte_end: 0
      canonical_statement_artifact_hash: sha256:...
      statement_hash: sha256:...
      proof_term_hash: sha256:... | null
      imported_declarations: []
      environment: {id: formal-env:..., record_revision: 1, content_hash: 'sha256:...', artifact_hash: 'sha256:...'}
  diagnostic_artifacts: []
```

`candidate_id` is unique within one `FormalizationRecord`; reusing it for any second element makes the record invalid. `declaration_candidates` is sorted by `(declaration_name, declaration_kind, statement_hash, source_artifact.artifact_hash, candidate_id)` and rejects duplicate tuples. The exact formalization-record reference plus `candidate_id` therefore resolves one element, while the remaining `FormalizationCandidateRef` fields provide integrity checks. `imported_declarations` is a canonical sorted set of exact declaration references. Byte ranges are half-open UTF-8 byte offsets and must hash to the declared source slice. `statement_hash` hashes the elaborated canonical type; `canonical_statement_artifact_hash` hashes its serialized syntax; `proof_term_hash` is null only when no proof term was generated.

An operation selects exactly one declaration candidate with the following immutable reference. All fields are mandatory and must resolve to one element of the pinned formalization record:

```yaml
formalization_candidate_ref:
  candidate_id: declaration-candidate:Namespace.mainBound
  declaration_name: Namespace.mainBound
  statement_hash: sha256:...
  source_artifact_hash: sha256:...
  formalization_record:
    id: formalization:paper-id:main-bound:lean4
    record_revision: 1
    content_hash: sha256:...
```

The candidate resolves only when `candidate_id`, `declaration_name`, `statement_hash`, and `source_artifact_hash` exactly equal one candidate under the specified formalization record. Resolution by declaration name alone, list position, or latest record is forbidden.

On `SUCCEEDED`, `generation_state: GENERATED`, a nonempty candidate list, and every element field above are mandatory; reason codes are empty. On `BLOCKED`, `generation_state: PARTIAL`, diagnostics are mandatory, and candidates may be empty or partial. `REJECTED` means the boundary or requested imports violate policy and requires no candidates. `FAILED_TO_RUN` requires `generation_state: null`, no candidate assertions, and execution diagnostics. No outcome contains a backtranslation or verification status.

```yaml
backtranslation_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.backtranslation-request/1.0.0
  applies_to: <exact FormalizationRecord TargetRef including governing ClaimIR>
  formalization_candidate: <exact FormalizationCandidateRef>
  source_blind_context:
    artifact_ref: backtranslation-context:...@1
    artifact_hash: sha256:...
    allowed_inputs: [lean_declaration, required_definitions, actual_imports, namespace_notation]
    forbidden_inputs: [source_text, claim_ir_statement, alignment_record, prior_backtranslation]
```

```yaml
backtranslation_record:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.backtranslation/1.0.0
  applies_to: <same exact FormalizationRecord TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  formalization_candidate: <same exact FormalizationCandidateRef>
  independence_attestation: null
  reconstructed_statement_artifact: null
  human_readable_expanded_latex: null
  detected_assumptions: []
  detected_object_types: []
  diagnostic_artifacts: []
```

When present, `independence_attestation` has this exact shape:

```yaml
independence_attestation:
  schema: agtxiv.backtranslation-independence-attestation/1.0.0
  source_blind_context_hash: sha256:...
  allowed_input_manifest_hash: sha256:...
  observed_input_manifest_hash: sha256:...
  execution_sandbox_hash: sha256:...
  model_and_adapter_hash: sha256:...
  forbidden_input_detected: false
  forbidden_input_kinds: []
  attestor:
    implementation: isolated-backtranslator-runner
    version: 1.0.0
    implementation_hash: sha256:...
  attestation_hash: sha256:...
```

Input-kind arrays are canonical sorted sets. `attestation_hash` uses record canonicalization over this object with that field omitted. The observed manifest must be a byte-identical subset of the allowed manifest; otherwise `forbidden_input_detected` is true.

Every outcome echoes the request's `formalization_candidate` byte-for-byte. `SUCCEEDED` requires this independence attestation with `forbidden_input_detected: false`, plus a reconstructed structured artifact and hash, expanded LaTeX, and detected assumption/type lists. `BLOCKED` requires the same valid attestation but incomplete interpretation and diagnostics. Detection of a forbidden input is `REJECTED`, requires an attestation with `forbidden_input_detected: true`, and emits no backtranslation assertion. `FAILED_TO_RUN` requires `independence_attestation: null` and no reconstructed statement. A candidate that does not resolve exactly is `REJECTED`. Backtranslation points inward; immutable targets never point outward to it.

#### 5.1.10 Verification and alignment

```yaml
verification_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.verification-request/1.0.0
  applies_to: <exact artifact TargetRef, including governing ClaimIR when present>
  method:
    id: lean-kernel-build
    version: 1.0.0
    implementation_hash: sha256:...
  environment:
    id: formal-env:...
    record_revision: 1
    content_hash: sha256:...
    artifact_hash: sha256:...
  requested_scope:
    id: verification-scope:kernel-and-axioms
    revision: 1
    content_hash: sha256:...
```

```yaml
verification_evidence_record:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.verification-evidence/1.0.0
  applies_to: <same exact artifact TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  observed_result: PASSED | FAILED | BLOCKED | null
  checked_scope: []
  unchecked_scope: []
  evidence_artifacts: []
```

`SUCCEEDED` requires `observed_result: PASSED | FAILED` and complete evidence hashes. `BLOCKED` requires `observed_result: BLOCKED` and unresolved prerequisites. `REJECTED` means method, target, scope, or environment is inadmissible and has no observed result. `FAILED_TO_RUN` also has no observed result and records execution diagnostics.

```yaml
alignment_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.alignment-request/1.0.0
  applies_to: <exact FormalizationRecord TargetRef including governing ClaimIR>
  exact_inputs:
    source_artifact:
      id: source:expanded:...
      artifact_hash: sha256:...
    claim_ir:
      id: math-claim-ir:paper-id:main-bound
      revision: 1
      semantic_content_hash: sha256:...
      artifact:
        schema_uri: https://agtxiv.org/schema/math-claimir/1.0.0
        schema_version: 1.0.0
        serialization_profile: {id: agtxiv.canonical-yaml/1.0.0, content_hash: 'sha256:...'}
        artifact_hash: sha256:...
    formalization_record:
      id: formalization:paper-id:main-bound:lean4
      record_revision: 1
      content_hash: sha256:...
    formalization_candidate: <exact FormalizationCandidateRef>
    backtranslation_record:
      id: backtranslation:paper-id:main-bound:lean4
      record_revision: 1
      content_hash: sha256:...
  comparison_policy:
    id: alignment-policy:default
    record_revision: 1
    content_hash: sha256:...
  criticality_policy:
    id: alignment-criticality:default
    record_revision: 1
    content_hash: sha256:...
```

```yaml
alignment_record:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.alignment/1.0.0
  applies_to: <same exact FormalizationRecord TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  formalization_candidate: <same exact FormalizationCandidateRef>
  exact_input_hashes: null
  field_deltas: []
  observed_result: AUTO_ALIGNMENT_PASSED | AUTO_ALIGNMENT_PARTIAL | MISALIGNED | BLOCKED | null
```

When present, `exact_input_hashes` is:

```yaml
exact_input_hashes:
  source_artifact_hash: sha256:...
  claim_ir_semantic_content_hash: sha256:...
  claim_ir_artifact_hash: sha256:...
  formalization_record_hash: sha256:...
  formalization_candidate_ref_hash: sha256:...
  declaration_statement_hash: sha256:...
  backtranslation_record_hash: sha256:...
  source_blind_context_hash: sha256:...
  comparison_policy_hash: sha256:...
  criticality_policy_hash: sha256:...
  combined_input_hash: sha256:...
```

`formalization_candidate_ref_hash` hashes the complete canonical `FormalizationCandidateRef`. `combined_input_hash` hashes the preceding map canonically with itself omitted. The alignment request's candidate must equal the candidate echoed by the pinned backtranslation record and resolve under the pinned formalization record. Each field delta has this exact shape:

```yaml
field_delta:
  field_path: /structured_statement/quantifiers/0
  field_class: QUANTIFIER
  delta_kind: MISSING
  source_value: {state: PRESENT, canonical_value_hash: 'sha256:...', reason_code: null}
  formal_value: {state: MISSING, canonical_value_hash: 'sha256:<missing-sentinel-hash>', reason_code: ABSENT_BINDER}
  backtranslation_value: {state: NOT_COMPARABLE, canonical_value_hash: 'sha256:...', reason_code: UPSTREAM_MISSING_BINDER}
  severity: CRITICAL
  explanation: ...
```

`field_class` is exactly one of `QUANTIFIER`, `BINDER_SCOPE`, `OBJECT_TYPE`, `ASSUMPTION`, `DOMAIN`, `CODOMAIN`, `EXACTNESS`, `FINITE_ASYMPTOTIC_MODE`, `NORMALIZATION`, `CONVENTION`, `CONCLUSION_STRENGTH`, or `EDGE_CASE`. `delta_kind` is `MISSING`, `ADDED`, `CHANGED`, `WEAKENED`, `STRENGTHENED`, `TYPE_CHANGED`, `SCOPE_CHANGED`, `EXACTNESS_CHANGED`, or `ORDER_CHANGED`. Value state is `PRESENT`, `MISSING`, or `NOT_COMPARABLE`. Present values hash canonical field-value JSON. Missing values use the fixed SHA-256 hash of UTF-8 `agtxiv:missing-value/1.0.0`. Noncomparable values hash canonical `(reason_code, available_value_hashes)`; reason code is mandatory and no invented value is permitted.

The exhaustive criticality rule starts from `MISSING:ERROR`, `ADDED:ERROR`, `CHANGED:WARNING`, `WEAKENED:ERROR`, `STRENGTHENED:ERROR`, `TYPE_CHANGED:CRITICAL`, `SCOPE_CHANGED:CRITICAL`, `EXACTNESS_CHANGED:CRITICAL`, and `ORDER_CHANGED:WARNING`, then raises severity one level, capped at `CRITICAL`, for field classes `QUANTIFIER`, `BINDER_SCOPE`, `OBJECT_TYPE`, `ASSUMPTION`, `DOMAIN`, `CODOMAIN`, and `CONCLUSION_STRENGTH`. A noncomparable required field blocks alignment instead of producing a delta. Deltas are sorted by `(field_path, field_class, delta_kind, source_value.canonical_value_hash, formal_value.canonical_value_hash, backtranslation_value.canonical_value_hash)` and duplicates are rejected. Any `CRITICAL` delta yields `MISALIGNED`; otherwise any `ERROR` yields `AUTO_ALIGNMENT_PARTIAL`; only `INFO` or `WARNING` deltas permit `AUTO_ALIGNMENT_PASSED`.

Every outcome echoes the request's `formalization_candidate` byte-for-byte. `SUCCEEDED` requires `exact_input_hashes`, complete ordered deltas, and one of `AUTO_ALIGNMENT_PASSED`, `AUTO_ALIGNMENT_PARTIAL`, or `MISALIGNED`; any unresolved `CRITICAL` delta forces `MISALIGNED`. `BLOCKED` requires the hashes available before the block, `observed_result: BLOCKED`, and an unavailable or uninterpretable input reason. `REJECTED` means input TargetRefs do not share the same ClaimIR, candidate resolution fails, the backtranslation selects another candidate, or independence policy is violated, and it pins the inspected input hashes. `FAILED_TO_RUN` requires `exact_input_hashes: null`, `observed_result: null`, and no alignment conclusion. `PASSED` alone is never an alignment aggregate.

#### 5.1.11 Blocker event interface

Blockers are immutable optimistic-concurrency event streams.

```yaml
blocker_write_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.blocker-write-request/1.0.0
  applies_to: <exact blocked TargetRef>
  blocker_id: blocker:paper-id:main-bound:missing-foundation
  write_kind: TRANSITION | CORRECTION
  transition: OPENED | RESOLVED | REOPENED | null
  expected_prior:
    record_revision: 1
    content_hash: sha256:...
  blocker_scope:
    stage: formalization
    required_axis: mathematics
    component_path: null
  blocker_type: UNRESOLVED_EXTERNAL_FOUNDATION
  statement: ...
  evidence_refs: []
  corrects: null
```

For initial `OPENED`, `expected_prior: null` is mandatory. Every later write pins the immediately preceding revision and hash. A correction sets `transition: null`, pins the exact event in `corrects`, and preserves its effective state; it corrects non-scope metadata without pretending that resolution occurred.

```yaml
blocker_write_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.blocker-write-result/1.0.0
  applies_to: <same exact blocked TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  blocker_record: null
  current_head: null
```

On `SUCCEEDED`, `blocker_record` is mandatory and is an immutable `BlockerRecord` containing the request target, scope, transition or correction, `effective_state_after: OPEN | RESOLVED`, exact prior link, and record hash. Legal transitions are initial `OPENED` to `OPEN`, `OPENED | REOPENED → RESOLVED`, and `RESOLVED → REOPENED`; all others are `REJECTED`. A stale `expected_prior` is `BLOCKED` and returns the exact current head for retry. `FAILED_TO_RUN` creates no event.

Every transition and correction must have the same blocker ID, target, and scope as its prior event; changing target or scope requires a new blocker ID. Stream folding rejects duplicate revisions, hash mismatch, forks, missing ancestors, and cycles. Such a stream has no current state and status derivation fails rather than choosing a branch. Resolution evidence must target the same object or a component within the blocker scope.

#### 5.1.12 Composite registry and external index snapshots

A `CompositeRegistrySnapshot` atomically pins the read boundary of every registry participating in an operation:

```yaml
composite_registry_snapshot:
  schema: agtxiv.composite-registry-snapshot/1.0.0
  id: composite-snapshot:registry-boundary-17
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  registries:
    - registry_id: ExternalRecordRegistry
      manifest_revision: 17
      manifest_content_hash: sha256:...
      append_log_segment: append-log:external:17
      inclusive_offset: 4812
      prefix_hash: sha256:...
      supersession_state_hash: sha256:...
  registry_order: lexicographic_registry_id
  content_hash: sha256:...
```

`registries` contains every participating registry exactly once, is sorted by `registry_id`, and rejects duplicates. `supersession_state_hash` hashes the canonical map from every visible logical record ID to its unique eligible head or explicit fork marker at that boundary. The snapshot is created under a multi-registry read lock or from one transaction receipt, so mixed-time boundaries are invalid. Forks may be represented for audit but make dependent status, graph, query, or release operations `BLOCKED`.

Every status derivation, graph build, query resolution, and release transaction pins one exact composite snapshot. Evidence and blocker indexes are deterministic derived views of that same snapshot and must echo its ID, revision, and content hash; an index derived from another boundary is incompatible.

Index snapshots are deterministic views over a content-addressed registry boundary and are not evidence authorities.

```yaml
index_snapshot_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.index-snapshot-request/1.0.0
  composite_registry_snapshot:
    id: composite-snapshot:registry-boundary-17
    record_revision: 1
    content_hash: sha256:...
  source_registry_ids: [ExternalRecordRegistry]
  index_kind: evidence | blocker | relation | import_receipt | graph | registry
  record_type_schemas: []
  index_profile:
    id: agtxiv.external-index/1.0.0
    content_hash: sha256:...
```

```yaml
index_snapshot_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.index-snapshot-result/1.0.0
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  index_snapshot: null
```

`SUCCEEDED` requires the following immutable non-target snapshot:

```yaml
index_snapshot:
  schema: agtxiv.index-snapshot/1.0.0
  id: external-index:snapshot-7
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  composite_registry_snapshot:
    id: composite-snapshot:registry-boundary-17
    record_revision: 1
    content_hash: sha256:...
  source_registry_ids: [ExternalRecordRegistry]
  index_kind: evidence | blocker | relation | import_receipt | graph | registry
  included_record_manifest_hash: sha256:...
  eligible_heads_hash: sha256:...
  index_implementation_hash: sha256:...
  content_hash: sha256:...
```

Records are deduplicated by `(id, record_revision, content_hash)`, sorted by `(type_schema_uri, id, record_revision, content_hash)`, and retain explicit supersession visibility: all visible revisions are listed, while a separately marked `eligible_heads` set contains only unique non-superseded heads. A duplicate key with unequal content, fork, cycle, missing predecessor, invalid prefix hash, or manifest/log disagreement is `BLOCKED`, not silently repaired. Invalid profile or boundary syntax is `REJECTED`; I/O or implementation failure is `FAILED_TO_RUN`.

```yaml
index_lookup_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.index-lookup-request/1.0.0
  applies_to: <TargetRef>
  index_snapshot:
    id: evidence-index:snapshot-7
    record_revision: 1
    content_hash: sha256:...
  record_type_schemas: []
```

```yaml
index_lookup_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.index-lookup-result/1.0.0
  applies_to: <same TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  matched_records: []
  result_hash: sha256:...
```

No match is `SUCCEEDED` with an empty list. Results use snapshot order. Invalid target/schema is `REJECTED`; unusable snapshot is `BLOCKED`; execution failure has no result hash.

#### 5.1.13 VerificationScope, deterministic StatusPolicy, and StatusView

A `VerificationScope` is immutable and makes the acceptance profile part of the requested computation:

```yaml
verification_scope:
  schema: agtxiv.verification-scope/1.0.0
  id: verification-scope:math-import
  revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  target_selectors:
    target_kinds: [org.agtxiv.claim_ir, org.agtxiv.math_contract, org.agtxiv.claim_contract]
    component_path_patterns: ['']
  required_axes: [source_fidelity, dependency_closure, mathematics, formal_alignment]
  required_axis_thresholds:
    source_fidelity: PASSED
    dependency_closure: COMPLETE
    mathematics: KERNEL_CHECKED
    formal_alignment: AUTO_ALIGNMENT_PASSED
  conditional_axes:
    relation_validation: required_when_target_has_required_relations
    semantic_alignment: omitted
    approximation_regime: omitted
    empirical_support: omitted
    computation: omitted
    human_review: omitted
  content_hash: sha256:...
```

`acceptance_profile` is exactly one of `SOURCE_ONLY`, `DERIVATION_CHECKED`, `PARTIALLY_FORMALIZED`, or `KERNEL_CHECKED_ALIGNED`. For profile-controlled axes, `required_axis_thresholds` must equal the exhaustive profile table below; additional semantic, empirical, computational, or human-review axes state their exact thresholds here. A scope whose axes or thresholds contradict its profile is invalid. Scope arrays are canonical set-valued arrays sorted by canonical bytes with duplicates rejected.

`StatusView` is generic; `ClaimStatusView` is the same schema restricted to a ClaimIR target. A policy is immutable and need not have `applies_to`.

```yaml
status_policy:
  schema: agtxiv.status-policy/1.0.0
  id: status-policy:default
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  producer:
    implementation: status-policy-publisher
    version: 1.0.0
    implementation_hash: sha256:...
  rule_tables:
    evidence_to_axis:
      id: status-rules:evidence-to-axis
      revision: 1
      content_hash: sha256:...
    target_scope_applicability:
      id: status-rules:target-scope-applicability
      revision: 1
      content_hash: sha256:...
    axis_precedence:
      id: status-rules:axis-precedence
      revision: 1
      content_hash: sha256:...
    blocker_reduction:
      id: status-rules:blocker-reduction
      revision: 1
      content_hash: sha256:...
    acceptance_thresholds:
      id: status-rules:acceptance-thresholds
      revision: 1
      content_hash: sha256:...
    overall_predicates:
      id: status-rules:overall-predicates
      revision: 1
      content_hash: sha256:...
  content_hash: sha256:...
```

Each referenced table is an immutable canonical-JSON artifact whose content hash is verified before derivation. Its rows use these schemas:

```yaml
status_rule_row_schemas:
  evidence_to_axis: [evidence_schema_uri, evidence_schema_hash, method, observed_result, checked_scope_predicate, axis, contribution]
  target_scope_applicability: [target_kind, target_type_schema_hash, component_path_pattern, required_scope_id, required_axes, admissible_target_relations]
  axis_precedence: [axis, complete_worst_to_best_values]
  blocker_reduction: [blocker_type, stage, scope_intersection_predicate, effective_state, axis, contribution]
  acceptance_thresholds: [profile_id, target_kind, required_scope_id, axis, minimum_value]
  overall_predicates: [priority, overall_value, boolean_expression_ast]
```

Rows are sorted by their canonical encoded bytes. Pattern languages and Boolean AST operators are versioned in the table schema. Overlapping rows must have identical outputs or derivation fails; no first-match behavior is allowed. Every vocabulary value must occur exactly once in its axis precedence row, and every required `(target, scope, evidence)` combination must map uniquely.

The hash-pinned tables are normative executable data:

- `evidence_to_axis` maps every accepted evidence schema, method, observed result, and checked scope to exactly one axis contribution or `NOT_APPLICABLE`; an unmapped record fails derivation.
- `target_scope_applicability` maps `(target_kind, component_path, required_scope)` to required axes and admissible evidence target relations; evidence for another target or scope is ignored with a derivation trace.
- `axis_precedence` gives complete worst-to-best total orders:
  - `source_fidelity`: `MISALIGNED < BLOCKED < UNCHECKED < PARTIAL < PASSED`;
  - `relation_validation`: `DISPUTED < INVALID < BLOCKED < CANDIDATE < SOURCE_GROUNDED < VALIDATED`;
  - `dependency_closure`: `DISPUTED < INCOMPLETE < BLOCKED < UNCHECKED < COMPLETE`;
  - `mathematics`: `FAILED < BLOCKED < UNCHECKED < PARTIALLY_FORMALIZED < SOURCE_DERIVATION_CHECKED < KERNEL_CHECKED < NOT_APPLICABLE`;
  - `formal_alignment`: `MISALIGNED < BLOCKED < UNCHECKED < BACKTRANSLATED < AUTO_ALIGNMENT_PARTIAL < AUTO_ALIGNMENT_PASSED < HUMAN_REVIEWED < NOT_APPLICABLE`;
  - `semantic_alignment`: `CONTESTED < BLOCKED < UNCHECKED < AGENT_REVIEWED < HUMAN_REVIEWED < NOT_APPLICABLE`;
  - `approximation_regime`: `FAILED < BLOCKED < DECLARED_ONLY < PARTIALLY_CHECKED < CHECKED_IN_STATED_REGIME < NOT_APPLICABLE`;
  - `empirical_support`: `CONTESTED < BLOCKED < UNMODELED < SOURCE_GROUNDED < PARTIAL < SUPPORTED_IN_RECORDED_REGIME < NOT_APPLICABLE`;
  - `computation`: `FAILED < BLOCKED < NOT_ATTEMPTED < QUALITATIVE_ONLY < REPRODUCED_WITH_TOLERANCE < REPRODUCED < NOT_APPLICABLE`;
  - `human_review`: `REJECTED < CONTESTED < NOT_PERFORMED < PARTIAL < PERFORMED`.
- `blocker_reduction` folds only valid blocker streams. An open blocker intersecting an axis scope contributes `BLOCKED`; `DISPUTED`, `MISALIGNED`, or `FAILED` remains worse where the axis order says so. Invalid streams fail derivation.
- `acceptance_thresholds` maps each named acceptance profile and required scope to a minimum value for every required axis. `NOT_APPLICABLE` satisfies a threshold only when applicability explicitly returns it.
- `overall_predicates` are evaluated in this order: `SUPERSEDED`, `DISPUTED`, `FAILED`, `BLOCKED`, `VERIFICATION_CLOSED`, `COMPUTATIONALLY_REPRODUCED`, `SEMANTICALLY_RECONSTRUCTED`, `MATH_CLOSED`, `PARTIALLY_VERIFIED`, `DEPENDENCY_MAPPED`, `RELATION_VALIDATED`, `SOURCE_VALIDATED`, `SOURCE_GROUNDED`, `PROPOSED`. `SUPERSEDED` requires a unique visible superseding target revision. `DISPUTED` requires any required axis at `DISPUTED` or `CONTESTED`. `FAILED` requires any required axis at `FAILED`, `MISALIGNED`, `INVALID`, or `REJECTED`. `BLOCKED` requires any required axis at `BLOCKED` after worse disputes or failures have been excluded. `VERIFICATION_CLOSED` requires every required-axis threshold. `COMPUTATIONALLY_REPRODUCED` requires the computation threshold for every load-bearing member. `SEMANTICALLY_RECONSTRUCTED` requires semantic-alignment and approximation thresholds. `MATH_CLOSED` requires `dependency_closure: COMPLETE`, mathematics and formal-alignment thresholds for the selected profile, and no intersecting open blocker. `PARTIALLY_VERIFIED` requires at least one above-untested required axis but failure of all stronger closure predicates. `DEPENDENCY_MAPPED` requires dependency closure `INCOMPLETE` or `COMPLETE`. `RELATION_VALIDATED` requires every required relation at `VALIDATED`. `SOURCE_VALIDATED` requires source fidelity `PASSED`; `SOURCE_GROUNDED` requires `PARTIAL` or `PASSED`; `PROPOSED` is the final fallback.

The following compact rule tables are the exhaustive pilot contents of the pinned artifacts. A row written `A → B` maps exact input `A` to contribution `B`; any unlisted evidence schema, method, result, blocker stage, profile, or predicate input fails derivation.

| Evidence schema and method | Exact result-to-axis mapping |
|---|---|
| `agtxiv.source-fidelity-evidence/1.0.0`, `source_audit` | `PASSED → source_fidelity:PASSED`; `PARTIAL → PARTIAL`; `MISALIGNED → MISALIGNED`; `BLOCKED → BLOCKED` |
| `agtxiv.candidate-relation/1.0.0` | record presence `→ relation_validation:CANDIDATE` |
| `agtxiv.relation-grounding-evidence/1.0.0` | `PASSED → relation_validation:SOURCE_GROUNDED`; `BLOCKED → BLOCKED` |
| `agtxiv.relation-validation/1.0.0` | `VALID → relation_validation:VALIDATED`; `INVALID → INVALID`; `WRONG_DIRECTION` or `WRONG_RELATION_TYPE → INVALID` |
| `agtxiv.relation-validation-result/1.0.0` | `BLOCKED` with `AMBIGUOUS` or `INSUFFICIENT_SOURCE_SUPPORT → relation_validation:BLOCKED`; `FAILED_TO_RUN` contributes no evidence |
| `agtxiv.closure-artifact/1.0.0` | fixed point with empty blocked frontier `→ dependency_closure:COMPLETE`; fixed point with unresolved required nodes `→ INCOMPLETE`; invalid or unavailable fixed point `→ BLOCKED`; disputed required edge `→ DISPUTED` |
| `agtxiv.verification-evidence/1.0.0`, `source_derivation_check` | `PASSED → mathematics:SOURCE_DERIVATION_CHECKED`; `FAILED → FAILED`; `BLOCKED → BLOCKED` |
| `agtxiv.formalization.lean4/1.0.0` | `SUCCEEDED → mathematics:PARTIALLY_FORMALIZED`; `BLOCKED → BLOCKED`; rejected or failed-to-run contributes no axis evidence |
| `agtxiv.verification-evidence/1.0.0`, `lean_kernel_build` | `PASSED → mathematics:KERNEL_CHECKED`; `FAILED → FAILED`; `BLOCKED → BLOCKED` |
| `agtxiv.backtranslation/1.0.0` | `SUCCEEDED → formal_alignment:BACKTRANSLATED`; `BLOCKED → BLOCKED`; rejected independence `→ MISALIGNED`; failed-to-run contributes no axis evidence |
| `agtxiv.alignment/1.0.0` | each observed result maps identically to `formal_alignment`; `FAILED_TO_RUN` contributes no evidence |
| `agtxiv.semantic-alignment-evidence/1.0.0` | `AGENT_REVIEWED`, `HUMAN_REVIEWED`, `CONTESTED`, `BLOCKED` map identically to `semantic_alignment` |
| `agtxiv.approximation-evidence/1.0.0` | `DECLARED_ONLY`, `PARTIALLY_CHECKED`, `CHECKED_IN_STATED_REGIME`, `FAILED`, `BLOCKED` map identically to `approximation_regime` |
| `agtxiv.semantic-evidence/1.0.0`, `empirical_support` | `SOURCE_GROUNDED`, `PARTIAL`, `SUPPORTED_IN_RECORDED_REGIME`, `CONTESTED`, `BLOCKED` map identically to `empirical_support` |
| `agtxiv.reproduction/1.1.0` | `REPRODUCED`, `REPRODUCED_WITH_TOLERANCE`, `QUALITATIVE_ONLY`, `FAILED` map identically to `computation`; `NOT_ATTEMPTED → NOT_ATTEMPTED`; blocked attempt `→ BLOCKED` |
| `agtxiv.human-review-evidence/1.0.0` | `PERFORMED`, `PARTIAL`, `NOT_PERFORMED`, `CONTESTED`, `REJECTED` map identically to `human_review` |

For multiple applicable contributions, the lowest value in the complete axis order is selected, except that a later evidence record supersedes an earlier record with the same logical ID only when the snapshot exposes a unique supersession head. Missing applicable evidence contributes the axis-specific untested value.

| Open blocker `stage` | Axis contribution |
|---|---|
| `source_preprocessing`, `source_alignment` | `source_fidelity:BLOCKED` |
| `relation_validation`, `relation_acceptance` | `relation_validation:BLOCKED` |
| `dependency_mapping`, `graph_build`, `closure_build` | `dependency_closure:BLOCKED` |
| `formalization`, `mathematical_verification` | `mathematics:BLOCKED` |
| `formal_alignment` | `formal_alignment:BLOCKED` |
| `semantic_alignment` | `semantic_alignment:BLOCKED` |
| `approximation_regime` | `approximation_regime:BLOCKED` |
| `empirical_support` | `empirical_support:BLOCKED` |
| `reproduction` | `computation:BLOCKED` |
| `human_review` | `human_review:CONTESTED` |

A blocker of type `DISPUTE` contributes the axis's `DISPUTED` or `CONTESTED` value instead of `BLOCKED`. A `RESOLVED` stream contributes nothing. Component and scope intersection uses exact TargetRef ancestry and RFC 6901 prefix matching; no textual matching is allowed.

| Acceptance profile | Required threshold rows | `MATH_CLOSED` predicate |
|---|---|---|
| `SOURCE_ONLY` | `source_fidelity ≥ PASSED`; `relation_validation ≥ VALIDATED` only when required by scope; `mathematics ≥ UNCHECKED`; `formal_alignment = NOT_APPLICABLE` | always `false`; strongest mathematical overall is `SOURCE_VALIDATED` |
| `DERIVATION_CHECKED` | `source_fidelity ≥ PASSED`; `dependency_closure ≥ COMPLETE`; `mathematics ≥ SOURCE_DERIVATION_CHECKED`; `formal_alignment = NOT_APPLICABLE` | true exactly when all thresholds hold and no required blocker/dispute/failure exists |
| `PARTIALLY_FORMALIZED` | `source_fidelity ≥ PASSED`; `mathematics ≥ PARTIALLY_FORMALIZED`; generated declarations require `formal_alignment ≥ BACKTRANSLATED`, otherwise `NOT_APPLICABLE` | always `false`; strongest mathematical overall is `PARTIALLY_VERIFIED` |
| `KERNEL_CHECKED_ALIGNED` | `source_fidelity ≥ PASSED`; `dependency_closure ≥ COMPLETE`; `mathematics ≥ KERNEL_CHECKED`; `formal_alignment ≥ AUTO_ALIGNMENT_PASSED` | true exactly when all thresholds hold and no required blocker/dispute/failure exists |

Semantic, empirical, computation, and human-review thresholds are added only when listed in `VerificationScope.required_axes`; their minimum is the profile-independent threshold stated by that scope. `VERIFICATION_CLOSED` is true exactly when every required axis meets its threshold. Overall predicates then use the fixed priority order above. Thus no profile can silently inherit a stronger `MATH_CLOSED` interpretation.

`DAG_COMPLETE` is not an overall status. It is the query property `dependency_closure: COMPLETE` at fixed-point closure.

Policy selection always pins ID, revision, and hash. A superseded policy may replay an old receipt but cannot produce a new view unless historical replay is explicit. Missing evidence contributes the axis's untested value (`UNCHECKED`, `UNMODELED`, `NOT_ATTEMPTED`, `DECLARED_ONLY`, or `NOT_PERFORMED` as specified by applicability). Forks, cycles, unknown vocabularies, unmapped evidence, invalid hashes, and non-total precedence fail derivation.

```yaml
status_derivation_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.status-derivation-request/1.0.0
  applies_to: <TargetRef>
  policy:
    id: status-policy:default
    record_revision: 1
    content_hash: sha256:...
  required_scope:
    id: verification-scope:math-import
    revision: 1
    content_hash: sha256:...
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  composite_registry_snapshot:
    id: composite-snapshot:registry-boundary-17
    record_revision: 1
    content_hash: sha256:...
  evidence_snapshot:
    id: evidence-index:snapshot-7
    record_revision: 1
    content_hash: sha256:...
  blocker_snapshot:
    id: blocker-index:snapshot-4
    record_revision: 1
    content_hash: sha256:...
```

```yaml
status_derivation_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.status-derivation-result/1.0.0
  applies_to: <same TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  status_view: null
```

`SUCCEEDED` requires an immutable view with this full shape:

```yaml
status_view:
  schema: agtxiv.status-view/1.0.0
  id: status-view:...
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <exact request TargetRef>
  policy: {id: status-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  required_scope: {id: verification-scope:math-import, revision: 1, content_hash: 'sha256:...'}
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  evidence_snapshot: {id: evidence-index:snapshot-7, record_revision: 1, content_hash: 'sha256:...'}
  blocker_snapshot: {id: blocker-index:snapshot-4, record_revision: 1, content_hash: 'sha256:...'}
  axes:
    source_fidelity:
      value: PASSED
      evidence_derivation_refs: []
      blocker_derivation_refs: []
    dependency_closure:
      value: COMPLETE
      evidence_derivation_refs: []
      blocker_derivation_refs: []
    mathematics:
      value: KERNEL_CHECKED
      evidence_derivation_refs: []
      blocker_derivation_refs: []
    formal_alignment:
      value: AUTO_ALIGNMENT_PASSED
      evidence_derivation_refs: []
      blocker_derivation_refs: []
  overall: MATH_CLOSED
  overall_derivation_ref: status-derivation:overall:...
  producer:
    implementation: status-deriver
    version: 1.0.0
    implementation_hash: sha256:...
  content_hash: sha256:...
```

The request and view `acceptance_profile` must equal `VerificationScope.acceptance_profile`. Both index snapshots must declare the exact same `composite_registry_snapshot`; mismatch is `REJECTED`. Every applicable axis is mandatory; omitted axes are a schema error. `REJECTED` means invalid policy/scope/target combination. `BLOCKED` means snapshots are internally invalid or rule tables cannot resolve uniquely. `FAILED_TO_RUN` emits no view. Partial aggregate output is forbidden.

#### 5.1.14 Import acceptance

```yaml
import_acceptance_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.import-acceptance-request/1.0.0
  applies_to: <exact ClaimContract TargetRef including governing ClaimIR>
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  consumer:
    id: agent:intermediate-paper
    manifest_revision: 1
    manifest_content_hash: sha256:...
  proposed_status_view:
    id: status-view:root-paper:theorem-T:...
    record_revision: 1
    content_hash: sha256:...
  required_scope:
    id: verification-scope:math-import
    revision: 1
    content_hash: sha256:...
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  policy:
    id: status-policy:default
    record_revision: 1
    content_hash: sha256:...
  evidence_snapshot: {id: evidence-index:snapshot-7, record_revision: 1, content_hash: 'sha256:...'}
  blocker_snapshot: {id: blocker-index:snapshot-4, record_revision: 1, content_hash: 'sha256:...'}
  assumption_matches: []
  object_mappings: []
  convention_mappings: []
```

```yaml
import_acceptance_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.import-acceptance-result/1.0.0
  applies_to: <same exact ClaimContract TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  decision: ACCEPTED | CONDITIONAL | REJECTED | null
  claim_import_receipt: null
  unmet_requirements: []
```

`SUCCEEDED` requires `decision: ACCEPTED | CONDITIONAL` and an immutable `ClaimImportReceipt`. `CONDITIONAL` requires explicit conditions; `ACCEPTED` requires none. `REJECTED` uses `decision: REJECTED`, lists incompatible scope, assumptions, objects, or policy, and emits no receipt. `BLOCKED` means evidence, blocker state, or mappings are unresolved and also emits no receipt. `FAILED_TO_RUN` has `decision: null` and no receipt.

```yaml
claim_import_receipt:
  schema: agtxiv.claim-import-receipt/1.0.0
  id: import-receipt:intermediate-paper:theorem-T
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <same exact ClaimContract TargetRef>
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  consumer: agent:intermediate-paper
  decision: ACCEPTED | CONDITIONAL
  accepted_status_view: {id: status-view:..., record_revision: 1, content_hash: 'sha256:...'}
  required_scope: {id: verification-scope:math-import, revision: 1, content_hash: 'sha256:...'}
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  policy: {id: status-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  evidence_snapshot: {id: evidence-index:snapshot-7, record_revision: 1, content_hash: 'sha256:...'}
  blocker_snapshot: {id: blocker-index:snapshot-4, record_revision: 1, content_hash: 'sha256:...'}
  assumption_matches: []
  object_mappings: []
  convention_mappings: []
  conditions: []
  producer:
    implementation: import-acceptance-service
    version: 1.0.0
    implementation_hash: sha256:...
  content_hash: sha256:...
```

The receipt scope must be a policy-proved superset of both `MathContract.required_verification_scope` and `ClaimContract.required_verification.scope`. The status view must have exactly the receipt target, scope, acceptance profile, policy, composite snapshot, and derived evidence/blocker snapshots. Receipts are consumer-side external records discovered through indexes; providers and immutable contracts never point outward to later receipts.

#### 5.1.15 Normative invariants

1. `MathClaimIR` records only what an immutable source mathematically asserts.
2. Source occurrence remains stable; intellectual attribution is an external `AttributionRecord`.
3. Every core and external record revision is immutable and content-addressed.
4. Every target-bearing request and record uses the canonical `TargetRef`; exact ClaimIR ID, revision, and `semantic_content_hash` are mandatory whenever a ClaimIR exists.
5. Preprocessing and pre-ClaimIR failures use `claim_ir: null`; no ClaimIR is fabricated.
6. Formalizations, backtranslations, evidence, alignments, blockers, index snapshots, status views, and receipts are independently versioned external records.
7. Backtranslation points inward and is never embedded in a formalization.
8. Generated code is not checked evidence; checked proof is not source alignment.
9. Status is deterministic policy output over exact evidence and blocker snapshots.
10. Blocker resolution, correction, and supersession create new revisions or events, never in-place updates.
11. Meaning-preserving migration preserves canonical semantic hash and semantic revision while assigning a new serialization artifact hash.
12. No migration, verifier, attribution process, or status policy may silently modify source meaning.

### 5.2 MathContract

A `MathContract` is the smallest reusable mathematical interface. It is immutable and packages dependency and compatibility requirements around one exact ClaimIR or MathematicalPropositionIR revision; it contains no formalization, evidence, blocker, or aggregate status field.

```yaml
schema: agtxiv.math-contract/1.0.0
id: math-contract:domain:result
record_revision: 1
supersedes: null
produced_at: 2026-08-18T00:00:00Z
applies_to: <exact ClaimIR or MathematicalPropositionIR TargetRef>
statement_interface:
  kind: theorem
  assumptions:
    - math-contract:domain:A@1
  imports:
    definitions: []
    theorems: []
source_manifestations:
  - work_id: work:stable-id
    source_version_id: arxiv:...vN
    anchor: anchor:paper:theorem
compatibility:
  policy: math-contract-compatibility/1.0.0
  breaking_fields: [conclusion, quantifiers, assumptions, conventions]
required_verification_scope:
  id: verification-scope:math-contract
  revision: 1
  content_hash: sha256:...
  acceptance_profile: KERNEL_CHECKED_ALIGNED
content_hash: sha256:...
```

External records are discovered through registries. A contract revision changes only when its interface, dependency requirements, compatibility policy, or required scope changes. Different papers may point to the same contract, but similarity search may only propose identity or specialization relations.

### 5.3 SourceAnchor

A stable location in an immutable source artifact.

```yaml
schema: agtxiv.source-anchor/1.1.0
id: anchor:paper-id:theorem-2
record_revision: 1
supersedes: null
produced_at: 2026-08-26T00:00:00Z
work_id: work:stable-id
source_version_id: arxiv:xxxx.xxxxxv2
artifact: main.tex
artifact_hash: sha256:...
location:
  section: "3.1"
  line_start: 412
  line_end: 430
  label: thm:main
content_hash: sha256:...
```

When only a PDF is available:

```yaml
schema: agtxiv.source-anchor/1.1.0
id: anchor:paper-id:pdf-p7-eq12
record_revision: 1
supersedes: null
produced_at: 2026-08-26T00:00:00Z
work_id: work:stable-id
source_version_id: doi:...
artifact: paper.pdf
artifact_hash: sha256:...
location:
  page: 7
  equation: "12"
  bounding_box: [72, 214, 518, 296]
content_hash: sha256:...
```

Legacy `agtxiv.source-anchor/1.0.0` records whose `paper_id` is an exact version remain valid. New `1.1.0` anchors separate stable `work_id` from exact `source_version_id`; this schema migration does not permit reusing an anchor across source versions.

### 5.4 Candidate and accepted relations

A candidate relation is an immutable proposal. It contains source anchors and extractor provenance, but no reverse link to later validation evidence.

```yaml
candidate_relation:
  schema: agtxiv.candidate-relation/1.0.0
  id: relation-candidate:paper-A:C3--paper-B:T2
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  source_target: <TargetRef for dependent claim C3>
  target_target: <TargetRef for imported claim T2>
  relation_type: imports_theorem
  source_anchors: [anchor:paper-A:citation-context, anchor:paper-A:local-derivation]
  extractor:
    implementation: ...
    version: ...
    implementation_hash: sha256:...
  extractor_confidence: 0.82
  content_hash: sha256:...
```

```yaml
relation_validation_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.relation-validation-request/1.0.0
  applies_to: <exact CandidateRelation TargetRef with governing ClaimIR members>
  validation_policy: {id: relation-validation-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  source_context_artifacts: []
```

```yaml
relation_validation_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.relation-validation-result/1.0.0
  applies_to: <same CandidateRelation TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  verdict: VALID | INVALID | AMBIGUOUS | WRONG_DIRECTION | WRONG_RELATION_TYPE | INSUFFICIENT_SOURCE_SUPPORT | null
  validation_record: null
```

`SUCCEEDED` requires a validation record and `VALID`, `INVALID`, `WRONG_DIRECTION`, or `WRONG_RELATION_TYPE`. `BLOCKED` uses `AMBIGUOUS` or `INSUFFICIENT_SOURCE_SUPPORT`. Invalid request structure is `REJECTED` with no scientific verdict; execution failure has `verdict: null`.

```yaml
relation_acceptance_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.relation-acceptance-request/1.0.0
  applies_to: <exact CandidateRelation TargetRef>
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  validation_record: {id: relation-validation:..., record_revision: 1, content_hash: 'sha256:...'}
  acceptance_policy: {id: relation-acceptance-policy:dependency/1.0.0, record_revision: 1, content_hash: 'sha256:...'}
  required_scope: {id: relation-scope:query-build, revision: 1, content_hash: 'sha256:...'}
```

```yaml
relation_acceptance_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.relation-acceptance-result/1.0.0
  applies_to: <same CandidateRelation TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  accepted_relation: null
```

On successful validation, `validation_record` has the following immutable shape:

```yaml
relation_validation_record:
  schema: agtxiv.relation-validation/1.0.0
  id: relation-validation:...
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <exact CandidateRelation TargetRef>
  validation_policy: {id: relation-validation-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  verdict: VALID | INVALID | WRONG_DIRECTION | WRONG_RELATION_TYPE
  findings: []
  content_hash: sha256:...
```

On successful acceptance, `accepted_relation` has this authoritative shape:

```yaml
accepted_relation:
  schema: agtxiv.accepted-relation/1.0.0
  id: relation:paper-A:C3--paper-B:T2
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  candidate_ref: {id: relation-candidate:paper-A:C3--paper-B:T2, record_revision: 1, content_hash: 'sha256:...'}
  source_target: <exact dependent TargetRef>
  target_target: <exact dependency TargetRef>
  relation_type: imports_theorem
  direction: SOURCE_DEPENDS_ON_TARGET
  accepted_scope: {id: relation-scope:query-build, revision: 1, content_hash: 'sha256:...'}
  acceptance_policy: {id: relation-acceptance-policy:dependency/1.0.0, record_revision: 1, content_hash: 'sha256:...'}
  content_hash: sha256:...
```

`SUCCEEDED` requires this accepted relation. `REJECTED` records an invalid or policy-ineligible candidate and emits no accepted relation. `BLOCKED` records ambiguous or insufficient validation and emits none. `FAILED_TO_RUN` has no promotion decision. The provisional candidate graph contains candidate relations only; accepted dependency DAGs contain accepted relations only. No model confidence or validation record alone promotes an edge.

### 5.5 InferenceStep

An `InferenceStep` is an immutable first-class graph node for one inspectable transformation from joint inputs to outputs.

```yaml
schema: agtxiv.inference-step/1.0.0
id: inference:paper-id:017
record_revision: 1
supersedes: null
produced_at: 2026-08-18T00:00:00Z
inputs:
  - <TargetRef for equation eq-7>
  - <TargetRef for assumption weak-coupling>
outputs:
  - <TargetRef for equation eq-8>
operation: approximation
justification:
  description: Expand to second order in lambda and discard order lambda cubed.
  retained_order: 2
  discarded_order_latex: O(\lambda^3)
active_assumptions: [assumption:small-lambda]
validity_regime_latex: ['$|\lambda|\ll 1$']
source_anchors: [anchor:paper-id:eq7-to-eq8]
content_hash: sha256:...
```

Formal links, checks, blockers, and status views target the exact inference-step revision through `TargetRef` and do not mutate it. Initial operations are `definition_expansion`, `algebra`, `substitution`, `logical_inference`, `theorem_application`, `citation_import`, `approximation`, `limit`, `symmetry_or_conservation`, `dimensional_argument`, `numerical_evaluation`, `physical_interpretation`, and `unresolved`.

### 5.6 VerificationEvidenceRecord

The sole normative schema and operation are `agtxiv.verification-request/1.0.0` and the result-envelope-derived `agtxiv.verification-evidence/1.0.0` in Section 5.1.10. No alternate `COMPLETED` outcome or legacy record shape is valid.

### 5.7 SemanticContract

A `SemanticContract` is immutable source-grounded semantic content. It contains no observations, evidence links, blockers, or statuses.

```yaml
semantic_contract:
  schema: agtxiv.semantic-contract/1.0.0
  id: semantic-contract:paper-id:claim-C
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <exact ScientificClaim TargetRef with governing ClaimIR when present>
  source_anchors: [anchor:paper-id:claim-C]
  physical_system:
    degrees_of_freedom: []
    preparation: ...
    observable: ...
    parameter_regime: ...
  object_alignment:
    paper_object: ...
    mathematical_object: ...
    operational_definition: ...
  assumptions:
    - component_id: semantic-assumption:weak-coupling
      statement: ...
      regime: ...
  approximations:
    - component_id: semantic-regime:perturbative
      method: perturbation
      control_parameter: lambda
      retained_order: 2
      discarded_order_latex: O(\lambda^3)
  conclusion:
    component_id: semantic-conclusion:claim-C
    statement: ...
  conventions: []
  content_hash: sha256:...
```

Evidence targets the exact contract revision and component JSON Pointer through `org.agtxiv.semantic_contract.component`. Assumptions, regimes, and conclusions therefore receive evidence independently without a reverse link from the contract.

### 5.8 EvidenceRecord

An `EvidenceRecord` is an immutable scoped observation attached through `TargetRef` to a semantic assumption, regime, or conclusion.

```yaml
schema: agtxiv.semantic-evidence/1.0.0
id: evidence:experiment-1
record_revision: 1
supersedes: null
produced_at: 2026-08-18T00:00:00Z
applies_to: <exact org.agtxiv.semantic_contract.component TargetRef for /assumptions/0>
source_anchors: [anchor:experiment-paper:figure-3]
evidence_type: experiment
system_or_sample: ...
protocol: ...
observable: ...
parameter_regime: ...
uncertainty_model: ...
reported_result: ...
relation: supports_under_conditions
support_scope: Supports the approximation only for the measured parameter window.
content_hash: sha256:...
```

Evidence does not automatically prove a theorem or validate an approximation outside its recorded regime.

### 5.9 ReproductionRecord

A `ReproductionRecord` is an immutable computational evidence record.

```yaml
schema: agtxiv.reproduction/1.1.0
id: reproduction:paper-id:result-R
record_revision: 1
supersedes: null
produced_at: 2026-08-26T00:00:00Z
applies_to: <exact ScientificClaim TargetRef, with claim_ir when one exists>
repository_state:
  work_repository_binding_ref: <exact WorkRepositoryBinding TargetRef>
  target_commit_oid: <full Git commit object ID>
  target_tree_oid: <full Git tree object ID>
role: LOAD_BEARING
layers:
  source:
    implementation_kind: AUTHORITATIVE | INDEPENDENT
    artifacts: [{commit_path: reproduction/code/..., artifact_hash: 'sha256:...'}]
  data:
    artifacts: [{commit_path_or_immutable_locator: reproduction/data/..., artifact_hash: 'sha256:...'}]
  environment:
    artifacts: [{commit_path: reproduction/environment/..., artifact_hash: 'sha256:...'}]
    environment_hash: sha256:...
  execution:
    workflow_path: reproduction/workflows/reproduce.yaml
    workflow_hash: sha256:...
    command: ...
    parameters: {}
    random_seed: ...
    execution_input_hash: sha256:...
  output:
    reported_output: ...
    reproduced_output: ...
    tolerance: ...
    artifacts: [{commit_path: reproduction/outputs/..., artifact_hash: 'sha256:...'}]
  evidence:
    comparison_artifact: {commit_path: reproduction/outputs/comparison.json, artifact_hash: 'sha256:...'}
    log_artifacts: [{commit_path: reproduction/logs/..., artifact_hash: 'sha256:...'}]
    blocker_refs: []
attempt_state: COMPLETED | BLOCKED | FAILED_TO_RUN | NOT_ATTEMPTED
observed_result: REPRODUCED | REPRODUCED_WITH_TOLERANCE | QUALITATIVE_ONLY | FAILED | null
content_hash: sha256:...
```

The observed result is evidence input, not aggregate claim status. Every non-null path resolves against `repository_state.target_commit_oid`, and every consumed or produced artifact has an independent hash. `repository_state` deliberately omits the later `ReleaseManifest`; the certification transaction binds this already-hashed record to the public release without creating a forward-reference cycle. `execution_input_hash` binds the exact source, data, environment, workflow, parameters, and seed; evidence and outputs therefore cannot be silently mixed across runs. `BLOCKED` requires at least one exact blocker reference and a null `observed_result`. The record has no mandatory internal DAG and no Lean requirement.

### 5.10 LeanPackageCapabilityRecord

A capability record is immutable package metadata used for routing; it contains no mutable trust or build observation.

```yaml
lean_package_capability_record:
  schema: agtxiv.lean-package-capability/1.0.0
  id: lean-capability:quantum-information-finite
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  package:
    repository: ...
    commit: ...
    lean_toolchain: ...
    build_targets: [QuantumInfo]
  field_tags: [quantum_information, finite_dimensional_quantum_mechanics]
  object_coverage: [density_operator, quantum_channel, measurement, entropy, resource_theory]
  declaration_index:
    artifact_ref: registry/declarations.jsonl
    artifact_hash: sha256:...
  compatibility:
    mathlib_commit: ...
    tested_imports: []
  known_gaps: []
  content_hash: sha256:...
```

Build, placeholder, axiom, maintenance, and review observations are immutable `VerificationEvidenceRecord` objects targeting the exact package-capability revision. Trust tiers are policy-derived status-view values, never fields updated inside the capability record. Field classification remains a routing prior; exact declaration matching is required.

### 5.11 Graph artifacts, closures, CompanionBundles, and repairs

```yaml
dependency_node_manifest:
  schema: agtxiv.dependency-node-manifest/1.0.0
  id: dependency-node-manifest:resolution-id
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  nodes:
    - target: <TargetRef>
      node_role: ROOT | INTERNAL | EXTERNAL_FOUNDATION
  ordering_rule: canonical_target_ref_bytes
  content_hash: sha256:...
```

Nodes are sorted by canonical TargetRef bytes and duplicate target identities are rejected.

```yaml
graph_build_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.graph-build-request/1.0.0
  applies_to: <exact query-resolution or target TargetRef>
  graph_kind: org.agtxiv.math_claim_dependency_dag
  root_set: [<canonically ordered TargetRef values>]
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  accepted_relation_snapshot: {id: relation-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
  node_manifest: {id: dependency-node-manifest:..., record_revision: 1, content_hash: 'sha256:...'}
  import_receipt_snapshot: {id: import-receipt-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
  blocker_snapshot: {id: blocker-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
  build_policy: {id: graph-build-policy:math-dag/1.0.0, record_revision: 1, content_hash: 'sha256:...'}
  algorithm:
    id: agtxiv.reverse-dependency-fixed-point/1.0.0
    content_hash: sha256:...
    traversal_order: canonical_breadth_first
    relation_admission: accepted_relation_only
    revisit_rule: never_after_canonical_identity_seen
    termination: no_new_nodes_or_relations
```

```yaml
graph_build_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.graph-build-result/1.0.0
  applies_to: <same TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  graph_artifact: null
  closure_artifact: null
```

`SUCCEEDED` publishes immutable `GraphArtifact` and `ClosureArtifact`. `REJECTED` identifies invalid edge types, direction, or target. `BLOCKED` identifies a cycle in the mathematical dependency view, unresolved endpoint, or invalid relation snapshot. `FAILED_TO_RUN` publishes no graph. Companion bundles and the paper projection are produced only by the `PaperBuildDAG` interface below.

```yaml
graph_artifact:
  schema: agtxiv.graph-artifact/1.0.0
  id: graph:resolution-id:math-dag
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <same TargetRef>
  graph_kind: org.agtxiv.math_claim_dependency_dag
  build_request_hash: sha256:...
  build_input_manifest_hash: sha256:...
  algorithm: {id: agtxiv.reverse-dependency-fixed-point/1.0.0, content_hash: 'sha256:...'}
  nodes: [<canonically ordered TargetRef values>]
  edges: [<canonically ordered accepted-relation TargetRef values>]
  ordering_rule: canonical_encoded_bytes/1.0.0
  graph_hash: sha256:...
  content_hash: sha256:...
```

```yaml
closure_artifact:
  schema: agtxiv.closure-artifact/1.0.0
  id: closure:resolution-id:required-math
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <same TargetRef>
  graph_ref: {id: graph:resolution-id:math-dag, record_revision: 1, content_hash: 'sha256:...'}
  inputs:
    root_set: [<same ordered TargetRef values>]
    composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
    accepted_relation_snapshot: {id: relation-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
    node_manifest: {id: dependency-node-manifest:..., record_revision: 1, content_hash: 'sha256:...'}
    import_receipt_snapshot: {id: import-receipt-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
    blocker_snapshot: {id: blocker-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
    build_policy: {id: graph-build-policy:math-dag/1.0.0, record_revision: 1, content_hash: 'sha256:...'}
    algorithm: {id: agtxiv.reverse-dependency-fixed-point/1.0.0, content_hash: 'sha256:...'}
  nodes:
    - target: <TargetRef>
      classification: ACCEPTED | CONDITIONAL | BLOCKED
      basis_refs: []
  relations:
    - relation: <AcceptedRelation TargetRef>
      classification: ACCEPTED | CONDITIONAL | BLOCKED
      basis_refs: []
  blocked_frontier: [<canonically ordered TargetRef values>]
  fixed_point:
    reached: true
    iterations: 0
    invariant_hash: sha256:...
  content_hash: sha256:...
```

`root_set`, nodes, relations, basis references, and blocked frontier are set-valued arrays sorted by canonical encoded TargetRef or record-reference bytes with duplicates rejected. Starting from the ordered roots, each iteration admits only accepted relations visible in the pinned relation snapshot, resolves imports only through receipts visible in the pinned receipt snapshot, applies blockers from the pinned blocker snapshot, and adds newly reached dependency endpoints in canonical order. `ACCEPTED` means every required import has an accepted receipt and no intersecting open blocker; `CONDITIONAL` means every unresolved requirement is covered by a conditional receipt; otherwise the element is `BLOCKED`. The fixed-point invariant is that another complete traversal over all admitted outgoing dependency relations adds no node, relation, receipt condition, or blocker classification. `invariant_hash` hashes the canonical final frontier and classification map. Any input snapshot not derived from the exact composite snapshot is rejected.

The paper-level projection uses a separate normative operation. Its mapping snapshot fixes the PaperAgent owner of every claim-DAG node:

```yaml
claim_to_paper_agent_mapping_snapshot:
  schema: agtxiv.claim-to-paper-agent-mapping-snapshot/1.0.0
  id: claim-paper-mapping:registry-boundary-17
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  mappings:
    - claim_target: <exact claim-DAG node TargetRef>
      paper_agent_target: <exact PaperAgentManifest TargetRef>
      mapping_basis_ref: <exact source-occurrence, proposition-owner, or policy record ref>
  ordering_rule: canonical_claim_then_paper_target_ref_bytes
  content_hash: sha256:...
```

Mappings are sorted by `(canonical(claim_target), canonical(paper_agent_target))`. Here ownership means the exact release/build unit that packages the node for this query, not intellectual priority or historical authorship. Every claim-DAG node has exactly one visible mapping; the mapped manifest must have one unambiguous publication-release binding visible through the pinned release manifest and composite snapshot. Duplicates, omissions, forks, floating PaperAgent heads, cross-snapshot mappings, and invented paper ownership for source-independent shared contracts are invalid.

```yaml
paper_build_dag_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.paper-build-dag-request/1.0.0
  applies_to: <exact query-resolution TargetRef>
  math_claim_dependency_dag:
    id: graph:resolution-id:math-dag
    record_revision: 1
    content_hash: sha256:...
    graph_hash: sha256:...
  claim_to_paper_agent_mapping_snapshot: {id: claim-paper-mapping:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  projection_policy: {id: paper-projection-policy:default, record_revision: 1, content_hash: 'sha256:...'}
  scc_algorithm:
    id: agtxiv.deterministic-paper-scc-condensation/1.0.0
    content_hash: sha256:...
    projected_node_order: canonical_paper_agent_target_ref_bytes
    adjacency_order: canonical_projected_edge_bytes
    scc_method: tarjan_depth_first
    component_member_order: canonical_paper_agent_target_ref_bytes
    component_order: canonical_component_member_sequence_bytes
    condensation_edge_order: canonical_component_pair_bytes
    topological_order: kahn_lexicographically_minimal
```

```yaml
paper_build_dag_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.paper-build-dag-result/1.0.0
  applies_to: <same query-resolution TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  paper_build_dag_artifact: null
  companion_bundles: []
```

```yaml
paper_build_dag_artifact:
  schema: agtxiv.paper-build-dag-artifact/1.0.0
  id: graph:resolution-id:paper-build-dag
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <same query-resolution TargetRef>
  inputs:
    math_claim_dependency_dag:
      id: graph:resolution-id:math-dag
      record_revision: 1
      content_hash: sha256:...
      graph_hash: sha256:...
    claim_to_paper_agent_mapping_snapshot: {id: claim-paper-mapping:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
    composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
    projection_policy: {id: paper-projection-policy:default, record_revision: 1, content_hash: 'sha256:...'}
    scc_algorithm: {id: agtxiv.deterministic-paper-scc-condensation/1.0.0, content_hash: 'sha256:...'}
  projected_paper_nodes: [<canonically ordered exact PaperAgentManifest TargetRefs>]
  projected_edges:
    - from_paper_agent: <exact PaperAgentManifest TargetRef>
      to_paper_agent: <exact PaperAgentManifest TargetRef>
      witness_claim_edges: [<canonically ordered exact claim-edge TargetRefs>]
  companion_bundle_refs: []
  condensation_nodes: [<canonically ordered exact singleton PaperAgent or CompanionBundle TargetRefs>]
  condensation_edges:
    - from_component: <exact singleton PaperAgent or CompanionBundle TargetRef>
      to_component: <exact singleton PaperAgent or CompanionBundle TargetRef>
      witness_projected_edge_hashes: [<canonically ordered hashes>]
  canonical_topological_order: [<exact singleton PaperAgent or CompanionBundle TargetRefs>]
  projection_graph_hash: sha256:...
  condensation_graph_hash: sha256:...
  build_input_hash: sha256:...
  content_hash: sha256:...
```

The projection visits claim-DAG nodes and edges in their canonical artifact order, replaces every claim endpoint with its mapped `PaperAgentManifest` target, drops no witness, and coalesces equal ordered manifest-target pairs while retaining the sorted exact claim-edge witnesses. The pinned projection policy determines whether claim edges within one PaperAgent manifest are retained only as internal witnesses; they never become condensation self-edges.

The SCC algorithm starts Tarjan depth-first searches in `projected_node_order` and visits adjacency lists in `adjacency_order`. Members of each SCC are sorted canonically; SCCs are ordered by their complete canonical member sequences. A multi-agent SCC produces one immutable `CompanionBundle`; a singleton remains its exact `PaperAgentManifest` target. Component identity is the SHA-256 hash of the ordered member-target sequence and pinned inputs. For every projected edge whose endpoints belong to different components, the condensation contains exactly one directed component pair with all witness projected-edge hashes sorted and deduplicated. Internal edges occur only in the corresponding bundle. Condensation edges are sorted by their endpoint component sequences. Kahn's algorithm selects the canonically smallest zero-indegree component at each step, yielding `canonical_topological_order`. A remaining cycle is an invariant failure.

`build_input_hash` hashes the complete canonical `inputs` map, and the two graph hashes cover their respective canonically ordered nodes, edges, and witnesses. `content_hash` covers the complete immutable artifact with itself omitted. The result must echo request inputs exactly through the artifact. `SUCCEEDED` requires a complete mapping, all required bundles, an acyclic condensation, and matching hashes. Invalid graph kind, projection policy, duplicate mapping, or cross-snapshot input is `REJECTED`; a missing mapping, unresolved exact ref, fork, or unavailable input is `BLOCKED`; `FAILED_TO_RUN` emits no artifact or bundle. Publication is atomic, so no bundle or paper DAG is visible alone.

```yaml
companion_bundle:
  schema: agtxiv.companion-bundle/1.0.0
  id: bundle:resolution-id:1
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  applies_to: <multi-ClaimIR query-resolution TargetRef>
  paper_build_request_hash: sha256:...
  paper_agent_targets: [<canonically ordered exact PaperAgentManifest TargetRefs>]
  internal_claim_relations: [<canonically ordered exact claim-edge TargetRefs>]
  external_imports: [<canonically ordered exact incoming projected-edge refs>]
  external_exports: [<canonically ordered exact outgoing projected-edge refs>]
  component_identity_hash: sha256:...
  component_graph_hash: sha256:...
  content_hash: sha256:...
```

```yaml
graph_repair_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.graph-repair-request/1.0.0
  applies_to: <exact GraphArtifact TargetRef>
  expected_graph_revision: 1
  expected_graph_content_hash: sha256:...
  operation: EXPAND_LOCAL | REWIRE_OR_RESCOPE | ESCALATE_OR_BLOCK
  actions: []
```

```yaml
graph_repair_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.graph-repair-result/1.0.0
  applies_to: <same GraphArtifact TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  repaired_graph: null
  graph_repair_record: null
```

Success atomically publishes a superseding graph and immutable repair transaction with before/after hashes. Stale expected revision is `BLOCKED`; invalid action or DAG invariant violation is `REJECTED`; execution failure publishes neither.

### 5.12 ClaimContract

A `ClaimContract` is an immutable export interface. It pins ClaimIR and `MathContract` revisions and declares import requirements; it contains no aggregate status.

```yaml
schema: agtxiv.claim-contract/1.0.0
id: export:root-agent:theorem-T
record_revision: 1
supersedes: null
produced_at: 2026-08-18T00:00:00Z
provider_agent: agent:root-paper
claim: claim:root-paper:theorem-T@1
math_contract: math-contract:root-paper:theorem-T@1
applies_to: <exact ClaimIR or MathematicalPropositionIR TargetRef>
assumptions: [assumption:finite-dimensional-space, assumption:positivity]
validity_regime: []
required_verification:
  scope:
    id: verification-scope:math-import
    revision: 1
    content_hash: sha256:...
    acceptance_profile: KERNEL_CHECKED_ALIGNED
  policy:
    id: status-policy:math-claim
    record_revision: 1
    content_hash: sha256:...
provenance:
  source_anchors: [anchor:root-paper:theorem-T]
content_hash: sha256:...
```

Import acceptance is performed by the external interface in Section 5.1.14. The immutable provider contract never points to consumer receipts, later evidence, blockers, or status views.

### 5.13 PaperAgentManifest

A published Agent manifest is immutable and holds exact registry references plus local staging or audit artifact hashes.

```yaml
schema: agtxiv.paper-agent-manifest/1.1.0
id: agent-manifest:work-slug
record_revision: 1
supersedes: null
produced_at: 2026-08-26T00:00:00Z
agent:
  id: agent:work-slug
  work_id: work:stable-id
  roles: [root, intermediate, target]
work_repository_binding_ref: <exact WorkRepositoryBinding TargetRef>
source_occurrence:
  source_version_id: arxiv:xxxx.xxxxxv2
  source_manifest_payload:
    commit_path: source/manifest.json
    type_schema: agtxiv.paper-source/0.2
    artifact_hash: sha256:...
  canonical_source_artifact_hash: sha256:...
paper_graph_refs: []
local_delta:
  scientific_claim_refs: []
  claim_ir_refs:
    - id: math-claim-ir:work-slug:claim-C
      revision: 1
      semantic_content_hash: sha256:...
  inference_step_refs: []
staging_and_audit_artifacts:
  normalization_attempts: agtxiv/staging/normalization/
  formalization_payloads: formal/
  backtranslation_payloads: agtxiv/audit/backtranslations/
  evidence_payloads: agtxiv/audit/evidence/
content_hash: sha256:...
```

---

## 6. Verification Semantics

### 6.1 Claim origin

Every `ScientificClaim` has exactly one origin class:

```text
SOURCE_OCCURRENCE
DERIVED_CLAIM
SOURCE_INDEPENDENT_PROPOSITION
```

`SOURCE_OCCURRENCE` requires a frozen source and anchors, with `assertion_mode: SOURCE_EXPLICIT | SOURCE_IMPLICIT | CITATION_REPORTED`. `DERIVED_CLAIM` requires exact premise and inference-step TargetRefs and must not inherit source-explicit status. `SOURCE_INDEPENDENT_PROPOSITION` identifies mathematics introduced independently of a frozen paper occurrence, for example a new helper lemma or package theorem. Computational reproduction, autoformalization, and human interpretation are evidence or production methods, never origin classes.

A paper-derived mathematical statement uses `MathClaimIR`, whose `source` field is mandatory. A source-independent proposition must not fabricate that field. It uses the structurally parallel `MathematicalPropositionIR`:

```yaml
mathematical_proposition_ir:
  schema: agtxiv.mathematical-proposition-ir/1.0.0
  id: mathematical-proposition-ir:domain:helper-lemma
  revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  scientific_claim:
    id: claim:domain:helper-lemma
    record_revision: 1
    content_hash: sha256:...
  origin: SOURCE_INDEPENDENT_PROPOSITION
  statement_kind: lemma
  normalized_statement_expanded_latex: ...
  structured_statement: {}
  semantic_content_hash: sha256:...
  artifact:
    schema_uri: https://agtxiv.org/schema/mathematical-proposition-ir/1.0.0
    schema_version: 1.0.0
    serialization_profile:
      id: agtxiv.canonical-yaml/1.0.0
      content_hash: sha256:...
    artifact_hash: sha256:...
```

It uses `agtxiv.proposition-semantic-canonical/1.0.0`, which reuses the ClaimIR encoding and mathematical field rules but omits source-occurrence and anchor fields from both input and hash. It is a distinct namespaced target kind and never populates `claim_ir`. Formalization, evidence, contracts, and status views may target it directly. If a later frozen source occurrence is discovered, the system creates a separate ClaimIR and an external relation; it does not relabel the proposition in place.

### 6.2 Candidate and accepted relations

AgtXIv distinguishes:

```text
CANDIDATE_RELATION
SOURCE_GROUNDED_RELATION
VALIDATED_RELATION
ACCEPTED_DEPENDENCY
REJECTED_RELATION
DISPUTED_RELATION
```

Only `ACCEPTED_DEPENDENCY` edges enter the accepted mathematical build DAG. Conditional edges may enter a conditional closure when their unresolved assumptions are public and propagated downstream.

A bibliography edge alone is not a claim dependency. A similarity score alone is not theorem identity. A compiled Lean theorem alone is not source alignment.

### 6.3 Unresolved External Mathematical Source

An `Unresolved External Mathematical Source` is a mathematical claim required by a target closure that has neither a verified source manifestation nor a completed independent Lean proof.

Every such claim follows one of three paths:

1. **Source found and verified.** Freeze an authoritative source version, record an exact anchor, match the normalized statement and hypotheses, and check the cited derivation to the level required by the contract.
2. **Independent Lean proof completed.** State the claim precisely and complete a kernel-checked proof in the pinned environment without `sorry`, `admit`, circular import, or a replacement axiom. The missing historical source remains a provenance limitation.
3. **Blocking unresolved claim.** Retain the claim as a visible blocked frontier. Any downstream theorem proved by assuming it remains conditional on an unverified foundation.

The mathematical trust gate is:

```text
ADMISSIBLE_MATHEMATICAL_CLAIM(c) =
    SOURCE_FOUND_AND_VERIFIED(c)
    OR INDEPENDENT_LEAN_PROOF_COMPLETED(c)

TRUSTWORTHY_REQUIRED_CLOSURE(target) =
    every required mathematical claim c in ancestors(target)
    satisfies ADMISSIBLE_MATHEMATICAL_CLAIM(c)
```

Definitions require precise formalization and type checking rather than proof that the definition is true. Physical assumptions and empirical claims retain their own contract semantics.

### 6.4 Query-relative DAG completion

For query \(q\), let \(C(q)\) be the required backward mathematical dependency closure and let \(U(q)\subseteq C(q)\) be unresolved external mathematical claims.

\[
\operatorname{DAGComplete}(q)
\iff
U(q)=\varnothing.
\]

This is query-relative and distinct from scientific acceptance. It states that every required external mathematical claim has a verified source path or an independent Lean proof. Target-local proof deltas, formal alignment, semantics, approximation regimes, evidence, and computation retain separate gates.

At iteration \(k\), let \(R_k\subseteq U_k(q)\) be resolved claims and let \(N_k(q)\) be newly exposed prerequisites:

\[
U_{k+1}(q)
=
\bigl(U_k(q)\setminus R_k\bigr)
\cup
N_k(q).
\]

Completion is checked only after recomputing the closure at a fixed point.

### 6.5 Failure classes and graph repair

The pilot uses three top-level failure classes.

#### LOCAL_BUILD_FAILURE

The source claim appears coherent, but the current proof skeleton, decomposition, notation bridge, or library connection is insufficient.

Typical diagnostic tags:

```text
missing_lemma
missing_definition_bridge
proof_decomposition_too_coarse
tactic_failure
library_search_incomplete
implicit_assumption_not_encoded
```

Default repair: `EXPAND_LOCAL`.

Possible actions:

- split one claim into helper claims;
- expose an implicit mathematical premise;
- search Mathlib or a domain package;
- introduce the smallest notation or representation bridge;
- replace one opaque reasoning step with several inspectable steps.

#### ALIGNMENT_FAILURE

The source claim, `MathClaimIR`, Lean declaration, backtranslation, or dependency edge does not preserve the same meaning.

Typical diagnostic tags:

```text
wrong_object_type
quantifier_drift
lost_assumption
new_unjustified_assumption
exact_to_approximate_drift
finite_to_asymptotic_drift
conclusion_too_strong
wrong_dependency_direction
wrong_relation_type
```

Default repair: `REWIRE_OR_RESCOPE`.

Possible actions:

- correct the object mapping;
- restore a lost assumption;
- replace an incorrect theorem import;
- weaken or condition the claim to the source-supported scope;
- split a source statement into distinct mathematical and interpretive claims;
- change an accepted edge back to candidate status.

#### SOURCE_OR_FOUNDATION_GAP

The source does not supply a required step, an imported foundation remains unavailable, or the normalized claim may be false or materially overstated.

Typical diagnostic tags:

```text
missing_source_derivation
unverified_external_foundation
circular_import
counterexample_found
source_claim_ambiguous
package_coverage_gap
```

Default repair: `ESCALATE_OR_BLOCK`.

Possible actions:

- expand backward to a new source;
- create a new Root Agent candidate;
- search for an alternative theorem or proof;
- construct or record a counterexample;
- derive `BLOCKED` or `DISPUTED` and open a blocker of type `UNRESOLVED_EXTERNAL_FOUNDATION` when the source foundation is missing.

A claim is not labeled false merely because Lean proof search failed. A public falsity claim requires an explicit source audit and a checkable counterexample or contradiction argument.

### 6.6 Package-first unresolved-source reduction

Before creating a new Root Agent for an unresolved mathematical claim, run a bounded package search-and-proof pass.

1. Classify the paper and claim into coarse physics and mathematics tags.
2. Retrieve candidate `LeanPackageCapabilityRecord` objects.
3. Normalize the unresolved claim as an exact Lean type, including quantifiers, assumptions, domains, and conventions.
4. Search the pinned project, Mathlib, and selected domain packages by declaration name, type shape, object coverage, and mathematical content.
5. Check candidates in the pinned environment and compare their hypotheses and conclusions with the `MathClaimIR`.
6. If an exact declaration or short transparent bridge suffices, record `INDEPENDENT_LEAN_PROOF_COMPLETED` without creating another PaperAgent.
7. Promote a broadly reusable checked result to a versioned shared `MathContract`.
8. Only when the bounded package pass does not close the claim should the workflow expand source archaeology, create a Root Agent, or retain a blocker.
9. Recompute \(C(q)\) and \(U(q)\) after every attempt.

A field label is only a routing prior. Exact object and declaration compatibility is required before import.

### 6.7 Verification axes

The only axis vocabularies are those defined by the complete precedence tables in Section 5.1.13:

```text
source_fidelity:
  MISALIGNED, BLOCKED, UNCHECKED, PARTIAL, PASSED
relation_validation:
  DISPUTED, INVALID, BLOCKED, CANDIDATE, SOURCE_GROUNDED, VALIDATED
dependency_closure:
  DISPUTED, INCOMPLETE, BLOCKED, UNCHECKED, COMPLETE
mathematics:
  FAILED, BLOCKED, UNCHECKED, PARTIALLY_FORMALIZED,
  SOURCE_DERIVATION_CHECKED, KERNEL_CHECKED, NOT_APPLICABLE
formal_alignment:
  MISALIGNED, BLOCKED, UNCHECKED, BACKTRANSLATED,
  AUTO_ALIGNMENT_PARTIAL, AUTO_ALIGNMENT_PASSED, HUMAN_REVIEWED,
  NOT_APPLICABLE
semantic_alignment:
  CONTESTED, BLOCKED, UNCHECKED, AGENT_REVIEWED, HUMAN_REVIEWED,
  NOT_APPLICABLE
approximation_regime:
  FAILED, BLOCKED, DECLARED_ONLY, PARTIALLY_CHECKED,
  CHECKED_IN_STATED_REGIME, NOT_APPLICABLE
empirical_support:
  CONTESTED, BLOCKED, UNMODELED, SOURCE_GROUNDED, PARTIAL,
  SUPPORTED_IN_RECORDED_REGIME, NOT_APPLICABLE
computation:
  FAILED, BLOCKED, NOT_ATTEMPTED, QUALITATIVE_ONLY,
  REPRODUCED_WITH_TOLERANCE, REPRODUCED, NOT_APPLICABLE
human_review:
  REJECTED, CONTESTED, NOT_PERFORMED, PARTIAL, PERFORMED
```

`relation_validation` describes individual relation acceptance evidence. `dependency_closure` describes fixed-point completeness of the query-required dependency closure. They are never merged. `KERNEL_CHECKED` is the sole kernel-success value. Cross-model agreement, when measured, is an evidence method mapped by policy to `formal_alignment`; it is not a separate axis value.

### 6.8 Overall lifecycle status

A policy-versioned generic `StatusView` for any canonical `TargetRef`, including a ClaimIR, inference step, contract, relation, export, chain, or query resolution, may report one of:

```text
PROPOSED
SOURCE_GROUNDED
SOURCE_VALIDATED
RELATION_VALIDATED
DEPENDENCY_MAPPED
PARTIALLY_VERIFIED
MATH_CLOSED
SEMANTICALLY_RECONSTRUCTED
COMPUTATIONALLY_REPRODUCED
VERIFICATION_CLOSED
BLOCKED
FAILED
DISPUTED
SUPERSEDED
```

For a non-ClaimIR target, the same derivation rules apply to that target's required scope and pinned member ClaimIR values; no proxy ClaimIR status is substituted. `MATH_CLOSED` is profile-sensitive: it is unavailable for `SOURCE_ONLY` and `PARTIALLY_FORMALIZED`, requires source-derivation closure for `DERIVATION_CHECKED`, and requires kernel checking plus automatic alignment for `KERNEL_CHECKED_ALIGNED`, exactly as specified in Section 5.1.13. Every derivation pins the scope/profile, composite snapshot, and evidence/blocker indexes derived from it. `VERIFICATION_CLOSED` means only that every verification coordinate required by that declared scope has an acceptable derived status. Neither label means universal scientific certainty. A new evidence record or policy version produces a new status view; it does not mutate the ClaimIR or overwrite the old view.

### 6.9 Public justification rule

A verification evidence record exposes only concise, independently inspectable reasoning:

```text
source premise
→ normalized claim
→ declared inference operation
→ formal or computational check
→ alignment result
→ scoped conclusion
```

Private model deliberation is not part of the scientific record.

---

## 7. End-to-End Construction Workflow

This section is the operational core of the pilot.

### Phase 0: Select a microdomain and target claim

#### Input

A candidate target paper and a bounded scientific question.

#### Actions

1. Select one central, concrete, dependency-rich claim.
2. Rewrite the target as:

   > Why does paper \(P_T\) conclude \(C_T\), and which mathematical parts of the chain can be independently formalized and checked?

3. Define the pilot boundary before expanding all citations.
4. Estimate whether the query-relative closure is small enough.
5. Exclude targets whose essential source or data are inaccessible or whose formal infrastructure is clearly outside the pilot budget.

#### Recommended pilot size

- 2–6 active papers;
- 5–15 principal claims;
- 3–8 complete inference chains;
- 1–3 Root Agents;
- 1–3 formal Lean declarations;
- at least one backtranslation and alignment audit;
- at least one repair round;
- zero or one essential reproduction task.

#### Output

`pilot-scope.yaml`

```yaml
pilot:
  target_paper: arxiv:...
  target_claim: claim:...
  question: >
    Why does the target paper conclude C?
  included_dependency_types:
    - theorem
    - definition
    - mathematical_assumption
  optional_profiles:
    - semantics
    - computation
  stopping_budget:
    maximum_active_papers: 6
    maximum_root_agents: 3
    maximum_initial_claim_depth: 3
```

#### Gate

The target must be claim-specific. “Understand the whole paper” does not pass.

---

### Phase 1: Freeze the target source

#### Actions

1. Fix the paper version.
2. Prefer author-provided TeX or repository source.
3. Hash every source artifact used.
4. Resolve the stable `work_id`, its one public publication repository, and the exact `source_version_id`.
5. Record the canonical source artifact for this acquisition boundary.
6. Resolve supplements, code, data, and formal artifacts.
7. Build stable anchors for the target claim and its immediate derivation.
8. Prepare a repository commit candidate; do not identify the publication by a branch or floating head.

#### Output

```text
source/artifacts.json
source/source-hashes.json
source/anchors.jsonl
source/cross-references.json
```

#### Gate

No downstream claim may be described as source-checked without an anchor to the frozen version.

---

### Phase 2: Extract and normalize the target claim

#### Actions

1. Run a coarse discourse pass over the full source to propose central claims and their textual realizations. Treat every cluster and paper-level relation as provisional.
2. Select the discourse claim that contains or supports the current query target; leave unrelated central claims at candidate granularity.
3. Extract the exact source span, together with theorem-wide, section-wide, appendix, and notation context needed to interpret it.
4. Preserve raw LaTeX and recursively expand author-defined commands into standard LaTeX.
5. Preserve quantifiers, negations, modality, scope, and exact-versus-approximate status.
6. Resolve all nontrivial symbols.
7. Separate a compound claim into atomic `ScientificClaim` objects and record how the atomic claims reconstruct the source occurrence.
8. Separate definitions, assumptions, semantic regimes, mathematical conclusions, empirical conclusions, and source-independent helper propositions. Do not promote a helper required by formalization to a source claim unless the frozen source supports it.
9. Submit a `claim_ir_build_request` for each formalizable component.
10. Record explicit and inherited assumptions, object types, carriers, domains, local binders, and conventions.
11. Separate the paper's mathematical result from interpretation, evidence, novelty claims, and verification status.
12. Emit either an immutable complete ClaimIR revision or an explicit review-required or failed build result.

#### Output

```text
MathClaimIRRegistry/claims/<claim-id>/revisions/<revision>/claim-ir.yaml
MathClaimIRRegistry/normalization-records/<record-id>/<record-revision>.yaml
MathClaimIRRegistry/decomposition-records/<record-id>/<record-revision>.yaml
agents/<agent-id>/knowledge/staging/<request-id>/
agents/<agent-id>/knowledge/registry-refs.yaml
```

`MathClaimIRRegistry` is authoritative for ClaimIR, normalization, and decomposition records. Agent directories contain only staging attempts, audit payloads, and exact registry references. These outputs contain no mathematical verification status; later records are published to the single authoritative home assigned in Section 10.2.

#### Gate

A successful ClaimIR must be understandable without an undefined symbol, hidden section-wide assumption, ambiguous object type, or author-defined LaTeX command. If that gate fails, the phase emits no complete ClaimIR and preserves the failed attempt and blocker as external audit records.

---

### Phase 3: Extract and validate candidate relations

#### Actions

1. Run the constrained claim and relation extractor.
2. Require source anchors for every candidate.
3. Classify the relation as dependency, epistemic, semantic, computational, or background.
4. Submit every candidate to `relation_validation_request` and preserve its immutable validation result.
5. Keep ambiguous, insufficiently supported, rejected, and failed validations only in the provisional candidate graph.
6. Submit each `VALID` candidate to `relation_acceptance_request` with the exact validation record, acceptance policy, scope, and composite snapshot.
7. Publish an `AcceptedRelation` only on successful acceptance; only those records may enter an accepted dependency DAG.

#### Gate

The candidate/provisional graph and accepted dependency DAG are distinct artifacts. Validation alone never promotes an edge; no relation enters the accepted build graph without an exact `AcceptedRelation` record.

---

### Phase 4: Perform backward dependency archaeology

For the current claim \(C\), ask:

1. Which local equation, theorem, definition, or computation directly supports \(C\)?
2. Which step is performed in the current paper?
3. Which premise is imported from an earlier source?
4. What exact statement is imported?
5. Does the cited source establish the same statement under compatible hypotheses?
6. Is the citation load-bearing, methodological, evidential, contrastive, or background?

Maintain a frontier:

```text
frontier = [target claim]

while frontier is not empty:
    select one unresolved load-bearing claim
    reconstruct only its direct local derivation
    identify imported premises
    ground and validate each proposed dependency
    either:
        expand an imported claim backward
    or:
        stop at a reusable contract, external foundation, or Root Agent
```

#### Gate

A bibliographic citation alone is not a dependency edge.

---

### Phase 5: Select roots and route formal packages

#### Actions

1. Group unresolved imported claims by source and by normalized mathematical object.
2. Search the accepted contract registry before creating PaperAgents.
3. Classify each claim into coarse physics and mathematics domains.
4. Retrieve candidate Lean package capability records.
5. Search exact declarations and type shapes in pinned environments.
6. Create a Root Agent only when source archaeology remains necessary.
7. Record why backward expansion stops.
8. Define exact exports expected from each root or package contract.

#### Valid stop reasons

```text
MATH_CONTRACT_REUSED_WITH_IMPORT_RECEIPT
EXACT_PACKAGE_DECLARATION_FOUND
SHORT_LOCAL_BRIDGE_SUFFICES
PRIMARY_SOURCE_REACHED
FORMAL_CORE_SELF_CONTAINED
STANDARD_BACKGROUND_ACCEPTED
FURTHER_EXPANSION_OUT_OF_SCOPE
SOURCE_UNAVAILABLE
PACKAGE_COVERAGE_GAP
FORMALIZATION_COST_EXCEEDS_PILOT
EMPIRICAL_INPUT_TREATED_AS_EXTERNAL
```

#### Gate

Every root must be selected because of a specific target dependency. A domain label or historical importance is insufficient.

---

### Phase 6: Build and refine Root Agents

For each root source or root contract:

1. Freeze and anchor the source manifestation.
2. Partition the contribution into mathematical claims, semantic assumptions, approximations, and optional computations.
3. Build a shallow inference blueprint.
4. Formalize the selected mathematical core using Section 8.
5. Run Lean and alignment checks.
6. Classify failures into one of the three top-level classes.
7. Apply one local graph-repair operation.
8. Recompute the unresolved frontier.
9. Repeat until the expected export is accepted, conditional, disputed, or blocked.
10. Export only claims whose assumptions, scope, and provenance are explicit; publish later status-view and import-receipt associations only in release manifests, indexes, or query results.

#### Gate

A Root Agent is not accepted merely because it is old, foundational, or frozen. A compiled Lean file is also insufficient without alignment review.

---

### Phase 7: Build intermediate PaperAgents forward

Process accepted mathematical dependencies in topological order.

#### Actions

1. Import predecessor ClaimContracts.
2. Check that the importer uses the same mathematical object.
3. Map notation and conventions.
4. Check every imported assumption against the local setting.
5. Record strengthened, weakened, or newly introduced assumptions.
6. Reconstruct only the paper's local scientific delta.
7. Formalize and refine only blocked local frontier nodes.
8. Export new contracts.

#### Import acceptance

The importer submits the Section 5.1.14 import-acceptance interface with the exact `ClaimContract` `TargetRef`, consumer, candidate status view, composite/evidence/blocker snapshots, scope, acceptance profile, policy, assumption matches, object mappings, and convention mappings. A satisfied import emits a `ClaimImportReceipt`; a conditional import lists unresolved assumptions in `conditions`; rejection or execution failure emits no accepted receipt.

```yaml
claim_import_receipt_excerpt:
  id: import-receipt:intermediate-paper:theorem-T
  record_revision: 1
  applies_to: <exact ClaimContract TargetRef>
  composite_registry_snapshot: {id: composite-snapshot:registry-boundary-17, record_revision: 1, content_hash: 'sha256:...'}
  consumer: agent:intermediate-paper
  decision: CONDITIONAL
  accepted_status_view:
    id: status-view:root-paper:theorem-T:...
    record_revision: 1
    content_hash: sha256:...
  required_scope:
    id: verification-scope:math-import
    revision: 1
    content_hash: sha256:...
  acceptance_profile: KERNEL_CHECKED_ALIGNED
  assumption_matches:
    - assumption: finite_dimensional
      observation: SATISFIED
      evidence_ref: claim:local:finite-dim@1
    - assumption: positivity
      observation: UNRESOLVED
  object_mappings:
    - provider_object: root_symbol_X
      consumer_object: local_symbol_M
  convention_mappings:
    - provider_convention: root_fourier_normalization
      consumer_convention: local_fourier_normalization
      reconciliation_ref: inference:normalization-map@1
  conditions: [positivity]
```

#### Gate

A kernel-checked theorem may not be imported if the importer has not established its hypotheses or object mapping.

---

### Phase 8: Rebuild the target PaperAgent

#### Actions

1. Import all accepted and explicitly conditional ancestor contracts.
2. Verify assumption, object, and convention compatibility.
3. Reconstruct the target paper's local mathematical delta.
4. Formalize and align the selected target claims.
5. Preserve blocked and disputed branches.
6. Generate target exports and limitations, then request exact external status views without copying their values into the Agent or export.
7. Derive `PaperBuildDAG(q)` from the accepted claim DAG through the Section 5.11 construction interface.

The target agent should answer:

```text
What does the paper claim?
Which source spans support that reading?
Why does the selected mathematical claim follow?
Which earlier contracts are imported?
Which assumptions and object mappings are active?
Which declarations were checked by Lean?
What does the source-blind backtranslation say?
Where is the first unresolved frontier?
Which graph repairs were applied?
Which semantic or numerical coordinates remain open?
```

---

### Phase 9: Add SemanticContracts and optional ReproductionRecords

#### Actions

1. Create a `SemanticContract` when physical interpretation is material.
2. Link assumptions and approximations to source spans.
3. Add evidence records only for explicitly relevant support.
4. Emit separate semantic, approximation, and empirical evidence inputs and derive their statuses only in external `StatusView` records.
5. Create a `ReproductionRecord` only when numerical checking is useful or load-bearing.
6. Classify the numerical role as illustrative, supporting, or load-bearing.
7. Map every attempted reproduction to exact release-commit paths for source, data, environment, execution, outputs, and evidence; retain independent hashes because Git location alone is not computational evidence.

#### Gate

The absence of a numerical DAG is not permission to claim that an unreproduced load-bearing numerical result is computationally verified.

---

### Phase 10: Adversarial audit

The audit actively searches for:

- quantifier drift;
- wrong object types;
- notational collapse;
- abstraction elevation;
- equality replaced by proportionality;
- exact results replaced by approximate ones;
- finite statements replaced by asymptotic limits;
- stronger imported claims than the cited source supports;
- hidden assumptions;
- circular claim dependencies;
- paper-level cycles incorrectly interpreted as proof cycles;
- approximation orders that disappear downstream;
- gauge-dependent statements interpreted as observables;
- numerical agreement without parameter equivalence;
- formal theorems describing a narrower or different physical class;
- claims supported only by background citations;
- unresolved Lean axioms or placeholders;
- source-blind backtranslations that expose lost semantics;
- Root Agent claims that fail under explicit counterexamples.

Every discovered problem becomes a first-class repair, blocker, limitation, dispute, or corrected contract.

---

### Phase 11: Release the agent graph

#### Required release objects

```text
source manifests and hashes
PaperAgent manifests
PaperInteractionGraph subset
candidate and accepted relation records
query-relative MathClaimDependencyDAG
query-relative PaperBuildDAG
accepted ScientificClaims and MathClaimIR objects
InferenceSteps
Lean projects and build logs
backtranslations and alignment audits
SemanticContracts and EvidenceRecords when present
ReproductionRecords when present
LeanPackageCapabilityRecords used by the build
GraphRepairRecords
immutable blocker events, status views, and ClaimImportReceipts
coverage and reuse telemetry
release manifest
```

#### Release rule

A publication release is created only after the repository tree is committed. The release operation:

1. creates a new, never-retargeted tag and public Git release for the exact commit;
2. records the commit, tree, provider release identity, release assets, and hashes;
3. atomically publishes the required AgtXIv records and registry-side `ReleaseManifest`;
4. attaches or otherwise exposes the AgtXIv manifest as a release asset without attempting to insert the commit's own identifier into its tree; and
5. verifies that the public tag still resolves to the recorded commit.

A new source version or correction creates a new release. Earlier releases, source manifests, anchors, records, and registry snapshots remain replayable. The release must make incompleteness visible. A partial but explicit graph is preferable to a polished narrative that silently bridges unsupported steps.

---

## 8. Automated Lean 4 Reconstruction Procedure

This procedure applies to selected mathematical cores, not automatically to every mathematical sentence in a paper.

### 8.1 Select the formalization boundary

Choose a theorem or lemma for which:

- the statement is load-bearing;
- hypotheses can be made explicit;
- required objects exist or are feasible to bridge;
- the result is not dominated by informal physical modeling;
- the formalization effort is proportional to the query;
- the expected contract has plausible reuse.

Record what is deliberately excluded.

### 8.2 Route packages and search before proving

Before introducing a project-specific declaration:

1. classify the claim by physics and mathematics tags;
2. retrieve `LeanPackageCapabilityRecord` candidates;
3. search pinned Mathlib, domain packages, and project sources by exact type shape, object coverage, declaration name, and mathematical content;
4. inspect the actual declaration, module, assumptions, axioms, and version;
5. classify each hit as:

```text
EXACT_REUSE
ADAPTABLE_NEAR_MATCH
STRUCTURAL_ANALOGY
NO_MATCH
```

6. retain only the paper-specific bridge and source-aligned wrapper as local delta.

A theorem-search result is candidate retrieval, not verification. It becomes a dependency only after the declaration compiles in the pinned environment and matches the contract assumptions.

### 8.3 Submit the formalization request

Before writing Lean code, submit the exact `agtxiv.formalization-request/1.0.0` interface in Section 5.1.9. The wire request expands `RequestEnvelope`, uses a namespaced artifact-bearing ClaimIR `TargetRef` with `type_schema`, `semantic_content_hash`, exact `target_artifact`, `claim_ir`, and empty `claim_ir_members`, and freezes the complete `formalization_boundary`. Its output is the outcome-dependent `FormalizationRecord` in that section. Section 8 defines no alternate field names or outcomes.

### 8.4 Pin the environment

The formal project contains at least:

```text
lean-toolchain
lakefile.toml
lake-manifest.json
Main.lean or a namespaced module tree
formal-environment.yaml
```

Record:

- Lean version;
- Mathlib commit or release;
- domain package repositories and commits;
- imported modules;
- project hash;
- package-capability records used;
- expected build and audit commands.

### 8.5 Maintain an evolving blueprint

The formalizer works against an evolving blueprint that serves as:

- a natural-language proof graph;
- a Lean theorem and lemma skeleton;
- a mapping from source claims to formal declarations;
- a list of unresolved leaves;
- the shared state for formalizer, auditor, and refiner agents.

Each published blueprint node is immutable semantic planning content. It never points to later attempts, evidence, blockers, or status views.

```yaml
blueprint_node:
  schema: agtxiv.blueprint-node/1.0.0
  id: blueprint:claim-T:lemma-03
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  target: <exact ClaimIR TargetRef>
  source_claims: []
  natural_language_role: ...
  proposed_declaration_signature: ...
  planned_imports: []
  child_node_refs: []
  content_hash: sha256:...
```

Proof attempts are external:

```yaml
blueprint_attempt_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.blueprint-attempt-request/1.0.0
  applies_to: <exact BlueprintNode TargetRef>
  formalization_request_ref: {id: request:formalization:..., record_revision: 1, content_hash: 'sha256:...'}
```

```yaml
blueprint_attempt_record:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.blueprint-attempt/1.0.0
  applies_to: <same BlueprintNode TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  attempt_artifacts: []
  diagnostic_artifacts: []
```

Success, rejection, unresolved proof obligations, and execution failure follow the envelope meanings. New planning content creates a superseding blueprint revision; an attempt never mutates the node.

### 8.6 Formalizer or Blueprinter Agent

Model A receives:

- frozen source spans;
- `MathClaimIR`;
- accepted contracts;
- selected package declarations;
- the current blueprint;
- compiler feedback from prior rounds.

It proposes:

- theorem statements;
- helper lemmas;
- explicit assumptions;
- package imports;
- proof code;
- candidate dependency refinements.

The Agent may not change the target `MathClaimIR` silently. Any proposed rescoping becomes an explicit alignment repair.

### 8.7 Lean kernel and dependency audit

For each generated declaration:

1. elaborate and compile in the pinned environment;
2. reject unresolved placeholders;
3. record actual declaration dependencies;
4. record axioms;
5. compare actual dependencies with the blueprint;
6. preserve compiler output and build hashes.

Lean establishes formal correctness under encoded assumptions. It does not establish source fidelity.

### 8.8 Source-blind Backtranslator Agent

Model B receives only the source-blind context allowed by the exact `agtxiv.backtranslation-request/1.0.0` interface in Section 5.1.9. The isolated runner hashes the delivered context and emits the `BacktranslationRecord` with its independence attestation. Source text, ClaimIR statement content, prior backtranslations, and alignment records are forbidden inputs. `SUCCEEDED`, `REJECTED`, `BLOCKED`, and `FAILED_TO_RUN` have exactly the field-presence rules stated there; Section 8 defines no alternate `PRODUCED` or `PARTIAL` outcome vocabulary.

### 8.9 Alignment Auditor

The auditor consumes the exact source artifact, ClaimIR semantic hash, formalization record, independent backtranslation record, comparison policy, and criticality policy through `agtxiv.alignment-request/1.0.0` in Section 5.1.10. It emits only the full `AlignmentRecord` schema defined there. Field deltas use the normative delta-kind and severity vocabularies; `PASSED` alone is not an alignment result.

### 8.10 Source-aware Refiner

The Refiner receives:

- original source spans;
- current `MathClaimIR`;
- blueprint;
- Lean compiler output;
- source-blind backtranslation;
- alignment audit;
- graph-repair history.

It first classifies the failure:

```text
LOCAL_BUILD_FAILURE
ALIGNMENT_FAILURE
SOURCE_OR_FOUNDATION_GAP
```

It then proposes one local repair family:

```text
EXPAND_LOCAL
REWIRE_OR_RESCOPE
ESCALATE_OR_BLOCK
```

The Refiner must not invent new source claims without assigning `origin.class: DERIVED_CLAIM` and exact premise/inference provenance. It must not silently weaken a theorem merely to obtain a proof.

### 8.11 Automation and human interface

The pipeline is designed to operate automatically across many root claims. Human reviewers need not inspect tactics. The review interface should display:

```text
frozen source statement
normalized MathClaimIR
source-blind backtranslation
added assumptions
lost assumptions
object mappings
exact versus approximate status
automatic alignment verdict
remaining blocker
```

External status views use only the normative axis values `mathematics: KERNEL_CHECKED`, `formal_alignment: AUTO_ALIGNMENT_PASSED`, `semantic_alignment: HUMAN_REVIEWED`, and `human_review: PERFORMED`. Cross-model agreement is an evidence method, not an axis value. `AUTO_ALIGNMENT_PASSED` does not imply human review.

### 8.12 Kernel, placeholder, and axiom checks

An accepted formal export requires:

1. a clean project build;
2. no `sorry`, `admit`, or equivalent placeholders in the accepted dependency closure;
3. no unexpected axioms;
4. a recorded `#print axioms` result or equivalent audit;
5. build logs and environment hashes;
6. a source-blind backtranslation;
7. an alignment audit with no unresolved critical mismatch;
8. exported assumptions exactly matching the Lean declaration.

Typical commands are recorded in the repository:

```bash
lake build
lake env lean AgtXIv/RootPaper.lean
```

### 8.13 Formal export

An export contains no aggregate status fields. A generic `StatusView` targeting the exact immutable export may derive a mathematics axis value of `KERNEL_CHECKED` only when its pinned evidence snapshot contains a clean placeholder-free build and documented axiom audit. It may derive `formal_alignment: AUTO_ALIGNMENT_PASSED` only when the source and ClaimIR are anchored, an independent source-blind backtranslation exists, no critical mismatch remains, and every accepted rescoping is explicit and versioned. Human-review evidence contributes only when a qualified reviewer actually produced it. The immutable export must not reference that later status view or any `ClaimImportReceipt`. Exact associations appear only in external indexes, release manifests, or query results.

### 8.14 Lean-guided semantic claim repair

Lean acts as an executable pressure test for the candidate decomposition. It may expose a missing definition, hidden premise, object-type mismatch, invalid dependency, omitted intermediate result, unexpected axiom, counterexample, or source-to-formal mismatch. These findings drive local repair proposals; they do not give Lean or the Refiner authority to rewrite the frozen source or mutate an accepted ClaimIR.

The repair loop preserves four distinct layers:

```text
frozen source occurrences
→ provisional discourse and atomic claim graph
→ immutable ScientificClaim, MathClaimIR, and SemanticContract revisions
→ formalizations, verification evidence, diagnostics, and repair history
```

The provisional graph may be iterated freely by publishing new or superseding candidate records, but no immutable candidate record is overwritten and no candidate is promoted without the existing validation and acceptance path. A change to accepted source meaning creates a new immutable revision through the existing construction or revision interface. A correction to Lean code creates a new formalization attempt or record. A helper inferred from exact recorded premises is a `DERIVED_CLAIM`; an independently introduced helper is a `SOURCE_INDEPENDENT_PROPOSITION` represented by `MathematicalPropositionIR`. Neither is attributed to the frozen paper unless a separate source occurrence supports it. A confirmed false source claim remains addressable as the original source occurrence and receives refutation evidence; it is never overwritten by a weaker true statement.

#### Diagnostic classification

The Refiner first assigns one of the existing top-level failure classes and then records a more specific non-normative diagnostic tag. Typical tags include:

```text
LOCAL_BUILD_FAILURE
  missing_definition
  lean_typecheck_or_coercion_failure
  missing_premise_candidate
  missing_helper
  invalid_or_incomplete_inference_step
  unexpected_dependency
  placeholder_or_axiom_violation

ALIGNMENT_FAILURE
  quantifier_mismatch
  assumption_added_or_lost
  wrong_object_type
  object_mapping_mismatch
  scope_mismatch
  exact_approximate_mismatch
  conclusion_strengthened_or_weakened

SOURCE_OR_FOUNDATION_GAP
  source_ambiguous
  required_premise_not_in_source
  external_foundation_missing
  counterexample_confirmed
```

A local Lean typechecking or coercion error remains `LOCAL_BUILD_FAILURE`; disagreement among the source, ClaimIR, Lean declaration, or backtranslation about the represented object or carrier is `ALIGNMENT_FAILURE`. These tags elaborate the existing failure classes and do not create a new wire-level outcome vocabulary. A timeout, failed theorem search, or unsolved goal is not by itself evidence that a claim is false or that an assumption is missing. A counterexample affects the source claim only after its objects satisfy the exact encoded assumptions and the object mapping has passed audit.

#### Allowed repair actions

Each diagnostic may propose one or more internal actions. These actions are not new values of `graph_repair_request.operation`; graph publication continues to use only `EXPAND_LOCAL`, `REWIRE_OR_RESCOPE`, or `ESCALATE_OR_BLOCK`.

- split a compound occurrence into separately anchored atomic conclusions while preserving reconstruction provenance and shared scope;
- merge only provisional realizations after types, quantifiers, assumptions, scope, exactness, and conclusions are shown equivalent; embedding similarity alone is insufficient;
- add a source-grounded definition, assumption, intermediate claim, external foundation, or explicit `InferenceStep`;
- add a helper proposition, choosing `DERIVED_CLAIM` only when exact recorded premises and an inference step derive it, and otherwise choosing `SOURCE_INDEPENDENT_PROPOSITION`;
- reverse or retype a candidate relation, replace a false single-premise edge with a multi-premise `InferenceStep`, or propose an explicit scope correction;
- repair imports, namespaces, coercions, package mappings, statements, or proof code without changing source meaning;
- preserve a source claim and attach a reproducible counterexample record, then propose a candidate `refutes` relation through the existing validation and acceptance interfaces;
- expose an unresolved source ambiguity or external foundation instead of inventing a bridge.

Source-grounded split, expansion, and added prerequisites are classified under `EXPAND_LOCAL`. Candidate merging, edge reversal, relation retyping, and rescoping are classified under `REWIRE_OR_RESCOPE`. Refutation evidence and unresolved ambiguity are handled under `ESCALATE_OR_BLOCK`. A formalization-only correction creates a new formalization attempt or record and does not invoke graph repair unless accepted dependencies also change. Dependent query outputs are invalidated only after the required evidence, accepted relations, repairs, and superseding snapshots become visible through the existing interfaces.

A rescoping from a claim over a domain \(X\) to a claim over a strict subdomain \(X_0\) is a source correction only when the frozen source supports \(X_0\) and the previous extraction omitted it. Otherwise the restricted result is a new derived claim. The same rule applies to added regularity, finiteness, nonemptiness, perfectness, exactness, or physical-regime assumptions.

#### Source-meaning gate

Every repair proposal that could affect semantic content returns to the frozen source. The gate compares the proposed change field by field against exact anchors. Implementations may use internal decision labels such as:

```text
SOURCE_EXPLICIT
SOURCE_IMPLICIT_SUPPORTED
SOURCE_AMBIGUOUS
NOT_IN_SOURCE
CONTRADICTED_BY_SOURCE
```

and internal action labels such as:

```text
ALLOW_NEW_IR_REVISION
ALLOW_SOURCE_GROUNDED_EXPANSION
REQUIRE_DERIVED_OR_INDEPENDENT_PROPOSITION
FORMALIZATION_ONLY
ATTACH_REFUTATION_EVIDENCE
REJECT_REPAIR
BLOCK
```

These labels are audit vocabulary, not new request, result, status, or graph-operation enums. Publication uses the existing ClaimIR revision, generic object-construction, formalization, evidence, relation-validation and acceptance, graph-repair, blocker, snapshot, and invalidation interfaces.

A new ClaimIR revision is reserved for a demonstrated extraction or normalization error and publishes a semantic diff; this repair workflow defines no alternate query or ClaimIR interface. A source-grounded expansion adds separately anchored nodes without changing the target statement. A required extra proposition keeps the source claim unchanged and receives the origin class determined by its actual provenance. A formalization-only action changes no semantic record. Refutation handling preserves the original source claim, publishes counterexample or contradiction evidence, and routes the proposed `refutes` relation through normal validation and acceptance. Unsupported proposals are rejected or blocked.

A source-supported change to physical interpretation, operational definition, or approximation regime creates a new immutable `SemanticContract` revision through the existing generic object-construction interface; it creates a ClaimIR revision only when represented mathematical meaning changes. An unsupported physical regime must not be inserted into a source-grounded `SemanticContract`; when mathematically useful, it may instead scope a distinct derived claim with explicit provenance.

#### Operational loop

```text
source-grounded claim or semantic component
→ package search and formalization attempt
→ Lean build, dependency, placeholder, and axiom checks
→ source-blind backtranslation
→ field-level alignment comparison
→ localized diagnostic
→ one or more local repair proposals
→ source-meaning gate
→ new formalization, graph expansion, immutable semantic revision,
  derived claim, refutation evidence, or blocker
→ rebuild only invalidated query closures
```

The loop terminates in existing artifacts and derived views: a `StatusView` such as `MATH_CLOSED`, `FAILED`, `BLOCKED`, or `DISPUTED`; a conditional `ClosureArtifact`; an `AlignmentRecord`; an open `BlockerRecord`; or accepted refutation evidence and relations. This section defines no additional lifecycle outcome vocabulary. Proof success never hides an alignment mismatch, and proof failure never silently weakens the target.

#### Required pilot repair cases

The first vertical slice should preserve three distinct repair traces:

1. **Extraction correction:** Lean or backtranslation exposes an assumption that is explicitly present in the source but absent from the extracted claim. The source-meaning gate permits a new ClaimIR revision with an exact semantic diff.
2. **Helper proposition:** Lean requires an intermediate proposition that the source does not state as a separate claim. If exact recorded premises and an `InferenceStep` derive it, the graph gains a `DERIVED_CLAIM`; otherwise it gains a `SOURCE_INDEPENDENT_PROPOSITION` represented by `MathematicalPropositionIR`. The source ClaimIR remains unchanged.
3. **Refuted source claim:** a reproducible counterexample satisfies the source assumptions and violates the conclusion. The original claim remains in the Registry with refutation evidence, while any valid restricted replacement is published as a distinct derived claim.

These cases demonstrate that verification feedback can improve claim decomposition and graph structure while preserving the authority of the frozen source.

---

## 9. Semantic Contracts and Numerical Reproduction

### 9.1 SemanticContract procedure

For every physically meaningful conclusion selected for semantic reconstruction:

1. define the physical system;
2. define preparation, state, observable, or effective degree of freedom;
3. record conventions and normalization;
4. identify physical assumptions;
5. identify mathematical assumptions;
6. identify approximations and control parameters;
7. map source objects to formal mathematical objects;
8. track validity regimes forward;
9. test dimensions, symmetries, and meaningful limits;
10. separate mathematical conclusion from physical interpretation;
11. attach evidence records to the exact assumption or regime they support;
12. record automatic and human review evidence separately and derive statuses only through external status views.

The unified contract avoids separate full schemas for physical semantics and evidence. It does not own status; external views preserve the distinct epistemic axes.

### 9.2 Assumption and evidence separation inside one contract

An experiment may support an assumption only under specified conditions:

```text
Evidence E
--supports_under_conditions-->
Assumption A in regime R
```

It does not prove:

```text
A in every regime
```

or

```text
all mathematical consequences of A describe nature exactly
```

A `SemanticContract` therefore supplies separately scoped evidence for `semantic_alignment`, `approximation_regime`, and `empirical_support`; a generic external `StatusView` derives those coordinates without writing them back into the contract.

### 9.3 Approximation propagation

If a step uses

\[
F(\epsilon)
=
F_0+\epsilon F_1+O(\epsilon^2),
\]

then every dependent claim inherits the approximation unless a later argument removes or bounds it.

```yaml
approximation:
  parameter: epsilon
  retained_order: 1
  discarded_order: "O(epsilon^2)"
  regime: "|epsilon| << 1"
  propagated_to:
    - claim:C1
    - claim:C2
```

A downstream exact theorem may use the truncated model exactly, but the physical conclusion remains conditional on the model approximation.

### 9.4 Minimal semantic checks

Apply when relevant:

- dimensional consistency;
- conservation laws;
- symmetry compatibility;
- gauge or basis dependence;
- weak- and strong-coupling limits;
- zero-temperature or classical limits;
- finite-size versus infinite-size distinctions;
- positivity, normalization, and probability bounds;
- singular and degenerate parameter values;
- operational correspondence between measured and formal quantities.

Passing these checks does not prove a physical conclusion. Failing one may refute or rescope it.

### 9.5 Numerical reproduction procedure

Numerical reproduction is optional unless the selected claim is computationally load-bearing.

#### Freeze inputs

Record:

- code source and commit;
- data version and hashes;
- model parameters;
- preprocessing;
- random seeds;
- numerical precision;
- hardware-sensitive settings when relevant.

#### Reproduce the minimal result

Prefer the smallest computation that checks the load-bearing claim:

- one reported table entry;
- one limiting value;
- one curve point plus convergence information;
- one figure generated from the released script;
- one independent implementation of the key numerical identity.

#### Compare

```yaml
comparison:
  reported_value: 0.12345
  reproduced_value: 0.12347
  absolute_error: 0.00002
  tolerance: 0.00010
  verdict: REPRODUCED_WITH_TOLERANCE
```

#### Preserve evidence

Store commands, logs, generated data, plots, environment lock files, output hashes, and failure traces under the canonical publication-repository layers in Section 10.1. A screenshot alone is not a reproduction record. Large data may use release assets, Git LFS, or external archives only when the record resolves the exact object and verifies an independent content hash; a mutable URL or unresolved LFS pointer is insufficient.

### 9.6 Closure semantics for computation

If a numerical result is `ILLUSTRATIVE`, `NOT_ATTEMPTED` does not block mathematical closure.

If it is `LOAD_BEARING`, the system may still report:

```text
MATH_CLOSED
SEMANTICALLY_RECONSTRUCTED
```

but not:

```text
COMPUTATIONALLY_REPRODUCED
```

or a scientific closure that explicitly requires numerical reproduction.

---

## 10. Publication Repositories, Registry Service, and Agent Interface

### 10.1 Per-publication repository and canonical referencing

Each traced `work_id` has one public Git repository. The repository is the evolving publication container; a release-bound commit is one immutable publication instance. The canonical layout is role-based rather than tool-based:

```text
README.md
CITATION.cff
LICENSE
source/
  manifest.json               # canonical release-commit acquisition payload
  anchors.jsonl               # derived SourceRegistry export; carries derived_from
  upstream/                  # exact redistributable inputs only
  locators/                  # hashes and stable external locators
paper/
  manuscript/
  bibliography/
  figures/
formal/
  lean-toolchain
  lakefile.toml
  lake-manifest.json
  formal-environment.yaml
  AgtXIv/
reproduction/
  manifest.yaml
  code/
  data/
  environment/
  workflows/
  outputs/
  logs/
  blockers/
agtxiv/
  paper-agent-manifest.yaml    # derived PaperAgentRegistry export; carries derived_from
  registry-refs/
  audit/
  staging/
  graph/                     # derived, rebuildable views only
docs/
  limitations.md
  release-notes.md
.github/workflows/           # automation, not scientific authority
```

The layout expresses six reproducibility layers:

| Layer | Canonical contents |
|---|---|
| source | exact redistributable manuscript/code bytes or hash-addressed restricted locators, plus independent implementations and provenance |
| data | exact inputs or content-addressed external locators |
| environment | lockfiles, containers, toolchains, hardware-sensitive settings |
| execution | deterministic commands, parameters, seeds, and workflows |
| output | regenerated values, figures, tables, and output hashes |
| evidence | comparisons, logs, validation reports, failures, and blockers |

The **canonical structure and referencing principle** applies across the repository and registries:

1. Every authoritative artifact or record has one owning path or registry home.
2. Other locations contain exact references, not independently maintained copies.
3. A necessary mirror declares `derived_from` together with the exact revision, content hash, and artifact hash; generated views are marked rebuildable.
4. Git history does not make duplicated paths non-duplicative, and a path is only a locator at one commit.
5. Cross-repository reuse points to the same authoritative registry object instead of vendoring a second authority.
6. Distinct semantic layers such as ClaimIR, formalization, evidence, blocker, and status view are not duplicates merely because they concern the same claim.

`source/manifest.json` is the canonical release-commit acquisition payload. `SourceRegistry` owns the immutable `SourcePackageRecord` that wraps its exact commit path, schema, serialization profile, artifact hash, and semantic fields. By contrast, `source/anchors.jsonl` and `agtxiv/paper-agent-manifest.yaml` are release serializations of registry-owned records and must carry `derived_from` metadata. They have no independent authority.

Git and provider features divide responsibility as follows:

| Capability | Reused repository feature | AgtXIv boundary |
|---|---|---|
| file evolution and comparison | commits, trees, diffs, blame, branches | byte history is not semantic revision history |
| publication snapshot | full commit and tree identifiers; signed tag; provider release and immutable-release enforcement | `ReleaseManifest` verifies the binding and asset hashes; branches and tag names alone are insufficient |
| collaboration | forks, pull requests, reviews, issues, discussions | events are provenance or candidate evidence until represented by accepted AgtXIv records |
| automation | versioned workflows, checks, logs, artifacts | ephemeral CI output is not durable verification evidence unless captured and hashed |
| citation and preservation | `CITATION.cff`, release notes, signatures, attestations, external archive or DOI | mutable repository metadata is not an exact citation; scientific correctness is not inferred |
| large artifacts | release assets, Git LFS, external archives | every dependency needs an immutable locator and independent content hash |

### 10.2 Authoritative registry-service ownership and publication

Every normative object has exactly one authoritative home. This registry-service ownership complements, rather than duplicates, the per-publication repository layout. Each registry's own manifest and append-log segments are authoritative in that registry and nowhere else:

| Objects | Authoritative home |
|---|---|
| `ScientificClaim` (including records with `claim_role: CONTRIBUTION`), `ProfileAssociationRecord` | `ScientificClaimRegistry` |
| `SourcePackageRecord`, registered source-artifact envelopes, and `SourceAnchor`; exact release-commit source payloads are addressed through those records | `SourceRegistry` |
| stable work identity and `WorkRepositoryBinding` | `WorkRegistry` |
| `CandidateRelation`, validation records, `AcceptedRelation` | `RelationRegistry` |
| `MathClaimIR`, `MathematicalPropositionIR`, normalization, decomposition, semantic revision, migration | `MathClaimIRRegistry` |
| `MathContract`, `ClaimContract`, immutable export interfaces | `ContractRegistry` |
| `InferenceStep`, `BlueprintNode` | `ReasoningRegistry` |
| `SemanticContract`, semantic component evidence | `SemanticRegistry` |
| `ReproductionRecord` | `ReproductionRegistry` |
| `LeanPackageCapabilityRecord` | `LeanPackageCapabilityRegistry` |
| graph artifacts, closures, `DependencyNodeManifest`, `ClaimToPaperAgentMappingSnapshot`, `PaperBuildDAGArtifact`, `CompanionBundle`, graph-repair records | `GraphRegistry` |
| `PaperAgentManifest` | `PaperAgentRegistry` |
| schema artifacts and serialization profiles | `SchemaRegistry` |
| `VerificationScope`, `FormalEnvironment`, every policy, status rule table, graph/query algorithm descriptor, and criticality table | `ConfigurationRegistry` |
| `CompositeRegistrySnapshot` and every evidence, blocker, relation, receipt, graph, or registry index snapshot | `SnapshotRegistry` |
| `ContributionCalibrationRecord`, `ClaimSupportAssociation`, attribution, formalization, backtranslation, verification, alignment, blocker events, status views, blueprint attempts, package trust evidence, and all request/result records not assigned by another row | `ExternalRecordRegistry` |
| `QueryResolution`, `DependencyManifest`, `ClaimImportReceipt`, `ReleaseManifest`, `RegistryTransactionReceipt`, and `PaperAgentAnswer` | `ReceiptRegistry` |
| build, coverage, and reuse telemetry records | `TelemetryRegistry` |

The corresponding normative layout is:

```text
WorkRegistry/
SourceRegistry/
ScientificClaimRegistry/
RelationRegistry/
MathClaimIRRegistry/
ContractRegistry/
ReasoningRegistry/
SemanticRegistry/
ReproductionRegistry/
LeanPackageCapabilityRegistry/
GraphRegistry/
PaperAgentRegistry/
SchemaRegistry/
ConfigurationRegistry/
SnapshotRegistry/
ExternalRecordRegistry/
ReceiptRegistry/
TelemetryRegistry/
agents/
graph/
```

Each registry owns an immutable content-addressed manifest and append log. `agents/` contains staging inputs, source code, logs, and payload artifacts only. `graph/` contains rebuildable indexes and visualizations only. Any duplicate under either path is marked `derived_from` with exact authoritative ID, revision, and hash and has no independent authority.

A release manifest is authoritative only in `ReceiptRegistry`:

```yaml
release_manifest:
  schema: agtxiv.release-manifest/1.1.0
  id: agtxiv-release-manifest:work-slug:release-tag
  record_revision: 1
  supersedes: null
  supersedes_publication_ref: null
  produced_at: 2026-08-26T00:00:00Z
  publication:
    work_repository_binding_ref: <exact WorkRepositoryBinding TargetRef>
    git_release:
      tag_name: agtxiv-v1
      tag_object_oid: <full annotated-tag object ID or null>
      target_commit_oid: <full commit object ID>
      target_tree_oid: <full tree object ID>
      provider_release_id: <stable provider release ID>
      release_url: https://github.com/owner/repository/releases/tag/agtxiv-v1
      payload_release_asset_hashes: []
  paper_agent_manifest: <exact PaperAgentManifest TargetRef>
  source_package_ref: <exact SourcePackageRecord TargetRef>
  content_registry_snapshot: {id: composite-snapshot:content-boundary-18, record_revision: 1, content_hash: 'sha256:...'}
  dependency_manifests: []
  published_objects: []
  external_associations: []
  payload_artifacts: []
  content_hash: sha256:...
```

Each release tag defines a distinct logical manifest ID and normally starts at `record_revision: 1`; `supersedes` is reserved for correcting an unpublished registry record with the same logical ID. Once public, a correction uses a new tag and manifest ID and records cross-publication lineage only in `supersedes_publication_ref`.

All arrays are canonical sorted sets of exact references. `payload_release_asset_hashes` covers release assets other than the serialized AgtXIv manifest itself, avoiding a self-hash cycle. The manifest asset uses the canonical JSON serialization declared by its schema; validation parses those bytes and recomputes the record `content_hash` with only the `content_hash` field omitted. This is record-hash verification, not an assertion that the complete asset-byte hash equals `content_hash`. Provider attestation or a later external evidence record may additionally preserve the complete manifest-asset byte hash. `external_associations` is the permitted home for status-view, blocker, attribution, and receipt associations that immutable targets do not own.

Cross-registry writes are atomic through this interface. The excerpt shows the second, release-certification transaction; an ordinary content transaction uses the same interface with `release_manifest_artifact_hash: null`:

```yaml
registry_transaction_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.registry-transaction-request/1.0.0
  base_composite_registry_snapshot: {id: composite-snapshot:content-boundary-18, record_revision: 1, content_hash: 'sha256:...'}
  expected_registry_heads:
    - registry_id: ReceiptRegistry
      manifest_revision: 18
      manifest_content_hash: sha256:...
  writes:
    - registry_id: ReceiptRegistry
      object_id: agtxiv-release-manifest:work-slug:release-tag
      object_revision: 1
      content_hash: sha256:...
      artifact_hash: sha256:...
  release_manifest_artifact_hash: sha256:...
```

```yaml
registry_transaction_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.registry-transaction-result/1.0.0
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  transaction_receipt: null
  current_registry_heads: []
```

`SUCCEEDED` requires this receipt in `ReceiptRegistry`:

```yaml
registry_transaction_receipt:
  schema: agtxiv.registry-transaction-receipt/1.0.0
  id: registry-transaction:...
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-22T00:00:00Z
  request_ref: {id: request:registry-transaction:..., record_revision: 1, content_hash: 'sha256:...'}
  base_composite_registry_snapshot: {id: composite-snapshot:content-boundary-18, record_revision: 1, content_hash: 'sha256:...'}
  precondition_heads: []
  committed_writes: []
  committed_write_set_hash: sha256:...
  release_manifest_artifact_hash: sha256:...
  committed_at: 2026-08-22T00:00:00Z
  producer:
    implementation: registry-transaction-service
    version: 1.0.0
    implementation_hash: sha256:...
  content_hash: sha256:...
```

The receipt pins the exact base snapshot, all precondition heads, committed writes, canonical write-set hash, release-manifest artifact hash, and commit time. It deliberately contains no post-transaction registry-manifest hash or resulting `CompositeRegistrySnapshot`: either would make the receipt hash depend on a registry state that already contains the receipt. `expected_registry_heads` must contain exactly the participating registries and equal their boundaries in the base composite snapshot; omission, addition, or mismatch is `REJECTED`. All writes and the receipt become visible together. After that commit, the snapshot service creates a separate `CompositeRegistrySnapshot` over the resulting manifests; no object inside that boundary points forward to the boundary itself.

Publication uses two acyclic boundaries. First, a content transaction publishes claims, contracts, evidence, graphs, and the PaperAgent manifest, after which the snapshot service emits the `content_registry_snapshot`. Second, after the repository commit and provider release exist, a certification transaction publishes the `ReleaseManifest`, which pins that prior content snapshot, the exact Git release, and its payload assets. A later publication snapshot may include the manifest and both transaction receipts, but the manifest does not point to that later snapshot. Invalid ownership or object schema is `REJECTED`. A stale head or unresolved cross-reference is `BLOCKED` and publishes nothing. `FAILED_TO_RUN` publishes nothing. Crash recovery either exposes each complete transaction and its writes or none; partial visibility is forbidden.

An AgtXIv registry release is accepted only through such a receipt. A public publication instance additionally requires successful verification that the recorded repository, tag, commit, tree, provider release, and release assets exist and match the `ReleaseManifest`. The Git release is the distribution coordinate; the AgtXIv manifest is its registry-side certificate and index. Release manifests may index exact status views, blockers, and receipts, but immutable claims, contracts, exports, blueprints, and relations do not acquire reverse links to them.

### 10.3 Generic Agent query interface

```yaml
agent_query_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.agent-query-request/1.0.0
  operation: claims | why | source | assumptions | dependencies | imports | local_delta | evidence | formalization | backtranslation | alignment | semantics | reproduction | repairs | blockers | exports | status
  applies_to: <TargetRef; omitted only for collection operations>
  index_snapshot: {id: external-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
```

```yaml
agent_query_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.agent-query-result/1.0.0
  applies_to: <same TargetRef; omitted for collection operations>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  resolved_targets: []
  record_refs: []
  payload_artifacts: []
  status_view_index_refs: []
  candidate_targets: []
```

`SUCCEEDED` returns exact immutable references. Invalid operation or target is `REJECTED`; not-found, ambiguous resolution, or unusable snapshot is `BLOCKED` with candidates where available; execution failure returns no inferred answer. No result fabricates a ClaimIR or copies aggregate status.

### 10.4 Graph query interface

```yaml
graph_query_request:
  extends: agtxiv.request-envelope/1.0.0
  schema: agtxiv.graph-query-request/1.0.0
  applies_to: <exact query-resolution, graph, chain, or relation TargetRef>
  operation: paper_interactions | math_dag | paper_build_dag | companion_bundles | accepted_closure | conditional_closure | blocked_frontier | local_delta
  graph_snapshot: {id: graph-index:snapshot-..., record_revision: 1, content_hash: 'sha256:...'}
```

```yaml
graph_query_result:
  extends: agtxiv.result-envelope/1.0.0
  schema: agtxiv.graph-query-result/1.0.0
  applies_to: <same TargetRef>
  outcome: SUCCEEDED | REJECTED | BLOCKED | FAILED_TO_RUN
  graph_artifact_ref: null
  closure_artifact_ref: null
  node_targets: []
  edge_targets: []
  status_view_index_refs: []
```

Success returns exact hashes and canonically ordered TargetRefs. Invalid operation or target is `REJECTED`; missing or invalid snapshot and unresolved closure are `BLOCKED`; execution failure returns no graph. Partial output is allowed only as a separately hashed audit artifact and is never an accepted closure. Non-ClaimIR targets use generic `StatusView`; singular and multi-member governing ClaimIR fields follow Section 5.1.2.

### 10.5 Response discipline

Every PaperAgent answer classifies its basis as `DIRECT_SOURCE`, `IMPORTED_CONTRACT`, `DERIVED_FROM_ACCEPTED_CHAIN`, `AUTOFORMALIZED_AND_ALIGNED`, `UNVERIFIED_INFERENCE`, `BLOCKED`, or `DISPUTED`.

```yaml
answer:
  schema: agtxiv.paper-agent-answer/1.0.0
  id: answer:target:C:why
  record_revision: 1
  supersedes: null
  produced_at: 2026-08-18T00:00:00Z
  applies_to: <exact chain TargetRef>
  question: Why does claim C hold?
  basis: DERIVED_FROM_ACCEPTED_CHAIN
  status_view_refs:
    - id: status-view:chain:target:C:...
      record_revision: 1
      content_hash: sha256:...
  unresolved_target_refs:
    - <exact semantic-contract TargetRef>
  conclusion: >
    The referenced status view supports the mathematical derivation under its
    pinned scope. The semantic and computational targets remain unresolved.
  content_hash: sha256:...
```

The answer contains no `math_status`, `formal_alignment`, or other aggregate axis field. It must refuse to present unsupported inference as a paper claim, and a request failure returns an immutable failure result rather than a fluent substitute answer.

---

## 11. Acceptance Criteria and First Pilot

### 11.1 Acceptance profiles for an exported MathContract

A contract declares exactly one hash-pinned acceptance profile in its required verification scope. The status policy defines these profiles:

| Profile | Required minimum axes | Formal artifacts |
|---|---|---|
| `SOURCE_ONLY` | `source_fidelity: PASSED`; applicable relation requirements satisfied | Formalization is out of scope; `mathematics: UNCHECKED` and `formal_alignment: NOT_APPLICABLE` are permitted. No backtranslation or alignment is required. |
| `DERIVATION_CHECKED` | `source_fidelity: PASSED`, `dependency_closure: COMPLETE`, `mathematics: SOURCE_DERIVATION_CHECKED` | Formalization is out of scope unless separately requested; no backtranslation or formal alignment is required. |
| `PARTIALLY_FORMALIZED` | `source_fidelity: PASSED`, `mathematics: PARTIALLY_FORMALIZED`; explicit unresolved formal boundary | Partial formalization evidence and blockers are required. Backtranslation or alignment is required only for generated declarations included by the scope. |
| `KERNEL_CHECKED_ALIGNED` | `source_fidelity: PASSED`, `dependency_closure: COMPLETE`, `mathematics: KERNEL_CHECKED`, `formal_alignment: AUTO_ALIGNMENT_PASSED` | Clean kernel build, placeholder and axiom audit, independent source-blind backtranslation, and full alignment record are required. |

Every accepted export also requires an exact ClaimIR semantic revision and hash, explicit assumptions and imports, source or independent-proposition provenance, typed inference steps where applicable, contract version and compatibility policy, visible limitations, and an external release-manifest association to an immutable `StatusView` whose target, profile scope, policy, composite snapshot, evidence snapshot, and blocker snapshot match. Human review is never inferred.

A contract may be accepted under a weaker profile without being represented as kernel checked. Formalization explicitly marked out of scope maps formal alignment to `NOT_APPLICABLE`; the system must not manufacture a backtranslation or alignment requirement. Consumers may demand a stronger profile through import acceptance.

### 11.2 Acceptance rule for a SemanticContract

A semantic contract is acceptable at the declared automated level when:

- the physical system and modeled objects are source-grounded;
- object mappings are explicit;
- assumptions and approximation regimes are recorded;
- evidence is linked to exact assumptions or regimes;
- external status views derive separate semantic-alignment and empirical-support axes;
- automated review is not labeled human review;
- unresolved interpretive ambiguity is visible.

### 11.3 Acceptance rule for a Root Agent

A Root Agent passes the pilot gate when:

- its expected root export is source-anchored;
- the selected mathematical derivation has been reconstructed;
- its formalizable core is kernel-checked or explicitly scoped out;
- source-to-formal alignment is audited;
- essential semantic assumptions are recorded when applicable;
- load-bearing numerical evidence is reproduced or marked unresolved;
- its export contract exposes all assumptions and regimes;
- no blocker affecting the exported conclusion is hidden.

Root status does not make every claim in the paper acceptable.

### 11.4 Acceptance rule for the target query

The query result should reference separate closure levels only through policy-versioned generic `StatusView` records targeting the query resolution, chain, export, or ClaimIR as appropriate. Every reported level cites its required scope, evidence snapshot, blocker snapshot, and policy; none is stored in a ClaimIR core record.

#### `dependency_closure: COMPLETE`

This fixed-point query property may be displayed as `DAG_COMPLETE`, but it is not an overall status. Every required external mathematical claim has an admissible source or independent proof path.

#### `MATH_CLOSED`

This label is profile-sensitive and is derived only under the selected `acceptance_profile`; it does not mean ``kernel checked'' by definition. Under `DERIVATION_CHECKED`, it requires `source_fidelity: PASSED`, `dependency_closure: COMPLETE`, `mathematics: SOURCE_DERIVATION_CHECKED`, `formal_alignment: NOT_APPLICABLE`, and no required blocker, dispute, or failure. Under `KERNEL_CHECKED_ALIGNED`, it requires `source_fidelity: PASSED`, `dependency_closure: COMPLETE`, `mathematics: KERNEL_CHECKED`, `formal_alignment: AUTO_ALIGNMENT_PASSED`, and no required blocker, dispute, or failure. It is unavailable under `SOURCE_ONLY` and `PARTIALLY_FORMALIZED`. The selected acceptance-profile thresholds and predicate in Section 5.1.13 are authoritative; target-query prose must not strengthen or weaken them.

#### `SEMANTICALLY_RECONSTRUCTED`

The selected physical interpretation, assumptions, and approximation regimes have a source-grounded `SemanticContract`.

#### `COMPUTATIONALLY_REPRODUCED`

Every numerical result declared load-bearing for the query has an acceptable reproduction record.

#### `VERIFICATION_CLOSED`

Every axis required by the query's declared scope has an acceptable status.

A target may be `MATH_CLOSED` without being scientifically or computationally closed.

### 11.5 Minimal first release

A realistic first release should contain:

```text
1 exact frozen source occurrence
1 source-faithful ScientificClaim
1 ClaimMathBridge with total mapped-or-residual component accounting
1 small set of exact MathClaimIR targets and explicit assumptions/dependencies
1 evidence snapshot with VERIFIED, REFUTED, BLOCKED, UNKNOWN, or NOT_CHECKED dispositions
1 separate BridgeAssessment
1 bounded Root Agent answer
1 adversarial physics review
1 release manifest
```

The first milestone is one complete, auditable round trip from source language to mathematical verification and back to a scoped scientific conclusion. The bridge passes only when source identity is pinned, every relevant component is mapped or retained, assumptions and physical objects match, mathematical dispositions cite exact evidence, residual semantics remain visible, and the projected conclusion is no stronger than its weakest load-bearing result.

A query-relative claim DAG may organize the selected dependencies, and Lean evidence may establish a selected mathematical disposition. A PaperBuildDAG, graph-repair cycle, reusable root optimization, contribution profile, semantic-pruning view, telemetry report, or global `VERIFICATION_CLOSED` result is useful later but is not a V1 acceptance requirement.

### 11.6 Post-V1 coverage and telemetry report

```yaml
coverage:
  target_claims:
    total: 1
    dependency_mapped: 1
    dag_complete: 1
    math_closed: 1
    verification_closed: 0
    blocked: 0

  agents:
    root: 2
    intermediate: 1
    target: 1
    companion_bundles: 0

  mathematics:
    selected_for_formalization: 3
    kernel_checked: 3
    auto_alignment_passed: 2
    auto_alignment_partial: 1

  semantics:
    contracts: 1
    agent_reviewed: 1
    human_reviewed: 0
    empirical_support_partial: 1

  computation:
    eligible_results: 1
    load_bearing: 0
    reproduced: 0

  refinement:
    repair_rounds: 3
    expand_local: 2
    rewire_or_rescope: 1
    escalate_or_block: 0

  reuse:
    accepted_contracts_reused: 2
    external_declarations_reused: 8
    new_local_bridge_declarations: 3
    observed_downstream_reuse: 0

  principal_blockers:
    - Approximation regime has not received human review
```

---

## 12. Post-V1 construction checklist

This checklist governs the larger graph, Lean, reuse, and closure program. It is retained as a post-V1 roadmap and is not a release gate for the bounded bridge prototype.

### Pilot scope

- [ ] One target paper is frozen.
- [ ] One primary target claim is selected.
- [ ] The research question is claim-specific.
- [ ] The maximum dependency and initial-depth scope is declared.
- [ ] Required closure axes are declared.

### Source integrity

- [ ] Source versions are fixed.
- [ ] Artifacts are hashed.
- [ ] Target and root claims have exact anchors.
- [ ] Missing artifacts are declared.
- [ ] Every candidate relation has source or derivation anchors.

### Graph construction

- [ ] Paper-level dependency and epistemic relations are distinguished.
- [ ] Refutation and qualification edges retain direction.
- [ ] Candidate and accepted relations are separated.
- [ ] The query mathematical graph is acyclic.
- [ ] Paper-level projection cycles are represented as CompanionBundles.
- [ ] Multi-premise reasoning uses InferenceStep nodes.

### Claim normalization

- [ ] Central discourse claims and their textual realizations are proposed before query-relative atomic decomposition.
- [ ] Realization clustering remains provisional until source and semantic equivalence are checked.
- [ ] Only claims on the selected query frontier are required to receive full atomic decomposition.
- [ ] Raw LaTeX and expanded standard LaTeX are both preserved.
- [ ] No complete ClaimIR depends on author-defined macros or `head.tex`.
- [ ] Compound claims are split atomically and reconstruction provenance is recorded.
- [ ] Top-level quantifiers and local binders are distinguished.
- [ ] Quantifiers and negations are preserved.
- [ ] Exact and approximate statements are distinguished.
- [ ] Object types and carriers are explicit.
- [ ] Assumptions and conventions are explicit.
- [ ] Mathematical and interpretive claims are separated.
- [ ] Every ClaimIR revision is immutable and contains no verification status.
- [ ] Review-required or failed normalization emits no pretend-complete ClaimIR.

### Lean package routing

- [ ] Coarse field tags are assigned.
- [ ] Candidate package-capability records are retrieved.
- [ ] Exact declaration and type-shape search is performed.
- [ ] Package versions and trust tiers are recorded.
- [ ] Field labels are not used as substitutes for exact object matching.

### Root construction

- [ ] Root stop reasons are recorded.
- [ ] Root status is query-relative.
- [ ] Root claims are not treated as axioms by authority.
- [ ] Root mathematical chains are explicit.
- [ ] Accepted declarations contain no unresolved placeholders.
- [ ] Source-blind backtranslations are generated.
- [ ] Alignment audits are recorded.
- [ ] Root exports are versioned contracts.

### Graph refinement

- [ ] Failed nodes are classified into one of three top-level failures and receive a localized diagnostic tag.
- [ ] Only the affected local graph region is repaired.
- [ ] Repair operations are recorded.
- [ ] Every semantic repair passes the source-meaning gate before publication.
- [ ] Formalization-only fixes do not revise ClaimIR.
- [ ] Helpers inferred from exact recorded premises are `DERIVED_CLAIM`; independently introduced helpers are `SOURCE_INDEPENDENT_PROPOSITION`; neither is attributed to the paper without a source occurrence.
- [ ] Rescoping without source support creates a distinct derived claim.
- [ ] Newly exposed prerequisites update the frontier.
- [ ] Claims are not labeled false from proof-search failure alone.
- [ ] Explicit counterexamples preserve the original source claim and invalidate only dependent outputs.
- [ ] The pilot includes extraction-correction, helper-proposition, and refuted-claim repair traces.

### Forward construction

- [ ] Imports use explicit contracts.
- [ ] Assumptions and object mappings are matched.
- [ ] Conventions are reconciled.
- [ ] Each intermediate paper's local delta is isolated.
- [ ] The target is rebuilt from accepted and conditional imports.

### SemanticContract

- [ ] Physical systems and observables are source-grounded.
- [ ] Model assumptions and approximations are explicit.
- [ ] Validity regimes propagate.
- [ ] Evidence is attached to exact assumptions or regimes.
- [ ] Semantic alignment and empirical support remain separate.
- [ ] Automated review is not mislabeled as human review.

### Numerical reproduction

- [ ] Numerical role is classified as illustrative, supporting, or load-bearing.
- [ ] Inputs, code, environment, and seeds are fixed when reproduction is attempted.
- [ ] Tolerances are declared.
- [ ] Outputs and logs are preserved.
- [ ] Unreproduced load-bearing results remain visibly open.

### Final audit

- [ ] Quantifiers are preserved.
- [ ] Object types have not collapsed.
- [ ] Exact and approximate claims are distinguished.
- [ ] Finite and asymptotic statements are distinguished.
- [ ] Approximation regimes propagate.
- [ ] Gauge- or convention-dependent statements are labeled.
- [ ] Formal correctness is separated from source fidelity and physical applicability.
- [ ] Every formalization, evidence, alignment, and blocker record points to an exact target revision.
- [ ] Aggregate statuses are derived under a named policy and evidence/blocker snapshot.
- [ ] No verification or autoformalization update has mutated a ClaimIR.
- [ ] Candidate edges have not been promoted by confidence alone.
- [ ] Blockers and disputes remain visible.
- [ ] A clean rebuild procedure is documented.
- [ ] Build and reuse telemetry is recorded.

---

## 13. Final Operational Rule

The V1 operational rule is one conservative round trip:

\[
\boxed{
\text{frozen source}
\rightarrow
\text{ScientificClaim}
\rightarrow
\text{ClaimMathBridge}
\rightarrow
\text{MathClaimIR and external evidence}
\rightarrow
\text{BridgeAssessment}
\rightarrow
\text{bounded Root Agent answer}
}
\]

Every relevant source component is either aligned to exact mathematical objects or retained as residual scientific semantics. The bridge records mapping provenance but no truth or acceptance. The assessment cites evidence, preserves `UNKNOWN` and `BLOCKED`, checks physical applicability, and never projects a conclusion stronger than the weakest load-bearing component. AgtXIv prefers an explicit bounded or incomplete answer over a fluent unsupported one.

The minimum useful V1 answer contains:

```text
exact source claim and anchors
+ mapped mathematical definitions, assumptions, dependencies, and conclusion
+ residual physical or empirical semantics
+ exact evidence, blocker, and classification references
+ separate evidence-completeness and scientific-acceptance states
+ bounded conclusion and explicit non-implications
```

Paper interaction graphs, query-relative dependency DAGs, Root Agent build schedules, Lean package reuse, backtranslation, graph repair, and telemetry remain valuable post-V1 infrastructure. They organize and strengthen evidence, but graph reachability, a producer edge, a compiled declaration, or navigation coverage never supplies scientific acceptance.

---

## 14. Related Work and Positioning

The components of AgtXIv have substantial prior art. The project must not claim novelty for theorem search, statement extraction, claim relation classification, premise retrieval, growing formal libraries, long-horizon autoformalization, paper-to-Lean translation, or paper-level agents by themselves.

Its V1 contribution is the conservative round trip from source-faithful `ScientificClaim` through exact `ClaimMathBridge` alignment and external evidence to a bounded `BridgeAssessment`. Its longer-term proposed combination also includes:

- frozen PaperAgents connected by claim-backed directed interactions;
- a query-relative mathematical dependency DAG;
- a derived PaperBuildDAG with CompanionBundle condensation;
- versioned MathContracts and structured MathClaimIR objects;
- candidate-versus-accepted relation semantics;
- source-blind backtranslation and formal-alignment audits;
- verification-guided local graph repair;
- domain-package capability routing;
- minimal blocked-frontier computation;
- reusable QueryResolution receipts and reuse telemetry.

### 14.1 Mathematical statement search, dependency graphs, and claim relations

- **Matlas: A Semantic Search Engine for Mathematics**, arXiv:2604.17484, extracts mathematical statements from papers and textbooks, builds document-level dependency information, recursively unfolds dependencies, and supports natural-language theorem search.
- **TheoremGraph: Bridging Formal and Informal Mathematics**, arXiv:2606.25363, builds statement-level dependency graphs for informal mathematics and Lean projects, records extractor provenance, and links informal statements to formal declarations.
- **ClaimFlow: Tracing the Evolution of Scientific Claims in NLP**, arXiv:2603.16073, represents directed claim-level interactions such as support, extension, qualification, refutation, and background use. Its ontology motivates keeping epistemic relations distinct from mathematical dependency edges.
- **A Semantic Search Engine for Mathlib4**, Findings of EMNLP 2024, maps informal queries to relevant Mathlib declarations.
- **LeanExplore: A Search Engine for Lean 4 Declarations**, arXiv:2506.11085, searches declarations across Mathlib, Physlib, and other Lean packages using semantic, lexical, and graph-based ranking.

These systems can provide candidates. AgtXIv treats their outputs as retrieval infrastructure rather than accepted verification records.

### 14.2 Premise retrieval and growing verified libraries

- **LeanDojo: Theorem Proving with Retrieval-Augmented Language Models**, arXiv:2306.15626, extracts fine-grained Lean premise annotations and supports retrieval-augmented proving.
- **LEGO-Prover: Neural Theorem Proving with Growing Libraries**, arXiv:2310.00656, adds verified generated lemmas to a reusable skill library.
- **LeanSearch v2: Global Premise Retrieval for Lean 4 Theorem Proving**, arXiv:2605.13137, retrieves groups of scattered premises needed for an entire theorem.
- **The Lean Mathematical Library**, CPP 2020, is the principal shared formal library on which downstream projects can prove only residual local results.
- **The Network Structure of Mathlib**, arXiv:2604.24797, analyzes declaration- and module-level dependencies and motivates declaration-level contracts rather than treating broad module imports as exact proof dependencies.
- **Physlib**, maintained under the Lean community, provides a growing physics- and quantum-information-oriented Lean ecosystem. Its existence motivates `LeanPackageCapabilityRecord` routing, but AgtXIv does not assume that every physics subfield has complete or uniform package coverage.

### 14.3 Autoformalization and long-horizon proof construction

- **Autoformalization with Large Language Models**, arXiv:2205.12615, studies translation from informal mathematics to formal specifications.
- **ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics**, arXiv:2302.12433, provides aligned natural-language and Lean theorem statements and proofs.
- **Consistent Autoformalization for Constructing Mathematical Libraries**, EMNLP 2024, studies retrieval, denoising, equivalence, and correction mechanisms for consistent library construction.
- **LeanMarathon: Toward Reliable AI Co-Mathematicians through Long-Horizon Lean Autoformalization**, arXiv:2606.05400, uses an evolving blueprint, contract-scoped agents, target-fidelity review, and DAG-orchestrated proof and repair. AgtXIv adopts the idea that the blueprint is a shared system of record, while extending it with cross-paper provenance, contract reuse, and query-relative roots.
- **FormalScience: Scalable Human-in-the-Loop Autoformalisation of Science with Agentic Code Generation in Lean**, arXiv:2604.23002, characterizes semantic drift in physics autoformalization, including notational collapse and abstraction elevation. These failure modes motivate `MathClaimIR`, source-blind backtranslation, and explicit alignment audits.
- **MerLean: An Agentic Framework for Autoformalization in Quantum Computation**, arXiv:2602.16554, extracts statements from theoretical quantum-computing papers, produces Lean declarations, and concentrates review on newly introduced definitions and axioms. It is highly adjacent to AgtXIv's local-delta and backtranslation goals.
- **Paper2Agent: Reimagining Research Papers As Interactive and Reliable AI Agents**, arXiv:2509.06917, converts papers and associated code into executable paper-specific agents. AgtXIv therefore does not claim novelty for the PaperAgent interface itself.

### 14.4 Formalized physics and domain packages

- **HepLean: Digitalising High Energy Physics**, arXiv:2405.08863, develops shared Lean infrastructure for high-energy physics and later contributes to the broader Physlib ecosystem.
- **Formalization of Physics Index Notation in Lean 4**, arXiv:2411.07667, develops reusable tensor-index infrastructure.
- **Formalizing Chemical Physics Using the Lean Theorem Prover**, Digital Discovery 2023, demonstrates that selected chemical-physics derivations can be represented and checked in Lean.
- **A Perspective on Interactive Theorem Provers in Physics**, Advanced Science 2025, motivates a community-maintained formal physics library.
- **PhysProver: Advancing Automatic Theorem Proving for Physics**, arXiv:2601.15737, trains a physics-oriented theorem prover using formal physics data.
- **Formalizing the Stability of the Two Higgs Doublet Model Potential into Lean: Identifying an Error in the Literature**, arXiv:2603.08139, illustrates that formalization can expose an error in an upstream physics result.
- **Axioms for Physical Reasoning: Codifying the Seiberg--Witten Solution in Lean**, arXiv:2607.06379, makes physical postulates explicit and tracks which formal consequences depend on them.

AgtXIv does not aim to develop a complete Lean package for every physical subfield. It builds a capability registry over existing packages, routes claims by field and formal object, checks exact declaration compatibility, and constructs only small paper-specific bridges when feasible.

### 14.5 Repository-centered publication protocols

- **Agentic Publication Protocol**, [`PROTOCOL.md` at commit `712c11b5`](https://github.com/LionSR/AgenticPublicationProtocol/blob/712c11b5290de184256166fc63e81d7331c15800/PROTOCOL.md), defines a publication around a public Git repository and a tagged release, requires a verified publication manifest, and applies canonical-location rules to paper, code, data, environment, and reproduction artifacts. AgtXIv adopts its repository-plus-release envelope and non-duplication discipline while retaining claim-level semantic revisions, `TargetRef`, multi-registry snapshots, verification semantics, and cross-repository scientific DAGs.

### 14.6 Positioning statement

Beyond the bounded V1 bridge, AgtXIv is not another general theorem search engine, paper chatbot, or universal autoformalizer. Its longer-term architecture is a verification-aware incremental query planner and build system over candidate literature graphs and formal libraries:

```text
candidate claim and relation extraction
→ constrained schema and source grounding
→ directed PaperInteractionGraph
→ query-relative MathClaimDependencyDAG
→ exact contract and package resolution
→ Lean construction and source-blind backtranslation
→ formal-alignment audit
→ verification-guided local graph repair
→ accepted and conditional closure
→ minimal blocked frontier
→ reusable QueryResolution receipt
```

The post-V1 research question is:

> Given release-bound PaperAgents, noisy candidate claim relations, formal declarations, semantic records, and heterogeneous verification states, how can a system compute a trustworthy reusable mathematical closure and a small remaining local delta, while using verification failure to refine the graph without allowing unaccepted status or semantic drift to propagate downstream?

This longer-term optimization question does not replace the V1 product question: whether one exact source claim can be aligned to mathematics and assessed conservatively without losing physical meaning.
