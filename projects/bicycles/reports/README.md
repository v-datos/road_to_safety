# Bicycle report outputs

The first national edition covers 2010–2023, with linked-record details labeled 2010–2021. The canonical interactive report is in `../report/`; serve its `dist/` directory to read it.

`tables/` contains exact annual involvements, bicyclist casualties, linked collision counts, all-road-user harm, other-vehicle involvements, source/query comparisons and annual category profiles. `summary.json` records checks, coverage and fingerprints. `figures/` contains native PNG captures of the 15 report charts and separate visual QA sheets; these are captures of the report's actual renderer.

Generated outputs are ignored by Git. Data definitions, source metadata, implementation and durable validation findings are versioned. Reproduce numerical outputs with `python -m bicycle_collisions.analyze`; chart PNGs must be recaptured from the current verified report after changing its presentation.

## Portable HTML edition

Open `canada-bicycle-collisions-2010-2023.html` in a browser. This self-contained export embeds the reviewed data, charts, narrative and source inspection. It does not require the local preview server or a separate JSON file. The canonical editable source remains `../report/`. Regenerate with the Data app `build --separate-data` and `export-offline` commands after report changes.
