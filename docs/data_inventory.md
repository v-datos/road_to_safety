# Inventory of `Collisions/`

Reviewed 2026-10-14. The directory contains **86 files (about 4.3 GB)**: 64 primary files, including `.DS_Store`, and 22 Jupyter checkpoints. File counts below include data and reference files even when they are duplicates. The review inspected file contents, schemas, notebook source cells, metadata, and archive members; it did not validate every analytical result in the notebooks.

## Canadian collision records and dictionary

| File | Contents and assessment |
| --- | --- |
| `NCDB_1999_to_2017.csv` | 6,772,563 **person records**, 1999–2017, 23 columns (including `C_YEAR`, `C_CASE`, `V_ID`, `V_TYPE`, `P_ID`, `C_SEV`, `P_ISEV`). Main historical microdata in this folder. Preserve code fields as strings. |
| `test_2019_dataset_en.csv`, `test_2019_dataset_en copy.csv` | Identical 2019 NCDB person-level extracts, 272,301 records, same 23 columns. The second file is a byte-for-byte copy. |
| `test99_to_2019_dataset_en.csv`, `test99_to_2019_dataset_en copy.csv`, `test99_to_2019_dataset_en (1).csv` | Three identical files. Despite the names, each has 1,048,575 nonblank data rows: all of 1999 and 2000, then part of 2001. With its header, that matches Excel's 1,048,576-row sheet limit; an additional blank line follows. **Never use as a 1999–2019 series.** Leading zeros have also been stripped from numeric-looking codes. |
| `data_dictionary.pdf` | 24-page bilingual NCDB codebook. `V_TYPE=08` is a road tractor with or without a semi-trailer; `07` is a heavy unit truck; `01` includes light pickups. `C_SEV`, `P_ISEV`, and special missing codes need separate treatment. |

The inherited archive omits **2018 and 2020 onward**. The files are person-level: rows, vehicles, collisions, injured people, and fatalities are different units. The subsequent acquisition has added official 2018–2021 sources under `data/raw/ncdb/`, leaving this archive unchanged. See [the acquisition notes](ncdb_acquisition.md), [dataset contract](dataset_contract.md), and [validation findings](dataset_validation.md). The initial 2019 CSV reproduces the archived file's tractor-event count. The subsequent [source repair](source_release_update.md) validates an alternate official XLSX and substantially reduces that discrepancy; the archive and earlier outputs remain preserved.

## NCDB Online aggregate exports

These CSVs are downloaded tables with multirow headers, nested totals, and varying filters. They are useful as cross-checks and historical exploration; none explicitly filters to road tractors.

| Files | Contents |
| --- | --- |
| `col_year.csv` | Annual national collision and fatality counts, 1999–2019. |
| `collision_age_sex_days.csv`, `collision_age_sex_month.csv`, `collisioon_age_sex_hour.csv` | Fatalities by age, sex, and weekday/month/hour. Hour-based table has a smaller total because hour is unavailable for some records. |
| `collision_fecha.csv`, `collision_fecha2.csv`, `collisions_fatalities.csv` | Collision and fatality tables by year, month, weekday, and hour; `collision_fecha.csv` is very wide. |
| `collision_weather_road.csv`, `collision_weather_road_month.csv`, `collision_weather_road_days.csv`, `collision_weather_road_hour.csv` | Collisions and fatalities by road surface and weather, crossed with time. The base and `_month` files are byte-for-byte identical. |
| `road_confg.csv`, `road_user.csv` | Annual fatalities by collision configuration and road user class. |

Totals differ across some exports when an hour or other dimension is required. Preserve each table's filters, measure, and unit before comparing values.

## Exposure and other Statistics Canada tables

Each CSV has a matching `_MetaData.csv` containing its catalogue URL and reference period. These are archived local snapshots and should be refreshed and definition-checked before trend modeling.

| Data file and metadata file | Scope | Relevance |
| --- | --- | --- |
| `vehicle_registration_by_type.csv`, `vehicle_registration_by_type_MetaData.csv` | Table 23-10-0067-01; annual 1999–2019, 14 geographies | Broad vehicle weight classes, not tractor-specific. |
| `vehicle_registration_dec_2023/23100308.csv`, `vehicle_registration_dec_2023/23100308_MetaData.csv` | Table 23-10-0308-01; annual 2017–2022, 14 geographies | Updated registered vehicle weight classes; definitions differ from the older table. |
| `fuel.csv`, `fuel_MetaData.csv` | Table 23-10-0066-01; annual 1987–2019 | Diesel fuel sales are a broad traffic proxy, not truck distance travelled. |
| `new_vehicle_registration.csv`, `new_vehicle_registration_MetaData.csv` | Table 20-10-0021-01; annual 2011–2019 | New light vehicle registrations; weak match to semis. |
| `vehicles sales by type of vehicles.csv`, `vehicles sales by type of vehicles_MetaData.csv` | Table 20-10-0002-01; annual 2010–2019 | New vehicle sales; weak exposure proxy. |
| `vehicles sales.csv`, `vehicles sales_MetaData.csv` | Table 20-10-0001-01; monthly 1946–2020 | General motor vehicle sales; peripheral. |
| `Zero_emission_vehicle_registration_dec_2023/20100025.csv`, `Zero_emission_vehicle_registration_dec_2023/20100025_MetaData.csv` | Table 20-10-0025-01; quarterly 2017–2023 | ZEV registrations; peripheral to the truck collision question. |

`vehicle_registration_by_type.zip`, `vehicle_registration_dec_2023.zip`, and `Zero_emission_vehicle_registration_dec_2023.zip` contain the corresponding data/metadata pairs already extracted above; do not count them as independent observations.

## Canadian reports, research, and notes

| Files | Contents and assessment |
| --- | --- |
| `Canadian Motor Vehicle Traffic Collision Statistics_ 2018.html`, `Canadian Motor Vehicle Traffic Collision Statistics_ 2020.html` | Saved Transport Canada national annual reports. Good reference totals and definitions, but old for the latest decade. The 2020 report separately lists tractor-trailer occupant fatalities, which are **not** all fatalities in crashes involving tractor-trailers. |
| `trans-alberta-traffic-collision-statistics-2018.pdf`, `trans-alberta-traffic-collision-statistics-2018 copy.pdf` | Identical 91-page Alberta report. Tables 7.8–7.12 cover truck tractors and 2018 collision factors. Alberta-specific; do not generalize its factor distribution to Canada. |
| `collision_casualties_alberta.csv`, `mefposigoatrafficcollisioncasualtiescsvv4.02016-01-11.csv` | Identical short Alberta casualty tables, 2001 onward. |
| `PREDICTION OF FATALITIES IN VEHICLE COLLISIONS IN CANADA.pdf`, `3782-Article Text-561569985-1-10-20211008.pdf` | Identical nine-page paper using NCDB 1999–2017 to predict individual fatalities. Background, not evidence about changes in semi collision rates. |
| `collisions_websites.rtf`, `info_collision.rtf` | Informal source links and a short road-safety idea note. Treat links as leads rather than validated data. |

## Exploratory notebooks

| File | Contents and reuse decision |
| --- | --- |
| `Canada_collision_2019.ipynb` | 2019 NCDB exploration, 107 cells. Reads the truncated 1999–2019 file and the separate 2019 file; do not reuse its time-series claims without rebuilding. |
| `Canada_collisions_1999_2017.ipynb` | 118 cells of Canadian descriptive analysis and registration comparisons. Useful code and chart ideas; unit-of-analysis checks are needed. |
| `collisions_1999_2021.ipynb` | 59 cells, mostly NCDB 1999–2017 exploration; filename exceeds the actual local input period. |
| `accidents.ipynb`, `accidents_TS.ipynb`, `Untitled.ipynb` | UK road casualty / DataCamp work. Not Canadian evidence. `accidents_TS.ipynb` also references a missing `tunnel.csv` example file. |
| `USA_collisions.ipynb` | Short US exploration; no Canadian input. |

Notebook outputs are large and may reflect different intermediate code states. Recompute any finding used in the new analysis.

## UK data and codebooks (separate context)

`dft-road-casualty-statistics-accident-1979-2020.csv`, `dft-road-casualty-statistics-accident-2020.csv`, `dft-road-casualty-statistics-casualty-1979-2020.csv`, `dft-road-casualty-statistics-casualty-2020.csv`, `dft-road-casualty-statistics-vehicle-1979-2020.csv`, and `dft-road-casualty-statistics-vehicle-2020.csv` are UK accident/casualty/vehicle tables. Their full-history files contain about 8.60 million, 11.45 million, and 15.35 million rows respectively. `accidents_datacamp.csv` is a 91,199-row 2020 UK accident subset; `lookup_datacamp.csv` and `Road-Safety-Open-Dataset-Data-Guide.xlsx` describe UK fields. Keep out of the Canadian results.

## Checkpoints and housekeeping

`Collisions/.ipynb_checkpoints/` holds 21 files; `Collisions/.ipynb_checkpoints2/` holds one more. Fifteen are byte-for-byte copies of primary data/reference files. Six notebook checkpoints and the `road_user.csv` checkpoint differ from their corresponding primary files; they are earlier working states, not additional data sources. `Collisions/accidents_datacamp.ipynb/` is an empty directory despite its notebook-like name. `.DS_Store` is macOS metadata.

## Source links reviewed

- [Website and live database review](website_database_review.md) records all supplied and archive-linked websites, their relevance, and a direct NCDB Online truck-tractor query.
- [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en), [tutorial](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-1-23-101), [FAQ](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-5-0), [help](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-0-23-101).
- [NCDB Open Government dataset](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) lists downloadable annual records and the dictionary.
- [Transport Canada commercial vehicle collisions, 2012–2021](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021) is the closest published national benchmark for the topic.
- [Transport Canada road safety statistics, 2004–2023](https://tc.canada.ca/en/binder/road-safety-statistics) provides later national commercial vehicle totals, though broader than semis.
