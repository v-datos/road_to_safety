# Bicycle project data

All paths are relative to `projects/bicycles/`.

| Location | Current contents | Git |
| --- | --- | --- |
| `raw/ncdb/` | Nine preserved record sources, dictionary, byte-copy acquisition metadata | Ignored |
| `raw/ncdb_online/` | Archived visible table matrices/text for 2010–2023 queries, including separately retained exploratory captures | Ignored |
| `derived/` | Linked records/events/vehicles/people, quality evidence, build database and reviewed report snapshot | Ignored |
| `reference/` | Normalized public online aggregates, acquisition metadata and revised-publication benchmark | Versioned |
| `sources.json` | Selected annual record inputs and pinned hashes; one release per year 2010–2021 | Versioned |
| `source_catalog.json` | Source roles and current acquisition status | Versioned |

The initial record acquisition copied the original files already preserved by the truck project into bicycle-owned paths. Every copy was checksum-verified and no truck-derived table was used as analytical input. Original provenance and original acquisition dates remain distinct from the new copy timestamp. Reacquisition without a local copy uses the pinned official download URLs.

Record headers, physical year coverage and source selection were independently checked for this bicycle build. `build.py` converts XLSX files in temporary staging, translates French column names, preserves code strings, selects bicycle events and retains all linked road users. Original bytes are unchanged.

Online acquisition used the visible table DOM through the four-step browser wizard. The native CSV download timed out. The selected complete matrices are listed by dataset and hash in `reference/ncdb_online_bicycles_2010_2023.metadata.json`; earlier known-age-only and vehicle-context demographic captures are retained for audit but excluded. The normalized CSV is a programmatic transformation of captured cells, not a native download or manually typed series.

The revised-publication benchmark was read and transcribed from Transport Canada's 2024 report, using its 2020–2023 bicyclist column only. Each row carries release, revision status, access date and direct URL. It is a comparison source, not a replacement for online values.

See [the data contract](../docs/data_contract.md) for actual grains and [validation](../docs/validation.md) for unresolved source differences. No 2022–2023 event records or exposure denominators have been fabricated.
