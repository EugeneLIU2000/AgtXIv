#!/usr/bin/env python3
"""Validate the structure of the first AgtXIv vertical-slice prototype.

Passing this program means that references, frozen sources, and the derivation
graph are internally coherent. It deliberately does not erase scientific
blockers or upgrade an unaccepted ClaimContract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.relative_to(REPO)}:{number}: {exc}") from exc
    return records


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_hash(path: Path, start: int, end: int) -> str:
    lines = path.read_bytes().splitlines(keepends=True)
    return hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest()


def collect_paths(value: Any, key: str | None = None) -> Iterable[str]:
    path_keys = {
        "canonical_artifact", "artifacts", "source_hashes", "anchors",
        "statements", "symbols", "chains", "records",
        "formalization_contract", "verification_partition", "assumption_match", "exports", "unresolved",
    }
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from collect_paths(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield from collect_paths(child, key)
    elif isinstance(value, str) and key in path_keys:
        yield value


def has_cycle(nodes: set[str], edges: list[dict[str, str]]) -> bool:
    outgoing: dict[str, set[str]] = defaultdict(set)
    indegree = {node: 0 for node in nodes}
    for edge in edges:
        source, target = edge["from"], edge["to"]
        if target not in outgoing[source]:
            outgoing[source].add(target)
            indegree[target] = indegree.get(target, 0) + 1
            indegree.setdefault(source, 0)
    queue = deque(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in outgoing[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return visited != len(indegree)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-science",
        action="store_true",
        help="also fail when an export is unaccepted or an open blocker remains",
    )
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    parsed_json: dict[Path, Any] = {}
    parsed_jsonl: dict[Path, list[dict[str, Any]]] = {}
    candidates = [
        *REPO.glob("*.json"), *REPO.glob("agents/**/*.json"),
        *REPO.glob("agents/**/*.jsonl"), *REPO.glob("foundations/*.json"),
        *REPO.glob("graph/*.json"),
    ]
    for path in sorted(set(candidates)):
        try:
            if path.suffix == ".jsonl":
                parsed_jsonl[path] = load_jsonl(path)
            else:
                parsed_json[path] = load_json(path)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"parse: {exc}")

    agents: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted(REPO.glob("agents/*/agent.json")):
        manifest = parsed_json.get(manifest_path)
        if not isinstance(manifest, dict):
            continue
        agent_id = manifest.get("agent", {}).get("id")
        if not agent_id:
            errors.append(f"manifest missing agent.id: {manifest_path.relative_to(REPO)}")
            continue
        if agent_id in agents:
            errors.append(f"duplicate agent id: {agent_id}")
        agents[agent_id] = manifest
        for relative in collect_paths(manifest):
            if not (REPO / relative).exists():
                errors.append(f"manifest path missing: {relative}")

    known_hashes: dict[str, str] = {}
    for path, document in parsed_json.items():
        if path.name not in {"source-hashes.json", "artifact-hashes.json"} or not isinstance(document, dict):
            continue
        if document.get("algorithm") != "sha256":
            errors.append(f"unsupported hash algorithm: {path.relative_to(REPO)}")
        for relative, expected in document.get("hashes", {}).items():
            artifact = REPO / relative
            if not artifact.is_file():
                errors.append(f"hashed artifact missing: {relative}")
                continue
            actual = sha256(artifact)
            known_hashes[relative] = actual
            if actual != expected:
                errors.append(f"source hash mismatch: {relative}")

    anchors: dict[str, dict[str, Any]] = {}
    statements: dict[str, dict[str, Any]] = {}
    steps: dict[str, dict[str, Any]] = {}
    verifications: dict[str, dict[str, Any]] = {}
    import_matches: dict[str, dict[str, Any]] = {}
    for path, records in parsed_jsonl.items():
        for record in records:
            record_id = record.get("id")
            if not record_id:
                errors.append(f"record missing id: {path.relative_to(REPO)}")
                continue
            index = None
            if path.name == "anchors.jsonl": index = anchors
            elif path.name == "statements.jsonl": index = statements
            elif path.name == "chains.jsonl": index = steps
            elif path.name == "records.jsonl": index = verifications
            elif path.name == "import-matches.jsonl": index = import_matches
            if index is not None:
                if record_id in index:
                    errors.append(f"duplicate id: {record_id}")
                index[record_id] = record

    for anchor_id, anchor in anchors.items():
        relative = anchor.get("artifact")
        artifact = REPO / str(relative)
        expected_artifact = str(anchor.get("artifact_hash", "")).removeprefix("sha256:")
        actual_artifact = known_hashes.get(str(relative))
        if actual_artifact is None:
            errors.append(f"{anchor_id}: artifact not in source-hashes.json: {relative}")
        elif actual_artifact != expected_artifact:
            errors.append(f"{anchor_id}: anchor artifact hash mismatch")
        content_hash = anchor.get("content_hash")
        location = anchor.get("location", {})
        if content_hash:
            start, end = location.get("line_start"), location.get("line_end")
            if not isinstance(start, int) or not isinstance(end, int) or start > end:
                errors.append(f"{anchor_id}: invalid content-hash line range")
            elif artifact.is_file():
                actual = line_hash(artifact, start, end)
                expected = str(content_hash).removeprefix("sha256:")
                if actual != expected:
                    errors.append(f"{anchor_id}: content hash mismatch")

    foundations: dict[str, dict[str, Any]] = {}
    foundation_statements: dict[str, dict[str, Any]] = {}
    for path, document in parsed_json.items():
        if path.parent == REPO / "foundations" and isinstance(document, dict):
            if document.get("id"): foundations[document["id"]] = document
            if document.get("statement_id"): foundation_statements[document["statement_id"]] = document

    contracts: dict[str, dict[str, Any]] = {}
    blockers: dict[str, dict[str, Any]] = {}
    for document in parsed_json.values():
        if not isinstance(document, dict) or not document.get("id"):
            continue
        record_id = document["id"]
        if record_id.startswith("contract:"): contracts[record_id] = document
        elif record_id.startswith("blocker:"): blockers[record_id] = document

    claim_ids = set(statements) | set(foundation_statements)
    for statement_id, statement in statements.items():
        for anchor_id in statement.get("source_anchors", []):
            if anchor_id not in anchors:
                errors.append(f"{statement_id}: unknown source anchor {anchor_id}")
        for hypothesis in statement.get("logical_form", {}).get("hypotheses", []):
            if hypothesis not in claim_ids:
                errors.append(f"{statement_id}: unknown hypothesis {hypothesis}")

    for step_id, step in steps.items():
        for claim_id in step.get("inputs", []) + step.get("outputs", []):
            if claim_id not in claim_ids:
                errors.append(f"{step_id}: unknown claim {claim_id}")
        for anchor_id in step.get("source_anchors", []):
            if anchor_id not in anchors:
                errors.append(f"{step_id}: unknown source anchor {anchor_id}")
        for verification_id in step.get("verification_records", []):
            if verification_id not in verifications:
                errors.append(f"{step_id}: unknown verification {verification_id}")
        for assumption in step.get("active_assumptions", []):
            if assumption not in claim_ids:
                errors.append(f"{step_id}: unknown active assumption {assumption}")

    for contract_id, contract in contracts.items():
        if contract.get("statement") not in claim_ids:
            errors.append(f"{contract_id}: unknown exported statement {contract.get('statement')}")
        for assumption in contract.get("assumptions", []):
            if isinstance(assumption, str) and assumption.startswith("assumption:") and assumption not in claim_ids:
                errors.append(f"{contract_id}: unknown assumption {assumption}")
        for imported in contract.get("imports", []):
            imported_id = imported.get("contract") if isinstance(imported, dict) else imported
            if imported_id not in contracts and imported_id not in foundation_statements:
                errors.append(f"{contract_id}: unknown import {imported_id}")
        for blocker_id in contract.get("blockers", []):
            if blocker_id not in blockers:
                errors.append(f"{contract_id}: unknown blocker {blocker_id}")
        accepted = contract.get("accepted") is True
        lifecycle = contract.get("lifecycle_status")
        if accepted and lifecycle not in {"VERIFIED", "VERIFICATION_CLOSED"}:
            errors.append(f"{contract_id}: accepted export lacks closed lifecycle status")
        if not accepted:
            warnings.append(f"unaccepted export: {contract_id} ({lifecycle})")

    graph = parsed_json.get(REPO / "graph/claim-dependencies.json", {})
    graph_nodes = set(graph.get("nodes", []))
    graph_edges = graph.get("edges", [])
    for node in graph_nodes:
        if node not in claim_ids:
            errors.append(f"claim graph: unknown node {node}")
    for edge in graph_edges:
        source, target, step_id = edge.get("from"), edge.get("to"), edge.get("via_step")
        if source not in graph_nodes or target not in graph_nodes:
            errors.append(f"claim graph: undeclared endpoint: {edge}")
        step = steps.get(step_id)
        if step is None:
            errors.append(f"claim graph: unknown step {step_id}")
        elif source not in step.get("inputs", []) or target not in step.get("outputs", []):
            errors.append(f"claim graph: edge does not match {step_id}: {source} -> {target}")
    if has_cycle(graph_nodes, graph_edges):
        errors.append("claim graph contains a cycle")

    open_blockers = sorted(record_id for record_id, record in blockers.items() if record.get("status") == "OPEN")
    warnings.extend(f"open blocker: {record_id}" for record_id in open_blockers)
    unaccepted = sorted(contract_id for contract_id, contract in contracts.items() if contract.get("accepted") is not True)
    result = {
        "schema_version": "0.1.0-prototype",
        "structural_validation": "PASSED" if not errors else "FAILED",
        "scientific_release_gate": "BLOCKED" if open_blockers or unaccepted else "PASSED",
        "counts": {
            "agents": len(agents), "artifacts_hashed": len(known_hashes),
            "anchors": len(anchors), "statements_and_assumptions": len(statements),
            "foundations": len(foundations), "reasoning_steps": len(steps),
            "verification_records": len(verifications), "contracts": len(contracts),
            "open_blockers": len(open_blockers),
        },
        "errors": errors,
        "warnings": warnings,
        "strict_science_requested": args.strict_science,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if errors or (args.strict_science and (open_blockers or unaccepted)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
