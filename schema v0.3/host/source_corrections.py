"""Retain correction notices as unresolved source obligations, never supports."""
from copy import deepcopy

from recursive_graph import _verified_json


def apply_source_corrections(assembly, references):
    # Absence preserves legacy artifacts exactly; it does not assert a clean search.
    if not references:
        return assembly
    nodes = {node["id"]: node for node in assembly["nodes"]}
    prepared = []
    seen = set()
    for reference in references:
        notice = _verified_json(reference)
        if (not isinstance(notice, dict)
                or notice.get("kind") != "SourceCorrectionNotice"
                or notice.get("relation") != "CORRECTS"
                or notice.get("impact") != "UNREVIEWED"
                or notice.get("source_alignment_accepted") is not False):
            raise ValueError("UNSUPPORTED_SOURCE_CORRECTION_NOTICE")
        for field in ("original_work_id", "correction_work_id"):
            if not isinstance(notice.get(field), str) or not notice[field].strip():
                raise ValueError("MISSING_CORRECTION_WORK_ID")
        if notice["original_work_id"] == notice["correction_work_id"]:
            raise ValueError("SELF_CORRECTION_RELATION")
        # A retained observation supports discovery only, not theorem extraction.
        evidence = _verified_json(notice["discovery_evidence"])
        if (not isinstance(evidence, dict)
                or evidence.get("original_work_id") != notice["original_work_id"]
                or evidence.get("correction_work_id") != notice["correction_work_id"]
                or not isinstance(evidence.get("publisher_url"), str)
                or not evidence["publisher_url"].startswith("https://")
                or not isinstance(evidence.get("observation"), str)
                or not evidence["observation"].strip()):
            raise ValueError("CORRECTION_DISCOVERY_IDENTITY_MISMATCH")
        targets = notice.get("targets")
        if not isinstance(targets, list) or not targets:
            raise ValueError("CORRECTION_TARGETS_REQUIRED")
        local = set()
        for target in targets:
            if not isinstance(target, dict):
                raise ValueError("INVALID_CORRECTION_TARGET")
            ident = target.get("node_id")
            if not isinstance(ident, str) or not ident.strip():
                raise ValueError("INVALID_CORRECTION_TARGET_ID")
            if ident in local:
                raise ValueError("DUPLICATE_CORRECTION_TARGET")
            local.add(ident)
            if (not isinstance(target.get("source_spans"), list)
                    or not target["source_spans"]
                    or any(not isinstance(span, dict) for span in target["source_spans"])
                    or not isinstance(target.get("statement"), str)
                    or not target["statement"].strip()
                    or not isinstance(target.get("conditions"), list)
                    or any(not isinstance(item, str) for item in target["conditions"])
                    or target.get("paper_id") != notice["original_work_id"]):
                raise ValueError("CORRECTION_TARGET_SOURCE_REQUIRED")
            node = nodes.get(ident)
            if node is None:
                continue  # A frozen target may enter after a later upstream join.
            if (node.get("paper_id") != target["paper_id"]
                    or node.get("text") != target["statement"]
                    or node.get("conditions") != target["conditions"]
                    or node.get("source_spans") != target["source_spans"]):
                raise ValueError("CORRECTION_TARGET_SOURCE_MISMATCH")
            key = (ident, reference["sha256"])
            if key in seen:
                continue
            seen.add(key)
            prepared.append((node, reference, notice))
    # Validate every notice before mutating the assembly.
    for node, reference, notice in prepared:
        record = {"notice": deepcopy(reference), "relation": "CORRECTS",
                  "original_work_id": notice["original_work_id"],
                  "correction_work_id": notice["correction_work_id"],
                  "impact": "UNREVIEWED", "source_alignment_accepted": False}
        obligations = node.setdefault("source_correction_obligations", [])
        if record not in obligations:
            obligations.append(record)
        node["blocked_by"] = sorted(set(node.get("blocked_by", [])) |
                                    {"SOURCE_CORRECTION_REVIEW_REQUIRED:" + reference["sha256"]})
    return assembly
