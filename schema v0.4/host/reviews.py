"""v0.4 human reviews (HumanReviewV4) and the dispositions derived from them (spec §9.1-§9.2, G11, I-9).

The v0.3 review.py semantics, over v0.4 subjects: the host lists each subject with the digest of the
content shown; only a human fills a decision; a review of an unknown subject or of changed content is
rejected, never applied; ACCEPT minus REJECT is accepted. Only an accepted subject is
SOURCE_FROZEN_HUMAN_SIGNED; every other subject is UNREVIEWED. Nothing here reads a model output.
"""
from __future__ import annotations

import contracts
from core import canonical, digest
from delta import asserted
from ids import edge

SIGNED, UNREVIEWED = "SOURCE_FROZEN_HUMAN_SIGNED", "UNREVIEWED"
KINDS = tuple(contracts.SCHEMAS[contracts.CORPUS_ID]["$defs"]["HumanReviewV4"]["properties"]["subject_kind"]["anyOf"][1]["enum"])


def leg_id(junction_id, position):
    """The LEG subject id: the id of the leg's PREMISE_OF relationship, keyed by (junction, position) (§5.2, G15)."""
    return edge("PREMISE_OF", None, junction_id, {"position": position})["id"]


def subjects(view, nominations=()):
    """(subject_kind, subject_id) -> the reviewed content, as asserted (no asserted_by or methods)."""
    nodes = {i: asserted(row) for table in view["nodes"].values() for i, row in table.items()}
    rows = {}
    for j in view["nodes"]["Junction"].values():
        j = asserted(j)
        rows["JUNCTION", j["id"]] = j
        context = {k: j[k] for k in ("conclusion_id", "derivation_id", "reading_method", "method_version")}
        for position, leg in enumerate(j["legs"]):
            rows["LEG", leg_id(j["id"], position)] = {"junction_id": j["id"], "position": position, **context, **leg}
    for e in view["edges"].values():
        if e["type"] in ("SAME_WORK", "RESOLVES_TO"):
            rows["WORK_IDENTITY", e["id"]] = {"edge": asserted(e), "start": nodes.get(e["start_id"]),
                                              "end": nodes.get(e["end_id"])}
    for p in view["nodes"]["PrimitiveAssertion"].values():
        rows["PRIMITIVE_ASSERTION", p["id"]] = asserted(p)
    for n in nominations:
        contracts.validate("FoundationNomination", n)
        rows["FOUNDATION_NOMINATION", n["nomination_id"]] = n
    return rows


def template(view, nominations=()):
    return [{"kind": "HumanReview", "subject_kind": kind, "subject_id": subject_id,
             "subject_sha256": digest(canonical(content)), "content": content,
             "decision": None, "reviewer": None, "basis": None, "reviewed_at": None}
            for (kind, subject_id), content in sorted(subjects(view, nominations).items())]


def review_set_digest(reviews):
    """The ProjectionManifest review_set_digest: one digest of the filled review rows, in canonical order."""
    return digest(canonical(sorted((r for r in reviews if r.get("decision") is not None), key=canonical)))


def _load(known, reviews):
    digests = {key: digest(canonical(content)) for key, content in known.items()}
    valid, rejections = [], []
    for review in reviews:
        if isinstance(review, dict) and review.get("decision") is None:
            continue  # An unfilled template row is not a review.
        errors = [error.message for error in contracts.validator("HumanReviewV4").iter_errors(review)]
        if errors:
            reason = "SCHEMA_INVALID: " + "; ".join(errors)
        else:
            expected = digests.get((review["subject_kind"], review["subject_id"]))
            reason = ("UNKNOWN_SUBJECT" if expected is None else
                      "SUBJECT_CHANGED_SINCE_REVIEW" if expected != review["subject_sha256"] else None)
        if reason:
            rejections.append({"review": review, "reason": reason})
        else:
            valid.append(review)
    decided = lambda decision: {(r["subject_kind"], r["subject_id"]) for r in valid if r["decision"] == decision}
    return {"accepted": sorted(decided("ACCEPT") - decided("REJECT")), "rejections": rejections}


def load(view, reviews, nominations=()):
    """{accepted: sorted [(kind, id)] = ACCEPT minus REJECT, rejections: [{review, reason}]} for one review set."""
    return _load(subjects(view, nominations), reviews)


def derive_dispositions(view, reviews, nominations=()):
    """{subject_kind: {subject_id: disposition}} for every reviewable subject; only an ACCEPT signs (G11)."""
    known = subjects(view, nominations)
    accepted = set(_load(known, reviews)["accepted"])
    out = {kind: {} for kind in KINDS}
    for kind, subject_id in known:
        out[kind][subject_id] = SIGNED if (kind, subject_id) in accepted else UNREVIEWED
    return out
