"""Full-file, source-preserving NCDB feasibility audit; no modeling tables are built.

Run from the project root: python -m road_to_safety.audit_data --workers 2
Numeric code padding is normalized only in the temporary audit view, never raw files.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re

import duckdb
import openpyxl
import pandas as pd

COLUMNS = 'C_YEAR C_MNTH C_WDAY C_HOUR C_SEV C_VEHS C_CONF C_RCFG C_WTHR C_RSUR C_RALN C_TRAF V_ID V_TYPE V_YEAR P_ID P_SEX P_AGE P_PSN P_ISEV P_SAFE P_USER C_CASE'.split()
FRENCH = 'C_ANNÉE C_MOIS C_JSEM C_HEURE C_GRAVITÉ C_VÉH C_CFG C_CFGR C_MÉTEO C_ÉCHSÉ C_TRAR C_CIRC V_ID V_TYPE V_ANNÉE P_ID P_SEXE P_ÂGE P_LOCP P_ISEV P_SÉCURITÉ P_USAG C_CAS'.split()
EVENT_FIELDS = COLUMNS[:12]
KEY_OK = "TRY_CAST(C_YEAR AS INTEGER) BETWEEN 1999 AND 2100 AND TRY_CAST(C_CASE AS BIGINT)>0"
PERSON_OK = KEY_OK + ' AND TRY_CAST(V_ID AS INTEGER) BETWEEN 1 AND 99 AND TRY_CAST(P_ID AS INTEGER) BETWEEN 1 AND 99'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def value_class(field, value):
    """Only dictionary-supported sentinel meanings; stars remain unresolved."""
    if value is None or not str(value).strip():
        return 'blank'
    value = str(value).strip()
    if field == 'P_USER' and value == 'U':
        return 'not_stated_other_unknown'
    if re.fullmatch('U+', value):
        return 'unknown'
    if re.fullmatch('X+', value):
        return 'jurisdiction_unavailable'
    if re.fullmatch('N+', value):
        return 'not_applicable'
    if re.fullmatch('Q+', value):
        return 'other'
    if '*' in value:
        return 'unresolved_star_code'
    return 'stated'


def xlsx_rows(path, sheet='in'):
    """Use the maintained calamine reader; compare row count/sample to openpyxl."""
    frame = pd.read_excel(path, sheet_name=sheet, engine='calamine', dtype=str, keep_default_na=False)
    yield list(frame.columns)
    yield from frame.itertuples(index=False, name=None)


def rows_for(path, sheet='in'):
    if path.suffix == '.xlsx':
        yield from xlsx_rows(path, sheet)
        return
    encoding = 'cp1252' if '-fr' in path.name else 'utf-8-sig'
    with path.open(newline='', encoding=encoding) as stream:
        yield from csv.reader(stream)


def dict_rows(connection, sql):
    result = connection.execute(sql)
    names = [desc[0] for desc in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def profile_file(args):
    root, resource = args
    path = Path(root) / resource['local_path']
    file_hash = sha256(path)
    if resource.get('sha256') and resource['sha256'] != file_hash:
        raise ValueError(f'{path}: manifest SHA256 mismatch')
    reader = iter(rows_for(path, resource.get('sheet') or 'in'))
    headers = next(reader)
    expected_headers = FRENCH if '-fr' in path.name else COLUMNS
    if headers != expected_headers:
        raise ValueError(f'{path}: unexpected headers {headers}')
    checked = []
    declared_rows = None
    if path.suffix == '.xlsx':
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet = wb[resource.get('sheet') or 'in']
        declared_rows = sheet.max_row - 1
        checked = [[str(v) if v is not None else '' for v in row] for row in sheet.iter_rows(min_row=2, max_row=101, values_only=True)]
        wb.close()
    connection = duckdb.connect()
    connection.execute("SET memory_limit='1GB'")
    connection.execute('SET threads=1')
    connection.execute('CREATE TABLE raw (' + ','.join(c + ' VARCHAR' for c in COLUMNS) + ')')
    batch, count, blank_rows = [], 0, 0
    for row in reader:
        if len(row) != len(COLUMNS):
            raise ValueError(f'{path}: row {count + 2} width={len(row)}')
        if not any(row):
            blank_rows += 1
            continue
        if count < len(checked) and list(row) != checked[count]:
            raise ValueError(f'{path}: calamine/openpyxl mismatch row {count + 2}')
        batch.append(row)
        count += 1
        if len(batch) == 50000:
            frame = pd.DataFrame(batch, columns=COLUMNS)
            connection.register('batch_frame', frame)
            connection.execute('INSERT INTO raw SELECT * FROM batch_frame')
            connection.unregister('batch_frame')
            batch = []
    if batch:
        frame = pd.DataFrame(batch, columns=COLUMNS)
        connection.register('batch_frame', frame)
        connection.execute('INSERT INTO raw SELECT * FROM batch_frame')
        connection.unregister('batch_frame')
    if declared_rows is not None and count + blank_rows != declared_rows:
        raise ValueError(f'{path}: calamine row count differs from worksheet dimensions')
    expressions = [f"CASE WHEN regexp_full_match(trim({c}), '[0-9]+') THEN CAST(CAST(trim({c}) AS BIGINT) AS VARCHAR) ELSE trim({c}) END AS {c}" for c in COLUMNS]
    connection.execute('CREATE VIEW records AS SELECT ' + ','.join(expressions) + ' FROM raw')
    summary = {
        'source_id': resource['resource_id'], 'path': resource['local_path'],
        'sha256': file_hash, 'selected': resource.get('selected',False), 'sheet':resource.get('sheet'), 'expected_year': resource['year'], 'rows': count,
        'blank_rows': blank_rows, 'columns': len(headers), 'original_headers': headers,
        'xlsx_declared_rows': declared_rows, 'independent_openpyxl_rows_checked': len(checked),
    }
    summary.update(dict_rows(connection, f'''SELECT
        count(*) FILTER (WHERE NOT coalesce(({KEY_OK}),false)) invalid_collision_key_rows,
        count(*) FILTER (WHERE {PERSON_OK}) identified_person_rows,
        count(*) FILTER (WHERE NOT coalesce(({PERSON_OK}),false)) unresolved_person_identity_rows,
        count(*) FILTER (WHERE TRY_CAST(C_YEAR AS INTEGER) != {resource['year']} OR TRY_CAST(C_YEAR AS INTEGER) IS NULL) unexpected_year_rows,
        count(*) FILTER (WHERE V_ID='99') pedestrian_dummy_vehicle_rows,
        count(*) FILTER (WHERE P_ID='NN') dummy_person_rows
        FROM records''')[0])
    summary['observed_years'] = [r[0] for r in connection.execute('SELECT DISTINCT C_YEAR FROM records ORDER BY C_YEAR').fetchall()]
    summary['exact_duplicate_extra_rows'] = connection.execute('SELECT coalesce(sum(n-1),0) FROM (SELECT ' + ','.join(COLUMNS) + ',count(*) n FROM raw GROUP BY ALL HAVING count(*)>1)').fetchone()[0]
    connection.execute(f'''CREATE TEMP TABLE events AS SELECT C_YEAR,C_CASE,count(*) source_rows,
        count(DISTINCT C_SEV) severity_values,min(C_SEV) severity,
        {','.join(f'count(DISTINCT {c}) AS {c}_values' for c in EVENT_FIELDS if c not in ('C_YEAR','C_SEV'))}
        FROM records WHERE {KEY_OK} GROUP BY C_YEAR,C_CASE''')
    summary.update(dict_rows(connection, '''SELECT count(*) collisions,
        count(*) FILTER (WHERE severity_values>1) severity_conflict_collisions,
        count(*) FILTER (WHERE severity_values=1 AND severity IN ('1','2')) valid_severity_collisions,
        count(*) FILTER (WHERE severity_values=1 AND severity='1') fatal_collisions,
        count(*) FILTER (WHERE severity_values=1 AND severity='2') injury_collisions,
        count(*) FILTER (WHERE severity_values=1 AND severity NOT IN ('1','2')) unresolved_severity_collisions,
        min(source_rows) min_rows_per_collision,max(source_rows) max_rows_per_collision
        FROM events''')[0])
    conflicts = []
    for field in EVENT_FIELDS:
        if field == 'C_YEAR':
            continue
        key = 'severity_values' if field == 'C_SEV' else field + '_values'
        conflicts.append({'field': field, 'conflict_collisions': connection.execute(f'SELECT count(*) FROM events WHERE {key}>1').fetchone()[0]})
    summary['collision_attribute_conflicts'] = conflicts
    summary.update(dict_rows(connection, f'''SELECT count(*) duplicate_identified_person_keys,
        coalesce(sum(n),0) rows_on_duplicate_identified_person_keys,
        coalesce(sum(n-1),0) duplicate_identified_person_extra_rows,
        count(*) FILTER (WHERE outcomes>1) person_severity_conflict_keys
        FROM (SELECT count(*) n,count(DISTINCT P_ISEV) outcomes FROM records WHERE {PERSON_OK}
        GROUP BY C_YEAR,C_CASE,V_ID,P_ID HAVING count(*)>1)''')[0])
    summary['identified_person_keys'] = connection.execute(f'SELECT count(*) FROM (SELECT DISTINCT C_YEAR,C_CASE,V_ID,P_ID FROM records WHERE {PERSON_OK})').fetchone()[0]
    # Full-domain profiles use normalized dictionary codes; originals remain archived.
    values, fields = [], []
    for field in COLUMNS:
        distinct = connection.execute(f'SELECT count(DISTINCT {field}) FROM records').fetchone()[0]
        fields.append({'field': field, 'distinct_values': distinct})
        if field == 'C_CASE':
            continue
        profile = dict_rows(connection, f"SELECT {field} AS value,count(*) AS rows FROM records GROUP BY {field} ORDER BY {field}")
        for result in profile:
            values.append({'field': field, **result, 'value_class': value_class(field, result['value'])})
    summary['fields'] = fields
    summary['value_counts'] = values
    summary['person_outcome_rows'] = dict_rows(connection, 'SELECT P_ISEV AS value,count(*) AS rows FROM records GROUP BY P_ISEV ORDER BY P_ISEV')
    summary['road_user_rows'] = dict_rows(connection, 'SELECT P_USER AS value,count(*) AS rows FROM records GROUP BY P_USER ORDER BY P_USER')
    # Event-count support by road-user code is overlapping; each event counted once per code.
    summary['road_user_collisions'] = dict_rows(connection, f'SELECT P_USER AS value,count(*) AS collisions FROM (SELECT DISTINCT C_YEAR,C_CASE,P_USER FROM records WHERE {KEY_OK}) GROUP BY P_USER ORDER BY P_USER')
    summary['person_target_valid_rows'] = connection.execute(f"SELECT count(*) FROM records WHERE {PERSON_OK} AND P_ISEV IN ('1','2','3')").fetchone()[0]
    summary['vehicle_attribute_conflict_keys'] = connection.execute(f'''SELECT count(*) FROM (SELECT C_YEAR,C_CASE,V_ID FROM records
        WHERE {KEY_OK} AND TRY_CAST(V_ID AS INTEGER) BETWEEN 1 AND 98 GROUP BY ALL
        HAVING count(DISTINCT V_TYPE)>1 OR count(DISTINCT V_YEAR)>1)''').fetchone()[0]
    summary['person_target_valid_unique_keys'] = connection.execute(f"""SELECT count(*) FROM (
        SELECT C_YEAR,C_CASE,V_ID,P_ID FROM records WHERE {PERSON_OK} GROUP BY ALL
        HAVING count(DISTINCT P_ISEV)=1 AND min(P_ISEV) IN ('1','2','3'))""").fetchone()[0]
    summary['fatal_collisions_without_recorded_fatal_person'] = connection.execute(f"""SELECT count(*) FROM events e
        WHERE severity_values=1 AND severity='1' AND NOT EXISTS (
        SELECT 1 FROM records r WHERE r.C_YEAR=e.C_YEAR AND r.C_CASE=e.C_CASE AND P_ISEV='3')""").fetchone()[0]
    summary['injury_collisions_with_recorded_fatal_person'] = connection.execute(f"""SELECT count(*) FROM events e
        WHERE severity_values=1 AND severity='2' AND EXISTS (
        SELECT 1 FROM records r WHERE r.C_YEAR=e.C_YEAR AND r.C_CASE=e.C_CASE AND P_ISEV='3')""").fetchone()[0]
    connection.close()
    return summary


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(root, results, code_hash):
    root = Path(root)
    tables = root / 'reports/tables'
    tables.mkdir(parents=True, exist_ok=True)
    annual, missing, values, fields, conflicts, outcomes, roadusers = [], [], [], [], [], [], []
    for result in sorted(results, key=lambda r: (r['expected_year'],r['path'])):
        tags = {'year': result['expected_year'], 'source_path': result['path'], 'selected':result['selected']}
        annual.append({**tags, **{k:v for k,v in result.items() if (isinstance(v,(str,int,float)) or v is None) and k not in ('path','sha256','source_id','selected')}})
        counts = {}
        for entry in result['value_counts']:
            values.append({**tags, **entry})
            key = (entry['field'],entry['value_class'])
            counts[key] = counts.get(key,0) + entry['rows']
        for (field,kind),count in counts.items():
            missing.append({**tags,'field':field,'value_class':kind,'rows':count,'row_denominator':result['rows'],'row_rate':count/result['rows']})
        fields.extend({**tags, **entry} for entry in result['fields'])
        conflicts.extend({**tags, **entry} for entry in result['collision_attribute_conflicts'])
        outcomes.extend({**tags,'grain':'source_record',**entry} for entry in result['person_outcome_rows'])
        collision_outcomes = {'1':result['fatal_collisions'],'2':result['injury_collisions'],'unresolved':result['unresolved_severity_collisions'],'conflict':result['severity_conflict_collisions']}
        outcomes.extend({**tags,'grain':'collision','value':code,'rows':count} for code,count in collision_outcomes.items())
        for entry in result['road_user_rows']:
            event_count = next((e['collisions'] for e in result['road_user_collisions'] if e['value']==entry['value']),0)
            roadusers.append({**tags,**entry,'collisions_with_code':event_count})
    for name,rows in [('record_annual_quality',annual),('quality_missingness',missing),('record_value_counts',values),('quality_fields',fields),('quality_collision_conflicts',conflicts),('record_outcomes',outcomes),('record_road_users',roadusers)]:
        write_csv(tables / (name + '.csv'), rows)
    payload = {'audit_code_sha256':code_hash,'normalization':'Trim strings; integer numeric code zero-padding removed only in temporary audit view. Raw files never modified.',
        'missingness_denominator':'All source records, including dummy and unresolved identities; P_USER U is inseparable not-stated/other/unknown.',
        'runtime':{name:importlib.metadata.version(name) for name in ('duckdb','pandas','openpyxl','python-calamine')},
        'files':sorted(results,key=lambda r:(r['expected_year'],r['path']))}
    output = root / 'data/derived/quality_audit.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,indent=2) + '\n')


def run(root, workers=2, years=None, include_comparator=False):
    root = Path(root).resolve()
    manifest = json.loads((root/'data/sources.json').read_text())
    resources = [r for r in manifest['resources'] if r.get('selected') and r.get('year') is not None]
    if include_comparator:
        resources.extend(r for r in manifest.get('alternatives',[]) if r.get('year') is not None)
    selected_years = [r['year'] for r in resources if r.get('selected')]
    if len(selected_years) != len(set(selected_years)):
        raise ValueError('More than one selected resource per year')
    if any(not r.get('sha256') for r in resources):
        raise ValueError('Acquisition manifest missing SHA256')
    if years:
        resources = [r for r in resources if r['year'] in years]
    for resource in resources:
        if sha256(root/resource['local_path']) != resource['sha256']:
            raise ValueError(f"{resource['local_path']}: manifest SHA256 mismatch")
    code_hash = sha256(__file__)
    cache_path = root/'data/derived/quality_audit.json'
    cached = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    results = cached.get('files',[]) if cached.get('audit_code_sha256') == code_hash else []
    desired = {r['local_path'] for r in resources}
    by_path = {r['local_path']:r for r in resources}
    results = [r for r in results if r['path'] in desired
               and r['sha256'] == by_path[r['path']]['sha256']
               and r['source_id'] == by_path[r['path']]['resource_id']
               and r['expected_year'] == by_path[r['path']]['year']
               and r['selected'] == by_path[r['path']].get('selected',False)
               and r.get('sheet') == by_path[r['path']].get('sheet')]
    todo = [r for r in resources if r['local_path'] not in {f['path'] for f in results}]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(profile_file,(str(root),r)):r for r in todo}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            write_outputs(root,results,code_hash)
            print(f"Audited {result['path']}: {result['rows']:,} rows; {result['collisions']:,} collisions",flush=True)
    write_outputs(root,results,code_hash)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--years', type=int, nargs='+')
    parser.add_argument('--include-comparator', action='store_true')
    options = parser.parse_args()
    run(options.root,options.workers,options.years,options.include_comparator)
