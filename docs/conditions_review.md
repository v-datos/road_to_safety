# Independent review of descriptive condition comparisons

Completed **2026-10-15**. The review reads the rebuilt event Parquet directly; it does not import the condition analysis module or reconstruct people from event records. No source or production dataset was modified.

## Result

**The exported descriptive comparisons reproduce direct event queries.** The interpretation is limited to recorded fatal and injury collisions. Exposure-adjusted risk, causal effects, fault, measured darkness and person death rates are not identified by these comparisons.

The 2012–2021 observed populations are mutually exclusive and exhaustive:

| Population | All casualty events | Fatal events | Injury events |
| --- | ---: | ---: | ---: |
| Recorded tractor involvement | 29,496 | 1,919 | 27,577 |
| No recorded tractor | 1,065,437 | 15,109 | 1,050,328 |

The strict sensitivity excludes 11 tractor events and two comparison events. It is an alternative source-quality cohort. The comparison population includes other heavy trucks and unknown vehicle classifications; it is not a car-only population.

## Independent arithmetic checks

DuckDB queries against `data/derived/ncdb/collisions.parquet` independently aggregate the nine fields and derived six-hour bands by year, recorded tractor status, candidate status and event severity. The codebook supplies named-code membership; the analysis module is not used for aggregation. Each exported row is compared with those direct counts.

| Export | Rows checked |
| --- | ---: |
| Annual distributions | 17,160 |
| Period distributions | 10,296 |
| Conditional fatal-event shares | 3,432 |
| Period joint distributions | 17,712 |
| Annual joint distributions | 29,520 |
| Cohort contrasts | 5,148 |
| Early/late changes | 1,716 |
| **Total** | **84,984** |

Checks cover exact numerators, all-event denominators, field-specific named-only denominators, percentages, conditional fatal shares, percentage-point differences, joint counts and joint named-only denominators. All rows passed, including zero-count domain rows. Undefined percentages remain blank when their denominator is zero.

Every primary field uses the full cohort/severity denominator rather than a common complete-case sample. Valid Q/QQ residual categories remain separate from unknown U/UU and not-provided X/XX. Defined dictionary categories containing the word “other” remain defined categories. No unobserved special-code category is redistributed to a named category.

The six period windows were independently recomputed from their actual constituent years: primary 2012–2021; early 2012–2016; late 2017–2021; pre-2020 2012–2019; omission of 2019; and available target years 2016–2021. Pooled shares divide summed category counts by summed event counts. They are not unweighted annual percentage averages. The late block includes 2020–2021, so its difference from the early block cannot isolate a pandemic effect or a policy effect.

## Interpretation checks

Direct checks distinguish three different denominators:

- Head-on configurations account for **1,939/29,496 (6.57%)** of tractor casualty collisions.
- Head-on configurations account for **641/1,919 (33.40%)** of tractor fatal collisions.
- **641/1,939 (33.06%)** of tractor head-on casualty collisions are fatal events.

These are event statistics. They do not imply that 33.06% of people in head-on collisions die, nor do they identify the vehicle responsible. Rear-end conditional fatal-event share independently reproduces **271/7,572 (3.58%)**.

The direction of the selected tractor/comparator composition differences for snow, head-on configuration and 00:00–05:59 survives the strict, pre-2020, omit-2019 and available-2016–2021 views. This is descriptive stability for those selected categories, not a result about every small cell or proof that exposure and reporting differences are absent. Small numerators and denominators remain visible; no significance ranking is inferred from sparse categories.

## Report and figure review

All three final figures were visually inspected. Labels, denominators and footnotes are readable, and bars are not clipped. Review caught and the reporting author corrected a conditional-fatal chart axis that initially used only the comparator maximum, plus an hour-band code dash mismatch before delivery. The final report distinguishes composition from conditional fatal-event shares and includes explicit early/late and alternative-window tables.

## Remaining limits

- The selected national event records stop at 2021. No 2022–2025 events were inferred or imputed.
- Existing two-event injury benchmark differences in 2013 and 2019 and partial person benchmark differences remain unresolved.
- One dictionary and syntactically valid codes do not prove identical reporting practice across jurisdictions and years.
- Pooled differences can reflect travel exposure, geography, reporting and changing collision composition; this phase cannot separate them.
- Weather describes recorded conditions, hour describes clock time, and configuration describes the collision. These do not establish exposure-specific collision risk, lighting, vehicle manoeuvres or fault.

See the [complete condition report](../reports/conditions/findings.md), [quality assessment](conditions_quality.md), and [run evidence](../reports/conditions/summary.json). Generated independent check counts are in `reports/conditions/independent_review_checks.json`; analytical outputs remain reproducible generated artifacts.
