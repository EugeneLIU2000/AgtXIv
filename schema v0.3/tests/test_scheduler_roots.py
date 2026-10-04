"""LIBRARY_SEARCHED roots are attemptable; placeholders and trivial statements stay blocked."""
import pytest

from core import PlanLedger
from scheduler import _root_audited, _statement_fingerprint, bottom_up_walk

ENV = "sha256:" + "e" * 64
RECEIPT = {"kind": "ProgramReceipt", "engine_class": "HOST", "status": "SUCCEEDED", "exit_code": 0,
           "operation": "lean.model_candidate", "input_sha256": "sha256:1", "output_sha256": "sha256:2"}
SEARCHED = {"status": "LIBRARY_SEARCHED", "searched_revisions": [ENV], "candidates": ["Finset.card_inter_le"],
            "method": "LEXICAL_IDF_TOKEN_OVERLAP_V1", "index": {"path": "i", "sha256": ENV, "byte_size": 1},
            "program_receipt": RECEIPT, "binding_accepted": False}


def graph():
    nodes = [{"id": "root", "kind": "lemma", "text": "root statement", "root_audit": SEARCHED},
             {"id": "occ", "kind": "unresolved_claim_occurrence", "text": "unresolved",
              "blocked_by": ["UNRESOLVED_CLAIM_OCCURRENCE"]},
             {"id": "a", "kind": "theorem", "text": "uses the root"},
             {"id": "b", "kind": "theorem", "text": "uses the placeholder"}]
    for node in nodes:
        node["source_spans"] = [{"path": "p.tex", "byte_start": 0, "byte_end": 1}]
    return {"nodes": nodes, "query_ids": ["a", "b"], "sccs": [], "condensation_order": ["root", "occ", "a", "b"],
            "support_groups": [{"id": "g:a", "target": "a", "members": ["root"]},
                               {"id": "g:b", "target": "b", "members": ["occ"]}]}


def walk(tmp_path, **extra):
    plan = {"plan_id": "plan:roots", "decision_policy": "CANDIDATE_EXPLORATION",
            "limits": {"max_proof_attempts": 10, "max_node_attempts": 1},
            "environment": {"lean_environment_sha256": ENV}}
    calls = []

    def attempt(node, number, prerequisites, reservation):
        calls.append(node["id"])
        result = {"kernel_checked": True, "program_receipt": RECEIPT, "source_node_id": node["id"],
                  "source_statement_sha256": _statement_fingerprint(node), "lamport": {"path": "l"},
                  "lean_source": {"path": "s"}, "declaration_bindings": [{"declaration": "D." + node["id"]}],
                  "nonvacuity_witness": "NONE", "declaration_kind": "THEOREM", "forbidden_axioms": [],
                  "hypotheses": [], "composition_witnesses": [
                      {"upstream_node_id": key, "downstream_node_id": node["id"], "status": "COMPOSED",
                       "basis": "LEAN_ELABORATED_TERM_CONSTANT"} for key in prerequisites]}
        return {**result, **extra.get(node["id"], {})}

    result = bottom_up_walk(graph(), attempt, lambda *args: None, ledger=PlanLedger(tmp_path, plan))
    return calls, {row["node_id"]: row for row in result["outcomes"]}, result


def test_searched_root_is_attempted_and_placeholder_dependents_stay_blocked(tmp_path):
    calls, outcomes, result = walk(tmp_path)
    assert calls == ["root", "a"]
    assert outcomes["root"]["state"] == outcomes["a"]["state"] == "AWAITING_REVIEW"
    assert set(result["available_dependencies"]) == {"root", "a"}
    assert outcomes["occ"]["state"] == "CONDITIONAL_ON_BLOCKED_ROOT"
    assert outcomes["b"]["state"] == "CONDITIONAL_ON_BLOCKED_ROOT" and outcomes["b"]["blocked_by"] == ["occ"]


@pytest.mark.parametrize("flag, reason", [(True, "STATEMENT_TRIVIALLY_PROVABLE"), (None, "STATEMENT_TRIVIALITY_UNKNOWN")])
def test_trivial_statement_stays_awaiting_review_and_is_not_discharged(tmp_path, flag, reason):
    calls, outcomes, result = walk(tmp_path, root={"statement_trivially_provable": flag})
    assert calls == ["root"] and outcomes["root"]["reason"] == reason
    assert outcomes["root"]["state"] == "AWAITING_REVIEW" and "root" not in result["available_dependencies"]
    assert outcomes["a"]["reason"] == "PREREQUISITE_NOT_AVAILABLE"


def test_nontrivial_flag_keeps_the_legacy_path(tmp_path):
    _, _, result = walk(tmp_path, root={"statement_trivially_provable": False})
    assert set(result["available_dependencies"]) == {"root", "a"}


@pytest.mark.parametrize("change", [{"searched_revisions": []}, {"candidates": None}, {"binding_accepted": True},
                                    {"program_receipt": {**RECEIPT, "engine_class": "MODEL"}}])
def test_malformed_library_search_is_not_a_root_audit(change):
    assert _root_audited({"root_audit": SEARCHED})
    assert not _root_audited({"root_audit": {**SEARCHED, **change}})
