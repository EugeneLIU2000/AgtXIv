import { catalog, loadDataset, kindNames, operations, layers } from './data.js?v=20260918-en';
import { enter, enhanceMap, destroyGrid, initializeMotion } from './motion.js?v=20260918-en';

const $ = selector => document.querySelector(selector);
const $$ = selector => Array.from(document.querySelectorAll(selector));
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const esc = escapeHTML;
const json = value => esc(JSON.stringify(value, null, 2));
const state = { page: 'workspace', dataset: 'minimal', node: 'mc1', view: 'map', data: null, zoom: 1 };
const cache = new Map();
let routeGeneration = 0;
let graphResize = null;
let previousDialogFocus = null;
const selected = () => state.data?.nodes.find(node => node.id === state.node);
const announce = message => { $('#announcement').textContent = message; };
// A tiny presentation mapping for the retained example, never a math parser.
// Unknown notation stays visible as source text; the raw comparison is unchanged.
const displayMath = item => String(item.normalization?.normalized_statement || item.conclusion || '')
  .replaceAll('\\forall', '∀ ').replaceAll('\\in', ' ∈ ').replaceAll('\\mathbb{R}', 'ℝ')
  .replaceAll('\\quad', ' ').replaceAll('^{2}', '²').replaceAll('\\geq', ' ≥ ');

function navigate(changes) {
  const route = { page: state.page, dataset: state.dataset, node: state.node, view: state.view, ...changes };
  const hash = new URLSearchParams(route).toString();
  if (location.hash.slice(1) === hash) return;
  location.hash = hash;
}

function openDialog(dialog) {
  previousDialogFocus = document.activeElement;
  dialog.showModal();
  enter([dialog]);
}
function showDetail(title, body, eyebrow = 'CONTEXT, KEPT CLOSE') {
  $('#detail-dialog-title').textContent = title;
  $('#detail-dialog-eyebrow').textContent = eyebrow;
  $('#detail-dialog-body').innerHTML = body;
  openDialog($('#detail-dialog'));
}

function updateShell() {
  ['workspace', 'library', 'protocol'].forEach(page => {
    $(`#${page}-page`).hidden = state.page !== page;
    const link = $(`[data-page="${page}"]`);
    link.classList.toggle('active', state.page === page);
    if (state.page === page) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  $$('.desk-item').forEach(button => {
    const active = button.dataset.dataset === state.dataset;
    button.classList.toggle('selected', active);
    button.setAttribute('aria-pressed', String(active));
  });
  $$('.view-tabs button').forEach(button => {
    const active = button.dataset.view === state.view;
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
  });
  $('#reading-view').setAttribute('aria-labelledby', `tab-${state.view}`);
}

async function route() {
  const parameters = new URLSearchParams(location.hash.slice(1));
  // Preserve links to existing published papers, jobs, protocol, and report.
  if (['explore', 'protocol', 'report'].includes(location.hash.slice(1)) || parameters.has('paper') || parameters.has('job')) {
    location.replace(`/reader.html${location.hash}`);
    return;
  }
  const generation = ++routeGeneration;
  const page = ['workspace', 'library', 'protocol'].includes(parameters.get('page')) ? parameters.get('page') : 'workspace';
  const dataset = catalog.some(item => item.id === parameters.get('dataset')) ? parameters.get('dataset') : 'minimal';
  const view = ['map', 'list', 'record'].includes(parameters.get('view')) ? parameters.get('view') : 'map';
  const changedPage = page !== state.page;
  const rebuild = dataset !== state.dataset || view !== state.view || !state.data || changedPage;
  const changedDataset = dataset !== state.dataset;
  state.page = page;
  state.dataset = dataset;
  state.view = view;
  updateShell();
  if (page !== 'workspace') {
    destroyGrid();
    graphResize?.disconnect();
    if (page === 'library') renderLibrary();
    if (page === 'protocol') renderProtocol();
    if (changedPage) enter([$(`#${page}-page`)]);
    return;
  }
  if (changedDataset || !state.data) {
    destroyGrid();
    graphResize?.disconnect();
    state.data = null;
    $('#download-record').disabled = true;
    $('#reading-view').innerHTML = '<div class="load-message" role="status">Loading the repository example…</div>';
    $('#inspector').innerHTML = '<p class="eyebrow">KEEPING THE CONTEXT CLOSE</p><p class="detail-summary">Sources and conditions will appear here once the material loads.</p>';
    $('#paper-origin').textContent = 'OPENING RESEARCH MATERIAL';
    $('#paper-title').textContent = catalog.find(item => item.id === dataset).title;
    $('#paper-subtitle').textContent = 'Loading the associated record.';
    $('#material-notice').textContent = 'Loading…';
    $('#record-count').textContent = 'Waiting for material';
  }
  try {
    if (!cache.has(dataset)) cache.set(dataset, loadDataset(dataset));
    const data = await cache.get(dataset);
    if (generation !== routeGeneration) return;
    state.data = data;
    state.node = data.nodes.some(node => node.id === parameters.get('node')) ? parameters.get('node') : data.defaultNode;
    $('#paper-title').textContent = data.title;
    $('#paper-origin').textContent = data.category;
    $('#paper-subtitle').textContent = data.subtitle;
    $('#material-notice').innerHTML = `<span class="notice-dot"></span><span>${esc(data.notice)}</span>`;
    $('#record-count').textContent = `${data.nodes.length} ${dataset === 'minimal' ? 'example objects' : 'historical candidates'}`;
    $('#download-record').disabled = false;
    if (rebuild) { state.zoom = 1; renderReadingView(); }
    else updateSelection();
    renderInspector();
    if (changedPage) enter([$('#workspace-page')]);
  } catch (error) {
    cache.delete(dataset);
    if (generation !== routeGeneration) return;
    state.data = null;
    $('#reading-view').innerHTML = `<div class="load-message"><p role="alert">${esc(error.message || 'The material could not be loaded.')}</p><button class="secondary-button" data-action="retry">Try again</button></div>`;
    $('#inspector').innerHTML = '<p class="eyebrow">MATERIAL UNAVAILABLE</p><p class="detail-summary">No material has loaded. Try again or choose another example.</p>';
    $('#material-notice').textContent = 'Loading failed · Unavailable content is not an empty record.';
    $('#record-count').textContent = 'Material unavailable';
    $('#download-record').disabled = true;
  }
}

const minimalPaths = [
  ['loc1', 'sc1', 'M184 148C216 148 204 88 241 88'],
  ['sc1', 'mc1', 'M397 88C430 88 423 151 453 151'],
];
const historicalPaths = [
  ['definition', 'channel', 'M184 60H237'],
  ['channel', 'feasibility', 'M394 60H447'],
  ['feasibility', 'contraction', 'M525 106V143Q525 152 516 152H325Q316 152 316 161V182'],
  ['contraction', 'R3', 'M394 224H447'],
  ['definition', 'R3', 'M106 106V130Q106 138 116 138H615Q623 138 623 149V215Q623 224 614 224H604'],
];

function renderMap() {
  const minimal = state.dataset === 'minimal';
  const paths = (minimal ? minimalPaths : historicalPaths).filter(([from, to]) =>
    state.data.edges.some(edge => edge.from === from && edge.to === to));
  $('#reading-view').innerHTML = `<div class="map-area"><div class="map-header"><div><h3>${minimal ? 'From source to mathematical statement' : 'The path to monotonicity'}</h3><p>${minimal ? 'Connected statements, with context at every step' : 'Historical candidates · Postselection shown separately'}</p></div><div class="map-view-controls" role="group" aria-label="Map zoom"><button data-action="zoom-out" aria-label="Zoom out">−</button><button data-action="zoom-in" aria-label="Zoom in">＋</button><button data-action="fit" aria-label="Fit the map">Fit</button></div></div><div class="graph-window" tabindex="0" aria-label="Claim map. Use the zoom controls; press Tab to select a claim."><div class="graph-size-container"><div class="graph-board ${minimal ? '' : 'historical'}"><svg class="graph-links" viewBox="0 0 640 306" aria-hidden="true">${paths.map(([from, to, d]) => `<path class="graph-link ${minimal ? 'correspondence' : ''}" data-from="${esc(from)}" data-to="${esc(to)}" d="${d}"/>`).join('')}${minimal ? '<path d="M531 208V236Q531 247 520 247H472" stroke-dasharray="3 5"/>' : ''}</svg>${state.data.nodes.map(node => `<button class="graph-node kind-${node.kind} position-${node.id}" data-node="${esc(node.id)}" aria-pressed="${node.id === state.node}" aria-label="${esc(kindNames[node.kind])}: ${esc(node.title)}"><span class="node-top"><i class="node-symbol" aria-hidden="true"></i>${esc(node.label)}</span><span class="node-name">${esc(node.title)}</span>${minimal ? `<span class="${node.id === 'mc1' ? 'node-formula' : 'node-description'}">${node.id === 'loc1' ? 'source.txt · Source markers' : node.id === 'sc1' ? 'The author’s statement' : esc(displayMath(node.raw))}</span>` : `<span class="node-description">${esc(node.id)} · Unassessed</span>`}</button>`).join('')}${minimal ? '<div class="graph-branch-note">Next, explore dependencies<br>and formalization for this target.</div>' : ''}</div></div></div><div class="map-legend"><span><i class="legend-line ${minimal ? '' : 'solid'}" aria-hidden="true"></i>${minimal ? 'Source / statement links, not proof edges' : 'Historical candidate dependencies'}</span><span>Select a node to read its context <span aria-hidden="true">↗</span></span></div></div>`;
  fitGraph();
  graphResize = new ResizeObserver(() => fitGraph());
  graphResize.observe($('.graph-window'));
  enhanceMap($('.map-area'));
}

function fitGraph() {
  const windowElement = $('.graph-window');
  const board = $('.graph-board');
  if (!windowElement || !board) return;
  // Keep node text readable on phones; the graph itself may scroll horizontally.
  const fitScale = Math.min(1, Math.max(.82, (windowElement.clientWidth - 12) / 640));
  const scale = fitScale * state.zoom;
  const container = $('.graph-size-container');
  const width = 640 * scale;
  board.style.transform = `scale(${scale})`;
  board.style.marginLeft = `${Math.max(0, (windowElement.clientWidth - width) / 2)}px`;
  board.style.marginRight = '0';
  container.style.width = `${Math.max(windowElement.clientWidth, width)}px`;
  container.style.height = `${Math.max(270, 306 * scale)}px`;
  $('[data-action="zoom-out"]').disabled = state.zoom <= .8;
  $('[data-action="zoom-in"]').disabled = state.zoom >= 2;
}

function renderReadingView() {
  destroyGrid();
  graphResize?.disconnect();
  if (state.view === 'map') renderMap();
  if (state.view === 'list') {
    $('#reading-view').innerHTML = `<div class="claim-list" aria-label="List view">${state.data.nodes.map((node, index) => `<button data-node="${esc(node.id)}" aria-pressed="${node.id === state.node}"><span class="list-number">${String(index + 1).padStart(2, '0')}</span><span><strong>${esc(node.title)}</strong><small>${esc(kindNames[node.kind])} · ${esc(node.id)}</small></span><span class="list-arrow" aria-hidden="true">↗</span></button>`).join('')}</div>`;
  }
  if (state.view === 'record') {
    $('#reading-view').innerHTML = `<div class="record-pane"><p>${state.dataset === 'minimal' ? 'The hand-authored v0.2 Output, with its original fields. No model execution receipt accompanies it.' : 'The selected historical paper object, with its original fields and V3 identity. It has not been converted to v0.2.'}</p><pre>${json(state.data.raw)}</pre></div>`;
  }
  updateSelection();
  enter($$('.graph-node, .claim-list button'));
}

function updateSelection() {
  $$('[data-node]').forEach(button => {
    const active = button.dataset.node === state.node;
    button.classList.toggle('selected', active);
    button.setAttribute('aria-pressed', String(active));
  });
  $$('.graph-link').forEach(path => path.classList.toggle('emphasized', path.dataset.to === state.node || path.dataset.from === state.node));
}

function detailHeader(node) {
  return `<div class="inspector-title-row"><p class="eyebrow">SELECTED ${state.dataset === 'minimal' ? 'OBJECT' : 'CANDIDATE'}</p><span class="inspector-index">${esc(node.id)}</span></div><div><h3>${esc(node.title)}</h3><span class="status-tag">${state.dataset === 'minimal' ? 'Hand-authored · Not executed' : 'Historical candidate · Unassessed'}</span></div>`;
}
const detailList = (items, empty) => items.length ? `<ul>${items.map(item => `<li>${esc(item)}</li>`).join('')}</ul>` : `<p>${esc(empty)}</p>`;

function renderInspector() {
  const node = selected();
  if (!node) return;
  const item = node.raw;
  let body = '';
  if (node.kind === 'math_claim') {
    body = `<div class="formula-box">${esc(displayMath(item))}<small>${esc(item.exactness)} · Statement exactness</small></div><p class="detail-summary">${esc(item.normalization.source_statement)}</p><dl class="detail-facts"><dt>Objects</dt><dd>${item.objects.map(object => `${esc(object.symbol)} ∈ ${esc(object.domain)}`).join('<br>')}</dd><dt>Quantifiers</dt><dd>${item.quantifiers.map(q => `${q.kind === 'FORALL' ? 'For every' : 'There exists'} ${esc(q.variable)}`).join('; ')}</dd><dt>Assumptions</dt><dd>${item.assumptions.length ? item.assumptions.map(esc).join('; ') : 'No additional assumptions listed'}</dd><dt>Derived from</dt><dd>${esc(item.source_claim.local)} / component ${esc(item.component_id)}</dd></dl><div class="detail-section"><h4>How does the wording change?</h4><p>The example declares that implicit context has been made explicit. Both versions are retained.</p><button class="inspector-action" data-action="normalization">Compare both versions <span aria-hidden="true">↗</span></button></div><button class="inspector-action" data-action="formalization">Explore this target <span aria-hidden="true">→</span></button>`;
  } else if (node.kind === 'scientific_claim') {
    body = `<p class="detail-summary">${esc(item.statement)}</p><dl class="detail-facts"><dt>Modality</dt><dd>${esc(item.modality)}</dd><dt>Attribution</dt><dd>${esc(item.attribution)}</dd><dt>System</dt><dd>${esc(item.system)}</dd><dt>Conditions</dt><dd>${item.conditions.length ? item.conditions.map(esc).join('; ') : 'No additional conditions listed'}</dd></dl><div class="detail-section"><h4>Claim components: ${item.components.length}</h4>${item.components.map(component => `<p>${esc(component.id)} · ${esc(component.conclusion)}</p><p>Math references: ${component.math_refs.map(ref => esc(ref.local)).join(', ')}. ${component.residual === null ? 'No residual is declared.' : esc(component.residual)}</p>`).join('')}</div><button class="inspector-action" data-action="source">Read the source statement <span aria-hidden="true">↗</span></button><button class="inspector-action" data-action="math-node">Read the mathematical claim <span aria-hidden="true">→</span></button>`;
  } else if (node.kind === 'source_locator') {
    body = `<p class="detail-summary">A source locator records start and end markers. The host must resolve the actual byte range in the original source.</p><dl class="detail-facts"><dt>Input alias</dt><dd>${esc(item.source.input)}</dd><dt>Start marker</dt><dd>${esc(item.start_marker)}</dd><dt>End marker</dt><dd>${esc(item.end_marker)}</dd><dt>Source type</dt><dd>Hand-authored teaching text, not a paper excerpt</dd></dl><div class="detail-section"><h4>Resolution boundary</h4><p>This example has no source_binding receipt. No resolved byte offsets or resolution status are claimed.</p></div><button class="inspector-action" data-action="source">Read the example source <span aria-hidden="true">↗</span></button>`;
  } else {
    body = `<p class="detail-summary">${esc(item.intuition)}</p><div class="formula-box small">${esc(item.formula)}</div><dl class="detail-facts"><dt>Retained status</dt><dd>${esc(item.verification)}</dd><dt>Record type</dt><dd>V3 argument-node</dd><dt>Candidate premises</dt><dd>${item.dependencies.length ? item.dependencies.map(esc).join(' + ') : 'No internal dependencies declared'}</dd></dl><div class="detail-section"><h4>Conditions that still apply</h4>${detailList(item.conditions, 'No conditions supplied.')}</div><button class="inspector-action" data-action="source">View sources and scope <span aria-hidden="true">↗</span></button>`;
  }
  $('#inspector').innerHTML = detailHeader(node) + body;
  enter([$('#inspector')]);
  announce(`Selected ${kindNames[node.kind]}: ${node.title}. Details appear beside or below the map.`);
}

function showSource() {
  if (!state.data) return;
  if (state.dataset === 'minimal') {
    const locator = state.data.raw.items.find(item => item.kind === 'source_locator');
    showDetail('Back to the source', `<p class="muted">This text comes from the repository teaching file. It is not an excerpt from a research paper.</p><blockquote class="source-quote"><pre>${esc(state.data.source)}</pre></blockquote><p class="source-meta">${esc(state.data.sourceOrigin)}</p><h3>Source markers</h3><dl class="detail-facts"><dt>Start</dt><dd>${esc(locator.start_marker)}</dd><dt>End</dt><dd>${esc(locator.end_marker)}</dd></dl><p class="boundary-note">The example retains markers only. No source resolution or source_binding has been produced, and no byte range is claimed to be verified.</p><div class="dialog-actions"><a href="/workspace/data/source.txt" target="_blank" rel="noopener">Open the source text ↗</a><a href="/workspace/data/paper-minimal.json" target="_blank" rel="noopener">Open the complete Output ↗</a></div>`, 'BACK TO THE SOURCE');
  } else {
    const node = selected();
    showDetail('Sources and scope', `<p>${esc(node.raw.interpretation)}</p><h3>Retained source anchors</h3>${node.raw.anchors.map(anchor => `<p class="source-meta">${esc(anchor.path)} · lines ${anchor.line_start}–${anchor.line_end}<br>bytes [${anchor.start_byte}, ${anchor.end_byte})<br>retained sha256: ${esc(anchor.sha256)}</p>`).join('')}<h3>Open uncertainties</h3>${detailList(node.raw.unknowns, 'No uncertainty notes supplied.')}<p class="boundary-note">These details come from the historical library. This interface has not reread the original source bytes or rechecked these anchors.</p><div class="dialog-actions"><a href="${esc(state.data.raw.source_url)}" target="_blank" rel="noopener">Open the paper on arXiv ↗</a><a href="/reader.html#paper=robustness-of-magic&claim=${encodeURIComponent(node.id)}">Continue in the legacy reader ↗</a></div>`, 'SOURCE-LINKED, STILL A CANDIDATE');
  }
}

function showNormalization() {
  if (!state.data || state.dataset !== 'minimal') return;
  const math = state.data.raw.items.find(item => item.kind === 'math_claim');
  const normalization = math.normalization;
  showDetail('One claim, two formulations', `<p class="muted">Keep the source statement alongside its normalized mathematical form so the changes remain visible.</p><div class="source-columns"><section><h3>01 · Source statement</h3><p>${esc(normalization.source_statement)}</p></section><section><h3>02 · Normalized statement</h3><p class="raw-math">${esc(normalization.normalized_statement)}</p></section></div><h3>Declared change</h3><p><code>${esc(normalization.relation_to_source)}</code></p><p class="muted">Meaning: context left implicit in the source is made explicit. This is the declaration in the example, not an independent assessment of that classification.</p><h3>Unresolved symbols</h3><p>${normalization.unresolved_symbols.length ? normalization.unresolved_symbols.map(esc).join(', ') : 'None listed in the example; no symbol check is implied.'}</p><div class="dialog-actions"><a href="/workspace/data/paper-minimal.json" target="_blank" rel="noopener">Read the full normalization record ↗</a></div>`, 'MEANING BEFORE NOTATION');
}

function showFormalization() {
  if (!state.data) { openDialog($('#paper-dialog')); return; }
  const legacy = state.dataset !== 'minimal';
  const math = legacy ? selected() : state.data.nodes.find(node => node.kind === 'math_claim');
  showDetail('A path for one mathematical claim', `<p>Selected target: <strong>${esc(math.title)}</strong> <code>${esc(math.id)}</code></p><p class="muted">${legacy ? 'This is a historical argument candidate. It needs an explicit v0.2 migration to a fixed MathClaim version first.' : 'This object comes from a hand-authored teaching Output. A real model run and host commit are required before it can become a persistent input to the next Task.'}</p><div class="formal-path"><div class="formal-stage"><span class="stage-number">01</span><div><h3>Pin the MathClaim</h3><p>Retain the exact producing Task, Output, and item_id identities, together with conditions and quantifiers.</p><code>Prerequisites missing</code></div></div><div class="formal-stage"><span class="stage-number">02</span><div><h3>Draft a Lamport proof</h3><p>Call a model to organize joint premises and proof steps. Commit the intermediate artifact before starting the next task.</p><code>autoformalization.lamport · Not started</code></div></div><div class="formal-stage"><span class="stage-number">03</span><div><h3>Draft Lean source in a fixed environment</h3><p>Use a previously committed Lamport artifact for this same target. Lean builds and statement alignment require separate evidence.</p><code>autoformalization.lean · Not started</code></div></div></div><p class="boundary-note"><strong>This is a workflow guide. </strong>The v0.2 execution service is not connected. No Task is created, model called, or Lean build run. The scope is one selected claim, with no automatic expansion to the whole paper or every upstream claim.</p>`, 'ONE FIXED MATHCLAIM');
}

function showProvenance() {
  if (!state.data) return;
  showDetail('Where this material comes from', `<p class="muted">${esc(state.data.notice)}</p><h3>Maintained source file</h3><p class="source-meta">${esc(state.data.origin)}</p><h3>Identity and reference boundaries</h3><p>${esc(state.data.identityNote)}</p><h3>Selected object, as recorded</h3><pre>${json(selected()?.raw)}</pre><p class="boundary-note">This view reads retained files. It is not the service specified in READ-INTERFACE.md and does not claim a host response containing message, reference, and artifacts.</p>`, 'THE MATERIAL, AS RETAINED');
}

function renderLibrary() {
  $('#library-page').innerHTML = `<p class="eyebrow">SMALL COLLECTION, CLEAR PROVENANCE</p><h1 id="library-title">A place to begin.</h1><p class="page-intro">Start with a simple example, then explore an argument from a research paper. Each material keeps its origin and completion boundary visible.</p><div class="library-search"><label for="library-filter">Search the collection</label><input id="library-filter" type="search" placeholder="Try square, quantum, or an arXiv ID" autocomplete="off"></div><p id="library-count" class="sr-only" role="status"></p><div class="library-grid" id="library-results"></div>`;
  const filter = () => {
    const query = $('#library-filter').value.trim().toLowerCase();
    const matches = catalog.filter(item => `${item.title} ${item.description} ${item.searchable}`.toLowerCase().includes(query));
    $('#library-count').textContent = `Matching entries: ${matches.length}`;
    $('#library-results').innerHTML = matches.length ? matches.map(item => `<article class="library-card"><span class="paper-mini">${item.number}</span><p class="eyebrow">${item.category}</p><h2>${item.title}</h2><p>${item.description}</p><button data-dataset="${item.id}">Open in workspace <span aria-hidden="true">↗</span></button></article>`).join('') : '<p class="library-empty">No matching materials. Try square or quantum.</p>';
  };
  $('#library-filter').addEventListener('input', filter);
  filter();
}

function renderProtocol() {
  $('#protocol-page').innerHTML = `<p class="eyebrow">RESEARCH / 0.2.0</p><h1 id="protocol-title">Less machinery.<br>More meaning.</h1><p class="page-intro">A schema is a shared record format across models. Version 0.2 retains sources, candidates, conditions, and gaps. Every executed research task requires a real model call.</p><section class="protocol-section"><h2>Four operations. A traceable research path.</h2><div class="operation-list">${operations.map(([operation, title, description], index) => `<article class="operation-row"><span>0${index + 1}</span><div><h3>${operation}</h3><strong>${title}</strong></div><p>${description}</p></article>`).join('')}</div></section><section class="protocol-section"><h2>Three layers to keep in view.</h2><div class="object-grid"><article class="object-card"><h3>01 / Sources</h3><p>A source_locator stores start and end markers. The host produces a source_binding after resolving original bytes. Display names and paths do not replace exact source identities.</p></article><article class="object-card"><h3>02 / Candidate content</h3><p>A ScientificClaim retains scientific context and claim components. A MathClaim retains objects, quantifiers, assumptions, and normalization changes. Correspondence between them is not a proof dependency.</p></article><article class="object-card"><h3>03 / Execution evidence</h3><p>The host records run receipts with actual calls, inputs, outputs, and check reports. COMMITTED means candidates were saved, not scientifically accepted.</p></article></div></section><section class="protocol-section"><h2>Seven check layers. Separate questions.</h2><div class="check-layers">${layers.map(layer => `<span>${layer}</span>`).join('')}</div><p class="boundary-note">These are the check layers defined in the specification. <strong>No passing checks are claimed for this example</strong>. Unperformed checks use NOT_RUN. PASS and FAIL must reference actual reports. A valid format does not establish a scientific conclusion.</p></section><section class="protocol-section"><h2>Read the specifications.</h2><div class="protocol-links"><a href="/workspace/data/contract.md" target="_blank" rel="noopener">Task and Output contract ↗</a><a href="/workspace/data/host.md" target="_blank" rel="noopener">Host execution ↗</a><a href="/workspace/data/read-interface.md" target="_blank" rel="noopener">Read interface ↗</a><a href="/workspace/data/items.schema.json" target="_blank" rel="noopener">Candidate object schema ↗</a></div></section>`;
}

function handleAction(action) {
  if (action === 'retry') { route(); return; }
  if (!state.data) return;
  if (action === 'source') showSource();
  if (action === 'normalization') showNormalization();
  if (action === 'formalization') showFormalization();
  if (action === 'math-node') navigate({ node: 'mc1' });
  if (action === 'fit') state.zoom = 1;
  if (action === 'zoom-in') state.zoom = Math.min(2, Math.round((state.zoom + .2) * 10) / 10);
  if (action === 'zoom-out') state.zoom = Math.max(.8, Math.round((state.zoom - .2) * 10) / 10);
  if (['fit', 'zoom-in', 'zoom-out'].includes(action)) {
    fitGraph();
    if (action === 'fit') $('.graph-window').scrollTo({ top: 0, left: 0 });
    announce(`Map zoom: ${Math.round(state.zoom * 100)}% relative to fit size.`);
  }
}

document.addEventListener('click', event => {
  const button = event.target.closest('button, a');
  if (!button) return;
  if (button.matches('[data-page]')) {
    event.preventDefault();
    navigate({ page: button.dataset.page });
  }
  if (button.matches('[data-dataset]')) {
    const dataset = button.dataset.dataset;
    $('#paper-dialog').close();
    navigate({ page: 'workspace', dataset, node: dataset === 'minimal' ? 'mc1' : 'R3', view: 'map' });
  }
  if (button.matches('[data-node]')) navigate({ node: button.dataset.node });
  if (button.matches('[data-view]')) navigate({ view: button.dataset.view });
  if (button.matches('[data-action]')) handleAction(button.dataset.action);
  if (button.matches('.close-dialog')) button.closest('dialog').close();
});

$('.view-tabs').addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  const tabs = $$('.view-tabs button');
  const current = tabs.indexOf(document.activeElement);
  if (current < 0) return;
  event.preventDefault();
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (current + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
  tabs[next].focus();
  navigate({ view: tabs[next].dataset.view });
});

$$('dialog').forEach(dialog => {
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    if (previousDialogFocus?.isConnected) previousDialogFocus.focus();
  });
});

$('#add-paper').addEventListener('click', () => openDialog($('#paper-dialog')));
$('#switch-example').addEventListener('click', () => openDialog($('#paper-dialog')));
$('#show-provenance').addEventListener('click', showProvenance);
$('#open-formalization').addEventListener('click', showFormalization);
$('#download-record').addEventListener('click', () => {
  if (!state.data) return;
  const blob = new Blob([JSON.stringify(state.data.raw, null, 2) + '\n'], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = state.dataset === 'minimal' ? 'agtxiv-v02-hand-authored-output.json' : 'agtxiv-historical-robustness.json';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  announce('Material exported with its original identities and fields.');
});

$('#paper-form').addEventListener('submit', event => {
  event.preventDefault();
  const input = $('#paper-input');
  let value = input.value.trim();
  try {
    if (/^https?:\/\//i.test(value)) {
      const url = new URL(value);
      if (!['arxiv.org', 'www.arxiv.org'].includes(url.hostname) || url.username || url.password || url.port || url.search || url.hash) throw new Error('Enter an arxiv.org abs or pdf link.');
      if (!/^\/(abs|pdf)\//.test(url.pathname)) throw new Error('Enter an arXiv abs or pdf link.');
      value = url.pathname.replace(/^\/(abs|pdf)\//, '').replace(/\.pdf$/i, '');
    } else value = value.replace(/^arxiv:\s*/i, '');
    if (!/^(?:\d{4}\.\d{4,5}|[a-z][a-z.\-]+\/\d{7})(?:v[1-9]\d*)?$/i.test(value)) throw new Error('Enter a valid arXiv identifier, such as 1609.07488v2.');
    input.removeAttribute('aria-invalid');
    // Navigation only. The legacy reader still requires explicit form submission.
    location.assign(`/reader.html?arxiv=${encodeURIComponent(value)}`);
  } catch (error) {
    input.setAttribute('aria-invalid', 'true');
    $('#paper-error').textContent = error.message;
    input.focus();
  }
});
$('#paper-input').addEventListener('input', () => {
  $('#paper-input').removeAttribute('aria-invalid');
  $('#paper-error').textContent = '';
});

window.addEventListener('hashchange', route);
initializeMotion(() => {
  if (state.page === 'workspace' && state.view === 'map' && state.data && !document.hidden) enhanceMap($('.map-area'));
});
route();
