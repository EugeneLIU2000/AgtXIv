# -*- coding: utf-8 -*-
"""The ending: three wishes, and one measurement that makes them worth wishing.

  WISH ONE   more papers decomposed, and one network rather than a pile
  MEASURED   which claims carry the load, and which dependencies can be cut
             with nothing lost - the SKELETON
  WISH TWO   propose a claim into a gap the structure names
  WISH THREE a new paper is cheap to check, because it inherits what is checked

The middle block is not a wish. It runs on the real 29-claim chain the deck
just built, using the pipeline's own edge_criticality artefact and a node
omission computed the same way. 29 of the 46 dependencies cost nothing on
their own - but they do not compose, so the greedy skeleton keeps 28.

The teal junction hue appears on exactly one frame here, frame 6, and means what
it means everywhere else: a junction. The threshold marker on the inset chart is
ink, because a threshold is not a junction.

IMPORTANCE IS ENCODED AS SIZE AND INK, NOT AS A NEW HUE. The reference figures
for this frame use a blue-to-red colour scale, and a red ramp would collide
head-on with the one thing warm means in every other frame of this deck - NOT
FROM THIS PAPER. Size plus luminance is a double encoding, it survives a
projector and colour-blindness, and it costs no vocabulary.
"""
import json, random
from frames_lib import Fig, INK, LIGHT, OPEN, PAPER

JUNC='#1F6F78'
SK=json.load(open('skeleton-geom.json'))

def sh(a, base=INK):
    """An ink shade at coverage a, mixed against the page."""
    h=base.lstrip('#'); c=[int(h[i:i+2],16) for i in (0,2,4)]
    return '#%02X%02X%02X' % tuple(round(a*v+(1-a)*255) for v in c)

F=Fig('clo', 'The real 29-claim chain re-drawn with each claim sized by how much is lost'
             ' if it is removed; its 46 dependencies weighted the same way; the 29 that'
             ' cost nothing alone removed one at a time to leave a 28-edge skeleton;'
             ' and two further'
             ' frames proposing a new claim and absorbing a new paper.')
box, txt, line, dot, mark, curve = F.box, F.txt, F.line, F.dot, F.mark, F.curve

SK=json.load(open('skeleton-geom.json'))

def sh(a, base=INK):
    """An ink shade at coverage a, mixed against the page."""
    h=base.lstrip('#'); c=[int(h[i:i+2],16) for i in (0,2,4)]
    return '#%02X%02X%02X' % tuple(round(a*v+(1-a)*255) for v in c)

SS=22; NS=42

# ---- the chain, mapped into the left two thirds --------------------------
XS=[n['x'] for n in SK['nodes']]; YS=[n['y'] for n in SK['nodes']]
S=0.695; X0,Y0=80,238
def PX(x): return X0+(x-121)*S
def PY(y): return Y0+(y-95)*S
MAXN, MAXE = SK['max_node'], SK['max_edge']

# label, and an explicit offset - the top four sit close together at the
# bottom of the chain, so a uniform offset stacks them on top of each other
NAME={'claim:exact-graph-program': ('the graph program',    30, -12),
      'claim:relaxed-mwis-dual':   ('the MWIS dual',        30, -12),
      'claim:relaxed-lp-dual':     ('the LP dual',          30, -12),
      'claim:no-active-free-signs':('no active free signs', 30,  22)}

def chain_nodes(step, weighted, labels=False):
    for n in SK['nodes']:
        f = n['crit']/MAXN
        r = (8 + 16*f) if weighted else 9
        col = sh(0.42+0.58*f) if weighted else INK
        mark(step, n['kind'], PX(n['x']), PY(n['y']), r,
             color=col, lw=3.4 if (weighted and f>0.6) else 2.6)
    if labels:
        for nid,(lab,dx,dy) in NAME.items():
            n=next(x for x in SK['nodes'] if x['id']==nid)
            r=8+16*n['crit']/MAXN
            x = PX(n['x'])+(r+dx if dx>0 else dx)
            txt(step, x, PY(n['y'])+dy, 470, SS, f'{lab}  \u2014  {n["crit"]}')

def chain_edges(step, weighted=False, only_load=False):
    for e in SK['edges']:
        if only_load and e['loss']==0: continue
        f=e['loss']/MAXE
        lw = (1.6 + 5.0*f) if weighted else 1.9
        col = sh(0.24+0.76*f) if weighted else sh(0.46)
        x1,y1,x2,y2 = PX(e['x1']),PY(e['y1']),PX(e['x2']),PY(e['y2'])
        ym=(y1+y2)/2
        curve(step, x1,y1, x1,ym, x2,ym, x2,y2, color=col, lw=lw)

def legend(step):
    txt(step,1290,236,560,SS,'claims lost if this one is removed',color=LIGHT)
    for k,v in enumerate((1,5,10,15,20)):
        f=v/MAXN; x=1320+k*112
        dot(step,x,320,8+16*f,color=sh(0.42+0.58*f),lw=2.0,fill='#ffffff')
        txt(step,x-30,356,60,20,str(v),color=LIGHT,align='c')

def inset(step, mark_zero=False):
    """The trend, small and to the side: 46 edges sorted by what their removal
    costs. It is the shape that matters, so it does not need the whole stage."""
    IX0,IX1,IB,IH=1300,1800,806,190
    for k,v in enumerate(SK['losses']):
        x=IX0+k*(IX1-IX0)/(len(SK['losses'])-1)
        h=max(2, v/MAXE*IH)
        box(step,x-4,IB-h,8,h,fill=INK,lw=0)
    line(step,IX0-16,IB,IX1+16,IB,color=LIGHT,lw=1.4)
    txt(step,1300,IB-IH-38,520,20,'sorted by what removing one costs',color=LIGHT)
    if mark_zero:
        z=len(SK['losses'])-SK['n_free']
        xz=IX0+z*(IX1-IX0)/(len(SK['losses'])-1)-6
        line(step,xz,IB+8,xz,IB-IH-8,color=INK,lw=1.6)
        txt(step,xz+12,IB-IH-8,420,20,f'{SK["n_free"]} cost nothing alone',color=INK)

# =====================================================================
# 0 - the object: one paper, as the deck left it
# =====================================================================
chain_edges(0); chain_nodes(0, weighted=False)

# =====================================================================
# 1 - WISH ONE: more papers, and it stops being a pile
# =====================================================================
KINDS=(['definition']*11+['lemma']*6+['external_contract']*5+
       ['theorem']*4+['proposition']*2+['standard_foundation'])
def cluster(seed,cx,cy,rx,ry,n):
    rnd=random.Random(seed); pts=[]
    for _ in range(n):
        for _t in range(400):
            r=rnd.uniform(0,1)**0.5
            x=cx+rx*r*rnd.uniform(-1,1); y=cy+ry*r*rnd.uniform(-1,1)
            if all((x-px)**2+(y-py)**2>52**2 for px,py in pts): pts.append((x,y)); break
    assert len(pts)==n, f'cluster {seed}: placed {len(pts)} of {n}'
    return pts
CL=[(11,400,540,195,175,16),(23,1000,280,185,115,12),
    (37,1060,790,185,110,11),(51,1610,510,170,150,12)]
NET={i:cluster(*c) for i,c in enumerate(CL)}
HUB=((0,0),(1,0),(2,0),(3,0))

def schematic(step, clusters, heavy=()):
    for ci in clusters:
        pts=NET[ci]
        for k in range(1,len(pts)):
            j=min(range(k), key=lambda q:(pts[q][0]-pts[k][0])**2+(pts[q][1]-pts[k][1])**2)
            line(step,pts[k][0],pts[k][1],pts[j][0],pts[j][1],color=sh(.40),lw=2.0)
    for a,b in ((0,1),(1,3),(0,2),(2,3)):
        if a in clusters and b in clusters:
            pa,pb=NET[a][0],NET[b][len(NET[b])//2]
            line(step,pa[0],pa[1],pb[0],pb[1],lw=2.8)
    # ONE neutral mark, not the kind vocabulary. These points are invented;
    # drawing them as diamonds and hexagons made every one of them assert a
    # kind, thirty frames after the deck taught the audience to read that.
    for ci in clusters:
        for k,(x,y) in enumerate(NET[ci]):
            hv=(ci,k) in heavy
            dot(step,x,y,15 if hv else 10,lw=4.2 if hv else 2.5)
    txt(step,1560,980,320,20,'schematic',color=LIGHT)

schematic(1,[0,1,2,3])

# =====================================================================
# 2 - MEASURED: which claims carry the load
# =====================================================================
chain_edges(2); chain_nodes(2, weighted=True, labels=True); legend(2)

# =====================================================================
# 3 - MEASURED: the same question asked of every dependency
# =====================================================================
chain_edges(3, weighted=True); chain_nodes(3, weighted=False); inset(3)

# =====================================================================
# 4 - the trap: each of the 29 is free ON ITS OWN
# =====================================================================
for e in SK['edges']:
    if e['free']:
        line(4,PX(e['x1']),PY(e['y1']),PX(e['x2']),PY(e['y2']),color=sh(.88),lw=3.6)
    else:
        line(4,PX(e['x1']),PY(e['y1']),PX(e['x2']),PY(e['y2']),color=sh(.16),lw=1.2)
for n in SK['nodes']:
    gone=n['lost_together']
    mark(4,n['kind'],PX(n['x']),PY(n['y']),9,
         color=sh(.16) if gone else INK, lw=2.0)
inset(4, mark_zero=True)

# =====================================================================
# 5 - the skeleton, computed one removal at a time
# =====================================================================
for e in SK['edges']:
    if e['skel']:
        line(5,PX(e['x1']),PY(e['y1']),PX(e['x2']),PY(e['y2']),
             color=sh(0.30+0.70*e['loss']/MAXE), lw=1.9+4.6*e['loss']/MAXE)
chain_nodes(5, weighted=False)

# =====================================================================
# 6 - WISH TWO: a claim in a gap the structure names
# =====================================================================
schematic(6,[0,1,2,3],heavy=HUB)
NX,NY=712,545; JY=NY+112
for px,py in [NET[0][0],NET[1][0],NET[2][0]]:
    line(6,px,py,NX,JY,color=JUNC,lw=1.8)
dot(6,NX,JY,13,color=JUNC,lw=2.4,fill='#ffffff')
line(6,NX-8,JY,NX+8,JY,color=JUNC,lw=2.2)
line(6,NX,JY-8,NX,JY+8,color=JUNC,lw=2.2)
line(6,NX,JY-13,NX,NY+26,lw=2.4,arrow=True)
mark(6,'theorem',NX,NY,26,lw=4.0)
txt(6,NX+44,NY-14,620,SS,'proposed')

# =====================================================================
# 7 - WISH THREE: the next paper is cheap, because it inherits
# =====================================================================
BASE_Y=760
rnd=random.Random(3)
basepts=[]
for k in range(22):
    x=150+k*(820/21); y=BASE_Y+rnd.uniform(-46,46)
    basepts.append((x,y))
for k in range(1,len(basepts)):
    line(7,basepts[k-1][0],basepts[k-1][1],basepts[k][0],basepts[k][1],color=sh(.35),lw=1.4)
for k,(x,y) in enumerate(basepts):
    mark(7,KINDS[k%len(KINDS)],x,y,11,color=INK,lw=2.0,fill=INK)
txt(7,150,BASE_Y+96,760,SS,'already checked — and it stays checked',color=LIGHT)

NEWP=cluster(77,1330,360,230,180,12)
for k in range(1,len(NEWP)):
    j=min(range(k), key=lambda q:(NEWP[q][0]-NEWP[k][0])**2+(NEWP[q][1]-NEWP[k][1])**2)
    line(7,NEWP[k][0],NEWP[k][1],NEWP[j][0],NEWP[j][1],color=LIGHT,lw=1.4)
for k,(x,y) in enumerate(NEWP):
    mark(7,KINDS[(k*5)%len(KINDS)],x,y,11,lw=2.0)
txt(7,1120,150,760,SS,'a new paper')
_order=sorted(range(len(NEWP)), key=lambda k: NEWP[k][0])
NEWK={_order[1],_order[5],_order[9]}          # the only genuinely new claims
# everything else already rests on something down there
for k in range(len(NEWP)):
    if k in NEWK: continue
    x,y=NEWP[k]
    bx,by=basepts[(k*2+3)%len(basepts)]
    line(7,x,y,bx,by,color=sh(.28),lw=1.3)
# and only these three are genuinely new - picked spread across the cluster,
# so the three junctions do not land on top of each other
for k in sorted(NEWK):
    x,y=NEWP[k]
    dot(7,x,y+54,11,color=JUNC,lw=2.2,fill='#ffffff')
    line(7,x-6,y+54,x+6,y+54,color=JUNC,lw=2.0)
    line(7,x,y+48,x,y+60,color=JUNC,lw=2.0)
    line(7,x,y+43,x,y+15,lw=2.2,arrow=True)
txt(7,1120,600,760,SS,'three new checks, not a hundred',color=JUNC)

# ---- the headline band -------------------------------------------------
# Every frame in this act used to open with a 22px grey caption, or with
# nothing at all, which left the room to work out from the picture what it was
# being shown. The band above y=238 is empty on the measured frames and empty
# left of x=815 on the schematic ones, so the headline goes there - wide on the
# first kind, narrow and two-line on the second.
HS2=34
CHAINW, SCHEMW = 1150, 640
HEADS=[
 (0,'chain','One theorem, and everything it rests on',
    '29 claims and 46 dependencies \u2014 the object the rest of this act works on'),
 (1,'schem','Wish one','More papers, one network',
    'the same claim leaned on twice, by two papers'),
 (2,'chain','Which claims actually carry the load',
    'remove one claim, recompute the closure, count what leaves \u2014 size is what is lost'),
 (3,'chain','The same question, asked of every dependency',
    f"{len(SK['edges'])} links, each weighted by what removing it costs"),
 (4,'chain',f"Alone every one of these {SK['n_free']} is free",
    f"take them away together and {SK['n_lost_together']} of the {SK['total']} claims leave the closure"),
 (5,'chain','The skeleton',
    f"{SK['n_skel']} dependencies, and every claim still reachable"),
 (6,'schem','Wish two','A claim in a gap the structure names',
    'a claim nobody has written yet'),
 (7,'schem','Wish three','A new paper inherits what is checked',
    'and only three of its claims are genuinely new'),
]
for h in HEADS:
    st, kind = h[0], h[1]
    if kind=='chain':
        txt(st,80,118,CHAINW,HS2,h[2])
        txt(st,80,172,CHAINW,SS,h[3],color=LIGHT)
    else:
        txt(st,150,110,SCHEMW,30,h[2],color=LIGHT)
        txt(st,150,152,SCHEMW,30,h[3])
        txt(st,150,200,SCHEMW,20,h[4],color=LIGHT)


METER=[
 'ONE THEOREM’S CHAIN · 29 CLAIMS, 46 DEPENDENCIES',
 'WISH ONE · MORE PAPERS, ONE NETWORK',
 'CUT ONE CLAIM OUT · COUNT WHAT LEAVES THE CLOSURE',
 '46 DEPENDENCIES · WEIGHTED BY WHAT REMOVING ONE COSTS',
 '29 FREE ON THEIR OWN · TOGETHER THEY COST 14 CLAIMS',
 'THE SKELETON · 28 DEPENDENCIES, NOTHING LOST',
 'WISH TWO · A CLAIM IN A GAP THE STRUCTURE NAMES',
 'WISH THREE · A NEW PAPER INHERITS WHAT IS ALREADY CHECKED',
]
OPENMETER=[False]*8

NOTE=[
"""The ending is three wishes with one measurement wedged in the middle, and I will keep saying which is which.

Start from the object the deck has been building: the closure of one theorem. Twenty-nine claims, forty-six dependencies, laid out exactly as in the chain frames - same positions, same shapes, same claims.""",

"""WISH ONE. Do this to the next paper, and the next.

The heavier lines between clusters are the point: the same claim, leaned on by two different papers. That is the moment a pile of decomposed papers becomes one network.

It is also the joint I said I cannot build. Deciding that this lemma and that lemma are the SAME lemma is an identity question, and v0.3 does not answer it. Schematic layout, no counts, nothing asserted.""",

"""NOT A WISH. Cut one claim out of the graph - remove every dependency into it - and recompute the backward closure of the theorem. Count what is no longer in it. Size and ink are that count.

Before trusting any of this: my computation reproduces all 46 of the omission experiments the pipeline recorded in closed-form-branch.json, edge for edge. The assertion is in gen_skeleton.py and the build fails if it ever stops matching. I am not showing you a model of the pipeline, I am showing you the pipeline's own arithmetic.

The graph program carries 25 of the 29. The distribution has a long thin tail and one spike, which is the shape that makes the rest of this worth attempting: you do not need taste to find the load-bearing parts, you need an omission test.""",

"""The same question asked of every dependency rather than every claim - and this one the pipeline already answered for itself, in all 46 cases.

Line weight is what removing that one edge costs. Most of the graph is thin.

The small chart is the whole distribution, sorted. It is deliberately small: the number on any one bar does not matter, the SHAPE does, and the shape is a cliff.""",

"""AND HERE IS THE TRAP, which I walked into while building this frame and think is the most useful thing on it.

Twenty-nine of the forty-six dependencies cost nothing when you remove them. Each one, on its own, is redundant - every claim is still reachable by some other route.

Take all twenty-nine away together and fourteen of the twenty-nine claims fall out of the closure.

Individual redundancy does not compose. Two edges can each be safe to cut because the other one is there. It is obvious once stated and it is extremely easy to miss - I had this frame drawn the wrong way round, asserting that the 29 could go and 17 would remain, before I checked it jointly.

That is precisely the kind of mistake a person makes reading a dependency structure by eye, and precisely the kind a machine does not.""",

"""So the skeleton has to be computed properly: remove one dependency, recheck the whole closure, and only then try the next. Greedily, to exhaustion.

Eighteen can go. TWENTY-EIGHT remain, and all twenty-nine claims are still reachable.

That is what I mean by the skeleton of a theory. Not a summary and not the important bits as judged by anybody - the subgraph you cannot cut any further without losing something, arrived at by an operation with no opinion in it.

Two honest caveats. It is a statement about the graph as recorded: if the extraction missed a route, an edge looks more necessary than it is. And 29 claims is small enough that a careful person could have done this by hand - slowly, and as the previous frame shows, probably wrongly.""",

"""WISH TWO. If you can compute where the load sits, you can also see where the structure is thin: a place where several load-bearing claims converge and nothing has been written.

The diamond is a claim nobody has stated, proposed because the shape of the network says something belongs there.

And the reason the junction is drawn exactly like every other junction in this deck: a proposed claim gets no special status. Same AND-junction, same premises, same arrow, same kernel. Accepted, it is knowledge. Refused, the system names what was missing and that becomes the next thing to read.""",

"""WISH THREE, and this is the one I would most like to be true.

Along the bottom: what has already been checked, and stays checked. A proof the kernel accepted does not need re-accepting next year.

Above: a new paper. Most of what it rests on is already down there - the same foundations, the same definitions, the same handful of load-bearing claims every paper in the area leans on. Those edges cost nothing new.

Only three things in it are actually new, and only those three need a junction and a check.

That is what the apparatus is FOR. Not to verify a paper - to make the NEXT paper cheap, by making verification something you inherit instead of something you repeat. Today, reading a paper properly means reconstructing its dependencies from scratch, every reader, every time. This is the version where you do not.

Then stop, and say the status: 29 claims, 14 reachable, accepted_support_edges 0, CHAIN_INCOMPLETE. Three wishes and one measurement.""",
]

F.dump(8, METER, OPENMETER, NOTE, 'pipe-svg', 'closing.svg', 'closing.json',
       cumulative=False)
