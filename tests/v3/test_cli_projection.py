"""Offline public entry points and preservation of conflicting assessments."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_contracts import FixtureGraph, bundle, mutate
from agtxiv_v3.contracts import RecordSet, canonical, exact_ref
from agtxiv_v3.projections import project_axes, render_axes_markdown

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args):
    process = subprocess.run([sys.executable,str(ROOT/'tools/validate_v3.py'),*map(str,args)],
                             capture_output=True,text=True,check=False)
    return process, json.loads(process.stdout) if process.stdout else None


def write_inputs(tmp_path, graph):
    records = tmp_path/'records.json'
    records.write_bytes(canonical(graph.records))
    locations=[]
    for i,artifact in enumerate(graph.artifacts):
        name=f'input-{i}.bin'
        (tmp_path/name).write_bytes(artifact.data)
        locations.append({'artifact_id':artifact.artifact_id,'media_type':artifact.media_type,'path':name})
    manifest=tmp_path/'artifacts.json'
    manifest.write_text(json.dumps(locations))
    return records,manifest


def test_cli_bundle_only_is_explicitly_not_scientific_acceptance():
    process,report=run_cli('--bundle-only')
    assert process.returncode==0,process.stderr
    assert report['scope']=='OFFLINE_SCHEMA_BUNDLE'
    assert report['record_types']==64
    assert not report['authority_checked'] and not report['scientific_acceptance']


def test_cli_checks_actual_bytes_and_returns_a_nonzero_failure(tmp_path,bundle):
    graph=FixtureGraph(bundle)
    records,manifest=write_inputs(tmp_path,graph)
    process,report=run_cli('--records',records,'--artifacts',manifest)
    assert process.returncode==0,report
    assert report['byte_artifacts_checked'] and not report['authority_checked']
    (tmp_path/'input-0.bin').write_bytes(b'corrupted bytes')
    process,report=run_cli('--records',records,'--artifacts',manifest)
    assert process.returncode==1
    assert any(issue['code']=='EXACT_REFERENCE' for issue in report['issues'])


def test_cli_cannot_silently_claim_bytes_were_checked(tmp_path,bundle):
    records,_=write_inputs(tmp_path,FixtureGraph(bundle))
    process,report=run_cli('--records',records)
    assert process.returncode==1
    process,report=run_cli('--records',records,'--without-artifact-bytes')
    assert process.returncode==0,report
    assert not report['byte_artifacts_checked']


@pytest.mark.parametrize('path',['../outside.txt','/tmp/outside.txt','linked/input.bin'])
def test_cli_rejects_escaping_or_linked_artifact_locators(tmp_path,bundle,path):
    records,manifest=write_inputs(tmp_path,FixtureGraph(bundle))
    (tmp_path/'linked').symlink_to(tmp_path.parent,target_is_directory=True)
    manifest.write_text(json.dumps([{'artifact_id':'artifact:paper','media_type':'text/plain','path':path}]))
    process,report=run_cli('--records',records,'--artifacts',manifest)
    assert process.returncode==1
    assert report['valid'] is False


def test_readonly_projection_keeps_conflicting_conclusions_and_conditions(bundle):
    graph=FixtureGraph(bundle)
    supported=graph.assessment()
    uncertain=graph.add('axis-assessment',{
        **supported['payload'],'result':'INCONCLUSIVE','support_refs':[],
        'conditions':[{'condition_id':'condition:pure','statement':'Only pure states were compared.',
                       'origin':'AGENT_ADDED','source_span_refs':[exact_ref(graph.span)]}],
        'rationale':'A distinct bounded assessment remains uncertain.',
    },actor='actor:auditor',role='SCIENTIFIC_REVIEWER')
    before=canonical(graph.records)
    records=RecordSet(bundle,graph.records,graph.artifacts)
    view=project_axes(records,exact_ref(graph.claim))
    assert len(view['axes'])==6
    source=view['axes'][0]
    assert source['apparent_disagreement']
    assert {x['record_ref']['record_id'] for x in source['assessments']}=={supported['record_id'],uncertain['record_id']}
    assert all(x['coverage']=='NO_SUPPLIED_ASSESSMENT' for x in view['axes'][1:])
    markdown=render_axes_markdown(view)
    assert 'Only pure states' in markdown and '未提供该维度的评估' in markdown
    assert '人工样例，不是真实科学评估' in markdown
    assert '身份与权限未核验' in markdown and '所提供字节与记录哈希、长度匹配' in markdown
    assert graph.span['record_id'] in markdown and '原文对应审阅' in markdown
    assert canonical(graph.records)==before
    assert project_axes(records,exact_ref(graph.claim))==view


def test_mutating_a_returned_record_or_view_cannot_change_inputs(bundle):
    graph=FixtureGraph(bundle)
    graph.assessment()
    records=RecordSet(bundle,graph.records,graph.artifacts)
    published=records.records
    published[0]['payload']['charter_state']='ADOPTED'
    assert records.validate().valid
    view=project_axes(records,exact_ref(graph.claim))
    pristine=copy.deepcopy(view)
    view['axes'][0]['assessments'][0]['result']='COUNTEREVIDENCE'
    assert project_axes(records,exact_ref(graph.claim))==pristine
