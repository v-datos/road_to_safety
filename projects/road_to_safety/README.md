# Road to Safety: Traffic Accident Analysis

Develop predictive models and uncover insights from Canadian collision data to support road safety decisions.

**Status:** Collision preparation, independent validation and exploratory descriptive analysis completed October 18, 2026. The analytical dataset covers **1999–2021**; separate publication aggregates cover **2005–2024**. The baseline, developmental calibration study and scoring-only 2020–2021 stress test are complete. The selected calibration correction did not transfer favorably; see the stress findings and independent validation.

Open the [stress-test findings](docs/calibration_stress_v1_results.md), [experiment card](models/calibration_stress_v1_card.md) and [sixth notebook](notebooks/06_calibration_transfer_stress_v1.ipynb), or revisit the [temporal calibration results](docs/temporal_calibration_v1_results.md), [experiment card](models/temporal_calibration_v1_card.md) and [fifth notebook](notebooks/05_temporal_robustness_calibration_v1.ipynb), or revisit the [modeling findings](docs/severity_modeling.md), [model card](models/severity_model_card.md) and [model notebook](notebooks/04_chronological_severity_baselines.ipynb), or revisit the [descriptive findings](docs/descriptive_analysis.md) and [executed exploratory notebook](notebooks/03_exploratory_descriptive_analysis.ipynb), or inspect the [validated collision dataset](data/derived/collisions.parquet), [preparation validation report](docs/preparation_validation.md), [modeling contract](docs/modeling_contract.md) and [executed validation notebook](notebooks/02_collision_dataset_validation.ipynb). The [source inventory](docs/source_inventory.md) and [acquisition audit](docs/data_quality_assessment.md) preserve the input evidence.

The selected releases contain **7,729,886 source records and 2,949,846 candidate collisions**, including **47,793 fatal collisions**. These are distinct counting units. Collision targets are internally consistent, but person/vehicle exceptions and differences from newer publication totals remain explicit. The collision dataset is validated with no target exclusions; accident likelihood and local hotspot maps need additional inputs. Three conflicting reported vehicle counts are null and flagged, and remain outside the predictor allowlist.

## Confirmed scope

- All road-user groups and all verified available years, with source-specific coverage and explicit unknown/other classifications.
- Project-owned inputs freshly acquired through the supplied official source route; original truck/bicycle datasets were not reused.
- Fatal versus nonfatal injury collision severity first; accident occurrence in a later phase using compatible exposure and non-crash observations.
- Reproducible analysis, risk-factor evidence, temporal/spatial visualizations and an evidence-linked policy brief. The portfolio will be delivered in English as a technical report and notebooks, a six-page policy brief, and a guided public visual story.

The observed case key is consistent within each selected release but undocumented in the dictionary. The records have no province, coordinates, full calendar date or non-crash exposure. The [analysis plan](docs/analysis_plan.md) and [data contract](docs/data_contract.md) distinguish observed feasibility from future modeling requirements.

## Project structure

| Location | Contents |
| --- | --- |
| `data/sources.json` | Selected originals, comparison release and source fingerprints |
| `data/source_catalog.json` | Source roles, audit status and remaining needs |
| `data/raw/` | Immutable records, dictionary, original HTTP responses and detailed provenance; Git-ignored |
| `data/derived/` | Collision and exception Parquet datasets, preparation manifest and validation receipts; Git-ignored |
| `data/reference/` | Catalog/asset inventories and source-linked aggregate extracts |
| `docs/` | Plan, contracts, source inventory, acquisition notes and quality/feasibility assessments |
| `src/road_to_safety/` | Acquisition, preparation, audits, descriptive analysis, independent reconciliation, and the 4-phase operational decision-support suite (`corridor_pilot`, `typology_severity`, `operational_triage`, `monitor_prospective`) |
| `notebooks/` | Nine executed audit/analysis/model/synthesis/operational-decision-support notebooks |
| `tests/` | Sixty-nine focused regression and operational action-plan tests |
| `reports/tables/` | Audit, preparation, validation and descriptive evidence tables |
| `reports/figures/` | Descriptive, baseline-model and temporal-calibration figures |
| `models/` | Original model card and versioned calibration experiment card; local fitted artifacts in data/derived |

## Reproduce and verify

Run from this directory. The audit used Python 3.13.9 and the locked project environment:

```bash
uv sync --locked --python 3.13 --extra notebook
.venv/bin/python -m road_to_safety.acquire_records
.venv/bin/python -m road_to_safety.acquire_aggregates --offline
.venv/bin/python -m road_to_safety.audit_data --workers 2 --include-comparator
.venv/bin/python -m road_to_safety.verify_sources
.venv/bin/python -m road_to_safety.prepare_collisions --workers 2
.venv/bin/python -m road_to_safety.validate_prepared
.venv/bin/python -m road_to_safety.explore
.venv/bin/python -m unittest discover -s tests -v
```

Record acquisition verifies saved originals and downloads missing pinned inputs. The aggregate offline command requires the preserved captures, regenerates five HTML-table extracts and verifies their hashes. For first acquisition in an empty capture directory, omit `--offline`; the native NCDB query failure remains documented. A later refresh requires a separately preserved snapshot.

The audit scans full files and reuses profiles only when input/manifest/code fingerprints and source roles match. The preparation builds one candidate collision per source/year/case and preserves row-numbered exceptions. Independent validation reconciles all source records, targets and missingness. The first two notebooks executed all seven code cells each. The exploratory notebook saves thirteen chart outputs; standalone charts were visually inspected. Whole-notebook rendered previews remain unverified because of the recorded browser URL policy restriction. See the [aggregate audit](docs/aggregate_source_audit.md) for the precise native-export and source-text limitations.

## Frozen severity baseline

Training is 1999–2016, validation 2017–2019, and retrospective temporal test 2020–2021. Unknown/other categories remain distinct; no feature-completeness exclusions or class balancing. The fixed eight-feature L2 logistic model improves test log loss (0.092626 vs 0.097444) and Brier (0.019177 vs 0.019369), with ROC-AUC 0.6992. Its illustrative threshold has 82.11% recall and 2.92% precision, flagging 55.59% of test collisions. Mean predicted severity 1.6036% is below observed 1.9746%. These are modest retrospective gains with material calibration/alert-burden limitations, not deployment evidence.

Reproduce this phase from the preserved frozen upstream inputs:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MPLCONFIGDIR=/tmp/road-to-safety-mpl .venv/bin/python -m road_to_safety.fit_severity
.venv/bin/python -m road_to_safety.validate_severity
```

The [frozen protocol](docs/severity_protocol.md) binds the original preparation/EDA receipts. Keep those receipts with the run; regenerating or refreshing upstream evidence requires a separately versioned protocol rather than overwriting the frozen experiment. The full earlier acquisition/preparation commands above document their own stages; the severity notebook validates saved model outputs without refitting.

## Temporal robustness and calibration v1

The [new frozen protocol](docs/temporal_calibration_v1_protocol.md) evaluates 2014–2019. For year t, fit 1999…t−3, calibrate t−2/t−1 and evaluate t. All six folds converged. Mean annual log loss is 0.07373510 unchanged, 0.07370461 intercept-only and0.07370303 sigmoid. Sigmoid meets the declared 4/6-year and Brier guardrails, but its relative log-loss gain is only 0.0435%; both corrections worsen 2018–2019. This is developmental method selection, not operational validation. The original baseline remains unchanged, and this version does not score 2020–2021.

Validate the saved version using `.venv/bin/python -m road_to_safety.validate_temporal_calibration_v1`. Completed v1 artifacts are protected from overwrite; refitting requires a separate working copy with the preserved pinned inputs and no completed v1 manifest. The [results](docs/temporal_calibration_v1_results.md) explain reproduction and all limitations.

## Frozen calibration transfer stress test v1

The saved final development model and sigmoid correction were applied to 2020–2021 without fitting or tuning. Transfer was not demonstrated: sigmoid worsens log loss and Brier in both years and increases aggregate underprediction. Existing baseline and development artifacts remain unchanged. Read the [results](docs/calibration_stress_v1_results.md), [protocol](docs/calibration_stress_v1_protocol.md) and [independent audit](docs/calibration_stress_v1_validation.md). Validate the saved version using `.venv/bin/python -m road_to_safety.validate_calibration_stress_v1`.

## Portfolio milestones

| Status | Work | Evidence |
| --- | --- | --- |
| Complete | Record audit, preparation and descriptive analysis | Validated 1999–2021 collision table, executed notebooks and descriptive figures |
| Complete | Prevalence and logistic baselines, temporal calibration and transfer | Frozen model cards, protocols and validation receipts |
| Complete | Expanded Random Forest and LightGBM comparison | Separate experiment, chronological development and reused 2020–2021 evaluation |
| Complete | 2024 jurisdiction geography | Validated map and rate comparison for all 13 jurisdictions |
| Complete | Technical HTML and synthesis notebooks | Verified evidence, geographic and model results, and evidence-linked recommendations |
| Complete | Policy PDF and public visual story | Six-page brief and downloadable interactive HTML |

The expanded comparison uses the same eight approved predictors. Its development folds evaluate 2014–2019. The reused 2020–2021 period measures retrospective performance after model and threshold selection. Newer untouched microdata would be needed for independent temporal evidence. See the [current analysis plan](docs/analysis_plan.md) and [experiment instructions](experiments/tree_comparison_v1/README.md).

Official starting points: [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?c=100-0-0&l=en), [Motor Vehicle Casualties Dashboard](https://tc.canada.ca/en/road-transportation/statistics-data/2025/motor-vehicle-casualties-dashboard), [Transport Canada statistics and data](https://tc.canada.ca/en/road-transportation/statistics-data), and the [NCDB record/dictionary catalog](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a).


## Completed portfolio

Open the [interactive visual story](reports/portfolio/index.html), [technical report](reports/portfolio/technical-report.html) and [six-page policy brief](reports/portfolio/road-to-safety-policy-brief.pdf), or download the [shareable portfolio bundle](reports/portfolio/road-to-safety-portfolio.zip).

The completed comparison includes 120 tree fits and 12 matching baseline fits. LightGBM improved development log loss in all six years and passed the predeclared Brier guardrail. Random Forest improved in three of six years and fell short of the development gate. In the reused 2020–2021 evaluation, pooled log loss is 0.091502 for LightGBM and 0.092573 for logistic regression. At the selected threshold, LightGBM has 81.86% recall and 3.02% precision. These are retrospective results with substantial false-positive burden.

See the [model card](models/tree_comparison_v1_card.md), [comparison notebook](notebooks/07_tree_comparison_v1.ipynb), [synthesis notebook](notebooks/08_portfolio_synthesis.ipynb) and [portfolio verification](docs/portfolio_validation.md).

## Operational Decision-Support Action Plan (Phases 1–4)

The four-phase Recommended Action Plan has been implemented and verified (69/69 tests passing):

1. **Phase 1 — Corridor-Level Pilot Linkage (`road_to_safety.corridor_pilot`)**: Joins 7,673 City of Toronto KSI collisions (2006–2023) to 50,083 Centreline road segments and 45,043 AADT traffic count studies (`14,410` monitored segments; `104.44B` VKT exposure-proxy screening estimate) alongside `7,911` Quebec MTQ highway sections. Audits short-duration count temporal coverage (median 72h, FHWA TMG caveats) and demonstrates high corridor EB ranking stability (Spearman $\rho = 0.982$ under 2006–2023 collision-window constraints). Fits offset-adjusted Poisson and Negative Binomial ($\alpha = 0.7749$) Safety Performance Functions (`4.706` KSI / $10^8$ VKT; `0.636` fatal / $10^8$ VKT) and ranks priority corridors via Empirical Bayes (EB) shrinkage.
2. **Phase 2 — Road-User & Vehicle Typologies (`road_to_safety.typology_severity`)**: Reintroduces person-level `P_USER` and vehicle-level `V_TYPE` across all `2,949,846` canonical NCDB collisions (`1999–2021`). Boosts out-of-time 2020–2021 test **ROC-AUC from `0.6958` to `0.7628` (+6.70 pp)** and **PR-AUC from `4.15%` to `7.47%` (+80.0% relative lift)** while lowering log-loss from `0.09276` to `0.08802` (-5.11%). Isolates adjusted fatality odds ratios for road tractors (`5.99x`), unit heavy trucks (`3.17x`), pedestrians (`2.69x`), and heavy-freight $\times$ VRU collisions (`2.54x` interaction; `12.46%` unadjusted fatality rate).
3. **Phase 3 — Operational Threshold Tuning & Tiered Triage (`road_to_safety.operational_triage`)**: Replaces the flat 80% recall heuristic (`55.94%` flagged, `2.89%` precision) with cost-utility / Vickers-Elkin Net Benefit curves and a **3-Tier Operational Triage Architecture** (`Tier 1 Critical 10:1` at `14.27%` precision / `14.24x` relative risk; `Tier 2 Priority 25:1` at `7.26%` precision / `34.46%` recall; `Tier 3 Watchlist 50:1` cutting false alarms by half while capturing `63.50%` of fatalities) plus rural high-speed dispatch vs. urban VRU operating curves.
4. **Phase 4 — Prospective Data Monitoring Pipeline (`road_to_safety.monitor_prospective`)**: Automates Open Canada CKAN catalog checks (`1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a`), schema/sentinel audits, covariate Population Stability Index (`PSI`), and calibration (`O/E`, $\Delta \alpha$, `ECE`) governance alerts (`GREEN` / `AMBER` / `RED`) for 2022+ NCDB releases.

Inspect the [operational action plan results](docs/operational_action_plan_results.md), [operational model card](models/typology_and_corridor_card.md), and [executed ninth notebook](notebooks/09_operational_decision_support.ipynb).
