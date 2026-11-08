# Person and casualty dataset contract

## Scope and source lineage

This preparation uses **all records of every observed road-tractor collision event**, not only the tractor's records. It covers every year 1999–2021 and reads the exact **nine selected inputs** in `data/sources.json`: inherited physical 1999–2017 CSV selected only for 1999–2013; annual English XLSX for 2014–2019; English 2020 CSV; French 2021 CSV. The physical legacy file is preserved unchanged; `selected_years` prevents overlap with its annual replacements. The current event and record totals are reported in [casualty validation](casualty_validation.md), not frozen in this contract. The source files are immutable. Hash verification and canonical header/code normalization reuse `truck_collisions.build`; the annual Excel workbooks and French CP1252 2021 CSV are handled explicitly. `data/derived/casualties/source_manifest.json` carries original URLs, source coverage, sizes, SHA256 and available acquisition dates. `validation.json` links the person pipeline, dictionary parent tractor-event Parquet and tracked occupant benchmark reference by SHA256. Inherited historical acquisition timing remains unknown.

The current source covers public-road fatal and injury collisions, not property-damage-only events. Tractor code `08` means road tractor **with or without semitrailer**. These records do not supply 2022–2025, mileage, fault, or severity detail beyond no injury/injury/fatality. The 2019 XLSX substantially reduces the earlier collision benchmark discrepancy but leaves a two-injury-collision difference; this is not forced into agreement. The 2013 injury benchmark difference also remains.

## Identity and duplicate rules

The NCDB dictionary gives `P_ID=01–99` as person sequence, `NN` as not applicable (for example a dummy parked-vehicle person), and `UU` as unknown. `V_ID=01–98` are vehicle sequence IDs; `99` is the dummy vehicle assigned to pedestrians, **not a dummy human**. `V_ID=UU` means a person cannot be linked to their vehicle. Nonstandard `00`, `*`, and other values are preserved, never guessed.

An **identified recorded-person key** is `(source_id,C_YEAR,C_CASE,V_ID,P_ID)` with both IDs numeric `01–99`. Including V_ID99 allows identified pedestrians. All event/person joins include the release `source_id`; the same case, vehicle and person numbers across releases do not establish the same physical collision or human. No cross-release identity matching or record splicing is performed. This is an operational source-key assumption, not proof of unique real people: corrupted multi-vehicle events can repeat or misassign identities across different vehicle IDs. Even a numeric key can have injury code `N` and represent not-applicable information. Consequently `identified_person_keys` is a key count, not an unqualified population count.

- Exact normalized repetitions on an identified key are counted once for person outcomes; original multiplicity remains in the alternatives and unit diagnostics.
- Multiple different records on that key are retained as alternatives. No first/last row, most severe value, majority vote, or demographic matching chooses the supposedly correct record.
- Unknown/invalid identity records retain every distinct normalized alternative and its **raw record multiplicity**. They are not merged into a person and receive no synthetic identity. Identical unknown records can be duplicates or multiple people; they can also overlap an identified record of the same person.
- `P_ID=NN` records are dummy records and contribute no human casualty. Positive injury/fatality coding on a dummy would be an explicit anomaly, not silently promoted to a human. No such positive dummy rows occur in this build.
- `P_ISEV=N` is separately not applicable, even for numeric keys. It is not treated as unknown severity or a potential fatality. `U`, `X`, blank and unexpected codes are retained as unknown/unavailable, without imputing outcomes.

## Outcomes and interpretation of scenarios

`P_ISEV=1` no injury, `2` nonfatal injury, `3` fatality. Death and nonfatal injury are separate measures. A given known key contributes to `deaths_min=1` only when **every alternative** is fatal; to `deaths_max=1` when **any** alternative is fatal. Injury and combined casualty fields follow the same rule. Thus a `1|2` key contributes injury 0–1; a `2|3` key would contribute combined casualty exactly one, but death/injury each 0–1. Death and injury maxima need not be jointly attainable and must not be added to infer combined casualties.

For each outcome/year/group/subset:

- `*_record_scenario_low` = identified-key consensus count (`identified_*_min`). Unknown identities add zero, because they may overlap known people.
- `*_record_scenario_high` = identified-key possible coded count (`identified_*_max`) + every raw unresolved-identity row explicitly coded with that outcome. This scenario allows unresolved rows to represent additional separate people; it does not assert they do.
- Unknown severity is reported separately and never reassigned to an outcome.

These are **source-record resolution scenarios**, conditional on the known-key identity assumption and observed outcome codes. They are **not bounds on actual national deaths/injuries, confidence intervals, or estimates of missing harm**. Missing or incorrectly reported records and severity coding can lie outside them. The low scenario is not a guaranteed population minimum. Complex-event source corruption can affect even identified keys.

## Road-user assignment

Each alternative uses concordant `P_USER`, `P_PSN`, `V_ID`, and all observed types on its known vehicle ID:

| Group | Evidence |
| --- | --- |
| `tractor_occupant` | Vehicle type08 without contradictory role evidence. |
| `other_motor_vehicle_occupant` | Type01/05/06/07/09/10/11/18/19/20/21/23 without contradictory role evidence. Type01 includes cars, passenger vans, SUVs and light pickups; this is not a car-only category. |
| `pedestrian` | P_USER3, P_PSN99 or V_ID99, with no conflicting vehicle/role evidence. The dummy vehicle does not exclude the person. |
| `cyclist` | P_USER4 or type17, with no conflicting evidence. |
| `motorcyclist` | P_USER5 or type14, with no conflicting evidence. |
| `other_or_unknown` | Insufficient category evidence or other road users (including off-road vehicles/type16 and snowmobiles/type22). |
| `ambiguous` | Contradictory role/type evidence, conflicting non-VRU vehicle assignments, or different group assignments across person alternatives. |

P_USER1/2 combined with explicit pedestrian/cyclist/motorcyclist evidence is marked ambiguous. Positive VRU role evidence can classify a row when vehicle type is unknown. Unknown vehicle type alone cannot assign a motor-vehicle user to a tractor or another vehicle. A vehicle coded08 andUU yields uncertain occupant assignment and is retained as ambiguous. Conflicts that are irrelevant to an otherwise consistent explicit VRU assignment need not eliminate that assignment. No category receives simultaneous copies of an ambiguous person.

These seven groups form an exclusive partition of records/keys, **not a fully resolved partition of true people**. The ambiguous and unknown buckets stay in all totals and denominators. Marginal low/high outcome scenarios can differ in which known keys contribute; coherent scenario shares may be reported, but are not probability intervals or mathematical extrema across all possible assignments. The vulnerable-road-user total, when used, means pedestrian + cyclist + motorcyclist and must be explicitly labeled.

## Outputs

All outputs are in `data/derived/casualties/`:

- `person_units.parquet`: one identified recorded-person key per row, parent-event strict flag, severity alternatives, outcome min/max, record multiplicity/variant counts, unknown/not-applicable severity and conflict flags. No invented corrected demographic attributes.
- `record_alternatives.parquet`: every distinct full normalized source row with original codes, `record_multiplicity`, `identity_status`, assigned group and event sensitivity flag. This is the audit authority for conflicts and unknown identities.
- `unresolved_and_dummy_records.parquet`: alternatives with identity status `unresolved_identity` or `dummy`, retaining multiplicity.
- `conflicting_person_keys.parquet`: identified keys with person-attribute, severity or group-assignment conflict.
- `annual_group_counts.csv`/`.parquet`: one row for each year × observed/strict subset × seven groups (322 rows), including identified key counts, coded-outcome scenarios, unresolved positive record counts, unknown and not-applicable severity counts.
- `annual_counts.csv`: the same metrics summed over the exclusive group partition (46 rows). Combined casualty identified min/max cannot be reconstructed by adding death/injury maxima for mixed-severity conflicts.
- `quality_by_year.csv`, `code_profile.csv`, `validation.json`, `source_manifest.json`: quality/provenance evidence. Profile rows are source alternatives weighted by original multiplicity, not people.
- `positive_tractor_position_profile.csv`: diagnostic raw positive type08 rows and known keys with each position/outcome code. Conflicting keys can appear in multiple cells. Positions98/NN are retained as observed rather than silently excluded; apparent benchmark differences matching these positions remain a research lead.
- `occupant_benchmark_comparison.csv`: separate published tractor-occupant fatalities and injury benchmarks compared with the **classified tractor-occupant** scenarios. Assignment ambiguity and source vintage can prevent equality. Broader commercial-vehicle victim counts are not used as tractor-event benchmarks.

`subset=observed` retains every positively recorded tractor event. `strict` uses the parent `is_analysis_candidate` flag and excludes the structurally/tractor-type-flagged events listed in the current parent validation outputs. It does not additionally discard unknown identities, ambiguous categories, unknown severity, or person conflicts. These uncertainties are represented by the scenario fields. Strict is a sensitivity view, not a corrected national series; excluded complex events may have unusual harm.

## Rebuild and checks

```bash
PYTHONPATH=src .venv/bin/python -m truck_collisions.build_casualties
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The build requires the parent tractor-event Parquet from `truck_collisions.build`. It verifies pinned raw hashes, every parent event's original row count, uniqueness of selected event keys, exact raw-row accounting across known keys and unknown/dummy alternatives, year/group coverage, fatal-person/event severity consistency and presence of a positively coded human fatal record in every fatal tractor event. Passing these checks validates this source representation; it does not reconcile official source versions or establish completeness of unreported casualties.

The testable helper `resolve_person_records(records, events)` accepts canonically normalized string-coded rows and parent event dictionaries; it returns identified units, source alternatives, unresolved/dummy alternatives and quality metrics. Normalization happens in the orchestrating `build_dataset` function, not this helper.
