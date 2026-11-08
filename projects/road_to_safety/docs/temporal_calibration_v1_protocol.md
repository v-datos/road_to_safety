# Temporal robustness and calibration experiment v1

Frozen before this experiment was fitted: 2026-10-18T21:27:24.265691+00:00.

This protocol is the human-readable companion to `data/reference/temporal_calibration_v1_protocol.json`. The JSON is the executable specification. Old baseline artifacts are immutable; their current hashes and the current analytical data are frozen in that file.

## Question and population

Can recent-year calibration improve retrospective annual fatal-versus-injury collision probability scores relative to an unchanged expanding-history logistic model?

All severity-eligible candidate collisions in selected official NCDB 1999–2021 annual releases; no feature-completeness exclusion; conditional on recorded fatal/injury collision.

All eight approved categorical predictors, dictionary levels, reference categories and original L2 logistic settings are retained. Unknown, other and unavailable codes remain distinct; no complete-case exclusion is permitted. The target remains fatal versus nonfatal-injury collision, conditional on a recorded fatal/injury event.

## Six chronological folds

| Evaluation year | Base-model training years | Calibration years | Evaluation year |
|---|---|---|---|
| 2014 | 1999–2011 | 2012–2013 | 2014 |
| 2015 | 1999–2012 | 2013–2014 | 2015 |
| 2016 | 1999–2013 | 2014–2015 | 2016 |
| 2017 | 1999–2014 | 2015–2016 | 2017 |
| 2018 | 1999–2015 | 2016–2017 | 2018 |
| 2019 | 1999–2016 | 2017–2018 | 2019 |

The model fits only the training years. The two calibration years are held out from base-model fitting. Evaluation labels never enter either fit. Earlier evaluation years can enter later folds as historical training or calibration data; folds are dependent. No records from 2020–2021 are fitted or scored. Those years were already evaluated in the preceding baseline, and are not fresh holdouts.

## Fixed model and calibration algorithms

The base model uses dictionary-fixed sparse float64 one-hot encoding with the original declared reference categories: month 1, weekday 1, hour 12, road configuration 1, weather 1, surface 1, alignment 1 and traffic control 18. It uses L2 regularization, C=1, lbfgs, max_iter=1000, tol=1e-7, random_state=2026, intercept enabled, no class weights, resampling or tuning. Fixed dictionary columns unseen in training remain neutral and are reported as unsupported by training evidence.

Use the model decision function directly as logit z. Compare unchanged expit(z), intercept-only expit(z+delta) and sigmoid expit(a*z+b). The sigmoid slope has lower bound 1e-6, preserving increasing within-fold ranking. A separate constant comparator uses training prevalence; it is not a calibration-selection candidate.

Fit both calibrators on exactly their two calibration years by unpenalized mean binary log likelihood, computed stably as mean(logaddexp(0,eta)-y*eta), with analytic gradients. Initialize delta=0 or (a,b)=(1,0). Both use scipy.optimize.minimize L-BFGS-B, maxiter=1000, maxls=50, ftol=1e-14, gtol=1e-9. Delta and b are unbounded. Require optimizer success, finite output, iterations below the cap and maximum absolute projected mean gradient <=1e-6. At a lower-bound slope (within 1e-10), the projected slope gradient is min(raw_gradient,0); other gradients are unchanged. A failed fit stops the run rather than silently changing settings.

## Scores and frozen selection rule

The primary score is the equal-weight arithmetic mean of six annual evaluation log losses. Natural logs and float64-epsilon probability clipping are fixed. Secondary scores include Brier, average precision (recall-step weighted), ROC-AUC, mean predicted probability, observed fatal proportion, predicted-minus-observed gap, and observed/expected fatal counts. Report both annual scores and clearly labeled pooled evaluation scores. Report sample SD across years (ddof=1) as temporal dispersion, not a confidence interval. Calibration-partition scores are in-sample fitting diagnostics and never selection evidence.

A calibrated candidate qualifies for recommendation only when all three hold: macro log loss improves on unchanged by more than 1e-10; at least four of six annual log losses improve by more than 1e-10; and macro Brier is no worse than unchanged plus 1e-10. Among qualifying candidates choose the lowest macro log loss. Values within 1e-10 of that minimum tie; resolve by complexity order unchanged, intercept-only, sigmoid. If none qualifies retain unchanged. Show the raw score ranking separately. This is developmental method selection, not a production decision.

## Calibration, sparse support and availability

Report reliability bins for both fixed deciles (0,.1,...,1) and fixed low-probability edges (0,.005,.01,.015,.02,.03,.05,.1,.2,.3,.5,1). Intervals are [lower,upper), with the final bin including 1. Include n, fatal count, mean prediction and observed proportion. Empty bins remain present with null means. Bin-dependent expected calibration error is descriptive and does not determine selection.

A group is sparse if n<100 OR fatal count<5; flag and retain it. Report train/calibration/evaluation support counts and training-unobserved level incidence. For each evaluation year report each feature’s stated, unknown U/UU, other Q/QQ and unavailable X/XX groups separately, including zero-support groups. Also report collision-level presence/absence of any-unknown and any-other flags; these flags can overlap. Other is not missing. Empty and one-class groups have undefined ranking scores, not zero. No stable-ranking claims for sparse groups.

## Validation and limits

Verify exact folds, eligible keys, immutable targets, domains, reference categories and all fingerprints; independently reconstruct base-model scores, training prevalence, calibration objectives and stationarity, annual/bin/group metrics and the selection rule. Preserve the original model, predictions, tables and charts byte-for-byte.

No thresholds, interactions, new features, trees, hyperparameter searches or 2020–2021 stress scoring are in scope. Prior analysis has already inspected all evaluation years, so this experiment is separately frozen developmental evidence. Shared training history makes fold scores dependent. We promise no confidence intervals here. No accident-occurrence, causal, individual mortality, deployment or prospective-performance claim is supported.

Any post-fit methodological amendment requires a separately versioned protocol, with disclosure of inspected results; never overwrite this frozen specification.
