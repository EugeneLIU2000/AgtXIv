-- Reference SQLite runtime metadata only; NOT an automatic migration.
-- No business records/artifacts tables: integrate with V3 in ONE database.
-- Exact-reference JSON and hashes are validated by the controlled service.
-- task_ref_json refers to orchestration Task metadata, NOT a V3 RecordRef.
-- Task/Result metadata must never enter the old business RecordSet.
-- UTC timestamps are text. Operational leases/heads/delivery may change by CAS;
-- immutable requests, attempts, events, outbox payloads and checkpoints may not.
PRAGMA foreign_keys = ON;
PRAGMA recursive_triggers = ON;
BEGIN;

CREATE TABLE runtime_tasks (
    task_id TEXT PRIMARY KEY NOT NULL,
    task_ref_json TEXT NOT NULL,
    input_snapshot_ref_json TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE runtime_attempts (
    attempt_id TEXT PRIMARY KEY NOT NULL,
    task_id TEXT NOT NULL REFERENCES runtime_tasks(task_id),
    attempt_number INTEGER NOT NULL CHECK(attempt_number >= 1),
    input_manifest_sha256 TEXT NOT NULL,
    worker_identity_ref_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(task_id, attempt_number)
);
-- Event payload carries task-schema-defined transitions and result exact refs.
CREATE TABLE runtime_events (
    event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES runtime_tasks(task_id),
    attempt_id TEXT REFERENCES runtime_attempts(attempt_id),
    event_type TEXT NOT NULL,
    payload BLOB NOT NULL,
    payload_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE runtime_leases (
    resource_key TEXT PRIMARY KEY NOT NULL,
    holder TEXT NOT NULL,
    fencing_token INTEGER NOT NULL CHECK(fencing_token >= 1),
    expires_at TEXT NOT NULL,
    state_version INTEGER NOT NULL CHECK(state_version >= 1)
);
CREATE TABLE runtime_outbox (
    message_id TEXT PRIMARY KEY NOT NULL,
    event_seq INTEGER NOT NULL REFERENCES runtime_events(event_seq),
    destination TEXT NOT NULL CHECK(destination IN ('GIT_ARCHIVE','NEO4J_PROJECTION')),
    idempotency_key TEXT NOT NULL,
    payload BLOB NOT NULL,
    payload_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(destination, idempotency_key)
);
CREATE TABLE runtime_delivery (
    message_id TEXT PRIMARY KEY NOT NULL REFERENCES runtime_outbox(message_id),
    state TEXT NOT NULL CHECK(state IN ('PENDING','LEASED','RETRY','CONFIRMED','BLOCKED')),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK(retry_count >= 0),
    next_attempt_at TEXT,
    lease_resource_key TEXT REFERENCES runtime_leases(resource_key),
    fencing_token INTEGER,
    result_receipt_json TEXT,
    last_error TEXT,
    state_version INTEGER NOT NULL DEFAULT 1 CHECK(state_version >= 1)
);
-- Append checkpoints; cursor_json includes chunk, counts, hashes and boundaries.
-- batch_id below is the PROJECTION batch ID; receipt/cursor binds archive batch_id.
-- manifest_sha256 is the raw hash of archive batch.json. Current CANDIDATE_EXPORT
-- permits CANDIDATE only; other views are reserved for future admission services.
CREATE TABLE runtime_projection_checkpoints (
    checkpoint_id TEXT PRIMARY KEY NOT NULL,
    message_id TEXT NOT NULL REFERENCES runtime_outbox(message_id),
    batch_id TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    projection_version TEXT NOT NULL,
    view TEXT NOT NULL CHECK(view IN ('ADMITTED_ONLY','CANDIDATE','MIXED')),
    checkpoint_number INTEGER NOT NULL CHECK(checkpoint_number >= 1),
    state TEXT NOT NULL CHECK(state IN ('BUILDING','READY','FAILED')),
    cursor_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(batch_id, checkpoint_number)
);
CREATE TABLE runtime_projection_heads (
    view TEXT PRIMARY KEY NOT NULL CHECK(view IN ('ADMITTED_ONLY','CANDIDATE','MIXED')),
    checkpoint_id TEXT NOT NULL REFERENCES runtime_projection_checkpoints(checkpoint_id),
    state_version INTEGER NOT NULL CHECK(state_version >= 1)
);
CREATE INDEX runtime_events_task ON runtime_events(task_id, event_seq);
CREATE INDEX runtime_delivery_due ON runtime_delivery(state, next_attempt_at);

CREATE TRIGGER runtime_event_attempt_task BEFORE INSERT ON runtime_events
WHEN NEW.attempt_id IS NOT NULL AND NOT EXISTS
    (SELECT 1 FROM runtime_attempts a WHERE a.attempt_id = NEW.attempt_id
     AND a.task_id = NEW.task_id)
BEGIN SELECT RAISE(ABORT, 'attempt belongs to another task'); END;

CREATE TRIGGER runtime_tasks_no_update BEFORE UPDATE ON runtime_tasks
BEGIN SELECT RAISE(ABORT, 'immutable task request'); END;
CREATE TRIGGER runtime_tasks_no_delete BEFORE DELETE ON runtime_tasks
BEGIN SELECT RAISE(ABORT, 'immutable task request'); END;
CREATE TRIGGER runtime_attempts_no_update BEFORE UPDATE ON runtime_attempts
BEGIN SELECT RAISE(ABORT, 'immutable attempt input'); END;
CREATE TRIGGER runtime_attempts_no_delete BEFORE DELETE ON runtime_attempts
BEGIN SELECT RAISE(ABORT, 'immutable attempt input'); END;
CREATE TRIGGER runtime_events_no_update BEFORE UPDATE ON runtime_events
BEGIN SELECT RAISE(ABORT, 'append-only event'); END;
CREATE TRIGGER runtime_events_no_delete BEFORE DELETE ON runtime_events
BEGIN SELECT RAISE(ABORT, 'append-only event'); END;
CREATE TRIGGER runtime_outbox_no_update BEFORE UPDATE ON runtime_outbox
BEGIN SELECT RAISE(ABORT, 'immutable outbox payload'); END;
CREATE TRIGGER runtime_outbox_no_delete BEFORE DELETE ON runtime_outbox
BEGIN SELECT RAISE(ABORT, 'immutable outbox payload'); END;
CREATE TRIGGER runtime_checkpoints_no_update BEFORE UPDATE ON runtime_projection_checkpoints
BEGIN SELECT RAISE(ABORT, 'append-only checkpoint'); END;
CREATE TRIGGER runtime_checkpoints_no_delete BEFORE DELETE ON runtime_projection_checkpoints
BEGIN SELECT RAISE(ABORT, 'append-only checkpoint'); END;
CREATE TRIGGER runtime_head_ready_insert BEFORE INSERT ON runtime_projection_heads
WHEN NOT EXISTS (SELECT 1 FROM runtime_projection_checkpoints c
    WHERE c.checkpoint_id = NEW.checkpoint_id AND c.state = 'READY' AND c.view = NEW.view)
BEGIN SELECT RAISE(ABORT, 'head requires ready checkpoint in same view'); END;
CREATE TRIGGER runtime_head_ready_update BEFORE UPDATE ON runtime_projection_heads
WHEN NOT EXISTS (SELECT 1 FROM runtime_projection_checkpoints c
    WHERE c.checkpoint_id = NEW.checkpoint_id AND c.state = 'READY' AND c.view = NEW.view)
BEGIN SELECT RAISE(ABORT, 'head requires ready checkpoint in same view'); END;
COMMIT;
