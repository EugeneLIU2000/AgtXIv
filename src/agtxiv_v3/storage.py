"""Bounded offline candidate persistence, not scientific admission.

Records are canonical JSON; artifacts retain exact raw bytes. Identity/revision
and artifact IDs cannot be overwritten, including by a differently hashed value.
Each ingest validates the entire resulting store with RecordSet (and therefore
shares its MAX_RECORDS limit). Caller-held authority is optional and never inferred
from stored producer fields. Validation reports are not durable authority grants.

Candidate heads are local CAS pointers to contract-valid knowledge snapshots, NOT
an authoritative knowledge index. No admission decisions, ingestion receipts,
query receipts, reviews or provenance labels are manufactured here. Read-only
queries are always PROVISIONAL, even when records contain positive decisions.
SQLite transactions coordinate separate connections; use one connection per
thread. The local filesystem and integrating Python caller are trusted; this is
not protection against an administrator replacing the database or its triggers.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterable

from .contracts import (
    REF_KEYS, AuthorityContext, ContractError, RecordSet, SchemaBundle,
    SuppliedArtifact, ValidationReport, canonical, exact_ref, kind,
    parse, ref_key,
)


class StorageError(ContractError):
    pass


class StaleSnapshot(StorageError):
    pass


def _exact_reference(reference: dict) -> dict:
    if not isinstance(reference, dict) or set(reference) != REF_KEYS:
        raise StorageError('Expected an exact record reference')
    # Python equality and SQLite coercion must not equate True/1.0 with revision 1.
    if (type(reference['revision']) is not int or not 1 <= reference['revision'] <= 9007199254740991) or not all(
            type(reference[k]) is str for k in REF_KEYS - {'revision'}):
        raise StorageError('Malformed exact reference')
    return dict(reference)


class LocalStore:
    """Immutable exact objects plus explicitly provisional domain head pointers."""
    def __init__(self, path: Path | str, bundle: SchemaBundle, *,
                 readonly: bool = False, timeout: float = 5.0):
        self.bundle = bundle
        self.readonly = readonly
        if readonly:
            uri = Path(path).resolve().as_uri() + '?mode=ro'
            self._db = sqlite3.connect(uri, uri=True, timeout=timeout, isolation_level=None)
        else:
            self._db = sqlite3.connect(str(path), timeout=timeout, isolation_level=None)
        try:
            if not readonly:
                self._db.executescript('''
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS metadata (
                        singleton INTEGER PRIMARY KEY CHECK(singleton=1), bundle_hash TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS records (
                        record_type TEXT NOT NULL, record_id TEXT NOT NULL, revision INTEGER NOT NULL,
                        content_hash TEXT NOT NULL, body BLOB NOT NULL,
                        PRIMARY KEY(record_type, record_id, revision));
                    CREATE TABLE IF NOT EXISTS artifacts (
                        artifact_id TEXT PRIMARY KEY, media_type TEXT NOT NULL, data BLOB NOT NULL);
                    CREATE TABLE IF NOT EXISTS candidate_heads (
                        domain TEXT PRIMARY KEY, reference BLOB NOT NULL);
                    CREATE TRIGGER IF NOT EXISTS records_no_update BEFORE UPDATE ON records
                        BEGIN SELECT RAISE(ABORT, 'immutable record'); END;
                    CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records
                        BEGIN SELECT RAISE(ABORT, 'immutable record'); END;
                    CREATE TRIGGER IF NOT EXISTS artifacts_no_update BEFORE UPDATE ON artifacts
                        BEGIN SELECT RAISE(ABORT, 'immutable artifact'); END;
                    CREATE TRIGGER IF NOT EXISTS artifacts_no_delete BEFORE DELETE ON artifacts
                        BEGIN SELECT RAISE(ABORT, 'immutable artifact'); END;
                    COMMIT;
                ''')
                with self._transaction(write=True):
                    self._db.execute('INSERT OR IGNORE INTO metadata VALUES (1, ?)', (bundle.bundle_hash,))
            row = self._db.execute('SELECT bundle_hash FROM metadata WHERE singleton=1').fetchone()
            if row != (bundle.bundle_hash,):
                raise StorageError('Store uses a different exact schema bundle')
        except BaseException:
            self._db.close()
            raise

    def close(self) -> None:
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @contextmanager
    def _transaction(self, *, write=False):
        if write and self.readonly:
            raise StorageError('Read-only store cannot ingest or move candidate heads')
        self._db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        try:
            yield
            self._db.execute('COMMIT')
        except BaseException:
            if self._db.in_transaction:
                self._db.execute('ROLLBACK')
            raise

    def resolve(self, reference: dict) -> dict:
        reference = _exact_reference(reference)
        row = self._db.execute('SELECT body FROM records WHERE record_type=? AND record_id=? '
                               'AND revision=? AND content_hash=?', ref_key(reference)).fetchone()
        if row is None:
            raise StorageError('Unknown, mistyped or stale exact reference')
        record = parse(row[0])
        issues = self.bundle.validate_record(record)
        if issues or exact_ref(record) != reference:
            raise StorageError('Stored record integrity failure')
        return record

    def artifact(self, reference: dict) -> bytes:
        if not isinstance(reference, dict) or not {'artifact_id','media_type','byte_size','sha256'} <= reference.keys():
            raise StorageError('Expected an exact artifact reference')
        if type(reference['byte_size']) is not int:
            raise StorageError('Artifact size must be an integer')
        row = self._db.execute('SELECT media_type, data FROM artifacts WHERE artifact_id=?',
                               (reference['artifact_id'],)).fetchone()
        if row is None:
            raise StorageError('Unknown exact artifact')
        item = SuppliedArtifact(reference['artifact_id'], row[0], row[1])
        if any(reference[k] != v for k, v in item.reference().items()):
            raise StorageError('Artifact type, size or raw hash mismatch')
        return item.data

    def _record_set(self, authority=None) -> RecordSet:
        records = (row[0] for row in self._db.execute('SELECT body FROM records ORDER BY record_type, record_id, revision'))
        artifacts = (SuppliedArtifact(*row) for row in self._db.execute(
            'SELECT artifact_id, media_type, data FROM artifacts ORDER BY artifact_id'))
        return RecordSet(self.bundle, records, artifacts, authority=authority)

    def candidate_head(self, domain: str) -> dict | None:
        row = self._db.execute('SELECT reference FROM candidate_heads WHERE domain=?', (domain,)).fetchone()
        if row is None:
            return None
        reference = parse(row[0])
        record = self.resolve(reference)
        if kind(record) != 'knowledge-snapshot' or record['payload']['domain'] != domain:
            raise StorageError('Candidate head integrity failure')
        return reference

    def ingest(self, records: Iterable[dict | bytes], artifacts: Iterable[SuppliedArtifact] = (), *,
               authority: AuthorityContext | None = None, snapshot_ref: dict | None = None,
               expected_head: dict | None = None) -> ValidationReport:
        """Atomically retain candidates, optionally CAS a provisional snapshot head.

        Identical retries are allowed; duplicate identities within one request are
        rejected. None is an explicit absent-head expectation when snapshot_ref is
        supplied. A retry of a head update must use the new head expectation and a
        new successor; stale writes never silently become successful.
        """
        if snapshot_ref is None and expected_head is not None:
            raise StorageError('Head expectation requires a snapshot update')
        if snapshot_ref is not None:
            snapshot_ref = _exact_reference(snapshot_ref)
        if expected_head is not None:
            expected_head = _exact_reference(expected_head)
        artifacts = tuple(artifacts)
        supplied = RecordSet(self.bundle, records, artifacts)
        incoming = supplied.records
        # Preserve RecordSet duplicate/shape rejection before accessing record fields.
        for record in incoming:
            issues = self.bundle.validate_record(record)
            if issues:
                raise StorageError('\n'.join(i.message for i in issues))
        identities = [ref_key(exact_ref(r))[:3] for r in incoming]
        if len(identities) != len(set(identities)):
            raise StorageError('Duplicate candidate identity/revision')
        with self._transaction(write=True):
            for record in incoming:
                key = ref_key(exact_ref(record))
                body = canonical(record)
                old = self._db.execute('SELECT body FROM records WHERE record_type=? AND record_id=? AND revision=?', key[:3]).fetchone()
                if old is not None:
                    if old[0] != body:
                        raise StorageError('Immutable record identity/revision overwrite')
                else:
                    self._db.execute('INSERT INTO records VALUES (?, ?, ?, ?, ?)', (*key, body))
            for item in artifacts:
                old = self._db.execute('SELECT media_type, data FROM artifacts WHERE artifact_id=?', (item.artifact_id,)).fetchone()
                if old is not None:
                    if old != (item.media_type, item.data):
                        raise StorageError('Immutable artifact identity overwrite')
                else:
                    self._db.execute('INSERT INTO artifacts VALUES (?, ?, ?)', (item.artifact_id, item.media_type, item.data))
            report = self._record_set(authority).validate(require_artifacts=True)
            report.require_valid()
            if snapshot_ref is not None:
                snapshot = self.resolve(snapshot_ref)
                if kind(snapshot) != 'knowledge-snapshot':
                    raise StorageError('Candidate head must be a knowledge snapshot')
                payload = snapshot['payload']
                if self.candidate_head(payload['domain']) != expected_head:
                    raise StaleSnapshot('Candidate head changed; transaction rolled back')
                if payload['predecessor_ref'] != expected_head:
                    raise StorageError('Snapshot must extend the exact expected candidate head')
                self._db.execute('INSERT INTO candidate_heads VALUES (?, ?) ON CONFLICT(domain) '
                                 'DO UPDATE SET reference=excluded.reference', (payload['domain'], canonical(snapshot_ref)))
        return report

    def query(self, snapshot_ref: dict, references: Iterable[dict] | None = None) -> dict:
        """Read an exact historical snapshot, retaining limiting relation closure.

        Selection is exact membership, not text search. No ranking, latest alias,
        scientific summary, execution, receipts, or durable mutation is performed.
        """
        snapshot_ref = _exact_reference(snapshot_ref)
        if references is not None:
            references = [_exact_reference(r) for r in references]
        with self._transaction():
            records = self._record_set()
            report = records.validate(require_artifacts=True)
            report.require_valid()
            snapshot = records.resolve(snapshot_ref)
            if kind(snapshot) != 'knowledge-snapshot':
                raise StorageError('Query requires an exact knowledge snapshot')
            payload = snapshot['payload']
            selected = payload['entry_refs'] if references is None else list(references)
            returned = {}
            for reference in selected:
                record = records.resolve(reference)
                if reference not in payload['entry_refs']:
                    raise StorageError('Query selection is not in the exact snapshot')
                returned[ref_key(reference)] = record
            relations = [records.resolve(r) for r in payload['relation_refs']]
            visible = {}
            changed = True
            while changed:
                changed = False
                for relation in relations:
                    p = relation['payload']
                    endpoints = [p['source_ref'], p['target_ref']]
                    relation_key = ref_key(exact_ref(relation))
                    if relation_key not in returned and not any(ref_key(r) in returned for r in endpoints):
                        continue
                    visible[relation_key] = relation
                    if p['relation'] in {'CONFLICTING','INCOMPARABLE','CORRECTS','QUALIFIES','REFUTES'}:
                        for reference in endpoints:
                            if ref_key(reference) not in returned:
                                returned[ref_key(reference)] = records.resolve(reference)
                                changed = True
            return {'scope':'LOCAL_CANDIDATE_SNAPSHOT', 'mode':'PROVISIONAL',
                    'knowledge_ref':exact_ref(snapshot), 'canonical_mutation':'FORBIDDEN',
                    'records':[returned[k] for k in sorted(returned)],
                    'relations':[visible[k] for k in sorted(visible)],
                    'authority_checked':False, 'artifact_bytes_checked':True,
                    'limitations':list(report.limitations) + [
                        'Persistence and snapshot membership do not grant scientific approval or reuse permission.',
                        'Stored attestations are not independently authenticated by this read.']}
