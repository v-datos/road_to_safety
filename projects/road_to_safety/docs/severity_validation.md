# Independent severity-model validation

This audit checks the reproducible implementation of the frozen retrospective severity experiment. It does not establish prospective usefulness, collision-occurrence risk, deployment readiness or causal policy effects. The audit reads original prepared collision rows and saved per-collision predictions; it never refits a model.

## Frozen design and provenance

The experiment uses `data/reference/severity_protocol.json`, frozen before fitting with SHA-256 `7684a32e919a0b73f57ed55e7c1c796c4cb5a73c1a62cdeb76a1ff8889259491`. Whole candidate collisions are assigned to 1999–2016 training, 2017–2019 validation and 2020–2021 test periods using source year. The target remains the validated fatal-versus-nonfatal-injury collision outcome. Each source-scoped collision identity must appear exactly once in the prediction artifact; source labels must match exactly.

The auditor verifies the eight-feature allowlist, dictionary-fixed category order and references, raw supported category membership, coefficient reconstruction of every saved logistic probability, finite probability ranges, unchanged input fingerprints, and model/manifest bindings to the frozen protocol. The baseline must equal the training prevalence for every collision, including validation and test collisions.

Code review of the producer establishes that the encoder is fitted on training rows with externally fixed dictionary categories, and logistic regression is fitted on training rows/labels only. Model parameters match the predeclared settings; no weighting, resampling, calibration fitting or hyperparameter search occurs. An independent normalized gradient calculation checks stationarity of the exported coefficients for the **training-only** L2-penalized logistic likelihood. This numerical consistency check complements code/provenance review; exported outputs alone cannot cryptographically prove which labels a process read.

## Independent calculations

`src/road_to_safety/validate_severity.py` implements calculations separately from the fitting module:

- ROC area uses cumulative true/false positives over distinct descending score groups and trapezoidal integration. Tied scores remain grouped.
- Average precision sums each positive-recall increment times cumulative precision; it is not trapezoidal precision–recall area. One-class ranking metrics remain undefined.
- Natural-log binary log loss uses float64 epsilon clipping. Brier score is mean squared probability error.
- Confusion matrices use inclusive `probability >= threshold`, with denominators retained. Precision, recall and F1 use zero for undefined zero-denominator classification ratios, as frozen.
- Ten fixed calibration bins retain empty bins, include probability 1 in the last bin, and independently reconcile counts, fatal counts, mean predictions and observed proportions. Expected calibration error uses count-weighted absolute bin gaps.
- The illustrative threshold maximizes validation precision among distinct logistic score thresholds satisfying recall at least 0.80. Equal precision selects the higher threshold. Merely choosing the highest threshold satisfying recall is **not** equivalent. The same numerical threshold applies to the prevalence baseline and logistic model; neither test year selects or changes it.

All emitted split, annual, quality-group and late-year individual-feature subgroup metrics are recomputed from saved predictions joined to original prepared events. Required annual output includes both 2020 and 2021 separately. Quality groups use unknown/unavailable precedence over “other”; overlapping source flags are also checked. The auditor reconciles training/validation/test category counts, all dictionary levels including zero-support levels, training-unobserved score support, coefficient table values and odds ratios. Unknown, unavailable and other remain distinct in year/split distributions. Sparse groups are retained and flagged when count <100 or fatal count <5.

## Scope and limitations

The 2020–2021 population had already been examined descriptively before the protocol froze. These years are a fixed retrospective temporal holdout, **not a pristine prospective test**. Per-year and subgroup checks expose case-mix/reporting shifts and model behavior; they cannot isolate pandemic effects from release/reporting changes or establish causal mechanisms. Training performance is in-sample; validation performance also supports threshold selection. Test performance is an assessment of this single frozen specification, not grounds for tuning that same experiment.

The source cohort contains recorded fatal/injury collisions only, with no exposure/non-collision observations or geographic fields. Conditions are recorded after a collision; their availability for prospective decisions remains unverified. Penalized odds ratios are conditional associations under the fitted additive model, without standard errors or significance claims. No uncertainty intervals were predeclared for model metrics. Sparse and training-unobserved categories deserve especially limited interpretation.

## Reproduction and evidence

Run from the project directory after the frozen fitting artifact exists:

```bash
.venv/bin/python -m road_to_safety.validate_severity
.venv/bin/python -m unittest discover -s tests -p test_validate_severity.py -v
```

The machine-readable receipt is `data/derived/severity_validation.json`; every named check appears in `reports/tables/severity_validation_checks.csv`. The receipt binds the validator, frozen protocol, prepared data, prediction artifact, model record and producer manifest by SHA-256. Edge/mutation tests cover split boundaries, outside-population years, nonfinite/out-of-range probabilities, tied ranking/confusion thresholds, precision-max threshold selection, changed coefficients, forbidden features and one-class/zero-prediction metrics.

## Final audited result

**Ready within the implementation scope, with the interpretation limits above.** All **22 independent check families passed**, with no failures. The audit reconciled all **2,949,846** scored candidate collisions, **1,400** metric rows, **7,000** fixed-bin calibration rows and **116** declared feature levels against original prepared events. Six validator edge/mutation tests passed. The final producer manifest SHA-256 is `d080cc69c582f748441c5492a537bfb032efc48cc2c00f4b548896e65acc42d7`.

| Partition | Source years | Candidate collisions | Fatal collisions |
|---|---|---:|---:|
| Training | 1999–2016 | 2,455,890 | 39,491 |
| Validation | 2017–2019 | 330,376 | 5,072 |
| Test | 2020–2021 | 163,580 | 3,230 |

The logistic model converged in 205 iterations, below the frozen cap of 1,000, and passed training-only penalized-likelihood stationarity and score-reconstruction checks. Eleven dictionary levels have no training observations; all eleven are also absent from validation and test, with neutral zero coefficients and explicit support flags. Thus this run has no scored collision containing a training-unobserved level, while preserving the future limitation of neutral treatment for such supported codes.

The independently reproduced illustrative threshold is **0.011511536878929743**. It yields validation recall **80.0079%**, test recall **82.1053%**, and test precision **2.9166%**. Test confusion counts are **2,652 true positives, 88,276 false positives, 578 false negatives and 72,074 true negatives**. The low precision and large false-positive burden prevent an operational recommendation from this threshold alone.

| Assessment population | Model | Log loss | Brier score | ROC-AUC | Average precision |
|---|---|---:|---:|---:|---:|
| Test 2020–2021 | Training prevalence | 0.097444 | 0.019369 | 0.500000 | 0.019746 |
| Test 2020–2021 | Logistic | 0.092626 | 0.019177 | 0.699171 | 0.042081 |
| 2020 only | Training prevalence | 0.098603 | 0.019642 | 0.500000 | 0.020028 |
| 2020 only | Logistic | 0.093622 | 0.019439 | 0.700600 | 0.043246 |
| 2021 only | Training prevalence | 0.096334 | 0.019108 | 0.500000 | 0.019476 |
| 2021 only | Logistic | 0.091673 | 0.018926 | 0.697752 | 0.041108 |

Logistic probability scores improve over the fixed prevalence baseline in the pooled test set and each test year, under the frozen acceptance comparison. This does not remove calibration concerns: the model's mean predictions are about **1.607% in 2020** and **1.601% in 2021**, below observed fatal proportions of **2.003%** and **1.948%**, respectively. This mismatch is reported rather than corrected using test labels. Source-year/split feature distributions, distinct sentinel classes, observed individual-feature subgroups and sparse flags all reconcile independently; their existence supports assessment of changes, without identifying their cause.

The broad full-cohort independent checks and focused mutation tests provide evidence of implementation correctness. They do not validate prospective feature availability, policy intervention effects, stability after 2021, decision costs, or local fairness/road-user-group performance that the prepared collision features do not identify.
