# Initial collision-severity model card

## Intended interpretation

The model estimates whether a **recorded fatal/injury candidate collision** is fatal, conditional on eight recorded conditions. A positive label means at least one fatality in the collision, and a negative label means a nonfatal injury collision. It does not estimate collision occurrence, individual death probability, or intervention effects. Property-damage-only incidents and non-crash observations are absent.

The dataset comprises selected official annual NCDB releases, one collision row per release-scoped `(source_id, C_YEAR, C_CASE)`, 1999–2021. These case identifiers do not establish independently verified real-world uniqueness across releases. The upstream audit and preparation receipts remain the authority on record identity, conflicts, provenance and current-source differences.

## Frozen design

The machine-readable [protocol](../data/reference/severity_protocol.json) was frozen before fitting. Train: 1999–2016; validation: 2017–2019; test: 2020–2021. Every eligible collision is included once. The test years were already inspected descriptively; this is a retrospective temporal holdout, not an untouched prospective test.

The prevalence baseline is the training fatal fraction, constant for all rows. The only fitted feature model is L2 logistic regression, C=1, lbfgs, max_iter=1000, tol=1e-7, intercept enabled, random_state=2026. No class/sample weights, resampling, interactions, search, calibration correction, or train-plus-validation refit are used.

Eight categorical predictors are month, weekday, hour, road configuration, weather, road surface, road alignment and traffic control. Explicit dictionary domains and reference categories are fixed external metadata. The encoder is fitted on training rows only; numeric-looking codes are categories. Unknown, unavailable and other are retained separately. Nulls or unsupported codes reject the run. Dictionary levels absent in training have zero coefficients and explicit unsupported-evidence flags; neutral scores do not establish absence of association. Year, source/case IDs, target proxies, casualty information and preparation diagnostics are excluded from predictors.

All coefficients and `exp(coefficient)` are exported against named references. These are regularized conditional associations with other included predictors held fixed, without causal, significance or standard-error claims. Unmeasured collision context, speed, geography, exposure and road users can confound them. Recorded conditions are post-crash reports; prospective feature availability remains unverified.

## Evaluation and operating points

Probability performance uses natural-log loss and Brier score; ranking uses average precision and ROC AUC. Average precision is recall-step weighted precision. One-class ranking metrics are null. Confusion counts, precision, recall and F1 are reported at 0.5 and an illustrative validation-selected threshold. The latter maximizes precision among distinct validation logistic scores attaining at least 80% recall; precision ties select the higher threshold. The same frozen numerical threshold applies to both models, including the constant-score baseline. No threshold uses test labels. It is not a cost-optimal or recommended operational cutoff.

Reliability uses ten fixed [0,.1), …, [.9,1] bins, empty bins retained, with bin counts, fatal counts, observed fractions and mean probabilities. ECE is descriptive and dependent on these coarse bins; low prevalence can make an aggregate ECE deceptively reassuring. No calibration correction was fitted. Annual observed prevalence and average predictions supplement the reliability plots.

Full-cohort metrics are partitioned by split, every year, and mutually exclusive feature status. Unknown/unavailable takes precedence over other in that summary partition; separate `has_other` and `has_unknown_or_unavailable` flags retain overlap. Test, 2020 and 2021 each have separate per-feature categorical results. A subgroup is sparse if n<100 or fatal count<5, and is retained with a flag. Feature distributions preserve every dictionary level, including zero support, by split and year. No exhaustive interaction search is performed.

## Reproduction and evidence

From the project directory:

```sh
uv sync --locked --python 3.13 --extra notebook
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MPLCONFIGDIR=/tmp/road-to-safety-mpl .venv/bin/python -m road_to_safety.fit_severity
.venv/bin/python -m road_to_safety.validate_severity
```

`data/derived/severity_model.json` contains exact domain order, dropped references, encoded feature order, coefficients/intercept, training prevalence, convergence information and threshold. `severity_predictions.parquet` preserves every collision identity, label, split, both probabilities, support flags and classification flags. `severity_manifest.json` records protocol/input/code/environment hashes and output fingerprints. The independent validation receipt is separate and must pass before numerical claims are accepted.

The initial execution was interrupted before outputs or result inspection to complete reporting and reduce subgroup-mask memory. The frozen specification and model configuration were unchanged; the completed run is an operational retry, not model selection or tuning.

## Fitted results

The solver converged after **205 iterations** with no convergence warning. Training includes **2,455,890 collisions / 39,491 fatal**, validation **330,376 / 5,072**, and test **163,580 / 3,230**. The training prevalence is 1.6080%. Eleven dictionary-supported levels are absent in training and also absent in validation/test; every scored row therefore has training support for each individual level. This establishes level support, not support for every joint feature combination.

| Partition | Model | Log loss | Brier | ROC AUC | Average precision |
|---|---|---:|---:|---:|---:|
| Validation | Prevalence | 0.079369 | 0.015117 | 0.500000 | 0.015352 |
| Validation | Logistic | 0.075583 | 0.014991 | 0.696042 | 0.034163 |
| Test | Prevalence | 0.097444 | 0.019369 | 0.500000 | 0.019746 |
| Test | Logistic | 0.092626 | 0.019177 | 0.699171 | 0.042081 |

The logistic model improves test log loss by approximately 0.004818 and Brier score by 0.000192 in absolute terms versus the training-prevalence baseline. The improvement also holds separately in 2020 and 2021; these are descriptive comparisons on this fixed retrospective cohort, without uncertainty intervals or a deployment-success claim.

| Source year | Observed fatal fraction | Mean logistic probability | Logistic log loss | Baseline log loss | Logistic Brier | Baseline Brier |
|---|---:|---:|---:|---:|---:|---:|
| 2019 (validation) | 1.5483% | 1.5460% | 0.076075 | 0.079908 | 0.015118 | 0.015244 |
| 2020 (test) | 2.0028% | 1.6068% | 0.093622 | 0.098603 | 0.019439 | 0.019642 |
| 2021 (test) | 1.9476% | 1.6006% | 0.091673 | 0.096334 | 0.018926 | 0.019108 |

Ranking remains around ROC AUC 0.70 in both test years, but average predicted probability is materially below observed fatal frequency. In pooled test the model predicts 1.6036% against 1.9746% observed. A ranking improvement does not establish reliable absolute probabilities under the changed late-period population. Feature-distribution and missingness tables document measured composition changes, but unmeasured exposure, source/release differences and reporting cannot be separated from real-world changes. The low fatal prevalence and coarse ten-bin ECE require particular care: 163,509 of 163,580 test predictions occupy the first bin; the two higher occupied bins have only 70 and one collision. All occupied calibration bins are shown and all zero bins remain in CSV evidence.

The validation-selected threshold is **0.011511536878929743**, with validation recall **80.0079%** and precision **2.2697%**. On test it yields **82.1053% recall**, **2.9166% precision**, 2,652 true positives, 88,276 false positives, 578 false negatives and 72,074 true negatives. It flags 90,928 / 163,580 collisions (55.59%) to capture those 2,652 fatal collisions. This low precision and broad flagging burden make the cutoff illustrative rather than an operational recommendation. Because the prevalence baseline's score exceeds that threshold, it flags every collision: 100% recall and precision equal to observed prevalence. At threshold 0.5 both models predict no fatal collisions in this dataset; the full zero-denominator classification metrics and confusion counts are retained.

The next research decision should consider the calibration shortfall and intended decision costs before choosing another model or threshold. Any future recalibration or model comparison needs a new development protocol and independent later evaluation data; repeatedly adapting to this same 2020–2021 holdout would turn it into development data.
