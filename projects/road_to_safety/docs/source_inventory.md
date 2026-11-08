# Verified source inventory

Acquisition/audit date: October 17, 2026, America/Edmonton. Original machine timestamps are UTC. This project acquired its inputs directly from official sources; no original datasets were copied from the truck or bicycle projects.

## Source roles and verified coverage

| Input | Coverage and unit | Preserved evidence | Intended use and limits |
| --- | --- | --- | --- |
| Official annual NCDB records | 23 selected annual files, 1999–2021; source records repeat collision attributes across vehicle/person involvements | [Selected manifest](../data/sources.json), [complete catalog resource inventory](../data/reference/record_source_inventory.csv), original files and provenance sidecars | Candidate collision severity and condition/temporal analysis after preparation. Source rows are not unique collisions or necessarily identified people. |
| Official bilingual NCDB dictionary | Definitions for 22 substantive coded fields; case ID is an additional observed column | Original PDF, source URL, release metadata and SHA-256 in the selected manifest | Confirms severity and road-user categories. Case-ID semantics/uniqueness require empirical checks. |
| Older 2019 CSV comparator | Same nominal year as the selected newer 2019 workbook, with different contents | `alternatives` in the selected manifest; both exact originals retained | Release sensitivity and reconciliation only; never add both releases to the selected analysis population. |
| NCDB Online | Verified selector year domain 1999–2023; national counts with distinct collision/vehicle/person measures | [Aggregate registry](../data/reference/aggregate_sources.json), original selector/help/error HTTP responses | Query/export capability inspection completed. No numeric query table or native export was obtained in this session. Error responses are acquisition evidence, not data. |
| Motor Vehicle Casualties Dashboard text | 2014–2023; seven separate marginal distributions for each of fatalities and injuries | Archived official HTML; [normalized margins](../data/reference/aggregate_dashboard_margins_2014_2023.csv) and full HTML-cell extract | Temporal/demographic descriptions; road-user injury margin has a reconciliation failure. Text captures are distinct from an unverified live Power BI view/export. |
| Statistics index and 2024 publication | National annual series 2005–2024; collisions and person casualties are separate measures | Archived index/publication HTML; [annual table](../data/reference/aggregate_national_annual_2024_vintage.csv), complete cell extract | National descriptive context and separately scoped benchmark comparisons; publication coverage does not extend microdata training years. |
| 2024 provincial/territorial casualty rates | Canada plus 13 provinces/territories; six published casualty-rate measures | [Geographic rates](../data/reference/aggregate_jurisdiction_rates_2024.csv) linked to the archived publication | Province/territory maps after acquiring boundaries and validating joins. Rounded rates, estimates, preliminary data and reporting changes require qualifications. No incident coordinates or hotspots. |

The three supplied entry points are related views and publications of NCDB information. Agreement can help reconciliation; they are not independent datasets to stack into a larger training sample.

## Original-file selection and preservation

The catalog snapshot contains **51 resources**, all listed in the catalog inventory with selection status. The selected set is **23 annual inputs plus one dictionary**. A further **one alternative release** is preserved for 2019. The 25 downloaded record/dictionary/comparator originals total **709,854,451 bytes**. The selected subset accounts for 692,455,793 bytes; the comparator accounts for 17,398,658 bytes.

Selection uses the explicit annual English XLSX releases for 1999–2019, the English 2020 CSV, and the French 2021 CSV. The English 2021 catalog entry has an empty URL. French headers are mapped explicitly after cp1252 decoding; the original is unchanged. Overlapping combined files and language duplicates remain catalogued but unselected. The catalog lists no annual 2022+ record release in the preserved snapshot.

The newer 2019 workbook is selected based on release recency, with its unresolved revision difference retained. It contains 269,328 source rows and 104,630 candidate events, versus 272,301 rows and 105,782 candidate events in the older CSV. Both passed the collision-attribute consistency checks; the audit did not establish a structural winner or authority over every other official publication. See [record acquisition](record_acquisition.md) and [data quality](data_quality_assessment.md).

The aggregate acquisition preserved **15 original HTTP responses** and produced **five derived CSV extracts**. The CSVs are reproducible HTML-table extracts, not native agency CSV downloads. Complete query/response provenance is saved locally; the versioned registry excludes transient session cookies, signed redirect query strings and ASP.NET state.

## Machine-readable verification

| Artifact | Meaning |
| --- | --- |
| [data/sources.json](../data/sources.json) | Selected originals and the comparison release, canonical resource URLs/IDs, language/encoding/sheet, selected years, timestamps, sizes and SHA-256 |
| [record_source_inventory.csv](../data/reference/record_source_inventory.csv) | All catalog resources, including unselected/empty-URL candidates and source metadata flags |
| [record_acquisition.json](../data/reference/record_acquisition.json) | Acquisition results and access/coverage gaps |
| [aggregate_sources.json](../data/reference/aggregate_sources.json) | HTTP originals, hash-linked provenance, extracted-table lineage, query scope and aggregate checks |
| [verified_source_inventory.csv](../data/reference/verified_source_inventory.csv) | Consolidated integrity-checked inventory of originals, catalog capture, HTTP captures and derived extracts; status distinguishes source errors from successful captures |
| [quality_audit.json](../data/derived/quality_audit.json) | Local full-file audit evidence, input/code fingerprints, runtime and field profiles; raw/derived files are intentionally ignored by Git |
| [source_benchmark_comparison.csv](../reports/tables/source_benchmark_comparison.csv) | Selected event counts against the separately scoped 2024 publication vintage; differences remain unresolved rather than overwritten |

Preserved catalog and raw files are immutable inputs. Acquisition reruns verify hashes; they refuse orphaned raw files or accidental replacement of an existing capture registry. A new source release needs a separately preserved snapshot and reviewed selection. Successful byte verification establishes reproducibility of the captured release, not its completeness or agreement with a later publication.

## Feasibility handoff

- **Collision severity:** Labels and records exist for 1999–2021. Prepare one validated observation per collision, retain quality flags and prevent outcome leakage before training.
- **Risk factors and temporal patterns:** The records support condition/time analysis; publication and dashboard aggregates provide separately scoped descriptive evidence. Counts, conditional severity proportions and exposure rates must remain distinct.
- **Maps:** Published provincial/territorial rates supply a geographic series. Boundary geometry and a validated name/code join are still needed. The records and NCDB Online do not supply point/road-segment location.
- **Accident likelihood:** The acquired inputs do not supply a complete exposure/non-accident observation frame. This remains the second modeling phase and requires additional sources.

The detailed [data-quality assessment](data_quality_assessment.md) identifies source and record-level limitations; the [aggregate audit](aggregate_source_audit.md) records the export failure, dashboard discrepancy, publication revisions and denominator caveats.
