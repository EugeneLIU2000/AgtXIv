#!/usr/bin/env python3
"""Assemble the v0.0 record set for this Paper Agent run from extraction/seed.json.

This script performs no model call and reads no new material. It replays one
already-completed extraction into records, computing every source-span offset
and digest from the actual paper bytes. Building successfully establishes
record shape and reference closure only; it establishes nothing scientific.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'src'))
from agtxiv_v3.contracts import SchemaBundle, RecordSet, SuppliedArtifact, digest, exact_ref  # noqa: E402

RUN = 'opus5-2608.14798v1'
PRINCIPAL = f'session:{RUN}'
RUN_AT = '2026-09-13T00:00:00Z'
MODEL = 'claude-opus-5 (single interactive execution; no separate reviewer process)'

EXEC = {
    'MAINTAINER': f'exec:{RUN}/s0-context',
    'COORDINATOR': f'exec:{RUN}/s0-plan',
    'SOURCE_PRODUCER': f'exec:{RUN}/s1-source',
    'CLAIM_PRODUCER': f'exec:{RUN}/s3-claims',
}

# Components whose source text cannot be read consistently as printed, so no
# representation is proposed at all. Everything else that is not mathematized
# is RESIDUAL: meaning preserved, no MathClaim produced.
UNRESOLVED = {('c04', 'comp:tighter'), ('c07', 'comp:rewrite'), ('c27', 'comp:lb')}

MEDIA = {'.tex': 'text/x-tex', '.bib': 'text/x-bibtex', '.json': 'application/json',
         '.png': 'image/png', '.pdf': 'application/pdf'}
KIND = {'.tex': 'TEX', '.bib': 'BIBLIOGRAPHY', '.json': 'OTHER', '.png': 'FIGURE', '.pdf': 'FIGURE'}


def unit_id(path: str) -> str:
    slug = path.replace('/', '-').replace('_', '-').replace('.', '-').lower()
    return 'unit:' + slug


class Builder:
    def __init__(self, out: Path):
        self.out = out
        self.bundle = SchemaBundle(REPO / 'schema v0.0')
        self.records: list[dict] = []
        self.policy_ref: dict | None = None
        self.seed = json.loads((HERE / 'extraction' / 'seed.json').read_text())
        self.acq = json.loads((HERE / 'acquisition.json').read_text())
        self.source_dir = REPO / self.acq['source_directory']
        self.artifacts: list[SuppliedArtifact] = []

    def add(self, name, record_id, payload, role, inputs=(), visible=None, policy=True):
        inputs = list(inputs)
        producer = {
            'principal_id': PRINCIPAL, 'role': role, 'actor_kind': 'AGENT',
            'identity_assurance': 'DECLARED', 'execution_id': EXEC[role], 'model': MODEL,
            'visible_input_refs': list(inputs if visible is None else visible),
            'identity_evidence': [],
        }
        record = self.bundle.make_record(
            name, record_id, payload, producer=producer,
            policy_ref=self.policy_ref if policy else None,
            input_refs=inputs, created_at=RUN_AT, data_class='RESEARCH')
        self.records.append(record)
        return exact_ref(record)

    # ---- S0 context -----------------------------------------------------
    def context(self):
        self.policy_ref = self.add('authority-policy', f'policy:{RUN}', {
            'charter_identity': 'AgtXIv-Charter/1.0',
            'charter_state': 'PROPOSED',
            'ratification_commit': None,
            'minimum_identity_assurance': 'LOCALLY_ATTESTED',
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
        }, 'MAINTAINER', policy=False)
        # The policy record carries no policy_ref; every later record binds to it.
        self.profile_ref = self.add('processing-profile', f'profile:{RUN}', {
            'name': 'V3_SOURCE_MAP',
            'required_stages': ['SOURCE', 'INVENTORY', 'CLAIM', 'SEMANTICS', 'COMPUTATION'],
            'success_required_stages': ['SOURCE', 'INVENTORY', 'CLAIM'],
            'required_axes': ['source_fidelity', 'mathematical_correctness', 'formal_alignment',
                              'semantic_applicability', 'empirical_support', 'computational_reproducibility'],
            'allowed_terminal_outcomes': ['DELIVERED', 'BLOCKED', 'DEFERRED'],
            'empirical_requirement': 'ACCOUNT_FOR',
            'computation_requirement': 'ACCOUNT_FOR',
            'non_implications': [
                'Completing this profile does not establish that any claim of the paper is true.',
                'Completing this profile does not establish that any mathematical target is provable or proved.',
                'Completing this profile does not reproduce or check any numerical result of the paper.',
                'Completing this profile does not constitute independent review of the extraction.',
            ],
        }, 'MAINTAINER')

    # ---- S1 source ------------------------------------------------------
    def source(self):
        units = []
        for entry in self.acq['files']:
            path = entry['path']
            suffix = Path(path).suffix
            raw = (self.source_dir / path).read_bytes()
            assert digest(raw) == entry['sha256'] and len(raw) == entry['bytes'], path
            artifact = {'artifact_id': 'artifact:' + unit_id(path).removeprefix('unit:'),
                        'sha256': entry['sha256'], 'byte_size': entry['bytes'],
                        'media_type': MEDIA[suffix], 'path_hint': path}
            self.artifacts.append(SuppliedArtifact(artifact['artifact_id'], artifact['media_type'], raw))
            units.append({'unit_id': unit_id(path), 'relative_path': path, 'artifact': artifact,
                          'activity': 'ACTIVE' if path in {'Pauli_Spectrum.tex', '00README.json', 'draft_ref.bib'} else 'UNKNOWN',
                          'kind': KIND[suffix]})
        archive = {'artifact_id': f'artifact:{RUN}-archive', 'sha256': self.acq['archive_sha256'],
                   'byte_size': self.acq['archive_bytes'], 'media_type': 'application/gzip'}
        self.snapshot_units = units
        self.snapshot_ref = self.add('source-snapshot', f'source:{RUN}', {
            'paper_id': 'arXiv:2608.14798', 'paper_version': '2608.14798v1',
            'source_uri': self.acq['source_uri'], 'acquired_at': self.acq['verified_at'],
            'acquisition_ref': None, 'acquisition_method': 'LOCAL_IMPORT',
            'units': units, 'archive': archive,
            'missing_material': [
                'No compiled PDF was produced or inspected; figure PDFs and PNGs were inventoried by hash only and their contents were not read.',
                'draft_ref.bib and Pauli_SpectrumNotes.bib were inventoried but no cited work was retrieved, so every attribution in this run is to the citing text only.',
                'The numerical data, scripts and geometries behind every figure are absent from the source archive.',
            ],
            'rights_status': 'UNRESOLVED',
            'rights_note': 'arXiv source archive held locally in this repository. No licence statement was located in the source; redistribution rights were not determined in this run.',
        }, 'SOURCE_PRODUCER', inputs=[self.profile_ref])
        # The archive artifact is referenced but its bytes are not supplied to
        # the record set; artifact checking therefore runs over the unit files.
        self.artifacts.append(SuppliedArtifact(archive['artifact_id'], 'application/gzip',
                                               (REPO / self.acq['archive_path']).read_bytes()))
        main = unit_id('Pauli_Spectrum.tex')
        self.structure_ref = self.add('paper-structure', f'structure:{RUN}', {
            'source_ref': self.snapshot_ref, 'main_unit_id': main,
            'edges': [{'source_unit_id': main, 'target_unit_id': unit_id(e['path']),
                       'relation': 'REFERENCES' if Path(e['path']).suffix == '.bib' else 'INCLUDES',
                       'activity': 'ACTIVE' if Path(e['path']).suffix != '.json' else 'UNKNOWN',
                       'locator': r'\includegraphics / \bibliography in Pauli_Spectrum.tex'}
                      for e in self.acq['files'] if e['path'] != 'Pauli_Spectrum.tex' and e['path'] != '00README.json'],
            'unclassified_unit_ids': [unit_id('00README.json')],
            'blockers': [
                'No LaTeX compilation was run, so include/graphics edges are read off the source text and not from a build log.',
                'Figure files were not opened; every edge to a figure is a textual reference, not a verified rendering.',
                'Pauli_SpectrumNotes.bib is declared "ignore" by 00README.json and is not reachable from the main text.',
            ],
        }, 'SOURCE_PRODUCER', inputs=[self.snapshot_ref, self.profile_ref])

    # ---- S0 plan --------------------------------------------------------
    def plan(self):
        self.plan_ref = self.add('agentization-plan', f'plan:{RUN}', {
            'source_ref': self.snapshot_ref, 'profile_ref': self.profile_ref, 'baseline_ref': None,
            'source_unit_ids': [unit_id(e['path']) for e in self.acq['files']],
            'max_steps': 400, 'max_seconds': 86400, 'max_cost_units': 0, 'no_progress_limit': 8,
            'trigger_note': (
                'User asked for a Paper Agent run over arXiv:2608.14798 following '
                'schema v0.1/Paper Agent/AGENT.md. The request is the trigger only; the scope '
                'denominator is the full supplied source inventory. NOTE ON TWO FIELDS: AGENT.md '
                'section 3 drops max_seconds and max_cost_units from the finalized 12-field plan, '
                'but the pinned v0.0 agentization-plan schema requires both as integers, so this '
                'record carries declared placeholders. No wall-clock budget and no cost metering '
                'existed in this run; 86400 was never enforced and 0 must not be read as a measured '
                'zero cost. The AGENT.md-shaped plan is kept beside this run as '
                'output/plan-as-agent-md-specifies.INVALID.json together with the validator error '
                'it produces.'),
        }, 'COORDINATOR', inputs=[self.snapshot_ref, self.profile_ref])

    # ---- S1 spans -------------------------------------------------------
    def spans(self):
        main = unit_id('Pauli_Spectrum.tex')
        artifact = next(u['artifact'] for u in self.snapshot_units if u['unit_id'] == main)
        raw = (self.source_dir / 'Pauli_Spectrum.tex').read_bytes()
        self.span_refs: dict[str, dict] = {}
        for key in sorted(self.seed['spans']):
            spec = self.seed['spans'][key]
            start_marker = spec['start_marker'].encode()
            end_marker = spec['end_marker'].encode()
            if raw.count(start_marker) != 1:
                raise SystemExit(f'span {key}: start marker is not unique in the source')
            start = raw.index(start_marker)
            end = raw.find(end_marker, start)
            if end < 0:
                raise SystemExit(f'span {key}: end marker not found after start')
            end += len(end_marker)
            self.span_refs[key] = self.add('source-span', f'span:{RUN}/{key}', {
                'source_ref': self.snapshot_ref, 'artifact': artifact,
                'locator_kind': 'RAW_TEXT_BYTES', 'byte_start': start, 'byte_end': end,
                'span_sha256': digest(raw[start:end]), 'pdf_region': None,
                'transformation_ref': None, 'locator': spec['locator'], 'activity': 'ACTIVE',
            }, 'SOURCE_PRODUCER', inputs=[self.snapshot_ref])

    # ---- S3 definitions, claims, targets --------------------------------
    def definitions(self):
        self.def_refs = {}
        for d in self.seed['definitions']:
            refs = [self.span_refs[s] for s in d['spans']]
            self.def_refs[d['id']] = self.add('definition', f'definition:{RUN}/{d["id"]}', {
                'name': d['name'], 'statement': d['statement'],
                'objects': [{'symbol': o['symbol'], 'object_type': o['object_type'],
                             'definition_refs': [], 'unit': o['unit'], 'convention': o['convention']}
                            for o in d['objects']],
                'source_span_refs': refs, 'origin': d['origin'],
            }, 'CLAIM_PRODUCER', inputs=refs)

    def claims(self):
        self.claim_refs, self.map_refs, self.math_refs = {}, {}, {}
        self.sem_refs, self.frontier_refs = {}, []
        for c in self.seed['claims']:
            cid = c['id']
            span_refs = [self.span_refs[s] for s in c['spans']]
            comp_spans = {}
            for comp in c['components']:
                comp_spans[comp['component_id']] = [self.span_refs[s] for s in comp['spans']]
            provenance = list({json.dumps(r, sort_keys=True): r
                               for r in span_refs + [r for v in comp_spans.values() for r in v]}.values())
            claim_ref = self.add('scientific-claim', f'claim:{RUN}/{cid}', {
                'statement': c['statement'], 'source_span_refs': provenance,
                'components': [{'component_id': comp['component_id'], 'text': comp['text'],
                                'role': comp['role'], 'source_span_refs': comp_spans[comp['component_id']]}
                               for comp in c['components']],
                'conditions': [{**cond, 'source_span_refs': span_refs[:1]} for cond in c['conditions']],
                'modality': c['modality'], 'attribution': c['attribution'],
                'system': c['system'], 'comparison_baseline': c['comparison_baseline'],
            }, 'CLAIM_PRODUCER', inputs=provenance)
            self.claim_refs[cid] = claim_ref

            sem_ref = None
            if 'semantic' in c:
                s = c['semantic']
                sem_ref = self.add('semantic-context', f'semantics:{RUN}/{s["id"]}', {
                    'claim_ref': claim_ref, 'physical_system': s['physical_system'],
                    'object_mapping': [{**m, 'witness_refs': []} for m in s['object_mapping']],
                    'assumptions': [{**a, 'source_span_refs': []} for a in s['assumptions']],
                    'approximation_regime': s['approximation_regime'], 'error_bound': s['error_bound'],
                    'observables': s['observables'], 'limitations': s['limitations'],
                }, 'CLAIM_PRODUCER', inputs=[claim_ref])
                self.sem_refs[cid] = sem_ref

            math_ref = None
            if 'math' in c:
                m = c['math']
                defs = [self.def_refs[d] for d in m['definition_ids']]
                objects = []
                for did in m['definition_ids']:
                    source = next(x for x in self.seed['definitions'] if x['id'] == did)
                    for o in source['objects']:
                        objects.append({'symbol': o['symbol'], 'object_type': o['object_type'],
                                        'definition_refs': [self.def_refs[did]],
                                        'unit': o['unit'], 'convention': o['convention']})
                math_ref = self.add('math-claim', f'math:{RUN}/{m["id"]}', {
                    'claim_ref': claim_ref, 'component_ids': m['component_ids'],
                    'objects': objects, 'quantifiers': m['quantifiers'],
                    'assumptions': [{**a, 'source_span_refs': []} for a in m['assumptions']],
                    'conclusion': m['conclusion'], 'exactness': m['exactness'],
                    'approximation_error': m['approximation_error'], 'definition_refs': defs,
                    'semantic_refs': [sem_ref] if sem_ref else [], 'normalization': m['normalization'],
                }, 'CLAIM_PRODUCER', inputs=[claim_ref] + defs + ([sem_ref] if sem_ref else []))
                self.math_refs[cid] = math_ref

            mapped_ids = set(c.get('math', {}).get('component_ids', []))
            mappings = []
            for comp in c['components']:
                key = comp['component_id']
                residual = c['residuals'].get(key, '')
                if key in mapped_ids:
                    mappings.append({'component_id': key, 'math_refs': [math_ref],
                                     'semantic_refs': [sem_ref] if sem_ref else [], 'evidence_refs': [],
                                     'disposition': 'MAPPED', 'residual': residual})
                elif (cid, key) in UNRESOLVED:
                    mappings.append({'component_id': key, 'math_refs': [], 'semantic_refs': [],
                                     'evidence_refs': [], 'disposition': 'UNRESOLVED', 'residual': residual})
                elif sem_ref is not None and comp['role'] in {'MODEL', 'EVIDENCE', 'LIMITATION', 'APPROXIMATION'}:
                    mappings.append({'component_id': key, 'math_refs': [], 'semantic_refs': [sem_ref],
                                     'evidence_refs': [], 'disposition': 'MAPPED', 'residual': residual})
                elif comp['role'] == 'ATTRIBUTION':
                    mappings.append({'component_id': key, 'math_refs': [], 'semantic_refs': [],
                                     'evidence_refs': [], 'disposition': 'NON_CLAIM',
                                     'residual': residual or 'Attribution of the statement, not a claim of the paper.'})
                else:
                    mappings.append({'component_id': key, 'math_refs': [], 'semantic_refs': [],
                                     'evidence_refs': [], 'disposition': 'RESIDUAL',
                                     'residual': residual or (
                                         'Not mathematized in this round. The component meaning is retained verbatim '
                                         'in the claim record; no MathClaim was produced for it.')})
            coverage = 'COMPLETE' if all(m['disposition'] == 'MAPPED' for m in mappings) else 'PARTIAL'
            self.map_refs[cid] = self.add('claim-component-map', f'map:{RUN}/{cid}', {
                'claim_ref': claim_ref, 'mappings': mappings,
                'review': {
                    'reviewed_refs': [claim_ref], 'producer_principal_ids': [PRINCIPAL],
                    'independence': 'UNESTABLISHED',
                    'conflicts': [
                        'The claim and this correspondence map were produced by the same principal in the same execution.',
                        'No second model, process or person inspected either record.',
                        'The AGENT.md working stages require an independent reviewer; none existed in this run.',
                    ],
                    'method': ('Component-by-component accounting against the exact source spans: every component is '
                               'MAPPED to a mathematical or semantic target, kept as RESIDUAL with its meaning stated, '
                               'marked UNRESOLVED where the printed source cannot be read consistently, or NON_CLAIM. '
                               'This is a producer self-accounting, not a review.'),
                    'evidence_refs': [],
                },
                'coverage': coverage,
            }, 'CLAIM_PRODUCER', inputs=[claim_ref] + ([math_ref] if math_ref else []) + ([sem_ref] if sem_ref else []))

            for i, f in enumerate(c['frontier'], start=1):
                targets = [claim_ref] + ([math_ref] if math_ref else [])
                self.frontier_refs.append(self.add('frontier-item', f'frontier:{RUN}/{cid}-{i:02d}', {
                    'target_refs': targets, 'kind': f['kind'], 'axes': f['axes'],
                    'statement': f['statement'], 'next_evidence': f['next_evidence'],
                    'attempt_refs': [], 'state': 'OPEN', 'resolution_refs': [],
                }, 'CLAIM_PRODUCER', inputs=targets))

    # ---- S2 discovery (proposed denominator, never frozen) --------------
    def discovery(self):
        obligations = []
        for e in self.acq['files']:
            path, uid = e['path'], unit_id(e['path'])
            if path == 'Pauli_Spectrum.tex':
                obligations.append({'obligation_id': f'obligation:{RUN}/source-main', 'target_refs': [self.snapshot_ref, self.structure_ref],
                                    'source_unit_ids': [uid], 'stage': 'SOURCE', 'requirement': 'SUCCESS_REQUIRED',
                                    'applicable_axes': ['source_fidelity'],
                                    'reason': 'The single top-level TeX file carries the whole text of the paper and its supplemental material.'})
            elif path in {'00README.json', 'draft_ref.bib', 'Pauli_SpectrumNotes.bib'}:
                obligations.append({'obligation_id': f'obligation:{RUN}/source-{uid.removeprefix("unit:")}', 'target_refs': [self.snapshot_ref],
                                    'source_unit_ids': [uid], 'stage': 'SOURCE', 'requirement': 'ACCOUNT_FOR',
                                    'applicable_axes': ['source_fidelity'],
                                    'reason': 'Text unit inventoried and opened, but no claim of the paper is carried by it; cited works were not retrieved.'})
            else:
                obligations.append({'obligation_id': f'obligation:{RUN}/source-{uid.removeprefix("unit:")}', 'target_refs': [],
                                    'source_unit_ids': [uid], 'stage': 'SOURCE', 'requirement': 'ACCOUNT_FOR',
                                    'applicable_axes': ['source_fidelity'],
                                    'reason': 'Figure bytes inventoried by hash only. The image was never opened, so every figure-based statement in the paper is unverified here.'})
        obligations.append({'obligation_id': f'obligation:{RUN}/inventory', 'target_refs': [self.structure_ref],
                            'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'INVENTORY',
                            'requirement': 'SUCCESS_REQUIRED', 'applicable_axes': ['source_fidelity'],
                            'reason': 'Sectioning, theorem environments and supplemental structure must be located before claims can be attributed to positions in the source.'})
        for c in self.seed['claims']:
            cid = c['id']
            obligations.append({'obligation_id': f'obligation:{RUN}/claim-{cid}', 'target_refs': [self.claim_refs[cid]],
                                'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'CLAIM',
                                'requirement': 'SUCCESS_REQUIRED', 'applicable_axes': ['source_fidelity'],
                                'reason': f'{c["section"]}: {c["label"]}'})
        for cid in sorted(self.sem_refs):
            obligations.append({'obligation_id': f'obligation:{RUN}/semantics-{cid}', 'target_refs': [self.sem_refs[cid]],
                                'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'SEMANTICS',
                                'requirement': 'ACCOUNT_FOR', 'applicable_axes': ['semantic_applicability'],
                                'reason': 'Physical reading of a numerical application: what the computed quantity is a property of, and under which representational choices.'})
        for cid in ('c29', 'c30'):
            obligations.append({'obligation_id': f'obligation:{RUN}/computation-{cid}', 'target_refs': [self.claim_refs[cid]],
                                'source_unit_ids': [unit_id('Pauli_Spectrum.tex')], 'stage': 'COMPUTATION',
                                'requirement': 'ACCOUNT_FOR', 'applicable_axes': ['computational_reproducibility'],
                                'reason': 'Numerical results are reported without data or code. Accounted for as unreproduced; nothing was executed in this run.'})
        classified = [unit_id(e['path']) for e in self.acq['files'] if e['path'] != '00README.json']
        self.discovery_ref = self.add('inventory-discovery', f'discovery:{RUN}', {
            'plan_ref': self.plan_ref, 'structure_ref': self.structure_ref,
            'classified_unit_ids': classified, 'unclassified_unit_ids': [unit_id('00README.json')],
            'obligations': obligations,
            'claim_refs': [self.claim_refs[c['id']] for c in self.seed['claims']],
            'coverage_rationale': (
                'Proposed denominator, NOT frozen. One SOURCE obligation per inventoried unit, one INVENTORY '
                'obligation for the document structure, one CLAIM obligation per extracted author claim, one '
                'SEMANTICS obligation per numerical application that needed a physical reading, and one COMPUTATION '
                'obligation per unreproduced numerical section. The claim count is a reading of this text, not a '
                'canonical atomisation: several obligations carry a theorem together with the surrounding prose that '
                'states its scope. Unknowns are kept inside the denominator as obligations with empty targets rather '
                'than dropped. This record cannot become a frozen-scope in this run because the accepting scope-decision '
                'that AGENT.md S2 requires must come from a principal other than the discoverer, and this execution had none.'),
        }, 'CLAIM_PRODUCER', inputs=[self.plan_ref, self.structure_ref] + [self.claim_refs[c['id']] for c in self.seed['claims']])

    # ---- output ---------------------------------------------------------
    def write(self):
        records_dir = self.out / 'records'
        records_dir.mkdir(parents=True, exist_ok=True)
        for stale in records_dir.glob('*.json'):
            stale.unlink()
        index = []
        for i, record in enumerate(self.records):
            short = record['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0')
            name = f'{i:04d}-{short}.json'
            raw = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=1).encode() + b'\n'
            (records_dir / name).write_bytes(raw)
            index.append({'path': f'records/{name}', 'sha256': digest(raw), 'ref': exact_ref(record)})
        (self.out / 'records.json').write_text(
            json.dumps(self.records, ensure_ascii=False, indent=1) + '\n')
        return index

    def validate(self):
        report = RecordSet(self.bundle, self.records, self.artifacts).validate(require_artifacts=True)
        return report


def render(builder, out, index):
    """Human-readable view of the same records. The JSON records are authoritative."""
    seed = builder.seed
    maps = {r['payload']['claim_ref']['record_id']: r for r in builder.records
            if r['record_type'].startswith('agtxiv.v3.claim-component-map')}
    lines = [
        '# Author claims extracted from arXiv:2608.14798v1',
        '',
        'Reading view of `records.json`. The JSON records are authoritative; this file is an attachment.',
        'Every quoted condition, component and residual is a reading of the source text, not a judgement',
        'about whether the paper is right. Nothing here was proved, checked or reproduced.',
        '',
        f'Claims: {len(seed["claims"])}. Definitions: {len(seed["definitions"])}. '
        f'MathClaims: {sum(1 for c in seed["claims"] if "math" in c)}. '
        f'SemanticContexts: {sum(1 for c in seed["claims"] if "semantic" in c)}. '
        f'Open frontier items: {sum(len(c["frontier"]) for c in seed["claims"])}.',
        '',
        '| # | Section | Claim | Modality | Components | Coverage | Open items |',
        '|---|---|---|---|---|---|---|',
    ]
    for c in seed['claims']:
        m = maps[f'claim:{RUN}/{c["id"]}']
        lines.append(f'| {c["id"]} | {c["section"]} | {c["label"]} | {c["modality"]} | '
                     f'{len(c["components"])} | {m["payload"]["coverage"]} | {len(c["frontier"])} |')
    lines += ['', '---', '']
    for c in seed['claims']:
        m = maps[f'claim:{RUN}/{c["id"]}']
        disposition = {x['component_id']: x['disposition'] for x in m['payload']['mappings']}
        lines += [f'## {c["id"]} — {c["label"]}', '',
                  f'*{c["section"]} · modality {c["modality"]} · coverage {m["payload"]["coverage"]}*', '',
                  '**What the authors said.** ' + c['statement'], '',
                  f'**System.** {c["system"]}', '',
                  f'**Comparison baseline.** {c["comparison_baseline"]}', '',
                  '**Stated conditions.**', '']
        for cond in c['conditions']:
            lines.append(f'- ({cond["origin"]}) {cond["statement"]}')
        lines += ['', '**Components and their accounting.**', '']
        for comp in c['components']:
            key = comp['component_id']
            lines.append(f'- `{key}` [{comp["role"]} / {disposition[key]}] {comp["text"]}')
            if c['residuals'].get(key):
                lines.append(f'  - residual: {c["residuals"][key]}')
        if 'math' in c:
            mm = c['math']
            lines += ['', f'**Math target `{mm["id"]}`** ({mm["exactness"]}), covering '
                      + ', '.join(f'`{x}`' for x in mm['component_ids']) + '.', '',
                      f'- conclusion: {mm["conclusion"]}']
            for q in mm['quantifiers']:
                lines.append(f'- quantifier: {q["kind"]} {q["variable"]} in {q["domain"]}')
            for a in mm['assumptions']:
                lines.append(f'- assumption ({a["origin"]}): {a["statement"]}')
            lines.append(f'- normalization: {mm["normalization"]}')
            if mm['approximation_error']:
                lines.append(f'- approximation error: {mm["approximation_error"]}')
        else:
            lines += ['', '**Math target.** None. This claim was not forced into a MathClaim; '
                      'its meaning is retained in the claim record and, where applicable, in a SemanticContext.']
        if 'semantic' in c:
            sc = c['semantic']
            lines += ['', f'**Semantic context `{sc["id"]}`.** {sc["physical_system"]}', '',
                      f'- approximation regime: {sc["approximation_regime"]}',
                      f'- error bound: {sc["error_bound"]}']
            for lim in sc['limitations']:
                lines.append(f'- limitation: {lim}')
        if c['frontier']:
            lines += ['', '**Open items recorded against this claim.**', '']
            for f in c['frontier']:
                lines.append(f'- [{f["kind"]} · {", ".join(f["axes"])}] {f["statement"]}')
                lines.append(f'  - what could settle it: {f["next_evidence"]}')
        lines += ['', f'Records: `claim:{RUN}/{c["id"]}`, `map:{RUN}/{c["id"]}`'
                  + (f', `math:{RUN}/{c["math"]["id"]}`' if 'math' in c else '')
                  + (f', `semantics:{RUN}/{c["semantic"]["id"]}`' if 'semantic' in c else '') + '.', '']
    (out / 'claims.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'output')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)

    builder = Builder(out)
    builder.context()
    builder.source()
    builder.plan()
    builder.spans()
    builder.definitions()
    builder.claims()
    builder.discovery()
    index = builder.write()
    render(builder, out, index)
    report = builder.validate()

    counts: dict[str, int] = {}
    for record in builder.records:
        short = record['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0')
        counts[short] = counts.get(short, 0) + 1
    issues = [{'code': i.code, 'record_id': i.record_id, 'path': i.path, 'message': i.message}
              for i in report.issues]
    summary = {
        'run': RUN, 'paper': self_paper(builder), 'built_at': RUN_AT,
        'schema_bundle_hash': builder.bundle.bundle_hash,
        'agent_spec_sha256': digest((HERE.parents[1] / 'AGENT.md').read_bytes()),
        'record_counts': counts, 'record_total': len(builder.records),
        'records': index,
        'record_set_valid': report.valid,
        'issue_codes': sorted({i['code'] for i in issues}),
        'issue_count': len(issues),
        'issues': issues,
        'byte_artifacts_checked': report.byte_artifacts_checked,
        'authority_checked': report.authority_checked,
        'scope_frozen': False,
        'formal_tasks_created': False,
        'numerics_reproduced': False,
        'scientific_acceptance_checked': False,
        'limitations': list(report.limitations),
    }
    (out / 'manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: summary[k] for k in (
        'record_total', 'record_counts', 'record_set_valid', 'issue_codes', 'issue_count',
        'scope_frozen', 'formal_tasks_created', 'numerics_reproduced')}, indent=2))
    return 0 if report.valid else 2


def self_paper(builder):
    return builder.seed['paper']['arxiv_id']


if __name__ == '__main__':
    raise SystemExit(main())
