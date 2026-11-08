# NCDB data-quality and modeling-feasibility assessment

This is the acquisition-audit snapshot. Collision-level preparation was subsequently completed; see the [preparation validation report](preparation_validation.md) for current dataset readiness.

Audit date: **October 17, 2026 (America/Edmonton)**. Scope: all 23 selected annual official releases, 1999–2021, covering every available road-user category. This is a source and feasibility audit, not exploratory risk-factor analysis or a trained model. The older 2019 CSV is a separate comparator and is excluded from every pooled selected-release total below.

## Decision and population

**Proceed with collision-severity preparation, subject to the explicit controls below.** The selected releases contain **7,729,886 source records representing 2,949,846 candidate collisions**. Every candidate collision has one consistent dictionary-defined severity: **47,793 fatal collisions (1.620%)** and **2,902,053 nonfatal injury collisions**. These are collisions conditional on the NCDB fatal/injury reporting population; they are not accident probabilities, individual fatality probabilities, all road incidents, or a causal evaluation of infrastructure.

The public microdata permit national temporal summaries and retrospective associations. They do not contain event coordinates, province/territory, road segment identifiers, a calendar day/date, traffic volume, or zero-crash observations. **Event hotspot maps, compatible event weather joins and accident-occurrence models are not supported by these inputs.** Separate provincial aggregate series may support provincial maps after their population, vintage and denominator are verified.

## Evidence, sources and reproducibility

The [source manifest](../data/sources.json) records URLs, versions, selected/comparator status, local paths, encodings and original-file SHA256 values. Originals were freshly acquired through the official [Open Government NCDB catalog](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a), following the supplied Transport Canada source routes. Definitions below come from its [official dictionary](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/21eb7966-38da-4814-a80e-521bce6c4c27/download/data_dictionary.pdf), archived as `data/raw/ncdb/data_dictionary.pdf` (English definitions pages 1–10).

The reproducible implementation is [audit_data.py](../src/road_to_safety/audit_data.py); [the companion notebook](../notebooks/01_source_and_quality_audit.ipynb) reruns or verifies the full selected-file audit and displays the key tables. [quality_audit.json](../data/derived/quality_audit.json) retains each input fingerprint, code fingerprint, runtime versions, parsed headers, full code-frequency profiles and per-file checks. Raw originals are never rewritten. Numeric code padding is removed only in a temporary audit view; this handles XLSX numeric cells and zero-padded CSV codes consistently. Candidate IDs are normalized numerically within a release, never joined across releases.

The dedicated project environment and lockfile pin the reader and profiling dependencies: DuckDB 1.5.3, pandas 2.3.3, openpyxl 3.1.5 and python-calamine 0.9.0. All rows are scanned. The calamine XLSX read is independently compared against openpyxl for declared row count and the first 100 data rows of each workbook. Those 100 records check parsing, not dataset quality by sampling. CSV parsing requires exactly 23 fields per nonblank record. French 2021 headers are checked against an explicit dictionary-aligned mapping and decoded using Windows-1252. No source-file schema is inferred from another year.

From the project root:

```bash
uv sync --locked --extra notebook
uv run --locked --extra notebook python -m road_to_safety.audit_data --workers 2 --include-comparator
uv run --locked --extra notebook python -m unittest discover -s tests -p 'test_audit_data.py'
```

The notebook may be executed with nbclient using its project root as working directory. Audit-cache reuse requires the current file and manifest checksums, code fingerprint, source identity, year, selection role and sheet to match. A changed manifest checksum fails before cache reuse.

## Dataset grain and dictionary meanings

Each original has **23 columns**. The selected annual files contain only their expected year; no blank source rows or invalid candidate collision-key rows were observed. Collision attributes repeat across person/vehicle segments. Records include people with no injury, unknown identities, dummy people for parked vehicles, and pedestrian dummy vehicles. Therefore raw rows cannot be summed as collisions or assumed to count distinct people.

| Concept | Verified meaning and handling |
| --- | --- |
| Candidate collision key | `(selected release, C_YEAR, C_CASE)`; numeric positive case ID and expected year. `C_CASE` is present but is **not defined in the linked dictionary**, so formal ID semantics remain unverified. Grouping is supported by within-release attribute consistency, not proof of cross-release stability. |
| Candidate vehicle key | Collision key plus numeric `V_ID=1–98`; `V_ID=99` is the sequence assigned to pedestrians, not a motor vehicle. Unknown/star IDs stay unresolved. |
| Candidate identified-person key | Collision key plus numeric `V_ID=1–99`, `P_ID=1–99`; numeric IDs still require uniqueness/conflict checks. This is an audit eligibility rule, not proof of true-person identity. |
| `C_SEV=1` | Collision producing at least one fatality. |
| `C_SEV=2` | Collision producing nonfatal injury. No separate property-damage-only class exists here. |
| `P_ISEV=1 / 2 / 3` | No injury / injury / fatality. These are person-segment outcomes; fatal collision does not mean every person died. |
| `P_USER=1 / 2 / 3 / 4 / 5` | Motor vehicle driver / passenger / pedestrian / bicyclist / motorcyclist. |
| `P_USER=U` | **Not stated / Other / Unknown**, an inseparable combined category; do not recode it as a single known road-user group. |
| Repeated `U`, `X`, `N`, `Q` | Unknown / jurisdiction does not provide / not applicable / other, respectively, where specified by the field dictionary. Keep these states separate. |
| `*` / `**` | Observed in 2020; their meaning is **not specified in the acquired dictionary**. Preserve as unresolved source codes pending authoritative clarification. |

All five defined road-user classes occur in the selected files; [record_road_users.csv](../reports/tables/record_road_users.csv) provides year-specific record counts and distinct collisions containing each code. Its event counts overlap across road-user groups and must not be added together. Coverage means observed categories in the released population, not proof of complete reporting for all Canadian road users or jurisdictions.

## Annual coverage and collision outcomes

All values below use one selected release per year and distinct candidate event keys. Full identity, duplicates and feature-conflict columns are in [record_annual_quality.csv](../reports/tables/record_annual_quality.csv).

| Year | Raw segments | Collisions | Fatal collisions | Fatal collision share |
| --- | ---: | ---: | ---: | ---: |
| 1999 | 413,509 | 151,315 | 2,632 | 1.739% |
| 2000 | 422,075 | 155,838 | 2,548 | 1.635% |
| 2001 | 409,389 | 151,438 | 2,415 | 1.595% |
| 2002 | 420,008 | 156,415 | 2,583 | 1.651% |
| 2003 | 407,036 | 152,980 | 2,487 | 1.626% |
| 2004 | 389,050 | 147,588 | 2,438 | 1.652% |
| 2005 | 386,470 | 148,111 | 2,551 | 1.722% |
| 2006 | 378,523 | 145,103 | 2,586 | 1.782% |
| 2007 | 368,507 | 141,070 | 2,455 | 1.740% |
| 2008 | 338,268 | 129,764 | 2,193 | 1.690% |
| 2009 | 330,771 | 125,456 | 2,007 | 1.600% |
| 2010 | 334,555 | 125,636 | 2,021 | 1.609% |
| 2011 | 325,153 | 124,199 | 1,849 | 1.489% |
| 2012 | 322,984 | 124,682 | 1,848 | 1.482% |
| 2013 | 317,149 | 122,132 | 1,772 | 1.451% |
| 2014 | 300,431 | 116,292 | 1,675 | 1.440% |
| 2015 | 312,042 | 119,550 | 1,693 | 1.416% |
| 2016 | 306,260 | 118,321 | 1,738 | 1.469% |
| 2017 | 289,823 | 114,412 | 1,698 | 1.484% |
| 2018 | 285,382 | 111,334 | 1,754 | 1.575% |
| 2019 | 269,328 | 104,630 | 1,620 | 1.548% |
| 2020 | 198,745 | 79,990 | 1,602 | 2.003% |
| 2021 | 204,428 | 83,590 | 1,628 | 1.948% |
| **Selected total** | **7,729,886** | **2,949,846** | **47,793** | **1.620%** |

Severity target availability is **2,949,846 / 2,949,846 collisions (100%)** under the candidate key. There are no within-event severity or eight-predictor conflicts. The machine audit records three 2020 collisions with conflicting reported vehicle counts (`C_VEHS`); the earlier narrative incorrectly generalized consistency to all 11 attributes. Preparation retains these events with null vehicle counts and conflict flags; vehicle count is excluded from the initial predictors. [quality_collision_conflicts.csv](../reports/tables/quality_collision_conflicts.csv) preserves each year/field check. This does not establish independence between collisions, geographic coverage completeness, or clinical injury detail beyond the provided labels.

## Quality findings and analytical consequences

| Finding | Evidence | Risk and severity | Required handling |
| --- | --- | --- | --- |
| Raw rows are not unique people or collisions | 7,729,886 segments versus 2,949,846 candidate events; 304,229 segments use pedestrian dummy `V_ID=99`. | **High**: repeated event labels cause incorrect denominators and train/test leakage. | Build event-level target rows only after preserving source lineage; keep every segment of one event in the same split. Do not count dummy pedestrian IDs as vehicles. |
| Person identity is partly unresolved | 30,589 rows (0.396%) fail the numeric candidate person-key rule; this includes 15,555 `P_ID=NN` dummy-person rows. | **High** for person modeling: unresolved rows cannot establish unique people or stable joins. | Retain unresolved records separately. Do not assign invented IDs, silently drop them, or count exact duplicate unresolved rows as known distinct people. |
| Repeated numeric person keys sometimes disagree | 761 duplicated candidate person keys cover 1,794 rows, with 1,033 extra rows above one per key; **410 keys disagree on `P_ISEV`**. | **High** for person modeling. Numeric IDs alone do not establish one trustworthy person outcome. | Define a conflict-resolution or exclusion policy before person modeling; preserve exception counts by year. Do not choose the first label. |
| Exact row duplication exists | 2,013 extra exact source rows, including unresolved identities; 386 in 2015, 403 in 2016, 400 in 2018, 401 in 2019, 405 in 2020. | **Medium**: duplicate segments can distort person statistics; duplication is not uniform over time. | Preserve multiplicity in raw ingestion. Event counts already use distinct candidate event keys. Any downstream deduplication needs a stated grain and exclusion receipt. |
| Vehicle characteristics sometimes conflict within a numeric key | 339 candidate numeric vehicle keys (`V_ID=1–98`) have multiple `V_TYPE` or `V_YEAR` values. | **High** for vehicle aggregation. | Preserve conflicting keys; do not collapse to arbitrary vehicle type/model year for collision features. |
| One fatal event lacks an observed fatal person segment | One event in 1999 has `C_SEV=1` but no `P_ISEV=3` segment; no nonfatal injury event contains `P_ISEV=3`. | **Medium**, unknown cause; could reflect recording or person-segment completeness. | Retain the event severity label for audit. Do not infer individual death or relabel the collision without source guidance. |
| Undefined asterisk codes | In 2020, `C_VEHS` has 182 records with asterisk codes; `V_ID` has 39. | **Medium**, unresolved meaning. | Keep a separate unresolved code state. Seek an authoritative definition before vehicle-count conversion or identity assignment. |
| Many person injury outcomes are non-target states | `P_ISEV=N`: 372,548 rows (4.820%); `U`: 130,004 (1.682%). `N` is far more common than `P_ID=NN` dummy-person records. | **High** for person modeling. `N` must not be assumed to mean no injury, and not every `N` can be attributed to a known dummy identity. | Exclude non-target states with explicit counts from a person injury target; investigate their population by year/road-user before interpreting eligibility. |
| Geographic and full-date fields are absent | Every file has the same 23 canonical fields after checked French-header mapping; none is province, coordinates, road segment or calendar day/date. | **High** for maps, exposure and external weather linkage. | Use only national month/weekday/hour patterns from microdata; obtain separate geographic/exposure inputs for other tasks. Do not decode location or a day from `C_CASE`. |
| `C_CASE` formal semantics are unresolved | Present and positive in all selected rows, but absent from the linked dictionary. | **Medium**; event-grain interpretation remains a candidate contract. | Seek source-owner documentation. Do not assume identifier stability, geography or chronological ordering across releases. |

Person outcomes illustrate the distinction between raw label coverage and unique eligible identities. Raw `P_ISEV` counts are **3,125,755 no-injury**, **4,048,350 injury**, **53,229 fatality**, **372,548 not applicable** and **130,004 unknown**. Of all source records, **7,226,708** both satisfy the candidate identified-person rule and have a target code in 1–3. After requiring one consistent valid outcome per numeric candidate person key, **7,225,489 keys** remain. These are audit eligibility counts, not a production person table or a guarantee of true-person identity. [record_outcomes.csv](../reports/tables/record_outcomes.csv) preserves separate source-record and collision grains; never compare 53,229 raw fatal-person segments directly to 47,793 fatal collisions as if the units matched.

## Missingness and coding profile

[quality_missingness.csv](../reports/tables/quality_missingness.csv) gives every year/field/state count and rate; its denominator is **all raw segments of that source**, including dummy segments. [record_value_counts.csv](../reports/tables/record_value_counts.csv) retains every normalized non-case code and its frequency, and [quality_fields.csv](../reports/tables/quality_fields.csv) records field cardinalities. No blank values or jurisdiction-unavailable `X` codes were observed in the selected releases. Their absence does **not** establish complete reporting from every jurisdiction or prove all unknowns are random.

| Field/state | Selected-record count | Share of 7,729,886 raw records | Interpretation |
| --- | ---: | ---: | --- |
| Month unknown | 455 | 0.006% | Rare unresolved month. |
| Weekday unknown | 1,394 | 0.018% | Rare unresolved weekday. |
| Hour unknown | 74,526 | 0.964% | Preserve as an unknown time category. |
| Weather unknown | 112,110 | 1.450% | Assess missingness drift before using weather as a predictor. |
| Road surface unknown | 94,407 | 1.221% | Keep separate from “other” surface (224,425 records). |
| Road configuration unknown | 602,285 | 7.792% | Material missingness in a plausible condition feature. |
| Road alignment unknown | 527,699 | 6.827% | Material missingness in a plausible condition feature. |
| Traffic control unknown | 315,287 | 4.079% | Do not interpret unknown as no control. |
| Model year unknown | 410,474 | 5.310% | Separate from 357,033 not-applicable records. |
| Age unknown | 499,246 | 6.459% | Separate from 23,419 not-applicable records. Age 99 is top-coded, not an exact age. |
| Safety device unknown | 835,111 | 10.804% | Separate from 747,656 not applicable and 68,799 other records; safety use is not independently observed exposure. |
| Road user not stated/other/unknown | 274,954 | 3.557% | Preserve the combined category; no unsupported split into its components. |

These are raw-record availability rates. They are not event-level feature missingness rates or risk ratios. Repeating an event's weather once per segment weights larger collisions more heavily; downstream collision-level preprocessing must recompute missingness at the selected modeling grain.

## Temporal and release anomalies

1. **A revised 2019 release changes totals.** The selected newer XLSX has 269,328 rows, 104,630 collisions and 1,620 fatal collisions. The older CSV has 272,301 rows, 105,782 collisions and 1,623 fatal collisions: differences of 2,973 rows, 1,152 events and 3 fatal events. Both have internally consistent collision attributes, 95 repeated numeric person keys, 61 person-severity conflict keys and 48 conflicting numeric vehicle keys. There is no demonstrated structural winner. Selecting the newer annual release is a version policy, not evidence that one file is more accurate. Preserve both, never pool them, and reconcile only with a benchmark of compatible vintage/definitions. Cause of the revision remains unverified.
2. **Identity exceptions change abruptly.** Unresolved person identity rises from 635 rows in 2014 (0.211%) to 3,592 in 2015 (1.151%), falls to 180 in 2017 (0.062%), rises to 3,419 in 2018 (1.198%) and reaches 4,066 in 2020 (2.046%). Exact duplicate rows show a related concentration in several later years. No causal explanation is established; release or reporting changes are hypotheses requiring source-owner evidence. Randomly mixed train/test splits would hide some of this temporal behavior.
3. **Person outcome encoding changes early.** `P_ISEV=N` rises from 0.15% of rows in 1999 to 5.30% in 2000, while `U` falls from 4.62% to 0.33%. This is a strong coding/composition warning; treating N and U interchangeably, or N as no injury, would fabricate a trend.
4. **Late-year collision volume and class mix shift.** Collision count falls from 104,630 in 2019 to 79,990 in 2020 (−23.55%), then rises to 83,590 in 2021. The fatal collision share rises from 1.548% to 2.003%, then is 1.948%. These are conditional descriptive rates; changed travel exposure, case mix, reporting and policy are possible explanations, not findings of this audit. Use chronological validation, including an explicit late-year shift assessment.
5. **Road-user coding completeness varies.** Combined `P_USER=U` is 1.86% of rows in 1999 and 7.15% in 2020. Unknown safety device is 19.63% in 1999 and 14.27% in 2020, versus roughly 9–12% in most intermediate years. Do not attribute road-user or safety-use trends entirely to behavior without assessing recording changes.

## Aggregate quality and cross-source reconciliation

The [aggregate-source audit](aggregate_source_audit.md) and [consolidated source inventory](source_inventory.md) extend this assessment beyond the record files. The [source comparison](../reports/tables/source_benchmark_comparison.csv) compares selected collision counts, not repeated person rows, with fatal/injury collision counts in the separately preserved 2024 publication vintage.

Across **2005–2021**, **6 of 34 year/measure pairs agree and 28 differ**. Differences range in direction and size. For example, 2020 injury collisions are 78,388 in the selected records versus 74,954 in the publication, a difference of +3,434. For 2021, fatal collisions are 1,628 versus 1,687, a difference of −59. These comparisons preserve source and publication vintages; they do not establish the cause of differences or justify adjusting raw observations. Revisions, release coverage and the undocumented case-key semantics remain relevant uncertainties. **Internal structural consistency does not establish a fully reconciled current national series.** Use the pinned microdata population for modeling and a consistently labeled publication vintage for newer national reporting.

Additional verified aggregate findings affect downstream use:

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Dashboard text injury margin fails reconciliation | Annual 2014–2023 injuries sum to 1,369,953; road-user injury categories, including Unknown, sum to 1,368,953: a deficit of 1,000. Other injury margins reconcile; all fatality margins reconcile. | High for road-user injury comparisons. Preserve the source; do not present this margin as complete or repair a category by assumption. The finding applies to the archived official text, not an independently verified live Power BI state. |
| Publication revision differs from dashboard text | 2016 injuries are 160,246 in the dashboard versus 160,248 in the newer publication. | Keep source vintages separate; do not splice overlapping rows or treat views of shared NCDB lineage as independent replications. |
| Publication percentages are internally inconsistent | Separate 2024 road-user percentage and count tables disagree for driver/other shares. | Use the preserved count table for explicit count-based calculations, flag the separate percentage table, and seek clarification before quoting its figures. |
| Geographic rates need source qualifications | The acquired publication supplies provincial/territorial rates, with preliminary/estimated-data, reporting-change and small-jurisdiction qualifications. | Aggregate maps are feasible after obtaining boundaries and validating joins. These rates do not add event locations or matched exposure observations to the microdata. |
| Native interactive exports remain unverified/unacquired | NCDB Online year domain is 1999–2023; wizard requests returned archived application errors. Dashboard HTML tables were acquired, but native Power BI export was not verified. | The HTML-derived CSVs are valid source-linked extracts, not native exports. Error pages are provenance evidence only. These access gaps do not invalidate the separately downloaded records or publication extracts. |

## Feasibility by intended use

| Intended output | Status with acquired microdata | Conditions / missing evidence |
| --- | --- | --- |
| Collision severity, fatal vs nonfatal injury | **Feasible to prepare**: 47,793 fatal events across all selected years; complete internally consistent candidate collision targets. | Confirm candidate event-key contract; use pre-outcome condition allowlist, event-level preprocessing, chronological splits, imbalance-aware metrics and calibration. This audit does not establish predictive performance. |
| Person injury severity | **Conditional**: three stated labels, plus coded non-target states and identity conflicts. | Separate unit/eligibility specification, conflicts and missing-state policy; compare exclusions by year and road-user. Never derive a person death label from `C_SEV`. |
| Risk-factor association analysis | **Feasible with restrictions**. | Quantify associations conditional on reported fatal/injury collisions. Account for release/time changes, missingness, class imbalance and absence of exposure; do not claim causal risk reduction. |
| National annual/month/weekday/hour plots | **Feasible**. | Use appropriate event/person denominators, retain coded unknowns, preserve vintage and distinguish counts from exposure-adjusted rates. No daily calendar series can be derived. |
| Road-user composition and outcome summaries | **Feasible with restrictions**. | Preserve unknown/other category and conflicting identities. Collision groups overlap; raw segments are not automatically unique people. |
| Collision hotspot / road-segment maps | **Unsupported**. | Need separately verified geocoded records or appropriate geographic aggregates. |
| Province/territory casualty maps | **Separate aggregate route**. | Use an acquired and reconciled provincial series with verified units, definitions, vintage and denominators; do not attach aggregate geography to individual NCDB records. |
| Accident likelihood / occurrence probability | **Unsupported in phase one**. | Need a compatible complete observation frame, traffic/exposure measures, reporting coverage and true zero-crash intervals. Nonfatal injury records are not non-accident controls. |
| Infrastructure or policy recommendations | **Descriptive groundwork only**. | Validate substantive associations and geographic/exposure context before recommendations; causal effectiveness requires an appropriate study design beyond these records. |

## Required decisions before modeling

- Confirm the event-key interpretation with authoritative documentation; preserve source-specific lineage regardless. Never join releases on case ID alone.
- Approve a modeling-grain contract and explicit exception handling. Keep raw segments intact; quarantine unresolved or conflicting identities for person/vehicle tasks and report their exclusions. A collision can remain usable for condition-only severity modeling even if a person or vehicle attribute is unresolved, provided those uncertain aggregates are not used as predictors.
- Establish a condition-only feature allowlist and prediction-time rationale. Exclude `P_ISEV`, casualty-derived totals, outcome-related aggregates and IDs. Collision configuration and vehicle count require an explicit availability argument or a separate retrospective model.
- Define chronological development, validation/calibration and untouched test periods after considering the observed 2020–2021 shift. Keep every segment from an event in one partition. Fit transformations only on development data.
- Resolve asterisk meanings and the 1999/2000 person-outcome coding shift before treating those fields as numeric or comparing person trends.
- Reconcile source-version-sensitive benchmarks using matching definitions, units and vintage. The three supplied Transport Canada views share NCDB lineage and are not independent validation populations.
- Treat the stable structural checks as future automated tests: manifest checksums, one selected release per year, expected schema and year, valid candidate event keys, consistent event outcomes, and exception counts at every intended modeling grain. Do not enforce fixed historical volume or missingness thresholds as if recording behavior were stationary.

No production modeling table, fitted model, causal claim, or road-safety recommendation is produced in this phase.

## Completion checks and remaining verification limit

The final audit covers all 23 selected annual files plus the separately marked 2019 comparator; the stored code fingerprint matches the executed audit source. All **25 record/dictionary/comparator originals** passed size and SHA-256 verification. The consolidated verifier checked **46 preserved assets/extracts**, including the catalog snapshot and aggregate inputs, and validated aggregate extract-to-original and capture-provenance hash links. The aggregate offline reproduction path verified its 15 original HTTP captures and five extracts. **Six focused regression tests passed**, covering coded states, grain/conflicts, cache/manifest handling, corrupted catalog bytes, incomplete audit rejection and preservation of source disagreements.

The companion notebook executed all **seven code cells** from top to bottom using the dedicated project interpreter; its table outputs and notebook structure were validated. Rendered visual inspection was not completed because browser URL policy blocked the local HTML preview. No figures were authored in this phase, and no visual-inspection claim is made. This limitation does not replace or diminish the executed data and integrity checks described above.

## Audit validation

The full audit executed successfully against all 23 selected annual files and the separate 2019 CSV comparator; its source and code fingerprints match the saved machine summary. The three focused regression tests passed, covering dictionary sentinel states, conflicting/repeated identities and collision targets, and cache rejection of changed manifest checksums or selection roles. All seven code cells in the saved companion notebook executed in order with the dedicated project interpreter and retain their results. Jupyter required an approved local execution outside the socket-restricted sandbox; a temporary kernel specification avoided a global kernel installation.
