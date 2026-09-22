# -*- coding: utf-8 -*-
"""aqa_talk_924.pptx = the speaker's own slides + this project's generated ones.

Slide_001.pptx is the BASE, not a source to copy out of. Its theme, its twelve
layouts, its thirty-two images and its twenty-seven slides stay exactly as the
author built them, so every one of those slides is still editable in the way its
author expects. The forty-three generated slides are copied INTO that package.

Copying a slide across packages means five registrations, and missing any one of
them produces a file PowerPoint refuses rather than a file that looks wrong:
  1. ppt/slides/slideN.xml                 the slide itself
  2. ppt/slides/_rels/slideN.xml.rels      with every Target re-pointed
  3. [Content_Types].xml                   an Override per part
  4. ppt/_rels/presentation.xml.rels       a relationship with a fresh rId
  5. ppt/presentation.xml <p:sldIdLst>     the running order
Each one is asserted below.
"""
import zipfile, re, json, shutil, os, sys

HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.join(HERE,'Slide_001.pptx')
GEN =os.path.join(HERE,'aqa-generated.pptx')
OUT =os.path.join(HERE,'aqa_talk_924.pptx')
WORK=os.path.join(HERE,'.merge-work')

R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
CT_SLIDE='application/vnd.openxmlformats-officedocument.presentationml.slide+xml'
CT_NOTES='application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml'

def read_all(path):
    z=zipfile.ZipFile(path); return {n:z.read(n) for n in z.namelist()}

BASEP=read_all(BASE); GENP=read_all(GEN)
MAN=json.load(open(os.path.join(HERE,'deck-v1-manifest.json')))
ORD=json.load(open(os.path.join(HERE,'order-v1.json')))

def txt(p): return BASEP[p].decode('utf-8')
def put(p,s): BASEP[p]=s.encode('utf-8')

# ---------------------------------------------------------------- 1. edits
BODY={'242832','1A1A16','000000'}
def de_highlight(x):
    """PowerPoint's yellow marker becomes bold, and - where the author left the
    run in plain body colour - the #C00000 this deck already uses to emphasise."""
    def run(m):
        r=m.group(0)
        if '<a:highlight>' not in r: return r
        r=re.sub(r'<a:highlight>.*?</a:highlight>','',r,flags=re.S)
        col=re.search(r'<a:solidFill><a:srgbClr val="([0-9A-Fa-f]{6})"',r)
        if col and col.group(1).upper() in BODY:
            r=r[:col.start(1)]+'C00000'+r[col.end(1):]
        r=re.sub(r'<a:rPr\b(?![^>]*\bb="1")', '<a:rPr b="1"', r, count=1)
        return r
    x=re.sub(r'<a:r>.*?</a:r>', run, x, flags=re.S)
    # Anything left is on <a:endParaRPr> - the paragraph mark's own properties,
    # invisible but still a marker in the file. A scoped regex for that element
    # cannot be written simply, because its children are self-closing tags; and
    # there is no case where a highlight should survive, so sweep the rest.
    return re.sub(r'<a:highlight>.*?</a:highlight>', '', x, flags=re.S)

# The context-window blocks are NOT recoloured. "new prompt" already carries
# accent1 at lumMod 40% / lumOff 60% in the source, so PowerPoint has always
# drawn it as a distinct lighter block; only this project's SVG converter was
# flattening the transform. The author's slide is left as the author made it.

EMU=12192000/1920
def emu(v): return int(round(v*EMU))
def pageno(x, n):
    """One text box, bottom left, matching the generated slides."""
    sp=(f'<p:sp><p:nvSpPr><p:cNvPr id="9{n:03d}" name="pageno"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
        f'<a:xfrm><a:off x="{emu(75)}" y="{emu(1005)}"/>'
        f'<a:ext cx="{emu(160)}" cy="{emu(44)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0"/>'
        f'<a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1100" dirty="0">'
        f'<a:solidFill><a:srgbClr val="8A8A80"/></a:solidFill>'
        f'<a:latin typeface="Calibri"/></a:rPr><a:t>{n}</a:t></a:r></a:p>'
        f'</p:txBody></p:sp>')
    return x.replace('</p:spTree>', sp+'</p:spTree>', 1)

# ---- slide 26 gets the Lean/Mathlib logo beside the physlib shot it had ----
def slide26_art(x, rid):
    x=re.sub(r'(<p:pic>.*?<a:off x=")-?\d+(" y=")-?\d+("/><a:ext cx=")\d+("\s*cy=")\d+',
             lambda m: (m.group(1)+str(emu(990))+m.group(2)+str(emu(330))+m.group(3)
                        +str(emu(790))+m.group(4)+str(emu(340))), x, count=1, flags=re.S)
    pic=(f'<p:pic><p:nvPicPr><p:cNvPr id="880" name="mathlib"/><p:cNvPicPr/><p:nvPr/>'
         f'</p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/>'
         f'</a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="{emu(150)}" y="{emu(300)}"/>'
         f'<a:ext cx="{emu(760)}" cy="{emu(428)}"/></a:xfrm>'
         f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
    caps=''
    for i,(cx,cy,sz,col,t) in enumerate(
            [(150,770,1700,'1A1A16','Mathlib — the mathematics'),
             (150,822,1150,'8A8A80','groups, measure, linear algebra, polytopes'),
             (990,770,1700,'1A1A16','physlib — the physics'),
             (990,822,1150,'8A8A80','an open-source community project, still being built')]):
        caps+=(f'<p:sp><p:nvSpPr><p:cNvPr id="88{i+1}" name="cap{i}"/>'
               f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
               f'<a:xfrm><a:off x="{emu(cx)}" y="{emu(cy)}"/>'
               f'<a:ext cx="{emu(780)}" cy="{emu(52)}"/></a:xfrm>'
               f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
               f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0"/>'
               f'<a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="{sz}" dirty="0">'
               f'<a:solidFill><a:srgbClr val="{col}"/></a:solidFill>'
               f'<a:latin typeface="Calibri"/></a:rPr><a:t>{t}</a:t></a:r></a:p>'
               f'</p:txBody></p:sp>')
    return x.replace('</p:spTree>', pic+caps+'</p:spTree>', 1)

# ---------------------------------------------------------------- 2. copy in
next_slide=28
next_note=max(int(re.search(r'(\d+)',n.rsplit('/',1)[-1]).group(1))
              for n in BASEP if n.startswith('ppt/notesSlides/notesSlide'))+1
next_media=max(int(re.search(r'(\d+)',n.rsplit('/',1)[-1]).group(1) or 0)
               for n in BASEP if re.search(r'image\d+', n))+1
base_notes_master='../notesMasters/notesMaster1.xml'
BLANK_LAYOUT='../slideLayouts/slideLayout7.xml'

media_map={}
gen_to_base={}
for m in MAN['frames']:
    if m['from']!='generated': continue
    g=m['gen']
    src=f'ppt/slides/slide{g}.xml'
    assert src in GENP, src
    dst=f'ppt/slides/slide{next_slide}.xml'
    BASEP[dst]=GENP[src]
    rels=GENP[f'ppt/slides/_rels/slide{g}.xml.rels'].decode()
    # every Target has to land on a part that exists in the BASE package
    def fix(mm):
        t=mm.group(1)
        if 'slideLayout' in t: return f'Target="{BLANK_LAYOUT}"'
        if 'notesSlide' in t:
            gn=t.rsplit('/',1)[-1]
            src_n='ppt/notesSlides/'+gn
            global next_note
            new=f'ppt/notesSlides/notesSlide{next_note}.xml'
            nx=GENP[src_n].decode()
            BASEP[new]=nx.encode()
            nr=GENP['ppt/notesSlides/_rels/'+gn+'.rels'].decode()
            nr=re.sub(r'Target="\.\./notesMasters/notesMaster\d+\.xml"',
                      f'Target="{base_notes_master}"', nr)
            nr=re.sub(r'Target="\.\./slides/slide\d+\.xml"',
                      f'Target="../slides/slide{next_slide}.xml"', nr)
            BASEP[f'ppt/notesSlides/_rels/notesSlide{next_note}.xml.rels']=nr.encode()
            out=f'Target="../notesSlides/notesSlide{next_note}.xml"'
            next_note+=1
            return out
        if '/media/' in t:
            gn=t.rsplit('/',1)[-1]
            if gn not in media_map:
                global next_media
                ext=gn.rsplit('.',1)[-1]
                new=f'image{next_media}.{ext}'
                BASEP['ppt/media/'+new]=GENP['ppt/media/'+gn]
                media_map[gn]=new; next_media+=1
            return f'Target="../media/{media_map[gn]}"'
        return mm.group(0)
    rels=re.sub(r'Target="([^"]+)"', fix, rels)
    BASEP[f'ppt/slides/_rels/slide{next_slide}.xml.rels']=rels.encode()
    gen_to_base[m['v1']]=next_slide
    next_slide+=1

# ---------------------------------------------------------------- 3. edits on
# the author's own slides, plus a page number on every slide in the deck
src_for={}                                    # v1 index -> base slide number
for k,(reg,step) in enumerate(ORD['order']):
    if reg=='f' and step<=26: src_for[k]=step+1

# slide 26 needs one new image part and a relationship to it
if any(v==26 for v in src_for.values()):
    logo=open(os.path.join(HERE,'art/lean-mathlib.png'),'rb').read()
    lname=f'image{next_media}.png'; next_media+=1
    BASEP['ppt/media/'+lname]=logo
    rp='ppt/slides/_rels/slide26.xml.rels'
    rx=txt(rp)
    used={int(x) for x in re.findall(r'Id="rId(\d+)"', rx)}
    lrid=f'rId{max(used)+1}'
    rx=rx.replace('</Relationships>',
        f'<Relationship Id="{lrid}" Type="{R}/image" Target="../media/{lname}"/></Relationships>')
    put(rp,rx)
    put('ppt/slides/slide26.xml', slide26_art(txt('ppt/slides/slide26.xml'), lrid))

for v1,n in src_for.items():
    p=f'ppt/slides/slide{n}.xml'
    x=de_highlight(txt(p))
    put(p, pageno(x, v1+1))
for v1,n in gen_to_base.items():
    pass                                       # generated slides number themselves

# ---------------------------------------------------------------- 4. register
ct=txt('[Content_Types].xml')
for n in sorted(BASEP):
    if n.startswith('ppt/slides/slide') and n.endswith('.xml'):
        if f'PartName="/{n}"' not in ct:
            ct=ct.replace('</Types>', f'<Override PartName="/{n}" ContentType="{CT_SLIDE}"/></Types>')
    if n.startswith('ppt/notesSlides/notesSlide') and n.endswith('.xml'):
        if f'PartName="/{n}"' not in ct:
            ct=ct.replace('</Types>', f'<Override PartName="/{n}" ContentType="{CT_NOTES}"/></Types>')
put('[Content_Types].xml', ct)

pr=txt('ppt/_rels/presentation.xml.rels')
used={int(x) for x in re.findall(r'Id="rId(\d+)"', pr)}
rid_of={}
nxt=max(used)+1
for n in range(28, next_slide):
    tgt=f'slides/slide{n}.xml'
    m=re.search(rf'Id="rId(\d+)"[^>]*Target="{re.escape(tgt)}"', pr)
    if m: rid_of[n]=f'rId{m.group(1)}'; continue
    rid_of[n]=f'rId{nxt}'
    pr=pr.replace('</Relationships>',
        f'<Relationship Id="rId{nxt}" Type="{R}/slide" Target="{tgt}"/></Relationships>')
    nxt+=1
for n in range(1,28):
    m=re.search(rf'Id="rId(\d+)"[^>]*Target="slides/slide{n}\.xml"', pr)
    if m: rid_of[n]=f'rId{m.group(1)}'
put('ppt/_rels/presentation.xml.rels', pr)

# ---------------------------------------------------------------- 5. the order
px=txt('ppt/presentation.xml')
ids=[]
for k in range(len(ORD['order'])):
    n = gen_to_base.get(k) or src_for.get(k)
    assert n is not None, f'frame {k} has no slide'
    assert n in rid_of, f'slide {n} has no relationship'
    ids.append(f'<p:sldId id="{256+k}" r:id="{rid_of[n]}"/>')
px=re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', '<p:sldIdLst>'+''.join(ids)+'</p:sldIdLst>',
          px, count=1, flags=re.S)
put('ppt/presentation.xml', px)

# Slides the running order never names are dropped - and then everything that
# only they referenced. Deleting the slide alone left four notesSlides pointing
# at parts that no longer existed, which PowerPoint reports as a corrupt file,
# so the sweep below is by REACHABILITY from the package root rather than by a
# list of things I remembered to remove.
keep={gen_to_base.get(k) or src_for.get(k) for k in range(len(ORD['order']))}
for n in range(1, next_slide):
    if n in keep: continue
    BASEP.pop(f'ppt/slides/slide{n}.xml', None)
    BASEP.pop(f'ppt/slides/_rels/slide{n}.xml.rels', None)
    pr=re.sub(rf'<Relationship Id="rId\d+"[^>]*Target="slides/slide{n}\.xml"/>','',
              txt('ppt/_rels/presentation.xml.rels'))
    put('ppt/_rels/presentation.xml.rels', pr)

import posixpath
def rels_of(part):
    d,f=posixpath.split(part)
    return posixpath.join(d,'_rels',f+'.rels')
def reachable():
    seen=set(); stack=['_rels/.rels']
    while stack:
        rp=stack.pop()
        if rp in seen or rp not in BASEP: continue
        seen.add(rp)
        base=posixpath.dirname(posixpath.dirname(rp)) if rp!='_rels/.rels' else ''
        for m in re.finditer(r'Target="([^"]+)"(?:\s+TargetMode="(\w+)")?', BASEP[rp].decode()):
            t,mode=m.group(1),m.group(2)
            if mode=='External' or t.startswith('http'): continue
            p=posixpath.normpath(posixpath.join(base,t)) if not t.startswith('/') else t[1:]
            if p in seen or p not in BASEP: continue
            seen.add(p); stack.append(rels_of(p))
    return seen
live=reachable()
dropped=[n for n in list(BASEP)
         if n.split('/')[0]=='ppt' and n not in live and '/_rels/' not in n
         and not n.startswith(('ppt/presentation.xml',))]
for n in dropped:
    BASEP.pop(n, None); BASEP.pop(rels_of(n), None)
    ct=txt('[Content_Types].xml')
    put('[Content_Types].xml', re.sub(rf'<Override PartName="/{re.escape(n)}"[^>]*/>','',ct))
print(f'  swept {len(dropped)} orphaned parts')

# ---------------------------------------------------------------- 6. write
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    for n in sorted(BASEP): z.writestr(n, BASEP[n])

z=zipfile.ZipFile(OUT)
n_sl=len([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$',n)])
_lst=re.search(r'<p:sldIdLst>(.*?)</p:sldIdLst>',
               z.read('ppt/presentation.xml').decode(), re.S).group(1)
order=re.findall(r'r:id="(rId\d+)"', _lst)
print(f'{OUT.rsplit("/",1)[-1]}  {len(z.read("ppt/presentation.xml"))} B presentation')
print(f'  {n_sl} slide parts, {len(order)} in the running order '
      f'({len(src_for)} the author\'s, {len(gen_to_base)} generated)')
