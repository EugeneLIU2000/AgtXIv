"""Actual process-exit recovery on disposable SQLite stores, never user data.

These deterministic synthetic probes bypass Python cleanup with os._exit.
They establish local SQLite restart behavior, not power-loss durability,
scientific approval, authenticated storage or production crash guarantees.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from test_contracts import FixtureGraph, bundle, mutate
from test_storage import snapshot
from agtxiv_v3.contracts import SuppliedArtifact, content_hash, exact_ref
from agtxiv_v3.storage import LocalStore, StorageError

ROOT = Path(__file__).resolve().parents[2]
EXIT_DURING_TRANSACTION = 79

# The child receives only a tmp_path database and fabricated records over stdin.
# Its marker is emitted only after confirming SQL inserts and an open transaction.
CHILD = r'''
import base64
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / 'src'))
from agtxiv_v3.contracts import SchemaBundle, SuppliedArtifact, exact_ref
from agtxiv_v3.storage import LocalStore

request = json.load(sys.stdin)
artifacts = [SuppliedArtifact(a['artifact_id'], a['media_type'],
                             base64.b64decode(a['data'])) for a in request['artifacts']]

class InterruptedStore(LocalStore):
    def _record_set(self, authority=None):
        assert self._db.in_transaction
        for record in request['records']:
            assert self.resolve(exact_ref(record)) == record
        for artifact in artifacts:
            assert self.artifact(artifact.reference()) == artifact.data
        assert self.candidate_head(request['domain']) == request['expected_head']
        os.write(1, b'INSERTS_VISIBLE_TRANSACTION_OPEN\n')
        os._exit(79)  # No exception, context-manager rollback, or connection close.

store_type = InterruptedStore if sys.argv[3] == 'interrupt' else LocalStore
store = store_type(Path(sys.argv[2]), SchemaBundle())
report = store.ingest(request['records'], artifacts,
                      snapshot_ref=request['snapshot_ref'], expected_head=request['expected_head'])
assert report.valid and report.byte_artifacts_checked and not report.authority_checked
assert not store._db.in_transaction
assert store.candidate_head(request['domain']) == request['snapshot_ref']
os.write(1, b'COMMIT_RETURNED\n')
os._exit(0)  # Even the success control does not rely on orderly Python shutdown.
'''


@pytest.fixture
def recovery_case(tmp_path, bundle):
    graph = FixtureGraph(bundle)
    first = snapshot(graph)
    initial = list(graph.records)
    old_claim = graph.claim
    revised = mutate(old_claim, statement='A second synthetic interpretation, not a scientific finding.')
    revised['revision'] = old_claim['revision'] + 1
    revised['content_hash'] = content_hash(revised)
    second = snapshot(graph, first)
    extra = SuppliedArtifact('artifact:restart-provenance', 'application/octet-stream',
                             b'\x00SYNTHETIC UNVERIFIED\r\n\xff')
    path = tmp_path / 'recovery.sqlite'
    with LocalStore(path, bundle) as store:
        report = store.ingest(initial, graph.artifacts, snapshot_ref=exact_ref(first))
        assert report.valid and report.byte_artifacts_checked
    request = {
        'records': [revised, second],
        'artifacts': [{'artifact_id': extra.artifact_id, 'media_type': extra.media_type,
                       'data': base64.b64encode(extra.data).decode('ascii')}],
        'snapshot_ref': exact_ref(second), 'expected_head': exact_ref(first),
        'domain': first['payload']['domain'],
    }
    return path, graph, initial, first, second, revised, extra, request


def run_child(path, request, mode):
    return subprocess.run(
        [sys.executable, '-c', CHILD, str(ROOT), str(path), mode],
        input=json.dumps(request), text=True, capture_output=True,
        cwd=ROOT, timeout=30, check=False,
    )


def persisted_rows(path):
    # Compare every persisted object, not merely the candidate pointer.
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        return {
            'records': db.execute('SELECT * FROM records ORDER BY record_type, record_id, revision').fetchall(),
            'artifacts': db.execute('SELECT * FROM artifacts ORDER BY artifact_id').fetchall(),
            'heads': db.execute('SELECT * FROM candidate_heads ORDER BY domain').fetchall(),
        }


def test_abrupt_exit_after_inserts_restores_previous_objects_and_head(recovery_case, bundle):
    path, graph, initial, first, second, revised, extra, request = recovery_case
    before = persisted_rows(path)
    process = run_child(path, request, 'interrupt')
    assert process.returncode == EXIT_DURING_TRANSACTION, (process.stdout, process.stderr)
    assert process.stdout == 'INSERTS_VISIBLE_TRANSACTION_OPEN\n'
    assert process.stderr == ''

    # This is the first LocalStore open after the child vanished mid-ingest.
    with LocalStore(path, bundle) as store:
        assert store.candidate_head(request['domain']) == exact_ref(first)
        for original in initial:
            assert store.resolve(exact_ref(original)) == original
        for artifact in graph.artifacts:
            assert store.artifact(artifact.reference()) == artifact.data
        for uncommitted in (revised, second):
            with pytest.raises(StorageError, match='Unknown, mistyped or stale'):
                store.resolve(exact_ref(uncommitted))
        with pytest.raises(StorageError, match='Unknown exact artifact'):
            store.artifact(extra.reference())
    assert persisted_rows(path) == before

    # Identical candidates can subsequently commit: the interruption did not
    # merely hide invalid input, leave locks, or reserve immutable identities.
    retry = run_child(path, request, 'commit')
    assert retry.returncode == 0, (retry.stdout, retry.stderr)
    assert retry.stdout == 'COMMIT_RETURNED\n'
    with LocalStore(path, bundle, readonly=True) as store:
        assert store.candidate_head(request['domain']) == exact_ref(second)
        assert store.resolve(exact_ref(revised)) == revised
        assert store.artifact(extra.reference()) == extra.data


def test_committed_process_exit_preserves_exact_historical_retrieval(recovery_case, bundle):
    path, graph, initial, first, second, revised, extra, request = recovery_case
    process = run_child(path, request, 'commit')
    assert process.returncode == 0, (process.stdout, process.stderr)
    assert process.stdout == 'COMMIT_RETURNED\n'
    assert process.stderr == ''
    before_reads = persisted_rows(path)
    assert len(before_reads['records']) == len(initial) + 2
    assert len(before_reads['artifacts']) == len(graph.artifacts) + 1

    with LocalStore(path, bundle, readonly=True) as store:
        assert store.candidate_head(request['domain']) == exact_ref(second)
        for original in initial:
            assert store.resolve(exact_ref(original)) == original
        assert store.resolve(exact_ref(revised)) == revised
        assert store.resolve(exact_ref(second)) == second
        for artifact in [*graph.artifacts, extra]:
            assert store.artifact(artifact.reference()) == artifact.data
        for historical in (first, second):
            result = store.query(exact_ref(historical))
            assert result['knowledge_ref'] == exact_ref(historical)
            assert result['records'] == [] and result['relations'] == []
            assert result['mode'] == 'PROVISIONAL'
            assert result['canonical_mutation'] == 'FORBIDDEN'
            assert result['artifact_bytes_checked'] and not result['authority_checked']
        stale = {**exact_ref(revised), 'content_hash': graph.claim['content_hash']}
        with pytest.raises(StorageError, match='Unknown, mistyped or stale'):
            store.resolve(stale)
    assert persisted_rows(path) == before_reads
