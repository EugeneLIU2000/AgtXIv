"""Bounded output batches with full frozen context and explicit unfinished scopes.

Supplied ranges are dispatch evidence, never assertions that a model read every
byte or found every claim. The retained batch combiner performs no semantic dedup.
"""
from __future__ import annotations

import json
from pathlib import Path

from chunks import bundle, reference
from core import digest, utcnow, write_json
from model_failures import GLOBAL_PROVIDER_FAILURES
from model import _candidate_focus_issues, _frozen_source_payload, extract_candidates
from recursive_graph import _verified_json


MAX_REUSE_DISPATCH_DEPTH = 16
MODEL_PROVIDER_CIRCUIT_OPEN = "MODEL_PROVIDER_CIRCUIT_OPEN"


def plan_ranges(full_sources, max_focus_bytes):
    if type(max_focus_bytes) is not int or not 1024 <= max_focus_bytes <= 131072:
        raise ValueError("Output focus limit must be 1024–131072 bytes")
    scopes, context_only = [], []
    for source in full_sources:
        # Bibliography content remains in every model prompt. It is not a new
        # paper's mathematical body, nor an assertion that cited works were read.
        if Path(source["path"]).suffix.lower() in {".bib", ".bbl"}:
            context_only.append({"path": source["path"], "reason": "BIBLIOGRAPHY_CONTEXT_ONLY"})
            continue
        raw = source["text"].encode("utf-8")
        start = 0
        while start < len(raw):
            end = min(len(raw), start + max_focus_bytes)
            if end < len(raw):
                newline = raw.rfind(b"\n", start + max_focus_bytes // 2, end)
                if newline >= 0:
                    end = newline + 1
                else:
                    # A very long line may need a cut between UTF-8 codepoints;
                    # the complete line still appears in full source context.
                    while raw[end] & 0xC0 == 0x80:
                        end -= 1
            scopes.append({"id": f"batch-{len(scopes):04d}", "path": source["path"],
                           "byte_start": start, "byte_end": end,
                           "span_sha256": digest(raw[start:end])})
            start = end
    return scopes, context_only


def _scope_identity(scope):
    return {key: scope.get(key) for key in ("id", "path", "byte_start", "byte_end", "span_sha256")}


def explicit_ranges(full_sources, scope_manifest, paper_id, max_focus_bytes):
    """Bind a selected output range plan; omitted text remains full context."""
    data = _verified_json(scope_manifest)
    if data["paper_id"] != paper_id:
        raise ValueError("EXPLICIT_SCOPE_PAPER_MISMATCH")
    source = data["source"]
    selected = [row for row in full_sources if Path(row["path"]).resolve() == Path(source["path"]).resolve()]
    if len(selected) != 1:
        raise ValueError("EXPLICIT_SCOPE_SOURCE_MISSING")
    raw = selected[0]["text"].encode("utf-8")
    if digest(raw) != source["sha256"] or len(raw) != source["byte_size"]:
        raise ValueError("EXPLICIT_SCOPE_SOURCE_CHANGED")
    scopes, seen, previous_end = [], set(), 0
    for row in data["remaining_scopes"]:
        start, end = row["byte_start"], row["byte_end"]
        if (type(start) is not int or type(end) is not int or not previous_end <= start < end <= len(raw)
                or end - start > max_focus_bytes or row["id"] in seen):
            raise ValueError("EXPLICIT_SCOPE_INTERVAL_INVALID")
        raw[start:end].decode("utf-8", errors="strict")
        scopes.append({"id": row["id"], "path": selected[0]["path"], "byte_start": start,
                       "byte_end": end, "span_sha256": digest(raw[start:end])})
        seen.add(row["id"])
        previous_end = end
    if not scopes:
        raise ValueError("EXPLICIT_SCOPE_EMPTY")
    return scopes, [{"path": row["path"], "reason": "OUTSIDE_SELECTED_OUTPUT_SOURCE_CONTEXT_ONLY"}
                    for row in full_sources if row["path"] != selected[0]["path"]]


def _same_reference(left, right):
    return (isinstance(left, dict) and isinstance(right, dict) and
            all(left.get(key) == right.get(key) for key in ("path", "sha256", "byte_size")))


def _recorded_result(row, scope):
    """Validate one direct historical success without trusting its current ledger."""
    if row.get("status") != "CANDIDATE_RECORDED" or _scope_identity(row) != _scope_identity(scope):
        raise ValueError("REUSE_SCOPE_NOT_A_MATCHING_RECORDED_SUCCESS")
    result_ref = row.get("result")
    result = _verified_json(result_ref)
    receipt = result.get("receipt") if isinstance(result, dict) else None
    if (not isinstance(receipt, dict) or result.get("candidate") is None or
            receipt.get("outcome") != "CANDIDATE_RECORDED" or not receipt.get("call_id")):
        raise ValueError("REUSE_RESULT_NOT_A_RECORDED_MODEL_CANDIDATE")
    receipt_path = Path(receipt.get("directory", "")) / "receipt.json"
    response_path = Path(receipt.get("directory", "")) / "response.json"
    try:
        raw_response = response_path.read_bytes()
        recorded_receipt = json.loads(receipt_path.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise ValueError("REUSE_MODEL_ARTIFACT_ABSENT") from error
    if (recorded_receipt != receipt or digest(raw_response) != receipt.get("response_sha256") or
            json.loads(raw_response) != result["candidate"]):
        raise ValueError("REUSE_MODEL_ARTIFACT_MISMATCH")
    return result_ref


def _reused_result(row, scope, *, trail, depth, expected):
    """Resolve a reused row to its original result, with a bounded acyclic chain."""
    if row.get("status") != "CANDIDATE_REUSED" or _scope_identity(row) != _scope_identity(scope):
        raise ValueError("REUSE_SCOPE_NOT_A_MATCHING_REUSED_SUCCESS")
    origin = row.get("reuse_origin")
    if not isinstance(origin, dict) or origin.get("scope_id") != scope["id"]:
        raise ValueError("REUSE_ORIGIN_MISSING")
    origin_dispatch = origin.get("dispatch")
    result_ref = _reusable_result(origin_dispatch, scope, trail=trail, depth=depth + 1, expected=expected)
    if not _same_reference(row.get("result"), result_ref):
        raise ValueError("REUSE_RESULT_REFERENCE_CHAIN_MISMATCH")
    return result_ref


def _reusable_result(dispatch_ref, scope, *, trail=(), depth=0, expected=None):
    """Read immutable prior-dispatch evidence and locate one reusable scope."""
    if depth >= MAX_REUSE_DISPATCH_DEPTH:
        raise ValueError("REUSE_DISPATCH_CHAIN_TOO_DEEP")
    if not isinstance(dispatch_ref, dict):
        raise ValueError("REUSE_DISPATCH_REFERENCE_INVALID")
    identity = (str(Path(dispatch_ref.get("path", "")).resolve()), dispatch_ref.get("sha256"), dispatch_ref.get("byte_size"))
    if identity in trail:
        raise ValueError("REUSE_DISPATCH_CHAIN_CYCLE")
    dispatch = _verified_json(dispatch_ref)
    dispatch_rows = dispatch.get("scopes")
    if not isinstance(dispatch_rows, list):
        raise ValueError("REUSE_DISPATCH_SCOPE_LIST_INVALID")
    if expected is not None and (
            dispatch.get("paper_id") != expected["paper_id"] or
            dispatch.get("source_manifest_sha256") != expected["source_manifest_sha256"] or
            dispatch.get("max_focus_bytes") != expected["max_focus_bytes"] or
            dispatch.get("context_only_files") != expected["context_only_files"] or
            [_scope_identity(row) for row in dispatch_rows] != expected["scopes"]):
        raise ValueError("REUSE_DISPATCH_SOURCE_OR_RANGE_PLAN_MISMATCH")
    rows = [row for row in dispatch_rows if isinstance(row, dict) and row.get("id") == scope["id"]]
    if len(rows) != 1:
        raise ValueError("REUSE_SCOPE_CARDINALITY_MISMATCH")
    row = rows[0]
    if row.get("status") == "CANDIDATE_RECORDED":
        return _recorded_result(row, scope)
    if row.get("status") == "CANDIDATE_REUSED":
        return _reused_result(row, scope, trail=trail + (identity,), depth=depth, expected=expected)
    raise ValueError("REUSE_SCOPE_NOT_SUCCESSFUL")


def _reusable_rows(reuse_dispatch, paper, scopes, context_only, max_focus_bytes):
    """Return successful prior rows whose plan is byte-identical to this dispatch."""
    if reuse_dispatch is None:
        return {}
    dispatch = _verified_json(reuse_dispatch)
    if (dispatch.get("paper_id") != paper["paper"]["id"] or
            dispatch.get("source_manifest_sha256") != paper["paper"]["source_manifest_sha256"] or
            dispatch.get("max_focus_bytes") != max_focus_bytes or
            dispatch.get("context_only_files") != context_only):
        raise ValueError("REUSE_DISPATCH_SOURCE_OR_RANGE_PLAN_MISMATCH")
    prior = dispatch.get("scopes")
    if not isinstance(prior, list) or [_scope_identity(row) for row in prior] != [_scope_identity(scope) for scope in scopes]:
        raise ValueError("REUSE_DISPATCH_SOURCE_OR_RANGE_PLAN_MISMATCH")
    expected = {"paper_id": paper["paper"]["id"],
                "source_manifest_sha256": paper["paper"]["source_manifest_sha256"],
                "max_focus_bytes": max_focus_bytes, "context_only_files": context_only,
                "scopes": [_scope_identity(scope) for scope in scopes]}
    reusable = {}
    for scope, row in zip(scopes, prior, strict=True):
        if row.get("status") not in {"CANDIDATE_RECORDED", "CANDIDATE_REUSED"}:
            continue
        result_ref = _reusable_result(reuse_dispatch, scope, expected=expected)
        reusable[scope["id"]] = {"result": result_ref,
                                  "reuse_origin": {"dispatch": reuse_dispatch, "scope_id": scope["id"]}}
    return reusable


def extract_candidate_batches(ledger, paper, directory, *, source_directory,
                              max_focus_bytes, max_batches=128, reuse_dispatch=None, scope_manifest=None):
    directory = Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError("Retain prior batch evidence; use a fresh dispatch directory")
    directory.mkdir(parents=True, exist_ok=True)
    if type(max_batches) is not int or not 1 <= max_batches <= 512:
        raise ValueError("Batch limit must be 1–512")
    sources = _frozen_source_payload(paper, source_directory, source_directory=source_directory)
    scopes, context_only = (explicit_ranges(sources, scope_manifest, paper["paper"]["id"], max_focus_bytes)
                            if scope_manifest else plan_ranges(sources, max_focus_bytes))
    reusable = _reusable_rows(reuse_dispatch, paper, scopes, context_only, max_focus_bytes)
    dispatch = {"kind": "SourceOutputBatchDispatch", "paper_id": paper["paper"]["id"],
                "created_at": utcnow(), "source_manifest_sha256": paper["paper"]["source_manifest_sha256"],
                "max_focus_bytes": max_focus_bytes, "max_batches": max_batches,
                "source_context": "COMPLETE_FROZEN_UTF8_SOURCES_EACH_CALL_WITH_NO_TRUNCATION",
                "context_only_files": context_only, "scopes": [],
                "reuse_dispatch": reuse_dispatch,
                "scope_manifest": scope_manifest,
                "reading_completeness_asserted": False, "semantic_completeness_asserted": False}
    write_json(directory / "scope-plan.json", {**dispatch, "scopes": scopes})
    manifest = {"paper_id": paper["paper"]["id"],
                "extraction": str(Path(source_directory).resolve() / "extraction.json"), "chunks": []}
    stopped, new_dispatches = None, 0
    for scope in scopes:
        row = {**scope, "status": "NOT_DISPATCHED", "reason": stopped}
        if scope["id"] in reusable:
            row.update(status="CANDIDATE_REUSED", reason=None, **reusable[scope["id"]])
            reused = _verified_json(row["result"])
            receipt = reused["receipt"]
            response = Path(receipt["directory"]) / "response.json"
            provenance_path = directory / scope["id"] / "provenance.json"
            write_json(provenance_path, {"kind": "MODEL_OUTPUT_SCOPE_REUSED", "paper_id": paper["paper"]["id"],
                "source_files": paper["source_files"], "supplied_focus_spans": [scope],
                "read_blocks": [], "reported_read_spans": [], "result": row["result"],
                "reuse_origin": row["reuse_origin"],
                "model_receipt": reference(Path(receipt["directory"]) / "receipt.json"),
                "reading_completeness_asserted": False, "source_alignment_accepted": False})
            manifest["chunks"].append({"id": scope["id"], "response": str(response),
                "provenance": str(provenance_path), "read_spans": []})
            dispatch["scopes"].append(row)
            write_json(directory / "dispatch-checkpoint.json", dispatch)
            ledger.event("ExtractionOutputBatchReused", {"paper_id": paper["paper"]["id"], **row})
            continue
        if new_dispatches >= max_batches:
            stopped = "PAPER_OUTPUT_BATCH_LIMIT"
        if stopped:
            row["reason"] = stopped
            dispatch["scopes"].append(row)
            continue
        try:
            new_dispatches += 1
            result = extract_candidates(ledger, paper, directory / scope["id"] / "model",
                                        source_directory=source_directory, focus_source_spans=[scope])
        except RuntimeError as error:
            if str(error) not in {"MODEL_CALL_BUDGET_EXHAUSTED", "MONETARY_BUDGET_EXHAUSTED", MODEL_PROVIDER_CIRCUIT_OPEN}:
                raise
            stopped = str(error)
            row["reason"] = stopped
            dispatch["scopes"].append(row)
            write_json(directory / "dispatch-checkpoint.json", dispatch)
            continue
        result_ref = write_json(directory / scope["id"] / "result.json", result)
        row.update(result=result_ref, status="FAILED" if result["candidate"] is None else "CANDIDATE_RECORDED")
        if result["candidate"] is not None:
            response = Path(result["receipt"]["directory"]) / "response.json"
            provenance_path = directory / scope["id"] / "provenance.json"
            write_json(provenance_path, {"kind": "MODEL_OUTPUT_SCOPE_SUPPLIED", "paper_id": paper["paper"]["id"],
                "source_files": paper["source_files"], "supplied_focus_spans": [scope],
                "read_blocks": [], "reported_read_spans": [], "result": result_ref,
                "model_receipt": reference(Path(result["receipt"]["directory"]) / "receipt.json"),
                "reading_completeness_asserted": False, "source_alignment_accepted": False})
            manifest["chunks"].append({"id": scope["id"], "response": str(response),
                "provenance": str(provenance_path), "read_spans": []})
        else:
            row["reason"] = result["receipt"].get("error")
        dispatch["scopes"].append(row)
        if row.get("reason") in GLOBAL_PROVIDER_FAILURES:
            stopped = row["reason"]
        # Every return is retained before the next dispatch. A BUSY controller
        # still requires explicit worker recovery after an interrupted call.
        write_json(directory / "dispatch-checkpoint.json", dispatch)
        ledger.event("ExtractionOutputBatchReturned", {"paper_id": paper["paper"]["id"], **row})
    dispatch["complete_output_scope_responses"] = bool(scopes) and all(
        row["status"] in {"CANDIDATE_RECORDED", "CANDIDATE_REUSED"} for row in dispatch["scopes"])
    dispatch["unfinished_scopes"] = [row for row in dispatch["scopes"]
                                     if row["status"] not in {"CANDIDATE_RECORDED", "CANDIDATE_REUSED"}]
    dispatch_ref = write_json(directory / "dispatch.json", dispatch)
    if not manifest["chunks"]:
        return {"candidate": None, "response_reference": None, "dispatch": dispatch_ref,
                "error": "NO_SUCCESSFUL_BATCH_RESPONSE"}
    manifest_path = directory / "bundle-manifest.json"
    manifest["combination_scope_notes"] = [
        "Output scopes supplied to a model are not verified reading or semantic coverage.",
        f"{len(dispatch['unfinished_scopes'])} of {len(scopes)} planned output scopes have no successful candidate response.",
        "Exact dispatch outcomes and omitted byte ranges: " + dispatch_ref["path"] + " (" + dispatch_ref["sha256"] + ").",
        "Bibliography files were supplied as context; output scopes cover the remaining frozen text files."]
    write_json(manifest_path, manifest)
    combined = bundle(manifest_path, directory / "combined")
    # The combined response retains unresolved batch omissions as explicit scope
    # evidence through provenance; never relabel dispatch bytes as read bytes.
    return {"candidate": json.loads(Path(combined["response"]["path"]).read_bytes()),
            "response_reference": combined["response"], "dispatch": dispatch_ref,
            "combination": reference(directory / "combined/bundle-provenance.json"),
            "complete_output_scope_responses": dispatch["complete_output_scope_responses"],
            "unfinished_scope_count": len(dispatch["unfinished_scopes"]),
            "source_completeness_asserted": False}


def audit_batch_dispatch(provenance, paper, full_sources, known_model_call_ids):
    """Reconcile one dispatch, including bounded immutable reuse chains."""
    dispatch = _verified_json(provenance["dispatch"])
    combined = _verified_json(provenance["combination"])
    scopes, context_only = (explicit_ranges(full_sources, dispatch["scope_manifest"], paper["paper"]["id"], dispatch["max_focus_bytes"])
                            if dispatch.get("scope_manifest") else plan_ranges(full_sources, dispatch["max_focus_bytes"]))
    issues = []
    def require(condition, code):
        if not condition:
            issues.append({"code": code, "paper_id": paper["paper"]["id"]})
    require(dispatch["paper_id"] == paper["paper"]["id"] and
            dispatch["source_manifest_sha256"] == paper["paper"]["source_manifest_sha256"], "BATCH_SOURCE_IDENTITY_MISMATCH")
    require([{key: row[key] for key in expected} for row, expected in zip(dispatch["scopes"], scopes)] == scopes
            and len(dispatch["scopes"]) == len(scopes), "BATCH_SCOPE_PLAN_MISMATCH")
    require(dispatch["context_only_files"] == context_only, "BATCH_CONTEXT_FILE_MISMATCH")
    expected_reuse = {"paper_id": paper["paper"]["id"],
                      "source_manifest_sha256": paper["paper"]["source_manifest_sha256"],
                      "max_focus_bytes": dispatch["max_focus_bytes"],
                      "context_only_files": context_only,
                      "scopes": [_scope_identity(scope) for scope in scopes]}
    successful, call_ids = {}, []
    for row in dispatch["scopes"]:
        if row["status"] == "NOT_DISPATCHED":
            require(not row.get("result") and bool(row.get("reason")), "BATCH_UNDISPATCHED_RESULT_MISMATCH")
            continue
        try:
            result = _verified_json(row["result"])
            receipt = result["receipt"]
        except (KeyError, TypeError, ValueError):
            require(False, "BATCH_RESULT_REFERENCE_INVALID")
            continue
        if row["status"] == "CANDIDATE_REUSED":
            origin = row.get("reuse_origin")
            require(isinstance(origin, dict) and _same_reference(origin.get("dispatch"), dispatch.get("reuse_dispatch")) and
                    origin.get("scope_id") == row["id"], "BATCH_REUSE_ORIGIN_MISMATCH")
            try:
                original = _reusable_result(origin.get("dispatch"), row, expected=expected_reuse)
                require(_same_reference(row.get("result"), original), "BATCH_REUSE_RESULT_CHAIN_MISMATCH")
            except (AttributeError, TypeError, ValueError):
                require(False, "BATCH_REUSE_CHAIN_INVALID")
        elif receipt.get("call_id"):
            call_ids.append(receipt["call_id"])
            require(receipt["call_id"] in known_model_call_ids, "BATCH_CALL_NOT_IN_PLAN_LEDGER")
            try:
                require(json.loads((Path(receipt["directory"]) / "receipt.json").read_bytes()) == receipt,
                        "BATCH_MODEL_RECEIPT_MISMATCH")
            except (OSError, ValueError, TypeError, KeyError):
                require(False, "BATCH_MODEL_RECEIPT_MISMATCH")
        if row["status"] in {"CANDIDATE_RECORDED", "CANDIDATE_REUSED"}:
            require(bool(receipt.get("call_id")), "BATCH_SUCCESS_WITHOUT_MODEL_CALL")
            require(result["candidate"] is not None and receipt["outcome"] == "CANDIDATE_RECORDED", "BATCH_SUCCESS_MISMATCH")
            issues.extend(_candidate_focus_issues(result["candidate"], paper["claims"], full_sources, [row]))
            source_response = Path(receipt["directory"]) / "response.json"
            receipt_path = Path(receipt["directory"]) / "receipt.json"
            try:
                raw = source_response.read_bytes()
                require(json.loads(receipt_path.read_bytes()) == receipt and
                        digest(raw) == receipt["response_sha256"] and json.loads(raw) == result["candidate"],
                        "BATCH_RESPONSE_BYTES_MISMATCH")
                successful[row["id"]] = digest(raw)
            except (OSError, ValueError, TypeError, KeyError):
                require(False, "BATCH_RESPONSE_BYTES_MISMATCH")
        else:
            require(row["status"] == "FAILED" and result["candidate"] is None, "BATCH_FAILURE_MISMATCH")
    require(len(call_ids) == len(set(call_ids)), "BATCH_MODEL_CALL_REUSED")
    require({row["id"]: row["response"]["sha256"] for row in combined["chunks"]} == successful,
            "BATCH_COMBINATION_INPUT_MISMATCH")
    for chunk in combined["chunks"]:
        _verified_json(chunk["response"])
        _verified_json(chunk["provenance"])
    unfinished = [row for row in dispatch["scopes"]
                  if row["status"] not in {"CANDIDATE_RECORDED", "CANDIDATE_REUSED"}]
    complete = bool(scopes) and not unfinished
    require(dispatch["unfinished_scopes"] == unfinished and provenance["unfinished_scope_count"] == len(unfinished),
            "BATCH_UNFINISHED_SCOPE_MISMATCH")
    require(dispatch["complete_output_scope_responses"] == provenance["complete_output_scope_responses"] == complete,
            "BATCH_COMPLETENESS_MISMATCH")
    require(combined["source_completeness_asserted"] is False and
            not any(row["reported_read_bytes"] for row in combined["reading_coverage"]), "BATCH_DISPATCH_MISLABELED_AS_READING")
    return issues
