# Model Card: Corridor Exposure SPF & Road-User/Vehicle Typology Severity Suite

**Version:** `operational_action_plan_v1` (November 7, 2026)  
**Modules:** [`corridor_pilot.py`](../src/road_to_safety/corridor_pilot.py), [`typology_severity.py`](../src/road_to_safety/typology_severity.py), [`operational_triage.py`](../src/road_to_safety/operational_triage.py), [`monitor_prospective.py`](../src/road_to_safety/monitor_prospective.py)

---

## 1. Model Family Overview

This card documents the two complementary operational model families developed to complete the *Road to Safety* Recommended Action Plan:

1. **Corridor-Level Safety Performance Functions (`SPF-Poisson` & `SPF-NB2` + Empirical Bayes)**:
   - **Target**: Segment-level Killed or Seriously Injured (KSI) collision count $y_i$ over the 18-year observation window (2006–2023) in the City of Toronto, with exposure offset $\log(E_i)$ in units of $10^8\text{ VKT}$.
   - **Population**: `14,410` AADT-monitored road segments (`2,338.33 km`; `4,915` KSI collisions; `664` fatal collisions) out of `50,083` total Centreline road segments (`6,474.72 km`).
   - **Formulation**:
     $$\log \mu_i = \log(E_i) + \beta_0 + \beta_1 \log(\text{AADT}_i / \overline{\text{AADT}}) + \beta_2 \log(L_i / \bar{L}) + \sum_{c} \gamma_c \mathbb{I}(\text{Class}_i = c)$$
     with Negative Binomial variance $\text{Var}(Y_i) = \mu_i + \alpha \mu_i^2$ ($\hat{\alpha} = 0.7749$) and Empirical Bayes shrinkage $\hat{\lambda}_i^{\text{EB}} = w_i \hat{\mu}_i + (1 - w_i) y_i$, $w_i = 1 / (1 + \hat{\alpha} \hat{\mu}_i)$.

2. **Typology-Enhanced National Collision Severity Model (`M2_full_typology` / `M_post`)**:
   - **Target**: Binary collision fatality indicator `is_fatal` (`1` = fatal collision `C_SEV=1`; `0` = non-fatal injury collision `C_SEV=2`).
   - **Population**: `2,949,846` canonical collisions (`47,793` fatal) from 23 Transport Canada NCDB annual releases (`1999–2021`).
   - **Predictors**:
     - `8` dictionary-validated environmental, temporal, and roadway condition predictors (`C_MNTH`, `C_WDAY`, `C_HOUR`, `C_RCFG`, `C_WTHR`, `C_RSUR`, `C_RALN`, `C_TRAF`).
     - `5` road-user involvement flags from `P_USER` (`has_pedestrian`, `has_bicyclist`, `has_motorcyclist`, `has_passenger`, `has_unknown_user`).
     - `11` vehicle typology and interaction flags from `V_TYPE` and `V_ID` (`has_light_duty`, `has_light_truck_van`, `has_heavy_truck`, `has_road_tractor`, `has_bus`, `has_motorcycle_moped`, `has_bicycle_vehicle`, `has_special_offroad`, `has_unknown_vehicle`, `multi_vehicle`, `heavy_freight_x_vru`).
   - **Estimator**: L2-regularized logistic regression (`C=1.0`, `lbfgs`, natural prevalence) with optional prior-year log-odds intercept recalibration (`M2_full_typology_recal`). Rolling chronological evaluation strictly enforces non-overlapping training and calibration sets (`train_cutoff = cal_year - 1`) with multi-key cache validity `(model_name, train_cutoff, cal_year)` preventing stale delta reuse across differing calibration years.

3. **Emergency Call Intake Severity Model (`M_intake`)**:
   - **Target**: Same binary fatality indicator `is_fatal`.
   - **Operational Scope**: Restricted strictly to variables available at 911 emergency call intake:
     - `3` timing predictors: `C_MNTH`, `C_WDAY`, `C_HOUR` (call timestamp).
     - `5` caller-reported binary indicators: `multi_vehicle` (scale), `has_pedestrian`, `has_bicyclist`, `has_motorcyclist` (caller-reported VRU involvement), `has_heavy_freight` (caller-reported semi-truck / tractor-trailer).
   - **Explicit Exclusions**: Excludes post-crash investigation variables (`C_RALN` alignment/grade, `C_RCFG` roadway configuration detail, `C_RSUR` surface condition, `C_TRAF` traffic control status, `C_WTHR` weather, fine vehicle sub-classes like `has_road_tractor` vs `has_special_offroad`, seating positions like `has_passenger`, and interaction terms like `heavy_freight_x_vru`).
   - **Purpose**: Establishes the validated performance envelope for 911 dispatch triage when decisions must be made before on-scene collision investigation.

---

## 2. Quantitative Evaluation Summary

### 2.1 Severity Model Benchmark (`Validation 2017–2019` vs. `Test 2020–2021`)

| Split | Model | ROC-AUC | PR-AUC (%) | Log-Loss | Brier Score | ECE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **Validation (2017–2019)** | `M0_conditions_only` | 0.6945 | 3.38% | 0.07565 | 0.01499 | 0.00031 |
| **Validation (2017–2019)** | `M_intake` | 0.7130 | 4.08% | 0.07488 | 0.01495 | 0.00049 |
| **Validation (2017–2019)** | `M1_plus_p_user` | 0.7248 | 4.41% | 0.07414 | 0.01492 | 0.00025 |
| **Validation (2017–2019)** | **`M2_full_typology` (`M_post`)** | **0.7692** | **6.16%** | **0.07166** | **0.01478** | **0.00039** |
| **Test (2020–2021)** | `M0_conditions_only` | 0.6958 | 4.15% | 0.09276 | 0.01918 | 0.00370 |
| **Test (2020–2021)** | `M_intake` | 0.7066 | 4.88% | 0.09208 | 0.01913 | 0.00364 |
| **Test (2020–2021)** | `M1_plus_p_user` | 0.7215 | 5.52% | 0.09093 | 0.01906 | 0.00355 |
| **Test (2020–2021)** | **`M2_full_typology` (`M_post`)** | **0.7628** | **7.47%** | **0.08802** | **0.01886** | **0.00353** |

### 2.2 Operational Triage Tiers (`Test 2020–2021`, `M2_full_typology_recal`)

| Tier | Cost Ratio ($C_{\text{FN}}:C_{\text{FP}}$) | Probability Cutoff ($\tau$) | Alert Volume (%) | Precision (%) | Recall (%) | FP / TP | Relative Risk vs. Routine |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Tier 1: Critical Trauma Dispatch** | 10:1 | 0.08828 | 1.10% | **14.27%** | 7.96% | 6.01 | **14.24x** |
| **Tier 2: Priority Field Response** | 25:1 | 0.03624 | 9.38% | **7.26%** | 34.46% | 12.78 | **6.31x** (Band 2) |
| **Tier 3: Systemic VRU Watchlist** | 50:1 | 0.01822 | 28.06% | **4.47%** | 63.50% | 21.38 | **3.06x** (Band 3) |
| *Legacy Flat 80% Recall (`M0`)* | — | 0.01161 | 55.94% | 2.89% | 81.73% | 33.66 | — |

### 2.3 Call Intake (`M_intake`) vs. Post-Investigation (`M_post`) Triage Comparison (`Test 2020–2021`)

From [`reports/tables/triage_intake_vs_post_comparison.csv`](../reports/tables/triage_intake_vs_post_comparison.csv):

| Triage Tier | Model Specification & Policy | Cutoff ($\tau$) | Alert Volume (%) | Precision (%) | Recall (%) | FP / TP | Relative Risk vs. Routine |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Tier 1: Critical Triage (10:1)** | `M_post_recal` (optimal validation) | 0.08828 | 1.10% (1,801) | **14.27%** | **7.96%** (257) | 6.01 | **14.24x** |
| | `M_intake_recal` (evaluated at `M_post` cutoff) | 0.08828 | 0.53% (872) | **10.55%** | **2.85%** (92) | 8.48 | **8.87x** |
| | `M_intake_recal` (separately tuned validation) | 0.08777 | 0.55% (892) | **10.43%** | **2.88%** (93) | 8.59 | **9.90x** |
| **Tier 2: Priority Response (25:1)** | `M_post_recal` (optimal validation) | 0.03624 | 9.38% (15,337) | **7.26%** | **34.46%** (1,113) | 12.78 | **7.24x** |
| | `M_intake_recal` (evaluated at `M_post` cutoff) | 0.03624 | 6.39% (10,457) | **6.20%** | **20.06%** (648) | 15.14 | **5.21x** |
| | `M_intake_recal` (separately tuned validation) | 0.03170 | 9.87% (16,144) | **5.68%** | **28.39%** (917) | 16.61 | **5.39x** |
| **Tier 3: Systemic Watchlist (50:1)** | `M_post_recal` (optimal validation) | 0.01821 | 28.06% (45,903) | **4.47%** | **63.50%** (2,051) | 21.38 | **4.46x** |
| | `M_intake_recal` (evaluated at `M_post` cutoff) | 0.01821 | 27.60% (45,153) | **4.04%** | **56.41%** (1,822) | 23.78 | **3.39x** |
| | `M_intake_recal` (separately tuned validation) | 0.01528 | 35.01% (57,274) | **3.68%** | **65.33%** (2,110) | 26.14 | **3.50x** |

**Operational Takeaways**:
- **Intake vs. Conditions-Only**: `M_intake` outperforms `M0` on test data (**ROC-AUC 0.7066 vs 0.6958; PR-AUC 4.88% vs 4.15%**), demonstrating that basic caller-reported road-user presence carries more signal than post-crash roadway and environmental conditions alone.
- **Intake vs. Post-Investigation Deficit**: Restricting to intake information incurs a **-5.62 pp drop in ROC-AUC** (0.7628 to 0.7066) and **-2.60 pp drop in PR-AUC** (7.47% to 4.88%, -34.7% relative).
- **Triage Sensitivity vs Specificity**: In Tier 1 Critical Dispatch, `M_intake` maintains high PPV (**10.43% precision, 9.90x relative risk vs routine**) with half the alert burden (0.55% vs 1.10%), but captures only **2.88% of fatal collisions** (93 fatals) compared to **7.96%** (257 fatals) for `M_post`. `M_intake` operates as a conservative, high-specificity triage filter at call intake, while on-scene investigation remains required to recover full sensitivity.

---

## 3. Intended Use, Limitations & Monitoring Governance

- **Intended Use**:
  - **Corridor SPF + EB Rankings**: Network screening for municipal Vision Zero capital allocation (protected bike lanes, leading pedestrian intervals, arterial speed reduction, and transit stop protection).
  - **Tiered Severity Triage**: Decision support for differentiating critical trauma dispatch (Tier 1), priority enforcement/EMS staging (Tier 2), and systemic VRU corridor audits (Tier 3).
  - **Context-Specific Operating Curves**: Retrospective scenario analysis contrasting non-intersection uncontrolled or freight collisions (`non_intersection_uncontrolled_or_freight`) with urban intersection/VRU collisions (`urban_intersection_vru`).
- **Limitations & Retrospective Operational Boundaries**:
  - National NCDB collisions record conditional post-crash severity given an injury or fatal collision; they do not include property-damage-only (PDO) collisions or uninvolved traffic exposure.
  - Pandemic traffic shifts in 2020–2021 elevated national fatality prevalence from `1.53%` (2017–2018) to `1.97%` (2020–2021), inducing an Observed/Expected ($\text{O/E}$) ratio of `1.21` across all pre-pandemic models.
  - Subgroup analyses like `non_intersection_uncontrolled_or_freight` represent retrospective research scenarios, NOT operational dispatch protocols. Features like post-crash road alignment (`C_RALN`), configuration (`C_RCFG`), and detailed vehicle typologies are ascertained post-investigation and are not available at emergency call intake. Operational dispatch protocols should deploy `M_intake`, which is restricted strictly to call-intake available variables (call timestamp + 5 caller-reported indicators) and achieves 10.43% Tier 1 precision (9.90x relative risk vs routine).
- **Prospective Governance (`monitor_prospective.py`)**:
  - Automated Release Ingestion & Schema Validation: Incoming annual microdata is validated via `validate_release_schema` against 15 mandatory NCDB columns, `explore.DICTIONARY_DOMAINS` code sets, non-null assertions, and key integrity. Bounded ingestion helper `ingest_and_score_release` captures SHA-256 integrity receipts before prospective scoring.
  - Drift Surveillance: Every release must pass covariate PSI ($\text{GREEN} < 0.10$, $\text{AMBER} \in [0.10, 0.25)$, $\text{RED} \ge 0.25$), sentinel shift, and $\text{O/E}$ calibration checks before updating production thresholds.
  - Implementation Boundaries:
    - *Implemented*: CKAN metadata monitor, SHA-256 verification of 1999–2021 releases, schema validation function, covariate PSI & calibration O/E drift calculation, synthetic release simulation.
    - *Research / Simulated*: 2022–2023 synthetic stress batches.
    - *Pending*: Live Transport Canada 2022+ release ingestion (awaiting Transport Canada publication).
