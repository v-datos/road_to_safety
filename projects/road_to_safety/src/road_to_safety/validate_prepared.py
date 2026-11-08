"""Independent SQL validation of the collision table against the acquisition audit.

Run after prepare_collisions: python -m road_to_safety.validate_prepared
This module reads raw inputs only to verify their archived SHA256 fingerprints.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import itertools

import openpyxl
from pathlib import Path

import duckdb

FEATURES = 'C_MNTH C_WDAY C_HOUR C_RCFG C_WTHR C_RSUR C_RALN C_TRAF'.split()
EVENT_FIELDS = 'C_MNTH C_WDAY C_HOUR C_SEV C_VEHS C_CONF C_RCFG C_WTHR C_RSUR C_RALN C_TRAF'.split()
KEYS = ['source_id', 'C_YEAR', 'C_CASE']


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def records(connection, query):
    result = connection.execute(query)
    return [dict(zip([column[0] for column in result.description], row)) for row in result.fetchall()]


def inspect_table(connection, contract, expected_sources):
    """Validate an existing SQL relation named collisions; useful for mutation tests."""
    failures = []
    def check(name, count):
        if count:
            failures.append({'check': name, 'violations': int(count)})
    features = contract['features']
    check('exact_feature_allowlist', int(features != FEATURES))
    check('target_excluded_from_features', int(contract.get('target_column', 'is_fatal') in features))
    check('unique_collision_key', connection.execute('SELECT count(*)-count(DISTINCT (source_id,C_YEAR,C_CASE)) FROM collisions').fetchone()[0])
    check('valid_collision_key', connection.execute("SELECT count(*) FROM collisions WHERE source_id IS NULL OR trim(source_id)='' OR NOT coalesce(regexp_full_match(C_YEAR,'[0-9]{4}') AND regexp_full_match(C_CASE,'[0-9]+') AND try_cast(C_YEAR AS INTEGER) BETWEEN 1999 AND 2100 AND try_cast(C_CASE AS BIGINT)>0,false)").fetchone()[0])
    check('severity_target_mapping', connection.execute("""SELECT count(*) FROM collisions WHERE
        severity_eligible IS DISTINCT FROM coalesce((C_SEV IN ('1','2') AND NOT C_SEV_conflict),false)
        OR is_fatal IS DISTINCT FROM CASE WHEN C_SEV IN ('1','2') AND NOT C_SEV_conflict THEN CASE WHEN C_SEV='1' THEN 1 ELSE 0 END END""").fetchone()[0])
    for field in EVENT_FIELDS:
        check(f'{field}_conflict_null', connection.execute(f'SELECT count(*) FROM collisions WHERE {field}_conflict AND {field} IS NOT NULL').fetchone()[0])
    actual_sources = records(connection, 'SELECT source_id,C_YEAR,count(*) collisions,sum(diagnostic_source_rows) source_rows FROM collisions GROUP BY ALL ORDER BY C_YEAR')
    for source in actual_sources:
        expected = expected_sources.get(source['source_id'])
        check('selected_source_and_expected_year', int(expected is None or str(expected['expected_year']) != source['C_YEAR']))
        if expected:
            check('collision_count_conservation', abs(source['collisions'] - expected['collisions']))
            check('source_row_conservation', abs(source['source_rows'] - (expected['rows'] - expected['invalid_collision_key_rows'])))
    check('all_selected_sources_present', len(set(expected_sources) - {row['source_id'] for row in actual_sources}))
    for field in ['diagnostic_source_rows', 'diagnostic_exact_duplicate_extra_rows', 'diagnostic_identified_person_keys', 'diagnostic_unresolved_person_rows']:
        check(f'{field}_nonnegative', connection.execute(f'SELECT count(*) FROM collisions WHERE {field} IS NULL OR {field}<0').fetchone()[0])
    check('person_row_key_conservation', connection.execute('SELECT count(*) FROM collisions WHERE diagnostic_identified_person_keys > diagnostic_source_rows-diagnostic_unresolved_person_rows').fetchone()[0])
    # Preserve undocumented values, but expose them as quality exceptions rather than recoding them.
    domains = []
    missingness = []
    for field in FEATURES:
        allowed = contract['categorical_domains'][field]
        values = records(connection, f'SELECT C_YEAR,{field} AS value,{field}_conflict AS conflict,count(*) collisions FROM collisions GROUP BY ALL ORDER BY C_YEAR,value')
        for row in values:
            value = row['value']
            value_class = ('conflict' if row['conflict'] else 'null' if value is None else 'blank' if not value else
                           'unknown' if set(value)=={'U'} else 'jurisdiction_unavailable' if set(value)=={'X'} else
                           'undocumented_n_token' if set(value)=={'N'} else 'other' if set(value)=={'Q'} else
                           'unresolved_star_code' if '*' in value else 'stated')
            missingness.append({'field': field, **row, 'value_class': value_class})
            if value is not None and value not in allowed:
                domains.append({'field': field, **row, 'dictionary_supported': False})
    return {'failures': failures, 'sources': actual_sources, 'value_counts': missingness, 'domain_exceptions': domains}


def verify_raw_samples(root, connection, selected, limit=100):
    """Compare bounded source values to final event attributes using independent readers."""
    checked, mismatches = [], []
    english = 'C_YEAR C_MNTH C_WDAY C_HOUR C_SEV C_VEHS C_CONF C_RCFG C_WTHR C_RSUR C_RALN C_TRAF V_ID V_TYPE V_YEAR P_ID P_SEX P_AGE P_PSN P_ISEV P_SAFE P_USER C_CASE'.split()
    french = 'C_ANNÉE C_MOIS C_JSEM C_HEURE C_GRAVITÉ C_VÉH C_CFG C_CFGR C_MÉTEO C_ÉCHSÉ C_TRAR C_CIRC V_ID V_TYPE V_ANNÉE P_ID P_SEXE P_ÂGE P_LOCP P_ISEV P_SÉCURITÉ P_USAG C_CAS'.split()
    def canonical(value):
        text = '' if value is None else str(value).strip()
        return str(int(text)) if text and text.isascii() and text.isdigit() else text
    for source_id, resource in selected.items():
        path = root/resource['local_path']
        if path.suffix == '.xlsx':
            workbook = openpyxl.load_workbook(path,read_only=True,data_only=True)
            source_rows = workbook[resource.get('sheet') or 'in'].iter_rows(values_only=True)
            headers = list(next(source_rows))
            sample = list(itertools.islice(source_rows,limit))
            workbook.close()
        else:
            with path.open(newline='',encoding='cp1252' if '-fr' in path.name else 'utf-8-sig') as stream:
                source_rows = csv.reader(stream)
                headers = next(source_rows)
                sample = list(itertools.islice(source_rows,limit))
        if headers not in [english,french]:
            raise ValueError(f'Unexpected source sample headers: {path}')
        # Explicit bilingual positional mapping is checked before interpreting any value.
        canonical_sample = [dict(zip(english,map(canonical,raw))) for raw in sample]
        cases = sorted({row['C_CASE'] for row in canonical_sample})
        query = 'SELECT * FROM collisions WHERE source_id=? AND C_YEAR=? AND C_CASE IN ('+','.join('?' for _ in cases)+')'
        result = connection.execute(query,[source_id,str(resource['year']),*cases])
        field_names = [column[0] for column in result.description]
        sample_events = {}
        for values in result.fetchall():
            event = dict(zip(field_names,values))
            sample_events.setdefault((event['C_YEAR'],event['C_CASE']),[]).append(event)
        rows_checked = 0
        for row in canonical_sample:
            found = sample_events.get((row['C_YEAR'],row['C_CASE']),[])
            if len(found)!=1:
                mismatches.append({'source_id':source_id,'check':'sample_event_key','violations':1})
                continue
            for field in EVENT_FIELDS:
                if not found[0][field+'_conflict'] and row[field] != found[0][field]:
                    mismatches.append({'source_id':source_id,'check':'sample_'+field,'violations':1})
            rows_checked += 1
        checked.append({'source_id':source_id,'year':resource['year'],'source_rows_checked':rows_checked})
    return checked,mismatches


def write_csv(path, rows, fields=None):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def published_profile_counts(rows):
    return {(row['observed_year'], row['field'], row['value'],
             row['value_class'] == 'conflict'): int(row['collisions']) for row in rows}


def run(root):
    root = Path(root).resolve()
    derived = root/'data/derived'
    reports = root/'reports/tables'
    contract_path = root/'data/reference/modeling_contract.json'
    contract = json.loads(contract_path.read_text())
    audit_path = derived/'quality_audit.json'
    audit = json.loads(audit_path.read_text())
    expected = {row['source_id']:row for row in audit['files'] if row['selected']}
    manifest = json.loads((root/'data/sources.json').read_text())
    selected = {row['resource_id']:row for row in manifest['resources'] if row.get('selected') and row.get('year') is not None}
    failures = []
    if set(expected) != set(selected):
        failures.append({'check':'audit_manifest_source_selection', 'violations':1})
    raw_hashes = []
    for resource in manifest['resources']:
        if not resource.get('selected'):
            continue
        actual = fingerprint(root/resource['local_path'])
        matches = actual == resource['sha256']
        if resource['resource_id'] in expected:
            matches = matches and actual == expected[resource['resource_id']]['sha256']
        raw_hashes.append({'source_id':resource['resource_id'], 'path':resource['local_path'], 'sha256':actual, 'matches_acquisition_and_audit':matches})
        if not matches:
            failures.append({'check':'raw_sha256_unchanged','violations':1})
    connection = duckdb.connect()
    connection.execute("SET threads=2")
    connection.read_parquet(str(derived/'collisions.parquet')).create_view('collisions')
    result = inspect_table(connection, contract, expected)
    sampled_sources, sample_errors = verify_raw_samples(root, connection, selected)
    failures += sample_errors
    failures += result.pop('failures')
    annual = records(connection, """SELECT source_id,C_YEAR,count(*) collisions,sum(diagnostic_source_rows) source_rows,
        count(*) FILTER(WHERE severity_eligible) eligible_collisions,count(*) FILTER(WHERE NOT severity_eligible) ineligible_collisions,
        count(*) FILTER(WHERE is_fatal=1) fatal_collisions,count(*) FILTER(WHERE is_fatal=0) injury_collisions,
        sum(diagnostic_exact_duplicate_extra_rows) exact_duplicate_extra_rows,
        sum(diagnostic_identified_person_keys) identified_person_keys,
        sum(diagnostic_duplicate_person_keys) duplicate_identified_person_keys,
        sum(diagnostic_vehicle_conflict_keys) vehicle_attribute_conflict_keys,
        sum(diagnostic_person_severity_conflict_keys) person_severity_conflict_keys,
        sum(diagnostic_unresolved_person_rows) unresolved_person_identity_rows,
        sum(diagnostic_pedestrian_dummy_rows) pedestrian_dummy_vehicle_rows,
        sum(diagnostic_dummy_person_rows) dummy_person_rows
        FROM collisions GROUP BY ALL ORDER BY C_YEAR""")
    comparisons = []
    for row in annual:
        reference = expected.get(row['source_id'], {})
        for field, observed in row.items():
            if field not in reference or field in ('source_id',):
                continue
            matches = observed == reference[field]
            comparisons.append({'source_id':row['source_id'],'year':row['C_YEAR'],'metric':field,'observed':observed,'audit':reference[field],'matches':matches})
            if not matches:
                failures.append({'check':f'annual_audit_{field}', 'violations':abs(observed-reference[field])})
    lineage_errors = 0
    for source_id, reference in expected.items():
        lineage_errors += connection.execute('SELECT count(*) FROM collisions WHERE source_id=? AND (source_path IS DISTINCT FROM ? OR source_sha256 IS DISTINCT FROM ?)', [source_id,reference['path'],reference['sha256']]).fetchone()[0]
    if lineage_errors:
        failures.append({'check':'row_source_lineage','violations':lineage_errors})
    conflict_counts = records(connection, 'SELECT ' + ','.join(f'count(*) FILTER (WHERE {field}_conflict) {field}' for field in EVENT_FIELDS) + ' FROM collisions')[0]
    for field, observed in conflict_counts.items():
        baseline = sum(next(item['conflict_collisions'] for item in row['collision_attribute_conflicts'] if item['field']==field) for row in expected.values())
        if observed != baseline:
            failures.append({'check':f'{field}_audit_conflict_count','violations':abs(observed-baseline)})
    preparation_path = derived/'preparation_manifest.json'
    preparation = json.loads(preparation_path.read_text())
    expected_hashes = {'preparation_code_sha256':root/'src/road_to_safety/prepare_collisions.py',
                       'audit_code_sha256':root/'src/road_to_safety/audit_data.py',
                       'audit_sha256':audit_path,'source_manifest_sha256':root/'data/sources.json',
                       'modeling_contract_sha256':contract_path}
    for key, path in expected_hashes.items():
        if fingerprint(path) != preparation[key]:
            failures.append({'check':key,'violations':1})
    for output in preparation['outputs']:
        if fingerprint(root/output['path']) != output['sha256']:
            failures.append({'check':'prepared_output_fingerprint','violations':1})
    connection.read_parquet(str(derived/'preparation_exceptions.parquet')).create_view('exceptions')
    exception_checks = {
        'unique_exception_source_row': "SELECT count(*)-count(DISTINCT (source_id,source_row_number)) FROM exceptions",
        'exception_has_reason': "SELECT count(*) FROM exceptions WHERE reasons IS NULL OR len(reasons)=0",
        'invalid_key_exception_conservation': "SELECT count(*) FROM exceptions WHERE list_contains(reasons,'invalid_collision_key')",
        'unresolved_person_exception_conservation': "SELECT count(*) FROM exceptions WHERE list_contains(reasons,'unresolved_person_identity')",
        'dummy_person_exception_conservation': "SELECT count(*) FROM exceptions WHERE list_contains(reasons,'dummy_person')",
        'pedestrian_dummy_exception_conservation': "SELECT count(*) FROM exceptions WHERE list_contains(reasons,'pedestrian_dummy_vehicle')",
        'duplicate_person_exception_conservation': "SELECT count(*) FROM exceptions WHERE list_contains(reasons,'duplicate_identified_person_key')",
        'valid_exception_collision_join': "SELECT count(*) FROM exceptions e LEFT JOIN collisions c ON e.source_id=c.source_id AND try_cast(e.C_YEAR AS INTEGER)=try_cast(c.C_YEAR AS INTEGER) AND try_cast(e.C_CASE AS BIGINT)=try_cast(c.C_CASE AS BIGINT) WHERE NOT list_contains(e.reasons,'invalid_collision_key') AND c.source_id IS NULL",
    }
    expected_exception = {'invalid_key_exception_conservation':'invalid_collision_key_rows',
                          'unresolved_person_exception_conservation':'unresolved_person_identity_rows',
                          'dummy_person_exception_conservation':'dummy_person_rows',
                          'pedestrian_dummy_exception_conservation':'pedestrian_dummy_vehicle_rows',
                          'duplicate_person_exception_conservation':'rows_on_duplicate_identified_person_keys'}
    exception_counts = {}
    for key, query in exception_checks.items():
        observed = connection.execute(query).fetchone()[0]
        exception_counts[key] = observed
        baseline = sum(row[expected_exception[key]] for row in expected.values()) if key in expected_exception else 0
        if observed != baseline:
            failures.append({'check':key,'violations':abs(observed-baseline)})
    exception_total = connection.execute('SELECT count(*) FROM exceptions').fetchone()[0]
    if exception_total != preparation['totals']['exception_rows']:
        failures.append({'check':'exception_manifest_count','violations':abs(exception_total-preparation['totals']['exception_rows'])})
    for source_id, reference in expected.items():
        count = connection.execute('SELECT count(*) FROM exceptions WHERE source_id=? AND (source_path IS DISTINCT FROM ? OR source_sha256 IS DISTINCT FROM ?)', [source_id,reference['path'],reference['sha256']]).fetchone()[0]
        if count:
            failures.append({'check':'exception_source_lineage','violations':count})
    # Recompute original person injury-label disagreement on all implicated raw exception rows.
    severity_conflicts = connection.execute("""SELECT count(*) FROM (
        SELECT source_id,try_cast(C_YEAR AS INTEGER),try_cast(C_CASE AS BIGINT),try_cast(V_ID AS INTEGER),try_cast(P_ID AS INTEGER)
        FROM exceptions WHERE list_contains(reasons,'duplicate_identified_person_key')
        GROUP BY ALL HAVING count(DISTINCT CASE WHEN regexp_full_match(trim(P_ISEV),'[0-9]+') THEN CAST(try_cast(trim(P_ISEV) AS BIGINT) AS VARCHAR) ELSE trim(P_ISEV) END)>1)""").fetchone()[0]
    if severity_conflicts != sum(row['person_severity_conflict_keys'] for row in expected.values()):
        failures.append({'check':'person_severity_conflict_audit','violations':1})
    # Counts of each canonical predictor value must exactly match the builder's published profile.
    with (reports/'preparation_missingness.csv').open(newline='') as stream:
        published_rows = [row for row in csv.DictReader(stream) if row['field'] in FEATURES]
        published = published_profile_counts(published_rows)
    independently_computed = {(row['C_YEAR'],row['field'],row['value'] if row['value'] is not None else '',row['conflict']):row['collisions'] for row in result['value_counts']}
    if independently_computed != published:
        failures.append({'check':'published_missingness_value_counts','violations':sum(independently_computed.get(key)!=published.get(key) for key in independently_computed.keys() | published.keys())})
    denominators = {row['C_YEAR']:row['collisions'] for row in annual}
    for row in published_rows:
        denominator = denominators[row['observed_year']]
        if int(row['collision_denominator']) != denominator or abs(float(row['collision_rate'])-int(row['collisions'])/denominator)>1e-12:
            failures.append({'check':'published_missingness_denominator_rate','violations':1})
    grouped = {}
    for row in result['value_counts']:
        key = (row['C_YEAR'],row['field'],row['value_class'])
        grouped[key] = grouped.get(key,0)+row['collisions']
    profiles = [{'year':year,'field':field,'value_class':value_class,'collisions':count,'denominator_collisions':denominators[year],'fraction':count/denominators[year]} for (year,field,value_class),count in sorted(grouped.items())]
    write_csv(reports/'validation_annual.csv', annual)
    write_csv(reports/'validation_audit_reconciliation.csv', comparisons)
    write_csv(reports/'validation_missingness.csv', profiles)
    write_csv(reports/'validation_domain_exceptions.csv', result['domain_exceptions'], ['field','C_YEAR','value','conflict','collisions','dictionary_supported'])
    write_csv(reports/'validation_feature_values.csv', result['value_counts'])
    outputs = [derived/'collisions.parquet', derived/'preparation_exceptions.parquet',derived/'preparation_manifest.json']
    receipt = {'status':'passed' if not failures else 'failed','failures':failures,
        'method':'Independent DuckDB full-table SQL checks against acquisition manifest and previous quality audit; no model training or EDA.',
        'collisions':sum(row['collisions'] for row in annual),'source_rows':sum(row['source_rows'] for row in annual),
        'fatal_collisions':sum(row['fatal_collisions'] for row in annual),'injury_collisions':sum(row['injury_collisions'] for row in annual),
        'ineligible_collisions':sum(row['ineligible_collisions'] for row in annual),
        'domain_exception_collision_values':sum(row['collisions'] for row in result['domain_exceptions']),
        'bounded_source_value_samples':sampled_sources,'conflict_counts':conflict_counts,'exception_rows':exception_total,'exception_checks':exception_counts,'person_severity_conflict_keys':severity_conflicts,'raw_fingerprints':raw_hashes,
        'input_fingerprints':{str(path.relative_to(root)):fingerprint(path) for path in [audit_path,contract_path,root/'data/sources.json',Path(__file__),*outputs] if path.exists()},
        'tables':{str(path.relative_to(root)):fingerprint(path) for path in sorted(reports.glob('validation_*.csv'))}}
    (derived/'prepared_validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    connection.close()
    if failures:
        raise ValueError(f'Prepared validation failed: {failures}')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    receipt = run(args.root)
    print(json.dumps({key:receipt[key] for key in ['status','collisions','source_rows','fatal_collisions','injury_collisions','ineligible_collisions']}))


if __name__ == '__main__':
    main()
