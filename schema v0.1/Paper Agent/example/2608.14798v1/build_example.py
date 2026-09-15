"""Assemble this session's source-grounded candidates, not an automatic extractor.

Replaying this script validates and packages saved agent-authored proposals. It
does not call a model, re-read the paper semantically, freeze scope, or prove it.
"""
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from agtxiv_v3.contracts import (SchemaBundle, RecordSet, SuppliedArtifact,
    exact_ref, content_hash, digest, AXES)
from agtxiv_v3.intake import inspect_source_directory, build_source_candidates

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Previously absent output directory')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite output; choose a new directory')
    out = args.output
    acquisition = json.loads((HERE / 'acquisition.json').read_text())
    source_root = ROOT / acquisition['source_directory']
    spec_bytes = (HERE.parents[1] / 'AGENT.md').read_bytes()
    main_path = source_root / 'Pauli_Spectrum.tex'
    raw = main_path.read_bytes()
    for item in acquisition['files']:
        data = (source_root / item['path']).read_bytes()
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
    text = raw.decode('utf-8')
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    run_key = hashlib.sha256(now.encode()).hexdigest()[:12]
    inspection = inspect_source_directory(source_root, 'Pauli_Spectrum.tex')
    bundle = SchemaBundle()
    records, artifacts = [], []
    principal = 'session:paper-example-2608.14798v1'
    producer = {'principal_id': principal, 'role': 'CLAIM_PRODUCER',
        'actor_kind': 'AGENT', 'identity_assurance': 'DECLARED',
        'execution_id': 'session:paper-extraction-2608.14798v1',
        'visible_input_refs': [], 'identity_evidence': []}
    policy_ref = None
    def make(name, slug, payload, inputs=(), observed=False, who=None):
        record = bundle.make_record(name, 'example:2608.14798v1-' + run_key + '-' + slug,
            payload, producer=who or producer, policy_ref=policy_ref,
            input_refs=inputs, created_at=now, data_class='OBSERVED' if observed else 'RESEARCH')
        records.append(record)
        return record
    policy = make('authority-policy', 'unadopted-policy', {
        'charter_identity': 'AgtXIv-Charter/1.0', 'charter_state': 'PROPOSED',
        'ratification_commit': None, 'minimum_identity_assurance': 'LOCALLY_ATTESTED',
        'separated_role_pairs': ['PRODUCER/REVIEWER'],
        'human_review_triggers': ['Local candidate context only; no policy adoption, signature, scientific approval or scope-freeze authority.'],
        'allowed_principal_ids': []}, who={**producer, 'role': 'MAINTAINER'})
    policy_ref = exact_ref(policy)
    source = build_source_candidates(inspection, bundle=bundle,
        producer={**producer, 'role': 'SOURCE_PRODUCER', 'actor_kind': 'MECHANICAL_SERVICE'},
        policy_ref=policy_ref, source_record_id='example:2608.14798v1-'+run_key+'-source',
        structure_record_id='example:2608.14798v1-'+run_key+'-structure',
        paper_id='arxiv:2608.14798', paper_version='2608.14798v1',
        created_at=now, rights_status='UNRESOLVED',
        rights_note='Downloaded from version-pinned arXiv source URL; retained locally, not published. See acquisition.json. Redistribution license not audited.')
    snapshot, structure = source.source_snapshot, source.paper_structure
    records.extend([snapshot, structure]); artifacts.extend(source.artifacts)
    sr = exact_ref(snapshot)
    units = {u['relative_path']: u for u in snapshot['payload']['units']}
    main_unit = units['Pauli_Spectrum.tex']
    profile = make('processing-profile', 'proposed-profile', {
        'name': 'V3_SOURCE_MAP', 'required_stages': ['SOURCE','INVENTORY','CLAIM'],
        'success_required_stages': ['SOURCE','INVENTORY','CLAIM'], 'required_axes': list(AXES),
        'allowed_terminal_outcomes': ['BLOCKED','DEFERRED'],
        'empirical_requirement': 'ACCOUNT_FOR', 'computation_requirement': 'ACCOUNT_FOR',
        'non_implications': ['Candidate-only extraction; no complete semantic inventory, frozen scope, mathematics check, formalization, experiment or admission.']})
    # Compatibility specimen, NOT the user's signed/finalized slim plan.
    plan = make('agentization-plan', 'legacy-compatible-proposed-plan', {
        'source_ref': sr, 'profile_ref': exact_ref(profile), 'baseline_ref': None,
        'source_unit_ids': [u['unit_id'] for u in units.values()],
        'max_steps': 200, 'max_seconds': 7200, 'max_cost_units': 0, 'no_progress_limit': 3,
        'trigger_note': 'User requested this real paper example. This unsigned, unadopted plan is a legacy-schema compatibility specimen. Extra required budget fields are NOT an agreed revision of AGENT.md; actual provider cost is unobserved and no scheduler budget was enforced.'},
        who={**producer, 'role': 'COORDINATOR'})
    plan_ref = exact_ref(plan)
    span_index = {}
    def span(start, end):
        if not (1 <= start <= end <= len(lines)):
            raise ValueError(f'Invalid anchor {start}:{end}')
        key = (start,end)
        if key not in span_index:
            lo, hi = offsets[start-1], offsets[end]
            span_index[key] = exact_ref(make('source-span', f'span-{start}-{end}', {
                'source_ref': sr, 'artifact': main_unit['artifact'],
                'locator_kind': 'RAW_TEXT_BYTES', 'byte_start': lo, 'byte_end': hi,
                'span_sha256': digest(raw[lo:hi]), 'pdf_region': None,
                'transformation_ref': None, 'locator': f'Pauli_Spectrum.tex:L{start}-L{end}',
                'activity': 'UNKNOWN'}, inputs=[sr], observed=True))
        return span_index[key]
    definitions = []
    for slug, name, start, end, statement, obj in [
        ('pauli-spectrum','Signed Pauli spectrum',305,353,
         'Spec(psi) is the multiset of tr(psi P) over phase-free n-qubit Pauli labels; psi denotes a rank-one projector. Signs and multiplicities are retained.', 'psi and phase-free Pauli labels'),
        ('nullity','Stabilizer nullity',410,413,
         'nu(psi)=n-log_2|Stab(psi)|, where the stabilizer-group size counts Pauli expectations of absolute value one.', 'pure n-qubit state psi'),
        ('renyi','Stabilizer Renyi entropy',440,451,
         'M_alpha(psi)=(1-alpha)^(-1) log_2[(1/d) sum_{x in Spec(psi)} x^{2 alpha}], as written by the source. Integer indices avoid signed fractional-power ambiguity; other domains require review.', 'M_alpha, alpha and pure state psi'),
        ('spf','Stabilizer partition function',533,543,
         'Z_beta(psi)=exp(-beta) sum_{x in Spec(psi)} cosh(beta x)=(1/2)tr exp(-beta H(psi)); beta is real.', 'Z_beta and beta'),
        ('core-spf','Core stabilizer partition function',561,567,
         'Z_beta^c(psi)=exp(-beta) sum_{x in Spec(psi)}[cosh(beta x)-1]=Z_beta(psi)-d^2 exp(-beta).', 'Z_beta^c, Z_beta and d'),
    ]:
        definitions.append(exact_ref(make('definition','def-'+slug, {
            'name': name, 'statement': statement,
            'objects': [{'symbol': obj, 'object_type':'Source-defined mathematical quantities',
                'definition_refs': [], 'unit':'', 'convention':'Preserve source conventions; no formal elaboration.'}],
            'source_span_refs':[span(start,end)], 'origin':'SOURCE'}, inputs=[sr])))
    seed_files = ['claims-foundations.json','claims-ensembles.json','claims-work-applications.json']
    seeds = []
    provenance = []
    for filename in seed_files:
        path = HERE / filename
        batch = json.loads(path.read_text())
        if not isinstance(batch,list):
            raise ValueError('Seed file must contain an array: '+filename)
        seeds.extend(batch)
        provenance.append({'path': filename, 'sha256':digest(path.read_bytes()), 'count':len(batch)})
    if len({s['id'] for s in seeds}) != len(seeds):
        raise ValueError('Duplicate claim id')
    claim_refs, math_refs, maps, handoffs = [], [], [], []
    binders = {
        'stabilizer-spectrum': [('n','positive integers'),('psi','normalized pure n-qubit stabilizer states')],
        'kernel-bounds': [('n','positive integers'),('psi','normalized pure n-qubit states')],
        'spf-limits': [('n','positive integers'),('psi','normalized pure n-qubit states; fixed in each beta limit')],
        'clifford-invariance': [('n','positive integers'),('psi','normalized pure n-qubit states'),('C','n-qubit Clifford unitaries'),('beta','real numbers')],
        'stabilizer-reference': [('n','positive integers'),('phi','normalized pure n-qubit stabilizer states'),('beta','real numbers')],
        'renyi-expansion': [('n','positive integers'),('psi','normalized pure n-qubit states'),('beta','real numbers')],
        'lipschitz': [('n','positive integers'),('psi','normalized pure n-qubit projectors'),('phi','normalized pure n-qubit projectors'),('beta','real numbers')],
        'state-independent-bounds': [('n','positive integers'),('psi','normalized pure n-qubit states'),('beta','real numbers')],
        'stabilizer-ancilla': [('n_A','nonnegative integers'),('n_B','nonnegative integers'),('psi_A','normalized pure states on n_A qubits'),('Stab_B','normalized pure stabilizer states on n_B qubits'),('beta','real numbers')],
    }
    authors = 'William E. Salazar, Gaurav Saxena, Jack S. Baker, Leong Chuan Kwek, Thi Ha Kyaw; arXiv:2608.14798v1. Author assertion, not independent endorsement.'
    for seed in seeds:
        refs = [span(a,b) for a,b in seed['anchors']]
        conditions = [{'condition_id': f"condition:{seed['id']}-{i}", 'statement':value,
            'origin':'SOURCE_RECONSTRUCTED','source_span_refs':refs} for i,value in enumerate(seed['assumptions'])]
        component_id = 'component:'+seed['id']
        sc = make('scientific-claim','claim-'+seed['id'], {
            'statement':seed['statement'], 'source_span_refs':refs,
            'components':[{'component_id':component_id,'text':seed['statement'],
                'role':'CONCLUSION','source_span_refs':refs}],
            'conditions':conditions, 'modality':'ASSERTED', 'attribution':authors,
            'system':'See claim-specific conditions and objects; pure-state default does not override explicit ensemble, mixed-state or channel scope.',
            'comparison_baseline':'See source-specific comparison in the statement and conditions; no independent prior-knowledge baseline was searched.'}, inputs=[sr, *refs])
        cr = exact_ref(sc); claim_refs.append(cr)
        semantic = make('semantic-context','semantics-'+seed['id'], {
            'claim_ref':cr, 'physical_system':'; '.join(seed['objects']),
            'object_mapping':[{'dimension':'OBJECT','source_value':seed['statement'],
                'target_value':seed['conclusion'],'relation':'UNKNOWN','witness_refs':refs}],
            'assumptions':conditions,
            'approximation_regime':seed['exactness']+'; '+seed['error_bound'],
            'error_bound':seed['error_bound'], 'observables':[],
            'limitations':seed['gaps']+['No independent source-to-math or physical interpretation review.']}, inputs=[cr,*refs])
        sem = exact_ref(semantic)
        mr = None
        if seed['math_extractable'] and seed['id'] in binders:
            mc = make('math-claim','math-'+seed['id'], {
                'claim_ref':cr,'component_ids':[component_id],
                'objects':[{'symbol':s.split(':',1)[0], 'object_type':s,
                    'definition_refs':[], 'unit':'',
                    'convention':'Source-scoped carrier; no formal type elaboration performed.'}
                    for i,s in enumerate(seed['objects'])],
                'quantifiers':[{'kind':'FORALL','variable':var,'domain':domain} for var,domain in binders[seed['id']]], 'assumptions':conditions,
                'conclusion':seed['conclusion'], 'exactness':seed['exactness'],
                'approximation_error':seed['error_bound'], 'definition_refs':definitions,
                'semantic_refs':[sem],
                'normalization':'d=2^n (or d_A=2^{n_A}, d_B=2^{n_B}); psi/phi denote rank-one projectors where used in traces or matrix norms. Logarithms are base two. Sum and limit indices are bound within the conclusion. No strengthening of source claim or formal type elaboration.'}, inputs=[cr,sem,*refs,*definitions])
            mr = exact_ref(mc); math_refs.append(mr)
        residual = '; '.join(seed['gaps'])
        residual += '; Complete component atomization and independent source alignment remain open; no scientific review.'
        if mr is None:
            residual += '; No MathClaim emitted: complete structured binders/conditions were not finalized in this pass. Formula remains in the source-linked semantic context and seed file.'
        mapping = make('claim-component-map','map-'+seed['id'], {
            'claim_ref':cr,
            'mappings':[{'component_id':component_id,'math_refs':[mr] if mr else [],
                'semantic_refs':[sem],'evidence_refs':refs,'disposition':'RESIDUAL','residual':residual}],
            'review':{'reviewed_refs':[cr], 'producer_principal_ids':[principal],
                'independence':'UNESTABLISHED', 'conflicts':['Producer-authored correspondence, not an independent review.'],
                'method':'Source-grounded partial mapping from this session; review pending.', 'evidence_refs':refs},
            'coverage':'PARTIAL'}, inputs=[cr,sem,*([mr] if mr else [])],
            who={**producer, 'visible_input_refs':[cr,sem,*([mr] if mr else []),*refs]})
        maps.append(exact_ref(mapping))
        make('frontier-item','gap-'+seed['id'], {
            'target_refs':[cr,*([mr] if mr else [])], 'kind':'ALIGNMENT_GAP',
            'axes':['source_fidelity','mathematical_correctness'],
            'statement':residual, 'next_evidence':'Review exact source spans, elaborate binders and assumptions, and resolve AGENT/schema conflicts before scope freeze.',
            'attempt_refs':[], 'state':'OPEN','resolution_refs':[]}, inputs=[cr])
        handoffs.append({'claim_id':seed['id'],'title':seed['title'],'claim_ref':cr,'math_ref':mr,
            'frozen_scope_ref':None,'formal_tasks_created':False,
            'proof':{'state':'BLOCKED','reason':'No independently frozen scope; remaining correspondence/component obligations.'},
            'dependency':{'state':'REQUEST_ONLY','citation_keys':seed['citations'],
                'reason':'Locate actual prerequisite statements; citation hints are not dependency bindings.'},
            'source_anchors':seed['anchors']})
    obligations = []
    for path, unit in units.items():
        obligations.append({'obligation_id':'obligation:'+unit['unit_id'].split(':',1)[1],
            'target_refs':[sr], 'source_unit_ids':[unit['unit_id']], 'stage':'INVENTORY',
            'requirement':'ACCOUNT_FOR','applicable_axes':['source_fidelity'],
            'reason':f'Retain {path}; byte capture is complete but exhaustive semantic/visual review is not claimed.'})
    for cr in claim_refs:
        obligations.append({'obligation_id':'obligation:'+cr['record_id'].split(':',1)[1],
            'target_refs':[cr],'source_unit_ids':[main_unit['unit_id']], 'stage':'CLAIM',
            'requirement':'ACCOUNT_FOR','applicable_axes':['source_fidelity'],
            'reason':'Candidate extraction requires independent scope and correspondence review.'})
    discovery = make('inventory-discovery','discovery', {
        'plan_ref':plan_ref, 'structure_ref':exact_ref(structure),
        'classified_unit_ids':[], 'unclassified_unit_ids':[u['unit_id'] for u in units.values()],
        'obligations':obligations, 'claim_refs':claim_refs,
        'coverage_rationale':'Candidate-only inventory: every captured source unit stays in the proposed denominator. Semantic extraction selects central claims; figures, tables, narrative and remaining theorem environments are not represented as exhaustively discovered. No FrozenScope.'},
        inputs=[plan_ref,exact_ref(structure),*claim_refs])
    report = RecordSet(bundle, records, artifacts).validate(require_artifacts=True)
    core_records = [r for r in records if r['record_type']!='agtxiv.v3.claim-component-map/0.0.0']
    core_report = RecordSet(bundle, core_records, artifacts).validate(require_artifacts=True)
    out.mkdir(parents=True)
    (out / 'records').mkdir()
    record_files = []
    for index, record in enumerate(records):
        short = record['record_type'].split('.')[2].split('/')[0]
        path = Path('records') / f'{index:04d}-{short}.json'
        dump(out/path,record)
        record_files.append({'path':str(path),'ref':exact_ref(record),'sha256':digest((out/path).read_bytes())})
    dump(out/'records.json', records)
    dump(out/'records-without-unreviewed-maps.json',core_records)
    dump(out/'validation.json', {'valid':report.valid,'scope':report.scope,
        'record_count':report.record_count,'byte_artifacts_checked':report.byte_artifacts_checked,
        'authority_checked':report.authority_checked,'issues':[asdict(i) for i in report.issues],
        'limitations':list(report.limitations),'strict_agent_protocol_completed':False,
        'single_record_json_schema_valid':all(not bundle.validate_record(r) for r in records),
        'without_unreviewed_maps':{'valid':core_report.valid,'record_count':core_report.record_count,
            'issues':[asdict(i) for i in core_report.issues],
            'excluded_record_refs':[exact_ref(r) for r in records if r['record_type']=='agtxiv.v3.claim-component-map/0.0.0'],
            'scope':'Explicit diagnostic subset, not a substitute for the required full output or a completed Paper handoff.'}})
    dump(out/'source-inspection.json',inspection.report())
    dump(out/'handoff-requests.json', handoffs)
    dump(out/'source-artifacts.json',[a.reference() for a in artifacts])
    # Retain non-source artifacts needed for exact reference verification.
    extra = out/'artifacts'; extra.mkdir()
    for artifact in artifacts:
        if artifact.artifact_id.startswith('artifact:inspection-'):
            (extra/'source-inspection.raw.json').write_bytes(artifact.data)
    lexical = []
    for match in re.finditer(r'\\begin\{(theorem|lemma|proposition|corollary|definition)\}', text):
        start = text.count('\n',0,match.start())+1
        lexical.append({'environment':match.group(1),'start_line':start,
            'status':'LEXICAL_OCCURRENCE_NOT_A_FROZEN_CLAIM',
            'overlapping_candidate_ids':[s['id'] for s in seeds if any(a<=start<=b for a,b in s['anchors'])]})
    dump(out/'lexical-inventory.json',lexical)
    readable = ['# 论文主张候选输出', '',
        '论文：Stabilizer Statistical Mechanics（arXiv:2608.14798v1）。', '',
        '本次为真实源码阅读后的候选提取；不是完整语义清点、科学审阅或形式化。',
        '每项保留原文范围、作者结论、适用条件和缺口。MathClaim 只对已整理结构化量词的目标生成；其余公式保留在语义记录中。', '']
    for seed, request in zip(seeds,handoffs):
        readable.extend(['## '+seed['title'], '', '**ID**：'+seed['id'], '',
            '**状态**：'+('已有候选 MathClaim；等待独立审阅。' if request['math_ref'] else '尚未生成 MathClaim；条件／量词或合并主张有残余。'), '',
            '**作者主张**：'+seed['statement'], '', '**数学表达或待规范化表达**：', '',
            seed['conclusion'].replace('\\\\','\\'), '', '**条件**：', ''])
        readable += ['- '+s for s in seed['assumptions']]
        readable += ['', '**原文**：'+', '.join(f'[L{a}–L{b}](<{main_path}:{a}>)' for a,b in seed['anchors']), '', '**未解项（非已证伪结论）**：', '']
        readable += ['- '+s for s in seed['gaps']]
        readable += ['', '**引用线索**：'+(', '.join(seed['citations']) or '本条未列外部引用线索；不表示没有历史依赖。'), '']
    (out/'claims.md').write_text('\n'.join(readable)+'\n')
    # Demonstrate the actual incompatibility without changing the user's file.
    slim = json.loads(json.dumps(plan))
    for key in ['created_at','data_class','schema_bundle_hash']:
        slim.pop(key)
    slim['producer']={k:slim['producer'][k] for k in ['principal_id','role']}
    for key in ['max_seconds','max_cost_units']:
        slim['payload'].pop(key)
    slim['content_hash']=content_hash(slim)
    slim_issues=bundle.validate_record(slim)
    dump(out/'plan-as-requested.INVALID.json',slim)
    dump(out/'plan-compatibility-check.json',{'valid':not slim_issues,
        'purpose':'Negative compatibility test; not an accepted plan or runtime input.',
        'issues':[asdict(i) for i in slim_issues]})
    counts=dict(Counter(r['record_type'].split('.')[2].split('/')[0] for r in records))
    dump(out/'manifest.json',{'paper':'arxiv:2608.14798v1','run_mode':'SESSION_AGENT_EXTRACTION_WITH_DETERMINISTIC_PACKAGING',
        'outcome':'BLOCKED_STRICT_PROTOCOL_WITH_RETAINED_PROVISIONAL_OUTPUTS',
        'full_record_set_valid':report.valid, 'diagnostic_subset_without_maps_valid':core_report.valid,
        'created_at':now,'spec_sha256':digest(spec_bytes),'schema_bundle_hash':bundle.bundle_hash,
        'packaging_script_sha256':digest(Path(__file__).read_bytes()),
        'producer_scope':'Session-level aggregate attribution, not an authenticated sole-agent identity. Records are assembled AFTER saved candidate reading; visible refs on maps describe this assembly, not earlier source reading.',
        'participants':[
            {'role':'primary extraction and assembly','identity':'current session','read_scope':'front matter/main text through line 730, plus explicitly inspected later excerpts'},
            {'role':'ensemble candidate extraction','identity':'01a09ba9-5186-7012-a9e4-225240f73dcf','read_scope':'731-1174 and selected prior definitions'},
            {'role':'work/applications/supplement candidate extraction','identity':'01a09ba9-51ee-7981-b8c3-f35052dc9ea0','read_scope':'1175-2723'},
            {'role':'interface audit and reader critique, not scientific review','identity':'01a09ba3-3dd7-7691-bd7d-5b1b37cbb7f9','read_scope':'AGENT.md, related contracts and candidate packaging boundary'}],
        'source_archive_sha256':acquisition['archive_sha256'],'seed_inputs':provenance,
        'record_type_counts':counts,'records':record_files,
        'source_unit_count':len(units),'proposed_obligation_count':len(obligations),
        'frozen_obligation_count':None,'exactly_one_disposition_per_proposed_obligation':[
            {'obligation_id':o['obligation_id'],'disposition':'OPEN_PENDING_INDEPENDENT_REVIEW'} for o in obligations],
        'not_performed':['Formal signed plan registration','Independent scope freeze','Proof expansion',
            'Historical recursive search','Formalization','Lean execution','Numerical reproduction','Publication','Knowledge admission'],
        'replay_boundary':'build_example.py packages saved model-authored seed files; it is not a live model pipeline or an independent extraction rerun.',
        'billing':'Provider token/cost usage was not measured; zero in the unsigned legacy plan is not a measured zero cost.'})
    print(json.dumps({'output':str(out),'valid':report.valid,'counts':counts,'issues':[asdict(i) for i in report.issues]},indent=2))
    if not report.valid:
        raise SystemExit(2)

if __name__=='__main__':
    main()
