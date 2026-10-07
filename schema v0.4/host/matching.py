"""S7 retrieved matching (spec §3.3, §7.3) without a model call: retrieval, prompt, and match rows → delta.

One pool = the external requests to one upstream paper version. Each CANDIDATE_SUPPORT row that passes the
host checks is its own ``source:<pv>:<match_key>`` derivation; MISMATCH and UNCERTAIN rows are issues.
Quotations bind only within a retrieved statement (``source_quotes[].path`` names its claim id); a
repeated quotation is extended to the shortest unique enclosing span (the earliest-starting one on a tie), recorded
as a HOST_RULE issue naming the rule.
Identity or scope errors reject the whole response; a failing row is dropped with an issue.
"""
from __future__ import annotations

import re

from core import canonical
from library import _tokens
from model import MATCH_RESPONSE_SCHEMA

import anchors
import ids

METHOD, OPERATION = "MODEL_MATCH", "dependency.match_retrieved"
QUOTE_RULE = "SHORTEST_UNIQUE_ENCLOSING_SPAN_EARLIEST_START"
RESPONSE_SCHEMA = MATCH_RESPONSE_SCHEMA
LOCATOR_KINDS = anchors.KINDS + (("eq", "equation"),)
INSTRUCTION = (
    "Operation dependency.match_retrieved. For each external request decide whether one retrieved upstream statement, "
    "or several jointly, states the exact premise the citing claim needs. Only the retrieved candidate statements of the "
    "upstream paper are supplied, not its full source; a citation, title similarity or formula shape is insufficient. "
    "Preserve quantifier domains, normalizations, conventions and hypotheses. Return exactly one row per request, naming "
    "only that request's candidate_claim_ids. Use CANDIDATE_SUPPORT only with upstream_claim_ids and, for each of them, "
    "an exact quotation of its statement: source_quotes[].path is that claim id and exact_text is copied byte for byte. "
    "Several claims jointly needed require JOINT_SUPPORT; one claim is SINGLE_CLAIM. Otherwise return MISMATCH or "
    "UNCERTAIN and explain in reason. Record stronger assumptions and proof gaps in extra_conditions and proof_issues. "
    "Confidence is self-reported and uncalibrated; every result stays unreviewed.")


def locator_kind(text):
    word = re.match(r"\s*([A-Za-z]+)", text or "")
    return word and anchors.kind_of(word[1], LOCATOR_KINDS)


def retrieve_candidates(request, citing, upstream, k):
    """Top-k upstream (claim, reading) pairs for one EXTERNAL_REQUEST, deterministically: the reading kind named
    by the request's ``\\cite`` locator text first, then token overlap with the citing reading; ties by claim id."""
    kind, query = locator_kind(request.get("locator_text")), _tokens((citing or {}).get("display_text") or "")
    best = {}
    for claim, reading in upstream:
        if not reading.get("display_text"):
            continue
        score = (-(reading["kind"] == kind), -len(query & _tokens(reading["display_text"])), reading["id"])
        if claim["id"] not in best or score < best[claim["id"]][0]:
            best[claim["id"]] = (score, claim, reading)
    return [{"claim_id": claim["id"], "paper_version_id": claim.get("paper_version_id"), "occurrence_ids": claim["occurrence_ids"],
             "reading_id": reading["id"], "kind": reading["kind"], "statement_sha256": reading["statement_sha256"],
             "text": reading["display_text"]} for _, claim, reading in sorted(best.values(), key=lambda row: (row[0][:2], row[1]["id"]))[:k]]


def build_match_prompt(upstream_paper_version_id, items):
    """items = [{"request": Placeholder row, "citing": citing ClaimReading row or None, "candidates": retrieved}]."""
    candidates = {}
    for item in items:
        for row in item["candidates"]:
            if row["paper_version_id"] != upstream_paper_version_id:
                raise ValueError("a candidate is not STATED by the pool's upstream paper version (G7)")
            candidates[row["claim_id"]] = row
    requests = [{"id": item["request"]["id"], "locator_text": item["request"].get("locator_text"),
                 "citing_claim": {"id": item["request"]["created_by_claim_id"], "kind": (item["citing"] or {}).get("kind"),
                                  "text": (item["citing"] or {}).get("display_text")},
                 "candidate_claim_ids": [row["claim_id"] for row in item["candidates"]]} for item in items]
    payload = {"operation": OPERATION, "upstream_paper_version_id": upstream_paper_version_id,
               "pool_id": ids.make_id("pool", {"paper_version_id": upstream_paper_version_id, "request_ids": sorted(row["id"] for row in requests)}),
               "requests": requests, "candidates": [candidates[key] for key in sorted(candidates)]}
    return {"prompt": INSTRUCTION + "\nSOURCE DATA:\n" + canonical(payload).decode("utf-8"),
            "response_schema": RESPONSE_SCHEMA, "context": payload}


def bind_quote(text, quote):
    """(start, end, extended) character offsets of quote in text, extended if repeated to the shortest unique
    enclosing span, the earliest-starting one among equally short spans (QUOTE_RULE); None when absent."""
    starts = [i for i in range(len(text)) if text.startswith(quote, i)] if quote else []
    if len(starts) <= 1:
        return (starts[0], starts[0] + len(quote), False) if starts else None
    for length in range(len(quote) + 1, len(text) + 1):
        found = {(a, a + length) for s in starts for a in range(max(0, s + len(quote) - length), min(s, len(text) - length) + 1)
                 if text.find(text[a:a + length]) == text.rfind(text[a:a + length])}
        if found:
            return (*min(found), True)
    return None


def match_rows_to_delta(context, response, *, method_version, parents=(), produced_by=()):
    """S7 delta: one source junction per accepted CANDIDATE_SUPPORT row of a response to ``context``."""
    pv, pool = context["upstream_paper_version_id"], context["pool_id"]
    problem = lambda code, detail, **evidence: ids.issue(code, pool, detail, evidence or None)
    delta = lambda nodes, issues: ids.make_delta("S7", METHOD, method_version, ("REQUEST_POOL", pool), nodes, (), issues,
                                                parents=parents, produced_by=produced_by)
    if message := ids.schema_error(RESPONSE_SCHEMA, response):
        return delta(None, [problem("MODEL_RESPONSE_SCHEMA_INVALID", message)])
    requests, candidates = {row["id"]: row for row in context["requests"]}, {row["claim_id"]: row for row in context["candidates"]}
    rows, found = response["matches"], []
    targets = [row["target_request_id"] for row in rows]
    if len(set(targets)) != len(targets) or set(targets) != requests.keys():
        found.append(problem("MATCH_REQUEST_SCOPE_INVALID", "Exactly one row per pooled request is required"))
    scoped = []
    for n, row in enumerate(rows):
        allowed = requests.get(row["target_request_id"], {}).get("candidate_claim_ids", [])
        by_occ = {}
        for cid in allowed:
            for occ in candidates[cid]["occurrence_ids"]:
                by_occ.setdefault(occ, set()).add(cid)
        if set(row["upstream_claim_ids"]) - set(allowed) or set(row["upstream_occurrence_ids"]) - by_occ.keys():
            found.append(problem("MATCH_SOURCE_ID_UNKNOWN", "A row names a statement not retrieved for its request", row=n))
        scoped.append(by_occ)
    if found:
        return delta(None, found)
    junctions, issues = [], []
    for n, (row, by_occ) in enumerate(zip(rows, scoped)):
        request = row["target_request_id"]
        if row["relation"] != "CANDIDATE_SUPPORT":
            issues.append(problem("MATCH_" + row["relation"], row["reason"] or "No reason given", row=n, request_id=request,
                                  upstream_claim_ids=row["upstream_claim_ids"]))
            continue
        hits = [by_occ[occ] for occ in row["upstream_occurrence_ids"]]
        premises = set(row["upstream_claim_ids"]).union(*hits)
        quoted, extended, reject = set(), [], None
        if any(len(hit) > 1 for hit in hits):
            reject = ("MATCH_OCCURRENCE_AMBIGUOUS", "An upstream occurrence belongs to several retrieved claims")
        elif not premises:
            reject = ("MATCH_SUPPORT_STATEMENT_ABSENT", "Support requires an upstream statement")
        elif (len(premises) > 1) != (row["combination"] == "JOINT_SUPPORT"):
            reject = ("MATCH_COMBINATION_INVALID", "Several claims require JOINT_SUPPORT, one claim SINGLE_CLAIM")
        for quote in row["source_quotes"] if reject is None else ():
            text = candidates.get(quote["path"], {}).get("text", "")
            bound = quote["path"] in premises and bind_quote(text, quote["exact_text"])
            if not bound:
                reject = ("MATCH_QUOTATION_UNBOUND", "A quotation is absent from a retrieved premise statement")
                break
            quoted.add(quote["path"])
            if bound[2]:
                extended.append({"claim_id": quote["path"], "statement_sha256": candidates[quote["path"]]["statement_sha256"],
                                 "byte_start": len(text[:bound[0]].encode()), "byte_end": len(text[:bound[1]].encode())})
        if reject is None and premises - quoted:
            reject = ("MATCH_SUPPORT_QUOTATION_ABSENT", "Each premise statement requires an exact quotation")
        if reject:
            issues.append(problem(*reject, row=n, request_id=request))
            continue
        issues += [problem("HOST_RULE_QUOTATION_EXTENDED", "Repeated quotation extended to the shortest unique enclosing span",
                           row=n, request_id=request, rule=QUOTE_RULE, **span) for span in extended]
        if row["extra_conditions"] or row["proof_issues"]:
            issues.append(problem("MATCH_CONDITIONS_REPORTED", "Model-reported extra conditions or proof issues", row=n, request_id=request,
                                  extra_conditions=row["extra_conditions"], proof_issues=row["proof_issues"]))
        junctions.append(ids.seal("Junction", {
            "conclusion_id": request, "derivation_id": ids.source_derivation(pv, premises), "reading_method": METHOD,
            "method_version": method_version, "grouping_basis": "MATCH_ROW_" + row["combination"],
            "legs": [{"premise_id": cid, "role": "UNCLASSIFIED", "use_site": "UNKNOWN", "flags": []} for cid in sorted(premises)]}))
    return delta({"Junction": junctions}, issues)
