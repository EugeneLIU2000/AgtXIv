"""Retain PDF-region reading candidates as a source-bound support graph.

PDF images and derived text are distinct artifacts. A bounded page rectangle is
not an exact quotation or a claim that OCR faithfully represents mathematics.
This adapter accepts attributed reading reports, never model-owned acceptance.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time

from chunks import reference
from core import VERSION, canonical, digest, utcnow, write_json
from graph import prune_graph


def retained(ref, directory, suffix, ceiling):
    path = Path(ref["path"]).resolve()
    with path.open("rb") as stream:
        raw = stream.read(ceiling + 1)
    actual = {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}
    if len(raw) > ceiling or actual != ref:
        raise ValueError("PDF reading artifact changed or exceeded its byte ceiling")
    dest = directory / (ref["sha256"].removeprefix("sha256:") + suffix)
    if not dest.exists():
        dest.write_bytes(raw)
    elif dest.read_bytes() != raw:
        raise ValueError("Content-addressed PDF asset collision")
    return reference(dest)


def frozen_document(reading, output):
    assets = output / "assets"
    assets.mkdir()
    pdf = retained(reading["pdf"], assets, ".pdf", 64 * 1024 * 1024)
    if not Path(pdf["path"]).read_bytes().startswith(b"%PDF-"):
        raise ValueError("Source artifact has no PDF header")
    binary = shutil.which("pdfinfo")
    if binary is None:
        raise RuntimeError("PDFINFO_UNAVAILABLE")
    command = [binary, pdf["path"]]
    started, tick = utcnow(), time.monotonic()
    process = subprocess.run(command, capture_output=True, timeout=30)
    log = process.stdout + b"\nSTDERR:\n" + process.stderr
    (output / "pdfinfo.log").write_bytes(log)
    match = re.search(rb"(?m)^Pages:\s+(\d+)\s*$", process.stdout)
    count = int(match[1]) if match else None
    receipt = {"kind": "ProgramReceipt", "contract_version": VERSION, "engine_class": "HOST",
        "program": "agtxiv.pdf-region/0.3.0", "operation": "pdf.page_inventory", "call": None,
        "input_sha256": pdf["sha256"], "output_sha256": digest(log), "command": command,
        "cwd": str(Path.cwd()), "started_at": started, "finished_at": utcnow(),
        "elapsed_seconds": round(time.monotonic()-tick, 6), "exit_code": process.returncode,
        "status": "SUCCEEDED" if process.returncode == 0 and count else "FAILED",
        "outcome": "RECORDED" if process.returncode == 0 and count else "FAILED"}
    receipt_ref = write_json(output / "pdfinfo-receipt.json", receipt)
    if process.returncode or count is None or not 1 <= count <= 2000:
        raise ValueError("Actual bounded PDF page inventory could not be established")
    images = reading["page_images"]
    if len(images) != count:
        raise ValueError("This adapter requires one ordered retained image for every PDF page")
    pages = []
    for number, ref in enumerate(images, 1):
        image = retained(ref, assets, ".png", 32 * 1024 * 1024)
        raw = Path(image["path"]).read_bytes()
        if raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR" or len(raw) < 24:
            raise ValueError("A retained page image is not a PNG with dimensions")
        width, height = int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
        if not 1 <= width <= 16384 or not 1 <= height <= 16384:
            raise ValueError("Page image dimensions exceed the supported range")
        pages.append({"page": number, "image": image, "width": width, "height": height})
    read = reading.get("pages_visually_read", [])
    if (not isinstance(read, list) or len(read) != len(set(read)) or
            any(type(page) is not int or not 1 <= page <= count for page in read)):
        raise ValueError("Invalid attributed page-reading report")
    return {"kind": "FrozenPDFRegionDocument", "pdf": pdf, "original_pdf": reading["pdf"],
        "page_count": count, "pages": pages, "page_count_receipt": receipt_ref,
        "derived_text": retained(reading["derived_text"], assets, ".txt", 8 * 1024 * 1024),
        "reported_visually_read_pages": read, "reading_report_is_attributed_not_independently_observed": True,
        "image_render_correspondence": "RETAINED_PROVIDER_REPORT_NOT_INDEPENDENT_RERENDER",
        "ocr_is_authoritative_math": False, "source_completeness_asserted": False}


def assemble(document, candidate):
    identity = candidate["source_identity"]
    if not isinstance(identity, str) or not identity:
        raise ValueError("PDF paper identity is absent")
    rows = candidate["claims"]
    if not isinstance(rows, list) or len(rows) > 20000:
        raise ValueError("Invalid PDF candidate array")
    nodes, names, roles, ids = [], {}, {}, {}
    for row in rows:
        source, role = row["source"], row["role"]
        if role not in {"DEFINITION", "CLAIM", "THEOREM", "LEMMA", "COROLLARY", "PROOF_LOCAL_CLAIM", "CONTRADICTION_CONTEXT"}:
            raise ValueError("Unknown PDF mathematical reading role")
        if source["pdf"] != document["original_pdf"]:
            raise ValueError("Candidate PDF reference differs from the frozen original")
        page, box = source["page"], source["region"]
        if type(page) is not int or not 1 <= page <= document["page_count"]:
            raise ValueError("PDF candidate page is outside the actual document")
        if (not isinstance(box, list) or len(box) != 4 or
            any(type(v) not in {int, float} or not math.isfinite(v) for v in box) or
            not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1)):
            raise ValueError("PDF rectangle must be a nonempty normalized top-left region")
        if not isinstance(row["statement"], str) or not row["statement"].strip():
            raise ValueError("PDF candidate mathematical statement is absent")
        if (not isinstance(row["conditions"], list) or any(not isinstance(c, str) for c in row["conditions"])):
            raise ValueError("PDF candidate conditions must be text")
        unresolved = row.get("unresolved_dependencies", [])
        if (not isinstance(unresolved, list) or
                any(not isinstance(item, str) or not item.strip() for item in unresolved)):
            raise ValueError("PDF unresolved dependencies must be nonempty text entries")
        if row["id"] in ids:
            raise ValueError("Duplicate source reading claim identifier")
        anchor = {"kind": "PDF_PAGE_REGION", "pdf": document["pdf"], "page": page,
            "page_image": document["pages"][page-1]["image"], "normalized_rectangle": box,
            "coordinate_system": "TOP_LEFT_UNIT_SQUARE", "printed_page": source.get("printed_page"),
            "binding_scope": "DOCUMENT_BYTES_PAGE_NUMBER_IMAGE_BYTES_AND_REGION_GEOMETRY_ONLY"}
        identity_anchor = {**anchor, "pdf": document["pdf"]["sha256"],
                           "page_image": anchor["page_image"]["sha256"]}
        node_id = "claim:pdf:" + digest(canonical([identity, identity_anchor, row["statement"], row["conditions"], role]))[7:31]
        if node_id in ids.values():
            raise ValueError("Duplicate PDF mathematical identity requires reconciliation")
        ids[row["id"]] = node_id
        names.setdefault(row["id"].split(":")[-1], []).append(node_id)
        roles[node_id] = role
        blockers = ["PDF_LOCAL_PROOF_SCOPE_REQUIRES_ALIGNMENT"] if role in {"PROOF_LOCAL_CLAIM", "CONTRADICTION_CONTEXT"} else []
        if unresolved:
            blockers.append("PDF_UNRESOLVED_DEPENDENCIES")
        nodes.append({"id": node_id, "paper_id": identity, "source_reading_id": row["id"],
            "kind": "definition" if role == "DEFINITION" else "proof_context" if role == "CONTRADICTION_CONTEXT" else role.lower(),
            "text": row["statement"], "conditions": row["conditions"], "source_spans": [anchor],
            "disposition": "AGENT_NORMALIZED_UNREVIEWED", "blocked_by": blockers,
            "confidence": {"source": "SELF_REPORTED", "value": 0, "calibration_ref": None},
            "cost_microusd": None, "upstream_search": "FRONTIER"})
        if "unresolved_dependencies" in row:
            nodes[-1]["unresolved_dependencies"] = list(unresolved)
    groups, requests = [], []
    for row in rows:
        target, members = ids[row["id"]], []
        for key in row["internal"]:
            matches = [ids[key]] if key in ids else names.get(key, [])
            if len(matches) != 1 or matches[0] == target:
                raise ValueError("PDF internal reference is absent, ambiguous or self-supporting")
            members.append(matches[0])
        for citation in row["external"]:
            if not isinstance(citation, str) or not citation:
                raise ValueError("External PDF statement request must be nonempty text")
            request_id = "request:pdf:" + digest(canonical([identity, target, citation]))[7:31]
            requests.append({"id": request_id, "kind": "external_claim_request", "downstream_node_id": target,
                "cited_statement_label": citation, "upstream_paper_identity": None,
                "identity_status": "BIBLIOGRAPHIC_LABEL_ONLY_REQUIRES_RESOLUTION",
                "source_spans": next(node["source_spans"] for node in nodes if node["id"] == target)})
            nodes.append({"id": request_id, "kind": "external_claim_request", "text": citation,
                "paper_id": identity, "disposition": "UNREVIEWED", "blocked_by": ["CITED_STATEMENT_NOT_READ"],
                "cost_microusd": None, "upstream_search": "FRONTIER", "source_spans": requests[-1]["source_spans"]})
            members.append(request_id)
        if members:
            groups.append({"id": "support-group:pdf:" + digest(canonical([target, sorted(set(members))]))[7:31],
                "target": target, "members": sorted(set(members)), "relation": "PROOF_DEPENDENCY",
                "disposition": "UNREVIEWED", "grouping_basis": "ATTRIBUTED_JOINT_SUPPORT_NOT_CHECKED_SUFFICIENCY",
                "confidence": {"source": "SELF_REPORTED", "value": 0, "calibration_ref": None}})
    return {"kind": "PDFCandidateGraphAssembly", "paper_id": identity, "nodes": nodes, "support_groups": groups,
        "query_ids": [value for value in ids.values() if roles[value] != "CONTRADICTION_CONTEXT"],
        "nonasserted_context_ids": [value for value in ids.values() if roles[value] == "CONTRADICTION_CONTEXT"],
        "dependency_requests": requests, "source_completeness_asserted": False,
        "source_alignment_accepted": False, "upstream_search_exhausted": False,
        "supplied_scope": candidate.get("coverage"), "all_judgements_unreviewed": True}


def run(reading_path, candidate_path, output):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("PDF source runs require a fresh output directory")
    output.mkdir(parents=True)
    runtime = []
    for name in ("pdf_candidates.py", "graph.py", "core.py", "chunks.py"):
        original = Path(__file__).resolve().parent / name
        destination = output / "runtime" / name
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(original.read_bytes())
        runtime.append({"repository_path": str(original), "snapshot": reference(destination)})
    inputs = {}
    for name, path in (("reading", reading_path), ("candidates", candidate_path)):
        raw = Path(path).read_bytes()
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("PDF reading JSON exceeded its byte ceiling")
        dest = output / (name + "-input.json")
        dest.write_bytes(raw)
        inputs[name] = {"retained": reference(dest), "original": reference(Path(path).resolve())}
    reading = json.loads((output / "reading-input.json").read_bytes())
    candidates = json.loads((output / "candidates-input.json").read_bytes())
    document = frozen_document(reading, output)
    document_ref = write_json(output / "document.json", document)
    assembly = assemble(document, candidates)
    assembly_ref = write_json(output / "assembly.json", assembly)
    graph = prune_graph(assembly["nodes"], assembly["support_groups"], assembly["query_ids"])
    graph_ref = write_json(output / "graph.json", graph)
    summary = {"kind": "PDFRegionCandidateRun", "paper_id": candidates["source_identity"], "inputs": inputs,
        "runtime_sources": runtime,
        "document": document_ref, "assembly": assembly_ref, "graph": graph_ref,
        "candidate_rows": len(candidates["claims"]), "query_candidates": len(assembly["query_ids"]),
        "nonasserted_proof_contexts": len(assembly["nonasserted_context_ids"]),
        "graph_nodes": len(graph["nodes"]), "support_groups": len(graph["support_groups"]),
        "external_requests": len(assembly["dependency_requests"]), "new_model_calls": 0,
        "source_alignment_accepted": False, "mathematical_status": "CHAIN_INCOMPLETE"}
    write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reading", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.reading, args.candidates, args.output)
    print(json.dumps({key: value for key, value in result.items() if key not in {"inputs", "runtime_sources", "document", "assembly", "graph"}}))


if __name__ == "__main__":
    main()
