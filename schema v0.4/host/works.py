"""S4 works (spec §3.5, §3.6): BibEntry → Work by identifier precedence, RESOLVES_TO, host-rule SAME_WORK, and
the paper version's own arXiv work with VERSION_OF. Offline: no metadata adapter here. Work-identity
components under the three ``work_identity`` policies are invariants.work_components.

Precedence: arXiv base id, lowercased DOI, OpenAlex id, else digest(normalized title, year, first-author
surname). Upgrades never rename: DOI ``10.48550/arXiv.X`` is its own DOI work, linked to arXiv work X by
SAME_WORK ``HOST_RULE_ARXIV_DOI``. A Work row carries only identity-derived fields, so every entry that
resolves to it asserts the same row; a BIB_DIGEST work keeps its digest as ``bib_digest``, so G6 recomputes its id.
terminal_kind follows the v0.3 identifier rule (an arXiv DOI names an e-print).
"""
from __future__ import annotations

import re
from collections import Counter

from core import canonical, digest
from ingest import _base_id, _bib_field, _title_key

import contracts
import ids

METHOD, METHOD_VERSION = "HOST_RULE", "works-0.4.0"
ARXIV_DOI = re.compile(r"10\.48550/arxiv\.(.+)")
TERMINAL = {"ARXIV_BASE": "ARXIV_SOURCE_AVAILABLE", "DOI": "PREARXIV_DOI_NO_SOURCE",
            "OPENALEX": "PREARXIV_DOI_NO_SOURCE", "BIB_DIGEST": "FREE_TEXT_UNRESOLVED"}


def normalize_doi(value):
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value.strip().lower()).rstrip(".,;")
    return doi if re.fullmatch(r"10\.[0-9]+/\S+", doi) else None


def normalize_arxiv(value):
    """arXiv base id (no prefix, no version), or None."""
    try:
        base = _base_id(re.sub(r"^arxiv:", "", value.strip(), flags=re.I)).removeprefix("arxiv:")
    except ValueError:
        return None
    base = re.sub(r"^([a-z-]+)\.([a-z]{2})/", lambda m: f"{m[1]}.{m[2].upper()}/", base)  # lowercased DOIs: math.ag → math.AG
    return base if contracts.validator("ArxivBaseId").is_valid(base) else None


def doi_arxiv(doi):
    """The arXiv base id an arXiv DOI (``10.48550/arXiv.X``) names, or None."""
    match = ARXIV_DOI.fullmatch(doi)
    return match and normalize_arxiv(match[1])


def first_author_surname(v03_row):
    author = (v03_row.get("literal_fields") or {}).get("author") or _bib_field(v03_row["text"].encode(), "author")
    first = re.split(r"\s+and\s+", (author or "").strip())[0]
    return _title_key(first.split(",")[0] if "," in first else (first.split() or [""])[-1]) or None


def work_identity(entry, v03_row):
    """(identity_basis, value) of a BibEntry row, or (None, issue code)."""
    ident = entry["identifiers"]
    if max(Counter(item.split(":")[0] for item in ident["evidence"]).values(), default=0) > 1:
        return None, "WORK_IDENTITY_AMBIGUOUS"
    if ident["arxiv_id"] and (base := normalize_arxiv(ident["arxiv_id"])):
        return "ARXIV_BASE", base
    if ident["doi"] and (doi := normalize_doi(ident["doi"])):
        return "DOI", doi
    if re.fullmatch(r"W[0-9]+", ident["openalex_id"] or ""):
        return "OPENALEX", ident["openalex_id"]
    title, year, surname = _title_key(entry.get("title") or ""), entry.get("year"), first_author_surname(v03_row)
    if title and year and surname:
        return "BIB_DIGEST", digest(canonical([title, year, surname]))
    return None, "WORK_IDENTITY_INSUFFICIENT"


def work_row(basis, value):
    terminal = "ARXIV_SOURCE_AVAILABLE" if basis == "DOI" and doi_arxiv(value) else TERMINAL[basis]
    return ids.seal("Work", {"identity_basis": basis, ids.WORK_FIELD[basis]: value, "work_kind": "UNKNOWN", "terminal_kind": terminal})


def build_metadata_doi_delta(work_rows, doi_index, subject_id, *, parents=(), produced_by=()):
    """S4 metadata delta (HOST_RULE, offline): a DOI work whose DOI exactly one arXiv record of a frozen metadata snapshot
    declares is the SAME_WORK as that e-print (basis HOST_RULE_ARXIV_METADATA_DOI, §3.5), which makes it expandable.
    work_rows: Work rows of the view; doi_index: acquire.snapshot_dois output; subject_id names the snapshot. A DOI
    several records declare is an issue, never a guess."""
    works, edges, issues = {}, [], []
    for work in sorted(work_rows, key=lambda w: w["id"]):
        if work["identity_basis"] != "DOI" or doi_arxiv(work["doi"]) or work["doi"] not in doi_index:
            continue
        bases = [base for base in (normalize_arxiv(pid) for pid in doi_index[work["doi"]]) if base]
        if len(bases) != 1:
            issues.append(ids.issue("WORK_METADATA_DOI_AMBIGUOUS", work["id"], "Several snapshot records declare this DOI",
                                    {"doi": work["doi"], "arxiv_base_ids": bases}))
            continue
        other = works.setdefault((row := work_row("ARXIV_BASE", bases[0]))["id"], row)
        edges.append(ids.edge("SAME_WORK", work["id"], other["id"], {"basis": "HOST_RULE_ARXIV_METADATA_DOI"}))
    return ids.make_delta("S4", METHOD, METHOD_VERSION + "+metadata-doi", ("MANIFEST", subject_id), {"Work": works.values()}, edges,
                          issues, parents=parents, produced_by=produced_by)


def build_work_delta(s3, extraction, *, produced_by=()):
    """S4 delta over its parent S3 delta (whose subject paper version and BibEntry rows it reads); ``extraction`` is
    the v0.3 record S3 was built from (author fields for BIB_DIGEST)."""
    pv, v03 = s3["subject"]["id"], {row["id"]: row for row in extraction["bibliography"]}
    own = work_row("ARXIV_BASE", ids.paper_version_parts(pv)[0])
    works, edges, issues = {own["id"]: own}, [ids.edge("VERSION_OF", pv, own["id"])], []
    for entry in s3["nodes"].get("BibEntry", []):
        basis, value = work_identity(entry, v03[entry["v03_id"]])
        if basis is None:
            issues.append(ids.issue(value, entry["id"], "No work identity from explicit bibliography fields", {"bib_entry_id": entry["id"]}))
            continue
        work = works.setdefault((row := work_row(basis, value))["id"], row)
        edges.append(ids.edge("RESOLVES_TO", entry["id"], work["id"], {"method": METHOD, "basis": basis}))
        if basis == "DOI" and (arxiv := doi_arxiv(value)):
            other = works.setdefault((row := work_row("ARXIV_BASE", arxiv))["id"], row)
            edges.append(ids.edge("SAME_WORK", work["id"], other["id"], {"basis": "HOST_RULE_ARXIV_DOI"}))
    return ids.make_delta("S4", METHOD, METHOD_VERSION, ("PAPER_VERSION", pv), {"Work": works.values()}, edges,
                          issues, parents=[s3["delta_id"]], produced_by=produced_by)
