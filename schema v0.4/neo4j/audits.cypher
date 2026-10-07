// schema v0.4 post-load audits (spec §3.7). Each block re-checks one invariant that the host already
// checked before load and returns rows (invariant, id); a satisfied invariant returns zero rows.
// Blocks start at a line "// @audit <name>"; host/projection.py splits on that line and sends each
// block as one statement with only the parameters it names ($deltas, $dispositions, $enums). No ";"
// terminators.
// G6 (id = digest of identity fields) and the digest part of G15 are host-only: Cypher has no sha256.
// G7 uses the widest work-identity class (every SAME_WORK basis), so a row here is a violation under
// every loading policy; the policy-exact check stays in the host.

// @audit G1
// A junction has exactly one outgoing CONCLUDES, to its conclusion_id, and at least one PREMISE_OF.
MATCH (j:Junction)
WHERE COUNT { (j)-[:CONCLUDES]->() } <> 1
   OR NOT EXISTS { (j)-[:CONCLUDES]->(c) WHERE c.id = j.conclusion_id }
   OR NOT EXISTS { ()-[:PREMISE_OF]->(j) }
RETURN 'G1' AS invariant, j.id AS id

// @audit G2
// PREMISE_OF: Claim or Placeholder -> Junction. CONCLUDES: Junction -> Claim or ExternalRequest.
MATCH (a)-[r:PREMISE_OF]->(b)
WHERE NOT ((a:Claim OR a:Placeholder) AND b:Junction)
RETURN 'G2' AS invariant, r.id AS id
UNION ALL
MATCH (a)-[r:CONCLUDES]->(b)
WHERE NOT (a:Junction AND (b:Claim OR b:ExternalRequest))
RETURN 'G2' AS invariant, r.id AS id

// @audit G3
// Between two logical nodes only PART_OF (Claim -> Claim); a logical node meets a junction only
// through PREMISE_OF or CONCLUDES.
MATCH (a:Logical)-[r]->(b:Logical)
WHERE NOT (type(r) = 'PART_OF' AND a:Claim AND b:Claim)
RETURN 'G3' AS invariant, r.id AS id
UNION ALL
MATCH (a:Logical)-[r]-(b:Junction)
WHERE NOT type(r) IN ['PREMISE_OF', 'CONCLUDES']
RETURN 'G3' AS invariant, r.id AS id

// @audit G4
// A junction's conclusion is not one of its premises.
MATCH (p)-[:PREMISE_OF]->(j:Junction)-[:CONCLUDES]->(p)
RETURN DISTINCT 'G4' AS invariant, j.id AS id

// @audit G5
// Every enumerated contract field takes a listed value and a required one is present ($enums.nodes by
// label, $enums.rels by type: {key, values, list, required}, built from the contracts by
// host/projection.py); leg positions of one junction are exactly 0..leg_count-1; Placeholder secondary
// labels match kind; Claim and Placeholder carry :Logical.
MATCH (n:Entity)
UNWIND $enums.nodes AS f
WITH n, f, n[f.key] AS v
WHERE f.label IN labels(n)
  AND CASE WHEN v IS NULL THEN f.required
           WHEN f.list THEN any(x IN v WHERE NOT x IN f.values)
           ELSE NOT v IN f.values END
RETURN DISTINCT 'G5' AS invariant, n.id AS id
UNION ALL
MATCH ()-[r]->()
UNWIND $enums.rels AS f
WITH r, f, r[f.key] AS v
WHERE type(r) = f.type
  AND CASE WHEN v IS NULL THEN f.required
           WHEN f.list THEN any(x IN v WHERE NOT x IN f.values)
           ELSE NOT v IN f.values END
RETURN DISTINCT 'G5' AS invariant, r.id AS id
UNION ALL
MATCH (j:Junction)
OPTIONAL MATCH ()-[r:PREMISE_OF]->(j)
WITH j, collect(r.position) AS ps
WHERE size(ps) <> coalesce(j.leg_count, -1)
   OR any(i IN range(0, size(ps) - 1) WHERE NOT i IN ps)
RETURN 'G5' AS invariant, j.id AS id
UNION ALL
MATCH (n:Entity)
WHERE (n:Placeholder AND ((n:ExternalRequest) <> (coalesce(n.kind, '') = 'EXTERNAL_REQUEST')
                          OR (n:UnresolvedOccurrence) <> (coalesce(n.kind, '') = 'UNRESOLVED_OCCURRENCE')))
   OR (n:Claim OR n:Placeholder) <> (n:Logical)
RETURN 'G5' AS invariant, n.id AS id

// @audit G7
// derivation_id starts with "source:" iff the conclusion is an EXTERNAL_REQUEST; for a
// source:<pv>:<key> junction, pv is VERSION_OF a work in the request's class and every Claim premise
// is STATED by pv or STATED_BY a work in that class.
MATCH (j:Junction)-[:CONCLUDES]->(c)
WHERE (coalesce(j.derivation_id, '') STARTS WITH 'source:') <> (c:ExternalRequest)
RETURN 'G7' AS invariant, j.id AS id
UNION ALL
MATCH (p:Claim)-[:PREMISE_OF]->(j:Junction)-[:CONCLUDES]->(r:ExternalRequest)
WHERE j.derivation_id STARTS WITH 'source:'
WITH p, j, r, split(j.derivation_id, ':') AS d
OPTIONAL MATCH (r)-[:REQUESTS_FROM]->(:BibEntry)-[:RESOLVES_TO]->(:Work)-[:SAME_WORK*0..]-(w:Work)
WITH p, j, d[1] + ':' + d[2] AS pv, collect(DISTINCT w.id) AS works
WHERE NOT EXISTS { (v:PaperVersion)-[:VERSION_OF]->(x:Work) WHERE v.id = pv AND x.id IN works }
   OR NOT (EXISTS { (v:PaperVersion)-[:STATES]->(p) WHERE v.id = pv }
           OR EXISTS { (p)-[:STATED_BY]->(x:Work) WHERE x.id IN works })
RETURN DISTINCT 'G7' AS invariant, j.id AS id

// @audit G8
// An EXTERNAL_REQUEST has exactly one REQUESTS_FROM (to its bib_entry_id) and is a premise of a
// junction whose conclusion and derivation are those in its identity.
MATCH (r:ExternalRequest)
WHERE COUNT { (r)-[:REQUESTS_FROM]->() } <> 1
   OR NOT EXISTS { (r)-[:REQUESTS_FROM]->(b:BibEntry) WHERE b.id = r.bib_entry_id }
   OR NOT EXISTS { (r)-[:PREMISE_OF]->(j:Junction)
                   WHERE j.conclusion_id = r.created_by_claim_id
                     AND j.derivation_id = r.citing_derivation_id }
RETURN 'G8' AS invariant, r.id AS id

// @audit G9
// Every projected element has a non-empty asserted_by drawn from the loaded manifest's deltas.
MATCH (n:Entity)
WHERE NOT n:ProjectionManifest
  AND (size(coalesce(n.asserted_by, [])) = 0 OR any(d IN n.asserted_by WHERE NOT d IN $deltas))
RETURN 'G9' AS invariant, n.id AS id
UNION ALL
MATCH ()-[r]->()
WHERE size(coalesce(r.asserted_by, [])) = 0 OR any(d IN r.asserted_by WHERE NOT d IN $deltas)
RETURN 'G9' AS invariant, r.id AS id

// @audit G10
// Every Claim has exactly one STATES from its paper version (PAPER_VERSION) or exactly one
// STATED_BY to its work (WORK_LOCATOR), and not the other.
MATCH (c:Claim)
WITH c,
     COUNT { ()-[:STATES]->(c) } AS s,
     COUNT { (v:PaperVersion)-[:STATES]->(c) WHERE v.id = c.paper_version_id } AS sv,
     COUNT { (c)-[:STATED_BY]->() } AS b,
     COUNT { (c)-[:STATED_BY]->(w:Work) WHERE w.id = c.work_id } AS bw
WHERE NOT ((c.origin = 'PAPER_VERSION' AND s = 1 AND sv = 1 AND b = 0)
        OR (c.origin = 'WORK_LOCATOR' AND b = 1 AND bw = 1 AND s = 0))
RETURN 'G10' AS invariant, c.id AS id

// @audit G11
// disposition equals the value derived from the loaded review set, element by element.
MATCH (n:Entity)
WHERE coalesce(n.disposition, '') <> coalesce($dispositions[n.id], '')
RETURN 'G11' AS invariant, n.id AS id
UNION ALL
MATCH ()-[r]->()
WHERE coalesce(r.disposition, '') <> coalesce($dispositions[r.id], '')
RETURN 'G11' AS invariant, r.id AS id

// @audit G12
// A proof:* or unlocated:* junction has only premises STATED by the conclusion's paper version, or
// placeholders created by a claim that paper version STATES.
MATCH (p)-[:PREMISE_OF]->(j:Junction)-[:CONCLUDES]->(c)
WHERE (j.derivation_id STARTS WITH 'proof:' OR j.derivation_id STARTS WITH 'unlocated:')
  AND NOT EXISTS { (v:PaperVersion)-[:STATES]->(s:Claim)
                   WHERE v.id = c.paper_version_id
                     AND (s = p OR (p:Placeholder AND s.id = p.created_by_claim_id)) }
RETURN DISTINCT 'G12' AS invariant, j.id AS id

// @audit G13
// At most one statement junction per (conclusion, reading_method, method_version); STATEMENT legs occur
// only in statement junctions.
MATCH (j:Junction)-[:CONCLUDES]->(c)
WHERE j.derivation_id = 'statement'
WITH c, j.reading_method AS m, j.method_version AS v, collect(j.id) AS js
WHERE size(js) > 1
UNWIND js AS jid
RETURN 'G13' AS invariant, jid AS id
UNION ALL
MATCH ()-[r:PREMISE_OF]->(j:Junction)
WHERE (coalesce(r.use_site, '') = 'STATEMENT') <> (coalesce(j.derivation_id, '') = 'statement')
RETURN DISTINCT 'G13' AS invariant, j.id AS id

// @audit G14
// No junction rests on a superseded reading of its conclusion (same method and method_version);
// SUPERSEDES is acyclic and each reading has at most one successor. A junction names no reading, so
// its basis is every reading of (conclusion, reading_method, method_version); if any is superseded the
// junction is flagged, as in host/invariants.py (a correction needs a new method or method_version).
MATCH (j:Junction)-[:CONCLUDES]->(:Claim)<-[:READS]-(old:ClaimReading)<-[:SUPERSEDES]-(:ClaimReading)
WHERE old.method = j.reading_method AND old.method_version = j.method_version
RETURN DISTINCT 'G14' AS invariant, j.id AS id
UNION ALL
MATCH (r:ClaimReading)-[:SUPERSEDES*1..]->(r)
RETURN DISTINCT 'G14' AS invariant, r.id AS id
UNION ALL
MATCH (r:ClaimReading)
WHERE COUNT { (:ClaimReading)-[:SUPERSEDES]->(r) } > 1
RETURN 'G14' AS invariant, r.id AS id

// @audit G15
// Relationship ids are rel:-prefixed and unique across all types (per-type uniqueness is also a
// constraint); whether an id equals its digest is checked by the host.
MATCH ()-[r]->()
WITH r.id AS rid, count(r) AS n
WHERE n > 1 OR NOT coalesce(rid, '') STARTS WITH 'rel:'
RETURN 'G15' AS invariant, rid AS id
