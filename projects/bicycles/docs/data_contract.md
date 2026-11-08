# Bicycle data contract

Implemented by `src/bicycle_collisions/build.py`, `online.py` and `analyze.py`.

## Population and identifiers

Select each valid 2010–2021 release event with at least one `V_TYPE=17` Bicycle record and retain every linked record in that event. One release supplies each year. Physical file coverage and selected years are validated separately. Codes and IDs remain strings; translated French headers and CP1252 encoding are normalized explicitly.

Event identity is `(source_id, C_YEAR, C_CASE)` with positive numeric case ID and a four-digit year. Vehicle identity adds a numeric `V_ID` from 01–98. Known person identity adds numeric `V_ID` 01–99 and `P_ID` 01–99; vehicle 99 permits pedestrian records. Dummy `P_ID=NN` and unknown IDs are not invented people.

`P_USER=4` is the primary bicyclist person classification. Disagreements with recorded bicycle type and events with a bicyclist code but no bicycle type are audited. A person's conflicting road-user codes are retained as `conflict`; no alternative is selected to maximize a count.

## Record artifacts under `data/derived/`

| Artifact | Grain and purpose |
| --- | --- |
| `records.parquet` | All retained normalized source rows, including duplicate multiplicity |
| `bicycle_collisions.parquet` | One selected event; collision attributes and conflict count |
| `vehicles.parquet` | One known vehicle ID per event; type conflict status and bicycle presence |
| `people.parquet` | One known person key per event/vehicle; resolved fields and injury-outcome alternatives |
| `unresolved_records.parquet` | Distinct normalized record alternatives with unknown or dummy identity |
| `validation.json` | Input fingerprints, coverage, annual counts and quality diagnostics |
| `build.duckdb` | Reusable build tables, supporting evidence queries |
| `report_snapshot.json` | Reviewed aggregate evidence for the report |

Exact duplicate rows are collapsed for grain construction. Their original multiplicity remains in `records.parquet`. Unknown-identity rows are not automatically distinct people or a single person. Blank/unknown codes are not zero outcomes.

## Measures

- **Unique bicycle-involved casualty collisions:** distinct selected event keys. `C_SEV=1` is fatal and `2` injury. A fatal event means someone died, not necessarily a bicyclist.
- **Bicycle involvements:** distinct known bicycle vehicle keys for the record series; the online vehicle series remains a separately scoped published measure.
- **Resolved bicyclist deaths/injuries:** known person keys with consistent `P_USER=4` and a single `P_ISEV=3` or `2` respectively.
- **All-road-user harm:** resolved identified casualties across all retained road users, including people outside the bicycles. Unknown identities and unresolved outcomes remain separately diagnosed.
- **Person outcome min/max:** whether all/any known alternatives for an identified key have that outcome. These are record-resolution scenarios, not confidence intervals or bounds on true population casualties.
- **Co-involved vehicle types:** distinct selected events containing each type among known vehicle IDs. Groups overlap and do not identify striking vehicles or fault. Conflicting types are not assigned to a single class.
- **Fatal-involvement share:** online bicycle involvements in fatal collisions divided by all bicycle involvements in fatal/injury collisions; not risk per cycling trip.

## Online aggregates

The selected source is the NCDB Online cube labeled August 12, 2025, captured October 17, 2026. Vehicle Type=Bicycle supplies the vehicle and condition/time series. Road User Class=Bicyclist supplies the person series and its age/gender profiles. All series cover 2010–2023; year and fixed-population totals are disabled. Age and hour use disjoint native ranges plus explicit unknown categories.

The 4,536 normalized observations in `data/reference/ncdb_online_bicycles_2010_2023.csv` have fields `dataset, year, category, measure, count`. Total rows are validation references, not additional observations to sum with categories. Each of 462 dataset/year/measure partitions reconciles to the correct annual person or vehicle series.

Preserved visible DOM cell matrices are the acquisition evidence. The native CSV download timed out; do not describe these as native exports. The selected matrices and normalization are pinned in the reference metadata. Earlier incomplete exploratory captures are excluded.

## Release and quality handling

Retain unknown and unavailable categories, source hashes and revision flags. Record files, online contexts and newer publications differ; keep these comparisons visible and never splice unlike counting units or overwrite values merely to obtain agreement. See [validation](validation.md) for the actual differences and checks.
