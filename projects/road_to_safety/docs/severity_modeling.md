# Chronological baseline severity modeling

Completed October 18, 2026. This phase freezes a retrospective evaluation protocol, fits a training-prevalence baseline and one categorical logistic regression, and independently verifies the saved run. It makes no accident-occurrence, individual fatality, causal intervention or deployment claim.

## Principal result

The logistic model improves pooled 2020–2021 log loss from **0.097444 to 0.092626** (4.94% relative reduction) and Brier score from **0.019369 to 0.019177** (0.99% relative reduction). Its test ROC-AUC is **0.6992** and average precision **4.208%**, against test fatal prevalence **1.975%**. This supports a modest predictive association within the archived collision population; it does not establish operational usefulness.

At the validation-selected threshold **0.011511537**, pooled test recall is **82.105%** and precision **2.917%**. It flags **90,928/163,580 collisions (55.59%)**, including **88,276 nonfatal injury collisions**. This large false-positive burden matters as much as the recall gain. At threshold 0.5 neither model identifies any fatal collision in these splits.

Raw logistic probabilities underpredict the observed fatal proportion in both test years. Ranking discrimination remains around 0.70, but stable ranking is not the same as calibrated probabilities. No calibration correction or model change was fitted after seeing test results.

## Frozen protocol and population

The [machine protocol](../data/reference/severity_protocol.json) was fingerprinted before fitting. Its immutable SHA256 is `7684a32e919a0b73f57ed55e7c1c796c4cb5a73c1a62cdeb76a1ff8889259491`. The [human protocol](severity_protocol.md) defines all metrics, threshold ties, categorical handling, calibration bins and acceptance checks. The earlier preparation contract and original inputs were not changed.

| Partition | Collision years | Candidate collisions | Fatal collisions | Role |
|---|---|---:|---:|---|
| Training | 1999–2016 | 2,455,890 | 39,491 | Fit prevalence, encoder and logistic coefficients |
| Validation | 2017–2019 | 330,376 | 5,072 | Select only the illustrative recall threshold |
| Temporal test | 2020–2021 | 163,580 | 3,230 | Evaluate fixed outputs; report each year separately |

All **2,949,846 eligible candidate collisions** remain in exactly one partition. No complete-case deletion, random splitting, resampling, class weighting or train+validation refit is used. The candidate key is release-scoped `(source_id,C_YEAR,C_CASE)`; dictionary documentation of case semantics remains absent. One annual release is selected per year. Newer aggregate publications are separate vintages and are not joined into the modeling cohort.

**Retrospective holdout limitation:** 2020–2021 had already been examined descriptively during EDA. No test predictions were used to select the model or threshold, but these years are not wholly unseen prospective evidence. Any later iteration must disclose reuse of this test population; this run cannot establish future surveillance or real-time performance.

## Estimator, categorical handling and interpretation

The baseline is the training fatal fraction, **1.60801%**, held constant in every partition. The sole fitted model is L2 logistic regression with C=1, lbfgs, maximum 1,000 iterations, tolerance 1e-7, intercept and seed 2026; no hyperparameter search or fitted calibration. The saved model converged in **205 iterations**.

Only eight approved categorical predictors enter: month, weekday, hour, road configuration, weather, surface, alignment and traffic control. Absolute year is partitioning/diagnostic information only. Identifiers, source proxies, targets, person outcomes, casualty counts, collision configuration, involved vehicle count and preparation diagnostics are excluded. Conditions are recorded after collisions; pre-crash availability and whether a condition was affected by the event remain unverified. This is a conditions-based severity scenario model.

One-hot domains come from the frozen dictionary, not test vocabulary. Reference levels are January, Monday, hour12, non-intersection, clear/sunny weather, dry/normal surface, straight/level alignment and no traffic control. Unknown U/UU, other Q/QQ and jurisdiction-unavailable X/XX retain distinct columns. Out-of-domain/null/conflicting inputs reject the run. A dictionary-supported level absent in training retains an all-zero training column and neutral coefficient, explicitly flagged as unsupported evidence.

The domain grid contains **116 levels**, including **11 not observed in training**. Their validation/test incidence is retained in the level-support evidence. A zero coefficient for an absent level does not demonstrate that the level has no association.

The coefficient table exports coefficients, exponentiated conditional odds ratios, reference labels, training support and absent-level flags. Effects are L2-regularized conditional associations, not causal road-safety effects. No standard errors, significance tests or confidence intervals are asserted. The model is additive on log odds; interactions and nonlinear effects beyond categorical levels are not modeled.

## Probability performance

Probability metrics do not depend on the classification threshold. Log loss and Brier are primary comparisons; ROC-AUC and average precision describe ranking. Average precision uses recall-step weighting rather than trapezoidal PR area. Accuracy is not a primary metric because the fatal class is rare.

| Period | Model | n | Fatal % | Mean predicted % | Log loss | Brier | AP % | ROC-AUC | ECE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | prevalence | 2,455,890 | 1.6080 | 1.6080 | 0.082364 | 0.015822 | 1.6080 | 0.5000 | 0.000000 |
| train | logistic | 2,455,890 | 1.6080 | 1.6080 | 0.077959 | 0.015662 | 3.7968 | 0.7068 | 0.000036 |
| validation | prevalence | 330,376 | 1.5352 | 1.6080 | 0.079369 | 0.015117 | 1.5352 | 0.5000 | 0.000728 |
| validation | logistic | 330,376 | 1.5352 | 1.5560 | 0.075583 | 0.014991 | 3.4163 | 0.6960 | 0.000207 |
| test | prevalence | 163,580 | 1.9746 | 1.6080 | 0.097444 | 0.019369 | 1.9746 | 0.5000 | 0.003666 |
| test | logistic | 163,580 | 1.9746 | 1.6036 | 0.092626 | 0.019177 | 4.2081 | 0.6992 | 0.003788 |
| 2019 | prevalence | 104,630 | 1.5483 | 1.6080 | 0.079908 | 0.015244 | 1.5483 | 0.5000 | 0.000597 |
| 2019 | logistic | 104,630 | 1.5483 | 1.5460 | 0.076075 | 0.015118 | 3.4066 | 0.6978 | 0.000080 |
| 2020 | prevalence | 79,990 | 2.0028 | 1.6080 | 0.098603 | 0.019642 | 2.0028 | 0.5000 | 0.003947 |
| 2020 | logistic | 79,990 | 2.0028 | 1.6068 | 0.093622 | 0.019439 | 4.3246 | 0.7006 | 0.004022 |
| 2021 | prevalence | 83,590 | 1.9476 | 1.6080 | 0.096334 | 0.019108 | 1.9476 | 0.5000 | 0.003396 |
| 2021 | logistic | 83,590 | 1.9476 | 1.6006 | 0.091673 | 0.018926 | 4.1108 | 0.6978 | 0.003565 |

The primary predeclared improvement assessment passes directionally in pooled test and in each of 2020 and 2021: both log loss and Brier improve over the training-prevalence baseline. No uncertainty interval or test of the differences is claimed. The small Brier improvement should not be described as a large predictive gain.

## Classification threshold and tradeoffs

Candidate thresholds are distinct validation logistic probabilities. Among thresholds with validation recall≥80%, select maximum precision; exact precision ties choose the higher threshold. Predictions use probability≥threshold, including all score ties. Freeze this number before test scoring, then apply the same threshold to both models in every period. This is an illustrative operating point, not an intervention-cost optimum or policy recommendation.

| Period | Model | Threshold | TP | FP | FN | TN | Precision % | Recall % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | prevalence | 0.011511537 | 5,072 | 325,304 | 0 | 0 | 1.5352 | 100.0000 |
| validation | logistic | 0.011511537 | 4,058 | 174,732 | 1,014 | 150,572 | 2.2697 | 80.0079 |
| test | prevalence | 0.011511537 | 3,230 | 160,350 | 0 | 0 | 1.9746 | 100.0000 |
| test | logistic | 0.011511537 | 2,652 | 88,276 | 578 | 72,074 | 2.9166 | 82.1053 |

Because the constant baseline probability exceeds the selected logistic threshold, it flags every collision at that threshold: recall 100% and precision equal to period prevalence. This is an honest common-threshold comparison, not a separately optimized baseline operating point. The full CSV also reports threshold 0.5 and all annual/subgroup confusion counts.

## Calibration and 2020–2021 stability

Calibration uses ten fixed equal-width bins on [0,1], retaining empty bins with undefined averages. ECE is the count-weighted absolute difference between mean prediction and observed fraction within those bins. It is descriptive and bin-dependent. Most probabilities fall in the first bin; a small ECE is not proof of calibration in finer risk ranges. Occupied high-probability bins can have only one observation and are visually flagged by their counts in the table. No post-hoc recalibration is fitted.

The pooled test observed fatal fraction is **1.9746%**, versus mean logistic prediction **1.6036%**: a gap of **0.3710 percentage points**. Test ECE is **0.003788**, compared with baseline **0.003666**; improved proper probability scores do not imply improved calibration on every summary.

Year-specific probability/ranking/threshold metrics show whether a pooled result conceals 2020 or 2021 degradation. The feature-distribution table reports every dictionary level, including zero-support states, for train/validation/test and all 23 source years. Unknown, other and unavailable are separate. Model metrics also compare mutually exclusive feature-status groups; unknown has precedence when a record contains both unknown and other, and overlapping flags remain available in predictions.

For every approved feature, categorical subgroup metrics are reported for pooled test,2020 and 2021. Groups with n<100 or fatal<5 are flagged and retained. These feature tables overlap and must not be summed to count unique collisions. Small groups and absent training levels do not support stable rankings or fairness conclusions. Road-user demographics are outside the condition-only model; this is not a demographic fairness audit.

Changes in prevalence, condition distributions and data availability cannot be separated into exposure, reporting, release-vintage and real-world mechanisms from this dataset. Source-format normalization and input validation do not eliminate this limitation.

### Test feature availability and sparse support

The mutually exclusive quality groups have different prevalence, calibration gaps and recall at the same frozen threshold. These comparisons describe selected collisions; they do not show that unknown coding causes a different outcome.

| Feature-status group | n | Fatal | Observed fatal % | Mean prediction % | Precision % | Recall % |
|---|---:|---:|---:|---:|---:|---:|
| complete_stated | 129,440 | 2,536 | 1.9592 | 1.6050 | 2.891 | 81.349 |
| contains_unknown_or_unavailable | 24,303 | 459 | 1.8887 | 1.4367 | 3.053 | 79.303 |
| contains_other | 9,837 | 235 | 2.3889 | 1.9973 | 2.942 | 95.745 |

Among 105 observed per-feature categories in each late-period summary, **17 pooled-test groups**, **22 groups in 2020**, and **23 in 2021** meet the sparse warning. Their estimates remain visible and should not be ranked as reliable standalone evidence. Eleven supported dictionary levels are absent in every split, so no observed validation/test level lacks marginal training support; joint combinations can still be unfamiliar.

For example, unknown traffic-control share rises from **4.3710% in training** to **5.3712% in validation** and **5.9408% in test**. Unknown road-configuration share is **8.4297%, 5.5285% and 5.6070%**, respectively. These changing coding/case-mix distributions support separate year and availability diagnostics; they do not identify a cause for the calibration shift.

## Artifacts, reproduction and checks

- [Executed model notebook](../notebooks/04_chronological_severity_baselines.ipynb): protocol, bounded metrics, figures, coefficients and independent checks.
- [Model card](../models/severity_model_card.md): intended use, measured results, limitations and prohibited interpretations.
- [Independent validation](severity_validation.md) and `reports/tables/severity_validation_checks.csv`: source joins, score/metric reconciliation and implementation evidence.
- `reports/tables/severity_metrics.csv`: split, annual, quality-status and categorical subgroup metrics, both models and both thresholds.
- `reports/tables/severity_calibration.csv`: all fixed bins, counts, fatal numerators and averages.
- `reports/tables/severity_coefficients.csv`, `severity_training_levels.csv`: conditional coefficients and category support.
- `reports/tables/severity_feature_distributions.csv`: full split/year category grid and sentinel classes.
- `reports/figures/severity_*.png`: PR, reliability, annual diagnostics and coefficient charts.
- `data/derived/severity_predictions.parquet`: all source keys, targets, split labels, probabilities and classifications; local derived data.
- `data/derived/severity_model.json`: portable logistic intercept/coefficients plus ordered encoding, references, classes and thresholds.
- `data/derived/severity_manifest.json`, `severity_validation.json`: producer and independent receipts with input/code/environment/output fingerprints.

```bash
uv sync --locked --python 3.13 --extra notebook
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MPLCONFIGDIR=/tmp/road-to-safety-mpl .venv/bin/python -m road_to_safety.fit_severity
.venv/bin/python -m road_to_safety.validate_severity
.venv/bin/python -m unittest discover -s tests -v
```

The protocol checks the upstream preparation and EDA receipts before fitting. All **22 independent checks** passed, with no failures, and all **37 regression tests** passed. Independent validation joins every predicted key back to the source cohort, reconstructs every logistic score from coefficients without refitting, recomputes baseline prevalence and threshold selection, and checks probability/ranking/confusion/calibration metrics and subgroup denominators. Focused tests exercise nonmonotonic precision optimization, tied scores, probability corruption, forbidden features, changed coefficients, split boundaries and bin endpoints.

An operational reporting-memory retry used the same fixed estimator/settings before results were inspected; it is not a model-selection search. Standalone chart images are visually inspected. The notebook executed all 12 code cells with four saved PNG outputs and no errors; whole-notebook page rendering remains unverified because of the previously recorded browser URL-policy restriction.

## Next project step

Treat this as a completed baseline, not a deployed safety score. The next modeling iteration should first specify development-only temporal robustness checks and a calibration strategy, with explicit disclosure that the 2020–2021 test has now been evaluated. Compare any refinement against this frozen run and avoid repeatedly claiming an untouched test. New post 2021 record-level data or a prospective cohort would provide stronger future validation if acquired and audited.

Candidate improvements should be justified from training/validation evidence rather than test-driven tuning. Before operational recommendations, define the decision, acceptable alert burden and error costs, verify feature availability, and obtain exposure/local evidence as needed. Accident occurrence and local hotspot maps still require additional datasets.
