"""Phase gate: mechanical checks that must pass before a stage may be treated as done.

Adapted from Paper2Agent's verify_workflow.py, which the coordinator must run at every handoff
and which "checks records and hashes" while the coordinator still reviews the substantive
scientific result. Same boundary here: this program decides nothing scientific. It answers one
question - is the ledger internally sound up to the phase you asked about - and refuses to say
yes when it is not.

The distinction matters because seven per-run check layers do not compose into a chain. A run can
be individually well formed and still stand on a predecessor that never committed.

Usage:
    verify_phase.py --store PATH --through {setup|extract|dependency|lamport|lean|complete}
"""
import argparse, hashlib, json, pathlib, sqlite3, sys

PHASES = ["setup", "extract", "dependency", "lamport", "lean", "complete"]
OP = {"extract": "paper.extract", "dependency": "dependency.search",
      "lamport": "autoformalization.lamport", "lean": "autoformalization.lean"}

def digest(b): return "sha256:" + hashlib.sha256(b).hexdigest()

def gate(store_path, through):
    if through not in PHASES:
        raise SystemExit(f"unknown phase {through!r}; expected one of {PHASES}")
    db = sqlite3.connect(f"file:{store_path}?mode=ro", uri=True)
    fail, note = [], []

    # --- blob integrity. "Never refresh hashes alone to make stale evidence current." ---
    n_blob = 0
    for sha, body in db.execute("SELECT sha256, body FROM blob"):
        n_blob += 1
        if digest(body) != sha:
            fail.append(("BLOB_HASH_MISMATCH", f"{sha[:26]}… does not hash to its own key"))
    note.append(f"{n_blob} blobs, bytes re-hashed")

    # --- every run's referenced blobs must exist ---
    runs = db.execute("SELECT attempt_id, task_sha256, state, principal, operation,"
                      " output_sha256, receipt_sha256 FROM run").fetchall()
    have = {r[0] for r in db.execute("SELECT sha256 FROM blob")}
    for aid, t, state, principal, op, o, rec in runs:
        for label, h in (("task", t), ("receipt", rec), ("output", o)):
            if h and h not in have:
                fail.append(("MISSING_BLOB", f"{aid}: {label} blob {h[:26]}… is not stored"))
        if state != "NOT_STARTED" and not principal:
            fail.append(("NO_PRINCIPAL", f"{aid}: state {state} with no attributed principal"))
    note.append(f"{len(runs)} runs, {sum(1 for r in runs if r[2]=='COMMITTED')} COMMITTED")

    # --- item index must resolve ---
    n_item = 0
    for pt, o, iid, kind, aid in db.execute(
            "SELECT producer_task_sha256, output_sha256, item_id, kind, attempt_id FROM item"):
        n_item += 1
        if pt not in have or o not in have:
            fail.append(("ITEM_UNRESOLVED", f"{iid}: producer_task or output blob missing"))
    note.append(f"{n_item} indexed items")

    # --- consumes must land on COMMITTED runs, per CONTRACT section 3 ---
    n_con = 0
    try:
        rows = db.execute("SELECT attempt_id, input, producer_task, output, item_id,"
                          " producer_principal FROM consumes").fetchall()
    except sqlite3.OperationalError:
        rows = []
        note.append("no consumes table: store predates lineage recording")
    for aid, inp, pt, o, iid, pprin in rows:
        n_con += 1
        row = db.execute("SELECT r.state, r.principal, r.attempt_id FROM item i"
                         " JOIN run r ON r.attempt_id=i.attempt_id"
                         " WHERE i.producer_task_sha256=? AND i.output_sha256=? AND i.item_id=?",
                         (pt, o, iid)).fetchone()
        if row is None:
            fail.append(("DANGLING_CONSUME", f"{aid}/{inp}: cites an item nothing produced"))
        elif row[0] != "COMMITTED":
            fail.append(("CONSUMED_UNCOMMITTED", f"{aid}/{inp}: producer is {row[0]}"))
        elif row[1] != pprin:
            fail.append(("PRINCIPAL_MISMATCH", f"{aid}/{inp}: ledger says {row[1]!r}"))
        elif row[2] == aid:
            fail.append(("SELF_CONSUME", f"{aid}/{inp}: cites itself"))
    if rows: note.append(f"{n_con} consumed items traced to their producing run")

    # --- the phase chain itself: each requested phase needs a COMMITTED run ---
    committed = {op for _, _, st, _, op, _, _ in runs if st == "COMMITTED" and op}
    reached = []
    for ph in PHASES[1:PHASES.index(through) + 1]:
        if ph == "complete":
            continue
        if OP[ph] in committed:
            reached.append(ph)
        else:
            fail.append(("PHASE_NOT_REACHED",
                         f"{ph}: no COMMITTED run for {OP[ph]}"))
    return fail, note, reached

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--through", required=True)
    a = ap.parse_args()
    if not pathlib.Path(a.store).exists():
        print(f"no store at {a.store}"); sys.exit(2)
    fail, note, reached = gate(a.store, a.through)
    print(f"store    {a.store}")
    print(f"through  {a.through}")
    for n in note: print(f"  · {n}")
    print(f"  · phases with a COMMITTED run: {reached or 'none'}")
    print()
    if not fail:
        print("GATE PASSED — the ledger is internally sound to this phase.")
        print("This says nothing about whether any claim is correct, reviewed, or admitted.")
        sys.exit(0)
    print(f"GATE FAILED — {len(fail)} problem(s):")
    for code, detail in fail: print(f"  [{code}] {detail}")
    sys.exit(1)

if __name__ == "__main__":
    main()
