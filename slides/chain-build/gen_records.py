# -*- coding: utf-8 -*-
"""Two opening frames, rendered as the records themselves: how a MathClaim is
made, and what a Lamport proof looks like. Both verbatim from the repo."""
import json, glob, textwrap
R='/Users/Yingjian/Documents/GitHub/AgtXIv/'
INK='#1A1A16'; LIGHT='#8A8A80'; OPEN='#8C4A2F'

def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

BOTTOM=1000     # keep clear of the meter line at the foot of the slide

def fit(lines, y0, lh, fs):
    """Shrink the line height, then the type, until the last line is inside
    the frame. Nothing may be clipped - a record that runs off the bottom is
    a record the audience cannot check."""
    T=sum(1 for k,_ in lines if k not in ('rule','gap'))
    G=sum(1 for k,_ in lines if k=='gap'); R=sum(1 for k,_ in lines if k=='rule')
    need=lambda lh: y0 + T*lh + G*0.55*lh + R*18
    while need(lh) > BOTTOM:
        if lh > fs*1.32: lh -= 0.5
        else: fs -= 0.5; lh = fs*1.36
    return round(lh,1), round(fs,1)

COL=440          # where the value column starts, relative to x0

def frame(lines, out, W=1920, H=1040, x0=150, y0=110, lh=38, fs=25):
    lh, fs = fit(lines, y0, lh, fs)
    o=[f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="background:#fff">',
       f'<style>.k{{font-family:Calibri,Carlito,sans-serif;font-size:{fs}px;fill:{LIGHT}}}'
       f'.v{{font-family:Calibri,Carlito,sans-serif;font-size:{fs}px;fill:{INK}}}'
       f'.w{{font-family:Calibri,Carlito,sans-serif;font-size:{fs}px;fill:{INK};font-weight:700}}'
       f'.r{{stroke:{INK};stroke-width:1.2}}</style>']
    y=y0
    for kind,text in lines:
        if kind=='rule':
            o.append(f'<line class="r" x1="{x0}" y1="{y-12}" x2="{W-x0}" y2="{y-12}"/>'); y+=18; continue
        if kind=='gap': y+=lh*0.55; continue
        if kind=='kv':
            k,v = text
            o.append(f'<text class="k" x="{x0}" y="{y}">{esc(k)}</text>')
            o.append(f'<text class="v" x="{x0+COL}" y="{y}" xml:space="preserve">{esc(v)}</text>')
            y+=lh; continue
        cls={'k':'k','v':'v','w':'w'}[kind]
        o.append(f'<text class="{cls}" x="{x0}" y="{y}" xml:space="preserve">{esc(text)}</text>'); y+=lh
    o.append('</svg>')
    open(out,'w').write('\n'.join(o))
    assert y <= BOTTOM+lh, f'{out} still overflows: last line at {y:.0f}'
    return lh, fs, y

# ---------- 1. how a MathClaim is made ----------
# THE SAME THEOREM THE CHAIN ENDS AT. The interesting content is not the
# statement, it is structured_statement: the paper writes one sentence, and the
# record has to name four quantifiers (three of which the sentence never
# writes), two stated assumptions, one assumption that appears only in the
# proof, and a convention about the empty clique.
recs=[json.loads(l) for l in open(R+'Stabilizerness/MathClaimIRRegistry/claims/graph-theoretic-nonstabilizerness.jsonl') if l.strip()]
r=next(x for x in recs if x['claim']['id'].endswith('closed-form-equality'))
ss=r['structured_statement']; src=r.get('source',{})
qs=ss['quantifiers']
nimp=sum(1 for q in qs if q['origin']=='SOURCE_IMPLICIT')
impv=', '.join(q['variable_latex'].replace('\\mathcal{M}','M') for q in qs if q['origin']=='SOURCE_IMPLICIT')
expv=', '.join(q['variable_latex'].replace('\\rho','rho') for q in qs if q['origin']=='SOURCE_EXPLICIT')

L=[('k','math-claim-ir  \u00b7  the theorem this chain ends at'),('gap',''),
   ('kv',('claim.id','closed-form-equality')),
   ('kv',('statement_kind', str(r.get('statement_kind')))),
   ('kv',('source.occurrence_work', str(src.get('occurrence_work')))),('gap',''),
   ('k','as the paper states it'),
   ('v','   RoM_M(rho) = max( 1, max_Q sum_{P in Q} |tr(P rho)| )'),('gap',''),
   ('rule',''),
   ('k','structured_statement  \u2014  what that one sentence actually contains'),('gap',''),
   ('kv',('assumptions.explicit','M has no active dependencies')),
   ('kv',('','G_M is perfect')),
   ('kv',('assumptions.source_implicit','m >= 1     found in the PROOF, not the statement')),
   ('kv',('quantifiers', f'{len(qs)}  \u2014  {nimp} SOURCE_IMPLICIT ({impv}),  1 SOURCE_EXPLICIT ({expv})')),
   ('kv',('local_binders','Q over Cliques(G_M)')),
   ('kv',('conventions', ss['conventions'][0])),
   ('kv',('conclusion','RoM_M(rho) = max{ 1, max_{Q in Cliques(G_M)} sum_{P in Q} |tr(P rho)| }')),('gap',''),
   ('rule',''),
   ('kv',('normalization.relation_to_source', r['normalization']['relation_to_source'])),
   ('kv',('normalization.unresolved_symbols','[ ]     nothing left unresolved')),('gap',''),
   ('kv',('claim.content_hash', r['claim']['content_hash'][:40]+'\u2026')),
   ('kv',('semantic_content_hash', r['semantic_content_hash'][:40]+'\u2026')),
   ('kv',('artifact.artifact_hash', r['artifact']['artifact_hash'][:40]+'\u2026')),('gap',''),
   ('rule',''),
   ('w','one sentence in the paper. four quantifiers, three assumptions and a convention in the record.'),
  ]
_lh,_fs,_y=frame(L,'frames/rec-mathclaim.svg')
REC_JSON={'mathclaim':{'lines':L,'lh':_lh,'fs':_fs,'x0':150,'y0':110,'last':_y,'col':COL}}
print('mathclaim frame:', r['claim']['id'])
print(f'  fitted: lh={_lh} fs={_fs} last line at y={_y:.0f}')

# ---------- 2. the Lamport proof from the real run ----------
f=glob.glob(R+'schema v0.3/runs/proof-worker-normalization-attempt02-20260919/attempts/*/lamport.json')[0]
d=json.load(open(f))
L=[('k','lamport.json  ·  the structured proof the model returned'),('gap','')]
for s in d['lamport_steps']:
    for i,seg in enumerate(textwrap.wrap(s, 76)):
        L.append(('v',('  ' if i==0 else '     ')+seg))
L+=[('gap',''),('rule',''),('k','alignment_notes')]
for n in d['alignment_notes']:
    for i,seg in enumerate(textwrap.wrap(n, 74)):
        L.append(('v',('  · ' if i==0 else '    ')+seg))
L+=[('gap',''),('k','remaining_obligations')]
for n in d['remaining_obligations']:
    for i,seg in enumerate(textwrap.wrap(n, 74)):
        L.append(('w',('  · ' if i==0 else '    ')+seg))

# AND WHAT THE HOST DID NEXT. The obligation above says no Lean was run - true
# at the moment the model wrote the record, and false a few seconds later.
# Showing only the first half put "no Lean execution was performed" on the same
# frame as a meter claiming the proof was kernel-checked.
led=json.load(open(R+'schema v0.3/runs/proof-worker-normalization-attempt02-20260919/ledger.json'))
res=led['proof_attempts'][0]['result']; ar=res['audit_record']
L+=[('gap',''),('rule',''),
    ('k','ledger.json  \u00b7  and what the host did next'),('gap',''),
    ('kv',('result.kernel_checked', str(ar['kernel_checked']).lower())),
    ('kv',('audit_record.declaration', ar['declaration'])),
    ('kv',('audit_record.axioms', ', '.join(ar['axioms']))),
    ('kv',('result.lean_source', f"{res['lean_source']['byte_size']} bytes")),('gap',''),
    ('w','the obligation above was outstanding when the model wrote it.'),
    ('w','the host then elaborated the terms and the kernel accepted them.')]

_lh,_fs,_y=frame(L,'frames/rec-lamport.svg', lh=34, fs=23)
REC_JSON['lamport']={'lines':L,'lh':_lh,'fs':_fs,'x0':150,'y0':110,'last':_y,'col':COL}
print(f'  lamport fitted:   lh={_lh} fs={_fs} last line at y={_y:.0f}')
json.dump(REC_JSON, open('records-geom.json','w'))
print('lamport frame:', len(d['lamport_steps']), 'steps,', len(d['alignment_notes']), 'alignment notes')
print('geometry export:', {k:len(v['lines']) for k,v in REC_JSON.items()}, 'lines')
