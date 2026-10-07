"""Run each schema v0.4 browse template (neo4j/browse.cypher) once on the loaded local projection with a real id, and
record whether Neo4j accepted it and how many rows it returned. Read-only."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "host"), str(HERE.parents[2] / "schema v0.3" / "host")]
import projection  # noqa: E402

client = projection.QueryClient("http://127.0.0.1:7474", "neo4j", "neo4j", "")
client.headers.pop("Authorization")  # local test server, login disabled
one = lambda q: client.run(q, {}, {})[0]["id"]
ids = {"premises": one("MATCH (c:Claim)<-[:CONCLUDES]-(:Junction)<-[:PREMISE_OF]-(:Claim) RETURN c.id AS id ORDER BY c.id LIMIT 1"),
       "dependents": one("MATCH (c:Claim)-[:PREMISE_OF]->(:Junction) RETURN c.id AS id ORDER BY c.id LIMIT 1"),
       "junctions": one("MATCH (c:Claim)<-[:CONCLUDES]-(:Junction) RETURN c.id AS id ORDER BY c.id LIMIT 1"),
       "paper_claims": "arxiv:2512.07919v2",
       "work_requests": one("MATCH (w:Work)<-[:RESOLVES_TO]-(:BibEntry)<-[:REQUESTS_FROM]-(:ExternalRequest) RETURN w.id AS id ORDER BY w.id LIMIT 1")}
out = {}
for name, query in projection.BROWSE.items():
    try:
        rows = client.run(query, {"id": ids[name]}, {"purpose": "browse-check"})
        out[name] = {"id": ids[name], "accepted": True, "rows": len(rows)}
    except RuntimeError as error:
        out[name] = {"id": ids[name], "accepted": False, "error": str(error)[:500]}
(HERE / "browse-check.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, indent=2))
