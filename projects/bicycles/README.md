# Canada bicycle collision report · 2010–2023

The first descriptive edition is implemented. National NCDB Online trends, severity, bicyclist demographics, timing and condition profiles cover **2010–2023**. Unique collision counts, all-road-user harm and co-involved vehicle detail use linked public records for **2010–2021**. Missing 2022–2023 event records are not estimated.

Open the [local report preview](http://127.0.0.1:4186/?view=1) while its server is running. The report's editable application source is in `report/`; the compiled preview is `report/dist/index.html` with its complete data sidecar.

## First-edition findings

- Bicycle involvements declined from 6,712 in 2010 to 4,902 in 2023 (−27.0%). The 2023 count rose 21.1% from 2022 and was 5.9% above 2019.
- The direct NCDB Online bicyclist query reports 46 deaths and 4,742 nonfatal injuries in 2023. Across 2010–2023, that same cube records 712 deaths and 75,610 nonfatal injuries.
- May–September accounts for 70.2% of bicycle involvements; public-road intersections account for 61.1%.
- Linked records identify 68,687 unique bicycle-involved casualty collisions during 2010–2021. A light-duty vehicle with a known ID is recorded in 89.8% of those events (`0.708%` fatal); heavy unit trucks (`7.623%` fatal, `10.76x`) and road tractors (`13.355%` fatal, `18.86x`) are co-involved in `2.05%` of bicycle collisions but `20.36%` of fatal bicycle collisions. Co-involvement does not establish impact or fault.
- Cross-linking national typology severity (`M2_full_typology` bicyclist `ROC-AUC 0.6810 -> 0.7576` on `2020–2021` test) with Toronto Centreline + AADT exposure (`2006–2023`, `543` monitored / `935` network cyclist KSI crashes) shows that Major and Minor Arterials concentrate `82.3%` of monitored cyclist KSI crashes, with Minor Arterials leading per unit of motor-vehicle travel (`0.751` cyclist KSI / 100M VKT) and Major Arterials leading in spatial density (`0.674` cyclist KSI / km), topped by `Spadina Ave` (`6.004 / 100M VKT`), `Bloor St W` (`29` monitored / `36` network cyclist KSI; `2.688 / 100M VKT`), `Danforth Ave` (`2.313 / 100M VKT`), and `Yonge St` (`21` monitored cyclist KSI; `1.061 / 100M VKT`). The Toronto corridor exposure denominator is an **exposure-proxy screening estimate** derived from short-duration studies (median 72h, FHWA TMG caveats; 43.5% single-year vs 56.5% multi-year count segments), with robust ranking stability (Spearman $\rho = 0.982$ under 2006–2023 window constraints). See [corridor exposure synthesis](docs/corridor_exposure_synthesis.md).

Involvements, collisions and people are different units. Results describe recorded casualty collisions and harm, without causal claims or trip-level bicycle-volume risk. The source and query differences documented in [validation](docs/validation.md) remain unresolved.

## Project layout

```text
data/sources.json         Selected record releases, project-relative paths and pinned hashes
data/source_catalog.json  Source roles and acquisition status
data/raw/                 Preserved originals, acquisition metadata and browser table captures
data/derived/             Linked event, vehicle and person tables, validation and report snapshot
data/reference/           Versioned online aggregate series, metadata and publication benchmark
docs/                     Analysis plan, data contract, validation findings and corridor exposure synthesis
src/bicycle_collisions/   Acquisition, record build, online normalization, report evidence and corridor synthesis
tests/                    Focused grain/identity, online-population, corridor exposure and notebook checks
notebooks/                Executed companion notebooks (01 validation, 02 trends/conditions, 03 corridor synthesis)
report/                   Canonical interactive report application
reports/tables/           CSV evidence tables (national + Toronto cyclist corridor exposure)
reports/figures/          Native report chart PNGs, synthesis figure and visual QA sheets
reports/summary.json      Checks, headline totals, coverage and fingerprints
```

## Reproduce the analysis

Run commands from `projects/bicycles/`:

```bash
uv sync --locked
.venv/bin/python -m bicycle_collisions.acquire
.venv/bin/python -m bicycle_collisions.build
.venv/bin/python -m bicycle_collisions.online
.venv/bin/python -m bicycle_collisions.analyze
MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src .venv/bin/python -m bicycle_collisions.corridor_exposure_link
MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

`acquire` verifies existing files and downloads missing pinned record inputs. The initial acquisition copied original bytes from `../trucks` with `--from-project ../trucks`; subsequent analysis reads only bicycle project inputs. Record builds convert the annual XLSX files and may take several minutes.

`online` requires the archived DOM captures under `data/raw/ncdb_online/`. The selected normalized public series and metadata are versioned in `data/reference/`, so `analyze` can rerun using that reviewed CSV when browser captures are unavailable. Reacquiring the online series requires the wizard selections recorded in its metadata; there is no unattended online downloader. A checksum mismatch requires a source-release review.

`analyze` regenerates tables and reviewed evidence. When `report/` exists, it updates its data while preserving the report identity and presentation metadata, and marks the app updating. Rebuild and check the report before setting `buildStatus` to `complete` in `report/src/data.json` for delivery. See [the report authoring guide](report/AGENTS.md) for the installed build command and verification contract.

Serve the complete compiled directory locally:

```bash
.venv/bin/python -m http.server 4186 --bind 127.0.0.1 --directory report/dist
```

## Definitions and source evidence

Read [the analysis plan](docs/analysis_plan.md), [data contract](docs/data_contract.md), [validation findings](docs/validation.md), [corridor exposure synthesis](docs/corridor_exposure_synthesis.md), [companion notebooks](notebooks/README.md) and [data provenance notes](data/README.md).

Official sources: [Transport Canada statistics index](https://tc.canada.ca/en/road-transportation/statistics-data), [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en), and [public NCDB records and dictionary](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a).
