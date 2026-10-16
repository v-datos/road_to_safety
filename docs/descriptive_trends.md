# Descriptive collision trends after the source-version update

Updated 2026-10-15 from the rebuilt production event table. Available event records cover **1999–2021**; the historical comparison decade is **2012–2021** and the observed portion of the intended 2016–2025 study is **2016–2021**. These periods do not answer the missing 2022–2025 national event question.

## Findings

| Road-tractor measure | 2012 | 2021 | Change |
| --- | ---: | ---: | ---: |
| Fatal or injury collision events | 3,300 | 2,276 | -31.03% |
| Fatal collision events | 197 | 169 | -14.21% |
| Injury collision events | 3,103 | 2,107 | -32.10% |
| Fatal share among casualty events | 5.97% | 7.43% | +1.46 percentage points |

The 2012 and 2021 endpoint counts are unchanged by the source repair. Fewer reported casualty events and a larger fatal share coexist because injury events declined faster. This does not establish increased driving risk or the cause of the change. People killed per event is a different measure, covered in [the separate casualty analysis](casualty_findings.md).

For 2016–2021, tractor events changed from **3,010 to 2,276 (-24.39%)**. Fatal events changed from 193 to 169 (-12.44%). The validated 2016 source adds one injury event relative to the previous baseline.

## Period and source sensitivity

- **Pre-2020:** the rebuilt 2012–2019 casualty count changes by -15.91%. Fatal counts change from 197 to 196. From 2016 to 2019 fatal events change from 193 to 196 (+1.55%). The earlier CSV-based near-flat decline is superseded.
- **Disruption and rebound:** events change by -23.53% during 2019–2020, then +7.26% during 2020–2021. The 2021 count is -17.98% relative to 2019. Timing alone does not establish a causal pandemic effect.
- **Source repair:** annual 2014–2017 and 2019 inputs were validated and replaced as complete releases. The original source selection and results remain preserved. Source choice is supported by documented provenance and collision/person validation; aggregate benchmark proximity is corroborating evidence, not a correction rule.
- **Residual benchmarks:** 2013 has 3,148 injury tractor events versus 3,150 published; 2019 has 196 fatal and 2,579 injury events versus 196 and 2,581 published. Other benchmarked years now match both severity totals. These remaining differences are not filled or assigned an unproven explanation.
- **Strict filtering:** observed events retain source-quality flags; the stricter sensitivity excludes 11 tractor events. It is an alternative cohort, not a corrected national series. The small 2020–2021 fatal-share movement remains sensitive to this filtering.
- **Comparisons:** heavy unit truck and tractor event groups can overlap. The no-recorded-tractor group includes other vehicles and unknown types; it is not a car-only population. Unknown-type sensitivity does not establish complete tractor ascertainment.

## Deliverables and verification

- [Full regenerated report and annual tables](../reports/trends/findings.md).
- [Executed trend notebook](../notebooks/02_descriptive_trends.ipynb).
- [Source repair, baseline and change audit](source_release_update.md).
- [Current dataset validation](dataset_validation.md).
- [Recent-year availability and separate aggregate vintages](data_availability.md).

The analysis recomputes unique event keys, complete 23-year coverage, severity arithmetic, overlap/complement definitions and observed/strict counts against the production build. It uses no fitted model, p-value, sampling confidence interval or exposure-adjusted rate. All three scientific figures and their underlying tables are regenerated from the selected release.

Reproduce with `PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.analyze_trends` after rebuilding the collision table. Input and code fingerprints are in `reports/trends/summary.json`.

## Next analytical gate

The source-repair, missingness audit, [condition comparisons](conditions_findings.md) and [configuration decomposition](configuration_decomposition.md) are complete. See [current status](project_status.md) for the exposure-compatibility priority. Person harm uses the separate validated casualty pipeline and scenarios; exposure compatibility remains necessary for risk estimates. Missing national event years remain explicit.
