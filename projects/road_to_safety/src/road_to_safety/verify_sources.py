"""Verify preserved inputs and regenerate the consolidated source inventory."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def verify(root=ROOT):
    root = Path(root)
    records = json.loads((root / "data/sources.json").read_text())
    aggregates = json.loads((root / "data/reference/aggregate_sources.json").read_text())
    assets = []

    def add(kind, entry, path, url, identifier, years="", language=""):
        absolute = root / path
        actual_hash = digest(absolute)
        if actual_hash != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {path}")
        size = absolute.stat().st_size
        expected_size = entry.get("size_bytes", entry.get("bytes", size))
        if size != expected_size:
            raise ValueError(f"Size mismatch: {path}")
        assets.append({
            "asset_type": kind, "source_id": identifier, "path": path,
            "source_url": url, "selected_years": years, "language": language,
            "acquisition_status": entry.get("status", entry.get("type", "captured")),
            "bytes": size, "sha256": actual_hash,
            "acquired_at_utc": entry.get("acquired_at_utc", ""),
        })

    catalog = json.loads((root / "data/raw/source_metadata/ncdb_catalog.provenance.json").read_text())
    add("catalog_snapshot", catalog, "data/raw/source_metadata/ncdb_catalog.json",
        catalog["url"], records["catalog_id"])
    for kind, entries in (("selected_record_or_dictionary", records["resources"]),
                          ("comparison_release", records.get("alternatives", []))):
        for entry in entries:
            if entry["status"] != "acquired":
                raise ValueError(f"Unacquired selected input: {entry['local_path']}")
            add(kind, entry, entry["local_path"], entry["url"], entry["resource_id"],
                ";".join(map(str, entry.get("selected_years", []))), entry["language"])
    for entry in aggregates["sources"]:
        add("http_capture", entry, entry["path"], entry["source_url"], entry["id"])
        if digest(root / entry["provenance_path"]) != entry["provenance_sha256"]:
            raise ValueError(f"Capture provenance mismatch: {entry['path']}")
    for entry in aggregates["extracts"]:
        if digest(root / entry["derived_from"]) != entry["source_sha256"]:
            raise ValueError(f"Extract parent mismatch: {entry['path']}")
        add("aggregate_extract", entry, entry["path"], "", entry["derived_from"])
    paths = [entry["path"] for entry in assets]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate paths in consolidated source inventory")
    selected_years = [year for entry in records["resources"] for year in entry.get("selected_years", [])]
    if len(selected_years) != len(set(selected_years)):
        raise ValueError("Overlapping selected record years")
    target = root / "data/reference/verified_source_inventory.csv"
    with target.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(assets[0]))
        writer.writeheader()
        writer.writerows(sorted(assets, key=lambda entry: (entry["asset_type"], entry["path"])))
    print(f"Verified {len(assets)} preserved inputs/extracts; unique record years "
          f"{min(selected_years)}–{max(selected_years)}. Inventory: {target}")
    return assets


def compare_benchmarks(root=ROOT):
    """Compare event counts to a separately scoped publication; retain differences."""
    root = Path(root)
    manifest = json.loads((root / "data/sources.json").read_text())
    selected = {(entry["year"], entry["local_path"]) for entry in manifest["resources"]
                if entry.get("year") is not None}
    with (root / "reports/tables/record_annual_quality.csv").open() as stream:
        audited = [row for row in csv.DictReader(stream) if row["selected"] == "True"]
    if len(audited) != len(selected) or {(int(row["year"]), row["source_path"]) for row in audited} != selected:
        raise ValueError("Full selected-file quality audit must finish before benchmark reconciliation")
    records = {int(row["year"]): row for row in audited}
    with (root / "data/reference/aggregate_national_annual_2024_vintage.csv").open() as stream:
        published = list(csv.DictReader(stream))
    rows = []
    for reference in published:
        year = int(reference["year"])
        if year not in records:
            continue
        for measure in ("fatal_collisions", "injury_collisions"):
            observed = int(records[year][measure])
            benchmark = int(reference[measure])
            rows.append({
                "year": year, "measure": measure,
                "record_source_path": records[year]["source_path"],
                "record_count": observed, "published_2024_vintage_count": benchmark,
                "difference": observed - benchmark,
                "status": "equal" if observed == benchmark else "unresolved_difference",
            })
    target = root / "reports/tables/source_benchmark_comparison.csv"
    with target.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Compared {len(rows)} year/measure pairs: "
          f"{sum(row['status'] != 'equal' for row in rows)} unresolved differences retained.")
    return rows


if __name__ == "__main__":
    verify()
    compare_benchmarks()
