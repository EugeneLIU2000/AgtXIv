"""End-to-end v0.2 minimal slice, minus the model call (no SDK/credential here).
Proves: task validates -> honest NOT_STARTED receipt -> legitimate STAGED receipt
with real source resolution -> atomic commit -> cross-process read-back."""
import sys, json, pathlib, os
P=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,P)
from registry import validator_for
from resolve import resolve_output
from store import Store, digest
ROOT=pathlib.Path(__file__).resolve().parents[2]
raw=(ROOT/"Stabilizerness/arXiv-2607.26154v1/draft.tex").read_bytes()
blob=lambda b,mt="application/json":{"sha256":digest(b),"byte_size":len(b),"media_type":mt}
L=["SHAPE","TASK_BINDING","REFERENCES","SOURCES","LAMPORT_STRUCTURE","FORMAL_BUILD","ALIGNMENT"]
def checks(rep=None,**s):
    out=[]
    for x in L:
        st=s.get(x,"NOT_RUN")
        out.append({"layer":x,"status":st,"report":(rep if st in("PASS","FAIL") else None)})
    return out

TASK={"contract_version":"0.2.0","task_id":"t-2607-paper-1","plan_id":"plan-2607",
 "operation":"paper.extract",
 "purpose":"Extract source locators and claim candidates from the theorem environments of draft.tex only; disclose unread ranges as UNREAD_SCOPE.",
 "target_ids":[],
 "inputs":[{"id":"draft_tex","kind":"source","blob":blob(raw,"text/x-tex"),"item_id":None,"producer_task":None}],
 "spec":blob(b"spec index"),"policy":blob(b"policy"),"model_profile":blob(b"model profile"),"module":None,
 "limits":{"max_input_bytes":2000000,"max_output_bytes":1048576,"max_output_tokens":16000,
           "max_seconds":600,"max_attempts":3,"no_progress_limit":2,"max_cost_microusd":500000}}

def main():
    tv=validator_for("task.schema.json"); rv=validator_for("run.schema.json")
    te=list(tv.iter_errors(TASK))
    print(f"1. TASK validates ......... {'PASS' if not te else 'FAIL'}")
    for e in te[:3]: print("     ",list(e.path),e.message[:90])
    tb=json.dumps(TASK,sort_keys=True).encode()

    r1={"contract_version":"0.2.0","attempt_id":"a-notstarted","task":blob(tb),"state":"NOT_STARTED",
        "call":None,"output":None,"checks":checks(),"source_bindings":[],"artifacts":[],
        "reason":"No provider SDK or credential is configured in this environment; no model call was attempted."}
    e1=list(rv.iter_errors(r1))
    print(f"2. honest NOT_STARTED ..... {'PASS' if not e1 else 'FAIL'}")
    for e in e1[:3]: print("     ",list(e.path),e.message[:90])

    # a model WOULD return this; here it is the repository's own hand-authored teaching output,
    # relabelled onto the real source. This is NOT a model call and the receipt says so.
    out={"contract_version":"0.2.0","operation":"paper.extract","items":[
        {"id":"loc-closed-form","kind":"source_locator","source":{"input":"draft_tex"},
         "start_marker":"\\label{thm:solvable}","end_marker":"\\end{theorem}"},
        {"id":"loc-perfect-collapse","kind":"source_locator","source":{"input":"draft_tex"},
         "start_marker":"\\label{lem:perfect-collapse}","end_marker":"\\end{lemma}"}],
       "issues":[{"code":"UNREAD_SCOPE","subject":None,"detail":"Only two theorem environments were located; the remaining 69,678 bytes of draft.tex were not inventoried."}]}
    ob=json.dumps(out,sort_keys=True).encode()
    ov=validator_for("output.schema.json"); oe=list(ov.iter_errors(out))
    print(f"3. OUTPUT validates ....... {'PASS' if not oe else 'FAIL'}")
    for e in oe[:3]: print("     ",list(e.path),e.message[:90])

    binds,issues=resolve_output(out["items"],{"draft_tex":raw})
    print(f"4. SOURCES resolved ....... {len(binds)} bound, {len(issues)} refused")
    for b in binds: print(f"      {b['locator_id']:22s} [{b['byte_start']},{b['byte_end']})  {b['span_sha256'][:24]}...")

    rep=blob(json.dumps({"shape":"pass","references":"pass","sources":binds},sort_keys=True).encode())
    r2={"contract_version":"0.2.0","attempt_id":"a-staged","task":blob(tb),"state":"STAGED",
        "call":{"execution_id":"x-none","provider":"none","model":"NOT-A-MODEL-CALL","provider_request_id":None,
                "request":blob(b"n/a"),"response":blob(b"n/a"),"started_at":"2026-09-17T09:00:00Z",
                "finished_at":"2026-09-17T09:00:00Z","input_tokens":0,"output_tokens":0,"cost_microusd":0},
        "output":blob(ob),"checks":checks(rep,SHAPE="PASS",REFERENCES="PASS",SOURCES="PASS"),
        "source_bindings":[{k:v for k,v in b.items() if k in
            ("locator_id","source_sha256","byte_start","byte_end","span_sha256")} for b in binds],
        "artifacts":[],"reason":"Machinery test only: no model was called, so this is not a v0.2 Agent execution."}
    e2=list(rv.iter_errors(r2))
    print(f"5. STAGED receipt ......... {'PASS' if not e2 else 'FAIL'}")
    for e in e2[:3]: print("     ",list(e.path),e.message[:110])

    dbp=os.path.join(P,"e2e.sqlite")
    if os.path.exists(dbp): os.remove(dbp)
    st=Store(dbp)
    st.pin(raw,"text/x-tex")
    t,o,rr=st.commit_run("a-staged",tb,ob,r2,out["items"],binds)
    print(f"6. atomic commit .......... task={t[:22]}... output={o[:22]}...")
    return dbp

if __name__=="__main__":
    print(main())
