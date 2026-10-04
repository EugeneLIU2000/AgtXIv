"""Read-only integrity audit of one recorded model/Lean proof walk.

This does not execute the recorded runtime, invoke a model, run Lean, rebuild
historical libraries, or accept a mathematical statement. The large frozen
base-object inventory is checked as a referenced manifest, not rehashed in full.
"""
from __future__ import annotations

import argparse
from image_evidence import image_evidence_issues
from pdf_proof_context import bound_pdf_proof_context, pdf_source_binding
from premise_evidence import bind_premise_report
from clause_evidence import bind_clause_report, clause_binding_coverage
from clause_coverage import candidate_clause_status
from certify import certificate
from review import load_reviews
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3


ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
COMPANIONS = (".olean", ".olean.private", ".olean.server", ".ir", ".ir.sig")
# Frozen like the source templates below, so recorded probes keep auditing if proof_backend's list changes.
TRIVIALITY_TACTICS = ("trivial", "rfl", "decide", "simp", "norm_num")


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


class Auditor:
    def __init__(self, run):
        self.run = Path(run).resolve()
        self.issues, self.references, self.notes = [], {}, []
        schema_path = Path(__file__).resolve().parents[1] / "schemas/research.schema.json"
        self.schema = self.read(schema_path)
        self.model_payloads, self.models, self.sources = {}, {}, {}
        self.lean_receipts, self.checked_attempts, self.explicit_prop_edges = set(), [], 0

    def require(self, condition, code, subject=None, detail=None):
        if not condition:
            self.issues.append({"code": code, "subject": subject, "detail": detail})
        return bool(condition)

    def file(self, path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        ref = {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}
        previous = self.references.get(str(path))
        self.require(previous is None or previous == ref, "FILE_CHANGED_DURING_AUDIT", str(path))
        self.references[str(path)] = ref
        return raw

    def read(self, path):
        return _json(self.file(path))

    def ref(self, ref, *, as_json=False):
        raw = self.file(ref["path"])
        self.require(ref.get("sha256") == digest(raw) and ref.get("byte_size") == len(raw),
                     "REFERENCED_BYTES_MISMATCH", ref.get("path"))
        return _json(raw) if as_json else raw

    def validate(self, value, kind, subject):
        from jsonschema import Draft202012Validator
        validator = Draft202012Validator({"$defs": self.schema["$defs"], "$ref": "#/$defs/" + kind})
        for error in validator.iter_errors(value):
            self.require(False, "SCHEMA_MISMATCH", subject,
                         {"kind": kind, "path": list(error.absolute_path), "message": error.message})

    def unreviewed(self, value, subject):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"accepted", "source_alignment_accepted", "promotion_allowed",
                           "proof_discharged", "statement_discharged"}:
                    self.require(child is not True, "UNREVIEWED_EVIDENCE_PROMOTED", subject, key)
                if key == "chain_state":
                    self.require(child == "CHAIN_INCOMPLETE", "CHAIN_STATE_PROMOTED", subject)
                self.unreviewed(child, subject)
        elif isinstance(value, list):
            for child in value:
                self.unreviewed(child, subject)

    def sqlite_projection(self, plan, ledger):
        path = self.run / "ledger.sqlite"
        # Never instantiate PlanLedger: even its constructor creates tables.
        db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            plans = list(db.execute("SELECT id,spec FROM plans"))
            self.require(len(plans) == 1 and plans[0]["id"] == plan["plan_id"] and
                         _json(plans[0]["spec"]) == plan == ledger["plan"], "SQLITE_FROZEN_PLAN_MISMATCH")
            pid = plan["plan_id"]
            calls = [dict(row) for row in db.execute("SELECT * FROM calls ORDER BY started,id")]
            proofs = [dict(row) for row in db.execute("SELECT * FROM proof_attempts ORDER BY node_id,kind,attempt_number")]
            events = [{"sequence": row[0], "kind": row[1], "payload": _json(row[2])}
                      for row in db.execute("SELECT seq,kind,payload FROM events WHERE plan_id=? ORDER BY seq", (pid,))]
            issues = [_json(row[0]) for row in db.execute("SELECT payload FROM issues WHERE plan_id=? ORDER BY id", (pid,))]
        finally:
            db.close()
        self.require(all(row["plan_id"] == pid for row in calls + proofs), "CROSS_PLAN_RESERVATION")
        call_projection = [{"id": row["id"], "state": row["state"], "reserved_microusd": row["reserved"],
                            "actual_cost_microusd": row["cost"],
                            "receipt": _json(row["receipt"]) if row["receipt"] else None} for row in calls]
        proof_projection = [{"id": row["id"], "plan_id": pid, "node_id": row["node_id"], "kind": row["kind"],
                             "context_sha256": row["context_sha256"], "attempt_number": row["attempt_number"],
                             "state": row["state"], "started_at": row["started"], "finished_at": row["finished"],
                             "outcome": row["outcome"], "receipt": _json(row["receipt"]) if row["receipt"] else None,
                             "result": _json(row["result"]) if row["result"] else None} for row in proofs]
        cost = {"mode": plan["cost_mode"], "known_microusd": sum(row["cost"] or 0 for row in calls),
                "unknown_cost_calls": sum(row["cost"] is None for row in calls),
                "unsettled_reserve_microusd": sum(row["reserved"] for row in calls if row["cost"] is None)}
        for key, expected in (("calls", call_projection), ("proof_attempts", proof_projection),
                              ("events", events), ("issues", issues), ("cost", cost)):
            self.require(ledger.get(key) == expected, "SQLITE_PROJECTION_MISMATCH", key)
        limits = plan["limits"]
        self.require(len(calls) <= limits["max_model_calls"], "MODEL_CALL_QUOTA_EXCEEDED")
        self.require(len(proofs) <= limits["max_proof_attempts"], "PROOF_AND_PREMISE_QUOTA_EXCEEDED")
        self.require(all(row["state"] == "RECORDED" for row in calls), "LIVE_MODEL_RESERVATION_REMAINS")
        self.require(all(row["state"] == "SETTLED" for row in proofs), "LIVE_PROOF_RESERVATION_REMAINS")
        self.require(sum(row["cost"] if row["cost"] is not None else row["reserved"] for row in calls)
                     <= limits["max_cost_microusd"], "MONETARY_QUOTA_EXCEEDED")
        if plan["cost_mode"] == "ACCOUNT_QUOTA":
            self.require(all(row["cost"] is None and row["reserved"] == 0 for row in calls),
                         "ACCOUNT_QUOTA_MISREPRESENTED_AS_OBSERVED_DOLLAR_COST")
        for node in {row["node_id"] for row in proofs}:
            for kind, cap in (("PROOF", limits["max_node_attempts"]), ("PREMISE", 1)):
                rows = [row for row in proofs if row["node_id"] == node and row["kind"] == kind]
                self.require(len(rows) <= cap and [row["attempt_number"] for row in rows] == list(range(1, len(rows)+1)),
                             "NODE_RESERVATION_CAP_OR_SEQUENCE_MISMATCH", [node, kind])
        for attempt in proof_projection:
            ident = attempt["id"]
            reservation = {key: attempt[key] for key in
                           ("id", "plan_id", "node_id", "kind", "context_sha256", "attempt_number", "started_at")}
            reserved = [event for event in events if event["kind"] == "ProofAttemptReserved" and event["payload"].get("id") == ident]
            settled = [event for event in events if event["kind"] == "ProofAttemptSettled" and
                       event["payload"].get("reservation", {}).get("id") == ident]
            self.require(len(reserved) == len(settled) == 1, "PROOF_RESERVATION_EVENT_CARDINALITY", ident)
            if reserved and settled:
                expected = {"reservation": reservation, "outcome": attempt["outcome"],
                            "receipt_sha256": digest(canonical(attempt["receipt"])),
                            "result_sha256": digest(canonical(attempt["result"]))}
                self.require(reserved[0]["payload"] == reservation and settled[0]["payload"] == expected and
                             reserved[0]["sequence"] < settled[0]["sequence"], "PROOF_RESERVATION_EVENT_MISMATCH", ident)
            receipt = attempt["receipt"]
            if receipt is not None:
                self.validate(receipt, "ProgramReceipt", ident)
                self.require(receipt["operation"] == ("scheduler.proof_attempt" if attempt["kind"] == "PROOF" else "scheduler.premise_attempt")
                             and receipt["input_sha256"] == attempt["context_sha256"]
                             and receipt["output_sha256"] == digest(canonical(attempt["result"]))
                             and receipt["outcome"] == ("RECORDED" if attempt["outcome"] == "RETURNED" else "FAILED"),
                             "PROOF_WRAPPER_RECEIPT_MISMATCH", ident)
        known = {row["id"] for row in proofs}
        for event in events:
            if event["kind"] in {"ProofAttemptReserved", "ProofAttemptSettled"}:
                ident = event["payload"].get("id") if event["kind"] == "ProofAttemptReserved" else event["payload"].get("reservation", {}).get("id")
                self.require(ident in known, "ORPHAN_PROOF_EVENT", ident)
            if event["kind"] == "ProgramReceipt":
                self.validate(event["payload"], "ProgramReceipt", "event:" + str(event["sequence"]))
        return calls, proof_projection

    def model_call(self, call, plan):
        from model_routing import routing_evidence_issues
        receipt = _json(call["receipt"]) if call["receipt"] else None
        if receipt is None:
            return
        ident, directory = call["id"], Path(receipt["directory"]).resolve()
        self.require(directory.is_relative_to(self.run / "attempts"), "MODEL_DIRECTORY_OUTSIDE_PROOF_RUN", ident)
        self.require(directory.name == ident.replace(":", "-") and call["started"] <= receipt["started_at"]
                     <= receipt["finished_at"] <= call["finished"], "MODEL_RESERVATION_TIME_OR_DIRECTORY_MISMATCH", ident)
        self.require(self.read(directory / "receipt.json") == receipt, "MODEL_RECEIPT_PROJECTION_MISMATCH", ident)
        task = self.read(directory / "task.json")
        self.issues.extend({**issue, "call_id": ident} for issue in image_evidence_issues(task, receipt, directory))
        self.validate(task, "Task", ident)
        self.issues.extend({**issue, "call_id": ident} for issue in routing_evidence_issues(plan, task, receipt))
        prompt, events = self.file(directory / "prompt.txt"), self.file(directory / "events.jsonl")
        if "input_character_count" in task:
            self.require(task["input_character_count"] == len(prompt.decode("utf-8"))
                         and task["input_character_count"] <= task["max_input_characters"] == 1048576,
                         "MODEL_PROMPT_CHARACTER_LIMIT_MISMATCH", ident)
        self.file(directory / "stderr.txt")
        schema_raw = self.file(directory / "response.schema.json")
        response_path = directory / "response.json"
        response = self.file(response_path) if response_path.is_file() else None
        self.require(receipt.get("kind") == "ModelReceipt" and receipt.get("contract_version") == "0.3.0"
                     and receipt.get("call_id") == ident and receipt.get("operation") == call["operation"],
                     "MODEL_RECEIPT_IDENTITY_MISMATCH", ident)
        self.require(receipt.get("request_sha256") == task.get("prompt_sha256") == digest(prompt)
                     and receipt.get("events_sha256") == digest(events)
                     and receipt.get("response_sha256") == (digest(response) if response is not None else None),
                     "MODEL_RAW_ARTIFACT_HASH_MISMATCH", ident)
        self.require(task.get("schema_sha256") == digest(schema_raw) and task["task_id"] == ident
                     and task["plan_id"] == plan["plan_id"] and task["operation"] == call["operation"]
                     and task["engine_class"] == receipt["engine_class"]
                     and task["actual_model_requested"] == receipt["actual_model_requested"]
                     and task["max_seconds"] == plan["limits"]["max_call_seconds"]
                     and task["input_byte_size"] == len(prompt) + len(schema_raw)
                     and task["input_byte_size"] <= task["max_input_bytes"], "MODEL_TASK_BINDING_MISMATCH", ident)
        self.require(receipt.get("model_identity_attested_by_provider") is False
                     and receipt.get("cost_microusd") is None, "MODEL_UNOBSERVED_FACT_PROMOTED", ident)
        parsed_events, malformed = [], []
        for number, line in enumerate(events.splitlines(), 1):
            if not line.strip():
                continue
            try:
                parsed_events.append(_json(line))
            except (ValueError, UnicodeError) as error:
                malformed.append({"line": number, "error": str(error)})
        tools = [event for event in parsed_events if event.get("item", {}).get("type") in
                 {"command_execution", "mcp_tool_call", "web_search", "file_change"}]
        self.require(tools == receipt.get("unexpected_tool_events", []), "MODEL_TOOL_EVENT_PROJECTION_MISMATCH", ident)
        completed = [event for event in parsed_events if event.get("type") == "turn.completed"]
        candidate = None
        if receipt.get("outcome") == "CANDIDATE_RECORDED":
            self.require(receipt.get("returncode") == 0 and receipt.get("error") is None and not tools
                         and not malformed and len(completed) == 1 and not receipt.get("validation_issues"),
                         "MODEL_CANDIDATE_NOT_SUPPORTED_BY_EVENTS", ident)
            self.require(completed and completed[-1].get("usage") == receipt.get("usage"), "MODEL_USAGE_EVENT_MISMATCH", ident)
            candidate = _json(response) if response is not None else None
            from jsonschema import Draft202012Validator
            for error in Draft202012Validator(_json(schema_raw)).iter_errors(candidate):
                self.require(False, "MODEL_RESPONSE_SCHEMA_MISMATCH", ident, error.message)
            self.require(all(event.get("item", {}).get("type") in {None, "reasoning", "agent_message"}
                             for event in parsed_events), "SOURCE_ONLY_MODEL_UNKNOWN_ITEM_TYPE", ident)
        text = prompt.decode("utf-8")
        marker = r'\{\s*"node"\s*:' if call["operation"] != "autoformalization.failure_classify" else r'\{\s*"candidate"\s*:'
        match = re.search(marker, text)
        self.require(match is not None, "MODEL_OPERATION_PAYLOAD_ABSENT", ident)
        payload = _json(text[match.start():]) if match else None
        self.model_payloads[ident] = payload
        self.models[ident] = {"receipt": receipt, "candidate": candidate, "directory": str(directory),
                              "task": task, "response_schema": _json(schema_raw)}

    def source_paper(self, paper_id, entry):
        if "pdf_run" in entry:
            summary, assembly = pdf_source_binding(paper_id, entry)
            self.ref(entry["pdf_run"], as_json=True)
            self.ref(summary["assembly"], as_json=True)
            self.ref(summary["document"], as_json=True)
            self.sources[paper_id] = {"pdf_entry": entry}
            return
        paper = self.ref(entry["extraction"], as_json=True)
        self.require(paper["paper"]["id"] == paper_id, "SOURCE_PAPER_ID_MISMATCH", paper_id)
        directory, files, payload = Path(entry["directory"]).resolve(), {}, []
        for row in paper["source_files"]:
            self.require(row["path"] not in files and row["blob_path"] == "sources/" + row["sha256"].removeprefix("sha256:"),
                         "SOURCE_MANIFEST_IDENTITY_MISMATCH", [paper_id, row["path"]])
            path = (directory / row["blob_path"]).resolve()
            self.require(path.is_relative_to(directory), "SOURCE_BLOB_PATH_ESCAPE", str(path))
            raw = self.file(path)
            self.require(digest(raw) == row["sha256"] and len(raw) == row["byte_size"], "FROZEN_SOURCE_BYTES_MISMATCH", str(path))
            files[row["path"]] = raw
            payload.append({"path": row["path"], "sha256": digest(raw), "byte_size": len(raw),
                            "encoding": "UTF-8", "text": raw.decode("utf-8")})
        self.sources[paper_id] = {"files": files, "payload": payload, "paper": paper}
        for key in ("claims", "anchors", "bibliography", "macro_table"):
            for row in paper.get(key, []):
                self.span(paper_id, row["source"], row.get("text") if key in {"claims", "bibliography"} else None)
                for span in row.get("proof_sources", []):
                    self.span(paper_id, span)
        for span in paper.get("proof_spans", []):
            self.span(paper_id, span)

    def span(self, paper_id, span, text=None):
        raw = self.sources[paper_id]["files"].get(span["path"])
        start, end = span["byte_start"], span["byte_end"]
        if self.require(raw is not None and type(start) is int and type(end) is int and 0 <= start < end <= len(raw),
                        "SOURCE_SPAN_UNBOUND", [paper_id, span]):
            self.require(digest(raw) == span["sha256"] and digest(raw[start:end]) == span["span_sha256"],
                         "SOURCE_SPAN_HASH_MISMATCH", [paper_id, span["path"]])
            if text is not None:
                self.require(raw[start:end].decode("utf-8") == text, "SOURCE_QUOTATION_MISMATCH", paper_id)

    def lean_receipt(self, receipt, environment):
        self.validate(receipt, "ProgramReceipt", receipt.get("log"))
        command = receipt["command"]
        source, directory = Path(command[-1]).resolve(), Path(receipt["cwd"]).resolve()
        raw, log = self.file(source), self.file(receipt["log"])
        self.require(source.parent == directory and receipt["input_sha256"] == digest(raw)
                     and receipt["output_sha256"] == digest(log), "LEAN_RECEIPT_BYTES_MISMATCH", str(source))
        self.require(command[0] == "/usr/bin/sandbox-exec" and command[1] == "-f"
                     and str(Path(command[3]).resolve()) == str(Path(environment["executable"]).resolve()),
                     "LEAN_RECEIPT_EXECUTABLE_MISMATCH", str(source))
        execution = receipt["execution_context"]
        profile = self.ref(execution["sandbox_profile"]).decode()
        self.require(str(Path(command[2]).resolve()) == execution["sandbox_profile"]["path"]
                     and execution.get("network_allowed") is False
                     and execution.get("dependency_builds_requested") is False
                     and execution.get("source_unchanged") is True, "LEAN_ISOLATION_RECEIPT_MISMATCH", str(source))
        expected_profile = ('(version 1) (deny default) (allow file-read*) (allow sysctl-read) '
                            '(allow mach-lookup) (allow process-info*) '
                            '(allow process-exec (literal ' + json.dumps(str(Path(environment["executable"]).resolve())) + ')) '
                            '(allow file-write* (subpath ' + json.dumps(str(directory / "compiled")) + ') '
                            '(subpath ' + json.dumps(str(directory / "tmp")) + '))\n')
        self.require(profile == expected_profile, "LEAN_SANDBOX_PROFILE_MISMATCH", str(source))
        self.require(receipt["status"] == "SUCCEEDED" if receipt["outcome"] == "RECORDED" else receipt["status"] != "SUCCEEDED",
                     "LEAN_STATUS_OUTCOME_MISMATCH", str(source))
        if receipt["status"] == "SUCCEEDED":
            self.require(receipt["exit_code"] == 0 and not receipt.get("error"), "LEAN_SUCCESS_WITH_ERROR", str(source))
        self.require(self.read(directory / "lean-receipt.json") == receipt, "LEAN_RECEIPT_DISK_MISMATCH", str(source))
        self.lean_receipts.add(str(directory / "lean-receipt.json"))
        rows, premises = [], []
        for line in log.decode("utf-8", errors="replace").splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                row = _json(line.removeprefix("AGTXIV_AUDIT_JSON "))
                row["forbidden_axioms"] = sorted(set(row["axioms"]) - ALLOWED_AXIOMS)
                row["kernel_checked"] = receipt["status"] == "SUCCEEDED" and not row["forbidden_axioms"]
                row["environment_sha256"] = environment["environment_sha256"]
                rows.append(row)
            if line.startswith("AGTXIV_USED_PREMISES_JSON "):
                premises.append(_json(line.removeprefix("AGTXIV_USED_PREMISES_JSON ")))
        return rows, premises, raw, log.decode("utf-8", errors="replace")

    def triviality(self, result, declaration, module, environment, directory):
        """Rebuild proof_backend.statement_triviality's source and recompute its flag from the hash-checked log."""
        probe = result.get("statement_triviality") or {}
        if not self.require("statement_trivially_provable" in result and "lean_source" in probe and
                            isinstance(probe.get("program_receipt"), dict), "TRIVIALITY_PROBE_INCOMPLETE", str(directory)):
            return
        probes = {declaration + "_trivial_" + str(number): tactic for number, tactic in enumerate(TRIVIALITY_TACTICS)}
        expected = ("import AgtXIvProofRuntime\n" + "".join("import " + name + "\n" for name in
            dict.fromkeys(environment["imports"] + [module])) + "open scoped BigOperators\n" +
            "".join("set_option maxHeartbeats 20000 in\ntheorem " + name + " : type_of% @" + declaration +
                    " := by\n  intros; " + tactic + "\n#agtxiv_audit " + name + "\n" for name, tactic in probes.items()))
        receipt = probe["program_receipt"]
        rows, _, raw, _ = self.lean_receipt(receipt, environment)
        axioms = {row["declaration"]: row["axioms"] for row in rows if row["declaration"] in probes}
        flag = (True if any("sorryAx" not in value for value in axioms.values()) else
                False if len(axioms) == len(probes) else None)
        self.require(raw.decode() == expected and self.ref(probe["lean_source"]) == raw
                     and receipt["operation"] == "lean.statement_triviality"
                     and Path(receipt["cwd"]).resolve() == directory / "triviality"
                     and receipt["execution_context"]["lean_path"] == result["program_receipt"]["execution_context"]["lean_path"]
                     and result["statement_trivially_provable"] is flag, "TRIVIALITY_PROBE_NOT_SUPPORTED_BY_LOG", str(directory))

    def environment(self, ref):
        environment = self.ref(ref, as_json=True)
        initial = {key: value for key, value in environment.items() if key not in
                   {"environment_sha256", "runtime_object", "runtime_artifacts", "library_records", "library_receipt"}}
        self.require(digest(canonical(initial)) == environment["environment_sha256"], "ENVIRONMENT_IDENTITY_HASH_MISMATCH")
        inventory = self.ref(environment["base_object_inventory"], as_json=True)
        self.require(len({row["path"] for row in inventory}) == len(inventory), "BASE_INVENTORY_DUPLICATE_PATH")
        self.notes.append({"code": "BASE_OBJECT_BYTES_NOT_REHASHED", "object_count": len(inventory),
                           "recorded_byte_size": sum(row["byte_size"] for row in inventory),
                           "scope": "Inventory manifest hash verified; historical 8.6 GB library bytes and builds not independently revalidated."})
        self.ref(environment["executable_artifact"])
        for artifact in environment["runtime_sources"] + environment["runtime_artifacts"] + [environment["runtime_object"]]:
            self.ref(artifact)
        runtime_directory = Path(ref["path"]).resolve().parent
        runtime_receipt = self.read(runtime_directory / "lean-receipt.json")
        _, _, runtime_raw, _ = self.lean_receipt(runtime_receipt, environment)
        bodies = ["\n".join(line for line in self.ref(item).decode().splitlines() if not line.startswith("import "))
                  for item in environment["runtime_sources"]]
        self.require(runtime_receipt["status"] == "SUCCEEDED" and runtime_raw.decode() == "import Lean\n" + "\n".join(bodies),
                     "TRUSTED_PROOF_RUNTIME_SOURCE_OR_COMPILATION_MISMATCH")
        receipt = self.ref(environment["library_receipt"], as_json=True)
        records = self.ref(environment["library_records"], as_json=True)
        actual, _, source_raw, _ = self.lean_receipt(receipt, environment)
        expected_source = ("import AgtXIvProofRuntime\n" + "\n".join("import " + name for name in environment["imports"]) +
                           "\n" + "\n".join("#agtxiv_audit " + name for name in environment["requested_declarations"]))
        self.require(source_raw.decode() == expected_source and receipt["operation"] == "lean.proof_library_audit"
                     and receipt["execution_context"]["lean_path"] == environment["lean_path"],
                     "LIBRARY_AUDIT_REQUEST_BINDING_MISMATCH")
        self.require(records == actual and len({row["declaration"] for row in actual}) == len(actual)
                     and {row["declaration"] for row in actual} == set(environment["requested_declarations"])
                     and all(row["kernel_checked"] for row in actual), "LIBRARY_AUDIT_NOT_SUPPORTED_BY_LOG")
        return environment, records, receipt

    def graph(self, request, graph, library, receipt, plan):
        original = self.ref(request["graph"], as_json=True)
        expected = copy.deepcopy(original)
        roots = {row["id"] for row in original["roots"]}
        bindings = request.get("candidate_root_bindings", {})
        lookup = {row["declaration"]: row for row in library}
        self.require(set(bindings) <= roots, "CANDIDATE_LIBRARY_BINDING_IS_NOT_ROOT")
        self.require(not any("root_audit" in node for node in original["nodes"]), "INPUT_GRAPH_CARRIES_ROOT_AUDIT")
        searched = self.ref(request["root_audits"], as_json=True) if "root_audits" in request else None
        audits = searched["root_audits"] if searched else {}
        self.require(not searched or (searched["environment_sha256"], searched["graph"]["sha256"]) ==
                     (plan["environment"]["lean_environment_sha256"], request["graph"]["sha256"])
                     and set(audits) <= roots - set(bindings), "ROOT_AUDITS_NOT_BOUND_TO_GRAPH_ROOTS_AND_ENVIRONMENT")
        for node in expected["nodes"]:
            name = bindings.get(node["id"])
            if name is not None:
                self.require(name in lookup and lookup[name]["kernel_checked"], "ROOT_LIBRARY_DECLARATION_NOT_AUDITED", name)
                node["root_audit"] = {"status": "LIBRARY_BOUND", "program_receipt": receipt,
                    "library_binding": {"library": "PINNED_COMMON_MATHLIB_PHYSLIB_AND_LOCAL_CASE_MODULES",
                        "revision": plan["environment"]["lean_environment_sha256"], "declaration": name},
                    "alignment": "CANDIDATE_SOURCE_BINDING_UNREVIEWED", "source_alignment_accepted": False}
                tag, blocker = "unreviewed-root-binding:", "CANDIDATE_ROOT_BINDING_REVIEW_REQUIRED"
            elif node["id"] in audits:
                self.validate(audits[node["id"]], "RootAudit", node["id"])
                node["root_audit"] = audits[node["id"]]
                tag, blocker = "unreviewed-root-search:", "CANDIDATE_ROOT_SEARCH_REVIEW_REQUIRED"
            else:
                continue
            node["unreviewed_blockers"] = sorted(set(node.get("unreviewed_blockers", [])) | {tag + node["id"]})
            if plan["decision_policy"] != "CANDIDATE_EXPLORATION":
                node["blocked_by"] = sorted(set(node.get("blocked_by", [])) | {blocker})
        self.require(expected == graph, "GRAPH_CHANGED_BEYOND_CANDIDATE_ROOT_ANNOTATIONS")
        self.require(graph["query_ids"] == plan["query_ids"], "QUERY_SCOPE_CHANGED")
        nodes = {node["id"]: node for node in graph["nodes"]}
        groups = {row["id"]: row for row in graph["support_groups"]}
        self.require(len(nodes) == len(graph["nodes"]) and len(groups) == len(graph["support_groups"]), "DUPLICATE_GRAPH_ID")
        for row in groups.values():
            self.validate(row, "SupportGroup", row["id"])
            self.require({row["target"], *row["members"]} <= set(nodes), "DANGLING_GRAPH_SUPPORT", row["id"])
        selected = request.get("selected_group_ids")
        self.require(selected is None or set(selected) <= set(groups), "UNKNOWN_SELECTED_SUPPORT_GROUP")
        by_target = {node: [row for row in groups.values() if row["target"] == node and
                            (selected is None or row["id"] in selected)] for node in nodes}
        active, pending = set(graph["query_ids"]), list(graph["query_ids"])
        while pending:
            for group in by_target[pending.pop()]:
                for member in group["members"]:
                    if member not in active:
                        active.add(member)
                        pending.append(member)
        return nodes, by_target, active

    def attempt(self, row, plan, environment, library, nodes, by_target, active, all_attempts):
        ident, node_id = row["id"], row["node_id"]
        directory = self.run / "attempts" / ident.replace(":", "-")
        self.require(node_id in active, "ATTEMPT_OUTSIDE_QUERY_ROUTE", ident)
        node = nodes[node_id]
        review_only = {"CANDIDATE_EXPLORATION_REVIEW_REQUIRED"} if plan["decision_policy"] == "CANDIDATE_EXPLORATION" else set()
        self.require(not (set(node.get("blocked_by", [])) - review_only), "ATTEMPT_BYPASSED_HARD_BLOCKER", ident)
        self.require(len(by_target[node_id]) <= 1, "ATTEMPT_WITH_AMBIGUOUS_SUPPORT_ROUTE", ident)
        group = by_target[node_id][0] if len(by_target[node_id]) == 1 else None
        result = row["result"]
        # A preflight callback can fail before creating a model call or even an
        # attempt directory. Its reserved context still has to match the graph.
        reserved_pre = {key: self.dependencies[key] for key in (group["members"] if group else [])}
        if row["kind"] == "PROOF":
            reserved_context = digest(canonical({"node": node, "support_group": group, "prerequisites": reserved_pre,
                "environment_sha256": environment["environment_sha256"], "decision_policy": plan["decision_policy"]}))
            self.require(row["context_sha256"] == reserved_context, "RESERVED_PROOF_CONTEXT_MISMATCH", ident)
        model_calls = [(call_id, model) for call_id, model in self.models.items()
                       if Path(model["directory"]).is_relative_to(directory) and
                       model["receipt"]["operation"] in {"autoformalization.lean", "autoformalization.premise"}]
        self.require(len(model_calls) <= 1, "MULTIPLE_PRIMARY_MODEL_CALLS_FOR_RESERVATION", ident)
        if row["outcome"] == "RETURNED":
            self.require(self.read(directory / "result.json") == result, "ATTEMPT_RESULT_PROJECTION_MISMATCH", ident)
        if not model_calls:
            self.require(row["outcome"] != "RETURNED", "RETURNED_ATTEMPT_HAS_NO_MODEL_CALL", ident)
            return
        call_id, model = model_calls[0]
        self.require(model["receipt"]["operation"] == ("autoformalization.premise" if row["kind"] == "PREMISE" else "autoformalization.lean"),
                     "MODEL_OPERATION_RESERVATION_KIND_MISMATCH", ident)
        for linked_id, linked in self.models.items():
            if Path(linked["directory"]).is_relative_to(directory):
                call = self.call_rows[linked_id]
                self.require(row["started_at"] <= call["started"] <= call["finished"] <= row["finished_at"],
                             "MODEL_CALL_OUTSIDE_PROOF_RESERVATION_LIFETIME", linked_id)
        payload = self.model_payloads[call_id]
        self.require(payload["node"] == node and payload["audited_library_declarations"] == library
                     and payload["premise_only"] == (row["kind"] == "PREMISE"), "MODEL_PROOF_CONTEXT_MISMATCH", ident)
        source = self.sources[node["paper_id"]]
        if "pdf_entry" in source:
            context, images = bound_pdf_proof_context(node, source["pdf_entry"])
            expected_sources = [context]
        else:
            expected_sources, images = source["payload"], []
            for span in node.get("source_spans", []):
                self.span(node["paper_id"], span)
        self.require([item["original"] for item in model["task"].get("image_inputs", [])] == images,
                     "MODEL_SOURCE_IMAGES_MISMATCH", ident)
        self.require(payload["full_frozen_sources"] == expected_sources,
                     "MODEL_FULL_FROZEN_SOURCE_MISMATCH", ident)
        self.require(bool(node.get("source_spans")) and bool(node.get("text")), "PROOF_STATEMENT_NOT_SOURCE_BOUND", ident)
        pre = payload["available_prerequisites"]
        self.require(self.read(directory / "prerequisites.json") == pre and set(pre) == set(group["members"] if group else []),
                     "PROOF_PREREQUISITE_SCOPE_MISMATCH", ident)
        for key, dependency in pre.items():
            prior = next((attempt for attempt in all_attempts if attempt["id"] == dependency.get("reservation_id")), None)
            self.require(self.dependencies.get(key) == dependency and prior is not None
                         and prior["node_id"] == key and prior["state"] == "SETTLED"
                         and prior["finished_at"] <= row["started_at"]
                         and prior["result"] == (dependency.get("evidence") or dependency.get("explicit_premise")),
                         "PREREQUISITE_NOT_BOUND_TO_EARLIER_SETTLED_ATTEMPT", [ident, key])
        expected_context = digest(canonical({"node": node, "support_group": group, "prerequisites": pre,
                                            "environment_sha256": environment["environment_sha256"],
                                            "decision_policy": plan["decision_policy"]}))
        if row["kind"] == "PROOF":
            self.require(row["context_sha256"] == expected_context, "PROOF_CONTEXT_HASH_MISMATCH", ident)
        else:
            failed = [attempt for attempt in all_attempts if attempt["node_id"] == node_id and attempt["kind"] == "PROOF"
                      and attempt["result"] == payload["failed_result"] and attempt["started_at"] < row["started_at"]]
            self.require(any(row["context_sha256"] == digest(canonical({"proof_context": attempt["context_sha256"],
                "failed_attempt_id": attempt["id"], "failed_result": attempt["result"], "decision_policy": plan["decision_policy"]}))
                             for attempt in failed), "PREMISE_CONTEXT_NOT_BOUND_TO_FAILED_PROOF", ident)
        earlier = [attempt["result"] for attempt in all_attempts if attempt["node_id"] == node_id and
                   attempt["kind"] == "PROOF" and attempt["started_at"] < row["started_at"] and attempt["result"]]
        self.require(payload["earlier_attempts"] == earlier, "EARLIER_ATTEMPT_CONTEXT_MISMATCH", ident)
        model_result = self.read(directory / "model-result.json")
        self.require(model_result == {"candidate": model["candidate"], "receipt": model["receipt"]}, "MODEL_RESULT_MISMATCH", ident)
        if not isinstance(result, dict) or row["outcome"] != "RETURNED":
            self.notes.append({"code": "FAILED_CALLBACK_PARTIAL_ARTIFACTS_RETAINED", "attempt": ident})
            return
        self.ref(result["model_result"], as_json=True)
        self.ref(result["prerequisite_manifest"], as_json=True)
        if model["candidate"] is None:
            self.require(result.get("kernel_checked") is False and "program_receipt" not in result,
                         "REJECTED_MODEL_OUTPUT_CLAIMED_AS_KERNEL_PROOF", ident)
            return
        candidate = model["candidate"]
        if result.get("compile_disposition") == "SKIPPED_SOURCE_COVERAGE":
            self.require("clause_scope_protocol" in model["response_schema"].get("required", []) and
                         candidate.get("clause_scope_protocol") == "NODE_SOURCE_SPANS_V1",
                         "COVERAGE_SKIP_PROTOCOL_MISMATCH", ident)
            clause_data = bind_clause_report(candidate["clause_report"], expected_sources, node)
            status = candidate_clause_status([{"clause_coverage": clause_binding_coverage(clause_data)}])
            self.require((status in {"INCOMPLETE", "MALFORMED"} or bool(candidate["remaining_obligations"])) and
                         result.get("clause_coverage_status") == status and
                         result.get("remaining_obligations") == candidate["remaining_obligations"] and
                         result.get("kernel_checked") is False and "program_receipt" not in result and
                         result.get("source_alignment_accepted") is False and result.get("promotion_allowed") is False,
                         "COVERAGE_SKIP_REASON_INVALID", ident)
            self.require(self.ref(result["clause_evidence"], as_json=True) == clause_data and
                         self.ref(result["premise_evidence"], as_json=True) ==
                         bind_premise_report(candidate["premise_report"], expected_sources),
                         "COVERAGE_SKIP_SOURCE_EVIDENCE_MISMATCH", ident)
            expected_lamport = {key: candidate[key] for key in
                ("lamport_steps", "alignment_notes", "remaining_obligations", "premise_report",
                 "clause_report", "clause_scope_protocol")}
            self.require(self.ref(result["lamport"], as_json=True) == expected_lamport,
                         "COVERAGE_SKIP_LAMPORT_MISMATCH", ident)
            return
        kind = "DEFINITION" if row["kind"] == "PREMISE" or node["kind"].lower() == "definition" else "THEOREM"
        module = "Proof_" + digest(canonical({"node": node_id, "directory": str(directory)}))[7:27]
        declaration = "AgtXIv.Generated." + module
        upstream = {key: dependency.get("evidence") or dependency.get("explicit_premise") for key, dependency in pre.items()}
        prior_modules = list(dict.fromkeys(item["module"] for item in upstream.values()))
        imports = list(dict.fromkeys(environment["imports"] + prior_modules))
        prop_protocol = environment.get("prop_composition_protocol") == "ACTUAL_VALUE_BINDER_ISDEFEQ_V2"
        prop_targets = [item["audit_record"]["declaration"] for key, item in upstream.items()
                        if pre[key].get("dependency_kind") == "EXPLICIT_PROP_PREMISE"]
        prop_command = " against [" + ", ".join(prop_targets) + "]" if prop_protocol else ""
        expected_source = ("import AgtXIvProofRuntime\n" + "".join("import " + name + "\n" for name in imports) +
            "open scoped BigOperators\n#agtxiv_candidate " + declaration + " " +
            " ".join(json.dumps(value, ensure_ascii=False) for value in (kind, candidate["lean_type"], candidate["lean_value"])) +
            "\n#agtxiv_audit " + declaration + "\n#agtxiv_used_premises " + declaration + prop_command + "\n")
        actual, used, raw, log = self.lean_receipt(result["program_receipt"], environment)
        self.require(raw.decode() == expected_source and self.ref(result["lean_source"]) == raw,
                     "GENERATED_SOURCE_NOT_BOUND_TO_MODEL_TERMS", ident)
        lamport = {key: candidate[key] for key in ("lamport_steps", "alignment_notes", "remaining_obligations")}
        expected_bindings = [{"declaration": declaration}]
        if "clause_report" in model["response_schema"].get("required", []):
            self.require("clause_report" in candidate and "clause_evidence" in result,
                         "CLAUSE_REPORT_EVIDENCE_MISSING", ident)
        if "clause_report" in candidate:
            lamport["clause_report"] = candidate["clause_report"]
            scoped = "clause_scope_protocol" in model["response_schema"].get("required", [])
            if scoped:
                self.require(candidate.get("clause_scope_protocol") == "NODE_SOURCE_SPANS_V1",
                             "CLAUSE_SCOPE_PROTOCOL_MISMATCH", ident)
                lamport["clause_scope_protocol"] = candidate["clause_scope_protocol"]
            clause_data = bind_clause_report(candidate["clause_report"], expected_sources, node if scoped else None)
            self.require(self.ref(result["clause_evidence"], as_json=True) == clause_data,
                         "CLAUSE_SOURCE_EVIDENCE_MISMATCH", ident)
            expected_bindings[0]["clause_coverage"] = clause_binding_coverage(clause_data)
        if "premise_report" in candidate:
            lamport["premise_report"] = candidate["premise_report"]
            report_schema = model["response_schema"].get("properties", {}).get("premise_report", {})
            bound_report_protocol = "source_quote" in report_schema.get("items", {}).get("required", [])
            if bound_report_protocol:
                self.require("premise_evidence" in result, "PREMISE_SOURCE_EVIDENCE_MISSING", ident)
            if "premise_evidence" in result:
                self.require(self.ref(result["premise_evidence"], as_json=True) ==
                             bind_premise_report(candidate["premise_report"], expected_sources),
                             "PREMISE_SOURCE_EVIDENCE_MISMATCH", ident)
            for item in candidate["premise_report"]:
                self.require(bool(item["source_evidence_description"].strip()) ==
                             (item["source_role"] != "NOT_LOCATED"),
                             "PREMISE_REPORT_LOCATION_INCONSISTENT", ident)
        self.require(self.ref(result["lamport"], as_json=True) == lamport, "LAMPORT_MODEL_BINDING_MISMATCH", ident)
        self.require(self.read(directory / "audits.json") == actual, "LEAN_AUDIT_RECORDS_LOG_MISMATCH", ident)
        valid = (len(actual) == 1 and actual[0]["declaration"] == declaration and actual[0]["kind"] == kind
                 and actual[0]["kernel_checked"] and len(used) == 1 and used[0]["declaration"] == declaration)
        if prop_protocol and valid:
            valid = used[0].get("protocol") == "ACTUAL_VALUE_BINDER_ISDEFEQ_V2" and used[0].get("checked_propositions") == prop_targets
            indices = [binder.get("binder_index") for binder in used[0]["used_prop_binders"]]
            self.require(all(type(index) is int and index >= 0 for index in indices) and
                         len(set(indices)) == len(indices), "ACTUAL_VALUE_BINDER_INDICES_INVALID", ident)
        self.require(result["kernel_checked"] == valid, "KERNEL_CHECKED_FLAG_MISMATCH", ident)
        fingerprint = digest(canonical({"node_id": node_id, "text": node.get("text"), "source_spans": node.get("source_spans", [])}))
        self.require(result["source_node_id"] == node_id and result["source_statement_sha256"] == fingerprint
                     and result["declaration_kind"] == kind and result["declaration_bindings"] == expected_bindings,
                     "DECLARATION_STATEMENT_BINDING_MISMATCH", ident)
        expected_paths = list(dict.fromkeys([str(directory / "compiled"),
                              *(path for item in upstream.values() for path in item["object_search_paths"])]))
        self.require(result["program_receipt"]["execution_context"]["lean_path"] == ":".join(expected_paths + [environment["lean_path"]]),
                     "CANDIDATE_OBJECT_SEARCH_ORDER_MISMATCH", ident)
        if valid:
            record = actual[0]
            self.require(result["audit_record"] == record and result["forbidden_axioms"] == []
                         and result["hypotheses"] == record["non_instance_prop_hypotheses"] + record["structure_prop_hypotheses"]
                         and result["module"] == module and result["object_search_paths"] == expected_paths
                         and result["nonvacuity_witness"] == "NONE", "SUCCESSFUL_LEAN_EVIDENCE_MISMATCH", ident)
            if kind == "THEOREM" and ({"statement_trivially_provable", "statement_triviality"} & set(result)
                                      or (directory / "triviality").exists()):  # Historical attempts carry no probe.
                self.triviality(result, declaration, module, environment, directory)
            artifacts = result["compiled_artifacts"]
            recorded_paths = {str(Path(item["path"]).resolve()) for item in artifacts}
            actual_paths = {str(path.resolve()) for path in (directory / "compiled").iterdir()
                            if path.is_file() and any(path.name.endswith(suffix) for suffix in COMPANIONS)}
            expected_files = {str(directory / "compiled" / (module + suffix)) for suffix in COMPANIONS}
            self.require(len(recorded_paths) == len(artifacts) and recorded_paths == actual_paths
                         and recorded_paths <= expected_files and str(directory / "compiled" / (module + ".olean")) in recorded_paths,
                         "COMPILED_COMPANION_INVENTORY_MISMATCH", ident)
            for artifact in artifacts:
                self.ref(artifact)
            self.ref(result["compiled_object"])
            expected_parents = {artifact["path"]: artifact for item in upstream.values()
                                for artifact in item["compiled_artifacts"] + item.get("parent_artifacts", [])}
            self.require({item["path"]: item for item in result["parent_artifacts"]} == expected_parents,
                         "TRANSITIVE_PARENT_OBJECT_INVENTORY_MISMATCH", ident)
            for artifact in expected_parents.values():
                self.ref(artifact)
            witnesses = result["composition_witnesses"]
            self.require(len(witnesses) == len(upstream) and {item["upstream_node_id"] for item in witnesses} == set(upstream),
                         "COMPOSITION_WITNESS_SCOPE_MISMATCH", ident)
            for witness in witnesses:
                key = witness["upstream_node_id"]
                predecessor = upstream[key]["audit_record"]["declaration"]
                self.require(witness["upstream_declaration"] == predecessor and witness["downstream_declaration"] == declaration
                             and witness["downstream_node_id"] == node_id, "COMPOSITION_DECLARATION_MISMATCH", ident)
                is_premise = pre[key].get("dependency_kind") == "EXPLICIT_PROP_PREMISE"
                mentioned = [binder for binder in used[0]["used_prop_binders"] if binder["proof_body_uses_binder"]
                             and predecessor in binder["type_constants"]]
                # Never join proof-value binders to declaration-type binders by
                # name: `fun k h => h` can reverse those names. Equality evidence
                # must describe this very binder in the proof value. The current
                # driver omits it, so explicit-premise composition stays unproved.
                matching = [binder for binder in used[0]["used_prop_binders"]
                            if binder.get("proof_body_uses_binder") is True and
                            type(binder.get("binder_index")) is int and binder["binder_index"] >= 0 and
                            binder.get("type_equality_method") == "LEAN_META_ISDEFEQ_ACTUAL_PROOF_VALUE_BINDER" and
                            predecessor in binder.get("definitionally_equal_propositions", [])] if prop_protocol else []
                composed = bool(matching) if is_premise else predecessor in record["term_constants"]
                expected_basis = "LEAN_USED_PROP_BINDER" if is_premise and matching else "LEAN_ELABORATED_TERM_CONSTANT"
                # A patched historical worker may conservatively disable Prop
                # composition; both the old uncomposed and explicit boundary
                # spellings remain admissible when no witness is claimed.
                allowed_basis = {expected_basis}
                if is_premise and not matching:
                    allowed_basis.add("PROP_BINDER_TYPE_EQUIVALENCE_UNAVAILABLE")
                self.require(witness["status"] == ("COMPOSED" if composed else "NOT_COMPOSED")
                             and witness["used_prop_binders"] == (matching if is_premise else [])
                             and witness["basis"] in allowed_basis,
                             "COMPOSITION_NOT_SUPPORTED_BY_ACTUAL_TERM", ident)
                if is_premise:
                    self.explicit_prop_edges += 1
                    self.notes.append({"code": "CONSERVATIVE_PROP_BINDER_MATCH", "attempt": ident, "upstream": key,
                        "matched": composed, "definitionally_equal_type_audit_performed": prop_protocol,
                        "limit": "Requires actual proof-value binder type evidence. Name matching to declaration parameters and merely mentioning a proposition are insufficient."})
            if row["kind"] == "PREMISE":
                self.require(candidate["lean_type"].strip() == "Prop" and record["type"] == "Prop"
                             and result["lean_prop"] == candidate["lean_value"] and result["declaration"] == declaration,
                             "PREMISE_IS_NOT_THE_ELABORATED_PROP", ident)
        for call_id, model in self.models.items():
            if Path(model["directory"]).is_relative_to(directory) and model["receipt"]["operation"] == "autoformalization.failure_classify":
                self.require(self.model_payloads[call_id] == {"candidate": candidate, "diagnostics": log},
                             "FAILURE_CLASSIFICATION_NOT_BOUND_TO_LOG", ident)
        self.unreviewed(result, ident)
        self.checked_attempts.append({"id": ident, "node_id": node_id, "kind": row["kind"], "kernel_checked": valid,
                                      "declaration": declaration, "explicit_premises": actual[0].get("non_instance_prop_hypotheses", []) if valid else []})

    def audit(self):
        plan = self.read(self.run / "plan.json")
        ledger = self.read(self.run / "ledger.json")
        request = self.read(self.run / "request-snapshot.json")
        graph = self.read(self.run / "candidate-root-audited-graph.json")
        result = self.read(self.run / "proof-walk-result.json")
        self.dependencies = result["available_dependencies"]
        summary = self.read(self.run / "summary.json")
        self.validate(plan, "Plan", "plan")
        if "model_routing" in plan["environment"]:
            from model_routing import validate_policy
            try:
                validate_policy(plan["environment"]["model_routing"])
            except (ValueError, TypeError, KeyError) as error:
                self.require(False, "MODEL_ROUTING_INVALID", "plan", str(error))
        self.validate(ledger, "PlanLedger", "ledger")
        calls, attempts = self.sqlite_projection(plan, ledger)
        self.call_rows = {row["id"]: row for row in calls}
        self.require(self.ref(plan["environment"]["request"], as_json=True) == request, "REQUEST_SNAPSHOT_MISMATCH")
        self.require(plan["environment"]["proof_environment"] == request["environment"]
                     and result["request"] == plan["environment"]["request"]
                     and plan["paper_id"] == request["paper_id"] and plan["source_sha256"] == request["source_sha256"],
                     "PLAN_REQUEST_IDENTITY_MISMATCH")
        runtime_findings = []
        for row in plan["environment"]["runtime_sources"]:
            raw = self.ref(row["snapshot"])
            if Path(row["repository_path"]).name == "proof_backend.py":
                text = raw.decode("utf-8")
                if 'used = [row for row in premise_rows[0]["used_prop_binders"]' in text:
                    if 'parameter["name"] == row["binder"]' in text:
                        runtime_findings.append({"code": "KNOWN_PROOF_TYPE_BINDER_NAME_JOIN_DEFECT",
                            "source": row["snapshot"], "basis": "STATIC_SOURCE_REVIEW_NOT_A_RUNTIME_COUNTEREXAMPLE",
                            "detail": "Type (h : P) → (k : ¬P) → ¬P with proof fun k h => h can join actual binder h : ¬P to statement binder h : P. Name matching does not establish proposition identity."})
                    elif 'upstream["declaration"] in row["type_constants"]' in text:
                        runtime_findings.append({"code": "KNOWN_PROP_CONTAINS_CONSTANT_COMPOSITION_DEFECT",
                            "source": row["snapshot"], "basis": "STATIC_SOURCE_REVIEW_NOT_A_RUNTIME_COUNTEREXAMPLE",
                            "detail": "A used proof binder mentioning P, such as ¬P or P → True, is not itself a premise of type P."})
        environment, library, receipt = self.environment(request["environment"])
        self.require(environment["environment_sha256"] == plan["environment"]["lean_environment_sha256"], "PLAN_ENVIRONMENT_MISMATCH")
        nodes, by_target, active = self.graph(request, graph, library, receipt, plan)
        trusted = set()
        if "human_reviews" in result:  # Pre-walk support-group reviews; rebuilt from their pinned file.
            self.ref(result["human_reviews"]["source"])
            loaded = load_reviews(result["human_reviews"]["source"]["path"], graph)
            self.require({key: loaded[key] for key in ("source", "rejections")} == result["human_reviews"],
                         "HUMAN_REVIEWS_NOT_REPRODUCED")
            trusted = set(loaded["trusted_human_support_groups"])
        for paper_id, entry in request["paper_sources"].items():
            self.source_paper(paper_id, entry)
        self.require(len(request["paper_sources"]) == plan["limits"]["max_papers"], "SOURCE_PAPER_COUNT_MISMATCH")
        for call in calls:
            self.model_call(call, plan)
        known_directories = {str(self.run / "attempts" / row["id"].replace(":", "-")) for row in attempts}
        self.require(all(str(path.resolve()) in known_directories for path in (self.run / "attempts").iterdir() if path.is_dir()),
                     "UNRESERVED_PROOF_DIRECTORY")
        self.require({str(Path(model["directory"]) / "receipt.json") for model in self.models.values()} ==
                     {str(path.resolve()) for path in (self.run / "attempts").glob("*/model/call-*/receipt.json")} |
                     {str(path.resolve()) for path in (self.run / "attempts").glob("*/failure-model/call-*/receipt.json")},
                     "MODEL_RECEIPT_WITHOUT_LEDGER_RESERVATION")
        cyclic = {node for scc in graph.get("sccs", []) for node in scc["members"]}
        self.require(not ({row["node_id"] for row in attempts} & cyclic), "ATTEMPT_ON_CYCLIC_ROUTE")
        for row in attempts:
            self.attempt(row, plan, environment, library, nodes, by_target, active, attempts)
        completed, premises = result["completed_candidates"], result["premise_candidates"]
        self.require(not set(completed) & set(premises) and result["available_dependencies"] == {**completed, **premises},
                     "AVAILABLE_DEPENDENCY_PROJECTION_MISMATCH")
        attempt_map = {row["id"]: row for row in attempts}
        for node_id, dependency in result["available_dependencies"].items():
            evidence = dependency.get("evidence") or dependency.get("explicit_premise")
            row = attempt_map.get(dependency["reservation_id"])
            self.require(row is not None and row["node_id"] == node_id and row["result"] == evidence
                         and evidence.get("kernel_checked") is True, "AVAILABLE_DEPENDENCY_NOT_ACTUALLY_AUDITED", node_id)
            if plan["decision_policy"] == "CANDIDATE_EXPLORATION":
                self.require(dependency["derived_state"] == "AWAITING_REVIEW" and dependency["unreviewed_blockers"],
                             "EXPLORATORY_DEPENDENCY_PROMOTED", node_id)
            group = by_target[node_id][0] if len(by_target[node_id]) == 1 else None
            predecessors = [result["available_dependencies"][key] for key in (group["members"] if group else [])]
            expected_conditionals = {key for item in predecessors for key in item["conditional_on"]}
            expected_vacuity = {key for item in predecessors for key in item["vacuity_unknown_nodes"]}
            is_premise = dependency["dependency_kind"] == "EXPLICIT_PROP_PREMISE"
            if is_premise:
                expected_conditionals.add(node_id)
            if is_premise or nodes[node_id]["kind"].lower() != "definition":
                expected_vacuity.add(node_id)
            self.require(set(dependency["conditional_on"]) == expected_conditionals
                         and set(dependency["vacuity_unknown_nodes"]) == expected_vacuity,
                         "INHERITED_PREMISE_OR_VACUITY_OBLIGATION_DROPPED", node_id)
            inherited_review = {key for item in predecessors for key in item.get("unreviewed_blockers", [])}
            inherited_review.update(nodes[node_id].get("unreviewed_blockers", []))
            if plan["decision_policy"] == "CANDIDATE_EXPLORATION":
                inherited_review.add("candidate-exploration:" + node_id)
                inherited_review.update(set(nodes[node_id].get("blocked_by", [])) & {"CANDIDATE_EXPLORATION_REVIEW_REQUIRED"})
                if group and group["id"] not in trusted:
                    inherited_review.add("unreviewed-support-group:" + group["id"])
            self.require(inherited_review <= set(dependency["unreviewed_blockers"]),
                         "INHERITED_SOURCE_REVIEW_OBLIGATION_DROPPED", node_id)
            if not is_premise:
                self.require({item["upstream_node_id"] for item in evidence["composition_witnesses"]
                              if item["status"] == "COMPOSED"} == set(group["members"] if group else []),
                             "UNCOMPOSED_PROOF_PUBLISHED_AS_AVAILABLE", node_id)
                # certify reads these copies; they must be what bottom_up_walk derives from the audited evidence.
                self.require(dependency["environment_hypotheses"] == evidence["hypotheses"]
                             and dependency["kernel_attestation_state"] == (
                                 "DEFINITION_ELABORATED" if nodes[node_id]["kind"].lower() == "definition" else
                                 "KERNEL_CHECKED_VACUITY_UNKNOWN" if dependency["vacuity_unknown_nodes"] else
                                 "KERNEL_CHECKED_CANDIDATE")
                             and evidence.get("statement_trivially_provable", False) is False,
                             "DERIVED_DEPENDENCY_FIELDS_MISMATCH", node_id)
        self.require(len(result["outcomes"]) == len(nodes) and {row["node_id"] for row in result["outcomes"]} == set(nodes),
                     "WALK_OUTCOME_NODE_SCOPE_MISMATCH")
        # Runs that pin a chain certificate put its recomputed state in the summary; the walk itself never promotes.
        chain = self.ref(summary["chain_certificate"], as_json=True) if "chain_certificate" in summary else None
        if chain is not None:
            self.validate(chain, "ChainCertificate", "chain-certificate")
            self.require(chain == certificate(graph, result, plan_id=plan["plan_id"],
                         environment_sha256=plan["environment"]["lean_environment_sha256"]) and chain["human_accepted"] is False
                         and all(self.ref(summary[key]) for key in ("audited_graph", "ledger")), "CHAIN_CERTIFICATE_NOT_REPRODUCED")
        self.require(result["chain_state"] == "CHAIN_INCOMPLETE" and summary["chain_state"] == (chain or {}).get("state", "CHAIN_INCOMPLETE")
                     and result["source_alignment_accepted"] is False and result["promotion_allowed"] is False
                     and summary["source_alignment_accepted"] is False and summary["promotion_allowed"] is False,
                     "WALK_OR_SUMMARY_PROMOTED")
        self.require(summary["query_count"] == len(graph["query_ids"]) and summary["kernel_candidate_count"] == len(completed)
                     and summary["explicit_premise_count"] == len(premises) and summary["outcome_count"] == len(result["outcomes"])
                     and summary["model_call_count"] == len(calls) and self.ref(summary["result"], as_json=True) == result,
                     "SUMMARY_PROJECTION_MISMATCH")
        self.unreviewed(result, "proof-walk-result")
        for finding in runtime_findings:
            finding["explicit_prop_composition_edges_in_this_run"] = self.explicit_prop_edges
            finding["not_exercised_by_this_run"] = self.explicit_prop_edges == 0
        self.notes.extend(runtime_findings)
        self.file(Path(__file__))
        return {"kind": "ActualProofWalkArtifactAudit", "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "run": str(self.run), "status": "PASS" if not self.issues else "FAILED", "issues": self.issues,
                "scope": "SINGLE_RECORDED_RUN_SQLITE_MODEL_BYTES_SOURCE_FINGERPRINTS_LEAN_RECEIPTS_AND_TERM_EVIDENCE",
                "model_call_count": len(calls), "proof_and_premise_reservation_count": len(attempts),
                "checked_attempts": self.checked_attempts, "lean_receipt_count": len(self.lean_receipts),
                "verified_file_references": list(self.references.values()), "scope_notes": self.notes,
                "auditor_source": self.references[str(Path(__file__).resolve())],
                "mathematical_status": "CHAIN_INCOMPLETE", "source_alignment_accepted": False,
                "promotion_allowed": False, "historical_library_rebuild_performed": False,
                "full_base_object_bytes_rehashed": False, "model_or_lean_execution_performed": False,
                "semantic_completeness_checked": False}


def audit(run):
    """The report on one run; an audit that raises is FAILED and keeps the evidence gathered so far."""
    auditor = None
    try:
        auditor = Auditor(run)
        return auditor.audit()
    except Exception as error:
        return {"kind": "ActualProofWalkArtifactAudit", "status": "FAILED", "run": str(Path(run).resolve()),
                "error": {"type": type(error).__name__, "detail": str(error)},
                "issues": auditor.issues if auditor else [], "scope_notes": auditor.notes if auditor else [],
                "verified_file_references": list(auditor.references.values()) if auditor else [],
                "mathematical_status": "CHAIN_INCOMPLETE", "promotion_allowed": False,
                "source_alignment_accepted": False, "full_base_object_bytes_rehashed": False,
                "historical_library_rebuild_performed": False, "model_or_lean_execution_performed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Keep prior audit evidence; choose a fresh output")
    report = audit(args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation never overwrites a previous report, including a race.
    with args.output.open("xb") as stream:
        stream.write(canonical(report))
    print(json.dumps({"status": report["status"], "issues": len(report.get("issues", [])),
                      "mathematical_status": "CHAIN_INCOMPLETE", "error": report.get("error")}))
    raise SystemExit(0 if report["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
