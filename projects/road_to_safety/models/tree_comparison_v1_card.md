# Tree comparison v1 model card

The target is fatal versus nonfatal injury among the selected 1999–2021 NCDB casualty collisions.
Use these scores to study retrospective severity patterns. Prospective use would require time-verified predictors, a new evaluation period and a decision-specific cost and calibration study.

## Design and selection

The four methods use matching chronological populations. Six development folds evaluate 2014–2019. Each fit uses only prior years. The probability inputs are eight dictionary-coded timing and road-condition fields.
The 2019 models were fitted through 2018. Thresholds use 2019 and maximize precision subject to 80% recall.
The reused 2020–2021 period was scored after freezing the selection and thresholds.

| Family | Configuration | Annual log loss wins vs logistic | Development gate |
| --- | --- | ---: | --- |
| Random Forest | rf_08 | 3 | Fell short |
| LightGBM | lgbm_12 | 6 | Met |

## Reused stress period

| Model | Log loss | Brier | Average precision | Fatal recall | Precision | Flagged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Training prevalence | 0.097459 | 0.019370 | 1.97% | 100.00% | 1.97% | 100.00% |
| Logistic regression | 0.092573 | 0.019175 | 4.23% | 82.32% | 2.91% | 55.83% |
| Random Forest | 0.092488 | 0.019165 | 4.45% | 81.52% | 2.94% | 54.69% |
| LightGBM | 0.091502 | 0.019084 | 5.66% | 81.86% | 3.02% | 53.57% |

## Scope and reproducibility

The records lack geographic identifiers and travel exposure. The outcome covers recorded casualty collisions. The inputs were recorded after crashes. Sparse groups and previously examined years limit generalization.
Permutation importance measures changes in predictive loss within the fitted models. Correlation and input availability affect interpretation.

See the [experiment instructions](../experiments/tree_comparison_v1/README.md) and [reviewed technical report](../reports/portfolio/technical-report.html).
