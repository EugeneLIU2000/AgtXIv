"""SVG shape primitives for the closure figure.

Shape carries node KIND; it is the secondary encoding the palette validator
requires (CVD separation sits in the 6-8 floor band, so colour alone is not
legal). Every shape is drawn on the same circumscribed radius so no kind
reads as 'bigger' than another - area is normalised, not the radius.
"""
import math

def _poly(cx, cy, r, n, rot_deg):
    pts = []
    for i in range(n):
        a = math.radians(rot_deg) + i * 2 * math.pi / n
        pts.append(f'{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}')
    return ' '.join(pts)

# Area-normalised radius: a regular n-gon of circumradius r has area
# (n/2) r^2 sin(2pi/n); scale each so all kinds read as the same visual weight.
def _norm(r, n):
    if n is None:                       # circle
        return r
    poly_area = (n / 2) * math.sin(2 * math.pi / n)
    return r * math.sqrt(math.pi / poly_area)

def shape_markup(kind, cx, cy, r, cls=''):
    """Return the SVG element for one node kind, centred on (cx, cy)."""
    c = f' class="{cls}"' if cls else ''
    if kind == 'definition':                       # circle
        return f'<circle{c} cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
    if kind == 'lemma':                            # square
        rr = _norm(r, 4)
        return f'<polygon{c} points="{_poly(cx, cy, rr, 4, 45)}"/>'
    if kind == 'proposition':                      # triangle, point up
        rr = _norm(r, 3)
        return f'<polygon{c} points="{_poly(cx, cy, rr, 3, -90)}"/>'
    if kind == 'theorem':                          # diamond
        rr = _norm(r, 4)
        return f'<polygon{c} points="{_poly(cx, cy, rr, 4, -90)}"/>'
    if kind in ('external_contract', 'standard_foundation'):   # hexagon
        rr = _norm(r, 6)
        return f'<polygon{c} points="{_poly(cx, cy, rr, 6, -90)}"/>'
    return f'<circle{c} cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'

if __name__ == '__main__':
    import json, collections
    d = json.load(open('/Users/Yingjian/Documents/GitHub/AgtXIv/schema v0.2/host_probe/evidence/closure.json'))
    kinds = collections.Counter(n['kind'] for n in d['nodes'])
    print('kind coverage:')
    for k, v in kinds.most_common():
        m = shape_markup(k, 50, 50, 12)
        print(f'  {v:>3}  {k:<22} -> {m.split()[0][1:]}')
    # every kind must map to a real shape, not silently fall through
    unmapped = [k for k in kinds if k not in
                ('definition','lemma','proposition','theorem','external_contract','standard_foundation')]
    print('unmapped kinds:', unmapped or 'none')
    # area check
    print()
    print('area normalisation (should all be ~equal):')
    for k in ('definition','lemma','proposition','theorem','external_contract'):
        n = {'definition':None,'lemma':4,'proposition':3,'theorem':4,'external_contract':6}[k]
        rr = _norm(12, n)
        area = math.pi*12**2 if n is None else (n/2)*rr**2*math.sin(2*math.pi/n)
        print(f'  {k:<22} r={rr:5.1f}  area={area:7.1f}')
