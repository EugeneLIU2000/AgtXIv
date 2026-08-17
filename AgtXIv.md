# AgtXIv: Verification-Aware Incremental Search over Scientific Claims

**Status:** Math-first pilot specification  
**Version:** 0.3  
**Date:** 2026-08-16  
**Primary target:** Mathematical claims in theoretical physics and mathematically structured sciences

## Abstract

AgtXIv is an experimental protocol for resolving a scientific theorem query into a reusable, versioned dependency path. Instead of returning only papers, it returns the target claim's address in a mathematical contract registry, its definition and theorem imports, the part already connected to checked Lean declarations, the conditional or blocked frontier, and the local mathematical delta that remains to be built.

The minimum viable system is **math-first**. It does not require every paper to be fully standardized as a complete Paper Agent. A paper may initially contribute only a source manifest and a small set of mathematical contracts. Those contracts record normalized statements, assumptions, imports, source anchors, Lean declarations, verification references, versions, and blockers. Paper Agents remain useful provenance and packaging objects, but the reusable unit is the claim-level `MathContract`, not the entire paper.

The construction begins with a target theorem and traces its load-bearing mathematical dependencies backward until it reaches reusable accepted contracts, explicit external foundations, or a blocked frontier. Verification then runs forward. Root mathematics is imported as a stable proof base; an intermediate paper formalizes only its local delta; the target imports both and formalizes only the remaining target delta. Completed contracts and query paths are cached so later queries reuse previous work instead of rebuilding the same dependency closure.

Longer-term profiles may add computational, physical-semantic, and empirical DAGs. They share artifact IDs, provenance, versions, and non-promotion rules, but they do not force experimental evidence or physical postulates into the same verification semantics as mathematical theorems.

AgtXIv distinguishes four questions that must not be collapsed:

1. **Source fidelity:** What did the paper actually state?
2. **Mathematical correctness:** Does the formal conclusion follow from the stated formal assumptions?
3. **Computational reproducibility:** Can the reported numerical result be independently regenerated?
4. **Physical-semantic alignment:** Does the formal or computational object represent the intended physical system, approximation, and observable?

Lean 4 and a pinned mathlib release form the trusted kernel for formal mathematical derivations. They are not treated as a complete ground-truth oracle for physics. Physical intent, model applicability, approximation validity, and empirical relevance require separate reasoning and review.

---

## 1. Goal and Boundaries

### 1.1 Goal

For a narrowly selected scientific topic, AgtXIv constructs a graph of agents of the form

\[
\text{Root Paper Agent(s)}
\longrightarrow
\text{Intermediate Paper Agents}
\longrightarrow
\text{Target Paper Agent}.
\]

Each exported claim should be supported by a public path

\[
\text{immutable source}
\rightarrow
\text{normalized statement}
\rightarrow
\text{assumptions and imports}
\rightarrow
\text{reasoning steps}
\rightarrow
\text{verification records}
\rightarrow
\text{scoped claim contract}.
\]

The resulting knowledge base is **reasoning-centric**, not merely paper-centric or citation-centric.

### 1.2 Immediate objective

The first implementation should cover one very small scientific dependency closure:

- one target paper;
- one primary target claim;
- one to three Root Agents;
- a small number of intermediate papers;
- a handful of complete reasoning chains;
- at least one Lean 4 reconstruction of a load-bearing mathematical result;
- at least one physical or numerical verification path when applicable.

### 1.3 Non-goals of the pilot

The pilot does not attempt to:

- formalize an entire paper in Lean;
- cover an entire research field;
- infer scientific truth from citation counts;
- replace expert physical judgment;
- convert every paragraph into a knowledge-graph node;
- assign a single scalar trust score to a paper;
- publish private model chain-of-thought;
- treat every cited paper as a dependency;
- regard a successful Lean build as proof that the formalized statement captures the intended physics.

### 1.4 Math-first pilot boundary

The pilot standardizes mathematical interfaces before attempting a universal Paper Agent schema. Its primary graph is a `MathematicsDependencyDAG` whose nodes are definitions, assumptions, lemmas, theorems, constructions, and external mathematical foundations. Its edge types are deliberately narrow:

```text
definition_dependency
assumption_dependency
theorem_import
scope_dependency
specializes
equivalent_under_assumptions
derived_by
```

A paper may initially be represented by:

```yaml
paper_math_package:
  paper_id: arxiv:...
  source_bundle: source/...
  math_contracts:
    - math-contract:...
  math_exports:
    - contract:...
  unmodeled_profiles:
    - computation
    - physical_semantics
    - empirical_evidence
```

`unmodeled_profiles` means that the pilot has not modeled those interfaces. It must not be interpreted as `PASSED` or `NOT_APPLICABLE`.

Other domains may use separate typed graphs:

- a computational workflow DAG for code, data, environments, tolerances, and outputs;
- an experimental evidence DAG for protocols, calibration, samples, statistical models, and observations;
- a provenance graph for papers, source spans, figures, datasets, and revisions.

Cross-layer relations such as `normalizes_to`, `operationalizes`, `numerically_checks`, and `supports_under_model` connect these graphs. AgtXIv standardizes identity, provenance, status propagation, and contracts across profiles; it does not standardize all scientific evidence into one proof notion.

---

## 2. Core Architecture

### 2.1 Two opposite directions

AgtXIv uses two complementary passes.

#### Backward pass: dependency archaeology

Starting from a recent target claim, trace the load-bearing scientific dependencies backward:

\[
\text{Target claim}
\rightarrow
\text{imported theorem, model, approximation, or numerical result}
\rightarrow
\cdots
\rightarrow
\text{Root Agent(s)}.
\]

This pass asks:

- Which earlier result is actually used?
- Which exact claim in the cited paper is imported?
- Are the hypotheses compatible?
- Is the citation load-bearing, methodological, or merely background?
- Where should backward expansion stop?

#### Forward pass: verification build

After the roots have been selected, rebuild the scientific dependency closure forward:

\[
\text{Verified Root exports}
\rightarrow
\text{verified intermediate deltas}
\rightarrow
\text{verified target delta}.
\]

This pass asks:

- Which root claim contracts are available?
- Does the importing paper satisfy their assumptions?
- How are notation, conventions, and regimes translated?
- What new reasoning does the importing paper add?
- Which target conclusions remain blocked?

### 2.2 Architecture diagram

```text
                         TARGET PAPER AGENT
                         target claim C_T
                                ▲
                                │ verified local delta
                                │
                     INTERMEDIATE PAPER AGENT
                    imports root and local claims
                         ▲                 ▲
                         │                 │
                ROOT AGENT R1       ROOT AGENT R2
                mathematical core   physical/numerical core
                         │                 │
                 Lean 4 / mathlib     code + reasoning chain
                         └────────┬────────┘
                                  │
                       verification artifacts
```

### 2.3 Claim-level inheritance

AgtXIv does not represent dependency only as

```text
Paper A CITES Paper B
```

but as

```text
Paper A, Claim A.3
    IMPORTS
Paper B, Theorem B.2
```

with an explicit assumption-matching record.

### 2.4 Search, registry, and incremental build

AgtXIv should be implemented as a search engine combined with a package manager and an incremental build system.

The expensive offline path is:

```text
freeze sources
→ extract candidate statements
→ normalize mathematical contracts
→ build candidate dependency edges
→ connect formal declarations
→ review high-value contracts
→ cache verified closures
```

The online query path is:

```text
normalize theorem query
→ retrieve candidate MathContracts
→ load previous QueryResolution records
→ check contract versions and assumptions
→ reuse the accepted dependency closure
→ locate the missing frontier
→ build only the local delta
→ cache the extended path
```

The global store is a DAG of versioned `MathContract` packages, not a permanent hierarchy of Root, subroot, and subsubroot papers. A contract is a root only relative to a query whose backward expansion stops there.

Search and verification must remain separate. Systems such as theorem search, premise retrieval, and informal/formal matching may propose candidates, but only exact type matching, source alignment, and the configured verification workflow can promote a candidate to a reusable contract.

### 2.5 QueryResolution cache

A query result should be preserved as a path receipt:

```yaml
query_resolution:
  id: resolution:...
  query: "..."
  resolved_target: math-contract:...
  accepted_imports: []
  conditional_imports: []
  dependency_closure: []
  local_delta: []
  blocked_frontier: []
  dependency_versions: {}
  reused_from:
    - resolution:earlier-query
```

A cached path may be reused only when its normalized statement, assumptions, imported contract versions, formal environment, and verification requirements remain compatible. An upstream breaking change invalidates only the affected downstream closure.

### 2.6 Progressive standardization

A contract need not reach full acceptance in one pass:

```text
INDEXED
→ NORMALIZED
→ DEPENDENCY_MAPPED
→ FORMALLY_CONNECTED
→ ACCEPTED_CONTRACT
```

The query planner upgrades only load-bearing frontier nodes. Broad extraction can remain candidate-level; scarce human and formalization effort is reserved for contracts whose closure blocks the selected query or whose expected reuse is high.

---

## 3. Trusted Verification Layers

AgtXIv uses several verification layers. They answer different questions and must remain separate.

### 3.1 Source and provenance layer

This layer establishes what the authors actually stated.

It records:

- paper identifier and version;
- repository release or source archive when available;
- file hashes;
- exact source anchors;
- theorem, equation, figure, table, and paragraph locations;
- cited source versions;
- whether a normalized statement is explicit, implicit, inferred, or derived.

A source check establishes fidelity to a source. It does not establish truth.

### 3.2 Mathematical kernel

For formalizable mathematical cores, AgtXIv uses:

- Lean 4;
- the Lean kernel;
- a pinned mathlib version;
- explicit project and toolchain files;
- kernel-checked theorem declarations;
- a no-unresolved-placeholder policy for accepted exports.

The mathematical kernel answers:

> Under the formal definitions and assumptions encoded in Lean, does the conclusion follow?

It does not by itself answer:

- whether the formal theorem matches the paper's intended statement;
- whether the physical assumptions are reasonable;
- whether an approximation is valid in the claimed regime;
- whether a mathematical parameter corresponds to a measurable quantity;
- whether the selected model is an adequate description of the physical system.

### 3.3 Computational kernel

For numerical or algorithmic claims, the computational layer records:

- authoritative code or an independent implementation;
- exact inputs and parameters;
- software environment;
- random seeds;
- precision and tolerance;
- generated outputs;
- logs and hashes;
- comparison with reported values or figures.

A numerical reproduction may be exact, tolerance-based, qualitative, failed, or blocked.

### 3.4 Physical-semantic layer

This layer reconstructs and reviews:

- physical systems and observables;
- model assumptions;
- conventions and normalization choices;
- gauge or basis dependence;
- approximation regimes;
- perturbative orders;
- dimensional consistency;
- limiting cases;
- physical interpretation of formal statements;
- the boundary between a mathematical theorem and a physical conclusion.

This layer normally requires qualified human review for high-impact conclusions.

### 3.5 No global Boolean verification

A claim should not be stored simply as `VERIFIED`.

Instead, it has a verification vector, for example:

```yaml
verification:
  source_fidelity: passed
  dependency_closure: passed
  mathematics: kernel_checked
  computation: not_applicable
  physical_semantics: reviewed
  approximation_regime: partially_checked
```

---

## 4. Paper Agents and Root Agents

### 4.1 Paper Agent

A **Paper Agent** is a source-bounded scientific software object representing one paper and its verified local contribution.

It is not merely a chatbot persona. Its answers and actions must be constrained by its accepted source objects, imports, reasoning chains, and verification records.

A Paper Agent is modeled as

\[
\mathcal A_i =
(S_i, I_i, \Delta_i, R_i, V_i, E_i, U_i),
\]

where:

- \(S_i\): immutable source bundle and anchors;
- \(I_i\): imported claim contracts from predecessor agents;
- \(\Delta_i\): the paper's local scientific delta;
- \(R_i\): reasoning chains connecting imports and local statements;
- \(V_i\): verification artifacts;
- \(E_i\): exported claim contracts;
- \(U_i\): unresolved questions, blockers, and disputes.

### 4.2 Local scientific delta

A Paper Agent should primarily represent what its paper adds beyond imported results:

- new definitions;
- new assumptions;
- new theorems;
- new derivations;
- new approximations;
- new algorithms or numerical results;
- new physical interpretations;
- new limitations or counterexamples.

Conceptually,

\[
\text{Paper Agent}
=
\text{verified imports}
+
\text{verified local delta}.
\]

### 4.3 Root Agent

A **Root Agent** is a paper agent at which backward expansion stops for a specified target claim and project scope.

A root is not necessarily:

- the chronologically earliest paper;
- the first paper to use a term;
- a paper with no citations;
- a universally foundational work.

Root status is contextual and claim-specific. A paper may be a root for one dependency chain and an intermediate agent for another.

A Root Agent may still depend on:

- Lean and mathlib definitions and theorems;
- basic physical postulates;
- standard constants or datasets;
- established numerical algorithms;
- explicitly declared axioms or accepted background.

These dependencies must be recorded even when they are not expanded into additional Paper Agents.

### 4.4 Root-selection principle

A practical root should satisfy most of the following:

- it contains a load-bearing result actually imported by the target chain;
- it is a primary or near-primary source for that result;
- its core statement can be identified precisely;
- its mathematical core is small enough to reconstruct;
- its physical assumptions can be stated explicitly;
- its numerical evidence, if essential, can be reproduced or bounded;
- further backward expansion would add little value relative to the pilot scope.

Every stop must have a recorded reason.

---

## 5. Minimal Data Model

The math-first pilot treats `MathContract` and `QueryResolution` as primary reusable objects. SourceAnchor, Statement, ReasoningStep, VerificationRecord, ClaimContract, and PaperAgentManifest remain provenance and lifecycle records.

### 5.0 MathContract

A `MathContract` is the smallest reusable mathematical package:

```yaml
id: math-contract:domain:result
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
verification_references:
  - verification:...
version: 1.0.0
blockers: []
```

Different papers may point to the same normalized contract. Similarity search may propose `candidate_same_as`, `specializes`, or `equivalent_under_assumptions`; it must not assert identity automatically.

The minimum required fields are:

1. normalized statement;
2. explicit assumptions;
3. definition and theorem imports;
4. source manifestations;
5. fully qualified Lean declarations when present;
6. verification references and blockers;
7. a version and compatibility policy.

### 5.1 SourceAnchor

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

### 5.2 Statement

An atomic scientific statement.

```yaml
id: statement:paper-id:main-theorem
kind: theorem
text: >
  Under assumptions A1 and A2, conclusion C holds for every finite N >= 1.
logical_form:
  quantifiers:
    - forall: N
      domain: integers N >= 1
  implication:
    hypotheses:
      - assumption:A1
      - assumption:A2
    conclusion: claim:C
symbols:
  - N
  - C
source_anchors:
  - anchor:paper-id:theorem-2
origin: SOURCE_EXPLICIT
```

Recommended `kind` values:

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
limitation
```

### 5.3 ReasoningStep

One inspectable transformation from input statements to output statements.

```yaml
id: step:paper-id:017
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

The vocabulary should be extended only when real chains repeatedly require a missing operation.

### 5.4 VerificationRecord

A scoped record of one check.

```yaml
id: verification:step-017-symbolic
target: step:paper-id:017
method: symbolic_algebra
checker: independent-script
checker_version: git:abc123
result: passed
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
  The algebraic truncation was reproduced. The physical range in which the
  neglected remainder is small remains only partially reviewed.
```

### 5.5 ClaimContract

A claim exported by one agent and imported by another.

```yaml
id: export:root-agent:theorem-T
provider_agent: agent:root-paper
statement: statement:root-paper:theorem-T
assumptions:
  - assumption:finite-dimensional-space
  - assumption:positivity
validity_regime: []
formalization:
  system: Lean4
  declaration: RootPaper.TheoremT
  status: kernel_checked
verification:
  source_fidelity: passed
  mathematics: kernel_checked
  physical_semantics: reviewed
provenance:
  source_anchors:
    - anchor:root-paper:theorem-T
version: "1.0.0"
```

An importer must not use the conclusion without importing the contract's assumptions and scope.

### 5.6 PaperAgentManifest

```yaml
agent:
  id: agent:paper-id
  paper_id: arxiv:xxxx.xxxxxv2
  role:
    - root
    - intermediate
    - target

source:
  canonical_artifact: source/main.tex
  source_hashes: source/source-hashes.json

imports:
  - contract: export:ancestor-agent:claim-A
    assumption_match: reviews/import-A.yaml

local_delta:
  statements: knowledge/statements.jsonl
  chains: reasoning/chains.jsonl

verification:
  records: verification/records.jsonl
  lean_project: formal/lean/
  numerics: computational/
  reviews: reviews/

exports:
  - exports/claim-C.yaml

unresolved:
  - blockers/blocker-001.yaml
```

---

## 6. Verification Semantics

### 6.1 Source origin

Every statement must declare its origin:

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

### 6.2 Unresolved External Mathematical Source

An `Unresolved External Mathematical Source` is a mathematical claim that is required by at least one target dependency closure but has neither a verified source manifestation nor a completed independent Lean proof. The label records unresolved provenance and verification; it does not mean that the claim is unrelated to all Target Agents, and it does not denote an accepted Root. A claim may be upstream of one or several targets while remaining unmapped to a Paper Agent.

Every such mathematical claim must follow exactly one of three resolution paths:

1. **Source found and verified.** Freeze an authoritative source version, record an exact source anchor, match the normalized statement and hypotheses to the source, and check the cited proof or derivation to the level required by the contract. The claim may then receive `SOURCE_FOUND_AND_VERIFIED`. Finding a citation or matching title alone is insufficient.
2. **Independent Lean proof completed.** State the claim precisely in Lean and complete a kernel-checked proof in the pinned environment. The proof must contain no `sorry` or `admit`, must not replace the claim with an `axiom`, and must not import the same unresolved claim through a circular dependency. The verification record must name the checked declaration, modules, Lean and Mathlib versions, assumptions, audit entry, and source-to-formal alignment review. The claim may then receive `INDEPENDENT_LEAN_PROOF_COMPLETED`; the missing historical source remains recorded as a provenance limitation.
3. **Blocking unresolved claim.** If neither of the first two paths succeeds, retain `BLOCKING_UNRESOLVED_CLAIM`. The node remains a `GAP` or `EXTERNAL_UNVERIFIED` frontier, and every target whose required closure contains it must remain `BLOCKED_BY_UNVERIFIED_DEPENDENCY`. A downstream Lean theorem proved only by assuming this claim is `CONDITIONAL_ON_UNVERIFIED_FOUNDATION`, not verification-closed.

The trust gate for a mathematical claim is therefore:

```text
ADMISSIBLE_MATHEMATICAL_CLAIM(c) =
    SOURCE_FOUND_AND_VERIFIED(c)
    OR INDEPENDENT_LEAN_PROOF_COMPLETED(c)

TRUSTWORTHY_REQUIRED_CLOSURE(target) =
    every required mathematical claim c in ancestors(target)
    satisfies ADMISSIBLE_MATHEMATICAL_CLAIM(c)
```

This rule applies to mathematical claims, lemmas, theorems, and load-bearing mathematical foundations. Definitions require precise formalization and type checking rather than a proof that the definition is ``true''. Scope assumptions must remain explicit and scientifically justified; merely declaring an assumption in Lean does not verify it. Empirical and computational claims require their own evidence and reproduction workflows and cannot be promoted solely by Lean type checking.

The Registry and Demo must expose the selected resolution path, its evidence, and its effect on downstream targets. Agent ownership, query relevance, source availability, and mathematical verification are separate fields. No virtual owner, graph highlight, or Registry normalization may promote an unresolved claim.

### 6.3 DAG completion and iterative resolution

**Definition (query-relative DAG completion).** For a query $q$, let $C(q)$ be the required backward dependency closure of its selected target, and let $U(q)\subseteq C(q)$ be the mathematical claims currently classified as `Unresolved External Mathematical Source`. A query, or the Target Agent relative to that query, has completed its DAG if and only if this unresolved set is empty:

$$
\begin{align}
\operatorname{DAGComplete}(q)
&\iff U(q)=\varnothing .
\end{align}
$$

This is the first mandatory completion criterion for a query DAG. It is query-relative: the same external claim may belong to $U(q_1)$ but not to $U(q_2)$. It is also distinct from `VERIFICATION_CLOSED` and scientific acceptance. `DAGComplete` states that every required external mathematical source has taken either the source-verified path or the independent-Lean-proof path; remaining target-local deltas, scope review, computation, physical semantics, and empirical evidence retain their own gates.

DAG construction is therefore iterative rather than a one-pass extraction. At iteration $k$, let $R_k\subseteq U_k(q)$ be the unresolved claims resolved during that iteration, and let $N_k(q)$ be newly discovered external mathematical prerequisites exposed by source checking or Lean proof construction. The next frontier is

$$
\begin{align}
U_{k+1}(q)
&=\bigl(U_k(q)\setminus R_k\bigr)\cup N_k(q),\\
\operatorname{DAGComplete}(q)
&\iff U_k(q)=\varnothing
\quad\text{at a recomputed fixed point.}
\end{align}
$$

Each iteration must update the dependency closure, blockers, verification records, and affected query-cache entries. Resolving one node does not complete the DAG if its proof or source reconstruction reveals another required unresolved premise.

#### Mathlib-first unresolved-source reduction

Before creating a new Root Agent for an unresolved mathematical claim, run a bounded search-and-proof pass against the pinned project declarations and Mathlib environment. This order reduces both the number of Root Agents and the amount of source reconstruction:

1. normalize the unresolved claim as an exact Lean type, including quantifiers, assumptions, domains, and conventions;
2. search the pinned project and Mathlib by declaration name, type shape, and mathematical content, using local search tools first and remote theorem search only for candidate retrieval;
3. check every candidate in the pinned environment and compare its hypotheses and conclusion with the `MathContract`;
4. when an exact theorem or a short transparent bridge suffices, construct the smallest local Lean proof, audit it, and record `INDEPENDENT_LEAN_PROOF_COMPLETED` without creating a new Root Agent;
5. promote a broadly reusable checked result to a versioned shared `MathContract`, while keeping Agent creation separate from theorem reuse;
6. only when the bounded Mathlib pass does not close the claim should the workflow expand source archaeology, create a dedicated Root Agent, or retain `BLOCKING_UNRESOLVED_CLAIM`;
7. recompute $C(q)$ and $U(q)$ after every successful or failed resolution attempt.

A theorem-search hit is not a resolution by itself. The unresolved node leaves $U(q)$ only after the exact declaration or bridge proof compiles without `sorry`, `admit`, or new unverified axioms, appears in the audit surface, and has a verification record whose assumptions match the contract. This policy implements ``search before proving'' and ``prove locally before creating another Root Agent'' without allowing retrieval confidence to become verification status.

### 6.4 Verification axes

Recommended axis values are:

#### Source fidelity

```text
UNCHECKED
PASSED
PARTIAL
MISALIGNED
BLOCKED
```

#### Dependency closure

```text
INCOMPLETE
COMPLETE
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

#### Physical semantics

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

### 6.5 Overall lifecycle status

A node, chain, or export may have one of the following lifecycle states:

```text
PROPOSED
SOURCE_VALIDATED
DEPENDENCY_MAPPED
PARTIALLY_VERIFIED
VERIFICATION_CLOSED
BLOCKED
DISPUTED
SUPERSEDED
```

`VERIFICATION_CLOSED` means only that all dependencies relevant to the declared scope have acceptable statuses. It does not mean universal scientific certainty.

### 6.6 Public justification rule

A verification record should expose only concise, independently inspectable reasoning:

```text
premise
  -> declared operation
  -> intermediate result
  -> check
  -> conclusion
```

Private model deliberation is not part of the scientific record.

---

## 7. End-to-End Construction Workflow

This section is the operational core of the pilot.

### Phase 0: Select a microdomain and target claim

#### Input

A candidate recent paper and a broad scientific interest.

#### Actions

1. Select one claim that is central, concrete, and dependency-rich.
2. Rewrite the research target as a bounded question:

   > Why does paper \(P_T\) conclude \(C_T\), and which parts of the chain can be independently verified?

3. Define the pilot boundary before reading all citations.
4. Estimate whether the dependency closure is small enough.
5. Exclude claims that require inaccessible proprietary data or an unmanageably large formal library for the first pilot.

#### Recommended pilot size

- 2–6 papers in the active dependency closure;
- 5–15 principal statements;
- 3–8 complete reasoning chains;
- 1–3 Root Agents;
- 1–3 formal Lean declarations;
- zero or one essential numerical reproduction task.

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
    - approximation
    - numerical_result
  excluded:
    - broad historical background
    - non-load-bearing citations
  stopping_budget:
    maximum_active_papers: 6
    maximum_root_agents: 3
```

#### Gate

The target must be claim-specific. “Understand the whole paper” does not pass.

---

### Phase 1: Freeze the target source

#### Actions

1. Fix the paper version.
2. Prefer author-provided TeX or repository source when available.
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

No downstream claim may be described as source-checked without a valid anchor to the frozen version.

---

### Phase 2: Identify and normalize the target claim

#### Actions

1. Extract the exact source span.
2. Preserve quantifiers, negations, modality, and exact-versus-approximate status.
3. Resolve all nontrivial symbols.
4. Separate a compound claim into atomic statements.
5. Record explicit and inherited assumptions.
6. Distinguish the paper's result from its interpretation or novelty claim.

#### Output

```text
knowledge/target-claim.yaml
knowledge/target-symbols.yaml
knowledge/target-assumptions.yaml
```

#### Gate

The normalized statement must be understandable without an unrecorded pronoun, undefined symbol, or hidden section-wide assumption.

---

### Phase 3: Perform backward dependency archaeology

#### Actions

For the current claim \(C\), ask:

1. Which local equation, theorem, figure, or computation directly supports \(C\)?
2. Which step is performed in the current paper?
3. Which premise is imported from an earlier paper?
4. What exact statement is imported?
5. Does the cited source prove the same statement under compatible hypotheses?
6. Is the citation background, method, data, contrast, or load-bearing result?

Maintain a dependency frontier:

```text
frontier = [target claim]

while frontier is not empty:
    select one unresolved claim
    reconstruct its direct local derivation
    identify every imported premise
    resolve each premise to a source claim
    add claim-level dependency edges
    either:
        expand the imported claim backward
    or:
        declare its paper a practical root with a stop reason
```

#### Required records

For each imported premise:

```yaml
import_candidate:
  importing_claim: claim:target:C
  cited_paper: arxiv:...
  cited_statement: theorem:ancestor:T
  citation_role: LOAD_BEARING_RESULT
  support_alignment: pending
  hypothesis_match: pending
```

#### Gate

A bibliographic citation alone is not a dependency edge. The imported claim and its role must be identified.

---

### Phase 4: Select Root Agents

#### Actions

1. Group unresolved imported claims by source paper.
2. Determine whether each source paper should be expanded further.
3. Prefer primary sources for load-bearing results.
4. Record why expansion stops.
5. Define the exact exports expected from each root.

#### Valid stop reasons

```text
PRIMARY_SOURCE_REACHED
FORMAL_CORE_SELF_CONTAINED
STANDARD_BACKGROUND_ACCEPTED
FURTHER_EXPANSION_OUT_OF_SCOPE
SOURCE_UNAVAILABLE
FORMALIZATION_COST_EXCEEDS_PILOT
EMPIRICAL_INPUT_TREATED_AS_EXTERNAL
```

#### Output

`roots.yaml`

```yaml
roots:
  - agent: agent:root-1
    expected_exports:
      - theorem:T1
    stop_reason: PRIMARY_SOURCE_REACHED
  - agent: agent:root-2
    expected_exports:
      - numerical_result:R2
    stop_reason: EMPIRICAL_INPUT_TREATED_AS_EXTERNAL
```

#### Gate

Every root must be selected because of a specific target dependency, not merely because it is historically famous.

---

### Phase 5: Build each Root Agent

For every root paper, perform the following.

#### 5A. Freeze and map the source

- fix the source version;
- hash artifacts;
- anchor the core statement;
- anchor its local derivation and assumptions.

#### 5B. Separate the scientific content

Partition the root contribution into:

```text
formal mathematical core
physical assumptions and interpretation
approximation structure
numerical or empirical evidence
```

#### 5C. Reconstruct the reasoning chain

For each root export, construct:

\[
A_1,\ldots,A_k
\rightarrow
S_1
\rightarrow
\cdots
\rightarrow
C_{\mathrm{root}}.
\]

Every arrow must have:

- an operation type;
- a justification;
- active assumptions;
- source anchors;
- a verification status.

#### 5D. Formalize the mathematical core

Where feasible, translate the central mathematical result into Lean 4 according to Section 8.

#### 5E. Reproduce essential numerical evidence

Where the root export depends on a numerical computation, follow Section 9.

#### 5F. Review physical-semantic alignment

Confirm that the formalized and reproduced objects correspond to the intended physical statement.

#### 5G. Export a ClaimContract

The root exports only the claims whose assumptions, scope, provenance, and verification vector are explicit.

#### Gate

A Root Agent is not accepted merely because its Lean file compiles. Source alignment and physical-semantic review remain required.

---

### Phase 6: Build intermediate Paper Agents forward

For each non-root ancestor paper, process dependencies in topological order.

#### Actions

1. Import predecessor ClaimContracts.
2. Check that the importing paper uses the same mathematical object.
3. Map notation and conventions.
4. Check every imported assumption against the local setting.
5. Record strengthened, weakened, or newly introduced assumptions.
6. Reconstruct only the paper's local scientific delta.
7. Verify the local steps.
8. Export new contracts.

#### Assumption-matching record

```yaml
import_match:
  contract: export:root-agent:theorem-T
  importer: agent:intermediate-paper
  mapping:
    root_symbol_X: local_symbol_M
    root_parameter_n: local_parameter_L
  assumptions:
    finite_dimensional:
      status: satisfied
      evidence: statement:local:finite-dim
    positivity:
      status: unresolved
  convention_changes:
    - description: Fourier normalization differs
      reconciliation: derivation:normalization-map
  verdict: BLOCKED
```

#### Gate

A kernel-checked theorem may not be imported if the importer has not established its hypotheses.

---

### Phase 7: Rebuild the target Paper Agent

#### Actions

1. Import all accepted ancestor contracts.
2. verify assumption and convention compatibility;
3. reconstruct the target paper's local delta;
4. apply mathematical, numerical, and physical checks;
5. connect every target conclusion to its dependency closure;
6. preserve blocked branches;
7. generate the target agent's exports and limitations.

#### Output

The target agent should be able to answer:

```text
What does this paper claim?
Why does the target claim follow?
Which earlier claims are imported?
Which assumptions are active?
Which parts were checked in Lean?
Which numerical results were reproduced?
Which physical steps remain interpretative?
Where is the first unresolved dependency?
```

---

### Phase 8: Adversarial audit

The audit should actively search for:

- quantifier drift;
- equality replaced by proportionality;
- exact results replaced by asymptotic ones;
- finite statements replaced by thermodynamic limits;
- stronger imported claims than the cited source supports;
- hidden assumptions;
- circular dependencies;
- approximation orders that disappear downstream;
- gauge-dependent statements interpreted as observables;
- numerical agreement without parameter equivalence;
- formal theorems that describe a narrower or different physical class;
- claims supported only by background citations;
- unresolved Lean axioms or placeholders;
- code paths that do not generate the published figure or value.

Every discovered problem becomes a first-class blocker, limitation, dispute, or corrected statement.

---

### Phase 9: Release the agent graph

#### Required release objects

```text
source manifests and hashes
paper-agent manifests
accepted statements
reasoning chains
imports and exports
Lean project and build logs
numerical code, environments, and outputs
human review records
blockers and disputes
coverage report
release manifest
```

#### Release rule

The release must make incompleteness visible. A partial but explicit graph is preferable to a polished narrative that silently bridges unsupported steps.

---

## 8. Lean 4 Reconstruction Procedure

This procedure applies to a selected mathematical core, not automatically to the whole paper.

### 8.1 Select the formalization boundary

Choose a theorem or lemma for which:

- the statement is load-bearing;
- hypotheses can be made explicit;
- the required mathematical objects are available or feasible to define;
- the result is not dominated by informal physical modeling;
- the formalization effort is proportional to the pilot.

Record what is deliberately excluded.

### 8.1A Search before proving

Before introducing a project-specific lemma:

1. search the pinned Mathlib and project sources by exact type shape and mathematical content;
2. query declaration search or global premise retrieval services when available;
3. inspect the actual declaration, module, assumptions, and version;
4. classify each hit as `EXACT_REUSE`, `ADAPTABLE_NEAR_MATCH`, `STRUCTURAL_ANALOGY`, or `NO_MATCH`;
5. keep only the paper-specific bridge and source-aligned wrapper as local delta.

A remote LeanSearch, LeanGraph, or theorem-matching result is candidate retrieval, not verification. It becomes a dependency only after the exact declaration is available in the pinned environment and its assumptions match the contract.

For every local declaration, record:

```yaml
reuse_audit:
  local_declaration: Paper.localLemma
  queries: []
  exact_reuse: []
  adaptable_candidates: []
  residual_local_delta: >
    The sign-attaining witness remains paper-specific.
```

### 8.2 Create a statement-alignment contract

Before writing Lean code, create:

```yaml
formalization_contract:
  source_statement: statement:root-paper:T
  source_anchors:
    - anchor:root-paper:T
  normalized_mathematical_statement: >
    For every X satisfying A and B, conclusion C holds.
  physical_context_removed:
    - interpretation of X as an observable
  assumptions_made_explicit:
    - finite dimensionality
    - nonzero denominator
  intended_lean_declaration: RootPaper.T
  reviewer_status: pending
```

This contract is the bridge between source physics and formal mathematics.

### 8.3 Pin the environment

The formal project must contain at least:

```text
lean-toolchain
lakefile.toml
lake-manifest.json
Main.lean or a namespaced module tree
```

Record:

- Lean version;
- mathlib commit or release;
- imported modules;
- project hash.

### 8.4 Map definitions

For each source object, decide whether to:

- use an existing mathlib definition;
- define a paper-local structure;
- introduce a typeclass assumption;
- state an axiom only when unavoidable and explicitly approved;
- leave the component outside the formal boundary.

Do not identify two objects merely because their notation is similar.

### 8.5 State the theorem before proving it

The theorem declaration should expose:

- all quantifiers;
- all hypotheses;
- domains and codomains;
- finiteness and positivity assumptions;
- exact versus approximate status;
- relevant conventions encoded in definitions.

A statement that is easier to prove but materially narrower than the source must be labeled as a special case.

### 8.6 Construct the proof

Use mathlib lemmas where they match the source semantics. When introducing intermediate lemmas, link them to the corresponding reasoning-chain steps.

Example linkage:

```yaml
lean_link:
  reasoning_step: step:root-paper:007
  lean_declaration: RootPaper.intermediate_identity
  status: kernel_checked
```

### 8.7 Kernel and placeholder checks

An accepted formal export requires:

1. a clean project build;
2. no `sorry`, `admit`, or equivalent unresolved placeholders in the accepted dependency closure;
3. no unexpected axioms;
4. a recorded `#print axioms` result or equivalent audit for exported declarations;
5. build logs and environment hashes.

Typical commands are recorded in the repository, for example:

```bash
lake build
lake env lean AgtXIv/RootPaper.lean
```

The exact acceptance commands belong in the root agent's manifest.

### 8.8 Semantic-alignment review

After the Lean theorem is proved, compare:

```text
source theorem
normalized theorem
Lean declaration
```

Check for:

- quantifier changes;
- stronger hypotheses;
- weaker conclusions;
- altered equality notions;
- finite/asymptotic substitution;
- normalized/unnormalized substitution;
- excluded edge cases;
- changed coefficient fields;
- lost physical interpretation.

### 8.9 Formal export

A mathematical claim may be exported as `KERNEL_CHECKED` only when:

- the Lean declaration builds in the pinned environment;
- the proof has no unresolved placeholder;
- its axioms are documented;
- the source-to-formal alignment has been reviewed;
- the exported assumptions exactly match the formal declaration.

---

## 9. Physical Reasoning and Numerical Reproduction

### 9.1 Physical reasoning-chain procedure

For every physically meaningful conclusion:

1. Define the physical system.
2. Define the state, observable, or effective degree of freedom.
3. Record conventions and normalization.
4. Identify physical assumptions.
5. Identify mathematical assumptions.
6. Identify approximations and their control parameters.
7. Split the derivation into inspectable steps.
8. Track validity regimes forward.
9. Test dimensions, symmetries, and meaningful limits.
10. Separate mathematical conclusion from physical interpretation.
11. Record expert review and remaining ambiguity.

A physical reasoning step may be accepted without Lean formalization, but it must not be presented as kernel-checked.

### 9.2 Approximation propagation

If a step uses

\[
F(\epsilon) = F_0 + \epsilon F_1 + O(\epsilon^2),
\]

then every dependent claim inherits the approximation unless a later argument removes it.

The graph should record:

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

### 9.3 Minimal physical checks

Apply when relevant:

- dimensional consistency;
- conservation laws;
- symmetry compatibility;
- gauge or basis dependence;
- weak- and strong-coupling limits;
- zero-temperature or classical limits;
- finite-size versus infinite-size distinctions;
- positivity, normalization, and probability bounds;
- behavior at singular or degenerate parameter values.

Passing these checks does not prove a result, but failing one may refute or rescope it.

### 9.4 Numerical-reproduction procedure

#### Freeze inputs

Record:

- code source and commit;
- data version and hash;
- model parameters;
- preprocessing;
- random seeds;
- numerical precision;
- hardware-sensitive settings when relevant.

#### Reproduce the minimal result

Prefer the smallest computation that verifies the load-bearing claim:

- one reported table entry;
- one limiting value;
- one curve point plus a convergence test;
- one figure generated from the released script;
- one independent implementation of the key numerical identity.

#### Compare

Record:

```yaml
comparison:
  reported_value: 0.12345
  reproduced_value: 0.12347
  absolute_error: 0.00002
  tolerance: 0.00010
  verdict: REPRODUCED_WITH_TOLERANCE
```

#### Preserve evidence

Store:

- commands;
- logs;
- generated data;
- plots;
- environment lock files;
- output hashes;
- failure traces.

A screenshot alone is not a numerical reproduction record.

---

## 10. Repository Layout and Agent Interface

### 10.1 Minimal repository layout

```text
.
├── AgtXIv.md
├── agtxiv.yaml
├── pilot-scope.yaml
├── README.md
│
├── MathContractRegistry/
│   ├── manifest.json
│   ├── schema/
│   ├── contracts/
│   ├── mappings/
│   ├── reuse/
│   ├── query-resolutions/
│   └── demo/
│
├── agents/
│   ├── root-paper-1/
│   │   ├── agent.yaml
│   │   ├── source/
│   │   │   ├── artifacts.json
│   │   │   ├── source-hashes.json
│   │   │   └── anchors.jsonl
│   │   ├── knowledge/
│   │   │   ├── statements.jsonl
│   │   │   └── symbols.yaml
│   │   ├── reasoning/
│   │   │   └── chains.jsonl
│   │   ├── formal/
│   │   │   └── lean/
│   │   ├── computational/
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
│   ├── paper-dependencies.json
│   ├── claim-dependencies.json
│   └── accepted-graph.json
│
├── reviews/
├── coverage.yaml
└── release-manifest.json
```

Source artifacts should be treated as read-only after freezing.

### 10.2 Paper Agent query contract

A Paper Agent should expose logically equivalent operations to:

```text
claims()
why(claim_id)
source(object_id)
assumptions(claim_id, transitive=true)
dependencies(claim_id)
imports(claim_id)
local_delta()
verification(claim_id)
reproduce(result_id)
blockers(claim_id)
exports()
```

### 10.3 Response discipline

Every answer from a Paper Agent should classify its basis:

```text
DIRECT_SOURCE
IMPORTED_CONTRACT
DERIVED_FROM_ACCEPTED_CHAIN
UNVERIFIED_INFERENCE
BLOCKED
```

A Paper Agent must refuse to present an unsupported inference as a paper claim.

Example:

```yaml
answer:
  question: "Why does claim C hold?"
  basis: DERIVED_FROM_ACCEPTED_CHAIN
  chain: chain:target:C
  unresolved:
    - step:ancestor:014
  conclusion: >
    The accepted graph supports the derivation through step 13. Step 14 is
    blocked because the imported theorem's positivity hypothesis has not
    been matched to the target notation.
```

---

## 11. Acceptance Criteria and First Pilot

### 11.1 Acceptance rule for an exported claim

An exported claim is acceptable only if it has:

1. a frozen source version;
2. an exact source anchor or an explicit derived origin;
3. a normalized statement preserving logical form;
4. an explicit assumption set;
5. a dependency path to accepted roots or declared external foundations;
6. typed reasoning steps;
7. a scoped verification vector;
8. visible blockers and limitations;
9. a versioned ClaimContract;
10. human physical-intent review when the interpretation is load-bearing.

### 11.2 Acceptance rule for a Root Agent

A Root Agent passes the pilot gate when:

- its expected root export is source-anchored;
- the core derivation has been reconstructed;
- its formalizable mathematical core has either been kernel-checked or explicitly scoped out with a reason;
- essential numerical evidence has been reproduced or marked blocked;
- the physical meaning and assumptions have been reviewed;
- its export contract exposes all assumptions and regimes;
- no blocker affecting the exported conclusion is hidden.

### 11.3 Acceptance rule for the target agent

The target agent passes when:

- every load-bearing import resolves to a versioned contract;
- every imported hypothesis is matched or explicitly blocked;
- the target paper's local delta is separated from inherited results;
- the target reasoning chain reaches the selected roots;
- all verification states are visible;
- the agent can identify the earliest unresolved step;
- the release can be rebuilt from a clean checkout.

### 11.4 Minimal first release

A realistic first AgtXIv release should contain:

```text
1 target Paper Agent
1–3 Root Agents
0–3 intermediate Paper Agents
5–15 accepted scientific statements
3–8 reasoning chains
1–3 Lean theorem declarations
0–1 numerical reproduction package
1 adversarial review
1 coverage report
1 release manifest
```

The first milestone is not broad coverage. It is one complete, auditable path from a target claim to its root dependencies and back to a verified target reconstruction.

### 11.5 Coverage report

```yaml
coverage:
  target_claims:
    total: 1
    dependency_mapped: 1
    verification_closed: 0
    blocked: 1

  agents:
    root: 2
    intermediate: 1
    target: 1

  mathematics:
    selected_for_formalization: 2
    kernel_checked: 1
    partial: 1

  computation:
    eligible_results: 1
    reproduced: 1

  physical_semantics:
    agent_reviewed: 4
    human_reviewed: 2

  principal_blockers:
    - Imported theorem hypothesis not yet matched
```

---

## 12. Construction Checklist

### Pilot scope

- [ ] One target paper is fixed.
- [ ] One primary target claim is selected.
- [ ] The research question is claim-specific.
- [ ] The maximum dependency scope is declared.

### Source integrity

- [ ] Source versions are fixed.
- [ ] Artifacts are hashed.
- [ ] Target and root statements have exact anchors.
- [ ] Missing artifacts are declared.

### Backward archaeology

- [ ] Every load-bearing citation is identified at claim level.
- [ ] Citation roles are classified.
- [ ] Imported statements are matched to cited source statements.
- [ ] Root stop reasons are recorded.

### Root construction

- [ ] Root scientific content is split into mathematics, physics, approximation, and computation.
- [ ] Root reasoning chains are explicit.
- [ ] Lean formalization boundaries are declared.
- [ ] Kernel-checked declarations have no unresolved placeholders.
- [ ] Physical-semantic alignment is reviewed.
- [ ] Root ClaimContracts are versioned.

### Forward construction

- [ ] Imports use explicit contracts.
- [ ] Assumptions are matched.
- [ ] Conventions and notation are reconciled.
- [ ] Each intermediate paper's local delta is isolated.
- [ ] The target agent is rebuilt from accepted imports.

### Numerical verification

- [ ] Inputs, code, environment, and seeds are fixed.
- [ ] Minimal load-bearing results are rerun.
- [ ] Tolerances are declared.
- [ ] Outputs and logs are preserved.

### Final audit

- [ ] Quantifiers are preserved.
- [ ] Exact and approximate claims are distinguished.
- [ ] Finite and asymptotic statements are distinguished.
- [ ] Approximation regimes propagate.
- [ ] Gauge- or convention-dependent statements are labeled.
- [ ] Formal correctness is separated from physical fidelity.
- [ ] Blockers and disputes remain visible.
- [ ] A clean rebuild procedure is documented.

---

## 13. Final Operational Rule

AgtXIv builds scientific knowledge in two directions:

\[
\boxed{
\text{Target}
\xrightarrow{\text{trace backward}}
\text{Root Agent(s)}
\xrightarrow{\text{verify and build forward}}
\text{Target Agent}
}
\]

Every mathematical package should import explicit versioned contracts, reuse existing declarations before writing local proofs, verify only its residual local delta, and export only claims whose assumptions, provenance, scope, and verification state are public. Paper Agents may remain thin provenance containers until a richer domain profile is required.

Never compress a scientific dependency into a simpler edge when omitted assumptions, quantifiers, approximation regimes, conventions, or verification states could change the meaning of the conclusion.

AgtXIv should prefer an explicit incomplete registry with a visible missing frontier over a fluent but unverifiable account of the literature. Its minimum useful answer is not merely a paper list, but a reusable path receipt:

```text
target address
+ accepted and conditional imports
+ checked declarations
+ blocked frontier
+ residual local delta
+ dependency versions
```

---

## 14. Related Work and Positioning

The components of AgtXIv have substantial prior art. The project must not claim novelty for theorem search, statement dependency extraction, premise retrieval, growing formal libraries, or paper-to-Lean translation by themselves. Its proposed contribution is the verification-aware combination: versioned mathematical contracts, query-relative roots, accepted-versus-candidate edge semantics, missing-frontier computation, and reusable query path receipts.

### 14.1 Mathematical statement search and dependency graphs

- **Matlas: A Semantic Search Engine for Mathematics**, arXiv:2604.17484 (2026 preprint), extracts millions of mathematical statements from papers and textbooks, constructs document-level dependency graphs, recursively unfolds dependencies, and supports natural-language theorem search.
- **TheoremGraph: Bridging Formal and Informal Mathematics**, arXiv:2606.25363 (2026 preprint), builds statement-level dependency graphs for informal mathematics and Lean projects, preserves candidate-edge extractor provenance, and links informal statements to formal declarations.
- **A Semantic Search Engine for Mathlib4**, Findings of EMNLP 2024, DOI `10.18653/v1/2024.findings-emnlp.470`, maps informal queries to relevant Mathlib declarations.
- **LeanExplore: A Search Engine for Lean 4 Declarations**, arXiv:2506.11085 (2025 preprint), searches declarations across Mathlib, PhysLean, and other Lean packages using semantic, lexical, and graph-based ranking.

These systems can provide candidate statements, declarations, and dependency edges. AgtXIv should consume them as retrieval infrastructure rather than reproduce their large-scale indexing work.

### 14.2 Premise retrieval and growing verified libraries

- **LeanDojo: Theorem Proving with Retrieval-Augmented Language Models**, arXiv:2306.15626 (2023), extracts fine-grained Lean premise annotations and supports retrieval-augmented proving.
- **LEGO-Prover: Neural Theorem Proving with Growing Libraries**, arXiv:2310.00656 (2023), adds generated verified lemmas to a growing reusable skill library.
- **LeanSearch v2: Global Premise Retrieval for Lean 4 Theorem Proving**, arXiv:2605.13137 (2026 preprint), retrieves groups of scattered premises required for an entire theorem rather than only one similar declaration.
- **The Lean Mathematical Library**, CPP 2020, DOI `10.1145/3372885.3373824`, is the principal example of a shared formal library in which downstream work imports existing definitions and lemmas and proves only new results.
- **The Network Structure of Mathlib**, arXiv:2604.24797 (2026 preprint), analyzes declaration- and module-level dependencies and reports that imported scope can be much broader than declarations actually used. This motivates declaration-level contracts rather than module imports alone.

AgtXIv adds source manifestations, contract versions, blocker propagation, and query cache invalidation to this reuse model.

### 14.3 Autoformalization and paper-level agents

- **Autoformalization with Large Language Models**, arXiv:2205.12615 (2022), studies translation from informal mathematics to formal specifications.
- **ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics**, arXiv:2302.12433 (2023), provides aligned natural-language and Lean theorem statements and proofs.
- **Consistent Autoformalization for Constructing Mathematical Libraries**, EMNLP 2024, DOI `10.18653/v1/2024.emnlp-main.233`, studies retrieval, denoising, and correction mechanisms for more consistent library construction.
- **Paper2Agent: Reimagining Research Papers As Interactive and Reliable AI Agents**, arXiv:2509.06917 (2025 preprint), converts papers and associated code into executable MCP-based agents. Its primary unit is an interactive paper workflow rather than a verification-aware claim contract DAG.

AgtXIv must not claim to be the first system to turn papers into agents. Its narrower distinction is the use of evidence-carrying, versioned claim contracts and incremental verification paths.

### 14.4 Formalized physics

- **HepLean: Digitalising High Energy Physics**, arXiv:2405.08863 (2024 preprint), proposes a searchable shared Lean library of definitions, theorems, proofs, and calculations in high-energy physics.
- **Formalization of Physics Index Notation in Lean 4**, arXiv:2411.07667 (2024 preprint), develops reusable formal infrastructure for tensor index notation.
- **Formalizing Chemical Physics Using the Lean Theorem Prover**, *Digital Discovery* (2023), DOI `10.1039/d3dd00077j`, demonstrates Lean formalization in chemical physics.
- **A Perspective on Interactive Theorem Provers in Physics**, *Advanced Science* (2025), DOI `10.1002/advs.202517294`, motivates a community-maintained open formal physics library, PhysLean/Physlib.
- **PhysProver: Advancing Automatic Theorem Proving for Physics**, arXiv:2601.15737 (2026 preprint), trains a physics-oriented theorem prover using formal physics data.
- **MerLean: An Agentic Framework for Autoformalization in Quantum Computation**, arXiv:2602.16554 (2026 preprint), extracts statements from theoretical quantum-computing papers, produces Lean declarations, and concentrates review on newly introduced definitions and axioms. This is highly adjacent to the local-delta principle.
- **Formalizing the Stability of the Two Higgs Doublet Model Potential into Lean: Identifying an Error in the Literature**, arXiv:2603.08139 (2026 preprint), reports a literature error found through physics formalization and illustrates why citations cannot automatically transmit trust.
- **Axioms for Physical Reasoning: Codifying the Seiberg--Witten Solution in Lean**, arXiv:2607.06379 (2026 preprint), makes physical postulates explicit and lets the prover report which assumptions each downstream result uses. This is closely related to conditional physical contracts.

### 14.5 Positioning statement

AgtXIv is not another general theorem search engine and should not attempt to replace Matlas, TheoremGraph, LeanSearch, LeanExplore, Mathlib, or Physlib. It is a verification-aware incremental query planner over their outputs:

```text
candidate theorem and dependency retrieval
→ exact contract resolution
→ assumption and version matching
→ accepted/conditional closure
→ minimal missing frontier
→ local-delta build
→ reusable QueryResolution receipt
```

The research question is therefore:

> Given candidate informal edges, formal declarations, explicit physical postulates, and heterogeneous verification records, how can a system compute the largest trustworthy reusable closure and the smallest remaining local delta without allowing unaccepted status to propagate downstream?
