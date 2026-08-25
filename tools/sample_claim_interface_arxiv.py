#!/usr/bin/env python3
"""Check the frozen arXiv frame and purposive ScientificClaim stress-test sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterable
from datetime import datetime
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
FROZEN_SOURCE_SHA256 = {
    "2608.05150": "sha256:ec88c5d70f0dd218f0761cc470c98879c8fbff7a6b4ba0c604949ddb390c24d9",
    "2608.12646": "sha256:ceda584f42416aa4d024913e307e91fc29ec2d17a0da9dbcafd4ad905483e605",
    "2608.20180": "sha256:9fce9de2adb839829928d4cb4f82aca19b7710f21a5a0f23da10871f93e58611",
    "2608.04867": "sha256:70e6bec186ce0d831f4bc8130e2efd0faabc8c173cbe5e4b2ea688c36abb5002",
    "2608.02862": "sha256:93827c1d67bba685a09886853df47822e88e62c436f526bda64f61f3e10ff9df",
    "2608.01996": "sha256:ecea1d235d049c949068700a282b6dc0e4d9bde7ea0fd8d7f1b142c8fc394086",
    "2608.15963": "sha256:4805fdb1c4eed5382aea8ed0e8f28d8419235a918a2af52c3c69408d5ba45859",
    "2608.14798": "sha256:3e3c04d827872466db57b58fe70ad9d5d61c8d141056ca25f82581ac14aa0d52",
    "2608.05845": "sha256:c6e39b5ea5e7c83debc30ffc053dd96d04fce92c1b24eda4c5ee14d7a1a98063",
    "2608.22867": "sha256:47337f57434318a90e0109edf2b9d25fd8597fcdeffeccf258235d566864de6c",
}
DOCUMENTED_EXCLUSION_IDS = frozenset(("2608.02735", "2608.14308"))
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
    if manifest.get("schema") != "agtxiv.claim-interface-sample/1.1.0":
        errors.append("manifest does not use the purposive-sample contract version")
    if "randomization" in manifest or "excluded_before_selection" in manifest:
        errors.append("manifest contains a retired selection-lineage field")

    selection_design = manifest.get("selection_design", {})
    if selection_design.get("type") != "stratified_purposive_stress_test":
        errors.append("manifest selection_design type is not stratified_purposive_stress_test")
    if selection_design.get("probability_sample") is not False:
        errors.append("manifest must state that this is not a probability sample")
    for field in ("candidate_pool_status", "selection_method", "lineage_scope"):
        if not selection_design.get(field):
            errors.append(f"manifest selection_design has no {field}")

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
        errors.append("manifest selected IDs/order differ from the frozen purposive sample")
    if len(selected_ids) != len(set(selected_ids)):
        errors.append("manifest selected papers contain duplicate IDs")
    if [item.get("sample_index") for item in selected] != list(range(1, len(selected) + 1)):
        errors.append("manifest selected sample_index values are not consecutive")

    by_id = {row.get("id"): row for row in rows}
    selected_strata: Counter[str] = Counter()
    for item in selected:
        paper_id = item.get("arxiv_id")
        row = by_id.get(paper_id)
        if row is None:
            errors.append(f"selected paper {paper_id} is absent from candidate pool")
            continue
        if item.get("versioned_id") != f"{paper_id}v1":
            errors.append(f"selected paper {paper_id} is not pinned to v1")
        expected_stratum = stratum_for(row.get("primary_category", ""))
        if item.get("stratum") != expected_stratum:
            errors.append(f"selected paper {paper_id} has an incorrect stratum")
        else:
            selected_strata[item["stratum"]] += 1
        if item.get("source_sha256") != FROZEN_SOURCE_SHA256.get(paper_id):
            errors.append(f"selected paper {paper_id} has an incorrect frozen source hash")
        if item.get("source_url") != f"https://arxiv.org/e-print/{paper_id}":
            errors.append(f"selected paper {paper_id} does not use the official arXiv source URL")
        if item.get("abs_url") != f"https://arxiv.org/abs/{paper_id}":
            errors.append(f"selected paper {paper_id} does not use the official arXiv abstract URL")
    if selected_strata != Counter({stratum: 2 for stratum in STRATA}):
        errors.append("manifest does not select exactly two papers in each topic stratum")

    exclusions = manifest.get("documented_eligibility_exclusions", [])
    exclusion_ids = [item.get("id") for item in exclusions]
    if frozenset(exclusion_ids) != DOCUMENTED_EXCLUSION_IDS or len(exclusion_ids) != len(DOCUMENTED_EXCLUSION_IDS):
        errors.append("manifest documented eligibility exclusions differ from the two preserved decisions")
    for item in exclusions:
        paper_id, stratum = item.get("id"), item.get("stratum")
        if "queue_position" in item:
            errors.append(f"documented exclusion {paper_id} retains an unsupported queue position")
        if paper_id not in by_id:
            errors.append(f"documented exclusion {paper_id} is absent from candidate pool")
        elif stratum_for(by_id[paper_id].get("primary_category", "")) != stratum:
            errors.append(f"documented exclusion {paper_id} has an incorrect stratum")
        if not item.get("reason"):
            errors.append(f"documented exclusion {paper_id} has no reason")
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
    action.add_argument("--check", action="store_true", help="validate the frozen pool and purposive sample manifest offline")
    action.add_argument("--refresh", action="store_true", help="politely retrieve the official API frame and compare it with the frozen pool")
    parser.add_argument("--pool", type=Path, default=POOL_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--rate-limit-seconds", type=float, default=3.0, help="delay between official API requests (default: 3 seconds)")
    args = parser.parse_args()
    errors = refresh(args.pool, args.manifest, args.rate_limit_seconds) if args.refresh else validate_frozen(args.pool, args.manifest)
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("candidate pool freezing: reproducible (count, digest, stable order, and frame verified)")
        print("selected-set random lineage: not claimed; design=stratified purposive stress test")
    print(f"claim-interface sample check: errors={len(errors)} network={'yes' if args.refresh else 'no'}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
