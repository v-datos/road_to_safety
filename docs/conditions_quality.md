# Missingness and coding consistency before condition comparisons

Completed **2026-10-15**, using the rebuilt 1999–2021 event release after source repair commit `e50bc6a`. This is a field-quality assessment, not an analysis of weather effects, crash causes or exposure-adjusted risk. The source and production tables are unchanged.

The subsequent [descriptive condition comparisons](conditions_findings.md) are now complete and carry forward these quality qualifications. This document records the preceding readiness assessment.

## Decision

**Proceed with descriptive weather, surface, configuration and time comparisons for 2012–2021, retaining unknown and residual categories explicitly.** The dictionary-domain and availability checks found no malformed codes in those condition fields. Readiness is conditional: one supplied dictionary does not prove identical reporting or classification practice across jurisdictions and years.

Use the 1999–2021 series for context. A substantial 1999–2000 crash-configuration distribution change needs qualification before using 1999 in a pooled configuration analysis. It is outside the primary 2012–2021 comparison window; no recoding is justified by frequency changes alone.

## Scope, grain and denominators

Inputs are `data/derived/ncdb/collisions.parquet`, its field-conflict export, source manifest and validation evidence. They contain **2,949,846 unique casualty-collision events**, including **80,540 observed tractor-involved events**. Each field is counted once per event; person rows and vehicle involvements never multiply the denominator.

The audit covers all eleven collision attributes: month, weekday, hour, severity, reported vehicle count, crash configuration, road configuration, weather, surface, alignment and traffic control. Event identifiers and source selection retain the earlier build's validated identity rules. Person identities/outcomes retain the separate [casualty contract](casualty_contract.md); vehicle/person covariate readiness is not established by this condition-field audit.

Results are partitioned by:

- Every calendar year, 1999–2021, with source identity preserved.
- All events, tractor-involved events and the complementary no-recorded-tractor population. The last group includes heavy trucks, other vehicles and uncertain types; it is not car-only.
- Observed and existing strict sensitivity subsets. Strict is an alternative cohort, not a corrected series.
- All casualty events, fatal events and injury events, each with its own denominator.

The code exports **4,554 field/partition profiles** and **1,656 joint-field coverage profiles**. Counts for each status exhaust their event denominator. Every field has the same denominator within a partition; all joint retained counts lie between zero and the relevant event total.

## Dictionary-aware missingness

The tracked [codebook](../data/reference/collision_codebook.json) transcribes English pages 1–6 of the supplied NCDB dictionary and pins its SHA256. It distinguishes:

| Status | Interpretation and treatment |
| --- | --- |
| Defined code | Explicit dictionary category. Midnight `00` is a valid hour; zero is not a valid month or vehicle count. |
| Top coded | `C_VEHS=99` means 99 or more; it is not an exact vehicle count. |
| Residual other | `Q`/`QQ` is valid recorded information outside the listed categories; preserve separately from unknown. Defined categories such as `C_CONF=06`, other single-vehicle configuration, remain defined codes. |
| Unknown | Field-specific `U`/`UU`. No imputation. |
| Not provided | Field-specific `X`/`XX`, meaning the jurisdiction does not provide the field. No such codes are observed in these event fields; their absence does not prove complete reporting. |
| Not applicable | Kept distinct by the classifier; the audited collision-field dictionary domains contain no N/NN code. |
| Null/blank | Absent value without a recorded field conflict. |
| Conflict null | Null introduced by the event builder because source rows disagree on that field. |
| Unexpected | Value outside the field-specific dictionary domain, including incorrect width. Preserve and flag; do not guess a replacement. |

“Unavailable” in the tables combines unknown, not provided, not applicable, null/blank, conflict null and unexpected. Q/QQ is excluded from that measure. “Named complete” means all selected fields have defined or top-coded dictionary values, excluding Q/QQ. The joint bundles contain no vehicle-count field, so top coding does not affect their retained counts.

## Findings

### 1. Recent condition fields are usable with explicit residual categories

The following denominator is **2,276 observed tractor events in 2021**:

| Field | Unknown/unavailable/invalid | Residual Q/QQ other | Interpretation |
| --- | ---: | ---: | --- |
| Weather | 0.97% | 0.22% | Strong recorded coverage; retain unknown and other. |
| Road surface | 0.35% | 4.79% | Low unknownness, but material uncategorized surface information. |
| Crash configuration | 1.54% | 5.93% | Broad comparisons possible; other is not evidence of a particular manoeuvre. |
| Road configuration | 5.32% | 3.95% | Largest recent unknown fraction among these fields; show explicit unavailable group. |
| Hour | 0.62% | 0.00% | Time-of-day available; it does not measure darkness. |
| Month | 0.00% | 0.00% | No unavailable event values in 2021 tractor records. |
| Weekday | 0.00% | 0.00% | No unavailable event values in 2021 tractor records. |
| Road alignment | 2.64% | 0.00% | Distinguishes geometry, not urban/rural road class. |
| Traffic control | 2.59% | 2.20% | Use recorded control categories; these are not speed-limit measurements. |

Severity has no out-of-domain or unavailable event codes. The only unexpected value among all eleven fields is the previously documented **one `C_VEHS=**` event in 2020**. Three additional 2020 vehicle-count values are conflict nulls, corresponding exactly to the existing field-conflict export. These defects remain visible; they do not require recoding weather or configuration.

**Risk: medium for detailed residual-category interpretation; low for condition-field syntax.** There is no reason to discard whole collisions because a single condition is unknown. Excluding them can change the analysed collision population.

![Field availability and residual categories](../reports/conditions_quality/field_availability.png)

### 2. Complete-case restriction would materially select the sample

| Required bundle | 2012 named complete | 2021 named complete | 2021 available if Q/QQ retained |
| --- | ---: | ---: | ---: |
| Weather + surface | 3,095 / 3,300 (93.79%) | 2,138 / 2,276 (93.94%) | 2,251 / 2,276 (98.90%) |
| Crash + road configuration | 2,763 / 3,300 (83.73%) | 1,918 / 2,276 (84.27%) | 2,123 / 2,276 (93.28%) |
| Weather + surface + both configurations + hour | 2,586 / 3,300 (78.36%) | 1,793 / 2,276 (78.78%) | 2,086 / 2,276 (91.65%) |
| All nine planned condition/time fields | 2,470 / 3,300 (74.85%) | 1,725 / 2,276 (75.79%) | 2,009 / 2,276 (88.27%) |

Requiring all nine named fields would remove **551 of 2,276 events (24.21%)** in 2021. Even retaining Q/QQ while excluding unknown/unavailable values removes 267 events (11.73%). For that nine-field restriction, named completeness is 74.56% among fatal events versus 75.89% among injury events. These are availability differences, not proof that missingness is random or ignorable.

**Risk: high for an unqualified multivariable complete-case analysis.** Start with field-specific descriptive tables using all-event denominators, including unknown and other rows. A conditional known-value table can be a separately labelled sensitivity; do not silently use a single nine-field complete-case sample for every question. No missing-value imputation is supported by this audit.

### 3. Availability differs between tractor and comparison events

In 2021, unavailable crash configuration is **1.54% among tractor events versus 4.02% among no-recorded-tractor events**. For surface it is 0.35% versus 1.07%, but surface Q/QQ is higher among tractor events: **4.79% versus 2.82%**. Weather unknown/unavailable is 0.97% versus 1.59%.

**Risk: medium for group comparisons.** Differences in recorded condition shares could partly reflect unequal information availability. Report both populations' denominators and unknown/other fractions by year and severity. Do not pool away these differences or call the comparison population cars.

### 4. Early configuration distributions need qualification

Annual review flags use **absolute unavailable-rate changes of at least 2 percentage points**, or **total variation at least 0.15** across the full code distribution, including special codes. These are transparent diagnostic thresholds, not significance tests or proof of a reporting change.

Only the 1999–2000 transition flags for tractors:

- Crash configuration has total variation **0.218**. Code01, hitting a moving object, changes from **418/4,186 (9.99%) to 15/4,258 (0.35%)**, while several other configuration shares move substantially. The broad no-recorded-tractor population also changes markedly, with total variation 0.288.
- Road-configuration unavailability changes from **354/4,186 (8.46%) to 211/4,258 (4.96%)**, a decrease of 3.50 percentage points.

No tractor transition during **2012–2021** triggers these predeclared thresholds. That does not establish invariant coding or rule out smaller changes, jurisdictional composition changes or offsetting errors. Source IDs, code presence and all unrounded changes are exported. A newly observed or absent valid code alone does not demonstrate a dictionary change; rare real collision categories may appear intermittently.

**Risk: high for unqualified configuration pooling that includes 1999; qualified use for 2012–2021.** Keep 1999 as context and show it separately in long-history configuration work until its comparability can be established from public evidence. No evidence here justifies relabelling or deleting 1999 records.

## Limits of the next analysis

- The public schema has **no measured lighting, latitude/location, jurisdiction, recorded vehicle manoeuvre or fault fields**. Hour cannot be relabelled darkness. Crash configuration cannot establish which vehicle acted or caused the collision.
- `C_RCFG` is road configuration and `C_RALN` is alignment. Neither supplies a complete urban/rural, highway/local-road or speed-limit classification.
- A single reference dictionary and valid syntax do not certify identical historical or jurisdictional coding semantics. Missingness rates and distributions cannot isolate reporting changes from real collision mix or exposure changes.
- Weather/surface categories describe recorded collisions. Their shares cannot estimate collision risk under those conditions without corresponding exposure.
- Any later person-harm comparison must preserve the casualty scenarios and group uncertainty; this event audit does not solve missing person outcomes.

## Deliverables and reproduction

- [Executed quality notebook](../notebooks/04_conditions_quality.ipynb), with independent direct-event checks.
- [Annual field availability](../reports/conditions_quality/annual_field_quality.csv).
- [Annual codes and denominators](../reports/conditions_quality/annual_code_counts.csv) and [observed code presence](../reports/conditions_quality/code_presence.csv).
- [Joint-field coverage](../reports/conditions_quality/joint_field_coverage.csv).
- [Tractor/comparator quality gaps](../reports/conditions_quality/cohort_quality_gaps.csv).
- [Distribution changes and flags](../reports/conditions_quality/annual_distribution_changes.csv).
- [Hashes, invariants and limitations](../reports/conditions_quality/summary.json).

Run `PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.audit_conditions` after the event build. The codebook, dictionary, selected source manifest, input event/conflict files and audit module are fingerprinted. The notebook recomputes primary field-year status counts from direct event queries, checks cohort/severity arithmetic, and verifies selected joint coverage independently. No production dataset is rewritten.

**Completed successors:** [descriptive comparisons](conditions_findings.md) and [configuration decomposition](configuration_decomposition.md) retain separate unknown/other categories, explicit denominators and strict/period sensitivities. The next priority is [exposure compatibility](project_status.md).
