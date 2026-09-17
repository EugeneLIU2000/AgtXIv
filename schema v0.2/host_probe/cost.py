"""Per-paper cost model for the talk's cost slide.

Two scopes, kept apart because v0.2's Lamport/Lean branch runs on ONE selected MathClaim by
design: there is no whole-paper autoformalization operation. Conflating them moves the answer by
a factor of four.

Everything measured is measured; everything estimated says so. The two estimates are the
token approximation (four characters per token, pending the provider's counting endpoint) and
the per-operation call counts, which come from docs/IDEAS-BACKLOG.md item 5 and are the thing to
replace with receipts after the first real runs.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import spec_index

REPO = pathlib.Path(__file__).resolve().parents[2]
CLAIMS_FILE = REPO / "Stabilizerness/MathClaimIRRegistry/claims/graph-theoretic-nonstabilizerness.jsonl"

# Rate card is looked up, never remembered. Override on the command line before the talk.
RATES = {"input_per_mtok": 5.00, "output_per_mtok": 25.00,
         "source": "Anthropic Claude Opus 5 rate card, as cached 2026-06-24 - RE-CHECK ON THE DAY"}

# calls, extra input tokens beyond the spec prefix, output tokens. Estimates.
PLAN = {
    "paper.extract":             ("chunks",      10, 3000, 2000, "low / medium"),
    "dependency.search":         ("per claim x2", 2, 3000, 2000, "medium"),
    "autoformalization.lamport": ("per target x2", 2, 2000, 5000, "high"),
    "autoformalization.lean":    ("per target x4", 4, 6000, 4000, "xhigh / max"),
}

def measured_claims():
    if not CLAIMS_FILE.exists(): return None
    return sum(1 for l in CLAIMS_FILE.read_text().splitlines() if l.strip())

def scope(targets, claims):
    """targets: how many MathClaims reach the Lamport/Lean branch."""
    rows, ti, to, calls = [], 0, 0, 0
    _, spec_text = spec_index.collect("paper.extract")
    prefix = len(spec_text.encode()) / 4
    for op, (basis, per, extra, out, effort) in PLAN.items():
        n = per if basis == "chunks" else per * (claims if op == "dependency.search" else targets)
        i, o = n * (prefix + extra), n * out
        rows.append((op, basis, n, i, o, effort)); ti += i; to += o; calls += n
    return rows, ti, to, calls, prefix

def report(claims=None):
    claims = claims or measured_claims() or 25
    src = "measured from the MathClaimIR registry" if measured_claims() else "assumed"
    print(f"paper          arXiv:2607.26154v1")
    print(f"MathClaims     {claims}  ({src})")
    print(f"rates          ${RATES['input_per_mtok']}/${RATES['output_per_mtok']} per MTok")
    print(f"               {RATES['source']}\n")
    for label, targets in (("A  spec-internal: formalize ONE claim", 1),
                           ("B  extension: formalize ALL claims", claims)):
        rows, ti, to, calls, prefix = scope(targets, claims)
        print(f"### scope {label}")
        print(f"  {'operation':28s} {'calls':>6} {'input':>11} {'output':>9}  effort")
        for op, basis, n, i, o, effort in rows:
            print(f"  {op:28s} {n:>6} {i:>11,.0f} {o:>9,.0f}  {effort}")
        cost = ti/1e6*RATES["input_per_mtok"] + to/1e6*RATES["output_per_mtok"]
        rep = calls*prefix
        print(f"  {'TOTAL':28s} {calls:>6} {ti:>11,.0f} {to:>9,.0f}")
        print(f"  cost per paper                       ${cost:,.2f}")
        print(f"  repeated spec prefix                 {rep:,.0f} tok = {rep/ti*100:.0f}% of all input")
        print(f"  -> cacheable, no quality traded; the largest lever and it is free\n")
    print("Not yet reflected here, because no call has been made: actual token counts, actual")
    print("iteration counts, and cache-read tokens. autoformalization.lean's iteration count is")
    print("over half of scope B and is the first quantity to measure.")

if __name__ == "__main__":
    report(int(sys.argv[1]) if len(sys.argv) > 1 else None)
