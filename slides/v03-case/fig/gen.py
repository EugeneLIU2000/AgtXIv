# -*- coding: utf-8 -*-
"""v0.3 dependency figures, in the talk's visual language:
   shape = node kind, hollow = nothing accepted, ink = extracted statement,
   warm = an open request the system has not answered."""
import json, collections, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

V3='/Users/Yingjian/Documents/GitHub/AgtXIv/schema v0.3/'
R='/Users/Yingjian/Documents/GitHub/AgtXIv/'
INK='#1A1A16'; OPEN='#8C4A2F'; MUTED='#7A7A72'; FAINT='#C9C9C4'; PAPER='#FFFFFF'

# shape = kind, shared with the seminar deck
MARK={'definition':'o','claim':'o','equation':'o',
      'lemma':'s','theorem':'D','proposition':'^',
      'external_contract':'h','standard_foundation':'h',
      'external_claim_request':'P','unresolved_claim_occurrence':'x'}

def load_v03():
    g=json.load(open(V3+'runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json'))
    G=nx.DiGraph()
    for n in g['nodes']: G.add_node(n['id'], kind=n['kind'], paper=bool(n.get('paper_id')))
    for e in g['edges']: G.add_edge(e['from'], e['to'])
    return G

def load_authored():
    d=json.load(open(R+'Stabilizerness/dag/claim-dag.json'))
    G=nx.DiGraph()
    for n in d['nodes']: G.add_node(n['id'], kind=n['kind'], layer=n['layer'], branch=n['branch'])
    for e in d['edges']: G.add_edge(e['from'], e['to'])
    return G

def draw(ax, G, pos, sizes=14, lw=0.9, ecol=FAINT, ealpha=0.55):
    for u,v in G.edges():
        if u in pos and v in pos:
            x1,y1=pos[u]; x2,y2=pos[v]
            ax.plot([x1,x2],[y1,y2], color=ecol, lw=lw, alpha=ealpha, zorder=1,
                    solid_capstyle='round')
    byk=collections.defaultdict(list)
    for n,d in G.nodes(data=True): byk[(d.get('kind'), d.get('paper', True))].append(n)
    for (kind,paper),ns in byk.items():
        xs=[pos[n][0] for n in ns if n in pos]; ys=[pos[n][1] for n in ns if n in pos]
        if not xs: continue
        m=MARK.get(kind,'o'); c=INK if paper else OPEN
        # 'x' and 'P' have no face; everything else stays hollow - nothing is accepted
        if m in ('x',):
            ax.scatter(xs,ys,marker=m,s=sizes,linewidths=0.9,color=c,zorder=3)
        else:
            ax.scatter(xs,ys,marker=m,s=sizes,facecolors=PAPER,edgecolors=c,
                       linewidths=0.9,zorder=3)
    ax.set_axis_off()

# ---------------- FIG 1 : the extracted graph, 613 nodes ----------------
G=load_v03()
U=G.to_undirected()
cc=sorted(nx.connected_components(U), key=len, reverse=True)
pos=nx.spring_layout(U, seed=11, k=0.42, iterations=220)
fig,ax=plt.subplots(figsize=(15,7.2), dpi=210)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
draw(ax,G,pos,sizes=15)
ax.set_title('')
handles=[Line2D([],[],marker='o',ls='',mfc=PAPER,mec=INK,mew=.9,ms=7,label='statement extracted from the frozen source  ·  240'),
         Line2D([],[],marker='P',ls='',mfc=PAPER,mec=OPEN,mew=.9,ms=7,label='external claim request  ·  152  ·  paper_id null'),
         Line2D([],[],marker='x',ls='',color=OPEN,mew=.9,ms=7,label='unresolved source occurrence  ·  221')]
lg=ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5,-0.07), ncol=3,
             frameon=False, fontsize=8.5, handletextpad=0.5, columnspacing=2.2)
for t in lg.get_texts(): t.set_color(MUTED)
plt.tight_layout(); plt.savefig('fig-613.png', facecolor=PAPER, bbox_inches='tight'); plt.close()
print('fig-613.png   613 nodes ·', G.number_of_edges(), 'edges ·', len(cc), 'components · largest', len(cc[0]))

# ---------------- FIG 2 : authored beside extracted, same canvas ----------------
A=load_authored()
posA={}
br=sorted({d['branch'] for _,d in A.nodes(data=True)})
BX={b:i for i,b in enumerate(br)}
buck=collections.defaultdict(list)
for n,d in A.nodes(data=True): buck[(d['layer'],d['branch'])].append(n)
for (L,b),ns in buck.items():
    ns.sort()
    for i,n in enumerate(ns): posA[n]=(BX[b]*1.0+(i-(len(ns)-1)/2)*0.22, L*1.0)

fig,axes=plt.subplots(1,2,figsize=(15,6.6), dpi=210)
fig.patch.set_facecolor(PAPER)
for a in axes: a.set_facecolor(PAPER)
for L in range(9):
    axes[0].axhline(L, color=FAINT, lw=0.7, alpha=0.5, zorder=0)
    axes[0].text(-0.75, L, f'L{L}', fontsize=6.5, color=MUTED, va='center', ha='right')
draw(axes[0],A,posA,sizes=26,lw=0.9,ecol='#9A9A94',ealpha=0.6)
axes[0].set_title('authored by hand  ·  74 nodes, 129 edges\none connected structure, acyclic by construction',
                  fontsize=10.5, color=INK, pad=14, linespacing=1.6)
draw(axes[1],G,pos,sizes=11,lw=0.7)
axes[1].set_title('extracted by machine  ·  613 nodes, 634 edges\n80 disconnected components  ·  24 isolated  ·  7 cycles',
                  fontsize=10.5, color=OPEN, pad=14, linespacing=1.6)
plt.tight_layout(); plt.savefig('fig-compare.png', facecolor=PAPER, bbox_inches='tight'); plt.close()
print('fig-compare.png  authored', A.number_of_nodes(), 'vs extracted', G.number_of_nodes())

# ---------------- FIG 3 : the 29-node closure, v0.3's re-derivation ----------------
cb=json.load(open(V3+'runs/2607-full-candidate-20260919/closed-form-branch.json'))
cn=cb.get('nodes') or []
cid={ (n['id'] if isinstance(n,dict) else n) for n in cn }
old=json.load(open(R+'schema v0.2/host_probe/evidence/closure.json'))
print('closure ids match v0.2:', {n["id"] for n in old["nodes"]} == cid, '| v0.3 closure nodes:', len(cid))

# ---------------- FIG 4 : the 29-node closure, v0.3's vocabulary ----------------
# Same ids and same layout as the seminar deck, so the two can be read side by
# side - but with v0.3's fields: no state, no declaration, 46 edges, all CANDIDATE.
oldn={n['id']:n for n in old['nodes']}
BR={'conceptual_foundation':0,'reduced_polytope':1,'relaxation':2,'optimization':3,'graph_theory':4,'closed_form':2}
C=nx.DiGraph()
for nid,n in oldn.items(): C.add_node(nid, kind=n['kind'], paper=True)
cbe = cb.get('edges') or []
for e in cbe:
    f=e.get('from') or e.get('source'); t=e.get('to') or e.get('target')
    if f in oldn and t in oldn: C.add_edge(f,t)
posC={}
bk=collections.defaultdict(list)
for nid,n in oldn.items(): bk[(n['layer'], n['branch'])].append(nid)
for (L,b),ns in bk.items():
    ns.sort()
    for i,nid in enumerate(ns): posC[nid]=(BR[b]+(i-(len(ns)-1)/2)*0.26, L)

fig,ax=plt.subplots(figsize=(14,6.4), dpi=210)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
for L in range(9):
    ax.axhline(L, color=FAINT, lw=0.7, alpha=0.55, zorder=0)
    ax.text(-0.85, L, f'L{L}', fontsize=7, color=MUTED, va='center', ha='right')
draw(ax,C,posC,sizes=64,lw=1.0,ecol='#9A9A94',ealpha=0.65)
for b,x in [('conceptual',0),('reduced polytope',1),('relaxation',2),('optimization',3),('graph theory',4)]:
    ax.text(x, -0.72, b, fontsize=7.5, color=MUTED, ha='center')
handles=[Line2D([],[],marker='o',ls='',mfc=PAPER,mec=INK,mew=1,ms=8,label='definition'),
         Line2D([],[],marker='s',ls='',mfc=PAPER,mec=INK,mew=1,ms=8,label='lemma'),
         Line2D([],[],marker='D',ls='',mfc=PAPER,mec=INK,mew=1,ms=8,label='theorem'),
         Line2D([],[],marker='^',ls='',mfc=PAPER,mec=INK,mew=1,ms=8,label='proposition'),
         Line2D([],[],marker='h',ls='',mfc=PAPER,mec=INK,mew=1,ms=9,label='imported foundation')]
lg=ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5,-0.15), ncol=5,
             frameon=False, fontsize=8.5, handletextpad=0.5, columnspacing=2.4)
for t in lg.get_texts(): t.set_color(MUTED)
ax.set_ylim(-1.15, 8.6)
plt.tight_layout(); plt.savefig('fig-closure.png', facecolor=PAPER, bbox_inches='tight'); plt.close()
print('fig-closure.png ', C.number_of_nodes(), 'nodes ·', C.number_of_edges(), 'edges (v0.3 re-derivation)')
print('  every node hollow: v0.3 has no state field - nothing is discharged')
