# Analysis notebooks

- [01_source_and_quality_audit.ipynb](01_source_and_quality_audit.ipynb): acquisition coverage, source grain, outcomes, raw-record missingness and revisions.
- [02_collision_dataset_validation.ipynb](02_collision_dataset_validation.ipynb): independent validation of collision uniqueness, targets, conservation, exception handling, event-level missingness and fingerprints.

- [03_exploratory_descriptive_analysis.ipynb](03_exploratory_descriptive_analysis.ipynb): temporal patterns, condition–severity comparisons, unknowns, sparse cells and source-year stability. Regenerates summaries and figures and independently validates them.

The first two notebooks executed all seven code cells in the locked project environment. Saved outputs and notebook structure were validated. Rendered visual inspection remains unverified because of the previously recorded browser URL policy restriction; no charts were authored in these preparation phases.

Use the project `.venv` Python kernel. The [validation report](../docs/preparation_validation.md) supplies reproducible preparation and validation commands. Source originals remain unchanged.

The exploratory notebook executes the three analysis modules and full-cohort reconciliation. Thirteen standalone chart images are embedded; those images were visually inspected, while a whole-notebook rendered preview remains unverified. Use `python -m road_to_safety.explore` to rerun all calculations and the validation gate. The descriptive notebook fits no model; the separate fourth notebook accompanies the completed baseline severity run.

- [04_chronological_severity_baselines.ipynb](04_chronological_severity_baselines.ipynb): frozen splits, baseline/model performance, late-year calibration and subgroup checks, coefficients and independent validation. Reads the saved fixed run without refitting; four model figures are embedded. Whole-notebook rendering remains unverified; standalone charts are inspected.

The severity notebook executed all **12 code cells** and saved **four PNG figure outputs** without errors. Its full-cohort saved-run audit passed all **22 checks**; standalone figure inspection is distinct from the unverified whole-page notebook preview.

- [05_temporal_robustness_calibration_v1.ipynb](05_temporal_robustness_calibration_v1.ipynb): frozen six-fold design, calibration comparison, recommendation, reliability and support. Verifies the independent audit receipt and bound saved-run artifacts without repeating model fits or the full source audit. Includes a clearly labeled low-probability zoom companion.

The fifth notebook executed all **11 code cells** with **three saved PNG outputs** and no errors. It verified the passed 44-check audit receipt and all bound artifact fingerprints; the standalone figures were visually inspected. Whole-notebook page rendering remains unverified.

- [06_calibration_transfer_stress_v1.ipynb](06_calibration_transfer_stress_v1.ipynb): scoring-only comparison on reused 2020–2021 data, frozen gates, signed probability-score changes, reliability and availability groups. Verifies the independent audit receipt without fitting or rescoring.

The sixth notebook executed all **9 code cells** with **two saved PNG outputs** and no errors. It verified the passed 30-check audit and all bound fingerprints; both standalone charts were visually inspected. Whole-notebook page rendering remains unverified.


## Completed portfolio extension

- [07_tree_comparison_v1.ipynb](07_tree_comparison_v1.ipynb) reads the validated 132-fit grid, frozen selection, retrospective metrics, permutation importance and reliability figure.
- [08_portfolio_synthesis.ipynb](08_portfolio_synthesis.ipynb) verifies descriptive denominators and combines national trends, geography and model results.

Both notebooks executed all three code cells with saved outputs and zero errors in the independent experiment environment. Their saved tables agree with the technical report and policy brief.
