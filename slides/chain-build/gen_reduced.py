# -*- coding: utf-8 -*-
"""The reduced graph: the 240 extraction candidates cut down to those that land
inside a result the paper actually DECLARES.

The cut is mechanical - the host reads \\begin{theorem}...\\end{theorem} byte
ranges out of the frozen source and asks which candidate spans fall inside one.
No model judgement, nothing accepted, fully reversible: the other 226 are not
deleted, they are simply not attributed to a declared result.
"""
import re, json, collections, subprocess
from shapes import shape_markup

R='/Users/Yingjian/Documents/GitHub/AgtXIv/'
tex=open(R+'Stabilizerness/arXiv-2607.26154v1/draft.tex','rb').read().decode('utf8','replace')

ENV=('theorem','lemma','definition','proposition','corollary')
envs=[]
for e in ENV:
    for m in re.finditer(r'\\begin\{'+e+r'\*?\}', tex):
        end=re.search(r'\\end\{'+e+r'\*?\}', tex[m.start():])
        if not end: continue
        s=len(tex[:m.start()].encode()); t=len(tex[:m.start()+end.end()].encode())
        lab=re.search(r'\\label\{([^}]+)\}', tex[m.start():m.start()+end.end()])
        envs.append({'kind':e,'start':s,'end':t,'label':lab.group(1) if lab else None})
envs.sort(key=lambda x:x['start'])

g=json.load(open(R+'schema v0.3/runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json'))
attr={}
for n in g['nodes']:
    if not n.get('paper_id'): continue
    for sp in (n.get('source_spans') or []):
        if not sp.get('path','').endswith('draft.tex'): continue
        for k,e in enumerate(envs):
            if sp['byte_start'] < e['end'] and e['start'] < sp['byte_end']:
                attr[n['id']]=k; break
        if n['id'] in attr: break
EDGES=[(e['from'],e['to']) for e in g['edges'] if e['from'] in attr and e['to'] in attr]
byenv=collections.defaultdict(list)
for nid,k in attr.items(): byenv[k].append(nid)

KMARK={'theorem':'theorem','lemma':'lemma','definition':'definition',
       'proposition':'proposition','corollary':'theorem'}
W,H=1920,1040
X0,X1=300,1770
def ex(k): return X0 + k*(X1-X0)/(len(envs)-1)
YB=790          # the declared-result row
YC=330          # the evidence row

pos={}
for k,ids in byenv.items():
    ids.sort()
    for i,nid in enumerate(ids):
        pos[nid]=(ex(k)+(i-(len(ids)-1)/2)*46, YC)

# The figure carries its OWN stylesheet. It used to rely on a <style> block
# that lived beside it in the page, which meant re-inlining the figure silently
# dropped every rule - filled black blobs where the curves should be. A figure
# that only renders correctly next to something else is not a figure.
STYLE = ('.envmark{fill:#fff;stroke:#1A1A16;stroke-width:2.6}'
 '.envlab{font-family:Calibri,Carlito,sans-serif;font-size:21px;fill:#1A1A16}'
 '.envkind{font-family:Calibri,Carlito,sans-serif;font-size:17px;fill:#8A8A80}'
 '.cmark{fill:#fff;stroke:#1A1A16;stroke-width:2}'
 '.rd-attr path{fill:none;stroke:#8A8A80;stroke-width:1.2;opacity:.5;stroke-dasharray:4 3}'
 '.rd-edges path{fill:none;stroke:#1A1A16;stroke-width:1.8;opacity:.55}'
 '.rdrow{font-family:Calibri,Carlito,sans-serif;font-size:20px;fill:#8A8A80;letter-spacing:.08em}')

o=[f'<svg class="red-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img"'
   f' aria-label="The reduced graph: 14 of 240 extraction candidates land inside the 9 results the paper declares.">',
   f'  <style>{STYLE}</style>']

# the declared results, as the paper wrote them
o.append('  <g class="rd-env">')
for k,e in enumerate(envs):
    x=ex(k)
    o.append(f'    {shape_markup(KMARK[e["kind"]], x, YB, 26, cls="envmark")}')
    dy = 56 if k % 2 == 0 else 118   # stagger: nine labels do not fit on one line
    o.append(f'    <text class="envlab" x="{x}" y="{YB+dy}" text-anchor="middle">{e["label"] or e["kind"]}</text>')
    o.append(f'    <text class="envkind" x="{x}" y="{YB+dy+24}" text-anchor="middle">{e["kind"]}</text>')
o.append('  </g>')

# attribution: candidate -> the declared result it lands in
o.append('  <g class="rd-attr">')
for nid,k in attr.items():
    x,y=pos[nid]
    o.append(f'    <path d="M {x:.1f} {y:.1f} C {x:.1f} {(y+YB)/2:.1f}, {ex(k):.1f} {(y+YB)/2:.1f}, {ex(k):.1f} {YB-30:.1f}"/>')
o.append('  </g>')

# dependencies that survive the cut
o.append('  <g class="rd-edges">')
for a,b in EDGES:
    x1,y1=pos[a]; x2,y2=pos[b]; m=min(y1,y2)-120
    o.append(f'    <path d="M {x1:.1f} {y1:.1f} C {x1:.1f} {m:.1f}, {x2:.1f} {m:.1f}, {x2:.1f} {y2:.1f}"/>')
o.append('  </g>')

o.append('  <g class="rd-cands">')
for nid,k in attr.items():
    x,y=pos[nid]
    o.append(f'    <g class="rd-c"><circle class="cmark" cx="{x:.1f}" cy="{y:.1f}" r="11"/></g>')
o.append('  </g>')
# the captions sit clear of the drawing: the dependency arcs rise to YC-120 and
# the attribution lines fill everything between the two rows, so a caption set
# beside either row is a caption with lines drawn through it.
CAP_A, CAP_B = 150, 968
o.append(f'  <text class="rdrow" x="70" y="{CAP_A}">14 candidates that land inside a declared result</text>')
o.append(f'  <text class="rdrow" x="70" y="{CAP_B}">the 9 results the paper actually declares</text>')
o.append('</svg>')
open('reduced.svg','w').write('\n'.join(o))
subprocess.run(['rsvg-convert','-w','3000','-b','white','reduced.svg','-o','frames/reduced.png'],check=True)

print('declared environments :', len(envs))
print('candidates attributed :', len(attr), 'of 240')
print('edges surviving       :', len(EDGES))
print('environments hit      :', len(byenv), 'of', len(envs))
json.dump({'envs':envs,'attr':attr,'edges':EDGES}, open('reduced-meta.json','w'))

# ---- geometry export for the native-pptx renderer -------------------------
import math as _m
from shapes import _poly, _norm
_SIDES={'definition':None,'lemma':(4,45),'proposition':(3,-90),'theorem':(4,-90)}
_PRESET={'definition':'ellipse','lemma':'rect','proposition':'triangle','theorem':'diamond'}
def _bbox(kind,cx,cy,r):
    sp=_SIDES.get(kind)
    if sp is None: return (cx-r,cy-r,2*r,2*r)
    n,rot=sp; rr=_norm(r,n)
    pts=[tuple(map(float,p.split(','))) for p in _poly(cx,cy,rr,n,rot).split()]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return (min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys))

G={'envs':[],'cands':[],'attr':[],'edges':[],'rows':[
    {'x':70,'y':CAP_A,'t':'14 candidates that land inside a declared result  (one mark each, kind not shown)'},
    {'x':70,'y':CAP_B,'t':'the 9 results the paper actually declares'}]}
for k,e in enumerate(envs):
    x=ex(k); bx,by,bw,bh=_bbox(e['kind'],x,YB,26)
    dy = 56 if k%2==0 else 118
    G['envs'].append({'x':bx,'y':by,'w':bw,'h':bh,'cx':x,'cy':YB,
        'preset':_PRESET[e['kind']],'lab':e['label'] or e['kind'],'kind':e['kind'],'dy':dy})
for nid,k in attr.items():
    x,y=pos[nid]
    G['cands'].append({'cx':x,'cy':y,'r':11})
    G['attr'].append({'x1':x,'y1':y,'x2':ex(k),'y2':YB-30,'ym':(y+YB)/2})
for a,b in EDGES:
    x1,y1=pos[a]; x2,y2=pos[b]
    G['edges'].append({'x1':x1,'y1':y1,'x2':x2,'y2':y2,'ym':min(y1,y2)-120})
json.dump(G, open('reduced-geom.json','w'))
print('geometry export:', len(G['envs']),'declared,',len(G['cands']),'candidates,',len(G['edges']),'edges')
