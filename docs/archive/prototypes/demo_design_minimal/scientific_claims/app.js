(() => {
  "use strict";

  const DATA_URL = "data/graph-theoretic-scientific-claims.json";
  const SVG_NS = "http://www.w3.org/2000/svg";
  const NODE_TYPES = new Set(["paper", "scientific_claim", "math_claim_ir", "oracle_candidate"]);
  const EDGE_TYPES = new Set(["contains", "claim_navigation", "normalizes_identity", "oracle_entry", "oracle_candidate_dependency"]);
  const CLAIM_TYPES = new Set(["contribution", "definition", "lemma", "proposition", "theorem", "result", "assumption", "convention", "referenced"]);
  const TYPE_LABELS = { paper: "Paper", scientific_claim: "Source-faithful ScientificClaim", math_claim_ir: "Reorganized MathClaimIR", oracle_candidate: "Unaccepted Oracle candidate" };
  const LEVELS = { paper: 0, contribution: 1, scientific_claim: 2, math_claim_ir: 3 };
  const READABLE_SCALE_FLOORS = { desktop: .5, tablet: .42, mobile: .34, narrow: .3 };
  const NODE_METRICS = {
    paper: { radius: 34, hitRadius: 44, footprint: 92, labelWidth: 190 },
    contribution: { radius: 26, hitRadius: 36, footprint: 84, labelWidth: 170 },
    scientific_claim: { radius: 20, hitRadius: 30, footprint: 74, labelWidth: 154 },
    math_claim_ir: { radius: 20, hitRadius: 30, footprint: 74, labelWidth: 154 },
    oracle_candidate: { radius: 17, hitRadius: 27, footprint: 68, labelWidth: 142 },
  };
  const state = {
    data: null, nodes: new Map(), edges: [], expanded: new Set(), facetFilter: null,
    pinnedId: null, visibleIds: [], positions: new Map(), bounds: null,
    transform: { x: 0, y: 0, scale: 1 }, preferReadableFit: false,
    dragging: null, tooltipId: null, highlightId: null, suppressTooltipFocusId: null,
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

  function appendStyledText(parent, source) {
    const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
    let offset = 0;
    for (const match of source.matchAll(pattern)) {
      if (match.index > offset) parent.append(document.createTextNode(source.slice(offset, match.index)));
      const token = match[0];
      if (token.startsWith("`")) parent.append(htmlElement("code", "", token.slice(1, -1)));
      else if (token.startsWith("**")) {
        const strong = document.createElement("strong");
        appendStyledText(strong, token.slice(2, -2));
        parent.append(strong);
      } else if (token.startsWith("*")) {
        const emphasis = document.createElement("em");
        appendStyledText(emphasis, token.slice(1, -1));
        parent.append(emphasis);
      } else {
        const parts = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
        if (parts && isSafeUrl(parts[2])) {
          const link = htmlElement("a", "", parts[1]);
          link.href = parts[2];
          link.rel = "noopener noreferrer";
          if (/^https?:/i.test(parts[2])) link.target = "_blank";
          parent.append(link);
        } else if (parts) parent.append(document.createTextNode(`${parts[1]} [unsafe link removed]`));
      }
      offset = match.index + token.length;
    }
    if (offset < source.length) parent.append(document.createTextNode(source.slice(offset)));
  }

  function findInlineMath(source, offset) {
    for (let index = offset; index < source.length; index += 1) {
      if (source[index] === "\\" && source[index + 1] === "(") {
        const end = source.indexOf("\\)", index + 2);
        if (end >= 0) return { start: index, end: end + 2, raw: source.slice(index, end + 2), tex: source.slice(index + 2, end) };
      }
      if (source[index] === "$" && source[index - 1] !== "\\" && source[index + 1] !== "$") {
        for (let end = index + 1; end < source.length; end += 1) {
          if (source[end] === "$" && source[end - 1] !== "\\") return { start: index, end: end + 1, raw: source.slice(index, end + 1), tex: source.slice(index + 1, end) };
        }
      }
    }
    return null;
  }

  function appendInline(parent, source) {
    let offset = 0;
    while (offset < source.length) {
      const math = findInlineMath(source, offset);
      if (!math) {
        appendStyledText(parent, source.slice(offset));
        break;
      }
      appendStyledText(parent, source.slice(offset, math.start));
      const formula = htmlElement("span", "math-source math-inline", math.raw);
      formula.dataset.texSource = math.tex;
      formula.setAttribute("aria-label", `Mathematical formula: ${math.tex}`);
      parent.append(formula);
      offset = math.end;
    }
  }

  function mathBlock(tex, raw = `\\[${tex}\\]`) {
    const block = htmlElement("div", "math-source math-display", raw);
    block.dataset.texSource = tex;
    block.setAttribute("role", "math");
    block.setAttribute("aria-label", `Mathematical formula: ${tex}`);
    return block;
  }

  function renderMarkdown(markdown) {
    const fragment = document.createDocumentFragment();
    const lines = String(markdown).replace(/\r\n?/g, "\n").split("\n");
    let index = 0;
    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) { index += 1; continue; }
      const fence = /^```([a-z0-9-]*)\s*$/i.exec(line);
      if (fence) {
        index += 1;
        const codeLines = [];
        while (index < lines.length && lines[index] !== "```") codeLines.push(lines[index++]);
        if (index < lines.length) index += 1;
        const source = codeLines.join("\n");
        if (fence[1].toLowerCase() === "latex") {
          const figure = htmlElement("figure", "math-figure");
          figure.append(mathBlock(source));
          const disclosure = document.createElement("details");
          disclosure.append(htmlElement("summary", "", "Copy TeX source"));
          const pre = document.createElement("pre");
          pre.append(htmlElement("code", "language-latex", source));
          disclosure.append(pre);
          figure.append(disclosure);
          fragment.append(figure);
        } else {
          const pre = document.createElement("pre");
          pre.append(htmlElement("code", fence[1] ? `language-${fence[1]}` : "", source));
          fragment.append(pre);
        }
        continue;
      }
      if (line.trim() === "$$" || line.trim() === "\\[") {
        const close = line.trim() === "$$" ? "$$" : "\\]";
        index += 1;
        const texLines = [];
        while (index < lines.length && lines[index].trim() !== close) texLines.push(lines[index++]);
        if (index < lines.length) index += 1;
        fragment.append(mathBlock(texLines.join("\n"), `${line.trim()}${texLines.join("\n")}${close}`));
        continue;
      }
      const heading = /^(#{1,6})\s+(.+)$/.exec(line);
      if (heading) {
        const node = document.createElement(`h${Math.min(heading[1].length, 6)}`);
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
      while (index < lines.length && lines[index].trim() && !/^```/.test(lines[index]) && !/^#{1,6}\s+/.test(lines[index]) && !/^-\s+/.test(lines[index]) && !/^(\$\$|\\\[)\s*$/.test(lines[index])) paragraphLines.push(lines[index++]);
      const paragraph = document.createElement("p");
      appendInline(paragraph, paragraphLines.join(" "));
      fragment.append(paragraph);
    }
    return fragment;
  }

  function typesetMath(container, isCurrent = () => true) {
    const generation = String(Number(container.dataset.mathGeneration || "0") + 1);
    container.dataset.mathGeneration = generation;
    if (!container.querySelector(".math-source")) return Promise.resolve(false);
    const ready = window.MathJax?.startup?.promise || Promise.resolve();
    return ready.then(() => {
      if (!isCurrent() || container.dataset.mathGeneration !== generation || !container.isConnected) return false;
      if (typeof window.MathJax?.typesetPromise !== "function") throw new Error("Local MathJax renderer is unavailable");
      return window.MathJax.typesetPromise([container]).then(() => isCurrent() && container.dataset.mathGeneration === generation);
    }).catch(() => {
      if (isCurrent() && container.dataset.mathGeneration === generation) {
        container.querySelectorAll(".math-source").forEach((formula) => {
          formula.classList.add("math-fallback");
          formula.title = "Formula renderer unavailable; showing TeX source.";
        });
      }
      return false;
    });
  }

  function clearTypeset(container) {
    if (typeof window.MathJax?.typesetClear === "function") window.MathJax.typesetClear([container]);
  }

  function parseDeepLink(hash) {
    if (typeof hash !== "string" || !hash.startsWith("#")) return null;
    const params = new URLSearchParams(hash.slice(1));
    const claimId = params.get("claim");
    const facetId = params.get("facet");
    if (!claimId || !claimId.startsWith("claim:")) return null;
    if (facetId !== null && !facetId.startsWith("facet:")) return null;
    return { claimId, facetId };
  }

  function resolveDeepLink(hash, graph) {
    const parsed = parseDeepLink(hash);
    if (!parsed || !graph || !Array.isArray(graph.nodes) || !Array.isArray(graph.facet_filters)) return null;
    const claim = graph.nodes.find((node) => node.id === parsed.claimId && node.type === "scientific_claim" && node.claim_type === "contribution");
    if (!claim) return null;
    if (parsed.facetId === null) return { claim, facet: null };
    const facet = graph.facet_filters.find((item) => item.claim_id === claim.id && item.facet_id === parsed.facetId);
    return facet ? { claim, facet } : null;
  }

  function deepLinkState(hash, graph) {
    const selection = resolveDeepLink(hash, graph);
    if (!selection) return null;
    const expandedIds = [...graph.initial_expanded_node_ids, selection.claim.id];
    let pinnedId = selection.claim.id;
    if (selection.facet) {
      expandedIds.push(...selection.facet.target_claim_ids);
      pinnedId = selection.facet.primary_claim_id;
    }
    return {
      selection,
      expandedIds: [...new Set(expandedIds)],
      facetFilter: selection.facet,
      pinnedId,
    };
  }

  function visibleGraphForState(graph, expandedIds, facetFilter = null) {
    if (!graph || !Array.isArray(graph.nodes) || !Array.isArray(graph.edges) || !Array.isArray(expandedIds)) return null;
    const expanded = new Set(expandedIds);
    const edgeAllowed = (edge) => edge.type !== "claim_navigation" || !facetFilter || edge.source !== facetFilter.claim_id || edge.facet_id === facetFilter.facet_id;
    const visible = new Set(graph.initial_node_ids);
    let changed = true;
    while (changed) {
      changed = false;
      graph.edges.forEach((edge) => {
        if (edge.type.startsWith("oracle_") || !edgeAllowed(edge)) return;
        if (visible.has(edge.source) && expanded.has(edge.expand_from) && !visible.has(edge.target)) {
          visible.add(edge.target);
          changed = true;
        }
      });
    }
    const oracleOwnerIds = graph.edges.filter((edge) => edge.type === "oracle_entry").map((edge) => edge.target);
    const oracleExpanded = oracleOwnerIds.some((ownerId) => expanded.has(ownerId));
    if (oracleExpanded) graph.nodes.filter((node) => node.type === "oracle_candidate").forEach((node) => visible.add(node.id));
    const nodes = graph.nodes.filter((node) => visible.has(node.id));
    const edges = graph.edges.filter((edge) => {
      if (!visible.has(edge.source) || !visible.has(edge.target) || !edgeAllowed(edge)) return false;
      return edge.type.startsWith("oracle_") ? oracleExpanded : expanded.has(edge.expand_from);
    });
    return { nodes, edges };
  }

  window.ScientificClaimDemo = Object.freeze({ isSafeUrl, renderMarkdown, typesetMath, parseDeepLink, resolveDeepLink, deepLinkState, visibleGraphForState });

  function requireData(condition, message) { if (!condition) throw new Error(message); }

  function validateGraphData(data) {
    requireData(data?.schema === "agtxiv.scientific-claim-demo/4.0.0", "The generated graph payload has the wrong schema.");
    const graph = data.graph;
    requireData(graph && Array.isArray(graph.nodes) && Array.isArray(graph.edges) && Array.isArray(graph.facet_filters), "The generated graph payload is incomplete.");
    const ids = new Set();
    graph.nodes.forEach((node) => {
      requireData(typeof node.id === "string" && !ids.has(node.id), `Duplicate or missing graph node ID: ${node.id}.`);
      ids.add(node.id);
      requireData(NODE_TYPES.has(node.type) && CLAIM_TYPES.has(node.claim_type), `Graph node ${node.id} has unsupported type metadata.`);
      requireData(["circle", "square"].includes(node.shape), `Graph node ${node.id} has an unsupported shape.`);
      requireData(node.type !== "scientific_claim" || node.shape === "circle", `ScientificClaim ${node.id} must be circular.`);
      requireData(!["math_claim_ir", "oracle_candidate"].includes(node.type) || node.shape === "square", `Processed claim ${node.id} must be square.`);
      requireData(node.type !== "oracle_candidate" || node.visual_state === "gray", `Oracle candidate ${node.id} must be gray.`);
      requireData(typeof node.label === "string" && node.label.trim() && typeof node.detail_markdown === "string" && node.detail_markdown.startsWith("## "), `Graph node ${node.id} has no accessible detail.`);
    });
    const endpointTypes = {
      contains: [["paper"], ["scientific_claim"]], claim_navigation: [["scientific_claim"], ["scientific_claim"]],
      normalizes_identity: [["scientific_claim"], ["math_claim_ir"]], oracle_entry: [["oracle_candidate"], ["math_claim_ir"]],
      oracle_candidate_dependency: [["oracle_candidate"], ["oracle_candidate"]],
    };
    const edgeIds = new Set();
    graph.edges.forEach((edge) => {
      requireData(typeof edge.id === "string" && !edgeIds.has(edge.id) && EDGE_TYPES.has(edge.type), `Duplicate or unsupported graph edge: ${edge.id}.`);
      edgeIds.add(edge.id);
      const source = graph.nodes.find((node) => node.id === edge.source);
      const target = graph.nodes.find((node) => node.id === edge.target);
      requireData(source && target && ids.has(edge.expand_from), `Graph edge ${edge.id} has a dangling endpoint or owner.`);
      const [sourceTypes, targetTypes] = endpointTypes[edge.type];
      requireData(sourceTypes.includes(source.type) && targetTypes.includes(target.type), `Graph edge ${edge.id} has invalid typed endpoints.`);
      if (edge.type.startsWith("oracle_")) requireData(edge.evidence?.oracle_status === "ORACLE_PROPOSED" && edge.evidence?.disposition === "CANDIDATE", `Graph edge ${edge.id} loses Oracle evidence status.`);
    });
    graph.facet_filters.forEach((filter) => requireData(ids.has(filter.claim_id) && filter.facet_id.startsWith("facet:") && filter.target_claim_ids.every((id) => ids.has(id)) && ids.has(filter.primary_claim_id), `Facet selector ${filter.facet_id} is invalid.`));
    requireData(!graph.nodes.some((node) => ["facet", "source_occurrence", "oracle_skeleton"].includes(node.type)), "Legacy visual categories are forbidden.");
  }

  function visibleGraph() {
    return visibleGraphForState(state.data.graph, [...state.expanded], state.facetFilter);
  }

  function nodeMetricKey(node) {
    if (node.type === "scientific_claim" && node.claim_type === "contribution") return "contribution";
    return node.type;
  }

  function layoutGraph(nodes) {
    const layers = new Map();
    nodes.forEach((node) => {
      const level = Number.isInteger(node.layout_level) ? node.layout_level : node.claim_type === "contribution" ? LEVELS.contribution : LEVELS[node.type];
      if (!layers.has(level)) layers.set(level, []);
      layers.get(level).push(node);
    });
    const maxLevel = Math.max(...layers.keys());
    const xPositions = Array.from({ length: maxLevel + 1 }, (_, level) => 82 + level * 205);
    const gap = 12;
    const layerHeights = [];
    for (let level = 0; level <= maxLevel; level += 1) {
      const layer = layers.get(level) || [];
      layerHeights.push(layer.reduce((total, node) => total + NODE_METRICS[nodeMetricKey(node)].footprint, 0) + Math.max(0, layer.length - 1) * gap);
    }
    const totalHeight = Math.max(220, ...layerHeights) + 54;
    const positions = new Map();
    for (let level = 0; level <= maxLevel; level += 1) {
      const layer = layers.get(level) || [];
      let y = (totalHeight - layerHeights[level]) / 2;
      layer.forEach((node) => {
        const metrics = NODE_METRICS[nodeMetricKey(node)];
        positions.set(node.id, { x: xPositions[level], y: y + metrics.hitRadius, radius: metrics.radius, hitRadius: metrics.hitRadius, labelWidth: metrics.labelWidth, footprint: metrics.footprint, level });
        y += metrics.footprint + gap;
      });
    }
    const populated = [...positions.values()];
    const left = Math.min(...populated.map((position) => position.x - Math.max(position.hitRadius, position.labelWidth / 2)));
    const right = Math.max(...populated.map((position) => position.x + Math.max(position.hitRadius, position.labelWidth / 2)));
    const bottom = Math.max(...populated.map((position) => position.y + position.footprint - position.hitRadius));
    state.positions = positions;
    state.bounds = { x: left - 24, y: 8, width: right - left + 48, height: bottom + 28 };
  }

  function conciseNodeLabel(node) {
    if (node.type === "paper") return "Graph-theoretic nonstabilizerness";
    const limit = node.claim_type === "contribution" ? 31 : 24;
    return node.label.length > limit ? `${node.label.slice(0, limit - 1)}…` : node.label;
  }

  function edgePath(source, target) {
    if (source.level === target.level) {
      const direction = source.y <= target.y ? 1 : -1;
      const loopX = Math.max(source.x, target.x) + Math.max(source.radius, target.radius) + 48;
      return `M ${source.x + source.radius} ${source.y} C ${loopX} ${source.y + direction * 5}, ${loopX} ${target.y - direction * 5}, ${target.x + target.radius} ${target.y}`;
    }
    const forward = target.x >= source.x;
    const x1 = source.x + (forward ? source.radius : -source.radius);
    const x2 = target.x - (forward ? target.radius : -target.radius);
    const curve = Math.max(42, Math.abs(x2 - x1) * .45);
    return `M ${x1} ${source.y} C ${x1 + (forward ? curve : -curve)} ${source.y}, ${x2 - (forward ? curve : -curve)} ${target.y}, ${x2} ${target.y}`;
  }

  function renderEdge(edge) {
    const source = state.positions.get(edge.source);
    const target = state.positions.get(edge.target);
    const candidate = edge.type.startsWith("oracle_");
    const group = svgElement("g", { class: `edge-group ${candidate ? "candidate" : "canonical"}`, "data-edge-id": edge.id, "data-source-id": edge.source, "data-target-id": edge.target });
    const path = edgePath(source, target);
    group.append(svgElement("path", { class: "graph-edge-underlay", d: path }));
    group.append(svgElement("path", { class: "graph-edge", d: path, "marker-end": candidate ? "url(#arrowCandidate)" : "url(#arrowCanonical)" }));
    return group;
  }

  function nodeAriaLabel(node) {
    const expansion = node.expandable ? (state.expanded.has(node.id) ? "expanded" : "collapsed") : "leaf";
    return `${TYPE_LABELS[node.type]}; ${node.claim_type}; ${node.label}; ${expansion}. Press Enter or Space to pin details${node.expandable ? " and toggle its branch" : ""}.`;
  }

  function renderNode(node) {
    const position = state.positions.get(node.id);
    const group = svgElement("g", {
      class: `graph-node ${node.type} claim-type-${node.claim_type} visual-${node.visual_state}${state.pinnedId === node.id ? " is-pinned" : ""}`,
      transform: `translate(${position.x} ${position.y})`, tabindex: "0", role: "button", "aria-label": nodeAriaLabel(node),
      ...(node.expandable ? { "aria-expanded": state.expanded.has(node.id) } : {}), "data-node-id": node.id, "data-node-type": node.type,
    });
    group.append(svgElement("circle", { r: position.hitRadius, class: "node-hit-area" }));
    if (node.shape === "square") {
      const side = position.radius * 1.7;
      group.append(svgElement("rect", { x: -side / 2, y: -side / 2, width: side, height: side, rx: node.visual_state === "gray" ? 4 : 1, class: "node-shape", filter: "url(#nodeShadow)" }));
      group.append(svgElement("rect", { x: -side / 2 - 4, y: -side / 2 - 4, width: side + 8, height: side + 8, rx: 5, class: "node-focus" }));
    } else {
      group.append(svgElement("circle", { r: position.radius, class: "node-shape", filter: "url(#nodeShadow)" }));
      group.append(svgElement("circle", { r: position.radius + 4, class: "node-focus" }));
    }
    const label = svgElement("text", { class: "external-node-label", x: 0, y: position.radius + 23, "text-anchor": "middle" });
    label.textContent = conciseNodeLabel(node);
    group.append(label);
    group.addEventListener("mouseenter", () => { applyConnectedHighlight(node.id); showTooltip(node, group); });
    group.addEventListener("mouseleave", () => { if (document.activeElement !== group) { hideTooltip(); restorePinnedHighlight(); } });
    group.addEventListener("focus", () => { applyConnectedHighlight(node.id); if (state.suppressTooltipFocusId === node.id) state.suppressTooltipFocusId = null; else showTooltip(node, group); updateSelectionStatus(node); });
    group.addEventListener("blur", () => { hideTooltip(); restorePinnedHighlight(); });
    group.addEventListener("click", (event) => { event.stopPropagation(); activateNode(node.id, { focusAfter: true }); });
    group.addEventListener("keydown", (event) => handleNodeKeydown(event, node));
    return group;
  }

  function clearConnectedHighlight() {
    state.highlightId = null;
    document.querySelectorAll(".graph-node").forEach((node) => node.classList.remove("hover-active", "hover-muted", "is-highlight-target"));
    document.querySelectorAll(".edge-group").forEach((edge) => edge.classList.remove("hover-active", "hover-muted"));
  }

  function applyConnectedHighlight(nodeId) {
    if (!state.visibleIds.includes(nodeId)) return;
    state.highlightId = nodeId;
    const connected = new Set([nodeId]);
    document.querySelectorAll(".edge-group").forEach((edge) => {
      const active = edge.dataset.sourceId === nodeId || edge.dataset.targetId === nodeId;
      edge.classList.toggle("hover-active", active);
      edge.classList.toggle("hover-muted", !active);
      if (active) { connected.add(edge.dataset.sourceId); connected.add(edge.dataset.targetId); }
    });
    document.querySelectorAll(".graph-node").forEach((node) => {
      const active = connected.has(node.dataset.nodeId);
      node.classList.toggle("hover-active", active);
      node.classList.toggle("hover-muted", !active);
      node.classList.toggle("is-highlight-target", node.dataset.nodeId === nodeId);
    });
  }

  function restorePinnedHighlight() { if (state.pinnedId && state.visibleIds.includes(state.pinnedId)) applyConnectedHighlight(state.pinnedId); else clearConnectedHighlight(); }

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
    if (focusId && state.visibleIds.includes(focusId)) requestAnimationFrame(() => document.querySelector(`[data-node-id="${CSS.escape(focusId)}"]`)?.focus());
    restorePinnedHighlight();
    updateExpandedSummary();
  }

  function descendantsOf(nodeId) {
    const descendants = new Set();
    const queue = [nodeId];
    while (queue.length) {
      const owner = queue.shift();
      state.edges.filter((edge) => edge.expand_from === owner && !edge.type.startsWith("oracle_")).forEach((edge) => {
        if (!descendants.has(edge.target)) { descendants.add(edge.target); queue.push(edge.target); }
      });
    }
    return descendants;
  }

  function hashForNode(node) {
    if (node.type === "scientific_claim" && node.claim_type === "contribution") return `#${new URLSearchParams({ claim: node.id })}`;
    const navigation = state.edges.find((edge) => edge.type === "claim_navigation" && (edge.target === node.id || state.edges.some((identity) => identity.type === "normalizes_identity" && identity.source === edge.target && identity.target === node.id)));
    return navigation ? `#${new URLSearchParams({ claim: navigation.source, facet: navigation.facet_id })}` : null;
  }

  function updateHashForNode(node) {
    const hash = hashForNode(node);
    if (hash && window.location.hash !== hash) history.replaceState(null, "", hash);
  }

  function applyDeepLink(hash) {
    const deepState = deepLinkState(hash, state.data?.graph);
    if (!deepState) return false;
    state.expanded = new Set(deepState.expandedIds);
    state.facetFilter = deepState.facetFilter;
    const selected = state.nodes.get(deepState.pinnedId) || deepState.selection.claim;
    state.pinnedId = selected.id;
    state.suppressTooltipFocusId = selected.id;
    pinDetail(selected);
    renderGraph({ fit: true, focusId: selected.id });
    updateSelectionStatus(selected);
    byId("graphLiveStatus").textContent = `${deepState.selection.facet?.facet_id || deepState.selection.claim.label} opened as a validated filter; unrelated claim branches remain collapsed.`;
    return true;
  }

  function activateNode(nodeId, options = {}) {
    const node = state.nodes.get(nodeId);
    if (!node) return;
    hideTooltip();
    state.suppressTooltipFocusId = options.focusAfter ? nodeId : null;
    state.pinnedId = nodeId;
    pinDetail(node);
    updateHashForNode(node);
    if (node.expandable) {
      if (state.facetFilter && node.id === state.facetFilter.claim_id) state.facetFilter = null;
      if (state.expanded.has(nodeId)) {
        state.expanded.delete(nodeId);
        descendantsOf(nodeId).forEach((id) => state.expanded.delete(id));
      } else state.expanded.add(nodeId);
      renderGraph({ readableFit: true, focusId: options.focusAfter ? nodeId : null });
      byId("graphLiveStatus").textContent = `${node.label} is ${state.expanded.has(nodeId) ? "expanded" : "collapsed"}; ${state.visibleIds.length} claims are visible.`;
    } else {
      renderGraph({ focusId: options.focusAfter ? nodeId : null });
      byId("graphLiveStatus").textContent = `${node.label} detail is pinned; ${state.visibleIds.length} claims are visible.`;
    }
    updateSelectionStatus(node);
  }

  function handleNodeKeydown(event, node) {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activateNode(node.id, { focusAfter: true }); return; }
    if (event.key === "Escape") { event.preventDefault(); clearSelection(); return; }
    const directions = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    if (!directions[event.key]) return;
    event.preventDefault();
    const current = state.positions.get(node.id);
    const [dx, dy] = directions[event.key];
    const candidates = state.visibleIds.filter((id) => id !== node.id).map((id) => ({ id, position: state.positions.get(id) })).filter(({ position }) => dx ? Math.sign(position.x - current.x) === dx : Math.sign(position.y - current.y) === dy);
    candidates.sort((left, right) => {
      const score = ({ position }) => Math.abs(position.x - current.x) * (dx ? 1 : 2) + Math.abs(position.y - current.y) * (dy ? 1 : 2);
      return score(left) - score(right);
    });
    if (candidates[0]) document.querySelector(`[data-node-id="${CSS.escape(candidates[0].id)}"]`)?.focus();
  }

  function incomingParent(nodeId) {
    const edge = state.edges.find((candidate) => candidate.target === nodeId && state.visibleIds.includes(candidate.source) && !candidate.type.startsWith("oracle_"));
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

  function updateSelectionStatus(node) { byId("breadcrumb").textContent = breadcrumbFor(node); }
  function updateExpandedSummary() {
    if (!state.pinnedId) byId("breadcrumb").textContent = "Paper › contribution ScientificClaims";
    byId("graphLiveStatus").dataset.expandedCount = String([...state.expanded].filter((id) => state.nodes.get(id)?.expandable).length);
  }

  function relationMarkdown(node) {
    const relations = state.edges.filter((edge) => edge.source === node.id || edge.target === node.id);
    if (!relations.length) return "";
    return "\n\n### Graph relations\n" + relations.map((edge) => {
      const direction = edge.source === node.id ? "to" : "from";
      const other = edge.source === node.id ? edge.target : edge.source;
      const evidence = edge.type.startsWith("oracle_") ? " · `ORACLE_PROPOSED / UNVERIFIED`" : "";
      const reason = edge.reason ? ` — ${edge.reason}` : "";
      return `- ${edge.relation || edge.type} ${direction} \`${other}\`${evidence}${reason}`;
    }).join("\n");
  }

  function renderDetail(container, node, isCurrent) {
    clearTypeset(container);
    container.replaceChildren(renderMarkdown(node.detail_markdown + relationMarkdown(node)));
    return typesetMath(container, isCurrent);
  }

  function pinDetail(node) {
    byId("detailTitle").textContent = node.label;
    const body = byId("pinnedDetail");
    renderDetail(body, node, () => state.pinnedId === node.id);
    byId("unpinButton").hidden = false;
    document.querySelectorAll(".graph-node").forEach((element) => element.classList.toggle("is-pinned", element.dataset.nodeId === node.id));
  }

  function clearSelection() {
    hideTooltip();
    state.pinnedId = null;
    const body = byId("pinnedDetail");
    clearTypeset(body);
    byId("detailTitle").textContent = "Select a claim";
    body.replaceChildren(htmlElement("p", "", "Activate a node to pin its source-faithful metadata or normalized mathematics."));
    byId("unpinButton").hidden = true;
    byId("breadcrumb").textContent = "Paper › contribution ScientificClaims";
    document.querySelectorAll(".graph-node").forEach((element) => element.classList.remove("is-pinned"));
    clearConnectedHighlight();
    byId("graphLiveStatus").textContent = "Floating and pinned details closed.";
  }

  function positionTooltip(anchor) {
    const tooltip = byId("nodeTooltip");
    if (tooltip.hidden) return;
    const anchorBox = anchor.getBoundingClientRect();
    const tooltipBox = tooltip.getBoundingClientRect();
    const margin = 12;
    let left = anchorBox.right + margin;
    if (left + tooltipBox.width > window.innerWidth - margin) left = anchorBox.left - tooltipBox.width - margin;
    left = Math.max(margin, Math.min(left, window.innerWidth - tooltipBox.width - margin));
    let top = Math.max(margin, Math.min(anchorBox.top, window.innerHeight - tooltipBox.height - margin));
    if (top < anchorBox.bottom && top + tooltipBox.height > anchorBox.top && left < anchorBox.right && left + tooltipBox.width > anchorBox.left) {
      top = anchorBox.bottom + margin;
      if (top + tooltipBox.height > window.innerHeight - margin) top = Math.max(margin, anchorBox.top - tooltipBox.height - margin);
    }
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function showTooltip(node, anchor) {
    const tooltip = byId("nodeTooltip");
    state.tooltipId = node.id;
    tooltip.hidden = false;
    renderDetail(tooltip, node, () => state.tooltipId === node.id && !tooltip.hidden).then((current) => { if (current) positionTooltip(anchor); });
    positionTooltip(anchor);
  }

  function hideTooltip() {
    const tooltip = byId("nodeTooltip");
    state.tooltipId = null;
    clearTypeset(tooltip);
    tooltip.hidden = true;
    tooltip.replaceChildren();
  }

  function applyTransform() {
    byId("claimGraphSvg").dataset.scale = String(state.transform.scale);
    byId("viewportGroup").setAttribute("transform", `translate(${state.transform.x} ${state.transform.y}) scale(${state.transform.scale})`);
  }

  function fittedScale(width, height) {
    const padding = 34;
    return Math.max(.15, Math.min(1.2, (width - padding * 2) / state.bounds.width, (height - padding * 2) / state.bounds.height));
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
    centerGraphAtScale(svg.clientWidth, svg.clientHeight, Math.max(fittedScale(svg.clientWidth, svg.clientHeight), readableScaleFloor(svg.clientWidth)));
  }

  function zoomAt(factor, clientX, clientY) {
    const box = byId("claimGraphSvg").getBoundingClientRect();
    const x = clientX - box.left;
    const y = clientY - box.top;
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
    byId("zoomInButton").addEventListener("click", () => { const box = byId("claimGraphSvg").getBoundingClientRect(); zoomAt(1.25, box.left + box.width / 2, box.top + box.height / 2); });
    byId("zoomOutButton").addEventListener("click", () => { const box = byId("claimGraphSvg").getBoundingClientRect(); zoomAt(.8, box.left + box.width / 2, box.top + box.height / 2); });
    byId("expandButton").addEventListener("click", () => {
      state.facetFilter = null;
      state.data.graph.nodes.filter((node) => node.expandable).forEach((node) => state.expanded.add(node.id));
      renderGraph({ readableFit: true });
      byId("graphLiveStatus").textContent = `All canonical and unverified candidate branches opened; ${state.visibleIds.length} claims are visible.`;
    });
    byId("collapseButton").addEventListener("click", () => {
      state.facetFilter = null;
      state.expanded = new Set(state.data.graph.initial_expanded_node_ids);
      renderGraph({ fit: true });
      byId("graphLiveStatus").textContent = "Graph collapsed to the paper and contribution claims.";
    });
    byId("resetButton").addEventListener("click", () => {
      state.facetFilter = null;
      state.expanded = new Set(state.data.graph.initial_expanded_node_ids);
      clearSelection();
      history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
      renderGraph({ fit: true });
      byId("graphLiveStatus").textContent = "Graph expansion, selection, pan, and zoom reset.";
    });
    byId("unpinButton").addEventListener("click", clearSelection);
    const stage = byId("graphStage");
    stage.addEventListener("wheel", (event) => { event.preventDefault(); zoomAt(event.deltaY < 0 ? 1.12 : .89, event.clientX, event.clientY); }, { passive: false });
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
    const endPan = (event) => { if (state.dragging?.pointerId === event.pointerId) { state.dragging = null; stage.classList.remove("is-panning"); } };
    stage.addEventListener("pointerup", endPan);
    stage.addEventListener("pointercancel", endPan);
    window.addEventListener("resize", () => { if (state.preferReadableFit) fitGraphReadably(); else fitGraph(); });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape" && (state.tooltipId || state.pinnedId)) { event.preventDefault(); clearSelection(); } });
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
      if (!response.ok) throw new Error(`The generated graph request failed with HTTP ${response.status}.`);
      const data = await response.json();
      validateGraphData(data);
      state.data = data;
      state.nodes = new Map(data.graph.nodes.map((node) => [node.id, node]));
      state.edges = data.graph.edges;
      state.expanded = new Set(data.graph.initial_expanded_node_ids);
      state.facetFilter = null;
      state.pinnedId = null;
      byId("paperTitle").textContent = data.paper.title;
      byId("paperAuthors").textContent = data.paper.authors.join(" · ");
      byId("graphApp").hidden = false;
      finishLoading();
      if (!applyDeepLink(window.location.hash)) renderGraph({ fit: true });
    } catch (error) {
      showLoadError(error instanceof Error ? error : new Error("The generated graph could not be loaded."));
    }
  }

  byId("retryButton").addEventListener("click", initialize);
  wireGraphControls();
  initialize();
})();
