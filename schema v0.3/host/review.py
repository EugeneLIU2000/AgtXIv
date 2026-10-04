"""Human review records: the only human input, each bound to a digest of what was reviewed.

The host writes templates with decision null and the reviewed content shown; only a
human fills decisions. A review whose subject is unknown or whose content changed is
rejected, never applied. Before a walk only support groups exist to review; alignment
and failure subjects are attempts in a run's ledger and count toward its certificate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from chunks import reference
from core import canonical, digest, write_json

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
VALIDATOR = Draft202012Validator({"$defs": SCHEMA["$defs"], "$ref": "#/$defs/HumanReview"})


def subjects(graph, ledger=None):
    """(subject_kind, subject_id) -> the reviewed content; attempt subjects need the run's ledger snapshot."""
    rows = {("SUPPORT_GROUP", group["id"]): group for group in graph["support_groups"]}
    nodes = {node["id"]: node for node in graph["nodes"]}
    for row in (ledger or {}).get("proof_attempts", []):
        result, node = row.get("result"), nodes.get(row["node_id"])
        if not isinstance(result, dict) or node is None:
            continue
        attempt = {"node_id": node["id"], "attempt_number": row["attempt_number"], "result_sha256": digest(canonical(result))}
        if row["kind"] == "PROOF" and "failure_kind" in result:  # The recorded failure (model- or host-assigned); Lean refs if Lean ran.
            receipt = result.get("program_receipt") or {}
            rows["FAILURE_CLASSIFICATION", row["id"]] = {**attempt, "failure_kind": result["failure_kind"],
                "failure_reason": result.get("failure_reason"), "lean_source": result.get("lean_source"),
                "lean_log": {"path": receipt["log"], "sha256": receipt.get("output_sha256")} if "log" in receipt else None}
        # Alignment compares the source text with the Lean statement of this very attempt.
        if row["kind"] == "PREMISE":
            rows["PREMISE_ALIGNMENT", row["id"]] = {**attempt, "source_text": node.get("text"),
                                                    "lean_statement": result.get("lean_prop")}
        elif result.get("kernel_checked") is True:
            rows["STATEMENT_ALIGNMENT", row["id"]] = {**attempt, "source_text": node.get("text"),
                "lean_statement": (result.get("audit_record") or {}).get("type")}
    return rows


def template(graph, ledger=None):
    return [{"kind": "HumanReview", "subject_kind": kind, "subject_id": subject_id,
             "subject_sha256": digest(canonical(content)), "content": content,
             "decision": None, "reviewer": None, "basis": None, "reviewed_at": None}
            for (kind, subject_id), content in sorted(subjects(graph, ledger).items())]


def load_reviews(path, graph, ledger=None):
    """Every accepted (kind, id), and the support groups bottom_up_walk may trust; a REJECT withdraws a subject."""
    known = {key: digest(canonical(content)) for key, content in subjects(graph, ledger).items()}
    valid, rejections = [], []
    for review in json.loads(Path(path).read_bytes()):
        if isinstance(review, dict) and review.get("decision") is None:
            continue  # An unfilled template row is not a review.
        errors = [error.message for error in VALIDATOR.iter_errors(review)]
        if errors:
            reason = "SCHEMA_INVALID: " + "; ".join(errors)
        else:
            expected = known.get((review["subject_kind"], review["subject_id"]))
            reason = ("UNKNOWN_SUBJECT" if expected is None else
                      "SUBJECT_CHANGED_SINCE_REVIEW" if expected != review["subject_sha256"] else None)
        if reason:
            rejections.append({"review": review, "reason": reason})
        else:
            valid.append(review)
    decided = lambda decision: {(r["subject_kind"], r["subject_id"]) for r in valid if r["decision"] == decision}
    accepted = sorted(decided("ACCEPT") - decided("REJECT"))
    return {"trusted_human_support_groups": [subject_id for kind, subject_id in accepted if kind == "SUPPORT_GROUP"],
            "accepted": accepted, "rejections": rejections, "source": reference(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("template", help="List reviewable subjects with fingerprints and decision null")
    make.add_argument("--graph", type=Path, required=True)
    make.add_argument("--ledger", type=Path, help="A proof-walk ledger.json, to list its alignments and failures")
    make.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Keep prior review files; choose a fresh output")
    ledger = json.loads(args.ledger.read_bytes()) if args.ledger else None
    rows = template(json.loads(args.graph.read_bytes()), ledger)
    write_json(args.output, rows)
    print(json.dumps({"subjects": len(rows), "output": str(args.output.resolve())}))


if __name__ == "__main__":
    main()
