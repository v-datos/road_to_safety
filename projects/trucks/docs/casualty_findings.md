# Who is harmed? Person-level casualty findings

Updated 2026-10-15 after the validated source-version rebuild. See [the repair record](source_release_update.md) for changes to annual 2014–2017 and 2019 inputs and the preserved earlier baseline.

## Scope and conclusion

The analysis reconstructs deaths and nonfatal injuries among **all recorded road users in tractor-involved fatal/injury collisions**, covering 1999–2021. It selects whole collision events containing `V_TYPE=08`, road tractor with or without semitrailer. It does not restrict casualties to people travelling in the tractor. The historical decade comparison is 2012–2021; 2016–2021 is the available part of the intended 2016–2025 study.

**Recorded harm declined overall, but the improvement was uneven.** Other motor vehicle occupants account for most recorded deaths. Tractor-occupant deaths and combined pedestrian/cyclist/motorcyclist deaths were higher at the 2021 endpoint than at the 2012 endpoint. These small subgroup endpoint differences do not establish an underlying trend or its cause.

## Principal results

| Measure | 2012 | 2021 | Change |
| --- | ---: | ---: | ---: |
| All recorded deaths, both resolution scenarios | 233 | 191 | −18.0% |
| Nonfatal injuries, identified consistent-outcome scenario | 4,337 | 2,828 | −34.8% |
| Nonfatal injuries, higher coded-outcome scenario | 4,337 | 2,844 | −34.4% |
| Tractor-occupant deaths | 27 | 30 | +11.1% |
| Other motor vehicle occupant deaths | 181 | 129 | −28.7% |
| Pedestrian + cyclist + motorcyclist deaths | 23 | 30 | +30.4% |

Deaths per 100 recorded tractor-involved casualty collisions increased from **7.06 to 8.39**, while casualty collision counts fell by 31.0%. Fewer events therefore coincided with fewer deaths overall, but deaths fell more slowly. This is a conditional measure among reported casualty events, not a rate per kilometre or among all crashes.

For the available target-period segment, 2016–2021, deaths changed from 217 to 191 (−12.0%); injury declines are 25.1–25.5% across the scenarios. Pre-2020 and disruption/rebound comparisons are reported separately in the full analysis. The 2020 disruption substantially affects endpoint comparisons.

### Who died in 2021?

| Assigned road-user group | Recorded deaths | Share of all 191 deaths |
| --- | ---: | ---: |
| Tractor occupants | 30 | 15.7% |
| Other motor vehicle occupants | 129 | 67.5% |
| Pedestrians | 21 | 11.0% |
| Cyclists | 3 | 1.6% |
| Motorcyclists | 6 | 3.1% |
| Other/unknown | 2 | 1.0% |

Across 2012–2021, other motor vehicle occupants account for **1,581 of 2,206 identified, consistent-outcome deaths (71.7%)**. This share is calculated from this extract rather than imported from a broader commercial-vehicle statistic. Other motor vehicles include passenger vehicles and other motorized vehicle classes; this is not a car-only group. Unknown and ambiguous categories remain in the denominator. The two other/unknown deaths in 2021 cannot be assigned to people outside the tractor with certainty.

## Record handling and validation

The build accounts for 212,532 input person/placeholder rows in 80,540 tractor-involved events. It retains record alternatives and original multiplicity, excludes dummy people, preserves pedestrians assigned a dummy vehicle, and keeps unknown identities without inventing person IDs. It identifies 43 keys with conflicting severity and 120 with ambiguous road-user assignment over the full period. Numeric person keys are operational source identities, not proof of distinct real humans.

The reported scenarios expose alternative handling of coded outcomes. The lower scenario counts identified keys whose variants consistently support an outcome; the higher scenario also allows any positively coded variant and every positively coded unresolved-identity row. **These spans are not confidence intervals or bounds on actual casualties.** Unknown severity is not imputed, and source errors can affect even apparently consistent identities. Death and injury maxima must not be added as a count of distinct casualties when contradictory outcomes overlap.

All 16 project tests pass, including source-selection, cross-release linkage and identity/outcome checks. Replacement releases passed separate candidate builds and group aggregation checks. Independent review confirmed that final person artifacts match the candidates for all five replaced years and the frozen baseline for all 18 unchanged years. Earlier CSV-based 2019 checks are historical evidence, not validation of the replacement XLSX. Group sums, event linkage, source-row accounting and severity consistency also passed. See [validation evidence](casualty_validation.md) and [the contract](casualty_contract.md).

## Unresolved limitations and next step

Published tractor-occupant benchmarks only partly reconcile. For example, this classification yields 30 tractor deaths and 812 injuries for 2021, while official publications report different occupant totals. Publication vintages also disagree with each other. These differences remain explicit; the data are not changed to fit a benchmark. The 2019 collision benchmark discrepancy is substantially reduced to two injury events, with a separate two-injury-event difference in 2013. Public national 2022–2025 microdata remain unlocated in the reviewed sources; verified newer aggregates are kept separate in [the availability assessment](data_availability.md). These are descriptive findings for the observed public release, not definitive current national casualty totals.

The [condition quality audit](conditions_quality.md), [descriptive comparisons](conditions_findings.md) and [configuration decomposition](configuration_decomposition.md) are complete. The [exposure audit](exposure_compatibility_audit.md) is complete; see [current status](project_status.md). Any casualty-based comparisons should carry forward these person scenarios and group uncertainties. Exposure denominators and stronger designs are needed for claims about driving risk, policy effects or causes.

## Full deliverables

- [Full report with annual tables, subgroup trends, sensitivities and figures](../reports/casualties/findings.md).
- [Executed casualty notebook](../notebooks/03_casualty_analysis.ipynb).
- [Person dataset contract and rebuild instructions](casualty_contract.md).
- [Validation and published benchmark comparisons](casualty_validation.md).

Rebuild with `python -m truck_collisions.build_casualties`, then `python -m truck_collisions.analyze_casualties` in the project environment. Outputs are under `data/derived/casualties/` and `reports/casualties/`; the README provides complete commands.
