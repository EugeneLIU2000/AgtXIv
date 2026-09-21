# -*- coding: utf-8 -*-
"""Why any of this matters - the frames before anything technical.

EVERY NUMBER ON THESE FRAMES IS READ OUT OF THIS REPOSITORY. That is not a
stylistic preference: the talk's whole claim is that unchecked assertions are
the problem, so a motivation slide carrying an invented ratio would refute the
talk before it started. Where the honest answer is "nobody measured that", the
frame says so and the speaker says so.

Deliberately NOT used here, because this deck has already spent them:
  warm #8C4A2F   = NOT FROM THIS PAPER
  a dashed ring  = a root, nothing below it
  a filled mark  = reached by the formalization order
  faint          = not part of this closure
Emphasis is carried by size, stroke weight and empty space instead.

Each frame is a function of its own step index, and ORDER is the list at the
bottom - so inserting a frame cannot silently renumber the ones after it.
"""
from frames_lib import Fig, INK, LIGHT, OPEN, PAPER

F=Fig('mot', 'Why a paper needs a dependency graph: one result with nothing under it,'
             ' six lines of answer over seven thousand of ground, structure nobody has'
             ' reviewed, kernel-checked but conditional theorems, modules that compile'
             ' without composing, what the project records and what it refuses to, the'
             ' checker as a download, and one statement reached twice.')
box, txt, line, dot, mark = F.box, F.txt, F.line, F.dot, F.mark
HS=34; SS=22; NS=46          # head, sub, number


def f_concession(S):
    """A result arrived. Look at the space under it."""
    mark(S,'theorem',960,300,96,lw=3.4)
    line(S,150,880,1770,880,color=LIGHT,lw=1.4)
    txt(S,150,838,520,SS,'where it came from',color=LIGHT)


def f_six_lines(S):
    """Six lines of answer, and the ground that had to exist first."""
    box(S,150,360,470,300)
    txt(S,186,404,398,NS,'6 lines')
    txt(S,186,470,398,SS,'one model call',color=LIGHT)
    txt(S,186,500,398,SS,'21 seconds',color=LIGHT)
    for k in range(6):                      # the file itself, at its real length
        line(S,186,558+k*18,186+150+(k%3)*58,558+k*18,color=LIGHT,lw=2.2)
    box(S,700,360,1070,300)
    txt(S,740,404,998,NS,'7,765 lines')
    txt(S,740,470,998,SS,'written by hand, so that',color=LIGHT)
    txt(S,740,500,998,SS,'six citations could be used',color=LIGHT)
    # a mass on purpose: six is countable, seven thousand is not, and drawing
    # it as units would be drawing a number nobody can check
    box(S,740,558,990,80,fill=INK,lw=0)


def f_unreviewed(S):
    """213 proposals in 71 minutes; 0 of them read by a person."""
    X0,X1,ROW=190,1730,520
    for k in range(213):                    # the real count, drawn as a field
        x=X0+k*(X1-X0)/212
        line(S,x,ROW-26,x,ROW+26,color=LIGHT,lw=1.3)
    txt(S,190,424,760,SS,'213 support groups, proposed in 71 minutes',color=LIGHT)
    txt(S,190,600,300,NS+22,'0')
    txt(S,300,626,900,SS,'of them reviewed by a person')


def f_conditional(S):
    """The kernel says yes. It does not say the premise can be met."""
    ROW=460; N=54; X0,X1=190,1730
    for k in range(N):
        x=X0+k*(X1-X0)/(N-1)
        mark(S,'theorem',x,ROW,9,lw=2.0)     # theorems: the deck's diamond
        if k<46:                             # 46 of the 54 carry such a premise
            line(S,x,ROW+11,x,ROW+96,color=LIGHT,lw=1.6)
    txt(S,190,372,600,SS,'54 kernel-checked theorems',color=LIGHT)
    txt(S,190,590,700,SS,'46 rest on a premise Lean does not',color=LIGHT)
    txt(S,190,620,700,SS,'establish can be satisfied at all',color=LIGHT)


def f_no_answer(S):
    """Eighty-two modules compile, and compose into nothing."""
    box(S,760,150,400,130)
    txt(S,796,190,328,SS,'the answer',color=LIGHT)
    BW,BH,PX,PY=70,8,92,46
    for k in range(82):
        r,c=divmod(k,14)
        box(S,327+c*PX,470+r*PY,BW,BH,fill=INK,lw=1.0)
    txt(S,327,410,600,SS,'82 of 82 modules compile',color=LIGHT)


def f_not_dollars(S):
    """What the project counts, and what it refuses to."""
    for k,(n,l) in enumerate([('7.6M','tokens'),('74','model calls'),
                              ('71','minutes'),('','dollars')]):
        x=190+k*400
        box(S,x,400,330,220)
        if n: txt(S,x+30,442,270,NS,n)
        txt(S,x+30,556,270,SS,l,color=LIGHT)


def f_library(S):
    """The expensive object is a download, and it is the same for everyone."""
    box(S,150,330,1060,330)
    txt(S,192,384,976,NS,'8.6 GB')
    txt(S,192,458,976,SS,'87,659 objects',color=LIGHT)
    txt(S,192,492,976,SS,'the library every proof is checked against,',color=LIGHT)
    txt(S,192,524,976,SS,'identical for everybody who downloads it',color=LIGHT)
    box(S,1290,330,480,330)
    txt(S,1330,384,400,NS,'137 s')
    txt(S,1330,458,400,SS,'to check this whole',color=LIGHT)
    txt(S,1330,492,400,SS,'chain, on a laptop',color=LIGHT)


def f_two_routes(S):
    """The same statement, reached twice."""
    for y,stops in ((420,11),(760,0)):
        line(S,300,y,1620,y,color=LIGHT,lw=1.4)
        mark(S,'external_contract',300,y,40,lw=3.0)   # a chain starts at an import
        mark(S,'theorem',1620,y,42,lw=3.0)            # and ends at the result
        for k in range(stops):                        # 11 definitions, the real count
            mark(S,'definition',430+k*106,y,15,lw=2.1)
    txt(S,300,326,900,SS,'with everything it passed through',color=LIGHT)
    txt(S,300,838,900,SS,'without',color=LIGHT)


# ---- the arc. Insert here; nothing below renumbers. ---------------------
ORDER=[
 (f_concession,  'ONE RESULT \u00b7 AND THE SPACE UNDERNEATH IT'),
 (f_six_lines,   '6 LINES OF ANSWER \u00b7 7,765 LINES OF GROUND'),
 (f_unreviewed,  '213 SUPPORT GROUPS \u00b7 0 REVIEWED BY A PERSON'),
 (f_conditional, '54 KERNEL-CHECKED THEOREMS \u00b7 46 OF THEM CONDITIONAL'),
 (f_no_answer,   '82 OF 82 MODULES COMPILE \u00b7 THE ANSWER IS STILL EMPTY'),
 (f_not_dollars, 'TOKENS, CALLS AND SECONDS ARE RECORDED \u00b7 DOLLARS ARE NOT'),
 (f_library,     '8.6 GB OF LIBRARY \u00b7 137 SECONDS OF CHECKING'),
 (f_two_routes,  'THE SAME STATEMENT, TWICE \u00b7 ONCE WITH ITS INTERMEDIATES'),
]
for k,(fn,_) in enumerate(ORDER): fn(k)
METER=[m for _,m in ORDER]
OPENMETER=[False]*len(ORDER)

NOTE=[
"""OPEN BY CONCEDING THE RESULT. I am not here to tell you the machine is wrong. Take the diamond as given - it arrived, it is probably right, and arguing with it is not my talk.

Everything I am going to say is about the space underneath it, and about that grey line at the bottom, which is where it came from. When a result arrives with nothing between it and its sources, there is nothing for a reader to do except believe it or not. That is a new situation for us. It is not that the answer is suspect; it is that the answer is the only thing we were handed.

Hold that empty region in mind - the rest of the talk is an attempt to put something in it.""",

"""THE INVERSION, and it is the most surprising thing I found in my own logs.

On the left: the one piece of Lean in this project that a model wrote and a kernel accepted. Six lines. One model call, 21.4 seconds. You will see that proof itself, with its own caveats attached, later in the deck - for now only its size matters.

On the right: 7,765 lines of Lean in formal/AgtXIvRootMath, written so that six citations in one paper could be used at all - definitions, bridges, the statements of things the paper simply cites.

The drawing is NOT to scale; the true ratio is about 1,300 to 1. One qualifier, because somebody will check: "written by hand" means authored rather than model-generated - 25 of the 32 recorded source adaptations later in this deck do touch files in this package, so it is not untouched, it is not autoformalized. Note what that means for concern one. The worry is usually "who will check the ten thousand lines the AI wrote". In this project the AI wrote six. The ten thousand lines are the theory-building that had to happen first - and that is the work nobody gets credit for, because it is not an answer to anything.""",

"""THE ASYMMETRY, measured - and measured on my own work rather than asserted about the field, because I cannot measure the field and neither can anyone who has tried.

Seventy-one minutes of model time produced this: 613 claim nodes and 213 support groups extracted from one paper. Every one of those 213 groups is a proposal that some set of claims, taken together, discharges another claim.

The number underneath is the point. accepted_support_edges: 0. all_judgements_unreviewed: true. Not one of them has been looked at by a person.

That is the shape of the whole problem in two numbers from one repository. Producing candidate structure is now minutes of machine time. Reviewing it is unchanged - it is a person reading, at the speed a person reads. Nothing in this project makes review faster, and I want to be honest that it does not: what it changes is that the unreviewed thing is now a small, enumerable, addressable list instead of a paragraph of prose.

Source: schema v0.3/runs/research-terra-continuation-20260920/summary.json""",

"""WHAT A KERNEL-CHECKED YES ACTUALLY MEANS. This project has 64 kernel-checked declarations - 54 theorems, 9 definitions, 1 inductive - resting on exactly three axioms (propext, Classical.choice, Quot.sound) and no project-introduced axiom. That part is real, and it is machine-verified.

Now the honest part. The audit's own metric PREMISE_NONVACUITY_UNKNOWN is 46 of 54: forty-six of those theorems carry at least one Prop hypothesis whose inhabitation Lean does not establish. The kernel confirms the implication. It does not confirm that the premise can ever be met - and a vacuously true theorem looks identical to a useful one from the outside.

I want to be careful: this is not a flaw in Lean, and it is not fraud. It is what "verified" means, stated precisely. The eight unstubbed marks are gathered at the right only for legibility; the audit does not order them.

Source: schema v0.3/runs/lean-evidence-20260919/lean-audit.json, coverage[2].""",

"""CONCERN ONE, IN ITS SHARPEST FORM. The largest single verification event in this project is the common-epoch migration: 82 modules, and all 82 compile under leanprover/lean4 v4.33.0. 74 declarations audited, 44 composition witnesses recorded.

And the same file records query_chain_complete = false and query_declaration = null. Eighty-two modules compile and compose into no answer. The empty box at the top is not a rhetorical device; it is a null in a JSON file.

That is what an isolated proof is. Not a wrong proof - a proof with no socket on either end. Getting those modules to compile also took 32 recorded source adaptations, each one a machine edit to somebody's proof, each stamped AGENT_NORMALIZED_UNREVIEWED.

Source: schema v0.3/epoch-migration/runs/20260919-full-case/full-case-audit.json.""",

"""CONCERN TWO, AND I HAVE TO BE CAREFUL HERE, because this is the concern my own repository can say the least about.

What it does record: 74 model receipts, 7,591,305 input tokens, 97,677 output tokens, 4,280 seconds - 71 minutes of model time for the entire project, on an ordinary personal account quota. No cluster, no allocation, no scheduler.

What it refuses to record is the fourth box. Every one of 23,583 cost_microusd fields is null; 225 receipts carry cost_basis = CHATGPT_ACCOUNT_QUOTA_NOT_DOLLAR_METERED. I did not leave the price out to be coy - a token count stays true and a price does not, so the deck records the thing that will still be checkable in a year.

Say the caveat out loud: 71 minutes is an argument from smallness, not a measured comparison against anyone's large-compute baseline. I have no such comparison, and neither, as far as I can tell, does anybody else. "Theory will become a capital game" is itself an unmeasured claim.""",

"""CONCERN TWO AGAIN, and this is the one place where I think there is a real answer rather than a caveat.

The expensive object in this picture is not the model time. It is the checker: the Lean library the proofs are checked against - 87,659 objects, 8.6 gigabytes. That is the fixed capital of the whole enterprise.

And it is a DOWNLOAD. Not an allocation, not a quota, not a queue. Everybody who works this way gets the identical one, and a proof that the kernel accepts against it is accepted for everybody. Checking this project's entire audited chain took 136.68 seconds across four receipts on one laptop.

So: if the worry is that theoretical research becomes a competition in who can afford the compute, then the most useful property of a proof kernel is that it is cheap, shared, and the same for everyone. That is not a refutation of the worry - the generation side may well concentrate. It is the one counterexample in this repository that I can put a number on.

One caveat, because it is in the file: the audit records that the 8.6 GB figure comes from an inventory manifest whose hash it verified, and that it did not independently re-hash those library bytes. Source: schema v0.3/runs/proof-worker-normalization-attempt02-20260919/audit-proof-walk-attempt05.json, scope_notes[0].""",

"""CONCERN THREE, which I think is the one that actually matters.

Two routes to the same statement, drawn at the same height because they end in the same place. The lower one is what an answer looks like when it arrives alone. The upper one is the same result with the things it passed through still attached.

Concretely, from this project: the closure of one theorem is 29 claims, and 11 of them are definitions - more than a third of what the headline result rests on is not a result at all. It is vocabulary. That is the part that transfers to the next problem, and it is exactly the part a good answer throws away.

Then hand over: for the rest of the talk, the question is what would have to come back instead of a single mark.""",
]

F.dump(len(ORDER), METER, OPENMETER, NOTE, 'pipe-svg', 'motivation.svg',
       'motivation.json', cumulative=False)   # eight separate pictures
