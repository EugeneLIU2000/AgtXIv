"""Offline schema bundle, exact references and bounded cross-record validation.

This module checks supplied records and bytes. It cannot certify whether an
agent actually observed an experiment or whether a mathematical interpretation
is correct. Identity assurance is checked only against an explicit caller-held
AuthorityContext; fields supplied by a producer cannot authenticate themselves.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from agtxiv_v2.contracts.canonical import (
    ParsedCanonicalValue, build_canonical_value, parse_canonical_json, canonical_bytes,
)

REF_KEYS = frozenset({'record_type', 'record_id', 'revision', 'content_hash'})
AXES = ('source_fidelity', 'mathematical_correctness', 'formal_alignment',
        'semantic_applicability', 'empirical_support', 'computational_reproducibility')
ROOT = Path(__file__).resolve().parents[2]
MAX_DOCUMENT_BYTES = 32 * 1024 * 1024
MAX_RECORDS = 10000


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Issue:
    code: str
    record_id: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Issue, ...]
    record_count: int
    byte_artifacts_checked: bool
    authority_checked: bool
    scope: str = 'SUPPLIED_RECORD_CONTRACTS'
    limitations: tuple[str, ...] = (
        'Contract checks do not establish mathematical or scientific correctness.',
        'Input completeness outside the supplied scope is not established.',
        'Identity is checked only against caller-supplied trusted attestations when present.',
    )

    @property
    def valid(self) -> bool:
        return not self.issues

    def require_valid(self) -> None:
        if self.issues:
            raise ContractError('\n'.join(f'{i.code} {i.record_id}{i.path}: {i.message}' for i in self.issues))


@dataclass(frozen=True)
class SuppliedArtifact:
    artifact_id: str
    media_type: str
    data: bytes

    def reference(self, path_hint: str | None = None) -> dict:
        value = {'artifact_id': self.artifact_id, 'media_type': self.media_type,
                 'byte_size': len(self.data), 'sha256': digest(self.data)}
        if path_hint is not None:
            value['path_hint'] = path_hint
        return value


@dataclass(frozen=True)
class ExecutionAttestation:
    """Caller-held execution evidence; do not construct from the record itself."""
    principal_id: str
    role: str
    visible_input_refs: tuple[dict, ...]
    assurance: str = 'LOCALLY_ATTESTED'


@dataclass(frozen=True)
class AuthorityContext:
    """Trusted locally supplied identities, roles and policy authorization.

    This is a capability passed by the integrating caller, not a cryptographic
    or institutional identity provider. A malicious caller remains outside this
    Python process's trust boundary.
    """
    executions: Mapping[str, ExecutionAttestation]
    principal_aliases: Mapping[str, str] = field(default_factory=dict)
    authorized_policy_hashes: frozenset[str] = frozenset()

    def principal(self, identifier: str) -> str:
        seen = set()
        while identifier in self.principal_aliases:
            if identifier in seen:
                raise ContractError('Cyclic trusted principal alias map')
            seen.add(identifier)
            identifier = self.principal_aliases[identifier]
        return identifier


def digest(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise ContractError('Raw artifact hashing requires bytes')
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    parsed = build_canonical_value(value)
    if not isinstance(parsed, ParsedCanonicalValue):
        raise ContractError(f'Canonical JSON rejected: {parsed}')
    return canonical_bytes(parsed)


def parse(raw: bytes) -> Any:
    if type(raw) is not bytes or len(raw) > MAX_DOCUMENT_BYTES:
        raise ContractError('JSON input must be bytes within the document limit')
    parsed = parse_canonical_json(raw)
    if not isinstance(parsed, ParsedCanonicalValue):
        raise ContractError(f'Canonical JSON rejected: {parsed}')
    return parsed.to_python()


def detached(value: Any) -> Any:
    return parse(canonical(value))


def content_hash(record: dict) -> str:
    if type(record) is not dict:
        raise ContractError('A record must be an object')
    return digest(canonical({k: v for k, v in record.items() if k != 'content_hash'}))


def exact_ref(record: dict) -> dict:
    return {k: record[k] for k in ('record_type', 'record_id', 'revision', 'content_hash')}


def validate_exact_ref(reference: dict) -> None:
    """Reject malformed identities before Python equality, hashing or caching."""
    if (type(reference) is not dict or set(reference) != REF_KEYS
            or type(reference['revision']) is not int
            or not 1 <= reference['revision'] <= 9007199254740991
            or any(type(reference[k]) is not str for k in REF_KEYS - {'revision'})):
        raise ContractError('Expected an exact record reference')


def ref_key(reference: dict) -> tuple:
    return tuple(reference[k] for k in ('record_type', 'record_id', 'revision', 'content_hash'))


def kind(record: dict) -> str:
    return record['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0')


def _walk(value: Any, path: str = ''):
    if isinstance(value, dict):
        yield path, value
        for k, v in value.items():
            yield from _walk(v, path + '/' + k.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, path + '/' + str(i))


class SchemaBundle:
    def __init__(self, directory: Path | str | None = None):
        self.directory = Path(directory) if directory is not None else ROOT / 'schema v0.0'
        self.manifest = parse((self.directory / 'manifest.json').read_bytes())
        self.bundle_hash = digest(canonical(self.manifest))
        self.schemas: dict[str, dict] = {}
        self.by_type: dict[str, dict] = {}
        resources = []
        for entry in self.manifest['schemas']:
            path = Path(entry['path'])
            if path.name != entry['path'] or path.is_absolute():
                raise ContractError('Manifest schema paths must be direct child filenames')
            target = self.directory / path
            if target.is_symlink():
                raise ContractError('Schema symlink rejected')
            raw = target.read_bytes()
            if digest(raw) != entry['sha256']:
                raise ContractError('Schema bytes differ from the bundle manifest: ' + str(path))
            schema = parse(raw)
            if schema.get('$id') != entry['uri'] or schema['$id'] in self.schemas:
                raise ContractError('Schema identity is missing, duplicated or mismatched')
            Draft202012Validator.check_schema(schema)
            self.schemas[schema['$id']] = schema
            resources.append((schema['$id'], Resource.from_contents(schema)))
            if entry['record_type'] is not None:
                if entry['record_type'] in self.by_type:
                    raise ContractError('Duplicate record discriminator')
                if schema['properties']['record_type'].get('const') != entry['record_type']:
                    raise ContractError('Manifest/schema discriminator mismatch')
                self.by_type[entry['record_type']] = schema
        if len(self.by_type) != self.manifest['record_count']:
            raise ContractError('Bundle record count mismatch')
        def no_network(uri):
            raise NoSuchResource(ref=uri)
        self.registry = Registry(retrieve=no_network).with_resources(resources)
        self.validators = {t: Draft202012Validator(s, registry=self.registry, format_checker=FormatChecker())
                           for t, s in self.by_type.items()}
        # Eagerly check all reference URIs, including common definitions.
        resolver = self.registry.resolver()
        for schema in self.schemas.values():
            for _, item in _walk(schema):
                if '$ref' in item:
                    try:
                        resolver.lookup(item['$ref'])
                    except Exception as error:
                        raise ContractError('Unresolved offline schema reference: ' + item['$ref']) from error

    def validate_record(self, value: dict | bytes) -> tuple[Issue, ...]:
        try:
            record = parse(value) if isinstance(value, bytes) else detached(value)
        except ContractError as error:
            return (Issue('INVALID_JSON', '', '', str(error)),)
        if not isinstance(record, dict):
            return (Issue('INVALID_RECORD', '', '', 'Record must be an object'),)
        rid = str(record.get('record_id', ''))
        validator = self.validators.get(record.get('record_type'))
        if validator is None:
            return (Issue('UNKNOWN_RECORD_TYPE', rid, '/record_type', 'Unknown or unversioned discriminator'),)
        issues = []
        for error in sorted(validator.iter_errors(record), key=lambda e: repr(list(e.absolute_path))):
            pointer = '/' + '/'.join(str(x) for x in error.absolute_path)
            issues.append(Issue('SCHEMA', rid, pointer, error.message))
        if record.get('schema_bundle_hash') != self.bundle_hash:
            issues.append(Issue('SCHEMA_BUNDLE_MISMATCH', rid, '/schema_bundle_hash', 'Wrong exact schema bundle'))
        if record.get('content_hash') != content_hash(record):
            issues.append(Issue('RECORD_HASH_MISMATCH', rid, '/content_hash', 'Record bytes do not match the exact content hash'))
        return tuple(issues)

    def make_record(self, name: str, record_id: str, payload: dict, *, producer: dict,
                    policy_ref: dict | None, input_refs: Iterable[dict] = (), revision: int = 1,
                    created_at: str | None = None, data_class: str = 'RESEARCH') -> dict:
        """Construct and shape-check a candidate; this does not authenticate it."""
        if created_at is None:
            created_at = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
        record = {'record_type': 'agtxiv.v3.' + name + '/0.0.0', 'record_id': record_id,
                  'revision': revision, 'created_at': created_at, 'data_class': data_class,
                  'schema_bundle_hash': self.bundle_hash, 'producer': producer,
                  'policy_ref': policy_ref, 'input_refs': list(input_refs), 'payload': payload}
        record = detached(record)
        record['content_hash'] = content_hash(record)
        issues = self.validate_record(record)
        if issues:
            raise ContractError('\n'.join(f'{x.code} {x.path}: {x.message}' for x in issues))
        return record


class RecordSet:
    """Detached supplied inputs; public record access always returns fresh copies.

    The integrating Python caller is trusted. This is not a sandbox against a
    caller modifying private attributes or replacing the validator itself.
    """
    def __init__(self, bundle: SchemaBundle, records: Iterable[dict | bytes],
                 artifacts: Iterable[SuppliedArtifact] = (), *, authority: AuthorityContext | None = None):
        self.bundle = bundle
        supplied = []
        for record in records:
            if len(supplied) >= MAX_RECORDS:
                raise ContractError('Supplied record count limit exceeded')
            supplied.append(parse(record) if isinstance(record, bytes) else detached(record))
        self._records = tuple(supplied)
        self._artifacts = {}
        for artifact in artifacts:
            if artifact.artifact_id in self._artifacts:
                raise ContractError('Duplicate supplied artifact identity: ' + artifact.artifact_id)
            if type(artifact.data) is not bytes:
                raise ContractError('Supplied artifacts require unmodified bytes')
            self._artifacts[artifact.artifact_id] = artifact
        self.authority = authority
        self._index: dict[tuple, dict] = {}
        self._initial_issues = []
        for record in self._records:
            issues = bundle.validate_record(record)
            self._initial_issues.extend(issues)
            if issues:
                continue
            reference = exact_ref(record)
            identity = ref_key(reference)[:3]
            if identity in self._index:
                self._initial_issues.append(Issue('DUPLICATE_IDENTITY', record['record_id'], '', 'Duplicate supplied record identity/revision'))
            else:
                self._index[identity] = record

    @property
    def records(self) -> tuple[dict, ...]:
        return tuple(detached(r) for r in self._records)

    def resolve(self, reference: dict) -> dict:
        validate_exact_ref(reference)
        target = self._index.get(ref_key(reference)[:3])
        if target is None or exact_ref(target) != reference:
            raise ContractError('Unresolved, mistyped or stale exact reference: ' + str(reference.get('record_id')))
        return detached(target)

    def artifact(self, reference: dict) -> bytes:
        target = self._artifacts.get(reference['artifact_id'])
        if target is None:
            raise ContractError('Missing supplied byte artifact: ' + reference['artifact_id'])
        expected = target.reference()
        if any(reference.get(k) != v for k, v in expected.items()):
            raise ContractError('Artifact type, size or raw hash mismatch: ' + reference['artifact_id'])
        return target.data

    def validate(self, *, require_artifacts: bool = True) -> ValidationReport:
        issues = list(self._initial_issues)
        if issues:
            return ValidationReport(tuple(issues), len(self.records), False, False)
        edges = defaultdict(set)
        for record in self.records:
            rid = record['record_id']
            for path, item in _walk(record):
                try:
                    if set(item) == REF_KEYS:
                        target = self.resolve(item)
                        edges[ref_key(exact_ref(record))].add(ref_key(exact_ref(target)))
                    elif {'artifact_id','sha256','byte_size','media_type'} <= item.keys():
                        if require_artifacts:
                            self.artifact(item)
                except ContractError as error:
                    issues.append(Issue('EXACT_REFERENCE', rid, path, str(error)))
        if issues:
            return ValidationReport(tuple(issues), len(self.records), require_artifacts, False)
        # Full exact input/reference closure cannot contain a circular identity.
        degrees = {ref_key(exact_ref(r)): len(edges[ref_key(exact_ref(r))]) for r in self.records}
        parents = defaultdict(set)
        for owner, dependencies in edges.items():
            for dependency in dependencies:
                parents[dependency].add(owner)
        queue = deque(k for k,v in degrees.items() if v == 0)
        visited = 0
        while queue:
            child = queue.popleft()
            visited += 1
            for parent in parents[child]:
                degrees[parent] -= 1
                if degrees[parent] == 0:
                    queue.append(parent)
        if visited != len(degrees):
            issues.append(Issue('CYCLIC_RECORD_REFERENCES', '', '', 'Exact records must have acyclic creation dependencies'))
            return ValidationReport(tuple(issues), len(self.records), require_artifacts, False)
        for record in self.records:
            issues.extend(self._semantic(record, require_artifacts))
            if self.authority is not None:
                issues.extend(self._authority(record))
        return ValidationReport(tuple(issues), len(self.records), require_artifacts, self.authority is not None)

    def _review_producers(self, references: Iterable[dict]) -> set[str]:
        """Include content authors hidden behind aggregate assembly records.

        This follows selected content fields, not every historical review or
        policy dependency: reviewing an earlier review is a distinct activity.
        """
        content_fields={
            'argument-snapshot':('node_refs','inference_refs','context_refs','math_refs','proof_plan_refs'),
            'proof-plan':('node_refs','inference_refs'),
            'formal-check':('attempt_ref',),
            'release-manifest':('record_refs','source_ref'),
            'paper-release':('manifest_ref',),
        }
        pending=list(references)
        seen=set()
        result=set()
        while pending:
            reference=pending.pop()
            key=ref_key(reference)
            if key in seen:
                continue
            seen.add(key)
            record=self.resolve(reference)
            result.add(record['producer']['principal_id'])
            for field_name in content_fields.get(kind(record),()):
                value=record['payload'][field_name]
                pending.extend(value if isinstance(value,list) else [value])
        return result

    def _semantic(self, record: dict, require_artifacts: bool) -> list[Issue]:
        issues=[]
        name=kind(record)
        p=record['payload']
        def fail(code, message, path='/payload'):
            issues.append(Issue(code, record['record_id'], path, message))
        def target(reference):
            return self.resolve(reference)
        def payload(reference):
            return target(reference)['payload']
        def keys(refs):
            return [ref_key(r) for r in refs]
        def unique(values, label):
            if len(values)!=len(set(values)):
                fail('DUPLICATE_MEMBER', label + ' must not contain duplicate identities')
        def same(a,b,label):
            if a!=b:
                fail('BINDING_MISMATCH',label)
        # Exact identity sets are not silently deduplicated.
        for path,item in _walk(p):
            for field_name,value in item.items():
                if isinstance(value,list) and value and all(isinstance(v,dict) and set(v)==REF_KEYS for v in value):
                    unique(keys(value),path+'/'+field_name)
        review=p.get('review')
        if review:
            producer_ids=self._review_producers(review['reviewed_refs'])
            if not producer_ids <= set(review['producer_principal_ids']):
                fail('REVIEW_PRODUCER_OMITTED','Review must include all actual producers of the exact reviewed records')
            if record['producer']['principal_id'] in set(review['producer_principal_ids']):
                fail('SELF_REVIEW','A producer cannot independently review its own content')
            if not set(keys(review['reviewed_refs']))<=set(keys(record['producer']['visible_input_refs'])):
                fail('REVIEW_VISIBILITY','Every exact reviewed object must be in the recorded visible inputs')
            if review['independence']=='UNESTABLISHED' and (
                p.get('outcome') in {'SUPPORTED','ACCEPTED','ALIGNED','ALLOW','KERNEL_CHECKED'} or
                p.get('decision')=='ACCEPT' or p.get('result') in {'SUPPORTED','PARTIALLY_SUPPORTED','COUNTEREVIDENCE'}):
                fail('INDEPENDENCE_UNESTABLISHED','Positive assessed authority needs an established review boundary')
        if name=='source-snapshot':
            unique([u['unit_id'] for u in p['units']],'source unit IDs')
            unique([u['relative_path'] for u in p['units']],'source paths')
            if p['paper_version'].strip().lower() in {'latest','current','head','main'}:
                fail('FLOATING_SOURCE','A source version must be exact')
        elif name=='source-span':
            source=payload(p['source_ref'])
            def artifact_identity(a):
                return tuple(a[k] for k in ('artifact_id','media_type','sha256','byte_size'))
            allowed_artifacts=[u['artifact'] for u in source['units']]
            if p['locator_kind']=='TRANSFORMED_TEXT':
                transformation=payload(p['transformation_ref'])
                same(transformation['source_ref'],p['source_ref'],'Transformed span uses a different source')
                allowed_artifacts=transformation['outputs']
            if not any(artifact_identity(a)==artifact_identity(p['artifact']) for a in allowed_artifacts):
                fail('SPAN_SOURCE_MISMATCH','Span bytes must belong to the exact source snapshot')
            if p['locator_kind']=='PDF_REGION':
                box=p['pdf_region']
                try:
                    x0,y0,x1,y1=(Decimal(box[c]) for c in ('x0','y0','x1','y1'))
                    if not all(x.is_finite() for x in (x0,y0,x1,y1)) or not (0<=x0<x1<=1 and 0<=y0<y1<=1):
                        fail('PDF_REGION_BOUNDS','PDF coordinates must describe a nonempty normalized page region')
                except (InvalidOperation,ValueError):
                    fail('PDF_REGION_BOUNDS','Invalid decimal PDF region coordinate')
            elif not 0<=p['byte_start']<p['byte_end']<=p['artifact']['byte_size']:
                fail('SPAN_BOUNDS','Invalid nonempty half-open source span')
            elif require_artifacts and digest(self.artifact(p['artifact'])[p['byte_start']:p['byte_end']])!=p['span_sha256']:
                fail('SPAN_HASH','Selected source bytes do not match the span digest')
        elif name=='paper-structure':
            unit_ids={u['unit_id'] for u in payload(p['source_ref'])['units']}
            if p['main_unit_id'] not in unit_ids or not set(p['unclassified_unit_ids'])<=unit_ids:
                fail('STRUCTURE_MEMBERSHIP','Unknown main or unclassified source unit')
            for edge in p['edges']:
                if not {edge['source_unit_id'],edge['target_unit_id']}<=unit_ids:
                    fail('STRUCTURE_MEMBERSHIP','Document edge points outside the supplied source')
        elif name=='agentization-plan':
            same(set(p['source_unit_ids']),{u['unit_id'] for u in payload(p['source_ref'])['units']},'Plan must account for the entire supplied source inventory')
            unique(p['source_unit_ids'],'plan source units')
        elif name=='inventory-discovery':
            plan=payload(p['plan_ref'])
            all_units=p['classified_unit_ids']+p['unclassified_unit_ids']
            unique(all_units,'discovery source partition')
            same(set(all_units),set(plan['source_unit_ids']),'Discovery must partition the exact planned source denominator')
            unique([o['obligation_id'] for o in p['obligations']],'obligations')
            for o in p['obligations']:
                if not set(o['source_unit_ids'])<=set(plan['source_unit_ids']):
                    fail('OBLIGATION_SOURCE','Obligation points outside the plan')
            same(payload(p['structure_ref'])['source_ref'],plan['source_ref'],'Discovery structure uses a different source')
        elif name=='scope-decision':
            if p['discovery_ref'] not in p['review']['reviewed_refs']:
                fail('REVIEW_TARGET','Scope review does not bind the exact discovery')
        elif name=='frozen-scope':
            decision=payload(p['decision_ref'])
            same(decision['discovery_ref'],p['discovery_ref'],'Scope decision targets a different discovery')
            if decision['decision']!='ACCEPT':
                fail('UNACCEPTED_SCOPE','A frozen scope requires an accepting independent decision')
            discovery=payload(p['discovery_ref'])
            same(discovery['plan_ref'],p['plan_ref'],'Scope uses a different plan')
            same(discovery['obligations'],p['obligations'],'Frozen obligations must equal the reviewed discovery')
            unique([o['obligation_id'] for o in p['obligations']],'frozen obligations')
            profile=payload(payload(p['plan_ref'])['profile_ref'])
            if not set(profile['required_stages'])<={o['stage'] for o in p['obligations']}:
                fail('MISSING_PROFILE_STAGE','Frozen scope omits mandatory profile work stages')
            if not set(profile['success_required_stages'])<={o['stage'] for o in p['obligations'] if o['requirement']=='SUCCESS_REQUIRED'}:
                fail('WEAKENED_PROFILE_STAGE','Frozen scope downgrades a mandatory success stage to accounting only')
            if p['predecessor_ref']:
                previous=payload(p['predecessor_ref'])
                removed={o['obligation_id'] for o in previous['obligations']}-{o['obligation_id'] for o in p['obligations']}
                accounted=set()
                for r in p['removed_obligation_dispositions']:
                    d=target(r)
                    if kind(d)!='obligation-disposition' or d['payload']['scope_ref']!=p['predecessor_ref']:
                        fail('REMOVAL_ACCOUNTING','Removed obligations need dispositions on the exact prior scope')
                    else:
                        accounted.add(d['payload']['obligation_id'])
                same(removed,accounted,'Every removed obligation needs exact retained accounting')
                if removed and not set(keys([p['predecessor_ref']]+p['removed_obligation_dispositions']))<=set(keys(decision['review']['reviewed_refs'])):
                    fail('UNREVIEWED_SCOPE_REMOVAL','Independent freeze decision must examine the previous scope and every removal disposition')
        elif name=='obligation-disposition':
            obligations={o['obligation_id']:o for o in payload(p['scope_ref'])['obligations']}
            if p['obligation_id'] not in obligations:
                fail('OBLIGATION_MEMBERSHIP','Disposition not in the frozen scope')
            if p['outcome']=='COMPLETED' and not p['result_refs']:
                fail('MISSING_RESULT','Completed work must identify an actual result')
            if p['previous_ref']:
                prev=payload(p['previous_ref'])
                same((prev['scope_ref'],prev['obligation_id']),(p['scope_ref'],p['obligation_id']),'Disposition history changes its obligation')
        elif name=='scientific-claim':
            unique([c['component_id'] for c in p['components']],'claim components')
            if any(s not in p['source_span_refs'] for c in p['components'] for s in c['source_span_refs']):
                fail('COMPONENT_PROVENANCE','Component source not present in claim provenance')
        elif name=='claim-component-map':
            component_ids=[c['component_id'] for c in payload(p['claim_ref'])['components']]
            unique([m['component_id'] for m in p['mappings']],'component mapping')
            same(set(component_ids),{m['component_id'] for m in p['mappings']},'Map must account for every exact source component')
            for m in p['mappings']:
                if m['disposition']=='MAPPED' and not (m['math_refs'] or m['semantic_refs'] or m['evidence_refs']):
                    fail('EMPTY_MAPPING','A mapped component requires an actual target')
                if m['disposition'] in {'RESIDUAL','UNRESOLVED'} and not m['residual']:
                    fail('MISSING_RESIDUAL','An unresolved component must preserve the missing meaning')
            if p['coverage']=='COMPLETE' and any(m['disposition']=='UNRESOLVED' for m in p['mappings']):
                fail('COVERAGE_OVERCLAIM','Unresolved components cannot imply complete accounting')
        elif name=='math-claim':
            if p['exactness']!='EXACT' and not p['approximation_error']:
                fail('MISSING_APPROXIMATION','Approximate targets need explicit error/regime information')
            source=target(p['claim_ref'])
            if kind(source)=='scientific-claim':
                if not set(p['component_ids'])<={c['component_id'] for c in source['payload']['components']}:
                    fail('MATH_COMPONENT','MathClaimIR references nonexistent original components')
        elif name=='inference-step':
            if p['conclusion_ref'] in p['premise_refs']:
                fail('CIRCULAR_INFERENCE','Conclusion cannot be its own premise')
            if p['rule']=='ASSUMPTION_DISCHARGE' and not p['discharged_context_refs']:
                fail('MISSING_DISCHARGE','Discharge rule must identify the discharged context')
            discharge_rules={'ASSUMPTION_DISCHARGE','CONTRADICTION','CASE_SPLIT','INDUCTION'}
            if p['discharged_context_refs'] and p['rule'] not in discharge_rules:
                fail('INVALID_DISCHARGE_RULE','This rule cannot discharge a local assumption context')
            if p['discharged_context_refs'] and not p['rule_evidence_refs']:
                fail('MISSING_DISCHARGE_EVIDENCE','Scope discharge requires explicit rule obligations and evidence')
            for discharged in p['discharged_context_refs']:
                if payload(discharged)['parent_ref']!=p['context_ref']:
                    fail('DISCHARGE_PARENT','A discharge must return to its immediate enclosing context')
            context=p['context_ref']
            ancestors=[]
            while context:
                ancestors.append(context)
                context=payload(context)['parent_ref']
            for premise in p['premise_refs']:
                pc=payload(premise)['context_ref']
                allowed_discharge=(p['rule'] in discharge_rules and p['rule_evidence_refs'] and pc in p['discharged_context_refs'])
                if pc and pc not in ancestors and not allowed_discharge:
                    fail('SCOPE_ESCAPE','A local premise escapes its valid context without explicit discharge')
            conclusion_context=payload(p['conclusion_ref'])['context_ref']
            if conclusion_context!=p['context_ref']:
                fail('CONCLUSION_SCOPE','Conclusion context must equal the resulting inference context')
            if p['rule'] in {'INDUCTION','CASE_SPLIT'} and not p['rule_evidence_refs']:
                fail('RULE_OBLIGATION','Special inference rules require explicit condition evidence')
        elif name=='proof-plan':
            obligations={o['obligation_id'] for o in payload(p['scope_ref'])['obligations']}
            if not set(p['required_obligation_ids'])<=obligations:
                fail('PROOF_SCOPE','Required proof obligation is absent from the exact frozen scope')
            node_keys=set(keys(p['node_refs']))
            if ref_key(p['conclusion_ref']) not in node_keys:
                fail('PROOF_MEMBERSHIP','Conclusion not included in proof plan')
            adjacency=defaultdict(set)
            for r in p['inference_refs']:
                step=payload(r)
                if not set(keys(step['premise_refs']+[step['conclusion_ref']]))<=node_keys:
                    fail('PROOF_MEMBERSHIP','Inference uses nodes outside its proof route')
                for premise in step['premise_refs']:
                    adjacency[ref_key(premise)].add(ref_key(step['conclusion_ref']))
            indegree={n:0 for n in node_keys}
            for children in adjacency.values():
                for child in children:
                    if child in indegree: indegree[child]+=1
            queue=deque(n for n,d in indegree.items() if d==0)
            count=0
            while queue:
                n=queue.popleft(); count+=1
                for child in adjacency[n]:
                    if child in indegree:
                        indegree[child]-=1
                        if indegree[child]==0: queue.append(child)
            if count!=len(node_keys):
                fail('CIRCULAR_PROOF','This selected proof route contains cyclic justification')
            if not set(p['open_obligation_ids'])<=set(p['required_obligation_ids']):
                fail('UNKNOWN_OBLIGATION','Open obligation absent from the frozen proof requirements')
        elif name=='challenge-disposition':
            if p['challenge_ref'] not in p['review']['reviewed_refs']:
                fail('REVIEW_TARGET','Challenge disposition does not review its exact challenge')
            if p['outcome']=='RESOLVED' and not p['response_refs']:
                fail('MISSING_RESOLUTION','Resolved challenge requires actual response evidence')
        elif name=='argument-snapshot':
            nodes=set(keys(p['node_refs']))
            for r in p['proof_plan_refs']:
                plan=payload(r)
                same(plan['scope_ref'],p['scope_ref'],'Argument snapshot and proof route use different frozen scopes')
                if not set(keys(plan['node_refs']))<=nodes or not set(keys(plan['inference_refs']))<=set(keys(p['inference_refs'])):
                    fail('SNAPSHOT_CLOSURE','Proof route is not fully included in the argument snapshot')
            required_contexts={ref_key(payload(r)['context_ref']) for r in p['node_refs'] if payload(r)['context_ref']}
            if not required_contexts<=set(keys(p['context_refs'])):
                fail('SNAPSHOT_CONTEXT','Argument snapshot omits local assumption contexts')
        elif name=='argument-review':
            if p['snapshot_ref'] not in p['review']['reviewed_refs']:
                fail('REVIEW_TARGET','Argument review must bind the exact complete snapshot')
            snapshot=payload(p['snapshot_ref'])
            if not set(keys(p['proof_plan_refs']))<=set(keys(snapshot['proof_plan_refs'])):
                fail('REVIEW_ROUTE','Reviewed proof route absent from snapshot')
            if p['outcome']=='SUPPORTED':
                if snapshot['missing_items'] or any(payload(r)['open_obligation_ids'] for r in p['proof_plan_refs']):
                    fail('OPEN_PROOF_OBLIGATIONS','Supported argument review hides incomplete input or open obligations')
                dispositions={ref_key(payload(r)['challenge_ref']):payload(r)['outcome'] for r in snapshot['challenge_disposition_refs']}
                for cr in snapshot['challenge_refs']:
                    c=payload(cr)
                    if c['severity'] in {'MAJOR','CRITICAL'} and dispositions.get(ref_key(cr),'OPEN') not in {'RESOLVED','WITHDRAWN'}:
                        fail('OPEN_CHALLENGE','Supported argument has a blocking unresolved challenge')
        elif name=='formalization-packet':
            snapshot=payload(p['argument_ref'])
            same(p['scope_ref'],snapshot['scope_ref'],'Packet uses a different argument scope')
            if p['math_ref'] not in snapshot['math_refs'] or p['proof_plan_ref'] not in snapshot['proof_plan_refs']:
                fail('PACKET_BINDING','Packet mathematical target or route not in exact argument snapshot')
            same(p['open_obligation_ids'],payload(p['proof_plan_ref'])['open_obligation_ids'],'Packet must retain all selected open proof obligations')
            unique(p['expected_declarations'],'expected declarations')
        elif name=='formal-check':
            packet=payload(p['packet_ref'])
            same(payload(p['attempt_ref'])['packet_ref'],p['packet_ref'],'Checked attempt targets a different packet')
            same(p['environment_ref'],packet['environment_ref'],'Checker used a different exact environment')
            if p['attempt_ref'] not in p['review']['reviewed_refs']:
                fail('REVIEW_TARGET','Formal checker must review the exact generated attempt')
            unique([d['name'] for d in p['built_declarations']],'built declarations')
            if p['outcome']=='KERNEL_CHECKED':
                if not set(packet['expected_declarations'])<={d['name'] for d in p['built_declarations']}:
                    fail('TARGET_NOT_BUILT','Successful build did not inspect every expected declaration')
                allowed=set(payload(p['environment_ref'])['allowed_axioms'])
                for declaration in p['built_declarations']:
                    if not set(declaration['axioms'])<=allowed:
                        fail('FORBIDDEN_AXIOM','Transitive axiom not allowed by the exact environment')
        elif name=='alignment-assessment':
            if not set(keys(p['source_refs']+p['target_refs']))<=set(keys(p['review']['reviewed_refs'])):
                fail('REVIEW_TARGET','Alignment review must bind both exact endpoint sets')
            if p['outcome']=='ALIGNED' and any(c['relation']!='EQUIVALENT' for c in p['comparisons']):
                fail('ALIGNMENT_OVERCLAIM','Full alignment cannot hide stronger, weaker, incomparable or unknown conditions')
            source_kinds={kind(target(r)) for r in p['source_refs']}
            if p['comparison_kind'].startswith('SOURCE_') and not source_kinds<={'scientific-claim','derived-claim'}:
                fail('ALIGNMENT_ENDPOINT','Source-side alignment needs original or explicitly derived propositions')
            if p['comparison_kind'] in {'MATH_TO_FORMAL','SOURCE_TO_FORMAL'}:
                # A packet describes the intended formal target. Alignment must
                # instead inspect actual formal output from that exact packet.
                # Translation can be faithful even when its proof is unfinished
                # or a kernel check failed; no kernel-success gate belongs here.
                if p['comparison_kind']=='MATH_TO_FORMAL' and source_kinds!={'math-claim'}:
                    fail('ALIGNMENT_ENDPOINT','Math-to-formal alignment needs exact mathematical targets')
                positive_alignment=p['outcome'] in {'PARTIAL','ALIGNED'}
                covered=set()
                for formal_ref in p['target_refs']:
                    formal=target(formal_ref)
                    if kind(formal) not in {'formalization-attempt','formal-check'}:
                        fail('ALIGNMENT_FORMAL_ENDPOINT','Formal alignment needs an actual formal attempt or check')
                        continue
                    attempt=formal if kind(formal)=='formalization-attempt' else target(formal['payload']['attempt_ref'])
                    if positive_alignment and not attempt['payload']['artifacts']:
                        fail('ALIGNMENT_FORMAL_ARTIFACT','Formal alignment needs preserved formal output bytes')
                    packet=payload(attempt['payload']['packet_ref'])
                    expected=[packet['math_ref']] if p['comparison_kind']=='MATH_TO_FORMAL' else packet['source_claim_refs']
                    matching=set(keys(p['source_refs'])) & set(keys(expected))
                    if positive_alignment and not matching:
                        fail('ALIGNMENT_FORMAL_TARGET','Formal output packet does not address any stated source endpoint')
                    covered.update(matching)
                if positive_alignment and not set(keys(p['source_refs']))<=covered:
                    fail('ALIGNMENT_FORMAL_TARGET','Every source endpoint needs its own exact formal output binding')
        elif name=='axis-assessment':
            if not set(keys(p['target_refs']))<=set(keys(p['review']['reviewed_refs'])):
                fail('REVIEW_TARGET','Axis review must bind every assessed target')
            method_axes={'SOURCE_REVIEW':'source_fidelity','ARGUMENT_REVIEW':'mathematical_correctness',
                'KERNEL_AND_ALIGNMENT':'mathematical_correctness','FORMAL_ALIGNMENT':'formal_alignment',
                'SEMANTIC_REVIEW':'semantic_applicability','EMPIRICAL_REVIEW':'empirical_support',
                'REPRODUCTION_REVIEW':'computational_reproducibility'}
            if p['method'] in method_axes and method_axes[p['method']]!=p['axis']:
                fail('AXIS_METHOD','Evidence method cannot establish a different axis')
            if record['data_class']=='OBSERVED' and p['result'] in {'SUPPORTED','PARTIALLY_SUPPORTED','COUNTEREVIDENCE'}:
                from .obligations import support_closure
                if any(r['data_class']=='SYNTHETIC' for r in support_closure([exact_ref(record)],self.resolve)):
                    fail('SYNTHETIC_PROMOTION','Synthetic fixture cannot support an observed scientific assessment')
            if p['result'] in {'SUPPORTED','PARTIALLY_SUPPORTED'}:
                support=[target(r) for r in p['support_refs']]
                kinds={kind(r) for r in support}
                required={'ARGUMENT_REVIEW':{'argument-review'},'KERNEL_AND_ALIGNMENT':{'formal-check','alignment-assessment'},
                          'FORMAL_ALIGNMENT':{'alignment-assessment'},'SEMANTIC_REVIEW':{'semantic-context'},
                          'EMPIRICAL_REVIEW':{'empirical-evidence'},'REPRODUCTION_REVIEW':{'reproduction-record'},
                          'SOURCE_REVIEW':{'source-span'}}.get(p['method'],set())
                if not required or not required<=kinds:
                    fail('EVIDENCE_METHOD_MISMATCH','Positive axis conclusion lacks required typed evidence')
                for evidence in support:
                    outcome=evidence['payload'].get('outcome')
                    if kind(evidence)=='formal-check' and outcome!='KERNEL_CHECKED' and p['axis']=='mathematical_correctness':
                        fail('FAILED_EVIDENCE','Unsuccessful formal check cannot support mathematics')
                    if kind(evidence)=='alignment-assessment' and (
                            outcome not in {'ALIGNED','PARTIAL'} or
                            (outcome!='ALIGNED' and p['result']=='SUPPORTED')):
                        fail('FAILED_EVIDENCE','Unknown or misaligned evidence cannot establish support; partial alignment cannot establish full support')
                    if kind(evidence)=='reproduction-record' and outcome!='REPRODUCED':
                        fail('FAILED_EVIDENCE','Failed reproduction cannot establish reproducibility')
                    if kind(evidence)=='argument-review':
                        if outcome=='CONDITIONAL' and p['result']=='SUPPORTED':
                            fail('CONDITIONAL_PROMOTION','Conditional argument evidence cannot establish full mathematical support')
                        if not {canonical(c) for c in evidence['payload']['conditions']}<={canonical(c) for c in p['conditions']}:
                            fail('DROPPED_EVIDENCE_CONDITION','Axis assessment must retain every supporting argument condition')
                for assessed_ref in p['target_refs']:
                    matching=False
                    if p['method']=='SOURCE_REVIEW':
                        assessed=target(assessed_ref)
                        matching=kind(assessed)=='scientific-claim' and set(keys(assessed['payload']['source_span_refs']))<=set(keys(p['support_refs']))
                    elif p['method']=='ARGUMENT_REVIEW':
                        for evidence in support:
                            if kind(evidence)=='argument-review' and evidence['payload']['outcome'] in {'SUPPORTED','CONDITIONAL'}:
                                snapshot=payload(evidence['payload']['snapshot_ref'])
                                matching |= assessed_ref in snapshot['source_claim_refs']+snapshot['math_refs']
                    elif p['method']=='KERNEL_AND_ALIGNMENT':
                        for evidence in support:
                            if kind(evidence)!='formal-check' or evidence['payload']['outcome']!='KERNEL_CHECKED':
                                continue
                            packet=payload(evidence['payload']['packet_ref'])
                            if assessed_ref!=packet['math_ref'] and assessed_ref not in packet['source_claim_refs']:
                                continue
                            for alignment in support:
                                if kind(alignment)!='alignment-assessment' or alignment['payload']['outcome']!='ALIGNED':
                                    continue
                                a=alignment['payload']
                                expected_kind='MATH_TO_FORMAL' if assessed_ref==packet['math_ref'] else 'SOURCE_TO_FORMAL'
                                matching |= (a['comparison_kind']==expected_kind and assessed_ref in a['source_refs'] and
                                             (exact_ref(evidence) in a['target_refs'] or evidence['payload']['attempt_ref'] in a['target_refs']))
                    elif p['method']=='FORMAL_ALIGNMENT':
                        matching=any(kind(e)=='alignment-assessment' and
                                     e['payload']['comparison_kind'] in {'MATH_TO_FORMAL','SOURCE_TO_FORMAL'} and
                                     assessed_ref in e['payload']['source_refs']+e['payload']['target_refs'] for e in support)
                    elif p['method']=='SEMANTIC_REVIEW':
                        matching=any(kind(e)=='semantic-context' and (e['payload']['claim_ref']==assessed_ref or exact_ref(e)==assessed_ref) for e in support)
                    elif p['method']=='EMPIRICAL_REVIEW':
                        matching=any(kind(e)=='empirical-evidence' and assessed_ref in e['payload']['target_refs'] for e in support)
                    elif p['method']=='REPRODUCTION_REVIEW':
                        matching=any(kind(e)=='reproduction-record' and assessed_ref in e['payload']['target_refs'] for e in support)
                    if not matching:
                        fail('EVIDENCE_TARGET_MISMATCH','Positive evidence does not address every exact assessed target')
            if p['method']=='UNASSESSED' and p['result']!='NOT_ASSESSED':
                fail('UNASSESSED_PROMOTION','No assessment method cannot produce an assessed conclusion')
            if p['result']=='COUNTEREVIDENCE' and p['method']=='COUNTEREXAMPLE_REVIEW':
                examples=[target(r) for r in p['counterevidence_refs'] if kind(target(r))=='counterexample']
                if not all(any(e['payload']['target_ref']==r for e in examples) for r in p['target_refs']):
                    fail('COUNTEREXAMPLE_TARGET','Counterexamples must match the exact challenged proposition')
        elif name=='status-view':
            for r in p['assessment_refs']+p['conflicting_assessment_refs']:
                if p['target_ref'] not in payload(r)['target_refs']:
                    fail('STATUS_TARGET','Status view imports an assessment of a different target')
        elif name=='relation-assessment':
            if p['source_ref']==p['target_ref']:
                fail('SELF_RELATION','Relation endpoints must be distinct')
            if not {ref_key(p['source_ref']),ref_key(p['target_ref'])}<=set(keys(p['review']['reviewed_refs'])):
                fail('REVIEW_TARGET','Relation review must bind both exact endpoints')
            if p['outcome']=='ACCEPTED' and not p['witness_refs']:
                fail('MISSING_RELATION_WITNESS','An accepted relation needs exact comparison evidence')
        elif name=='baseline-snapshot':
            if p['knowledge_ref']:
                knowledge=payload(p['knowledge_ref'])
                if not set(keys(p['entry_refs']))<=set(keys(knowledge['entry_refs'])):
                    fail('BASELINE_MEMBERSHIP','Baseline entries do not belong to the exact prior knowledge snapshot')
        elif name=='contribution-delta':
            baseline=payload(p['baseline_ref'])
            if not set(keys(p['prior_refs']))<=set(keys(baseline['entry_refs'])):
                fail('DELTA_BASELINE','Compared prior results are absent from the frozen baseline')
            if not set(keys(p['current_refs']+p['prior_refs']))<=set(keys(p['review']['reviewed_refs'])):
                fail('REVIEW_TARGET','Contribution review must bind both current and prior results')
            if p['outcome']=='SUPPORTED':
                relations=[payload(r) for r in p['relation_refs']]
                if not relations or any(r['outcome']!='ACCEPTED' for r in relations):
                    fail('UNSUPPORTED_DELTA','Supported contribution needs accepted witnessed comparisons')
                endpoints=set(keys(p['current_refs']+p['prior_refs']))
                if any(not set(keys([r['source_ref'],r['target_ref']]))<=endpoints for r in relations):
                    fail('DELTA_RELATION','Comparison relation does not connect the stated contribution endpoints')
        elif name=='reuse-decision':
            if not set(keys([p['source_ref'],p['target_ref']]))<=set(keys(p['review']['reviewed_refs'])):
                fail('REVIEW_TARGET','Reuse review must bind both source result and intended use')
            if p['source_ref']==p['target_ref']:
                fail('SELF_REUSE','Reuse needs a distinct specified target use')
            if p['outcome']=='ALLOW' and any(c['relation'] not in {'EQUIVALENT','SOURCE_STRONGER'} for c in p['comparisons']):
                fail('UNSAFE_REUSE','Allow cannot bypass incompatible or unknown use conditions')
            dimensions={c['dimension'] for c in p['comparisons']}
            if p['outcome'] in {'ALLOW','CONDITIONAL'} and not {'OBJECT','ASSUMPTION','REGIME','EVIDENCE'}<=dimensions:
                fail('INCOMPLETE_REUSE','Use permission must explicitly compare objects, assumptions, regime and evidence')
            if p['outcome']=='CONDITIONAL' and not p['conditions']:
                fail('MISSING_REUSE_CONDITIONS','Conditional reuse must state the remaining target conditions')
            if p['outcome'] in {'ALLOW','CONDITIONAL'}:
                evidence=[target(r) for r in p['assessment_refs']]
                supporting=[r for r in evidence if kind(r)=='axis-assessment' and p['source_ref'] in r['payload']['target_refs'] and r['payload']['result'] in {'SUPPORTED','PARTIALLY_SUPPORTED'}]
                if not supporting:
                    fail('REUSE_EVIDENCE_TARGET','Reuse needs an assessment supporting its exact source result')
                if any(kind(r) not in {'axis-assessment','relation-assessment','environment-check'} for r in evidence):
                    fail('REUSE_EVIDENCE_TYPE','Raw data and source spans do not substitute for reuse assessments')
                for assessment in supporting:
                    if p['outcome']=='ALLOW' and assessment['payload']['result']!='SUPPORTED':
                        fail('REUSE_EVIDENCE_STRENGTH','Full permission cannot use partial source support')
                    if not {canonical(c) for c in assessment['payload']['conditions']}<={canonical(c) for c in p['conditions']}:
                        fail('DROPPED_REUSE_CONDITION','Reuse must retain source assessment conditions')
                if p['environment_check_ref'] and payload(p['environment_check_ref'])['outcome']!='COMPATIBLE':
                    fail('REUSE_ENVIRONMENT','Reuse cannot permit an incompatible or blocked formal environment')
                if p['outcome']=='ALLOW' and p['conflict_refs']:
                    fail('UNRESOLVED_REUSE_CONFLICT','Full permission requires resolving relevant limiting relations')
        elif name=='reproduction-record':
            protocol=payload(p['protocol_ref'])
            attempt=payload(p['attempt_ref'])
            if p['protocol_ref'] not in target(p['attempt_ref'])['input_refs']:
                fail('UNFROZEN_COMPARISON','Execution inputs must include the exact predetermined evidence protocol')
            same(p['comparison_rule'],protocol['comparison_rule'],'Reproduction changed its predetermined comparison rule')
            same(p['environment'],protocol['environment'],'Reproduction changed its predetermined environment')
            if not set(keys(p['target_refs']))<=set(keys(protocol['target_refs'])):
                fail('EVIDENCE_PROTOCOL_TARGET','Reproduction uses targets outside the frozen protocol')
        elif name=='evidence-protocol':
            if not set(p['obligation_ids'])<={o['obligation_id'] for o in payload(p['scope_ref'])['obligations']}:
                fail('EVIDENCE_OBLIGATION','Protocol obligations are absent from the exact frozen scope')
        elif name=='work-completion':
            for r in p['result_refs']:
                if not any(item==p['attempt_ref'] for _,item in _walk(target(r))):
                    fail('COMPLETION_BINDING','Completed result does not refer to the exact earlier execution')
        elif name=='release-manifest':
            scope=payload(p['scope_ref'])
            same(payload(scope['plan_ref'])['source_ref'],p['source_ref'],'Package source does not match frozen scope')
            same(payload(scope['plan_ref'])['profile_ref'],p['profile_ref'],'Package profile does not match frozen plan')
            disposition_list=[payload(r) for r in p['disposition_refs']]
            unique([d['obligation_id'] for d in disposition_list],'release dispositions')
            same({d['obligation_id'] for d in disposition_list},{o['obligation_id'] for o in scope['obligations']},'Package must account for every frozen obligation exactly once')
            for d in disposition_list:
                same(d['scope_ref'],p['scope_ref'],'Disposition uses a different scope revision')
            packaged=set(keys(p['record_refs']))
            if not set(keys(p['frontier_refs']+p['contribution_refs']+p['disposition_refs']))<=packaged:
                fail('PACKAGE_MEMBERSHIP','Package omits listed frontier, contribution or disposition records')
            # The manifest is a candidate, so honest unfinished mandatory work
            # remains representable. Its selected current branches and every
            # claimed completion still require exact, typed evidence.
            from .obligations import check_obligations
            accounting=check_obligations(self,p['scope_ref'],p['disposition_refs'],
                universe_refs=p['record_refs'],enforce_success=False,require_artifacts=require_artifacts)
            issues.extend(Issue(i.code,i.record_id,i.path,i.message) for i in accounting.issues)
        elif name=='release-audit':
            manifest=payload(p['manifest_ref'])
            if p['manifest_ref'] not in p['review']['reviewed_refs']:
                fail('REVIEW_TARGET','Audit must bind the exact candidate manifest')
            same(p['frontier_refs'],manifest['frontier_refs'],'Audit cannot suppress unresolved frontier')
            if p['recommendation']=='RECOMMEND_PROFILE_RELEASE':
                from .obligations import check_obligations
                success=check_obligations(self,manifest['scope_ref'],manifest['disposition_refs'],
                    universe_refs=manifest['record_refs'],enforce_success=True,require_artifacts=require_artifacts)
                issues.extend(Issue(i.code,i.record_id,i.path,i.message) for i in success.issues)
        elif name=='release-certificate':
            audit=target(p['audit_ref'])
            same(audit['payload']['manifest_ref'],p['manifest_ref'],'Certificate binds mismatched audit and candidate')
            if record['producer']['principal_id']==audit['producer']['principal_id']:
                fail('SELF_CERTIFICATION','Auditor cannot mechanically certify its own audit')
            if p['outcome']=='CERTIFIED':
                if audit['payload']['recommendation']!='RECOMMEND_PROFILE_RELEASE':
                    fail('UNRECOMMENDED_RELEASE','Certification needs a positive exact audit')
                if not {'EXACT_BINDING','AUDIT_RECOMMENDATION','ROLE_SEPARATION','PROFILE_CONFORMANCE'}<=set(p['checks']):
                    fail('MISSING_CERTIFICATION_CHECK','All four mandatory mechanical checks are required')
        elif name=='paper-release':
            cert=payload(p['certificate_ref'])
            if cert['outcome']!='CERTIFIED':
                fail('UNCERTIFIED_RELEASE','A paper release requires its exact successful certificate')
            same((cert['manifest_ref'],cert['audit_ref']),(p['manifest_ref'],p['audit_ref']),'Release does not match the certified package')
        elif name=='admission-decision':
            unique(keys([item['candidate_ref'] for item in p['items']]),'admission candidate universe')
            same(payload(p['before_ref'])['domain'],p['domain'],'Admission changes domain')
            manifest=payload(payload(p['release_ref'])['manifest_ref'])
            reviewed=set(keys(p['review']['reviewed_refs']))
            if not {ref_key(item['candidate_ref']) for item in p['items']}<=reviewed:
                fail('REVIEW_TARGET','Admission review must bind every exact candidate in its decision universe')
            for item in p['items']:
                if item['candidate_ref'] not in manifest['record_refs']:
                    fail('ADMISSION_PACKAGE','Candidate absent from exact release package')
                if item['decision']=='ACCEPT' and not item['assessment_refs']:
                    fail('UNASSESSED_ADMISSION','Accepted reusable record needs explicit admission evidence')
                if item['decision']=='ACCEPT':
                    addressed=False
                    for assessment_ref in item['assessment_refs']:
                        assessment=target(assessment_ref)
                        ap=assessment['payload']
                        if kind(assessment)=='axis-assessment':
                            addressed |= item['candidate_ref'] in ap['target_refs'] and ap['execution']=='COMPLETED' and ap['method']!='UNASSESSED'
                        elif kind(assessment)=='argument-review':
                            argument=payload(ap['snapshot_ref'])
                            addressed |= item['candidate_ref'] in [ap['snapshot_ref']]+argument['source_claim_refs']+argument['math_refs']+argument['node_refs']
                        elif kind(assessment)=='alignment-assessment':
                            addressed |= item['candidate_ref'] in ap['source_refs']+ap['target_refs']
                        elif kind(assessment)=='relation-assessment':
                            addressed |= item['candidate_ref'] in [ap['source_ref'],ap['target_ref']]
                    if not addressed:
                        fail('ADMISSION_EVIDENCE_TARGET','Admission assessment does not address this exact candidate')
        elif name=='knowledge-snapshot':
            entries=set(keys(p['entry_refs']))
            if p['predecessor_ref']:
                previous=payload(p['predecessor_ref'])
                same(previous['domain'],p['domain'],'Snapshot lineage changes domain')
                if not set(keys(previous['entry_refs']))<=entries or not set(keys(previous['relation_refs']))<=set(keys(p['relation_refs'])):
                    fail('DESTRUCTIVE_SNAPSHOT','Append-only snapshot cannot delete old records or conflicts')
                allowed=set(keys(previous['entry_refs']))
                allowed_relations=set(keys(previous['relation_refs']))
                allowed_releases=set(keys(previous['release_refs']))
                for decision_ref in p['admission_refs']:
                    decision=payload(decision_ref)
                    if decision['before_ref']==p['predecessor_ref']:
                        allowed.update(ref_key(item['candidate_ref']) for item in decision['items'] if item['decision']=='ACCEPT')
                        allowed_relations.update(ref_key(item['candidate_ref']) for item in decision['items'] if item['decision']=='ACCEPT' and kind(target(item['candidate_ref']))=='relation-assessment')
                        allowed_releases.add(ref_key(decision['release_ref']))
                    elif decision_ref not in previous['admission_refs']:
                        fail('SNAPSHOT_ADMISSION_BASE','New admission does not target the immediate prior snapshot')
                same(entries,allowed,'Snapshot additions must be exactly independently authorized entries')
                same(set(keys(p['relation_refs'])),allowed_relations,'Snapshot relations must retain every admitted relation and add no unadmitted relation')
                same(set(keys(p['release_refs'])),allowed_releases,'Snapshot backing releases must match its admission history')
                if not set(keys(previous['admission_refs']))<=set(keys(p['admission_refs'])):
                    fail('DESTRUCTIVE_SNAPSHOT','Snapshot cannot remove admission provenance')
            elif p['entry_refs'] or p['relation_refs'] or p['release_refs'] or p['admission_refs']:
                fail('NONEMPTY_GENESIS','Genesis snapshot is empty; additions require admission from a prior snapshot')
        elif name=='ingestion-receipt':
            candidate=keys(p['candidate_refs'])
            partitions=keys(p['accepted_refs']+p['rejected_refs']+p['blocked_refs'])
            unique(partitions,'ingestion candidate partition')
            same(set(candidate),set(partitions),'Every candidate must have exactly one disposition')
            decision=payload(p['decision_ref'])
            same(decision['before_ref'],p['before_ref'],'Ingestion decision uses a different prior snapshot')
            same(set(candidate),{ref_key(i['candidate_ref']) for i in decision['items']},'Receipt candidate set differs from the reviewed universe')
            if p['outcome']=='ABORTED':
                if p['accepted_refs'] or p['before_ref']!=p['after_ref']:
                    fail('PARTIAL_ABORT','Aborted transaction cannot mutate or accept entries')
            else:
                after=payload(p['after_ref'])
                same(after['predecessor_ref'],p['before_ref'],'Committed snapshot must extend the exact prior snapshot')
                expected_entries=set(keys(payload(p['before_ref'])['entry_refs']+p['accepted_refs']))
                same(set(keys(after['entry_refs'])),expected_entries,'Committed result does not contain exactly this transaction additions')
                if p['decision_ref'] not in after['admission_refs']:
                    fail('TRANSACTION_DECISION','Committed result does not bind the receipt admission decision')
                for field,outcome in [('accepted_refs','ACCEPT'),('rejected_refs','REJECT'),('blocked_refs','BLOCK')]:
                    same(set(keys(p[field])),{ref_key(i['candidate_ref']) for i in decision['items'] if i['decision']==outcome},'Committed receipt changes reviewed dispositions')
        elif name=='event':
            if p['previous_ref']:
                previous=payload(p['previous_ref'])
                same((p['stream_id'],p['sequence']),(previous['stream_id'],previous['sequence']+1),'Event sequence must be contiguous within one exact stream')
            elif p['sequence']!=1:
                fail('EVENT_GENESIS','First event must have sequence 1')
        elif name=='query-receipt':
            snapshot=payload(p['knowledge_ref'])
            entries=set(keys(snapshot['entry_refs']))
            if p['mode']=='PACKAGE_BACKED' and not set(keys(p['returned_refs']))<=entries:
                fail('QUERY_UNADMITTED','Package-backed answer cannot return unadmitted records')
            returned=set(keys(p['returned_refs']))
            relations=set(keys(p['relation_refs']))
            if not relations<=set(keys(snapshot['relation_refs'])):
                fail('QUERY_UNADMITTED_RELATION','Query relation set must belong to its exact knowledge snapshot')
            for relation_ref in snapshot['relation_refs']:
                r=payload(relation_ref)
                endpoints={ref_key(r['source_ref']),ref_key(r['target_ref'])}
                relevant=bool(returned & endpoints) or ref_key(relation_ref) in returned | relations
                if relevant and r['relation'] in {'CONFLICTING','INCOMPARABLE','CORRECTS','QUALIFIES','REFUTES'}:
                    if not endpoints<=returned or ref_key(relation_ref) not in relations:
                        fail('QUERY_CONFLICT_SUPPRESSION','Relevant conflict and both endpoint records must remain visible')
            for assertion in p['assertions']:
                if not set(keys(assertion['support_refs']))<=returned:
                    fail('ANSWER_PROVENANCE','Answer assertion cites a record absent from its exact returned set')
        return issues

    def _authority(self, record: dict) -> list[Issue]:
        context=self.authority
        assert context is not None
        issues=[]
        def fail(code,message):
            issues.append(Issue(code,record['record_id'],'/producer',message))
        producer=record['producer']
        attestation=context.executions.get(producer['execution_id'])
        if attestation is None:
            fail('UNATTESTED_EXECUTION','No caller-held identity evidence for this execution')
            return issues
        if context.principal(attestation.principal_id)!=context.principal(producer['principal_id']) or attestation.role!=producer['role']:
            fail('EXECUTION_IDENTITY_MISMATCH','Record producer differs from the trusted execution identity or role')
        if list(attestation.visible_input_refs)!=producer['visible_input_refs']:
            fail('INPUT_VISIBILITY_MISMATCH','Producer visibility differs from the independently recorded inputs')
        if producer['identity_assurance']!=attestation.assurance:
            fail('IDENTITY_ASSURANCE_MISMATCH','Producer cannot assert stronger or different identity evidence')
        if record['policy_ref']:
            policy=self.resolve(record['policy_ref'])
            if policy['content_hash'] not in context.authorized_policy_hashes:
                fail('UNAUTHORIZED_POLICY','The integrating authority did not authorize this exact policy')
            if context.principal(producer['principal_id']) not in {context.principal(x) for x in policy['payload']['allowed_principal_ids']}:
                fail('UNAUTHORIZED_PRINCIPAL','Principal not authorized by this exact policy')
            assurance_levels={'DECLARED':0,'LOCALLY_ATTESTED':1,'EXTERNALLY_ATTESTED':2}
            authoritative=(bool(record['payload'].get('review')) or kind(record) in {
                'release-certificate','paper-release','knowledge-snapshot','ingestion-receipt','backtranslation'})
            if authoritative and assurance_levels.get(attestation.assurance,-1)<assurance_levels[policy['payload']['minimum_identity_assurance']]:
                fail('INSUFFICIENT_IDENTITY_ASSURANCE','Decision identity evidence is below the exact policy minimum')
        review=record['payload'].get('review')
        if review:
            owner=context.principal(producer['principal_id'])
            actual={context.principal(p) for p in self._review_producers(review['reviewed_refs'])}
            actual.update(context.principal(p) for p in review['producer_principal_ids'])
            if owner in actual:
                fail('ALIASED_SELF_REVIEW','Different display names resolve to the same actual producer')
        expected={'scope-decision':'SCOPE_REVIEWER','argument-review':'ARGUMENT_REVIEWER',
                  'formal-check':'FORMAL_CHECKER','backtranslation':'BACKTRANSLATOR',
                  'alignment-assessment':'ALIGNMENT_REVIEWER','release-audit':'PAPER_AUDITOR',
                  'release-certificate':'CERTIFIER','admission-decision':'ADMISSION_REVIEWER',
                  'knowledge-snapshot':'KNOWLEDGE_SERVICE','ingestion-receipt':'KNOWLEDGE_SERVICE'}.get(kind(record))
        if expected and producer['role']!=expected:
            fail('WRONG_AUTHORITY_ROLE','Record requires role '+expected)
        if kind(record)=='release-certificate':
            auditor=self.resolve(record['payload']['audit_ref'])['producer']['principal_id']
            if context.principal(auditor)==context.principal(producer['principal_id']):
                fail('ALIASED_SELF_CERTIFICATION','Certificate actor is the same actual principal as the auditor')
            manifest_ref=record['payload']['manifest_ref']
            if context.principal(producer['principal_id']) in {context.principal(x) for x in self._review_producers([manifest_ref])}:
                fail('CERTIFIER_CONTENT_CONFLICT','Certifier also produced content in the candidate package')
        if kind(record)=='admission-decision':
            release=self.resolve(record['payload']['release_ref'])
            forbidden=self._review_producers([release['payload']['manifest_ref']])
            forbidden.update(self.resolve(release['payload'][field])['producer']['principal_id'] for field in ('audit_ref','certificate_ref'))
            if context.principal(producer['principal_id']) in {context.principal(x) for x in forbidden}:
                fail('ADMISSION_ROLE_CONFLICT','Admission reviewer participated in production, audit or certification of this package')
        if kind(record)=='backtranslation':
            forbidden={'source-snapshot','source-span','scientific-claim','derived-claim','math-claim','argument-snapshot','formalization-packet','alignment-assessment'}
            if any(kind(self.resolve(r)) in forbidden for r in producer['visible_input_refs']):
                fail('BACKTRANSLATION_UNBLINDED','Initial backtranslation visible inputs contain the expected source or alignment answer')
        return issues
