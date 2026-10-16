# Canadian truck collision analysis

Research question: Did collisions involving road tractors (the closest NCDB category to semis) increase over the latest comparable decade, and which measured factors are associated with changes?

This repository contains the validated historical analysis and its reproducible pipelines. The pre-existing `Collisions/` directory is a 4.3 GB legacy research archive. It remains in place and is excluded from Git because it contains large raw datasets and duplicate copies. See [the inventory](docs/data_inventory.md) before using any of its files.

## Project layout

```text
Collisions/             Legacy inputs and references; leave original files unchanged
data/derived/           Reproducible intermediate tables (ignored by Git)
data/raw/ncdb/          Official annual originals and dictionary (ignored by Git)
data/sources.json       Input selection, source URLs, coverage and checksums
data/source_releases/   Preserved source selections, baseline hashes and provenance
data/reference/         Benchmarks separated by unit, source and release
docs/data_inventory.md  File inventory, provenance, and known quality issues
docs/analysis_plan.md   Research definitions, methods, and acceptance checks
docs/research_questions.md  Published precedents and prioritized questions
docs/website_database_review.md  Supplied websites and live NCDB tool findings
docs/dataset_contract.md  Dataset grain, columns, flags and rebuild commands
docs/dataset_validation.md  Current validation findings and unresolved issues
docs/casualty_contract.md  Person identities, outcomes and group assignment rules
docs/casualty_validation.md  Person record checks and occupant benchmark differences
src/truck_collisions/   Data preparation and analysis code
notebooks/              Exploratory work and presentation notebooks
tests/                  Focused checks for data grain and metric calculations
reports/                Final tables, figures, and written findings
```

The build covers **1999–2021** from public NCDB microdata. The observed collision tables preserve quality flags; a stricter tractor subset is available for sensitivity checks. The [source-version repair](docs/source_release_update.md) replaces selected historical inputs after collision and casualty validation and preserves the earlier baseline. Residual published benchmark differences and internally conflicting records remain explicit. Read [the validation findings](docs/dataset_validation.md) before interpreting a trend. The intended 2016–2025 research period remains incomplete; [the availability assessment](docs/data_availability.md) separates newer aggregates from missing public event records.

## Reproduce the dataset

```bash
uv sync --extra notebook
PYTHONPATH=src .venv/bin/python -m truck_collisions.download
PYTHONPATH=src .venv/bin/python -m truck_collisions.build
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The build writes `data/derived/ncdb/collisions.parquet`, `road_tractor_collisions.parquet` and `.csv`, `road_tractor_collisions_strict.parquet`, annual counts and validation evidence. The [dataset contract](docs/dataset_contract.md) defines every field and inclusion rule. [The notebook](notebooks/01_dataset_validation.ipynb) independently checks the saved outputs.

The [analysis plan](docs/analysis_plan.md) sets the research definitions and remaining gates; the [research questions](docs/research_questions.md) document worthwhile analyses and future studies; the [website review](docs/website_database_review.md) records national and provincial source coverage.

## First descriptive analysis

[The first findings](docs/descriptive_trends.md) compare event frequency and fatal share, with 2019, 2020 and strict-record sensitivities. The [executed notebook](notebooks/02_descriptive_trends.ipynb) and full report under `reports/trends/` reproduce the results.

```bash
uv sync --extra notebook --extra analysis
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib \
  .venv/bin/python -m truck_collisions.analyze_trends
```

## Who is harmed?

The [casualty findings](docs/casualty_findings.md) count deaths and injuries across **all people in tractor-involved events**, with annual results for 1999–2021 and group comparisons for the historical 2012–2021 decade. The [person contract](docs/casualty_contract.md) explains duplicate, dummy, unidentified and conflicting records; the [validation](docs/casualty_validation.md) documents checks and unresolved published benchmark differences. Record-resolution scenarios preserve uncertainty without inventing identities or imputing missing outcomes. These are descriptive results from the observed release, not a fully reconciled national casualty series.

```bash
PYTHONPATH=src .venv/bin/python -m truck_collisions.build_casualties
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib \
  .venv/bin/python -m truck_collisions.analyze_casualties
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The pipeline writes person keys, retained record alternatives, unresolved/dummy records, annual group counts and quality evidence under `data/derived/casualties/`. The analysis writes tables and figures under `reports/casualties/`; [the executed notebook](notebooks/03_casualty_analysis.ipynb) provides a reviewable companion.

## Condition-field readiness

[The quality assessment](docs/conditions_quality.md) profiles eleven collision fields by year, cohort, severity and observed/strict subset before weather or configuration comparisons. It separates unknown and invalid values from Q/QQ residual categories and measures joint-field sample loss. The [executed quality notebook](notebooks/04_conditions_quality.ipynb) independently checks the primary field-year counts and selected joint coverage.

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib \
  .venv/bin/python -m truck_collisions.audit_conditions
```

Results and input/code fingerprints are under `reports/conditions_quality/`. The audit leaves production data unchanged. Descriptive 2012–2021 comparisons can proceed with explicit unknown/other categories; the 1999 configuration distribution and any multivariable complete-case restriction require qualification.

## Descriptive condition comparisons

[The condition findings](docs/conditions_findings.md) compare recorded weather, surface, configuration, road setting and time patterns for tractor-involved and no-recorded-tractor events during 2012–2021. Full category tables retain unknown and Q/QQ other, both cohorts, fatal/injury strata, all-event denominators, and labelled named-only sensitivities. Conditional fatal-event shares are separate from composition shares and person deaths.

```bash
PYTHONPATH=src .venv/bin/python -m truck_collisions.analyze_conditions
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib \
  .venv/bin/python -m truck_collisions.report_conditions
```

Tables, figures and the full report are under `reports/conditions/`. The [executed notebook](notebooks/05_descriptive_conditions.ipynb) reruns the work; [independent review](docs/conditions_review.md) checks all seven statistical exports against direct event queries. These are descriptive collision patterns, not exposure-adjusted risks or causal effects.

## Configuration decomposition and current status

[Current project status](docs/project_status.md) maps the eight original questions, completed work, unresolved limitations and next priority. The [configuration decomposition](docs/configuration_decomposition.md) separates mix changes from changes within configurations, with [independent review](docs/decomposition_review.md) and an [executed notebook](notebooks/06_configuration_decomposition.ipynb).

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib \
  .venv/bin/python -m truck_collisions.decompose_configuration
```

Full-precision tables, allocation sensitivities and two PNG/SVG figures are regenerated under `reports/decomposition/`. The optional frozen source baseline is evaluated when present; its absence is recorded in the summary. Production data and preserved originals are not rewritten.
