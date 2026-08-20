# -*- coding: utf-8 -*-
"""Figure 5 — Lean is the kernel, not the oracle."""
from figlib import *

W, H = 1680, 720
f = Fig(W, H)
M = 64
f.title(M, 74, "Lean is the trusted kernel — it is not an oracle for physics",
        kicker="AgtXIv · formalization loop")
f.caption(M, 100, "The kernel decides one thing: does the conclusion follow from the encoded assumptions. "
                  "Whether the encoding is the intended object is decided by a separate, source-blind audit.")

# ---------- the loop -------------------------------------------------------
ly = 176
bw, bgap, bh = 300, 46, 108
stages = [
    ("MathClaimIR", "normalized statement,\nquantifiers, domain", ACC),
    ("Lean 4 + mathlib", "pinned environment,\nno sorry / admit", ACC),
    ("source-blind\nbacktranslation", "restate the declaration\nwithout seeing the paper", INK),
    ("alignment audit", "does the restatement\nmatch the source claim?", GAP),
]
for i, (t, s, col) in enumerate(stages):
    x = M + i * (bw + bgap)
    f.rect(x, ly, bw, bh, fill=ACC_FILL if col == ACC else (GAP_FILL if col == GAP else WHITE),
           stroke=col, sw=1.8)
    tl = t.split("\n")
    ty = ly + (30 if len(tl) == 1 else 24)
    for j, line in enumerate(tl):
        f.text(x + bw / 2, ty + j * 19, line, size=15, fill=INK, anchor="middle", weight="700")
    sy_ = ly + (58 if len(tl) == 1 else 66)
    for j, line in enumerate(s.split("\n")):
        f.text(x + bw / 2, sy_ + j * 17, line, size=11.5, fill=MID, anchor="middle")
    if i < len(stages) - 1:
        f.arrow(x + bw + 4, ly + bh / 2, x + bw + bgap - 4, ly + bh / 2, stroke=DARK, sw=2.0)

# verdict split out of the audit
ax = M + 3 * (bw + bgap)
vy = ly + bh + 52
f.path(f"M {ax + bw/2} {ly + bh} L {ax + bw/2} {vy - 14}", stroke=GAP, sw=2.0)

vw = 300
f.rect(ax, vy, vw, 62, fill=WHITE, stroke=ACC, sw=1.8)
f.text(ax + vw / 2, vy + 26, "aligned", size=14, fill=ACC, anchor="middle", weight="700")
f.text(ax + vw / 2, vy + 46, "promote the math axis only", size=11.5, fill=MID, anchor="middle")
f.rect(ax, vy + 78, vw, 62, fill=WHITE, stroke=GAP, sw=1.8)
f.text(ax + vw / 2, vy + 104, "drift detected", size=14, fill=GAP, anchor="middle", weight="700")
f.text(ax + vw / 2, vy + 124, "rewire or rescope, do not promote", size=11.5, fill=MID, anchor="middle")

# repair edge back to MathClaimIR
f.path(f"M {ax} {vy + 109} L {ax - 22} {vy + 109} "
       f"Q {ax - 34} {vy + 109} {ax - 34} {vy + 97} L {ax - 34} {ly + bh + 24} "
       f"Q {ax - 34} {ly + bh + 12} {ax - 46} {ly + bh + 12} "
       f"L {M + bw/2 + 12} {ly + bh + 12} "
       f"Q {M + bw/2} {ly + bh + 12} {M + bw/2} {ly + bh}", stroke=GAP, sw=1.7, dash="6 5")
f.text(M + bw / 2 + 18, ly + bh + 34, "repair the encoding, re-enter the loop", size=11.5, fill=GAP)

# ---------- what the kernel does and does not decide -----------------------
gy = vy + 176
gw = (W - 2 * M - 40) / 2

f.rect(M, gy, gw, 150, fill=WHITE, stroke=ACC, sw=1.8)
f.chip(M + 22, gy + 20, "KERNEL_CHECKED", size=11, fill=ACC_FILL, color=ACC, h=26)
f.text(M + 22, gy + 78, "The conclusion follows from the definitions", size=14, fill=INK, weight="600")
f.text(M + 22, gy + 100, "and assumptions you encoded.", size=14, fill=INK, weight="600")
f.text(M + 22, gy + 126, "Mechanically checkable. Reproducible from a clean environment.", size=12, fill=MID)

f.rect(M + gw + 40, gy, gw, 150, fill=WHITE, stroke=GAP, sw=1.8)
f.chip(M + gw + 62, gy + 20, "STILL UNDECIDED", size=11, fill=GAP_FILL, color=GAP, h=26)
f.text(M + gw + 62, gy + 78, "Whether that encoding is the physical object,", size=14, fill=INK, weight="600")
f.text(M + gw + 62, gy + 100, "regime, and observable you meant.", size=14, fill=INK, weight="600")
f.text(M + gw + 62, gy + 126, "Needs a domain reviewer. No kernel can settle it.", size=12, fill=MID)

f.text(W - M, H - 20, "AgtXIv v0.4  ·  §3.2 mathematical kernel  ·  §8.7 kernel checks  ·  §8.8 semantic-alignment review",
       size=11, fill=LIGHT, anchor="end")

f.save("fig5_lean.svg")
