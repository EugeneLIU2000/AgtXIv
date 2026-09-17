"""Minimal v0.2 content store + execution ledger.  STORAGE.md sections 1-2, 5.
Blobs are immutable, addressed by sha256 of ORIGINAL bytes.  One SQL transaction
pins the run, item index and input dependencies."""
import hashlib, json, pathlib, sqlite3, contextlib

DDL = """
CREATE TABLE IF NOT EXISTS blob(
  sha256 TEXT PRIMARY KEY, length INTEGER NOT NULL,
  media_type TEXT NOT NULL, body BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS run(
  attempt_id TEXT PRIMARY KEY, task_sha256 TEXT NOT NULL, state TEXT NOT NULL,
  principal TEXT, operation TEXT,
  output_sha256 TEXT, receipt_sha256 TEXT NOT NULL,
  FOREIGN KEY(task_sha256) REFERENCES blob(sha256));
CREATE TABLE IF NOT EXISTS consumes(
  attempt_id TEXT NOT NULL, input TEXT NOT NULL,
  producer_task TEXT NOT NULL, output TEXT NOT NULL, item_id TEXT NOT NULL,
  producer_principal TEXT NOT NULL,
  PRIMARY KEY(attempt_id, input));
CREATE TABLE IF NOT EXISTS item(
  producer_task_sha256 TEXT NOT NULL, output_sha256 TEXT NOT NULL, item_id TEXT NOT NULL,
  kind TEXT NOT NULL, attempt_id TEXT NOT NULL,
  PRIMARY KEY(producer_task_sha256, output_sha256, item_id));
CREATE TABLE IF NOT EXISTS source_binding(
  attempt_id TEXT NOT NULL, locator_id TEXT NOT NULL, source_sha256 TEXT NOT NULL,
  byte_start INTEGER NOT NULL, byte_end INTEGER NOT NULL, span_sha256 TEXT NOT NULL,
  PRIMARY KEY(attempt_id, locator_id));
CREATE TABLE IF NOT EXISTS event(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id TEXT NOT NULL, state TEXT NOT NULL);
"""

def digest(b: bytes) -> str: return "sha256:" + hashlib.sha256(b).hexdigest()

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(DDL); self.db.commit()

    @contextlib.contextmanager
    def tx(self):
        try:
            self.db.execute("BEGIN IMMEDIATE"); yield self.db; self.db.commit()
        except Exception:
            self.db.rollback(); raise

    def pin(self, body: bytes, media_type: str) -> str:
        """Immutable blob.  Same bytes -> same id.  Different bytes, same id -> refuse."""
        h = digest(body)
        row = self.db.execute("SELECT body FROM blob WHERE sha256=?", (h,)).fetchone()
        if row is not None:
            if row[0] != body: raise RuntimeError("hash collision with different bytes")
            return h
        self.db.execute("INSERT INTO blob VALUES(?,?,?,?)", (h, len(body), media_type, body))
        self.db.commit()
        return h

    def commit_run(self, attempt_id, task_bytes, output_bytes, receipt, items, bindings,
                   operation=None):
        """STORAGE section 5: pin blobs first, then ONE transaction for run+index."""
        t = self.pin(task_bytes, "application/json")
        o = self.pin(output_bytes, "application/json")
        r = self.pin(json.dumps(receipt, sort_keys=True).encode(), "application/json")
        principal = ((receipt.get("call") or {}) or {}).get("principal")
        with self.tx() as db:
            db.execute("INSERT INTO run VALUES(?,?,?,?,?,?,?)",
                       (attempt_id, t, receipt["state"], principal, operation, o, r))
            for c in receipt.get("consumes", []) or []:
                db.execute("INSERT INTO consumes VALUES(?,?,?,?,?,?)",
                           (attempt_id, c["input"], c["producer_task"], c["output"],
                            c["item_id"], c["producer_principal"]))
            for it in items:
                db.execute("INSERT INTO item VALUES(?,?,?,?,?)",
                           (t, o, it["id"], it["kind"], attempt_id))
            for b in bindings:
                db.execute("INSERT INTO source_binding VALUES(?,?,?,?,?,?)",
                           (attempt_id, b["locator_id"], b["source_sha256"],
                            b["byte_start"], b["byte_end"], b["span_sha256"]))
            db.execute("INSERT INTO event(attempt_id,state) VALUES(?,?)", (attempt_id, receipt["state"]))
        return t, o, r

    def read_back(self, attempt_id):
        r = self.db.execute("SELECT task_sha256,state,output_sha256,principal FROM run WHERE attempt_id=?", (attempt_id,)).fetchone()
        if not r: return None
        t, state, o, principal = r
        out = json.loads(self.db.execute("SELECT body FROM blob WHERE sha256=?", (o,)).fetchone()[0])
        items = self.db.execute("SELECT item_id,kind FROM item WHERE producer_task_sha256=? AND output_sha256=?", (t,o)).fetchall()
        binds = self.db.execute("SELECT locator_id,byte_start,byte_end,span_sha256 FROM source_binding WHERE attempt_id=?", (attempt_id,)).fetchall()
        return {"state":state, "principal":principal, "task_sha256":t, "output_sha256":o,
                "items":items, "bindings":binds, "output_verifies": len(out["items"])==len(items)}
