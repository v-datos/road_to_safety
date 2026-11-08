# Bicycle notebooks

Three companion notebooks are implemented and executed with captured outputs (`nbformat` v4):

1. [`01_bicycle_dataset_and_online_validation.ipynb`](01_bicycle_dataset_and_online_validation.ipynb): Reconciles the `2010–2021` linked public microdata (`68,687` unique bicycle collisions across `155,984` input rows) with the `2010–2023` NCDB Online aggregate series (`712` deaths, `75,610` nonfatal injuries across `462` validated partitions) and published `2020–2023` benchmarks, verifying grain conservation and documenting source/context discrepancies.
2. [`02_bicyclist_casualty_and_condition_trends.ipynb`](02_bicyclist_casualty_and_condition_trends.ipynb): Analyzes temporal trends (including the `-27.0%` decline from `2010` to `2023` and the `+21.1%` rebound in `2023` over `2022`), seasonal concentration (`May–September` `70.2%`), public-road intersection concentration (`61.1%`), age/sex demographics, and co-involved vehicle typologies (`89.82%` light-duty vehicles at `0.708%` fatality rate vs. `7.623%` [10.76x] in heavy unit trucks and `13.355%` [18.86x] in road tractors).
3. [`03_corridor_exposure_and_vru_synthesis.ipynb`](03_corridor_exposure_and_vru_synthesis.ipynb): Cross-links the national bicycle severity findings with the Phase 1 Toronto arterial AADT exposure rates (`cyclist_ksi_per_100m_vkt` and `cyclist_ksi_per_km` by road class and top corridors including `Bloor St W`, `Spadina Ave`, `Danforth Ave`, `Yonge St`, `St Clair Ave W`, `Davenport Rd`, `College St`, and `Harbord St`) and national `M2_full_typology` bicyclist discrimination lift (`ROC-AUC 0.6901 -> 0.7852` on `2017–2019` validation; `0.6810 -> 0.7576` on `2020–2021` test).

Reusable preparation and analytical calculations live in `src/bicycle_collisions/` (including `src/bicycle_collisions/corridor_exposure_link.py`). Each notebook resolves the project root using `pyproject.toml`, so execution works from either `projects/bicycles/` or `projects/bicycles/notebooks/` using:

```bash
MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src .venv/bin/python -m bicycle_collisions.corridor_exposure_link
```
