# Data staging

The inherited source files in `../Collisions/` are unchanged. Official 2018–2021 originals are in `raw/ncdb/`, along with acquisition metadata and a dictionary. `sources.json` selects exactly one input for each year and pins its checksum. `reference/` contains the published tractor-trailer collision benchmark and its source citation.

`derived/ncdb/` contains one-row-per-collision Parquet tables, the observed tractor subset in Parquet/CSV, a strict sensitivity subset, source hashes and quality/reconciliation tables. Raw and derived files are ignored by Git. See [the dataset contract](../docs/dataset_contract.md), [validation findings](../docs/dataset_validation.md), and [acquisition notes](../docs/ncdb_acquisition.md).
