# Bicycle notebooks

No analysis notebooks have been created or executed yet. The first report is reproducible through the acquisition, build, online-normalization and analysis modules in `src/bicycle_collisions/`. A notebook companion can be added using the validated saved evidence below; it is not required to reproduce this edition.

Proposed sequence:

1. `01_data_validation.ipynb`: inspect coverage, event/vehicle/person keys, coding consistency and official benchmark comparisons.
2. `02_trends_and_casualties.ipynb`: independently verify annual collision and bicyclist casualty tables.
3. `03_profiles_and_conditions.ipynb`: inspect demographics, timing, co-involved vehicles and usable condition fields.

Reusable preparation and analytical calculations belong in `src/bicycle_collisions/`. Notebooks provide exploration, direct checks and presentation of saved results. Resolve the project root using its own `pyproject.toml`, so execution works from either this directory or the project root. Document dependencies and execution commands when implementing each notebook.
