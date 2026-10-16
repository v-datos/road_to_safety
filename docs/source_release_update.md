# Validated NCDB source-version repair

Completed **2026-10-15**, before weather or configuration analysis. This repair changes the selected source releases and rebuilds their downstream products. No event, vehicle or person count was manually adjusted to match a publication. No emails or other contact were made.

## Completion of the six steps

| Step | Delivered | Verification |
| --- | --- | --- |
| 1. Preserve the baseline | Git commit `c7baeb3`, original source selection, raw originals, and a frozen output/notebook/report snapshot. | Snapshot manifest contains 68 files with sizes and SHA256 hashes; baseline is not overwritten by rebuilds. |
| 2. Validate the 2019 workbook | Separate collision and casualty candidate builds, independent workbook normalization/group aggregation, source checksums and audit report. | 196 fatal and 2,579 injury tractor events; person identity, multiplicity and severity checks pass. |
| 3. Audit source releases | Catalogue inventory for all resources covering 1999–2021; normalized content comparisons for annual 2012–2017; separate validation of changed 2014–2017 files. | 2012–2013 content is identical to legacy; 2014–2017 changes pass collision/person gates. Earlier alternatives remain catalogued but unvalidated. |
| 4. Promote and rebuild | Active nine-source selection; full event/person pipelines, both analyses, tables, six figures and three executed notebooks. | Final outputs match validated candidates for five replaced years and the frozen baseline for 18 unchanged years. |
| 5. Separate benchmarks | Catalogue distinguishes unique collisions, vehicle involvements, occupant casualties, all-person tractor-event harm and national/provincial context. | Existing collision/occupant reference values and schemas are preserved. Incompatible newer aggregates do not enter the production event series. |
| 6. Document recent-year availability | Source/year/grain register for public national 2022–2025 records and separate verified aggregate/provincial sources. | No public annual national NCDB record file for those years was located. Missing releases are not described as nonexistent internal data. |

## Baseline and rollback evidence

- Original source selection: [baseline_c7baeb3.json](../data/source_releases/baseline_c7baeb3.json).
- Snapshot checksums: [baseline_output_manifest.json](../data/source_releases/baseline_output_manifest.json).
- Local frozen snapshot: `data/derived/baselines/pre_source_revision_20261015/`, including the original outputs, reports, executed notebooks and Git archive.
- Source-selection and restoration instructions: [source release README](../data/source_releases/README.md).

The original CSV and inherited archive remain unchanged. The baseline is evidence of the earlier analysis, not a competing current national estimate. Restoring earlier outputs requires the matching source selection and code version; a newer pipeline using old inputs need not produce byte-identical artifacts.

## Active source selection

| Selected years | Physical source | Reason |
| --- | --- | --- |
| 1999–2013 | Pinned inherited 1999–2017 CSV, with explicit `selected_years`. | Retain known baseline content. Annual 2012–2013 normalized records are identical; alternatives before 2012 have not been content-validated. |
| 2014–2017 | Separate official annual XLSX releases. | Documented resource provenance and substantive record changes, validated using complete collision/person candidate builds. |
| 2018 | Existing official XLSX. | Retained existing validated source. |
| 2019 | Alternate official XLSX, resource `91d586f9-fb72-4eac-b1f5-d9b95830c877`. | Distinct official resource, internally coherent data and validated changed contents; improved reconciliation supports selection without forcing a match. |
| 2020 | Existing official English CSV. | Retained existing validated source. |
| 2021 | Existing official French CSV. | Retained usable official source; English catalogue entry has no URL. |

`data/sources.json` is the production selection; [selected_20261015.json](../data/source_releases/selected_20261015.json) records this repair's selection. Every physical source retains its original checksum and coverage. The complete physical year coverage is checked before filtering selected legacy years, and overlapping selected years are rejected.

Calendar year and case number identify an event only within the selected release. Cross-release keys also require source identity. Matching case numbers across exports are not used to infer additions, removals, changed people or vehicle responsibility. Neither metadata dates nor aggregate agreement establish that a file is officially final, authoritative or exactly the extract used for a publication.

## What changed

### Tractor-involved collision counts

| Year | Previous fatal / injury / total | Selected fatal / injury / total | Published fatal / injury |
| --- | ---: | ---: | ---: |
| 2014 | 211 / 3,216 / 3,427 | 211 / 3,216 / 3,427 | 211 / 3,216 |
| 2015 | 194 / 2,880 / 3,074 | 194 / 2,881 / 3,075 | 194 / 2,881 |
| 2016 | 193 / 2,816 / 3,009 | 193 / 2,817 / 3,010 | 193 / 2,817 |
| 2017 | 214 / 2,962 / 3,176 | 216 / 2,962 / 3,178 | 216 / 2,962 |
| 2019 | 192 / 2,679 / 2,871 | 196 / 2,579 / 2,775 | 196 / 2,581 |

The 2014 all-vehicle event/person inputs change even though its tractor-event total does not. It is therefore important to replace validated complete releases and rebuild comparison populations, rather than patching selected annual totals.

### All-person harm in tractor-involved events

| Year | Previous deaths | Selected deaths | Previous nonfatal injury scenarios | Selected injury scenarios |
| --- | ---: | ---: | ---: | ---: |
| 2014 | 247 | 247 | 4,472–4,475 | 4,472–4,475 |
| 2015 | 227 | 227 | 4,060–4,061 | 4,046–4,047 |
| 2016 | 217 | 217 | 3,793–3,795 | 3,794–3,796 |
| 2017 | 240 | 242 | 4,066–4,069 | 4,068–4,071 |
| 2019 | 214 | 222 | 3,785–3,786 | 3,665–3,666 |

These are the documented source-record resolution scenarios, not confidence intervals or bounds on actual casualties. Unknown severity remains unallocated; no person identity is invented. The classified 2019 tractor-occupant counts are 31 deaths and 953 injuries. Their remaining publication differences are retained separately from all-person harm.

### Updated conclusions

The 2012 and 2021 endpoints are unchanged: tractor casualty collisions fall **3,300 → 2,276**, recorded deaths **233 → 191**, and injury scenarios **4,337 → 2,828–2,844**. The overall endpoint conclusion survives the repair.

Interior-year and pooled results change. The available 2016–2021 tractor-event comparison is now **3,010 → 2,276 (−24.39%)**. The pooled 2012–2021 other-motor-vehicle occupant death share is **1,581 / 2,206 = 71.67%**, replacing the earlier CSV-based 71.58%. The pre-2020 2016–2019 fatal-event comparison is **193 → 196 (+1.55%)**; the earlier 193 → 192 decline is superseded. None of these comparisons establishes exposure-adjusted risk or causation.

The complete aggregate change audit compares **6,026 annual/group metric cells**, with **217 changed cells**, confined to 2014–2017 and 2019. Its CSV includes unchanged cells so the scope is inspectable: [annual_metric_changes.csv](../reports/source_revision/annual_metric_changes.csv), with source/input hashes in [summary.json](../reports/source_revision/summary.json). It compares independently computed aggregates and never joins case/person IDs between releases.

## Final validation

Production covers all 23 years, 1999–2021:

- **7,729,886** selected input rows and **2,949,846** unique all-vehicle casualty events.
- **80,540** observed tractor events; **80,529** strict sensitivity events.
- **212,532** raw person/placeholder rows in tractor events, represented by **211,699** identified source person keys plus retained alternatives and unresolved/dummy records. Key counts are not proof of distinct physical humans.
- **133** unresolved identity rows, **438** dummy rows, **43** severity-conflicted keys and **120** ambiguous group keys remain explicit. No dummy row claims a positive casualty outcome.
- Event keys and person keys are unique at their documented grains; person multiplicities partition input rows exactly. No event/person row-count mismatch, injury-event fatality conflict or fatal event without a coded fatal record was found.

Independent review passed **15 event checks and 21 person checks**, including complete output-row comparisons for all unchanged and replacement years, pinned source hashes, identical event/person source manifests, selected-year coverage, and code/parent/dictionary/benchmark fingerprints. **All 16 tests pass. All three notebooks execute successfully: 23 code cells, zero errors.** Both analyses and all six scientific figures were regenerated and visually checked.

The remaining collision benchmark gaps are **2013: 3,148 versus 3,150 injury events**, and **2019: 2,579 versus 2,581**. Their causes remain unproven. Three 2020 events retain contradictory vehicle-count fields, and the strict sensitivity still excludes 11 tractor events. Published tractor-occupant totals also remain only partly reconciled. Structural validation and aggregate agreement do not establish complete national ascertainment or true person identity.

## Newer sources and remaining gaps

The updated public-source review verifies the [2024 national traffic collision report](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024), published 2026-10-15: 2,050 deaths and 130,551 injuries across all vehicle classes. Its revised historical totals remain a separate publication vintage. S11 tractor vehicle involvements, provincial tractor vehicle counts, and broader national totals do not supply missing unique national tractor events or all-person casualties.

No public annual national NCDB record release for 2022–2025 was located in the reviewed catalogue. This is an availability finding, not proof those years do not exist internally or are obtainable by request. [The availability register and scoped sources](data_availability.md) document what is verified, missing or blocked. No outreach is planned.

## Reproduce and next step

```bash
PYTHONPATH=src .venv/bin/python -m truck_collisions.download
PYTHONPATH=src .venv/bin/python -m truck_collisions.build
PYTHONPATH=src .venv/bin/python -m truck_collisions.build_casualties
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.analyze_trends
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.analyze_casualties
PYTHONPATH=src .venv/bin/python -m truck_collisions.compare_source_releases
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The comparison command requires the preserved local baseline. Notebook execution instructions are in [notebooks/README.md](../notebooks/README.md). Candidate validation can be repeated with `python -m truck_collisions.validate_source_revision`; historical candidate source choices and evidence are in [the release audit](source_release_audit.md).

**Steps 1–6 are complete.** At the source-repair phase, condition comparisons had not started. The subsequent audit, comparisons and decomposition are now complete; see [current status](project_status.md). Person scenarios and unknown categories remain necessary, and exposure compatibility is still required before interpreting counts as driving risk.
