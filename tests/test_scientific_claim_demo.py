from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from unittest import mock
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
        cls.edges_by_type: dict[str, list[dict]] = {}
        for edge in cls.graph["edges"]:
            cls.edges_by_type.setdefault(edge["type"], []).append(edge)
        cls.demo = exporter.ROOT / "demo_design/scientific_claims"
        cls.html = (cls.demo / "index.html").read_text(encoding="utf-8")
        cls.javascript = (cls.demo / "app.js").read_text(encoding="utf-8")
        cls.css = (cls.demo / "styles.css").read_text(encoding="utf-8")
        cls.source_dag = json.loads(exporter.CANDIDATE_DAG.read_text(encoding="utf-8"))

    def test_export_is_deterministic_and_matches_committed_payload(self) -> None:
        first = exporter.serialize(exporter.build_demo_data())
        second = exporter.serialize(exporter.build_demo_data())
        self.assertEqual(first, second)
        self.assertEqual(first, self.committed_text)
        self.assertEqual(self.generated, self.committed)
        self.assertEqual(self.generated["schema"], "agtxiv.scientific-claim-demo/4.0.0")

    def test_export_contains_exactly_the_two_current_contribution_claims(self) -> None:
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

    def test_export_rejects_duplicate_calibration_or_support_record_for_one_claim(self) -> None:
        original_load_jsonl = exporter.load_jsonl
        for duplicate_path, expected_message in (
            (exporter.CALIBRATIONS, "duplicate calibration for"),
            (exporter.SUPPORT, "duplicate support association for"),
        ):
            def load_with_duplicate(path: Path, selected_path: Path = duplicate_path) -> list[dict]:
                records = original_load_jsonl(path)
                if path == selected_path:
                    duplicate = copy.deepcopy(next(
                        record for record in records
                        if record.get("scientific_claim_ref", {}).get("target_id") == exporter.POLYTOPE_CLAIM_ID
                    ))
                    duplicate["id"] += ":duplicate-test"
                    records.append(duplicate)
                return records

            with self.subTest(path=duplicate_path):
                with mock.patch.object(exporter, "load_jsonl", side_effect=load_with_duplicate):
                    with self.assertRaisesRegex(exporter.ExportError, expected_message):
                        exporter.build_demo_data()

    def test_old_visual_categories_are_absent_from_graph_schema_and_ui(self) -> None:
        self.assertEqual({node["type"] for node in self.graph["nodes"]}, exporter.GRAPH_NODE_TYPES)
        for forbidden in ("facet", "source_occurrence", "oracle_skeleton", "mathematical_proposition_ir"):
            self.assertNotIn(forbidden, {node["type"] for node in self.graph["nodes"]})
            self.assertNotIn(f'class="glyph-swatch {forbidden}"', self.html)
        self.assertFalse(any(node["id"].startswith(("occurrence:", "graph-facet:", "oracle-skeleton:")) for node in self.graph["nodes"]))
        self.assertNotIn("HAS FACET", self.html + self.javascript)
        self.assertNotIn("PROVISIONAL NAVIGATION", self.html + self.javascript)

    def test_canvas_has_only_neutral_paper_claim_circles_math_squares_and_gray_candidates(self) -> None:
        papers = [node for node in self.graph["nodes"] if node["type"] == "paper"]
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["visual_state"], "neutral")
        for node in self.graph["nodes"]:
            if node["type"] == "scientific_claim":
                self.assertEqual(node["shape"], "circle")
                self.assertEqual(node["visual_state"], "grounded")
            elif node["type"] == "math_claim_ir":
                self.assertEqual(node["shape"], "square")
                self.assertEqual(node["visual_state"], "normalized")
            elif node["type"] == "oracle_candidate":
                self.assertEqual(node["shape"], "square")
                self.assertEqual(node["visual_state"], "gray")
                self.assertEqual(node["claim_type"], "referenced")
        self.assertIn('node.shape === "square"', self.javascript)
        self.assertIn('svgElement("rect"', self.javascript)
        self.assertIn('svgElement("circle"', self.javascript)
        self.assertGreater(self.css.index(".graph-node.paper {"), self.css.index(".graph-node.claim-type-theorem"))

    def test_mathematical_claim_type_color_is_data_driven_and_shared_by_exact_identity(self) -> None:
        for claim_type in ("contribution", "definition", "lemma", "proposition", "theorem"):
            self.assertIn(f"--{claim_type}:", self.css)
            self.assertIn(f"claim-type-{claim_type}", self.css)
            self.assertIn(f'class="type-swatch {claim_type}"', self.html)
        self.assertIn("claim-type-${node.claim_type}", self.javascript)
        for edge in self.edges_by_type["normalizes_identity"]:
            source, target = self.nodes[edge["source"]], self.nodes[edge["target"]]
            self.assertEqual(source["type"], "scientific_claim")
            self.assertEqual(target["type"], "math_claim_ir")
            self.assertEqual(source["claim_type"], target["claim_type"])
            self.assertEqual(target["claim_identity"]["id"], source["id"])
            self.assertEqual(edge["basis"], "Exact MathClaimIR.claim immutable reference")

    def test_canonical_flow_is_paper_to_contribution_to_formal_to_math(self) -> None:
        for edge in self.edges_by_type["contains"]:
            self.assertEqual(self.nodes[edge["source"]]["type"], "paper")
            self.assertEqual(self.nodes[edge["target"]]["claim_type"], "contribution")
        for edge in self.edges_by_type["claim_navigation"]:
            self.assertEqual(self.nodes[edge["source"]]["claim_type"], "contribution")
            self.assertEqual(self.nodes[edge["target"]]["provenance_role"], "SOURCE_FAITHFUL_FORMAL_ATOMIC")
            self.assertIn(edge["facet_id"], {item["facet_id"] for item in self.graph["facet_filters"]})
        for edge in self.edges_by_type["normalizes_identity"]:
            self.assertEqual(self.nodes[edge["source"]]["provenance_role"], "SOURCE_FAITHFUL_FORMAL_ATOMIC")
            self.assertEqual(self.nodes[edge["target"]]["provenance_role"], "REORGANIZED_NORMALIZED")
        self.assertNotIn("formal_source", self.edges_by_type)

    def test_occurrences_facets_calibration_and_support_are_embedded_in_contribution_details(self) -> None:
        for bundle in self.generated["claims"]:
            claim = bundle["claim"]
            node = self.nodes[claim["id"]]
            self.assertEqual(node["occurrences"], claim["occurrences"])
            self.assertEqual(node["facets"], claim["facets"])
            self.assertEqual(node["calibration_record"], bundle["calibration"])
            self.assertEqual(node["support_metadata"], bundle["support_association"])
            detail = node["detail_markdown"]
            expected_previews = {}
            for occurrence in claim["occurrences"]:
                self.assertIn(occurrence["id"], detail)
                self.assertIn(occurrence["source_artifact"]["path"], detail)
                self.assertIn(occurrence["source_text"], detail)
                self.assertIn(occurrence["occurrence_role"], detail)
                previews = exporter.extract_formula_previews(occurrence["source_text"])
                expected_previews[occurrence["id"]] = previews
                for formula in previews:
                    self.assertIn(f"$$\n{formula}\n$$", detail)
                    self.assertNotRegex(formula, r"\\(?:begin|end|label|ref|eqref|cite)\b")
            self.assertEqual(node["occurrence_formula_previews"], expected_previews)
            for facet in claim["facets"]:
                self.assertIn(facet["facet_id"], detail)
                self.assertIn(facet["statement"], detail)
            self.assertIn("No occurrence-to-facet proof edge is asserted", detail)

    def test_occurrence_formula_previews_are_source_derived_deduplicated_and_structure_free(self) -> None:
        formula_occurrences = 0
        for bundle in self.generated["claims"]:
            node = self.nodes[bundle["claim"]["id"]]
            for occurrence in bundle["claim"]["occurrences"]:
                previews = node["occurrence_formula_previews"][occurrence["id"]]
                self.assertEqual(previews, list(dict.fromkeys(previews)))
                if previews:
                    formula_occurrences += 1
                    self.assertIn("##### Formula preview", node["detail_markdown"])
        self.assertEqual(formula_occurrences, 5)
        theorem_source = next(
            occurrence["source_text"]
            for bundle in self.generated["claims"]
            for occurrence in bundle["claim"]["occurrences"]
            if occurrence["id"] == "occurrence:2607-sign-relaxation-exactness:3"
        )
        previews = exporter.extract_formula_previews(theorem_source)
        self.assertIn(r"\RoM_\Mcal(\rho)=\widetilde{\RoM}_\Mcal(\rho).", previews)
        self.assertFalse(any(r"\begin{theorem}" in formula or r"\label" in formula for formula in previews))

    def test_facet_filters_exactly_match_registry_support_without_facet_nodes(self) -> None:
        filters = {(item["claim_id"], item["facet_id"]): item for item in self.graph["facet_filters"]}
        for bundle in self.generated["claims"]:
            claim, association = bundle["claim"], bundle["support_association"]
            for facet in claim["facets"]:
                item = filters[(claim["id"], facet["facet_id"])]
                links = [link for link in association["links"] if link["facet_id"] == facet["facet_id"]]
                self.assertEqual(set(item["target_math_ids"]), {link["target_ref"]["target_id"] for link in links})
                self.assertEqual(len(item["target_claim_ids"]), len(links))
                self.assertIn(item["primary_claim_id"], item["target_claim_ids"])
        selected = filters[(exporter.POLYTOPE_CLAIM_ID, exporter.POLYTOPE_FACET_ID)]
        self.assertEqual(
            set(selected["target_math_ids"]),
            {
                exporter.EXACT_POLYTOPE_MATH_ID,
                "math-claim-ir:graph-theoretic-nonstabilizerness:sign-set-collapse",
            },
        )
        self.assertEqual(selected["primary_claim_id"], exporter.EXACT_POLYTOPE_CLAIM_ID)
        self.assertFalse(any("robustness" in identifier for identifier in selected["target_math_ids"] + selected["target_claim_ids"]))

    def test_initial_state_contains_only_paper_and_contributions(self) -> None:
        initial = self.graph["initial_node_ids"]
        self.assertEqual(len(initial), 3)
        self.assertEqual([self.nodes[node_id]["type"] for node_id in initial], ["paper", "scientific_claim", "scientific_claim"])
        self.assertEqual(self.graph["initial_expanded_node_ids"], [initial[0]])

    def test_deep_link_end_to_end_state_and_visibility_filter_without_a_facet_node(self) -> None:
        start = self.javascript.index("  function parseDeepLink")
        end = self.javascript.index("\n  window.ScientificClaimDemo", start)
        functions = self.javascript[start:end]
        graph = json.dumps(self.graph)
        script = f"""
{functions}
const graph = {graph};
const hash = '#claim=claim%3Agraph-theoretic-nonstabilizerness%3Asign-relaxation-exactness&facet=facet%3Apolytope-exactness';
const deep = deepLinkState(hash, graph);
const initial = visibleGraphForState(graph, deep.expandedIds, deep.facetFilter);
const oracle = visibleGraphForState(graph, [...deep.expandedIds, '{exporter.EXACT_POLYTOPE_MATH_ID}'], deep.facetFilter);
const invalid = deepLinkState('#claim=claim%3Amissing&facet=facet%3Apolytope-exactness', graph);
const mismatch = deepLinkState('#claim=claim%3Agraph-theoretic-nonstabilizerness%3Aperfect-graph-closed-form&facet=facet%3Apolytope-exactness', graph);
console.log(JSON.stringify({{
  claim: deep.selection.claim.id,
  facet: deep.selection.facet.facet_id,
  pinned: deep.pinnedId,
  initialIds: initial.nodes.map(node => node.id),
  oracleIds: oracle.nodes.map(node => node.id),
  invalid,
  mismatch
}}));
"""
        result = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        parsed = json.loads(result.stdout)
        initial_ids = set(parsed["initialIds"])
        self.assertEqual(parsed["claim"], exporter.POLYTOPE_CLAIM_ID)
        self.assertEqual(parsed["facet"], exporter.POLYTOPE_FACET_ID)
        self.assertEqual(parsed["pinned"], exporter.EXACT_POLYTOPE_CLAIM_ID)
        self.assertIn(exporter.POLYTOPE_CLAIM_ID, initial_ids)
        self.assertTrue({
            exporter.EXACT_POLYTOPE_CLAIM_ID,
            "claim:graph-theoretic-nonstabilizerness:sign-set-collapse",
            exporter.EXACT_POLYTOPE_MATH_ID,
            "math-claim-ir:graph-theoretic-nonstabilizerness:sign-set-collapse",
        }.issubset(initial_ids))
        self.assertFalse(any("robustness" in identifier for identifier in initial_ids))
        self.assertFalse(any(identifier.startswith("oracle-candidate:") for identifier in initial_ids))
        self.assertEqual(sum(identifier.startswith("oracle-candidate:") for identifier in parsed["oracleIds"]), 10)
        self.assertIsNone(parsed["invalid"])
        self.assertIsNone(parsed["mismatch"])

    def test_oracle_branch_has_no_wrapper_and_one_direct_unverified_entry(self) -> None:
        entries = self.edges_by_type["oracle_entry"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "oracle-candidate:claim:relaxation-exactness")
        self.assertEqual(entries[0]["target"], exporter.EXACT_POLYTOPE_MATH_ID)
        self.assertEqual(entries[0]["evidence"], exporter.ORACLE_EVIDENCE)
        self.assertNotIn("oracle_contains", self.edges_by_type)
        self.assertNotIn("oracle_overlay", self.edges_by_type)
        exact = self.nodes[exporter.EXACT_POLYTOPE_MATH_ID]
        self.assertTrue(exact["expandable"])
        self.assertNotIn(exact["id"], self.graph["initial_expanded_node_ids"])
        self.assertIn('edge.type.startsWith("oracle_") ? oracleExpanded', self.javascript)

    def test_oracle_candidates_edges_evidence_blockers_and_issues_match_source_dag(self) -> None:
        selected_ids = exporter.ORACLE_NODE_IDS
        source_nodes = {node["id"]: node for node in self.source_dag["nodes"] if node["id"] in selected_ids}
        candidates = {node["candidate_id"]: node for node in self.graph["nodes"] if node["type"] == "oracle_candidate"}
        self.assertEqual(set(candidates), selected_ids)
        for candidate_id, source in source_nodes.items():
            self.assertEqual(candidates[candidate_id]["candidate_record"], source)
            self.assertEqual(candidates[candidate_id]["issue_badges"], source.get("issue_badges", []))
            self.assertEqual(candidates[candidate_id]["source_status"], source["status"])
        source_edges = {
            (edge["from"], edge["to"], edge["type"], edge["reason"], json.dumps(edge["evidence"], sort_keys=True))
            for edge in self.source_dag["edges"] if edge["from"] in selected_ids and edge["to"] in selected_ids
        }
        graph_edges = {
            (edge["source"].removeprefix("oracle-candidate:"), edge["target"].removeprefix("oracle-candidate:"), edge["candidate_edge_type"], edge["reason"], json.dumps(edge["evidence"], sort_keys=True))
            for edge in self.edges_by_type["oracle_candidate_dependency"]
        }
        self.assertEqual(graph_edges, source_edges)
        details = "\n".join(node["detail_markdown"] for node in candidates.values())
        for blocker in ("BLOCKED_BY_ROOT_CONTRACT", "BLOCKED_BY_VREP_PROOF_GAP", "AGENT_EXPLICITATION_REQUIRES_PROOF_AUDIT"):
            self.assertIn(blocker, details)

    def test_monotonicity_counterexample_does_not_refute_v_representation(self) -> None:
        varela = next(node for node in self.graph["nodes"] if node.get("candidate_id") == "root:varela-reduced-polytope")
        false_issue = next(issue for issue in varela["issue_badges"] if issue["status"] == "CLAIM_FALSE")
        self.assertEqual(false_issue["object"], "fixed-window reduced-RoM monotonicity")
        self.assertEqual(false_issue["badges"], ["FALSE", "EXPLICIT_COUNTEREXAMPLE"])
        self.assertIn("does not refute the V-representation", false_issue["interpretation"])
        self.assertIn(false_issue["interpretation"], varela["detail_markdown"])

    def test_mathematical_statements_use_display_markup_not_raw_latex_fences(self) -> None:
        math_nodes = [node for node in self.graph["nodes"] if node["type"] == "math_claim_ir"]
        self.assertTrue(math_nodes)
        for node in math_nodes:
            detail = node["detail_markdown"]
            self.assertIn("### Mathematical statement\n\n$$\n", detail)
            self.assertNotIn("```latex", detail)
        source_details = "\n".join(node["detail_markdown"] for node in self.graph["nodes"] if node.get("claim_type") == "contribution")
        self.assertIn("```tex-source", source_details)

    def test_safe_markdown_and_real_local_mathjax_hooks_are_present(self) -> None:
        self.assertNotIn(".innerHTML", self.javascript)
        self.assertIn("document.createTextNode", self.javascript)
        self.assertIn("function renderMarkdown(markdown)", self.javascript)
        self.assertIn("function isSafeUrl(value)", self.javascript)
        self.assertIn("[unsafe link removed]", self.javascript)
        self.assertIn("function typesetMath(container, isCurrent", self.javascript)
        self.assertIn("window.MathJax.typesetPromise([container])", self.javascript)
        self.assertIn("window.MathJax.typesetClear([container])", self.javascript)
        self.assertIn("state.tooltipId === node.id && !tooltip.hidden", self.javascript)
        self.assertIn('fence[1].toLowerCase() === "latex"', self.javascript)
        self.assertIn("Mathematical formula:", self.javascript)
        self.assertIn("Formula renderer unavailable; showing TeX source", self.javascript)
        self.assertIn('src="vendor/mathjax/tex-svg.js"', self.html)
        for macro, expansion in (
            ("Mcal", r"\mathcal M"), ("STAB", r"\mathrm{STAB}"), ("RoM", r"\mathrm{RoM}"),
            ("tr", r"\operatorname{tr}"), ("clnum", r"\operatorname{cl}"),
        ):
            self.assertIn(f'{macro}: "{expansion.replace(chr(92), chr(92) * 2)}"', self.html)
        self.assertNotIn("cdn", self.html.lower())

    def test_mathjax_vendor_manifest_version_source_hash_and_license_are_auditable(self) -> None:
        vendor = self.demo / "vendor/mathjax"
        manifest = json.loads((vendor / "manifest.json").read_text(encoding="utf-8"))
        bundle = vendor / "tex-svg.js"
        self.assertEqual(manifest["name"], "MathJax")
        self.assertEqual(manifest["version"], "3.2.2")
        self.assertEqual(manifest["source"], "https://registry.npmjs.org/mathjax/-/mathjax-3.2.2.tgz")
        self.assertEqual(manifest["sha256"], hashlib.sha256(bundle.read_bytes()).hexdigest())
        self.assertGreater(bundle.stat().st_size, 1_000_000)
        self.assertIn("Apache License", (vendor / "LICENSE").read_text(encoding="utf-8"))

    def test_math_and_details_have_mobile_overflow_protection(self) -> None:
        for rule in (
            ".math-display, .math-figure", "overflow-x: auto", ".markdown-body mjx-container svg",
            "max-width: 100%", "width: min(390px, calc(100vw - 24px))", "overflow-x: hidden",
            "@media (max-width: 480px)", "@media (max-width: 340px)",
        ):
            self.assertIn(rule, self.css)

    def test_hover_pin_keyboard_pan_zoom_and_relation_detail_hooks_remain(self) -> None:
        for hook in ("mouseenter", "mouseleave", "focus", "blur", "click", "keydown", "pointerdown", "pointermove", "wheel"):
            self.assertIn(f'addEventListener("{hook}"', self.javascript)
        self.assertIn('event.key === "Enter" || event.key === " "', self.javascript)
        self.assertIn("ArrowLeft", self.javascript)
        self.assertIn("function relationMarkdown(node)", self.javascript)
        self.assertIn("edge.reason", self.javascript)
        self.assertIn('id="nodeTooltip" role="tooltip"', self.html)
        self.assertIn('id="pinnedPanel"', self.html)
        for control in ("fitButton", "expandButton", "collapseButton", "resetButton", "zoomInButton", "zoomOutButton"):
            self.assertIn(f'id="{control}"', self.html)

    def test_graph_validator_rejects_structural_identity_filter_source_and_oracle_mutations(self) -> None:
        cases = []
        duplicate = copy.deepcopy(self.graph)
        duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
        cases.append(duplicate)

        dangling = copy.deepcopy(self.graph)
        dangling["edges"][0]["target"] = "claim:missing"
        cases.append(dangling)

        wrong_shape = copy.deepcopy(self.graph)
        next(node for node in wrong_shape["nodes"] if node["type"] == "scientific_claim")["shape"] = "square"
        cases.append(wrong_shape)

        wrong_identity_type = copy.deepcopy(self.graph)
        identity = next(edge for edge in wrong_identity_type["edges"] if edge["type"] == "normalizes_identity")
        wrong_identity_type["nodes"][next(index for index, node in enumerate(wrong_identity_type["nodes"]) if node["id"] == identity["target"])]["claim_type"] = "definition"
        cases.append(wrong_identity_type)

        missing_occurrence = copy.deepcopy(self.graph)
        contribution = next(node for node in missing_occurrence["nodes"] if node.get("claim_type") == "contribution")
        contribution["occurrences"] = contribution["occurrences"][:-1]
        cases.append(missing_occurrence)

        invented_formula_preview = copy.deepcopy(self.graph)
        contribution = next(node for node in invented_formula_preview["nodes"] if node.get("claim_type") == "contribution")
        occurrence_id = next(iter(contribution["occurrence_formula_previews"]))
        contribution["occurrence_formula_previews"][occurrence_id].append(r"\text{invented}")
        cases.append(invented_formula_preview)

        bad_filter = copy.deepcopy(self.graph)
        selected = next(item for item in bad_filter["facet_filters"] if item["facet_id"] == exporter.POLYTOPE_FACET_ID)
        selected["target_claim_ids"] = selected["target_claim_ids"][:-1]
        cases.append(bad_filter)

        missing_entry = copy.deepcopy(self.graph)
        missing_entry["edges"] = [edge for edge in missing_entry["edges"] if edge["type"] != "oracle_entry"]
        cases.append(missing_entry)

        mutated_oracle = copy.deepcopy(self.graph)
        oracle = next(edge for edge in mutated_oracle["edges"] if edge["type"] == "oracle_candidate_dependency")
        oracle["reason"] += " mutated"
        cases.append(mutated_oracle)

        erased_issues = copy.deepcopy(self.graph)
        varela = next(node for node in erased_issues["nodes"] if node.get("candidate_id") == "root:varela-reduced-polytope")
        varela["issue_badges"] = []
        cases.append(erased_issues)

        unsafe = copy.deepcopy(self.graph)
        unsafe["nodes"][0]["detail_markdown"] = "## Bad\n[jump](javascript:alert(1))"
        cases.append(unsafe)

        for index, graph in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(exporter.ExportError):
                    exporter.validate_graph(graph)

    def test_missing_mathclaimir_anchor_is_not_rendered_as_resolved(self) -> None:
        formal = self.nodes[exporter.EXACT_POLYTOPE_CLAIM_ID]
        self.assertIn("referenced anchor / Registry record missing", formal["detail_markdown"])
        self.assertNotIn("resolved SourceAnchor", formal["detail_markdown"])

    def test_javascript_syntax_and_internal_assets(self) -> None:
        subprocess.run(["node", "--check", str(self.demo / "app.js")], check=True, capture_output=True, text=True)
        parser = AssetParser()
        parser.feed(self.html)
        references = {value for _, value in parser.references}
        self.assertIn("../assets/agentxiv-logo.svg", references)
        self.assertIn("styles.css", references)
        self.assertIn("app.js", references)
        self.assertIn("vendor/mathjax/tex-svg.js", references)
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
