# Report evidence and portfolio deliverables

Updated November 4, 2026. Preparation, descriptive analysis, severity baselines, temporal calibration and the calibration transfer study are complete. The expanded `tree_comparison_v1` study is being implemented. Geographic presentation and the three final portfolio formats are pending. The [analysis plan](../docs/analysis_plan.md) tracks dependencies and acceptance evidence.

The acquisition/feasibility phase produced seven full-file record-quality tables and one cross-source benchmark comparison under `tables/`. Their methods, interpretation and limitations are in the [data-quality assessment](../docs/data_quality_assessment.md). Source-linked aggregate extracts and registries are in `data/reference/`, documented in the [source inventory](../docs/source_inventory.md).

| Evidence table | Purpose |
| --- | --- |
| `record_annual_quality.csv` | Source/comparator status, rows, event counts, targets, identity exceptions and consistency checks |
| `quality_missingness.csv` | Per-year/field/state counts and raw-record rates |
| `quality_fields.csv` | Field cardinalities by selected or comparison release |
| `quality_collision_conflicts.csv` | Collision-attribute agreement by year/field |
| `record_value_counts.csv` | Full normalized code profiles; raw originals preserved |
| `record_outcomes.csv` | Person-segment and collision outcomes with explicit grain |
| `record_road_users.csv` | Road-user record counts and overlapping distinct event support |
| `source_benchmark_comparison.csv` | Selected event counts versus a separately scoped publication vintage; unresolved differences retained |

The older 2019 comparator is marked separately and excluded from selected-population totals. Raw-record missingness is not event-level feature availability. Counts, conditional severity proportions, person casualties and exposure rates must remain distinct.

The existing analytical evidence includes 22 standalone figures across the EDA, severity baseline, temporal calibration and stress-test studies, together with fitted model artifacts and six executed notebooks. The 2024 provincial/territorial rate table and 2005–2024 national publication series are already acquired. Boundary acquisition, geographic joins, maps, intervention research and final presentation remain pending. Historical result documents retain their original experiment context.

## Prepared dataset validation

Collision-level preparation is complete. `preparation_*.csv` records normalization, collision profiles, conflicts and source reconciliation. `validation_*.csv` contains independently computed annual totals, audit comparisons, missingness, feature values and domain exceptions. The [validation report](../docs/preparation_validation.md) explains their denominators and exceptions. These quality checks support the completed descriptive analysis and model studies documented below.

## Descriptive analysis

See [combined findings](../docs/descriptive_analysis.md) and [executed notebook](../notebooks/03_exploratory_descriptive_analysis.ipynb). `tables/eda_*.csv` contains 19 analytical evidence tables plus `eda_validation_checks.csv`; `figures/` contains thirteen visually inspected PNGs. Unknown/other codes and sparse groups remain explicit. Run `python -m road_to_safety.explore` for the complete gated reproduction, including independent group-count, denominator and sensitivity checks.

## Frozen severity baselines

[Modeling findings](../docs/severity_modeling.md), [model card](../models/severity_model_card.md), [protocol](../docs/severity_protocol.md) and [notebook](../notebooks/04_chronological_severity_baselines.ipynb) accompany five `severity_*.csv` model tables, a separate validation ledger, and four model figures. Every result remains conditional on recorded fatal/injury collisions. Low precision and late-period calibration gaps are explicit.

## Temporal robustness/calibration v1

[Results](../docs/temporal_calibration_v1_results.md) and the [experiment notebook](../notebooks/05_temporal_robustness_calibration_v1.ipynb) accompany nine analytical `tcal_v1_*.csv` tables, a validation ledger, two producer figures and a notebook-generated low-probability zoom. Frozen source membership, sparse/zero-support groups and the small/uneven gains remain explicit.

## Calibration transfer stress test v1

[Results](../docs/calibration_stress_v1_results.md) and the [sixth notebook](../notebooks/06_calibration_transfer_stress_v1.ipynb) accompany eight `cstress_v1_*.csv` analytical tables, an independent check ledger and two inspected figures. The scoring-only reused 2020–2021 comparison found worsening log loss/Brier in both years; no refit, model search or replacement occurred.

## Expanded research and final presentation

| Deliverable | Status on November 4, 2026 | Required evidence |
| --- | --- | --- |
| `tree_comparison_v1` | Implementation in progress | Six chronological development folds, Random Forest/LightGBM comparison with matching reference methods, reused 2020–2021 stress results, interpretation and independent validation |
| Geographic comparison | Rates acquired, maps pending | Official boundaries, 13 validated jurisdiction joins, 2024 rate map/chart and source notes |
| Technical portfolio | Complete | Executed comparison and synthesis notebooks, polished HTML, methods, findings, limitations and three to five externally supported recommendations |
| Policy PDF | Complete | Six English pages, consistent figures/recommendations and complete visual review |
| Public interactive story | Complete | Local static HTML, supported temporal year controls, 2024 map metric selection, accessible tables and responsive layout |

The new presentations consume reviewed CSV/JSON summaries and retain counting units, periods, denominators, provenance and unknown categories. Every headline and chart must agree with its saved evidence table. The new model study will have a separately versioned protocol, environment, fitted artifacts and receipts. Its developmental rankings and reused retrospective stress performance will be clearly identified. Update this index with result links when each deliverable passes its acceptance checks.

## Geographic comparison and portfolio

The 2024 casualty rates match all 13 official Statistics Canada cartographic jurisdictions. See the [mortality map](figures/geography_map_2024.png), [rate comparison](figures/geography_comparison_2024.png) and [source and join record](../data/reference/geography/jurisdictions_2024.json).

The [technical report](portfolio/technical-report.html), [policy brief](portfolio/road-to-safety-policy-brief.pdf) and [public story](portfolio/index.html) incorporate the independently validated model comparison. The [portfolio bundle](portfolio/road-to-safety-portfolio.zip) contains all three standalone presentations. See [portfolio verification](../docs/portfolio_validation.md) and [experiment instructions](../experiments/tree_comparison_v1/README.md).
