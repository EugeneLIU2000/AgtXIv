"""Independent adversarial package boundaries; synthetic, offline, Python only."""
from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import subprocess
import sys

import pytest

from test_candidates import ROOT, bundle, inspection, proposal
from test_contracts import FixtureGraph
from test_intake import caller_metadata, source_tree
from agtxiv_v3.candidates import (
    CandidatePackage, build_candidate_package, build_interpretation_records,
    persist_candidate_package, query_candidate_package,
)
from agtxiv_v3.contracts import ContractError, SuppliedArtifact, canonical, exact_ref, kind
from agtxiv_v3.intake import build_source_candidates, inspect_source_directory
from agtxiv_v3.source import SourceError
from agtxiv_v3.storage import LocalStore


def reseal_package(package, body):
    # Independently rehash the enclosing artifact: rejection must be semantic,
    # not merely detection of an obsolete outer checksum.
    data = canonical(body)
    media = 'application/json'
    identity = hashlib.sha256(media.encode() + b'\0' + data).hexdigest()
    artifact = SuppliedArtifact('artifact:candidate-' + identity, media, data)
    artifacts = tuple(a for a in package.artifacts if a.artifact_id != package.artifact.artifact_id)
    return CandidatePackage(artifact, (*artifacts, artifact), package.records)


def counts(store):
    return tuple(store._db.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                 for table in ('records', 'artifacts', 'candidate_heads'))


@pytest.fixture
def record_case(bundle, inspection):
    graph = FixtureGraph(bundle)
    metadata = caller_metadata(bundle)
    metadata['policy_ref'] = exact_ref(graph.policy)
    source = build_source_candidates(inspection, **metadata)
    proposals = [proposal(inspection)]
    records = build_interpretation_records(
        inspection, proposals, source_snapshot=source.source_snapshot, bundle=bundle,
        producer=metadata['producer'], policy_ref=metadata['policy_ref'],
        created_at=metadata['created_at'])
    package = build_candidate_package(
        inspection, proposals=proposals,
        records=(source.source_snapshot, source.paper_structure, *records),
        supporting_artifacts=source.artifacts)
    return package, graph.policy


@pytest.mark.parametrize('mutation', ['total_bytes', 'file_hash', 'file_path', 'span_hash',
                                     'span_end', 'duplicate_path', 'omitted_generated'])
@pytest.mark.parametrize('boundary', ['persist', 'query'])
def test_rehashed_manifest_mutations_fail_closed(bundle, inspection, mutation, boundary):
    package = build_candidate_package(inspection)
    body = package.report()
    if mutation == 'total_bytes':
        body['total_bytes'] += 1
    elif mutation == 'file_hash':
        body['files'][0]['sha256'] = 'sha256:' + '0' * 64
    elif mutation == 'file_path':
        body['files'][0]['path'] = '../outside.tex'
    elif mutation == 'span_hash':
        body['segments'][0]['sha256'] = '0' * 64
    elif mutation == 'span_end':
        body['segments'][0]['end_byte'] += 1
    elif mutation == 'duplicate_path':
        body['files'].append(copy.deepcopy(body['files'][0]))
    else:
        body['files'] = [f for f in body['files'] if not f['path'].startswith('build/')]
        # Keep the original bound count/byte denominator. A wholly different,
        # self-consistent capture cannot be detected without an external pin.
    bad = reseal_package(package, body)
    with LocalStore(':memory:', bundle) as store:
        if boundary == 'query':
            assert store.ingest((), bad.artifacts).valid
        before = counts(store)
        with pytest.raises((SourceError, ContractError)):
            if boundary == 'persist':
                persist_candidate_package(store, bad)
            else:
                query_candidate_package(store, bad.reference())
        assert counts(store) == before


@pytest.mark.parametrize('field,value', [('path', 'absent.tex'), ('start_byte', True),
                                        ('end_byte', 1), ('sha256', '0' * 64)])
def test_anchor_mutations_reject_before_packaging(inspection, field, value):
    candidate = proposal(inspection)
    candidate['anchors'][0][field] = value
    with pytest.raises(SourceError):
        build_candidate_package(inspection, proposals=[candidate])


def test_generated_projection_preserves_proposal_semantics(bundle, inspection, record_case):
    package, _ = record_case
    proposed = proposal(inspection)
    node = next(r for r in package.records if kind(r) == 'argument-node')
    frontier = next(r for r in package.records if kind(r) == 'frontier-item')
    span = next(r for r in package.records if kind(r) == 'source-span')
    assert proposed['interpretation'] in node['payload']['statement']
    assert all(c in node['payload']['statement'] for c in proposed['conditions'])
    assert proposed['unknowns'][0] in frontier['payload']['statement']
    assert frontier['payload']['target_refs'] == [exact_ref(node)]
    assert frontier['payload']['state'] == 'OPEN'
    assert node['payload']['source_span_refs'] == [exact_ref(span)]
    anchor = proposed['anchors'][0]
    assert span['payload']['byte_start'] == anchor['start_byte']
    assert span['payload']['byte_end'] == anchor['end_byte']
    assert span['payload']['span_sha256'] == 'sha256:' + anchor['sha256']
    source = next(r for r in package.records if kind(r) == 'source-snapshot')
    unit = next(u for u in source['payload']['units'] if u['relative_path'] == anchor['path'])
    assert span['payload']['source_ref'] == exact_ref(source)
    assert span['payload']['artifact'] == unit['artifact']


def test_generated_projection_rejects_mismatched_source_denominator(bundle, inspection, record_case):
    package, policy = record_case
    source = next(r for r in package.records if kind(r) == 'source-snapshot')
    smaller = replace(inspection, sources={p: b for p, b in inspection.sources.items()
                                          if not p.startswith('build/')})
    with pytest.raises(SourceError):
        build_interpretation_records(smaller, [proposal(inspection)],
            source_snapshot=source, bundle=bundle, producer=source['producer'],
            policy_ref=exact_ref(policy), created_at=source['created_at'])


@pytest.mark.parametrize('duplicate', ['artifact', 'conflicting_artifact', 'record'])
def test_duplicate_supplied_identities_cannot_be_hidden_by_pending_maps(bundle, record_case, duplicate):
    package, policy = record_case
    if duplicate == 'record':
        bad = replace(package, records=(*package.records, package.records[0]))
    else:
        item = package.artifacts[0]
        if duplicate == 'conflicting_artifact':
            item = SuppliedArtifact(item.artifact_id, item.media_type, b'conflicting bytes')
        bad = replace(package, artifacts=(item, *package.artifacts))
    with LocalStore(':memory:', bundle) as store:
        with pytest.raises((SourceError, ContractError)):
            persist_candidate_package(store, bad, context_records=[policy])
        assert counts(store) == (0, 0, 0)


def test_historical_reader_rejects_duplicate_record_members(bundle, inspection, record_case):
    package, policy = record_case
    with LocalStore(':memory:', bundle) as store:
        assert persist_candidate_package(store, package, context_records=[policy]).valid
        try:
            bad = build_candidate_package(inspection, proposals=[proposal(inspection)],
                records=(*package.records, package.records[0]),
                supporting_artifacts=tuple(a for a in package.artifacts
                                           if a.reference() in package.report()['supporting_artifacts']))
        except (SourceError, ContractError):
            return  # Rejecting duplicate membership at construction is valid.
        # Generic artifact ingestion is legitimate; query must independently
        # validate a coherent package, not rely on its own persistence wrapper.
        assert store.ingest((), [bad.artifact]).valid
        with pytest.raises((SourceError, ContractError)):
            query_candidate_package(store, bad.reference())


@pytest.mark.parametrize('self_cycle', [True, False])
def test_cyclic_proposals_fail_closed_or_expose_specific_potential_only_unknown(
        bundle, inspection, self_cycle):
    first = proposal(inspection)
    first['dependencies'] = ['candidate' if self_cycle else 'second']
    proposals = [first]
    if not self_cycle:
        second = copy.deepcopy(first)
        second.update(id='second', dependencies=['candidate'])
        proposals.append(second)
    with LocalStore(':memory:', bundle) as store:
        try:
            package = build_candidate_package(inspection, proposals=proposals)
            persist_candidate_package(store, package)
        except (SourceError, ContractError):
            assert counts(store) == (0, 0, 0)
            return
        result = query_candidate_package(store, package.reference())
        # Generic "unverified" labels do not disclose circular support.
        questions = result['open_questions'] + [q for p in result['package']['proposals'] for q in p['unknowns']]
        assert any(('cycl' in q.lower() or 'circular' in q.lower()) and
                   ('potential' in q.lower() or 'unknown' in q.lower() or 'unverified' in q.lower())
                   for q in questions), 'Accepted dependency cycle has no explicit potential-only/unknown warning'
        assert all(p['verification'] == 'UNVERIFIED' for p in result['package']['proposals'])
        assert result['authority_checked'] is False


def test_reopen_retains_exact_records_unknowns_and_no_admission(tmp_path, bundle, record_case):
    package, policy = record_case
    database = tmp_path / 'history.sqlite'
    body = package.report()
    body['open_questions'].append('Later capture does not resolve the earlier unknown.')
    later = reseal_package(package, body)
    with LocalStore(database, bundle) as store:
        assert persist_candidate_package(store, package, context_records=[policy]).valid
        assert persist_candidate_package(store, later, context_records=[policy]).valid
        before = counts(store)
    with LocalStore(database, bundle, readonly=True) as store:
        for expected in (later, package):
            result = query_candidate_package(store, expected.reference())
            assert result['package'] == expected.report()
            assert sorted(result['records'], key=canonical) == sorted(expected.records, key=canonical)
            assert result['open_questions'] == expected.report()['open_questions']
            assert {kind(r) for r in result['records']} == {
                'source-snapshot', 'paper-structure', 'source-span', 'argument-node', 'frontier-item'}
            frontiers = [r['payload'] for r in result['records'] if kind(r) == 'frontier-item']
            assert frontiers and all(f['state'] == 'OPEN' and not f['resolution_refs'] for f in frontiers)
            assert result['authority_checked'] is False
            assert result['canonical_mutation'] == 'FORBIDDEN'
            assert result['scientific_assessment'] == 'NOT_PERFORMED'
            for item in expected.artifacts:
                assert store.artifact(item.reference()) == item.data
        assert counts(store) == before
        assert before[2] == 0


def test_generated_files_are_retained_and_cli_cannot_add_output_to_capture(tmp_path, bundle):
    files = {'main.tex': b'Comment only\r\n', 'build/main.aux': b'aux\x00',
             'nested/build/run.log': b'log', '.cache/generated.json': b'{}',
             'main.bbl': b'bibliography', 'build/empty.tex': b''}
    root = source_tree(tmp_path, files)
    inspection = inspect_source_directory(root, 'main.tex')
    package = build_candidate_package(inspection)
    assert package.report()['file_count'] == len(files)
    assert package.report()['total_bytes'] == sum(map(len, files.values()))
    with LocalStore(':memory:', bundle) as store:
        assert persist_candidate_package(store, package).valid
        for item in query_candidate_package(store, package.reference())['package']['files']:
            assert store.artifact(item['artifact']) == files[item['path']]
    for flag in ('--database', '--output'):
        target = root / 'build' / 'new-output'
        result = subprocess.run([sys.executable, str(ROOT / 'tools/inspect_v3_candidates.py'),
            'build', str(root), '--main', 'main.tex', flag, str(target)],
            capture_output=True, timeout=15)
        assert result.returncode == 2, result.stderr
        assert not target.exists()
    assert {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()} == files
