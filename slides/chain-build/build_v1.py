# -*- coding: utf-8 -*-
"""chain-build-v1.html - the same figures, in an order that argues.

WHY THIS IS A SEPARATE FILE. build_html.py reads chain-build.html and patches
it in place, so that file is both the build's input and its output. This script
takes the finished v0 page as read-only input and writes a new one, which means
the restructure can never damage the deck that already works.

WHAT CHANGES. Only the driver and three new frames. Every figure, every style
rule and the whole inspector are carried over untouched - so a frame that was
correct in v0 is the same pixels here.

THE ONE STRUCTURAL CHANGE. v0 addressed regions by arithmetic (fro = i < NFRO,
mot = i < NFRO+NMOT, ...), which hard-codes both the region order and the
assumption that each region is one contiguous run. The measured-numbers region
has to split into three pieces that sit in three different acts, and that is
exactly what the arithmetic cannot express. So the order is declared instead:
ORDER[i] is the pair (region, step) for frame i, and any sequence is sayable.
"""
import re, json

SRC='chain-build.html'; OUT='chain-build-v1.html'
H=open(SRC,encoding='utf-8').read()

# ---- 0. the v0 order, read back out of the page we are rebuilding -------
hdr=re.search(r'const METER=\[(.*?)\], MAXW=(\d+), NMOT=(\d+), NPIPE=(\d+),'
              r' NOPEN=(\d+), NCLO=(\d+), NFRO=(\d+), OPENM=new Set\(\[(.*?)\]\)', H, re.S)
assert hdr, 'could not find the v0 driver header'
OLD=json.loads('['+hdr.group(1)+']')
MAXW=int(hdr.group(2)); NMOT,NPIPE,NOPEN,NCLO,NFRO=(int(hdr.group(k)) for k in (3,4,5,6,7))
OLDOPEN={int(x) for x in hdr.group(8).split(',') if x.strip()}
assert len(OLD)==69, f'expected 69 v0 frames, found {len(OLD)}'

def where(i):
    """v0 global frame index -> (region, step within that region)."""
    if i < NFRO:                     return 'f', i
    if i < NFRO+NMOT:                return 'm', i-NFRO
    if i < NFRO+NMOT+NPIPE:          return 'p', i-NFRO-NMOT
    if i < NFRO+NMOT+NPIPE+NOPEN:    return 'o', i-NFRO-NMOT-NPIPE
    if i >= len(OLD)-NCLO:           return 'z', i-(len(OLD)-NCLO)
    return 'c', i-NFRO-NMOT-NPIPE-NOPEN

# ---- 0b. re-inline the figures whose generators v1 changed --------------
# build_v1 reads the FINISHED v0 page, so a figure only reaches v1 if it is
# re-inlined here. closing.py's headline band and heavier strokes went into
# closing.svg and stopped there - the page kept showing the v0 drawing while
# the generator had moved on. Same failure build_html.py once had with #fig.
def put_wrap(H, wid, path):
    svg=re.sub(r'>\s*\n\s*<','><',open(path,encoding='utf-8').read()).strip()
    block=f'<div class="wrap" id="{wid}">{svg}</div>'
    m=re.search(rf'<div class="wrap" id="{wid}">.*?</div>', H, re.S)
    assert m, f'no wrap #{wid} in {SRC}'
    print(f'  re-inlined #{wid} <- {path}')
    return H[:m.start()]+block+H[m.end():]

for wid,path in (('cw','closing.svg'), ('pw','pipeline.svg')):
    H=put_wrap(H, wid, path)

# ---- 1. the three new front frames, appended to #fw ---------------------
NEW=[('title','title.svg','title.json'),
     ('hinge','hinge.svg','hinge.json'),
     ('roadmap','roadmap.svg','roadmap.json'),
     ('crisisbridge','crisisbridge.svg','crisisbridge.json'),
     ('lean1','lean1.svg','lean1.json'),
     ('lean2','lean2.svg','lean2.json'),
     ('lean3','lean3.svg','lean3.json'),
     ('conclusion','conclusion.svg','conclusion.json'),
     ('discussion','discussion.svg','discussion.json')]
def mini(s): return re.sub(r'>\s*\n\s*<','><',s).strip()
frag=''; NEWAT={}
for k,(key,svgp,jsonp) in enumerate(NEW):
    idx=NFRO+k                                  # its position among #fw's children
    s=mini(open(svgp,encoding='utf-8').read())
    s=re.sub(r'<svg class="pipe-svg"[^>]*?(?= viewBox| xmlns)',
             f'<svg class="frosvg" id="fs{idx}"', s, count=1)
    # the front region shows whole SVGs, so the build group is on at author time
    s=s.replace('class="pp-g"','class="pp-g on"')
    frag+=s
    NEWAT[key]=(idx, json.load(open(jsonp))['meter'][0])
m=re.search(r'(<div class="wrap" id="fw">.*?)(</div>\s*<div class="wrap" id="cw">)', H, re.S)
assert m, 'could not find the front wrap'
H=H[:m.end(1)]+frag+H[m.end(1):]

# ---- 2. the arc ---------------------------------------------------------
# Each entry is a v0 frame index or one of the new keys. Cut on purpose:
#   0  source slide 1  - two empty placeholders, zero text runs
#   4  source slide 5  - slide 6 is the same frame with one more picture
#   6  source slide 7  - slide 8 is the same frame plus the context window
#   18 source slide 19 - slide 20 is the same frame with the second picture
#   20 source slide 21 - slide 22 is the same frame with the fourth picture
# Each entry is a v0 frame index or one of the new keys.
ARC=[
 ('I \u00b7 OPENING',                      ['title', 1]),
 ('II \u00b7 WHAT THE MACHINE IS DOING',   ['crisisbridge', 2, 3, 5, 7, 8]),
 ('III \u00b7 WHAT HAS TEETH',             [9, 10, 11, 12, 13, 14, 15, 16, 17, 'hinge']),
 ('IV \u00b7 WHAT WE ARE TRYING TO TRUST', [19, 21, 22, 23, 27, 'roadmap']),
 ('V \u00b7 HOW A PAPER BECOMES CLAIMS',   [24, 25, 'lean1', 'lean2', 'lean3', 26,
                                          36, 37, 38, 39, 40, 41, 42]),
 ('VI \u00b7 ONE REAL PAPER',              [43, 44, 45, 46, 47, 48, 49]),
 ('VII \u00b7 ONE THEOREM\u2019S CHAIN',    list(range(50, 61))),
 ('VIII \u00b7 THREE WISHES',              list(range(61, 69))),
 ('IX \u00b7 IN CLOSING',                  ['conclusion', 'discussion']),
]
ORDER=[]; METER=[]; ACTS=[]; OPENM=[]; provenance=[]
for act,items in ARC:
    for it in items:
        if isinstance(it,str):
            idx,met=NEWAT[it]; ORDER.append(('f',idx)); METER.append(met)
        else:
            ORDER.append(where(it)); METER.append(OLD[it])
            if it in OLDOPEN: OPENM.append(len(ORDER)-1)
        ACTS.append(act); provenance.append(it)

used={it for _,items in ARC for it in items if isinstance(it,int)}
dropped=sorted(set(range(len(OLD)))-used)
# 0/4/6/18/20 are duplicate build steps of one source slide; 28-35 is the whole
# measured-numbers region, which the speaker cut as a technical report in a talk
# that is about a possibility. What it said honestly now lives on the conclusion.
assert dropped==[0,4,6,18,20]+list(range(28,36)), f'unexpected cut list {dropped}'
assert len(ORDER)==len(METER)==len(ACTS)
assert len({p for p in provenance if isinstance(p,int)})==len(used), 'a frame is used twice'

# ---- 3. the driver ------------------------------------------------------
js=lambda o: json.dumps(o, ensure_ascii=False, separators=(',',':'))
HEADER=(f'const METER={js(METER)}, ORDER={js([list(t) for t in ORDER])},'
        f' ACTS={js(ACTS)}, MAXW={MAXW}, NOPEN={NOPEN},'
        f' OPENM=new Set({js(OPENM)}), N=METER.length;')
H=re.sub(r'const METER=\[.*?N=METER\.length;', lambda _: HEADER, H, count=1, flags=re.S)

RENDER = """function render(){
 document.querySelectorAll('.is-new').forEach(el=>el.classList.remove('is-new'));
 if(typeof clearSel==='function') clearSel();
 const R=ORDER[i][0], j=ORDER[i][1];
 const fro=R==='f', mot=R==='m', pipe=R==='p', opening=R==='o',
       chain=R==='c', closing=R==='z';
 if(fw) fw.classList.toggle('off', !fro);
 if(mw) mw.classList.toggle('off', !mot);
 if(cw) cw.classList.toggle('off', !closing);
 pw.classList.toggle('off', !pipe);
 ow.classList.toggle('off', !opening);
 fig.classList.toggle('off', !chain);
 if(fw) fw.querySelectorAll('svg').forEach((el,k)=>el.classList.toggle('on', fro && k===j));
 showFig(mw, mot, j);
 showFig(cw, closing, j);
 showFig(pw, pipe, j);
 for(let k=0;k<NOPEN;k++)
   document.getElementById('o'+k).classList.toggle('on', opening && k===j);
 if(chain){
   const phase = j===8?'roots' : j===9?'form' : j===10?'stuck' : 'build';
   fig.dataset.phase=phase;
   const upto = phase==='build' ? j : MAXW;
   document.querySelectorAll('[data-wave]').forEach(el=>{
     const w=parseInt(el.dataset.wave,10);
     el.classList.toggle('on', w<=upto);
     el.classList.toggle('is-new', phase==='build' && j>=2 && w===upto && !el.classList.contains('ch-lab'));
   });
 }
 const m=document.getElementById('m');
 m.textContent=METER[i];
 m.classList.toggle('open', OPENM.has(i));
 const a=document.getElementById('act');
 if(a) a.textContent=ACTS[i];
 hint.style.display = (chain && !insp.classList.contains('on')) ? '' : 'none';
}
"""
H,n=re.subn(r'function render\(\)\{[\s\S]*?\n\}\n', lambda _: RENDER, H, count=1)
assert n==1, 'render() not replaced'

# ---- 4. the act line, opposite the meter --------------------------------
if 'id="act"' not in H:
    H=H.replace('<div class="meter" id="m"></div>',
                '<div class="meter" id="m"></div>\n  <div class="actline" id="act"></div>',1)
    H=H.replace('.meter{',
 '.actline{position:absolute;right:58px;bottom:34px;font-family:var(--f-mono);'
 'font-size:15px;letter-spacing:.2em;text-transform:uppercase;color:var(--light);'
 'opacity:.8;text-align:right}\n.meter{',1)

open(OUT,'w',encoding='utf-8').write(H)
json.dump({'order':[list(t) for t in ORDER],'meter':METER,'acts':ACTS,
           'provenance':provenance,'dropped':dropped},
          open('order-v1.json','w'), ensure_ascii=False, indent=1)

print(f'{OUT}  {len(H.encode())//1024} KB')
print(f'{len(ORDER)} frames  (v0 had {len(OLD)}; {len(dropped)} cut, {len(NEW)} new)')
print(f'cut: {dropped}   warm meters at {OPENM}')
for act,items in ARC:
    print(f'  {len(items):>2}  {act}')
