# Verification

Sixty-one focused regression tests cover the implemented pipeline:

- `test_audit_data.py`: source sentinel meanings, grain/conflicts and manifest-aware cache reuse.
- `test_verify_sources.py`: corrupted catalog bytes, incomplete audit rejection and source disagreement preservation.
- `test_prepare_collisions.py`: strict keys, unexpected years, blank/invalid codes, duplicate multiplicity, child joins, conflicting targets and row-numbered exception evidence.
- `test_validate_prepared.py`: independent mutations of keys, targets, feature leakage, domains, conservation, arbitrary conflict resolution and blank-versus-conflict profile reconciliation.

- `test_exploration.py`: stale receipt rejection, corrupted proportions/numerators, duplicate groups and count conservation.
- `test_analyze_temporal.py`: dictionary weekday/sentinel meanings and eligible target denominators.
- `test_analyze_conditions.py`: Wilson interval hand calculation/boundaries, category labels and sparse flags.
- `test_analyze_stability.py`: domain-aware availability classes, conflict precedence and unsupported code handling.

Run `.venv/bin/python -m unittest discover -s tests -v` from the project directory.

Full source fingerprints, independent full-Parquet SQL validation, 253 audit comparisons and 2,300 independently read source rows supplement these fixtures. See the [preparation validation report](../docs/preparation_validation.md). Modeling transforms, chronological split isolation and predictive performance will be tested when those stages are implemented.

- `test_fit_severity.py`: precision-optimal threshold, tied-score inclusion, calibration boundaries and one-class metric handling.
- `test_validate_severity.py`: independent score/metric mutations, split boundaries, unsupported features and tied ranking.

Full-cohort severity validation additionally reconstructs every model probability and recomputes saved metrics from collision-level predictions without refitting.

The temporal calibration v1 producer/auditor tests cover calibration likelihood convergence, monotonicity, bin edges, selection gates/ties, temporal exclusion, changed coefficients/labels and tied ranking scores. The full source-linked audit supplements these fixtures without refitting estimators.

- `test_calibration_stress_v1.py`: source-score/domain handling, probability/bin boundaries and frozen transfer gates.
- `test_validate_calibration_stress_v1.py`: changed parameters/years/probabilities, independent ranking/bin behavior and the annual-only assessment rule.

The completed stress-test audit passed 30 independent full-artifact checks; all 61 regression tests pass.
