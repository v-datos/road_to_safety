# Temporal robustness and calibration v1: independent validation

This document describes the independent acceptance audit for the separately versioned `temporal_calibration_v1` experiment. The executable audit is `src/road_to_safety/validate_temporal_calibration_v1.py`. Its machine-readable receipt is `data/derived/temporal_calibration_v1/validation.json`; individual checks are saved to `reports/tables/tcal_v1_validation_checks.csv`.

## Frozen design and protected evidence

The protocol was frozen before fitting with SHA-256 `756f5d52e79da6f6b63a5bfa576e1b814b6749165d3881a1aa34c76fc424ec73`. The auditor independently checks this literal hash, every frozen source and prior-baseline fingerprint, upstream passed receipts, and the experiment manifest's input/output fingerprints. The original severity model, predictions, metrics, figures and protocol must remain byte-for-byte unchanged.

There are exactly six evaluation folds, 2014–2019. In each fold `t`, base-model fitting uses 1999 through `t−3`, calibration uses exactly `t−2` and `t−1`, and evaluation uses `t`. No 2020–2021 records may be fitted, calibrated or scored in this experiment. Source records for eligible 1999–2019 candidate collisions are read directly from the immutable prepared Parquet. Keys are the release-scoped `(source_id, C_YEAR, C_CASE)`; this is conditional fatal-versus-injury collision severity, without exposure denominators.

## Independent calculations

The audit does not instantiate or refit a classifier, calibrator or encoder. It does not call producer metric, selection, sigmoid or reliability helpers.

For every fold it joins all calibration/evaluation predictions to prepared source keys, checks exact coverage and unchanged binary outcomes, verifies chronological assignments, and independently reconciles source/year membership counts. Dictionary domains, references, the eight-feature allowlist and additive design terms are checked against the frozen protocol. Exported coefficients reconstruct every raw logit directly; a numerically stable NumPy sigmoid reconstructs every probability.

Training-only evidence consists of independently recomputed L2-penalized score-equation residuals: intercept `mean(p−y)` and each encoded term's `(sum(x*(p−y)) + coefficient/C)/n`. The maximum absolute derivative must be below `1e−5`. This is numerical consistency evidence for the declared training population and objective; a stationary convex likelihood is stronger evidence than a saved convergence flag alone, though it is not a historical record of every instruction executed. Training prevalence is recomputed from source labels, and dictionary-supported training-absent terms must have neutral zero coefficients.

For calibration, the auditor independently reconstructs `eta = z + delta` and `eta = a*z + b`, the unpenalized mean `logaddexp(0,eta)−y*eta` objective, and analytic gradients using **only the declared two calibration years**. Optimizer success, finite parameters/objective, iteration limits and saved raw gradients are checked. The maximum absolute projected gradient must not exceed `1e−6`. At a sigmoid slope within `1e−10` of its `1e−6` lower bound, the projected slope derivative is `min(raw_derivative,0)`; elsewhere the raw derivative applies. A strictly positive slope is required. No threshold search or thresholded prediction fields are accepted.

Categorical support counts and fatal counts are recomputed separately for all training, calibration and evaluation dictionary levels, including zero-support levels. Per-record training-absent flags, hierarchical feature status, overlapping any-other flags, combined unknown/unavailable flags and separate unknown/unavailable flags are verified directly from source codes. Unknown, unavailable and other retain their distinct meanings.

Every saved annual, calibration and quality-subgroup score is independently recalculated: natural-log loss with float64-epsilon clipping, Brier score, observed prevalence, mean prediction, prediction-minus-observed, observed/expected ratio, tie-aware ROC-AUC and recall-step average precision. Empty groups retain zero counts and undefined scores; one-class ranking metrics remain undefined. Sparse flags use the frozen rule `n < 100 OR fatal < 5`, without dropping these groups.

Both predeclared reliability schemes retain all bins, including empty bins. The auditor independently checks interval edges, counts, fatal counts, mean probabilities, observed fractions and sparse flags. ECE is checked from the independently reconciled fixed-bin evidence. Macro scores use six equally weighted annual means and sample standard deviations (`ddof=1`); pooled scores are recalculated from all evaluation collisions and remain explicitly collision-weighted. Evaluation keys must appear exactly once across folds.

The recommendation is independently reconstructed from paired annual scores: calibrated methods require a macro log-loss improvement greater than `1e−10`, improvement in at least four years, and macro Brier no worse than unchanged plus `1e−10`. Among eligible candidates the lowest macro log loss wins, with `1e−10` ties resolved by complexity. Raw score ranks are reported separately. This selection uses developmental historical evaluation scores; it does not create a new independent test.

## Focused mutation checks

`tests/test_validate_temporal_calibration_v1.py` challenges temporal boundary/exclusion handling, duplicate or missing year/method pairing, the Brier selection guardrail, coefficient corruption, outcome leakage into encoded terms, a calibration-intercept sign flip, invalid probabilities, tied ranking scores and extreme but finite logits. These tests supplement the exhaustive artifact-to-source audit; they do not replace it.

## Interpretation limits

All historical evaluation years were previously inspected. Windows overlap across folds, so annual scores are dependent, and their sample standard deviation is descriptive rather than a confidence interval. Calibration checks address probability agreement within the recorded collision population; they establish neither prospective feature availability nor operational usefulness, accident-occurrence probabilities, causal effects or contemporary external validity. No 2020–2021 re-evaluation is authorized by this protocol.

## Execution result

**Passed: 44 independent checks, zero failures.** The audit reconciled all 2,101,969 saved fold-specific calibration/evaluation prediction rows. These comprise 1,417,430 calibration memberships (collisions may recur in different folds) and 684,539 distinct evaluation collisions from 2014–2019. No evaluation key was repeated across folds, and no 2020–2021 prediction was present.

All 1,344 metric rows, 1,008 reliability-bin rows across both fixed schemes, 96 ECE rows, 696 dictionary-level support rows, 111 source/year membership rows, 18 calibrator-summary rows, four macro summaries, four pooled summaries and three selection-candidate rows were reconciled. The seven focused mutation/edge tests passed.

The frozen rule selects **sigmoid**: macro annual log loss is 0.0737030282 versus 0.0737351015 for unchanged probabilities, a difference of −0.0000320733. Macro Brier is 0.0145449533 versus 0.0145473946. Both calibrated methods improve log loss in four of six years and worsen it in 2018 and 2019. Intercept-only macro log loss is 0.0737046063. These small developmental differences satisfy the predeclared recommendation rule, without establishing a meaningful practical advantage, independent validation or an operational decision.

The receipt binds the final validator source hash and all experiment evidence-table, model, prediction, manifest, protocol and source fingerprints. Reproduce the complete audit from the project directory with:

```sh
.venv/bin/python -m road_to_safety.validate_temporal_calibration_v1
.venv/bin/python -m unittest discover -s tests -p test_validate_temporal_calibration_v1.py -v
```

The audit writes its own receipt and check table; it does not modify any upstream data, fitted model, prediction, original-baseline artifact or selection.
