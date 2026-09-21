# -*- coding: utf-8 -*-
"""Build the construction of ONE theorem's chain, step by step.

The unit of construction is not an edge, it is a SUPPORT GROUP: an AND-set of
premises that together discharge one target. The figure draws each group as a
bracket, so "all of these, together" is visible rather than implied.
"""
import json, collections, math
from shapes import shape_markup

# COLOUR = WHICH PAPER THIS CAME FROM. Lifted unchanged from the seminar deck
# (2026-09-22-talk.html, slides 25-30 and 33) so the two decks finally encode
# provenance the same way. Hollow ink = this paper. A hue = a named source.
# This replaces the old one-bit warm/ink split with the six values it was
# standing in for.
INKC='#1A1A16'
SRC={'root:perfect-graph-weighted-duality': ('chvatal',   '#2a78d6'),
     'root:gottesman-stabilizer-formalism': ('gottesman', '#1baf7a'),
     'root:veitch-stabilizer-resource-theory':('veitch',  '#eda100'),
     'root:howard-campbell-rom':            ('howard',    '#e87ba4'),
     'foundation:finite-lp-strong-duality': ('handbook',  '#008300'),
     'root:varela-reduced-polytope':        ('varela',    '#4a3aa7')}

V3='/Users/Yingjian/Documents/GitHub/AgtXIv/schema v0.3/runs/2607-full-candidate-20260919/'
OLD='/Users/Yingjian/Documents/GitHub/AgtXIv/schema v0.2/host_probe/evidence/closure.json'
d=json.load(open(V3+'closed-form-branch.json'))
old={n['id']:n for n in json.load(open(OLD))['nodes']}
nodes={n['id']:n for n in d['nodes']}
groups=d['support_groups']; FO=set(d['formalization_order'])
bytarget=collections.defaultdict(list)
for g in groups: bytarget[g['target']].append(g)
ROOTS=[i for i in nodes if i not in bytarget]

# --- expansion waves: open the theorem's group, then its members' groups ---
TH='claim:closed-form-rom'
wave={TH:0}; frontier=[TH]; w=0
gwave={}                       # support group -> the step at which it opens
while frontier:
    w+=1; nxt=[]
    for t in frontier:
        for g in bytarget.get(t,[]):
            gwave[g['id']]=w
            for m in g['members']:
                if m not in wave: wave[m]=w; nxt.append(m)
    frontier=nxt
MAXW=max(wave.values())

# --- layout: reuse the deck's branch columns and layers, so the picture is
#     the same object the audience already learned to read -----------------
BRX={'conceptual_foundation':215,'reduced_polytope':560,'relaxation':905,
     'optimization':1255,'graph_theory':1610,'closed_form':905}
LAY=9; TOP,BOT=95,905
def ly(L): return BOT-L*((BOT-TOP)/(LAY-1))
buck=collections.defaultdict(list)
for i,n in nodes.items(): buck[(old[i]['layer'], old[i]['branch'])].append(i)
pos={}
for (L,b),ns in buck.items():
    ns.sort()
    for k,i in enumerate(ns): pos[i]=(BRX[b]+(k-(len(ns)-1)/2)*94, ly(L))
nbr=collections.defaultdict(list)
for g in groups:
    for m in g['members']: nbr[m].append(g['target']); nbr[g['target']].append(m)
for _ in range(6):
    for (L,b),ns in buck.items():
        if len(ns)<2: continue
        ns.sort(key=lambda i: sum(pos[x][0] for x in nbr[i] if x in pos)/max(1,len([x for x in nbr[i] if x in pos])) if any(x in pos for x in nbr[i]) else pos[i][0])
        for k,i in enumerate(ns): pos[i]=(BRX[b]+(k-(len(ns)-1)/2)*94, ly(L))

W,H=1920,1040  # the figure now fills the stage; right margin keeps labels unclipped
o=[f'<svg class="chain-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img"'
   f' aria-label="Construction of one theorem\'s dependency chain: 20 support groups over 29 claims,'
   f' each group meeting at an AND junction that points at the claim it discharges.">',
   '  <defs><marker id="dep" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5"'
   ' markerHeight="6.5" orient="auto-start-reverse">'
   '<path d="M 0 0 L 10 5 L 0 10 z" fill="#1A1A16"/></marker></defs>']
# ---- the key. Colour is only information if the room can read it, and the
#      seminar deck puts this same row under its own dependency figures.
LEGEND=[('this paper',None),('Chv\u00e1tal 1970s','#2a78d6'),('Gottesman 1997','#1baf7a'),
        ('Veitch 2013','#eda100'),('Howard 2016','#e87ba4'),
        ('Handbook 2024','#008300'),('Varela 2026','#4a3aa7')]
o.append('  <g class="ch-key">')
o.append('    <text class="ch-keyhead" x="118" y="34">COLOUR = SOURCE</text>')
_x=118+236
for _t,_c in LEGEND:
    _f=_c or '#FFFFFF'
    o.append(f'    <circle class="ch-sw" cx="{_x+7}" cy="28" r="7" fill="{_f}"'
             f' stroke="{_c or INKC}"/>')
    o.append(f'    <text class="ch-keyt" x="{_x+22}" y="34">{_t}</text>')
    _x += 22 + len(_t)*8.6 + 26
o.append('  </g>')

o.append('  <g class="ch-guides">')
for L in range(LAY):
    y=ly(L); o.append(f'    <line x1="118" y1="{y:.1f}" x2="{W-46}" y2="{y:.1f}"/>')
    o.append(f'    <text class="ch-lay" x="102" y="{y+6:.1f}" text-anchor="end">L{L}</text>')
o.append('  </g>')

# --- support groups -------------------------------------------------------
# A group is an AND: all of its members together discharge one target. Drawn as
# legs rising to a collector bar, a JUNCTION where they meet, and ONE arrow out
# of the junction into the claim it discharges - so the arrow means "therefore"
# and the junction means "all of these, jointly". The solid dots mark exactly
# which nodes are members, which a bar alone cannot say: the bar has to reach
# the junction, so it passes over nodes that are not in the group.
# In this chain every target has exactly one group, so there is no OR here.
JR=11; BAROFF=50

o.append('  <g class="ch-groups">')
for g in groups:
    t=g['target']; ms=[m for m in g['members'] if m in pos]
    if t not in pos or not ms: continue
    tx,ty=pos[t]; gw=gwave.get(g['id'],99)
    bar=ty+BAROFF                      # the junction sits just under its target
    tr=24 if t==TH else (20 if t in ROOTS else 15)
    o.append(f'    <g class="ch-grp" data-wave="{gw}" data-gid="{g['id']}"'
             f' data-members="{" ".join(ms)}">')
    # One curve per member, running into the junction. Same bezier the seminar
    # deck uses - vertical control points at the midpoint - which is why the
    # curves separate on their own and need no collision routing.
    for m in ms:
        mx,my=pos[m]
        ym=(my+bar)/2
        src=SRC.get(m)
        cls='gcurve' + (f' from-{src[0]}' if src else ' from-this-paper')
        o.append(f'      <path class="{cls}" d="M {mx:.1f} {my:.1f} '
                 f'C {mx:.1f} {ym:.1f}, {tx:.1f} {ym:.1f}, {tx:.1f} {bar:.1f}"/>')
    o.append(f'      <circle class="gjunc" cx="{tx:.1f}" cy="{bar:.1f}" r="{JR}"/>')
    o.append(f'      <line class="gplus" x1="{tx-6:.1f}" y1="{bar:.1f}" x2="{tx+6:.1f}" y2="{bar:.1f}"/>')
    o.append(f'      <line class="gplus" x1="{tx:.1f}" y1="{bar-6:.1f}" x2="{tx:.1f}" y2="{bar+6:.1f}"/>')
    o.append(f'      <line class="gstem" x1="{tx:.1f}" y1="{bar-JR:.1f}" x2="{tx:.1f}"'
             f' y2="{ty+tr+3:.1f}" marker-end="url(#dep)"/>')
    o.append('    </g>')
o.append('  </g>')

# --- nodes ---------------------------------------------------------------
o.append('  <g class="ch-nodes">')
for i,n in nodes.items():
    x,y=pos[i]; k=n['kind']
    cls=f'ch-node k-{k.replace("_","-")}'
    # provenance, straight off the id prefix: root:/foundation: are the imports.
    # Warm means exactly one thing across all 15 frames - NOT FROM THIS PAPER -
    # so the roots frame must not paint the paper's own definitions warm.
    if i.startswith(('root:','foundation:')): cls+=' is-import'
    src=SRC.get(i)
    cls += f' src-{src[0]}' if src else ' src-this-paper'
    if i in ROOTS: cls+=' is-root'
    if i in FO: cls+=' is-form'
    if i==TH: cls+=' is-theorem'
    r=24 if i==TH else (20 if i in ROOTS else 15)
    style=f' style="--src:{src[1]}"' if src else ''
    sa  = f' stroke="{src[1]}"' if src else ''
    o.append(f'    <g class="{cls}" data-wave="{wave.get(i,99)}" data-id="{i}"{style}>')
    o.append(f'      <circle class="nring" cx="{x:.1f}" cy="{y:.1f}" r="{r+9}"{sa}/>')
    o.append(f'      {shape_markup(k,x,y,r,cls="nmark").replace("/>", sa + "/>")}')
    o.append('    </g>')
o.append('  </g>')

LAB={TH:('the theorem',0,-44,'middle'),
     'root:perfect-graph-weighted-duality':('perfect-graph duality',-40,8,'end'),
     'root:varela-reduced-polytope':('Varela',-40,8,'end'),
     'root:gottesman-stabilizer-formalism':('Gottesman',0,58,'middle'),
     'claim:mwis-definition':('MWIS',40,8,'start'),
     'claim:perfect-graph-definition':('perfect graph',40,8,'start')}
o.append('  <g class="ch-labels">')
for i,(t,dx,dy,an) in LAB.items():
    if i not in pos: continue
    x,y=pos[i]
    o.append(f'    <text class="ch-lab" data-wave="{wave.get(i,99)}" x="{x+dx:.1f}" y="{y+dy:.1f}" text-anchor="{an}">{t}</text>')
o.append('  </g></svg>')
open('chain.svg','w').write('\n'.join(o))

print('nodes',len(nodes),'| support groups',len(groups),'| roots',len(ROOTS))
print('expansion waves:',MAXW,'| per wave:',[sum(1 for v in wave.values() if v==i) for i in range(MAXW+1)])
print('groups per wave:',[sum(1 for v in gwave.values() if v==i) for i in range(1,MAXW+1)])
print('formalizable',len(FO),'of',len(nodes))
json.dump({'wave':wave,'gwave':gwave,'roots':ROOTS,'fo':sorted(FO),'maxw':MAXW},
          open('chain-meta.json','w'), indent=1)

# ---------------------------------------------------------------------------
# GEOMETRY EXPORT - so the pptx can draw the same figure as native PowerPoint
# shapes instead of a flattened image. One source, two renderers; if the layout
# above changes, the slide changes with it.
# ---------------------------------------------------------------------------
import math as _m
from shapes import _poly, _norm

_SIDES={'definition':None,'lemma':(4,45),'proposition':(3,-90),'theorem':(4,-90),
        'external_contract':(6,-90),'standard_foundation':(6,-90)}
_PRESET={'definition':'ellipse','lemma':'rect','proposition':'triangle',
         'theorem':'diamond','external_contract':'hexagon','standard_foundation':'hexagon'}

def _bbox(kind,cx,cy,r):
    """Bounding box of the SVG polygon, so the PowerPoint preset lands centred
    on exactly the same point with exactly the same visual area."""
    sp=_SIDES.get(kind)
    if sp is None: return (cx-r,cy-r,2*r,2*r)
    n,rot=sp; rr=_norm(r,n)
    pts=[tuple(map(float,p.split(','))) for p in _poly(cx,cy,rr,n,rot).split()]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return (min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys))

GEOM={'nodes':[],'groups':[],'guides':[],'labels':[],'maxw':MAXW,
      'key':{'head':'COLOUR = SOURCE','x':118,'y':34,'items':[]}}
_kx=118+236
for _t,_c in LEGEND:
    GEOM['key']['items'].append({'t':_t,'c':_c,'x':_kx})
    _kx += 22 + len(_t)*8.6 + 26
for L in range(LAY):
    GEOM['guides'].append({'y':ly(L),'x1':118,'x2':W-46,'lab':f'L{L}'})
for i,n in nodes.items():
    x,y=pos[i]; k=n['kind']; r=24 if i==TH else (20 if i in ROOTS else 15)
    bx,by,bw,bh=_bbox(k,x,y,r)
    GEOM['nodes'].append({'id':i,'x':bx,'y':by,'w':bw,'h':bh,'cx':x,'cy':y,'r':r,
        'preset':_PRESET.get(k,'ellipse'),'kind':k,'wave':wave.get(i,99),
        'root':i in ROOTS,'imp':i.startswith(('root:','foundation:')),
        'src':(SRC[i][1] if i in SRC else None),
        'form':i in FO,'th':i==TH})
for g in groups:
    t=g['target']; ms=[m for m in g['members'] if m in pos]
    if t not in pos or not ms: continue
    tx,ty=pos[t]
    tr=24 if t==TH else (20 if t in ROOTS else 15)
    bar=ty+BAROFF
    GEOM['groups'].append({'wave':gwave.get(g['id'],99),'tx':tx,'ty':ty,'bar':bar,
        'legs':[[pos[m][0],pos[m][1],(SRC[m][1] if m in SRC else None)] for m in ms],
        'n':len(ms),'tr':tr,'jr':JR})
for i,(t,dx,dy,an) in LAB.items():
    if i not in pos: continue
    x,y=pos[i]
    GEOM['labels'].append({'t':t,'x':x+dx,'y':y+dy,'an':an,'wave':wave.get(i,99)})
json.dump(GEOM, open('chain-geom.json','w'))
print('geometry export:', len(GEOM['nodes']),'nodes,',len(GEOM['groups']),'brackets,',
      len(GEOM['labels']),'labels')
