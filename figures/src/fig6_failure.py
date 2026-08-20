# -*- coding: utf-8 -*-
"""Figure 6 — lifecycle, failure classification, and the non-promotion rule."""
from figlib import *

W, H = 1680, 880
f = Fig(W, H)
M = 64
f.title(M, 74, "A failed check refines the graph locally — it never silently promotes",
        kicker="AgtXIv · lifecycle and failure semantics")
f.caption(M, 100, "Every node carries a lifecycle state. A failure is classified before it is repaired, "
                  "and two different kinds of red are never merged into one.")

# ---------- lifecycle ------------------------------------------------------
ly = 168
f.text(M, ly, "LIFECYCLE OF A NODE, CHAIN, OR EXPORT", size=10.5, fill=LIGHT, weight="700", ls="1.3")
main = ["PROPOSED", "SOURCE_VALIDATED", "DEPENDENCY_MAPPED", "PARTIALLY_VERIFIED", "VERIFICATION_CLOSED"]
sx = M
sy = ly + 26
for i, st in enumerate(main):
    last = i == len(main) - 1
    wch = f.chip(sx, sy, st, size=11.5,
                 fill=ACC_FILL if last else FILL, color=ACC if last else DARK, h=32)
    if i < len(main) - 1:
        f.arrow(sx + wch + 6, sy + 16, sx + wch + 30, sy + 16, stroke=LIGHT, sw=1.6)
    sx += wch + 36
closed_x = sx - 36

# off-ramps
off = [("BLOCKED", "an import or evidence is unresolved"),
       ("DISPUTED", "the literature does not agree"),
       ("SUPERSEDED", "a newer version replaces it")]
ox = M
oy = sy + 66
for name, desc in off:
    wch = f.chip(ox, oy, name, size=11, fill=GAP_FILL, color=GAP, h=28)
    f.text(ox + wch + 12, oy + 19, desc, size=12, fill=MID)
    ox += wch + 12 + len(desc) * 6.4 + 44

f.text(M, oy + 62, "VERIFICATION_CLOSED is query-scoped: every axis relevant to the declared scope is acceptable — for this query.",
       size=12.5, fill=INK, weight="600")
f.text(M, oy + 84, "It is not universal certainty, and it does not propagate upward on its own.",
       size=12.5, fill=MID)

f.line(M, oy + 116, W - M, oy + 116, stroke="#E6EAF0", sw=1.5)

# ---------- failure classification -----------------------------------------
fy = oy + 152
f.text(M, fy, "A FAILURE IS CLASSIFIED BEFORE IT IS REPAIRED", size=10.5, fill=LIGHT, weight="700", ls="1.3")

classes = [
    ("LOCAL_BUILD_FAILURE", "missing lemma, bridge, unfolding, or premise retrieval",
     "EXPAND_LOCAL", "add the missing step, rebuild this region only", ACC),
    ("ALIGNMENT_FAILURE", "wrong object, lost assumption, scope or exactness drift",
     "REWIRE_OR_RESCOPE", "re-encode or narrow the claim, then re-audit", DARK),
    ("SOURCE_OR_FOUNDATION_GAP", "unsupported import, missing source step, counterexample",
     "ESCALATE_OR_BLOCK", "record the blocker; do not fill the gap with prose", GAP),
]
cw = (W - 2 * M - 2 * 36) / 3
for i, (tag, desc, act, adesc, col) in enumerate(classes):
    x = M + i * (cw + 36)
    y = fy + 26
    f.rect(x, y, cw, 214, fill=WHITE, stroke=LINE, sw=1.4)
    f.chip(x + 20, y + 20, tag, size=10.5, fill=FILL, color=DARK, h=26)
    f.lines(x + 20, y + 76, wrap(desc, 44), size=12.5, fill=MID, lh=19)
    f.arrow(x + cw / 2, y + 112, x + cw / 2, y + 132, stroke=col, sw=1.8)
    f.chip(x + 20, y + 140, act, size=10.5, fill=ACC_FILL if col == ACC else (GAP_FILL if col == GAP else FILL),
           color=col, h=26)
    f.lines(x + 20, y + 182, wrap(adesc, 46), size=11.5, fill=DARK, lh=17)

# ---------- two reds -------------------------------------------------------
ry = fy + 26 + 214 + 40
f.text(M, ry, "TWO DIFFERENT REDS — MERGING THEM DESTROYS THE INFORMATION", size=10.5, fill=GAP, weight="700", ls="1.3")

hw = (W - 2 * M - 36) / 2
f.rect(M, ry + 26, hw, 128, fill=WHITE, stroke="#E8B4B0", sw=1.6)
f.chip(M + 22, ry + 46, "PROOF_GAP", size=11, fill=GAP_FILL, color=GAP, h=26)
f.chip(M + 150, ry + 46, "THEOREM_NOT_REFUTED", size=11, fill=FILL, color=DARK, h=26)
f.text(M + 22, ry + 100, "The route is incomplete; the statement still stands.", size=13, fill=INK, weight="600")
f.text(M + 22, ry + 124, "Record a repair path and keep the claim conditional.", size=12, fill=MID)

f.rect(M + hw + 36, ry + 26, hw, 128, fill=WHITE, stroke=GAP, sw=1.9)
f.chip(M + hw + 58, ry + 46, "CLAIM_FALSE", size=11, fill=GAP_FILL, color=GAP, h=26)
f.chip(M + hw + 190, ry + 46, "EXPLICIT_COUNTEREXAMPLE", size=11, fill=GAP_FILL, color=GAP, h=26)
f.text(M + hw + 58, ry + 100, "A concrete instance refutes it — it must be retracted.", size=13, fill=INK, weight="600")
f.text(M + hw + 58, ry + 124, "Export only the properties that survive.", size=12, fill=MID)

f.text(W - M, H - 20, "AgtXIv v0.4  ·  §6.3 DAG completion and iterative resolution  ·  §6.5 lifecycle status  ·  §6.6 public justification",
       size=11, fill=LIGHT, anchor="end")

f.save("fig6_failure.svg")
