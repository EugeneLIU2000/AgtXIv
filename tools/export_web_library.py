#!/usr/bin/env python3
"""Build the public reader projection from exact local evidence, never from UI state."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text())

def fingerprint(path):
    return 'sha256:' + hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def build():
    inv = read('docs/evidence/v3-real-candidate/candidate-inventory.json')
    records = read('docs/evidence/v3-real-candidate/records.json')
    closure = read('docs/evidence/v3-real-candidate/closure-verification.json')
    source = ROOT / 'Reference/Application of a resource theory for magic states to fault-tolerant quantum computing/Robustness_main_appendix.tex'
    raw = source.read_bytes()
    names = {
        'definition': ('Measure the signed-weight cost', 'Robustness is the least total absolute coefficient weight among all signed decompositions into pure stabilizer states.', 'ℛ(ρ) = min ∑ᵢ |xᵢ|,   ρ = ∑ᵢ xᵢ σᵢ'),
        'channel': ('Free operations mix stabilizer states', 'A stabilizer-preserving channel can send a pure stabilizer state to a probability mixture of stabilizer states. It need not map pure states to pure states.', 'ℰ(σᵢ) = ∑ⱼ pᵢⱼ σⱼ,   pᵢⱼ ≥ 0,   ∑ⱼ pᵢⱼ = 1'),
        'feasibility': ('Build a decomposition of the output', 'Regroup the transformed terms. This produces one feasible output decomposition and therefore an upper bound on its minimum cost.', 'x′ⱼ = ∑ᵢ xᵢ pᵢⱼ,   ℛ(ℰ(ρ)) ≤ ∑ⱼ |x′ⱼ|'),
        'contraction': ('Mixing cannot increase absolute weight', 'The triangle inequality and normalized mixture coefficients bound the new total absolute weight by the old one. Mixing can cancel positive and negative contributions.', '∑ⱼ |∑ᵢ xᵢ pᵢⱼ| ≤ ∑ᵢ |xᵢ| ∑ⱼ pᵢⱼ = ∑ᵢ |xᵢ|'),
        'R3': ('Compare with the best input decomposition', 'Choose a minimum-cost input decomposition to obtain monotonicity. This optimal-input requirement is a contextual reconstruction in the current candidate analysis.', 'ℛ(ℰ(ρ)) ≤ ℛ(ρ)'),
        'postselection': ('What changes when an outcome is selected?', 'A selected measurement outcome requires its probability and normalization to be tracked. The paper states a separate average-robustness extension and refers to another proof. The trace-preserving chain does not establish monotonicity for every selected branch.', None),
    }
    proposals=[]
    for p in inv['proposals']:
        entry=dict(p)
        title, intuition, formula=names.get(p['id'],(p['id'],p['interpretation'],None))
        entry.update(title=title,intuition=intuition,formula=formula,editorial_explanation=True)
        entry['anchors']=[]
        for a in p['anchors']:
            span=raw[a['start_byte']:a['end_byte']]
            if hashlib.sha256(span).hexdigest()!=a['sha256']:
                raise ValueError('Source anchor bytes changed: '+p['id'])
            entry['anchors'].append({**a,'line_start':raw[:a['start_byte']].count(b'\n')+1,
                'line_end':raw[:a['end_byte']].count(b'\n')+1})
        expected='ORACLE_PROPOSED / UNVERIFIED interpretation: '+p['interpretation']
        matching=[r for r in records if r['record_type']=='agtxiv.v3.argument-node/0.0.0' and r['payload']['statement'].split('\n',1)[0]==expected]
        if len(matching)!=1:
            raise ValueError('Expected one exact argument record for '+p['id'])
        record=matching[0]
        entry['record_ref']={k:record[k] for k in ('record_type','record_id','revision','content_hash')}
        entry['assessments']=[{'axis':axis,'status':'NOT_ASSESSED'} for axis in ('source_fidelity','mathematical_correctness','formal_alignment','semantic_applicability','empirical_support','computational_reproducibility')]
        proposals.append(entry)
    papers=[]
    for slug in read('schema v0.0/evaluation-corpus.json')['selection']['predecessor_slugs']+['graph-theoretic-nonstabilizerness']:
        path=f'agents/{slug}/agent.json'
        agent=read(path)
        paper={'slug':slug,'title':agent['agent']['title'],'arxiv':agent['agent']['paper_id'].removeprefix('arxiv:'),
            'source_url':'https://arxiv.org/abs/'+agent['agent']['paper_id'].removeprefix('arxiv:'),
            'legacy_status':agent['agent']['lifecycle_status'],'provenance':{'path':path,'sha256':fingerprint(path)},
            'view':'LEGACY_REFERENCE','imports':agent.get('imports',[]),'claims':[],
            'note':'Historical pilot reference. Its original status is retained; no V3 scientific assessment is inferred.'}
        if slug=='robustness-of-magic':
            paper.update(view='V3_CANDIDATE_READER',claims=proposals,records_url='/data/robustness-records.json',
                open_questions=inv['open_questions'],obligations=inv['proposed_obligations'],
                package_ref=inv['package_ref'],source_ref=closure['source_ref'],
                observed_at=closure['capture_observed_at'],note='Six source-linked interpretations of a selected argument. Whole-paper scientific review and formal scope freeze remain open.')
        papers.append(paper)
    docs=[]
    for row in read('schema v0.0/catalog.json')['records']:
        schema=read('schema v0.0/'+row['schema'])
        payload=schema['properties']['payload']
        fields=[]
        for name, value in payload.get('properties',{}).items():
            kind=value.get('type') or ('reference' if '$ref' in value or 'allOf' in value else 'variant')
            fields.append({'name':name,'type':kind,'required':name in payload.get('required',[]),'description':value.get('description',''),'definition':value})
        docs.append({**row,'description':schema.get('description',''),'fields':fields,
            'sha256':fingerprint('schema v0.0/'+row['schema']),'url':'/schemas/v3/'+row['schema']})
    return {'api_version':'1.0','kind':'AGTXIV_READER_LIBRARY','status':'RESEARCH_PREVIEW',
        'schema_bundle_hash':closure['schema_bundle_hash'],'papers':papers,'schemas':docs,
        'evidence':{'inventory':fingerprint('docs/evidence/v3-real-candidate/candidate-inventory.json'),
            'records':fingerprint('docs/evidence/v3-real-candidate/records.json')},
        'scientific_acceptance':False}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--check',action='store_true'); args=p.parse_args()
    output=ROOT/'web/public/data/library.json'
    body=json.dumps(build(),ensure_ascii=False,indent=2)+'\n'
    copies={ROOT/'web/public/data/robustness-records.json':ROOT/'docs/evidence/v3-real-candidate/records.json'}
    copies.update({ROOT/'web/public/schemas/v3'/source.name:source for source in (ROOT/'schema v0.0').glob('*.schema.json')})
    if args.check:
        if not output.exists() or output.read_text()!=body: raise SystemExit('Web projection differs from exact current inputs')
        for destination,source in copies.items():
            if not destination.exists() or destination.read_bytes()!=source.read_bytes():
                raise SystemExit(f'Published copy differs: {destination.relative_to(ROOT)}')
        print('Web library and all published copies match exact source anchors, records and schema fields')
    else:
        output.parent.mkdir(parents=True,exist_ok=True); output.write_text(body)
        (output.parent/'robustness-records.json').write_bytes((ROOT/'docs/evidence/v3-real-candidate/records.json').read_bytes())
        dest=ROOT/'web/public/schemas/v3';dest.mkdir(parents=True,exist_ok=True)
        for source in (ROOT/'schema v0.0').glob('*.schema.json'): (dest/source.name).write_bytes(source.read_bytes())
        print(output)

if __name__=='__main__': main()
