# Data and provenance

Acquisition and full-file feasibility audit are complete for **23 selected official annual inputs (1999–2021)**, the official dictionary, a separate 2019 comparison release and aggregate evidence. [source_catalog.json](source_catalog.json) records source roles and remaining gaps; [sources.json](sources.json) pins record originals. Read the [verified inventory](../docs/source_inventory.md) and [quality assessment](../docs/data_quality_assessment.md). Paths here are project-relative. Collision-level preparation is now validated; see the [preparation report](../docs/preparation_validation.md).

| Directory | Purpose | Versioning |
| --- | --- | --- |
| `data/raw/ncdb/` | Exact official record originals and bilingual dictionary | Ignored; retain manifest fingerprints |
| `data/raw/source_metadata/` | Original catalog snapshot and record provenance sidecars | Ignored; selected metadata/hashes retained in manifests |
| `data/raw/aggregates/` | Original HTTP captures and detailed provenance | Ignored; captures and source errors distinguished |
| `data/derived/` | Collision/exception Parquet files, preparation manifest, source audit and independent validation receipt | Ignored |
| `data/reference/` | Catalog/asset inventories, acquisition reports and aggregate extracts | Version small text/CSV/JSON with source lineage |

## Selection and preservation

- One explicit annual release supplies each selected year: English XLSX 1999–2019, English CSV 2020, French CSV 2021. The English 2021 catalog URL is empty. Preserve source language and encoding; do not rewrite originals while translating headers.
- The older 2019 CSV is an alternative only. Both releases are preserved and profiled, but never pooled.
- The dictionary is `data/raw/ncdb/data_dictionary.pdf`. It defines 22 substantive fields; observed case IDs and asterisk-code meanings need additional documentation.
- Original URLs/resource IDs, release metadata, acquisition timestamps, byte sizes, SHA-256, encodings/sheets and selected years are retained. Signed redirect query strings and session state are excluded from versioned inventories; detailed acquisition evidence stays local.
- Acquisition reruns verify existing bytes and refuse accidental overwrite. A new release needs a separate catalog/capture snapshot and reviewed selection. A matching checksum establishes byte identity, not national reporting completeness.

## Coverage and aggregate limits

Selected records cover 1999–2021. NCDB Online selector years are 1999–2023, but no numeric query export was obtained. Dashboard text covers 2014–2023; the acquired publication's annual series covers 2005–2024. These related views share NCDB lineage and are not independent observations to stack together.

The aggregate CSVs are reproducible extracts of archived official HTML, not native agency CSV downloads. Preserve measure, counting unit, filters/grouping, source vintage and footnotes. The dashboard road-user injury margin and cross-vintage record/publication discrepancies remain unresolved.

The [consolidated asset inventory](reference/verified_source_inventory.csv), [aggregate registry](reference/aggregate_sources.json) and record manifest retain inspectable fingerprints. [quality_audit.json](derived/quality_audit.json) is local generated evidence. The [project README](../README.md) gives tested acquisition, audit and verification commands.
