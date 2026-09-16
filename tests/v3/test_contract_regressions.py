"""Independent regressions for audited V3 contract bypasses.

Every case first validates its complete synthetic control, including supplied
bytes and caller-held execution attestations. A resealed negative then changes
the audited condition, so stale hashes or unrelated malformed records cannot
make the test pass. These fixtures are not scientific or production approvals.
"""
from __future__ import annotations

import copy

import pytest

from test_contracts import FixtureGraph
from agtxiv_v3.contracts import (
    AuthorityContext, ExecutionAttestation, RecordSet, SchemaBundle, canonical,
    content_hash, exact_ref,
)


@pytest.fixture(scope="module")
def bundle():
    return SchemaBundle()


def report(graph, records=None):
    """Attest the fixture executions outside the tested RecordSet."""
    records = graph.records if records is None else records
    authority = AuthorityContext(
        executions={
            r["producer"]["execution_id"]: ExecutionAttestation(
                r["producer"]["principal_id"], r["producer"]["role"],
                tuple(r["producer"]["visible_input_refs"]),
                assurance=r["producer"]["identity_assurance"],
            ) for r in records
        },
        authorized_policy_hashes=frozenset(
            r["content_hash"] for r in records
            if r["record_type"] == "agtxiv.v3.authority-policy/0.0.0"
        ),
    )
    return RecordSet(graph.bundle, records, graph.artifacts, authority=authority).validate()


def require_control(graph, records=None):
    result = report(graph, records)
    assert result.valid, result.issues
    assert result.authority_checked and result.byte_artifacts_checked


def reseal(records, edit):
    """Edit exact content, then update all downstream references in order."""
    replacements, output = {}, []

    def replace(value):
        if isinstance(value, dict):
            if set(value) == {"record_type", "record_id", "revision", "content_hash"}:
                return copy.deepcopy(replacements.get(canonical(value), value))
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return value

    for old in records:
        new = replace(old)
        edit(new)
        new["content_hash"] = content_hash(new)
        replacements[canonical(exact_ref(old))] = exact_ref(new)
        output.append(new)
    return output


def require_rejected(graph, records, expected):
    result = report(graph, records)
    assert not result.valid
    assert result.authority_checked and result.byte_artifacts_checked
    # Exact equality rules out an unrelated schema/hash/identity failure masking
    # the targeted regression. Several independent gates may diagnose one edit.
    assert {issue.code for issue in result.issues} == set(expected), result.issues


def local_discharge(graph):
    context = graph.add("assumption-context", {
        "parent_ref": None,
        "assumptions": [{"condition_id": "condition:h", "statement": "H holds.",
                         "origin": "AGENT_ADDED", "source_span_refs": []}],
        "introduction_reason": "Assume H within a local derivation.",
        "allowed_use": "Within this context until a justified discharge.",
    })
    premise = graph.node("H holds.", context)
    conclusion = graph.node("If H holds, then H holds.")
    witness = graph.add("derived-claim", {
        "statement": "Assumption discharge derives H implies H.",
        "origin": "SYSTEM_DERIVATION", "parent_refs": [exact_ref(graph.claim)],
        "added_conditions": [], "relation": "INDEPENDENT",
        "rationale": "Synthetic rule witness for structural validation only.",
    })
    return graph.add("inference-step", {
        "premise_refs": [exact_ref(premise)], "conclusion_ref": exact_ref(conclusion),
        "rule": "ASSUMPTION_DISCHARGE", "justification": "Introduce the implication.",
        "context_ref": None, "discharged_context_refs": [exact_ref(context)],
        "rule_evidence_refs": [exact_ref(witness)],
    })


@pytest.mark.parametrize("field,value,expected", [
    ("rule", "DIRECT", {"INVALID_DISCHARGE_RULE", "SCOPE_ESCAPE"}),
    ("rule_evidence_refs", [], {"MISSING_DISCHARGE_EVIDENCE", "SCOPE_ESCAPE"}),
])
def test_local_scope_cannot_escape_by_listing_a_discharge(bundle, field, value, expected):
    graph = FixtureGraph(bundle)
    inference = local_discharge(graph)
    require_control(graph)

    def edit(record):
        if record["record_id"] == inference["record_id"]:
            record["payload"][field] = value

    require_rejected(graph, reseal(graph.records, edit), expected)


def reuse_control(graph):
    target = graph.claim_record("A separately identified use of the source result.")
    source_assessment = graph.assessment()
    other_assessment = graph.assessment(target=target)
    decision = graph.add("reuse-decision", {
        "source_ref": exact_ref(graph.claim), "target_ref": exact_ref(target),
        "profile_ref": exact_ref(graph.profile),
        "comparisons": [{"dimension": dimension, "source_value": "fixture value",
                         "target_value": "fixture value", "relation": "EQUIVALENT",
                         "witness_refs": []}
                        for dimension in ["OBJECT", "ASSUMPTION", "REGIME", "EVIDENCE"]],
        "assessment_refs": [exact_ref(source_assessment)],
        "review": graph.review(graph.claim, target), "outcome": "ALLOW",
        "conditions": [], "conflict_refs": [], "environment_check_ref": None,
    }, actor="actor:auditor", role="SCIENTIFIC_REVIEWER")
    return decision, source_assessment, other_assessment


@pytest.mark.parametrize("attack,expected", [
    ("unrelated_review", {"REVIEW_TARGET"}),
    ("raw_evidence", {"REUSE_EVIDENCE_TYPE", "REUSE_EVIDENCE_TARGET"}),
    ("wrong_target", {"REUSE_EVIDENCE_TARGET"}),
])
def test_reuse_needs_both_reviewed_endpoints_and_exact_typed_evidence(bundle, attack, expected):
    graph = FixtureGraph(bundle)
    decision, source_assessment, other_assessment = reuse_control(graph)
    require_control(graph)

    def edit(record):
        if record["record_id"] != decision["record_id"]:
            return
        if attack == "unrelated_review":
            # The actual source producer pretends to review only somebody else's
            # assessment. The endpoint-binding gate must expose this escape.
            record["producer"]["principal_id"] = "actor:producer"
            record["payload"]["review"] = graph.review(source_assessment)
        else:
            evidence = graph.span if attack == "raw_evidence" else other_assessment
            record["payload"]["assessment_refs"] = [exact_ref(evidence)]

    require_rejected(graph, reseal(graph.records, edit), expected)


@pytest.mark.parametrize("attack,expected", [
    ("promote", {"CONDITIONAL_PROMOTION"}),
    ("drop_condition", {"DROPPED_EVIDENCE_CONDITION"}),
])
def test_conditional_argument_cannot_become_unconditional_support(bundle, attack, expected):
    graph = FixtureGraph(bundle)
    _, _, route, snapshot = graph.argument(open_obligations=True)
    conditions = [{"condition_id": "condition:extra", "statement": "Hypothesis H holds.",
                   "origin": "AGENT_ADDED", "source_span_refs": []}]
    argument_review = graph.add("argument-review", {
        "snapshot_ref": exact_ref(snapshot), "proof_plan_refs": [exact_ref(route)],
        "review": graph.review(snapshot), "outcome": "CONDITIONAL",
        "open_obligation_ids": ["obligation:proof"], "open_challenge_refs": [],
        "conditions": conditions,
    }, actor="actor:reviewer", role="ARGUMENT_REVIEWER")
    assessment = graph.add("axis-assessment", {
        "target_refs": [exact_ref(graph.claim)], "axis": "mathematical_correctness",
        "applicability": "APPLICABLE", "result": "PARTIALLY_SUPPORTED",
        "execution": "COMPLETED", "method": "ARGUMENT_REVIEW",
        "review": graph.review(graph.claim), "support_refs": [exact_ref(argument_review)],
        "counterevidence_refs": [], "conditions": conditions, "frontier_refs": [],
        "rationale": "Conditional structural evidence, with the extra hypothesis retained.",
    }, actor="actor:auditor", role="SCIENTIFIC_REVIEWER")
    require_control(graph)

    def edit(record):
        if record["record_id"] == assessment["record_id"]:
            if attack == "promote":
                record["payload"]["result"] = "SUPPORTED"
            else:
                record["payload"]["conditions"] = []

    require_rejected(graph, reseal(graph.records, edit), expected)


def test_attested_identity_must_meet_exact_policy_minimum(bundle):
    graph = FixtureGraph(bundle)

    def require_external(record):
        if record["record_id"] == graph.policy["record_id"]:
            record["payload"]["minimum_identity_assurance"] = "EXTERNALLY_ATTESTED"
        record["producer"]["identity_assurance"] = "EXTERNALLY_ATTESTED"

    external = reseal(graph.records, require_external)
    require_control(graph, external)

    def downgrade(record):
        if record["record_id"] == graph.decision["record_id"]:
            record["producer"]["identity_assurance"] = "LOCALLY_ATTESTED"

    require_rejected(graph, reseal(external, downgrade), {"INSUFFICIENT_IDENTITY_ASSURANCE"})


def test_removing_failed_obligation_requires_review_of_old_scope_and_disposition(bundle):
    graph = FixtureGraph(bundle)
    failed = graph.add("obligation-disposition", {
        "scope_ref": exact_ref(graph.scope), "obligation_id": "obligation:proof",
        "outcome": "FAILED", "result_refs": [], "attempt_refs": [],
        "reason": "The original route did not establish its target.", "previous_ref": None,
    })
    obligations = [
        {**o, "obligation_id": "obligation:replacement", "reason": "An explicitly reviewed replacement route."}
        if o["obligation_id"] == "obligation:proof" else o for o in graph.obligations
    ]
    discovery = graph.add("inventory-discovery", {**graph.discovery["payload"], "obligations": obligations})
    decision = graph.add("scope-decision", {
        "discovery_ref": exact_ref(discovery),
        "review": graph.review(discovery, graph.scope, failed), "decision": "ACCEPT",
        "reason": "Review the earlier obligation and its failure before accepting its replacement.",
    }, actor="actor:reviewer", role="SCOPE_REVIEWER")
    graph.add("frozen-scope", {
        **graph.scope["payload"], "discovery_ref": exact_ref(discovery),
        "decision_ref": exact_ref(decision), "obligations": obligations,
        "predecessor_ref": exact_ref(graph.scope), "change_reason": "Reviewed alternative route.",
        "removed_obligation_dispositions": [exact_ref(failed)],
    })
    require_control(graph)

    def omit_old_inputs(record):
        if record["record_id"] == decision["record_id"]:
            record["payload"]["review"] = graph.review(discovery)

    require_rejected(graph, reseal(graph.records, omit_old_inputs), {"UNREVIEWED_SCOPE_REMOVAL"})


@pytest.mark.parametrize("attack,expected", [
    ("remove", {"MISSING_PROFILE_STAGE", "WEAKENED_PROFILE_STAGE"}),
    ("downgrade", {"WEAKENED_PROFILE_STAGE"}),
])
def test_scope_cannot_remove_or_weaken_named_profile_obligations(bundle, attack, expected):
    graph = FixtureGraph(bundle)
    require_control(graph)

    def edit(record):
        if record["record_id"] not in {graph.discovery["record_id"], graph.scope["record_id"]}:
            return
        obligations = record["payload"]["obligations"]
        if attack == "remove":
            record["payload"]["obligations"] = [o for o in obligations if o["stage"] != "SOURCE"]
        else:
            for obligation in obligations:
                if obligation["stage"] == "SOURCE":
                    obligation["requirement"] = "ACCOUNT_FOR"

    require_rejected(graph, reseal(graph.records, edit), expected)


def released_control(graph):
    """Build a small lawful *synthetic contract* release with mixed outcomes."""
    other_claim = graph.claim_record("A second separately identified source occurrence.")
    assessment = graph.assessment()
    other_assessment = graph.assessment(target=other_claim)
    baseline = graph.add("baseline-snapshot", {
        "knowledge_ref": None, "entry_refs": [], "domain": "Synthetic",
        "selection_method": "Fixed empty fixture baseline.", "search_coverage": "No external search.",
        "limitations": ["No scientific contribution is established by this fixture."],
    })
    delta = graph.add("contribution-delta", {
        "baseline_ref": exact_ref(baseline), "current_refs": [exact_ref(graph.claim)],
        "prior_refs": [], "operation": "INTRODUCES", "relation_refs": [],
        "author_declaration": "", "review": graph.review(graph.claim), "outcome": "PROPOSED",
        "qualifications": ["The contribution remains a candidate."],
    }, actor="actor:reviewer", role="SCIENTIFIC_REVIEWER")
    frontier = graph.add("frontier-item", {
        "target_refs": [exact_ref(graph.claim)], "kind": "UNPROVED_LEMMA",
        "axes": ["mathematical_correctness"], "statement": "The argument work is deferred.",
        "next_evidence": "A separately reviewed mathematical argument.",
        "attempt_refs": [], "state": "DEFERRED", "resolution_refs": [],
    })
    results = {"SOURCE": graph.source, "INVENTORY": graph.decision, "CLAIM": assessment}
    dispositions = []
    for obligation in graph.obligations:
        completed = obligation["requirement"] == "SUCCESS_REQUIRED"
        dispositions.append(graph.add("obligation-disposition", {
            "scope_ref": exact_ref(graph.scope), "obligation_id": obligation["obligation_id"],
            "outcome": "COMPLETED" if completed else "DEFERRED",
            "result_refs": [exact_ref(results[obligation["stage"]])] if completed else [],
            "attempt_refs": [], "reason": "Synthetic source-map work accounted for.", "previous_ref": None,
        }))
    manifest = graph.add("release-manifest", {
        "source_ref": exact_ref(graph.source), "scope_ref": exact_ref(graph.scope),
        "profile_ref": exact_ref(graph.profile), "record_refs": [exact_ref(r) for r in graph.records],
        "artifacts": [], "disposition_refs": [exact_ref(d) for d in dispositions],
        "frontier_refs": [exact_ref(frontier)], "contribution_refs": [exact_ref(delta)],
        "non_implications": ["This package is synthetic regression input, not a scientific release."],
    })
    review = graph.review(manifest)
    # The manifest includes independently produced scope/axis/contribution
    # records. An assembler's identity cannot hide those content producers.
    review["producer_principal_ids"] = ["actor:producer", "actor:reviewer"]
    audit = graph.add("release-audit", {
        "manifest_ref": exact_ref(manifest), "review": review,
        "ordered_target_refs": [exact_ref(graph.source), exact_ref(graph.claim)],
        "assessment_refs": [exact_ref(assessment), exact_ref(other_assessment)],
        "frontier_refs": [exact_ref(frontier)], "recommendation": "RECOMMEND_PROFILE_RELEASE",
        "findings": ["Source-map contract work is accounted for; mathematical work remains deferred."],
    }, actor="actor:auditor", role="PAPER_AUDITOR")
    certificate = graph.add("release-certificate", {
        "manifest_ref": exact_ref(manifest), "audit_ref": exact_ref(audit),
        "checks": ["EXACT_BINDING", "AUDIT_RECOMMENDATION", "ROLE_SEPARATION", "PROFILE_CONFORMANCE"],
        "outcome": "CERTIFIED", "failed_checks": [],
    }, actor="actor:certifier", role="CERTIFIER")
    release = graph.add("paper-release", {
        "manifest_ref": exact_ref(manifest), "audit_ref": exact_ref(audit),
        "certificate_ref": exact_ref(certificate), "release_name": "Synthetic source-map regression",
        "publication_uri": None,
    })
    genesis = graph.add("knowledge-snapshot", {
        "domain": "Synthetic", "predecessor_ref": None, "entry_refs": [],
        "relation_refs": [], "release_refs": [], "admission_refs": [],
    }, actor="actor:knowledge", role="KNOWLEDGE_SERVICE")
    return {"release": release, "genesis": genesis, "dispositions": dispositions,
            "assessment": assessment, "other_claim": other_claim, "other_assessment": other_assessment}


def admit(graph, release, before, candidate, assessment):
    return graph.add("admission-decision", {
        "release_ref": exact_ref(release), "before_ref": exact_ref(before),
        "review": graph.review(candidate), "items": [{
            "candidate_ref": exact_ref(candidate), "decision": "ACCEPT",
            "assessment_refs": [exact_ref(assessment)], "reason": "Exact synthetic source record only."}],
        "domain": "Synthetic",
    }, actor="actor:knowledge", role="ADMISSION_REVIEWER")


def admitted_snapshot(graph, release, before, decision, candidate):
    return graph.add("knowledge-snapshot", {
        "domain": "Synthetic", "predecessor_ref": exact_ref(before),
        "entry_refs": [exact_ref(candidate)], "relation_refs": [],
        "release_refs": [exact_ref(release)], "admission_refs": [exact_ref(decision)],
    }, actor="actor:knowledge", role="KNOWLEDGE_SERVICE")


def test_release_cannot_certify_deferred_required_success(bundle):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    require_control(graph)
    source_disposition = next(d for d in chain["dispositions"] if d["payload"]["obligation_id"] == "obligation:source")

    def defer(record):
        if record["record_id"] == source_disposition["record_id"]:
            record["payload"].update(outcome="DEFERRED", result_refs=[])

    require_rejected(graph, reseal(graph.records, defer), {"OBLIGATION_SUCCESS_REQUIRED"})


def test_complete_release_cannot_substitute_another_targets_result_for_required_work(bundle):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    require_control(graph)
    claim_disposition = next(d for d in chain['dispositions'] if d['payload']['obligation_id'] == 'obligation:claim')

    def substitute(record):
        if record['record_id'] == claim_disposition['record_id']:
            record['payload']['result_refs'] = [exact_ref(chain['other_assessment'])]

    require_rejected(graph, reseal(graph.records, substitute), {'OBLIGATION_STAGE_EVIDENCE'})


@pytest.mark.parametrize('fork,expected', [
    (False, {'OBLIGATION_STALE_DISPOSITION'}),
    (True, {'OBLIGATION_AMBIGUOUS_HEAD'}),
])
def test_complete_release_checks_disposition_heads_inside_its_explicit_manifest(bundle, fork, expected):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    require_control(graph)
    previous = next(d for d in chain['dispositions'] if d['payload']['obligation_id'] == 'obligation:source')
    newer = graph.add('obligation-disposition', {
        **previous['payload'], 'outcome': 'FAILED', 'result_refs': [],
        'reason': 'A later synthetic source-processing diagnostic.',
        'previous_ref': None if fork else exact_ref(previous),
    })
    # A new record outside the published historical manifest does not rewrite
    # its past. The same record inside a new manifest must affect currentness.
    require_control(graph)
    manifest_ref = chain['release']['payload']['manifest_ref']

    def include_newer(record):
        if record['record_id'] == manifest_ref['record_id']:
            record['payload']['record_refs'].append(exact_ref(newer))

    require_rejected(graph, reseal(graph.records, include_newer), expected)


@pytest.mark.parametrize("conflicting_actor", ["actor:auditor", "actor:certifier"])
def test_admission_reviewer_cannot_be_package_auditor_or_certifier(bundle, conflicting_actor):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    decision = admit(graph, chain["release"], chain["genesis"], graph.claim, chain["assessment"])
    require_control(graph)

    def merge_roles(record):
        if record["record_id"] == decision["record_id"]:
            record["producer"]["principal_id"] = conflicting_actor

    require_rejected(graph, reseal(graph.records, merge_roles), {"ADMISSION_ROLE_CONFLICT"})


@pytest.mark.parametrize("same_candidate,expected", [
    (False, {"BINDING_MISMATCH", "TRANSACTION_DECISION"}),
    (True, {"TRANSACTION_DECISION"}),
])
def test_committed_receipt_cannot_borrow_another_transactions_snapshot(bundle, same_candidate, expected):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    first = admit(graph, chain["release"], chain["genesis"], graph.claim, chain["assessment"])
    first_after = admitted_snapshot(graph, chain["release"], chain["genesis"], first, graph.claim)
    other = graph.claim if same_candidate else chain["other_claim"]
    other_assessment = chain["assessment"] if same_candidate else chain["other_assessment"]
    second = admit(graph, chain["release"], chain["genesis"], other, other_assessment)
    second_after = admitted_snapshot(graph, chain["release"], chain["genesis"], second, other)
    receipt = graph.add("ingestion-receipt", {
        "before_ref": exact_ref(chain["genesis"]), "after_ref": exact_ref(first_after),
        "decision_ref": exact_ref(first), "candidate_refs": [exact_ref(graph.claim)],
        "accepted_refs": [exact_ref(graph.claim)], "rejected_refs": [], "blocked_refs": [],
        "outcome": "COMMITTED",
    }, actor="actor:knowledge", role="KNOWLEDGE_SERVICE")
    require_control(graph)

    def wrong_result(record):
        if record["record_id"] == receipt["record_id"]:
            record["payload"]["after_ref"] = exact_ref(second_after)

    require_rejected(graph, reseal(graph.records, wrong_result), expected)


def test_public_records_cannot_mutate_recordsets_detached_content(bundle):
    graph = FixtureGraph(bundle)
    require_control(graph)
    store = RecordSet(bundle, graph.records, graph.artifacts)
    exposed = store.records
    exposed[0]["payload"]["charter_state"] = "ADOPTED"
    exposed[-1]["payload"]["obligations"].clear()
    assert store.resolve(exact_ref(graph.scope))["payload"]["obligations"] == graph.obligations
    assert store.validate().valid


def test_admission_cannot_substitute_another_candidates_assessment(bundle):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    decision = admit(graph, chain["release"], chain["genesis"], graph.claim, chain["assessment"])
    require_control(graph)

    def unrelated_evidence(record):
        if record["record_id"] == decision["record_id"]:
            # C2 and its completed assessment are valid members of the same
            # released package; only their relevance to admitted C1 is wrong.
            record["payload"]["items"][0]["assessment_refs"] = [exact_ref(chain["other_assessment"])]

    require_rejected(graph, reseal(graph.records, unrelated_evidence), {"ADMISSION_EVIDENCE_TARGET"})


def test_admission_review_must_include_its_exact_candidate(bundle):
    graph = FixtureGraph(bundle)
    chain = released_control(graph)
    decision = admit(graph, chain["release"], chain["genesis"], graph.claim, chain["assessment"])

    def make_other_candidate_visible(record):
        if record["record_id"] == decision["record_id"]:
            # Both versions give the reviewer access to C1 and C2. Thus a
            # missing-visibility error cannot mask the missing review of C1.
            other_ref = exact_ref(chain["other_claim"])
            record["producer"]["visible_input_refs"].append(other_ref)
            record["input_refs"].append(other_ref)

    control = reseal(graph.records, make_other_candidate_visible)
    require_control(graph, control)

    def omit_candidate(record):
        if record["record_id"] == decision["record_id"]:
            # Keep C1's valid assessment and the same independent principal;
            # change only which candidate the admission review examined.
            record["payload"]["review"] = graph.review(chain["other_claim"])

    require_rejected(graph, reseal(control, omit_candidate), {"REVIEW_TARGET"})
