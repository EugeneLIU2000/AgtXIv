const stepProfiles = [
  {
    title: "Paper citation is not theorem dependency",
    summary: "The target paper cites Xu et al. This paper-level relation identifies where to investigate, but it does not say which theorem supports which conclusion.",
    badge: "PAPER_CITES",
    badgeClass: "citation",
    note: "Semantic literature relation only. Do not infer a theorem edge from citation alone.",
    relation: "paper_cites",
    evidence: "citation context",
    promotion: "none",
    verdict: "semantic only",
    alignment: "citation verified",
    explanationTitle: "A citation starts dependency archaeology",
    explanationBody: "At paper level, scholarship looks linear: the target cites Xu et al. Claim-level inspection is needed before that line can become a typed mathematical dependency.",
    activeNodes: ["xuPaper", "gtnPaper"],
    activeEdges: ["gtn-cites-xu"]
  },
  {
    title: "The cited theorem supports one target branch",
    summary: "Xu et al.'s perfect-to-hbar-perfect theorem is imported in the squared Pauli-profile branch, where it rules out a strict beta-alpha quadratic witness on perfect graphs.",
    badge: "THEOREM_IMPORT",
    badgeClass: "import",
    note: "The source spans support this direct import, but Registry source-to-contract and formal alignment remain pending.",
    relation: "theorem_import",
    evidence: "source-grounded",
    promotion: "not accepted",
    verdict: "direct import",
    alignment: "pending",
    explanationTitle: "Claim-level provenance identifies the load-bearing theorem",
    explanationBody: "The imported result is narrow and precise: perfect graphs are hbar-perfect, so beta(G,w)=alpha(G,w) for every nonnegative weight and no strict quadratic witness exists on that branch.",
    activeNodes: ["xuPaper", "gtnPaper", "xuPerfectHbar", "gtnQuadraticBenchmark", "gtnNoQuadraticWitness"],
    activeEdges: ["xu-membership", "gtn-quadratic-membership", "gtn-witness-membership", "xu-imports-witness", "benchmark-supports-witness"]
  },
  {
    title: "A plausible shortcut has the wrong relation type",
    summary: "The Xu theorem does not establish the target paper's weighted perfect-graph collapse, antiblocker identity, or closed-form reduced robustness of magic.",
    badge: "REJECTED / WRONG_RELATION_TYPE",
    badgeClass: "rejected",
    note: "The rejected edge remains visible as audit evidence; it is never inserted into the mathematical build DAG.",
    relation: "rejected_shortcut",
    evidence: "relation audit",
    promotion: "prohibited",
    verdict: "WRONG_RELATION_TYPE",
    alignment: "rejected",
    explanationTitle: "Citation proximity cannot bridge two distinct perfect-graph branches",
    explanationBody: "The squared-profile result concerns beta versus weighted independence. The closed-form RoM branch instead uses weighted stable-set/fractional clique-cover duality, a theta sandwich, an antiblocker identity, and a separate no-active-dependency premise.",
    activeNodes: ["xuPerfectHbar", "gtnPerfectCollapse", "gtnAntiblocker", "gtnClosedFormRom"],
    activeEdges: ["wrong-shortcut", "collapse-antiblocker", "antiblocker-rom"]
  },
  {
    title: "The claim graph branches from shared foundations",
    summary: "Chvátal supports both lineages, while the target collapse branch additionally depends on distinct Lovász, Fulkerson, and Grötschel-Lovász-Schrijver foundations.",
    badge: "SHARED FOUNDATION / ALIGNMENT PENDING",
    badgeClass: "foundation",
    note: "Shared roots explain the resemblance without turning one downstream theorem into the source of the other branch.",
    relation: "shared_foundation",
    evidence: "local citation chains",
    promotion: "none",
    verdict: "branched lineage",
    alignment: "primary sources pending",
    explanationTitle: "Apparently linear scholarship becomes a branched mathematical lineage",
    explanationBody: "Chvátal 1975 participates in both chains, but it is not the target collapse's unique source. The claim graph preserves the separate Lovász, Fulkerson, and GLS contributions and the target paper's local derivation.",
    activeNodes: ["xuPaper", "gtnPaper", "classicCorpus", "xuPerfectHbar", "gtnPerfectCollapse", "gtnAntiblocker", "gtnClosedFormRom", "chvatal", "lovasz72", "lovasz79", "fulkerson", "gls"],
    activeEdges: ["xu-membership", "gtn-collapse-membership", "gtn-antiblocker-membership", "gtn-rom-membership", "classic-chvatal-membership", "classic-lovasz72-membership", "classic-lovasz79-membership", "classic-fulkerson-membership", "classic-gls-membership", "chvatal-xu", "chvatal-collapse", "lovasz72-collapse", "lovasz79-collapse", "fulkerson-antiblocker", "gls-collapse", "collapse-antiblocker", "antiblocker-rom"]
  }
];

const nodeCatalog = {
  xuPaper: {
    type: "agent", owner: "XU", x: 175, y: 145, code: "A-XU",
    title: "Xu et al. paper Agent",
    identifier: "arXiv:2511.13531v1",
    status: "SOURCE_IDENTIFIED / AGENT_STANDARDIZATION_PENDING",
    statement: "Simultaneous variances of Pauli strings, weighted independence numbers, and a new kind of perfection of graphs.",
    imports: ["Chvátal 1975 stable-set-polytope characterization", "Xu et al. 2023 odd-cycle beta result"],
    scope: "The local source is frozen and inspected. This page does not promote the existing coarse Registry root to an accepted Paper Agent or MathContract.",
    sources: [
      { label: "arXiv abstract and version record", anchor: "arXiv:2511.13531v1, 2025-11-17", href: "https://arxiv.org/abs/2511.13531" },
      { label: "Frozen LaTeX theorem", anchor: "main.tex:394-400", href: "../../../References/2511.13531/main.tex" },
      { label: "Frozen LaTeX proof", anchor: "appendix.tex:177-197", href: "../../../References/2511.13531/appendix.tex" }
    ]
  },
  gtnPaper: {
    type: "agent", owner: "GTN", x: 1145, y: 145, code: "A-GTN",
    title: "Graph-Theoretic Nonstabilizerness Agent",
    identifier: "target manuscript / arXiv-2607.26154v1 source package",
    status: "MAPPED TARGET AGENT / PARTIAL REGISTRY",
    statement: "Target paper containing distinct squared-profile and perfect-collapse branches.",
    imports: ["Xu et al. in the squared-profile branch", "Classical perfect-graph foundations in the closed-form RoM branch"],
    scope: "Agent membership records paper ownership. It does not make every citation a theorem dependency or every local claim accepted.",
    sources: [
      { label: "Target arXiv record", anchor: "arXiv:2607.26154v1", href: "https://arxiv.org/abs/2607.26154" },
      { label: "Target manuscript: perfect-collapse branch", anchor: "draft.tex:634-684", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Target manuscript: squared-profile branch", anchor: "draft.tex:912-933", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  },
  classicCorpus: {
    type: "agent", owner: "PGF", x: 175, y: 650, code: "PGF",
    title: "Classical perfect-graph foundations",
    identifier: "visual source corpus, not a virtual Root Agent",
    status: "PRIMARY_SOURCE_ALIGNMENT_PENDING",
    statement: "A visual membership container for the classical works cited by the two branches.",
    imports: [],
    scope: "This circle groups sources for readability. It is not a mathematical claim, a synthetic theorem, or an accepted Registry Agent.",
    sources: [
      { label: "Target local citation chain", anchor: "draft.tex:649-684", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Xu local citation chain", anchor: "main.tex:385-400; appendix.tex:177-197", href: "../../../References/2511.13531/main.tex" }
    ]
  },
  xuPerfectHbar: {
    type: "claim", owner: "XU", x: 450, y: 295,
    title: "Perfect graph implies hbar-perfect",
    status: "SOURCE_GROUNDED_ALIGNMENT_PENDING",
    statement: "For every perfect graph G and every nonnegative weight w, beta(G,w)=alpha(G,w); equivalently, every perfect graph is hbar-perfect.",
    imports: ["perfect G -> h-perfect G", "h-perfect G -> hbar-perfect G", "Chvátal 1975 facet characterization"],
    scope: "The theorem and proof are source-grounded. Atomic Registry replacement of root:xu-quadratic-pauli-graph, formal alignment, and Lean support have not been completed.",
    sources: [
      { label: "Theorem thm:perfect", anchor: "main.tex:394-400", href: "../../../References/2511.13531/main.tex" },
      { label: "Proof thm:perfect2", anchor: "appendix.tex:177-197", href: "../../../References/2511.13531/appendix.tex" },
      { label: "arXiv source record", anchor: "arXiv:2511.13531v1", href: "https://arxiv.org/abs/2511.13531" }
    ]
  },
  gtnQuadraticBenchmark: {
    type: "claim", owner: "GTN", x: 720, y: 275,
    title: "Weighted quadratic stabilizer benchmark",
    status: "LOCAL_SOURCE_GROUNDED",
    statement: "For nonnegative w, the stabilizer maximum of the weighted squared Pauli profile equals alpha_w(G_M).",
    imports: ["squared stabilizer support is an independent set", "frustration-graph definition"],
    scope: "This local claim supplies the stabilizer side of the comparison. It does not use the target paper's closed-form reduced-RoM branch.",
    sources: [
      { label: "Target derivation", anchor: "draft.tex:912-921", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Current Registry node", anchor: "claim:quadratic-stabilizer-mwis", href: "../contracts/contracts.json" }
    ]
  },
  gtnNoQuadraticWitness: {
    type: "claim", owner: "GTN", x: 1010, y: 300,
    title: "No strict quadratic witness on perfect graphs",
    status: "SOURCE_GROUNDED_ALIGNMENT_PENDING",
    statement: "If G_M is perfect, then it is hbar-perfect and beta(G_M,w)=alpha_w(G_M) for every nonnegative w; therefore no strict beta-alpha witness exists in this quadratic family.",
    imports: ["Xu perfect -> hbar-perfect theorem", "target weighted quadratic stabilizer benchmark"],
    scope: "This is the direct cross-paper theorem import. The Registry currently labels the corresponding extension source unchecked, so the page does not call it accepted.",
    sources: [
      { label: "Target import and conclusion", anchor: "draft.tex:923-930", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Current Registry node", anchor: "claim:hbar-perfect-quadratic-witness", href: "../contracts/contracts.json" },
      { label: "Imported theorem", anchor: "main.tex:394-400", href: "../../../References/2511.13531/main.tex" }
    ]
  },
  gtnPerfectCollapse: {
    type: "claim", owner: "GTN", x: 765, y: 455,
    title: "Target perfect-graph collapse",
    status: "SOURCE_GROUNDED_ALIGNMENT_PENDING",
    statement: "For perfect G and every nonnegative w, alpha_w(G)=theta(G,w)=fractional-clique-cover_w(G).",
    imports: ["Lovász weighted theta sandwich", "weighted stable-set/fractional clique-cover duality", "Chvátal and Lovász perfect-graph foundations", "GLS perfect-graph optimization results"],
    scope: "This target-local lemma does not import Xu's perfect-to-hbar-perfect theorem. Classical primary-source theorem alignment remains incomplete.",
    sources: [
      { label: "Lemma and proof", anchor: "draft.tex:634-684", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Perfect-collapse statement", anchor: "draft.tex:664-678", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  },
  gtnAntiblocker: {
    type: "claim", owner: "GTN", x: 1000, y: 455,
    title: "Target perfect-graph antiblocker identity",
    status: "LOCAL_DERIVATION_BLOCKED",
    statement: "For perfect G, {z>=0: alpha_z(G)<=1} is the convex hull of clique incidence vectors, including the empty clique.",
    imports: ["target perfect-graph collapse", "Fulkerson antiblocker foundation", "downward closure"],
    scope: "The target derives this locally, but the current Registry records a weighted-duality alignment blocker and no Lean mapping.",
    sources: [
      { label: "Statement and local proof", anchor: "draft.tex:671-684", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Current Registry node", anchor: "claim:perfect-graph-antiblocker", href: "../contracts/contracts.json" }
    ]
  },
  gtnClosedFormRom: {
    type: "claim", owner: "GTN", x: 1190, y: 500,
    title: "Closed-form reduced RoM",
    status: "LOCAL_DERIVATION_BLOCKED",
    statement: "If the Pauli window has no active dependency and G_M is perfect, reduced RoM equals the maximum clique l1 expression stated in the target theorem.",
    imports: ["exact graph program", "perfect-graph antiblocker identity", "perfect-graph scope", "no-Pauli-active-dependency scope"],
    scope: "The displayed lineage shows only the perfect-graph subbranch. The no-active-dependency and exact-graph-program prerequisites remain essential and are not supplied by Xu et al.",
    sources: [
      { label: "Target theorem and proof", anchor: "draft.tex:687-723", href: "../../arXiv-2607.26154v1/draft.tex" },
      { label: "Current Registry node", anchor: "claim:closed-form-rom", href: "../contracts/contracts.json" }
    ]
  },
  chvatal: {
    type: "claim", owner: "PGF", x: 410, y: 625,
    title: "Chvátal 1975 stable-set-polytope foundation",
    status: "PRIMARY_SOURCE_ALIGNMENT_PENDING",
    statement: "The cited work supplies stable-set-polytope characterizations used in the perfect/h-perfect and weighted perfect-graph source chains.",
    imports: [],
    scope: "Shared foundation does not mean unique foundation. Exact original theorem/page alignment for each downstream use remains pending.",
    sources: [
      { label: "Primary publication DOI", anchor: "JCTB 18(2), 138-154 (1975)", href: "https://doi.org/10.1016/0095-8956(75)90041-6" },
      { label: "Use in Xu et al.", anchor: "main.tex:385-400; appendix.tex:185-197", href: "../../../References/2511.13531/main.tex" },
      { label: "Use in target collapse", anchor: "draft.tex:681", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  },
  lovasz72: {
    type: "claim", owner: "PGF", x: 575, y: 650,
    title: "Lovász 1972 perfect-graph duality foundations",
    status: "PRIMARY_SOURCE_ALIGNMENT_PENDING",
    statement: "The target cites the 1972 perfect-graph results in its weighted stable-set/fractional clique-cover equality chain.",
    imports: [],
    scope: "The exact weighted statement and the separate role of each 1972 paper still require primary-source claim alignment.",
    sources: [
      { label: "Normal hypergraphs and the perfect graph conjecture", anchor: "Discrete Mathematics 2 (1972)", href: "https://doi.org/10.1016/0012-365X(72)90006-4" },
      { label: "A characterization of perfect graphs", anchor: "JCTB 13 (1972)", href: "https://doi.org/10.1016/0095-8956(72)90045-7" },
      { label: "Target citation context", anchor: "draft.tex:681", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  },
  lovasz79: {
    type: "claim", owner: "PGF", x: 735, y: 625,
    title: "Lovász 1979 theta-sandwich foundation",
    status: "PRIMARY_SOURCE_ALIGNMENT_PENDING",
    statement: "The weighted theta number is placed between weighted independence and fractional clique cover in the target argument.",
    imports: [],
    scope: "The target cites both the original work and a later exposition. Alignment of the precise weighted formulation remains pending.",
    sources: [
      { label: "Primary publication DOI", anchor: "IEEE TIT 25(1), 1-7 (1979)", href: "https://doi.org/10.1109/TIT.1979.1055985" },
      { label: "Target lemma", anchor: "draft.tex:649-662", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  },
  fulkerson: {
    type: "claim", owner: "PGF", x: 895, y: 650,
    title: "Fulkerson antiblocker foundations",
    status: "PRIMARY_SOURCE_ALIGNMENT_PENDING",
    statement: "The target identifies its convex-hull equality as the perfect-graph antiblocker identity of Fulkerson.",
    imports: [],
    scope: "The exact statement split between the 1971 and 1972 papers and its mapping to the target notation remain pending.",
    sources: [
      { label: "Blocking and anti-blocking pairs of polyhedra", anchor: "Mathematical Programming 1 (1971)", href: "https://doi.org/10.1007/BF01584085" },
      { label: "Anti-blocking polyhedra", anchor: "JCTB 12(1) (1972)", href: "https://doi.org/10.1016/0095-8956(72)90032-9" },
      { label: "Target citation context", anchor: "draft.tex:683", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  },
  gls: {
    type: "claim", owner: "PGF", x: 1055, y: 625,
    title: "GLS 1981 optimization foundation",
    status: "PRIMARY_SOURCE_ALIGNMENT_PENDING",
    statement: "The target uses optimization-separation equivalence and the perfect-graph construction for polynomial-time weighted optimization.",
    imports: [],
    scope: "The target gives section and page pointers, but claim-level primary-source alignment and formal binding remain pending.",
    sources: [
      { label: "Primary publication DOI", anchor: "Combinatorica 1, 169-197 (1981)", href: "https://doi.org/10.1007/BF02579273" },
      { label: "Target source pointer", anchor: "draft.tex:664-684; GLS Theorem 3.1 and Sec. 6, pp. 192-194", href: "../../arXiv-2607.26154v1/draft.tex" }
    ]
  }
};

const edgeCatalog = [
  { id: "gtn-cites-xu", from: "gtnPaper", to: "xuPaper", type: "paper_cites", step: 1, status: "CITATION_VERIFIED", label: "paper_cites", reason: "The target cites xu2025simultaneous in its squared-profile discussion.", scope: "Semantic literature relation only; not a theorem dependency.", source: "draft.tex:928-930" },
  { id: "xu-membership", from: "xuPaper", to: "xuPerfectHbar", type: "membership", step: 2, status: "MEMBERSHIP_ONLY", label: "contains claim", reason: "The theorem is stated and proved in the Xu et al. source package.", scope: "Paper ownership is not a mathematical dependency.", source: "main.tex:394-400; appendix.tex:177-197" },
  { id: "gtn-quadratic-membership", from: "gtnPaper", to: "gtnQuadraticBenchmark", type: "membership", step: 2, status: "MEMBERSHIP_ONLY", label: "contains local claim", reason: "The weighted stabilizer benchmark is derived in the target paper.", scope: "Paper ownership is not a mathematical dependency.", source: "draft.tex:912-921" },
  { id: "gtn-witness-membership", from: "gtnPaper", to: "gtnNoQuadraticWitness", type: "membership", step: 2, status: "MEMBERSHIP_ONLY", label: "contains imported conclusion", reason: "The target paper states the no-witness consequence.", scope: "Paper ownership is not a mathematical dependency.", source: "draft.tex:923-930" },
  { id: "xu-imports-witness", from: "xuPerfectHbar", to: "gtnNoQuadraticWitness", type: "theorem_import", step: 2, status: "SOURCE_GROUNDED / ALIGNMENT_PENDING", label: "theorem_import", reason: "Perfect implies hbar-perfect, hence beta equals alpha for every nonnegative weight and the strict witness is unavailable.", scope: "Direct cross-paper import; not yet an accepted Registry edge or Lean-supported relation.", source: "main.tex:394-400; appendix.tex:177-197 -> draft.tex:923-930" },
  { id: "benchmark-supports-witness", from: "gtnQuadraticBenchmark", to: "gtnNoQuadraticWitness", type: "local_derivation", step: 2, status: "LOCAL_SOURCE_GROUNDED", label: "supplies stabilizer benchmark", reason: "The target's alpha_w benchmark identifies the stabilizer side compared against beta.", scope: "Target-local derivation; formal alignment pending.", source: "draft.tex:916-930" },
  { id: "gtn-collapse-membership", from: "gtnPaper", to: "gtnPerfectCollapse", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "contains local lemma", reason: "The target states and proves the perfect-graph collapse.", scope: "Paper ownership is not a mathematical dependency.", source: "draft.tex:634-684" },
  { id: "gtn-antiblocker-membership", from: "gtnPaper", to: "gtnAntiblocker", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "contains local identity", reason: "The antiblocker identity is included in the target lemma.", scope: "Paper ownership is not a mathematical dependency.", source: "draft.tex:671-684" },
  { id: "gtn-rom-membership", from: "gtnPaper", to: "gtnClosedFormRom", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "contains target theorem", reason: "The target paper derives the closed-form reduced-RoM result.", scope: "Paper ownership is not a mathematical dependency.", source: "draft.tex:687-723" },
  { id: "wrong-shortcut", from: "xuPerfectHbar", to: "gtnPerfectCollapse", type: "rejected_shortcut", step: 3, status: "REJECTED", verdict: "WRONG_RELATION_TYPE", label: "does not support", reason: "The Xu theorem concerns beta versus alpha in a squared-profile optimization; the target collapse concerns alpha, theta, and fractional clique cover.", scope: "Retained only as negative relation-audit evidence. It must not enter MathClaimDependencyDAG(q).", source: "Xu main.tex:394-400 compared with target draft.tex:634-684" },
  { id: "collapse-antiblocker", from: "gtnPerfectCollapse", to: "gtnAntiblocker", type: "derives", step: 3, status: "LOCAL_DERIVATION / ALIGNMENT_BLOCKED", label: "derives locally", reason: "The target uses perfect collapse, a fractional clique cover, and downward closure to obtain the convex-hull identity.", scope: "Classical weighted-duality and antiblocker alignment remains open.", source: "draft.tex:680-684" },
  { id: "antiblocker-rom", from: "gtnAntiblocker", to: "gtnClosedFormRom", type: "derives", step: 3, status: "LOCAL_DERIVATION / BLOCKED_IMPORTS", label: "supports closed form", reason: "Clique-incidence convex combinations reduce the exact graph program to the clique l1 expression.", scope: "The no-active-dependency and exact-graph-program prerequisites remain essential but are outside this focused lineage.", source: "draft.tex:687-723" },
  { id: "classic-chvatal-membership", from: "classicCorpus", to: "chvatal", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "groups source", reason: "Visual source-corpus membership.", scope: "Not a mathematical dependency or virtual Agent import.", source: "DOI:10.1016/0095-8956(75)90041-6" },
  { id: "classic-lovasz72-membership", from: "classicCorpus", to: "lovasz72", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "groups sources", reason: "Visual source-corpus membership.", scope: "Not a mathematical dependency or virtual Agent import.", source: "draft.tex:681" },
  { id: "classic-lovasz79-membership", from: "classicCorpus", to: "lovasz79", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "groups source", reason: "Visual source-corpus membership.", scope: "Not a mathematical dependency or virtual Agent import.", source: "draft.tex:649-662" },
  { id: "classic-fulkerson-membership", from: "classicCorpus", to: "fulkerson", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "groups sources", reason: "Visual source-corpus membership.", scope: "Not a mathematical dependency or virtual Agent import.", source: "draft.tex:683" },
  { id: "classic-gls-membership", from: "classicCorpus", to: "gls", type: "membership", step: 4, status: "MEMBERSHIP_ONLY", label: "groups source", reason: "Visual source-corpus membership.", scope: "Not a mathematical dependency or virtual Agent import.", source: "draft.tex:664-684" },
  { id: "chvatal-xu", from: "chvatal", to: "xuPerfectHbar", type: "shared_foundation", step: 4, status: "PRIMARY_SOURCE_ALIGNMENT_PENDING", label: "facet characterization foundation", reason: "Xu et al. use Chvátal's perfect/h-perfect stable-set-polytope characterization in the selected proof.", scope: "Exact original theorem/page alignment remains pending.", source: "Xu main.tex:385-400; appendix.tex:185-197" },
  { id: "chvatal-collapse", from: "chvatal", to: "gtnPerfectCollapse", type: "shared_foundation", step: 4, status: "PRIMARY_SOURCE_ALIGNMENT_PENDING", label: "weighted duality source chain", reason: "The target cites Chvátal in its weighted stable-set/fractional clique-cover equality chain.", scope: "Chvátal is one source among several, not the unique foundation.", source: "draft.tex:681" },
  { id: "lovasz72-collapse", from: "lovasz72", to: "gtnPerfectCollapse", type: "shared_foundation", step: 4, status: "PRIMARY_SOURCE_ALIGNMENT_PENDING", label: "perfect-graph duality foundation", reason: "The two Lovász 1972 references are cited in the target weighted-duality step.", scope: "The precise theorem imported from each paper remains to be aligned.", source: "draft.tex:681" },
  { id: "lovasz79-collapse", from: "lovasz79", to: "gtnPerfectCollapse", type: "shared_foundation", step: 4, status: "PRIMARY_SOURCE_ALIGNMENT_PENDING", label: "theta sandwich", reason: "The theta number is fixed between equal weighted independence and cover endpoints.", scope: "Precise weighted primary-source formulation remains pending.", source: "draft.tex:649-662, 681" },
  { id: "fulkerson-antiblocker", from: "fulkerson", to: "gtnAntiblocker", type: "shared_foundation", step: 4, status: "PRIMARY_SOURCE_ALIGNMENT_PENDING", label: "antiblocker identity foundation", reason: "The target explicitly identifies the local equality with Fulkerson's perfect-graph antiblocker identity.", scope: "Exact 1971/1972 statement alignment remains pending.", source: "draft.tex:683" },
  { id: "gls-collapse", from: "gls", to: "gtnPerfectCollapse", type: "shared_foundation", step: 4, status: "PRIMARY_SOURCE_ALIGNMENT_PENDING", label: "optimization and construction", reason: "GLS supplies the target's cited perfect-graph construction and optimization-separation basis for the algorithmic claim.", scope: "The target's section/page pointers have not yet been converted to an accepted atomic contract.", source: "draft.tex:664-684" }
];

let currentStep = 1;
let pinnedNodeId = null;
let tooltipPinned = false;
let svg;

const escapeHtml = value => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

function svgElement(name, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function markerFor(type) {
  return type === "membership" ? "" : `url(#lineage-arrow-${type})`;
}

function edgePath(edge) {
  const from = nodeCatalog[edge.from];
  const to = nodeCatalog[edge.to];
  const fromRadius = from.type === "agent" ? 45 : 17;
  const toRadius = to.type === "agent" ? 45 : 17;
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.max(1, Math.hypot(dx, dy));
  const startX = from.x + dx / length * fromRadius;
  const startY = from.y + dy / length * fromRadius;
  const endX = to.x - dx / length * toRadius;
  const endY = to.y - dy / length * toRadius;
  if (edge.type === "paper_cites") {
    return `M ${startX} ${startY} C ${startX - 120} 60, ${endX + 120} 60, ${endX} ${endY}`;
  }
  const bend = Math.max(28, Math.abs(endX - startX) * 0.38);
  return `M ${startX} ${startY} C ${startX + Math.sign(dx || 1) * bend} ${startY}, ${endX - Math.sign(dx || 1) * bend} ${endY}, ${endX} ${endY}`;
}

function drawDefs() {
  const defs = svgElement("defs");
  const colors = {
    paper_cites: "#315f78",
    theorem_import: "#1f6b4f",
    local_derivation: "#b06b20",
    shared_foundation: "#695283",
    derives: "#b06b20",
    rejected_shortcut: "#9c3f39"
  };
  Object.entries(colors).forEach(([type, fill]) => {
    const marker = svgElement("marker", {
      id: `lineage-arrow-${type}`,
      viewBox: "0 0 10 10",
      markerWidth: "8",
      markerHeight: "8",
      refX: "9",
      refY: "5",
      orient: "auto",
      markerUnits: "userSpaceOnUse"
    });
    marker.appendChild(svgElement("path", { d: "M1,1 L9,5 L1,9 L3.2,5 Z", fill }));
    defs.appendChild(marker);
  });
  const shadow = svgElement("filter", { id: "lineageNodeShadow", x: "-100%", y: "-100%", width: "300%", height: "320%" });
  shadow.appendChild(svgElement("feDropShadow", { dx: "0", dy: "3", stdDeviation: "2.5", "flood-color": "#17211c", "flood-opacity": "0.18" }));
  defs.appendChild(shadow);
  svg.appendChild(defs);
}

function renderScaffold() {
  const layer = svgElement("g", { class: "lineage-scaffold" });
  [
    { lane: "paper", y: 14, h: 210, labelY: 32, title: "PAPER AGENTS", caption: "citation and ownership" },
    { lane: "claim", y: 224, h: 330, labelY: 246, title: "MATH CLAIMS", caption: "typed theorem provenance" },
    { lane: "foundation", y: 554, h: 188, labelY: 576, title: "FOUNDATIONS", caption: "primary-source alignment pending" }
  ].forEach(band => {
    const group = svgElement("g", { class: "lane-band", "data-lane": band.lane });
    group.appendChild(svgElement("rect", { x: 14, y: band.y, width: 1292, height: band.h, class: "lane-band-fill" }));
    const title = svgElement("text", { x: 28, y: band.labelY, class: "lane-label" });
    title.textContent = band.title;
    group.appendChild(title);
    const caption = svgElement("text", { x: 28, y: band.labelY + 16, class: "lane-caption" });
    caption.textContent = band.caption;
    group.appendChild(caption);
    layer.appendChild(group);
  });
  [224, 554].forEach(y => layer.appendChild(svgElement("line", { x1: 14, y1: y, x2: 1306, y2: y, class: "lane-rule" })));
  const branchA = svgElement("text", { x: 610, y: 345, class: "branch-label" });
  branchA.textContent = "SQUARED PROFILE BRANCH";
  layer.appendChild(branchA);
  const branchB = svgElement("text", { x: 610, y: 402, class: "branch-label" });
  branchB.textContent = "CLOSED-FORM RoM BRANCH";
  layer.appendChild(branchB);
  const warning = svgElement("text", { x: 610, y: 420, class: "branch-caption" });
  warning.textContent = "parallel perfect-graph use; no Xu theorem dependency";
  layer.appendChild(warning);
  svg.appendChild(layer);
}

function renderEdges() {
  const layer = svgElement("g", { class: "lineage-edge-layer" });
  edgeCatalog.forEach(edge => {
    const group = svgElement("g", {
      class: "lineage-edge-group",
      "data-edge-id": edge.id,
      "data-step": String(edge.step),
      tabindex: edge.type === "membership" ? "-1" : "0",
      role: edge.type === "membership" ? "presentation" : "button",
      "aria-label": `${edge.label}: ${nodeCatalog[edge.from].title} to ${nodeCatalog[edge.to].title}. Status ${edge.status}.`
    });
    const pathData = edgePath(edge);
    group.appendChild(svgElement("path", { d: pathData, class: "lineage-edge-underlay" }));
    const path = svgElement("path", { d: pathData, class: `lineage-edge ${edge.type}` });
    const marker = markerFor(edge.type);
    if (marker) path.setAttribute("marker-end", marker);
    group.appendChild(path);
    const hit = svgElement("path", { d: pathData, class: "lineage-edge-hit" });
    group.appendChild(hit);
    const showAtPointer = event => {
      highlightEdge(edge.id);
      showEdgeTooltip(edge, event.clientX + 18, event.clientY + 18);
    };
    hit.addEventListener("pointerenter", showAtPointer);
    hit.addEventListener("pointermove", moveTooltip);
    hit.addEventListener("pointerleave", clearHoverHighlight);
    if (edge.type !== "membership") {
      group.addEventListener("focus", () => {
        const rect = group.getBoundingClientRect();
        highlightEdge(edge.id);
        showEdgeTooltip(edge, rect.right + 12, rect.top);
      });
      group.addEventListener("blur", clearHoverHighlight);
    }
    layer.appendChild(group);
  });
  svg.appendChild(layer);
}

function renderAgentNode(id, node) {
  const group = svgElement("g", {
    class: "lineage-node agent-lineage-node",
    transform: `translate(${node.x},${node.y})`,
    tabindex: "0",
    role: "button",
    "aria-label": `${node.title}. ${node.status}.`,
    "data-node-id": id,
    "data-owner": node.owner,
    "data-status": node.status
  });
  group.appendChild(svgElement("circle", { r: 52, class: "node-hit-area" }));
  group.appendChild(svgElement("circle", { r: 44, class: "agent-status-track" }));
  group.appendChild(svgElement("circle", { r: 44, class: "agent-status-ring", "stroke-dasharray": "166 276", transform: "rotate(-90)" }));
  group.appendChild(svgElement("circle", { r: 40, class: "agent-outline" }));
  group.appendChild(svgElement("circle", { r: 36, class: "agent-disc", filter: "url(#lineageNodeShadow)" }));
  const first = svgElement("text", { x: 0, y: -4, class: "agent-label" });
  first.textContent = node.owner === "PGF" ? "SOURCE" : "PAPER";
  group.appendChild(first);
  const second = svgElement("text", { x: 0, y: 11, class: "agent-label" });
  second.textContent = node.owner === "PGF" ? "CORPUS" : "AGENT";
  group.appendChild(second);
  const code = svgElement("text", { x: 0, y: 25, class: "agent-code" });
  code.textContent = node.code;
  group.appendChild(code);
  return group;
}

function renderClaimNode(id, node) {
  const group = svgElement("g", {
    class: "lineage-node claim-lineage-node",
    transform: `translate(${node.x},${node.y})`,
    tabindex: "0",
    role: "button",
    "aria-label": `${node.title}. ${node.status}. ${node.statement}`,
    "data-node-id": id,
    "data-owner": node.owner,
    "data-status": node.status
  });
  group.appendChild(svgElement("circle", { r: 23, class: "node-hit-area" }));
  group.appendChild(svgElement("circle", { r: 15.5, class: "claim-membership-ring" }));
  group.appendChild(svgElement("circle", { r: 12.5, class: "claim-status-ring" }));
  group.appendChild(svgElement("circle", { r: 10.5, class: "claim-shell", filter: "url(#lineageNodeShadow)" }));
  group.appendChild(svgElement("circle", { r: 7.5, class: "claim-dot" }));
  group.appendChild(svgElement("circle", { r: 14, class: "node-focus" }));
  const owner = svgElement("text", { x: 14, y: -14, class: "owner-code" });
  owner.textContent = node.owner;
  group.appendChild(owner);
  return group;
}

function bindNodeInteractions(id, group) {
  group.addEventListener("pointerenter", event => {
    highlightNode(id);
    showNodeTooltip(id, event.clientX + 18, event.clientY + 18);
  });
  group.addEventListener("pointermove", moveTooltip);
  group.addEventListener("pointerleave", clearHoverHighlight);
  group.addEventListener("focus", () => {
    const rect = group.getBoundingClientRect();
    highlightNode(id);
    showNodeTooltip(id, rect.right + 12, rect.top);
  });
  group.addEventListener("blur", clearHoverHighlight);
  group.addEventListener("click", event => {
    event.stopPropagation();
    pinNodeTooltip(id, group);
  });
  group.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      pinNodeTooltip(id, group);
    }
  });
}

function renderNodes() {
  const layer = svgElement("g", { class: "lineage-node-layer" });
  Object.entries(nodeCatalog).forEach(([id, node]) => {
    const group = node.type === "agent" ? renderAgentNode(id, node) : renderClaimNode(id, node);
    const fallback = svgElement("title");
    fallback.textContent = `${node.title}: ${node.statement}`;
    group.appendChild(fallback);
    bindNodeInteractions(id, group);
    layer.appendChild(group);
  });
  svg.appendChild(layer);
}

function renderGraph() {
  svg.innerHTML = "";
  drawDefs();
  renderScaffold();
  renderEdges();
  renderNodes();
  applyStepState();
}

function activeProfile() {
  return stepProfiles[currentStep - 1];
}

function highlightNode(id) {
  if (tooltipPinned) return;
  const relatedNodes = new Set([id]);
  const relatedEdges = new Set();
  edgeCatalog.forEach(edge => {
    if (edge.from === id || edge.to === id) {
      relatedEdges.add(edge.id);
      relatedNodes.add(edge.from);
      relatedNodes.add(edge.to);
    }
  });
  document.querySelectorAll(".lineage-node").forEach(element => {
    element.classList.toggle("hover-active", relatedNodes.has(element.dataset.nodeId));
    element.classList.toggle("hover-muted", !relatedNodes.has(element.dataset.nodeId));
  });
  document.querySelectorAll(".lineage-edge-group").forEach(element => {
    element.classList.toggle("hover-active", relatedEdges.has(element.dataset.edgeId));
    element.classList.toggle("hover-muted", !relatedEdges.has(element.dataset.edgeId));
  });
}

function highlightEdge(id) {
  if (tooltipPinned) return;
  const edge = edgeCatalog.find(candidate => candidate.id === id);
  if (!edge) return;
  document.querySelectorAll(".lineage-node").forEach(element => {
    const active = [edge.from, edge.to].includes(element.dataset.nodeId);
    element.classList.toggle("hover-active", active);
    element.classList.toggle("hover-muted", !active);
  });
  document.querySelectorAll(".lineage-edge-group").forEach(element => {
    const active = element.dataset.edgeId === id;
    element.classList.toggle("hover-active", active);
    element.classList.toggle("hover-muted", !active);
  });
}

function clearHoverHighlight() {
  if (tooltipPinned) return;
  document.querySelectorAll(".hover-active, .hover-muted").forEach(element => element.classList.remove("hover-active", "hover-muted"));
  hideTooltip();
}

function sourceLinks(sources) {
  return `<div class="tooltip-source-list">${sources.map(source => `
    <a class="tooltip-source-link" href="${escapeHtml(source.href)}"${source.href.startsWith("http") ? ' target="_blank" rel="noopener"' : ""}>
      <span>${escapeHtml(source.label)}</span><code>${escapeHtml(source.anchor)}</code>
    </a>`).join("")}</div>`;
}

function importsList(imports) {
  if (!imports.length) return "<p>No imported premise is recorded for this source node.</p>";
  return `<div class="tooltip-list">${imports.map(item => `<span>${escapeHtml(item)}</span>`).join("")}</div>`;
}

function nodeTooltipContent(id) {
  const node = nodeCatalog[id];
  return `
    <div class="tooltip-head" data-status="${escapeHtml(node.status)}">
      <span>${node.type === "agent" ? "Agent / source container" : `Claim / ${escapeHtml(node.owner)} membership`}</span>
      <span>${escapeHtml(node.status)}</span>
    </div>
    <h3>${escapeHtml(node.title)}</h3>
    <section><h4>Identifier</h4><code>${escapeHtml(node.identifier || id)}</code></section>
    <section><h4>Exact content</h4><p>${escapeHtml(node.statement)}</p></section>
    <section><h4>Imports</h4>${importsList(node.imports)}</section>
    <section><h4>Scope warning</h4><p>${escapeHtml(node.scope)}</p></section>
    <section><h4>Sources and exact local anchors</h4>${sourceLinks(node.sources)}</section>
    <p class="tooltip-policy">Status and membership rings remain independent. Source-grounded, local derivation, Registry mapping, and primary-source alignment do not by themselves mean ACCEPTED_CONTRACT.</p>`;
}

function edgeTooltipContent(edge) {
  const from = nodeCatalog[edge.from];
  const to = nodeCatalog[edge.to];
  return `
    <div class="tooltip-head" data-status="${escapeHtml(edge.status === "REJECTED" ? "REJECTED" : "SOURCE_GROUNDED_ALIGNMENT_PENDING")}">
      <span>${escapeHtml(edge.type)}</span><span>${escapeHtml(edge.status)}</span>
    </div>
    <h3>${escapeHtml(from.title)} &rarr; ${escapeHtml(to.title)}</h3>
    <section><h4>Relationship</h4><code>${escapeHtml(edge.label)}${edge.verdict ? ` / ${escapeHtml(edge.verdict)}` : ""}</code></section>
    <section><h4>Why this arrow exists</h4><p>${escapeHtml(edge.reason)}</p></section>
    <section><h4>Scope warning</h4><p>${escapeHtml(edge.scope)}</p></section>
    <section><h4>Source anchors</h4><code>${escapeHtml(edge.source)}</code></section>
    <p class="tooltip-policy">Only typed mathematical prerequisite edges may enter a query build DAG. Citation, membership, pending foundation, and rejected relations remain separate evidence records.</p>`;
}

function showNodeTooltip(id, x, y) {
  showTooltip(nodeTooltipContent(id), x, y);
}
function showEdgeTooltip(edge, x, y) {
  showTooltip(edgeTooltipContent(edge), x, y);
}

function pinNodeTooltip(id, element) {
  const tooltip = document.getElementById("tooltip");
  if (pinnedNodeId === id && tooltipPinned) {
    closePinnedTooltip();
    return;
  }
  pinnedNodeId = id;
  tooltipPinned = true;
  tooltip.classList.add("pinned");
  tooltip.innerHTML = `<button type="button" class="tooltip-close" aria-label="Close pinned details">Close</button>${nodeTooltipContent(id)}`;
  tooltip.hidden = false;
  tooltip.querySelector(".tooltip-close").addEventListener("click", closePinnedTooltip);
  const rect = element.getBoundingClientRect();
  positionTooltip(rect.right + 12, rect.top);
  document.querySelectorAll(".lineage-node").forEach(node => node.classList.toggle("is-pinned", node.dataset.nodeId === id));
  highlightNode(id);
}

function closePinnedTooltip() {
  const tooltip = document.getElementById("tooltip");
  tooltipPinned = false;
  pinnedNodeId = null;
  tooltip.classList.remove("pinned");
  tooltip.hidden = true;
  document.querySelectorAll(".is-pinned, .hover-active, .hover-muted").forEach(element => element.classList.remove("is-pinned", "hover-active", "hover-muted"));
}

function showTooltip(content, x, y) {
  if (tooltipPinned) return;
  const tooltip = document.getElementById("tooltip");
  tooltip.innerHTML = content;
  tooltip.hidden = false;
  positionTooltip(x, y);
}
function moveTooltip(event) {
  if (!tooltipPinned) positionTooltip(event.clientX + 18, event.clientY + 18);
}
function positionTooltip(x, y) {
  const tooltip = document.getElementById("tooltip");
  if (tooltip.hidden) return;
  const margin = 14;
  const left = Math.min(x, window.innerWidth - tooltip.offsetWidth - margin);
  const top = Math.min(y, window.innerHeight - tooltip.offsetHeight - margin);
  tooltip.style.left = `${Math.max(margin, left)}px`;
  tooltip.style.top = `${Math.max(margin, top)}px`;
}
function hideTooltip() {
  if (!tooltipPinned) document.getElementById("tooltip").hidden = true;
}

function applyStepState() {
  const profile = activeProfile();
  const activeNodes = new Set(profile.activeNodes);
  const activeEdges = new Set(profile.activeEdges);
  const contextNodes = new Set();
  activeEdges.forEach(id => {
    const edge = edgeCatalog.find(candidate => candidate.id === id);
    if (edge) {
      contextNodes.add(edge.from);
      contextNodes.add(edge.to);
    }
  });
  document.querySelectorAll(".lineage-node").forEach(element => {
    const id = element.dataset.nodeId;
    element.classList.toggle("step-current", activeNodes.has(id));
    element.classList.toggle("step-context", !activeNodes.has(id) && contextNodes.has(id));
    element.classList.toggle("step-muted", !activeNodes.has(id) && !contextNodes.has(id));
  });
  document.querySelectorAll(".lineage-edge-group").forEach(element => {
    const id = element.dataset.edgeId;
    const edge = edgeCatalog.find(candidate => candidate.id === id);
    const context = edge && activeNodes.has(edge.from) && activeNodes.has(edge.to);
    element.classList.toggle("step-current", activeEdges.has(id));
    element.classList.toggle("step-context", !activeEdges.has(id) && context);
    element.classList.toggle("step-muted", !activeEdges.has(id) && !context);
  });
}

function updateCopy() {
  const profile = activeProfile();
  document.getElementById("stepTitle").textContent = profile.title;
  document.getElementById("stepSummary").textContent = profile.summary;
  const badge = document.getElementById("stepBadge");
  badge.textContent = profile.badge;
  badge.className = profile.badgeClass;
  document.getElementById("stepBannerText").textContent = profile.note;
  document.getElementById("stepNote").textContent = profile.note;
  document.getElementById("relationValue").textContent = profile.relation;
  document.getElementById("evidenceValue").textContent = profile.evidence;
  document.getElementById("promotionValue").textContent = profile.promotion;
  document.getElementById("verdictValue").textContent = profile.verdict;
  document.getElementById("alignmentValue").textContent = profile.alignment;
  document.getElementById("explanationTitle").textContent = profile.explanationTitle;
  document.getElementById("explanationBody").textContent = profile.explanationBody;
  const alignmentMetric = document.querySelector(".lineage-status-panel .query-metric.state");
  alignmentMetric.classList.toggle("pending", currentStep !== 3);
  alignmentMetric.classList.toggle("rejected", currentStep === 3);
  document.querySelectorAll("#stepTabs button").forEach(button => {
    button.setAttribute("aria-selected", String(Number(button.dataset.step) + 1 === currentStep));
  });
  document.getElementById("previousStep").disabled = currentStep === 1;
  document.getElementById("nextStep").disabled = currentStep === stepProfiles.length;
  document.getElementById("nextStep").textContent = currentStep === stepProfiles.length ? "Lineage complete" : "Next step ->";
  document.getElementById("stepMeta").textContent = `${profile.activeNodes.length} active nodes | ${profile.activeEdges.length} typed links | step ${String(currentStep).padStart(2, "0")} of 04`;
}

function setStep(step) {
  currentStep = Math.max(1, Math.min(stepProfiles.length, step));
  closePinnedTooltip();
  applyStepState();
  updateCopy();
}

document.addEventListener("DOMContentLoaded", () => {
  svg = document.getElementById("lineageDag");
  renderGraph();
  updateCopy();
  document.querySelectorAll("#stepTabs button").forEach(button => {
    button.addEventListener("click", () => setStep(Number(button.dataset.step) + 1));
  });
  document.getElementById("previousStep").addEventListener("click", () => setStep(currentStep - 1));
  document.getElementById("nextStep").addEventListener("click", () => setStep(currentStep + 1));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closePinnedTooltip();
  });
  document.getElementById("graphStage").addEventListener("click", event => {
    if (event.target === event.currentTarget) closePinnedTooltip();
  });
});
