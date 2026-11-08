# Canadian collision research

Independent analysis projects are organized under `projects/`.

| Project | Scope | Status |
| --- | --- | --- |
| [Truck collisions](projects/trucks/README.md) | Canadian road-tractor collision trends, casualties, conditions and exposure | Existing analysis and reproducible pipelines; public records cover 1999–2021 |
| [Bicycle collisions](projects/bicycles/README.md) | Canadian bicycle-involved collisions and bicyclist casualties | First descriptive report, 2010–2023; linked detail through 2021 |
| [Road to Safety](projects/road_to_safety/README.md) | All-road-user collision severity, risk factors, spatial/temporal patterns, corridor exposure SPFs and operational triage | Portfolio + 4-phase operational decision-support action plan complete (69/69 tests passing) |

Each project owns its data, source code, tests, notebooks, reports and documentation. See [the project organization guide](projects/README.md) when adding another analysis.

## Data sources

- [Transport Canada — Statistics and data](https://tc.canada.ca/en/road-transportation/statistics-data): official index for road-transportation statistical reports and data sources.
- [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en): interactive national aggregate tables.
- [NCDB Open Government dataset](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a): public record releases and data dictionary.

## Running the truck analysis

Run the commands documented by a project from its own directory. For the existing truck project:

```bash
cd projects/trucks
uv sync --extra notebook --extra analysis
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The [truck project README](projects/trucks/README.md) contains the build and analysis commands.
