# Exposure compatibility audit: road-tractor collisions and kilometres travelled

Completed 2026-10-17. Roles: transport exposure source researcher, independent statistical-methods reviewer, and project integration/verification. The task is to decide whether our event counts support a defensible comparison with road-tractor travel. A completed audit does not require approving a denominator.

## Decision

**The candidate is not approved for a primary national road-tractor driving-risk rate.** Preserve it as modeled exposure context. A separately declared historical **model-normalized sensitivity** is possible, with explicit class, geography and model assumptions; it would not be a validated observed risk series. No collision/exposure ratios were calculated in this phase.

Calendar years and units can be aligned. The vehicle-population and travel-geography boundaries, and the model's ability to represent annual changes, have not been established well enough for an unqualified risk conclusion. This is a high-confidence decision about the evidence available, not a finding that the denominator is necessarily wrong.

## Evidence and population

**Numerator:** unique `(source_id, C_YEAR, C_CASE)` public NCDB events on Canadian public roads, with at least one recorded vehicle type 08. Fatal and injury events are separate; property-damage-only events are excluded. Type08 includes road tractors with or without semitrailers. The public schema has no vehicle weight or registration-country field with which to enforce an exposure population boundary. Observed and strict cohorts are both preserved; source-version and residual benchmark limitations remain.

**Candidate denominator:** Transport Canada's [Commercial vehicle safety in Canada—2021 annual report to Parliament](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament), prepared May 2026. Table 10 contains econometric estimates for 2015–2021, in millions of vehicle-kilometres, for tractor-trailers described as over 15,000 kg. Figure 28 provides extra decimal places; Figure 29 also covers older years. The report's reference year is not its publication year. The model draws on CVS, CVUS and Statistics Canada inputs.

The [source review](exposure_source_review.md) documents exact locations, downloaded originals, model descriptions, alternative publications and the bounded newer-source search. The [independent methods review](exposure_methods_review.md) provides the full compatibility matrix and estimands. The [candidate register](../data/reference/tractor_exposure_candidates.csv) and [metadata](../data/reference/tractor_exposure_candidates.metadata.json) retain units, eligibility and provenance rather than being added to production inputs.

## Compatibility findings

| Dimension | Finding | Impact and disposition |
|---|---|---|
| Annual overlap | Table 10 and current events both cover 2015–2021. | Pass for this historical overlap. No extension to 2016–2025. |
| Vehicle boundary | NCDB 08 is design based and has no explicit weight threshold in the public code definition; model class is described as >15,000 kg. Exact mapping is unverified. | High analytical risk. Do not assume the below-threshold share or its stability. |
| Semitrailer attachment | The report explicitly includes tractors without trailers in its NCDB collision definition. Distance-model treatment is not independently specified. | Unknown, not proof that tractor-only travel is excluded. Do not silently treat the model as attached-semitrailer-only. |
| Road and fleet geography | Numerator concerns Canadian public roads. The underlying CVS uses Canadian registrations; final-model adjustments for foreign domestic travel, Canadian travel abroad and territories are not established here. | High analytical risk. Registration frame alone does not prove final geographic coverage. |
| Units and scaling | Table 10 uses millions of vehicle-kilometres. | Pass for arithmetic: billion km = published million km /1000. Numerical scaling cannot resolve population mismatch. |
| Event/involvement grain | Multiple tractors can occur in one collision. | Both event/VKT and involvement/VKT can be coherent, different measures when populations match. Do not interchange them. |
| Severity coverage | Public event data contains fatal/injury events only. | Pass for appropriately labelled casualty-event analysis; fails an all-accidents interpretation. |
| Denominator measurement | Econometric forecasting estimates, not directly observed annual travel totals. | Model-normalized interpretation only; no claim that modeled growth proves actual exposure growth. |
| Method and uncertainty | The inspected report does not supply enough detail to independently replicate the exposure model or its uncertainty. | High risk for risk-trend magnitude and inference. Do not treat fixed-denominator intervals as complete uncertainty. |
| Pandemic and source vintage | Related official commercial-travel descriptions differ from this model's increasing 2020 trajectory, with different scope and vintage. | Unresolved, not a demonstrated error or a reason to splice series. Separate pre 2020 and pandemic-inclusive sensitivity windows if a ratio is later calculated. |
| Numerator validation | Current counts are reproducible;2019 retains a two-injury-event published benchmark gap. | Carry observed/strict and separately labelled publication alternatives. Never patch events to make a rate fit. |
| Newer coverage | No newer compatible 2022–2025 tractor VKT series was located in the documented official-source search. | A contextual all-vehicle VKT or truck-registration series cannot fill the denominator gap. |

Unknown compatibility is not proof of incompatibility. Conversely, a related official label or matching calendar year is not proof of equivalence. The sources support a conditional comparison, not an unqualified population-risk estimate.

## Numerator checks and the estimand distinction

The direct event query in [notebook 07](../notebooks/07_exposure_compatibility.ipynb) preserves one event per collision and separately sums recorded known tractor vehicle IDs. It checks seven complete annual partitions, severity additivity, strict exclusions and multiple-tractor events.

| Year | Casualty events | Fatal | Injury | Known tractor involvements | Multi-tractor events | Strict exclusions |
|---|---:|---:|---:|---:|---:|---:|
|2015|3,075|194|2,881|3,282|161|0|
|2016|3,010|193|2,817|3,208|174|0|
|2017|3,178|216|2,962|3,445|208|2|
|2018|2,990|190|2,800|3,264|207|0|
|2019|2,775|196|2,579|3,040|187|0|
|2020|2,122|158|1,964|2,299|152|6|
|2021|2,276|169|2,107|2,459|152|1|

There are no flagged unidentified-tractor events in this seven-year query. Known-involvement totals are diagnostic; they have not been promoted to a fully reconciled external vehicle series. Vehicle-type conflicts and release differences still need consideration in such a series.

For compatible annual tractor kilometres `K`, unique tractor-involved casualty events `E` divided by `K` gives a system event-incidence measure. Involved tractors `I` divided by `K` gives a vehicle-involvement measure. A two-tractor crash contributes once to `E`, twice to `I`. Neither establishes fault, individual driver probability, or the number of people killed. Using an event numerator with vehicle-distance is not inherently a dimensional error; the unresolved issue is whether the populations and geography match.

## Implications for the original research question

Historical event counts, all-person harm and configuration decomposition remain the primary findings. This audit does not establish that driving risk increased or decreased, and it does not supply missing event records after 2021. NCDB Online's 2022–2023 vehicle-involvement tables are a separate source and counting unit. Newer registrations and freight volume remain context until they support a specific definition.

Fatal-event share is conditional on reported casualty events and needs no VKT denominator; its increase can still reflect injury reporting or changing composition. Dividing by uncertain exposure would not repair those limitations. The present decision also does not support causal conclusions about training, speed limiters, logbooks or the pandemic.

## Next action and stop conditions

A bounded next analysis can calculate a **model-normalized historical sensitivity**, not a primary risk estimate, after declaring:

1. The exact Table 10 denominator release,2015–2021 overlap, vehicle boundary and unresolved geographic assumptions.
2. A unique-event numerator, fatal/injury strata, observed/strict sensitivities and a separately labelled 2019 publication alternative. Vehicle involvement requires its own validation.
3. Counts and modeled kilometres displayed alongside any ratio; compare pre 2020 and pandemic-inclusive windows. Do not mix Table 10 rounded values with higher-precision figure values without labelling the choice.
4. No extrapolation to 2022–2025, no causal attribution, and no interval that pretends to include unestimated model uncertainty.

A primary national risk result remains conditional on public evidence establishing class/geographic coverage and model calibration, including pandemic behavior. If those cannot be supported, retain the conditional sensitivity and descriptive counts. Public-source review is permitted; no contact or email is part of the project. Do not repeatedly search unchanged sources or add forecasts to make the latest decade appear complete.

## Reproduction and preservation

Notebook07 contains the exact source-table transcription check and event SQL. It writes `reports/exposure/numerator_audit.csv` and `summary.json` with input hashes and `rate_calculated=false`. The reference metadata pins the captured source files. These checks establish transcription and arithmetic, not substantive model validity. Original sources, active selections, production collision/person tables and frozen baselines are unchanged. Source and methods reviewers worked in separate owned files; the project audit consolidates their decisions.
