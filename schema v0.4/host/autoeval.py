"""AUTO_EVAL_V1 (spec §11.2): automatic, blinded judging of proposed legs and matches, calibrated by controls.

No model is called here. The host freezes an EvaluationPlan, draws the samples from the view of the plan's
DeltaSetManifest, builds one blinded card per item (the card shows texts only: never the method, the reading or whether
it is a control), builds controls (positive: premises the conclusion's own proof references by label; negative: decoy
premises of the same kind that the conclusion cannot use), turns each judge response into a Judgement, combines the
panel (UNANIMOUS_VALID_USED), and computes an EvaluationReport. A USED verdict counts only with a quotation of at least
MIN_QUOTE_CHARS characters that the host binds inside the card's evidence text (I-7). A judgement is a measurement by a
declared instrument, never a disposition (I-0, I-15), and every estimate states its assumptions.

The gate uses a bound that needs no sensitivity: with panel-positive rate p among real items and false-positive rate f on
unused premises, p = Se·q + f·(1 - q) <= q + f·(1 - q), so the precision q >= (p - f) / (1 - f) for any Se <= 1. The report
takes the Wilson lower end of p and fpr_inflation times the largest per-rule Wilson upper end of f (decoys may be easier
than real unused premises), each one-sided at 1 - alpha/2, so the bound holds at 1 - alpha (Bonferroni; the largest
per-rule upper end covers the worst rule's rate whenever that rule's own bound holds). recheck() recomputes a stored row
from its counts, so the P0 gate never trusts a stored decision.
"""
from __future__ import annotations

import math
from collections import defaultdict
from statistics import NormalDist

import anchors
import contracts
import ids
from core import canonical, digest
from corpus import CONTRACT_VERSION, order_key
from delta import address
from invariants import admitted, work_components
from library import _tokens
from matching import bind_quote
from review_sample import review_sample, stratum_key
from reviews import leg_id

SCHEME, RULE, BLINDING = "AUTO_EVAL_V1", "UNANIMOUS_VALID_USED", "METHOD_AND_CONTROL_HIDDEN"
JUDGE_OPERATIONS = {"leg.judge": ("LEG_PRECISION", "LOCAL_VS_WHOLE_RECALL"), "match.judge": ("MATCH_PRECISION",)}
QUESTION = {"leg.judge": "LEG", "match.judge": "MATCH"}
PRECISION_OPERATION = {"LEG_PRECISION": "leg.judge", "MATCH_PRECISION": "match.judge"}
DECOY_RULES = ("SAME_PAPER_NEAR_MISS_V1", "OTHER_PAPER_DECOY_V1")
NON_MODEL_METHODS = ("HUMAN", "LIBRARY")  # entered or library-derived legs: admitted without a panel estimate, never sampled
MAX_INFLATED_FPR = 0.5  # beyond this the panel does not separate used from unused premises: NOT_ESTIMABLE
MIN_QUOTE_CHARS, MAX_QUOTE_EXTENSION = 12, 80  # a USED quotation's least length; the most a repeat may be extended by
WINDOW_BEFORE, WINDOW_AFTER = 2048, 512  # evidence window of an unlocated derivation, bytes
EQUATION = "DISPLAY_EQUATION"
RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"verdict": {"enum": ["USED", "NOT_USED", "CANNOT_TELL"]}, "quote": {"type": ["string", "null"]},
                   "reason": {"type": "string"}},
    "required": ["verdict", "quote", "reason"]}
INSTRUCTIONS = {
    "leg.judge": (
        "Operation leg.judge. CARD shows a conclusion, a candidate premise and EVIDENCE: the text of the conclusion's "
        "proof, statement or surrounding derivation. Decide whether EVIDENCE uses the premise to establish the "
        "conclusion. USED requires quote: an exact passage of EVIDENCE of at least 12 characters, copied byte for byte, "
        "where the premise is invoked by name, number, label or restatement. NOT_USED when EVIDENCE does not rely on the "
        "premise. CANNOT_TELL when EVIDENCE is insufficient. Judge only what EVIDENCE shows; whether the premise is true, "
        "well known or used elsewhere does not matter. Give a one-sentence reason."),
    "match.judge": (
        "Operation match.judge. CARD shows a citing claim, the passage where it invokes a cited work, the cited work's "
        "bibliography entry, and EVIDENCE: statements taken from the cited work. Decide whether EVIDENCE states the "
        "result the citing passage invokes, with the same hypotheses and conclusion up to notation. USED requires quote: "
        "an exact passage of EVIDENCE of at least 12 characters, copied byte for byte, that states it. NOT_USED when "
        "EVIDENCE states something else. CANNOT_TELL when the citing passage does not say enough. Give a one-sentence "
        "reason."),
}
ASSUMPTIONS = (
    "Leg decoys are unused by their conclusions. Each replaces the premise by one of the same kind (a bibliography entry "
    "for a cited work, a display equation for an equation, else a theorem-like or definition environment). "
    "SAME_PAPER_NEAR_MISS_V1 takes it from the same file after the evidence, never one that a label or citation inside "
    "the evidence or the conclusion references, that encloses such a target, that references the conclusion, or that "
    "is a premise of the conclusion; OTHER_PAPER_DECOY_V1 takes it from another supplied paper that neither cites nor "
    "is cited by the conclusion's paper.",
    "Match decoys do not state the invoked result. SAME_PAPER_NEAR_MISS_V1 takes the statement of the upstream paper "
    "that no source junction of the request uses with the largest token overlap with the citing claim (a hard "
    "negative); OTHER_PAPER_DECOY_V1 takes a statement of a supplied paper other than the citing and upstream papers "
    "and their citation neighbours. A decoy that does state it raises the measured false-positive rate, so that error "
    "is conservative.",
    "On real unused premises the panel's false-positive rate is at most fpr_inflation times its rate on the decoy rule "
    "with the largest upper bound.",
    "lower_bound holds for any panel sensitivity; point uses the sensitivity measured on premises the proof "
    "references by label (ANCHOR_IN_OWNED_PROOF_V1), which are easier than an average leg, so point is optimistic.",
    "Judges are not stratified by training cutoff: a judge that saw a paper in training may recognise its proofs "
    "(open, spec §15).",
    "No recall estimate uses a gold proof set; each states its own basis and assumption.",
)


def instruction_sha256(operation):
    return digest(INSTRUCTIONS[operation].encode())


def z_one_sided(alpha):
    """z of one of the two one-sided bounds (each at 1 - alpha/2) whose Bonferroni union holds at 1 - alpha."""
    return NormalDist().inv_cdf(1 - alpha / 2)


def rate(successes, n, z):
    """A Rate row: the Wilson score interval at z; n may be an effective, non-integer size."""
    if n <= 0:
        return {"successes": 0, "n": 0, "estimate": None, "lower": 0.0, "upper": 1.0, "z": z}
    p, z2 = successes / n, z * z
    centre, half = p + z2 / (2 * n), z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return {"successes": successes, "n": n, "estimate": p, "lower": max(0.0, (centre - half) / (1 + z2 / n)),
            "upper": min(1.0, (centre + half) / (1 + z2 / n)), "z": z}


def min_decoys(alpha, fpr_inflation):
    """The fewest decoys of one rule with which a stratum can be estimable: with none judged positive the Wilson upper
    end is z²/(n + z²), and fpr_inflation times it must stay below MAX_INFLATED_FPR, so n > z²(fpr_inflation / MAX - 1)
    (12 at alpha 0.05 and fpr_inflation 2)."""
    z = z_one_sided(alpha)
    return math.floor(z * z * (fpr_inflation / MAX_INFLATED_FPR - 1)) + 1


# ---- plan ------------------------------------------------------------------------------------------------------

def freeze_plan(corpus_manifest, delta_manifest, *, estimands, sample, controls, panel, producers, created_at):
    """The frozen EvaluationPlan. panel: [{judge_id, route}] with ModelSelectionV4 routes of leg.judge / match.judge;
    producers: {judge operation: the models whose outputs it judges}. Every operation the estimands need has >= 2
    judges that differ in model or effort, one of them not a producer. sample.per_stratum must reach the P0 min_items
    and controls.negative.count_per_rule must reach min_decoys, so the plan itself dooms no stratum to NOT_ESTIMABLE."""
    contracts.validate("CorpusManifest", corpus_manifest)
    contracts.validate("DeltaSetManifest", delta_manifest)
    if delta_manifest["corpus_id"] != corpus_manifest["corpus_id"]:
        raise ValueError("EVALUATION_MANIFEST_OF_ANOTHER_CORPUS")
    rule = corpus_manifest["gates"]["P0"]
    if sample["per_stratum"] < rule["min_items"]:
        raise ValueError(f"PER_STRATUM_BELOW_MIN_ITEMS: {sample['per_stratum']} < {rule['min_items']}")
    need = min_decoys(rule["alpha"], rule["fpr_inflation"])
    if controls["negative"]["count_per_rule"] < need:
        raise ValueError(f"TOO_FEW_DECOYS_PER_RULE: {controls['negative']['count_per_rule']} < {need}")
    ids_ = [j["judge_id"] for j in panel]
    if len(set(ids_)) != len(ids_):
        raise ValueError("JUDGE_IDS_REPEATED")
    judges = [{"judge_id": j["judge_id"], "route": j["route"], "instruction_sha256": instruction_sha256(j["route"]["operation"])}
              for j in panel if j["route"].get("operation") in JUDGE_OPERATIONS]
    if len(judges) != len(panel):
        raise ValueError("JUDGE_ROUTE_IS_NOT_A_JUDGE_OPERATION")
    if set(producers) - set(JUDGE_OPERATIONS):
        raise ValueError("PRODUCERS_OF_A_NON_JUDGE_OPERATION")
    for operation, served in JUDGE_OPERATIONS.items():
        if not set(served) & set(estimands):
            continue
        members = [j for j in judges if j["route"]["operation"] == operation]
        if len(members) < 2:
            raise ValueError("JUDGE_PANEL_TOO_SMALL: " + operation)
        if not producers.get(operation):
            raise ValueError("PRODUCERS_MISSING_FOR: " + operation)
        if all(j["route"]["model"] in producers[operation] for j in members):
            raise ValueError("JUDGE_PANEL_NOT_INDEPENDENT_OF_PRODUCERS: " + operation)
        if len({(j["route"]["model"], j["route"]["effort"]) for j in members}) < 2:
            raise ValueError("JUDGE_PANEL_MEMBERS_IDENTICAL: " + operation)
    body = {"kind": "EvaluationPlan", "contract_version": CONTRACT_VERSION, "corpus_id": corpus_manifest["corpus_id"],
            "manifest_id": delta_manifest["manifest_id"], "scheme": SCHEME, "estimands": sorted(estimands), "sample": sample,
            "controls": controls, "panel": judges, "decision_rule": RULE, "blinding": BLINDING,
            "producers": {op: sorted(set(models)) for op, models in sorted(producers.items())}}
    plan = {**body, "plan_id": address("eval-plan", body), "created_at": created_at}
    contracts.validate("EvaluationPlan", plan)
    return plan


def _check_view(plan, delta_manifest, view):
    """Samples are drawn from exactly the view the plan was frozen on (I-12)."""
    contracts.validate("EvaluationPlan", plan)
    contracts.validate("DeltaSetManifest", delta_manifest)
    if delta_manifest["manifest_id"] != plan["manifest_id"]:
        raise ValueError("SAMPLE_MANIFEST_IS_NOT_THE_PLAN_MANIFEST")
    if sorted(view["deltas"]) != sorted(delta_manifest["deltas"]):
        raise ValueError("VIEW_WAS_NOT_MERGED_FROM_THE_PLAN_MANIFEST")


def draw_leg_sample(plan, delta_manifest, view, created_at):
    """The LEG_PRECISION ReviewSample: every leg of a non-source junction whose reading method needs an estimate,
    stratified by (reading method, method_version, role, use site), per_stratum of each in seeded order; labelled by
    the plan's leg.judge panel."""
    _check_view(plan, delta_manifest, view)
    population = [{"subject_kind": "LEG", "subject_id": leg_id(j["id"], p),
                   "stratum": {"method": j["reading_method"], "method_version": j["method_version"],
                               "role": leg["role"], "use_site": leg["use_site"]}}
                  for j in view["nodes"]["Junction"].values()
                  if not j["derivation_id"].startswith("source:") and j["reading_method"] not in NON_MODEL_METHODS
                  for p, leg in enumerate(j["legs"])]
    return _plan_sample(plan, "LEG_PRECISION", "leg.judge", population, created_at)


def draw_match_sample(plan, delta_manifest, view, created_at):
    """The MATCH_PRECISION ReviewSample: every MODEL_MATCH source junction, stratified by method_version."""
    _check_view(plan, delta_manifest, view)
    population = [{"subject_kind": "JUNCTION", "subject_id": j["id"],
                   "stratum": {"method": "MODEL_MATCH", "method_version": j["method_version"]}}
                  for j in view["nodes"]["Junction"].values()
                  if j["derivation_id"].startswith("source:") and j["reading_method"] == "MODEL_MATCH"]
    return _plan_sample(plan, "MATCH_PRECISION", "match.judge", population, created_at)


def _plan_sample(plan, estimand, operation, population, created_at):
    if estimand not in plan["estimands"] or not population:
        raise ValueError("NOTHING_TO_SAMPLE_FOR: " + estimand)
    members = [j for j in plan["panel"] if j["route"]["operation"] == operation]
    guide = {"path": "autoeval/" + operation + ".instruction.txt", "sha256": instruction_sha256(operation),
             "byte_size": len(INSTRUCTIONS[operation].encode())}
    return review_sample(plan["manifest_id"], estimand, "RANDOM", plan["sample"]["seed"], guide, len(members), population,
                         plan["sample"]["per_stratum"], created_at, label_source="AUTO_PANEL", evaluation_plan_id=plan["plan_id"])


# ---- cards -----------------------------------------------------------------------------------------------------

class Papers:
    """Lazy per-paper indices over {paper_version_id: (v0.3 extraction record, {v0.3 path: frozen bytes})}."""

    def __init__(self, papers):
        self.raw, self.cache = papers, {}

    def __call__(self, pv):
        if pv not in self.cache:
            if pv not in self.raw:
                raise ValueError("CARD_NEEDS_THE_SOURCES_OF: " + pv)
            P = anchors.index(*self.raw[pv])
            P["paths"] = {anchors.rel(P, path): path for path in P["sources"]}
            P["bib"] = anchors.bib_entries(P)
            self.cache[pv] = P
        return self.cache[pv]


def _card(body):
    return {"card_id": ids.make_id("card", body), "card_sha256": digest(canonical(body)), **body}


def _text(data, start, end):
    """Bytes [start, end) moved inward to UTF-8 character boundaries, decoded."""
    while start < end and data[start] & 0xC0 == 0x80:
        start += 1
    while end > start and end < len(data) and data[end] & 0xC0 == 0x80:
        end -= 1
    return data[start:end].decode("utf-8", "replace")


def _occurrence_cid(P, claim):
    occ = claim["occurrence_ids"][0] if claim.get("occurrence_ids") else None
    return P["by_occ"].get(occ)


def _occurrences(view, premise_id):
    """The occurrence ids a premise stands for: a Claim's, or an UNRESOLVED_OCCURRENCE's; () for a request."""
    nodes = view["nodes"]
    if premise_id in nodes["Claim"]:
        return tuple(nodes["Claim"][premise_id].get("occurrence_ids", ()))
    h = nodes["Placeholder"].get(premise_id)
    return (h["occurrence_id"],) if h and h["kind"] == "UNRESOLVED_OCCURRENCE" else ()


def claim_text(papers, view, claim):
    """What a card shows for a claim: its occurrence's source text, its locator's bytes, or its entered locator."""
    if claim["origin"] == "WORK_LOCATOR":
        return claim["work_locator_text"]
    P, cid = papers(claim["paper_version_id"]), None
    if claim["part"] == "whole" and len(claim["occurrence_ids"]) == 1:
        cid = _occurrence_cid(P, claim)
    if cid is not None:
        return P["claims"][cid]["text"]
    if "locator" in claim:
        loc = claim["locator"]
        return _text(P["sources"][P["paths"][loc["artifact"]]], loc["start_byte"], loc["end_byte"])
    return "\n\n".join(P["claims"][P["by_occ"][o]]["text"] for o in claim["occurrence_ids"] if o in P["by_occ"])


def _entry_text(P, locator):
    return "Cited work: " + _text(P["sources"][P["paths"][locator["artifact"]]], locator["start_byte"], locator["end_byte"])


def premise_text(papers, view, premise_id):
    nodes = view["nodes"]
    if premise_id in nodes["Claim"]:
        return claim_text(papers, view, nodes["Claim"][premise_id])
    h, P = nodes["Placeholder"][premise_id], papers(nodes["Placeholder"][premise_id]["paper_version_id"])
    if h["kind"] == "UNRESOLVED_OCCURRENCE":
        return P["claims"][P["by_occ"][h["occurrence_id"]]]["text"]
    entry = _entry_text(P, nodes["BibEntry"][h["bib_entry_id"]]["locator"])
    return entry + (f" [{h['locator_text']}]" if h.get("locator_text") else "")


def _proof_sets(P, claim):
    """{proof derivation id: owned proof spans} of a claim: each owned proof alone (S3 anchors derive per proof) and all
    of them together (S6 extraction derives over every proof of the claim's occurrences)."""
    proofs = sorted({anchors.span_key(p): p for occ in claim.get("occurrence_ids", []) if occ in P["by_occ"]
                     for p in P["owned"].get(P["by_occ"][occ], [])}.values(), key=anchors.span_key)
    out = {ids.proof_derivation([anchors.occurrence(P, p)]): [p] for p in proofs}
    if proofs:
        out[ids.proof_derivation([anchors.occurrence(P, p) for p in proofs])] = proofs
    return out


def evidence(papers, view, conclusion_id, derivation_id):
    """(text, spans) of the region a leg is used in: exactly the owned proofs a proof: derivation names (one proof, or
    all of them), the statement of the statement derivation, else a window around the conclusion. spans: [(v0.3 path,
    start, end)] of that region. A proof: derivation that names no owned proof set raises EVIDENCE_DERIVATION_NOT_FOUND."""
    claim = view["nodes"]["Claim"][conclusion_id]
    if claim["origin"] == "WORK_LOCATOR":
        return claim["work_locator_text"], []
    P = papers(claim["paper_version_id"])
    if derivation_id.startswith("proof:"):
        proofs = _proof_sets(P, claim).get(derivation_id)
        if proofs is None:
            raise ValueError("EVIDENCE_DERIVATION_NOT_FOUND: " + derivation_id)
        return ("\n\n".join(_text(P["sources"][p["path"]], p["byte_start"], p["byte_end"]) for p in proofs),
                [(p["path"], p["byte_start"], p["byte_end"]) for p in proofs])
    cid = _occurrence_cid(P, claim)
    if cid is not None:
        span = P["claims"][cid]["source"]
        if derivation_id == "statement":
            return P["claims"][cid]["text"], [(span["path"], span["byte_start"], span["byte_end"])]
        path, start, end = span["path"], span["byte_start"], span["byte_end"]
    elif "locator" in claim:
        loc = claim["locator"]
        path, start, end = P["paths"][loc["artifact"]], loc["start_byte"], loc["end_byte"]
    else:
        return claim_text(papers, view, claim), []
    data = P["sources"][path]
    lo, hi = max(0, start - WINDOW_BEFORE), min(len(data), end + WINDOW_AFTER)
    return _text(data, lo, hi), [(path, lo, hi)]


def leg_card(papers, view, junction_id, position):
    """The blinded card of one leg of a non-source junction: question LEG, conclusion, premise and evidence texts only."""
    j = view["nodes"]["Junction"][junction_id]
    if j["derivation_id"].startswith("source:"):
        raise ValueError("A_SOURCE_JUNCTION_IS_JUDGED_BY_A_MATCH_CARD: " + junction_id)
    text, _ = evidence(papers, view, j["conclusion_id"], j["derivation_id"])
    return _card({"question": "LEG", "conclusion": claim_text(papers, view, view["nodes"]["Claim"][j["conclusion_id"]]),
                  "premise": premise_text(papers, view, j["legs"][position]["premise_id"]), "evidence": text})


def match_card(papers, view, junction_id, evidence_text=None):
    """The blinded card of one S7 source junction: the citing claim, its citing passage, the request's bibliography
    entry, and as evidence the upstream statements (the junction's premises, or evidence_text for a decoy)."""
    j = view["nodes"]["Junction"][junction_id]
    if not j["derivation_id"].startswith("source:"):
        raise ValueError("A_MATCH_CARD_NEEDS_A_SOURCE_JUNCTION: " + junction_id)
    request = view["nodes"]["Placeholder"][j["conclusion_id"]]
    citing = view["nodes"]["Claim"][request["created_by_claim_id"]]
    passage, _ = evidence(papers, view, citing["id"], request["citing_derivation_id"])
    if evidence_text is None:
        evidence_text = "\n\n".join(_upstream_text(papers, view, leg["premise_id"]) for leg in j["legs"])
    return _card({"question": "MATCH", "conclusion": claim_text(papers, view, citing), "citing_passage": passage,
                  "premise": premise_text(papers, view, request["id"]), "evidence": evidence_text})


def _upstream_text(papers, view, claim_id):
    """An upstream statement from its frozen source bytes (or its entered locator), never from a model reading."""
    claim = view["nodes"]["Claim"][claim_id]
    if claim["origin"] != "WORK_LOCATOR" and claim.get("paper_version_id") not in papers.raw:
        raise ValueError("UPSTREAM_SOURCES_NOT_SUPPLIED: " + str(claim.get("paper_version_id")))
    return claim_text(papers, view, claim)


# ---- controls --------------------------------------------------------------------------------------------------

def positive_controls(plan, view):
    """ANCHOR_IN_OWNED_PROOF_V1: DETERMINISTIC_ANCHOR legs used in a proof whose premise is a Claim (a \\ref to a
    theorem-like or definition environment inside the conclusion's owned proof), count of them in seeded order."""
    rule = plan["controls"]["positive"]
    legs = [(j["id"], p) for j in view["nodes"]["Junction"].values() if j["reading_method"] == "DETERMINISTIC_ANCHOR"
            for p, leg in enumerate(j["legs"]) if leg["use_site"] == "PROOF" and leg["premise_id"] in view["nodes"]["Claim"]]
    return sorted(legs, key=lambda k: order_key(plan["controls"]["seed"], leg_id(*k)))[:rule["count"]]


def _premises_of(view, conclusion_id):
    return {leg["premise_id"] for j in view["nodes"]["Junction"].values() if j["conclusion_id"] == conclusion_id for leg in j["legs"]}


def _kind_of(papers, view, premise_id):
    """The decoy kind a premise calls for: BIB (a cited work), EQUATION (a display equation), else ENVIRONMENT."""
    nodes = view["nodes"]
    row = nodes["Claim"].get(premise_id) or nodes["Placeholder"][premise_id]
    if row.get("kind") == "EXTERNAL_REQUEST":
        return "BIB"
    kind, occs = row.get("occurrence_kind"), _occurrences(view, premise_id)
    if kind is None and occs and row.get("paper_version_id") in papers.raw:
        P = papers(row["paper_version_id"])
        kind = P["claims"][P["by_occ"][occs[0]]]["kind"] if occs[0] in P["by_occ"] else None
    return "EQUATION" if kind == EQUATION else "ENVIRONMENT"


def _pool(P, kind):
    """(key, text, source span or None) decoy candidates of one paper, one per occurrence: bibliography entries (key:
    v0.3 bib id), display equations or environments (key: v0.3 claim id)."""
    if kind == "BIB":
        return [(row["v03_id"], _entry_text(P, row["locator"]), None) for row in sorted(P["bib"].values(), key=lambda r: r["v03_id"])]
    kinds = (EQUATION,) if kind == "EQUATION" else anchors.ENVIRONMENTS
    return [(cid, row["text"], row["source"]) for cid, row in sorted(P["claims"].items(), key=lambda kv: anchors.span_key(kv[1]["source"]))
            if row["kind"] in kinds and P["by_occ"].get(P["occ"][cid]) == cid]


def _region(span):
    return [(span["path"], span["byte_start"], span["byte_end"])]


def _inside(span, spans):
    return any(span["path"] == path and start <= span["byte_start"] and span["byte_end"] <= end for path, start, end in spans)


def _targets(P, spans):
    """v0.3 ids of every candidate target (label or citation, resolved or not) of an anchor inside the spans."""
    return {t for a in P["anchors"] if _inside(a["source"], spans) for t in a["candidate_target_ids"]}


def _enclosing(P, cids):
    """cids plus every environment whose span contains one of them."""
    out = set(cids)
    for cid in cids:
        if cid in P["claims"]:
            s = P["claims"][cid]["source"]
            out |= {e for e, row in P["claims"].items() if row["kind"] in anchors.ENVIRONMENTS and _inside(s, _region(row["source"]))}
    return out


def _neighbours(view):
    """{paper version: the paper versions of the view it cites or is cited by}, by explicit-id work identity."""
    comps = work_components(view, "EXPLICIT_IDS_ONLY")
    work = lambda w: min(comps.get(w, {w}))
    versions, out, bib = defaultdict(set), defaultdict(set), view["nodes"]["BibEntry"]
    for e in view["edges"].values():
        if e["type"] == "VERSION_OF":
            versions[work(e["end_id"])].add(e["start_id"])
    for e in view["edges"].values():
        if e["type"] == "RESOLVES_TO" and e["start_id"] in bib and admitted(e, "EXPLICIT_IDS_ONLY", ()):
            citing = bib[e["start_id"]]["paper_version_id"]
            for cited in versions[work(e["end_id"])] - {citing}:
                out[citing].add(cited)
                out[cited].add(citing)
    return out


def near_miss_decoy(plan, papers, view, junction_id, position, *, near=None):
    """SAME_PAPER_NEAR_MISS_V1: a candidate of the premise's kind (_kind_of) from the conclusion's paper that no source
    of the conclusion can use: an equation or environment of a file the evidence lies in, beginning after the
    evidence's end there, whose occurrence is no premise of the conclusion, that no anchor inside the evidence or the
    conclusion targets or encloses such a target, and that references no occurrence of the conclusion; a bibliography
    entry cited neither there nor by a request of the conclusion. The least order_key wins; None if there is none."""
    j = view["nodes"]["Junction"][junction_id]
    claim = view["nodes"]["Claim"][j["conclusion_id"]]
    if claim["origin"] != "PAPER_VERSION":
        return None
    P = papers(claim["paper_version_id"])
    _, spans = evidence(papers, view, claim["id"], j["derivation_id"])
    if not spans:
        return None
    kind = _kind_of(papers, view, j["legs"][position]["premise_id"])
    own = set(claim.get("occurrence_ids", ()))
    mine = {cid for cid, occ in P["occ"].items() if occ in own}
    premises = _premises_of(view, claim["id"])
    used = own | {o for pid in premises for o in _occurrences(view, pid)}
    taken = _enclosing(P, _targets(P, spans + [r for cid in mine for r in _region(P["claims"][cid]["source"])]))
    requested = {view["nodes"]["BibEntry"][h["bib_entry_id"]]["v03_id"] for pid in premises
                 if (h := view["nodes"]["Placeholder"].get(pid)) and h["kind"] == "EXTERNAL_REQUEST"}
    ends = defaultdict(int)
    for path, _, end in spans:
        ends[path] = max(ends[path], end)
    options = []
    for key, text, span in _pool(P, kind):
        if key in taken or key in requested:
            continue
        if span is not None and (span["path"] not in ends or span["byte_start"] < ends[span["path"]]
                                 or P["occ"][key] in used or _targets(P, _region(span)) & mine):
            continue
        options.append((order_key(plan["controls"]["seed"], claim["id"] + "|" + key), text))
    return min(options)[1] if options else None


def other_paper_decoy(plan, papers, view, junction_id, position, *, near=None):
    """OTHER_PAPER_DECOY_V1: a candidate of the premise's kind from another supplied paper that neither cites nor is
    cited by the conclusion's paper, preferring another primary category; seeded order. None if there is none."""
    j = view["nodes"]["Junction"][junction_id]
    claim, seed = view["nodes"]["Claim"][j["conclusion_id"]], plan["controls"]["seed"]
    own = claim.get("paper_version_id")
    kind = _kind_of(papers, view, j["legs"][position]["premise_id"])
    near = _neighbours(view) if near is None else near
    category = lambda pv: view["nodes"]["PaperVersion"].get(pv, {}).get("primary_category")
    others = [pv for pv in papers.raw if pv != own and pv not in near.get(own, ())]
    far = [pv for pv in others if category(pv) != category(own)]
    for pv in sorted(far or others, key=lambda pv: order_key(seed, claim["id"] + "|" + pv)):  # the first paper with one
        options = [(order_key(seed, claim["id"] + "|" + pv + "|" + key), text) for key, text, _ in _pool(papers(pv), kind)]
        if options:
            return min(options)[1]
    return None


def negative_controls(plan, papers, view, base_legs):
    """Leg decoy cards, count_per_rule of every rule: for each rule in turn, the base legs in seeded order, each card the
    base leg's card with its premise replaced by that rule's decoy. Returns (cards, {rule: card ids}, skipped): skipped
    counts the (rule, base leg) pairs without a decoy; a card equal to one already made (another leg of the same
    junction) is made once. Base legs of source junctions are refused (they are judged by match cards)."""
    per_rule, seed = plan["controls"]["negative"]["count_per_rule"], plan["controls"]["seed"]
    if any(view["nodes"]["Junction"][jid]["derivation_id"].startswith("source:") for jid, _ in base_legs):
        raise ValueError("BASE_LEG_OF_A_SOURCE_JUNCTION")
    make = {"SAME_PAPER_NEAR_MISS_V1": near_miss_decoy, "OTHER_PAPER_DECOY_V1": other_paper_decoy}
    near, order = _neighbours(view), sorted(set(base_legs), key=lambda k: order_key(seed, leg_id(*k)))
    cards, by_rule, skipped = {}, {}, 0
    for rule in plan["controls"]["negative"]["rules"]:
        by_rule[rule] = []
        for jid, position in order:
            if len(by_rule[rule]) == per_rule:
                break
            text = make[rule](plan, papers, view, jid, position, near=near)
            if text is None:
                skipped += 1
                continue
            base = leg_card(papers, view, jid, position)
            card = _card({**{k: base[k] for k in ("question", "conclusion", "evidence")}, "premise": text})
            if card["card_id"] not in cards:
                cards[card["card_id"]] = card
                by_rule[rule].append(card["card_id"])
    return list(cards.values()), by_rule, skipped


def match_decoys(plan, papers, view, base_junctions):
    """Match decoy cards, count_per_rule of every rule: the base source junction's card with its evidence replaced.
    SAME_PAPER_NEAR_MISS_V1: the environment of the upstream paper whose occurrence no source junction of the request
    uses, with the largest token overlap with the citing claim (a hard negative), then order_key. OTHER_PAPER_DECOY_V1:
    an environment of a supplied paper other than the citing and upstream papers and their citation neighbours.
    Returns (cards, {rule: card ids}, skipped) as negative_controls."""
    per_rule, seed, nodes = plan["controls"]["negative"]["count_per_rule"], plan["controls"]["seed"], view["nodes"]
    near, order = _neighbours(view), sorted(set(base_junctions), key=lambda k: order_key(seed, k))
    cards, by_rule, skipped = {}, {}, 0
    for rule in plan["controls"]["negative"]["rules"]:
        by_rule[rule] = []
        for jid in order:
            if len(by_rule[rule]) == per_rule:
                break
            j = nodes["Junction"][jid]
            if not j["derivation_id"].startswith("source:"):
                raise ValueError("MATCH_DECOY_BASE_IS_NOT_A_SOURCE_JUNCTION: " + jid)
            upstream = j["derivation_id"].removeprefix("source:").rsplit(":sha256:", 1)[0]
            request = nodes["Placeholder"][j["conclusion_id"]]
            citing = nodes["Claim"][request["created_by_claim_id"]]
            used = {o for k in nodes["Junction"].values() if k["conclusion_id"] == j["conclusion_id"]
                    for leg in k["legs"] for o in _occurrences(view, leg["premise_id"])}
            options = []
            if rule == "SAME_PAPER_NEAR_MISS_V1" and upstream in papers.raw:
                words, P = _tokens(claim_text(papers, view, citing)), papers(upstream)
                options = [(-len(words & _tokens(text)), order_key(seed, jid + "|" + key), text)
                           for key, text, _ in _pool(P, "ENVIRONMENT") if P["occ"][key] not in used]
            elif rule == "OTHER_PAPER_DECOY_V1":
                excluded = {upstream, request["paper_version_id"]} | near.get(upstream, set()) | near.get(request["paper_version_id"], set())
                for pv in sorted((pv for pv in papers.raw if pv not in excluded), key=lambda pv: order_key(seed, jid + "|" + pv)):
                    options = [(order_key(seed, jid + "|" + pv + "|" + key), text) for key, text, _ in _pool(papers(pv), "ENVIRONMENT")]
                    if options:
                        break
            if not options:
                skipped += 1
                continue
            card = match_card(papers, view, jid, min(options)[-1])
            if card["card_id"] not in cards:
                cards[card["card_id"]] = card
                by_rule[rule].append(card["card_id"])
    return list(cards.values()), by_rule, skipped


# ---- judgements and the panel ------------------------------------------------------------------------------------

def _judge(plan, judge_id):
    judge = next((j for j in plan["panel"] if j["judge_id"] == judge_id), None)
    if judge is None:
        raise ValueError("JUDGE_NOT_IN_PLAN: " + judge_id)
    return judge


def build_judge_prompt(card, operation):
    if card["question"] != QUESTION[operation]:
        raise ValueError("CARD_QUESTION_IS_NOT_THE_OPERATION: " + operation)
    shown = {k: v for k, v in card.items() if k not in ("card_id", "card_sha256")}
    return {"prompt": INSTRUCTIONS[operation] + "\nCARD:\n" + canonical(shown).decode("utf-8"),
            "response_schema": RESPONSE_SCHEMA, "context": card}


def judgement(plan, judge_id, card, response, receipt):
    """One Judgement from one judge response to one card, with the receipt of that call: RESPONSE_INVALID if the
    response breaks the schema; EVIDENCE_UNBOUND if USED comes without a quotation of at least MIN_QUOTE_CHARS
    characters found in the card's evidence, or with one that is repeated and would have to be extended by more than
    MAX_QUOTE_EXTENSION characters to its shortest unique enclosing span (matching.QUOTE_RULE); otherwise VALID."""
    judge = _judge(plan, judge_id)
    if card["question"] != QUESTION[judge["route"]["operation"]]:
        raise ValueError("CARD_QUESTION_IS_NOT_THE_JUDGE_OPERATION: " + judge_id)
    if card["card_sha256"] != digest(canonical({k: v for k, v in card.items() if k not in ("card_id", "card_sha256")})):
        raise ValueError("CARD_CONTENT_CHANGED")
    verdict, validity, found = "CANNOT_TELL", "RESPONSE_INVALID", None
    if ids.schema_error(RESPONSE_SCHEMA, response) is None:
        verdict, validity = response["verdict"], "VALID"
        if verdict == "USED":
            text, quote = card["evidence"], response["quote"]
            bound = bind_quote(text, quote) if quote and len(quote.strip()) >= MIN_QUOTE_CHARS else None
            if bound and (bound[1] - bound[0]) - len(quote) > MAX_QUOTE_EXTENSION:
                bound = None
            if bound:
                start, end = len(text[:bound[0]].encode()), len(text[:bound[1]].encode())
                found = {"byte_start": start, "byte_end": end, "span_sha256": digest(text.encode()[start:end]), "extended": bound[2]}
            else:
                validity = "EVIDENCE_UNBOUND"
    body = {"kind": "Judgement", "contract_version": CONTRACT_VERSION, "plan_id": plan["plan_id"], "judge_id": judge_id,
            "card_id": card["card_id"], "card_sha256": card["card_sha256"], "verdict": verdict, "validity": validity,
            "evidence": found, "receipt": receipt}
    row = {**body, "judgement_id": address("judgement", body)}
    contracts.validate("Judgement", row)
    return row


def panel_labels(plan, operation, judgements):
    """({card_id: panel-positive}, unresolved card ids) for the plan's judges of one operation. A card is positive iff
    every judge gave a VALID USED, and unresolved iff it is neither that nor a unanimous VALID NOT_USED. Every card must
    carry exactly one judgement of every judge of the operation."""
    judges = {j["judge_id"] for j in plan["panel"] if j["route"]["operation"] == operation}
    by_card = defaultdict(dict)
    for row in judgements:
        contracts.validate("Judgement", row)
        if row["plan_id"] != plan["plan_id"]:
            raise ValueError("JUDGEMENT_OF_ANOTHER_PLAN: " + row["judgement_id"])
        if row["judge_id"] not in judges:  # a judge of the other operation
            continue
        if row["judge_id"] in by_card[row["card_id"]]:
            raise ValueError("JUDGE_ANSWERED_A_CARD_TWICE: " + row["card_id"])
        by_card[row["card_id"]][row["judge_id"]] = row
    labels, unresolved = {}, set()
    for card, rows in sorted(by_card.items()):
        if set(rows) != judges:
            raise ValueError("PANEL_INCOMPLETE_FOR: " + card)
        labels[card] = all(r["validity"] == "VALID" and r["verdict"] == "USED" for r in rows.values())
        if not labels[card] and not all(r["validity"] == "VALID" and r["verdict"] == "NOT_USED" for r in rows.values()):
            unresolved.add(card)
    return labels, unresolved


# ---- estimates -------------------------------------------------------------------------------------------------

def _worst(by_rule):
    """The per-rule Rate with the largest upper end (ties: the first rule of DECOY_RULES)."""
    return max(sorted(by_rule.items(), key=lambda kv: DECOY_RULES.index(kv[0])), key=lambda kv: kv[1]["upper"])[1]


def _decide(items, open_items, p, f, negatives, gate_rule):
    """(decision, lower_bound, reason) of one stratum under a P0 rule."""
    inflated = gate_rule["fpr_inflation"] * f["upper"]
    if items < gate_rule["min_items"]:
        reason = f"{items} items < min_items {gate_rule['min_items']}"
    elif not negatives:
        reason = "no negative control was judged"
    elif inflated >= MAX_INFLATED_FPR:
        reason = f"inflated false-positive bound {inflated:.3f} >= {MAX_INFLATED_FPR}: the panel does not separate used from unused"
    elif open_items / items > gate_rule["max_unresolved_fraction"]:
        reason = f"unresolved fraction {open_items / items:.3f} > {gate_rule['max_unresolved_fraction']}"
    else:
        bound = max(0.0, (p["lower"] - inflated) / (1 - inflated))
        return ("ADMIT" if bound >= gate_rule["admission_threshold"] else "REJECT", bound,
                f"lower bound {bound:.3f} vs threshold {gate_rule['admission_threshold']}")
    return "NOT_ESTIMABLE", None, reason


def precision_estimates(plan, gate_rule, sample, cards_of, positive, negative_by_rule, labels, unresolved):
    """PrecisionEstimate rows, one per full stratum of a ReviewSample. cards_of: {item subject_id: card_id}; positive:
    positive-control card ids and negative_by_rule: {decoy rule: card ids} of this estimand; labels and unresolved
    from panel_labels. Every plan decoy rule gets its own false-positive Rate (n = 0 when it made no decoy, whose upper
    end 1 makes every stratum NOT_ESTIMABLE); the bound uses the worst."""
    contracts.validate("ReviewSample", sample)
    if sample["label_source"] != "AUTO_PANEL" or sample["evaluation_plan_id"] != plan["plan_id"]:
        raise ValueError("SAMPLE_IS_NOT_LABELLED_BY_THIS_PLAN")
    if sample["estimand"] not in PRECISION_OPERATION:
        raise ValueError("NOT_A_PRECISION_SAMPLE: " + sample["estimand"])
    rules = plan["controls"]["negative"]["rules"]
    if set(negative_by_rule) - set(rules):
        raise ValueError("DECOY_RULE_NOT_IN_THE_PLAN")
    negatives = [c for r in rules for c in negative_by_rule.get(r, [])]
    missing = [c for c in [*cards_of.values(), *positive, *negatives] if c not in labels]
    if missing:
        raise ValueError("PANEL_LABEL_MISSING: " + missing[0])
    z = z_one_sided(gate_rule["alpha"])
    by_rule = {r: rate(sum(labels[c] for c in negative_by_rule.get(r, [])), len(negative_by_rule.get(r, [])), z) for r in rules}
    f = _worst(by_rule)
    se = rate(sum(labels[c] for c in positive), len(positive), z) if positive else None
    strata = defaultdict(list)
    for item in sample["items"]:
        if "stratum" not in item:
            raise ValueError("PRECISION_ITEM_WITHOUT_STRATUM: " + item["subject_id"])
        strata[stratum_key(item["stratum"])].append(item)
    out = []
    for key, items in sorted(strata.items()):
        w = [(1 / i["inclusion_probability"], labels[cards_of[i["subject_id"]]]) for i in items]
        total, n_eff = sum(x for x, _ in w), sum(x for x, _ in w) ** 2 / sum(x * x for x, _ in w)
        p = rate(sum(x for x, y in w if y) / total * n_eff, n_eff, z)
        open_items = sum(cards_of[i["subject_id"]] in unresolved for i in items)
        decision, bound, reason = _decide(len(items), open_items, p, f, len(negatives), gate_rule)
        point = None
        if se and se["estimate"] is not None and f["estimate"] is not None and se["estimate"] - f["estimate"] > 0:
            point = min(1.0, max(0.0, (p["estimate"] - f["estimate"]) / (se["estimate"] - f["estimate"])))
        out.append({"estimand": sample["estimand"], "sample_id": sample["sample_id"], "stratum": dict(key),
                    "items": len(items), "unresolved": open_items, "panel_positive": p, "false_positive": f,
                    "false_positive_by_rule": by_rule, "sensitivity": se, "fpr_inflation": gate_rule["fpr_inflation"],
                    "lower_bound": bound, "point": point,
                    "gate": {"threshold": gate_rule["admission_threshold"], "decision": decision, "reason": reason}})
    for row in out:
        contracts.validate("PrecisionEstimate", row)
    return out


def _same(a, b):
    return a == b or (a is not None and b is not None and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12))


def _same_rate(r, s):
    return all(_same(r[k], s[k]) for k in ("successes", "n", "estimate", "lower", "upper", "z"))


def recheck(row, gate_rule):
    """The decision of a stored PrecisionEstimate row, recomputed under a P0 rule from its counts: every Rate from its
    (successes, n) at the rule's z, false_positive as the worst rule, the bound and the decision. Raises
    PRECISION_ROW_DOES_NOT_RECOMPUTE when anything stored differs; a gate uses the returned decision."""
    contracts.validate("PrecisionEstimate", row)
    z = z_one_sided(gate_rule["alpha"])
    rates = [row["panel_positive"], row["false_positive"], *row["false_positive_by_rule"].values(),
             *([row["sensitivity"]] if row["sensitivity"] else [])]
    problems = []
    if not all(_same_rate(r, rate(r["successes"], r["n"], z)) for r in rates):
        problems.append("a rate does not recompute at the rule's z")
    if not _same_rate(row["false_positive"], _worst(row["false_positive_by_rule"])):
        problems.append("false_positive is not the worst decoy rule")
    if row["fpr_inflation"] != gate_rule["fpr_inflation"] or row["gate"]["threshold"] != gate_rule["admission_threshold"]:
        problems.append("the row was computed under another rule")
    negatives = sum(r["n"] for r in row["false_positive_by_rule"].values())
    decision, bound, _ = _decide(row["items"], row["unresolved"], row["panel_positive"], row["false_positive"], negatives, gate_rule)
    if decision != row["gate"]["decision"] or not _same(bound, row["lower_bound"]):
        problems.append("the bound or the decision does not recompute")
    if problems:
        raise ValueError("PRECISION_ROW_DOES_NOT_RECOMPUTE: " + "; ".join(problems))
    return decision


def _whole_of(view):
    """{UNRESOLVED_OCCURRENCE id: the whole Claim of the same occurrence} where the view has one (other than the
    placeholder's creator): as in analysis, the placeholder and that claim are one premise."""
    claims, holders = view["nodes"]["Claim"], view["nodes"]["Placeholder"]
    whole = {r["occurrence_ids"][0]: c for c, r in claims.items()
             if r["origin"] == "PAPER_VERSION" and r["part"] == "whole" and len(r["occurrence_ids"]) == 1}
    return {h: whole[r["occurrence_id"]] for h, r in holders.items() if r["kind"] == "UNRESOLVED_OCCURRENCE"
            and whole.get(r["occurrence_id"]) not in (None, r["created_by_claim_id"])}


def _leg_keys(view, method, method_version=None, conclusions=None):
    """{(conclusion, premise)} of the method's non-source junctions (optionally one method_version, some conclusions),
    an UNRESOLVED_OCCURRENCE premise named by the whole claim of its occurrence where the view has one."""
    resolved = _whole_of(view)
    return {(j["conclusion_id"], resolved.get(leg["premise_id"], leg["premise_id"])) for j in view["nodes"]["Junction"].values()
            if j["reading_method"] == method and (method_version is None or j["method_version"] == method_version)
            and not j["derivation_id"].startswith("source:") and (conclusions is None or j["conclusion_id"] in conclusions)
            for leg in j["legs"]}


def _examined(view, method_version):
    """Conclusions a MODEL_EXTRACTION method_version examined: those it read or proposed a non-source junction for."""
    out = {j["conclusion_id"] for j in view["nodes"]["Junction"].values() if j["reading_method"] == "MODEL_EXTRACTION"
           and j["method_version"] == method_version and not j["derivation_id"].startswith("source:")}
    return out | {r["claim_id"] for r in view["nodes"]["ClaimReading"].values()
                  if r["method"] == "MODEL_EXTRACTION" and r["method_version"] == method_version}


def anchor_recall(view, method_version, z=NormalDist().inv_cdf(0.975)):
    """ANCHOR_REFERENCED_V1 (deterministic, no judge): of the DETERMINISTIC_ANCHOR proof legs to a Claim premise whose
    conclusion the MODEL_EXTRACTION method_version examined, the fraction that method_version also proposed."""
    examined = _examined(view, method_version)
    anchored = {(j["conclusion_id"], leg["premise_id"]) for j in view["nodes"]["Junction"].values()
                if j["reading_method"] == "DETERMINISTIC_ANCHOR" and j["conclusion_id"] in examined
                for leg in j["legs"] if leg["use_site"] == "PROOF" and leg["premise_id"] in view["nodes"]["Claim"]}
    found = anchored & _leg_keys(view, "MODEL_EXTRACTION", method_version)
    row = {"estimand": "LEG_RECALL", "basis": "ANCHOR_REFERENCED_V1", "method": "MODEL_EXTRACTION/" + method_version,
           "versus": "DETERMINISTIC_ANCHOR", "rate": rate(len(found), len(anchored), z),
           "estimate": len(found) / len(anchored) if anchored else None,
           "counts": {"anchored": len(anchored), "found": len(found)},
           "assumption": "Only premises the proof references by label; implicit premises are not covered, so this is not the recall on all legs."}
    contracts.validate("RecallEstimate", row)
    return row


def union_legs(view, version_a, version_b):
    """{(conclusion, premise): (junction id, position)} of the legs either MODEL_EXTRACTION version proposed on the
    conclusions both examined (keys as _leg_keys); the least (junction id, position) represents each for its card."""
    both, resolved = _examined(view, version_a) & _examined(view, version_b), _whole_of(view)
    out = {}
    for j in sorted(view["nodes"]["Junction"].values(), key=lambda j: j["id"]):
        if (j["reading_method"] == "MODEL_EXTRACTION" and j["method_version"] in (version_a, version_b)
                and not j["derivation_id"].startswith("source:") and j["conclusion_id"] in both):
            for p, leg in enumerate(j["legs"]):
                out.setdefault((j["conclusion_id"], resolved.get(leg["premise_id"], leg["premise_id"])), (j["id"], p))
    return out


def union_recall(view, version_a, version_b, labels_by_key, z=NormalDist().inv_cdf(0.975)):
    """LOCAL_VS_WHOLE_RECALL on the conclusions both MODEL_EXTRACTION versions examined (read or proposed a junction
    for): within the panel-confirmed union of their legs (labels_by_key: {(conclusion, premise): panel-positive} for
    every key of union_legs), each version's share (UNION_OF_TWO_METHODS_V1), and the Chapman capture-recapture
    estimate (CAPTURE_RECAPTURE_CHAPMAN_V1)."""
    both_examined = _examined(view, version_a) & _examined(view, version_b)
    a, b = _leg_keys(view, "MODEL_EXTRACTION", version_a, both_examined), _leg_keys(view, "MODEL_EXTRACTION", version_b, both_examined)
    if missing := sorted((a | b) - labels_by_key.keys()):
        raise ValueError(f"UNION_LEG_NOT_JUDGED: {missing[0]}")
    confirmed = {k for k in a | b if labels_by_key[k]}
    ya, yb = confirmed & a, confirmed & b
    m, n1, n2 = len(ya & yb), len(ya), len(yb)
    total = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    counts = {"conclusions": len(both_examined), "confirmed_union": len(confirmed), "confirmed_a": n1, "confirmed_b": n2, "confirmed_both": m}
    rows = [{"estimand": "LOCAL_VS_WHOLE_RECALL", "basis": "UNION_OF_TWO_METHODS_V1", "method": "MODEL_EXTRACTION/" + x,
             "versus": "MODEL_EXTRACTION/" + y, "rate": rate(k, len(confirmed), z),
             "estimate": k / len(confirmed) if confirmed else None, "counts": counts,
             "assumption": "Share of the panel-confirmed legs of either version; legs both versions missed are not counted."}
            for x, y, k in ((version_a, version_b, n1), (version_b, version_a, n2))]
    rows += [{"estimand": "LOCAL_VS_WHOLE_RECALL", "basis": "CAPTURE_RECAPTURE_CHAPMAN_V1", "method": "MODEL_EXTRACTION/" + x,
              "versus": "MODEL_EXTRACTION/" + y, "rate": None, "estimate": min(1.0, k / total) if total > 0 else None,
              "counts": counts,
              "assumption": "The two versions miss legs independently; correlated misses make this optimistic."}
             for x, y, k in ((version_a, version_b, n1), (version_b, version_a, n2))]
    for row in rows:
        contracts.validate("RecallEstimate", row)
    return rows


def human_audit(sample, auto_labels, human_labels, z=NormalDist().inv_cdf(0.975)):
    """Agreement of the panel with human labels on the items both labelled ({subject_id: bool} each)."""
    both = sorted(auto_labels.keys() & human_labels.keys())
    return {"sample_id": sample["sample_id"], "agreement": rate(sum(auto_labels[k] == human_labels[k] for k in both), len(both), z)}


def report_inputs(samples, cards, judgements, controls):
    """EvaluationReport.inputs: the precision samples' ids, digests of every card and judgement the estimates used, and
    per precision estimand the control composition {positive, negative_by_rule: {rule: decoys}, skipped}."""
    return {"samples": sorted({s["sample_id"] for s in samples}),
            "cards_sha256": digest(canonical(sorted({c["card_sha256"] for c in cards}))),
            "judgements_sha256": digest(canonical(sorted({j["judgement_id"] for j in judgements}))),
            "controls": controls}


def report(plan, precision, recall, inputs, created_at, audit=None):
    """The EvaluationReport of one plan; inputs from report_inputs."""
    contracts.validate("EvaluationPlan", plan)
    if not {row["sample_id"] for row in precision} <= set(inputs["samples"]):
        raise ValueError("PRECISION_ROW_OF_A_SAMPLE_NOT_IN_THE_INPUTS")
    judge_models = defaultdict(set)
    for j in plan["panel"]:
        judge_models[j["route"]["operation"]].add(j["route"]["model"])
    judge_models = {op: sorted(models) for op, models in sorted(judge_models.items())}
    body = {"kind": "EvaluationReport", "contract_version": CONTRACT_VERSION, "plan_id": plan["plan_id"],
            "manifest_id": plan["manifest_id"], "label_source": "AUTO_PANEL",
            "independence": {"judge_models": judge_models, "producers": plan["producers"],
                             "distinct_model_present": all(set(models) - set(plan["producers"].get(op, ()))
                                                           for op, models in judge_models.items())},
            "inputs": inputs, "precision": precision, "recall": recall,
            "assumptions": [*ASSUMPTIONS, *([] if audit else ["No human audit of the panel was made."])],
            "human_audit": audit}
    row = {**body, "report_id": address("eval-report", body), "created_at": created_at}
    contracts.validate("EvaluationReport", row)
    return row
