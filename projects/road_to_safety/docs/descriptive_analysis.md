# Exploratory descriptive analysis — Road to Safety

Completed October 18, 2026. The temporal, road-condition and data-quality subagents produced complementary analyses; an independent review checked the condition/stability methodology, followed by full-cohort SQL reconciliation. This document connects the results and their implications. Detailed tables and reasoning remain in the three linked findings documents and reproducible notebook.

## Population, scope and interpretation

The validated analytical table contains **2,949,846 candidate collisions**, including **47,793 fatal collisions** and **2,902,053 nonfatal injury collisions**, from **23 selected annual NCDB releases, 1999–2021**. The pooled fatal-collision proportion is **1.6202%**. Every candidate has an eligible binary target; this phase applies no target or feature-completeness exclusions.

One row is a candidate collision identified within a release by `(source_id, C_YEAR, C_CASE)`. Case-field semantics remain undocumented; the analysis does not establish unique real-world events across different source releases. One release is selected for each year. No person-row or vehicle-row weighting is used. Counts are collisions, not casualties or fatalities: a fatal collision can involve multiple deaths.

The estimand is **the proportion of recorded fatal/injury collisions that are fatal within a stated group**. It is not the probability of having a collision, the probability an individual dies, a per-trip/per-kilometre rate, or the causal effect of weather/infrastructure. There is no non-crash observation frame or travel-exposure denominator. Property-damage-only crashes are outside this cohort.

The analytical years end in 2021. Later years in online selectors, dashboards and publication aggregates are separate sources and vintages, not additional record-level observations. Earlier auditing found differences between these archived releases and later publication totals; no aggregate totals are appended or used to scale the cohort. These results describe the selected microdata, rather than a fully reconciled current national statistical series.

## Temporal patterns

[Full temporal findings and tables](temporal_findings.md) describe every annual, month, season, weekday and hour category. The CSV partitions preserve source/year provenance, counts, fatal/injury numerators, proportions and sparse flags. Unknown codes remain explicit; stated-category figures disclose omitted unknown counts.

| Comparison | Largest recorded collision count | Highest fatal-collision proportion among stated categories |
|---|---|---|
| Annual | 2002: 156,415 | 2020: 1,602 / 79,990 = 2.003% |
| Month | August: 268,582 | August: 1.896% (not duration-adjusted) |
| Meteorological season | Summer: 796,187 | Summer: 1.814% |
| Weekday | Friday: 496,697 | Sunday: 2.148% |
| Hour | 16:00–16:59: 249,337 | 02:00–02:59: 3.915% |

Counts and severity proportions peak at different times. A busy time contributes more recorded collisions while another time can have a larger fatal fraction among its collisions. Both burden and conditional severity matter for forming later research questions; neither supplies an exposure-adjusted risk ranking.

The annual collision count falls from **104,630 in 2019 to 79,990 in 2020**, while fatal collisions change from **1,620 to 1,602**. The fatal fraction consequently rises; 2021 contains **83,590 collisions**, including **1,628 fatal**, a **1.948%** fatal fraction. These changes do not identify a cause. Exposure, case mix, coverage, reporting and source vintage cannot be separated with this table. Annual stratification and an explicit late-period evaluation are necessary before treating a pooled association as stable.

Seasons are calendar-month categories: winter December–February, spring March–May, summer June–August and autumn September–November. December is not shifted into the following year, so a year/season row is not a continuous winter cohort. Month lengths, number of weekdays and travel volume are not normalized. Hours are reported source values with no timezone conversion. Full calendar dates and jurisdiction are unavailable.

Both weekday and hour are stated for **2,918,220 collisions**. The 168 displayed weekday/hour cells all exceed the sparse thresholds. **31,626 collisions** with at least one unknown temporal value remain outside the heatmaps but inside the evidence tables. All temporal partitions reconcile to the full cohort and fatal numerator.

## Weather, surface and road conditions

[Full condition findings](condition_findings.md) include all 59 observed pooled categories across weather, surface, alignment, configuration and traffic control, plus annual results and year-composition sensitivity. These selected comparisons illustrate the observed associations:

| Condition | Fatal / collisions | Fatal proportion |
|---|---:|---:|
| Clear and sunny | 32,538 / 2,038,632 | 1.596% |
| Visibility limitation | 1,255 / 44,517 | 2.819% |
| Strong wind | 257 / 9,433 | 2.724% |
| Dry, normal surface | 32,581 / 1,920,788 | 1.696% |
| Wet surface | 7,342 / 515,894 | 1.423% |
| Sand/gravel/dirt debris on surface | 578 / 17,080 | 3.384% |
| Muddy surface | 130 / 3,503 | 3.711% |
| Straight and level alignment | 27,522 / 2,063,954 | 1.333% |
| Curved with gradient | 4,542 / 131,584 | 3.452% |

Visibility limitation includes drifting snow, fog, smog, dust, smoke and mist. Surface debris is a condition on the road, not a classification of an unpaved road. Dictionary code labels and sentinel meanings remain traceable to the archived official dictionary, English pages 4–6.

These comparisons do not show that clear/dry conditions cause fatal outcomes or that rain/snow protects people. Speed, urban/rural setting, collision type, participants, travel volume, reporting thresholds and other unmeasured factors can alter the selected collision populations. Clear/sunny conditions account for many fatal collisions because their recorded collision denominator is large even though their conditional fatal fraction is lower than visibility-limited groups. The findings motivate adjusted severity checks, not intervention-effect estimates.

Five condition figures show every observed category with its collision denominator and a 95% Wilson interval. The interval is a descriptive binomial precision calculation, not design-based confidence for the complete Canadian collision population. Administrative coverage, selection and dependence are not captured by that interval. Comparing overlaps is not a significance test of a difference.

A group is flagged sparse if **n < 100 or fatal count < 5**, without exclusion. Across these five features, **381 of 1,337 observed annual category cells** meet the rule. For example, flooded surfaces have only **9 fatal collisions among 232 pooled collisions**, and oily surfaces **2 among 851**. A large point estimate or a narrow-looking pooled interval is insufficient to establish stable annual evidence. Zero-observation categories have no observed proportion; supported but unobserved codes appear explicitly in the quality grid.

The year-standardization sensitivity uses the same weights for each category: each year's share of all cohort collisions, applied to the category's within-year fatal proportion. It changes year composition only and does not control other factors. It withholds an estimate if any year lacks observations. Sparse-year counts accompany the sensitivity results because some of the largest changes occur in categories sparse in almost every year. Pooled cohort proportions remain the primary observed quantities.

## Missingness, sparse groups and source-year changes

[Full quality/stability findings](stability_findings.md) provide the complete annual availability, complete-case sensitivity, rare-category grid and adjacent-year distribution comparisons. Unknown, other, jurisdiction unavailable, not applicable, conflict, blank, null and out-of-domain values are separate states. Each percentage uses the same year's collision denominator, or the full cohort for pooled rows.

| Predictor | Unknown collisions | Unknown % | Other collisions |
|---|---:|---:|---:|
| Month | 112 | 0.0038% | 0 |
| Weekday | 526 | 0.0178% | 0 |
| Hour | 31,261 | 1.0598% | 0 |
| Road configuration | 234,461 | 7.9482% | 95,746 |
| Weather | 45,409 | 1.5394% | 6,775 |
| Road surface | 37,623 | 1.2754% | 87,977 |
| Road alignment | 192,854 | 6.5378% | 14,738 |
| Traffic control | 134,811 | 4.5701% | 42,317 |

All eight predictor domains have **zero observed conflicts, blanks, nulls, jurisdiction-unavailable, not-applicable, unresolved-star and out-of-domain values** in this prepared cohort. This does not imply complete data: unknown and other categories are substantive parts of the table. The three reported vehicle-count conflicts from preparation remain outside the eight-feature allowlist and do not change these predictor results.

Requiring numeric stated values in all eight predictors would retain **2,378,300 collisions (80.6245%)**, including **38,354 fatal collisions**, and discard **571,546 (19.3755%)**. The retained set has a **1.6127%** fatal fraction, compared with **1.6515%** for records with at least one non-stated predictor. Such deletion changes the population and can bias comparisons; no complete-case filter is applied. “Other” is observed information and remains separate from unknown in all outputs.

Sparse observed annual cells are particularly frequent for traffic control (**223/433**) and configuration (**94/263**); the surface field has **50/250**, and weather **6/207**. These counts refer to feature/category/year groups and are not counts of unique collisions. The full sparse grid distinguishes observed low-volume groups from supported categories with no observations.

Adjacent-year total variation distance is half the sum of absolute category-share changes, including non-stated values. It ranges from zero for identical composition to one for disjoint composition. This is a descriptive distance, without a hypothesis-test or causal interpretation. The largest monthly-distribution change occurs in **2020→2021 (0.07034)**; the largest hourly-distribution change occurs in **2019→2020 (0.02469)**. Annual missingness and complete-case charts show that feature availability also varies over time. The source format/language changes in these late years were normalized and independently checked during preparation; this EDA cannot determine the causes of observed distribution changes.

## Reproducibility, verification and artifacts

Run from the project directory:

```bash
uv sync --locked --python 3.13 --extra notebook
.venv/bin/python -m road_to_safety.explore
.venv/bin/python -m road_to_safety.validate_exploration
.venv/bin/python -m unittest discover -s tests -v
```

The exploration entry point rejects stale preparation evidence before producing summaries. It checks every preparation-validation input fingerprint, then regenerates temporal, condition and stability evidence. It reads source/prepared inputs without modifying them. Individual `analyze_temporal`, `analyze_conditions` and `analyze_stability` modules are also runnable; use the combined entry point for the complete input and reconciliation gate.

Independent DuckDB queries compare every observed temporal, condition and predictor-value group's collision count and fatal numerator against the entire Parquet table. Checks cover duplicate summary keys, fatal/injury conservation, proportions and denominators, complete-case counts, sparse flags and common-year weighting. Stability analysis additionally matches every observed feature value to preparation missingness and every annual count to prior independent validation. Regression tests exercise stale-input rejection, corrupted rates/numerators, duplicate summary groups, outcome-denominator eligibility, code meanings and Wilson calculations.

- [Executed analysis notebook](../notebooks/03_exploratory_descriptive_analysis.ipynb): methods, regenerated evidence, saved chart/table outputs and interpretation.
- `reports/tables/eda_temporal_*.csv`: 11 complete temporal partitions, including annual provenance and weekday/hour joint counts.
- `reports/tables/eda_condition_*.csv`: pooled, annual and common-year weighting results.
- `reports/tables/eda_quality_*.csv`, `eda_sparse_categories.csv`: availability, complete-case sensitivity, distribution changes and supported category grid.
- [Independent check ledger](../reports/tables/eda_validation_checks.csv): check-level pass/fail evidence.
- `reports/figures/`: 13 standalone PNGs, also embedded in the notebook.
- `data/derived/exploration_validation.json`: input, producer-code and output fingerprints plus full validation status; local derived artifact.

Standalone charts were visually inspected for values, labels, scales and clipping. The notebook executes top-to-bottom with saved outputs. A rendered whole-notebook page preview remains unverified because of the previously recorded browser URL policy restriction; notebook execution and chart inspection are distinct checks.

## Next phase and acceptance gate

The next step is **chronological baseline severity modeling**, preceded by a frozen evaluation design:

1. Define the prediction/use case, feature availability and chronological development/validation/test periods. Reserve the newest years for a genuinely held-out temporal evaluation and explicitly address their changed composition.
2. Predeclare metrics and decision criteria against the training-period prevalence baseline. Fatal outcomes are only about 1.62%, so accuracy alone is insufficient. Include precision–recall performance, fatal recall/precision at stated thresholds, probability calibration and a proper probability score; report year-specific denominators.
3. Preserve unknown/other categories, define unseen-category handling and fit encoding/any transformations on training data only. Avoid complete-case deletion and outcome leakage. Keep IDs, casualty outcomes, preparation diagnostics and excluded collision fields outside the initial feature set.
4. Fit a prevalence baseline and an interpretable categorical severity model. Evaluate once the protocol is fixed, with late-period sensitivity, sparse-group warnings and a model card. Adjusted associations still require confounding caveats; prediction coefficients alone are not policy effects.

No model, feature transform or data split is fitted in this phase. Accident occurrence requires exposure/non-crash observations, and local maps require geographic data; neither can be inferred from these descriptive results.
