# Recent-year availability and benchmark separation

As of **2026-10-15**. This implements source repair Steps 5–6. Research used publicly accessible official websites only. No emails, contact requests or communications were sent; none is part of this plan.

## Decisions

1. Keep the validated national event/person study at the years supported by public record files. No 2022–2025 national annual NCDB record file was located in the catalogue reviewed.
2. Keep each external series separate by **counting unit, population, geography and release**. Vehicle involvements and broad national totals cannot extend a unique tractor-collision series.
3. Add verified 2024 national context and the separate 2022–2023 tractor vehicle reference, retaining revision flags and vintages.
4. Treat provincial sources as individually scoped future studies until their schemas and definitions are validated. Do not estimate national missing records by summing selected provinces.
5. Preserve explicit missing years. Recheck public sources when a new release is actually available; no automated monitoring or outreach has been created.

## National evidence

### Public records

The [NCDB Open Government package](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) contains 51 resources in the inspected metadata, last modified 2025-12-17. Annual resources reach 2021; none is labelled 2022–2025. The 2021 French file is usable; its English counterpart has no URL. Metadata and the source-version audit are retained in the project's raw/source audit records. The web reader returned 403 on the catalogue landing page; the separately obtained package metadata and the search-index resource listing support the resource assessment.

**Interpretation:** those years' public records were not found in this review. This is not evidence that the underlying national database has no such records or that research access is available on request.

### A verified 2024 publication changes the earlier assessment

The [official statistics index](https://tc.canada.ca/en/road-transportation/statistics-data) now lists the [2024 traffic collision report](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024) with publication date **2026-10-15**. The full report resolves using the URL linked by the index. Its all-vehicle 2024 totals are **1,848 fatal collisions, 93,317 personal-injury collisions, 2,050 deaths, and 130,551 nonfatal injuries**. The 9,357 serious injuries are included in total injuries. These are aggregate national measures, not tractor-specific records.

The same release revises earlier years. Thus the old statement that 2023 is the newest verified annual national publication is superseded. The new report still cannot answer who was harmed in tractor-involved collisions during 2022–2024. No 2025 national collision report was located in the official index and bounded official-domain search.

### Separate vehicle reference through 2023

[TDIH 2024 Table S11](https://tdih-cdit.tc.canada.ca/en/addendum-tables/2024/table-s11-vehicles-involved-fatal-collisions-vehicle-type-2018-2023) reports **204 tractor-trailer vehicles in fatal collisions in 2022 (revised)** and **212 in 2023 (estimated)**. Ontario/Alberta are preliminary and New Brunswick estimated. A fatal event may involve multiple tractors. These values belong in `tractor_vehicle_benchmarks.csv` and cannot be appended to `tractor_collision_benchmark.csv`.

[TDIH Table S6](https://tdih-cdit.tc.canada.ca/en/addendum-tables/2024/table-s6-road-casualty-collisions-fatalities-and-injuries-rates-10000-mvr-0) reports national all-vehicle casualty collisions, deaths and injuries through 2023. It is retained as a distinct vintage in `national_road_safety_benchmarks.csv`. The earlier NCDB Online review exposed years through 2023 and tractor vehicle/occupant measures; its unarchived query is explicitly marked previously verified, not newly re-executed here.

## Provincial evidence and restrictions

| Source checked | Verified year and scope | Database decision |
| --- | --- | --- |
| [SGI 2024 Table 6.1](https://sgi.sk.ca/documents/37148/5370559/06%2B-%2BVehicle%2BFactors-2024_FINAL_SECURED.pdf/0401c88e-a6d9-1ff9-9ac9-573b18494082?t=1764949226124) and [index](https://sgi.sk.ca/news?cat=statistics&topic=collision-statistics) | Saskatchewan 2024: 1,251 semi-trailer power-unit vehicle involvements: 1,006 property damage, 221 injury, 24 fatal. Index newest collision report is 2024. | Verified separate provincial vehicle reference; no 2025 report found in this index check. |
| [NWT 2024 Figure 6.1](https://www.inf.gov.nt.ca/en/content/2024-nwt-traffic-collision-facts-0) | 12 road-tractor vehicle involvements: 7 property damage, 5 injury, 0 fatal. | Verified territorial vehicle reference; no claim about current 2025 release status. |
| [ICBC May 2026 release](https://icbc.com/about-icbc/newsroom/2026-05-26-data) | Confirms updated 2025 crashes/injuries and heavy-vehicle statistics. | Candidate BC study; tractor-only class/schema unverified. The announcement schedules 2025 police/fatality reconciliation for fall 2026; actual later availability was not established here. |
| [SAAQ 2025 report](https://saaq.gouv.qc.ca/blob/saaq/documents/publications/Bilan-Routier-2025-Faits-Saillants.pdf) | Quebec 2025 person outcomes for heavy trucks and road tractors combined. | Useful separate contextual series; not tractor-only event data. |
| [Quebec event-data portal](https://www.donneesquebec.ca/recherche/fr/dataset/rapports-d-accident) | Current access blocked by anti-bot JavaScript. | Latest reference year currently unverified; earlier 2022 inventory is not proof the source still stops there. |
| [Ontario preliminary 2024 PDF](https://www.ontario.ca/files/2026-02/mto-orsar-preliminary-selected-statistics-en-2024-2026-02-05.pdf) | Direct PDF returned 403 during this check. Earlier inventory identified a large-truck aggregate. | No numerical ingestion from unverified notes; class broader than tractors. |

Other provincial/territorial leads remain in [the earlier website inventory](website_database_review.md). They were not all re-audited here; their gaps are research tasks rather than evidence of nonexistence. This bounded verification is sufficient to prevent incompatible data from entering the national series. A harmonized provincial panel is a future analysis requiring explicit class/severity/reporting crosswalks and verified downloadable data.

## Deliverables and acceptance checks

- `data/reference/benchmark_catalog.csv`: scope/provenance for external and project-derived series.
- `data/reference/tractor_vehicle_benchmarks.csv`: six S11 observations, 2018–2023.
- `data/reference/national_road_safety_benchmarks.csv`: S6 and 2024 traffic-report observations, each release separate.
- `data/reference/provincial_tractor_vehicle_benchmarks.csv`: eight scoped 2024 vehicle observations.
- `data/reference/data_availability.csv`: year/source/grain/status register for 2022–2025 and provincial leads.
- Existing production benchmark schemas and figures are unchanged. No newer aggregates have been used to overwrite, pad or interpolate missing event/person records.

The repair completes the **availability assessment**, not acquisition of missing national records. The main rebuild uses the validated source manifest; these references provide evidence and context without changing its supported years.
