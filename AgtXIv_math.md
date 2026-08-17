# AgtXIv Mathematics Pipeline

**Status:** Normative design specification for the mathematics profile

**Version:** 0.1

**Date:** 2026-08-16

**Parent specification:** [AgtXIv](AgtXIv.md)

## 0. Purpose

This document defines the iterative, reusable mathematics pipeline

```text
Math Claims Decomposition
→ Oracle DAG Search
→ Lean Proof
→ Proof-Guided DAG Optimization
→ Registry and Query Cache Update
→ Next Target Agent
```

The pipeline converts a target mathematical claim into a typed dependency DAG, resolves its load-bearing mathematical frontier, checks formal claims in Lean where appropriate, optimizes the active DAG using proof evidence, and stores reusable contracts for later Target Agents.

`AgtXIv.md` remains the system-wide specification. This document refines its mathematics profile. The non-promotion, provenance, source-alignment, and scientific-acceptance rules in `AgtXIv.md` remain mandatory. A successful Lean build does not establish physical applicability, empirical support, or scientific acceptance.

The present implementation does not train or fine-tune a DAG-search model. DAG search is an Oracle stage. In practical runs, a general-purpose language model proposes the initial graph. Every Oracle output remains `ORACLE_PROPOSED / UNVERIFIED` until independent gates accept its nodes and edges.

### 0.1 Normative stage contract

| Stage | Required input | Primary output | Promotion gate |
|---|---|---|---|
| Math Claims Decomposition | frozen source or explicit `SOURCE_UNAVAILABLE` record | atomic typed `MathClaim` records | reconstruction, symbol, assumption, and source-fidelity checks |
| Oracle DAG Search | normalized target and allowed dependency types | high-recall candidate DAG | mechanical validation only; no verification promotion |
| Lean Proof | formalization contract and pinned environment | checked declarations and proof-support records | clean build, axiom audit, and statement alignment |
| DAG Optimization | semantic DAG, Lean support graph, and edge evidence | smaller active query DAG plus reversible revisions | meaning, assumptions, provenance, and blockers preserved |
| Iteration and Reuse | updated Registry and query receipt | resolved frontier or explicit fixed-point blocker | compatibility checks and recomputed closure |

Each stage consumes versioned artifacts and emits evidence that the next stage can inspect. No stage may infer a stronger status than its promotion gate permits.

---

## 1. Scope and non-goals

### 1.1 In scope

The mathematics pipeline handles:

- definitions;
- explicit mathematical assumptions;
- scope assumptions that delimit a theorem;
- lemmas, propositions, and theorems;
- mathematical constructions;
- external mathematical foundations;
- mappings from normalized claims to Lean declarations;
- theorem, definition, and scope dependencies;
- unresolved mathematical frontiers;
- query-relative reuse and cache invalidation.

### 1.2 Out of scope

The mathematics pipeline does not by itself verify:

- experimental observations;
- statistical evidence;
- numerical reproduction;
- physical modeling assumptions;
- approximation validity in a physical regime;
- novelty or priority claims;
- the truth of an empirical premise.

Those objects belong to separate typed profiles. Cross-profile links may refer to them, but the mathematics DAG must not silently convert them into kernel-checked mathematical facts.

### 1.3 Safety invariant

The pipeline may increase structure and evidence, but it must never increase scientific acceptance merely because:

- an Oracle proposed an edge;
- a theorem-search system returned a candidate;
- a declaration type-checked under an unverified axiom;
- a graph became smaller;
- a claim received a Registry entry;
- a query reused a previous path.

---

## 2. Core objects and notation

### 2.1 Query

A mathematics query is a tuple

$$
\begin{align}
q
&=(A_T,c_T,v_T,\Gamma_q,E_q),
\end{align}
$$

where:

- $A_T$ is the selected Target Agent;
- $c_T$ is the selected target `MathClaim`;
- $v_T$ is the target source version;
- $\Gamma_q$ is the declared query scope and assumption context;
- $E_q$ is the pinned formal environment.

The same Target Agent may support several queries. A root is therefore query-relative, not a permanent level in a paper hierarchy.

### 2.2 MathClaim

A `MathClaim` is the smallest claim-level object considered by the DAG. It must contain enough information to distinguish source meaning, normalized mathematics, formal meaning, and verification state.

```yaml
math_claim:
  id: claim:...
  kind: definition | assumption | lemma | proposition | theorem | construction | foundation
  owner_agent: agent:... | UNMAPPED
  source_origin: SOURCE_EXPLICIT | SOURCE_IMPLICIT | CITATION_REPORTED | AGENT_NORMALIZED | MATHEMATICALLY_DERIVED
  source_anchors: []
  source_statement: "..."
  normalized_statement: "..."
  quantifiers: []
  domains: []
  assumptions: []
  conventions: []
  exactness: exact | approximate | asymptotic | conditional
  interface_class: MATHEMATICAL
  lean_binding:
    status: UNFORMALIZED
    declarations: []
    modules: []
    environment: null
  blockers: []
  version: 1.0.0
```

A `MathClaim` is not accepted merely because all required fields are present. The fields make the claim inspectable; separate gates determine whether it is source-aligned, formally checked, reusable, or blocked.

### 2.3 Dependency types

The active mathematics DAG uses three primary directed dependency types:

```text
scientific_claim_dependency
    a claim, lemma, theorem, or mathematical foundation used as a premise

definition_dependency
    a definition required to state or interpret the dependent claim

scope_dependency
    an assumption or regime condition under which the dependent claim is asserted
```

Every directed edge points from prerequisite to dependent conclusion:

$$
\begin{align}
(u,v)\in E
&\quad\Longrightarrow\quad
u\text{ is required by }v.
\end{align}
$$

Agent membership is not a mathematical dependency. Paper ownership, source provenance, semantic equivalence, specialization, and derivation-method relations must be stored separately from the three prerequisite edge types.

### 2.4 Four graph views

One mutable graph cannot safely represent proposal, source meaning, formal proof support, and optimized execution at the same time. The pipeline maintains four related views.

#### Oracle candidate graph $G^{O}$

Contains all claims and edges proposed by the Oracle. Its contents are candidates only.

#### Registered semantic graph $G^{S}$

Contains source-aligned or explicitly normalized mathematical interfaces and their accepted, conditional, rejected, or blocked dependency records. This is the canonical mathematical provenance view.

#### Lean support graph $G^{L}$

Contains checked Lean declarations and the declaration dependencies extracted from theorem statements and proof terms in the pinned environment.

#### Optimized query graph $G^{Q}$

Contains the smallest currently justified active graph for resolving query $q$. It reuses accepted contracts and removes only dependencies shown to be unnecessary under the optimization rules in Section 8.

These views satisfy no unconditional equality. In particular,

$$
\begin{align}
G^{O}
&\neq G^{S},\\
G^{L}
&\neq G^{S},\\
G^{Q}
&\neq G^{S}
\end{align}
$$

in general. The views are connected by evidence-carrying mappings rather than silent replacement.

### 2.5 Node and edge states

Oracle and verification states must remain separate.

#### Node lifecycle

```text
ORACLE_PROPOSED
→ NORMALIZED
→ SOURCE_ALIGNED or SOURCE_UNAVAILABLE
→ FORMALLY_STATED
→ KERNEL_CHECKED
→ AUDITED
→ REUSABLE_CONTRACT
```

The path is not necessarily linear. A source-unavailable mathematical claim may become `KERNEL_CHECKED` through an independent Lean proof while retaining a provenance limitation.

#### Edge lifecycle

```text
ORACLE_PROPOSED
→ SCHEMA_VALID
→ RETRIEVAL_SUPPORTED
→ SOURCE_ALIGNED
→ LEAN_SUPPORTED
→ ACCEPTED
```

Alternative terminal or side states are:

```text
CONDITIONAL
REJECTED
REDUNDANT_IN_QUERY_VIEW
BLOCKED
DISPUTED
```

`LEAN_SUPPORTED` means that a checked formal dependency supports the edge. It does not by itself prove that the formal statements match the source claims.

---

## 3. Stage I: strict mathematical claim decomposition

This stage adopts source freezing, target normalization, atomic statement extraction, symbol resolution, assumption extraction, and backward dependency archaeology from `AgtXIv.md`. It makes those steps stricter by requiring typed outputs, reconstruction records, explicit gates, and the same three dependency semantics used by the mathematics DAG application.

### 3.1 Input gate

Decomposition begins from a frozen target source whenever a source exists. The input must identify:

- paper or artifact version;
- immutable artifact hash;
- exact source span;
- target claim boundary;
- local symbol table;
- inherited section assumptions;
- citation context.

If no source exists, the input must say `SOURCE_UNAVAILABLE`. An Oracle reconstruction must not be labeled source-explicit.

### 3.2 Decomposition output

The stage produces:

```text
ClaimDecompositionRecord
MathClaim records
Symbol records
Assumption records
Definition records
Source-to-claim mappings
Candidate local dependency records
```

A decomposition record has the form:

```yaml
claim_decomposition:
  parent_source_claim: source-claim:...
  source_anchor: anchor:...
  children:
    - claim:...
  reconstruction:
    operator: conjunction | implication | equivalence | definition_expansion | ordered_derivation
    statement: "..."
  omitted_text:
    - text: "..."
      reason: interpretation | rhetoric | empirical_content | out_of_scope
  reviewer_status: pending
```

### 3.3 Atomicity rule

A mathematical claim is atomic for the DAG when it has one principal mathematical conclusion under one explicit assumption context. Split a source sentence when it contains independently reusable conclusions, logically separable conjuncts, or a theorem plus a distinct corollary.

Do not split when doing so would:

- change quantifier scope;
- detach a conclusion from a shared condition;
- turn an equivalence into two accepted implications without evidence for both;
- discard exact-versus-approximate qualifications;
- erase an ordering dependency between derivation steps.

The source-level parent may remain as a container even when its mathematical children are split.

### 3.4 Quantifier and domain rule

Every nontrivial variable must have:

- a quantifier;
- a mathematical domain;
- any finiteness or dimensionality condition;
- relevant positivity, nonzero, normalization, regularity, or measurability assumptions;
- a convention when several standard conventions produce different statements.

A claim fails decomposition if its normalized statement depends on an unrecorded pronoun, undefined symbol, hidden section-wide assumption, or unstated convention.

### 3.5 Premise classification rule

For each prerequisite of a dependent claim $v$, classify it by role:

$$
\begin{align}
\operatorname{role}(u,v)
&\in
\{\text{claim premise},\text{definition prerequisite},\text{scope assumption}\}.
\end{align}
$$

Use:

- `scientific_claim_dependency` when $u$ asserts a mathematical fact used to derive $v$;
- `definition_dependency` when $u$ fixes the meaning of an object or predicate in $v$;
- `scope_dependency` when $u$ limits the domain or regime in which $v$ is asserted.

A premise cannot be classified by citation proximity alone. Background citations do not become dependency edges.

### 3.6 Source-fidelity rule

Normalization may rewrite notation and expose assumptions, but it must preserve:

- quantifier order;
- logical polarity and negation;
- equality versus proportionality or approximation;
- finite versus asymptotic scope;
- existence versus construction;
- necessary versus sufficient conditions;
- universal versus generic or almost-everywhere claims.

A materially narrower formalizable statement must be recorded as `SPECIAL_CASE`, not as an equivalent normalization.

### 3.7 Reconstruction completeness

Let $s$ be the source claim and let $D(s)=\{c_1,\ldots,c_m\}$ be its decomposed mathematical claims. Decomposition is complete only when the record explains how the retained children reconstruct the mathematical content of $s$ and accounts for every omitted component.

$$
\begin{align}
\operatorname{DecompositionComplete}(s)
&\iff
\operatorname{Reconstructable}(s;D(s))\\
&\quad\land
\operatorname{AllSymbolsResolved}(D(s))\\
&\quad\land
\operatorname{AllAssumptionsVisible}(D(s))\\
&\quad\land
\operatorname{AllOmissionsClassified}(s).
\end{align}
$$

This is a documentation and review condition. It is not delegated to the Oracle alone.

### 3.8 Decomposition gate

A decomposed node may enter Oracle DAG search only if:

1. its identity is stable;
2. its source origin is explicit;
3. its normalized statement is complete;
4. its assumptions and symbols are resolved;
5. its interface class is mathematical;
6. its decomposition parent and reconstruction record are available;
7. no unsupported strengthening has been introduced.

---

## 4. Stage II: Oracle DAG search

### 4.1 Oracle boundary

DAG discovery is treated as an Oracle because high-recall scientific dependency extraction may require a specialized or fine-tuned model. Model training is outside the current implementation. The operational Oracle is a general-purpose language model constrained to emit typed candidate artifacts.

The Oracle may:

- propose missing mathematical claims;
- propose direct prerequisite edges;
- classify edge types;
- propose source anchors and cited statements;
- propose Registry and Mathlib search queries;
- estimate which nodes are load-bearing.

The Oracle may not:

- accept its own edges;
- promote a source-unavailable claim;
- declare a theorem kernel-checked;
- remove a blocker;
- mark a query DAG complete;
- infer scientific acceptance from graph shape.

### 4.2 Oracle input contract

The Oracle receives only versioned, explicit context:

```yaml
oracle_dag_request:
  query_id: query:...
  target_claim: claim:...
  normalized_target: "..."
  active_assumptions: []
  definitions: []
  source_spans: []
  cited_claim_candidates: []
  registry_candidates: []
  allowed_edge_types:
    - scientific_claim_dependency
    - definition_dependency
    - scope_dependency
  excluded_profiles:
    - empirical
    - computational
    - physical_semantics
```

### 4.3 Oracle output contract

```yaml
oracle_dag_proposal:
  proposal_id: oracle-proposal:...
  model_record: model:...
  prompt_hash: sha256:...
  target_claim: claim:...
  proposed_nodes: []
  proposed_edges:
    - from: claim:premise
      to: claim:dependent
      type: scientific_claim_dependency
      reason: "..."
      evidence_candidates: []
      status: ORACLE_PROPOSED
  unresolved_questions: []
  confidence_for_prioritization_only: {}
```

Confidence may schedule review but must not determine acceptance.

### 4.4 Candidate graph validation

Before scientific review, the proposal must pass mechanical checks:

- all node IDs are unique;
- all edge endpoints exist;
- all edge types are allowed;
- no self-loop exists;
- every edge has a reason;
- every proposed source anchor resolves or is marked unresolved;
- the directed mathematical prerequisite graph is acyclic;
- no edge direction contradicts the prerequisite-to-conclusion convention;
- non-mathematical nodes are excluded or connected through a typed cross-profile relation.

Passing these checks yields `SCHEMA_VALID`, not scientific verification.

### 4.5 Initial DAG policy

The initial graph is

$$
\begin{align}
G_0
&=G^{O}(q),\\
\operatorname{status}(G_0)
&=\texttt{ORACLE_PROPOSED / UNVERIFIED}.
\end{align}
$$

The initial DAG should favor recall over premature minimality. False-positive edges can later be rejected; a missing load-bearing dependency may make an apparently clean proof chain unsound.

### 4.6 Oracle review queue

Review priority should favor:

1. nodes on every candidate route to the target;
2. unresolved external mathematical sources;
3. high-reuse Registry candidates;
4. edges whose removal would disconnect the target;
5. claims with severe assumption mismatch risk;
6. claims for which a quick Mathlib proof appears feasible.

This ordering allocates work. It does not alter verification status.

---

## 5. Stage III: dependency resolution and the unresolved frontier

### 5.1 Required closure

For query $q$, let $C_k(q)$ be the required backward closure in the current accepted-or-conditional semantic graph at iteration $k$.

A mathematical claim belongs to the unresolved external frontier $U_k(q)$ when it is required by $C_k(q)$ and has neither:

- a source found and verified to the required level; nor
- an independently completed Lean proof.

Such a claim is an `Unresolved External Mathematical Source`.

### 5.2 Resolution outcomes

Every member of $U_k(q)$ must end in exactly one state:

```text
SOURCE_FOUND_AND_VERIFIED
INDEPENDENT_LEAN_PROOF_COMPLETED
BLOCKING_UNRESOLVED_CLAIM
```

The third state remains in the blocking frontier.

### 5.3 Mathlib-first policy

Before creating a new Root Agent, perform a bounded search against:

1. accepted project-local declarations;
2. accepted shared AgtXIv contracts;
3. the pinned Mathlib source tree;
4. remote theorem retrieval only as a candidate generator.

Classify search results as:

```text
EXACT_REUSE
ADAPTABLE_NEAR_MATCH
STRUCTURAL_ANALOGY
NO_MATCH
```

Only `EXACT_REUSE` or a checked bridge from `ADAPTABLE_NEAR_MATCH` can resolve the node. A name match, embedding similarity, or remote search score is not proof evidence.

### 5.4 Root Agent creation gate

A dedicated Root Agent should be created only when at least one of the following holds:

- source archaeology is required to identify or align a load-bearing claim;
- several unresolved claims form a coherent source-bounded package;
- the mathematical result requires a substantial reusable local theory;
- physical, computational, or empirical context must be preserved by a source-bounded Agent;
- the result is expected to support several targets and cannot be represented adequately as a small shared `MathContract`.

Do not create a Root Agent merely because an unresolved theorem has no current owner. A small independent Lean bridge should remain a local or shared contract.

---

## 6. Stage IV: Lean proof construction

### 6.1 Formalization contract

Before proof construction, create a statement-alignment contract:

```yaml
formalization_contract:
  math_claim: claim:...
  source_statement: source-claim:... | SOURCE_UNAVAILABLE
  source_anchors: []
  normalized_statement: "..."
  assumptions_made_explicit: []
  conventions: []
  excluded_semantics: []
  intended_declaration: Namespace.theoremName
  environment: formal/project
  reviewer_status: pending
```

The Lean theorem must be compared with the normalized `MathClaim`, not only with an informal summary.

### 6.2 Formal status machine

```text
UNFORMALIZED
→ TYPE_STATED
→ SEARCHED
→ PROOF_CANDIDATE
→ KERNEL_CHECKED
→ AXIOM_AUDITED
→ STATEMENT_ALIGNED
→ REUSABLE_CONTRACT
```

A claim may remain `KERNEL_CHECKED_BUT_MISALIGNED` if the theorem compiles but formalizes a narrower, stronger, weaker, or otherwise different statement.

### 6.3 Pinned environment

Every accepted proof must record:

- Lean version;
- Mathlib revision;
- project manifest;
- imported modules;
- source modules;
- declaration names;
- build command;
- project and artifact hashes.

### 6.4 Proof acceptance

A Lean proof resolves a mathematical claim only if:

1. the declaration has the intended type;
2. the project builds in the pinned environment;
3. the accepted closure contains no `sorry`, `admit`, or equivalent placeholder;
4. the declaration does not depend on a new unverified axiom;
5. an axiom audit is recorded;
6. all imported declarations are available in the pinned environment;
7. the theorem assumptions match the `MathContract`;
8. the source-to-formal alignment is reviewed when a source exists;
9. the declaration is included in the audit surface and verification record.

A theorem proved from an unresolved foundation is conditional:

```text
CONDITIONAL_ON_UNVERIFIED_FOUNDATION
```

It does not remove that foundation from $U_k(q)$.

### 6.5 Proof support extraction

For an accepted Lean declaration $d$, extract:

- constants in its theorem type;
- constants referenced by its proof term;
- project-local declaration dependencies;
- imported module versions;
- axioms reported by the environment.

Let $\operatorname{supp}(d)$ denote the resulting formal support set. Map each support declaration to zero or more versioned `MathContract` IDs. An unmapped support declaration creates a mapping task; it must not be silently ignored.

### 6.6 Local delta rule

For query $q$, let $C(q)$ be the required claim closure and let $R(q)$ be the compatible reusable contracts already present in the Registry. The residual local delta is

$$
\begin{align}
\Delta(q)
&=C(q)\setminus R(q).
\end{align}
$$

Only $\Delta(q)$ should receive new target-local proof work. If a local result becomes broadly reusable, promote it to a shared versioned `MathContract`; do not duplicate the declaration in each Target Agent.

---

## 7. Evidence reconciliation

### 7.1 Three independent questions

For every candidate dependency edge $(u,v)$, answer separately:

1. **Source question:** Does the source state or use $u$ as a prerequisite of $v$?
2. **Mathematical question:** Is $u$ actually sufficient or necessary under the normalized assumptions?
3. **Formal question:** Does the checked Lean proof of $v$ use a declaration mapped to $u$?

The answers need not coincide. A source may include a redundant premise; a Lean proof may use a stronger library theorem; a formalization may omit physical scope that remains scientifically necessary.

### 7.2 Edge evidence record

```yaml
edge_evidence:
  edge: edge:...
  from: claim:u
  to: claim:v
  type: scientific_claim_dependency
  oracle_status: ORACLE_PROPOSED
  source_alignment: PASSED | PARTIAL | FAILED | BLOCKED
  hypothesis_match: PASSED | PARTIAL | FAILED | BLOCKED
  lean_support:
    declaration: Namespace.v
    support_declarations: []
    status: PRESENT | ABSENT | NOT_APPLICABLE | BLOCKED
  disposition: ACCEPTED | CONDITIONAL | REJECTED | REDUNDANT_IN_QUERY_VIEW | BLOCKED
  reasons: []
```

### 7.3 Conflict handling

If evidence conflicts:

- preserve all evidence records;
- do not let Lean evidence overwrite source history;
- do not let source usage overwrite a Lean counterexample or failed proof obligation;
- mark the edge `DISPUTED` or `BLOCKED`;
- create a revised claim only with a new ID and explicit relation to the original.

---

## 8. Stage V: proof-guided DAG optimization

### 8.1 Objective

DAG optimization reduces redundant work and graph complexity while preserving mathematical meaning, provenance, and blockers. It is not permission to delete difficult unresolved premises.

The optimization is lexicographic under hard correctness constraints:

$$
\begin{align}
\min
\Bigl(
&\lvert\text{new Root Agents}\rvert,
\operatorname{ProofCost}(\Delta(q)),
\lvert E_{\mathrm{redundant}}\rvert,
\operatorname{InvalidationRadius}(q)
\Bigr),
\end{align}
$$

subject to:

$$
\begin{align}
\operatorname{TargetMeaningPreserved}
&=\mathrm{true},\\
\operatorname{RequiredAssumptionsPreserved}
&=\mathrm{true},\\
\operatorname{ProvenancePreserved}
&=\mathrm{true},\\
\operatorname{NoBlockerHidden}
&=\mathrm{true}.
\end{align}
$$

The unresolved set may shrink only by resolving a claim or proving that its candidate edge is invalid. It may not shrink because an optimizer deletes an inconvenient edge without evidence.

### 8.2 Allowed transformations

#### Confirm an edge

Promote an edge when source alignment, assumption matching, or Lean support supplies the required evidence.

#### Reject a false-positive Oracle edge

Reject an edge when its proposed prerequisite is not used, not source-supported, and not mathematically required. Record the rejection reason; do not erase the Oracle proposal.

#### Mark an edge redundant in the query view

An accepted semantic edge may be omitted from $G^{Q}$ when another accepted path supplies the dependency and the direct edge is unnecessary for query execution. The edge remains in $G^{S}$ when it records direct source usage or provenance.

#### Replace a local proof by exact reuse

When a compatible accepted declaration already proves the same contract, remove duplicate local proof work and import the versioned contract.

#### Introduce a checked bridge

Use a small local theorem to translate compatible definitions, conventions, or assumptions between an existing declaration and the target contract.

#### Merge equivalent interfaces

Merge query execution nodes only after equivalence under explicit assumptions is checked. Preserve aliases, source manifestations, versions, and specialization relations in the Registry.

#### Split an overloaded node

Split a node when proof construction reveals that it combines logically independent statements or hides an assumption with a separate downstream role.

#### Expand a missing premise

Add a node or edge when Lean proof obligations, source checking, or counterexample analysis exposes an omitted prerequisite.

### 8.3 Forbidden transformations

Optimization must not:

- remove a scope assumption merely because it is absent from an incomplete formalization;
- remove a definition dependency merely because Lean unfolded or inferred it;
- treat an imported module as proof that every theorem in the module is used;
- merge claims based only on similar notation or embeddings;
- replace an exact theorem by a weaker special case without changing the claim ID;
- convert a conditional theorem into an unconditional theorem;
- prune an unresolved source solely to make $U(q)$ empty;
- delete rejected or superseded evidence records;
- infer source equivalence from a shared Lean declaration without alignment review.

### 8.4 Lean-supported pruning test

A candidate theorem-premise edge $(u,v)$ may be removed from the active query graph only if all of the following hold:

1. $v$ rebuilds in the pinned environment without importing the local declaration mapped exclusively to $u$;
2. no declaration in the mapped proof support $\operatorname{supp}(v)$ requires $u$ under the current contract mapping;
3. the statement of $v$ does not retain $u$ as an explicit hypothesis;
4. source and semantic review do not require the direct edge for meaning or provenance;
5. removing the edge does not hide an unresolved assumption or blocker;
6. the target remains reachable from all remaining required prerequisites;
7. the removal receives an evidence record and a reversible graph revision.

Absence from a proof term is not sufficient when $u$ is encoded in a typeclass, definition, quotient, structure field, imported axiom, or deliberately excluded semantic layer.

### 8.5 Transitive reduction

A transitive edge $u\to v$ may be omitted from $G^{Q}$ when an accepted path $u\leadsto v$ already exists and the direct edge is not required for execution. The canonical semantic graph retains the edge when it represents direct source dependence.

Thus optimization produces a view, not destructive historical rewriting:

$$
\begin{align}
G^{Q}_{\mathrm{optimized}}
&\subseteq G^{S}_{\mathrm{active}},\\
G^{S}_{\mathrm{history}}
&\text{ remains append-only by revision.}
\end{align}
$$

### 8.6 Root minimization

Root Agent count is reduced by the following priority order:

```text
exact reusable contract
→ checked local bridge
→ shared contract without a new Paper Agent
→ extend an existing coherent Root Agent
→ create a new Root Agent
```

A lower Root Agent count is desirable only after dependency completeness and source boundaries are preserved.

---

## 9. Stage VI: fixed-point iteration

### 9.1 Iteration state

At iteration $k$, maintain

$$
\begin{align}
S_k(q)
&=\bigl(G^{O}_k,G^{S}_k,G^{L}_k,G^{Q}_k,U_k,\Delta_k,V_k\bigr),
\end{align}
$$

where $V_k$ is the set of verification and audit records.

### 9.2 Transition

One iteration performs:

```text
select unresolved or disputed frontier item
→ search Registry, project declarations, and Mathlib
→ attempt source resolution or Lean proof
→ extract proof support
→ reconcile edge evidence
→ optimize the active query graph
→ discover any new prerequisites
→ update contracts, blockers, and versions
→ recompute closure and cache
```

Let $R_k\subseteq U_k$ be resolved claims and let $N_k$ be newly discovered unresolved prerequisites. Then

$$
\begin{align}
U_{k+1}
&=\bigl(U_k\setminus R_k\bigr)\cup N_k,\\
G^{Q}_{k+1}
&=\operatorname{Optimize}
\bigl(G^{S}_{k+1},G^{L}_{k+1},q\bigr).
\end{align}
$$

The unresolved frontier is not assumed to decrease monotonically. A correct proof attempt may expose a missing premise and temporarily enlarge the DAG.

### 9.3 Completion

A query or its Target Agent completes the mathematics DAG if and only if the recomputed unresolved external frontier is empty:

$$
\begin{align}
\operatorname{DAGComplete}(q)
&\iff U_{*}(q)=\varnothing,
\end{align}
$$

where $U_{*}(q)$ is evaluated after closure recomputation at the current fixed point.

A structural fixed point additionally requires:

$$
\begin{align}
G^{Q}_{k+1}
&\cong G^{Q}_{k},\\
U_{k+1}
&=U_k,\\
\Delta_{k+1}
&=\Delta_k
\end{align}
$$

under unchanged source, Registry, and environment versions.

`DAGComplete` does not imply `VERIFICATION_CLOSED`. Target-local Lean deltas, scope review, and non-mathematical profiles retain separate gates.

### 9.4 Termination outcomes

A run terminates with one of:

```text
DAG_COMPLETE
FIXED_POINT_BLOCKED
BUDGET_EXHAUSTED_WITH_VISIBLE_FRONTIER
DISPUTED
INVALIDATED_BY_UPSTREAM_CHANGE
```

No incomplete outcome may be serialized as success.

### 9.5 Reference algorithm

```text
resolve_math_query(q):
    freeze and normalize q
    decompose the target claim
    G_oracle := OracleDAGBuilder(q)
    validate G_oracle mechanically
    initialize semantic graph and unresolved frontier

    repeat:
        recompute required closure C(q)
        recompute unresolved frontier U(q)

        if unresolved_frontier_at_recomputed_fixed_point(q) is empty:
            optimize query view
            write QueryResolution
            return DAG_COMPLETE

        item := choose_frontier_item(U(q), disputed_edges, pending_deltas)

        candidates := search_registry_project_mathlib(item)
        proof_result := attempt_smallest_checked_proof(item, candidates)

        if proof_result resolves item:
            record proof, audit, mappings, and contract version
        else:
            source_result := attempt_source_resolution(item)
            record source result or explicit blocker

        extract Lean support for every changed declaration
        reconcile Oracle, source, semantic, and Lean evidence
        optimize only with admissible transformations
        add newly exposed prerequisites
        invalidate affected downstream cache entries

        if no admissible action remains:
            return FIXED_POINT_BLOCKED
```

The reference algorithm specifies state transitions, not a mandatory implementation language.

---

## 10. Cross-Target Agent reuse

### 10.1 Reusable unit

The reusable unit is the versioned `MathContract`, not the whole Paper Agent. A Paper Agent packages source-bounded provenance; a mathematical contract packages a normalized statement, assumptions, imports, formal binding, evidence, version, and blockers.

### 10.2 Compatibility predicate

A contract $c$ is reusable for query $q$ only if:

$$
\begin{align}
\operatorname{Reusable}(c,q)
&\iff
\operatorname{StatementCompatible}(c,q)\\
&\quad\land
\operatorname{AssumptionsCompatible}(c,q)\\
&\quad\land
\operatorname{VersionCompatible}(c,q)\\
&\quad\land
\operatorname{EnvironmentCompatible}(c,E_q)\\
&\quad\land
\operatorname{VerificationSufficient}(c,q)\\
&\quad\land
\neg\operatorname{Blocked}(c).
\end{align}
$$

Similarity is not compatibility. A candidate match must pass exact statement and assumption review.

### 10.3 QueryResolution receipt

Each completed or blocked run writes:

```yaml
query_resolution:
  id: resolution:...
  query_id: query:...
  target_agent: agent:...
  target_contract: math-contract:...
  oracle_proposal: oracle-proposal:...
  accepted_closure: []
  optimized_query_edges: []
  reused_contracts: []
  local_delta: []
  unresolved_external_sources: []
  conditional_imports: []
  rejected_oracle_edges: []
  graph_revision: graph-revision:...
  dependency_versions: {}
  formal_environment: formal-env:...
  status: DAG_COMPLETE | FIXED_POINT_BLOCKED | BUDGET_EXHAUSTED_WITH_VISIBLE_FRONTIER
```

### 10.4 Next-target procedure

For a new query $q_2$:

1. normalize and decompose its target claim;
2. retrieve compatible contracts and prior `QueryResolution` receipts;
3. reuse accepted subclosures without rerunning their completed proof work;
4. rerun assumption and version compatibility checks;
5. construct only the residual local delta $\Delta(q_2)$;
6. merge newly accepted contracts into the shared Registry;
7. update reuse links from $q_2$ to earlier resolutions;
8. preserve Target Agent-specific source and scope records.

The pipeline therefore grows a reusable mathematical DAG without forcing all target papers into one permanent Root hierarchy.

### 10.5 Shared unresolved sources

If several targets depend on the same unresolved claim, create one shared frontier record keyed by normalized contract and version. Resolution work should be scheduled by expected reuse and blocking impact, but scheduling priority must not become a trust score.

A successful shared resolution updates every compatible downstream query. An incompatible assumption context creates a distinct contract or bridge rather than silently reusing the result.

---

## 11. Versioning and invalidation

### 11.1 Contract changes

A contract change is breaking when it modifies:

- normalized conclusion;
- quantifiers;
- assumptions;
- definitions or conventions;
- exactness or approximation regime;
- formal declaration type;
- imported contract versions;
- verification requirements.

Source metadata corrections that do not affect meaning may be non-breaking but still require a new evidence revision.

### 11.2 Local invalidation

When contract $c$ changes, invalidate only cached query closures reachable downstream from $c$ under active accepted or conditional dependency edges.

$$
\begin{align}
\operatorname{Invalidate}(c)
&=\{q:\ c\in C(q)\text{ and compatibility no longer holds}\}.
\end{align}
$$

Unrelated queries remain reusable.

### 11.3 Oracle invalidation

A new Oracle proposal does not invalidate an accepted graph by itself. It creates candidate revisions. Invalidation occurs only when accepted evidence changes a required node, edge, assumption, or contract version.

### 11.4 Environment invalidation

A Lean or Mathlib update requires rebuilding affected declarations. Cached `KERNEL_CHECKED` status is environment-specific and must not be transferred to a new pinned environment without replay.

---

## 12. Required artifacts

A mathematics query run should produce:

```text
math/
├── queries/
│   └── <query-id>.json
├── decomposition/
│   ├── claims.json
│   ├── symbols.json
│   ├── assumptions.json
│   └── reconstruction.json
├── oracle/
│   ├── request.json
│   ├── proposal.json
│   └── model-record.json
├── dag/
│   ├── oracle-candidate.json
│   ├── semantic.json
│   ├── lean-support.json
│   ├── optimized-query.json
│   └── revisions.jsonl
├── search/
│   ├── registry-results.json
│   ├── mathlib-results.json
│   └── reuse-audit.json
├── formal/
│   ├── formalization-contracts.json
│   ├── declaration-mappings.json
│   ├── axiom-audit.json
│   └── verification-records.jsonl
├── optimization/
│   ├── edge-evidence.json
│   ├── transformations.jsonl
│   └── rejected-oracle-edges.json
└── resolutions/
    └── query-resolution.json
```

Every generated artifact must identify its schema version, producer, input hashes, timestamp, and upstream artifact IDs.

---

## 13. Validators and acceptance tests

### 13.1 Decomposition validator

Check:

- stable IDs;
- source origins and anchors;
- explicit quantifiers and domains;
- complete symbol definitions;
- classified assumptions;
- reconstruction records;
- no unclassified omission;
- no cross-profile claim mislabeled as mathematical.

### 13.2 Oracle DAG validator

Check:

- schema validity;
- endpoint existence;
- allowed edge types;
- edge direction;
- acyclicity;
- edge reasons;
- explicit `ORACLE_PROPOSED / UNVERIFIED` status.

### 13.3 Lean validator

Check:

- pinned environment;
- clean build;
- declaration existence;
- theorem type hash;
- no placeholders;
- axiom audit;
- contract alignment;
- proof-support mapping.

### 13.4 Optimization validator

For every graph transformation, check:

- transformation type is allowed;
- before and after graph revisions exist;
- evidence record exists;
- target meaning and assumptions are preserved;
- no blocker disappears without resolution evidence;
- canonical provenance remains available;
- optimized graph remains acyclic;
- query closure is recomputed.

### 13.5 Reuse validator

Check:

- contract versions;
- statement compatibility;
- assumption compatibility;
- environment compatibility;
- blocker state;
- cache receipt provenance;
- local invalidation after breaking changes.

---

## 14. Evaluation metrics

Metrics describe performance; they do not replace correctness gates.

### 14.1 Decomposition

- atomic-claim precision and recall under expert review;
- hidden-assumption rate;
- symbol-resolution completeness;
- source reconstruction completeness;
- unsupported-strengthening count.

### 14.2 Oracle DAG search

- required-edge recall;
- false-positive edge rate;
- unresolved-node discovery recall;
- edge-type accuracy;
- number of unsupported source anchors;
- review effort per accepted edge.

### 14.3 Lean proof

- exact Mathlib reuse rate;
- adaptable near-match closure rate;
- local delta size;
- kernel-checked claim count;
- statement-misalignment rate;
- unexpected-axiom count;
- proof replay success across clean environments.

### 14.4 DAG optimization

- redundant active edges removed with evidence;
- new missing prerequisites discovered;
- Root Agents avoided through exact reuse or local bridges;
- proof work avoided by contract reuse;
- blocker-preservation violations, which must remain zero;
- provenance-loss violations, which must remain zero.

### 14.5 Cross-target reuse

- fraction of a new closure reused;
- residual local delta size;
- cache hit rate after compatibility checks;
- invalidation radius after upstream changes;
- shared unresolved frontiers resolved once for multiple targets.

---

## 15. Pilot implementation order

The minimum implementation should proceed in this order:

1. freeze the current mathematics contract and DAG schemas;
2. implement strict decomposition records and validators;
3. wrap the current general-language-model proposal as an explicit Oracle artifact;
4. separate Oracle, semantic, Lean-support, and optimized query graph views;
5. implement `Unresolved External Mathematical Source` frontier computation;
6. run Registry and Mathlib search before Root Agent creation;
7. connect checked Lean declarations and axiom audits;
8. extract proof-support declarations and map them to contracts;
9. implement non-destructive optimization revisions;
10. write `QueryResolution` receipts and compatibility checks;
11. test reuse on a second Target Agent;
12. measure closure reuse, local delta reduction, and blocker preservation.

Model fine-tuning for DAG search remains a later research task. The pilot should first establish whether strict artifacts, Oracle labeling, proof evidence, and iterative graph optimization can produce reliable reusable closures with a general-purpose model.

---

## 16. Normative invariants

Every conforming mathematics pipeline must preserve the following invariants:

1. Oracle proposals never equal verification.
2. Search results never equal proof.
3. Lean proof never automatically equals source alignment.
4. Source alignment never automatically equals mathematical truth.
5. Graph optimization never deletes provenance.
6. Graph optimization never hides an unresolved blocker.
7. Agent ownership never determines query relevance.
8. Query relevance never determines verification status.
9. A new Root Agent is created only after simpler reuse and local-proof paths are checked.
10. Reuse requires statement, assumption, version, environment, and verification compatibility.
11. Breaking upstream changes invalidate only affected downstream closures.
12. A query DAG is complete if and only if its recomputed unresolved external mathematical source set is empty.
13. `DAGComplete` does not imply `VERIFICATION_CLOSED` or scientific acceptance.
14. Every accepted graph change has a reversible evidence-carrying revision.
15. Every incomplete run exposes its unresolved frontier.

These invariants define the reusable loop: decompose claims strictly, let the Oracle propose broadly, verify narrowly, optimize only from evidence, cache compatible results, and repeat on the next Target Agent.
