"""Fetch missing sources listed in data/sources.json and verify pinned hashes."""

import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen

from .build import sha256


def main():
    root = Path.cwd()
    sources = json.loads((root / "data/sources.json").read_text())
    for source in sources:
        path = root / source["path"]
        if path.exists():
            if source.get("sha256") and sha256(path) != source["sha256"]:
                raise ValueError(f"Existing source checksum mismatch: {path}")
            print(f"Present: {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix(path.suffix + ".part")
        try:
            request = Request(source["url"], headers={"User-Agent": "CanadianCollisionResearch/0.1"})
            with urlopen(request, timeout=120) as response, pending.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            if source.get("sha256") and sha256(pending) != source["sha256"]:
                raise ValueError(f"Downloaded source changed; review metadata and checksum: {path}")
            pending.replace(path)
            print(f"Downloaded: {path}")
        finally:
            pending.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
