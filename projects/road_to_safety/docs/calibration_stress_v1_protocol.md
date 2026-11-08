# Saved-calibration transfer stress test v1

Protocol frozen on 20 October 2026, before new stress-test scores were computed. The executable specification is [`data/reference/calibration_stress_v1_protocol.json`](../data/reference/calibration_stress_v1_protocol.json), SHA-256 `a7c1732e8aa9348c264d8e5d118b7e93190a73604d600b405ec5ca5655eef54d`. Its UTC timestamp records the machine execution time; the project’s user-facing date and timezone are 2026-10-20, America/Edmonton.

## Question and evidence status

Does the previously selected, saved sigmoid correction transfer to probability scores in 2020 and 2021 without any refitting or new model search?

This is a **reused retrospective stress test**. Both years were examined in descriptive analysis and evaluated during the original baseline experiment. Their underprediction was known when this test was proposed. Freezing this protocol before these new comparisons prevents further methodological adaptation within this experiment; it does not turn these years into fresh or independent holdouts. Favorable results would remain descriptive evidence.

The population is recorded fatal/injury candidate collisions from the selected NCDB annual releases. The target is fatal collision versus nonfatal-injury collision, conditional on a recorded fatal/injury event. The release-scoped key is `(source_id, C_YEAR, C_CASE)`. Every severity-eligible candidate in 2020 or 2021 is retained, with its unchanged binary target. An invalid target, unsupported feature code or conflicting feature value stops the run rather than producing a silent exclusion.

## Exactly which saved model is scored

Load `data/derived/temporal_calibration_v1/model_2019.json` and require the previous `selection.json` to select `sigmoid`. The model’s complete dictionary domains, reference levels, coefficient vector and intercept are copied into the frozen protocol as well as bound by file checksum.

| Component | Frozen origin or parameter |
|---|---|
| Base logistic fit | 1999–2016, exactly the saved final 2019 development-fold model |
| Calibration fit | 2017–2018 only; 225,746 calibration collisions |
| Base intercept | −4.149527843473987 |
| Sigmoid slope `a` | 0.9697790551002594 |
| Sigmoid intercept `b` | −0.1386345837431384 |
| Training fatal prevalence | 0.01608011759484342 |
| Stress evaluation | 2020 and 2021 separately, then pooled and equal-year macro summaries |

The saved base fit uses the same 1999–2016 training period and frozen design as the original severity baseline. There is no newly trained estimator. The saved sigmoid is from the final development fold; it is **not** recalibrated on all 2017–2019 records.

Compute float64 `z` directly from the saved intercept and categorical coefficients. Compare only:

1. **Unchanged:** `expit(z)`.
2. **Saved selected sigmoid:** `expit(a*z+b)` using the exact saved values above.
3. **Training-prevalence comparator:** the saved constant 0.01608011759484342.

Do not score intercept-only recalibration or another candidate. Do not fit an estimator, change a threshold, modify a coefficient, optimize a calibrator or select a replacement model. Save candidate keys, year, target, base logit and all three probabilities so independent reconstruction is possible.

## Categorical handling and population checks

Retain the same eight approved features: `C_MNTH`, `C_WDAY`, `C_HOUR`, `C_RCFG`, `C_WTHR`, `C_RSUR`, `C_RALN` and `C_TRAF`. Use the exact dictionary order and dropped references from the previous protocol: month 1, weekday 1, hour 12, road configuration 1, weather 1, surface 1, alignment 1 and traffic control 18. Numeric tokens remain canonical strings.

Unknown `U/UU`, other `Q/QQ` and unavailable `X/XX` are separate supported categories. Other is not missing. No imputation, complete-case filtering, recoding or vocabulary learning is permitted. Nulls, blanks, conflicts and out-of-domain values reject the run. Dictionary levels without training support retain their saved neutral coefficient; report their stress-year incidence and do not interpret neutrality as evidence of no association.

The evaluator must verify that source keys are unique, the target is unchanged, all intended 2020–2021 keys appear once and no other years are scored. Eligibility and feature states are checked against the prepared analytical source rather than inferred from the output predictions alone.

## Scores and aggregation

Report candidate count, fatal count and nonfatal count alongside every annual and pooled score. Compute natural-log binary log loss with float64-epsilon probability clipping; Brier score; recall-step weighted average precision; ROC-AUC; mean predicted probability; observed fatal proportion; mean predicted minus observed; and observed/expected fatal counts (`sum(y)/sum(p)`). Higher observed/expected ratios indicate underprediction. Empty groups have null scores; ranking measures are null for one-class groups.

Show 2020 and 2021 separately. Also show the collision-weighted pooled 2020–2021 scores and the unweighted arithmetic mean of the two annual scores. These answer different descriptive questions. Macro ranking measures average annual metrics; pooled ranking measures are computed on all pooled predictions. No confidence interval or statistical independence is inferred from two annual values.

For the sigmoid, show actual signed differences from unchanged for annual, pooled and macro metrics. Negative log-loss or Brier differences favor sigmoid. Comparator results remain visible, with no use of stress labels to update its constant probability. Aggregate calibration gaps and observed/expected ratios are descriptive and do not identify a mechanism behind changes in case mix.

## Reliability diagrams and ECE

Reuse both frozen bin schemes:

- Fixed deciles: `0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1`.
- Low-probability edges: `0, .005, .01, .015, .02, .03, .05, .1, .2, .3, .5, 1`.

Intervals are `[lower, upper)`; the last includes 1. Retain empty bins, with count zero and null averages. For every method, year and pooled partition report bin count, fatal count, mean prediction, observed proportion and sparse flag. Expected calibration error is `sum((n_bin/n)*abs(observed_bin-mean_prediction_bin))`. ECE is bin-dependent descriptive evidence; it does not determine the transfer assessment. Sparse groups satisfy `n < 100 OR fatal_count < 5`; flag and retain them without stable subgroup-ranking claims.

## Availability and support checks

For each of the eight features separately, report stated, unknown, other and unavailable groups, including groups with no observations. Show the three methods’ probability/ranking scores with denominators and sparse flags for 2020, 2021 and their pooled population. Report every dictionary category’s support, including zero-support categories and training-unobserved levels.

Also report three pure collision-level flags across the eight features: `has_unknown`, `has_other` and `has_unavailable`, each with both presence and absence groups even when empty. These flags may overlap. A collision with an unknown in one field and an other code in another belongs to both presence groups; do not create mutually exclusive priority groups or add their counts as if disjoint.

## Frozen descriptive transfer assessment

For **both** 2020 and 2021, require:

- `sigmoid log_loss − unchanged log_loss < −1e−10`; and
- `sigmoid Brier <= unchanged Brier + 1e−10`.

Only if both conditions hold in each year is the outcome `favorable_descriptive_transfer`. Otherwise it is `transfer_not_demonstrated`. Report the actual differences regardless of the outcome. Pooled or macro improvements cannot override a failing year. This assessment neither changes the previous developmental selection nor authorizes replacement of the baseline or operational use.

## Preservation, independent validation and amendment policy

The machine specification fingerprints 60 existing assets, including the prepared collision dataset, source/preparation metadata, modeling contracts, environment lockfile, original baseline outputs and receipt, all completed temporal-calibration model/prediction/table/chart outputs, the selected model and method, relevant notebooks and prior result/protocol documents. Existing manifest hashes were verified while freezing the protocol, and preparation, severity and temporal-calibration validation receipts must have passed status. All bound assets must match before and after the run. The new protocol and producer/validator code fingerprints belong in the new experiment manifest and validation receipt.

An independent validator reconstructs predictions from original categorical values and saved parameters, reconciles candidate coverage and target labels, recomputes annual/pooled/macro/group metrics, reliability bins, ECE, score differences and the assessment rule, and verifies byte-for-byte preservation of prior artifacts. New evidence is written under `calibration_stress_v1` names; old baseline and temporal-calibration artifacts remain unchanged.

The JSON also carries historical limitations from the preceding six-fold development experiment. Its references to six evaluation years, overlapping training windows and shared cross-fold history describe that prior method-selection evidence. This stress test itself uses only two evaluation years and one fixed saved estimator; it creates no new expanding-window folds.

No accident-occurrence, individual-mortality, causal, prospective-performance, statistical-significance or deployment-readiness claim follows from this test. Shared source/reporting changes and unknown feature availability limit interpretation. This experiment introduces no confidence intervals. Any methodological amendment after scores are inspected requires a separately versioned protocol with disclosure of inspected results; never overwrite this frozen specification.
