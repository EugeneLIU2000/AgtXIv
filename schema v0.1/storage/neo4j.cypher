// Community-compatible node property uniqueness only. DDL only, no parameters.
// Existence, type, hash integrity and full premise closure are importer checks.
// Exact deterministic algorithm: STORAGE.md "图键的确定性计算".
// H(x) = V3 digest(canonical(x)); output is sha256:<64 lowercase hex>.
// exact_key = H(full validated V3 RecordRef / ArtifactRef).
// projection_batch_id = H({archive_batch_id, manifest_sha256, projection_version, view}).
// projection_key = H({projection_batch_id, exact_ref: full validated reference}).
// manifest_sha256 hashes batch.json RAW bytes. Never hash CLI display strings.
CREATE CONSTRAINT agtxiv_record_projection_key IF NOT EXISTS
FOR (n:Record) REQUIRE n.projection_key IS UNIQUE;
CREATE CONSTRAINT agtxiv_artifact_projection_key IF NOT EXISTS
FOR (n:Artifact) REQUIRE n.projection_key IS UNIQUE;
CREATE CONSTRAINT agtxiv_batch_identity IF NOT EXISTS
FOR (n:ProjectionBatch) REQUIRE n.batch_id IS UNIQUE;
CREATE CONSTRAINT agtxiv_view_identity IF NOT EXISTS
FOR (n:ProjectionHead) REQUIRE n.view IS UNIQUE;
