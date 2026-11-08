# Canadian collision research

Independent analysis projects are organized under `projects/`.

| Project | Scope | Status |
| --- | --- | --- |
| [Truck collisions](projects/trucks/README.md) | Canadian road-tractor collision trends, casualties, conditions, Table 10 modeled VKT sensitivity (2015–2021) and vehicle-age (`V_YEAR`) severity audit | Complete through Question 7 + 9 executed notebooks (36/36 tests passing) |
| [Bicycle collisions](projects/bicycles/README.md) | Canadian bicycle-involved collisions, bicyclist casualties, heavy-freight lethality and Toronto corridor VKT exposure linkage | Descriptive report (2010–2023), corridor synthesis + 3 executed notebooks (10/10 tests passing) |
| [Road to Safety](projects/road_to_safety/README.md) | All-road-user collision severity, risk factors, spatial/temporal patterns, corridor exposure SPFs and operational triage | Refreshed portfolio + 4-phase operational decision-support action plan complete (69/69 tests passing) |

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
