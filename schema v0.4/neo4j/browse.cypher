// schema v0.4 browsing templates (spec §9.5). Each block starts at "// @browse <name>", takes $id,
// starts from the unique :Entity(id) index, names relationship types and directions, bounds depth to
// 1..8 and sets a LIMIT. None computes a transitive count; analysis numbers come from S9 artifacts.
// Every template first requires a READY ProjectionManifest (readers never read a BUILDING graph).

// @browse premises
// What $id rests on: paths down through junctions, at most 8 junctions deep.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH path = (:Entity {id: $id}) (()<-[:CONCLUDES]-(:Junction)<-[:PREMISE_OF]-()){1,8} ()
RETURN path
LIMIT 100

// @browse dependents
// What rests on $id: paths up through junctions, at most 8 junctions deep.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH path = (:Entity {id: $id}) (()-[:PREMISE_OF]->(:Junction)-[:CONCLUDES]->()){1,8} ()
RETURN path
LIMIT 100

// @browse junctions
// The junctions concluding $id with their ordered, typed legs.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (:Entity {id: $id})<-[:CONCLUDES]-(j:Junction)<-[l:PREMISE_OF]-(p)
RETURN j.id AS junction, j.derivation_id AS derivation, j.reading_method AS method,
       l.position AS position, l.role AS role, l.use_site AS use_site, p.id AS premise
ORDER BY junction, position
LIMIT 100

// @browse paper_claims
// The claims paper version $id states.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (:PaperVersion:Entity {id: $id})-[:STATES]->(c:Claim)
RETURN c.id AS claim, c.part AS part, c.occurrence_kind AS kind
ORDER BY claim
LIMIT 100

// @browse work_requests
// External requests whose bibliography entry resolves to work $id.
MATCH (:ProjectionManifest {state: 'READY'})
MATCH (:Work:Entity {id: $id})<-[:RESOLVES_TO]-(b:BibEntry)<-[:REQUESTS_FROM]-(r:ExternalRequest)
RETURN r.id AS request, r.created_by_claim_id AS citing_claim, r.locator_text AS locator,
       b.paper_version_id AS citing_paper
ORDER BY request
LIMIT 100
