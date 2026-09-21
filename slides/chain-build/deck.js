const pptxgen = require('pptxgenjs');
const fs = require('fs');

/* Figure-only slides. No title, no caption - every explanation lives in the
   speaker notes, so the projected frame is nothing but nodes and dependencies.

   EDITABLE. Everything here except the two large extracted-graph frames is
   drawn as native PowerPoint shapes and text boxes, generated from the same
   geometry the web page uses, so the deck and the page cannot drift and every
   element can be selected, moved, recoloured or retyped in PowerPoint. The
   613- and 74-node scatters stay images: several hundred marks each, where a
   flattened picture is the honest format and nothing is gained by shipping
   600 selectable dots. */

const INK='1A1A16', LIGHT='8A8A80', OPEN='8C4A2F', WHITE='FFFFFF', MONO='Calibri';
/* the deck's third and last reserved hue, meaning only: A JUNCTION, NOT A CLAIM. */
const JUNC='1F6F78';
/* COLOUR = WHICH PAPER THIS CAME FROM - the seminar deck's palette, adopted
   verbatim so chain-build and 2026-09-22-talk encode provenance identically. */
const SRCLINE={'#2a78d6':'2A78D6','#1baf7a':'1BAF7A','#eda100':'EDA100',
               '#e87ba4':'E87BA4','#008300':'008300','#4a3aa7':'4A3AA7'};
const SPACE_EM=0.2256;   // Calibri space width, for listing indentation
const W=13.333, H=7.5;

/* PowerPoint line strokes take no alpha channel, so an SVG opacity becomes a
   lighter ink mixed against the white page. Exact, and it stays editable. */
function hex6(c){
  if (!c) return null;
  let h=String(c).replace('#','').toUpperCase();
  if (h.length===3) h=h[0]+h[0]+h[1]+h[1]+h[2]+h[2];   // #fff is not a valid pptx colour
  return h;
}
function blend(hex, a){
  const n=parseInt(hex,16), r=(n>>16)&255, g=(n>>8)&255, b=n&255;
  const m=v=>Math.round(a*v+(1-a)*255).toString(16).padStart(2,'0');
  return (m(r)+m(g)+m(b)).toUpperCase();
}

/* Two coordinate frames, both anchored on the 1920-wide stage the page uses.
   PIPE fills the slide edge to edge; FIG leaves room for the meter line. */
const PIPE={x0:0,    y0:0,    s:13.333/1920};
const FIG ={x0:0.48, y0:0.10, s:6.70/1040};
const X=(f,p)=>f.x0+p*f.s, Y=(f,p)=>f.y0+p*f.s, L=(f,p)=>p*f.s, PT=(f,p)=>p*f.s*72;

/* --- primitives ------------------------------------------------------- */
function rect(s,f,o){
  s.addShape('rect',{x:X(f,o.x), y:Y(f,o.y), w:L(f,o.w), h:L(f,o.h),
    fill: o.fill?{color:o.fill}:{type:'none'},
    line:{color:o.color||INK, width:PT(f,o.lw==null?2:o.lw),
          dashType:o.dash?'dash':'solid'}});
}
function seg(s,f,o){
  /* Always emitted with a non-negative extent so the arrowhead lands on the
     end we asked for; PowerPoint flips a negative-extent line and takes the
     arrow with it. */
  let {x1,y1,x2,y2}=o, beg=false;
  if (x2<x1 || y2<y1){ [x1,y1,x2,y2]=[x2,y2,x1,y1]; beg=true; }
  const ln={color:o.color||INK, width:PT(f,o.lw==null?2:o.lw),
            dashType:o.dash?'dash':'solid'};
  if (o.arrow) ln[beg?'beginArrowType':'endArrowType']='triangle';
  s.addShape('line',{x:X(f,x1), y:Y(f,y1), w:L(f,x2-x1), h:L(f,y2-y1), line:ln});
}
function oval(s,f,o){
  s.addShape('ellipse',{x:X(f,o.cx-o.r), y:Y(f,o.cy-o.r), w:L(f,2*o.r), h:L(f,2*o.r),
    fill: o.fill?{color:o.fill}:{type:'none'},
    line:{color:o.color||INK, width:PT(f,o.lw==null?2:o.lw),
          dashType:o.dash?'dash':'solid'}});
}
function mark(s,f,o){           // a node: one of the five kind presets
  s.addShape(o.preset,{x:X(f,o.x), y:Y(f,o.y), w:L(f,o.w), h:L(f,o.h),
    fill: o.fill?{color:o.fill}:{color:WHITE},
    line:{color:o.color||INK, width:PT(f,o.lw)}});
}
/* baseline: SVG anchors text on the baseline, PowerPoint on the box top.
   Calibri puts the baseline ~0.91em below the top of the line box. */
function tx(s,f,o){
  const fs=o.size, top=o.base? o.y-fs*0.91 : o.y;
  const w=o.w;
  const x = o.align==='c' ? o.cx-w/2 : o.align==='r' ? o.cx-w : o.x;
  s.addText(o.t,{x:X(f,x), y:Y(f,top), w:L(f,w), h:L(f,fs*1.7), isTextBox:true,
    margin:0, valign:'top',
    align: o.align==='c'?'center' : o.align==='r'?'right' : 'left',
    fontFace:MONO, fontSize:PT(f,fs), color:o.color||INK, bold:!!o.bold,
    charSpacing:o.track?PT(f,fs)*o.track:0});
}
function curve(s,f,pts,o){      // a freeform through cubic control points
  s.addShape('custGeom',{x:X(f,o.bx), y:Y(f,o.by), w:L(f,o.bw), h:L(f,o.bh),
    points:pts, fill:{type:'none'},
    line:{color:o.color||INK, width:PT(f,o.lw), dashType:o.dash?'dash':'solid'}});
}

/* ====================================================================== */
/* 1. THE HAND-BUILT FIGURES - one primitive list per figure, drawn native */
/* ====================================================================== */
const PP=JSON.parse(fs.readFileSync('pipeline.json','utf8'));
const MO=fs.existsSync('motivation.json')
  ? JSON.parse(fs.readFileSync('motivation.json','utf8')) : null;
const CL=fs.existsSync('closing.json')
  ? JSON.parse(fs.readFileSync('closing.json','utf8')) : null;
const FR=fs.existsSync('front.json')
  ? JSON.parse(fs.readFileSync('front.json','utf8')) : null;

function prims(s, FIGURE, step){
  const cum = FIGURE.cumulative !== false;   // a build-up, or six separate pictures
  for (const p of FIGURE.prims){
    if (cum ? p.step>step : p.step!==step) continue;
    const dim = p.dim===true;
    const col = hex6(p.color) || INK;
    if (p.t==='box')  rect(s,PIPE,{x:p.x,y:p.y,w:p.w,h:p.h,color:col,lw:p.lw,
        dash:p.style==='dash', fill:hex6(p.fill)});
    else if (p.t==='line') seg(s,PIPE,{x1:p.x1,y1:p.y1,x2:p.x2,y2:p.y2,
        color: dim?blend(INK,.13):col, lw:p.lw, dash:p.style==='dash', arrow:p.arrow});
    else if (p.t==='curve') cubic(s, p.x1,p.y1, p.c1x,p.c1y, p.c2x,p.c2y, p.x2,p.y2,
        {color: hex6(p.color)||INK, lw:p.lw}, PIPE);
    else if (p.t==='mark') mark(s,PIPE,{x:p.x,y:p.y,w:p.w,h:p.h,preset:p.preset,
        fill: hex6(p.fill)||WHITE, color:col, lw:p.lw});
    else if (p.t==='dot')  oval(s,PIPE,{cx:p.cx,cy:p.cy,r:p.r,
        fill: hex6(p.fill)||WHITE,
        color: dim?blend(INK,.13):col, lw:p.lw});
    else tx(s,PIPE,{x:p.x,y:p.y,w:p.w,size:p.size,t:p.text,color:col,align:'l',bold:p.bold});
  }
}

/* ====================================================================== */
/* 2. THE TWO RECORDS - real repo artifacts, as live text                  */
/* ====================================================================== */
const RECG=JSON.parse(fs.readFileSync('records-geom.json','utf8'));
/* warm is reserved for NOT FROM THIS PAPER. An outstanding obligation is not
   an external source, so the emphasis line takes weight, not hue. */
const RCOL={k:LIGHT, v:INK, w:INK};
function record(s, key){
  const g=RECG[key]; let y=g.y0;
  for (const [kind,t] of g.lines){
    if (kind==='rule'){ seg(s,FIG,{x1:g.x0,y1:y-12,x2:1920-g.x0,y2:y-12,lw:1.2}); y+=18; continue; }
    if (kind==='gap'){ y+=g.lh*0.55; continue; }
    /* Leading spaces become a real x offset. PowerPoint collapses leading
       whitespace in a run, so indentation carried as spaces does not survive;
       carried as a position it does, and it stays aligned when the text is
       retyped. */
    if (kind==='kv'){                       // key at the margin, value at the column
      const [k,v]=t;
      if (k) tx(s,FIG,{x:g.x0, y, w:g.col-10, size:g.fs, t:k, color:LIGHT, align:'l', base:true});
      const ind=(v.match(/^ */)||[''])[0].length;
      tx(s,FIG,{x:g.x0+g.col+ind*g.fs*SPACE_EM, y, w:1920-g.x0-g.col-80, size:g.fs,
                t:v.slice(ind), color:INK, align:'l', base:true});
      y+=g.lh; continue;
    }
    const ind=(t.match(/^ */)||[''])[0].length;
    tx(s,FIG,{x:g.x0+ind*g.fs*SPACE_EM, y: y, w:1920-2*g.x0, size:g.fs, t:t.slice(ind),
              color:RCOL[kind]||INK, align:'l', base:true, bold:kind==='w'});
    y+=g.lh;
  }
}

/* ====================================================================== */
/* 3. THE REDUCTION - 240 candidates, 14 that land on a declared result    */
/* ====================================================================== */
const RG=JSON.parse(fs.readFileSync('reduced-geom.json','utf8'));
function cubic(s, x1,y1, c1x,c1y, c2x,c2y, x2,y2, o, f){
  f = f || FIG;
  const bx=Math.min(x1,c1x,c2x,x2), by=Math.min(y1,c1y,c2y,y2);
  const bw=Math.max(x1,c1x,c2x,x2)-bx, bh=Math.max(y1,c1y,c2y,y2)-by;
  curve(s,f,[{x:L(f,x1-bx),y:L(f,y1-by)},
             {x:L(f,x2-bx),y:L(f,y2-by),curve:{type:'cubic',
               x1:L(f,c1x-bx),y1:L(f,c1y-by),x2:L(f,c2x-bx),y2:L(f,c2y-by)}}],
        {bx,by,bw:bw||1,bh:bh||1,...o});
}
function reduced(s){
  for (const a of RG.attr)                       // candidate -> declared result
    cubic(s,a.x1,a.y1,a.x1,a.ym,a.x2,a.ym,a.x2,a.y2,
          {color:blend(LIGHT,.5),lw:1.2,dash:true});
  for (const e of RG.edges)                      // dependencies that survive
    cubic(s,e.x1,e.y1,e.x1,e.ym,e.x2,e.ym,e.x2,e.y2,{color:blend(INK,.55),lw:1.8});
  for (const c of RG.cands) oval(s,FIG,{cx:c.cx,cy:c.cy,r:c.r,fill:WHITE,lw:2});
  for (const e of RG.envs){
    mark(s,FIG,{x:e.x,y:e.y,w:e.w,h:e.h,preset:e.preset,fill:WHITE,lw:2.6});
    tx(s,FIG,{cx:e.cx,y:e.cy+e.dy,w:300,size:21,t:e.lab,align:'c',base:true});
    tx(s,FIG,{cx:e.cx,y:e.cy+e.dy+24,w:300,size:17,t:e.kind,color:LIGHT,align:'c',base:true});
  }
  for (const r of RG.rows)
    tx(s,FIG,{x:r.x,y:r.y,w:1200,size:20,t:r.t,color:LIGHT,align:'l',base:true,track:.08});
}

/* ====================================================================== */
/* 4. THE CHAIN - 29 claims, 20 AND-groups, eleven construction steps      */
/* ====================================================================== */
const CG=JSON.parse(fs.readFileSync('chain-geom.json','utf8'));
function chain(s, step){
  const phase = step===8?'roots' : step===9?'form' : step===10?'stuck' : 'build';
  const upto  = phase==='build' ? step : CG.maxw;

  if (CG.key){                                   // the source key
    const K=CG.key;
    tx(s,FIG,{x:K.x,y:K.y,w:300,size:17,t:K.head,color:LIGHT,align:'l',base:true,track:.14});
    for (const it of K.items){
      const c = it.c ? (SRCLINE[it.c]||INK) : INK;
      oval(s,FIG,{cx:it.x+7,cy:28,r:7,fill:it.c?c:WHITE,color:c,lw:2});
      tx(s,FIG,{x:it.x+22,y:K.y,w:320,size:17,t:it.t,align:'l',base:true});
    }
  }
  for (const g of CG.guides){                    // layer rules
    seg(s,FIG,{x1:g.x1,y1:g.y,x2:g.x2,y2:g.y,color:blend(INK,.09),lw:1});
    tx(s,FIG,{cx:102,y:g.y+6,w:120,size:17,t:g.lab,color:LIGHT,align:'r',base:true,track:.14});
  }
  for (const g of CG.groups){                    // the AND junctions
    if (g.wave>upto) continue;
    const isnew = phase==='build' && step>=2 && g.wave===upto;
    const a = phase!=='build' ? .12 : null;
    /* one curve per member into the junction - the seminar deck's bezier,
       vertical control points at the midpoint */
    for (const [mx,my,src] of g.legs){
      const base = src ? (SRCLINE[src]||INK) : INK;
      const col  = a!=null ? blend(base,a) : blend(base, src? .60 : .34);
      cubic(s, mx,my, mx,(my+g.bar)/2, g.tx,(my+g.bar)/2, g.tx,g.bar,
            {color:col, lw: isnew?2.2:1.2});
    }
    const jc = a!=null ? blend(INK,a) : INK;
    oval(s,FIG,{cx:g.tx,cy:g.bar,r:g.jr,fill:WHITE,color:jc,lw:isnew?2.8:2});
    seg(s,FIG,{x1:g.tx-6,y1:g.bar,x2:g.tx+6,y2:g.bar,color:jc,lw:1.8});
    seg(s,FIG,{x1:g.tx,y1:g.bar-6,x2:g.tx,y2:g.bar+6,color:jc,lw:1.8});
    seg(s,FIG,{x1:g.tx,y1:g.bar-g.jr,x2:g.tx,y2:g.ty+g.tr+3,
               color: a!=null?blend(INK,a):blend(INK,.9), lw:isnew?2.8:2.2, arrow:true});
  }
  for (const n of CG.nodes){                     // the claims
    if (n.wave>upto) continue;
    const src = n.src ? (SRCLINE[n.src]||INK) : null;
    let color = src || INK, lw = n.th?3.2:2.1, fill=WHITE, ring=null;
    if (phase==='build'){
      if (step>=2 && n.wave===upto){ lw=3.6; ring={color:blend(INK,.3), lw:2.6}; }
    } else if (phase==='roots'){
      if (n.root){ lw = src?3.8:3.4; ring={color, lw:2.6, dash:true}; }
      else color=blend(color,.14);
    } else if (phase==='form'){
      if (n.form) fill=INK; else color=blend(color,.14);
    } else {
      if (n.form) color=blend(color,.14);
      else if (src){ lw=3.8; ring={color, lw:2.5, dash:true}; }
      else lw = n.th?4:2.8;
    }
    if (ring) oval(s,FIG,{cx:n.cx,cy:n.cy,r:n.r+9,color:ring.color,lw:ring.lw,dash:ring.dash});
    mark(s,FIG,{x:n.x,y:n.y,w:n.w,h:n.h,preset:n.preset,fill:fill===INK?INK:WHITE,color,lw});
  }
  for (const l of CG.labels){                    // the six named claims
    if (l.wave>upto) continue;
    const w=520, al = l.an==='end' ? 'r' : l.an==='middle' ? 'c' : 'l';
    tx(s,FIG,{x:l.x, cx:l.x, y:l.y, w, size:22, t:l.t, align:al, base:true});
  }
}

/* ====================================================================== */
/* the deck                                                                */
/* ====================================================================== */
const SLIDES=[];
function addFigure(F){
  if (!F) return 0;
  F.meter.forEach((m,k)=>SLIDES.push({draw:s=>prims(s,F,k), meter:m, open:F.open[k], note:F.note[k]}));
  return F.meter.length;
}
const N_FRO  = addFigure(FR);      // the background: the crisis, the model, the stack
const N_MOT  = addFigure(MO);      // why any of this matters - before anything technical
const N_PIPE = addFigure(PP);      // the whole thing in five boxes

SLIDES.push({draw:s=>record(s,'mathclaim'),
  meter:'ONE MATH CLAIM  ·  NORMALIZED, HASHED, ANCHORED',
  note:`How the schema turns one sentence of a paper into a MathClaim - and deliberately the SAME theorem this deck spends its last eleven frames building the chain for. The registry holds 25 such records for this paper; this is the headline one.

Read the middle block. The paper states the closed form in a single line. The record has to say what that line actually contains: two assumptions the paper states (no active dependencies, G_M perfect), FOUR quantifiers of which THREE are marked SOURCE_IMPLICIT - n, m and M are never quantified in the sentence - a local binder for Q over the cliques, and a convention that the empty clique counts as zero.

And one line worth stopping on: assumptions.source_implicit, m >= 1, anchored to the PROOF rather than the statement. The paper uses a hypothesis in its proof that its theorem does not state. That is not a criticism of the paper; every paper does it. It is the thing a reader has to reconstruct by hand, and it is exactly what this record exists to make mechanical.

Three separate hashes, differing on purpose: re-wording the statement changes one and not the others.

A caution if asked: this registry id (closed-form-equality) and the chain's id (claim:closed-form-rom) are different identifiers in different files. They are the same mathematics, not the same record.

Source: Stabilizerness/MathClaimIRRegistry/claims/graph-theoretic-nonstabilizerness.jsonl`});

SLIDES.push({draw:s=>record(s,'lamport'),
  meter:'ONE LAMPORT PROOF  ·  WHAT THE MODEL RETURNED, THEN WHAT THE HOST DID',
  note:`A Lamport-style structured proof: hierarchically numbered steps, each one checkable on its own, rather than a paragraph of prose.

This is the real artifact from the one end-to-end run that worked - 1 model call, and the Lean it produced was accepted by the kernel using the audited library theorem AgtXIv.RoM.normalized_l1.

READ THE TWO HALVES IN ORDER, because they look like a contradiction and are not. The model's record ends with remaining_obligations: "no Lean execution was performed" - which was true at the moment it wrote it. The ledger below records what happened next: the host elaborated the proposed terms, Lean accepted the declaration AgtXIv.Generated.Proof_a29f133fb6f82da97507, and the audit shows it resting on the three standard axioms and nothing else.

That sequence is the point. A record is a snapshot carrying its own outstanding obligations; the ledger is the account of which ones were then discharged. Neither alone tells you the state - and a deck that showed only the first half would be claiming the opposite of what it meant.

Note what else travels with it. alignment_notes record what the formal statement does and does NOT assert ("no nonnegativity or nonempty-index assumption is added"; "does not assert primal feasibility or strong duality"). remaining_obligations records what was still pending at that point. The proof does not arrive alone - it arrives with its own caveats attached.

Source: schema v0.3/runs/proof-worker-normalization-attempt02-20260919/attempts/*/lamport.json`});

SLIDES.push({img:'frames/open00.png', a:3000/1623,
  meter:'613 NODES  ·  634 DEPENDENCIES  ·  ONE PASS OVER ONE PAPER',
  note:`What you get when you ask a machine to extract every mathematical claim in one paper and every dependency between them: 613 nodes, 634 edges, assembled from the frozen bytes of arXiv:2607.26154v1 without using any hand-authored graph (legacy_dag_edges_used: false).

Shape = node kind, as in the seminar deck. Everything is hollow because v0.3 has no accepted state to fill a mark with: accepted_support_edges is 0.

This frame and the next two extracted-graph frames are images rather than shapes - several hundred marks each, where a flattened picture is the honest format.

Source: schema v0.3/runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json`});

SLIDES.push({img:'frames/open01.png', a:3000/1623, open:true,
  meter:'240 FROM THE TARGET PAPER  ·  373 EVERYTHING ELSE',
  note:`The same graph, two colours.

INK - the 240 candidate statements actually extracted from the target paper's own .tex. These carry a paper_id.
WARM - the other 373: 152 external claim requests (anchored to a .bbl byte range, paper_id null - nobody has fetched the source yet) and 221 unresolved source occurrences (a location in the paper no candidate has yet claimed).

The point of the colour split: most of this graph is not knowledge, it is the system's own record of what it has not done. Computed connectivity: 80 weakly connected components, largest 379 nodes, 24 isolated, and the digraph is NOT acyclic - 7 simple cycles.`});

SLIDES.push({draw:reduced,
  meter:'14 OF THE 240 LAND ON A RESULT THE PAPER DECLARES  ·  9 OF 9 HIT',
  note:`THE REDUCTION, and it is mechanical - no model judgement anywhere in it.

The host reads the frozen .tex and takes the byte range of every \\begin{theorem}...\\end{theorem} and its siblings. The paper declares NINE formal results: 2 theorems, 3 lemmas, 3 propositions, 1 definition, each with its own \\label. Then it asks which of the 240 extraction candidates have a source span falling inside one.

Answer: 14 candidates, hitting 9 of 9 - so nothing the paper formally declares was missed - and 8 of the dependency edges survive among them. The other 226 candidates are assertions in running prose, where "is this a claim?" is a judgement rather than a fact.

WHAT THIS IS NOT. It does not delete the 226 and it asserts nothing about them; many are load-bearing (the curated registry holds 25, not 9). It is a mechanical attribution, fully reversible, and it is the cheapest honest cut available: from 240 unreviewed candidates to the 9 results the paper itself chose to state formally.

Counts computed live from draft.tex and graphs/00001-db0e3d21/graph.json.`});

SLIDES.push({img:'frames/open02.png', a:3000/1623,
  meter:'A DIFFERENT OBJECT  ·  74 CLAIMS, AUTHORED BY HAND',
  note:`IMPORTANT - this is a CHANGE OF OBJECT, not a zoom.

This is the paper's hand-authored dependency DAG: 74 claim nodes, 129 edges, one connected structure, acyclic because a person made it so.

It is NOT a subgraph of the previous slide, and the deck must never imply that it is. The two graphs share ZERO node ids (extracted ids look like claim:candidate:51e98811..., authored ids like claim:closed-form-rom). I also tested correspondence by source location - converting the authored line anchors to byte ranges and intersecting them with the extracted spans - and it is far too coarse to be an extraction: 436 of 458 extracted candidates overlap SOME authored claim, 224 overlap this theorem's chain. So no clean subgraph exists.

Say it plainly if asked: the machine's reading and the human's reading of the same paper are two different objects, and neither is derived from the other.

Source: Stabilizerness/dag/claim-dag.json`});

SLIDES.push({img:'frames/open03.png', a:3000/1623,
  meter:'29 OF 74  ·  THE CLOSURE OF ONE THEOREM',
  note:`THIS extraction is real, and verified: the 29 node ids of the closure are a strict subset of the 74 authored ids (checked in code - the build asserts it).

Ink = the backward closure of the main theorem (the closed form for reduced robustness of magic). Ghosted = the other 45 claims of the paper, which include five further external roots, the whole empirical branch behind Figure 2, three open problems and two stated limitations.

So: the figure everything after this is built on covers 29 of the paper's 74 claims - 39%. A closure answers "what does this theorem rest on", not "what is in this paper".

ONE EDGE OF BOOKKEEPING, in case somebody counts the lines. The ink edges here are the AUTHORED DAG restricted to these 29 claims, and there are 45 of them. From the next frame on, the deck draws the v0.3 pruned branch artefact, which has 46 - it carries no-active-free-signs -> sign-alignment-identity, an edge the hand-authored graph does not. Same 29 nodes, one more edge. Both drawings are faithful to their own source; they are two readings of one closure, a version apart.`});

const CHAIN = [
  ['1 CLAIM',
   'Start at the theorem: claim:closed-form-rom. Nothing under it yet.\n\nThe unit of construction here is the SUPPORT GROUP - an AND-set of premises that together discharge one target - not the individual edge. closed-form-branch.json records 20 such groups over the 29 claims.'],
  ['4 CLAIMS  ·  1 AND-GROUP',
   'The theorem’s support group opens: exact-graph-program, perfect-graph-antiblocker and perfect-graph-definition.\n\nDrawn as a bracket rather than three separate edges, because it is an AND: all three must hold. Any one missing and the target is not discharged. That is why the bracket, not the arrows, is the right primitive.'],
  ['7 CLAIMS  ·  3 GROUPS',
   'The same question is now asked of each premise: what discharges this? Two more groups open underneath.'],
  ['13 CLAIMS  ·  5 GROUPS',
   'The relaxation branch and the antiblocker branch descend separately.\n\nFrom here on, a heavier stroke and a faint ring mark what arrived at THIS step, and the brighter brackets are the groups that just opened. Later steps add only 3, 2 and 1 marks among 26-29, which is otherwise undetectable in a static frame.'],
  ['23 CLAIMS  ·  10 GROUPS',
   'The widest step: ten new claims at once, and three more of the roots arrive together.'],
  ['26 CLAIMS  ·  16 GROUPS', 'Three more, completing the reduced-polytope side.'],
  ['28 CLAIMS  ·  19 GROUPS', 'Two: the full robustness of magic, and the resource theory that defines it.'],
  ['29 CLAIMS  ·  20 GROUPS  ·  NOTHING LEFT TO EXPAND',
   'Twenty-nine claims, twenty support groups. The recursion terminates because every remaining premise is already in the chain.\n\nSay \u201cterminates\u201d, not \u201ccomplete\u201d. The pipeline\u2019s own chain-certificate.json records state CHAIN_INCOMPLETE for this very query, and three frames from now this deck prints that. What has finished is the expansion; what has not is the proof.\n\nWorth saying aloud: it terminates because the input was a closed, hand-authored DAG. Run the same question against the paper itself and it does not terminate - the v0.3 controller stops at a budget limit with 400 roots, 373 of them unfetched requests.'],
  ['9 ROOTS  ·  NOTHING BELOW THEM',
   'Nine claims have NO support group at all - nothing in the chain explains them. They are where the paper stops arguing and starts citing.\n\nSix are imported foundations. Three are the paper’s own definitions that rest on nothing, which is why the DAG has 9 sources rather than 6.'],
  ['FORMALIZATION ORDER  ·  14 OF 29',
   'The system orders the chain for Lean and can reach fourteen of the twenty-nine. formalization_order begins at the MWIS definition, the Pauli window, the perfect-graph definition and finite LP strong duality.\n\nNote the shape: every filled mark sits in the lower-left mass. Nothing near the top is reachable.'],
  ['15 UNREACHABLE  ·  CHAIN_INCOMPLETE',
   'The fifteen the ordering cannot reach - everything downstream of a blocked root, including the theorem itself. Not because the Lean is missing, but because a premise above it has no discharged source.\n\nThe two ringed marks are the CAUSE, and they carry their own source colours - Varela in violet, the perfect-graph duality (Chvatal/Fulkerson) in blue, exactly as in the seminar deck. They are the only two imports outside formalization_order. Computed from closed-form-branch.json, the fifteen break down as 11 blocked by Varela alone, 1 by the perfect-graph root alone, 1 (the theorem) by both, plus the 2 blocked roots themselves. So resolving the Varela citation would return 11 of the 15.\n\nThe chain is complete and the proof is not: mathematical_status CHAIN_INCOMPLETE, accepted_support_edges 0, proof_backend NOT_CONNECTED.'],
];
CHAIN.forEach(([meter,note],k)=>SLIDES.push({
  draw:s=>chain(s,k), meter, note, open:false}));

const N_CLO = addFigure(CL);       // the wish, at the end where it belongs

const p = new pptxgen();
p.layout = 'LAYOUT_WIDE';
p.author = 'Yingjian Liu';
p.title  = 'From a paper to a checked chain';

SLIDES.forEach((sl,i)=>{
  const s=p.addSlide();
  s.background={color:WHITE};
  if (sl.img){
    const availH=H-0.86; let w=W, h=w/sl.a;
    if (h>availH){ h=availH; w=h*sl.a; }
    s.addImage({path:sl.img, x:(W-w)/2, y:0.16, w, h});
  } else sl.draw(s);
  s.addText(sl.meter,{x:0.52, y:H-0.62, w:10.2, h:0.32, isTextBox:true, margin:0, valign:'top',
    fontFace:MONO, fontSize:12, color: sl.open?OPEN:INK, charSpacing:1.4});
  s.addNotes(sl.note);
});

/* The page's driver reads its meters and its region boundaries from here, so
   the deck order is declared exactly once. */
fs.writeFileSync('deck-meters.json', JSON.stringify({
  meter: SLIDES.map(s=>s.meter),
  open:  SLIDES.map(s=>!!s.open),
  nFro:  N_FRO, nMot: N_MOT, nPipe: N_PIPE, nOpen: 7, nClo: N_CLO,
}, null, 1));

p.writeFile({fileName:'chain-build.pptx'}).then(f=>{
  const native=SLIDES.filter(s=>!s.img).length;
  console.log('wrote',f,'·',SLIDES.length,'slides ·',native,'fully editable,',
              SLIDES.length-native,'with an image');
});
