"""Offline adversarial orchestration checks; all references are synthetic.

Run: .venv/bin/python -B -m unittest discover -s 'schema v0.1/tests' -v
Only temporary directories and in-memory SQLite are written by these tests.
No scientific proof, authenticated identity, or execution readiness is asserted.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('orchestration_reference', ROOT / 'validate.py')
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)
ERRORS = tuple(getattr(reference, name) for name in ('InterfaceError', 'ContractError')
               if hasattr(reference, name))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def put(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = reference.Contracts()
        cls.workflow = read_json(ROOT / 'examples/workflow.json')

    def pair(self, index=0):
        task = copy.deepcopy(self.workflow['tasks'][index])
        result = copy.deepcopy(next(r for r in self.workflow['results']
                                    if r['task_id'] == task['task_id']))
        self.contracts.result(task, result)  # Positive control before each mutation.
        return task, result

    def test_package_and_example_graph(self):
        report = self.contracts.check_package()
        self.assertEqual(report['schemas'], 5)
        self.assertEqual(report['base_record_families'], 64)
        order = self.contracts.task_graph(self.workflow['tasks'])
        self.assertEqual(set(order), {t['task_id'] for t in self.workflow['tasks']})
        for task in self.workflow['tasks']:
            for dependency in task['depends_on']:
                self.assertLess(order.index(dependency['task_id']), order.index(task['task_id']))
        self.assertFalse(report['scientific_acceptance_checked'])

    def test_all_local_object_types_are_closed(self):
        # Conditional schema fragments refine their enclosing object; they are
        # not standalone object declarations and must not forbid other fields.
        for path in sorted((ROOT / 'schemas').glob('*.json')):
            for node in reference.walk(read_json(path)):
                if node.get('type') == 'object':
                    with self.subTest(schema=path.name, properties=list(node.get('properties', {}))):
                        self.assertIs(node.get('additionalProperties'), False)

    def test_unknown_fields_rejected_at_actual_boundaries(self):
        task, result = self.pair()
        registry = read_json(ROOT / 'agents.json')
        manifest = read_json(ROOT / 'examples/batch/batch.json')
        cases = [('task', task, p) for p in [(), ('limits',), ('input_refs', 0)]]
        cases += [('result', result, p) for p in [(), ('execution',), ('output_refs', 0)]]
        cases += [('agent-registry', registry, p) for p in [(), ('agents', 0), ('agents', 0, 'operations', 0)]]
        cases += [('archive-batch', manifest, p) for p in [(), ('files', 0), ('files', 0, 'ref')]]
        for name, good, path in cases:
            with self.subTest(schema=name, path=path):
                self.contracts.shape(name, good)
                bad = copy.deepcopy(good)
                put(bad, path + ('scientific_passed',), True)
                with self.assertRaises(ERRORS):
                    self.contracts.shape(name, bad)

    def test_task_operation_targets_capabilities_and_output(self):
        good, _ = self.pair()
        cases = [(('agent',), 'reader'), (('operation',), 'formalization.unknown'),
                 (('expected_record_types',), ['release-certificate']),
                 (('capabilities',), ['release.certify']),
                 (('target_refs', 0, 'content_hash'), 'sha256:' + 'a' * 64),
                 (('limits', 'no_progress_limit'), good['limits']['max_attempts'] + 1),
                 (('limits', 'max_attempts'), True), (('input_artifacts',), 'not-an-array')]
        for path, replacement in cases:
            with self.subTest(path=path):
                bad = copy.deepcopy(good)
                put(bad, path, replacement)
                with self.assertRaises(ERRORS):
                    self.contracts.task(bad)
        aid, operation = self.contracts.operations[good['operation']]
        good['capabilities'] = operation['capabilities'][:1]
        self.contracts.task(good)

    def test_identifiers_types_and_hash_reject_trailing_newline(self):
        task, _ = self.pair()
        for path in [('task_id',), ('operation',), ('expected_record_types', 0)]:
            with self.subTest(path=path):
                bad = copy.deepcopy(task)
                value = bad
                for key in path:
                    value = value[key]
                put(bad, path, value + '\n')
                # Shape alone must reject, even before operation lookup.
                with self.assertRaises(ERRORS):
                    self.contracts.shape('task', bad)
        manifest = read_json(ROOT / 'examples/batch/batch.json')
        self.contracts.shape('archive-batch', manifest)
        for value in [manifest['base_bundle_hash'] + '\n', 'sha256:' + '1' * 63,
                      'sha256:' + '1' * 65]:
            with self.subTest(hash=value):
                bad = copy.deepcopy(manifest)
                bad['base_bundle_hash'] = value
                with self.assertRaises(ERRORS):
                    self.contracts.shape('archive-batch', bad)

    def test_required_task_and_execution_fields(self):
        task, result = self.pair()
        for field in ('brief', 'target_refs', 'input_artifacts'):
            with self.subTest(field=field):
                bad = copy.deepcopy(task)
                del bad[field]
                with self.assertRaises(ERRORS):
                    self.contracts.task(bad)
        del result['execution']['visible_artifact_refs']
        with self.assertRaises(ERRORS):
            self.contracts.result(task, result)

    def test_backtranslation_accepts_environment_and_artifacts_without_attempt(self):
        task, _ = self.pair(1)
        task.update(agent='review', operation='review.backtranslate', acceptance='DELIVERY',
                    expected_record_types=['backtranslation'])
        task['input_refs'] = [r for r in task['input_refs']
                              if reference.short_type(r) == 'formal-environment']
        task['target_refs'] = copy.deepcopy(task['input_refs'])
        task['input_artifacts'] = copy.deepcopy(self.workflow['results'][2]['artifacts'])
        # No formalization-attempt is needed or exposed in this positive case.
        self.contracts.task(task)
        for case in ('no-artifact', 'no-environment', 'source-leak'):
            with self.subTest(case=case):
                bad = copy.deepcopy(task)
                if case == 'no-artifact':
                    bad['input_artifacts'] = []
                elif case == 'no-environment':
                    bad['input_refs'] = []
                    bad['target_refs'] = []
                else:
                    bad['input_refs'].append(copy.deepcopy(self.workflow['tasks'][0]['input_refs'][0]))
                with self.assertRaises(ERRORS):
                    self.contracts.task(bad)

    def test_reader_can_start_from_brief_only(self):
        task, result = self.pair(2)
        task.update(input_refs=[], target_refs=[], input_artifacts=[],
                    brief='Explain why delivery alone does not establish scientific validity.')
        result['execution']['visible_input_refs'] = []
        self.contracts.result(task, result)
        task['brief'] = ''
        with self.assertRaises(ERRORS):
            self.contracts.task(task)

    def blind_environment(self):
        return copy.deepcopy(next(r for r in self.workflow['tasks'][1]['input_refs']
                                  if reference.short_type(r) == 'formal-environment'))

    def blind_forbidden_refs(self):
        for family in ('authority-policy', 'processing-profile', 'agentization-plan',
                       'definition', 'work-attempt', 'formalization-attempt'):
            ref = self.blind_environment()
            ref.update(record_type='agtxiv.v3.' + family + '/0.0.0', record_id='fixture:' + family)
            yield family, ref

    def test_blind_task_rejects_context_and_diagnostic_leaks(self):
        task, _ = self.pair(1)
        task.update(agent='review', operation='review.backtranslate', acceptance='DELIVERY',
                    expected_record_types=['backtranslation'], input_refs=[self.blind_environment()],
                    target_refs=[self.blind_environment()],
                    input_artifacts=copy.deepcopy(self.workflow['results'][2]['artifacts']))
        self.contracts.task(task)
        for family, ref in self.blind_forbidden_refs():
            with self.subTest(family=family):
                bad = copy.deepcopy(task)
                bad['input_refs'].append(ref)
                with self.assertRaises(ERRORS):
                    self.contracts.task(bad)
        task['acceptance'] = 'EVIDENCE'
        with self.assertRaises(ERRORS):
            self.contracts.task(task)

    def test_blind_follow_up_rejects_forbidden_visible_inputs(self):
        task, result = self.pair(2)
        result['follow_up_requests'] = [{
            'agent': 'review', 'operation': 'review.backtranslate',
            'input_refs': [self.blind_environment()],
            'reason': 'Request a source-blind interpretation; scheduler must supply formal artifacts.'}]
        # FollowUp is a suggestion, not a complete Task. Do not require Task-only
        # fields here, but operation input-family restrictions must still hold.
        self.contracts.result(task, result)
        for family, ref in self.blind_forbidden_refs():
            with self.subTest(family=family):
                bad = copy.deepcopy(result)
                bad['follow_up_requests'][0]['input_refs'].append(ref)
                with self.assertRaises(ERRORS, msg=f'Blind follow-up must not expose {family}'):
                    self.contracts.result(task, bad)

    def test_required_inputs_cannot_be_removed(self):
        good, _ = self.pair(1)
        for family in ('formalization-packet', 'formalization-attempt', 'formal-environment',
                       'authority-policy', 'processing-profile'):
            with self.subTest(family=family):
                bad = copy.deepcopy(good)
                bad['input_refs'] = [r for r in bad['input_refs'] if reference.short_type(r) != family]
                # Keep a valid target so failure tests the missing input rule.
                bad['target_refs'] = [copy.deepcopy(bad['input_refs'][0])]
                with self.assertRaises(ERRORS):
                    self.contracts.task(bad)

    def assert_required_catalog_inputs(self, operation, families, removals):
        # These requirements come from agents.json's explicit operation
        # principles, not from the implementation's hard-coded required map.
        good, _ = self.pair()
        agent, definition = self.contracts.operations[operation]
        good.update(agent=agent, operation=operation, acceptance='DELIVERY',
                    exclusions=['fixture:producer'], capabilities=[],
                    expected_record_types=definition['output_record_types'][:1])
        good['input_refs'] = [{'record_type': 'agtxiv.v3.' + family + '/0.0.0',
                              'record_id': 'fixture:' + family, 'revision': 1,
                              'content_hash': 'sha256:' + '1' * 64} for family in families]
        good['target_refs'] = copy.deepcopy(good['input_refs'][:1])
        self.contracts.task(good)
        for family in removals:
            with self.subTest(operation=operation, missing=family):
                bad = copy.deepcopy(good)
                bad['input_refs'] = [r for r in bad['input_refs'] if reference.short_type(r) != family]
                bad['target_refs'] = copy.deepcopy(bad['input_refs'][:1])
                with self.assertRaises(ERRORS, msg=f'{operation} must require {family}'):
                    self.contracts.task(bad)

    def test_paper_requires_declared_plan_and_profile(self):
        self.assert_required_catalog_inputs('paper.extract',
            ['source-snapshot', 'agentization-plan', 'processing-profile'],
            ['agentization-plan', 'processing-profile'])

    def test_packet_assembly_requires_declared_business_inputs(self):
        families = ['math-claim', 'frozen-scope', 'argument-snapshot', 'proof-plan', 'formal-environment']
        self.assert_required_catalog_inputs('utility.assemble-packet', families, families)

    def test_certification_requires_manifest_audit_policy_and_profile(self):
        families = ['release-manifest', 'release-audit', 'authority-policy', 'processing-profile']
        self.assert_required_catalog_inputs('utility.certify', families, families)

    def test_explicit_artifacts_and_frozen_visibility(self):
        task, result = self.pair(2)
        task['target_refs'] = []
        task['input_refs'] = []
        task['input_artifacts'] = copy.deepcopy(result['artifacts'])
        result['execution']['visible_input_refs'] = []
        result['execution']['visible_artifact_refs'] = copy.deepcopy(task['input_artifacts'])
        self.contracts.result(task, result)
        for field, value in [('sha256', 'sha256:' + 'c' * 64), ('byte_size', 1),
                             ('media_type', 'text/plain'), ('artifact_id', 'fixture:other')]:
            with self.subTest(field=field):
                bad = copy.deepcopy(result)
                bad['execution']['visible_artifact_refs'][0][field] = value
                with self.assertRaises(ERRORS):
                    self.contracts.result(task, bad)
        duplicate = copy.deepcopy(task['input_artifacts'][0])
        duplicate['sha256'] = 'sha256:' + 'd' * 64
        task['input_artifacts'].append(duplicate)
        with self.assertRaises(ERRORS):
            self.contracts.task(task)

    def test_task_graph_rejects_missing_duplicate_cycle_and_wrong_gate(self):
        good = copy.deepcopy(self.workflow['tasks'])
        self.contracts.task_graph(good)
        for case in ('missing', 'duplicate-id', 'duplicate-edge', 'cycle', 'evidence-to-delivery'):
            with self.subTest(case=case):
                bad = copy.deepcopy(good)
                if case == 'missing':
                    bad[1]['depends_on'][0]['task_id'] = 'fixture:absent'
                elif case == 'duplicate-id':
                    bad.append(copy.deepcopy(bad[0]))
                elif case == 'duplicate-edge':
                    bad[1]['depends_on'].append(copy.deepcopy(bad[1]['depends_on'][0]))
                elif case == 'cycle':
                    bad[0]['depends_on'] = [{'task_id': bad[1]['task_id'], 'gate': 'DELIVERY'}]
                else:
                    bad[1]['depends_on'][0]['gate'] = 'EVIDENCE'
                with self.assertRaises(ERRORS):
                    self.contracts.task_graph(bad)
        good[2]['depends_on'] = [{'task_id': good[1]['task_id'], 'gate': 'EVIDENCE'}]
        self.contracts.task_graph(good)  # Structure only, despite blocked checker result.

    def test_result_bindings_time_and_required_output(self):
        task, good = self.pair()
        cases = [(('task_id',), 'fixture:other'), (('output_refs',), []),
                 (('execution', 'visible_input_refs'), []),
                 (('execution', 'visible_input_refs', 0, 'revision'), 2),
                 (('execution', 'finished_at'), '2026-09-11T00:00:00Z')]
        for path, value in cases:
            with self.subTest(path=path):
                bad = copy.deepcopy(good)
                put(bad, path, value)
                with self.assertRaises(ERRORS):
                    self.contracts.result(task, bad)
        task, bad = self.pair(1)
        bad['execution']['principal_id'] = task['exclusions'][0]
        with self.assertRaises(ERRORS):
            self.contracts.result(task, bad)

    def test_no_fake_scientific_outcome_or_empty_delivery(self):
        task, good = self.pair(2)
        for outcome in ('PASSED', 'KERNEL_CHECKED', 'SUPPORTED', 'UNKNOWN', 'passed'):
            with self.subTest(outcome=outcome):
                bad = copy.deepcopy(good)
                bad['outcome'] = outcome
                with self.assertRaises(ERRORS):
                    self.contracts.result(task, bad)
        good['artifacts'] = []
        with self.assertRaises(ERRORS):
            self.contracts.result(task, good)
        for outcome in ('BLOCKED', 'FAILED', 'DEFERRED'):
            with self.subTest(outcome=outcome):
                good['outcome'] = outcome
                good['open_items'] = ['Synthetic environment unavailable.']
                self.contracts.result(task, good)
                good['open_items'] = []
                with self.assertRaises(ERRORS):
                    self.contracts.result(task, good)

    def test_follow_up_operation_and_input_family(self):
        task, good = self.pair(2)
        good['artifacts'] = []
        good['follow_up_requests'] = [{'agent': 'reader', 'operation': 'reader.explain',
                                      'input_refs': copy.deepcopy(task['input_refs']),
                                      'reason': 'Explain the remaining gap.'}]
        self.contracts.result(task, good)
        for field, value in [('agent', 'proof'), ('operation', 'reader.unknown')]:
            bad = copy.deepcopy(good)
            bad['follow_up_requests'][0][field] = value
            with self.assertRaises(ERRORS):
                self.contracts.result(task, bad)
        bad = copy.deepcopy(good)
        bad['follow_up_requests'][0].update(agent='paper', operation='paper.extract')
        with self.assertRaises(ERRORS):
            self.contracts.result(task, bad)


class ArchiveTests(ContractTests):
    # Reuse setup, not the contract tests themselves (see load_tests below).
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.manifest = read_json(ROOT / 'examples/batch/batch.json')
        self.manifest['files'] = []
        self.path = self.directory / 'batch.json'

    def add_artifact(self, path, raw=b'synthetic note', identifier='fixture:note'):
        target = self.directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        ref = {'artifact_id': identifier, 'sha256': reference.digest(raw),
               'byte_size': len(raw), 'media_type': 'text/plain'}
        self.manifest['files'].append({'path': path, 'kind': 'ARTIFACT',
                                      'sha256': ref['sha256'], 'size_bytes': len(raw), 'ref': ref})

    def check(self):
        self.path.write_text(json.dumps(self.manifest), encoding='utf-8')
        return self.contracts.archive(self.path)

    def test_bytes_and_lengths(self):
        self.add_artifact('note.txt')
        self.check()
        target = self.directory / 'note.txt'
        original = target.read_bytes()
        target.write_bytes(b'X' + original[1:])
        with self.assertRaisesRegex(ERRORS, 'hash'):
            self.check()
        target.write_bytes(original + b'!')
        with self.assertRaisesRegex(ERRORS, 'length'):
            self.check()

    def test_paths_and_symlinks(self):
        self.add_artifact('note.txt')
        self.check()
        for path in ('../note.txt', '/note.txt', 'a/../../note.txt', 'a\\note.txt'):
            with self.subTest(path=path):
                self.manifest['files'][0]['path'] = path
                with self.assertRaises(ERRORS):
                    self.check()
        (self.directory / 'link.txt').symlink_to(self.directory / 'note.txt')
        self.manifest['files'][0]['path'] = 'link.txt'
        with self.assertRaisesRegex(ERRORS, 'Symlink'):
            self.check()
        (self.directory / 'real').mkdir()
        (self.directory / 'real/note.txt').write_bytes(b'synthetic note')
        (self.directory / 'linkdir').symlink_to(self.directory / 'real', target_is_directory=True)
        self.manifest['files'][0]['path'] = 'linkdir/note.txt'
        with self.assertRaisesRegex(ERRORS, 'Symlink'):
            self.check()

    def test_case_collision_and_artifact_identity_conflict(self):
        self.add_artifact('note.txt')
        self.add_artifact('other.txt', b'other note', 'fixture:other')
        self.check()
        second = self.manifest['files'][1]
        second['path'] = 'NOTE.txt'  # Rejected before opening, also on case-insensitive hosts.
        with self.assertRaisesRegex(ERRORS, 'colliding'):
            self.check()
        second['path'] = 'other.txt'
        second['ref']['artifact_id'] = 'fixture:note'
        with self.assertRaisesRegex(ERRORS, 'identity'):
            self.check()

    def business_records(self):
        producer = {'principal_id': 'fixture:author', 'role': 'MAINTAINER', 'actor_kind': 'AGENT',
                    'identity_assurance': 'LOCALLY_ATTESTED', 'execution_id': 'fixture:execution',
                    'visible_input_refs': [], 'identity_evidence': []}
        payload = {'charter_identity': 'AgtXIv-Charter/1.0', 'charter_state': 'PROPOSED',
                   'ratification_commit': None, 'minimum_identity_assurance': 'LOCALLY_ATTESTED',
                   'separated_role_pairs': ['PRODUCER/REVIEWER'],
                   'human_review_triggers': ['Synthetic fixture only.'],
                   'allowed_principal_ids': ['fixture:author']}
        def make(identifier, policy=None, inputs=(), text='Synthetic fixture only.'):
            data = copy.deepcopy(payload)
            data['human_review_triggers'] = [text]
            return self.contracts.base.make_record('authority-policy', identifier, data,
                producer=producer, policy_ref=policy, input_refs=inputs,
                data_class='SYNTHETIC', created_at='2026-09-12T00:00:00Z')
        first = make('fixture:policy')
        second = make('fixture:child', inputs=[reference.exact_ref(first)])
        conflict = make('fixture:policy', text='Different synthetic bytes, same identity and revision.')
        return first, second, conflict

    def add_record(self, path, record):
        raw = json.dumps(record, sort_keys=True).encode('utf-8')
        (self.directory / path).write_bytes(raw)
        self.manifest['files'].append({'path': path, 'kind': 'RECORD',
            'sha256': reference.digest(raw), 'size_bytes': len(raw), 'ref': reference.exact_ref(record)})

    def test_business_reference_closure(self):
        first, second, _ = self.business_records()
        self.add_record('parent.json', first)
        self.add_record('child.json', second)
        self.assertEqual(self.check()['records'], 2)
        self.manifest['files'].pop(0)  # Bytes still exist but are outside the declared closure.
        with self.assertRaisesRegex(ERRORS, 'reference|REFERENCE'):
            self.check()

    def test_business_same_identity_different_hash(self):
        first, _, conflict = self.business_records()
        self.add_record('first.json', first)
        self.check()
        self.add_record('conflict.json', conflict)
        with self.assertRaises(ERRORS):
            self.check()


class SQLTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript((ROOT / 'storage/runtime.sql').read_text(encoding='utf-8'))
        for task in ('t1', 't2'):
            self.db.execute('INSERT INTO runtime_tasks VALUES (?, ?, ?, ?, ?, ?)',
                            (task, '{}', '{}', 'key:' + task, 'hash', '2026-09-12T00:00:00Z'))
        self.db.execute("INSERT INTO runtime_attempts VALUES ('a1','t1',1,'hash','{}','now')")
        self.db.execute("INSERT INTO runtime_events(task_id,attempt_id,event_type,payload,payload_sha256,created_at) VALUES ('t1','a1','DELIVERED',X'00','hash','now')")
        self.db.execute("INSERT INTO runtime_outbox VALUES ('m1',1,'NEO4J_PROJECTION','key',X'00','hash','now')")
        self.checkpoint('ready', 'READY', 'CANDIDATE')

    def checkpoint(self, identifier, state, view):
        self.db.execute('INSERT INTO runtime_projection_checkpoints VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (identifier, 'm1', 'batch:' + identifier, 'hash', 'commit', 'v1', view, 1, state, '{}', 'now'))

    def test_append_only_rows(self):
        tables = ('runtime_tasks', 'runtime_attempts', 'runtime_events',
                  'runtime_outbox', 'runtime_projection_checkpoints')
        for table in tables:
            for operation in ('UPDATE', 'DELETE'):
                with self.subTest(table=table, operation=operation):
                    before = self.db.execute('SELECT * FROM ' + table).fetchall()
                    sql = ('UPDATE ' + table + " SET created_at='later'" if operation == 'UPDATE'
                           else 'DELETE FROM ' + table)
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.db.execute(sql)
                    self.assertEqual(before, self.db.execute('SELECT * FROM ' + table).fetchall())

    def test_foreign_keys_and_event_task_binding(self):
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone()[0], 1)
        statements = [
            "INSERT INTO runtime_attempts VALUES ('a2','missing',1,'hash','{}','now')",
            "INSERT INTO runtime_events(task_id,attempt_id,event_type,payload,payload_sha256,created_at) VALUES ('t2','a1','DELIVERED',X'00','hash','now')",
            "INSERT INTO runtime_outbox VALUES ('m2',999,'GIT_ARCHIVE','key',X'00','hash','now')",
            "INSERT INTO runtime_delivery(message_id,state) VALUES ('missing','PENDING')",
        ]
        for sql in statements:
            with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
        self.db.execute("INSERT INTO runtime_delivery(message_id,state) VALUES ('m1','PENDING')")

    def test_outbox_idempotency_key_is_per_destination(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO runtime_outbox VALUES ('m2',1,'NEO4J_PROJECTION','key',X'01','hash','now')")
        self.db.execute("INSERT INTO runtime_outbox VALUES ('m2',1,'GIT_ARCHIVE','key',X'00','hash','now')")
        self.assertEqual(self.db.execute('SELECT count(*) FROM runtime_outbox').fetchone()[0], 2)

    def test_head_insert_and_update_require_ready_same_view(self):
        self.checkpoint('building', 'BUILDING', 'CANDIDATE')
        self.checkpoint('failed', 'FAILED', 'CANDIDATE')
        self.checkpoint('mixed', 'READY', 'MIXED')
        for checkpoint in ('building', 'failed', 'mixed', 'missing'):
            with self.subTest(action='insert', checkpoint=checkpoint), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("INSERT INTO runtime_projection_heads VALUES ('CANDIDATE',?,1)", (checkpoint,))
        self.db.execute("INSERT INTO runtime_projection_heads VALUES ('CANDIDATE','ready',1)")
        for checkpoint in ('building', 'failed', 'mixed', 'missing'):
            with self.subTest(action='update', checkpoint=checkpoint), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("UPDATE runtime_projection_heads SET checkpoint_id=?,state_version=2", (checkpoint,))
        self.checkpoint('ready2', 'READY', 'CANDIDATE')
        self.db.execute("UPDATE runtime_projection_heads SET checkpoint_id='ready2',state_version=2")
        self.assertEqual(self.db.execute('SELECT checkpoint_id,state_version FROM runtime_projection_heads').fetchone(), ('ready2', 2))


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for cls in (ContractTests, ArchiveTests, SQLTests):
        for name in sorted(cls.__dict__):
            if name.startswith('test_'):
                suite.addTest(cls(name))
    return suite


if __name__ == '__main__':
    unittest.main()
