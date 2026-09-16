"""Read-only import of the pinned vibefeld graph/ledger protocol.

This code interprets supplied bytes. It never invokes af, Go, Lean, a shell,
an attached script, or a network request. Upstream workflow labels remain
reported labels; successful structural import grants no scientific authority.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from types import MappingProxyType
from typing import Mapping

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from .contracts import ContractError, ROOT, SchemaBundle, SuppliedArtifact, digest

PINNED_COMMIT = '392b2da3bee5766cca1a201f28e0255056baaba4'
ADAPTER_VERSION = 'agtxiv.vibefeld-capture/0.0.0'
FEATURES = ('readiness-flags','closure-flag','node-dependencies','proof-author')
EVENT_TYPES = frozenset('''proof_initialized node_created nodes_claimed nodes_released
challenge_raised challenge_resolved challenge_withdrawn challenge_superseded
node_validated node_admitted node_refuted node_archived node_amended taint_recomputed
def_added lemma_extracted lock_reaped scope_opened scope_closed claim_refreshed
refinement_requested node_submitted node_unvalidated node_unadmitted approach_tried
evidence_attached outline_set outline_stage_linked hint_added node_vetoed strategy_proposed
pattern_added claim_tested def_checked node_proof_authored'''.split())
TRANSITIONS = {
    'pending':{'validated','admitted','refuted','archived'},
    'validated':{'needs_refinement','pending'},'admitted':{'pending'},
    'needs_refinement':{'validated','admitted','refuted','archived'},
    'draft':{'pending','archived'},'archived':set(),'refuted':set(),
}
CLEARED = {'validated','admitted','archived'}
UNRESOLVED = {'pending','draft','needs_refinement'}
SEVERED = {'archived','refuted'}


class ImportError(ContractError):
    """Invalid or unsupported supplied capture, not a scientific refutation."""


@dataclass(frozen=True)
class CaptureLimits:
    max_files: int = 10000
    max_events: int = 8000
    max_file_bytes: int = 16*1024*1024
    max_total_bytes: int = 128*1024*1024
    max_nodes: int = 4000
    max_json_depth: int = 96

    def __post_init__(self):
        if any(type(v) is not int or v<1 for v in vars(self).values()):
            raise ImportError('Capture resource limits must be positive integers')


def _encode(value) -> bytes:
    """Deterministic lossless JSON encoding; do NOT apply V3 NFC/LF to upstream."""
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def _json(raw: bytes, limits: CaptureLimits, *, allow_floats: bool=False):
    if type(raw) is not bytes or len(raw)>limits.max_file_bytes:
        raise ImportError('JSON input must be original bytes within the file limit')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:
                raise ImportError('Duplicate upstream JSON key: '+key)
            result[key]=value
        return result
    def reject_number(value):
        raise ImportError('Unsupported floating or nonfinite upstream JSON number: '+value)
    try:
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_float=float if allow_floats else reject_number,parse_constant=reject_number)
        pending=[(value,0)]
        while pending:
            item,depth=pending.pop()
            if depth>limits.max_json_depth:
                raise ImportError('Upstream JSON exceeds the nesting limit')
            if isinstance(item,dict):
                pending.extend((x,depth+1) for x in item.values())
            elif isinstance(item,list):
                pending.extend((x,depth+1) for x in item)
            elif type(item) is int and not -(2**63)<=item<2**63:
                raise ImportError('Upstream integer exceeds signed 64-bit bounds')
            elif type(item) is float and not math.isfinite(item):
                raise ImportError('Nonfinite upstream JSON number')
        _encode(value)  # Also rejects unpaired Unicode surrogates.
        return value
    except (ValueError,UnicodeError,RecursionError) as error:
        raise ImportError('Invalid upstream JSON: '+str(error)) from error


def _path(path: str) -> str:
    if not isinstance(path,str) or not path or len(path.encode('utf-8'))>4096:
        raise ImportError('Invalid capture path')
    if '\\' in path or any(ord(c)<32 for c in path) or PurePosixPath(path).is_absolute():
        raise ImportError('Capture paths must be relative POSIX paths')
    if any(p in {'','.','..'} for p in path.split('/')):
        raise ImportError('Capture path is noncanonical or traverses its root')
    return path


def _node_key(identifier: str):
    if not isinstance(identifier,str) or not re.fullmatch(r'1(?:\.[1-9][0-9]*)*',identifier) or identifier.count('.')>64:
        raise ImportError('Invalid or over-deep upstream node ID: '+str(identifier))
    return tuple(int(x) for x in identifier.split('.'))


def _timestamp(value: str | None) -> str:
    """Mirror Timestamp.String without losing nanoseconds to Python microseconds."""
    if value is None:return '0001-01-01T00:00:00Z'
    match=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)',value)
    if not match:raise ImportError('Unsupported upstream timestamp')
    instant=datetime.fromisoformat(match[1]+match[3].replace('Z','+00:00')).astimezone(timezone.utc)
    fraction=(match[2] or '').rstrip('0')
    return instant.isoformat(timespec='seconds').removesuffix('+00:00')+('.'+fraction if fraction else '')+'Z'


def node_content_hash(node: dict) -> str:
    """The pinned upstream hash, distinct from the full V3 context identity."""
    value='type:'+node['type']+'|statement:'+node['statement']
    if node.get('latex'):
        value+='|latex:'+node['latex']
    value+='|inference:'+node['inference']
    for key in ('context','dependencies','validation_deps'):
        if node.get(key):
            value+='|'+key+':'+','.join(sorted(node[key]))
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class Protocol:
    """Byte-pinned generated protocol schemas, with offline reference lookup."""
    def __init__(self,directory: Path | None=None):
        directory=directory or ROOT/'schema v0.0/upstream/vibefeld-392b2da3'
        limits=CaptureLimits()
        self.manifest=_json((directory/'manifest.json').read_bytes(),limits)
        if (self.manifest.get('upstream_commit')!=PINNED_COMMIT or
            set(self.manifest.get('graph_features',[]))!=set(FEATURES) or
            self.manifest.get('event_count')!=len(EVENT_TYPES)):
            raise ImportError('Unsupported local protocol manifest')
        self.hash=digest(_encode(self.manifest))
        self.schemas={}
        resources=[]
        # This field is the maintained protocol manifest's explicit schema list.
        for entry in self.manifest['schemas']:
            name=entry['path']
            if Path(name).name!=name or (directory/name).is_symlink():
                raise ImportError('Protocol manifest uses a nonlocal schema path')
            raw=(directory/name).read_bytes()
            expected=entry['sha256'].removeprefix('sha256:')
            if hashlib.sha256(raw).hexdigest()!=expected:
                raise ImportError('Protocol schema differs from its pinned manifest: '+name)
            schema=_json(raw,limits)
            Draft202012Validator.check_schema(schema)
            self.schemas[name]=schema
            resources.append((schema['$id'],Resource.from_contents(schema)))
        def no_network(uri):
            raise NoSuchResource(ref=uri)
        self.registry=Registry(retrieve=no_network).with_resources(resources)
        self.validators={name:Draft202012Validator(schema,registry=self.registry,format_checker=FormatChecker()) for name,schema in self.schemas.items()}

    def check(self,name,value):
        parts=name.split('#',1)
        validator=self.validators[parts[0]]
        if len(parts)==2:
            validator=validator.evolve(schema={'$ref':self.schemas[parts[0]]['$id']+'#'+parts[1]})
        errors=list(validator.iter_errors(value))
        if errors:
            first=errors[0]
            raise ImportError(name+' '+('/'+'/'.join(map(str,first.absolute_path)))+': '+first.message[:1500])


def _replay(events: list[dict],limits: CaptureLimits) -> dict:
    nodes={};definitions={};lemmas={};challenges={};scopes={};outline=[];outline_links={}
    history=[]
    initialized=False
    def node(identifier):
        if identifier not in nodes:
            raise ImportError('Event refers to an absent node: '+str(identifier))
        return nodes[identifier]
    for event in events:
        event_type=event['type']
        if event_type not in EVENT_TYPES:
            raise ImportError('Unsupported event type: '+event_type)
        if event_type=='proof_initialized':
            if initialized or history:
                raise ImportError('Proof initialization must occur once at the ledger start')
            initialized=True
        elif not initialized:
            raise ImportError('Missing initial proof_initialized event')
        elif event_type=='node_created':
            value=copy.deepcopy(event['node']);identifier=value['id'];_node_key(identifier)
            if identifier in nodes:
                raise ImportError('Node creation overwrites an existing identity: '+identifier)
            if len(nodes)>=limits.max_nodes:
                raise ImportError('Node count limit exceeded')
            if value['content_hash']!=node_content_hash(value):
                raise ImportError('Created node content hash mismatch: '+identifier)
            for key in ('context','dependencies','validation_deps','scope'):
                value[key]=value.get(key) or []
            for key in ('latex','author','validated_by','validation_batch_id','proof_author','claimed_by','claimed_at'):
                value.setdefault(key,'')
            value.setdefault('crux',False)
            value['created']=_timestamp(value['created'])
            nodes[identifier]=value
        elif event_type in {'nodes_claimed','nodes_released'}:
            for identifier in event['node_ids'] or []:
                value=node(identifier)
                next_state='claimed' if event_type=='nodes_claimed' else 'available'
                allowed={'available':{'claimed'},'claimed':{'available','blocked'},'blocked':{'available'}}
                if next_state not in allowed[value['workflow_state']]:
                    raise ImportError('Invalid recorded workflow transition for '+identifier)
                value['workflow_state']=next_state
                value['claimed_by']=event.get('owner','')
                value['claimed_at']=event.get('timeout','')
        elif event_type=='claim_refreshed':
            value=node(event['node_id'])
            if value['workflow_state']!='claimed' or value['claimed_by']!=event['owner']:
                raise ImportError('Claim refresh does not match the recorded owner')
            value['claimed_at']=event['new_timeout']
        elif event_type in {'node_validated','node_admitted','node_refuted','node_archived','refinement_requested','node_submitted','node_unvalidated','node_unadmitted','node_vetoed'}:
            value=node(event['node_id'])
            next_state={'refinement_requested':'needs_refinement','node_submitted':'pending','node_unvalidated':'pending','node_unadmitted':'pending','node_vetoed':'refuted'}.get(event_type,event_type.removeprefix('node_'))
            if event_type=='node_vetoed':
                if value['epistemic_state'] in SEVERED:
                    raise ImportError('Veto applied to a terminal node')
            elif next_state not in TRANSITIONS[value['epistemic_state']]:
                raise ImportError('Invalid recorded epistemic transition for '+event['node_id'])
            value['epistemic_state']=next_state
            if event_type=='node_validated':
                value['validated_by']=event.get('verified_by','')
                value['validation_batch_id']=event.get('batch_id','')
            if event_type=='node_unvalidated':
                value['validated_by']='';value['validation_batch_id']=''
            if next_state in SEVERED:
                for challenge in challenges.values():
                    if challenge['node_id']==event['node_id'] and challenge['status']=='open':
                        challenge['status']='superseded'
        elif event_type=='node_proof_authored':
            node(event['node_id'])['proof_author']=event['author']
        elif event_type=='node_amended':
            value=node(event['node_id'])
            if value['statement']!=event['previous_statement']:
                raise ImportError('Amendment previous statement disagrees with ledger state')
            value['statement']=event['new_statement'];value['content_hash']=node_content_hash(value)
        elif event_type=='taint_recomputed':
            node(event['node_id'])  # Preserved as an event; final taint is recomputed below.
        elif event_type in {'def_added','lemma_extracted'}:
            field='definition' if event_type=='def_added' else 'lemma'
            collection=definitions if field=='definition' else lemmas
            value=copy.deepcopy(event[field])
            if field=='lemma':
                node(value['node_id'])
            if value['id'] in collection:
                raise ImportError('Repeated context identity would overwrite its history: '+value['id'])
            collection[value['id']]=value
        elif event_type=='challenge_raised':
            identifier=event['challenge_id'];node(event['node_id'])
            if identifier in challenges:
                raise ImportError('Duplicate challenge identity')
            if (event.get('severity') or 'major') not in {'critical','major','minor','note'}:
                raise ImportError('Unsupported challenge severity')
            if event.get('category','') not in {'','gap','missing','dependency','incorrect','unclear','other'}:
                raise ImportError('Unsupported challenge category')
            challenges[identifier]={**copy.deepcopy(event),'status':'open','severity':event.get('severity') or 'major'}
        elif event_type in {'challenge_resolved','challenge_withdrawn','challenge_superseded'}:
            if event['challenge_id'] not in challenges:
                raise ImportError('Disposition refers to an absent challenge')
            challenge=challenges[event['challenge_id']]
            if event_type=='challenge_superseded' and challenge['node_id']!=event['node_id']:
                raise ImportError('Superseded challenge targets a different node')
            challenge['status']=event_type.removeprefix('challenge_')
        elif event_type=='scope_opened':
            identifier=event['node_id'];value=node(identifier)
            if identifier in scopes or not event['statement'].strip():
                raise ImportError('Repeated or empty assumption scope')
            if value['type']!='local_assume':
                raise ImportError('Scope origin is not a local-assumption node')
            scopes[identifier]={'node_id':identifier,'statement':event['statement'],'introduced':event['timestamp'],'discharged':None,'discharge_node_id':None}
        elif event_type=='scope_closed':
            scope=scopes.get(event['node_id']);node(event['discharge_node_id'])
            if scope is None or scope['discharged'] is not None:
                raise ImportError('Missing or already closed assumption scope')
            scope['discharged']=event['timestamp'];scope['discharge_node_id']=event['discharge_node_id']
        elif event_type=='outline_set':
            outline=copy.deepcopy(event['stages'] or [])
        elif event_type=='outline_stage_linked':
            node(event['node_id'])
            matching=[s for s in outline if s['label']==event['label']]
            if len(matching)!=1:
                raise ImportError('Outline link requires one exact existing stage')
            outline_links[event['label']]=event['node_id']
        elif event_type in {'approach_tried','evidence_attached','hint_added','strategy_proposed','claim_tested'}:
            node(event['node_id'])
        elif event_type in {'pattern_added','def_checked','lock_reaped'}:
            pass  # Full attributed metadata retained in history, not discarded.
        else:
            raise ImportError('Known event has no replay handler: '+event_type)
        history.append(copy.deepcopy(event))
    for identifier,value in nodes.items():
        if identifier!='1' and identifier.rsplit('.',1)[0] not in nodes:
            raise ImportError('Capture has a node without its display parent: '+identifier)
    return {'nodes':nodes,'definitions':definitions,'lemmas':lemmas,'challenges':challenges,'scopes':scopes,'outline':outline,'outline_links':outline_links,'history':history}


def _graph_projection(state: dict,workspace: dict) -> dict:
    """Pinned export-derived labels. These never become V3 assessment axes."""
    nodes=state['nodes'];challenges=state['challenges']
    order=sorted(nodes,key=_node_key)
    children=defaultdict(list)
    for identifier in order:
        if '.' in identifier:
            children[identifier.rsplit('.',1)[0]].append(identifier)
    contribution=lambda value: 2 if value in UNRESOLVED else 1 if value=='admitted' else 0
    down={};chain={};up={};taints={};closed={};blocking=set()
    for challenge in challenges.values():
        if challenge['status']=='open' and challenge['severity'] in {'major','critical'}:
            blocking.add(challenge['node_id'])
    for identifier in sorted(order,key=lambda i:len(_node_key(i))):
        parent=identifier.rsplit('.',1)[0] if '.' in identifier else None
        down[identifier]=chain.get(parent,0)
        chain[identifier]=max(down[identifier],contribution(nodes[identifier]['epistemic_state']))
    for identifier in sorted(order,key=lambda i:-len(_node_key(i))):
        value=nodes[identifier];state_value=value['epistemic_state'];parts=[]
        for child in children[identifier]:
            child_state=nodes[child]['epistemic_state']
            if child_state in SEVERED:continue
            parts.append(contribution(child_state) or up[child])
        up[identifier]=max(parts,default=0)
        if state_value in SEVERED:taint='clean'
        elif state_value in UNRESOLVED or down[identifier]==2:taint='unresolved'
        elif state_value=='admitted':taint='self_admitted'
        elif up[identifier]==2:taint='unresolved'
        elif down[identifier]==1 or up[identifier]==1:taint='tainted'
        else:taint='clean'
        taints[identifier]=taint
        closed[identifier]=(state_value in CLEARED and value['workflow_state']!='blocked' and identifier not in blocking and all(closed[c] for c in children[identifier]))
    output=[]
    required=('id','type','statement','inference','content_hash','workflow_state','epistemic_state','created')
    optional=('latex','crux','author','validated_by','validation_batch_id','proof_author','dependencies')
    for identifier in order:
        value=nodes[identifier]
        row={k:value[k] for k in required}
        row['taint_state']=taints[identifier]
        for key in optional:
            if value.get(key):row[key]=copy.deepcopy(value[key])
        if '.' in identifier:row['parent_id']=identifier.rsplit('.',1)[0]
        if children[identifier]:row['child_ids']=children[identifier]
        if closed[identifier]:row['closed']=True
        if value['workflow_state']!='blocked' and (value['epistemic_state'] in {'draft','needs_refinement'} or value['epistemic_state']=='pending' and identifier in blocking):
            row['prover_ready']=True
        if value['statement'] and value['workflow_state']=='available' and value['epistemic_state']=='pending' and identifier not in blocking and all(nodes[c]['epistemic_state'] in CLEARED for c in children[identifier]):
            row['verifier_ready']=True
        output.append(row)
    return {'schema_version':'1','features':list(FEATURES),'workspace':copy.deepcopy(workspace),'nodes':output,
        'validation':{'total_nodes':len(nodes),'epistemic_counts':dict(Counter(n['epistemic_state'] for n in nodes.values())),
            'taint_counts':dict(Counter(taints.values())),'total_challenges':len(challenges),
            'challenge_status_counts':dict(Counter(c['status'] for c in challenges.values()))}}


@dataclass(frozen=True)
class CaptureInspection:
    files: Mapping[str,bytes]
    _report: bytes

    def __post_init__(self):
        object.__setattr__(self,'files',MappingProxyType(dict(self.files)))

    def report(self) -> dict:
        return json.loads(self._report)

    def json_bytes(self) -> bytes:
        return self._report


def inspect_capture(files: Mapping[str,bytes],*,commit: str,workspace_key: str,
                    protocol: Protocol | None=None,limits: CaptureLimits=CaptureLimits()) -> CaptureInspection:
    """Inspect an explicit complete capture boundary, preserving every input.

    Expected names: graph.json, meta.json, ledger/NNNNNN.json and optional
    assumptions/*.json / externals/*.json plus referenced evidence files.
    identity-map.json maps upstream names to declared principal strings; its
    presence NEVER independently authenticates those principals.
    """
    protocol=protocol or Protocol()
    if len(files)>limits.max_files:
        raise ImportError('Capture file count limit exceeded')
    copied={};total=0
    for path,raw in files.items():
        _path(path)
        if type(raw) is not bytes or len(raw)>limits.max_file_bytes:
            raise ImportError('Capture member exceeds the original-byte file boundary')
        total+=len(raw)
        if total>limits.max_total_bytes:raise ImportError('Capture total byte limit exceeded')
        copied[path]=raw
    issues=[];missing=[];checks=['CAPTURE_BYTE_BOUNDARIES'];state=None;graph=None;meta=None
    if commit!=PINNED_COMMIT:issues.append({'code':'UNSUPPORTED_COMMIT','path':'','message':'Only the exact pinned source commit is supported'})
    if not re.fullmatch(r'[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:/-]*',workspace_key):
        raise ImportError('Provide a stable namespaced workspace key, not an absolute directory')
    for required in ('graph.json','meta.json'):
        if required not in copied:missing.append(required)
    ledger=[]
    for path in copied:
        if path.startswith('ledger/'):
            match=re.fullmatch(r'ledger/([0-9]{6,})\.json',path)
            if not match:
                issues.append({'code':'LEDGER_FILENAME','path':path,'message':'Unrecognized file inside the frozen ledger boundary'})
            else:ledger.append((int(match[1]),path))
    ledger.sort()
    if not ledger:missing.append('ledger events')
    if len(ledger)>limits.max_events:raise ImportError('Capture event count limit exceeded')
    if [n for n,_ in ledger]!=list(range(1,len(ledger)+1)):
        issues.append({'code':'LEDGER_SEQUENCE','path':'ledger','message':'Events must form a unique contiguous sequence from 1'})
    if not issues:
        try:
            if 'graph.json' in copied:
                graph=_json(copied['graph.json'],limits);protocol.check('graph.schema.json',graph)
                if graph['schema_version']!='1' or set(graph['features'])!=set(FEATURES):
                    raise ImportError('Unsupported graph version or exact pinned capability set')
                if len(graph['features'])!=len(FEATURES):raise ImportError('Duplicate graph capability')
                checks.append('GRAPH_PROTOCOL')
            events=[]
            for _,path in ledger:
                event=_json(copied[path],limits)
                if not isinstance(event,dict) or event.get('type') not in EVENT_TYPES:
                    raise ImportError('Unsupported event type at '+path)
                protocol.check('event.schema.json',event);events.append(event)
            if events:
                state=_replay(events,limits);checks.extend(['EVENT_PROTOCOL','LEDGER_SEQUENCE','NODE_CONTENT_HASHES','RECORDED_EVENT_REPLAY'])
                if not state['nodes']:missing.append('root node 1')
            if state is not None and graph is not None:
                expected=_graph_projection(state,graph['workspace'])
                # Compare semantic JSON values; upstream textual key order is not identity.
                if graph!=expected:raise ImportError('Graph projection disagrees with replayed ledger state')
                checks.append('GRAPH_LEDGER_AGREEMENT')
            if 'meta.json' in copied:
                meta=_json(copied['meta.json'],limits,allow_floats=True)
                protocol.check('sidecar.schema.json#/$defs/Config',meta)
                if meta.get('schema_path') or 'schema.json' in copied:
                    raise ImportError('Custom upstream schemas are outside this pinned import profile')
                checks.append('CONFIG_PROTOCOL')
            if meta is not None and graph is not None:
                for field in ('title','conjecture'):
                    if graph['workspace'].get(field,'')!=meta.get(field,''):
                        raise ImportError('Graph workspace metadata differs from meta.json: '+field)
                checks.append('META_GRAPH_AGREEMENT')
        except (ImportError,KeyError,TypeError,ValueError) as error:
            issues.append({'code':'PROTOCOL_OR_REPLAY','path':'','message':str(error)})
    context={};dependency_gaps=[]
    if state is not None and not issues:
        try:
            for path,raw in copied.items():
                if path.startswith(('nodes/','.af/pending_defs/')):
                    missing.append('separate interpretation of non-replay sidecar '+path)
                if path.startswith(('assumptions/','externals/','defs/','lemmas/')):
                    entry=_json(raw,limits)
                    category=path.split('/')[0]
                    names={'assumptions':'Assumption','externals':'External','defs':'Definition','lemmas':'Lemma'}
                    protocol.check('sidecar.schema.json#/$defs/'+names[category],entry)
                    if path!=category+'/'+entry['id']+'.json':raise ImportError('Context file name differs from its identity')
                    source=entry[{'assumptions':'statement','externals':'source','defs':'content','lemmas':'statement'}[category]]
                    if hashlib.sha256(source.encode('utf-8')).hexdigest()!=entry['content_hash']:
                        raise ImportError('Context content hash mismatch: '+path)
                    if entry['id'] in context or category!='defs' and entry['id'] in state['definitions']:
                        raise ImportError('Ambiguous context identity: '+entry['id'])
                    if category=='defs':
                        registered=state['definitions'].get(entry['id'])
                        if registered is None:missing.append('ledger definition for '+path)
                        elif registered['name']!=entry['name'] or registered['definition']!=entry['content']:
                            raise ImportError('Definition sidecar disagrees with ledger')
                    if category=='lemmas':
                        registered=state['lemmas'].get(entry['id'])
                        if registered is None:missing.append('ledger lemma for '+path)
                        elif registered['statement']!=entry['statement'] or registered['node_id']!=entry['source_node_id']:
                            raise ImportError('Lemma sidecar disagrees with ledger')
                    context[entry['id']]={'category':category,'entry':entry}
            for identifier,node in state['nodes'].items():
                for dependency in node['dependencies']+node['validation_deps']:
                    if dependency not in state['nodes']:missing.append('node '+identifier+' dependency '+dependency)
                    elif state['nodes'][dependency]['epistemic_state']!='validated':
                        dependency_gaps.append({'node_id':identifier,'dependency_id':dependency,'reported_dependency_state':state['nodes'][dependency]['epistemic_state']})
                for reference in node['context']:
                    if reference not in context and reference not in state['definitions']:
                        missing.append('node '+identifier+' context '+reference)
                for scope_id in node['scope']:
                    # Scope strings in the node are upstream context, not proof of discharge.
                    if scope_id not in state['scopes']:
                        missing.append('node '+identifier+' scope '+scope_id)
            for event in state['history']:
                if event['type']=='evidence_attached':
                    path=_path(event['file_path'])
                    if path not in copied:missing.append('attached evidence '+path)
                    elif hashlib.sha256(copied[path]).hexdigest()!=event['content_hash']:
                        raise ImportError('Attached evidence byte hash mismatch: '+path)
                if event['type'] in {'claim_tested','def_checked'} and event.get('script_path'):
                    path=_path(event['script_path'])
                    if path not in copied:missing.append('recorded test script '+path)
            checks.append('CONTEXT_AND_DEPENDENCY_PRESENCE')
        except (ImportError,KeyError,TypeError,ValueError) as error:
            issues.append({'code':'CONTEXT_OR_EVIDENCE','path':'','message':str(error)})
    identity_map=None
    if 'identity-map.json' not in copied:missing.append('identity-map.json (declared mapping, not authentication)')
    elif state is not None:
        try:
            identity_map=_json(copied['identity-map.json'],limits)
            if not isinstance(identity_map,dict) or not all(isinstance(k,str) and k and isinstance(v,str) and v for k,v in identity_map.items()):
                raise ImportError('Identity map must map nonempty upstream names to nonempty principal identifiers')
            names=set()
            for identifier,node in state['nodes'].items():
                for field in ('author','proof_author','validated_by'):
                    if node[field]:names.add(node[field])
                if not node['author']:missing.append('node '+identifier+' content author')
                if node['epistemic_state']=='validated' and not node['validated_by']:missing.append('node '+identifier+' reported verifier')
                if not node['proof_author'] and any(n.startswith(identifier+'.') for n in state['nodes']):
                    missing.append('node '+identifier+' decomposition author')
            for event in state['history']:
                for key in ('author','owner','verified_by','raised_by','tried_by','attached_by','hint_by','proposed_by','added_by','set_by','agent','revoked_by','requested_by','vetoed_by'):
                    if event.get(key):names.add(event[key])
            for name in sorted(names):
                if name not in identity_map:missing.append('principal mapping for '+name)
            checks.append('DECLARED_IDENTITY_MAP_COVERAGE')
        except (ImportError,ValueError) as error:
            issues.append({'code':'IDENTITY_MAP','path':'identity-map.json','message':str(error)})
    outcome='REJECTED' if issues else 'INCOMPLETE' if missing else 'STRUCTURALLY_IMPORTED'
    semantic=None
    if state is not None and not issues:
        semantic={'workspace_key':workspace_key,'commit':commit,'state':state,'context':context,'identity_map':identity_map,
                  'retained_artifacts':{p:digest(raw) for p,raw in sorted(copied.items()) if p!='graph.json'}}
    report={'report_type':ADAPTER_VERSION,'upstream_commit':commit,'protocol_manifest_hash':protocol.hash,
        'workspace_key':workspace_key,'outcome':outcome,'checks':checks,'issues':issues,'missing_items':sorted(set(missing)),
        'file_manifest':[{'path':path,'byte_size':len(raw),'sha256':digest(raw)} for path,raw in sorted(copied.items())],
        'semantic_snapshot_hash':digest(_encode(semantic)) if semantic is not None else None,
        'replayed_state':state,'context_sidecars':context,'reported_graph':graph,'dependency_gaps':dependency_gaps,
        'dependency_scan':'DIRECT_REPORTED_STATE_ONLY',
        'identity_assurance':'DECLARED_MAP_ONLY','scientific_assessment':'NOT_PERFORMED',
        'limitations':['Only the supplied capture boundary is inspected; omitted files or rewritten external history cannot be disproved.',
            'Reported validated, admitted, closed and clean are not V3 mathematical support or knowledge admission.',
            'Source components, joint-inference meaning, discharge validity and independent actor authority require separate V3 review.',
            'Local hash agreement is not an independently held checkpoint or authenticated execution receipt.',
            'Scope times come from raw events; upstream replay wall-clock scope timestamps are not copied.']}
    return CaptureInspection(copied,_encode(report)+b'\n')


def build_import_candidate(inspection: CaptureInspection,*,bundle: SchemaBundle,record_id: str,
                           producer: dict,policy_ref: dict,created_at: str,data_class: str='OBSERVED'):
    """Produce an attributed UpstreamImport candidate plus every retained byte.

    No ArgumentReview, MathClaim, assessment, release or admission is generated.
    Scientific interpretation of dependency meaning must be an explicit step.
    """
    report=inspection.report();artifacts={};by_path={}
    for path,raw in inspection.files.items():
        media='application/json' if path.endswith('.json') else 'application/octet-stream'
        artifact=SuppliedArtifact('artifact:vibefeld-'+hashlib.sha256(raw).hexdigest()+'-'+hashlib.sha256(media.encode()).hexdigest()[:8],media,raw)
        artifacts[artifact.artifact_id]=artifact;by_path[path]=artifact.reference(path)
    ledger_index=[{'path':path,'artifact':by_path[path]} for path in sorted(by_path) if path.startswith('ledger/')]
    ledger_artifact=None
    if ledger_index:
        raw=_encode(ledger_index)
        ledger_artifact=SuppliedArtifact('artifact:vibefeld-ledger-'+hashlib.sha256(raw).hexdigest(),'application/json',raw)
        artifacts[ledger_artifact.artifact_id]=ledger_artifact
    raw=inspection.json_bytes()
    inspection_artifact=SuppliedArtifact('artifact:vibefeld-inspection-'+hashlib.sha256(raw).hexdigest(),'application/json',raw)
    artifacts[inspection_artifact.artifact_id]=inspection_artifact
    payload={'engine':'vibefeld','commit':report['upstream_commit'],'protocol_version':'graph-v1/ledger-35',
        'adapter_version':ADAPTER_VERSION,'ledger':ledger_artifact.reference() if ledger_artifact else None,
        'graph':by_path.get('graph.json'),'context_artifacts':[by_path[p] for p in sorted(by_path) if p!='graph.json'],
        'identity_map':by_path.get('identity-map.json'),'reported_states':inspection_artifact.reference(),
        'import_checks':report['checks'],'outcome':report['outcome'],'missing_items':report['missing_items']}
    record=bundle.make_record('upstream-import',record_id,payload,producer=producer,policy_ref=policy_ref,
                              created_at=created_at,data_class=data_class)
    return record,tuple(artifacts.values())
