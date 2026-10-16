"""Accounting decomposition of fatal-event shares, not causal attribution."""
import json
from collections import defaultdict
from pathlib import Path

import duckdb

from .analyze_conditions import category, domain
from .audit_conditions import write_csv
from .build import quote, sha256

SCENARIOS = {
    'primary': (tuple(range(2012, 2017)), tuple(range(2017, 2022))),
    'endpoints': ((2012,), (2021,)),
    'target_available': ((2016,), (2021,)),
    'pre2020': (tuple(range(2012, 2017)), (2017, 2018, 2019)),
    'late_without_2019': (tuple(range(2012, 2017)), (2017, 2018, 2020, 2021)),
}


def components(a, b):
    """Counts are code -> (events, fatal). Undefined rates stay undefined.

    A category present in only one period has an identified total contribution,
    but no uniquely identified mix/within split. Export that as unallocated.
    """
    na, nb = sum(n for n, _ in a.values()), sum(n for n, _ in b.values())
    if not na or not nb:
        raise ValueError('Both periods require events')
    rows = []
    for code in sorted(a.keys() | b.keys()):
        n0, f0 = a.get(code, (0, 0))
        n1, f1 = b.get(code, (0, 0))
        if not (0 <= f0 <= n0 and 0 <= f1 <= n1):
            raise ValueError('Fatal counts must be between zero and event counts')
        w0, w1 = n0 / na, n1 / nb
        r0, r1 = f0 / n0 if n0 else None, f1 / n1 if n1 else None
        net = 100 * (f1 / nb - f0 / na)
        identified = bool(n0 and n1)
        absent = not n0 and not n1
        mix = 100 * (w1-w0) * (r0+r1)/2 if identified else 0.0 if absent else None
        within = 100 * (r1-r0) * (w0+w1)/2 if identified else 0.0 if absent else None
        rows.append(dict(code=code, events_a=n0, fatal_a=f0, events_b=n1, fatal_b=f1,
                         weight_a=w0, weight_b=w1, fatal_share_a=r0, fatal_share_b=r1,
                         mix_pp=mix, within_pp=within, unallocated_pp=0.0 if identified or absent else net,
                         net_pp=net, split_status='identified' if identified else 'both_absent' if absent else 'one_period_absent'))
    return rows


def analyze(root):
    root = Path(root)
    out = root/'reports/decomposition'
    out.mkdir(parents=True, exist_ok=True)
    book_path = root/'data/reference/collision_codebook.json'
    book = json.loads(book_path.read_text())
    assert sha256(root/book['source']['path']) == book['source']['sha256']
    spec = book['fields']['C_CONF']
    sources = {'active': root/'data/derived/ncdb/collisions.parquet'}
    baseline = root/'data/derived/baselines/pre_source_revision_20261015/data/derived/ncdb/collisions.parquet'
    if baseline.exists():
        sources['frozen_baseline'] = baseline
    details, totals, methods = [], [], []
    con = duckdb.connect()
    for source, path in sources.items():
        raw = con.execute(f'''SELECT C_YEAR,is_road_tractor,is_analysis_candidate,C_CONF,
            count(*),count(*) FILTER(WHERE C_SEV='1') FROM read_parquet({quote(path)})
            WHERE C_YEAR BETWEEN 2012 AND 2021 GROUP BY ALL''').fetchall()
        for scenario, (years_a, years_b) in SCENARIOS.items():
            if source != 'active' and scenario != 'primary':
                continue
            for cohort in ('tractor', 'no_recorded_tractor'):
                for subset in ('observed', 'strict'):
                    periods = [defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])]
                    for year, tractor, strict, code, n, f in raw:
                        if tractor != (cohort == 'tractor') or (subset == 'strict' and not strict):
                            continue
                        for counts, years in zip(periods, (years_a, years_b)):
                            if year in years:
                                counts[code][0] += n
                                counts[code][1] += f
                    for counts in periods:
                        for code, _, _ in domain(spec):
                            counts.setdefault(code, [0, 0])
                    rows = components(*periods)
                    meta = dict(source=source, scenario=scenario, cohort=cohort, subset=subset,
                                years_a=','.join(map(str, years_a)), years_b=','.join(map(str, years_b)))
                    for row in rows:
                        _, status, label = category(row['code'], spec)
                        details.append({**meta, 'label': label, 'code_status': status, **row})
                    ns = [sum(n for n, _ in p.values()) for p in periods]
                    fs = [sum(f for _, f in p.values()) for p in periods]
                    mix = sum(r['mix_pp'] or 0 for r in rows)
                    within = sum(r['within_pp'] or 0 for r in rows)
                    unallocated = sum(r['unallocated_pp'] for r in rows)
                    delta = 100 * (fs[1]/ns[1]-fs[0]/ns[0])
                    assert abs(mix+within+unallocated-delta) < 1e-10
                    totals.append({**meta, 'events_a': ns[0], 'fatal_a': fs[0], 'events_b': ns[1],
                                   'fatal_b': fs[1], 'share_a_pct': 100*fs[0]/ns[0], 'share_b_pct': 100*fs[1]/ns[1],
                                   'delta_pp': delta, 'mix_pp': mix, 'within_pp': within,
                                   'unallocated_pp': unallocated,
                                   'unidentified_categories': sum(r['split_status']=='one_period_absent' for r in rows)})
                    for method in ('symmetric', 'a_reference_rates', 'b_reference_rates'):
                        m, v = mix, within
                        if method != 'symmetric':
                            m = v = 0.0
                            for r in rows:
                                if r['split_status'] != 'identified':
                                    continue
                                a_reference = method == 'a_reference_rates'
                                m += 100*(r['weight_b']-r['weight_a'])*r['fatal_share_a' if a_reference else 'fatal_share_b']
                                v += 100*(r['fatal_share_b']-r['fatal_share_a'])*r['weight_b' if a_reference else 'weight_a']
                        assert abs(m+v+unallocated-delta) < 1e-10
                        methods.append({**meta, 'method': method, 'mix_pp': m, 'within_pp': v,
                                        'unallocated_pp': unallocated, 'delta_pp': delta})
    con.close()
    write_csv(out/'category_contributions.csv', details)
    write_csv(out/'totals.csv', totals)
    write_csv(out/'allocation_sensitivity.csv', methods)
    inputs = [*sources.values(), book_path, root/book['source']['path'], root/'data/sources.json']
    summary = {'inputs_sha256': {str(p.relative_to(root)): sha256(p) for p in inputs},
               'code_sha256': {str(p.relative_to(root)): sha256(p) for p in
                               (Path(__file__), root/'src/truck_collisions/analyze_conditions.py',
                                root/'src/truck_collisions/audit_conditions.py', root/'src/truck_collisions/build.py')},
               'baseline_available': baseline.exists(), 'comparisons': len(totals),
               'category_rows': len(details), 'allocation_rows': len(methods),
               'maximum_reconciliation_error_pp': max(abs(r['delta_pp']-r['mix_pp']-r['within_pp']-r['unallocated_pp']) for r in totals)}
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    report(root, totals, details, methods)
    return totals


def report(root, totals, details, methods):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    out = root/'reports/decomposition'
    primary = [r for r in totals if r['source']=='active' and r['scenario']=='primary' and r['subset']=='observed']
    text = ['# Configuration decomposition of fatal-event share', '',
            '## Measure and method', '',
            'Population: reported fatal and injury collisions, not all crashes. Tractor means NCDB type08, with or without a semitrailer. The comparator is no recorded tractor, not cars only. Fatal event means at least one death; this is not a count of people killed.', '',
            'Primary periods are pooled 2012–2016 and 2017–2021, each five years. Events, rather than years, receive equal weight. For configuration k, w is its share of events and r its fatal-event share. P = Σ w r. The symmetric accounting decomposition is:', '',
            '`mix = Σ (wB − wA)(rA + rB)/2`; `within = Σ (rB − rA)(wA + wB)/2`.', '',
            'Multiplication by 100 gives percentage points (pp); mix + within equals the change in P. The interaction is shared equally. Polar reference allocations are exported because the allocation is not unique. Both-absent categories keep undefined rates and zero contributions. One-period-absent categories retain an unallocated entry/exit contribution rather than inventing a rate. No such one-sided category occurs in these comparisons. Unknown/other codes remain in every denominator.', '',
            '## Primary results', '',
            '| Cohort | Fatal/events A | Fatal/events B | Share A → B | Change pp | Mix pp | Within pp |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for r in primary:
        text.append(f"| {r['cohort']} | {r['fatal_a']:,}/{r['events_a']:,} | {r['fatal_b']:,}/{r['events_b']:,} | {r['share_a_pct']:.4f}% → {r['share_b_pct']:.4f}% | {r['delta_pp']:.6f} | {r['mix_pp']:.6f} | {r['within_pp']:.6f} |")
    text += ['', 'Most of the observed tractor change is within configurations. Rear-end and other single-vehicle events have large positive within contributions. Head-on events have a positive mix contribution but a negative within contribution: their fatal-event share fell. These are accounting contributions, not causes or intervention effects.', '',
             '## All sensitivity comparisons', '',
             'The pre2020 comparison uses five early years versus three late years; late_without_2019 uses five versus four. They are pooled event shares, not annual counts. The frozen baseline is an earlier release selection, compared separately without linking case IDs across releases.', '',
             '| Source | Scenario | Cohort | Subset | Change pp | Mix pp | Within pp |',
             '|---|---|---|---|---:|---:|---:|']
    for r in totals:
        text.append(f"| {r['source']} | {r['scenario']} | {r['cohort']} | {r['subset']} | {r['delta_pp']:.6f} | {r['mix_pp']:.6f} | {r['within_pp']:.6f} |")
    text += ['', '## Tractor primary category accounting', '',
             'Rates below are conditional on a reported casualty event. Full precision weights, counts, status flags and contributions are in category_contributions.csv.', '',
             '| Code / configuration | Fatal/events A | Fatal/events B | Fatal share A → B | Mix pp | Within pp | Net pp |',
             '|---|---:|---:|---:|---:|---:|---:|']
    def fmt(value):
        return 'undefined' if value is None else f'{value:.6f}'

    rows = [r for r in details if r['source']=='active' and r['scenario']=='primary' and r['cohort']=='tractor' and r['subset']=='observed']
    for r in rows:
        rates = ' → '.join('undefined' if r['fatal_share_'+p] is None else f"{100*r['fatal_share_'+p]:.3f}%" for p in ('a', 'b'))
        text.append(f"| {r['code']} {r['label']} | {r['fatal_a']}/{r['events_a']} | {r['fatal_b']}/{r['events_b']} | {rates} | {fmt(r['mix_pp'])} | {fmt(r['within_pp'])} | {r['net_pp']:.6f} |")
    text += ['', '## Allocation sensitivity: primary observed cohorts', '',
             '| Cohort | Allocation | Mix pp | Within pp |', '|---|---|---:|---:|']
    for r in methods:
        if r['source']=='active' and r['scenario']=='primary' and r['subset']=='observed':
            text.append(f"| {r['cohort']} | {r['method']} | {r['mix_pp']:.6f} | {r['within_pp']:.6f} |")
    text += ['', '## Interpretation, validation and limits', '',
             'This is a descriptive identity, with no fitted model, sampling intervals, p-values or causal attribution. Within-configuration changes can reflect changing geography, road users, weather, exposure, recording or year composition. A decline in reported injury events can increase fatal share without an increase in fatal counts or underlying physical severity. The comparator is contextual, not a matched control.', '',
             'The current public record series ends in 2021. These results do not answer the intended 2016–2025 decade. Residual two-injury-event benchmark discrepancies remain in 2013 and 2019. Strict filtering, omission of 2019, pre2020, endpoint and frozen-source comparisons preserve those limitations; source changes are not manually adjusted to match publications. Configuration coding does not establish driver fault. Person-level harm is analyzed separately.', '',
             'The primary within contribution remains larger than the mix contribution across the specified sensitivities. The pre2020 mix contribution is small, showing that the numerical allocation depends on the period. No pandemic effect is identified.', '',
             'Reproduce with `PYTHONPATH=src .venv/bin/python -m truck_collisions.decompose_configuration`. summary.json pins input/code hashes; totals.csv, category_contributions.csv and allocation_sensitivity.csv contain inspectable full-precision results. Notebook06 adds direct event-query checks; docs/decomposition_review.md records independent replication. Generated reports are ignored build artifacts; the durable methods and findings are retained in docs/configuration_decomposition.md.', '']
    (out/'findings.md').write_text('\n'.join(text))
    (root/'docs/configuration_decomposition.md').write_text('\n'.join(text))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for offset, field, label in [(-.24, 'mix_pp', 'Configuration mix'), (0, 'within_pp', 'Within configuration'), (.24, 'delta_pp', 'Total change')]:
        ax.bar([i+offset for i in range(2)], [r[field] for r in primary], width=.23, label=label)
    ax.set_xticks(range(2), ['Tractor', 'No recorded tractor'])
    ax.set_ylabel('Change in fatal-event share (percentage points)')
    ax.set_title('2012–2016 → 2017–2021: reported casualty events')
    ax.axhline(0, color='black', linewidth=.6)
    ax.legend(frameon=False)
    fig.tight_layout()
    for ext in ('png', 'svg'):
        fig.savefig(out/f'components.{ext}', dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(11, 10))
    ys = list(range(len(rows)))
    ax.barh([y-.18 for y in ys], [float('nan') if r['mix_pp'] is None else r['mix_pp'] for r in rows], height=.35, label='Mix')
    ax.barh([y+.18 for y in ys], [float('nan') if r['within_pp'] is None else r['within_pp'] for r in rows], height=.35, label='Within')
    ax.set_yticks(ys, [f"{r['code']} {r['label']}" for r in rows], fontsize=9)
    ax.invert_yaxis()
    ax.axvline(0, color='black', linewidth=.6)
    ax.set_xlabel('Contribution to fatal-event-share change (percentage points)')
    ax.set_title('Tractor events: 2012–2016 → 2017–2021')
    ax.legend(frameon=False)
    fig.tight_layout()
    for ext in ('png', 'svg'):
        fig.savefig(out/f'configuration_contributions.{ext}', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    analyze(Path(__file__).resolve().parents[2])
