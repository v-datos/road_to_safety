"""Normalize archived visible NCDB Online table cells, preserving their units."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from .acquire import sha256

DATASETS = ['annual_bicycle_2010_2023','road_user_annual','gender','age_complete','month','weekday','hour',
            'weather','surface','road_configuration','light']
MEASURES = {'Number of vehicles':'vehicles','Number of persons':'persons',
            'Number of injured':'injured','Number of fatalities':'fatalities'}
CAPTURES = {'gender':'gender_road_user','age_complete':'age_road_user_complete'}


def parse_dom(table, dataset):
    years = [int(y) for y in table[0][1:]]
    if years != list(range(2010,2024)):
        raise ValueError(f'Incomplete online year selection: {years}')
    labels = table[1][1:]
    if len(labels) != 42 or len(table[2]) != 2 or not {'Vehicle Type','Road User Class'}.intersection(table[2]):
        raise ValueError('Unexpected table dimensions or pagination')
    result=[]
    for record in table[3:]:
        dimensions, values = record[:-42], record[-42:]
        if not dimensions or len(values) != 42:
            raise ValueError('Unexpected table row shape')
        category = dimensions[-1] if table[2][0] in {'Vehicle Type','Road User Class'} else dimensions[0]
        for i, year in enumerate(years):
            for j in range(3):
                value=values[3*i+j].replace(',','').strip()
                if not value.isdigit():
                    raise ValueError(f'Non-numeric or suppressed value needs review: {value}')
                result.append(dict(dataset=dataset,year=year,category=category,
                    measure=MEASURES[labels[3*i+j]],count=int(value)))
    return result


def validate_partitions(records):
    totals={}
    sums={}
    for row in records:
        key=(row['dataset'],row['year'],row['measure'])
        if row['category']=='Total':
            if key in totals:
                raise ValueError('Duplicate total row')
            totals[key]=row['count']
        else:
            sums[key]=sums.get(key,0)+row['count']
    if totals != sums:
        raise ValueError('Category totals do not reconcile')
    base={(dataset,year,measure):value for (dataset,year,measure),value in totals.items()
          if dataset in {'annual_bicycle_2010_2023','road_user_annual'}}
    for (dataset,year,measure),value in totals.items():
        population='road_user_annual' if dataset in {'road_user_annual','gender','age_complete'} else 'annual_bicycle_2010_2023'
        if measure in {'injured','fatalities','vehicles'} and value != base[(population,year,measure)]:
            raise ValueError(f'Query population differs from annual table: {dataset,year,measure}')
    return totals


def main():
    root=Path.cwd()
    raw=root/'data/raw/ncdb_online'
    records=[]
    files=[]
    for dataset in DATASETS:
        path=raw/(CAPTURES.get(dataset,dataset)+'.dom.json')
        records += parse_dom(json.loads(path.read_text()),dataset)
        files.append(dict(dataset=dataset,path=str(path.relative_to(root)),sha256=sha256(path),
            captured_at=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()))
    totals=validate_partitions(records)
    ref=root/'data/reference'
    path=ref/'ncdb_online_bicycles_2010_2023.csv'
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['dataset','year','category','measure','count'])
        writer.writeheader()
        writer.writerows(records)
    metadata=dict(source='Transport Canada NCDB Online',
        url='https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en',
        source_vintage='August 12, 2025',reference_years=list(range(2010,2024)),geography='Canada',
        filters={'Vehicle Type':'Bicycle','Year':'2010–2023','Year totals':False,
            'Vehicle Type totals':False,'Road User Class':'Bicyclist in road_user_annual, gender and age profiles; no Vehicle Type filter in those queries',
            'Collision Sev':'Total, Fatal collisions, Injury collisions in annual queries; all severity in profiles'},
        acquisition='Read visible DOM table cells through the browser. Original cell matrices preserved. Native CSV download timed out; these are not native CSV exports or manually typed counts.',
        profile_selection='All displayed mutually exclusive categories, including unknown and not applicable; age uses disjoint native age ranges plus unknown/not applicable; hour uses disjoint three-hour ranges plus unknown.',
        excluded_capture='Earlier age/gender vehicle-context and known-age-only captures are retained for audit; the selected person profiles are gender_road_user.dom.json and age_road_user_complete.dom.json.',
        files=files,normalized_sha256=sha256(path),normalized_rows=len(records),
        checks={'all_14_years':True,'all_category_partitions_reconcile':True,'profile_totals_match_corresponding_person_or_vehicle_annual':True},
        limitations=['Vehicle involvements are not unique collision counts.',
            'Person-level and vehicle-level query casualties differ for 2020–2022. Person profiles reconcile to Road User Class=Bicyclist; vehicle/condition profiles reconcile to Vehicle Type=Bicycle. Both series are retained without overwriting.',
            'Casualties belong to the selected bicycle vehicle type; they do not count all people harmed in bicycle-involved events.',
            'Recorded deaths/injuries and vehicle involvement counts do not measure exposure-adjusted cycling risk.',
            'This source vintage may differ from newer revised official publications.'])
    (ref/'ncdb_online_bicycles_2010_2023.metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({'normalized_rows':len(records),'checked_partitions':len(totals)},indent=2))


if __name__=='__main__':
    main()
