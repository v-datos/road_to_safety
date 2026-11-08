# Descriptive condition comparisons

Completed **2026-10-15** using the rebuilt NCDB event release. The available historical comparison is **2012–2021**; it does not answer the intended 2016–2025 national question. The analysis covers police-reported fatal and injury collisions, excluding property-damage-only events.

## Conclusion

Tractor-involved casualty collisions have a different recorded mix of weather, surface, road setting, configuration and clock time from collisions without a recorded tractor. Snow, non-intersection settings, head-on configurations and early-morning hours represent larger shares of the tractor population. Most events in both cohorts nevertheless occur in clear weather and on dry surfaces.

The temporal patterns are mixed. Tractor head-on share is higher at the 2021 endpoint than in 2012, while snow and 00:00–05:59 shares are lower. Equal five-year pooled comparisons show smaller movements than some endpoint comparisons. These findings describe recorded collisions; they do not establish why collision counts or harm changed, fault, or risk per kilometre.

## Population and metric definitions

| 2012–2021 observed cohort | All casualty events | Fatal events | Injury events |
| --- | ---: | ---: | ---: |
| At least one recorded road tractor, type08 | 29,496 | 1,919 | 27,577 |
| No recorded road tractor | 1,065,437 | 15,109 | 1,050,328 |

Type08 includes road tractors with or without semitrailers. The complementary comparison population includes other heavy trucks, other vehicles and uncertain vehicle types. It is **not car-only** and does not establish true absence of tractors when types are missing.

- **Composition share:** category events divided by all events in that cohort, period, subset and severity stratum. Unknown, Q/QQ other and unavailable categories stay in the denominator.
- **Fatal-stratum composition:** category fatal events divided by all fatal events in that cohort/period. It answers which conditions appear among fatal collisions.
- **Category-conditional fatal-event share:** fatal events in a category divided by all fatal and injury events in that category. It answers what fraction of recorded casualty events in that category were fatal.
- **Named-only sensitivity:** defined dictionary categories divided by their own named-category denominator. It excludes Q/QQ and unavailable values and is labelled separately; it is not the primary result.

Every collision counts once, including multi-tractor events. No person-row, vehicle-involvement or death counts are substituted for event counts. A fatal event can contain more than one death.

## Recorded condition mix

Each primary cell is **n/N (%)**, including unknown and other categories in N.

| Recorded category | Tractor events | No recorded tractor |
| --- | ---: | ---: |
| Clear/sunny weather | 18,987/29,496 (64.37%) | 754,298/1,065,437 (70.80%) |
| Snowing weather | 3,391/29,496 (11.50%) | 66,945/1,065,437 (6.28%) |
| Ice/packed-snow surface | 2,578/29,496 (8.74%) | 68,936/1,065,437 (6.47%) |
| Rear-end configuration | 7,572/29,496 (25.67%) | 251,349/1,065,437 (23.59%) |
| Head-on configuration | 1,939/29,496 (6.57%) | 26,675/1,065,437 (2.50%) |
| Non-intersection road configuration | 18,244/29,496 (61.85%) | 449,209/1,065,437 (42.16%) |
| No traffic control recorded | 22,270/29,496 (75.50%) | 551,527/1,065,437 (51.77%) |
| 00:00–05:59 | 3,182/29,496 (10.79%) | 67,512/1,065,437 (6.34%) |

Different geography, freight schedules, road use, condition exposure, reporting practices and collision mechanisms could contribute to these composition differences. Those explanations are not separated here. In particular, a larger snow share is not evidence that a kilometre driven in snow has a higher relative collision risk for tractors.

The full report provides exhaustive category tables for weather, surface, crash configuration, road configuration, hour, month, weekday, alignment and traffic control, plus derived six-hour bands, for both cohorts and all/fatal/injury strata. It retains zero-count valid categories and unavailable codes. A zero numerator with a positive denominator is 0%; a zero denominator is undefined.

## Why severity strata matter

| Recorded category | Tractor fatal events | Tractor injury events | Comparator fatal events | Comparator injury events |
| --- | ---: | ---: | ---: | ---: |
| Snowing weather | 191/1,919 (9.95%) | 3,200/27,577 (11.60%) | 684/15,109 (4.53%) | 66,261/1,050,328 (6.31%) |
| Head-on configuration | 641/1,919 (33.40%) | 1,298/27,577 (4.71%) | 2,375/15,109 (15.72%) | 24,300/1,050,328 (2.31%) |
| 00:00–05:59 | 290/1,919 (15.11%) | 2,892/27,577 (10.49%) | 2,345/15,109 (15.52%) | 65,167/1,050,328 (6.20%) |

The all-event early-morning difference does not carry over to the fatal-stratum composition: 15.11% and 15.52% are close. These are different descriptive denominators, not an adjusted comparison of driving risk.

Head-on events illustrate the distinction between composition and conditional severity:

- **641/1,919 = 33.40%:** share of fatal tractor events recorded as head-on.
- **641/1,939 = 33.06%:** share of recorded head-on tractor casualty events that were fatal.
- For rear-end tractor events, the second measure is **271/7,572 = 3.58%**.

These contrasts identify a configuration associated with a large part of fatal tractor events. They do not assign responsibility to either vehicle, measure person fatality rates, or establish a causal effect of configuration.

## Change over time

| Tractor-event category | 2012 | 2021 | Share change |
| --- | ---: | ---: | ---: |
| Snowing weather | 394/3,300 (11.94%) | 235/2,276 (10.33%) | −1.61 pp |
| Rear-end | 787/3,300 (23.85%) | 571/2,276 (25.09%) | +1.24 pp |
| Head-on | 193/3,300 (5.85%) | 169/2,276 (7.43%) | +1.58 pp |
| 00:00–05:59 | 388/3,300 (11.76%) | 231/2,276 (10.15%) | −1.61 pp |

The head-on event count fell from 193 to 169 while its share rose because the overall event count fell faster. A rising category share therefore need not mean more collisions in that category.

Equal five-year event-weighted blocks provide another view: head-on share changes from **1,021/16,155 (6.32%)** during 2012–2016 to **918/13,341 (6.88%)** during 2017–2021, a 0.56-point increase. Snow shares are nearly unchanged, **11.54% → 11.45%**; the early-morning share changes **11.06% → 10.46%**. These pool counts before division rather than averaging annual percentages. The late block includes the 2020 disruption and 2021 rebound.

## Missingness and sensitivities

Unknown and valid residual categories stay visible. Pooled tractor weather unknown is **199/29,496 (0.67%)**; surface unknown is **119/29,496 (0.40%)** and Q other is **1,405/29,496 (4.76%)**. Configuration unknown is **433/29,496 (1.47%)**, with QQ other **2,073/29,496 (7.03%)**. Their presence limits the meaning of named-category shares; they are not reassigned to a particular condition.

The strict sensitivity excludes 11 tractor events and two comparison events in this period. Selected higher tractor shares of snow, head-on and 00:00–05:59 persist under strict filtering, the pre-2020 window, omission of 2019 and the observed 2016–2021 target-period segment. This is descriptive stability for those contrasts, not a claim that every sparse category is stable or that confounding is absent. Omitting 2019 changes the included years; it is not a correction to that year's records.

Two exploratory joint tables, weather × surface and crash configuration × hour band, retain every category pair, including zero and special-code cells, for both cohorts and severity strata. They are not interaction tests. Rare-cell counts and undefined denominators must be read directly; no inferential ranking is attached.

The earlier [quality gate](conditions_quality.md) remains applicable: do not impose a single nine-field complete-case sample, and do not pool the flagged 1999 configuration distribution into this primary comparison. The two-injury-event benchmark differences in 2013 and 2019 and incomplete 2022–2025 national record coverage remain unresolved.

## Verification and deliverables

- [Full report, complete stratum tables and three figures](../reports/conditions/findings.md).
- [Executed notebook](../notebooks/05_descriptive_conditions.ipynb).
- [Independent review receipt](conditions_review.md).
- [Annual distributions](../reports/conditions/annual_distributions.csv), [period distributions](../reports/conditions/period_distributions.csv), [cohort contrasts](../reports/conditions/cohort_comparisons.csv), [period changes](../reports/conditions/period_changes.csv), and [conditional fatal shares](../reports/conditions/category_fatal_shares.csv).
- [Joint period tables](../reports/conditions/joint_distributions.csv) and [annual joint tables](../reports/conditions/joint_annual_distributions.csv).
- [Input/code hashes and metric definitions](../reports/conditions/summary.json).

An independent reviewer reproduced **84,984 rows across all seven statistical exports** from direct Parquet queries, including zero cells, numerators, all-event and named-only denominators, percentages and contrasts. The executed notebook independently checks 822 primary category/cohort/stratum cells, denominator arithmetic, selected conditional shares and joint counts. The three figures were visually checked. The production event/person datasets and earlier analyses were not changed.

All **26 project tests pass**, including five new denominator, zero-count, category and strict-subset checks. All seven notebook code cells execute successfully without errors.

Reproduce with `python -m truck_collisions.analyze_conditions`, then `python -m truck_collisions.report_conditions` in the project environment. Use `PYTHONPATH=src` and `MPLCONFIGDIR=/tmp/collisions-matplotlib` as in the README. Notebook execution instructions are in [notebooks/README.md](../notebooks/README.md).

The statistics module checks its direct event counts against the earlier quality audit; run `python -m truck_collisions.audit_conditions` first if those generated quality outputs are absent. A mismatch stops the comparison rather than silently using stale audit results.

## Completed follow-on and next priority

The [configuration decomposition](configuration_decomposition.md) is complete, retaining unknown/QQ groups and strict, period and source sensitivities. Most of the primary increase is within configurations. This is accounting, not a causal explanation; see [current status](project_status.md) for the completed exposure audit and remaining risk gate. A compatible tractor exposure denominator is still required before drawing conclusions about driving risk. Vehicle manoeuvres, fault, measured darkness and policy effects need additional information or a separate defensible design.
