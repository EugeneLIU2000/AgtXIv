"""Adversarial contract tests, explicitly synthetic and not scientific approvals."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from agtxiv_v3.contracts import (
    AXES, AuthorityContext, ContractError, ExecutionAttestation, RecordSet, SchemaBundle,
    SuppliedArtifact, canonical, content_hash, digest, exact_ref, parse,
)


@pytest.fixture(scope='module')
def bundle():
    return SchemaBundle()


class FixtureGraph:
    """A fabricated contract graph; no real review, experiment or proof is asserted."""
    def __init__(self, bundle):
        self.bundle=bundle
        self.records=[]
        self.artifacts=[]
        self.count=0
        self.policy=None
        self.policy=self.add('authority-policy', {
            'charter_identity':'AgtXIv-Charter/1.0','charter_state':'PROPOSED','ratification_commit':None,
            'minimum_identity_assurance':'LOCALLY_ATTESTED','separated_role_pairs':['PRODUCER/REVIEWER'],
            'human_review_triggers':['Actual production admission follows repository governance.'],
            'allowed_principal_ids':['actor:producer','actor:reviewer','actor:auditor','actor:certifier','actor:knowledge'],
        }, role='MAINTAINER')
        self.profile=self.add('processing-profile', {
            'name':'V3_SOURCE_MAP','required_stages':['SOURCE','INVENTORY','CLAIM'],
            'success_required_stages':['SOURCE','INVENTORY','CLAIM'], 'required_axes':list(AXES),
            'allowed_terminal_outcomes':['BLOCKED','DEFERRED'],'empirical_requirement':'ACCOUNT_FOR',
            'computation_requirement':'ACCOUNT_FOR','non_implications':['No scientific truth claim.'],
        })
        raw=b'For pure states, the constructed quantity is nonnegative.\n'
        self.source_bytes=self.asset('paper',raw,'text/plain')
        self.source=self.add('source-snapshot', {
            'paper_id':'fixture:paper','paper_version':'v1','source_uri':'https://example.invalid/paper/v1',
            'acquired_at':'2026-09-07T00:00:00Z','acquisition_ref':None,'acquisition_method':'LOCAL_IMPORT',
            'units':[{'unit_id':'unit:main','relative_path':'main.tex','artifact':self.source_bytes,'activity':'ACTIVE','kind':'TEX'}],
            'archive':None,'missing_material':[],'rights_status':'KNOWN','rights_note':'Synthetic test input.',
        },role='SOURCE_PRODUCER')
        self.span=self.add('source-span', {
            'source_ref':exact_ref(self.source),'artifact':self.source_bytes,'locator_kind':'RAW_TEXT_BYTES',
            'byte_start':0,'byte_end':len(raw),'span_sha256':digest(raw),'pdf_region':None,'transformation_ref':None,
            'locator':'main.tex:1','activity':'ACTIVE',
        })
        self.claim=self.claim_record('For pure states, the constructed quantity is nonnegative.')
        self.plan=self.add('agentization-plan', {
            'source_ref':exact_ref(self.source),'profile_ref':exact_ref(self.profile),'baseline_ref':None,
            'source_unit_ids':['unit:main'],'max_steps':10,'max_seconds':60,'max_cost_units':100,
            'no_progress_limit':2,'trigger_note':'Synthetic test input independent of user query.',
        })
        self.structure=self.add('paper-structure', {
            'source_ref':exact_ref(self.source),'main_unit_id':'unit:main','edges':[],
            'unclassified_unit_ids':[],'blockers':[],
        })
        self.obligation={'obligation_id':'obligation:proof','target_refs':[exact_ref(self.claim)],
            'source_unit_ids':['unit:main'],'stage':'ARGUMENT','requirement':'ACCOUNT_FOR',
            'applicable_axes':['mathematical_correctness'],'reason':'A synthetic proof obligation.'}
        self.obligations=[self.obligation]+[{
            'obligation_id':'obligation:'+stage.lower(),'target_refs':[exact_ref(subject)],
            'source_unit_ids':['unit:main'],'stage':stage,'requirement':'SUCCESS_REQUIRED',
            'applicable_axes':['source_fidelity'],'reason':'Mandatory source-map work, synthetic contract only.'}
            for stage,subject in [('SOURCE',self.source),('INVENTORY',self.structure),('CLAIM',self.claim)]]
        self.discovery=self.add('inventory-discovery', {
            'plan_ref':exact_ref(self.plan),'structure_ref':exact_ref(self.structure),
            'classified_unit_ids':['unit:main'],'unclassified_unit_ids':[],
            'obligations':self.obligations,'claim_refs':[exact_ref(self.claim)],'coverage_rationale':'Fixture shape only.',
        })
        self.decision=self.add('scope-decision', {
            'discovery_ref':exact_ref(self.discovery),'review':self.review(self.discovery),
            'decision':'ACCEPT','reason':'Synthetic independent-role test only.',
        },actor='actor:reviewer',role='SCOPE_REVIEWER')
        self.scope=self.add('frozen-scope', {
            'plan_ref':exact_ref(self.plan),'discovery_ref':exact_ref(self.discovery),'decision_ref':exact_ref(self.decision),
            'obligations':self.obligations,'predecessor_ref':None,'change_reason':'Synthetic genesis scope.',
            'removed_obligation_dispositions':[],
        })

    def asset(self,name,data,media='text/plain'):
        item=SuppliedArtifact('artifact:'+name,media,data)
        self.artifacts.append(item)
        return item.reference()

    @staticmethod
    def refs(value):
        result=[]
        if isinstance(value,dict):
            if set(value)=={'record_id','record_type','revision','content_hash'}:
                result.append(value)
            else:
                for v in value.values(): result.extend(FixtureGraph.refs(v))
        elif isinstance(value,list):
            for v in value: result.extend(FixtureGraph.refs(v))
        unique={canonical(r):r for r in result}
        return list(unique.values())

    def add(self,name,payload,*,actor='actor:producer',role='CLAIM_PRODUCER'):
        self.count+=1
        refs=self.refs(payload)
        producer={'principal_id':actor,'role':role,'actor_kind':'AGENT','identity_assurance':'LOCALLY_ATTESTED',
            'execution_id':f'execution:{self.count}','visible_input_refs':refs,'identity_evidence':[]}
        record=self.bundle.make_record(name,f'fixture:{name}-{self.count}',payload,producer=producer,
            policy_ref=exact_ref(self.policy) if self.policy else None,input_refs=refs,
            created_at='2026-09-07T00:00:00Z',data_class='SYNTHETIC')
        self.records.append(record)
        return record

    def review(self,*records):
        return {'reviewed_refs':[exact_ref(r) for r in records],
            'producer_principal_ids':sorted({r['producer']['principal_id'] for r in records}),
            'independence':'ROLE_SEPARATED','conflicts':['Synthetic actor identities, not real review evidence.'],
            'method':'Synthetic bounded test review.','evidence_refs':[]}

    def claim_record(self,statement):
        return self.add('scientific-claim', {
            'statement':statement,'source_span_refs':[exact_ref(self.span)],
            'components':[{'component_id':'component:conclusion','text':statement,'role':'CONCLUSION','source_span_refs':[exact_ref(self.span)]}],
            'conditions':[],'modality':'CONDITIONAL','attribution':'Synthetic test author.',
            'system':'Synthetic mathematical domain.','comparison_baseline':'',
        })

    def argument(self,*,open_obligations=True):
        math=self.add('math-claim',{
            'claim_ref':exact_ref(self.claim),'component_ids':['component:conclusion'],
            'objects':[{'symbol':'x','object_type':'nonnegative real','definition_refs':[],'unit':'','convention':''}],
            'quantifiers':[{'kind':'FORALL','variable':'x','domain':'nonnegative reals'}],
            'assumptions':[],'conclusion':'x >= 0','exactness':'EXACT','approximation_error':'',
            'definition_refs':[],'semantic_refs':[],'normalization':'Synthetic target; not a claim of actual formalization.',
        })
        node=self.node('The synthetic quantity is nonnegative.')
        plan=self.add('proof-plan',{
            'scope_ref':exact_ref(self.scope),'conclusion_ref':exact_ref(node),'route':'RECONSTRUCTED',
            'node_refs':[exact_ref(node)],'inference_refs':[],'required_obligation_ids':['obligation:proof'],
            'open_obligation_ids':['obligation:proof'] if open_obligations else [],
        })
        snapshot=self.add('argument-snapshot',{
            'scope_ref':exact_ref(self.scope),'source_claim_refs':[exact_ref(self.claim)],'math_refs':[exact_ref(math)],
            'node_refs':[exact_ref(node)],'inference_refs':[],'context_refs':[],'proof_plan_refs':[exact_ref(plan)],
            'dependency_refs':[],'challenge_refs':[],'challenge_disposition_refs':[],
            'upstream_import_ref':None,'missing_items':[],
        })
        return math,node,plan,snapshot

    def node(self,statement,context=None):
        return self.add('argument-node',{'statement':statement,'kind':'CLAIM','origin':'RECONSTRUCTED',
            'claim_refs':[exact_ref(self.claim)],'context_ref':exact_ref(context) if context else None,
            'definition_refs':[],'source_span_refs':[exact_ref(self.span)]})

    def assessment(self,target=None,support=None,axis='source_fidelity',method='SOURCE_REVIEW'):
        target=target or self.claim
        return self.add('axis-assessment',{
            'target_refs':[exact_ref(target)],'axis':axis,'applicability':'APPLICABLE','result':'SUPPORTED',
            'execution':'COMPLETED','method':method,'review':self.review(target),
            'support_refs':[exact_ref(support or self.span)],'counterevidence_refs':[],'conditions':[],
            'frontier_refs':[],'rationale':'Synthetic shape/target-binding test, not an actual scientific result.',
        },actor='actor:reviewer',role='SCIENTIFIC_REVIEWER')

    def report(self,records=None,*,require_artifacts=True,authority=None):
        return RecordSet(self.bundle,self.records if records is None else records,self.artifacts,authority=authority).validate(require_artifacts=require_artifacts)

    def trusted(self,aliases=None):
        return AuthorityContext({r['producer']['execution_id']:ExecutionAttestation(
            r['producer']['principal_id'],r['producer']['role'],tuple(r['producer']['visible_input_refs'])) for r in self.records},
            principal_aliases=aliases or {},authorized_policy_hashes=frozenset({self.policy['content_hash']}))


def mutate(record, **payload_changes):
    changed=copy.deepcopy(record)
    changed['payload'].update(payload_changes)
    changed['content_hash']=content_hash(changed)
    return changed


def codes(report):
    return {issue.code for issue in report.issues}


def replace_reference(record, before, after):
    """Retarget every exact occurrence so a negative test reaches semantics."""
    def replace(value):
        if value == before:
            return copy.deepcopy(after)
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list):
            return [replace(v) for v in value]
        return value
    changed = replace(record)
    changed['content_hash'] = content_hash(changed)
    return changed


def test_positive_exact_source_scope_chain_with_actual_bytes(bundle):
    graph=FixtureGraph(bundle)
    report=graph.report()
    assert report.valid,report.issues
    assert report.byte_artifacts_checked and not report.authority_checked
    assert 'scientific' in ' '.join(report.limitations)


def test_raw_json_duplicate_normalized_key_float_and_unsafe_integer_rejected():
    for raw in [b'{"x":1,"x":2}',b'{"x":1.0}',b'{"x":9007199254740992}',
                '{"é":1,"é":2}'.encode()]:
        with pytest.raises(ContractError): parse(raw)
    assert canonical({'z':'é\r\na','a':1})==canonical({'a':1,'z':'é\na'})


def test_artifact_hash_does_not_normalize_text():
    assert digest(b'a\r\nb')!=digest(b'a\nb')


def test_unsealed_modified_record_is_rejected(bundle):
    graph=FixtureGraph(bundle)
    changed=copy.deepcopy(graph.claim)
    changed['payload']['statement']='For all states, the quantity is nonnegative.'
    assert 'RECORD_HASH_MISMATCH' in {i.code for i in bundle.validate_record(changed)}


def test_resealed_target_cannot_satisfy_stale_exact_reference(bundle):
    graph=FixtureGraph(bundle)
    changed=mutate(graph.claim,statement='A changed proposition.')
    records=[changed if r==graph.claim else r for r in graph.records]
    assert 'EXACT_REFERENCE' in codes(graph.report(records))


def test_duplicate_identity_and_wrong_typed_target_rejected(bundle):
    graph=FixtureGraph(bundle)
    assert 'DUPLICATE_IDENTITY' in codes(graph.report(graph.records+[graph.claim]))
    wrong=mutate(graph.scope,decision_ref=exact_ref(graph.discovery))
    assert 'SCHEMA' in {i.code for i in bundle.validate_record(wrong)}


def test_missing_or_corrupted_source_bytes_rejected(bundle):
    graph=FixtureGraph(bundle)
    graph.artifacts=[]
    assert 'EXACT_REFERENCE' in codes(graph.report())
    graph.artifacts=[SuppliedArtifact(graph.source_bytes['artifact_id'],'text/plain',b'forged')]
    assert 'EXACT_REFERENCE' in codes(graph.report())


def test_display_locator_does_not_change_artifact_identity(bundle):
    graph=FixtureGraph(bundle)
    changed=copy.deepcopy(graph.span)
    changed['payload']['artifact']['path_hint']='relocated.txt'
    changed['content_hash']=content_hash(changed)
    subset=[r for r in graph.records if r in [graph.policy,graph.source]]+[changed]
    assert graph.report(subset).valid


@pytest.mark.parametrize('start,end',[(0,0),(10,2),(0,10000)])
def test_byte_span_bounds_rejected(bundle,start,end):
    graph=FixtureGraph(bundle)
    changed=mutate(graph.span,byte_start=start,byte_end=end)
    subset=[graph.policy,graph.source,changed]
    assert not graph.report(subset).valid


def test_source_span_wrong_selected_bytes_digest_rejected(bundle):
    graph=FixtureGraph(bundle)
    changed=mutate(graph.span,span_sha256=digest(b'other'))
    assert 'SPAN_HASH' in codes(graph.report([graph.policy,graph.source,changed]))


def test_discovery_cannot_drop_unclassified_source_units(bundle):
    graph=FixtureGraph(bundle)
    changed=mutate(graph.discovery,classified_unit_ids=[],unclassified_unit_ids=[])
    assert 'BINDING_MISMATCH' in codes(graph.report(graph.records[:graph.records.index(graph.discovery)]+[changed]))


def test_scope_requires_accept_decision_and_identical_denominator(bundle):
    graph=FixtureGraph(bundle)
    blocked=mutate(graph.decision,decision='BLOCK')
    scope=replace_reference(graph.scope,exact_ref(graph.decision),exact_ref(blocked))
    report=graph.report([r for r in graph.records if r not in [graph.decision,graph.scope]]+[blocked,scope])
    assert 'UNACCEPTED_SCOPE' in codes(report)
    altered=mutate(graph.scope,obligations=[{**graph.obligation,'obligation_id':'obligation:invented'}])
    assert 'BINDING_MISMATCH' in codes(graph.report(graph.records[:-1]+[altered]))


def test_unknown_proof_obligation_not_accepted_from_same_name_elsewhere(bundle):
    graph=FixtureGraph(bundle)
    _,_,plan,_=graph.argument()
    changed=mutate(plan,required_obligation_ids=['obligation:other'],open_obligation_ids=[])
    records=graph.records[:graph.records.index(plan)]+[changed]
    assert 'PROOF_SCOPE' in codes(graph.report(records))


def test_local_premise_cannot_escape_assumption_scope(bundle):
    graph=FixtureGraph(bundle)
    context=graph.add('assumption-context',{'parent_ref':None,'assumptions':[{
        'condition_id':'condition:positive','statement':'x > 0','origin':'AGENT_ADDED','source_span_refs':[]}],
        'introduction_reason':'Synthetic local proof case.','allowed_use':'Inside the local case only.'})
    premise=graph.node('x > 0',context)
    conclusion=graph.node('x >= 0')
    graph.add('inference-step',{'premise_refs':[exact_ref(premise)],'conclusion_ref':exact_ref(conclusion),
        'rule':'DIRECT','justification':'A synthetic invalid scope escape.','context_ref':None,
        'discharged_context_refs':[],'rule_evidence_refs':[]})
    assert 'SCOPE_ESCAPE' in codes(graph.report())


def test_joint_premises_preserved_and_circular_proof_rejected(bundle):
    graph=FixtureGraph(bundle)
    a=graph.node('A')
    b=graph.node('B')
    c=graph.node('C follows from A and B jointly')
    step=graph.add('inference-step',{'premise_refs':[exact_ref(a),exact_ref(b)],'conclusion_ref':exact_ref(c),
        'rule':'DIRECT','justification':'Synthetic joint inference.','context_ref':None,
        'discharged_context_refs':[],'rule_evidence_refs':[]})
    plan=graph.add('proof-plan',{'scope_ref':exact_ref(graph.scope),'conclusion_ref':exact_ref(c),
        'route':'RECONSTRUCTED','node_refs':[exact_ref(a),exact_ref(b),exact_ref(c)],
        'inference_refs':[exact_ref(step)],'required_obligation_ids':['obligation:proof'],'open_obligation_ids':['obligation:proof']})
    assert graph.report().valid
    assert RecordSet(bundle,graph.records,graph.artifacts).resolve(exact_ref(step))['payload']['premise_refs']==[exact_ref(a),exact_ref(b)]
    reverse=graph.add('inference-step',{'premise_refs':[exact_ref(c)],'conclusion_ref':exact_ref(a),
        'rule':'DIRECT','justification':'Deliberately circular synthetic inference.','context_ref':None,
        'discharged_context_refs':[],'rule_evidence_refs':[]})
    changed=mutate(plan,inference_refs=[exact_ref(step),exact_ref(reverse)])
    assert 'CIRCULAR_PROOF' in codes(graph.report([r for r in graph.records if r!=plan]+[changed]))


def test_incomplete_snapshot_cannot_be_supported_argument(bundle):
    graph=FixtureGraph(bundle)
    _,_,plan,snapshot=graph.argument(open_obligations=True)
    graph.add('argument-review',{'snapshot_ref':exact_ref(snapshot),'proof_plan_refs':[exact_ref(plan)],
        'review':graph.review(snapshot),'outcome':'SUPPORTED','open_obligation_ids':[],
        'open_challenge_refs':[],'conditions':[]},actor='actor:reviewer',role='ARGUMENT_REVIEWER')
    assert 'OPEN_PROOF_OBLIGATIONS' in codes(graph.report())


def test_six_axis_source_evidence_is_separate_from_mathematics(bundle):
    graph=FixtureGraph(bundle)
    graph.assessment()
    assert graph.report().valid
    graph.assessment(axis='mathematical_correctness',method='ARGUMENT_REVIEW')
    assert 'EVIDENCE_METHOD_MISMATCH' in codes(graph.report())


def test_unassessed_method_cannot_produce_positive_result(bundle):
    graph=FixtureGraph(bundle)
    assessment=graph.assessment()
    changed=mutate(assessment,method='UNASSESSED')
    assert 'SCHEMA' in {i.code for i in bundle.validate_record(changed)}


def test_inapplicable_and_failed_execution_not_promoted_to_support(bundle):
    graph=FixtureGraph(bundle)
    assessment=graph.assessment()
    for changes in [{'applicability':'NOT_APPLICABLE'},{'execution':'FAILED'}]:
        assert bundle.validate_record(mutate(assessment,**changes))


def test_positive_source_assessment_cannot_borrow_unrelated_span(bundle):
    graph=FixtureGraph(bundle)
    other_raw=b'Unrelated scientific assertion.'
    other_artifact=graph.asset('other',other_raw)
    other_source=graph.add('source-snapshot',{
        **graph.source['payload'],'paper_id':'fixture:other','units':[{
            'unit_id':'unit:other','relative_path':'other.tex','artifact':other_artifact,'activity':'ACTIVE','kind':'TEX'}]})
    other_span=graph.add('source-span',{
        **graph.span['payload'],'source_ref':exact_ref(other_source),'artifact':other_artifact,
        'byte_end':len(other_raw),'span_sha256':digest(other_raw)})
    graph.assessment(support=other_span)
    assert 'EVIDENCE_TARGET_MISMATCH' in codes(graph.report())


def test_all_six_axes_required_even_without_assessments(bundle):
    graph=FixtureGraph(bundle)
    view=graph.add('status-view',{'target_ref':exact_ref(graph.claim),'assessment_refs':[],
        'conflicting_assessment_refs':[],'axes':list(AXES),'frontier_refs':[],
        'projection_method':'Retain each axis explicitly without inventing evidence.'})
    assert graph.report().valid
    assert bundle.validate_record(mutate(view,axes=list(AXES)[:3]))


def test_named_formal_profile_cannot_remove_formal_success_obligations(bundle):
    graph=FixtureGraph(bundle)
    bad=mutate(graph.profile,name='V3_FORMAL_SUPPORT')
    assert bundle.validate_record(bad)
    bad=mutate(graph.profile,required_axes=['source_fidelity'])
    assert bundle.validate_record(bad)


def test_declared_self_review_and_trusted_alias_self_review_rejected(bundle):
    graph=FixtureGraph(bundle)
    decision=copy.deepcopy(graph.decision)
    decision['producer']['principal_id']='actor:producer'
    decision['content_hash']=content_hash(decision)
    assert 'SELF_REVIEW' in codes(graph.report(graph.records[:graph.records.index(graph.decision)]+[decision]))
    report=graph.report(authority=graph.trusted({'actor:reviewer':'actor:producer'}))
    assert 'ALIASED_SELF_REVIEW' in codes(report)


def test_identity_evidence_must_come_from_caller_context(bundle):
    graph=FixtureGraph(bundle)
    report=graph.report(authority=graph.trusted())
    assert report.valid,report.issues
    assert report.authority_checked
    empty=AuthorityContext({},authorized_policy_hashes=frozenset({graph.policy['content_hash']}))
    assert 'UNATTESTED_EXECUTION' in codes(graph.report(authority=empty))
    unauthorized=AuthorityContext(graph.trusted().executions)
    assert 'UNAUTHORIZED_POLICY' in codes(graph.report(authority=unauthorized))


def test_rejected_scope_review_does_not_freeze_a_new_scope(bundle):
    graph=FixtureGraph(bundle)
    refused=mutate(graph.decision,decision='BLOCK')
    updated=replace_reference(graph.scope,exact_ref(graph.decision),exact_ref(refused))
    records=[r for r in graph.records if r not in [graph.decision,graph.scope]]+[refused,updated]
    assert 'UNACCEPTED_SCOPE' in codes(graph.report(records))


def test_truth_fields_forbidden_in_math_target(bundle):
    graph=FixtureGraph(bundle)
    math,_,_,_=graph.argument()
    for field in ['verified','truth','scientifically_accepted']:
        assert bundle.validate_record(mutate(math,**{field:True}))


def test_upstream_incomplete_can_honestly_record_missing_inputs(bundle):
    graph=FixtureGraph(bundle)
    upstream=graph.add('upstream-import',{'engine':'vibefeld','commit':'392b2da3bee5766cca1a201f28e0255056baaba4',
        'protocol_version':'graph-v1','adapter_version':'0.0.0','ledger':None,'graph':None,
        'context_artifacts':[],'identity_map':None,'reported_states':None,
        'import_checks':['REQUIRED_INPUT_PRESENCE'],'outcome':'INCOMPLETE','missing_items':['ledger','scope','identity']})
    assert graph.report().valid
    assert bundle.validate_record(mutate(upstream,outcome='STRUCTURALLY_IMPORTED',missing_items=[]))


def test_first_source_acquisition_failure_needs_no_fabricated_snapshot(bundle):
    graph=FixtureGraph(bundle)
    request=graph.add('source-request',{'paper_id':'arxiv:1234.56789','paper_version':'v1',
        'source_uri':'https://arxiv.org/src/1234.56789v1','allowed_hosts':['arxiv.org'],
        'max_bytes':100000,'timeout_seconds':30},role='SOURCE_PRODUCER')
    failed=graph.add('source-acquisition',{'request_ref':exact_ref(request),'outcome':'FAILED',
        'started_at':'2026-09-07T00:00:00Z','finished_at':'2026-09-07T00:00:10Z',
        'artifacts':[],'final_uri':None,'transport_evidence':[],'reason':'Synthetic network failure.'},role='SOURCE_PRODUCER')
    assert graph.report([graph.policy,request,failed]).valid


def test_pdf_region_does_not_invent_text_byte_offsets(bundle):
    graph=FixtureGraph(bundle)
    pdf=graph.asset('pdf',b'%PDF-1.7\nsynthetic structural bytes only','application/pdf')
    source=graph.add('source-snapshot',{**graph.source['payload'],'units':[{
        'unit_id':'unit:pdf','relative_path':'paper.pdf','artifact':pdf,'activity':'ACTIVE','kind':'PDF'}]})
    span=graph.add('source-span',{'source_ref':exact_ref(source),'artifact':pdf,'locator_kind':'PDF_REGION',
        'byte_start':None,'byte_end':None,'span_sha256':None,'pdf_region':{
            'page_index':0,'x0':'0.1','y0':'0.2','x1':'0.8','y1':'0.4'},'transformation_ref':None,
        'locator':'page 1 region','activity':'UNKNOWN'})
    assert graph.report().valid
    bad=mutate(span,pdf_region={'page_index':0,'x0':'NaN','y0':'0','x1':'1','y1':'1'})
    assert 'PDF_REGION_BOUNDS' in codes(graph.report(graph.records[:-1]+[bad]))


def test_records_are_detached_from_caller_mutations(bundle):
    graph=FixtureGraph(bundle)
    supplied=copy.deepcopy(graph.records)
    store=RecordSet(bundle,supplied,graph.artifacts)
    supplied[0]['payload']['charter_state']='ADOPTED'
    resolved=store.resolve(exact_ref(graph.claim))
    resolved['payload']['statement']='modified result'
    assert store.validate().valid
    assert store.resolve(exact_ref(graph.claim))['payload']['statement']==graph.claim['payload']['statement']
