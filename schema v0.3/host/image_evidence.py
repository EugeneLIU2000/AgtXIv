"""Reconstruct ordered image evidence without inferring model perception."""
from pathlib import Path
from core import canonical, digest


def image_evidence_issues(task, receipt, directory):
    issues = []
    def require(ok, code):
        if not ok:
            issues.append({"code": code})
    images = task.get("image_inputs", [])
    require(images == receipt.get("image_inputs", []), "MODEL_IMAGE_RECEIPT_MISMATCH")
    if not images:
        require("multimodal_input_sha256" not in task and "multimodal_input_sha256" not in receipt,
                "MODEL_IMAGE_DIGEST_WITHOUT_IMAGES")
        return issues
    require(len(images) <= 32, "MODEL_IMAGE_COUNT_EXCEEDED")
    total, hashes = 0, []
    try:
        for index, item in enumerate(images):
            ref = item["snapshot"]
            path = Path(ref["path"]).resolve()
            require(path.parent == Path(directory).resolve() and path.stem == f"image-{index:03d}",
                    "MODEL_IMAGE_SNAPSHOT_PATH_MISMATCH")
            require(item["index"] == index, "MODEL_IMAGE_ORDER_MISMATCH")
            with path.open("rb") as stream:
                raw = stream.read(32 * 1024 * 1024 + 1)
            total += len(raw)
            require(len(raw) == ref["byte_size"] and digest(raw) == ref["sha256"], "MODEL_IMAGE_BYTES_CHANGED")
            require(all(item["original"][key] == ref[key] for key in ("sha256", "byte_size")),
                    "MODEL_IMAGE_ORIGIN_MISMATCH")
            hashes.append(ref["sha256"])
        require(total == task["image_input_bytes"] and total <= 32 * 1024 * 1024, "MODEL_IMAGE_SIZE_MISMATCH")
        expected = digest(canonical({"prompt_sha256": task["prompt_sha256"], "ordered_image_sha256": hashes}))
        require(expected == task.get("multimodal_input_sha256") == receipt.get("multimodal_input_sha256"),
                "MODEL_MULTIMODAL_DIGEST_MISMATCH")
    except (OSError, ValueError, KeyError, TypeError) as error:
        issues.append({"code": "MODEL_IMAGE_EVIDENCE_UNREADABLE", "detail": str(error)})
    return issues
