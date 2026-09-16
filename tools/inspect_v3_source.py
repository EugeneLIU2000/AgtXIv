#!/usr/bin/env python3
"""Inspect an explicitly selected local source tree; never execute its contents."""
from __future__ import annotations

import argparse
from dataclasses import fields
import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agtxiv_v3.intake import IntakeLimits, inspect_source_directory, _open_directory_no_symlinks  # noqa: E402
from agtxiv_v3.source import SourceError  # noqa: E402


def _write_new_file(path: Path, data: bytes) -> None:
    """Publish complete bytes without replacing any existing path."""
    if path.name in {"", ".", ".."}:
        raise SourceError("Output must name a previously absent file")
    _, parent_fd = _open_directory_no_symlinks(path.parent)
    temporary = ".agtxiv-inspection-" + secrets.token_hex(16)
    created = False
    try:
        try:
            os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise SourceError("Output already exists and will not be overwritten")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
        created = True
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # link is an atomic no-replace publication of the complete same-device
        # temporary file, including when another writer races to create target.
        os.link(temporary, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False)
    finally:
        try:
            if created:
                os.unlink(temporary, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog="Exit 0 means an inspection report was produced; unresolved syntax remains explicit in that report.")
    parser.add_argument("root", type=Path, help="Explicit source directory; no symlinks are followed")
    parser.add_argument("--main", required=True, help="Relative POSIX path of the chosen TeX main")
    parser.add_argument("--working-directory", default=".", help="TeX working directory relative to source root (default: .)")
    parser.add_argument("--output", type=Path, help="Previously absent JSON output path; omitted means stdout")
    defaults = IntakeLimits()
    for field in fields(IntakeLimits):
        parser.add_argument("--" + field.name.replace("_", "-"), type=int, default=getattr(defaults, field.name))
    args = parser.parse_args(argv)
    try:
        limits = IntakeLimits(**{field.name: getattr(args, field.name) for field in fields(IntakeLimits)})
        inspection = inspect_source_directory(args.root, args.main, working_directory=args.working_directory, limits=limits)
        payload = inspection.json_bytes()
        if args.output is None:
            sys.stdout.buffer.write(payload)
        else:
            _write_new_file(args.output, payload)
        return 0
    except (SourceError, OSError, UnicodeError) as error:
        print("Source inspection failed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
