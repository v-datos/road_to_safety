# Road to Safety — portfolio completion plan

Revised November 5, 2026. The original planning work began October 17, 2026.

Use Canadian collision data to describe recorded harm, evaluate conditional severity prediction and connect findings to evidence about road safety interventions. Deliver the technical portfolio first, followed by a six-page policy PDF and an interactive public visual story, all in English.

## Evidence and limits

| Evidence | Coverage | Role |
| --- | --- | --- |
| Selected NCDB records | 1999–2021, 2,949,846 candidate collisions, including 47,793 fatal collisions | National descriptive analysis and severity modeling |
| Transport Canada annual publication series | 2005–2024 | Separately published national collision and casualty trends |
| Published jurisdiction rates | 2024, 13 provinces and territories plus Canada | Geographic comparisons using published denominators |

The binary target distinguishes fatal and nonfatal injury collisions in the selected releases. The event table has no province, municipality, coordinate, full calendar date or non-crash exposure. Local hotspots and collision occurrence require further geographic and exposure data. Publication totals use a separate vintage and counting scope. See the [source inventory](source_inventory.md), [preparation validation](preparation_validation.md), [descriptive analysis](descriptive_analysis.md) and [modeling contract](modeling_contract.md).

## Milestones

| Status | Milestone | Dependency | Evidence of completion |
| --- | --- | --- | --- |
| Complete | Acquisition, validation and EDA | Official releases and dictionary | Pinned sources, prepared collision table, independent audit and executed notebooks |
| Complete | Logistic baseline, calibration and transfer study | Validated collision data | Frozen protocols, model cards and independent validations. The selected sigmoid correction worsened both proper scores in 2020 and 2021 |
| Complete | Documentation and reference check | Archived evidence | Current status in the project and report indexes. The expanded runner verifies 61 archived input fingerprints |
| Complete | Geographic comparison | 2024 rates and Statistics Canada cartographic boundaries | Exactly 13 validated matches, mortality choropleth, companion comparison chart and provenance |
| Complete | Tree comparison v1 | Verified collision table and independent environment | Frozen protocol, 120 tree fits, comparable baselines, verified selection, stress scores and interpretation |
| Complete | Technical portfolio | Geographic and model evidence | Technical HTML, synthesis and comparison notebooks, and three to five sourced recommendations |
| Complete | Policy PDF | Reviewed technical evidence | Six visually inspected pages with traceable data and actions |
| Complete | Public visual story | Same reviewed evidence | Local, accessible, responsive HTML with working year and rate selectors |
| Complete | Operational decision-support action plan (Phases 1–4) | Corridor spatial/AADT files, raw 1999–2021 NCDB `P_USER`/`V_TYPE`, CKAN catalog | Validated Toronto + Quebec MTQ SPF/EB corridor models, typology-enhanced severity models (`M0`/`M1`/`M2`), 3-tier cost-utility triage, prospective 2022+ drift monitor, [technical report](operational_action_plan_results.md), [model card](../models/typology_and_corridor_card.md) and [executed notebook](../notebooks/09_operational_decision_support.ipynb) |

The [baseline results](severity_modeling.md) and [calibration transfer results](calibration_stress_v1_results.md) are historical evidence. Existing protocols, environment, artifacts and model cards are linked to their original validations. The completed extension uses independent versioned outputs.

## Expanded severity comparison

Evaluate 2014 through 2019 individually, using training observations from 1999 through the preceding year. Compare training prevalence, refitted L2 logistic regression, Random Forest and LightGBM. Keep the eight approved categorical predictors and dictionary-based one-hot encoding. Preserve stated, unknown, other and unavailable categories.

| Family | Fixed | Full grid |
| --- | --- | --- |
| Random Forest | 300 trees, bootstrap, seed 2026 | Depth 8 or 16 × minimum leaf size 200 or 50 × feature fraction sqrt or 0.5 |
| LightGBM | 500 trees, learning rate 0.03, binary objective, seed 2026 | Leaves 15, 31 or 63 × minimum child samples 500 or 100 × L2 regularization 1 or 0 |

Use natural class prevalence. Select each family by mean annual log loss, then Brier, then fixed grid order for ties within 1e-10. A favorable development result requires lower mean log loss, lower log loss in at least four years and no worse mean Brier than logistic. Retain negative results.

Use models fitted through 2018 to select the highest-precision 2019 threshold with at least 80% fatal recall. Freeze the settings before scoring reused 2020–2021. Report annual and pooled probability scores, ranking metrics, calibration, classification counts, flagged fraction and availability groups. Interpret models with five repeats of whole-field permutation on each development evaluation year. Conditions are recorded after a crash. Feature importance reflects predictive contribution and can depend on correlations.

## Portfolio and verification

Compare the 13 jurisdictions using 2024 published rates and 2021 official cartographic boundaries. Use fatalities per 100,000 residents as the primary measure and show Canada's published benchmark. Explain preliminary, estimated and small-population figures and changes in reporting practices.

Build the technical portfolio around the validated temporal, condition, geographic and model results. Each of three to five recommendations will link an observation, primary intervention evidence, a responsible role and a measure of success. The policy PDF and public visual story will reuse these reviewed results. The public story will have supported year filters and selectable jurisdiction metrics, with keyboard access and companion data tables.

Verify input fingerprints, chronological membership, denominators, selection and thresholds, model reloads, geography joins, link targets and numerical consistency between formats. Inspect notebook and report layouts, all PDF pages and desktop and mobile interactive controls before marking the portfolio complete.
