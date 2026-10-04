"""Produce an explicit partial import from a frozen, quotation-failed call.

This does not rerun the model or accept mathematical support. Original failure
receipts remain immutable; the ordinary research join still checks source binding.
"""
import argparse
import json
from pathlib import Path

from core import digest, write_json


def recover(call_directory, output):
    if output.exists():
        raise ValueError("RECOVERY_OUTPUT_ALREADY_EXISTS")
    refs = {}
    def read(name):
        path = call_directory / name
        raw = path.read_bytes()
        refs[name] = {"path": str(path.resolve()), "sha256": digest(raw), "byte_size": len(raw)}
        return raw
    receipt = json.loads(read("receipt.json"))
    response_raw = read("response.json")
    prompt_raw = read("prompt.txt")
    task = json.loads(read("task.json"))
    if (receipt.get("error") != "MODEL_CANDIDATE_VALIDATION_FAILED"
            or receipt.get("operation") != "dependency.match" or receipt.get("returncode") != 0
            or receipt.get("unexpected_tool_events") or receipt.get("outcome") == "CANDIDATE_RECORDED"):
        raise ValueError("NOT_A_QUOTATION_FAILED_MATCH_CALL")
    if (digest(response_raw) != receipt["response_sha256"]
            or digest(prompt_raw) != receipt["request_sha256"]
            or task["prompt_sha256"] != receipt["request_sha256"]
            or task["task_id"] != receipt["call_id"]):
        raise ValueError("FROZEN_CALL_BYTES_MISMATCH")
    issues = receipt.get("validation_issues", [])
    allowed = {"MODEL_SOURCE_LOCATOR_INVALID", "MODEL_SOURCE_LOCATOR_NOT_UNIQUE", "MATCH_SUPPORT_QUOTATION_ABSENT"}
    if not issues or any(x.get("code") not in allowed or type(x.get("row")) is not int for x in issues):
        raise ValueError("NONLOCAL_FAILURE_CANNOT_BE_PARTIALLY_REUSED")
    payload = json.loads(prompt_raw.decode().split("\nSOURCE DATA:\n", 1)[1])
    rows = json.loads(response_raw)["matches"]
    wanted = [r["id"] for r in payload["requests"]]
    actual = [r["target_request_id"] for r in rows]
    if len(set(actual)) != len(actual) or set(actual) != set(wanted):
        raise ValueError("REQUEST_SCOPE_MISMATCH")
    bad = {x["row"] for x in issues}
    if any(i < 0 or i >= len(rows) for i in bad):
        raise ValueError("ERROR_ROW_OUT_OF_RANGE")
    selected = [i for i in range(len(rows)) if i not in bad]
    result = {"kind": "HistoricalPartialMatchImport", "matches": [rows[i] for i in selected],
              "downstream_paper_id": payload["downstream_paper"]["id"],
              "upstream_paper_id": payload["upstream_paper"]["id"],
              "selected_row_indices": selected, "rejected_row_indices": sorted(bad),
              "unresolved_request_ids": [rows[i]["target_request_id"] for i in sorted(bad)],
              "original_evidence": refs, "original_receipt": receipt,
              "selection_basis": "EXISTING_ROW_LOCAL_FAILURE_RECEIPT_NOT_NEW_SEMANTIC_REVIEW",
              "all_judgements_unreviewed": True, "new_model_calls": 0}
    write_json(output, result)
    return {"output": str(output), "retained_rows": len(selected), "excluded_rows": len(bad)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--call-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(recover(args.call_directory, args.output)))
