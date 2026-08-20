# -*- coding: utf-8 -*-
"""Figure 4 — registry as search + package manager + incremental build."""
from figlib import *

W, H = 1680, 760
f = Fig(W, H)
M = 64
f.title(M, 74, "The registry behaves like a package manager with an incremental build",
        kicker="AgtXIv · query execution")
f.caption(M, 100, "The expensive offline path standardizes contracts once. The online path reuses the accepted closure "
                  "and pays only for the frontier that is actually missing.")

# ---------- offline lane ---------------------------------------------------
oy = 168
f.text(M, oy, "OFFLINE  —  done once, amortised over every later query", size=10.5, fill=LIGHT, weight="700", ls="1.3")
off = ["freeze sources", "extract candidates", "normalize contracts", "map dependencies",
       "connect declarations", "cache verified closures"]
ow_, ogap = 232, 18
for i, t in enumerate(off):
    x = M + i * (ow_ + ogap)
    f.module(x, oy + 22, ow_, 54, t, fill=FILL, stroke=LINE, sw=1.3, tsize=13)
    if i < len(off) - 1:
        f.arrow(x + ow_ + 2, oy + 49, x + ow_ + ogap - 2, oy + 49, stroke=LIGHT, sw=1.5)

f.line(M, oy + 112, W - M, oy + 112, stroke="#E6EAF0", sw=1.5)

# ---------- online lane ----------------------------------------------------
ny = oy + 148
f.text(M, ny, "ONLINE  —  what a single query actually costs", size=10.5, fill=ACC, weight="700", ls="1.3")

steps = [
    ("normalize the query", "resolve to a contract address", FILL, LINE, INK),
    ("retrieve candidates", "search proposes, never promotes", FILL, LINE, INK),
    ("reuse accepted closure", "zero rebuild cost", ACC_FILL, ACC, ACC),
    ("locate missing frontier", "the first unresolved import", GAP_FILL, GAP, GAP),
    ("build only the local delta", "the sole new work", ACC_FILL, ACC, ACC),
    ("cache the extended path", "next query inherits it", FILL, LINE, INK),
]
sw_, sgap, sh = 232, 18, 96
for i, (t, s, fill, stroke, col) in enumerate(steps):
    x = M + i * (sw_ + sgap)
    y = ny + 26
    f.rect(x, y, sw_, sh, fill=fill, stroke=stroke, sw=1.8 if stroke in (ACC, GAP) else 1.4)
    f.step(x + 26, y + 26, i + 1, r=13, fill=col if col != INK else DARK)
    f.text(x + sw_ / 2, y + 58, t, size=13.2, fill=INK, anchor="middle", weight="600")
    f.text(x + sw_ / 2, y + 78, s, size=11, fill=MID, anchor="middle")
    if i < len(steps) - 1:
        f.arrow(x + sw_ + 2, y + sh / 2, x + sw_ + sgap - 2, y + sh / 2,
                stroke=ACC if i in (1, 2, 3, 4) else LIGHT, sw=2.0 if i in (2, 3, 4) else 1.5)

# cost annotation under the two paid steps
cy_ = ny + 26 + sh + 16
x3 = M + 3 * (sw_ + sgap)
x4 = M + 4 * (sw_ + sgap)
f.path(f"M {x3 + 12} {cy_} L {x3 + 12} {cy_ + 16} L {x4 + sw_ - 12} {cy_ + 16} L {x4 + sw_ - 12} {cy_}",
       stroke=GAP, sw=1.5, marker=False)
f.text((x3 + x4 + sw_) / 2, cy_ + 38, "the only part this query pays for",
       size=12.5, fill=GAP, anchor="middle", weight="600")

# ---------- invalidation ---------------------------------------------------
iy = cy_ + 76
f.text(M, iy, "WHEN AN UPSTREAM CONTRACT CHANGES", size=10.5, fill=LIGHT, weight="700", ls="1.3")

gx, gy = M, iy + 26
node_r = 22
cols = [(gx + 60, gy + 60, "root", ACC), (gx + 230, gy + 20, "A", ACC), (gx + 230, gy + 100, "B", ACC),
        (gx + 400, gy + 20, "C", GAP), (gx + 400, gy + 100, "D", ACC), (gx + 570, gy + 60, "target", GAP)]
edges = [(0, 1, ACC), (0, 2, ACC), (1, 3, GAP), (2, 4, ACC), (3, 5, GAP), (4, 5, ACC)]
for a, b, col in edges:
    x1, y1 = cols[a][0], cols[a][1]
    x2, y2 = cols[b][0], cols[b][1]
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / L, dy / L
    f.arrow(x1 + ux * (node_r + 3), y1 + uy * (node_r + 3),
            x2 - ux * (node_r + 6), y2 - uy * (node_r + 6),
            stroke=col, sw=2.0 if col == GAP else 1.5,
            dash="5 4" if col == GAP else None)
for cx_, cy2, lab, col in cols:
    f.circle(cx_, cy2, node_r, fill=GAP_FILL if col == GAP else WHITE, stroke=col, sw=2.0)
    f.text(cx_, cy2 + 5, lab, size=11.5, fill=col if col == GAP else DARK, anchor="middle", weight="700")

f.text(gx + 60, gy + 60 + node_r + 26, "version bump", size=11.5, fill=MID, anchor="middle")

# legend for the graph
lgx = gx + 660
f.rect(lgx, gy + 4, W - M - lgx, 116, fill=FILL, stroke="none", sw=0)
f.circle(lgx + 26, gy + 34, 6, fill=GAP)
f.text(lgx + 44, gy + 39, "invalidated — must be rechecked", size=12.5, fill=INK, weight="600")
f.circle(lgx + 26, gy + 66, 6, fill=ACC)
f.text(lgx + 44, gy + 71, "untouched — stays accepted, no rebuild", size=12.5, fill=INK, weight="600")
f.text(lgx + 26, gy + 100, "Invalidation follows the dependency edges, not the calendar.",
       size=12, fill=MID)

f.text(W - M, H - 20, "AgtXIv v0.4  ·  §2.4 search, registry and incremental build  ·  §2.5 QueryResolution cache",
       size=11, fill=LIGHT, anchor="end")

f.save("fig4_incremental.svg")
