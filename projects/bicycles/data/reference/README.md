# Bicycle references

| File | Scope and acquisition |
| --- | --- |
| `ncdb_online_bicycles_2010_2023.csv` | 4,536 normalized visible table cells; dataset/year/category/measure/count; totals retained for validation |
| `ncdb_online_bicycles_2010_2023.metadata.json` | Selected capture files and hashes, query filters, timestamps, cube vintage, checks and limitations |
| `published_bicyclist_fatalities_2020_2023.csv` | Four revised bicyclist fatality values transcribed from the 2024 national publication; 2020–2023 reference years only |

The online person and vehicle contexts differ for 2020–2022. Demographics reconcile to the direct bicyclist person series; time/conditions reconcile to the bicycle vehicle series. Do not sum Total rows with categories or combine different counting units. Native age/hour ranges are disjoint, and unknown categories are included.

These are public reference aggregates. The underlying linked record selection is pinned separately in `../sources.json`. The newer publication benchmark and online cube are separate releases; the 2020 death-count difference remains visible.
