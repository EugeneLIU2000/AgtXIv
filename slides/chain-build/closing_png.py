# -*- coding: utf-8 -*-
"""Bake one closing step into a flat picture, for the slide only.

WHY THIS EXISTS. The closing act's schematic frames are ~90 native shapes each,
and rebuilt natively they kept coming out wrong in PowerPoint in a way neither
LibreOffice nor the browser reproduces, so there was nothing to debug against.
The page keeps the live drawing; the slide gets exactly what the browser draws,
rasterised. Editability is traded away deliberately and only for these frames.

The step groups carry no inline opacity - the page's stylesheet hides all but
the current one - so a standalone SVG has to contain that group and no other.
"""
import re, subprocess, sys, os

SRC='closing.svg'
STEPS=[int(a) for a in sys.argv[1:]] or [1]
svg=open(SRC,encoding='utf-8').read()

# The text elements carry class="pp-t" and get their face from the PAGE's
# stylesheet, which a standalone file does not have - without this rsvg falls
# back to its default serif and the baked frame is the only page in the deck
# set in Times.
STYLE='.pp-t{font-family:Calibri,Carlito,DejaVu Sans,sans-serif}'
head=svg[:svg.index('</defs>')+len('</defs>')]+f'<style>{STYLE}</style>'
groups=dict()
for m in re.finditer(r'<g class="pp-g" data-step="(\d+)">.*?</g>\n?(?=\s*<g class="pp-g"|</svg>)',
                     svg, re.S):
    groups[int(m.group(1))]=m.group(0)
assert groups, 'no step groups found in '+SRC

os.makedirs('frames', exist_ok=True)
for k in STEPS:
    assert k in groups, f'{SRC} has no step {k} (has {sorted(groups)})'
    out=f'frames/closing-step{k}.svg'
    open(out,'w',encoding='utf-8').write(head+groups[k]+'</svg>')
    png=f'frames/closing-step{k}.png'
    subprocess.run(['rsvg-convert','-w','3840','-b','white',out,'-o',png], check=True)
    print(f'  {png}  {os.path.getsize(png)//1024} KB')
