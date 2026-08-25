from __future__ import annotations

import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.export_scientific_claim_demo as exporter


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append((tag, values[attribute]))


class ScientificClaimDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generated = exporter.build_demo_data()
        cls.committed = json.loads(exporter.OUTPUT.read_text(encoding="utf-8"))
        cls.demo = exporter.ROOT / "demo_design/scientific_claims"
        cls.html = (cls.demo / "index.html").read_text(encoding="utf-8")
        cls.javascript = (cls.demo / "app.js").read_text(encoding="utf-8")
        cls.css = (cls.demo / "styles.css").read_text(encoding="utf-8")

    def test_export_is_deterministic_and_matches_committed_json(self) -> None:
        first = exporter.serialize(exporter.build_demo_data())
        second = exporter.serialize(exporter.build_demo_data())
        self.assertEqual(first, second)
        self.assertEqual(first, exporter.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(self.generated, self.committed)

    def test_export_contains_exactly_the_two_current_paper_claims(self) -> None:
        bundles = self.generated["claims"]
        self.assertEqual(len(bundles), 2)
        self.assertEqual({bundle["claim"]["paper_id"] for bundle in bundles}, {exporter.PAPER_ID})
        self.assertEqual({bundle["claim"]["claim_role"] for bundle in bundles}, {"CONTRIBUTION"})
        self.assertEqual(
            {bundle["claim"]["id"] for bundle in bundles},
            {
                "claim:graph-theoretic-nonstabilizerness:perfect-graph-closed-form",
                "claim:graph-theoretic-nonstabilizerness:sign-relaxation-exactness",
            },
        )

    def test_claim_references_resolve_exact_revision_hash_and_artifact(self) -> None:
        for bundle in self.generated["claims"]:
            claim = bundle["claim"]
            for record in (bundle["calibration"], bundle["support_association"]):
                reference = record["scientific_claim_ref"]
                self.assertEqual(reference["target_id"], claim["id"])
                self.assertEqual(reference["target_revision"], claim["record_revision"])
                self.assertEqual(reference["target_content_hash"], claim["content_hash"])
                self.assertEqual(reference["target_artifact"], claim["artifact"])
            navigation = bundle["support_association"]["navigation_basis_ref"]
            self.assertEqual(navigation["target_id"], claim["id"])
            self.assertEqual(navigation["component_path"], "/facets")
            self.assertIsNone(navigation["target_artifact"])

    def test_every_facet_has_one_outcome_and_at_least_one_support_link(self) -> None:
        for bundle in self.generated["claims"]:
            facet_ids = {facet["facet_id"] for facet in bundle["claim"]["facets"]}
            association = bundle["support_association"]
            outcome_ids = [outcome["facet_id"] for outcome in association["facet_outcomes"]]
            linked_ids = {link["facet_id"] for link in association["links"]}
            self.assertEqual(len(outcome_ids), len(set(outcome_ids)))
            self.assertEqual(set(outcome_ids), facet_ids)
            self.assertEqual(linked_ids, facet_ids)

    def test_mathematical_support_never_targets_a_scientific_claim(self) -> None:
        allowed = {"org.agtxiv.claim_ir", "org.agtxiv.mathematical_proposition_ir"}
        for bundle in self.generated["claims"]:
            for link in bundle["support_association"]["links"]:
                reference = link["target_ref"]
                self.assertIn(reference["target_kind"], allowed)
                self.assertFalse(reference["target_id"].startswith("claim:"))

    def test_detail_panels_follow_facet_source_calibration_support_order(self) -> None:
        positions = [
            self.html.index('id="facetTitle"'),
            self.html.index('id="evidenceTitle"'),
            self.html.index('id="calibrationTitle"'),
            self.html.index('id="supportTitle"'),
        ]
        self.assertEqual(positions, sorted(positions))
        for number, title in (("01", "facetTitle"), ("02", "evidenceTitle"), ("03", "calibrationTitle"), ("04", "supportTitle")):
            heading = self.html.rfind('<div class="panel-heading">', 0, self.html.index(f'id="{title}"'))
            self.assertIn(f'<span class="panel-number">{number}</span>', self.html[heading:self.html.index(f'id="{title}"')])

    def test_selection_loading_and_history_accessibility_contracts_are_present(self) -> None:
        self.assertIn('id="claimWorkspace" aria-labelledby="workspaceTitle" aria-busy="true"', self.html)
        self.assertIn('id="loadStatus" role="status"', self.html)
        self.assertIn("[hidden] { display: none !important; }", self.css)
        self.assertIn('id="retryButton"', self.html)
        self.assertIn('id="claimRecord" role="tabpanel" tabindex="0"', self.html)
        self.assertIn('role="radiogroup"', self.html)
        self.assertIn('button.setAttribute("role", "radio")', self.javascript)
        self.assertIn('button.setAttribute("aria-checked"', self.javascript)
        self.assertNotIn('aria-pressed', self.javascript)
        self.assertIn('setAttribute("aria-labelledby", `claim-tab-${state.claimIndex}`)', self.javascript)
        self.assertIn('history.pushState', self.javascript)
        self.assertIn('history.replaceState', self.javascript)
        self.assertIn('window.addEventListener("popstate", applyLocation)', self.javascript)
        self.assertIn('writeSelection("replace")', self.javascript)

    def test_navigation_wording_and_source_treatment_do_not_imply_verification(self) -> None:
        combined = self.html + self.javascript
        self.assertNotIn("COMPLETE COVERAGE", combined)
        self.assertNotIn("is-context", combined)
        self.assertIn("PROVISIONAL NAVIGATION ·", self.javascript)
        self.assertIn("Provisional facet navigation", combined)
        self.assertIn("Shared across this claim’s facets", self.html)
        self.assertIn("not query-specific coverage or mathematical verification", self.html)
        self.assertIn("font-size: 12.5px", self.css)
        self.assertIn("width: min(100%, 78ch)", self.css)
        self.assertIn(".metadata-list dd", self.css)
        self.assertIn("font-size: 12px", self.css)

    def test_html_internal_links_and_assets_resolve_without_network_dependencies(self) -> None:
        parser = AssetParser()
        parser.feed(self.html)
        references = {value for _, value in parser.references}
        self.assertIn("../assets/agentxiv-logo.svg", references)
        self.assertIn("styles.css", references)
        self.assertIn("app.js", references)
        self.assertIn(exporter.OUTPUT.name, self.javascript)
        for _, reference in parser.references:
            self.assertFalse(reference.startswith(("http://", "https://", "//")))
            if reference.startswith("#"):
                self.assertIn(reference[1:], parser.ids)
            else:
                path = (self.demo / reference.split("#", 1)[0]).resolve()
                self.assertTrue(path.is_file(), f"missing demo asset: {reference}")


if __name__ == "__main__":
    unittest.main()
