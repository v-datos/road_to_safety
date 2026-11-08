"""Build linked bicycle collision records for the available public years."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

import duckdb
from openpyxl import load_workbook

from .acquire import sha256

COLUMNS = 'C_YEAR C_MNTH C_WDAY C_HOUR C_SEV C_VEHS C_CONF C_RCFG C_WTHR C_RSUR C_RALN C_TRAF V_ID V_TYPE V_YEAR P_ID P_SEX P_AGE P_PSN P_ISEV P_SAFE P_USER C_CASE'.split()
FRENCH = dict(zip('C_ANNÉE C_MOIS C_JSEM C_HEURE C_GRAVITÉ C_VÉH C_CFG C_CFGR C_MÉTEO C_ÉCHSÉ C_TRAR C_CIRC V_ID V_TYPE V_ANNÉE P_ID P_SEXE P_ÂGE P_LOCP P_ISEV P_SÉCURITÉ P_USAG C_CAS'.split(), COLUMNS))
TWO_DIGIT = set('C_MNTH C_HOUR C_VEHS C_CONF C_RCFG C_TRAF V_ID V_TYPE P_ID P_AGE P_PSN P_SAFE'.split())
EVENT_KEY = 'source_id,C_YEAR,C_CASE'
VEHICLE_KEY = EVENT_KEY+',V_ID'
PERSON_KEY = VEHICLE_KEY+',P_ID'
EVENT_FIELDS = [c for c in COLUMNS if c.startswith('C_') and c not in {'C_YEAR','C_CASE'}]


def quote(value):
    return "'"+str(value).replace("'", "''")+"'"


def rows(connection, query):
    result = connection.execute(query)
    return [dict(zip([c[0] for c in result.description], row)) for row in result.fetchall()]


def export(connection, query, path):
    options = 'HEADER' if path.suffix == '.csv' else 'FORMAT PARQUET, COMPRESSION ZSTD'
    connection.execute(f'COPY ({query}) TO {quote(path)} ({options})')


def canonical_csv(original, source, temporary):
    if original.suffix == '.xlsx':
        target = temporary/(source['id']+'.csv')
        workbook = load_workbook(original, read_only=True, data_only=True)
        sheet = workbook[source.get('sheet', workbook.sheetnames[0])]
        with target.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            for record in sheet.iter_rows(values_only=True):
                if any(value is not None for value in record):
                    writer.writerow(record)
        workbook.close()
        return target, 'utf-8-sig'
    encoding = source.get('encoding','utf-8-sig')
    if encoding.lower() not in {'utf-8','utf-8-sig'}:
        target = temporary/(source['id']+'.csv')
        with original.open(encoding=encoding) as inp, target.open('w',encoding='utf-8') as out:
            for line in inp:
                out.write(line)
        return target, 'utf-8-sig'
    return original, encoding


def derive(connection):
    """Resolve grains without inventing people for unknown identities."""
    connection.execute(f'''CREATE OR REPLACE TABLE clean AS SELECT DISTINCT * FROM records
        WHERE regexp_full_match(C_CASE,'[0-9]+') AND try_cast(C_CASE AS DECIMAL(38,0))>0
        AND regexp_full_match(C_YEAR,'[0-9]{{4}}')''')
    attributes = ','.join(f'CASE WHEN count(DISTINCT {f})=1 THEN min({f}) END AS {f}' for f in EVENT_FIELDS)
    conflicts = '+'.join(f'cast(count(DISTINCT {f})>1 AS INTEGER)' for f in EVENT_FIELDS)
    connection.execute(f'''CREATE OR REPLACE TABLE collisions AS
        SELECT {EVENT_KEY},{attributes},({conflicts}) AS attribute_conflicts,
        count(*) AS distinct_record_rows FROM clean GROUP BY {EVENT_KEY}''')
    connection.execute(f'''CREATE OR REPLACE TABLE vehicles AS SELECT {VEHICLE_KEY},
        count(DISTINCT V_TYPE) AS type_variants,
        CASE WHEN count(DISTINCT V_TYPE)=1 THEN min(V_TYPE) END AS V_TYPE,
        bool_or(V_TYPE='17') AS bicycle_record_present
        FROM clean WHERE regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '98'
        GROUP BY {VEHICLE_KEY}''')
    connection.execute(f'''CREATE OR REPLACE TABLE people AS SELECT {PERSON_KEY},
        CASE WHEN count(DISTINCT P_USER)=1 THEN min(P_USER) ELSE 'conflict' END AS P_USER,
        CASE WHEN count(DISTINCT P_SEX)=1 THEN min(P_SEX) ELSE 'conflict' END AS P_SEX,
        CASE WHEN count(DISTINCT P_AGE)=1 THEN min(P_AGE) ELSE 'conflict' END AS P_AGE,
        count(DISTINCT P_ISEV) AS severity_variants,
        string_agg(DISTINCT P_ISEV,'|' ORDER BY P_ISEV) AS severity_codes,
        CASE WHEN count(DISTINCT P_ISEV)=1 THEN min(P_ISEV) END AS P_ISEV,
        bool_or(V_TYPE='17') AS bicycle_record_present,
        bool_or(P_USER='4') AS bicyclist_code_present,
        count(DISTINCT P_USER)>1 AS road_user_conflict,
        min(P_ISEV='3')::INTEGER AS deaths_min, max(P_ISEV='3')::INTEGER AS deaths_max,
        min(P_ISEV='2')::INTEGER AS injuries_min, max(P_ISEV='2')::INTEGER AS injuries_max
        FROM clean WHERE regexp_full_match(V_ID,'[0-9]{{2}}') AND V_ID BETWEEN '01' AND '99'
        AND regexp_full_match(P_ID,'[0-9]{{2}}') AND P_ID BETWEEN '01' AND '99'
        GROUP BY {PERSON_KEY}''')
    connection.execute('''CREATE OR REPLACE TABLE unresolved_records AS SELECT * FROM clean
        WHERE NOT (coalesce(regexp_full_match(V_ID,'[0-9]{2}') AND V_ID BETWEEN '01' AND '99',false)
          AND coalesce(regexp_full_match(P_ID,'[0-9]{2}') AND P_ID BETWEEN '01' AND '99',false))''')


def main():
    root = Path.cwd()
    output = root/'data/derived'
    output.mkdir(parents=True, exist_ok=True)
    sources = json.loads((root/'data/sources.json').read_text())
    selected = [y for s in sources for y in s['selected_years']]
    if sorted(selected) != list(range(2010,2022)):
        raise ValueError('The selected record releases must cover 2010–2021 exactly once')
    db = output/'build.duckdb'
    connection = duckdb.connect(str(db))
    connection.execute("SET memory_limit='2GB'")
    connection.execute('SET threads=2')
    connection.execute('SET preserve_insertion_order=false')
    connection.execute('DROP TABLE IF EXISTS records')
    acquisition = []
    orphan_counts = []
    with tempfile.TemporaryDirectory(prefix='bicycle-input-',dir=output) as temporary:
        for i, source in enumerate(sources):
            original = root/source['path']
            if sha256(original) != source['sha256']:
                raise ValueError(f'Checksum mismatch: {original}')
            print(f'Reading {source["id"]}',flush=True)
            path, encoding = canonical_csv(original,source,Path(temporary))
            with path.open(encoding=encoding,newline='') as stream:
                header = next(csv.reader(stream))
            mapped = [FRENCH.get(name.strip(),name.strip()) for name in header]
            if mapped != COLUMNS:
                raise ValueError(f'Unexpected schema: {source["id"]}')
            expressions=[]
            for raw, canonical in zip(header,COLUMNS):
                value='trim("'+raw.replace('"','""')+'")'
                if canonical in TWO_DIGIT:
                    value=f"CASE WHEN regexp_full_match({value},'[0-9]') THEN '0'||{value} ELSE {value} END"
                expressions.append(f'{value} AS {canonical}')
            query=f"SELECT {quote(source['id'])} AS source_id,{','.join(expressions)} FROM read_csv({quote(path)},all_varchar=true,header=true,strict_mode=true)"
            connection.execute(f'CREATE OR REPLACE TEMP VIEW input_records AS {query}')
            physical=[r[0] for r in connection.execute('SELECT DISTINCT try_cast(C_YEAR AS INTEGER) FROM input_records ORDER BY 1').fetchall()]
            if physical != list(range(source['first_year'],source['last_year']+1)):
                raise ValueError(f'Physical year coverage mismatch: {physical}')
            years=','.join(map(str,source['selected_years']))
            connection.execute(f'CREATE OR REPLACE TEMP TABLE year_records AS SELECT * FROM input_records WHERE try_cast(C_YEAR AS INTEGER) IN ({years})')
            connection.execute(f"CREATE OR REPLACE TEMP TABLE bicycle_events AS SELECT DISTINCT {EVENT_KEY} FROM year_records WHERE V_TYPE='17'")
            orphan_counts += rows(connection,f'''SELECT cast(C_YEAR AS INTEGER) AS year,count(DISTINCT C_CASE) AS bicyclist_events_without_bicycle
                FROM year_records r WHERE P_USER='4' AND NOT EXISTS(SELECT 1 FROM bicycle_events e
                WHERE e.source_id=r.source_id AND e.C_YEAR=r.C_YEAR AND e.C_CASE=r.C_CASE) GROUP BY C_YEAR''')
            verb='CREATE TABLE records AS' if i==0 else 'INSERT INTO records'
            connection.execute(f'{verb} SELECT r.* FROM year_records r JOIN bicycle_events e USING({EVENT_KEY})')
            acquisition.append(dict(source_id=source['id'],path=source['path'],sha256=source['sha256'],
                selected_years=source['selected_years'],physical_years=physical))
            print(f'Loaded bicycle-linked records: {source["selected_years"]}',flush=True)
    derive(connection)
    for table,filename in [('records','records.parquet'),('collisions','bicycle_collisions.parquet'),
            ('vehicles','vehicles.parquet'),('people','people.parquet'),('unresolved_records','unresolved_records.parquet')]:
        export(connection,f'SELECT * FROM {table}',output/filename)
    quality = {
        'input_rows':connection.execute('SELECT count(*) FROM records').fetchone()[0],
        'distinct_rows':connection.execute('SELECT count(*) FROM clean').fetchone()[0],
        'invalid_key_rows':connection.execute('''SELECT count(*) FROM records WHERE NOT coalesce(
            regexp_full_match(C_CASE,'[0-9]+') AND try_cast(C_CASE AS DECIMAL(38,0))>0,false)''').fetchone()[0],
        'collision_attribute_conflicts':connection.execute('SELECT count(*) FROM collisions WHERE attribute_conflicts>0').fetchone()[0],
        'person_severity_conflicts':connection.execute('SELECT count(*) FROM people WHERE severity_variants>1').fetchone()[0],
        'person_road_user_conflicts':connection.execute('SELECT count(*) FROM people WHERE road_user_conflict').fetchone()[0],
        'bicycle_role_disagreements':connection.execute("SELECT count(*) FROM people WHERE (P_USER='4') IS DISTINCT FROM bicycle_record_present").fetchone()[0],
        'unresolved_rows':connection.execute('SELECT count(*) FROM unresolved_records').fetchone()[0],
        'unresolved_positive_casualty_rows':connection.execute("SELECT count(*) FROM unresolved_records WHERE P_ISEV IN ('2','3')").fetchone()[0],
        'bicyclist_events_without_bicycle':orphan_counts,
        'annual':rows(connection,'''SELECT cast(C_YEAR AS INTEGER) AS year,count(*) AS collisions,
            count(*) FILTER(WHERE C_SEV='1') AS fatal_collisions,
            count(*) FILTER(WHERE C_SEV='2') AS injury_collisions,
            count(*) FILTER(WHERE C_SEV IS NULL) AS unknown_severity_collisions
            FROM collisions GROUP BY C_YEAR ORDER BY C_YEAR''')}
    assert [r['year'] for r in quality['annual']]==list(range(2010,2022))
    assert all(r['collisions']==r['fatal_collisions']+r['injury_collisions']+r['unknown_severity_collisions'] for r in quality['annual'])
    quality.update(built_at=datetime.now(timezone.utc).isoformat(),code_sha256=sha256(Path(__file__)),sources=acquisition)
    (output/'validation.json').write_text(json.dumps(quality,indent=2)+'\n')
    print(json.dumps({k:v for k,v in quality.items() if k not in {'sources','annual'}},indent=2),flush=True)
    connection.close()


if __name__=='__main__':
    main()
