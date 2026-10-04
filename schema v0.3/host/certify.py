"""Read a ChainCertificate off a recorded proof walk and human reviews; nothing here is 'verified'.

Emission needs a kernel attestation for every query and, for a theorem, a triviality
probe that did not close its statement (no probe, no emission). Premises are read from
the walk's Lean evidence, never from graph prose. --run re-certifies only a run whose
proof-walk audit passes. human_accepted additionally needs an ACCEPT review covering
every open review blocker and aligning the very Lean attempt of every query and every
explicit premise the queries are conditional on.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from chunks import reference
from core import VERSION, canonical, digest, write_json
from graph import _THEOREM_KINDS
from recursive_graph import _verified_graph_json, _verified_json
from review import load_reviews

ATTESTED = {"KERNEL_CHECKED_CANDIDATE", "KERNEL_CHECKED_VACUITY_UNKNOWN", "DEFINITION_ELABORATED"}
# Blocker prefix -> the subject kind whose ACCEPT closes it; node-named blockers close with that node's alignment.
COVERING = {"unreviewed-support-group": "SUPPORT_GROUP", "unreviewed-premise-alignment": "PREMISE_ALIGNMENT",
            "unreviewed-failure-classification": "FAILURE_CLASSIFICATION"}
NODE_BLOCKERS = {"unreviewed-root-binding", "unreviewed-root-search", "candidate-exploration"}


def certificate(graph, walk_result, *, plan_id, environment_sha256, reviews=None):
    queries, completed, premises = graph["query_ids"], walk_result["completed_candidates"], walk_result["premise_candidates"]
    outcomes = {row["node_id"]: row for row in walk_result["outcomes"]}
    accepted = set((reviews or {}).get("accepted", ()))
    alignment = {**{node: ("STATEMENT_ALIGNMENT", record["reservation_id"]) for node, record in completed.items()},
                 **{node: ("PREMISE_ALIGNMENT", record["reservation_id"]) for node, record in premises.items()}}
    aligned = lambda node: alignment.get(node) in accepted

    def covered(blocker):
        kind, _, subject = blocker.partition(":")
        return aligned(subject) if kind in NODE_BLOCKERS else (COVERING.get(kind), subject) in accepted

    attested = {node for node, record in completed.items() if record.get("kernel_attestation_state") in ATTESTED}
    definitions = [node["id"] for node in graph["nodes"] if node["kind"].lower() == "definition"]

    def unmet(query):
        if query in attested:  # No probe, no emission; only theorems (by the graph's kind) are probed.
            flag = completed[query]["evidence"].get("statement_trivially_provable", False if query in definitions else "UNPROBED")
            return None if flag is False else ("QUERY_STATEMENT_TRIVIALLY_PROVABLE " if flag is True else
                                               "QUERY_STATEMENT_TRIVIALITY_UNPROBED " if flag == "UNPROBED" else
                                               "QUERY_STATEMENT_TRIVIALITY_UNKNOWN ") + query
        outcome = outcomes.get(query, {})
        return ("QUERY_NOT_KERNEL_ATTESTED " + query + ": " + outcome.get("state", "NOT_WALKED") + "/" +
                str(outcome.get("reason") or ",".join(outcome.get("blocked_by", []))))

    missing = [item for item in map(unmet, queries) if item]
    ready = [(query, completed[query]) for query in queries if not unmet(query)]
    explicit = sorted({node for _, record in ready for node in record["conditional_on"]})
    open_reviews = sorted({b for _, record in ready for b in record["unreviewed_blockers"] if not covered(b)})
    unaligned = [kind + "_REVIEW_REQUIRED " + node for kind, nodes in (("STATEMENT_ALIGNMENT", [q for q, _ in ready]),
                 ("PREMISE_ALIGNMENT", explicit)) for node in nodes if not aligned(node)]
    missing += (["UNREVIEWED_BLOCKER " + b for b in open_reviews] + unaligned +
                ["VACUITY_UNKNOWN " + node for node in sorted({n for _, r in ready for n in r["vacuity_unknown_nodes"]})])
    emitted = len(ready) == len(queries)
    lean = [{"kind": "LEAN_HYPOTHESIS", "query_id": query, "hypothesis": hypothesis}
            for query, record in ready for hypothesis in record["environment_hypotheses"]]
    lean += [{"kind": "EXPLICIT_PROP_PREMISE", "node_id": node, "declaration": premises[node]["explicit_premise"]["declaration"],
              "lean_prop": premises[node]["explicit_premise"]["lean_prop"]} for node in explicit]
    labels = dict.fromkeys([h["type"] for _, record in ready for h in record["environment_hypotheses"]] +
                           [premises[node]["explicit_premise"]["lean_prop"] for node in explicit])
    scope = "GRAPH_SCOPE:" + digest(canonical(graph["scope"]))
    theorems = [node["id"] for node in graph["nodes"] if node["kind"].lower() in _THEOREM_KINDS]
    coverage = [{"scope": scope + ":" + label, "metric": "KERNEL_ATTESTED_CANDIDATE_NOT_SOURCE_ALIGNED",
                 "eligible": len(members), "kernel_attested": len(attested.intersection(members))}
                for label, members in (("THEOREM_LIKE", theorems), ("DEFINITION", definitions))]
    result = {"kind": "ChainCertificate", "contract_version": VERSION, "plan_id": plan_id,
        "state": "CHAIN_CERTIFICATE_EMITTED" if emitted else "CHAIN_INCOMPLETE", "query_ids": queries,
        "query_declarations": list(dict.fromkeys(b["declaration"] for _, r in ready for b in r["evidence"]["declaration_bindings"]))
                              if emitted else [],
        "environment_sha256": environment_sha256,
        "premise_extraction_status": "LEAN_ENVIRONMENT_EXTRACTED" if emitted else "QUERY_DECLARATION_ABSENT",
        "premises_from_lean_environment": lean if emitted else [],
        "terminal_kind_counts": {"scope": scope + ":GRAPH_ROOTS_NOT_LEAN_PREMISES", "counts": dict(Counter(
            root.get("terminal_kind") or "NO_TERMINAL_KIND" for root in graph["roots"]))},
        "coverage": coverage, "stage_coverage": [], "missing_obligations": missing,
        "source_completeness_asserted": False,
        "human_accepted": emitted and not open_reviews and not unaligned,
        "headline": (", ".join(queries) + " holds CONDITIONAL ON {" + ", ".join(labels) + "}" if emitted else
                     "CHAIN_INCOMPLETE: " + str(len(queries) - len(ready)) + " of " + str(len(queries)) +
                     " queries lack an admissible kernel-attested candidate.")}
    # Pre-walk support-group reviews shaped the walk itself; the walk result names their file.
    sources = [ref for ref in ((walk_result.get("human_reviews") or {}).get("source"), (reviews or {}).get("source")) if ref]
    if sources:
        result["human_reviews"] = list({ref["sha256"]: ref for ref in sources}.values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="A proof_walk.py output directory")
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit_path = args.output.with_suffix(".run-audit.json")  # The certificate schema has no audit field.
    if args.output.exists() or audit_path.exists():
        parser.error("Keep prior certificates; choose a fresh output")
    import audit_proof_walk  # Imported here: it imports certify.
    report = audit_proof_walk.audit(args.run)  # An unreadable run is a FAILED audit, never a certificate.
    with audit_path.open("xb") as stream:
        stream.write(canonical(report))
    if report["status"] != "PASS":
        raise SystemExit("Refusing to certify: the run's proof-walk audit is " + report["status"] + "; see " + str(audit_path))
    summary = json.loads((args.run / "summary.json").read_bytes())

    def pinned(name, key, check=_verified_json):
        """Read a run file through the pin its summary records; older runs pin only the result."""
        path = args.run / name
        return check({**summary[key], "path": str(path)}) if key in summary else json.loads(path.read_bytes())

    graph, ledger = pinned("candidate-root-audited-graph.json", "audited_graph", _verified_graph_json), pinned("ledger.json", "ledger")
    result = pinned("proof-walk-result.json", "result")
    if "human_reviews" in result:
        _verified_json(result["human_reviews"]["source"])  # The pre-walk review file must be unchanged.
    reviews = load_reviews(args.reviews, graph, ledger) if args.reviews else None
    value = certificate(graph, result, plan_id=ledger["plan"]["plan_id"],
                        environment_sha256=ledger["plan"]["environment"]["lean_environment_sha256"], reviews=reviews)
    write_json(args.output, value)
    print(json.dumps({"state": value["state"], "human_accepted": value["human_accepted"],
                      "run_audit": {"status": report["status"], **reference(audit_path)}}))


if __name__ == "__main__":
    main()
