# Reference benchmarks and availability

`collision_codebook.json` is a field-domain reference, not a numerical benchmark. It transcribes the eleven collision attributes from English pages 1–6 of the supplied NCDB dictionary, pins the PDF checksum, and separates unknown, unavailable, residual other and top-coded values. The condition-quality audit uses it without recoding production data. One dictionary does not establish invariant historical or jurisdictional coding practice; see `docs/conditions_quality.md`.

Reviewed **2026-10-15**. References keep their original counting unit, population and source release. The production collision and casualty pipelines continue to read the existing files below; their schemas and values were preserved during the source-version repair.

| File | Counting unit and scope | Permitted use |
| --- | --- | --- |
| `tractor_collision_benchmark.csv` | Unique fatal/injury tractor-trailer collisions, Canada, 2012–2021 | Collision reconciliation only |
| `tractor_vehicle_benchmarks.csv` | Tractor-trailer vehicle involvements in fatal collisions, Canada, 2018–2023 | Separate vehicle reconciliation; **never append to collision counts** |
| `tractor_occupant_benchmarks.csv` | Published deaths/injuries among tractor-trailer occupants, Canada, 2017–2021 | Occupant reconciliation; excludes people in other vehicles and vulnerable road users |
| `national_road_safety_benchmarks.csv` | All-vehicle collision or person aggregates, Canada; measure/unit explicit on every row | National context and source-vintage comparison; no semi-specific extension |
| `provincial_tractor_vehicle_benchmarks.csv` | Tractor vehicle involvements, Saskatchewan and NWT, 2024 | Separately scoped provincial comparisons; no national fill |
| `data_availability.csv` | Evidence/status for recent-year sources; **not numerical observations** | Public availability and acquisition-gap register |
| `benchmark_catalog.csv` | File/series metadata and source links | Scope, release and provenance lookup |

## Source definitions and release handling

`tractor_collision_benchmark.csv` transcribes the **tractor-trailer** fatal and injury collision columns of Table 1 in Transport Canada's [Commercial vehicle collisions in Canada, 2012–2021](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021), published 2023-11-16 and accessed 2026-10-15. This counts collisions; Table S8/S11 vehicle involvements have a different grain. Its operational `V_TYPE` filter and NCDB extract vintage are not explicit. Differences remain visible rather than being corrected to the publication.

`tractor_occupant_benchmarks.csv` retains two published occupant series separately: Table 12 of the [2021 commercial-vehicle report to Parliament](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament) (prepared May 2026) and [2021 traffic collision statistics](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2021/canadian-motor-vehicle-traffic-collision-statistics-2021). They differ for 2019 and 2021 fatalities. Unusual seating-position treatment remains unverified. Broad commercial-vehicle victims cannot validate the tractor subset.

`tractor_vehicle_benchmarks.csv` transcribes the tractor-trailer row in [TDIH 2024 Table S11](https://tdih-cdit.tc.canada.ca/en/addendum-tables/2024/table-s11-vehicles-involved-fatal-collisions-vehicle-type-2018-2023). It preserves **2022 revised (R)** and **2023 estimated (E)**. Ontario/Alberta are preliminary for both years; New Brunswick was estimated. The report year is 2024; the latest collision reference year is 2023. Page-modified dates are not asserted to be publication dates.

`national_road_safety_benchmarks.csv` keeps [TDIH 2024 Table S6](https://tdih-cdit.tc.canada.ca/en/addendum-tables/2024/table-s6-road-casualty-collisions-fatalities-and-injuries-rates-10000-mvr-0) and the [2024 annual traffic report](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024) separate. The latter is now verified and listed as published **2026-10-15** by the [official index](https://tc.canada.ca/en/road-transportation/statistics-data); it revises earlier years. For example, 2023 fatalities are 1,964 in S6 and 2,000 in the 2024 report. These are separate official vintages, not duplicates to average or reconcile by overwriting. Serious injuries are a subset of total nonfatal injuries and must not be added to them.

`provincial_tractor_vehicle_benchmarks.csv` transcribes SGI Table 6.1 and NWT Figure 6.1 using their published vehicle names and geography. Different reporting systems and property-damage thresholds prevent direct pooling. Each all-severity total includes its property-damage, injury and fatal vehicle involvements; these remain vehicle counts.

## All people harmed in tractor-involved events

No independently verified external series in these files counts **all people harmed in the road-tractor subset**. The project's derived `data/derived/casualties/annual_counts.csv` and `annual_group_counts.csv` provide that analysis using source-record resolution scenarios. They are project outputs, not external benchmarks. Do not substitute tractor-occupant counts, broad commercial-vehicle counts or national all-vehicle counts for this target.

## CSV conventions

New numerical files include source ID/release, reference year, geography, population, measure, unit, count, source status, publication date when verified, page-modified date when observed, access date and direct URL. Blank dates mean unverified/not supplied; they do not imply an unpublished source. Existing compact benchmark schemas remain compatible; `benchmark_catalog.csv` supplies their scope metadata. New tables are descriptive references and are not automatically joined into production observations.

`data_availability.csv` distinguishes published aggregates, previously verified interactive tables, access blocks, and records **not publicly found in this bounded review**. It makes no claims about internal holdings, release promises or availability on request. See [the availability review](../../docs/data_availability.md) for decisions and follow-up using public sources only.
