"""Resolve observed person keys in all records of road-tractor casualty collisions.

Run: PYTHONPATH=src .venv/bin/python -m truck_collisions.build_casualties
Ranges are source-record resolution scenarios, never bounds on true population harm.
"""
import argparse
from collections import Counter, defaultdict
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile

import duckdb

from .build import COLUMNS, TWO_DIGIT, prepare_csv, quote, sha256, export, selected_years, select_source_records

GROUPS = ('tractor_occupant', 'other_motor_vehicle_occupant', 'pedestrian',
          'cyclist', 'motorcyclist', 'other_or_unknown', 'ambiguous')
MOTOR_TYPES = {'01', '05', '06', '07', '09', '10', '11', '18', '19', '20', '21', '23'}
IDENTITY = ('source_id', 'C_YEAR', 'C_CASE', 'V_ID', 'P_ID')
PERSON_FIELDS = ('P_SEX', 'P_AGE', 'P_PSN', 'P_ISEV', 'P_SAFE', 'P_USER')


def valid_id(value):
    return isinstance(value, str) and len(value) == 2 and value.isdigit() and '01' <= value <= '99'


def classify_record(record, vehicle_types):
    """Use concordant role/vehicle/position evidence; contradictory evidence is explicit."""
    user, position, vehicle = record.get('P_USER'), record.get('P_PSN'), record.get('V_ID')
    signals = set()
    if user == '3' or position == '99' or vehicle == '99':
        signals.add('pedestrian')
    if user == '4':
        signals.add('cyclist')
    if user == '5':
        signals.add('motorcyclist')
    for kind in vehicle_types:
        if kind == '08':
            signals.add('tractor_occupant')
        elif kind in MOTOR_TYPES:
            signals.add('other_motor_vehicle_occupant')
        elif kind == '17':
            signals.add('cyclist')
        elif kind == '14':
            signals.add('motorcyclist')
        elif kind in {'16', '22'}:
            signals.add('other_or_unknown')
    # Vehicle-role contradictions are not resolved by choosing one field.
    if user in {'1', '2'} and signals.intersection({'pedestrian', 'cyclist', 'motorcyclist'}):
        return 'ambiguous'
    if len(signals) > 1:
        return 'ambiguous'
    return next(iter(signals)) if signals else 'other_or_unknown'


def resolve_person_records(records, events):
    """Return identified units, all normalized alternatives, unresolved/dummy rows, quality.

    Known composite keys are assumed to refer to one recorded person; conflicting
    alternatives are preserved. Unknown identities are never given surrogate IDs.
    """
    event_map = {(str(e['source_id']), str(e['C_YEAR']), str(e['C_CASE'])): e for e in events}
    selected = []
    for original in records:
        row = {name: original.get(name) for name in ('source_id', *COLUMNS)}
        row['C_YEAR'] = str(row['C_YEAR'])
        event = event_map.get(tuple(row[name] for name in IDENTITY[:3]))
        if event is None:
            raise ValueError('Record has no selected tractor parent event')
        selected.append(row)
    vehicle_types = defaultdict(set)
    for row in selected:
        if valid_id(row['V_ID']) and row['V_ID'] != '99':
            vehicle_types[tuple(row[name] for name in IDENTITY[:4])].add(row['V_TYPE'])
    columns = ('source_id', *COLUMNS)
    multiplicities = Counter(tuple(row[name] for name in columns) for row in selected)
    known = defaultdict(list)
    alternatives, unresolved = [], []
    for values, multiplicity in sorted(multiplicities.items(), key=lambda x: tuple('' if v is None else str(v) for v in x[0])):
        row = dict(zip(columns, values))
        event = event_map[tuple(row[name] for name in IDENTITY[:3])]
        types = vehicle_types.get(tuple(row[name] for name in IDENTITY[:4]), {row['V_TYPE']})
        # Unknown vehicle types mixed with a positive category remain assignment uncertainty.
        group = classify_record(row, types)
        vehicle_conflict = len(types) > 1
        if vehicle_conflict and group not in {'pedestrian', 'cyclist', 'motorcyclist'}:
            group = 'ambiguous'
        status = 'dummy' if row['P_ID'] == 'NN' else ('identified' if valid_id(row['V_ID']) and valid_id(row['P_ID']) else 'unresolved_identity')
        out = {**row, 'C_YEAR': int(row['C_YEAR']), 'record_multiplicity': multiplicity,
               'identity_status': status, 'road_user_group': group,
               'vehicle_type_conflict': vehicle_conflict,
               'is_analysis_candidate': bool(event['is_analysis_candidate'])}
        alternatives.append(out)
        if status == 'identified':
            known[tuple(row[name] for name in IDENTITY)].append(out)
        else:
            unresolved.append(out)
    units = []
    for key, rows in sorted(known.items()):
        severities = {r['P_ISEV'] for r in rows}
        groups = {r['road_user_group'] for r in rows}
        event = event_map[key[:3]]
        unit = dict(zip(IDENTITY, key))
        unit.update(C_YEAR=int(key[1]), is_analysis_candidate=bool(event['is_analysis_candidate']),
                    event_severity=event['C_SEV'], road_user_group=next(iter(groups)) if len(groups) == 1 else 'ambiguous',
                    severity_codes='|'.join(sorted(str(s) for s in severities)),
                    record_variants=len(rows), input_record_rows=sum(r['record_multiplicity'] for r in rows),
                    person_attribute_conflict=len({tuple(r[n] for n in PERSON_FIELDS) for r in rows}) > 1,
                    severity_conflict=len(severities) > 1,
                    unknown_severity=bool(severities.difference({'1', '2', '3', 'N'})),
                    not_applicable_severity='N' in severities,
                    vehicle_type_conflict=any(r['vehicle_type_conflict'] for r in rows),
                    road_user_group_conflict=len(groups) > 1 or 'ambiguous' in groups)
        for label, codes in [('deaths', {'3'}), ('injuries', {'2'}), ('casualties', {'2', '3'})]:
            unit[label + '_min'] = int(severities.issubset(codes))
            unit[label + '_max'] = int(bool(severities.intersection(codes)))
        units.append(unit)
    quality = {
        'input_record_rows': len(selected), 'distinct_normalized_records': len(alternatives),
        'exact_repeated_rows_beyond_first': len(selected) - len(alternatives),
        'identified_person_keys': len(units),
        'conflicting_person_keys': sum(u['person_attribute_conflict'] for u in units),
        'conflicting_severity_keys': sum(u['severity_conflict'] for u in units),
        'ambiguous_group_keys': sum(u['road_user_group'] == 'ambiguous' for u in units),
        'unresolved_identity_rows': sum(r['record_multiplicity'] for r in unresolved if r['identity_status'] == 'unresolved_identity'),
        'dummy_rows': sum(r['record_multiplicity'] for r in unresolved if r['identity_status'] == 'dummy'),
        'dummy_positive_casualty_rows': sum(r['record_multiplicity'] for r in unresolved if r['identity_status'] == 'dummy' and r['P_ISEV'] in {'2', '3'}),
    }
    return units, alternatives, unresolved, quality


def write_records(connection, rows, path):
    # JSON staging keeps nullable fields and booleans stable without pandas/Arrow.
    target = path.with_suffix('.jsonl')
    with target.open('w') as handle:
        for row in rows:
            handle.write(json.dumps(row) + '\n')
    if not rows:
        raise ValueError(f'Expected nonempty output: {path}')
    export(connection, f'SELECT * FROM read_json_auto({quote(target)},maximum_object_size=1048576)', path)
    target.unlink()


def build_dataset(root, sources, output, event_path=None):
    root, output = Path(root), Path(output)
    if len({source['id'] for source in sources}) != len(sources):
        raise ValueError('Source IDs must be unique')
    selected = {(source['id'], year) for source in sources for year in selected_years(source)}
    if len(selected) != len({year for _, year in selected}):
        raise ValueError('Overlapping source years')
    event_path = Path(event_path) if event_path else root / 'data/derived/ncdb/road_tractor_collisions.parquet'
    output.mkdir(parents=True, exist_ok=True)
    stage = output / 'staging.duckdb'
    if stage.exists():
        stage.unlink()
    connection = duckdb.connect(str(stage))
    connection.execute("SET memory_limit='2GB'")
    connection.execute('SET threads=2')
    connection.execute(f'CREATE TABLE events AS SELECT * FROM read_parquet({quote(event_path)})')
    event_sources = connection.execute('SELECT DISTINCT source_id,C_YEAR FROM events').fetchall()
    if any(pair not in selected for pair in event_sources):
        connection.close()
        raise ValueError('Event source/year not selected by the supplied source releases')
    manifest = []
    with tempfile.TemporaryDirectory(prefix='person-ncdb-', dir=output) as temporary:
        for i, source in enumerate(sources):
            original = root / source['path']
            checksum = sha256(original)
            if source.get('sha256') and checksum != source['sha256']:
                raise ValueError(f'Checksum mismatch {original}')
            path, header = prepare_csv(original, source, Path(temporary))
            expressions = []
            for old, name in zip(header, COLUMNS):
                value = 'trim("' + old.replace('"', '""') + '")'
                if name in TWO_DIGIT:
                    value = f"CASE WHEN regexp_full_match({value},'[0-9]') THEN '0'||{value} ELSE {value} END"
                expressions.append(f'{value} AS "{name}"')
            query = f"SELECT {quote(source['id'])} source_id,{','.join(expressions)} FROM read_csv({quote(path)},header=true,all_varchar=true,strict_mode=true)"
            query = select_source_records(connection, source, query)
            connection.execute(('CREATE TABLE records AS ' if i == 0 else 'INSERT INTO records ') + f'SELECT r.* FROM ({query}) r JOIN events e ON try_cast(r.C_YEAR AS INTEGER)=e.C_YEAR AND r.C_CASE=e.C_CASE AND r.source_id=e.source_id')
            manifest.append({**source, 'sha256': checksum, 'size_bytes': original.stat().st_size})
            print('Loaded tractor-event people:', source['id'], flush=True)
    result = connection.execute('SELECT * FROM records')
    names = [d[0] for d in result.description]
    records = [dict(zip(names, row)) for row in result.fetchall()]
    result = connection.execute('SELECT * FROM events')
    names = [d[0] for d in result.description]
    events = [dict(zip(names, row)) for row in result.fetchall()]
    if len({(e['source_id'], e['C_YEAR'], e['C_CASE']) for e in events}) != len(events):
        raise ValueError('Duplicate event keys')
    units, alternatives, unresolved, quality = resolve_person_records(records, events)
    write_records(connection, units, output / 'person_units.parquet')
    write_records(connection, alternatives, output / 'record_alternatives.parquet')
    write_records(connection, unresolved, output / 'unresolved_and_dummy_records.parquet')
    for name in ('person_units', 'record_alternatives', 'unresolved_and_dummy_records'):
        connection.execute(f'CREATE VIEW {name} AS SELECT * FROM read_parquet({quote(output/(name+".parquet"))})')
    columns = ['identified_person_keys', 'identified_deaths_min', 'identified_deaths_max', 'identified_injuries_min', 'identified_injuries_max', 'identified_casualties_min', 'identified_casualties_max', 'unresolved_identity_record_rows', 'unresolved_death_record_rows', 'unresolved_injury_record_rows', 'unknown_severity_identified_keys', 'unknown_severity_unresolved_rows', 'not_applicable_severity_identified_keys', 'not_applicable_severity_unresolved_rows']
    counts = defaultdict(Counter)
    for year in sorted({e['C_YEAR'] for e in events}):
        for subset in ('observed', 'strict'):
            for group in GROUPS:
                counts[(year, subset, group)] = Counter({c: 0 for c in columns})
    for u in units:
        for subset in ('observed', 'strict') if u['is_analysis_candidate'] else ('observed',):
            counter = counts[(u['C_YEAR'], subset, u['road_user_group'])]
            counter['identified_person_keys'] += 1
            counter['unknown_severity_identified_keys'] += int(u['unknown_severity'])
            counter['not_applicable_severity_identified_keys'] += int(u['not_applicable_severity'])
            for label in ('deaths', 'injuries', 'casualties'):
                for end in ('min', 'max'):
                    counter[f'identified_{label}_{end}'] += u[f'{label}_{end}']
    for row in unresolved:
        if row['identity_status'] == 'dummy':
            continue
        for subset in ('observed', 'strict') if row['is_analysis_candidate'] else ('observed',):
            counter = counts[(row['C_YEAR'], subset, row['road_user_group'])]
            m = row['record_multiplicity']
            counter['unresolved_identity_record_rows'] += m
            counter['unresolved_death_record_rows'] += m * (row['P_ISEV'] == '3')
            counter['unresolved_injury_record_rows'] += m * (row['P_ISEV'] == '2')
            counter['unknown_severity_unresolved_rows'] += m * (row['P_ISEV'] not in {'1', '2', '3', 'N'})
            counter['not_applicable_severity_unresolved_rows'] += m * (row['P_ISEV'] == 'N')
    grouped = []
    for (year, subset, group), counter in sorted(counts.items()):
        row = dict(year=year, subset=subset, road_user_group=group, **counter)
        for label, raw in [('deaths', 'death'), ('injuries', 'injury')]:
            row[f'{label}_record_scenario_low'] = row[f'identified_{label}_min']
            row[f'{label}_record_scenario_high'] = row[f'identified_{label}_max'] + row[f'unresolved_{raw}_record_rows']
        grouped.append(row)
    write_records(connection, grouped, output / 'annual_group_counts.parquet')
    export(connection, f"SELECT * FROM read_parquet({quote(output/'annual_group_counts.parquet')}) ORDER BY year,subset,road_user_group", output / 'annual_group_counts.csv')
    metrics = [n for n in grouped[0] if n not in {'year', 'subset', 'road_user_group'}]
    annual_query = f"SELECT year,subset,{','.join(f'sum({n})::BIGINT AS {n}' for n in metrics)} FROM read_parquet({quote(output/'annual_group_counts.parquet')}) GROUP BY year,subset ORDER BY year,subset"
    export(connection, annual_query, output / 'annual_counts.csv')
    export(connection, 'SELECT * FROM person_units WHERE person_attribute_conflict OR severity_conflict OR road_user_group_conflict ORDER BY C_YEAR,C_CASE,V_ID,P_ID', output / 'conflicting_person_keys.parquet')
    export(connection, "SELECT C_YEAR AS year,identity_status,P_ID,V_ID,P_ISEV,P_USER,V_TYPE,P_PSN,sum(record_multiplicity)::BIGINT AS record_rows FROM record_alternatives GROUP BY ALL ORDER BY ALL", output / 'code_profile.csv')
    export(connection, """SELECT C_YEAR AS year,count(*)::BIGINT AS identified_person_keys,
      sum(input_record_rows-record_variants)::BIGINT AS exact_repeats_on_identified_keys,
      sum(CAST(person_attribute_conflict AS INTEGER))::BIGINT AS person_attribute_conflicts,
      sum(CAST(severity_conflict AS INTEGER))::BIGINT AS severity_conflicts,
      sum(CAST(unknown_severity AS INTEGER))::BIGINT AS unknown_severity_keys,
      count(*) FILTER(WHERE road_user_group='ambiguous')::BIGINT AS ambiguous_group_keys
      FROM person_units GROUP BY C_YEAR ORDER BY C_YEAR""", output / 'quality_by_year.csv')
    export(connection, """SELECT C_YEAR AS year,P_PSN,P_ISEV,
      sum(record_multiplicity)::BIGINT AS raw_positive_record_rows,
      count(DISTINCT struct_pack(source_id:=source_id,C_YEAR:=C_YEAR,C_CASE:=C_CASE,V_ID:=V_ID,P_ID:=P_ID))
        FILTER(WHERE identity_status='identified')::BIGINT AS identified_keys_with_code
      FROM record_alternatives WHERE V_TYPE='08' AND P_ISEV IN ('2','3')
      GROUP BY ALL ORDER BY year,P_PSN,P_ISEV""", output / 'positive_tractor_position_profile.csv')
    benchmark = root / 'data/reference/tractor_occupant_benchmarks.csv'
    if benchmark.exists():
        export(connection, f"""WITH selected AS (
          SELECT b.*,a.subset,
            CASE WHEN b.measure='fatalities' THEN a.deaths_record_scenario_low ELSE a.injuries_record_scenario_low END AS classified_record_scenario_low,
            CASE WHEN b.measure='fatalities' THEN a.deaths_record_scenario_high ELSE a.injuries_record_scenario_high END AS classified_record_scenario_high
          FROM read_csv({quote(benchmark)},header=true) b
          JOIN read_csv({quote(output/'annual_group_counts.csv')},header=true) a USING(year)
          WHERE a.road_user_group='tractor_occupant'
        ) SELECT *,classified_record_scenario_low-count AS low_minus_published,
          classified_record_scenario_high-count AS high_minus_published,
          CASE WHEN classified_record_scenario_low=count AND classified_record_scenario_high=count THEN 'classified_scenario_exact_match'
            WHEN count BETWEEN classified_record_scenario_low AND classified_record_scenario_high THEN 'published_within_classified_scenario'
            ELSE 'unresolved_definition_assignment_or_vintage_difference' END AS comparison_status
          FROM selected ORDER BY source_id,year,measure,subset""", output / 'occupant_benchmark_comparison.csv')
    consistency = connection.execute("""SELECT count(*) FILTER(WHERE event_severity='2' AND deaths_max>0),
      count(*) FILTER(WHERE event_severity NOT IN ('1','2')) FROM person_units""").fetchone()
    fatal_missing = connection.execute("""SELECT count(*) FROM events e WHERE e.C_SEV='1' AND NOT EXISTS
      (SELECT 1 FROM record_alternatives r WHERE r.C_YEAR=e.C_YEAR AND r.C_CASE=e.C_CASE AND r.source_id=e.source_id AND r.P_ISEV='3' AND r.identity_status<>'dummy')""").fetchone()[0]
    event_rows_match = connection.execute("""SELECT count(*) FROM events e LEFT JOIN
      (SELECT source_id,cast(C_YEAR AS INTEGER) AS C_YEAR,C_CASE,count(*) n FROM records GROUP BY ALL) r
      USING(source_id,C_YEAR,C_CASE) WHERE coalesce(r.n,0)<>e.input_record_rows""").fetchone()[0]
    quality.update(tractor_events=len(events), event_rows_mismatch=event_rows_match,
                   injury_events_with_fatal_person_keys=consistency[0],
                   invalid_event_severity_person_keys=consistency[1], fatal_events_without_fatal_record=fatal_missing)
    # Synthetic identity is never used. Validate only documented invariants.
    assert event_rows_match == 0 and consistency == (0, 0) and fatal_missing == 0
    assert sum(u['input_record_rows'] for u in units) + sum(r['record_multiplicity'] for r in unresolved) == len(records)
    assert len(grouped) == len({e['C_YEAR'] for e in events}) * 2 * len(GROUPS)
    validation = dict(built_at_utc=datetime.now(timezone.utc).isoformat(), status='validated_source_record_scenarios_external_reconciliation_partial',
                      pipeline_sha256=sha256(Path(__file__)), event_dataset_sha256=sha256(event_path),
                      dictionary_sha256=sha256(root/'Collisions/data_dictionary.pdf'),
                      benchmark_reference_sha256=sha256(benchmark) if benchmark.exists() else None,
                      duckdb_version=duckdb.__version__,
                      quality=quality, year_coverage=sorted({u['C_YEAR'] for u in units}),
                      limitations=['Unknown or unavailable injury severity is not imputed.', 'Intervals describe record-resolution scenarios, not true population bounds.',
                                   'Known composite keys are assumed to identify one recorded person; source corruption can violate this assumption.',
                                   '2019 event benchmark difference remains unresolved; 2022–2025 absent.',
                                   'Group ambiguity stays in a separate partition; category-specific certainty is incomplete.'])
    (output/'validation.json').write_text(json.dumps(validation, indent=2)+'\n')
    (output/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    connection.close()
    stage.unlink()
    print(json.dumps(validation, indent=2), flush=True)
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    build_dataset(args.root, json.loads((args.root/'data/sources.json').read_text()), args.root/'data/derived/casualties')


if __name__ == '__main__':
    main()
