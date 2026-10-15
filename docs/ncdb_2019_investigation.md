# Investigation of the 2019 NCDB benchmark difference

Verified 2026-10-14. This investigation distinguishes checks on the supplied records from agreement with published statistics. Passing structural checks does not establish that the public extract reproduces the latest national totals.

## Fresh source compared with local file

The official [2019 English CSV](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/1e2a6aa0-c35f-4736-984a-71f2eac1c1dc/download/2019_dataset_en.csv) was acquired as `data/raw/ncdb/2019_dataset_en.csv`, SHA256 `d1d4fcc176b387281dadbf02b9e32890174e7e9e07f05961c54e5e7c4487a87c`, 17,398,658 bytes. A Python `csv.DictReader` comparison found exact equality of row multisets with `Collisions/test_2019_dataset_en.csv`: neither file contains rows absent from the other, including row multiplicity. Both contain 272,301 rows.

Selecting every `(C_YEAR,C_CASE)` with at least one `V_TYPE` numerically equal to 8, then counting each collision once, gives:

| Measure | Public CSV | Published benchmark | Difference: CSV minus benchmark |
| --- | ---: | ---: | ---: |
| All fatal collisions | 1,623 | 1,623 | 0 |
| All injury collisions | 104,159 | 104,169 | -10 |
| Road-tractor fatal collisions | 192 | 196 | -4 |
| Road-tractor injury collisions | 2,679 | 2,581 | +98 |
| Road-tractor casualty collisions | 2,871 | 2,777 | +94 |

The all-vehicle benchmark is the [2019 annual statistical report](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2019/canadian-motor-vehicle-traffic-collision-statistics-2019). The tractor benchmark is Table 1 of [Commercial vehicle collisions in Canada, 2012–2021](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021).

## What the investigation establishes

The tractor difference persists in the freshly downloaded official extract. Local editing, truncation, duplicate person rows, or counting more than one tractor per collision do not explain it. Every collision field is constant within each public CSV collision key. No conflicting vehicle type involves code 08. All code 08 rows have a valid numeric vehicle sequence 01–98. The selection is therefore reproducible from this extract.

Source vintage is a plausible contributor, but the specific explanation remains unresolved. Official totals do change: the later [2024 addendum Table S6](https://tdih-cdit.tc.canada.ca/en/addendum-tables/2024/table-s6-road-casualty-collisions-fatalities-and-injuries-rates-10000-mvr-0) reports 104,640 total casualty collisions and 1,756 fatalities for 2019, whereas the original annual report has 105,792 casualty collisions and 1,762 fatalities. The fresh public extract has 105,782 casualty collisions. A current download does not imply an updated underlying historical extract.

The public [data dictionary](https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/21eb7966-38da-4814-a80e-521bce6c4c27/download/data_dictionary.pdf) defines 08 as a road tractor with or without a semitrailer. An earlier [Transport Canada commercial vehicle report](https://tc.canada.ca/sites/default/files/2022-01/commercial-vehicle-safety-canada-2012-2018.pdf), footnote 4, uses the same definition for tractor-trailers. There is no verified evidence here that excluding tractors without trailers would reconcile the difference; the public extract cannot identify trailer attachment separately.

Transport Canada's [road safety program evaluation](https://tc.canada.ca/en/corporate-services/transparency/corporate-management-reporting/evaluation-reports/evaluation-road-safety-programs) documents reporting delays and the use of estimates. That explains why different official vintages can exist, but does not prove the cause of this particular difference. Seek clarification from `NCDB-BNDC@tc.gc.ca`, the contact on the [NCDB FAQ](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-5-0). Do not adjust the extracted records to force agreement.

## Integrity findings and recommended handling

| Check | Entire 2019 file | Road-tractor collision subset | Handling |
| --- | ---: | ---: | --- |
| Unique collision keys | 105,782 | 2,871 | Use `(C_YEAR,C_CASE)` across years; preserve source case ID as text. |
| Inconsistent collision fields within a key | 0 | 0 | Fail or quarantine conflicting event attributes rather than selecting an arbitrary row. |
| Missing or nonnumeric case/year | 0 | 0 | Reject missing keys; check year against source coverage. |
| Exact duplicate rows beyond first occurrence | 401 | 1 | They do not affect unique collision selection; retain counts in audit. Do not assume every identical row with an unknown person ID is a duplicated human. |
| Rows beyond first per `(year,case,V_ID,P_ID)` | 493 | 2 | This composite key is not universally a unique person key. |
| Person keys with nonidentical rows | 85 | 1 | Do not silently merge records or sum casualties as though every key were reliable. |
| Conflicting keys with valid vehicle ID and numeric person ID | 79 | 1 | Flag before building person-level outputs. |
| Vehicle keys with inconsistent `V_TYPE` | 48 | 1 | Conflicts are known type vs unknown, or QQ vs unknown; none includes 08. |
| Fatal collisions without any fatal person record (`P_ISEV=3`) | 0 | 0 | Check all involved vehicles and road users, not only tractor occupants. |
| Injury collisions containing a fatal person record | 0 | 0 | Severity consistency passes for 2019. |
| Known `C_VEHS` differing from observed valid vehicle count | Present | 7 | Flag as a warning; unmatched people or absent vehicle records can prevent exact reconstruction. |

The one conflicting person key in a tractor-involved collision is `(2019,2711833,1,1)`. It has two nonidentical records for an occupant of another vehicle, with differing age, vehicle type, vehicle year, injury severity, and road-user type. One record is uninjured and one injured. Its parent collision has 70 reported vehicles. This ambiguity does not change whether a tractor is present or the event severity, but it prevents an unqualified person-level casualty sum for the event.

Dictionary-aware rules:

- Count observed vehicles only for `V_ID` 01–98. Code 99 is a pedestrian dummy vehicle; `UU` means a person could not be linked to a vehicle. Compare this observed count with numeric `C_VEHS` and preserve unknown codes separately. The seven tractor-event discrepancies are five cases with reported two vehicles but one observed, one with reported five but four observed, and one with reported three but two observed.
- `P_ID=NN` can represent a dummy person for a parked vehicle; `UU` is unknown. Neither is a stable person identifier. Preserve records and ambiguity flags rather than manufacturing individual identities. Even numeric person keys can conflict, as above.
- Build the collision table from collision attributes and the presence of tractor code 08 anywhere in the complete event. Do not discard other involved rows before validating the event or reviewing victims.
- Keep the source file, hash, coverage, code normalization, selection rule, and external benchmark status with the outputs. Mark 2019 as structurally checked and externally unreconciled. The extracted count can be used to describe this public release, but should not be presented as a reconciled latest official national total.

No person-level casualty totals are validated by this investigation. Those need a separate treatment of dummy records, unknown IDs, exact duplicates, conflicting identities, and injury coding.

## Independent checks of newly acquired years

A separate streaming Python calculation used `csv.DictReader` for CSVs and `openpyxl` read-only iteration of worksheet `in` for the 2018 workbook. It did not call the dataset builder or its SQL. Each `(year,case)` retained its collision severity, whether any row contained `V_TYPE=8` or `08`, and whether any row contained `P_ISEV=3`. The French 2021 CSV was decoded with CP1252 and its year, case, and severity headers translated.

| Year | Input rows | All unique casualty collisions | Road-tractor fatal collisions | Road-tractor injury collisions | Road-tractor total | TC Table 1 agreement |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2018 | 285,382 | 111,334 | 190 | 2,800 | 2,990 | Exact |
| 2020 | 198,745 | 79,990 | 158 | 1,964 | 2,122 | Exact |
| 2021 | 204,428 | 83,590 | 169 | 2,107 | 2,276 | Exact |

For each of these three sources, there were zero conflicting severities within a collision, zero fatal collisions without a fatal person record, and zero injury collisions with a fatal person record. Checks considered all involved road users. These results corroborate the counting method and establish that the unresolved 2019 difference is not a necessary consequence of converting person records to unique tractor-involved collisions.

## Review of strict-view exclusions

The first full builder output was independently inspected. Its observed tractor totals for 2018 (2,990), 2020 (2,122), and 2021 (2,276) agree with the streaming calculation above. A separate strict view excludes 11 observed tractor events across the full series: one in 2013, one in 2014, two in 2017, six in 2020, and one in 2021. Those exclusions reduce the 2020 strict count to 2,116 and the 2021 strict count to 2,275; they should not be interpreted as failures to reproduce the published observed counts.

The strict exclusions are defensible as an explicitly conservative view for analyses requiring consistent vehicle coding. They do not establish that the excluded collisions did not involve tractors. Five of the 11 events have tractor-related vehicle keys with `08|UU` (positive tractor evidence plus an unknown record); six have a tractor key mixed with another numeric vehicle type. Some events also contain additional unconflicted tractor vehicles. Keep every observed tractor collision in an audit/sensitivity dataset, and distinguish observed counts from strict counts in trend and benchmark outputs. Removing all conflicted events can disproportionately remove large multi-vehicle crashes, whose repeated or inconsistent vehicle IDs deserve separate investigation.

Three 2020 collision keys have inconsistent `C_VEHS`: `000000002850492` (`01|04`), `000000002849895` (`01|04`), and `000000002851746` (`02|16`). Only the last is tractor-involved. Raw CSV inspection confirms that all other collision attributes, including severity, agree within each of the three events. Thus these are conflicts in the recorded number of vehicles, not conflicting event severities.

For tractor event `000000002851746`, all 23 input rows are distinct. Two records report two vehicles, unknown vehicle types and largely unknown person attributes; 21 records report 16 vehicles. Vehicle IDs 01 and 02 have `UU|08`; vehicle IDs 03–08 independently contain unconflicted code 08. The event therefore has strong positive tractor evidence despite its inconsistent vehicle count. Repeated demographic and vehicle attributes across several vehicle IDs further mean that casualty or distinct-vehicle inferences require care. It is appropriate to retain this event in the observed national series and quarantine it from the strict attribute-consistent view. There is no defensible basis in the extract alone to select two or 16 as the corrected count or to reconstruct individual casualties.

Another excluded 2020 event, `000000002811894`, has `C_VEHS=**` and vehicle IDs including `*` and `00`, in addition to conflicting numeric vehicle types. Those are unexpected codes relative to the dictionary and should remain visible in the code-domain audit. They are not ordinary missing codes that can safely be normalized to a guessed vehicle count or identity.
