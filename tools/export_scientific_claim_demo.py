#!/usr/bin/env python3
"""Export the graph-theoretic paper's simplified ScientificClaim demo graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "arxiv:2607.26154v1"
POLYTOPE_CLAIM_ID = "claim:graph-theoretic-nonstabilizerness:sign-relaxation-exactness"
POLYTOPE_FACET_ID = "facet:polytope-exactness"
EXACT_POLYTOPE_MATH_ID = "math-claim-ir:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness"
EXACT_POLYTOPE_CLAIM_ID = "claim:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness"
CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/claims/contribution-role-scientific-claims.jsonl"
CALIBRATIONS = ROOT / "Stabilizerness/ExternalRecordRegistry/scientific-claim-calibrations/scientific-claim-calibrations.jsonl"
SUPPORT = ROOT / "Stabilizerness/ExternalRecordRegistry/claim-support-associations/scientific-claim-support.jsonl"
MATH_MANIFEST = ROOT / "Stabilizerness/MathClaimIRRegistry/manifest.json"
EXTERNAL_MANIFEST = ROOT / "Stabilizerness/ExternalRecordRegistry/manifest.json"
FORMAL_CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/claims/graph-theoretic-nonstabilizerness.jsonl"
SOURCE_ANCHORS = ROOT / "Stabilizerness/MathClaimIRRegistry/source-anchors/graph-theoretic-nonstabilizerness.jsonl"
CANDIDATE_DAG = ROOT / "Stabilizerness/dag/claim-dag.json"
OUTPUT = ROOT / "demo_design/scientific_claims/data/graph-theoretic-scientific-claims.json"
GRAPH_NODE_TYPES = {"paper", "scientific_claim", "math_claim_ir", "oracle_candidate"}
GRAPH_EDGE_TYPES = {"contains", "claim_navigation", "normalizes_identity", "oracle_entry", "oracle_candidate_dependency"}
CLAIM_TYPES = {"contribution", "definition", "lemma", "proposition", "theorem", "result", "assumption", "convention", "referenced"}
ORACLE_NODE_IDS = {
    "root:gottesman-stabilizer-formalism", "root:varela-reduced-polytope",
    "claim:reduced-stabilizer-polytope", "claim:frustration-graph",
    "claim:exact-reduced-vrep", "claim:sign-syndrome-linear-consistent",
    "claim:dependency-affine-code", "claim:pauli-active-dependency",
    "claim:no-active-free-signs", "claim:relaxation-exactness",
}
ORACLE_EVIDENCE = {
    "oracle_status": "ORACLE_PROPOSED",
    "source_alignment": "UNREVIEWED_AT_EDGE_LEVEL",
    "lean_support": "NOT_EXTRACTED",
    "disposition": "CANDIDATE",
}
SUPPORTED_TARGETS = {"org.agtxiv.claim_ir": "math-claim-ir:", "org.agtxiv.mathematical_proposition_ir": "math-proposition-ir:"}
TARGET_SCHEMAS = {
    "org.agtxiv.scientific_claim": ROOT / "Stabilizerness/ScientificClaimRegistry/schema/scientific-claim.schema.json",
    "org.agtxiv.claim_ir": ROOT / "Stabilizerness/MathClaimIRRegistry/schema/math-claim-ir.schema.json",
    "org.agtxiv.mathematical_proposition_ir": ROOT / "Stabilizerness/ExternalRecordRegistry/schema/mathematical-proposition-ir.schema.json",
}


class ExportError(ValueError):
    """Raised when Registry data cannot be exported without ambiguity."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExportError(f"cannot read JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExportError(f"expected a JSON object in {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ExportError(f"cannot read {path}: {error}") from error
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ExportError(f"invalid JSON in {path}:{line_number}: {error}") from error
        if not isinstance(record, dict):
            raise ExportError(f"expected a JSON object in {path}:{line_number}")
        records.append(record)
    return records


def file_hash(path: Path) -> str:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ExportError(f"cannot hash {path}: {error}") from error


def unique_by(records: list[dict[str, Any]], key: str, label: str) -> dict[Any, dict[str, Any]]:
    indexed: dict[Any, dict[str, Any]] = {}
    for record in records:
        value = record.get(key)
        if value is None:
            raise ExportError(f"{label} has no {key}")
        if value in indexed:
            raise ExportError(f"duplicate {label} {key}: {value}")
        indexed[value] = record
    return indexed


def index_related_by_claim(records: list[dict[str, Any]], selected_ids: set[str], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        reference = record.get("scientific_claim_ref")
        claim_id = reference.get("target_id") if isinstance(reference, dict) else None
        if claim_id not in selected_ids:
            continue
        if claim_id in indexed:
            raise ExportError(f"duplicate {label} for {claim_id}")
        indexed[claim_id] = record
    return indexed


def assert_claim_ref(reference: Any, claim: dict[str, Any], label: str, component_path: str | None = None) -> None:
    if not isinstance(reference, dict):
        raise ExportError(f"{label} has no scientific_claim_ref object")
    expected = {
        "target_kind": "org.agtxiv.scientific_claim", "target_id": claim["id"],
        "target_revision": claim["record_revision"], "target_content_hash": claim["content_hash"],
        "component_path": component_path, "claim_ir": None, "claim_ir_members": [],
    }
    for key, value in expected.items():
        if reference.get(key) != value:
            raise ExportError(f"{label} {key} does not match {claim['id']}")
    if reference.get("target_artifact") != (None if component_path else claim["artifact"]):
        raise ExportError(f"{label} target_artifact does not match {claim['id']}")
    expected_schema = {"uri": claim["artifact"]["schema_uri"], "content_hash": file_hash(TARGET_SCHEMAS["org.agtxiv.scientific_claim"])}
    if reference.get("type_schema") != expected_schema:
        raise ExportError(f"{label} type schema does not match {claim['id']}")


def validate_occurrences(claims: list[dict[str, Any]]) -> None:
    occurrence_ids: set[str] = set()
    for claim in claims:
        occurrences = claim.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            raise ExportError(f"{claim['id']} has no source occurrences")
        for occurrence in occurrences:
            identifier = occurrence.get("id") if isinstance(occurrence, dict) else None
            if not isinstance(identifier, str) or identifier in occurrence_ids:
                raise ExportError(f"missing or duplicate source occurrence ID: {identifier!r}")
            occurrence_ids.add(identifier)
            artifact = occurrence.get("source_artifact")
            if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
                raise ExportError(f"{identifier} has no source artifact path")
            source_path = ROOT / artifact["path"]
            if artifact.get("sha256") != file_hash(source_path):
                raise ExportError(f"{identifier} source artifact hash mismatch")
            start, end = occurrence.get("line_start"), occurrence.get("line_end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                raise ExportError(f"{identifier} has an invalid source line range")
            source_lines = source_path.read_text(encoding="utf-8").splitlines()
            if end > len(source_lines) or occurrence.get("source_text") != "\n".join(source_lines[start - 1:end]):
                raise ExportError(f"{identifier} verbatim source text mismatch")


def load_support_targets() -> dict[tuple[str, int], dict[str, Any]]:
    relative_paths = load_json(MATH_MANIFEST).get("claim_files", []) + load_json(EXTERNAL_MANIFEST).get("proposition_files", [])
    if not relative_paths or not all(isinstance(path, str) for path in relative_paths):
        raise ExportError("support target manifests contain no usable target files")
    targets: dict[tuple[str, int], dict[str, Any]] = {}
    for relative_path in relative_paths:
        for target in load_jsonl(ROOT / relative_path):
            identifier, revision = target.get("id"), target.get("revision")
            if not isinstance(identifier, str) or not identifier.startswith(tuple(SUPPORTED_TARGETS.values())):
                continue
            key = (identifier, revision)
            if key in targets:
                raise ExportError(f"duplicate support target: {identifier} revision {revision}")
            targets[key] = target
    return targets


def assert_support_ref(reference: Any, targets: dict[tuple[str, int], dict[str, Any]], label: str) -> None:
    if not isinstance(reference, dict):
        raise ExportError(f"{label} has no target_ref object")
    kind, identifier, revision = reference.get("target_kind"), reference.get("target_id"), reference.get("target_revision")
    prefix = SUPPORTED_TARGETS.get(kind)
    if prefix is None or not isinstance(identifier, str) or not identifier.startswith(prefix):
        raise ExportError(f"{label} target kind does not match target ID {identifier!r}")
    target = targets.get((identifier, revision))
    if target is None:
        raise ExportError(f"{label} has dangling target {identifier} revision {revision}")
    if reference.get("target_content_hash") != target.get("semantic_content_hash") or reference.get("target_artifact") != target.get("artifact"):
        raise ExportError(f"{label} target identity does not match {identifier}")
    expected_schema = {"uri": target["artifact"]["schema_uri"], "content_hash": file_hash(TARGET_SCHEMAS[kind])}
    if reference.get("type_schema") != expected_schema:
        raise ExportError(f"{label} target type schema does not match {identifier}")
    if reference.get("component_path") is not None or reference.get("claim_ir_members") != []:
        raise ExportError(f"{label} has an unexpected component path or member list")
    if kind == "org.agtxiv.claim_ir":
        expected = {"id": identifier, "revision": revision, "semantic_content_hash": target["semantic_content_hash"]}
        if reference.get("claim_ir") != expected:
            raise ExportError(f"{label} ClaimIR identity does not match {identifier}")
    elif reference.get("claim_ir") is not None:
        raise ExportError(f"{label} MathematicalPropositionIR must not contain claim_ir")


def compact_label(identifier: str) -> str:
    return identifier.rsplit(":", 1)[-1].replace("-", " ").title()


def fenced(text: str, language: str = "") -> str:
    if "```" in text:
        raise ExportError("graph Markdown code content contains an unsupported fence")
    return f"```{language}\n{text}\n```"


def extract_formula_previews(source_text: str) -> list[str]:
    """Extract standalone TeX fragments without passing document structure to MathJax."""
    candidates: list[tuple[int, str]] = []
    patterns = (
        re.compile(r"(?<!\\)(?<!\$)\$(?!\$)([^\n$]+?)(?<!\\)\$"),
        re.compile(r"\\\((.*?)\\\)", re.DOTALL),
        re.compile(r"\\\[(.*?)\\\]", re.DOTALL),
    )
    for pattern in patterns:
        candidates.extend((match.start(), match.group(1)) for match in pattern.finditer(source_text))
    equation_pattern = re.compile(
        r"\\begin\{(?P<environment>(?:equation|align|gather|multline)\*?)\}(.*?)\\end\{(?P=environment)\}",
        re.DOTALL,
    )
    candidates.extend((match.start(), match.group(2)) for match in equation_pattern.finditer(source_text))

    previews: list[str] = []
    seen: set[str] = set()
    for _, candidate in sorted(candidates, key=lambda item: item[0]):
        without_labels = re.sub(r"\\label\{[^{}]*\}", "", candidate)
        tex = "\n".join(line.strip() for line in without_labels.splitlines() if line.strip()).strip()
        if not tex or re.search(r"\\(?:begin|end|label|ref|eqref|cite)\b", tex):
            continue
        if tex not in seen:
            seen.add(tex)
            previews.append(tex)
    return previews


def validate_markdown_detail(detail: Any, node_id: str) -> None:
    if not isinstance(detail, str) or not detail.strip().startswith("## "):
        raise ExportError(f"graph node {node_id} has missing or malformed Markdown detail")
    lowered = detail.lower()
    if any(token in lowered for token in ("<script", "javascript:", "data:text/html", "onerror=", "onload=", "\x00")):
        raise ExportError(f"graph node {node_id} has unsafe Markdown detail")
    if detail.count("```") % 2:
        raise ExportError(f"graph node {node_id} has an unclosed Markdown fence")


def load_oracle_subgraph() -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    dag = load_json(CANDIDATE_DAG)
    if dag.get("graph_view") != "ORACLE_CANDIDATE":
        raise ExportError("candidate DAG is not an ORACLE_CANDIDATE graph view")
    dag_nodes = unique_by(dag.get("nodes", []), "id", "candidate DAG node")
    missing = ORACLE_NODE_IDS - dag_nodes.keys()
    if missing:
        raise ExportError(f"candidate DAG is missing required nodes: {sorted(missing)}")
    selected_nodes = {candidate_id: dag_nodes[candidate_id] for candidate_id in ORACLE_NODE_IDS}
    for candidate_id, record in selected_nodes.items():
        issues = record.get("issue_badges", [])
        if not isinstance(issues, list):
            raise ExportError(f"candidate DAG node {candidate_id} has malformed issue badges")
        for issue in issues:
            if not isinstance(issue, dict) or set(issue) != {"object", "status", "badges", "interpretation"} or not issue["badges"]:
                raise ExportError(f"candidate DAG node {candidate_id} has malformed structured issue metadata")
    selected_edges = [edge for edge in dag.get("edges", []) if edge.get("from") in selected_nodes and edge.get("to") in selected_nodes]
    if not selected_edges:
        raise ExportError("candidate DAG contains no selected dependency edges")
    for edge in selected_edges:
        if edge.get("evidence") != ORACLE_EVIDENCE or edge.get("type") not in dag.get("edge_types", {}) or not str(edge.get("reason", "")).strip():
            raise ExportError(f"candidate DAG edge {edge.get('from')} -> {edge.get('to')} is malformed")
    return dag, selected_nodes, selected_edges


def oracle_layout_levels(selected_nodes: dict[str, dict[str, Any]], selected_edges: list[dict[str, Any]]) -> dict[str, int]:
    predecessors = {candidate_id: set() for candidate_id in selected_nodes}
    successors = {candidate_id: set() for candidate_id in selected_nodes}
    for edge in selected_edges:
        predecessors[edge["to"]].add(edge["from"])
        successors[edge["from"]].add(edge["to"])
    ready = sorted(candidate_id for candidate_id, incoming in predecessors.items() if not incoming)
    levels = {candidate_id: 4 for candidate_id in ready}
    remaining = {candidate_id: set(incoming) for candidate_id, incoming in predecessors.items()}
    visited = 0
    while ready:
        candidate_id = ready.pop(0)
        visited += 1
        for target in sorted(successors[candidate_id]):
            levels[target] = max(levels.get(target, 4), levels[candidate_id] + 1)
            remaining[target].discard(candidate_id)
            if not remaining[target]:
                ready.append(target)
                ready.sort()
    if visited != len(selected_nodes):
        raise ExportError("selected Oracle candidate subgraph contains a cycle")
    return levels


def expected_polytope_navigation() -> list[dict[str, Any]]:
    associations = [record for record in load_jsonl(SUPPORT) if record.get("scientific_claim_ref", {}).get("target_id") == POLYTOPE_CLAIM_ID]
    if len(associations) != 1:
        raise ExportError("expected exactly one support association for the polytope contribution claim")
    links = [link for link in associations[0].get("links", []) if link.get("facet_id") == POLYTOPE_FACET_ID]
    required = {
        (EXACT_POLYTOPE_MATH_ID, "DIRECT_ATOMIC_SUPPORT", "COMPLETE"),
        ("math-claim-ir:graph-theoretic-nonstabilizerness:sign-set-collapse", "FRAMEWORK_SUPPORT", "PARTIAL"),
    }
    actual = {(link.get("target_ref", {}).get("target_id"), link.get("relationship"), link.get("facet_coverage")) for link in links}
    if actual != required:
        raise ExportError("polytope facet Registry association does not contain the required exact navigation pair")
    return links


def anchor_lines(formal: dict[str, Any], anchors: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    for anchor_id in formal["source_anchors"]:
        anchor = anchors.get(anchor_id)
        if anchor is None:
            lines.append(f"- `{anchor_id}` — **referenced anchor / Registry record missing**")
        else:
            location = anchor["location"]
            lines.append(f"- `{anchor_id}` — resolved SourceAnchor, lines `{location['line_start']}–{location['line_end']}`")
    return lines


def occurrence_detail(occurrence: dict[str, Any], calibration: dict[str, Any]) -> str:
    role = occurrence["occurrence_role"]
    relation = calibration.get("primary_to_normalized_relation") if role == "PRIMARY" else calibration.get("body_to_normalized_relation") if role == "BODY_SUPPORT" else "SOURCE OCCURRENCE"
    parts = [
        f"#### {role} · lines {occurrence['line_start']}–{occurrence['line_end']}",
        "\n".join([
            f"- Occurrence: `{occurrence['id']}`", f"- Source: `{occurrence['source_artifact']['path']}`",
            f"- Zone: `{occurrence['source_zone']}`", f"- Calibration: `{relation or 'SOURCE OCCURRENCE'}`",
        ]),
        "##### Exact source excerpt\n" + fenced(occurrence["source_text"], "tex-source"),
    ]
    previews = extract_formula_previews(occurrence["source_text"])
    if previews:
        parts.append("##### Formula preview\n" + "\n\n".join(f"$$\n{formula}\n$$" for formula in previews))
    return "\n\n".join(parts)


def contribution_detail(claim: dict[str, Any], calibration: dict[str, Any], association: dict[str, Any]) -> str:
    outcomes = {item["facet_id"]: item["coverage"] for item in association["facet_outcomes"]}
    facets = []
    for facet in claim["facets"]:
        links = [link for link in association["links"] if link["facet_id"] == facet["facet_id"]]
        facets.append("\n".join([
            f"#### {compact_label(facet['facet_id'])}", facet["statement"],
            f"- Facet selector: `{facet['facet_id']}`", f"- Navigation coverage: **{outcomes[facet['facet_id']]}**",
            *[f"- `{link['relationship']}` / `{link['facet_coverage']}` → `{link['target_ref']['target_id']}`" for link in links],
        ]))
    return "\n\n".join([
        "## Contribution ScientificClaim", f"**{compact_label(claim['id'])}**", claim["normalized_statement"],
        f"- ID: `{claim['id']}`", f"- Revision: `{claim['record_revision']}`", f"- Content hash: `{claim['content_hash']}`",
        "### Scope\n" + "\n".join(f"- {hint}" for hint in claim["scope_hints"]),
        "### Facet and support metadata\n" + "\n\n".join(facets),
        "### Claim-level source occurrences\n" + "\n\n".join(occurrence_detail(item, calibration) for item in claim["occurrences"]),
        "### Source calibration", f"- Calibration record: `{calibration['id']}`", f"- Direction: `{calibration['relation_direction']}`",
        "*Occurrences and facets remain metadata of this source-faithful claim. No occurrence-to-facet proof edge is asserted.*",
    ])


def build_oracle_branch(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    _, dag_nodes, selected_edges = load_oracle_subgraph()
    levels = oracle_layout_levels(dag_nodes, selected_edges)
    owner = EXACT_POLYTOPE_MATH_ID
    for candidate_id in sorted(ORACLE_NODE_IDS):
        record = dag_nodes[candidate_id]
        source = record.get("source") or {"anchor": record.get("anchor")}
        blockers = [record["status"]] if record.get("status") in {
            "BLOCKED_BY_ROOT_CONTRACT", "BLOCKED_BY_VREP_PROOF_GAP", "AGENT_EXPLICITATION_REQUIRES_PROOF_AUDIT",
            "LOCAL_DERIVATION_BLOCKED_BY_VREP_IMPORT",
        } else []
        issues = record.get("issue_badges", [])
        parts = [
            "## Oracle-proposed candidate", f"**{record['contract']}**", f"- Candidate ID: `{candidate_id}`",
            f"- Kind: `{record['kind']}`", f"- Source status: `{record['status']}`", "- Scientific acceptance: **UNKNOWN**",
            "- Proof-DAG assertion: **NOT ACCEPTED / NOT ASSERTED**",
            "### Preserved source\n" + fenced(json.dumps(source, ensure_ascii=False, sort_keys=True, indent=2), "json"),
        ]
        if blockers:
            parts.append("### Blockers / audit status\n" + "\n".join(f"- `{blocker}`" for blocker in blockers))
        for issue in issues:
            parts.append("\n".join([
                f"### Structured issue: {issue['object']}", f"- Object: **{issue['object']}**", f"- Status: `{issue['status']}`",
                "- Badges: " + ", ".join(f"`{badge}`" for badge in issue["badges"]), f"- Interpretation: {issue['interpretation']}",
            ]))
        nodes.append({
            "id": f"oracle-candidate:{candidate_id}", "candidate_id": candidate_id, "type": "oracle_candidate",
            "label": compact_label(candidate_id), "detail_markdown": "\n\n".join(parts), "expandable": False,
            "shape": "square", "claim_type": "referenced", "visual_state": "gray", "provenance_role": "ORACLE_PROPOSED",
            "source_status": record["status"], "issue_badges": issues, "candidate_record": record, "layout_level": levels[candidate_id],
        })
    edges.append({
        "id": "edge:oracle-entry:relaxation-exactness", "source": "oracle-candidate:claim:relaxation-exactness",
        "target": owner, "expand_from": owner, "type": "oracle_entry", "relation": "UNVERIFIED CANDIDATE ENTRY",
        "evidence": ORACLE_EVIDENCE,
    })
    for index, record in enumerate(selected_edges):
        edges.append({
            "id": f"edge:oracle-dependency:{index:02d}:{record['from']}:{record['to']}",
            "source": f"oracle-candidate:{record['from']}", "target": f"oracle-candidate:{record['to']}",
            "expand_from": owner, "type": "oracle_candidate_dependency", "relation": "UNVERIFIED CANDIDATE DEPENDENCY",
            "candidate_edge_type": record["type"], "reason": record["reason"], "evidence": record["evidence"],
        })


def expected_facet_filters(exported_claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filters = []
    for bundle in exported_claims:
        claim, association = bundle["claim"], bundle["support_association"]
        for facet in claim["facets"]:
            links = [link for link in association["links"] if link["facet_id"] == facet["facet_id"]]
            claim_ids = []
            math_ids = []
            primary = None
            for link in links:
                target_id = link["target_ref"]["target_id"]
                math_ids.append(target_id)
                if target_id.startswith("math-claim-ir:"):
                    formal_id = link["target_ref"]["claim_ir"]["id"].replace("math-claim-ir:", "claim:", 1)
                    # The immutable claim ID is validated from the target during graph construction.
                    claim_ids.append(formal_id)
                    if link["relationship"] == "DIRECT_ATOMIC_SUPPORT":
                        primary = formal_id
            filters.append({
                "claim_id": claim["id"], "facet_id": facet["facet_id"], "statement": facet["statement"],
                "target_claim_ids": claim_ids, "target_math_ids": math_ids, "primary_claim_id": primary or claim_ids[0],
            })
    return filters


def build_graph(exported_claims: list[dict[str, Any]], targets: dict[tuple[str, int], dict[str, Any]], paper: dict[str, Any]) -> dict[str, Any]:
    formal_by_id = unique_by(load_jsonl(FORMAL_CLAIMS), "id", "FORMAL_ATOMIC ScientificClaim")
    anchor_records = load_jsonl(SOURCE_ANCHORS)
    anchors = unique_by(anchor_records, "id", "SourceAnchor")
    for anchor in anchor_records:
        if anchor.get("artifact_hash") != file_hash(ROOT / anchor["artifact"]):
            raise ExportError(f"SourceAnchor {anchor['id']} artifact hash mismatch")
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    paper_node_id = f"paper:{paper['id']}"
    nodes.append({
        "id": paper_node_id, "type": "paper", "label": paper["title"], "expandable": True, "shape": "circle",
        "claim_type": "result", "visual_state": "neutral", "provenance_role": "PAPER",
        "detail_markdown": "\n\n".join(["## Paper", f"**{paper['title']}**", f"`{paper['id']}`", "### Authors\n" + "\n".join(f"- {a}" for a in paper["authors"]), f"### Frozen source\n`{paper['source_path']}`"]),
    })

    support_contexts: dict[tuple[str, int], list[dict[str, Any]]] = {}
    support_refs: dict[tuple[str, int], dict[str, Any]] = {}
    for bundle in exported_claims:
        claim, calibration, association = bundle["claim"], bundle["calibration"], bundle["support_association"]
        nodes.append({
            "id": claim["id"], "type": "scientific_claim", "label": compact_label(claim["id"]), "expandable": True,
            "shape": "circle", "claim_type": "contribution", "visual_state": "grounded", "provenance_role": "SOURCE_FAITHFUL_CONTRIBUTION",
            "detail_markdown": contribution_detail(claim, calibration, association), "occurrences": claim["occurrences"],
            "occurrence_formula_previews": {item["id"]: extract_formula_previews(item["source_text"]) for item in claim["occurrences"]},
            "facets": claim["facets"], "calibration_record": calibration, "support_metadata": association,
            "record_revision": claim["record_revision"], "content_hash": claim["content_hash"],
        })
        edges.append({"id": f"edge:paper:{claim['id']}", "source": paper_node_id, "target": claim["id"], "expand_from": paper_node_id, "type": "contains", "relation": "CONTAINS CONTRIBUTION"})
        for link in association["links"]:
            reference = link["target_ref"]
            key = (reference["target_id"], reference["target_revision"])
            support_refs[key] = reference
            support_contexts.setdefault(key, []).append({
                "claim_id": claim["id"], "facet_id": link["facet_id"], "relationship": link["relationship"],
                "facet_coverage": link["facet_coverage"], "target_ref": reference,
            })

    formal_added: set[str] = set()
    for key in sorted(support_contexts):
        target, reference, contexts = targets[key], support_refs[key], support_contexts[key]
        if reference["target_kind"] != "org.agtxiv.claim_ir":
            raise ExportError(f"demo support target {target['id']} is referenced but is not a normalized MathClaimIR")
        formal_ref = target.get("claim")
        formal = formal_by_id.get(formal_ref.get("id") if isinstance(formal_ref, dict) else None)
        if formal is None or (formal_ref.get("record_revision"), formal_ref.get("content_hash")) != (formal["record_revision"], formal["content_hash"]):
            raise ExportError(f"MathClaimIR {target['id']} has invalid FORMAL_ATOMIC ScientificClaim identity")
        claim_type = target.get("statement_kind")
        if claim_type != formal.get("kind") or claim_type not in CLAIM_TYPES:
            raise ExportError(f"MathClaimIR {target['id']} has inconsistent mathematical claim type")
        if formal["id"] not in formal_added:
            formal_added.add(formal["id"])
            nodes.append({
                "id": formal["id"], "type": "scientific_claim", "label": compact_label(formal["id"]), "expandable": True,
                "shape": "circle", "claim_type": claim_type, "visual_state": "grounded", "provenance_role": "SOURCE_FAITHFUL_FORMAL_ATOMIC",
                "record_revision": formal["record_revision"], "content_hash": formal["content_hash"], "source_anchors": formal["source_anchors"],
                "detail_markdown": "\n\n".join([
                    "## Source-faithful FORMAL_ATOMIC ScientificClaim", f"**{formal['text']}**", f"- ID: `{formal['id']}`",
                    f"- Mathematical claim type: `{claim_type}`", f"- Revision: `{formal['record_revision']}`", f"- Content hash: `{formal['content_hash']}`",
                    "### Source-anchor resolution\n" + "\n".join(anchor_lines(formal, anchors)),
                    "### Paired normalized display (MathClaimIR)", f"$$\n{target['normalized_statement_expanded_latex']}\n$$",
                    "*The prose above is the immutable source-faithful identity. The displayed formula previews its paired normalized MathClaimIR; the identity edge is not a proof edge.*",
                ]),
            })
            nodes.append({
                "id": target["id"], "type": "math_claim_ir", "label": compact_label(target["id"]), "expandable": target["id"] == EXACT_POLYTOPE_MATH_ID,
                "shape": "square", "claim_type": claim_type, "visual_state": "normalized", "provenance_role": "REORGANIZED_NORMALIZED",
                "revision": target["revision"], "claim_identity": formal_ref, "normalization": target.get("normalization"),
                "detail_markdown": "\n\n".join([
                    "## Reorganized MathClaimIR", f"**{compact_label(target['id'])}**", f"- Target ID: `{target['id']}`",
                    f"- Mathematical claim type: `{claim_type}`", f"- Revision: `{target['revision']}`",
                    f"- Immutable ScientificClaim identity: `{formal['id']}`", "### Mathematical statement",
                    f"$$\n{target['normalized_statement_expanded_latex']}\n$$",
                    "### Registry support metadata\n" + "\n".join(f"- `{item['facet_id']}` · `{item['relationship']}` · coverage `{item['facet_coverage']}`" for item in contexts),
                    "### Exact artifact\n" + fenced(json.dumps(reference["target_artifact"], ensure_ascii=False, sort_keys=True, indent=2), "json"),
                    "*Support coverage, scientific acceptance, and proof-DAG assertion are metadata, not canvas badges. This edge records exact normalization identity only.*",
                ]),
            })
            edges.append({
                "id": f"edge:identity:{formal['id']}:{target['id']}", "source": formal["id"], "target": target["id"],
                "expand_from": formal["id"], "type": "normalizes_identity", "relation": "EXACT IMMUTABLE NORMALIZATION IDENTITY",
                "basis": "Exact MathClaimIR.claim immutable reference", "claim_ref": formal_ref,
            })
        for context in contexts:
            edges.append({
                "id": f"edge:navigation:{context['claim_id']}:{context['facet_id']}:{formal['id']}", "source": context["claim_id"],
                "target": formal["id"], "expand_from": context["claim_id"], "type": "claim_navigation", "relation": "REGISTRY NAVIGATION",
                "facet_id": context["facet_id"], "relationship": context["relationship"], "facet_coverage": context["facet_coverage"],
                "target_ref": context["target_ref"],
            })

    if EXACT_POLYTOPE_MATH_ID not in {node["id"] for node in nodes}:
        raise ExportError("polytope exactness MathClaimIR is missing from Registry navigation")
    build_oracle_branch(nodes, edges)
    graph = {
        "nodes": nodes, "edges": edges, "facet_filters": expected_facet_filters(exported_claims),
        "initial_node_ids": [node["id"] for node in nodes if node["type"] == "paper" or node.get("claim_type") == "contribution"],
        "initial_expanded_node_ids": [paper_node_id],
    }
    # Replace the provisional IDs in filters with the exact immutable identities resolved above.
    math_to_claim = {node["id"]: node["claim_identity"]["id"] for node in nodes if node["type"] == "math_claim_ir"}
    for facet_filter in graph["facet_filters"]:
        facet_filter["target_claim_ids"] = [math_to_claim[target_id] for target_id in facet_filter["target_math_ids"]]
        direct = next((edge for edge in edges if edge["type"] == "claim_navigation" and edge["source"] == facet_filter["claim_id"] and edge["facet_id"] == facet_filter["facet_id"] and edge["relationship"] == "DIRECT_ATOMIC_SUPPORT"), None)
        facet_filter["primary_claim_id"] = direct["target"] if direct else facet_filter["target_claim_ids"][0]
    validate_graph(graph)
    return graph


def validate_graph(graph: dict[str, Any]) -> None:
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ExportError("graph payload must contain node and edge arrays")
    node_by_id = unique_by(nodes, "id", "graph node")
    unique_by(edges, "id", "graph edge")
    forbidden = {"facet", "source_occurrence", "oracle_skeleton", "mathematical_proposition_ir"}
    if any(node.get("type") in forbidden for node in nodes):
        raise ExportError("facet, occurrence, wrapper, and proposition Registry records must not become graph nodes")
    for node in nodes:
        if node.get("type") not in GRAPH_NODE_TYPES or node.get("claim_type") not in CLAIM_TYPES:
            raise ExportError(f"graph node {node.get('id')} has unsupported type metadata")
        if node.get("shape") not in {"circle", "square"} or not str(node.get("label", "")).strip():
            raise ExportError(f"graph node {node.get('id')} has invalid shape or label")
        if node["type"] == "scientific_claim" and node["shape"] != "circle":
            raise ExportError(f"ScientificClaim {node['id']} must be a circle")
        if node["type"] in {"math_claim_ir", "oracle_candidate"} and node["shape"] != "square":
            raise ExportError(f"processed/referenced claim {node['id']} must be a square")
        if node["type"] == "oracle_candidate" and (node.get("visual_state") != "gray" or not isinstance(node.get("layout_level"), int)):
            raise ExportError(f"Oracle candidate {node['id']} must use gray source-derived styling")
        validate_markdown_detail(node.get("detail_markdown"), node["id"])
    endpoint_types = {
        "contains": ({"paper"}, {"scientific_claim"}),
        "claim_navigation": ({"scientific_claim"}, {"scientific_claim"}),
        "normalizes_identity": ({"scientific_claim"}, {"math_claim_ir"}),
        "oracle_entry": ({"oracle_candidate"}, {"math_claim_ir"}),
        "oracle_candidate_dependency": ({"oracle_candidate"}, {"oracle_candidate"}),
    }
    for edge in edges:
        edge_type = edge.get("type")
        if edge_type not in GRAPH_EDGE_TYPES or edge.get("source") not in node_by_id or edge.get("target") not in node_by_id:
            raise ExportError(f"graph edge {edge.get('id')} has unsupported type or dangling endpoint")
        source_types, target_types = endpoint_types[edge_type]
        if node_by_id[edge["source"]]["type"] not in source_types or node_by_id[edge["target"]]["type"] not in target_types:
            raise ExportError(f"graph edge {edge['id']} has endpoint types invalid for {edge_type}")
        if edge.get("expand_from") not in node_by_id:
            raise ExportError(f"graph edge {edge['id']} has an invalid expansion owner")
        if edge_type == "normalizes_identity":
            source, target = node_by_id[edge["source"]], node_by_id[edge["target"]]
            if edge.get("basis") != "Exact MathClaimIR.claim immutable reference" or target.get("claim_identity", {}).get("id") != source["id"] or source["claim_type"] != target["claim_type"]:
                raise ExportError(f"identity edge {edge['id']} is not exact or loses claim type")
        if edge_type.startswith("oracle_") and edge.get("evidence") != ORACLE_EVIDENCE:
            raise ExportError(f"Oracle edge {edge['id']} does not preserve exact candidate evidence")

    contribution_by_id = {node["id"]: node for node in nodes if node.get("claim_type") == "contribution"}
    source_claims = unique_by([record for record in load_jsonl(CLAIMS) if record.get("paper_id") == PAPER_ID], "id", "source contribution")
    for claim_id, source in source_claims.items():
        node = contribution_by_id.get(claim_id)
        if node is None or node.get("occurrences") != source["occurrences"] or node.get("facets") != source["facets"]:
            raise ExportError(f"source claim {claim_id} does not embed exact occurrences and facets")
        if not all(occurrence["source_text"] in node["detail_markdown"] for occurrence in source["occurrences"]):
            raise ExportError(f"source claim {claim_id} does not render every exact excerpt")
        expected_previews = {occurrence["id"]: extract_formula_previews(occurrence["source_text"]) for occurrence in source["occurrences"]}
        if node.get("occurrence_formula_previews") != expected_previews:
            raise ExportError(f"source claim {claim_id} has non-source-derived occurrence formula previews")
        for occurrence_id, previews in expected_previews.items():
            if previews and any(f"$$\n{formula}\n$$" not in node["detail_markdown"] for formula in previews):
                raise ExportError(f"source claim {claim_id} does not render formula previews for {occurrence_id}")

    filters = graph.get("facet_filters")
    if not isinstance(filters, list):
        raise ExportError("graph has no facet filter mappings")
    filter_keys = {(item.get("claim_id"), item.get("facet_id")) for item in filters}
    expected_keys = {(claim["id"], facet["facet_id"]) for claim in source_claims.values() for facet in claim["facets"]}
    if filter_keys != expected_keys or len(filter_keys) != len(filters):
        raise ExportError("facet filters do not map every Registry facet exactly once")
    for item in filters:
        outgoing = [edge for edge in edges if edge["type"] == "claim_navigation" and edge["source"] == item["claim_id"] and edge["facet_id"] == item["facet_id"]]
        if {edge["target"] for edge in outgoing} != set(item.get("target_claim_ids", [])):
            raise ExportError(f"facet filter {item['facet_id']} does not exactly match Registry navigation")
        math_ids = {next(edge["target"] for edge in edges if edge["type"] == "normalizes_identity" and edge["source"] == claim_id) for claim_id in item["target_claim_ids"]}
        if math_ids != set(item.get("target_math_ids", [])) or item.get("primary_claim_id") not in item["target_claim_ids"]:
            raise ExportError(f"facet filter {item['facet_id']} loses exact identity mapping")
    polytope = next((item for item in filters if (item["claim_id"], item["facet_id"]) == (POLYTOPE_CLAIM_ID, POLYTOPE_FACET_ID)), None)
    if polytope is None or set(polytope["target_math_ids"]) != {link["target_ref"]["target_id"] for link in expected_polytope_navigation()}:
        raise ExportError("selected polytope facet filter does not exactly match its Registry association")
    if any("robustness" in target for target in polytope["target_math_ids"]):
        raise ExportError("polytope facet filter incorrectly includes robustness")

    _, source_candidates, source_oracle_edges = load_oracle_subgraph()
    graph_candidates = {node.get("candidate_id"): node for node in nodes if node["type"] == "oracle_candidate"}
    if set(graph_candidates) != set(source_candidates):
        raise ExportError("graph Oracle candidate node set does not match the source DAG")
    levels = oracle_layout_levels(source_candidates, source_oracle_edges)
    for candidate_id, source in source_candidates.items():
        node = graph_candidates[candidate_id]
        if node.get("candidate_record") != source or node.get("issue_badges") != source.get("issue_badges", []) or node.get("layout_level") != levels[candidate_id]:
            raise ExportError(f"Oracle candidate {candidate_id} does not preserve its source record")
        for issue in source.get("issue_badges", []):
            if any(value not in node["detail_markdown"] for value in [f"Object: **{issue['object']}**", f"Status: `{issue['status']}`", issue["interpretation"], *(f"`{badge}`" for badge in issue["badges"]) ]):
                raise ExportError(f"Oracle candidate {candidate_id} does not render structured issues")
    expected_oracle_edges = sorted((edge["from"], edge["to"], edge["type"], edge["reason"], json.dumps(edge["evidence"], sort_keys=True)) for edge in source_oracle_edges)
    actual_oracle_edges = sorted((edge["source"].removeprefix("oracle-candidate:"), edge["target"].removeprefix("oracle-candidate:"), edge.get("candidate_edge_type"), edge.get("reason"), json.dumps(edge.get("evidence"), sort_keys=True)) for edge in edges if edge["type"] == "oracle_candidate_dependency")
    if actual_oracle_edges != expected_oracle_edges:
        raise ExportError("Oracle candidate dependency edges do not exactly match the source DAG")
    entry = [edge for edge in edges if edge["type"] == "oracle_entry"]
    if len(entry) != 1 or (entry[0]["source"], entry[0]["target"]) != ("oracle-candidate:claim:relaxation-exactness", EXACT_POLYTOPE_MATH_ID):
        raise ExportError("Oracle branch must have one direct unverified entry relation to the normalized target")

    expected_initial = [node["id"] for node in nodes if node["type"] == "paper" or node.get("claim_type") == "contribution"]
    paper_ids = [node["id"] for node in nodes if node["type"] == "paper"]
    if graph.get("initial_node_ids") != expected_initial or graph.get("initial_expanded_node_ids") != paper_ids or len(paper_ids) != 1:
        raise ExportError("graph initial state must contain one paper and contribution claims only")


def build_demo_data() -> dict[str, Any]:
    all_claims = load_jsonl(CLAIMS)
    unique_by(all_claims, "id", "ScientificClaim")
    claims = sorted((record for record in all_claims if record.get("paper_id") == PAPER_ID), key=lambda record: record["id"])
    if len(claims) != 2 or any(record.get("claim_role") != "CONTRIBUTION" for record in claims):
        raise ExportError(f"expected exactly two contribution-role ScientificClaims for {PAPER_ID}")
    validate_occurrences(claims)
    calibrations, support_records = load_jsonl(CALIBRATIONS), load_jsonl(SUPPORT)
    unique_by(calibrations, "id", "calibration")
    unique_by(support_records, "id", "support association")
    selected_ids = {claim["id"] for claim in claims}
    calibration_by_claim = index_related_by_claim(calibrations, selected_ids, "calibration")
    support_by_claim = index_related_by_claim(support_records, selected_ids, "support association")
    targets = load_support_targets()
    exported_claims = []
    for claim in claims:
        calibration, association = calibration_by_claim.get(claim["id"]), support_by_claim.get(claim["id"])
        if calibration is None or association is None:
            raise ExportError(f"missing calibration or support association for {claim['id']}")
        assert_claim_ref(calibration.get("scientific_claim_ref"), claim, calibration["id"])
        assert_claim_ref(association.get("scientific_claim_ref"), claim, association["id"])
        assert_claim_ref(association.get("navigation_basis_ref"), claim, association["id"], "/facets")
        if calibration.get("record_revision") != claim["record_revision"] or calibration.get("relation_direction") != "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM" or association.get("record_revision") != claim["record_revision"]:
            raise ExportError(f"revision or calibration direction does not match {claim['id']}")
        facets = claim.get("facets")
        facet_ids = [facet.get("facet_id") for facet in facets or [] if isinstance(facet, dict)]
        outcomes = association.get("facet_outcomes")
        if not facets or len(facet_ids) != len(facets) or len(set(facet_ids)) != len(facet_ids) or not isinstance(outcomes, list) or sorted(item.get("facet_id") for item in outcomes) != sorted(facet_ids):
            raise ExportError(f"{claim['id']} has malformed facet mappings")
        links = association.get("links")
        if not isinstance(links, list) or not links:
            raise ExportError(f"{association['id']} has no support links")
        linked_facets = set()
        for index, link in enumerate(links):
            if not isinstance(link, dict) or link.get("facet_id") not in facet_ids:
                raise ExportError(f"{association['id']} link {index} has a dangling facet")
            linked_facets.add(link["facet_id"])
            assert_support_ref(link.get("target_ref"), targets, f"{association['id']} link {index}")
        if linked_facets != set(facet_ids):
            raise ExportError(f"{association['id']} has a facet without a support link")
        exported_claims.append({"calibration": calibration, "claim": claim, "support_association": association})
    paper = {
        "authors": ["Yingjian Liu", "Albert Gasull", "Mengyao Hu", "Ruiyun Zhang", "Flavio Baccari", "Jordi Tura"],
        "id": PAPER_ID, "source_path": "Stabilizerness/arXiv-2607.26154v1/draft.tex",
        "title": "Graph Theoretic Approach to Quantum Nonstabilizerness",
    }
    return {
        "architecture": {
            "visual_encoding": {
                "circle": "Source-faithful ScientificClaim with minimal source normalization",
                "square": "Reorganized MathClaimIR",
                "gray": "Temporary, referenced, Oracle-proposed, or otherwise unaccepted claim",
                "color": "Mathematical claim type",
            },
            "calibration_direction": {"code": "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM", "explanation": "Relations describe each embedded source occurrence relative to its normalized contribution ScientificClaim."},
            "verification_boundary": "Navigation, normalization identity, scientific acceptance, and candidate proof dependencies remain distinct metadata.",
        },
        "claims": exported_claims, "graph": build_graph(exported_claims, targets, paper), "paper": paper,
        "schema": "agtxiv.scientific-claim-demo/4.0.0", "source_revision": "2d9b1b7",
    }


def serialize(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT, help="output JSON path")
    parser.add_argument("--check", action="store_true", help="fail if the output differs instead of writing")
    args = parser.parse_args()
    content = serialize(build_demo_data())
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        try:
            current = output.read_text(encoding="utf-8")
        except OSError as error:
            raise SystemExit(f"cannot check {output}: {error}") from error
        if current != content:
            raise SystemExit(f"generated output differs: run {Path(__file__).relative_to(ROOT)}")
        print(f"ScientificClaim demo data is current: {output.relative_to(ROOT)}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Exported 2 ScientificClaims to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
