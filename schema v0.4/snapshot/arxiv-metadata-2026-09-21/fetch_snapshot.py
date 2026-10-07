"""Download the Hugging Face copy of the Kaggle arXiv metadata snapshot, pinned to one commit, and verify every file
against the SHA-256 that Hugging Face publishes for it (the LFS oid). Writes MANIFEST.json beside the files."""
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request

REPO = "librarian-bots/arxiv-metadata-snapshot"
API = f"https://huggingface.co/api/datasets/{REPO}"
HERE = pathlib.Path(__file__).resolve().parent


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


info = get_json(API)
commit = info["sha"]
tree = get_json(f"{API}/tree/{commit}/data")
files = sorted((row for row in tree if row["type"] == "file" and row["path"].endswith(".parquet")), key=lambda r: r["path"])
rows = []
for row in files:
    target = HERE / pathlib.Path(row["path"]).name
    expected = row["lfs"]["oid"]
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{commit}/{row['path']}"
    digest = hashlib.sha256()
    if target.exists() and target.stat().st_size == row["size"]:
        with target.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 22), b""):
                digest.update(block)
    else:
        with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as handle:
            for block in iter(lambda: response.read(1 << 22), b""):
                digest.update(block)
                handle.write(block)
    actual = digest.hexdigest()
    ok = actual == expected and target.stat().st_size == row["size"]
    rows.append({"file": target.name, "url": url, "bytes": target.stat().st_size, "sha256": actual, "published_sha256": expected, "verified": ok})
    print(target.name, target.stat().st_size, "OK" if ok else "MISMATCH", flush=True)
manifest = {"source": f"https://huggingface.co/datasets/{REPO}", "commit": commit, "commit_last_modified": info.get("lastModified"),
            "mirrors": "https://www.kaggle.com/datasets/Cornell-University/arxiv (version 304, 2026-09-19T23:51:39Z)",
            "license": "CC0-1.0 (arXiv metadata)", "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "files": rows, "all_verified": all(r["verified"] for r in rows),
            "manifest_sha256": hashlib.sha256(json.dumps(sorted((r["file"], r["sha256"]) for r in rows)).encode()).hexdigest()}
(HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("all_verified", manifest["all_verified"], "commit", commit, flush=True)
