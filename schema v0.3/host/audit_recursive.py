"""Audit one recorded recursive join and its exact quotations, not truth."""
from __future__ import annotations

import argparse
import json
import pathlib

from core import canonical, digest, utcnow, write_json
from model import _frozen_source_payload, bind_source_locators
from recursive_graph import _verified_json, join_candidate_paper


def main():
    from jsonschema import Draft202012Validator
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=pathlib.Path)
    parser.add_argument("--proof-issues", type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Retain previous audit evidence; choose a new output")
    run = args.run.resolve()
    plan = json.loads((run / "plan.json").read_bytes())
    refs = plan["environment"]["input_references"]
    inputs = {name: _verified_json(reference) for name, reference in refs.items()}
    source_directory = pathlib.Path(refs["upstream_extraction"]["path"]).parent
    paper = inputs["upstream_extraction"]
    sources = _frozen_source_payload(paper, source_directory, source_directory=source_directory)
    expected = join_candidate_paper(inputs["base"], inputs["upstream"], inputs["matches"], sources,
                                    matches_reference=refs["matches"])
    recorded = {name: json.loads((run / (name + ".json")).read_bytes()) for name in ("assembly", "graph", "ledger")}
    issues = []
    for name in ("assembly", "graph"):
        if canonical(expected[name]) != canonical(recorded[name]):
            issues.append({"code": "RECURSIVE_RECONSTRUCTION_MISMATCH", "artifact": name})
    schema = json.loads((pathlib.Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
    def validate(value, kind, subject):
        validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + kind})
        issues.extend({"code": "SCHEMA_MISMATCH", "subject": subject, "detail": error.message,
                       "path": list(error.absolute_path)} for error in validator.iter_errors(value))
    validate(plan, "Plan", "plan")
    validate(recorded["ledger"], "PlanLedger", "ledger")
    for group in recorded["graph"]["support_groups"]:
        validate(group, "SupportGroup", group["id"])
    if set(plan["query_ids"]) != set(recorded["graph"]["query_ids"]):
        issues.append({"code": "QUERY_SCOPE_CHANGED"})
    evidence_sets = [("source_matches", inputs["matches"]["matches"])]
    proof_reference = None
    if args.proof_issues:
        raw = args.proof_issues.read_bytes()
        proof_reference = {"path": str(args.proof_issues.resolve()), "sha256": digest(raw), "byte_size": len(raw)}
        evidence_sets.append(("proof_issue_candidates", json.loads(raw)["issues"]))
    quotation_reports = []
    known_occurrences = {row["id"] for row in paper["claims"]}
    for kind, rows in evidence_sets:
        for index, row in enumerate(rows):
            quotes = row.get("source_quotes")
            if not isinstance(quotes, list) or not quotes:
                issues.append({"code": "QUOTATION_EVIDENCE_ABSENT", "kind": kind, "row": index})
                continue
            used = row.get("upstream_occurrence_ids", row.get("source_occurrence_ids", []))
            if set(used) - known_occurrences:
                issues.append({"code": "UNKNOWN_SOURCE_OCCURRENCE", "kind": kind, "row": index})
            bound = bind_source_locators({"claims": [{"source_locators": quotes}]}, sources)
            issues.extend({**problem, "kind": kind, "row": index} for problem in bound["issues"])
            quotation_reports.append({"kind": kind, "row": index, "exact_quotations": bound["bindings"],
                                      "semantic_status": "AWAITING_REVIEW"})
    report = {"kind": "RecursiveCandidateArtifactAudit", "created_at": utcnow(), "run": str(run),
              "scope": "SCHEMA_FROZEN_SOURCES_QUOTATION_LOCATIONS_AND_DETERMINISTIC_JOIN_RECONSTRUCTION",
              "status": "PASS" if not issues else "FAILED", "issues": issues,
              "input_references": refs, "proof_issues_reference": proof_reference,
              "quotation_reports": quotation_reports, "accepted_support_edges": 0,
              "source_defects_proved": False, "mathematical_status": "CHAIN_INCOMPLETE"}
    write_json(args.output, report)
    print(json.dumps({"status": report["status"], "issues": len(issues), "quotation_rows": len(quotation_reports),
                      "mathematical_status": report["mathematical_status"]}))
    raise SystemExit(0 if not issues else 2)


if __name__ == "__main__":
    main()
