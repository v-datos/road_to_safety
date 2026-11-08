# Independent exposure compatibility and statistical methods review

Reviewed 2026-10-17. Role: statistical methods and numerator compatibility reviewer. This review makes no changes to source records, collision tables or casualty reconstruction. It does not calculate exposure-adjusted rates.

## Decision

**Do not promote the candidate denominator to a validated primary measure of national road-tractor driving risk.** The current evidence supports retaining it as exposure context and, if calculated, an explicitly named **model-normalized sensitivity analysis** for overlapping years. This is a substantive compatibility decision, rather than an instruction to abandon exposure adjustment.

The relevant distinction is between a measurable arithmetic ratio and an established population risk rate. A ratio can be reproducible while its interpretation remains conditional on unverified coverage and model assumptions. In particular, matching calendar years does not establish matching vehicle populations, travel geography or reliable year-to-year exposure changes.

## Evidence inspected

The local [dataset contract](dataset_contract.md), [event validation](dataset_validation.md), [source revision validation](source_revision_validation.md), [analysis plan](analysis_plan.md) and [research questions](research_questions.md) establish the numerator and outstanding source limitations.

The denominator candidate is Transport Canada's [2021 annual report to Parliament](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament), exposure section, Table 10 and Figures 28–31. Table 10 reports modeled tractor-trailer distance for 2015–2021, in millions of vehicle-kilometres; Figure 29 additionally displays estimates for 2005–2021. The present audit focuses on Table 10 overlap. The class is described as exceeding 15,000 kg. Its estimates derive from an econometric model using CVS, CVUS and Statistics Canada inputs. The report distinguishes these estimates from directly observed collision information. Its values increase through the pandemic years; that interpretation remains model dependent. Footnote 5 defines NCDB tractors as including operation without semitrailers; it does not independently specify how the distance model handles attachment. These statements concern this report vintage, rather than a validated current exposure series.

The original CVS sampling population is Canadian-registered vehicles, drawn from provincial and territorial registration lists. Territories collect odometer information without the same trip-log detail. These are properties of a model input; they do not prove the final model's geography. [NRCan CVS methodology](https://oee.nrcan.gc.ca/publications/statistics/cvs/2009/annexb.cfm?wbdisable=true) and [Statistics Canada CVS documentation](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=80421).

## Compatibility matrix

Statuses distinguish **pass** (supports the specified use), **approximate** (related populations or measurements, with an unresolved boundary), **unknown** (not established), and **fail** (does not support the proposed claim). An unknown is not evidence that coverage is absent.

| Dimension | Numerator and denominator assessment | Status | Consequence |
| --- | --- | --- | --- |
| Numerator grain | Production events are unique source/year/case keys. At least one recorded type 08 marks tractor involvement. | Pass for observed events | Preserve one count per collision; use the strict subset as sensitivity. |
| Population boundary | The report uses the same NCDB tractor definition for collision statistics. The distance-model class has a weight boundary whose exact mapping is unverified; the event schema cannot impose it or identify attachment. The label “tractor-trailer” alone does not prove bobtail distance is excluded. | Approximate | Cannot assert exact equivalence or silently rename the numerator as attached-semitrailer events. |
| Travel location | Events occur on Canadian public roads. A Canadian registration sampling frame alone does not establish whether the final exposure includes overseas travel or foreign-registered vehicles' domestic travel. | Unknown | Require explicit domestic-travel accounting before a primary population-risk interpretation. Do not assume either inclusion or exclusion. |
| Territorial coverage | Numerator scope is national. Input-survey designs differ across jurisdictions; final model treatment has not been verified. | Unknown | National labeling alone is insufficient for exact geographic compatibility. |
| Calendar overlap | Annual event counts exist for all Table 10 years. | Pass, 2015–2021 | Join by year only after preserving source vintages. Do not extrapolate to the intended 2016–2025 decade. |
| Event severity | Current public microdata covers fatal and injury collisions, excluding property-damage-only events. | Pass for casualty-event rates; fail for all-accident rates | Name the event class explicitly and display fatal and injury numerators separately. |
| Event count versus distance | Unique collision events divided by vehicle-distance is a coherent system incidence measure when the population and geography match. | Pass in principle | Units alone do not invalidate the calculation; the matching conditions remain unresolved. |
| Individual-vehicle risk | A collision with two tractors counts once in the event numerator and twice in an involvement numerator. | Fail for interpreting event rate as vehicle-involvement rate | Reconstruct/validate a separate involvement series if that is the target estimand. |
| Observed versus modeled exposure | A model estimate is not a direct census of distance; uncertainty in its trajectory propagates to rates. | Approximate | Label any result model-normalized, not observed risk per kilometre. |
| Model specification and uncertainty | This review has not established the model equation, coefficients, fit diagnostics, extrapolation choices or covariance/prediction uncertainty. | Unknown | No complete uncertainty interval or independent model replication is currently justified. |
| Pandemic response | An estimated growth path does not establish actual exposure during 2020–2021. Nor does the absence of a downturn establish model error. | Unknown | Separate pre-2020 and pandemic-inclusive results; do not infer pandemic effects from the ratio. |
| Revisions and provenance | Source files and event releases are pinned locally. Denominator vintage must be pinned independently and cross-report comparisons documented. | Pass for numerator; conditional for denominator | Record report date, table, units, extraction, checksum and any changed overlap values. |
| External event reconciliation | Fatal benchmarks match for 2012–2021; injury-event gaps persist in 2013 and 2019, two events each. | Approximate | Relevant overlap sensitivity is 2019; retain both observed and publication-reference numerators separately. Never patch records. |
| Latest-decade question | Event microdata ends in 2021; the candidate does not supply exposure through 2025. | Fail | A historical sensitivity cannot answer the original latest-decade question. |

## What event/vehicle-distance does and does not mean

Let `E_y` count distinct fatal/injury events involving at least one recorded tractor in year `y`, and `K_y` be compatible tractor vehicle-distance in kilometres. Then `10^9 E_y / K_y` describes **tractor-involved casualty events per billion tractor vehicle-kilometres**. This is a system-level incidence measure. There is no dimensional requirement to replace events with vehicles merely because the denominator is vehicle-distance.

For a different question, let `I_y` count tractors involved in those events. Then `10^9 I_y / K_y` describes **tractor involvements in casualty events per billion tractor vehicle-kilometres**. It answers an involvement-frequency question. With multiple tractors in an event, `I_y` and `E_y` differ. Neither numerator establishes fault. Fatal events also remain distinct from the number of people killed.

The production table has a `road_tractor_vehicle_count` field based on distinct known vehicle IDs. That field is useful for a future involvement audit, but simply summing it is not automatically a complete national vehicle series: unidentified tractors and conflicting vehicle types must be considered. Reconciliation to the portal or published vehicle tables requires comparable counting rules and source vintages. An agreement would check the numerator; it would not resolve exposure geography.

For the candidate denominator, use `Khat_y` and state the approximation in the label. A constant multiplicative mismatch changes rate levels but cancels from endpoint rate ratios. A mismatch that changes over time changes the estimated trend. Stability of an unknown mismatch is an assumption, not a validation result.

## Allowed and disallowed conclusions

### Allowed now

- The validated historical public releases contain the reported event counts, with their documented quality flags and benchmark gaps.
- The candidate provides a related modeled measure of tractor activity and deserves a sensitivity calculation rather than automatic rejection.
- An explicitly conditional calculation can describe how observed event counts change relative to that particular modeled exposure series.
- Fatal-event share among casualty events remains a separate, exposure-free descriptive measure; its decomposition does not validate a distance denominator.

### Allowed only after calculating and checking the sensitivity

“Observed tractor-involved fatal/injury events per billion kilometres of the specified modeled exposure series changed by X over Y–Z. This calculation assumes sufficiently stable population and geographic compatibility and is not a validated estimate of the change in national individual-tractor driving risk.”

Use the actual result and years in place of the placeholders. Show event counts and exposure alongside the ratio, so changes in the numerator and denominator are inspectable.

### Not supported

- “Semi accident risk fell/increased by X” without the qualifications above.
- A causal explanation involving regulation, driver training, freight growth or the pandemic.
- Rates for all crashes, individual driver fault, all-person death risk, road-user-specific exposure or weather-specific risk from these inputs alone.
- Treating vehicle involvement totals through 2023 as additional collision records, or extending these historical ratios to 2025 without exposure for those years.
- Treating a counting-process confidence interval conditional on fixed exposure as a complete interval accounting for denominator uncertainty.

## Gates for a primary exposure-adjusted result

1. Establish that the denominator target covers the same domestic road travel and vehicle population, including tractor-only operation, weight boundary, territories and foreign-registered vehicles. If a component is excluded, quantify or explicitly bound the difference using authoritative evidence rather than assuming it is negligible.
2. Preserve a specific denominator release and reconstruct its stated units. Keep Table 10 rounding distinct from higher-precision figure descriptions. Do not silently combine model vintages or treat publication years as observation years.
3. Find public model documentation or validation evidence sufficient to assess year-to-year behavior, including 2020–2021. Missing documentation remains an explicit limitation; this project will not contact anyone.
4. Validate the selected numerator estimand independently. Keep observed and strict events, the 2019 publication alternative and any future vehicle-involvement reconstruction separately labeled.
5. If a sensitivity is produced, pre-specify historical overlap, pre-2020 comparison and pandemic-inclusive comparison. Avoid an arbitrary uncertainty band presented as empirical confidence. If illustrative denominator scenarios are used, name them as assumptions.
6. Revisit the decision only when evidence changes. A small numerical residual or a smooth rate trend cannot establish population compatibility.

## Recommended immediate implementation

Complete a source-backed denominator register and record the remaining unknowns. On the evidence reviewed here, a **historical model-normalized sensitivity is permissible as a predeclared follow-on**, while a **validated primary driving-risk series is not**. The current audit should finish with the compatibility decision and provenance checks; it does not require calculating that ratio. Keep the original national event and harm findings as the primary results until the gates above are met. A context-only decision is also defensible if the geographic or model gaps prevent the sensitivity from being useful; do not obscure those gaps by calling the ratio fully exposure-adjusted.
