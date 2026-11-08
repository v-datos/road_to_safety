# Independent validation of the alternate 2019 source

> **Promotion adopted.** This candidate validation justified the 2019 source replacement. Production now also includes validated annual 2014–2017 replacements; see [the complete repair record](source_release_update.md). Counts below compare the frozen CSV baseline with the independently built 2019 XLSX candidate.

Validated 2026-10-15. This is an audit of the candidate release, not a manual adjustment to published totals. No external contact was made.

## Reproducible candidate and protected comparison

The candidate is the official English workbook [resource 91d586f9-fb72-4eac-b1f5-d9b95830c877](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/91d586f9-fb72-4eac-b1f5-d9b95830c877/download/y_2019_en.xlsx), worksheet `in`, SHA256 `8285d8d734a1835ccd4bc72617ee11419d6e16c3dcd6effb8b5bdbe51fc43d0b`. Catalogue metadata record creation on 2023-06-06 and content modification on 2023-06-06. These dates establish a different published resource, not proof that a particular statistical report used these exact records.

`truck_collisions.validate_source_revision` runs the existing event builder and complete casualty builder into `data/derived/candidates/2019_xlsx/`, independently normalizes the workbook in Python, selects every record belonging to a tractor-involved event, and passes those records to the tested person resolver. Its separately aggregated group outcomes must agree with the complete casualty build. This corroborates loading, selection, and aggregation; the person-resolution methodology is deliberately shared rather than independently reimplemented.

Comparison uses the frozen CSV baseline at `data/derived/baselines/pre_source_revision_20261015/data/derived/casualties/`. It never joins case IDs between releases. Source ID is included in event and person identities. Outputs include candidate manifests, raw-record alternatives, person units, annual group comparisons, occupant benchmark comparisons, and validation summaries. Production source selection is managed separately.

```bash
PYTHONPATH=src .venv/bin/python -m truck_collisions.validate_source_revision
```

## Collision and source checks

| Measure | Earlier CSV baseline | Candidate workbook |
| --- | ---: | ---: |
| Input rows | 272,301 | 269,328 |
| All casualty collision keys | 105,782 | 104,630 |
| Tractor-involved collision keys | 2,871 | 2,775 |
| Tractor-involved fatal collisions | 192 | 196 |
| Tractor-involved injury collisions | 2,679 | 2,579 |
| Tractor strict-view exclusions | 0 | 0 |

The candidate contains 1,620 fatal and 103,010 injury collisions across all vehicle classes. All event keys are unique after event aggregation, none has invalid case/year, and all collision attributes are consistent within a key. Its 196 fatal tractor events contain 239 known tractor vehicle involvements; those are distinct counting units. Every fatal tractor event contains a positively coded human fatality; no injury event contains a fatal record.

The published tractor benchmark is 196 fatal and 2,581 injury collisions: the candidate exactly matches fatal events but remains two injury events below the benchmark. The workbook therefore substantially explains the earlier source-version discrepancy without fully resolving it. The difference is preserved, not filled or assigned a speculative cause.

## All-person casualty results

Every person record from each selected tractor event is retained, including other vehicles and vulnerable road users. No casualty filter is applied before selecting complete events.

| Exclusive road-user group | CSV deaths | Workbook deaths | CSV nonfatal injuries | Workbook nonfatal injuries |
| --- | ---: | ---: | ---: | ---: |
| Tractor occupants | 32 | 31 | 1,003 | 953 |
| Other motor vehicle occupants | 147 | 154 | 2,656 | 2,587 |
| Pedestrians | 22 | 21 | 44 | 47 |
| Cyclists | 4 | 5 | 22 | 21 |
| Motorcyclists | 7 | 9 | 31 | 29 |
| Other or unknown | 2 | 2 | 27 | 26 |
| Ambiguous assignment | 0 | 0 | 2–3 | 2–3 |
| **All groups** | **214** | **222** | **3,785–3,786** | **3,665–3,666** |

These are conditional source-record resolution scenarios, not confidence intervals or bounds on true population casualties. The same known-key assumptions and unresolved identity rules apply to both releases. Unknown severity is never converted into no injury, injury, or death. Within 2019, observed and strict results are identical because no tractor event fails the strict event criteria.

The source replacement changes all-person deaths by +8 and coded nonfatal injury scenarios by −120, illustrating why adjusting collision totals alone would be incorrect. These are aggregate differences between releases, not identified additions or deletions of individual people.

## Candidate person-quality checks

| Check within tractor events | Candidate result |
| --- | ---: |
| Original input person-record rows | 7,694 |
| Distinct normalized alternatives | 7,693 |
| Exact repetitions beyond first | 1 |
| Identified source person keys | 7,674 |
| Keys with conflicting personal attributes | 1 |
| Keys with conflicting severity | 1 |
| Keys with ambiguous group assignment | 3 |
| Unresolved-identity raw rows | 6 |
| Dummy person rows | 13 |
| Dummy rows coded with injury or death | 0 |
| Identified keys with unknown/unavailable severity | 82 |
| Unresolved-identity rows with unknown/unavailable severity | 6 |
| Identified keys containing not-applicable severity | 534 |
| Missing or extra raw rows when partitioned by identity status | 0 |

All six unresolved identity rows have unknown severity and add no positively coded casualty to the upper record scenario. The one severity conflict produces the remaining one-injury scenario difference. Numeric source keys with not-applicable severity are retained as keys, not automatically interpreted as known real people. Four tractor events have reported-versus-observed vehicle count disagreements; these remain warnings. One event has a vehicle type conflict that does not involve a tractor key, hence no strict tractor exclusion. Dummy records and unknown people are never assigned invented identities.

## Occupant benchmarks remain separate and partly unresolved

The candidate's 31 tractor-occupant deaths match the 2019 figure in the [2021 annual traffic statistics](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2021/canadian-motor-vehicle-traffic-collision-statistics-2021). They are one above the 30 reported in Table 12 of the [2021 commercial vehicle annual report](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament). Candidate tractor-occupant injuries are 953, five above that report's 948.

There is one tractor fatality and five injuries coded at position 98 in the workbook. Those numbers equal the residual occupant differences with the commercial vehicle report. This is a diagnostic lead, not proof that the publication excluded position 98, and no position-based exclusion is applied. Position codes and exact source alternatives remain available for further definition checks.

## Recommendation

The candidate passes the existing structural and casualty invariants and is supported as the preferred 2019 release by its distinct official resource provenance, internally coherent data, and substantially improved external reconciliation. Benchmark proximity is corroborating evidence, not the sole selection criterion. Promote the complete source release and rebuild downstream products; retain the former CSV and its frozen outputs as the previous release. Keep the residual two-collision and occupant benchmark differences explicitly unresolved. Do not use vehicle involvements or other national aggregates to fabricate collision records for missing years.
