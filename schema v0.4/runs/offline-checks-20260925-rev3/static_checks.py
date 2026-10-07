"""Offline static checks: JSON syntax, Draft 2020-12 metaschema, Cypher statement split / bracket and quote balance / params."""
import json, re, sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT / "host"), str(ROOT.parent / "schema v0.3" / "host")]
jsons = sorted(ROOT.rglob("*.json"))
for p in jsons:
    json.loads(p.read_bytes())
schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
for p in schemas:
    Draft202012Validator.check_schema(json.loads(p.read_bytes()))
print(f"JSON parsed: {len(jsons)}; metaschema-valid schemas: {len(schemas)}")

def scan(text):
    """Balanced (), [], {} outside quotes, and every ', \", ` closed; // line comments ignored."""
    stack, quote, i = [], None, 0
    pairs = {")": "(", "]": "[", "}": "{"}
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\" and quote != "`":
                i += 2; continue
            if ch == quote:
                quote = None
        elif text.startswith("//", i):
            i = text.find("\n", i); i = len(text) if i < 0 else i; continue
        elif ch in "'\"`":
            quote = ch
        elif ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        i += 1
    return not stack and quote is None

import projection as P
total = 0
for name in ("schema.cypher", "audits.cypher", "browse.cypher"):
    text = (ROOT / "neo4j" / name).read_text()
    assert scan(text), name
    if name == "schema.cypher":
        stmts = [s for s in P.SCHEMA]
        assert all(scan(s) for s in stmts) and len(stmts) == sum(l.count(";") for l in text.splitlines() if not l.lstrip().startswith("//")), name
    else:
        blocks = P.AUDITS if name == "audits.cypher" else tuple(P.BROWSE.items())
        stmts = [q for _, q in blocks]
        assert len(stmts) == len(re.findall(r"^// @" + name.split(".")[0].rstrip("s") + r" \S+$", text, re.M)) and all(scan(q) and ";" not in q for q in stmts), name
    total += len(stmts)
    print(f"{name}: {len(stmts)} statements, brackets and quotes balanced")
templates = [*P.NODE_MERGE.values(), *P.REL_MERGE.values(), P.NODE_PREFLIGHT, *P.REL_PREFLIGHT.values(), P.EXISTING, P.SET_MANIFEST]
assert all(scan(t) for t in templates)
node_fields = {"id", "content_sha256", "props"}
rel_fields = {"id", "content_sha256", "start", "end", "props"}
for t in P.NODE_MERGE.values():
    assert set(re.findall(r"\brow\.(\w+)", t)) <= node_fields and set(re.findall(r"\$(\w+)", t)) == {"rows"}
for t in P.REL_MERGE.values():
    assert set(re.findall(r"\brow\.(\w+)", t)) <= rel_fields and set(re.findall(r"\$(\w+)", t)) == {"rows"}
for t in (P.NODE_PREFLIGHT, *P.REL_PREFLIGHT.values()):  # preflight rows are {id, content_sha256}
    assert set(re.findall(r"\brow\.(\w+)", t)) <= {"id", "content_sha256"}
params = {"deltas", "dispositions", "enums"}
for name, q in P.AUDITS:
    assert set(re.findall(r"\$(\w+)", q)) <= params, name
    assert set(re.findall(r"\$enums\.(\w+)", q)) <= set(P.ENUMS), name
for name, q in P.BROWSE.items():
    assert set(re.findall(r"\$(\w+)", q)) == {"id"}, name
assert set(re.findall(r"\$(\w+)", P.SET_MANIFEST)) == {"id", "props"}
print(f"in-code templates: {len(templates)} balanced; every row./$ parameter is a field the loader sends")
print(f"total cypher statements checked: {total + len(templates)}")
