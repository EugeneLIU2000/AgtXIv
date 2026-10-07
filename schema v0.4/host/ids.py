"""v0.4 identities (spec §5): ``<prefix>:<64 hex>`` of v0.3 ``core.digest(core.canonical(identity))``, except
PaperVersion ids, which are ``arxiv:<base>v<n>`` with no digest.

An identity is a dict of exactly the §5.2 identity fields, read from the row itself, so a loader can
recompute every id (G6); ``content_sha256`` is the digest of the same dict, so equal id implies equal
content. Derivation ids keep the ``sha256:`` form of their digests. Nothing here sets a state.
"""
from __future__ import annotations

import re

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from core import canonical, digest

import contracts

PREFIX = {"Work": "work", "BibEntry": "bib", "Claim": "claim", "ClaimReading": "reading",
          "Junction": "junction", "Placeholder": "placeholder", "PrimitiveAssertion": "primitive", "Edge": "rel"}
FIELDS = {"PaperVersion": ("arxiv_base_id", "version"), "BibEntry": ("paper_version_id", "citation_key", "locator"),
          # work_locator_text is the entered locator of a WORK_LOCATOR claim (it has no occurrence), not method text.
          "Claim": ("origin", "paper_version_id", "work_id", "occurrence_ids", "part", "work_locator_text"),
          "ClaimReading": ("claim_id", "method", "method_version", "statement_sha256", "conditions_sha256", "kind"),
          "Junction": ("conclusion_id", "derivation_id", "reading_method", "method_version", "legs"),
          "Placeholder": ("kind", "created_by_claim_id", "bib_entry_id", "occurrence_id", "citing_derivation_id"),
          "PrimitiveAssertion": ("claim_id", "method", "basis")}
WORK_FIELD = {"ARXIV_BASE": "arxiv_base_id", "DOI": "doi", "OPENALEX": "openalex_id", "BIB_DIGEST": "bib_digest"}
# Relationship key properties (§5.2); every other type is unique per (type, start, end).
KEY_PROPS = {"RESOLVES_TO": ("method", "basis"), "SAME_WORK": ("basis",),
             "INCLUDES": ("admission", "round", "sampling_record_id")}


def hexdigest(value):
    return digest(canonical(value))[7:]


def make_id(prefix, value):
    return prefix + ":" + hexdigest(value)


def paper_version_id(arxiv_base_id, version):
    return f"arxiv:{arxiv_base_id}v{version}"


def paper_version_parts(paper_version_id):
    """(arxiv base id, version) of ``arxiv:<base>v<n>``."""
    base, version = re.fullmatch(r"arxiv:(.+)v([1-9][0-9]*)", paper_version_id).groups()
    return base, int(version)


def occurrence_id(paper_version_id, path, byte_start, byte_end, span_sha256):
    return make_id("occ", {"paper_version_id": paper_version_id, "path": path, "byte_start": byte_start,
                           "byte_end": byte_end, "span_sha256": span_sha256})


def anchor_id(paper_version_id, path, byte_start, byte_end):
    """A ``\\cite`` command's span; its keys' requests share it as ``citation_group`` (§3.4)."""
    return make_id("anchor", {"paper_version_id": paper_version_id, "path": path,
                              "byte_start": byte_start, "byte_end": byte_end})


def proof_derivation(proof_occurrence_ids):
    return "proof:" + digest(canonical(sorted(proof_occurrence_ids)))


def unlocated_derivation(method, k):
    return f"unlocated:{method}:{k}"


def source_derivation(paper_version_id, upstream_claim_ids):
    """``source:<pv>:<match_key>``, match_key = digest(sorted upstream claim ids) (§3.3)."""
    return f"source:{paper_version_id}:" + digest(canonical(sorted(upstream_claim_ids)))


def identity(label, row):
    """The §5.2 identity fields of a row (label = GraphDelta node label, or 'Edge')."""
    if label == "Work":
        return {"identity_basis": row["identity_basis"], "value": row[WORK_FIELD[row["identity_basis"]]]}
    if label == "Edge":
        if row["type"] == "PREMISE_OF":
            return {"type": "PREMISE_OF", "end_id": row["end_id"], "position": row["props"]["position"]}
        return {"type": row["type"], "start_id": row["start_id"], "end_id": row["end_id"],
                **{key: row["props"][key] for key in KEY_PROPS.get(row["type"], ())}}
    out = {key: row[key] for key in FIELDS[label] if key in row}
    if label == "Claim":
        out["occurrence_ids"] = sorted(out["occurrence_ids"])
        if row.get("part", "whole") != "whole" and "locator" in row:  # a part is named by where it was quoted
            out["locator"] = [row["locator"][key] for key in ("artifact", "start_byte", "end_byte")]
    elif label == "Junction":
        out["legs"] = [[leg["premise_id"], leg["role"], leg["use_site"]] for leg in out["legs"]]
    elif label == "BibEntry":
        out["locator"] = [out["locator"][key] for key in ("artifact", "start_byte", "end_byte")]
    return out


def seal(label, row):
    """Return row with id and content_sha256."""
    ident = identity(label, row)
    rid = paper_version_id(row["arxiv_base_id"], row["version"]) if label == "PaperVersion" else make_id(PREFIX[label], ident)
    return {"id": rid, "content_sha256": digest(canonical(ident)), **row}


def edge(type_, start_id, end_id, props=None):
    return seal("Edge", {"type": type_, "start_id": start_id, "end_id": end_id, "props": props or {}})


def logical_edges(junction):
    """The PREMISE_OF and CONCLUDES rows a projection derives from a junction (never in a delta)."""
    return [*(edge("PREMISE_OF", leg["premise_id"], junction["id"],
                   {"position": index, "role": leg["role"], "use_site": leg["use_site"]})
              for index, leg in enumerate(junction["legs"])),
            edge("CONCLUDES", junction["id"], junction["conclusion_id"])]


def issue(code, subject, detail, evidence=None):
    """A v0.3 ``Issue`` row; the id covers everything it says."""
    row = {"code": code, "subject": subject, "detail": detail, **({} if evidence is None else {"evidence": evidence})}
    return {"id": make_id("issue", row), **row}


def schema_error(schema, instance):
    """The most relevant JSON Schema error message (as contracts.validate reports it), or None."""
    error = best_match(Draft202012Validator(schema).iter_errors(instance))
    return error and error.message


def unique(rows, what="row"):
    """Rows sorted by id with repeats dropped; two different rows under one id are a host bug."""
    out = {}
    for row in rows:
        if out.setdefault(row["id"], row) != row:
            raise ValueError(f"two different {what}s share id {row['id']}")
    return [out[key] for key in sorted(out)]


def make_delta(stage, method, method_version, subject, nodes=None, edges=(), issues=(), *, parents=(), produced_by=(),
               measurements=None):
    """A validated GraphDelta (Appendix A); subject = (kind, id); measurements: host measurements about the subject,
    never graph content. Rows are de-duplicated and ordered by id, so equal content gives an equal delta_id = digest
    of the body without it (re-exported by ``delta``)."""
    nodes = {label: unique(rows, label) for label, rows in sorted((nodes or {}).items())}
    body = {"kind": "GraphDelta", "contract_version": "0.4.0", "stage": stage, "method": method,
            "method_version": method_version, "subject": {"kind": subject[0], "id": subject[1]},
            "parents": sorted(set(parents)), "produced_by": list(produced_by),
            "nodes": {label: rows for label, rows in nodes.items() if rows},
            "edges": unique(edges, "edge"), "issues": unique(issues, "issue"),
            **({} if measurements is None else {"measurements": measurements})}
    delta = {"delta_id": make_id("delta", body), **body}
    contracts.validate("GraphDelta", delta)
    return delta
