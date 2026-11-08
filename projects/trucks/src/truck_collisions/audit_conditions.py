"""Profile collision-field missingness and codes before condition comparisons.

Run: PYTHONPATH=src .venv/bin/python -m truck_collisions.audit_conditions
Reads rebuilt events; never rewrites source or production datasets.
"""
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from .build import quote, sha256

STATUSES = ('defined', 'top_coded', 'other', 'unknown', 'not_provided',
            'not_applicable', 'null_or_blank', 'conflict_null', 'unexpected')
BUNDLES = {
    'weather_surface': ('C_WTHR', 'C_RSUR'),
    'configuration_road': ('C_CONF', 'C_RCFG'),
    'core_conditions_time': ('C_WTHR', 'C_RSUR', 'C_CONF', 'C_RCFG', 'C_HOUR'),
    'all_planned_conditions': ('C_WTHR', 'C_RSUR', 'C_CONF', 'C_RCFG', 'C_HOUR',
                               'C_MNTH', 'C_WDAY', 'C_RALN', 'C_TRAF'),
}


def classify(code, spec, conflict=False):
    if code is None or not str(code).strip():
        return 'conflict_null' if conflict else 'null_or_blank'
    for status in ('top_coded', 'other', 'unknown', 'not_provided', 'not_applicable'):
        if code in spec[status + '_codes']:
            return status
    return 'defined' if code in spec['defined_codes'] else 'unexpected'


def variation(before, after):
    """Total variation of complete code distributions, including special codes."""
    left, right = sum(before.values()), sum(after.values())
    return .5 * sum(abs(before.get(k, 0)/left-after.get(k, 0)/right)
                    for k in before.keys() | after.keys())


def write_csv(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def partitions(year, source, tractor, candidate, severity):
    for cohort in ('all_events', 'tractor' if tractor else 'no_recorded_tractor'):
        for subset in ('observed', 'strict') if candidate else ('observed',):
            for level in ('all', 'fatal' if severity == '1' else 'injury'):
                yield year, source, cohort, subset, level


def audit(root):
    root = Path(root)
    data = root / 'data/derived/ncdb'
    output = root / 'reports/conditions_quality'
    output.mkdir(parents=True, exist_ok=True)
    book_path = root / 'data/reference/collision_codebook.json'
    book = json.loads(book_path.read_text())
    assert sha256(root/book['source']['path']) == book['source']['sha256']
    fields = book['fields']
    connection = duckdb.connect()
    connection.execute("SET memory_limit='1GB'")
    connection.execute('SET threads=2')
    connection.execute(f'CREATE VIEW events AS SELECT * FROM read_parquet({quote(data/"collisions.parquet")})')
    connection.execute(f'CREATE VIEW conflicts AS SELECT * FROM read_parquet({quote(data/"collision_attribute_conflicts.parquet")})')
    assert connection.execute("SELECT count(*) FROM events WHERE C_SEV NOT IN ('1','2') OR C_SEV IS NULL").fetchone()[0] == 0
    assert connection.execute('SELECT count(*)-count(DISTINCT (source_id,C_YEAR,C_CASE)) FROM events').fetchone()[0] == 0
    values = ','.join(f'({quote(f)}, e.{f})' for f in fields)
    raw = connection.execute(f'''SELECT e.C_YEAR,e.source_id,e.is_road_tractor,
      e.is_analysis_candidate,e.C_SEV,v.field,v.code,c.field IS NOT NULL AS conflict,count(*)
      FROM events e CROSS JOIN LATERAL (VALUES {values}) v(field,code)
      LEFT JOIN conflicts c ON e.source_id=c.source_id AND e.C_YEAR=try_cast(c.C_YEAR AS INTEGER)
        AND e.C_CASE=c.C_CASE AND v.field=c.field GROUP BY ALL''').fetchall()
    codes = defaultdict(Counter)
    for year, source, tractor, candidate, severity, field, code, conflict, count in raw:
        status = classify(code, fields[field], conflict)
        for key in partitions(year, source, tractor, candidate, severity):
            codes[(*key, field)][(code if code is not None else '<NULL>', status)] += count
    profiles, code_rows = [], []
    names = ('year', 'source_id', 'cohort', 'subset', 'severity', 'field')
    for key, counts in sorted(codes.items()):
        base = dict(zip(names, key)); total = sum(counts.values())
        row = {**base, 'events': total}
        for status in STATUSES:
            row[status+'_events'] = sum(n for (_, s), n in counts.items() if s == status)
            row[status+'_pct'] = 100*row[status+'_events']/total
        row['unavailable_events'] = sum(row[s+'_events'] for s in
            ('unknown', 'not_provided', 'not_applicable', 'null_or_blank', 'conflict_null', 'unexpected'))
        row['unavailable_pct'] = 100*row['unavailable_events']/total
        row['named_events'] = row['defined_events'] + row['top_coded_events']
        row['named_pct'] = 100*row['named_events']/total
        assert sum(row[s+'_events'] for s in STATUSES) == total
        profiles.append(row)
        for (code, status), count in sorted(counts.items()):
            code_rows.append({**base, 'code': code, 'status': status, 'code_events': count,
                              'events': total, 'pct': 100*count/total})
    # Every field must have exactly the same event denominator in a partition.
    denominators = defaultdict(set)
    for row in profiles:
        denominators[tuple(row[k] for k in names[:-1])].add(row['events'])
    assert all(len(values) == 1 for values in denominators.values())
    write_csv(output/'annual_field_quality.csv', profiles)
    write_csv(output/'annual_code_counts.csv', code_rows)
    spans = defaultdict(list)
    for row in code_rows:
        if row['subset'] == 'observed' and row['severity'] == 'all':
            spans[(row['cohort'], row['field'], row['code'], row['status'])].append(row)
    write_csv(output/'code_presence.csv', [dict(cohort=key[0], field=key[1], code=key[2],
        status=key[3], first_observed_year=min(r['year'] for r in rows),
        last_observed_year=max(r['year'] for r in rows), years_observed=len(rows),
        total_code_events=sum(r['code_events'] for r in rows))
        for key, rows in sorted(spans.items())])
    joint = defaultdict(Counter)
    for bundle, selected in BUNDLES.items():
        def condition(other):
            terms = []
            for field in selected:
                valid = list(fields[field]['defined_codes']) + (fields[field]['other_codes'] if other else [])
                terms.append(f"coalesce({field} IN ({','.join(quote(v) for v in valid)}),false)")
            return ' AND '.join(terms)
        rows = connection.execute(f'''SELECT C_YEAR,source_id,is_road_tractor,is_analysis_candidate,C_SEV,
          count(*),count(*) FILTER(WHERE {condition(False)}),count(*) FILTER(WHERE {condition(True)})
          FROM events GROUP BY ALL''').fetchall()
        for year, source, tractor, candidate, severity, count, named, available in rows:
            for key in partitions(year, source, tractor, candidate, severity):
                joint[(*key, bundle)].update(events=count, named_complete_events=named,
                                            available_including_other_events=available)
    joint_rows = []
    for key, values in sorted(joint.items()):
        row = dict(zip((*names[:-1], 'bundle'), key), **values)
        assert 0 <= row['named_complete_events'] <= row['available_including_other_events'] <= row['events']
        for metric in ('named_complete', 'available_including_other'):
            row[metric+'_pct'] = 100*row[metric+'_events']/row['events']
        row['fields'] = '|'.join(BUNDLES[key[-1]])
        joint_rows.append(row)
    write_csv(output/'joint_field_coverage.csv', joint_rows)
    index = {(r['year'], r['cohort'], r['subset'], r['severity'], r['field']): r for r in profiles}
    differences, shifts = [], []
    for row in profiles:
        if row['subset'] != 'observed' or row['severity'] != 'all':
            continue
        year, cohort, field = row['year'], row['cohort'], row['field']
        if cohort == 'tractor':
            other = index[(year, 'no_recorded_tractor', 'observed', 'all', field)]
            differences.append(dict(year=year, field=field, tractor_events=row['events'],
                comparator_events=other['events'], tractor_unavailable_pct=row['unavailable_pct'],
                comparator_unavailable_pct=other['unavailable_pct'],
                unavailable_gap_pp=row['unavailable_pct']-other['unavailable_pct'],
                tractor_other_pct=row['other_pct'], comparator_other_pct=other['other_pct']))
        previous = index.get((year-1, cohort, 'observed', 'all', field))
        if previous:
            before = codes[(year-1, previous['source_id'], cohort, 'observed', 'all', field)]
            after = codes[(year, row['source_id'], cohort, 'observed', 'all', field)]
            tv = variation(before, after)
            gap = row['unavailable_pct']-previous['unavailable_pct']
            shifts.append(dict(year=year, cohort=cohort, field=field,
                unavailable_change_pp=gap, other_change_pp=row['other_pct']-previous['other_pct'],
                total_variation=tv, source_id_changed=row['source_id']!=previous['source_id'],
                review_flag=abs(gap)>=2 or tv>=.15))
    write_csv(output/'cohort_quality_gaps.csv', differences)
    write_csv(output/'annual_distribution_changes.csv', shifts)
    unexpected = [r for r in code_rows if r['cohort']=='all_events' and r['subset']=='observed'
                  and r['severity']=='all' and r['status']=='unexpected']
    summary = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        scope='Collision-level dictionary/availability audit, 1999–2021; no imputation or outcome associations',
        checks=dict(unique_source_event_keys=True, severity_domain=True,
            status_partition=True, equal_field_denominators=True, joint_coverage_ordering=True),
        annual_field_rows=len(profiles), joint_coverage_rows=len(joint_rows), unexpected_codes=unexpected,
        flagged_tractor_transitions=[r for r in shifts if r['cohort']=='tractor' and r['review_flag']],
        input_sha256={str(p.relative_to(root)): sha256(p) for p in
            (data/'collisions.parquet', data/'collision_attribute_conflicts.parquet',
             data/'source_manifest.json', data/'validation.json', book_path, root/book['source']['path'])},
        code_sha256=sha256(Path(__file__)), thresholds={'availability_change_pp': 2, 'total_variation': .15},
        limitations=['Frequency shifts do not prove a coding change or its cause.',
            'One supplied dictionary cannot establish identical jurisdiction/year coding practice.',
            'No jurisdiction, measured lighting, vehicle manoeuvre or fault fields in the public schema.',
            'No-recorded-tractor comparison is not car-only and may contain unknown vehicle types.',
            'Other is a valid residual category, not unknown; complete-case restriction can select events.',
            'All counts are events; no person outcome records are multiplied into these denominators.'])
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    make_figure(output, profiles, fields)
    connection.close()
    print(json.dumps({k: summary[k] for k in ('annual_field_rows', 'joint_coverage_rows', 'unexpected_codes', 'flagged_tractor_transitions')}, indent=2))
    return summary


def make_figure(output, profiles, fields):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    selected = list(BUNDLES['all_planned_conditions'])
    years = sorted({r['year'] for r in profiles})
    index = {(r['year'], r['field']): r for r in profiles
             if r['cohort']=='tractor' and r['subset']=='observed' and r['severity']=='all'}
    fig, axes = plt.subplots(2, 1, figsize=(13, 8.3))
    fig.suptitle('Field availability in reported tractor-involved casualty collisions', fontsize=15, y=.98)
    for ax, metric, title in zip(axes, ('unavailable_pct', 'other_pct'),
        ('Unknown, unavailable or invalid (%)', 'Valid residual Q/QQ “other” category (%)')):
        matrix = np.array([[index[(y, f)][metric] for y in years] for f in selected])
        im = ax.imshow(matrix, aspect='auto', vmin=0, vmax=max(10, math.ceil(matrix.max())), cmap='YlOrRd')
        ax.set_title(title, fontsize=12)
        ax.set_yticks(range(len(selected)), [fields[f]['label'] for f in selected], fontsize=9)
        ax.set_xticks(range(len(years)), years, rotation=45, ha='right', fontsize=8)
        fig.colorbar(im, ax=ax, label='Share of events (%)', fraction=.025, pad=.02)
    fig.text(.07, .025, '1999–2021 observed events; no imputation. Residual Q/QQ is separate from missing information and named dictionary codes.\nFrequency/availability changes can reflect reporting, source revisions or collision mix; they do not establish causes.', fontsize=9)
    fig.subplots_adjust(left=.19, right=.93, bottom=.15, top=.88, hspace=.55)
    for ext in ('png', 'svg'):
        fig.savefig(output/f'field_availability.{ext}', dpi=180, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    audit(Path.cwd())
