# Initial review of supplied sources

**Historical planning snapshot.** Acquisition and the full-file audit were subsequently completed. Use the [verified source inventory](source_inventory.md), [quality assessment](data_quality_assessment.md) and [aggregate audit](aggregate_source_audit.md) for current status. The initial observations below describe the earlier planning review.

Reviewed October 17, 2026. This is a source-feasibility review for planning. No datasets were downloaded, tables extracted, aggregate calculations performed or models trained.

## Supplied sources and assigned roles

| Source | Verified during setup | Planned role | Remaining check |
| --- | --- | --- | --- |
| [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-0-0&l=en) | Official overview, FAQ and variable-selection page describe national aggregate queries, including condition, time, vehicle and person dimensions | Condition/time profiles and comparable aggregate checks | Query exact years/measures; inspect total/category handling; archive exports and source vintage |
| [Motor Vehicle Casualties Dashboard](https://tc.canada.ca/en/road-transportation/statistics-data/2025/motor-vehicle-casualties-dashboard) | Public text displays fatalities/injuries for 2014–2023, plus timing and demographic breakdowns; user guide describes filtering | Temporal and demographic context | Audit interactive coverage, exports and filters; do not assume text and interactive states match |
| [Transport Canada statistics and data](https://tc.canada.ca/en/road-transportation/statistics-data) | Official index links the dashboard, reports and NCDB; a 2024 collision statistics publication is listed | Discover current/historical benchmarks and geographic/exposure context | Select publication versions and preserve definitions and revision notes |

The supplied links are sufficient to begin a source audit. They are entry points into related NCDB products, rather than three independent datasets whose observations can be concatenated.

## Source-specific observations

### NCDB Online

The [overview](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/) describes selected fatal/injury collision variables and generated count tables. The [FAQ](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-5-0&l=en) confirms national scope and excludes collision-identifying locations. Its underlying-data link is a discovery lead; no training release was acquired through it.

The [variable-selection page](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-1-0&l=en) exposes additional conditions such as light and speed limit. Their availability in this aggregate interface does not prove they exist in downloadable event records. Exact year/category selections and query-specific population units still need verification.

The exact supplied landing URL failed in the web-fetch tool. The official overview and linked FAQ/selection pages were accessible, so source discovery could continue. This is an access result for that URL/tool, not a conclusion that NCDB Online is unavailable.

### Motor Vehicle Casualties Dashboard

The [dashboard page](https://tc.canada.ca/en/road-transportation/statistics-data/2025/motor-vehicle-casualties-dashboard) lists year, month, weekday, hour, age, gender and road-user class as its seven factors. The visible text's 2014–2023 range is a checked page observation, not a guarantee of complete downloadable records. The [user guide](https://tc.canada.ca/en/road-transportation/statistics-data/motor-vehicle-casualties-dashboard-user-guide) explains filters and viewing charts as tables.

Use it for aggregate context and verification after matching population and vintage. Its reviewed page does not establish event-level training inputs or geographic coverage.

### Statistics index and linked 2024 publication

The supplied [index](https://tc.canada.ca/en/road-transportation/statistics-data) lists the 2024 collision publication with publication date October 15, 2026. Its linked [2024 report](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024) contains national collision/casualty history for 2005–2024 and provincial/territorial casualty rates for 2024. These support a candidate aggregate map and national context, with an appropriate boundary source.

Retain the report's preliminary/estimated-data notes, Manitoba reporting change, denominator methodology and small-jurisdiction rate instability. Detailed rate comparisons require these qualifications. A published exposure-adjusted casualty rate is neither a collision-level severity label nor a matched set of non-crash observations.

## Modeling and map implications

1. **Severity:** Locate and audit official event-level record releases and matching dictionaries as the first implementation milestone. The [public NCDB catalog](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) remains a candidate. Search metadata were visible, while direct catalog/dictionary fetches failed during setup; release contents and current training-year coverage are unverified.
2. **Descriptive analysis:** Acquire reproducible aggregate selections from the supplied sources, retaining source-specific coverage. Do not join separate marginal distributions to fabricate joint weather/time/person observations.
3. **Spatial analysis:** Begin with the linked publication's provincial/territorial aggregate rates, subject to comparability and boundary checks. Road-level hotspots need separate location data.
4. **Occurrence:** Keep this as the second modeling phase. Obtain compatible exposure and complete observations of both crash and zero-crash conditions; published national rates alone do not provide that training frame.
5. **Reconciliation:** The views share NCDB lineage and can reflect different release vintages. Compare like units and definitions, record revisions and preserve differences. Never force agreement or treat a later publication as proof of newer downloadable event records.

## Next acquisition checklist

- Pin exact source/query/publication versions and capture timestamps.
- Verify all available years separately for aggregates and training records.
- Select one record release per year and preserve originals/checksums.
- Match target and input fields to the correct dictionary.
- Record each aggregate measure's unit, population, totals and filters.
- Validate provincial/territorial rates and geographic boundaries before mapping.
- Update the data contract with actual fields and feasibility outcomes before training code is written.
