#!/usr/bin/env python3
"""Validate the offline experimental V3 bundle and explicitly supplied records.

Exit 0 means the reported contract checks passed, never scientific approval.
This CLI intentionally has no identity-attestation import or release command.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path, PurePosixPath
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from agtxiv_v3.contracts import (
    ContractError, MAX_DOCUMENT_BYTES, RecordSet, SchemaBundle, SuppliedArtifact, parse,
)


def read_bytes(path: Path, *, maximum: int = MAX_DOCUMENT_BYTES) -> bytes:
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ContractError('Expected a regular non-symlink input: ' + str(path))
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ContractError('Input exceeds the configured byte limit: ' + str(path))
    return raw


def load_artifacts(path: Path) -> list[SuppliedArtifact]:
    manifest = parse(read_bytes(path))
    if not isinstance(manifest, list) or len(manifest) > 10000:
        raise ContractError('Artifact manifest must be a bounded JSON array')
    root = path.parent.resolve(strict=True)
    artifacts = []
    total = 0
    for item in manifest:
        if not isinstance(item, dict) or set(item) != {'artifact_id','media_type','path'}:
            raise ContractError('Each artifact location requires exactly artifact_id, media_type and path')
        if not all(isinstance(v,str) and v for v in item.values()):
            raise ContractError('Artifact manifest values must be nonempty strings')
        relative = PurePosixPath(item['path'])
        if relative.is_absolute() or any(p in {'.','..'} for p in item['path'].split('/')) or '\\' in item['path']:
            raise ContractError('Artifact path must stay below its manifest directory')
        file_path = root
        for part in relative.parts:
            file_path = file_path / part
            if file_path.is_symlink():
                raise ContractError('Artifact locator must not traverse a symlink')
        if not file_path.resolve(strict=True).is_relative_to(root):
            raise ContractError('Artifact locator escapes its manifest directory')
        raw = read_bytes(file_path, maximum=64*1024*1024)
        total += len(raw)
        if total > 256*1024*1024:
            raise ContractError('Supplied artifact set exceeds 256 MiB')
        artifacts.append(SuppliedArtifact(item['artifact_id'], item['media_type'], raw))
    return artifacts


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,default=ROOT/'schema v0.0')
    parser.add_argument('--bundle-only',action='store_true',help='Check schemas and all offline references only.')
    parser.add_argument('--records',type=Path,action='append',default=[],help='One JSON record or JSON array; repeat for more files.')
    parser.add_argument('--artifacts',type=Path,help='JSON array of explicit artifact locations, relative to this manifest.')
    parser.add_argument('--without-artifact-bytes',action='store_true',help='Report a weaker record-only check; raw artifact integrity stays unchecked.')
    args = parser.parse_args(argv)
    if args.bundle_only and (args.records or args.artifacts or args.without_artifact_bytes):
        parser.error('--bundle-only cannot be combined with record or artifact options')
    if not args.bundle_only and not args.records:
        parser.error('Provide --bundle-only or at least one --records file')
    try:
        bundle = SchemaBundle(args.bundle)
        if args.bundle_only:
            output = {'valid':True,'scope':'OFFLINE_SCHEMA_BUNDLE','record_types':len(bundle.by_type),
                'schema_bundle_hash':bundle.bundle_hash,'authority_checked':False,
                'scientific_acceptance':False}
        else:
            records = []
            for path in args.records:
                value = parse(read_bytes(path))
                records.extend(value if isinstance(value,list) else [value])
            artifacts = load_artifacts(args.artifacts) if args.artifacts else []
            report = RecordSet(bundle,records,artifacts).validate(require_artifacts=not args.without_artifact_bytes)
            output = {'valid':report.valid,**asdict(report),'schema_bundle_hash':bundle.bundle_hash,
                'scientific_acceptance':False}
    except (ContractError,OSError,KeyError,TypeError,ValueError) as error:
        output = {'valid':False,'scope':'SUPPLIED_RECORD_CONTRACTS','error':str(error),
            'authority_checked':False,'scientific_acceptance':False}
    print(json.dumps(output,ensure_ascii=True,indent=2))
    return 0 if output['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
