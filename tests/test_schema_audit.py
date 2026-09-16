"""Auditor boundary checks; green structural reports must not hide missing inputs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.audit_schemas import ROOT, collect, parse


DIALECT = 'https://json-schema.org/draft/2020-12/schema'


def write(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def root(tmp_path):
    write(tmp_path, 'docs/audits/schema-semantic-review.json', {
        'v3_families': {}, 'groups': {}, 'findings': [], 'cross_record_review': [],
    })
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'tools/audit_schemas.py').write_bytes((ROOT / 'tools/audit_schemas.py').read_bytes())
    return tmp_path


def schema(identifier, **extra):
    return {'$schema': DIALECT, '$id': identifier, 'type': 'object', **extra}


def primary(report):
    return [row for row in report['schemas'] if row['primary_project_schema']]


def test_missing_fragment_is_a_failure_after_a_valid_control(root):
    identifier = 'https://example.invalid/contract'
    write(root, 'schemas/a.schema.json', schema(identifier, **{'$defs': {'present': {'type': 'string'}},
                                                             'properties': {'value': {'$ref': '#/$defs/present'}}}))
    assert collect(root)['coverage']['primary_structure_passed'] == 1
    write(root, 'schemas/a.schema.json', schema(identifier, properties={'value': {'$ref': '#/$defs/missing'}}))
    row = primary(collect(root))[0]
    assert row['checks']['metaschema'] == 'PASS'
    assert row['checks']['references'] == 'FAIL'
    assert row['issues'][0]['code'] == 'UNRESOLVED_REFERENCE'


def test_nested_worktree_cannot_supply_missing_primary_dependency(root):
    identifier = 'https://example.invalid/external'
    write(root, 'schemas/a.schema.json', schema('https://example.invalid/root', properties={'value': {'$ref': identifier}}))
    write(root, '.claude/worktrees/copy/schemas/b.schema.json', schema(identifier))
    report = collect(root)
    assert report['coverage']['physical_schema_files'] == 2
    assert report['coverage']['primary_project_schemas'] == 1
    assert primary(report)[0]['checks']['references'] == 'FAIL'
    assert report['schemas'][0]['resolution_group'] == '.claude/worktrees/copy'


def test_duplicates_fail_within_primary_but_not_across_worktree_copies(root):
    identifier = 'https://example.invalid/repeated'
    write(root, 'schemas/a.schema.json', schema(identifier))
    write(root, '.claude/worktrees/copy/schemas/a.schema.json', schema(identifier))
    assert collect(root)['duplicate_ids'] == []
    write(root, 'schemas/b.schema.json', schema(identifier))
    report = collect(root)
    assert len(report['duplicate_ids']) == 1
    assert all(any(issue['code'] == 'DUPLICATE_ID' for issue in row['issues']) for row in primary(report))


def test_duplicate_json_keys_are_not_silently_replaced():
    with pytest.raises(ValueError, match='Duplicate JSON key'):
        parse(b'{"type":"integer","type":"string"}')


def test_symlink_target_is_not_scanned_or_used_as_a_primary_schema(root):
    write(root, 'tmp/copied/a.schema.json', schema('https://example.invalid/copied'))
    (root / 'schemas').mkdir()
    (root / 'schemas/a.schema.json').symlink_to(root / 'tmp/copied/a.schema.json')
    report = collect(root)
    assert report['coverage']['primary_project_schemas'] == 0
    assert {'path': 'schemas/a.schema.json', 'reason': 'SYMLINK_NOT_FOLLOWED'} in report['exclusions']


def test_unknown_schema_location_is_explicitly_unclassified(root):
    write(root, 'unknown/a.schema.json', schema('https://example.invalid/new'))
    row = primary(collect(root))[0]
    assert row['checks']['metaschema'] == 'PASS'
    assert any(issue['code'] == 'UNCLASSIFIED_SCHEMA' for issue in row['issues'])


def test_nested_id_changes_reference_base_and_literal_refs_remain_data(root):
    write(root, 'schemas/a.schema.json', schema('https://example.invalid/root/', **{
        '$defs': {'child': {'$id': 'child', 'type': 'object',
                            '$defs': {'inner': {'type': 'string'}},
                            'properties': {'value': {'$ref': '#/$defs/inner'}}}},
        'properties': {'child': {'$ref': 'child'}},
        'examples': [{'$ref': 'https://not-a-schema-reference.invalid'}],
    }))
    report = collect(root)
    assert report['coverage']['primary_structure_passed'] == 1
    assert report['coverage']['primary_reference_occurrences'] == 2


def test_duplicate_nested_identifiers_are_not_last_file_wins(root):
    write(root, 'schemas/a.schema.json', schema('https://example.invalid/root/', **{
        '$defs': {'one': {'$id': 'same', 'type': 'string'},
                  'two': {'$id': 'same', 'type': 'integer'}},
    }))
    report = collect(root)
    assert len(report['duplicate_ids']) == 1
    assert report['duplicate_ids'][0]['schema_id'] == 'https://example.invalid/root/same'
    assert primary(report)[0]['issues'][0]['code'] == 'DUPLICATE_ID'


def test_published_web_copies_are_deduplicated_and_byte_checked(root):
    identifier = 'https://example.invalid/published'
    value = schema(identifier, properties={
        'record_type': {'const': 'agtxiv.v3.fixture/0.0.0'},
        'payload': {'type': 'object', 'properties': {'value': {'type': 'string'}}},
    })
    write(root, 'schema v0.0/a.schema.json', value)
    write(root, 'web/public/schemas/v3/a.schema.json', value)
    report = collect(root)
    assert report['coverage']['physical_schema_files'] == 2
    assert report['coverage']['primary_project_schemas'] == 1
    assert report['coverage']['v3_payload_fields'] == 1
    assert report['coverage']['generated_web_schema_copy_mismatches'] == 0
    copy = next(row for row in report['schemas'] if not row['primary_project_schema'])
    assert copy['semantic_review']['state'] == 'EXCLUDED_FROM_PRIMARY_SEMANTIC_ACCEPTANCE'
    write(root, 'web/public/schemas/v3/a.schema.json', schema(identifier, description='Changed publication bytes.'))
    report = collect(root)
    assert report['coverage']['generated_web_schema_copy_mismatches'] == 1


def test_openapi_components_and_external_local_schema_refs_are_audited_separately(root):
    write(root, 'web/public/api/v1/job.schema.json', schema('https://example.invalid/job'))
    document = {'openapi': '3.1.0', 'paths': {'/jobs': {'get': {'operationId': 'readJobs'}}},
                'components': {'schemas': {'Job': {'$ref': 'job.schema.json'},
                                           'Result': {'type': 'object', 'properties': {'job': {'$ref': '#/components/schemas/Job'}}}}}}
    write(root, 'web/public/api/v1/openapi.json', document)
    report = collect(root)
    assert report['coverage']['primary_project_schemas'] == 1
    assert report['coverage']['openapi_component_schemas'] == 2
    assert report['coverage']['openapi_operations'] == 1
    assert report['public_api_documents'][0]['issues'] == []
    document['components']['schemas']['Job']['$ref'] = 'missing.schema.json'
    write(root, 'web/public/api/v1/openapi.json', document)
    assert report['coverage']['primary_structure_passed'] == 1
    assert collect(root)['public_api_documents'][0]['issues'][0]['code'] == 'OPENAPI_REFERENCE'


def test_analysis_publication_alias_requires_exact_primary_bytes(root):
    value = schema('https://example.invalid/analysis')
    write(root, 'src/agtxiv_web/analysis.schema.json', value)
    write(root, 'web/public/api/v1/analysis.schema.json', value)
    write(root, 'web/dist/client/api/v1/analysis.schema.json', value)
    write(root, 'web/public/api/v1/openapi.json', {
        'openapi': '3.1.0', 'paths': {},
        'components': {'schemas': {'Analysis': {'$ref': 'analysis.schema.json'}}},
    })
    report = collect(root)
    assert report['coverage']['primary_project_schemas'] == 1
    assert report['coverage']['generated_web_schema_copy_mismatches'] == 0
    assert report['duplicate_ids'] == []
    assert report['public_api_documents'][0]['issues'] == []
    write(root, 'web/public/api/v1/analysis.schema.json', schema('https://example.invalid/analysis', description='Unreviewed drift'))
    report = collect(root)
    assert report['coverage']['generated_web_schema_copy_mismatches'] == 2
    assert report['public_api_documents'][0]['issues'][0]['code'] == 'OPENAPI_REFERENCE'
