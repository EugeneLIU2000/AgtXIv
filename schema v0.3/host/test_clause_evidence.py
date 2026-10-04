"""Targeted, offline regression cases. Running these requires user authorization."""
from copy import deepcopy
import unittest

from core import digest
from clause_evidence import bind_clause_report, clause_binding_coverage
from clause_coverage import candidate_clause_status


class ClauseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.text = "背景。目标结论。其他结论。"
        self.source = {"path": "paper.tex", "text": self.text,
                       "sha256": digest(self.text.encode())}
        quote = "目标结论。"
        start = self.text.encode().find(quote.encode())
        self.node = {"id": "claim:target", "source_spans": [{
            "path": "paper.tex", "sha256": self.source["sha256"],
            "byte_start": start, "byte_end": start + len(quote.encode()),
            "offset_unit": "BYTE", "interval": "HALF_OPEN"}]}
        self.row = {"clause_id": "conclusion", "statement": "目标结论",
                    "source_role": "THEOREM_STATEMENT", "source_evidence_description": "目标定理",
                    "source_path": "paper.tex", "source_quote": quote,
                    "pdf_region_indices": [], "relation": "CANDIDATE_EQUIVALENT",
                    "remaining_obligations": []}

    def bind(self, row=None, node=None):
        return bind_clause_report([row or self.row], [self.source], node or self.node)

    def test_utf8_positions_and_unaccepted_semantics(self):
        evidence = self.bind()
        span = evidence["coverage"][0]["source_spans"][0]
        self.assertEqual(span["byte_start"], len("背景。".encode()))
        self.assertEqual(span["span_sha256"], digest("目标结论。".encode()))
        self.assertFalse(evidence["inventory_complete"])
        self.assertFalse(evidence["source_alignment_accepted"])
        self.assertEqual(candidate_clause_status([{"clause_coverage": evidence["coverage"]}]),
                         "MAPPED_INVENTORY_UNREVIEWED")

    def test_real_quote_elsewhere_does_not_cover_target(self):
        row = dict(self.row, source_quote="其他结论。")
        evidence = self.bind(row)
        self.assertEqual(evidence["unbound"][0]["status"], "OUTSIDE_TARGET_NODE_SOURCE_SCOPE")
        self.assertEqual(clause_binding_coverage(evidence), [])

    def test_cross_boundary_quote_not_accepted(self):
        evidence = self.bind(dict(self.row, source_quote="背景。目标结论。"))
        self.assertEqual(clause_binding_coverage(evidence), [])

    def test_changed_target_source_digest(self):
        node = deepcopy(self.node)
        node["source_spans"][0]["sha256"] = digest(b"other")
        self.assertEqual(clause_binding_coverage(self.bind(node=node)), [])

    def test_ambiguous_quote_rejected(self):
        source = dict(self.source, text=self.text + "目标结论。")
        source["sha256"] = digest(source["text"].encode())
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS"):
            bind_clause_report([self.row], [source], self.node)

    def test_partial_mapping_stops_candidate_flow(self):
        for relation in ("PARTIAL", "STRONGER", "WEAKER", "UNRESOLVED"):
            with self.subTest(relation=relation):
                evidence = self.bind(dict(self.row, relation=relation))
                self.assertEqual(candidate_clause_status([{"clause_coverage": evidence["coverage"]}]),
                                 "INCOMPLETE")

    def test_one_unlocated_clause_does_not_disappear(self):
        missing = dict(self.row, clause_id="missing", source_role="NOT_LOCATED",
                       source_evidence_description="", source_path="", source_quote="")
        evidence = bind_clause_report([self.row, missing], [self.source], self.node)
        self.assertEqual(len(evidence["coverage"]), 1)
        self.assertEqual(len(evidence["unbound"]), 1)
        self.assertEqual(clause_binding_coverage(evidence), [])

    def test_legacy_missing_mapping_is_unknown(self):
        self.assertEqual(candidate_clause_status([{"declaration": "Old.theorem"}]), "UNRECORDED")
        old = bind_clause_report([self.row], [self.source])
        self.assertNotIn("scope_protocol", old)

    def test_duplicate_clause_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATED"):
            bind_clause_report([self.row, self.row], [self.source], self.node)

    def test_pdf_regions_are_selected_not_replaced(self):
        region = {"kind": "PDF_PAGE_REGION", "page": 1, "pdf": {"sha256": "frozen-pdf"},
                  "page_image": {"sha256": "frozen-image"}, "normalized_rectangle": [0, 0, 1, 1]}
        # Minimal already-bound context fixture; asset validation belongs to
        # pdf_proof_context and is deliberately outside this offline unit scope.
        context = {"kind": "RetainedPDFProofContext", "page_regions": [region]}
        node = {"id": "pdf:claim", "source_spans": [region]}
        row = dict(self.row, source_path="", source_quote="", pdf_region_indices=[0])
        evidence = bind_clause_report([row], [context], node)
        self.assertEqual(evidence["coverage"][0]["source_spans"], [region])
        evidence["coverage"][0]["source_spans"][0]["page"] = 99
        self.assertEqual(region["page"], 1)
        for indices in ([True], [-1], [1], [0, 0]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                bind_clause_report([dict(row, pdf_region_indices=indices)], [context], node)


if __name__ == "__main__":
    unittest.main()
