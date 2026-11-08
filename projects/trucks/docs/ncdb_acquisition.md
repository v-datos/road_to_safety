# Official NCDB acquisition record

> **Initial acquisition log with subsequent source update.** This document preserves the first downloads. The active selection now uses validated annual 2014–2019 workbooks and selected legacy 1999–2013 records; the old 2019 CSV remains preserved. Additional resource IDs, exact URLs, metadata and SHA256 hashes are recorded in `data/sources.json`, [the release inventory](../data/reference/source_release_inventory.csv), and [the source repair](source_release_update.md). No earlier raw file was overwritten.

Retrieved 2026-10-15 UTC (2026-10-14 in America/Edmonton). Official originals are preserved in `data/raw/ncdb/`; files in `Collisions/` were not changed.

## Source and version

- Publisher: Transport Canada. Licence: Open Government Licence – Canada.
- Catalogue: https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a
- Metadata API: https://open.canada.ca/data/api/action/package_show?id=1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a
- Package metadata_modified: `2025-12-17T16:11:47.651332`; no explicit version is supplied. Complete API response is saved as `data/raw/ncdb/package_metadata.json`.
- `download_manifest.json` records actual acquisition timestamps, URL, resource ID, bytes, SHA256, resource modification metadata, and HTTP headers.
- Current package has 51 resources, with annual microdata resources through **2021**, and none for 2022 or later. This is a finding about downloadable public microdata, not the latest year in the NCDB online tabulator.
- The package-level coverage end still says 2017 and `date_modified` says 2022-02-23 despite later annual resources; rely on inspected files and resource metadata rather than that stale coverage field.

## Acquired files

|File|Reference period / language|Actual bytes|SHA256|
|---|---|---:|---|
|`2019_dataset_en.csv`|National Collision Database (2019); en|17,398,658|`d1d4fcc176b387281dadbf02b9e32890174e7e9e07f05961c54e5e7c4487a87c`|
|`data_dictionary.pdf`|National Collision Database - Data Dictionary; en, fr|385,704|`beef296c25eee70a55f747327b768b8da1bbdd428d02a9ca56ba781a7b6edb40`|
|`y_2018_en.xlsx`|National Collision Database (2018); en|25,786,257|`1ca01fa57a216d9d7187f0926cb4910dcff256517738639727e7a7a9d6bc2db1`|
|`y_2020.csv`|National Collision Database (2020); en|15,700,970|`2c81d99278819c28f99c02bfec319fb99c94b02734418300306e86a68ec3f83b`|
|`y_2021-fr.csv`|National Collision Database (2021); fr|16,149,978|`024a2d24cdaf6e30ec018433836075b83c626e7f8e189d14a46ea9d99b3d8dbb`|


Exact download URLs:

- [2019_dataset_en.csv](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/1e2a6aa0-c35f-4736-984a-71f2eac1c1dc/download/2019_dataset_en.csv)
- [data_dictionary.pdf](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/21eb7966-38da-4814-a80e-521bce6c4c27/download/data_dictionary.pdf)
- [y_2018_en.xlsx](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/bf937c33-6fc2-4010-8036-d91d4e1a6285/download/y_2018_en.xlsx)
- [y_2020.csv](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/2164b2a7-a580-4708-bdac-8ab0c1304bc2/download/y_2020.csv)
- [y_2021-fr.csv](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/f964d00f-6bba-44be-ae79-85f574d04a31/download/y_2021-fr.csv)

## Inspected schema and limitations

- **2018:** XLSX workbook opens as a valid ZIP/XML workbook, one sheet named `in`, range `A1:W285383` (285,382 data rows plus header). Header contains the standard 23 English NCDB column codes. Catalogue validation status is `failure`; this is retained as a source warning and must not be confused with a failed download. Actual file size matches the catalogue size. Dataset-level validation must determine usability.
- **2019:** English CSV has 272,301 data rows, all `C_YEAR=2019`, standard 23 English columns. The fresh file enables comparison with the existing local 2019 extract.
- **2020:** English CSV has 198,745 data rows, all `C_YEAR=2020`, standard 23 English columns. Numeric-looking codes are padded. `C_VEHS` contains `**` on 182 rows and `V_ID` contains `*` on 39 rows; retain these strings and audit rather than silently coercing them to numbers.
- **2021:** English resource `d86294f3-1acf-411c-a033-52f551ea85a6` exists in metadata but has **no URL**. The French resource is downloadable and contains 204,428 data rows, all year 2021. It uses Windows-1252 (CP1252) and translated column headers. Numeric, U/N/Q special codes, and M/F sex codes remain coded; headers require mapping.
- None of these public files supplies province, geolocation, fault, or complete driver contributing factors. Public NCDB casualty scope excludes property-damage-only collisions.
- These are records relating to people and vehicles, not pre-deduplicated collision rows. Key and collision-level field validation are required before analysis.

## 2021 French to English header mapping

Mapping is based on the 23 corresponding NCDB variables and their header meanings, with unchanged order. Preserve raw source columns in the original file.

|French header|Canonical English header|
|---|---|
|`C_ANNÉE`|`C_YEAR`|
|`C_MOIS`|`C_MNTH`|
|`C_JSEM`|`C_WDAY`|
|`C_HEURE`|`C_HOUR`|
|`C_GRAVITÉ`|`C_SEV`|
|`C_VÉH`|`C_VEHS`|
|`C_CFG`|`C_CONF`|
|`C_CFGR`|`C_RCFG`|
|`C_MÉTEO`|`C_WTHR`|
|`C_ÉCHSÉ`|`C_RSUR`|
|`C_TRAR`|`C_RALN`|
|`C_CIRC`|`C_TRAF`|
|`V_ID`|`V_ID`|
|`V_TYPE`|`V_TYPE`|
|`V_ANNÉE`|`V_YEAR`|
|`P_ID`|`P_ID`|
|`P_SEXE`|`P_SEX`|
|`P_ÂGE`|`P_AGE`|
|`P_LOCP`|`P_PSN`|
|`P_ISEV`|`P_ISEV`|
|`P_SÉCURITÉ`|`P_SAFE`|
|`P_USAG`|`P_USER`|
|`C_CAS`|`C_CASE`|

## Additional 2019 language-version check

Downloaded the official [2019 French CSV](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/a21d391f-5c08-493f-a1dd-c6ab6202e11b/download/2019_dataset_fr.csv) on 2026-10-15 UTC as `data/raw/ncdb/2019_dataset_fr.csv`. It is 17,398,670 bytes, SHA256 `9397c91682673cd5ce6d4fa4022263b7c8ee8845d7b23724373f4fdf16a85183`; metadata last_modified is `2022-11-02T18:07:29.849702`. Complete details were appended to `download_manifest.json`.

It uses CP1252 with the same French header mapping as the 2021 file. After excluding the translated header, all **272,301 row records match the English 2019 CSV exactly in the same order**. Independent filtering for V_TYPE=08 and deduplicating (year, case ID) finds **2,871** observed tractor collisions: **192 fatal** and **2,679 injury**. The language version therefore does not resolve the published 2019 difference. This additional file is an audit input; it is not selected as a second source for the dataset.

## Open Government portal recheck — 2026-10-15 local

Rechecked the user-supplied [DataStore-enabled search](https://search.open.canada.ca/opendata/?datastore_enabled=True&page=1&sort=metadata_modified+desc). The web reader could not render the search page, so the official catalogue API was used directly. The unrestricted searches for the English dataset title, `NCDB`, and the French title each returned the same single NCDB package. A Transport Canada collision search returned that package and Canadian Vehicle Specifications; no separate newer national collision package was identified.

The live [package metadata API](https://open.canada.ca/data/api/action/package_show?id=1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) still lists **51 resources** and package modification `2025-12-17T16:11:47.651332`. All resource names and URLs were inspected: annual record resources end at **2021**, with none for 2022–2025. A metadata modification date is not a collision reference year.

Four resources are DataStore active: English 1999–2001, English and French 2020, and French 2021. The latest [2021 French resource](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/f964d00f-6bba-44be-ae79-85f574d04a31) has **204,428 records** in the live DataStore. A distinct `C_ANNEE` query returns **2021 only**. Its stored field names are unaccented French (`C_ANNEE`, etc.), unlike the raw CSV headers. No schema substitution or production rebuild was performed. The SQL endpoint returned HTTP400; the supported `datastore_search` endpoint successfully verified distinct years.

The DataStore filter limits results to indexed resources; unrestricted catalogue search was also performed to include downloadable files without DataStore indexing. It did not reveal a newer NCDB annual file. This is evidence about the current public catalogue, not proof that Transport Canada lacks later internal records. NCDB Online separately offers aggregate vehicle-involvement/occupant tables through 2023.

Complete catalogue responses, resource lists, search responses and DataStore checks are preserved separately under `data/raw/ncdb/portal_recheck_20261015/`; earlier metadata snapshots and selected input files were not overwritten. The downloadable event-data gap for 2022–2025 remains unresolved. No contact or outreach was performed.
