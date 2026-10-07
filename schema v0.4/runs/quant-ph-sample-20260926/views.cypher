// Views of the quant-ph test projection in Neo4j Browser (http://127.0.0.1:7474/browser/, local server, no login).
// Every view starts from the READY ProjectionManifest, like the browse templates in schema v0.4/neo4j/browse.cypher.

// @view dependency_skeleton
// Every deterministic dependency: premise -[:PREMISE_OF]-> junction -[:CONCLUDES]-> conclusion, with the stating paper.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (pv:PaperVersion)-[s:STATES]->(c:Claim)<-[k:CONCLUDES]-(j:Junction)<-[l:PREMISE_OF]-(x)
RETURN pv, s, c, k, j, l, x
LIMIT 600

// @view one_paper
// One paper's dependency graph; set $id to a paper version id, e.g. :param id => 'arxiv:1512.00602v1'
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (pv:PaperVersion {id: $id})-[:STATES]->(c:Claim)
OPTIONAL MATCH p = (c)<-[:CONCLUDES]-(:Junction)<-[:PREMISE_OF]-()
RETURN pv, c, p
LIMIT 300

// @view shared_works
// Works cited by at least two sample papers (explicit arXiv or DOI identity only; S4 host rules).
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (w:Work)<-[:RESOLVES_TO]-(b:BibEntry)
WITH w, count(DISTINCT b.paper_version_id) AS citing WHERE citing >= 2
MATCH p = (:PaperVersion)-[:HAS_ENTRY]->(:BibEntry)-[:RESOLVES_TO]->(w)
RETURN p
LIMIT 400

// @view counts
// Row counts by label, for comparison with runs/quant-ph-sample-20260926/projection-manifest.json.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (n:Entity)
RETURN labels(n) AS labels, count(*) AS nodes
ORDER BY nodes DESC
