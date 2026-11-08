# Model artifacts

The frozen training-prevalence and categorical L2 logistic severity baselines have been fitted. See [model card](severity_model_card.md), [protocol](../docs/severity_protocol.md) and [results](../docs/severity_modeling.md). Exact portable coefficients/encoding, predictions and receipts are preserved locally as `data/derived/severity_*`. Serialized estimators, preprocessing objects and run directories belong here locally and are ignored by Git. Version model cards as Markdown; place reviewed evaluation tables in `reports/tables/`.

Each saved run must identify its source checksums, selected population/years, target, feature allowlist, split membership, preprocessing, dependency lockfile, seed, parameters, calibration and threshold. Save the estimator and preprocessing together.

A model card must explain intended use, prediction-time inputs, conditional population, temporal test results, class support, calibration, subgroup limitations and prohibited interpretations. A conditional severity score must never be presented as the chance of having an accident during ordinary travel.

The separate [temporal calibration v1 card](temporal_calibration_v1_card.md) documents six expanding-window development folds and the marginal sigmoid recommendation. The original model card and artifacts remain unchanged.

The [calibration transfer stress-test card](calibration_stress_v1_card.md) records failure of the saved correction to improve 2020–2021 scores. No prior model is replaced or altered.


The completed [tree comparison v1 card](tree_comparison_v1_card.md) documents the matching prevalence/logistic baselines, Random Forest and LightGBM, six development years and reused 2020–2021 evaluation. The selected LightGBM configuration passed the developmental improvement rule. The selected Random Forest configuration fell short of that rule. Local fitted estimators, predictions and integrity receipts are in `data/derived/tree_comparison_v1/`.
