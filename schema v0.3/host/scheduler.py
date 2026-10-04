"""Durable source frontier and a still-unconnected bottom-up proof-worker seam.

Frontier and proof-attempt caps are transactional and durable. Model calls still
reserve their monetary/call quota separately through the same PlanLedger.
The research controller has exercised source admission and normal resumption;
this does not attest concurrency, fault recovery or the proof-worker callbacks.
"""
from __future__ import annotations

from collections import defaultdict
import json
import re
import subprocess
import time
from typing import Callable
import uuid

from core import PlanLedger, TERMINAL_KINDS, VERSION, canonical, decision_gate, digest, utcnow
from ingest import normalize_paper_id
from clause_coverage import candidate_clause_status


FAILURE_KINDS = frozenset({"SYNTAX", "MISSING_LEMMA", "STATEMENT_WRONG", "TIMEOUT",
                           "HEARTBEAT", "UNPROVABLE_AS_STATED"})
RETRY_STRATEGIES = {
    "SYNTAX": "REPAIR_SYNTAX_WITH_SAME_STATEMENT",
    "MISSING_LEMMA": "SEARCH_PINNED_LIBRARY",
    "STATEMENT_WRONG": "RETURN_TO_SOURCE_ALIGNMENT",
    "TIMEOUT": "REPLAN_WITHIN_REMAINING_TIME",
    "HEARTBEAT": "REFACTOR_PROOF_WITHIN_RESOURCE_CAP",
    "UNPROVABLE_AS_STATED": "RECORD_EXPLICIT_PREMISE_AND_COUNTEREVIDENCE",
}


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + " must be a nonempty string")
    return value


def _advances(confidence, registry):
    if not isinstance(confidence, dict):
        return False
    try:
        return decision_gate(confidence, calibration_registry=registry) == "ADVANCE_CANDIDATE"
    except (TypeError, ValueError, KeyError):
        # A malformed classification gates its own branch, not independent work.
        return False


class Frontier:
    """Versioned-paper queue, stable lead identities, and unique worker tokens.

    Failed papers retain their reserved paper slot. Retrying one paper does not
    consume another slot. Model/money reservation belongs to PlanLedger at worker
    dispatch, not this queue. A trusted human flag is an explicit caller argument,
    never a field inferred from model output. take() requires the current graph.
    """

    def __init__(self, ledger):
        self.ledger, self.db = ledger, ledger.db
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self.ledger._frozen_plan()
            self.db.execute("""CREATE TABLE IF NOT EXISTS frontier(
                plan_id TEXT NOT NULL REFERENCES plans(id), paper_id TEXT NOT NULL,
                lead_id TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL,
                updated TEXT NOT NULL, admitted INTEGER NOT NULL DEFAULT 0,
                claim_token TEXT, attempts INTEGER NOT NULL DEFAULT 0, admission_json TEXT,
                PRIMARY KEY(plan_id,paper_id))""")
            columns = {row[1] for row in self.db.execute("PRAGMA table_info(frontier)")}
            for name, declaration in (("admitted", "INTEGER NOT NULL DEFAULT 0"),
                                      ("claim_token", "TEXT"),
                                      ("attempts", "INTEGER NOT NULL DEFAULT 0"),
                                      ("admission_json", "TEXT")):
                if name not in columns:
                    self.db.execute(f"ALTER TABLE frontier ADD COLUMN {name} {declaration}")
            self.db.execute("UPDATE frontier SET admitted=1 WHERE plan_id=? AND state IN ('QUEUED','RUNNING','RECORDED')",
                            (frozen["plan_id"],))

    def _event(self, kind, result):
        self.db.execute("INSERT INTO events(plan_id,kind,payload) VALUES (?,?,?)",
                        (self.ledger._frozen_plan()["plan_id"], kind, canonical(result).decode()))

    def seed(self, paper_id):
        """Reserve and claim the frozen query paper once, including its paper slot.

        Only a newly claimed seed returns a work token. Every existing paper row
        returns claimed=False without its token, even after failure or completion.
        Such a row is never restarted or adopted by calling seed again. Persist
        the first returned work object for record() and explicit crash recovery.
        A query seed authorizes source acquisition, never acceptance of its claims.
        """
        paper_id = normalize_paper_id(_text(paper_id, "paper_id"))
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self.ledger._frozen_plan()
            policy = self.ledger.decision_policy()
            query_id = normalize_paper_id(_text(frozen.get("paper_id"), "plan.paper_id"))
            if paper_id != query_id:
                raise ValueError("seed paper must equal the frozen query paper")
            if not re.search(r"v[1-9]\d*$", paper_id):
                raise ValueError("query seed requires an explicitly pinned paper version")
            pid = frozen["plan_id"]
            existing = self.db.execute("""SELECT lead_id,state,reason,admitted,admission_json
                FROM frontier WHERE plan_id=? AND paper_id=?""", (pid, paper_id)).fetchone()
            if existing:
                admission = json.loads(existing[4]) if existing[4] else None
                return {"paper_id": paper_id, "lead_id": existing[0], "state": existing[1],
                        "reason": existing[2], "decision_reason": "QUERY_PAPER_ALREADY_PRESENT",
                        "claimed": False, "admitted": bool(existing[3]),
                        "admission_evidence": admission, **self._review_metadata(admission, policy)}
            count = self.db.execute("SELECT COUNT(*) FROM frontier WHERE plan_id=? AND admitted=1",
                                    (pid,)).fetchone()[0]
            admitted = count < frozen["limits"]["max_papers"]
            state = "RUNNING" if admitted else "FRONTIER"
            reason = "FROZEN_QUERY_PAPER" if admitted else "PAPER_BUDGET_EXHAUSTED"
            token = uuid.uuid4().hex if admitted else None
            lead_id = "query-seed:" + paper_id
            admission = {"admission_kind": "QUERY_SEED", "paper_id": paper_id,
                         "terminal_kind": "ARXIV_SOURCE_AVAILABLE", "decision_policy": policy,
                         "decision_reason": reason, "bound_to_frozen_query": True,
                         "unreviewed_blockers": (["candidate-exploration:" + paper_id]
                                                 if policy == "CANDIDATE_EXPLORATION" else [])}
            self.db.execute("""INSERT INTO frontier
                (plan_id,paper_id,lead_id,state,reason,updated,admitted,claim_token,attempts,admission_json)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (pid, paper_id, lead_id, state, reason, utcnow(), int(admitted), token,
                 int(admitted), canonical(admission).decode()))
            work = {"paper_id": paper_id, "lead_id": lead_id, "state": state, "reason": reason,
                    "claimed": admitted, "admitted": admitted, "admission_evidence": admission,
                    **self._review_metadata(admission, policy)}
            if token is not None:
                work["claim_token"] = token
            self._event("FrontierSeeded", work)
            return work

    def admit_retained_pdf(self, paper_id, pdf_run, lead, graph):
        """Count an already extracted PDF against the same transactional paper cap.

        This is candidate exploration, not an arXiv version or earliest-origin
        assertion. No worker token is needed because extraction is reused.
        """
        from pdf_proof_context import pdf_source_binding
        paper_id = _text(paper_id, "paper_id")
        if self.ledger.decision_policy() != "CANDIDATE_EXPLORATION":
            raise ValueError("PDF_ADMISSION_REQUIRES_CANDIDATE_EXPLORATION")
        if not self._load_bearing(lead, graph):
            raise ValueError("PDF_ADMISSION_NOT_LOAD_BEARING")
        pdf_source_binding(paper_id, {"pdf_run": pdf_run})
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self.ledger._frozen_plan()
            pid = frozen["plan_id"]
            old = self.db.execute("SELECT admitted,admission_json FROM frontier WHERE plan_id=? AND paper_id=?",
                                  (pid, paper_id)).fetchone()
            if old:
                evidence = json.loads(old[1]) if old[1] else {}
                if evidence.get("admission_kind") != "RETAINED_PDF_SOURCE" or evidence.get("pdf_run") != pdf_run:
                    raise ValueError("PDF_ADMISSION_CONFLICTING_SOURCE")
                return {"paper_id": paper_id, "admitted": bool(old[0]), "reused": True,
                        "reason": "PAPER_ALREADY_ADMITTED", "admission_evidence": evidence}
            count = self.db.execute("SELECT COUNT(*) FROM frontier WHERE plan_id=? AND admitted=1", (pid,)).fetchone()[0]
            if count >= frozen["limits"]["max_papers"]:
                return {"paper_id": paper_id, "admitted": False, "reason": "PAPER_BUDGET_EXHAUSTED"}
            evidence = {"admission_kind": "RETAINED_PDF_SOURCE", "pdf_run": pdf_run,
                        "paper_id": paper_id, "upstream_node_id": lead["upstream_node_id"],
                        "downstream_node_id": lead["downstream_node_id"],
                        "node_binding_sha256": self._binding_fingerprint(lead, graph),
                        "decision_policy": "CANDIDATE_EXPLORATION",
                        "unreviewed_blockers": ["candidate-exploration:" + paper_id,
                                                 "unreviewed-paper-identity:" + paper_id]}
            self.db.execute("""INSERT INTO frontier
                (plan_id,paper_id,lead_id,state,reason,updated,admitted,claim_token,attempts,admission_json)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (pid, paper_id, lead["lead_id"], "RECORDED", "RETAINED_PDF_EXTRACTION_REUSED",
                 utcnow(), 1, None, 0, canonical(evidence).decode()))
            result = {"paper_id": paper_id, "admitted": True, "reused": False,
                      "reason": "RETAINED_PDF_EXTRACTION_REUSED", "admission_evidence": evidence}
            self._event("RetainedPDFAdmitted", result)
            return result

    def snapshot(self):
        """Read the queue without claiming work, changing state, or exposing tokens.

        has_active_claim describes an outstanding worker; it is not authorization
        to adopt its work. Recover only with the original persisted work token and
        after establishing that its worker has stopped.
        """
        frozen = self.ledger._frozen_plan()
        policy = self.ledger.decision_policy()
        rows = self.db.execute("""SELECT f.paper_id,f.lead_id,f.state,f.reason,f.updated,
            f.admitted,f.claim_token IS NOT NULL,f.attempts,f.admission_json,
            COALESCE(p.empty_runs,0) FROM frontier AS f LEFT JOIN progress AS p
            ON p.plan_id=f.plan_id AND p.lead=f.lead_id WHERE f.plan_id=? ORDER BY f.paper_id""",
            (frozen["plan_id"],)).fetchall()
        papers, state_counts = [], defaultdict(int)
        for row in rows:
            admission = json.loads(row[8]) if row[8] else None
            papers.append({"paper_id": row[0], "lead_id": row[1], "state": row[2],
                           "reason": row[3], "updated": row[4], "admitted": bool(row[5]),
                           "has_active_claim": bool(row[6]), "attempts": row[7],
                           "consecutive_empty_runs": row[9], "admission_evidence": admission,
                           **self._review_metadata(admission, policy)})
            state_counts[row[2]] += 1
        admitted = sum(paper["admitted"] for paper in papers)
        return {"kind": "FrontierSnapshot", "plan_id": frozen["plan_id"],
                "query_paper_id": frozen["paper_id"], "decision_policy": policy,
                "max_papers": frozen["limits"]["max_papers"], "admitted_papers": admitted,
                "remaining_papers": max(0, frozen["limits"]["max_papers"] - admitted),
                "no_progress_limit": frozen["limits"]["no_progress_limit"],
                "state_counts": dict(state_counts), "papers": papers}

    @staticmethod
    def _binding_fingerprint(admission, graph):
        indexed = {node["id"]: node for node in graph["nodes"]}
        return digest(canonical([{key: indexed.get(node_id, {}).get(key)
                                  for key in ("id", "paper_id", "text", "source_spans")}
                                 for node_id in (admission["upstream_node_id"], admission["downstream_node_id"])]))

    @staticmethod
    def _load_bearing(admission, graph):
        if not admission or not all(admission.get(key) for key in ("upstream_node_id", "downstream_node_id")):
            return False
        selected = set(graph["selected_node_ids"])
        edge = (admission["upstream_node_id"], admission["downstream_node_id"])
        return (set(edge) <= selected and edge in {(e["from"], e["to"]) for e in graph["edges"]}
                and (not admission.get("node_binding_sha256") or
                     admission["node_binding_sha256"] == Frontier._binding_fingerprint(admission, graph)))

    @staticmethod
    def _review_metadata(admission, policy):
        blockers = sorted(set((admission or {}).get("unreviewed_blockers", [])))
        if policy == "CANDIDATE_EXPLORATION" and not blockers:
            # Even an older/incomplete admission cannot lose the frozen policy's
            # review boundary when it is projected or resumed.
            blockers = ["candidate-exploration:frontier"]
        return {"decision_policy": policy,
                "review_state": "AWAITING_REVIEW" if blockers else "CANDIDATE",
                "unreviewed_blockers": blockers, "source_alignment_accepted": False,
                "promotion_allowed": False}

    def consider(self, lead, graph, *, calibration_registry, trusted_human_decision=False):
        if type(trusted_human_decision) is not bool:
            raise ValueError("trusted_human_decision must be a host boolean")
        policy = self.ledger.decision_policy()
        exploratory = policy == "CANDIDATE_EXPLORATION"
        paper_id = normalize_paper_id(_text(lead.get("paper_id"), "paper_id"))
        proposed_id = _text(lead.get("lead_id"), "lead_id")
        _text(lead.get("upstream_node_id"), "upstream_node_id")
        _text(lead.get("downstream_node_id"), "downstream_node_id")
        terminal_kind = lead.get("terminal_kind")
        if terminal_kind not in TERMINAL_KINDS:
            raise ValueError("missing or unknown terminal_kind")
        node_map = {node["id"]: node for node in graph["nodes"]}
        bound_paper = node_map.get(lead["upstream_node_id"], {}).get("paper_id")
        identity_bound = bool(bound_paper and normalize_paper_id(bound_paper) == paper_id)
        support_ok = trusted_human_decision or _advances(lead.get("confidence"), calibration_registry)
        identity_ok = (trusted_human_decision or identity_bound or
                       _advances(lead.get("identity_confidence"), calibration_registry))
        if not self._load_bearing(lead, graph):
            state, reason = "REJECTED", "NOT_LOAD_BEARING_IN_CURRENT_GRAPH"
        elif (not support_ok or not identity_ok) and not (
                exploratory and terminal_kind == "ARXIV_SOURCE_AVAILABLE"):
            state, reason = "AWAITING_REVIEW", "UNCALIBRATED_SUPPORT_OR_IDENTITY"
        elif terminal_kind == "FOLKLORE_NO_PRIMARY_SOURCE" and not lead.get("subject_match_evidence"):
            state, reason = "AWAITING_REVIEW", "FOLKLORE_REQUIRES_A_THEOREM_STATING_SOURCE"
        elif terminal_kind == "IN_LIBRARY" and not all(
                isinstance(lead.get("library_binding"), dict) and lead["library_binding"].get(key)
                for key in ("library", "revision", "declaration")):
            state, reason = "AWAITING_REVIEW", "LIBRARY_BINDING_INCOMPLETE"
        elif terminal_kind != "ARXIV_SOURCE_AVAILABLE":
            state, reason = "TERMINAL", "TYPED_TERMINAL; ORIGIN_NOT_IMPLIED"
        elif not re.search(r"v\d+$", paper_id):
            state, reason = "FRONTIER", "PAPER_VERSION_NOT_PINNED"
        else:
            state, reason = "QUEUED", ("CANDIDATE_EXPLORATION; REVIEW_REQUIRED" if exploratory
                                       else "CHECKED_LOAD_BEARING_LEAD")
        blockers = []
        if exploratory:
            blockers.append("candidate-exploration:" + paper_id)
        if not support_ok:
            blockers.append("unreviewed-support:" + proposed_id)
        if not identity_ok:
            blockers.append("unreviewed-paper-identity:" + proposed_id)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self.ledger._frozen_plan()
            pid = frozen["plan_id"]
            existing = self.db.execute("""SELECT lead_id,state,reason,admitted,attempts,admission_json
                FROM frontier WHERE plan_id=? AND paper_id=?""", (pid, paper_id)).fetchone()
            lead_id = existing[0] if existing else proposed_id
            admitted = existing[3] if existing else 0
            previous_admission = json.loads(existing[5]) if existing and existing[5] else None
            if existing and (existing[1] in {"RUNNING", "RECORDED"} or
                             (previous_admission or {}).get("admission_kind") == "QUERY_SEED"):
                result = {"paper_id": paper_id, "lead_id": lead_id, "state": existing[1],
                          "reason": "PAPER_ALREADY_ADMITTED", "admission_evidence": previous_admission,
                          **self._review_metadata(previous_admission, policy)}
                self._event("FrontierDecision", result)
                return result
            admission = previous_admission
            # A weaker duplicate must not erase an existing, still-load-bearing admission.
            if (existing and existing[1] == "QUEUED" and state in {"AWAITING_REVIEW", "REJECTED"}
                    and self._load_bearing(previous_admission, graph)):
                state, reason = "QUEUED", existing[2]
            else:
                admission = {"upstream_node_id": lead["upstream_node_id"],
                             "downstream_node_id": lead["downstream_node_id"],
                             "terminal_kind": terminal_kind, "confidence": lead.get("confidence"),
                             "identity_confidence": lead.get("identity_confidence"),
                             "identity_bound_to_graph": identity_bound,
                             "trusted_human_decision": trusted_human_decision,
                             "subject_match_evidence": lead.get("subject_match_evidence"),
                             "library_binding": lead.get("library_binding"),
                             "decision_policy": policy, "decision_reason": reason,
                             "unreviewed_blockers": blockers,
                             "node_binding_sha256": self._binding_fingerprint(lead, graph)}
            if state == "QUEUED":
                progress = self.db.execute("SELECT empty_runs FROM progress WHERE plan_id=? AND lead=?",
                                           (pid, lead_id)).fetchone()
                count = self.db.execute("SELECT COUNT(*) FROM frontier WHERE plan_id=? AND admitted=1",
                                        (pid,)).fetchone()[0]
                if progress and progress[0] >= frozen["limits"]["no_progress_limit"]:
                    state, reason = "FRONTIER", "NO_PROGRESS_LIMIT"
                elif not admitted and count >= frozen["limits"]["max_papers"]:
                    state, reason = "FRONTIER", "PAPER_BUDGET_EXHAUSTED"
                else:
                    admitted = 1
            self.db.execute("""INSERT INTO frontier
                (plan_id,paper_id,lead_id,state,reason,updated,admitted,claim_token,attempts,admission_json)
                VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(plan_id,paper_id) DO UPDATE SET
                state=excluded.state,reason=excluded.reason,updated=excluded.updated,
                admitted=excluded.admitted,claim_token=NULL,admission_json=excluded.admission_json""",
                (pid, paper_id, lead_id, state, reason, utcnow(), admitted, None,
                 existing[4] if existing else 0, canonical(admission).decode() if admission else None))
            result = {"paper_id": paper_id, "lead_id": lead_id, "state": state, "reason": reason,
                      "admission_evidence": admission, **self._review_metadata(admission, policy)}
            self._event("FrontierDecision", result)
        return result

    def take(self, graph, *, calibration_registry):
        """Recheck current graph, calibration and no-progress state before claiming."""
        policy = self.ledger.decision_policy()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self.ledger._frozen_plan()
            pid = frozen["plan_id"]
            rows = self.db.execute("""SELECT paper_id,lead_id,admission_json FROM frontier
                WHERE plan_id=? AND state='QUEUED' ORDER BY paper_id""", (pid,)).fetchall()
            for paper_id, lead_id, encoded in rows:
                admission = json.loads(encoded) if encoded else None
                progress = self.db.execute("SELECT empty_runs FROM progress WHERE plan_id=? AND lead=?",
                                           (pid, lead_id)).fetchone()
                authorized = bool(admission and (admission.get("trusted_human_decision") or
                    (policy == "CANDIDATE_EXPLORATION" and
                     admission.get("terminal_kind") == "ARXIV_SOURCE_AVAILABLE") or
                    (_advances(admission.get("confidence"), calibration_registry) and
                     (admission.get("identity_bound_to_graph") or
                      _advances(admission.get("identity_confidence"), calibration_registry)))))
                reason = ("NOT_LOAD_BEARING_IN_CURRENT_GRAPH" if not self._load_bearing(admission, graph)
                          else "ADMISSION_POLICY_MISMATCH" if admission.get("decision_policy", "STRICT_CALIBRATED") != policy
                          else "PAPER_VERSION_NOT_PINNED" if not re.search(r"v\d+$", paper_id)
                          else "ADMISSION_CALIBRATION_NO_LONGER_VALID" if not authorized
                          else "NO_PROGRESS_LIMIT" if progress and progress[0] >= frozen["limits"]["no_progress_limit"]
                          else None)
                if reason:
                    self.db.execute("UPDATE frontier SET state='FRONTIER',reason=?,updated=? WHERE plan_id=? AND paper_id=?",
                                    (reason, utcnow(), pid, paper_id))
                    self._event("FrontierDeferred", {"paper_id": paper_id, "lead_id": lead_id, "reason": reason,
                                                     **self._review_metadata(admission, policy)})
                    continue
                token = uuid.uuid4().hex
                self.db.execute("""UPDATE frontier SET state='RUNNING',claim_token=?,attempts=attempts+1,updated=?
                    WHERE plan_id=? AND paper_id=? AND state='QUEUED'""", (token, utcnow(), pid, paper_id))
                work = {"paper_id": paper_id, "lead_id": lead_id, "claim_token": token,
                        "admission_evidence": admission, **self._review_metadata(admission, policy)}
                self._event("FrontierClaimed", work)
                return work
        return None

    def record(self, work, new_items, success, *, failure_reason="SOURCE_UNREACHABLE"):
        """Commit progress once for the current worker, refusing stale results.

        A trusted controller may recover a crashed worker with its persisted token
        and failure_reason='WORKER_INTERRUPTED'. It consumes one no-progress attempt;
        a delayed result from that worker can no longer overwrite a newer claim.
        """
        if type(success) is not bool or type(new_items) is not int or new_items < 0:
            raise ValueError("success must be boolean and new_items a nonnegative integer")
        if failure_reason not in {"SOURCE_UNREACHABLE", "SOURCE_READ_DEFECTIVE", "HOST_PROCESSING_FAILED", "WORKER_INTERRUPTED"}:
            raise ValueError("unknown frontier failure reason")
        policy = self.ledger.decision_policy()
        paper_id = normalize_paper_id(work["paper_id"])
        token = _text(work.get("claim_token"), "claim_token")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self.ledger._frozen_plan()
            pid = frozen["plan_id"]
            row = self.db.execute("SELECT lead_id,state,claim_token,admission_json FROM frontier WHERE plan_id=? AND paper_id=?",
                                  (pid, paper_id)).fetchone()
            if row is None or tuple(row[:3]) != (work.get("lead_id"), "RUNNING", token):
                raise ValueError("unknown, stale, or already-recorded frontier work")
            admission = json.loads(row[3]) if row[3] else None
            previous = self.db.execute("SELECT empty_runs FROM progress WHERE plan_id=? AND lead=?",
                                       (pid, row[0])).fetchone()
            empty = 0 if success and new_items > 0 else (previous[0] if previous else 0) + 1
            self.db.execute("INSERT OR REPLACE INTO progress VALUES (?,?,?)", (pid, row[0], empty))
            state, reason = ("RECORDED", "SOURCE_RECORDED") if success else ("FRONTIER", failure_reason)
            if empty >= frozen["limits"]["no_progress_limit"]:
                state, reason = "FRONTIER", "NO_PROGRESS_LIMIT"
            self.db.execute("UPDATE frontier SET state=?,reason=?,updated=?,claim_token=NULL WHERE plan_id=? AND paper_id=?",
                            (state, reason, utcnow(), pid, paper_id))
            # NO_PROGRESS_LIMIT may replace the reason; a failure keeps its classification beside it.
            result = {"paper_id": paper_id, "lead_id": row[0], "state": state, "reason": reason,
                      **({} if success else {"failure_reason": failure_reason}),
                      "new_items": new_items if success else 0, "consecutive_empty_runs": empty,
                      "admission_evidence": admission, **self._review_metadata(admission, policy)}
            self._event("FrontierRecorded", result)
        return result


def _host_receipt(receipt):
    return (isinstance(receipt, dict) and receipt.get("kind") == "ProgramReceipt"
            and receipt.get("engine_class") == "HOST"
            and (receipt.get("status") == "SUCCEEDED" or
                 (receipt.get("outcome") == "RECORDED" and "status" not in receipt))
            and bool(receipt.get("input_sha256")) and bool(receipt.get("output_sha256")))


def _lean_receipt(receipt):
    """Shape guard only: the injected host is responsible for receipt authenticity."""
    return (_host_receipt(receipt) and receipt.get("status") == "SUCCEEDED"
            and type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0
            and str(receipt.get("operation", "")).startswith("lean."))


def _root_audited(node):
    audit = node.get("root_audit")
    if not isinstance(audit, dict) or not _host_receipt(audit.get("program_receipt")):
        return False
    # A searched root is attemptable; its ranked candidates are not a binding.
    if audit.get("status") == "LIBRARY_SEARCHED":
        return (bool(audit.get("searched_revisions")) and isinstance(audit.get("candidates"), list)
                and audit.get("binding_accepted") is False)
    # Only proof_walk writes LIBRARY_BOUND, for an audited candidate_root_bindings declaration.
    return (audit.get("status") == "LIBRARY_BOUND" and isinstance(audit.get("library_binding"), dict)
            and all(audit["library_binding"].get(key) for key in ("library", "revision", "declaration")))


def _statement_fingerprint(node):
    return digest(canonical({"node_id": node["id"], "text": node.get("text"),
                             "source_spans": node.get("source_spans", [])}))


def _checked_premise(premise, node, registry, trusted_nodes, *, exploratory=False):
    return (isinstance(premise, dict) and bool(node.get("source_spans")) and bool(node.get("text"))
            and premise.get("source_node_id") == node["id"]
            and premise.get("source_statement_sha256") == _statement_fingerprint(node)
            and bool(premise.get("lean_prop")) and bool(premise.get("declaration"))
            and premise.get("elaborated_type") == "Prop" and premise.get("forbidden_axioms") == []
            and _lean_receipt(premise.get("program_receipt"))
            and (exploratory or node["id"] in trusted_nodes or
                 _advances(premise.get("alignment_confidence"), registry)))


def _nonvacuity_checked(witness):
    return (isinstance(witness, dict) and bool(witness.get("term"))
            and witness.get("term") != "NONE" and _lean_receipt(witness.get("program_receipt")))


def _reserved_callback(ledger, node_id, context_sha256, kind, callback, *, reuse):
    """Reuse exact-context evidence or atomically reserve, execute and settle once."""
    history = ledger.proof_attempt_history(node_id, context_sha256=context_sha256, kind=kind)
    if reuse and history:
        latest = history[-1]
        if latest["state"] == "RESERVED":
            raise RuntimeError("NODE_PROOF_ATTEMPT_ALREADY_RESERVED")
        return latest
    reservation = ledger.reserve_proof_attempt(node_id, context_sha256, kind=kind)
    started, tick = utcnow(), time.monotonic()
    interrupted = None
    try:
        result = callback(reservation)
        canonical(result)  # Refuse unserializable callback evidence before settlement.
        outcome = "RETURNED"
    except BaseException as exc:
        timed_out = isinstance(exc, (TimeoutError, subprocess.TimeoutExpired))
        outcome = "TIMED_OUT" if timed_out else "FAILED" if isinstance(exc, Exception) else "INTERRUPTED"
        result = {"callback_exception": {"type": type(exc).__name__, "message": str(exc)}}
        if timed_out:
            result["failure_kind"] = "TIMEOUT"
        if not isinstance(exc, Exception):
            interrupted = exc
    receipt = {"kind": "ProgramReceipt", "contract_version": VERSION,
               "program": "agtxiv.research.host.scheduler/0.3.0",
               "operation": "scheduler.proof_attempt" if kind == "PROOF" else "scheduler.premise_attempt",
               "engine_class": "HOST", "call": None,
               "input_sha256": context_sha256, "output_sha256": digest(canonical(result)),
               "started_at": started, "finished_at": utcnow(),
               "elapsed_seconds": round(time.monotonic() - tick, 6),
               "outcome": "RECORDED" if outcome == "RETURNED" else "FAILED"}
    if interrupted is not None:
        # Interrupting this controller does not establish that a child worker
        # stopped. Keep its durable exclusion lock until explicit host recovery.
        ledger.event("ProofAttemptInterruptionObserved", {
            "reservation": reservation, "receipt": receipt, "result": result,
            "state": "RESERVED", "reason": "WORKER_STOP_NOT_CONFIRMED"})
        raise interrupted
    ledger.settle_proof_attempt(reservation, receipt, result=result, outcome=outcome)
    return {**reservation, "state": "SETTLED", "outcome": outcome,
            "receipt": receipt, "result": result}


def bottom_up_walk(graph, attempt: Callable, render_premise: Callable, *, ledger: PlanLedger, cap=None,
                   calibration_registry=None, selected_group_ids=None,
                   trusted_human_support_groups=(), trusted_human_failure_decisions=(),
                   trusted_human_premise_nodes=()):
    """Future proof walk, not connected to the running migration pipeline.

    Supply host-reviewed group IDs or calibrated group decision_confidence. With
    several OR groups, selected_group_ids chooses one; a union is never treated
    as a joint proof. Roots need root_audit. attempt(node, number, prerequisites, reservation)
    receives only available selected-group dependencies, including checked Prop
    fallbacks. Blocked, cyclic, ungated or missing-prerequisite nodes call neither
    callback. Other branches continue.

    Host results require an actual Lean receipt, declaration_kind, hypotheses,
    forbidden_axioms, bindings and per-prerequisite composition_witnesses. Literal
    nonvacuity_witness='NONE' is unknown. Retrying requires failure_confidence or
    a trusted (node_id, attempt_number) decision; failure_gate is ignored.
    render_premise(node, result, reservation) must bind an elaborated Prop to the source
    fingerprint with calibrated/human alignment. This does not prove the Prop.

    All proof/premise calls reserve a persistent slot first. The plan must freeze
    max_proof_attempts, max_node_attempts and environment.lean_environment_sha256.
    cap, if supplied, must equal the frozen node cap. Restart reuses identical-context
    evidence and rechecks gates; it cannot reset counters. Hard-killed workers stay
    RESERVED until a trusted controller confirms termination and settles recovery.
    Model/money calls still use ledger.reserve()/settle(); callbacks enforce their
    subprocess timeout and return actual Lean receipts. A wrapper receipt alone is
    not a Lean attestation. This seam is not yet connected to the case runner.
    STRICT_CALIBRATED is the default frozen decision policy. Explicit
    CANDIDATE_EXPLORATION permits unreviewed support/failure/alignment decisions
    only as candidate work. Every resulting dependency and descendant keeps an
    AWAITING_REVIEW blocker; neither policy permits acceptance or promotion here.
    """
    if not isinstance(ledger, PlanLedger):
        raise TypeError("bottom_up_walk requires an authoritative PlanLedger")
    limits = ledger.proof_attempt_limits()
    if cap is not None and (type(cap) is not int or cap != limits["max_node_attempts"]):
        raise ValueError("attempt cap must equal the frozen plan's max_node_attempts")
    cap = limits["max_node_attempts"]
    environment = ledger.plan.get("environment", {}).get("lean_environment_sha256")
    if not isinstance(environment, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", environment):
        raise RuntimeError("MISSING_FROZEN_PROOF_ENVIRONMENT")
    policy = ledger.decision_policy()
    exploratory = policy == "CANDIDATE_EXPLORATION"
    registry = calibration_registry or {}
    trusted_groups = set(trusted_human_support_groups)
    trusted_failures = set(trusted_human_failure_decisions)
    trusted_premises = set(trusted_human_premise_nodes)
    nodes = {node["id"]: node for node in graph["nodes"]}
    groups = {group["id"]: group for group in graph["support_groups"]}
    scc_members = {scc["id"]: scc["members"] for scc in graph.get("sccs", [])}
    cyclic = {node for members in scc_members.values() for node in members}
    if len(nodes) != len(graph["nodes"]) or len(groups) != len(graph["support_groups"]):
        raise ValueError("duplicate node or support-group identity")
    by_target = defaultdict(list)
    for group in groups.values():
        if group["target"] not in nodes or any(member not in nodes for member in group["members"]):
            raise ValueError("dangling support-group reference")
        by_target[group["target"]].append(group)
    explicit_choice = selected_group_ids is not None
    chosen = set(selected_group_ids or [])
    if chosen - set(groups):
        raise ValueError("selected route references an unknown group")
    selected_by_target = {}
    for node_id, alternatives in by_target.items():
        choices = [group for group in alternatives if group["id"] in chosen] if explicit_choice else alternatives
        if len(choices) > 1 and explicit_choice and node_id not in cyclic:
            raise ValueError("a selected route must choose one OR alternative per target")
        selected_by_target[node_id] = choices[0] if len(choices) == 1 else None
    active = set(graph["query_ids"])
    pending = list(active)
    while pending:
        target = pending.pop()
        if target not in nodes:
            raise ValueError("query is absent from graph")
        group = selected_by_target.get(target)
        if explicit_choice and by_target[target] and group is None and target not in cyclic:
            raise ValueError("selected route omits a required target's support group: " + target)
        # An unresolved choice keeps its alternatives inspectable; its target is gated below.
        candidate_groups = [group] if group else by_target[target]
        for item in candidate_groups:
            for member in item["members"]:
                if member not in active:
                    active.add(member)
                    pending.append(member)
    order = [node for component in graph["condensation_order"] for node in scc_members.get(component, [component])]
    if set(order) != set(nodes) or len(order) != len(nodes):
        raise ValueError("condensation order must account for all selected nodes exactly once")
    completed, available, premises, outcomes = {}, {}, {}, []
    for node_id in order:
        node = nodes[node_id]
        base = {"node_id": node_id, "attempts": len(ledger.proof_attempt_history(node_id, kind="PROOF")),
                "attempt_count_scope": "PERSISTENT_PLAN_NODE"}
        if node_id not in active:
            outcomes.append({**base, "state": "CANDIDATE", "reason": "NOT_ON_SELECTED_ROUTE"})
            continue
        if node_id in cyclic:
            outcomes.append({**base, "state": "ROUTE_UNDETERMINED", "blocked_by": node.get("blocked_by", [])})
            continue
        # Candidate exploration authorizes an attempt despite the controller's
        # review-only marker. Preserve that marker below and never waive source,
        # mathematical, identity, or missing-dependency blockers.
        review_only = {"CANDIDATE_EXPLORATION_REVIEW_REQUIRED"} if exploratory else set()
        hard_blockers = sorted(set(node.get("blocked_by", [])) - review_only)
        if hard_blockers:
            outcomes.append({**base, "state": "CONDITIONAL_ON_BLOCKED_ROOT", "blocked_by": hard_blockers,
                             "unreviewed_blockers": sorted(set(node.get("unreviewed_blockers", [])) |
                                                           (set(node.get("blocked_by", [])) & review_only))})
            continue
        group = selected_by_target.get(node_id)
        if by_target[node_id] and group is None:
            outcomes.append({**base, "state": "AWAITING_REVIEW", "reason": "ROUTE_CHOICE_REQUIRED"})
            continue
        group_approved = not group or group["id"] in trusted_groups or _advances(group.get("decision_confidence"), registry)
        if not group_approved and not exploratory:
            outcomes.append({**base, "state": "AWAITING_REVIEW", "reason": "SUPPORT_GROUP_NOT_CALIBRATED_OR_REVIEWED"})
            continue
        if group is None and not _root_audited(node):
            outcomes.append({**base, "state": "AWAITING_REVIEW", "reason": "ROOT_LIBRARY_AUDIT_REQUIRED"})
            continue
        required_ids = group["members"] if group else []
        missing = sorted(set(required_ids) - set(available))
        if missing:
            outcomes.append({**base, "state": "CONDITIONAL_ON_BLOCKED_ROOT",
                             "reason": "PREREQUISITE_NOT_AVAILABLE", "blocked_by": missing})
            continue
        context = {key: available[key] for key in required_ids}
        inherited_premises = {entry for record in context.values() for entry in record["conditional_on"]}
        inherited_vacuity = {entry for record in context.values() for entry in record["vacuity_unknown_nodes"]}
        unreviewed = set(node.get("unreviewed_blockers", []))
        unreviewed.update(set(node.get("blocked_by", [])) & review_only)
        unreviewed.update(entry for record in context.values() for entry in record.get("unreviewed_blockers", []))
        if exploratory:
            unreviewed.add("candidate-exploration:" + node_id)
        if not group_approved:
            unreviewed.add("unreviewed-support-group:" + group["id"])
        context_sha256 = digest(canonical({"node": node, "support_group": group,
            "prerequisites": context, "environment_sha256": environment, "decision_policy": policy}))
        # Reconstruct prior exploratory retry decisions so restart yields the
        # same dependency record and cannot erase why review remains necessary.
        if exploratory:
            for previous in ledger.proof_attempt_history(node_id, context_sha256=context_sha256, kind="PROOF"):
                previous_result = previous.get("result")
                if (isinstance(previous_result, dict) and previous_result.get("failure_kind") in FAILURE_KINDS
                        and (node_id, previous["attempt_number"]) not in trusted_failures
                        and not _advances(previous_result.get("failure_confidence"), registry)):
                    unreviewed.add("unreviewed-failure-classification:" + previous["id"])
        reuse = True
        # The extra evaluation permits replay of the last persisted result before
        # deciding whether a new reservation is legal; only the ledger grants slots.
        for _ in range(cap + 1):
            try:
                stored = _reserved_callback(ledger, node_id, context_sha256, "PROOF",
                    lambda reservation: attempt(node, reservation["attempt_number"], context, reservation), reuse=reuse)
            except RuntimeError as exc:
                if str(exc) not in {"NODE_PROOF_ATTEMPT_ALREADY_RESERVED", "PLAN_PROOF_ATTEMPT_BUDGET_EXHAUSTED",
                                    "NODE_PROOF_ATTEMPT_CAP_EXHAUSTED", "MODEL_PROVIDER_CIRCUIT_OPEN"}:
                    raise
                outcomes.append({**base, "state": "AWAITING_REVIEW", "reason": str(exc),
                                 "attempts": len(ledger.proof_attempt_history(node_id, kind="PROOF"))})
                break
            number, result = stored["attempt_number"], stored["result"]
            reuse = False
            if stored["outcome"] in {"FAILED", "INTERRUPTED"}:
                outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                 "reason": "HOST_ATTEMPT_CALLBACK_" + stored["outcome"],
                                 "reservation_id": stored["id"], "evidence": result})
                break
            if not isinstance(result, dict):
                outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                 "reason": "MALFORMED_HOST_ATTEMPT_RESULT"})
                break
            is_definition = node["kind"].lower() == "definition"
            if result.get("compile_disposition") == "SKIPPED_SOURCE_COVERAGE":
                outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                 "reason": "SOURCE_COVERAGE_REQUIRES_REVIEW", "evidence": result,
                                 "source_alignment_accepted": False, "promotion_allowed": False})
                break
            expected_kind = "DEFINITION" if is_definition else "THEOREM"
            bindings = result.get("declaration_bindings")
            bindings_valid = (isinstance(bindings, list) and bool(bindings)
                              and all(isinstance(item, dict) and isinstance(item.get("declaration"), str)
                                      and bool(item["declaration"]) for item in bindings))
            attested = (result.get("kernel_checked") is True and _lean_receipt(result.get("program_receipt"))
                        and result.get("source_node_id") == node_id
                        and result.get("source_statement_sha256") == _statement_fingerprint(node)
                        and bool(result.get("lamport")) and bool(result.get("lean_source")) and bindings_valid
                        and "nonvacuity_witness" in result and result.get("declaration_kind") == expected_kind
                        and result.get("forbidden_axioms") == [] and isinstance(result.get("hypotheses"), list))
            if attested:
                clause_status = candidate_clause_status(bindings)
                if clause_status in {"INCOMPLETE", "MALFORMED"}:
                    outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                     "reason": "SOURCE_CLAUSE_COVERAGE_" + clause_status,
                                     "clause_coverage_status": clause_status, "evidence": result,
                                     "source_alignment_accepted": False, "promotion_allowed": False})
                    break
                # Absent in historical results; a probe that proved or could not
                # decide the elaborated statement keeps it out of the dependencies.
                trivial = result.get("statement_trivially_provable", False)
                if trivial is not False:
                    outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number, "evidence": result,
                                     "reason": "STATEMENT_TRIVIALLY_PROVABLE" if trivial is True else
                                     "STATEMENT_TRIVIALITY_UNKNOWN",
                                     "source_alignment_accepted": False, "promotion_allowed": False})
                    break
                witnesses = result.get("composition_witnesses", [])
                if not isinstance(witnesses, list):
                    witnesses = []
                composed = {item.get("upstream_node_id") for item in witnesses
                            if isinstance(item, dict) and item.get("status") == "COMPOSED"
                            and item.get("downstream_node_id") == node_id
                            and (item.get("basis") == "LEAN_ELABORATED_TERM_CONSTANT" or
                                 (item.get("basis") == "LEAN_USED_PROP_BINDER" and
                                  context.get(item.get("upstream_node_id"), {}).get("dependency_kind") == "EXPLICIT_PROP_PREMISE" and
                                  bool(item.get("used_prop_binders"))))}
                if set(required_ids) - composed:
                    outcomes.append({**base, "state": "NOT_COMPOSED", "attempts": number, "evidence": result,
                                     "missing_composition_upstream_ids": sorted(set(required_ids) - composed)})
                    break
                vacuity = set(inherited_vacuity)
                if not is_definition and not _nonvacuity_checked(result["nonvacuity_witness"]):
                    vacuity.add(node_id)
                attestation_state = ("DEFINITION_ELABORATED" if is_definition else
                                     "KERNEL_CHECKED_VACUITY_UNKNOWN" if vacuity else "KERNEL_CHECKED_CANDIDATE")
                state = "AWAITING_REVIEW" if unreviewed else attestation_state
                record = {"evidence": result, "derived_state": state, "kernel_attestation_state": attestation_state,
                          "clause_coverage_status": clause_status,
                          "reservation_id": stored["id"], "environment_hypotheses": result["hypotheses"],
                          "conditional_on": sorted(inherited_premises), "vacuity_unknown_nodes": sorted(vacuity),
                          "unreviewed_blockers": sorted(unreviewed), "decision_policy": policy,
                          "source_alignment_accepted": False, "promotion_allowed": False,
                          "dependency_kind": "ELABORATED_DEFINITION" if is_definition else "FORMAL_IMPLICATION_CANDIDATE"}
                completed[node_id] = available[node_id] = record
                outcomes.append({**base, "state": state, "attempts": number, **record})
                break
            failure = result.get("failure_kind")
            checked_failure = ((node_id, number) in trusted_failures or
                               _advances(result.get("failure_confidence"), registry))
            authorized = checked_failure or exploratory
            if failure not in FAILURE_KINDS or not authorized:
                outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number, "evidence": result,
                                 "reason": "FAILURE_CLASSIFICATION_NOT_CALIBRATED_OR_REVIEWED"})
                break
            if not checked_failure:
                unreviewed.add("unreviewed-failure-classification:" + stored["id"])
            if failure in {"STATEMENT_WRONG", "UNPROVABLE_AS_STATED"} or number == cap:
                premise_context = digest(canonical({"proof_context": context_sha256,
                    "failed_attempt_id": stored["id"], "failed_result": result, "decision_policy": policy}))
                try:
                    premise_stored = _reserved_callback(ledger, node_id, premise_context, "PREMISE",
                        lambda reservation: render_premise(node, result, reservation), reuse=True)
                except RuntimeError as exc:
                    if str(exc) not in {"NODE_PROOF_ATTEMPT_ALREADY_RESERVED", "PLAN_PROOF_ATTEMPT_BUDGET_EXHAUSTED",
                                        "NODE_PREMISE_ATTEMPT_CAP_EXHAUSTED", "MODEL_PROVIDER_CIRCUIT_OPEN"}:
                        raise
                    outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                     "reason": str(exc)})
                    break
                premise = premise_stored["result"]
                if premise_stored["outcome"] != "RETURNED":
                    outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                     "reason": "HOST_PREMISE_CALLBACK_" + premise_stored["outcome"],
                                     "reservation_id": premise_stored["id"], "evidence": premise})
                    break
                if not _checked_premise(premise, node, registry, trusted_premises, exploratory=exploratory):
                    outcomes.append({**base, "state": "AWAITING_REVIEW", "attempts": number,
                                     "reason": "PREMISE_NOT_SOURCE_BOUND_AND_CHECKED", "premise_candidate": premise})
                    break
                if not (node_id in trusted_premises or _advances(premise.get("alignment_confidence"), registry)):
                    unreviewed.add("unreviewed-premise-alignment:" + premise_stored["id"])
                record = {"explicit_premise": premise, "dependency_kind": "EXPLICIT_PROP_PREMISE",
                          "derived_state": "AWAITING_REVIEW" if unreviewed else "CANDIDATE",
                          "reservation_id": premise_stored["id"], "unreviewed_blockers": sorted(unreviewed),
                          "decision_policy": policy, "source_alignment_accepted": False, "promotion_allowed": False,
                          "conditional_on": sorted(inherited_premises | {node_id}),
                          "vacuity_unknown_nodes": sorted(inherited_vacuity | {node_id})}
                premises[node_id] = available[node_id] = record
                outcomes.append({**base, "state": record["derived_state"], "attempts": number,
                                 "reason": RETRY_STRATEGIES[failure], **record})
                break
    return {"completed_candidates": completed, "premise_candidates": premises,
            "available_dependencies": available, "outcomes": outcomes,
            "chain_state": "CHAIN_INCOMPLETE", "integration_status": "NOT_CONNECTED_TO_CASE_RUNNER",
            "decision_policy": policy, "promotion_allowed": False,
            "attempt_accounting": "DURABLE_PLAN_AND_NODE_PROOF_PREMISE_RESERVATIONS; MODEL_CALLS_RESERVED_SEPARATELY"}
