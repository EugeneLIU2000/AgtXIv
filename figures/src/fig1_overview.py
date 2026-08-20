# -*- coding: utf-8 -*-
"""Figure 1 — AgtXIv method overview: backward archaeology, forward build."""
from figlib import *

W, H = 1680, 880
f = Fig(W, H)
M = 64
f.title(M, 74, "Resolving a theorem query into a verified dependency path",
        kicker="AgtXIv · method overview")
f.caption(M, 100, "A query is answered by a build receipt, not a reading list. Backward archaeology finds the load-bearing imports; "
                  "forward verification rebuilds only what is missing.")

colw, gap = 366, 58
xL = M
xR = M + colw + gap
xgap = xL + colw + gap / 2

# ---------- query in -------------------------------------------------------
qy = 140
f.rect(xL, qy, colw, 70, fill=ACC_FILL, stroke=ACC, sw=1.8)
f.text(xL + 18, qy + 27, "theorem query", size=12.5, fill=ACC, weight="700")
f.text(xL + 18, qy + 51, "claim:closed-form-rom", size=14, fill=INK, font=MONO)

top = 288
bh, bstep = 78, 112
f.arrow(xL + colw / 2, qy + 70, xL + colw / 2, top - 8, stroke=GAP, sw=1.8)

f.text(xL, top - 34, "1 · BACKWARD  —  dependency archaeology", size=12.5, fill=GAP, weight="700", ls="0.8")
f.text(xR, top - 34, "2 · FORWARD  —  verification build", size=12.5, fill=ACC, weight="700", ls="0.8")

back = [("target claim", "the statement actually asked for"),
        ("direct local support", "what this paper proves itself"),
        ("imported premises", "exact claim + version, not the paper"),
        ("root contracts", "accepted, reusable, or declared frontier")]
fwd  = [("verified root exports", "reused unchanged, never rebuilt"),
        ("intermediate local delta", "only this paper's new reasoning"),
        ("target local delta", "the residual that must be proved"),
        ("versioned target export", "scoped contract + status vector")]

for i, (t, s) in enumerate(back):
    y = top + i * bstep
    f.module(xL, y, colw, bh, t, s,
             fill=GAP_FILL if i == 3 else WHITE,
             stroke=GAP if i in (0, 3) else LINE,
             sw=1.8 if i in (0, 3) else 1.4, tsize=14.5, ssize=11.5)
    if i < 3:
        f.arrow(xL + colw / 2, y + bh, xL + colw / 2, y + bstep - 4, stroke=GAP, sw=1.8)

for i, (t, s) in enumerate(fwd):
    y = top + i * bstep
    f.module(xR, y, colw, bh, t, s,
             fill=ACC_FILL if i == 3 else WHITE,
             stroke=ACC if i in (0, 3) else LINE,
             sw=1.8 if i in (0, 3) else 1.4, tsize=14.5, ssize=11.5)
    if i < 3:
        f.arrow(xR + colw / 2, y + bh, xR + colw / 2, y + bstep - 4, stroke=ACC, sw=1.8)

# roots feed the forward build — routed through the gutter, never across a column
ybot = top + 3 * bstep + bh
ymid = top + bh / 2
f.path(f"M {xL + colw/2} {ybot} L {xL + colw/2} {ybot + 30} "
       f"Q {xL + colw/2} {ybot + 44} {xL + colw/2 + 14} {ybot + 44} "
       f"L {xgap - 14} {ybot + 44} Q {xgap} {ybot + 44} {xgap} {ybot + 30} "
       f"L {xgap} {ymid + 14} Q {xgap} {ymid} {xgap + 14} {ymid} L {xR - 7} {ymid}",
       stroke=LIGHT, sw=1.7, dash="6 5")
f.text(xgap + 8, ybot + 66, "roots fixed  →  build forward", size=11.5, fill=MID)

# ---------- right: the receipt --------------------------------------------
xO = xR + colw + gap
ow = W - xO - M
f.text(xO, top - 34, "3 · QUERYRESOLUTION  —  the receipt", size=12.5, fill=INK, weight="700", ls="0.8")

rows = [("accepted imports", "reused from the registry", ACC),
        ("dependency closure", "everything actually used", ACC),
        ("local delta", "what this query had to build", INK),
        ("blocked frontier", "first unresolved source", GAP),
        ("dependency versions", "pins the whole closure", LIGHT)]
ry = top
for k, v, col in rows:
    f.rect(xO, ry, ow, 66, fill=WHITE, stroke=LINE, sw=1.4)
    f.circle(xO + 22, ry + 33, 5.5, fill=col)
    f.text(xO + 42, ry + 28, k, size=14, fill=INK, weight="600")
    f.text(xO + 42, ry + 49, v, size=11.5, fill=MID)
    ry += 74

f.rect(xO, ry + 10, ow, 96, fill=FILL, stroke="none", sw=0)
f.text(xO + 22, ry + 40, "Cached, then reused.", size=13.5, fill=INK, weight="700")
f.text(xO + 22, ry + 64, "A later query sharing a prefix inherits the accepted", size=12.5, fill=DARK)
f.text(xO + 22, ry + 84, "closure and pays only for its own delta.", size=12.5, fill=DARK)

# ---------- bottom rule ----------------------------------------------------
by = H - 96
f.band(M, by, W - 2 * M, 58,
       "the reusable unit is the claim-level contract, not the paper — and the frontier is reported, never hidden.",
       fill=FILL, bold_prefix="Two invariants:")
f.text(W - M, H - 20, "AgtXIv v0.4  ·  §2.1 two opposite directions  ·  §2.5 QueryResolution",
       size=11, fill=LIGHT, anchor="end")

f.save("fig1_overview.svg")
