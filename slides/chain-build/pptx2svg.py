# -*- coding: utf-8 -*-
"""Convert Slide_001.pptx to SVG frames, faithfully.

Not a redraw and not a summary: every shape, every run of text and every
picture on all 27 source slides, at its own position, in its own colour. The
earlier attempt rebuilt the deck in this project's monochrome vocabulary and
lost content doing it - the published figures on slides 25-27, the sessions on
19-23, the transformer diagram. This reads the OOXML instead.

Geometry: the source is 13.333 x 7.5in = 12192000 x 6858000 EMU, and this deck's
stage is 1920 x 1080 px, so px = EMU * 1920/12192000 exactly. Type is in
hundredths of a point, and 1pt maps to 2px at this scale.

Pictures are re-encoded at twice their displayed size, which is what takes the
media from 8.7 MB to something a browser will open.
"""
import re, os, io, json, base64, zipfile, subprocess, sys
from xml.etree import ElementTree as ET

SRC='Slide_001.pptx'; OUT='front-media'
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
EMU=1920/12192000.0
# what a highlighted run becomes. EMPH is #C00000 because the source deck
# already uses exactly that red for emphasis on nine other runs - this
# introduces no new colour, it reuses the author's own.
EMPH='#C00000'
BODY={'#242832','#1A1A16','#000000'}

def px(v): return float(v)*EMU

z=zipfile.ZipFile(SRC)
os.makedirs(OUT, exist_ok=True)

def rels(slide):
    p=f'ppt/slides/_rels/slide{slide}.xml.rels'
    d={}
    for m in re.finditer(r'Id="([^"]+)"[^>]*Target="([^"]+)"', z.read(p).decode('utf8')):
        d[m.group(1)]=m.group(2).replace('../','ppt/')
    return d

# ---- pictures: decode once, downscale to 2x their largest use --------------
from PIL import Image
USE={}
def note_use(tgt,w,h):
    a=USE.get(tgt,(0,0)); USE[tgt]=(max(a[0],w),max(a[1],h))

def emit_media():
    out={}
    for tgt,(w,h) in USE.items():
        name=os.path.basename(tgt)
        raw=z.read(tgt)
        if name.lower().endswith('.svg'):
            out[tgt]=('image/svg+xml', raw); continue
        im=Image.open(io.BytesIO(raw))
        tw,th=max(8,int(w*2)),max(8,int(h*2))
        if im.width>tw or im.height>th:
            im.thumbnail((tw,th), Image.LANCZOS)
        buf=io.BytesIO()
        if im.mode in ('RGBA','LA','P') and 'transparency' in im.info or im.mode=='RGBA':
            im.convert('RGBA').save(buf,'PNG',optimize=True); mt='image/png'
        else:
            im.convert('RGB').save(buf,'JPEG',quality=82,optimize=True); mt='image/jpeg'
        out[tgt]=(mt, buf.getvalue())
    return out

def esc(s): return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

def _to_hsl(r,g,b):
    r,g,b=r/255,g/255,b/255; mx,mn=max(r,g,b),min(r,g,b); l=(mx+mn)/2
    if mx==mn: return 0.0,0.0,l
    d=mx-mn; sat=d/(2-mx-mn) if l>0.5 else d/(mx+mn)
    h={mx:0}.get(None,0)
    h=((g-b)/d+(6 if g<b else 0)) if mx==r else ((b-r)/d+2 if mx==g else (r-g)/d+4)
    return h/6, sat, l

def _to_rgb(h,s,l):
    def f(p,q,t):
        t%=1
        if t<1/6: return p+(q-p)*6*t
        if t<1/2: return q
        if t<2/3: return p+(q-p)*(2/3-t)*6
        return p
    if s==0: v=int(round(l*255)); return v,v,v
    q=l*(1+s) if l<0.5 else l+s-l*s; p=2*l-q
    return tuple(int(round(max(0,min(1,f(p,q,h+o)))*255)) for o in (1/3,0,-1/3))

def _mods(hexcol, el):
    """OOXML colour transforms. Without these a shape filled with accent1 at
    lumMod 40% / lumOff 60% - PowerPoint's "Lighter 60%" - came out as solid
    accent1, which is why the context window's three blocks rendered as one
    unbroken bar. shade and tint are applied in RGB, which is an approximation
    PowerPoint does in linear space; lumMod/lumOff are exact."""
    r,g,b=(int(hexcol[i:i+2],16) for i in (1,3,5))
    h,sa,l=_to_hsl(r,g,b)
    for ch in el:
        tag=ch.tag.split('}')[-1]; v=ch.get('val')
        if v is None: continue
        f=int(v)/100000.0
        if   tag=='lumMod': l*=f
        elif tag=='lumOff': l+=f
        elif tag=='satMod': sa*=f
        elif tag=='shade':  r,g,b=_to_rgb(h,sa,l); r,g,b=(int(round(c*f)) for c in (r,g,b)); h,sa,l=_to_hsl(r,g,b)
        elif tag=='tint':   r,g,b=_to_rgb(h,sa,l); r,g,b=(int(round(c*f+255*(1-f))) for c in (r,g,b)); h,sa,l=_to_hsl(r,g,b)
    l=max(0.0,min(1.0,l)); sa=max(0.0,min(1.0,sa))
    return '#%02X%02X%02X' % _to_rgb(h,sa,l)

def solid(el):
    if el is None: return None
    f=el.find('a:solidFill/a:srgbClr', NS)
    if f is not None: return _mods('#'+f.get('val'), f)
    sc=el.find('a:solidFill/a:schemeClr', NS)
    if sc is not None:
        base={'bg1':'#FFFFFF','lt1':'#FFFFFF','tx1':'#000000','dk1':'#000000',
              'bg2':'#EEEEEE','lt2':'#EEEEEE','tx2':'#333333','dk2':'#333333',
              'accent1':'#4472C4','accent2':'#ED7D31','accent3':'#A5A5A5',
              'accent4':'#FFC000','accent5':'#5B9BD5','accent6':'#70AD47'
             }.get(sc.get('val'),'#666666')
        return _mods(base, sc)
    return None

def xfrm_of(sp):
    x=sp.find('.//a:xfrm', NS)
    if x is None: return None
    o=x.find('a:off',NS); e=x.find('a:ext',NS)
    if o is None or e is None: return None
    return (px(o.get('x')),px(o.get('y')),px(e.get('cx')),px(e.get('cy')),
            int(x.get('rot','0'))/60000.0, x.get('flipH')=='1', x.get('flipV')=='1')

def walk(node, out, xf=(0,0,1,1), depth=0):
    """xf maps child space to slide space: (dx,dy,sx,sy)."""
    dx,dy,sx,sy = xf
    for el in node:
        tag=el.tag.split('}')[1]
        if tag=='grpSp':
            g=el.find('p:grpSpPr/a:xfrm', NS)
            nxf=xf
            if g is not None:
                o=g.find('a:off',NS); e=g.find('a:ext',NS)
                co=g.find('a:chOff',NS); ce=g.find('a:chExt',NS)
                if None not in (o,e,co,ce):
                    gx,gy=px(o.get('x')),px(o.get('y'))
                    gw,gh=px(e.get('cx')),px(e.get('cy'))
                    cw,chh=float(ce.get('cx')),float(ce.get('cy'))
                    ssx=gw/(cw*EMU) if cw else 1; ssy=gh/(chh*EMU) if chh else 1
                    nxf=(dx+gx-px(co.get('x'))*ssx*sx, dy+gy-px(co.get('y'))*ssy*sy,
                         sx*ssx, sy*ssy)
            walk(el.find('p:grpSpPr',NS) is not None and el or el, out, nxf, depth+1)
            continue
        if tag in ('sp','pic','cxnSp'):
            out.append((tag, el, xf))
    return out

def collect(sp_tree):
    items=[]
    def rec(node, xf):
        for el in node:
            tag=el.tag.split('}')[1]
            if tag=='grpSp':
                g=el.find('p:grpSpPr/a:xfrm', NS); nxf=xf
                if g is not None:
                    o=g.find('a:off',NS); e=g.find('a:ext',NS)
                    co=g.find('a:chOff',NS); ce=g.find('a:chExt',NS)
                    if o is not None and e is not None and co is not None and ce is not None:
                        gx,gy=px(o.get('x')),px(o.get('y'))
                        gw,gh=px(e.get('cx')),px(e.get('cy'))
                        cwx=px(ce.get('cx')) or 1; cwy=px(ce.get('cy')) or 1
                        ssx,ssy=gw/cwx, gh/cwy
                        nxf=(xf[0]+gx-px(co.get('x'))*ssx*xf[2],
                             xf[1]+gy-px(co.get('y'))*ssy*xf[3], xf[2]*ssx, xf[3]*ssy)
                rec(el, nxf)
            elif tag in ('sp','pic','cxnSp'):
                items.append((tag, el, xf))
    rec(sp_tree, (0,0,1,1))
    return items

def place(xf, b):
    dx,dy,sx,sy=xf
    return (dx+b[0]*sx, dy+b[1]*sy, b[2]*sx, b[3]*sy, b[5], b[6], b[4])

# ---------------------------------------------------------------- rendering
def runs_of(sp):
    """[(text, size_px, bold, italic, colour, align, indent_level)] per paragraph."""
    tx=sp.find('p:txBody', NS)
    if tx is None: return []
    paras=[]
    for p_ in tx.findall('a:p', NS):
        pPr=p_.find('a:pPr', NS)
        algn = pPr.get('algn') if pPr is not None else None
        lvl  = int(pPr.get('lvl','0')) if pPr is not None else 0
        bullet = pPr is not None and (pPr.find('a:buChar',NS) is not None or
                                      pPr.find('a:buAutoNum',NS) is not None)
        rs=[]
        for r_ in p_.findall('a:r', NS):
            t=r_.find('a:t', NS)
            if t is None or t.text is None: continue
            rPr=r_.find('a:rPr', NS)
            sz=float(rPr.get('sz'))/100*2 if (rPr is not None and rPr.get('sz')) else 36.0
            b = rPr is not None and rPr.get('b')=='1'
            i = rPr is not None and rPr.get('i')=='1'
            col = solid(rPr) or '#1A1A16'
            hl = rPr is not None and rPr.find('a:highlight', NS) is not None
            rs.append((t.text, sz, b, i, col, hl))
        paras.append((rs, algn, lvl, bullet))
    return paras

def brace_path(x, y, w, h, right=True):
    """A curly brace inside its own box, point at the middle of one side.
    PowerPoint draws these as prstGeom; without this they fell through to the
    rect branch, which has no stroke of its own, so they rendered as nothing -
    the slide lost the brace tying the three boxes to "context window"."""
    m = x + w*0.5
    tip = x + w if right else x
    return (f'M {x if right else x+w:.1f} {y:.1f} '
            f'C {m:.1f} {y+h*0.01:.1f}, {m:.1f} {y+h*0.03:.1f}, {m:.1f} {y+h*0.12:.1f} '
            f'L {m:.1f} {y+h*0.40:.1f} '
            f'C {m:.1f} {y+h*0.47:.1f}, {(m+tip)/2:.1f} {y+h*0.5:.1f}, {tip:.1f} {y+h*0.5:.1f} '
            f'C {(m+tip)/2:.1f} {y+h*0.5:.1f}, {m:.1f} {y+h*0.53:.1f}, {m:.1f} {y+h*0.60:.1f} '
            f'L {m:.1f} {y+h*0.88:.1f} '
            f'C {m:.1f} {y+h*0.97:.1f}, {m:.1f} {y+h*0.99:.1f}, '
            f'{x if right else x+w:.1f} {y+h:.1f}')

def style_line(sp):
    """A shape with no explicit <a:ln> can still get its outline from the theme
    via <p:style><a:lnRef>. The brace does exactly that."""
    ref=sp.find('p:style/a:lnRef', NS)
    return solid(ref) if ref is not None else None

# NOTHING IS OVERRIDDEN HERE ANY MORE. "new prompt" looked merged into
# "conversation history" because both resolved to flat accent1; in the source
# the second one carries lumMod 40% / lumOff 60%. Honouring the transform in
# solid() partitions them exactly as the author drew it.
BLOCK_FILL={}

def sp_svg(sp, box, o):
    x,y,w,h = box[:4]
    rot = box[6] if len(box)>6 else 0
    start = len(o)
    spPr=sp.find('p:spPr', NS)
    prst=spPr.find('a:prstGeom', NS) if spPr is not None else None
    kind=prst.get('prst') if prst is not None else None
    fill=solid(spPr)
    nofill = spPr is not None and spPr.find('a:noFill', NS) is not None
    if fill:
        _t=''.join(t.text or '' for t in sp.iter(f'{{{NS["a"]}}}t')).strip()
        fill=BLOCK_FILL.get(_t, fill)
    ln=spPr.find('a:ln', NS) if spPr is not None else None
    stroke=(solid(ln) if ln is not None else None) or style_line(sp)
    lw = (float(ln.get('w'))/12700*2 if (ln is not None and ln.get('w')) else 1.5)
    dash = ln is not None and ln.find('a:prstDash', NS) is not None and \
           ln.find('a:prstDash', NS).get('val','').startswith('dash')
    if kind and kind not in ('line','straightConnector1'):
        at=(f' fill="{fill}"' if fill and not nofill else ' fill="none"')
        st=(f' stroke="{stroke}" stroke-width="{lw:.1f}"' if stroke else '')
        dd=' stroke-dasharray="9 7"' if dash else ''
        if kind in ('ellipse','circle'):
            o.append(f'<ellipse cx="{x+w/2:.1f}" cy="{y+h/2:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}"{at}{st}{dd}/>')
        elif kind in ('rightBrace','leftBrace'):
            o.append(f'<path d="{brace_path(x,y,w,h,kind=="rightBrace")}" fill="none" '
                     f'stroke="{stroke or "#4472C4"}" stroke-width="{max(lw,2.2):.1f}" '
                     f'stroke-linecap="round"/>')
        elif kind=='roundRect':
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{min(w,h)*0.12:.1f}"{at}{st}{dd}/>')
        else:
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{at}{st}{dd}/>')
    elif stroke:
        # a line shape spans its own box corner to corner; flipV/flipH pick the
        # diagonal. Drawing it flat is what turned slide 2's two curves into a
        # ladder of horizontal dashes.
        fh, fv = box[4] if len(box)>4 else False, box[5] if len(box)>5 else False
        x1,y1,x2,y2 = x, (y+h if fv else y), x+w, (y if fv else y+h)
        if fh: x1,x2 = x2,x1
        dd=' stroke-dasharray="9 7"' if dash else ''
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{lw:.1f}"{dd}/>')
    # ---- text, wrapped and laid out top-down inside the box
    paras=runs_of(sp)
    if not paras: return
    bodyPr=sp.find('p:txBody/a:bodyPr', NS)
    anchor=bodyPr.get('anchor') if bodyPr is not None else None
    ADV=0.47                                  # Calibri average advance, in em

    def wrap(chars, avail):
        """chars: [(ch, size, bold, italic, colour, highlight)] -> list of lines"""
        lines=[]; cur=[]; wcur=0.0
        word=[]; wword=0.0
        for c in chars:
            cw=c[1]*ADV
            if c[0]==' ':
                if wcur+wword+cw>avail and cur: lines.append(cur); cur=[]; wcur=0
                cur+=word+[c]; wcur+=wword+cw; word=[]; wword=0
            else:
                word.append(c); wword+=cw
                if wcur+wword>avail and cur:
                    lines.append(cur); cur=[]; wcur=0
        if word:
            if wcur+wword>avail and cur: lines.append(cur); cur=[]
            cur+=word
        if cur: lines.append(cur)
        return lines or [[]]

    laid=[]
    for rs,algn,lvl,bullet in paras:
        if not rs: laid.append((None,None,None,None,20)); continue
        chars=[(ch,)+r[1:] for r in rs for ch in r[0]]
        pad=14+lvl*34
        for k,ln in enumerate(wrap(chars, max(40, (w-2*pad)*1.08))):
            fs=max((c[1] for c in ln), default=max(r[1] for r in rs))
            laid.append((ln, algn, pad, bullet and k==0, fs*1.32))
    tot=sum(e[4] for e in laid)
    cy = y + (max(0,(h-tot)/2) if anchor in (None,'ctr') else 4)
    for ln, algn, pad, bul, adv in laid:
        if ln is None: cy += adv; continue
        fs=max(c[1] for c in ln)
        cy += fs
        wpx=sum(c[1]*ADV for c in ln)
        ax = {'ctr':x+w/2-wpx/2, 'r':x+w-pad-wpx}.get(algn, x+pad)
        if bul: o.append(f'<text x="{ax-16:.1f}" y="{cy:.1f}" font-size="{fs*.8:.0f}" fill="#8A8A80">\u2022</text>')
        # NO HIGHLIGHT WASH. PowerPoint's yellow marker was drawn here as one
        # rect per character, sized on the pessimistic ADV advance, so every
        # marked phrase came out as a ragged row of overlapping blocks. The
        # emphasis is carried by the type instead: bold, and - for runs the
        # author left in plain body colour - EMPH, which is the red this same
        # deck already uses for emphasis elsewhere. A run that already has a
        # colour of its own keeps it and only gains the weight.
        parts=[]; run=[]
        def flush():
            if not run: return
            t,sz,b,i,col,hl = ''.join(q[0] for q in run), run[0][1],run[0][2],run[0][3],run[0][4],run[0][5]
            if hl:
                b=True
                if col.upper() in BODY: col=EMPH
            st=f'font-size="{sz:.0f}" fill="{col}"'
            if b: st+=' font-weight="700"'
            if i: st+=' font-style="italic"'
            parts.append(f'<tspan {st}>{esc(t)}</tspan>')
        key=None
        for c in ln:
            k2=c[1:]
            if k2!=key and run: flush(); run=[]
            key=k2; run.append(c)
        flush()
        o.append(f'<text x="{ax:.1f}" y="{cy:.1f}" class="s" xml:space="preserve">'
                 f'{"".join(parts)}</text>')
        cy += adv-fs
    # a shape's own rotation, applied to everything it drew. Only two shapes in
    # this deck are rotated - the braces on the two context-window slides - and
    # discarding the rotation is why one of them was a vertical brace hidden
    # off the side of the drawing instead of a horizontal one under the boxes.
    if rot:
        o.insert(start, f'<g transform="rotate({rot:.2f} {x+w/2:.1f} {y+h/2:.1f})">')
        o.append('</g>')

# ---- editorial overlays on a converted slide ------------------------------
# The source slide is reproduced shape for shape; these two tables are the only
# places this deck adds to it, and they are declared here rather than hidden in
# a string edit downstream so that the slide's drawing stays in one file.
PIC_BOX={26: (990, 330, 790, 340)}       # slide 26's physlib shot, moved right
EXTRA_ART={26: [('art/lean-mathlib.png', 150, 300, 760, 428)]}
EXTRA_TEXT={26: [(150, 782, 34, '#1A1A16', 'Mathlib \u2014 the mathematics'),
                 (150, 830, 23, '#8A8A80', 'groups, measure, linear algebra, polytopes'),
                 (990, 782, 34, '#1A1A16', 'physlib \u2014 the physics'),
                 (990, 830, 23, '#8A8A80',
                  'an open-source community project, still being built')]}

def build(slide_no, media):
    root=ET.fromstring(z.read(f'ppt/slides/slide{slide_no}.xml'))
    tree=root.find('p:cSld/p:spTree', NS)
    rel=rels(slide_no)
    o=[]; moved=False
    for tag, el, xf in collect(tree):
        b=xfrm_of(el)
        if b is None: continue
        box=place(xf, b)
        if tag=='pic':
            emb=el.find('p:blipFill/a:blip', NS)
            rid=emb.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') if emb is not None else None
            tgt=rel.get(rid)
            if not tgt or tgt not in media: continue
            mt,data=media[tgt]
            x,y,w,h=box[:4]
            if slide_no in PIC_BOX and not moved:
                x,y,w,h = PIC_BOX[slide_no]; moved=True
            o.append(f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                     f'preserveAspectRatio="none" href="data:{mt};base64,{base64.b64encode(data).decode()}"/>')
        else:
            sp_svg(el, box, o)
    for tx_,ty,tsz,tcol,ttxt in EXTRA_TEXT.get(slide_no, []):
        o.append(f'<text x="{tx_}" y="{ty}" font-size="{tsz}" fill="{tcol}" '
                 f'class="s">{esc(ttxt)}</text>')
    for path,ax,ay,aw,ah in EXTRA_ART.get(slide_no, []):
        raw=open(path,'rb').read()
        o.append(f'<image x="{ax}" y="{ay}" width="{aw}" height="{ah}" '
                 f'preserveAspectRatio="xMidYMid meet" '
                 f'href="data:image/png;base64,{base64.b64encode(raw).decode()}"/>')
    return ('<svg class="pipe-svg" data-cum="0" viewBox="0 0 1920 1080" '
            'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<style>.s{font-family:Calibri,Carlito,sans-serif}</style>'
            + ''.join(o) + '</svg>')

# ---- pass 1: learn how big each picture is actually drawn ------------------
for n in range(1,28):
    root=ET.fromstring(z.read(f'ppt/slides/slide{n}.xml'))
    rel=rels(n)
    for tag, el, xf in collect(root.find('p:cSld/p:spTree', NS)):
        if tag!='pic': continue
        b=xfrm_of(el)
        if b is None: continue
        _,_,w,h = place(xf,b)[:4]
        emb=el.find('p:blipFill/a:blip', NS)
        rid=emb.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') if emb is not None else None
        if rid and rel.get(rid): note_use(rel[rid], w, h)
MEDIA=emit_media()
print(f'media: {len(MEDIA)} images, {sum(len(v[1]) for v in MEDIA.values())/1024/1024:.1f} MB after downscaling')

frames=[build(n, MEDIA) for n in range(1,28)]
open('front-slides.json','w').write(json.dumps({'svg':frames}))
print(f'converted {len(frames)} slides, {sum(len(f) for f in frames)/1024/1024:.1f} MB of SVG')
