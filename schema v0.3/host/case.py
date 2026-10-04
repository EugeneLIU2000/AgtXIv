"""Explicit migration of the existing 2607 case, never automatic edge promotion."""
from __future__ import annotations

import json
import pathlib
import re

from core import canonical, digest

SUPPORT_TYPES = {
    "definition_dependency": "DEFINITION_DEPENDENCY",
    "scientific_claim_dependency": "SCIENTIFIC_CLAIM_DEPENDENCY",
    "scope_dependency": "SCOPE_DEPENDENCY",
}


def frozen_line_spans(repo, artifact, line_spec):
    path = (repo / artifact).resolve()
    if not path.is_relative_to(repo.resolve()) or not path.is_file():
        return []
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    spans = []
    for piece in line_spec.split(","):
        m = re.fullmatch(r"\s*(\d+)(?:-(\d+))?\s*", piece)
        if not m:
            continue
        first, last = int(m[1]), int(m[2] or m[1])
        if 1 <= first <= last <= len(lines):
            start, end = offsets[first - 1], offsets[last]
            spans.append({"artifact": str(path.relative_to(repo.resolve())),
                          "source_sha256": digest(raw), "start_byte": start, "end_byte": end,
                          "span_sha256": digest(raw[start:end]),
                          "line_start": first, "line_end": last})
    return spans


def import_case(repo: pathlib.Path):
    """Conservative AND import, kept entirely on the unreviewed candidate side.

    The old edge format has no alternative-route semantics. The adapter retains
    every listed support dependency jointly; it records this as a migration
    assumption, not as a model decision or checked scientific judgement.
    """
    source = repo / "Stabilizerness/dag/claim-dag.json"
    raw = source.read_bytes()
    data = json.loads(raw)
    nodes, issues, mentions = [], [], []
    target_paper = data["paper"]["id"]
    main_source = data["paper"]["canonical_source"]
    for old in data["nodes"]:
        origin = old.get("source", {})
        artifact, lines = origin.get("artifact"), origin.get("lines", "")
        if old.get("anchor", "").startswith("draft.tex:"):
            artifact, lines = main_source, old["anchor"].split(":", 1)[1]
        elif origin.get("target_anchor", "").startswith("draft.tex:"):
            artifact, lines = main_source, origin["target_anchor"].split(":", 1)[1]
        anchors = frozen_line_spans(repo, artifact, lines) if artifact else []
        node = {"id": old["id"], "kind": old["kind"], "text": old["contract"],
                "paper_id": origin.get("paper_id", target_paper if old["id"].startswith("claim:") else None),
                "source": origin, "source_spans": anchors,
                "disposition": "CANDIDATE", "blocked_by": [], "upstream_search": "FRONTIER",
                "statement_alignment": "AGENT_NORMALIZED_UNREVIEWED", "bridging_claims": [],
                "legacy_source": {"artifact": str(source.relative_to(repo)), "sha256": digest(raw),
                                  "id": old["id"], "status_not_promoted": old.get("status")}}
        # The literal identity below is a reviewed migration mapping, not a
        # substring parser for the legacy graph's 44 ad-hoc status strings.
        if old["id"] == "root:varela-reduced-polytope":
            node["blocked_by"] = ["vrep-repair-not-inhabited"]
            node["source_read_defective"] = True
        elif old["id"] == "root:perfect-graph-weighted-duality":
            node["blocked_by"] = ["weighted-perfect-duality-primary-source-not-aligned"]
        if old["id"] == "claim:fixed-window-monotonicity":
            node["blocked_by"].append("fixed-window-monotonicity-counterexample")
            issues.append({"code": "RECORDED_COUNTEREXAMPLE", "subject": old["id"],
                           "detail": "The legacy review records a counterexample; this claim cannot be scheduled as a theorem without changing its statement.",
                           "evidence": "agents/predicting-magic-from-very-few-measurements/reviews/reduced-rom-monotonicity-counterexample.md"})
        if not anchors:
            issues.append({"code": "SOURCE_ANCHOR_UNRESOLVED", "subject": old["id"],
                           "detail": "No exact source span could be frozen from the legacy locator; source judgement remains pending."})
        if old["id"] == "claim:sign-alignment-identity":
            node["statement_alignment"] = "DOMAIN_WIDENED"
            node["bridging_claims"] = ["claim:no-active-free-signs"]
        nodes.append(node)
    groups = {}
    for idx, edge in enumerate(data["edges"]):
        relation = SUPPORT_TYPES.get(edge["type"])
        if not relation:
            mentions.append({"id": f"legacy-mention:{idx}", "source": edge["from"],
                             "target": edge["to"], "relation": edge["type"], "legacy": edge})
            continue
        target = edge["to"]
        group = groups.setdefault(target, {"id": "legacy-and:" + target, "target": target,
            "members": [], "relation": "PROOF_DEPENDENCY", "disposition": "CANDIDATE"})
        if edge["from"] not in group["members"]:
            group["members"].append(edge["from"])
    for group in groups.values():
        group["members"].sort()
    issues.append({"code": "LEGACY_AND_GROUPING_UNREVIEWED", "subject": target_paper,
                   "detail": "Legacy support edges imported jointly (AND) per target. No automatic promotion or inferred OR alternatives."})
    return {"nodes": nodes, "support_groups": list(groups.values()), "mentions": mentions,
            "issues": issues, "source_sha256": digest(raw), "source_artifact": str(source.relative_to(repo)),
            "target_paper_id": target_paper}


def query_ids(case, selection):
    if selection != "all":
        if selection not in {n["id"] for n in case["nodes"]}:
            raise ValueError("unknown query claim: " + selection)
        return [selection]
    excluded = {"empirical_protocol", "empirical_claim", "limitation", "open_problem"}
    return [n["id"] for n in case["nodes"] if n["id"].startswith("claim:") and n["kind"] not in excluded]
