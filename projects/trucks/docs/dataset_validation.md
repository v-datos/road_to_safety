# Collision dataset validation

Final promoted-source build snapshot: **2026-10-15T16:37:22.666521+00:00**. Pipeline SHA-256 `aa6e36e1d7e54b64b02db9c0384c20ca61e929abe8ceed0673bb90404f2463bc`; DuckDB 1.5.6. This document describes the **nine-source production rebuild**, not the earlier CSV-only 2019 baseline or an intermediate candidate run. Machine-readable evidence is `data/derived/ncdb/validation.json`; source hashes and physical/selected coverage are in its source manifest.

## Delivered data

The selected inputs contain **7,729,886 person/placeholder record rows**, yielding **2,949,846 unique collision events for 1999–2021**. Every calendar year is present. Source-scoped event keys are `(source_id,C_YEAR,C_CASE)`; `(C_YEAR,C_CASE)` is additionally unique because exactly one release supplies each selected year. No invalid case/year rows were found. This does not establish that case IDs are stable across releases.

There are **80,540 observed road-tractor collisions** (`V_TYPE=08`). The strict sensitivity subset has **80,529 events**, excluding 11 flagged events. The primary table retains the flagged events; the strict view is not a corrected national total.

| Selected source | Input rows | Collision keys |
| --- | ---: | ---: |
| `ncdb_1999_2017_legacy` | 5,563,447 | 2,101,727 |
| `ncdb_2014_official_xlsx` | 300,431 | 116,292 |
| `ncdb_2015_official_xlsx` | 312,042 | 119,550 |
| `ncdb_2016_official_xlsx` | 306,260 | 118,321 |
| `ncdb_2017_official_xlsx` | 289,823 | 114,412 |
| `ncdb_2018_official` | 285,382 | 111,334 |
| `ncdb_2019_official_xlsx` | 269,328 | 104,630 |
| `ncdb_2020_official` | 198,745 | 79,990 |
| `ncdb_2021_official_fr` | 204,428 | 83,590 |

The physical inherited CSV still covers 1999–2017; only its **1999–2013** rows are selected. Annual 2014–2019 English XLSX and 2020 English/2021 French CSV supply the other years. Raw inputs were not edited or combined across releases. Full source-choice evidence and candidate checks are in [the source release audit](source_release_audit.md) and [source revision validation](source_revision_validation.md).

Files:

- `data/derived/ncdb/collisions.parquet`: all observed collision events and flags.
- `road_tractor_collisions.parquet` and `.csv`: all observed tractor-involved events.
- `road_tractor_collisions_strict.parquet`: sensitivity subset.
- `annual_counts.csv`, `reconciliation.csv`, `quality_by_year.csv`, code profiles, issue Parquet files, `source_manifest.json` and `validation.json`: audit evidence in the same directory.
- `notebooks/01_dataset_validation.ipynb`: runnable audit companion.

## External reconciliation

This comparison uses **unfiltered observed unique tractor collisions**, separately by fatal/injury severity, against [Transport Canada Table 1](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021). Strict exclusions are shown separately. Vehicle involvements, occupant casualties and broad commercial-vehicle totals are different counting units; they cannot repair this series. Source counts are never modified to fit a benchmark.

| Year | Observed fatal | Published fatal | Observed injury | Published injury | Strict exclusions | Source comparison |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2012 | 197 | 197 | 3,103 | 3,103 | 0 | exact match |
| 2013 | 195 | 195 | 3,148 | 3,150 | 1 | unresolved difference |
| 2014 | 211 | 211 | 3,216 | 3,216 | 1 | exact match |
| 2015 | 194 | 194 | 2,881 | 2,881 | 0 | exact match |
| 2016 | 193 | 193 | 2,817 | 2,817 | 0 | exact match |
| 2017 | 216 | 216 | 2,962 | 2,962 | 2 | exact match |
| 2018 | 190 | 190 | 2,800 | 2,800 | 0 | exact match |
| 2019 | 196 | 196 | 2,579 | 2,581 | 0 | unresolved difference |
| 2020 | 158 | 158 | 1,964 | 1,964 | 6 | exact match |
| 2021 | 169 | 169 | 2,107 | 2,107 | 1 | exact match |

Eight of the ten benchmark years match both observed severity counts. **2013 and 2019 each remain two injury collisions below the publication**; all ten fatal counts match. Years before 2012 have no tractor-event benchmark in this package.

The 2012–2013 annual workbooks have the same normalized record multisets as the selected inherited years. The 2013 difference therefore survives that alternate-source check. Annual 2014–2017 files have substantive changes and passed separate collision/person checks before promotion. Their benchmark agreement is a validation result, not the selection rule.

For historical comparison only, the earlier 2019 CSV yielded 192 fatal plus 2,679 injury tractor collisions (2,871 total). The promoted XLSX yields 196 plus 2,579 (2,775 total), versus published 196 plus 2,581. Source-version differences explain most of the earlier discrepancy; the final two-event injury difference has no established cause. Neither the later catalogue timestamp nor closer agreement proves that the XLSX was the exact publication extract or a formally designated final release. Earlier baseline artifacts and hashes remain preserved; see [source revision validation](source_revision_validation.md).

## Internal findings and impact

- **Localized event-field conflicts:** three 2020 events have contradictory `C_VEHS` values. Their vehicle-count field is null in the event table and alternatives remain in `collision_attribute_conflicts.parquet`. Two events are non-tractor and one tractor-involved. The validation field `invalid_collision_events=3` refers to these structurally flagged events; it does not mean three invalid event keys or three invalid severity codes.
- **Sensitivity exclusions:** 11 tractor events have known-vehicle tractor-type conflicts, including the tractor event with contradictory vehicle totals: 2013 (1), 2014 (1), 2017 (2), 2020 (6), 2021 (1). Some conflicts include `08|UU`; some events have other consistently coded tractors. A conflict does not prove absence of a tractor. Filtering can preferentially remove complex multi-vehicle events.
- **Exact record repetitions:** 2,013 normalized repeated rows are collapsed for event construction. This is not a count of duplicated physical people; identical unidentified rows can represent different people.
- **Vehicle/person uncertainty:** known-vehicle type and person-attribute conflicts, reported/observed vehicle-count differences, other/unknown/unavailable vehicle types and unidentified IDs remain explicit diagnostics. Pedestrian dummy vehicle 99/type NN and parked-vehicle dummy person NN are distinct cases.
- **Nonstandard 2020 codes:** `C_VEHS=**`, `V_ID=*` and `V_ID=00` remain preserved, profiled and unresolved.
- **Fatality consistency:** one 1999 non-tractor event lacks a fatal-person record despite fatal collision severity. No tractor event has this warning. This consistency check does not by itself validate casualty counts; see [person-level validation](casualty_validation.md).

## Verification and use boundary

The full event build completed with unique output keys, verified input hashes, physical coverage checks and selected-year overlap prevention. Focused integration tests cover event grain/code normalization/conflicts, official Excel/French ingestion, invalid-key quarantine, overlapping-source rejection, partial historical year selection and preservation of physical source coverage. Independent review passed 15 event and 21 person checks: complete output rows for 18 unchanged years matched the baseline and five promoted years matched validated candidates. Nine-source manifest parity and pinned hashes verified. The full 16-test suite and 23 notebook code cells passed. The audit notebook inspects saved outputs separately.

Overall status is **`partial_structural_exclusions_review_required`**. Structural flags and external gaps remain explicit even where benchmarks match. The reproducible event tables describe the selected public releases; they are not a fully reconciled current national series or a risk-per-kilometre measure. Person-level casualty totals have their own validation and conditional record-resolution scenarios.

The intended research period remains **2016–2025**, while selected national event records end at **2021**. Missing 2022–2025 records are not inferred from aggregates, vehicle involvements or provincial extracts. See [data availability](data_availability.md) for the separate source/geography/unit register. Use observed and strict views together and retain unresolved 2013/2019 source differences in interpretation.

## Sources and reproducibility

[Official NCDB catalogue](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a), [source release audit](source_release_audit.md), [dataset contract](dataset_contract.md), `data/sources.json` and `data/derived/ncdb/source_manifest.json` provide source URLs, dictionaries, physical/selected years, hashes and rebuild commands. Raw originals remain under `data/raw/ncdb/` and `Collisions/`. A future rebuild writes new machine-readable evidence; the timestamp above identifies the production run documented here.
