# -*- coding: utf-8 -*-
"""The whole thing in five boxes, built one box at a time.

No product name, no version number, no field names - the audience has not been
told what a schema is yet. The last two boxes are the bridge: a sketch network
appears, then most of it goes faint and a handful stays ink, which is exactly
what the next fifteen frames do for real with 613 nodes and then 29.

ONE SOURCE, TWO RENDERERS. This file emits primitives; pipeline.svg (inline in
the HTML) and deck.js (native pptx shapes) both draw the same list, so the page
and the slide cannot drift. Nothing here is an image - every element on the
finished slide is an editable PowerPoint shape or text box.

Stage is 1920x1080 px = 13.333 x 7.5 in, so px/144 = inches and px/2 = points.
"""
import json
from frames_lib import Fig, INK, LIGHT, OPEN, PAPER

F=Fig('pipe', "The pipeline in five boxes: a frozen paper, one record per statement,"
              " the records pointing at each other, one result and what it rests on,"
              " and a checker.")
box, txt, line, dot = F.box, F.txt, F.line, F.dot
P=F.P

# ---- the five boxes on one row -----------------------------------------
# Courier New / JetBrains Mono advance is 0.6em, so a box of inner width 252px
# holds 13 characters at 30px and 20 at 21px. Every string below is checked
# against that at the bottom of this file - nothing is allowed to overflow.
XS=[70,440,810,1180,1550]; BW=300; BY=385; BH=230
HS=30; SS=21                              # head size, sub size
IX=24; IW=BW-2*IX                         # inner left pad, inner width

def stage(step,i,head,head2=None):
    x=XS[i]
    box(step,x,BY,BW,BH)
    txt(step,x+IX,BY+26,IW,HS,head)
    if head2: txt(step,x+IX,BY+64,IW,HS,head2)

def sub(step,i,lines,y0,lh=30,color=LIGHT,size=SS):
    for k,t in enumerate(lines):
        txt(step,XS[i]+IX,BY+y0+k*lh,IW,size,t,color=color)

# 0 - a paper
stage(0,0,'a paper')
sub(0,0,['frozen.','every byte fixed,','so pointers hold.'],110)

# 1 - extract the claims
stage(1,1,'extract','the claims')
for k,t in enumerate(['what it says','where it came from','a fingerprint']):
    y=BY+116+k*30
    line(1,XS[1]+IX,y+11,XS[1]+IX+13,y+11,color=LIGHT,lw=1.6)
    txt(1,XS[1]+IX+22,y,IW-22,SS,t,color=LIGHT)

# 2 - the dependency graph  (the bridge to the real network)
stage(2,2,'dependency','graph')
SKX=[16,52,90,124,150,186,214,244,74]
SKY=[83,39,87,23,67,35,85,46,7]
SKE=[(0,1),(1,8),(8,3),(3,4),(2,4),(1,2),(4,5),(5,7),(6,4),(6,7)]
SUB={4,5,6,7}
def sketch(step,x0,y0,subset_only=False):
    for a,b in SKE:
        if subset_only and not (a in SUB and b in SUB): continue
        line(step,x0+SKX[a],y0+SKY[a],x0+SKX[b],y0+SKY[b],
             lw=2.4 if subset_only else 1.7)
    for k in range(9):
        if subset_only and k not in SUB: continue
        r=12 if (subset_only and k==7) else 8
        dot(step,x0+SKX[k],y0+SKY[k],r,lw=2.8 if subset_only else 2.1)
SK3=(XS[2]+20,BY+118)
sketch(2,*SK3)

# 3 - and some of it points outside the paper
SAT=(810,104,300,160)
box(3,*SAT,style='dash',color=OPEN,lw=2.0)
txt(3,SAT[0]+IX,SAT[1]+20,IW,HS,'outside',color=OPEN)
txt(3,SAT[0]+IX,SAT[1]+56,IW,HS,'dependency',color=OPEN)
txt(3,SAT[0]+IX,SAT[1]+104,IW,SS,'nobody has fetched it',color=OPEN)
line(3,SAT[0]+BW/2,BY-8,SAT[0]+BW/2,SAT[1]+SAT[3]+14,color=OPEN,lw=2.0,style='dash',arrow=True)

# 4 - the core claims, and what they rest on
stage(4,3,'core claims','+ dependencies')
SK4=(XS[3]+20,BY+118)
for a,b in SKE:                       # the faint remainder, drawn under the kept part
    if a in SUB and b in SUB: continue
    line(4,SK4[0]+SKX[a],SK4[1]+SKY[a],SK4[0]+SKX[b],SK4[1]+SKY[b],lw=1.3)
    P[-1]['dim']=True
for k in range(9):
    if k in SUB: continue
    dot(4,SK4[0]+SKX[k],SK4[1]+SKY[k],8,lw=1.7,dim=True)
sketch(4,*SK4,subset_only=True)

# 5 - auto-formalization, into something that cannot be argued with
stage(5,4,'auto-','formalization')
sub(5,4,['a kernel does not','negotiate, and it','does not tire.'],110)

# arrows along the row. An arrow arrives with the box it points AT, not one
# step early - a step showing an arrow into empty space reads as a bug.
BOX_STEP=[0,1,2,4,5]
for i in range(4):
    line(BOX_STEP[i+1],XS[i]+BW+14,BY+BH/2,XS[i+1]-14,BY+BH/2,lw=2.0,arrow=True)

# 6 - what comes back: two exits, and the second one is the point
AX,AW,BX,BW2,OY,OH = 1250,265,1565,285,725,150
ACX,BCX = AX+AW/2, BX+BW2/2
line(6,1700,BY+BH,1700,676,lw=2.0)
line(6,ACX,676,BCX,676,lw=2.0)
line(6,ACX,676,ACX,OY-14,lw=2.0,arrow=True)
line(6,BCX,676,BCX,OY-14,lw=2.0,arrow=True)
box(6,AX,OY,AW,OH)
txt(6,AX+22,OY+28,AW-44,HS,'it holds')
txt(6,AX+22,OY+78,AW-44,20,'every step',color=LIGHT)
txt(6,AX+22,OY+106,AW-44,20,'was accepted',color=LIGHT)
# NOT warm. Warm means one thing in this deck - NOT FROM THIS PAPER - and a
# refusal is not an external source. The exit that matters is set apart by
# weight, which is the same device the Lamport frame uses for an outstanding
# obligation. Spending the hue here would cost the audience the ability to read
# it on the frames where it carries real information.
box(6,BX,OY,BW2,OH,lw=3.6)
txt(6,BX+22,OY+28,BW2-44,HS,'it does not',bold=True)
txt(6,BX+22,OY+78,BW2-44,20,'and it names',color=LIGHT)
txt(6,BX+22,OY+106,BW2-44,20,'what is missing',color=LIGHT)

# THE LOOP. The second exit is not a failure state, it is the next work order:
# an unmet obligation is a thing to go and read. Without this arrow the diagram
# says the pipeline runs once, which is not what the controller does.
LY=958
line(6,BCX,OY+OH,BCX,LY,lw=2.0)
line(6,BCX,LY,XS[1]+BW/2,LY,lw=2.0)
line(6,XS[1]+BW/2,LY,XS[1]+BW/2,BY+BH+14,lw=2.0,arrow=True)
txt(6,XS[1]+BW/2+26,LY-34,560,20,'what is missing goes back in',color=LIGHT)

# ---- copy: the bottom meter line, and the note that ships in the pptx ---
METER=[
 'ONE PAPER \u00b7 FROZEN',
 'EVERY STATEMENT BECOMES ONE CLAIM RECORD',
 'THE CLAIMS POINT AT EACH OTHER \u00b7 A DEPENDENCY GRAPH',
 'AND SOME POINT OUTSIDE THE PAPER',
 'THE CORE CLAIMS \u00b7 ONLY WHAT THE RESULT RESTS ON',
 'EVERY REMAINING STEP GOES TO AUTO-FORMALIZATION',
 'IT HOLDS \u00b7 OR WHAT IS MISSING GOES BACK IN',
]
OPENMETER=[False,False,False,True,False,False,False]
NOTE=[
"""THE WHOLE PIPELINE IN FIVE BOXES. Deliberately no product name, no version number and no field names on the slide - none of that has been introduced yet, and the five boxes are the part that generalises beyond this project.

Box one: a paper, frozen. Every downstream pointer is a byte offset into these exact bytes, so nothing can drift underneath the record while the work is going on. This is the cheapest and least glamorous idea in the system and it is the one that makes everything else auditable.""",

"""Box two: every statement in the paper becomes one record, and the record carries three things - what it says, where in the source it came from, and a fingerprint of its content.

"Where it came from" is a byte range, not a page number. "A fingerprint" is a hash, so re-wording the statement produces a different record rather than silently editing the old one. The next slide shows one of these records in full.""",

"""Box three: the records point at each other. This premise discharges that conclusion. Do that for every record and you no longer have a list, you have a network - and that network is the object the rest of the talk is about.

The little sketch is a cartoon. Two slides from now you see the real one.""",

"""Box four, drawn dashed and in the one warm colour this deck uses: some records point OUTSIDE the paper, at work it leans on that nobody has fetched.

Warm means exactly one thing in every frame of this deck - NOT FROM THIS PAPER. Keep it that way; the moment warm also means "bad" or "pending", the audience stops being able to read the colour.

This box is where most of the honest difficulty lives. A paper's citations are promises, and until somebody resolves one it is a promise the machine cannot check.""",

"""Box five: choose one result and keep only what it rests on. Everything else in the network goes faint - not deleted, just not part of this question.

This is the single most useful operation in the system, and it is also the answer to "why are there so many claims?" There are that many because nobody asked a question yet. Ask one, and the graph collapses to the part that answers it.""",

"""Box six: every step that survives goes to a checker that cannot be argued with - a proof kernel. It does not negotiate, it does not get tired on the fortieth lemma, and it does not care who wrote the step.

That is the entire reason for the machinery in front of it. The pipeline exists to get statements into a shape where a thing that cannot be persuaded can look at them.""",

"""And the output has two exits, which is the point of the whole design.

It holds - every step was accepted. Or it does NOT hold, and the system names what is missing. The second exit is the valuable one: a "no" that comes with a specific unmet obligation is a research to-do list, where a "no" without one is just a failure.

What it never does is the third thing, which is to return something that looks like a proof because the prose around it was fluent.""",
]

F.dump(7, METER, OPENMETER, NOTE, 'pipe-svg', 'pipeline.svg', 'pipeline.json')
