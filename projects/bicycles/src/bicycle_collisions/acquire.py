"""Acquire the pinned public record releases; optionally copy existing originals."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-project', type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    sources = json.loads((root/'data/sources.json').read_text())
    sources.append(dict(id='dictionary', path='data/raw/ncdb/data_dictionary.pdf',
        existing_project_path='data/raw/ncdb/data_dictionary.pdf',
        url='https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/21eb7966-38da-4814-a80e-521bce6c4c27/download/data_dictionary.pdf',
        sha256='beef296c25eee70a55f747327b768b8da1bbdd428d02a9ca56ba781a7b6edb40'))
    manifest_path = root/'data/raw/ncdb/acquisition.json'
    acquired = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    for source in sources:
        target = root/source['path']
        if target.exists():
            if sha256(target) != source['sha256']:
                raise ValueError(f'Existing file checksum mismatch: {target}')
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        pending = target.with_suffix(target.suffix+'.part')
        try:
            if args.from_project:
                original = args.from_project/source['existing_project_path']
                if sha256(original) != source['sha256']:
                    raise ValueError(f'Original checksum mismatch: {original}')
                shutil.copyfile(original, pending)
                method = 'Copied original bytes from an existing local project; original acquisition metadata retained in source manifest.'
            else:
                with urlopen(Request(source['url'], headers={'User-Agent':'CanadianBicycleCollisionResearch/0.1'}), timeout=120) as response, pending.open('wb') as out:
                    shutil.copyfileobj(response, out)
                method = 'Downloaded pinned public source URL.'
            if sha256(pending) != source['sha256']:
                raise ValueError(f'Source changed: {target}')
            pending.replace(target)
            acquired.append(dict(id=source['id'], path=source['path'], url=source['url'],
                sha256=source['sha256'], size_bytes=target.stat().st_size,
                acquired_at=datetime.now(timezone.utc).isoformat(), method=method))
            manifest_path.write_text(json.dumps(acquired, indent=2)+'\n')
            print(f'Acquired {target.name}', flush=True)
        finally:
            pending.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
