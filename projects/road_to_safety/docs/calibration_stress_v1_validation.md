# Independent validation: frozen calibration transfer stress test v1

Validated on 20 October 2026. **Passed: 30 checks, no failures.** This is reused retrospective stress evidence, not an independent test. The assessment was chosen after the original baseline's known 2020–2021 underprediction. A passed audit establishes faithful execution of the frozen experiment; it does not establish successful calibration transfer.

## Frozen scope and preservation

The auditor pins `data/reference/calibration_stress_v1_protocol.json` to SHA-256 `a7c1732e8aa9348c264d8e5d118b7e93190a73604d600b405ec5ca5655eef54d`. The protocol's 60 input fingerprints cover the original data, baseline, temporal models and predictions, protocols, documentation, notebooks, tables and charts. All remain unchanged. The prepared-data, original severity and developmental calibration validation receipts remain passed. Producer code and all published producer artifacts are fingerprinted in its manifest and checked independently.

The selected correction is the archived 2019 developmental fold's sigmoid: slope **0.9697790551002594**, intercept **−0.1386345837431384**. The unchanged logistic model was fitted on 1999–2016; that sigmoid was fitted on 2017–2018, not 2017–2019. The development-selected method is read from the unchanged selection artifact. No fitting, optimization, estimator reconstruction, hyperparameter search, threshold selection or candidate selection occurs in this stress experiment. The archived model copy matches the original byte for byte.

## Population and immutable labels

The source Parquet independently yields:

| Release year | Candidate collisions | Fatal | Injury |
|---|---:|---:|---:|
| 2020 | 79,990 | 1,602 | 78,388 |
| 2021 | 83,590 | 1,628 | 81,962 |
| Pooled | 163,580 | 3,230 | 160,350 |

Every `(source_id, C_YEAR, C_CASE)` is unique and present exactly once in predictions; all records remain severity eligible with unchanged binary labels. All eight approved features have dictionary-supported, nonblank, nonconflicting values. No feature-completeness exclusions occur. Prediction feature values equal their immutable source values. This remains a candidate-collision identity scoped to each release, not a newly verified cross-release accident identifier.

## Independent numerical reconciliation

The auditor implements a separate grouped-category coefficient lookup and stable numpy sigmoid, rather than calling the producer scoring function. It reconstructs raw logits, unchanged probabilities, saved sigmoid probabilities and the fixed historical training-prevalence comparator. Unchanged and prevalence probabilities also reproduce the original severity model's saved 2020–2021 scores within numerical tolerance. Probability reconstruction uses absolute tolerance `1e-13` and relative tolerance `1e-11`; raw logits use `1e-12` and `1e-10`. Numerical comparisons of published statistics use absolute and relative tolerance `1e-10`.

All **387** annual/pooled group-method metric rows reconcile against independent numpy calculations: sample size, fatal/injury counts, observed fatal proportion, mean prediction, signed aggregate gap, observed/expected ratio, natural-log loss, Brier score and tie-aware ROC-AUC/average precision. Both fixed bin schemes reconcile across all **189** reliability rows, retaining empty bins and their null averages. ECE is recomputed from bin counts and means with explicit population denominators. Macro means and sample SD use equal weights for the two annual scores. Annual, pooled and macro signed differences, including relative log-loss differences, reconcile independently.

All **348** dictionary-level support rows reconcile with each year and the pooled population. Historical training/calibration/development support matches the archived 2019 support artifact. Supported training-unobserved columns retain zero coefficients; there are no stress records containing a training-unobserved level. Unknown, other and unavailable flags are checked separately and may overlap. Zero-support quality groups remain present; undefined ranking metrics and empty-group scores remain null. The sparse rule remains `n < 100 OR fatal < 5`; sparse records are flagged and retained, not removed or ranked as reliable groups.

The positive sigmoid preserves annual and pooled ranking metrics. This numerical property does not imply improved probability calibration.

## Transfer assessment and interpretation

The frozen gate requires, separately in **both years**, sigmoid-minus-unchanged log loss below `−1e-10` and Brier difference at most `1e-10`. Aggregate absolute calibration-gap differences are diagnostics and do not enter the gate. Pooled or macro scores cannot override an annual failure. The independent implementation verifies the JSON assessment, CSV annual gates and manifest evidence labels against that rule.

| Year | Unchanged log loss | Sigmoid log loss | Unchanged Brier | Sigmoid Brier | Annual gate |
|---|---:|---:|---:|---:|---|
| 2020 | 0.093622 | 0.093709 | 0.019439 | 0.019444 | Failed |
| 2021 | 0.091673 | 0.091746 | 0.018926 | 0.018930 | Failed |

**Transfer is not demonstrated.** Both probability scores worsen in both years; the sigmoid also increases aggregate underprediction. No replacement of the baseline is authorized or implied. These comparisons do not identify a causal mechanism or establish prospective generalization, individual mortality, accident-occurrence prediction, operational benefit or deployment readiness. Two annual observations do not supply independent uncertainty coverage.

## Mutation tests and reproducibility

Six focused auditor tests reject missing/duplicated or altered year-method pairs, a single-year failure hidden by other scores, Brier guardrail violations, sub-tolerance gains, changed coefficients/calibrator/selection labels, invalid probability domains, incorrect empty-group scores and unexpected source years. They also verify overlapping unknown/other flags, retained zero unavailable groups and tie-aware ranking. The previous validated helpers are reused without modification and their source hash is bound in the new receipt.

From the project directory:

```sh
.venv/bin/python -m road_to_safety.validate_calibration_stress_v1
.venv/bin/python -m unittest discover -s tests -p test_validate_calibration_stress_v1.py -v
```

Evidence: `reports/tables/cstress_v1_validation_checks.csv` and `data/derived/calibration_stress_v1/validation.json`. The JSON receipt binds the protocol, source dataset, producer manifest, archived model, predictions, assessment, supporting CSVs, auditor code, numeric-helper code and mutation tests. The audit performed no refitting or new method search. Chart and notebook presentation checks are separate from this numerical audit.
