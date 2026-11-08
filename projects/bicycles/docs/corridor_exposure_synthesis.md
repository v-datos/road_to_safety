# Corridor Cyclist Exposure & National Typology Synthesis

Implemented by `src/bicycle_collisions/corridor_exposure_link.py`.

## 1. Purpose and Cross-Linked Evidence Scope

National collision surveillance and municipal corridor engineering answer complementary halves of the vulnerable road user (VRU) safety problem:

1. **National NCDB Linked Microdata (`2010–2021`, `68,687` unique bicycle collisions) and NCDB Online (`2010–2023`, `712` bicyclist deaths and `75,610` nonfatal injuries)** quantify national temporal trends, seasonal and intersection concentration (`70.2%` May–September; `61.1%` at intersections), and the kinetic lethality gradient across co-involved vehicle classes. However, public national records omit municipal street geometry and motor-vehicle traffic volume (`AADT`).
2. **Toronto Centreline + Short-Term Volume Count (`AADT`) Corridor Linkage (`2006–2023`, `14,410` monitored segments covering `2,338.3 km` and `1,044.45` cumulative `100M VKT`)** provides segment-level motor-vehicle exposure denominators (`exposure_100m_vkt`) and spatial linear density (`length_km`) for `543` AADT-monitored cyclist KSI collisions (`935` network-wide snapped cyclist KSI collisions across `6,474.7 km`).
3. **National `M2_full_typology` Severity Modeling (`2006–2021` out-of-time splits)** quantifies how explicit vehicle-unit and road-user indicators (`has_bicyclist`, `has_heavy_truck`, `has_road_tractor`, `heavy_freight_x_vru`) improve fatal-vs-nonfatal discrimination and calibration over environmental/contextual baselines (`M0_baseline`).

---

## 2. Functional Road Class Synthesis: Exposure Rate vs. Spatial Density

Saved in `reports/tables/toronto_cyclist_corridor_exposure_by_class.csv`.

| Road Class | Monitored Segments | Monitored km | Mean AADT | Cumulative 100M VKT (18y) | Monitored Cyclist KSI | Cyclist KSI / 100M VKT | Cyclist KSI / Monitored km | Cyclist Share of KSI (%) | Network Cyclist KSI (All Segments) | Network Cyclist KSI / km |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Major Arterial** | 3,031 | 479.494 | 18,287.1 | 621.7977 | 323 | **0.519** | **0.674** | 9.71% | 493 | 0.672 |
| **Minor Arterial** | 1,696 | 255.591 | 9,574.2 | 165.2028 | 124 | **0.751** | **0.485** | 14.45% | 219 | 0.527 |
| **Collector** | 2,768 | 427.137 | 3,627.0 | 104.9402 | 54 | **0.515** | **0.126** | 13.60% | 100 | 0.130 |
| **Local** | 6,069 | 1,015.278 | 1,085.9 | 70.0861 | 40 | **0.571** | **0.039** | 13.89% | 107 | 0.032 |
| **Expressway Ramp** | 259 | 77.967 | 9,656.7 | 47.5057 | 1 | **0.021** | **0.013** | 5.56% | 1 | 0.004 |
| **Expressway** | 38 | 12.063 | 29,660.2 | 26.0240 | 0 | **0.000** | **0.000** | 0.00% | 1 | 0.003 |

### Key Structural Findings by Road Class

- **Arterial Concentration (`82.32%` of Monitored Cyclist KSI):** Major Arterials (`323` monitored cyclist KSI; `493` network-wide) and Minor Arterials (`124` monitored cyclist KSI; `219` network-wide) together account for **82.32%** (`447 / 543`) of all cyclist KSI crashes on AADT-monitored segments and **76.15%** (`712 / 935`) across the entire Centreline network.
- **Divergence Between VKT-Normalized Rate and Spatial Density:**
  - **Minor Arterials** exhibit the highest cyclist KSI rate per unit of motor-vehicle travel at **0.751 cyclist KSI per 100M VKT** (`1.45x` the Major Arterial rate of `0.519`), and cyclists represent **14.45%** of all KSI crashes (`20.63%` of VRU KSI crashes) on Minor Arterials.
  - **Major Arterials** exhibit the highest spatial density at **0.674 cyclist KSI per monitored km** (`0.672` per network km, `1.39x` the Minor Arterial spatial density of `0.485 / km`), driven by higher motor-vehicle volumes (`mean AADT 18,287` vs. `9,574`) and multi-lane arterial conflict points.
  - **Collectors and Local Streets** show moderate rates per 100M motor-vehicle VKT (`0.515` and `0.571`) because motor-vehicle AADT denominators are small (`3,627` and `1,086`), but their spatial density per km is an order of magnitude lower (`0.126` and `0.039` cyclist KSI per monitored km).

---

## 3. High-Risk Toronto Corridors for Cyclist KSI

Saved in `reports/tables/toronto_top_cyclist_ksi_corridors.csv` (evaluating corridors with `>= 2.0 km` monitored length and `>= 0.50` cumulative `100M VKT`, alongside network-wide totals).

| Corridor | Road Class | Monitored km | Mean AADT | Cumulative 100M VKT | Monitored Cyclist KSI | Cyclist KSI / 100M VKT | Cyclist KSI / Monitored km | Network Cyclist KSI | Network Cyclist KSI / km | Rank (Count) | Rank (VKT Rate) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Bloor St W** | Major Arterial | 11.375 | 13,882.5 | 10.7876 | **29** | **2.688** | **2.550** | 36 | 2.161 | 1 | 4 |
| **Yonge St** | Major Arterial | 13.437 | 21,316.1 | 19.7873 | **21** | **1.061** | **1.563** | 26 | 1.477 | 2 | 13 |
| **Danforth Ave** | Major Arterial | 5.059 | 16,370.8 | 5.6193 | **13** | **2.313** | **2.570** | 20 | 2.864 | 3 | 6 |
| **Spadina Ave** | Major Arterial | 2.092 | 15,427.4 | 1.9986 | **12** | **6.004** | **5.736** | 14 | 4.513 | 4 | 1 |
| **Kingston Rd** | Major Arterial | 14.451 | 20,208.0 | 19.9472 | **11** | **0.551** | **0.761** | 15 | 0.736 | 5 | 25 |
| **Avenue Rd** | Major Arterial | 6.372 | 22,431.7 | 9.6844 | **10** | **1.033** | **1.569** | 10 | 1.249 | 6 | 14 |
| **Kennedy Rd** | Major Arterial | 9.675 | 20,948.7 | 14.0238 | **10** | **0.713** | **1.034** | 12 | 0.961 | 7 | 19 |
| **Bathurst St** | Major Arterial | 9.832 | 17,612.0 | 11.9111 | **9** | **0.756** | **0.915** | 18 | 1.003 | 8 | 17 |
| **Lake Shore Blvd W** | Major Arterial | 7.875 | 20,783.1 | 12.7163 | **9** | **0.708** | **1.143** | 15 | 0.693 | 9 | 20 |
| **Dundas St W** | Major Arterial | 8.198 | 18,383.1 | 10.2462 | **8** | **0.781** | **0.976** | 15 | 1.122 | 10 | 16 |
| **Keele St** | Major Arterial | 9.384 | 21,024.8 | 14.2715 | **8** | **0.561** | **0.853** | 9 | 0.686 | 11 | 24 |
| **Dupont St** | Major Arterial | 2.000 | 13,055.9 | 1.7751 | **7** | **3.943** | **3.500** | 9 | 1.892 | 12 | 2 |
| **Bay St** | Major Arterial | 2.785 | 13,876.4 | 2.6650 | **7** | **2.627** | **2.514** | 9 | 2.440 | 13 | 5 |
| **Jane St** | Major Arterial | 10.760 | 17,476.2 | 13.2917 | **7** | **0.527** | **0.651** | 8 | 0.557 | 14 | 26 |
| **St Clair Ave W** | Major Arterial | 6.338 | 10,401.3 | 4.6604 | **6** | **1.287** | **0.947** | 8 | 0.906 | 15 | 11 |
| **Dundas St E** | Minor Arterial | 2.196 | 10,230.2 | 1.5013 | **5** | **3.331** | **2.276** | 6 | 1.778 | 18 | 3 |
| **Sherbourne St** | Minor Arterial | 2.300 | 8,268.7 | 1.4468 | **3** | **2.074** | **1.304** | 3 | 1.179 | 29 | 7 |
| **Gerrard St E** | Minor Arterial | 2.140 | 10,332.8 | 1.4594 | **3** | **2.056** | **1.402** | 11 | 1.207 | 30 | 8 |
| **Spadina Rd** | Minor Arterial | 2.568 | 10,090.9 | 1.8309 | **3** | **1.639** | **1.168** | 3 | 0.750 | 31 | 9 |
| **Davenport Rd** | Minor Arterial | 2.835 | 10,815.3 | 2.0387 | **3** | **1.472** | **1.058** | 9 | 1.786 | 32 | 10 |
| **College St** *(ref)* | Major Arterial | 0.067 | 7,321.7 | 0.0323 | 0 | 0.000 | 0.000 | **20** | **4.842** | — | — |
| **Harbord St** *(ref)* | Minor Arterial | 1.079 | 9,663.9 | 0.7105 | 0 | 0.000 | 0.000 | **1** | **0.458** | — | — |

### Corridor-Level Diagnostics

1. **Extreme Exposure-Normalized Risk on Downtown/Midtown Arterials:** `Spadina Ave` (`6.004` cyclist KSI / 100M VKT; `5.736 / km`), `Dupont St` (`3.943 / 100M VKT`), `Dundas St E` (`3.331 / 100M VKT`), `Bloor St W` (`2.688 / 100M VKT`; `29` monitored / `36` network cyclist KSI), `Bay St` (`2.627 / 100M VKT`), and `Danforth Ave` (`2.313 / 100M VKT`; `13` monitored / `20` network cyclist KSI) exhibit cyclist KSI rates **4.4x to 11.5x** the citywide monitored average (`0.520 / 100M VKT`).
2. **Why Both VKT-Normalized Rates and Network Linear Density Are Required:** `College St (Major Arterial)` records **20 network-wide cyclist KSI collisions across 4.130 km (`4.842 cyclist KSI / km`, #3 citywide by total count)**, but only `0.067 km` (1 segment) had a matched 24-hour midblock AADT study in the short-term volume count program. Relying solely on AADT-matched segments would miss `College St`, whereas combining `cyclist_ksi_per_100m_vkt` with `network_cyclist_ksi_per_km` captures both volume-normalized risk and unmonitored streetcar corridors. By contrast, `Harbord St (Minor Arterial)` (`2.182 km`, `1.079 km` monitored) records only `1` network cyclist KSI collision (`0.458 / km`).

---

## 4. National Co-Involved Vehicle Lethality & Typology Discrimination Synthesis

Linking the national NCDB microdata (`data/derived/build.duckdb`, `68,687` unique bicycle collisions and `614` fatal bicycle collisions across `2010–2021`) with the national `M2_full_typology` severity model (`typology_odds_ratios.csv`, `typology_subgroup_performance.csv`) explains **why** arterial corridor co-exposure with heavy vehicles is disproportionately lethal:

| Co-Involved Vehicle Group (`2010–2021`) | Unique Bicycle Collisions | Share of Bicycle Collisions (%) | Fatal Bicycle Collisions | Share of Fatal Bicycle Collisions (%) | Collision Fatality Rate (%) | Lethality Multiplier vs. Light-Duty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Light-duty vehicle (`V_TYPE=01`)** | 61,698 | **89.82%** | 437 | 71.17% | **0.708%** | **1.00x (ref)** |
| **Cargo or other light truck/van (`V_TYPE=05,06`)** | 2,415 | 3.52% | 34 | 5.54% | **1.408%** | **1.99x** |
| **Bus (`V_TYPE=09,10,11`)** | 918 | 1.34% | 16 | 2.61% | **1.743%** | **2.46x** |
| **Heavy unit truck (`V_TYPE=07`)** | 1,102 | 1.60% | 84 | 13.68% | **7.623%** | **10.76x** |
| **Road tractor (`V_TYPE=08`)** | 307 | 0.45% | 41 | 6.68% | **13.355%** | **18.86x** |
| **Heavy freight combined (`V_TYPE=07,08`)** | 1,409 | **2.05%** | 125 | **20.36%** | **8.872%** | **12.53x** |

### National `M2_full_typology` Bicyclist Severity Performance

- **Out-of-Time Discrimination Lift:** On the `2017–2019` validation split (`n = 14,940` bicyclist collisions, `128` fatal, `0.857%` fatal), adding vehicle and VRU typology features (`M2_full_typology` vs. `M0_baseline`) lifts `ROC-AUC` from **0.6901 to 0.7852 (+0.0951)** and doubles `PR-AUC` from **0.0308 to 0.0648 (2.10x)**. On the `2020–2021` pandemic test split (`n = 8,885`, `98` fatal, `1.103%` fatal), `ROC-AUC` improves from **0.6810 to 0.7576 (+0.0766)** and `PR-AUC` improves from **0.0359 to 0.0475 (+32.3%)**.
- **Heavy Freight × VRU Interaction:** In the national logistic severity model, `has_road_tractor` carries an adjusted odds ratio of **6.4277**, `has_heavy_truck` carries **3.2306**, and the explicit `heavy_freight_x_vru` interaction adds a multiplicative **2.5716** odds ratio (`12.455%` unadjusted fatality rate across all heavy-freight × VRU collisions; `15.475%` in the `2020–2021` test split).
- **Corridor Co-Occurrence:** In Toronto's monitored corridor table, major arterials with high cyclist KSI counts also carry substantial heavy-truck KSI burdens — notably `Yonge St` (`25` heavy-truck KSI, `21` cyclist KSI), `Keele St` (`21` heavy-truck KSI, `8` cyclist KSI), `Spadina Ave` (`20` heavy-truck KSI, `12` cyclist KSI), `St Clair Ave W` (`18` heavy-truck KSI, `6` cyclist KSI), `Bathurst St` (`15` heavy-truck KSI, `9` cyclist KSI), and `Bloor St W` (`8` heavy-truck KSI, `29` cyclist KSI).

---

## 5. Methodological Boundaries

- **Motor-Vehicle VKT vs. Bicycle Volume Denominators:** `cyclist_ksi_per_100m_vkt` normalizes cyclist KSI occurrences by cumulative motor-vehicle travel (`AADT × 365.25 × length_km × 18 years / 10^8`), measuring cyclist severe harm per unit of motor-vehicle traffic exposure on each corridor. It does **not** divide by bicycle trip counts or bicycle-kilometres traveled (`BKT`), which are not available system-wide across all 14,410 Centreline segments. High `cyclist_ksi_per_100m_vkt` on downtown arterials (`Spadina Ave`, `Bloor St W`, `Danforth Ave`) reflects both high cyclist volumes and frequent motor-vehicle conflict density.
- **Co-Involvement vs. Fault:** In the national NCDB microdata, co-involvement indicates that a vehicle type was recorded in the same collision event (`(source_id, C_YEAR, C_CASE)`); it does not establish which unit struck the bicyclist or legal fault.
