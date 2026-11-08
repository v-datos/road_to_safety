# Tree comparison v1

This study extends the severity research with Random Forest and LightGBM. It uses the pinned prepared collision table and the eight dictionary-coded fields already approved in the project. Each of the six development folds fits the models on prior years and evaluates the following year. The final stress evaluation reuses 2020 and 2021. Selection and thresholds are written before stress scoring.

The complete specification is described in the [analysis plan](../../docs/analysis_plan.md). The [frozen machine protocol](../../data/reference/tree_comparison_v1_protocol.json) records the executable configuration, input fingerprints and ordered candidates. The runner verified and saved its local copy before fitting. The archived project environment and results are verified separately.

## Run and resume

From the Road to Safety project directory, synchronize the independent environment with the lock file.

```sh
uv sync --locked --project experiments/tree_comparison_v1 --python .venv/bin/python
```

Then run the full pipeline.

```sh
experiments/tree_comparison_v1/.venv/bin/python -u experiments/tree_comparison_v1/complete.py
```

The pipeline waits if the training process is active. Each completed candidate stores its fitted model, development predictions, scores and a commit marker with their checksums. Restart with the same command to reuse verified checkpoints. The search performs 120 tree fits plus 12 baseline fits and can take several hours on a laptop.

The independent validator checks the complete grid, candidate files, population, scores, model selection, thresholds, restored predictions, classification metrics and reliability tables. After validation the pipeline creates the technical report and executed notebooks, then the policy brief and public story. Visual inspection is recorded separately.

## Files and evidence

- Local experiment files are in `data/derived/tree_comparison_v1/`.
- Aggregate comparison evidence goes in `reports/tables/tree_comparison_v1/`.
- The final HTML and PDF files go in `reports/portfolio/`.
- [Reviewed policy sources](../../docs/policy_evidence.md) record intervention evidence, recommended actions and evaluation measures.
- Geographic source and join details are stored with the [reviewed 2024 rates and boundary paths](../../data/reference/geography/jurisdictions_2024.json).

The outcome describes the fatal share among recorded casualty collisions. The records lack a travel exposure frame and event geography. The map represents published rates at the province and territory level.
