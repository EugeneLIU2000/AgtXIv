"""Real retained inputs + adversarial mutations in temporary run directories only."""
import copy
import importlib.util
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('claim_handoff', HERE / 'handoff.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix='agtxiv-handoff-tests-')
        cls.seed = Path(cls.workspace.name) / 'seed'
        h.prepare(cls.seed)
        cls.contracts = h.Contracts()
        with h.database(cls.seed) as db:
            cls.task, cls.manifest = h.load(db, cls.contracts)
        cls.records, cls.artifacts = h.checked_inputs(cls.seed, cls.task, cls.manifest, cls.contracts)

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.workspace.name)
        self.directory = Path(self.temp.name)
        shutil.copyfile(self.seed / 'handoff.sqlite', self.directory / 'handoff.sqlite')

    def tearDown(self):
        self.temp.cleanup()

    def outputs(self, result):
        with h.database(self.directory) as db:
            return {ref['artifact_id'].rsplit(':', 1)[-1]: h.parse(db.execute(
                'SELECT data FROM handoff_outputs WHERE artifact_id=?', (ref['artifact_id'],)).fetchone()[0])
                for ref in result['artifacts']}

    def test_real_handoff_delivers_two_anchored_citation_leads(self):
        result = h.run(self.directory)
        self.contracts.result(self.task, result)
        self.assertEqual(result['outcome'], 'DELIVERED')
        outputs = self.outputs(result)
        draft, findings = outputs['search-draft.json'], outputs['findings.json']
        self.assertEqual({f['citation_key'] for f in findings['findings']},
                         {'Leone/Stab_Renyi/2022', 'Leone/Stab_Renyi_monotone/2024'})
        by_id = {a.artifact_id: a.data for a in self.artifacts}
        for found in findings['findings']:
            self.assertEqual(len(found['bibliography_matches']), 1)
            for match in found['bibliography_matches']:
                raw = by_id[match['artifact_ref']['artifact_id']][match['byte_start']:match['byte_end']]
                self.assertEqual(h.digest(raw), match['slice_sha256'])
                self.assertEqual(raw.decode(), match['raw_text'])
        self.assertFalse(draft['records'])
        self.assertFalse(findings['mathematical_dependency_established'])
        self.assertFalse(findings['remote_retrieval_performed'])

    def test_old_self_review_blocker_and_unknown_alpha_are_preserved(self):
        self.assertEqual(self.manifest['original_issue_counts'], {'SELF_REVIEW': 82})
        self.assertFalse(self.manifest['original_recordset_valid'])
        self.assertEqual(self.manifest['selected_record_count'], 7)
        self.assertFalse(self.manifest['whole_paper_delivery_accepted'])
        findings = self.outputs(h.run(self.directory))['findings.json']
        target = next(r for r in self.records if h.exact_ref(r) == h.DEFAULT_CLAIM)
        self.assertEqual(findings['target_payload_unchanged'], target['payload'])
        self.assertIn('not stated', target['payload']['quantifiers'][1]['domain'])

    def test_business_and_runtime_records_stay_separate(self):
        h.run(self.directory)
        with h.database(self.directory) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0], 7)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM runtime_tasks').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM runtime_attempts').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM handoff_outputs').fetchone()[0], 2)

    def test_visible_input_gate_excludes_images_and_archive(self):
        def inspect(task, records, artifacts):
            self.assertEqual([h.exact_ref(r) for r in records], task['input_refs'])
            self.assertEqual([a.reference() for a in artifacts], task['input_artifacts'])
            self.assertEqual(len(artifacts), 3)
            self.assertFalse(any(a.media_type in {'image/png', 'application/pdf', 'application/gzip'} for a in artifacts))
            return original(task, records, artifacts)
        original = h.scan
        with patch.object(h, 'scan', side_effect=inspect):
            self.assertEqual(h.run(self.directory)['outcome'], 'DELIVERED')

    def test_readback_does_not_rerun_handler(self):
        first = h.run(self.directory)
        with patch.object(h, 'scan', side_effect=AssertionError('must not run')):
            self.assertEqual(h.run(self.directory), first)
        self.assertEqual(h.status(self.directory)['attempts'], 1)

    def test_restart_reads_only_frozen_store_not_original_files(self):
        original = h.read_bytes
        def read(path):
            self.assertNotIn('Reference/', str(path))
            self.assertNotIn('/example/', str(path))
            return original(path)
        with patch.object(h, 'read_bytes', side_effect=read):
            self.assertEqual(h.run(self.directory)['outcome'], 'DELIVERED')

    def test_interrupted_attempt_is_retained_then_bounded_retry_runs(self):
        with patch.object(h, 'scan', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            h.run(self.directory)
        self.assertEqual(h.status(self.directory)['state'], 'RUNNING')
        self.assertEqual(h.run(self.directory)['outcome'], 'DELIVERED')
        status = h.status(self.directory)
        self.assertEqual(status['attempts'], 2)
        self.assertEqual([e['state'] for e in status['events']], ['READY', 'RUNNING', 'FAILED', 'RUNNING', 'DELIVERED'])

    def test_repeated_failures_exhaust_budget_without_new_attempt(self):
        with patch.object(h, 'scan', side_effect=ValueError('synthetic test failure')):
            for _ in range(2):
                self.assertEqual(h.run(self.directory)['outcome'], 'FAILED')
        with self.assertRaisesRegex(h.InterfaceError, 'budget exhausted'):
            h.run(self.directory)
        self.assertEqual(h.status(self.directory)['attempts'], 2)

    def test_elapsed_budget_cannot_deliver_success(self):
        with patch.object(h.time, 'monotonic', side_effect=[0, 31]):
            result = h.run(self.directory)
        self.assertEqual(result['outcome'], 'FAILED')
        self.assertEqual(result['artifacts'], [])
        self.assertIn('elapsed-time budget', result['open_items'][0])

    def test_output_and_receipt_commit_atomically(self):
        original = h.event
        def fail(db, task, attempt, state, payload):
            if state == 'DELIVERED':
                raise h.InterfaceError('synthetic interrupted commit')
            return original(db, task, attempt, state, payload)
        with patch.object(h, 'event', side_effect=fail), self.assertRaises(h.InterfaceError):
            h.run(self.directory)
        with h.database(self.directory) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM handoff_outputs').fetchone()[0], 0)
        self.assertEqual(h.status(self.directory)['state'], 'RUNNING')
        self.assertEqual(h.run(self.directory)['outcome'], 'DELIVERED')

    def test_local_host_lock_prevents_second_worker(self):
        with h.locked(self.directory), self.assertRaisesRegex(h.InterfaceError, 'Another local host'):
            h.run(self.directory)

    def test_schema_or_handler_drift_refuses_resume(self):
        with patch.object(h, 'pins', return_value={}), self.assertRaisesRegex(h.InterfaceError, 'drift'):
            h.run(self.directory)
        self.assertEqual(h.status(self.directory)['attempts'], 0)

    def test_unknown_or_stale_ref_is_rejected(self):
        for field, value in [('record_id', 'math:missing'), ('content_hash', 'sha256:' + '0' * 64), ('revision', True)]:
            target = dict(h.DEFAULT_CLAIM, **{field: value})
            with self.subTest(field=field), self.assertRaises((h.InterfaceError, h.ContractError)):
                h.closure(self.records, target)

    def test_duplicate_identity_and_missing_closure_are_rejected(self):
        with self.assertRaisesRegex(h.InterfaceError, 'Duplicate'):
            h.closure(self.records + [self.records[0]], h.DEFAULT_CLAIM)
        with self.assertRaisesRegex(h.InterfaceError, 'Missing'):
            h.closure([r for r in self.records if h.short_type(r) != 'definition'], h.DEFAULT_CLAIM)

    def test_corrupt_input_bytes_rejected_before_handler(self):
        with h.database(self.directory) as db:
            db.execute('DROP TRIGGER artifacts_no_update')  # Synthetic hostile-host mutation.
            db.execute("UPDATE artifacts SET data=? WHERE artifact_id='artifact:pauli-spectrum-tex'", (b'corrupt',))
        with patch.object(h, 'scan') as handler, self.assertRaises(h.ContractError):
            h.run(self.directory)
        handler.assert_not_called()

    def test_corrupt_output_cannot_be_replayed_as_success(self):
        h.run(self.directory)
        with h.database(self.directory) as db:
            db.execute('DROP TRIGGER handoff_outputs_no_update')
            db.execute('UPDATE handoff_outputs SET data=?', (b'{}',))
        with self.assertRaisesRegex(h.InterfaceError, 'output hash'):
            h.run(self.directory)

    def test_prepare_failure_never_publishes_half_registered_database(self):
        destination = self.directory / 'new-run'
        with patch.object(h, 'event', side_effect=h.InterfaceError('synthetic registration failure')):
            with self.assertRaises(h.InterfaceError):
                h.prepare(destination)
        self.assertFalse((destination / 'handoff.sqlite').exists())

    def test_running_state_cannot_export_a_stale_final_receipt(self):
        with patch.object(h, 'scan', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            h.run(self.directory)
        with self.assertRaisesRegex(h.InterfaceError, 'terminal receipt'):
            h.status(self.directory, export=True)

    def test_sql_immutable_task_and_output(self):
        h.run(self.directory)
        with h.database(self.directory) as db:
            for sql in ['UPDATE runtime_tasks SET task_ref_json="{}"', 'DELETE FROM handoff_outputs']:
                with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                    db.execute(sql)

    def test_unavailable_target_in_draft_is_failure(self):
        output = copy.deepcopy(h.scan(self.task, self.records, self.artifacts))
        output['search-draft.json']['search_requests'][0]['target_ref']['record_id'] = 'math:invisible'
        with patch.object(h, 'scan', return_value=output):
            self.assertEqual(h.run(self.directory)['outcome'], 'FAILED')

    def test_unknown_draft_fields_are_rejected(self):
        output = h.scan(self.task, self.records, self.artifacts)
        output['search-draft.json']['verified'] = True
        with patch.object(h, 'scan', return_value=output):
            self.assertEqual(h.run(self.directory)['outcome'], 'FAILED')

    def test_handler_cannot_change_the_host_task(self):
        original = h.scan
        def mutated(task, records, artifacts):
            task['target_refs'][0]['record_id'] = 'math:invisible'
            return original(task, records, artifacts)
        with patch.object(h, 'scan', side_effect=mutated):
            result = h.run(self.directory)
        self.assertEqual(result['outcome'], 'FAILED')
        self.assertEqual(result['execution']['visible_input_refs'], self.task['input_refs'])
        with h.database(self.directory) as db:
            task, _ = h.load(db, self.contracts)
        self.assertEqual(task, self.task)

    def test_same_prepare_is_idempotent_and_different_target_conflicts(self):
        self.assertEqual(h.prepare(self.directory)['attempts'], 0)
        all_records = h.read_json(h.DEFAULT_EXAMPLE / 'records.json')
        other = next(r for r in all_records if r['record_id'].endswith('/A07-conclusion-2'))
        with self.assertRaisesRegex(h.InterfaceError, 'different fixed inputs'):
            h.prepare(self.directory, target=h.exact_ref(other))
        self.assertEqual(h.status(self.directory)['attempts'], 0)

    def test_export_preserves_artifact_bytes_and_does_not_overwrite(self):
        result = h.run(self.directory)
        h.status(self.directory, export=True)
        h.status(self.directory, export=True)
        for ref in result['artifacts']:
            name = ref['artifact_id'].rsplit(':', 1)[-1]
            self.assertEqual(h.digest((self.directory / name).read_bytes()), ref['sha256'])
        (self.directory / 'findings.json').write_bytes(b'conflict')
        with self.assertRaisesRegex(h.InterfaceError, 'different bytes'):
            h.status(self.directory, export=True)

    def test_safe_path_rejects_escape_and_symlink(self):
        for value in ['/etc/passwd', '../outside']:
            with self.assertRaises(h.InterfaceError):
                h.safe_member(self.directory, value)
        (self.directory / 'link').symlink_to(self.seed, target_is_directory=True)
        with self.assertRaises(h.InterfaceError):
            h.safe_member(self.directory, 'link/handoff.sqlite')

    def test_parser_preserves_nested_braces_comments_and_offsets(self):
        raw = b'% @article{fake, title={bad}}\n@article{real, title={A {nested} title}, note={x\\{y}}\n'
        entries = h.bib_entries(raw)
        self.assertEqual(len(entries), 1)
        key, start, end = entries[0]
        self.assertEqual(key, 'real')
        self.assertTrue(raw[start:end].startswith(b'@article{real,'))
        with self.assertRaisesRegex(h.InterfaceError, 'Unbalanced'):
            h.bib_entries(b'@article{bad,title={unfinished}')

    def test_no_citation_does_not_become_no_prior_art(self):
        records, artifacts = copy.deepcopy(self.records), list(self.artifacts)
        for record in records:
            if h.short_type(record) == 'source-span':
                p = record['payload']
                p['byte_start'], p['byte_end'], p['span_sha256'] = 0, 4, h.digest(b'Test')
        artifacts = [h.SuppliedArtifact(a.artifact_id, a.media_type, b'Test')
                     if a.artifact_id == 'artifact:pauli-spectrum-tex' else a for a in artifacts]
        draft = h.scan(self.task, records, artifacts)['search-draft.json']
        self.assertEqual(draft['search_requests'], [])
        self.assertTrue(any('NOT evidence' in gap for gap in draft['open_items']))

    def test_duplicate_bibliography_key_remains_ambiguous(self):
        item = next(a for a in self.artifacts if a.artifact_id == 'artifact:draft-ref-bib')
        duplicate = h.SuppliedArtifact('artifact:synthetic-duplicate-bib', item.media_type, item.data)
        output = h.scan(self.task, self.records, self.artifacts + [duplicate])
        self.assertTrue(all(len(f['bibliography_matches']) == 2 for f in output['findings.json']['findings']))
        self.assertTrue(any('multiple local' in gap for gap in output['search-draft.json']['open_items']))


if __name__ == '__main__':
    unittest.main()
