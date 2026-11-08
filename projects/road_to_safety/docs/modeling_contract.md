# Collision-severity modeling contract

Status: preparation contract, October 17, 2026. No exploration, trained model, feature transformation, resampling or performance claim is included. The executable allowlist and code domains are in [modeling_contract.json](../data/reference/modeling_contract.json); exception rules are in [preparation_policy.md](preparation_policy.md).

## Population, unit and target

The population is the selected official annual NCDB microdata releases for **1999–2021**, including all released road-user categories. Exactly one pinned source release supplies each year. The older 2019 comparator and national/provincial/dashboard aggregate cells are excluded from this event table. This is the released fatal/injury collision population, not every Canadian road incident or a verified complete national surveillance census.

The unit is one **candidate collision**, identified by `(source_id, C_YEAR, C_CASE)`, where `source_id` is the selected resource UUID. `C_YEAR` must match the manifest's selected year and `C_CASE` must be a positive integer-form identifier. Canonical strings remove numeric zero padding, so raw `001` and `1` identify the same within-release candidate. Original strings and row positions remain recoverable from the archived source and evidence. The acquired dictionary does not define `C_CASE`; within-release repeated-attribute consistency supports this candidate grain but does not establish permanent identity or cross-release linkage. No geographical meaning is inferred from case numbers.

| Original target | `is_fatal` | Meaning |
| --- | ---: | --- |
| `C_SEV=1` | 1 | Collision producing at least one fatality |
| `C_SEV=2` | 0 | Collision producing nonfatal injury |
| Blank, unknown, unavailable, invalid or conflicting `C_SEV` | null | Retained candidate collision; `severity_eligible=false` |

`severity_eligible=true` requires a valid candidate key and exactly one observed normalized target code, either `1` or `2`. Blanks count as observed values when checking agreement: a mixture of `1` and blank is unresolved, not automatically fatal. There is no majority, first-row, worst-outcome or person-outcome override. A single agreed unknown target remains ineligible. This eligibility is about the target, not a guarantee that every predictor is usable.

Class 0 is an **injury collision**, never a no-accident observation. A future model estimates fatal severity conditional on a recorded fatal/injury collision and supplied conditions. It does not estimate accident occurrence, individual fatality, property-damage-only outcomes or a serious-injury subclass. `P_ISEV` describes person segments and must not be substituted for `C_SEV`, including where person outcomes disagree with the event label.

## Initial predictor allowlist

Only the following eight columns may enter the initial condition-based severity model. They remain categorical, including numeric-looking codes; code differences are not numeric weather/road severity distances. Cyclical encodings or alternative representations require a later modeling-stage decision fitted within chronological development data.

| Field | Dictionary domain after numeric padding normalization | Purpose and rationale |
| --- | --- | --- |
| `C_MNTH` | `1`–`12`, `UU`, `XX` | Seasonal conditions; month cannot identify an actual date. |
| `C_WDAY` | `1` Monday–`7` Sunday, `U`, `X` | Weekly travel context; no daily exposure denominator is available. |
| `C_HOUR` | `0`–`23`, `UU`, `XX` | Time-of-day context; `0` means midnight through 00:59, not missing. |
| `C_RCFG` | `1`–`12`, `QQ`, `UU`, `XX` | Road setting such as non-intersection, intersection, bridge, ramp or traffic circle. This is road configuration, distinct from outcome-related collision configuration `C_CONF`. |
| `C_WTHR` | `1`–`7`, `Q`, `U`, `X` | Reported weather including precipitation and visibility limitation; an association within reported collisions, not an exposure-adjusted weather risk. |
| `C_RSUR` | `1`–`9`, `Q`, `U`, `X` | Reported surface condition, including dry, wet, snow, ice, debris, oil or flooding. The dictionary's sand/gravel/dirt category describes debris, not construction material. |
| `C_RALN` | `1`–`6`, `Q`, `U`, `X` | Straight/curved and gradient context without an assumed ordinal scale. |
| `C_TRAF` | `1`–`18`, `QQ`, `UU`, `XX` | Reported traffic-control context; includes dynamic states such as signal mode, police officer and stopped school bus. Availability before the crash is an assumption requiring future verification. |

Domains come from the archived [official dictionary](../data/raw/ncdb/data_dictionary.pdf), English pages 1–6: month/weekday page 1; hour/severity page 2; road configuration/weather page 4; surface/alignment page 5; traffic control page 6. Numeric normalization changes `01` to `1` and `00` to `0`, but never changes `UU` to `U`, `QQ` to `Q`, or undocumented stars to unknown. The JSON domains describe documented source codes; they do not authorize silently dropping out-of-domain observations.

Recorded conditions were collected **after crashes**. Their presence in a report does not prove they were measured or available before the crash, nor that a real-time system could supply them. The initial interpretation is a conditions-based scenario model: users supply a scenario and estimate conditional severity within the released collision population. Prospective timestamps, latency, coverage and deployment fitness remain unverified. Some conditions may themselves be affected by the event; prospective causal or operational interpretation requires separate evidence.

## Leakage exclusions and retained audit roles

The allowlist is authoritative: every column not explicitly listed is excluded even if it does not match an exclusion pattern in the JSON.

| Excluded field/group | Retained purpose | Why excluded from initial predictors |
| --- | --- | --- |
| `C_SEV`, `is_fatal`, `P_ISEV` | Label verification and target construction | Direct outcomes or target definitions. |
| Fatality/injury/casualty totals or any outcome-derived aggregates | Outcome reconciliation only | Encode target information unavailable before outcome. |
| `C_CONF`, `C_VEHS` | Event description and diagnostics | Realized crash configuration and involved vehicle count describe event results; pre-outcome availability has not been demonstrated. |
| `C_YEAR` | Chronological partitioning, coverage and temporal-shift assessment | Prevent an initial model from relying on absolute release/year trends as a surrogate for prospective conditions. No random split is substituted for chronology. |
| `source_id`, `C_CASE`, source row number, file paths/hashes, all person/vehicle/record IDs | Lineage, uniqueness, joins and grouping | Identifiers and source proxies do not represent transferable road conditions. |
| Duplicate multiplicity, exception flags/counts, conflict flags, `diagnostic_*`, `severity_eligible` | Quality assessment and conservation | Reporting artifacts can reveal outcome/source processes; they are not initial scenario inputs. |
| `V_TYPE`, `V_YEAR`, `P_SEX`, `P_AGE`, `P_PSN`, `P_SAFE`, `P_USER`, and demographic/road-user/vehicle aggregates | Separate future descriptive or fairness designs with defined units | Not in the requested condition-only scope; aggregation would require trustworthy identities, population definitions and availability evidence. Their exclusion is a scope/measurement decision, not a claim that every demographic field inherently leaks outcomes. |
| Any added future/horizon-unknown field | Unapproved until contract revision | Neither a plausible name nor a post-crash report establishes prediction-time availability. |

Person and vehicle identity problems **do not remove** a collision with an otherwise valid target. Their evidence remains in diagnostics/exceptions. No person or vehicle aggregates enter the feature table. Conflicting condition fields become null with explicit conflict flags and preserved source-row evidence; otherwise agreed unknown/invalid codes remain their original canonical tokens. Preparation does not invent safe/default conditions, impute unknown weather, merge unknown with unavailable, or learn an encoder.

## Boundary before modeling

This phase prepares reproducible event tables, profiles and a validation report. It does not choose train/test years, fit imputers/encoders, select features by association, rebalance classes, tune thresholds, calibrate probabilities or train any model. Later chronological development, validation/calibration and untouched test periods must address the documented 2020–2021 distribution shift. All records belonging to an event stay together, and transformations/resampling/feature selection must be fitted only within the relevant training folds. No final-test population is balanced or used for selection.

Known barriers remain: undocumented case-ID semantics, unresolved asterisk codes, reporting/version changes, and inconsistent national aggregate comparisons. The selected microdata define a pinned analysis population; forcing their totals to match newer publications would change that population without evidence. No geography or exposure is synthesized from those aggregates.
