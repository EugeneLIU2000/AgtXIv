"""Eligibility program THEOREM_OR_DERIVATION_V1 (spec §6.2), decided after acquisition from the S2 parse.

A paper is eligible iff its v0.3 ``ingest.extract_paper`` record has at least ``min_theorem_like`` theorem-like or
definition environments, or at least ``min_display_equations`` display equations. The second arm keeps physics papers
that derive results in equations without theorem environments inside P (quant-ph/9705052v1 has no theorem
environment, MEASURED).

A paper whose source could not be read is UNDETERMINED, not INELIGIBLE (§6.2: P = frame ∩ determinable ∩ eligible):
no frozen source file, or an S1/S2 issue that blocks reading (BLOCKING), gives its undetermined class; a parse that
skipped part of the source (INCOMPLETE issues) and still falls short of both thresholds is UNDETERMINED PARSE_FAILED,
because the unread part could hold what is missing. Pure functions; the manifest freezes the rule, its params and the
digest of this file.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from core import digest

RULE = "THEOREM_OR_DERIVATION_V1"
THEOREM_KINDS = ("THEOREM_LIKE_ENVIRONMENT", "DEFINITION_ENVIRONMENT")
EQUATION_KIND = "DISPLAY_EQUATION"
BLOCKING = (("SOURCE_UNREACHABLE", "NO_TEX_SOURCE"), ("SOURCE_ACQUISITION_FAILED", "NO_TEX_SOURCE"),
            ("SOURCE_MAIN_NOT_FOUND", "NO_TEX_SOURCE"), ("SOURCE_MAIN_AMBIGUOUS", "MAIN_AMBIGUOUS"))  # v0.3 ingest codes, in priority order
INCOMPLETE = ("SOURCE_ENCODING_UNSUPPORTED", "SOURCE_INCLUDE_MISSING", "DYNAMIC_INCLUDE_UNRESOLVED", "INCLUDE_OUTSIDE_SOURCE_ROOT")


def program_sha256():
    """The CorpusManifest.eligibility.program_sha256 of this program."""
    return digest(Path(__file__).read_bytes())


def counts(extraction):
    """{theorem_like, display_equations} of one extraction record (bundles overlap equations and are not counted)."""
    kinds = Counter(row["kind"] for row in extraction["claims"])
    return {"theorem_like": sum(kinds[k] for k in THEOREM_KINDS), "display_equations": kinds[EQUATION_KIND]}


def decide(extraction, eligibility):
    """{outcome: ACCEPTED | INELIGIBLE | UNDETERMINED, counts, reason (INELIGIBLE), undetermined_class and issues
    (UNDETERMINED)} under a manifest's eligibility block."""
    if eligibility["rule"] != RULE:
        raise ValueError("ELIGIBILITY_RULE_UNSUPPORTED: " + str(eligibility["rule"]))
    codes = {issue["code"] for issue in extraction.get("issues", [])}
    found, params = counts(extraction), eligibility["params"]
    if not extraction.get("source_files"):
        return {"outcome": "UNDETERMINED", "counts": found, "undetermined_class": "NO_TEX_SOURCE", "issues": sorted(codes)}
    for code, undetermined in BLOCKING:
        if code in codes:
            return {"outcome": "UNDETERMINED", "counts": found, "undetermined_class": undetermined, "issues": sorted(codes)}
    if found["theorem_like"] >= params["min_theorem_like"] or found["display_equations"] >= params["min_display_equations"]:
        return {"outcome": "ACCEPTED", "counts": found}
    if unread := sorted(codes & set(INCOMPLETE)):
        return {"outcome": "UNDETERMINED", "counts": found, "undetermined_class": "PARSE_FAILED", "issues": unread}
    return {"outcome": "INELIGIBLE", "counts": found,
            "reason": (f"{RULE}: {found['theorem_like']} theorem-like < {params['min_theorem_like']} and "
                       f"{found['display_equations']} display equations < {params['min_display_equations']}")}


def candidate_outcome(decision, attempts, paper_version_id):
    """The SamplingRecord outcome row fields for one examined candidate."""
    if decision["outcome"] == "ACCEPTED":
        return {"outcome": "ACCEPTED", "attempts": attempts, "paper_version_id": paper_version_id}
    if decision["outcome"] == "UNDETERMINED":
        return {"outcome": "UNDETERMINED", "attempts": attempts, "undetermined_class": decision["undetermined_class"]}
    return {"outcome": "INELIGIBLE", "attempts": attempts, "reason": decision["reason"]}


def grid(extractions, theorem_thresholds, equation_thresholds):
    """P-1 (§11): under each (min_theorem_like, min_display_equations), the eligible fraction accepted / (accepted +
    ineligible) that decide() would give over the parsed candidates, measured before the manifest's params are relied
    on: a candidate without a readable source is left out, and one whose parse skipped part of the source counts only
    when it meets the thresholds (else it would be UNDETERMINED). Keys are 'k=<t>,m=<e>'; a value is None when nothing
    is determinable under it."""
    blocking = {code for code, _ in BLOCKING}
    rows = []
    for e in extractions:
        codes = {issue["code"] for issue in e.get("issues", [])}
        if e.get("source_files") and not codes & blocking:
            rows.append((counts(e), bool(codes & set(INCOMPLETE))))
    if not rows:
        raise ValueError("ELIGIBILITY_GRID_NEEDS_PARSED_CANDIDATES")
    out = {}
    for k in theorem_thresholds:
        for m in equation_thresholds:
            meets = [r["theorem_like"] >= k or r["display_equations"] >= m for r, _ in rows]
            accepted = sum(meets)
            ineligible = sum(not ok and not unread for ok, (_, unread) in zip(meets, rows))
            out[f"k={k},m={m}"] = accepted / (accepted + ineligible) if accepted + ineligible else None
    return out
