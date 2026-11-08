# Official NCDB record acquisition

## Scope and preserved evidence

Fresh downloads were obtained directly from the Government of Canada Open Government catalog, dataset `1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a`. No originals were copied from sibling projects. The catalog request is preserved byte-for-byte in `data/raw/source_metadata/ncdb_catalog.json`, with its URL, actual UTC acquisition timestamp, byte size, and SHA-256 in `ncdb_catalog.provenance.json`. Acquisition began on October 17, 2026 in America/Edmonton (October 18 UTC); machine-readable timestamps use UTC.

The catalog snapshot contains 51 resources: bilingual annual files, overlapping historical CSV material, and one bilingual PDF dictionary. The complete resource inventory is `data/reference/record_source_inventory.csv`, including unselected candidates, language, publication/modification metadata, catalog validation flags, and selection rationale. Catalog dataset-level coverage ends in 2017 despite later resources being present; use verified file contents rather than that stale field to establish coverage.

There are 24 selected originals (23 annual files and the PDF), totaling 692,455,793 bytes, plus one 17,398,658-byte comparator CSV.

Selected originals and their hashes are in `data/sources.json`; the complete acquisition result is `data/reference/record_acquisition.json`. Each original has a separate provenance sidecar in `data/raw/source_metadata/<resource_id>.json` recording the original and resolved URLs, response headers, release metadata, timestamps, SHA-256, and observed size. Raw bytes remain unchanged. Versioned manifests redact transient query strings from resolved download redirects and omit response headers; canonical official resource URLs remain the primary references, while local raw provenance retains the acquisition evidence. A successful second acquisition run checked every selected SHA-256 against those sidecars.

## Selection and available coverage

The selection uses one explicit annual official release per year, covering catalog-listed 1999–2021, plus the linked dictionary. English annual XLSX files are used for 1999–2019; the workbook sheet is `in`. The English annual CSV is selected for 2020; the older 2019 English CSV is retained only as a comparator. The English 2021 resource exists in catalog metadata but has an empty download URL, so the available official French CSV is acquired instead. Its bytes are cp1252, not UTF-8; all 23 French headers must be explicitly mapped to verified English canonical equivalents during audit. Original strings, codes and leading zeros are preserved.

The 1999–2001 combined English CSV is excluded to avoid overlapping yearly observations. French duplicates are excluded where selected English annual files exist. Both 2019 releases were freshly acquired and fully audited. The older CSV, last modified in November 2022, has 272,301 rows and 105,782 distinct case IDs (1,623 fatal collisions and 104,159 injury collisions); the newer XLSX, last modified in June 2023, has 269,328 rows and 104,630 distinct case IDs (1,620 fatal and 103,010 injury collisions). Both releases have zero within-case collision-attribute conflicts and the same identified-person duplicate/conflict counts. There is no structural-quality winner. The newer official XLSX is selected on release recency, with the older CSV preserved as an explicit alternative. Do not combine their rows or explain the difference as missing records without further source evidence. The 1,152-case difference includes three fatal cases; these are release revisions of uncertain cause, not permission to force agreement with another publication.

The catalog's CSV/XLSX validation statuses are preserved as source metadata; they are not a substitute for parsing and auditing the actual files. Some annual workbooks have a source validation flag of `failure` despite successful download and valid XLSX containers.

No annual record release for 2022 or later appears in this catalog snapshot. Newer aggregate statistics or dashboard observations do not extend record-level training coverage. Neither the unpopulated English 2021 URL nor absent newer records should be silently replaced by inferred URLs or copies of older years.

## Dictionary and modeling implications

The matching catalog-linked bilingual `data_dictionary.pdf` is preserved unchanged. It documents 22 substantive fields; the actual records additionally contain a 23rd case identifier (`C_CASE`, or `C_CAS` in the 2021 French header). The dictionary does not define the semantics or uniqueness of that extra identifier; collision, vehicle and person key candidates therefore require empirical validation.

`C_SEV` defines 1 as a collision producing at least one fatality and 2 as a collision producing nonfatal injury, with U/X missingness categories. `P_ISEV` defines 1 no injury, 2 injury, 3 fatality, and N/U/X nonapplicable/unknown/not provided. An uninjured person in an injury-producing collision is not a no-collision observation. The dataset does not contain the general population of travel opportunities needed for absolute accident occurrence likelihood.

`P_USER` distinguishes motor vehicle driver, motor vehicle passenger, pedestrian, bicyclist, and motorcyclist (1–5), with U representing not stated/other/unknown. Preserve all road-user categories and report source gaps rather than interpreting the scope as a guarantee of complete reporting for every road user.

The 23-field record schema has no province, municipality, coordinates, full event date, or external weather join key. Month, weekday and hour support descriptive temporal patterns; road/weather categories support conditional severity and association analysis after leakage review. These records alone cannot support local hotspot maps, province-stratified evaluation, exact-date joins, or causal claims.

## Reproduction and integrity

Run from the project root:

```sh
python3 src/road_to_safety/acquire_records.py
```

The script uses only the Python standard library. Network access is needed on first acquisition. It pins and reuses the original catalog snapshot, verifies the pinned catalog and existing originals against their provenance checksums, refuses to overwrite an existing raw file without a sidecar, and exits nonzero if any selected resource is blocked. It uses bounded parallel public downloads and writes temporary `.part` files before completing an original. It does not accept a refresh flag that would overwrite the preserved catalog. A future source review should preserve a separate new catalog snapshot and explicitly review newly available years.

The source license is [Open Government Licence — Canada](https://open.canada.ca/en/open-government-licence-canada). Source metadata and resource URLs are evidence; descriptive counts, key validation, missingness, and final modeling eligibility are established separately in the full data-quality audit.
