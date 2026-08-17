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
    ]
    missing = [str(path.relative_to(site)) for path in required if not path.is_file()]
    if missing:
        fail(f"missing required files: {missing}")

    contracts_path = site / "Stabilizerness/MathContractRegistry/contracts/contracts.json"
    contracts_document = json.loads(contracts_path.read_text(encoding="utf-8"))
    contracts = contracts_document.get("contracts", [])
    if len(contracts) != 74:
        fail(f"expected 74 Registry contracts, found {len(contracts)}")

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

    print(
        "PAGES_SITE_VALIDATION=PASS "
        f"contracts={len(contracts)} "
        f"verified_claims={len(green)} "
        f"lean_modules={len(linked_modules)}"
    )


if __name__ == "__main__":
    main()
