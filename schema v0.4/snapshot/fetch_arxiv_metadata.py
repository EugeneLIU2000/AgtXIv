"""Fetch the arXiv metadata snapshot that the schema v0.4 runs read, pinned to one Hugging Face commit, and check every
file against the SHA-256 that Hugging Face publishes for it and against the recorded manifest.

    python 'schema v0.4/snapshot/fetch_arxiv_metadata.py' [--commit SHA] [--output DIR]

Defaults: the commit the 2026-09-26 runs used (a weekly copy of Kaggle Cornell-University/arxiv version 304), written to
local-archive/arxiv-metadata/2026-09-21 under the repository root, which Git ignores. The download is about 3 GB.
arxiv-metadata-2026-09-21/ beside this script holds what actually ran then: the original script (which took the
dataset's latest commit), its log and its MANIFEST.json. With the default commit the new manifest must list the same
files and digests, so its manifest_sha256 equals the recorded one. The metadata is CC0-1.0.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import urllib.request

DATASET = "librarian-bots/arxiv-metadata-snapshot"
API = f"https://huggingface.co/api/datasets/{DATASET}"
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # schema v0.4/snapshot -> repository root
RECORD = json.loads((HERE / "arxiv-metadata-2026-09-21" / "MANIFEST.json").read_text())


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def manifest_sha256(rows):
    return hashlib.sha256(json.dumps(sorted((r["file"], r["sha256"]) for r in rows)).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--commit", default=RECORD["commit"], help="Hugging Face dataset commit (default: the recorded one)")
    parser.add_argument("--output", default=str(ROOT / "local-archive" / "arxiv-metadata" / "2026-09-21"))
    args = parser.parse_args()
    out = pathlib.Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    info = get_json(f"{API}/revision/{args.commit}")
    tree = get_json(f"{API}/tree/{args.commit}/data")
    files = sorted((row for row in tree if row["type"] == "file" and row["path"].endswith(".parquet")), key=lambda r: r["path"])
    rows = []
    for row in files:
        target = out / pathlib.Path(row["path"]).name
        url = f"https://huggingface.co/datasets/{DATASET}/resolve/{args.commit}/{row['path']}"
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
        ok = digest.hexdigest() == row["lfs"]["oid"] and target.stat().st_size == row["size"]
        rows.append({"file": target.name, "url": url, "bytes": target.stat().st_size, "sha256": digest.hexdigest(),
                     "published_sha256": row["lfs"]["oid"], "verified": ok})
        print(target.name, target.stat().st_size, "OK" if ok else "MISMATCH", flush=True)
    manifest = {"source": f"https://huggingface.co/datasets/{DATASET}", "commit": args.commit,
                "commit_last_modified": info.get("lastModified"), "mirrors": RECORD.get("mirrors"),
                "license": "CC0-1.0 (arXiv metadata)", "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "files": rows, "all_verified": all(r["verified"] for r in rows), "manifest_sha256": manifest_sha256(rows)}
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    same = manifest["manifest_sha256"] == RECORD["manifest_sha256"]
    print("all_verified", manifest["all_verified"], "| same files as the 2026-09-21 record:", same, flush=True)
    return 0 if manifest["all_verified"] and (same or args.commit != RECORD["commit"]) else 1


if __name__ == "__main__":
    sys.exit(main())
