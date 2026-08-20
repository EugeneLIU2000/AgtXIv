# -*- coding: utf-8 -*-
"""Minimal SVG builder implementing the paper-craft `paper-figure` style spec.

Style contract (from skills/paper-comic/references/styles/paper-figure.md):
  white / very light bg · clean vector modules · precise arrows, main path
  thicker · sans-serif short labels · dark grey dominant + 1-2 accent colours
  used for the core contribution / key path / contrast, never decoration.
"""
from xml.sax.saxutils import escape

# ---- palette: greys dominant, exactly two accents -------------------------
INK      = "#14171C"   # near-black, primary structure
DARK     = "#3A4048"   # secondary text
MID      = "#6B7480"   # captions
LIGHT    = "#9AA2AC"   # de-emphasised
LINE     = "#D4D9E0"   # hairlines / inactive borders
FILL     = "#F4F6F8"   # neutral module fill
WHITE    = "#FFFFFF"

ACC      = "#2563EB"   # accent 1 — verified / accepted path
ACC_FILL = "#E8EFFD"
GAP      = "#DC2626"   # accent 2 — gap / blocked / frontier
GAP_FILL = "#FCEAEA"

FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Menlo, Consolas, monospace"


class Fig:
    def __init__(self, w, h, bg=WHITE):
        self.w, self.h = w, h
        self.parts = []
        self.bg = bg

    # -- primitives ---------------------------------------------------------
    def rect(self, x, y, w, h, fill=WHITE, stroke=LINE, sw=1.5, r=8, dash=None, op=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{op}"' if op else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.5, dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linecap="{cap}"{d}/>')

    def path(self, d, stroke=INK, sw=1.5, fill="none", dash=None, marker=True, mk=None):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{mk or self._mk(stroke)})"' if marker else ""
        self.parts.append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{ds}{m}/>')

    def arrow(self, x1, y1, x2, y2, stroke=INK, sw=1.8, dash=None):
        self.path(f"M {x1} {y1} L {x2} {y2}", stroke=stroke, sw=sw, dash=dash)

    def elbow(self, x1, y1, x2, y2, stroke=INK, sw=1.8, dash=None, r=10, via="h"):
        """right-angled connector with rounded corner"""
        if via == "h":
            mx = (x1 + x2) / 2
            sgn_y = 1 if y2 > y1 else -1
            sgn_x = 1 if x2 > mx else -1
            d = (f"M {x1} {y1} L {mx - r*(1 if mx>x1 else -1)} {y1} "
                 f"Q {mx} {y1} {mx} {y1 + r*sgn_y} L {mx} {y2 - r*sgn_y} "
                 f"Q {mx} {y2} {mx + r*sgn_x} {y2} L {x2} {y2}")
        else:
            my = (y1 + y2) / 2
            sgn_x = 1 if x2 > x1 else -1
            sgn_y = 1 if y2 > my else -1
            d = (f"M {x1} {y1} L {x1} {my - r*(1 if my>y1 else -1)} "
                 f"Q {x1} {my} {x1 + r*sgn_x} {my} L {x2 - r*sgn_x} {my} "
                 f"Q {x2} {my} {x2} {my + r*sgn_y} L {x2} {y2}")
        self.path(d, stroke=stroke, sw=sw, dash=dash)

    def text(self, x, y, s, size=14, fill=INK, weight="normal", anchor="start",
             font=None, ls=None, op=None):
        f = font or FONT
        l = f' letter-spacing="{ls}"' if ls else ""
        o = f' opacity="{op}"' if op else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{f}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{l}{o}>'
            f'{escape(s)}</text>')

    def lines(self, x, y, rows, size=13, fill=MID, lh=17, anchor="start", weight="normal", font=None):
        for i, r in enumerate(rows):
            self.text(x, y + i * lh, r, size=size, fill=fill, anchor=anchor,
                      weight=weight, font=font)

    def circle(self, cx, cy, r, fill=ACC, stroke="none", sw=0):
        self.parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    # -- composites ---------------------------------------------------------
    def module(self, x, y, w, h, title, sub=None, fill=WHITE, stroke=LINE, sw=1.5,
               tsize=15, tcolor=INK, ssize=12, scolor=MID, r=8, mono=False, dash=None):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, r=r, dash=dash)
        cx = x + w / 2
        if sub:
            self.text(cx, y + h / 2 - 3, title, size=tsize, fill=tcolor,
                      weight="600", anchor="middle", font=MONO if mono else None)
            self.text(cx, y + h / 2 + 15, sub, size=ssize, fill=scolor, anchor="middle")
        else:
            self.text(cx, y + h / 2 + 5, title, size=tsize, fill=tcolor,
                      weight="600", anchor="middle", font=MONO if mono else None)

    def chip(self, x, y, s, size=11, fill=FILL, color=DARK, pad=9, h=22, mono=True):
        w = len(s) * (size * 0.62) + pad * 2
        self.rect(x, y, w, h, fill=fill, stroke="none", sw=0, r=h / 2)
        self.text(x + w / 2, y + h / 2 + 4, s, size=size, fill=color,
                  anchor="middle", font=MONO if mono else None, weight="600")
        return w

    def step(self, cx, cy, n, r=13, fill=INK):
        self.circle(cx, cy, r, fill=fill)
        self.text(cx, cy + 5, str(n), size=13, fill=WHITE, anchor="middle", weight="700")

    def caption(self, x, y, s, size=12.5, fill=MID):
        self.text(x, y, s, size=size, fill=fill)

    def title(self, x, y, main, kicker=None):
        if kicker:
            self.text(x, y - 22, kicker.upper(), size=11.5, fill=ACC,
                      weight="700", ls="1.6")
        self.text(x, y, main, size=25, fill=INK, weight="700")

    def band(self, x, y, w, h, s, fill=FILL, color=INK, size=14, weight="600", r=8, bold_prefix=None):
        self.rect(x, y, w, h, fill=fill, stroke="none", sw=0, r=r)
        if bold_prefix:
            self.text(x + 22, y + h / 2 + 5, bold_prefix, size=size, fill=color, weight="700")
            off = len(bold_prefix) * (size * 0.56) + 30
            self.text(x + off, y + h / 2 + 5, s, size=size, fill=color, weight="400")
        else:
            self.text(x + w / 2, y + h / 2 + 5, s, size=size, fill=color,
                      anchor="middle", weight=weight)

    # -- output -------------------------------------------------------------
    def _mk(self, color):
        key = "mk" + color.replace("#", "")
        if key not in getattr(self, "_marks", set()):
            if not hasattr(self, "_marks"):
                self._marks = set()
            self._marks.add(key)
        return key

    def svg(self):
        marks = getattr(self, "_marks", set())
        defs = "".join(
            f'<marker id="{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" '
            f'markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M 0 0.6 L 10 5 L 0 9.4 z" fill="#{k[2:]}"/></marker>' for k in marks)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}">'
            f'<defs>{defs}</defs>'
            f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>'
            + "".join(self.parts) + "</svg>")

    def save(self, path):
        # markers are collected during draw; svg() must run after all parts exist
        open(path, "w", encoding="utf-8").write(self.svg())
        print("wrote", path)

def wrap(text, max_chars):
    """Greedy word wrap — never splits a word."""
    out, line = [], ""
    for w in text.split():
        cand = (line + " " + w).strip()
        if line and len(cand) > max_chars:
            out.append(line); line = w
        else:
            line = cand
    if line:
        out.append(line)
    return out
