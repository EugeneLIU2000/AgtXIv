"""Prepare source-reading revisions without mutating extraction receipts.

This is a local preparation API, not an accepted-run or proof-discharge API.
It deliberately has no model call, graph publication, or CLI side effect.
"""
from copy import deepcopy

from core import canonical, digest
from pdf_candidates import assemble
from recursive_graph import _verified_json


_ROW_KEYS = {"id", "role", "statement", "conditions", "internal", "external",
             "unresolved_dependencies", "source"}
_LOCAL_ROLES = {"CONTRADICTION_CONTEXT", "PROOF_LOCAL_CLAIM"}


def prepare_amendment(document, original_reference, proposal):
    """Return a revised candidate plus provenance; all changed rows stay blocked.

    Proposal keys: kind=PDFReadingAmendmentProposal, original, replacements,
    proof_contexts. Each replacement has old_id, reason, claims (nonempty).
    Context entries have conclusion_id, context_ids, reason. These are reading
    associations only: they do not become permanent support premises or attest
    that any assumption was discharged. Every affected incoming edge must be
    explicitly rewritten in another replacement; no ID aliasing is performed.
    """
    if (set(proposal) != {"kind", "original", "replacements", "proof_contexts"}
            or proposal["kind"] != "PDFReadingAmendmentProposal"
            or proposal["original"] != original_reference):
        raise ValueError("PDF_AMENDMENT_ORIGINAL_BINDING_REQUIRED")
    original = _verified_json(original_reference)
    assemble(document, original)
    rows = {row["id"]: row for row in original["claims"]}
    changes = proposal["replacements"]
    if not isinstance(changes, list) or not 1 <= len(changes) <= len(rows):
        raise ValueError("PDF_AMENDMENT_REPLACEMENTS_REQUIRED")
    replacements, new_ids = {}, set()
    for change in changes:
        if (not isinstance(change, dict) or set(change) != {"old_id", "reason", "claims"}
                or change["old_id"] not in rows or change["old_id"] in replacements
                or not isinstance(change["reason"], str) or not change["reason"].strip()
                or not isinstance(change["claims"], list) or not change["claims"]):
            raise ValueError("PDF_AMENDMENT_REPLACEMENT_INVALID")
        for row in change["claims"]:
            if (not isinstance(row, dict) or set(row) != _ROW_KEYS
                    or not isinstance(row["id"], str) or not row["id"].strip()
                    or row["id"] in rows or row["id"] in new_ids):
                raise ValueError("PDF_AMENDMENT_REQUIRES_FRESH_EXPLICIT_ROW_IDS")
            for key in ("internal", "external", "unresolved_dependencies"):
                if (not isinstance(row[key], list)
                        or any(not isinstance(v, str) or not v.strip() for v in row[key])
                        or len(row[key]) != len(set(row[key]))):
                    raise ValueError("PDF_AMENDMENT_ROW_REFERENCES_INVALID")
            new_ids.add(row["id"])
        replacements[change["old_id"]] = change
    revised = deepcopy(original)
    revised["claims"] = []
    amendment_id = digest(canonical(proposal))
    for old in original["claims"]:
        if old["id"] not in replacements:
            revised["claims"].append(deepcopy(old))
            continue
        for row in replacements[old["id"]]["claims"]:
            updated = deepcopy(row)
            updated["unresolved_dependencies"].append(
                "SOURCE_READING_AMENDMENT_REQUIRES_REVIEW:" + amendment_id)
            revised["claims"].append(updated)
    current = {row["id"]: row for row in revised["claims"]}
    if len(current) > 20000:
        raise ValueError("PDF_AMENDMENT_TOO_MANY_ROWS")
    for row in current.values():
        for dependency in row["internal"]:
            # No suffix matching: a split cannot silently retarget an old edge.
            if dependency not in current:
                raise ValueError("PDF_AMENDMENT_EXPLICIT_INCOMING_EDGE_MIGRATION_REQUIRED")
            if (current[dependency]["role"] == "CONTRADICTION_CONTEXT"
                    and row["role"] not in _LOCAL_ROLES):
                raise ValueError("PDF_AMENDMENT_ASSUMPTION_IS_NOT_GLOBAL_SUPPORT")
    for row in current.values():
        if row["role"] in _LOCAL_ROLES:
            continue
        pending, visited = list(row["internal"]), set()
        while pending:
            dependency = pending.pop()
            if dependency in visited:
                continue
            visited.add(dependency)
            premise = current[dependency]
            if premise["role"] == "CONTRADICTION_CONTEXT":
                raise ValueError("PDF_AMENDMENT_ASSUMPTION_LEAKS_THROUGH_LOCAL_STEP")
            pending.extend(premise["internal"])
    contexts = proposal["proof_contexts"]
    if not isinstance(contexts, list) or len(contexts) > len(current):
        raise ValueError("PDF_AMENDMENT_CONTEXT_ARRAY_INVALID")
    seen = set()
    for context in contexts:
        if (not isinstance(context, dict)
                or set(context) != {"conclusion_id", "context_ids", "reason"}
                or context["conclusion_id"] not in new_ids
                or context["conclusion_id"] in seen
                or current[context["conclusion_id"]]["role"] in _LOCAL_ROLES | {"DEFINITION"}
                or not isinstance(context["reason"], str) or not context["reason"].strip()):
            raise ValueError("PDF_AMENDMENT_CONTEXT_CONCLUSION_INVALID")
        ids = context["context_ids"]
        if (not isinstance(ids, list) or not ids
                or any(not isinstance(v, str) or v not in current
                       or current[v]["role"] not in _LOCAL_ROLES for v in ids)
                or len(ids) != len(set(ids))):
            raise ValueError("PDF_AMENDMENT_LOCAL_CONTEXT_REQUIRED")
        seen.add(context["conclusion_id"])
        current[context["conclusion_id"]]["unresolved_dependencies"].append(
            "LOCAL_ASSUMPTION_DISCHARGE_NOT_VERIFIED:" + amendment_id)
    # This association is provenance, never a SupportGroup or a proof receipt.
    record = {"kind": "PDFReadingAmendmentPreparation", "original": original_reference,
              "proposal_sha256": amendment_id, "proposal": deepcopy(proposal),
              "proof_context_associations": deepcopy(contexts),
              "source_alignment_accepted": False, "proof_discharge_verified": False,
              "graph_publication_supported": False}
    revised["amendment_preparation"] = record
    assemble(document, revised)
    return {"candidate": revised, "preparation": record}
