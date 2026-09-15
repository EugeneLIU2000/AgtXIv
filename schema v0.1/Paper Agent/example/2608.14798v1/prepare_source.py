"""Safely retain the requested arXiv source; never compile or execute it."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import shutil
import tarfile
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[4]
DEST = REPO / 'Reference' / 'Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States'
ARCHIVE = Path('/private/tmp/agtxiv-2608.14798v1-source.tar')

def main():
    if DEST.exists():
        raise SystemExit('Refusing to overwrite an existing source directory')
    with tarfile.open(ARCHIVE, 'r:*') as archive:
        members = archive.getmembers()
        names = set()
        total = 0
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isdir() or member.isfile()):
                raise ValueError('Unsafe archive member: ' + member.name)
            if member.name in names:
                raise ValueError('Duplicate archive member')
            names.add(member.name)
            total += member.size
        if len(members) > 1000 or total > 100 * 1024 * 1024:
            raise ValueError('Archive exceeds extraction limits')
        DEST.mkdir(parents=True)
        shutil.copyfile(ARCHIVE, DEST / 'source-v1.tar.gz')
        source = DEST / 'source'
        source.mkdir()
        for member in members:
            target = source.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as src, target.open('xb') as out:
                    shutil.copyfileobj(src, out)
    manifest = {
        'arxiv_id': '2608.14798v1',
        'source_url': 'https://arxiv.org/src/2608.14798v1',
        'recorded_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'archive_sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        'archive_bytes': ARCHIVE.stat().st_size,
        'source_directory': str(source.relative_to(REPO)),
        'files': [{'path': str(p.relative_to(source)), 'bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in sorted(source.rglob('*')) if p.is_file()],
        'source_execution': 'NOT_EXECUTED',
    }
    (Path(__file__).parent / 'acquisition.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
