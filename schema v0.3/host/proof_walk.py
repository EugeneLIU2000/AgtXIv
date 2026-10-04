"""Run the pruned graph through the actual model/Lean worker in a fresh plan."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import uuid

from jsonschema import Draft202012Validator

from certify import certificate
from chunks import reference
from core import PlanLedger, VERSION, canonical, digest, utcnow, write_json
from proof_backend import ModelProofBackend
from recursive_graph import _verified_graph_json, _verified_json
from review import SCHEMA, load_reviews
from scheduler import bottom_up_walk
from model_routing import freeze_model_routing
from pdf_proof_context import pdf_source_binding

ROOT_AUDIT = Draft202012Validator({"$defs": SCHEMA["$defs"], "$ref": "#/$defs/RootAudit"})


def run_walk(request_path, output, *, max_model_calls, max_proof_attempts, max_node_attempts,
             max_call_seconds, candidate_exploration=False, reviews=None):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Keep proof runs immutable; choose a fresh output directory")
    request = json.loads(Path(request_path).read_bytes())
    graph = _verified_graph_json(request["graph"])
    if any("root_audit" in node for node in graph["nodes"]):  # Only the two request fields below annotate roots.
        raise ValueError("The input graph may not carry root audits")
    environment = _verified_json(request["environment"])
    library_rows = _verified_json(environment["library_records"])
    libraries = {row["declaration"]: row for row in library_rows}
    roots = {row["id"] for row in graph["roots"]}
    bindings = request.get("candidate_root_bindings", {})
    if set(bindings) - roots:
        raise ValueError("Root library bindings may only annotate actual graph roots")
    # Optional library.py root-search audits for roots without a binding; the walk still gates each one.
    searched = _verified_json(request["root_audits"]) if "root_audits" in request else None
    if searched and (searched.get("environment_sha256"), (searched.get("graph") or {}).get("sha256")) != (
            environment["environment_sha256"], request["graph"]["sha256"]):
        raise ValueError("Root audits belong to another graph or proof environment")
    audits = searched["root_audits"] if searched else {}
    if set(audits) - (roots - set(bindings)):
        raise ValueError("Root audits may only annotate actual graph roots without a library binding")
    # Only library.root_audits' LIBRARY_SEARCHED shape; LIBRARY_BOUND comes from candidate_root_bindings alone.
    invalid = sorted(node for node, audit in audits.items() if not ROOT_AUDIT.is_valid(audit))
    if invalid:
        raise ValueError("Root audits must match $defs.RootAudit (LIBRARY_SEARCHED): " + ", ".join(invalid))
    for node in graph["nodes"]:
        name = bindings.get(node["id"])
        if name is not None:
            row = libraries.get(name)
            if row is None or not row["kernel_checked"]:
                raise ValueError("Root binding requires a freshly audited concrete declaration")
            node["root_audit"] = {"status": "LIBRARY_BOUND",
                "program_receipt": _verified_json(environment["library_receipt"]),
                "library_binding": {"library": "PINNED_COMMON_MATHLIB_PHYSLIB_AND_LOCAL_CASE_MODULES",
                    "revision": environment["environment_sha256"], "declaration": name},
                "alignment": "CANDIDATE_SOURCE_BINDING_UNREVIEWED", "source_alignment_accepted": False}
            tag, blocker = "unreviewed-root-binding:", "CANDIDATE_ROOT_BINDING_REVIEW_REQUIRED"
        elif node["id"] in audits:
            node["root_audit"] = audits[node["id"]]
            tag, blocker = "unreviewed-root-search:", "CANDIDATE_ROOT_SEARCH_REVIEW_REQUIRED"
        else:
            continue
        # This explicit mapping is a candidate judgement, not a calibrated result.
        node["unreviewed_blockers"] = sorted(set(node.get("unreviewed_blockers", [])) | {tag + node["id"]})
        if not candidate_exploration:
            node["blocked_by"] = sorted(set(node.get("blocked_by", [])) | {blocker})
    trusted = load_reviews(reviews, graph) if reviews is not None else {}
    if min(max_model_calls, max_proof_attempts, max_node_attempts, max_call_seconds) < 1:
        raise ValueError("All proof plan limits must be positive")
    source_papers = request["paper_sources"]
    for paper_id, entry in source_papers.items():
        if "pdf_run" in entry:
            pdf_source_binding(paper_id, entry)
        else:
            _verified_json(entry["extraction"])
    source_request = reference(Path(request_path).resolve())
    output.mkdir(parents=True)
    runtime = []
    for path in sorted(Path(__file__).parent.glob("*.py")):
        snapshot = output / "runtime" / path.name
        snapshot.parent.mkdir(exist_ok=True)
        snapshot.write_bytes(path.read_bytes())
        runtime.append({"repository_path": str(path), "snapshot": reference(snapshot)})
    plan = {"contract_version": VERSION, "plan_id": "plan:" + uuid.uuid4().hex,
        "paper_id": request["paper_id"], "query_ids": graph["query_ids"], "created_at": utcnow(),
        "cost_mode": "ACCOUNT_QUOTA", "source_sha256": request["source_sha256"],
        "decision_policy": "CANDIDATE_EXPLORATION" if candidate_exploration else "STRICT_CALIBRATED",
        "limits": {"max_model_calls": max_model_calls, "max_proof_attempts": max_proof_attempts,
            "max_node_attempts": max_node_attempts, "max_call_seconds": max_call_seconds,
            "max_papers": len(source_papers), "max_cost_microusd": 0, "no_progress_limit": 1},
        "environment": {"mode": "ACTUAL_MODEL_LEAN_PROOF_WALK", "model_routing": freeze_model_routing(),
            "lean_environment_sha256": environment["environment_sha256"],
            "proof_environment": request["environment"], "request": source_request,
            "runtime_sources": runtime}}
    write_json(output / "plan.json", plan)
    write_json(output / "request-snapshot.json", request)
    write_json(output / "candidate-root-audited-graph.json", graph)
    ledger = PlanLedger(output, plan)
    backend = ModelProofBackend(ledger, request["environment"], source_papers, output / "attempts",
                                library_index=(searched or {}).get("index"))
    result = bottom_up_walk(graph, backend.attempt, backend.render_premise, ledger=ledger,
                           selected_group_ids=request.get("selected_group_ids"),
                           trusted_human_support_groups=trusted.get("trusted_human_support_groups", ()))
    result["integration_status"] = "CONNECTED_TO_ACTUAL_MODEL_AND_ISOLATED_LEAN_WORKER"
    result["request"] = source_request
    result["graph_derivation"] = "ORIGINAL_PRUNED_GRAPH_WITH_CANDIDATE_ROOT_LIBRARY_ANNOTATIONS_ONLY"
    result["source_alignment_accepted"] = False
    if trusted:
        result["human_reviews"] = {"source": trusted["source"], "rejections": trusted["rejections"]}
    write_json(output / "proof-walk-result.json", result)
    write_json(output / "ledger.json", ledger.snapshot())
    chain = certificate(graph, result, plan_id=plan["plan_id"], environment_sha256=environment["environment_sha256"])
    write_json(output / "chain-certificate.json", chain)
    summary = {"kind": "ActualProofWalkResult", "chain_state": chain["state"],
        "query_count": len(graph["query_ids"]), "kernel_candidate_count": len(result["completed_candidates"]),
        "explicit_premise_count": len(result["premise_candidates"]), "outcome_count": len(result["outcomes"]),
        "model_call_count": len(ledger.snapshot()["calls"]), "source_alignment_accepted": False,
        "promotion_allowed": False, "result": reference(output / "proof-walk-result.json"),
        "audited_graph": reference(output / "candidate-root-audited-graph.json"), "ledger": reference(output / "ledger.json"),
        "chain_certificate": reference(output / "chain-certificate.json")}
    write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-model-calls", type=int, default=4)
    parser.add_argument("--max-proof-attempts", type=int, default=2)
    parser.add_argument("--max-node-attempts", type=int, default=1)
    parser.add_argument("--max-call-seconds", type=int, default=180)
    parser.add_argument("--candidate-exploration", action="store_true")
    parser.add_argument("--reviews", type=Path, help="Filled review.py template; before a walk only SUPPORT_GROUP reviews apply")
    args = parser.parse_args()
    print(json.dumps(run_walk(args.request, args.output, max_model_calls=args.max_model_calls,
        max_proof_attempts=args.max_proof_attempts, max_node_attempts=args.max_node_attempts,
        max_call_seconds=args.max_call_seconds, candidate_exploration=args.candidate_exploration,
        reviews=args.reviews)))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
