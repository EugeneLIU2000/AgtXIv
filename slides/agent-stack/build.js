const pptxgen = require('pptxgenjs');

// ---- palette: ink-dominant to match the seminar deck, ONE accent -------
const INK='1A1A16', MUTED='8A8A80', FAINT='D8D8D4', WHITE='FFFFFF', ACCENT='065A82';
const HEAD='Cambria', BODY='Calibri';

// ---- geometry, inches on a 13.3 x 7.5 canvas ---------------------------
const G = {
  task:   {x:0.55, y:2.75, w:1.45, h:1.15},
  agent:  {x:2.45, y:2.75, w:3.75, h:1.15},
  llm:    {x:2.80, y:2.98, w:3.05, h:0.68},
  skills: {x:2.45, y:1.30, w:3.75, h:0.68},
  mcp:    {x:2.70, y:4.80, w:1.55, h:0.68},
  tools:  {x:4.75, y:4.80, w:2.45, h:0.68},
  schema: {x:7.55, y:2.75, w:2.70, h:1.15},
  okBox:  {x:10.80,y:2.60, w:1.95, h:0.52},
  noBox:  {x:10.80,y:3.38, w:1.95, h:0.52},
};

const STEPS = [
  { t:'A language model, by itself',
    c:'Text in, a distribution over next tokens out. Stateless: nothing carries between calls, and the weights never change.' },
  { t:'Put it in a loop — that is an agent',
    c:'The agent calls the model repeatedly, decides what to do next, and stops when it judges the work done. The model is the engine; the loop is the agent.' },
  { t:'Give the loop a task',
    c:'A bounded work order arrives: what to do, on which inputs, and what counts as finished.' },
  { t:'A skill is a written procedure',
    c:'A protocol loaded into the context when the task matches it — drawn dashed, because it is advice. The model can read it and not follow it, and nothing records that it did.' },
  { t:'MCP is the socket, not the tool',
    c:'A published convention for exposing a tool so that any model can call it. It standardises the plug; it says nothing about what comes through it.' },
  { t:'Tools are what actually act',
    c:'A compiler, a database, a filesystem. The result returns to the loop, which calls the model again — this return arrow is the whole reason it is called an agent.' },
  { t:'The output meets a schema',
    c:'A machine-checked contract: which fields a valid record must have, which types, and — crucially — that no field nobody agreed to may be added.' },
  { t:'And the schema can say no',
    c:'This is the only arrow on the diagram that rejects. A record that does not conform is not repaired or accepted with a warning; it is refused.' },
  { t:'Three ways of asking. One way of refusing.',
    c:'The prompt, the skill and the tool call are all requests — they can be ignored, and the transcript looks the same either way. Only the schema can make an answer impossible to express.' },
];

function diagram(slide, step) {
  const on = (n) => step >= n;
  const box = (g, o={}) => ({ x:g.x, y:g.y, w:g.w, h:g.h, ...o });
  const label = (g, text, o={}) => slide.addText(text, {
    ...box(g), isTextBox:true, margin:0, align:'center', valign:'middle',
    fontFace:o.face||BODY, fontSize:o.size||13, bold:o.bold!==false,
    color:o.color||INK, ...o.extra });

  // --- 5: tools + return arrow (drawn first so it sits under the boxes)
  if (on(5)) {
    slide.addShape('line', { x:G.tools.x+G.tools.w*0.55, y:G.agent.y+G.agent.h, w:0, h:G.tools.y-(G.agent.y+G.agent.h),
      line:{color:MUTED, width:1.25, endArrowType:'triangle', beginArrowType:'triangle'} });
    slide.addText('result returns', {
      x:G.tools.x+G.tools.w*0.55+0.08, y:4.16, w:1.5, h:0.3, isTextBox:true, margin:0,
      fontFace:BODY, fontSize:10, italic:true, color:MUTED });
  }

  // --- 0: the model
  slide.addShape('rect', { ...box(G.llm), fill:{color: on(1)?WHITE:WHITE},
    line:{color:INK, width: on(1)?1.25:2} });
  label(G.llm, 'LLM', {size: on(1)?14:20, face:HEAD});
  if (!on(1)) slide.addText('text → a distribution over next tokens', {
    x:G.llm.x, y:G.llm.y+G.llm.h+0.12, w:G.llm.w, h:0.3, isTextBox:true, margin:0,
    align:'center', fontFace:BODY, fontSize:11, italic:true, color:MUTED });

  // --- 1: the agent loop around it
  if (on(1)) {
    slide.addShape('roundRect', { ...box(G.agent), rectRadius:0.12, fill:{type:'none'},
      line:{color:INK, width:1.75} });
    slide.addText('AGENT · the loop', { x:G.agent.x, y:G.agent.y-0.30, w:1.9, h:0.26,
      isTextBox:true, margin:0, align:'left', fontFace:BODY, fontSize:10, bold:true,
      color:INK, charSpacing:1.6 });
  }

  // --- 2: the task
  if (on(2)) {
    slide.addShape('rect', { ...box(G.task), fill:{color:INK}, line:{color:INK, width:1} });
    label(G.task, 'TASK', {color:WHITE, size:13, face:HEAD});
    slide.addShape('line', { x:G.task.x+G.task.w, y:G.agent.y+G.agent.h/2, w:G.agent.x-(G.task.x+G.task.w), h:0,
      line:{color:INK, width:1.5, endArrowType:'triangle'} });
  }

  // --- 3: the skill, dashed because it is advice
  if (on(3)) {
    slide.addShape('rect', { ...box(G.skills), fill:{type:'none'},
      line:{color:MUTED, width:1.25, dashType:'dash'} });
    label(G.skills, 'SKILL · a written procedure', {color:MUTED, size:12});
    slide.addShape('line', { x:G.agent.x+G.agent.w/2, y:G.skills.y+G.skills.h, w:0, h:G.agent.y-(G.skills.y+G.skills.h),
      line:{color:MUTED, width:1.25, dashType:'dash', endArrowType:'triangle'} });
    slide.addText('loaded into context — advice', { x:G.agent.x+G.agent.w/2+0.10, y:2.14, w:2.6, h:0.26,
      isTextBox:true, margin:0, fontFace:BODY, fontSize:10, italic:true, color:MUTED });
  }

  // --- 4: MCP, the socket
  if (on(4)) {
    slide.addShape('rect', { ...box(G.mcp), fill:{type:'none'}, line:{color:INK, width:1.25} });
    label(G.mcp, 'MCP', {size:13, face:HEAD});
    slide.addText('the socket', { x:G.mcp.x, y:G.mcp.y+G.mcp.h+0.06, w:G.mcp.w, h:0.26, isTextBox:true,
      margin:0, align:'center', fontFace:BODY, fontSize:10, italic:true, color:MUTED });
    slide.addShape('line', { x:G.mcp.x+G.mcp.w*0.45, y:G.agent.y+G.agent.h, w:0, h:G.mcp.y-(G.agent.y+G.agent.h),
      line:{color:INK, width:1.25, endArrowType:'triangle'} });
    slide.addText('tool call', { x:G.mcp.x+G.mcp.w*0.45+0.08, y:4.12, w:1.4, h:0.26, isTextBox:true,
      margin:0, fontFace:BODY, fontSize:10, italic:true, color:MUTED });
  }

  // --- 5: tools
  if (on(5)) {
    slide.addShape('rect', { ...box(G.tools), fill:{type:'none'}, line:{color:INK, width:1.25} });
    label(G.tools, 'TOOLS', {size:13, face:HEAD});
    slide.addText('a compiler · a database · a filesystem', { x:G.tools.x, y:G.tools.y+G.tools.h+0.06,
      w:G.tools.w, h:0.26, isTextBox:true, margin:0, align:'center', fontFace:BODY, fontSize:10,
      italic:true, color:MUTED });
    slide.addShape('line', { x:G.mcp.x+G.mcp.w, y:G.mcp.y+G.mcp.h/2, w:G.tools.x-(G.mcp.x+G.mcp.w), h:0,
      line:{color:INK, width:1.25, endArrowType:'triangle', beginArrowType:'triangle'} });
  }

  // --- 6: the schema
  if (on(6)) {
    slide.addShape('line', { x:G.agent.x+G.agent.w, y:G.agent.y+G.agent.h/2, w:G.schema.x-(G.agent.x+G.agent.w), h:0,
      line:{color:INK, width:1.5, endArrowType:'triangle'} });
    slide.addText('output', { x:G.agent.x+G.agent.w+0.18, y:G.agent.y+G.agent.h/2-0.34, w:1.1, h:0.26,
      isTextBox:true, margin:0, fontFace:BODY, fontSize:10, italic:true, color:MUTED });
    slide.addShape('rect', { ...box(G.schema), fill:{color:ACCENT}, line:{color:ACCENT, width:1.5} });
    label(G.schema, 'SCHEMA', {color:WHITE, size:15, face:HEAD});
    slide.addText('a machine-checked contract', { x:G.schema.x, y:G.schema.y+G.schema.h+0.08, w:G.schema.w, h:0.26,
      isTextBox:true, margin:0, align:'center', fontFace:BODY, fontSize:10, italic:true, color:ACCENT });
  }

  // --- 7: the two exits, one of which is a refusal
  if (on(7)) {
    slide.addShape('line', { x:G.schema.x+G.schema.w, y:G.agent.y+G.agent.h/2, w:0.28, h:-0.50,
      line:{color:INK, width:1.25, endArrowType:'triangle'} });
    slide.addShape('line', { x:G.schema.x+G.schema.w, y:G.agent.y+G.agent.h/2, w:0.28, h:0.31,
      line:{color:ACCENT, width:1.75, endArrowType:'triangle'} });
    slide.addShape('rect', { ...box(G.okBox), fill:{type:'none'}, line:{color:INK, width:1} });
    label(G.okBox, 'conforms → recorded', {size:11});
    slide.addShape('rect', { ...box(G.noBox), fill:{type:'none'}, line:{color:ACCENT, width:1.75} });
    label(G.noBox, 'does not → REFUSED', {size:11, color:ACCENT});
  }
}

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';            // 13.3 x 7.5 - set BEFORE adding slides
pres.author = 'Yingjian Liu';
pres.title  = 'Agent, MCP, Skill, Schema - the data flow';

// ---------- title ----------
const t = pres.addSlide();
t.background = { color: INK };
t.addText('How the pieces fit', { x:0.9, y:2.35, w:11.5, h:1.0, isTextBox:true, margin:0,
  fontFace:HEAD, fontSize:44, bold:true, color:WHITE });
t.addText('Agent · LLM · Skill · MCP · Tools · Schema', { x:0.9, y:3.35, w:11.5, h:0.5,
  isTextBox:true, margin:0, fontFace:BODY, fontSize:19, color:'CADCFC' });
t.addText('One data flow, built one piece at a time. Advance with the arrow key.', { x:0.9, y:4.15, w:11.5, h:0.4,
  isTextBox:true, margin:0, fontFace:BODY, fontSize:13, italic:true, color:MUTED });
t.addNotes('Nine build steps. Each slide adds exactly one element to the same diagram, so advancing the deck animates the flow.');

// ---------- the nine build steps ----------
STEPS.forEach((s, i) => {
  const sl = pres.addSlide();
  sl.background = { color: WHITE };
  sl.addText(s.t, { x:0.55, y:0.42, w:12.2, h:0.6, isTextBox:true, margin:0,
    fontFace:HEAD, fontSize:28, bold:true, color:INK });
  diagram(sl, i);
  sl.addText(s.c, { x:0.55, y:6.05, w:12.2, h:0.95, isTextBox:true, margin:0,
    fontFace:BODY, fontSize:14, color:INK, lineSpacingMultiple:1.25 });
  sl.addText(`${i+1} / ${STEPS.length}`, { x:11.9, y:0.5, w:0.9, h:0.3, isTextBox:true, margin:0,
    align:'right', fontFace:BODY, fontSize:11, color:MUTED });
  sl.addNotes(s.c);
});

// ---------- the same build as a looping animation ----------
// An animated GIF plays by itself in PowerPoint's slideshow mode, so this
// slide is the hands-free version of the nine steps above.
const fs = require('fs');
if (fs.existsSync('agent-stack-dataflow.gif')) {
  const g = pres.addSlide();
  g.background = { color: WHITE };
  g.addText('The whole flow, looping', { x:0.55, y:0.42, w:12.2, h:0.6, isTextBox:true, margin:0,
    fontFace:HEAD, fontSize:28, bold:true, color:INK });
  g.addImage({ path:'agent-stack-dataflow.gif', x:0.75, y:1.45, w:11.8, h:4.47 });
  g.addText('Plays automatically in slideshow mode (press F5 / Play). The nine slides before this one are the same build, under your own clicks \u2014 use whichever suits the room.',
    { x:0.55, y:6.20, w:12.2, h:0.7, isTextBox:true, margin:0, fontFace:BODY, fontSize:13,
      italic:true, color:MUTED, lineSpacingMultiple:1.25 });
  g.addNotes('The GIF loops on its own in slideshow mode. It will not animate in the editing view - press F5 to see it move.');
}

pres.writeFile({ fileName: 'agent-stack-dataflow.pptx' })
  .then(f => console.log('wrote', f));
