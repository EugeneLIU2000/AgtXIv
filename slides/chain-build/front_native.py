# -*- coding: utf-8 -*-
"""The front matter, rebuilt from Slide_001.pptx in this deck's own language.

The source deck is the talk's opening: the crisis, what an LLM actually is,
what its memory actually is, the agent stack, how people really use it, and
what a theorist can trust. Everything here is redrawn rather than pasted, so
the whole talk speaks one visual language - and so every element stays an
editable shape rather than a screenshot.

TWO DELIBERATE CHANGES FROM THE SOURCE.
  * The source paints the SCHEMA box in a blue accent. This deck already spends
    warm on "not from this paper" and teal on "a junction"; a third product
    colour would cost more than it buys. The schema is filled ink instead -
    the same treatment the TASK box gets, which is right, because those two are
    the only things on the diagram that are not negotiable.
  * "does not -> REFUSED" is set by weight rather than by colour, exactly as
    the pipeline's second exit is later in this deck.

Slides 19-23 and 25-27 of the source are screenshots and published figures.
They are redrawn as schematics with their citations kept in the notes; a
screenshot of somebody else's paper is not something this deck should restate
as if it were its own.
"""
from frames_lib import Fig, INK, LIGHT, OPEN, PAPER

JUNC='#1F6F78'
F=Fig('fro', 'Front matter: publication rate against verification bandwidth; what an LLM'
             ' is as a function; what its memory is; the agent, skill, MCP, tool and'
             ' schema stack built one box at a time; how the tool is actually used; and'
             ' the four things a theorist might want to trust.')
box, txt, line, dot, mark = F.box, F.txt, F.line, F.dot, F.mark
HS=34; SS=22; TS=26; NS=42

def head(S, t, sub=None):
    txt(S,120,120,1680,HS,t)
    if sub: txt(S,120,168,1680,SS,sub,color=LIGHT)

def mono(S,x,y,w,s,t,color=INK):    # code and transcript lines
    txt(S,x,y,w,s,t,color=color)

# =====================================================================
# 0 - the crisis: two curves that are not growing at the same rate
# =====================================================================
AX0,AX1,AY0,AY1 = 240,1180,760,250
line(0,AX0,AY0,AX1,AY0,color=LIGHT,lw=1.8,arrow=True)
line(0,AX0,AY0,AX0,AY1,color=LIGHT,lw=1.8,arrow=True)
txt(0,150,AY1-10,180,SS,'scale',color=LIGHT)
txt(0,AX1-20,AY0+22,180,SS,'time',color=LIGHT)
line(0,560,AY0-8,560,AY0+8,color=LIGHT,lw=1.6)
txt(0,516,AY0+22,180,SS,'2024',color=LIGHT)
PUB=[(0,.02),(.25,.06),(.45,.13),(.6,.24),(.72,.40),(.82,.58),(.9,.75),(1,.95)]
VER=[(0,.03),(.3,.055),(.6,.08),(.8,.10),(1,.12)]
def curve(S,pts,lw,color):
    for a,b in zip(pts,pts[1:]):
        line(S,AX0+a[0]*(AX1-AX0),AY0-a[1]*(AY0-AY1),
               AX0+b[0]*(AX1-AX0),AY0-b[1]*(AY0-AY1),color=color,lw=lw)
curve(0,PUB,3.4,INK); curve(0,VER,3.4,LIGHT)
txt(0,1000,AY1-16,620,SS,'scientific publications')
txt(0,1000,AY0-118,620,SS,'human verification bandwidth',color=LIGHT)
box(0,240,838,700,92,lw=2.6)
txt(0,272,868,640,TS,'read  ≠  checked  ≠  reusable')
head(0,'The AI crisis in theoretical research')

# =====================================================================
# 1-4 - what is actually inside the black box
# =====================================================================
for S in range(1,5):
    head(S,'What is inside the black box of LLM reasoning')
    box(S,150,300,300,300,fill=INK,lw=0)
    box(S,560,300,1210,74)
    mono(S,586,322,1160,TS,'f  :  String  →  String')
for S in range(2,5):
    box(S,560,404,1210,74)
    mono(S,586,426,1160,TS,'f  :  String → token → prob. distribution → (next) token → String')
# the sampling picture
for S in range(3,5):
    for k,(lab,h) in enumerate([('the',30),('cat',96),('dog',54),('sat',18),('…',10)]):
        x=640+k*116
        box(S,x,700-h,66,h,fill=INK if k==1 else None,lw=2.0)
        txt(S,x,716,120,SS,lab,color=LIGHT)
    txt(S,560,546,1210,SS,'a distribution over the next token, then one is sampled',color=LIGHT)
txt(4,150,842,1620,TS,
    'the model returns a conditioned probability distribution — not an answer')

# =====================================================================
# 5-7 - model memory: there isn't any
# =====================================================================
for S in range(5,8):
    head(S,'Model memory',
         'the conversation is a forward pass. It does not update any weight.')
    box(S,150,260,760,430)
    for k,t in enumerate(['Turn 1','  [User: I am a physicist.]',
                          '  → LLM → [Response: Understood.]','',
                          'Turn 2','  [User: I am a physicist.]',
                          '  [Response: Understood.]',
                          '  [User: Explain entropy at my level.]',
                          '  → LLM → [Response: …]']):
        if t: mono(S,186,292+k*42,700,SS,t,color=INK if t.startswith('Turn') else LIGHT)
    txt(S,150,712,860,SS,'the whole history is re-sent every single time',color=LIGHT)
for S in range(6,8):
    CWX, CW = 990, [('system prompt',230),('conversation history',410),('new prompt',190)]
    x=CWX
    for lab,w in CW:
        box(S,x,380,w,110,fill=INK if lab=='system prompt' else None,lw=2.4)
        txt(S,x+16,414,w-32,SS,lab,color=PAPER if lab=='system prompt' else INK)
        x+=w
    END=CWX+sum(w for _,w in CW)
    line(S,CWX,532,END,532,color=LIGHT,lw=1.6)
    line(S,CWX,518,CWX,546,color=LIGHT,lw=1.6)
    line(S,END,518,END,546,color=LIGHT,lw=1.6)
    txt(S,CWX,558,700,SS,'context window  —  a fixed token capacity',color=LIGHT)
txt(7,1000,652,820,TS,'exceed it and something must be')
txt(7,1000,692,820,TS,'compressed, truncated or dropped')

# =====================================================================
# 8 - two kinds of API
# =====================================================================
head(8,'API / Agent / MCP / schema / skills',
     'prompt sorcery from the LLM era')
box(8,150,300,740,300)
txt(8,186,330,680,TS,'a numpy API')
mono(8,186,404,680,SS,'import numpy as np',color=LIGHT)
mono(8,186,442,680,SS,'result = np.mean([1, 2, 3])',color=LIGHT)
txt(8,186,514,680,SS,'one answer, and the same one every time',color=LIGHT)
box(8,1030,300,740,300)
txt(8,1066,330,680,TS,'an LLM API')
box(8,1066,392,200,70); txt(8,1090,414,160,SS,'client',align='l')
box(8,1506,392,200,70); txt(8,1530,414,160,SS,'model',align='l')
line(8,1266,414,1506,414,lw=2.0,arrow=True); txt(8,1300,382,200,SS,'prompt',color=LIGHT)
line(8,1506,446,1266,446,lw=2.0,arrow=True); txt(8,1300,452,200,SS,'response',color=LIGHT)
txt(8,1066,514,680,SS,'a distribution, and a different sample each time',color=LIGHT)
txt(8,150,680,1620,TS,
    'an agent is a system with a model at its core: the model decides the next step')

# =====================================================================
# 9-16 - the stack, one box at a time  (geometry from agent-stack/build.js)
# =====================================================================
# geometry from agent-stack/build.js (inches x144), dropped 64px so the
# subtitle line clears the SKILL box at the top of the diagram
YOFF=64
_G={'task':(79,396,209,166),'agent':(353,396,540,166),'llm':(403,429,439,98),
    'skill':(353,187,540,98),'mcp':(389,691,223,98),'tools':(684,691,353,98),
    'schema':(1087,396,389,166),'ok':(1555,374,281,75),'no':(1555,487,281,75)}
G={k:(x,y+YOFF,w,h) for k,(x,y,w,h) in _G.items()}
ROW=479+YOFF
def gbox(S,k,**kw): box(S,*G[k],**kw)
def gmid(k): x,y,w,h=G[k]; return x+w/2, y+h/2
STACK=[
 ('A language model, by itself','text in, a distribution over next tokens out'),
 ('Put it in a loop — that is an agent','the model is the engine; the loop is the agent'),
 ('Give the loop a task','what to do, on what, and what counts as finished'),
 ('A skill is a written procedure','a protocol loaded into context — drawn dashed, because it is advice'),
 ('MCP is the socket, not the tool','a published convention for exposing a tool'),
 ('Tools are what actually act','a compiler, a database, a filesystem'),
 ('The output meets a schema','a machine-checked contract'),
 ('And the schema can say no','the only arrow on the diagram that rejects'),
]
for i,(t,sub) in enumerate(STACK):
    S=9+i
    head(S,t,sub)
    if i>=5:                                   # tools + the return arrow, drawn under
        tx,_=gmid('tools')
        # the result comes BACK to the loop - that return is the whole reason
        # this is called an agent, so the arrow points at the agent
        line(S,tx,G['tools'][1],tx,G['agent'][1]+G['agent'][3],color=LIGHT,lw=2.0,arrow=True)
        txt(S,tx+14,600+YOFF,320,SS,'result returns',color=LIGHT)
    gbox(S,'llm',lw=2.6 if i==0 else 1.8)
    lx,ly=gmid('llm'); txt(S,G['llm'][0]+20,ly-24,G['llm'][2]-40,NS if i==0 else TS,'LLM')
    if i==0: txt(S,G['llm'][0],G['llm'][1]+G['llm'][3]+18,560,SS,
                 'text → a distribution over next tokens',color=LIGHT)
    if i>=1:
        gbox(S,'agent',lw=2.6)
        txt(S,G['agent'][0],G['agent'][1]-40,440,SS,'AGENT · the loop')
    if i>=2:
        gbox(S,'task',fill=INK,lw=0)
        txt(S,G['task'][0]+22,G['task'][1]+62,G['task'][2]-44,TS,'TASK',color=PAPER)
        line(S,G['task'][0]+G['task'][2],ROW,G['agent'][0],ROW,lw=2.2,arrow=True)
    if i>=3:
        gbox(S,'skill',style='dash',color=LIGHT,lw=2.0)
        txt(S,G['skill'][0]+20,G['skill'][1]+34,G['skill'][2]-40,SS,
            'SKILL · a written procedure',color=LIGHT)
        ax,_=gmid('agent')
        line(S,ax,G['skill'][1]+G['skill'][3],ax,G['agent'][1],color=LIGHT,lw=2.0,
             style='dash',arrow=True)
        txt(S,ax+14,320+YOFF,420,SS,'loaded into context — advice',color=LIGHT)
    if i>=4:
        gbox(S,'mcp',lw=1.8)
        txt(S,G['mcp'][0]+20,G['mcp'][1]+34,G['mcp'][2]-40,SS,'MCP')
        mx,_=gmid('mcp')
        line(S,mx,G['agent'][1]+G['agent'][3],mx,G['mcp'][1],lw=2.0,arrow=True)
        txt(S,mx+14,600+YOFF,260,SS,'tool call',color=LIGHT)
    if i>=5:
        gbox(S,'tools',lw=1.8)
        txt(S,G['tools'][0]+20,G['tools'][1]+34,G['tools'][2]-40,SS,'TOOLS')
        txt(S,G['tools'][0],G['tools'][1]+G['tools'][3]+14,520,SS,
            'a compiler · a database · a filesystem',color=LIGHT)
        line(S,G['mcp'][0]+G['mcp'][2],740+YOFF,G['tools'][0],740+YOFF,lw=2.0,arrow=True)
    if i>=6:
        line(S,G['agent'][0]+G['agent'][2],ROW,G['schema'][0],ROW,lw=2.2,arrow=True)
        txt(S,G['agent'][0]+G['agent'][2]+22,436+YOFF,200,SS,'output',color=LIGHT)
        gbox(S,'schema',fill=INK,lw=0)
        txt(S,G['schema'][0]+24,G['schema'][1]+58,G['schema'][2]-48,TS,'SCHEMA',color=PAPER)
        txt(S,G['schema'][0],G['schema'][1]+G['schema'][3]+18,520,SS,
            'a machine-checked contract',color=LIGHT)
    if i>=7:
        sx=G['schema'][0]+G['schema'][2]
        line(S,sx,ROW,G['ok'][0],G['ok'][1]+37,lw=2.0,arrow=True)
        line(S,sx,ROW,G['no'][0],G['no'][1]+37,lw=2.6,arrow=True)
        gbox(S,'ok',lw=1.8);  txt(S,G['ok'][0]+18,G['ok'][1]+24,G['ok'][2]-36,SS,'conforms → recorded')
        gbox(S,'no',lw=3.6);  txt(S,G['no'][0]+18,G['no'][1]+24,G['no'][2]-36,SS,
                                  'does not → REFUSED',bold=True)

# =====================================================================
# 17-18 - how the thing is actually used
# =====================================================================
for S in (17,18):
    head(S,'“Please help me …”')
    box(S,150,300,760,260)
    txt(S,186,336,700,TS,'learn backwards')
    txt(S,186,404,700,SS,'here is a result I do not understand.',color=LIGHT)
    txt(S,186,438,700,SS,'take me back to what it rests on.',color=LIGHT)
    line(S,830,510,230,510,lw=2.4,arrow=True)
box(18,1010,300,760,260)
txt(18,1046,336,700,TS,'reason forwards')
txt(18,1046,404,700,SS,'here is where I want to get to.',color=LIGHT)
txt(18,1046,438,700,SS,'work out what has to hold first.',color=LIGHT)
line(18,1090,510,1690,510,lw=2.4,arrow=True)
txt(18,150,640,1620,TS,'— and, more often than either, both at once')

# =====================================================================
# 19 - what a theorist might want to trust
# =====================================================================
TRUST=[('The story','What did the paper actually state?'),
       ('Mathematical correctness','Does the conclusion follow from the stated assumptions?'),
       ('Computational reproducibility','Can the numerical result be reproduced?'),
       ('Physical-semantic alignment','Does the formal object represent the intended physics?')]
def trust(S, live=None):
    head(S,'What we actually care about — and what can we trust?')
    for k,(t,q) in enumerate(TRUST):
        r,c=divmod(k,2); x=150+c*830; y=300+r*250
        on = live is None or k in live
        box(S,x,y,760,190,lw=3.4 if (live and k in live) else 2.0,
            color=INK if on else LIGHT)
        txt(S,x+26,y+34,708,TS,t,color=INK if on else LIGHT)
        txt(S,x+26,y+96,708,SS,q,color=LIGHT)
trust(19)

# =====================================================================
# 20 - THE BRIDGE into the rest of the talk
# =====================================================================
trust(20, live={1})
txt(20,150,820,1620,TS,'everything after this slide is about the second box')
txt(20,150,872,1620,SS,
    'and about one paper, one theorem, and what it actually rests on',color=LIGHT)

METER=[
 'TWO CURVES · PUBLISHING AND CHECKING',
 'A MODEL IS A FUNCTION FROM STRING TO STRING',
 '… BY WAY OF TOKENS AND A DISTRIBUTION',
 'IT RETURNS A DISTRIBUTION · THEN SAMPLES ONE',
 'NOT AN ANSWER · A CONDITIONED DISTRIBUTION',
 'NO WEIGHTS CHANGE · THE HISTORY IS RE-SENT',
 'THE CONTEXT WINDOW · A FIXED TOKEN CAPACITY',
 'EXCEED IT AND SOMETHING MUST BE DROPPED',
 'TWO KINDS OF API · ONE ANSWERS, ONE SAMPLES',
 'A LANGUAGE MODEL, BY ITSELF',
 'PUT IT IN A LOOP · THAT IS AN AGENT',
 'GIVE THE LOOP A TASK',
 'A SKILL IS ADVICE · DRAWN DASHED',
 'MCP IS THE SOCKET, NOT THE TOOL',
 'TOOLS ARE WHAT ACTUALLY ACT',
 'THE OUTPUT MEETS A SCHEMA',
 'AND THE SCHEMA CAN SAY NO',
 'LEARN BACKWARDS',
 'REASON FORWARDS · AND USUALLY BOTH',
 'FOUR THINGS A THEORIST MIGHT WANT TO TRUST',
 'OF THE FOUR, THIS TALK IS ABOUT THE SECOND',
]
OPENMETER=[False]*21

NOTE=[
"""THE OPENING CLAIM, and it is a claim about the field rather than a measurement - the curves have no numbers on them and no numbers are implied.

The top curve is how fast results are produced. The bottom one is how fast a human being can check them. They are not growing at the same rate, and 2024 is roughly where most people in this room felt the gap open.

The line in the box is the whole talk in three words: READ is not CHECKED, and CHECKED is not REUSABLE. A paper you have read is not a paper you have verified; a paper you have verified is not a thing the next paper can build on without doing the verification again.

Four things to say out loud: researchers are drowning in "recent progress"; every open problem solved raises both the confidence in AGI and the anxiety about our own careers; later work still needs the exact imported claim, not the headline; and claims and semantic content are routinely exaggerated.""",

"""Before anything else, what the thing actually is. A language model is a function from a string to a string. That is the entire type signature, and it is worth writing down because almost every confusion about these systems comes from imagining something richer.

Source for the diagram: Zhang Y, Khan S A, Mahmud A, et al., npj Artificial Intelligence, 2025, 1(1): 14.""",

"""Expand the signature and the mechanism appears. The string becomes tokens; the model maps the tokens to a probability distribution over what comes next; one token is drawn from it; the token is appended; and the whole thing runs again.

Nothing in there is reasoning in the sense a physicist means. It is a very good conditional distribution, sampled repeatedly.""",

"""And here is the part with consequences. At each step the model does not choose a token, it produces a distribution over all of them and something samples from it.

Run the same prompt twice and you get two different answers, both fluent. That is not a bug being fixed in the next version; it is the operation. Any system built on top has to be designed for an engine whose output is a sample.""",

"""So: the model does not return an answer. It returns a conditioned probability distribution, and then something takes a sample.

Hold onto that sentence. It is the reason the rest of this talk is about contracts rather than about prompts - you cannot make a sampler reliable by asking it nicely.""",

"""Second thing worth being concrete about: the model has no memory.

Every turn is a forward pass. No weight is updated. What looks like memory is the client re-sending the entire conversation each time - turn 2 contains all of turn 1, verbatim, as text.

Source: Tobias Osborne's 2026 talk at UCL, which is where I first saw this laid out properly for physicists.""",

"""Which means there is a budget. The system prompt, the whole conversation so far, and the new prompt all have to fit inside a fixed token capacity: the context window.

The system prompt is drawn filled because it is the one part you do not control from inside the conversation.""",

"""And when it does not fit, something has to go. The history gets compressed, truncated, or selected from.

This is worth a moment because it is invisible from the outside: the transcript looks the same whether the model saw the whole history or a summary of it. Any claim of the form "but I told it that earlier" has to survive this, and often does not.""",

"""Two kinds of API, and the difference is the whole problem.

Call numpy and you get one answer, and the same answer every time. Call a model and you get a sample from a distribution, and a different one on the next call.

An agent is a system with a model at its core, executing high-level tasks: the model decides the next step. Which means the non-determinism is now inside the control flow, not just in the output.""",

"""Now build the stack, one box at a time. Start with the engine: text in, a distribution over next tokens out. Stateless - nothing carries between calls and the weights never change.""",

"""Put it in a loop, and that is an agent. The loop calls the model repeatedly, decides what to do next, and stops when it judges the work done. The model is the engine; the loop is the agent.""",

"""Give the loop a task: a bounded work order - what to do, on which inputs, and what counts as finished.""",

"""A skill is a written procedure - a protocol loaded into the context when the task matches it.

Drawn dashed, because it is advice. The model can read it and not follow it, and nothing records that it did. This is the single most over-sold idea in the current ecosystem and the dashes are the honest way to draw it.""",

"""MCP is the socket, not the tool. A published convention for exposing a tool so that any model can call it. It standardises the plug; it says nothing whatever about what comes through it.""",

"""Tools are what actually act: a compiler, a database, a filesystem. The result returns to the loop, which calls the model again - and that return arrow is the whole reason the thing is called an agent rather than a chatbot.""",

"""The output meets a schema: a machine-checked contract. Which fields a valid record must have, which types, and - crucially - that no field nobody agreed to may be added.

The source deck paints this box in a blue accent. Here it is filled ink, like the task box, because in this deck colour already means two specific things and this is not one of them.""",

"""And the schema can say no. This is the only arrow on the diagram that rejects. A record that does not conform is not repaired, and not accepted with a warning - it is refused.

Say the closing line slowly, because the rest of the talk depends on it: the prompt, the skill and the tool call are all REQUESTS. They can be ignored, and the transcript looks exactly the same either way. Only the schema can make an answer impossible to express.""",

"""How the tool is actually used, in practice, by people in this room.

Backwards: here is a result I do not understand, take me back to what it rests on. That is most of what I do with it, and it is the mode the rest of this talk is about.

The source deck shows real sessions here; those are redrawn rather than pasted.""",

"""And forwards: here is where I want to get to, work out what has to hold first.

In practice it is almost never one or the other. You go backwards until you hit something you believe, then forwards from there, and the useful question is what got recorded along the way - which is, as far as I can tell, usually nothing.""",

"""So what do we actually want to trust, as theorists? Four different things, and they are genuinely different questions with genuinely different methods.

THE STORY - what did the paper actually state? MATHEMATICAL CORRECTNESS - does the conclusion follow from the stated assumptions? COMPUTATIONAL REPRODUCIBILITY - can the numerical result be reproduced? PHYSICAL-SEMANTIC ALIGNMENT - does the formal object represent the intended physics?

The references on the source slide: the Reverse Mathematics Zoo (Dzhafarov, 2019), and the Lean 4 theorem prover and programming language (de Moura and Ullrich, 2021).""",

"""THE BRIDGE, and it is worth being blunt about the scope.

Of those four, everything after this slide is about the second one - does the conclusion follow from the stated assumptions - plus a little of the first, because you cannot check a conclusion until you have pinned down what was actually claimed.

It is NOT about physical-semantic alignment. Whether a Lean definition of the reduced stabilizer polytope means the physics you had in mind is a judgement no kernel makes, and this project does not pretend otherwise - the records carry alignment_notes precisely because that gap cannot be closed mechanically.

It is NOT about computational reproducibility either; there is no numerical claim in the case study.

So the rest of the talk narrows hard: one paper, one theorem, and what it actually rests on. The next few slides are the honest version of the first curve on the opening slide - not the field's publication rate, which I cannot measure, but my own logs, which I can."""
]

F.dump(21, METER, OPENMETER, NOTE, 'pipe-svg', 'front.svg', 'front.json',
       cumulative=False)
