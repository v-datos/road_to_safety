# First descriptive trend analysis

Completed 2026-10-15. The analysis describes the public NCDB release covering 1999–2021. **It does not answer the intended 2016–2025 question.** The historical decade is 2012–2021; the available part of the target period is 2016–2021.

## Findings

| Road-tractor measure | 2012 | 2021 | Change |
| --- | ---: | ---: | ---: |
| Fatal or injury collision events | 3,300 | 2,276 | −31.03% |
| Fatal collision events | 197 | 169 | −14.21% |
| Injury collision events | 3,103 | 2,107 | −32.10% |
| Fatal share of casualty collisions | 5.97% | 7.43% | +1.46 percentage points |

For 2016–2021, casualty events fell from 3,009 to 2,276 (−24.36%), fatal events from 193 to 169 (−12.44%), and fatal share rose from 6.41% to 7.43%. These are observed release counts; the small 2016 published benchmark difference is retained in the full sensitivity table.

Both fatal and injury events fell in the historical endpoint comparison. The higher fatal share arises because injury events fell faster. It does not establish more people killed per event, higher risk per kilometre, or the reasons for the change.

Fatal share also rose for heavy unit truck events (3.68%→4.27%) and collisions without recorded tractors (1.36%→1.79%). The pattern is therefore not unique to tractors. These comparison groups overlap: a collision can involve types 07 and 08, and the no-recorded-tractor group includes heavy trucks, other vehicles and unknown types. It is not a car-only comparison.

## Period and data-quality sensitivity

- **2020:** the observed tractor count fell 26.09% from 2019 to 2020 and rebounded 7.26% in 2021, remaining 20.72% below the observed 2019 count. The pre-2020 comparison, 2012–2019, shows a smaller 13.00% casualty-event decline. Do not interpret the 2021 endpoint as an undisturbed long-run trend or infer a causal pandemic effect.
- **Strict filtering:** the main 2012–2021 and 2016–2021 patterns survive removal of flagged events. The tiny 2020–2021 fatal-share change reverses direction under strict filtering, so that one-year direction is not emphasized.
- **2019 benchmark:** observed 2019 counts are 192 fatal and 2,679 injury events; the separately published Transport Canada table has 196 and 2,581. The nearly flat 2016–2019 fatal-event direction changes under that alternative. The full report keeps both series separate, without modifying event records.
- **Unknown vehicle types:** the exported known-type comparator sensitivity removes events with an unspecified type. This cannot guarantee complete national ascertainment or turn the comparator into passenger cars.

The analysis uses no fitted model, p-value or sampling confidence interval. These are complete observed counts within this release; source completeness, revisions, classification and exposure are the material uncertainties. No person casualty totals or exposure-adjusted rates are calculated.

## Deliverables and verification

- [Full findings and methods](../reports/trends/findings.md)
- [Executed analysis notebook](../notebooks/02_descriptive_trends.ipynb)
- [Annual group and subset counts](../reports/trends/annual_counts.csv)
- [Period comparisons](../reports/trends/period_changes.csv)
- [Strict sensitivity](../reports/trends/strict_sensitivity.csv)
- [Published benchmark comparison](../reports/trends/benchmark_comparison.csv)
- [Machine-readable summary and provenance](../reports/trends/summary.json)

The three figures are available as PNG and SVG under `reports/trends/`: `tractor_counts`, `fatal_share` and `indexed_comparison`. Their input series are exported in CSV. The analyst verified unique event keys, all 23 years, severity arithmetic and agreement with the dataset build. An independent statistical reviewer reproduced all **184 annual group/subset rows** directly from the collision Parquet table. The notebook reruns the analysis and independently checks observed tractor annual totals; all six code cells execute successfully. Final standalone figures were visually inspected for readable labels, scales and legends.

Reproduce from the repository root:

```bash
uv sync --extra notebook --extra analysis
PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib \
  .venv/bin/python -m truck_collisions.analyze_trends
```

Raw and derived collision data are unchanged. The analysis module is `src/truck_collisions/analyze_trends.py`. Generated reports and figures are ignored by Git and recreated by this command; this document and the executed notebook preserve the project handoff.

## Next analytical gates

Validate person identities and casualty counts before answering who dies in tractor-involved collisions. Review the modeled tractor-trailer kilometre estimates before estimating exposure rates. Then compare crash configuration, weather, surface and time patterns with appropriate missingness checks. The source gap for 2022–2025 and the unresolved 2019 publication difference remain open.
