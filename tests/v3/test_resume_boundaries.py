"""Interrupted-build boundary regressions; synthetic, offline and non-executing.

Reuse the V3 contract/capture fixtures. Structural import and obligation
accounting are never scientific approval, authenticated review or admission.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import pytest

from test_contracts import FixtureGraph, bundle
from test_contract_regressions import require_control, reseal
from test_obligations import by_stage, codes, evaluate, source_map
from test_vibefeld import TIME, capture, edit, event, inspect, protocol
from agtxiv_v3.contracts import RecordSet, exact_ref
from agtxiv_v3.vibefeld import (
    CaptureLimits, ImportError as CaptureError, PINNED_COMMIT,
    build_import_candidate, inspect_capture,
)

ROOT = Path(__file__).resolve().parents[2]


def test_resumed_generator_is_byte_idempotent_and_matches_both_published_languages():
    # Import declarations only: do not invoke main() or write generated files.
    spec = importlib.util.spec_from_file_location(
        'resume_schema_generator', ROOT / 'tools/generate_v3_schema_v00.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    first = generator.generate()
    assert first == generator.generate(), 'Repeated generation accumulates mutable rules'
    assert {'SCHEMA.md', 'SCHEMA.zh-CN.md'} <= {path.name for path in first}
    for path, expected in first.items():
        assert path.read_bytes() == expected, f'Interrupted or stale generated output: {path.name}'


@pytest.mark.parametrize('state', ['validated', 'admitted'])
def test_reported_terminal_labels_remain_provenance_in_observed_import(bundle, protocol, state):
    files = capture(validated=state == 'validated')
    if state == 'admitted':
        files['ledger/000003.json'] = json.dumps(event('node_admitted', node_id='1')).encode()

        def admit(graph):
            graph['nodes'][0].update(epistemic_state='admitted', taint_state='self_admitted', closed=True)
            graph['nodes'][0].pop('verifier_ready')
            graph['validation'].update(epistemic_counts={'admitted': 1}, taint_counts={'self_admitted': 1})

        edit(files, 'graph.json', admit)
    observation = inspect(files, protocol)
    assert observation.report()['outcome'] == 'STRUCTURALLY_IMPORTED'
    graph = FixtureGraph(bundle)
    before = list(graph.records)
    candidate, artifacts = build_import_candidate(
        observation, bundle=bundle, record_id='fixture:observed-import',
        producer=graph.claim['producer'], policy_ref=exact_ref(graph.policy),
        created_at=TIME, data_class='OBSERVED')
    store = RecordSet(bundle, graph.records + [candidate], graph.artifacts + list(artifacts))
    result = store.validate()
    assert result.valid, result.issues
    assert result.byte_artifacts_checked and not result.authority_checked
    assert candidate['data_class'] == 'OBSERVED'
    assert candidate['record_type'] == 'agtxiv.v3.upstream-import/0.0.0'
    assert graph.records == before
    assert store.records[:-1] == tuple(before)
    assert len(store.records) == len(before) + 1  # No hidden assessments/admissions.
    retained = json.loads(store.artifact(candidate['payload']['reported_states']))
    assert retained['replayed_state']['nodes']['1']['epistemic_state'] == state
    assert retained['reported_graph']['nodes'][0]['closed'] is True
    assert retained['scientific_assessment'] == 'NOT_PERFORMED'
    assert retained['identity_assurance'] == 'DECLARED_MAP_ONLY'


def test_capture_order_and_relocation_do_not_erase_explicit_workspace_identity(protocol):
    files = capture(validated=True)
    original = inspect(files, protocol)
    reordered = inspect(dict(reversed(list(files.items()))), protocol)
    assert reordered.json_bytes() == original.json_bytes()
    edit(files, 'graph.json', lambda g: g['workspace'].update(id='/relocated/elsewhere'))
    relocated = inspect(files, protocol).report()
    assert relocated['outcome'] == 'STRUCTURALLY_IMPORTED'
    assert relocated['semantic_snapshot_hash'] == original.report()['semantic_snapshot_hash']
    assert relocated['file_manifest'] != original.report()['file_manifest']
    distinct = inspect_capture(files, commit=PINNED_COMMIT, workspace_key='fixture:other', protocol=protocol).report()
    assert distinct['outcome'] == 'STRUCTURALLY_IMPORTED'
    assert distinct['semantic_snapshot_hash'] != relocated['semantic_snapshot_hash']


@pytest.mark.parametrize('boundary', ['max_files', 'max_events', 'max_file_bytes', 'max_total_bytes', 'max_json_depth'])
def test_capture_accepts_exact_budget_and_rejects_one_less(protocol, boundary):
    files = capture()
    # Root depth is zero: graph -> nodes list -> node object -> field is three.
    limits = CaptureLimits(max_files=len(files), max_events=2,
                           max_file_bytes=max(map(len, files.values())),
                           max_total_bytes=sum(map(len, files.values())),
                           max_nodes=1, max_json_depth=3)
    control = inspect(files, protocol, limits=limits).report()
    assert control['outcome'] == 'STRUCTURALLY_IMPORTED', control
    tighter = replace(limits, **{boundary: getattr(limits, boundary) - 1})
    if boundary == 'max_json_depth':
        report = inspect(files, protocol, limits=tighter).report()
        assert report['outcome'] == 'REJECTED'
        assert report['semantic_snapshot_hash'] is None
        assert any('nesting limit' in issue['message'] for issue in report['issues'])
    else:
        with pytest.raises(CaptureError):
            inspect(files, protocol, limits=tighter)


@pytest.mark.parametrize('omitted', ['span', 'plan', 'assessment'])
def test_success_cannot_borrow_required_evidence_from_outside_explicit_universe(bundle, omitted):
    graph = FixtureGraph(bundle)
    dispositions, assessment = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions).valid
    victim = assessment if omitted == 'assessment' else getattr(graph, omitted)
    universe = [exact_ref(r) for r in graph.records if r != victim]
    # All records and bytes still exist in the store: only the ledger cut changes.
    result = evaluate(graph, dispositions, universe=universe)
    assert not result.valid
    assert 'OBLIGATION_OUTSIDE_UNIVERSE' in codes(result)
    assert any(i.code == 'OBLIGATION_OUTSIDE_UNIVERSE' and i.record_id == victim['record_id']
               for i in result.issues)
    assert not result.artifact_checked and not result.authority_checked


def test_explicit_universe_order_is_irrelevant_but_duplicate_members_fail_closed(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    universe = [exact_ref(r) for r in graph.records]
    control = evaluate(graph, dispositions, universe=universe)
    assert control.valid, control.issues
    assert evaluate(graph, dispositions, universe=iter(reversed(universe))) == control
    duplicate = evaluate(graph, dispositions, universe=universe + [exact_ref(graph.scope)])
    assert codes(duplicate) == {'OBLIGATION_UNIVERSE_DUPLICATE'}
    assert duplicate.universe_count == control.universe_count


def test_candidate_mode_still_rejects_completed_claim_without_typed_assessment(bundle):
    graph = FixtureGraph(bundle)
    dispositions, _ = source_map(graph)
    require_control(graph)
    assert evaluate(graph, dispositions, enforce_success=False).valid
    victim = by_stage(graph, dispositions, 'CLAIM')

    def replace_assessment(record):
        if record['record_id'] == victim['record_id']:
            record['payload']['result_refs'] = [exact_ref(graph.span)]

    changed = reseal(graph.records, replace_assessment)
    require_control(graph, changed)
    result = evaluate(graph, dispositions, records=changed, enforce_success=False)
    assert not result.success_enforced
    assert codes(result) == {'OBLIGATION_STAGE_EVIDENCE'}
