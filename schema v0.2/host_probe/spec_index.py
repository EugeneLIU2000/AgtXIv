"""Build the pinned spec index a Task must carry, and render it for any model.

CONTRACT.md section 1: "The spec index must cover the specifications actually read, all five
schemas, applicable Agent documents, and implementation identity."

The index serves two purposes at once. It pins, by original-byte hash, exactly which
specification the model was shown; and it renders that same text into the prompt, so a model
with no prior knowledge of this protocol can still produce conforming output. Nothing here is
provider-specific.
"""
import hashlib, json, pathlib

SPEC = pathlib.Path(__file__).resolve().parent.parent          # schema v0.2/
REPO = SPEC.parent

CORE = ["CONTRACT.md", "HOST.md", "STORAGE.md"]
SCHEMAS = ["common.schema.json", "task.schema.json", "items.schema.json",
           "output.schema.json", "run.schema.json"]
AGENT_FOR = {
    "paper.extract": "Paper Agent/AGENT.md",
    "dependency.search": "Dependency Agent/AGENT.md",
    "autoformalization.lamport": "Autoformalization Agent/AGENT.md",
    "autoformalization.lean": "Autoformalization Agent/AGENT.md",
}
IMPL = ["host_probe/registry.py", "host_probe/resolve.py", "host_probe/store.py",
        "host_probe/check_output.py", "host_probe/adapter.py", "host_probe/expand.py",
        "host_probe/cost.py", "host_probe/spec_index.py"]

def digest(b): return "sha256:" + hashlib.sha256(b).hexdigest()

def collect(operation):
    """Returns (index, rendered_text). index pins bytes; rendered_text goes in the prompt."""
    if operation not in AGENT_FOR:
        raise ValueError(f"unknown operation {operation!r}")
    parts, entries = [], []
    def add(rel, render=True):
        p = SPEC / rel
        b = p.read_bytes()
        entries.append({"path": f"schema v0.2/{rel}", "sha256": digest(b), "byte_size": len(b),
                        "rendered": render})
        if render: parts.append((rel, b.decode("utf-8")))
    for f in CORE: add(f)
    add(AGENT_FOR[operation])
    for s in SCHEMAS: add(f"schemas/{s}")
    for f in IMPL:
        p = SPEC / f
        if p.exists(): add(f, render=False)      # identity only; never shown to the model
    index = {"spec_version": "research/0.2.0", "operation": operation,
             "renderer_version": "spec-index/1.0", "entries": entries}
    index["index_sha256"] = digest(json.dumps(index, sort_keys=True, separators=(",", ":")).encode())
    rendered = "\n\n".join(
        f"===== {rel} =====\n{text}" for rel, text in parts)
    return index, rendered

if __name__ == "__main__":
    import sys
    op = sys.argv[1] if len(sys.argv) > 1 else "paper.extract"
    idx, txt = collect(op)
    shown = sum(1 for e in idx["entries"] if e["rendered"])
    print(f"operation      {op}")
    print(f"index_sha256   {idx['index_sha256']}")
    print(f"entries        {len(idx['entries'])}  ({shown} rendered into the prompt, "
          f"{len(idx['entries'])-shown} identity-only)")
    print(f"rendered size  {len(txt.encode()):,} bytes  (~{len(txt)//4:,} tokens, rough)")
    print()
    for e in idx["entries"]:
        mark = "render" if e["rendered"] else "  pin "
        print(f"  [{mark}] {e['byte_size']:>7,}  {e['sha256'][:22]}…  {e['path']}")
