"""Synthetic offline dependency probes; no scientific evaluation is executed."""
from __future__ import annotations

import copy

import pytest

from test_contracts import FixtureGraph
from agtxiv_v3.contracts import ContractError, RecordSet, SchemaBundle, content_hash, exact_ref
from agtxiv_v3.dependencies import inspect_dependencies


@pytest.fixture(scope='module')
def bundle():
    return SchemaBundle()


def binding(graph, source, target, route=None, axes=('mathematical_correctness',), kind='MATHEMATICAL'):
    return graph.add('dependency-binding', {
        'prerequisite_ref': exact_ref(source), 'dependent_ref': exact_ref(target),
        'kind': kind, 'affected_axes': list(axes),
        'proof_plan_ref': exact_ref(route) if route else None,
        'comparison': [{'dimension': 'ASSUMPTION', 'source_value': 'Synthetic premise.',
                        'target_value': 'Synthetic use.', 'relation': 'UNKNOWN', 'witness_refs': []}],
        'reuse_decision_ref': None,
    })


def inspect(graph, *triggers, reverse=False):
    records = graph.records[::-1] if reverse else graph.records
    store = RecordSet(graph.bundle, records, graph.artifacts)
    store.validate().require_valid()
    return inspect_dependencies(store, [exact_ref(r) for r in triggers])


def test_display_containment_and_input_provenance_are_not_edges(bundle):
    graph = FixtureGraph(bundle)
    _, node, route, snapshot = graph.argument()
    result = inspect(graph, node)
    assert result.payload['affected'] == []
    assert result.payload['unaffected_proof_plan_refs'] == [exact_ref(route)]
    assert exact_ref(snapshot) in result.input_refs
    assert 'unknown' in ' '.join(result.limitations)


def test_typed_transitive_axes_are_potential_not_filtered_by_invented_transfer(bundle):
    graph = FixtureGraph(bundle)
    a, b, c = [graph.node(name) for name in ['A', 'B', 'C']]
    first = binding(graph, a, b, axes=('source_fidelity',), kind='VALIDATION')
    second = binding(graph, b, c, axes=('semantic_applicability',), kind='SEMANTIC')
    result = inspect(graph, a)
    targets = {r['target_ref']['record_id']: r for r in result.payload['affected']}
    assert targets[b['record_id']]['axes'] == ['source_fidelity']
    assert targets[c['record_id']]['axes'] == ['semantic_applicability']
    assert all('Potential reachability' in r['reason'] for r in targets.values())
    assert result.payload['dependency_refs'] == [exact_ref(first), exact_ref(second)]
    assert 'no prerequisite-axis transfer' in ' '.join(result.limitations)


def test_route_local_failure_does_not_spill_to_shared_conclusion_alternative(bundle):
    graph = FixtureGraph(bundle)
    _, conclusion, route, _ = graph.argument()
    alternative = graph.add('proof-plan', {**route['payload'], 'route': 'ALTERNATIVE'})
    source = graph.node('Premise used only by the first route.')
    binding(graph, source, conclusion, route)
    result = inspect(graph, source)
    assert [r['target_ref'] for r in result.payload['affected']] == [exact_ref(conclusion)]
    assert result.payload['affected'][0]['proof_plan_ref'] == exact_ref(route)
    assert result.payload['unaffected_proof_plan_refs'] == [exact_ref(alternative)]


@pytest.mark.parametrize('prerequisite_is_route', [False, True])
def test_explicit_cross_route_binding_is_traversed(bundle, prerequisite_is_route):
    graph = FixtureGraph(bundle)
    _, conclusion, route, _ = graph.argument()
    alternative = graph.add('proof-plan', {**route['payload'], 'route': 'ALTERNATIVE'})
    source, target = graph.node('A'), graph.node('Z')
    prerequisite = route if prerequisite_is_route else conclusion
    binding(graph, source, prerequisite, route)
    binding(graph, prerequisite, target, alternative)
    result = inspect(graph, source)
    affected = next((r for r in result.payload['affected'] if r['target_ref'] == exact_ref(target)), None)
    assert affected is not None
    assert affected['proof_plan_ref'] == exact_ref(alternative)
    assert result.payload['unaffected_proof_plan_refs'] == []


def test_many_reasons_are_bounded_with_exact_provenance_retained(bundle):
    graph = FixtureGraph(bundle)
    source, target = graph.node('A'), graph.node('Z')
    declarations = [binding(graph, source, target) for _ in range(250)]
    result = inspect(graph, source)
    assert len(result.payload['affected']) == 1
    reason = result.payload['affected'][0]['reason']
    assert len(reason) <= 65536
    assert '250' in reason and 'input_refs' in reason
    assert result == inspect(graph, source, reverse=True)
    assert all(exact_ref(r) in result.input_refs for r in declarations)
    assert result.payload['dependency_refs'] == sorted(
        [exact_ref(r) for r in declarations], key=lambda r: r['record_id'])
    assert not bundle.validate_record(graph.add('impact-analysis', result.payload))


@pytest.mark.parametrize('route_count, downstream_count', [(100, 99), (101, 100)])
def test_affected_target_route_pairs_respect_schema_limit(bundle, route_count, downstream_count):
    graph = FixtureGraph(bundle)
    _, conclusion, route, _ = graph.argument()
    source, shared = graph.node('A'), graph.node('Shared dependent')
    routes = [route] + [graph.add('proof-plan', route['payload']) for _ in range(route_count - 1)]
    for route in routes:
        binding(graph, source, shared, route)
    for i in range(downstream_count):
        binding(graph, shared, graph.node(f'Target {i}'))
    expected = route_count * (downstream_count + 1)
    if expected > 10000:
        # The output can exceed its limit even with < 10000 input records.
        with pytest.raises(ContractError, match='affected.*10000'):
            inspect(graph, source)
    else:
        result = inspect(graph, source)
        assert len(result.payload['affected']) == expected == 10000
        assert not bundle.validate_record(graph.add('impact-analysis', result.payload))


def test_shared_inference_premise_does_not_transfer_route_local_impact(bundle):
    graph = FixtureGraph(bundle)
    _, shared, route, _ = graph.argument()
    source, target = graph.node('A'), graph.node('Alternative result')
    step = graph.add('inference-step', {
        'premise_refs': [exact_ref(shared)], 'conclusion_ref': exact_ref(target),
        'rule': 'DIRECT', 'justification': 'Synthetic alternative inference.',
        'context_ref': None, 'discharged_context_refs': [], 'rule_evidence_refs': [],
    })
    alternative = graph.add('proof-plan', {
        **route['payload'], 'route': 'ALTERNATIVE', 'conclusion_ref': exact_ref(target),
        'node_refs': [exact_ref(shared), exact_ref(target)], 'inference_refs': [exact_ref(step)],
    })
    binding(graph, source, shared, route)
    result = inspect(graph, source)
    assert [r['target_ref'] for r in result.payload['affected']] == [exact_ref(shared)]
    assert result.payload['unaffected_proof_plan_refs'] == [exact_ref(alternative)]
    # A direct trigger on the shared premise is not a route-local finding.
    direct = inspect(graph, shared)
    assert direct.payload['affected'][0]['target_ref'] == exact_ref(target)
    assert direct.payload['affected'][0]['proof_plan_ref'] == exact_ref(alternative)


def test_joint_premises_traverse_actual_inference_not_unused_route_nodes(bundle):
    graph = FixtureGraph(bundle)
    a, b, conclusion, unused = [graph.node(name) for name in ['A', 'B', 'C', 'Unused']]
    step = graph.add('inference-step', {
        'premise_refs': [exact_ref(a), exact_ref(b)], 'conclusion_ref': exact_ref(conclusion),
        'rule': 'DIRECT', 'justification': 'Synthetic joint-premise declaration only.',
        'context_ref': None, 'discharged_context_refs': [], 'rule_evidence_refs': [],
    })
    route = graph.add('proof-plan', {
        'scope_ref': exact_ref(graph.scope), 'conclusion_ref': exact_ref(conclusion),
        'route': 'ORIGINAL', 'node_refs': [exact_ref(r) for r in [a, b, conclusion, unused]],
        'inference_refs': [exact_ref(step)], 'required_obligation_ids': ['obligation:proof'],
        'open_obligation_ids': ['obligation:proof'],
    })
    for trigger in [a, b, step]:
        result = inspect(graph, trigger)
        assert result.payload['affected'][0]['target_ref'] == exact_ref(conclusion)
        assert result.payload['affected'][0]['proof_plan_ref'] == exact_ref(route)
        assert result.payload['affected'][0]['axes'] == ['mathematical_correctness']
    assert inspect(graph, unused).payload['affected'] == []


def test_dependency_cycles_terminate_and_diamond_reasons_are_retained(bundle):
    graph = FixtureGraph(bundle)
    a, b, c = [graph.node(name) for name in ['A', 'B', 'C']]
    binding(graph, a, b)
    binding(graph, b, a)
    binding(graph, a, c)
    binding(graph, b, c)
    result = inspect(graph, a)
    assert len(result.payload['affected']) == 3
    target = next(r for r in result.payload['affected'] if r['target_ref'] == exact_ref(c))
    assert target['reason'].count('Potential reachability') == 2


def test_exact_revisions_never_implicitly_retarget_old_dependencies(bundle):
    graph = FixtureGraph(bundle)
    a, b = graph.node('Old premise.'), graph.node('Dependent.')
    binding(graph, a, b)
    newer = copy.deepcopy(a)
    newer['revision'] = 2
    newer['payload']['statement'] = 'Changed premise.'
    newer['content_hash'] = content_hash(newer)
    graph.records.append(newer)
    assert inspect(graph, newer).payload['affected'] == []
    assert inspect(graph, a).payload['affected'][0]['target_ref'] == exact_ref(b)


@pytest.mark.parametrize('attack', ['hash', 'type', 'revision', 'missing', 'empty', 'bool_revision', 'float_revision'])
def test_invalid_exact_triggers_fail_closed(bundle, attack):
    graph = FixtureGraph(bundle)
    reference = exact_ref(graph.claim)
    if attack == 'hash':
        reference['content_hash'] = 'sha256:' + '0' * 64
    elif attack == 'type':
        reference['record_type'] = graph.span['record_type']
    elif attack == 'revision':
        reference['revision'] += 1
    elif attack == 'missing':
        del reference['content_hash']
    elif attack == 'bool_revision':
        reference['revision'] = True
    elif attack == 'float_revision':
        reference['revision'] = 1.0
    with pytest.raises(ContractError):
        inspect_dependencies(RecordSet(bundle, graph.records), [] if attack == 'empty' else [reference])


def test_invalid_store_is_not_treated_as_validated_input(bundle):
    graph = FixtureGraph(bundle)
    graph.claim['payload']['statement'] = 'Unsealed mutation.'
    with pytest.raises(ContractError):
        inspect_dependencies(RecordSet(bundle, graph.records), [exact_ref(graph.claim)])


def test_deterministic_schema_shaped_report_binds_all_inputs_without_mutation(bundle):
    graph = FixtureGraph(bundle)
    _, node, route, _ = graph.argument()
    binding(graph, graph.claim, node, route)
    before = copy.deepcopy(graph.records)
    result = inspect(graph, graph.claim, graph.span)
    reordered = inspect(graph, graph.span, graph.claim, graph.claim, reverse=True)
    assert result == reordered
    assert graph.records == before
    assert result.authority_status == 'ORACLE_PROPOSED'
    assert result.scientific_status == 'UNVERIFIED'
    record = graph.add('impact-analysis', result.payload)
    assert not bundle.validate_record(record)
    assert inspect(graph, graph.claim, graph.span).input_hash != result.input_hash
    # Public report values are detached from the store and original records.
    result.payload['affected'][0]['target_ref']['revision'] = 999
    assert graph.records[:len(before)] == before
