"""Audit the alternate 2019 workbook without modifying selected production sources.

Run: PYTHONPATH=src .venv/bin/python -m truck_collisions.validate_source_revision
Cross-release comparisons aggregate independently; case IDs are never joined.
"""
import csv
import json
from pathlib import Path
import tempfile

import duckdb

from .build import COLUMNS, TWO_DIGIT, build_dataset, prepare_csv, quote, sha256
from .build_casualties import GROUPS, build_dataset as build_casualties, resolve_person_records, write_records


CANDIDATE = {
    'id': 'ncdb_2019_official_xlsx',
    'path': 'data/raw/ncdb/y_2019_en.xlsx', 'sheet': 'in',
    'first_year': 2019, 'last_year': 2019,
    'sha256': '8285d8d734a1835ccd4bc72617ee11419d6e16c3dcd6effb8b5bdbe51fc43d0b',
    'url': 'https://open.canada.ca/data/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a/resource/91d586f9-fb72-4eac-b1f5-d9b95830c877/download/y_2019_en.xlsx',
    'resource_id': '91d586f9-fb72-4eac-b1f5-d9b95830c877',
    'metadata_created': '2023-06-06T13:21:13.546751',
    'metadata_last_modified': '2023-06-06T13:15:16.364357',
    'metadata_modified': '2025-01-17T22:20:27.173889',
    'provenance': 'Alternate official workbook candidate; release identity is distinct from CSV. Resource metadata must be retained separately.',
}


def read_rows(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def audit(root):
    output = root / 'data/derived/candidates/2019_xlsx'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'candidate_source.json').write_text(json.dumps(CANDIDATE, indent=2) + '\n')
    collision = build_dataset(root, [CANDIDATE], output / 'collisions')
    build_casualties(root, [CANDIDATE], output / 'casualties', event_path=output / 'collisions/road_tractor_collisions.parquet')
    connection = duckdb.connect()
    result = connection.execute(f'SELECT * FROM read_parquet({quote(output / "collisions/road_tractor_collisions.parquet")})')
    names = [d[0] for d in result.description]
    events = [dict(zip(names, r)) for r in result.fetchall()]
    event_keys = {str(e['C_CASE']) for e in events}
    records = []
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        path, header = prepare_csv(root / CANDIDATE['path'], CANDIDATE, Path(temporary))
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                row = dict(zip(COLUMNS, (raw[h].strip() for h in header)))
                for field in TWO_DIGIT:
                    if row[field].isdigit() and len(row[field]) == 1:
                        row[field] = '0' + row[field]
                if row['C_CASE'] in event_keys:
                    records.append(dict(row, source_id=CANDIDATE['id']))
    units, alternatives, unresolved, quality = resolve_person_records(records, events)
    for name, rows in [('person_units', units), ('record_alternatives', alternatives), ('unresolved_and_dummy_records', unresolved)]:
        write_records(connection, rows, output / (name + '.parquet'))
    event_map = {str(e['C_CASE']): e for e in events}
    quality['injury_events_with_fatal_records'] = len({r['C_CASE'] for r in alternatives if r['P_ISEV'] == '3' and event_map[r['C_CASE']]['C_SEV'] == '2'})
    quality['fatal_events_without_fatal_record'] = len({e['C_CASE'] for e in events if e['C_SEV'] == '1'} - {r['C_CASE'] for r in alternatives if r['P_ISEV'] == '3' and r['identity_status'] != 'dummy'})
    quality['raw_row_accounting_exact'] = sum(u['input_record_rows'] for u in units) + sum(r['record_multiplicity'] for r in unresolved) == len(records)
    assert quality['raw_row_accounting_exact']
    assert quality['injury_events_with_fatal_records'] == quality['fatal_events_without_fatal_record'] == 0
    grouped = []
    for subset in ['observed', 'strict']:
        for group in GROUPS:
            selected = [u for u in units if u['road_user_group'] == group and (subset == 'observed' or u['is_analysis_candidate'])]
            extra = [r for r in unresolved if r['identity_status'] == 'unresolved_identity' and r['road_user_group'] == group and (subset == 'observed' or r['is_analysis_candidate'])]
            row = dict(year=2019, subset=subset, road_user_group=group, identified_person_keys=len(selected))
            for label, code in [('deaths', '3'), ('injuries', '2')]:
                row[label + '_record_scenario_low'] = sum(u[label + '_min'] for u in selected)
                row[label + '_record_scenario_high'] = sum(u[label + '_max'] for u in selected) + sum(r['record_multiplicity'] for r in extra if r['P_ISEV'] == code)
            row['unknown_severity_identified_keys'] = sum(u['unknown_severity'] for u in selected)
            row['unknown_severity_unresolved_rows'] = sum(r['record_multiplicity'] for r in extra if r['P_ISEV'] not in {'1','2','3','N'})
            grouped.append(row)
    write_records(connection, grouped, output / 'annual_group_counts.parquet')
    with (output / 'annual_group_counts.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(grouped[0]))
        writer.writeheader()
        writer.writerows(grouped)
    # Check separate Python normalization/selection against the complete builder.
    full_groups = read_rows(output / 'casualties/annual_group_counts.csv')
    for row in grouped:
        full = next(r for r in full_groups if (r['subset'], r['road_user_group']) == (row['subset'], row['road_user_group']))
        assert all(int(full[name]) == value for name, value in row.items() if name not in {'subset', 'road_user_group'})
    baseline = [r for r in read_rows(root / 'data/derived/baselines/pre_source_revision_20261015/data/derived/casualties/annual_group_counts.csv') if r['year'] == '2019']
    comparison = []
    for candidate in grouped:
        old = next(r for r in baseline if (r['subset'], r['road_user_group']) == (candidate['subset'], candidate['road_user_group']))
        for measure in ['identified_person_keys', 'deaths_record_scenario_low', 'deaths_record_scenario_high', 'injuries_record_scenario_low', 'injuries_record_scenario_high', 'unknown_severity_identified_keys', 'unknown_severity_unresolved_rows']:
            comparison.append(dict(subset=candidate['subset'], road_user_group=candidate['road_user_group'], measure=measure, baseline_csv=int(old[measure]), candidate_xlsx=candidate[measure], difference=candidate[measure] - int(old[measure])))
    with (output / 'baseline_group_comparison.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparison[0]))
        writer.writeheader()
        writer.writerows(comparison)
    benchmark = []
    for reference in read_rows(root / 'data/reference/tractor_occupant_benchmarks.csv'):
        if reference['year'] != '2019':
            continue
        label = 'deaths' if reference['measure'] == 'fatalities' else 'injuries'
        for row in grouped:
            if row['road_user_group'] != 'tractor_occupant':
                continue
            low, high = row[label + '_record_scenario_low'], row[label + '_record_scenario_high']
            benchmark.append(dict(reference, subset=row['subset'], candidate_low=low, candidate_high=high, low_minus_published=low-int(reference['count']), high_minus_published=high-int(reference['count'])))
    with (output / 'occupant_benchmark_comparison.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(benchmark[0]))
        writer.writeheader()
        writer.writerows(benchmark)
    summary = dict(candidate=CANDIDATE, collision_validation=collision, casualty_quality=quality,
                   observed_totals={name: sum(r[name] for r in grouped if r['subset'] == 'observed') for name in grouped[0] if name not in {'year', 'subset', 'road_user_group'}},
                   pipeline_sha256=sha256(Path(__file__)), comparison_rule='Aggregate independently by release. No case-ID joins across releases.',
                   limitation='Source-record resolution scenarios are conditional, not true population bounds. Benchmark equality is not proof of source authority.')
    (output / 'validation.json').write_text(json.dumps(summary, indent=2) + '\n')
    connection.close()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    audit(Path.cwd())
