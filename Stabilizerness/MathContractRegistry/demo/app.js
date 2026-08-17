const paths = {
  contracts: "../contracts/contracts.json",
  dag: "data/claim-dag.en.json",
  paperDag: "../../../graph/paper-dependencies.json"
};

const statusLabels = {
  EXISTING_PROJECT_DECLARATIONS: "Existing Lean",
  PLANNED_DELTA: "Planned Delta",
  GAP: "Gap",
  EXTERNAL_OR_UNMAPPED: "External or Unmapped",
  NOT_APPLICABLE: "Not Applicable"
};

const profiles = {
  mathematics: {
    title: "Mathematics",
    description: "All registered mathematical interfaces and dependencies. The selected target highlights one backward query closure.",
    available: true
  },
  computation: {
    title: "Computation",
    description: "Computational workflows, environments, inputs, and reproducibility interfaces.",
    available: false
  },
  physical: {
    title: "Physical Semantics",
    description: "Physical systems, observables, modeling assumptions, and regime-alignment interfaces.",
    available: false
  },
  empirical: {
    title: "Empirical Evidence",
    description: "Protocols, samples, observations, and statistical-evidence interfaces.",
    available: false
  }
};

const mappedAgentDetails = {
  "agent:graph-theoretic-nonstabilizerness": {
    title: "Graph-Theoretic Nonstabilizerness",
    identifier: "arXiv:2607.26154v1",
    role: "Target-paper package in the current Stabilizerness registry."
  },
  "agent:predicting-magic-from-very-few-measurements": {
    title: "Predicting Magic from Very Few Measurements",
    identifier: "arXiv:2602.18939v1",
    role: "Reduced-polytope source package."
  },
  "agent:resource-theory-of-stabilizer-computation": {
    title: "The Resource Theory of Stabilizer Computation",
    identifier: "arXiv:1307.7171v1",
    role: "Stabilizer-resource-theory source package."
  },
  "agent:robustness-of-magic": {
    title: "Application of a Resource Theory for Magic States to Fault-Tolerant Quantum Computing",
    identifier: "arXiv:1609.07488v2",
    role: "Robustness-of-magic source package."
  },
  "agent:stabilizer-codes-and-quantum-error-correction": {
    title: "Stabilizer Codes and Quantum Error Correction",
    identifier: "arXiv:quant-ph/9705052v1",
    role: "Stabilizer-formalism source package."
  }
};

let mathematicsContracts = [];
let contractMap = new Map();
let mathematicsEdges = [];
let incomingEdges = new Map();
let agentCatalog = new Map();
let ownerByInterface = new Map();
let dag = null;
let paperDag = null;
let activeProfile = "mathematics";
let selectedAgent = "agent:graph-theoretic-nonstabilizerness";
let selectedTarget = "claim:closed-form-rom";
let currentClosure = new Set();
let graphRendered = false;
let tooltipPinned = false;

const esc = value => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;").replaceAll('"', "&quot;");

function svgElement(name, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function ownerId(contract) {
  if (contract.paper_agent && contract.paper_agent !== "UNMAPPED") return contract.paper_agent;
  return `profile-agent:${contract.dag_node_id}`;
}

function sourceIdentifier(contract) {
  const source = contract.source_reference;
  if (typeof source === "object" && source?.paper_id) return source.paper_id;
  return contract.dag_node_id;
}

function buildAgentCatalog() {
  agentCatalog = new Map();
  ownerByInterface = new Map();
  mathematicsContracts.forEach(contract => {
    const owner = ownerId(contract);
    ownerByInterface.set(contract.dag_node_id, owner);
    if (agentCatalog.has(owner)) return;
    const mapped = mappedAgentDetails[owner];
    agentCatalog.set(owner, mapped ? { ...mapped } : {
      title: "External Mathematical Root",
      identifier: sourceIdentifier(contract),
      role: "Unmapped external root or foundation represented as a query-level Agent."
    });
  });
  [...agentCatalog.entries()]
    .sort((left, right) => left[1].title.localeCompare(right[1].title) || left[1].identifier.localeCompare(right[1].identifier))
    .forEach(([id], index) => {
      agentCatalog.get(id).code = `A${String(index + 1).padStart(2, "0")}`;
    });
}

function buildIncomingIndex() {
  incomingEdges = new Map();
  mathematicsEdges.forEach(edge => {
    if (!incomingEdges.has(edge.to)) incomingEdges.set(edge.to, []);
    incomingEdges.get(edge.to).push(edge);
  });
}

function validateMathematicsDag() {
  const importField = {
    definition_dependency: "definition_imports",
    scientific_claim_dependency: "theorem_imports",
    scope_dependency: "assumption_nodes"
  };
  const outgoing = new Map(mathematicsContracts.map(contract => [contract.dag_node_id, []]));
  const indegree = new Map(mathematicsContracts.map(contract => [contract.dag_node_id, 0]));
  const seenPairs = new Set();

  mathematicsEdges.forEach(edge => {
    const field = importField[edge.type];
    const target = contractMap.get(edge.to);
    const pair = `${edge.from}->${edge.to}`;
    if (!field || !target || !contractMap.has(edge.from)) {
      throw new Error(`Unsupported mathematical dependency edge: ${pair}`);
    }
    if (!target[field].includes(edge.from)) {
      throw new Error(`Dependency direction does not match the target contract import: ${pair}`);
    }
    if (!edge.reason?.trim()) {
      throw new Error(`Dependency edge lacks a recorded reason: ${pair}`);
    }
    if (edge.from === edge.to || seenPairs.has(pair)) {
      throw new Error(`Invalid self-loop or duplicate dependency: ${pair}`);
    }
    seenPairs.add(pair);
    outgoing.get(edge.from).push(edge.to);
    indegree.set(edge.to, indegree.get(edge.to) + 1);
  });

  const queue = [...indegree.entries()].filter(([, degree]) => degree === 0).map(([id]) => id);
  let visited = 0;
  while (queue.length) {
    const node = queue.shift();
    visited += 1;
    for (const target of outgoing.get(node)) {
      indegree.set(target, indegree.get(target) - 1);
      if (indegree.get(target) === 0) queue.push(target);
    }
  }
  if (visited !== mathematicsContracts.length) {
    throw new Error("The displayed mathematical dependency graph is not acyclic.");
  }
}

async function load() {
  try {
    if (!globalThis.d3?.sugiyama || !globalThis.d3?.graphConnect) {
      throw new Error("The vendored d3-dag library did not initialize.");
    }
    const [registryResponse, dagResponse, paperDagResponse] = await Promise.all([
      fetch(paths.contracts), fetch(paths.dag), fetch(paths.paperDag)
    ]);
    if (!registryResponse.ok || !dagResponse.ok || !paperDagResponse.ok) {
      throw new Error("One or more Registry graph files could not be loaded.");
    }
    const allContracts = (await registryResponse.json()).contracts;
    mathematicsContracts = allContracts
      .filter(contract => contract.interface_class !== "NON_MATHEMATICAL");
    contractMap = new Map(mathematicsContracts.map(contract => [contract.dag_node_id, contract]));
    dag = await dagResponse.json();
    paperDag = await paperDagResponse.json();
    mathematicsEdges = dag.edges.filter(edge =>
      contractMap.has(edge.from) && contractMap.has(edge.to)
    );
    buildAgentCatalog();
    buildIncomingIndex();
    validateMathematicsDag();
    bindProfiles();
    bindQueryControls();
    populateAgentSelect();
    selectInitialQuery();
    setProfile(activeProfile);
  } catch (error) {
    document.querySelector("main").innerHTML = `
      <section class="load-error"><b>Unable to load graph data</b><p>${esc(error.message)}</p>
      <p>Run a static server from the repository root, for example
      <code>python3 -m http.server 8000</code>, then reopen this page.</p></section>`;
  }
}

function bindProfiles() {
  document.querySelectorAll("#profileTabs button").forEach(button => {
    button.addEventListener("click", () => setProfile(button.dataset.profile));
  });
}

function bindQueryControls() {
  document.getElementById("targetAgentSelect").addEventListener("change", event => {
    closePinnedTooltip();
    selectedAgent = event.target.value;
    populateInterfaceSelect();
    selectedTarget = preferredTargetForAgent(selectedAgent);
    document.getElementById("queryInterfaceSelect").value = selectedTarget;
    applyQueryHighlight();
  });
  document.getElementById("queryInterfaceSelect").addEventListener("change", event => {
    closePinnedTooltip();
    selectedTarget = event.target.value;
    applyQueryHighlight();
  });
}

function populateAgentSelect() {
  const select = document.getElementById("targetAgentSelect");
  const agents = [...agentCatalog.entries()].sort((left, right) => {
    if (left[0] === selectedAgent) return -1;
    if (right[0] === selectedAgent) return 1;
    return left[1].title.localeCompare(right[1].title);
  });
  select.innerHTML = agents.map(([id, agent]) =>
    `<option value="${esc(id)}">${esc(agent.title)} | ${esc(agent.identifier)}</option>`
  ).join("");
  select.value = selectedAgent;
}

function interfacesForAgent(agentId) {
  return mathematicsContracts
    .filter(contract => ownerByInterface.get(contract.dag_node_id) === agentId)
    .sort((left, right) => left.dag_node_id.localeCompare(right.dag_node_id));
}

function populateInterfaceSelect() {
  const select = document.getElementById("queryInterfaceSelect");
  const interfaces = interfacesForAgent(selectedAgent);
  select.innerHTML = interfaces.map(contract =>
    `<option value="${esc(contract.dag_node_id)}">${esc(contract.dag_node_id)}</option>`
  ).join("");
}

function ancestorClosure(targetId) {
  const closure = new Set([targetId]);
  const queue = [targetId];
  while (queue.length) {
    const node = queue.shift();
    for (const edge of incomingEdges.get(node) || []) {
      if (!closure.has(edge.from)) {
        closure.add(edge.from);
        queue.push(edge.from);
      }
    }
  }
  return closure;
}

function preferredTargetForAgent(agentId) {
  const interfaces = interfacesForAgent(agentId);
  if (!interfaces.length) return "";
  if (agentId === "agent:graph-theoretic-nonstabilizerness" &&
      interfaces.some(contract => contract.dag_node_id === "claim:closed-form-rom")) {
    return "claim:closed-form-rom";
  }
  return interfaces
    .map(contract => ({
      id: contract.dag_node_id,
      size: ancestorClosure(contract.dag_node_id).size
    }))
    .sort((left, right) => right.size - left.size || left.id.localeCompare(right.id))[0].id;
}

function selectInitialQuery() {
  if (!agentCatalog.has(selectedAgent)) selectedAgent = agentCatalog.keys().next().value;
  document.getElementById("targetAgentSelect").value = selectedAgent;
  populateInterfaceSelect();
  if (!contractMap.has(selectedTarget) || ownerByInterface.get(selectedTarget) !== selectedAgent) {
    selectedTarget = preferredTargetForAgent(selectedAgent);
  }
  document.getElementById("queryInterfaceSelect").value = selectedTarget;
}

function setProfile(profileId) {
  const profile = profiles[profileId];
  if (!profile) return;
  activeProfile = profileId;
  closePinnedTooltip();
  document.getElementById("profileTitle").textContent = profile.title;
  document.getElementById("profileDescription").textContent = profile.description;
  document.querySelectorAll("#profileTabs button").forEach(button => {
    button.setAttribute("aria-selected", String(button.dataset.profile === profileId));
  });

  const svg = document.getElementById("dag");
  const empty = document.getElementById("emptyState");
  const queryBar = document.getElementById("queryBar");
  if (profile.available) {
    svg.hidden = false;
    empty.hidden = true;
    queryBar.hidden = false;
    if (!graphRendered) renderMathematicsGraph();
    applyQueryHighlight();
  } else {
    svg.hidden = true;
    empty.hidden = false;
    queryBar.hidden = true;
    document.getElementById("profileMeta").textContent = "0 registered nodes | 0 registered links";
  }
}

function renderMathematicsGraph() {
  const svg = document.getElementById("dag");
  const ownershipEdges = mathematicsContracts.map(contract => ({
    from: ownerByInterface.get(contract.dag_node_id),
    to: contract.dag_node_id,
    type: "layout_ownership"
  }));
  const layoutEdges = [...ownershipEdges, ...mathematicsEdges];
  const dependencyMap = new Map(mathematicsEdges.map(edge => [`${edge.from}->${edge.to}`, edge]));
  const graph = d3.graphConnect()(layoutEdges.map(edge => [edge.from, edge.to]));
  const layout = d3.sugiyama()
    .layering(d3.layeringSimplex())
    .decross(d3.decrossTwoLayer())
    .coord(d3.coordQuad())
    .nodeSize(node => agentCatalog.has(node.data) ? [72, 72] : [28, 28])
    .gap([18, 78]);
  const dimensions = layout(graph);
  const margin = { x: 92, y: 78 };
  const width = Math.max(1280, dimensions.height + margin.x * 2);
  const height = Math.max(720, dimensions.width + margin.y * 2);

  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.innerHTML = `
    <defs>
      <marker id="dependencyArrow" viewBox="0 0 10 10" markerWidth="9" markerHeight="9" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse">
        <path d="M1,1 L9,5 L1,9 L3.2,5 Z" fill="#8f9e96"></path>
      </marker>
      <marker id="activeDependencyArrow" viewBox="0 0 12 10" markerWidth="11" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse">
        <path d="M1,1 L11,5 L1,9 L3.4,5 Z" fill="#1f6b4f"></path>
      </marker>
      <filter id="nodeShadow" x="-80%" y="-80%" width="260%" height="280%">
        <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#17211c" flood-opacity="0.18"></feDropShadow>
      </filter>
    </defs>`;

  const underlayLayer = svgElement("g", { class: "link-underlay-layer" });
  const linkLayer = svgElement("g", { class: "link-layer" });
  for (const link of graph.links()) {
    const from = link.source.data;
    const to = link.target.data;
    const dependency = dependencyMap.get(`${from}->${to}`);
    if (!dependency) continue;
    const points = link.points.map(([x, y]) => ({ x: y + margin.x, y: x + margin.y }));
    const pathData = smoothPath(points);
    const underlay = svgElement("path", {
      d: pathData,
      class: "dependency-link-underlay"
    });
    const path = svgElement("path", {
      d: pathData,
      class: `dependency-link ${dependency.type}`,
      "marker-end": "url(#dependencyArrow)"
    });
    path.dataset.from = from;
    path.dataset.to = to;
    path.dataset.type = dependency.type;
    const title = svgElement("title");
    title.textContent = `${dependency.type}: ${from} -> ${to}. ${dependency.reason}`;
    path.appendChild(title);
    underlayLayer.appendChild(underlay);
    linkLayer.appendChild(path);
  }
  svg.appendChild(underlayLayer);
  svg.appendChild(linkLayer);

  const nodeLayer = svgElement("g", { class: "node-layer" });
  for (const node of graph.nodes()) {
    const x = node.y + margin.x;
    const y = node.x + margin.y;
    const agent = agentCatalog.get(node.data);
    if (agent) {
      nodeLayer.appendChild(renderAgentNode(node.data, agent, x, y));
    } else {
      const contract = contractMap.get(node.data);
      if (contract) nodeLayer.appendChild(renderInterfaceNode(contract, x, y));
    }
  }
  svg.appendChild(nodeLayer);

  graphRendered = true;
  document.getElementById("profileMeta").textContent =
    `${mathematicsContracts.length} interfaces | ${agentCatalog.size} agents | ${mathematicsEdges.length} dependencies`;
}

function smoothPath(points) {
  if (points.length < 2) return "";
  let path = `M${points[0].x},${points[0].y}`;
  for (let index = 1; index < points.length; index++) {
    const previous = points[index - 1];
    const current = points[index];
    const middle = (previous.x + current.x) / 2;
    path += ` C${middle},${previous.y} ${middle},${current.y} ${current.x},${current.y}`;
  }
  return path;
}

function agentVerificationStats(agentId) {
  const owned = mathematicsContracts
    .filter(contract => ownerByInterface.get(contract.dag_node_id) === agentId);
  const verified = owned
    .filter(contract => contract.lean_binding.status === "EXISTING_PROJECT_DECLARATIONS").length;
  const percentage = owned.length ? Math.round(100 * verified / owned.length) : 0;
  return { verified, total: owned.length, percentage };
}

function renderAgentNode(id, agent, x, y) {
  const verification = agentVerificationStats(id);
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const progress = circumference * verification.percentage / 100;
  const group = svgElement("g", {
    class: "agent-node agent-root",
    transform: `translate(${x},${y})`,
    tabindex: "0",
    role: "button",
    "aria-label": `Agent: ${agent.title}`
  });
  group.dataset.id = id;
  group.dataset.verifiedPercentage = verification.percentage;
  group.appendChild(svgElement("circle", { r: radius, class: "agent-progress-track" }));
  group.appendChild(svgElement("circle", {
    r: radius,
    class: "agent-progress-ring",
    "stroke-dasharray": `${progress} ${circumference}`,
    transform: "rotate(-90)"
  }));
  group.appendChild(svgElement("circle", { r: 36, class: "agent-outline" }));
  group.appendChild(svgElement("circle", { r: 32, class: "agent-disc", filter: "url(#nodeShadow)" }));
  const firstLine = svgElement("text", { x: 0, y: -3, class: "agent-label agent-label-first" });
  firstLine.textContent = "ROOT";
  const secondLine = svgElement("text", { x: 0, y: 11, class: "agent-label agent-label-small" });
  secondLine.textContent = "AGENT";
  const codeLine = svgElement("text", { x: 0, y: 24, class: "agent-code" });
  codeLine.textContent = agent.code;
  const progressLabel = svgElement("text", { x: 0, y: -47, class: "agent-progress-label" });
  progressLabel.textContent = `${verification.percentage}% verified`;
  group.appendChild(firstLine);
  group.appendChild(secondLine);
  group.appendChild(codeLine);
  group.appendChild(progressLabel);
  group.addEventListener("pointerenter", event => {
    applyMembershipHighlight(id);
    showAgentTooltip(id, agent, event);
  });
  group.addEventListener("pointermove", moveTooltip);
  group.addEventListener("pointerleave", () => {
    clearMembershipHighlight();
    hideTooltip();
  });
  group.addEventListener("focus", () => {
    applyMembershipHighlight(id);
    showAgentTooltipAtNode(id, agent, group);
  });
  group.addEventListener("blur", () => {
    clearMembershipHighlight();
    hideTooltip();
  });
  return group;
}

function renderInterfaceNode(contract, x, y) {
  const group = svgElement("g", {
    class: "interface-node",
    transform: `translate(${x},${y})`,
    tabindex: "0",
    role: "button",
    "aria-label": `${contract.dag_node_id}: ${statusLabels[contract.lean_binding.status]}`
  });
  const owner = ownerByInterface.get(contract.dag_node_id);
  const agent = agentCatalog.get(owner);
  group.dataset.id = contract.dag_node_id;
  group.dataset.owner = owner;
  group.dataset.status = contract.lean_binding.status;
  group.appendChild(svgElement("circle", { r: 20, class: "node-hit-area" }));
  group.appendChild(svgElement("circle", { r: 12.5, class: "membership-ring" }));
  group.appendChild(svgElement("circle", { r: 10.5, class: "interface-shell", filter: "url(#nodeShadow)" }));
  group.appendChild(svgElement("circle", { r: 7.5, class: "interface-dot" }));
  group.appendChild(svgElement("circle", { r: 14, class: "interface-focus" }));
  const ownerCode = svgElement("text", { x: 10, y: -10, class: "owner-code" });
  ownerCode.textContent = agent.code;
  group.appendChild(ownerCode);
  group.addEventListener("pointerenter", event => {
    applyMembershipHighlight(owner);
    showInterfaceTooltip(contract, event);
  });
  group.addEventListener("pointermove", moveTooltip);
  group.addEventListener("pointerleave", () => {
    clearMembershipHighlight();
    hideTooltip();
  });
  group.addEventListener("focus", () => {
    applyMembershipHighlight(owner);
    showInterfaceTooltipAtNode(contract, group);
  });
  group.addEventListener("blur", () => {
    clearMembershipHighlight();
    hideTooltip();
  });
  group.addEventListener("click", event => {
    event.stopPropagation();
    pinInterfaceTooltip(contract, group);
  });
  return group;
}

function applyMembershipHighlight(ownerId) {
  document.querySelectorAll("#dag .agent-node").forEach(node => {
    node.classList.toggle("membership-owner", node.dataset.id === ownerId);
  });
  document.querySelectorAll("#dag .interface-node").forEach(node => {
    node.classList.toggle("membership-related", node.dataset.owner === ownerId);
  });
}

function clearMembershipHighlight() {
  document.querySelectorAll("#dag .membership-owner, #dag .membership-related").forEach(node => {
    node.classList.remove("membership-owner", "membership-related");
  });
}

function applyQueryHighlight() {
  if (!graphRendered || !selectedTarget) return;
  currentClosure = ancestorClosure(selectedTarget);
  const activeOwners = new Set([...currentClosure].map(id => ownerByInterface.get(id)).filter(Boolean));

  document.querySelectorAll("#dag .interface-node").forEach(node => {
    const active = currentClosure.has(node.dataset.id);
    node.classList.toggle("query-active", active);
    node.classList.toggle("query-muted", !active);
    node.classList.toggle("query-target", node.dataset.id === selectedTarget);
  });

  const activeLinks = [];
  document.querySelectorAll("#dag .dependency-link").forEach(link => {
    const active = currentClosure.has(link.dataset.from) && currentClosure.has(link.dataset.to);
    link.classList.toggle("query-active", active);
    link.classList.toggle("query-muted", !active);
    link.setAttribute("marker-end", active
      ? "url(#activeDependencyArrow)"
      : "url(#dependencyArrow)");
    if (active) activeLinks.push(link);
  });
  activeLinks.forEach(link => link.parentNode.appendChild(link));

  document.querySelectorAll("#dag .agent-node").forEach(node => {
    const id = node.dataset.id;
    const target = id === selectedAgent;
    const active = activeOwners.has(id);
    node.classList.toggle("agent-target", target);
    node.classList.toggle("agent-root", !target);
    node.classList.toggle("query-active", active || target);
    node.classList.toggle("query-muted", !active && !target);
    node.querySelector(".agent-label-first").textContent = target ? "TARGET" : "ROOT";
  });

  const agent = agentCatalog.get(selectedAgent);
  document.getElementById("querySummary").textContent =
    `${agent?.title || selectedAgent} | ${selectedTarget} | ${currentClosure.size} interfaces in query closure`;
}

function listSection(title, items, emptyText) {
  if (!items?.length) return `<section><h4>${esc(title)}</h4><p>${esc(emptyText)}</p></section>`;
  return `<section><h4>${esc(title)}</h4><div class="tooltip-list">${items.map(item =>
    `<span>${esc(typeof item === "string" ? item : JSON.stringify(item))}</span>`
  ).join("")}</div></section>`;
}

function leanSourceSection(contract) {
  if (contract.lean_binding.status !== "EXISTING_PROJECT_DECLARATIONS") return "";
  const modules = [...new Set(contract.lean_binding.modules || [])];
  if (!modules.length) {
    throw new Error(`Verified claim lacks a Lean source module link: ${contract.dag_node_id}`);
  }
  const links = modules.map(module => {
    const href = encodeURI(`../../../${module}`);
    const label = module.split("/").pop();
    return `<a class="lean-source-link" href="${esc(href)}" target="_blank" rel="noopener">Open ${esc(label)}</a>`;
  }).join("");
  return `<section><h4>Lean source links</h4><div class="source-link-list">${links}</div></section>`;
}

function agentTooltipContent(id, agent) {
  const selected = id === selectedAgent;
  const paperNode = paperDag.nodes.find(node => node.id === id);
  const verification = agentVerificationStats(id);
  return `
    <div class="tooltip-head ${selected ? "target" : "root"}"><span>${selected ? "Target Agent" : "Root Agent"}</span><span>${esc(paperNode?.role || "registry owner")}</span></div>
    <h3>${esc(agent.title)}</h3>
    <section><h4>Membership code</h4><code>${esc(agent.code)} | ${verification.total} owned interface${verification.total === 1 ? "" : "s"}</code></section>
    <section><h4>Lean verification coverage</h4><code>${verification.verified} / ${verification.total} = ${verification.percentage}%</code></section>
    <section><h4>Identifier</h4><code>${esc(agent.identifier)}</code></section>
    <section><h4>Role in this view</h4><p>${esc(agent.role)}</p></section>
    <section><h4>Query state</h4><p>${selected ? "Selected as the current Target Agent." : "Available as a Root Agent or alternate Target Agent."}</p></section>`;
}

function interfaceTooltipContent(contract) {
  const owner = ownerByInterface.get(contract.dag_node_id);
  const agent = agentCatalog.get(owner);
  const allImports = [
    ...contract.assumption_nodes,
    ...contract.definition_imports,
    ...contract.theorem_imports,
    ...contract.data_imports
  ];
  const inClosure = currentClosure.has(contract.dag_node_id);
  const isTarget = contract.dag_node_id === selectedTarget;
  return `
    <div class="tooltip-head" data-status="${esc(contract.lean_binding.status)}">
      <span>${esc(statusLabels[contract.lean_binding.status])}</span><span>${isTarget ? "Query target" : inClosure ? "Highlighted route" : "Outside current route"}</span>
    </div>
    <h3>${esc(contract.dag_node_id)}</h3>
    <section><h4>Contained by Agent</h4><code>${esc(agent.code)} | ${esc(agent.title)} | ${esc(agent.identifier)}</code></section>
    <section><h4>Mathematical content</h4><p>${esc(contract.normalized_mathematical_statement || "No mathematical theorem is required for this node.")}</p></section>
    ${listSection("Registered imports", allImports, "No registered import is recorded.")}
    ${listSection("Existing Lean declarations", contract.lean_binding.existing_declarations, "No existing Lean declaration is mapped.")}
    ${leanSourceSection(contract)}
    ${listSection("Planned local delta", contract.lean_binding.planned_declarations, contract.lean_binding.gap || "No planned declaration is recorded.")}
    <section><h4>Source</h4><code>${esc(typeof contract.source_reference === "string" ? contract.source_reference : JSON.stringify(contract.source_reference))}</code></section>
    <p class="tooltip-policy">Every node retains its Registry status; query selection changes highlighting only. Click the node to pin this card and use its source links.</p>`;
}

function showAgentTooltip(id, agent, event) {
  showTooltip(agentTooltipContent(id, agent), event.clientX + 18, event.clientY + 18);
}

function showAgentTooltipAtNode(id, agent, node) {
  const rect = node.getBoundingClientRect();
  showTooltip(agentTooltipContent(id, agent), rect.right + 12, rect.top);
}

function showInterfaceTooltip(contract, event) {
  showTooltip(interfaceTooltipContent(contract), event.clientX + 18, event.clientY + 18);
}

function showInterfaceTooltipAtNode(contract, node) {
  const rect = node.getBoundingClientRect();
  showTooltip(interfaceTooltipContent(contract), rect.right + 12, rect.top);
}

function pinInterfaceTooltip(contract, node) {
  const tooltip = document.getElementById("tooltip");
  const rect = node.getBoundingClientRect();
  tooltipPinned = true;
  tooltip.classList.add("pinned");
  tooltip.innerHTML = `<button type="button" class="tooltip-close" aria-label="Close pinned details">Close</button>${interfaceTooltipContent(contract)}`;
  tooltip.hidden = false;
  tooltip.querySelector(".tooltip-close").addEventListener("click", closePinnedTooltip);
  positionTooltip(rect.right + 12, rect.top);
}

function closePinnedTooltip() {
  const tooltip = document.getElementById("tooltip");
  tooltipPinned = false;
  tooltip.classList.remove("pinned");
  tooltip.hidden = true;
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
  const margin = 14;
  const left = Math.min(x, window.innerWidth - tooltip.offsetWidth - margin);
  const top = Math.min(y, window.innerHeight - tooltip.offsetHeight - margin);
  tooltip.style.left = `${Math.max(margin, left)}px`;
  tooltip.style.top = `${Math.max(margin, top)}px`;
}

function hideTooltip() {
  if (!tooltipPinned) document.getElementById("tooltip").hidden = true;
}

load();
