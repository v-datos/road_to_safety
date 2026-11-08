# Temporal robustness and calibration experiment v1

This is a developmental retrospective comparison of fatal-versus-injury collision probability estimates. Its unit is a release-scoped candidate collision, not a person, trip or road segment. The population contains recorded fatal/injury collisions in selected official NCDB microdata. There are no non-crash or exposure observations, so probabilities do not describe accident occurrence or individual mortality.

## Fixed design

The immutable specification is `data/reference/temporal_calibration_v1_protocol.json`, SHA256 `756f5d52e79da6f6b63a5bfa576e1b814b6749165d3881a1aa34c76fc424ec73`. It was frozen before any experiment fit. The six evaluation years are 2014–2019. For year t, logistic regression uses 1999 through t−3; calibration uses t−2 and t−1; evaluation uses t alone. The windows are disjoint within each fold, but histories overlap between folds. No 2020–2021 records are fitted, calibrated or scored in this experiment. Earlier inspection of evaluation years is disclosed; these are developmental evaluations, not untouched external validation.

The original eight categorical features, dictionary domains and reference levels are fixed. One-hot columns retain supported unknown, other and unavailable levels separately. There is no imputation, completeness exclusion, class weighting, resampling, feature selection, interaction expansion or hyperparameter search. C_YEAR controls partitions and is not a predictor. The logistic estimator is L2-regularized with C=1, lbfgs, max_iter=1000 and tol=1e-7. Only training collisions estimate its coefficients and constant-prevalence comparator.

## Candidates and estimation

Unchanged probabilities are expit(z), where z is the base logistic decision function. Intercept-only probabilities are expit(z+delta). Sigmoid probabilities are expit(a*z+b), with a constrained to be at least 1e-6. Each calibration fit minimizes mean unpenalized binary log loss using only its two calibration years. The stable logaddexp objective and analytic gradients use float64. L-BFGS-B starts at delta=0 or (a,b)=(1,0), with max_iter=1000, maxls=50, ftol=1e-14 and gtol=1e-9. A successful, finite solution below the iteration cap and maximum absolute projected gradient ≤1e-6 is required. Positive slope preserves ranking within a fold except numerical ties.

## Selection and evidence

The primary score is the unweighted mean of the six annual evaluation log losses. A calibrated method is eligible only if it improves that mean by more than 1e-10, improves at least four annual log losses by more than 1e-10, and has mean Brier score no greater than unchanged plus 1e-10. Choose minimum macro log loss among eligible candidates; ties within 1e-10 favor unchanged, then intercept-only, then sigmoid. Retain unchanged if neither correction qualifies. Training prevalence is an additional comparator, never a selection candidate. No threshold search or operational cutoff is part of this experiment.

Supporting evidence includes annual and pooled log loss, Brier score, average precision, ROC-AUC, mean predicted probability, observed fatal fraction, prediction-minus-observed gap and observed/expected ratio. Macro sample standard deviation describes variability across six dependent years and is not a confidence interval. Pooled evaluation scores weight collisions and are reported separately; fold-specific recalibration can alter pooled ranking even when each fold's ranking is preserved.

Reliability uses two prespecified sets of fixed bins, retaining empty bins and complete counts. ECE is descriptive and bin-dependent, not a selection criterion. Every feature has stated/unknown/other/unavailable evaluation groups, including empty groups; collision-level any-unknown and any-other flags can overlap. Groups with fewer than 100 collisions or five fatalities are flagged rather than dropped. Category support includes zero-support dictionary levels, per-partition collision and fatal counts, and training-unobserved incidence.

## Reproduction and limitations

Run `.venv/bin/python -m road_to_safety.fit_temporal_calibration_v1` from the project root. Existing completed version outputs are protected from overwrite. Per-fold JSON archives the complete base model and calibration parameters; Parquet archives contain calibration/evaluation identities, target, raw logits and each probability. Membership and category support tables permit independent reconstruction. The manifest fingerprints inputs, producer code, lock file and outputs. Original baseline artifacts must remain unchanged.

This experiment estimates historical conditional severity associations. Calibration may adjust observed prevalence shifts without identifying their cause. Reporting practices, source composition and real conditions can all influence outcomes. Prospective availability of recorded conditions is unverified; modern external validation and decision costs are still absent. No causal policy effect or deployment-readiness claim follows from these results.

## Results and validation

The frozen developmental rule recommends sigmoid recalibration: it improves log loss in four of six evaluation years, has the lowest eligible macro log loss and satisfies the macro Brier guardrail. The gain is small: macro log loss changes from 0.07373510 unchanged to 0.07370303 sigmoid, a difference of −0.00003207 (about 0.0435% relative). Intercept-only achieves 0.07370461, only 0.00000158 above sigmoid. Macro Brier scores are 0.01454739 unchanged, 0.01454510 intercept-only and 0.01454495 sigmoid.

Both calibration corrections worsen evaluation log loss in 2018 and 2019. The recommendation is therefore a result of the predeclared historical selection rule, not evidence of a material practical upgrade or reliable contemporary improvement. All three transformations have the same within-year average precision and ROC-AUC; the sigmoid transformation cannot improve theoretical ranking when its slope is positive. Six-year mean ROC-AUC is 0.697798 and mean average precision is 0.0337575.

The unchanged model overpredicts fatal probability by 0.0008396 on average across years; sigmoid shifts this to underprediction by 0.0002452. Opposite signed errors should not be hidden by the six-year average; consult the annual scores, reliability tables and saved calibrator slopes/intercepts. In-sample calibration diagnostics are not selection evidence. Independent validation status is recorded separately in the experiment receipt; a successful implementation audit cannot establish practical usefulness.
