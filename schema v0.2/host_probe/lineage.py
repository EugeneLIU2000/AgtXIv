"""Lineage checks the JSON Schemas cannot perform.

Two requirements v0.2 states and nothing previously enforced:

  CONTRACT section 3 - "The next Task pins identity with producer_task, the output blob, and
  item_id, and verifies a real COMMITTED run binding that Task/output pair."

  HOST section 4 - "Lean's lamport must reference a previously committed lamport_proof with the
  same target version. A string authored in the current call is not a pinned intermediate layer."

Both are about lineage: does the thing this attempt says it read actually exist, in a run that
actually committed, produced by someone other than this attempt. Independence is one consequence
of that, not the whole of it - v0.2 has no review operation yet, so nothing here is a claim that
producer-versus-reviewer separation is solved. What it does establish is that the ledger can
answer the question when a review operation arrives.

Principals come from the host's own execution facts. Paper2Agent puts the point sharply:
"Do not substitute a changed role prompt in the same agent context for independent verification."
A principal the model reports about itself is not a principal.
"""
import sqlite3

LAMPORT_CONSUMER = "autoformalization.lean"

def check(db_path, attempt_id, task, receipt):
    """Returns a list of (code, detail). Empty means the lineage is sound."""
    errs = []
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    call = receipt.get("call") or {}
    principal = call.get("principal")
    state = receipt["state"]
    consumes = receipt.get("consumes") or []

    if state == "NOT_STARTED":
        if consumes: errs.append(("NOT_STARTED_CONSUMES",
            "a run that never called a model cannot have read committed items"))
        return errs

    # 1. the host-attributed principal must not be one the Task excluded
    excluded = set(task.get("excluded_principals") or [])
    if principal is None:
        errs.append(("NO_PRINCIPAL", "the host attributed no principal to this execution"))
    elif principal in excluded:
        errs.append(("EXCLUDED_PRINCIPAL",
            f"principal {principal!r} is in this task's excluded_principals"))

    # 2. every consumed item must resolve to a real COMMITTED run, and the producing
    #    principal must be the one the LEDGER records, not the one the receipt asserts
    for c in consumes:
        row = db.execute(
            "SELECT r.state, r.principal, r.attempt_id FROM item i JOIN run r"
            "  ON r.attempt_id = i.attempt_id"
            " WHERE i.producer_task_sha256=? AND i.output_sha256=? AND i.item_id=?",
            (c["producer_task"], c["output"], c["item_id"])).fetchone()
        if row is None:
            errs.append(("DANGLING_CONSUME",
                f"{c['input']}: no indexed item for that producer_task/output/item_id"))
            continue
        pstate, pprincipal, pattempt = row
        if pstate != "COMMITTED":
            errs.append(("CONSUMED_UNCOMMITTED",
                f"{c['input']}: producing run {pattempt} is {pstate}, not COMMITTED"))
        if pprincipal != c["producer_principal"]:
            errs.append(("PRINCIPAL_MISMATCH",
                f"{c['input']}: receipt says the producer was {c['producer_principal']!r}, "
                f"the ledger says {pprincipal!r}"))
        if pattempt == attempt_id:
            errs.append(("SELF_CONSUME",
                f"{c['input']}: this attempt cites itself as the producer"))

    # 3. the Lean stage must stand on a previously committed Lamport artifact
    if task.get("operation") == LAMPORT_CONSUMER:
        lam = [c for c in consumes if c["item_id"].startswith("lamport")
               or _kind(db, c) == "lamport_proof"]
        if not lam:
            errs.append(("NO_COMMITTED_LAMPORT",
                "autoformalization.lean consumed no committed lamport_proof; a string authored "
                "in this call is not a pinned intermediate layer"))
    return errs

def _kind(db, c):
    row = db.execute("SELECT kind FROM item WHERE producer_task_sha256=? AND output_sha256=?"
                     " AND item_id=?", (c["producer_task"], c["output"], c["item_id"])).fetchone()
    return row[0] if row else None
