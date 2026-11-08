# Temporal descriptive analysis: selected NCDB releases, 1999–2021

## Population, grain, and denominator

This analysis describes **2,949,846 candidate fatal/injury collisions**, with **47,793 fatal collisions** and **2,902,053 injury collisions**, in the validated collision-level Parquet. The pooled fatal-collision proportion is **1.620%**. One row is a release-scoped candidate collision `(source_id, C_YEAR, C_CASE)`, not an individual casualty or a uniquely verified real-world event across multiple releases. These selected releases include one source per collision year; no dashboard totals or newer publications are appended.

Every displayed proportion is `fatal_collisions / eligible_collisions` for that category. All current candidate collisions have an eligible fatal-versus-injury outcome. Unknown temporal codes remain separate categories, with their own eligible denominators; they are excluded only from the stated-category chart panels. Therefore, chart populations differ slightly across temporal fields. Unknown target values would remain in candidate counts but not the eligible denominator. Counts and proportions are neither per-trip/per-kilometre rates nor the probability that a collision occurs. There is no noncollision/exposure population.

Official English dictionary pages 1–2 establish month codes 01–12, weekday 1=Monday through 7=Sunday, and hour 00=midnight–00:59 through 23=23:00–23:59. Numeric source codes were already normalized during preparation. `U/UU` means unknown, `X/XX` means the jurisdiction does not provide the element. There are no observed unavailable codes in these temporal fields. No full collision date or jurisdiction is available; reported hours are used as supplied with no time-zone conversion.

## Annual series

Candidate collision counts peak in **2002 (156,415)** and reach the minimum in **2020 (79,990)**. The count rises to **83,590 in 2021**. Fatal proportions reach their minimum in **2015 (1.416%; 1,693/119,550)** and their maximum in **2020 (2.003%; 1,602/79,990)**; **2021 is 1.948% (1,628/83,590)**. The change from 2019 to 2020 combines a much smaller reported collision denominator (104,630 to 79,990) with a much smaller change in fatal-collision counts (1,620 to 1,602). This descriptive pattern does not identify why counts or case mix changed.

These are annual release-specific records. They do not reconcile to every later aggregate publication; the acquisition audit documented revision/coverage differences. The sharp 2020–2021 shift warrants chronological validation and a separate late-period sensitivity check in eventual modeling. No causal explanation or national safety-effect estimate is inferred.

| Collision year | Candidate collisions | Fatal collisions | Fatal proportion |
|---|---:|---:|---:|
| 1999 | 151,315 | 2,632 | 1.739% |
| 2000 | 155,838 | 2,548 | 1.635% |
| 2001 | 151,438 | 2,415 | 1.595% |
| 2002 | 156,415 | 2,583 | 1.651% |
| 2003 | 152,980 | 2,487 | 1.626% |
| 2004 | 147,588 | 2,438 | 1.652% |
| 2005 | 148,111 | 2,551 | 1.722% |
| 2006 | 145,103 | 2,586 | 1.782% |
| 2007 | 141,070 | 2,455 | 1.740% |
| 2008 | 129,764 | 2,193 | 1.690% |
| 2009 | 125,456 | 2,007 | 1.600% |
| 2010 | 125,636 | 2,021 | 1.609% |
| 2011 | 124,199 | 1,849 | 1.489% |
| 2012 | 124,682 | 1,848 | 1.482% |
| 2013 | 122,132 | 1,772 | 1.451% |
| 2014 | 116,292 | 1,675 | 1.440% |
| 2015 | 119,550 | 1,693 | 1.416% |
| 2016 | 118,321 | 1,738 | 1.469% |
| 2017 | 114,412 | 1,698 | 1.484% |
| 2018 | 111,334 | 1,754 | 1.575% |
| 2019 | 104,630 | 1,620 | 1.548% |
| 2020 | 79,990 | 1,602 | 2.003% |
| 2021 | 83,590 | 1,628 | 1.948% |

## Calendar month

August has the largest pooled count (268,582) and highest stated-month fatal proportion (1.896%; 5,092 fatal collisions). April has the fewest candidate collisions (194,556); February has the lowest stated-month fatal proportion (1.286%). Month lengths, travel exposure, weather composition, and year composition differ, so raw counts are not normalized seasonal occurrence rates.

| Calendar month | Candidate collisions | Fatal collisions | Fatal proportion |
|---|---:|---:|---:|
| January | 254,459 | 3,357 | 1.319% |
| February | 216,789 | 2,788 | 1.286% |
| March | 206,982 | 2,877 | 1.390% |
| April | 194,556 | 3,092 | 1.589% |
| May | 233,755 | 3,865 | 1.653% |
| June | 261,304 | 4,343 | 1.662% |
| July | 266,301 | 5,011 | 1.882% |
| August | 268,582 | 5,092 | 1.896% |
| September | 260,595 | 4,589 | 1.761% |
| October | 262,366 | 4,581 | 1.746% |
| November | 260,560 | 4,194 | 1.610% |
| December | 263,485 | 3,999 | 1.518% |
| Unknown | 112 | 5 | 4.464% |

## Meteorological season

Summer (JJA) has the largest pooled count (796,187) and highest fatal proportion (1.814%). Spring has the fewest collisions (635,293); winter has the lowest proportion (1.381%). DJF means January, February and December of the same collision calendar year in the supporting year table; it is a month category, not a continuous cross-year winter cohort. Each season contains three calendar months, without adjustment for day counts or travel.

| Meteorological season | Candidate collisions | Fatal collisions | Fatal proportion |
|---|---:|---:|---:|
| Winter (December–February) | 734,733 | 10,144 | 1.381% |
| Spring (March–May) | 635,293 | 9,834 | 1.548% |
| Summer (June–August) | 796,187 | 14,446 | 1.814% |
| Autumn (September–November) | 783,521 | 13,364 | 1.706% |
| Unknown | 112 | 5 | 4.464% |

## Reported weekday

Friday has the largest count (496,697), while Sunday has the highest fatal proportion (2.148%; 7,211/335,659). Saturday is next (1.985%). Tuesday has the lowest proportion (1.388%). These weekday labels are the reported NCDB values; without full dates, calendar consistency and numbers of each weekday cannot be verified.

| Reported weekday | Candidate collisions | Fatal collisions | Fatal proportion |
|---|---:|---:|---:|
| Monday | 403,917 | 6,040 | 1.495% |
| Tuesday | 426,345 | 5,916 | 1.388% |
| Wednesday | 430,751 | 6,047 | 1.404% |
| Thursday | 450,405 | 6,684 | 1.484% |
| Friday | 496,697 | 7,834 | 1.577% |
| Saturday | 405,546 | 8,052 | 1.985% |
| Sunday | 335,659 | 7,211 | 2.148% |
| Unknown | 526 | 9 | 1.711% |

## Reported hour

16:00–16:59 has the largest count (249,337), followed by 17:00–17:59 (239,474). The highest stated-hour proportion is at 02:00–02:59 (3.915%; 1,591/40,635), followed by 04:00–04:59 (3.893%). 08:00–08:59 has the lowest proportion (1.005%; 1,605/159,760). High-volume afternoon hours and high-proportion overnight hours describe different aspects of the data; neither ranking establishes exposure-adjusted danger.

| Reported hour | Candidate collisions | Fatal collisions | Fatal proportion |
|---|---:|---:|---:|
| 00:00–00:59 | 46,978 | 1,531 | 3.259% |
| 01:00–01:59 | 40,336 | 1,520 | 3.768% |
| 02:00–02:59 | 40,635 | 1,591 | 3.915% |
| 03:00–03:59 | 35,346 | 1,362 | 3.853% |
| 04:00–04:59 | 25,533 | 994 | 3.893% |
| 05:00–05:59 | 31,771 | 1,097 | 3.453% |
| 06:00–06:59 | 68,525 | 1,542 | 2.250% |
| 07:00–07:59 | 120,432 | 1,692 | 1.405% |
| 08:00–08:59 | 159,760 | 1,605 | 1.005% |
| 09:00–09:59 | 123,218 | 1,722 | 1.398% |
| 10:00–10:59 | 129,121 | 1,850 | 1.433% |
| 11:00–11:59 | 150,487 | 1,965 | 1.306% |
| 12:00–12:59 | 178,838 | 2,140 | 1.197% |
| 13:00–13:59 | 177,170 | 2,263 | 1.277% |
| 14:00–14:59 | 192,065 | 2,502 | 1.303% |
| 15:00–15:59 | 234,726 | 2,800 | 1.193% |
| 16:00–16:59 | 249,337 | 2,880 | 1.155% |
| 17:00–17:59 | 239,474 | 2,862 | 1.195% |
| 18:00–18:59 | 180,393 | 2,700 | 1.497% |
| 19:00–19:59 | 137,117 | 2,345 | 1.710% |
| 20:00–20:59 | 108,181 | 2,261 | 2.090% |
| 21:00–21:59 | 100,763 | 2,122 | 2.106% |
| 22:00–22:59 | 82,709 | 1,967 | 2.378% |
| 23:00–23:59 | 65,670 | 1,815 | 2.764% |
| Unknown | 31,261 | 665 | 2.127% |

## Weekday–hour interaction

The paired heatmaps use **2,918,220 collisions** with both weekday and hour stated, including **47,121 fatal collisions**. The remaining **31,626 candidate collisions** are preserved in the joint tables, including combinations where either or both fields are unknown. Do not add the two marginal unknown counts to derive this exclusion, because some records overlap.

All **168 stated weekday–hour cells** are observed and none meets the pooled sparse flag (`eligible_collisions < 100` or `fatal_collisions < 5`). The largest count is **Friday 16:00–16:59 (43,710 collisions; 488 fatal; 1.116%)**. The largest fatal proportion among stated cells is **Friday 04:00–04:59 (167/3,584; 4.660%)**. Searching many cells makes a maximum an exploratory description, not a stable forecast or evidence of a specific mechanism. Sparse flags are retained in all tables and are particularly relevant to year-specific and unknown-code strata. They do not remove data or automatically merge categories.

## Missingness and source-year interpretation

Month has **112 unknown collisions**, weekday **526**, and hour **31,261**. Their respective fatal counts are **5**, **9**, and **665**. Thus missing hour is not safely assumed to have the same fatal proportion as stated hour. Seasonal unknown exactly inherits missing month. Unknown monthly values pool to 4.464% fatal (5/112); this is a small, distinct recording-quality stratum, not a calendar season. Complete year-by-category tables preserve release ID, path and SHA256, enabling the companion missingness/stability analysis to distinguish source-year shifts from pooled composition. No imputation, removal, weighting or adjustment was performed.

All annual counts and fatal counts are preserved in every temporal partition; fatal plus injury equals eligible for every output group. The generation checks all **11 tables** against the passed preparation receipt. Two focused unit tests verify official weekday labels/unknown-state distinction and the eligible-target denominator when an unresolved target exists. The current output is based on the validated full dataset, not sampling. Annual and weekday–hour figures were visually inspected for readable labels and chronological order.

## Reproduction and files

From the project directory run:

```sh
MPLCONFIGDIR=/tmp/road-to-safety-matplotlib .venv/bin/python -m road_to_safety.analyze_temporal
.venv/bin/python -m unittest discover -s tests -p test_analyze_temporal.py -v
```

The executable module is `src/road_to_safety/analyze_temporal.py`. Tables `reports/tables/eda_temporal_annual.csv`, `eda_temporal_month.csv`, `eda_temporal_season.csv`, `eda_temporal_weekday.csv`, `eda_temporal_hour.csv`, and `eda_temporal_weekday_hour.csv` provide pooled counts, eligible counts, fatal/injury counts, fatal proportions, and sparse flags. Each univariate/joint temporal table also has a `_by_year.csv` companion with source provenance (annual already includes provenance). Unknown codes are explicit table rows. A missing combination has no observed collisions; no proportion can be inferred for it. Charts are `reports/figures/temporal_{annual,month,season,weekday,hour,weekday_hour}.png`. The code can be rerun without reading or modifying original raw inputs. Preparation artifacts remain unchanged.

The next modeling phase should define chronological training/validation/test periods and test whether these patterns persist under year stratification and changing reporting completeness. This phase fits no model and claims no causal policy effect.
