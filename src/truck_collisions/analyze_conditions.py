"""Descriptive event-condition distributions; no exposure or causal estimates.

Run: PYTHONPATH=src .venv/bin/python -m truck_collisions.analyze_conditions
"""
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import duckdb

from .audit_conditions import classify, write_csv
from .build import quote, sha256

FIELDS = ('C_WTHR', 'C_RSUR', 'C_CONF', 'C_RCFG', 'C_HOUR', 'C_MNTH',
          'C_WDAY', 'C_RALN', 'C_TRAF')
PERIODS = {
    'primary_2012_2021': tuple(range(2012, 2022)),
    'early_2012_2016': tuple(range(2012, 2017)),
    'late_2017_2021': tuple(range(2017, 2022)),
    'pre2020_2012_2019': tuple(range(2012, 2020)),
    'omit2019_2012_2021': tuple(y for y in range(2012, 2022) if y != 2019),
    'target_available_2016_2021': tuple(range(2016, 2022)),
}
COHORTS = ('tractor', 'no_recorded_tractor')
SUBSETS = ('observed', 'strict')
SEVERITIES = ('all', 'fatal', 'injury')
NAMED = {'defined', 'top_coded'}
PAIRS = {'weather_surface': ('C_WTHR', 'C_RSUR'),
         'configuration_hour_band': ('C_CONF', 'HOUR_BAND')}


def hour_band(code):
    """Six-hour clock intervals only; no assumption about measured lighting."""
    if code is not None and code in {f'{h:02}' for h in range(24)}:
        start = 6 * (int(code) // 6)
        return f'{start:02}–{start+5:02}'
    return code


def percentage(numerator, denominator):
    return 100 * numerator / denominator if denominator else None


def category(code, spec, conflict=False):
    status = classify(code, spec, conflict)
    value = '<NULL>' if code is None else code
    labels = {'other': 'Residual other', 'unknown': 'Unknown',
              'not_provided': 'Not provided', 'not_applicable': 'Not applicable',
              'conflict_null': 'Conflicting source values', 'null_or_blank': 'Null/blank',
              'unexpected': 'Unexpected code'}
    return value, status, spec['defined_codes'].get(code, labels.get(status, str(code)))


def domain(spec):
    codes = set(spec['defined_codes'])
    for status in ('top_coded', 'other', 'unknown', 'not_provided', 'not_applicable'):
        codes.update(spec[status + '_codes'])
    return {category(code, spec) for code in codes}


def partitions(tractor, candidate, severity):
    for subset in SUBSETS if candidate else ('observed',):
        for level in ('all', 'fatal' if severity == '1' else 'injury'):
            yield 'tractor' if tractor else 'no_recorded_tractor', subset, level


def distribute(counts, categories):
    """Exhaust the event denominator; named-only shares exclude residual/unknown."""
    total = sum(counts.values())
    named = sum(n for key, n in counts.items() if key[1] in NAMED)
    return [dict(code=key[0], status=key[1], label=key[2], code_events=counts[key],
                 events=total, named_events=named, share_pct=percentage(counts[key], total),
                 named_share_pct=percentage(counts[key], named) if key[1] in NAMED else None)
            for key in sorted(categories)]


def analyze(root):
    root = Path(root)
    data = root/'data/derived/ncdb'
    output = root/'reports/conditions'
    output.mkdir(parents=True, exist_ok=True)
    book_path = root/'data/reference/collision_codebook.json'
    book = json.loads(book_path.read_text())
    assert sha256(root/book['source']['path']) == book['source']['sha256']
    specs = {field: book['fields'][field] for field in FIELDS}
    specs['HOUR_BAND'] = {**specs['C_HOUR'], 'label': 'Six-hour clock band',
        'defined_codes': {f'{h:02}–{h+5:02}': f'{h:02}:00–{h+5:02}:59' for h in (0, 6, 12, 18)}}
    connection = duckdb.connect()
    connection.execute("SET memory_limit='1GB'")
    connection.execute('SET threads=2')
    connection.execute(f'CREATE VIEW events AS SELECT * FROM read_parquet({quote(data/"collisions.parquet")}) WHERE C_YEAR BETWEEN 2012 AND 2021')
    connection.execute(f'CREATE VIEW conflicts AS SELECT * FROM read_parquet({quote(data/"collision_attribute_conflicts.parquet")})')
    assert connection.execute("SELECT count(*) FROM events WHERE C_SEV NOT IN ('1','2') OR C_SEV IS NULL").fetchone()[0] == 0
    assert connection.execute('SELECT count(*)-count(DISTINCT(source_id,C_YEAR,C_CASE)) FROM events').fetchone()[0] == 0
    values = ','.join(f'({quote(field)},e.{field})' for field in FIELDS)
    raw = connection.execute(f'''SELECT e.C_YEAR,e.source_id,e.is_road_tractor,
        e.is_analysis_candidate,e.C_SEV,v.field,v.code,c.field IS NOT NULL AS conflict,count(*)
        FROM events e CROSS JOIN LATERAL (VALUES {values}) v(field,code)
        LEFT JOIN conflicts c ON e.source_id=c.source_id AND e.C_YEAR=try_cast(c.C_YEAR AS INTEGER)
          AND e.C_CASE=c.C_CASE AND v.field=c.field GROUP BY ALL''').fetchall()
    annual = defaultdict(Counter)
    categories = {field: domain(spec) for field, spec in specs.items()}
    sources = defaultdict(set)
    for year, source, tractor, candidate, severity, field, code, conflict, count in raw:
        sources[year].add(source)
        selected = [(field, code)]
        if field == 'C_HOUR':
            selected.append(('HOUR_BAND', hour_band(code)))
        for field, value in selected:
            key = category(value, specs[field], conflict)
            categories[field].add(key)
            for partition in partitions(tractor, candidate, severity):
                annual[(year, *partition, field)][key] += count
    annual_rows = []
    for year, cohort, subset, severity, field in product(range(2012, 2022), COHORTS, SUBSETS, SEVERITIES, specs):
        base = dict(year=year, source_ids='|'.join(sorted(sources[year])), cohort=cohort,
                    subset=subset, severity=severity, field=field)
        annual_rows.extend({**base, **row} for row in distribute(annual[(year,cohort,subset,severity,field)], categories[field]))
    write_csv(output/'annual_distributions.csv', annual_rows)
    # Direct-event counts must reproduce every nonzero audited code partition.
    with (root/'reports/conditions_quality/annual_code_counts.csv').open() as handle:
        audited = [r for r in csv.DictReader(handle) if 2012 <= int(r['year']) <= 2021
                   and r['cohort'] in COHORTS and r['field'] in FIELDS]
    direct = {(r['year'],r['cohort'],r['subset'],r['severity'],r['field'],r['code'],r['status']): r['code_events']
              for r in annual_rows if r['field'] in FIELDS and r['code_events']}
    expected = {(int(r['year']),r['cohort'],r['subset'],r['severity'],r['field'],r['code'],r['status']): int(r['code_events']) for r in audited}
    assert direct == expected, 'Quality audit differs from current events; rerun audit and investigate.'
    pooled, period_rows = {}, []
    for period, years in PERIODS.items():
        for cohort, subset, severity, field in product(COHORTS, SUBSETS, SEVERITIES, specs):
            counts = Counter()
            for year in years:
                counts.update(annual[(year,cohort,subset,severity,field)])
            pooled[(period,cohort,subset,severity,field)] = counts
            base = dict(period=period, years='|'.join(map(str, years)), cohort=cohort,
                        subset=subset, severity=severity, field=field)
            period_rows.extend({**base, **row} for row in distribute(counts,categories[field]))
    write_csv(output/'period_distributions.csv', period_rows)
    index = {(r['period'],r['cohort'],r['subset'],r['severity'],r['field'],r['code'],r['status']): r for r in period_rows}
    comparisons, changes, fatal_shares = [], [], []
    for row in period_rows:
        period,cohort,subset,severity,field,code,status = (row[k] for k in ('period','cohort','subset','severity','field','code','status'))
        base = {k: row[k] for k in ('period','subset','severity','field','code','status','label')}
        if cohort == 'tractor':
            comparator = index[(period,'no_recorded_tractor',subset,severity,field,code,status)]
            comparisons.append({**base, 'tractor_code_events': row['code_events'],
                'tractor_events': row['events'], 'comparator_code_events': comparator['code_events'],
                'comparator_events': comparator['events'], 'tractor_share_pct': row['share_pct'],
                'comparator_share_pct': comparator['share_pct'],
                'share_gap_pp': row['share_pct']-comparator['share_pct'],
                'tractor_named_share_pct': row['named_share_pct'],
                'comparator_named_share_pct': comparator['named_share_pct'],
                'named_share_gap_pp': row['named_share_pct']-comparator['named_share_pct']
                    if row['named_share_pct'] is not None and comparator['named_share_pct'] is not None else None})
        if period == 'late_2017_2021':
            early = index[('early_2012_2016',cohort,subset,severity,field,code,status)]
            changes.append({**base, 'cohort': cohort, 'early_code_events': early['code_events'],
                'early_events': early['events'], 'late_code_events': row['code_events'],
                'late_events': row['events'], 'early_share_pct': early['share_pct'],
                'late_share_pct': row['share_pct'], 'share_change_pp': row['share_pct']-early['share_pct'],
                'early_named_share_pct': early['named_share_pct'], 'late_named_share_pct': row['named_share_pct'],
                'named_share_change_pp': row['named_share_pct']-early['named_share_pct']
                    if row['named_share_pct'] is not None and early['named_share_pct'] is not None else None})
        if severity == 'all':
            fatal = index[(period,cohort,subset,'fatal',field,code,status)]['code_events']
            injury = index[(period,cohort,subset,'injury',field,code,status)]['code_events']
            assert fatal+injury == row['code_events']
            fatal_shares.append({**base, 'cohort': cohort, 'fatal_events': fatal,
                'injury_events': injury, 'category_events': fatal+injury,
                'fatal_share_pct': percentage(fatal,fatal+injury)})
    write_csv(output/'cohort_comparisons.csv', comparisons)
    write_csv(output/'period_changes.csv', changes)
    write_csv(output/'category_fatal_shares.csv', fatal_shares)
    # Two small joint tables preserve every collision, including unknown and other.
    joint_rows, joint_annual_rows = [], []
    for pair, (left,right) in PAIRS.items():
        sql_right = 'C_HOUR' if right == 'HOUR_BAND' else right
        raw_joint = connection.execute(f'''SELECT e.C_YEAR,e.is_road_tractor,e.is_analysis_candidate,e.C_SEV,
            e.{left},e.{sql_right},c1.field IS NOT NULL,c2.field IS NOT NULL,count(*)
            FROM events e LEFT JOIN conflicts c1 ON e.source_id=c1.source_id
              AND e.C_YEAR=try_cast(c1.C_YEAR AS INTEGER) AND e.C_CASE=c1.C_CASE AND c1.field={quote(left)}
            LEFT JOIN conflicts c2 ON e.source_id=c2.source_id AND e.C_YEAR=try_cast(c2.C_YEAR AS INTEGER)
              AND e.C_CASE=c2.C_CASE AND c2.field={quote(sql_right)} GROUP BY ALL''').fetchall()
        joint = defaultdict(Counter)
        for year,tractor,candidate,severity,left_code,right_code,left_conflict,right_conflict,count in raw_joint:
            if right == 'HOUR_BAND':
                right_code = hour_band(right_code)
            left_key = category(left_code,specs[left],left_conflict)
            right_key = category(right_code,specs[right],right_conflict)
            for partition in partitions(tractor,candidate,severity):
                joint[(year,*partition)][(left_key,right_key)] += count
        for period, years in [*(('annual_'+str(y), (y,)) for y in range(2012,2022)), *PERIODS.items()]:
            for cohort,subset,severity in product(COHORTS,SUBSETS,SEVERITIES):
                counts = Counter()
                for year in years:
                    counts.update(joint[(year,cohort,subset,severity)])
                total = sum(counts.values())
                named = sum(n for (l,r),n in counts.items() if l[1] in NAMED and r[1] in NAMED)
                for l,r in product(sorted(categories[left]),sorted(categories[right])):
                    count = counts[(l,r)]
                    row = dict(period=period,cohort=cohort,subset=subset,severity=severity,pair=pair,
                        left_field=left,left_code=l[0],left_status=l[1],left_label=l[2],
                        right_field=right,right_code=r[0],right_status=r[1],right_label=r[2],
                        cell_events=count,events=total,named_events=named,share_pct=percentage(count,total),
                        named_share_pct=percentage(count,named) if l[1] in NAMED and r[1] in NAMED else None)
                    (joint_annual_rows if period.startswith('annual_') else joint_rows).append(row)
                assert total == sum(annual[(y,cohort,subset,severity,left)].total() for y in years)
    write_csv(output/'joint_distributions.csv', joint_rows)
    write_csv(output/'joint_annual_distributions.csv', joint_annual_rows)
    # Independent arithmetic identities are gates, not post-hoc adjustments.
    partitions_totals = defaultdict(set)
    for row in annual_rows:
        partitions_totals[(row['year'],row['cohort'],row['subset'],row['severity'])].add(row['events'])
    assert all(len(totals)==1 for totals in partitions_totals.values())
    assert all(row['named_events'] <= row['events'] for row in annual_rows)
    summary = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        scope='2012–2021 unique casualty-collision event descriptions; no exposure-adjusted or causal estimates',
        periods={name:list(years) for name,years in PERIODS.items()}, fields=specs,
        primary_cohort_definition='At least one recorded V_TYPE08 road tractor, with or without semitrailer',
        comparator_definition='No recorded V_TYPE08; includes other truck classes and uncertain vehicle types; not car-only',
        denominators={'share_pct':'All events in the cohort/subset/severity/period, retaining unknown and residual other',
            'named_share_pct':'Only defined/top-coded categories of this field (both fields in joint tables); excludes residual other and unavailable values',
            'fatal_share_pct':'Fatal events divided by fatal plus injury events WITHIN the recorded category; not people, death probability or exposure risk'},
        checks=dict(unique_event_keys=True,severity_domain=True,quality_audit_reproduced=True,
            full_code_domains_zero_filled=True,equal_field_denominators=True,fatal_injury_partition=True,
            joint_denominator_equality=True),
        rows={name:len(rows) for name,rows in [('annual_distributions',annual_rows),('period_distributions',period_rows),
            ('cohort_comparisons',comparisons),('period_changes',changes),('category_fatal_shares',fatal_shares),
            ('joint_distributions',joint_rows),('joint_annual_distributions',joint_annual_rows)]},
        input_sha256={str(p.relative_to(root)):sha256(p) for p in (data/'collisions.parquet',
            data/'collision_attribute_conflicts.parquet',data/'source_manifest.json',data/'validation.json',book_path,
            root/book['source']['path'],root/'reports/conditions_quality/annual_code_counts.csv')},
        code_sha256=sha256(Path(__file__)),
        limitations=['No collision-free vehicle travel or weather/time exposure denominators: shares are collision composition.',
            'Fatal events count once regardless of number of deaths; no person casualty outcomes are calculated here.',
            'Strict is a source-quality sensitivity, not a corrected population.',
            'Equal five-year pooled periods are event-weighted, not averages of annual percentages.',
            'Pandemic, source revisions, reporting practice, geography and traffic mix can affect descriptive patterns.',
            'Clock hour is not darkness; configuration is not manoeuvre or fault.',
            'Rare category fatal shares are unstable; report numerator and denominator without ranking small cells.',
            'No 2022–2025 national events are imputed; the intended recent decade remains incomplete.'])
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    connection.close()
    print(json.dumps(summary['rows'],indent=2))
    return summary


if __name__ == '__main__':
    analyze(Path.cwd())
