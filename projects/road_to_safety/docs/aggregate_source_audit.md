# Official aggregate sources: acquisition and feasibility audit

Audit date: **2026-10-17 America/Edmonton**. Original responses acquired 2026-10-18 03:31–03:32 UTC. Scope: all road users; acquisition and feasibility only. No models, inferred joint records or policy causal claims were produced.

## Evidence inventory and freshness

| Official source | Verified coverage and grain | Acquired evidence | Permitted analytical use |
|---|---|---|---|
| [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-0-0&l=en) | Variable-details domain explicitly lists **All years plus 1999–2023**. National aggregate queries of fatal/injury collisions; not geographic incident records. The 26-item Year label includes All years, not 2024. | Landing, FAQ, help, variable selector, measure items, year items/details, failed table-generation responses and bounded single-measure retry. | Supported variables and query design are verified. A native annual table/export was **not obtained**; do not treat error HTML as data. |
| [Motor vehicle casualties dashboard](https://tc.canada.ca/en/road-transportation/statistics-data/2025/motor-vehicle-casualties-dashboard) | **2014–2023**; fatalities and injuries as person counts; seven separate marginal tables for each outcome. Page modified 2025-12-11. | Original HTML containing public text alternative; 14 tables extracted. Native Power BI export not obtained. | National annual, seasonal, age, gender and road-user descriptions, subject to the reconciliation failure below. No geographic analysis or training data. |
| [Transport Canada statistics index](https://tc.canada.ca/en/road-transportation/statistics-data) | Index links a new **2024** annual report published **2026-10-15**. Footer date 2023-04-13 is not the latest linked publication date. | Original HTML. | Source discovery and publication provenance, not observations. |
| [Canadian Motor Vehicle Traffic Collision Statistics: 2024](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024) | **2005–2024** annual national collisions/casualties; 2024 provincial/territorial rates; age, road-user, seatbelt, urban/rural tables; 2005–2024 licensed-driver and vehicle-registration series. | Original HTML, all 11 tables as cell extracts; normalized 20-row annual national series and 14-row rates table (Canada + 13 jurisdictions). | Descriptive annual charts, national comparisons and province/territory choropleths with external boundaries. Qualified rate comparisons and exposure context. |
| [Dashboard user guide](https://tc.canada.ca/en/road-transportation/statistics-data/motor-vehicle-casualties-dashboard-user-guide) | Modified 2025-03-07; describes year slider, six categorical filters, focus mode, show-as-table and two dashboard pages. | Original HTML. | Explains the dashboard's supported interactions. Does not establish a downloadable row-level dataset. |

All 15 original captures and five generated extracts have SHA-256, original URL, byte length, UTC acquisition time, small HTTP response metadata and acquisition type recorded in `data/reference/aggregate_sources.json`. Full response headers and wizard POST state are preserved locally in hash-linked `data/raw/aggregates/*.provenance.json` sidecars; transient cookies and ASP.NET state are excluded from the versioned inventory. Original bytes are in `data/raw/aggregates/`. No files were copied from sibling projects. The registry distinguishes HTTP capture from HTML-table extraction. CSV files in `data/reference/aggregate_*.csv` are our derived extracts, **not native agency CSV exports**. They retain source hashes. The cell extracts preserve table/row/cell positions and footnote text; spanning headers are not flattened silently.

## Query/export inspection and access limit

NCDB's current selector exposes these dimensions:

- Collision date: Year, Month, Day of Week, Collision Hour.
- Collision details: Collision Configuration, Persons per Collision, Road Alignment, Road Surface, Roadway Configuration, Collision Severity, Traffic Control, Vehicles per Collision, Weather, Light Condition, Road Class I, Road Class III, Speed Limit, Pedestrians.
- Vehicle details: People in Vehicle, Vehicle Type, Vehicle Year, Vehicle Maneuver, First Impact Location.
- Person details: Injury Severity, Person Age, Person Position, Person Gender, Road User Class, Safety Device.

Measures are **Number of collisions, Number of vehicles, Number of persons, Number of injured, Number of fatalities**. These are different counting units. A vehicle/person dimension can condition a collision count; the requested measure must remain explicit. The displayed dimensions include All/Unknown/Not applicable categories in some domains; do not equate domain size with the number of known classes. Current selector is controlling: the static help has older variable counts (e.g. 11 year items) and lists Day of Month, which the current selector does not show.

The documented wizard permits up to eight dimensions, including mandatory Year and Measures. Its help documents IVT, XLS, CSV, SSV and PDF table downloads, a download confirmation page and a cell-count limit without stating its current numeric limit. These are **aggregate table exports**, not evidence of incident microdata.

Public HTTP GETs and wizard Steps 1–2 succeeded. A default all-years/all-road-user query (only mandatory Year and Measures) reached a Transport Canada application error at Step 3: `Failed during Utility.Execute`. The attempted Step 4 also returned an error. One fresh-session retry with **Number of collisions only** failed at Step 3 as well. The original response/error IDs and complete form state were archived. This establishes an application/query failure observed through this acquisition route; it does not prove that the service is broken for every user or browser. CUA browser discovery returned an empty browser inventory, so interactive verification/export was unavailable. No native NCDB CSV/XLS was acquired and no NCDB numeric counts are claimed from those error pages. Working annual publication tables provide the reproducible national all-road-user aggregate evidence for this phase.

The dashboard embeds a public Power BI view in an `embed` element. The surrounding official HTML supplies the text tables. The linked guide documents “Show as a table” but not a file export; absent a usable browser, native visual export availability and live filter results remain **unverified**. No private/undocumented Power BI endpoint was queried.

## Quality checks and findings

### Checks completed

- Verified SHA-256 against every archived original and extract; the offline verification path makes no network requests.
- Parsed tables from original HTML, excluding superscript footnote markers from numeric cells while retaining full source text.
- Verified exactly **20 unique contiguous years, 2005–2024**, and six fields in the normalized national series. Numeric count cells parse as integers; no blank count cells in this extract.
- Verified **14 unique geographic labels** in 2024 rates: Canada plus each of the 13 provinces/territories. All six rates parse as numbers. No coordinates or lower-level geography were found in these tables.
- Compared all seven dashboard partitions for each outcome, including explicit Unknown and Not applicable rows.
- Compared overlapping annual dashboard/publication values and inspected definitions, revision markers, geographic notes and exposure-unit headers.
- Checked latest publication age and grain separately from page footer dates. Timeliness differs by source and cannot be represented by one universal “latest NCDB year.”

### High: dashboard injury road-user partition does not reconcile

The dashboard's annual injuries sum to **1,369,953** for 2014–2023. Month, weekday, hour, gender and age tables each sum to the same value. Its Road User Class injuries sum to **1,368,953**, a shortfall of **1,000** (approximately 0.0730% of the annual total), even after including the explicit Unknown count of 28,806. All seven fatality partitions sum to **18,867**. This is a directly observed source-text inconsistency; its cause is unknown. The live Power BI view was not verified, so the finding applies to the archived official text alternative. **Do not calculate road-user injury shares against the annual total as though the margin were complete.** Retain the table for audit and resolve against an authoritative corrected export before stakeholder comparisons. No category was changed or imputed.

### Medium: source vintages contain different revised values

Dashboard injuries for 2016 are **160,246**; the 2024 annual publication reports **160,248**, marked revised. Other overlapping annual fatality and injury counts match in the acquired tables. Do not concatenate sources and silently choose one value. Use the 2024 publication vintage consistently for annual reporting, preserve the dashboard independently, and label extraction and publication vintage. These aggregates are not strict row-level totals for an older microdata release.

### Medium: estimates, reporting changes and outcome definitions affect comparability

The 2024 publication states:

- Ontario and Alberta 2024 data are preliminary; New Brunswick data were estimated.
- Manitoba changed collision-report collection, capturing more minimal injuries in 2024. A resulting increase is not evidence of a proportional increase in collision risk.
- Newfoundland and Labrador data reflect reports received and processed by June 1, 2025.
- Serious injuries (hospital admission for treatment or observation) are estimated because several jurisdictions under-reported them. “Serious injuries” here is not automatically a record-level class in the public microdata.
- Fatalities use death within 30 days, except Quebec before 2007 used eight days. Personal injury collisions exclude collisions with a death under the corresponding definition. Total injuries include minimal through serious injuries, and **exclude fatalities**; serious injuries are a subset of total injuries.
- Smaller jurisdictions have volatile rates due to small samples.
- Urban/rural categories use road type or posted speed, with Alberta, New Brunswick, Manitoba and Saskatchewan using municipal corporate boundaries. Do not treat these as one harmonized physical-density measure.

### Low/medium: internal road-user percentage discrepancy

In the 2024 report's fatality counts by road-user class table, drivers are 990 of 2,050 (48.29%, displayed as 48.3%); its separate percentage-of-fatalities table reports drivers at 48.1% and Not stated/other at 3.8%, whereas the count table has 73 of 2,050 (3.56%, displayed 3.6%). Both source tables are retained. Prefer explicit counts for count-based calculations and flag the discrepancy before quoting the separate percentage table. Cause is unverified; no repair was made.

### Structural: missingness is not equivalent to blank-cell absence

The table extracts have numeric values but source categories include Unknown, Not applicable and Not stated. For example, the dashboard has 116 unknown fatality ages, 27,910 unknown injury ages, 266 unknown fatal collision hours and 11,632 unknown injury collision hours. These are substantive missingness categories, not zeroes. Category definitions and relevant denominators must be preserved. Aggregate margins cannot reveal cross-field missingness or record-level duplicate IDs; those checks belong to the acquired microdata audit.

## Feasibility decisions by expected outcome

| Intended result | Decision from these sources | Required constraint or next input |
|---|---|---|
| Severity model | **No training rows from these aggregate sources.** | Use independently acquired record-level NCDB data and its dictionary; never synthesize joint age/weather/time records by combining margins. Aggregate serious-injury counts do not create a serious-injury microdata label. |
| Accident likelihood | **Not supported as individual accident probability.** | Published population/VKT/licensed-driver rates are aggregate exposure context. They do not supply matched non-collision observations, segment traffic, trip exposure or model negatives. Phase two still needs suitable exposure and non-accident inputs. |
| Risk factors | **Descriptive correlations only**, subject to query availability. | Dashboard margins permit one-dimensional distributions, not adjusted effects. Marginal counts measure burden, not causal or exposure-adjusted risk. |
| National temporal charts | **Ready with qualifiers.** | Use 2005–2024 annual publication series. Dashboard 2014–2023 margins permit hour/weekday/month patterns with Unknown visible; the text tables alone do not supply year-by-month joint cells. |
| Geographic maps | **Province/territory rates feasible**, with a boundary file. | 2024 table has province/territory names; external authoritative geometry and explicit name/code matching are needed. Territories require uncertainty caveats. NCDB Online explicitly excludes data that identify collision location; no hotspot, municipality, road segment or point maps from it. |
| Infrastructure/policy recommendations | **Evidence framing ready; causal recommendation not yet justified.** | Use reporting changes and exposure limitations in analysis; validate factors using microdata and jurisdictional/infrastructure inputs before attributing effects. |

The rate table supplies fatality/injury rates per **100,000 population**, **billion vehicle-kilometres**, and **100,000 licensed drivers**. Population reference is Statistics Canada's Annual Demographic Estimates 2025; vehicle-kilometre rates use Transport Canada econometric calculations/estimates. The publication also supplies licensed-driver and vehicle-registration totals in **thousands**. The fatality-rate series is per **10,000 registered motor vehicles**. These denominators are not interchangeable and do not represent pedestrian/cyclist-specific exposure. The rate table provides rounded published rates, not exact underlying VKT or population rows; do not reverse-engineer them as exact denominators.

## Reproduction and stop condition

From the project directory, with its `src` package on Python's import path:

```sh
PYTHONPATH=src python3 -m road_to_safety.acquire_aggregates --offline
```

This verifies preserved hashes, regenerates the five derived CSVs and repeats numeric/domain/partition checks using the captured bytes. It reports the known reconciliation failure in the registry rather than silently changing values. For an initial acquisition into an empty capture directory, use the same command without `--offline`. The acquisition refuses to overwrite existing named originals. A later refresh should use a separately preserved acquisition directory rather than replace these bytes. It uses only Python's standard library and follows the public HTML wizard. If the wizard returns an application error, the refresh records that status and stops that query path. Any network/sandbox approval remains controlled by the execution environment.

The aggregate audit is complete with the precise native-export gap above. A useful follow-up is a later successful interactive all-years table export with explicit measure/all-road-user selection, then source-vintage reconciliation. It is not a prerequisite for auditing the separate record-level files or using the captured publication's verified annual series.
