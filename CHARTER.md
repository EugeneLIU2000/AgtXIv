# AgtXIv Charter

**Ratification state:** PENDING under ADR 0007 unless and until the qualifying ratification commit exists
**Canonical document identity:** `AgtXIv-Charter/1.0`
**Initial Charter version:** 1.0
**Adoption authority record:** [`ADR 0007`](docs/adr/0007-adopt-project-charter.md)
**Stable adoption record:** unavailable while pending; after ratification, the full Git object ID of the qualifying ratification commit defined by ADR 0007
**Effective date:** unavailable while pending; after ratification, the Git committer timestamp of that commit
**Scope:** All AgtXIv specifications, versions, profiles, implementations, releases, and knowledge products

This exact version is `PROPOSED` in every repository state before the qualifying ratification commit and `ADOPTED` only in canonical authoritative `main` history at or after that commit. Required project-authority approval and relevant specialist reviews must independently bind the exact combined change under `GOVERNANCE.md`; uncommitted bytes, a feature-branch commit, an unauthorized commit, or copied status labels have no constitutional effect.

Upon adoption, this Charter states why AgtXIv exists and the principles that every version must preserve. It becomes the project's highest-level normative authority. Versioned specifications and governance may define narrower missions, products, schemas, workflows, acceptance criteria, and decision processes, but they MUST remain subordinate to the adopted Charter. A version may implement only part of the Charter; it MUST NOT redefine the project's purpose, collapse distinctions protected here, or claim that a version-specific deliverable is the final mission of AgtXIv.

Upon adoption, the authority hierarchy is:

1. this Charter;
2. version specifications and repository governance;
3. Architecture Decision Records, contracts, schemas, and plans; and
4. implementations, fixtures, generated views, and operational outputs.

A lower-level artifact may be more specific, but it cannot override a higher-level authority. Changes to this Charter are project-level amendments, not ordinary version revisions. No version specification, governance rule, Architecture Decision Record, implementation plan, contract, schema, migration, compatibility layer, implementation, or release may amend it implicitly.

## North Star

> **From scientific literature to verified and reusable knowledge.**

In this Charter, *verified* does not mean unconditionally true. It means that the relevant source, claim, dependency, evidence, alignment, and unresolved boundary have been examined under explicit scopes and distinct verification axes. AgtXIv MUST state which axes were evaluated, what the evidence establishes, and what remains unsupported, unknown, blocked, failed, disputed, or out of scope.

## Mission

AgtXIv turns static arXiv papers into auditable Paper Agents and accumulates their verified claims, dependencies, evidence, substantive contributions, and unresolved frontiers in a provenance-preserving scientific knowledge base.

## Normative Ideal

For every paper in scope, AgtXIv identifies attributable scientific claims and reconstructs their definitions, assumptions, prior results, reasoning dependencies, computational or empirical evidence, and conditions of applicability. It evaluates source fidelity, mathematical correctness, formal alignment, semantic applicability, empirical support, and computational reproducibility on separate verification axes, while preserving conflicts, failures, unknown states, and unresolved frontiers.

AgtXIv represents a paper's substantive contribution as the traceable delta it adds to, corrects, qualifies, refutes, or independently verifies against the existing knowledge base—not as a judgment inferred from narrative packaging, citation counts, or the paper's own novelty claims. Audited paper-level packages and individually admissible knowledge entries are accumulated in a versioned, provenance-preserving, conflict-aware, and reusable scientific knowledge base.

The long-term objective is that readers and agents can interpret each new paper from the current verified knowledge frontier, identify its actual dependencies and contribution delta, and reuse prior verification work without repeatedly traversing layers of historical literature.

The normative ideal describes the direction of the project, not a claim that every current version or release realizes the entire system. Each version MUST state which portion it implements, how completion is bounded, and which capabilities remain future work.

## Constitutional Principles

### 1. Exact and attributable sources

Authoritative knowledge MUST remain anchored to an identifiable source occurrence. It must be possible to determine which work, version, passage, artifact, or other source object supports a claim and who or what produced each relevant assertion, evidence item, assessment, or transformation.

A mutable title, informal citation, generated summary, or semantic similarity match is not sufficient provenance. Derived objects MUST retain an auditable route back to their source material. Later specifications may define the identifiers, hashes, locators, manifests, and integrity checks used to satisfy this principle, but may not weaken the requirement itself.

### 2. Explicit reasoning and applicability

AgtXIv MUST expose the load-bearing structure between source and conclusion: definitions, assumptions, imported results, inference dependencies, evidence, conditions of applicability, and unresolved steps whenever they affect what may be concluded.

A fluent explanation, paper-level label, citation edge, retrieval score, or successful output is not a substitute for this structure. Representations may vary by domain and version, but they MUST show why a conclusion is supported, conditional, blocked, disputed, or unsupported.

### 3. Independent verification axes and no silent promotion

AgtXIv MUST keep distinct at least the following questions whenever they apply:

1. **Source fidelity:** What does the identified source actually assert?
2. **Mathematical correctness:** Does a conclusion follow from the stated mathematical assumptions?
3. **Formal alignment:** Does a formal representation preserve the intended mathematical claim?
4. **Semantic applicability:** Does the represented object correspond to the intended system, model, approximation, regime, or observable?
5. **Empirical support:** What observations or external evidence support the scientific assumptions and conclusions?
6. **Computational reproducibility:** Can a load-bearing computational result be regenerated under a sufficiently specified environment and procedure?

A version may add further axes, but MUST NOT collapse them into one truth or verification status. Success on one axis cannot establish another: source preservation does not prove correctness; a proof or formal build does not establish source fidelity, physical applicability, or empirical adequacy; reproducibility does not establish scientific validity; and package completion, certification, publication, or database admission does not establish whole-paper truth. Every conclusion MUST remain bounded by its weakest load-bearing evidence, assumptions, scope, and conditions of applicability.

### 4. Preserve uncertainty, conflict, and bounded completeness

Unknown, blocked, failed, refuted, disputed, incompatible, deferred, and out-of-scope outcomes are durable knowledge about the frontier and MUST remain visible. Conflicting sources or assessments must remain independently inspectable with their provenance and scopes intact; ranking, summarization, deduplication, or supersession must not erase relevant alternatives or objections.

Completion MUST always be relative to an explicit scope, profile, claim set, or evidence requirement. It means that required items within that boundary have been accounted for—not exhaustive understanding, closure of a literature, or truth of all included claims. Every version and release MUST state its coverage, exclusions, unresolved capabilities, and non-implications.

### 5. Auditable authority and non-self-certification

Every authoritative transformation, assessment, audit, certification, admission, or release MUST have an explicit authority boundary. The system must identify which actor or process generated an object, which assessed or approved it, and what each decision is authorized to imply.

A producer's confidence in its own output is not independent verification. Versions may define different roles and review mechanisms, but an artifact MUST NOT acquire stronger authority merely because the process that generated it also labeled it successful. Public authority must rest on inspectable sources, records, evidence, procedures, and decisions—not inaccessible chain-of-thought or undocumented agent judgment.

### 6. Provenance-preserving reuse and accumulation

Reuse MUST carry forward the provenance, assumptions, scope, environment, alignment conditions, status, and known limitations needed to interpret an object correctly. Textual similarity, shared notation, citations, embeddings, or apparent theorem equivalence are not sufficient to establish identity or safe reuse; substantive relations require an explicit assessment appropriate to the domain.

Each completed investigation SHOULD reduce the work required to interpret and verify later papers while preserving access to the underlying history. AgtXIv should compress repeated traversal, not provenance; reuse evidence, not overclaims; and let new analyses begin from the current knowledge frontier rather than an empty context. Accumulation MUST be versioned and non-destructive so that corrections, stronger evidence, changed environments, and later conflicts remain inspectable.

### 7. Contribution as a traceable knowledge delta

AgtXIv MUST distinguish a paper's presentation from its attributable contribution without treating narrative as disposable. Narrative may carry motivation, scope, interpretation, limitations, and semantic meaning, but is not itself evidence of novelty or correctness.

A substantive contribution is represented relative to an identified prior knowledge state. It may introduce, derive, generalize, specialize, correct, qualify, refute, reproduce, independently verify, unify, improve, or apply existing knowledge in a new regime. Its baseline, delta, dependencies, evidence, and unresolved qualifications must remain traceable. Citation counts, rhetorical emphasis, publication venue, and self-declared novelty are not sufficient grounds for a contribution judgment.

### 8. Query-independent, human- and agent-auditable knowledge

A query may retrieve, summarize, or trigger new work, but MUST NOT silently redefine a canonical source, alter an existing claim, narrow an authoritative verification scope, suppress relevant conflict, or promote provisional output into accepted knowledge. Query-relative products may have explicitly bounded authority, but must remain distinguishable from query-independent paper records, assessments, releases, and knowledge entries.

Knowledge products MUST be usable by both people and computational agents without depending on an uninspectable fluent interpretation. Human-readable explanations should connect to structured, machine-checkable records, and structured records should preserve enough context and semantics to remain scientifically interpretable.

## Version Responsibilities

Every version specification MUST:

1. identify the portion of the Mission and Normative Ideal it serves;
2. define its version-specific primary deliverable without presenting that deliverable as the project’s ultimate purpose;
3. state its scope, acceptance criteria, non-goals, and non-implications;
4. preserve every applicable Constitutional Principle;
5. identify any principle not yet operationalized and mark it as future work rather than weakening or redefining it;
6. explain how its artifacts remain interpretable and reusable by later versions;
7. distinguish constitutional requirements from version-specific implementation choices.

Version-specific implementation rules may become stable and shared over time. Such rules should be documented separately from this Charter so that operational precision can evolve without causing mission drift. The first candidate for that shared implementation layer is the exact-source contract: the concrete identifiers, immutable source bindings, locators, integrity checks, and provenance requirements by which implementations satisfy Principle 1.

## Amendment Procedure

A constitutional amendment MUST:

1. be proposed through a pull request that identifies the exact Charter version to be amended and the exact bytes of the proposed change;
2. include a public rationale and an analysis of every Constitutional Principle and Version Responsibility affected, including compatibility, migration, and non-promotion consequences;
3. receive review from the project maintainer or other formally delegated repository authority and from every relevant scientific, contract, security, rights, or governance specialist implicated by the change, with each required review binding the exact proposed bytes through an immutable commit or tree identity or an equally unambiguous public review-system identity;
4. receive an explicit, publicly recorded approval from the project maintainer or repository authority after the required specialist reviews are complete, with that approval binding the same exact proposed bytes;
5. assign a new Charter version; and
6. preserve the superseded Charter text and the complete amendment history as immutable, addressable Git history.

The exact reviewed amendment object MUST identify an exact full base commit ID, the complete proposed path set, and, for every path, exact base and target entries, each expressed as explicit absence or the tuple `(Git tree-entry mode, Git object type, full object ID)`. An equivalent base-tree/target-tree formulation is acceptable only when it uniquely identifies the same complete delta. Reviews and the later approval may bind an isolated candidate commit only when its parent and tree mechanically provide that complete identity. A branch name, abbreviated ID, mutable review head, path list without exact entry tuples, blob-only identity, or prose summary is insufficient. The base and target entry identity is fixed before review; recording the later qualifying commit is not part of the reviewed bytes and therefore creates no circularity.

An approved proposal becomes effective only through a **dedicated post-approval qualifying amendment commit** integrated into canonical authoritative `main` after all required exact-change reviews and approval. A pre-integration review candidate MUST NOT itself be that qualifying commit. The integration record MUST designate the qualifying commit's Git first parent by full object ID. Against that first parent, the commit MUST change exactly the reviewed path set and no other path, with a change defined as any difference in absence, tree-entry mode, object type, or object ID. Every designated first-parent entry and every resulting entry MUST match its reviewed base or target tuple or explicit absence, respectively, and every entry outside the reviewed path set MUST remain unchanged. A mode-only or type-only mutation MUST be rejected even when the blob object ID is unchanged. If the qualifying commit is a merge, only its Git first parent defines this delta; no second or later parent may supply or obscure it. A squash, rebase, cherry-pick, or non-merge integration is acceptable only as a new, dedicated post-approval commit satisfying the same first-parent entry checks.

The stable amendment record is that dedicated commit's full Git object ID. The amendment's effective date is its Git committer timestamp, which MUST be later than the recorded final approval time; neither candidate creation nor later approval gives the amendment retrospective effect. A version label, status label, stated date, author or candidate timestamp, uncommitted text, review candidate, or commit outside canonical authoritative `main` has no constitutional effect and cannot make an amendment self-ratifying.

Silence, implementation practice, schema evolution, release publication, or approval of a subordinate document never amends this Charter. If required authority, specialist review, exact-change binding, or qualifying canonical integration is unavailable, the proposal remains pending and has no constitutional effect.

An editorial correction may fix spelling, formatting, broken links, or metadata without a new constitutional version only when it does not change normative meaning, scope, authority, obligations, permissions, prohibitions, or conformance. Its substantive impact analysis and specialist review may be proportionate to that meaning-preserving scope, but it still requires a pull request and public explanation. All relevant reviews and explicit maintainer or repository-authority approval must bind its exact full-base, path-set, and base/target entry tuples or explicit absences, and it becomes effective only through its own dedicated post-approval qualifying amendment commit under the same first-parent, merge-handling, exact-entry, unchanged-other-entry, canonical-integration, stable-record, non-retrospective committer-timestamp rules above. A mode-only or type-only mutation with an unchanged blob object ID remains disqualifying. A pre-integration editorial review candidate can never itself qualify. Any disputed or potentially meaning-changing edit MUST use the full amendment procedure.

## Historical Applicability

Once adopted, this Charter applies prospectively from the qualifying ratification commit's effective date. A record, release, contract bundle, schema-bound artifact, assessment, decision, or other immutable object created before that commit remains interpreted under the exact contracts, policies, schemas, scopes, and authority boundaries that it bound at creation. Charter adoption does not silently rewrite, promote, reclassify, invalidate, certify, admit, or otherwise change such historical objects.

A later document may evaluate a pre-adoption object against this Charter, but the result is a new, separately attributable conformance assessment; it is not a mutation of the historical object. Every claim of Charter conformance made at or after adoption MUST bind or cite the exact adopted Charter version and its stable adoption record, beginning with `AgtXIv-Charter/1.0` and the qualifying ratification commit's full Git object ID. If no such binding or citation exists, Charter conformance MUST NOT be inferred.

## Interpretive Rule

When a version document, schema, implementation, or release appears to conflict with this Charter, the interpretation that preserves this Charter's mission, distinctions, provenance, uncertainty, and non-promotion rules takes precedence. If the conflict cannot be resolved by interpretation, the subordinate artifact must be revised or explicitly marked non-conforming; it cannot amend the Charter by implication.
