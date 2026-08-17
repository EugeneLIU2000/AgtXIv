#!/usr/bin/env python3
"""Validate the static GitHub Pages artifact for the AgtXIv demo."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"Pages validation failed: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_pages_site.py SITE_DIRECTORY")

    site = Path(sys.argv[1]).resolve()
    required = [
        site / ".nojekyll",
        site / "index.html",
        site / "Stabilizerness/MathContractRegistry/demo/index.html",
        site / "Stabilizerness/MathContractRegistry/demo/app.js",
        site / "Stabilizerness/MathContractRegistry/demo/styles.css",
        site / "Stabilizerness/MathContractRegistry/demo/vendor/d3-dag-1.2.2.iife.min.js",
        site / "Stabilizerness/MathContractRegistry/demo/data/claim-dag.en.json",
        site / "Stabilizerness/MathContractRegistry/contracts/contracts.json",
        site / "Stabilizerness/dag/claim-dag.json",
        site / "graph/paper-dependencies.json",
        site / "formal/AgtXIvStabilizerness/verification-result.json",
        site / "Stabilizerness/MathContractRegistry/schema/dependency-edge-evidence.schema.json",
    ]
    missing = [str(path.relative_to(site)) for path in required if not path.is_file()]
    if missing:
        fail(f"missing required files: {missing}")

    contracts_path = site / "Stabilizerness/MathContractRegistry/contracts/contracts.json"
    contracts_document = json.loads(contracts_path.read_text(encoding="utf-8"))
    contracts = contracts_document.get("contracts", [])
    if len(contracts) != 74:
        fail(f"expected 74 Registry contracts, found {len(contracts)}")

    resolution_states = {
        "NOT_APPLICABLE",
        "SOURCE_FOUND_AND_VERIFIED",
        "INDEPENDENT_LEAN_PROOF_COMPLETED",
        "BLOCKING_UNRESOLVED_CLAIM",
    }
    unresolved = []
    for contract in contracts:
        resolution = contract.get("external_resolution")
        if not resolution or resolution.get("status") not in resolution_states:
            fail(f"contract lacks a valid external resolution state: {contract['dag_node_id']}")
        if resolution["status"] == "BLOCKING_UNRESOLVED_CLAIM":
            unresolved.append(contract)
            if contract["paper_agent"] != "UNMAPPED":
                fail(f"unresolved source was converted into an Agent: {contract['dag_node_id']}")
            if resolution.get("effect") != "BLOCKS_DAG_COMPLETION_WHEN_REQUIRED":
                fail(f"unresolved source does not block DAG completion: {contract['dag_node_id']}")
    if len(unresolved) != 8:
        fail(f"expected 8 unresolved external mathematical sources, found {len(unresolved)}")

    green = [
        contract
        for contract in contracts
        if contract["lean_binding"]["status"] == "EXISTING_PROJECT_DECLARATIONS"
    ]
    if not green:
        fail("no verified claim links were found")

    linked_modules: set[str] = set()
    for contract in green:
        modules = contract["lean_binding"].get("modules", [])
        if not modules:
            fail(f"verified claim has no Lean source link: {contract['dag_node_id']}")
        for module in modules:
            linked_modules.add(module)
            if not (site / module).is_file():
                fail(f"published Lean source is missing: {module}")

    demo_dag = json.loads(required[6].read_text(encoding="utf-8"))
    canonical_dag = json.loads(required[8].read_text(encoding="utf-8"))
    if demo_dag.get("graph_view") != "ORACLE_CANDIDATE":
        fail("the demo DAG does not declare the Oracle candidate graph view")
    if demo_dag.get("edges") != canonical_dag.get("edges"):
        fail("the demo edge projection does not match the canonical DAG")

    allowed_dispositions = {
        "CANDIDATE",
        "ACCEPTED",
        "CONDITIONAL",
        "REJECTED",
        "REDUNDANT_IN_QUERY_VIEW",
        "BLOCKED",
        "DISPUTED",
    }
    for edge in demo_dag.get("edges", []):
        evidence = edge.get("evidence")
        pair = f"{edge.get('from')}->{edge.get('to')}"
        if not evidence:
            fail(f"dependency edge lacks evidence: {pair}")
        if evidence.get("oracle_status") != "ORACLE_PROPOSED":
            fail(f"dependency edge lost Oracle provenance: {pair}")
        if evidence.get("disposition") not in allowed_dispositions:
            fail(f"dependency edge has invalid disposition: {pair}")
        if not evidence.get("source_alignment") or not evidence.get("lean_support"):
            fail(f"dependency edge has incomplete evidence axes: {pair}")

    contract_map = {
        contract["dag_node_id"]: contract
        for contract in contracts
        if contract["interface_class"] != "NON_MATHEMATICAL"
    }
    mathematics_edges = [
        edge
        for edge in demo_dag["edges"]
        if edge["from"] in contract_map and edge["to"] in contract_map
    ]
    if len(contract_map) != 65 or len(mathematics_edges) != 114:
        fail(
            "unexpected mathematics projection size: "
            f"interfaces={len(contract_map)} edges={len(mathematics_edges)}"
        )

    incoming: dict[str, list[dict[str, object]]] = {}
    for edge in mathematics_edges:
        incoming.setdefault(edge["to"], []).append(edge)
    target = "claim:closed-form-rom"
    closure = {target}
    frontier = [target]
    while frontier:
        node = frontier.pop()
        for edge in incoming.get(node, []):
            if edge["from"] not in closure:
                closure.add(edge["from"])
                frontier.append(edge["from"])

    closure_contracts = [contract_map[node] for node in closure]
    closure_unresolved = [
        contract
        for contract in closure_contracts
        if contract["external_resolution"]["status"] == "BLOCKING_UNRESOLVED_CLAIM"
    ]
    closure_blocker_references = [
        blocker
        for contract in closure_contracts
        for blocker in contract.get("blocker_ids", [])
    ]
    closure_blockers = set(closure_blocker_references)
    closure_edges = [
        edge
        for edge in mathematics_edges
        if edge["from"] in closure and edge["to"] in closure
    ]
    expected_unresolved = {
        "foundation:finite-lp-strong-duality",
        "root:perfect-graph-weighted-duality",
    }
    if len(closure) != 29 or len(closure_edges) != 45:
        fail(
            "default query closure changed unexpectedly: "
            f"interfaces={len(closure)} edges={len(closure_edges)}"
        )
    closure_status_counts: dict[str, int] = {}
    for contract in closure_contracts:
        status = contract["lean_binding"]["status"]
        closure_status_counts[status] = closure_status_counts.get(status, 0) + 1
    expected_status_counts = {
        "EXISTING_PROJECT_DECLARATIONS": 10,
        "GAP": 15,
        "PLANNED_DELTA": 2,
        "EXTERNAL_OR_UNMAPPED": 2,
    }
    if closure_status_counts != expected_status_counts:
        fail(f"default query status counts changed unexpectedly: {closure_status_counts}")
    if any(edge["evidence"]["disposition"] != "CANDIDATE" for edge in closure_edges):
        fail("default query should remain entirely Oracle-candidate at edge level")
    if {contract["dag_node_id"] for contract in closure_unresolved} != expected_unresolved:
        fail("default query unresolved frontier is incorrect")
    if len(closure_blockers) != 7 or len(closure_blocker_references) != 10:
        fail(
            "default query blocker surface changed unexpectedly: "
            f"unique={len(closure_blockers)} references={len(closure_blocker_references)}"
        )

    forbidden_parts = {".lake", ".tools", "__pycache__"}
    for path in site.rglob("*"):
        if any(part in forbidden_parts for part in path.parts):
            fail(f"forbidden cache path was published: {path.relative_to(site)}")
        if path.is_file() and path.stat().st_size >= 100 * 1024 * 1024:
            fail(f"file exceeds the GitHub 100 MiB limit: {path.relative_to(site)}")

    demo_html = required[2].read_text(encoding="utf-8")
    demo_js = required[3].read_text(encoding="utf-8")
    demo_css = required[4].read_text(encoding="utf-8")
    if "vendor/d3-dag-1.2.2.iife.min.js" not in demo_html:
        fail("the demo does not load the vendored d3-dag bundle")

    semantic_highlight_tokens = [
        "activeClaimArrow",
        "activeDefinitionArrow",
        "activeScopeArrow",
        "dependencyMarker(link.dataset.type, active)",
    ]
    missing_tokens = [token for token in semantic_highlight_tokens if token not in demo_js]
    if missing_tokens:
        fail(f"highlighting does not preserve dependency markers: {missing_tokens}")

    active_edge_selectors = [
        ".dependency-link.scientific_claim_dependency.query-active",
        ".dependency-link.definition_dependency.query-active",
        ".dependency-link.scope_dependency.query-active",
    ]
    missing_selectors = [selector for selector in active_edge_selectors if selector not in demo_css]
    if missing_selectors:
        fail(f"highlighting does not preserve dependency styles: {missing_selectors}")

    required_pipeline_ui = [
        "Graph view: ORACLE CANDIDATE",
        "queryStatusPanel",
        "Unresolved external source",
        "Lean-linked",
        "UEMS",
    ]
    missing_ui = [token for token in required_pipeline_ui if token not in demo_html]
    if missing_ui:
        fail(f"the demo lacks required pipeline state UI: {missing_ui}")

    required_pipeline_logic = [
        "validateContractPipelineState",
        "BLOCKING_UNRESOLVED_CLAIM",
        "renderQueryState",
        "DAGComplete",
        "VerificationClosed",
        "candidate_reuse",
        "blocker_ids",
    ]
    missing_logic = [token for token in required_pipeline_logic if token not in demo_js]
    if missing_logic:
        fail(f"the demo lacks required pipeline state logic: {missing_logic}")

    forbidden_ui = ["External Mathematical Root", "profile-agent:", "% verified"]
    present_forbidden = [token for token in forbidden_ui if token in demo_js or token in demo_html]
    if present_forbidden:
        fail(f"the demo retains misleading virtual-agent or verification labels: {present_forbidden}")

    print(
        "PAGES_SITE_VALIDATION=PASS "
        f"contracts={len(contracts)} "
        f"lean_linked_claims={len(green)} "
        f"lean_modules={len(linked_modules)} "
        f"unresolved_sources={len(unresolved)} "
        f"default_query_unresolved={len(closure_unresolved)} "
        f"default_query_gap={closure_status_counts['GAP']} "
        f"default_query_planned={closure_status_counts['PLANNED_DELTA']} "
        f"default_query_blockers={len(closure_blockers)}"
    )


if __name__ == "__main__":
    main()
