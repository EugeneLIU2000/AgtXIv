#!/usr/bin/env python3
"""Offline orchestration contract reference. No scheduler or scientific oracle."""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'src'))

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Resource
from agtxiv_v3.contracts import (
    ContractError, RecordSet, SchemaBundle, SuppliedArtifact,
    digest, exact_ref, parse,
)

MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
CONTEXT_TYPES = {'authority-policy', 'processing-profile', 'agentization-plan'}
BLIND_FORBIDDEN = {
    'source-snapshot', 'source-span', 'paper-structure', 'scientific-claim',
    'math-claim', 'formalization-packet', 'alignment-assessment',
}


class InterfaceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InterfaceError(message)


def read_bytes(path):
    path = Path(path)
    require(not path.is_symlink(), f'Symlink input rejected: {path}')
    require(path.is_file(), f'Missing regular input file: {path}')
    require(path.stat().st_size <= MAX_FILE, f'Input exceeds 64 MiB: {path}')
    # A read bound also covers growth after stat; not a hostile-filesystem sandbox.
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE + 1)
    require(len(raw) <= MAX_FILE, f'Input exceeds 64 MiB: {path}')
    return raw


def read_json(path):
    return parse(read_bytes(path))


def short_type(ref):
    return ref['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0')


def ref_key(ref):
    return tuple(ref[k] for k in ('record_type', 'record_id', 'revision', 'content_hash'))


def check_ref_set(refs):
    identities = {}
    for ref in refs:
        key = ref_key(ref)
        require(key[:3] not in identities, 'Duplicate identity/revision, even with a different hash')
        identities[key[:3]] = key[3]


def artifact_key(ref):
    return tuple(ref[k] for k in ('artifact_id', 'sha256', 'byte_size', 'media_type'))


def check_artifact_set(refs):
    ids = [r['artifact_id'] for r in refs]
    require(len(ids) == len(set(ids)), 'Duplicate artifact identity')


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class Contracts:
    def __init__(self, directory=ROOT):
        self.directory = Path(directory)
        lock = read_json(self.directory / 'compatibility.lock.json')
        require(lock['contract_version'] == '0.1.0', 'Wrong orchestration lock version')
        require(lock['base_directory'] == '../schema v0.0', 'Unexpected base location')
        self.base = SchemaBundle(self.directory.parent / 'schema v0.0')
        require(self.base.bundle_hash == lock['base_bundle_hash'], 'Pinned v0.0 bundle changed')
        require(len(self.base.by_type) == lock['record_count'] == 64, 'Base record count changed')
        self.types = {t.removeprefix('agtxiv.v3.').removesuffix('/0.0.0') for t in self.base.by_type}
        self.schemas = {}
        self.registry = self.base.registry
        for path in sorted((self.directory / 'schemas').glob('*.schema.json')):
            schema = read_json(path)
            Draft202012Validator.check_schema(schema)
            require(schema['$id'] not in self.schemas, 'Duplicate schema URI')
            self.schemas[schema['$id']] = schema
            self.registry = self.registry.with_resource(schema['$id'], Resource.from_contents(schema))
        require(len(self.schemas) == 5, 'Expected five local schema files')
        for uri, schema in self.schemas.items():
            resolver = self.registry.resolver(base_uri=uri)
            for item in walk(schema):
                if '$ref' in item:
                    resolver.lookup(item['$ref'])
        self.agents = read_json(self.directory / 'agents.json')
        self.shape('agent-registry', self.agents)
        self.operations = {}
        seen = set()
        for agent in self.agents['agents']:
            aid = agent['agent_id']
            require(aid not in seen, f'Duplicate agent: {aid}')
            seen.add(aid)
            for operation in agent['operations']:
                op = operation['operation']
                require(op.startswith(aid + '.'), f'Operation/agent mismatch: {op}')
                require(op not in self.operations, f'Duplicate operation: {op}')
                for field in ('input_record_types', 'output_record_types'):
                    require(set(operation[field]) <= self.types, f'Unknown business family in {op}/{field}')
                self.operations[op] = (aid, operation)

    def shape(self, name, value):
        uri = f'https://agtxiv.org/schema/orchestration/0.1.0/{name}.schema.json'
        validator = Draft202012Validator(self.schemas[uri], registry=self.registry, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(value), key=lambda e: repr(list(e.absolute_path)))
        if errors:
            first = errors[0]
            raise InterfaceError(f'{name}/{"/".join(map(str, first.absolute_path))}: {first.message}')

    def operation(self, agent, name):
        require(name in self.operations, f'Unknown operation: {name}')
        aid, operation = self.operations[name]
        require(aid == agent, 'Agent/operation mismatch')
        return operation

    def task(self, task):
        self.shape('task', task)
        operation = self.operation(task['agent'], task['operation'])
        check_ref_set(task['input_refs'])
        check_ref_set(task['target_refs'])
        check_artifact_set(task['input_artifacts'])
        require({ref_key(r) for r in task['target_refs']} <= {ref_key(r) for r in task['input_refs']}, 'Task target is not an exact visible input')
        require(bool(task['target_refs']) or task['agent'] in {'planner', 'reader'} or bool(task['input_artifacts']), 'Task needs an exact target or explicit artifact input')
        inputs = {short_type(r) for r in task['input_refs']}
        allowed_inputs = set(operation['input_record_types']) | CONTEXT_TYPES
        if task['operation'] == 'review.backtranslate':
            allowed_inputs = {'formal-environment'}
        require(inputs <= allowed_inputs, 'Disallowed input family')
        require(set(task['expected_record_types']) <= set(operation['output_record_types']), 'Disallowed output family')
        require(set(task['capabilities']) <= set(operation['capabilities']), 'Capability escalation')
        require(task['limits']['no_progress_limit'] <= task['limits']['max_attempts'], 'No-progress limit exceeds attempt limit')
        deps = [d['task_id'] for d in task['depends_on']]
        require(len(deps) == len(set(deps)), 'Duplicate prerequisite task')
        require(task['task_id'] not in deps, 'Task depends on itself')
        required = {
            'paper.extract': {'source-snapshot', 'agentization-plan', 'processing-profile'},
            'proof.expand': {'math-claim', 'frozen-scope'},
            'formalization.generate': {'formalization-packet'},
            'review.scope': {'inventory-discovery', 'source-snapshot', 'paper-structure', 'agentization-plan', 'processing-profile'},
            'review.argument': {'argument-snapshot', 'frozen-scope'},
            'review.backtranslate': {'formal-environment'},
            'review.audit': {'release-manifest', 'processing-profile'},
            'review.admission': {'paper-release', 'knowledge-snapshot', 'authority-policy', 'processing-profile'},
            'delta.compare': {'baseline-snapshot'},
            'utility.register-plan': {'source-snapshot', 'processing-profile'},
            'utility.assemble-packet': {'math-claim', 'frozen-scope', 'argument-snapshot', 'proof-plan', 'formal-environment'},
            'utility.formal-check': {'formalization-packet', 'formalization-attempt', 'formal-environment'},
            'utility.certify': {'release-manifest', 'release-audit', 'authority-policy', 'processing-profile'},
        }.get(task['operation'], set())
        require(required <= inputs, 'Missing required operation input: ' + ', '.join(sorted(required - inputs)))
        if task['operation'] == 'dependency.search':
            require(bool(inputs & {'source-snapshot', 'scientific-claim', 'math-claim'}), 'Dependency search requires source or claim')
        if task['operation'] == 'utility.capture':
            require(bool(inputs & {'source-request', 'source-snapshot'}), 'Capture requires a fixed request or source')
        if task['operation'] in {'review.reuse', 'review.alignment'}:
            require(len(task['target_refs']) >= 2, 'Comparison requires both exact target endpoints')
        if task['operation'] == 'review.reuse' and 'reuse-decision' in task['expected_record_types']:
            require('processing-profile' in inputs, 'Reuse decision requires a processing profile')
        if task['operation'] == 'review.alignment':
            formal_targets = {'formalization-packet', 'formalization-attempt', 'formal-check'}
            if {short_type(r) for r in task['target_refs']} & formal_targets:
                require('backtranslation' in inputs, 'Formal alignment requires frozen backtranslation')
        if task['operation'] == 'delta.compare':
            require(any(short_type(r) != 'baseline-snapshot' for r in task['target_refs']), 'Delta needs a current target, not only the baseline')
        if task['operation'] == 'utility.export':
            if 'paper-release' in task['expected_record_types']:
                require({'release-manifest', 'release-audit', 'release-certificate'} <= inputs, 'Release assembly requires manifest, audit and certificate')
            if 'archive-receipt' in task['expected_record_types']:
                require('paper-release' in inputs, 'Archive receipt requires an existing paper release')
        if task['acceptance'] == 'EVIDENCE':
            require({'authority-policy', 'processing-profile'} <= inputs, 'Evidence gate requires exact policy and profile')
            require(bool(task['expected_record_types']), 'Evidence task must name business outputs')
            require(bool(task['target_refs']), 'Evidence task must name exact targets')
        independent = task['agent'] in {'review', 'delta'} or task['operation'] in {'utility.formal-check', 'utility.certify'}
        if independent:
            require(bool(task['exclusions']), 'Independent work requires declared producer exclusions')
        if task['operation'] == 'review.backtranslate':
            require(not (inputs & BLIND_FORBIDDEN), 'Source-blind work has forbidden visible input')
            require(bool(task['input_artifacts']), 'Source-blind work requires explicit formal artifacts')
            require(task['acceptance'] == 'DELIVERY', 'Blind interpretation delivers a candidate; later independent review evaluates evidence')
        return task

    def task_graph(self, tasks):
        require(isinstance(tasks, list) and len(tasks) <= 10000, 'Task graph must be a bounded list')
        index = {}
        for task in tasks:
            self.task(task)
            require(task['task_id'] not in index, 'Duplicate task ID')
            index[task['task_id']] = task
        indegree = {key: 0 for key in index}
        children = {key: [] for key in index}
        for task in tasks:
            for dependency in task['depends_on']:
                parent = dependency['task_id']
                require(parent in index, f'Missing prerequisite task: {parent}')
                if dependency['gate'] == 'EVIDENCE':
                    require(index[parent]['acceptance'] == 'EVIDENCE', 'Evidence dependency points to delivery-only task')
                indegree[task['task_id']] += 1
                children[parent].append(task['task_id'])
        ready = deque(key for key, degree in indegree.items() if degree == 0)
        order = []
        while ready:
            key = ready.popleft()
            order.append(key)
            for child in children[key]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        require(len(order) == len(index), 'Cycle in task prerequisites')
        # This order is structural, NOT an execution-readiness or science decision.
        return order

    def result(self, task, result):
        self.task(task)
        self.shape('result', result)
        require(result['task_id'] == task['task_id'], 'Result belongs to another task')
        check_ref_set(result['output_refs'])
        execution = result['execution']
        check_ref_set(execution['visible_input_refs'])
        check_artifact_set(execution['visible_artifact_refs'])
        check_artifact_set(result['artifacts'])
        require(execution['principal_id'] not in task['exclusions'], 'Declared producer self-review/conflict')
        require({ref_key(r) for r in execution['visible_input_refs']} == {ref_key(r) for r in task['input_refs']}, 'Visible input versions differ from frozen task')
        require({artifact_key(r) for r in execution['visible_artifact_refs']} == {artifact_key(r) for r in task['input_artifacts']}, 'Visible artifacts differ from frozen task')
        start = datetime.fromisoformat(execution['started_at'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(execution['finished_at'].replace('Z', '+00:00'))
        require(end >= start, 'Negative execution duration')
        output_types = {short_type(r) for r in result['output_refs']}
        expected = set(task['expected_record_types'])
        require(output_types <= expected, 'Unexpected output family for this task')
        if result['outcome'] == 'DELIVERED':
            require(expected <= output_types, 'Delivered task is missing expected output family')
            require(bool(result['output_refs'] or result['artifacts'] or result['follow_up_requests']), 'Empty delivery')
        else:
            require(bool(result['open_items']), 'Non-delivery requires an explicit reason or gap')
        for request in result['follow_up_requests']:
            operation = self.operation(request['agent'], request['operation'])
            check_ref_set(request['input_refs'])
            allowed = set(operation['input_record_types']) | CONTEXT_TYPES
            if request['operation'] == 'review.backtranslate':
                allowed = {'formal-environment'}
            require({short_type(r) for r in request['input_refs']} <= allowed, 'Disallowed follow-up input family')
        # No approval boolean is returned: delivery and evidence are separate.
        return result

    def archive(self, manifest_path):
        manifest_path = Path(manifest_path)
        manifest = read_json(manifest_path)
        self.shape('archive-batch', manifest)
        require(manifest['base_bundle_hash'] == self.base.bundle_hash, 'Archive uses a different business bundle')
        require(manifest['batch_id'] != manifest['parent_batch_id'], 'Archive cannot be its own parent')
        require(sum(f['size_bytes'] for f in manifest['files']) <= MAX_TOTAL, 'Archive exceeds 256 MiB')
        root = manifest_path.parent.resolve()
        paths, records, artifacts, artifact_ids = set(), [], [], set()
        total = 0
        for member in manifest['files']:
            parts = member['path'].split('/')
            require(all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', p) for p in parts), 'Unsafe/nonportable archive member path')
            normalized = unicodedata.normalize('NFC', member['path']).casefold()
            require(normalized not in paths, 'Duplicate/case-colliding archive member path')
            paths.add(normalized)
            target = root
            for part in parts:
                target = target / part
                require(not target.is_symlink(), 'Symlink archive member rejected')
            require(target.resolve().is_relative_to(root), 'Archive member escapes root')
            require(target.resolve() != manifest_path.resolve(), 'Manifest cannot include itself')
            raw = read_bytes(target)
            total += len(raw)
            require(total <= MAX_TOTAL, 'Archive exceeds actual byte budget')
            require(len(raw) == member['size_bytes'], 'Archive file length mismatch')
            require(digest(raw) == member['sha256'], 'Archive raw-byte hash mismatch')
            if member['kind'] == 'RECORD':
                record = parse(raw)
                issues = self.base.validate_record(record)
                require(not issues, 'Invalid business record: ' + '; '.join(i.message for i in issues))
                require(exact_ref(record) == member['ref'], 'Manifest record reference mismatch')
                records.append(record)
            else:
                ref = member['ref']
                require(ref['artifact_id'] not in artifact_ids, 'Duplicate artifact identity')
                artifact_ids.add(ref['artifact_id'])
                item = SuppliedArtifact(ref['artifact_id'], ref['media_type'], raw)
                require(all(ref[k] == v for k, v in item.reference().items()), 'Manifest artifact reference mismatch')
                artifacts.append(item)
        checked = RecordSet(self.base, records, artifacts).validate(require_artifacts=True)
        checked.require_valid()
        return {'batch_id': manifest['batch_id'], 'members': len(paths), 'records': len(records),
                'artifacts': len(artifacts), 'raw_bytes': total, 'record_closure_checked': True,
                'authority_checked': False, 'scientific_acceptance_checked': False,
                'parent_batch_history_checked': False}

    def check_package(self):
        fixture = read_json(self.directory / 'examples' / 'workflow.json')
        require(fixture['data_class'] == 'SYNTHETIC', 'Examples must be explicitly synthetic')
        order = self.task_graph(fixture['tasks'])
        tasks = {t['task_id']: t for t in fixture['tasks']}
        attempts = set()
        for result in fixture['results']:
            require(result['attempt_id'] not in attempts, 'Duplicate fixture attempt ID')
            attempts.add(result['attempt_id'])
            require(result['task_id'] in tasks, 'Unknown fixture result task')
            self.result(tasks[result['task_id']], result)
        archive = self.archive(self.directory / 'examples' / 'batch' / 'batch.json')
        sql_path = self.directory / 'storage' / 'runtime.sql'
        with sqlite3.connect(':memory:') as db:
            db.executescript(read_bytes(sql_path).decode('utf-8'))
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {'contract_version': '0.1.0', 'schemas': len(self.schemas),
                'base_record_families': len(self.types), 'agent_templates': len(self.agents['agents']),
                'operations': len(self.operations), 'synthetic_tasks': len(tasks),
                'synthetic_results': len(attempts), 'structural_task_order': order,
                'example_archive': archive, 'sql_reference_tables': tables,
                'task_record_references_resolved': False, 'runtime_identity_authenticated': False,
                'scientific_acceptance_checked': False, 'neo4j_executed': False,
                'model_or_lean_executed': False, 'git_published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check the package, synthetic examples and SQL DDL')
    parser.add_argument('--task', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    if args.result and not args.task:
        parser.error('--result requires --task')
    try:
        contracts = Contracts()
        report = {'valid': True, 'scope': 'OFFLINE_CONTRACT_CHECK', 'authority_checked': False,
                  'scientific_acceptance_checked': False}
        if args.check or not (args.task or args.archive):
            report['package'] = contracts.check_package()
        if args.task:
            task = contracts.task(read_json(args.task))
            report['task'] = task['task_id']
            report['task_record_references_resolved'] = False
            if args.result:
                result = contracts.result(task, read_json(args.result))
                report['attempt'] = result['attempt_id']
                report['runtime_identity_authenticated'] = False
        if args.archive:
            report['archive'] = contracts.archive(args.archive)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (InterfaceError, ContractError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'valid': False, 'scope': 'OFFLINE_CONTRACT_CHECK', 'error': str(error)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
