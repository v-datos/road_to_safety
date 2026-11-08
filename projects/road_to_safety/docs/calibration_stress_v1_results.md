# Frozen calibration transfer stress test v1 — results

Completed October 20, 2026. Protocol, scoring and independent audit were delegated to separate roles. This is a scoring-only, reused retrospective comparison on 2020 and 2021; it does not fit or modify a model.

## Principal result

**Transfer was not demonstrated.** The saved sigmoid correction worsens both log loss and Brier score in **2020 and 2021**, and increases aggregate underprediction in each year. The predeclared rule therefore returns `transfer_not_demonstrated`. This is a valid negative analytical result, not a failed implementation.

| Year | Sigmoid minus unchanged log loss | Sigmoid minus unchanged Brier | Year gate passed |
|---|---:|---:|---|
| 2020 | +0.0000874889 | +0.0000049955 | False |
| 2021 | +0.0000722204 | +0.0000035539 | False |

Negative proper-score differences would favor sigmoid; positive values above show worsening. The differences are small, with no significance or uncertainty claim. Neither a pooled average nor an aggregate calibration-gap diagnostic overrides the annual rule.

## Frozen estimator, adjustment and comparison

The new [machine protocol](../data/reference/calibration_stress_v1_protocol.json) was frozen before new scores; its SHA256 is `a7c1732e8aa9348c264d8e5d118b7e93190a73604d600b405ec5ca5655eef54d`. The [human protocol](calibration_stress_v1_protocol.md) gives the exact scope and inherited development context.

The saved final development estimator is `data/derived/temporal_calibration_v1/model_2019.json`:

- Logistic coefficients fitted on 1999–2016, with the original eight categorical condition features and frozen L2 settings.
- Sigmoid parameters fitted on 2017–2018: **slope 0.9697790551002594**, **intercept −0.1386345837431384**.
- Sigmoid selected in the earlier 2014–2019 developmental comparison, which showed only a 0.0435% relative mean log-loss gain and worsening in 2018–2019.
- Training-prevalence comparator remains **0.01608011759484342**, without updating it to the stress-year prevalence.

For the saved additive logit`z`, score unchanged`expit(z)` and sigmoid`expit(a*z+b)`. The third comparator is the saved constant training prevalence. Intercept-only calibration is not rescored in this protocol. There is no estimator fit, calibration fit, optimizer, predictor/model search, weighting, resampling, threshold search, threshold change or baseline replacement.

The favorable directional transfer criterion requires **both years** to have sigmoid-minus-unchanged log loss <−1e−10 and Brier ≤1e−10. Absolute mean prediction-gap changes are reported as diagnostics only and do not form an additional gate. The outcome is not a new method-selection decision.

## Population and source preservation

| Reused stress year | Candidate collisions | Fatal collisions | Injury collisions |
|---|---:|---:|---:|
| 2020 | 79,990 | 1,602 | 78,388 |
| 2021 | 83,590 | 1,628 | 81,962 |
| Pooled | 163,580 | 3,230 | 160,350 |

All source-valid binary targets in these two releases are retained, once per release-scoped candidate key. No completeness filter is applied. IDs/year/source provenance accompany predictions for reconciliation only. The eight model predictors retain dictionary-supported stated, unknown, other and jurisdiction-unavailable codes; null, conflicting, blank or unsupported values reject scoring.

The cohort is recorded fatal/nonfatal-injury collisions, not all crashes, trips, road users or individual deaths. Property-damage-only crashes, traffic exposure and non-crash observations are absent. Prospective availability of the post-crash recorded conditions remains unverified.

The producer verified **60 frozen prior input fingerprints** before and after scoring. Original baseline probabilities are reproduced within **1.39e-16**, below the 1e−12 check tolerance; the tiny difference reflects float64 score summation. Existing baseline and completed temporal-calibration artifacts remain byte-for-byte unchanged. The new scorer writes a separate versioned output directory and refuses to overwrite a completed stress version.

## Annual and pooled probability performance

| Population | Method | Mean predicted % | Observed fatal % | Log loss | Brier | AP % | ROC-AUC | O/E |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | unchanged | 1.6068 | 2.0028 | 0.09362190 | 0.01943947 | 4.3246 | 0.700600 | 1.24643 |
| 2020 | sigmoid | 1.5730 | 2.0028 | 0.09370939 | 0.01944446 | 4.3246 | 0.700600 | 1.27319 |
| 2020 | prevalence | 1.6080 | 2.0028 | 0.09860317 | 0.01964198 | 2.0028 | 0.500000 | 1.24548 |
| 2021 | unchanged | 1.6006 | 1.9476 | 0.09167345 | 0.01892611 | 4.1108 | 0.697752 | 1.21681 |
| 2021 | sigmoid | 1.5672 | 1.9476 | 0.09174567 | 0.01892967 | 4.1108 | 0.697752 | 1.24271 |
| 2021 | prevalence | 1.6080 | 1.9476 | 0.09633437 | 0.01910823 | 1.9476 | 0.500000 | 1.21119 |
| pooled | unchanged | 1.6036 | 1.9746 | 0.09262623 | 0.01917714 | 4.2081 | 0.699171 | 1.23132 |
| pooled | sigmoid | 1.5701 | 1.9746 | 0.09270592 | 0.01918140 | 4.2081 | 0.699171 | 1.25764 |
| pooled | prevalence | 1.6080 | 1.9746 | 0.09744380 | 0.01936923 | 1.9746 | 0.500000 | 1.22796 |

Log loss and Brier are proper probability scores; lower is better. Average precision is recall-step weighted precision, not trapezoidal PR area. O/E is the number of fatal collisions divided by summed predicted fatal-collision probabilities; values above 1 indicate aggregate underprediction. Here counts are fatal collisions, not the number of people killed.

Both feature-based score variants still outperform the training-prevalence comparator on proper probability scores. That is a different comparison from whether the selected calibration correction transfers. Against the unchanged feature model, sigmoid is worse in both years.

Positive sigmoid slope preserves ranking within this fixed model, so AP and ROC-AUC remain unchanged apart from possible numerical ties. The stress result concerns probability reliability, not a newly improved or degraded ranking model. It cannot establish that another threshold would fix probability calibration.

## Calibration gap and stability

| Year | Unchanged mean % | Sigmoid mean % | Observed % | Unchanged prediction−observed, pp | Sigmoid prediction−observed, pp |
|---|---:|---:|---:|---:|---:|
| 2020 | 1.6068 | 1.5730 | 2.0028 | -0.3960 | -0.4297 |
| 2021 | 1.6006 | 1.5672 | 1.9476 | -0.3470 | -0.3804 |

The saved 2017–2018 adjustment lowers average predicted severity in both stress years, while the original model already underpredicts their fatal proportion. The correction therefore increases the observed aggregate shortfall. This arithmetic does not identify why the later population differs. Exposure, reporting, source vintage, omitted conditions and real case mix cannot be separated using these records.

Fixed ten-bin and prespecified low-probability reliability summaries retain every bin, including empty/sparse bins. ECE is diagnostic and depends on the bins. The reliability figure shows full-range fixed-bin results alongside a0–10% low-probability view with omitted-bin collision counts labeled separately per method. Crosses identify bins with n<100 or fatal<5. Rare-bin estimates should not be treated as stable individual-risk evidence.

Macro summaries give each of the two years equal weight; pooled summaries weight collisions. Macro sample SD is descriptive, not a confidence interval from two independent replications. No hypothesis test or inferential interval was promised. The transfer decision uses the two annual comparisons directly.

## Availability and support checks

Every feature is reported separately as stated, unknown(U/UU), other(Q/QQ) or unavailable(X/XX), including absent groups. Pure any-unknown, any-other and any-unavailable flags overlap; there is no mutually exclusive priority recoding. Other remains observed information. Each group retains n, fatal count, probability/ranking metrics and the sparse warning; empty metrics and one-class ranking measures are undefined.

Category support reuses the saved 2019-fold training support and recomputes stress counts for every dictionary level, including zero support. Per-record training-unobserved flags remain visible. Marginal training support does not establish support for every joint scenario, and overlapping feature groups cannot be summed into a unique collision count. These diagnostics are not a demographic fairness evaluation.

## Reused-test limitation and interpretation

These years were previously inspected in EDA and scored by the original severity baseline. This stress test was chosen after their underprediction was known. Freezing the new comparison prevents further tuning but does not make the evidence pristine, independent or prospective. The earlier tiny developmental gain did not demonstrate transfer to these two reused years. This result does not prove that all calibration methods fail generally.

The original baseline remains the comparison reference, with its existing calibration and low-precision limitations intact. Neither unchanged nor sigmoid scores are promoted to deployment. No causal road-safety intervention effect, individual mortality probability or chance of an accident can be inferred.

## Artifacts, reproduction and validation

- [Executed stress-test notebook](../notebooks/06_calibration_transfer_stress_v1.ipynb): preserved model details, audit receipt verification, annual/pooled comparisons, gates and reliability outputs.
- [Experiment card](../models/calibration_stress_v1_card.md), [protocol](calibration_stress_v1_protocol.md), [independent validation](calibration_stress_v1_validation.md).
- `reports/tables/cstress_v1_metrics.csv`, `cstress_v1_macro.csv`, `cstress_v1_differences.csv`, `cstress_v1_transfer_gates.csv`: metrics and frozen directional assessment.
- `cstress_v1_reliability.csv`, `cstress_v1_ece.csv`, `cstress_v1_level_support.csv`, `cstress_v1_membership.csv`: bins, source coverage and category evidence.
- `reports/figures/cstress_v1_scores.png`, `cstress_v1_reliability.png`: inspected probability-score/gap and reliability figures.
- `data/derived/calibration_stress_v1/`: full predictions, byte-identical archived model copy, assessment and producer/audit manifests.

Validate a completed saved version:

```bash
.venv/bin/python -m road_to_safety.validate_calibration_stress_v1
.venv/bin/python -m unittest discover -s tests -v
```

To reproduce scoring in a separate working copy containing the pinned inputs and no completed stress manifest:

```bash
uv sync --locked --python 3.13 --extra notebook
MPLCONFIGDIR=/tmp/road-to-safety-mpl .venv/bin/python -m road_to_safety.score_calibration_stress_v1
```

All **30 independent audit checks passed with zero failures**, and all **61 regression tests passed**. The independent auditor joins every prediction to the source, reconstructs logits and both probability functions without fitting, checks exact saved parameters and original-baseline agreement, recomputes all metrics/bins/availability/support/gates, and verifies no fitting/search API occurs in the producer. The notebook verifies the passed audit receipt and bound input/output fingerprints instead of repeating the full audit merely to display unchanged results.

The notebook executed all **9 code cells** with **two saved PNG outputs** and no errors. It verified the passed audit receipt and all bound inputs/outputs without fitting or rescoring. Both standalone figures were visually inspected separately from notebook execution. Whole-notebook page rendering remains unverified because of the previously recorded local browser URL-policy restriction.

## Next research decision

Do not replace the baseline or retune the correction on these stress years. Preserve this negative result. Stronger independent evaluation requires newer audited record-level or prospective observations; better temporal/contextual information is needed before claiming an operational probability model. Any additional fitting or model comparison needs a separate protocol, explicit decision context and disclosure of all previously inspected outcomes.
