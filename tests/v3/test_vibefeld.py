"""Synthetic byte/protocol probes; no af, Go, Lean or scientific demo runs.

The expected exports below are hand-written from the pinned Go contract.
They are not produced by the importer under test or by executing upstream.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from agtxiv_v3.vibefeld import (
    CaptureLimits, EVENT_TYPES, FEATURES, PINNED_COMMIT, Protocol,
    ImportError as CaptureError, _graph_projection, _replay,
    build_import_candidate, inspect_capture, node_content_hash,
)
from agtxiv_v3.contracts import RecordSet, exact_ref
from test_contracts import FixtureGraph, bundle

TIME='2026-09-07T00:00:00.123456789Z'


def raw(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()


def event(event_type,**kw):
    return {'type':event_type,'timestamp':TIME,**kw}


def node(identifier='1',**kw):
    value={'id':identifier,'type':'claim','statement':'Synthetic P(x)',
           'inference':'assumption','workflow_state':'available','epistemic_state':'pending',
           'taint_state':'unresolved','created':TIME,'author':'prover',**kw}
    # Independently spell the upstream preimage, not node_content_hash().
    preimage='type:'+value['type']+'|statement:'+value['statement']
    if value.get('latex'):preimage+='|latex:'+value['latex']
    preimage+='|inference:'+value['inference']
    for key in ('context','dependencies','validation_deps'):
        if value.get(key):preimage+='|'+key+':'+','.join(sorted(value[key]))
    value['content_hash']=hashlib.sha256(preimage.encode()).hexdigest()
    return value


def capture(value=None,*,extra=(),validated=False):
    value=node() if value is None else copy.deepcopy(value)
    events=[event('proof_initialized',conjecture='Synthetic P(x)',author='prover'),
            event('node_created',node=value),*extra]
    exported={k:copy.deepcopy(value[k]) for k in (
        'id','type','statement','inference','content_hash','workflow_state',
        'epistemic_state','taint_state','created','author') if k in value}
    for key in ('latex','crux','dependencies','validated_by','validation_batch_id','proof_author'):
        if value.get(key):exported[key]=copy.deepcopy(value[key])
    exported['verifier_ready']=True
    if validated:
        events.append(event('node_validated',node_id='1',verified_by='reviewer',batch_id='synthetic-batch'))
        exported.update(epistemic_state='validated',taint_state='clean',validated_by='reviewer',validation_batch_id='synthetic-batch',closed=True)
        exported.pop('verifier_ready')
    graph={'schema_version':'1','features':list(FEATURES),
           'workspace':{'id':'/synthetic/capture','title':'Synthetic','conjecture':'Synthetic P(x)'},
           'nodes':[exported],
           'validation':{'total_nodes':1,'epistemic_counts':{exported['epistemic_state']:1},
                         'taint_counts':{exported['taint_state']:1},'total_challenges':0,'challenge_status_counts':{}}}
    meta={'title':'Synthetic','conjecture':'Synthetic P(x)','lock_timeout':1000000000,
          'max_depth':20,'max_children':10,'warn_depth':10,'auto_correct_threshold':0.8,'created':TIME,'version':'1.0'}
    files={'graph.json':raw(graph),'meta.json':raw(meta),
           'identity-map.json':raw({'prover':'actor:producer','reviewer':'actor:reviewer'})}
    files.update({f'ledger/{i:06d}.json':raw(e) for i,e in enumerate(events,1)})
    return files


@pytest.fixture(scope='module')
def protocol():
    return Protocol()


def inspect(files,protocol,**kw):
    return inspect_capture(files,commit=kw.pop('commit',PINNED_COMMIT),workspace_key='fixture:synthetic',protocol=protocol,**kw)


def edit(files,path,change):
    value=json.loads(files[path]);change(value);files[path]=raw(value)


@pytest.mark.parametrize('validated',[False,True])
def test_complete_capture_keeps_reported_acceptance_separate_from_scientific_support(protocol,validated):
    files=capture(validated=validated)
    observation=inspect(files,protocol);report=observation.report()
    assert report['outcome']=='STRUCTURALLY_IMPORTED',report['issues']
    assert report['scientific_assessment']=='NOT_PERFORMED'
    assert report['identity_assurance']=='DECLARED_MAP_ONLY'
    assert report['dependency_scan']=='DIRECT_REPORTED_STATE_ONLY'
    assert dict(observation.files)==files
    report['outcome']='CERTIFIED'
    assert observation.report()['outcome']=='STRUCTURALLY_IMPORTED'
    files.clear()
    assert len(observation.files)>=5


def test_only_upstream_import_candidate_is_built_and_original_bytes_resolve(protocol,bundle):
    fixture=FixtureGraph(bundle)
    inspection=inspect(capture(validated=True),protocol)
    record,artifacts=build_import_candidate(inspection,bundle=bundle,record_id='fixture:import',
        producer=fixture.claim['producer'],policy_ref=exact_ref(fixture.policy),created_at=TIME,data_class='SYNTHETIC')
    assert record['record_type']=='agtxiv.v3.upstream-import/0.0.0'
    assert not bundle.validate_record(record)
    store=RecordSet(bundle,fixture.records+[record],fixture.artifacts+list(artifacts))
    result=store.validate()
    assert not result.issues
    assert not result.authority_checked
    assert all(any(a.data==data for a in artifacts) for data in inspection.files.values())


@pytest.mark.parametrize('missing',['graph.json','meta.json','identity-map.json','ledger/000001.json'])
def test_missing_inputs_never_become_complete(protocol,missing):
    files=capture();files.pop(missing)
    result=inspect(files,protocol).report()
    assert result['outcome']!='STRUCTURALLY_IMPORTED'
    assert result['issues'] or result['missing_items']


@pytest.mark.parametrize('attack',[
    'commit','graph-version','unknown-feature','duplicate-feature','unknown-graph-field',
    'unknown-event','unknown-event-field','ledger-gap','duplicate-sequence','bad-node-hash',
    'duplicate-node','bad-graph-state','unknown-config','custom-schema','nonfinite-config',
    'unknown-severity','unknown-category',
])
def test_protocol_and_replay_reject_incompatible_capture(protocol,attack):
    files=capture();kw={}
    if attack=='commit':kw['commit']='a'*40
    elif attack=='graph-version':edit(files,'graph.json',lambda g:g.update(schema_version='2'))
    elif attack=='unknown-feature':edit(files,'graph.json',lambda g:g['features'].append('future'))
    elif attack=='duplicate-feature':edit(files,'graph.json',lambda g:g['features'].append(FEATURES[0]))
    elif attack=='unknown-graph-field':edit(files,'graph.json',lambda g:g.update(extra_semantics=True))
    elif attack=='unknown-event':files['ledger/000003.json']=raw(event('future_proof'))
    elif attack=='unknown-event-field':edit(files,'ledger/000002.json',lambda e:e.update(extra_semantics=True))
    elif attack=='ledger-gap':files['ledger/000004.json']=files.pop('ledger/000002.json')
    elif attack=='duplicate-sequence':files['ledger/0000002.json']=files['ledger/000002.json']
    elif attack=='bad-node-hash':edit(files,'ledger/000002.json',lambda e:e['node'].update(content_hash='a'*64))
    elif attack=='duplicate-node':files['ledger/000003.json']=files['ledger/000002.json']
    elif attack=='bad-graph-state':edit(files,'graph.json',lambda g:g['nodes'][0].update(epistemic_state='validated'))
    elif attack=='unknown-config':edit(files,'meta.json',lambda g:g.update(future_semantics=True))
    elif attack=='custom-schema':edit(files,'meta.json',lambda g:g.update(schema_path='new.json'))
    elif attack=='nonfinite-config':files['meta.json']=files['meta.json'].replace(b'0.8',b'1e999')
    else:
        files['ledger/000003.json']=raw(event('challenge_raised',node_id='1',challenge_id='c',target='statement',
            reason='Synthetic objection',raised_by='reviewer',severity='wrong' if attack=='unknown-severity' else 'major',
            category='wrong' if attack=='unknown-category' else 'gap'))
    report=inspect(files,protocol,**kw).report()
    assert report['outcome']=='REJECTED',report


def test_raw_unicode_newlines_and_scope_have_separate_identity(protocol):
    value=node(statement='e\u0301\r\nP(x)')
    assert node_content_hash(value)==value['content_hash']
    assert node_content_hash(node(statement='é\nP(x)'))!=value['content_hash']
    first=inspect(capture(value),protocol).report()
    second=inspect(capture({**value,'scope':['missing-local-assumption']}),protocol).report()
    assert first['outcome']=='STRUCTURALLY_IMPORTED'
    assert second['outcome']=='INCOMPLETE'
    assert first['semantic_snapshot_hash']!=second['semantic_snapshot_hash']
    assert value['content_hash']==node_content_hash({**value,'scope':['different']})


def test_relocation_changes_raw_graph_identity_but_not_semantic_capture(protocol):
    files=capture();first=inspect(files,protocol).report()
    edit(files,'graph.json',lambda g:g['workspace'].update(id='/elsewhere/capture'))
    second=inspect(files,protocol).report()
    assert first['semantic_snapshot_hash']==second['semantic_snapshot_hash']
    assert first['file_manifest']!=second['file_manifest']


def test_upstream_timestamp_offsets_preserve_all_nine_digits(protocol):
    files=capture(node(created='2026-09-07T02:00:00.123456789+02:00'))
    edit(files,'graph.json',lambda g:g['nodes'][0].update(created=TIME))
    assert inspect(files,protocol).report()['outcome']=='STRUCTURALLY_IMPORTED'
    edit(files,'graph.json',lambda g:g['nodes'][0].update(created='2026-09-07T00:00:00.123456Z'))
    assert inspect(files,protocol).report()['outcome']=='REJECTED'


def test_context_hash_and_hidden_validation_dependencies_are_inspected(protocol):
    value=node(context=['h'],validation_deps=['1.2'])
    files=capture(value,validated=True)
    files['assumptions/h.json']=raw({'id':'h','statement':'Synthetic H','content_hash':hashlib.sha256(b'Synthetic H').hexdigest(),'created':TIME})
    report=inspect(files,protocol).report()
    assert report['outcome']=='INCOMPLETE'
    assert 'node 1 dependency 1.2' in report['missing_items']
    assert report['replayed_state']['nodes']['1']['context']==['h']
    edit(files,'assumptions/h.json',lambda a:a.update(statement='Changed H'))
    assert inspect(files,protocol).report()['outcome']=='REJECTED'


def test_evidence_attachment_is_retained_and_never_executed(protocol):
    script=b'raise RuntimeError("This synthetic attachment must never execute")\n'
    files=capture(extra=[event('evidence_attached',node_id='1',file_path='evidence/check.py',content_hash=hashlib.sha256(script).hexdigest(),attached_by='prover')])
    assert inspect(files,protocol).report()['outcome']=='INCOMPLETE'
    files['evidence/check.py']=script
    assert inspect(files,protocol).report()['outcome']=='STRUCTURALLY_IMPORTED'
    files['evidence/check.py']+=b'# changed'
    assert inspect(files,protocol).report()['outcome']=='REJECTED'


def test_amendment_checks_exact_previous_statement_and_rehashes(protocol):
    previous=node();amend=event('node_amended',node_id='1',previous_statement=previous['statement'],new_statement='Synthetic Q(x)',owner='prover')
    files=capture(previous,extra=[amend])
    edit(files,'graph.json',lambda g:g['nodes'][0].update(statement='Synthetic Q(x)',content_hash=node(statement='Synthetic Q(x)')['content_hash']))
    assert inspect(files,protocol).report()['outcome']=='STRUCTURALLY_IMPORTED'
    edit(files,'ledger/000003.json',lambda e:e.update(previous_statement='Wrong previous text'))
    assert inspect(files,protocol).report()['outcome']=='REJECTED'


def test_same_declared_identity_is_not_independent_review(protocol):
    files=capture(validated=True)
    files['identity-map.json']=raw({'prover':'actor:same','reviewer':'actor:same'})
    report=inspect(files,protocol).report()
    assert report['outcome']=='STRUCTURALLY_IMPORTED'
    assert report['identity_assurance']=='DECLARED_MAP_ONLY'
    assert report['scientific_assessment']=='NOT_PERFORMED'
    files['identity-map.json']=raw({'prover':'actor:same'})
    assert inspect(files,protocol).report()['outcome']=='INCOMPLETE'


@pytest.mark.parametrize('path',['../outside','/absolute','a//b','a/./b','a\\b','bad\x00name'])
def test_unsafe_capture_member_paths_rejected_before_interpretation(protocol,path):
    with pytest.raises(CaptureError):inspect({path:b''},protocol)


@pytest.mark.parametrize('raw_value',[b'{"type":"x","type":"node_created"}',b'{"x":NaN}',b'{"x":1.2}',b'{"x":9223372036854775808}',b'{"x":"\\ud800"}'])
def test_ambiguous_or_unsupported_json_does_not_replay(protocol,raw_value):
    files=capture();files['ledger/000002.json']=raw_value
    assert inspect(files,protocol).report()['outcome']=='REJECTED'


def test_capture_resource_limits_precede_full_loading(protocol):
    with pytest.raises(CaptureError):inspect(capture(),protocol,limits=CaptureLimits(max_files=1))
    with pytest.raises(CaptureError):inspect(capture(),protocol,limits=CaptureLimits(max_file_bytes=10))
    with pytest.raises(CaptureError):inspect(capture(),protocol,limits=CaptureLimits(max_total_bytes=10))
    with pytest.raises(CaptureError):inspect(capture(),protocol,limits=CaptureLimits(max_events=1))


def test_every_pinned_event_has_a_replay_branch_and_original_history(protocol):
    events=[event('proof_initialized',conjecture='Synthetic P(x)',author='prover')]
    for value in [node(),node('1.1',type='local_assume',statement='Synthetic H'),
                  node('1.2',type='local_discharge'),node('1.3',epistemic_state='draft')]:
        events.append(event('node_created',node=value))
    events += [
        event('nodes_claimed',node_ids=['1'],owner='prover',timeout=TIME),
        event('claim_refreshed',node_id='1',owner='prover',new_timeout=TIME),
        event('nodes_released',node_ids=['1']),
        event('node_validated',node_id='1',verified_by='reviewer',batch_id='first'),
        event('refinement_requested',node_id='1',reason='Synthetic recheck',requested_by='reviewer'),
        event('node_validated',node_id='1',verified_by='reviewer'),
        event('node_unvalidated',node_id='1',reason='Synthetic revoke'),
        event('node_admitted',node_id='1.1'),event('node_unadmitted',node_id='1.1'),
        event('node_submitted',node_id='1.3',owner='prover'),
        event('node_amended',node_id='1.3',previous_statement='Synthetic P(x)',new_statement='Synthetic Q',owner='prover'),
        event('taint_recomputed',node_id='1',new_taint='clean'),
        event('def_added',definition={'id':'d','name':'D','definition':'Synthetic definition','created':TIME}),
        event('lemma_extracted',lemma={'id':'l','statement':'Synthetic lemma','node_id':'1','created':TIME}),
        event('lock_reaped',node_id='1',owner='prover'),
        event('scope_opened',node_id='1.1',statement='Synthetic H'),
        event('scope_closed',node_id='1.1',discharge_node_id='1.2'),
        event('approach_tried',node_id='1',approach='Synthetic route',outcome='failed',tried_by='prover'),
        event('evidence_attached',node_id='1',file_path='proof.txt',content_hash='0'*64),
        event('outline_set',stages=[{'label':'A','description':'Synthetic stage','criticality':'critical'}]),
        event('outline_stage_linked',label='A',node_id='1.1'),
        event('outline_set',stages=[{'label':'B','description':'Replacement','criticality':'routine'}]),
        event('hint_added',node_id='1',text='Synthetic hint'),
        event('strategy_proposed',node_id='1',strategy='Synthetic strategy',novelty='distinct'),
        event('pattern_added',name='Synthetic pattern',description='Record only'),
        event('claim_tested',node_id='1',engine='script',passed=False,output='Synthetic failure'),
        event('def_checked',def_name='D',check_type='boundary',passed=False,output='Synthetic failure'),
        event('node_proof_authored',node_id='1',author='prover'),
    ]
    for number,(disposition,target) in enumerate([('resolved','1'),('withdrawn','1'),('superseded','1'),('auto','1.1')],1):
        events.append(event('challenge_raised',challenge_id=f'c{number}',node_id=target,target='statement',reason='Synthetic challenge',severity='major',raised_by='reviewer'))
        if disposition!='auto':
            extra={'node_id':target} if disposition=='superseded' else {}
            events.append(event('challenge_'+disposition,challenge_id=f'c{number}',**extra))
    events += [event('node_archived',node_id='1.1'),event('node_refuted',node_id='1.2'),
               event('node_vetoed',node_id='1.3',reason='Synthetic veto',vetoed_by='reviewer')]
    for e in events:protocol.check('event.schema.json',e)
    assert {e['type'] for e in events}==EVENT_TYPES
    state=_replay(events,CaptureLimits())
    assert state['history']==events
    assert state['nodes']['1']['validated_by']==''
    assert state['nodes']['1']['proof_author']=='prover'
    assert state['nodes']['1.3']['statement']=='Synthetic Q'
    assert state['challenges']['c4']['status']=='superseded'
    assert state['outline_links']=={'A':'1.1'}
    assert state['scopes']['1.1']['discharged']==TIME
    assert state['scopes']['1.1']['discharge_node_id']=='1.2'
    projection=_graph_projection(state,{'id':'synthetic'})
    assert projection['nodes'][0]['taint_state']=='unresolved' # overrides taint_recomputed clean
    assert projection['validation']['total_challenges']==4


def test_direct_dependency_status_cannot_be_read_from_tree_clean_flag(protocol):
    # A refuted sibling is cut from taint propagation; a validated sibling
    # references it through validation_deps, which the export omits.
    values=[node(epistemic_state='validated',proof_author='prover',validated_by='reviewer'),
            node('1.1',epistemic_state='refuted'),
            node('1.2',epistemic_state='validated',validated_by='reviewer',validation_deps=['1.1'])]
    events=[event('proof_initialized',conjecture='Synthetic P',author='prover')]+[event('node_created',node=n) for n in values]
    state=_replay(events,CaptureLimits())
    projected=_graph_projection(state,{'id':'synthetic'})
    assert [n['taint_state'] for n in projected['nodes']]==['clean','clean','clean']
    assert state['nodes']['1.2']['validation_deps']==['1.1']
    assert not projected['nodes'][0].get('closed',False) # refutation is not closure
    assert [n['id'] for n in projected['nodes']]==['1','1.1','1.2']
