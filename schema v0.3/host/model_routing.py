"""Host-owned model selection, frozen once per plan, never inferred from source text."""
from __future__ import annotations

import json
from pathlib import Path

from core import canonical, digest

POLICY_VERSION = "operation-routing-v1"
PROOF_OPERATIONS = frozenset({"autoformalization.lean", "autoformalization.lamport", "autoformalization.premise"})
OPERATION_CLASSES = {
    "paper.extract": "LIGHT", "dependency.match": "DECISION",
    "autoformalization.failure_classify": "DECISION",
    **{operation: "HEAVY" for operation in PROOF_OPERATIONS},
}


def validate_policy(policy):
    if not isinstance(policy, dict) or policy.get("version") != POLICY_VERSION:
        raise ValueError("MODEL_ROUTING_POLICY_UNSUPPORTED")
    body = {key: value for key, value in policy.items() if key != "sha256"}
    if policy.get("sha256") != digest(canonical(body)):
        raise ValueError("MODEL_ROUTING_POLICY_HASH_MISMATCH")
    if (policy.get("selection_authority") != "HOST_OPERATION_POLICY"
            or policy.get("automatic_escalation") is not False
            or policy.get("tier_savings_measured") is not False
            or policy.get("quality_calibration") is not None):
        raise ValueError("MODEL_ROUTING_AUTHORITY_OR_CALIBRATION_INVALID")
    routes = policy.get("operations", {})
    if set(routes) != set(OPERATION_CLASSES):
        raise ValueError("MODEL_ROUTING_OPERATION_SET_MISMATCH")
    for operation, route in routes.items():
        if route.get("engine_class") != OPERATION_CLASSES[operation]:
            raise ValueError("MODEL_ROUTING_ENGINE_MISMATCH")
        allowed = {"gpt-6-astra"} if operation in PROOF_OPERATIONS else {"gpt-5.6-luna", "gpt-5.6-terra"}
        if route.get("model") not in allowed or route.get("effort") not in {"low", "medium", "high"}:
            raise ValueError("MODEL_ROUTING_MODEL_OR_EFFORT_FORBIDDEN")
        if not isinstance(route.get("reason"), str) or not route["reason"].strip():
            raise ValueError("MODEL_ROUTING_REASON_ABSENT")
    return policy


def freeze_model_routing(extraction_profile="LIGHT"):
    """Read project profiles only at new-plan creation; never inherit account defaults."""
    if extraction_profile not in {"LIGHT", "LIGHT_TERRA"}:
        raise ValueError("EXTRACTION_PROFILE_MUST_BE_LUNA_OR_TERRA")
    path = Path(__file__).resolve().parents[1] / "profiles/engines.json"
    raw = path.read_bytes()
    config = json.loads(raw)
    operations = {}
    for operation, selection in config["operations"].items():
        profile_name = extraction_profile if operation == "paper.extract" else selection["profile"]
        profile = config[profile_name]
        reason = selection["reason"]
        if operation == "paper.extract" and extraction_profile == "LIGHT_TERRA":
            reason += " Host explicitly selected Terra for this new plan's extraction; successful prior scopes remain reusable."
        operations[operation] = {"profile": profile_name,
            "engine_class": selection["engine_class"], "model": profile["model"],
            "effort": profile["effort"], "reason": reason}
    policy = {"version": POLICY_VERSION, "selection_authority": "HOST_OPERATION_POLICY",
        "profile_source_sha256": digest(raw), "operations": operations,
        "automatic_escalation": False, "tier_savings_measured": False,
        "quality_calibration": None,
        "reuse_policy": "RETAIN_SUCCESSFUL_SOURCE_BOUND_EVIDENCE_WITH_ORIGINAL_MODEL_IDENTITY"}
    policy["sha256"] = digest(canonical(policy))
    return validate_policy(policy)


def select_model_route(plan, operation, engine_class):
    policy = plan.get("environment", {}).get("model_routing")
    if policy is None:
        raise ValueError("MODEL_ROUTING_NOT_FROZEN_NEW_PLAN_REQUIRED")
    validate_policy(policy)
    route = policy["operations"].get(operation)
    if route is None or route["engine_class"] != engine_class:
        raise ValueError("MODEL_ROUTING_OPERATION_OR_ENGINE_FORBIDDEN")
    return {"policy_version": policy["version"], "policy_sha256": policy["sha256"],
            "operation": operation, **route}


def routing_evidence_issues(plan, task, receipt):
    """Historical plans remain historical; routed plans must bind task and receipt."""
    if "model_routing" not in plan.get("environment", {}):
        return []
    try:
        selection = select_model_route(plan, task["operation"], task["engine_class"])
    except (ValueError, KeyError, TypeError) as error:
        return [{"code": "MODEL_ROUTING_INVALID", "detail": str(error)}]
    issues = []
    for name, artifact in (("Task", task), ("ModelReceipt", receipt)):
        if (artifact.get("model_selection") != selection
                or artifact.get("actual_model_requested") != selection["model"]
                or artifact.get("actual_effort_requested") != selection["effort"]
                or artifact.get("operation") != task["operation"]
                or artifact.get("engine_class") != task["engine_class"]):
            issues.append({"code": "MODEL_ROUTING_EVIDENCE_MISMATCH", "subject": name})
    return issues
