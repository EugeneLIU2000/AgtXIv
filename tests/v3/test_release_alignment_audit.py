"""Release-audit regressions: formal alignment is distinct from proof success.

All inputs are synthetic and no prover is run. Positive controls include original
artifact bytes and explicit fixture authority; negatives are resealed so unrelated
hash/schema failures cannot hide the audited boundary.
"""
from __future__ import annotations

import pytest

from test_contracts import FixtureGraph
from agtxiv_v3.contracts import SchemaBundle, exact_ref
from test_contract_regressions import require_control, report, reseal


@pytest.fixture(scope='module')
def bundle():
    return SchemaBundle()


def formal_statement(graph, *, comparison_kind, failed_check=False):
    math, _, route, snapshot = graph.argument(open_obligations=True)
    statement = graph.asset('unproved-formal-statement', b'-- synthetic fixture; never executed\ntheorem target : True := by sorry\n')
    lock = graph.asset('alignment-lock', b'{"synthetic":true}', 'application/json')
    log = graph.asset('alignment-check-log', b'Synthetic unsuccessful check; never executed.\n')
    environment = graph.add('formal-environment', {
        'prover': 'Lean4', 'toolchain': 'leanprover/lean4:fixture',
        'package_manifest': lock, 'source_artifacts': [statement], 'allowed_axioms': [],
        'allowed_trust_mechanisms': [], 'command': ['fixture-do-not-run'], 'network_access': 'DISABLED',
    })
    packet = graph.add('formalization-packet', {
        'scope_ref': exact_ref(graph.scope), 'math_ref': exact_ref(math),
        'argument_ref': exact_ref(snapshot), 'proof_plan_ref': exact_ref(route),
        'source_claim_refs': [exact_ref(graph.claim)], 'semantic_refs': [],
        'environment_ref': exact_ref(environment), 'expected_declarations': ['target'],
        'open_obligation_ids': ['obligation:proof'], 'mode': 'EXPLORATORY',
    })
    work = graph.add('work-attempt', {
        'plan_ref': exact_ref(graph.plan), 'operation': 'synthetic-statement-generation',
        'target_refs': [exact_ref(packet)], 'started_at': '2026-09-07T00:00:00Z',
        'finished_at': '2026-09-07T00:00:00Z', 'outcome': 'SUCCEEDED',
        'output_refs': [], 'logs': [], 'cost_units': 0, 'progress_observed': True,
    })
    attempt = graph.add('formalization-attempt', {
        'packet_ref': exact_ref(packet), 'attempt_ref': exact_ref(work), 'outcome': 'PARTIAL',
        'artifacts': [statement], 'diagnostics': ['The proof remains unfinished; this fixture is not executed.'],
    }, role='FORMALIZER')
    formal = attempt
    if failed_check:
        formal = graph.add('formal-check', {
            'packet_ref': exact_ref(packet), 'attempt_ref': exact_ref(attempt),
            'environment_ref': exact_ref(environment), 'review': graph.review(attempt),
            'outcome': 'FAILED', 'built_declarations': [], 'placeholder_findings': ['Unfinished proof.'],
            'logs': [log], 'exit_code': 1,
        }, actor='actor:reviewer', role='FORMAL_CHECKER')
    source = math if comparison_kind == 'MATH_TO_FORMAL' else graph.claim
    alignment = graph.add('alignment-assessment', {
        'comparison_kind': comparison_kind, 'source_refs': [exact_ref(source)],
        'target_refs': [exact_ref(formal)], 'review': graph.review(source, formal),
        'comparisons': [{'dimension': 'OBJECT', 'source_value': 'Fixture proposition.',
                         'target_value': 'Fixture proposition.', 'relation': 'EQUIVALENT', 'witness_refs': []}],
        'outcome': 'ALIGNED', 'backtranslation_refs': [],
    }, actor='actor:auditor', role='ALIGNMENT_REVIEWER')
    assessment = graph.assessment(target=source, support=alignment,
                                  axis='formal_alignment', method='FORMAL_ALIGNMENT')
    return source, attempt, alignment, assessment


@pytest.mark.parametrize('comparison_kind', ['SOURCE_TO_FORMAL', 'MATH_TO_FORMAL'])
@pytest.mark.parametrize('failed_check', [False, True])
def test_faithful_formal_statement_alignment_does_not_require_proof_success(bundle, comparison_kind, failed_check):
    graph = FixtureGraph(bundle)
    formal_statement(graph, comparison_kind=comparison_kind, failed_check=failed_check)
    require_control(graph)


def test_failed_kernel_check_can_be_preserved_with_alignment_evidence(bundle):
    graph = FixtureGraph(bundle)
    _, _, alignment, assessment = formal_statement(graph, comparison_kind='SOURCE_TO_FORMAL', failed_check=True)
    require_control(graph)
    check_ref = alignment['payload']['target_refs'][0]

    def preserve_check(record):
        if record['record_id'] == assessment['record_id']:
            record['payload']['support_refs'].append(check_ref)
            record['input_refs'].append(check_ref)
            record['producer']['visible_input_refs'].append(check_ref)

    require_control(graph, reseal(graph.records, preserve_check))


def test_source_argument_alignment_cannot_support_formal_axis(bundle):
    graph = FixtureGraph(bundle)
    _, node, _, _ = graph.argument()
    alignment = graph.add('alignment-assessment', {
        'comparison_kind': 'SOURCE_TO_ARGUMENT', 'source_refs': [exact_ref(graph.claim)],
        'target_refs': [exact_ref(node)], 'review': graph.review(graph.claim, node),
        'comparisons': [{'dimension': 'OBJECT', 'source_value': 'same', 'target_value': 'same',
                         'relation': 'EQUIVALENT', 'witness_refs': []}],
        'outcome': 'ALIGNED', 'backtranslation_refs': [],
    }, actor='actor:reviewer', role='ALIGNMENT_REVIEWER')
    require_control(graph)
    graph.assessment(support=alignment, axis='formal_alignment', method='FORMAL_ALIGNMENT')
    result = report(graph)
    assert not result.valid and result.authority_checked and result.byte_artifacts_checked
    assert {issue.code for issue in result.issues} == {'EVIDENCE_TARGET_MISMATCH'}

    def disguise(record):
        if record['record_id'] == alignment['record_id']:
            record['payload']['comparison_kind'] = 'SOURCE_TO_FORMAL'

    result = report(graph, reseal(graph.records, disguise))
    assert not result.valid and result.authority_checked and result.byte_artifacts_checked
    assert {issue.code for issue in result.issues} == {'ALIGNMENT_FORMAL_ENDPOINT', 'ALIGNMENT_FORMAL_TARGET'}


def test_formal_alignment_requires_output_artifacts_even_when_generation_failed(bundle):
    graph = FixtureGraph(bundle)
    _, attempt, _, _ = formal_statement(graph, comparison_kind='SOURCE_TO_FORMAL')
    require_control(graph)

    def remove_output(record):
        if record['record_id'] == attempt['record_id']:
            record['payload'].update(artifacts=[], outcome='FAILED')

    result = report(graph, reseal(graph.records, remove_output))
    assert not result.valid and result.authority_checked and result.byte_artifacts_checked
    assert {issue.code for issue in result.issues} == {'ALIGNMENT_FORMAL_ARTIFACT'}


def test_unknown_alignment_can_honestly_retain_a_failed_attempt_without_output(bundle):
    graph = FixtureGraph(bundle)
    _, attempt, alignment, assessment = formal_statement(graph, comparison_kind='SOURCE_TO_FORMAL')
    require_control(graph)

    def unknown(record):
        if record['record_id'] == attempt['record_id']:
            record['payload'].update(artifacts=[], outcome='FAILED')
        if record['record_id'] == alignment['record_id']:
            record['payload']['outcome'] = 'UNKNOWN'
        if record['record_id'] == assessment['record_id']:
            record['payload']['result'] = 'INCONCLUSIVE'

    require_control(graph, reseal(graph.records, unknown))


def test_math_alignment_rejects_source_claim_disguised_as_math(bundle):
    graph = FixtureGraph(bundle)
    _, _, alignment, _ = formal_statement(graph, comparison_kind='SOURCE_TO_FORMAL')
    require_control(graph)

    def wrong_kind(record):
        if record['record_id'] == alignment['record_id']:
            record['payload']['comparison_kind'] = 'MATH_TO_FORMAL'

    result = report(graph, reseal(graph.records, wrong_kind))
    assert not result.valid and result.authority_checked and result.byte_artifacts_checked
    assert {issue.code for issue in result.issues} == {'ALIGNMENT_ENDPOINT', 'ALIGNMENT_FORMAL_TARGET'}


@pytest.mark.parametrize('outcome', ['UNKNOWN', 'MISALIGNED'])
def test_unknown_or_misaligned_evidence_cannot_be_upgraded_to_partial_support(bundle, outcome):
    graph = FixtureGraph(bundle)
    _, _, alignment, assessment = formal_statement(graph, comparison_kind='SOURCE_TO_FORMAL')
    require_control(graph)

    def partial(record):
        if record['record_id'] == alignment['record_id']:
            record['payload']['outcome'] = 'PARTIAL'
        if record['record_id'] == assessment['record_id']:
            record['payload']['result'] = 'PARTIALLY_SUPPORTED'

    partial_records = reseal(graph.records, partial)
    require_control(graph, partial_records)

    def unsupported(record):
        if record['record_id'] == alignment['record_id']:
            record['payload']['outcome'] = outcome

    result = report(graph, reseal(partial_records, unsupported))
    assert not result.valid and result.authority_checked and result.byte_artifacts_checked
    assert {issue.code for issue in result.issues} == {'FAILED_EVIDENCE'}
