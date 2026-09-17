"""Prove the lineage checks fire. A checker that only ever reports PASS establishes nothing."""
import copy, json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lineage
from store import Store, digest

P = pathlib.Path(__file__).resolve().parent
DB = P / "lineage_test.sqlite"
blob = lambda b, mt="application/json": {"sha256": digest(b), "byte_size": len(b), "media_type": mt}
L = ["SHAPE","TASK_BINDING","REFERENCES","SOURCES","LAMPORT_STRUCTURE","FORMAL_BUILD","ALIGNMENT"]
REP = blob(b'{"ok":true}')
def checks(**s): return [{"layer":x,"status":s.get(x,"NOT_RUN"),
                          "report":(REP if s.get(x) in ("PASS","FAIL") else None)} for x in L]
def call(principal):
    return {"execution_id":f"x-{principal}","principal":principal,"provider":"none",
            "model":"test","provider_request_id":None,"request":blob(b"q"),"response":blob(b"a"),
            "started_at":"2026-09-17T10:00:00Z","finished_at":"2026-09-17T10:00:05Z",
            "input_tokens":1,"output_tokens":1,"cost_microusd":0}
def task(op, excluded=()): return {"task_id":f"t-{op}","operation":op,
                                   "excluded_principals":list(excluded)}
def receipt(aid, principal, state="COMMITTED", consumes=(), **kw):
    r={"contract_version":"0.2.0","attempt_id":aid,"task":blob(b"t"),"state":state,
       "call":call(principal),"output":blob(b"o"),
       "checks":checks(SHAPE="PASS",TASK_BINDING="PASS",REFERENCES="PASS",SOURCES="PASS"),
       "source_bindings":[],"artifacts":[],"reason":None,"expansions":[],
       "consumes":list(consumes)}
    r.update(kw); return r

if DB.exists(): DB.unlink()
st = Store(str(DB))

# --- set the stage: principal A commits a lamport_proof ---
TB = json.dumps(task("autoformalization.lamport"), sort_keys=True).encode()
OB = json.dumps({"items":[{"id":"lam1","kind":"lamport_proof"}]}, sort_keys=True).encode()
rA = receipt("a-lamport", "agent-A")
tA, oA, _ = st.commit_run("a-lamport", TB, OB, rA,
                          [{"id":"lam1","kind":"lamport_proof"}], [],
                          operation="autoformalization.lamport")
# --- and a STAGED run, to be cited illegitimately later ---
SB = json.dumps({"items":[{"id":"lam9","kind":"lamport_proof"}]}, sort_keys=True).encode()
rS = receipt("a-staged", "agent-S", state="STAGED", reason="not committed")
tS, oS, _ = st.commit_run("a-staged", json.dumps(task("autoformalization.lamport"),sort_keys=True).encode()+b" ",
                          SB, rS, [{"id":"lam9","kind":"lamport_proof"}], [],
                          operation="autoformalization.lamport")

GOOD = {"input":"target_lamport","producer_task":tA,"output":oA,
        "item_id":"lam1","producer_principal":"agent-A"}

print("POSITIVE")
errs = lineage.check(str(DB), "a-lean", task("autoformalization.lean"),
                     receipt("a-lean","agent-B",consumes=[GOOD]))
print(f"  {'PASS   ' if not errs else 'FAIL   '} lean by agent-B standing on agent-A's committed lamport"
      + ("" if not errs else f"  {errs}"))

CASES = [
 ("lean consumed no lamport at all", "autoformalization.lean", "agent-B", [], {}, ()),
 ("lean cites itself as producer", "autoformalization.lean", "agent-B",
   [dict(GOOD, producer_task=tA, output=oA)], {}, ()),          # attempt_id set to a-lamport below
 ("consumed a STAGED run", "autoformalization.lean", "agent-B",
   [{"input":"target_lamport","producer_task":tS,"output":oS,"item_id":"lam9",
     "producer_principal":"agent-S"}], {}, ()),
 ("consumed item does not exist", "autoformalization.lean", "agent-B",
   [dict(GOOD, item_id="nope")], {}, ()),
 ("receipt lies about who produced it", "autoformalization.lean", "agent-B",
   [dict(GOOD, producer_principal="agent-B")], {}, ()),
 ("principal is excluded by the task", "autoformalization.lean", "agent-A",
   [GOOD], {}, ("agent-A",)),
 ("NOT_STARTED yet claims to have read items", "autoformalization.lean", "agent-B",
   [GOOD], {"state":"NOT_STARTED","call":None,"output":None,
            "checks":checks(),"reason":"no credential"}, ()),
 ("host attributed no principal", "autoformalization.lean", None, [GOOD], {}, ()),
]
print("\nNEGATIVE")
hit = 0
for name, op, principal, cons, kw, excl in CASES:
    aid = "a-lamport" if "itself" in name else "a-lean"
    r = receipt(aid, principal or "agent-B", consumes=cons, **kw)
    if principal is None: r["call"]["principal"] = None
    e = lineage.check(str(DB), aid, task(op, excl), r)
    hit += bool(e)
    code = e[0][0] if e else "-"
    print(f"  {'CAUGHT ' if e else 'MISSED!'} {name:44s} {code}")
print(f"\n{hit}/{len(CASES)} lineage failures rejected")
DB.unlink()
sys.exit(0 if hit == len(CASES) else 1)
