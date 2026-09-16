"""Local synthetic storage tests; no external execution or scientific approval."""
from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import sys
from pathlib import Path
from threading import Barrier

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from agtxiv_v3.contracts import AuthorityContext, ContractError, SchemaBundle, SuppliedArtifact, content_hash, exact_ref
from agtxiv_v3.storage import LocalStore, StaleSnapshot, StorageError
from test_contracts import FixtureGraph, mutate


@pytest.fixture(scope='module')
def bundle():
    return SchemaBundle()


@pytest.fixture
def graph(bundle):
    return FixtureGraph(bundle)


def snapshot(graph, previous=None, domain='synthetic-local'):
    return graph.add('knowledge-snapshot', {
        'domain':domain, 'predecessor_ref':exact_ref(previous) if previous else None,
        'entry_refs':[], 'relation_refs':[], 'release_refs':[], 'admission_refs':[],
    }, actor='actor:knowledge', role='KNOWLEDGE_SERVICE')


def test_exact_persistence_reopen_detachment_and_retry(tmp_path, bundle, graph):
    path=tmp_path/'records.sqlite'
    original=copy.deepcopy(graph.claim)
    with LocalStore(path,bundle) as store:
        report=store.ingest(graph.records,graph.artifacts)
        assert report.valid and report.byte_artifacts_checked and not report.authority_checked
        assert store.ingest(graph.records,graph.artifacts).valid
        record=store.resolve(exact_ref(original))
        record['payload']['statement']='caller mutation'
        assert store.resolve(exact_ref(original))==original
        assert store.artifact({**graph.source_bytes,'path_hint':'../../not-opened'})==graph.artifacts[0].data
    with LocalStore(path,bundle,readonly=True) as store:
        assert store.resolve(exact_ref(original))==original
        with pytest.raises(StorageError,match='Read-only'):
            store.ingest([])


def test_revisions_remain_exact_without_latest_alias(tmp_path,bundle,graph):
    old=graph.claim
    new=mutate(old,statement='A new provisional source interpretation.')
    new['revision']=2
    new['content_hash']=content_hash(new)
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(graph.records,graph.artifacts)
        store.ingest([new])
        assert store.resolve(exact_ref(old))==old
        assert store.resolve(exact_ref(new))==new
        wrong={**exact_ref(new),'content_hash':old['content_hash']}
        with pytest.raises(StorageError): store.resolve(wrong)
        with pytest.raises(StorageError): store.resolve({'record_id':old['record_id']})
        with pytest.raises(StorageError): store.resolve({**exact_ref(old),'revision':True})


def test_overwrites_and_duplicate_candidates_rejected(tmp_path,bundle,graph):
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(graph.records,graph.artifacts)
        with pytest.raises(StorageError,match='overwrite'):
            store.ingest([mutate(graph.claim,statement='Changed under the same revision.')])
        with pytest.raises(StorageError,match='Duplicate'):
            store.ingest([graph.claim,graph.claim])
        with pytest.raises(ContractError,match='Duplicate supplied artifact'):
            store.ingest([],graph.artifacts*2)
        for item in [SuppliedArtifact(graph.artifacts[0].artifact_id,'text/plain',b'changed'),
                     SuppliedArtifact(graph.artifacts[0].artifact_id,'application/pdf',graph.artifacts[0].data)]:
            with pytest.raises(StorageError,match='overwrite'): store.ingest([], [item])
        assert store.resolve(exact_ref(graph.claim))==graph.claim


def test_unsealed_record_and_wrong_artifact_hash(tmp_path,bundle,graph):
    with LocalStore(tmp_path/'db',bundle) as store:
        bad=copy.deepcopy(graph.claim)
        bad['payload']['statement']='unsealed change'
        with pytest.raises(StorageError): store.ingest([bad])
        with pytest.raises(ContractError):
            store.ingest(graph.records,[SuppliedArtifact(graph.artifacts[0].artifact_id,'text/plain',b'wrong')])
        with pytest.raises(StorageError): store.resolve(exact_ref(graph.policy))
        with pytest.raises(StorageError): store.artifact(graph.source_bytes)
        store.ingest(graph.records,graph.artifacts)
        for changes in [{'sha256':'sha256:'+'0'*64},{'byte_size':1},{'media_type':'application/pdf'},
                        {'artifact_id':'artifact:unknown'},{'byte_size':True}]:
            with pytest.raises(StorageError): store.artifact({**graph.source_bytes,**changes})


def test_unknown_dependencies_rollback_records_and_artifacts(tmp_path,bundle,graph):
    extra=SuppliedArtifact('artifact:extra','text/plain',b'not committed')
    with LocalStore(tmp_path/'db',bundle) as store:
        with pytest.raises(ContractError,match='EXACT_REFERENCE'):
            store.ingest([graph.policy,graph.claim],[extra])
        with pytest.raises(StorageError): store.resolve(exact_ref(graph.policy))
        with pytest.raises(StorageError): store.artifact(extra.reference())
        assert store.ingest([graph.policy]).valid


def test_late_sql_failure_rolls_back_whole_bundle(tmp_path,bundle,graph):
    with LocalStore(tmp_path/'db',bundle) as store:
        store._db.execute("CREATE TRIGGER fail_bytes BEFORE INSERT ON artifacts BEGIN SELECT RAISE(ABORT, 'injected disk failure'); END")
        with pytest.raises(sqlite3.IntegrityError,match='injected'):
            store.ingest(graph.records,graph.artifacts)
        with pytest.raises(StorageError): store.resolve(exact_ref(graph.policy))
        store._db.execute('DROP TRIGGER fail_bytes')
        assert store.ingest(graph.records,graph.artifacts).valid


def test_sql_immutable_guards(tmp_path,bundle,graph):
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(graph.records,graph.artifacts)
        for sql in ['DELETE FROM records','UPDATE records SET revision=10',
                    'DELETE FROM artifacts',"UPDATE artifacts SET data=X'00'"]:
            with pytest.raises(sqlite3.IntegrityError,match='immutable'):
                store._db.execute(sql)
        assert store.resolve(exact_ref(graph.claim))==graph.claim


def test_cas_historical_queries_and_readonly_head(tmp_path,bundle,graph):
    first=snapshot(graph)
    second=snapshot(graph,first)
    path=tmp_path/'db'
    with LocalStore(path,bundle) as store:
        assert store.candidate_head('synthetic-local') is None
        store.ingest(graph.records,graph.artifacts,snapshot_ref=exact_ref(first))
        store.ingest([],snapshot_ref=exact_ref(second),expected_head=exact_ref(first))
        assert store.candidate_head('synthetic-local')==exact_ref(second)
        before=store._db.total_changes
        for record in [first,second]:
            result=store.query(exact_ref(record))
            assert result['knowledge_ref']==exact_ref(record)
            assert result['mode']=='PROVISIONAL' and not result['authority_checked']
            assert result['canonical_mutation']=='FORBIDDEN'
            assert result['records']==[] and result['relations']==[]
        assert store._db.total_changes==before
        with pytest.raises(StorageError,match='not in'): store.query(exact_ref(first),[exact_ref(graph.claim)])
        with pytest.raises(StorageError): store.query(exact_ref(graph.claim))
        unknown={**exact_ref(first),'record_id':'unknown:snapshot'}
        with pytest.raises(ContractError): store.query(unknown)
    with LocalStore(path,bundle,readonly=True) as store:
        assert store.query(exact_ref(first))['records']==[]
        assert store.candidate_head('synthetic-local')==exact_ref(second)


def test_stale_cas_rolls_back_all_new_objects(tmp_path,bundle,graph):
    first=snapshot(graph)
    initial=list(graph.records)
    winner=snapshot(graph,first)
    loser=snapshot(graph,first)
    extra=SuppliedArtifact('artifact:loser','text/plain',b'loser')
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(initial,graph.artifacts,snapshot_ref=exact_ref(first))
        store.ingest([winner],snapshot_ref=exact_ref(winner),expected_head=exact_ref(first))
        with pytest.raises(StaleSnapshot):
            store.ingest([loser],[extra],snapshot_ref=exact_ref(loser),expected_head=exact_ref(first))
        with pytest.raises(StorageError): store.resolve(exact_ref(loser))
        with pytest.raises(StorageError): store.artifact(extra.reference())
        assert store.candidate_head('synthetic-local')==exact_ref(winner)


def test_concurrent_connections_have_one_cas_winner(tmp_path,bundle,graph):
    first=snapshot(graph)
    initial=list(graph.records)
    contenders=[snapshot(graph,first),snapshot(graph,first)]
    path=tmp_path/'db'
    with LocalStore(path,bundle) as store:
        store.ingest(initial,graph.artifacts,snapshot_ref=exact_ref(first))
    barrier=Barrier(2)
    def attempt(record):
        with LocalStore(path,bundle) as store:
            barrier.wait(timeout=10)
            try:
                store.ingest([record],snapshot_ref=exact_ref(record),expected_head=exact_ref(first))
                return 'committed',record
            except StaleSnapshot:
                return 'stale',record
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(attempt,contenders))
    assert sorted(status for status,_ in results)==['committed','stale']
    with LocalStore(path,bundle) as store:
        for status,record in results:
            if status=='committed': assert store.candidate_head('synthetic-local')==exact_ref(record)
            else:
                with pytest.raises(StorageError): store.resolve(exact_ref(record))


def test_no_admission_from_candidate_storage_or_nonempty_genesis(tmp_path,bundle,graph):
    genesis=snapshot(graph)
    forged=mutate(genesis,entry_refs=[exact_ref(graph.claim)])
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(graph.records,graph.artifacts)
        assert store.candidate_head('synthetic-local') is None
        forged['record_id']='forged:genesis'
        forged['content_hash']=content_hash(forged)
        with pytest.raises(ContractError,match='NONEMPTY_GENESIS'):
            store.ingest([forged],snapshot_ref=exact_ref(forged))
        assert store.candidate_head('synthetic-local') is None
        with pytest.raises(StorageError): store.resolve(exact_ref(forged))


def test_caller_authority_is_checked_not_inferred_or_cached(tmp_path,bundle,graph):
    with LocalStore(tmp_path/'db',bundle) as store:
        with pytest.raises(ContractError,match='UNATTESTED_EXECUTION'):
            store.ingest(graph.records,graph.artifacts,authority=AuthorityContext({}))
        with pytest.raises(StorageError): store.resolve(exact_ref(graph.policy))
        report=store.ingest(graph.records,graph.artifacts,authority=graph.trusted())
        assert report.authority_checked
        assert not store.ingest([]).authority_checked
        assert store.resolve(exact_ref(graph.policy))['payload']['charter_state']=='PROPOSED'


def test_invalid_cas_target_and_wrong_predecessor(tmp_path,bundle,graph):
    first=snapshot(graph)
    unrelated=snapshot(graph)
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(graph.records,graph.artifacts,snapshot_ref=exact_ref(first))
        with pytest.raises(StorageError,match='extend'):
            store.ingest([],snapshot_ref=exact_ref(unrelated),expected_head=exact_ref(first))
        with pytest.raises(StorageError,match='must be a knowledge'):
            store.ingest([],snapshot_ref=exact_ref(graph.claim))
        with pytest.raises(StorageError,match='requires'):
            store.ingest([],expected_head=exact_ref(first))
        assert store.candidate_head('synthetic-local')==exact_ref(first)


def test_historical_admitted_records_still_query_as_provisional(tmp_path,bundle,graph):
    from test_contract_regressions import released_control, admit, admitted_snapshot
    control=released_control(graph)
    initial=list(graph.records)
    decision=admit(graph,control['release'],control['genesis'],graph.claim,control['assessment'])
    after=admitted_snapshot(graph,control['release'],control['genesis'],decision,graph.claim)
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(initial,graph.artifacts,snapshot_ref=exact_ref(control['genesis']))
        store.ingest([decision,after],snapshot_ref=exact_ref(after),expected_head=exact_ref(control['genesis']))
        result=store.query(exact_ref(after),[exact_ref(graph.claim)])
        assert result['records']==[graph.claim]
        assert result['mode']=='PROVISIONAL' and not result['authority_checked']
        assert store.query(exact_ref(control['genesis']))['records']==[]
        assert store.query(exact_ref(after),[])['records']==[]
        with pytest.raises(StorageError):
            store.query(exact_ref(after),[exact_ref(control['other_claim'])])
        assert store.resolve(exact_ref(control['assessment']))==control['assessment']


def test_raw_provenance_labels_are_never_rewritten(tmp_path,bundle):
    raw=b'{"origin":"ORACLE_PROPOSED","verification":"UNVERIFIED"}\r\n'
    item=SuppliedArtifact('artifact:provisional','application/json',raw)
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest([], [item])
        assert store.artifact(item.reference())==raw
        with pytest.raises(StorageError):
            store.artifact(SuppliedArtifact(item.artifact_id,item.media_type,raw.replace(b'\r\n',b'\n')).reference())


def test_schema_binding_and_read_integrity_fail_closed(tmp_path,bundle,graph):
    path=tmp_path/'db'
    with LocalStore(path,bundle) as store:
        store.ingest(graph.records,graph.artifacts)
        # Direct administrator tampering is outside the trust boundary, but reads
        # still verify canonical record hashes and raw artifact hashes.
        store._db.execute('DROP TRIGGER records_no_update')
        store._db.execute("UPDATE records SET body=? WHERE record_id=?", (b'{}',graph.claim['record_id']))
        with pytest.raises(StorageError,match='integrity'): store.resolve(exact_ref(graph.claim))
        store._db.execute('DROP TRIGGER artifacts_no_update')
        store._db.execute("UPDATE artifacts SET data=X'00'")
        with pytest.raises(StorageError,match='hash mismatch'): store.artifact(graph.source_bytes)
        store._db.execute("UPDATE metadata SET bundle_hash='wrong'")
    with pytest.raises(StorageError,match='schema bundle'):
        LocalStore(path,bundle,readonly=True)


@pytest.mark.parametrize('relation_kind',['CONFLICTING','INCOMPARABLE','CORRECTS','QUALIFIES','REFUTES'])
@pytest.mark.parametrize('relation_only',[False,True])
def test_query_retains_transitive_conflicts_and_opposing_endpoints(tmp_path,bundle,graph,relation_kind,relation_only):
    from test_contract_regressions import released_control, admit
    endpoints=[graph.claim,graph.claim_record('Opposing candidate B.'),graph.claim_record('Opposing candidate C.')]
    relations=[]
    assessments=[]
    for left,right in zip(endpoints,endpoints[1:]):
        relation=graph.add('relation-assessment', {
            'source_ref':exact_ref(left),'target_ref':exact_ref(right),'relation':relation_kind,
            'review':graph.review(left,right),'comparisons':[{
                'dimension':'OBJECT','source_value':'A','target_value':'B','relation':'UNKNOWN','witness_refs':[]}],
            'outcome':'PROPOSED','witness_refs':[],
        },actor='actor:reviewer',role='SCIENTIFIC_REVIEWER')
        relations.append(relation)
        assessment=graph.assessment(target=relation)
        assessment=mutate(assessment,result='INCONCLUSIVE')
        assessment['producer']['principal_id']='actor:producer'
        assessment['content_hash']=content_hash(assessment)
        graph.records[-1]=assessment
        assessments.append(assessment)
    control=released_control(graph)
    decisions=[admit(graph,control['release'],control['genesis'],r,a) for r,a in zip(relations,assessments)]
    decision=admit(graph,control['release'],control['genesis'],graph.claim,control['assessment'])
    decisions.append(decision)
    after=graph.add('knowledge-snapshot',{
        'domain':'Synthetic','predecessor_ref':exact_ref(control['genesis']),
        'entry_refs':[exact_ref(graph.claim)]+[exact_ref(r) for r in relations],
        'relation_refs':[exact_ref(r) for r in relations],
        'release_refs':[exact_ref(control['release'])],'admission_refs':[exact_ref(d) for d in decisions],
    },actor='actor:knowledge',role='KNOWLEDGE_SERVICE')
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(graph.records,graph.artifacts)
        selected=relations[0] if relation_only else graph.claim
        result=store.query(exact_ref(after),[exact_ref(selected)])
        expected=endpoints+[selected] if relation_only else endpoints
        assert {r['record_id'] for r in result['records']}=={r['record_id'] for r in expected}
        assert {r['record_id'] for r in result['relations']}=={r['record_id'] for r in relations}
        assert result['mode']=='PROVISIONAL'
        assert all(r['payload']['outcome']=='PROPOSED' for r in result['relations'])


@pytest.mark.parametrize('revision',[True,1.0])
@pytest.mark.parametrize('operation',['resolve','query_snapshot','query_selection','cas_expected','cas_snapshot'])
def test_all_public_record_references_reject_numeric_coercion(tmp_path,bundle,graph,revision,operation):
    from test_contract_regressions import released_control, admit, admitted_snapshot
    control=released_control(graph)
    decision=admit(graph,control['release'],control['genesis'],graph.claim,control['assessment'])
    after=admitted_snapshot(graph,control['release'],control['genesis'],decision,graph.claim)
    initial=list(graph.records)
    successor=graph.add('knowledge-snapshot',{
        **after['payload'],'predecessor_ref':exact_ref(after),
    },actor='actor:knowledge',role='KNOWLEDGE_SERVICE')
    extra=SuppliedArtifact('artifact:invalid-reference','text/plain',b'not retained')
    def malformed(record):
        return {**exact_ref(record),'revision':revision}
    with LocalStore(tmp_path/'db',bundle) as store:
        store.ingest(initial,graph.artifacts,snapshot_ref=exact_ref(control['genesis']))
        store.ingest([],snapshot_ref=exact_ref(after),expected_head=exact_ref(control['genesis']))
        with pytest.raises(ContractError):
            if operation=='resolve': store.resolve(malformed(after))
            elif operation=='query_snapshot': store.query(malformed(after))
            elif operation=='query_selection': store.query(exact_ref(after),[malformed(graph.claim)])
            elif operation=='cas_expected':
                store.ingest([successor],[extra],snapshot_ref=exact_ref(successor),expected_head=malformed(after))
            else:
                store.ingest([successor],[extra],snapshot_ref=malformed(successor),expected_head=exact_ref(after))
        assert store.candidate_head('Synthetic')==exact_ref(after)
        assert not store._db.in_transaction
        with pytest.raises(StorageError): store.resolve(exact_ref(successor))
        with pytest.raises(StorageError): store.artifact(extra.reference())


def test_concurrent_genesis_cas_rolls_back_loser_objects_and_bytes(tmp_path,bundle,graph):
    initial=list(graph.records)
    contenders=[(snapshot(graph),SuppliedArtifact('artifact:genesis-a','text/plain',b'a')),
                (snapshot(graph),SuppliedArtifact('artifact:genesis-b','text/plain',b'b'))]
    path=tmp_path/'db'
    with LocalStore(path,bundle) as store:
        store.ingest(initial,graph.artifacts)
        assert store.candidate_head('synthetic-local') is None
    barrier=Barrier(2)
    def attempt(candidate):
        record,artifact=candidate
        with LocalStore(path,bundle) as store:
            barrier.wait(timeout=10)
            try:
                store.ingest([record],[artifact],snapshot_ref=exact_ref(record),expected_head=None)
                return 'committed',record,artifact
            except StaleSnapshot:
                assert not store._db.in_transaction
                return 'stale',record,artifact
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(attempt,contenders))
    assert sorted(status for status,_,_ in results)==['committed','stale']
    with LocalStore(path,bundle) as store:
        for status,record,artifact in results:
            if status=='committed':
                assert store.candidate_head('synthetic-local')==exact_ref(record)
                assert store.resolve(exact_ref(record))==record
                assert store.artifact(artifact.reference())==artifact.data
            else:
                with pytest.raises(StorageError): store.resolve(exact_ref(record))
                with pytest.raises(StorageError): store.artifact(artifact.reference())
        assert store.resolve(exact_ref(graph.claim))==graph.claim
