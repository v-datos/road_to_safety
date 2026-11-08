# Condition–severity descriptive findings

The cohort contains **2,949,846 candidate collisions**, including **47,793 fatal collisions** (1.6202%), from the selected 1999–2021 NCDB releases. These are fatal/injury collisions, not all crashes or traffic exposure.

## Methods and denominators

Each candidate collision contributes once to every condition table. Fatal proportion is `fatal_collisions / collisions` within that exact field/category/year; injury collisions are the complement. This measures recorded severity conditional on a collision being in the fatal/injury extract. It does not measure the chance of having a crash in a condition. No weighting by source person records, deletion of unknowns, or significance tests are used.

Code labels were checked against the archived official NCDB data dictionary, English pages 4–6. Sand/gravel/dirt means debris, not pavement construction. Visibility limitation includes drifting snow, fog, smog, dust, smoke and mist. Icy includes packed snow. `Q/QQ` means other; `U/UU` means unknown; `X/XX` means jurisdiction unavailable. Each is distinct. No unavailable or blank values occur in these five fields in this cohort.

95% Wilson intervals provide a familiar binomial precision description, not design-based confidence intervals for the complete Canadian collision population. Administrative coverage, coding changes, selection and dependence can dominate that precision. Sparse groups are flagged when n<100 or fatal collisions<5, without removing them. Absent year/category combinations have no observed collisions and are absent from the annual condition table; they are not zero fatal-proportion observations.

## Main descriptive signals

Clear/sunny conditions account for 32,538/2,038,632 (1.596%) fatal/total collisions and 68.08% of the cohort’s fatal collisions. Visibility limitation has 1,255/44,517 (2.819%); strong wind has 257/9,433 (2.724%). Rain has 3,911/285,907 (1.368%) and snowing has 2,737/188,959 (1.448%). These comparisons are not evidence that precipitation reduces crash likelihood or mortality.

Dry/normal surfaces have 32,581/1,920,788 (1.696%); wet surfaces have 7,342/515,894 (1.423%). Sand/gravel/dirt debris has 578/17,080 (3.384%), muddy surfaces 130/3,503 (3.711%), and flooding 9/232 (3.879%). Flooding’s small denominator and oil’s low fatal count (2/851 (0.235%)) make extreme rankings fragile. Oil is explicitly flagged sparse.

Curved/gradient alignment has 4,542/131,584 (3.452%), compared with 27,522/2,063,954 (1.333%) on straight/level alignments. This is a hypothesis for later multivariable severity modeling, not an isolated effect of curvature or gradient.

## Pooled comparisons

### Weather (`C_WTHR`)

| Code | Category | Collisions | Fatal | Injury | Fatal % | Wilson 95% % | Sparse |
|---|---|---:|---:|---:|---:|---:|---|
| 6 | Visibility limitation | 44,517 | 1,255 | 43,262 | 2.819 | 2.669–2.977 | No |
| 7 | Strong wind | 9,433 | 257 | 9,176 | 2.724 | 2.415–3.073 | No |
| Q | Other | 6,775 | 162 | 6,613 | 2.391 | 2.053–2.783 | No |
| 2 | Overcast, no precipitation | 312,852 | 6,008 | 306,844 | 1.920 | 1.873–1.969 | No |
| 5 | Freezing rain, sleet, hail | 17,362 | 292 | 17,070 | 1.682 | 1.501–1.884 | No |
| 1 | Clear and sunny | 2,038,632 | 32,538 | 2,006,094 | 1.596 | 1.579–1.613 | No |
| 4 | Snowing (excluding drifting snow) | 188,959 | 2,737 | 186,222 | 1.448 | 1.396–1.503 | No |
| U | Unknown | 45,409 | 633 | 44,776 | 1.394 | 1.290–1.506 | No |
| 3 | Raining | 285,907 | 3,911 | 281,996 | 1.368 | 1.326–1.411 | No |

### Road surface (`C_RSUR`)

| Code | Category | Collisions | Fatal | Injury | Fatal % | Wilson 95% % | Sparse |
|---|---|---:|---:|---:|---:|---:|---|
| 9 | Flooded | 232 | 9 | 223 | 3.879 | 2.054–7.207 | No |
| 7 | Muddy | 3,503 | 130 | 3,373 | 3.711 | 3.134–4.390 | No |
| 6 | Sand/gravel/dirt debris | 17,080 | 578 | 16,502 | 3.384 | 3.123–3.666 | No |
| Q | Other | 87,977 | 1,568 | 86,409 | 1.782 | 1.697–1.872 | No |
| 1 | Dry, normal | 1,920,788 | 32,581 | 1,888,207 | 1.696 | 1.678–1.715 | No |
| U | Unknown | 37,623 | 569 | 37,054 | 1.512 | 1.394–1.641 | No |
| 4 | Slush, wet snow | 42,227 | 618 | 41,609 | 1.464 | 1.353–1.583 | No |
| 2 | Wet | 515,894 | 7,342 | 508,552 | 1.423 | 1.391–1.456 | No |
| 5 | Icy (including packed snow) | 183,037 | 2,522 | 180,515 | 1.378 | 1.325–1.432 | No |
| 3 | Snow (fresh, loose) | 140,634 | 1,874 | 138,760 | 1.333 | 1.274–1.394 | No |
| 8 | Oil (including spilled/applied liquid) | 851 | 2 | 849 | 0.235 | 0.064–0.853 | Yes |

### Road configuration (`C_RCFG`)

| Code | Category | Collisions | Fatal | Injury | Fatal % | Wilson 95% % | Sparse |
|---|---|---:|---:|---:|---:|---:|---|
| 7 | Passing or climbing lane | 613 | 32 | 581 | 5.220 | 3.722–7.276 | No |
| 4 | Railroad level crossing | 11,870 | 453 | 11,417 | 3.816 | 3.486–4.176 | No |
| 10 | Freeway express lane | 248 | 7 | 241 | 2.823 | 1.374–5.711 | No |
| 1 | Non-intersection | 1,169,341 | 28,522 | 1,140,819 | 2.439 | 2.411–2.467 | No |
| 6 | Tunnel or underpass | 3,282 | 75 | 3,207 | 2.285 | 1.827–2.855 | No |
| 5 | Bridge, overpass, viaduct | 24,229 | 542 | 23,687 | 2.237 | 2.058–2.431 | No |
| QQ | Other | 95,746 | 1,807 | 93,939 | 1.887 | 1.803–1.975 | No |
| UU | Unknown | 234,461 | 3,098 | 231,363 | 1.321 | 1.276–1.368 | No |
| 3 | Intersection with private entrance/exit | 128,006 | 1,314 | 126,692 | 1.027 | 0.973–1.083 | No |
| 2 | Intersection of public roadways | 1,273,402 | 11,879 | 1,261,523 | 0.933 | 0.916–0.950 | No |
| 8 | Ramp | 7,102 | 56 | 7,046 | 0.789 | 0.608–1.022 | No |
| 9 | Traffic circle | 1,546 | 8 | 1,538 | 0.517 | 0.262–1.018 | No |

### Road alignment (`C_RALN`)

| Code | Category | Collisions | Fatal | Injury | Fatal % | Wilson 95% % | Sparse |
|---|---|---:|---:|---:|---:|---:|---|
| 4 | Curved with gradient | 131,584 | 4,542 | 127,042 | 3.452 | 3.355–3.552 | No |
| 3 | Curved and level | 227,733 | 7,250 | 220,483 | 3.184 | 3.112–3.256 | No |
| 6 | Bottom of hill or gradient | 19,227 | 529 | 18,698 | 2.751 | 2.529–2.992 | No |
| 5 | Top of hill or gradient | 25,064 | 660 | 24,404 | 2.633 | 2.442–2.839 | No |
| 2 | Straight with gradient | 274,692 | 5,455 | 269,237 | 1.986 | 1.934–2.039 | No |
| 1 | Straight and level | 2,063,954 | 27,522 | 2,036,432 | 1.333 | 1.318–1.349 | No |
| Q | Other | 14,738 | 166 | 14,572 | 1.126 | 0.968–1.310 | No |
| U | Unknown | 192,854 | 1,669 | 191,185 | 0.865 | 0.825–0.908 | No |

### Traffic control (`C_TRAF`)

| Code | Category | Collisions | Fatal | Injury | Fatal % | Wilson 95% % | Sparse |
|---|---|---:|---:|---:|---:|---:|---|
| 16 | Railway signs only | 672 | 53 | 619 | 7.887 | 6.080–10.172 | No |
| 15 | Railway signals/gates | 2,091 | 108 | 1,983 | 5.165 | 4.296–6.199 | No |
| 12 | Road markings | 1,862 | 81 | 1,781 | 4.350 | 3.514–5.374 | No |
| 10 | Reduced speed zone | 1,439 | 58 | 1,381 | 4.031 | 3.131–5.175 | No |
| 5 | Warning sign | 2,449 | 84 | 2,365 | 3.430 | 2.779–4.227 | No |
| 11 | No passing zone sign | 2,156 | 66 | 2,090 | 3.061 | 2.413–3.876 | No |
| 17 | Control device not specified | 1,841 | 42 | 1,799 | 2.281 | 1.692–3.069 | No |
| 18 | No control present | 1,616,440 | 36,281 | 1,580,159 | 2.245 | 2.222–2.267 | No |
| 2 | Traffic signals flashing | 8,925 | 171 | 8,754 | 1.916 | 1.652–2.222 | No |
| QQ | Other | 42,317 | 727 | 41,590 | 1.718 | 1.598–1.846 | No |
| UU | Unknown | 134,811 | 1,936 | 132,875 | 1.436 | 1.374–1.501 | No |
| 3 | Stop sign | 314,264 | 3,793 | 310,471 | 1.207 | 1.169–1.246 | No |
| 7 | Police officer | 897 | 10 | 887 | 1.115 | 0.607–2.040 | No |
| 6 | Pedestrian crosswalk | 22,781 | 200 | 22,581 | 0.878 | 0.765–1.008 | No |
| 8 | School guard/flagman | 10,834 | 88 | 10,746 | 0.812 | 0.660–1.000 | No |
| 13 | Stopped school bus, signals flashing | 1,646 | 12 | 1,634 | 0.729 | 0.418–1.270 | No |
| 1 | Traffic signals operational | 738,657 | 3,851 | 734,806 | 0.521 | 0.505–0.538 | No |
| 4 | Yield sign | 45,466 | 231 | 45,235 | 0.508 | 0.447–0.578 | No |
| 9 | School crossing | 298 | 1 | 297 | 0.336 | 0.059–1.876 | Yes |

## Year composition and stability sensitivity

The year-standardization table applies the same annual weights to every category: each year’s share of all cohort collisions. It averages within-year category fatal proportions. This is a descriptive check of changing year composition only; it does not control weather, speed, road type, location or road-user mix. Estimates are withheld when a category is absent in any year. The pooled estimate remains the primary observed cohort proportion. Observed sparse years count annual cells with n<100 or fatal<5, even when the pooled group is not sparse. The largest shifts below include railway signs only and passing/climbing lanes, both sparse in 23/23 years, and reduced speed zones, sparse in 22/23 years. These shifts are fragile descriptive sensitivities, not evidence of reliable year-composition effects.

| Field | Category | Pooled % | Common-year-weighted % | Difference, percentage points | Sparse years / observed | Any sparse year |
|---|---|---:|---:|---:|---:|---|
| C_TRAF | Railway signs only | 7.887 | 8.392 | +0.505 | 23/23 | Yes |
| C_TRAF | Reduced speed zone | 4.031 | 4.460 | +0.429 | 22/23 | Yes |
| C_RALN | Other | 1.126 | 1.424 | +0.297 | 8/23 | Yes |
| C_RCFG | Passing or climbing lane | 5.220 | 5.477 | +0.257 | 23/23 | Yes |
| C_RALN | Bottom of hill or gradient | 2.751 | 2.964 | +0.213 | 0/23 | No |
| C_TRAF | Warning sign | 3.430 | 3.225 | -0.205 | 17/23 | Yes |
| C_RSUR | Unknown | 1.512 | 1.677 | +0.164 | 0/23 | No |
| C_RALN | Top of hill or gradient | 2.633 | 2.795 | +0.162 | 0/23 | No |
| C_TRAF | No passing zone sign | 3.061 | 3.219 | +0.158 | 20/23 | Yes |
| C_TRAF | Police officer | 1.115 | 0.984 | -0.131 | 23/23 | Yes |
| C_WTHR | Other | 2.391 | 2.515 | +0.124 | 4/23 | Yes |
| C_WTHR | Strong wind | 2.724 | 2.809 | +0.085 | 1/23 | Yes |

381 of 1,337 observed year/category cells meet the sparse rule. These include supporting road configuration and traffic-control groups, so small annual cells should not be ranked as stable risk factors.

## Interpretation and limitations

Condition comparisons are observational and unadjusted. Higher fatal proportions can reflect speed, urban/rural mix, crash type, participants, time of day, emergency response, or selective reporting rather than an independent condition effect. A common condition can contribute many fatal collisions while having a lower conditional fatal proportion. The analysis cannot justify a claim that snow, wet pavement, traffic signals or other recorded conditions prevent or cause deaths. Policy proposals require adjustment, exposure and local evidence.

The candidate collision identity is release-scoped; source key semantics remain undocumented. The selected historic releases do not reconcile exactly to the newer national publication series, so these results describe the prepared microdata cohort. No precise geographic mapping is possible from its released fields. See the main descriptive analysis for source-year missingness and temporal patterns.

## Reproduction and checks

Run `.venv/bin/python -m road_to_safety.analyze_conditions` from the project directory. Outputs: `reports/tables/eda_condition_pooled.csv`, `eda_condition_by_year.csv`, `eda_condition_year_standardization.csv`; five `reports/figures/conditions_*.png` figures. The producer asserts that every field reconciles to the complete collision and fatal totals and that every field/year reconciles to that year’s collision denominator. Inputs are read-only; the preparation data and validation outputs are unchanged.
