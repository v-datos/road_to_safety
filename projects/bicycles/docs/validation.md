# First-edition validation · 2010–2023

Validated October 17, 2026. This describes checks that ran and known limitations; it does not certify complete reporting or causal validity.

## Acquired evidence and grains

Nine pinned public record files were copied byte-for-byte into the bicycle project's raw directory, independently of the truck project's derived datasets. SHA256, the 23-column English/French schema, physical file coverage and exactly one selected release for each year 2010–2021 were checked. The official dictionary was copied and hash-verified separately.

The selected bicycle cohort contains **155,984 input rows**, **155,969 distinct normalized rows** and **68,687 unique events**. Event, known-vehicle and known-person output keys are unique. A direct count of distinct bicycle-event keys in retained records equals the event table. Road-user group counts add to all identified person keys.

## Identity and classification issues

| Diagnostic | Count |
| --- | ---: |
| Invalid event-key rows in the selected cohort | 0 |
| Events with conflicting collision-level attributes | 0 |
| Known person keys with conflicting injury outcomes | 3 |
| Known person keys with conflicting road-user codes | 5 |
| Known people with disagreeing bicycle-type / bicyclist-role signals | 1 |
| Distinct unresolved or dummy-identity rows | 306 |
| Positive-casualty rows among those unresolved/dummy records | 1 |
| Events with a bicyclist code but no recorded bicycle | 0 |

Resolved casualties exclude unresolved identities and outcomes. No missing people or outcomes were imputed. Unknown/dummy row counts are not estimates of the number of unidentified real people. The linked harm table is conditional on the selected public record releases and resolution rules.

## Online completeness and query contexts

Selected online tables cover every year 2010–2023. All **462 dataset/year/measure partitions** sum to their totals and reconcile with the appropriate annual person or vehicle query. There are 4,536 normalized cells. Age and hour default ranges initially omitted unknown values; complete captures explicitly include them. Rejected exploratory captures remain separate.

The direct Road User Class=Bicyclist query and its demographic profiles reconcile. Vehicle Type=Bicycle queries and their time/condition profiles also reconcile. These contexts yield different casualties for 2020–2022:

| Year | Vehicle-context injuries | Person-context injuries | Vehicle-context deaths | Person-context deaths |
| --- | ---: | ---: | ---: | ---: |
| 2020 | 3,440 | 3,837 | 50 | 54 |
| 2021 | 4,059 | 4,432 | 39 | 42 |
| 2022 | 3,928 | 4,281 | 48 | 51 |

No explanation for the difference has been established. The primary casualty trend uses the explicit bicyclist road-user query throughout 2010–2023; the involvement/time/condition series uses the vehicle query throughout. Neither context is silently substituted into the other.

Native CSV export reached the download page but timed out. Acquisition uses the visible DOM cells, archived before normalization. Filters, cube vintage, capture timestamps and file hashes are in `data/reference/ncdb_online_bicycles_2010_2023.metadata.json`.

## External and release comparisons

The [2024 national publication](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024) marks its historical road-user-class figures revised. Its 2020–2023 bicyclist deaths are **53, 42, 51 and 46**. The online person series is **54, 42, 51 and 46**. The 2020 one-death difference is retained, and the online 712-death period sum is labeled as belonging to its own cube vintage. No 2024 observation enters this report's 2010–2023 scope.

Linked public records differ from online aggregates beyond the few conflicted records. For example, resolved bicyclist deaths for 2021 are 47 in the selected record release, versus 42 in the online person query. This is not explained or repaired by changing source rows. Complete annual vehicle/person comparisons are exported in `reports/tables/record_online_comparison.csv` and shown in the report.

## Code and rendered checks

Seven focused tests passed: multiple bicycles and duplicate people in one event; identities across years/releases; dummy and unknown identities; conflicting person role/outcome alternatives; incomplete online periods; category partition failures; and the archived complete profiles at their respective grains.

Direct data checks additionally cover selected/physical year coverage, uniqueness at each output grain, event cohort replication and road-user additivity. These are structural and arithmetic checks, not evidence of complete collision reporting.

The desktop report was rendered through its local HTTP preview. All 15 chart components were captured natively and visually inspected for plotted marks, axes and labels. Table pagination was verified through 2023, and source metadata was inspected through the page's read-only context interface. The interactive source drawer could not be exercised through the current browser controls. No browser errors were recorded. Narrow-viewport inspection is not available through the current browser controls and is not claimed. The report has no global period filters that could silently change its fixed 2010–2023 scope.

## Remaining limits

- Linked national event records stop at 2021; unique events, all-person harm and co-involved vehicles cannot be extended to 2022–2023 from the online aggregates.
- Source/query differences remain visible; neither source is called fully reconciled with the other.
- E-bikes, province/location, a serious-injury split in the reviewed person schema, cycling exposure and causal effects are outside the supported evidence.
- Age bands have different widths, and unknown demographic values remain material. Category counts do not estimate risk per trip.

## Portable HTML edition — October 17, 2026

The editorial design revision preserves the app ID, all reviewed data and all seven chapters. The verified split build was exported through the supported offline exporter, then copied to `reports/canada-bicycle-collisions-2010-2023.html`. Browser inspection of that exact single-file export confirmed all 15 chart components mounted, the first trend chart and tooltip rendered, and no horizontal overflow at the inspected desktop width. No browser console errors were reported. The summary and 2010–2021 linked-record coverage qualification remained visible. The section menu opened; automated link activation could not be completed through the browser locator, so chapter-jump behavior and narrow-screen rendering were not verified in this revision.
