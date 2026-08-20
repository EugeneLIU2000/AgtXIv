const roundProfiles = [
  {
    shortTitle: "Extract candidate",
    caption: "prose -> semantic v0",
    title: "The sentence becomes an overgeneralized candidate",
    summary: "The wording suggests a route to a closed-form value. It proposes a dependency; it does not yet establish the missing assumptions.",
    badge: "CANDIDATE EXTRACTION",
    badgeClass: "candidate",
    note: "This is an extracted semantic shortcut, not an accepted theorem.",
    explanationTitle: "Semantic extraction proposes a route; it does not close it",
    explanationBody: "Round 1 records the strongest reading suggested by the prose. The later rounds keep this dot visible so the precise mathematical correction remains traceable.",
    candidateClaim: "perfect graph is enough",
    graphValue: "not evaluated",
    exactValue: "not evaluated",
    activeRelations: "not checked",
    disposition: "candidate"
  },
  {
    shortTitle: "Formalize graph",
    caption: "anticommutation -> relaxation",
    title: "The graph captures anticommutation, not every physical sign",
    summary: "G_M = C4 + K1 is perfect, but perfectness only simplifies the graph optimization. It does not make all relaxed sign assignments physical.",
    badge: "GRAPH RELAXATION",
    badgeClass: "math",
    note: "Graph edges record pairwise anticommutation; independent sets give mutually commuting contexts.",
    explanationTitle: "Pairwise graph structure is only the compatibility skeleton",
    explanationBody: "The frustration graph correctly determines which observables anticommute. The graph-only relaxation adds all sign corners inside an independent set, including corners that Pauli multiplication may forbid.",
    candidateClaim: "graph relaxation treated as exact",
    graphValue: "1",
    exactValue: "unknown",
    activeRelations: "not checked",
    disposition: "unsafe shortcut"
  },
  {
    shortTitle: "Correct with math",
    caption: "parity locks -> corrected claim",
    title: "Pauli products add the missing sign constraints",
    summary: "Two product relations lie inside commuting contexts. Each parity lock reduces 8 graph-relaxed sign choices to 4 physical choices, so exactness fails for this M.",
    badge: "CORRECTION REQUIRED",
    badgeClass: "blocked",
    note: "Operator multiplication tells us which joint outcomes can physically exist, information that the pairwise graph cannot contain.",
    explanationTitle: "The math claim changes the semantic claim",
    explanationBody: "Perfectness still controls the graph optimization, but exact projected geometry additionally requires no Pauli-active dependency. The corrected semantic statement keeps both hypotheses and marks this instance as outside its regime.",
    candidateClaim: "missing no-active condition",
    graphValue: "1",
    exactValue: "not equal",
    activeRelations: "2 found",
    disposition: "corrected / blocked"
  },
  {
    shortTitle: "Validate finitely",
    caption: "1 vs 5/4 -> local verdict",
    title: "Finite evidence rejects the shortcut edge, not the whole method",
    summary: "The graph gives 1; matching exact primal and dual certificates give 5/4. The local shortcut is rejected while the corrected conditional statement is retained.",
    badge: "SHORTCUT REJECTED",
    badgeClass: "rejected",
    note: "This finite certificate validates the local audit verdict. It neither proves nor disproves a universal if-and-only-if theorem.",
    explanationTitle: "The final round separates a bad implication from a useful theorem",
    explanationBody: "The counterexample shows that perfectness alone is insufficient for this Pauli window. It supports retaining the additional no-active-dependency gate rather than discarding graph methods altogether.",
    candidateClaim: "conditional statement retained",
    graphValue: "1",
    exactValue: "5/4",
    activeRelations: "2 certified",
    disposition: "shortcut rejected"
  }
];

const roundBands = [
  { x1: 90, x2: 330 },
  { x1: 330, x2: 620 },
  { x1: 620, x2: 970 },
  { x1: 970, x2: 1300 }
];

const nodeCatalog = {
  sourceProse: {
    round: 1, lane: "evidence", status: "source", x: 145, y: 610,
    title: "Citation and target prose",
    meaning: "The wording proposes a graph-only route, but it does not expose every hypothesis carried by that route.",
    why: "It creates the candidate semantic dependency that the later rounds audit.",
    math: "No theorem is established at this node.",
    changes: "Proposes semantic claim v0.",
    scope: "Source-language evidence only.",
    source: "draft.tex:134-157, 198-244"
  },
  exactTarget: {
    round: 1, lane: "math", status: "source", x: 215, y: 370,
    title: "Exact projected robustness",
    meaning: "Robustness of magic restricted to the measured Pauli window is defined using physically realizable projected stabilizer points.",
    why: "It fixes the exact quantity that the semantic shortcut is trying to compute.",
    math: "RoM_M is optimized over STAB(M), the stabilizer polytope projected onto the coordinates in M.",
    changes: "Defines the target quantity; it does not justify a graph-only formula.",
    scope: "Finite Pauli window with exact expectation values.",
    source: "statement:2607.26154v1:relaxation-exactness"
  },
  semanticV0: {
    round: 1, lane: "semantic", status: "candidate", x: 210, y: 145,
    title: "Semantic claim v0: perfectness appears sufficient",
    meaning: "The extracted language is read as though a perfect frustration graph alone made the graph formula exact.",
    why: "This is the overgeneralized implication that the audit must either support, repair, or reject.",
    math: "Candidate only: perfect(G_M) => exact RoM_M equals the clique expression.",
    changes: "Starts the semantic-claim lineage.",
    scope: "Oracle candidate; not an accepted paper theorem in this form.",
    source: "Language and citation extraction"
  },
  pauliWindow: {
    round: 2, lane: "evidence", status: "source", x: 390, y: 610,
    title: "Recorded Pauli window",
    meaning: "The concrete two-qubit measurement set used to stress-test the candidate claim.",
    why: "It supplies the operators from which both the graph and the product relations are calculated.",
    math: "M = {XX, ZZ, YY, IX, XI}.",
    changes: "Turns the semantic question into a finite instance.",
    scope: "One two-qubit Pauli window.",
    source: "statement:prototype:active-dependency-physical-counterexample"
  },
  frustrationGraph: {
    round: 2, lane: "math", status: "neutral", x: 385, y: 315,
    title: "Frustration graph",
    meaning: "A graph edge means that two Pauli observables anticommute.",
    why: "It captures pairwise incompatibility but not products involving three or more commuting observables.",
    math: "G_M = C4 disjoint union K1.",
    changes: "Replaces vague compatibility language with the correct anticommutation relation.",
    scope: "Pairwise commutation data only.",
    source: "statement:2607.26154v1:perfect-frustration-graph"
  },
  commutingContexts: {
    round: 2, lane: "math", status: "neutral", x: 465, y: 405,
    title: "Independent sets are commuting contexts",
    meaning: "Vertices with no frustration-graph edges between them represent pairwise commuting Pauli observables.",
    why: "The graph relaxation assigns signs independently inside these contexts.",
    math: "S is a commuting context exactly when S is an independent set of G_M.",
    changes: "Defines the contexts on which the sign relaxation is built.",
    scope: "Pairwise commuting support; product parity is still absent.",
    source: "agents/graph-theoretic-nonstabilizerness/reviews/physical-semantics.md"
  },
  perfectGraph: {
    round: 2, lane: "math", status: "neutral", x: 545, y: 315,
    title: "Perfectness condition",
    meaning: "The four-cycle plus isolated point is a perfect graph.",
    why: "Perfectness simplifies the graph optimization, but it does not guarantee that graph-relaxed signs are physical.",
    math: "Every induced H of G_M satisfies chi(H) = omega(H); all 32 induced subgraphs are checked in Round 4.",
    changes: "Retains a necessary graph hypothesis while exposing its limited role.",
    scope: "Graph optimization only.",
    source: "assumption:2607.26154v1:perfect-frustration-graph"
  },
  semanticV1: {
    round: 2, lane: "semantic", status: "candidate", x: 585, y: 145,
    title: "Semantic claim v1: graph relaxation treated as exact",
    meaning: "Every deterministic sign assignment on a commuting context is temporarily treated as a physical projected stabilizer point.",
    why: "This step makes the hidden assumption explicit and produces the graph-only value 1.",
    math: "Sign-relaxed polytope = exact STAB(M), assumed without the no-active-dependency gate.",
    changes: "Makes semantic claim v0 mathematically testable.",
    scope: "Outer relaxation; exactness is not established.",
    source: "statement:2607.26154v1:sign-relaxed-polytope"
  },
  productMinus: {
    round: 3, lane: "math", status: "correction", x: 665, y: 300,
    title: "Negative Pauli product relation",
    meaning: "Three commuting observables multiply to minus the identity, fixing the parity of their eigenvalue signs.",
    why: "The graph sees no edges inside this triple, yet the three signs are not independent.",
    math: "XX * ZZ * YY = -I, hence s_XX s_ZZ s_YY = -1.",
    changes: "Adds a higher-order constraint missing from semantic claim v1.",
    scope: "Commuting context {XX, ZZ, YY}.",
    source: "verification/logs/finite-instance-results.json"
  },
  productPlus: {
    round: 3, lane: "math", status: "correction", x: 755, y: 300,
    title: "Positive Pauli product relation",
    meaning: "A second commuting triple also has a fixed product sign.",
    why: "It shows that the chosen window contains two active contexts, not one cherry-picked relation.",
    math: "XX * IX * XI = +I, hence s_XX s_IX s_XI = +1.",
    changes: "Strengthens the diagnosis of the missing sign layer.",
    scope: "Commuting context {XX, IX, XI}.",
    source: "verification/logs/finite-instance-results.json"
  },
  activeDependencies: {
    round: 3, lane: "math", status: "correction", x: 710, y: 375,
    title: "Pauli-active dependencies",
    meaning: "Both product relations lie completely inside commuting contexts and therefore constrain allowed signs.",
    why: "Active dependencies are precisely the graph-invisible obstruction to treating the sign relaxation as exact.",
    math: "Two inclusion-minimal product relations have commuting support.",
    changes: "Supplies the missing hypothesis test for the semantic claim.",
    scope: "Local diagnosis for this M.",
    source: "assumption:2607.26154v1:no-pauli-active-dependencies"
  },
  signGap: {
    round: 3, lane: "math", status: "correction", x: 710, y: 455,
    title: "Physical signs differ from graph-relaxed signs",
    meaning: "Each parity check keeps four physical sign triples while the graph relaxation contains eight.",
    why: "The relaxed cube contains nonphysical corners, so its geometry is strictly too large for this instance.",
    math: "|B_S| = 4 while the unrestricted sign set has size 8.",
    changes: "Converts product identities into a geometric correction.",
    scope: "Exact finite sign enumeration for the displayed contexts.",
    source: "statement:prototype:active-dependency-negative-control"
  },
  exactnessGate: {
    round: 3, lane: "math", status: "rejected", x: 845, y: 415,
    title: "Exactness gate fails for this window",
    meaning: "The exact and sign-relaxed projected polytopes coincide only when no Pauli-active dependency is present.",
    why: "Two active relations are present, so graph-relaxed robustness cannot be promoted to exact robustness here.",
    math: "STAB(M) = relaxed STAB(M) iff M has no Pauli-active dependencies.",
    changes: "Blocks the unconditional implication in semantic claim v1.",
    scope: "The local failure is certified; the universal iff theorem is not proved by this demo.",
    source: "statement:2607.26154v1:relaxation-exactness"
  },
  semanticV2: {
    round: 3, lane: "semantic", status: "corrected", x: 900, y: 105,
    title: "Corrected semantic claim",
    meaning: "Perfectness controls graph optimization; absence of active dependencies controls whether that optimization represents exact projected stabilizer geometry.",
    why: "It preserves the useful graph result while restoring the missing physical premise.",
    math: "perfect(G_M) AND no active dependency => the conditional closed-form equality.",
    changes: "Revises semantic claim v1 rather than discarding graph methods.",
    scope: "Conditional theorem form; dependency closure remains separate.",
    source: "statement:2607.26154v1:closed-form-equality"
  },
  instanceBlocked: {
    round: 3, lane: "semantic", status: "rejected", x: 940, y: 185,
    title: "Local instance is outside the corrected regime",
    meaning: "This M is perfect but violates the added no-active-dependency condition.",
    why: "The graph-only value is now a candidate relaxation value, not an exact semantic conclusion.",
    math: "perfect(G_M) is true; no-active(M) is false.",
    changes: "Blocks promotion of the original shortcut before numerical comparison.",
    scope: "Local applicability assessment only.",
    source: "statement:prototype:active-dependency-physical-counterexample"
  },
  graphCertificate: {
    round: 4, lane: "evidence", status: "validated", x: 1005, y: 550,
    title: "Graph certificate",
    meaning: "Direct anticommutation calculation confirms the graph and its perfectness.",
    why: "It rules out graph-construction error as the source of the later mismatch.",
    math: "G_M = C4 disjoint union K1; 32 induced subgraphs checked; perfect = true.",
    changes: "Validates the graph premise without validating the shortcut.",
    scope: "Finite exhaustive graph check.",
    source: "verification/logs/finite-instance-results.json"
  },
  graphValue: {
    round: 4, lane: "evidence", status: "validated", x: 1100, y: 550,
    title: "Graph-only value",
    meaning: "The clique or sign-relaxed calculation returns 1 for the recorded physical state.",
    why: "This is the numerical prediction made by the unsafe semantic shortcut.",
    math: "graph-only formula = 1.",
    changes: "Makes semantic claim v1 quantitatively falsifiable on this instance.",
    scope: "Graph-relaxed computation for one state.",
    source: "statement:prototype:active-dependency-physical-counterexample"
  },
  exactPrimal: {
    round: 4, lane: "evidence", status: "validated", x: 1005, y: 655,
    title: "Exact primal certificate",
    meaning: "A signed affine decomposition over physical projected stabilizer vertices attains value 5/4.",
    why: "It gives an exact feasible upper certificate using only physical vertices.",
    math: "Primal l1 value = 1.25 with coefficient sum 1.",
    changes: "Supports the exact side of the comparison.",
    scope: "Finite linear program certificate.",
    source: "verification/logs/finite-instance-results.json"
  },
  exactDual: {
    round: 4, lane: "evidence", status: "validated", x: 1100, y: 655,
    title: "Exact dual certificate",
    meaning: "A matching feasible witness reaches the same value 5/4.",
    why: "Matching primal and dual objectives certify exact optimality rather than a numerical guess.",
    math: "Dual objective = 1.25; maximum vertex constraint = 1.",
    changes: "Closes the finite optimization gap.",
    scope: "Finite deterministic certificate at tolerance 1e-9.",
    source: "verification:prototype:finite-instances"
  },
  certifiedMismatch: {
    round: 4, lane: "evidence", status: "rejected", x: 1200, y: 600,
    title: "Certified mismatch",
    meaning: "The graph-only prediction and the exact projected robustness disagree on the same physical state.",
    why: "A direct mismatch is sufficient to reject the local missing-premise shortcut.",
    math: "1 != 5/4, with exact primal = exact dual = 5/4.",
    changes: "Validates the local rejection produced by the mathematical correction.",
    scope: "Counterexample to the unqualified implication, not to every conditional graph formula.",
    source: "statement:prototype:active-dependency-physical-counterexample"
  },
  conditionalRetained: {
    round: 4, lane: "semantic", status: "corrected", x: 1045, y: 105,
    title: "Conditional semantic statement retained",
    meaning: "The graph formula remains meaningful when perfectness and the no-active-dependency gate are both present.",
    why: "The finite audit isolates the missing premise instead of rejecting the entire graph-theoretic program.",
    math: "Retain: perfect(G_M) AND no-active(M) => conditional closed form.",
    changes: "Carries semantic claim v2 forward as the corrected claim.",
    scope: "This finite demo does not prove the universal theorem.",
    source: "statement:2607.26154v1:closed-form-equality"
  },
  shortcutRejected: {
    round: 4, lane: "semantic", status: "rejected", x: 1200, y: 185,
    title: "Unqualified shortcut rejected",
    meaning: "For this instance, perfectness alone does not justify promoting the graph-only value to exact projected robustness.",
    why: "It is the final local semantic verdict supported independently by math and finite evidence.",
    math: "Reject for this M: perfect(G_M) => graph value = exact RoM_M.",
    changes: "Closes the audit of semantic claim v0/v1.",
    scope: "Local finite verdict; no universal disproof is claimed.",
    source: "verification:prototype:finite-instances"
  }
};

const edgeCatalog = [
  { id: "source-target", from: "sourceProse", to: "exactTarget", type: "definition", round: 1, label: "defines the target", reason: "The source language identifies the projected robustness being discussed." },
  { id: "target-v0", from: "exactTarget", to: "semanticV0", type: "definition", round: 1, label: "fixes the quantity", reason: "The semantic claim concerns exact projected robustness, not merely a relaxed surrogate." },

  { id: "v0-v1", from: "semanticV0", to: "semanticV1", type: "revision", round: 2, label: "formalizes as graph relaxation", reason: "The vague shortcut becomes the explicit assumption that all graph-relaxed sign patterns are physical." },
  { id: "window-graph", from: "pauliWindow", to: "frustrationGraph", type: "definition", round: 2, label: "computes anticommutation", reason: "Pairwise Pauli commutators define the frustration graph." },
  { id: "graph-contexts", from: "frustrationGraph", to: "commutingContexts", type: "definition", round: 2, label: "independent sets", reason: "Nonadjacent vertices form pairwise commuting contexts." },
  { id: "graph-perfect", from: "frustrationGraph", to: "perfectGraph", type: "support", round: 2, label: "tests perfectness", reason: "The concrete graph is checked against the perfect-graph condition." },
  { id: "contexts-v1", from: "commutingContexts", to: "semanticV1", type: "support", round: 2, label: "builds relaxed signs", reason: "The relaxation assigns unrestricted deterministic signs to each commuting context." },
  { id: "perfect-v1", from: "perfectGraph", to: "semanticV1", type: "support", round: 2, label: "makes shortcut plausible", reason: "Perfectness collapses the graph optimization but says nothing about sign parity." },
  { id: "target-v1", from: "exactTarget", to: "semanticV1", type: "definition", round: 2, label: "compares exact and relaxed", reason: "The unsafe step identifies the relaxed graph quantity with the exact target." },

  { id: "window-minus", from: "pauliWindow", to: "productMinus", type: "math", round: 3, label: "multiplies Pauli operators", reason: "The concrete window contains the negative product relation." },
  { id: "window-plus", from: "pauliWindow", to: "productPlus", type: "math", round: 3, label: "multiplies Pauli operators", reason: "The same window also contains the positive product relation." },
  { id: "minus-active", from: "productMinus", to: "activeDependencies", type: "math", round: 3, label: "lies in a commuting context", reason: "Its support is an independent set, so the product parity is active." },
  { id: "plus-active", from: "productPlus", to: "activeDependencies", type: "math", round: 3, label: "lies in a commuting context", reason: "The second support is also a commuting context." },
  { id: "contexts-active", from: "commutingContexts", to: "activeDependencies", type: "definition", round: 3, label: "checks support", reason: "Active means that a product relation lies wholly inside a commuting context." },
  { id: "active-sign-gap", from: "activeDependencies", to: "signGap", type: "math", round: 3, label: "removes sign corners", reason: "Each product equation becomes a parity lock on joint eigenvalue signs." },
  { id: "sign-gate", from: "signGap", to: "exactnessGate", type: "math", round: 3, label: "fails exactness", reason: "Four physical corners cannot equal the eight-corner graph relaxation." },
  { id: "v1-v2", from: "semanticV1", to: "semanticV2", type: "revision", round: 3, label: "revised by missing premise", reason: "The semantic claim is repaired by adding the no-active-dependency condition." },
  { id: "perfect-v2", from: "perfectGraph", to: "semanticV2", type: "support", round: 3, label: "retains graph hypothesis", reason: "Perfectness remains the condition that simplifies graph optimization." },
  { id: "gate-v2", from: "exactnessGate", to: "semanticV2", type: "math", round: 3, label: "adds exactness hypothesis", reason: "No active dependency is needed before relaxed graph geometry can represent exact geometry." },
  { id: "v2-blocked", from: "semanticV2", to: "instanceBlocked", type: "blocked", round: 3, label: "applies corrected regime", reason: "The corrected claim is not applicable because one required premise fails." },
  { id: "active-blocked", from: "activeDependencies", to: "instanceBlocked", type: "blocked", round: 3, label: "violates premise", reason: "Two active relations directly falsify the no-active condition for this M." },

  { id: "perfect-cert", from: "perfectGraph", to: "graphCertificate", type: "certificate", round: 4, label: "checks graph premise", reason: "Finite enumeration confirms perfectness independently." },
  { id: "graph-cert-value", from: "graphCertificate", to: "graphValue", type: "certificate", round: 4, label: "evaluates graph route", reason: "The certified graph produces the graph-only prediction 1." },
  { id: "sign-primal", from: "signGap", to: "exactPrimal", type: "certificate", round: 4, label: "uses physical vertices", reason: "The exact primal keeps only physically admissible projected stabilizer vertices." },
  { id: "sign-dual", from: "signGap", to: "exactDual", type: "certificate", round: 4, label: "uses physical constraints", reason: "The dual witness is checked against the exact physical vertex set." },
  { id: "graph-mismatch", from: "graphValue", to: "certifiedMismatch", type: "blocked", round: 4, label: "compares value 1", reason: "The graph-only side of the comparison is fixed at 1." },
  { id: "primal-mismatch", from: "exactPrimal", to: "certifiedMismatch", type: "certificate", round: 4, label: "upper certificate 5/4", reason: "The primal certificate reaches 5/4." },
  { id: "dual-mismatch", from: "exactDual", to: "certifiedMismatch", type: "certificate", round: 4, label: "lower certificate 5/4", reason: "The matching dual certificate proves that 5/4 is exact." },
  { id: "v2-retained", from: "semanticV2", to: "conditionalRetained", type: "certificate", round: 4, label: "retains corrected form", reason: "The finite audit is consistent with the corrected conditional semantic statement." },
  { id: "blocked-rejected", from: "instanceBlocked", to: "shortcutRejected", type: "blocked", round: 4, label: "awaits finite verdict", reason: "The failed premise predicts that the shortcut must not be promoted." },
  { id: "mismatch-rejected", from: "certifiedMismatch", to: "shortcutRejected", type: "blocked", round: 4, label: "validates local rejection", reason: "The certified numerical mismatch closes the local semantic audit." }
];

let currentRound = 1;
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
  return `url(#arrow-${type})`;
}

function edgePath(edge) {
  const from = nodeCatalog[edge.from];
  const to = nodeCatalog[edge.to];
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.max(1, Math.hypot(dx, dy));
  const offset = 14;
  const startX = from.x + dx / length * offset;
  const startY = from.y + dy / length * offset;
  const endX = to.x - dx / length * offset;
  const endY = to.y - dy / length * offset;
  if (Math.abs(dx) < 44) {
    const middleY = (startY + endY) / 2;
    return `M ${startX} ${startY} C ${startX} ${middleY}, ${endX} ${middleY}, ${endX} ${endY}`;
  }
  const bend = Math.max(28, Math.abs(endX - startX) * 0.42);
  return `M ${startX} ${startY} C ${startX + bend} ${startY}, ${endX - bend} ${endY}, ${endX} ${endY}`;
}

function drawDefs() {
  const defs = svgElement("defs");
  const colors = {
    definition: "#315f78",
    support: "#8f9e96",
    revision: "#1f6b4f",
    math: "#b06b20",
    certificate: "#1f6b4f",
    blocked: "#9c3f39"
  };
  Object.entries(colors).forEach(([type, fill]) => {
    const marker = svgElement("marker", {
      id: `arrow-${type}`,
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
  const shadow = svgElement("filter", { id: "auditNodeShadow", x: "-100%", y: "-100%", width: "300%", height: "320%" });
  shadow.appendChild(svgElement("feDropShadow", { dx: "0", dy: "3", stdDeviation: "2.5", "flood-color": "#17211c", "flood-opacity": "0.18" }));
  defs.appendChild(shadow);
  svg.appendChild(defs);
}

function renderScaffold() {
  const layer = svgElement("g", { class: "audit-scaffold" });
  roundBands.forEach((band, index) => {
    const group = svgElement("g", { class: "round-band", "data-round": String(index + 1) });
    group.appendChild(svgElement("rect", {
      x: band.x1,
      y: 14,
      width: band.x2 - band.x1,
      height: 716,
      class: "round-band-fill"
    }));
    const roundLabel = svgElement("text", { x: band.x1 + 18, y: 36, class: "round-label" });
    roundLabel.textContent = `ROUND ${String(index + 1).padStart(2, "0")}`;
    group.appendChild(roundLabel);
    const title = svgElement("text", { x: band.x1 + 18, y: 56, class: "round-title" });
    title.textContent = roundProfiles[index].shortTitle;
    group.appendChild(title);
    const caption = svgElement("text", { x: band.x1 + 18, y: 73, class: "round-caption" });
    caption.textContent = roundProfiles[index].caption;
    group.appendChild(caption);
    group.addEventListener("click", () => setRound(index + 1));
    layer.appendChild(group);
  });

  [235, 505].forEach(y => layer.appendChild(svgElement("line", { x1: 90, y1: y, x2: 1300, y2: y, class: "lane-rule" })));
  [330, 620, 970].forEach(x => layer.appendChild(svgElement("line", { x1: x, y1: 14, x2: x, y2: 730, class: "round-rule" })));

  [
    [28, 128, "SEMANTIC", "claim versions"],
    [28, 355, "MATH", "premises + constraints"],
    [28, 585, "EVIDENCE", "finite checks"]
  ].forEach(([x, y, title, caption]) => {
    const titleNode = svgElement("text", { x, y, class: "lane-label" });
    titleNode.textContent = title;
    layer.appendChild(titleNode);
    const captionNode = svgElement("text", { x, y: y + 16, class: "lane-caption" });
    captionNode.textContent = caption;
    layer.appendChild(captionNode);
  });
  svg.appendChild(layer);
}

function renderEdges() {
  const layer = svgElement("g", { class: "audit-edge-layer" });
  edgeCatalog.forEach(edge => {
    const group = svgElement("g", { class: "audit-edge-group", "data-edge-id": edge.id, "data-round": String(edge.round) });
    const pathData = edgePath(edge);
    const underlay = svgElement("path", { d: pathData, class: "claim-edge-underlay" });
    const path = svgElement("path", {
      d: pathData,
      class: `claim-edge ${edge.type}`,
      "marker-end": markerFor(edge.type)
    });
    const hitArea = svgElement("path", { d: pathData, class: "claim-edge-hit" });
    group.appendChild(underlay);
    group.appendChild(path);
    group.appendChild(hitArea);
    const show = event => {
      highlightEdge(edge.id);
      showEdgeTooltip(edge, event.clientX + 18, event.clientY + 18);
    };
    hitArea.addEventListener("pointerenter", show);
    hitArea.addEventListener("pointermove", moveTooltip);
    hitArea.addEventListener("pointerleave", clearHoverHighlight);
    path.addEventListener("pointerenter", show);
    path.addEventListener("pointermove", moveTooltip);
    path.addEventListener("pointerleave", clearHoverHighlight);
    layer.appendChild(group);
  });
  svg.appendChild(layer);
}

function renderNodes() {
  const layer = svgElement("g", { class: "audit-node-layer" });
  Object.entries(nodeCatalog).forEach(([id, node]) => {
    const group = svgElement("g", {
      class: "claim-node",
      transform: `translate(${node.x},${node.y})`,
      tabindex: "0",
      role: "button",
      "aria-label": `${node.title}. Round ${node.round}. ${node.meaning}`,
      "data-node-id": id,
      "data-round": String(node.round),
      "data-lane": node.lane,
      "data-status": node.status
    });
    group.appendChild(svgElement("circle", { r: 21, class: "node-hit-area" }));
    group.appendChild(svgElement("circle", { r: 12.5, class: "node-status-ring" }));
    group.appendChild(svgElement("circle", { r: 10.5, class: "node-shell", filter: "url(#auditNodeShadow)" }));
    group.appendChild(svgElement("circle", { r: 7.5, class: "node-dot" }));
    group.appendChild(svgElement("circle", { r: 14, class: "node-focus" }));
    const fallbackTitle = svgElement("title");
    fallbackTitle.textContent = `${node.title}: ${node.meaning}`;
    group.appendChild(fallbackTitle);
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
  applyRoundState();
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
  document.querySelectorAll(".claim-node").forEach(element => {
    element.classList.toggle("hover-active", relatedNodes.has(element.dataset.nodeId));
    element.classList.toggle("hover-muted", !relatedNodes.has(element.dataset.nodeId));
  });
  document.querySelectorAll(".audit-edge-group").forEach(element => {
    element.classList.toggle("hover-active", relatedEdges.has(element.dataset.edgeId));
    element.classList.toggle("hover-muted", !relatedEdges.has(element.dataset.edgeId));
  });
}

function highlightEdge(id) {
  if (tooltipPinned) return;
  const edge = edgeCatalog.find(candidate => candidate.id === id);
  if (!edge) return;
  document.querySelectorAll(".claim-node").forEach(element => {
    const active = [edge.from, edge.to].includes(element.dataset.nodeId);
    element.classList.toggle("hover-active", active);
    element.classList.toggle("hover-muted", !active);
  });
  document.querySelectorAll(".audit-edge-group").forEach(element => {
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

function statusLabel(status) {
  return {
    source: "Source / definition",
    neutral: "Mathematical structure",
    candidate: "Candidate / unchecked",
    correction: "Mathematical correction",
    corrected: "Corrected claim",
    validated: "Finite certificate passed",
    rejected: "Blocked / rejected"
  }[status] || status;
}

function laneLabel(lane) {
  return {
    semantic: "Semantic claim",
    math: "Mathematical claim",
    evidence: "Verification evidence"
  }[lane] || lane;
}

function nodeTooltipContent(id) {
  const node = nodeCatalog[id];
  return `
    <div class="tooltip-head" data-status="${escapeHtml(node.status)}">
      <span>Round ${String(node.round).padStart(2, "0")} / ${escapeHtml(laneLabel(node.lane))}</span>
      <span>${escapeHtml(statusLabel(node.status))}</span>
    </div>
    <h3>${escapeHtml(node.title)}</h3>
    <section><h4>Meaning</h4><p>${escapeHtml(node.meaning)}</p></section>
    <section><h4>Why it matters in this round</h4><p>${escapeHtml(node.why)}</p></section>
    <section><h4>Exact statement</h4><code>${escapeHtml(node.math)}</code></section>
    <section><h4>Effect on the semantic claim</h4><p>${escapeHtml(node.changes)}</p></section>
    <section><h4>Evidence boundary</h4><p>${escapeHtml(node.scope)}</p></section>
    <section><h4>Source</h4><code>${escapeHtml(node.source)}</code></section>
    <p class="tooltip-policy">Physical picture: the graph records pairwise anticommutation; Pauli multiplication determines which joint signs can physically exist. DAG means directed acyclic graph, RoM means robustness of magic, and STAB(M) means the stabilizer polytope projected onto M.</p>`;
}

function edgeTooltipContent(edge) {
  const from = nodeCatalog[edge.from];
  const to = nodeCatalog[edge.to];
  const typeLabel = {
    definition: "Defines / imports",
    support: "Supports",
    revision: "Revises semantic claim",
    math: "Mathematically refines",
    certificate: "Finite certificate",
    blocked: "Blocks implication"
  }[edge.type];
  return `
    <div class="tooltip-head" data-status="${edge.type === "blocked" ? "rejected" : edge.type === "certificate" ? "validated" : "neutral"}">
      <span>Round ${String(edge.round).padStart(2, "0")} / ${escapeHtml(typeLabel)}</span>
      <span>Claim dependency</span>
    </div>
    <h3>${escapeHtml(from.title)} &rarr; ${escapeHtml(to.title)}</h3>
    <section><h4>Relationship</h4><code>${escapeHtml(edge.label)}</code></section>
    <section><h4>Why this arrow exists</h4><p>${escapeHtml(edge.reason)}</p></section>
    <p class="tooltip-policy">These arrows connect claims, premises, and certificates. They are not edges of the Pauli frustration graph; those graph edges specifically mean anticommutation.</p>`;
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
  highlightNode(id);
  document.querySelectorAll(".claim-node").forEach(node => node.classList.toggle("is-pinned", node.dataset.nodeId === id));
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

function applyRoundState() {
  document.querySelectorAll(".claim-node, .audit-edge-group, .round-band").forEach(element => {
    const round = Number(element.dataset.round);
    element.classList.toggle("round-current", round === currentRound);
    element.classList.toggle("round-prior", round < currentRound);
    element.classList.toggle("round-future", round > currentRound);
  });
}

function updateCopy() {
  const profile = roundProfiles[currentRound - 1];
  document.getElementById("stepTitle").textContent = profile.title;
  document.getElementById("stepSummary").textContent = profile.summary;
  const badge = document.getElementById("stepBadge");
  badge.textContent = profile.badge;
  badge.className = profile.badgeClass;
  document.getElementById("stepBannerText").textContent = profile.note;
  document.getElementById("stepNote").textContent = profile.note;
  document.getElementById("candidateClaim").textContent = profile.candidateClaim;
  document.getElementById("graphValue").textContent = profile.graphValue;
  document.getElementById("exactValue").textContent = profile.exactValue;
  document.getElementById("activeRelations").textContent = profile.activeRelations;
  document.getElementById("auditDisposition").textContent = profile.disposition;
  document.getElementById("explanationTitle").textContent = profile.explanationTitle;
  document.getElementById("explanationBody").textContent = profile.explanationBody;

  const dispositionMetric = document.querySelector(".audit-status-panel .query-metric.state");
  dispositionMetric.classList.toggle("pending", currentRound < 3);
  dispositionMetric.classList.toggle("rejected", currentRound >= 3);
  document.querySelectorAll("#stepTabs button").forEach(button => {
    button.setAttribute("aria-selected", String(Number(button.dataset.step) + 1 === currentRound));
  });
  document.getElementById("previousStep").disabled = currentRound === 1;
  document.getElementById("nextStep").disabled = currentRound === roundProfiles.length;
  document.getElementById("nextStep").textContent = currentRound === roundProfiles.length ? "Audit complete" : "Next round ->";
  const cumulativeNodes = Object.values(nodeCatalog).filter(node => node.round <= currentRound).length;
  const currentNodes = Object.values(nodeCatalog).filter(node => node.round === currentRound).length;
  document.getElementById("stepMeta").textContent = `${currentNodes} new dots | ${cumulativeNodes} cumulative | round ${String(currentRound).padStart(2, "0")} of 04`;
}

function setRound(round) {
  currentRound = Math.max(1, Math.min(roundProfiles.length, round));
  closePinnedTooltip();
  applyRoundState();
  updateCopy();
}

document.addEventListener("DOMContentLoaded", () => {
  svg = document.getElementById("claimAuditDag");
  renderGraph();
  updateCopy();
  document.querySelectorAll("#stepTabs button").forEach(button => {
    button.addEventListener("click", () => setRound(Number(button.dataset.step) + 1));
  });
  document.getElementById("previousStep").addEventListener("click", () => setRound(currentRound - 1));
  document.getElementById("nextStep").addEventListener("click", () => setRound(currentRound + 1));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closePinnedTooltip();
  });
  document.getElementById("graphStage").addEventListener("click", event => {
    if (event.target === event.currentTarget) closePinnedTooltip();
  });
});
