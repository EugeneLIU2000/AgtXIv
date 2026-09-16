"""Exact provisional source packages; static segmentation is not claim discovery.

Packages are ordinary retained artifacts, not knowledge snapshots or schema
records. Optional caller-authored V3 candidates use the existing RecordSet path.
No policy, identity, scope, review, admission or scientific status is fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Iterable

from .contracts import SuppliedArtifact, canonical, exact_ref, kind, parse
from .intake import LocalInspection, _relative
from .source import SourceError, verify_byte_span

PROFILE = 'agtxiv.v3.provisional-source-package/0.0.0'
MAX_SEGMENTS = 10_000
MAX_PACKAGE_BYTES = 8 * 1024 * 1024
MAX_QUERY_BYTES = 16 * 1024 * 1024
CANDIDATE_KINDS = frozenset({
    'source-snapshot', 'source-span', 'paper-structure', 'scientific-claim', 'math-claim', 'derived-claim', 'argument-node',
    'inference-step', 'dependency-binding', 'frontier-item', 'inventory-discovery',
})
QUESTIONS = (
    'Static line segmentation and lexical cues cover bytes, not semantic claims; comments, definitions and nonclaims are not independently semantically classified.',
    'Macros, external packages, missing includes and published rendering require independent review.',
    'PDFs, figures, bibliography, archives, code and data are retained without content or scientific execution.',
    'Publication participation, external source completeness and redistribution rights remain unverified.',
)


def _artifact(data: bytes, media_type: str) -> SuppliedArtifact:
    identity = hashlib.sha256(media_type.encode() + b'\0' + data).hexdigest()
    return SuppliedArtifact('artifact:candidate-' + identity, media_type, data)


def _span(path: str, data: bytes, start: int, end: int) -> dict:
    return {'path': path, 'start_byte': start, 'end_byte': end,
            'sha256': hashlib.sha256(data[start:end]).hexdigest()}



def _candidate_cues(line: bytes) -> dict:
    """Conservative lexical cues, including false positives, not parsed assertions."""
    stripped = line.strip()
    cues = []
    if not stripped or stripped.startswith(b'%'):
        bucket = 'NONCLAIM_CUE'
        cues = ['BLANK_OR_LEXICAL_COMMENT']
    else:
        for label, pattern in (
            ('THEOREM_PROPERTY', rb'\\begin\s*\{(?:theorem|lemma|proposition|corollary)|\b(?:theorem|lemma|property|monotonicity)\b'),
            ('ENUMERATED_ASSERTION', rb'\\item(?:\[|\b)'),
            ('VERBAL_ASSERTION', rb'\b(?:we (?:show|prove|find|demonstrate)|implies|it follows|therefore|hence|is (?:equal|optimal|bounded)|can be|must be|satisfies)\b'),
            ('NUMERICAL', rb'\b\d+\.\d+|\\(?:approx|geq|leq)\b'),
            ('TABLE', rb'\\(?:begin\s*\{(?:table\*?|tabular)\}|caption)|&'),
            ('EQUATION', rb'\$|\\(?:begin\s*\{(?:equation\*?|align\*?|eqnarray\*?)\}|\[|\])'),
            ('DEFINITION', rb'\b(?:define|defined|definition|denote)\b'),
        ):
            if re.search(pattern, line, re.IGNORECASE):
                cues.append(label)
        bucket = 'TENTATIVE_CLAIM_CUE' if cues else 'UNKNOWN_TEXT'
        if not cues and re.match(rb'\\(?:usepackage|documentclass|newcommand|renewcommand|bibliography|label|end)\b', stripped):
            bucket, cues = 'NONCLAIM_CUE', ['TEX_STRUCTURAL_OR_MACRO_CUE']
    return {'bucket': bucket, 'cues': cues, 'authority_status': 'ORACLE_PROPOSED',
            'verification': 'UNVERIFIED', 'basis': 'LEXICAL_LINE_ONLY_NOT_ASSERTION_OR_PUBLICATION_PROOF'}


def _proposed_obligations(files: list, records: tuple) -> list:
    obligations = []
    def add(category, targets, source_targets, question):
        obligations.append({
            'obligation_id': 'proposed-obligation:' + str(len(obligations)),
            'category': category, 'target_refs': targets, 'source_artifact_refs': source_targets,
            'statement': question, 'authority_status': 'ORACLE_PROPOSED', 'verification': 'UNVERIFIED',
            'state': 'OPEN', 'disposition': 'DEFERRED', 'performed': False, 'evidence_refs': [],
            'frozen_scope_ref': None, 'frozen_obligation_check': 'NOT_PERFORMED',
        })
    add('SOURCE_AND_RENDERING_REVIEW', [exact_ref(r) for r in records if kind(r) == 'source-snapshot'],
        [f['artifact'] for f in files], 'Review all captured source units, missing macros/packages, PDF content and published participation.')
    add('WHOLE_TEXT_CANDIDATE_REVIEW', [], [f['artifact'] for f in files if f['kind'] == 'TEX'],
        'Review tentative lexical cues, nonclaim cues and unknown text; find missed claims and remove false positives.')
    for record in records:
        if kind(record) == 'argument-node':
            add('SOURCE_AND_MATHEMATICAL_REVIEW', [exact_ref(record)], [],
                'Check this proposed statement, all conditions, feasibility, attainment and declared dependencies; nothing is discharged.')
    add('SUPPLEMENT_AND_EXTERNAL_EVIDENCE_REVIEW', [], [f['artifact'] for f in files],
        'Locate and verify supplementary matrices/code/data, external citations and numerical/gate/synthesis claims; no evidence execution was performed.')
    return obligations


def _line_spans(data: bytes):
    start = 0
    for match in re.finditer(rb'\r\n|\r|\n', data):
        yield start, match.end()
        start = match.end()
    if start < len(data):
        yield start, len(data)


def _check_json_budget(value, limit):
    size = 0
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    for chunk in encoder.iterencode(value):
        size += len(chunk.encode('utf-8'))
        if size > limit:
            raise SourceError('Generated candidate JSON exceeds its byte budget')


def _bounded_items(values, *, byte_budget=None):
    if byte_budget is None:
        byte_budget = MAX_PACKAGE_BYTES
    result, size = [], 0
    for value in values:
        if len(result) >= MAX_SEGMENTS:
            raise SourceError('Candidate item count exceeds its limit')
        _check_json_budget(value, byte_budget - size)
        size += len(canonical(value)) + 1
        if size > byte_budget:
            raise SourceError('Generated candidate items exceed their byte budget')
        result.append(value)
    return result


def _validate_manifest(files, limits):
    if len(files) > limits.max_files:
        raise SourceError('Candidate manifest exceeds file count limit')
    paths, directories, total = set(), set(), 0
    for item in files:
        path, size = item['path'], item['byte_size']
        if _relative(path, limits.max_path_bytes) != path or path in paths:
            raise SourceError('Candidate source path is noncanonical or duplicated')
        if type(size) is not int or not 0 <= size <= limits.max_file_bytes:
            raise SourceError('Candidate manifest exceeds per-file byte limit')
        if 'artifact' in item and item['artifact']['byte_size'] != size:
            raise SourceError('Candidate artifact size disagrees with bounded file manifest')
        parts = PurePosixPath(path).parts
        if len(parts) - 1 > limits.max_depth:
            raise SourceError('Candidate manifest exceeds directory depth limit')
        paths.add(path)
        directories.update('/'.join(parts[:index]) for index in range(1, len(parts)))
        total += size
        if total > limits.max_total_bytes:
            raise SourceError('Candidate manifest exceeds total byte limit')
        if len(paths) + len(directories) > limits.max_entries:
            raise SourceError('Candidate manifest exceeds minimum directory entry limit')
    if paths & directories:
        raise SourceError('Candidate file path is also an implied directory')


def _inventory(inspection: LocalInspection) -> tuple[list, list, list]:
    files, segments, artifacts = [], [], []
    report_files = inspection.report()['files']
    _validate_manifest(report_files, inspection.limits)
    segment_count = 0
    for item in report_files:
        path = item['path']
        data = inspection.sources[path]
        artifact = _artifact(data, item['media_type_hint'])
        artifacts.append(artifact)
        text = item['kind'] in {'TEX', 'BIBLIOGRAPHY', 'CODE'} or path == inspection.structure.main
        try:
            data.decode('utf-8')
        except UnicodeError:
            text = False
        status = 'STATIC_TEXT_SEGMENTED' if text else 'BYTES_ONLY_UNREVIEWED'
        if not data:
            status = 'EMPTY_FILE'
        files.append({**item, 'artifact': artifact.reference(), 'status': status,
                      'origin': 'LOCAL_GENERATED_UNVERIFIED' if PurePosixPath(path).parts[0] == 'build'
                      else 'LOCAL_FILE_UNVERIFIED'})
        if text:
            # Count with bounded iteration before constructing any segment list.
            for _ in _line_spans(data):
                segment_count += 1
                if segment_count > MAX_SEGMENTS:
                    raise SourceError('Candidate segmentation exceeds its segment limit')
    def items():
        for item in files:
            if item['status'] != 'STATIC_TEXT_SEGMENTED':
                continue
            path, data = item['path'], inspection.sources[item['path']]
            for start, end in _line_spans(data):
                yield {**_span(path, data, start, end),
                       'classification': 'UNCLASSIFIED_STATIC_TEXT',
                       'data_class': 'OBSERVED', 'observation': 'RAW_BYTE_SPAN',
                       'candidate_cues': _candidate_cues(data[start:end])}
    segments = _bounded_items(items())
    return files, segments, artifacts


@dataclass(frozen=True)
class CandidatePackage:
    artifact: SuppliedArtifact
    artifacts: tuple[SuppliedArtifact, ...]
    records: tuple[dict, ...] = ()

    def report(self) -> dict:
        return parse(self.artifact.data)

    def reference(self) -> dict:
        return self.artifact.reference()


def build_candidate_package(inspection: LocalInspection, *, proposals: Iterable[dict] = (),
                            open_questions: Iterable[str] = (), records: Iterable[dict] = (),
                            supporting_artifacts: Iterable[SuppliedArtifact] = ()) -> CandidatePackage:
    """Bind a whole captured directory, explicit proposals and exact V3 references.

    Proposals have id, interpretation, anchors, conditions, dependencies and
    unknowns. Anchors carry original-byte hashes. Dependencies name other proposal
    IDs in this package; neither edges nor conditions are scientifically verified.
    The caller supplies any normative V3 records and their real policy context.
    """
    files, segments, artifacts = _inventory(inspection)
    proposals = parse(canonical(_bounded_items(proposals)))
    ids = set()
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {
            'id', 'interpretation', 'anchors', 'conditions', 'dependencies', 'unknowns'
        }:
            raise SourceError('Malformed explicit candidate proposal')
        if not isinstance(proposal['id'], str) or not proposal['id'] or proposal['id'] in ids:
            raise SourceError('Proposal IDs must be nonempty and unique')
        ids.add(proposal['id'])
        if not isinstance(proposal['interpretation'], str) or not proposal['interpretation'].strip():
            raise SourceError('A proposal requires an explicit interpretation')
        for field in ('conditions', 'dependencies', 'unknowns'):
            if not isinstance(proposal[field], list) or not all(isinstance(x, str) and x for x in proposal[field]):
                raise SourceError('Proposal lists require nonempty strings')
        if not isinstance(proposal['anchors'], list) or not proposal['anchors']:
            raise SourceError('A proposal requires source anchors')
        for anchor in proposal['anchors']:
            _verify_anchor(anchor, inspection.sources)
        proposal.update(data_class='ORACLE_PROPOSED', verification='UNVERIFIED')
    for proposal in proposals:
        if not set(proposal['dependencies']) <= ids:
            raise SourceError('Proposal dependency is absent from this exact package')
    # Reject circular proposed support rather than presenting an unmarked loop.
    remaining = {p['id']: set(p['dependencies']) for p in proposals}
    dependents = {identifier: [] for identifier in ids}
    for identifier, dependencies in remaining.items():
        for dependency in dependencies:
            dependents[dependency].append(identifier)
    ready = [identifier for identifier, dependencies in remaining.items() if not dependencies]
    visited = 0
    while ready:
        identifier = ready.pop()
        visited += 1
        for dependent in dependents[identifier]:
            remaining[dependent].remove(identifier)
            if not remaining[dependent]:
                ready.append(dependent)
    if visited != len(ids):
        raise SourceError('Cyclic proposed dependencies are not accepted as candidate support')
    questions = _bounded_items(open_questions)
    if not all(isinstance(x, str) and x.strip() for x in questions):
        raise SourceError('Open questions must be nonempty strings')
    records = tuple(sorted((parse(canonical(r)) for r in _bounded_items(records)), key=lambda r: canonical(exact_ref(r))))
    if len({canonical(exact_ref(r)) for r in records}) != len(records):
        raise SourceError('Duplicate exact record membership in candidate package')
    for record in records:
        if kind(record) not in CANDIDATE_KINDS:
            raise SourceError('Only candidate record families may be package members')
        if kind(record) not in {'source-snapshot', 'source-span', 'paper-structure'}:
            # ORACLE_PROPOSED is a proposal status, not a V3 data_class enum.
            text = record.get('payload', {}).get('statement', record.get('payload', {}).get('justification', ''))
            if kind(record) == 'dependency-binding':
                text = ' '.join(c['source_value'] for c in record['payload']['comparison'])
            if record.get('data_class') != 'RESEARCH' or 'ORACLE_PROPOSED / UNVERIFIED' not in text:
                raise SourceError('Interpretation records require explicit ORACLE_PROPOSED / UNVERIFIED attribution')
    supporting_artifacts = tuple(supporting_artifacts)
    report = inspection.report()
    body = {
        'package_type': PROFILE, 'mode': 'PROVISIONAL', 'canonical_mutation': 'FORBIDDEN',
        'scientific_assessment': 'NOT_PERFORMED', 'authority_checked': False,
        'segmentation': 'FULL_UTF8_TEXT_LINES_WITH_TENTATIVE_LEXICAL_CUES_NOT_SEMANTIC_DISCOVERY',
        'main': report['main'], 'working_directory': report['working_directory'],
        'limits': report['limits'], 'file_count': len(files),
        'package_limits': {'max_segments': MAX_SEGMENTS, 'max_package_bytes': MAX_PACKAGE_BYTES, 'max_query_bytes': MAX_QUERY_BYTES},
        'filesystem_limit_verification': 'MANIFEST_CHECKABLE_LIMITS_ONLY; empty directories, inode/link/device facts and capture-time mutations are reported by intake, not independently reconstructible from retained files.',
        'total_bytes': sum(f['byte_size'] for f in files), 'files': files,
        'source_bytes_sha256': hashlib.sha256(canonical([{'path': f['path'], 'byte_size': f['byte_size'], 'sha256': f['sha256']} for f in files])).hexdigest(),
        'candidate_inventory': {
            'basis': 'TENTATIVE_LEXICAL_CUES_NOT_SEMANTIC_COMPLETENESS',
            'authority_status': 'ORACLE_PROPOSED', 'verification': 'UNVERIFIED',
            'semantic_claim_denominator': None,
            'main_line_count': sum(s['path'] == report['main'] for s in segments),
            'main_bucket_counts': {bucket: sum(s['path'] == report['main'] and s['candidate_cues']['bucket'] == bucket for s in segments)
                for bucket in ('TENTATIVE_CLAIM_CUE', 'NONCLAIM_CUE', 'UNKNOWN_TEXT')},
        },
        'segments': segments, 'includes': report['includes'], 'issues': report['issues'],
        'proposals': proposals, 'open_questions': list(QUESTIONS) + questions,
        'record_refs': sorted((exact_ref(r) for r in records), key=canonical),
        'proposed_obligations': _proposed_obligations(files, records),
        'supporting_artifacts': sorted((a.reference() for a in supporting_artifacts), key=canonical),
        'limitations': report['limitations'],
    }
    _check_json_budget(body, MAX_PACKAGE_BYTES)
    artifact = _artifact(canonical(body), 'application/json')
    if len(artifact.data) > MAX_PACKAGE_BYTES:
        raise SourceError('Candidate package exceeds its byte budget')
    unique = {}
    for item in [*artifacts, *supporting_artifacts, artifact]:
        if item.artifact_id in unique and unique[item.artifact_id] != item:
            raise SourceError('Conflicting artifact identity')
        unique[item.artifact_id] = item
    return CandidatePackage(artifact, tuple(unique[k] for k in sorted(unique)), records)


def _verify_anchor(anchor: dict, sources: dict) -> bytes:
    if not isinstance(anchor, dict) or set(anchor) != {'path', 'start_byte', 'end_byte', 'sha256'}:
        raise SourceError('Expected an exact source span')
    if not isinstance(anchor['path'], str) or anchor['path'] not in sources:
        raise SourceError('Source anchor path absent from whole inventory')
    return verify_byte_span(sources[anchor['path']], anchor['start_byte'], anchor['end_byte'],
                            expected_sha256=anchor['sha256'])


def persist_candidate_package(store, package: CandidatePackage, *, context_records=(), context_artifacts=()):
    """Retain exact artifacts and supplied records without an admission/head update."""
    # Check the package before writing, including every source span and reference.
    artifacts = {a.artifact_id: a for a in package.artifacts}
    records = {canonical(exact_ref(r)): r for r in package.records}

    class Pending:
        def artifact(self, reference):
            item = artifacts.get(reference.get('artifact_id'))
            if item is None or item.reference() != reference:
                raise SourceError('Candidate artifact reference mismatch')
            return item.data

        def resolve(self, reference):
            try:
                return records[canonical(reference)]
            except KeyError as error:
                raise SourceError('Candidate record reference missing') from error

    query_candidate_package(Pending(), package.reference())
    return store.ingest((*context_records, *package.records), (*context_artifacts, *package.artifacts))


def query_candidate_package(store, reference: dict) -> dict:
    """Read an exact historical artifact package, even after a database reopen.

    Rebuild the deterministic inventory to reject omitted files/spans relative to
    the bound manifest. An externally incomplete but self-consistent directory
    still requires an independent checkpoint; this is not global completeness.
    """
    if type(reference.get('byte_size')) is not int or not 0 <= reference['byte_size'] <= MAX_PACKAGE_BYTES:
        raise SourceError('Candidate package reference exceeds its byte budget')
    raw = store.artifact(reference)
    if len(raw) > MAX_PACKAGE_BYTES:
        raise SourceError('Candidate package exceeds its byte budget before parsing')
    body = parse(raw)
    if not isinstance(body, dict) or body.get('package_type') != PROFILE or body.get('mode') != 'PROVISIONAL':
        raise SourceError('Expected an exact provisional candidate package')
    from .intake import IntakeLimits
    limits = IntakeLimits(**body['limits'])
    _validate_manifest(body['files'], limits)
    if len(body['segments']) > MAX_SEGMENTS:
        raise SourceError('Candidate package exceeds its segment limit before rebuild')
    sources = {}
    for item in body['files']:
        if item['path'] in sources:
            raise SourceError('Duplicate candidate source path')
        sources[item['path']] = store.artifact(item['artifact'])
    from .source import analyze_tex_structure
    from pathlib import Path
    structure = analyze_tex_structure(body['main'], sources, working_directory=body['working_directory'],
        max_files=limits.max_files, max_total_bytes=limits.max_total_bytes,
        max_commands=limits.max_commands, max_includes=limits.max_includes,
        max_conditional_depth=limits.max_conditional_depth)
    inspection = LocalInspection(Path('.'), 'UNUSED', sources, structure, limits)
    proposals = [{k: v for k, v in p.items() if k not in {'data_class', 'verification'}} for p in body['proposals']]
    records = tuple(store.resolve(r) for r in body['record_refs'])
    support = tuple(SuppliedArtifact(r['artifact_id'], r['media_type'], store.artifact(r)) for r in body['supporting_artifacts'])
    rebuilt = build_candidate_package(inspection, proposals=proposals,
        open_questions=body['open_questions'][len(QUESTIONS):], records=records, supporting_artifacts=support)
    if rebuilt.artifact.data != raw or rebuilt.reference() != reference:
        raise SourceError('Candidate package inventory, hash, span or interpretation integrity failure')
    # Account hex expansion and fixed response fields before constructing spans.
    reserved = len(raw) + sum(len(canonical(r)) for r in records) + len(canonical(body['open_questions'])) + 4096
    minimum = sum(2 * (s['end_byte'] - s['start_byte']) for s in body['segments'])
    if reserved + minimum > MAX_QUERY_BYTES:
        raise SourceError('Candidate query exceeds its generated byte budget')
    spans = _bounded_items(({**span, 'bytes_hex': _verify_anchor({k: span[k] for k in ('path', 'start_byte', 'end_byte', 'sha256')}, sources).hex()}
             for span in body['segments']), byte_budget=MAX_QUERY_BYTES - reserved)
    result = {'mode': 'PROVISIONAL', 'scope': 'EXACT_SOURCE_CANDIDATE_PACKAGE',
            'package_ref': reference, 'package': body, 'source_spans': spans,
            'records': list(records), 'open_questions': body['open_questions'],
            'authority_checked': False, 'scientific_assessment': 'NOT_PERFORMED',
            'canonical_mutation': 'FORBIDDEN'}
    _check_json_budget(result, MAX_QUERY_BYTES)
    return result


def robustness_proposals(inspection: LocalInspection) -> tuple[dict, ...]:
    """Manually authored static-review interpretations, never governed reviews."""
    path = 'Robustness_main_appendix.tex'
    data = inspection.sources.get(path, b'')
    if hashlib.sha256(data).hexdigest() != '48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d':
        raise SourceError('Robustness interpretations require the exact reviewed TeX bytes')
    definitions = [
        ('definition', 9218, 10126, 'Robustness is the minimum signed stabilizer pseudomixture L1 norm.', []),
        ('channel', 35064, 35619, 'Channel maps each stabilizer atom to a normalized nonnegative mixture, not necessarily an atom.', ['definition']),
        ('feasibility', 35619, 35847, 'Regrouped coefficients propose a feasible output pseudomixture upper bound.', ['channel']),
        ('contraction', 35847, 36153, 'Triangle inequality and row normalization propose L1 contraction.', ['feasibility']),
        ('R3', 33249, 33406, 'Trace-preserving stabilizer channels do not increase robustness.', ['definition', 'contraction']),
        ('postselection', 36153, 36418, 'Separate average/postselection extension cites external support; branchwise monotonicity is not inferred.', []),
    ]
    conditions = ['Finite multiqubit density operators and pure stabilizer atoms.',
                  'Real signed input coefficients; linear trace-preserving channel.',
                  'Nonnegative mixture coefficients with each row summing to one.',
                  'Optimal input pseudomixture is a contextual reconstructed requirement, not a verbatim premise.']
    return tuple({'id': name, 'interpretation': text, 'anchors': [_span(path, data, start, end)],
                  'conditions': conditions if name != 'postselection' else [], 'dependencies': dependencies,
                  'unknowns': ['SOFTWARE_STATIC_SOURCE_REVIEW only; no governed scientific review.',
                               'Feasibility, attainment and finite-sum algebra remain undischarged.' if name != 'postselection'
                               else 'External citation and average/postselection conditions remain unverified.']}
                 for name, start, end, text, dependencies in definitions)


ROBUSTNESS_QUESTIONS = (
    'Supplementary numerical matrices, code, data and solver certificates referenced at lines 69, 110 and 430 were not located in the original directory/archive.',
    'Robustness_main.bib is absent locally; the job-name BBL is present. External packages and published rendering remain unreviewed.',
    'Simulation overhead, lower bounds, numerical values, maximization, gates, synthesis optimality and interconvertibility remain unreviewed beyond static byte segmentation.',
)


def build_interpretation_records(inspection: LocalInspection, proposals: Iterable[dict], *,
                                 source_snapshot: dict, bundle, producer: dict,
                                 policy_ref: dict, created_at: str) -> tuple[dict, ...]:
    """Project explicit proposals into existing V3 spans/nodes/steps/frontiers.

    Requires a caller-supplied exact source snapshot, producer and policy. No
    authority context or scientific claim approval is inferred from these fields.
    Conditions stay explicit in reconstructed node statements; unknowns remain
    OPEN frontier items. Dependencies are jointly proposed inference premises.
    """
    package = build_candidate_package(inspection, proposals=proposals)
    proposals = package.report()['proposals']
    if bundle.validate_record(source_snapshot) or kind(source_snapshot) != 'source-snapshot':
        raise SourceError('Expected a contract-valid exact source snapshot')
    units = {u['relative_path']: u for u in source_snapshot['payload']['units']}
    if set(units) != set(inspection.sources) or len(units) != len(source_snapshot['payload']['units']):
        raise SourceError('Source snapshot omits or duplicates whole-directory files')
    for path, data in inspection.sources.items():
        artifact = units[path]['artifact']
        if artifact['byte_size'] != len(data) or artifact['sha256'] != 'sha256:' + hashlib.sha256(data).hexdigest():
            raise SourceError('Source snapshot differs from captured bytes')
    if not policy_ref or not created_at:
        raise SourceError('Explicit policy and creation time are required')
    records, nodes = [], {}
    seed = hashlib.sha256(canonical({'package': package.reference(), 'source': exact_ref(source_snapshot),
                                    'producer': producer, 'policy': policy_ref, 'created_at': created_at})).hexdigest()

    def make(name, payload, *, observed=False):
        record = bundle.make_record(name, 'candidate:' + seed + '-' + str(len(records)), payload,
            producer=producer, policy_ref=policy_ref, created_at=created_at,
            input_refs=(exact_ref(source_snapshot),), data_class='OBSERVED' if observed else 'RESEARCH')
        records.append(record)
        return exact_ref(record)

    for proposal in proposals:
        spans = []
        for anchor in proposal['anchors']:
            spans.append(make('source-span', {
                'source_ref': exact_ref(source_snapshot), 'artifact': units[anchor['path']]['artifact'],
                'locator_kind': 'RAW_TEXT_BYTES', 'byte_start': anchor['start_byte'], 'byte_end': anchor['end_byte'],
                'span_sha256': 'sha256:' + anchor['sha256'], 'pdf_region': None, 'transformation_ref': None,
                'locator': anchor['path'] + ': original byte span', 'activity': 'UNKNOWN'}, observed=True))
        statement = 'ORACLE_PROPOSED / UNVERIFIED interpretation: ' + proposal['interpretation']
        if proposal['conditions']:
            statement += '\nExplicit proposed conditions (not discharged):\n' + '\n'.join(proposal['conditions'])
        nodes[proposal['id']] = make('argument-node', {
            'statement': statement, 'kind': 'CLAIM', 'origin': 'RECONSTRUCTED', 'claim_refs': [],
            'context_ref': None, 'definition_refs': [], 'source_span_refs': spans})
    for proposal in proposals:
        target = nodes[proposal['id']]
        if proposal['dependencies']:
            make('inference-step', {
                'premise_refs': [nodes[p] for p in proposal['dependencies']], 'conclusion_ref': target,
                'rule': 'DIRECT', 'justification': 'ORACLE_PROPOSED / UNVERIFIED joint dependence only; no entailment check performed. ' + proposal['interpretation'],
                'context_ref': None, 'discharged_context_refs': [], 'rule_evidence_refs': []})
        for prerequisite in proposal['dependencies']:
            make('dependency-binding', {
                'dependent_ref': target, 'prerequisite_ref': nodes[prerequisite],
                'kind': 'MATHEMATICAL', 'affected_axes': ['mathematical_correctness'],
                'proof_plan_ref': None, 'comparison': [{
                    'dimension': 'ASSUMPTION',
                    'source_value': 'ORACLE_PROPOSED / UNVERIFIED prerequisite: ' + prerequisite,
                    'target_value': 'Proposed use in ' + proposal['id'] + '; compatibility not checked.',
                    'relation': 'UNKNOWN', 'witness_refs': []}], 'reuse_decision_ref': None})
        for unknown in proposal['unknowns']:
            make('frontier-item', {'target_refs': [target], 'kind': 'UNPROVED_LEMMA',
                'axes': ['source_fidelity', 'mathematical_correctness'], 'statement': 'ORACLE_PROPOSED / UNVERIFIED: ' + unknown,
                'next_evidence': 'Independent source and mathematical review under a separately supplied policy.',
                'attempt_refs': [], 'state': 'OPEN', 'resolution_refs': []})
    return tuple(records)


def build_local_proposed_context(inspection: LocalInspection, *, bundle, corpus_bytes: bytes) -> dict:
    """Explicit opt-in unadopted local context; never an authority capability.

    Bibliography is reported from supplied corpus bytes, not remote authenticated
    metadata. This creates no allowed principal, attestation or adopted policy.
    Caller must use a real capture time, or explicitly replay a known observation.
    """
    from .contracts import content_hash
    from .intake import build_source_candidates
    corpus = parse(corpus_bytes)
    matches = [p for p in corpus['papers'] if p['canonical_source_path'].endswith('/' + inspection.structure.main)]
    if len(matches) != 1:
        raise SourceError('Local proposed context requires one explicit corpus paper match')
    paper = matches[0]
    assets = [a for a in corpus['assets'] if a['path'] == paper['canonical_source_path']]
    main_bytes = inspection.sources[inspection.structure.main]
    if len(assets) != 1 or assets[0]['byte_length'] != len(main_bytes) or assets[0]['sha256'] != hashlib.sha256(main_bytes).hexdigest():
        raise SourceError('Local proposed context requires the corpus-pinned canonical main asset bytes')
    seed = hashlib.sha256(canonical({'capture': build_candidate_package(inspection).reference(),
        'observed_at': inspection.observed_at, 'root': str(inspection.root), 'corpus': _artifact(corpus_bytes, 'application/json').reference()})).hexdigest()
    producer = {'principal_id': 'local:static-candidate-producer', 'role': 'MAINTAINER',
        'actor_kind': 'MECHANICAL_SERVICE', 'identity_assurance': 'DECLARED',
        'execution_id': 'local:static-candidate-' + seed, 'visible_input_refs': [], 'identity_evidence': []}
    policy = bundle.make_record('authority-policy', 'local:unadopted-candidate-policy-' + seed, {
        'charter_identity': 'AgtXIv-Charter/1.0', 'charter_state': 'PROPOSED', 'ratification_commit': None,
        'minimum_identity_assurance': 'LOCALLY_ATTESTED', 'separated_role_pairs': ['PRODUCER/REVIEWER'],
        'human_review_triggers': ['This local candidate policy is unadopted and grants no authority. Require an independently adopted policy and authenticated separated actors before scientific review, scope freeze or admission.'],
        'allowed_principal_ids': []}, producer=producer, policy_ref=None,
        created_at=inspection.observed_at, data_class='RESEARCH')
    source_producer = {**producer, 'role': 'SOURCE_PRODUCER'}
    source = build_source_candidates(inspection, bundle=bundle, producer=source_producer,
        policy_ref=exact_ref(policy), source_record_id='local:source-' + seed,
        structure_record_id='local:structure-' + seed, paper_id=paper['paper_id'],
        paper_version=paper['paper_id'], created_at=inspection.observed_at, rights_status='UNRESOLVED',
        rights_note='Local byte capture only. Bibliographic identity/version reported by the retained evaluation corpus; remote version, publication participation and redistribution rights are unverified.')
    snapshot, structure = source.source_snapshot, source.paper_structure
    if paper['slug'] == 'robustness-of-magic':
        robustness_proposals(inspection)  # Require the independently reviewed exact TeX.
        snapshot['payload']['missing_material'] = [
            'Supplementary numerical matrices, code/data and solver certificates referenced at lines 69, 110 and 430 were not located in the original directory/archive; remote availability unverified.',
            'Robustness_main.bib named in TeX is absent locally; job-name BBL is present.',
            'External TeX class/package versions and publication rendering environment are not bundled or verified.']
        snapshot['content_hash'] = content_hash(snapshot)
        structure['payload']['source_ref'] = exact_ref(snapshot)
        structure['input_refs'] = [exact_ref(snapshot)]
        structure['content_hash'] = content_hash(structure)
    return {'source_snapshot': snapshot, 'paper_structure': structure,
            'context_records': (policy,), 'producer': {**producer, 'role': 'ARGUMENT_PRODUCER'},
            'policy_ref': exact_ref(policy), 'created_at': inspection.observed_at,
            'artifacts': (*source.artifacts, _artifact(corpus_bytes, 'application/json'))}
