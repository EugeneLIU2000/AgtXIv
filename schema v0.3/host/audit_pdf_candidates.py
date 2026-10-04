"""Audit one retained PDF-region graph without rendering or mathematical acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from core import canonical, digest, utcnow, write_json
from graph import prune_graph


class Audit:
    def __init__(self):
        self.issues, self.files = [], {}
        self.report_kind = "PDFRegionIntegrityAudit"

    def require(self, condition, code, subject=None):
        if not condition:
            self.issues.append({"code": code, "subject": subject})

    def file(self, path):
        path = Path(path).resolve()
        with path.open("rb") as stream:
            raw = stream.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("Audit input exceeds the byte ceiling")
        ref = {"path": str(path), "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}
        self.require(str(path) not in self.files or self.files[str(path)] == ref, "BYTES_CHANGED", str(path))
        self.files[str(path)] = ref
        return raw

    def ref(self, ref, *, json_value=False):
        raw = self.file(ref["path"])
        self.require(ref == self.files[str(Path(ref["path"]).resolve())], "REFERENCE_MISMATCH", ref["path"])
        return json.loads(raw) if json_value else raw

    def run(self, directory):
        directory = Path(directory).resolve()
        summary = json.loads(self.file(directory / "summary.json"))
        if summary.get("kind") == "PDFReadingAmendmentRun":
            from pdf_amendment_run import reconstruct_amendment
            self.report_kind = "PDFReadingAmendmentIntegrityAudit"
            run_ref = self.files[str(directory / "summary.json")]
            reconstruct_amendment(run_ref)
            return {"kind": self.report_kind, "created_at": utcnow(),
                "run": run_ref, "integrity_status": "PASS", "issues": [],
                "source_alignment_accepted": False, "mathematical_status": "CHAIN_INCOMPLETE",
                "scope_notes": [
                    "Reconstructs one normally completed local reading amendment and its source run.",
                    "Compares the proposal, changed rows, context associations and candidate assembly.",
                    "Does not establish semantics, assumption discharge, coverage or Lean correctness.",
                    "Does not audit recursive source admission, publication, failure or interruption."]}
        if summary.get("kind") in {"PDFModelExtractionRun", "PDFModelExtractionRecoveryRun"}:
            from pdf_extract_recover import model_run_binding, recovery_binding
            recovery = summary["kind"] == "PDFModelExtractionRecoveryRun"
            self.report_kind = "PDFModelRecoveryIntegrityAudit" if recovery else "PDFModelExtractionIntegrityAudit"
            run_ref = self.files[str(directory / "summary.json")]
            (recovery_binding if recovery else model_run_binding)(run_ref)
            return {"kind": self.report_kind, "created_at": utcnow(),
                "run": run_ref, "integrity_status": "PASS", "issues": [],
                "source_alignment_accepted": False, "mathematical_status": "CHAIN_INCOMPLETE",
                "scope_notes": [
                    "Reconstructs retained model output with the shared source binding and PDF adapter.",
                    "Checks frozen routing, source/page inputs, response schema, candidate assembly and graph.",
                    "Does not call a model, execute historical Python, rerender pages or accept mathematical semantics.",
                    "Does not establish extraction completeness, earliest origins, proof sufficiency or Lean correctness."]}
        if summary.get("kind") != "PDFRegionCandidateRun":
            raise ValueError("PDF_AUDIT_RUN_KIND_UNSUPPORTED")
        frozen = {}
        for name, item in summary["inputs"].items():
            raw = self.ref(item["retained"])
            self.require(raw == self.ref(item["original"]), "INPUT_SNAPSHOT_MISMATCH", name)
            frozen[name] = json.loads(raw)
        runtime = summary.get("runtime_sources", [])
        self.require({Path(item["snapshot"]["path"]).name for item in runtime} ==
                     {"pdf_candidates.py", "core.py", "graph.py", "chunks.py"}, "RUNTIME_SNAPSHOT_MISSING")
        for item in runtime:
            self.ref(item["snapshot"])
        reading, candidates = frozen["reading"], frozen["candidates"]
        from jsonschema import Draft202012Validator
        schema = json.loads(self.file(Path(__file__).resolve().parents[1] / "schemas/research.schema.json"))
        region_validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/PDFPageRegion"})
        document = self.ref(summary["document"], json_value=True)
        assembly = self.ref(summary["assembly"], json_value=True)
        graph = self.ref(summary["graph"], json_value=True)
        pdf = self.ref(document["pdf"])
        self.require(pdf.startswith(b"%PDF-") and pdf == self.ref(reading["pdf"]), "PDF_SNAPSHOT_MISMATCH")
        self.require(document["original_pdf"] == reading["pdf"], "PDF_ORIGINAL_REFERENCE_MISMATCH")
        self.require(self.ref(document["derived_text"]) == self.ref(reading["derived_text"]), "DERIVED_TEXT_MISMATCH")
        receipt = self.ref(document["page_count_receipt"], json_value=True)
        log = self.file(directory / "pdfinfo.log")
        match = re.search(rb"(?m)^Pages:\s+(\d+)\s*$", log)
        self.require(receipt["input_sha256"] == document["pdf"]["sha256"] and
                     receipt["output_sha256"] == digest(log) and receipt["exit_code"] == 0 and
                     receipt["status"] == "SUCCEEDED" and receipt["command"][1:] == [document["pdf"]["path"]],
                     "PAGE_INVENTORY_RECEIPT_MISMATCH")
        self.require(match is not None and int(match[1]) == document["page_count"] == len(document["pages"]) ==
                     len(reading["page_images"]), "PAGE_COUNT_MISMATCH")
        for index, page in enumerate(document["pages"]):
            image = self.ref(page["image"])
            self.require(image == self.ref(reading["page_images"][index]) and page["page"] == index + 1 and
                         image[:8] == b"\x89PNG\r\n\x1a\n" and image[12:16] == b"IHDR" and
                         page["width"] == int.from_bytes(image[16:20], "big") and
                         page["height"] == int.from_bytes(image[20:24], "big"), "PAGE_IMAGE_MISMATCH", index + 1)
        self.require(document["reported_visually_read_pages"] == reading["pages_visually_read"] and
                     document["reading_report_is_attributed_not_independently_observed"] is True and
                     document["ocr_is_authoritative_math"] is False and document["source_completeness_asserted"] is False,
                     "READING_SCOPE_PROMOTED")
        rows = candidates["claims"]
        bound = {node["source_reading_id"]: node for node in assembly["nodes"] if "source_reading_id" in node}
        self.require(set(bound) == {row["id"] for row in rows}, "READING_ROWS_CHANGED")
        expected_queries, expected_contexts = set(), set()
        expected_requests, expected_groups = [], {}
        for row in rows:
            node = bound[row["id"]]
            role, source = row["role"], row["source"]
            span, = node["source_spans"]
            self.require(not list(region_validator.iter_errors(span)), "PDF_REGION_SCHEMA_MISMATCH", row["id"])
            box = span["normalized_rectangle"]
            self.require(len(box) == 4 and all(type(v) in {int, float} and math.isfinite(v) for v in box) and
                         0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1, "INVALID_PDF_RECTANGLE", row["id"])
            self.require(span["kind"] == "PDF_PAGE_REGION" and span["pdf"] == document["pdf"] and
                         source["pdf"] == document["original_pdf"] and span["page"] == source["page"] and
                         span["printed_page"] == source.get("printed_page") and box == source["region"] and
                         span["page_image"] == document["pages"][source["page"] - 1]["image"] and
                         span["coordinate_system"] == "TOP_LEFT_UNIT_SQUARE" and
                         span["binding_scope"] == "DOCUMENT_BYTES_PAGE_NUMBER_IMAGE_BYTES_AND_REGION_GEOMETRY_ONLY",
                         "SOURCE_REGION_CHANGED", row["id"])
            anchor = {**span, "pdf": span["pdf"]["sha256"], "page_image": span["page_image"]["sha256"]}
            expected_id = "claim:pdf:" + digest(canonical([candidates["source_identity"], anchor,
                                                         row["statement"], row["conditions"], role]))[7:31]
            self.require(node["id"] == expected_id and node["text"] == row["statement"] and
                         node["conditions"] == row["conditions"] and node["disposition"] == "AGENT_NORMALIZED_UNREVIEWED",
                         "CANDIDATE_STATEMENT_CHANGED", row["id"])
            expected_kind = "definition" if role == "DEFINITION" else "proof_context" if role == "CONTRADICTION_CONTEXT" else role.lower()
            self.require(node["kind"] == expected_kind, "READING_ROLE_CHANGED", row["id"])
            expected_blockers = ["PDF_LOCAL_PROOF_SCOPE_REQUIRES_ALIGNMENT"] if role in {"PROOF_LOCAL_CLAIM", "CONTRADICTION_CONTEXT"} else []
            if row.get("unresolved_dependencies"):
                expected_blockers.append("PDF_UNRESOLVED_DEPENDENCIES")
            self.require(("unresolved_dependencies" in node) == ("unresolved_dependencies" in row) and
                         node.get("unresolved_dependencies") == row.get("unresolved_dependencies"),
                         "UNRESOLVED_DEPENDENCIES_CHANGED", row["id"])
            self.require(node["blocked_by"] == expected_blockers, "LOCAL_SCOPE_BLOCKER_CHANGED", row["id"])
            (expected_contexts if role == "CONTRADICTION_CONTEXT" else expected_queries).add(node["id"])
            members = []
            for key in row["internal"]:
                found = [other for label, other in bound.items() if label == key or label.split(":")[-1] == key]
                self.require(len(found) == 1, "INTERNAL_REFERENCE_AMBIGUOUS", key)
                if len(found) == 1:
                    members.append(found[0]["id"])
            for citation in row["external"]:
                request_id = "request:pdf:" + digest(canonical([candidates["source_identity"], node["id"], citation]))[7:31]
                expected_requests.append({"id": request_id, "kind": "external_claim_request", "downstream_node_id": node["id"],
                    "cited_statement_label": citation, "upstream_paper_identity": None,
                    "identity_status": "BIBLIOGRAPHIC_LABEL_ONLY_REQUIRES_RESOLUTION", "source_spans": node["source_spans"]})
                members.append(request_id)
            if members:
                expected_groups[node["id"]] = set(members)
        self.require(set(assembly["query_ids"]) == expected_queries and set(assembly["nonasserted_context_ids"]) == expected_contexts,
                     "CONTRADICTION_CONTEXT_ASSERTED_OR_QUERY_CHANGED")
        self.require(assembly["dependency_requests"] == expected_requests, "EXTERNAL_REQUESTS_CHANGED")
        self.require(len(assembly["support_groups"]) == len(expected_groups) and
                     {group["target"]: set(group["members"]) for group in assembly["support_groups"]} == expected_groups and
                     all(group["disposition"] == "UNREVIEWED" and group["relation"] == "PROOF_DEPENDENCY" and
                         group["grouping_basis"] == "ATTRIBUTED_JOINT_SUPPORT_NOT_CHECKED_SUFFICIENCY" for group in assembly["support_groups"]),
                     "SUPPORT_GROUPS_CHANGED_OR_ACCEPTED")
        requests = {node["id"]: node for node in assembly["nodes"] if node["kind"] == "external_claim_request"}
        self.require(set(requests) == {item["id"] for item in expected_requests} and all(
            requests[item["id"]]["text"] == item["cited_statement_label"] and
            requests[item["id"]]["source_spans"] == item["source_spans"] and
            requests[item["id"]]["blocked_by"] == ["CITED_STATEMENT_NOT_READ"] for item in expected_requests),
            "EXTERNAL_FRONTIER_CHANGED")
        self.require(graph == prune_graph(assembly["nodes"], assembly["support_groups"], assembly["query_ids"]),
                     "GRAPH_REPLAY_MISMATCH")
        self.require(all(node["upstream_search"] == "FRONTIER" and not node.get("proof_discharged") and
                         not node.get("statement_discharged") for node in assembly["nodes"]) and
                     assembly["source_alignment_accepted"] is False and assembly["upstream_search_exhausted"] is False and
                     summary["source_alignment_accepted"] is False and summary["mathematical_status"] == "CHAIN_INCOMPLETE",
                     "MATHEMATICAL_STATUS_PROMOTED")
        self.require(summary["candidate_rows"] == len(rows) and summary["query_candidates"] == len(expected_queries) and
                     summary["nonasserted_proof_contexts"] == len(expected_contexts) and
                     summary["graph_nodes"] == len(graph["nodes"]) and summary["support_groups"] == len(graph["support_groups"]) and
                     summary["external_requests"] == len(expected_requests) and summary["new_model_calls"] == 0, "SUMMARY_COUNT_MISMATCH")
        return {"kind": "PDFRegionIntegrityAudit", "created_at": utcnow(), "run": str(directory),
            "integrity_status": "PASS" if not self.issues else "FAIL", "issues": self.issues,
            "checked_files": list(self.files.values()), "source_alignment_accepted": False,
            "mathematical_status": "CHAIN_INCOMPLETE", "scope_notes": [
                "Verifies retained bytes, page-inventory receipt, supplied region geometry, candidate roles and support graph replay.",
                "Does not rerender the PDF or independently establish image-to-PDF correspondence or visual reading.",
                "Does not accept OCR, mathematical statements, support sufficiency, complete extraction, or earliest origins."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Keep previous audit reports; choose a fresh filename")
    auditor = Audit()
    try:
        report = auditor.run(args.run)
    except Exception as error:
        report = {"kind": auditor.report_kind, "integrity_status": "FAIL", "issues": auditor.issues,
                  "error": type(error).__name__ + ": " + str(error), "source_alignment_accepted": False,
                  "mathematical_status": "CHAIN_INCOMPLETE"}
    write_json(args.output.resolve(), report)
    print(json.dumps({key: report[key] for key in ("kind", "integrity_status", "issues", "mathematical_status")}))
    raise SystemExit(0 if report["integrity_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
