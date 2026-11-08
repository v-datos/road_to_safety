"""Acquire official NCDB originals; reruns verify saved files without overwriting them."""
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit, urlunsplit
import sys

ROOT = Path(__file__).resolve().parents[2]
CATALOG_URL = "https://open.canada.ca/data/api/action/package_show?id=1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a"


def utc():
    return datetime.now(timezone.utc).isoformat()


def acquire(resource):
    target = ROOT / resource["local_path"]
    sidecar = ROOT / "data/raw/source_metadata" / (resource["resource_id"] + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and sidecar.exists():
        saved = json.loads(sidecar.read_text())
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != saved["sha256"]:
            raise ValueError(f"Checksum mismatch: {target}")
        return dict(saved, **{key: resource[key] for key in ("encoding", "sheet", "selected_years", "selected", "selection_reason", "resource_date_published", "resource_last_modified", "resource_metadata_modified") if key in resource})
    if target.exists():
        raise ValueError(f"Existing raw file lacks provenance sidecar; refusing overwrite: {target}")
    try:
        acquired = utc()
        with urllib.request.urlopen(resource["url"], timeout=180) as response:
            headers = dict(response.headers.items())
            final_url = response.url
            temporary = target.with_suffix(target.suffix + ".part")
            digest = hashlib.sha256()
            size = 0
            with temporary.open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
                    digest.update(block)
                    size += len(block)
        temporary.replace(target)
        saved = dict(resource, status="acquired", acquired_at_utc=acquired,
                     completed_at_utc=utc(), sha256=digest.hexdigest(), size_bytes=size,
                     final_url=final_url, response_headers=headers)
        sidecar.write_text(json.dumps(saved, indent=2) + "\n")
        print(f"acquired {target.name}: {size:,} bytes", flush=True)
        return saved
    except Exception as error:
        print(f"blocked {resource['resource_id']}: {error}", flush=True)
        return dict(resource, status="blocked", attempted_at_utc=utc(), error=str(error))


def main():
    metadata_path = ROOT / "data/raw/source_metadata/ncdb_catalog.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    if not metadata_path.exists():
        with urllib.request.urlopen(CATALOG_URL, timeout=60) as response:
            original = response.read()
            metadata_path.write_bytes(original)
        (metadata_path.with_suffix(".provenance.json")).write_text(json.dumps({
            "url": CATALOG_URL, "acquired_at_utc": utc(), "size_bytes": len(original),
            "sha256": hashlib.sha256(original).hexdigest()}, indent=2) + "\n")
    catalog_provenance = json.loads(metadata_path.with_suffix(".provenance.json").read_text())
    if hashlib.sha256(metadata_path.read_bytes()).hexdigest() != catalog_provenance["sha256"]:
        raise ValueError("Catalog snapshot checksum mismatch")
    catalog = json.loads(metadata_path.read_text())["result"]
    selected = []
    alternatives = []
    inventory = []
    for resource in catalog["resources"]:
        year_match = re.search(r"\((\d{4})\)", resource["name"])
        year = int(year_match[1]) if year_match else None
        selected_reason = ""
        if resource["format"] == "PDF":
            selected_reason = "Official bilingual dictionary linked from the same catalog"
        elif year and 1999 <= year <= 2019 and resource["format"] == "XLSX" and resource["language"] == ["en"]:
            selected_reason = ("Newer 2023 annual XLSX release; both 2019 releases pass structural checks but totals differ" if year == 2019 else "Explicit annual release; avoids overlapping legacy combined file")
        elif year == 2020 and resource["format"] == "CSV" and resource["language"] == ["en"]:
            selected_reason = "Official annual English CSV"
        elif year == 2021 and resource["language"] == ["fr"] and resource["url"]:
            selected_reason = "English resource has empty URL; French annual CSV retained for schema audit"
        entry = dict(resource_id=resource["id"], name=resource["name"], year=year,
                     format=resource["format"], language=",".join(resource["language"]),
                     url=resource["url"], selected=bool(selected_reason), selection_reason=selected_reason,
                     resource_date_published=resource.get("date_published"),
                     resource_last_modified=resource.get("last_modified"),
                     resource_metadata_modified=resource.get("metadata_modified"),
                     catalog_validation_status=resource.get("validation_status"),
                     catalog_size_bytes=resource.get("size"))
        inventory.append(entry)
        comparator = year == 2019 and resource["format"] == "CSV" and resource["language"] == ["en"]
        if comparator:
            entry["selection_reason"] = "Older 2022 release retained as audit comparator; do not pool with selected 2019 XLSX"
        if selected_reason or comparator:
            entry["local_path"] = "data/raw/ncdb/" + resource["url"].rsplit("/", 1)[1]
            entry["expected_years"] = [year] if year else []
            entry["selected_years"] = entry["expected_years"]
            entry["encoding"] = ("cp1252" if year == 2021 else "utf-8") if resource["format"] == "CSV" else None
            entry["sheet"] = "in" if resource["format"] == "XLSX" else None
            (alternatives if comparator else selected).append(entry.copy())
    manifest = dict(catalog_url=CATALOG_URL, catalog_id=catalog["id"],
                    catalog_metadata_modified=catalog["metadata_modified"],
                    license_url=catalog["license_url"],
                    selection_policy="One explicit official annual release per year; no language duplicates or overlapping combined files",
                    resources=selected)
    (ROOT / "data/sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with (ROOT / "data/reference/record_source_inventory.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(inventory[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(inventory)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(acquire, selected + alternatives))
    for result in results:
        if "final_url" in result:
            parts = urlsplit(result["final_url"])
            result["final_url"] = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
            result["redirect_query_redacted"] = bool(parts.query)
            result.pop("response_headers", None)
    selected_results = [result for result in results if result["resource_id"] in {entry["resource_id"] for entry in selected}]
    alternative_results = [result for result in results if result not in selected_results]
    report = dict(completed_at_utc=utc(), resources=selected_results, alternatives=alternative_results,
                  known_access_gaps=["English 2021 catalog resource has an empty URL; French release selected",
                                     "No 2022 or newer annual records listed in this catalog snapshot"])
    (ROOT / "data/reference/record_acquisition.json").write_text(json.dumps(report, indent=2) + "\n")
    manifest["resources"] = selected_results
    manifest["alternatives"] = alternative_results
    manifest["catalog_snapshot_note"] = "Pinned original catalog snapshot; discover newer releases through a separately preserved catalog snapshot and reviewed selection."
    (ROOT / "data/sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"acquired": sum(r["status"] == "acquired" for r in results),
                      "blocked": sum(r["status"] != "acquired" for r in results)}))
    if any(r["status"] != "acquired" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
