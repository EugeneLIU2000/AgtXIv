"""Scoped artifact/location audit; never a scientific acceptance judgement."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import pathlib

from core import canonical, digest, utcnow, write_json
from model import _frozen_source_payload, bind_source_locators
from candidates import assemble_candidates, select_candidate_graph


def audit_anchor_candidates(paper, data, sources):
    anchors = {row["id"]: row for row in paper["anchors"]}
    occurrences = {row["id"] for row in paper["claims"]}
    bibliographies = {row["id"] for row in paper["bibliography"]}
    rows = data.get("classifications", [])
    issues, seen, bound = [], set(), []
    for index, row in enumerate(rows):
        aid = row.get("anchor_id")
        if aid not in anchors or aid in seen:
            issues.append({"row": index, "code": "UNKNOWN_OR_REPEATED_ANCHOR", "anchor_id": aid})
            continue
        seen.add(aid)
        original = anchors[aid]
        if row.get("classification") not in {"SUPPORT", "MENTION", "UNCERTAIN"}:
            issues.append({"row": index, "code": "UNKNOWN_ROLE"})
        if row.get("review_state") != "CANDIDATE_UNREVIEWED":
            issues.append({"row": index, "code": "CANDIDATE_REVIEW_STATUS_MISMATCH"})
        for field in ("command", "key"):
            if row.get(field) != original.get(field):
                issues.append({"row": index, "code": "ANCHOR_IDENTITY_MISMATCH", "field": field})
        for field in ("source_owner_occurrence_ids", "proof_owner_occurrence_ids", "target_occurrence_ids", "supported_occurrence_ids"):
            if set(row.get(field, [])) - occurrences:
                issues.append({"row": index, "code": "UNKNOWN_OCCURRENCE_REFERENCE", "field": field})
        if set(row.get("bibliography_target_ids", [])) - bibliographies:
            issues.append({"row": index, "code": "UNKNOWN_BIBLIOGRAPHY_REFERENCE"})
        evidence = row.get("evidence", {})
        if evidence.get("anchor_source") != original["source"]:
            issues.append({"row": index, "code": "ANCHOR_SPAN_MISMATCH"})
        result = bind_source_locators({"claims": [{"source_locators": [evidence]}]}, sources)
        if result["issues"]:
            issues.extend({**problem, "row": index} for problem in result["issues"])
            continue
        span = result["bindings"][0]["source"]
        original_span = original["source"]
        if (span["path"] != original_span["path"] or span["byte_start"] > original_span["byte_start"] or
                span["byte_end"] < original_span["byte_end"]):
            issues.append({"row": index, "code": "EVIDENCE_DOES_NOT_CONTAIN_ANCHOR"})
        else:
            bound.append({"anchor_id": aid, "evidence_source": span,
                          "candidate_role": row["classification"], "semantic_status": "AWAITING_REVIEW"})
    missing = sorted(set(anchors) - seen)
    return {"scope": "TARGET_PAPER_CANDIDATE_ANCHOR_LOCATIONS", "candidate_counts": dict(Counter(row.get("classification") for row in rows)),
            "supplied_anchors": len(anchors), "located_candidates": len(bound), "missing_anchor_ids": missing,
            "issues": issues, "bindings": bound, "location_status": "PASS" if not issues and not missing else "FAILED",
            "semantic_classification_status": "AWAITING_REVIEW", "accepted_support_edges": 0,
            "final_exclusions": 0}


def main():
    from jsonschema import Draft202012Validator
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=pathlib.Path)
    parser.add_argument("--extraction", required=True, type=pathlib.Path)
    parser.add_argument("--source-directory", required=True, type=pathlib.Path)
    parser.add_argument("--anchors", type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Audit output already exists; retain earlier evidence")
    paper = json.loads(args.extraction.read_bytes())
    sources = _frozen_source_payload(paper, args.source_directory, source_directory=args.source_directory)
    schema = json.loads((pathlib.Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
    errors, hashes = [], {}
    values = {}
    for name in ("plan.json", "ledger.json", "assembly.json", "graph.json", "candidate-input.json"):
        raw = (args.run / name).read_bytes()
        hashes[name] = digest(raw)
        values[name] = json.loads(raw)
    def validate(value, kind, artifact):
        validator = Draft202012Validator({"$ref": "#/$defs/" + kind, "$defs": schema["$defs"]})
        for error in validator.iter_errors(value):
            errors.append({"artifact": artifact, "path": list(error.absolute_path), "detail": error.message})
    validate(values["plan.json"], "Plan", "plan.json")
    validate(values["ledger.json"], "PlanLedger", "ledger.json")
    for group in values["graph.json"]["support_groups"]:
        validate(group, "SupportGroup", group["id"])
    if values["plan.json"]["query_ids"] != values["assembly.json"]["query_ids"]:
        errors.append({"artifact": "plan.json", "detail": "Plan query IDs differ from assembled queries"})
    if set(values["graph.json"]["query_ids"]) != set(values["assembly.json"]["query_ids"]):
        errors.append({"artifact": "graph.json", "detail": "Selected query IDs differ from assembled queries"})
    try:
        expected = assemble_candidates(paper, values["candidate-input.json"], sources,
                                       response_reference=values["assembly.json"]["response_reference"])
        if canonical(expected) != canonical(values["assembly.json"]):
            errors.append({"artifact": "assembly.json", "detail": "Assembly differs from source-bound candidate reconstruction"})
        if canonical(select_candidate_graph(expected)) != canonical(values["graph.json"]):
            errors.append({"artifact": "graph.json", "detail": "Graph differs from deterministic candidate reconstruction"})
    except (ValueError, KeyError, TypeError, OSError) as error:
        errors.append({"artifact": "candidate-input.json", "detail": str(error)})
    anchor_report = None
    if args.anchors:
        raw = args.anchors.read_bytes()
        hashes[str(args.anchors.resolve())] = digest(raw)
        anchor_report = audit_anchor_candidates(paper, json.loads(raw), sources)
    report = {"kind": "CandidateArtifactAudit", "created_at": utcnow(), "run": str(args.run.resolve()),
              "scope": "SCHEMA_QUERY_REFERENCES_FROZEN_SOURCE_EXACT_ANCHOR_LOCATIONS_AND_GRAPH_RECONSTRUCTION",
              "status": "PASS" if not errors and (anchor_report is None or anchor_report["location_status"] == "PASS") else "FAILED",
              "schema_errors": errors, "artifact_hashes": hashes, "anchor_audit": anchor_report,
              "semantic_status": "AWAITING_REVIEW", "mathematical_status": "CHAIN_INCOMPLETE"}
    write_json(args.output, report)
    print(json.dumps({key: report[key] for key in ("status", "semantic_status", "mathematical_status")}))
    raise SystemExit(0 if report["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
