# Bicycle tests

Run from `projects/bicycles/`:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

`test_grains.py` exercises duplicate source rows, multiple bicycles in one event, retention of other road users, source/year-scoped identities, unresolved/dummy identities and conflicting role/outcome alternatives. It uses synthetic fixtures.

`test_online.py` rejects incomplete periods and non-additive categories, then checks the versioned public aggregate series against the correct person/vehicle annual contexts. It deliberately preserves their observed 2020 difference.

`test_corridor_and_notebooks.py` verifies the Toronto Centreline + AADT cyclist corridor exposure tables (`toronto_cyclist_corridor_exposure_by_class.csv`, `toronto_top_cyclist_ksi_corridors.csv`), the 4-panel synthesis figure (`cyclist_corridor_exposure_synthesis.png`), national co-involved vehicle lethality multipliers, and that all three companion notebooks in `notebooks/` parse as valid `nbformat` v4 JSON with executed outputs on every code cell.

The real-data build and analysis also run direct coverage, uniqueness, event replication and road-user additivity checks. See `docs/validation.md` for what those checks establish and leave unresolved.
