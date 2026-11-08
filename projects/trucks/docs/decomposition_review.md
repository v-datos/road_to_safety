# Independent configuration decomposition review

Reviewed 2026-10-15. Calculations below were made by direct DuckDB queries of the event Parquet files and separate Python arithmetic, without importing the decomposition implementation. The population is recorded fatal and injury collision events; no people, exposure rates or causal effects are estimated.

## Independent primary result

Periods are 2012–2016 and 2017–2021. Counts are pooled before division.

| Cohort | Early fatal/all events | Late fatal/all events | Early fatal share | Late fatal share | Change (pp) | Configuration mix (pp) | Within configuration (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Recorded tractor | 990/16,155 | 929/13,341 | 6.128133705% | 6.963495990% | +0.835362285 | +0.133870991 | +0.701491294 |
| No recorded tractor | 7,736/584,822 | 7,373/480,615 | 1.322795654% | 1.534076132% | +0.211280478 | +0.041679283 | +0.169601194 |

The calculation uses the symmetric two-component identity:

`change = sum((w_late − w_early) × (r_early + r_late)/2) + sum((r_late − r_early) × (w_early + w_late)/2)`.

Here `w` is a configuration's share of all casualty events in its period, and `r` is the fatal-event share within that configuration. Multiply by 100 for percentage points. Both components are descriptive accounting terms. The within component can reflect changes in unmeasured composition, reporting, injury ascertainment or other factors; it does not isolate changes in mechanical crash severity.

All 20 observed configuration categories, including QQ and UU, have positive denominators in both periods and all requested current-release sensitivity windows. The dictionary's XX category has no events on either side: its contribution is zero but its conditional fatal share remains undefined. One-sided categories would require an explicitly unallocated observed contribution, rather than an invented missing rate.

## Method allocation

The two polar decompositions also reconcile to the same total:

| Cohort | Mix at early fatal shares | Within at late weights | Mix at late fatal shares | Within at early weights |
| --- | ---: | ---: | ---: | ---: |
| Recorded tractor | +0.159711839 | +0.675650446 | +0.108030143 | +0.727332142 |
| No recorded tractor | +0.043428006 | +0.167852472 | +0.039930561 | +0.171349917 |

All cells are percentage points. The symmetric method averages the two paths and splits their interaction equally. Component allocation is therefore a stated method choice, not a uniquely identified causal contribution.

## Sensitivities reproduced independently

| Tractor comparison | Change (pp) | Mix (pp) | Within (pp) |
| --- | ---: | ---: | ---: |
| Strict primary | +0.824302854 | +0.135509080 | +0.688793773 |
| 2012 versus 2021 | +1.455610587 | +0.354214733 | +1.101395854 |
| 2016 versus 2021 | +1.013347424 | +0.202591544 | +0.810755881 |
| 2012–2016 versus 2017–2019 | +0.603388156 | +0.007172591 | +0.596215565 |
| 2012–2016 versus 2017, 2018, 2020, 2021 | +0.809212500 | +0.131917317 | +0.677295183 |
| Frozen pre-revision release, primary periods | +0.741222905 | +0.103362026 | +0.637860879 |

The mix component is much smaller when the late block excludes 2020–2021. Within-configuration changes remain the larger component in these comparisons. The frozen source release is a separate analysis, never a case-ID join across releases. Its comparator result is +0.208652633 pp, comprising +0.041632014 mix and +0.167020619 within.

For the current tractor primary result, the largest positive net category contributions are rear-end (code 21: +0.389045101 pp), other single-vehicle configuration (06: +0.190774706 pp), approaching sideswipe (32: +0.105372558 pp), and head-on (31: +0.096848212 pp). Contributions are changes in each category's share of all fatal/injury events that are fatal; they are not changes in numbers of deaths. Labels must follow the source dictionary.

## Scope and remaining analytical gaps

This decomposition directly supports the existing question of whether recorded casualty collisions are becoming less frequent but more often fatal. It does not complete the intended recent decade, an exposure-adjusted risk analysis, policy evaluation, fault attribution, or an explanation of person-level harm. Those gaps remain substantive: national event data end in 2021, the public data do not identify provinces for a provincial policy comparison, and tractor travel exposure is not supplied by these collision records.

Before expanding to additional decompositions or models, prioritize a compatible exposure assessment and a clear decision about how the available historical analysis should be presented alongside the unresolved 2022–2025 gap. Older truck analysis additionally requires model-year quality and an appropriate comparison fleet; collision-only age distributions cannot establish over-representation. Configuration does not reveal each vehicle's pre-impact manoeuvre or fault, so it cannot test a car-at-fault percentage.

## Export verification receipt

Independently reproduced **all 600 exported statistical rows**: 504 category contributions, 24 cohort/period/subset totals and 72 allocation-sensitivity rows. Direct Parquet queries used each exported year set, release, cohort and strict flag; separate arithmetic recomputed every count, weight, conditional fatal share, component and total. No decomposition module was imported. The largest absolute numerical difference was **2.22 × 10⁻¹⁶**. Every zero-count XX row retained undefined rates, zero contributions and `both_absent` status.

The reviewed implementation applies the symmetric identity correctly, includes the requested comparison population and period/source sensitivities, retains unknown/other categories, and exports both polar allocations. The positive net head-on contribution is driven by composition; its within-configuration contribution is negative. The report explicitly preserves that distinction and the event/person/exposure limitations.

Phase-five descriptive-condition source and narrative were also reviewed for concrete denominator or interpretation problems; no additional arithmetic issue was identified. A rendering robustness issue for hypothetical one-sided categories was reported to the author and fixed: conditional rates are formatted independently, undefined components remain explicit, and undefined plot components are omitted. The updated rendering code was inspected. It does not change current arithmetic because no requested comparison contains such a category.

**Final disposition:** no statistical blocker identified for the current descriptive decomposition. Primary totals and every exported component reconcile, the method choice is visible, and interpretation remains within the event-level study scope. Residual source, coverage and exposure limitations remain unresolved rather than being adjusted away.

## Saved-artifact revalidation, 2026-10-17

Rechecked the completed analysis in commit `4072e67` without expanding or rerunning the analysis. All **nine saved input/code SHA-256 values** in `reports/decomposition/summary.json` match the current files. Notebook 06 contains four executed code cells with no recorded errors. Independent direct queries of the active event Parquet reproduce both primary cohorts' counts and components: tractor change **+0.835362285 pp = +0.133870991 mix +0.701491294 within**; comparator change **+0.211280478 pp = +0.041679283 mix +0.169601194 within**. The saved report and durable methods document agree. No blocker or additional repair was identified.
