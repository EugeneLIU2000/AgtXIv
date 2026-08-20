# -*- coding: utf-8 -*-
"""Figure 3 — MathContract: the reusable unit is the claim, not the paper."""
from figlib import *

W, H = 1680, 800
f = Fig(W, H)
M = 64
f.title(M, 74, "The reusable unit is a claim-level contract, not a paper",
        kicker="AgtXIv · minimal data model")
f.caption(M, 100, "A citation binds two documents. A MathContract binds one normalized statement to one version, "
                  "so a later query can import it without re-reading the paper.")

# ---------- left: what dependency binds to ---------------------------------
lx, lw = M, 456
f.text(lx, 156, "WHAT THE DEPENDENCY BINDS TO", size=10.5, fill=LIGHT, weight="700", ls="1.3")

# paper-level
py = 180
f.rect(lx, py, lw, 158, fill=WHITE, stroke=LINE, sw=1.4)
f.text(lx + 22, py + 30, "paper-level  (citation graph)", size=13, fill=MID, weight="600")
f.rect(lx + 22, py + 48, 172, 46, fill=FILL, stroke=LINE, sw=1.2)
f.text(lx + 108, py + 76, "Paper A", size=13.5, fill=DARK, anchor="middle", weight="600")
f.rect(lx + 262, py + 48, 172, 46, fill=FILL, stroke=LINE, sw=1.2)
f.text(lx + 348, py + 76, "Paper B", size=13.5, fill=DARK, anchor="middle", weight="600")
f.arrow(lx + 194, py + 71, lx + 262, py + 71, stroke=LIGHT, sw=1.6)
f.text(lx + 228, py + 60, "cites", size=10.5, fill=LIGHT, anchor="middle")
f.text(lx + 22, py + 124, "Which result? Under which hypotheses?", size=12, fill=GAP)
f.text(lx + 22, py + 144, "Load-bearing, or background? Unanswerable.", size=12, fill=GAP)

# claim-level
qy = py + 186
f.rect(lx, qy, lw, 176, fill=ACC_FILL, stroke=ACC, sw=1.8)
f.text(lx + 22, qy + 30, "claim-level  (AgtXIv)", size=13, fill=ACC, weight="700")
f.rect(lx + 22, qy + 48, 190, 52, fill=WHITE, stroke=ACC, sw=1.3)
f.text(lx + 117, qy + 70, "A · Claim A.3", size=12.5, fill=INK, anchor="middle", weight="600")
f.text(lx + 117, qy + 89, "the importing statement", size=10, fill=MID, anchor="middle")
f.rect(lx + 244, qy + 48, 190, 52, fill=WHITE, stroke=ACC, sw=1.3)
f.text(lx + 339, qy + 70, "B · Theorem B.2", size=12.5, fill=INK, anchor="middle", weight="600")
f.text(lx + 339, qy + 89, "the imported statement", size=10, fill=MID, anchor="middle")
f.arrow(lx + 212, qy + 74, lx + 244, qy + 74, stroke=ACC, sw=1.9)
f.text(lx + 22, qy + 128, "IMPORTS  +  an explicit assumption-matching record", size=12, fill=INK, weight="600")
f.text(lx + 22, qy + 152, "pinned to a contract version, so it can be reused", size=12, fill=DARK)

# ---------- right: the contract anatomy ------------------------------------
rx = lx + lw + 56
rw = W - rx - M
f.text(rx, 156, "MATHCONTRACT — WHAT ONE RECORD MUST CARRY", size=10.5, fill=LIGHT, weight="700", ls="1.3")

cy0 = 180
ch0 = 466
f.rect(rx, cy0, rw, ch0, fill=WHITE, stroke=INK, sw=1.8)
f.rect(rx, cy0, rw, 52, fill=INK, stroke="none", sw=0, r=8)
f.rect(rx, cy0 + 40, rw, 12, fill=INK, stroke="none", sw=0, r=0)
f.text(rx + 22, cy0 + 33, "math-contract:claim.closed-form-rom", size=14, fill=WHITE, font=MONO)
f.chip(rx + rw - 132, cy0 + 14, "v0.4", size=11, fill="#2E3440", color="#9FB4E8", h=24)

fields = [
    ("normalized statement", "quantifiers · domain · exactness", INK),
    ("assumptions", "no Pauli-active dependency; G_M perfect", INK),
    ("theorem imports", "exact-graph-program · perfect-graph-antiblocker", ACC),
    ("source anchor", "frozen bundle hash + span in draft.tex", INK),
    ("Lean binding", "declaration, or an explicit GAP — never blank", ACC),
    ("status vector", "one value per axis, never one Boolean", INK),
    ("blockers", "what stops promotion, named and open", GAP),
]
fy = cy0 + 76
for k, v, col in fields:
    f.circle(rx + 26, fy + 8, 4, fill=col)
    f.text(rx + 44, fy + 13, k, size=13.5, fill=INK, weight="600")
    f.text(rx + 250, fy + 13, v, size=12.5, fill=MID)
    fy += 40
    if k != "blockers":
        f.line(rx + 22, fy - 14, rx + rw - 22, fy - 14, stroke="#EDF0F4", sw=1)

# version-pinning strip inside the card
vy = cy0 + ch0 - 96
f.rect(rx + 22, vy, rw - 44, 74, fill=FILL, stroke="none", sw=0)
f.text(rx + 40, vy + 27, "An importer binds to", size=12, fill=DARK)
f.chip(rx + 178, vy + 12, "contract@v0.4", size=11, fill=WHITE, color=ACC, h=24)
f.text(rx + 320, vy + 27, "— not to “the paper”.", size=12, fill=DARK)
f.text(rx + 40, vy + 55, "An upstream version bump invalidates only the affected downstream closure.",
       size=12, fill=MID)

# ---------- progressive standardization ------------------------------------
sy = cy0 + ch0 + 42
f.text(rx, sy, "A CONTRACT NEED NOT REACH ACCEPTANCE IN ONE PASS", size=10.5, fill=LIGHT, weight="700", ls="1.3")
stages = ["INDEXED", "NORMALIZED", "DEPENDENCY_MAPPED", "FORMALLY_CONNECTED", "ACCEPTED_CONTRACT"]
sxx = rx
for i, st in enumerate(stages):
    last = i == len(stages) - 1
    wch = f.chip(sxx, sy + 20, st, size=10.5,
                 fill=ACC_FILL if last else FILL, color=ACC if last else DARK, h=28)
    if i < len(stages) - 1:
        f.arrow(sxx + wch + 5, sy + 34, sxx + wch + 25, sy + 34, stroke=LIGHT, sw=1.5)
    sxx += wch + 30

# left column bottom note
ny = qy + 176 + 42
f.text(lx, ny, "WHY THIS MATTERS", size=10.5, fill=LIGHT, weight="700", ls="1.3")
f.lines(lx, ny + 26, [
    "A paper exports many results at different maturity.",
    "Binding reuse to the paper inherits all of them —",
    "including the ones that are still unverified.",
], size=13, fill=DARK, lh=22)

f.text(W - M, H - 20, "AgtXIv v0.4  ·  §2.3 claim-level inheritance  ·  §5.0 MathContract  ·  §2.6 progressive standardization",
       size=11, fill=LIGHT, anchor="end")

f.save("fig3_contract.svg")
