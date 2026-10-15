# Person-level casualty validation

Build date: 2026-10-15. Evidence is generated under `data/derived/casualties/`; `validation.json` provides the exact UTC run time and SHA256 linkage. Method and rebuild commands: [casualty contract](casualty_contract.md).

## Scope and checks

The pipeline accounts for **212,788 input person/placeholder records** across **80,632 observed road-tractor collision events**, every calendar year 1999–2021. It reads all linked vehicles and road users. Every selected event has the same raw row count as the parent collision builder. No source record is silently dropped: known-key unit multiplicities plus unresolved/dummy multiplicities reproduce the input total.

| Finding | Count | Handling |
| --- | ---: | --- |
| Distinct normalized full records | 212,774 | Export every alternative with original multiplicity. |
| Exact repetitions beyond first occurrence | 14 | Collapse for known-key outcomes only; retain unknown multiplicity. |
| Identified recorded-person keys | 211,947 | Operational composite keys, not proof of distinct humans. |
| Keys with conflicting person attributes | 86 | Preserve alternatives; never choose the first, most severe or most common row. |
| Keys with conflicting injury severity | 43 | Publish consensus/possible coded-outcome scenarios. |
| Keys with ambiguous road-user assignment | 119 | Keep an exclusive ambiguous category, in all totals. |
| Unresolved identity raw rows | 133 | Preserve alternatives/multiplicity without assigning person IDs. |
| Dummy P_IDNN raw rows | 447 | Exclude from human casualties; no positively coded casualty rows. |
| Identified keys with unknown/unavailable severity evidence | 4,148 | Separately visible; no imputation into injury/death. |
| Identified keys with not-applicable severityN evidence | 13,207 | Separately visible, not treated as unknown human injury. |
| Unresolved-ID rows with unknown/unavailable severity | 49 | Separately visible. |
| Unresolved-ID rows with not-applicable severity | 1 | Separately visible. |

All fatal tractor events have a linked positively coded fatal-person record; no injury-severity event contains a fatal known-person key. Every event/person join and the known-key partition passed. This validates the representation of the extract, not its completeness relative to true national casualties or later official revisions.

The numerical key count should never be described as the number of people in these crashes. Numeric P_ID records include not-applicable injury codes and source identity defects. Conversely unreported/unavailable severity and unlinked identities can conceal actual harm.

## Source-record outcome scenarios

A low scenario counts known composite keys whose alternatives all support the outcome. A high scenario counts keys with any explicitly coded outcome and adds all positively coded unresolved-identity raw records. Unknown-identity rows contribute zero in the low scenario because they might overlap known people. Unknown severity is not reassigned. These are **conditional source-record resolution scenarios, not confidence intervals or true population bounds**. Known source-key identity can itself be wrong in complex events.

| Year | Observed deaths, low–high | Observed nonfatal injuries, low–high | Strict deaths, low–high | Strict nonfatal injuries, low–high |
| --- | ---: | ---: | ---: | ---: |
| 2012 | 233–233 | 4,337–4,337 | 233–233 | 4,337–4,337 |
| 2016 | 217–217 | 3,793–3,795 | 217–217 | 3,793–3,795 |
| 2019 | 214–214 | 3,785–3,786 | 214–214 | 3,785–3,786 |
| 2020 | 179–181 | 2,599–2,625 | 177–177 | 2,588–2,589 |
| 2021 | 191–191 | 2,828–2,844 | 191–191 | 2,821–2,822 |

Across the full 1999–2021 observed extract, coded outcomes are **6,393–6,395 deaths** and **105,971–106,034 nonfatal injuries** under these scenarios. These totals do not incorporate unknown severity or estimate missing casualties. Raw row sums can count conflicting representations more than once; they are diagnostic record counts, not a third validated person estimate. For example 2021 has 2,852 raw injury rows, versus the scenario 2,828–2,844 after known-key conflict handling.

The strict view applies the existing event-level exclusions only (11 events), preserving person uncertainty inside retained events. It is a sensitivity analysis, not a corrected national series. In 2020 two positively coded fatal unresolved-ID rows occur among structurally flagged events; therefore the strict death count is lower even than the observed identified-key low scenario.

## Road-user partition

The group assignment uses mutually consistent person role, position and recorded vehicle type. A separate ambiguous bucket prevents silently choosing between conflicting tractor/other/VRU evidence. Code01 covers light-duty cars, passenger vans, SUVs and pickups, so occupants of other motor vehicles cannot be described as car occupants alone.

For 2021 the observed death partition is: **30 tractor occupants, 129 occupants of other motor vehicles, 21 pedestrians, 3 cyclists, 6 motorcyclists, and 2 other/unknown**. There are no death-assignment-ambiguous keys that year. The 191 deaths refer to tractor-involved casualty events; they do not establish which vehicle caused the collision. Further trend interpretation and charts are in the separate casualty analysis outputs.

## External comparison remains partial

The tracked `data/reference/tractor_occupant_benchmarks.csv` contains two distinct official publication vintages. The generated `occupant_benchmark_comparison.csv` compares them separately with classified tractor-occupant scenarios. It does not substitute broad commercial-vehicle victims for tractor-specific harm.

| Year | Extract classified tractor deaths | TC 2021 traffic statistics | TC 2021 Parliament report | Extract classified tractor injuries | Parliament report injuries |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2017 | 43 | 43 | 43 | 1,117 | 1,118 |
| 2018 | 30 | 30 | 30 | 1,117 | 1,111 |
| 2019 | 32 | 31 | 30 | 1,003 | 948 |
| 2020 | 30 | 30 | 30 | 764 | 758 |
| 2021 | 30 | 28 | 29 | 812 | 806 |

Sources: [Transport Canada's 2021 traffic statistics](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2021/canadian-motor-vehicle-traffic-collision-statistics-2021), and [2021 commercial-vehicle safety report to Parliament](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament), Table12. Publication versions disagree with each other for some deaths. Classified occupant scenarios can also differ because of assignment ambiguity and source definitions. No specific explanation is established, and no record is changed to match a publication. These results must be presented as the observed public extract with qualifications, not a fully reconciled current official national series. The previously unresolved 2019 collision-count difference remains open.

### Occupant-position definition lead

A separate diagnostic found that some differences coincide with positive casualty rows coded `P_PSN=98` (outside the passenger compartment) or `NN` (position not applicable). In 2018, six tractor injury rows at position98 equal the injury difference. In 2020, five position98 and one positionNN injury row equal the six-injury difference; in 2021, three of each equal the six-injury difference. One 2021 tractor fatality at position98 equals the difference from the Parliament report, and one 2019 fatality at position98 equals the difference from the traffic-statistics report. These coincidences are a **candidate occupancy-definition explanation**, not evidence of the published filter or a resolution of the full discrepancy. The 2019 injury difference is much larger and official death vintages still disagree.

Position98 can explicitly describe a real passenger outside the compartment; NN conflicts with some positive casualty coding. Neither justifies silently deleting the recorded casualty. The pipeline retains linked tractor casualties in the broad tractor-occupant group. `positive_tractor_position_profile.csv` exposes raw positive source rows and identified keys with each position/outcome code for investigation. Those profile cells can overlap for conflicting known keys and are diagnostic, not additive estimates of people. Seek Transport Canada clarification of its precise published occupant definition.

## Independent verification

A separate reviewer reproduced 2019–2021 annual scenario endpoints and the seven road-user group endpoints directly from raw CSVs without importing this builder: **84 group/outcome/year endpoint cells matched**. An independent 2018 workbook calculation found 224 deaths and 3,977 identified injuries versus 3,978 raw injury rows, agreeing with these outputs. The reviewer separately checked dummy/unknown codes, injury severity, vehicle type and pedestrian identity definitions against the dictionary. Focused synthetic tests owned by the main project cover exact duplicates, conflicts, unknown identities, dummy codes, role contradictions and event links.

## Remaining limitations

- Unknown severity is not estimated; missing/unreported records are outside these scenarios.
- The NCDB dictionary's fatality definition is death immediately or within the reporting time limit; the public dictionary does not independently verify identical reporting practice in every jurisdiction/year.
- A valid numeric key can still duplicate a real human under a different vehicle ID, especially in complex events. Strict event sensitivity exposes some defects but cannot detect every such error.
- Group assignment uncertainty remains explicit and should not be excluded from denominators.
- External occupant benchmarks do not fully reconcile, and 2019 has the larger existing event-series discrepancy.
- National 2022–2025 event records are absent from the current project; no extrapolation fills them.
