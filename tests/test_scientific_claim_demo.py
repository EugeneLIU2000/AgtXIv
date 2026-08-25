from __future__ import annotations

import copy
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
        cls.committed_text = exporter.OUTPUT.read_text(encoding="utf-8")
        cls.committed = json.loads(cls.committed_text)
        cls.graph = cls.generated["graph"]
        cls.nodes = {node["id"]: node for node in cls.graph["nodes"]}
        cls.demo = exporter.ROOT / "demo_design/scientific_claims"
        cls.html = (cls.demo / "index.html").read_text(encoding="utf-8")
        cls.javascript = (cls.demo / "app.js").read_text(encoding="utf-8")
        cls.css = (cls.demo / "styles.css").read_text(encoding="utf-8")

    def test_export_is_deterministic_and_matches_committed_graph_payload(self) -> None:
        first = exporter.serialize(exporter.build_demo_data())
        second = exporter.serialize(exporter.build_demo_data())
        self.assertEqual(first, second)
        self.assertEqual(first, self.committed_text)
        self.assertEqual(self.generated, self.committed)
        self.assertEqual(self.generated["schema"], "agtxiv.scientific-claim-demo/2.0.0")

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

    def test_graph_has_typed_nodes_and_persistent_color_legend(self) -> None:
        actual_types = {node["type"] for node in self.graph["nodes"]}
        self.assertEqual(actual_types, exporter.GRAPH_NODE_TYPES - {"mathematical_proposition_ir"})
        for class_name in ("paper", "contribution", "facet", "formal", "occurrence", "math", "proposition"):
            self.assertIn(f'class="glyph-swatch {class_name}"', self.html)
        for variable in ("--navy", "--blue", "--cyan", "--formal", "--occurrence", "--purple", "--orange"):
            self.assertIn(variable, self.css)
        self.assertIn("MathematicalPropositionIR", self.html)

    def test_circle_glyphs_use_the_new_demo_palette(self) -> None:
        expected_palette = {
            "--navy": "#0b1527",
            "--blue": "#2457f5",
            "--cyan": "#0d9fc2",
            "--formal": "#657286",
            "--occurrence": "#9ba7b8",
            "--purple": "#7653c6",
            "--orange": "#dc7629",
        }
        for variable, value in expected_palette.items():
            self.assertIn(f"{variable}: {value}", self.css)
        self.assertIn(".graph-node.paper { --node-color: var(--navy); }", self.css)
        self.assertIn(".graph-node.scientific_claim_contribution { --node-color: var(--blue); }", self.css)
        self.assertIn("background-color: #f8fafc", self.css)

    def test_every_graph_node_uses_reference_style_circle_glyphs_and_external_labels(self) -> None:
        renderer = self.javascript.split("function renderNode", 1)[1].split("function clearConnectedHighlight", 1)[0]
        self.assertNotIn('svgElement("rect"', renderer)
        for class_name in (
            "node-hit-area", "agent-progress-track", "agent-outline", "agent-disc",
            "membership-ring", "interface-shell node-shell", "interface-dot node-dot",
            "interface-focus node-focus", "external-node-type", "external-node-label",
            "expand-badge", "expand-badge-shell", "expand-badge-label",
        ):
            self.assertIn(class_name, renderer)
        self.assertIn('role: "button"', renderer)
        self.assertIn('"aria-label": nodeAriaLabel(node)', renderer)
        self.assertIn('"aria-expanded": state.expanded.has(node.id)', renderer)
        self.assertIn("glyph size encodes hierarchy", self.html)

    def test_active_node_neighbors_and_typed_edges_use_reference_highlighting(self) -> None:
        for hook in ("function applyConnectedHighlight", "function restorePinnedHighlight", 'classList.toggle("hover-active"', 'classList.toggle("hover-muted"'):
            self.assertIn(hook, self.javascript)
        for class_name in ("graph-edge-underlay", "edge-group.hover-active", "edge-group.hover-muted", "graph-node.hover-muted", "is-highlight-target"):
            self.assertIn(class_name, self.css + self.javascript)
        self.assertIn("provisional_navigation", self.css)
        self.assertIn("stroke-dasharray: 2 6", self.css)

    def test_initial_graph_is_paper_plus_two_contribution_claims_only(self) -> None:
        initial = self.graph["initial_node_ids"]
        self.assertEqual(len(initial), 3)
        self.assertEqual([self.nodes[node_id]["type"] for node_id in initial], ["paper", "scientific_claim_contribution", "scientific_claim_contribution"])
        self.assertEqual(self.graph["initial_expanded_node_ids"], [initial[0]])

    def test_expansion_edges_encode_claim_facet_source_and_math_progression(self) -> None:
        edges_by_type: dict[str, list[dict]] = {}
        for edge in self.graph["edges"]:
            edges_by_type.setdefault(edge["type"], []).append(edge)
        self.assertEqual(len(edges_by_type["contains"]), 2)
        self.assertEqual(len(edges_by_type["has_facet"]), 4)
        self.assertTrue(edges_by_type["source_calibration"])
        self.assertTrue(edges_by_type["formal_source"])
        self.assertTrue(edges_by_type["provisional_navigation"])
        for edge in edges_by_type["contains"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "paper")
            self.assertEqual(self.nodes[edge["target"]]["type"], "scientific_claim_contribution")
        for edge in edges_by_type["has_facet"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "scientific_claim_contribution")
            self.assertEqual(self.nodes[edge["target"]]["type"], "facet")
        for edge in edges_by_type["source_calibration"] + edges_by_type["formal_source"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "scientific_claim_contribution")
            self.assertIn(self.nodes[edge["target"]]["type"], {"source_occurrence", "scientific_claim_formal"})
        for edge in edges_by_type["provisional_navigation"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "facet")
            self.assertIn(self.nodes[edge["target"]]["type"], {"math_claim_ir", "mathematical_proposition_ir"})
            self.assertTrue(edge["label"].startswith("PROVISIONAL NAVIGATION · "))

    def test_shared_mathematical_targets_are_deduplicated_and_endpoints_resolve(self) -> None:
        support_target_ids = {
            link["target_ref"]["target_id"]
            for bundle in self.generated["claims"]
            for link in bundle["support_association"]["links"]
        }
        mathematical_nodes = [node for node in self.graph["nodes"] if node["type"] in {"math_claim_ir", "mathematical_proposition_ir"}]
        self.assertEqual({node["id"] for node in mathematical_nodes}, support_target_ids)
        self.assertEqual(len(mathematical_nodes), len(support_target_ids))
        self.assertEqual(len(self.nodes), len(self.graph["nodes"]))
        for edge in self.graph["edges"]:
            self.assertIn(edge["source"], self.nodes)
            self.assertIn(edge["target"], self.nodes)

    def test_mathematical_edges_never_target_a_scientific_claim(self) -> None:
        for edge in self.graph["edges"]:
            if edge["type"] != "provisional_navigation":
                continue
            self.assertIn(self.nodes[edge["target"]]["type"], {"math_claim_ir", "mathematical_proposition_ir"})
            self.assertFalse(edge["target"].startswith("claim:"))

    def test_every_node_has_safe_nonempty_markdown_detail(self) -> None:
        unsafe = ("<script", "javascript:", "data:text/html", "onerror=", "onload=")
        for node in self.graph["nodes"]:
            detail = node["detail_markdown"]
            self.assertTrue(detail.startswith("## "))
            self.assertFalse(any(token in detail.lower() for token in unsafe))
            self.assertEqual(detail.count("```") % 2, 0)
        self.assertIn("Verbatim excerpt", "\n".join(node["detail_markdown"] for node in self.graph["nodes"] if node["type"] == "source_occurrence"))
        self.assertIn("Exact artifact", "\n".join(node["detail_markdown"] for node in self.graph["nodes"] if node["type"] == "math_claim_ir"))

    def test_graph_validator_rejects_duplicate_dangling_wrong_target_and_unsafe_markdown(self) -> None:
        cases = []
        duplicate = copy.deepcopy(self.graph)
        duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
        cases.append(duplicate)
        dangling = copy.deepcopy(self.graph)
        dangling["edges"][0]["target"] = "claim:missing"
        cases.append(dangling)
        wrong_target = copy.deepcopy(self.graph)
        support = next(edge for edge in wrong_target["edges"] if edge["type"] == "provisional_navigation")
        support["target"] = wrong_target["initial_node_ids"][1]
        cases.append(wrong_target)
        unsafe = copy.deepcopy(self.graph)
        unsafe["nodes"][0]["detail_markdown"] = "## Bad\n[jump](javascript:alert(1))"
        cases.append(unsafe)
        for graph in cases:
            with self.subTest(case=cases.index(graph)):
                with self.assertRaises(exporter.ExportError):
                    exporter.validate_graph(graph)

    def test_safe_markdown_renderer_escapes_raw_html_and_rejects_unsafe_links(self) -> None:
        self.assertNotIn(".innerHTML", self.javascript)
        self.assertIn("document.createTextNode", self.javascript)
        self.assertIn("function renderMarkdown(markdown)", self.javascript)
        self.assertIn("function isSafeUrl(value)", self.javascript)
        self.assertIn("[unsafe link removed]", self.javascript)
        self.assertIn('window.ScientificClaimDemo = Object.freeze({ isSafeUrl, renderMarkdown })', self.javascript)
        self.assertIn('url.startsWith("//")', self.javascript)
        self.assertIn("https?:|mailto:", self.javascript)

    def test_hover_focus_pin_keyboard_fit_reset_and_pan_hooks_are_present(self) -> None:
        for hook in ("mouseenter", "mouseleave", "focus", "blur", "click", "keydown", "pointerdown", "pointermove", "wheel"):
            self.assertIn(f'addEventListener("{hook}"', self.javascript)
        self.assertIn('event.key === "Enter" || event.key === " "', self.javascript)
        self.assertIn('"aria-expanded": state.expanded.has(node.id)', self.javascript)
        self.assertIn("ArrowLeft", self.javascript)
        self.assertIn('id="nodeTooltip" role="tooltip"', self.html)
        self.assertIn('id="pinnedPanel"', self.html)
        for control in ("fitButton", "expandButton", "collapseButton", "resetButton", "zoomInButton", "zoomOutButton"):
            self.assertIn(f'id="{control}"', self.html)
        self.assertIn('id="graphLiveStatus" role="status" aria-live="polite"', self.html)

    def test_pinning_closes_tooltip_and_expansion_keeps_a_readable_scale(self) -> None:
        activation = self.javascript.split("function activateNode", 1)[1].split("function handleNodeKeydown", 1)[0]
        self.assertLess(activation.index("hideTooltip();"), activation.index("pinDetail(node);"))
        self.assertIn("suppressTooltipFocusId", activation)
        self.assertIn("const READABLE_SCALE_FLOORS = { desktop: .46, tablet: .38, mobile: .32, narrow: .28 };", self.javascript)
        self.assertIn("Math.max(fittedScale(svg.clientWidth, svg.clientHeight), readableScaleFloor(svg.clientWidth))", self.javascript)
        self.assertGreaterEqual(self.javascript.count("renderGraph({ readableFit: true"), 2)
        self.assertIn("use Fit graph for an all-in-view overview", self.javascript)
        self.assertIn("width: min(380px, calc(100vw - 24px))", self.css)
        self.assertIn("max-height: min(450px, calc(100vh - 24px))", self.css)

    def test_ui_states_provisional_navigation_not_verification(self) -> None:
        combined = self.html + self.javascript
        self.assertIn("PROVISIONAL NAVIGATION", combined)
        self.assertNotIn("COMPLETE COVERAGE", combined)
        self.assertNotIn("success-green", combined)
        self.assertIn("not final query coverage or verification", combined)
        self.assertIn("never enter the mathematical proof DAG", self.html)

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
