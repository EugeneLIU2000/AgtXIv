"""Apply frozen source-review objections without accepting or deleting claims."""
from pathlib import Path

from core import digest
from recursive_graph import _verified_json


def apply_review_blocks(assembly, references):
    for reference in references:
        review = _verified_json(reference)
        if (review.get("kind") != "SourceClaimCounterexampleAssociation" or
                review.get("required_boundary") != "DO_NOT_USE_AS_DISCHARGED_PREMISE"):
            raise ValueError("UNSUPPORTED_REVIEW_BOUNDARY")
        matches = _verified_json(review["original_match"])
        row = matches["matches"][review["original_row_index"]]
        if (row["target_request_id"] != review["target_request_id"] or
                row["upstream_claim_ids"] != review["upstream_claim_ids"]):
            raise ValueError("REVIEW_TARGET_DIFFERS_FROM_MATCH")
        for key in ("historical_blocker", "counterexample_review"):
            ref = review[key]
            raw = Path(ref["path"]).read_bytes()
            if len(raw) != ref["byte_size"] or digest(raw) != ref["sha256"]:
                raise ValueError("REVIEW_EVIDENCE_CHANGED")
        disputed = review["disputed_claim_ids"]
        if not disputed or not set(disputed) <= set(review["upstream_claim_ids"]):
            raise ValueError("REVIEW_DISPUTED_CLAIMS_UNBOUND")
        affected = {review["target_request_id"], *disputed}
        blocker = "SOURCE_REVIEW_OBJECTION:" + reference["sha256"]
        for node in assembly["nodes"]:
            if node["id"] in affected:
                node["blocked_by"] = sorted(set(node.get("blocked_by", [])) | {blocker})
    return assembly
