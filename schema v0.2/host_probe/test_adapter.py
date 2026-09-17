"""Render a real paper.extract request for every registered provider, with no credential.
Proves: the request description is reconstructible and hashed before any network call, and the
protocol text itself is provider-independent."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import adapter, spec_index

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "Stabilizerness/arXiv-2607.26154v1/draft.tex"
raw = SRC.read_bytes()
BRIEF = ("Extract source locators and claim candidates from the theorem environments of "
         "draft.tex only. Disclose every range you did not read as UNREAD_SCOPE.")

idx, spec_text = spec_index.collect("paper.extract")
print(f"spec index      {idx['index_sha256'][:30]}…")
print(f"spec rendered   {len(spec_text.encode()):,} bytes")
print(f"source          {SRC.name}  {len(raw):,} bytes\n")

for name in sorted(p.stem for p in adapter.PROFILES.glob("*.json")):
    prof = adapter.load_profile(name)
    desc = adapter.render(prof, spec_text, BRIEF, {"draft_tex": raw}, "paper.extract")
    key, envs = adapter.credential(prof)
    print(f"{name}")
    print(f"   provider           {desc['provider']} / {desc['model']}")
    print(f"   profile blob       {prof['_blob']['sha256'][:26]}…  {prof['_blob']['byte_size']} B")
    print(f"   request content    {desc['request_content_sha256'][:26]}…  {desc['rendered_bytes']:,} B")
    print(f"   blocks             {len(desc['blocks'])}  " +
          ", ".join(f"{b['role']}:{b['kind']}" for b in desc['blocks']))
    try:
        adapter.send(prof, desc)
        print("   send               UNEXPECTED: a call went out")
    except adapter.MissingCredential as e:
        print(f"   send               refused, receipt reason ready:")
        print(f"                      \"{e}\"")
    except adapter.ProviderError as e:
        print(f"   send               reached provider, failed: {str(e)[:90]}")
    print()
