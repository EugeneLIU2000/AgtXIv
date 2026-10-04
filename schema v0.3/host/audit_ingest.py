"""Audit one frozen source extraction's bytes and reference bookkeeping."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from core import digest, utcnow, write_json


def audit(extraction: Path, repo: Path) -> dict:
    raw = extraction.read_bytes()
    report = json.loads(raw)
    sources, errors, span_count = {}, [], 0
    for row in report["source_files"]:
        blob = (extraction.parent / row["blob_path"]).resolve()
        if not blob.is_relative_to(extraction.parent.resolve()):
            errors.append({"code": "BLOB_PATH_ESCAPE", "path": row["blob_path"]})
            continue
        data = blob.read_bytes()
        if len(data) != row["byte_size"] or digest(data) != row["sha256"]:
            errors.append({"code": "BLOB_IDENTITY_MISMATCH", "path": row["path"]})
        if row["path"] in sources:
            errors.append({"code": "DUPLICATE_SOURCE_PATH", "path": row["path"]})
        sources[row["path"]] = data
    source_root = (repo / report["paper"].get("source_root", ".")).resolve()
    for path in sources:
        if not (repo / path).resolve().is_relative_to(source_root):
            errors.append({"code": "SOURCE_OUTSIDE_DECLARED_ROOT", "path": path})

    def spans(value):
        nonlocal span_count
        if isinstance(value, dict):
            if {"path", "sha256", "byte_start", "byte_end", "span_sha256"} <= value.keys():
                span_count += 1
                data = sources.get(value["path"])
                if data is None:
                    errors.append({"code": "SPAN_SOURCE_MISSING", "span": value})
                else:
                    start, end = value["byte_start"], value["byte_end"]
                    valid = type(start) is int and type(end) is int and 0 <= start < end <= len(data)
                    if (not valid or digest(data) != value["sha256"]
                            or digest(data[start:end]) != value["span_sha256"]
                            or value.get("offset_unit") != "BYTE" or value.get("interval") != "HALF_OPEN"):
                        errors.append({"code": "SPAN_IDENTITY_MISMATCH", "span": value})
            for child in value.values():
                spans(child)
        elif isinstance(value, list):
            for child in value:
                spans(child)
    spans(report)
    for kind in ("claims", "bibliography"):
        identifiers = [row["id"] for row in report[kind]]
        if len(identifiers) != len(set(identifiers)):
            errors.append({"code": "DUPLICATE_ROW_ID", "kind": kind})
        for row in report[kind]:
            span = row["source"]
            data = sources.get(span["path"])
            if data is not None and data[span["byte_start"]:span["byte_end"]].decode("utf-8", errors="replace") != row["text"]:
                errors.append({"code": "ROW_TEXT_MISMATCH", "id": row["id"]})
    citation_counts = Counter()
    for anchor in report["anchors"]:
        if not anchor["command"].startswith("cite"):
            continue
        targets = sorted(row["id"] for row in report["bibliography"]
                         if (row["key"], row["bibliography_unit"]) == (anchor["key"], anchor["bibliography_unit"]))
        expected = "RESOLVED_BIBLIOGRAPHY_MENTION" if len(targets) == 1 else "AMBIGUOUS_BIBLIOGRAPHY_KEY" if targets else "UNRESOLVED_BIBLIOGRAPHY_KEY"
        if targets != sorted(anchor["candidate_target_ids"]) or anchor["resolution"] != expected:
            errors.append({"code": "CITATION_TARGET_BOOKKEEPING_MISMATCH", "id": anchor["id"]})
        citation_counts[anchor["resolution"]] += 1
    return {"kind": "FrozenSourceExtractionAudit", "created_at": utcnow(),
            "program_sha256": digest(Path(__file__).read_bytes()),
            "input": {"path": str(extraction.resolve()), "sha256": digest(raw), "byte_size": len(raw)},
            "status": "PASS" if not errors else "FAILED", "errors": errors,
            "source_files": len(sources), "span_references_checked": span_count,
            "occurrences": len(report["claims"]), "bibliography_entries": len(report["bibliography"]),
            "citation_resolutions": dict(citation_counts),
            "scope": "FROZEN_SOURCE_BYTES_ALL_RECORDED_SPANS_ROW_TEXTS_AND_CITATION_TARGET_BOOKKEEPING",
            "limitations": ["Does not prove parsing completeness, semantic identities, scientific support or earliest-source exhaustion.",
                            "Checks frozen blobs; does not treat later mutable source files as the extraction input.",
                            "This is an artifact audit, not an adversarial parser/path/concurrency exercise."],
            "semantic_status": "AWAITING_REVIEW", "mathematical_status": "CHAIN_INCOMPLETE"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Retain previous evidence; choose a fresh audit output")
    result = audit(args.extraction.resolve(), Path(__file__).resolve().parents[2])
    write_json(args.output, result)
    print(json.dumps({key: result[key] for key in ("status", "source_files", "span_references_checked", "occurrences", "bibliography_entries", "citation_resolutions")}))
    raise SystemExit(0 if result["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
