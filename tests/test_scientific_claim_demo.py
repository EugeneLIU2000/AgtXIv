from __future__ import annotations

import copy
import json
import subprocess
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
        cls.source_dag = json.loads(exporter.CANDIDATE_DAG.read_text(encoding="utf-8"))

    def test_export_is_deterministic_and_matches_committed_graph_payload(self) -> None:
        first = exporter.serialize(exporter.build_demo_data())
        second = exporter.serialize(exporter.build_demo_data())
        self.assertEqual(first, second)
        self.assertEqual(first, self.committed_text)
        self.assertEqual(self.generated, self.committed)
        self.assertEqual(self.generated["schema"], "agtxiv.scientific-claim-demo/3.0.0")

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
        for class_name in ("paper", "contribution", "facet", "formal", "occurrence", "math", "proposition", "oracle"):
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
        self.assertTrue(edges_by_type["normalizes_identity"])
        self.assertTrue(edges_by_type["provisional_navigation"])
        self.assertEqual(len(edges_by_type["oracle_overlay"]), 1)
        self.assertTrue(edges_by_type["oracle_candidate_dependency"])
        for edge in edges_by_type["contains"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "paper")
            self.assertEqual(self.nodes[edge["target"]]["type"], "scientific_claim_contribution")
        for edge in edges_by_type["has_facet"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "scientific_claim_contribution")
            self.assertEqual(self.nodes[edge["target"]]["type"], "facet")
        for edge in edges_by_type["source_calibration"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "scientific_claim_contribution")
            self.assertEqual(self.nodes[edge["target"]]["type"], "source_occurrence")
        for edge in edges_by_type["normalizes_identity"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "math_claim_ir")
            self.assertEqual(self.nodes[edge["target"]]["type"], "scientific_claim_formal")
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

    def test_graph_validator_rejects_required_semantic_structure_mutations(self) -> None:
        missing_complete_navigation = copy.deepcopy(self.graph)
        missing_complete_navigation["edges"] = [
            edge for edge in missing_complete_navigation["edges"]
            if not (
                edge["type"] == "provisional_navigation"
                and edge.get("facet_id") == "facet:polytope-exactness"
                and edge.get("facet_coverage") == "COMPLETE"
            )
        ]

        missing_oracle_edge = copy.deepcopy(self.graph)
        oracle_index = next(index for index, edge in enumerate(missing_oracle_edge["edges"]) if edge["type"] == "oracle_candidate_dependency")
        missing_oracle_edge["edges"].pop(oracle_index)

        mutated_oracle_edge = copy.deepcopy(self.graph)
        oracle_edge = next(edge for edge in mutated_oracle_edge["edges"] if edge["type"] == "oracle_candidate_dependency")
        oracle_edge["reason"] += " mutated"

        erased_issues = copy.deepcopy(self.graph)
        varela = next(node for node in erased_issues["nodes"] if node.get("candidate_id") == "root:varela-reduced-polytope")
        varela["issue_badges"] = []

        mutated_issue = copy.deepcopy(self.graph)
        varela = next(node for node in mutated_issue["nodes"] if node.get("candidate_id") == "root:varela-reduced-polytope")
        varela["candidate_record"]["issue_badges"][1]["interpretation"] = "mutated"

        erased_issue_rendering = copy.deepcopy(self.graph)
        varela = next(node for node in erased_issue_rendering["nodes"] if node.get("candidate_id") == "root:varela-reduced-polytope")
        varela["detail_markdown"] = varela["detail_markdown"].replace("fixed-window reduced-RoM monotonicity", "removed issue", 2)

        for graph in (missing_complete_navigation, missing_oracle_edge, mutated_oracle_edge, erased_issues, mutated_issue, erased_issue_rendering):
            with self.subTest(mutation=id(graph)):
                with self.assertRaises(exporter.ExportError):
                    exporter.validate_graph(graph)

    def test_safe_markdown_renderer_escapes_raw_html_and_rejects_unsafe_links(self) -> None:
        self.assertNotIn(".innerHTML", self.javascript)
        self.assertIn("document.createTextNode", self.javascript)
        self.assertIn("function renderMarkdown(markdown)", self.javascript)
        self.assertIn("function isSafeUrl(value)", self.javascript)
        self.assertIn("[unsafe link removed]", self.javascript)
        self.assertIn('window.ScientificClaimDemo = Object.freeze({ isSafeUrl, renderMarkdown, parseDeepLink, resolveDeepLink })', self.javascript)
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
        self.assertIn("Navigation coverage is not proof completeness", combined)
        self.assertIn("Contribution ScientificClaims never enter the proof DAG", self.html)

    def test_polytope_facet_has_exact_registry_navigation_decomposition(self) -> None:
        facet_id = "graph-facet:sign-relaxation-exactness:polytope-exactness"
        outgoing = [edge for edge in self.graph["edges"] if edge["source"] == facet_id]
        self.assertEqual(
            {(edge["target"], edge["relationship"], edge["label"]) for edge in outgoing},
            {
                ("math-claim-ir:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness", "DIRECT_ATOMIC_SUPPORT", "PROVISIONAL NAVIGATION · COMPLETE"),
                ("math-claim-ir:graph-theoretic-nonstabilizerness:sign-set-collapse", "FRAMEWORK_SUPPORT", "PROVISIONAL NAVIGATION · PARTIAL"),
            },
        )
        self.assertFalse(any("robustness" in edge["target"] for edge in outgoing))
        self.assertFalse(any(self.nodes[edge["target"]]["type"] == "mathematical_proposition_ir" for edge in outgoing))
        self.assertFalse(any(edge["type"] == "source_calibration" and edge["target"] == facet_id for edge in self.graph["edges"]))

    def test_formal_claims_are_exact_mathclaimir_identities_not_contribution_sources(self) -> None:
        identity_edges = [edge for edge in self.graph["edges"] if edge["type"] == "normalizes_identity"]
        self.assertTrue(identity_edges)
        self.assertFalse(any(edge["type"] == "formal_source" for edge in self.graph["edges"]))
        for edge in identity_edges:
            math = self.nodes[edge["source"]]
            formal = self.nodes[edge["target"]]
            self.assertEqual(math["type"], "math_claim_ir")
            self.assertEqual(formal["type"], "scientific_claim_formal")
            self.assertEqual(edge["basis"], "Exact MathClaimIR.claim immutable reference")
        exact = "math-claim-ir:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness"
        exact_edge = next(edge for edge in identity_edges if edge["source"] == exact)
        self.assertEqual(exact_edge["target"], "claim:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness")

    def test_navigation_copy_separates_coverage_acceptance_and_proof_assertion(self) -> None:
        for node in self.graph["nodes"]:
            if node["type"] not in {"facet", "math_claim_ir"}:
                continue
            detail = node["detail_markdown"]
            self.assertIn("SCIENTIFIC ACCEPTANCE: **UNKNOWN**", detail)
            self.assertIn("PROOF-DAG EDGE: **NOT ASSERTED**", detail)
        polytope = self.nodes["graph-facet:sign-relaxation-exactness:polytope-exactness"]["detail_markdown"]
        self.assertIn("NAVIGATION COVERAGE: **COMPLETE**", polytope)
        self.assertNotIn("PROOF COMPLETENESS: **COMPLETE**", polytope)

    def test_missing_mathclaimir_anchors_are_not_rendered_as_resolved(self) -> None:
        formal = self.nodes["claim:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness"]
        self.assertIn("referenced anchor / Registry record missing", formal["detail_markdown"])
        self.assertNotIn("resolved SourceAnchor", formal["detail_markdown"])

    def test_oracle_overlay_matches_independently_loaded_source_dag(self) -> None:
        selected_ids = {
            "root:gottesman-stabilizer-formalism", "root:varela-reduced-polytope",
            "claim:reduced-stabilizer-polytope", "claim:frustration-graph",
            "claim:exact-reduced-vrep", "claim:sign-syndrome-linear-consistent",
            "claim:dependency-affine-code", "claim:pauli-active-dependency",
            "claim:no-active-free-signs", "claim:relaxation-exactness",
        }
        source_nodes = {node["id"]: node for node in self.source_dag["nodes"] if node["id"] in selected_ids}
        candidates = {node["candidate_id"]: node for node in self.graph["nodes"] if node["type"] == "oracle_candidate"}
        self.assertEqual(set(source_nodes), selected_ids)
        self.assertEqual(set(candidates), selected_ids)
        for candidate_id, source_record in source_nodes.items():
            self.assertEqual(candidates[candidate_id]["candidate_record"], source_record)
            self.assertEqual(candidates[candidate_id]["source_status"], source_record["status"])
            self.assertEqual(candidates[candidate_id]["issue_badges"], source_record.get("issue_badges", []))

        source_edges = {
            (edge["from"], edge["to"], edge["type"], edge["reason"], json.dumps(edge["evidence"], sort_keys=True))
            for edge in self.source_dag["edges"]
            if edge["from"] in selected_ids and edge["to"] in selected_ids
        }
        graph_edges = {
            (
                edge["source"].removeprefix("oracle-candidate:"),
                edge["target"].removeprefix("oracle-candidate:"),
                edge["candidate_edge_type"], edge["reason"], json.dumps(edge["evidence"], sort_keys=True),
            )
            for edge in self.graph["edges"] if edge["type"] == "oracle_candidate_dependency"
        }
        self.assertEqual(graph_edges, source_edges)
        overlay = next(node for node in self.graph["nodes"] if node["type"] == "oracle_skeleton")
        self.assertTrue(overlay["expandable"])
        self.assertNotIn(overlay["id"], self.graph["initial_expanded_node_ids"])
        combined = "\n".join(node["detail_markdown"] for node in candidates.values())
        for blocker in ("BLOCKED_BY_ROOT_CONTRACT", "BLOCKED_BY_VREP_PROOF_GAP", "AGENT_EXPLICITATION_REQUIRES_PROOF_AUDIT"):
            self.assertIn(blocker, combined)
        self.assertNotIn("Finite LP duality", combined)
        self.assertNotIn("Perfect graph duality", combined)

    def test_varela_issues_remain_structured_and_scope_claim_false_precisely(self) -> None:
        source = next(node for node in self.source_dag["nodes"] if node["id"] == "root:varela-reduced-polytope")
        graph_node = next(node for node in self.graph["nodes"] if node.get("candidate_id") == source["id"])
        self.assertEqual(graph_node["issue_badges"], source["issue_badges"])
        self.assertEqual(len(graph_node["issue_badges"]), 2)
        false_issue = next(issue for issue in graph_node["issue_badges"] if issue["status"] == "CLAIM_FALSE")
        self.assertEqual(false_issue["object"], "fixed-window reduced-RoM monotonicity")
        self.assertEqual(false_issue["badges"], ["FALSE", "EXPLICIT_COUNTEREXAMPLE"])
        self.assertIn("does not refute the V-representation", false_issue["interpretation"])
        detail = graph_node["detail_markdown"]
        for issue in source["issue_badges"]:
            self.assertIn(f"Object: **{issue['object']}**", detail)
            self.assertIn(f"Status: `{issue['status']}`", detail)
            self.assertIn(issue["interpretation"], detail)
            for badge in issue["badges"]:
                self.assertIn(f"`{badge}`", detail)

    def test_oracle_topological_layout_and_same_layer_route_avoid_glyph_double_back(self) -> None:
        syndrome = self.nodes["oracle-candidate:claim:sign-syndrome-linear-consistent"]
        affine = self.nodes["oracle-candidate:claim:dependency-affine-code"]
        self.assertLess(syndrome["layout_level"], affine["layout_level"])
        edge_path = self.javascript.split("function edgePath", 1)[1].split("function edgeLabel", 1)[0]
        self.assertIn("source.level === target.level", edge_path)
        self.assertIn("loopX", edge_path)
        self.assertIn("target.x + target.radius", edge_path)

    def test_deep_link_parser_and_resolver_accept_exact_branch_and_reject_invalid_ids(self) -> None:
        start = self.javascript.index("  function parseDeepLink")
        end = self.javascript.index("\n  window.ScientificClaimDemo", start)
        functions = self.javascript[start:end]
        graph = json.dumps(self.graph)
        script = f"""
{functions}
const graph = {graph};
const valid = resolveDeepLink('#claim=claim%3Agraph-theoretic-nonstabilizerness%3Asign-relaxation-exactness&facet=facet%3Apolytope-exactness', graph);
const invalid = resolveDeepLink('#claim=claim%3Amissing&facet=facet%3Apolytope-exactness', graph);
const mismatch = resolveDeepLink('#claim=claim%3Agraph-theoretic-nonstabilizerness%3Aperfect-graph-closed-form&facet=facet%3Apolytope-exactness', graph);
console.log(JSON.stringify({{claim: valid?.claim.id, facet: valid?.facet.facet_id, invalid, mismatch}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["claim"], "claim:graph-theoretic-nonstabilizerness:sign-relaxation-exactness")
        self.assertEqual(parsed["facet"], "facet:polytope-exactness")
        self.assertIsNone(parsed["invalid"])
        self.assertIsNone(parsed["mismatch"])
        self.assertIn("state.expanded.add(selection.claim.id)", self.javascript)
        self.assertIn("state.expanded.add(selection.facet.id)", self.javascript)
        self.assertIn("pinDetail(selected)", self.javascript)
        self.assertIn("history.replaceState", self.javascript)

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
