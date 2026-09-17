import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from resolve import resolve, LocatorError
REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "Stabilizerness/arXiv-2607.26154v1/draft.tex"
raw = SRC.read_bytes()
print(f"REAL SOURCE: draft.tex  {len(raw)} bytes\n")
# positive: a real theorem statement from the paper
cases_ok = [
  ("\\begin{theorem}", "\\end{theorem}"),
]
# find a genuinely unique pair by scanning for a distinctive phrase
import re
txt = raw.decode('utf-8', 'replace')
for probe in ["perfect", "frustration graph", "maximum-weight independent"]:
    n = txt.count(probe)
    print(f"  occurrences of {probe!r}: {n}")
print()
NEG = [
  ("__no_such_marker__", "x", "START_NOT_FOUND"),
  ("\\begin{equation}", "\\end{equation}", "START_AMBIGUOUS"),
  ("", "x", "EMPTY_MARKER"),
]
print("NEGATIVE CASES (must refuse, never guess):")
ok=0
for s,e,expect in NEG:
    try:
        resolve(raw, s, e); print(f"  MISSED!  {expect}")
    except LocatorError as ex:
        hit = ex.code==expect
        ok += hit
        print(f"  {'CAUGHT ' if hit else 'WRONG  '} expected={expect:18s} got={ex.code}")
print(f"\n{ok}/{len(NEG)} refusal cases correct")
