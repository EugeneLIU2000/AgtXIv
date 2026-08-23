from __future__ import annotations

import collections
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import jsonschema

import tools.extract_provisional_claims as extractor
from tools.extract_provisional_claims import (
    OUTPUT,
    PAPERS,
    ROOT,
    candidate_records,
    extract_spans,
    generate,
    graph_record,
    occurrence_record,
    section_paths,
    strip_comment,
    validate_paper_artifacts,
    validate_static_registry_integrity,
)


class ExtractorUnitTests(unittest.TestCase):
    def test_comments_and_escaped_percent(self) -> None:
        self.assertEqual(strip_comment("value % ordinary comment"), "value ")
        self.assertEqual(strip_comment(r"success is 90\% % comment"), r"success is 90\% ")
        self.assertEqual(strip_comment(r"two slashes \\% comment"), "two slashes " + "\\" * 2)

    def test_multiline_paragraph_and_normal_prose_claim(self) -> None:
        lines = [
            r"\begin{document}",
            "We show that every admissible state",
            "satisfies the stated upper bound.",
            "",
            r"\end{document}",
        ]
        spans = extract_spans(lines)
        prose = [span for span in spans if span.kind == "PROSE_PARAGRAPH"]
        self.assertEqual([(span.start, span.end) for span in prose], [(2, 3)])
        self.assertEqual(prose[0].speech_act, "MATHEMATICAL_ASSERTION")

    def test_comment_only_lines_continue_prose_but_true_blanks_split(self) -> None:
        lines = [
            r"\begin{document}",
            r"We show that success is 90\% for every admissible state",
            "% this comment suppresses the TeX newline",
            "and satisfies the stated upper bound.",
            "",
            "We prove that a separate state satisfies another bound.",
            r"\end{document}",
        ]
        prose = [span for span in extract_spans(lines) if span.kind == "PROSE_PARAGRAPH"]
        self.assertEqual([(span.start, span.end) for span in prose], [(2, 4), (6, 6)])
        paths = section_paths([strip_comment(line) for line in lines])
        occurrence = occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, prose[0])
        self.assertIn("% this comment", occurrence["verbatim_source_text"])
        self.assertIn(r"90\%", occurrence["verbatim_source_text"])

    def test_balanced_section_headings_and_hierarchy(self) -> None:
        lines = [
            r"\begin{document}",
            r"\section{Main \emph{nested} title\label{sec:main}}",
            r"\subsection{Child {with braces} \label{sec:child} tail}",
            "We show that every state satisfies the bound.",
            r"\end{document}",
        ]
        paths = section_paths([strip_comment(line) for line in lines])
        self.assertEqual(paths[1], [r"Main nested title"])
        self.assertEqual(paths[2], [r"Main nested title", "Child {with braces} tail"])
        self.assertEqual(paths[3], paths[2])

    def test_known_nested_label_headings_are_preserved(self) -> None:
        predicting = (ROOT / "Reference/Predicting magic from very few measurements/pra_version.tex").read_text().splitlines()
        predicting_paths = section_paths([strip_comment(line) for line in predicting])
        self.assertEqual(predicting_paths[337][-1], "On small polytopes and Pauli commutativity")
        resource = (ROOT / "Reference/The Resource Theory of Stabilizer Computation/stab_resource_theory_021.tex").read_text().splitlines()
        resource_paths = section_paths([strip_comment(line) for line in resource])
        self.assertEqual(resource_paths[561][-1], "Magic Monotones")

    def test_equation_discourse_bundle(self) -> None:
        lines = [
            r"\begin{document}",
            "We show that every admissible state satisfies the following identity.",
            r"\begin{equation}",
            "x = 1",
            r"\end{equation}",
            "Thus the resulting quantity is bounded for every admissible state.",
            r"\end{document}",
        ]
        spans = extract_spans(lines)
        self.assertIn((3, 5, "DISPLAY_EQUATION"), [(s.start, s.end, s.kind) for s in spans])
        self.assertIn((2, 6, "EQUATION_DISCOURSE_BUNDLE"), [(s.start, s.end, s.kind) for s in spans])

    def test_equation_context_bundle_is_neutral_without_derivation_cue(self) -> None:
        lines = [
            r"\begin{document}",
            "Every admissible state satisfies the following identity.",
            r"\begin{equation}",
            "x = 1",
            r"\end{equation}",
            "The resulting quantity is bounded for every admissible state.",
            r"\end{document}",
        ]
        spans = extract_spans(lines)
        bundle = next(span for span in spans if span.kind == "EQUATION_CONTEXT_BUNDLE")
        self.assertEqual(bundle.speech_act, "UNRESOLVED")
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in spans]
        candidate = next(row for row in candidate_records("test-paper", occurrences) if any(ref == occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, bundle)["id"] for ref in row["occurrence_refs"]))
        self.assertEqual((candidate["speech_act"], candidate["source_relation"]), ("UNRESOLVED", "UNRESOLVED"))

    def test_consecutive_equations_do_not_enter_each_others_context_bundles(self) -> None:
        lines = [
            r"\begin{document}",
            "We use the following identities for every admissible state.",
            r"\begin{equation}", "x = 1", r"\end{equation}",
            r"\begin{equation}", "y = 2", r"\end{equation}",
            "These quantities are used below.",
            r"\end{document}",
        ]
        displays = [span for span in extract_spans(lines) if span.kind == "DISPLAY_EQUATION"]
        bundles = [span for span in extract_spans(lines) if span.kind in {"EQUATION_CONTEXT_BUNDLE", "EQUATION_DISCOURSE_BUNDLE"}]
        self.assertLessEqual(len(bundles), len(displays))
        for bundle in bundles:
            self.assertEqual(sum(bundle.start <= display.start and display.end <= bundle.end for display in displays), 1)
        for left, right in zip(bundles, bundles[1:]):
            self.assertLess(left.end, right.start)

    def test_derivation_bundle_requires_and_records_explicit_cue(self) -> None:
        lines = [r"\begin{document}", r"\begin{equation}", "x = 1", r"\end{equation}", "Thus every admissible value is bounded.", r"\end{document}"]
        bundle = next(span for span in extract_spans(lines) if span.kind == "EQUATION_DISCOURSE_BUNDLE")
        self.assertIn("EXPLICIT_DERIVATION_CUE", bundle.reasons)
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in extract_spans(lines)]
        candidate = next(row for row in candidate_records("test-paper", occurrences) if row["source_relation"] == "MULTI_SPAN_DERIVED")
        self.assertIn("EXPLICIT_DERIVATION_CUE", candidate["reason_codes"])

    def test_theorem_like_environment(self) -> None:
        lines = [r"\begin{document}", r"\begin{thm}", "Every code corrects the stated errors.", r"\end{thm}", r"\end{document}"]
        spans = extract_spans(lines)
        theorem = next(span for span in spans if span.kind == "THEOREM_LIKE_ENVIRONMENT")
        self.assertEqual((theorem.start, theorem.end, theorem.speech_act), (2, 4, "MATHEMATICAL_ASSERTION"))

    def test_definition_like_environment(self) -> None:
        lines = [r"\begin{document}", r"\begin{defn}", "A free state is a convex combination of stabilizer states.", r"\end{defn}", r"\end{document}"]
        spans = extract_spans(lines)
        definition = next(span for span in spans if span.kind == "DEFINITION_ENVIRONMENT")
        self.assertEqual((definition.start, definition.end, definition.speech_act), (2, 4, "DEFINITION"))

    def test_environment_matching_rejects_arbitrary_substrings(self) -> None:
        lines = [r"\begin{document}", r"\begin{problem}", "Every code corrects the errors.", r"\end{problem}", r"\begin{definitionbox}", "A free state is specified.", r"\end{definitionbox}", r"\end{document}"]
        self.assertFalse(any(span.kind in {"THEOREM_LIKE_ENVIRONMENT", "DEFINITION_ENVIRONMENT"} for span in extract_spans(lines)))

    def test_deterministic_ids_hashes_and_one_based_lines(self) -> None:
        lines = [r"\begin{document}", "We prove that every state satisfies the bound.", r"\end{document}"]
        paths = section_paths([strip_comment(line) for line in lines])
        span = next(span for span in extract_spans(lines) if span.kind == "PROSE_PARAGRAPH")
        args = ("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span)
        first = occurrence_record(*args)
        second = occurrence_record(*args)
        self.assertEqual(first, second)
        self.assertEqual((first["line_start"], first["line_end"]), (2, 2))
        self.assertEqual(first["verbatim_source_text"], lines[1])
        candidates = candidate_records("test-paper", [first])
        self.assertEqual(candidates, candidate_records("test-paper", [second]))
        self.assertTrue(first["id"].endswith(first["content_hash"][7:23]))
        self.assertTrue(candidates[0]["id"].endswith(candidates[0]["canonical_content_hash"][7:23]))

    def test_invalid_line_range_is_rejected_at_runtime(self) -> None:
        lines = ["only line"]
        with self.assertRaisesRegex(ValueError, "invalid 1-based inclusive range"):
            occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, [[]], extractor.Span(2, 1, "PROSE_PARAGRAPH", "MATHEMATICAL_ASSERTION", ("REVIEW_REQUIRED",)))

    def test_repeated_occurrences_are_preserved_when_candidates_merge(self) -> None:
        lines = [
            r"\begin{document}",
            "We prove that every state satisfies the bound.",
            "",
            "We prove that every state satisfies the bound.",
            r"\end{document}",
        ]
        paths = section_paths([strip_comment(line) for line in lines])
        prose = [span for span in extract_spans(lines) if span.kind == "PROSE_PARAGRAPH"]
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in prose]
        candidates = candidate_records("test-paper", occurrences)

        self.assertEqual([(row["line_start"], row["line_end"]) for row in occurrences], [(2, 2), (4, 4)])
        self.assertEqual(len({row["id"] for row in occurrences}), 2)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(set(candidates[0]["occurrence_refs"]), {row["id"] for row in occurrences})

    def test_equation_bundle_candidate_references_its_component_spans(self) -> None:
        lines = [
            r"\begin{document}",
            "We show that every admissible state satisfies the following identity.",
            r"\begin{equation}",
            "x = 1",
            r"\end{equation}",
            "Thus the resulting quantity is bounded for every admissible state.",
            r"\end{document}",
        ]
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [
            occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span)
            for span in extract_spans(lines)
        ]
        occurrence_by_id = {row["id"]: row for row in occurrences}
        bundle = next(row for row in candidate_records("test-paper", occurrences) if row["source_relation"] == "MULTI_SPAN_DERIVED")

        self.assertGreaterEqual(len(bundle["occurrence_refs"]), 2)
        referenced_kinds = {occurrence_by_id[ref]["span_kind"] for ref in bundle["occurrence_refs"]}
        self.assertTrue({"EQUATION_DISCOURSE_BUNDLE", "DISPLAY_EQUATION", "PROSE_PARAGRAPH"} <= referenced_kinds)

    def test_partial_theorem_environment_is_not_marked_exact(self) -> None:
        lines = [r"\begin{document}", r"\begin{thm}", "Every code corrects the stated errors.", r"\end{thm}", r"\end{document}"]
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in extract_spans(lines)]
        candidate = next(row for row in candidate_records("test-paper", occurrences) if row["speech_act"] == "MATHEMATICAL_ASSERTION")
        self.assertEqual(candidate["source_relation"], "INTERPRETIVE")
        self.assertEqual(candidate["statement"]["conclusion"]["parse_status"], "PARTIAL")

    def test_unrelated_adjacent_claims_do_not_create_graph_edges(self) -> None:
        lines = [r"\begin{document}", "We show that every magic state satisfies the upper bound.", "", "We prove that every code corrects the specified errors.", r"\end{document}"]
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in extract_spans(lines)]
        candidates = candidate_records("test-paper", occurrences)
        self.assertEqual(graph_record("test-paper", candidates, occurrences)["edges"], [])

    def test_internal_biconditional_does_not_create_previous_claim_relation(self) -> None:
        lines = [r"\begin{document}", "We show that every magic state satisfies the upper bound.", "", "A magic state satisfies the upper bound if and only if its witness is feasible.", r"\end{document}"]
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in extract_spans(lines)]
        candidates = candidate_records("test-paper", occurrences)
        graph = graph_record("test-paper", candidates, occurrences)
        self.assertFalse(any(edge["edge_type"] == "EQUIVALENCE_CANDIDATE" for edge in graph["edges"]))

    def test_graph_direction_is_support_to_dependent(self) -> None:
        lines = [r"\begin{document}", "We show that every magic state satisfies the upper bound.", "", "Thus every magic state satisfies the resulting bound.", r"\end{document}"]
        paths = section_paths([strip_comment(line) for line in lines])
        occurrences = [occurrence_record("arxiv:test", "test-paper", "paper.tex", "0" * 64, lines, paths, span) for span in extract_spans(lines)]
        candidates = candidate_records("test-paper", occurrences)
        graph = graph_record("test-paper", candidates, occurrences)
        edge = next(row for row in graph["edges"] if row["edge_type"] == "DERIVATION")
        self.assertEqual((edge["source"], edge["target"]), (candidates[0]["id"], candidates[1]["id"]))
        self.assertIn("EXPLICIT_DERIVATION_CUE", edge["reason_codes"])
        self.assertGreaterEqual(len(edge["evidence_occurrence_refs"]), 2)

    def test_source_hash_mismatch_fails_before_any_output_write(self) -> None:
        bad_papers = (("arxiv:test", "test-paper", "paper.tex", "0" * 64),)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "registry"
            (root / "paper.tex").write_text("different bytes")
            manifest = root / "Stabilizerness/PaperAgentRegistry/manifests/test-paper.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"paper_id": "arxiv:test", "source": {"canonical_artifact": "paper.tex", "artifact_hash": "sha256:" + "0" * 64}}))
            with mock.patch.object(extractor, "PAPERS", bad_papers), mock.patch.object(extractor, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "source hash mismatch for paper.tex"):
                    generate(output)
            self.assertFalse(output.exists())

    def test_agent_manifest_mismatch_fails_before_any_output_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "registry"
            source = root / "paper.tex"
            source.write_text("canonical bytes")
            expected = hashlib.sha256(source.read_bytes()).hexdigest()
            papers = (("arxiv:test", "test-paper", "paper.tex", expected),)
            manifest = root / "Stabilizerness/PaperAgentRegistry/manifests/test-paper.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"paper_id": "arxiv:test", "source": {"canonical_artifact": "wrong.tex", "artifact_hash": f"sha256:{expected}"}}))
            with mock.patch.object(extractor, "PAPERS", papers), mock.patch.object(extractor, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "agent manifest artifact mismatch"):
                    generate(output)
            self.assertFalse(output.exists())


class GeneratedRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "registry"
        cls.manifest = generate(cls.output)
        schema_dir = OUTPUT / "schema"
        cls.schemas = {
            "occurrences.jsonl": json.loads((schema_dir / "source-claim-occurrence.schema.json").read_text()),
            "canonical-candidates.jsonl": json.loads((schema_dir / "canonical-semantic-candidate.schema.json").read_text()),
            "modules.json": json.loads((schema_dir / "canonical-claim-module.schema.json").read_text()),
            "graph.json": json.loads((schema_dir / "candidate-graph.schema.json").read_text()),
            "paper-delta.json": json.loads((schema_dir / "paper-delta.schema.json").read_text()),
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_all_records_validate_and_references_resolve(self) -> None:
        for paper in self.manifest["papers"]:
            directory = self.output / "papers" / paper["slug"]
            occurrences = [json.loads(line) for line in (directory / "occurrences.jsonl").read_text().splitlines() if line]
            candidates = [json.loads(line) for line in (directory / "canonical-candidates.jsonl").read_text().splitlines() if line]
            modules = json.loads((directory / "modules.json").read_text())
            graph = json.loads((directory / "graph.json").read_text())
            delta = json.loads((directory / "paper-delta.json").read_text())
            for row in occurrences:
                jsonschema.validate(row, self.schemas["occurrences.jsonl"])
            for row in candidates:
                jsonschema.validate(row, self.schemas["canonical-candidates.jsonl"])
            for row in modules:
                jsonschema.validate(row, self.schemas["modules.json"])
            jsonschema.validate(graph, self.schemas["graph.json"])
            jsonschema.validate(delta, self.schemas["paper-delta.json"])
            occurrence_ids = {row["id"] for row in occurrences}
            candidate_ids = {row["id"] for row in candidates}
            self.assertEqual(len(occurrence_ids), len(occurrences))
            self.assertEqual(len(candidate_ids), len(candidates))
            self.assertTrue(all(set(row["occurrence_refs"]) <= occurrence_ids for row in candidates))
            self.assertEqual(set(graph["nodes"]), candidate_ids)
            self.assertTrue(all(edge["source"] in candidate_ids and edge["target"] in candidate_ids for edge in graph["edges"]))

    def test_every_artifact_is_provisional_and_referentially_complete(self) -> None:
        graph_edge_count = 0
        multi_span_count = 0
        for paper in self.manifest["papers"]:
            directory = self.output / "papers" / paper["slug"]
            expected_files = {
                "occurrences.jsonl",
                "canonical-candidates.jsonl",
                "modules.json",
                "graph.json",
                "paper-delta.json",
            }
            self.assertEqual({path.name for path in directory.iterdir() if path.is_file()}, expected_files)

            occurrences = [json.loads(line) for line in (directory / "occurrences.jsonl").read_text().splitlines() if line]
            candidates = [json.loads(line) for line in (directory / "canonical-candidates.jsonl").read_text().splitlines() if line]
            modules = json.loads((directory / "modules.json").read_text())
            graph = json.loads((directory / "graph.json").read_text())
            delta = json.loads((directory / "paper-delta.json").read_text())
            occurrence_ids = {row["id"] for row in occurrences}
            candidate_ids = {row["id"] for row in candidates}

            self.assertTrue(all(row["candidate_status"] == "PROVISIONAL" for row in occurrences))
            self.assertTrue(all(row["candidate_status"] == "PROVISIONAL" for row in candidates))
            self.assertTrue(all(row["candidate_status"] == "PROVISIONAL" for row in modules))
            self.assertEqual(graph["graph_status"], "PROVISIONAL_NOT_VERIFIED_DAG")
            self.assertEqual({ref for row in candidates for ref in row["occurrence_refs"]}, occurrence_ids)

            module_refs = {
                ref
                for module in modules
                for field in ("assumption_contracts", "definitions", "core_claims", "derived_exports", "unresolved_review_queue")
                for ref in module[field]
            }
            module_ref_list = [
                ref
                for module in modules
                for field in ("assumption_contracts", "definitions", "core_claims", "derived_exports", "unresolved_review_queue")
                for ref in module[field]
            ]
            self.assertEqual(collections.Counter(module_ref_list), collections.Counter({candidate_id: 1 for candidate_id in candidate_ids}))
            self.assertEqual(collections.Counter(row["candidate_ref"] for row in delta["dispositions"]), collections.Counter({candidate_id: 1 for candidate_id in candidate_ids}))
            self.assertTrue(all(row["status"] == "REVIEW_REQUIRED" for row in delta["dispositions"]))

            for edge in graph["edges"]:
                self.assertIs(edge["candidate_only"], True)
                self.assertEqual(edge["status"], "REVIEW_REQUIRED")
                self.assertTrue(edge["shared_terms"])
                self.assertFalse({"mathrm", "mathcal", "mathbf", "text", "label", "ref", "eqref", "begin", "end"} & set(edge["shared_terms"]))
            for row in delta["dispositions"]:
                if row["comparison_evidence"][0]["method"] == "NO_CONSERVATIVE_MATCH":
                    self.assertEqual(row["baseline_record_refs"], [])
            graph_edge_count += len(graph["edges"])

            for candidate in candidates:
                if candidate["source_relation"] == "MULTI_SPAN_DERIVED":
                    multi_span_count += 1
                    self.assertGreaterEqual(len(candidate["occurrence_refs"]), 2)

        self.assertGreater(graph_edge_count, 0)
        self.assertGreater(multi_span_count, 0)

    def test_graph_sign_set_collapse_has_one_precise_baseline_link(self) -> None:
        slug = "graph-theoretic-nonstabilizerness"
        directory = self.output / "papers" / slug
        occurrences = [json.loads(line) for line in (directory / "occurrences.jsonl").read_text().splitlines()]
        candidates = [json.loads(line) for line in (directory / "canonical-candidates.jsonl").read_text().splitlines()]
        delta = json.loads((directory / "paper-delta.json").read_text())
        occurrence_by_id = {row["id"]: row for row in occurrences}
        disposition_by_id = {row["candidate_ref"]: row for row in delta["dispositions"]}
        candidate = next(row for row in candidates if any(occurrence_by_id[ref]["line_start"] == 546 for ref in row["occurrence_refs"]))
        disposition = disposition_by_id[candidate["id"]]
        expected = "math-claim-ir:graph-theoretic-nonstabilizerness:sign-set-collapse"
        unrelated = {
            "math-claim-ir:graph-theoretic-nonstabilizerness:relaxed-affine-span",
            "math-claim-ir:graph-theoretic-nonstabilizerness:relaxed-dual-vertex-form",
            "math-claim-ir:graph-theoretic-nonstabilizerness:relaxed-primal-feasibility",
            "math-claim-ir:graph-theoretic-nonstabilizerness:relaxed-primal-lower-bound",
        }
        self.assertEqual(disposition["baseline_record_refs"], [expected])
        self.assertEqual(disposition["disposition"], "unresolved")
        self.assertIn("PARTIAL_STATEMENT_MATCH_RELATION_UNRESOLVED", disposition["reason_codes"])
        self.assertFalse(unrelated & set(disposition["baseline_record_refs"]))
        self.assertEqual(disposition["comparison_evidence"][0]["method"], "CONSERVATIVE_STATEMENT_MATCH")
        possible = {row["possible_baseline_ref"] for row in disposition["possible_baseline_region_refs"]}
        self.assertTrue(unrelated & possible)

    def test_frozen_nonempty_dependency_definition_is_not_mwis_prerequisite(self) -> None:
        slug = "graph-theoretic-nonstabilizerness"
        directory = self.output / "papers" / slug
        candidates = [json.loads(line) for line in (directory / "canonical-candidates.jsonl").read_text().splitlines()]
        graph = json.loads((directory / "graph.json").read_text())
        source = next(row for row in candidates if "A dependency is a nonempty inclusion-minimal subset" in extractor.candidate_text(row))
        target = next(row for row in candidates if "maximum-weight independent set (MWIS) value is defined" in extractor.candidate_text(row))
        pair = {source["id"], target["id"]}
        self.assertFalse(any({edge["source"], edge["target"]} == pair for edge in graph["edges"]))

    def test_manifest_summaries_match_generated_records(self) -> None:
        for paper in self.manifest["papers"]:
            directory = self.output / "papers" / paper["slug"]
            occurrences = [json.loads(line) for line in (directory / "occurrences.jsonl").read_text().splitlines() if line]
            candidates = [json.loads(line) for line in (directory / "canonical-candidates.jsonl").read_text().splitlines() if line]
            modules = json.loads((directory / "modules.json").read_text())
            graph = json.loads((directory / "graph.json").read_text())
            delta = json.loads((directory / "paper-delta.json").read_text())

            self.assertEqual(paper["occurrence_count"], len(occurrences))
            self.assertEqual(paper["candidate_count"], len(candidates))
            self.assertEqual(paper["module_count"], len(modules))
            self.assertEqual(paper["graph_edge_count"], len(graph["edges"]))
            self.assertEqual(paper["speech_act_distribution"], dict(collections.Counter(row["speech_act"] for row in occurrences)))
            self.assertEqual(paper["span_kind_distribution"], dict(collections.Counter(row["span_kind"] for row in occurrences)))
            self.assertEqual(paper["occurrence_status_distribution"], dict(collections.Counter(row["candidate_status"] for row in occurrences)))
            self.assertEqual(paper["candidate_status_distribution"], dict(collections.Counter(row["candidate_status"] for row in candidates)))
            self.assertEqual(paper["source_relation_distribution"], dict(collections.Counter(row["source_relation"] for row in candidates)))
            self.assertEqual(paper["graph_edge_type_distribution"], dict(collections.Counter(row["edge_type"] for row in graph["edges"])))
            self.assertEqual(paper["paper_delta_disposition_distribution"], dict(collections.Counter(row["disposition"] for row in delta["dispositions"])))
            refs = [ref for row in delta["dispositions"] for ref in row["baseline_record_refs"]]
            methods = collections.Counter(evidence["method"] for row in delta["dispositions"] for evidence in row["comparison_evidence"])
            self.assertEqual(paper["paper_delta_baseline_reference_count"], len(refs))
            self.assertEqual(paper["paper_delta_linked_candidate_count"], sum(bool(row["baseline_record_refs"]) for row in delta["dispositions"]))
            self.assertEqual(paper["paper_delta_unique_baseline_count"], len(set(refs)))
            self.assertEqual(paper["paper_delta_evidence_method_distribution"], dict(methods))
            self.assertEqual(paper["paper_delta_possible_region_count"], sum(len(row["possible_baseline_region_refs"]) for row in delta["dispositions"]))
            self.assertEqual(paper["paper_delta_max_refs_per_candidate"], max((len(row["baseline_record_refs"]) for row in delta["dispositions"]), default=0))
            self.assertEqual(paper["review_required_occurrence_count"], sum("REVIEW_REQUIRED" in row["reason_codes"] for row in occurrences))
            self.assertEqual(paper["unresolved_occurrence_count"], sum(row["speech_act"] == "UNRESOLVED" for row in occurrences))

    def test_ranges_and_verbatim_text_are_externally_checkable(self) -> None:
        papers = {slug: (artifact, expected) for _, slug, artifact, expected in PAPERS}
        for paper in self.manifest["papers"]:
            artifact, expected_hash = papers[paper["slug"]]
            path = ROOT / artifact
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected_hash)
            lines = path.read_text().splitlines()
            occurrence_path = self.output / "papers" / paper["slug"] / "occurrences.jsonl"
            for raw in occurrence_path.read_text().splitlines():
                row = json.loads(raw)
                self.assertGreaterEqual(row["line_start"], 1)
                self.assertLessEqual(row["line_start"], row["line_end"])
                self.assertLessEqual(row["line_end"], len(lines))
                self.assertEqual(row["verbatim_source_text"], "\n".join(lines[row["line_start"] - 1:row["line_end"]]))

    def test_occurrence_schema_rejects_missing_review_reason(self) -> None:
        paper = self.manifest["papers"][0]
        path = self.output / "papers" / paper["slug"] / "occurrences.jsonl"
        row = json.loads(path.read_text().splitlines()[0])
        row["reason_codes"] = [code for code in row["reason_codes"] if code != "REVIEW_REQUIRED"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["occurrences.jsonl"])

    def test_candidate_schema_rejects_missing_review_reason(self) -> None:
        paper = self.manifest["papers"][0]
        path = self.output / "papers" / paper["slug"] / "canonical-candidates.jsonl"
        row = json.loads(path.read_text().splitlines()[0])
        row["reason_codes"] = [code for code in row["reason_codes"] if code != "REVIEW_REQUIRED"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["canonical-candidates.jsonl"])

    def test_candidate_schema_rejects_resolved_unresolved_overlap(self) -> None:
        paper = self.manifest["papers"][0]
        path = self.output / "papers" / paper["slug"] / "canonical-candidates.jsonl"
        row = next(json.loads(line) for line in path.read_text().splitlines() if json.loads(line)["statement"]["conclusion"] is not None)
        row["statement"]["unresolved"] = {"source_text": "ambiguous", "issues": ["conflict"]}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["canonical-candidates.jsonl"])

    def test_delta_schema_rejects_recognized_relation_without_baseline_ref(self) -> None:
        paper = self.manifest["papers"][0]
        delta = json.loads((self.output / "papers" / paper["slug"] / "paper-delta.json").read_text())
        row = copy.deepcopy(delta)
        row["dispositions"][0]["disposition"] = "equivalent"
        row["dispositions"][0]["baseline_record_refs"] = []
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["paper-delta.json"])

    def test_delta_schema_reused_requires_exact_representation_method(self) -> None:
        paper = self.manifest["papers"][0]
        row = json.loads((self.output / "papers" / paper["slug"] / "paper-delta.json").read_text())
        item = row["dispositions"][0]
        item["disposition"] = "reused"
        item["baseline_record_refs"] = ["math-claim-ir:test:baseline"]
        item["comparison_evidence"] = [{"method": "CONSERVATIVE_STATEMENT_MATCH", "baseline_ref": "math-claim-ir:test:baseline", "representation": "structured_conclusion", "occurrence_refs": ["source-claim-occurrence:test:one"], "shared_terms": ["active", "dependencies", "sign"], "score": 0.8}]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["paper-delta.json"])

    def test_delta_schema_semantic_relation_requires_explicit_review_method(self) -> None:
        paper = self.manifest["papers"][0]
        row = json.loads((self.output / "papers" / paper["slug"] / "paper-delta.json").read_text())
        item = row["dispositions"][0]
        item["disposition"] = "equivalent"
        item["baseline_record_refs"] = ["math-claim-ir:test:baseline"]
        item["comparison_evidence"] = [{"method": "NO_CONSERVATIVE_MATCH", "detail": "not reviewed"}]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["paper-delta.json"])

    def test_delta_schema_new_to_registry_requires_absence_audit_method(self) -> None:
        paper = self.manifest["papers"][0]
        row = json.loads((self.output / "papers" / paper["slug"] / "paper-delta.json").read_text())
        item = row["dispositions"][0]
        item["disposition"] = "new-to-registry"
        item["reason_codes"] = ["REGISTRY_ABSENCE_CONFIRMED", "REVIEW_REQUIRED"]
        item["comparison_evidence"] = [{"method": "NO_CONSERVATIVE_MATCH", "detail": "not audited"}]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["paper-delta.json"])

    def test_delta_schema_statement_match_requires_method_fields(self) -> None:
        paper = self.manifest["papers"][0]
        row = json.loads((self.output / "papers" / paper["slug"] / "paper-delta.json").read_text())
        item = row["dispositions"][0]
        item["disposition"] = "unresolved"
        item["baseline_record_refs"] = ["math-claim-ir:test:baseline"]
        item["comparison_evidence"] = [{"method": "CONSERVATIVE_STATEMENT_MATCH", "baseline_ref": "math-claim-ir:test:baseline", "representation": "structured_conclusion", "occurrence_refs": [item["candidate_ref"].replace("provisional-claim:", "source-claim-occurrence:")]}]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(row, self.schemas["paper-delta.json"])

    def test_candidate_schema_enforces_unresolved_coupling(self) -> None:
        paper = self.manifest["papers"][0]
        rows = [json.loads(line) for line in (self.output / "papers" / paper["slug"] / "canonical-candidates.jsonl").read_text().splitlines()]
        unresolved = copy.deepcopy(next(row for row in rows if row["speech_act"] == "UNRESOLVED"))
        unresolved["source_relation"] = "INTERPRETIVE"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(unresolved, self.schemas["canonical-candidates.jsonl"])
        unresolved["source_relation"] = "UNRESOLVED"
        unresolved["statement"]["unresolved"]["source_text"] = ""
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(unresolved, self.schemas["canonical-candidates.jsonl"])

    def test_procedural_validation_rejects_duplicate_module_candidate(self) -> None:
        paper = self.manifest["papers"][0]
        directory = self.output / "papers" / paper["slug"]
        occurrences = [json.loads(line) for line in (directory / "occurrences.jsonl").read_text().splitlines()]
        candidates = [json.loads(line) for line in (directory / "canonical-candidates.jsonl").read_text().splitlines()]
        modules = json.loads((directory / "modules.json").read_text())
        graph = json.loads((directory / "graph.json").read_text())
        delta = json.loads((directory / "paper-delta.json").read_text())
        modules[0]["unresolved_review_queue"].append(candidates[0]["id"])
        with self.assertRaisesRegex(RuntimeError, "covered exactly once"):
            validate_paper_artifacts(paper["slug"], occurrences, candidates, modules, graph, delta)

    def test_static_registry_integrity_detects_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory)
            for relative in extractor.STATIC_REGISTRY_FILES:
                destination = registry / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((OUTPUT / relative).read_bytes())
            manifest = {"static_file_hashes": extractor.static_registry_hashes(registry)}
            (registry / "manifest.json").write_text(json.dumps(manifest))
            validate_static_registry_integrity(registry)
            (registry / "README.md").write_text("drift")
            with self.assertRaisesRegex(RuntimeError, "integrity mismatch"):
                validate_static_registry_integrity(registry)

    def test_generation_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as second_temp:
            second = Path(second_temp) / "registry"
            generate(second)
            first_files = {path.relative_to(self.output): path.read_bytes() for path in self.output.rglob("*") if path.is_file()}
            second_files = {path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()}
            self.assertEqual(first_files, second_files)


if __name__ == "__main__":
    unittest.main()
