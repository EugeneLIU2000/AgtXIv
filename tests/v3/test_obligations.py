"""Offline obligation-contract probes; all evidence is explicitly SYNTHETIC.

No Lean process, demonstration, paper experiment, or scientific review runs.
Each attack starts from a fully valid byte/authority-checked fixture control.
"""
from __future__ import annotations

import copy

import pytest

from test_contracts import FixtureGraph
from test_contract_regressions import require_control, reseal
from agtxiv_v3.contracts import RecordSet, SchemaBundle, exact_ref
from agtxiv_v3.obligations import check_obligations


@pytest.fixture(scope='module')
def bundle():
    return SchemaBundle()


def current(records, original):
    return next(r for r in records if r['record_id'] == original['record_id'])


def evaluate(graph, dispositions, *, records=None, universe=None, **options):
    records = graph.records if records is None else records
    store = RecordSet(graph.bundle, records, graph.artifacts)
    return check_obligations(store, exact_ref(current(records, graph.scope)),
                             [exact_ref(current(records, r)) for r in dispositions],
                             universe_refs=[exact_ref(r) for r in records] if universe is None else universe,
                             **options)


def codes(result):
    return {i.code for i in result.issues}


def source_map(graph, argument_result=None):
    source_assessment = graph.assessment()
    results = {'SOURCE': [graph.source], 'INVENTORY': [graph.decision], 'CLAIM': [source_assessment],
               'ARGUMENT': argument_result or [], 'FORMAL': argument_result or []}
    dispositions = []
    for obligation in graph.scope['payload']['obligations']:
        evidence = results[obligation['stage']]
        dispositions.append(graph.add('obligation-disposition', {
            'scope_ref': exact_ref(graph.scope), 'obligation_id': obligation['obligation_id'],
            'outcome': 'COMPLETED' if evidence else 'DEFERRED',
            'result_refs': [exact_ref(r) for r in evidence], 'attempt_refs': [],
            'reason': 'Synthetic accounting fixture only.', 'previous_ref': None,
        }))
    return dispositions, source_assessment


def by_stage(graph, dispositions, stage):
    oid = next(o['obligation_id'] for o in graph.scope['payload']['obligations'] if o['stage'] == stage)
    return next(d for d in dispositions if d['payload']['obligation_id'] == oid)


def test_source_map_requires_only_recorded_processing_and_explicit_claim_assessment(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    result = evaluate(graph, dispositions)
    assert result.valid, result.issues
    assert result.artifact_checked and result.checked_artifact_count == 1
    assert not result.authority_checked
    assert any('not scientific claim fidelity' in text for text in result.limitations)
    assert not evaluate(graph, dispositions, require_artifacts=False).artifact_checked


@pytest.mark.parametrize('stage', ['SOURCE', 'INVENTORY', 'CLAIM'])
def test_arbitrary_or_other_target_result_cannot_satisfy_required_success(bundle, stage):
    graph = FixtureGraph(bundle)
    other = graph.claim_record('A separately identified source assertion.')
    unrelated = graph.assessment(target=other)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    victim = by_stage(graph, dispositions, stage)

    def edit(record):
        if record['record_id'] == victim['record_id']:
            record['payload']['result_refs'] = [exact_ref(unrelated if stage == 'CLAIM' else graph.span)]

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_STAGE_EVIDENCE'}


def test_completed_source_snapshot_must_not_hide_missing_material(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_id'] == graph.source['record_id']:
            record['payload']['missing_material'] = ['An invoked source supplement is unavailable.']

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_STAGE_EVIDENCE'}


def test_candidate_manifest_accounts_for_deferred_required_work_but_positive_audit_blocks(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    victim = by_stage(graph, dispositions, 'CLAIM')

    def edit(record):
        if record['record_id'] == victim['record_id']:
            record['payload'].update(outcome='DEFERRED', result_refs=[])

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert evaluate(graph, dispositions, records=changed, enforce_success=False).valid
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_SUCCESS_REQUIRED'}


def successor(graph, disposition, *, previous=True):
    return graph.add('obligation-disposition', {
        **disposition['payload'], 'outcome': 'FAILED', 'result_refs': [],
        'reason': 'Later synthetic evidence invalidates this attempted source processing.',
        'previous_ref': exact_ref(disposition) if previous else None,
    })


def test_current_disposition_is_relative_to_explicit_historical_universe(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    historical_universe = [exact_ref(r) for r in graph.records]
    before = by_stage(graph, dispositions, 'SOURCE')
    after = successor(graph, before)
    require_control(graph)
    # A later known record must not retroactively alter an explicitly bounded
    # historical snapshot, but cannot be ignored inside a newer ledger cut.
    assert evaluate(graph, dispositions, universe=historical_universe).valid
    assert codes(evaluate(graph, dispositions)) == {'OBLIGATION_STALE_DISPOSITION'}
    latest = [after if d == before else d for d in dispositions]
    assert evaluate(graph, latest, enforce_success=False).valid
    assert codes(evaluate(graph, latest)) == {'OBLIGATION_SUCCESS_REQUIRED'}


def test_two_unmerged_current_branches_cannot_be_selected_away(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    successor(graph, by_stage(graph, dispositions, 'SOURCE'), previous=False)
    require_control(graph)
    assert codes(evaluate(graph, dispositions)) == {'OBLIGATION_AMBIGUOUS_HEAD'}


def test_universe_cannot_omit_selected_history_to_hide_a_branch(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    before = by_stage(graph, dispositions, 'SOURCE')
    after = successor(graph, before)
    latest = [after if d == before else d for d in dispositions]
    require_control(graph)
    assert evaluate(graph, latest, enforce_success=False).valid
    universe = [exact_ref(r) for r in graph.records if r != before]
    assert codes(evaluate(graph, latest, universe=universe, enforce_success=False)) == {'OBLIGATION_OUTSIDE_UNIVERSE'}


@pytest.mark.parametrize('attack', ['missing', 'duplicate'])
def test_each_frozen_obligation_selects_exactly_one_current_disposition(bundle, attack):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    selected = dispositions[:-1] if attack == 'missing' else dispositions + [dispositions[-1]]
    assert codes(evaluate(graph, selected)) == {'OBLIGATION_CARDINALITY'}


def set_argument_obligation(graph, *, stage='ARGUMENT'):
    def edit(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['obligation_id'] == 'obligation:proof':
                    obligation.update(stage=stage, requirement='SUCCESS_REQUIRED')
    graph.records = reseal(graph.records, edit)
    for name in ['policy', 'profile', 'source', 'span', 'claim', 'plan', 'structure', 'discovery', 'decision', 'scope']:
        setattr(graph, name, current(graph.records, getattr(graph, name)))


def argument_control(graph):
    set_argument_obligation(graph)
    math, _, route, snapshot = graph.argument(open_obligations=False)
    review = graph.add('argument-review', {
        'snapshot_ref': exact_ref(snapshot), 'proof_plan_refs': [exact_ref(route)],
        'review': graph.review(snapshot), 'outcome': 'SUPPORTED',
        'open_obligation_ids': [], 'open_challenge_refs': [], 'conditions': [],
    }, actor='actor:reviewer', role='ARGUMENT_REVIEWER')
    assessment = graph.add('axis-assessment', {
        'target_refs': [exact_ref(graph.claim)], 'axis': 'mathematical_correctness',
        'applicability': 'APPLICABLE', 'result': 'SUPPORTED', 'execution': 'COMPLETED',
        'method': 'ARGUMENT_REVIEW', 'review': graph.review(graph.claim),
        'support_refs': [exact_ref(review)], 'counterevidence_refs': [], 'conditions': [],
        'frontier_refs': [], 'rationale': 'Synthetic argument-result fixture, not an actual argument evaluation.',
    }, actor='actor:auditor', role='SCIENTIFIC_REVIEWER')
    return math, review, assessment


def test_new_condition_cannot_be_added_to_success_for_the_frozen_original_claim(bundle):
    graph = FixtureGraph(bundle)
    _, review, assessment = argument_control(graph)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    condition = {'condition_id': 'condition:new', 'statement': 'An additional hypothesis H holds.',
                 'origin': 'AGENT_ADDED', 'source_span_refs': []}

    def edit(record):
        if record['record_id'] in {review['record_id'], assessment['record_id']}:
            record['payload']['conditions'] = [condition]

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_NEW_CONDITIONS', 'OBLIGATION_STAGE_EVIDENCE'}


def test_order_of_existing_independent_conditions_does_not_change_target(bundle):
    graph = FixtureGraph(bundle)
    _, review, assessment = argument_control(graph)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    conditions = [{'condition_id': f'condition:{name}', 'statement': f'Premise {name} holds.',
                   'origin': 'SOURCE_EXPLICIT', 'source_span_refs': [exact_ref(graph.span)]} for name in ['a', 'b']]

    def edit(record):
        if record['record_id'] in {graph.claim['record_id'], review['record_id'], assessment['record_id']}:
            record['payload']['conditions'] = copy.deepcopy(conditions if record['record_id'] == graph.claim['record_id'] else conditions[::-1])

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert evaluate(graph, dispositions, records=changed).valid


def formal_control(graph):
    set_argument_obligation(graph, stage='FORMAL')
    math, _, route, snapshot = graph.argument(open_obligations=False)
    formal_bytes = graph.asset('formal', b'-- synthetic source, deliberately never executed\n')
    lock = graph.asset('formal-lock', b'{"synthetic":true}', 'application/json')
    log = graph.asset('checker-log', b'Synthetic contract fixture only, no checker was invoked.\n')
    environment = graph.add('formal-environment', {
        'prover': 'Lean4', 'toolchain': 'leanprover/lean4:fixture', 'package_manifest': lock,
        'source_artifacts': [formal_bytes], 'allowed_axioms': [], 'allowed_trust_mechanisms': [],
        'command': ['fixture-do-not-run'], 'network_access': 'DISABLED',
    })
    packet = graph.add('formalization-packet', {
        'scope_ref': exact_ref(graph.scope), 'math_ref': exact_ref(math),
        'argument_ref': exact_ref(snapshot), 'proof_plan_ref': exact_ref(route),
        'source_claim_refs': [exact_ref(graph.claim)], 'semantic_refs': [],
        'environment_ref': exact_ref(environment), 'expected_declarations': ['Synthetic.target'],
        'open_obligation_ids': [], 'mode': 'EXPLORATORY',
    })
    work = graph.add('work-attempt', {
        'plan_ref': exact_ref(graph.plan), 'operation': 'synthetic-contract-fixture',
        'target_refs': [exact_ref(packet)], 'started_at': '2026-09-07T00:00:00Z',
        'finished_at': '2026-09-07T00:00:00Z', 'outcome': 'SUCCEEDED', 'output_refs': [],
        'logs': [], 'cost_units': 0, 'progress_observed': True,
    })
    attempt = graph.add('formalization-attempt', {
        'packet_ref': exact_ref(packet), 'attempt_ref': exact_ref(work), 'outcome': 'GENERATED',
        'artifacts': [formal_bytes], 'diagnostics': ['Synthetic fixture, never executed.'],
    }, role='FORMALIZER')
    check = graph.add('formal-check', {
        'packet_ref': exact_ref(packet), 'attempt_ref': exact_ref(attempt),
        'environment_ref': exact_ref(environment), 'review': graph.review(attempt),
        'outcome': 'KERNEL_CHECKED', 'built_declarations': [{
            'name': 'Synthetic.target', 'statement': 'Synthetic proposition, no proof has run.',
            'source_artifact': formal_bytes, 'is_axiom': False, 'axioms': [], 'dependencies': []}],
        'placeholder_findings': [], 'logs': [log], 'exit_code': 0,
    }, actor='actor:reviewer', role='FORMAL_CHECKER')
    alignment = graph.add('alignment-assessment', {
        'comparison_kind': 'SOURCE_TO_FORMAL', 'source_refs': [exact_ref(graph.claim)],
        'target_refs': [exact_ref(check)], 'review': graph.review(graph.claim, check),
        'comparisons': [{'dimension': 'ASSUMPTION', 'source_value': 'Fixture meaning.',
                         'target_value': 'Fixture meaning.', 'relation': 'EQUIVALENT', 'witness_refs': []}],
        'outcome': 'ALIGNED', 'backtranslation_refs': [],
    }, actor='actor:auditor', role='ALIGNMENT_REVIEWER')
    assessment = graph.add('axis-assessment', {
        'target_refs': [exact_ref(graph.claim)], 'axis': 'mathematical_correctness',
        'applicability': 'APPLICABLE', 'result': 'SUPPORTED', 'execution': 'COMPLETED',
        'method': 'KERNEL_AND_ALIGNMENT', 'review': graph.review(graph.claim),
        'support_refs': [exact_ref(check), exact_ref(alignment)], 'counterevidence_refs': [],
        'conditions': [], 'frontier_refs': [], 'rationale': 'Synthetic formal evidence-contract fixture only.',
    }, actor='actor:auditor', role='SCIENTIFIC_REVIEWER')
    return math, check, assessment


def test_failed_formal_result_cannot_satisfy_completed_required_obligation(bundle):
    graph = FixtureGraph(bundle)
    _, check, assessment = formal_control(graph)
    dispositions, _ = source_map(graph, [check, assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_id'] == check['record_id']:
            record['payload'].update(outcome='FAILED', built_declarations=[], exit_code=1)
        if record['record_id'] == assessment['record_id']:
            # Honest failed evidence remains schema/contract-valid; only the
            # obligation disposition still makes an unjustified success claim.
            record['payload']['result'] = 'INCONCLUSIVE'

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_STAGE_EVIDENCE', 'OBLIGATION_AXIS_EVIDENCE'}


def test_formal_math_assumption_cannot_silently_narrow_original_scientific_target(bundle):
    graph = FixtureGraph(bundle)
    math, check, assessment = formal_control(graph)
    dispositions, _ = source_map(graph, [check, assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_id'] == math['record_id']:
            record['payload']['assumptions'] = [{
                'condition_id': 'condition:extra', 'statement': 'An extra premise not in the original claim.',
                'origin': 'AGENT_ADDED', 'source_span_refs': []}]

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_NEW_CONDITIONS', 'OBLIGATION_AXIS_EVIDENCE'}


def test_unimplemented_release_stage_cannot_claim_completion_with_arbitrary_reference(bundle):
    graph = FixtureGraph(bundle)
    _, _, assessment = argument_control(graph)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['obligation_id'] == 'obligation:proof':
                    obligation['stage'] = 'RELEASE'

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_UNSUPPORTED_STAGE'}


def test_artifact_check_is_not_inferred_from_reference_hash_alone(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    graph.artifacts = []
    result = evaluate(graph, dispositions)
    assert not result.valid and not result.artifact_checked
    assert codes(result) == {'OBLIGATION_ARTIFACT'}
    result = evaluate(graph, dispositions, require_artifacts=False)
    assert result.valid and not result.artifact_checked


def test_success_must_cover_every_exact_target_and_every_requested_axis(bundle):
    graph = FixtureGraph(bundle)
    other = graph.claim_record('Another exact target that has not been assessed.')
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def add_target(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['stage'] == 'CLAIM':
                    obligation['target_refs'].append(exact_ref(other))

    changed = reseal(graph.records, add_target)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_STAGE_EVIDENCE'}

    def add_axis(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['stage'] == 'CLAIM':
                    obligation['applicable_axes'].append('semantic_applicability')

    changed = reseal(graph.records, add_axis)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_AXIS_EVIDENCE'}


def test_accounting_for_an_inconclusive_review_does_not_require_a_positive_conclusion(bundle):
    graph = FixtureGraph(bundle)
    _, review, assessment = argument_control(graph)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['stage'] == 'ARGUMENT':
                    obligation['requirement'] = 'ACCOUNT_FOR'
        if record['record_id'] == review['record_id']:
            record['payload']['outcome'] = 'INCONCLUSIVE'
        if record['record_id'] == assessment['record_id']:
            record['payload']['result'] = 'INCONCLUSIVE'

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert evaluate(graph, dispositions, records=changed).valid


def test_observed_completion_cannot_relabel_synthetic_result_evidence(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    victim = by_stage(graph, dispositions, 'CLAIM')

    def edit(record):
        if record['record_id'] == victim['record_id']:
            record['data_class'] = 'OBSERVED'

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_SYNTHETIC_PROMOTION'}


def test_repaired_target_must_explicitly_retain_parent_condition_to_use_restricted_evidence(bundle):
    graph = FixtureGraph(bundle)
    pure = {'condition_id': 'condition:pure', 'statement': 'The state is pure.',
            'origin': 'SOURCE_EXPLICIT', 'source_span_refs': [exact_ref(graph.span)]}

    def condition_original(record):
        if record['record_id'] == graph.claim['record_id']:
            record['payload']['conditions'] = [pure]

    graph.records = reseal(graph.records, condition_original)
    set_argument_obligation(graph)
    original = graph.claim
    derived = graph.add('derived-claim', {
        'statement': 'The repaired quantity is nonnegative for pure states.', 'origin': 'REPAIR',
        'parent_refs': [exact_ref(original)], 'added_conditions': [pure], 'relation': 'CORRECTS',
        'rationale': 'The repair explicitly retains the earlier pure-state restriction.',
    })
    # Keep creation dependencies ordered so later exact reseals also update the
    # scope's forward reference to this explicitly frozen derived target.
    graph.records.remove(derived)
    graph.records.insert(graph.records.index(graph.plan), derived)

    def retarget(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['stage'] == 'ARGUMENT':
                    obligation['target_refs'] = [exact_ref(derived)]

    graph.records = reseal(graph.records, retarget)
    graph.claim = derived
    math, review, assessment = argument_control(graph)
    graph.claim = current(graph.records, original)

    def restricted_evidence(record):
        if record['record_id'] == math['record_id']:
            record['payload']['assumptions'] = [pure]
        if record['record_id'] in {review['record_id'], assessment['record_id']}:
            record['payload']['conditions'] = [pure]

    graph.records = reseal(graph.records, restricted_evidence)
    assessment = current(graph.records, assessment)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def broaden_repair(record):
        if record['record_id'] == derived['record_id']:
            record['payload'].update(statement='The repaired quantity is nonnegative for all states.',
                                     added_conditions=[])

    changed = reseal(graph.records, broaden_repair)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_NEW_CONDITIONS', 'OBLIGATION_STAGE_EVIDENCE'}


def test_typed_counterexample_completes_argument_accounting_without_success_promotion(bundle):
    graph = FixtureGraph(bundle)
    instance = graph.node('A synthetic instance in the target domain violates the conclusion.')
    example = graph.add('counterexample', {
        'target_ref': exact_ref(graph.claim), 'construction': 'A synthetic witness for contract testing.',
        'premise_checks': [{'dimension': 'ASSUMPTION', 'source_value': 'The stated target premise.',
                            'target_value': 'The witness satisfies that premise.', 'relation': 'EQUIVALENT',
                            'witness_refs': [exact_ref(instance)]}],
        'violated_conclusion': 'The exact target conclusion fails for this synthetic instance.',
        'evidence_refs': [exact_ref(instance)], 'limitations': ['Not an actual mathematical result.'],
    })
    assessment = graph.add('axis-assessment', {
        'target_refs': [exact_ref(graph.claim)], 'axis': 'mathematical_correctness',
        'applicability': 'APPLICABLE', 'result': 'COUNTEREVIDENCE', 'execution': 'COMPLETED',
        'method': 'COUNTEREXAMPLE_REVIEW', 'review': graph.review(graph.claim),
        'support_refs': [], 'counterevidence_refs': [exact_ref(example)], 'conditions': [],
        'frontier_refs': [], 'rationale': 'Record an independently reviewed synthetic counterexample.',
    }, actor='actor:reviewer', role='SCIENTIFIC_REVIEWER')
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def require_success(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['stage'] == 'ARGUMENT':
                    obligation['requirement'] = 'SUCCESS_REQUIRED'

    changed = reseal(graph.records, require_success)
    require_control(graph, changed)
    assert codes(evaluate(graph, dispositions, records=changed)) == {'OBLIGATION_STAGE_EVIDENCE'}
