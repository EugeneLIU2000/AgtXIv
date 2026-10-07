# AgtXIv schema v0.4 — Design: corpus dependency graph and foundation analysis

**Date:** 2026-09-25 (revised the same day after a five-lens adversarial critique, then after the owner decided
the gaps the implementers reported, then after the owner's corpus and cost decisions: see Revision 3 below; Revision 3
was then corrected after two independent static reviews, 2026-09-26, see the end of Revision 3).
**Status:** Design. The contracts, Neo4j schema and host code are built from this document; no corpus
instance has been run, no model has been called and no Neo4j server has been started.
**Ladder:** schema contract ladder v0.4 (`$id` prefix `https://agtxiv.org/schema/research/0.4.0/`).
This is not the superseded AgtXIv *protocol* v0.4 of
`docs/specifications/v0.3-to-v0.4-architecture-changes.md`. In that document's terms, the v0.4 corpus
graph is `PaperInteractionGraph` at claim resolution (cycles allowed) and a query view of it is
`MathClaimDependencyDAG(q)`; `PaperBuildDAG(q)` is not produced.
**Builds on:** schema v0.3 (merged 2026-09-24). **Inputs:** `docs/LIGHTWEIGHT_DAG_MODEL_RESEARCH.md`
(2026-08-16); TheoremGraph (`References/2606.25363`); the ICML 2026 position paper on theory-level
autoformalization (assessment: `docs/literature/2026-09-25-theory-level-autoformalization.md`).

Numbers are MEASURED (with source), CITED (with reference), OFFICIAL (a provider's dated page) or ESTIMATED.

**Revision 3 (2026-09-25, owner decisions, applied to this document, the contracts and the host):**

- **EQUAL_FULL.** Every accepted paper receives the same full claim extraction; no ranking decides which papers a
  model reads. The audit arm and the prioritized arm are withdrawn (§6.4).
- **Broad corpus.** Many same-field papers on different topics are what reveals shared foundations. Papers that
  derive results in equations without theorem environments (including experiment-plus-theory papers) are eligible
  (§6.2); cited papers (EXPANSION) and papers a model search proposes (DISCOVERY) are admitted, counted apart from
  the random sample (§6.3, I-14).
- **Fully automatic judgement.** No stage waits for a person. Extraction quality is measured by a blinded panel of
  model judges calibrated with controls (AUTO_EVAL_V1, §11.2); every stage gate is a rule pre-registered at S0 and
  applied by the host (§11). Human labels become an optional audit of the panel.
- **Cost basis.** A WHOLE_PAPER_FOCUS extraction mode keeps the whole paper as one cache-stable prompt prefix
  (§7.2); the projection for 10,000 papers on MiMo-V2.6-Flash is in §1.1.
- **Review corrections (2026-09-26).** Two static reviews of the Revision 3 code found gaps that are now closed:
  the P0 gate recomputes every stored estimate under the manifest rule and checks that each input is the unedited
  record its id names (§11.3); strata carry the producing `method_version`, and only the corpus extraction version
  can admit MODEL_EXTRACTION; decoys match the kind of the premise they replace, the false-positive rate is taken
  per decoy rule and the worst is used, and decoy contamination is excluded more strictly (§11.2); a USED quotation
  needs 12 characters and may be extended by at most 80; the cost projection is tied to the run and states that
  focus-mode tokens grow as S² (§1.1); unreadable sources are UNDETERMINED, not INELIGIBLE (§6.2); coverage uses
  the ledger's terminal states and a rejected model response may be retried (§6.4, §7.4); a PRIMARY analysis needs
  its P0 GO, the corpus manifest and a complete coverage report (§8.1).

---

## 1. What changes and why

v0.3 followed one query paper along its chain into Lean. In the retained four-paper graph 401 of 683
nodes (59%) are unresolved requests or occurrences (MEASURED, main checkout
`schema v0.3/runs/research-doi-available-20260922`), and formalization is the expensive tier.

v0.4 orders the work by cost:

```
Stage 1  CORPUS GRAPH    many same-field theory papers → typed claim dependency graph (Neo4j projection)
Stage 2  FOUNDATIONS     graph analysis → early, widely depended-upon claims and works (nominations)
Stage 3  KNOWLEDGE BASE  nominations → library audit, human review, auto-formalization (v0.3 machinery)
```

Stage 1 must itself be cheap. A v0.3 extraction prompt re-sends the whole paper's source, its
occurrence inventory and its anchor list with every output scope: one retained 384,919-byte prompt is
33% source, 44% occurrence inventory and 22% anchors (MEASURED,
`research-luna-continuation-20260920/.../batch-0025/.../prompt.txt`); the median call used 156,608
input tokens on a 118 KB paper (MEASURED, 22 Luna receipts). With 39 scopes that paper needed about
6 M input tokens (ESTIMATED, n = 1, 2,048-byte focus); 1,000 papers would need billions (ESTIMATED).

v0.4 therefore builds the graph cheap-first: a deterministic tier from `\ref`/`\cite` anchors that v0.3
`ingest.py` already parses; automatic measurement gates (§11) before any model spending; then the same model
extraction of every paper and retrieved matching (§6.4, §7), with prompts whose billed cost is dominated by terms
linear in the paper's size when the prompt cache works (§1.1).

The deterministic tier is thin and its yield must be measured, not assumed. On the four retained papers
there are 953 anchors; 324 resolve to an automatic occurrence, but 224 of those are display equations
and 69 are theorem or definition environments; 56 `\ref` and 27 `\cite` anchors lie inside an owned
proof; one paper (`quant-ph/9705052v1`) has no theorem environment and no owned proof (MEASURED).
TheoremGraph reports 98.8% LLM-judged precision for within-paper theorem-environment edges in math
papers (CITED); this is not assumed to transfer.

### 1.1 Cost basis (host/cost.py)

The v0.3 layout re-sent the whole source and inventory with every 2 KB scope: calls ∝ S and each call ∝ S, so its
input grows as S² in the source size S, and nothing was laid out for a cache. WHOLE_PAPER_FOCUS keeps that shape —
about βS/focus_bytes calls per paper, each carrying the whole paper as a prefix of about τS tokens — so **its input
tokens also grow as S²** (a correction of the first Revision 3 text, which said both v0.4 modes grow as S). What
changes is the price: the prefix is byte-identical across a paper's calls, so from the paper's second call on a
provider prompt cache can bill it at the cache-hit price, 1/50 of the miss price for MiMo-V2.6-Flash. With the cache
working, the money is dominated by the terms linear in S (each paper's first call and the output); without it, it
grows as S² at the miss price (the bracketed figures below). LOCAL_BATCH sends only a batch and its local context and
grows as S. The cache pays only if one paper's foci reach the provider back to back inside the cache lifetime, which
the provider pages do not state, so the dispatcher sends a paper's foci consecutively; whether Batch API requests hit
the cache is documented only by the batch cache-hit price. `cache_efficiency` therefore stays ESTIMATED until pilot
receipts measure it.

The formulas are in `host/cost.py`. `cost.project` reads the pricing file itself (the recorded digest is of the
prices used); takes each paper either as a source size (a MODELLED plan) or as the plan the host's prompt builder
MEASURED (`cost.focus_plan`: calls, focus bytes, prefix bytes, prompt bytes); reserves budget in the ceiling's unit
for S7, AUTO_EVAL_V1 and DISCOVERY calls (`other_stages`) and for what the ledger has already spent; and lists only
the parameters its formulas used, each labelled MEASURED, OFFICIAL, POLICY (a host choice: the output reserve, the
local batch size) or ESTIMATED. Wall-clock is `max(calls/RPM, tokens/TPM)` in real time and the provider's 24 h
completion window for Batch jobs submitted together. The P0 gate refuses a projection that uses an ESTIMATED
parameter or ESTIMATED sizes, covers fewer than `target_size` papers, is of another model than the one evaluated,
leaves no room under the ceiling, or does not fit the context window (§11.3).

Prices: MiMo-V2.6-Flash, overseas pay-as-you-go, per million tokens: cache hit $0.0028, cache miss $0.14, output
$0.28; Batch API half of each; 1 M context, 128 K output, 100 requests and 10 M tokens per minute (OFFICIAL,
mimo.mi.com pages dated 2026-09-21/22, `profiles/pricing-mimo-20260922.json`). Sizes: the 8 text sources the v0.3
runs acquired, mean 153 KB, repeated to 10,000 papers (MEASURED, chain-selected, not a random sample). Parameters:
0.40 tokens per byte, 0.621 focus fraction, 0.887 visible output tokens per focus byte, retry factor 1.2
(MEASURED on GPT receipts); 500 reasoning tokens per call, cache efficiency 0.9 (ESTIMATED).

| S6 mode, 10,000 papers | calls | real-time API | Batch API | real-time wall-clock at 100 RPM |
|---|---|---|---|---|
| WHOLE_PAPER_FOCUS, 8 KB focus | 139 k | $638 ($2,038 if no prefix hits the cache) | $319 ($1,019) | ≈ 23 h |
| WHOLE_PAPER_FOCUS, 2 KB focus | 557 k | $1,414 ($7,302) | $707 ($3,651) | ≈ 93 h |
| LOCAL_BATCH, 8 KB batches | 139 k | $534 | $267 | ≈ 23 h |
| v0.3 layout (not a v0.4 mode) | 610 k | ≈ $23,400 | ≈ $11,700 | ≈ 12 days (TPM-bound) |

About half of the focus-mode cost is output (the model writes each claim back); 3,000 reasoning tokens per call
instead of 500 adds about $100 (real-time). S7 retrieved matching, discovery searches and the P0 pilot are
additional and ESTIMATED at $100–400, tens of dollars, and about $20 (real-time). The MiMo tokenizer, cache hit rate,
thinking length and validation rate are unmeasured and are P0 measurements (`PENDING_TESTS` V04-11).

## 2. Invariants

Carried from v0.3 (design 2026-09-19 §3–§7, `schema v0.3/host/GRAPH.md`):

- **I-0** No model output sets a state, disposition, layer, coverage, rank or blocker.
- **I-1** No state, field or page says VERIFIED. The strongest Stage 3 sentence stays
  "`q` holds CONDITIONAL ON {P₁…Pₖ}".
- **I-2** Self-reported confidence never passes an automatic gate.
- **I-3** Citation is not dependency. Only `PREMISE_OF` and `CONCLUDES` are traversed as dependencies.
- **I-4** AND inside a junction; OR only across distinct derivations (§3.3).
- **I-5** Layers are derived from the edge set, never stored as input or written by a model.
- **I-6** A root is FRONTIER unless there is exhausted-search evidence. A corpus root is not a historical
  origin.
- **I-7** Exact byte binding proves location, not meaning.
- **I-8** Evidence is immutable; corrections are new records.
- **I-9** Promotion is a human judgement bound to a digest.

New:

- **I-10** Analysis produces **nominations**, never status (schema v0.1 `SYSTEM-REVIEW.md`, NG-13).
- **I-11** Every logical element records the method that proposed it; analysis can be re-run per method
  set, and mixed-method results say so.
- **I-12** Neo4j is a rebuildable projection of one delta-set manifest plus one review set. It is never
  the authority and never writes back.
- **I-13** Nothing that may be shared contains verbatim e-print text of a paper whose licence forbids
  redistribution (arXiv default licence). Verbatim text stays in the private artifact store.
- **I-14** A statistic states its count basis — `SAMPLE_ONLY` (only randomly sampled papers count as
  dependents) or `ALL_ADMITTED` (expansion and discovery papers count too) — and the two are never pooled.
  Traversal may pass through every admitted paper under either basis (§6.3, §8.1). (Revision 3 replaces the
  uniform-versus-prioritized label: under EQUAL_FULL every paper has the same coverage.)
- **I-15** An automatic judgement is a measurement by a declared instrument: a frozen panel of judges, blinded
  cards, stated controls. It never sets a disposition or a status; every statistic computed from it is labelled
  `AUTO_PANEL` and lists its assumptions; a USED verdict counts only with a quotation the host bound (I-7).

## 3. The logical graph

### 3.1 Vocabulary (the chain-build frontend made into data)

`slides/chain-build/gen_chain.py:99-133` draws a support group as legs from each member into one
**junction** ("all of these, jointly") and one **arrow** from the junction to the claim it discharges
("therefore"), premises below, L0 at the bottom. v0.4 stores exactly that:

```
(premise)-[:PREMISE_OF {id, position, role, use_site}]->(:Junction)-[:CONCLUDES {id}]->(conclusion)
```

A single-premise junction is still a junction node. There is no direct premise→conclusion edge.
Premise-capable: `Claim`, `Placeholder`. Conclusion-capable: `Claim`, `Placeholder` of kind
`EXTERNAL_REQUEST`.

### 3.2 Typed legs

The logical type lives on the leg: 31 of 56 targets in the authored DAG receive premises of mixed
types (MEASURED, `Stabilizerness/dag/claim-dag.json`), which v0.3 flattened to `PROOF_DEPENDENCY`.

- `role` ∈ {`DEFINITION_DEPENDENCY`, `SCIENTIFIC_CLAIM_DEPENDENCY`, `SCOPE_DEPENDENCY`,
  `PROOF_DEPENDENCY`, `BRIDGING_DEPENDENCY`, `UNCLASSIFIED`}. Deterministic legs are `UNCLASSIFIED`
  unless a published host rule assigns a role.
- `use_site` ∈ {`STATEMENT`, `PROOF`, `UNKNOWN`}. From v0.3 anchors: PROOF = the anchor lies in the
  claim's owned proof (`proof_owner_claim_ids`); STATEMENT = owner minus proof owners (v0.3
  `owner_claim_ids` includes proof owners, `ingest.py:817-822`).
- `position` = the leg's index in the junction's ordered leg list.

### 3.3 Derivations, readings, and OR

Two junctions into one conclusion mean different things:

- **Different derivations** (OR): genuinely different ways to establish it.
- **Different readings** of one derivation: competing premise-set hypotheses about the *same* argument
  from different methods. Treating readings as OR would accept a claim if *either* hypothesis held.

`derivation_id` rules (v0.3 `SupportGroup.route_id`, never set by v0.3 code, becomes this field):

| derivation_id | used for |
|---|---|
| `statement` | one statement junction per (conclusion, reading_method, method_version): that reading's `use_site = STATEMENT` legs. No other junction carries a STATEMENT leg. Analysis combines the statement junctions of admitted readings by `establishment_reading` (§8.1: under UNION every reading's statement legs, under ONLY(methods) the union of the admitted methods' statement legs) into the statement junction of §4.1. |
| `proof:<digest(sorted proof-span occurrence ids)>` | an argument located in a proof span. Readings are combined only when their derivation ids are equal. Anchors in two proof spans give two derivations. |
| `unlocated:<method>:<k>` | a model-reported argument that binds to no proof span; never combined with another method's reading. |
| `source:<paper_version_id>:<match_key>` | resolution of an external request by one match row; `match_key = digest(sorted upstream claim ids)`. Each SINGLE_CLAIM row and each JOINT_SUPPORT row is its own derivation (v0.3 `recursive_graph.py:187-190`). Readings of it are re-judgements of the same row (model vs human). |

A deterministic reading that joins what a model split into `proof:` and `unlocated:` derivations is
kept separate, never merged into the model's OR.

### 3.4 Placeholders and citation groups

`Placeholder{kind}` (one shape, as v0.3 `library.PLACEHOLDER_KINDS`):

- `EXTERNAL_REQUEST` — "the statement in cited entry B that claim C uses". Created only by a *used*
  citation (v0.3 `external_citation_keys`, or a `\cite` inside an owned proof at the deterministic
  tier), never by a mention. Identity is paper-local: `digest(citing claim, bibliography entry,
  citing derivation_id)`, independent of how the entry resolves to a work. It carries the `\cite`
  optional argument (e.g. "Theorem 3.2") as `locator_text`. A multi-key `\cite{A,B}` yields one request
  per key sharing `citation_group` = the anchor id; `citation_group_semantics` ∈ {`AND` (default),
  `OR`} is an analysis policy, and importance is reported under both.
- `UNRESOLVED_OCCURRENCE` — an internal reference that could not be bound to one claim, with a reason
  (`AMBIGUOUS_OR_SELF_CLAIM`, `NOT_YET_EXTRACTED`, `SHARED_OCCURRENCE_EXPANSION_CYCLIC`,
  `NON_ENVIRONMENT_TARGET` for equation and prose targets).

Placeholders carry a hard blocker, are never nominated individually, and are pooled into works (§8.3).

### 3.5 Works, bibliography entries and work-level claims

- `BibEntry` — one bibliography row of one paper version (paper-local, from v0.3 `bibtex` / `ingest`).
- `Work` — a bibliographic entity. `BibEntry -[:RESOLVES_TO {method, basis}]-> Work`. Identifier upgrades
  never rename: two works that are the same are linked by `SAME_WORK {basis}` with basis
  `HOST_RULE_ARXIV_DOI` (DOI `10.48550/arXiv.X` ↔ arXiv id), `HOST_RULE_ARXIV_METADATA_DOI`,
  `MODEL_MATCH` or `HUMAN`. Pooling uses the connected components admitted by the analysis policy
  `work_identity` ∈ {`EXPLICIT_IDS_ONLY`, `PLUS_REVIEWED_SAME_WORK`, `PLUS_CANDIDATE_SAME_WORK`}.
- An admitted `CORRECTS (W′→W)` blocks resolutions from W until reviewed (v0.3 design §4.5).
- A **work-level claim** is a `Claim` with `origin = WORK_LOCATOR` (e.g. "Nielsen–Chuang Thm 10.1,
  p. 437"), entered by a person or a library audit, `STATED_BY` a `Work`; it lets books and theses
  resolve requests without a source file. Its identity includes `work_locator_text` (§5.2).

### 3.6 Non-logical relationships

Never traversed as dependencies: `STATES` (PaperVersion→Claim), `STATED_BY` (Claim→Work),
`READS` (ClaimReading→Claim), `PART_OF` (Claim→Claim), `HAS_ENTRY` (PaperVersion→BibEntry),
`RESOLVES_TO` (BibEntry→Work), `REQUESTS_FROM` (Placeholder→BibEntry), `MENTIONS` (Claim→BibEntry),
`RESTATES_RESULT_OF` (Claim→BibEntry, a `\cite` in a theorem header), `VERSION_OF`
(PaperVersion→Work), `SAME_WORK`, `CORRECTS` (Work→Work), `SUPERSEDES` (ClaimReading→ClaimReading),
`ASSERTS_PRIMITIVE` (PrimitiveAssertion→Claim), `INCLUDES {admission, round, sampling_record_id}`
(Corpus→PaperVersion). Reviews, analysis runs and nominations are artifacts, not projected in v0.4
(§9.2).

### 3.7 Strict invariants

Neo4j Community enforces only uniqueness (§9.3). The host checks every invariant before load
(`host/invariants.py`); the auditable ones are re-checked after load by zero-row queries
(`neo4j/audits.cypher`, each returning `(invariant, id)`).

| # | Invariant | Where |
|---|---|---|
| G1 | A `Junction` has exactly one outgoing `CONCLUDES` and ≥ 1 incoming `PREMISE_OF`. | host + audit |
| G2 | `PREMISE_OF` goes from a premise-capable label to a `Junction`; `CONCLUDES` from a `Junction` to a conclusion-capable label. | host + audit |
| G3 | Only `PREMISE_OF` and `CONCLUDES` join logical nodes as dependencies; `PART_OF` is the only other type allowed between two `Claim`s. | host + audit |
| G4 | A junction's conclusion is not one of its premises. | host + audit |
| G5 | Enumerated fields take listed values; `position` of one junction's legs is `0..n-1`. | host (schema) + audit |
| G6 | Every id equals the digest of its identity fields (§5.2). | host only |
| G7 | A `source:<pv>:*` junction concludes an `EXTERNAL_REQUEST`; each Claim premise is `STATED` by `pv` (or `STATED_BY` a work in the request's work-identity class); `pv`'s work is in that class under the loading policy. `derivation_id` starts with `source:` iff the conclusion is a request. | host + audit |
| G8 | An `EXTERNAL_REQUEST` has exactly one `REQUESTS_FROM`, and is a premise of ≥ 1 junction whose conclusion and derivation equal those in its identity. | host + audit |
| G9 | Every projected element has a non-empty `asserted_by` whose entries are in the loaded manifest. | host + audit |
| G10 | Every `Claim` has exactly one `STATES` (origin `PAPER_VERSION`) or one `STATED_BY` (origin `WORK_LOCATOR`). | host + audit |
| G11 | `disposition` is derived only from the loaded review set; only an ACCEPT review yields `SOURCE_FROZEN_HUMAN_SIGNED`. | host + audit |
| G12 | A `proof:*` or `unlocated:*` junction has only premises `STATED` by the conclusion's paper version or placeholders created by its claims. | host + audit |
| G13 | At most one `statement` junction per (conclusion, reading_method, method_version); no other junction carries a `STATEMENT` leg. | host + audit |
| G14 | No junction uses a superseded `ClaimReading` basis — a junction's basis is every `ClaimReading` of its conclusion with the same (reading_method, method_version), and it violates G14 if any of them is superseded; `SUPERSEDES` is acyclic and each reading has at most one successor. | host + audit |
| G15 | A `PREMISE_OF` id is `digest(junction id, position)`; relationship ids are unique per type. | host + audit |

Cycles are allowed in the corpus graph; they are an analysis diagnostic (§4.1), not a load error.
Acyclicity is required only of a selected route (schema v0.1 `STORAGE.md:57`); this resolves the
conflict with `docs/specifications/mathematics-pipeline.md:477` in favour of the corpus reading.

## 4. Layers

### 4.1 Derivation layer (computed)

Over the policy-effective graph (§8.1), with `value` in ℕ ∪ {∞}:

```
root r (no effective junction):        value(r) = 0 if r ∈ base set B, else ∞
junction j:                            value(j) = max over premises p of value(p)
external request R (transparent):      value(R) = min over its source junctions j of value(j)
claim v:                               value(v) = 1 + max( value(statement junction of v),
                                                          min over derivation junctions j of value(j) )
                                       (a missing statement junction contributes 0; a claim
                                        with a statement junction but no derivation uses it alone)
```

AND takes the maximum, OR the minimum; only claims add a layer, so crossing a paper boundary through a
request costs no extra layer. Two structural host rules join identities without a model and add no layer: an
`UNRESOLVED_OCCURRENCE` whose occurrence has a whole Claim in the graph (other than the placeholder's creator) takes
that claim's value — it is the same occurrence — and a whole Claim whose parts are in the graph and that has no
derivation of its own takes the maximum over its parts, which state it jointly. The v0.3 export (§10) adds neither
rule: there the placeholder stays a blocker. The base set `B` is a policy: `ALL_ROOTS` (structural) or
`PRIMITIVE_ASSERTED` (only roots with a `PrimitiveAssertion`, §8.2); placeholders and
`NO_SUPPORT_PROPOSED` roots are outside `PRIMITIVE_ASSERTED`.

The system has a unique solution because every claim step adds 1. It is computed top-down (Knuth's
superior-function algorithm): roots in `B` start at 0 and all other nodes at ∞; a junction fires when
its last premise is finalized; a node is finalized at the smallest value among its fired junctions (plus
1 for claims); unfinalized nodes are ∞. Upward iteration from 0 is wrong (it never terminates on a pure
2-cycle) and must not be used. `route_status = ROUTE_UNDETERMINED` iff `value = ∞`; every nontrivial
strongly connected component is listed as a CYCLE diagnostic, and a finite member records
`in_cycle = true`. This deliberately differs from v0.3 `graph._condense`, which makes every SCC member
undetermined; `cycle_policy` ∈ {`FIXPOINT` (default), `CONDENSE_V03`} allows comparison.

Under under-extraction the layer is a **lower bound**: missing premises can only lower a maximum, and
the layer can rise when requests are resolved.

### 4.2 Other orderings

- `wave_q(v)`: minimum number of junctions from a query `q` down to `v` (`gen_chain.py:34-46`); a query
  view, never stored.
- Authored layers (the frontend's L0–L8) are display data only; 10 of 129 authored edges fail to rise
  a layer (MEASURED), so they are never read by analysis.
- The theory-level *tower layer* (L0 primitives … L3 targets) is assigned in Stage 3 relative to a
  named library commit (§10), not in Stages 1–2, where a host rule would mislabel.

## 5. Identity, provenance and manifests

### 5.1 Canonical form

All v0.4 ids are `<prefix>:<64-hex>` from v0.3 `core.digest(core.canonical(·))` (sorted keys,
`ensure_ascii=False`, compact separators, trailing newline), untruncated. v0.3 ingest ids (32-hex,
another canonical profile) are kept only as `v03_id` provenance; v0.1/V3 digests are never mixed.

### 5.2 Identifiers

| Entity | id = prefix + digest of |
|---|---|
| PaperVersion | `arxiv:<base>v<n>` (no digest; arXiv only in v0.4) |
| Work | `work:` + (identity_basis, normalized value): arXiv base id, lowercased DOI, OpenAlex id, or `bib_digest` = digest(normalized title, year, first-author surname), stored on the row (required for `BIB_DIGEST`) |
| BibEntry | `bib:` + (paper version, citation key, entry byte span); paths relative to the paper's source root |
| Occurrence | carried from S2 as `occurrence_id` = `occ:` + (paper version, path relative to the paper's source root, byte span, span sha256) |
| Claim | `claim:` + (origin, paper version or work, sorted occurrence ids, part, and for `WORK_LOCATOR` the `work_locator_text`); `part` = `whole` or `part:<k>` with `k` ordered by the byte start of the part's locator inside the occurrence. **No method-written text.** |
| ClaimReading | `reading:` + (claim, method, method_version, statement sha256, conditions sha256, kind) |
| Junction | `junction:` + (conclusion, derivation_id, reading_method, method_version, [(premise, role, use_site)] in order) |
| Placeholder | `placeholder:` + (kind, citing claim, bib entry or occurrence, citing derivation_id) |
| PrimitiveAssertion | `primitive:` + (claim, method, basis) |
| Relationship | `rel:` + (type, start, end, key properties); `PREMISE_OF` = (junction, position) |

`content_sha256` = digest of exactly the identity fields, so equal id implies equal content; the loader
check catches collisions and host bugs, not legitimate re-assertions.

Model claims must bind to S2 occurrence ids (`source_occurrence_ids`); a model claim with no enclosing
environment takes its identity from its locator span as a new occurrence. When an occurrence yields
several claims, each needs a distinguishing locator; otherwise the reading is rejected as
`AMBIGUOUS_PART` and retained as a failed delta, never guessed. Parts get `PART_OF` the whole claim;
legs another method drew to the whole expand to all parts and are flagged
`EXPANDED_TO_PARTS` (the v0.3 `MULTI_CLAIM_OCCURRENCE_EXPANDED` idea).

### 5.3 Deltas and manifests

- **GraphDelta** — immutable content-addressed JSON: `{delta_id, stage, method, method_version,
  subject, parents, produced_by, nodes{Label: [rows]}, edges: [rows], measurements?}`,
  `delta_id = digest(body)`. `stage` ∈ {`S1`…`S9`, `HUMAN_ENTRY` (method `HUMAN`), `LIBRARY_AUDIT`
  (method `LIBRARY`)}; the last two carry `PrimitiveAssertion`s, `WORK_LOCATOR` claims and
  human-entered edges. Only an `S1` delta may carry `PaperVersion` rows (the contract refuses any other
  stage that does). `measurements` holds host measurements about the delta's subject (e.g. S3's
  `deterministic_yield`), never graph content. The same element may be asserted by several deltas;
  per-assertion provenance lives in the delta store, and the projection keeps `asserted_by: [delta_id]`
  and `methods: [method]`.
- **Merge rule** — an id asserted by several deltas must carry identical rows (the loader refuses
  otherwise); method-dependent data lives only in method-scoped records (readings, junctions) or in
  delta `measurements`.
- **DeltaSetManifest** — `{manifest_id, corpus_id, parent_manifest_id, deltas[], excluded[{delta_id,
  reason}]}`; valid only if closed under parents and every edge endpoint is asserted by an included
  delta. `manifest_id` = digest of the manifest body without `manifest_id` and `created_at`. A
  correction is a new manifest, not a retraction delta.
- **ProjectionManifest** — a singleton node naming what Neo4j holds: `{delta_set_digest,
  review_set_digest, state ∈ BUILDING|READY|FAILED, loader_version, audit_counts}`; readers require
  `READY`. `delta_set_digest` = `sha256:` + the manifest id's hex; `review_set_digest` = the digest of
  the filled review rows in canonical order (the review set's own `review_set_digest`).

### 5.4 Methods and routing

`method` ∈ {`DETERMINISTIC_ANCHOR`, `HOST_RULE`, `MODEL_EXTRACTION`, `MODEL_MATCH`, `HUMAN`,
`LIBRARY`} with `method_version`. Model methods record a v0.4 `ModelSelection`: routing policy
`operation-routing-v2`, which adds `paper.extract_local`, `paper.extract_focus` and `corpus.discover` (LIGHT) and
`dependency.match_retrieved`, `leg.judge` and `match.judge` (DECISION) to the v0.3 operations and records the model's
`training_cutoff` (`value` or `UNKNOWN`, with source). The v0.4 operations admit the v0.3 GPT models and
MiMo-V2.6-Flash/Pro; a MiMo route names its thinking mode (`thinking-enabled` fixes temperature at 1.0) instead of an
effort. Two profiles exist — `profiles/engines-v2.json` (GPT) and `profiles/engines-v2-mimo.json` (the metered MiMo
candidate) — and a plan freezes one; an AUTO_EVAL_V1 panel may take one judge route from each, so its judges differ
in model family. Judge and discovery calls are ledger items with methods `MODEL_JUDGE` and `MODEL_SEARCH`; they write
records, never graph rows. v0.3 receipts keep `operation-routing-v1`.

## 6. Corpus and sampling

### 6.1 Corpus manifest (S0, HOST)

`CorpusManifest` freezes the field (primary arXiv categories, date window), the sampling frame (an
OAI-PMH `arXivRaw` harvest or a metadata snapshot, by digest and snapshot date), the eligibility program
and parser (sha256), size limits, the version rule (latest version on or before the snapshot date), the
seed, the target size, the coverage (`EQUAL_FULL`), the one S6 extraction policy of the corpus, the automatic
gate rules (§11), the PRIMARY analysis policy template (§8.1, with `admission_gate` null) and a budget ceiling (a
money ceiling names the digest of the pricing profile it is in).

### 6.2 Sampling and the estimand

The frame is ordered by `sha256(seed_utf8 ‖ 0x00 ‖ arxiv_base_id)` (a new rule modelled on
`agtxiv.random-paper-selection/0.1.0-experimental`, drawn without replacement). Candidates are examined
in that order until the target size is accepted; this is round 0, the `SAMPLE` round. Each examined
candidate gets exactly one outcome: `ACCEPTED`, `INELIGIBLE(reason)`, or `UNDETERMINED(class)` with
class ∈ {`TRANSIENT_NETWORK`, `NO_TEX_SOURCE`, `SIZE_LIMIT`, `MAIN_AMBIGUOUS`, `WITHDRAWN`,
`PARSE_FAILED`, `ID_NOT_FOUND`}; `TRANSIENT_NETWORK` is retried up to a frozen limit. In a `SamplingRecord`,
`reason` appears only on `INELIGIBLE`, `paper_version_id` only on `ACCEPTED`, and `order_key` never on an
`EXPANSION` candidate. The estimand population is **P = frame ∩ determinable by this pipeline ∩
eligible**; every statistic is an estimate over P, reported with its `UNDETERMINED` counts. S1 asserts
the `PaperVersion` row of every accepted paper (§7), so an accepted paper that later fails a stage keeps
its node and `INCLUDES` edge, stays in the sample with missing data, is never replaced, and counts in
every denominator.

Eligibility is decided after acquisition by the program `THEOREM_OR_DERIVATION_V1` (`host/eligibility.py`,
digest in the manifest): a paper is eligible iff its S2 parse has at least `min_theorem_like` theorem-like or
definition environments **or** at least `min_display_equations` display equations. The second arm keeps
physics papers that derive results in equations without theorem environments inside P, including
experiment-plus-theory papers with derivations (`quant-ph/9705052v1` has no theorem environment, MEASURED).
P-1 (§11) reports the eligible fraction on a grid of both parameters (`eligibility.grid`).

A paper whose source could not be read is `UNDETERMINED`, never `INELIGIBLE`, so an unreadable paper cannot pass as
one without derivations: no frozen source file, or the v0.3 issue `SOURCE_UNREACHABLE`, `SOURCE_ACQUISITION_FAILED`
or `SOURCE_MAIN_NOT_FOUND`, gives `NO_TEX_SOURCE`, and `SOURCE_MAIN_AMBIGUOUS` gives `MAIN_AMBIGUOUS`. A parse that
skipped part of the source (`SOURCE_ENCODING_UNSUPPORTED`, `SOURCE_INCLUDE_MISSING`, `DYNAMIC_INCLUDE_UNRESOLVED`,
`INCLUDE_OUTSIDE_SOURCE_ROOT`) is `ACCEPTED` if what was read meets the rule and otherwise
`UNDETERMINED(PARSE_FAILED)`, because the unread part could hold what is missing. The grid applies the same rule
at each grid point.

### 6.3 Expansions and discoveries

Two kinds of bounded rounds add papers outside the random sample, numbered from round 1 across both kinds; no
round re-examines an id examined in an earlier round, and neither kind is ever in P.

- **EXPANSION** — nominated or cited works, a frozen record `{source manifest, analysis run, selection rule, M}`.
  Only works with `terminal_kind = ARXIV_SOURCE_AVAILABLE` can be expanded; others get `LIBRARY_AUDIT` or
  `HUMAN_REVIEW`, which keeps "early" from drifting to the arXiv era silently.
- **DISCOVERY** — arXiv ids proposed by a model search (`corpus.discover`), a frozen record
  `{queries digest, receipts, M}`. The seed is derived by the host as `<manifest seed>/discovery/<round>`
  (`corpus.discovery_seed`), so it cannot be chosen after the proposals are seen. The host drops malformed ids,
  repeats and ids seen in earlier rounds, orders the rest by `order_key(seed, id)`, examines the first M like sampled
  candidates (acquisition, eligibility; `ID_NOT_FOUND` for an id the source does not know), and admits nothing by
  itself (I-0). The record counts every proposal once: proposed = dropped_invalid + duplicates + dropped_seen +
  not_selected + examined.

Papers enter with `INCLUDES.admission ∈ {EXPANSION, DISCOVERY}`. The analysis policy decides whether their claims
enter the graph (`traverse`) and whether they count as dependents (`count_basis`, I-14). The recommended
PRIMARY setting is `traverse = ALL_ADMITTED`, `count_basis = SAMPLE_ONLY`: a chain may pass through a cited or
discovered paper, while "how many papers depend on this" counts only the random sample, so the estimate stays
an estimate over P. Nominations are reported under both bases.

### 6.4 Equal coverage (EQUAL_FULL)

Every accepted paper of every round receives S6 under the manifest's one extraction policy, and every
`EXTERNAL_REQUEST` whose upstream paper version is in the corpus receives S7. No ranking decides which papers a
model reads, so there is no prioritized arm and no audit arm (both withdrawn in Revision 3), and no statistic is
conditional on a prioritization. `corpus.coverage_report` takes every round of the corpus and the ledger item of each
planned S6 work item, and accounts every accepted paper: `DONE` (every item DONE or SKIPPED, one DONE); `FAILED`
(every item terminal and one not DONE or SKIPPED; the paper keeps its row and counts in every denominator with
missing data); `INCOMPLETE` (an item still RUNNING, unregistered, or READY / QUOTA_WAIT with an attempt left); or
`MISSING` (no planned item). Terminal means DONE, FAILED, SKIPPED, ABANDONED, or READY / QUOTA_WAIT that the ledger
would no longer dispatch (`ledger.item(...)["dispatchable"]` false). A PRIMARY analysis waits until nothing is
`INCOMPLETE` or `MISSING` and the report is of this corpus and its extraction policy
(`gates.require_equal_coverage(coverage, corpus)`). The report accounts S6; S7 is accounted per nomination by
`match_coverage` (the fraction of requests to its work that S7 attempted), null until the ledger holds S7 attempt
records.

## 7. Stage 1: building the corpus graph

| Stage | Tier | Input → output |
|---|---|---|
| S1 ACQUIRE | HOST | ids → frozen sources in a configured git-ignored corpus data root (`host/acquire.py`: e-prints from export.arxiv.org, arXiv's host for programmatic access, unpacked by the v0.3 bounded adapter; first used 2026-09-26, `schema v0.4/runs/quant-ph-sample-20260926`). v0.3 `fetch_arxiv_source` limits; one shared arXiv rate token (≥ 3 s between request starts, all processes); versions, licence and category from the frozen OAI-PMH snapshot, not per-id calls. Its `HOST_RULE` delta asserts the `PaperVersion` row of every accepted paper from the frozen metadata and manifest (`parser_sha256` from `CorpusManifest.eligibility.parser_sha256`); later stages never re-assert `PaperVersion` and take this delta as a parent. |
| S2 PARSE | HOST | source → occurrences, labels, anchors, bibliography (v0.3 `ingest.extract_paper`, `bibtex.parse_bibtex`), plus the `\cite` optional argument and proof-header ownership (below). |
| S3 ANCHOR GRAPH | HOST | anchors → `DETERMINISTIC_ANCHOR` readings and junctions (`host/anchors.py`). |
| S4 WORKS | HOST | bib entries → `Work`, `RESOLVES_TO`, host-rule `SAME_WORK`; metadata adapters (Crossref, OpenAlex snapshot) only with network authorization. |
| S5 P-1 GATE | HOST | eligibility, density and yield (§11) → `GateDecision` GO, GO_WITH_EXPANSION or NO_GO (`host/gates.py`). |
| S6 EXTRACT | LIGHT | every accepted paper, one policy → `MODEL_EXTRACTION` readings and junctions (`paper.extract_focus` or `paper.extract_local`, §7.2). |
| S7 MATCH | DECISION | requests of one upstream paper version → `source:` junctions (`dependency.match_retrieved`). |
| S8 LOAD | HOST | manifest + reviews → Neo4j; audits (§9). |
| S9 ANALYZE | HOST | manifest (+ reviews) → metrics and nominations (§8). |

**Deterministic tier rules (S2–S3).** The conclusion is the THEOREM_LIKE or DEFINITION occurrence whose
owned proof contains the anchor (`use_site = PROOF`) or whose own span contains it (`STATEMENT`).
Premises are environment occurrences; `\eqref` (always) and prose targets become
`UNRESOLVED_OCCURRENCE` (`NON_ENVIRONMENT_TARGET`); a label that resolves to nothing yields an issue, not
a leg. A proof whose header contains `\ref{L}` is owned by L's claim, overriding adjacency, and that
anchor is excluded from its premises (`PROOF_HEADER_OWNERSHIP`). A `\cite` inside an owned proof creates
an `EXTERNAL_REQUEST`; a `\cite` in a theorem-like header creates `RESTATES_RESULT_OF` (host rule, its own
method, never merged with proof use); any other `\cite` is a `MENTIONS`. Each paper's S3 delta records
`measurements.deterministic_yield {theorem_like_environments, owned_proofs, proof_owned_anchors,
junction_bearing_conclusions}`.

### 7.2 Extraction (S6): two modes, one per corpus

Both modes use the v0.3 `CLAIM_RESPONSE_SCHEMA` with its `CLAIM_REFERENCE_V1` fields; it records no role or use
site, so model legs are `UNCLASSIFIED` / `UNKNOWN`. The corpus manifest fixes one mode and its `method_version`
for every paper (EQUAL_FULL).

**WHOLE_PAPER_FOCUS (`paper.extract_focus`, the recommended mode).** `extraction.plan_foci` cuts a paper's S2
occurrences, in source order and per file, into foci spanning at most `focus_bytes`; each occurrence belongs to the
focus that holds its start, and the focus scopes of a file are disjoint and cover it, so a quoted new claim belongs
to one call only. A cut falls only where a new occurrence begins after every member of the current focus ends, so a
nested occurrence stays with its container, and the first focus of a file starts at byte 0. Every prompt of the paper
is one byte-identical prefix — the instruction, every source file, an inventory naming each occurrence once by a short
alias (`o1`, `o2`, …) with kind and byte span, and the bibliography keys — followed by a FOCUS block of a few hundred
bytes. Body files (`.tex`, `.ltx`) are sent byte-exact; bibliography files (`.bib`, `.bbl`) and files that are not
UTF-8 are marked `context_only`, and no quotation binds there. A body file with no S2 occurrence gets no focus of
its own: it is read as context only, so a claim stated only in its prose is not extracted (a known gap). When two S2
claims share a span they share one occurrence id, and the canonical claim of the occurrence is the environment one
(`anchors.index`). The model emits the claims stated inside the
focus and may cite any occurrence of the paper as support; the host maps aliases back to occurrence ids (an unknown
alias is rejected as an unknown occurrence). Because the whole paper was supplied, an internal premise is always the
claim of the occurrence it names, of any kind: a derivation through display equations stays connected
(`(12) ← (10), (11)`) instead of ending in `UNRESOLVED_OCCURRENCE` placeholders. Two calls that name the same
occurrence assert the same Claim row, so their deltas merge. Quotations are bound with TeX comments masked (a
quotation that matches only inside a comment is `MODEL_LOCATOR_IN_COMMENT`) and a new claim's quotation belongs to
the occurrence that encloses it — the one the response names if it names one, else the innermost; a part claim is
identified by where it was quoted, so two quoted parts of one occurrence are two claims.

**LOCAL_BATCH (`paper.extract_local`).** Per claim batch the prompt carries: the batch's environments and owned
proofs; the statement text of occurrences they reference; the bibliography entries they cite; up to `B` bytes of
preceding section prose (policy); and an id-and-span-only inventory of those items with no duplicated text.
Premises may be cited only by ids supplied in the prompt; a non-environment occurrence stays a placeholder unless
the response also emits it.

Loss of LOCAL_BATCH relative to whole-paper context is **estimated in P0** by running both modes on the same
papers (`LOCAL_VS_WHOLE_RECALL`, §11.2); it is not recorded per claim, because a model that never sees a premise
cannot list it.

### 7.3 Retrieved matching (S7)

Requests are pooled per upstream paper version; the prompt carries the request, the citing claim's
reading and the upstream paper's candidate claim readings retrieved deterministically (same `\cite`
locator text, kind, lexical overlap), not two full sources. The v0.3 `MATCH_RESPONSE_SCHEMA` is reused;
quotations bind within the retrieved statement only, and the host extends a non-unique quotation to the
shortest unique enclosing span, the earliest-starting one on a tie, recording the rule name in a
`HOST_RULE` issue (v0.3's 8 of 22 validation failures were non-unique quotations, MEASURED).

### 7.4 Corpus ledger

A corpus SQLite ledger with one coordinator (the single writer; workers write only immutable artifacts):

- **Work item** key `(stage, subject_kind ∈ {PAPER_VERSION, CLAIM_BATCH, REQUEST_POOL, MANIFEST, JUDGE_CARD,
  DISCOVERY_QUERY}, subject_id, method, method_version, input_digest)`; judge calls are stage `EVAL`, method
  `MODEL_JUDGE`, and discovery searches stage `S1`, method `MODEL_SEARCH` (they produce records, not graph rows);
  states `READY → RUNNING(lease) → DONE | FAILED | QUOTA_WAIT | ABANDONED | SKIPPED`. An expired lease becomes
  `ABANDONED` and its reservation stays spent. `cost.call_cost` prices a receipt's usage for `settle`.
- **Provider window** `(provider, account_ref, OPEN | CLOSED_UNTIL(t) | CLOSED_UNKNOWN)`: a quota failure
  closes the window for all items (v0.3 exhausted its quota after 22 calls in one run, MEASURED). After
  it reopens, a `QUOTA_WAIT` item may receive one new attempt in total (new reservation, new receipt,
  never a replay). A model response the host checks refused (failure `RESPONSE_REJECTED`, model items only)
  returns the item to `READY` while attempts remain, else `FAILED`. These are the only automatic re-dispatches.
  `ledger.item` reports `dispatchable`, whether `reserve` would accept the item now or after its window reopens.
- Reserve-before-dispatch (every model dispatch reserves against `CorpusManifest.budget_ceiling`) and
  failure classification as in v0.3 (`SOURCE_READ_DEFECTIVE` only for source problems).

## 8. Stage 2: foundation analysis

### 8.1 Analysis policy

Frozen per run and digested into every output:

- `establishment_reading` ∈ {`UNION`, `ONLY(methods)`} — readings of one derivation for layers and
  establishment (UNION: all proposed premises jointly required; conservative).
- `importance_methods` — methods admitted to importance counts (only those the P0 gate admits, §11.3).
  Importance is reported as a **bracket**: lower bound from legs proposed by ≥ 2 admitted
  readings (or the only present reading), upper bound from the union. Ranking uses the lower bound. A
  cycle present only in the union is `READING_CONFLICT_CYCLE` and does not make its members undetermined
  under the lower bound.
- `work_identity`, `citation_group_semantics`, `cycle_policy`, base set `B`, `include_part_expansions`.
- `traverse` ∈ {`SAMPLE_ONLY`, `ALL_ADMITTED`} — whose claims enter the graphs; `count_basis` ∈ {`SAMPLE_ONLY`,
  `ALL_ADMITTED`} — whose claims make a paper dependent (I-14; `traverse = SAMPLE_ONLY` forces `count_basis =
  SAMPLE_ONLY`). The bootstrap resamples the counted papers only. A paper without an `INCLUDES` edge (a hand-built
  view) is treated as sampled.
- `nomination` (`FOUNDATION_V1`, threshold `T`, top `K`), `bootstrap` (`B_boot`, seed,
  `PAPER_REWEIGHT_V1`), `edge_precision` (estimates reference, or disabled).
- `status` ∈ {`PRIMARY`, `EXPLORATORY`} and `admission_gate`. The corpus manifest freezes the PRIMARY template
  before the first full run with `admission_gate` null; `gates.primary_policy` derives the PRIMARY policy of the
  run from it by keeping the importance methods the P0 gate admitted and naming that gate (a new `policy_id`).
  `analysis.analyze` refuses a PRIMARY policy unless it is given the P0 GateDecision it names (an unedited P0 GO of
  the corpus under the manifest's P0 rule), the CorpusManifest (the policy must equal `gates.primary_policy` of the
  two), and a complete coverage report of that corpus's extraction policy (§6.4), and unless every MODEL_EXTRACTION
  reading and junction of the view has the corpus extraction `method_version`. Every published list states its
  status and the number of runs on its manifest.

### 8.2 Metrics (a vector, never one score)

Per logical node (and pooled per work, §8.3):

| Metric | Definition |
|---|---|
| `layer`, `layer_basis` | §4.1; `layer_basis` = root classes used by the minimizing derivation |
| `route_status`, `in_cycle` | §4.1 |
| `dependent_papers` | `[lower, upper]` distinct counted corpus papers (excluding its own) with a claim `u ≠ v` having it as a transitive premise |
| `dependent_topics` | for nominated subjects: `[lower, upper]` distinct arXiv categories (primary and cross-lists, `ARXIV_CATEGORIES_V1`) of those papers — breadth across topics, reported and not ranked; categories cannot separate topics inside one primary category, which a later version may do by bibliographic coupling |
| `dependent_papers_by_depth` | the same restricted to witness paths of ≤ 1, 2, 3 junctions |
| `dependents` | claims `u ≠ v` of counted papers having subject `v` as a transitive premise (the subject never counts itself, also inside a cycle); exact for nominated subjects, otherwise a seeded bottom-k sketch marked ESTIMATED |
| `necessary_dependents` | for `B` = all roots and `B` = primitive-asserted: claims of counted papers finite before and ∞ after setting its value to ∞ (roots fixed before the knockout) |
| `direct_uses` | legs out of it |
| `date` | `{value, kind ∈ ARXIV_V1 \| ARXIV_VERSION \| JOURNAL_PUBLISHED \| BIB_YEAR \| UNKNOWN, precision, source}`; compared at year precision within compatible kinds; UNKNOWN in its own bucket; for a claim, the stating paper's date, not the result's |
| `root_class` | `PRIMITIVE` (only with a `PrimitiveAssertion {basis ∈ AXIOM \| ASSUMPTION \| STANDARD_NOTION \| HUMAN}`), `DEFINITION_NO_SUPPORT_PROPOSED`, `NO_SUPPORT_PROPOSED`, `EXTERNAL_REQUEST`, `UNRESOLVED_OCCURRENCE`, with the methods that examined it |
| `uncertainty` | its legs by method, role and disposition |

### 8.3 Work pooling

Requests are pooled per work-identity component: `citing_claims`, `citing_papers`, and the union of
their dependents; `layer(W)` = the minimum layer of source junctions resolving its requests, or
`UNRESOLVED`. Pooling measures a work's importance, not which result of it is used; `locator_text`
("Theorem 3.2") is kept to split pools later.

### 8.4 Nomination rule `FOUNDATION_V1`

A claim or work is nominated when `layer ≤ 1` (or, for a work, `UNRESOLVED`), its `layer_basis` contains
only `PRIMITIVE`, `IN_LIBRARY` or work-level-claim roots, and `dependent_papers.lower ≥ T`. Subjects
with a low layer that rests on open premises are listed separately as `LOW_LAYER_BY_OPEN_PREMISES`. A
`NO_SUPPORT_PROPOSED` claim meeting `T` is nominated with next action `EXTRACT` and cannot reach
`FORMALIZE` before a model extraction was attempted. Nominations come in three lists — definitions,
theorem-like claims, works — ordered by `dependent_papers.lower` (maximize), then `date` (minimize),
then `layer` (minimize); ties are broken by id and reported as rank intervals. Each nomination carries
witness paths (to counted papers), blockers, its count basis (I-14), `dependent_topics`, and a next action:
`ACQUIRE_SOURCE`, `EXTRACT`, `MATCH_REQUESTS`, `LIBRARY_AUDIT`, `HUMAN_REVIEW` or `FORMALIZE`.

Reported distortions: under-extraction (layers are lower bounds, §4.1); infrastructure bias (raw
centrality ranks the most generic results highest — `Eq.refl` is second by in-degree in Mathlib, CITED,
arXiv 2604.24797; Stage 3's library audit removes what Mathlib/Physlib provide); definition-level
importance is under-measured by the cheap tier (8 of 324 resolved anchors target definitions, MEASURED);
method mix (I-11).

### 8.5 Stability

- `PAPER_REWEIGHT_V1` bootstrap: multinomial paper weights, graph fixed; a paper drawn m times counts m
  times; report per nomination the fraction of resamples in the top K.
- `EDGE_PRECISION_V1` perturbation (when estimates exist): drop each leg independently with probability
  `1 − p̂(method, role, premise kind)`, where premise kind is the premise's agreed `ClaimReading` kind
  for a Claim (`UNKNOWN` if its readings disagree or it has none) or the Placeholder kind; report top-K survival.
- Top-K overlap across reading and edge-filter policies.

### 8.6 Algorithms (normative)

At about 324 k claims, 244 k junctions and 583 k legs (ESTIMATED by extrapolating the four-paper totals):
layers by the §4.1 procedure, O((V + J + L) log V); SCC listing by v0.3 `graph._tarjan`;
`dependent_papers` by paper-bitset union over the SCC condensation in reverse topological order (exact);
`dependents` exact for nominated subjects by one reverse traversal each; knockouts on each candidate's
descendant subgraph with an AND/OR support closure (the v0.3 `graph._supported` rule). No transitive
count is computed in Cypher.

## 9. Storage and Neo4j

### 9.1 Authority

The private artifact store (sources, receipts, deltas), the corpus ledger and the review set are the
authority. Neo4j is a pure function of one `DeltaSetManifest` plus one review set (I-12). Analysis
outputs are immutable artifacts keyed by (policy digest, manifest digest): `NodeMetrics` as JSON Lines,
nominations, bootstrap records.

### 9.2 What the projection holds

Labels: `Corpus`, `PaperVersion`, `Work`, `BibEntry`, `Claim`, `ClaimReading`, `Junction`, `Placeholder`
(plus `:ExternalRequest` or `:UnresolvedOccurrence`), `PrimitiveAssertion`, `ProjectionManifest`. Every
node also carries `:Entity`; logical nodes carry `:Logical`. Identifiers are scalar properties. The
`Corpus` node is derived from `DeltaSetManifest.corpus_id` when `INCLUDES` edges exist.

Not projected: occurrences, anchors and receipts (claims keep locators and the ids that point to them);
reviews, analysis runs and nominations (reviews act through derived dispositions; nominations stay
immutable artifacts; a top-K overlay is deferred); analysis-derived properties on logical or
bibliographic nodes; verbatim text of restricted papers (a reading stores `statement_sha256`, and
`display_text` only when the licence permits or the text is a flagged paraphrase). `disposition` ∈
{`UNREVIEWED`, `SOURCE_FROZEN_HUMAN_SIGNED`} is derived by the loader from the review set and excluded
from `content_sha256`; a `LEG` review's subject id is its `PREMISE_OF` relationship id. A review change
triggers a rebuild.

### 9.3 Edition, constraints, indexes

Target Neo4j 2026.x or 5.26 LTS, **Community Edition**: only uniqueness constraints (node and
relationship property uniqueness); existence, type and key constraints, `GRAPH TYPE` and incremental
import are Enterprise-only (CITED, Neo4j operations manual, 2026-09). `neo4j/schema.cypher` creates
`entity_id` uniqueness on `:Entity(id)`, per-label `id` uniqueness, per-type relationship `id`
uniqueness, and range indexes on `Work(doi)`, `Work(arxiv_base_id)`, `Work(openalex_id)`,
`PaperVersion(arxiv_base_id)`, `Claim(paper_version_id)`, `Junction(conclusion_id)`,
`Junction(derivation_id)`, `Placeholder(kind)`.

### 9.4 Load protocol (fixed parameterized templates only)

1. Apply `neo4j/schema.cypher`.
2. Refuse if the database holds a `ProjectionManifest` with a different id (re-running the same projection
   is idempotent). Client errors in steps 1–2 raise `LoadError` and write no manifest.
3. Set `ProjectionManifest.state = 'BUILDING'`.
4. Preflight read: `UNWIND $rows AS row MATCH (n:Entity {id: row.id}) WHERE n.content_sha256 <>
   row.content_sha256 RETURN row.id` — any row aborts before writing.
5. Node batches (`MERGE (n:<Label>:Entity {id: row.id}) ON CREATE SET n += row.props`), then relationship
   batches (`MATCH (a:Entity {id: row.start}) MATCH (b:Entity {id: row.end}) MERGE
   (a)-[r:<TYPE> {id: row.id}]->(b) ON CREATE SET r += row.props RETURN count(r)`); a returned count
   below the batch size aborts (a missed `MATCH` would otherwise drop rows silently).
6. Audits (`neo4j/audits.cypher`) must all return zero rows.
7. Set `READY` with audit counts. Any failure from step 3 on sets `FAILED` and raises `LoadError`.

The host sends auto-commit requests of ≤ 5,000 rows to the Query API (`POST /db/{db}/query/v2`, which
replaces the deprecated HTTP transactional API) as a single writer, with the manifest digest in
`txMetadata`; `CALL {} IN TRANSACTIONS` is not used. v0.4 always rebuilds from empty (recreate schema,
load); the loader refuses a database that holds a different projection. Incremental loading is deferred.
`neo4j-admin database import full` may accelerate a first load outside the contract. The v0.1 ban on subqueries and dynamic labels applies to model-facing read templates;
this loader's labels come from fixed templates.

### 9.5 Browsing and GDS

Browsing templates name relationship type and direction, start from an indexed id, bound depth to
1..8 and set a LIMIT; they never compute transitive counts. Graph Data Science (Community: all
algorithms, ≤ 4 cores) may run in `stream` or `stats` mode for exploration; its topological sort drops
nodes on or below a cycle, so it is never the reference.

## 10. Stage 3 hand-off

`host/export_v03.py` exports a nomination's backward closure as a v0.3 graph `{nodes, support_groups}`:
one group per effective junction, `relation` = the strongest leg role (PROOF > SCIENTIFIC_CLAIM >
DEFINITION > SCOPE > BRIDGING > UNCLASSIFIED→PROOF), with dropped `position` and `use_site` recorded in
`losses`. The dispositions are a required argument, so no closure is exported silently unsigned. Stage 3
reviews bind to the exported ids and map back through the export record. The v0.3
library audit, `proof_walk` and `certify` then apply unchanged. A formal proof counts as
`JUNCTION_SUFFICIENCY_FORMAL` only when its hypotheses are exactly the junction's premises; it is never
evidence that any single leg is necessary. The tower layer is assigned here, relative to a named library
commit; `L0_PRIMITIVE` only after a library audit and a human review.

## 11. Automatic gates and automatic judgement

No 1,000-paper model run is authorized by this design, and every item below is recorded in
`schema v0.1/PENDING_TESTS.md`. No stage waits for a person: each gate is a rule the corpus manifest freezes at
S0, before anything is measured (`CorpusManifest.gates`), applied by `host/gates.py` to recorded measurements, and
its output is a `GateDecision` — a decision about what runs next, never a statement about a claim (I-10).

### 11.1 P-1 (S5, no model)

S1–S4 on the frozen sample. `gates.p_minus_1` measures the eligible and undetermined fractions of the SAMPLE
round, the works each cited by at least `min_citing_papers` sample papers (bibliography citations, with in-proof
counts beside them), the share of (sample paper, cited work) pairs whose work is itself a sample paper, and the
summed deterministic yield. Decision: `NO_GO` if the eligible fraction is below `min_eligible_fraction` or the
undetermined fraction above `max_undetermined_fraction`; `GO` if at least `min_works` works meet the citing-paper
threshold; otherwise `GO_WITH_EXPANSION` — the sample shares too few cited works for claim-level analysis, so
EXPANSION or DISCOVERY rounds acquire the cited and related papers first (§6.3). The eligibility grid
(`eligibility.grid`) is reported with it.

### 11.2 AUTO_EVAL_V1 (P0, automatic judgement)

Human labels are replaced by a frozen panel of model judges whose error is measured with controls. The host
(`host/autoeval.py`) does everything except the judge calls:

1. **Plan.** `autoeval.freeze_plan` freezes the estimands, the per-stratum sample size and seed, the controls, the
   panel (≥ 2 judges per judge operation, differing in model or thinking mode, at least one whose model is not among
   the `producers` of that operation — the S6 extraction models for `leg.judge`, the S7 match models for
   `match.judge`) and the instruction digests. It refuses a plan that dooms every stratum in advance: `per_stratum`
   below the P0 `min_items`, or fewer than `min_decoys` = ⌊z²(fpr_inflation/0.5 − 1)⌋ + 1 decoys per rule (12 at
   α = 0.05 and fpr_inflation 2; with none judged positive the Wilson upper end is z²/(n + z²), and twice it must stay
   below 0.5). The plan is fixed before any judge call.
2. **Sample.** `draw_leg_sample` and `draw_match_sample` take the plan's DeltaSetManifest and refuse any other view.
   The leg sample covers every leg of a non-source junction whose method needs an estimate (not HUMAN or LIBRARY),
   stratified by (reading method, method_version, role, use site); the match sample every MODEL_MATCH source junction,
   stratified by method_version. Versions are never pooled. Both are `ReviewSample`s with `label_source = AUTO_PANEL`
   and inclusion probabilities.
3. **Blinded cards.** `leg_card` shows the conclusion, the candidate premise and the evidence — exactly the owned
   proofs its proof derivation names (one proof for an S3 anchor junction, all of them for an S6 junction; a
   derivation that names no owned proof set is refused), its statement for the statement derivation, else a window
   around it — and never the method, the reading, an id or whether the card is a control. `match_card` shows the
   citing claim, its citing passage, the bibliography entry and the upstream statements, taken from the upstream
   paper's frozen source and never from a model reading. A source junction is judged only by a match card.
4. **Controls.** Positive (`ANCHOR_IN_OWNED_PROOF_V1`): premises the conclusion's own proof references by `\ref`.
   Negative, `count_per_rule` decoys of every rule for each precision estimand, each card made once:
   - leg decoys replace the premise by one of the **same kind** — a bibliography entry for a cited work, a display
     equation for an equation, else a theorem-like or definition environment. `SAME_PAPER_NEAR_MISS_V1` takes it from
     a file the evidence lies in, beginning after the evidence's end there, never one that a label or citation inside
     the evidence or the conclusion references (any candidate target, resolved or not), that encloses such a target,
     that references the conclusion, or whose occurrence is a premise of the conclusion; a bibliography entry must be
     cited neither there nor by a request of the conclusion. `OTHER_PAPER_DECOY_V1` takes it from another supplied
     paper that neither cites nor is cited by the conclusion's paper, another primary category when possible;
   - match decoys replace the evidence: `SAME_PAPER_NEAR_MISS_V1` by the statement of the upstream paper that no
     source junction of the request uses with the largest token overlap with the citing claim (a hard negative),
     `OTHER_PAPER_DECOY_V1` by a statement of a supplied paper other than the citing and upstream papers and their
     citation neighbours. A decoy that does state the invoked result raises the measured false-positive rate, so that
     error is conservative.
5. **Judgements.** Each judge answers `USED` / `NOT_USED` / `CANNOT_TELL`; `USED` needs an exact quotation of the
   evidence of at least 12 characters, which the host binds (the repeated-quotation rule of §7.3, with at most 80
   characters of extension) or records as `EVIDENCE_UNBOUND`; a response off the schema is `RESPONSE_INVALID`. A
   card's question must be its judge's operation (LEG for `leg.judge`, MATCH for `match.judge`). Each answer is a
   `Judgement` bound to the card's digest and to the receipt of its call.
6. **Panel.** `UNANIMOUS_VALID_USED`: a card is panel-positive iff every judge gave a VALID USED; anything else is
   not positive; a card that is neither unanimous USED nor unanimous NOT_USED is counted as unresolved.
7. **Precision bound.** With panel-positive rate `p` on real legs and false-positive rate `f` on unused premises,
   `p = Se·q + f(1 − q) ≤ q + f(1 − q)`, so the precision `q ≥ (p − f)/(1 − f)` for any sensitivity `Se`. The
   false-positive rate is measured per decoy rule (`false_positive_by_rule`) and the rule with the largest Wilson
   upper end is used. The report takes the Wilson lower end of `p` and `fpr_inflation` times that upper end, each
   one-sided at `1 − α/2`, so the bound holds at `1 − α` (Bonferroni; the largest per-rule upper end covers the worst
   rule's true rate whenever that rule's own bound holds). `point` is the Rogan–Gladen estimate with the control
   sensitivity; it is optimistic because referenced premises are easier than average. A stratum is `NOT_ESTIMABLE`
   with fewer than `min_items` items, no judged decoy, an inflated false-positive bound ≥ 0.5 (also when a rule made
   no decoy), or an unresolved fraction above `max_unresolved_fraction`.
8. **Recall without gold proofs.** `ANCHOR_REFERENCED_V1` (deterministic): of the proof legs the deterministic tier
   found to environment premises, the share the extraction also proposed — recall on explicitly referenced
   premises only. `LOCAL_VS_WHOLE_RECALL` on papers run in both S6 modes, over the conclusions both modes examined (read
   or proposed a junction for, so a mode that read a claim and proposed nothing is counted as missing its legs): each
   mode's share of the panel-confirmed union of their legs (`UNION_OF_TWO_METHODS_V1`) and the Chapman
   capture–recapture estimate (`CAPTURE_RECAPTURE_CHAPMAN_V1`, which assumes independent misses and is optimistic when
   misses correlate). An `UNRESOLVED_OCCURRENCE` premise and the whole claim of the same occurrence count as one premise.
9. **Report.** An `EvaluationReport` (`label_source = AUTO_PANEL`) with the independence of the judges from the
   producers per judge operation, its `inputs` (the precision samples, digests of every card and judgement, and per
   estimand the control composition: positive controls, decoys per rule, base items skipped for want of a decoy),
   every estimate, and its assumptions. A human audit (agreement of the panel with human labels on a sample,
   `autoeval.human_audit`) is optional and, when present, is reported beside the panel, never instead of it.

Leakage: model `training_cutoff` versus paper dates is recorded; precision can be stratified by it, but the v0.4
panel is not (a judge that saw a paper in training may recognise its proofs; open, §15). The theory-level paper's
benchmark criteria apply to Stage 3; v0.4 itself is not a benchmark.

### 11.3 P0 gate

`gates.p0` reads the plan, its report, the report's precision samples and a `CostProjection` of the manifest's S6
policy (§1.1). It first refuses inputs that are not what they claim: a plan, report or projection whose id is not the
digest of its content, of another corpus or plan, or a report whose rows do not cover every stratum of its samples
exactly once with the right item counts. It then recomputes every precision row under the manifest's P0 rule
(`autoeval.recheck`: every Rate from its counts at the rule's z, the worst decoy rule, the bound and the decision)
and refuses a row that does not recompute, so a stored decision is never trusted. `GO` iff:

- MODEL_EXTRACTION strata of the corpus extraction `method_version` exist and every one is `ADMIT` (lower bound ≥
  `admission_threshold`); strata of another version (a comparison arm of the pilot) admit nothing and block nothing;
- the projection is of the corpus extraction, of a model whose extraction the plan judged, against the manifest's
  ceiling and pricing profile, over at least `target_size` papers of MEASURED size, with no ESTIMATED parameter
  (the pilot's measurements replace them), under the ceiling after the reserves, and inside the context window;
- a judge model is independent of the producers.

`admitted_methods` are the methods whose every counted stratum is admitted, plus the non-model methods HUMAN and
LIBRARY; a MODEL_MATCH that is not admitted keeps S7 legs out of importance counts and is reported as a reason.
`gates.primary_policy` then derives the PRIMARY analysis policy (§8.1) from an unedited P0 GO under the manifest's P0
rule. Throughput measured in the pilot — calls per paper, prompt tokens per call, cached-token share, reasoning
tokens, validation rate, achieved parallelism — replaces the ESTIMATED parameters of §1.1 before the full run; a quota
shared with the user's interactive use would be consumed by the run.

**Open:** `match_coverage` needs S7 attempt records from the ledger and is null until those exist. The Cypher
files are checked statically only; no Neo4j server has parsed or run them.

## 12. Deferred to v0.4.1: cross-paper statement clusters

The same result is restated across papers. Clustering depends on the P-1 cross-paper density and a
false merge creates a hub that inflates the headline metric, so it is deferred. Fixed now as entry
conditions: a cluster records an assessed relation (`SAME_STATEMENT`, `SPECIALIZES`, `GENERALIZES`,
`CONCEPT_SAME_DEFINITION`; schema v0.0 `relation-assessment`), never a string or embedding merge, never
renaming a claim; every judgement records an `equivalence_threshold` ∈ {`NOTATION_AND_RENAMING`,
`STANDARD_ALGEBRAIC_IDENTITIES`, `PARAMETER_SPECIALIZATION_ALLOWED`, `FORMAL_FRAGMENT:<name>`} (the
theory-level paper: equivalence depends on how much computation the judge allows); quotient analysis
separates reviewed from candidate clusters, takes the OR-union of member junctions, drops
self-concluding junctions as `SELF_SUPPORT_VIA_RESTATEMENT`; candidate pairs are compared against a
star centre with a frozen cap per block (`TRUNCATED_BY_CAP`).

## 13. What v0.4 does not establish

A corpus graph does not establish that any claim is correct; that any extraction is complete; that a root
is a historical origin; that two restatements are the same theorem; that a nominated claim is
formalizable; that a rank reflects importance rather than extraction coverage and method precision; that
an absent subject is unimportant; that results hold beyond the eligible population P; that a pooled
work's rank identifies which of its results is used; that a date is a result's origin; that definitional
dependencies were captured at the recall of theorem citations; that a citation inside a proof is a
logical premise; that a model premise came from the supplied context rather than from memory; that
bootstrap stability implies correctness; that an automatic judgement is right about any single leg (a panel
estimate is a rate with stated assumptions); or, until measured (§11), match coverage, the cost parameters of §1.1,
or that its Cypher runs on Neo4j.

## 14. Contract objects (`schema v0.4/schemas/corpus.schema.json`)

Reused from v0.3 by `$ref`: `SourceSpan`, `Confidence`, `ProgramReceipt` (also used as the load
receipt), `Issue`, `ContentArtifactReference`, `TerminalRecord` (terminal kinds). v0.3 `ModelReceipt`
has no schema (code-only) and is referenced by artifact.

New: `DateValue`, `ExternalIdentifierV4` (adds `openalex_id`, `OPENALEX_CANDIDATE`,
`HOST_RULE_ARXIV_DOI`), `ModelSelectionV4`, `CorpusManifest`, `SamplingRecord`, `PaperVersionNode`,
`WorkNode`, `BibEntryNode`, `ClaimNode`, `ClaimReadingNode`, `JunctionNode` (with ordered `legs`),
`PlaceholderNode`, `PrimitiveAssertionNode`, `Edge`, `GraphDelta`, `DeltaSetManifest`,
`ProjectionManifest`, `AnalysisPolicy`, `NodeMetrics`, `FoundationNomination`, `ReviewSample`,
`HumanReviewV4` (the v0.3 shape with subject kinds `JUNCTION`, `LEG`, `WORK_IDENTITY`,
`PRIMITIVE_ASSERTION`, `FOUNDATION_NOMINATION` added). Revision 3 adds `Admission`, `CountBasis`, `Rate`,
`TokenPrices`, `EvaluationPlan`, `Judgement`, `PrecisionEstimate`, `RecallEstimate`, `EvaluationReport`,
`GateDecision`, `PricingProfile` and `CostProjection` (with wrapper files for the six top-level records), and removes
`CoverageLabel`, the audit arm and `missed_nomination_rate`. The review corrections add `Stratum` (method,
method_version and, for a leg, role and use site), `PrecisionEstimate.false_positive_by_rule`,
`EvaluationPlan.producers` (replacing `extraction_models`) and `controls.negative.count_per_rule`,
`EvaluationReport.inputs`, a required `Judgement.receipt`, `CostProjection.paper_plans`, `wallclock_basis` and the
ceiling's reserves, the POLICY parameter label, `PricingProfile` `batch_completion_minutes`, and the DISCOVERY counts
`duplicates` and `not_selected`. The corpus ledger's work items are SQLite rows,
not JSON contracts. Row shapes: Appendix A.

## 15. Decisions still open for the user

1. **Field, window and eligibility parameters** of the first corpus (e.g. `quant-ph` or `math-ph`, 2015–2025;
   `min_theorem_like`, `min_display_equations`), best fixed after the P-1 eligibility grid.
2. **Network sources** (arXiv OAI-PMH and e-prints, Crossref, OpenAlex snapshot, Semantic Scholar) —
   each needs explicit authorization; Semantic Scholar's licence restricts redistribution.
3. **Model access and money**: whether to open a metered MiMo account (candidate profile
   `profiles/engines-v2-mimo.json`), the budget ceiling (the §1.1 projection suggests about $1,000 with the Batch
   API and the prefix cache, $2,500 without relying on it), and a check of the provider's terms for sending paper
   full text (I-13).
4. **Neo4j edition** (Community assumed).
5. **Judge training cutoffs**: whether to stratify AUTO_EVAL_V1 by judge training cutoff versus paper date, which
   needs dated cutoffs the provider pages do not state (both MiMo profiles record `UNKNOWN`).

Resolved in Revision 3: who labels P0 (nobody by default: AUTO_EVAL_V1, with an optional human audit), coverage
(EQUAL_FULL), eligibility of derivation papers, admission of cited and discovered papers.

---

## Appendix A. Row shapes

All rows carry `id` and `content_sha256` (§5.2). Dates are `DateValue`. `?` marks optional fields.

- **Corpus** `{id = DeltaSetManifest.corpus_id, asserted_by = union of the INCLUDES edges' deltas}`,
  derived by the projection, present only when `INCLUDES` edges exist.
- **PaperVersion** `{id, arxiv_base_id, version, title?, primary_category, categories[], license?,
  redistribution ∈ OPEN|RESTRICTED|UNKNOWN, date_v1, date_version, source_sha256, parser_sha256}`,
  asserted only by S1.
- **Work** `{id, identity_basis ∈ ARXIV_BASE|DOI|OPENALEX|BIB_DIGEST, arxiv_base_id?, doi?, openalex_id?,
  bib_digest? (required for BIB_DIGEST), title?, year?, work_kind ∈ ARTICLE|BOOK|THESIS|PROCEEDINGS|
  UNKNOWN, terminal_kind}`
- **BibEntry** `{id, paper_version_id, citation_key, locator (SourceSpan), identifiers
  (ExternalIdentifierV4), title?, year?, entry_type?, v03_id?}`
- **Claim** `{id, origin ∈ PAPER_VERSION|WORK_LOCATOR, paper_version_id?, work_id?, occurrence_ids[],
  part, locator (SourceSpan)?, work_locator_text?, occurrence_kind?}`
- **ClaimReading** `{id, claim_id, method, method_version, kind ∈ definition|theorem|lemma|proposition|
  corollary|equation|claim|remark|UNKNOWN, statement_sha256, conditions_sha256, display_text?,
  display_text_class ∈ VERBATIM|PARAPHRASE|NONE, confidence?}`
- **Junction** `{id, conclusion_id, derivation_id, reading_method, method_version, legs[{premise_id,
  role, use_site, flags[]}], grouping_basis, citation_groups[]?}`
- **Placeholder** `{id, kind ∈ EXTERNAL_REQUEST|UNRESOLVED_OCCURRENCE, paper_version_id,
  created_by_claim_id, citing_derivation_id, bib_entry_id?, citation_group?, locator_text?,
  occurrence_id?, reason?}`
- **PrimitiveAssertion** `{id, claim_id, method, basis ∈ AXIOM|ASSUMPTION|STANDARD_NOTION|HUMAN}`
- **Edge** `{id, type, start_id, end_id, props{}}` for every non-logical type of §3.6, plus the derived
  `PREMISE_OF` and `CONCLUDES` rows the projection generates from junctions.
- **GraphDelta** `{kind: GraphDelta, contract_version: 0.4.0, delta_id, stage ∈ S1…S9|HUMAN_ENTRY|
  LIBRARY_AUDIT, method, method_version, subject{kind, id}, parents[],
  produced_by[ContentArtifactReference], nodes{Label: [rows]}, edges[], issues[], measurements{}?}`
- **DeltaSetManifest** `{kind, manifest_id, corpus_id, parent_manifest_id?, deltas[], excluded[{delta_id,
  reason}], created_at}`
- **ProjectionManifest** `{id, delta_set_digest, review_set_digest, state, loader_version,
  audit_counts{}}`
