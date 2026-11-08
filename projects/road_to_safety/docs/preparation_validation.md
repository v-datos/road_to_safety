# Collision-level dataset: preparation validation

Validated October 18, 2026 (America/Edmonton). **Passed** for the pinned selected 1999–2021 releases. This phase prepares data; no exploratory risk-factor analysis, feature fitting or model training was performed.

## Delivered dataset and population

[collisions.parquet](../data/derived/collisions.parquet) contains one row per `(source_id, C_YEAR, C_CASE)`. This remains a candidate-event identity convention because the source dictionary does not formally define `C_CASE`. Source UUID, path, original-file hash and year remain attached to each row. Only the 23 selected annual releases enter this population; the older 2019 comparator and aggregate publications are excluded.

| Check | Validated result |
| --- | ---: |
| Selected annual releases | 23 (1999–2021) |
| Raw source records accounted for | 7,729,886 |
| Unique candidate collisions | 2,949,846 |
| Fatal collision target (`is_fatal=1`) | 47,793 |
| Nonfatal injury collision target (`is_fatal=0`) | 2,902,053 |
| Target-ineligible collisions | 0 |
| Invalid event-key records | 0 |
| Exact duplicate extra raw rows retained in multiplicity | 2,013 |
| Unique raw-position exception records | 332,599 |
| Annual metric comparisons matching the source audit | 253 of 253 |
| Independent source-value samples checked | 2,300 source rows, 100 per annual file |
| Predictor values outside documented domains | 0 |
| Regression tests passed | 17 |

Each of the 11 collision attributes was checked against independently read source samples where unconflicted, with zero mismatches. This bounded value check supplements full-table SQL checks and full-file fingerprints; it is not a claim that source quality was assessed only by sampling.

## Construction and conservation

The build checks source, audit, code and machine-contract fingerprints before using the selected files. It validates English/French headers and the expected source year. Canonical digit-only numeric strings lose zero padding; all original bytes remain unchanged. Unknown, other, unavailable and unresolved tokens are not collapsed or converted to zero. An unexpected source year stops the build; other invalid event keys are retained in row-numbered quarantine evidence rather than assigned new IDs.

Collision attributes are aggregated only when all canonical observations agree. A conflict yields a null value and a corresponding conflict flag. Person and vehicle diagnostics are aggregated to event grain before joining, so child records cannot multiply collisions. Source record multiplicity is preserved: the sum of event source-row counts equals all 7,729,886 selected records. No collision was removed for an incomplete predictor or unresolved linked person/vehicle.

**Three 2020 collisions have conflicting reported vehicle counts (`C_VEHS`).** Their vehicle counts are null and flagged, with all 43 supporting raw rows in exception evidence. The source audit already recorded these conflicts; its earlier prose incorrectly generalized consistency across all collision attributes. There are no conflicts in collision severity or any of the eight selected predictors. Vehicle count is a descriptive field excluded from the initial feature list.

## Duplicate, person and vehicle handling

The [exception dataset](../data/derived/preparation_exceptions.parquet) preserves raw values, source row number (first data row is 2), provenance and overlapping reason labels. It is evidence, not a table of excluded collisions or unique people. Its 332,599 source positions are unique; summing reason counts would double-count rows.

- Exact repeated rows retain original multiplicity and supporting evidence; the event is represented once. There are 7,727,873 distinct normalized source-record combinations, which are not a count of unique people.
- 30,589 records have unresolved candidate person identity, including 15,555 dummy-person records. Pedestrian dummy vehicle sequences occur in 304,229 records and are not motor vehicles.
- 761 duplicated identified-person keys cover 1,794 records. Of these keys, 410 disagree on injury outcome. No first-row, majority or most-severe outcome is selected.
- 687 candidate person keys have at least one conflicting person attribute; 339 candidate vehicle keys have conflicting type or model year. These remain diagnostics and source evidence, not initial predictors.
- The 182 source rows with undocumented collision vehicle-count codes are retained as exception evidence. Their existence does not turn them into valid numeric counts or non-accident observations.

All otherwise target-valid collisions remain eligible for the condition-only severity task. Person/vehicle model tables would require separately defined resolution and eligibility rules.

## Target and feature contract

The [machine contract](../data/reference/modeling_contract.json), [modeling contract](modeling_contract.md) and [preparation policy](preparation_policy.md) define the exact interpretation:

- `C_SEV=1` maps to `is_fatal=1`; `C_SEV=2` maps to `is_fatal=0`. Class zero means a nonfatal injury collision, not an accident-free observation. Invalid, blank or conflicting target observations would remain retained with a null binary target and eligibility false.
- The eight categorical predictors are month, weekday, hour, weather, road surface, road configuration, road alignment and traffic control.
- Target proxies, person outcomes, casualty totals, IDs, source/year identifiers, collision configuration, involved-vehicle count, demographic/vehicle aggregates, multiplicity and quality flags are excluded from the initial predictor list. They may remain in the wider analytical artifact for provenance or descriptive use; models must explicitly select the allowlist.
- No imputation, numeric scaling, category fitting, resampling, split assignment or model fitting was performed. Conditions were recorded after crashes; prospective measurement availability remains an assumption to evaluate before operational use.

## Missingness at collision grain

Denominator: **2,949,846 candidate collisions**, one vote per collision rather than one per person/vehicle segment. Unknown and other remain distinct. No blank, unavailable, invalid or conflicting values occur in the eight predictors in the selected release.

| Predictor | Unknown collisions | Unknown share | Documented other collisions |
| --- | ---: | ---: | ---: |
| `C_MNTH` | 112 | 0.004% | 0 |
| `C_WDAY` | 526 | 0.018% | 0 |
| `C_HOUR` | 31,261 | 1.060% | 0 |
| `C_WTHR` | 45,409 | 1.539% | 6,775 |
| `C_RSUR` | 37,623 | 1.275% | 87,977 |
| `C_RCFG` | 234,461 | 7.948% | 95,746 |
| `C_RALN` | 192,854 | 6.538% | 14,738 |
| `C_TRAF` | 134,811 | 4.570% | 42,317 |

The per-year/state tables retain exact counts and denominators: [preparation profile](../reports/tables/preparation_missingness.csv), [independent missingness](../reports/tables/validation_missingness.csv) and [independent value counts](../reports/tables/validation_feature_values.csv). Target eligibility is not complete-case eligibility; missing predictors were preserved without row exclusion.

## Independent verification and reproducibility

The validator independently scans the complete Parquet table using SQL. It checks unique keys, selected source/year membership, lineage, targets, conflict flags, child join/cardinality constraints, raw-record conservation, exception uniqueness/reasons, audit reconciliation, feature domains and exact published missingness counts/rates. All 24 selected originals, including the dictionary, retain their acquisition hashes. The preparation manifest fingerprints source inputs, audit/code/contract and generated outputs. The validation receipt fingerprints its inputs, code and evidence tables.

The [validation receipt](../data/derived/prepared_validation.json) has status `passed` and an empty failure list. The [preparation manifest](../data/derived/preparation_manifest.json) identifies the exact prepared release. The [validation notebook](../notebooks/02_collision_dataset_validation.ipynb) executed all seven code cells top to bottom using the locked project interpreter. Notebook structure and saved table outputs were checked; rendered visual inspection was not performed because the earlier browser URL-policy restriction remains in force. No charts were authored for this phase.

Run from the project directory:

```bash
uv sync --locked --python 3.13 --extra notebook
.venv/bin/python -m road_to_safety.prepare_collisions --workers 2
.venv/bin/python -m road_to_safety.validate_prepared
.venv/bin/python -m unittest discover -s tests -v
```

Open the saved notebook using the project `.venv` Python kernel. Raw and generated Parquet files remain local/Git-ignored; code, contracts, validation tables and documentation are versionable.

## Limits and next step

This validation establishes internal preparation consistency for the selected source releases. It does not reconcile them to newer publication vintages: the previously documented 28 of 34 annual collision-count differences remain unresolved. Case-ID semantics, source reporting completeness, undocumented vehicle-count codes and prospective input availability also remain qualifications.

The dataset has no event coordinates, province, full calendar date, traffic exposure or zero-crash observations. Provincial maps use a separate aggregate route; event hotspots and occurrence probability require additional sources.

**Next: exploratory descriptive analysis.** Describe annual/month/weekday/hour patterns and condition distributions; compare fatal-collision proportions with explicit denominators and unknown categories; assess changes in missingness, source-era effects and sparse groups. Then specify chronological development/validation/test periods and develop a prevalence baseline and regularized logistic severity model. Exploration must stay within recorded fatal/injury collisions and distinguish association from accident occurrence risk or causality.
