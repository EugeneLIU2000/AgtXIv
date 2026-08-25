#!/usr/bin/env python3
"""Reproduce and check the frozen arXiv frame for the ScientificClaim study."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STUDY_ROOT = ROOT / "docs/specifications/scientific-claim-interface"
DATA_ROOT = STUDY_ROOT / "data"
POOL_PATH = DATA_ROOT / "candidate_pool.jsonl"
MANIFEST_PATH = DATA_ROOT / "sample_manifest.json"
API_URL = "https://export.arxiv.org/api/query"
WINDOW_START = "2026-08-01T00:00:00Z"
WINDOW_END = "2026-08-25T23:59:00Z"
SEED_TEXT = "AgtXIv-ScientificClaim-interface-2026-08-25-v1"
CATEGORIES = (
    "hep-th",
    "gr-qc",
    "math-ph",
    "quant-ph",
    "cond-mat.stat-mech",
    "hep-ph",
    "nucl-th",
)
STRATA = {
    "qft-particle-nuclear": frozenset(("hep-th", "hep-ph", "nucl-th")),
    "gravity-cosmology": frozenset(("gr-qc",)),
    "mathematical-physics": frozenset(("math-ph",)),
    "quantum-information": frozenset(("quant-ph",)),
    "many-body-statistical": frozenset(("cond-mat.stat-mech",)),
}
FROZEN_POOL_COUNT = 2352
FROZEN_POOL_SHA256 = "sha256:999aae7786744683b71e61d171224d4f98d97e1e01f34a48994a27b221aab8fb"
FROZEN_SELECTED_IDS = (
    "2608.05150",
    "2608.12646",
    "2608.20180",
    "2608.04867",
    "2608.02862",
    "2608.01996",
    "2608.15963",
    "2608.14798",
    "2608.05845",
    "2608.22867",
)
ATOM = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
USER_AGENT = "AgtXIv-ScientificClaim-study/1.0 (https://github.com/AgtXIv/AgtXIv; reproducibility query)"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number}: candidate must be a JSON object")
        rows.append(value)
    return rows


def stable_pool_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    ordered = sorted(rows, key=lambda row: (row["published"], row["id"]))
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered)
    return text.encode("utf-8")


def stratum_for(primary_category: str) -> str | None:
    return next((name for name, categories in STRATA.items() if primary_category in categories), None)


def deterministic_shuffle(rows: Iterable[dict[str, Any]], stratum: str) -> list[dict[str, Any]]:
    """Return a stable, implementation-independent permutation for one stratum."""
    if stratum not in STRATA:
        raise ValueError(f"unknown stratum: {stratum}")

    def shuffle_key(row: dict[str, Any]) -> tuple[bytes, str]:
        material = f"{SEED_TEXT}\0{stratum}\0{row['id']}".encode("utf-8")
        return hashlib.sha256(material).digest(), row["id"]

    members = (row for row in rows if row.get("primary_category") in STRATA[stratum])
    return sorted(members, key=shuffle_key)


def queue_report(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    selected = {item["arxiv_id"] for item in manifest.get("selected", [])}
    excluded = {item["id"] for item in manifest.get("excluded_before_selection", [])}
    report: dict[str, list[dict[str, Any]]] = {}
    for stratum in STRATA:
        queue = deterministic_shuffle(rows, stratum)
        report[stratum] = [
            {"queue_position": position, "id": row["id"], "recorded_decision": "selected" if row["id"] in selected else "excluded" if row["id"] in excluded else None}
            for position, row in enumerate(queue, 1)
            if row["id"] in selected or row["id"] in excluded
        ]
    return report


def validate_frozen(pool_path: Path = POOL_PATH, manifest_path: Path = MANIFEST_PATH) -> list[str]:
    errors: list[str] = []
    try:
        rows = load_jsonl(pool_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    raw_digest = sha256_bytes(pool_path.read_bytes())
    if len(rows) != FROZEN_POOL_COUNT:
        errors.append(f"candidate pool count is {len(rows)}, expected frozen count {FROZEN_POOL_COUNT}")
    if raw_digest != FROZEN_POOL_SHA256:
        errors.append(f"candidate pool digest is {raw_digest}, expected {FROZEN_POOL_SHA256}")
    if manifest.get("pool_size") != len(rows):
        errors.append("manifest pool_size does not match candidate pool")
    if manifest.get("candidate_pool_sha256") != raw_digest:
        errors.append("manifest candidate_pool_sha256 does not match candidate pool")
    if manifest.get("sampling_window", {}).get("start") != WINDOW_START or manifest.get("sampling_window", {}).get("end") != WINDOW_END:
        errors.append("manifest sampling window does not match the frozen frame")
    if tuple(manifest.get("eligible_primary_categories", ())) != CATEGORIES:
        errors.append("manifest primary categories do not match the frozen frame")
    randomization = manifest.get("randomization", {})
    if randomization.get("seed_text") != SEED_TEXT:
        errors.append("manifest randomization seed text does not match")
    if randomization.get("digest") != sha256_bytes(SEED_TEXT.encode("utf-8")):
        errors.append("manifest randomization digest does not match the seed text")

    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("candidate pool contains duplicate IDs")
    if pool_path.read_bytes() != stable_pool_bytes(rows):
        errors.append("candidate pool is not in stable published-time/ID JSONL order")
    start = datetime.fromisoformat(WINDOW_START.replace("Z", "+00:00"))
    end = datetime.fromisoformat(WINDOW_END.replace("Z", "+00:00"))
    for index, row in enumerate(rows, 1):
        category = row.get("primary_category")
        if category not in CATEGORIES:
            errors.append(f"candidate row {index} has ineligible primary category {category!r}")
        try:
            published = datetime.fromisoformat(row["published"].replace("Z", "+00:00"))
        except (KeyError, AttributeError, ValueError):
            errors.append(f"candidate row {index} has invalid published timestamp")
        else:
            if not start <= published <= end:
                errors.append(f"candidate row {index} is outside the first-submission window")

    selected = manifest.get("selected", [])
    selected_ids = tuple(item.get("arxiv_id") for item in selected)
    if selected_ids != FROZEN_SELECTED_IDS:
        errors.append("manifest selected IDs/order differ from the frozen sample")
    by_id = {row.get("id"): row for row in rows}
    for item in selected:
        paper_id = item.get("arxiv_id")
        row = by_id.get(paper_id)
        if row is None:
            errors.append(f"selected paper {paper_id} is absent from candidate pool")
            continue
        if item.get("versioned_id") != f"{paper_id}v1":
            errors.append(f"selected paper {paper_id} is not pinned to v1")
        if item.get("stratum") != stratum_for(row.get("primary_category", "")):
            errors.append(f"selected paper {paper_id} has an incorrect stratum")
    seen_exclusions: set[tuple[str, int]] = set()
    for item in manifest.get("excluded_before_selection", []):
        paper_id, stratum, position = item.get("id"), item.get("stratum"), item.get("queue_position")
        if paper_id not in by_id:
            errors.append(f"pre-selection exclusion {paper_id} is absent from candidate pool")
        elif stratum_for(by_id[paper_id].get("primary_category", "")) != stratum:
            errors.append(f"pre-selection exclusion {paper_id} has an incorrect stratum")
        if not isinstance(position, int) or position < 1:
            errors.append(f"pre-selection exclusion {paper_id} has an invalid queue position")
        elif (stratum, position) in seen_exclusions:
            errors.append(f"duplicate exclusion queue position {stratum}:{position}")
        else:
            seen_exclusions.add((stratum, position))
        if not item.get("reason"):
            errors.append(f"pre-selection exclusion {paper_id} has no reason")
    return errors


def _text(node: ET.Element, path: str) -> str:
    value = node.findtext(path, default="", namespaces=ATOM)
    return " ".join(value.split())


def parse_atom(payload: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    records: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM):
        raw_id = _text(entry, "atom:id").rsplit("/", 1)[-1]
        base_id, separator, version = raw_id.rpartition("v")
        if not separator or not version.isdigit():
            base_id, raw_id = raw_id, raw_id + "v1"
        primary = entry.find("arxiv:primary_category", ATOM)
        categories = [node.attrib["term"] for node in entry.findall("atom:category", ATOM)]
        records.append({
            "authors": [_text(author, "atom:name") for author in entry.findall("atom:author", ATOM)],
            "categories": categories,
            "id": base_id,
            "primary_category": primary.attrib.get("term", "") if primary is not None else "",
            "published": _text(entry, "atom:published"),
            "title": _text(entry, "atom:title"),
            "updated": _text(entry, "atom:updated"),
            "versioned_id": raw_id,
        })
    return records


def retrieve_candidates(rate_limit_seconds: float = 3.0, page_size: int = 500) -> list[dict[str, Any]]:
    collected: dict[str, dict[str, Any]] = {}
    date_range = "submittedDate:[202608010000 TO 202608252359]"
    first_request = True
    for category in CATEGORIES:
        offset = 0
        while True:
            if not first_request:
                time.sleep(rate_limit_seconds)
            first_request = False
            params = urllib.parse.urlencode({
                "search_query": f"cat:{category} AND {date_range}",
                "start": offset,
                "max_results": page_size,
                "sortBy": "submittedDate",
                "sortOrder": "ascending",
            })
            request = urllib.request.Request(f"{API_URL}?{params}", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                page = parse_atom(response.read())
            for row in page:
                if row["primary_category"] == category:
                    collected[row["id"]] = row
            if len(page) < page_size:
                break
            offset += page_size

    start = datetime.fromisoformat(WINDOW_START.replace("Z", "+00:00"))
    end = datetime.fromisoformat(WINDOW_END.replace("Z", "+00:00"))
    return [
        row for row in collected.values()
        if row["primary_category"] in CATEGORIES
        and start <= datetime.fromisoformat(row["published"].replace("Z", "+00:00")) <= end
    ]


def refresh(pool_path: Path = POOL_PATH, manifest_path: Path = MANIFEST_PATH, rate_limit_seconds: float = 3.0) -> list[str]:
    rows = retrieve_candidates(rate_limit_seconds=rate_limit_seconds)
    candidate_bytes = stable_pool_bytes(rows)
    digest = sha256_bytes(candidate_bytes)
    if len(rows) != FROZEN_POOL_COUNT or digest != FROZEN_POOL_SHA256:
        return [
            "refreshed API result differs from the frozen pool; refusing to overwrite it",
            f"retrieved count={len(rows)} digest={digest}",
        ]
    if not pool_path.exists() or pool_path.read_bytes() != candidate_bytes:
        pool_path.write_bytes(candidate_bytes)
    return validate_frozen(pool_path, manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="validate the frozen local pool and manifest without network access")
    action.add_argument("--refresh", action="store_true", help="retrieve the official API frame and compare it with the frozen pool")
    parser.add_argument("--pool", type=Path, default=POOL_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--rate-limit-seconds", type=float, default=3.0)
    parser.add_argument("--show-queue", action="store_true", help="print selected/excluded positions in the reproducible per-stratum queues")
    args = parser.parse_args()
    errors = refresh(args.pool, args.manifest, args.rate_limit_seconds) if args.refresh else validate_frozen(args.pool, args.manifest)
    for error in errors:
        print(f"ERROR: {error}")
    if args.show_queue and not errors:
        rows = load_jsonl(args.pool)
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        print(json.dumps(queue_report(rows, manifest), indent=2, sort_keys=True))
    print(f"claim-interface sampling check: errors={len(errors)} network={'yes' if args.refresh else 'no'}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
