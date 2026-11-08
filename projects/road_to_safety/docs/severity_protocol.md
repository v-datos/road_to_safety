# Frozen chronological severity-model protocol

This protocol was frozen before fitting the first prevalence baseline or logistic severity model. Its machine-readable authority is [`data/reference/severity_protocol.json`](../data/reference/severity_protocol.json), SHA-256 **`7684a32e919a0b73f57ed55e7c1c796c4cb5a73c1a62cdeb76a1ff8889259491`**. The JSON records the UTC freeze timestamp and fingerprints for the prepared collision dataset, original feature contract, preparation validation and exploratory validation. This document explains the fixed choices; it contains no fitted results. Any subsequent design change requires a new version and disclosure of whether test results were already observed.

## Population, question and outcome

The analysis concerns all severity-eligible candidate collisions in the selected official NCDB fatal/injury releases for 1999–2021. One row is the release-scoped candidate key `(source_id, C_YEAR, C_CASE)`. The target `is_fatal=1` means a collision producing at least one fatality; `is_fatal=0` means a collision producing nonfatal injury. The estimand is fatal severity conditional on a recorded fatal/injury collision. It is neither individual mortality nor collision-occurrence probability.

No record is excluded merely for a documented unknown, unavailable or other feature value. The existing preparation policy, provenance and target eligibility remain unchanged. Feature availability before an outcome is known remains an assumption: these are post-crash records, and prospective recording times have not been verified. No deployment, causal policy-effect or infrastructure-effect claim follows from this baseline exercise.

## Chronological partitions

| Partition | Inclusive years | Permitted use |
|---|---|---|
| Training | 1999–2016 | Fit prevalence and the fixed logistic coefficients |
| Validation | 2017–2019 | Evaluate and select one illustrative threshold using the fixed rule below |
| Test | 2020–2021 | Evaluate the frozen models and thresholds, pooled and separately for each year |

Every eligible collision belongs to exactly one partition. There is no shuffle or train/validation/test overlap, and no refitting on combined training and validation. `C_YEAR` is a grouping variable, never a feature. The 2020 and 2021 distributions and outcomes were already inspected descriptively in the exploratory phase, so this is a **retrospective temporal holdout**, not a pristine prospective test. The protocol prevents fitting or threshold selection to those labels but cannot undo prior descriptive exposure. A future untouched period would be needed for stronger prospective evidence.

Late-year collision volume, fatal fraction and feature composition differ from earlier years. This motivates separate 2020 and 2021 assessment; it does not justify attributing changes to a particular cause. Travel exposure, reporting, source vintage, selection and case mix cannot be disentangled with these records.

## Predictors and categorical handling

Only these eight existing allowlisted categorical variables enter the logistic model:

| Field | Meaning | Dropped reference code |
|---|---|---|
| `C_MNTH` | Month | `1` |
| `C_WDAY` | Weekday | `1` |
| `C_HOUR` | Reported hour | `12` |
| `C_RCFG` | Road configuration | `1` |
| `C_WTHR` | Weather | `1` |
| `C_RSUR` | Road surface | `1` |
| `C_RALN` | Road alignment | `1` |
| `C_TRAF` | Traffic control | `18` |

Domains and their ordering are copied from the archived-dictionary-based modeling contract into the frozen JSON. The encoder uses sparse float64 one-hot columns and drops exactly the declared reference per field. Numeric-looking codes have no ordinal spacing or linear interpretation. Category vocabulary is fixed external dictionary metadata, not learned from validation or test observations.

Unknown `U/UU`, other `Q/QQ` and jurisdiction-unavailable `X/XX` retain separate dictionary-supported categories. “Other” is observed information, not missingness. There is no imputation, category pooling, complete-case deletion or resampling. A supported level absent in training retains a column, receives a neutral zero coefficient, and is explicitly flagged along with its later incidence. Such a coefficient indicates absent training evidence rather than proof of no association. A blank, null, conflict or out-of-domain value rejects this modeling run before fitting/scoring; it remains preserved in the immutable preparation inputs for investigation. No undocumented catch-all code is invented.

`C_SEV`, injury/casualty information, identifiers, source/release metadata, `C_YEAR`, diagnostics, conflict flags, collision configuration `C_CONF`, vehicle count `C_VEHS`, and every other field outside the exact allowlist are excluded. The candidate key and year accompany predictions only for reconciliation and grouping.

## Two fixed estimators

The prevalence baseline predicts the training fatal count divided by the training collision count for every row in every partition. Validation and test prevalences never fit or update it.

The interpretable model is a single binary logistic regression with intercept, L2 penalty, `C=1.0`, `solver=lbfgs`, `max_iter=1000`, `tol=1e-7` and reproducibility seed `2026`. It uses no class weights, sample weights, oversampling, undersampling, hyperparameter search, interactions or fitted probability calibration. All coefficients are fitted to training data only. Fixed external dictionary encoding and the validation-selected threshold are the only declared handling beyond that fit.

Export each level’s coefficient, `exp(coefficient)`, reference and training count, including flags for absent training support. Exponentiated coefficients are regularized conditional odds associations relative to the stated reference, conditional on the other included categories. They are not causal effects, unregularized effect estimates, risk ratios or evidence of prospective availability. No confidence intervals, standard errors or significance tests are promised for penalized coefficients in this phase.

## Metrics and thresholds

Evaluate both estimators on training, validation and test, with annual denominators and separate late-year results. Include collision count, fatal count and observed prevalence in each relevant partition/year/group.

| Type | Frozen measures and interpretation |
|---|---|
| Probability error | Natural-log binary log loss, with float64 epsilon clipping, and mean Brier error `(y−p)²`; lower is better |
| Ranking | Average precision using recall-step weighting, and ROC-AUC; higher is better. Average precision is not trapezoidal PR area. One-class ranking metrics are explicitly undefined/null |
| Classification | Precision, recall, F1 and the full TN/FP/FN/TP confusion counts at each declared threshold |
| Calibration | Ten fixed equal-width bins from 0 to 1, bin counts, fatal counts, mean predictions, observed fatal proportions and expected calibration error |

Accuracy is not a primary comparison or acceptance gate because the fatal class is rare. A fatal prediction means `p >= threshold`. Precision is `TP/(TP+FP)`, recall is `TP/(TP+FN)` and F1 is `2TP/(2TP+FP+FN)`; zero denominators use zero, with underlying counts available so undefined-use cases remain visible.

Two thresholds are evaluated:

1. The fixed threshold **0.5**.
2. One threshold selected from distinct validation logistic probabilities. Among candidates attaining validation fatal recall **at least 80%**, maximize validation precision; ties choose the higher threshold. Failure to find a valid threshold fails the selection check. Freeze the selected number before test scoring.

Apply both thresholds to both models on every evaluated partition/year/group; the prevalence baseline uses the same numerical thresholds rather than a separately optimized baseline threshold. The 80% recall rule is an illustrative operating point, not a deployment recommendation or an optimum under known decision costs. There is no test-driven threshold revision or calibration fit.

Calibration bins are `[lower, upper)` except the last includes 1.0. Retain empty bins with count zero and null means. Expected calibration error is `Σ (bin count / partition count) × |observed fatal proportion − mean prediction|` over nonempty bins. ECE is descriptive and depends on bin choices. Save validation/test precision–recall comparisons, fixed-bin reliability comparisons and annual prevalence/probability-error diagnostics. Low aggregate error can coexist with poor rare-class recall, and broad calibration bins can conceal local miscalibration; present all these views together.

## Changed-population and sparse-group checks

For 2020 and 2021 separately, and the pooled test period, report the frozen probability, ranking, classification and calibration results. Compare all eight feature distributions and unknown/unavailable/other shares with training and validation; report supported but training-unobserved levels and their incidence. Review each allowed feature’s categories individually, without an exhaustive interaction search.

For each reported category group show collision/fatal denominators, probability errors and threshold recall/precision where defined. Flag a group as sparse if **collision count <100 OR fatal count <5**. Retain sparse groups, distinguish zero observed support from a sparse observed group, and avoid stable-ranking or operational conclusions from their estimates. These are transparent descriptive flags, not statistical significance thresholds. Preserve all supported non-stated categories in subgroup evidence.

## Completion and assessment gates

Implementation is complete only when upstream receipts and fingerprints are current, keys are unique, partitions conserve the eligible cohort, the target is binary, and the exact feature/domain/reference rules are enforced. All fitted quantities must have the stated training/validation provenance. Require finite probabilities in `[0,1]`, no logistic convergence warning, and iteration count below the cap. Independently reconcile counts, classification results, calibration bins and probability metrics. Confirm immutable prepared-input fingerprints after the run.

Assess predictive improvement using logistic minus baseline **test log-loss and Brier differences**, both pooled and separately for 2020 and 2021. Negative differences mean improvement. This is a result to report, not a condition to force: no improvement must remain visible and cannot trigger a test-driven tuning loop. Ranking improvements alone do not establish usable probability quality or operational utility. Report any nonconvergence, unsupported domain, reconciliation failure or failed improvement candidly. Stronger future work would require a separately documented design and, preferably, new untouched temporal data.
