# -*- coding: utf-8 -*-
"""Opening frames: the whole extracted graph, then the change of object,
then the real subgraph extraction (74 -> 29).

HONESTY NOTE, enforced by construction: the 613-node extracted graph and the
74-node authored DAG share ZERO node ids, and a byte-overlap test matches 436
of 458 candidates to some authored claim - far too coarse to call a subgraph.
So frames 0-1 and frames 2-3 are DIFFERENT OBJECTS, and the sequence never
draws a zoom between them. The only extraction shown is 74 -> 29, which is an
exact subset (verified: closure ids are a strict subset of the authored DAG).
"""
import json, collections, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx

R='/Users/Yingjian/Documents/GitHub/AgtXIv/'
INK='#1A1A16'; OPEN='#8C4A2F'; FAINT='#C9C9C4'; PAPER='#FFFFFF'; GHOST='#E8E8E4'
MARK={'definition':'o','claim':'o','equation':'o','lemma':'s','theorem':'D',
      'proposition':'^','external_contract':'h','standard_foundation':'h',
      'construction':'o','empirical_protocol':'o','empirical_claim':'o',
      'limitation':'o','open_problem':'o',
      'external_claim_request':'P','unresolved_claim_occurrence':'x'}

ex=json.load(open(R+'schema v0.3/runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json'))
au=json.load(open(R+'Stabilizerness/dag/claim-dag.json'))
clo={n['id'] for n in json.load(open(R+'schema v0.2/host_probe/evidence/closure.json'))['nodes']}
A={n['id'] for n in au['nodes']}
assert clo <= A, 'closure must be a strict subset of the authored DAG'

G=nx.DiGraph()
for n in ex['nodes']: G.add_node(n['id'], kind=n['kind'], tgt=bool(n.get('paper_id')))
for e in ex['edges']: G.add_edge(e['from'], e['to'])
posE=nx.spring_layout(G.to_undirected(), seed=11, k=0.42, iterations=220)

AG=nx.DiGraph()
for n in au['nodes']: AG.add_node(n['id'], kind=n['kind'], layer=n['layer'], branch=n['branch'])
for e in au['edges']: AG.add_edge(e['from'], e['to'])
br=sorted({d['branch'] for _,d in AG.nodes(data=True)})
BX={b:i for i,b in enumerate(br)}
bk=collections.defaultdict(list)
for n,d in AG.nodes(data=True): bk[(d['layer'],d['branch'])].append(n)
posA={}
for (L,b),ns in bk.items():
    ns.sort()
    for i,n in enumerate(ns): posA[n]=(BX[b]+(i-(len(ns)-1)/2)*0.22, L)

W,H,DPI = 15.0, 8.12, 200      # 16:9-ish, matches the chain frames

def render(fn, Gx, pos, colour, size, ewidth=0.75, ecol=FAINT, ealpha=.5, edge_col=None):
    fig,ax=plt.subplots(figsize=(W,H), dpi=DPI)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    for u,v in Gx.edges():
        if u in pos and v in pos:
            c,a = (edge_col(u,v) if edge_col else (ecol,ealpha))
            ax.plot([pos[u][0],pos[v][0]],[pos[u][1],pos[v][1]],
                    color=c, lw=ewidth, alpha=a, zorder=1, solid_capstyle='round')
    byk=collections.defaultdict(list)
    for n,d in Gx.nodes(data=True): byk[(d.get('kind'), colour(n))].append(n)
    for (kind,c),ns in byk.items():
        xs=[pos[n][0] for n in ns if n in pos]; ys=[pos[n][1] for n in ns if n in pos]
        if not xs: continue
        m=MARK.get(kind,'o')
        if m=='x': ax.scatter(xs,ys,marker=m,s=size(ns[0]),linewidths=1.0,color=c,zorder=3)
        else: ax.scatter(xs,ys,marker=m,s=size(ns[0]),facecolors=PAPER,edgecolors=c,linewidths=1.0,zorder=3)
    ax.set_axis_off(); plt.tight_layout(pad=0.4)
    plt.savefig(fn, facecolor=PAPER)
    # also emit SVG so the page can inline it and stay self-contained
    plt.savefig(fn.replace('.png','.svg'), facecolor=PAPER, format='svg')
    plt.close()
    print(' ', fn)

# f0 - everything extracted, undifferentiated
render('frames/open00.png', G, posE, lambda n: INK, lambda n: 20)
# f1 - two colours: the target paper's own claims, and everything else
render('frames/open01.png', G, posE,
       lambda n: INK if G.nodes[n]['tgt'] else OPEN, lambda n: 20)
# f2 - a DIFFERENT object: the paper's authored DAG
render('frames/open02.png', AG, posA, lambda n: INK, lambda n: 60)
# f3 - inside it, the closure of the one theorem
render('frames/open03.png', AG, posA,
       lambda n: INK if n in clo else GHOST,
       lambda n: 95 if n in clo else 45,
       ewidth=0.9,
       edge_col=lambda u,v: ((INK,.55) if (u in clo and v in clo) else (GHOST,.75)))
print('extracted %d nodes | authored %d | closure %d (subset verified)' % (
      G.number_of_nodes(), AG.number_of_nodes(), len(clo)))
print('target-paper nodes: %d | other: %d' % (
      sum(1 for n in G if G.nodes[n]['tgt']), sum(1 for n in G if not G.nodes[n]['tgt'])))
