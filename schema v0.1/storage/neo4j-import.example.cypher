// PARAMETERIZED EXAMPLES, NOT a one-shot script or a complete importer.
// Execute each numbered statement separately through a controlled driver.
// Before ANY write, verify immutable manifest/bytes, batch identity, non-null
// exact keys and view membership. One fenced writer per batch; no agent access.
// Parameters: $batch_id, $manifest_sha256, $git_commit, $projection_version,
// $view, $records (validated maps), $steps (validated maps).
// $batch_id is projection identity; bind original export batch_id in receipt.
// $manifest_sha256 hashes batch.json. Current CANDIDATE_EXPORT requires
// $view = 'CANDIDATE'; it cannot produce an admitted or mixed graph.
// Reusing a batch/key with differing content MUST fail in the importing service.
// Recompute every key from verified batch.json/record bytes using V3 canonical()
// and digest(), exactly as STORAGE.md specifies. Never trust keys supplied by rows.
// H(x)=digest(canonical(x)); exact_key=H(full exact_ref).
// projection_batch_id=H({archive_batch_id,manifest_sha256,projection_version,view}).
// projection_key=H({projection_batch_id,exact_ref}); $batch_id=projection_batch_id.
// All hash strings retain the sha256: prefix and lowercase hexadecimal.

// 1. Begin or resume an identical batch. On match the driver must compare ALL
// returned identity properties; mismatches abort, they are never overwritten.
MERGE (b:ProjectionBatch {batch_id: $batch_id})
ON CREATE SET b.manifest_sha256 = $manifest_sha256,
              b.git_commit = $git_commit,
              b.projection_version = $projection_version,
              b.view = $view, b.state = 'BUILDING'
RETURN b;

// 2. Import a node chunk only while BUILDING. $records are flattened projections
// of V3 objects, not new business objects. exact_key hashes the full V3 ref.
MATCH (b:ProjectionBatch {batch_id: $batch_id, state: 'BUILDING'})
UNWIND $records AS row
MERGE (r:Record {projection_key: row.projection_key})
ON CREATE SET r.batch_id = $batch_id, r.exact_key = row.exact_key,
              r.record_type = row.record_type, r.record_id = row.record_id,
              r.revision = row.revision, r.content_hash = row.content_hash
MERGE (b)-[:CONTAINS]->(r)
RETURN count(r) AS processed;

// 3. Joint inference example. Validate every step/premise/conclusion belongs to
// this batch BEFORE execution. Each row has step_key, conclusion_key and the
// COMPLETE premise_keys array. Nulls/duplicates/missing endpoints are rejected.
// A missing MATCH can silently drop rows in Cypher: driver must compare exact
// imported sets with the manifest, including zero-premise steps, before READY.
// Context, rule, route and evidence refs require additional importer mappings;
// their absence in this minimal example MUST NOT certify a complete projection.
MATCH (b:ProjectionBatch {batch_id: $batch_id, state: 'BUILDING'})
UNWIND $steps AS row
MATCH (s:Record {projection_key: row.step_key, batch_id: $batch_id})
MATCH (c:Record {projection_key: row.conclusion_key, batch_id: $batch_id})
SET s:InferenceStep
MERGE (s)-[:CONCLUDES]->(c)
WITH s, row
UNWIND row.premise_keys AS premise_key
MATCH (p:Record {projection_key: premise_key, batch_id: $batch_id})
MERGE (p)-[:PREMISE_OF]->(s)
RETURN count(*) AS premise_links_processed;

// 4. Query one READY batch, never an implicit latest graph.
// Default application $view is ADMITTED_ONLY; candidate queries opt in explicitly.
// Actual service must return all STORAGE.md snapshot-boundary fields and apply
// permissions. READY transition and visible-head CAS deliberately are NOT given
// here: they require full closure/set/hash checks absent from this example.
MATCH (b:ProjectionBatch {batch_id: $batch_id, view: $view, state: 'READY'})
MATCH (b)-[:CONTAINS]->(r:Record)
RETURN b.batch_id, b.manifest_sha256, b.git_commit, b.projection_version,
       b.view, r.exact_key, r.record_type, r.content_hash;
