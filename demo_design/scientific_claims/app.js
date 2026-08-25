(() => {
  "use strict";

  const DATA_URL = "data/graph-theoretic-scientific-claims.json";
  const FROZEN_PAPER_ID = "arxiv:2607.26154v1";
  const COVERAGE_STATES = new Set(["NONE", "PARTIAL", "COMPLETE"]);
  const state = { data: null, claimIndex: 0, facetId: null };
  const byId = (id) => document.getElementById(id);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function requireData(condition, message) {
    if (!condition) throw new Error(message);
  }

  function validateDemoData(data) {
    requireData(data && typeof data === "object", "The frozen demo export is not a JSON object.");
    requireData(data.paper?.id === FROZEN_PAPER_ID, `The frozen demo must describe exactly ${FROZEN_PAPER_ID}.`);
    requireData(Array.isArray(data.claims) && data.claims.length === 2, `The frozen ${FROZEN_PAPER_ID} demo requires exactly two ScientificClaims.`);
    requireData(data.architecture?.calibration_direction && data.architecture?.verification_boundary, "The frozen demo export is missing architecture boundary metadata.");

    const claimIds = new Set();
    data.claims.forEach((bundle, bundleIndex) => {
      const label = `ScientificClaim bundle ${bundleIndex + 1}`;
      const claim = bundle?.claim;
      const association = bundle?.support_association;
      requireData(claim?.paper_id === FROZEN_PAPER_ID && typeof claim.id === "string", `${label} has an invalid paper or claim identity.`);
      requireData(!claimIds.has(claim.id), `${label} duplicates claim ID ${claim.id}.`);
      claimIds.add(claim.id);
      requireData(Array.isArray(claim.facets) && claim.facets.length > 0, `${claim.id} has no selectable facets.`);
      const facetIds = claim.facets.map((facet) => facet?.facet_id);
      requireData(facetIds.every((id) => typeof id === "string") && new Set(facetIds).size === facetIds.length, `${claim.id} has missing or duplicate facet IDs.`);
      requireData(Array.isArray(claim.occurrences), `${claim.id} has no source occurrence list.`);
      requireData(bundle.calibration?.relation_direction === "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM", `${claim.id} has an invalid calibration direction.`);
      requireData(Array.isArray(association?.facet_outcomes), `${claim.id} has no facet outcomes.`);
      requireData(Array.isArray(association?.links), `${claim.id} has no support-link list.`);

      const outcomeIds = association.facet_outcomes.map((outcome) => outcome?.facet_id);
      requireData(outcomeIds.length === facetIds.length && new Set(outcomeIds).size === facetIds.length && facetIds.every((id) => outcomeIds.includes(id)), `${claim.id} must have exactly one outcome for every facet.`);
      association.facet_outcomes.forEach((outcome) => requireData(COVERAGE_STATES.has(outcome.coverage), `${claim.id} has an invalid provisional navigation state.`));
      association.links.forEach((link) => {
        requireData(facetIds.includes(link?.facet_id), `${claim.id} has a support link with a dangling facet.`);
        requireData(COVERAGE_STATES.has(link?.facet_coverage), `${claim.id} has a support link with an invalid provisional navigation state.`);
        requireData(["org.agtxiv.claim_ir", "org.agtxiv.mathematical_proposition_ir"].includes(link?.target_ref?.target_kind), `${claim.id} has an unsupported mathematical navigation target.`);
        requireData(link.target_ref.target_artifact && typeof link.target_ref.target_artifact.artifact_hash === "string", `${claim.id} has a mathematical navigation target without an immutable artifact.`);
      });
    });
  }

  function shortHash(value) {
    if (!value) return "—";
    const [algorithm, digest = ""] = value.split(":", 2);
    return `${algorithm}:${digest.slice(0, 10)}…${digest.slice(-5)}`;
  }

  function displayCode(value) {
    return String(value || "—").replace(/^org\.agtxiv\./, "");
  }

  function hashDetail(label, value) {
    const details = element("details", "hash-detail");
    const summary = document.createElement("summary");
    summary.append(element("span", "", label), document.createTextNode(shortHash(value)));
    details.append(summary, element("code", "", value || "—"));
    return details;
  }

  function addMetadata(list, label, value) {
    const wrapper = document.createElement("div");
    wrapper.append(element("dt", "", label), element("dd", "", value));
    list.append(wrapper);
  }

  function currentBundle() {
    return state.data.claims[state.claimIndex];
  }

  function claimLabel(claim) {
    if (claim.id.endsWith("sign-relaxation-exactness")) return "Sign-relaxation exactness";
    if (claim.id.endsWith("perfect-graph-closed-form")) return "Perfect-graph closed form";
    return claim.id;
  }

  function readHash() {
    const params = new URLSearchParams(window.location.hash.slice(1));
    return { claimId: params.get("claim"), facetId: params.get("facet") };
  }

  function canonicalHash() {
    const claim = currentBundle().claim;
    return `#${new URLSearchParams({ claim: claim.id, facet: state.facetId }).toString()}`;
  }

  function writeSelection(mode) {
    const next = canonicalHash();
    if (window.location.hash === next) return;
    if (mode === "push") history.pushState(null, "", next);
    else history.replaceState(null, "", next);
  }

  function normalizedSelectionFromHash() {
    const requested = readHash();
    const requestedIndex = state.data.claims.findIndex((bundle) => bundle.claim.id === requested.claimId);
    const claimIndex = requestedIndex >= 0 ? requestedIndex : 0;
    const claim = state.data.claims[claimIndex].claim;
    const facetId = claim.facets.some((facet) => facet.facet_id === requested.facetId) ? requested.facetId : claim.facets[0].facet_id;
    return {
      claimIndex,
      facetId,
      normalized: requestedIndex < 0 || facetId !== requested.facetId,
    };
  }

  function renderArchitecture() {
    const { data } = state;
    byId("paperTitle").textContent = data.paper.title;
    byId("paperAuthors").textContent = data.paper.authors.join(" · ");
    byId("paperId").textContent = data.paper.id;
    byId("paperSource").textContent = data.paper.source_path;
    byId("sourceRevision").textContent = data.source_revision;

    const list = byId("layerList");
    list.replaceChildren();
    data.architecture.layers.forEach((layer) => {
      const item = document.createElement("li");
      item.append(element("strong", "", layer.label), element("p", "", layer.description));
      list.append(item);
    });

    byId("calibrationDirection").textContent = data.architecture.calibration_direction.code;
    byId("calibrationExplanation").textContent = data.architecture.calibration_direction.explanation;
    byId("boundaryAvailable").textContent = data.architecture.verification_boundary.available;
    byId("boundaryPending").replaceChildren(...data.architecture.verification_boundary.pending.map((text) => element("li", "", text)));
  }

  function updateTabs() {
    document.querySelectorAll(".claim-tab").forEach((tab, index) => {
      const selected = index === state.claimIndex;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    byId("claimRecord").setAttribute("aria-labelledby", `claim-tab-${state.claimIndex}`);
  }

  function activateClaim(index, options = {}) {
    const { historyMode = "push", focusTab = false, facetId = null } = options;
    const changed = index !== state.claimIndex;
    state.claimIndex = index;
    const claim = currentBundle().claim;
    state.facetId = claim.facets.some((facet) => facet.facet_id === facetId) ? facetId : claim.facets[0].facet_id;
    renderClaim();
    if (historyMode) writeSelection(historyMode);
    if (focusTab) byId(`claim-tab-${index}`).focus();
    return changed;
  }

  function renderTabs() {
    const container = byId("claimTabs");
    container.replaceChildren();
    state.data.claims.forEach((bundle, index) => {
      const claim = bundle.claim;
      const button = element("button", "claim-tab");
      button.type = "button";
      button.id = `claim-tab-${index}`;
      button.setAttribute("role", "tab");
      button.setAttribute("aria-controls", "claimRecord");
      const copy = element("span", "tab-copy");
      copy.append(element("strong", "", claimLabel(claim)), element("small", "", claim.id));
      button.append(element("span", "tab-number", String(index + 1).padStart(2, "0")), copy, element("span", "tab-arrow", "→"));
      button.addEventListener("click", () => {
        if (index !== state.claimIndex) activateClaim(index);
      });
      button.addEventListener("keydown", (event) => {
        let next = null;
        if (["ArrowRight", "ArrowDown"].includes(event.key)) next = (index + 1) % state.data.claims.length;
        if (["ArrowLeft", "ArrowUp"].includes(event.key)) next = (index - 1 + state.data.claims.length) % state.data.claims.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = state.data.claims.length - 1;
        if (next === null) return;
        event.preventDefault();
        if (next === state.claimIndex) byId(`claim-tab-${next}`).focus();
        else activateClaim(next, { focusTab: true });
      });
      container.append(button);
    });
    updateTabs();
  }

  function renderIdentity(claim) {
    byId("claimIndex").textContent = String(state.claimIndex + 1).padStart(2, "0");
    byId("claimRole").textContent = `ROLE · ${claim.claim_role}`;
    byId("claimGranularity").textContent = claim.granularity;
    byId("claimRevision").textContent = `REVISION ${claim.record_revision}`;
    byId("claimStatement").textContent = claim.normalized_statement;
    byId("claimId").textContent = claim.id;

    const metadata = byId("claimMetadata");
    metadata.replaceChildren();
    addMetadata(metadata, "Stable neutral ID", claim.id);
    addMetadata(metadata, "Role", claim.claim_role);
    addMetadata(metadata, "Granularity", claim.granularity);
    addMetadata(metadata, "Contribution kind", claim.contribution_kind);
    addMetadata(metadata, "Contribution tags", claim.contribution_tags.join(" · "));
    addMetadata(metadata, "Current revision", String(claim.record_revision));
    addMetadata(metadata, "Produced at", claim.produced_at);
    addMetadata(metadata, "Source characterization", Object.entries(claim.source_characterization).map(([key, value]) => `${key}: ${value}`).join(" · "));

    byId("scopeHints").replaceChildren(...claim.scope_hints.map((hint) => element("li", "", hint)));
    byId("claimHashes").replaceChildren(
      hashDetail("Semantic", claim.semantic_content_hash),
      hashDetail("Artifact", claim.artifact.artifact_hash),
      hashDetail("Content", claim.content_hash),
    );
  }

  function updateFacetRadios() {
    document.querySelectorAll(".facet-button").forEach((button) => {
      const selected = button.dataset.facetId === state.facetId;
      button.setAttribute("aria-checked", String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
  }

  function activateFacet(facetId, options = {}) {
    const { historyMode = "push", focusFacet = false } = options;
    if (!currentBundle().claim.facets.some((facet) => facet.facet_id === facetId)) return;
    const changed = facetId !== state.facetId;
    state.facetId = facetId;
    updateFacetRadios();
    renderSupport();
    if (changed && historyMode) writeSelection(historyMode);
    if (focusFacet) document.querySelector(`[data-facet-index="${currentBundle().claim.facets.findIndex((facet) => facet.facet_id === facetId)}"]`).focus();
  }

  function renderFacets() {
    const facets = currentBundle().claim.facets;
    const list = byId("facetList");
    list.replaceChildren();
    facets.forEach((facet, index) => {
      const button = element("button", "facet-button");
      button.type = "button";
      button.dataset.facetId = facet.facet_id;
      button.dataset.facetIndex = String(index);
      button.setAttribute("role", "radio");
      button.append(
        element("small", "", facet.facet_id),
        element("strong", "", facet.statement),
        element("span", "", displayCode(facet.facet_kind)),
      );
      button.addEventListener("click", () => activateFacet(facet.facet_id));
      button.addEventListener("keydown", (event) => {
        let next = null;
        if (["ArrowRight", "ArrowDown"].includes(event.key)) next = (index + 1) % facets.length;
        if (["ArrowLeft", "ArrowUp"].includes(event.key)) next = (index - 1 + facets.length) % facets.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = facets.length - 1;
        if (next === null) return;
        event.preventDefault();
        activateFacet(facets[next].facet_id, { focusFacet: true });
      });
      list.append(button);
    });
    updateFacetRadios();
  }

  function targetType(kind) {
    if (kind === "org.agtxiv.claim_ir") return "MathClaimIR";
    if (kind === "org.agtxiv.mathematical_proposition_ir") return "MathematicalPropositionIR";
    return kind;
  }

  function navigationLabel(value) {
    return `PROVISIONAL NAVIGATION · ${value}`;
  }

  function supportCard(link) {
    const reference = link.target_ref;
    const card = element("article", "support-card");
    const header = document.createElement("header");
    header.append(
      element("span", "target-type", targetType(reference.target_kind)),
      element("span", "relationship", link.relationship),
      element("span", `link-coverage ${link.facet_coverage.toLowerCase()}`, navigationLabel(link.facet_coverage)),
    );
    const coordinates = element("dl", "target-coordinates");
    addMetadata(coordinates, "Target kind", reference.target_kind);
    addMetadata(coordinates, "Revision", String(reference.target_revision));
    addMetadata(coordinates, "Content hash", reference.target_content_hash);
    addMetadata(coordinates, "Artifact hash", reference.target_artifact.artifact_hash);
    addMetadata(coordinates, "Schema", `${reference.target_artifact.schema_uri} · ${reference.target_artifact.schema_version}`);
    addMetadata(coordinates, "Serialization", `${reference.target_artifact.serialization_profile.id} · ${reference.target_artifact.serialization_profile.content_hash}`);
    const artifact = element("details", "artifact-details");
    artifact.append(element("summary", "", "View exact target artifact"), element("pre", "", JSON.stringify(reference.target_artifact, null, 2)));
    card.append(header, element("h5", "", reference.target_id), coordinates, artifact);
    return card;
  }

  function renderSupport() {
    const bundle = currentBundle();
    const claim = bundle.claim;
    const association = bundle.support_association;
    const facet = claim.facets.find((item) => item.facet_id === state.facetId);
    const outcome = association.facet_outcomes.find((item) => item.facet_id === state.facetId);
    const links = association.links.filter((link) => link.facet_id === state.facetId);
    byId("selectedFacetStatement").textContent = facet.statement;
    const pill = byId("facetOutcome");
    pill.textContent = navigationLabel(outcome.coverage);
    pill.className = `coverage-pill ${outcome.coverage.toLowerCase()}`;
    const summary = byId("supportSummary");
    summary.replaceChildren();
    addMetadata(summary, "Association scope", association.association_scope);
    addMetadata(summary, "Provisional facet navigation", association.provisional_facet_coverage.toLowerCase());
    addMetadata(summary, "Reason codes", association.reason_codes.join(" · "));
    byId("supportLinks").replaceChildren(...(links.length ? links.map(supportCard) : [element("p", "empty-support", "No mathematical navigation target is currently associated with this facet.")]));
  }

  function occurrenceCard(occurrence) {
    const card = element("article", "occurrence-card");
    const header = document.createElement("header");
    header.append(
      element("span", "occurrence-role", occurrence.occurrence_role),
      element("span", "occurrence-zone", occurrence.source_zone),
      element("span", "line-range", `LINES ${occurrence.line_start}–${occurrence.line_end}`),
    );
    const meta = element("div", "occurrence-meta");
    [
      ["Source path", occurrence.source_artifact.path],
      ["Speech act", occurrence.source_characterization.speech_act],
      ["Formality", occurrence.source_characterization.formality],
      ["Conditionality", occurrence.source_characterization.conditionality],
      ["Source SHA-256", occurrence.source_artifact.sha256],
      ["Occurrence ID", occurrence.id],
    ].forEach(([label, value]) => {
      const item = document.createElement("div");
      item.append(element("span", "", label), element("code", "", value));
      meta.append(item);
    });
    const details = element("details", "source-details");
    details.append(element("summary", "", "Verbatim source text"), element("pre", "", occurrence.source_text));
    card.append(header, meta, details);
    return card;
  }

  function renderOccurrences() {
    byId("occurrenceList").replaceChildren(...currentBundle().claim.occurrences.map(occurrenceCard));
  }

  function renderCalibration() {
    const calibration = currentBundle().calibration;
    const grid = byId("calibrationGrid");
    grid.replaceChildren();
    [
      ["Primary → normalized", calibration.primary_to_normalized_relation],
      ["Body → normalized", calibration.body_to_normalized_relation],
      ["Stage", calibration.calibration_stage],
      ["Reason codes", calibration.reason_codes.join(" · ")],
      ["Record", `${calibration.id} · revision ${calibration.record_revision}`],
    ].forEach(([label, value]) => {
      const item = element("div", "calibration-item");
      item.append(element("span", "", label), element("code", "", value));
      grid.append(item);
    });
  }

  function renderClaim() {
    updateTabs();
    renderIdentity(currentBundle().claim);
    renderFacets();
    renderOccurrences();
    renderCalibration();
    renderSupport();
    byId("claimRecord").hidden = false;
  }

  function applyLocation() {
    if (!state.data) return;
    const selection = normalizedSelectionFromHash();
    if (selection.claimIndex !== state.claimIndex) {
      activateClaim(selection.claimIndex, { historyMode: null, facetId: selection.facetId });
    } else if (selection.facetId !== state.facetId) {
      activateFacet(selection.facetId, { historyMode: null });
    }
    if (selection.normalized || window.location.hash !== canonicalHash()) writeSelection("replace");
  }

  function setLoading() {
    state.data = null;
    byId("claimWorkspace").setAttribute("aria-busy", "true");
    byId("loadStatus").hidden = false;
    byId("loadError").hidden = true;
    byId("retryButton").disabled = true;
  }

  function finishLoading() {
    byId("claimWorkspace").removeAttribute("aria-busy");
    byId("loadStatus").hidden = true;
    byId("retryButton").disabled = false;
  }

  function showLoadError(error) {
    finishLoading();
    byId("claimRecord").hidden = true;
    byId("claimTabs").replaceChildren();
    byId("loadErrorMessage").textContent = `${error.message} This frozen demo uses a local generated file; serve the repository root with the preview command in README.md, then retry.`;
    byId("loadError").hidden = false;
  }

  async function initialize() {
    setLoading();
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`The frozen demo data request failed with HTTP ${response.status}.`);
      const data = await response.json();
      validateDemoData(data);
      state.data = data;
      const selection = normalizedSelectionFromHash();
      state.claimIndex = selection.claimIndex;
      state.facetId = selection.facetId;
      renderArchitecture();
      renderTabs();
      renderClaim();
      writeSelection("replace");
      byId("loadError").hidden = true;
      finishLoading();
    } catch (error) {
      const message = error instanceof Error ? error : new Error("The frozen demo data could not be loaded.");
      showLoadError(message);
    }
  }

  byId("retryButton").addEventListener("click", initialize);
  window.addEventListener("popstate", applyLocation);
  window.addEventListener("hashchange", applyLocation);
  initialize();
})();
