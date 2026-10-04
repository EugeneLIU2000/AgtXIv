"""Human review records, chain certificates and their proof_walk wiring (stub backend; no model, no Lean)."""
from collections import Counter
import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

import audit_proof_walk
import certify
from certify import certificate
from chunks import reference
from core import write_json
import proof_walk
import review
from review import load_reviews, template
from scheduler import _statement_fingerprint

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
SHA = "sha256:" + "0" * 64
LEAN = {"kind": "ProgramReceipt", "contract_version": "0.3.0", "program": "stub", "engine_class": "HOST", "call": None,
        "status": "SUCCEEDED", "outcome": "RECORDED", "input_sha256": SHA, "output_sha256": SHA, "exit_code": 0,
        "operation": "lean.check", "started_at": "t0", "finished_at": "t1", "elapsed_seconds": 0}
A, B, Q = "claim:a", "claim:b", "claim:q"
ENV = "sha256:" + "1" * 64


def graph():
    span = [{"artifact": "paper.tex", "start_byte": 0, "end_byte": 4}]
    return {"nodes": [{"id": node, "kind": "theorem", "text": "Statement " + node, "source_spans": span,
                       "paper_id": "paper:x", "blocked_by": []} for node in (A, B, Q)],
            "support_groups": [{"id": "group:b", "target": B, "members": [A], "relation": "PROOF_DEPENDENCY"},
                               {"id": "group:q", "target": Q, "members": [B], "relation": "PROOF_DEPENDENCY"}],
            "roots": [{"id": A, "terminal_kind": None}], "query_ids": [Q], "condensation_order": [A, B, Q],
            "sccs": [], "scope": {"kind": "PRUNED_SUPPORT_GRAPH", "node_set_sha256": "x"}}


class StubBackend:
    """A premise for the root A, kernel-checked candidates composed above it."""
    probe = {}  # node id -> triviality fields; by default probed and not trivial

    def __init__(self, ledger, environment, sources, output, *, library_index=None):
        StubBackend.library_index = library_index

    def attempt(self, node, number, prerequisites, reservation):
        if node["id"] == A:
            return {"failure_kind": "UNPROVABLE_AS_STATED", "failure_reason": "stub: A is taken as a premise",
                    "program_receipt": {**LEAN, "status": "FAILED", "log": "/stub/lean.log"}}
        witnesses = [{"upstream_node_id": key, "downstream_node_id": node["id"], "status": "COMPOSED",
                      "basis": "LEAN_USED_PROP_BINDER", "used_prop_binders": [{"binder": "h"}]}
                     if value["dependency_kind"] == "EXPLICIT_PROP_PREMISE" else
                     {"upstream_node_id": key, "downstream_node_id": node["id"], "status": "COMPOSED",
                      "basis": "LEAN_ELABORATED_TERM_CONSTANT"} for key, value in prerequisites.items()]
        return {"kernel_checked": True, "program_receipt": LEAN, "source_node_id": node["id"],
                "source_statement_sha256": _statement_fingerprint(node), "lamport": "1. qed", "lean_source": "theorem",
                "declaration_bindings": [{"declaration": "Gen." + node["id"][6:]}], "declaration_kind": "THEOREM",
                "nonvacuity_witness": {"term": "w", "program_receipt": LEAN}, "forbidden_axioms": [],
                "hypotheses": [{"name": "h", "type": "P_a"}], "composition_witnesses": witnesses,
                **self.probe.get(node["id"], {"statement_trivially_provable": False})}

    def render_premise(self, node, result, reservation):
        return {"source_node_id": node["id"], "source_statement_sha256": _statement_fingerprint(node),
                "lean_prop": "P_a", "declaration": "Gen.PA", "elaborated_type": "Prop", "forbidden_axioms": [],
                "program_receipt": LEAN}


def request(tmp_path, *, root_audit="LIBRARY_SEARCHED", audit_graph=None, base=None):
    def ref(name, value):
        write_json(tmp_path / name, value)
        return reference(tmp_path / name)
    value = {"graph": ref("graph.json", base or graph()), "paper_id": "paper:x", "source_sha256": SHA,
             "environment": ref("environment.json", {"environment_sha256": ENV,
                 "library_records": ref("library.json", []), "library_receipt": ref("receipt.json", LEAN)}),
             "paper_sources": {"paper:x": {"extraction": ref("extraction.json", {})}}}
    if root_audit:  # The shape library.root_audits writes.
        index = ref("library-index.json", {"kind": "LibraryIndex", "environment_sha256": ENV})
        value["root_audits"] = ref("root-audits.json", {"kind": "RootLibraryAudits", "environment_sha256": ENV,
            "graph": ref("audit-graph.json", audit_graph) if audit_graph else value["graph"], "index": index,
            "root_audits": {A: {"status": root_audit, "searched_revisions": [ENV], "candidates": ["Nat.le_refl"],
                                "method": "LEXICAL_IDF_TOKEN_OVERLAP_V1", "index": index, "program_receipt": LEAN,
                                "binding_accepted": False}}})
    return ref("request.json", value)["path"]


def walk(tmp_path, monkeypatch, name, *, reviews=None, probe={}, **kw):
    monkeypatch.setattr(proof_walk, "ModelProofBackend", StubBackend)
    monkeypatch.setattr(StubBackend, "probe", probe)
    out = tmp_path / name
    summary = proof_walk.run_walk(request(tmp_path, **kw), out, max_model_calls=1, max_proof_attempts=10,
        max_node_attempts=1, max_call_seconds=1, candidate_exploration=True, reviews=reviews)
    return summary, lambda file: json.loads((out / file).read_bytes())


def recertify(monkeypatch, run, output, reviews=None, audit_status="PASS"):
    if audit_status:  # A stub run cannot pass the real proof-walk audit.
        monkeypatch.setattr(audit_proof_walk, "audit", lambda run: {"status": audit_status})
    monkeypatch.setattr(sys, "argv", ["certify.py", "--run", str(run), "--output", str(output)] +
                        (["--reviews", str(reviews)] if reviews else []))
    certify.main()
    return json.loads(output.read_bytes())


def fill(rows, decision="ACCEPT"):
    return [{**row, "decision": decision, "reviewer": "a human", "basis": "Read the source and the Lean.",
             "reviewed_at": "2026-09-23T00:00:00+00:00"} for row in rows]


def errors(value):
    validator = Draft202012Validator({"$defs": SCHEMA["$defs"], "$ref": "#/$defs/ChainCertificate"})
    return [error.message for error in validator.iter_errors(value)]


def test_template_fill_and_load(tmp_path, monkeypatch):
    write_json(tmp_path / "graph.json", graph())
    monkeypatch.setattr(sys, "argv", ["review.py", "template", "--graph", str(tmp_path / "graph.json"),
                                      "--output", str(tmp_path / "template.json")])
    review.main()
    rows = json.loads((tmp_path / "template.json").read_bytes())  # before a walk only support groups exist
    assert [row["subject_kind"] for row in rows] == ["SUPPORT_GROUP"] * 2 and all(row["decision"] is None for row in rows)
    assert load_reviews(tmp_path / "template.json", graph())["accepted"] == []  # unfilled rows are not reviews

    _, read = walk(tmp_path, monkeypatch, "run")
    audited, ledger = read("candidate-root-audited-graph.json"), read("ledger.json")
    rows = template(audited, ledger)
    assert Counter(row["subject_kind"] for row in rows) == {"SUPPORT_GROUP": 2, "STATEMENT_ALIGNMENT": 2,
                                                            "PREMISE_ALIGNMENT": 1, "FAILURE_CLASSIFICATION": 1}
    failure = next(row["content"] for row in rows if row["subject_kind"] == "FAILURE_CLASSIFICATION")
    assert (failure["failure_kind"], failure["failure_reason"], failure["lean_log"]) == (
        "UNPROVABLE_AS_STATED", "stub: A is taken as a premise", {"path": "/stub/lean.log", "sha256": SHA})
    write_json(tmp_path / "reviews.json", fill(rows[:-1]) + [{**fill(rows[-1:])[0], "basis": "  "}])
    loaded = load_reviews(tmp_path / "reviews.json", audited, ledger)
    assert len(loaded["accepted"]) == 5 and loaded["rejections"][0]["reason"].startswith("SCHEMA_INVALID")
    assert loaded["trusted_human_support_groups"] == ["group:b"]
    unbound = load_reviews(tmp_path / "reviews.json", audited)["rejections"]  # attempts need their run's ledger
    assert Counter(r["reason"].split(":")[0] for r in unbound) == {"UNKNOWN_SUBJECT": 4, "SCHEMA_INVALID": 1}


def test_changed_content_and_reject_are_not_trusted(tmp_path, monkeypatch):
    _, read = walk(tmp_path, monkeypatch, "run")
    audited, ledger = read("candidate-root-audited-graph.json"), read("ledger.json")
    rows = fill(template(audited, ledger))
    write_json(tmp_path / "reviews.json", rows + [{**rows[-1], "decision": "REJECT"}])  # group:q is also rejected
    changed, relogged = copy.deepcopy(audited), copy.deepcopy(ledger)
    changed["support_groups"][0]["members"] = [A, Q]
    next(row for row in relogged["proof_attempts"] if row["kind"] == "PREMISE")["result"]["lean_prop"] = "True"
    loaded = load_reviews(tmp_path / "reviews.json", changed, relogged)
    assert {(r["review"]["subject_kind"], r["reason"]) for r in loaded["rejections"]} == {
        ("SUPPORT_GROUP", "SUBJECT_CHANGED_SINCE_REVIEW"), ("PREMISE_ALIGNMENT", "SUBJECT_CHANGED_SINCE_REVIEW")}
    assert loaded["trusted_human_support_groups"] == []
    assert {kind for kind, _ in loaded["accepted"]} == {"STATEMENT_ALIGNMENT", "FAILURE_CLASSIFICATION"}


def test_walk_applies_root_audit_and_reviews_then_certifies(tmp_path, monkeypatch):
    summary, read = walk(tmp_path, monkeypatch, "plain")
    result, cert = read("proof-walk-result.json"), read("chain-certificate.json")
    audit = read("candidate-root-audited-graph.json")["nodes"][0]["root_audit"]
    assert audit["status"] == "LIBRARY_SEARCHED" and StubBackend.library_index == audit["index"]
    assert "unreviewed-root-search:" + A in result["premise_candidates"][A]["unreviewed_blockers"]
    assert summary["chain_state"] == cert["state"] == "CHAIN_CERTIFICATE_EMITTED" and not errors(cert)
    assert cert["headline"] == Q + " holds CONDITIONAL ON {P_a}" and cert["query_declarations"] == ["Gen.q"]
    assert {row["kind"] for row in cert["premises_from_lean_environment"]} == {"LEAN_HYPOTHESIS", "EXPLICIT_PROP_PREMISE"}
    assert cert["human_accepted"] is False and "human_reviews" not in cert
    assert {"VACUITY_UNKNOWN " + A, "STATEMENT_ALIGNMENT_REVIEW_REQUIRED " + Q, "PREMISE_ALIGNMENT_REVIEW_REQUIRED " + A,
            "UNREVIEWED_BLOCKER unreviewed-support-group:group:q"} <= set(cert["missing_obligations"])

    write_json(tmp_path / "prewalk.json", fill(template(graph())))
    _, read = walk(tmp_path, monkeypatch, "reviewed", reviews=tmp_path / "prewalk.json")
    result = read("proof-walk-result.json")
    blockers = result["completed_candidates"][Q]["unreviewed_blockers"]
    assert not any(b.startswith("unreviewed-support-group") for b in blockers) and result["human_reviews"]["rejections"] == []
    assert any(b.startswith("unreviewed-premise-alignment") for b in blockers)

    # Post hoc: this run's alignments and failure, reviewed against its ledger, then re-certified.
    run = tmp_path / "reviewed"
    write_json(tmp_path / "posthoc.json", fill(template(read("candidate-root-audited-graph.json"), read("ledger.json"))))
    accepted = recertify(monkeypatch, run, tmp_path / "accepted.json", tmp_path / "posthoc.json")
    assert accepted["human_accepted"] is True and not errors(accepted)
    assert [ref["path"] for ref in accepted["human_reviews"]] == [str((tmp_path / name).resolve())
                                                              for name in ("prewalk.json", "posthoc.json")]
    assert accepted["missing_obligations"] == ["VACUITY_UNKNOWN " + A]
    assert json.loads((tmp_path / "accepted.run-audit.json").read_bytes()) == {"status": "PASS"}

    write_json(run / "proof-walk-result.json", {**result, "outcomes": []})  # no longer the bytes summary.json pins
    with pytest.raises(ValueError, match="differ"):
        recertify(monkeypatch, run, tmp_path / "forged.json", tmp_path / "posthoc.json")


def test_incomplete_and_trivially_provable_block_emission(tmp_path, monkeypatch):
    summary, read = walk(tmp_path, monkeypatch, "old", root_audit=None)  # an old request shape
    result, cert = read("proof-walk-result.json"), read("chain-certificate.json")
    assert "human_reviews" not in result and summary["chain_state"] == cert["state"] == "CHAIN_INCOMPLETE"
    assert cert["missing_obligations"] == ["QUERY_NOT_KERNEL_ATTESTED " + Q + ": CONDITIONAL_ON_BLOCKED_ROOT/PREREQUISITE_NOT_AVAILABLE"]
    assert cert["query_declarations"] == [] and cert["human_accepted"] is False and not errors(cert)

    _, read = walk(tmp_path, monkeypatch, "trivial", probe={Q: {"statement_trivially_provable": True}})
    trivial = read("chain-certificate.json")  # the scheduler withholds a trivially provable query
    assert trivial["missing_obligations"] == ["QUERY_NOT_KERNEL_ATTESTED " + Q + ": AWAITING_REVIEW/STATEMENT_TRIVIALLY_PROVABLE"]

    _, read = walk(tmp_path, monkeypatch, "unprobed", probe={Q: {}})
    result, unprobed = read("proof-walk-result.json"), read("chain-certificate.json")  # no probe, no emission
    assert unprobed["state"] == "CHAIN_INCOMPLETE" and unprobed["missing_obligations"] == ["QUERY_STATEMENT_TRIVIALITY_UNPROBED " + Q]
    relabelled = copy.deepcopy(result)  # the graph's node kind, not the record's state, exempts definitions
    relabelled["completed_candidates"][Q]["kernel_attestation_state"] = "DEFINITION_ELABORATED"
    assert certificate(read("candidate-root-audited-graph.json"), relabelled, plan_id="plan:x",
                       environment_sha256=ENV)["missing_obligations"] == unprobed["missing_obligations"]
    result["completed_candidates"][Q]["evidence"]["statement_trivially_provable"] = False
    emitted = certificate(read("candidate-root-audited-graph.json"), result, plan_id="plan:x", environment_sha256=ENV)
    assert emitted["state"] == "CHAIN_CERTIFICATE_EMITTED"
    result["completed_candidates"][Q]["evidence"]["statement_trivially_provable"] = True  # so does the certificate
    flagged = certificate(read("candidate-root-audited-graph.json"), result, plan_id="plan:x", environment_sha256=None)
    assert flagged["state"] == "CHAIN_INCOMPLETE" and flagged["missing_obligations"] == ["QUERY_STATEMENT_TRIVIALLY_PROVABLE " + Q]
    assert not errors(trivial) and not errors(flagged) and not errors(unprobed) and not errors(emitted)
    assert errors({**emitted, "query_declarations": []}) and errors({**emitted, "headline": "verified"})
    assert errors({**cert, "human_accepted": True}) and errors({**emitted, "human_accepted": True})


@pytest.mark.parametrize("status", ["SOMETHING_ELSE", "NO_LIBRARY_PROVIDES_THIS", "LIBRARY_BOUND"])
def test_root_audits_must_be_library_searched(tmp_path, monkeypatch, status):
    with pytest.raises(ValueError, match="RootAudit"):  # only library.root_audits' LIBRARY_SEARCHED records
        walk(tmp_path, monkeypatch, "status", root_audit=status)
    assert not (tmp_path / "status").exists()


def test_root_audits_come_only_from_the_request_for_its_graph(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="another graph"):
        walk(tmp_path, monkeypatch, "stale", audit_graph={**graph(), "query_ids": [B]})
    prebaked = graph()  # an audit shipped inside the graph would skip both request gates
    prebaked["nodes"][0]["root_audit"] = {"status": "LIBRARY_BOUND", "program_receipt": LEAN,
        "library_binding": {"library": "L", "revision": ENV, "declaration": "Nat.le_refl"}}
    with pytest.raises(ValueError, match="input graph"):
        walk(tmp_path, monkeypatch, "prebaked", root_audit=None, base=prebaked)
    assert not (tmp_path / "prebaked").exists()


def test_certify_refuses_a_run_whose_audit_fails(tmp_path, monkeypatch):
    walk(tmp_path, monkeypatch, "run")  # a stub run: the real proof-walk audit cannot pass it
    with pytest.raises(SystemExit, match="Refusing to certify"):
        recertify(monkeypatch, tmp_path / "run", tmp_path / "cert.json", audit_status=None)
    assert not (tmp_path / "cert.json").exists()
    report = json.loads((tmp_path / "cert.run-audit.json").read_bytes())
    assert report["status"] == "FAILED" and "verified_file_references" in report  # the auditor's own report
