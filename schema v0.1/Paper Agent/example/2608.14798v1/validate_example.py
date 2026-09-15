"""Read-back checks for this retained example; expected blockers remain failures."""
from pathlib import Path
import json
import sys
from dataclasses import asdict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from agtxiv_v3.contracts import SchemaBundle, RecordSet, SuppliedArtifact, digest, exact_ref

def main():
    out=HERE/'output'
    acquisition=json.loads((HERE/'acquisition.json').read_text())
    source=ROOT/acquisition['source_directory']
    records=json.loads((out/'records.json').read_text())
    manifest=json.loads((out/'manifest.json').read_text())
    bundle=SchemaBundle()
    assert manifest['spec_sha256']==digest((HERE.parents[1]/'AGENT.md').read_bytes()), 'AGENT.md changed after this run'
    assert manifest['schema_bundle_hash']==bundle.bundle_hash
    artifacts=[]
    snap=next(r for r in records if r['record_type']=='agtxiv.v3.source-snapshot/0.0.0')
    for unit in snap['payload']['units']:
        ref=unit['artifact']; data=(source/unit['relative_path']).read_bytes()
        assert digest(data)==ref['sha256'] and len(data)==ref['byte_size']
        artifacts.append(SuppliedArtifact(ref['artifact_id'],ref['media_type'],data))
    for ref in json.loads((out/'source-artifacts.json').read_text()):
        if ref['artifact_id'].startswith('artifact:inspection-'):
            data=(out/'artifacts/source-inspection.raw.json').read_bytes()
            assert digest(data)==ref['sha256']
            artifacts.append(SuppliedArtifact(ref['artifact_id'],ref['media_type'],data))
    for item, record in zip(manifest['records'],records):
        data=(out/item['path']).read_bytes()
        assert digest(data)==item['sha256']
        assert json.loads(data)==record and exact_ref(record)==item['ref']
    assert len(manifest['records'])==len(records)
    assert all(not bundle.validate_record(record) for record in records)
    full=RecordSet(bundle,records,artifacts).validate()
    assert not full.valid
    assert len(full.issues)==33 and {i.code for i in full.issues}=={'SELF_REVIEW'}, full.issues
    core=json.loads((out/'records-without-unreviewed-maps.json').read_text())
    assert core==[r for r in records if r['record_type']!='agtxiv.v3.claim-component-map/0.0.0']
    subset=RecordSet(bundle,core,artifacts).validate()
    assert subset.valid, subset.issues
    invalid=json.loads((out/'plan-as-requested.INVALID.json').read_text())
    assert bundle.validate_record(invalid), 'Slim plan unexpectedly accepted by pinned legacy schema'
    dispositions=manifest['exactly_one_disposition_per_proposed_obligation']
    assert len(dispositions)==len({x['obligation_id'] for x in dispositions})==49
    assert manifest['frozen_obligation_count'] is None
    assert not any(r['record_type'].split('/')[0].split('.')[-1] in {
        'frozen-scope','scope-decision','argument-node','inference-step','formalization-attempt','formal-check'} for r in records)
    result={'readback_checks_passed':True,'full_record_set_valid':full.valid,
        'expected_blocker':'33 producer-authored correspondence maps rejected as SELF_REVIEW',
        'single_record_shapes_valid':True,'record_count':len(records),
        'diagnostic_subset_valid':subset.valid,'diagnostic_subset_count':len(core),
        'raw_source_hashes_checked':len(snap['payload']['units']),
        'scope_frozen':False,'scientific_acceptance_checked':False,
        'interpretation':'Exit 0 means the expected success and failure boundaries reproduced, NOT that Paper S0-S5 passed.'}
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
