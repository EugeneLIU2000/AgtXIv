"""S3 anchor graph (spec §3, §7): DETERMINISTIC_ANCHOR and theorem-header HOST_RULE deltas from a v0.3 ``ingest.extract_paper`` record.

``sources`` maps every v0.3 source path of the record to its frozen bytes. Row paths and ids are relative
to the paper's source root, so relocating the corpus data root renames nothing. Citation is not
dependency (I-3): a ``\\cite`` becomes a request only inside an owned proof; legs stay UNCLASSIFIED; a
``\\cite`` in a theorem-like header is RESTATES_RESULT_OF, a host rule with its own delta. Rows several
methods assert (occurrence claims, placeholders) are built only here, so equal ids carry equal rows.
Readings keep the environment text as VERBATIM display_text: deltas are private artifacts, and the
loader must drop it unless the paper's redistribution is OPEN (I-13); it is not identity content.
"""
from __future__ import annotations

import posixpath
import re

from core import canonical, digest
from ingest import _mask_comments, _overlap

import ids

METHOD, METHOD_VERSION = "DETERMINISTIC_ANCHOR", "anchors-0.4.0"
THEOREM_LIKE = "THEOREM_LIKE_ENVIRONMENT"
ENVIRONMENTS = (THEOREM_LIKE, "DEFINITION_ENVIRONMENT")
KINDS = (("thm", "theorem"), ("theorem", "theorem"), ("lem", "lemma"), ("prop", "proposition"),
         ("cor", "corollary"), ("def", "definition"))
BEGIN = re.compile(rb"\\begin\s*\{([A-Za-z]+)\*?\}")
PROOF = re.compile(rb"\\begin\s*\{proof\}")
REF = re.compile(rb"\\(?:ref|autoref|cref|Cref)\*?\s*\{([^{}]*)\}")
NO_CONDITIONS = digest(canonical([]))


def _optional(data, i):
    """Half-open span of the TeX optional argument ``[...]`` at i (after whitespace), or None."""
    while i < len(data) and data[i] in b" \t\r\n":
        i += 1
    if i >= len(data) or data[i] != 91:
        return None
    square = brace = 0
    j = i
    while j < len(data):
        c = data[j]
        if c == 92:
            j += 2
            continue
        brace += (c == 123) - (c == 125)
        if brace == 0 and c in (91, 93):
            square += 1 if c == 91 else -1
            if square == 0:
                return i, j + 1
        j += 1
    return None


def span_key(span):
    return span["path"], span["byte_start"], span["byte_end"]


def index(extraction, sources):
    """One paper's occurrence ids, claims, labels and proof ownership (adjacency, then PROOF_HEADER_OWNERSHIP)."""
    paper = extraction["paper"]
    root = (paper.get("source_root") or ".").rstrip("/")
    claims = {row["id"]: row for row in extraction["claims"]}
    P = {"pv": paper["id"], "root": root, "sources": sources, "claims": claims, "labels": extraction["labels"],
         "anchors": extraction["anchors"], "bibliography": extraction["bibliography"], "headers": {}, "issues": []}
    P["occ"] = {cid: occurrence(P, row["source"]) for cid, row in claims.items()}
    # Two S2 claims with the same span share one occurrence id; the canonical one prefers an environment kind.
    P["by_occ"] = {}
    for cid in sorted(claims, key=lambda cid: (claims[cid]["kind"] in ENVIRONMENTS, cid)):
        P["by_occ"][P["occ"][cid]] = cid
    owner = {span_key(proof): cid for cid, row in claims.items() for proof in row["proof_sources"]}
    proofs = {span_key(proof): proof for proof in extraction["proof_spans"]}
    for key, proof in sorted(proofs.items()):
        clean = _mask_comments(sources[proof["path"]])
        begin = PROOF.match(clean, proof["byte_start"])
        header = begin and _optional(clean, begin.end())
        if not header:
            continue
        P["headers"][key] = header
        labels = [P["labels"].get(ref.decode("utf-8", "replace").strip(), [])
                  for ref in REF.findall(clean[header[0]:header[1]])]
        if not labels:
            continue
        targets = {cid for rows in labels for row in rows for cid in row["claim_ids"] if claims[cid]["kind"] == THEOREM_LIKE}
        if len(targets) != 1 or any(len(rows) != 1 for rows in labels):
            P["issues"].append(ids.issue("PROOF_HEADER_OWNER_UNRESOLVED", P["pv"], "Proof header references no unique theorem-like claim", {"proof": proof}))
            continue
        target = targets.pop()
        if owner.get(key) not in (None, target):
            P["issues"].append(ids.issue("PROOF_OWNER_REASSIGNED", P["pv"], "PROOF_HEADER_OWNERSHIP overrides adjacency ownership",
                                         {"proof": proof, "adjacent_owner": owner[key], "header_owner": target}))
        owner[key] = target
    P["owned"], P["cites"] = {}, {}
    for key in sorted(owner):
        P["owned"].setdefault(owner[key], []).append(proofs[key])
    for anchor in P["anchors"]:  # (proof derivation, v0.3 bib id) → the entry's first \cite in that proof span
        if anchor["command"].startswith("cite") and len(anchor["candidate_target_ids"]) == 1:
            for _, site, derivation in sites(P, anchor):
                if site == "PROOF":
                    P["cites"].setdefault((derivation, anchor["candidate_target_ids"][0]), anchor)
    return P


def rel(P, path):
    return posixpath.relpath(path, P["root"]) if P["root"] != "." and path.startswith(P["root"] + "/") else path


def occurrence(P, span):
    return ids.occurrence_id(P["pv"], rel(P, span["path"]), span["byte_start"], span["byte_end"], span["span_sha256"])


def source_span(P, span):
    """An ingest span as a v0.3 ``SourceSpan``, checked against the frozen bytes."""
    data = P["sources"][span["path"]]
    start, end = span["byte_start"], span["byte_end"]
    if digest(data) != span["sha256"] or digest(data[start:end]) != span["span_sha256"]:
        raise ValueError("frozen source bytes differ from the extraction record: " + span["path"])
    return {"artifact": rel(P, span["path"]), "source_sha256": span["sha256"], "start_byte": start, "end_byte": end,
            "span_sha256": span["span_sha256"], "line_start": data.count(b"\n", 0, start) + 1,
            "line_end": data.count(b"\n", 0, end - 1) + 1}


def occurrence_claim(P, cid):
    """The whole Claim of one S2 occurrence; identical in every delta that asserts it."""
    row = P["claims"][cid]
    return ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": P["pv"], "occurrence_ids": [P["occ"][cid]],
                              "part": "whole", "locator": source_span(P, row["source"]), "occurrence_kind": row["kind"]})


def bib_entries(P):
    """BibEntry rows keyed by v0.3 bibliography id; an identifier is kept only when it is unique."""
    out = {}
    for row in P["bibliography"]:
        if not row["key"]:
            P["issues"].append(ids.issue("BIB_ENTRY_KEY_EMPTY", P["pv"], "Bibliography entry without a citation key", {"v03_id": row["id"]}))
            continue
        arxiv, doi = row["identifiers"]["arxiv"], row["identifiers"]["doi"]
        entry = {"paper_version_id": P["pv"], "citation_key": row["key"], "locator": source_span(P, row["source"]),
                 "identifiers": {"arxiv_id": arxiv[0] if len(arxiv) == 1 else None, "doi": doi[0] if len(doi) == 1 else None,
                                 "openalex_id": None, "resolution_basis": "SOURCE_EXPLICIT" if len(arxiv) == 1 or len(doi) == 1 else "UNRESOLVED",
                                 "evidence": [*arxiv, *("doi:" + value for value in doi)]},
                 "v03_id": row["id"]}
        year = re.search(r"\b\d{4}\b", row.get("year") or "")
        entry.update({key: value for key, value in (("title", row.get("title")), ("year", year and int(year[0])),
                                                    ("entry_type", row.get("entry_type"))) if value})
        out[row["id"]] = ids.seal("BibEntry", entry)
    return out


def sites(P, anchor):
    """(v0.3 claim id, use_site, derivation_id) of each conclusion of an anchor (§3.2); proof-header anchors have none."""
    span, out = anchor["source"], []
    for cid, proofs in sorted(P["owned"].items()):
        for proof in proofs:
            header = P["headers"].get(span_key(proof))
            in_header = header and header[0] <= span["byte_start"] and span["byte_end"] <= header[1] and span["path"] == proof["path"]
            if _overlap(span, proof) and not in_header:
                out.append((cid, "PROOF", ids.proof_derivation([occurrence(P, proof)])))
    owners = {row[0] for row in out}
    return out + [(cid, "STATEMENT", "statement") for cid, row in sorted(P["claims"].items())
                  if row["kind"] in ENVIRONMENTS and cid not in owners and _overlap(span, row["source"])]


def resolve(P, anchor, bib):
    """('bib', BibEntry row) of a ``\\cite``, ('claim' | 'occurrence', v0.3 claim id) of a label reference, or
    (None, code): the v0.3 resolution, or BIB_ENTRY_KEY_EMPTY for an entry bib_entries dropped."""
    found = anchor["candidate_target_ids"]
    if anchor["command"].startswith("cite"):
        if len(found) == 1 and found[0] in bib:
            return "bib", bib[found[0]]
        return None, "BIB_ENTRY_KEY_EMPTY" if len(found) == 1 else anchor["resolution"]
    if anchor["resolution"] != "RESOLVED_CANDIDATE" or len(found) != 1:
        return None, "AMBIGUOUS_LABEL" if len(found) > 1 else anchor["resolution"]
    return ("claim" if anchor["command"] != "eqref" and P["claims"][found[0]]["kind"] in ENVIRONMENTS else "occurrence"), found[0]


def request(P, conclusion, derivation, entry):
    """The EXTERNAL_REQUEST of claim ``conclusion`` on a BibEntry row under a derivation (§3.4), as every method
    asserts it: in a proof span it carries citation_group and locator_text of the entry's first ``\\cite`` there."""
    anchor, extra = P["cites"].get((derivation, entry["v03_id"])), {}
    if anchor:
        span = anchor["source"]
        extra["citation_group"] = ids.anchor_id(P["pv"], rel(P, span["path"]), span["byte_start"], span["byte_end"])
        extra.update({"locator_text": note} if (note := locator_text(P, anchor)) else {})
    return ids.seal("Placeholder", {"kind": "EXTERNAL_REQUEST", "paper_version_id": P["pv"], "created_by_claim_id": conclusion,
                                    "citing_derivation_id": derivation, "bib_entry_id": entry["id"], **extra})


def non_environment(P, conclusion, derivation, occurrence_id):
    """The UNRESOLVED_OCCURRENCE of an equation or prose target (§3.4), as every method asserts it."""
    return ids.seal("Placeholder", {"kind": "UNRESOLVED_OCCURRENCE", "paper_version_id": P["pv"], "created_by_claim_id": conclusion,
                                    "citing_derivation_id": derivation, "occurrence_id": occurrence_id, "reason": "NON_ENVIRONMENT_TARGET"})


def locator_text(P, anchor):
    """The last non-empty optional argument of a ``\\cite`` (natbib post-note), from the source bytes."""
    span = anchor["source"]
    raw = P["sources"][span["path"]][span["byte_start"]:span["byte_end"]]
    notes = [note.strip() for note in re.findall(rb"\[([^\]]*)\]", raw[:raw.rfind(b"{")])]
    return next((note.decode("utf-8", "replace") for note in reversed(notes) if note), None)


def in_theorem_header(P, anchor, cid):
    row, span = P["claims"][cid], anchor["source"]
    if row["kind"] != THEOREM_LIKE or row["source"]["path"] != span["path"]:
        return False
    clean = _mask_comments(P["sources"][span["path"]])
    begin = BEGIN.search(clean, row["source"]["byte_start"], row["source"]["byte_end"])
    header = begin and _optional(clean, begin.end())
    return bool(header) and header[0] <= span["byte_start"] and span["byte_end"] <= header[1]


def kind_of(name, table=KINDS):
    """The reading kind an environment or locator word names by prefix ('Lemma' → lemma), or None."""
    return next((kind for prefix, kind in table if name.lower().startswith(prefix)), None)


def _kind(row):
    begin = BEGIN.search(row["text"].encode())
    return kind_of(begin[1].decode() if begin else "") or "UNKNOWN"


def build_anchor_delta(extraction, sources, *, parents, produced_by=()):
    """S3 delta; ``parents`` include the S1 acquisition delta, the only delta asserting the PaperVersion row (S3 never
    re-asserts it). The measured deterministic_yield goes into the delta's measurements, not into a row."""
    P = index(extraction, sources)
    pv = P["pv"]
    claims = {cid: occurrence_claim(P, cid) for cid, row in P["claims"].items() if row["kind"] in ENVIRONMENTS}
    readings = [ids.seal("ClaimReading", {"claim_id": claim["id"], "method": METHOD, "method_version": METHOD_VERSION,
                                          "kind": _kind(P["claims"][cid]), "statement_sha256": digest(P["claims"][cid]["text"].encode()),
                                          "conditions_sha256": NO_CONDITIONS, "display_text": P["claims"][cid]["text"],
                                          "display_text_class": "VERBATIM"}) for cid, claim in claims.items()]
    bib = bib_entries(P)
    edges = [*(ids.edge("STATES", pv, row["id"]) for row in claims.values()),
             *(ids.edge("READS", row["id"], row["claim_id"]) for row in readings),
             *(ids.edge("HAS_ENTRY", pv, row["id"]) for row in bib.values())]
    placeholders, legs, issues, proof_owned = {}, {}, P["issues"], 0
    add = lambda row: placeholders.setdefault(row["id"], row)["id"]
    for anchor in P["anchors"]:
        found = sites(P, anchor)
        proof_owned += any(site == "PROOF" for _, site, _ in found)
        if not found:
            continue
        kind, ref = resolve(P, anchor, bib)
        if kind is None:
            issues.append(ids.issue(ref, anchor["id"], "Anchor yields no graph element", {"anchor_id": anchor["id"], "key": anchor["key"]}))
            continue
        for cid, site, derivation in found:
            conclusion = claims[cid]["id"]
            if kind == "bib" and site == "STATEMENT":  # a theorem-header \cite is RESTATES_RESULT_OF (build_restates_delta)
                if not in_theorem_header(P, anchor, cid):
                    edges.append(ids.edge("MENTIONS", conclusion, ref["id"]))
                continue
            if kind == "bib":
                premise = add(request(P, conclusion, derivation, ref))
            elif kind == "claim":
                premise = claims[ref]["id"]
            else:
                premise = add(non_environment(P, conclusion, derivation, P["occ"][ref]))
            if premise == conclusion:
                issues.append(ids.issue("ANCHOR_SELF_REFERENCE", anchor["id"], "A claim is not its own premise (G4)", {"anchor_id": anchor["id"]}))
                continue
            legs.setdefault((conclusion, derivation), []).append((premise, site))
    junctions = []
    for (conclusion, derivation), items in sorted(legs.items()):  # the derivation fixes the use site
        out = [{"premise_id": premise, "role": "UNCLASSIFIED", "use_site": site, "flags": []} for premise, site in dict(items).items()]
        groups = sorted({placeholders[leg["premise_id"]]["citation_group"] for leg in out
                         if "citation_group" in placeholders.get(leg["premise_id"], {})})
        junctions.append(ids.seal("Junction", {"conclusion_id": conclusion, "derivation_id": derivation, "reading_method": METHOD,
                                               "method_version": METHOD_VERSION, "legs": out,
                                               "grouping_basis": "ANCHOR_STATEMENT_SPAN" if derivation == "statement" else "ANCHOR_PROOF_SPAN",
                                               **({"citation_groups": groups} if groups else {})}))
    edges += [ids.edge("REQUESTS_FROM", row["id"], row["bib_entry_id"]) for row in placeholders.values() if row["kind"] == "EXTERNAL_REQUEST"]
    measured = {"deterministic_yield": {
        "theorem_like_environments": sum(row["kind"] == THEOREM_LIKE for row in P["claims"].values()),
        "owned_proofs": sum(map(len, P["owned"].values())), "proof_owned_anchors": proof_owned,
        "junction_bearing_conclusions": len({row["conclusion_id"] for row in junctions})}}
    nodes = {"Claim": claims.values(), "ClaimReading": readings, "BibEntry": bib.values(),
             "Placeholder": placeholders.values(), "Junction": junctions}
    return ids.make_delta("S3", METHOD, METHOD_VERSION, ("PAPER_VERSION", pv), nodes, edges, issues, parents=parents,
                          produced_by=produced_by, measurements=measured)


def build_restates_delta(extraction, sources, s3, *, produced_by=()):
    """RESTATES_RESULT_OF (§7): a resolved ``\\cite`` in a theorem-like header, a HOST_RULE with its own delta,
    never a request or a leg; its parent is the S3 delta whose Claim and BibEntry rows it joins."""
    P = index(extraction, sources)
    bib, edges = {row["v03_id"]: row for row in s3["nodes"].get("BibEntry", [])}, []
    for anchor in P["anchors"]:
        kind, ref = resolve(P, anchor, bib)
        edges += [ids.edge("RESTATES_RESULT_OF", occurrence_claim(P, cid)["id"], ref["id"]) for cid, site, _ in sites(P, anchor)
                  if kind == "bib" and site == "STATEMENT" and in_theorem_header(P, anchor, cid)]
    return ids.make_delta("S3", "HOST_RULE", METHOD_VERSION, ("PAPER_VERSION", P["pv"]), None, edges, (),
                          parents=[s3["delta_id"]], produced_by=produced_by)
