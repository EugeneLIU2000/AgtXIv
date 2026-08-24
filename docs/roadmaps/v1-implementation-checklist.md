# AgtXIv v1 To-Do

**Document type:** implementation and release checklist
**Target release:** AgtXIv v1 — first complete vertical-slice demonstration
**Primary domain:** Stabilizerness
**Primary objective:** demonstrate one complete query-specific path from frozen literature source, through claim extraction and dependency archaeology, to Lean-checked mathematical closure, including at least one verification-driven graph repair and reusable contract export.
**System specification:** [AgtXIv](../../AgtXIv.md)
**Mathematics pipeline:** [normative mathematics profile](../specifications/mathematics-pipeline.md)
**Current implementation:** [Stabilizerness artifact synthesis](../../Stabilizerness/CURRENT_ARTIFACTS_SYNTHESIS.md)

This is an implementation and release checklist, not a competing design specification. Product release `v1` is distinct from the specification version (`v0.4` at the time this checklist was organized).

---

## 0. v1 Definition

AgtXIv v1 is **not** the first version with the largest knowledge graph.

It is the first version in which one query can be followed through the complete AgtXIv workflow:

```text
frozen source
→ source-grounded claims
→ candidate dependency graph
→ validated query-relative MathClaimDependencyDAG
→ root selection / contract reuse
→ Lean formalization
→ source-blind backtranslation
→ source-to-formal alignment audit
→ verification failure
→ local graph repair
→ re-verification
→ reusable accepted MathContract(s)
→ target local delta
→ MATH_CLOSED query result
→ reproducible release
```

The v1 demonstration must also show that AgtXIv distinguishes:

```text
VERIFIED / MATH_CLOSED
BLOCKED / UNRESOLVED
FALSE / REFUTED
```

These statuses must not be conflated.

---

# 1. Scope Freeze

## 1.1 Primary query

Use a query immediately upstream of the current closed-form target as the first query required to become fully mathematically closed.

Recommended primary query:

```text
statement:2607.26154v1:exact-graph-dual
```

or the canonical normalized ScientificClaim / MathContract identifier that replaces it.

Interpretation:

> Why does the reduced RoM admit the exact graph-program / MWIS-dual representation under the stated assumptions?

The exact identifier may change during namespace normalization, but the mathematical scope must remain fixed after v1 scope freeze.

## 1.2 Secondary query

Retain the stronger downstream closed-form result as a deliberately incomplete query:

```text
statement:2607.26154v1:closed-form-equality
```

Expected v1 behavior:

```text
MATH_CLOSED = FALSE
```

with the first unresolved frontier explicitly reported, expected to involve the perfect-graph / weighted-duality step unless that dependency is actually closed during v1.

The secondary query is useful precisely because it demonstrates that AgtXIv can stop at a visible frontier instead of silently bridging an unresolved theorem.

## 1.3 Negative-control claim

Keep at least one known false claim in the Registry, such as the current fixed-window monotonicity example.

Expected behavior:

```text
status = REFUTED / CLAIM_FALSE
evidence = EXPLICIT_COUNTEREXAMPLE
```

This must be visually and semantically distinct from:

```text
BLOCKED
PROOF_GAP
SOURCE_OR_FOUNDATION_GAP
```

## 1.4 v1 scope budget

Freeze a bounded query closure.

Recommended limits:

```yaml
v1_scope:
  primary_queries: 1
  secondary_queries: 1
  negative_controls: 1

  active_papers: 2-6
  root_agents_or_root_contracts: 1-3
  principal_claims_in_primary_closure: 5-15
  accepted_inference_chains: 3-8
  lean_declarations_required_for_primary_query: 1-5
  required_real_graph_repairs: ">= 1"
  required_backtranslations: ">= 1"
  required_alignment_audits: ">= 1"
  required_numerical_reproductions: 0
```

Do not enlarge the scope because another interesting citation or theorem is discovered unless it is load-bearing for the primary query.

## 1.5 Explicit v1 non-goals

Do **not** make the following prerequisites for v1:

- formalizing the whole target paper;
- formalizing all current Registry claims;
- resolving every whole-paper candidate dependency;
- formalizing a general perfect-graph library from scratch;
- creating a general-purpose physics Lean package;
- reproducing every numerical figure;
- reproducing the complete numerical pipeline of every ancestor paper;
- fine-tuning a graph-extraction model;
- covering additional theoretical-physics domains;
- building a universal scientific hypergraph;
- implementing cost-aware optimal scheduling;
- making every PaperAgent `VERIFICATION_CLOSED`;
- proving that every root paper is globally correct;
- replacing human-readable source alignment with a single LLM confidence score.

---

# 2. Freeze the v1 Source Bundle

## Goal

All v1 conclusions must refer to immutable source versions.

## Tasks

- [ ] Freeze the target paper version.
- [ ] Freeze all root/intermediate paper versions needed by the primary closure.
- [ ] Prefer author TeX/source archives where available.
- [ ] Freeze supplement files needed for relevant claims.
- [ ] Freeze code repositories only when referenced by the v1 closure.
- [ ] Record source hashes.
- [ ] Create exact source anchors for all primary-query claims.
- [ ] Create exact anchors for all load-bearing imported statements.
- [ ] Record missing source artifacts explicitly.
- [ ] Record cited-paper version when the target paper identifies one.
- [ ] Prevent mutable URLs alone from serving as canonical provenance.

## Required artifacts

```text
v1/
├── source/
│   ├── artifacts.json
│   ├── source-hashes.json
│   ├── anchors.jsonl
│   └── cross-references.json
```

## Gate

No claim or dependency edge may receive `SOURCE_VALIDATED` unless it points to a frozen source and exact anchor.

---

# 3. Normalize the Claim Namespace

This is one of the highest-priority v1 tasks.

The current demo contains multiple representations of related claims, including whole-paper claim identifiers, statement identifiers, Registry contracts, PaperAgent-local claims, and Lean declarations.

v1 must make these mappings machine-readable.

## 3.1 Establish canonical identities

For every claim in the primary closure create one canonical:

```text
ScientificClaim ID
```

Example structure:

```yaml
scientific_claim:
  id: claim:stabilizerness:exact-graph-dual
  kind: theorem
  source_manifestations:
    - source_statement: statement:2607.26154v1:exact-graph-dual
  math_claim_ir: math-ir:stabilizerness:exact-graph-dual
```

## 3.2 Add explicit normalization relations

Where old identifiers remain necessary, record:

```text
source manifestation
    --normalizes_to-->
canonical ScientificClaim
```

Possible relations:

```text
normalizes_to
same_claim_as
specializes
equivalent_under_assumptions
source_manifestation_of
formalizes_as
```

Do not infer identity from similar names.

## 3.3 Scope

Only normalize all identifiers in the **primary v1 query closure** before release.

Whole-repository normalization can happen later.

## Gate

The user interface, Registry, Lean links, query resolution, and release manifest must all resolve the same primary claim IDs.

There must not be two independent nodes that humans understand as the same theorem but the machine treats as unrelated without an explicit relation.

---

# 4. Build the v1 Candidate Claim Graph

## Goal

Create a small, source-grounded candidate graph for the primary query.

## Pipeline

```text
LLM extraction
→ constrained schema
→ source grounding
→ relation validation
→ candidate graph
```

Do not fine-tune a model in v1.

## 4.0 ContributionClaim vertical slice

`ContributionClaim` is the source-grounded narrative entry point for selecting
which paper-packaged result to decompose. It is a constrained `CONTRIBUTION`,
`NARRATIVE_ATOMIC` role/profile of `ScientificClaim`, stored in
`ScientificClaimRegistry` with a `claim:` ID. It is not a proof object and must
never enter `MathClaimDependencyDAG(q)` in place of `MathClaimIR`.

Required pipeline:

```text
Abstract / Introduction / Conclusion / Discussion candidate discovery
→ source calibration across repeated realizations
→ explicit body support locating
→ query-relative FORMAL_ATOMIC decomposition
→ canonical reusable theory alignment
→ load-bearing verification
→ PaperTheoryDelta / QueryResolution persistence
```

Milestone checklist:

- [x] preserve existing `agtxiv.scientific-claim/1.0.0` records without bulk migration;
- [x] implement the schema-pinned NFC/LF canonical profile for the supported JSON subset, including declared set/ordered arrays and duplicate rejection;
- [x] add seven exact-source fixtures with one primary and explicit body occurrences;
- [x] keep calibration and facet-aware navigation mappings in immutable external records pinned to each claim's `/facets` basis;
- [x] separate completed calibration stage from `NONE`/`PARTIAL`/`COMPLETE` facet outcomes;
- [x] validate source hashes/ranges/text, manifests, canonical TargetRefs, globally unique occurrence IDs, exact target artifacts, and append-only `(id, record_revision)` continuity;
- [x] retain one calibration and support generation per claim revision, with matching revisions and exact supersession references;
- [x] enforce source-strength guardrails plus generic MathClaimIR/non-promotion and mathematical-target-kind/ID-family DAG invariants;
- [ ] connect selected ContributionClaims to query-specific `PaperTheoryDelta` generation;
- [ ] persist the first query-relative decomposition and resulting `QueryResolution`;
- [ ] expose contribution-to-atomic support coverage in the verification viewer without presenting it as proof status.

The 1,645 provisional extractor candidates remain candidate inventory. They are
not accepted ContributionClaims and must pass calibration before promotion.

## 4.1 Claim extraction schema

Every extracted claim must record at minimum:

```yaml
claim:
  id: ...
  source_anchor: ...
  source_text: ...
  kind: theorem | definition | assumption | equation | derived_claim
  normalized_text: ...
  quantifiers: ...
  objects: ...
  assumptions: ...
  exactness: exact | approximate | asymptotic
  origin: SOURCE_EXPLICIT | SOURCE_IMPLICIT | AGENT_NORMALIZED | ...
```

## 4.2 Relation extraction schema

Every candidate relation must record:

```yaml
candidate_relation:
  id: ...
  from: ...
  to: ...
  relation_type: ...
  source_evidence:
    - anchor: ...
  extractor: ...
  extractor_version: ...
  confidence: ...
  status: CANDIDATE
```

## 4.3 Allowed v1 mathematical dependency relations

Keep the ontology small.

Recommended:

```text
definition_dependency
assumption_dependency
theorem_import
derived_by
scope_dependency
```

Non-build registry relations may include:

```text
specializes
equivalent_under_assumptions
```

Epistemic relations may be recorded separately:

```text
supports
extends
qualifies
refutes
supersedes
```

Do not allow epistemic edges to become mathematical proof dependencies automatically.

---

# 5. Validate the Primary Query DAG

The current candidate graph must not be treated as an accepted mathematical DAG merely because edges were proposed by an Oracle.

## 5.1 Edge validation

For each load-bearing candidate edge in the primary closure:

- [ ] inspect the source span of the importing claim;
- [ ] inspect the cited/imported source statement;
- [ ] confirm edge direction;
- [ ] confirm relation type;
- [ ] compare assumptions;
- [ ] compare mathematical objects;
- [ ] classify citation role;
- [ ] record verdict.

Allowed verdicts:

```text
ACCEPTED
REJECTED
AMBIGUOUS
WRONG_DIRECTION
WRONG_RELATION_TYPE
```

## 5.2 Accepted build graph

Only `ACCEPTED` mathematical dependency edges enter:

```text
MathClaimDependencyDAG(primary_query)
```

Ambiguous edges remain visible as candidates but do not determine build order.

## 5.3 DAG audit

- [ ] verify graph is acyclic at claim dependency level;
- [ ] detect circular proof dependencies;
- [ ] distinguish real claim cycles from paper-level bidirectional interactions;
- [ ] topologically sort accepted mathematical dependencies.

## Gate

The primary query cannot be declared `DAG_COMPLETE` merely because candidate edges exist.

---

# 6. Derive Paper-Level Views

## 6.1 PaperInteractionGraph

Build or retain:

```text
PaperInteractionGraph
```

Properties:

- typed;
- directed;
- may contain cycles;
- may include dependency and epistemic relations;
- primarily used for literature navigation.

Do not force global acyclicity.

## 6.2 PaperBuildDAG(primary_query)

Project the accepted claim DAG to papers.

If projection produces a paper-level cycle:

1. identify the strongly connected component;
2. verify that it is caused by distinct claim dependencies rather than circular mathematical proof;
3. collapse the papers into a query-local:

```text
CompanionBundle
```

Then construct the acyclic paper build order.

## Gate

The build scheduler uses `PaperBuildDAG(primary_query)`, not the unrestricted PaperInteractionGraph.

---

# 7. Establish Root Contracts Before Root Agents

## Goal

Avoid creating paper-sized Agents for mathematics that already exists as reusable infrastructure.

For every unresolved upstream mathematical dependency:

```text
search accepted AgtXIv contracts
→ search pinned project
→ search Mathlib / relevant Lean package
→ construct short bridge if possible
→ only then create / expand Root Agent
```

## 7.1 Required decisions for every root candidate

Record one stop reason:

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
```

## 7.2 Root Agent is not an axiom

For every root export:

- [ ] anchor source;
- [ ] state exact normalized theorem;
- [ ] list assumptions;
- [ ] run package search;
- [ ] formalize selected mathematical core;
- [ ] backtranslate;
- [ ] audit alignment;
- [ ] preserve unresolved gaps.

Root status must not automatically promote all claims in the paper.

---

# 8. Build the Stable Root API

The existing RootMath project may contain many internal lemmas.

v1 needs a small public facade.

## Goal

Downstream papers import **contracts**, not an uncontrolled internal namespace.

## Recommended structure

```text
formal/
└── AgtXIvRootMath/
    ├── Internal/
    │   └── ...
    └── Exports.lean
```

`Exports.lean` should expose only reusable declarations needed by the v1 target.

## Tasks

- [ ] identify every root declaration currently imported by the primary query;
- [ ] classify declarations as:
  - `PUBLIC_ROOT_EXPORT`
  - `INTERNAL_HELPER`
  - `PAPER_SPECIFIC`
- [ ] eliminate downstream reliance on internal helpers when a stable wrapper is appropriate;
- [ ] attach each public Lean export to a versioned `MathContract`;
- [ ] record imported Mathlib/Physlib declarations;
- [ ] record `#print axioms`;
- [ ] record package/environment versions.

## Gate

The target paper formalization imports only documented public contracts or documented external declarations.

---

# 9. Introduce MathClaimIR for Every Formalized v1 Claim

Do not use:

```text
paper text → Lean
```

as the only representation.

Every formalized claim must first have a structured `MathClaimIR`.

## Minimum fields

```yaml
math_claim_ir:
  id: ...
  source_claim: ...
  quantifiers: ...
  objects:
    - symbol: ...
      semantic_type: ...
      carrier: ...
  assumptions: ...
  definitions: ...
  conclusion: ...
  exactness: ...
  parameter_regime: ...
  source_anchor: ...
```

## Purpose

Prevent:

```text
notational collapse
wrong object type
abstraction elevation
lost assumption
domain drift
exact/approximate drift
finite/asymptotic drift
```

## Gate

A Lean theorem cannot be promoted to an accepted AgtXIv contract if its input `MathClaimIR` is missing.

---

# 10. Implement the v1 Autoformalization Loop

The first complete demonstration should show an automated multi-agent loop.

## Required roles

### A. Formalizer / Blueprint Agent

Input:

```text
frozen source
MathClaimIR
available accepted contracts
LeanPackageCapabilityRegistry
relevant declarations
```

Output:

```text
Lean statement
proof blueprint
candidate subclaims
candidate package imports
```

### B. Lean Kernel / Build

Checks:

```text
elaboration
proof compilation
sorry/admit
axioms
actual dependencies
```

Kernel failure remains a compiler fact, not an LLM judgment.

### C. Source-Blind Backtranslator

Input:

```text
Lean declaration
definitions
actual imported declarations
```

The original source text must not be given to this agent.

Output:

```text
human-readable mathematical claim
reconstructed MathClaimIR'
```

### D. Alignment Auditor

Compare:

```text
Source claim
MathClaimIR
Lean declaration
Backtranslated MathClaimIR'
```

Mandatory comparisons:

```text
quantifiers
object types
domains/codomains
assumptions
definition mappings
exact vs approximate
finite vs asymptotic
conclusion strength
excluded edge cases
```

### E. Source-Aware Refiner

Input includes the original frozen source.

It may repair:

```text
proof blueprint
claim decomposition
object mappings
assumptions
dependency edges
formalization boundary
```

It must not optimize merely for Lean compilation.

---

# 11. Make the Varela Gap the Main v1 Graph-Repair Demonstration

The current unresolved V-representation path is ideal for demonstrating AgtXIv's central iterative behavior.

The point is **not** to pre-declare that the theorem is correct.

The point is to demonstrate:

```text
initial shallow dependency
→ formal/source failure
→ local refinement
→ smaller obligations
→ re-check
```

## 11.1 Initial shallow representation

Conceptually:

```text
Varela theorem/source
        ↓
V-representation contract
```

## 11.2 First failure

When source reconstruction or Lean cannot close the result:

```yaml
failure:
  class: SOURCE_OR_FOUNDATION_GAP
```

or, if diagnosis shows a local proof decomposition issue:

```yaml
failure:
  class: LOCAL_BUILD_FAILURE
```

Do not decide the class in advance; determine it from the actual failure.

## 11.3 Graph repair

Apply:

```text
EXPAND_LOCAL
```

and split the coarse node into the actual missing obligations discovered during reconstruction.

Possible examples, only if actually supported by the source audit:

```text
candidate physicality
projected-atom refinement
extremality
convex-hull / V-representation implication
```

Do not hard-code these as truths before checking the source.

## 11.4 Required GraphRepairRecord

```yaml
graph_repair:
  id: repair:...
  query: ...
  graph_before: ...
  blocked_node: ...
  failure_class: ...
  diagnostic_tags: [...]
  operation: EXPAND_LOCAL
  added_claims: [...]
  removed_edges: [...]
  added_edges: [...]
  graph_after: ...
  verification_effect: ...
```

## 11.5 Repeat shallowly

At each iteration:

1. choose one current blocked frontier node;
2. attempt source/Lean closure;
3. diagnose;
4. apply one local repair;
5. recompute the query closure;
6. continue.

Do **not** regenerate the whole DAG after each failure.

---

# 12. Use Only Three Top-Level Failure Classes

Keep v1 taxonomy minimal.

## `LOCAL_BUILD_FAILURE`

Meaning:

> The current mathematical statement may be appropriate, but the proof decomposition, bridge, or library connection is insufficient.

Typical tags:

```text
missing_lemma
missing_bridge
definition_not_unfolded
premise_retrieval_failure
typeclass_gap
```

Default repair:

```text
EXPAND_LOCAL
```

## `ALIGNMENT_FAILURE`

Meaning:

> The formalized object or dependency does not faithfully match the source claim.

Typical tags:

```text
wrong_object_type
quantifier_drift
lost_assumption
stronger_conclusion
weaker_conclusion
wrong_domain
exactness_drift
abstraction_elevation
```

Default repair:

```text
REWIRE_OR_RESCOPE
```

## `SOURCE_OR_FOUNDATION_GAP`

Meaning:

> The source itself omits a needed result, relies on an unresolved foundation, or may be mathematically overstated.

Typical tags:

```text
missing_source_step
unresolved_external_theorem
unsupported_import
possible_false_claim
counterexample_found
```

Default repair:

```text
ESCALATE_OR_BLOCK
```

---

# 13. Complete the Primary Target Local Delta

Once root dependencies are accepted or explicitly conditional, formalize only the residual target mathematics.

For the current Stabilizerness route, expected local targets include only the mathematical steps actually needed to derive the chosen exact graph-dual result.

Potential local steps should be confirmed from source before implementation.

Likely categories include:

```text
sign maximization / sign-set collapse
relaxed affine-span argument
finite LP representation
LP dual
MWIS interpretation
exact graph-program identity
```

The actual accepted chain must be source-grounded.

## Required behavior

For every local target claim:

- [ ] source anchor;
- [ ] MathClaimIR;
- [ ] imported contracts;
- [ ] Lean theorem;
- [ ] clean proof;
- [ ] source-blind backtranslation;
- [ ] alignment audit;
- [ ] verification record.

## Primary final theorem

The canonical v1 primary theorem must have a concrete Lean declaration.

Example placeholder:

```text
Stabilizerness.ExactGraphDual
```

Do not freeze the theorem name until the normalized objects are stable.

---

# 14. Lean Acceptance Gate

The primary query may receive `MATH_CLOSED` only if all accepted formal dependencies satisfy:

- [ ] pinned Lean version;
- [ ] pinned Mathlib version;
- [ ] pinned external physics-package versions;
- [ ] clean `lake build`;
- [ ] no `sorry`;
- [ ] no `admit`;
- [ ] no hidden replacement of a theorem by a project axiom;
- [ ] `#print axioms` recorded for exported declarations;
- [ ] exact declaration dependencies recorded;
- [ ] assumptions match exported MathContracts;
- [ ] source-to-formal alignment audit passed at the declared v1 automated threshold.

---

# 15. Create a LeanPackageCapabilityRegistry Entry

v1 does not need a complete survey of theoretical physics.

It needs at least one working package-routing example.

For Stabilizerness this should identify the actual formal infrastructure used.

## Required record

```yaml
lean_package_capability:
  id: ...
  package: ...
  commit: ...
  lean_version: ...
  mathlib_version: ...

  field_tags:
    - quantum_information
    - stabilizer_resource_theory
    - graph_theory
    - convex_geometry

  object_coverage:
    - ...

  trust_tier: ...

  declarations_used:
    - ...

  known_gaps:
    - ...

  local_bridges:
    - ...
```

## Package selection rule

Use:

```text
domain classification
→ object extraction
→ declaration search
→ exact type/environment check
→ local bridge
```

Do not assume:

```text
field label → package contains all necessary postulates/theorems
```

---

# 16. Add the v1 SemanticContract

The mathematical demo should still show that mathematical correctness is not identical to physical interpretation.

Create one compact `SemanticContract` covering the objects required to understand the primary query.

Possible content:

```text
measurement set
Pauli observables
reduced stabilizer polytope
reduced RoM
active dependencies
frustration graph
physical/resource-theoretic interpretation
```

Only include what is material to the chosen query.

## SemanticContract fields

```yaml
semantic_contract:
  id: ...

  physical_system: ...
  modeled_objects: ...

  object_alignment:
    paper_objects: ...
    mathematical_objects: ...

  assumptions: ...
  approximations: []

  evidence: []

  status:
    semantic_alignment: ...
    empirical_support: NOT_REQUIRED
    human_review: ...
```

For the math-first Stabilizerness demo, experimental evidence may legitimately be:

```text
NOT_REQUIRED
```

if the target query is purely mathematical.

---

# 17. Keep Computation Minimal in v1

Do not create a computational DAG.

Use claim-attached:

```text
ReproductionRecord
```

only where useful.

Existing finite-instance scripts can serve as:

```text
SUPPORTING
REGRESSION_CHECK
COUNTEREXAMPLE_CHECK
```

They must not be promoted to mathematical proof.

## Reproduction role

Every record must say:

```text
ILLUSTRATIVE
SUPPORTING
LOAD_BEARING
```

The primary query should preferably not depend on a new expensive numerical reproduction.

## Required fields

```yaml
reproduction_record:
  claim_id: ...
  role: SUPPORTING
  code_commit: ...
  inputs: ...
  environment: ...
  parameters: ...
  random_seed: ...
  command: ...
  reported_output: ...
  reproduced_output: ...
  tolerance: ...
  verdict: ...
```

---

# 18. Preserve a Secondary Blocked Query

After the primary exact graph-dual query closes, evaluate the downstream closed-form equality query.

Do not force it closed for v1.

The expected interface should show:

```text
query: closed-form-equality

DAG_COMPLETE: ...
MATH_CLOSED: FALSE

first_unresolved_frontier:
  claim: perfect-graph-weighted-duality
  status: BLOCKED / UNRESOLVED
  reason: ...
```

If that claim is independently closed before release, move the frontier to the next actual unresolved dependency.

The purpose is to demonstrate honest frontier computation.

---

# 19. Preserve the False-Claim Negative Control

The demo must show a mathematically false claim separately.

Required fields:

```yaml
claim_status:
  status: REFUTED
  evidence_type: EXPLICIT_COUNTEREXAMPLE
  counterexample: ...
  source_alignment: ...
```

UI must clearly distinguish:

```text
FALSE
```

from:

```text
UNPROVEN
BLOCKED
SOURCE_GAP
FORMALIZATION_FAILURE
```

---

# 20. Upgrade the Web Demo from DAG Viewer to Verification Viewer

The v1 UI is part of the scientific demonstration.

It should not merely display nodes and edges.

## 20.1 Main query page

Show:

```text
Primary query
Current closure status
Accepted imports
Conditional imports
Blocked frontier
Local delta
Repair history
```

## 20.2 Mathematics view

Recommended tabs:

```text
Candidate
Accepted
Build
```

### Candidate

Shows all source-grounded candidate relations.

### Accepted

Shows only reviewed mathematical dependencies.

### Build

Shows topological verification order and current blocked frontier.

## 20.3 Claim detail panel

For each claim show:

```text
Canonical ID
PaperAgent
Frozen source
Exact source anchor
Source text
Normalized claim
MathClaimIR
Assumptions
Imports
Inference steps
Lean declaration
Lean environment
Axioms
Source-blind backtranslation
Alignment diff
Verification records
Repair history
Blockers
Exported contract version
```

## 20.4 Repair Timeline

A critical v1 visualization:

```text
G0
↓
failure
↓
repair
↓
G1
↓
failure / success
↓
G2
↓
accepted
```

The UI should allow the user to see what changed:

```text
claim added
claim split
edge removed
edge rewired
assumption added
claim rescoped
```

## 20.5 Main profile structure

Use:

```text
Mathematics
Semantics
Computation
```

Provenance should be visible across all three rather than as a competing scientific layer.

---

# 21. QueryResolution Receipt

The primary query must generate a machine-readable result.

Example:

```yaml
query_resolution:
  id: resolution:stabilizerness:exact-graph-dual:v1

  query: ...
  target: claim:...

  status:
    dag_complete: true
    math_closed: true
    semantically_reconstructed: true
    computationally_reproduced: false
    verification_closed: true

  accepted_imports: [...]
  conditional_imports: []
  dependency_closure: [...]
  paper_build_order: [...]

  root_contracts: [...]
  local_delta: [...]

  blocked_frontier: []

  graph_repairs:
    - repair:...

  lean_exports:
    - ...

  alignment_audits:
    - ...

  package_versions: ...
  dependency_versions: ...
```

For the secondary query, the same format must return a non-empty `blocked_frontier`.

---

# 22. v1 Telemetry

Do not implement optimization yet.

Record enough data to support v2 cost/reuse analysis.

## Required metrics

```yaml
build_metrics:
  candidate_claims_extracted: 0
  candidate_relations_extracted: 0
  accepted_relations: 0
  rejected_relations: 0

  reused_registry_contracts: 0
  reused_external_declarations: 0
  new_root_export_declarations: 0
  new_local_bridge_declarations: 0
  new_target_declarations: 0

  formalizer_agent_calls: 0
  backtranslator_agent_calls: 0
  alignment_auditor_calls: 0
  refiner_agent_calls: 0

  lean_build_attempts: 0
  repair_rounds: 0
  expand_local_repairs: 0
  rewire_or_rescope_repairs: 0
  escalate_or_block_repairs: 0

  source_expansions: 0
  blocked_claims_unlocked: 0

  accepted_contracts_exported: 0
  downstream_targets_reusing_export: 0

  human_review_minutes: 0
```

---

# 23. Adversarial Audit

Before v1 release, run an explicit adversarial review.

The reviewer/agent should attempt to falsify the accepted closure.

## Mandatory checks

- [ ] quantifier drift;
- [ ] object-type mismatch;
- [ ] lost assumptions;
- [ ] stronger conclusion than source;
- [ ] weaker formal theorem silently presented as source theorem;
- [ ] exact-to-approximate drift;
- [ ] finite-to-asymptotic drift;
- [ ] notational collapse;
- [ ] abstraction elevation;
- [ ] hidden project axioms;
- [ ] circular mathematical dependency;
- [ ] incorrect paper-level cycle handling;
- [ ] wrong source version;
- [ ] unsupported import;
- [ ] citation used as proof;
- [ ] false claim accidentally classified as blocked;
- [ ] blocked claim accidentally classified as false;
- [ ] numerical support accidentally classified as proof;
- [ ] Lean theorem that compiles but formalizes the wrong mathematical object;
- [ ] Root Agent claim accepted only because it is a root.

---

# 24. Release Validator

Create a strict v1 validator.

Recommended command:

```bash
python scripts/validate_v1_release.py
```

or an equivalent repository-native entry point.

## Required validator checks

### Source

- all required frozen artifacts exist;
- hashes match;
- all accepted claims have source anchors.

### Registry

- all canonical claim IDs resolve;
- mappings are unique where required;
- no dangling contract references;
- no accepted relation references a missing claim.

### Query DAG

- accepted primary DAG is acyclic;
- all primary dependencies are reviewed;
- candidate-only edges are not in accepted graph;
- topological build order exists.

### Lean

- clean build;
- no `sorry`;
- no `admit`;
- exported axioms recorded;
- exported declarations exist.

### Alignment

- each required formalized claim has:
  - MathClaimIR;
  - source-blind backtranslation;
  - alignment audit.

### Repair

- at least one real GraphRepairRecord exists;
- before/after graph versions are reconstructible;
- repair points to an actual verification failure.

### Query result

Primary:

```text
DAG_COMPLETE = true
MATH_CLOSED = true
```

Secondary:

```text
MATH_CLOSED = false
blocked_frontier != []
```

Negative control:

```text
status = REFUTED
counterexample != null
```

### Release integrity

- release manifest exists;
- dependency versions recorded;
- coverage report exists;
- telemetry exists;
- clean checkout rebuild command documented.

---

# 25. Required v1 Release Artifacts

The final v1 repository/release should contain at minimum:

```text
AgtXIv/
├── AgtXIv.md
├── README.md
├── docs/roadmaps/v1-implementation-checklist.md
├── release-manifest.json
├── coverage.yaml
│
├── v1/
│   ├── pilot-scope.yaml
│   │
│   ├── source/
│   │   ├── artifacts.json
│   │   ├── source-hashes.json
│   │   └── anchors.jsonl
│   │
│   ├── registry/
│   │   ├── scientific-claims/
│   │   ├── math-claim-ir/
│   │   ├── math-contracts/
│   │   ├── semantic-contracts/
│   │   ├── mappings/
│   │   └── package-capabilities/
│   │
│   ├── graph/
│   │   ├── candidate-relations.jsonl
│   │   ├── accepted-relations.jsonl
│   │   ├── primary-query-dag.json
│   │   ├── paper-interaction-graph.json
│   │   ├── paper-build-dag.json
│   │   └── repairs/
│   │
│   ├── formal/
│   │   ├── root/
│   │   ├── target/
│   │   ├── backtranslations/
│   │   ├── alignment-audits/
│   │   └── build-logs/
│   │
│   ├── computation/
│   │   └── reproduction-records/
│   │
│   ├── query-resolutions/
│   │   ├── primary.yaml
│   │   └── secondary.yaml
│   │
│   ├── audit/
│   │   └── adversarial-review.md
│   │
│   └── telemetry/
│       └── build-metrics.yaml
│
└── scripts/
    └── validate_v1_release.py
```

Exact repository layout may adapt to the current implementation, but all semantic objects above must be represented somewhere.

---

# 26. v1 Release Acceptance Matrix

| Requirement | Required for v1 | Notes |
|---|---:|---|
| Frozen target source | YES | exact version + hashes |
| Frozen root sources | YES | only primary closure |
| Canonical claim namespace | YES | primary closure |
| Candidate claim graph | YES | source grounded |
| Accepted primary MathClaimDependencyDAG | YES | reviewed edges only |
| PaperInteractionGraph | YES | may contain cycles |
| PaperBuildDAG | YES | query-relative |
| Root contract facade | YES | stable Lean/API exports |
| MathClaimIR | YES | every formalized claim |
| Lean build | YES | clean |
| Source-blind backtranslation | YES | at least one, preferably every primary export |
| Alignment audit | YES | primary formalized claims |
| Real graph repair | YES | at least one |
| Varela gap resolution | REQUIRED IF PRIMARY DEPENDS ON IT | otherwise primary cannot be MATH_CLOSED |
| Primary target Lean theorem | YES | concrete declaration |
| SemanticContract | YES | compact |
| Numerical DAG | NO | explicitly out of scope |
| New expensive numerical reproduction | NO | unless unexpectedly load-bearing |
| ReproductionRecord | OPTIONAL | supporting checks can be retained |
| Secondary blocked query | YES | demonstrates frontier |
| False-claim negative control | YES | demonstrates REFUTED |
| Cost optimizer | NO | telemetry only |
| Fine-tuned extractor | NO | general LLM + schema |
| New physics Lean package | NO | use package registry + local bridges |
| Adversarial audit | YES | before release |
| Release validator | YES | `rc=0` |
| Clean-checkout reproduction | YES | required |

---

# 27. Recommended Implementation Order

The following ordering minimizes wasted work.

## Milestone A — Freeze and Normalize

- [ ] freeze primary v1 query;
- [ ] freeze source versions;
- [ ] determine exact primary closure;
- [ ] create canonical claim IDs;
- [ ] map current namespaces into canonical IDs;
- [ ] freeze v1 scope file.

**Do not write substantial new Lean code before this milestone passes.**

## Milestone B — Accepted DAG

- [ ] extract/reuse candidate claims;
- [ ] source-ground all primary closure claims;
- [ ] validate every load-bearing edge;
- [ ] construct accepted primary DAG;
- [ ] topologically sort;
- [ ] derive PaperBuildDAG.

**Deliverable:** the first authoritative query graph.

## Milestone C — Root Infrastructure

- [ ] search Registry first;
- [ ] search Lean packages;
- [ ] identify exact root exports;
- [ ] create stable `Exports.lean`;
- [ ] create versioned root MathContracts;
- [ ] record package capabilities.

**Deliverable:** reusable root API.

## Milestone D — First Real Repair

- [ ] attempt V-representation/root closure;
- [ ] capture the actual first failure;
- [ ] classify it;
- [ ] locally expand/rewire/rescope;
- [ ] save `GraphRepairRecord`;
- [ ] repeat until accepted or blocked.

**Deliverable:** first verification-guided graph refinement trace.

## Milestone E — Target Closure

- [ ] formalize residual target local delta;
- [ ] compile final primary theorem;
- [ ] remove placeholders;
- [ ] audit axioms;
- [ ] create target MathContract.

**Deliverable:** `MATH_CLOSED` primary query.

## Milestone F — Alignment Loop

- [ ] source-blind backtranslate root/target exports;
- [ ] build structural diffs;
- [ ] repair any semantic drift;
- [ ] rerun Lean if statements change;
- [ ] record final alignment verdicts.

**Deliverable:** source-to-formal fidelity evidence.

## Milestone G — Honest Contrast Cases

- [ ] evaluate downstream closed-form query;
- [ ] expose first unresolved frontier;
- [ ] preserve false-claim negative control;
- [ ] verify three statuses remain distinct.

**Deliverable:** verified / blocked / false comparison.

## Milestone H — UI and Release

- [ ] update demo profiles;
- [ ] add Candidate / Accepted / Build views;
- [ ] add claim detail panel;
- [ ] add Repair Timeline;
- [ ] generate QueryResolution receipts;
- [ ] record telemetry;
- [ ] run adversarial audit;
- [ ] run strict validator;
- [ ] rebuild from clean checkout;
- [ ] create v1 release manifest.

**Deliverable:** public AgtXIv v1 demonstration.

---

# 28. Stop Conditions

AgtXIv v1 should **not** be declared complete if any of the following is true:

- the primary query graph still relies on unreviewed candidate edges;
- the primary final theorem has no Lean declaration;
- a required Root claim is assumed rather than verified/explicitly conditional;
- a required Lean theorem contains `sorry` or `admit`;
- a source-to-formal critical mismatch remains unresolved;
- the Varela path is load-bearing and remains a proof/source gap;
- the primary query is labeled `MATH_CLOSED` despite an unresolved mathematical frontier;
- the release cannot rebuild from a clean checkout;
- the GraphRepairRecord is synthetic rather than generated from a real verification failure;
- false claims and blocked claims are not represented differently;
- the UI shows verification status that is stronger than the underlying Registry status.

---

# 29. Allowed v1 Partial Outcomes

The project should remain scientifically honest even if the intended primary theorem cannot be closed.

If a genuine source gap or counterexample prevents closure, the acceptable outcome is:

```text
primary query:
  MATH_CLOSED = false

verified closure:
  maximal trustworthy subset

blocked frontier:
  exact first unresolved claim

repair history:
  preserved

reason:
  explicit
```

This would not satisfy the planned **complete v1** gate, but it would still be a valid AgtXIv experimental result.

Do not repair the demonstration by silently strengthening assumptions or replacing the source theorem with an easier theorem.

---

# 30. Definition of Done

AgtXIv v1 is complete when an external user can open the demo and perform the following conceptual experiment.

## Query 1 — Successfully verified target

User asks:

> Why does the target paper obtain the exact graph-dual representation?

The system shows:

```text
target claim
↓
accepted query-specific dependencies
↓
root contracts
↓
a real detected verification gap
↓
local DAG repair
↓
reconstructed missing obligations
↓
Lean-checked root/local mathematics
↓
source-blind backtranslation
↓
alignment audit
↓
target local delta
↓
Lean-checked target theorem
↓
MATH_CLOSED
```

Every important node is inspectable.

## Query 2 — Downstream unresolved target

User asks for the stronger closed-form result.

The system shows:

```text
accepted verified prefix
+
first unresolved frontier
+
reason for blockage
```

It does not fabricate closure.

## Query 3 — False historical/current claim

User opens the negative-control claim.

The system shows:

```text
REFUTED
explicit counterexample
```

rather than presenting it as a proof gap.

---

# 31. What v1 Should Demonstrate Scientifically

The scientific/system claim demonstrated by v1 should be modest and precise:

> AgtXIv can convert a noisy paper-level mathematical reasoning path into a query-relative, source-grounded and incrementally verified dependency closure; use formal-verification failure to refine only the local blocked frontier; export reusable verified mathematical contracts; and explicitly distinguish verified, unresolved, and refuted claims.

v1 does **not** need to establish that AgtXIv can yet:

- autonomously formalize arbitrary theoretical physics;
- discover all scientific dependencies;
- replace expert review;
- cover all physics subfields;
- guarantee empirical validity;
- minimize formalization cost globally;
- produce an optimal knowledge graph.

Those are later research questions.

---

# 32. v1 → v2 Handoff Data

Even though v2 optimization is out of scope, v1 should preserve the data needed to study it.

At release record:

```text
number of previously verified contracts reused
number of external Lean declarations reused
number of paper-specific local declarations created
number of repair rounds
number of source expansions
number of LLM formalization attempts
number of alignment failures
number of claims unlocked by each repair
human review time
```

This enables later study of:

\[
C_{\mathrm{marginal}}(q)
\]

and:

\[
\operatorname{ReuseGain}(q)
=
1-
\frac{C_{\mathrm{with\ registry}}(q)}
     {C_{\mathrm{cold\ start}}(q)}.
\]

The central long-term hypothesis is not merely that the Registry grows, but that reusable accepted contracts reduce the marginal formalization cost of later related queries.

---

# 33. Immediate Next Actions

The first implementation session after adopting this document should do only the following:

1. [ ] freeze the canonical primary query;
2. [ ] enumerate its current candidate dependency closure;
3. [ ] reduce that closure to at most roughly 5–15 principal mathematical claims;
4. [ ] assign one canonical ScientificClaim ID to every node;
5. [ ] create machine-readable mappings from current demo/Registry identifiers;
6. [ ] source-ground and review every edge in this reduced closure;
7. [ ] output the first accepted `MathClaimDependencyDAG`;
8. [ ] identify the exact first unresolved frontier;
9. [ ] only then begin additional Lean construction.

Do not start by adding new papers or expanding the global graph.

---

## Final v1 Principle

```text
Make one path trustworthy before making the graph large.
```

The first AgtXIv release succeeds when one query has a complete, inspectable, rebuildable verification history—not when the Registry contains the largest number of nodes.
