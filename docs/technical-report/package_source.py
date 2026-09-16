#!/usr/bin/env python3
"""Package the complete report source and included appendix, without build caches."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE = Path(__file__).resolve().parent
DEST = HERE / "agtxiv-technical-report-source.zip"
TOP = "agtxiv-technical-report/"


def main() -> None:
    files = sorted(
        [HERE / name for name in ("main.tex", "references.bib", "README.md", "build.sh", "generate_appendix.py", "package_source.py")]
        + list((HERE / "sections").glob("*.tex"))
        + list((HERE / "generated").glob("*.tex"))
        + list((HERE / "generated").glob("*.json"))
    )
    entries = {path.relative_to(HERE).as_posix(): path.read_bytes() for path in files}
    manifest = {
        "kind": "AGTXIV_PORTABLE_TECHNICAL_REPORT_SOURCE",
        "build": "bash build.sh --frozen-appendix",
        "scope": "Compiles the included generated appendix; repository schema drift requires the original repository and default build.",
        "files": [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in entries.items()],
    }
    entries["SOURCE-MANIFEST.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    temporary = DEST.with_suffix(".zip.tmp")
    with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            info = ZipInfo(TOP + name, date_time=(2026, 9, 8, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o100755 if name.endswith((".sh", ".py")) else 0o100644) << 16
            archive.writestr(info, data)
    temporary.replace(DEST)
    print(f"Packaged {len(entries)} source entries: {DEST.name} ({DEST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
