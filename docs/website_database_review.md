# Website and live database review

Reviewed 2026-10-14. This records the URLs supplied in the request, saved in the two RTF notes, or cited in the Canadian notebooks. Direct source pages are preferred to secondary summaries. A page that did not load is listed as unverified, not treated as missing data.

## National Collision Database: the five supplied links

| Supplied URL | What it is | Decision |
| --- | --- | --- |
| [NCDB Online homepage](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en) | Entry to an interactive **national aggregate table builder** for fatal and injury collisions. It is not a bulk record download. | Primary source for available national tables. |
| [Tutorial](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-1-23-101) | Explains the four-step wizard, measures, downloads, and that fatalities filtered to a vehicle type are deaths **in that vehicle**. It describes contributing-factor categories at collision and vehicle level. | Primary guide to interpreting output; note that the live variable selector reviewed today did not display the tutorial's contributing-factor sections E/F. |
| [FAQ](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-5-0) | Explains national-only coverage, source jurisdictions, and collision/vehicle/person fields; links to underlying data. | Primary scope reference. |
| [Help](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-0-23-101) | Documents variables, totals, layout, five export formats, and download cell limits. | Primary query reference. |
| [Dynamic `wk=0#o106` link](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&wk=0#o106) | Another state of the homepage, not a separate database or saved analysis. | Do not count as an independent source. |

### What the live database actually exposes

I used the live four-step wizard. Its Year details listed **1999–2023** (plus an “All years” item). Vehicle Type includes “Truck tractor,” and the local NCDB dictionary maps that to `V_TYPE=08`. The current wizard also exposes collision severity, weather, road surface, road configuration, light condition, road class, speed limit, vehicle maneuver, and first impact location. Some fields are absent from the older local 23-column extracts.

The query selected **2014–2023**, **Vehicle Type = Truck tractor**, and **Collision Sev = fatal and injury**, with no year or vehicle-type totals. The only offered measures in this configuration were **Number of vehicles**, **Number of injured**, and **Number of fatalities**. The table identified its source as “Transport Canada - Road Safety, NCDB - August 12, 2025.” The first and last rows for all severity combined were:

| Year | Truck tractors involved in casualty collisions | People injured in those tractors | People killed in those tractors |
| --- | ---: | ---: | ---: |
| 2014 | 3,789 | 1,265 | 32 |
| 2023 | 2,392 | 782 | 30 |

These are **vehicle involvement and tractor-occupant casualty counts**, not the number of unique collisions involving a tractor and not deaths of other road users in those collisions. They are a useful preliminary signal and validation series, not a final accident trend. A collision can involve more than one tractor; fatalities in the other vehicle are excluded by this vehicle-level filter. The displayed table had 30 cells per row and offered a CSV export; the attempted download did not complete in this review, so no local copy of this query is claimed.

The [Open Government NCDB dataset](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) is the separate underlying-record source. The initial web-page read returned 403, but the later acquisition successfully inspected the complete package metadata and downloaded annual files through **2021**. No later annual resource was listed. The English 2021 resource has no URL; the French CSV is usable after explicit header translation and CP1252 decoding. See [the acquisition record](ncdb_acquisition.md) for URLs, hashes, dates, and source issues.

Transport Canada's [commercial vehicle fact sheet, 2012–2021](https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021) gives unique fatal and injury collision counts for tractor-trailers through 2021, as well as broader commercial-vehicle exposure rates. Its [road safety statistics table, 2004–2023](https://tc.canada.ca/en/binder/road-safety-statistics) extends national commercial-vehicle totals to 2023 but combines vehicle types. These are benchmark sources, not interchangeable measures.

## Canadian sources found in the notebooks or metadata

| URL | Assessment |
| --- | --- |
| [Transport Canada statistics index](https://tc.canada.ca/en/road-transportation/statistics-data) and [2020 collision report](https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics-2020) | Official summaries and reference definitions. The index currently lists the 2023 national report as the newest annual collision report found in this review. |
| [Statistics Canada vehicle registrations, older table 23-10-0067-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310006701) | Now marked inactive. Its local 1999–2019 file is useful for historical context, but weight classes are not a tractor-specific denominator. |
| [Statistics Canada vehicle registrations, table 23-10-0308-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310030801) | Current annual vehicle registrations by weight/type and fuel; still not an exact tractor-kilometre denominator. |
| [Alberta collision statistics](https://open.alberta.ca/publications/0844-7985) | Official province-level reports; the 2018 PDF is already local. Use for Alberta validation or factor examples, not national trend inference. |
| [Archived NCDB CSV on Transport Canada storage](https://opendatatc.blob.core.windows.net/opendatatc/NCDB_1999_to_2017.csv) | Notebook's source link for the large local historical extract; record checksum and version if reused. |

### Statistics Canada search for 2024–2025 data

A search of Statistics Canada's official tables found **supporting data through 2024 or 2025, but no 2024–2025 collision-event dataset identifying road tractors or semis**. These tables cannot extend the NCDB tractor-collision series. Check release metadata again when the analysis is run, since the tables can be revised.

| Source | Latest reference year found | What it can contribute | Limit |
| --- | ---: | --- | --- |
| [Table 23-10-0308-01, vehicle registrations](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310030801) | 2025 | Annual Canada and provincial fleet context, including heavy-duty and Class 8 categories. The [2025 release](https://www150.statcan.gc.ca/n1/daily-quotidien/260922/dq260922c-eng.htm) was published September 22, 2026. | Registration stock is neither road-tractor vehicle-kilometres nor a semi-only count. Ontario's July 2024 automatic renewal change complicates comparisons, especially for light vehicles. |
| [Table 13-10-0156-01, deaths by external cause](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310015601) | 2024 | Transport-death context by ICD-10 cause, age, and sex. | Death records have no collision identifier or road-tractor involvement flag. The [2025 cause-of-death release is scheduled for March 25, 2027](https://www150.statcan.gc.ca/n1/daily-quotidien/260709/dq260709a-eng.htm). |
| [Table 35-10-0177-01, police-reported crime](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3510017701) | 2025 | Context for reported dangerous/impaired-driving offences. | Criminal offence incidents are not collision events and have no truck-class field. |
| [Table 23-10-0067-01, archived vehicle registrations](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2310006701) | 2019 | Historical fleet context only. | No 2024–2025 observations or collision counts. |

Statistics Canada's [Canadian Vehicle Survey and successor Fuel Consumption Survey](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getMainChange&Id=80421) ended in 2009 and 2014, respectively; no current StatCan heavy-truck vehicle-kilometre series was found. Its [2025 automobile-insurance analysis](https://www150.statcan.gc.ca/n1/pub/11-621-m/11-621-m2025003-eng.htm) displays collision figures only through 2022 and attributes them to Transport Canada. The search for 2024–2025 semi-collision events should therefore continue with Transport Canada and provincial collision-data publishers.

## Transport Canada and provincial follow-up for 2024–2025

Official-source search conducted 2026-10-14. **No verified source supplies a comparable Canada-wide count of unique semi-truck collisions through 2025.** A publication date or portal metadata update must not be mistaken for the collision reference year. Provincial reports use different vehicle classes and counting units.

| Jurisdiction and source | Latest verified collision year | Relevant measure and availability | Comparability limit or gap |
| --- | ---: | --- | --- |
| [Transport Canada road statistics](https://tc.canada.ca/en/road-transportation/statistics-data), [casualties dashboard](https://tc.canada.ca/en/road-transportation/statistics-data/2025/motor-vehicle-casualties-dashboard), and [NCDB open data](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a?res_page=6) | 2023 published collision series; 2021 latest annual bulk file identified | NCDB Online has truck-tractor vehicle involvement through 2023. Bulk files are person records with collision and vehicle fields. | No 2024–2025 national collision release found. Dashboard counts people. The open-data portal's 2025 metadata modification is not a new collision year. |
| [Saskatchewan SGI 2024 vehicle factors](https://sgi.sk.ca/documents/37148/5370559/06%2B-%2BVehicle%2BFactors-2024_FINAL_SECURED.pdf/0401c88e-a6d9-1ff9-9ac9-573b18494082?t=1764949226124) | 2024 | `Semi-Trailer Power Unit`: 1,251 vehicles involved in collisions (1,006 property damage, 221 injury, 24 fatal). Annual report PDFs reach back through 2016. | Vehicle involvements, not unique collisions; no 2025 report found. |
| [BC ICBC 2025 release](https://icbc.com/about-icbc/newsroom/2026-05-26-data), [statistics portal](https://www.icbc.com/about-icbc/newsroom/Statistics) | 2025 | Crash statistics include a `heavy vehicle` category in the released data. | Broader than semis; claims and police records differ. A tractor-only filter and raw schema need inspection. 2025 police/fatality figures were scheduled for fall 2026. |
| [Ontario preliminary 2024 ORSAR](https://www.ontario.ca/files/2026-02/mto-orsar-preliminary-selected-statistics-en-2024-2026-02-05.pdf), [report index](https://www.ontario.ca/document/ontario-road-safety-annual-reports-orsar) | 2024 | `Large Truck`: 1,341 vehicles in fatal/injury collisions (80 fatal, 1,261 injury). | Broader than semis; counts vehicles. Full report index reaches 2022; no 2025 report found. The preliminary page has potentially inconsistent source-year wording to verify with MTO. |
| [Quebec SAAQ 2025 report](https://saaq.gouv.qc.ca/blob/saaq/documents/publications/Bilan-Routier-2025-Faits-Saillants.pdf), [collision-event open data](https://www.donneesquebec.ca/recherche/dataset/rapports-d-accident) | 2025 report; event CSV through 2022 | Report includes casualties in heavy-vehicle collisions; open CSV has one row per collision and vehicle-type fields. | Published 2025 measure is people, not unique semi collisions. The event file's latest year identified is 2022. |
| [Manitoba MPI dashboard](https://www.mpi.mb.ca/manitoba-collision-dashboard/) | Current monthly data | Police and insurance collision reports with time, place, and factor views. | Dashboard warns archived annual reports through 2022 cannot be compared like for like. Tractor filter and downloadable event data are unverified. |
| [Northwest Territories 2024 report](https://www.inf.gov.nt.ca/en/content/2024-nwt-traffic-collision-facts-0), [event-level open data](https://opendata.gov.nt.ca/dataset/collision-data) | 2024 report; raw XLS through 2022 | `Road Tractor`: 12 vehicle involvements in 2024 (7 property damage, 5 injury). | Published figure is vehicles, not unique collisions; no 2025 report found. |
| [PEI collision series](https://www.princeedwardisland.ca/en/information/transportation-infrastructure-and-energy/traffic-related-collisions-injuries-and) | 2025 preliminary | All-vehicle collision totals, including 2,064 for 2025. | No truck type. Its 2024 figure of 1,164 conflicts with 1,724 in the [2024–25 departmental report](https://www.princeedwardisland.ca/sites/default/files/a72a/DTI%20Annual%20Report%20FY%2024-25.pdf); resolve before use. |
| [Alberta collision statistics](https://www.alberta.ca/collision-vehicle-licence-statistics) | 2023 report located | Historical reports distinguish truck tractors. | Direct verification of 2024–2025 releases was blocked; latest year remains unverified. |
| New Brunswick, Nova Scotia, Newfoundland and Labrador, Yukon, Nunavut | Unverified | Official portals searched. | No 2024–2025 semi-specific source verified; this is a research gap, not evidence of absence. |

The most useful next acquisition is collision-level data from Transport Canada and provincial custodians for **2016–2025**, with event ID, tractor-specific vehicle code, severity, year, jurisdiction, and dictionary. SGI and NWT can validate tractor-coded 2024 vehicle involvement; BC needs a class/schema check; Quebec's event-file delay and PEI's conflicting totals need clarification before inclusion.

## Other links saved in `collisions_websites.rtf` and `info_collision.rtf`

| URL | Relevance to this project |
| --- | --- |
| [PLOS One paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0214205) | South Korean older-versus-younger driver study; methodological background only. |
| [IIHS 2020 Status Report](https://www.iihs.org/api/datastoredocument/status-report/pdf/55/2) and [IIHS driver death rates](https://www.iihs.org/ratings/driver-death-rates-by-make-and-model) | US passenger-vehicle model death rates; not a source for Canadian truck collisions. |
| [tests.ca driving statistics](https://tests.ca/driving-statistics/) | Secondary Canadian roundup that largely repeats Transport Canada; trace any useful claim to TC directly. |
| [Brampton community motor vehicle collision rate](https://geohub.brampton.ca/pages/community-mvc-rate) | Municipal dashboard link did not load through the web reader; local-city measure would not represent Canada. |
| [SafetyDawg collision-rate article](https://safetydawg.com/measure-collision-rate-safety-consultant/) | Commercial fleet example of collisions per million miles. Useful intuition, but it uses US FMCSA definitions rather than NCDB definitions. |
| [FHWA appendix](https://safety.fhwa.dot.gov/local_rural/training/fhwasa1109/app_c.cfm) | US road-safety training link did not load; no Canadian data used. |
| [NSC historical deaths and rates](https://injuryfacts.nsc.org/motor-vehicle/historical-fatality-trends/deaths-and-rates/) | US historical series, not Canadian evidence. |
| [Oregon State accident statistics PDF](https://cce.oregonstate.edu/sites/cce.oregonstate.edu/files/pw_accid.pdf) | Legacy US methods link did not load; no data used. |
| [NHTSA FARS](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars) | US fatal-crash census; possible later comparison, not part of the Canadian baseline. |
| [Statistics Canada research data centre link](https://www.statcan.gc.ca/eng/rdc/cvsd-dad-nacrs-omhrs) | Link did not load; its path concerns linked death/hospital data, not the NCDB truck collision series. |
| [Norway road-safety graphic](https://informationisbeautiful.net/beautifulnews/1419-norway-road-safety/) | Inspiration only; no Canadian collision data. |

## Other links embedded in notebooks

The UK notebooks cite the [UK road-accident dataset](https://data.gov.uk/dataset/road-accidents-safety-data) and a [UK forecasting article](https://towardsdatascience.com/time-series-forecasting-for-road-accidents-in-uk-f940e5970988); both are outside the Canadian study. The Canadian notebooks also cite the [Insurance Information Institute's US highway statistics](https://www.iii.org/fact-statistic/facts-statistics-highway-safety), an [NIH-hosted article](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3583287/) that could not be verified through the web reader, and a [Stack Overflow answer](https://stackoverflow.com/a/49238256/5769929) about code, none of which supplies Canadian semi counts. They also cite the NCDB Online tool, Open Government dataset, TC statistics, Alberta reports, and Statistics Canada table already listed above.
