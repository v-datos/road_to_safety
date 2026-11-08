# Bicycle tests

Run from `projects/bicycles/`:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

`test_grains.py` exercises duplicate source rows, multiple bicycles in one event, retention of other road users, source/year-scoped identities, unresolved/dummy identities and conflicting role/outcome alternatives. It uses synthetic fixtures.

`test_online.py` rejects incomplete periods and non-additive categories, then checks the versioned public aggregate series against the correct person/vehicle annual contexts. It deliberately preserves their observed 2020 difference.

The real-data build and analysis also run direct coverage, uniqueness, event replication and road-user additivity checks. See `docs/validation.md` for what those checks establish and leave unresolved.
