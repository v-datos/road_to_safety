# Temporal robustness and calibration experiment v1

Completed October 18, 2026. A separately versioned, frozen development experiment compares unchanged probabilities, intercept-only recalibration and sigmoid recalibration across six chronological evaluation years. The prior baseline run and its artifacts remain preserved. No 2020–2021 record is fitted, calibrated or scored.

## Result and predeclared recommendation

The frozen rule selects **sigmoid** for developmental follow-up. The rule assesses equally weighted annual log loss, requires a calibrated method to improve at least four of six years, and prevents mean Brier worsening. This is a method recommendation within historical development evidence, not a production or independent-test claim.

| Candidate | Macro log loss | Difference vs unchanged | Macro Brier | Brier difference | Years improved | Eligible | Raw log-loss rank |
|---|---:|---:|---:|---:|---:|---|---:|
| unchanged | 0.07373510 | +0.00000000 | 0.01454739 | +0.00000000 | 0/6 | True | 3 |
| intercept_only | 0.07370461 | -0.00003050 | 0.01454510 | -0.00000229 | 4/6 | True | 2 |
| sigmoid | 0.07370303 | -0.00003207 | 0.01454495 | -0.00000244 | 4/6 | True | 1 |

The selected method lowers macro log loss by **0.00003207** (**0.0435% relative**) and macro Brier by **0.00000244**. These are very small gains. Both recalibration methods improve 2014–2017 but worsen **2018 and 2019**; the newest development years therefore provide a material counterpoint to the average result. There is no confidence interval or significance claim for this tiny difference.

Smaller log loss and Brier are better. A negative difference favors the calibrated method. “Eligible” for unchanged denotes the retained fallback, not a claim that it improves itself. Raw score ranking is shown separately from the recommendation gates. No method is silently discarded because its result is unfavorable.

## Frozen design and chronological support

The protocol was frozen before any experiment fitting: [machine specification](../data/reference/temporal_calibration_v1_protocol.json), [methods](temporal_calibration_v1_protocol.md), SHA256 `756f5d52e79da6f6b63a5bfa576e1b814b6749165d3881a1aa34c76fc424ec73`. For evaluation year`t`, base training is 1999 through`t−3`, calibration is`t−2` and`t−1`, and evaluation is`t`. These are explicit source-year boundaries, not random row splits.

| Evaluation year | Training years | Training n / fatal | Calibration years | Calibration n / fatal | Evaluation n / fatal |
|---|---|---:|---|---:|---:|
| 2014 | 1999–2011 | 1,854,913 / 30,765 | 2012–2013 | 246,814 / 3,620 | 116,292 / 1,675 |
| 2015 | 1999–2012 | 1,979,595 / 32,613 | 2013–2014 | 238,424 / 3,447 | 119,550 / 1,693 |
| 2016 | 1999–2013 | 2,101,727 / 34,385 | 2014–2015 | 235,842 / 3,368 | 118,321 / 1,738 |
| 2017 | 1999–2014 | 2,218,019 / 36,060 | 2015–2016 | 237,871 / 3,431 | 114,412 / 1,698 |
| 2018 | 1999–2015 | 2,337,569 / 37,753 | 2016–2017 | 232,733 / 3,436 | 111,334 / 1,754 |
| 2019 | 1999–2016 | 2,455,890 / 39,491 | 2017–2018 | 225,746 / 3,452 | 104,630 / 1,620 |

**684,539 distinct evaluation collisions** appear once across 2014–2019. Saved predictions include **1,417,430 calibration-role rows**, for **2,101,969 fold-specific calibration/evaluation rows** in total. A historical collision may be used in different roles in later folds; the correct prediction key includes evaluation-fold year and source collision identity. Within each fold, train/calibration/evaluation keys are disjoint. No expansion or duplication is used to weight an evaluation collision.

Every evaluation year was previously inspected during EDA and prior baseline reporting. These are development comparisons, not newly pristine holdouts. Training and calibration windows overlap between folds, so six annual scores are dependent. Macro sample standard deviation is descriptive, never a confidence interval. The source cohort remains recorded fatal/injury collisions; it excludes traffic exposure, non-crash observations and property-damage-only crashes.

## Estimator and calibration formulas

Each fold fits one new base model with the original eight categorical features, dictionary domains and dropped references: month, weekday, hour, road configuration, weather, surface, alignment and traffic control. C_YEAR controls chronology and is not a predictor. IDs, source proxies, targets, realized collision configuration, vehicle counts, casualty information and preparation diagnostics remain excluded. Unknown, other and jurisdiction-unavailable codes are separate; no imputation, completeness deletion, balancing or additional predictor selection is applied.

The base model is the same L2 logistic specification: C=1, lbfgs, maximum 1,000 iterations, tolerance 1e-7, seed 2026, intercept and no class/sample weights. The dictionary-fixed one-hot encoder and coefficients are fitted on training rows only. A constant training-prevalence comparator is retained per fold and is never a calibration-selection candidate.

For the base decision-function logit`z`, the candidates are:

- Unchanged: `expit(z)`; no calibration fit.
- Intercept-only: `expit(z + delta)`.
- Sigmoid: `expit(a*z + b)`, with `a >= 1e-6`.

The two adjustments minimize mean unpenalized binomial negative log likelihood on exactly the two calibration years. The stable objective is `mean(logaddexp(0,eta) − y*eta)` with analytic gradients. L-BFGS-B settings are maximum 1,000 iterations, maximum 50 line-search steps, ftol 1e-14 and gtol 1e-9. Parameters/objective must be finite, optimizer success true, iterations below the cap and maximum absolute projected gradient≤1e-6. Lower-bound slope solutions are checked using the minimization KKT sign. No evaluation label enters base fitting or calibration fitting.

All methods are increasing transformations within a fold. They address probability estimation rather than adding discriminatory features. Within-fold AP/AUC should therefore remain unchanged apart from numerical ties. Pooled AP/AUC across folds can change because different folds use different calibration functions; pooled ranking changes are not evidence that a within-fold calibrator discovered new predictive information.

## Annual evaluation results

| Year | Method | n | Fatal % | Mean predicted % | Log loss | Brier | AP % | ROC-AUC | O/E |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2014 | unchanged | 116,292 | 1.4403 | 1.5876 | 0.07164702 | 0.01407737 | 3.3364 | 0.70435 | 0.90722 |
| 2014 | intercept_only | 116,292 | 1.4403 | 1.4561 | 0.07157555 | 0.01407359 | 3.3364 | 0.70435 | 0.98918 |
| 2014 | sigmoid | 116,292 | 1.4403 | 1.4561 | 0.07157554 | 0.01407356 | 3.3364 | 0.70435 | 0.98917 |
| 2014 | prevalence | 116,292 | 1.4403 | 1.6586 | 0.07552650 | 0.01420070 | 1.4403 | 0.50000 | 0.86842 |
| 2015 | unchanged | 119,550 | 1.4161 | 1.5799 | 0.07071968 | 0.01384626 | 3.3455 | 0.70160 | 0.89637 |
| 2015 | intercept_only | 119,550 | 1.4161 | 1.4516 | 0.07063401 | 0.01384183 | 3.3455 | 0.70160 | 0.97559 |
| 2015 | sigmoid | 119,550 | 1.4161 | 1.4516 | 0.07063407 | 0.01384185 | 3.3455 | 0.70160 | 0.97559 |
| 2015 | prevalence | 119,550 | 1.4161 | 1.6475 | 0.07452252 | 0.01396624 | 1.4161 | 0.50000 | 0.85959 |
| 2016 | unchanged | 118,321 | 1.4689 | 1.5812 | 0.07316392 | 0.01436487 | 3.2920 | 0.69344 | 0.92897 |
| 2016 | intercept_only | 118,321 | 1.4689 | 1.4391 | 0.07312514 | 0.01436129 | 3.2920 | 0.69344 | 1.02068 |
| 2016 | sigmoid | 118,321 | 1.4689 | 1.4391 | 0.07312473 | 0.01436126 | 3.2920 | 0.69344 | 1.02068 |
| 2016 | prevalence | 118,321 | 1.4689 | 1.6360 | 0.07666707 | 0.01447589 | 1.4689 | 0.50000 | 0.89783 |
| 2017 | unchanged | 114,412 | 1.4841 | 1.5801 | 0.07371142 | 0.01450884 | 3.2723 | 0.69348 | 0.93923 |
| 2017 | intercept_only | 114,412 | 1.4841 | 1.4525 | 0.07368437 | 0.01450619 | 3.2723 | 0.69348 | 1.02173 |
| 2017 | sigmoid | 114,412 | 1.4841 | 1.4525 | 0.07367885 | 0.01450573 | 3.2723 | 0.69348 | 1.02177 |
| 2017 | prevalence | 114,412 | 1.4841 | 1.6258 | 0.07728134 | 0.01462285 | 1.4841 | 0.50000 | 0.91286 |
| 2018 | unchanged | 111,334 | 1.5754 | 1.5622 | 0.07709376 | 0.01536912 | 3.6016 | 0.69615 | 1.00849 |
| 2018 | intercept_only | 111,334 | 1.5754 | 1.4714 | 0.07713002 | 0.01536996 | 3.6016 | 0.69615 | 1.07071 |
| 2018 | sigmoid | 111,334 | 1.5754 | 1.4714 | 0.07712803 | 0.01537025 | 3.6016 | 0.69615 | 1.07070 |
| 2018 | prevalence | 111,334 | 1.5754 | 1.6151 | 0.08102538 | 0.01550635 | 1.5754 | 0.50000 | 0.97547 |
| 2019 | unchanged | 104,630 | 1.5483 | 1.5460 | 0.07607481 | 0.01511792 | 3.4066 | 0.69777 | 1.00149 |
| 2019 | intercept_only | 104,630 | 1.5483 | 1.5149 | 0.07607855 | 0.01511776 | 3.4066 | 0.69777 | 1.02207 |
| 2019 | sigmoid | 104,630 | 1.5483 | 1.5154 | 0.07607696 | 0.01511705 | 3.4066 | 0.69777 | 1.02171 |
| 2019 | prevalence | 104,630 | 1.5483 | 1.6080 | 0.07990780 | 0.01524376 | 1.5483 | 0.50000 | 0.96287 |

Observed/expected(O/E) is observed fatal count divided by summed predicted probabilities. Above 1 indicates aggregate underprediction; below 1 indicates overprediction. Mean agreement alone does not establish calibration across the probability range. Log loss and Brier reflect both reliability and discrimination; improvement is not proof of every subgroup’s calibration.

## Macro, pooled and reliability summaries

| Method | Macro log loss | Annual SD | Macro Brier | Annual SD | Macro AP % | Macro ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| intercept_only | 0.07370461 | 0.00251661 | 0.01454510 | 0.00059339 | 3.3757 | 0.69780 |
| prevalence | 0.07748844 | 0.00251899 | 0.01466930 | 0.00059734 | 1.4889 | 0.50000 |
| sigmoid | 0.07370303 | 0.00251579 | 0.01454495 | 0.00059334 | 3.3757 | 0.69780 |
| unchanged | 0.07373510 | 0.00247121 | 0.01454739 | 0.00059128 | 3.3757 | 0.69780 |

Selection gives each year equal weight. The separate pooled table weights collisions and must not be substituted for the primary macro criterion. It contains the same evaluation observations, not independent corroboration.

Reliability uses two frozen bin sets: ten equal-width bins over [0,1], and low-probability edges 0,.005,.01,.015,.02,.03,.05,.1,.2,.3,.5,1. Intervals are left-closed/right-open, with1 included in the last bin. Empty bins remain explicit; averages are undefined. Bin counts and fatal numerators are retained, and bins with n<100 or fatal<5 are marked sparse. ECE is weighted absolute within-bin calibration difference, descriptive/bin-dependent and not a selection rule. Rare high-probability bins do not support stable pointwise claims.

## Availability, category support and safeguards

Every feature is summarized by stated, unknown(U/UU), other(Q/QQ) and unavailable(X/XX) in each evaluation year, including absent groups. Separate collision-level unknown/unavailable/other flags retain overlapping conditions, with presence and absence denominators. Hierarchical feature-status groups additionally give unknown/unavailable precedence over other; that partition must not be mistaken for the full set containing any other code. Zero-observation groups have undefined metrics; one-class groups have undefined ranking measures. Sparse groups are retained, not silently excluded.

Per-fold category support includes collision/fatal counts for train, calibration and evaluation. Dictionary levels absent in training have neutral coefficients and explicit support flags; they do not establish absence of an association. Marginal support is not proof that every joint scenario was represented. Feature and availability group tables overlap and cannot be summed as unique collisions.

The original baseline remains byte-for-byte unchanged, including model coefficients, predictions, tables, figures and frozen receipts. This experiment does not modify the old threshold, replace the earlier model or score 2020–2021 anew. Additional reporting and plot completion, where needed, is performed from saved fold predictions without changing model or calibration fits.

## Reproduction and verification

For an existing completed run, validate the saved evidence:

```bash
.venv/bin/python -m road_to_safety.validate_temporal_calibration_v1
.venv/bin/python -m unittest discover -s tests -v
```

To regenerate fitting, use a separate working copy retaining the pinned source/baseline inputs and receipts, with no completed v1 manifest. The producer protects an existing completed version from overwrite:

```bash
uv sync --locked --python 3.13 --extra notebook
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MPLCONFIGDIR=/tmp/road-to-safety-mpl .venv/bin/python -m road_to_safety.fit_temporal_calibration_v1
```

- [Executed notebook](../notebooks/05_temporal_robustness_calibration_v1.ipynb): frozen windows, source-linked validation, bounded summaries, plots, support and calibrator parameters.
- [Experiment card](../models/temporal_calibration_v1_card.md) and [independent validation](temporal_calibration_v1_validation.md).
- `reports/tables/tcal_v1_metrics.csv`, `tcal_v1_macro.csv`, `tcal_v1_pooled.csv`, `tcal_v1_selection.csv`: annual/group, macro, pooled and recommendation evidence.
- `tcal_v1_reliability.csv`, `tcal_v1_ece.csv`, `tcal_v1_membership.csv`, `tcal_v1_level_support.csv`: both bin schemes, availability/source-year denominators and complete level support.
- `reports/figures/tcal_v1_annual_scores.png`, `tcal_v1_reliability.png`: annual proper scores/calibration gap and full-support reliability. `tcal_v1_reliability_zoom.png` is generated by editable notebook plotting code and discloses per-method observations outside its 0–5% axes.
- `data/derived/temporal_calibration_v1/`: six base/calibration model JSONs, six source-keyed Parquet predictions, selection, producer manifest and independent validation receipt. These derived data remain local.

A separate parent check confirms that the 2019 fold’s unchanged probabilities reproduce all 104,630 original-baseline 2019 scores exactly (maximum absolute difference 0), with unchanged labels. All **44 independent checks passed with zero failures**. All **51 regression tests** passed, and the 14 experiment-specific tests also passed after the final reporting changes. The independent auditor reconstructs logits and calibrated probabilities from the source features and archived parameters, recomputes training/calibration likelihood gradients without refitting, validates fold boundaries and every metric/bin/selection record, and rechecks immutable fingerprints. Focused tests cover wrong-year leakage, altered outcomes/coefficients, tied rankings, calibration sign errors, probability/bin boundaries, optimizer behavior and recommendation guardrails.

The notebook executed all **11 code cells** with **three saved PNG outputs** and no errors. It verifies the passed audit receipt and bound artifacts rather than repeating the full source scan. All three standalone figures were visually inspected; the supplementary low-probability zoom preserves the original bin definitions, identifies omitted counts per method and retains the full-support figure alongside it. A whole-notebook page preview remains unverified because of the previously recorded local browser URL-policy restriction. No inferential confidence interval, causal policy effect, individual mortality estimate or deployment-readiness claim is supplied by this phase.

## Next research decision

Review the selected method’s annual weaknesses as well as its average improvement. A developmental recommendation is not evidence that it corrects the already-observed 2020–2021 calibration shift. Any subsequent application to those years requires a separately specified reused retrospective stress test; those years are not new untouched data. Newer audited record-level or prospective observations would strengthen independent validation. Do not expand predictor/model searches or operational threshold decisions without a separate design and decision context.
