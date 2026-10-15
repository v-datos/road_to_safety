# Collision dataset contract

## Scope and sources

The build reads the inherited NCDB 1999–2017 CSV and freshly acquired official 2018–2021 files. It does not read the truncated `test99_to_2019*` files, duplicate copies, old aggregate exports, UK data, or notebook outputs. Each year is assigned exactly one source in `data/sources.json`. The build rejects overlapping source years and unexpected column schemas. The raw files are immutable inputs; source paths, URLs, coverage, SHA256 hashes and download dates remain traceable.

NCDB's public records cover **fatal and injury collisions on public roads**. They do not cover property-damage-only collisions. Coverage of all years in a source does not prove full agreement with revised national statistics. The intended research period remains 2016–2025, and 2022–2025 remain outside the current microdata dataset.

## Grain and selection

- Primary key: `(C_YEAR, C_CASE)`; year is an integer and case ID remains text. Case IDs are not assumed unique across years.
- `collisions.parquet` contains one row per observed collision, including any structurally flagged events.
- `road_tractor_collisions.parquet` and `.csv` contain every collision with a recorded `V_TYPE=08`, retaining flags. `road_tractor_collisions_strict.parquet` additionally requires `is_analysis_candidate=true` and is a sensitivity subset, not a corrected national series.
- Code 08 means road tractor **with or without semitrailer**. Code 07 heavy unit truck is stored as a separate presence flag.
- All records of a selected collision are used to validate its attributes, including records for other vehicles and pedestrians. Selecting only tractor occupants would lose harm to others.
- No counts are adjusted to agree with an external benchmark. Externally unresolved counts are retained and labeled.

## Columns

| Columns | Meaning |
| --- | --- |
| `C_YEAR`, `C_CASE` | Event key, preserving the public release's case ID. |
| `C_MNTH`, `C_WDAY`, `C_HOUR`, `C_SEV`, `C_VEHS`, `C_CONF`, `C_RCFG`, `C_WTHR`, `C_RSUR`, `C_RALN`, `C_TRAF` | Original collision codes. Consult the source dictionary; special codes remain strings. If rows disagree on one of these fields, its value is null and the conflict is exported. `C_SEV=1` is fatal, `2` injury. |
| `source_id` | Join to the source manifest and `data/sources.json`. |
| `is_road_tractor`, `is_heavy_unit_truck` | At least one record has vehicle type 08 or 07, respectively. This establishes recorded involvement, not fault. |
| `known_vehicle_count`, `road_tractor_vehicle_count` | Distinct vehicle IDs 01–98, all types or type 08. These are involvements, not event counts. Pedestrian dummy ID 99 is excluded. |
| `input_record_rows`, `distinct_record_rows` | Input rows and distinct normalized rows for the event. These are **record counts, not people**. |
| `collision_attribute_conflict_count`, `vehicle_type_conflict_count`, `person_attribute_conflict_count` | Conflicting collision fields, known vehicle IDs with conflicting types, and known person keys with conflicting person attributes. Person checks use numeric IDs linked to numeric vehicle IDs; unknown identities cannot be deduplicated reliably. |
| `no_tractor_type_conflict` | No known vehicle ID is coded both 08 and another vehicle type. This does not establish true absence of tractors when vehicle type is unknown. |
| `has_unidentified_tractor`, `has_unidentified_vehicle`, `has_unknown_vehicle_type`, `has_unknown_person_id` | Source completeness warnings. The vehicle-type warning includes QQ other/unspecified, UU unknown and XX unavailable; `vehicle_type_profile.csv` distinguishes them. Dummy vehicle type NN is excluded. |
| `has_dummy_pedestrian_vehicle` | At least one record has dummy vehicle type NN. |
| `vehicle_count_difference` | Known observed vehicles minus numeric `C_VEHS`. Null for unknown counts or top-coded 99 (99 or more). A difference is a warning, not an instruction to create or delete vehicles. |
| `reported_vehicle_count_top_coded` | Reported vehicle count is 99 or more. |
| `fatal_person_record_present`, `fatality_consistency_warning` | Whether any linked record has `P_ISEV=3`, and whether that disagrees with the event's fatal severity. This is a consistency check, not a validated count of fatalities. |
| `is_structurally_valid` | All collision fields agree within the event and severity is 1 or 2. Valid key/year checks occur before aggregation. |
| `is_analysis_candidate` | Structurally valid and no known-vehicle tractor-type conflict. Other completeness warnings and external benchmark differences remain visible and must be considered for the intended analysis. |

## Normalization and exclusions

One-digit numeric codes in dictionary fields of width two are zero-padded. Longer codes are never truncated. Unknown/not-applicable/other codes (`U`, `N`, `Q`, `X` variants) and the 2020 source's `*`/`**` are preserved. The French 2021 header names are mapped explicitly to the English canonical column names after CP1252 decoding; coded values are unchanged. The 2018 workbook is read from its `in` sheet and converted only in temporary staging.

Exact duplicate normalized records are collapsed before attribute checks. Because identical unknown-person rows could represent different people, this operation is used only for event construction and record diagnostics. **No person casualty totals are produced by this build.** Person keys with known IDs can conflict; NN dummy parked-vehicle people and UU unidentified people must not be treated as identified human beings.

Missing or invalid event keys are exported to `invalid_key_records.parquet`. Conflicting event fields and known-vehicle tractor-type conflicts are excluded from the **strict** subset and listed in `excluded_tractor_collisions.parquet` and issue exports; they remain in the observed tables. Such exclusions change the overall validation status to partial, requiring review. A conflicting code can coexist with positive tractor evidence elsewhere in the event. The strict filter may preferentially remove complex multi-vehicle events, so always show observed and strict totals together.

## Validation layers

1. **Input and grain:** source checksum, schema, actual year coverage, nonoverlapping sources, valid case/year and unique output event key.
2. **Internal consistency:** collision fields, known-vehicle types, person-attribute conflicts, reported/observed vehicle counts, and event/person fatality consistency.
3. **External reconciliation:** each **unfiltered observed** 2012–2021 tractor fatal/injury count compared separately with Transport Canada's published Table 1. Strict candidate counts and exclusions appear alongside them, so intentional filtering is not mistaken for a source discrepancy. Exact equality, unresolved difference and no benchmark are explicit statuses; no tolerance is silently accepted.

Structural validity and external agreement are separate. A structurally valid event table can describe its public release while differing from another official publication's vintage. It cannot be called a reconciled current national series until differences are explained. Unknown vehicle types also mean observed tractor involvement may be incomplete.

## Rebuild and inspect

From the repository root:

```bash
uv sync --extra notebook
PYTHONPATH=src .venv/bin/python -m truck_collisions.download
PYTHONPATH=src .venv/bin/python -m truck_collisions.build
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The download command fetches missing files only and verifies pinned hashes. If an official file has changed, it stops for a source-version review. The inherited historical source's original acquisition date is unknown; its hash is recorded and pinned after inspection.

Outputs are under `data/derived/ncdb/`: the collision Parquet table, tractor subset in Parquet/CSV, annual counts, external reconciliation, quality by year, collision-code profile, source manifest, issue tables and `validation.json`. See `notebooks/01_dataset_validation.ipynb` for a runnable audit companion. Raw and derived datasets are excluded from Git; code, manifests, reference counts and methods are versioned.
