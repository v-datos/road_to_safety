# Collision dataset validation

Build snapshot: 2026-10-15T06:01:31.657216+00:00. Pipeline SHA256 `a024132f150d0f50629ef5cd85e77482c3cd486b7c02b2ea0debac943e9b1f29`; DuckDB 1.5.6. Live machine-readable evidence is in `data/derived/ncdb/validation.json`.

## Delivered data

The build reads **7,733,419 person/placeholder record rows** and produces **2,950,931 unique casualty-collision events for 1999–2021**. Every calendar year is present and the output key `(C_YEAR,C_CASE)` is unique. No invalid case/year records were found. An independent numeric-equivalent case-ID check found no additional duplicate keys hidden by leading-zero formatting.

There are **80,632 observed road-tractor collisions** (`V_TYPE=08`) in the primary tractor table. The strict sensitivity subset has **80,621 events**, excluding 11 flagged events. The primary table retains these events with their flags; the stricter count is not a corrected national total.

Files:

- `data/derived/ncdb/collisions.parquet`: all observed collision events and flags.
- `data/derived/ncdb/road_tractor_collisions.parquet` and `.csv`: all observed tractor-involved events.
- `data/derived/ncdb/road_tractor_collisions_strict.parquet`: conservative sensitivity subset.
- `data/derived/ncdb/annual_counts.csv`, `reconciliation.csv`, `quality_by_year.csv`, code profiles, issue Parquet files and source manifest: audit evidence.
- `notebooks/01_dataset_validation.ipynb`: runnable independent checks of the outputs.

## External reconciliation

This comparison uses **unfiltered observed** tractor collisions, separately by fatal and injury severity, against [Transport Canada Table 1](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021). Intentional strict exclusions are shown separately. Source counts are never modified to fit a benchmark.

| Year | Observed fatal | Published fatal | Observed injury | Published injury | Strict exclusions | Source comparison |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2012 | 197 | 197 | 3,103 | 3,103 | 0 | exact match |
| 2013 | 195 | 195 | 3,148 | 3,150 | 1 | unresolved difference |
| 2014 | 211 | 211 | 3,216 | 3,216 | 1 | exact match |
| 2015 | 194 | 194 | 2,880 | 2,881 | 0 | unresolved difference |
| 2016 | 193 | 193 | 2,816 | 2,817 | 0 | unresolved difference |
| 2017 | 214 | 216 | 2,962 | 2,962 | 2 | unresolved difference |
| 2018 | 190 | 190 | 2,800 | 2,800 | 0 | exact match |
| 2019 | 192 | 196 | 2,679 | 2,581 | 0 | unresolved difference |
| 2020 | 158 | 158 | 1,964 | 1,964 | 6 | exact match |
| 2021 | 169 | 169 | 2,107 | 2,107 | 1 | exact match |

The 2018, 2020 and 2021 counts were independently reproduced with streaming Python/openpyxl against the official originals. Historical 2012–2017 counts and the 2019 count were also reconstructed separately during scoping. The 2019 English and French official downloads contain the same 272,301 coded records, and the English records match the inherited local file. Redownloading and changing language do not resolve the 94-event difference (192+2,679 versus published 196+2,581).

The 2013 and 2015–2017 differences are 1–2 events each. Source versions and revisions are plausible explanations, but no specific cause is established. Years before 2012 have no tractor-event benchmark in this package and are labeled accordingly. See [the investigation](ncdb_2019_investigation.md).

## Internal findings and impact

- **High confidence, localized event defects:** three 2020 events have contradictory `C_VEHS` values. Their vehicle-count field is null in the event table and the alternatives are retained in `collision_attribute_conflicts.parquet`. Two are non-tractor events; one is tractor-involved. Other collision attributes agree.
- **Conservative sensitivity exclusions:** 11 tractor events have known-vehicle tractor-type conflicts, including the tractor event with contradictory vehicle totals. They occur in 2013 (1), 2014 (1), 2017 (2), 2020 (6) and 2021 (1). Some conflicts are `08|UU`; other events have additional consistently coded tractors. These flags do not establish that tractor involvement is false. Strict filtering can disproportionately remove complex multi-vehicle events.
- **Duplicate records:** 2,013 exact normalized record duplicates are collapsed for event construction. This does not establish a count of duplicated people; unidentified records can be observationally identical.
- **Vehicle and person uncertainty:** reported versus observed vehicle-count differences, other/unknown/unavailable vehicle types, unidentified vehicle IDs and conflicting person attributes remain explicit flags. Pedestrian dummy vehicle 99/type NN and parked-vehicle dummy person NN are handled separately from real vehicle/person IDs.
- **Nonstandard 2020 codes:** `C_VEHS=**`, `V_ID=*` and `V_ID=00` are preserved and profiled. They are not numerically coerced or guessed.
- **Fatality consistency:** one 1999 non-tractor event lacks a corresponding fatal-person record despite fatal collision severity. No tractor event has this warning. This supports event severity checks but does not validate person-level casualty totals.

## Verification and use boundary

The full build completed. Four focused integration tests pass: event grain/code normalization/conflicts, official Excel and French ingestion, invalid-key quarantine, and overlapping-source rejection. The locked project environment and pinned input hashes were checked. The audit notebook compares the saved Parquet subsets and annual totals independently.

Overall status is **`partial_structural_exclusions_review_required`**. The event tables are reproducible and useful for describing this public release with explicit sensitivities. They are not a fully reconciled current national series. Person-level deaths/injuries are deliberately not summed, because unknown and conflicting identities require their own validation.

The original research target remains **2016–2025**. Current downloadable event records end at **2021**; 2022–2025 cannot be inferred or filled with vehicle-involvement tables. Before headline trend interpretation, show the observed and strict series together, retain the 2019 benchmark qualification, and seek source-owner clarification of unresolved differences.

## Sources and reproducibility

[Official NCDB catalogue](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a), [acquisition notes](ncdb_acquisition.md), [dataset contract](dataset_contract.md), and `data/sources.json` provide URLs, dictionaries, hashes and rebuild commands. Raw originals are under `data/raw/ncdb/`; the inherited historical file remains in `Collisions/` unchanged. A later rebuild writes new evidence under `data/derived/ncdb/`; this document records the run above.
