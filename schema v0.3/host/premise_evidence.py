"""Bind reported premises to text bytes; never accept their semantic relation."""
from core import digest


def bind_premise_report(report, sources):
    text_sources = {row["path"]: row for row in sources if "text" in row}
    pdf = any(row.get("kind") == "RetainedPDFProofContext" for row in sources)
    rows = []
    for index, item in enumerate(report):
        located = item["source_role"] != "NOT_LOCATED"
        if bool(item["source_evidence_description"].strip()) != located:
            raise ValueError("PREMISE_REPORT_LOCATION_INCONSISTENT")
        path, quote = item["source_path"], item["source_quote"]
        row = {"report_index": index, "source_spans": [], "source_alignment_accepted": False}
        if item["source_role"] == "NOT_LOCATED":
            if path or quote:
                raise ValueError("UNLOCATED_PREMISE_HAS_QUOTATION")
            row["status"] = "NOT_LOCATED"
        elif pdf:
            if path or quote:
                raise ValueError("PDF_PREMISE_REQUIRES_REGION_ADAPTER_NOT_TEXT_QUOTATION")
            row["status"] = "PDF_DESCRIPTION_UNBOUND"
        else:
            source = text_sources.get(path)
            if source is None or not quote:
                raise ValueError("PREMISE_SOURCE_OR_QUOTATION_MISSING")
            raw, needle = source["text"].encode("utf-8"), quote.encode("utf-8")
            if digest(raw) != source["sha256"]:
                raise ValueError("PREMISE_FROZEN_SOURCE_DIGEST_MISMATCH")
            start = raw.find(needle)
            if start < 0 or raw.find(needle, start + 1) >= 0:
                raise ValueError("PREMISE_QUOTATION_ABSENT_OR_AMBIGUOUS")
            row["source_spans"] = [{"path": path, "sha256": source["sha256"],
                "byte_start": start, "byte_end": start + len(needle),
                "span_sha256": digest(needle), "offset_unit": "BYTE", "interval": "HALF_OPEN"}]
            row["status"] = "TEXT_BYTES_BOUND_SEMANTICS_UNREVIEWED"
        rows.append(row)
    return {"kind": "PremiseSourceEvidence", "rows": rows,
            "premise_completeness_verified": False, "source_alignment_accepted": False}
