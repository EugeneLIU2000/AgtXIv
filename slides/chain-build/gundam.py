# -*- coding: utf-8 -*-
"""One picture for the discussion page: the same machine, twice.

The question the speaker wants to leave the room with is whether a theorist is
the pilot of this thing or the one underneath it. So the drawing is the SAME
silhouette both times - identical geometry, one <use> of one symbol - and the
only thing that changes is where the person is. If the machine differed between
the panels the picture would be arguing something; it is not, the audience is.

Solid silhouette rather than the deck's usual hollow line work, on purpose: this
frame is a metaphor, not a measurement, and it should not be mistaken for one.
"""
INK='#1A1A16'; LIGHT='#8A8A80'; MID='#B9B9B2'
W,H=1920,1080

def mech(sx, sy, s):
    """A Gundam-ish silhouette in a local 200x300 box, scaled and placed.

    The torso is ONE polygon from collar to skirt. Drawn as separate chest,
    abdomen and waist blocks it left enclosed white rectangles between the arms
    and the waist - holes in the middle of a silhouette, which read as mistakes
    rather than as armour.
    """
    P=[]; add=P.append
    # V-fin and the two side vents
    # the V-fin proper: two blades angling out from the forehead, plus the
    # small centre crest between them. A single spike with two side spurs read
    # as a crown, which is the one thing this silhouette must not look like.
    add('<polygon points="100,27 82,6 88,27"/>')
    add('<polygon points="100,27 118,6 112,27"/>')
    add('<polygon points="96,26 100,15 104,26"/>')
    # helmet and jaw
    add('<polygon points="88,23 112,23 114,35 109,45 91,45 86,35"/>')
    add('<polygon points="93,44 107,44 104,50 96,50"/>')
    add('<rect x="94" y="48" width="12" height="6"/>')
    # backpack and thruster fins, behind everything
    add('<rect x="84" y="50" width="32" height="34"/>')
    add('<polygon points="66,50 84,56 84,82 64,74"/>')
    add('<polygon points="134,50 116,56 116,82 136,74"/>')
    # shoulders: angular pauldrons that flare up and out
    add('<polygon points="40,74 46,52 78,46 80,88 52,94"/>')
    add('<polygon points="160,74 154,52 122,46 120,88 148,94"/>')
    # ONE torso, collar to skirt
    add('<polygon points="74,50 126,50 126,90 118,112 116,122 84,122 82,112 74,90"/>')
    # skirt armour: front plates and two side plates
    add('<polygon points="70,120 130,120 134,152 112,154 103,145 97,145 88,154 66,152"/>')
    add('<polygon points="56,120 72,122 70,154 54,150"/>')
    add('<polygon points="144,120 128,122 130,154 146,150"/>')
    # arms
    add('<polygon points="48,88 76,86 76,126 50,128"/>')
    add('<polygon points="152,88 124,86 124,126 150,128"/>')
    add('<polygon points="46,126 78,126 76,170 48,172"/>')
    add('<polygon points="154,126 122,126 124,170 152,172"/>')
    add('<rect x="48" y="170" width="26" height="17"/>')
    add('<rect x="126" y="170" width="26" height="17"/>')
    # legs: thigh, knee armour, shin, foot
    add('<polygon points="80,152 100,152 98,200 78,200"/>')
    add('<polygon points="120,152 100,152 102,200 122,200"/>')
    add('<polygon points="74,198 100,198 100,216 72,216"/>')
    add('<polygon points="126,198 100,198 100,216 128,216"/>')
    add('<polygon points="76,214 98,214 96,260 78,260"/>')
    add('<polygon points="124,214 102,214 104,260 122,260"/>')
    add('<polygon points="68,258 100,258 103,278 62,278"/>')
    add('<polygon points="132,258 100,258 97,278 138,278"/>')
    return (f'<g transform="translate({sx},{sy}) scale({s})" fill="{INK}">'
            + ''.join(P) + '</g>')

def person(x, y, h, fill=INK, lying=False):
    """A human at 1/10 the machine's height - which is roughly the real ratio,
    and the only reason the two panels can be read at a glance."""
    u=h/8.0
    if not lying:
        return (f'<g fill="{fill}">'
                f'<circle cx="{x}" cy="{y-7*u}" r="{1.05*u}"/>'
                f'<rect x="{x-0.95*u}" y="{y-5.8*u}" width="{1.9*u}" height="{3.2*u}" rx="{0.4*u}"/>'
                f'<rect x="{x-2.3*u}" y="{y-5.5*u}" width="{1.3*u}" height="{2.9*u}" rx="{0.5*u}"/>'
                f'<rect x="{x+1.0*u}" y="{y-5.5*u}" width="{1.3*u}" height="{2.9*u}" rx="{0.5*u}"/>'
                f'<rect x="{x-0.95*u}" y="{y-2.7*u}" width="{0.85*u}" height="{2.7*u}"/>'
                f'<rect x="{x+0.1*u}" y="{y-2.7*u}" width="{0.85*u}" height="{2.7*u}"/>'
                f'</g>')
    return (f'<g fill="{fill}">'
            f'<circle cx="{x-3.4*u}" cy="{y-1.0*u}" r="{1.05*u}"/>'
            f'<rect x="{x-2.2*u}" y="{y-1.9*u}" width="{3.2*u}" height="{1.9*u}" rx="{0.4*u}"/>'
            f'<rect x="{x-1.6*u}" y="{y-2.9*u}" width="{2.6*u}" height="{1.1*u}" rx="{0.5*u}"'
            f' transform="rotate(-24 {x-1.6*u} {y-2.9*u})"/>'
            f'<rect x="{x+1.0*u}" y="{y-1.6*u}" width="{2.7*u}" height="{0.85*u}"/>'
            f'<rect x="{x+1.0*u}" y="{y-0.75*u}" width="{2.4*u}" height="{0.85*u}"'
            f' transform="rotate(14 {x+1.0*u} {y-0.75*u})"/>'
            f'</g>')

S=1.74                      # mech is 300 local units tall -> 522 px
MECH_TOP=178
GROUND=MECH_TOP+278*S       # the soles, not the box
LX, RX = 430, 1150          # left edge of each mech's local box

o=[f'<svg class="gun-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"'
   f' role="img" aria-label="The same machine twice: once with a person in the'
   f' cockpit, once with a person lying at its feet.">',
   f'<style>.gt{{font-family:Calibri,Carlito,sans-serif}}</style>']

# NO CAST SHADOW. The first draft put a grey wedge on the right to say "in its
# shadow"; at this size it read as a stray grey slab on the floor. The figure
# lying at the foot says it without help.

# ---- left: the pilot -----------------------------------------------------
o.append(mech(LX, MECH_TOP, S))
# an open hatch in the chest, and someone standing in it
hx, hy = LX+80*S, MECH_TOP+58*S
hw, hh = 40*S, 46*S
o.append(f'<rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" fill="#fff"/>')
o.append(person(hx+hw/2, hy+hh-6, 62))
o.append(f'<rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" fill="none"'
         f' stroke="{INK}" stroke-width="3.4"/>')

# ---- right: the one underneath -------------------------------------------
o.append(mech(RX, MECH_TOP, S))
o.append(person(RX+44*S, GROUND+26, 76, lying=True))

# ---- ground, and the two readings ----------------------------------------
o.append(f'<line x1="{LX-200}" y1="{GROUND+2}" x2="{RX+200*S+40}" y2="{GROUND+2}"'
         f' stroke="{LIGHT}" stroke-width="1.6"/>')
o.append(f'<text class="gt" x="{LX+100*S}" y="{GROUND+128}" text-anchor="middle"'
         f' font-size="40" fill="{INK}">in the cockpit</text>')
o.append(f'<text class="gt" x="{LX+100*S}" y="{GROUND+176}" text-anchor="middle"'
         f' font-size="24" fill="{LIGHT}">you are the one flying it</text>')
o.append(f'<text class="gt" x="{RX+100*S}" y="{GROUND+128}" text-anchor="middle"'
         f' font-size="40" fill="{INK}">under the foot</text>')
o.append(f'<text class="gt" x="{RX+100*S}" y="{GROUND+176}" text-anchor="middle"'
         f' font-size="24" fill="{LIGHT}">it arrives either way</text>')
o.append(f'<text class="gt" x="{(LX+RX)/2+100*S}" y="{MECH_TOP+260}" text-anchor="middle"'
         f' font-size="34" fill="{LIGHT}">or</text>')
o.append('</svg>')
open('gundam.svg','w',encoding='utf-8').write('\n'.join(o))
print('gundam.svg written')
