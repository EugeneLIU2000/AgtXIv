/* v0 assembly. The drawing primitives, the figure data and the opening /
   chain descriptors now live in deck_core.js, because deck_v1.js draws the
   same figures in a different order and neither should own them. */
const C=require('./deck_core');
const {CG,CHAIN,CL,CODE,FIG,FR,H,INK,JUNC,L,LIGHT,MO,MONO,OPEN,OPENING,PIPE,PP,PT,RCOL,RECG,RG,SPACE_EM,SRCLINE,W,WHITE,X,Y,blend,chain,cubic,curve,fs,hex6,mark,oval,pptxgen,prims,record,rect,reduced,seg,tx}=C;
const SLIDES=[];
function addFigure(F){
  if (!F) return 0;
  F.meter.forEach((m,k)=>SLIDES.push({draw:s=>prims(s,F,k), meter:m, open:F.open[k], note:F.note[k]}));
  return F.meter.length;
}
const N_FRO  = addFigure(FR);      // the background: the crisis, the model, the stack
const N_MOT  = addFigure(MO);      // why any of this matters - before anything technical
const N_PIPE = addFigure(PP);      // the whole thing in five boxes

OPENING.forEach(o=>SLIDES.push(o));

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
