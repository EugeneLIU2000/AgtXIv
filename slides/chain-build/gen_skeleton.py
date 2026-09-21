# -*- coding: utf-8 -*-
"""The skeleton: which claims carry the load, and which dependencies can go.

THE MODEL IS VALIDATED AGAINST THE PIPELINE'S OWN ARTEFACT. closed-form-branch
.json records, for each of the 46 dependency edges, the set of claims that drop
out of the query's closure when that edge is removed. Removing an edge means
removing that member from its support group and recomputing the backward
closure of the query - and with those semantics this file reproduces all 46
recorded experiments exactly. The assertion below is the proof; if it ever
fails, the figure is drawn from a model that is not the pipeline's.

The result worth drawing is a trap. 29 of the 46 edges cost NOTHING when
removed on their own. Remove all 29 together and 14 of the 29 claims fall out
of the closure: individual redundancy does not compose. The honest skeleton has
to be computed greedily, re-checking after every single removal, and it leaves
28 edges rather than 17.
"""
import json, collections

R='/Users/Yingjian/Documents/GitHub/AgtXIv/'
b=json.load(open(R+'schema v0.3/runs/2607-full-candidate-20260919/closed-form-branch.json'))
geom=json.load(open('chain-geom.json'))
POS={n['id']:(n['cx'],n['cy']) for n in geom['nodes']}
KIND={n['id']:n['kind'] for n in geom['nodes']}

Q=b['query_ids'][0]
G={g['id']:(g['target'],list(g['members'])) for g in b['support_groups']}
EC=[(e['from'],e['to'],e['support_group_id'],set(e['removed_node_ids']))
    for e in b['edge_criticality']]

def closure(drop=frozenset()):
    """Backward closure of the query, with (group, member) pairs removed."""
    bytar=collections.defaultdict(list)
    for gid,(t,ms) in G.items():
        bytar[t].append([m for m in ms if (gid,m) not in drop])
    seen={Q}; st=[Q]
    while st:
        n=st.pop()
        for ms in bytar.get(n,[]):
            for m in ms:
                if m not in seen: seen.add(m); st.append(m)
    return seen

BASE=closure(); N=len(BASE)
mismatch=[(f,t) for f,t,gid,rm in EC if BASE-closure(frozenset({(gid,f)}))!=rm]
assert not mismatch, f'model disagrees with the artefact on {len(mismatch)} edges: {mismatch[:3]}'

# node criticality: drop every edge INTO a claim, i.e. cut it out of the graph
NCRIT={}
for n in BASE:
    drop=frozenset((gid,m) for gid,(t,ms) in G.items() for m in ms if m==n)
    NCRIT[n]=N-len(closure(drop))

FREE=frozenset((gid,f) for f,t,gid,rm in EC if not rm)      # free one at a time
TOGETHER=closure(FREE)
LOST=sorted(BASE-TOGETHER)

drop=set(); ch=True                                          # the honest skeleton
while ch:
    ch=False
    for f,t,gid,_ in EC:
        if (gid,f) in drop: continue
        if len(closure(frozenset(drop|{(gid,f)})))==N: drop.add((gid,f)); ch=True
KEPT=[(f,t) for f,t,gid,_ in EC if (gid,f) not in drop]

def xy(a,z): return {'x1':POS[a][0],'y1':POS[a][1],'x2':POS[z][0],'y2':POS[z][1]}
EDGES=[dict(f=f,t=t,loss=len(rm),free=not rm,
            skel=(f,t) in KEPT, **xy(f,t)) for f,t,gid,rm in EC]
EDGES.sort(key=lambda e:-e['loss'])

OUT={'nodes':[{'id':n,'x':POS[n][0],'y':POS[n][1],'kind':KIND[n],'crit':NCRIT[n],
               'lost_together': n in LOST} for n in BASE if n in POS],
     'edges':EDGES, 'losses':[e['loss'] for e in EDGES],
     'n_free':len(FREE), 'n_skel':len(KEPT), 'n_lost_together':len(LOST),
     'max_node':max(NCRIT.values()), 'max_edge':max(e['loss'] for e in EDGES),
     'total':N}
json.dump(OUT, open('skeleton-geom.json','w'))

print(f'model reproduces all {len(EC)} recorded omission experiments')
print(f'closure                        : {N} claims, {len(EC)} dependencies')
print(f'edges free ON THEIR OWN        : {len(FREE)}')
print(f'  ... removed ALL TOGETHER     : {len(LOST)} claims fall out')
print(f'skeleton (greedy, re-checked)  : {len(KEPT)} edges, {len(closure(frozenset(drop)))} claims kept')
print('most load-bearing claims:')
for k,v in sorted(NCRIT.items(), key=lambda kv:-kv[1])[:5]: print(f'   {v:>3}   {k}')
