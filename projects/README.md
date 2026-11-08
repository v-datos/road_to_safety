# Analysis projects

Create one directory under `projects/` for each analysis, using a short lowercase name. Add it to the repository's main project index.

Each project has its own README describing its research question, source coverage, status and execution commands. Keep its documentation in `docs/`, notebooks in `notebooks/`, and generated results in `reports/`. Add `data/`, `src/`, `tests/` and a Python project configuration when implementation requires them.

Run project commands from that project's directory. Paths such as `data/sources.json` and `reports/` in its documentation are relative to that directory. Each project owns its inputs and outputs; preserve source URLs, release metadata and checksums when acquiring data. Configure project-specific ignore rules for large source files and generated artifacts.

| Directory | Analysis |
| --- | --- |
| [trucks/](trucks/README.md) | Existing road-tractor collision analysis, including its original data archive and Python environment |
| [bicycles/](bicycles/README.md) | National bicycle report, 2010–2023; reproducible linked detail through 2021 |
| [road_to_safety/](road_to_safety/README.md) | All-road-user severity, corridor SPF/EB screening, typology-enhanced severity (`P_USER`/`V_TYPE`), 3-tier cost-utility triage and 2022+ prospective drift monitoring |
