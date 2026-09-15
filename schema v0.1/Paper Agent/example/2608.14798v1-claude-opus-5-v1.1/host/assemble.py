#!/usr/bin/env python3
"""Host-side assembler for the AGENT.md 1.1 re-run of arXiv:2608.14798v1.

Emulates the host half of the 1.1 interface. For each round it writes the fixed
Task, the model draft (record_type + payload only, per extraction-draft.schema),
then fills identity, revision, time, data_class, schema bundle hash, producer,
policy_ref, input_refs and content_hash and checks that the payload is
byte-identical before and after assembly.

This script performs no model call. It replays one already-completed extraction
and computes every source-span offset and digest from the real paper bytes.
Running it establishes record shape, reference closure and payload preservation
only; it establishes nothing scientific and produces no Result.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
SPECDIR = RUN_DIR.parents[1]   # .../schema v0.1/Paper Agent
REPO = RUN_DIR.parents[3]
sys.path.insert(0, str(REPO / 'src'))
import importlib.util  # noqa: E402
from agtxiv_v3.contracts import (  # noqa: E402
    SchemaBundle, RecordSet, SuppliedArtifact, canonical, digest, exact_ref, parse,
)


def load_checker():
    """The specification's own offline checker, run in-process so its verdict is stored."""
    spec = importlib.util.spec_from_file_location('check_output', SPECDIR / 'check_output.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_claims(host, out):
    """Reading view of the same records. The JSON records are authoritative."""
    seed = host.seed
    maps = {r['payload']['claim_ref']['record_id']: r for r in host.records
            if r['record_type'].startswith('agtxiv.v3.claim-component-map')}
    lines = [
        '# Author claims extracted from arXiv:2608.14798v1 (AGENT.md 1.1 run)',
        '',
        'Reading view of `records.json`. The JSON records are authoritative; this file is a run attachment.',
        'One claim per source assertion unit, per R2: a numbered Proposition/Theorem/Lemma/Corollary/Algorithm',
        'is never merged with another, and unnumbered text contributes the minimal contiguous range that',
        'carries a complete assertion. Every condition and assumption cites its own source span. Nothing here',
        'was proved, checked or reproduced, and nothing here is an independent review.',
        '',
        f'Claims: {len(seed["claims"])}. Definitions: {len(seed["definitions"])}. '
        f'MathClaims: {sum(1 for c in seed["claims"] for x in c["components"] if "math" in x)}. '
        f'SemanticContexts: {sum(1 for c in seed["claims"] if "semantic" in c)}. '
        f'Open frontier items: {sum(len(c["frontier"]) for c in seed["claims"])}.',
        '',
        '| # | Section | Kind | Claim | Modality | Components | Targets | Coverage | Open |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for c in seed['claims']:
        m = maps[f'claim:{RUN}/{c["id"]}']
        targets = sum(1 for x in c['components'] if 'math' in x)
        lines.append(f'| {c["id"]} | {c["section"]} | {c["kind"]} | {c["label"]} | {c["modality"]} | '
                     f'{len(c["components"])} | {targets} | {m["payload"]["coverage"]} | {len(c["frontier"])} |')
    lines += ['', '---', '']
    for c in seed['claims']:
        m = maps[f'claim:{RUN}/{c["id"]}']
        disposition = {x['component_id']: x['disposition'] for x in m['payload']['mappings']}
        lines += [f'## {c["id"]} — {c["label"]}', '',
                  f'*{c["section"]} · {c["kind"]} · modality {c["modality"]} · coverage {m["payload"]["coverage"]}*', '',
                  '**What the authors said.** ' + c['statement'], '',
                  f'**System.** {c["system"]}', '']
        if c['comparison_baseline']:
            lines += [f'**Comparison baseline.** {c["comparison_baseline"]}', '']
        lines += ['**Stated conditions.**', '']
        for cond in c['conditions']:
            lines.append(f'- `{cond["condition_id"]}` ({cond["origin"]}) {cond["statement"]}')
        lines += ['', '**Components, their accounting and their targets.**', '']
        for comp in c['components']:
            key = comp['component_id']
            lines.append(f'- `{key}` [{comp["role"]} / {disposition[key]}] {comp["text"]}')
            if comp.get('math'):
                mm = comp['math']
                lines.append(f'  - target ({mm["exactness"]}): {mm["conclusion"]}')
                for q in mm['quantifiers']:
                    lines.append(f'    - quantifier: {q["kind"]} {q["variable"]} in {q["domain"]}')
                for a in mm['assumptions']:
                    lines.append(f'    - assumption ({a["origin"]}): {a["statement"]}')
                lines.append(f'    - normalization: {mm["normalization"]}')
                if mm['approximation_error']:
                    lines.append(f'    - approximation error: {mm["approximation_error"]}')
            if comp['residual']:
                lines.append(f'  - residual: {comp["residual"]}')
        if 'semantic' in c:
            sc = c['semantic']
            lines += ['', f'**Semantic context.** {sc["physical_system"]}', '',
                      f'- approximation regime: {sc["approximation_regime"]}',
                      f'- error bound: {sc["error_bound"]}']
            for lim in sc['limitations']:
                lines.append(f'- limitation: {lim}')
        if c['frontier']:
            lines += ['', '**Open items recorded against this claim.**', '']
            for f in c['frontier']:
                lines.append(f'- [{f["kind"]} · {", ".join(f["axes"])}] {f["statement"]}')
                lines.append(f'  - what could settle it: {f["next_evidence"]}')
        lines += ['', f'Records: `claim:{RUN}/{c["id"]}`, `map:{RUN}/{c["id"]}`.', '']
    (out / 'claims.md').write_text('\n'.join(lines) + '\n')

RUN = 'opus5-v11-2608.14798v1'
PRINCIPAL = f'session:{RUN}'
RUN_AT = '2026-09-14T00:00:00Z'
MODEL_ID = 'claude-opus-5'
MODEL = f'{MODEL_ID} (single interactive execution; one principal in all roles, no independent reviewer)'

EXEC = {
    'MAINTAINER': f'exec:{RUN}/host-context',
    'COORDINATOR': f'exec:{RUN}/host-plan',
    'SOURCE_PRODUCER': f'exec:{RUN}/round-1',
    'CLAIM_PRODUCER': f'exec:{RUN}/round-2',
}
ROUND_EXEC = {1: f'exec:{RUN}/round-1', 2: f'exec:{RUN}/round-2',
              3: f'exec:{RUN}/round-3', 4: f'exec:{RUN}/round-4', 5: f'exec:{RUN}/round-5'}

MEDIA = {'.tex': 'text/x-tex', '.bib': 'text/x-bibtex', '.json': 'application/json',
         '.png': 'image/png', '.pdf': 'application/pdf'}
KIND = {'.tex': 'TEX', '.bib': 'BIBLIOGRAPHY', '.json': 'OTHER', '.png': 'FIGURE', '.pdf': 'FIGURE'}
SPEC_FILES = ['AGENT.md', 'INTERFACE.md', 'CONFORMANCE.md', 'extraction-draft.schema.json']


def unit_id(path: str) -> str:
    return 'unit:' + path.replace('/', '-').replace('_', '-').replace('.', '-').lower()


class Host:
    """The trusted side: it owns identity, references and hashes."""

    def __init__(self, out: Path):
        self.out = out
        self.bundle = SchemaBundle(REPO / 'schema v0.0')
        self.seed = json.loads((RUN_DIR / 'extraction' / 'seed.json').read_text())
        self.acq = json.loads((RUN_DIR / 'acquisition.json').read_text())
        self.source_dir = REPO / self.acq['source_directory']
        self.records: list[dict] = []
        self.artifacts: list[SuppliedArtifact] = []
        self.payload_preserved = 0
        self.policy_ref: dict | None = None

    # ---- assembly ------------------------------------------------------
    @staticmethod
    def used_refs(payload):
        """Exact references actually appearing in this payload, in stable order.

        The round's complete visible catalog is the Task's input_refs, kept in
        that round's task.json; a record's own input_refs are the subset it was
        actually built from.
        """
        found, seen = [], set()
        stack = [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                if set(item) == {'record_type', 'record_id', 'revision', 'content_hash'}:
                    key = (item['record_type'], item['record_id'], item['revision'], item['content_hash'])
                    if key not in seen:
                        seen.add(key)
                        found.append(item)
                else:
                    stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
        return sorted(found, key=lambda r: (r['record_type'], r['record_id'], r['revision']))

    def register(self, draft_record, *, role, execution, inputs, record_id, policy=True):
        """Fill the envelope around a model payload. The payload is never touched."""
        before = canonical(draft_record['payload'])
        inputs = self.used_refs(draft_record['payload'])
        name = draft_record['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0')
        producer = {
            'principal_id': PRINCIPAL, 'role': role, 'actor_kind': 'AGENT',
            'identity_assurance': 'DECLARED', 'execution_id': execution, 'model': MODEL,
            'visible_input_refs': list(inputs), 'identity_evidence': [],
        }
        record = self.bundle.make_record(
            name, record_id, parse(before), producer=producer,
            policy_ref=self.policy_ref if policy else None,
            input_refs=list(inputs), created_at=RUN_AT, data_class='RESEARCH')
        assert canonical(record['payload']) == before, f'payload changed during assembly: {record_id}'
        self.payload_preserved += 1
        self.records.append(record)
        return exact_ref(record)

    # ---- host context (not model output) -------------------------------
    def context(self):
        self.policy_ref = self.register({'record_type': 'agtxiv.v3.authority-policy/0.0.0', 'payload': {
            'charter_identity': 'AgtXIv-Charter/1.0', 'charter_state': 'PROPOSED',
            'ratification_commit': None, 'minimum_identity_assurance': 'LOCALLY_ATTESTED',
            'separated_role_pairs': [
                'CLAIM_PRODUCER/SCOPE_REVIEWER on the same inventory-discovery',
                'CLAIM_PRODUCER/SCOPE_REVIEWER on the same claim-component-map',
                'SOURCE_PRODUCER/SCOPE_REVIEWER on the same source-snapshot',
            ],
            'human_review_triggers': [
                'Any freeze of the obligation denominator for this paper',
                'Any promotion of an extracted claim into a knowledge base',
                'Any assertion that a mathematical target of this paper holds',
            ],
            'allowed_principal_ids': [PRINCIPAL],
        }}, role='MAINTAINER', execution=EXEC['MAINTAINER'], inputs=[],
            record_id=f'policy:{RUN}', policy=False)
        self.profile_ref = self.register({'record_type': 'agtxiv.v3.processing-profile/0.0.0', 'payload': {
            'name': 'V3_SOURCE_MAP',
            'required_stages': ['SOURCE', 'INVENTORY', 'CLAIM', 'SEMANTICS', 'COMPUTATION'],
            'success_required_stages': ['SOURCE', 'INVENTORY', 'CLAIM'],
            'required_axes': ['source_fidelity', 'mathematical_correctness', 'formal_alignment',
                              'semantic_applicability', 'empirical_support', 'computational_reproducibility'],
            'allowed_terminal_outcomes': ['DELIVERED', 'BLOCKED', 'DEFERRED'],
            'empirical_requirement': 'ACCOUNT_FOR', 'computation_requirement': 'ACCOUNT_FOR',
            'non_implications': [
                'Completing this profile does not establish that any claim of the paper is true.',
                'Completing this profile does not establish that any mathematical target is provable or proved.',
                'Completing this profile does not reproduce or check any numerical result of the paper.',
                'Completing this profile does not constitute independent review of the extraction.',
                'Payload preservation through assembly does not establish that the extraction is faithful.',
            ],
        }}, role='MAINTAINER', execution=EXEC['MAINTAINER'], inputs=[self.policy_ref],
            record_id=f'profile:{RUN}')

        units = []
        for entry in self.acq['files']:
            path, suffix = entry['path'], Path(entry['path']).suffix
            raw = (self.source_dir / path).read_bytes()
            assert digest(raw) == entry['sha256'] and len(raw) == entry['bytes'], path
            artifact = {'artifact_id': 'artifact:' + unit_id(path).removeprefix('unit:'),
                        'sha256': entry['sha256'], 'byte_size': entry['bytes'],
                        'media_type': MEDIA[suffix], 'path_hint': path}
            self.artifacts.append(SuppliedArtifact(artifact['artifact_id'], artifact['media_type'], raw))
            units.append({'unit_id': unit_id(path), 'relative_path': path, 'artifact': artifact,
                          'activity': 'ACTIVE' if path in {'Pauli_Spectrum.tex', '00README.json', 'draft_ref.bib'} else 'UNKNOWN',
                          'kind': KIND[suffix]})
        self.units = units
        archive = {'artifact_id': f'artifact:{RUN}-archive', 'sha256': self.acq['archive_sha256'],
                   'byte_size': self.acq['archive_bytes'], 'media_type': 'application/gzip'}
        self.artifacts.append(SuppliedArtifact(archive['artifact_id'], 'application/gzip',
                                               (REPO / self.acq['archive_path']).read_bytes()))
        self.snapshot_ref = self.register({'record_type': 'agtxiv.v3.source-snapshot/0.0.0', 'payload': {
            'paper_id': 'arXiv:2608.14798', 'paper_version': '2608.14798v1',
            'source_uri': self.acq['source_uri'], 'acquired_at': self.acq['verified_at'],
            'acquisition_ref': None, 'acquisition_method': 'LOCAL_IMPORT',
            'units': units, 'archive': archive,
            'missing_material': [
                'No compiled PDF was produced or inspected; figure PDFs and PNGs were inventoried by hash only and their contents were never read.',
                'draft_ref.bib and Pauli_SpectrumNotes.bib were inventoried but no cited work was retrieved, so every attribution in this run is to the citing text only.',
                'The numerical data, scripts and geometries behind every figure are absent from the source archive.',
            ],
            'rights_status': 'UNRESOLVED',
            'rights_note': 'arXiv source archive held locally in this repository. No licence statement was located in the source; redistribution rights were not determined in this run.',
        }}, role='SOURCE_PRODUCER', execution=EXEC['SOURCE_PRODUCER'], inputs=[self.profile_ref],
            record_id=f'source:{RUN}')
        self.plan_ref = self.register({'record_type': 'agtxiv.v3.agentization-plan/0.0.0', 'payload': {
            'source_ref': self.snapshot_ref, 'profile_ref': self.profile_ref, 'baseline_ref': None,
            'source_unit_ids': [unit_id(e['path']) for e in self.acq['files']],
            'max_steps': 600, 'max_seconds': 86400, 'max_cost_units': 0, 'no_progress_limit': 8,
            'trigger_note': (
                'User asked for a re-run of arXiv:2608.14798 under Paper Agent AGENT.md 1.1, in a new '
                'directory, leaving the 1.0 example untouched. The request is the trigger only; the scope '
                'denominator is the full supplied source inventory. This plan carries every field the v0.0 '
                'schema requires, as INTERFACE.md section 5 now directs: the 12-field slim plan of the 1.0 '
                'document is not used. max_seconds and max_cost_units are declared ceilings that were never '
                'enforced and never measured; 0 cost units must not be read as a measured zero cost.'),
        }}, role='COORDINATOR', execution=EXEC['COORDINATOR'], inputs=[self.snapshot_ref, self.profile_ref],
            record_id=f'plan:{RUN}')
        self.context_refs = [self.policy_ref, self.profile_ref, self.snapshot_ref, self.plan_ref]

    # ---- task construction ---------------------------------------------
    def task(self, index, slug, brief, targets, inputs, expected, artifacts):
        return {
            'contract_version': '0.1.0', 'task_id': f'task.{RUN}.r{index}-{slug}',
            'agent': 'paper', 'operation': 'paper.extract', 'brief': brief,
            'target_refs': list(targets), 'input_refs': list(inputs),
            'input_artifacts': list(artifacts),
            'depends_on': ([{'task_id': f'task.{RUN}.r{index - 1}-{PREV[index]}', 'gate': 'DELIVERY'}]
                           if index > 1 else []),
            'expected_record_types': list(expected),
            'limits': {'max_attempts': 3, 'max_seconds': 86400, 'max_cost_units': 0, 'no_progress_limit': 2},
            'acceptance': 'DELIVERY', 'exclusions': [],
            'capabilities': ['records.read', 'source.read', 'candidates.propose'],
        }

    def spec_artifacts(self):
        refs = []
        for name in SPEC_FILES:
            raw = (SPECDIR / name).read_bytes()
            aid = 'artifact:spec-' + name.replace('.', '-').lower()
            refs.append({'artifact_id': aid, 'sha256': digest(raw), 'byte_size': len(raw),
                         'media_type': 'text/markdown' if name.endswith('.md') else 'application/json',
                         'path_hint': f'schema v0.1/Paper Agent/{name}'})
            self.artifacts.append(SuppliedArtifact(aid, refs[-1]['media_type'], raw))
        return refs

    def main_artifact(self):
        return next(u['artifact'] for u in self.units if u['relative_path'] == 'Pauli_Spectrum.tex')


PREV = {2: '1-source', 3: '2-claims', 4: '3-semantics', 5: '4-math'}


# ===================== the five model rounds ==============================

def open_item(target, missing, checked, nxt):
    return f'target={target}; missing={missing}; checked={checked}; next={nxt}'


def follow_up(agent, operation, refs, target, need, purpose):
    return {'agent': agent, 'operation': operation, 'input_refs': list(refs),
            'reason': f'target={target}; need={need}; purpose={purpose}'}


def draft(records, open_items, follow_ups):
    return {'draft_version': '1.1', 'records': records,
            'open_items': open_items, 'follow_up_requests': follow_ups}


def round_1(host):
    """Source positions and document structure."""
    raw = (host.source_dir / 'Pauli_Spectrum.tex').read_bytes()
    artifact = host.main_artifact()
    main = unit_id('Pauli_Spectrum.tex')
    records, host.span_order = [], sorted(host.seed['spans'])
    for key in host.span_order:
        spec = host.seed['spans'][key]
        start_marker, end_marker = spec['start_marker'].encode(), spec['end_marker'].encode()
        if raw.count(start_marker) != 1:
            raise SystemExit(f'span {key}: start marker is not unique in the source')
        start = raw.index(start_marker)
        end = raw.find(end_marker, start)
        if end < 0:
            raise SystemExit(f'span {key}: end marker not found after start')
        end += len(end_marker)
        records.append({'record_type': 'agtxiv.v3.source-span/0.0.0', 'payload': {
            'source_ref': host.snapshot_ref, 'artifact': artifact, 'locator_kind': 'RAW_TEXT_BYTES',
            'byte_start': start, 'byte_end': end, 'span_sha256': digest(raw[start:end]),
            'pdf_region': None, 'transformation_ref': None, 'locator': spec['locator'],
            'activity': 'ACTIVE'}})
    records.append({'record_type': 'agtxiv.v3.paper-structure/0.0.0', 'payload': {
        'source_ref': host.snapshot_ref, 'main_unit_id': main,
        'edges': [{'source_unit_id': main, 'target_unit_id': unit_id(e['path']),
                   'relation': 'REFERENCES' if Path(e['path']).suffix == '.bib' else 'INCLUDES',
                   'activity': 'ACTIVE' if Path(e['path']).suffix != '.json' else 'UNKNOWN',
                   'locator': r'\includegraphics / \bibliography in Pauli_Spectrum.tex'}
                  for e in host.acq['files'] if e['path'] not in {'Pauli_Spectrum.tex', '00README.json'}],
        'unclassified_unit_ids': [unit_id('00README.json')],
        'blockers': [
            'No LaTeX compilation was run, so include and graphics edges are read off the source text rather than from a build log.',
            'Figure files were never opened; every edge to a figure is a textual reference, not a verified rendering.',
            'Pauli_SpectrumNotes.bib is declared "ignore" by 00README.json and is not reachable from the main text.',
        ]}})
    items = [
        open_item('unit:figures-* (12 figure files)', 'image contents',
                  'byte inventory and hash only', 'a reader able to open PDF and PNG figures, if any figure-based claim is to be checked'),
        open_item('unit:draft-ref-bib', 'the cited works themselves',
                  'bibliography file inventoried, not parsed into entries',
                  'a dependency.search round once claims are registered'),
        open_item('Pauli_Spectrum.tex line 2723 (end of document)', 'nothing further',
                  'the whole file was read end to end in a fixed order',
                  'no further source acquisition for this version'),
    ]
    return records, items, []


def round_2(host):
    """Definitions and author claims."""
    records = []
    host.def_index, host.claim_index = {}, {}
    for d in host.seed['definitions']:
        host.def_index[d['id']] = len(records)
        records.append({'record_type': 'agtxiv.v3.definition/0.0.0', 'payload': {
            'name': d['name'], 'statement': d['statement'],
            'objects': [{'symbol': o['symbol'], 'object_type': o['object_type'],
                         'definition_refs': [], 'unit': o['unit'], 'convention': o['convention']}
                        for o in d['objects']],
            'source_span_refs': [host.span_refs[s] for s in d['spans']], 'origin': d['origin']}})
    for c in host.seed['claims']:
        spans = [host.span_refs[s] for s in c['spans']]
        comp_spans = {x['component_id']: [host.span_refs[s] for s in x['spans']] for x in c['components']}
        provenance = list({json.dumps(r, sort_keys=True): r for r in
                           spans + [r for v in comp_spans.values() for r in v]
                           + [host.span_refs[s] for x in c['conditions'] for s in x['spans']]}.values())
        host.claim_index[c['id']] = len(records)
        records.append({'record_type': 'agtxiv.v3.scientific-claim/0.0.0', 'payload': {
            'statement': c['statement'], 'source_span_refs': provenance,
            'components': [{'component_id': x['component_id'], 'text': x['text'], 'role': x['role'],
                            'source_span_refs': comp_spans[x['component_id']]} for x in c['components']],
            'conditions': [{'condition_id': x['condition_id'], 'statement': x['statement'],
                            'origin': x['origin'],
                            'source_span_refs': [host.span_refs[s] for s in x['spans']]}
                           for x in c['conditions']],
            'modality': c['modality'], 'attribution': c['attribution'],
            'system': c['system'], 'comparison_baseline': c['comparison_baseline']}})
    unmathed = [(c['id'], x['component_id']) for c in host.seed['claims'] for x in c['components']
                if x['role'] == 'CONCLUSION' and 'math' not in x]
    items = [
        open_item(f'{len(unmathed)} CONCLUSION components across {len({i for i, _ in unmathed})} claims',
                  'a mathematical target',
                  'each such component carries a per-component reason in its correspondence row',
                  'author clarification of the missing definition, range or quantifier; no target is invented here'),
        open_item('component:definition-* rows in A02, A23, A41, A64, A65',
                  'nothing: these are definitional components already carried by Definition records',
                  'cross-checked against the 16 Definition records of this round',
                  'no further work'),
        open_item('A53 component:conclusion-1 (quoted stabilizer-fidelity lower bound)',
                  'a usable form of the quoted inequality, which as printed contradicts F_Stab <= 1',
                  'the citing sentence only; no cited paper was retrieved',
                  'a dependency.search round to retrieve the cited bound'),
    ]
    ups = [follow_up('dependency', 'dependency.search', [host.snapshot_ref],
                     'the imported definitions and bounds cited in Sec. II C, Sec. IV C-E and Sec. VI A',
                     'the cited statements of the stabilizer Renyi monotonicity range, the nu-compressible equivalence, the Haar Pauli-spectrum density, the Bell-sampling moment primitive and the stabilizer-fidelity lower bound',
                     'to decide whether each import is used within its stated conditions, and to resolve the printed fidelity bound')]
    return records, items, ups


def round_3(host):
    """Scientific readings that the mathematical targets cannot carry."""
    records = []
    host.sem_index = {}
    for c in host.seed['claims']:
        s = c.get('semantic')
        if not s:
            continue
        host.sem_index[c['id']] = len(records)
        records.append({'record_type': 'agtxiv.v3.semantic-context/0.0.0', 'payload': {
            'claim_ref': host.claim_refs[c['id']], 'physical_system': s['physical_system'],
            'object_mapping': [{**m, 'witness_refs': []} for m in s['object_mapping']],
            'assumptions': [{'condition_id': a['condition_id'], 'statement': a['statement'],
                             'origin': a['origin'],
                             'source_span_refs': [host.span_refs[x] for x in a['spans']]}
                            for a in s['assumptions']],
            'approximation_regime': s['approximation_regime'], 'error_bound': s['error_bound'],
            'observables': s['observables'], 'limitations': s['limitations']}})
    items = [open_item('A59, A62 (numerical application sections)',
                       'measured data, code, geometries and tolerances behind every figure',
                       'the prose and figure captions only; nothing was executed',
                       'author-supplied data or an independent reproduction round'),
             open_item('all other claims',
                       'nothing: no SemanticContext is emitted where the MathClaim and Definition records already carry the meaning',
                       'each claim was checked for physical content beyond its mathematical target',
                       'no further work')]
    return records, items, []


def round_4(host):
    """Mathematical targets, one per fully expressible CONCLUSION component."""
    records = []
    host.math_index = {}
    for c in host.seed['claims']:
        for comp in c['components']:
            m = comp.get('math')
            if not m:
                continue
            key = (c['id'], comp['component_id'])
            host.math_index[key] = len(records)
            records.append({'record_type': 'agtxiv.v3.math-claim/0.0.0', 'payload': {
                'claim_ref': host.claim_refs[c['id']], 'component_ids': [comp['component_id']],
                'objects': [{'symbol': o['symbol'], 'object_type': o['object_type'],
                             'definition_refs': [host.def_refs[d] for d in o['definition_ids']],
                             'unit': o['unit'], 'convention': o['convention']} for o in m['objects']],
                'quantifiers': m['quantifiers'],
                'assumptions': [{'condition_id': a['condition_id'], 'statement': a['statement'],
                                 'origin': a['origin'],
                                 'source_span_refs': [host.span_refs[x] for x in a['spans']]}
                                for a in m['assumptions']],
                'conclusion': m['conclusion'], 'exactness': m['exactness'],
                'approximation_error': m['approximation_error'],
                'definition_refs': [host.def_refs[d] for d in m['definition_ids']],
                'semantic_refs': ([host.sem_refs[c['id']]] if c['id'] in host.sem_refs else []),
                'normalization': m['normalization']}})
    items = [open_item('every APPROXIMATE or ASYMPTOTIC target',
                       'quantified error terms where the source writes only o(1), logPoly(n) or an ellipsis',
                       'the printed statements; no error bound was manufactured',
                       'author clarification, which R6 requires rather than an invented bound'),
             open_item('A46 (stabilizer-work limits), A51 (SPS separation criterion)',
                       'the function, expansion order and constants the two limit statements would need',
                       'the whole main text and supplement were searched for a derivation; none is present',
                       'author-supplied expansions before these can become targets')]
    ups = [follow_up('proof', 'proof.expand', [host.snapshot_ref],
                     'the mathematical targets whose proofs are deferred in the source: the Lipschitz property, the Haar SPF theorem, the SPS SPF theorem and the reweighting step behind sub-additivity',
                     'expansion of the deferred proofs and of the asserted reweighting hypothesis, together with the proof locations recorded as source spans',
                     'to establish whether the deferred arguments close, which this extraction does not and cannot decide')]
    return records, items, ups


def round_5(host):
    """Correspondence, discovery and open items."""
    records = []
    for c in host.seed['claims']:
        claim_ref = host.claim_refs[c['id']]
        sem = host.sem_refs.get(c['id'])
        mappings = []
        for comp in c['components']:
            key = (c['id'], comp['component_id'])
            math_ref = host.math_refs.get(key)
            residual = comp['residual']
            if math_ref:
                mappings.append({'component_id': comp['component_id'], 'math_refs': [math_ref],
                                 'semantic_refs': [sem] if sem else [], 'evidence_refs': [],
                                 'disposition': 'MAPPED', 'residual': residual})
            elif sem and comp['role'] in {'MODEL', 'EVIDENCE', 'LIMITATION', 'APPROXIMATION'}:
                mappings.append({'component_id': comp['component_id'], 'math_refs': [],
                                 'semantic_refs': [sem], 'evidence_refs': [],
                                 'disposition': 'MAPPED', 'residual': residual})
            elif comp['role'] == 'ATTRIBUTION':
                mappings.append({'component_id': comp['component_id'], 'math_refs': [],
                                 'semantic_refs': [], 'evidence_refs': [], 'disposition': 'NON_CLAIM',
                                 'residual': residual or 'Attribution of the statement, not a claim of the paper.'})
            else:
                mappings.append({'component_id': comp['component_id'], 'math_refs': [],
                                 'semantic_refs': [], 'evidence_refs': [],
                                 'disposition': 'UNRESOLVED' if comp['unresolved'] else 'RESIDUAL',
                                 'residual': residual or (
                                     'Not mathematized in this round. The component meaning is retained verbatim '
                                     'in the claim record; no MathClaim was produced for it.')})
        coverage = 'COMPLETE' if all(m['disposition'] == 'MAPPED' for m in mappings) else 'PARTIAL'
        records.append({'record_type': 'agtxiv.v3.claim-component-map/0.0.0', 'payload': {
            'claim_ref': claim_ref, 'mappings': mappings,
            'review': {
                'reviewed_refs': [claim_ref], 'producer_principal_ids': [PRINCIPAL],
                'independence': 'UNESTABLISHED',
                'conflicts': [
                    'The claim and this correspondence map were produced by the same principal in the same execution.',
                    'No second model, process or person inspected either record.',
                    'AGENT.md 1.1 R8 requires this state to be recorded rather than repaired; no reviewer was manufactured.',
                ],
                'method': ('Component-by-component accounting against the exact source spans: every component is '
                           'MAPPED to a mathematical or semantic target, kept as RESIDUAL with its meaning stated, '
                           'marked UNRESOLVED where the printed source cannot be read consistently, or NON_CLAIM. '
                           'This is a producer self-accounting, not a review.'),
                'evidence_refs': []},
            'coverage': coverage}})

    for c in host.seed['claims']:
        targets = [host.claim_refs[c['id']]] + [
            host.math_refs[(c['id'], x['component_id'])] for x in c['components']
            if (c['id'], x['component_id']) in host.math_refs]
        for f in c['frontier']:
            records.append({'record_type': 'agtxiv.v3.frontier-item/0.0.0', 'payload': {
                'target_refs': targets, 'kind': f['kind'], 'axes': f['axes'],
                'statement': f['statement'], 'next_evidence': f['next_evidence'],
                'attempt_refs': [], 'state': 'OPEN', 'resolution_refs': []}})

    obligations = []
    for e in host.acq['files']:
        path, uid = e['path'], unit_id(e['path'])
        if path == 'Pauli_Spectrum.tex':
            obligations.append({'obligation_id': f'obligation:{RUN}/source-main',
                                'target_refs': [host.snapshot_ref, host.structure_ref],
                                'source_unit_ids': [uid], 'stage': 'SOURCE', 'requirement': 'SUCCESS_REQUIRED',
                                'applicable_axes': ['source_fidelity'],
                                'reason': 'The single top-level TeX file carries the whole text of the paper and its supplemental material.'})
        elif path in {'00README.json', 'draft_ref.bib', 'Pauli_SpectrumNotes.bib'}:
            obligations.append({'obligation_id': f'obligation:{RUN}/source-{uid.removeprefix("unit:")}',
                                'target_refs': [host.snapshot_ref],
                                'source_unit_ids': [uid], 'stage': 'SOURCE', 'requirement': 'ACCOUNT_FOR',
                                'applicable_axes': ['source_fidelity'],
                                'reason': 'Text unit inventoried and opened, but no claim of the paper is carried by it; cited works were not retrieved.'})
        else:
            obligations.append({'obligation_id': f'obligation:{RUN}/source-{uid.removeprefix("unit:")}',
                                'target_refs': [], 'source_unit_ids': [uid], 'stage': 'SOURCE',
                                'requirement': 'ACCOUNT_FOR', 'applicable_axes': ['source_fidelity'],
                                'reason': 'Figure bytes inventoried by hash only. The image was never opened, so every figure-based statement in the paper is unverified here.'})
    obligations.append({'obligation_id': f'obligation:{RUN}/inventory', 'target_refs': [host.structure_ref],
                        'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'INVENTORY',
                        'requirement': 'SUCCESS_REQUIRED', 'applicable_axes': ['source_fidelity'],
                        'reason': 'Sectioning, theorem environments and supplemental structure must be located before claims can be attributed to positions in the source.'})
    for c in host.seed['claims']:
        obligations.append({'obligation_id': f'obligation:{RUN}/claim-{c["id"]}',
                            'target_refs': [host.claim_refs[c['id']]],
                            'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'CLAIM',
                            'requirement': 'SUCCESS_REQUIRED', 'applicable_axes': ['source_fidelity'],
                            'reason': f'{c["section"]} | {c["kind"]} | {c["label"]}'})
    for cid in sorted(host.sem_refs):
        obligations.append({'obligation_id': f'obligation:{RUN}/semantics-{cid}',
                            'target_refs': [host.sem_refs[cid]],
                            'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'SEMANTICS',
                            'requirement': 'ACCOUNT_FOR', 'applicable_axes': ['semantic_applicability'],
                            'reason': 'Physical reading of a numerical application: what the computed quantity is a property of, and under which representational choices.'})
    for cid in ('A54', 'A60', 'A61', 'A62', 'A63', 'A80'):
        obligations.append({'obligation_id': f'obligation:{RUN}/computation-{cid}',
                            'target_refs': [host.claim_refs[cid]],
                            'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'COMPUTATION',
                            'requirement': 'ACCOUNT_FOR', 'applicable_axes': ['computational_reproducibility'],
                            'reason': 'Numerical result reported without data or code. Accounted for as unreproduced; nothing was executed in this run.'})

    records.append({'record_type': 'agtxiv.v3.inventory-discovery/0.0.0', 'payload': {
        'plan_ref': host.plan_ref, 'structure_ref': host.structure_ref,
        'classified_unit_ids': [unit_id(e['path']) for e in host.acq['files'] if e['path'] != '00README.json'],
        'unclassified_unit_ids': [unit_id('00README.json')],
        'obligations': obligations,
        'claim_refs': [host.claim_refs[c['id']] for c in host.seed['claims']],
        'coverage_rationale': (
            'Proposed denominator, NOT frozen. One SOURCE obligation per inventoried unit, one INVENTORY '
            'obligation for the document structure, one CLAIM obligation per source assertion unit, one '
            'SEMANTICS obligation per numerical application that needed a physical reading, and one '
            'COMPUTATION obligation per unreproduced numerical result. Claim obligations follow R2: one '
            'numbered assertion is one obligation and numbered results are never merged, while unnumbered '
            'prose contributes the minimal contiguous range that carries a complete assertion. The count is '
            'therefore a reading of this text under a stated rule, not a canonical atomisation, and it is '
            'not a target for agreement with any other run. Unknowns stay inside the denominator as '
            'obligations with empty target_refs rather than being dropped. This record cannot become a '
            'frozen-scope in this run: AGENT.md 1.1 leaves scope freezing outside Paper Agent, and the '
            'accepting scope-decision it requires must come from a principal other than the discoverer, '
            'which this single-principal execution does not have.')}})

    items = [
        open_item(f'{sum(1 for c in host.seed["claims"] for x in c["components"] if x["unresolved"])} UNRESOLVED component rows',
                  'a readable form of the printed source at those points',
                  'each row names what cannot be read consistently and why',
                  'errata or author clarification; R4 and R8 forbid repairing them here'),
        open_item('every claim-component-map in this round',
                  'an independent reviewer',
                  'producer self-accounting only; independence is declared UNESTABLISHED',
                  'a review.scope round by a different principal, without which the full record set stays blocked'),
        open_item(f'obligation:{RUN}/* (the proposed denominator)',
                  'an accepting scope-decision from a second principal',
                  'the denominator was formed and is internally consistent with the plan and the structure',
                  'review.scope; no frozen-scope exists and none was fabricated'),
    ]
    ups = [follow_up('review', 'review.scope',
                     [host.snapshot_ref, host.structure_ref, host.plan_ref, host.profile_ref],
                     'the inventory-discovery of this round, together with the plan, the structure and the standard',
                     'an independent reviewer able to accept or block the proposed obligation denominator',
                     'to reach a frozen-scope, which Paper Agent cannot produce and which proof.expand requires')]
    return records, items, ups


ROUNDS = [
    (1, 'source', round_1, ['source-span', 'paper-structure'], 'SOURCE_PRODUCER',
     'Locate every assertion-bearing range of the supplied TeX and record the document structure. Read the '
     'file end to end in a fixed order. Give byte positions for the host to verify against the actual bytes; '
     'do not compute hashes by hand. Record what was not read rather than omitting it.'),
    (2, 'claims', round_2, ['definition', 'scientific-claim'], 'CLAIM_PRODUCER',
     'Extract the definitions and the author claims from the registered source spans, following R1-R5: one '
     'ScientificClaim per numbered assertion, never merging different numbered results; for unnumbered text '
     'the minimal contiguous range carrying a complete assertion; components ordered by appearance with at '
     'least one CONCLUSION each; every source condition citing its own span; assertion strength by the fixed '
     'CONFORMANCE ladder. Do not add or import premises.'),
    (3, 'semantics', round_3, ['semantic-context'], 'CLAIM_PRODUCER',
     'Emit a SemanticContext only where the physical correspondence, observables, applicability range or '
     'approximation reading cannot be carried by a MathClaim and a Definition (R7). Do not copy a template '
     'per claim, and do not drop scientific content that cannot yet be mathematized.'),
    (4, 'math', round_4, ['math-claim'], 'CLAIM_PRODUCER',
     'Produce one MathClaim per fully expressible CONCLUSION component (R6): objects taken from the target '
     'own variables and carriers rather than copied from the definition table, definition references limited '
     'to what is actually used, quantifier order preserved, all applicable premises present, and the '
     'exact/approximate/asymptotic character with the error information the source gives. Where a definition '
     'or range is missing, produce no target and state the reason per component.'),
    (5, 'maps', round_5, ['claim-component-map', 'inventory-discovery', 'frontier-item'], 'CLAIM_PRODUCER',
     'Account for every component: mapped, residual with its meaning preserved, unresolved, or non-claim '
     '(R8). Declare independence UNESTABLISHED; do not claim independent review. Propose the obligation '
     'denominator without freezing it, and record the gaps and follow-up requests.'),
]


# ============================ driver =====================================

def run(out: Path):
    host = Host(out)
    host.context()
    spec_refs = host.spec_artifacts()
    tex_ref = host.main_artifact()
    registered = list(host.context_refs)
    rounds_report = []

    for index, slug, builder, expected, role, brief in ROUNDS:
        draft_records, items, ups = builder(host)
        task = host.task(index, slug,
                         brief=brief,
                         targets=[host.snapshot_ref] if index == 1 else [host.structure_ref],
                         inputs=registered, expected=expected,
                         artifacts=[tex_ref] + spec_refs)
        document = draft(draft_records, items, ups)
        directory = out / 'rounds' / f'round-{index}-{slug}'
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'task.json').write_text(json.dumps(task, ensure_ascii=False, indent=1) + '\n')
        (directory / 'draft.json').write_text(json.dumps(document, ensure_ascii=False, indent=1) + '\n')

        first = len(host.records)
        refs = [host.register(record, role=role, execution=ROUND_EXEC[index],
                              inputs=registered, record_id=record_id(host, index, position, record))
                for position, record in enumerate(draft_records)]
        assembled = host.records[first:]
        (directory / 'records.json').write_text(json.dumps(assembled, ensure_ascii=False, indent=1) + '\n')
        bind(host, index, refs)
        registered = registered + refs
        rounds_report.append({'round': index, 'slug': slug, 'task_id': task['task_id'],
                              'draft_records': len(draft_records), 'assembled_records': len(assembled),
                              'expected_record_types': expected,
                              'open_items': len(items), 'follow_up_requests': len(ups),
                              'result_written': False,
                              'note': 'No Result receipt: this run has no scheduler, no runtime identity and no execution facts to report.'})

    return host, rounds_report


def record_id(host, index, position, record):
    name = record['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0')
    if index == 1:
        return (f'span:{RUN}/{host.span_order[position]}' if name == 'source-span'
                else f'structure:{RUN}')
    if index == 2:
        if name == 'definition':
            return f'definition:{RUN}/{host.seed["definitions"][position]["id"]}'
        claim = host.seed['claims'][position - len(host.seed['definitions'])]
        return f'claim:{RUN}/{claim["id"]}'
    if index == 3:
        cid = [c['id'] for c in host.seed['claims'] if 'semantic' in c][position]
        return f'semantics:{RUN}/{cid}'
    if index == 4:
        key = [(c['id'], x['component_id']) for c in host.seed['claims'] for x in c['components']
               if 'math' in x][position]
        return f'math:{RUN}/{key[0]}-{key[1].removeprefix("component:")}'
    maps = len(host.seed['claims'])
    if position < maps:
        return f'map:{RUN}/{host.seed["claims"][position]["id"]}'
    frontier = [(c['id'], i) for c in host.seed['claims'] for i, _ in enumerate(c['frontier'], 1)]
    if position < maps + len(frontier):
        cid, i = frontier[position - maps]
        return f'frontier:{RUN}/{cid}-{i:02d}'
    return f'discovery:{RUN}'


def bind(host, index, refs):
    if index == 1:
        host.span_refs = dict(zip(host.span_order, refs[:-1]))
        host.structure_ref = refs[-1]
    elif index == 2:
        host.def_refs = {d['id']: refs[host.def_index[d['id']]] for d in host.seed['definitions']}
        host.claim_refs = {c['id']: refs[host.claim_index[c['id']]] for c in host.seed['claims']}
    elif index == 3:
        host.sem_refs = {cid: refs[i] for cid, i in host.sem_index.items()}
    elif index == 4:
        host.math_refs = {key: refs[i] for key, i in host.math_index.items()}


def write_outputs(host, rounds_report, out: Path):
    (out / 'records.json').write_text(json.dumps(host.records, ensure_ascii=False, indent=1) + '\n')
    report = RecordSet(host.bundle, host.records, host.artifacts).validate(require_artifacts=True)
    issues = [{'code': i.code, 'record_id': i.record_id, 'path': i.path, 'message': i.message}
              for i in report.issues]
    without_maps = [r for r in host.records
                    if not r['record_type'].startswith('agtxiv.v3.claim-component-map')]
    subset = RecordSet(host.bundle, without_maps, host.artifacts).validate(require_artifacts=True)
    (out / 'diagnostics' / 'records-without-maps.json').write_text(
        json.dumps(without_maps, ensure_ascii=False, indent=1) + '\n')

    counts: dict[str, int] = {}
    for record in host.records:
        counts[record['record_type']] = counts.get(record['record_type'], 0) + 1

    validation = {
        'validation_version': 'paper-agent/1.1',
        'scope': 'OFFLINE_DIAGNOSTIC: record shape, reference closure, source bytes and payload preservation. No independent review, no runtime identity, no scientific check.',
        'rounds': rounds_report,
        'payload_preserved_before_and_after_assembly': {
            'records_checked': host.payload_preserved, 'all_equal': True,
            'method': 'canonical JSON of payload compared before and after envelope filling'},
        'single_record_shapes_and_hashes': {'checked': len(host.records), 'valid': True},
        'full_record_set': {'records': len(host.records), 'valid': report.valid,
                            'issue_codes': sorted({i['code'] for i in issues}),
                            'issue_count': len(issues), 'issues': issues},
        'diagnostic_subset_without_correspondence_maps': {
            'records': len(without_maps), 'valid': subset.valid,
            'issue_codes': sorted({i.code for i in subset.issues}),
            'meaning': ('Everything except the producer-authored correspondence maps closes: every exact '
                        'reference resolves, every source span re-hashes against the real paper bytes, and '
                        'every record shape is accepted. This subset is a diagnostic, not a deliverable, '
                        'because R8 requires a correspondence row for every component.')},
        'source_bytes': {'files_rehashed': len(host.acq['files']),
                         'spans_rehashed': len(host.span_refs),
                         'method': 'every unit re-read from the repository and digested; every span digest recomputed from the selected byte range'},
        'not_established': [
            'No claim of the paper was checked for truth.',
            'No mathematical target was proved, disproved or formalized.',
            'No numerical result of the paper was reproduced; nothing was executed against the physics.',
            'No cited work was retrieved, so every attribution is to the citing text only.',
            'No identity was authenticated; identity_assurance is DECLARED on every record.',
            'No scope was frozen and no Result receipt was produced.',
        ],
        'byte_artifacts_checked': report.byte_artifacts_checked,
        'authority_checked': report.authority_checked,
        'limitations': list(report.limitations),
    }
    checker = load_checker()
    spec_checks = {'checker': 'schema v0.1/Paper Agent/check_output.py', 'rounds': [], 'records': None}
    instance = checker.OutputChecker()
    for entry in rounds_report:
        directory = out / 'rounds' / f'round-{entry["round"]}-{entry["slug"]}'
        result = instance.check_draft(json.loads((directory / 'draft.json').read_text()),
                                      json.loads((directory / 'task.json').read_text()))
        (directory / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n')
        spec_checks['rounds'].append({
            'round': entry['round'], 'error_count': result['error_count'],
            'missing_expected_record_types': result['missing_expected_record_types'],
            'failed_layers': sorted(k for k, v in result['layers'].items() if v['checked'] and not v['passed']),
            'unchecked_layers': sorted(k for k, v in result['layers'].items() if not v['checked'])})
    records_result = instance.check_records(host.records)
    spec_checks['records'] = {
        'record_count': records_result['record_count'],
        'paper_record_count': records_result['paper_record_count'],
        'error_count': records_result['error_count'],
        'failed_layers': sorted(k for k, v in records_result['layers'].items() if v['checked'] and not v['passed'])}
    (out / 'diagnostics' / 'check-output-records.json').write_text(
        json.dumps(records_result, ensure_ascii=False, indent=1) + '\n')
    validation['specification_checker'] = spec_checks
    validation['input_refs_convention'] = (
        "Each record's input_refs and producer.visible_input_refs are the exact references appearing in "
        "that record's own payload, i.e. what it was actually built from. The complete catalog visible in "
        "each round is that round's Task.input_refs, stored in rounds/*/task.json; it is not repeated on "
        "every record.")
    (out / 'validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=1) + '\n')
    render_claims(host, out)

    files = []
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.name != 'manifest.json':
            raw = path.read_bytes()
            files.append({'path': str(path.relative_to(out)), 'sha256': digest(raw), 'byte_size': len(raw)})
    manifest = {
        'manifest_version': 'paper-agent/1.1', 'run_id': RUN, 'mode': 'OFFLINE_DIAGNOSTIC',
        'source_refs': [host.snapshot_ref],
        'spec_files': [{'path': f'schema v0.1/Paper Agent/{name}',
                        'sha256': digest((SPECDIR / name).read_bytes())}
                       for name in SPEC_FILES],
        'schema_bundle_hash': host.bundle.bundle_hash,
        'model': {'provider': None, 'model_id': MODEL_ID,
                  'settings': {'execution': 'single interactive session',
                               'principals': 1,
                               'independent_reviewer': False,
                               'tools_used': 'local filesystem reads of the arXiv source archive only',
                               'network_access': 'none during extraction'}},
        'files': files, 'record_counts': counts,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=RUN_DIR)
    args = parser.parse_args()
    host, rounds_report = run(args.output)
    validation = write_outputs(host, rounds_report, args.output)
    print(json.dumps({
        'run': RUN, 'mode': 'OFFLINE_DIAGNOSTIC',
        'records': len(host.records),
        'rounds': [{'round': r['round'], 'draft': r['draft_records']} for r in rounds_report],
        'payload_preserved': validation['payload_preserved_before_and_after_assembly']['records_checked'],
        'full_record_set_valid': validation['full_record_set']['valid'],
        'issue_codes': validation['full_record_set']['issue_codes'],
        'issue_count': validation['full_record_set']['issue_count'],
        'subset_valid': validation['diagnostic_subset_without_correspondence_maps']['valid'],
    }, indent=2))
    return 0 if validation['full_record_set']['valid'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
