PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id TEXT PRIMARY KEY,
    schema_id TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    description TEXT,
    manifest_path TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS paper_works (
    work_id TEXT PRIMARY KEY,
    title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_versions (
    paper_version_id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL REFERENCES paper_works(work_id),
    primary_source_artifact_id TEXT NOT NULL,
    source_artifact_ids_json TEXT NOT NULL,
    source_bundle_complete INTEGER NOT NULL CHECK (source_bundle_complete IN (0, 1)),
    UNIQUE (work_id, paper_version_id)
);

CREATE TABLE IF NOT EXISTS queries (
    query_id TEXT PRIMARY KEY,
    raw_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    fingerprint_sha256 TEXT NOT NULL UNIQUE,
    scope_artifact_id TEXT NOT NULL,
    target_refs_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS query_papers (
    query_id TEXT NOT NULL REFERENCES queries(query_id),
    paper_version_id TEXT NOT NULL REFERENCES paper_versions(paper_version_id),
    role TEXT NOT NULL CHECK (role IN ('TARGET', 'DEPENDENCY', 'BACKGROUND')),
    PRIMARY KEY (query_id, paper_version_id)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL UNIQUE REFERENCES datasets(dataset_id),
    query_id TEXT NOT NULL REFERENCES queries(query_id),
    attempt INTEGER NOT NULL CHECK (attempt >= 1),
    execution_state TEXT NOT NULL,
    outcome TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    producer_json TEXT NOT NULL,
    code_commit TEXT NOT NULL,
    working_tree_state TEXT NOT NULL,
    command_json TEXT NOT NULL,
    reproducibility_refs_json TEXT NOT NULL,
    input_snapshot_ref TEXT,
    idempotency_key_sha256 TEXT,
    retry_of_run_id TEXT REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    media_type TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    UNIQUE (sha256, byte_size)
);

CREATE TABLE IF NOT EXISTS run_artifacts (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    role TEXT NOT NULL CHECK (role IN ('INPUT', 'INTERMEDIATE', 'OUTPUT', 'EVIDENCE', 'LOG')),
    storage_class TEXT NOT NULL,
    authority TEXT NOT NULL,
    publication_state TEXT NOT NULL CHECK (publication_state IN ('FROZEN', 'STAGING', 'PUBLISHED', 'SUPERSEDED')),
    repo_path TEXT NOT NULL,
    schema_name TEXT,
    schema_version TEXT,
    source_refs_json TEXT NOT NULL,
    PRIMARY KEY (run_id, artifact_id)
);

CREATE TABLE IF NOT EXISTS provenance_edges (
    edge_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    from_ref TEXT NOT NULL,
    relation TEXT NOT NULL,
    to_ref TEXT NOT NULL,
    CHECK (from_ref <> to_ref)
);

CREATE TABLE IF NOT EXISTS knowledge_records (
    object_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    kind TEXT NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
    content_hash TEXT NOT NULL,
    supersedes_object_id TEXT,
    supersedes_revision INTEGER,
    supersedes_content_hash TEXT,
    record_locator_json TEXT NOT NULL,
    PRIMARY KEY (object_id, revision),
    CHECK (
        (supersedes_object_id IS NULL AND supersedes_revision IS NULL AND supersedes_content_hash IS NULL)
        OR
        (supersedes_object_id = object_id AND supersedes_revision < revision AND supersedes_content_hash IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS audit_findings (
    dataset_id TEXT NOT NULL REFERENCES datasets(dataset_id),
    ordinal INTEGER NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'ERROR')),
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    related_refs_json TEXT NOT NULL,
    PRIMARY KEY (dataset_id, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_query_papers_paper
    ON query_papers(paper_version_id);

CREATE INDEX IF NOT EXISTS idx_runs_query
    ON runs(query_id, captured_at);

CREATE INDEX IF NOT EXISTS idx_artifacts_kind
    ON artifacts(kind);

CREATE INDEX IF NOT EXISTS idx_run_artifacts_role
    ON run_artifacts(run_id, role, publication_state);

CREATE INDEX IF NOT EXISTS idx_provenance_from
    ON provenance_edges(from_ref, relation);

CREATE INDEX IF NOT EXISTS idx_provenance_to
    ON provenance_edges(to_ref, relation);

PRAGMA user_version = 1;
