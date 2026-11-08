# Current project status and research alignment

Updated 2026-10-17. This is the current completion ledger; earlier phase documents retain their dated validation evidence.

## Goal and coverage

Determine whether semi/road-tractor collisions increased over the latest comparable decade and investigate changes in harm and associated recorded conditions. The intended ten completed years are **2016–2025**. The validated public event series covers **1999–2021**; **2012–2021** is an explicitly historical decade, and 2016–2021 is only the available segment of the intended period. A result for 2026 would require comparable partial-year records.

NCDB type08 means road tractor **with or without** a semitrailer. Public records cover fatal and injury collisions, not property-damage-only accidents. Collision events, vehicle involvements, people harmed and exposure are different units.

## Live database clarification

Rechecked 2026-10-15: **NCDB Online includes 2022 and 2023**, although our downloadable event-record series ends in 2021. With Vehicle Type selected, the live tool offers vehicle counts and selected-vehicle occupant casualties, not unique collision counts. The verified [2022–2023 tractor table](../data/reference/ncdb_online_2022_2023_tractor.csv) and [acquisition metadata](../data/reference/ncdb_online_2022_2023_tractor.json) are kept separately. Therefore “missing records” means missing linked event microdata, not an absence of national statistics for those years. The live year selector has no 2024/2025 option. These aggregates cannot be appended as event records or all-person harm.

## Completed work

1. [Source inventory](data_inventory.md), [website/database review](website_database_review.md) and [public availability assessment](data_availability.md).
2. [Collision table and validation](dataset_validation.md), including a [validated source-version repair](source_release_update.md) and preserved original baseline.
3. [Annual event trends](descriptive_trends.md), with source/period/strict sensitivities.
4. [Person-level harm](casualty_findings.md), with duplicate/dummy/conflicting records and group uncertainty retained.
5. [Condition missingness and coding gate](conditions_quality.md).
6. [Descriptive condition comparisons](conditions_findings.md), including explicit denominators, unknown/other, fatal/injury strata and no-recorded-tractor context.
7. [Configuration decomposition](configuration_decomposition.md), separating mix from within-configuration accounting changes, with endpoint, period, strict and frozen-source sensitivities and [independent replication](decomposition_review.md).

8. [Exposure compatibility audit](exposure_compatibility_audit.md): seven-year candidate register, preserved source originals, independent methods decision and executed source/numerator checks. The candidate is not approved for a primary national driving-risk rate.

The latest primary comparison pools 2012–2016 against 2017–2021. Tractor fatal-event share changes **6.1281% → 6.9635%**, or **+0.835362 percentage points = +0.133871 mix +0.701491 within**. Fatal events fall 990→929 while all casualty events fall 16,155→13,341. Within-category change is an accounting term, not an isolated safety effect. Rear-end and other single-vehicle categories contribute strongly; head-on within-category fatal share decreases, offsetting part of its positive mix contribution.

## Original eight questions

| Original question | Status | Evidence and remaining requirement |
|---|---|---|
| 1. Less frequent but more deadly, and why? | Partly answered | Historical event counts, conditional fatal share, person harm and configuration accounting are complete. Fewer reported casualty events and a higher fatal share do not imply greater risk per kilometre. Latest-decade coverage and compatible exposure remain missing; causes are not identified. |
| 2. Who dies; are about 70% in another vehicle? | Descriptive answer with uncertainty | Other motor vehicle occupants account for 1,581/2,206 (71.7%) identified, consistent-outcome deaths in 2012–2021. The group includes more than cars. Person scenarios and incomplete occupant benchmark reconciliation remain explicit. |
| 3. Did speed limiters, mandatory training or electronic logs help? | Not estimable with current design | Requires jurisdiction-specific rules/adherence, compatible exposure, comparison groups, pretrend checks and enough post-policy records. Current public schema lacks jurisdiction and ends before 2023 enforcement. Before/after counts cannot establish effects. |
| 4. Was Ontario's 2022 spike national? | Blocked by coverage and units | Current national event records end in 2021 and lack jurisdiction. Ontario, OPP and national publications cover different vehicles, roads and outcomes. Do not merge unlike aggregates. |
| 5. Do events track freight or registered trucks? | Compatibility audit complete; risk result remains conditional | The candidate tractor VKT is preserved and checked; class/geography/model compatibility has not passed the primary-risk gate. Freight, broad weight-class registrations and tractor kilometres measure different things. |
| 6. Do weather, darkness, road and time patterns differ from cars and change? | Partly answered | Recorded weather/surface/configuration/time comparisons and changes are complete. The comparator includes all no-recorded-tractor events, not cars only. No measured lighting exists; hour is not darkness. Road configuration/alignment are not a full road-type classification. |
| 7. Are older trucks overrepresented? | Documented follow-on, not started | Model year exists, but vehicle-level age validity and multi-tractor event assignment need validation. Conditional severity is feasible; overrepresentation requires fleet-age or distance-by-age denominators. |
| 8. What were cars and tractors doing before impact; test 86% car-at-fault claim? | Not supported by current fields | Public linked records lack manoeuvres and fault. Configuration cannot identify either vehicle's action or responsibility. The news claim has a different scope and is not a national validation target. |

Further ideas and their data/design gates remain in [research questions](research_questions.md); they are not unplanned active work.

## Exposure audit decision and next analysis

The [exposure audit](exposure_compatibility_audit.md) is complete. Transport Canada's Table 10 modeled tractor-trailer distance is available for 2015–2021, but unresolved class, travel-geography and model-calibration boundaries prevent approving it as a primary national driving-risk denominator. Seven values match the official table and its figure rounding; source provenance and numerical validity do not establish population equivalence. No collision rates were calculated.

The next bounded analysis can be an explicitly **model-normalized historical sensitivity**: declare the 2015–2021 overlap and compatibility assumptions, use unique casualty events with separate fatal/injury counts, show counts and modeled kilometres alongside any ratio, and repeat pre-2020, strict and source/2019 sensitivities. This would describe changes relative to one specified model; it must not become an unqualified claim about national semi-driving risk. A vehicle-involvement rate requires its own numerator validation.

A primary risk result requires public evidence supporting class/geographic coverage and annual model behavior. No newer compatible 2022–2025 tractor VKT was located. Keep freight and registrations separate as context; no email or contact is authorized. NCDB Online aggregates through 2023 remain a distinct potential analysis, not added event records. More condition splits or predictive models remain lower priority than these measurement questions.

## Important gaps and safeguards

- **Selection and reporting:** fatal share can rise when recorded injury events decline faster, including from changing ascertainment. Restriction to casualty collisions cannot establish all-crash frequency or underlying physical severity.
- **Within-configuration composition:** geography, road users, weather, exposure and recording may change inside each category. The decomposition is descriptive, its mix/within allocation depends on the chosen convention, and the period matters.
- **Missing records:** no public national 2022–2025 event release was located in the documented review. Newer all-vehicle aggregates and tractor vehicle-involvement tables remain separate.
- **Residual validation:** 2013 and 2019 each retain a two-injury-event benchmark gap; person occupant totals only partly reconcile. Never adjust records to match a publication.
- **Comparator and vehicle ascertainment:** no-recorded-tractor is not car-only; unknown vehicle types may hide tractors. Strict filtering is a sensitivity, not proof of a corrected national population.
- **Person identity:** source keys are not guaranteed real-person identities. Record-resolution scenarios are not statistical confidence intervals or bounds on actual harm.
- **Future vehicle-age work:** audit model-year validity and vehicle/event grain before analysis; do not call collision-conditioned findings overrepresentation in the fleet.

## Repository and verification

Code, tests, selected-source manifests, reference definitions, durable findings and executed notebooks are tracked. Large raw originals, generated reports/derived data, caches and the protected baseline are intentionally ignored. They serve reproducibility and preservation roles; they are not disposable clutter. There are no identified stray tracked scratch/backup artifacts. The optional frozen-baseline comparison requires the local preserved baseline; absence is recorded rather than reconstructed silently.

All 31 project tests pass. Notebook07 also executes without errors, checking candidate/source hashes, seven Table 10 cells and rounding, annual numerator grain and severity additivity without calculating rates. Notebook06 executes without errors and independently checks primary category counts and contributions and all scenario identities/polar allocations. Both new figures were visually checked; local Markdown links, Python 3.11 syntax and all decomposition input/code fingerprints pass verification. The independent review reproduces 504 category rows, 24 totals and 72 allocation rows directly from Parquet. Reproduction commands are in the [README](../README.md) and [notebook guide](../notebooks/README.md). No production collision/person records are modified by these analysis phases.
