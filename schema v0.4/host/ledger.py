"""Corpus work-item ledger (§7.4): SQLite tables, not JSON contracts.

One coordinator is the single writer: it holds an exclusive lock for the connection's lifetime, and workers
write only immutable artifacts. A reservation is made before every dispatch and stays spent: an expired lease
turns the item ABANDONED, and settling with no observed cost keeps the reserved amount. A model item reserves a
positive amount against the manifest's budget_ceiling on its provider window; a host item names no window. A
receipt error is either a provider failure (QUOTA_WAIT) or classified by the caller (FAILED). A provider quota failure
closes the provider window for every item; after it reopens, a QUOTA_WAIT item may get one new attempt on the
same window (a new reservation and receipt, never a replay), counted against max_attempts_per_item. A response the host
checks refused (failure RESPONSE_REJECTED) returns the item to READY while attempts remain, else FAILED. Those are the
only automatic re-dispatches. Besides the graph stages, the ledger schedules AUTO_EVAL_V1 judge calls (stage EVAL,
subject JUDGE_CARD, method MODEL_JUDGE) and DISCOVERY searches (stage S1, subject DISCOVERY_QUERY, method MODEL_SEARCH),
which produce records, not graph rows.
"""
from __future__ import annotations

import contextlib
import sqlite3
import time

import contracts
from core import canonical, digest
from corpus import check_corpus_manifest
from model_failures import GLOBAL_PROVIDER_FAILURES

_DEFS = contracts.SCHEMAS[contracts.CORPUS_ID]["$defs"]
STAGES = (*_DEFS["GraphDelta"]["properties"]["stage"]["enum"], "EVAL")
SUBJECT_KINDS = (*_DEFS["GraphDelta"]["properties"]["subject"]["properties"]["kind"]["enum"], "JUDGE_CARD", "DISCOVERY_QUERY")
METHODS = (*_DEFS["Method"]["enum"], "MODEL_JUDGE", "MODEL_SEARCH")
STATES = ("READY", "RUNNING", "DONE", "FAILED", "QUOTA_WAIT", "ABANDONED", "SKIPPED")
FAILURES = ("SOURCE_UNREACHABLE", "SOURCE_READ_DEFECTIVE", "HOST_PROCESSING_FAILED", "WORKER_INTERRUPTED",  # v0.3
            "RESPONSE_REJECTED")  # v0.4: the host checks refused the model response; the item may be tried again
MODEL_METHODS = ("MODEL_EXTRACTION", "MODEL_MATCH", "MODEL_JUDGE", "MODEL_SEARCH")
KEY_FIELDS = ("stage", "subject_kind", "subject_id", "method", "method_version", "input_digest")
SCHEMA = f"""
CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id = 1), spec TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS items(key TEXT PRIMARY KEY, {", ".join(f + " TEXT NOT NULL" for f in KEY_FIELDS)},
  state TEXT NOT NULL CHECK(state IN {STATES}), detail TEXT, requeued INTEGER NOT NULL DEFAULT 0,
  UNIQUE({", ".join(KEY_FIELDS)}));
CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY, item_key TEXT NOT NULL REFERENCES items(key),
  attempt INTEGER NOT NULL, provider TEXT, account_ref TEXT, amount REAL NOT NULL, cost REAL,
  reserved_at REAL NOT NULL, lease_until REAL NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('RESERVED', 'SETTLED', 'ABANDONED')), receipt TEXT, UNIQUE(item_key, attempt));
CREATE UNIQUE INDEX IF NOT EXISTS one_live_reservation_per_item ON reservations(item_key) WHERE state = 'RESERVED';
CREATE TABLE IF NOT EXISTS windows(provider TEXT NOT NULL, account_ref TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('OPEN', 'CLOSED_UNTIL', 'CLOSED_UNKNOWN')), until REAL,
  PRIMARY KEY(provider, account_ref));
"""


class CorpusLedger:
    def __init__(self, path, manifest, *, max_attempts_per_item, lease_seconds):
        check_corpus_manifest(manifest)
        if type(max_attempts_per_item) is not int or max_attempts_per_item < 1 or not lease_seconds > 0:
            raise ValueError("LEDGER_LIMITS_INVALID")
        self.db = sqlite3.connect(path, timeout=0, isolation_level=None)
        try:
            self.db.execute("PRAGMA locking_mode=EXCLUSIVE")
            self.db.execute("BEGIN EXCLUSIVE")
            self.db.execute("COMMIT")
        except sqlite3.OperationalError as error:
            self.db.close()
            raise RuntimeError("LEDGER_HAS_ANOTHER_WRITER") from error
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(SCHEMA)
        self.config = {"corpus_id": manifest["corpus_id"], "budget_ceiling": manifest["budget_ceiling"],
                       "max_attempts_per_item": max_attempts_per_item, "lease_seconds": lease_seconds}
        spec = canonical(self.config).decode()
        with self._tx() as db:
            db.execute("INSERT OR IGNORE INTO config VALUES (1, ?)", (spec,))
            frozen = db.execute("SELECT spec FROM config").fetchone()[0]
        if frozen != spec:
            self.db.close()  # release the writer lock at once
            raise ValueError("LEDGER_CONFIG_FROZEN")

    def close(self):
        self.db.close()

    @contextlib.contextmanager
    def _tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        self.db.execute("COMMIT")

    def add(self, stage, subject_kind, subject_id, method, method_version, input_digest):
        """Register a work item (idempotent); returns its key, the digest of the six key fields."""
        if (stage not in STAGES or subject_kind not in SUBJECT_KINDS or method not in METHODS
                or not all(isinstance(x, str) and x for x in (subject_id, method_version))
                or not contracts.validator("Sha256").is_valid(input_digest)):
            raise ValueError("WORK_ITEM_KEY_INVALID")
        fields = (stage, subject_kind, subject_id, method, method_version, input_digest)
        key = digest(canonical(dict(zip(KEY_FIELDS, fields))))
        with self._tx() as db:
            db.execute("INSERT OR IGNORE INTO items(key, state, " + ", ".join(KEY_FIELDS) + ") VALUES (?, 'READY', ?, ?, ?, ?, ?, ?)",
                       (key, *fields))
        return key

    def item(self, key):
        row = self.db.execute("SELECT method, state, detail, requeued, (SELECT COUNT(*) FROM reservations "
                              "WHERE item_key = key) FROM items WHERE key = ?", (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        dispatchable = (row[1] == "READY" or row[1] == "QUOTA_WAIT" and not row[3]) and row[4] < self.config["max_attempts_per_item"]
        return {"key": key, "method": row[0], "state": row[1], "detail": row[2], "requeued": bool(row[3]), "attempts": row[4],
                "dispatchable": dispatchable}

    def items(self, state):
        return [row[0] for row in self.db.execute("SELECT key FROM items WHERE state = ? ORDER BY key", (state,))]

    def spent(self):
        return self.db.execute("SELECT COALESCE(SUM(COALESCE(cost, amount)), 0) FROM reservations").fetchone()[0]

    def skip(self, key, reason):
        with self._tx() as db:
            if db.execute("UPDATE items SET state = 'SKIPPED', detail = ? WHERE key = ? AND state = 'READY'",
                          (reason, key)).rowcount != 1:
                raise ValueError("ONLY_A_READY_ITEM_CAN_BE_SKIPPED")

    def window(self, provider, account_ref, now=None):
        """Effective window state; CLOSED_UNTIL(t) reads OPEN from t on, CLOSED_UNKNOWN only after open_window."""
        now = time.time() if now is None else now
        row = self.db.execute("SELECT state, until FROM windows WHERE provider = ? AND account_ref = ?",
                              (provider, account_ref)).fetchone()
        return "OPEN" if row is None or row[0] == "CLOSED_UNTIL" and row[1] <= now else row[0]

    def open_window(self, provider, account_ref):
        with self._tx() as db:
            db.execute("INSERT OR REPLACE INTO windows VALUES (?, ?, 'OPEN', NULL)", (provider, account_ref))

    def expire_leases(self, now=None):
        """RUNNING items whose lease ended become ABANDONED; their reservations stay spent. Returns their keys."""
        now = time.time() if now is None else now
        with self._tx() as db:
            keys = [row[0] for row in db.execute(
                "SELECT item_key FROM reservations WHERE state = 'RESERVED' AND lease_until <= ? ORDER BY item_key", (now,))]
            db.execute("UPDATE reservations SET state = 'ABANDONED' WHERE state = 'RESERVED' AND lease_until <= ?", (now,))
            db.executemany("UPDATE items SET state = 'ABANDONED', detail = 'LEASE_EXPIRED' WHERE key = ?", [(k,) for k in keys])
        return keys

    def reserve(self, key, now=None, *, provider=None, account_ref=None, amount=0):
        """Reserve one attempt before dispatch. Model items name their provider window and an amount > 0; host items
        name no window."""
        now = time.time() if now is None else now
        self.expire_leases(now)
        with self._tx() as db:
            item = self.item(key)
            model = item["method"] in MODEL_METHODS
            if (model != (provider is not None) or model != (account_ref is not None)
                    or not (amount > 0 if model else amount >= 0)):
                raise ValueError("RESERVATION_ARGUMENTS_INVALID")
            if item["state"] == "QUOTA_WAIT":
                last = db.execute("SELECT provider, account_ref FROM reservations WHERE item_key = ? ORDER BY attempt DESC",
                                  (key,)).fetchone()
                if item["requeued"] or last != (provider, account_ref):
                    raise RuntimeError("QUOTA_REATTEMPT_USED_OR_ON_ANOTHER_WINDOW")
            elif item["state"] != "READY":
                raise RuntimeError("ITEM_NOT_DISPATCHABLE: " + item["state"])
            if item["attempts"] >= self.config["max_attempts_per_item"]:
                raise RuntimeError("MAX_ATTEMPTS_PER_ITEM_EXHAUSTED")
            if provider is not None and self.window(provider, account_ref, now) != "OPEN":
                raise RuntimeError("PROVIDER_WINDOW_CLOSED")
            if self.spent() + amount > self.config["budget_ceiling"]["value"]:
                raise RuntimeError("BUDGET_CEILING_REACHED")
            reservation = {"id": digest(canonical([key, item["attempts"] + 1])), "item_key": key,
                           "attempt": item["attempts"] + 1, "provider": provider, "account_ref": account_ref,
                           "amount": amount, "lease_until": now + self.config["lease_seconds"]}
            db.execute("INSERT INTO reservations VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, 'RESERVED', NULL)",
                       (reservation["id"], key, reservation["attempt"], provider, account_ref, amount, now,
                        reservation["lease_until"]))
            db.execute("UPDATE items SET state = 'RUNNING', requeued = ? WHERE key = ?",
                       (item["requeued"] or item["state"] == "QUOTA_WAIT", key))
        return reservation

    def settle(self, reservation_id, receipt, now=None, *, failure=None, cost=None, closed_until=None):
        """Record the receipt of a live reservation; returns the item's new state (DONE, FAILED, READY or QUOTA_WAIT)."""
        self.expire_leases(now)
        with self._tx() as db:
            row = db.execute("SELECT item_key, provider, account_ref, state FROM reservations WHERE id = ?",
                             (reservation_id,)).fetchone()
            if row is None or row[3] != "RESERVED":
                raise ValueError("RESERVATION_NOT_LIVE")
            if not isinstance(receipt, dict) or receipt.get("reservation_id") != reservation_id:
                raise ValueError("RECEIPT_DOES_NOT_BIND_RESERVATION")
            error = receipt.get("error")
            quota = error in GLOBAL_PROVIDER_FAILURES
            if (quota and (row[1] is None or failure is not None)) or (failure is not None and failure not in FAILURES) \
                    or (failure == "RESPONSE_REJECTED" and row[1] is None) \
                    or (error is not None and not quota and failure is None) or (cost is not None and not cost >= 0):
                raise ValueError("SETTLEMENT_CLASSIFICATION_INVALID")
            attempts = db.execute("SELECT COUNT(*) FROM reservations WHERE item_key = ?", (row[0],)).fetchone()[0]
            retry = failure == "RESPONSE_REJECTED" and attempts < self.config["max_attempts_per_item"]
            state = "QUOTA_WAIT" if quota else "READY" if retry else "FAILED" if failure else "DONE"
            db.execute("UPDATE reservations SET state = 'SETTLED', cost = ?, receipt = ? WHERE id = ?",
                       (cost, canonical(receipt).decode(), reservation_id))
            db.execute("UPDATE items SET state = ?, detail = ? WHERE key = ?",
                       (state, error if quota else failure, row[0]))
            if quota:
                db.execute("INSERT OR REPLACE INTO windows VALUES (?, ?, ?, ?)", (
                    row[1], row[2], "CLOSED_UNKNOWN" if closed_until is None else "CLOSED_UNTIL", closed_until))
        return state
