# Data contract and preparation requirements

**Status:** Collision-level preparation and independent validation completed October 18, 2026. See the [validation report](preparation_validation.md), [implemented modeling contract](modeling_contract.md) and [machine feature contract](../data/reference/modeling_contract.json). The analytical dataset and exception evidence are materialized; person/vehicle model tables remain separate future work.

## Population and analytical units

The confirmed scope is all road-user groups and all verified available years using the supplied official source route. The [verified inventory](source_inventory.md) identifies selected records for 1999–2021 and separately scoped aggregates. Public NCDB fatal/injury records describe a population conditional on a collision being recorded. Do not describe collision-only records as a sample of both accident and non-accident conditions.

| Analytical unit / artifact | Intended grain | Identity and interpretation |
| --- | --- | --- |
| Normalized source records | One input record with source lineage and original row multiplicity | Rows can repeat collision attributes and do not equal collisions or people |
| Published aggregate observations | One source/query context, period, category combination and measure | Preserve counting unit, filters, totals and publication vintage; overlapping margins are not independent event records |
| Collisions | One candidate event in a selected release | `(source_id, C_YEAR, C_CASE)` has valid observed keys and consistent collision fields; `C_CASE` formal semantics remain undocumented. One selected release supplies each year. |
| Vehicles | One identified vehicle within an event | Event key plus a validated `V_ID`; distinguish dummy/unknown identifiers |
| People | One identified person within an event/vehicle | Event key plus validated `V_ID, P_ID`; preserve unresolved identities separately |
| Occurrence observations, if feasible | One defined geographic/time observation with exposure | A different dataset covering both qualifying crashes and zero-crash observations |

The collision table and raw-position exception evidence are materialized. Person/vehicle identities are used for diagnostics; resolved person/vehicle model tables were not produced. Case identifiers must not be assumed stable between source versions. Never join different releases on case ID alone. Keep vehicle and person grains separate from event counts, including when aggregating mixed road-user collisions.

## Proposed outcomes

| Outcome | Definition to verify | Interpretation and exclusions |
| --- | --- | --- |
| Collision severity, primary | Verified `C_SEV=1` fatal; `C_SEV=2` nonfatal injury | All selected candidate events have consistent valid targets. Estimate fatal severity conditional on a recorded fatal/injury collision; preserve target checks in preparation. |
| Person injury severity, optional | Dictionary-defined `P_ISEV` categories | Separate person-level task; classes and eligibility need confirmation; keep all people from one event in one split |
| Accident occurrence, additional data required | At least one qualifying collision in a specified area/road segment and time interval | Needs compatible exposure and zero-crash observations; a count/rate model may be more defensible than binary probability |

Nonfatal injury collisions are not non-accident examples. Property-damage-only collisions and detailed serious-injury classes must not be invented from the initial binary collision outcome. Do not infer individual death from a fatal collision label.

## Normalization and exclusions

- Preserve original codes and identifiers as strings. Translate headers and normalize encoding explicitly; retain source language and file lineage.
- Use the matching dictionary for each release. Preserve unknown, unavailable, not applicable and other codes as distinct documented states where the source distinguishes them.
- Do not interpret special codes as zero, safe conditions, no injuries or missing numeric measurements. Apply numeric parsing only after code validation.
- Preserve raw multiplicity. Deduplicate only at the appropriate validated grain; exact duplicate rows with unknown person IDs do not establish how many people exist.
- Detect inconsistent collision attributes and outcomes across linked rows. Retain conflict evidence; define and quantify modeling exclusions before training.
- Audit invalid keys, unknown identities, missingness, top coding and exclusions by year and road-user group. Report retained and excluded populations separately.
- Select one source per year to avoid overlapping legacy and annual releases. Compare source revisions without overwriting values to force agreement with a benchmark.

## Feature availability and leakage

The primary proposed severity model uses conditions that could be specified before an outcome is known. Recording a value in a collision report does not prove it was available at the intended prediction time.

| Feature group | Initial treatment |
| --- | --- |
| Month, weekday, hour; weather; road surface/configuration/alignment; traffic control | Approved initial categorical allowlist: `C_MNTH,C_WDAY,C_HOUR,C_RCFG,C_WTHR,C_RSUR,C_RALN,C_TRAF`; prospective availability remains a scenario assumption |
| Road-user, vehicle and demographic attributes | Excluded from initial predictors; any future use needs a separately validated unit, eligibility and aggregation policy |
| Collision configuration, crash vehicle count and other event-result descriptors | Reserve for descriptive analysis or an explicitly separate retrospective model unless prediction-time availability is demonstrated |
| Target, person injury severity, fatality/injury totals, outcome-derived aggregates | Exclude from severity predictors |
| Case IDs, row IDs, release IDs, duplicate multiplicity and data-quality diagnostics | Keep for provenance, grouping and audits; exclude from primary predictors |

Do not create person-outcome aggregates as collision predictors. Evaluate year as a trend/shift diagnostic rather than assuming arbitrary identifiers generalize. The initial eight-feature allowlist is enforced by independent validation; changes require an explicit contract revision before tuning.

## Splits and transformations

Use chronological training, validation/calibration and final test periods after complete years and class support are known. Prefer rolling chronological validation within the development period. Keep every record from the same collision in the same split.

Fit imputation, category encoding, feature selection, resampling, hyperparameter selection and calibration using the appropriate development folds only. Never balance, oversample or tune against the final test population. Lock the feature list, threshold and evaluation protocol before final testing.

## Geography, time and exposure

The [NCDB Online FAQ](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-5-0&l=en) states that its data do not identify collision locations. The supplied dashboard's listed dimensions are temporal/demographic. The linked [2024 publication](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024) provides provincial/territorial casualty rates, a candidate for geographic maps using a separate aggregate series. Those rates do not identify collision hotspots.

The full-file audit confirms all selected records share 23 canonical fields after explicit French-header mapping, without province, coordinates, road segment or full calendar date. Source-page dimensions do not add missing fields to these files. Audit future release schemas and coverage independently.

Maps require verified geographic fields or separately sourced geographic aggregates. Do not infer location from `C_CASE`. External weather joins require compatible actual time/location keys; month and weekday do not identify a calendar date. National annual exposure can support national annual rates, but cannot supply weather-specific or road-segment accident probabilities by itself.

Zero-crash observations must come from a complete observation/exposure frame with verified crash reporting coverage. Absence from an incomplete crash file does not establish a safe or zero-crash interval. Define outcome window, exposure unit, reporting completeness and join coverage before occurrence modeling.

## Aggregate source handling

Archive aggregate exports or clearly labeled page captures with query variables, filters, measures, grouping, totals, capture date and source vintage. Validate category partitions against compatible totals. Do not add marginal tables together, infer joint distributions by joining separate margins, expand aggregate counts into invented individual records, or randomly split repeated aggregate cells to claim event-level model validation. A grouped-data model would require an explicitly different design and validation protocol.

The supplied views share NCDB lineage. Agreement is useful for reconciliation but is not independent replication. Preserve source revisions and rate denominators; keep person casualty counts separate from collision severity counts.

## Acceptance evidence to produce

The completed audit provides a selected-source manifest, verified checksums, year/field coverage and code profiles, grain/identity checks, duplicate/conflict diagnostics and separate benchmark comparisons. Preparation must define explicit exclusion/conflict handling and recompute feature availability at event grain. Modeling adds a prediction-time feature register and a split manifest proving chronology and collision separation.
