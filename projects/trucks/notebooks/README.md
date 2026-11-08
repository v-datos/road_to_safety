# Notebooks

`01_dataset_validation.ipynb` inspects existing collision build outputs, independently checks keys and selected counts, and displays bounded reconciliation and quality tables. It does not rerun the dataset build or calculate casualty totals.

From the repository root:

```bash
uv sync --extra notebook
.venv/bin/python -m truck_collisions.build
.venv/bin/python - <<'PYTHON'
import nbformat
from nbclient import NotebookClient
path = "notebooks/01_dataset_validation.ipynb"
notebook = nbformat.read(path, as_version=4)
NotebookClient(notebook, timeout=300, kernel_name="python3", resources={"metadata": {"path": "."}}).execute()
nbformat.write(notebook, path)
PYTHON
```

Use the same Python environment for the build and notebook. The notebook locates the repository root automatically. Saved outputs are retained so readers can inspect the executed checks without rerunning them. Passing notebook assertions covers structural checks and internal consistency; unresolved differences with published counts remain visible.

`02_descriptive_trends.ipynb` reruns the descriptive analysis, checks its annual tractor counts against a separate event query, and embeds its figures and sensitivity tables. Install both extras with `uv sync --extra notebook --extra analysis`, then use the execution command above with the second notebook's path. It reads the existing collision dataset; rebuilding the raw sources is unnecessary when those files have not changed. The notebook reports the historical 2012–2021 decade and the available 2016–2021 segment, while retaining the unfulfilled 2016–2025 target.

`03_casualty_analysis.ipynb` reads the person-level casualty build, reruns the casualty analysis, independently checks group sums and selected change/share formulas, and displays the annual harm and group figures. Run `python -m truck_collisions.build_casualties` first, then execute this notebook with both extras installed. Its record-resolution scenarios are not confidence intervals or bounds on actual casualties; unknown outcomes and unresolved published benchmark differences remain explicit. Full methods are in `docs/casualty_contract.md` and `docs/casualty_validation.md`.

`04_conditions_quality.ipynb` reruns the missingness/code audit, directly recomputes 253 tractor field/year profiles and all their status counts from event queries, checks cohort/severity additivity across all 4,554 profiles, and verifies selected joint-field retention counts. It displays the availability figure and records the conditional readiness decision for 2012–2021. Install both extras and execute it using the same command pattern above. Methods, residual categories, early distribution flags and next-step safeguards are in `docs/conditions_quality.md`; it does not perform weather-effect or configuration-outcome analysis.

`05_descriptive_conditions.ipynb` reruns the condition statistics and reporting modules, displays three figures and selected n/N tables, and independently queries 822 primary category/cohort/severity cells plus selected joint counts and formulas. It compares the 2012–2021 tractor and no-recorded-tractor populations, preserving unknown/other categories, all-event and named-only denominators, fatal/injury strata, strict filtering and period sensitivities. Both extras and the existing condition-quality outputs are required. The full narrative and limitations are in `docs/conditions_findings.md` and `reports/conditions/findings.md`. Shares describe reported casualty events, not driving risk or fault.

`06_configuration_decomposition.ipynb` reruns the symmetric configuration accounting decomposition, displays both figures and independently recomputes primary category counts and effects from direct event queries. It verifies all scenario accounting identities and polar allocations. Both extras and the existing event dataset are required. Baseline-source checks are included when the preserved local baseline is available. Methods and results are in `docs/configuration_decomposition.md`; this is descriptive event accounting, not causal attribution or driving risk.

`07_exposure_compatibility.ipynb` checks all seven Table10 candidate cells directly against the preserved official HTML, Figure28 rounding, candidate uniqueness/units/status, five original source hashes and annual event/involvement diagnostics. It writes numerator and provenance evidence under `reports/exposure/` and calculates no collision rates. It requires the candidate CSV/metadata and preserved `data/raw/exposure/` sources listed in that metadata, plus the existing event dataset. Execute it with the same kernel pattern above. The controlling decision is in `docs/exposure_compatibility_audit.md`; passing arithmetic does not establish model or population compatibility.

`08_model_normalized_vkt_sensitivity.ipynb` reruns `truck_collisions.analyze_vkt_sensitivity`, embeds the durable narrative (`docs/model_normalized_vkt_sensitivity.md`) and three-panel figure (`reports/figures/vkt_model_normalized_sensitivity.png`), and independently verifies all 42 annual rows (`reports/tables/vkt_sensitivity_annual.csv`) and 114 summary rows (`reports/tables/vkt_sensitivity_summary.csv`) against direct DuckDB queries on `data/derived/ncdb/collisions.parquet`, `reconciliation.csv`, and `data/reference/tractor_exposure_candidates.csv`. All ratios are explicitly bounded as model-normalized historical sensitivities relative to the Table 10 model trajectory, not validated national semi-driving risk rates.

`09_vehicle_age_severity_audit.ipynb` reruns `truck_collisions.analyze_vehicle_age`, embeds the durable narrative (`docs/vehicle_age_severity.md`) and three-panel figure (`reports/figures/vehicle_age_conditional_severity.png`), and independently verifies all 28 vehicle/event `V_YEAR` audit rows (`reports/tables/vehicle_age_audit.csv`), 32 age-cohort severity rows (`reports/tables/vehicle_age_severity_cohorts.csv`), and 64 multi-tractor assignment sensitivity rows (`reports/tables/vehicle_age_multi_tractor_sensitivity.csv`) against direct DuckDB queries on `data/derived/casualties/record_alternatives.parquet` and `data/derived/ncdb/road_tractor_collisions.parquet`. Collision-conditioned age shares and severity do not measure fleet overrepresentation without fleet-age VKT denominators.
