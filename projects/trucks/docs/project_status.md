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
9. [Bounded 2015–2021 model-normalized VKT sensitivity](model_normalized_vkt_sensitivity.md): evaluates annual (`2015–2021`) and period-pooled (`2015–2017` vs `2018–2019` pre-pandemic vs `2018–2021` full overlap, plus `2019`-excluded sensitivities) road-tractor casualty collisions and vehicle involvements relative to Table 10 modeled tractor-trailer VKT (`reports/tables/vkt_sensitivity_annual.csv`, `reports/tables/vkt_sensitivity_summary.csv`, `reports/figures/vkt_model_normalized_sensitivity.png`, and [executed notebook08](../notebooks/08_model_normalized_vkt_sensitivity.ipynb)). Primary observed casualty events per billion modeled VKT decline `-25.50%` over `2015–2019` (`89.903 → 66.973`) and `-44.47%` over `2015–2021` (`89.903 → 49.919`); fatal events per billion modeled VKT decline `-16.60%` over `2015–2019` (`5.672 → 4.730`) and `-34.65%` over `2015–2021` (`5.672 → 3.707`).
10. [Tractor vehicle-age (`V_YEAR`) audit and conditional severity analysis](vehicle_age_severity.md): audits `V_YEAR` across `86,154` road-tractor vehicles (`V_TYPE='08'`) and `80,540` road-tractor casualty collisions in `1999–2021` (`32,022` vehicles and `29,496` collisions in `2012–2021`), evaluates multi-tractor (`2+` tractor) assignment rules (`oldest_tractor`, `newest_tractor`, `single_tractor_only`, and `vehicle_grain_all_tractors`), and estimates Wilson 95% CIs and multivariable logistic regression ORs controlling for `C_YEAR`, `C_RCFG`, `C_RALN`, `C_WTHR`, and `C_HOUR` (`reports/tables/vehicle_age_audit.csv`, `reports/tables/vehicle_age_severity_cohorts.csv`, `reports/tables/vehicle_age_multi_tractor_sensitivity.csv`, `reports/figures/vehicle_age_conditional_severity.png`, and [executed notebook09](../notebooks/09_vehicle_age_severity_audit.ipynb)). Older tractors do not exhibit higher conditional fatality severity than `0–2` year tractors (`7.21%` fatal in `2012–2021` vs `6.58%` for `11–15` years and `5.65%` for `16+` years; `16+` years adjusted OR `0.786`, 95% CI `0.646–0.957`).

The latest primary comparison pools 2012–2016 against 2017–2021. Tractor fatal-event share changes **6.1281% → 6.9635%**, or **+0.835362 percentage points = +0.133871 mix +0.701491 within**. Fatal events fall 990→929 while all casualty events fall 16,155→13,341. Within-category change is an accounting term, not an isolated safety effect. Rear-end and other single-vehicle categories contribute strongly; head-on within-category fatal share decreases, offsetting part of its positive mix contribution.

## Original eight questions

| Original question | Status | Evidence and remaining requirement |
|---|---|---|
| 1. Less frequent but more deadly, and why? | Partly answered | Historical event counts, conditional fatal share, person harm and configuration accounting are complete. Fewer reported casualty events and a higher fatal share do not imply greater risk per kilometre. Latest-decade coverage and compatible exposure remain missing; causes are not identified. |
| 2. Who dies; are about 70% in another vehicle? | Descriptive answer with uncertainty | Other motor vehicle occupants account for 1,581/2,206 (71.7%) identified, consistent-outcome deaths in 2012–2021. The group includes more than cars. Person scenarios and incomplete occupant benchmark reconciliation remain explicit. |
| 3. Did speed limiters, mandatory training or electronic logs help? | Not estimable with current design | Requires jurisdiction-specific rules/adherence, compatible exposure, comparison groups, pretrend checks and enough post-policy records. Current public schema lacks jurisdiction and ends before 2023 enforcement. Before/after counts cannot establish effects. |
| 4. Was Ontario's 2022 spike national? | Blocked by coverage and units | Current national event records end in 2021 and lack jurisdiction. Ontario, OPP and national publications cover different vehicles, roads and outcomes. Do not merge unlike aggregates. |
| 5. Do events track freight or registered trucks? | Compatibility audit and bounded model-normalized sensitivity complete; primary risk remains conditional | The candidate tractor VKT is preserved and checked; class/geography/model compatibility has not passed the primary-risk gate. Bounded 2015–2021 model-normalized sensitivities ([model_normalized_vkt_sensitivity.md](model_normalized_vkt_sensitivity.md)) show declining events and fatal events per billion modeled VKT across all six numerator specifications, but remain conditional on the Table 10 forecast model. Freight, broad weight-class registrations and tractor kilometres measure different things. |
| 6. Do weather, darkness, road and time patterns differ from cars and change? | Partly answered | Recorded weather/surface/configuration/time comparisons and changes are complete. The comparator includes all no-recorded-tractor events, not cars only. No measured lighting exists; hour is not darkness. Road configuration/alignment are not a full road-type classification. |
| 7. Are older trucks overrepresented? | Vehicle-age (`V_YEAR`) audit & conditional severity complete; fleet overrepresentation blocked by missing VKT-by-age denominators | Vehicle- and event-grain `V_YEAR` audits and conditional severity models ([vehicle_age_severity.md](vehicle_age_severity.md)) are complete for 1999–2021 and 2012–2021 across `oldest_tractor`, `newest_tractor`, `single_tractor_only`, and vehicle-grain assignments. Older tractors (`11–15` and `16+` years) do not show higher conditional fatality severity than `0–2` year tractors (`16+` years adjusted OR `0.786` in 2012–2021). True fleet overrepresentation remains unestimable without fleet-age or VKT-by-age denominators. |
| 8. What were cars and tractors doing before impact; test 86% car-at-fault claim? | Not supported by current fields | Public linked records lack manoeuvres and fault. Configuration cannot identify either vehicle's action or responsibility. The news claim has a different scope and is not a national validation target. |

Further ideas and their data/design gates remain in [research questions](research_questions.md); they are not unplanned active work.

## Exposure audit decision and completed model-normalized sensitivity

The [exposure audit](exposure_compatibility_audit.md) and the follow-on [bounded 2015–2021 model-normalized VKT sensitivity](model_normalized_vkt_sensitivity.md) are complete. Transport Canada's Table 10 modeled tractor-trailer distance is available for 2015–2021, but unresolved class, travel-geography and model-calibration boundaries prevent approving it as a primary national driving-risk denominator. Seven values match the official table and its figure rounding; source provenance and numerical validity do not establish population equivalence.

In the bounded **model-normalized historical sensitivity** (`src/truck_collisions/analyze_vkt_sensitivity.py`, `reports/tables/vkt_sensitivity_annual.csv`, `reports/tables/vkt_sensitivity_summary.csv`, and `notebooks/08_model_normalized_vkt_sensitivity.ipynb`), raw event counts and modeled kilometres are reported alongside ratios across six numerator specifications (`primary_observed_events`, `strict_candidate_events`, `strict_zero_unknown_vtype_events`, `published_tc_benchmark_events`, `observed_tractor_vehicle_involvements`, and `strict_tractor_vehicle_involvements`), with pre-pandemic (`2015–2019`), full-overlap (`2015–2021`), and `2019`-excluded sensitivities. These ratios describe changes relative to the specified Table 10 model and must not be cited as unqualified national semi-driving risk rates.

A primary risk result requires public evidence supporting class/geographic coverage and annual model behavior. No newer compatible 2022–2025 tractor VKT was located. Keep freight and registrations separate as context; no email or contact is authorized. NCDB Online aggregates through 2023 remain a distinct potential analysis, not added event records.

## Important gaps and safeguards

- **Selection and reporting:** fatal share can rise when recorded injury events decline faster, including from changing ascertainment. Restriction to casualty collisions cannot establish all-crash frequency or underlying physical severity.
- **Within-configuration composition:** geography, road users, weather, exposure and recording may change inside each category. The decomposition is descriptive, its mix/within allocation depends on the chosen convention, and the period matters.
- **Missing records:** no public national 2022–2025 event release was located in the documented review. Newer all-vehicle aggregates and tractor vehicle-involvement tables remain separate.
- **Residual validation:** 2013 and 2019 each retain a two-injury-event benchmark gap; person occupant totals only partly reconcile. Never adjust records to match a publication.
- **Comparator and vehicle ascertainment:** no-recorded-tractor is not car-only; unknown vehicle types may hide tractors. Strict filtering is a sensitivity, not proof of a corrected national population.
- **Person identity:** source keys are not guaranteed real-person identities. Record-resolution scenarios are not statistical confidence intervals or bounds on actual harm.
- **Vehicle-age interpretation:** `V_YEAR` validity and vehicle/event grain are audited in [vehicle_age_severity.md](vehicle_age_severity.md); collision-conditioned age shares and conditional fatality ratios do not measure overrepresentation in the operating fleet without fleet-age VKT denominators.

## Repository and verification

Code, tests, selected-source manifests, reference definitions, durable findings and executed notebooks are tracked. Large raw originals, generated reports/derived data, caches and the protected baseline are intentionally ignored. They serve reproducibility and preservation roles; they are not disposable clutter. There are no identified stray tracked scratch/backup artifacts. The optional frozen-baseline comparison requires the local preserved baseline; absence is recorded rather than reconstructed silently.

All 36 project tests pass (31 prior tests plus 5 new tests in `tests/test_vkt_and_vehicle_age.py`). Notebooks 06, 07, 08 and 09 execute without errors and independently verify their outputs against direct DuckDB queries. All new figures (`reports/figures/vkt_model_normalized_sensitivity.png` and `reports/figures/vehicle_age_conditional_severity.png`) were visually checked; local Markdown links, Python syntax and input/code fingerprints pass verification. Reproduction commands are in the [README](../README.md) and [notebook guide](../notebooks/README.md). No production collision/person records are modified by these analysis phases.
