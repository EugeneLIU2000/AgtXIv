#!/usr/bin/env python3
"""Validate AgtXIv Query Run manifests without mutating repository data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DATABASE_DIR.parent
SCHEMA_PATH = DATABASE_DIR / "schemas" / "query-run-dataset.schema.json"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ARTIFACT_ID_RE = re.compile(r"^artifact:sha256:([0-9a-f]{64})$")
NAMESPACED_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]+$")

TOP_LEVEL_KEYS = {
    "schema",
    "dataset_id",
    "captured_at",
    "description",
    "paper_versions",
    "query",
    "run",
    "run_artifacts",
    "provenance_edges",
    "knowledge_records",
    "audit",
}
REQUIRED_TOP_LEVEL_KEYS = TOP_LEVEL_KEYS - {"description"}

PAPER_ROLES = {"TARGET", "DEPENDENCY", "BACKGROUND"}
RUN_STATES = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "UNKNOWN"}
RUN_OUTCOMES = {"SUCCEEDED", "REJECTED", "BLOCKED", "FAILED_TO_RUN"}
ARTIFACT_ROLES = {"INPUT", "INTERMEDIATE", "OUTPUT", "EVIDENCE", "LOG"}
STORAGE_CLASSES = {"SOURCE", "RUN", "KNOWLEDGE", "DERIVED"}
AUTHORITIES = {
    "AUTHORITATIVE_SOURCE",
    "AUTHORITATIVE_RECORD",
    "LEGACY_RECORD",
    "DERIVED",
    "STAGING",
}
PUBLICATION_STATES = {"FROZEN", "STAGING", "PUBLISHED", "SUPERSEDED"}
PROVENANCE_RELATIONS = {
    "CONSUMED_BY",
    "DERIVED_FROM",
    "EVIDENCES",
    "BLOCKS",
    "SUMMARIZED_BY",
    "MIGRATED_TO",
    "NORMALIZED_AS",
    "PACKAGED_BY",
    "SUPERSEDES",
    "REFERENCES",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return value.endswith("Z") or "+" in value[10:]


def is_id(value: Any) -> bool:
    return isinstance(value, str) and bool(NAMESPACED_ID_RE.fullmatch(value))


def require_keys(record: Any, required: set[str], context: str, errors: list[str]) -> bool:
    if not isinstance(record, dict):
        errors.append(f"{context}: expected object")
        return False
    missing = sorted(required - set(record))
    if missing:
        errors.append(f"{context}: missing keys {missing}")
        return False
    return True


def unique(values: Iterable[str], context: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            errors.append(f"{context}: duplicate value {value}")
        seen.add(value)


def resolve_repo_path(raw_path: Any, context: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        errors.append(f"{context}: path must be a non-empty string")
        return None
    pure = PurePosixPath(raw_path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in raw_path:
        errors.append(f"{context}: unsafe repository-relative path {raw_path!r}")
        return None
    resolved = (REPO_ROOT / Path(*pure.parts)).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        errors.append(f"{context}: path escapes repository root: {raw_path!r}")
        return None
    return resolved


def validate_manifest(path: Path, verify_hashes: bool = True) -> list[str]:
    errors: list[str] = []
    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: cannot read JSON: {exc}"]

    if not require_keys(data, REQUIRED_TOP_LEVEL_KEYS, "manifest", errors):
        return errors
    extra = sorted(set(data) - TOP_LEVEL_KEYS)
    if extra:
        errors.append(f"manifest: unknown top-level keys {extra}")
    if data.get("schema") != "agtxiv.query-run-dataset/0.1.0":
        errors.append("manifest.schema: expected agtxiv.query-run-dataset/0.1.0")
    if not is_id(data.get("dataset_id")):
        errors.append("manifest.dataset_id: invalid namespaced ID")
    if not is_timestamp(data.get("captured_at")):
        errors.append("manifest.captured_at: expected an ISO 8601 timestamp with timezone")

    papers = data.get("paper_versions")
    if not isinstance(papers, list) or not papers:
        errors.append("paper_versions: expected a non-empty array")
        papers = []
    paper_ids: list[str] = []
    work_ids: list[str] = []
    paper_source_ids: list[str] = []
    for index, paper in enumerate(papers):
        context = f"paper_versions[{index}]"
        required = {
            "work_id",
            "paper_version_id",
            "title",
            "role",
            "primary_source_artifact_id",
            "source_artifact_ids",
            "source_bundle_complete",
        }
        if not require_keys(paper, required, context, errors):
            continue
        if set(paper) != required:
            errors.append(f"{context}: unknown keys {sorted(set(paper) - required)}")
        for field in ("work_id", "paper_version_id"):
            if not is_id(paper.get(field)):
                errors.append(f"{context}.{field}: invalid namespaced ID")
        if not isinstance(paper.get("title"), str) or not paper["title"].strip():
            errors.append(f"{context}.title: expected non-empty text")
        if paper.get("role") not in PAPER_ROLES:
            errors.append(f"{context}.role: invalid value {paper.get('role')!r}")
        primary_source_id = paper.get("primary_source_artifact_id")
        if not ARTIFACT_ID_RE.fullmatch(str(primary_source_id or "")):
            errors.append(f"{context}.primary_source_artifact_id: invalid artifact ID")
        source_ids = paper.get("source_artifact_ids")
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(f"{context}.source_artifact_ids: expected a non-empty array")
            source_ids = []
        for source_id in source_ids:
            if not ARTIFACT_ID_RE.fullmatch(str(source_id)):
                errors.append(f"{context}.source_artifact_ids: invalid artifact ID {source_id!r}")
        unique([str(value) for value in source_ids], f"{context}.source_artifact_ids", errors)
        if primary_source_id not in source_ids:
            errors.append(f"{context}: primary_source_artifact_id must occur in source_artifact_ids")
        if not isinstance(paper.get("source_bundle_complete"), bool):
            errors.append(f"{context}.source_bundle_complete: expected boolean")
        paper_ids.append(str(paper.get("paper_version_id")))
        work_ids.append(str(paper.get("work_id")))
        paper_source_ids.extend(str(value) for value in source_ids)
    unique(paper_ids, "paper_versions.paper_version_id", errors)

    query = data.get("query")
    query_required = {
        "query_id",
        "raw_text",
        "normalized_text",
        "fingerprint_sha256",
        "target_refs",
        "scope_artifact_id",
    }
    if not require_keys(query, query_required, "query", errors):
        query = {}
    elif set(query) != query_required:
        errors.append(f"query: unknown keys {sorted(set(query) - query_required)}")
    if query:
        if not is_id(query.get("query_id")):
            errors.append("query.query_id: invalid namespaced ID")
        for field in ("raw_text", "normalized_text"):
            if not isinstance(query.get(field), str) or not query[field].strip():
                errors.append(f"query.{field}: expected non-empty text")
        if not SHA256_RE.fullmatch(str(query.get("fingerprint_sha256", ""))):
            errors.append("query.fingerprint_sha256: invalid SHA-256")
        targets = query.get("target_refs")
        if not isinstance(targets, list) or not targets:
            errors.append("query.target_refs: expected a non-empty array")
            targets = []
        for target in targets:
            if not is_id(target):
                errors.append(f"query.target_refs: invalid ID {target!r}")
        unique([str(value) for value in targets], "query.target_refs", errors)
        if not ARTIFACT_ID_RE.fullmatch(str(query.get("scope_artifact_id", ""))):
            errors.append("query.scope_artifact_id: invalid artifact ID")

    run = data.get("run")
    run_required = {
        "run_id",
        "query_id",
        "attempt",
        "execution_state",
        "outcome",
        "captured_at",
        "producer",
        "code_commit",
        "working_tree_state",
        "command",
        "reproducibility_refs",
        "input_snapshot_ref",
        "idempotency_key_sha256",
        "retry_of_run_id",
    }
    if not require_keys(run, run_required, "run", errors):
        run = {}
    elif set(run) != run_required:
        errors.append(f"run: unknown keys {sorted(set(run) - run_required)}")
    if run:
        if not is_id(run.get("run_id")):
            errors.append("run.run_id: invalid namespaced ID")
        if run.get("query_id") != query.get("query_id"):
            errors.append("run.query_id: must equal query.query_id")
        if not isinstance(run.get("attempt"), int) or isinstance(run.get("attempt"), bool) or run["attempt"] < 1:
            errors.append("run.attempt: expected integer >= 1")
        if run.get("execution_state") not in RUN_STATES:
            errors.append(f"run.execution_state: invalid value {run.get('execution_state')!r}")
        if run.get("outcome") not in RUN_OUTCOMES:
            errors.append(f"run.outcome: invalid value {run.get('outcome')!r}")
        if not is_timestamp(run.get("captured_at")):
            errors.append("run.captured_at: expected an ISO 8601 timestamp with timezone")
        producer = run.get("producer")
        producer_required = {"implementation", "version", "implementation_hash"}
        if require_keys(producer, producer_required, "run.producer", errors):
            if set(producer) != producer_required:
                errors.append(f"run.producer: unknown keys {sorted(set(producer) - producer_required)}")
            if not isinstance(producer.get("implementation"), str) or not producer["implementation"].strip():
                errors.append("run.producer.implementation: expected non-empty text")
            if not isinstance(producer.get("version"), str) or not producer["version"].strip():
                errors.append("run.producer.version: expected non-empty text")
            implementation_hash = producer.get("implementation_hash")
            if implementation_hash is not None and not SHA256_RE.fullmatch(str(implementation_hash)):
                errors.append("run.producer.implementation_hash: invalid SHA-256")
        if not re.fullmatch(r"[0-9a-f]{40}", str(run.get("code_commit", ""))):
            errors.append("run.code_commit: expected a 40-character Git commit")
        if run.get("working_tree_state") not in {"CLEAN", "DIRTY", "UNKNOWN"}:
            errors.append("run.working_tree_state: invalid value")
        if not isinstance(run.get("command"), list) or not all(
            isinstance(value, str) and value for value in run.get("command", [])
        ):
            errors.append("run.command: expected an array of non-empty strings")
        reproducibility = run.get("reproducibility_refs")
        reproducibility_fields = {"configuration", "prompts", "models", "tools", "formal_environments"}
        if require_keys(reproducibility, reproducibility_fields, "run.reproducibility_refs", errors):
            if set(reproducibility) != reproducibility_fields:
                errors.append(
                    "run.reproducibility_refs: unknown keys "
                    f"{sorted(set(reproducibility) - reproducibility_fields)}"
                )
            for field in sorted(reproducibility_fields):
                values = reproducibility.get(field)
                if not isinstance(values, list) or not all(is_id(value) for value in values):
                    errors.append(f"run.reproducibility_refs.{field}: expected namespaced IDs")
                    continue
                unique(values, f"run.reproducibility_refs.{field}", errors)
        for field in ("input_snapshot_ref", "retry_of_run_id"):
            value = run.get(field)
            if value is not None and not is_id(value):
                errors.append(f"run.{field}: invalid namespaced ID")
        idempotency_key = run.get("idempotency_key_sha256")
        if idempotency_key is not None and not SHA256_RE.fullmatch(str(idempotency_key)):
            errors.append("run.idempotency_key_sha256: invalid SHA-256")

    artifacts = data.get("run_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("run_artifacts: expected a non-empty array")
        artifacts = []
    artifact_ids: list[str] = []
    artifact_by_id: dict[str, dict[str, Any]] = {}
    artifact_required = {
        "artifact_id",
        "kind",
        "role",
        "storage_class",
        "authority",
        "publication_state",
        "path",
        "media_type",
        "sha256",
        "byte_size",
        "schema_name",
        "schema_version",
        "source_refs",
    }
    for index, artifact in enumerate(artifacts):
        context = f"run_artifacts[{index}]"
        if not require_keys(artifact, artifact_required, context, errors):
            continue
        if set(artifact) != artifact_required:
            errors.append(f"{context}: unknown keys {sorted(set(artifact) - artifact_required)}")
        artifact_id = artifact.get("artifact_id")
        match = ARTIFACT_ID_RE.fullmatch(str(artifact_id))
        if not match:
            errors.append(f"{context}.artifact_id: invalid content-addressed artifact ID")
        if not SHA256_RE.fullmatch(str(artifact.get("sha256", ""))):
            errors.append(f"{context}.sha256: invalid SHA-256")
        elif match and match.group(1) != artifact.get("sha256"):
            errors.append(f"{context}: artifact ID digest does not equal sha256 field")
        if artifact.get("role") not in ARTIFACT_ROLES:
            errors.append(f"{context}.role: invalid value {artifact.get('role')!r}")
        if artifact.get("storage_class") not in STORAGE_CLASSES:
            errors.append(f"{context}.storage_class: invalid value")
        if artifact.get("authority") not in AUTHORITIES:
            errors.append(f"{context}.authority: invalid value")
        if artifact.get("publication_state") not in PUBLICATION_STATES:
            errors.append(f"{context}.publication_state: invalid value")
        if not isinstance(artifact.get("kind"), str) or not re.fullmatch(r"[a-z][a-z0-9._-]+", artifact["kind"]):
            errors.append(f"{context}.kind: invalid lower-case kind")
        if not isinstance(artifact.get("media_type"), str) or "/" not in artifact["media_type"]:
            errors.append(f"{context}.media_type: expected an Internet media type")
        if not isinstance(artifact.get("byte_size"), int) or isinstance(artifact.get("byte_size"), bool) or artifact["byte_size"] < 0:
            errors.append(f"{context}.byte_size: expected integer >= 0")
        for field in ("schema_name", "schema_version"):
            if artifact.get(field) is not None and not isinstance(artifact[field], str):
                errors.append(f"{context}.{field}: expected string or null")
        source_refs = artifact.get("source_refs")
        if not isinstance(source_refs, list) or not all(is_id(value) for value in source_refs):
            errors.append(f"{context}.source_refs: expected namespaced IDs")
            source_refs = []
        unique([str(value) for value in source_refs], f"{context}.source_refs", errors)

        resolved = resolve_repo_path(artifact.get("path"), context, errors)
        if resolved is not None:
            if not resolved.is_file():
                errors.append(f"{context}: artifact path does not exist or is not a file: {artifact.get('path')}")
            elif verify_hashes:
                actual_size = resolved.stat().st_size
                if actual_size != artifact.get("byte_size"):
                    errors.append(f"{context}: byte_size {artifact.get('byte_size')} != actual {actual_size}")
                actual_hash = sha256_file(resolved)
                if actual_hash != artifact.get("sha256"):
                    errors.append(f"{context}: sha256 {artifact.get('sha256')} != actual {actual_hash}")
        artifact_ids.append(str(artifact_id))
        if isinstance(artifact_id, str):
            artifact_by_id[artifact_id] = artifact
    unique(artifact_ids, "run_artifacts.artifact_id", errors)

    for source_id in paper_source_ids:
        if source_id not in artifact_by_id:
            errors.append(f"paper_versions: unresolved source artifact {source_id}")
        elif artifact_by_id[source_id].get("storage_class") != "SOURCE":
            errors.append(f"paper_versions: source artifact {source_id} is not storage_class SOURCE")
    if query and query.get("scope_artifact_id") not in artifact_by_id:
        errors.append(f"query: unresolved scope_artifact_id {query.get('scope_artifact_id')}")
    reproducibility = run.get("reproducibility_refs", {}) if isinstance(run, dict) else {}
    if isinstance(reproducibility, dict):
        for category, refs in reproducibility.items():
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if isinstance(ref, str) and ref.startswith("artifact:sha256:") and ref not in artifact_by_id:
                    errors.append(f"run.reproducibility_refs.{category}: unresolved artifact {ref}")

    if query and query.get("scope_artifact_id") in artifact_by_id:
        scope_sha = artifact_by_id[query["scope_artifact_id"]]["sha256"]
        fingerprint_input = {
            "normalized_text": query["normalized_text"],
            "scope_sha256": scope_sha,
            "target_refs": query["target_refs"],
        }
        canonical = json.dumps(
            fingerprint_input,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        expected = hashlib.sha256(canonical).hexdigest()
        if expected != query.get("fingerprint_sha256"):
            errors.append(
                f"query.fingerprint_sha256: expected {expected} from normalized query, scope hash, and target refs"
            )

    knowledge = data.get("knowledge_records")
    if not isinstance(knowledge, list):
        errors.append("knowledge_records: expected an array")
        knowledge = []
    knowledge_keys: list[str] = []
    knowledge_ids: set[str] = set()
    knowledge_by_key: dict[tuple[str, int], dict[str, Any]] = {}
    supersession_refs: list[tuple[tuple[str, int], tuple[str, int], str]] = []
    knowledge_required = {
        "object_id",
        "revision",
        "kind",
        "artifact_id",
        "content_hash",
        "supersedes",
        "record_locator",
    }
    for index, record in enumerate(knowledge):
        context = f"knowledge_records[{index}]"
        if not require_keys(record, knowledge_required, context, errors):
            continue
        if set(record) != knowledge_required:
            errors.append(f"{context}: unknown keys {sorted(set(record) - knowledge_required)}")
        if not is_id(record.get("object_id")):
            errors.append(f"{context}.object_id: invalid namespaced ID")
        if not isinstance(record.get("revision"), int) or isinstance(record.get("revision"), bool) or record["revision"] < 1:
            errors.append(f"{context}.revision: expected integer >= 1")
        if not isinstance(record.get("kind"), str) or not re.fullmatch(r"[A-Z][A-Z0-9_]+", record["kind"]):
            errors.append(f"{context}.kind: invalid upper-case kind")
        if record.get("artifact_id") not in artifact_by_id:
            errors.append(f"{context}: unresolved artifact_id {record.get('artifact_id')}")
        if not SHA256_RE.fullmatch(str(record.get("content_hash", ""))):
            errors.append(f"{context}.content_hash: invalid SHA-256")
        supersedes = record.get("supersedes")
        if supersedes is not None:
            supersedes_fields = {"object_id", "revision", "content_hash"}
            if require_keys(supersedes, supersedes_fields, f"{context}.supersedes", errors):
                if set(supersedes) != supersedes_fields:
                    errors.append(
                        f"{context}.supersedes: unknown keys {sorted(set(supersedes) - supersedes_fields)}"
                    )
                if supersedes.get("object_id") != record.get("object_id"):
                    errors.append(f"{context}.supersedes.object_id: must equal object_id")
                previous_revision = supersedes.get("revision")
                if (
                    not isinstance(previous_revision, int)
                    or isinstance(previous_revision, bool)
                    or previous_revision < 1
                    or not isinstance(record.get("revision"), int)
                    or previous_revision >= record["revision"]
                ):
                    errors.append(f"{context}.supersedes.revision: must be an earlier positive revision")
                if not SHA256_RE.fullmatch(str(supersedes.get("content_hash", ""))):
                    errors.append(f"{context}.supersedes.content_hash: invalid SHA-256")
                if (
                    isinstance(previous_revision, int)
                    and not isinstance(previous_revision, bool)
                    and isinstance(record.get("revision"), int)
                    and not isinstance(record.get("revision"), bool)
                ):
                    current_key = (str(record.get("object_id")), record["revision"])
                    target_key = (str(supersedes.get("object_id")), previous_revision)
                    supersession_refs.append((current_key, target_key, str(supersedes.get("content_hash"))))
        locator = record.get("record_locator")
        locator_fields = {"format", "id_field", "id_value"}
        if require_keys(locator, locator_fields, f"{context}.record_locator", errors):
            if set(locator) != locator_fields:
                errors.append(
                    f"{context}.record_locator: unknown keys {sorted(set(locator) - locator_fields)}"
                )
            if locator.get("format") not in {"JSON", "JSONL"}:
                errors.append(f"{context}.record_locator.format: invalid value")
            if not isinstance(locator.get("id_field"), str) or not locator["id_field"]:
                errors.append(f"{context}.record_locator.id_field: expected non-empty text")
            if locator.get("id_value") != record.get("object_id"):
                errors.append(f"{context}.record_locator.id_value: must equal object_id")
            artifact = artifact_by_id.get(record.get("artifact_id"))
            artifact_path = None
            if artifact is not None:
                artifact_path = resolve_repo_path(artifact.get("path"), f"{context}.artifact", errors)
            if artifact_path is not None and artifact_path.is_file():
                try:
                    if locator.get("format") == "JSONL":
                        candidates = [
                            json.loads(line)
                            for line in artifact_path.read_text(encoding="utf-8").splitlines()
                            if line.strip()
                        ]
                    else:
                        payload = read_json(artifact_path)
                        candidates = payload if isinstance(payload, list) else [payload]
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f"{context}.record_locator: cannot parse record artifact: {exc}")
                    candidates = []
                matches = [
                    candidate
                    for candidate in candidates
                    if isinstance(candidate, dict)
                    and candidate.get(locator.get("id_field")) == locator.get("id_value")
                ]
                if len(matches) != 1:
                    errors.append(
                        f"{context}.record_locator: expected exactly one record, found {len(matches)}"
                    )
                else:
                    embedded_hash = matches[0].get("semantic_content_hash", matches[0].get("content_hash"))
                    if isinstance(embedded_hash, str) and embedded_hash.startswith("sha256:"):
                        embedded_hash = embedded_hash.removeprefix("sha256:")
                    if embedded_hash != record.get("content_hash"):
                        errors.append(
                            f"{context}.content_hash: locator record contains {embedded_hash!r}"
                        )
        knowledge_keys.append(f"{record.get('object_id')}@{record.get('revision')}")
        if isinstance(record.get("object_id"), str):
            knowledge_ids.add(record["object_id"])
            if isinstance(record.get("revision"), int):
                knowledge_by_key[(record["object_id"], record["revision"])] = record
    unique(knowledge_keys, "knowledge_records identity", errors)
    for current_key, target_key, expected_hash in supersession_refs:
        target = knowledge_by_key.get(target_key)
        if target is not None and target.get("content_hash") != expected_hash:
            errors.append(
                "knowledge_records supersedes: "
                f"{current_key} pins {target_key} with content hash {expected_hash}, "
                f"but the local record has {target.get('content_hash')}"
            )

    resolvable_refs = (
        set(artifact_ids)
        | set(paper_ids)
        | set(work_ids)
        | set(query.get("target_refs", []))
        | knowledge_ids
    )
    if query.get("query_id"):
        resolvable_refs.add(query["query_id"])
    if run.get("run_id"):
        resolvable_refs.add(run["run_id"])
    for artifact in artifacts:
        if isinstance(artifact, dict):
            resolvable_refs.update(artifact.get("source_refs", []))
    edges = data.get("provenance_edges")
    if not isinstance(edges, list):
        errors.append("provenance_edges: expected an array")
        edges = []
    edge_ids: list[str] = []
    edge_required = {"edge_id", "from_ref", "relation", "to_ref"}
    for index, edge in enumerate(edges):
        context = f"provenance_edges[{index}]"
        if not require_keys(edge, edge_required, context, errors):
            continue
        if set(edge) != edge_required:
            errors.append(f"{context}: unknown keys {sorted(set(edge) - edge_required)}")
        if not is_id(edge.get("edge_id")):
            errors.append(f"{context}.edge_id: invalid namespaced ID")
        if edge.get("relation") not in PROVENANCE_RELATIONS:
            errors.append(f"{context}.relation: invalid value {edge.get('relation')!r}")
        for field in ("from_ref", "to_ref"):
            if not is_id(edge.get(field)):
                errors.append(f"{context}.{field}: invalid namespaced ID")
            elif edge[field] not in resolvable_refs:
                errors.append(f"{context}.{field}: unresolved reference {edge[field]}")
        if edge.get("from_ref") == edge.get("to_ref"):
            errors.append(f"{context}: self-edge is not allowed")
        edge_ids.append(str(edge.get("edge_id")))
    unique(edge_ids, "provenance_edges.edge_id", errors)

    audit = data.get("audit")
    audit_required = {"legacy_capture", "accepted_release", "findings"}
    if require_keys(audit, audit_required, "audit", errors):
        if set(audit) != audit_required:
            errors.append(f"audit: unknown keys {sorted(set(audit) - audit_required)}")
        for field in ("legacy_capture", "accepted_release"):
            if not isinstance(audit.get(field), bool):
                errors.append(f"audit.{field}: expected boolean")
        findings = audit.get("findings")
        if not isinstance(findings, list):
            errors.append("audit.findings: expected an array")
            findings = []
        finding_required = {"severity", "code", "message", "related_refs"}
        for index, finding in enumerate(findings):
            context = f"audit.findings[{index}]"
            if not require_keys(finding, finding_required, context, errors):
                continue
            if set(finding) != finding_required:
                errors.append(f"{context}: unknown keys {sorted(set(finding) - finding_required)}")
            if finding.get("severity") not in {"INFO", "WARNING", "ERROR"}:
                errors.append(f"{context}.severity: invalid value")
            if not isinstance(finding.get("code"), str) or not re.fullmatch(r"[A-Z][A-Z0-9_]+", finding["code"]):
                errors.append(f"{context}.code: invalid upper-case code")
            if not isinstance(finding.get("message"), str) or not finding["message"].strip():
                errors.append(f"{context}.message: expected non-empty text")
            related = finding.get("related_refs")
            if not isinstance(related, list) or not all(is_id(value) for value in related):
                errors.append(f"{context}.related_refs: expected namespaced IDs")
                related = []
            for ref in related:
                if ref not in resolvable_refs:
                    errors.append(f"{context}.related_refs: unresolved reference {ref}")

    return errors


def discover_manifests(include_examples: bool = True) -> list[Path]:
    paths = list((DATABASE_DIR / "runs").glob("**/manifest.json"))
    if include_examples:
        paths.extend((DATABASE_DIR / "examples").glob("**/manifest.json"))
    return sorted(set(path.resolve() for path in paths))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        help="Validate only this manifest; may be repeated.",
    )
    parser.add_argument(
        "--production-only",
        action="store_true",
        help="Skip manifests under database/examples.",
    )
    parser.add_argument(
        "--skip-hashes",
        action="store_true",
        help="Validate structure and references without reading artifact bytes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        read_json(SCHEMA_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR schema: {exc}", file=sys.stderr)
        return 2

    paths = [path.resolve() for path in args.manifest] if args.manifest else discover_manifests(not args.production_only)
    if not paths:
        print("No Query Run manifests found.")
        return 0

    error_count = 0
    for path in paths:
        errors = validate_manifest(path, verify_hashes=not args.skip_hashes)
        try:
            label = path.relative_to(REPO_ROOT)
        except ValueError:
            label = path
        if errors:
            print(f"FAIL {label}")
            for error in errors:
                print(f"  - {error}")
            error_count += len(errors)
        else:
            data = read_json(path)
            print(
                f"OK   {label}: "
                f"{len(data['paper_versions'])} papers, "
                f"{len(data['run_artifacts'])} artifacts, "
                f"{len(data['provenance_edges'])} provenance edges"
            )

    if error_count:
        print(f"Validation failed with {error_count} error(s).", file=sys.stderr)
        return 1
    print(f"Validated {len(paths)} manifest(s); structural validity does not imply scientific acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
