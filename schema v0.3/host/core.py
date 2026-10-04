"""Host-owned identities, receipts, state derivation and durable plan accounting."""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import pathlib
import sqlite3
import time
import uuid

from model_failures import GLOBAL_PROVIDER_FAILURES

VERSION = "0.3.0"
TERMINAL_KINDS = (
    "ARXIV_SOURCE_AVAILABLE", "PREARXIV_DOI_NO_SOURCE", "MONOGRAPH",
    "FOLKLORE_NO_PRIMARY_SOURCE", "FREE_TEXT_UNRESOLVED", "IN_LIBRARY",
)
DERIVED_STATES = (
    "CANDIDATE", "AWAITING_REVIEW", "SOURCE_UNREACHABLE", "SOURCE_READ_DEFECTIVE",
    "ROUTE_UNDETERMINED", "DEFINITION_ELABORATED", "KERNEL_CHECKED_CANDIDATE",
    "KERNEL_CHECKED_VACUITY_UNKNOWN", "CONDITIONAL_ON_BLOCKED_ROOT", "NOT_COMPOSED",
)
MODEL_FORBIDDEN_KEYS = {"state", "derived_state", "disposition", "coverage", "blocked",
                        "blocked_by", "proof_discharged", "statement_discharged", "accepted",
                        "kernel_checked", "all_composed", "nonvacuity_checked", "source_unreachable",
                        "source_read_defective", "cycle", "gate"}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(value)
    # Atomic publication. Run directories are unique; older runs are never overwritten.
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_bytes(raw)
    tmp.replace(path)
    return {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}


def reject_model_state(value):
    if isinstance(value, dict):
        bad = MODEL_FORBIDDEN_KEYS.intersection(value)
        if bad:
            raise ValueError("model attempted host-owned fields: " + ", ".join(sorted(bad)))
        for child in value.values():
            reject_model_state(child)
    elif isinstance(value, list):
        for child in value:
            reject_model_state(child)


def decision_gate(confidence, *, calibration_registry, threshold=0.95):
    """A self-report or an unregistered calibration is never an automatic gate."""
    if confidence.get("source") != "CALIBRATED":
        return "AWAITING_REVIEW"
    ref = confidence.get("calibration_ref")
    curve = calibration_registry.get(ref) if isinstance(ref, str) else None
    if not curve or not curve.get("held_out") or not curve.get("epoch_matches"):
        return "AWAITING_REVIEW"
    value = confidence.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError("confidence must be a number in [0,1]")
    return "ADVANCE_CANDIDATE" if value >= threshold else "AWAITING_REVIEW"


def derive_state(facts):
    """Total conservative host function. Acceptance is a separate, human-owned act."""
    if facts.get("source_unreachable"):
        return "SOURCE_UNREACHABLE"
    if facts.get("source_read_defective"):
        return "SOURCE_READ_DEFECTIVE"
    if facts.get("cycle"):
        return "ROUTE_UNDETERMINED"
    if facts.get("blocked_by"):
        return "CONDITIONAL_ON_BLOCKED_ROOT"
    if not facts.get("kernel_checked"):
        return "AWAITING_REVIEW" if facts.get("needs_review") else "CANDIDATE"
    if facts.get("declaration_kind") == "definition":
        return "DEFINITION_ELABORATED"
    if facts.get("required_edges") and not facts.get("all_composed"):
        return "NOT_COMPOSED"
    if facts.get("hypotheses") and not facts.get("nonvacuity_checked"):
        return "KERNEL_CHECKED_VACUITY_UNKNOWN"
    return "KERNEL_CHECKED_CANDIDATE"


class PlanLedger:
    """SQLite is authoritative; JSON and Cypher are pure projections.

    Monetary calls reserve their upper bound *before* dispatch. Unknown charges
    retain the reservation. Subscription calls use a separate bounded call quota;
    their dollar cost remains null, never a manufactured zero.
    """

    def __init__(self, directory, plan):
        self.directory = pathlib.Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "ledger.sqlite", timeout=30)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY, spec TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(id),
          operation TEXT NOT NULL, state TEXT NOT NULL, reserved INTEGER NOT NULL,
          cost INTEGER, started TEXT NOT NULL, finished TEXT, receipt TEXT);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
          plan_id TEXT NOT NULL REFERENCES plans(id), kind TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS progress(plan_id TEXT NOT NULL, lead TEXT NOT NULL,
          empty_runs INTEGER NOT NULL, PRIMARY KEY(plan_id,lead));
        CREATE TABLE IF NOT EXISTS issues(id TEXT PRIMARY KEY, plan_id TEXT NOT NULL,
          payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS proof_attempts(
          id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(id),
          node_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('PROOF','PREMISE')),
          context_sha256 TEXT NOT NULL, attempt_number INTEGER NOT NULL,
          state TEXT NOT NULL CHECK(state IN ('RESERVED','SETTLED')),
          started TEXT NOT NULL, finished TEXT, outcome TEXT, receipt TEXT, result TEXT,
          UNIQUE(plan_id,node_id,kind,attempt_number));
        CREATE UNIQUE INDEX IF NOT EXISTS one_reserved_proof_attempt_per_node
          ON proof_attempts(plan_id,node_id) WHERE state='RESERVED';
        """)
        encoded = canonical(plan).decode()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT spec FROM plans WHERE id=?", (plan["plan_id"],)).fetchone()
            if old and old[0] != encoded:
                raise ValueError("cannot replace a frozen plan")
            self.db.execute("INSERT OR IGNORE INTO plans VALUES (?,?)", (plan["plan_id"], encoded))
        self.plan = json.loads(encoded)

    def event(self, kind, payload):
        with self.db:
            self.db.execute("INSERT INTO events(plan_id,kind,payload) VALUES (?,?,?)",
                            (self.plan["plan_id"], kind, canonical(payload).decode()))

    def issue(self, code, subject, detail, evidence=None):
        item = {"id": "issue:" + digest(canonical([code, subject, detail])).split(":")[1][:24],
                "code": code, "subject": subject, "detail": detail, "evidence": evidence}
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO issues VALUES (?,?,?)",
                            (item["id"], self.plan["plan_id"], canonical(item).decode()))
        return item

    def reserve(self, operation, upper_cost_microusd=0):
        if type(upper_cost_microusd) is not int or upper_cost_microusd < 0:
            raise ValueError("reservation must be an integer >= 0")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            frozen = self._frozen_plan()
            if self.provider_failure() is not None:
                raise RuntimeError("MODEL_PROVIDER_CIRCUIT_OPEN")
            limits = frozen["limits"]
            count, committed = self.db.execute(
                "SELECT COUNT(*),COALESCE(SUM(COALESCE(cost,reserved)),0) FROM calls WHERE plan_id=?",
                (self.plan["plan_id"],)).fetchone()
            if count >= limits["max_model_calls"]:
                raise RuntimeError("MODEL_CALL_BUDGET_EXHAUSTED")
            if frozen["cost_mode"] == "METERED_USD" and upper_cost_microusd <= 0:
                raise RuntimeError("MISSING_CALL_COST_UPPER_BOUND")
            if committed + upper_cost_microusd > limits["max_cost_microusd"]:
                raise RuntimeError("MONETARY_BUDGET_EXHAUSTED")
            call_id = "call:" + uuid.uuid4().hex
            self.db.execute("INSERT INTO calls VALUES (?,?,?,?,?,?,?,?,?)", (
                call_id, self.plan["plan_id"], operation, "RESERVED", upper_cost_microusd,
                None, utcnow(), None, None))
        return call_id

    def settle(self, call_id, receipt, cost_microusd=None):
        if cost_microusd is not None and (type(cost_microusd) is not int or cost_microusd < 0):
            raise ValueError("invalid observed cost")
        with self.db:
            self._frozen_plan()
            updated = self.db.execute(
                "UPDATE calls SET state=?,cost=?,finished=?,receipt=? WHERE id=? AND plan_id=? AND state='RESERVED'",
                ("RECORDED", cost_microusd, utcnow(), canonical(receipt).decode(), call_id, self.plan["plan_id"]))
            if updated.rowcount != 1:
                raise ValueError("unknown or already settled call")
            if receipt.get("error") in GLOBAL_PROVIDER_FAILURES:
                self.db.execute("INSERT INTO events(plan_id,kind,payload) VALUES (?,?,?)",
                    (self.plan["plan_id"], "ModelProviderCircuitOpened", canonical({
                        "call_id": call_id, "reason": receipt["error"],
                        "scope": "NO_MORE_MODEL_DISPATCH_IN_THIS_PLAN", "automatic_retry": False}).decode()))

    def provider_failure(self):
        """Persistent gate, including restart; successful cached evidence remains reusable."""
        for row in self.db.execute("SELECT receipt FROM calls WHERE plan_id=? AND receipt IS NOT NULL ORDER BY started",
                                   (self.plan["plan_id"],)):
            receipt = json.loads(row[0])
            if receipt.get("error") in GLOBAL_PROVIDER_FAILURES:
                return {"call_id": receipt["call_id"], "reason": receipt["error"]}
        return None

    def _frozen_plan(self):
        """Read authority from the frozen database plan, never mutable callback data."""
        row = self.db.execute("SELECT spec FROM plans WHERE id=?", (self.plan["plan_id"],)).fetchone()
        if row is None or row[0] != canonical(self.plan).decode():
            raise ValueError("in-memory plan does not match the frozen ledger plan")
        return json.loads(row[0])

    def _frozen_proof_limits(self):
        limits = self._frozen_plan()["limits"]
        if type(limits.get("max_proof_attempts")) is not int or limits["max_proof_attempts"] < 1:
            raise RuntimeError("MISSING_PROOF_ATTEMPT_BUDGET")
        if type(limits.get("max_node_attempts")) is not int or limits["max_node_attempts"] < 1:
            raise RuntimeError("MISSING_NODE_PROOF_ATTEMPT_CAP")
        return limits

    def decision_policy(self):
        """Exploration is a frozen plan choice; a candidate cannot enable it."""
        policy = self._frozen_plan().get("decision_policy", "STRICT_CALIBRATED")
        if policy not in {"STRICT_CALIBRATED", "CANDIDATE_EXPLORATION"}:
            raise ValueError("unknown frozen decision policy")
        return policy

    def proof_attempt_limits(self):
        """Proof and premise reservations share one persistent plan-wide quota."""
        limits = self._frozen_proof_limits()
        return {"max_proof_attempts": limits["max_proof_attempts"],
                "max_node_attempts": limits["max_node_attempts"],
                "max_node_premise_attempts": 1,
                "scope": "ALL_PROOF_AND_PREMISE_RESERVATIONS_IN_FROZEN_PLAN"}

    def reserve_proof_attempt(self, node_id, context_sha256, *, kind="PROOF"):
        """Reserve before dispatch; crashes, failures and retries never refund quota.

        PROOF is capped per node by max_node_attempts. PREMISE has one rendering
        reservation per node. Both consume max_proof_attempts. At most one worker
        may own a RESERVED attempt for a node, including across context changes.
        This reserves attempt slots only; model calls still use reserve()/settle().
        """
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("proof node_id must be a nonempty string")
        if (not isinstance(context_sha256, str) or not context_sha256.startswith("sha256:")
                or len(context_sha256) != 71
                or any(char not in "0123456789abcdef" for char in context_sha256[7:])):
            raise ValueError("proof context must be a canonical sha256 digest")
        if kind not in {"PROOF", "PREMISE"}:
            raise ValueError("unknown proof-attempt kind")
        pid = self.plan["plan_id"]
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            limits = self._frozen_proof_limits()
            if self.provider_failure() is not None:
                raise RuntimeError("MODEL_PROVIDER_CIRCUIT_OPEN")
            running = self.db.execute(
                "SELECT id FROM proof_attempts WHERE plan_id=? AND node_id=? AND state='RESERVED'",
                (pid, node_id)).fetchone()
            if running:
                raise RuntimeError("NODE_PROOF_ATTEMPT_ALREADY_RESERVED")
            total = self.db.execute("SELECT COUNT(*) FROM proof_attempts WHERE plan_id=?", (pid,)).fetchone()[0]
            if total >= limits["max_proof_attempts"]:
                raise RuntimeError("PLAN_PROOF_ATTEMPT_BUDGET_EXHAUSTED")
            count = self.db.execute("SELECT COUNT(*) FROM proof_attempts WHERE plan_id=? AND node_id=? AND kind=?",
                                    (pid, node_id, kind)).fetchone()[0]
            cap = limits["max_node_attempts"] if kind == "PROOF" else 1
            if count >= cap:
                raise RuntimeError("NODE_PROOF_ATTEMPT_CAP_EXHAUSTED" if kind == "PROOF" else "NODE_PREMISE_ATTEMPT_CAP_EXHAUSTED")
            reservation = {"id": "proof-attempt:" + uuid.uuid4().hex, "plan_id": pid,
                           "node_id": node_id, "kind": kind, "context_sha256": context_sha256,
                           "attempt_number": count + 1, "started_at": utcnow()}
            self.db.execute("""INSERT INTO proof_attempts
                (id,plan_id,node_id,kind,context_sha256,attempt_number,state,started)
                VALUES (?,?,?,?,?,?,'RESERVED',?)""",
                (reservation["id"], pid, node_id, kind, context_sha256, count + 1, reservation["started_at"]))
            self.db.execute("INSERT INTO events(plan_id,kind,payload) VALUES (?,?,?)",
                            (pid, "ProofAttemptReserved", canonical(reservation).decode()))
        return reservation

    def settle_proof_attempt(self, reservation, receipt, *, result=None, outcome="RETURNED"):
        """Persist immutable host callback evidence, including failed/time-out runs.

        RETURNED says a callback returned data, not that a proof succeeded.
        INTERRUPTED is for a trusted controller after the worker is confirmed
        stopped. Stale, cross-plan and duplicate settlements are refused. An
        unobserved crash remains RESERVED until explicit host recovery; it keeps
        both its slot and its per-node exclusion lock and can never silently retry.
        """
        if outcome not in {"RETURNED", "FAILED", "TIMED_OUT", "INTERRUPTED"}:
            raise ValueError("unknown proof-attempt outcome")
        if not isinstance(reservation, dict) or not isinstance(receipt, dict):
            raise ValueError("proof settlement requires host reservation and receipt objects")
        pid = self.plan["plan_id"]
        if reservation.get("plan_id") != pid:
            raise ValueError("proof reservation belongs to another plan")
        result_raw, receipt_raw = canonical(result), canonical(receipt)
        expected_operation = "scheduler.proof_attempt" if reservation.get("kind") == "PROOF" else "scheduler.premise_attempt"
        if (receipt.get("kind") != "ProgramReceipt" or receipt.get("engine_class") != "HOST"
                or receipt.get("operation") != expected_operation
                or receipt.get("input_sha256") != reservation.get("context_sha256")
                or receipt.get("output_sha256") != digest(result_raw)
                or receipt.get("outcome") != ("RECORDED" if outcome == "RETURNED" else "FAILED")):
            raise ValueError("proof receipt does not bind this reservation and exact result")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            self._frozen_proof_limits()
            updated = self.db.execute("""UPDATE proof_attempts SET state='SETTLED',finished=?,outcome=?,receipt=?,result=?
                WHERE id=? AND plan_id=? AND node_id=? AND kind=? AND context_sha256=?
                  AND attempt_number=? AND state='RESERVED'""",
                (utcnow(), outcome, receipt_raw.decode(), result_raw.decode(), reservation.get("id"), pid,
                 reservation.get("node_id"), reservation.get("kind"), reservation.get("context_sha256"),
                 reservation.get("attempt_number")))
            if updated.rowcount != 1:
                raise ValueError("unknown, stale, or already settled proof attempt")
            self.db.execute("INSERT INTO events(plan_id,kind,payload) VALUES (?,?,?)",
                            (pid, "ProofAttemptSettled", canonical({"reservation": reservation, "outcome": outcome,
                              "receipt_sha256": digest(receipt_raw), "result_sha256": digest(result_raw)}).decode()))

    def proof_attempt_history(self, node_id=None, *, context_sha256=None, kind=None):
        """Read immutable evidence for resumption; consumers must reapply their gates."""
        query = "SELECT id,node_id,kind,context_sha256,attempt_number,state,started,finished,outcome,receipt,result FROM proof_attempts WHERE plan_id=?"
        args = [self.plan["plan_id"]]
        for field, value in (("node_id", node_id), ("context_sha256", context_sha256), ("kind", kind)):
            if value is not None:
                query += " AND " + field + "=?"
                args.append(value)
        rows = self.db.execute(query + " ORDER BY node_id,kind,attempt_number", args).fetchall()
        return [{"id": row[0], "plan_id": self.plan["plan_id"], "node_id": row[1], "kind": row[2],
                 "context_sha256": row[3], "attempt_number": row[4], "state": row[5],
                 "started_at": row[6], "finished_at": row[7], "outcome": row[8],
                 "receipt": json.loads(row[9]) if row[9] else None,
                 "result": json.loads(row[10]) if row[10] else None} for row in rows]

    def progress(self, lead, new_items):
        if not isinstance(lead, str) or not lead.strip() or type(new_items) is not int or new_items < 0:
            raise ValueError("progress requires a nonempty stable lead and a nonnegative integer item count")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            limit = self._frozen_plan()["limits"]["no_progress_limit"]
            row = self.db.execute("SELECT empty_runs FROM progress WHERE plan_id=? AND lead=?",
                                  (self.plan["plan_id"], lead)).fetchone()
            n = 0 if new_items > 0 else (row[0] if row else 0) + 1
            self.db.execute("INSERT OR REPLACE INTO progress VALUES (?,?,?)", (self.plan["plan_id"], lead, n))
        return n < limit

    @contextlib.contextmanager
    def stage(self, operation, inputs):
        started, tick = utcnow(), time.monotonic()
        output = {}
        try:
            yield output
        except BaseException as exc:
            output.update(outcome="FAILED", error={"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            receipt = {"kind": "ProgramReceipt", "contract_version": VERSION,
                       "program": "agtxiv.research.host/0.3.0", "operation": operation,
                       "engine_class": "HOST", "call": None, "input_sha256": digest(canonical(inputs)),
                       "output_sha256": digest(canonical(output)), "started_at": started,
                       "finished_at": utcnow(), "elapsed_seconds": round(time.monotonic()-tick, 6),
                       "outcome": output.get("outcome", "RECORDED")}
            self.event("ProgramReceipt", receipt)

    def snapshot(self):
        pid = self.plan["plan_id"]
        calls = self.db.execute("SELECT id,state,reserved,cost,receipt FROM calls WHERE plan_id=? ORDER BY started,id", (pid,)).fetchall()
        return {"kind": "PlanLedger", "contract_version": VERSION, "plan": self.plan,
                "proof_attempts": self.proof_attempt_history(),
                "calls": [{"id": x[0], "state": x[1], "reserved_microusd": x[2],
                           "actual_cost_microusd": x[3], "receipt": json.loads(x[4]) if x[4] else None} for x in calls],
                "cost": {"mode": self.plan["cost_mode"], "known_microusd": sum(x[3] or 0 for x in calls),
                         "unknown_cost_calls": sum(x[3] is None for x in calls),
                         "unsettled_reserve_microusd": sum(x[2] for x in calls if x[3] is None)},
                "events": [{"sequence": x[0], "kind": x[1], "payload": json.loads(x[2])} for x in self.db.execute(
                    "SELECT seq,kind,payload FROM events WHERE plan_id=? ORDER BY seq", (pid,))],
                "issues": [json.loads(x[0]) for x in self.db.execute("SELECT payload FROM issues WHERE plan_id=? ORDER BY id", (pid,))]}
