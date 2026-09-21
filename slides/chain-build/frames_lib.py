# -*- coding: utf-8 -*-
"""Shared drawing primitives for the deck's hand-built figures.

ONE SOURCE, TWO RENDERERS. A figure declares a flat list of primitives tagged
with the build step they arrive at; this module writes the inline SVG the page
uses, and deck.js reads the same list to emit native PowerPoint shapes. Nothing
is an image, so every element on the finished slide stays editable - and the
page and the slide cannot drift, because neither is drawn by hand.

Stage is 1920x1080 px = 13.333 x 7.5 in, so px/144 = inches and px/2 = points.
Type is Calibri throughout, in the page and in the slide. Calibri is
proportional, so the width guard below uses a deliberately pessimistic 0.55em
average advance - it over-estimates, which means it can complain about a line
that would actually fit, and never the other way round. SPACE_EM is the real
space width, used to turn a listing's leading spaces into an x offset, because
PowerPoint collapses leading whitespace inside a run.
"""
import json

FONT='Calibri'
FONT_CSS="Calibri,Carlito,sans-serif"
ADV_EM=0.55          # pessimistic average advance, for the overflow guard
SPACE_EM=0.2256      # Calibri's actual space width
from shapes import shape_markup, _poly, _norm

# node kind -> its SVG polygon, and the PowerPoint preset that matches it.
# Shape carries KIND in this deck; a diamond is a theorem wherever it appears,
# so the motivation frames can use the same vocabulary without inventing one.
_SIDES={'definition':None,'lemma':(4,45),'proposition':(3,-90),'theorem':(4,-90),
        'external_contract':(6,-90),'standard_foundation':(6,-90)}
_PRESET={'definition':'ellipse','lemma':'rect','proposition':'triangle',
         'theorem':'diamond','external_contract':'hexagon','standard_foundation':'hexagon'}

INK='#1A1A16'; LIGHT='#8A8A80'; OPEN='#8C4A2F'; PAPER='#fff'

class Fig:
    def __init__(self, name, label):
        self.name=name; self.label=label; self.P=[]

    # ---- primitives ----------------------------------------------------
    def box(self,step,x,y,w,h,style='solid',color=INK,lw=2.0,fill=None):
        self.P.append(dict(t='box',step=step,x=x,y=y,w=w,h=h,style=style,
                           color=color,lw=lw,fill=fill)); return self.P[-1]
    def txt(self,step,x,y,w,s,text,color=INK,align='l',bold=False,italic=False,h=None):
        self.P.append(dict(t='text',step=step,x=x,y=y,w=w,h=h or s*1.45,size=s,
                           text=text,color=color,align=align,bold=bold,italic=italic))
        return self.P[-1]
    def line(self,step,x1,y1,x2,y2,color=INK,lw=2.0,style='solid',arrow=False):
        self.P.append(dict(t='line',step=step,x1=x1,y1=y1,x2=x2,y2=y2,color=color,
                           lw=lw,style=style,arrow=arrow)); return self.P[-1]
    def mark(self,step,kind,cx,cy,r,color=INK,lw=2.0,fill=None):
        """A node-kind mark, area-normalised exactly as the chain figures draw
        it, carrying both its SVG polygon and the bounding box PowerPoint needs
        to land the matching preset on the same centre."""
        sp=_SIDES.get(kind)
        if sp is None:
            bx,by,bw,bh = cx-r, cy-r, 2*r, 2*r
        else:
            n,rot=sp; rr=_norm(r,n)
            pts=[tuple(map(float,p.split(','))) for p in _poly(cx,cy,rr,n,rot).split()]
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            bx,by,bw,bh = min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)
        self.P.append(dict(t='mark',step=step,kind=kind,cx=cx,cy=cy,r=r,
                           x=bx,y=by,w=bw,h=bh,preset=_PRESET.get(kind,'ellipse'),
                           color=color,lw=lw,fill=fill,
                           svg=shape_markup(kind,cx,cy,r)))
        return self.P[-1]

    def curve(self,step,x1,y1,c1x,c1y,c2x,c2y,x2,y2,color=INK,lw=1.3):
        """One cubic bezier, as one element in both renderers. Drawing these as
        sixteen-segment polylines put 780 shapes on a slide."""
        self.P.append(dict(t='curve',step=step,x1=x1,y1=y1,c1x=c1x,c1y=c1y,
                           c2x=c2x,c2y=c2y,x2=x2,y2=y2,color=color,lw=lw))
        return self.P[-1]

    def dot(self,step,cx,cy,r,color=INK,lw=2.0,fill=None,dim=False):
        self.P.append(dict(t='dot',step=step,cx=cx,cy=cy,r=r,color=color,lw=lw,
                           fill=fill,dim=dim)); return self.P[-1]

    # ---- guards --------------------------------------------------------
    def check(self, bottom=1000, right=1880):
        """Nothing may overflow its own box, and nothing may sit where the
        meter line goes. A figure that clips is a figure the room cannot read."""
        bad=[p for p in self.P if p['t']=='text' and len(p['text'])*p['size']*ADV_EM > p['w']+0.5]
        assert not bad, f'{self.name}: text overflows its box: ' + repr([(p['text'],p['w']) for p in bad])
        out=[p for p in self.P if p['t']=='box' and
             (p['x']<40 or p['x']+p['w']>right or p['y']+p['h']>bottom)]
        assert not out, f'{self.name}: box outside the safe area: ' + repr(out)
        low=[p for p in self.P if p['t']=='text' and p['y']+p['size'] > bottom]
        assert not low, f'{self.name}: text runs into the meter line: ' + repr([p['text'] for p in low])

    # ---- render: the inline SVG for the page ---------------------------
    def svg(self, nsteps, cls, H=1080, cumulative=True):
        def dash(p): return ' stroke-dasharray="9 7"' if p.get('style')=='dash' else ''
        # cumulative: each step ADDS to the picture (the pipeline builds one box
        # at a time). Otherwise each step IS a picture (the motivation frames are
        # six separate arguments, not one drawing).
        o=[f'<svg class="{cls}" data-cum="{1 if cumulative else 0}" viewBox="0 0 1920 {H}"'
           f' xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{self.label}">',
           '<defs>'
           f'<marker id="{self.name}ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"'
           f' markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z"'
           f' fill="{INK}"/></marker>'
           f'<marker id="{self.name}aw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"'
           f' markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z"'
           f' fill="{OPEN}"/></marker>'
           '</defs>']
        for st in range(nsteps):
            o.append(f'  <g class="pp-g" data-step="{st}">')
            for p in self.P:
                if p['step']!=st: continue
                if p['t']=='box':
                    f=f' fill="{p["fill"]}"' if p.get('fill') else ' fill="none"'
                    o.append(f'    <rect x="{p["x"]:.1f}" y="{p["y"]:.1f}" width="{p["w"]:.1f}"'
                             f' height="{p["h"]:.1f}"{f} stroke="{p["color"]}"'
                             f' stroke-width="{p["lw"]}"{dash(p)}/>')
                elif p['t']=='line':
                    a=(f' marker-end="url(#{self.name}aw)"' if p['color']==OPEN
                       else f' marker-end="url(#{self.name}ah)"') if p['arrow'] else ''
                    op=' opacity=".13"' if p.get('dim') else ''
                    o.append(f'    <line x1="{p["x1"]:.1f}" y1="{p["y1"]:.1f}" x2="{p["x2"]:.1f}"'
                             f' y2="{p["y2"]:.1f}" stroke="{p["color"]}" stroke-width="{p["lw"]}"'
                             f'{dash(p)}{a}{op}/>')
                elif p['t']=='curve':
                    o.append(f'    <path d="M {p["x1"]:.1f} {p["y1"]:.1f} '
                             f'C {p["c1x"]:.1f} {p["c1y"]:.1f}, {p["c2x"]:.1f} {p["c2y"]:.1f}, '
                             f'{p["x2"]:.1f} {p["y2"]:.1f}" fill="none" '
                             f'stroke="{p["color"]}" stroke-width="{p["lw"]}"/>')
                elif p['t']=='mark':
                    o.append('    '+p['svg'].replace('/>',
                        f' fill="{p.get("fill") or "#fff"}" stroke="{p["color"]}"'
                        f' stroke-width="{p["lw"]}"/>'))
                elif p['t']=='dot':
                    op=' opacity=".13"' if p.get('dim') else ''
                    fl=p.get('fill') or '#fff'
                    o.append(f'    <circle cx="{p["cx"]:.1f}" cy="{p["cy"]:.1f}" r="{p["r"]:.1f}"'
                             f' fill="{fl}" stroke="{p["color"]}" stroke-width="{p["lw"]}"{op}/>')
                else:
                    anc={'l':'start','c':'middle'}[p['align']]
                    x=p['x'] if p['align']=='l' else p['x']+p['w']/2
                    w=' font-weight="700"' if p.get('bold') else ''
                    o.append(f'    <text x="{x:.1f}" y="{p["y"]+p["size"]*0.84:.1f}"'
                             f' text-anchor="{anc}" font-size="{p["size"]}" fill="{p["color"]}"'
                             f'{w} class="pp-t">{p["text"]}</text>')
            o.append('  </g>')
        o.append('</svg>')
        return '\n'.join(o)

    def dump(self, nsteps, meter, openmeter, note, cls, svg_path, json_path,
             H=1080, cumulative=True):
        assert len(meter)==nsteps and len(openmeter)==nsteps and len(note)==nsteps, \
            f'{self.name}: {nsteps} steps but {len(meter)}/{len(openmeter)}/{len(note)} copy entries'
        self.check(bottom=H-80)
        open(svg_path,'w').write(self.svg(nsteps, cls, H, cumulative))
        json.dump({'prims':self.P,'meter':meter,'open':openmeter,'note':note,
                   'cumulative':cumulative}, open(json_path,'w'), indent=1)
        print(f'{self.name}: {len(self.P)} primitives over {nsteps} steps')
        for st in range(nsteps):
            print(f'  step {st}: {sum(1 for p in self.P if p["step"]==st):>3} new elements'
                  f'  |  {meter[st]}')
