# -*- coding: utf-8 -*-
"""Assemble chain-build.html from the generated figures.

The page is not hand-edited. Every figure is re-inlined from the file that
generated it, and the driver - the meter strings and the region boundaries - is
regenerated from deck-meters.json, which deck.js writes. So the deck order is
declared exactly once, in deck.js, and the page and the pptx cannot disagree
about what frame 12 is.

Run order: pipeline.py, motivation.py, gen_chain.py, frames.py, gen_reduced.py,
gen_records.py, then `node deck.js`, then this.
"""
import re, json, os

H=open('chain-build.html',encoding='utf-8').read()
M=json.load(open('deck-meters.json'))
def mini(s): return re.sub(r'>\s*\n\s*<','><',s).strip()

# ---- 1. re-inline every figure whose source changed --------------------
def replace_open(H, oid, path, viewbox='0 0 1920 1040'):
    raw=mini(open(path,encoding='utf-8').read())
    raw=re.sub(r'^<\?xml[^>]*\?>','',raw)
    raw=re.sub(r'^<!DOCTYPE[^>]*>','',raw, flags=re.S)
    raw=re.sub(r'^\s*','',raw)
    body=re.sub(r'^<svg[^>]*?>','',raw,count=1,flags=re.S)
    tag=(f'<svg class="opensvg" id="{oid}" preserveAspectRatio="xMidYMid meet"'
         f' viewBox="{viewbox}" xmlns="http://www.w3.org/2000/svg" style="background:#fff">')
    i=H.index(f'id="{oid}"'); a=H.rindex('<svg', 0, i); b=H.index('</svg>', i)+len('</svg>')
    return H[:a] + tag + body + H[b:]

# EVERY opening frame is re-inlined, not just the three that happened to
# change first. o2/o3/o5/o6 are matplotlib output and were frozen pastes: the
# build rebuilt every frame around them and left them stating whatever counts
# they held when they were last hand-inlined.
for oid,path,vb in (('o0','frames/rec-mathclaim.svg','0 0 1920 1040'),
                    ('o1','frames/rec-lamport.svg',  '0 0 1920 1040'),
                    ('o2','frames/open00.svg',       '0 0 1080 584.6'),
                    ('o3','frames/open01.svg',       '0 0 1080 584.6'),
                    ('o4','reduced.svg',             '0 0 1920 1040'),
                    ('o5','frames/open02.svg',       '0 0 1080 584.6'),
                    ('o6','frames/open03.svg',       '0 0 1080 584.6')):
    H=replace_open(H,oid,path,vb); print(f'  re-inlined {oid} <- {path}')

# ---- 2. the hand-built figures, each in its own wrap -------------------
def put_wrap(H, wid, path, before):
    """Insert or replace the wrap holding one Fig-generated figure."""
    if not os.path.exists(path):
        return H, False
    svg=mini(open(path,encoding='utf-8').read())
    block=f'<div class="wrap" id="{wid}">{svg}</div>'
    m=re.search(rf'<div class="wrap" id="{wid}">.*?</div>', H, re.S)
    if m: H=H[:m.start()]+block+H[m.end():]; print(f'  replaced #{wid} <- {path}')
    else: H=H.replace(before, block+'\n  '+before, 1); print(f'  inserted #{wid} <- {path}')
    return H, True

def put_fig(H, path):
    """Re-inline the chain figure itself. This was missing: every other figure
    was regenerated on each build and #fig was not, so the page kept showing a
    chain drawn by an older version of gen_chain.py while the pptx moved on."""
    svg=mini(open(path,encoding='utf-8').read())
    i=H.index('id="fig"'); a=H.rindex('<div', 0, i)
    o=H.index('<svg', i); c=H.index('</svg>', o)+len('</svg>')
    print(f'  re-inlined #fig <- {path}')
    return H[:o] + svg + H[c:]

H = put_fig(H, 'chain.svg')
H,_      = put_wrap(H,'pw','pipeline.svg',   '<div class="wrap" id="ow">')
H,hasMot = put_wrap(H,'mw','motivation.svg', '<div class="wrap" id="pw">')
H,hasClo = put_wrap(H,'cw','closing.svg',    '<div class="wrap" id="mw">')
# THE PAGE AND THE PPTX DIVERGE HERE, ON PURPOSE.
# The page shows Slide_001.pptx exactly - all 27 slides, converted shape for
# shape by pptx2svg.py, images and all. The pptx keeps the redrawn, editable
# 21-frame version, because pasting 27 rasterised slides into it would be
# strictly worse than the original file, which the user already has. Nothing is
# shared between the two paths, so they cannot silently disagree about a frame.
FRO=json.load(open('front-slides.json'))['svg']
FMETA=json.load(open('front-meta.json'))['meter']
# one native frame closes the imported opening and hands over to this deck
# the front region shows whole SVGs, so the bridge's build-group has to be
# switched on at author time - nothing here ever adds .on to a .pp-g
FRO=FRO+[open('bridge.svg',encoding='utf-8').read().replace('class="pp-g"','class="pp-g on"')]
FMETA=FMETA+['OF THE FOUR, THIS TALK IS ABOUT THE SECOND']
assert len(FRO)==len(FMETA), f'{len(FRO)} slides but {len(FMETA)} meters'
block='<div class="wrap" id="fw">'+''.join(
    re.sub(r'<svg class="pipe-svg"[^>]*?(?= viewBox| xmlns)',
           f'<svg class="frosvg" id="fs{k}"', s, count=1)
    for k,s in enumerate(FRO))+'</div>'
m=re.search(r'<div class="wrap" id="fw">.*?</div>\s*(?=<div class="wrap" id="cw">)', H, re.S)
if m: H=H[:m.start()]+block+H[m.end():]
else: H=H.replace('<div class="wrap" id="cw">', block+'\n  <div class="wrap" id="cw">',1)
print(f'  inlined #fw <- {len(FRO)} converted slides')

if '.frosvg' not in H:
    H=H.replace('.pipe-svg{',
 '''.frosvg{position:absolute;left:0;top:0;width:1920px;height:1080px;display:none}
.frosvg.on{display:block}
.pipe-svg{''',1)
if '.pipe-svg' not in H:
    H=H.replace('.opensvg{position:absolute',
 '''.pipe-svg{width:1920px;height:1080px;overflow:visible}
.pp-t{font-family:var(--f-body)}
.pp-g{opacity:0;transition:opacity .55s var(--ease)}
.pp-g.on{opacity:1}
.opensvg{position:absolute''',1)
    print('  inserted the figure CSS')

# ---- 3. the driver, regenerated wholesale from deck-meters.json --------
nFro = len(FMETA)          # the page's front region, not the pptx's
nMot, nPipe, nOpen, nClo = M['nMot'], M['nPipe'], M['nOpen'], M.get('nClo',0)
assert len(M['meter'])==len(M['open']), 'deck-meters.json is inconsistent'
# swap the pptx's native front meters for the converted slides' own titles
ALL = FMETA + M['meter'][M.get('nFro',0):]
opens_at = [k+nFro-M.get('nFro',0) for k,v in enumerate(M['open']) if v and k>=M.get('nFro',0)]
meters=', '.join(json.dumps(m, ensure_ascii=False) for m in ALL)
opens =', '.join(str(k) for k in opens_at)

HEADER=(f'const METER=[{meters}], MAXW=7, NMOT={nMot}, NPIPE={nPipe}, NOPEN={nOpen},'
        f' NCLO={nClo}, NFRO={nFro}, OPENM=new Set([{opens}]), N=METER.length;')
H=re.sub(r'const METER=\[.*?N=METER\.length;', lambda _: HEADER, H, count=1, flags=re.S)

H=re.sub(r"const stage=document\.getElementById\('stage'\)[\s\S]*?;\n",
 "const stage=document.getElementById('stage'), fig=document.getElementById('fig'),\n"
 "      ow=document.getElementById('ow'), pw=document.getElementById('pw'),\n"
 "      mw=document.getElementById('mw');\n", H, count=1)

RENDER = """function showFig(wrap, active, step){
 if(!wrap) return;
 const svg=wrap.querySelector('svg'), cum=!svg||svg.dataset.cum!=='0';
 wrap.querySelectorAll('.pp-g').forEach(g=>{
   const s=+g.dataset.step;
   g.classList.toggle('on', active && (cum ? s<=step : s===step));
 });
}
function render(){
 document.querySelectorAll('.is-new').forEach(el=>el.classList.remove('is-new'));
 const fro = i < NFRO,
       mot = !fro && i < NFRO+NMOT,
       pipe = !fro && !mot && i < NFRO+NMOT+NPIPE,
       opening = !fro && !mot && !pipe && i < NFRO+NMOT+NPIPE+NOPEN,
       closing = i >= N-NCLO && NCLO>0;
 if(fw) fw.classList.toggle('off', !fro);
 if(mw) mw.classList.toggle('off', !mot);
 if(cw) cw.classList.toggle('off', !closing);
 pw.classList.toggle('off', !pipe);
 ow.classList.toggle('off', !opening);
 fig.classList.toggle('off', fro||mot||pipe||opening||closing);
 if(fw) fw.querySelectorAll('svg').forEach((el,k)=>el.classList.toggle('on', fro && k===i));
 showFig(mw, mot, i-NFRO);
 showFig(cw, closing, i-(N-NCLO));
 showFig(pw, pipe, i-NFRO-NMOT);
 for(let k=0;k<NOPEN;k++)
   document.getElementById('o'+k).classList.toggle('on', opening && k===i-NFRO-NMOT-NPIPE);
 if(!fro && !mot && !pipe && !opening && !closing){
   const j=i-NFRO-NMOT-NPIPE-NOPEN;
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
 hint.style.display = (i>=NFRO+NMOT+NPIPE+NOPEN && !closing && !insp.classList.contains('on')) ? '' : 'none';
}
"""
H=re.sub(r'(function showFig\(wrap[\s\S]*?\n\}\n)?function render\(\)\{[\s\S]*?\n\}\n',
         lambda _: RENDER, H, count=1)

open('chain-build.html','w',encoding='utf-8').write(H)
print(f'\ndriver: {len(ALL)} frames  ({nFro} front, {nMot} motivation, {nPipe} pipeline,'
      f' {nOpen} opening, {len(ALL)-nFro-nMot-nPipe-nOpen-nClo} chain, {nClo} closing)'
      f'  |  warm meters at {opens_at}')
print(f'chain-build.html  {len(H.encode())//1024} KB')
