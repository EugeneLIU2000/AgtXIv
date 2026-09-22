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
T=Fig('ttl','Some thoughts about LLM for theoretical research. Yingjian Liu.')
T.txt(0,150,330,1620,72,'Some thoughts about LLM')
T.txt(0,150,416,1620,72,'for theoretical research')
T.line(0,150,556,900,556,color=LIGHT,lw=1.4)
T.txt(0,150,596,900,30,'Yingjian Liu')
# NOTHING ELSE ON THIS FRAME. The affiliation, the date, the schema version and
# the one-sentence thesis were all here and all left again: the room can read
# the title and the name, and everything else is something the speaker says.
T.dump(1,['SOME THOUGHTS ABOUT LLM FOR THEORETICAL RESEARCH'],[False],
 ["""OPEN HERE, on almost nothing. The title is deliberately modest - these are thoughts, not results, and saying so in the first ten seconds buys the room's patience for the honest parts later.

Everything that used to be printed on this frame is now yours to say: where you are, what the date is, and the sentence the talk is actually about - a paper states what it proves, and it does not state what it depends on, or who checked which part.

Say that sentence here, word for word. It is the only one in the talk worth memorising."""],
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

# =========================================================================
# v1.1 - the frames this revision adds
# =========================================================================

# ---- 4. the one-sentence bridge, crisis -> what the machine is ----------
# It replaces two frames (a lone theorem, and 6 lines over 7,765) that opened
# an argument the deck then did not make here. One sentence, one turn.
B=Fig('crb','Before asking whether the output can be trusted, look at what the'
            ' machine is doing when it produces it.')
B.txt(0,150,380,1620,54,'Before asking whether we can trust what it writes,')
B.txt(0,150,456,1620,54,'look at what it is doing when it writes.')
B.line(0,150,584,700,584,color=LIGHT,lw=1.4)
B.txt(0,150,620,1620,26,'Nothing in the next four frames is a criticism. It is a description.',
      color=LIGHT)
B.dump(1,['WHAT IS THE MACHINE ACTUALLY DOING'],[False],
 ["""ONE SENTENCE, THEN TURN THE PAGE. Do not elaborate - the next four frames are the elaboration.

The curve you just saw is about volume. This is the turn from volume to mechanism: the reason a generated result is hard to reuse is not that it is sloppy, it is that of what the machine did to produce it, nothing survives except the text.

Say the second line - it is a description, not a criticism - and move on. It buys you the room's patience for four frames of mechanism."""],
 'pipe-svg','crisisbridge.svg','crisisbridge.json',cumulative=False)

# ---- 5,6,7. what formalization actually looks like ----------------------
MONO=0.60                                  # a monospace space, as a fraction of em
def ind(n,size): return n*size*MONO

# WRITTEN FOR SOMEBODY WHO HAS NEVER SEEN LEAN. The first draft put the code on
# the left and three summary notes on the right, which tells a newcomer what the
# blocks are FOR without telling them how to read a single line. Every line now
# has its own plain-English reading on the same row.
L=Fig('lna','A Lean 4 example read line by line: a definition, a claim about it,'
            ' and a two-step proof, each line with its plain-English reading.')
L.txt(0,150,112,1620,44,'Lean 4  \u2014  how to read it')
L.txt(0,150,176,1620,24,'Six lines. On the left is what you type; on the right is what'
                        ' each line says.',color=LIGHT)
L.box(0,150,236,760,404,color=LIGHT,lw=1.8)
CS=24
ROWS=[(0,'def double (n : Nat) : Nat :=',
         'DEFINE a thing called double. Give it a whole number n \u2026'),
      (2,'2 * n',
         '\u2026 and what comes back is 2 times n. Nothing is claimed yet.'),
      (None,None,None),
      (0,'theorem double_eq_add (n : Nat) :',
         'CLAIM, and give the claim a name. For every whole number n \u2026'),
      (4,'double n = n + n := by',
         '\u2026 double n is the same as n + n.  "by" means: proof follows.'),
      (None,None,None),
      (2,'unfold double',
         'step 1 \u2014 replace double by what it stands for: 2 * n = n + n.'),
      (2,'omega',
         'step 2 \u2014 omega settles arithmetic statements like that one.')]
y=282
for sp,code,eng in ROWS:
    if code is None: y+=26; continue
    L.txt(0,186+ind(sp,CS),y,724,CS,code,mono=True)
    L.txt(0,960,y+2,810,22,eng,color=LIGHT)
    y+=46
L.line(0,150,676,1770,676,color=LIGHT,lw=1.4)
L.txt(0,150,712,1620,32,'Nothing here is prose. That line IS the theorem \u2014'
                        ' not a description of one.')
L.txt(0,150,772,1620,24,'Which is the whole trade: you give up the words, and in exchange'
                        ' the claim becomes something',color=LIGHT)
L.txt(0,150,810,1620,24,'a machine can check, and refuse.',color=LIGHT)
L.dump(1,['LEAN 4 \u00b7 HOW TO READ IT'],[False],
 ["""THE ONLY CODE IN THE TALK. Give it a full minute and read it out loud, left column then right column, line by line. Most of the room has never seen this.

Line one: def. I am DEFINING a thing. 'double' is its name, '(n : Nat)' means it takes a whole number which I will call n, and the ': Nat' after it means it hands back a whole number too. Line two says what it hands back: two times n. Stop and make one point - a definition cannot be wrong. It is not claiming anything. It is just naming a construction.

Line three is where it gets interesting: theorem. Now I am CLAIMING something, and I give the claim a name so other work can refer to it. Line four is the claim itself: double n equals n + n, for every n. The word 'by' at the end means: what follows is the proof.

Lines five and six are the proof, and they are a program, not an argument. 'unfold double' replaces the name by what it stands for, so the goal becomes 2 * n = n + n. 'omega' is a decision procedure for this kind of arithmetic; it either closes the goal or it does not.

Then the bottom line, which is the point of the frame: that fourth line is not a description of a theorem. It IS the theorem. You gave up the prose and got back something checkable."""],
 'pipe-svg','lean1.svg','lean1.json',cumulative=False)

K=Fig('lnb','Lean accepts or rejects; the only escape hatch is sorry, and this'
            ' repository contains none.')
K.txt(0,150,130,1620,44,'It compiles, or it does not. There is no third answer.')
K.box(0,150,250,760,230,lw=3.4)
K.txt(0,186,286,688,34,'accepted')
K.txt(0,186,348,688,22,'each step re-checked by a kernel of a few thousand lines',color=LIGHT)
K.txt(0,186,384,688,22,'that does not know who wrote it, or how tired it is',color=LIGHT)
K.box(0,1010,250,760,230,color=LIGHT,lw=1.8)
K.txt(0,1046,286,688,34,'rejected',color=LIGHT)
K.txt(0,1046,348,688,24,'and it names the step it would not take —',color=LIGHT)
K.txt(0,1046,386,688,24,'which is a research to-do list, not a failure',color=LIGHT)
K.line(0,150,548,1770,548,color=LIGHT,lw=1.4)
K.txt(0,150,588,1620,30,'There is exactly one way to cheat, and it is a keyword:')
K.txt(0,186,644,700,40,'sorry',mono=True)
K.txt(0,420,652,1340,24,'— accept this claim without a proof. It compiles. It is also'
                        ' recorded, forever, in the file.',color=LIGHT)
# NO REPOSITORY COUNTS HERE. A block of "66 files, 0 sorry" belongs with the
# case study, and the case study is not on this frame - quoting it here makes a
# general point about Lean look like a boast about one project.
K.txt(0,150,730,1620,26,'Anybody can write it, and it compiles. The difference from prose'
                        ' is that it is written down',color=LIGHT)
K.txt(0,150,768,1620,26,'\u2014 it sits in the file, and anybody who looks can find'
                        ' every one of them.',color=LIGHT)
K.dump(1,['ACCEPTED, OR REFUSED · AND THE ONE WAY TO CHEAT'],[False],
 ["""THE POINT OF THE WHOLE APPROACH IS ON THIS FRAME.

A referee can be tired, generous, or in a hurry. A kernel is none of those. It re-checks every step, and it does not know whose proof it is.

The right-hand box matters more than it looks. When Lean refuses, it tells you WHICH step it would not take. A 'no' with a specific unmet obligation is a to-do list. A 'no' without one is just a failure. That distinction is why this is worth doing at all.

Then be honest about the escape hatch. 'sorry' means: accept this without proof. It compiles. Anybody can write it. The difference from prose is that it is WRITTEN DOWN - you cannot wave at it, it sits in the file and anybody grepping finds it.

The four numbers are this repository, counted this morning: sixty-six files, and not one sorry, admit, or new axiom. Say 'counted this morning' - it is the kind of claim you should be able to date."""],
 'pipe-svg','lean2.svg','lean2.json',cumulative=False)

M=Fig('lnc','Nobody proves from nothing: Mathlib for the mathematics, physlib for'
            ' the physics, and everything a paper needs that is in neither.')
M.txt(0,150,130,1620,44,'Nobody proves anything from nothing')
M.txt(0,150,200,1620,26,'Every proof stands on definitions somebody else already wrote'
                        ' and checked.',color=LIGHT)
# PHYSICS DOES HAVE ONE. An earlier draft of this frame said it did not, which
# the speaker's own formalization slide disproves - it carries a screenshot of
# physlib. The interesting claim is not absence, it is scale.
# Both counted the same way on 2026-09-22: every .lean file on the project's
# own main branch. An earlier draft used 8,450, which was the pinned revision
# vendored into this repository - a different thing, and not comparable to a
# number taken from physlib's main branch.
LIB=[('9,146','Mathlib','the mathematics. Groups, measure, linear algebra, polytopes.'
                        '  Begun 2017.'),
     ('927','physlib','the physics. An open-source community project to digitalize'
                      ' results from physics into Lean 4.  Begun 2024.')]
for k,(n,name,d) in enumerate(LIB):
    y=300+k*150
    M.txt(0,150,y,280,52,n,color=INK if k==0 else LIGHT)
    M.txt(0,150,y+64,280,20,'.lean files',color=LIGHT)
    M.txt(0,440,y+4,420,34,name,color=INK)
    M.txt(0,440,y+54,1330,22,d,color=LIGHT)
M.line(0,150,640,1770,640,color=LIGHT,lw=1.4)
M.txt(0,150,674,1620,34,'Ten times the size, and seven years of a head start.')
M.txt(0,150,738,1620,26,'So the question for any paper is not "can Lean express this" \u2014'
                        ' it is how much of what the paper',color=LIGHT)
M.txt(0,150,776,1620,26,'stands on already exists, and how much somebody has to build'
                        ' first.',color=LIGHT)
M.txt(0,150,838,1620,26,'For a physics paper today, the honest answer is: a great deal'
                        ' has to be built first.')
M.dump(1,['THE LIBRARIES \u00b7 AND HOW MUCH IS ALREADY THERE'],[False],
 ["""THE FRAME FOR THIS AUDIENCE. Slow down; this is what a physicist should leave the room remembering.

Mathlib is the mathematics - nine thousand files of it, other people's work, and it is the reason formalizing a piece of mathematics is affordable at all. You are not proving anything from nothing; you are standing on a decade of somebody else's checked definitions.

physlib is the physics equivalent, and you saw its front page a few frames ago. Nine hundred files against nine thousand. It exists, it is a real community project, and it is an order of magnitude earlier in its life - the mathematics library lineage starts in 2017, physlib in 2024. Both counts are every .lean file on each project's own main branch, taken this morning; if somebody challenges a number, that is the definition to give them.

Then the honest question, which is the one that decides whether any of this is practical for us. It is not 'can Lean express my physics' - the answer to that is almost always yes, eventually. It is: how much of what my paper stands on is already in a library, and how much does somebody have to build first? For a physics paper today, a great deal has to be built first, and that is where the time goes.

If somebody asks how much: say you have not measured it, because you have not."""],
 'pipe-svg','lean3.svg','lean3.json',cumulative=False)

# ---- 8,9. the ending -----------------------------------------------------
C=Fig('ccl','What was shown, what it cost, and where it stops.')
C.txt(0,150,130,1620,46,'Where this actually is')
ROWS=[('shown','One paper, frozen. 29 claims and 46 dependencies for one theorem,'
                ' and a chain that runs.'),
      ('shown','Removing a claim has a measurable cost, so the structure can say'
                ' which parts carry load.'),
      ('not yet','The 613-claim extraction is not usable: every node is blocked'
                ' pending review, and nothing is accepted.'),
      ('not yet','The chain rests on a DAG written by hand, for this paper.'
                ' Automatic library lookup is zero lines of code.'),
      ('not shown','Whether the formal object means the physics you had in mind.'
                ' No kernel judges that.')]
Y=230
for k,(tag,t) in enumerate(ROWS):
    y=Y+k*98
    live = tag=='shown'
    C.box(0,150,y,190,68,color=INK if live else LIGHT,lw=2.8 if live else 1.6)
    C.txt(0,168,y+20,154,24,tag,color=INK if live else LIGHT)
    C.txt(0,376,y+18,1394,24,t,color=INK if live else LIGHT)
C.line(0,150,760,1770,760,color=LIGHT,lw=1.4)
C.txt(0,150,796,1620,34,'The claim is not that this works. It is that it is now'
                        ' small enough to argue about.')
C.txt(0,150,856,1620,24,'Everything on this frame is one paper and one run — a'
                        ' possibility with a receipt, not a result.',color=LIGHT)
C.dump(1,['IN CLOSING · WHAT IS SHOWN, AND WHAT IS NOT'],[False],
 ["""THE CONCLUSION. Do not soften it and do not oversell it - the credibility of the whole talk is spent or kept here.

Two things are shown. A chain for one theorem that actually runs, and a structure whose load-bearing parts can be measured rather than guessed.

Three things are not. The big extraction is not usable - every one of those six hundred nodes is blocked pending a review nobody has done. The chain that does run stands on a dependency graph I wrote by hand for this paper, and automatic library lookup - finding the matching declaration in Mathlib - is zero lines of code today. And none of this touches whether the formal object means the physics you had in mind; no kernel judges that.

Then the last line, which is the honest version of the whole talk: the claim is not that this works. It is that it has become small enough to argue about. A year ago I could not have shown you a specific place where it stops."""],
 'pipe-svg','conclusion.svg','conclusion.json',cumulative=False)

D=Fig('dsc','Three open questions: whether more compute and more intelligence is a'
            ' golden age for theoretical research, and whether that is the same thing'
            ' as a golden age for theoretical researchers.')
D.txt(0,150,190,1620,26,'Three questions I do not have answers to',color=LIGHT)
D.txt(0,150,256,1620,52,'A golden age for theoretical research.')
D.txt(0,150,330,1620,52,'But for theoretical researchers?')
D.line(0,150,450,1260,450,color=LIGHT,lw=1.4)
QS=['Does more compute and more intelligence excite you \u2014 or frustrate you?',
    'If a machine can produce the result, which part did you want to do?',
    'What would have to be checked before you would build on it?']
for k,q in enumerate(QS):
    y=500+k*68
    D.txt(0,150,y,50,26,f'{k+1}',color=LIGHT)
    D.txt(0,210,y,1050,26,q)
# the discussion glyph: two bubbles, drawn rather than pasted
for cx,cy,r,col in ((1480,640,88,INK),(1640,720,64,LIGHT)):
    D.dot(0,cx,cy,r,color=col,lw=3.0 if col==INK else 2.2)
    for k in (-1,0,1):
        D.dot(0,cx+k*r*0.42,cy,r*0.10,color=col,lw=1.0,fill=col)
D.line(0,1420,712,1386,772,color=INK,lw=3.0)
D.line(0,1386,772,1456,736,color=INK,lw=3.0)
D.txt(0,150,808,1000,24,'yingjian@lorentz.leidenuniv.nl',color=LIGHT)
D.txt(0,150,846,1000,24,'the deck, the records and the logs are all in the repository',color=LIGHT)
D.dump(1,['DISCUSSION'],[False],
 ["""THE LAST FRAME. Ask, then stop talking. Do not answer your own questions.

The framing is the useful part: it is entirely possible that this is a golden age for theoretical RESEARCH and a difficult one for theoretical RESEARCHERS, and those two things pull in opposite directions. Say that out loud - most people in the room have thought it and not said it.

Question one is the honest one and usually gets the room going: excited, or frustrated? Both answers are respectable and people will disagree in public, which is what you want.

Question two is the one that produces the best answers. If the machine can produce the result, which part did you actually want to do? Some people will say the proof; more will say the question, or the picture, or the argument about what it means.

Question three brings it back to this talk: what would have to be checked before you would build on it. That is the only question the last forty minutes was about.

If the room is slow, ask somebody what the ROOT claims of their last paper would be - the things they assumed without proof - and whether they would have been willing to write them down."""],
 'pipe-svg','discussion.svg','discussion.json',cumulative=False)
