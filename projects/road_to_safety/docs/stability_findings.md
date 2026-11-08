# Feature availability, sparse groups and source-year stability

This descriptive analysis uses the validated collision-level table only: one candidate collision per selected source, year and case. It covers 1999–2021, all released road users, and fatal/injury collisions only. It does not estimate the chance of a collision occurring, individual death risk, or causal effects. Counts describe this archived release selection; they are not substituted for later national statistical revisions.

## Definitions and reproducibility

`python -m road_to_safety.analyze_stability` recomputes all accompanying CSVs, figures and this document. The routine verifies the prepared-validation success receipt, collision/contract/preparation-manifest hashes, the annual evidence hash, and the preparation-missingness hash. Every observed year–field–value count reconciles exactly to preparation evidence; annual collision/fatal counts reconcile exactly to independent validation. No input, target or prepared dataset is changed.

Unknown (`U/UU`), other (`Q/QQ`), jurisdiction unavailable (`X/XX`), documented not applicable, blank, null, conflict and out-of-domain states are separate. A numeric dictionary-supported value is “stated.” Other is an observed category, not silently imputed or combined with unknown. Zero-count supported codes are enumerated so absence of observations is explicit. Denominators are all candidate collisions in the same source year, or all collisions for pooled rows. Percentages in CSVs are fractions, except explicitly named percentage-point changes.

A year–field–category is flagged sparse when its collision count is <100 **or** its fatal count is <5. These are predeclared descriptive warning thresholds, not exclusion criteria, disclosure rules or significance tests. Flags include non-stated categories; unobserved supported codes are distinguished by `observed=False`. The same collision can appear in eight feature summaries, so feature-level counts must not be added to estimate distinct collisions.

## Pooled feature availability

| Feature | Stated | Unknown | Other | Remaining states | Unknown % |
|---|---:|---:|---:|---:|---:|
| C_MNTH | 2,949,734 | 112 | 0 | 0 | 0.0038 |
| C_WDAY | 2,949,320 | 526 | 0 | 0 | 0.0178 |
| C_HOUR | 2,918,585 | 31,261 | 0 | 0 | 1.0598 |
| C_RCFG | 2,619,639 | 234,461 | 95,746 | 0 | 7.9482 |
| C_WTHR | 2,897,662 | 45,409 | 6,775 | 0 | 1.5394 |
| C_RSUR | 2,824,246 | 37,623 | 87,977 | 0 | 1.2754 |
| C_RALN | 2,742,254 | 192,854 | 14,738 | 0 | 6.5378 |
| C_TRAF | 2,772,718 | 134,811 | 42,317 | 0 | 4.5701 |

Total: **2,949,846 candidate collisions**, **47,793 fatal**, fatal proportion **1.6202%**. All eight predictor domains have zero conflicts, blanks, nulls, jurisdiction-unavailable, documented-not-applicable, star-code and out-of-domain observations in this selected dataset. Dictionary-supported but unobserved sentinel codes remain explicitly present as zero rows.

## Complete-case sensitivity (diagnostic only)

Requiring all eight numeric stated codes retains **2,378,300 collisions (80.6245%)** and would remove **571,546 (19.3755%)**. The retained set has **38,354 fatal collisions**, fatal proportion **1.6127%**; collisions with at least one non-stated feature have fatal proportion **1.6515%**. This composition difference means complete-case exclusion would change the analytical population. It is not evidence that missingness causes severity. Unknown and other categories remain available for downstream modeling; no complete-case filter is applied.

| Year | All collisions | Fatal | All-eight-stated % | All fatal % | Stated-set fatal % | Non-stated-set fatal % |
|---|---:|---:|---:|---:|---:|---:|
| 1999 | 151,315 | 2,632 | 79.346 | 1.739 | 1.732 | 1.766 |
| 2000 | 155,838 | 2,548 | 81.032 | 1.635 | 1.661 | 1.526 |
| 2001 | 151,438 | 2,415 | 80.719 | 1.595 | 1.608 | 1.538 |
| 2002 | 156,415 | 2,583 | 80.629 | 1.651 | 1.655 | 1.637 |
| 2003 | 152,980 | 2,487 | 81.254 | 1.626 | 1.648 | 1.531 |
| 2004 | 147,588 | 2,438 | 81.502 | 1.652 | 1.659 | 1.623 |
| 2005 | 148,111 | 2,551 | 81.491 | 1.722 | 1.751 | 1.594 |
| 2006 | 145,103 | 2,586 | 80.169 | 1.782 | 1.793 | 1.738 |
| 2007 | 141,070 | 2,455 | 80.686 | 1.740 | 1.712 | 1.857 |
| 2008 | 129,764 | 2,193 | 80.959 | 1.690 | 1.667 | 1.789 |
| 2009 | 125,456 | 2,007 | 81.246 | 1.600 | 1.568 | 1.738 |
| 2010 | 125,636 | 2,021 | 80.990 | 1.609 | 1.586 | 1.704 |
| 2011 | 124,199 | 1,849 | 80.465 | 1.489 | 1.466 | 1.583 |
| 2012 | 124,682 | 1,848 | 79.104 | 1.482 | 1.476 | 1.505 |
| 2013 | 122,132 | 1,772 | 79.511 | 1.451 | 1.414 | 1.594 |
| 2014 | 116,292 | 1,675 | 79.777 | 1.440 | 1.404 | 1.582 |
| 2015 | 119,550 | 1,693 | 81.838 | 1.416 | 1.422 | 1.391 |
| 2016 | 118,321 | 1,738 | 82.246 | 1.469 | 1.450 | 1.557 |
| 2017 | 114,412 | 1,698 | 81.145 | 1.484 | 1.439 | 1.678 |
| 2018 | 111,334 | 1,754 | 80.489 | 1.575 | 1.582 | 1.547 |
| 2019 | 104,630 | 1,620 | 80.225 | 1.548 | 1.525 | 1.643 |
| 2020 | 79,990 | 1,602 | 79.490 | 2.003 | 1.989 | 2.054 |
| 2021 | 83,590 | 1,628 | 78.785 | 1.948 | 1.930 | 2.013 |

## Unknown-code variation across releases

| Feature | Lowest unknown % (year) | Highest unknown % (year) | 2019 % | 2020 % | 2021 % |
|---|---:|---:|---:|---:|---:|
| C_MNTH | 0.0009 (2018) | 0.0096 (2012) | 0.0010 | 0.0013 | 0.0024 |
| C_WDAY | 0.0009 (2018) | 0.1963 (1999) | 0.0010 | 0.0013 | 0.0024 |
| C_HOUR | 0.7301 (2014) | 1.3463 (2008) | 0.7531 | 1.1576 | 0.8913 |
| C_RCFG | 5.0731 (2020) | 11.8204 (1999) | 5.2012 | 5.0731 | 6.1180 |
| C_WTHR | 1.2831 (2017) | 1.9724 (2006) | 1.4222 | 1.6090 | 1.5696 |
| C_RSUR | 0.8089 (2015) | 1.8041 (2005) | 0.9663 | 1.0901 | 1.0456 |
| C_RALN | 4.5681 (2016) | 8.1712 (2002) | 4.8600 | 4.9606 | 5.2805 |
| C_TRAF | 3.7934 (1999) | 5.9545 (2020) | 5.5080 | 5.9545 | 5.9277 |

## Sparse and unobserved groups

| Feature | Observed year-category groups | Observed sparse | Observed sparse numeric stated | Unobserved supported year-category groups |
|---|---:|---:|---:|---:|
| C_MNTH | 299 | 23 | 0 | 23 |
| C_WDAY | 184 | 23 | 0 | 23 |
| C_HOUR | 575 | 0 | 0 | 23 |
| C_RCFG | 263 | 94 | 94 | 82 |
| C_WTHR | 207 | 6 | 2 | 23 |
| C_RSUR | 250 | 50 | 50 | 26 |
| C_RALN | 184 | 8 | 0 | 23 |
| C_TRAF | 433 | 223 | 223 | 50 |

The complete `eda_sparse_categories.csv` includes every supported code for every year, observed indicators, both sparse triggers, collision/fatal counts, denominators, category shares and conditional fatal proportions. A zero-count group has a blank fatal proportion. Sparse groups should retain warning flags in charts and model evaluation; avoid ranking them as stable high-risk conditions. No p-values or significance claims are made.

## Distribution changes and late-period checks

For each feature and adjacent pair of years, total variation distance is one half the sum of absolute changes in category shares, including non-stated states. It ranges from 0 (same composition) to 1 (disjoint composition). This is a descriptive compositional distance, not a causal estimate or a hypothesis test. The table lists the largest adjacent-year change per feature; full adjacent comparisons are in `eda_quality_year_changes.csv`.

| Feature | Previous → current | Total variation | Largest changing code | Change (percentage points) |
|---|---|---:|---|---:|
| C_MNTH | 2020 → 2021 | 0.07034 | 1 | -4.0548 |
| C_WDAY | 2007 → 2008 | 0.01446 | 1 | -0.7605 |
| C_HOUR | 2019 → 2020 | 0.02469 | 8 | -0.9710 |
| C_RCFG | 1999 → 2000 | 0.03079 | UU | -2.3830 |
| C_WTHR | 2006 → 2007 | 0.04454 | 3 | -3.2718 |
| C_RSUR | 2014 → 2015 | 0.04655 | 1 | +4.6506 |
| C_RALN | 2009 → 2010 | 0.02692 | 1 | +1.3017 |
| C_TRAF | 2011 → 2012 | 0.02093 | 18 | -1.8807 |

| Feature | 2019 → 2020 total variation | 2020 → 2021 total variation |
|---|---:|---:|
| C_MNTH | 0.05198 | 0.07034 |
| C_WDAY | 0.00982 | 0.00371 |
| C_HOUR | 0.02469 | 0.01311 |
| C_RCFG | 0.00961 | 0.02305 |
| C_WTHR | 0.02140 | 0.02495 |
| C_RSUR | 0.02795 | 0.04065 |
| C_RALN | 0.01945 | 0.01027 |
| C_TRAF | 0.01490 | 0.00602 |

2019 → 2020: collision count changes from **104,630 to 79,990 (-23.550%)**; fatal collisions change from **1,620 to 1,602 (-1.111%)**.

2020 → 2021: collision count changes from **79,990 to 83,590 (+4.501%)**; fatal collisions change from **1,602 to 1,628 (+1.623%)**.

Treat 2020–2021 as a distinct late-period sensitivity. Archived file formats/languages also differ (2020 CSV; 2021 French CSV). The preparation process normalized bilingual headers and numeric formatting and independently validated values. These observations cannot attribute changes to travel exposure, reporting practice, source vintage or real severity changes. There are no travel-exposure denominators or provincial fields in this table. Annual stratification and future chronological validation are needed; pooled feature associations must not be presented as invariant across years.

## Artifacts and practical implications

- `reports/tables/eda_quality_values.csv`: collision-level category counts and shares, annual denominators and source IDs, including zero supported codes.
- `reports/tables/eda_quality_missingness.csv`: annual and pooled separate availability classes for each predictor.
- `reports/tables/eda_quality_complete_cases.csv`: annual/pooled complete-case sensitivity; no records excluded.
- `reports/tables/eda_quality_year_changes.csv`: every adjacent-year distribution distance and largest category change.
- `reports/tables/eda_sparse_categories.csv`: full category grid and transparent sparse flags.
- `reports/figures/quality_unknown_by_year.png`: unknown-code percentages using annual collision denominators.
- `reports/figures/quality_complete_cases.png`: completeness and severity-composition sensitivity.

Input collision SHA256: `32b62f217040e2a4ca30d76faabf495e13cbe77ed7aef732f0e413ba3a34f0de`.

Proceed with explicit categorical unknown/other handling, sparse-group flags, and year-aware interpretation. Keep all target-valid events. The next modeling design should fix chronological development/validation/test periods before fitting transforms and compare temporal stability and calibration; none of these exploratory summaries establishes an operational forecasting model.
