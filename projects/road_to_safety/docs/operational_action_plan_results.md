# Operational Decision-Support Action Plan — Technical Results (Phases 1–4)

**Completed:** November 7, 2026  
**Scope:** Implementation of the four-phase Recommended Action Plan transitioning the *Road to Safety* portfolio from retrospective national condition-only baselines into an operational decision-support toolkit.

---

## Executive Summary

| Phase | Operational Capability | Primary Dataset & Grain | Headline Empirical Finding |
| --- | --- | --- | --- |
| **Phase 1: Corridor-Level Pilot Linkage** ([`corridor_pilot.py`](../src/road_to_safety/corridor_pilot.py)) | Exposure-proxy screening rate modeling ($\text{Crash} / 10^8\text{ VKT}$), Negative Binomial Safety Performance Functions (SPFs) & Empirical Bayes (EB) hotspot screening | **City of Toronto** (`50,083` road segments; `14,410` AADT-monitored segments; `7,673` KSI collisions, 2006–2023) + **Quebec MTQ** (`7,911` highway sections) | **99.95%** of valid-coordinate KSI events (`7,669 / 7,672`) snap within 50 m of a centreline (`1.74 m` median distance). Pooled rate is **4.706 KSI / 100M VKT** (`0.636` fatal / 100M VKT; NB2 $\alpha = 0.7749$). Urban Major Arterials (`5.352` KSI / 100M VKT; NB2 rate ratio `6.31x` vs Local) carry **12.6x** the per-VKT KSI rate of grade-separated Expressways (`0.423` KSI / 100M VKT), driven by Vulnerable Road Users (**65.5%** of Major Arterial KSI). |
| **Phase 2: Road-User & Vehicle Typologies** ([`typology_severity.py`](../src/road_to_safety/typology_severity.py)) | Reintroduction of person-level `P_USER` and vehicle-level `V_TYPE` into collision severity models | **NCDB 1999–2021** (`2,949,846` collisions; `47,793` fatal collisions conserved 1:1 with `collisions.parquet`) | Adding `P_USER` and `V_TYPE` (`M2_full_typology`) boosts 2020–2021 out-of-time **ROC-AUC from 0.6958 to 0.7628 (+6.70 pp)** and **PR-AUC from 4.15% to 7.47% (+80.0% relative lift)** while reducing log-loss from `0.09276` to `0.08802` (**-5.11%** — nearly 9x the log-loss gain achieved by GBDT trees on conditions alone). Top adjusted fatality drivers: **Road tractors (`OR = 5.99x`)**, **Off-road/special vehicles (`OR = 4.86x`)**, **Unit heavy trucks (`OR = 3.17x`)**, **Pedestrians (`OR = 2.69x`)**, and **Heavy Freight $\times$ VRU interaction (`OR = 2.54x`, 12.46% observed fatality rate)**. |
| **Phase 3: Threshold Tuning & Tiered Triage** ([`operational_triage.py`](../src/road_to_safety/operational_triage.py)) | Cost-utility / Vickers-Elkin Net Benefit curves & 3-Tier operational triage replacing the flat 80% recall heuristic | **NCDB Validation (2017–2019, `330,376` collisions)** & **Out-of-Time Test (2020–2021, `163,580` collisions)** | Replaces the legacy flat 80% recall threshold (`55.94%` flagged, `2.89%` precision) with a **3-Tier Operational Triage**: **Tier 1 Critical (`10:1` cost ratio)** flags `1.10%` of collisions at **14.27% precision (`14.24x` relative risk vs routine)**; **Tier 2 Priority (`25:1`)** flags `9.38%` of collisions capturing **34.46% of all fatalities at 7.26% precision**; **Tier 3 Watchlist (`50:1`)** flags `28.06%` (half the legacy alert burden) while capturing **63.50% of all fatalities**. |
| **Phase 4: Prospective Monitoring Pipeline** ([`monitor_prospective.py`](../src/road_to_safety/monitor_prospective.py)) | Open Canada CKAN release scraper, schema/sentinel auditor, and covariate ($\text{PSI}$, $\text{JSD}$) + calibration ($\text{O/E}$, $\Delta \alpha$, $\text{ECE}$) drift monitor | **CKAN Package `1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a`** + **2017–2021 Backtest & 2022–2023 Prospective Stress Simulations** | Verifies all `24` local selected artifacts (`SHA-256` match), confirms `2017–2019` remain in the **`GREEN`** governance band ($\text{O/E} \in [0.96, 1.01]$, $\max \text{PSI} \le 0.0022$), automatically triggers **`RED`** calibration drift alerts in `2020` ($\text{O/E} = 1.217$) and `2021` ($\text{O/E} = 1.202$), and isolates prospective rebound (`AMBER`) vs. jurisdiction sentinel degradation (`RED`, $\text{PSI} = 0.297$). |

---

## Phase 1: Corridor-Level Pilot Linkage (Spatial + Exposure)

### 1.1 Methodology & Spatial-Exposure Reconciliation
National NCDB microdata intentionally omit municipal street names, coordinates, and traffic volume denominators. To build exposure-proxy screening models ($\text{Crash} / 10^8\text{ VKT}$), Phase 1 links three official open datasets for the **City of Toronto (2006–2023, 18-year study window)** alongside a provincial highway exposure comparator from **Transports et Mobilité durable Québec (MTQ)**:
1. **Collision Numerators (`toronto_ksi_4326.csv`)**: `18,957` person-level records collapsed by `collision_id` into **`7,673` unique Killed or Seriously Injured (KSI) collision events** (`1,073` fatal collisions, `6,600` serious non-fatal injury collisions). `7,672` events carry valid WGS84 coordinates.
2. **Road Network Inventory (`toronto_centreline_4326.csv`)**: `50,083` motor-vehicle and active-corridor road segments totaling **`6,474.72` centreline km** across 12 road classes.
3. **AADT Volume Denominators (`toronto_svc_summary.csv`)**: `45,043` short-term traffic volume studies mapped 100% by `CENTRELINE_ID` to **`14,410` unique monitored road segments (`2,338.33 km`)**, representing **`1,044.446` units of $10^8\text{ VKT}$ (104.44 billion vehicle-kilometres traveled)** as an **exposure-proxy screening estimate** over the 18-year period.
4. **Exposure Denominator Audit & FHWA Caveats ([`toronto_exposure_study_audit.csv`](../reports/tables/toronto_exposure_study_audit.csv))**:
   - Short-term count studies span 1993–2026 with a **median duration of 72.0 hours** (typically 3-day counts).
   - `1,882` studies were conducted post-2023, and `615` segments have counts recorded exclusively after the 2006–2023 collision period.
   - `6,273` of `14,410` monitored segments (`43.5%`) rely on counts from only one calendar year, while `8,137` (`56.5%`) are multi-year verified ($\ge 2$ distinct years).
   - Under FHWA Traffic Monitoring Guide (TMG) standards, extrapolating 72-hour counts without local seasonal or day-of-week expansion factors serves as an **exposure screening proxy**, not a continuous longitudinal travel audit.
5. **Exposure Ranking Sensitivity ([`corridor_ranking_sensitivity.csv`](../reports/tables/corridor_ranking_sensitivity.csv))**:
   - Comparing corridor Empirical Bayes (EB) rankings under the **Primary specification** vs. **Collision-window constrained (2006–2023 only)** yields a Spearman rank correlation of **$\rho = 0.9816$** ($p = 2.10 \times 10^{-69}$, $n=96$ qualifying corridors).
   - Comparing Primary vs. **Multi-year verified ($\ge 2$ calendar years)** yields **$\rho = 0.9800$** ($p = 2.37 \times 10^{-61}$, $n=87$ corridors).
   - These results confirm that while absolute exposure figures are screening proxies, relative corridor risk prioritization and EB hotspot identifications are remarkably robust.
6. **Hybrid Spatial + Street-Name Snapping**: Using a local equirectangular projection ($\varphi_0 = 43.70^\circ\text{N}$) and `scipy.spatial.cKDTree` vertex/midpoint indexing, each collision is evaluated against candidate segments within `50 m`, prioritizing segments whose `LINEAR_NAME_FULL` shares a normalized street token with `stname1` or `stname2`. **`7,669` of `7,672` valid-coordinate collisions (`99.95%`)** snap within `50 m`, with a **median perpendicular snap distance of `1.74 m`** and **`7,559` (`98.53%`)** verified by both spatial proximity and street name.

### 1.2 Exposure-Normalized Occurrence Rates by Functional Road Class
From [`reports/tables/corridor_pilot_by_road_class.csv`](../reports/tables/corridor_pilot_by_road_class.csv):

| Functional Road Class | Monitored Segments | Monitored Length (km) | Mean AADT (veh/day) | Cumulative Exposure ($10^8$ VKT) | KSI Crashes | Fatal Crashes | VRU KSI Crashes | KSI per $10^8$ VKT | Fatal per $10^8$ VKT | VRU KSI per $10^8$ VKT | EB Expected KSI per $10^8$ VKT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Major Arterial** | 3,031 | 479.49 | 18,287.1 | 621.798 | 3,328 | 455 | 2,180 | **5.352** | **0.732** | **3.506** | 5.352 |
| **Minor Arterial** | 1,696 | 255.59 | 9,574.2 | 165.203 | 858 | 113 | 601 | **5.194** | **0.684** | **3.638** | 5.193 |
| **Collector** | 2,768 | 427.14 | 3,627.0 | 104.940 | 397 | 46 | 281 | **3.783** | **0.438** | **2.678** | 3.783 |
| **Local** | 6,069 | 1,015.28 | 1,085.9 | 70.086 | 288 | 37 | 211 | **4.109** | **0.528** | **3.011** | 4.039 |
| **Expressway Ramp** | 259 | 77.97 | 9,656.7 | 47.506 | 18 | 3 | 9 | **0.379** | **0.063** | **0.189** | 0.474 |
| **Expressway** | 38 | 12.06 | 29,660.2 | 26.024 | 11 | 1 | 2 | **0.423** | **0.038** | **0.077** | 0.250 |
| **Major Arterial Ramp** | 54 | 9.27 | 5,968.0 | 3.821 | 7 | 6 | 3 | **1.832** | **1.570** | **0.785** | 1.504 |

### 1.3 Safety Performance Functions (Poisson vs. NB2) & Top EB Hotspots
Fitting offset-adjusted Poisson and Negative Binomial (NB2) Safety Performance Functions with offset $\log(\text{Exposure}_{10^8\text{ VKT}})$ ([`corridor_pilot_model_coefficients.csv`](../reports/tables/corridor_pilot_model_coefficients.csv)) confirms substantial extra-Poisson overdispersion ($\alpha = 0.7749$, NB2 log-likelihood $-9,393.1$ vs. Poisson $-9,828.9$). Controlling for $\log(\text{AADT})$ and segment length, NB2 rate ratios relative to Local/Other streets are **`6.31x` for Major Arterials**, **`4.03x` for Minor Arterials**, **`1.76x` for Collectors**, and **`0.53x` for Expressways**.

Empirical Bayes (EB) shrinkage ($\hat{\lambda}_i^{\text{EB}} = w_i \hat{\mu}_i + (1 - w_i) y_i$, where $w_i = 1 / (1 + \alpha \hat{\mu}_i)$) identifies the highest-risk corridors with $\ge 2.0\text{ km}$ monitored length and $\ge 0.50 \times 10^8\text{ VKT}$ ([`corridor_pilot_top_corridors.csv`](../reports/tables/corridor_pilot_top_corridors.csv)):
1. **Spadina Ave (Major Arterial)**: `13.98` EB KSI / $10^8$ VKT (`21.52` observed; `43` KSI, `8` fatal, `40` VRU KSI; $+8.52$ PSI excess KSI).
2. **St Clair Ave W (Major Arterial)**: `11.26` EB KSI / $10^8$ VKT (`13.73` observed; `64` KSI, `8` fatal, `45` VRU KSI; $+9.36$ PSI excess KSI).
3. **Bay St (Major Arterial)**: `10.49` EB KSI / $10^8$ VKT (`13.88` observed; `37` KSI, `4` fatal, `29` VRU KSI).
4. **Danforth Ave (Major Arterial)**: `9.94` EB KSI / $10^8$ VKT (`13.17` observed; `74` KSI, `3` fatal, `57` VRU KSI; $+11.30$ PSI excess KSI).
5. **Bloor St W (Major Arterial)**: `8.41` EB KSI / $10^8$ VKT (`8.90` observed; `96` KSI, `10` fatal, `78` VRU KSI).
6. **Sherbourne St (Minor Arterial)**: `8.19` EB KSI / $10^8$ VKT (`12.44` observed; `18` KSI, `6` fatal, `16` VRU KSI; `4.15` fatals / $10^8$ VKT).
7. **Yonge St (Major Arterial)**: `7.41` EB KSI / $10^8$ VKT (`8.54` observed; `169` KSI, `14` fatal, `130` VRU KSI; highest total excess $\text{PSI} = +19.03$ KSI crashes).

Visualizations: [`reports/figures/corridor_pilot_spf_and_corridors.png`](../reports/figures/corridor_pilot_spf_and_corridors.png) and [`reports/figures/corridor_pilot_spatial_hotspot_map.png`](../reports/figures/corridor_pilot_spatial_hotspot_map.png).

---

## Phase 2: Incorporate Road-User (`P_USER`) & Vehicle (`V_TYPE`) Typologies

### 2.1 Collision-Grain Extraction & Conservation
Previously, `P_USER` and `V_TYPE` were excluded from the primary severity model because they reside at the person/vehicle level in the raw NCDB files. [`typology_severity.py`](../src/road_to_safety/typology_severity.py) scans all 23 selected raw NCDB releases (1999–2021; `7,729,886` source rows), normalizes English and French (`y_2021-fr.csv`, `cp1252`) schemas, and aggregates binary involvement flags per collision key `(source_id, C_YEAR, C_CASE)` into [`data/derived/typology_severity/collision_typologies.parquet`](../data/derived/typology_severity/collision_typologies.parquet), conserving **`2,949,846` collisions and `47,793` fatal collisions (100.00% exact match)**.

### 2.2 Nested Model Comparison & Non-Overlapping Rolling Calibration
Rolling chronological folds (2014–2021) in [`reports/tables/typology_rolling_folds.csv`](../reports/tables/typology_rolling_folds.csv) enforce strictly non-overlapping training and calibration partitions: for evaluation year $t$, calibration uses $t - 1$ (or pre-pandemic 2019 for $t \ge 2020$) and training strictly uses prior years ($\le \text{cal\_year} - 1$), avoiding any training/calibration leakage. Intercept recalibration shifts are keyed by `(model_name, train_cutoff, cal_year)` guaranteeing distinct cache storage.

From [`reports/tables/typology_model_summary.csv`](../reports/tables/typology_model_summary.csv):

| Split | Model Specification | ROC-AUC | PR-AUC (%) | Log-Loss | Brier Score | O/E Ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **Validation (2017–2019, `n=330,376`)** | `M0_conditions_only` (8 env/road vars) | 0.6945 | 3.38% | 0.07565 | 0.01499 | 0.980 |
| **Validation (2017–2019, `n=330,376`)** | `M1_plus_p_user` (+ Road-User `P_USER`) | 0.7248 | 4.41% | 0.07414 | 0.01492 | 0.984 |
| **Validation (2017–2019, `n=330,376`)** | **`M2_full_typology` (+ `P_USER` + `V_TYPE`)** | **0.7692** | **6.16%** | **0.07166** | **0.01478** | **0.990** |
| **Test (2020–2021, `n=163,580`)** | `M0_conditions_only` (8 env/road vars) | 0.6958 | 4.15% | 0.09276 | 0.01918 | 1.227 |
| **Test (2020–2021, `n=163,580`)** | `M1_plus_p_user` (+ Road-User `P_USER`) | 0.7215 | 5.52% | 0.09093 | 0.01906 | 1.219 |
| **Test (2020–2021, `n=163,580`)** | **`M2_full_typology` (+ `P_USER` + `V_TYPE`)** | **0.7628** | **7.47%** | **0.08802** | **0.01886** | **1.210** |

### 2.3 Adjusted Fatality Drivers & Subgroup Recovery
Controlling for all 8 environmental, temporal, and roadway configuration predictors ([`reports/tables/typology_odds_ratios.csv`](../reports/tables/typology_odds_ratios.csv)):
- **Road tractor / semi-trailer (`V_TYPE=08`)**: Adjusted **$\text{OR} = 5.99\text{x}$** (`6.80%` unadjusted fatality rate across `80,540` collisions; `5,475` fatal collisions).
- **Off-road / farm / construction / streetcar (`V_TYPE=16,18-23`)**: Adjusted **$\text{OR} = 4.86\text{x}$** (`5.62%` fatality rate across `30,380` collisions).
- **Unit heavy truck $> 4,536\text{ kg}$ (`V_TYPE=07`)**: Adjusted **$\text{OR} = 3.17\text{x}$** (`3.57%` fatality rate across `96,460` collisions).
- **Pedestrian involved (`P_USER=3` / `V_TYPE=NN`)**: Adjusted **$\text{OR} = 2.69\text{x}$** (`2.81%` fatality rate across `282,626` collisions; `7,947` fatal collisions).
- **Heavy Freight $\times$ Vulnerable Road User interaction (`heavy_freight_x_vru`)**: Multiplicative interaction **$\text{OR} = 2.54\text{x}$** (`12.46%` unadjusted fatality rate — `1,526` fatals in `12,252` collisions).
- **Motorcyclist involved (`P_USER=5` / `V_TYPE=14`)**: Combined person + vehicle effect yields $> 3.2\text{x}$ odds (`3.19%` fatality rate across `140,835` collisions).

Crucially, `M0_conditions_only` severely underpredicts high-lethality road-user and vehicle subgroups on the 2020–2021 test set ([`reports/tables/typology_subgroup_performance.csv`](../reports/tables/typology_subgroup_performance.csv)):
- **Pedestrian collisions (`3.57%` observed fatal in 2020–2021)**: `M0` predicts `1.27%` (severe underprediction because most pedestrian crashes occur on dry urban intersections during daylight); `M2` recovers prediction to `2.74%` and boosts pedestrian PR-AUC from `9.84%` to `13.47%`.
- **Road Tractor collisions (`7.44%` observed fatal)**: `M0` predicts `2.07%`; `M2` recovers prediction to `7.09%` and boosts PR-AUC from `8.97%` to `17.17%`.
- **Heavy Freight $\times$ VRU collisions (`15.48%` observed fatal)**: `M0` predicts `1.56%` (a 10-fold underprediction!); `M2` predicts `12.82%` and cuts subgroup log-loss from `0.6556` to `0.4121`.

Visualizations: [`reports/figures/typology_model_comparison.png`](../reports/figures/typology_model_comparison.png) and [`reports/figures/typology_odds_and_subgroups.png`](../reports/figures/typology_odds_and_subgroups.png).

---

## Phase 3: Operational Threshold Tuning & Tiered Triage

### 3.1 Replacing the Flat 80% Recall Heuristic with a 3-Tier Triage Architecture
The legacy protocol optimized a single threshold for $\ge 80\%$ validation recall on `M0_conditions_only` ($\tau = 0.01161$), which flags **`55.94%` of all test collisions (`91,507` alerts)** with **`2.89%` precision (`33.7` false positives per true fatality)**.

Using decision-curve cost-utility optimization on 2017–2019 validation data (`C_FN : C_FP` cost ratios of `10:1`, `25:1`, and `50:1`) and evaluating out-of-sample on 2020–2021 ([`reports/tables/triage_tiered_operating_points.csv`](../reports/tables/triage_tiered_operating_points.csv) and [`reports/tables/triage_mutually_exclusive_bands.csv`](../reports/tables/triage_mutually_exclusive_bands.csv)):

| Triage Tier / Operating Policy (Test 2020–2021, `n=163,580`, `3,230` Fatal) | Threshold ($\tau$) | Collisions Flagged (%) | Precision / PPV (%) | Fatal Recall (%) | False Positives per True Fatal | Net Benefit per 10k Collisions | Primary Operational Action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **Legacy Flat 80% Recall (`M0`)** | 0.01161 | 55.94% (`91,507`) | 2.89% | 81.73% | 33.66 | 52.74 (at 50:1) | Unchanged baseline heuristic |
| **Flat 80% Recall (`M2` Typology)** | 0.01167 | 44.58% (`72,931`) | 3.57% | 80.62% | 27.01 | 73.20 (at 50:1) | Cuts 18,576 false alarms at same 80% recall |
| **Tier 1: Critical Trauma Dispatch (`10:1`)** | 0.08828 | **1.10%** (`1,801`) | **14.27%** | **7.96%** | **6.01** | **+6.27** (vs `-782.8` treat-all) | Immediate air/ALS trauma dispatch & trauma center pre-alert |
| **Tier 2: Priority Field Response (`25:1`)** | 0.03624 | **9.38%** (`15,337`) | **7.26%** | **34.46%** | **12.78** | **+33.26** (vs `-194.6` treat-all) | Priority police/EMS staging & high-lethality corridor enforcement |
| **Tier 3: Systemic VRU Watchlist (`50:1`)** | 0.01822 | **28.06%** (`45,903`) | **4.47%** | **63.50%** | **21.38** | **+71.77** (vs `+1.41` treat-all) | Network screening for protected signal phases & road safety audits |

When partitioned into **mutually exclusive risk bands** on 2020–2021 test collisions ([`triage_mutually_exclusive_bands.csv`](../reports/tables/triage_mutually_exclusive_bands.csv)):
- **Band 1 (`p >= 0.0883`, `1.10%` of crashes)**: **14.27% fatality rate** (**`14.24x`** relative risk vs. Routine Band 4).
- **Band 2 (`0.0362 <= p < 0.0883`, `8.28%` of crashes)**: **6.32% fatality rate** (**`6.31x`** relative risk vs. Routine Band 4).
- **Band 3 (`0.0182 <= p < 0.0362`, `18.69%` of crashes)**: **3.07% fatality rate** (**`3.06x`** relative risk vs. Routine Band 4).
- **Band 4 (`p < 0.0182`, `71.94%` of crashes)**: **1.00% fatality rate** (`1.00x` baseline routine risk).

### 3.2 Context-Specific Operating Curves (Non-Intersection Uncontrolled/Freight Scenario vs. Urban VRU Calming)
From [`reports/tables/triage_context_specific_curves.csv`](../reports/tables/triage_context_specific_curves.csv):

> [!NOTE]
> **Retrospective Research Scope & Operational Boundaries**:
> Subgroup analyses such as `non_intersection_uncontrolled_or_freight` represent retrospective research scenarios, NOT an operational dispatch protocol. In NCDB microdata, predictors like post-crash roadway alignment (`C_RALN`), configuration (`C_RCFG`), and multi-vehicle freight typologies are ascertained post-investigation and are not proven to be reliably available at 911 emergency call intake.

- **Non-Intersection Uncontrolled or Freight Scenario (`non_intersection_uncontrolled_or_freight`; `n=59,138` test collisions, `1,884` fatals, `3.19%` base fatality rate)**:
  - Factual definition: Non-intersection (`C_RCFG=1`) collisions that are uncontrolled (`C_TRAF=18`), on non-level/curved alignments (`C_RALN \in {2..6}`), or involve heavy freight.
  - At `10:1` cost ratio ($\tau = 0.0860$): flags `2.50%` of collisions (`1,478`) with **14.28% precision** and **11.20% recall** (`6.00` FP/TP).
  - At `25:1` cost ratio ($\tau = 0.0348$): flags `20.47%` of collisions (`12,106`) with **7.20% precision** and **46.23% recall** (`12.90` FP/TP).
- **Urban Intersection & VRU Traffic Calming Context (`urban_intersection_vru`; `n=90,636` test collisions, `1,609` fatals, `1.78%` base fatality rate)**:
  - At `25:1` cost ratio ($\tau = 0.0423$): flags `5.56%` of urban/VRU collisions (`5,037`) with **9.89% precision** (`5.56x` lift over base rate) and **30.95% recall**, isolating pedestrian/cyclist intersections with heavy-vehicle turning or high-speed arterial exposure.
  - At `50:1` cost ratio ($\tau = 0.0198$): flags `25.29%` of urban/VRU collisions (`22,923`) and captures **60.91% of all urban/VRU fatalities**.

Visualizations: [`reports/figures/triage_cost_utility_and_pr.png`](../reports/figures/triage_cost_utility_and_pr.png) and [`reports/figures/triage_context_operating_curves.png`](../reports/figures/triage_context_operating_curves.png).

---

## Phase 4: Prospective Data Monitoring Pipeline (2022+ NCDB Drift & Catalog Scraper)

### 4.1 Open Canada CKAN Catalog Monitor & Integrity Check
[`monitor_prospective.py`](../src/road_to_safety/monitor_prospective.py) monitors Transport Canada's Open Government CKAN dataset (`1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a`, supporting both offline snapshot verification and `--online` live CKAN API queries):
- Confirms all **24 local selected resources** (23 annual releases `1999–2021` + `data_dictionary.pdf`) match their pinned `SHA-256` fingerprints (`0` mismatches).
- Confirms `0` post-2021 microdata CSV/XLSX releases are present in the preserved CKAN catalog (`ingestion_status = READY_WAITING_FOR_TC_2022_RELEASE`).

### 4.2 Historical Backtest (2017–2021) & Prospective 2022–2023 Stress Simulations
From [`reports/tables/monitoring_annual_drift_summary.csv`](../reports/tables/monitoring_annual_drift_summary.csv) and [`reports/tables/monitoring_feature_psi_matrix.csv`](../reports/tables/monitoring_feature_psi_matrix.csv):

| Release / Cohort | Collisions | Observed Fatal % | `M2` Pred Fatal % | `M2` O/E Ratio | `M2` Log-Odds Drift ($\Delta \alpha$) | Max Feature PSI (Feature) | Max Unknown Sentinel Shift (pp) | Governance Alert | Automated Action Triggered |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| **2017** | 114,412 | 1.484% | 1.547% | 0.960 | -0.043 | 0.00089 (`C_MNTH`) | +0.20 pp | **`GREEN`** | Retain production model weights |
| **2018** | 111,334 | 1.575% | 1.553% | 1.014 | +0.015 | 0.00093 (`C_MNTH`) | +0.18 pp | **`GREEN`** | Retain production model weights |
| **2019** | 104,630 | 1.548% | 1.551% | 0.998 | -0.002 | 0.00223 (`C_RSUR`) | +0.20 pp | **`GREEN`** | Retain production model weights |
| **2020 (Pandemic Y1)** | 79,990 | 2.003% | 1.645% | **1.217** | **+0.206** | 0.03037 (`C_MNTH`) | +0.65 pp | **`RED`** | Quarantine uncalibrated scores; apply rolling intercept recalibration |
| **2021 (Pandemic Y2)** | 83,590 | 1.948% | 1.620% | **1.202** | **+0.193** | 0.01970 (`C_RSUR`) | +0.62 pp | **`RED`** | Quarantine uncalibrated scores; apply rolling intercept recalibration |
| **2022 Rebound (Sim)** | 90,000 | 1.726% | 1.580% | **1.093** | **+0.093** | 0.00429 (`C_RSUR`) | +0.41 pp | **`AMBER`** | Apply prior-year intercept recalibration update |
| **2023 Sentinel Outage (Sim)** | 83,590 | 1.948% | 1.620% | **1.202** | **+0.193** | **0.29705 (`C_WTHR`)** | **+11.81 pp** | **`RED`** | Quarantine release & audit jurisdiction `U/UU` reporting spike |

Visualization: [`reports/figures/monitoring_drift_dashboard.png`](../reports/figures/monitoring_drift_dashboard.png).

### 4.3 Prospective Release Schema Validator & Ingestion Workflow
[`monitor_prospective.py`](../src/road_to_safety/monitor_prospective.py) implements the production intake validator:
- `validate_release_schema(df, expected_schema=None)`: Validates mandatory NCDB columns (`C_YEAR`, `C_CASE`, `C_SEV`, `C_MNTH`, `C_WDAY`, `C_HOUR`, `C_RCFG`, `C_WTHR`, `C_RSUR`, `C_RALN`, `C_TRAF`, `V_ID`, `V_TYPE`, `P_ID`, `P_USER`), domain codes against `explore.DICTIONARY_DOMAINS`, non-null requirements, and key integrity. Returns status (`valid`, `anomalies_detected`, `invalid_schema`) with error counts and column profile summaries.
- `ingest_and_score_release(csv_path, model_weights=None, ...)`: Demonstrates the bounded new-release workflow: validate schema $\to$ capture receipt (SHA-256 fingerprint, timestamps, row counts) $\to$ score prospective records with calibrated model weights.
- **Operational Status & Boundaries**:
  - *Implemented*: Open Canada CKAN metadata monitor, SHA-256 integrity verification of 1999–2021 releases, schema validation function, covariate PSI & calibration O/E drift calculation, synthetic release simulation.
  - *Research / Simulated*: 2022–2023 synthetic stress batches (post-pandemic normalization & reporting outage stress tests).
  - *Pending*: Live Transport Canada 2022+ release ingestion (awaiting Transport Canada publication).

---

## Reproducibility Commands

Run all four operational phases and the 71-test verification suite from `projects/road_to_safety`:

```bash
MPLCONFIGDIR=/tmp/mpl .venv/bin/python -m road_to_safety.corridor_pilot
MPLCONFIGDIR=/tmp/mpl .venv/bin/python -m road_to_safety.typology_severity --workers 4
MPLCONFIGDIR=/tmp/mpl .venv/bin/python -m road_to_safety.operational_triage
MPLCONFIGDIR=/tmp/mpl .venv/bin/python -m road_to_safety.monitor_prospective
MPLCONFIGDIR=/tmp/mpl .venv/bin/python -m unittest discover -s tests -v
```
