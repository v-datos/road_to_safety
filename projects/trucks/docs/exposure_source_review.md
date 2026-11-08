# Tractor exposure source review

Audit date: **2026-10-17**, America/Edmonton. This is the source and provenance component of the exposure compatibility audit. No collision rates were calculated here, and no source was contacted.

## Decision

Retain Transport Canada's annual modeled tractor-trailer distance as a **candidate exposure series**, with explicit eligibility status `not_validated_for_ncdb08_rates`. The source provides inspectable annual numbers, but the public documentation reviewed does not establish a fully matched denominator for our Canadian public-road NCDB type08 population.

This is a limitation of the proposed use, not a finding that the official estimates are erroneous. A rate would inherit the model's scope and assumptions. Merely obtaining seven numeric denominators does not validate those assumptions.

## Source and extraction

The governing source is [Commercial vehicle safety in Canada – 2021 annual report to Parliament](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament), published May 2026; the HTML modification date is June 25, 2026. Its [official PDF](https://tc.canada.ca/sites/default/files/2026-06/2021-CMVsafety-En.pdf) places Table 10 on **printed page 45, physical PDF page 57**. The exposure-method section starts on **printed page 44, physical page 56**.

The unit is **million vehicle-kilometres**, not vehicles, tonne-kilometres, passenger-kilometres or billions of kilometres. The model's named sources are CVS, CVUS and unspecified Statistics Canada tables. The exposure class is tractor-trailers **over 15,000 kg**; the weight concept for that cutoff is not specified in the section. The collision definition in footnote 5 includes tractors with and without semitrailers. Neither the label nor the cutoff establishes whether the exposure model treats detached tractors consistently with that collision definition.

| Calendar year | Table 10 tractor VKT, million km |
|---|---:|
| 2015 | 34,203.5 |
| 2016 | 35,898.0 |
| 2017 | 37,651.3 |
| 2018 | 39,494.7 |
| 2019 | 41,434.4 |
| 2020 | 43,463.5 |
| 2021 | 45,593.8 |

The seven records are in [tractor_exposure_candidates.csv](../data/reference/tractor_exposure_candidates.csv). Python's HTML parser extracted the row from the preserved official HTML, and the values were checked against the PDF. All seven HTML Figure 28 values round to Table 10's one decimal precision; the extra figure decimals are retained only in the [metadata](../data/reference/tractor_exposure_candidates.metadata.json). They do not represent additional validated measurement accuracy.

The [earlier official report](https://tc.canada.ca/sites/default/files/2022-01/commercial-vehicle-safety-canada-2012-2018.pdf), Table 28, printed page 85 / physical page 97, gives identical overlapping 2015–2018 tractor values. This establishes stability of those four published cells. It does not establish a model re-estimation date, unchanged inputs or validation of forecasts for later years.

## Checks and limitations

| Check | Evidence and outcome | Consequence |
|---|---|---|
| Annual grain | Seven distinct series/year keys, 2015–2021; seven positive numeric values; no missing cells. | Usable as a candidate reference table. No 2022–2025 values are fabricated. |
| Source agreement | HTML Table 10 and PDF Table 10 agree; Figure 28 agrees after rounding. | Transcription and unit checks pass. |
| Vehicle boundary | Model cutoff >15,000 kg; our public type08 records do not expose a corresponding weight field. | **High severity:** matched population cannot be demonstrated by filtering the current extract. Confidence high in this documentation gap. |
| Geography and border accounting | Canadian context is clear, but the model section supplies no explicit territorial coverage, treatment of Canadian vehicles abroad, or foreign vehicles in Canada. | **High severity:** national labels alone do not establish travel on exactly the roads/population covered by the numerator. Coverage remains unknown. |
| Road boundary | No explicit public-road-only model restriction was located. | An NCDB public-road event numerator cannot automatically be paired with all activity of a registered fleet. |
| Model reproducibility | No equations, coefficients, input table identifiers, estimation cutoff, validation statistics or uncertainty intervals were located in the report. | **High severity:** cannot independently recreate the denominator or quantify model uncertainty from this publication. |
| Numerator grain | Exposure is vehicle distance; the report separately publishes vehicle involvements, whereas our principal dataset counts unique events. | Define either events per tractor-km or tractor involvements per tractor-km explicitly. They are different estimands; multi-tractor events prevent treating them as interchangeable. |
| Newer coverage | No comparable 2022–2025 tractor-specific VKT was located in the bounded official-source checks below. | Current candidate cannot support a through-2023 vehicle trend rate or latest-decade risk rate. |

These limitations apply before selecting a rate's scale, fitting a trend model, or interpreting a change. Broad registrations and freight volume cannot repair population mismatch simply by serving as substitute denominators.

## Pandemic-period inconsistency

The candidate's 2019–2020 increase is **4.897%**, followed by **4.901%** in 2020–2021, calculated from the published cells. The report explicitly discusses its model's lack of a pandemic decline and indicates the issue will be monitored. Smooth growth is not, by itself, a data error or evidence of actual observed traffic growth.

A separate [Transport Canada commercial-collision fact sheet](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021), section **Commercial vehicle exposure and involvement rates**, modified November 16, 2023, reports broader commercial-vehicle VKT decreasing **12%** in 2019–2020 and increasing **16%** in 2020–2021, reaching **48.9 billion km** in 2021. Its population includes straight trucks, tractor trailers and buses excluding school buses.

Those are different published populations and vintages. They are not interchangeable tractor denominators, and the fact sheet supplies no published tractor split or bridge to Table 10. The available evidence therefore does not resolve whether the directional disagreement reflects coverage, estimator choice, revisions, or some combination. It also does not establish that either series measures the same target as our numerator. Do not interpolate a tractor series from these broad percentages, splice them onto Table 10, or treat the disagreement as proven pandemic behavior of tractors.

## Bounded newer-source search

The [Transport Canada motor-carrier index](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers) linked annual reports for 2021, 2020 and 2019 when retrieved. Official-domain web searches combined tractor/tractor-trailer with VKT or vehicle-kilometres and each of 2022, 2023, 2024 and 2025. A Government of Canada publications search sought a newer commercial-vehicle annual report. No newer comparable tractor-specific distance table was located. This is a scoped search result, not proof that no other or unpublished estimate exists.

[TDIH 2024 Table S6](https://tdih-cdit.tc.canada.ca/sites/default/files/addendum-tables/2024/S6-en.pdf) provides **all-vehicle** estimated VKT through 2023. That is useful national context, not a tractor-specific denominator. Likewise, recent publication or metadata modification dates do not extend the collision or distance reference years of a historical series.

## Preserved evidence and remaining gate

The original HTML, PDF, companion fact sheet, motor-carrier index and older-vintage PDF are preserved under ignored `data/raw/exposure/`. The tracked metadata records each original URL, local retrieval date, byte size and SHA-256. Derived plain text is retained alongside the PDFs for inspection; it is not an alternative source vintage.

The main audit should combine this source review with the [independent methods review](exposure_methods_review.md) and numerator-grain checks. Before a primary rate is approved, public evidence must resolve the vehicle and geographical boundary and provide sufficient model information to interpret time changes, particularly 2020. If those gaps remain, the defensible output is the documented audit decision and counts. An explicitly assumption-based sensitivity measure would require its own predeclared assumptions; it should not silently become the project's main risk result.
