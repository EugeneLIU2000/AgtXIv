"""Combine retained source-reading batches without claiming semantic deduplication."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from candidates import assemble_candidates
from core import canonical, digest, utcnow, write_json
from model import _frozen_source_payload


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}


def union_intervals(intervals):
    result = []
    for start, end in sorted(intervals):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def bundle(manifest_path: Path, output: Path):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Retain previous combined candidates; choose a fresh output directory")
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_bytes())
    scope_notes = manifest.get("combination_scope_notes", [])
    if not isinstance(scope_notes, list) or any(not isinstance(note, str) for note in scope_notes):
        raise ValueError("Combination scope notes must be strings")
    manifest_snapshot = write_json(output / "manifest.json", manifest)
    extraction = Path(manifest["extraction"]).resolve()
    paper = json.loads(extraction.read_bytes())
    if manifest["paper_id"] != paper["paper"]["id"]:
        raise ValueError("Batch manifest and source extraction identify different papers")
    sources = _frozen_source_payload(paper, extraction.parent, source_directory=extraction.parent)
    raw_sources = {row["path"]: (extraction.parent / row["blob_path"]).read_bytes() for row in paper["source_files"]}
    ids, entries, read_intervals, chunks, uncertainty = set(), defaultdict(list), defaultdict(list), [], []
    for item in manifest["chunks"]:
        chunk_id = item["id"]
        if not isinstance(chunk_id, str) or not chunk_id or chunk_id in ids:
            raise ValueError("Reading batch IDs must be nonempty and distinct")
        ids.add(chunk_id)
        retained = {}
        for kind in ("response", "provenance"):
            original = Path(item[kind]).resolve()
            raw = original.read_bytes()
            destination = output / "inputs" / f"{len(chunks):04d}-{kind}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(raw)
            retained[kind] = {"snapshot": reference(destination), "original": {
                "path": str(original), "sha256": digest(raw), "byte_size": len(raw)}}
        response_ref, provenance_ref = retained["response"]["snapshot"], retained["provenance"]["snapshot"]
        response = json.loads(Path(response_ref["path"]).read_bytes())
        provenance = json.loads(Path(provenance_ref["path"]).read_bytes())
        if provenance.get("paper_id") != paper["paper"]["id"]:
            raise ValueError("Reading provenance belongs to another paper")
        signatures = lambda rows: sorted((row["path"], row["sha256"], row["byte_size"]) for row in rows)
        if signatures(provenance["source_files"]) != signatures(paper["source_files"]):
            raise ValueError("Reading provenance source snapshot differs from the supplied extraction")
        candidate = response.get("candidate", response)
        assembled = assemble_candidates(paper, candidate, sources, response_reference=response_ref)
        for index, (claim, claim_id) in enumerate(zip(candidate["claims"], assembled["query_ids"], strict=True)):
            if "internal_support_claim_indexes" in claim:
                # Batch-local positions are rebound through claim identities below.
                claim = {**claim, "internal_support_claim_indexes": [
                    assembled["query_ids"][i] for i in claim["internal_support_claim_indexes"]]}
            entries[claim_id].append({"claim": claim, "origin": {"chunk_id": chunk_id, "response": response_ref,
                                      "response_claim_index": index, "candidate_claim_id": claim_id}})
        spans = []
        reported_spans = set()
        for block in provenance.get("read_blocks", []):
            if block.get("reading_status") != "READ":
                continue
            source_path = block.get("path")
            if source_path is None and len(paper["source_files"]) == 1:
                source_path = paper["source_files"][0]["path"]
            reported_spans.add((source_path, block["byte_start"], block["byte_end_exclusive"]))
        for block in provenance.get("reported_read_spans", []):
            reported_spans.add((block["path"], block["byte_start"], block["byte_end"]))
        for interval in item["read_spans"]:
            path, start, end = interval["path"], interval["byte_start"], interval["byte_end"]
            if (path, start, end) not in reported_spans:
                raise ValueError("Manifest reading interval has no matching structured provenance report")
            if path not in raw_sources or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw_sources[path]):
                raise ValueError("Reported reading range is outside the frozen source")
            data = raw_sources[path]
            span = {"path": path, "byte_start": start, "byte_end": end, "sha256": digest(data),
                    "span_sha256": digest(data[start:end]), "interval": "HALF_OPEN", "offset_unit": "BYTE"}
            spans.append(span)
            read_intervals[path].append([start, end])
        chunks.append({"id": chunk_id, "response": response_ref, "provenance": provenance_ref,
                       "original_inputs": {kind: value["original"] for kind, value in retained.items()},
                       "reported_read_spans": spans, "candidate_rows": len(candidate["claims"])})
        uncertainty.extend(f"[{chunk_id}] {text}" for text in candidate["unread_or_uncertain_scope"])
    accepted_rows, accepted_ids, origins, conflicts, repeats = [], [], [], [], []
    for claim_id, rows in entries.items():
        origins_for_claim = [row["origin"] for row in rows]
        if len({canonical(row["claim"]) for row in rows}) != 1:
            # The same source/statement identity carries different support or
            # other assertions. Exclude all variants pending reconciliation;
            # neither first/last wins nor unioning dependencies is justified.
            conflicts.append({"claim_id": claim_id, "origins": origins_for_claim,
                              "status": "RECONCILIATION_REQUIRED_ALL_VARIANTS_RETAINED_IN_ORIGINAL_RESPONSES"})
            uncertainty.append("Unresolved conflicting batch rows for candidate " + claim_id)
            continue
        if len(rows) > 1:
            repeats.append({"claim_id": claim_id, "origins": origins_for_claim,
                            "basis": "IDENTICAL_COMPLETE_CANDIDATE_ROW_ONLY"})
        origins.append({"combined_response_claim_index": len(accepted_rows), "origins": origins_for_claim})
        accepted_rows.append(rows[0]["claim"])
        accepted_ids.append(claim_id)
    position = {claim_id: index for index, claim_id in enumerate(accepted_ids)}
    for row in accepted_rows:
        if "internal_support_claim_indexes" in row:
            support = row["internal_support_claim_indexes"]
            row["internal_support_claim_indexes"] = [position[i] for i in support if i in position]
            row["unresolved_dependencies"] = row["unresolved_dependencies"] + [
                "Host combination: support claim " + i + " was excluded pending batch reconciliation"
                for i in support if i not in position]
    coverage = []
    for path, data in sorted(raw_sources.items()):
        intervals = union_intervals(read_intervals[path])
        gaps, last = [], 0
        for start, end in intervals:
            if start > last:
                gaps.append([last, start])
            last = end
        if last < len(data):
            gaps.append([last, len(data)])
        coverage.append({"path": path, "source_bytes": len(data), "reported_read_intervals": intervals,
                         "reported_read_bytes": sum(end-start for start, end in intervals), "unreported_read_intervals": gaps})
    result = {"claims": accepted_rows, "unread_or_uncertain_scope": [
        "This is a host combination of retained reading batches, not a new model extraction or semantic deduplication.",
        "Reading intervals are attributed reports checked against frozen bytes; interval coverage does not prove all mathematical claims were extracted.",
        "Earlier batch-local unread statements remain historical context; use bundle-provenance.json for cumulative reported reading ranges.",
        *scope_notes, *uncertainty]}
    response_ref = write_json(output / "response.json", result)
    # Rebinding the combined rows resolves cross-batch internal occurrences where
    # a unique candidate actually exists. Multiple matches remain typed requests.
    assembly = assemble_candidates(paper, result, sources, response_reference=response_ref)
    provenance = {"kind": "RetainedReadingBatchCombination", "created_at": utcnow(),
                  "paper_id": paper["paper"]["id"], "program_sha256": digest(Path(__file__).read_bytes()),
                  "source_files": paper["source_files"], "source_manifest_sha256": paper["paper"]["source_manifest_sha256"],
                  "manifest": manifest_snapshot, "original_manifest": reference(manifest_path), "extraction": reference(extraction), "response": response_ref,
                  "chunks": chunks, "claim_origins": origins, "byte_identical_repeats": repeats, "conflicts": conflicts,
                  "reading_coverage": coverage, "raw_candidate_rows": sum(row["candidate_rows"] for row in chunks),
                  "combined_candidate_rows": len(accepted_rows), "new_model_calls": 0,
                  "semantic_deduplication_performed": False, "source_completeness_asserted": False,
                  "semantic_status": "AWAITING_REVIEW", "mathematical_status": "CHAIN_INCOMPLETE"}
    write_json(output / "bundle-provenance.json", provenance)
    write_json(output / "assembly.json", assembly)
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = bundle(args.manifest.resolve(), args.output.resolve())
    print(json.dumps({"raw_rows": result["raw_candidate_rows"], "combined_rows": result["combined_candidate_rows"],
                      "conflicts": len(result["conflicts"]), "identical_repeats": len(result["byte_identical_repeats"]),
                      "reported_read_bytes": sum(row["reported_read_bytes"] for row in result["reading_coverage"]),
                      "semantic_status": result["semantic_status"]}))


if __name__ == "__main__":
    main()
