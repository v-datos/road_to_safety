"""Produce the first national 2010–2023 report evidence and reviewed snapshot."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import duckdb

from .acquire import sha256
from .build import rows, EVENT_KEY, VEHICLE_KEY, PERSON_KEY

ONLINE_URL='https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en'
CATALOG_URL='https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a'


def write_csv(path, values):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def online_rows(root):
    result={}
    with (root/'data/reference/ncdb_online_bicycles_2010_2023.csv').open() as stream:
        for row in csv.DictReader(stream):
            key=(int(row['year']),row['category'])
            item=result.setdefault(row['dataset'],{}).setdefault(key,dict(year=key[0],category=key[1]))
            item[row['measure']]=int(row['count'])
    return {key:list(value.values()) for key,value in result.items()}


def source_online(root, dataset, component_ids):
    metadata=json.loads((root/'data/reference/ncdb_online_bicycles_2010_2023.metadata.json').read_text())
    person=dataset in {'gender','age_complete','road_user_annual'}
    return dict(type='file',name='Transport Canada · NCDB Online',provider='Transport Canada',
        url=ONLINE_URL,urls=[ONLINE_URL],files=['data/reference/ncdb_online_bicycles_2010_2023.csv'],
        executedAt=next(x['captured_at'] for x in metadata['files'] if x['dataset']==dataset),
        description=('Bicyclist person-level series' if person else 'Bicycle vehicle-level series')+'; Canada, 2010–2023; August 12, 2025 cube.',
        caveats=[('Person casualties use Road User Class=Bicyclist; demographic unknown categories remain in totals.' if person else 'Casualties under the vehicle filter belong to the selected bicycle vehicle type, not all people in the event.'),
            *[item for item in metadata['limitations'] if not item.startswith('Casualties belong')]],
        evidenceFlow=[dict(title='Public table query',detail=f'NCDB Online wizard: years 2010–2023; '+
            ('Road User Class=Bicyclist.' if person else 'Vehicle Type=Bicycle.')+f' Selected table capture for dataset {dataset} is pinned in ncdb_online_bicycles_2010_2023.metadata.json.'),
            dict(title='Capture',detail='Visible DOM cell matrices archived; native CSV download timed out. No manually typed numerical values.'),
            dict(title='Normalization',detail='python -m bicycle_collisions.online; all 14 years, mutually exclusive category sums, and corresponding person/vehicle annual totals verified.')],
        metricDefinitions=[dict(label='Counting unit',definition=('People classified as bicyclists for annual casualties; person profiles reconcile to that annual series.' if person else 'Bicycles involved in reported fatal/injury collisions; one event can contain more than one bicycle.'),componentIds=component_ids),
            dict(label='Period',definition='Calendar years 2010–2023, Canada. Category totals include unknown values.',componentIds=component_ids)])


def main():
    root=Path.cwd()
    output=root/'reports/tables'
    output.mkdir(parents=True,exist_ok=True)
    online=online_rows(root)
    vehicle_by_year={r['year']:dict(r) for r in online['annual_bicycle_2010_2023'] if r['category']=='Total'}
    for r in online['annual_bicycle_2010_2023']:
        if r['category']=='Fatal collisions': vehicle_by_year[r['year']]['vehicles_in_fatal_collisions']=r['vehicles']
        if r['category']=='Injury collisions': vehicle_by_year[r['year']]['vehicles_in_injury_collisions']=r['vehicles']
    vehicle_annual=list(vehicle_by_year.values())
    cyclist_annual=[r for r in online['road_user_annual'] if r['category']=='Total']
    for r in vehicle_annual:
        r['fatal_involvement_share']=r['vehicles_in_fatal_collisions']/r['vehicles']
    person_by_year={r['year']:r for r in cyclist_annual}
    context_difference=[dict(year=r['year'],vehicle_query_injured=r['injured'],person_query_injured=person_by_year[r['year']]['injured'],
        injury_difference=person_by_year[r['year']]['injured']-r['injured'],vehicle_query_fatalities=r['fatalities'],
        person_query_fatalities=person_by_year[r['year']]['fatalities'],
        fatality_difference=person_by_year[r['year']]['fatalities']-r['fatalities']) for r in vehicle_annual]
    connection=duckdb.connect(str(root/'data/derived/build.duckdb'),read_only=True)
    micro_annual=rows(connection,'''SELECT cast(c.C_YEAR AS INTEGER) AS year,count(*) AS collisions,
        count(*) FILTER(WHERE c.C_SEV='1') AS fatal_collisions,
        count(*) FILTER(WHERE c.C_SEV='2') AS injury_collisions
        FROM collisions c GROUP BY c.C_YEAR ORDER BY c.C_YEAR''')
    vehicle_counts={r['year']:r for r in rows(connection,"""SELECT cast(C_YEAR AS INTEGER) AS year,
        count(*) FILTER(WHERE bicycle_record_present) AS bicycle_vehicles FROM vehicles GROUP BY C_YEAR""")}
    for r in micro_annual:
        r.update(vehicle_counts[r['year']])
        r['fatal_event_share']=r['fatal_collisions']/r['collisions']
    harm_sql='''SELECT CASE P_USER WHEN '1' THEN 'Motor vehicle driver' WHEN '2' THEN 'Motor vehicle passenger'
        WHEN '3' THEN 'Pedestrian' WHEN '4' THEN 'Bicyclist' WHEN '5' THEN 'Motorcyclist'
        WHEN 'conflict' THEN 'Conflicting road-user classification' ELSE 'Other or unknown' END AS road_user,
        count(*) AS identified_people,
        count(*) FILTER(WHERE P_ISEV='3') AS deaths_resolved,
        count(*) FILTER(WHERE P_ISEV='2') AS injuries_resolved,
        count(*) FILTER(WHERE P_ISEV IS NULL OR P_ISEV='U') AS unresolved_outcome_people,
        sum(deaths_min) AS deaths_min,sum(deaths_max) AS deaths_max,
        sum(injuries_min) AS injuries_min,sum(injuries_max) AS injuries_max
        FROM people GROUP BY road_user ORDER BY deaths_resolved DESC,injuries_resolved DESC'''
    harm=rows(connection,harm_sql)
    groups=[('Light-duty vehicle',"V_TYPE='01'"),('Cargo or other light truck/van',"V_TYPE IN ('05','06')"),
        ('Heavy unit truck',"V_TYPE='07'"),('Road tractor',"V_TYPE='08'"),('Bus',"V_TYPE IN ('09','10','11')"),
        ('Motorcycle or moped',"V_TYPE='14'"),('Other classified non-bicycle vehicle',"V_TYPE IN ('16','18','19','20','21','22','23')"),
        ('Unknown, other or conflicting vehicle type',"V_TYPE IS NULL OR V_TYPE IN ('UU','QQ','XX')")]
    other_vehicles=[]
    for label,predicate in groups:
        value=connection.execute(f'SELECT count(DISTINCT ({EVENT_KEY})) FROM vehicles WHERE {predicate}').fetchone()[0]
        other_vehicles.append(dict(vehicle_group=label,collisions=value,share_of_collisions=value/sum(r['collisions'] for r in micro_annual)))
    compare=[]
    for row in micro_annual:
        year=row['year']
        resolved=connection.execute("SELECT count(*) FILTER(WHERE P_USER='4' AND P_ISEV='3'), count(*) FILTER(WHERE P_USER='4' AND P_ISEV='2') FROM people WHERE C_YEAR=?",[str(year)]).fetchone()
        compare.append(dict(year=year,record_bicycle_vehicles=row['bicycle_vehicles'],online_bicycle_vehicles=vehicle_by_year[year]['vehicles'],
            record_resolved_bicyclist_deaths=resolved[0],online_bicyclist_deaths=person_by_year[year]['fatalities'],
            record_resolved_bicyclist_injuries=resolved[1],online_bicyclist_injuries=person_by_year[year]['injured']))
    validation=json.loads((root/'data/derived/validation.json').read_text())
    assert connection.execute(f'SELECT count(*)=count(DISTINCT ({EVENT_KEY})) FROM collisions').fetchone()[0]
    assert connection.execute(f'SELECT count(*)=count(DISTINCT ({VEHICLE_KEY})) FROM vehicles').fetchone()[0]
    assert connection.execute(f'SELECT count(*)=count(DISTINCT ({PERSON_KEY})) FROM people').fetchone()[0]
    direct=connection.execute(f"SELECT count(DISTINCT ({EVENT_KEY})) FROM records WHERE V_TYPE='17'").fetchone()[0]
    assert direct==sum(r['collisions'] for r in micro_annual)
    assert sum(r['identified_people'] for r in harm)==connection.execute('SELECT count(*) FROM people').fetchone()[0]
    connection.close()
    tables=dict(annual_bicycle_involvements=vehicle_annual,annual_bicyclist_casualties=cyclist_annual,
        annual_unique_collisions_2010_2021=micro_annual,people_harmed_2010_2021=harm,
        other_vehicle_involvement_2010_2021=other_vehicles,record_online_comparison=compare,
        online_query_context_comparison=context_difference)
    for name in ['gender','age_complete','month','weekday','hour','weather','surface','road_configuration','light']:
        tables[name+'_2010_2023']=[r for r in online[name] if r['category']!='Total']
    for name,values in tables.items():write_csv(output/(name+'.csv'),values)
    queries={}
    mapping={'annual_vehicles':('annual_bicycle_2010_2023',vehicle_annual,['involvement-trend','involvement-severity']),
        'annual_cyclists':('road_user_annual',cyclist_annual,['casualty-trend'])}
    for name in ['gender','age_complete','month','weekday','hour','weather','surface','road_configuration','light']:
        mapping[name]=(name,tables[name+'_2010_2023'],[name+'-profile']+(['age-injury-profile'] if name=='age_complete' else []))
    for query_id,(dataset,values,components) in mapping.items():
        queries[query_id]=dict(rows=values,source=source_online(root,dataset,components),
            methods=[dict(language='python',code=f'python -m bicycle_collisions.online\npython -m bicycle_collisions.analyze\n# Select dataset={dataset}; category Total for annual series, exclude Total for category profiles.')])
    queries['annual_vehicles']['source']['metricDefinitions'].append(dict(label='Fatal-involvement share',
        definition='Bicycle involvements in fatal collisions divided by all bicycle involvements in fatal/injury collisions. This is not risk per trip.',
        formula='vehicles_in_fatal_collisions / vehicles',componentIds=['involvement-severity']))
    raw_sources=json.loads((root/'data/sources.json').read_text())
    micro_source=dict(type='file',name='Public NCDB records · selected 2010–2021 releases',provider='Transport Canada',url=CATALOG_URL,
        files=['data/sources.json','data/derived/bicycle_collisions.parquet','data/derived/vehicles.parquet','data/derived/people.parquet'],
        executedAt=validation['built_at'],description='Canada, 2010–2021. Source releases selected in data/sources.json; independent bicycle build.',
        caveats=['Linked records stop in 2021; no 2022–2023 collision-level fill or extrapolation.',
            'Identified person counts exclude unresolved identities; record conflicts remain explicit.',
            'Record releases and online cube disagree in several years; neither is overwritten to force agreement.'],
        evidenceFlow=[dict(title='Input acquisition',detail='Original pinned NCDB files copied into this project with SHA256 verification; language/header normalization preserves codes.'),
            dict(title='Cohort',detail="Select unique (source_id,C_YEAR,C_CASE) with V_TYPE=17 and retain all linked records; validate physical and selected years."),
            dict(title='Grains',detail='Separate event, known vehicle and known person keys. Preserve unresolved identities and conflicting outcomes.'),
            dict(title='Verification',detail='Independent distinct-key checks against retained records and source-release comparisons saved in report tables.')],
        metricDefinitions=[dict(label='Linked-record population',definition='Police-reported fatal/injury events with a recorded bicycle, Canada 2010–2021. Other vehicles are co-involved; presence does not establish impact or fault.'),
            dict(label='Resolved casualties',definition='Identified person keys with a single recorded death or nonfatal injury outcome. Unresolved records and min/max record-resolution scenarios are reported separately.')])
    for key,values,sql in [('micro_annual',micro_annual,'SELECT C_YEAR, count(*) FROM collisions GROUP BY C_YEAR;'),
            ('harm',harm,harm_sql),('other_vehicles',other_vehicles,'Count distinct (source_id,C_YEAR,C_CASE) in vehicles for each documented vehicle-type group; groups can overlap.'),
            ('source_comparison',compare,'Compare annual known bicycle vehicle keys and resolved bicyclist casualties with corresponding online annual values; retain both releases.'),
            ('query_context',context_difference,'Subtract vehicle-context casualties from person-context casualties for each year.')]:
        source=dict(micro_source) if key!='query_context' else source_online(root,'road_user_annual',['context-table'])
        if key=='harm':source['sql']=harm_sql
        if key=='source_comparison':
            source['files']=[*micro_source['files'],'data/reference/ncdb_online_bicycles_2010_2023.csv']
            source['urls']=[CATALOG_URL,ONLINE_URL]
        queries[key]=dict(rows=values,source=source,methods=[dict(language='python',code='python -m bicycle_collisions.analyze\n# '+sql)])
    with (root/'data/reference/published_bicyclist_fatalities_2020_2023.csv').open() as stream:
        published=[dict(year=int(r['year']),published_fatalities=int(r['published_fatalities']),
            online_fatalities=person_by_year[int(r['year'])]['fatalities']) for r in csv.DictReader(stream)]
    write_csv(output/'published_fatality_comparison.csv',published)
    queries['published_comparison']=dict(rows=published,source=dict(type='file',provider='Transport Canada',
        name='Canadian Motor Vehicle Traffic Collision Statistics 2024 · revised bicyclist fatalities',
        url='https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024',
        files=['data/reference/published_bicyclist_fatalities_2020_2023.csv','data/reference/ncdb_online_bicycles_2010_2023.csv'],
        description='Published road-user-class table, 2020–2023 subset only; values marked revised. Read and transcribed October 17, 2026; compared with archived NCDB Online person query.',
        evidenceFlow=[dict(title='Official reference',detail='Read the Bicyclists column in Fatalities by road user class: 2020–2024; transcribe 2020–2023 counts and revision flags; no 2024 observation enters the report scope.')]))
    quality_values={key:value for key,value in validation.items() if isinstance(value,(int,float))}
    queries['quality']=dict(rows=[quality_values],source={**micro_source,
        'files':['data/derived/validation.json'],
        'description':'Bicycle linked-record identity and conflict checks, 2010–2021. Counts concern source records or person keys, not estimated missing population casualties.'})
    queries['query_context']['source']['metricDefinitions']=[dict(label='Injury difference',
        definition='Direct bicyclist person-query injuries minus bicycle vehicle-query injuries for the same year and cube vintage.',
        formula='person_query_injured - vehicle_query_injured',componentIds=['context-table'])]
    now=datetime.now(timezone.utc).isoformat()
    snapshot=dict(surface='report',title='Bicycle involvement fell over 2010–2023, then rose sharply in 2023',
        generatedAt=now,report={'asOf':'2023-12-31'},status='observed',buildStatus='creating',filters=[],queries=queries)
    target=root/'data/derived/report_snapshot.json'
    target.write_text(json.dumps(snapshot,indent=2)+'\n')
    report_path=root/'report/src/data.json'
    if report_path.exists():
        current=json.loads(report_path.read_text())
        current.update(queries=queries,generatedAt=now,report=snapshot['report'],buildStatus='updating')
        report_path.write_text(json.dumps(current,indent=2)+'\n')
    summary=dict(scope='Canada 2010–2023; linked collision/other-vehicle detail 2010–2021',
        unique_collisions_2010_2021=direct,quality=validation,
        online_totals={k:sum(r[k] for r in cyclist_annual) for k in ['injured','fatalities']},
        verified_checks=['unique event/vehicle/person keys','direct V_TYPE=17 event-count replication','road-user group additivity','online category/year partition additivity'],
        input_sha256={'online_reference':sha256(root/'data/reference/ncdb_online_bicycles_2010_2023.csv'),
            'source_manifest':sha256(root/'data/sources.json'),'analysis_code':sha256(Path(__file__))})
    (root/'reports/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='quality'},indent=2))


if __name__=='__main__':
    main()
