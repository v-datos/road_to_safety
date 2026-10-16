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
