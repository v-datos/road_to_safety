# Frozen calibration transfer stress test v1

This scoring-only experiment applies the saved 2019 development fold: logistic regression fitted on 1999–2016, sigmoid calibration fitted on 2017–2018, selected using the six 2014–2019 developmental evaluations. No estimator, calibrator, prevalence, threshold or hyperparameter is fitted to 2020–2021.

Population: all prepared severity-eligible candidate collisions in the 2020 and 2021 releases. Target: fatal versus injury among recorded collisions; no accident-occurrence, individual mortality, causal or deployment inference. Dictionary-supported unknown, other and unavailable categories remain separate.

Frozen protocol SHA-256: `a7c1732e8aa9348c264d8e5d118b7e93190a73604d600b405ec5ca5655eef54d`. Original-model maximum absolute probability discrepancy: `1.39e-16`.

Comparators: unchanged probabilities, saved sigmoid correction, and constant 1999–2016 training fatal prevalence. Report each year, pooled collision-weighted evidence, and macro annual mean/sample SD. Sample SD is descriptive, not uncertainty coverage. Fixed-bin reliability and ECE are diagnostic and bin-dependent. Flag n < 100 OR fatal < 5; retain empty groups with null rates.

Predeclared directional transfer gate passes in both years: **False**. See `reports/tables/cstress_v1_transfer_gates.csv` and `docs/calibration_stress_v1_results.md` for score differences and interpretation. This is reused retrospective stress evidence: these years were previously inspected and scored in the original baseline. There is no fresh holdout, model replacement, threshold recommendation or claim of reliable transfer.
