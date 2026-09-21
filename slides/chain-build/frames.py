# -*- coding: utf-8 -*-
"""Bake each construction step into a standalone SVG, then rasterise.
The browser page and these frames are generated from the same chain.svg,
so the deck and the pptx cannot drift apart."""
import json, re, subprocess, os
svg=open('chain.svg',encoding='utf-8').read()
meta=json.load(open('chain-meta.json'))
MAXW=meta['maxw']; ROOTS=set(meta['roots']); FO=set(meta['fo'])

INK='#1A1A16'; LIGHT='#8A8A80'; OPEN='#8C4A2F'; PAPER='#FFFFFF'
# a third reserved hue, and only ever this: THIS IS A JUNCTION, NOT A CLAIM.
JUNC='#1F6F78'
BASE = f"""
/* COLOUR = WHICH PAPER THIS CAME FROM, the seminar deck's own encoding.
   The hue is carried as a presentation ATTRIBUTE on each mark, not by a CSS
   variable: rsvg-convert does not resolve custom properties, so a rule saying
   stroke:var(--src) computes to nothing and the mark falls back to black. So
   no rule below ever sets `stroke` on a node that has a source - it sets only
   width and dash, and lets the attribute supply the colour. */
.ch-guides line{{stroke:{INK};stroke-width:1;opacity:.09}}
.ch-lay{{font-family:Calibri,Carlito,sans-serif;font-size:17px;letter-spacing:.14em;fill:{LIGHT}}}
.ch-keyhead{{font-family:Calibri,Carlito,sans-serif;font-size:17px;letter-spacing:.14em;fill:{LIGHT}}}
.ch-keyt{{font-family:Calibri,Carlito,sans-serif;font-size:17px;fill:{INK}}}
.ch-sw{{stroke-width:2}}
.gcurve{{fill:none;stroke:{INK};stroke-width:1.2;opacity:.34}}
.gcurve.from-chvatal{{stroke:#2a78d6;opacity:.55}}
.gcurve.from-gottesman{{stroke:#1baf7a;opacity:.55}}
.gcurve.from-veitch{{stroke:#eda100;opacity:.6}}
.gcurve.from-howard{{stroke:#e87ba4;opacity:.6}}
.gcurve.from-handbook{{stroke:#008300;opacity:.55}}
.gcurve.from-varela{{stroke:#4a3aa7;opacity:.55}}
.gstem{{stroke:{INK};fill:none;stroke-width:2.2;opacity:.9}}
.gjunc{{fill:{PAPER};stroke:{INK};stroke-width:2}}
.gplus{{stroke:{INK};stroke-width:1.8;fill:none}}
.gand{{font-family:Calibri,Carlito,sans-serif;font-size:15px;fill:{LIGHT};opacity:.9}}
.nmark{{fill:{PAPER};stroke-width:2.1}}
.src-this-paper .nmark{{stroke:{INK}}}
.nring{{fill:none;stroke-width:2.6;opacity:0}}
.src-this-paper .nring{{stroke:{INK}}}
.is-theorem .nmark{{stroke-width:3.2}}
.ch-lab{{font-family:Calibri,Carlito,sans-serif;font-size:22px;fill:{INK}}}
.hide{{display:none}}
.dim{{opacity:.14}}
.root-on .nmark{{stroke-width:3.4}}
.root-on .nring{{opacity:1;stroke-dasharray:6 4}}
.root-on:not(.src-this-paper) .nmark{{stroke-width:3.8}}
.form-on .nmark{{fill:{INK};stroke:{INK}}}
.stuck-on .nmark{{stroke-width:2.8}}
.stuck-on.is-theorem .nmark{{stroke-width:4}}
.stuck-on:not(.src-this-paper) .nmark{{stroke-width:3.8}}
.stuck-on:not(.src-this-paper) .nring{{opacity:1;stroke-width:2.5;stroke-dasharray:6 4}}
.new-on .nmark{{stroke-width:3.6}}
.new-on .nring{{opacity:.3;stroke:{INK}}}
.gnew .gcurve{{opacity:.95;stroke-width:2.2}}
.gnew .gstem{{stroke-width:2.8}}
.gnew .gjunc{{stroke-width:2.8}}
.grp-dim{{opacity:.12}}
"""

def frame(step):
    s=svg
    phase = 'roots' if step==8 else 'form' if step==9 else 'stuck' if step==10 else 'build'
    upto = step if phase=='build' else MAXW
    def node_sub(m):
        whole=m.group(0); cls=m.group(1); wave=int(m.group(2)); nid=m.group(3)
        add=[]
        imp = nid.startswith(('root:','foundation:'))
        if wave>upto: add.append('hide')
        elif phase=='roots':
            add.append('root-on' if nid in ROOTS else 'dim')
            if nid in ROOTS and imp: add.append('imp')
        elif phase=='form':   add.append('form-on' if nid in FO else 'dim')
        elif phase=='stuck':
            add.append('dim' if nid in FO else 'stuck-on')
            if nid not in FO and imp: add.append('imp')
        elif phase=='build' and step>=2 and wave==upto: add.append('new-on')
        return whole.replace(f'class="{cls}"', f'class="{cls} {" ".join(add)}"') if add else whole
    s=re.sub(r'<g class="(ch-node[^"]*)" data-wave="(\d+)" data-id="([^"]+)"[^>]*>', node_sub, s)
    def grp_sub(m):
        whole=m.group(0); wave=int(m.group(1))
        if wave>upto: return whole.replace('class="ch-grp"','class="ch-grp hide"')
        if phase!='build': return whole.replace('class="ch-grp"','class="ch-grp grp-dim"')
        if step>=2 and wave==upto: return whole.replace('class="ch-grp"','class="ch-grp gnew"')
        return whole
    s=re.sub(r'<g class="ch-grp" data-wave="(\d+)">', grp_sub, s)
    def lab_sub(m):
        whole=m.group(0); wave=int(m.group(1))
        return whole.replace('class="ch-lab"','class="ch-lab hide"') if wave>upto else whole
    s=re.sub(r'<text class="ch-lab" data-wave="(\d+)"', lambda m: lab_sub(m), s)
    s=s.replace('<svg class="chain-svg"', f'<svg style="background:{PAPER}"', 1)
    return s.replace('>', f'><style>{BASE}</style>', 1)

os.makedirs('frames', exist_ok=True)
for i in range(11):
    open(f'frames/step{i:02d}.svg','w',encoding='utf-8').write(frame(i))
    subprocess.run(['rsvg-convert','-w','3000','-b','white',
                    f'frames/step{i:02d}.svg','-o',f'frames/step{i:02d}.png'], check=True)
print('rendered 11 frames')
for i in (0,1,7,8,9,10):
    f=f'frames/step{i:02d}.png'
    print(f'  {f}  {os.path.getsize(f)//1024} KB')
