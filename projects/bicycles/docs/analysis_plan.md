# National bicycle collision report · 2010–2023

The first edition is implemented. The intended national reference period is **2010–2023**, following the requested order: **trend → severity → who was harmed → other vehicles → time and conditions**.

The question is: How have police-reported fatal and injury collisions involving bicycles changed in Canada, and who is harmed in them?

## Evidence coverage

| Section | Counting unit | Supported years | Source |
| --- | --- | --- | --- |
| Trend | Bicycle vehicle involvements | 2010–2023 | NCDB Online, Vehicle Type=Bicycle |
| Unique collision trend | Distinct selected event keys | 2010–2021 | Public linked records |
| Severity | Bicyclist deaths/nonfatal injuries; fatal-collision involvement share separately | 2010–2023 | Online person and vehicle queries at their respective grains |
| Who was harmed | Bicyclist age/gender profiles | 2010–2023 | Online Road User Class=Bicyclist |
| All-road-user harm | Identified people in bicycle-involved events, resolved outcomes | 2010–2021 | Public linked records |
| Other vehicles | Distinct events containing each known-ID co-involved vehicle type | 2010–2021 | Public linked records; overlapping categories |
| Time and conditions | Bicycle involvements by month, weekday, three-hour period, weather, surface, road setting and lighting | 2010–2023 | Online Vehicle Type=Bicycle |

The source does not supply every bicycle fall or unreported injury, an e-bike identifier, cycling exposure, or province/location in the reviewed record schema. Do not infer risk, fault, causal effects or infrastructure effectiveness from these counts.

## Completed sequence and checks

1. Acquired independent copies of nine pinned record sources and the official dictionary. Verified their hashes, headers, physical reference years and non-overlapping selection of 2010–2021. Preserved the live online table cells and the query selections for all 14 years.
2. Built separate event, known-vehicle and known-person tables, retaining all road users in bicycle-involved events. Preserved unknown identities, duplicate-row evidence and conflicting outcomes.
3. Reconciled every selected online category partition to its corresponding annual series. Person and vehicle query differences for 2020–2022 remain explicit. Compared annual record outputs with the online cube and checked the newer publication's revised 2020–2023 bicyclist deaths.
4. Exported inspectable CSV tables and created the interactive report using reviewed aggregates. Kept 2022–2023 linked-record gaps visible; no interpolation or substitution was performed.
5. Ran seven focused tests plus direct distinct-key and road-user additivity checks. Rendered the report and captured its native charts for visual inspection. See [validation](validation.md) for the scope of those checks and unresolved differences.

The report application in `../report/` is the canonical narrative surface. Source rows and definitions are available from each evidence component. `../reports/tables/` contains exact computational exports; `../reports/summary.json` pins analysis inputs and code.

## Boundaries for interpretation and future revisions

Road-user composition and seasonality describe reported harm and collision activity. Exposure-adjusted risk and causal claims are outside this edition. Vehicle presence in the same event does not establish which vehicle struck a cyclist. The light-duty category combines cars, passenger vans, utility vehicles and light pickups.

Keep unknown categories in denominators. Native age groups have unequal widths, including 0–14 and 80+; raw age-group counts do not rank per-age or per-trip risk. No serious-injury split or helmet-effect estimate is derived from the public person severity field.

A later edition can extend linked details only after a verified public record release or another explicitly scoped source is acquired. A newer official release must be recorded as a new vintage; numerical disagreement alone is not grounds to overwrite old records or aggregate values.
