# Perfect-Graph Claim Lineage Demo

**Document type:** implementation roadmap and source-alignment boundary

**Demo:** [`perfect-graph-lineage.html`](../../Stabilizerness/MathContractRegistry/demo/perfect-graph-lineage.html)

**System specification:** [`AgtXIv.md`](../../AgtXIv.md)

**Mathematics pipeline:** [`mathematics-pipeline.md`](../specifications/mathematics-pipeline.md)

This roadmap defines one source-bounded visualization case. It is not a claim that the displayed candidate contracts are accepted, formally aligned, or Lean-checked.

## 1. Mathematical relations

The case keeps four relations separate.

1. **Paper citation.** *Graph-Theoretic Nonstabilizerness* cites arXiv:2511.13531 in `draft.tex:928-930`. This is a semantic literature relation, not by itself a theorem dependency.
2. **Direct claim import.** Xu et al. state and prove that every perfect graph is $\hbar$-perfect (`main.tex:394-400`; `appendix.tex:177-197`). The target paper imports that result in its squared-Pauli-profile branch (`draft.tex:923-930`) to conclude that a perfect frustration graph cannot provide a strict $\beta-\alpha$ quadratic witness.
3. **Rejected shortcut.** The Xu theorem does not support the target paper's perfect-graph collapse, antiblocker identity, or closed-form reduced-RoM branch (`draft.tex:634-684`). The proposed edge is retained only as a rejected relation with verdict `WRONG_RELATION_TYPE`.
4. **Shared foundation.** Chvátal 1975 supports the perfect/$h$-perfect stable-set-polytope characterization used by Xu et al. It also appears in the target paper's weighted stable-set/fractional clique-cover chain. The target branch additionally cites distinct Lovász, Fulkerson, and Grötschel–Lovász–Schrijver results; Chvátal 1975 is not represented as its sole source.

The intended conclusion is:

> Citation tells us which paper points to which paper. Math Claim provenance tells us which theorem supports which conclusion, and reveals when apparently linear scholarship actually branches from a shared mathematical root.

## 2. Page nodes and edges

### 2.1 Paper and corpus Agents

- `paper:xu-2511.13531`: arXiv:2511.13531v1.
- `paper:gtn-2607.26154`: target-paper Agent.
- `corpus:classical-perfect-graph`: visual membership container for the classical graph-theory sources; it is not a synthetic theorem or accepted Root Agent.

### 2.2 Claim nodes

- Xu perfect $\Rightarrow h$-perfect $\Rightarrow \hbar$-perfect.
- Target weighted quadratic stabilizer benchmark.
- Target no-strict-$\beta-\alpha$-witness conclusion.
- Chvátal 1975 stable-set-polytope characterization.
- Lovász 1972 weighted perfect-graph duality foundations.
- Lovász 1979 weighted theta sandwich.
- Fulkerson 1971/1972 antiblocker foundation.
- Grötschel–Lovász–Schrijver 1981 optimization and perfect-graph construction.
- Target perfect-graph collapse.
- Target antiblocker identity.
- Target closed-form reduced RoM.

### 2.3 Typed edges

- `paper_cites`: target paper to Xu et al.; semantic literature relation.
- `theorem_import`: Xu theorem to the target quadratic-witness conclusion; source-supported direct import, still alignment-pending in the Registry.
- `local_derivation`: target squared-profile benchmark to the target quadratic-witness conclusion.
- `rejected_shortcut`: Xu theorem to target perfect-graph collapse; terminal status `REJECTED`, verdict `WRONG_RELATION_TYPE`.
- `shared_foundation`: classical sources to the two distinct claim branches.
- `derives`: target perfect collapse to its antiblocker identity and then to the closed-form reduced-RoM result.
- `membership`: visual containment only; never interpreted as a mathematical dependency.

All dependency arrows point from prerequisite to dependent conclusion. `paper_cites` retains citation direction and is labeled separately so it cannot be mistaken for a prerequisite edge.

## 3. File-change boundary

Create:

- `Stabilizerness/MathContractRegistry/demo/perfect-graph-lineage.html`
- `Stabilizerness/MathContractRegistry/demo/perfect-graph-lineage.js`
- `Stabilizerness/MathContractRegistry/demo/perfect-graph-lineage.css`
- this roadmap

Edit only to add navigation links:

- `Stabilizerness/MathContractRegistry/demo/index.html`
- `Stabilizerness/MathContractRegistry/demo/pauli-active.html`

The page keeps its source-bounded data model in the JavaScript file so direct `file://` loading does not depend on `fetch()` or browser-specific local-file CORS behavior.

## 4. Acceptance conditions

- Direct `file://` opening renders the complete page without a server.
- Four step tabs and Previous/Next controls update the fixed DAG.
- Pointer hover and keyboard focus expose details.
- Enter, Space, or click pins a node card; Close and Escape dismiss it.
- Every important node records status, imports, scope warning, exact local source lines, and source links.
- arXiv and DOI links use stable public URLs.
- Direct import, candidate/shared-foundation, and rejected relations have distinct line color/pattern and node status treatment.
- Candidate and source-alignment-pending objects are never labeled accepted.
- The page links back to the Registry DAG and to the Pauli-active audit; both existing pages link into this case.
- The fixed graph remains horizontally scrollable on narrow screens, while controls and details reflow without obscuring the graph.
- JavaScript syntax, internal relative links, console output, and desktop/mobile interaction checks pass.

## 5. Primary-source alignment still pending

This demo verifies the quoted Xu theorem and the target paper's two local branches against their frozen LaTeX line ranges. It does **not** complete claim-level primary-source alignment for the classical literature. In particular, the following remain open Registry work:

- identify exact theorem or proposition numbers and original-page spans in Chvátal 1975 for each use;
- separate the two Lovász 1972 citations by the precise weighted-duality statement imported by the target proof;
- align the weighted form of the Lovász sandwich with the cited original and later exposition;
- identify the exact Fulkerson 1971/1972 antiblocker statement used by `draft.tex:683`;
- verify the optimization-separation and perfect-graph algorithm spans cited from Grötschel–Lovász–Schrijver 1981;
- replace the Registry's coarse `root:xu-quadratic-pauli-graph` only after source-aligned atomic records and relation evidence exist;
- perform formal-statement and Lean alignment for both branches.

Until those tasks are complete, the corresponding nodes remain `PRIMARY_SOURCE_ALIGNMENT_PENDING`, and the direct Xu import remains source-grounded rather than accepted.
