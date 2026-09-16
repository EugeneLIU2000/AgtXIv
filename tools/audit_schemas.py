#!/usr/bin/env python3
"""Offline, deterministic schema inventory; structural validity is not scientific acceptance.

No repository code, source generator, TeX, or external schema is executed. The
semantic review is a maintained human/agent review input, never inferred from a
green JSON Schema result. Run with the locked repository Python environment.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote, urljoin

from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

ROOT = Path(__file__).resolve().parents[1]
PRUNED_NAMES = frozenset({'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.lake'})
TEXT_SUFFIXES = frozenset({'.py', '.md', '.toml', '.yaml', '.yml', '.json', '.js', '.mjs', '.cjs', '.ts', '.jsx', '.tsx', '.html', '.tex', '.sh'})
NON_PRIMARY = frozenset({'NESTED_WORKTREE', 'GENERATED_SITE_COPY', 'GENERATED_WEB_SCHEMA_COPY', 'GENERATED_WEB_API_SCHEMA_COPY', 'GENERATED_WEB_BUILD_COPY', 'THIRD_PARTY_SCRATCH', 'THIRD_PARTY_REFERENCE'})
REVIEW_PATH = 'docs/audits/schema-semantic-review.json'
OUTPUTS = ('schema-release-audit.json', 'schema-release-audit.md')


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def parse(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('Duplicate JSON key: ' + key)
            out[key] = value
        return out

    def invalid(value):
        raise ValueError('Non-JSON numeric constant: ' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def walk(value, pointer=''):
    if isinstance(value, dict):
        yield pointer, value
        for key, child in value.items():
            yield from walk(child, pointer + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + '/' + str(index))


def classify(path):
    parts = Path(path).parts
    if len(parts) > 2 and parts[:2] == ('.claude', 'worktrees'):
        return 'NESTED_WORKTREE', '/'.join(parts[:3])
    if parts[:2] == ('web', 'dist'):
        return 'GENERATED_WEB_BUILD_COPY', 'WEB_BUILD_COPY'
    if parts[:4] == ('web', 'public', 'schemas', 'v3'):
        return 'GENERATED_WEB_SCHEMA_COPY', 'WEB_GENERATED_COPY'
    if path == 'web/public/api/v1/analysis.schema.json':
        return 'GENERATED_WEB_API_SCHEMA_COPY', 'WEB_API_PUBLICATION_COPY'
    if parts[:4] == ('web', 'public', 'api', 'v1'):
        return 'PUBLIC_WEB_API_CONTRACT', 'PRIMARY'
    if parts[:2] == ('src', 'agtxiv_web'):
        return 'PUBLIC_WEB_API_CONTRACT', 'PRIMARY'
    if parts[0] in {'_site', 'dist'}:
        return 'GENERATED_SITE_COPY', parts[0]
    if parts[0] == 'tmp':
        return 'THIRD_PARTY_SCRATCH', '/'.join(parts[:2])
    if parts[0] in {'Reference', 'References'}:
        return 'THIRD_PARTY_REFERENCE', '/'.join(parts[:2])
    if parts[:2] == ('schema v0.0', 'upstream'):
        return 'PINNED_UPSTREAM_PROFILE', 'PRIMARY'
    if parts[0] == 'schema v0.0':
        return 'V3_EXPERIMENTAL_CONTRACT', 'PRIMARY'
    if parts[:2] == ('schemas', 'v2'):
        return 'V2_COMPATIBILITY_CONTRACT', 'PRIMARY'
    if parts[:2] == ('schemas', 'repository-validation'):
        return 'REPOSITORY_VALIDATION_CONTRACT', 'PRIMARY'
    if parts[0] == 'schemas':
        return 'CROSS_VERSION_SUPPORT_CONTRACT', 'PRIMARY'
    if parts[:2] == ('database', 'schemas'):
        return 'RESEARCH_QUERY_DATASET_CONTRACT', 'PRIMARY'
    if parts[0] == 'Stabilizerness' and 'schema' in parts:
        return 'LEGACY_RESEARCH_REGISTRY_CONTRACT', 'PRIMARY'
    if parts[0] == 'fixtures':
        return 'TEST_FIXTURE_CONTRACT', 'PRIMARY'
    return 'UNCLASSIFIED_REQUIRES_REVIEW', 'PRIMARY'


def inventory(root):
    """Visit physical project files, without following symlinks or git internals."""
    paths, excluded = [], []

    def visit(directory):
        for path in sorted(directory.iterdir(), key=lambda p: p.name):
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                excluded.append({'path': rel, 'reason': 'SYMLINK_NOT_FOLLOWED'})
            elif path.is_dir():
                if path.name in PRUNED_NAMES:
                    excluded.append({'path': rel, 'reason': 'DEPENDENCY_CACHE_OR_INTERNAL_DIRECTORY'})
                else:
                    visit(path)
            elif path.is_file():
                paths.append(path)

    visit(root)
    return paths, excluded


def resource_uri(relative):
    # Stable local identifiers preserve relative $ref resolution without encoding
    # the host checkout path or permitting retrieval.
    return 'https://schema-audit.invalid/workspace/' + quote(relative, safe='/')


def schema_resources(document, base_uri):
    """Visit dialect-defined subschemas, respecting nested identifiers.

    A literal ``$ref`` inside an example or const value is data, not a schema
    reference. Resource.subresources uses the selected JSON Schema dialect.
    """
    pointers = {id(value): pointer for pointer, value in walk(document)}

    def visit(resource, base):
        identifier = resource.id()
        current = urljoin(base, identifier) if identifier is not None else base
        yield pointers.get(id(resource.contents), ''), resource, current, identifier is not None
        for child in resource.subresources():
            yield from visit(child, current)

    yield from visit(Resource.from_contents(document), base_uri)


def maintained_source(path, classification):
    if classification == 'V3_EXPERIMENTAL_CONTRACT':
        return {'kind': 'GENERATED', 'paths': ['tools/generate_v3_schema_v00.py'],
                'instruction': 'Edit the generator; retain published historical bytes and explicit bundle versions.'}
    if classification == 'PINNED_UPSTREAM_PROFILE':
        return {'kind': 'GENERATED_PINNED_UPSTREAM', 'paths': ['tools/generate_vibefeld_protocol.py', 'schema v0.0/upstream/vibefeld-392b2da3/manifest.json'],
                'instruction': 'Preserve upstream source pins and profile identity.'}
    if classification == 'GENERATED_SITE_COPY':
        source = '/'.join(Path(path).parts[1:])
        return {'kind': 'GENERATED_COPY', 'paths': [source, 'tools/build_pages_site.sh'],
                'instruction': 'Regenerate from project inputs; do not edit the published copy.'}
    if classification == 'GENERATED_WEB_SCHEMA_COPY':
        source = 'schema v0.0/' + '/'.join(Path(path).parts[4:])
        return {'kind': 'GENERATED_BYTE_COPY', 'paths': [source, 'tools/export_web_library.py'],
                'instruction': 'Keep the copied schema byte-identical; rebuild from the primary V3 bundle.'}
    if classification == 'GENERATED_WEB_API_SCHEMA_COPY':
        return {'kind': 'GENERATED_BYTE_COPY', 'paths': ['src/agtxiv_web/analysis.schema.json', 'web/build.mjs'],
                'instruction': 'Publish the exact source-engine report contract bytes; do not edit this copy.'}
    if classification == 'GENERATED_WEB_BUILD_COPY':
        parts = Path(path).parts
        remainder = parts[3:] if parts[:3] == ('web', 'dist', 'client') else parts[2:]
        return {'kind': 'GENERATED_BYTE_COPY', 'paths': ['web/public/' + '/'.join(remainder), 'web/build.mjs'],
                'instruction': 'Build artifacts do not define a new contract; compare with the published input resource.'}
    if path == 'web/public/api/v1/job.schema.json':
        return {'kind': 'GENERATED_PRIMARY_INTERFACE', 'paths': ['web/api-spec.mjs', 'web/build.mjs'],
                'instruction': 'Edit jobSchema in the API definition and regenerate public resources.'}
    return {'kind': 'FILE_ORIGIN_NOT_GENERATOR_VERIFIED', 'paths': [path],
            'instruction': 'Preserve compatibility bytes; examine producer history before changing or moving.'}


def document_section(text, filename):
    for section in re.split(r'(?m)^## ', text):
        if re.search(r'\]\(' + re.escape(filename) + r'\)', section):
            return section
    return ''


def common_section(text, name):
    for section in re.split(r'(?m)^### ', text):
        if name in section.split('\n', 1)[0]:
            return section
    return ''


def collect(root):
    auditor_raw = (root / 'tools/audit_schemas.py').read_bytes()
    paths, excluded = inventory(root)
    inventoried_paths = {p.relative_to(root).as_posix() for p in paths}
    schemas = [p for p in paths if p.name.endswith('.schema.json')]
    semantic_path = root / REVIEW_PATH
    semantic_raw = semantic_path.read_bytes()
    semantic = parse(semantic_raw)
    sources = {}
    source_fingerprints = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        category, _ = classify(rel)
        if (category in NON_PRIMARY or rel.startswith('docs/audits/') or
                rel == 'tools/audit_schemas.py' or path.name.endswith('.schema.json') or
                (path.suffix not in TEXT_SUFFIXES and path.name not in {'Makefile', 'LICENSE'})):
            continue
        raw = path.read_bytes()
        if len(raw) > 4 * 1024 * 1024:
            excluded.append({'path': rel, 'reason': 'STATIC_CONSUMER_SCAN_OVER_4_MIB'})
            continue
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            excluded.append({'path': rel, 'reason': 'STATIC_CONSUMER_SCAN_NON_UTF8'})
            continue
        sources[rel] = text
        source_fingerprints.append({'path': rel, 'byte_size': len(raw), 'sha256': sha(raw)})

    entries, documents, groups = [], {}, defaultdict(list)
    for path in schemas:
        rel = path.relative_to(root).as_posix()
        category, group = classify(rel)
        raw = path.read_bytes()
        row = {'path': rel, 'classification': category, 'resolution_group': group,
               'primary_project_schema': category not in NON_PRIMARY,
               'byte_size': len(raw), 'sha256': sha(raw), 'issues': [],
               'maintained_source': maintained_source(rel, category),
               'checks': {'json_parse': 'NOT_RUN', 'metaschema': 'NOT_RUN', 'references': 'NOT_RUN'}}
        if category in {'GENERATED_SITE_COPY', 'GENERATED_WEB_SCHEMA_COPY', 'GENERATED_WEB_API_SCHEMA_COPY', 'GENERATED_WEB_BUILD_COPY'}:
            source = row['maintained_source']['paths'][0]
            original = root / source
            same = source in inventoried_paths and original.is_file() and not original.is_symlink() and sha(original.read_bytes()) == row['sha256']
            row['copy_consistency'] = {'primary_path': source,
                                       'status': 'EXACT_BYTES_MATCH' if same else 'MISSING_OR_DIFFERENT_PRIMARY_BYTES'}
            if not same:
                row['issues'].append({'code': 'GENERATED_COPY_MISMATCH', 'message': 'Published copy does not match its declared primary source bytes.'})
        if category == 'UNCLASSIFIED_REQUIRES_REVIEW':
            row['issues'].append({'code': 'UNCLASSIFIED_SCHEMA', 'message': 'Assign an authority/lifecycle classification before release.'})
        try:
            doc = parse(raw)
            if not isinstance(doc, dict):
                raise ValueError('Schema root is not an object')
            row['checks']['json_parse'] = 'PASS'
            row.update({'schema_id': doc.get('$id'), 'dialect': doc.get('$schema'), 'title': doc.get('title'),
                        'description': doc.get('description'), 'record_type': doc.get('properties', {}).get('record_type', {}).get('const')})
            if not doc.get('$schema'):
                raise ValueError('Schema dialect is not declared')
            validator_for(doc).check_schema(doc)
            row['checks']['metaschema'] = 'PASS'
            documents[rel] = doc
            groups[group].append(row)
        except Exception as error:
            key = 'metaschema' if row['checks']['json_parse'] == 'PASS' else 'json_parse'
            row['checks'][key] = 'FAIL'
            row['issues'].append({'code': key.upper(), 'message': str(error)})
        entries.append(row)

    def no_network(uri):
        raise NoSuchResource(ref=uri)

    duplicates = []
    registries = {}
    for group, rows in sorted(groups.items()):
        registry = Registry(retrieve=no_network)
        ids = defaultdict(list)
        resources_by_path = {}
        for row in rows:
            doc = documents[row['path']]
            resource = Resource.from_contents(doc)
            local = resource_uri(row['path'])
            registry = registry.with_resource(local, resource)
            resources_by_path[row['path']] = list(schema_resources(doc, local))
            for pointer, child, base, identified in resources_by_path[row['path']]:
                if identified:
                    ids[base].append((row['path'], pointer, child))
        # A duplicated identifier is not allowed to resolve by last-file-wins.
        for identifier, owners in sorted(ids.items()):
            if len(owners) == 1:
                registry = registry.with_resource(identifier, owners[0][2])
            else:
                duplicates.append({'resolution_group': group, 'schema_id': identifier,
                                   'paths': [path + ('#' + pointer if pointer else '') for path, pointer, _ in owners]})
        for row in rows:
            doc = documents[row['path']]
            refs = []
            for pointer, resource, base, _ in resources_by_path[row['path']]:
                value = resource.contents
                if not isinstance(value, dict):
                    continue
                resolver = registry.resolver(base)
                for keyword in ('$ref', '$dynamicRef'):
                    if keyword not in value:
                        continue
                    ref = value[keyword]
                    result = {'pointer': pointer + '/' + keyword, 'reference': ref, 'status': 'PASS'}
                    try:
                        resolver.lookup(ref)
                    except Exception as error:
                        result.update({'status': 'FAIL', 'message': str(error)})
                        row['issues'].append({'code': 'UNRESOLVED_REFERENCE', **result})
                    refs.append(result)
            row['references'] = refs
            row['checks']['references'] = 'PASS' if all(r['status'] == 'PASS' for r in refs) else 'FAIL'
            if any(len(owners)>1 and any(path==row['path'] for path, _, _ in owners) for owners in ids.values()):
                row['issues'].append({'code': 'DUPLICATE_ID', 'message': 'Identifier is duplicated within this resolution group.'})
        registries[group] = registry

    api_documents = []
    api_path = 'web/public/api/v1/openapi.json'
    if api_path in sources:
        document = parse(sources[api_path])
        api = {'path': api_path, 'openapi': document.get('openapi'), 'issues': [],
               'components': [], 'references': [], 'operations': [],
               'review_boundary': 'OpenAPI 3.1 component-schema shapes and reference closure only; this is not a full OpenAPI specification validator or runtime conformance test.'}
        if not str(document.get('openapi', '')).startswith('3.1.'):
            api['issues'].append({'code': 'UNSUPPORTED_OPENAPI_DIALECT'})
        # The synthetic $schema supplies the JSON Pointer resolver with a dialect;
        # it is not written into or used to claim validation of the OpenAPI file.
        context = {'$schema': 'https://json-schema.org/draft/2020-12/schema', **document}
        registry = registries.get('PRIMARY', Registry(retrieve=no_network)).with_resource(
            resource_uri(api_path), Resource.from_contents(context))
        for row in entries:
            if row['classification']=='GENERATED_WEB_API_SCHEMA_COPY' and row.get('copy_consistency', {}).get('status')=='EXACT_BYTES_MATCH':
                registry = registry.with_resource(resource_uri(row['path']), Resource.from_contents(documents[row['path']]))
        resolver = registry.resolver(resource_uri(api_path))
        for name, shape in document.get('components', {}).get('schemas', {}).items():
            component = {'name': name, 'metaschema': 'PASS', 'properties': sorted(shape.get('properties', {})) if isinstance(shape, dict) else []}
            try:
                Draft202012Validator.check_schema(shape)
            except Exception as error:
                component.update({'metaschema': 'FAIL', 'message': str(error)})
                api['issues'].append({'code': 'OPENAPI_COMPONENT_SCHEMA', 'component': name, 'message': str(error)})
            api['components'].append(component)
        for pointer, value in walk(document):
            if '$ref' not in value or any('/' + name + '/' in pointer for name in ('example', 'examples', 'default', 'const', 'enum')):
                continue
            result = {'pointer': pointer + '/$ref', 'reference': value['$ref'], 'status': 'PASS'}
            try:
                resolver.lookup(value['$ref'])
            except Exception as error:
                result.update({'status': 'FAIL', 'message': str(error)})
                api['issues'].append({'code': 'OPENAPI_REFERENCE', **result})
            api['references'].append(result)
        for path, methods in document.get('paths', {}).items():
            for method, operation in methods.items():
                if method.lower() in {'get', 'post', 'put', 'patch', 'delete', 'options', 'head', 'trace'}:
                    api['operations'].append({'method': method.upper(), 'path': path, 'operation_id': operation.get('operationId')})
        api_documents.append(api)

    family_reviews = semantic['v3_families']
    found_families = set()
    for row in entries:
        rel = row['path']
        doc = documents.get(rel, {})
        primary = row['primary_project_schema']
        row['declared_object_fields'] = [
            {'object_pointer': pointer, 'field': field, 'required': field in shape.get('required', []),
             'type': declaration.get('type'), 'reference': declaration.get('$ref'),
             'const': declaration.get('const'), 'enum': declaration.get('enum'),
             'description': declaration.get('description'),
             'extra_properties': shape.get('additionalProperties', 'UNSPECIFIED')}
            for pointer, shape in walk(doc)
            for field, declaration in shape.get('properties', {}).items()
            if isinstance(declaration, dict)
        ]
        row['field_review_boundary'] = ('V3 payload/shared-field descriptions are compared with both generated references; other fields are inventoried without reapproving legacy semantics.'
                                        if primary else 'Copied or third-party fields are inventoried but excluded from primary semantic acceptance.')
        tokens = [('relative_path', rel), ('schema_id', doc.get('$id'))]
        discriminator = row.get('record_type')
        if discriminator:
            tokens.append(('record_discriminator', discriminator))
            if discriminator.startswith('agtxiv.v3.'):
                family = discriminator.removeprefix('agtxiv.v3.').split('/')[0]
                tokens.extend([('v3_family_literal', repr(family)), ('v3_family_literal', '"' + family + '"')])
        # File names alone are ambiguous across contract generations and are
        # deliberately not reported as exact consumers.
        consumers = []
        if primary:
            variants = [(label, tuple({token, quote(token, safe='/')}))
                        for label, token in tokens if token]
            for source, text in sorted(sources.items()):
                hits = []
                for label, values in variants:
                    matching = [value for value in values if value in text]
                    if not matching:
                        continue
                    for line_number, line in enumerate(text.splitlines(), 1):
                        if any(value in line for value in matching):
                            hits.append({'line': line_number, 'matched_by': label})
                if hits:
                    consumers.append({'path': source, 'matches': hits,
                                      'kind': 'CODE_REFERENCE' if Path(source).suffix in {'.py', '.js', '.mjs', '.cjs', '.ts', '.jsx', '.tsx', '.sh'} else 'DOCUMENT_OR_DATA_REFERENCE'})
        row['direct_static_references'] = consumers
        row['consumer_search_scope'] = 'PRIMARY_PROJECT_TEXT_EXACT_IDENTIFIERS; dynamic directory/glob consumers require group review' if primary else 'NOT_SCANNED_NON_PRIMARY_COPY_OR_THIRD_PARTY'
        row['group_consumers'] = semantic['groups'].get(row['classification'], {}).get('consumers', [])
        row['semantic_review'] = {'state': 'COMPATIBILITY_OR_AUXILIARY_SCHEMA_RECORDED_NOT_REAPPROVED',
                                  'review': semantic['groups'].get(row['classification'], {}).get('review', 'Classification needs manual review.')}
        if row['classification']=='PUBLIC_WEB_API_CONTRACT':
            row['semantic_review'] = semantic.get('public_api_files', {}).get(rel, row['semantic_review'])
        if primary and discriminator and discriminator.startswith('agtxiv.v3.'):
            family = discriminator.removeprefix('agtxiv.v3.').split('/')[0]
            found_families.add(family)
            row['semantic_review'] = family_reviews.get(family, {'state': 'MISSING_FAMILY_REVIEW'})
            fields = doc.get('properties', {}).get('payload', {}).get('properties', {})
            field_rows = []
            english = document_section(sources.get('schema v0.0/SCHEMA.md', ''), Path(rel).name)
            chinese = document_section(sources.get('schema v0.0/SCHEMA.zh-CN.md', ''), Path(rel).name)
            implementation_sources = [(path, sources.get(path, '')) for path in row['semantic_review'].get('implementation_paths', [])]
            for name, value in fields.items():
                field_rows.append({'name': name, 'required': name in doc['properties']['payload'].get('required', []),
                                   'description': value.get('description'),
                                   'english_field_table_present': '| `' + name + '` |' in english,
                                   'chinese_field_table_present': '| `' + name + '` |' in chinese,
                                   'implementation_literal_mentions': [path for path, text in implementation_sources if repr(name) in text or '"' + name + '"' in text],
                                   'literal_mention_limit': 'Text occurrence is navigation evidence, not field-specific enforcement or scientific adequacy.'})
            row['payload_field_review'] = field_rows
            missing = [f['name'] for f in field_rows if not f['english_field_table_present'] or not f['chinese_field_table_present']]
            if missing:
                row['issues'].append({'code': 'BILINGUAL_FIELD_TABLE_GAP', 'fields': missing})
        elif not primary:
            row['semantic_review']['state'] = 'EXCLUDED_FROM_PRIMARY_SEMANTIC_ACCEPTANCE'
        if rel == 'schema v0.0/common.schema.json':
            shared = []
            for name, value in doc.get('$defs', {}).items():
                english = common_section(sources.get('schema v0.0/SCHEMA.md', ''), name)
                chinese = common_section(sources.get('schema v0.0/SCHEMA.zh-CN.md', ''), name)
                fields = [{'name': field, 'description': field_schema.get('description'),
                           'required': field in value.get('required', []),
                           'english_field_table_present': '| `' + field + '` |' in english,
                           'chinese_field_table_present': '| `' + field + '` |' in chinese}
                          for field, field_schema in value.get('properties', {}).items()]
                shared.append({'name': name, 'description': value.get('description'), 'fields': fields,
                               'review_boundary': 'Shared shape/description and bilingual field correspondence; record-specific semantic use is reviewed in each family.'})
                if any(not field['english_field_table_present'] or not field['chinese_field_table_present'] for field in fields):
                    row['issues'].append({'code': 'BILINGUAL_SHARED_FIELD_TABLE_GAP', 'shared_type': name})
            row['shared_value_field_review'] = shared

    missing_reviews = sorted(found_families - family_reviews.keys())
    obsolete_reviews = sorted(family_reviews.keys() - found_families)
    primary = [r for r in entries if r['primary_project_schema']]
    input_bindings = [{'path': r['path'], 'sha256': r['sha256'], 'byte_size': r['byte_size']} for r in entries]
    for rel, raw in [('tools/audit_schemas.py', auditor_raw), (REVIEW_PATH, semantic_raw)]:
        input_bindings.append({'path': rel, 'sha256': sha(raw), 'byte_size': len(raw)})
    input_bindings.extend(source_fingerprints)
    input_bindings.sort(key=lambda r: r['path'])
    changed_inputs = []
    for item in input_bindings:
        path = root / item['path']
        if not path.is_file() or path.is_symlink() or sha(path.read_bytes()) != item['sha256']:
            changed_inputs.append(item['path'])
    current_paths, _ = inventory(root)
    initial_schema_paths = {p.relative_to(root).as_posix() for p in schemas}
    current_schema_paths = {p.relative_to(root).as_posix() for p in current_paths if p.name.endswith('.schema.json')}
    changed_inputs.extend('SCHEMA_INVENTORY_CHANGED:' + path for path in sorted(initial_schema_paths ^ current_schema_paths))
    support = []
    for item in source_fingerprints:
        if not item['path'].startswith('schema v0.0/') and item['path']!='schemas/record-canonical-json-v1.profile.json':
            continue
        name = Path(item['path']).name
        support.append({**item, 'role': {
            'README.md': 'PACKAGE_ENTRY_AND_MAINTENANCE', 'INVARIANTS.md': 'MECHANICAL_VERSUS_SCIENTIFIC_BOUNDARIES',
            'SCHEMA.md': 'GENERATED_ENGLISH_FIELD_REFERENCE', 'SCHEMA.zh-CN.md': 'GENERATED_CHINESE_FIELD_REFERENCE',
            'manifest.json': 'EXACT_BYTE_PIN_MANIFEST', 'catalog.json': 'RECORD_FAMILY_AND_ROADMAP_INDEX',
            'evaluation-corpus.json': 'HISTORICAL_EVALUATION_INPUT_NOT_SCIENTIFIC_GROUND_TRUTH',
            'record-canonical-json-v1.profile.json': 'LEGACY_CANONICAL_SERIALIZATION_PROFILE_NOT_A_JSON_SCHEMA',
        }.get(name, 'PACKAGE_SUPPORT_REQUIRES_REVIEW')})
    return {'audit_format': 'agtxiv.schema-release-audit/1.0.0',
            'scope': 'READ_ONLY_OFFLINE_STRUCTURE_AND_EXPLICIT_BOUNDED_SEMANTIC_REVIEW',
            'scientific_acceptance': False, 'release_certification': False,
            'coverage': {'physical_schema_files': len(entries), 'primary_project_schemas': len(primary),
                         'primary_structure_passed': sum(not r['issues'] for r in primary),
                         'primary_reference_occurrences': sum(len(r.get('references', [])) for r in primary),
                         'generated_web_schema_copy_mismatches': sum(r['classification'] in {'GENERATED_WEB_SCHEMA_COPY','GENERATED_WEB_API_SCHEMA_COPY','GENERATED_WEB_BUILD_COPY'} and bool(r['issues']) for r in entries),
                         'openapi_documents': len(api_documents),
                         'openapi_component_schemas': sum(len(doc['components']) for doc in api_documents),
                         'openapi_operations': sum(len(doc['operations']) for doc in api_documents),
                         'v3_record_families': len(found_families), 'explicit_v3_family_reviews': len(found_families & family_reviews.keys()),
                         'v3_payload_fields': sum(len(r.get('payload_field_review', [])) for r in entries),
                         'v3_shared_value_types': sum(len(r.get('shared_value_field_review', [])) for r in entries),
                         'v3_shared_value_fields': sum(len(t['fields']) for r in entries for t in r.get('shared_value_field_review', [])),
                         'v3_shared_envelope_fields': len(next((d.get('properties', {}) for p,d in documents.items() if p=='schema v0.0/axis-assessment.schema.json'), {})),
                         'classification_counts': dict(sorted(Counter(r['classification'] for r in entries).items())),
                         'missing_family_reviews': missing_reviews, 'obsolete_family_reviews': obsolete_reviews},
            'limitations': [
                'A family review identifies interface meaning, inspected enforcement and remaining work; it is not a complete proof of every semantic invariant.',
                'Legacy, test, generated, nested-worktree and third-party schemas are inventoried separately; no old scientific status is upgraded.',
                'Static consumers are exact path, URI or discriminator text matches plus explicitly reviewed group consumers; dynamic references and runtime execution are not inferred.',
                'All refs resolve offline within the primary group or isolated copied/third-party groups. Copies cannot satisfy a missing primary dependency.',
                'Symlinks and dependency/internal directories are excluded explicitly; no source generator, TeX, build, remote fetch or scientific execution is performed.',
                'The script validates schema syntax and references, not every dataset instance; test execution and real scientific review are separate evidence.',
            ],
            'findings': semantic['findings'], 'cross_record_review': semantic['cross_record_review'],
            'schema_package_support_files': support,
            'public_api_documents': api_documents,
            'group_review': semantic['groups'], 'duplicate_ids': duplicates,
            'inputs_changed_during_scan': changed_inputs,
            'exclusions': sorted(excluded, key=lambda r: (r['path'], r['reason'])),
            'input_bindings': input_bindings, 'input_fingerprint': sha(encode(input_bindings)), 'schemas': entries}


def markdown(report):
    c = report['coverage']
    lines = ['# Schema release audit', '',
             'This is a reproducible structural inventory and a bounded interface review. It is **not** scientific acceptance, release certification, or a declaration that all planned services exist.', '',
             f"Primary project scope: **{c['primary_project_schemas']} schemas**; **{c['primary_structure_passed']}** have no reported structural/document-table issues. The scan found **{c['physical_schema_files']} physical schema files** including copies and third-party material. It resolved **{c['primary_reference_occurrences']} primary reference occurrences** offline.", '',
             f"V3 review denominator: **{c['explicit_v3_family_reviews']}/{c['v3_record_families']} record families**, **{c['v3_payload_fields']} payload fields** and **{c['v3_shared_value_fields']} fields in {c['v3_shared_value_types']} shared value types** inventoried against both generated field tables. The common record envelope has **{c['v3_shared_envelope_fields']} fields**. These counts describe review coverage, not scientific completion.", '',
             'Reproduce from the repository root:', '', '```bash',
             '.venv/bin/python -B tools/audit_schemas.py', '.venv/bin/python -B tools/audit_schemas.py --check', '```', '',
             'The JSON ledger contains every file, exact byte hash, dialect, reference result, field inventory, static consumer matches, maintained source and semantic-review boundary. `--check` fails when inputs or the generated reports differ. It never regenerates contracts.', '',
             f"Input fingerprint: `{report['input_fingerprint']}`.", '',
             '## Scope and classification', '', '| Classification | Files |', '|---|---:|']
    lines.extend(f'| {key} | {value} |' for key, value in c['classification_counts'].items())
    lines += ['', 'Nested worktrees resolve independently. Generated site files and scratch/reference dependencies cannot silently satisfy a main-project reference. The JSON ledger lists every excluded symlink, dependency directory and oversized/non-UTF8 consumer input.', '',
              f"The web API additionally contains **{c['openapi_component_schemas']} component schemas** and **{c['openapi_operations']} operations** in **{c['openapi_documents']} OpenAPI document(s)**. Component shapes and reference closure are checked separately; this is not a full OpenAPI validator or evidence that handlers conform at runtime.", '',
              '## Release findings', '', '| Finding | Evidence and consequence | Acceptance task |', '|---|---|---|']
    for finding in report['findings']:
        evidence = '<br>'.join(finding['evidence'])
        lines.append(f"| {finding['id']} · {finding['status']} | {finding['summary']}<br>{evidence} | {finding['acceptance']} |")
    lines += ['', '## Cross-record review', '', '| Boundary | Observed mechanism | Remaining verification |', '|---|---|---|']
    for row in report['cross_record_review']:
        lines.append(f"| {row['boundary']} | {row['observed']} | {row['remaining']} |")
    lines += ['', '## Public submission and analysis interfaces', '', '| Contract | Reviewed behavior | Runtime evidence still required |', '|---|---|---|']
    for row in report['schemas']:
        if row['classification']!='PUBLIC_WEB_API_CONTRACT':
            continue
        review = row['semantic_review']
        lines.append(f"| [{row['path']}](../../{quote(row['path'], safe='/')}) | {review.get('observed', review.get('review', 'Pending review'))} | {review.get('remaining', 'Runtime conformance review remains separate.')} |")
    lines += ['', '## All V3 record families', '', '| Family | Inspected contract meaning and enforcement | Remaining work |', '|---|---|---|']
    for row in report['schemas']:
        if 'payload_field_review' not in row:
            continue
        review = row['semantic_review']
        lines.append(f"| [{row['title']}](../../{quote(row['path'], safe='/')}) | {review.get('observed', 'MISSING REVIEW')} | {review.get('remaining', 'MISSING REVIEW')} |")
    lines += ['', '## Interpretation and limits', '']
    lines.extend('- ' + limit for limit in report['limitations'])
    lines += ['', 'Maintained review input: [schema-semantic-review.json](schema-semantic-review.json). Detailed generated ledger: [schema-release-audit.json](schema-release-audit.json).', '']
    return '\n'.join(lines).encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    output = args.output_dir or root / 'docs/audits'
    report = collect(root)
    if report['inputs_changed_during_scan']:
        print(json.dumps({'status': 'INPUTS_CHANGED_RETRY_REQUIRED',
                          'paths': report['inputs_changed_during_scan']}, indent=2))
        return 1
    results = {OUTPUTS[0]: encode(report), OUTPUTS[1]: markdown(report)}
    stale = []
    for name, raw in results.items():
        path = output / name
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                stale.append(str(path))
        else:
            output.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    problems = [r['path'] for r in report['schemas'] if r['primary_project_schema'] and r['issues']]
    api_problems = [r['path'] for r in report['public_api_documents'] if r['issues']]
    missing = report['coverage']['missing_family_reviews'] + report['coverage']['obsolete_family_reviews']
    print(json.dumps({'coverage': report['coverage'], 'primary_problem_paths': problems,
                      'api_problem_paths': api_problems,
                      'stale_outputs': stale, 'input_fingerprint': report['input_fingerprint'],
                      'scientific_acceptance': False}, ensure_ascii=False, indent=2))
    return 1 if stale or problems or api_problems or missing or report['coverage']['generated_web_schema_copy_mismatches'] else 0


if __name__ == '__main__':
    sys.exit(main())
