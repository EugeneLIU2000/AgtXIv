(() => {
  "use strict";

  const DATA_URL = "data/graph-theoretic-scientific-claims.json";
  const SVG_NS = "http://www.w3.org/2000/svg";
  const NODE_TYPES = new Set([
    "paper", "scientific_claim_contribution", "facet", "scientific_claim_formal",
    "source_occurrence", "math_claim_ir", "mathematical_proposition_ir",
  ]);
  const EDGE_TYPES = new Set(["contains", "has_facet", "source_calibration", "formal_source", "provisional_navigation"]);
  const TYPE_LABELS = {
    paper: "Paper",
    scientific_claim_contribution: "Contribution ScientificClaim",
    facet: "Facet",
    scientific_claim_formal: "FORMAL_ATOMIC claim",
    source_occurrence: "Source occurrence",
    math_claim_ir: "MathClaimIR",
    mathematical_proposition_ir: "MathematicalPropositionIR",
  };
  const LEVELS = {
    paper: 0,
    scientific_claim_contribution: 1,
    facet: 2,
    scientific_claim_formal: 2,
    source_occurrence: 2,
    math_claim_ir: 3,
    mathematical_proposition_ir: 3,
  };
  const READABLE_SCALE_FLOORS = { desktop: .46, tablet: .38, mobile: .32, narrow: .28 };
  const DIMENSIONS = {
    paper: [220, 82],
    scientific_claim_contribution: [270, 88],
    facet: [225, 76],
    scientific_claim_formal: [230, 70],
    source_occurrence: [230, 66],
    math_claim_ir: [240, 74],
    mathematical_proposition_ir: [250, 74],
  };
  const state = {
    data: null,
    nodes: new Map(),
    edges: [],
    expanded: new Set(),
    pinnedId: null,
    visibleIds: [],
    positions: new Map(),
    bounds: null,
    transform: { x: 0, y: 0, scale: 1 },
    preferReadableFit: false,
    dragging: null,
    tooltipId: null,
    suppressTooltipFocusId: null,
  };
  const byId = (id) => document.getElementById(id);

  function htmlElement(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function svgElement(tag, attributes = {}) {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, String(value)));
    return node;
  }

  function isSafeUrl(value) {
    const url = value.trim();
    if (url.startsWith("//")) return false;
    if (/^(https?:|mailto:)/i.test(url)) return true;
    return /^(#|\/(?!\/)|\.\/|\.\.\/)/.test(url);
  }

  function appendInline(parent, source) {
    const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
    let offset = 0;
    for (const match of source.matchAll(pattern)) {
      if (match.index > offset) parent.append(document.createTextNode(source.slice(offset, match.index)));
      const token = match[0];
      if (token.startsWith("`")) {
        parent.append(htmlElement("code", "", token.slice(1, -1)));
      } else if (token.startsWith("**")) {
        const strong = document.createElement("strong");
        appendInline(strong, token.slice(2, -2));
        parent.append(strong);
      } else if (token.startsWith("*")) {
        const emphasis = document.createElement("em");
        appendInline(emphasis, token.slice(1, -1));
        parent.append(emphasis);
      } else {
        const parts = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
        if (parts && isSafeUrl(parts[2])) {
          const link = htmlElement("a", "", parts[1]);
          link.href = parts[2];
          link.rel = "noopener noreferrer";
          if (/^https?:/i.test(parts[2])) link.target = "_blank";
          parent.append(link);
        } else if (parts) {
          parent.append(document.createTextNode(`${parts[1]} [unsafe link removed]`));
        }
      }
      offset = match.index + token.length;
    }
    if (offset < source.length) parent.append(document.createTextNode(source.slice(offset)));
  }

  function renderMarkdown(markdown) {
    const fragment = document.createDocumentFragment();
    const lines = String(markdown).replace(/\r\n?/g, "\n").split("\n");
    let index = 0;
    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) {
        index += 1;
        continue;
      }
      const fence = /^```([a-z0-9-]*)\s*$/i.exec(line);
      if (fence) {
        index += 1;
        const codeLines = [];
        while (index < lines.length && lines[index] !== "```") codeLines.push(lines[index++]);
        if (index < lines.length) index += 1;
        const pre = document.createElement("pre");
        const code = htmlElement("code", fence[1] ? `language-${fence[1]}` : "", codeLines.join("\n"));
        pre.append(code);
        fragment.append(pre);
        continue;
      }
      const heading = /^(#{1,6})\s+(.+)$/.exec(line);
      if (heading) {
        const level = Math.min(heading[1].length, 6);
        const node = document.createElement(`h${level}`);
        appendInline(node, heading[2]);
        fragment.append(node);
        index += 1;
        continue;
      }
      if (/^-\s+/.test(line)) {
        const list = document.createElement("ul");
        while (index < lines.length && /^-\s+/.test(lines[index])) {
          const item = document.createElement("li");
          appendInline(item, lines[index].replace(/^-\s+/, ""));
          list.append(item);
          index += 1;
        }
        fragment.append(list);
        continue;
      }
      const paragraphLines = [];
      while (index < lines.length && lines[index].trim() && !/^```/.test(lines[index]) && !/^#{1,6}\s+/.test(lines[index]) && !/^-\s+/.test(lines[index])) {
        paragraphLines.push(lines[index++]);
      }
      const paragraph = document.createElement("p");
      appendInline(paragraph, paragraphLines.join(" "));
      fragment.append(paragraph);
    }
    return fragment;
  }

  window.ScientificClaimDemo = Object.freeze({ isSafeUrl, renderMarkdown });

  function requireData(condition, message) {
    if (!condition) throw new Error(message);
  }

  function validateGraphData(data) {
    requireData(data?.schema === "agtxiv.scientific-claim-demo/2.0.0", "The frozen graph payload has the wrong schema.");
    const graph = data.graph;
    requireData(graph && Array.isArray(graph.nodes) && Array.isArray(graph.edges), "The frozen graph payload is missing nodes or edges.");
    const ids = new Set();
    graph.nodes.forEach((node) => {
      requireData(typeof node.id === "string" && !ids.has(node.id), `Duplicate or missing graph node ID: ${node.id}.`);
      ids.add(node.id);
      requireData(NODE_TYPES.has(node.type), `Graph node ${node.id} has an unsupported type.`);
      requireData(typeof node.label === "string" && node.label.trim(), `Graph node ${node.id} has no accessible label.`);
      requireData(typeof node.detail_markdown === "string" && node.detail_markdown.startsWith("## "), `Graph node ${node.id} has no Markdown detail.`);
    });
    const endpointTypes = {
      contains: [["paper"], ["scientific_claim_contribution"]],
      has_facet: [["scientific_claim_contribution"], ["facet"]],
      source_calibration: [["scientific_claim_contribution"], ["source_occurrence"]],
      formal_source: [["scientific_claim_contribution"], ["scientific_claim_formal"]],
      provisional_navigation: [["facet"], ["math_claim_ir", "mathematical_proposition_ir"]],
    };
    const edgeIds = new Set();
    graph.edges.forEach((edge) => {
      requireData(typeof edge.id === "string" && !edgeIds.has(edge.id), `Duplicate or missing graph edge ID: ${edge.id}.`);
      edgeIds.add(edge.id);
      requireData(EDGE_TYPES.has(edge.type), `Graph edge ${edge.id} has an unsupported type.`);
      requireData(ids.has(edge.source) && ids.has(edge.target), `Graph edge ${edge.id} has a dangling endpoint.`);
      const source = graph.nodes.find((node) => node.id === edge.source);
      const target = graph.nodes.find((node) => node.id === edge.target);
      const [sourceTypes, targetTypes] = endpointTypes[edge.type];
      requireData(sourceTypes.includes(source.type) && targetTypes.includes(target.type), `Graph edge ${edge.id} has invalid typed endpoints.`);
      if (edge.type === "provisional_navigation") {
        requireData(edge.label.startsWith("PROVISIONAL NAVIGATION · "), `Graph edge ${edge.id} has misleading support wording.`);
      }
    });
    const initialTypes = graph.initial_node_ids.map((id) => graph.nodes.find((node) => node.id === id)?.type);
    requireData(initialTypes.length === 3 && initialTypes[0] === "paper" && initialTypes.slice(1).every((type) => type === "scientific_claim_contribution"), "Initial graph must show one paper and two contribution-role ScientificClaims.");
  }

  function visibleGraph() {
    const visible = new Set(state.data.graph.initial_node_ids);
    let changed = true;
    while (changed) {
      changed = false;
      state.edges.forEach((edge) => {
        if (visible.has(edge.source) && state.expanded.has(edge.expand_from) && !visible.has(edge.target)) {
          visible.add(edge.target);
          changed = true;
        }
      });
    }
    const nodes = state.data.graph.nodes.filter((node) => visible.has(node.id));
    const edges = state.edges.filter((edge) => visible.has(edge.source) && visible.has(edge.target) && state.expanded.has(edge.expand_from));
    return { nodes, edges };
  }

  function layoutGraph(nodes) {
    const layers = new Map();
    nodes.forEach((node) => {
      const level = LEVELS[node.type];
      if (!layers.has(level)) layers.set(level, []);
      layers.get(level).push(node);
    });
    const xPositions = [40, 350, 690, 1030];
    const gap = 28;
    const layerHeights = [];
    for (let level = 0; level <= 3; level += 1) {
      const layer = layers.get(level) || [];
      const height = layer.reduce((total, node) => total + DIMENSIONS[node.type][1], 0) + Math.max(0, layer.length - 1) * gap;
      layerHeights.push(height);
    }
    const totalHeight = Math.max(220, ...layerHeights) + 80;
    const positions = new Map();
    for (let level = 0; level <= 3; level += 1) {
      const layer = layers.get(level) || [];
      let y = (totalHeight - layerHeights[level]) / 2;
      layer.forEach((node) => {
        const [width, height] = DIMENSIONS[node.type];
        positions.set(node.id, { x: xPositions[level], y, width, height, level });
        y += height + gap;
      });
    }
    const populated = [...positions.values()];
    const right = Math.max(...populated.map((position) => position.x + position.width));
    const bottom = Math.max(...populated.map((position) => position.y + position.height));
    state.positions = positions;
    state.bounds = { x: 10, y: 10, width: right, height: bottom + 30 };
  }

  function shortId(identifier, limit = 31) {
    const suffix = identifier.rsplit ? identifier.rsplit(":", 1)[1] : identifier.split(":").pop();
    const value = suffix || identifier;
    return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
  }

  function wrapLabel(label, maxLength = 28) {
    const words = label.split(/\s+/);
    const lines = [""];
    words.forEach((word) => {
      const current = lines[lines.length - 1];
      if (current && `${current} ${word}`.length > maxLength && lines.length < 2) lines.push(word);
      else lines[lines.length - 1] = current ? `${current} ${word}` : word;
    });
    if (lines[lines.length - 1].length > maxLength + 8) lines[lines.length - 1] = `${lines[lines.length - 1].slice(0, maxLength + 7)}…`;
    return lines;
  }

  function edgePath(source, target) {
    const x1 = source.x + source.width;
    const y1 = source.y + source.height / 2;
    const x2 = target.x;
    const y2 = target.y + target.height / 2;
    const curve = Math.max(48, (x2 - x1) * .48);
    return `M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}`;
  }

  function edgeLabel(edge) {
    if (edge.type === "provisional_navigation") return edge.label.replace("PROVISIONAL NAVIGATION · ", "NAV · ");
    if (edge.type === "source_calibration") return edge.label.split(" · ")[0];
    if (edge.type === "formal_source") return "FORMAL_ATOMIC";
    return "";
  }

  function renderEdge(edge) {
    const source = state.positions.get(edge.source);
    const target = state.positions.get(edge.target);
    const group = svgElement("g", { class: `edge-group ${edge.type}` });
    const path = svgElement("path", { class: `graph-edge ${edge.type}`, d: edgePath(source, target), "data-edge-id": edge.id });
    group.append(path);
    const label = edgeLabel(edge);
    if (label) {
      const x = (source.x + source.width + target.x) / 2;
      const y = (source.y + source.height / 2 + target.y + target.height / 2) / 2 - 5;
      const text = svgElement("text", { class: `edge-label ${edge.type}`, x, y, "text-anchor": "middle" });
      text.textContent = label;
      group.append(text);
    }
    return group;
  }

  function nodeAriaLabel(node) {
    const expansion = node.expandable ? (state.expanded.has(node.id) ? "expanded" : "collapsed") : "leaf";
    return `${TYPE_LABELS[node.type]}: ${node.label}; ${expansion}. Press Enter or Space to pin details${node.expandable ? " and toggle children" : ""}.`;
  }

  function renderNode(node) {
    const position = state.positions.get(node.id);
    const group = svgElement("g", {
      class: `graph-node ${node.type}${state.pinnedId === node.id ? " is-pinned" : ""}`,
      transform: `translate(${position.x} ${position.y})`,
      tabindex: "0",
      role: "button",
      "aria-label": nodeAriaLabel(node),
      ...(node.expandable ? { "aria-expanded": state.expanded.has(node.id) } : {}),
      "data-node-id": node.id,
      "data-node-type": node.type,
    });
    const radius = node.type === "source_occurrence" ? position.height / 2 : node.type === "scientific_claim_formal" ? 4 : 11;
    group.append(svgElement("rect", { class: "node-shape", width: position.width, height: position.height, rx: radius, ry: radius }));
    const typeText = svgElement("text", { class: "node-type", x: 14, y: 18 });
    typeText.textContent = TYPE_LABELS[node.type];
    group.append(typeText);
    wrapLabel(node.label, node.type === "scientific_claim_contribution" ? 34 : 28).forEach((line, index) => {
      const text = svgElement("text", { class: "node-label", x: 14, y: 39 + index * 14 });
      text.textContent = line;
      group.append(text);
    });
    const idText = svgElement("text", { class: "node-id", x: 14, y: position.height - 9 });
    idText.textContent = shortId(node.id);
    group.append(idText);
    if (node.expandable) {
      const indicator = svgElement("text", { class: "expand-indicator", x: position.width - 16, y: 20, "text-anchor": "middle" });
      indicator.textContent = state.expanded.has(node.id) ? "−" : "+";
      group.append(indicator);
    }
    group.addEventListener("mouseenter", () => showTooltip(node, group));
    group.addEventListener("mouseleave", () => {
      if (document.activeElement !== group) hideTooltip();
    });
    group.addEventListener("focus", () => {
      if (state.suppressTooltipFocusId === node.id) state.suppressTooltipFocusId = null;
      else showTooltip(node, group);
      updateSelectionStatus(node);
    });
    group.addEventListener("blur", hideTooltip);
    group.addEventListener("click", (event) => {
      event.stopPropagation();
      activateNode(node.id, { focusAfter: true });
    });
    group.addEventListener("keydown", (event) => handleNodeKeydown(event, node));
    return group;
  }

  function renderGraph(options = {}) {
    const { fit = false, readableFit = false, focusId = null } = options;
    const graph = visibleGraph();
    state.visibleIds = graph.nodes.map((node) => node.id);
    layoutGraph(graph.nodes);
    byId("edgeLayer").replaceChildren(...graph.edges.map(renderEdge));
    byId("nodeLayer").replaceChildren(...graph.nodes.map(renderNode));
    byId("graphEmpty").hidden = graph.nodes.length > 0;
    applyTransform();
    if (fit) requestAnimationFrame(fitGraph);
    else if (readableFit) requestAnimationFrame(fitGraphReadably);
    if (focusId && state.visibleIds.includes(focusId)) {
      requestAnimationFrame(() => document.querySelector(`[data-node-id="${CSS.escape(focusId)}"]`)?.focus());
    }
    updateExpandedSummary();
  }

  function descendantsOf(nodeId) {
    const descendants = new Set();
    const queue = [nodeId];
    while (queue.length) {
      const source = queue.shift();
      state.edges.filter((edge) => edge.source === source).forEach((edge) => {
        if (!descendants.has(edge.target)) {
          descendants.add(edge.target);
          queue.push(edge.target);
        }
      });
    }
    return descendants;
  }

  function activateNode(nodeId, options = {}) {
    const node = state.nodes.get(nodeId);
    if (!node) return;
    hideTooltip();
    state.suppressTooltipFocusId = options.focusAfter ? nodeId : null;
    state.pinnedId = nodeId;
    pinDetail(node);
    if (node.expandable) {
      if (state.expanded.has(nodeId)) {
        state.expanded.delete(nodeId);
        descendantsOf(nodeId).forEach((id) => state.expanded.delete(id));
      } else {
        state.expanded.add(nodeId);
      }
      renderGraph({ readableFit: true, focusId: options.focusAfter ? nodeId : null });
      const navigationHint = state.expanded.has(nodeId) ? " Pan to inspect branches, or use Fit graph for an all-in-view overview." : "";
      byId("graphLiveStatus").textContent = `${node.label} is ${state.expanded.has(nodeId) ? "expanded" : "collapsed"}; ${state.visibleIds.length} nodes are visible.${navigationHint}`;
    } else {
      renderGraph({ focusId: options.focusAfter ? nodeId : null });
      byId("graphLiveStatus").textContent = `${node.label} detail is pinned; ${state.visibleIds.length} nodes are visible.`;
    }
    updateSelectionStatus(node);
  }

  function handleNodeKeydown(event, node) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activateNode(node.id, { focusAfter: true });
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      clearSelection();
      return;
    }
    const directions = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    if (!directions[event.key]) return;
    event.preventDefault();
    const current = state.positions.get(node.id);
    const [dx, dy] = directions[event.key];
    const candidates = state.visibleIds.filter((id) => id !== node.id).map((id) => ({ id, position: state.positions.get(id) })).filter(({ position }) => {
      const horizontal = position.x - current.x;
      const vertical = position.y - current.y;
      return dx ? Math.sign(horizontal) === dx : Math.sign(vertical) === dy;
    });
    candidates.sort((left, right) => {
      const score = ({ position }) => Math.abs(position.x - current.x) * (dx ? 1 : 2) + Math.abs(position.y - current.y) * (dy ? 1 : 2);
      return score(left) - score(right);
    });
    if (candidates[0]) document.querySelector(`[data-node-id="${CSS.escape(candidates[0].id)}"]`)?.focus();
  }

  function incomingParent(nodeId) {
    const edge = state.edges.find((candidate) => candidate.target === nodeId && state.visibleIds.includes(candidate.source));
    return edge?.source || null;
  }

  function breadcrumbFor(node) {
    const labels = [node.label];
    let parentId = incomingParent(node.id);
    const visited = new Set([node.id]);
    while (parentId && !visited.has(parentId)) {
      visited.add(parentId);
      labels.unshift(state.nodes.get(parentId)?.label || parentId);
      parentId = incomingParent(parentId);
    }
    return labels.join(" › ");
  }

  function updateSelectionStatus(node) {
    byId("breadcrumb").textContent = breadcrumbFor(node);
  }

  function updateExpandedSummary() {
    const expanded = [...state.expanded].filter((id) => state.nodes.get(id)?.expandable);
    if (!state.pinnedId) byId("breadcrumb").textContent = "Paper › contribution-role ScientificClaims";
    byId("graphLiveStatus").dataset.expandedCount = String(expanded.length);
  }

  function pinDetail(node) {
    byId("detailTitle").textContent = node.label;
    const body = byId("pinnedDetail");
    body.replaceChildren(renderMarkdown(node.detail_markdown));
    byId("unpinButton").hidden = false;
    document.querySelectorAll(".graph-node").forEach((element) => element.classList.toggle("is-pinned", element.dataset.nodeId === node.id));
  }

  function clearSelection() {
    hideTooltip();
    state.pinnedId = null;
    byId("detailTitle").textContent = "Select a graph node";
    byId("pinnedDetail").replaceChildren(htmlElement("p", "", "Click or press Enter/Space on a node to pin its rendered detail here. Hovering or keyboard focus opens the same detail in a floating card."));
    byId("unpinButton").hidden = true;
    byId("breadcrumb").textContent = "Paper › contribution-role ScientificClaims";
    document.querySelectorAll(".graph-node").forEach((element) => element.classList.remove("is-pinned"));
    byId("graphLiveStatus").textContent = "Floating and pinned details closed.";
  }

  function showTooltip(node, anchor) {
    const tooltip = byId("nodeTooltip");
    tooltip.replaceChildren(renderMarkdown(node.detail_markdown));
    tooltip.hidden = false;
    state.tooltipId = node.id;
    const anchorBox = anchor.getBoundingClientRect();
    const tooltipBox = tooltip.getBoundingClientRect();
    const margin = 12;
    let left = anchorBox.right + margin;
    if (left + tooltipBox.width > window.innerWidth - margin) left = anchorBox.left - tooltipBox.width - margin;
    left = Math.max(margin, Math.min(left, window.innerWidth - tooltipBox.width - margin));
    let top = anchorBox.top;
    if (top + tooltipBox.height > window.innerHeight - margin) top = window.innerHeight - tooltipBox.height - margin;
    top = Math.max(margin, top);
    if (top < anchorBox.bottom && top + tooltipBox.height > anchorBox.top && left < anchorBox.right && left + tooltipBox.width > anchorBox.left) {
      top = anchorBox.bottom + margin;
      if (top + tooltipBox.height > window.innerHeight - margin) top = Math.max(margin, anchorBox.top - tooltipBox.height - margin);
    }
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function hideTooltip() {
    const tooltip = byId("nodeTooltip");
    tooltip.hidden = true;
    tooltip.replaceChildren();
    state.tooltipId = null;
  }

  function applyTransform() {
    byId("claimGraphSvg").dataset.scale = String(state.transform.scale);
    byId("viewportGroup").setAttribute("transform", `translate(${state.transform.x} ${state.transform.y}) scale(${state.transform.scale})`);
  }

  function fittedScale(width, height) {
    const padding = 36;
    return Math.max(.16, Math.min(1.15, (width - padding * 2) / state.bounds.width, (height - padding * 2) / state.bounds.height));
  }

  function centerGraphAtScale(width, height, scale) {
    state.transform.scale = scale;
    state.transform.x = (width - state.bounds.width * scale) / 2 - state.bounds.x * scale;
    state.transform.y = (height - state.bounds.height * scale) / 2 - state.bounds.y * scale;
    applyTransform();
  }

  function readableScaleFloor(width) {
    if (width < 360) return READABLE_SCALE_FLOORS.narrow;
    if (width < 640) return READABLE_SCALE_FLOORS.mobile;
    if (width < 900) return READABLE_SCALE_FLOORS.tablet;
    return READABLE_SCALE_FLOORS.desktop;
  }

  function fitGraph() {
    if (!state.bounds) return;
    state.preferReadableFit = false;
    const svg = byId("claimGraphSvg");
    centerGraphAtScale(svg.clientWidth, svg.clientHeight, fittedScale(svg.clientWidth, svg.clientHeight));
  }

  function fitGraphReadably() {
    if (!state.bounds) return;
    state.preferReadableFit = true;
    const svg = byId("claimGraphSvg");
    const scale = Math.max(fittedScale(svg.clientWidth, svg.clientHeight), readableScaleFloor(svg.clientWidth));
    centerGraphAtScale(svg.clientWidth, svg.clientHeight, scale);
  }

  function zoomAt(factor, clientX, clientY) {
    const svgBox = byId("claimGraphSvg").getBoundingClientRect();
    const x = clientX - svgBox.left;
    const y = clientY - svgBox.top;
    const oldScale = state.transform.scale;
    const newScale = Math.max(.15, Math.min(2.5, oldScale * factor));
    const graphX = (x - state.transform.x) / oldScale;
    const graphY = (y - state.transform.y) / oldScale;
    state.transform.x = x - graphX * newScale;
    state.transform.y = y - graphY * newScale;
    state.transform.scale = newScale;
    applyTransform();
  }

  function wireGraphControls() {
    byId("fitButton").addEventListener("click", fitGraph);
    byId("zoomInButton").addEventListener("click", () => {
      const box = byId("claimGraphSvg").getBoundingClientRect();
      zoomAt(1.25, box.left + box.width / 2, box.top + box.height / 2);
    });
    byId("zoomOutButton").addEventListener("click", () => {
      const box = byId("claimGraphSvg").getBoundingClientRect();
      zoomAt(.8, box.left + box.width / 2, box.top + box.height / 2);
    });
    byId("expandButton").addEventListener("click", () => {
      state.data.graph.nodes.filter((node) => node.expandable).forEach((node) => state.expanded.add(node.id));
      renderGraph({ readableFit: true });
      byId("graphLiveStatus").textContent = `All expandable branches opened at a readable scale; ${state.visibleIds.length} nodes are visible. Pan to inspect branches, or use Fit graph for an all-in-view overview.`;
    });
    byId("collapseButton").addEventListener("click", () => {
      state.expanded = new Set(state.data.graph.initial_expanded_node_ids);
      renderGraph({ fit: true });
      byId("graphLiveStatus").textContent = "Graph collapsed to the paper and two contribution-role ScientificClaims.";
    });
    byId("resetButton").addEventListener("click", () => {
      state.expanded = new Set(state.data.graph.initial_expanded_node_ids);
      clearSelection();
      renderGraph({ fit: true });
      byId("graphLiveStatus").textContent = "Graph expansion, selection, pan, and zoom reset.";
    });
    byId("unpinButton").addEventListener("click", clearSelection);

    const stage = byId("graphStage");
    stage.addEventListener("wheel", (event) => {
      event.preventDefault();
      zoomAt(event.deltaY < 0 ? 1.12 : .89, event.clientX, event.clientY);
    }, { passive: false });
    stage.addEventListener("pointerdown", (event) => {
      if (event.target.closest?.(".graph-node")) return;
      state.dragging = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, startX: state.transform.x, startY: state.transform.y };
      stage.setPointerCapture(event.pointerId);
      stage.classList.add("is-panning");
    });
    stage.addEventListener("pointermove", (event) => {
      if (!state.dragging || state.dragging.pointerId !== event.pointerId) return;
      state.transform.x = state.dragging.startX + event.clientX - state.dragging.x;
      state.transform.y = state.dragging.startY + event.clientY - state.dragging.y;
      applyTransform();
    });
    const endPan = (event) => {
      if (!state.dragging || state.dragging.pointerId !== event.pointerId) return;
      state.dragging = null;
      stage.classList.remove("is-panning");
    };
    stage.addEventListener("pointerup", endPan);
    stage.addEventListener("pointercancel", endPan);
    window.addEventListener("resize", () => {
      if (state.preferReadableFit) fitGraphReadably();
      else fitGraph();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && (state.tooltipId || state.pinnedId)) {
        event.preventDefault();
        clearSelection();
      }
    });
  }

  function setLoading() {
    byId("claimGraph").setAttribute("aria-busy", "true");
    byId("loadStatus").hidden = false;
    byId("loadError").hidden = true;
    byId("graphApp").hidden = true;
    byId("retryButton").disabled = true;
  }

  function finishLoading() {
    byId("claimGraph").removeAttribute("aria-busy");
    byId("loadStatus").hidden = true;
    byId("retryButton").disabled = false;
  }

  function showLoadError(error) {
    finishLoading();
    byId("loadErrorMessage").textContent = `${error.message} Serve the repository root with the preview command in README.md, then retry.`;
    byId("loadError").hidden = false;
  }

  async function initialize() {
    setLoading();
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`The frozen graph request failed with HTTP ${response.status}.`);
      const data = await response.json();
      validateGraphData(data);
      state.data = data;
      state.nodes = new Map(data.graph.nodes.map((node) => [node.id, node]));
      state.edges = data.graph.edges;
      state.expanded = new Set(data.graph.initial_expanded_node_ids);
      state.pinnedId = null;
      byId("paperTitle").textContent = data.paper.title;
      byId("paperAuthors").textContent = data.paper.authors.join(" · ");
      byId("graphApp").hidden = false;
      finishLoading();
      renderGraph({ fit: true });
    } catch (error) {
      showLoadError(error instanceof Error ? error : new Error("The frozen graph could not be loaded."));
    }
  }

  byId("retryButton").addEventListener("click", initialize);
  wireGraphControls();
  initialize();
})();
