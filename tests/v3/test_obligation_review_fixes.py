"""Reviewed obligation/import regressions using offline synthetic controls."""
import pytest

from test_contracts import FixtureGraph
from agtxiv_v3.contracts import exact_ref
from agtxiv_v3.vibefeld import PINNED_COMMIT, inspect_capture
from test_contract_regressions import require_control, reseal, report
from test_obligations import argument_control, formal_control, source_map, evaluate, codes, bundle, current
from test_vibefeld import capture, event, raw, TIME


def add_support_inventory(graph):
    route = next(r for r in graph.records if r['record_type'].split('/')[0].endswith('proof-plan'))
    start = len(graph.records)
    context = graph.add('assumption-context', {
        'parent_ref': None, 'assumptions': [{'condition_id': 'condition:local',
            'statement': 'Synthetic local premise.', 'origin': 'AGENT_ADDED', 'source_span_refs': []}],
        'introduction_reason': 'Synthetic local scope.', 'allowed_use': 'Local only.'})
    conclusion = graph.node('Synthetic inference conclusion.')
    inference = graph.add('inference-step', {
        'premise_refs': route['payload']['node_refs'], 'conclusion_ref': exact_ref(conclusion),
        'rule': 'DIRECT', 'justification': 'Synthetic rule fixture.', 'context_ref': None,
        'discharged_context_refs': [], 'rule_evidence_refs': []})
    dependency = graph.add('dependency-binding', {
        'dependent_ref': exact_ref(conclusion), 'prerequisite_ref': exact_ref(graph.claim),
        'kind': 'MATHEMATICAL', 'affected_axes': ['mathematical_correctness'],
        'proof_plan_ref': None, 'reuse_decision_ref': None, 'comparison': [{
            'dimension': 'ASSUMPTION', 'source_value': 'Synthetic premise.',
            'target_value': 'Synthetic premise.', 'relation': 'EQUIVALENT', 'witness_refs': []}]})
    challenge = graph.add('challenge', {
        'target_ref': exact_ref(conclusion), 'category': 'INFERENCE', 'severity': 'MAJOR',
        'statement': 'Synthetic objection.', 'evidence_refs': []})
    disposition = graph.add('challenge-disposition', {
        'challenge_ref': exact_ref(challenge), 'response': 'Synthetic response.',
        'response_refs': [exact_ref(inference)], 'review': graph.review(challenge),
        'outcome': 'RESOLVED', 'replacement_ref': None, 'reason': 'Synthetic resolution.'},
        actor='actor:reviewer', role='ARGUMENT_REVIEWER')
    additions = graph.records[start:]
    graph.records = graph.records[:start]
    index = graph.records.index(route)
    graph.records[index:index] = additions

    def edit(record):
        name = record['record_type'].split('/')[0].split('.')[-1]
        if name in {'proof-plan', 'argument-snapshot'}:
            record['payload']['node_refs'].append(exact_ref(conclusion))
            record['payload']['inference_refs'].append(exact_ref(inference))
        if name == 'argument-snapshot':
            record['payload'].update(context_refs=[exact_ref(context)],
                dependency_refs=[exact_ref(dependency)], challenge_refs=[exact_ref(challenge)],
                challenge_disposition_refs=[exact_ref(disposition)])

    graph.records = reseal(graph.records, edit)


@pytest.mark.parametrize('control', [argument_control, formal_control])
@pytest.mark.parametrize('kind', ['proof-plan', 'argument-node', 'inference-step', 'assumption-context',
                                  'dependency-binding', 'challenge', 'challenge-disposition'])
def test_support_must_be_inside_explicit_universe(bundle, control, kind):
    graph = FixtureGraph(bundle)
    _, _, assessment = control(graph)
    add_support_inventory(graph)
    assessment = current(graph.records, assessment)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    universe = [exact_ref(r) for r in graph.records if r['record_type'].split('/')[0].split('.')[-1] != kind]
    assert 'OBLIGATION_OUTSIDE_UNIVERSE' in codes(evaluate(graph, dispositions, universe=universe))


@pytest.mark.parametrize('control', [argument_control, formal_control])
@pytest.mark.parametrize('kind', ['proof-plan', 'argument-node', 'inference-step', 'assumption-context',
                                  'dependency-binding', 'challenge', 'challenge-disposition'])
def test_observed_wrappers_cannot_launder_support(bundle, control, kind):
    graph = FixtureGraph(bundle)
    _, _, assessment = control(graph)
    add_support_inventory(graph)
    assessment = current(graph.records, assessment)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if not record['record_type'].split('/')[0].endswith(kind):
            record['data_class'] = 'OBSERVED'

    changed = reseal(graph.records, edit)
    assert {i.code for i in report(graph, changed).issues} == {'SYNTHETIC_PROMOTION'}
    assert 'OBLIGATION_SYNTHETIC_PROMOTION' in codes(evaluate(graph, dispositions, records=changed))


def test_failed_formal_execution_can_be_accounted_for(bundle):
    graph = FixtureGraph(bundle)
    _, check, assessment = formal_control(graph)
    dispositions, _ = source_map(graph, [check, assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_type'].split('/')[0].endswith(('inventory-discovery', 'frozen-scope')):
            for obligation in record['payload']['obligations']:
                if obligation['stage'] == 'FORMAL':
                    obligation['requirement'] = 'ACCOUNT_FOR'
        if record['record_id'] == check['record_id']:
            record['payload'].update(outcome='FAILED', built_declarations=[], exit_code=1)
        if record['record_id'] == assessment['record_id']:
            record['payload']['result'] = 'INCONCLUSIVE'

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert evaluate(graph, dispositions, records=changed).valid


def test_public_capture_rejects_extraction_from_absent_node():
    files = capture(extra=[event('lemma_extracted', lemma={
        'id': 'lemma', 'statement': 'Synthetic lemma', 'node_id': '1', 'created': TIME})])
    options = dict(commit=PINNED_COMMIT, workspace_key='fixture:lemma')
    assert inspect_capture(files, **options).report()['outcome'] == 'STRUCTURALLY_IMPORTED'
    files['ledger/000003.json'] = raw(event('lemma_extracted', lemma={
        'id': 'lemma', 'statement': 'Synthetic lemma', 'node_id': '1.99', 'created': TIME}))
    report = inspect_capture(files, **options).report()
    assert report['outcome'] == 'REJECTED'
    assert any('absent node' in issue['message'] for issue in report['issues'])


def test_provenance_only_synthetic_parent_does_not_contaminate_observed_support(bundle):
    graph = FixtureGraph(bundle)
    _, _, assessment = argument_control(graph)
    parent = graph.claim_record('Synthetic historical claim, not a premise of the repair.')
    graph.records.remove(parent)
    graph.records.insert(graph.records.index(graph.claim), parent)

    parent_refs = []

    def edit(record):
        if record['record_id'] == parent['record_id']:
            from agtxiv_v3.contracts import content_hash
            record['content_hash'] = content_hash(record)
            parent_refs.append(exact_ref(record))
        if record['record_type'].split('/')[0].endswith('inventory-discovery'):
            record['payload']['claim_refs'] = parent_refs.copy()
        if record['record_id'] != parent['record_id']:
            record['data_class'] = 'OBSERVED'
        if record['record_id'] == graph.claim['record_id']:
            record['record_type'] = 'agtxiv.v3.derived-claim/0.0.0'
            record['payload'] = {
                'statement': 'Independently reconstructed target.', 'origin': 'REPAIR',
                'parent_refs': parent_refs.copy(), 'added_conditions': [], 'relation': 'CORRECTS',
                'rationale': 'History only; the old statement is not a premise.'}

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    graph.records = changed
    graph.claim = current(changed, graph.claim)
    assessment = current(changed, assessment)
    # SOURCE_REVIEW is intentionally not used for this derived target.
    from agtxiv_v3.obligations import support_closure
    from agtxiv_v3.contracts import RecordSet
    store = RecordSet(bundle, changed, graph.artifacts)
    closure = list(support_closure([exact_ref(assessment)], store.resolve))
    assert all(r['data_class'] == 'OBSERVED' for r in closure)
    assert parent['record_id'] not in {r['record_id'] for r in closure}


def test_blocked_formal_check_is_not_performed_execution(bundle):
    graph = FixtureGraph(bundle)
    _, check, assessment = formal_control(graph)
    dispositions, _ = source_map(graph, [check, assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_id'] == check['record_id']:
            record['payload'].update(outcome='BLOCKED', built_declarations=[], exit_code=1)
        if record['record_id'] == assessment['record_id']:
            record['payload']['result'] = 'INCONCLUSIVE'

    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert 'OBLIGATION_STAGE_EVIDENCE' in codes(evaluate(
        graph, dispositions, records=changed, enforce_success=False))


@pytest.mark.parametrize('revision', [True, 1.0, False, 0, -1, 9007199254740992, '1', None])
def test_record_set_resolve_rejects_non_integer_or_nonpositive_revision(bundle, revision):
    from agtxiv_v3.contracts import ContractError, RecordSet
    graph = FixtureGraph(bundle)
    store = RecordSet(bundle, graph.records, graph.artifacts)
    reference = exact_ref(graph.claim)
    assert store.resolve(reference) == graph.claim
    reference['revision'] = revision
    with pytest.raises(ContractError):
        store.resolve(reference)


@pytest.mark.parametrize('field', ['record_type', 'record_id', 'content_hash'])
@pytest.mark.parametrize('value', [None, True, 1, [], {}])
def test_record_set_resolve_requires_string_identity_fields(bundle, field, value):
    from agtxiv_v3.contracts import ContractError, RecordSet
    graph = FixtureGraph(bundle)
    store = RecordSet(bundle, graph.records, graph.artifacts)
    reference = exact_ref(graph.claim)
    assert store.resolve(reference) == graph.claim
    reference[field] = value
    with pytest.raises(ContractError):
        store.resolve(reference)


def counterexample_control(graph, witness_field):
    witness = graph.node('Synthetic counterexample witness.')
    example = graph.add('counterexample', {
        'target_ref': exact_ref(graph.claim), 'construction': 'Synthetic instance.',
        'premise_checks': [{'dimension': 'ASSUMPTION', 'source_value': 'Target premise.',
            'target_value': 'Witness satisfies premise.', 'relation': 'EQUIVALENT',
            'witness_refs': [exact_ref(witness)] if witness_field == 'comparison' else []}],
        'violated_conclusion': 'Synthetic conclusion fails.',
        'evidence_refs': [exact_ref(witness)] if witness_field == 'evidence' else [exact_ref(graph.span)],
        'limitations': ['Not actual mathematical evidence.']})
    assessment = graph.add('axis-assessment', {
        'target_refs': [exact_ref(graph.claim)], 'axis': 'mathematical_correctness',
        'applicability': 'APPLICABLE', 'result': 'COUNTEREVIDENCE', 'execution': 'COMPLETED',
        'method': 'COUNTEREXAMPLE_REVIEW', 'review': graph.review(graph.claim),
        'support_refs': [], 'counterevidence_refs': [exact_ref(example)], 'conditions': [],
        'frontier_refs': [], 'rationale': 'Synthetic assessed counterexample.'},
        actor='actor:reviewer', role='SCIENTIFIC_REVIEWER')
    return witness, example, assessment


@pytest.mark.parametrize('witness_field', ['comparison', 'evidence'])
def test_accounted_counterexample_requires_full_witness_universe(bundle, witness_field):
    graph = FixtureGraph(bundle)
    witness, _, assessment = counterexample_control(graph, witness_field)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    universe = [exact_ref(r) for r in graph.records if r != witness]
    assert 'OBLIGATION_OUTSIDE_UNIVERSE' in codes(evaluate(graph, dispositions, universe=universe))


@pytest.mark.parametrize('witness_field', ['comparison', 'evidence'])
def test_assessed_counterexample_cannot_launder_synthetic_witness(bundle, witness_field):
    graph = FixtureGraph(bundle)
    witness, _, assessment = counterexample_control(graph, witness_field)
    dispositions, _ = source_map(graph, [assessment])
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_id'] != witness['record_id']:
            record['data_class'] = 'OBSERVED'

    changed = reseal(graph.records, edit)
    assert {i.code for i in report(graph, changed).issues} == {'SYNTHETIC_PROMOTION'}
    assert 'OBLIGATION_SYNTHETIC_PROMOTION' in codes(evaluate(graph, dispositions, records=changed))


@pytest.mark.parametrize('location', ['selected', 'universe', 'scope'])
@pytest.mark.parametrize('attack', ['bool', 'float', 'extra', 'missing', 'unhashable', 'not-object'])
def test_public_obligation_checker_validates_before_cache_and_universe(bundle, location, attack):
    from agtxiv_v3.contracts import RecordSet
    from agtxiv_v3.obligations import check_obligations
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    selected = [exact_ref(r) for r in dispositions]
    universe = [exact_ref(r) for r in graph.records]
    scope = exact_ref(graph.scope)
    reference = scope if location == 'scope' else exact_ref(dispositions[0])
    if attack == 'bool':
        reference['revision'] = True
    elif attack == 'float':
        reference['revision'] = 1.0
    elif attack == 'extra':
        reference['unexpected'] = 'field'
    elif attack == 'missing':
        del reference['revision']
    elif attack == 'unhashable':
        reference['record_id'] = []
    else:
        reference = None
    if location == 'scope':
        scope = reference
    elif location == 'selected':
        selected[0] = reference
    else:
        # Keep the valid entry as well, exposing aliasing during ingestion.
        universe.append(reference)
    result = check_obligations(RecordSet(bundle, graph.records, graph.artifacts),
        scope, selected, universe_refs=universe)
    assert 'OBLIGATION_EXACT_REFERENCE' in codes(result)


@pytest.mark.parametrize('enforce_success', [False, True])
def test_positive_support_is_not_contaminated_by_retained_counterevidence(bundle, enforce_success):
    graph = FixtureGraph(bundle)
    witness, example, counterassessment = counterexample_control(graph, 'comparison')
    dispositions, assessment = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid

    def edit(record):
        if record['record_id'] not in {witness['record_id'], counterassessment['record_id']}:
            record['data_class'] = 'OBSERVED'
        if record['record_id'] == assessment['record_id']:
            record['payload']['counterevidence_refs'] = [exact_ref(current(changed_prefix, example))]
        changed_prefix.append(record)

    changed_prefix = []
    changed = reseal(graph.records, edit)
    require_control(graph, changed)
    assert evaluate(graph, dispositions, records=changed, enforce_success=enforce_success).valid
    retained_only = {witness['record_id'], example['record_id'], counterassessment['record_id']}
    universe = [exact_ref(r) for r in changed if r['record_id'] not in retained_only]
    assert evaluate(graph, dispositions, records=changed, universe=universe,
                    enforce_success=enforce_success).valid
