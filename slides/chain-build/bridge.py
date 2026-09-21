# -*- coding: utf-8 -*-
"""One frame between the imported opening and the rest of the deck.

It does two jobs. It narrows the scope out loud - of the four things slide 24
says a theorist might want to trust, everything after this is about one of
them - and it announces the change of visual language, because the frames
before it are the source deck in full colour and everything after is this
project's monochrome.
"""
from frames_lib import Fig, INK, LIGHT, PAPER

F=Fig('bri', 'Of the four things a theorist might want to trust, this talk is about'
             ' mathematical correctness, and about one paper and one theorem.')
box, txt, line = F.box, F.txt, F.line
SS=22; TS=26; HS=34

TRUST=[('The story','What did the paper actually state?'),
       ('Mathematical correctness','Does the conclusion follow from encoded assumptions?'),
       ('Computational reproducibility','Can the numerical result be reproduced?'),
       ('Physical-semantic alignment','Does the formal object represent the intended physics?')]
for k,(t,q) in enumerate(TRUST):
    r,c=divmod(k,2); x=150+c*830; y=250+r*230
    live = k==1
    box(0,x,y,760,180,lw=3.6 if live else 1.8, color=INK if live else LIGHT)
    txt(0,x+26,y+30,708,TS,t,color=INK if live else LIGHT)
    txt(0,x+26,y+92,708,SS,q,color=LIGHT)
line(0,150,760,1710,760,color=LIGHT,lw=1.4)
txt(0,150,790,1680,TS,'one paper · one theorem · and what it actually rests on')
txt(0,150,842,1680,SS,
    'not whether the formalisation means the physics you had in mind — no kernel judges that',
    color=LIGHT)
txt(0,150,876,1680,SS,
    'and not reproducibility — there is no numerical claim in the case study',color=LIGHT)

F.dump(1, ['OF THE FOUR, THIS TALK IS ABOUT THE SECOND'], [False],
       ["""THE BRIDGE, and it is worth saying the scope out loud before the room starts wondering.

Of the four boxes on the trust slide four frames back, everything after this one is about MATHEMATICAL CORRECTNESS - does the conclusion follow from the stated assumptions - plus a little of THE STORY, because you cannot check a conclusion until you have pinned down what was actually claimed.

It is NOT about physical-semantic alignment. Whether a Lean definition of the reduced stabilizer polytope means the physics you had in mind is a judgement no kernel makes, and this project does not pretend otherwise - the records carry alignment_notes precisely because that gap cannot be closed mechanically.

It is NOT about computational reproducibility either; there is no numerical claim in the case study.

Two practical notes. The slides up to here are the opening deck reproduced as it is, in its own colours; from here the deck is monochrome, and colour means exactly two things - warm for NOT FROM THIS PAPER and teal for A JUNCTION. And the opening curve was a claim about the field that neither I nor anyone else has measured. What comes next is the same argument measured on my own logs, which I can."""],
       'pipe-svg', 'bridge.svg', 'bridge.json', cumulative=False)
