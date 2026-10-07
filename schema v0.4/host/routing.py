"""operation-routing-v2 (§5.4): the v0.3 routes plus the v0.4 operations, each with a training_cutoff.

v0.3 receipts keep operation-routing-v1 (v0.3 model_routing.py, unchanged). Per-route rules (engine class,
permitted models and efforts) live in the ModelSelectionV4 contract, which reuses the v0.3 rules by $ref. Two
profiles exist: engines-v2.json (the v0.3 GPT models) and engines-v2-mimo.json (the metered MiMo candidate for the
v0.4 operations); a plan freezes exactly one of them.
"""
from __future__ import annotations

import json
from pathlib import Path

import contracts
from core import canonical, digest
from model_routing import OPERATION_CLASSES as V03_OPERATION_CLASSES

POLICY_VERSION = "operation-routing-v2"
OPERATION_CLASSES = {**V03_OPERATION_CLASSES, "paper.extract_local": "LIGHT", "paper.extract_focus": "LIGHT",
                     "dependency.match_retrieved": "DECISION", "leg.judge": "DECISION", "match.judge": "DECISION",
                     "corpus.discover": "LIGHT"}
PROFILE = Path(__file__).resolve().parents[1] / "profiles" / "engines-v2.json"
MIMO_PROFILE = PROFILE.with_name("engines-v2-mimo.json")
UNKNOWN_CUTOFF = {"value": "UNKNOWN", "source": "PROFILE_STATES_NO_TRAINING_CUTOFF"}
ROUTE_FIELDS = {"profile", "engine_class", "model", "effort", "reason", "training_cutoff"}


def _selection(policy, operation):
    return {**policy["operations"][operation], "policy_version": policy["version"], "policy_sha256": policy["sha256"],
            "operation": operation}


def validate_policy(policy):
    if not isinstance(policy, dict) or policy.get("version") != POLICY_VERSION:
        raise ValueError("MODEL_ROUTING_POLICY_UNSUPPORTED")
    if policy.get("sha256") != digest(canonical({k: v for k, v in policy.items() if k != "sha256"})):
        raise ValueError("MODEL_ROUTING_POLICY_HASH_MISMATCH")
    if (policy.get("selection_authority") != "HOST_OPERATION_POLICY" or policy.get("automatic_escalation") is not False
            or policy.get("tier_savings_measured") is not False or policy.get("quality_calibration") is not None):
        raise ValueError("MODEL_ROUTING_AUTHORITY_OR_CALIBRATION_INVALID")
    routes = policy.get("operations")
    if not isinstance(routes, dict) or set(routes) != set(OPERATION_CLASSES):
        raise ValueError("MODEL_ROUTING_OPERATION_SET_MISMATCH")
    for operation, route in routes.items():
        if (not isinstance(route, dict) or set(route) != ROUTE_FIELDS
                or route["engine_class"] != OPERATION_CLASSES[operation]
                or not contracts.validator("ModelSelectionV4").is_valid(_selection(policy, operation))
                or not route["reason"].strip()):
            raise ValueError("MODEL_ROUTING_ROUTE_INVALID: " + operation)
    return policy


def freeze_model_routing_v2(profile=PROFILE):
    """Read a project profile only when a new plan is frozen; never inherit account defaults."""
    raw = Path(profile).read_bytes()
    config = json.loads(raw)
    operations = {}
    for operation, selection in config["operations"].items():
        profile = config[selection["profile"]]
        operations[operation] = {"profile": selection["profile"], "engine_class": selection["engine_class"],
                                 "model": profile["model"], "effort": profile["effort"], "reason": selection["reason"],
                                 "training_cutoff": profile.get("training_cutoff", UNKNOWN_CUTOFF)}
    policy = {"version": POLICY_VERSION, "selection_authority": "HOST_OPERATION_POLICY",
              "profile_source_sha256": digest(raw), "operations": operations,
              "automatic_escalation": False, "tier_savings_measured": False, "quality_calibration": None,
              "reuse_policy": "RETAIN_SUCCESSFUL_SOURCE_BOUND_EVIDENCE_WITH_ORIGINAL_MODEL_IDENTITY"}
    policy["sha256"] = digest(canonical(policy))
    return validate_policy(policy)


def select_model_route(policy, operation, engine_class):
    """The ModelSelectionV4 a model receipt records for one call."""
    validate_policy(policy)
    route = policy["operations"].get(operation)
    if route is None or route["engine_class"] != engine_class:
        raise ValueError("MODEL_ROUTING_OPERATION_OR_ENGINE_FORBIDDEN")
    return _selection(policy, operation)
