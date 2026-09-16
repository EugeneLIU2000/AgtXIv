"""Deterministic second gates based on the historical test gaps.

These functions are checks of structure/coverage, not mathematical judgments.
The original per-agent checker report is always retained, including unchecked.
"""
from __future__ import annotations

from agtxiv_v3.contracts import canonical, digest, ref_key

from .types import Assignment


def follow_up_key(request: dict) -> tuple:
    return (request["agent"], request["operation"],
            frozenset(ref_key(ref) for ref in request["input_refs"]))


def guard_draft(task: dict, draft: dict) -> tuple[str, ...]:
    """Called only after the original draft shape/checker passes."""
    reasons: list[str] = []
    if task["operation"] == "planner.propose":
        proposals: dict[tuple, list[dict]] = {}
        for item in draft["proposals"]:
            proposals.setdefault(follow_up_key(item), []).append(item)
        for follow_up in draft["follow_up_requests"]:
            matches = proposals.get(follow_up_key(follow_up), [])
            if len(matches) != 1:
                reasons.append("PLANNER_AMBIGUOUS_OR_UNPROPOSED_FOLLOW_UP")
            elif matches[0]["blocked_on"]:
                reasons.append("PLANNER_BLOCKED_FOLLOW_UP")
        # A valid suggestion still needs a separately approved host template.
    if task["operation"] == "delta.compare":
        targets = {ref_key(ref) for ref in task["target_refs"]
                   if ref["record_type"] != "agtxiv.v3.baseline-snapshot/0.0.0"}
        coverage: set[tuple] = set()
        for record in draft["records"]:
            if record["record_type"] == "agtxiv.v3.contribution-delta/0.0.0":
                coverage.update(ref_key(ref) for ref in record["payload"]["current_refs"])
            elif record["record_type"] == "agtxiv.v3.frontier-item/0.0.0":
                coverage.update(ref_key(ref) for ref in record["payload"]["target_refs"])
        if targets - coverage:
            # Includes the all-empty draft case not rejected by `not deltas`.
            reasons.append("DELTA_DELIVERY_TARGETS_UNACCOUNTED")
    return tuple(dict.fromkeys(reasons))


def delivery_families(task: dict, draft: dict) -> tuple[str, ...]:
    if task["operation"] == "review.backtranslate":
        # Interpretation is frozen FIRST; packet/identity assembly is private.
        return ("BLIND_BACKTRANSLATION_REQUIRES_PRIVATE_ASSEMBLY",)
    if task["operation"] == "formalization.generate":
        # Files need actual byte registration and work-attempt attribution;
        # narrowing expected_record_types must not bypass dedicated assembly.
        return ("LEAN_DRAFT_REQUIRES_ATTEMPT_AND_ARTIFACT_ASSEMBLY",)
    produced = {record["record_type"].removeprefix("agtxiv.v3.").removesuffix("/0.0.0")
                for record in draft.get("records", [])}
    missing = sorted(set(task["expected_record_types"]) - produced)
    return tuple("MISSING_DELIVERY_FAMILY:" + name for name in missing)


def dispatch_key(assignment: Assignment, task: dict) -> str:
    """Conservative work identity includes approved purpose AND actual brief.

    This is NOT a RecordRef or a replacement for immutable task identity.
    Model settings/specification also distinguish execution/cache compatibility.
    Planner reason prose never becomes a template or permission by itself.
    Different dependency gates, exclusions or caps must not reuse admission.
    """
    return digest(canonical({
        "binding": assignment.binding.model_dump(),
        "agent": task["agent"], "operation": task["operation"],
        "brief_raw_sha256": digest(task["brief"].encode("utf-8")),
        "target_refs": task["target_refs"], "input_refs": task["input_refs"],
        "input_artifacts": [{k: ref[k] for k in ("artifact_id", "sha256", "byte_size", "media_type")}
                            for ref in task["input_artifacts"]],
        "expected_record_types": task["expected_record_types"],
        "acceptance": task["acceptance"],
        "depends_on": task["depends_on"], "capabilities": task["capabilities"],
        "exclusions": task["exclusions"], "limits": task["limits"],
    }))
