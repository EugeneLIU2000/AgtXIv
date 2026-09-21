# -*- coding: utf-8 -*-
"""The three frames the restructured deck needs and the source deck cannot supply.

They are written with the same primitives as every other hand-built figure, so
they stay editable and can never be a pasted picture.

  title    - source slide 1 is two empty placeholders and zero text runs, so
             the deck opened on nothing. Same title as the main talk, so the
             two decks read as one session.
  hinge    - source slide 18 lands the sentence the whole second half rests on
             ("only the schema can make an answer impossible to express") and
             then the deck walked away from it. This frame spends it.
  roadmap  - 67 frames with no route. Says, once, what the rest is for.
"""
from frames_lib import Fig, INK, LIGHT, PAPER

# ---- 1. the title -------------------------------------------------------
T=Fig('ttl','What a paper does not state: a paper states what it proves, not what'
            ' it depends on, nor who checked which part.')
T.txt(0,150,250,1620,84,'What a paper does not state')
T.line(0,150,392,1770,392,color=LIGHT,lw=1.4)
T.txt(0,150,430,1620,30,'A paper states what it proves. It does not state what it'
                        ' depends on, or who checked which part.',color=LIGHT)
# NO PICTURE HERE ON PURPOSE. The first draft previewed the diamond-over-an-
# empty-line that Act II opens on, two frames before that frame arrives, which
# spends the reveal for nothing. The title slide is text.
T.txt(0,150,800,900,26,'Yingjian Liu')
T.txt(0,150,846,900,22,'AgtXIv  ·  schema v0.3  ·  a companion figure deck',color=LIGHT)
T.txt(0,150,882,900,22,'Lorentz Institute  ·  Leiden University  ·  22 September 2026',color=LIGHT)
T.dump(1,['WHAT A PAPER DOES NOT STATE'],[False],
 ["""OPEN HERE. The title is the claim: a paper states what it proves, and it does not state what it depends on, or who checked which part.

Read the second line out loud - it is the whole argument in one sentence, and the only sentence in the talk you should deliver word for word.

Then move on. The next two frames do the arguing; this one only has to land the claim and your name."""],
 'pipe-svg','title.svg','title.json',cumulative=False)

# ---- 2. the hinge -------------------------------------------------------
H=Fig('hng','A request can be ignored and the transcript looks the same either way;'
            ' only a constraint can make an answer impossible to express.')
H.txt(0,150,150,1620,46,'A request can be ignored.  A constraint cannot.')
H.box(0,150,270,760,330,color=LIGHT,lw=1.8)
H.txt(0,186,300,688,26,'REQUESTS',color=LIGHT)
for k,t in enumerate(('the prompt','the skill','the tool call')):
    H.txt(0,186,352+k*54,688,34,t,color=LIGHT)
H.txt(0,186,528,688,22,'can be ignored — and the transcript',color=LIGHT)
H.txt(0,186,558,688,22,'looks exactly the same either way',color=LIGHT)
H.box(0,1010,270,760,330,lw=3.6)
H.txt(0,1046,300,688,26,'CONSTRAINT')
H.txt(0,1046,352,688,34,'the schema')
H.txt(0,1046,528,688,22,'a record that does not conform is not',color=LIGHT)
H.txt(0,1046,558,688,22,'repaired, and not accepted with a warning',color=LIGHT)
H.line(0,1046,470,1400,470,lw=2.4,arrow=True)
H.txt(0,1420,456,320,26,'REFUSED')
H.line(0,150,676,1770,676,color=LIGHT,lw=1.4)
H.txt(0,150,716,1620,34,'A paper’s claims are requests too.')
H.txt(0,150,786,1620,30,'The rest of this talk is an attempt to make them refusable:',color=LIGHT)
H.txt(0,150,828,1620,30,'one paper, broken into claims that each carry what they rest on.',color=LIGHT)
H.dump(1,['A REQUEST CAN BE IGNORED · A CONSTRAINT CANNOT'],[False],
 ["""THE HINGE OF THE TALK. Do not rush this frame.

The previous slide said it in the source deck's own words: the prompt, the skill and the tool call are all requests. The model can read them and not follow them, and the transcript looks identical either way. Only the schema can make an answer impossible to express.

Now spend that sentence. A paper's claims are requests too. 'By Theorem 3 of reference 14' is a request that the reader go and check something, and almost nobody does, and the paper looks the same either way.

So the question for the rest of the talk is: what would it take to make a paper's claims refusable? That is the only thing being attempted here."""],
 'pipe-svg','hinge.svg','hinge.json',cumulative=False)

# ---- 3. the roadmap -----------------------------------------------------
R=Fig('rmp','For later work to use a conclusion it must know what was said, what it'
            ' rested on and what has been checked; the route is one paper, its claims'
            ' and dependencies, one theorem’s chain, and where it stops.')
R.txt(0,150,140,1620,40,'For later work to use a conclusion, it has to know three things')
COL=[('what it said','the exact statement, not the abstract'),
     ('what it relied on','every claim underneath it, named'),
     ('what was checked','and by what — a kernel, or nobody')]
for k,(t,s) in enumerate(COL):
    x=150+k*550
    R.box(0,x,230,520,180,lw=2.8 if k else 2.8)
    R.txt(0,x+30,266,460,32,t)
    R.txt(0,x+30,330,460,22,s,color=LIGHT)
R.line(0,150,500,1770,500,color=LIGHT,lw=1.4)
ROUTE=[('one paper, frozen','the source, byte for byte'),
       ('claims + dependencies','what points at what'),
       ('one theorem’s chain','29 claims, 46 links'),
       ('where it stops','and it does stop')]
for k,(t,s) in enumerate(ROUTE):
    x=150+k*400
    R.box(0,x,590,340,150,color=LIGHT,lw=1.8)
    R.txt(0,x+22,620,296,24,t)
    R.txt(0,x+22,664,296,20,s,color=LIGHT)
    if k<3: R.line(0,x+350,665,x+390,665,color=LIGHT,lw=2.0,arrow=True)
R.txt(0,150,800,1620,26,'One real paper, one real run. Every number after this frame is read out'
                        ' of the logs, not estimated.',color=LIGHT)
R.txt(0,150,844,1620,26,'Where nobody measured it, the frame says so.',color=LIGHT)
R.dump(1,['THE ROUTE · WHAT IS COMING, AND WHY'],[False],
 ["""THE ROADMAP, and the only one in the deck - say it once, clearly, and then do not repeat it.

Three things a later paper needs before it can use your conclusion: what you actually said, what you relied on, and which parts anybody checked. A PDF gives you the first, sometimes. It does not give you the other two in any form a machine - or a hurried human - can follow.

Then the route across the bottom. One paper, frozen. Its claims and the dependencies between them. One theorem's chain pulled out of that graph. And then, honestly, where the whole thing stops - because it does stop, and the last act of this talk is about exactly where.

The promise on the last line matters more than it looks: every number from here on is read out of this repository's own logs. Where nobody has measured something, the frame says nobody measured it."""],
 'pipe-svg','roadmap.svg','roadmap.json',cumulative=False)
