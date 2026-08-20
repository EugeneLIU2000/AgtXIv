# -*- coding: utf-8 -*-
"""Figure 2 — four verification axes that must not be collapsed."""
from figlib import *

W, H = 1680, 900
f = Fig(W, H)
M = 64
f.title(M, 74, "One claim carries four independent verification axes",
        kicker="AgtXIv · verification semantics")
f.caption(M, 100, "Each axis answers a different question, has its own status enum, and is promoted by its own evidence. "
                  "Collapsing them into a single Boolean destroys the information a reader needs.")

# ---------- the claim ------------------------------------------------------
cx, cy, cw, ch = M, 250, 268, 132
f.rect(cx, cy, cw, ch, fill=INK, stroke="none", sw=0)
f.text(cx + 20, cy + 34, "ONE CLAIM", size=11, fill="#8FA6D8", weight="700", ls="1.4")
f.text(cx + 20, cy + 66, "claim:closed-form-rom", size=13.5, fill=WHITE, font=MONO)
f.text(cx + 20, cy + 96, "not one status —", size=12.5, fill="#B9C4DA")
f.text(cx + 20, cy + 116, "a status vector", size=12.5, fill="#B9C4DA")

# ---------- lanes ----------------------------------------------------------
lx = 396                     # lane start
lw_q = 470                   # question block
sx = lx + lw_q + 26          # status chips
sw_ = 300
px = sx + sw_ + 26           # promoted-by
pw = W - px - M

top, lh, lgap = 196, 128, 16

axes = [
    ("Source fidelity", "What did the paper actually state?",
     ["UNCHECKED", "PASSED", "MISALIGNED"],
     "frozen source bundle + span-level anchor review", MID, False),
    ("Mathematical correctness", "Does the conclusion follow from the encoded assumptions?",
     ["PARTIALLY_FORMALIZED", "KERNEL_CHECKED", "FAILED"],
     "Lean 4 + pinned mathlib, no sorry / admit", ACC, True),
    ("Computational reproducibility", "Can the reported number be regenerated?",
     ["NOT_ATTEMPTED", "REPRODUCED", "BLOCKED"],
     "code + data + seed + tolerance, rerun from a clean checkout", MID, False),
    ("Physical-semantic alignment", "Does the formal object mean the intended physics?",
     ["AGENT_REVIEWED", "HUMAN_REVIEWED", "CONTESTED"],
     "domain reviewer — no kernel can decide this", GAP, False),
]

for i, (name, q, states, promo, col, hero) in enumerate(axes):
    y = top + i * (lh + lgap)
    # question block
    f.rect(lx, y, lw_q, lh, fill=ACC_FILL if hero else WHITE,
           stroke=col if hero else LINE, sw=1.8 if hero else 1.4)
    f.step(lx + 34, y + 40, i + 1, r=14, fill=col if hero else DARK)
    f.text(lx + 60, y + 45, name, size=15.5, fill=INK, weight="700")
    f.text(lx + 22, y + 78, q, size=12.5, fill=DARK)
    f.text(lx + 22, y + 104, "independent of the other three", size=11.5, fill=LIGHT)

    # status enum
    f.text(sx, y + 22, "STATUS ENUM", size=10, fill=LIGHT, weight="700", ls="1.2")
    yy = y + 36
    for s in states:
        hot = s in ("KERNEL_CHECKED",)
        bad = s in ("FAILED", "BLOCKED", "MISALIGNED", "CONTESTED")
        f.chip(sx, yy, s, size=10.5,
               fill=ACC_FILL if hot else (GAP_FILL if bad else FILL),
               color=ACC if hot else (GAP if bad else DARK), h=24)
        yy += 30

    # promoted by
    f.text(px, y + 22, "PROMOTED ONLY BY", size=10, fill=LIGHT, weight="700", ls="1.2")
    words, line, out = promo.split(), "", []
    for wd in words:
        if len(line + " " + wd) > 40:
            out.append(line); line = wd
        else:
            line = (line + " " + wd).strip()
    out.append(line)
    f.lines(px, y + 50, out, size=12.5, fill=DARK, lh=19)

    # claim -> lane connector
    gx, ymid_l, yl = lx - 30, cy + ch / 2, y + lh / 2
    down = 1 if yl > ymid_l else -1
    f.path(f"M {cx + cw} {ymid_l} L {gx - 12} {ymid_l} "
           f"Q {gx} {ymid_l} {gx} {ymid_l + 12 * down} L {gx} {yl - 12 * down} "
           f"Q {gx} {yl} {gx + 12} {yl} L {lx - 7} {yl}",
           stroke=col if hero else LINE, sw=1.8 if hero else 1.3, dash=None if hero else "5 4")

# ---------- bottom gate ----------------------------------------------------
by = H - 104
f.rect(M, by, W - 2 * M, 62, fill=GAP_FILL, stroke="none", sw=0, r=8)
f.text(M + 24, by + 38, "A clean Lean build answers axis 2 only", size=15, fill=GAP, weight="700")
f.text(M + 24 + 300, by + 38,
       "— and only under the definitions you encoded. It certifies nothing on axes 1, 3, or 4.",
       size=14, fill=INK)
f.text(W - M, H - 20, "AgtXIv v0.4  ·  §3 trusted verification layers  ·  §6.4 verification axes",
       size=11, fill=LIGHT, anchor="end")

f.save("fig2_axes.svg")
