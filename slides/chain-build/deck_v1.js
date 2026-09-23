/* The generated half of aqa_talk_924.pptx.
 *
 * 43 of the deck's 65 frames are drawn by this project; the other 22 are the
 * speaker's own slides and are carried over from Slide_001.pptx unchanged, by
 * merge_pptx.py. This script emits only the 43, in deck order, and writes a
 * manifest saying which position in the final deck each one belongs at.
 *
 * Everything here is native PowerPoint shapes and text - the four extracted-
 * graph frames are the only images, and they are images in the page too.
 */
const C=require('./deck_core');
const {CHAIN,CL,FR,H,INK,LIGHT,MONO,OPEN,OPENING,PP,W,WHITE,chain,pptxgen,
       prims,record,reduced,fs}=C;

const ORD=JSON.parse(fs.readFileSync('order-v1.json','utf8'));
const NEWKEYS=['title','hinge','roadmap','crisisbridge','lean1','lean2','lean3',
               'conclusion','discussion'];
const NATIVE={};                       // the nine frames written for v1
NEWKEYS.forEach(k=>{ NATIVE[k]=JSON.parse(fs.readFileSync(`${k}.json`,'utf8')); });
const BRIDGE=JSON.parse(fs.readFileSync('bridge.json','utf8'));

/* Closing steps the SLIDE takes as a flat picture instead of native shapes.
 * These frames kept coming out wrong in PowerPoint in a way neither the browser
 * nor LibreOffice reproduced, so there was nothing to debug against; the slide
 * now carries exactly what the browser draws. The page is unaffected and stays
 * live. closing_png.py bakes them - keep the two lists in step. */
const FLAT_CLOSING=new Set([1]);

/* v1 frame -> what draws it, or null when the frame is one of the speaker's
   own slides and the merger will supply it from Slide_001.pptx. */
function resolve(reg, step){
  if (reg==='f'){
    if (step<=26) return null;                       // a source slide
    if (step===27) return {fig:BRIDGE, step:0};
    return {fig:NATIVE[NEWKEYS[step-28]], step:0};
  }
  if (reg==='p') return {fig:PP, step};
  if (reg==='z') return FLAT_CLOSING.has(step)
      ? {flat:`frames/closing-step${step}.png`, note:(CL.note||[])[step]||''}
      : {fig:CL, step};
  if (reg==='c') return {chain:step, note:CHAIN[step][1]};
  if (reg==='o') return {open:OPENING[step]};
  throw new Error('unknown region '+reg);
}

const p=new pptxgen();
p.layout='LAYOUT_WIDE';
p.author='Yingjian Liu';
p.title='Some thoughts about LLM for theoretical research';

const manifest=[];
ORD.order.forEach(([reg,step],i)=>{
  const r=resolve(reg,step);
  if (!r){ manifest.push({v1:i, from:'source'}); return; }
  const s=p.addSlide();
  s.background={color:WHITE};
  let note='';
  if (r.flat){
    // the closing figure is authored on the full 1920x1080 stage, so it goes
    // edge to edge rather than through the opening frames' letterboxing
    s.addImage({path:r.flat, x:0, y:0, w:W, h:H});
    note=r.note;
  } else if (r.open){
    const o=r.open;
    if (o.img){
      const availH=H-0.86; let w=W, h=w/o.a;
      if (h>availH){ h=availH; w=h*o.a; }
      s.addImage({path:o.img, x:(W-w)/2, y:0.16, w, h});
    } else o.draw(s);
    note=o.note||'';
  } else if (r.chain!==undefined){
    chain(s, r.chain); note=r.note;
  } else {
    prims(s, r.fig, r.step); note=(r.fig.note||[])[r.step]||'';
  }
  // the page number, in the same corner and the same weight as the page's
  s.addText(String(i+1), {x:0.52, y:H-0.60, w:0.8, h:0.30, isTextBox:true, margin:0,
    valign:'top', fontFace:MONO, fontSize:11, color:LIGHT});
  s.addNotes(note);
  manifest.push({v1:i, from:'generated', gen:manifest.filter(m=>m.from==='generated').length+1,
                 meter:ORD.meter[i]});
});

const nGen=manifest.filter(m=>m.from==='generated').length;
fs.writeFileSync('deck-v1-manifest.json', JSON.stringify(
  {total:ORD.order.length, generated:nGen,
   source:ORD.order.length-nGen, frames:manifest}, null, 1));

p.writeFile({fileName:'aqa-generated.pptx'}).then(f=>{
  console.log('wrote', f, '·', nGen, 'generated slides for', ORD.order.length, 'frames');
});
