// schema v0.4 Neo4j projection schema (spec §9.3). Community Edition: uniqueness constraints only.
// Idempotent (IF NOT EXISTS); one statement per line, terminated by ";". host/projection.py splits on ";".
// Written for Neo4j 5.26 LTS and 2026.x (Cypher 5 and Cypher 25 accept the same text); no version prefix.
// Review, AnalysisRun and Nomination are not projected in v0.4 (reviews act through derived dispositions;
// nominations stay immutable artifacts), so they have no constraint here.
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT corpus_id IF NOT EXISTS FOR (n:Corpus) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT paper_version_id IF NOT EXISTS FOR (n:PaperVersion) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT work_id IF NOT EXISTS FOR (n:Work) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT bib_entry_id IF NOT EXISTS FOR (n:BibEntry) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (n:Claim) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT claim_reading_id IF NOT EXISTS FOR (n:ClaimReading) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT junction_id IF NOT EXISTS FOR (n:Junction) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT placeholder_id IF NOT EXISTS FOR (n:Placeholder) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT primitive_assertion_id IF NOT EXISTS FOR (n:PrimitiveAssertion) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT projection_manifest_id IF NOT EXISTS FOR (n:ProjectionManifest) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT rel_states_id IF NOT EXISTS FOR ()-[r:STATES]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_stated_by_id IF NOT EXISTS FOR ()-[r:STATED_BY]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_reads_id IF NOT EXISTS FOR ()-[r:READS]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_part_of_id IF NOT EXISTS FOR ()-[r:PART_OF]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_has_entry_id IF NOT EXISTS FOR ()-[r:HAS_ENTRY]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_resolves_to_id IF NOT EXISTS FOR ()-[r:RESOLVES_TO]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_requests_from_id IF NOT EXISTS FOR ()-[r:REQUESTS_FROM]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_mentions_id IF NOT EXISTS FOR ()-[r:MENTIONS]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_restates_result_of_id IF NOT EXISTS FOR ()-[r:RESTATES_RESULT_OF]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_version_of_id IF NOT EXISTS FOR ()-[r:VERSION_OF]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_same_work_id IF NOT EXISTS FOR ()-[r:SAME_WORK]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_corrects_id IF NOT EXISTS FOR ()-[r:CORRECTS]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_supersedes_id IF NOT EXISTS FOR ()-[r:SUPERSEDES]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_asserts_primitive_id IF NOT EXISTS FOR ()-[r:ASSERTS_PRIMITIVE]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_includes_id IF NOT EXISTS FOR ()-[r:INCLUDES]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_premise_of_id IF NOT EXISTS FOR ()-[r:PREMISE_OF]-() REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT rel_concludes_id IF NOT EXISTS FOR ()-[r:CONCLUDES]-() REQUIRE r.id IS UNIQUE;
CREATE RANGE INDEX work_doi IF NOT EXISTS FOR (n:Work) ON (n.doi);
CREATE RANGE INDEX work_arxiv_base_id IF NOT EXISTS FOR (n:Work) ON (n.arxiv_base_id);
CREATE RANGE INDEX work_openalex_id IF NOT EXISTS FOR (n:Work) ON (n.openalex_id);
CREATE RANGE INDEX paper_version_arxiv_base_id IF NOT EXISTS FOR (n:PaperVersion) ON (n.arxiv_base_id);
CREATE RANGE INDEX claim_paper_version_id IF NOT EXISTS FOR (n:Claim) ON (n.paper_version_id);
CREATE RANGE INDEX junction_conclusion_id IF NOT EXISTS FOR (n:Junction) ON (n.conclusion_id);
CREATE RANGE INDEX junction_derivation_id IF NOT EXISTS FOR (n:Junction) ON (n.derivation_id);
CREATE RANGE INDEX placeholder_kind IF NOT EXISTS FOR (n:Placeholder) ON (n.kind);
