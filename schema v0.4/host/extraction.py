"""S6 extraction (spec §5.2, §7.2) without a model call: prompt assembly and response → delta, in two modes.

LOCAL_BATCH (``paper.extract_local``): one claim batch of environments with its local context. WHOLE_PAPER_FOCUS
(``paper.extract_focus``): the whole paper as a byte-identical prefix shared by every call of the paper (so a provider
prompt cache bills it at the cache-hit price after the first call), then one focus span; occurrences are named by short
aliases, and every internal premise is the claim of the occurrence it names, of any kind, so derivations through
display equations stay connected. The response schema is v0.3 ``CLAIM_RESPONSE_SCHEMA`` with its CLAIM_REFERENCE_V1
fields, unchanged; the one v0.4 rule JSON Schema cannot state (several claims of one occurrence each need a
distinguishing locator inside it) is host-checked. Any rejected claim makes the whole response a failed delta (issues
only), never a guess. Legs are UNCLASSIFIED with use_site UNKNOWN: the v0.3 schema records neither.
"""
from __future__ import annotations

import copy
import re
from collections import defaultdict
from itertools import groupby

from core import canonical, digest
from ingest import _mask_comments
from model import CLAIM_RESPONSE_SCHEMA, _candidate_reference_issues, bind_source_locators

import anchors
import ids

METHOD, OPERATION, FOCUS_OPERATION = "MODEL_EXTRACTION", "paper.extract_local", "paper.extract_focus"
RESPONSE_SCHEMA = CLAIM_RESPONSE_SCHEMA
SECTION = re.compile(rb"\\(?:part|chapter|section|subsection|subsubsection|paragraph)\*?\s*[\[{]")
INSTRUCTION = (
    "Operation paper.extract_local. SOURCE DATA is a local excerpt of one paper, not the whole paper: the batch's "
    "environments and their owned proofs, the statements of occurrences they reference, the bibliography entries "
    "they cite and some preceding prose; inventory gives each item's id and byte span once, without text. Emit only "
    "claims stated in the batch environments or their owned proofs. source_occurrence_ids name batch environments. "
    "Cite internal support only by inventory occurrence ids (internal_support_occurrence_ids) or by the zero-based "
    "position of another claim you emit (internal_support_claim_indexes, never the claim's own). external_citation_keys "
    "lists supplied bibliography keys whose results the statement or proof uses; keys cited for attribution, context or "
    "comparison go in external_mention_citation_keys, never in both. When one occurrence yields several claims, give each "
    "a source_locators quotation inside that occurrence; otherwise all of them are rejected. A claim with no listed "
    "occurrence needs source_locators. exact_text is copied byte for byte and must be unique within its file. Support "
    "outside the supplied data goes in unresolved_dependencies: outside knowledge cannot fill a missing dependency. "
    "Never invent an id or key. Confidence is only a self-report.")
FOCUS_INSTRUCTION = (
    "Operation paper.extract_focus. PAPER DATA is the whole paper: every source file, and an inventory naming each "
    "occurrence once by a short alias (o1, o2, ...) with its kind and byte span, without repeating its text. FOCUS names "
    "one span of one file and the aliases of the occurrences that begin inside it. Emit every mathematical claim stated "
    "inside the focus, and only those: a claim names focus occurrences in source_occurrence_ids or, when none fits, "
    "quotes itself in source_locators inside the focus span. Cite internal support by any inventory alias of the paper "
    "(internal_support_occurrence_ids), including display equations a derivation uses, or by the zero-based position of "
    "another claim you emit (internal_support_claim_indexes, never the claim's own). external_citation_keys lists "
    "bibliography keys whose results the statement or its derivation uses; keys cited for attribution, context or "
    "comparison go in external_mention_citation_keys, never in both. When one occurrence yields several claims, give each "
    "a source_locators quotation inside that occurrence; otherwise all of them are rejected. exact_text is copied byte "
    "for byte and must be unique within its file, and never inside a TeX comment. A focus that states no claim returns no "
    "claims and one unread_or_uncertain_scope entry saying so. Support outside the paper goes in unresolved_dependencies: "
    "outside knowledge cannot fill a missing dependency. Never invent an alias or key. Confidence is only a self-report.")
BODY_SUFFIXES, CONTEXT_SUFFIXES = (".tex", ".ltx"), (".bbl", ".bib")  # style and class files are never sent


def _span(P, span):
    return {"path": anchors.rel(P, span["path"]), "byte_start": span["byte_start"], "byte_end": span["byte_end"]}


def _within(span, row):
    return span["path"] == row["path"] and row["byte_start"] <= span["byte_start"] and span["byte_end"] <= row["byte_end"]


def build_local_prompt(extraction, sources, occurrence_ids, *, prose_bytes):
    """§7.2 prompt for one claim batch (S2 occurrence ids); ``prose_bytes`` is the policy bound B."""
    P = anchors.index(extraction, sources)
    by_occ = P["by_occ"]
    if not occurrence_ids or set(occurrence_ids) - by_occ.keys():
        raise ValueError("a claim batch names distinct S2 occurrence ids of this paper")
    batch = sorted({by_occ[occ] for occ in occurrence_ids}, key=lambda cid: anchors.span_key(P["claims"][cid]["source"]))
    proofs = [(cid, proof) for cid in batch for proof in P["owned"].get(cid, [])]
    spans = [P["claims"][cid]["source"] for cid in batch] + [proof for _, proof in proofs]
    inside = lambda span: any(_within(span, row) for row in spans)
    bib, v03, referenced, cited = anchors.bib_entries(P), {row["id"]: row for row in P["bibliography"]}, set(), set()
    for anchor in P["anchors"]:
        kind, ref = anchors.resolve(P, anchor, bib) if inside(anchor["source"]) else (None, None)
        if kind == "bib":
            cited.add(ref["v03_id"])
        elif kind and ref not in batch:
            referenced.add(ref)
    inventory = [{"id": P["occ"][cid], "role": "ENVIRONMENT", "kind": P["claims"][cid]["kind"], **_span(P, P["claims"][cid]["source"])} for cid in batch]
    inventory += [{"id": anchors.occurrence(P, proof), "role": "OWNED_PROOF", "owner_id": P["occ"][cid], **_span(P, proof)} for cid, proof in proofs]
    inventory += [{"id": P["occ"][cid], "role": "REFERENCED", "kind": P["claims"][cid]["kind"], **_span(P, P["claims"][cid]["source"])} for cid in sorted(referenced)]
    inventory += [{"id": bib[bid]["id"], "role": "BIBLIOGRAPHY", "key": bib[bid]["citation_key"], **_span(P, v03[bid]["source"])}
                  for bid in sorted(cited)]
    # Prose stops at the previous environment or proof, so no statement text is sent twice.
    blocks = [row["source"] for row in P["claims"].values() if row["kind"] in anchors.ENVIRONMENTS] + extraction["proof_spans"]
    prose = []
    for cid in batch if prose_bytes > 0 else ():
        span = P["claims"][cid]["source"]
        data, end = sources[span["path"]], span["byte_start"]
        heads = [match.start() for match in SECTION.finditer(_mask_comments(data), 0, end)]
        start = max([0, end - prose_bytes, *heads[-1:], *(row["byte_end"] for row in blocks if row["path"] == span["path"] and row["byte_end"] <= end)])
        while start < end and data[start] & 0xC0 == 0x80:
            start += 1
        if data[start:end].strip():
            prose.append({"id": f"prose:{len(prose)}", "text": data[start:end].decode("utf-8")})
            inventory.append({"id": prose[-1]["id"], "role": "PROSE", "path": anchors.rel(P, span["path"]), "byte_start": start, "byte_end": end})
    payload = {"operation": OPERATION, "paper_version_id": P["pv"],
               "batch_id": ids.make_id("batch", {"paper_version_id": P["pv"], "occurrence_ids": sorted(occurrence_ids)}),
               "batch_occurrence_ids": [P["occ"][cid] for cid in batch],
               "environments": [{"id": P["occ"][cid], "kind": P["claims"][cid]["kind"], "text": P["claims"][cid]["text"]} for cid in batch],
               "owned_proofs": [{"id": anchors.occurrence(P, proof), "owner_id": P["occ"][cid],
                                 "text": sources[proof["path"]][proof["byte_start"]:proof["byte_end"]].decode("utf-8")} for cid, proof in proofs],
               "referenced_statements": [{"id": P["occ"][cid], "kind": P["claims"][cid]["kind"], "text": P["claims"][cid]["text"]}
                                         for cid in sorted(referenced) if not inside(P["claims"][cid]["source"])],
               "bibliography": [{"id": bib[bid]["id"], "key": bib[bid]["citation_key"], "text": v03[bid]["text"]} for bid in sorted(cited)],
               "preceding_prose": prose, "inventory": inventory}
    return {"prompt": INSTRUCTION + "\nSOURCE DATA:\n" + canonical(payload).decode("utf-8"),
            "response_schema": RESPONSE_SCHEMA, "context": payload}


def _canonical(P):
    """One S2 claim per occurrence id (anchors.index prefers an environment kind), in source order."""
    return sorted(set(P["by_occ"].values()), key=lambda cid: anchors.span_key(P["claims"][cid]["source"]))


def plan_foci(extraction, sources, *, focus_bytes):
    """§7.2 WHOLE_PAPER_FOCUS: the paper's S2 occurrences in source order, cut per file into foci of about
    ``focus_bytes``. A cut is made only before an occurrence that starts at or after the end of every occurrence already
    in the focus, so no occurrence straddles two foci, occurrences sharing a start stay together, and occurrences nested
    in a long one stay in its focus (which may then exceed the budget). A file's focus scopes are disjoint, the first
    starts at byte 0 and the last ends at the end of the file, so a quoted new claim can belong to one call only."""
    if type(focus_bytes) is not int or focus_bytes < 256:
        raise ValueError("focus_bytes is an integer >= 256 (CorpusManifest.extraction)")
    P = anchors.index(extraction, sources)
    cut = []
    for path, group in groupby(_canonical(P), key=lambda cid: P["claims"][cid]["source"]["path"]):
        members, first, reach = [], None, 0
        for cid in group:
            span = P["claims"][cid]["source"]
            if members and span["byte_start"] >= reach and span["byte_end"] - first > focus_bytes:
                cut.append((path, first, members))
                members = []
            if not members:
                first = span["byte_start"]
            members.append(cid)
            reach = max(reach, span["byte_end"])
        cut.append((path, first, members))
    foci = []
    for n, (path, first, members) in enumerate(cut):
        start = 0 if n == 0 or cut[n - 1][0] != path else first
        end = cut[n + 1][1] if n + 1 < len(cut) and cut[n + 1][0] == path else len(sources[path])
        rel = anchors.rel(P, path)
        foci.append({"focus_id": ids.make_id("focus", {"paper_version_id": P["pv"], "path": rel, "byte_start": start, "byte_end": end}),
                     "path": path, "byte_start": start, "byte_end": end, "claim_ids": members})
    return foci


def build_focus_prompts(extraction, sources, *, focus_bytes):
    """Every WHOLE_PAPER_FOCUS prompt of one paper: {prefix_sha256, prompts: [{focus_id, prompt, response_schema,
    context}]}. Each prompt is the shared prefix (instruction, every source file, the alias inventory, the bibliography
    keys) followed by its own FOCUS block, so only the last few hundred bytes differ between calls."""
    P = anchors.index(extraction, sources)
    ordered = _canonical(P)
    alias = {cid: f"o{n}" for n, cid in enumerate(ordered, 1)}
    bib = anchors.bib_entries(P)
    files = []
    for path in sorted(sources):
        if not path.lower().endswith(BODY_SUFFIXES + CONTEXT_SUFFIXES):
            continue
        try:  # a body file is sent byte-exact; a bibliography or an undecodable file only as context (no locator binds there)
            text, context_only = sources[path].decode("utf-8"), path.lower().endswith(CONTEXT_SUFFIXES)
        except UnicodeDecodeError:
            text, context_only = sources[path].decode("utf-8", errors="replace"), True
        files.append({"path": anchors.rel(P, path), "text": text, **({"context_only": True} if context_only else {})})
    paper = {"operation": FOCUS_OPERATION, "paper_version_id": P["pv"], "files": files,
             "inventory": [{"alias": alias[cid], "kind": P["claims"][cid]["kind"], **_span(P, P["claims"][cid]["source"])} for cid in ordered],
             "bibliography_keys": sorted({row["citation_key"] for row in bib.values()})}
    prefix = FOCUS_INSTRUCTION + "\nPAPER DATA:\n" + canonical(paper).decode("utf-8") + "\n"
    prefix_sha256 = digest(prefix.encode())
    prompts = []
    for focus in plan_foci(extraction, sources, focus_bytes=focus_bytes):
        inside, rel = set(focus["claim_ids"]), anchors.rel(P, focus["path"])
        block = {"focus_id": focus["focus_id"], "path": rel, "byte_start": focus["byte_start"], "byte_end": focus["byte_end"],
                 "occurrences": [alias[cid] for cid in focus["claim_ids"]]}
        inventory = [{"id": P["occ"][cid], "alias": alias[cid], "role": "ENVIRONMENT" if cid in inside else "REFERENCED",
                      "kind": P["claims"][cid]["kind"], **_span(P, P["claims"][cid]["source"])} for cid in ordered]
        inventory.append({"id": focus["focus_id"], "role": "FOCUS", "path": rel, "byte_start": focus["byte_start"], "byte_end": focus["byte_end"]})
        context = {"operation": FOCUS_OPERATION, "paper_version_id": P["pv"], "batch_id": focus["focus_id"],
                   "prefix_sha256": prefix_sha256, "aliases": {alias[cid]: P["occ"][cid] for cid in ordered}, "inventory": inventory,
                   "bibliography": [{"id": row["id"], "key": row["citation_key"]} for row in sorted(bib.values(), key=lambda r: r["id"])]}
        prompts.append({"focus_id": focus["focus_id"], "prompt": prefix + "FOCUS:\n" + canonical(block).decode("utf-8"),
                        "response_schema": RESPONSE_SCHEMA, "context": context})
    return {"paper_version_id": P["pv"], "prefix_sha256": prefix_sha256, "prefix_bytes": len(prefix.encode()), "prompts": prompts}


def focus_response_to_delta(extraction, sources, context, response, *, method_version, parents=(), produced_by=()):
    """S6 delta of a WHOLE_PAPER_FOCUS response: aliases become occurrence ids (an unknown alias stays as written and
    is rejected as an unknown occurrence), then the shared checks of response_to_delta apply."""
    if context.get("operation") != FOCUS_OPERATION:
        raise ValueError("a focus response needs a paper.extract_focus context")
    translated = copy.deepcopy(response)
    for claim in translated.get("claims", []) if isinstance(translated, dict) and isinstance(translated.get("claims"), list) else ():
        for field in ("source_occurrence_ids", "internal_support_occurrence_ids"):
            if isinstance(claim, dict) and isinstance(claim.get(field), list):
                claim[field] = [context["aliases"].get(x, x) if isinstance(x, str) else x for x in claim[field]]
    return response_to_delta(extraction, sources, context, translated, method_version=method_version, parents=parents,
                             produced_by=produced_by)


def response_to_delta(extraction, sources, context, response, *, method_version, parents=(), produced_by=()):
    """S6 delta of MODEL_EXTRACTION readings bound to occurrence claims, from a response to ``context`` (either mode;
    a focus response goes through focus_response_to_delta first)."""
    P = anchors.index(extraction, sources)
    pv, batch_id, focus = P["pv"], context["batch_id"], context.get("operation") == FOCUS_OPERATION
    problem = lambda code, detail, **evidence: ids.issue(code, batch_id, detail, evidence or None)
    delta = lambda nodes, edges, issues: ids.make_delta("S6", METHOD, method_version, ("CLAIM_BATCH", batch_id), nodes, edges, issues,
                                                       parents=parents, produced_by=produced_by)
    if message := ids.schema_error(RESPONSE_SCHEMA, response):
        return delta(None, (), [problem("MODEL_RESPONSE_SCHEMA_INVALID", message)])
    inventory = context["inventory"]
    envs = {row["id"]: row for row in inventory if row["role"] == "ENVIRONMENT"}
    scope = [row for row in inventory if row["role"] in ("ENVIRONMENT", "OWNED_PROOF", "FOCUS")]
    keys = defaultdict(list)
    for row in context["bibliography"]:
        keys[row["key"]].append(row["id"])
    paths = {anchors.rel(P, path): path for path in sources}
    full = [{"path": path, "text": sources[paths[path]].decode("utf-8")} for path in sorted({row["path"] for row in scope})]
    supplied = [{"id": row["id"]} for row in inventory if row["role"] in ("ENVIRONMENT", "REFERENCED")]
    claims = response["claims"]
    found = [problem(row.pop("code"), row.pop("detail"), **row) for row in _candidate_reference_issues(response, supplied, [{"key": k} for k in keys], full)]
    bindings = bind_source_locators(response, full)["bindings"]
    for i, claim in enumerate(claims):
        if set(claim["source_occurrence_ids"]) - envs.keys():
            found.append(problem("MODEL_CLAIM_OUTSIDE_BATCH", "A claim's occurrence is not a batch environment", claim_index=i))
        if any(len(keys.get(key, ())) > 1 for key in claim["external_citation_keys"] + claim["external_mention_citation_keys"]):
            found.append(problem("MODEL_CITATION_KEY_AMBIGUOUS", "A citation key names several bibliography entries", claim_index=i))
    found += [problem("MODEL_LOCATOR_OUTSIDE_BATCH", "A locator lies outside the batch environments and owned proofs", claim_index=b["claim_index"])
              for b in bindings if not any(_within(b["source"], row) for row in scope)]
    masked = {}
    for b in bindings:  # a quotation of commented-out text is not a statement of the paper
        data = sources[paths[b["source"]["path"]]]
        clean = masked.setdefault(b["source"]["path"], _mask_comments(data))
        if clean[b["source"]["byte_start"]:b["source"]["byte_end"]] != data[b["source"]["byte_start"]:b["source"]["byte_end"]]:
            found.append(problem("MODEL_LOCATOR_IN_COMMENT", "A locator quotes text inside a TeX comment", claim_index=b["claim_index"]))
    if found:
        return delta(None, (), found)
    # Bind each claim to S2 occurrences; a locator outside every environment is a new occurrence (§5.2). A quotation binds
    # to a named occurrence of the claim that contains it, else to the innermost batch occurrence containing it.
    locators = [sorted((b["source"] for b in bindings if b["claim_index"] == i), key=anchors.span_key) for i in range(len(claims))]
    size = lambda occ: envs[occ]["byte_end"] - envs[occ]["byte_start"]

    def enclosing(span, named):
        own = [occ for occ in named if occ in envs and _within(span, envs[occ])]
        inside = own or [occ for occ, row in envs.items() if _within(span, row)]
        return min(inside, key=lambda occ: (size(occ), occ), default=None)
    new, occs, marks = {}, [], []
    for i, claim in enumerate(claims):
        occ_ids, mark = set(claim["source_occurrence_ids"]), {}
        for span in locators[i]:
            occ = enclosing(span, claim["source_occurrence_ids"])
            if occ is None and not claim["source_occurrence_ids"]:
                occ = ids.occurrence_id(pv, span["path"], span["byte_start"], span["byte_end"], span["span_sha256"])
                new[occ] = span
            if occ is not None:
                mark.setdefault(occ, span)
                occ_ids.update([] if claim["source_occurrence_ids"] else [occ])
        occs.append(sorted(occ_ids))
        marks.append(mark)
    users, part = defaultdict(list), ["whole"] * len(claims)
    for i, occ_ids in enumerate(occs):
        for occ in occ_ids:
            users[occ].append(i)
    for occ, members in sorted(users.items()):
        starts = [marks[i].get(occ) for i in members]
        if len(members) < 2:
            continue
        if any(len(occs[i]) != 1 for i in members) or None in starts or len({s["byte_start"] for s in starts}) != len(members):
            found.append(problem("AMBIGUOUS_PART", "Several claims of one occurrence need distinguishing locators inside it",
                                 occurrence_id=occ, claim_indexes=members))
            continue
        for k, i in enumerate(sorted(members, key=lambda i: marks[i][occ]["byte_start"])):
            part[i] = f"part:{k}"
    if found:
        return delta(None, (), found)
    by_occ, bib = P["by_occ"], {row["id"]: row for row in anchors.bib_entries(P).values()}
    locate = lambda span: anchors.source_span(P, {**span, "path": paths[span["path"]]})
    whole = lambda occ: anchors.occurrence_claim(P, by_occ[occ])
    rows, extra, edges, placeholders, junctions, issues = [], {}, [], {}, [], []
    for i in range(len(claims)):
        occ_ids = occs[i]
        if part[i] != "whole":
            w = extra.setdefault(whole(occ_ids[0])["id"], whole(occ_ids[0]))
            rows.append(ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": pv, "occurrence_ids": occ_ids,
                                           "part": part[i], "locator": locate(marks[i][occ_ids[0]])}))
            edges.append(ids.edge("PART_OF", rows[-1]["id"], w["id"]))
        elif len(occ_ids) == 1 and occ_ids[0] in by_occ:
            rows.append(whole(occ_ids[0]))
        else:
            rows.append(ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": pv, "occurrence_ids": occ_ids, "part": "whole",
                                           **({"locator": locate(new[occ_ids[0]])} if len(occ_ids) == 1 else {})}))
    parts = defaultdict(list)
    for i, row in enumerate(rows):
        if part[i] != "whole":
            parts[occs[i][0]].append(row["id"])
    readings = []
    for i, claim in enumerate(claims):
        conclusion = rows[i]["id"]
        readings.append(ids.seal("ClaimReading", {
            "claim_id": conclusion, "method": METHOD, "method_version": method_version, "kind": claim["kind"],
            "statement_sha256": digest(claim["statement"].encode()), "conditions_sha256": digest(canonical(claim["conditions"])),
            "display_text": claim["statement"], "display_text_class": "VERBATIM",
            "confidence": {"value": claim["confidence"], "source": "SELF_REPORTED", "calibration_ref": None}}))
        proofs = [anchors.occurrence(P, proof) for occ in occs[i] if occ in by_occ for proof in P["owned"].get(by_occ[occ], [])]
        derivation = ids.proof_derivation(proofs) if proofs else ids.unlocated_derivation(METHOD, 0)
        premises = [(rows[j]["id"], []) for j in claim["internal_support_claim_indexes"]]
        for occ in claim["internal_support_occurrence_ids"]:
            if occ in parts:
                premises += [(pid, ["EXPANDED_TO_PARTS"]) for pid in parts[occ]]
            elif (focus or P["claims"][by_occ[occ]]["kind"] in anchors.ENVIRONMENTS
                  or any(o == [occ] and p == "whole" for o, p in zip(occs, part))):  # the whole paper was supplied (focus)
                w = extra.setdefault(whole(occ)["id"], whole(occ))
                premises.append((w["id"], []))
            else:  # the rows S3 builds for the same identity (anchors), so the deltas merge
                row = anchors.non_environment(P, conclusion, derivation, occ)
                premises.append((placeholders.setdefault(row["id"], row)["id"], []))
        for key in claim["external_citation_keys"]:
            row = anchors.request(P, conclusion, derivation, bib[keys[key][0]])
            premises.append((placeholders.setdefault(row["id"], row)["id"], []))
            edges.append(ids.edge("REQUESTS_FROM", row["id"], keys[key][0]))
        edges += [ids.edge("MENTIONS", conclusion, keys[key][0]) for key in claim["external_mention_citation_keys"]]
        legs, seen = [], {conclusion}
        for premise, flags in premises:
            if premise == conclusion:
                issues.append(problem("MODEL_SELF_SUPPORT_DROPPED", "A claim is not its own premise (G4)", claim_index=i))
            if premise not in seen:
                seen.add(premise)
                legs.append({"premise_id": premise, "role": "UNCLASSIFIED", "use_site": "UNKNOWN", "flags": flags})
        if legs:
            junctions.append(ids.seal("Junction", {"conclusion_id": conclusion, "derivation_id": derivation, "reading_method": METHOD,
                                                   "method_version": method_version, "legs": legs, "grouping_basis": "MODEL_EXTRACTION_READING"}))
        issues += [problem("MODEL_UNRESOLVED_DEPENDENCY", "Model-reported dependency outside the supplied context",
                           claim_id=conclusion, text=text) for text in claim["unresolved_dependencies"]]
    issues += [problem("MODEL_UNCERTAIN_SCOPE", "Model-reported unread or uncertain scope", text=text) for text in response["unread_or_uncertain_scope"]]
    claim_rows = {row["id"]: row for row in rows} | extra
    edges += [ids.edge("STATES", pv, cid) for cid in claim_rows] + [ids.edge("READS", row["id"], row["claim_id"]) for row in readings]
    return delta({"Claim": claim_rows.values(), "ClaimReading": readings, "Placeholder": placeholders.values(), "Junction": junctions},
                 edges, issues)
