# Person-level casualty validation

Final promoted-source build: **2026-10-15T16:39:15.243056+00:00**. This document describes the nine-source production rebuild following the 2014–2017 and 2019 source changes. Machine-readable evidence is `data/derived/casualties/validation.json`; it pins pipeline, dictionary, parent tractor-event dataset and occupant benchmark reference by SHA-256. Parent event dataset hash: `c4541b558e3f81fb25f15e02a14abb8ec39e4f35d56ba551330c0730a1e5a495`. Method and rebuild commands: [casualty contract](casualty_contract.md).

## Scope and checks

The pipeline accounts for **212,532 input person/placeholder records** across **80,540 observed road-tractor collision events**, every calendar year 1999–2021. It reads all records for all linked vehicles and road users, not only tractor records. Nine immutable inputs match `data/sources.json`: physical inherited 1999–2017 CSV selected for 1999–2013, annual English 2014–2019 XLSX, English 2020 CSV and French 2021 CSV. Source manifests preserve physical and selected coverage separately.

Every selected event has the same raw row count as the parent collision builder. Known-key unit multiplicities plus unresolved/dummy alternative multiplicities reproduce the input total. Event/person links include the release `source_id`; case numbers are not matched across source vintages.

| Finding | Count | Handling |
| --- | ---: | --- |
| Distinct normalized full records | 212,518 | Export every alternative with original multiplicity. |
| Exact repetitions beyond first occurrence | 14 | Collapse for known-key outcomes only; retain unknown multiplicity. |
| Identified recorded-person keys | 211,699 | Operational composite keys, not proof of distinct humans. |
| Keys with conflicting person attributes | 87 | Preserve alternatives; do not choose first, most severe or most common. |
| Keys with conflicting injury severity | 43 | Publish consensus/possible coded-outcome scenarios. |
| Keys with ambiguous road-user assignment | 120 | Keep an exclusive ambiguous category in all totals. |
| Unresolved identity raw rows | 133 | Preserve alternatives/multiplicity without invented person IDs. |
| Dummy P_IDNN raw rows | 438 | Exclude from human casualties; zero positively coded casualty rows. |
| Identified keys with unknown/unavailable severity evidence | 4,147 | Separately visible; no imputation into injury/death. |
| Identified keys with not-applicable severityN evidence | 13,206 | Separately visible, not unknown human injury. |
| Unresolved-ID rows with unknown/unavailable severity | 49 | Separately visible. |
| Unresolved-ID rows with not-applicable severity | 1 | Separately visible. |

All fatal tractor events have a linked positively coded human fatal record; no injury-severity event contains a fatal identified key. Event/person row mismatches, invalid event-severity person keys and fatal events without a fatal record are all **zero**. The known-key/raw-row partition and complete year/group output checks passed.

These checks validate the representation of selected releases, not completeness relative to true national casualties or later revisions. The numerical key count is not an unqualified count of people: numeric P_ID records include not-applicable injury codes and source identity defects; unreported severity and unresolved identities can conceal harm.

## Source-record outcome scenarios

`P_ISEV=1` means **uninjured**, `2` means nonfatal injury, and `3` means fatality. Code1 is never added to injury totals. A low scenario counts identified composite keys whose alternatives all support the outcome. A high scenario counts keys with any explicit outcome and adds all positively coded unresolved-identity raw records. Unknown identities add zero in the low scenario because they can overlap known people. Unknown severity is not reassigned; N remains separately not applicable.

These are **conditional source-record resolution scenarios, not confidence intervals or true population bounds**. The known-key identity assumption can itself fail in complex events. Death and injury marginal maxima need not be jointly attainable; they cannot be added to reconstruct combined-casualty maxima when severity alternatives conflict.

| Year | Observed deaths, low–high | Observed nonfatal injuries, low–high | Strict deaths, low–high | Strict nonfatal injuries, low–high |
| --- | ---: | ---: | ---: | ---: |
| 2012 | 233–233 | 4,337–4,337 | 233–233 | 4,337–4,337 |
| 2014 | 247–247 | 4,472–4,475 | 247–247 | 4,470–4,472 |
| 2015 | 227–227 | 4,046–4,047 | 227–227 | 4,046–4,047 |
| 2016 | 217–217 | 3,794–3,796 | 217–217 | 3,794–3,796 |
| 2017 | 242–242 | 4,068–4,071 | 242–242 | 4,066–4,068 |
| 2018 | 224–224 | 3,977–3,978 | 224–224 | 3,977–3,978 |
| 2019 | 222–222 | 3,665–3,666 | 222–222 | 3,665–3,666 |
| 2020 | 179–181 | 2,599–2,625 | 177–177 | 2,588–2,589 |
| 2021 | 191–191 | 2,828–2,844 | 191–191 | 2,821–2,822 |

The complete 23-year table is `data/derived/casualties/annual_counts.csv`. Across the full observed 1999–2021 extract, coded outcomes are **6,403–6,405 deaths** and **105,840–105,903 nonfatal injuries**. These totals do not estimate unknown severity or missing casualties. Raw row sums are diagnostic record counts, not a third validated person estimate. For example, 2021 still has 2,852 raw injury rows, versus 2,828–2,844 after known-key conflict handling.

Strict applies the existing 11 event exclusions only, retaining person uncertainty inside retained events. It is a sensitivity view, not a corrected national series. In 2020, positively coded fatal unresolved-ID rows occur among flagged events; strict deaths can therefore fall below the observed identified-key consensus count.

## Road-user partition

The seven groups use mutually consistent person role, position and recorded vehicle type; ambiguous and unknown assignments remain in denominators. Code01 includes cars, passenger vans, SUVs and pickups, so other-motor-vehicle occupants are not a car-only category. Pedestrians, cyclists and motorcyclists are separate groups; any combined vulnerable-road-user total must state those components.

For 2021 the observed death partition remains **30 tractor occupants, 129 other motor vehicle occupants, 21 pedestrians, 3 cyclists, 6 motorcyclists, 2 other/unknown and zero ambiguous death assignments**. These 191 deaths occurred in tractor-involved casualty events. They do not establish fault or risk per kilometre. See the separately rebuilt casualty analysis outputs for temporal comparisons.

## External comparison remains partial

`data/reference/tractor_occupant_benchmarks.csv` retains two official publication vintages. The generated `occupant_benchmark_comparison.csv` compares each separately with classified tractor-occupant scenarios. It does not substitute broader commercial-vehicle victims for all-person harm in tractor events.

| Year | Extract classified tractor deaths | TC 2021 traffic statistics | TC 2021 Parliament report | Extract classified tractor injuries | Parliament report injuries |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2017 | 43 | 43 | 43 | 1,118 | 1,118 |
| 2018 | 30 | 30 | 30 | 1,117 | 1,111 |
| 2019 | 31 | 31 | 30 | 953 | 948 |
| 2020 | 30 | 30 | 30 | 764 | 758 |
| 2021 | 30 | 28 | 29 | 812 | 806 |

Sources: [Transport Canada's 2021 traffic statistics](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2021/canadian-motor-vehicle-traffic-collision-statistics-2021) and [2021 commercial-vehicle safety report to Parliament](https://tc.canada.ca/en/road-transportation/motor-vehicle-safety/motor-carriers-commercial-vehicles-drivers/commercial-vehicle-safety-canada-2021-annual-report-parliament), Table12. Publications disagree for some deaths. Source vintage, assignment ambiguity and operational occupant definitions may prevent equality; the precise causes remain unproven. No record is changed to match either publication.

The annual 2017 replacement now matches the 1,118 published tractor-occupant injuries. The 2019 XLSX yields 31 classified tractor deaths and 953 injuries, versus 32 and 1,003 in the earlier CSV baseline. It matches traffic-statistics fatalities but remains one death and five injuries above the Parliament series. These are occupant comparisons, distinct from the residual two **collision** gap in 2019. The 2013 event gap also remains. See [source revision validation](source_revision_validation.md) and [collision validation](dataset_validation.md).

### Occupant-position definition lead

`positive_tractor_position_profile.csv` retains diagnostic positive type08 source rows and known keys by position/outcome. Some benchmark differences coincide with position98 (outside passenger compartment) or NN (not applicable): 2018 has six position98 injury rows; 2019 has five such injury rows and one fatal row; 2020 has five position98 and one NN injury row; 2021 has three of each injury row and one position98 fatal row. These coincidences are a **candidate definition explanation**, not proof of the publication's filter. As a counterexample to a universal exclusion rule, 2017 includes one position98 injury row while the broad classified injury count already matches the publication.

Position98 can describe a real passenger outside the compartment; positive outcomes with NN are also retained as source evidence. Neither permits silently deleting a casualty. Profile cells can overlap for conflicting keys and are diagnostic, not additive person estimates. Keep the uncertainty until additional public documentation establishes an applicable definition.

## Independent verification and source changes

Separate candidate runs used the unchanged collision/person identity rules before promotion. The 2014–2017 candidate person run accounted for 33,409 rows across 12,690 events with zero event/person consistency failures. The 2019 XLSX candidate was independently checked, including normalized records and road-user outcome cells; its evidence is recorded in [source revision validation](source_revision_validation.md).

The final independent review passed **15 event and 21 person checks**. Complete event/person Parquet rows for all 18 unchanged years matched the preserved baseline, while all five promoted years matched their separately validated candidates. Event and person source manifests matched all nine active source selections. Pinned source, pipeline, parent-event, dictionary and benchmark hashes verified; all 23 years and unique keys were present; record multiplicities accounted for all 212,532 rows; all event/person consistency failures were zero. No review findings remained. The full **16-test suite** and **23 notebook code cells** (8 validation, 6 collision-trend and 9 casualty-analysis cells) passed.

Earlier independent work reproduced 84 annual/group endpoint cells for the **previous 2019 CSV plus unchanged 2020–2021 sources**. That is baseline evidence, not independent verification of the replacement 2019 XLSX. The earlier 2018 workbook check found 224 deaths and 3,977 consensus identified injuries versus 3,978 raw injury rows; those source inputs remain unchanged. Focused synthetic tests exercise duplicates, conflicts, unknown identities, dummy records, contradictory roles, event links and selected-year restrictions.

## Remaining limitations

- Unknown severity is not estimated; missing/unreported records are outside the scenarios.
- The dictionary's fatality definition is death immediately or within the reporting time limit; identical reporting practice in every jurisdiction/year is not independently established.
- A valid numeric key can duplicate a real human under a different vehicle ID. Strict event sensitivity cannot detect every such defect.
- Assignment uncertainty remains explicit; ambiguous/unknown records are retained in denominators.
- External occupant benchmarks remain partly unreconciled. Residual event differences are two injury collisions in each of 2013 and 2019; neither is manually repaired.
- National 2022–2025 event records remain absent from the selected project data. [The availability register](data_availability.md) records separately scoped aggregates and provincial sources without filling national microdata gaps.

Overall status: **`validated_source_record_scenarios_external_reconciliation_partial`**. The baseline and previous source files remain preserved separately; this timestamp identifies the final promoted-source casualty run.
