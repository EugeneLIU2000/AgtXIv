"""A query selecting a limiting relation must retain its opposing endpoints."""
from __future__ import annotations

import pytest

from test_contracts import FixtureGraph, mutate
from test_contract_regressions import admit, released_control, require_control, report, reseal
from agtxiv_v3.contracts import SchemaBundle, content_hash, exact_ref


@pytest.mark.parametrize('relation_kind', ['CONFLICTING', 'INCOMPARABLE', 'CORRECTS', 'QUALIFIES', 'REFUTES'])
@pytest.mark.parametrize('selection', ['relation_refs', 'returned_refs'])
def test_relation_selected_query_receipt_cannot_hide_both_endpoints(relation_kind, selection):
    graph = FixtureGraph(SchemaBundle())
    other = graph.claim_record('Synthetic opposing candidate.')
    relation = graph.add('relation-assessment', {
        'source_ref': exact_ref(graph.claim), 'target_ref': exact_ref(other), 'relation': relation_kind,
        'review': graph.review(graph.claim, other), 'comparisons': [{
            'dimension': 'OBJECT', 'source_value': 'A', 'target_value': 'B',
            'relation': 'UNKNOWN', 'witness_refs': []}], 'outcome': 'PROPOSED', 'witness_refs': [],
    }, actor='actor:reviewer', role='SCIENTIFIC_REVIEWER')
    assessment = mutate(graph.assessment(target=relation), result='INCONCLUSIVE')
    assessment['producer']['principal_id'] = 'actor:producer'
    assessment['content_hash'] = content_hash(assessment)
    graph.records[-1] = assessment
    control = released_control(graph)
    decision = admit(graph, control['release'], control['genesis'], relation, assessment)
    snapshot = graph.add('knowledge-snapshot', {
        'domain': 'Synthetic', 'predecessor_ref': exact_ref(control['genesis']),
        'entry_refs': [exact_ref(relation)], 'relation_refs': [exact_ref(relation)],
        'release_refs': [exact_ref(control['release'])], 'admission_refs': [exact_ref(decision)],
    }, actor='actor:knowledge', role='KNOWLEDGE_SERVICE')
    receipt = graph.add('query-receipt', {
        'query': 'Inspect this limiting relation.', 'knowledge_ref': exact_ref(snapshot),
        'mode': 'PROVISIONAL', 'returned_refs': [exact_ref(relation), exact_ref(graph.claim), exact_ref(other)],
        'relation_refs': [exact_ref(relation)], 'assertions': [], 'frontier_refs': [],
        'work_request_ref': None, 'canonical_mutation': 'FORBIDDEN',
    })
    require_control(graph)

    def omit_endpoints(record):
        if record['record_id'] == receipt['record_id']:
            record['payload']['returned_refs'] = [exact_ref(relation)] if selection == 'returned_refs' else []
            record['payload']['relation_refs'] = [exact_ref(relation)] if selection == 'relation_refs' else []

    result = report(graph, reseal(graph.records, omit_endpoints))
    assert not result.valid and result.authority_checked and result.byte_artifacts_checked
    assert {issue.code for issue in result.issues} == {'QUERY_CONFLICT_SUPPRESSION'}
