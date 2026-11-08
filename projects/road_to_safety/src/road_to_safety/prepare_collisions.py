"""Prepare collision-grain data without removing incomplete predictors or linked records.

Run: python -m road_to_safety.prepare_collisions --workers 2
Original row numbers include the header (first data row is 2).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil

import duckdb
import pandas as pd

from .audit_data import (COLUMNS, EVENT_FIELDS, FRENCH,
                         dict_rows, rows_for, sha256, value_class, write_csv)

FIELDS = [c for c in EVENT_FIELDS if c != 'C_YEAR']
KEY_OK = "regexp_full_match(C_YEAR,'[0-9]+') AND TRY_CAST(C_YEAR AS INTEGER) BETWEEN 1999 AND 2100 AND regexp_full_match(C_CASE,'[0-9]+') AND TRY_CAST(C_CASE AS BIGINT)>0"
PERSON_OK = KEY_OK + ' AND TRY_CAST(V_ID AS INTEGER) BETWEEN 1 AND 99 AND TRY_CAST(P_ID AS INTEGER) BETWEEN 1 AND 99'
DOMAINS = {
    'C_MNTH': range(1,13), 'C_WDAY': range(1,8), 'C_HOUR': range(24),
    'C_SEV': (1,2), 'C_VEHS': range(1,100),
    'C_CONF': (*range(1,7), *range(21,26), *range(31,37), 41),
    'C_RCFG': range(1,13), 'C_WTHR': range(1,8), 'C_RSUR': range(1,10),
    'C_RALN': range(1,7), 'C_TRAF': range(1,19),
}
SENTINELS = {field: ('UU','XX') if field in ('C_MNTH','C_HOUR','C_VEHS') else
             ('QQ','UU','XX') if field in ('C_CONF','C_RCFG','C_TRAF') else
             ('U','X') if field in ('C_WDAY','C_SEV') else ('Q','U','X')
             for field in FIELDS}
DOCUMENTED_DOMAINS = {field: {str(code) for code in codes} | set(SENTINELS[field])
                      for field,codes in DOMAINS.items()}


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def normalized_expression(field):
    return (f"CASE WHEN regexp_full_match(trim({field}), '[0-9]+') "
            f"THEN coalesce(CAST(TRY_CAST(trim({field}) AS BIGINT) AS VARCHAR),trim({field})) "
            f"ELSE trim({field}) END AS {field}")


def create_tables(connection):
    """Child identities are aggregated before any join to collision rows."""
    connection.execute('CREATE VIEW records AS SELECT source_row_number,' +
                       ','.join(normalized_expression(c) for c in COLUMNS) + ' FROM raw')
    person_fields = [c for c in COLUMNS if c.startswith('P_') and c != 'P_ID']
    conflict_person = ' OR '.join(f'count(DISTINCT {c})>1' for c in person_fields)
    connection.execute(f'''CREATE TEMP TABLE persons AS SELECT C_YEAR,C_CASE,V_ID,P_ID,
        count(*) n,({conflict_person}) has_conflict,count(DISTINCT P_ISEV)>1 severity_conflict FROM records WHERE {PERSON_OK}
        GROUP BY C_YEAR,C_CASE,V_ID,P_ID''')
    connection.execute(f'''CREATE TEMP TABLE vehicles AS SELECT C_YEAR,C_CASE,V_ID,
        (count(DISTINCT V_TYPE)>1 OR count(DISTINCT V_YEAR)>1) has_conflict
        FROM records WHERE {KEY_OK} AND TRY_CAST(V_ID AS INTEGER) BETWEEN 1 AND 98
        GROUP BY C_YEAR,C_CASE,V_ID''')
    connection.execute('CREATE TEMP TABLE person_events AS SELECT C_YEAR,C_CASE,'
        'count(*) diagnostic_identified_person_keys,'
        'count(*) FILTER (WHERE has_conflict) diagnostic_person_conflict_keys,'
        'count(*) FILTER (WHERE severity_conflict) diagnostic_person_severity_conflict_keys,'
        'count(*) FILTER (WHERE n>1) diagnostic_duplicate_person_keys '
        'FROM persons GROUP BY C_YEAR,C_CASE')
    connection.execute('CREATE TEMP TABLE vehicle_events AS SELECT C_YEAR,C_CASE,'
        'count(*) diagnostic_vehicle_keys,'
        'count(*) FILTER (WHERE has_conflict) diagnostic_vehicle_conflict_keys '
        'FROM vehicles GROUP BY C_YEAR,C_CASE')
    connection.execute('CREATE TEMP TABLE raw_duplicates AS SELECT ' + ','.join(COLUMNS) +
        ',count(*) n FROM raw GROUP BY ALL HAVING count(*)>1')
    # Number of duplicate *extras* at the original raw representation, not canonical representation.
    connection.execute('CREATE TEMP TABLE duplicate_events AS SELECT C_YEAR,C_CASE,sum(n-1) '
        'diagnostic_exact_duplicate_extra_rows FROM (SELECT ' +
        normalized_expression('C_YEAR') + ',' + normalized_expression('C_CASE') +
        ',n FROM raw_duplicates) GROUP BY C_YEAR,C_CASE')
    connection.execute(f'''CREATE TEMP TABLE normalized_events AS SELECT C_YEAR,C_CASE,
        count(*) diagnostic_normalized_distinct_rows FROM
        (SELECT DISTINCT {','.join(COLUMNS)} FROM records WHERE {KEY_OK}) GROUP BY C_YEAR,C_CASE''')
    attrs = ','.join(f'CASE WHEN count(DISTINCT {c})=1 THEN min({c}) END AS {c},'
                    f'count(DISTINCT {c})>1 AS {c}_conflict' for c in FIELDS)
    connection.execute(f'''CREATE TEMP TABLE events AS SELECT C_YEAR,C_CASE,{attrs},
        count(*) diagnostic_source_rows,
        count(*) FILTER (WHERE NOT coalesce(({PERSON_OK}),false)) diagnostic_unresolved_person_rows,
        count(*) FILTER (WHERE V_ID='99') diagnostic_pedestrian_dummy_rows,
        count(*) FILTER (WHERE P_ID='NN') diagnostic_dummy_person_rows
        FROM records WHERE {KEY_OK} GROUP BY C_YEAR,C_CASE''')
    diagnostics = ['diagnostic_identified_person_keys','diagnostic_person_conflict_keys',
        'diagnostic_duplicate_person_keys','diagnostic_vehicle_keys','diagnostic_vehicle_conflict_keys',
        'diagnostic_exact_duplicate_extra_rows','diagnostic_normalized_distinct_rows',
        'diagnostic_person_severity_conflict_keys']
    connection.execute('CREATE TEMP TABLE collisions AS SELECT e.*,' +
        ','.join(f'coalesce({c},0)::BIGINT AS {c}' for c in diagnostics) +
        ",CASE C_SEV WHEN '1' THEN 1 WHEN '2' THEN 0 END::INTEGER AS is_fatal,"
        "coalesce(C_SEV IN ('1','2'),false) AS severity_eligible FROM events e "
        'LEFT JOIN person_events USING(C_YEAR,C_CASE) LEFT JOIN vehicle_events USING(C_YEAR,C_CASE) '
        'LEFT JOIN duplicate_events USING(C_YEAR,C_CASE) LEFT JOIN normalized_events USING(C_YEAR,C_CASE)')


def write_exceptions(connection, path, resource):
    raw_equal = ' AND '.join(f'b.{c}=d.{c}' for c in COLUMNS)
    event_conflict = ' OR '.join(f'e.{c}_conflict' for c in FIELDS)
    reasons = [
        (f'NOT coalesce(({KEY_OK}),false)', 'invalid_collision_key'),
        (f'NOT coalesce(({PERSON_OK}),false)', 'unresolved_person_identity'),
        ("r.V_ID='99'", 'pedestrian_dummy_vehicle'),
        ("r.P_ID='NN'", 'dummy_person'),
        ('p.n>1', 'duplicate_identified_person_key'),
        ('p.has_conflict', 'conflicting_person_attributes'),
        ('v.has_conflict', 'conflicting_vehicle_attributes'),
        (f'({event_conflict})', 'conflicting_collision_attributes'),
        ('d.n>1', 'exact_duplicate_source_row'),
        ("r.C_SEV NOT IN ('1','2')", 'unresolved_target'),
        (' OR '.join(f'r.{field} NOT IN ({",".join(quote(v) for v in sorted(DOCUMENTED_DOMAINS[field]))})'
                     for field in FIELDS if field != 'C_SEV'), 'undocumented_collision_code'),
    ]
    # Qualify key clauses to avoid ambiguous collision keys introduced by joins.
    for index in (0,1):
        condition, label = reasons[index]
        for col in ('C_YEAR','C_CASE','V_ID','P_ID'):
            condition = condition.replace(col, 'r.'+col)
        reasons[index] = condition,label
    expression = 'list_filter([' + ','.join(f'CASE WHEN {condition} THEN {quote(label)} END' for condition,label in reasons) + '], x -> x IS NOT NULL)'
    connection.execute(f'''COPY (SELECT b.*, {quote(resource['resource_id'])} AS source_id,
        {quote(resource['local_path'])} AS source_path,{quote(resource['sha256'])} AS source_sha256,
        {expression} AS reasons FROM raw b JOIN records r USING(source_row_number)
        LEFT JOIN persons p ON r.C_YEAR=p.C_YEAR AND r.C_CASE=p.C_CASE AND r.V_ID=p.V_ID AND r.P_ID=p.P_ID
        LEFT JOIN vehicles v ON r.C_YEAR=v.C_YEAR AND r.C_CASE=v.C_CASE AND r.V_ID=v.V_ID
        LEFT JOIN events e ON r.C_YEAR=e.C_YEAR AND r.C_CASE=e.C_CASE
        LEFT JOIN raw_duplicates d ON {raw_equal}
        WHERE len({expression})>0) TO {quote(path)} (FORMAT PARQUET, COMPRESSION ZSTD)''')


def prepare_file(args):
    root, resource, output_directory = args
    root, output_directory = Path(root), Path(output_directory)
    path = root/resource['local_path']
    if sha256(path) != resource['sha256']:
        raise ValueError(f'{path}: source fingerprint mismatch')
    connection = duckdb.connect()
    connection.execute("SET memory_limit='700MB'")
    connection.execute('SET threads=1')
    reader = iter(rows_for(path, resource.get('sheet') or 'in'))
    headers = next(reader)
    if headers != (FRENCH if '-fr' in path.name else COLUMNS):
        raise ValueError(f'{path}: unexpected source headers')
    connection.execute('CREATE TABLE raw (source_row_number BIGINT,' + ','.join(c+' VARCHAR' for c in COLUMNS)+')')
    count, blanks, batch = 0,0,[]
    for row_number,row in enumerate(reader,2):
        if len(row) != len(COLUMNS):
            raise ValueError(f'{path}:{row_number}: unexpected row width')
        if not any(row):
            blanks += 1
            continue
        batch.append((row_number,*row))
        count += 1
        if len(batch)>=50000:
            frame = pd.DataFrame(batch,columns=['source_row_number',*COLUMNS])
            connection.register('batch_frame',frame)
            connection.execute('INSERT INTO raw SELECT * FROM batch_frame')
            connection.unregister('batch_frame')
            batch=[]
    if batch:
        frame=pd.DataFrame(batch,columns=['source_row_number',*COLUMNS])
        connection.register('batch_frame',frame)
        connection.execute('INSERT INTO raw SELECT * FROM batch_frame')
        connection.unregister('batch_frame')
    create_tables(connection)
    tags = {'source_id':resource['resource_id'],'year':resource['year']}
    normalization=[]
    for field in COLUMNS:
        changed=connection.execute(f'SELECT count(*) FROM raw b JOIN records r USING(source_row_number) WHERE b.{field} IS DISTINCT FROM r.{field}').fetchone()[0]
        normalization.append({**tags,'field':field,'changed_rows':changed})
    summary={**tags,'path':resource['local_path'],'sha256':resource['sha256'],'rows':count,'blank_rows':blanks}
    summary.update(dict_rows(connection,"""SELECT count(*) collisions,
        count(*) FILTER (WHERE is_fatal=1) fatal_collisions,
        count(*) FILTER (WHERE is_fatal=0) injury_collisions,
        count(*) FILTER (WHERE NOT severity_eligible) target_ineligible_collisions,
        coalesce(sum(diagnostic_source_rows),0) retained_source_rows FROM collisions""")[0])
    summary['invalid_collision_key_rows']=connection.execute(f'SELECT count(*) FROM records WHERE NOT coalesce(({KEY_OK}),false)').fetchone()[0]
    summary['exact_duplicate_extra_rows']=connection.execute('SELECT coalesce(sum(n-1),0) FROM raw_duplicates').fetchone()[0]
    summary['unexpected_year_rows']=connection.execute(f"SELECT count(*) FROM records WHERE C_YEAR IS DISTINCT FROM {quote(resource['year'])}").fetchone()[0]
    if summary['unexpected_year_rows']:
        raise ValueError(f'{path}: observed year differs from selected manifest year')
    if summary['rows'] != summary['retained_source_rows']+summary['invalid_collision_key_rows']:
        raise ValueError('Source-record conservation failed')
    summary['normalization_changes']=normalization
    profiles=[]
    for field in FIELDS:
        counts=dict_rows(connection,f'SELECT C_YEAR,{field} AS value,{field}_conflict AS conflict,count(*) AS collisions FROM collisions GROUP BY ALL')
        for item in counts:
            state='conflict' if item['conflict'] else value_class(field,item['value'])
            numeric_ok = item['value'] in {str(v) for v in DOMAINS[field]}
            domain_valid = item['value'] in DOCUMENTED_DOMAINS[field]
            if not domain_valid and state not in ('blank','conflict','unresolved_star_code'):
                state='invalid_code'
            profiles.append({**tags,'observed_year':item['C_YEAR'],'field':field,'value':item['value'],
                'value_class':state,'numeric_code_eligible':numeric_ok,'documented_domain_valid':domain_valid,
                'collisions':item['collisions'],
                'collision_denominator':summary['collisions'],'collision_rate':item['collisions']/summary['collisions']})
    summary['profiles']=profiles
    collision_path=output_directory/f"{resource['year']}_collisions.parquet"
    connection.execute(f'''COPY (SELECT {quote(resource['resource_id'])} source_id,
        {quote(resource['local_path'])} source_path,{quote(resource['sha256'])} source_sha256,*
        FROM collisions ORDER BY C_YEAR,TRY_CAST(C_CASE AS BIGINT)) TO {quote(collision_path)}
        (FORMAT PARQUET,COMPRESSION ZSTD)''')
    exception_path=output_directory/f"{resource['year']}_exceptions.parquet"
    write_exceptions(connection,exception_path,resource)
    summary['exception_rows']=connection.execute(f'SELECT count(*) FROM read_parquet({quote(exception_path)})').fetchone()[0]
    summary['conflict_counts']={field:connection.execute(f'SELECT count(*) FROM collisions WHERE {field}_conflict').fetchone()[0] for field in FIELDS}
    connection.close()
    return summary


def run(root,workers=2):
    root=Path(root).resolve()
    catalog_path=root/'data/sources.json'
    audit_path=root/'data/derived/quality_audit.json'
    catalog=json.loads(catalog_path.read_text())
    audit=json.loads(audit_path.read_text())
    contract_path=root/'data/reference/modeling_contract.json'
    contract=json.loads(contract_path.read_text())
    if any(set(codes)!=DOCUMENTED_DOMAINS[field] for field,codes in contract['categorical_domains'].items()):
        raise ValueError('Preparation and modeling contract dictionary domains differ')
    audit_code=root/'src/road_to_safety/audit_data.py'
    if audit['audit_code_sha256']!=sha256(audit_code):
        raise ValueError('Audit code changed since authoritative audit; rerun audit first')
    selected=[r for r in catalog['resources'] if r.get('selected')]
    for resource in selected:
        if sha256(root/resource['local_path'])!=resource['sha256']:
            raise ValueError('Source manifest fingerprint mismatch: '+resource['local_path'])
    resources=[r for r in selected if r.get('year') is not None]
    if len({r['year'] for r in resources})!=len(resources):
        raise ValueError('More than one selected release per year')
    audited={r['source_id']:r for r in audit['files'] if r['selected']}
    if set(audited)!={r['resource_id'] for r in resources}:
        raise ValueError('Audit selection differs from preparation inputs')
    for resource in resources:
        previous=audited[resource['resource_id']]
        if (previous['sha256'],previous['path'],previous['expected_year'],previous.get('sheet')) != (resource['sha256'],resource['local_path'],resource['year'],resource.get('sheet')):
            raise ValueError('Audit/source identity mismatch')
    derived=root/'data/derived'
    temporary=derived/'.preparation_tmp'
    temporary.mkdir(parents=True,exist_ok=False)
    results=[]
    try:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(prepare_file,(str(root),r,str(temporary))) for r in resources]
            for future in as_completed(futures):
                result=future.result()
                previous=audited[result['source_id']]
                for key in ('rows','collisions','fatal_collisions','injury_collisions','invalid_collision_key_rows','exact_duplicate_extra_rows'):
                    if result[key]!=previous[key]:
                        raise ValueError(f"Audit reconciliation failed {result['year']} {key}: {result[key]} != {previous[key]}")
                results.append(result)
                print(f"Prepared {result['year']}: {result['rows']:,} source records; {result['collisions']:,} collisions",flush=True)
        results.sort(key=lambda r:r['year'])
        connection=duckdb.connect()
        for kind,target in [('collisions','collisions.parquet'),('exceptions','preparation_exceptions.parquet')]:
            connection.execute(f"COPY (SELECT * FROM read_parquet({quote(temporary/('*_'+kind+'.parquet'))})) TO {quote(derived/target)} (FORMAT PARQUET, COMPRESSION ZSTD)")
        connection.close()
        tables=root/'reports/tables'
        write_csv(tables/'preparation_missingness.csv',[p for r in results for p in r['profiles']])
        write_csv(tables/'preparation_normalization.csv',[p for r in results for p in r['normalization_changes']])
        annual=[{k:v for k,v in r.items() if k not in ('profiles','normalization_changes','conflict_counts')} for r in results]
        write_csv(tables/'preparation_reconciliation.csv',annual)
        write_csv(tables/'preparation_conflicts.csv',[{'source_id':r['source_id'],'year':r['year'],'field':f,'conflict_collisions':n} for r in results for f,n in r['conflict_counts'].items()])
        outputs=[derived/'collisions.parquet',derived/'preparation_exceptions.parquet',*sorted(tables.glob('preparation_*.csv'))]
        payload={'created_at_utc':datetime.now(timezone.utc).isoformat(),
            'preparation_code_sha256':sha256(__file__),'audit_code_sha256':sha256(audit_code),
            'audit_sha256':sha256(audit_path),'source_manifest_sha256':sha256(catalog_path),
            'modeling_contract_sha256':sha256(contract_path),
            'runtime':{name:importlib.metadata.version(name) for name in ('duckdb','pandas','openpyxl','python-calamine')},
            'normalization':'Trim whitespace; integer numeric strings lose zero padding; all sentinel strings remain distinct. Original raw values and source row number are retained in exceptions and immutable inputs.',
            'candidate_key':['source_id','C_YEAR','C_CASE'],
            'key_policy':'Digit-only year in 1999..2100 and positive digit-only BIGINT case. Any observed year differing from the selected manifest year aborts the build.',
            'record_conservation':'raw nonblank rows = sum(diagnostic_source_rows) + invalid_collision_key_rows; no person/vehicle or predictor exclusion',
            'inputs':[{k:r.get(k) for k in ('resource_id','year','local_path','sha256','sheet')} for r in selected],
            'files':[{k:v for k,v in r.items() if k!='profiles'} for r in results],
            'totals':{key:sum(r[key] for r in results) for key in ('rows','collisions','fatal_collisions','injury_collisions','target_ineligible_collisions','invalid_collision_key_rows','exact_duplicate_extra_rows','retained_source_rows','exception_rows')},
            'outputs':[{'path':str(p.relative_to(root)),'sha256':sha256(p),'size_bytes':p.stat().st_size} for p in outputs]}
        (derived/'preparation_manifest.json').write_text(json.dumps(payload,indent=2)+'\n')
        return payload
    finally:
        shutil.rmtree(temporary)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--workers',type=int,default=2)
    options=parser.parse_args()
    run(options.root,options.workers)
