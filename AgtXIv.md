# AgtXIv: Verification-Aware Incremental Search over Scientific Claims

**Status:** Math-first pilot specification
**Version:** 0.4
**Date:** 2026-08-18
**Primary target:** Mathematical claims in theoretical physics and mathematically structured sciences
**Normative paper-source acquisition:** [AgtXIv Paper Source Acquisition](docs/specifications/paper-source-acquisition.md)
**Normative mathematics detail:** [AgtXIv Mathematics Pipeline](docs/specifications/mathematics-pipeline.md)
**Implementation roadmap:** [AgtXIv v1 vertical-slice checklist](docs/roadmaps/v1-implementation-checklist.md)
**Revision note:** [Architecture changes from v0.3 to v0.4](docs/specifications/v0.3-to-v0.4-architecture-changes.md)

`AgtXIv.md` is the system-wide specification. The paper-source acquisition specification governs canonical full-text acquisition, and the mathematics pipeline refines the mathematics profile. Each document is normative within its stated scope; if wording appears to conflict, the system-wide safety and non-promotion rules in this document take precedence.

## Abstract

AgtXIv is an experimental protocol for resolving a scientific query into a reusable, versioned, and partially verified dependency path. Instead of returning only a paper list or a fluent explanation, it returns the target claim's address in a contract registry, the source spans from which the claim was reconstructed, its accepted and conditional imports, the Lean declarations already connected to it, the unresolved frontier, and the local mathematical delta that remains to be built.

The minimum viable system is **math-first**. A frozen paper is represented by a source-bounded `PaperAgent`, but the primary reusable unit is a claim-level `MathContract`. PaperAgents are connected by a typed directed `PaperInteractionGraph`, which may contain cycles because two frozen companion papers can depend on different claims from one another. For a selected query, AgtXIv derives a strict `MathClaimDependencyDAG(q)` containing only the load-bearing mathematical claims required by the target. The corresponding `PaperBuildDAG(q)` is a query-relative build view obtained by projecting the claim DAG to PaperAgents and condensing any paper-level strongly connected components.

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

Physical interpretation, model assumptions, approximation regimes, operational definitions, and empirical support are represented in one `SemanticContract`. They share a natural-language interface but retain distinct internal status axes, especially `semantic_alignment`, `approximation_regime`, and `empirical_support`. Numerical reproduction is an optional claim-attached `ReproductionRecord`; the pilot does not require a computational DAG or Lean verification of numerical software.

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

For a narrowly selected scientific topic, AgtXIv constructs two connected graph views.

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

The first implementation should cover one small scientific dependency closure:

- one target paper;
- one primary target claim;
- one to three query-relative Root Agents;
- zero to three intermediate papers;
- a small number of complete mathematical reasoning chains;
- at least one Lean 4 reconstruction of a load-bearing result;
- at least one automatic source-to-formal backtranslation and alignment audit;
- at least one graph-refinement cycle triggered by a verification failure;
- an optional semantic or numerical record when relevant.

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
- regard a frozen PaperAgent as an axiom or an automatically trusted source.

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

A query-relative projection of the mathematical claim DAG to PaperAgents. If the projection creates a paper-level cycle, the involved papers are grouped into a `CompanionBundle`. The condensation graph of these bundles is the actual build DAG.

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
  paper_id: arxiv:...
  source_bundle: source/...
  math_contracts:
    - math-contract:...
  semantic_contracts:
    - semantic-contract:...
  reproduction_records:
    - reproduction:...
  unmodeled_profiles:
    - semantics
    - computation
```

`unmodeled_profiles` means that the pilot has not modeled those interfaces. It must not be interpreted as `PASSED` or `NOT_APPLICABLE`.

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

Projecting a claim DAG to papers can produce a cycle even when the claim DAG is acyclic. Therefore AgtXIv computes strongly connected components after projection and treats each component as a build unit:

```yaml
companion_bundle:
  id: bundle:...
  query: resolution:...
  agents:
    - agent:paper-A
    - agent:paper-B
  internal_claim_dependencies: []
  external_imports: []
  external_exports: []
```

The condensation graph of these bundles is acyclic.

#### Crosswalk to the mathematics-pipeline graph views

The [mathematics-pipeline specification](docs/specifications/mathematics-pipeline.md) uses four evidence and lifecycle views that cut across the three system-level graphs above. They are related as follows:

| Mathematics-pipeline view | System-level role |
|---|---|
| Oracle candidate graph $G^{O}$ | Claim-level proposals emitted by extraction and search Oracles. It is not the `PaperInteractionGraph`, and its edges are not accepted dependencies. |
| Registered semantic graph $G^{S}$ | The registry-wide claim graph after normalization and evidence recording. For a query $q$, accepted load-bearing mathematical edges in its required closure induce `MathClaimDependencyDAG(q)`. |
| Lean support graph $G^{L}$ | Kernel-checked declaration dependencies and source-to-formal bindings used as evidence. It supports, but does not replace, source fidelity or semantic alignment. |
| Optimized query graph $G^{Q}$ | The proof-guided, query-relative mathematical view after reversible rejection, redundancy marking, reuse, splitting, or premise expansion. |

`PaperBuildDAG(q)` is a separate paper-level projection of the accepted query-relative claim DAG, followed by strongly connected-component condensation. No candidate, paper-level, or Lean-support edge is silently promoted into that build order.

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

### 2.5 Search, registry, and incremental build

AgtXIv should be implemented as a search engine combined with a package manager and an incremental build system.

The expensive offline path is:

```text
freeze sources
→ extract candidate claims
→ ground candidates to source spans
→ validate high-value relations
→ normalize MathClaimIR objects
→ search formal packages and declarations
→ build or repair local formal deltas
→ publish accepted contracts
→ cache verified query closures
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

### 2.6 QueryResolution cache

A query result is preserved as a path receipt:

```yaml
query_resolution:
  id: resolution:...
  query: "..."
  target_agent: agent:...
  resolved_target: math-contract:...

  graph_views:
    paper_interaction_subgraph: graph:...
    math_claim_dag: graph:...
    paper_build_dag: graph:...

  accepted_imports: []
  conditional_imports: []
  dependency_closure: []
  local_delta: []
  blocked_frontier: []
  companion_bundles: []

  dependency_versions: {}
  formal_environment: formal-env:...
  reused_from:
    - resolution:earlier-query

  metrics:
    reused_contracts: 0
    new_contracts: 0
    repair_rounds: 0
```

A cached path may be reused only when its normalized target, assumptions, imported contract versions, formal package versions, and verification requirements remain compatible. A breaking upstream change invalidates only the affected downstream closure.

### 2.7 Progressive standardization

A contract need not reach full acceptance in one pass:

```text
INDEXED
→ SOURCE_GROUNDED
→ NORMALIZED
→ RELATION_VALIDATED
→ DEPENDENCY_MAPPED
→ FORMALLY_CONNECTED
→ AUTO_ALIGNMENT_PASSED
→ ACCEPTED_CONTRACT
```

`HUMAN_SEMANTIC_REVIEWED` is an additional review status, not a mandatory predecessor of every automated contract. An automatically accepted contract must not be labeled as human-reviewed.

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

AgtXIv uses several verification layers. They answer different questions and retain separate status axes.

### 3.1 Source and provenance layer

This layer establishes what the authors actually stated.

It records:

- paper identifier and frozen version;
- repository release or source archive when available;
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

The object is unified, but the statuses are not:

```text
semantic_alignment
approximation_regime
empirical_support
```

A correct interpretation can have weak empirical support. Strong empirical agreement can coexist with an ambiguous mapping between the measured quantity and the formal observable.

Human review is represented explicitly when it occurs. Automated semantic alignment is allowed as a pilot output, but it must not be mislabeled as expert review.

### 3.5 Computational reproduction layer

The pilot treats numerical work as an optional claim-attached record rather than a separate DAG. A `ReproductionRecord` may contain:

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

A claim should not be stored simply as `VERIFIED`.

Instead, it has a verification vector, for example:

```yaml
verification:
  source_fidelity: PASSED
  relation_validation: PASSED
  dependency_closure: COMPLETE
  mathematics: KERNEL_CHECKED
  formal_alignment: AUTO_ALIGNMENT_PASSED
  semantic_alignment: AGENT_REVIEWED
  approximation_regime: PARTIALLY_CHECKED
  empirical_support: PARTIAL
  computation: NOT_ATTEMPTED
  human_review: NOT_PERFORMED
```

A downstream system must state which coordinates are required for its claim of closure.

---

## 4. Paper Agents, Root Agents, and Build Units

### 4.1 Paper Agent

A **PaperAgent** is a source-bounded scientific software object representing one frozen paper and its reconstructed local contribution.

It is not merely a chatbot persona. Its answers and actions are constrained by its frozen source objects, accepted imports, candidate and accepted reasoning relations, verification records, and unresolved blockers.

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

The math-first pilot treats `ScientificClaim`, `MathClaimIR`, `MathContract`, `ClaimContract`, and `QueryResolution` as primary reusable objects. PaperAgents, semantic records, reproduction records, package-capability records, and graph-repair records provide provenance and lifecycle context.

### 5.0 ScientificClaim

A `ScientificClaim` is the cross-profile identity of one atomic source-bounded claim.

```yaml
id: claim:paper-id:main-bound
paper_id: arxiv:xxxx.xxxxxv2
kind: theorem
text: >
  Under assumptions A and B, the quantity F is bounded by g(n).
source_anchors:
  - anchor:paper-id:theorem-2
origin: SOURCE_EXPLICIT
profiles:
  mathematics: math-claim-ir:paper-id:main-bound
  semantics: semantic-contract:paper-id:main-bound
  computation: reproduction:paper-id:main-bound
status: NORMALIZED
```

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

`MathClaimIR` is the structured bridge between a source mathematical claim and Lean.

```yaml
id: math-claim-ir:paper-id:main-bound
claim: claim:paper-id:main-bound
source_anchors:
  - anchor:paper-id:theorem-2

quantifiers:
  - binder: rho
    mode: forall
    domain: density_operators_on_H

objects:
  - symbol: H
    semantic_type: finite_dimensional_complex_hilbert_space
  - symbol: rho
    semantic_type: density_operator
    carrier: H
  - symbol: F
    semantic_type: real_valued_functional

assumptions:
  - id: assumption:finite-dimensional
  - id: assumption:rho-normalized

conclusion:
  relation: le
  lhs: F(rho)
  rhs: g(n)

statement_mode:
  exactness: exact
  finite_or_asymptotic: finite
  equality_notions: []

conventions:
  - trace_normalization: standard

unresolved_symbols: []
```

The object type fields are required to detect notational collapse and abstraction elevation. A source state vector must not silently become a complex scalar merely because the resulting Lean theorem is easier to prove.

### 5.2 MathContract

A `MathContract` is the smallest reusable mathematical package:

```yaml
id: math-contract:domain:result
claim_ir: math-claim-ir:domain:result
statement: >
  For every X satisfying assumptions A, conclusion C holds.
kind: theorem
assumptions:
  - math-contract:domain:A
imports:
  definitions: []
  theorems: []
source_manifestations:
  - paper_id: arxiv:...
    anchor: anchor:paper:theorem
formalization:
  status: EXISTING_PROJECT_DECLARATION
  declarations:
    - Namespace.theoremName
  modules:
    - Package.Module
  environment: formal/project
alignment:
  backtranslation: backtranslation:...
  audit: alignment-audit:...
verification_references:
  - verification:...
version: 1.0.0
compatibility: semver
blockers: []
```

Different papers may point to the same normalized contract. Similarity search may propose `candidate_same_as`, `specializes`, or `equivalent_under_assumptions`; it must not assert identity automatically.

The minimum required fields are:

1. a normalized `MathClaimIR`;
2. explicit assumptions;
3. definition and theorem imports;
4. source manifestations;
5. fully qualified Lean declarations when present;
6. a source-blind backtranslation and alignment audit when autoformalized;
7. verification references and blockers;
8. a version and compatibility policy.

### 5.3 SourceAnchor

A stable location in an immutable source artifact.

```yaml
id: anchor:paper-id:theorem-2
paper_id: arxiv:xxxx.xxxxxv2
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
id: anchor:paper-id:pdf-p7-eq12
paper_id: doi:...
artifact: paper.pdf
artifact_hash: sha256:...
location:
  page: 7
  equation: "12"
  bounding_box: [72, 214, 518, 296]
```

### 5.4 CandidateRelation

A candidate relation is never accepted solely because an extractor emitted it.

```yaml
id: relation-candidate:paper-A:C3--paper-B:T2
source_claim: claim:paper-A:C3
target_claim: claim:paper-B:T2
relation_type: imports_theorem
direction:
  from: claim:paper-A:C3
  to: claim:paper-B:T2
source_anchors:
  - anchor:paper-A:citation-context
  - anchor:paper-A:local-derivation
extractor:
  model: ...
  version: ...
  confidence: 0.82
validator:
  verdict: AMBIGUOUS
  reason: >
    The citation supplies both a definition and a theorem; the exact imported
    object is not yet isolated.
status: CANDIDATE
```

For dependency edges, direction means "the source claim depends on or imports the target claim." Epistemic relations retain their ordinary direction, such as `new_claim --refutes--> old_claim`.

### 5.5 InferenceStep

An `InferenceStep` is a first-class graph node representing one inspectable transformation from joint inputs to outputs.

```yaml
id: inference:paper-id:017
inputs:
  - equation:eq-7
  - assumption:weak-coupling
outputs:
  - equation:eq-8
operation: approximation
justification:
  description: >
    Expand to second order in lambda and discard terms of order lambda^3.
  retained_order: 2
  discarded_order: "O(lambda^3)"
active_assumptions:
  - assumption:small-lambda
validity_regime:
  - "|lambda| << 1"
source_anchors:
  - anchor:paper-id:eq7-to-eq8
formal_links:
  - Namespace.intermediateIdentity
verification_records:
  - verification:step-017-symbolic
status: PARTIALLY_VERIFIED
```

Initial operation vocabulary:

```text
definition_expansion
algebra
substitution
logical_inference
theorem_application
citation_import
approximation
limit
symmetry_or_conservation
dimensional_argument
numerical_evaluation
physical_interpretation
unresolved
```

### 5.6 VerificationRecord

A scoped record of one check.

```yaml
id: verification:step-017-symbolic
target: inference:paper-id:017
method: symbolic_algebra
checker: independent-script
checker_version: git:abc123
result: PASSED
scope:
  checked:
    - series expansion through second order
    - coefficient equality
  not_checked:
    - rigorous remainder bound
assumptions:
  - lambda is real
  - denominator is nonzero
environment:
  python: "3.13"
  sympy: "1.x"
evidence:
  - verification/logs/step-017.txt
notes: >
  The algebraic truncation was reproduced. The physical regime in which the
  neglected remainder is small remains only partially reviewed.
```

### 5.7 SemanticContract

A `SemanticContract` combines physical-semantic reconstruction and evidence linkage while preserving separate internal status axes.

```yaml
id: semantic-contract:paper-id:claim-C
claim: claim:paper-id:claim-C
source_anchors:
  - anchor:paper-id:claim-C

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
  - id: semantic-assumption:weak-coupling
    statement: ...
    regime: ...

approximations:
  - method: perturbation
    control_parameter: lambda
    retained_order: 2
    discarded_order: "O(lambda^3)"

conventions:
  - ...

checks:
  dimensional_consistency: PASSED
  symmetry_compatibility: PARTIAL
  limiting_cases: PARTIAL

evidence:
  - evidence:experiment-1

status:
  semantic_alignment: AGENT_REVIEWED
  approximation_regime: PARTIALLY_CHECKED
  empirical_support: PARTIAL
  human_review: NOT_PERFORMED
```

### 5.8 EvidenceRecord

An `EvidenceRecord` is a lightweight record attached to a semantic assumption, regime, or conclusion.

```yaml
id: evidence:experiment-1
target:
  semantic_contract: semantic-contract:paper-id:claim-C
  component: semantic-assumption:weak-coupling
source_anchors:
  - anchor:experiment-paper:figure-3
evidence_type: experiment
system_or_sample: ...
protocol: ...
observable: ...
parameter_regime: ...
uncertainty_model: ...
reported_result: ...
relation: supports_under_conditions
support_scope: >
  Supports the approximation only for the measured parameter window.
status: SOURCE_GROUNDED
```

Evidence does not automatically prove a mathematical theorem or validate an approximation outside the recorded regime.

### 5.9 ReproductionRecord

A numerical or computational record attached to one claim.

```yaml
id: reproduction:paper-id:result-R
claim: claim:paper-id:result-R
role: LOAD_BEARING
source_code:
  repository: ...
  commit: ...
data:
  identifier: ...
  hashes: []
environment:
  lockfile: ...
parameters: {}
random_seed: ...
command: ...
reported_output: ...
reproduced_output: ...
tolerance: ...
verdict: NOT_ATTEMPTED
artifacts: []
```

The record has no mandatory internal DAG and no Lean requirement.

### 5.10 LeanPackageCapabilityRecord

A `LeanPackageCapabilityRecord` supports domain routing and exact object matching.

```yaml
id: lean-capability:quantum-information-finite
package:
  repository: ...
  commit: ...
  lean_toolchain: ...
  build_targets:
    - QuantumInfo

field_tags:
  - quantum_information
  - finite_dimensional_quantum_mechanics

object_coverage:
  - density_operator
  - quantum_channel
  - measurement
  - entropy
  - resource_theory

declaration_index: registry/declarations.jsonl

trust:
  tier: COMMUNITY_CURATED
  build_status: PASSED
  sorry_audit: REVIEWED
  axiom_policy: REVIEWED
  maintenance: ACTIVE

compatibility:
  mathlib_commit: ...
  tested_imports: []

paper_to_lean_mappings: []
known_gaps: []
```

Suggested trust tiers:

```text
MATHLIB_OR_CORE_CURATED
COMMUNITY_CURATED
COMMUNITY_STABLE
ALPHA_OR_EXPERIMENTAL
STANDALONE_AUDITED
PROTOTYPE
```

Field classification is a routing prior. Exact claim-object and declaration matching is the final selection criterion.

### 5.11 GraphRepairRecord

A local graph-repair transaction.

```yaml
id: graph-repair:resolution-id:round-03
query_resolution: resolution:...
iteration: 3
target_node: math-contract:...
failure_class: ALIGNMENT_FAILURE
diagnostic_tags:
  - lost_normalization_assumption
  - conclusion_too_strong
operation: REWIRE_OR_RESCOPE
before:
  graph_hash: sha256:...
actions:
  - restore_assumption: assumption:normalized-observable
  - replace_edge: relation-candidate:...
  - rescope_claim: math-claim-ir:...
after:
  graph_hash: sha256:...
new_frontier: []
verdict: APPLIED
```

### 5.12 ClaimContract

A claim exported by one Agent and imported by another.

```yaml
id: export:root-agent:theorem-T
provider_agent: agent:root-paper
claim: claim:root-paper:theorem-T
math_contract: math-contract:root-paper:theorem-T
assumptions:
  - assumption:finite-dimensional-space
  - assumption:positivity
validity_regime: []
formalization:
  system: Lean4
  declaration: RootPaper.TheoremT
  status: KERNEL_CHECKED
alignment:
  status: AUTO_ALIGNMENT_PASSED
verification:
  source_fidelity: PASSED
  mathematics: KERNEL_CHECKED
  semantic_alignment: NOT_APPLICABLE
provenance:
  source_anchors:
    - anchor:root-paper:theorem-T
version: 1.0.0
```

An importer must not use the conclusion without importing the contract's assumptions, object mappings, and scope.

### 5.13 PaperAgentManifest

```yaml
agent:
  id: agent:paper-id
  paper_id: arxiv:xxxx.xxxxxv2
  roles:
    - root
    - intermediate
    - target

source:
  canonical_artifact: source/main.tex
  source_hashes: source/source-hashes.json

paper_graph:
  interactions: graph/paper-interactions.jsonl

imports:
  - contract: export:ancestor-agent:claim-A
    assumption_match: reviews/import-A.yaml

local_delta:
  claims: knowledge/claims.jsonl
  math_claim_ir: knowledge/math-claim-ir/
  inference_steps: reasoning/inference-steps.jsonl

verification:
  records: verification/records.jsonl
  lean_project: formal/lean/
  semantic_contracts: semantic/
  reproductions: computational/reproductions/
  reviews: reviews/

exports:
  - exports/claim-C.yaml

unresolved:
  - blockers/blocker-001.yaml
```

---

## 6. Verification Semantics

### 6.1 Source origin

Every claim must declare its origin:

```text
SOURCE_EXPLICIT
SOURCE_IMPLICIT
CITATION_REPORTED
AGENT_NORMALIZED
AGENT_INFERRED
MATHEMATICALLY_DERIVED
COMPUTATIONALLY_REPRODUCED
HUMAN_INTERPRETED
```

A derived statement must not inherit `SOURCE_EXPLICIT` merely because its premises are source-explicit.

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
- mark the branch `BLOCKED`, `DISPUTED`, or `SOURCE_GAP`.

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

#### Source fidelity

```text
UNCHECKED
PASSED
PARTIAL
MISALIGNED
BLOCKED
```

#### Relation validation and dependency closure

```text
CANDIDATE
SOURCE_GROUNDED
VALIDATED
COMPLETE
INCOMPLETE
BLOCKED
DISPUTED
```

#### Mathematics

```text
NOT_APPLICABLE
UNCHECKED
SOURCE_DERIVATION_CHECKED
PARTIALLY_FORMALIZED
KERNEL_CHECKED
FAILED
BLOCKED
```

#### Formal alignment

```text
UNCHECKED
BACKTRANSLATED
AUTO_ALIGNMENT_PASSED
AUTO_ALIGNMENT_PARTIAL
MISALIGNED
HUMAN_REVIEWED
BLOCKED
```

#### Semantic alignment

```text
UNCHECKED
AGENT_REVIEWED
HUMAN_REVIEWED
CONTESTED
BLOCKED
```

#### Approximation regime

```text
NOT_APPLICABLE
DECLARED_ONLY
PARTIALLY_CHECKED
CHECKED_IN_STATED_REGIME
FAILED
BLOCKED
```

#### Empirical support

```text
NOT_APPLICABLE
UNMODELED
SOURCE_GROUNDED
PARTIAL
SUPPORTED_IN_RECORDED_REGIME
CONTESTED
BLOCKED
```

#### Computation

```text
NOT_APPLICABLE
NOT_ATTEMPTED
REPRODUCED
REPRODUCED_WITH_TOLERANCE
QUALITATIVE_ONLY
FAILED
BLOCKED
```

### 6.8 Overall lifecycle status

A node, chain, relation, or export may have one of:

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
DISPUTED
SUPERSEDED
```

`MATH_CLOSED` means that the declared mathematical dependency closure and local formal delta satisfy the mathematical gates. `VERIFICATION_CLOSED` means only that every verification coordinate required by the declared scope has an acceptable status. Neither label means universal scientific certainty.

### 6.9 Public justification rule

A verification record exposes only concise, independently inspectable reasoning:

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
4. Record the canonical manuscript.
5. Resolve supplements, code, data, and formal artifacts.
6. Build stable anchors for the target claim and its immediate derivation.

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

1. Extract the exact source span.
2. Preserve quantifiers, negations, modality, and exact-versus-approximate status.
3. Resolve all nontrivial symbols.
4. Separate a compound claim into atomic `ScientificClaim` objects.
5. Construct `MathClaimIR` for formalizable components.
6. Record explicit and inherited assumptions.
7. Record object types, carriers, domains, and conventions.
8. Separate the paper's mathematical result from interpretation, evidence, and novelty claims.

#### Output

```text
knowledge/target-claim.yaml
knowledge/target-math-claim-ir.yaml
knowledge/target-symbols.yaml
knowledge/target-assumptions.yaml
```

#### Gate

The normalized claim must be understandable without an undefined symbol, hidden section-wide assumption, or ambiguous object type.

---

### Phase 3: Extract and validate candidate relations

#### Actions

1. Run the constrained claim and relation extractor.
2. Require source anchors for every candidate.
3. Classify the relation as dependency, epistemic, semantic, computational, or background.
4. Validate direction and relation type independently.
5. Keep ambiguous edges as candidates.
6. Add only validated load-bearing mathematical edges to the provisional query DAG.

#### Gate

No relation enters the accepted build graph solely from model confidence or citation presence.

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
ACCEPTED_CONTRACT_REUSED
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
10. Export only claims whose assumptions, scope, provenance, and statuses are explicit.

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

#### Assumption-matching record

```yaml
import_match:
  contract: export:root-agent:theorem-T
  importer: agent:intermediate-paper
  object_mapping:
    root_symbol_X: local_symbol_M
    root_parameter_n: local_parameter_L
  assumptions:
    finite_dimensional:
      status: SATISFIED
      evidence: claim:local:finite-dim
    positivity:
      status: UNRESOLVED
  convention_changes:
    - description: Fourier normalization differs
      reconciliation: inference:normalization-map
  verdict: BLOCKED
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
6. Generate the target exports, verification vector, and limitations.
7. Derive `PaperBuildDAG(q)` from the accepted claim DAG.

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
4. Preserve separate semantic, approximation, and empirical statuses.
5. Create a `ReproductionRecord` only when numerical checking is useful or load-bearing.
6. Classify the numerical role as illustrative, supporting, or load-bearing.

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
blockers and disputes
coverage and reuse telemetry
release manifest
```

#### Release rule

The release must make incompleteness visible. A partial but explicit graph is preferable to a polished narrative that silently bridges unsupported steps.

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

### 8.3 Create the MathClaimIR and alignment contract

Before writing Lean code, create:

```yaml
formalization_contract:
  source_claim: claim:root-paper:T
  source_anchors:
    - anchor:root-paper:T
  math_claim_ir: math-claim-ir:root-paper:T
  normalized_statement: >
    For every X satisfying A and B, conclusion C holds.
  physical_context_removed:
    - interpretation of X as an observable
  assumptions_made_explicit:
    - finite dimensionality
    - nonzero denominator
  intended_lean_declaration: RootPaper.T
  alignment_requirements:
    preserve_quantifiers: true
    preserve_object_types: true
    preserve_exactness: true
    preserve_conclusion_strength: true
  status: READY_FOR_BLUEPRINT
```

This contract is the bridge between frozen source, mathematical normalization, and Lean.

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

A blueprint node contains:

```yaml
blueprint_node:
  id: blueprint:claim-T:lemma-03
  source_claims: []
  target_math_claim_ir: ...
  natural_language_role: ...
  lean_declaration: ...
  imports: []
  children: []
  status: UNPROVED
  failure_class: null
```

The blueprint is initially shallow. It is expanded only when a local node fails.

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

Model B receives only:

- the Lean declaration;
- definitions needed to interpret its types;
- actual imported declarations;
- relevant namespace and notation information.

It does not receive the original source claim during backtranslation.

It outputs:

```yaml
backtranslation:
  id: backtranslation:RootPaper.T
  lean_declaration: RootPaper.T
  reconstructed_math_claim_ir: ...
  human_readable_statement: >
    ...
  assumptions_detected: []
  object_types_detected: []
  confidence: ...
```

Source blindness forces the backtranslation to expose what the Lean declaration actually encodes rather than merely repeating the paper.

### 8.9 Alignment Auditor

The auditor compares:

```text
frozen source
MathClaimIR
Lean declaration
source-blind reconstructed MathClaimIR
human-readable backtranslation
```

Required checks:

```text
quantifier_delta
object_type_delta
assumption_delta
domain_and_codomain_delta
exactness_delta
finite_asymptotic_delta
normalization_delta
conclusion_strength_delta
edge_case_delta
```

Example record:

```yaml
alignment_audit:
  id: alignment-audit:RootPaper.T
  source_claim: claim:root-paper:T
  lean_declaration: RootPaper.T
  verdict: MISALIGNED
  differences:
    - field: object_type
      source: quantum_state_vector
      lean: complex_scalar
      severity: CRITICAL
    - field: conclusion
      source: Hilbert-space normalization identity
      lean: scalar conjugation identity
      severity: CRITICAL
  repair_recommendation: REWIRE_OR_RESCOPE
```

A round-trip theorem equivalence check may be added, but it is one signal among several.

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

The Refiner must not invent new source claims without marking them `AGENT_INFERRED`. It must not silently weaken a theorem merely to obtain a proof.

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

Status levels remain explicit:

```text
LEAN_KERNEL_CHECKED
AUTO_ALIGNMENT_PASSED
CROSS_MODEL_ALIGNMENT_PASSED
HUMAN_SEMANTIC_REVIEWED
```

`AUTO_ALIGNMENT_PASSED` does not imply `HUMAN_SEMANTIC_REVIEWED`.

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

A mathematical claim may be exported as `KERNEL_CHECKED` only when its Lean declaration builds without placeholders and its axioms are documented.

It may be exported as `AUTO_ALIGNMENT_PASSED` only when:

- the source claim and `MathClaimIR` are anchored;
- the source-blind backtranslation has been generated;
- no critical quantifier, object-type, assumption, exactness, or conclusion-strength mismatch remains;
- any accepted rescoping is explicit and versioned.

A human review status is added only when a qualified reviewer has actually reviewed the alignment.

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
12. record automatic and human review statuses separately.

The unified contract avoids maintaining separate full schemas for physical semantics and evidence. It does not merge their epistemic statuses.

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

A `SemanticContract` therefore keeps:

```text
semantic_alignment
approximation_regime
empirical_support
```

as separate coordinates.

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

Store commands, logs, generated data, plots, environment lock files, output hashes, and failure traces. A screenshot alone is not a reproduction record.

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

## 10. Repository Layout and Agent Interface

### 10.1 Minimal repository layout

The following is the normative target interface, not a claim that every current pilot path already has this shape. The [repository README](README.md#repository-map) maps the present implementation; migrations must preserve stable identifiers and update consumers atomically.

```text
.
├── AgtXIv.md
├── agtxiv.yaml
├── pilot-scope.yaml
├── README.md
│
├── ScientificClaimRegistry/
│   ├── manifest.json
│   ├── schema/
│   ├── claims/
│   ├── source-anchors/
│   ├── candidate-relations/
│   └── accepted-relations/
│
├── MathContractRegistry/
│   ├── manifest.json
│   ├── contracts/
│   ├── math-claim-ir/
│   ├── mappings/
│   ├── reuse/
│   ├── query-resolutions/
│   └── demo/
│
├── LeanPackageCapabilityRegistry/
│   ├── packages/
│   ├── declaration-index/
│   ├── compatibility/
│   └── audits/
│
├── agents/
│   ├── root-paper-1/
│   │   ├── agent.yaml
│   │   ├── source/
│   │   │   ├── artifacts.json
│   │   │   ├── source-hashes.json
│   │   │   └── anchors.jsonl
│   │   ├── knowledge/
│   │   │   ├── claims.jsonl
│   │   │   └── math-claim-ir/
│   │   ├── reasoning/
│   │   │   ├── blueprint.yaml
│   │   │   └── inference-steps.jsonl
│   │   ├── formal/
│   │   │   └── lean/
│   │   ├── alignment/
│   │   │   ├── backtranslations/
│   │   │   └── audits/
│   │   ├── semantic/
│   │   │   ├── contracts/
│   │   │   └── evidence/
│   │   ├── computational/
│   │   │   └── reproductions/
│   │   ├── verification/
│   │   │   ├── records.jsonl
│   │   │   └── logs/
│   │   ├── reviews/
│   │   ├── exports/
│   │   └── blockers/
│   │
│   ├── intermediate-paper-1/
│   └── target-paper/
│
├── graph/
│   ├── paper-interactions.jsonl
│   ├── candidate-claim-relations.jsonl
│   ├── accepted-claim-relations.jsonl
│   ├── query-math-dags/
│   ├── query-paper-build-dags/
│   └── companion-bundles/
│
├── repairs/
│   └── graph-repair-records.jsonl
│
├── telemetry/
│   ├── build-metrics.jsonl
│   └── reuse-metrics.jsonl
│
├── reviews/
├── coverage.yaml
└── release-manifest.json
```

Source artifacts are read-only after freezing.

### 10.2 PaperAgent query contract

A PaperAgent should expose operations logically equivalent to:

```text
claims()
why(claim_id)
source(object_id)
assumptions(claim_id, transitive=true)
dependencies(claim_id)
imports(claim_id)
local_delta()
verification(claim_id)
formalization(claim_id)
backtranslation(claim_id)
alignment(claim_id)
semantics(claim_id)
reproduction(claim_id)
repairs(claim_id)
blockers(claim_id)
exports()
```

### 10.3 Graph query contract

The system should expose:

```text
paper_interactions(agent_id)
math_dag(query_resolution_id)
paper_build_dag(query_resolution_id)
companion_bundles(query_resolution_id)
accepted_closure(query_resolution_id)
conditional_closure(query_resolution_id)
blocked_frontier(query_resolution_id)
local_delta(query_resolution_id)
```

### 10.4 Response discipline

Every answer from a PaperAgent classifies its basis:

```text
DIRECT_SOURCE
IMPORTED_CONTRACT
DERIVED_FROM_ACCEPTED_CHAIN
AUTOFORMALIZED_AND_ALIGNED
UNVERIFIED_INFERENCE
BLOCKED
DISPUTED
```

Example:

```yaml
answer:
  question: "Why does claim C hold?"
  basis: DERIVED_FROM_ACCEPTED_CHAIN
  chain: chain:target:C
  math_status: MATH_CLOSED
  formal_alignment: AUTO_ALIGNMENT_PASSED
  unresolved:
    - semantic-contract:target:C
  conclusion: >
    The accepted mathematical graph supports the derivation. The physical
    interpretation remains agent-reviewed but has not received human review,
    and the load-bearing numerical result has not been reproduced.
```

A PaperAgent must refuse to present an unsupported inference as a paper claim.

---

## 11. Acceptance Criteria and First Pilot

### 11.1 Acceptance rule for an exported MathContract

An exported mathematical contract is acceptable only if it has:

1. a frozen source version or an explicit independent-proof origin;
2. an exact source anchor or explicit derived provenance;
3. an atomic `ScientificClaim`;
4. a normalized `MathClaimIR` preserving logical form and object types;
5. explicit assumptions and imports;
6. a dependency path to accepted roots or declared external foundations;
7. typed `InferenceStep` nodes;
8. a clean Lean build when the contract is marked formalized;
9. no unresolved placeholders in the accepted closure;
10. documented axioms and declaration dependencies;
11. a source-blind backtranslation;
12. an alignment audit with no unresolved critical mismatch;
13. visible blockers and limitations;
14. a version and compatibility policy.

Human semantic review strengthens the contract but is not silently assumed.

### 11.2 Acceptance rule for a SemanticContract

A semantic contract is acceptable at the declared automated level when:

- the physical system and modeled objects are source-grounded;
- object mappings are explicit;
- assumptions and approximation regimes are recorded;
- evidence is linked to exact assumptions or regimes;
- semantic alignment and empirical support have separate statuses;
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

The query result should report separate closure levels.

#### `DAG_COMPLETE`

Every required external mathematical claim has an admissible source or independent proof path.

#### `MATH_CLOSED`

The target mathematical delta and required imports are kernel-checked and formally aligned to the declared automated threshold.

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
1 target PaperAgent
1–3 Root Agents or reusable root contracts
0–3 intermediate PaperAgents
5–15 accepted ScientificClaims
3–8 InferenceStep chains
1 query-relative MathClaimDependencyDAG
1 query-relative PaperBuildDAG
1–3 Lean declarations
1 or more source-blind backtranslations
1 or more alignment audits
at least 1 GraphRepairRecord
at least 1 LeanPackageCapabilityRecord
0–1 ReproductionRecord
1 adversarial review
1 coverage and reuse-telemetry report
1 release manifest
```

The first milestone is one complete, auditable path from target claim to root dependencies and back to a formally checked target reconstruction, including at least one visible repair cycle.

### 11.6 Coverage and telemetry report

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

## 12. Construction Checklist

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

- [ ] Compound claims are split atomically.
- [ ] Quantifiers and negations are preserved.
- [ ] Exact and approximate statements are distinguished.
- [ ] Object types and carriers are explicit.
- [ ] Assumptions and conventions are explicit.
- [ ] Mathematical and interpretive claims are separated.

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

- [ ] Failed nodes are classified into one of three top-level failures.
- [ ] Only the affected local graph region is repaired.
- [ ] Repair operations are recorded.
- [ ] Newly exposed prerequisites update the frontier.
- [ ] Claims are not labeled false from proof-search failure alone.
- [ ] Explicit counterexamples are preserved when found.

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
- [ ] Candidate edges have not been promoted by confidence alone.
- [ ] Blockers and disputes remain visible.
- [ ] A clean rebuild procedure is documented.
- [ ] Build and reuse telemetry is recorded.

---

## 13. Final Operational Rule

AgtXIv builds scientific knowledge using distinct but connected graph views:

\[
\boxed{
\text{PaperInteractionGraph}
\xrightarrow{\text{target query }q}
\text{MathClaimDependencyDAG}(q)
\xrightarrow{\text{project + condense}}
\text{PaperBuildDAG}(q)
}
\]

Verification proceeds in two directions:

\[
\boxed{
\text{Target}
\xrightarrow{\text{trace backward}}
\text{root contracts and Root Agents}
\xrightarrow{\text{verify and build forward}}
\text{Target}
}
\]

and failures trigger local iteration:

\[
\boxed{
\text{blocked frontier}
\rightarrow
\text{failure classification}
\rightarrow
\text{local graph repair}
\rightarrow
\text{recomputed frontier}
}
\]

Every mathematical package should import explicit versioned contracts, reuse existing declarations before writing local proofs, verify only its residual local delta, generate a source-blind backtranslation, and export only claims whose assumptions, provenance, scope, alignment status, and verification state are public.

PaperAgents organize frozen literature sources. They do not provide trust by authority. The strict mathematical DAG is query-relative. Paper-level directed cycles are allowed and are condensed only for build scheduling. Multi-premise deductions use explicit `InferenceStep` nodes rather than a specialized hypergraph implementation.

`SemanticContract` unifies physical interpretation and evidence linkage as one natural-language-facing object, while preserving separate semantic, approximation, empirical, and human-review statuses. Numerical work remains an optional `ReproductionRecord`, not a required DAG or Lean target.

AgtXIv should prefer an explicit incomplete registry with a visible missing frontier over a fluent but unverifiable account. Its minimum useful answer is a reusable path receipt:

```text
target claim and source address
+ validated claim dependencies
+ accepted and conditional imports
+ checked Lean declarations
+ source-blind backtranslations
+ alignment audits
+ blocked frontier
+ graph-repair history
+ residual local delta
+ dependency and package versions
+ reuse telemetry
```

---

## 14. Related Work and Positioning

The components of AgtXIv have substantial prior art. The project must not claim novelty for theorem search, statement extraction, claim relation classification, premise retrieval, growing formal libraries, long-horizon autoformalization, paper-to-Lean translation, or paper-level agents by themselves.

Its proposed contribution is the verification-aware combination of:

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

### 14.5 Positioning statement

AgtXIv is not another general theorem search engine, paper chatbot, or universal autoformalizer. It is a verification-aware incremental query planner and build system over candidate literature graphs and formal libraries:

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

The central research question is:

> Given frozen PaperAgents, noisy candidate claim relations, formal declarations, semantic records, and heterogeneous verification states, how can a system compute the largest trustworthy reusable mathematical closure and the smallest remaining local delta, while using verification failure to refine the graph without allowing unaccepted status or semantic drift to propagate downstream?
