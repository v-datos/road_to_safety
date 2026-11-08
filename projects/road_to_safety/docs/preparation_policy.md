# Collision preparation and exception policy

Effective October 17, 2026. This policy defines event construction and lineage before exploration or modeling. It operationalizes the [source audit](data_quality_assessment.md) and the [modeling contract](modeling_contract.md), preserving exceptions rather than silently resolving identities or labels.

## Inputs and provenance

Read only annual resources marked selected in [sources.json](../data/sources.json), one resource per selected year, with matching archived-file SHA-256. The accepted baseline is 23 selected annual resources, 1999–2021. The older 2019 comparator and aggregate publications stay separate. Preserve raw originals; never rewrite source bytes to align versions or benchmark totals. Validate exact schema, French-to-canonical header mapping, expected year, record width and file fingerprints before writing the prepared release.

Retain the source resource UUID, original-file hash/path, sheet or CSV context, expected year, source row number and preparation-code/contract fingerprints. A source row number includes header offset: data begin at row 2. It is a source position, not a person ID. A manifest and immutable original permit reconstruction of every event's supporting segments; exception evidence records original rows and reason(s). The event table also records source multiplicity and diagnostics. These fields serve lineage only.

Trim derived string values and strip leading zeros only from digit-only tokens, matching the audit. Keep canonical `C_*` codes as strings; hour `00` becomes `0`. Never normalize nonnumeric sentinels together or mutate archived rows. Missing/null input values require an explicit blank state during consistency checking so nulls cannot disappear from distinct-value counts.

## Keys and conservation

The candidate key is `(source_id, C_YEAR, C_CASE)`. Accept a digit-only positive case ID and a manifest-matching selected year. The source UUID separates releases; case IDs are not linked across releases. Source-level schema, manifest-integrity or observed-year mismatches stop the build because input interpretation is untrustworthy. Other record-level invalid event keys are quarantined with raw evidence rather than assigned fabricated IDs or silently dropped; the remaining valid-key rows can be grouped. Unexpected or malformed years are never reassigned to the expected year.

Produce one row for each distinct valid candidate key. This grouping is an explicit working identity convention: the dictionary does not formally define `C_CASE`. Do not claim record linkage has proven true-event identity across vintages.

Every selected source segment must be accounted for by:

1. A valid-key collision group, retaining source-row multiplicity; or
2. Invalid-key quarantine, with reason and lineage.

Therefore `input segments = sum(event source-row counts) + invalid-key segments`. Do not subtract exact duplicates a second time. Exception categories can overlap and exception evidence can include rows that remain members of valid events; adding exception-reason counts is not a conservation equation. Report event totals and segment totals separately. The baseline audit reports 7,729,886 selected segments, 2,949,846 candidate collisions, 47,793 fatal events and 2,902,053 injury events, with no invalid event keys, severity conflicts or conflicts in the eight initial predictors. Three 2020 events have conflicting reported vehicle counts, which are null and flagged in the prepared dataset. These are reconciliation expectations for the pinned inputs, not permanent thresholds for future releases.

## Duplicate and conflict decisions

| Finding | Preparation decision | Consequence for condition-only severity eligibility |
| --- | --- | --- |
| Exact repeated raw row | Keep original multiplicity, duplicate diagnostics and exception evidence; group its event once. Do not claim copies establish multiple people. | No automatic event exclusion. |
| Repeated candidate person key with identical attributes | Preserve supporting rows and duplicate-key evidence; do not inflate a unique-person count or discard source rows. | No automatic event exclusion. |
| Repeated candidate person key with disagreeing outcomes/attributes | Flag and retain all evidence; no first-row, majority, worst-injury or synthetic-person resolution. This phase does not produce a trustworthy person model table. | No automatic event exclusion; person outcomes are not initial features. |
| Numeric vehicle key with conflicting type/year | Retain conflict evidence; do not select one version or build trusted vehicle aggregates from it. | No automatic event exclusion. |
| Sole agreed `C_SEV=1` / `2` | Retain source target and map `is_fatal=1` / `0`; `severity_eligible=true`. | Eligible target. |
| Sole blank, `U`, `X`, star or other invalid target code | Retain original canonical target, nullable binary target and evidence; set `severity_eligible=false`. | Retained, ineligible. |
| Disagreeing target values, including valid plus blank/unknown | Set event `C_SEV` and `is_fatal` null, set `C_SEV_conflict`, retain observed values/source rows, and set eligibility false. | Retained, ineligible. |
| Disagreeing condition or other collision attribute | Set that event attribute null and `<FIELD>_conflict=true`; retain all original conflicting observations. No arbitrary selection. | Does not alter target eligibility; later model-stage handling required. |
| Consistent blank or invalid condition code | Preserve token and separate missing/domain status; never coerce to a safe code or ordinary category. | Does not alter target eligibility; later model-stage handling required. |

An exception can trigger multiple reasons. A conflict is disagreement among all observed canonical values, including blank; a known value does not automatically override an unknown. Agreement after documented numeric-padding normalization is not a conflict. Collision severity is taken only from `C_SEV`, even if person rows fail casualty reconciliation. Person/outcome disagreements are flags, never automatic outcome repair.

## Person and vehicle identity boundaries

The audit's numeric candidate-person rule uses valid event identity with numeric `V_ID=1–99` and `P_ID=1–99`; uniqueness and agreement are additional requirements, not guaranteed by a numeric ID. `V_ID=99` is the pedestrian dummy vehicle sequence and must not be counted as a motor vehicle. Candidate motor-vehicle IDs are `1–98`. `P_ID=NN` is a dummy person for situations such as a parked car; unknown `UU`, blanks and unresolved star codes do not identify people. Preserve these records and their coded context rather than inventing person IDs, matching unknown IDs together or removing their otherwise usable collision.

This phase does not claim one raw row equals one person and does not build deduplicated person or vehicle tables. Separate future tasks must define eligibility and reconcile conflicts before person-level modeling, age/safety comparisons or vehicle-count analysis. Road-user memberships can overlap within collisions; group counts cannot be added to obtain an exclusive collision total.

## Missingness and code domains at collision grain

Recompute each feature's distributions and missingness with **one candidate event per denominator**, by source/year and pooled only over the selected population. Include all documented states, unresolved stars, blanks, invalid codes and conflicts; if an eligible-target subset is also reported, label its denominator explicitly. Do not recycle person-segment-weighted missingness from the source audit.

| State | Interpretation |
| --- | --- |
| `U` / repeated `UU` etc., only where the field dictionary defines it | Unknown. Preserve token width. |
| `X` / repeated `XX` etc., only where defined | Jurisdiction does not provide this element; distinct from unknown. |
| `Q` / repeated `QQ` etc., only where defined | Other than listed values; not missing and not a particular known condition. |
| `N` / repeated `NN` etc., only where defined | Not applicable, including documented dummy cases; not no injury or zero. |
| `P_USER=U` | Combined not-stated/other/unknown category that cannot be decomposed. |
| `*` / `**` and other star-bearing tokens | Meaning unresolved in the acquired dictionary; preserve as unresolved source codes. |
| Blank | No recorded token, separate from documented sentinel states. |
| Conflict | Multiple canonical source values for one collision attribute, represented as null with the corresponding conflict flag. |
| Nonblank code outside the field's documented domain | Preserve as invalid/undocumented for that field; generic sentinel spelling does not establish a valid field-specific meaning. |

The machine contract gives the exact eight predictor domains. In those domains no not-applicable code is documented, so e.g. `C_WTHR=N` must remain an invalid field-specific value rather than gaining a legitimate weather meaning. An audit's broad sentinel-class helper can describe token shape, but a domain check must still expose invalid field-specific codes. Missingness and valid numeric-code support are distinct measures: `Q`/`QQ` is a documented other category, while numeric support excludes it. All eight predictors remain categorical.

Do not impute, encode, scale, merge categories, resample, fit features or make model-oriented row exclusions during preparation. A target-eligible collision with a missing/invalid predictor remains in the dataset; target eligibility is not complete-case eligibility or deployment readiness.

## Required validation evidence and boundaries

The validation report must account for selected inputs and hashes, years, schemas and normalization; unique event keys; nonempty source lineage; input/event/quarantine conservation; annual and pooled counts; target-label/eligibility consistency; exact agreement with audit totals and exclusion differences; duplicate/identity/attribute-conflict counts; and collision-level value/missingness profiles with explicit denominators. Check declared eight-feature allowlist and deny all target, identity, event-result and quality-derived predictors. Negative/synthetic cases must exercise exception behavior even when a finding is zero in the selected real data.

Reconcile against the audited **selected microdata**; separately preserve the documented differences from newer national publication totals. Do not reweight, invent records or overwrite outcomes to force those totals to agree. Record exceptions or failures visibly. Output fingerprints identify the exact prepared release and make reruns inspectable.

Successful preparation establishes a reproducible analytical dataset and its limits. It does not prove predictive performance, reporting completeness, causal policy effectiveness, source-key semantics, or prospective measurement availability. Event locations, daily dates, traffic exposure and no-crash controls are absent; hotspot maps and occurrence probability remain outside this dataset's supported uses. Chronological split design and training-only transformations belong to the following modeling phase.
