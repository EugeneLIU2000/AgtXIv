#!/usr/bin/env python3
"""Build a disposable SQLite catalog from authoritative Query Run manifests."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from validate_database import DATABASE_DIR, REPO_ROOT, discover_manifests, read_json, validate_manifest


MIGRATION_PATH = DATABASE_DIR / "migrations" / "0001_core.sql"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def insert_or_assert(
    connection: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    values: Sequence[Any],
    key_columns: Sequence[str],
) -> None:
    key_positions = [columns.index(column) for column in key_columns]
    where = " AND ".join(f"{column} = ?" for column in key_columns)
    key_values = tuple(values[position] for position in key_positions)
    row = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}",
        key_values,
    ).fetchone()
    expected = tuple(values)
    if row is None:
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            expected,
        )
    elif tuple(row) != expected:
        identity = ", ".join(f"{name}={value!r}" for name, value in zip(key_columns, key_values))
        raise ValueError(f"conflicting duplicate in {table} for {identity}")


def manifest_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def import_manifest(connection: sqlite3.Connection, path: Path, data: dict[str, Any]) -> None:
    insert_or_assert(
        connection,
        "datasets",
        ("dataset_id", "schema_id", "captured_at", "description", "manifest_path"),
        (
            data["dataset_id"],
            data["schema"],
            data["captured_at"],
            data.get("description"),
            manifest_label(path),
        ),
        ("dataset_id",),
    )

    for paper in data["paper_versions"]:
        insert_or_assert(
            connection,
            "paper_works",
            ("work_id", "title"),
            (paper["work_id"], paper["title"]),
            ("work_id",),
        )
        insert_or_assert(
            connection,
            "paper_versions",
            (
                "paper_version_id",
                "work_id",
                "primary_source_artifact_id",
                "source_artifact_ids_json",
                "source_bundle_complete",
            ),
            (
                paper["paper_version_id"],
                paper["work_id"],
                paper["primary_source_artifact_id"],
                canonical_json(paper["source_artifact_ids"]),
                int(paper["source_bundle_complete"]),
            ),
            ("paper_version_id",),
        )

    query = data["query"]
    insert_or_assert(
        connection,
        "queries",
        (
            "query_id",
            "raw_text",
            "normalized_text",
            "fingerprint_sha256",
            "scope_artifact_id",
            "target_refs_json",
        ),
        (
            query["query_id"],
            query["raw_text"],
            query["normalized_text"],
            query["fingerprint_sha256"],
            query["scope_artifact_id"],
            canonical_json(query["target_refs"]),
        ),
        ("query_id",),
    )
    for paper in data["paper_versions"]:
        insert_or_assert(
            connection,
            "query_papers",
            ("query_id", "paper_version_id", "role"),
            (query["query_id"], paper["paper_version_id"], paper["role"]),
            ("query_id", "paper_version_id"),
        )

    run = data["run"]
    insert_or_assert(
        connection,
        "runs",
        (
            "run_id",
            "dataset_id",
            "query_id",
            "attempt",
            "execution_state",
            "outcome",
            "captured_at",
            "producer_json",
            "code_commit",
            "working_tree_state",
            "command_json",
            "reproducibility_refs_json",
            "input_snapshot_ref",
            "idempotency_key_sha256",
            "retry_of_run_id",
        ),
        (
            run["run_id"],
            data["dataset_id"],
            run["query_id"],
            run["attempt"],
            run["execution_state"],
            run["outcome"],
            run["captured_at"],
            canonical_json(run["producer"]),
            run["code_commit"],
            run["working_tree_state"],
            canonical_json(run["command"]),
            canonical_json(run["reproducibility_refs"]),
            run["input_snapshot_ref"],
            run["idempotency_key_sha256"],
            run["retry_of_run_id"],
        ),
        ("run_id",),
    )

    for artifact in data["run_artifacts"]:
        insert_or_assert(
            connection,
            "artifacts",
            (
                "artifact_id",
                "kind",
                "media_type",
                "sha256",
                "byte_size",
            ),
            (
                artifact["artifact_id"],
                artifact["kind"],
                artifact["media_type"],
                artifact["sha256"],
                artifact["byte_size"],
            ),
            ("artifact_id",),
        )
        insert_or_assert(
            connection,
            "run_artifacts",
            (
                "run_id",
                "artifact_id",
                "role",
                "storage_class",
                "authority",
                "publication_state",
                "repo_path",
                "schema_name",
                "schema_version",
                "source_refs_json",
            ),
            (
                run["run_id"],
                artifact["artifact_id"],
                artifact["role"],
                artifact["storage_class"],
                artifact["authority"],
                artifact["publication_state"],
                artifact["path"],
                artifact["schema_name"],
                artifact["schema_version"],
                canonical_json(artifact["source_refs"]),
            ),
            ("run_id", "artifact_id"),
        )

    for edge in data["provenance_edges"]:
        insert_or_assert(
            connection,
            "provenance_edges",
            ("edge_id", "run_id", "from_ref", "relation", "to_ref"),
            (edge["edge_id"], run["run_id"], edge["from_ref"], edge["relation"], edge["to_ref"]),
            ("edge_id",),
        )

    for record in data["knowledge_records"]:
        supersedes = record["supersedes"]
        insert_or_assert(
            connection,
            "knowledge_records",
            (
                "object_id",
                "revision",
                "kind",
                "artifact_id",
                "content_hash",
                "supersedes_object_id",
                "supersedes_revision",
                "supersedes_content_hash",
                "record_locator_json",
            ),
            (
                record["object_id"],
                record["revision"],
                record["kind"],
                record["artifact_id"],
                record["content_hash"],
                supersedes["object_id"] if supersedes else None,
                supersedes["revision"] if supersedes else None,
                supersedes["content_hash"] if supersedes else None,
                canonical_json(record["record_locator"]),
            ),
            ("object_id", "revision"),
        )

    for ordinal, finding in enumerate(data["audit"]["findings"], start=1):
        insert_or_assert(
            connection,
            "audit_findings",
            ("dataset_id", "ordinal", "severity", "code", "message", "related_refs_json"),
            (
                data["dataset_id"],
                ordinal,
                finding["severity"],
                finding["code"],
                finding["message"],
                canonical_json(finding["related_refs"]),
            ),
            ("dataset_id", "ordinal"),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Path for the generated SQLite catalog.")
    parser.add_argument(
        "--include-examples",
        action="store_true",
        help="Also ingest non-authoritative fixtures under database/examples.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Explicitly replace an existing generated catalog.",
    )
    parser.add_argument(
        "--skip-hashes",
        action="store_true",
        help="Skip artifact byte hashing before catalog construction.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        if not args.replace:
            print(f"Refusing to overwrite existing catalog: {output}", file=sys.stderr)
            return 2
        if not output.is_file():
            print(f"Output exists and is not a regular file: {output}", file=sys.stderr)
            return 2
        if output.read_bytes()[:16] != b"SQLite format 3\x00":
            print(f"Refusing to replace a file that is not an SQLite database: {output}", file=sys.stderr)
            return 2
        output.unlink()

    manifests = discover_manifests(include_examples=args.include_examples)
    if not manifests:
        print("No Query Run manifests found; use --include-examples for the demo fixture.", file=sys.stderr)
        return 2

    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in manifests:
        errors = validate_manifest(path, verify_hashes=not args.skip_hashes)
        if errors:
            print(f"Cannot index invalid manifest {manifest_label(path)}:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        loaded.append((path, read_json(path)))

    output.parent.mkdir(parents=True, exist_ok=True)
    migration = MIGRATION_PATH.read_text(encoding="utf-8")
    connection = sqlite3.connect(output)
    try:
        connection.executescript(migration)
        with connection:
            connection.execute(
                "INSERT OR REPLACE INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (1, "0001_core", datetime.now(timezone.utc).isoformat()),
            )
            for path, data in loaded:
                import_manifest(connection, path, data)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity_check returned {integrity!r}")
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("datasets", "paper_versions", "queries", "runs", "artifacts", "provenance_edges")
        }
    except Exception:
        connection.close()
        if output.exists():
            output.unlink()
        raise
    finally:
        try:
            connection.close()
        except sqlite3.Error:
            pass

    print(f"Built {output}")
    print(" ".join(f"{name}={count}" for name, count in counts.items()))
    print("Catalog is derived; its successful build does not imply scientific acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
