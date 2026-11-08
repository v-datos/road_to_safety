"""Descriptive condition–severity comparisons of the validated collision dataset."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import duckdb
import pandas as pd

# Official NCDB dictionary, English pages 4–6. Codes are canonical unpadded strings.
LABELS = {
    'C_WTHR': ['Clear and sunny', 'Overcast, no precipitation', 'Raining',
               'Snowing (excluding drifting snow)', 'Freezing rain, sleet, hail',
               'Visibility limitation', 'Strong wind'],
    'C_RSUR': ['Dry, normal', 'Wet', 'Snow (fresh, loose)', 'Slush, wet snow',
               'Icy (including packed snow)', 'Sand/gravel/dirt debris', 'Muddy',
               'Oil (including spilled/applied liquid)', 'Flooded'],
    'C_RCFG': ['Non-intersection', 'Intersection of public roadways',
               'Intersection with private entrance/exit', 'Railroad level crossing',
               'Bridge, overpass, viaduct', 'Tunnel or underpass', 'Passing or climbing lane',
               'Ramp', 'Traffic circle', 'Freeway express lane', 'Freeway collector lane',
               'Freeway transfer lane'],
    'C_RALN': ['Straight and level', 'Straight with gradient', 'Curved and level',
               'Curved with gradient', 'Top of hill or gradient', 'Bottom of hill or gradient'],
    'C_TRAF': ['Traffic signals operational', 'Traffic signals flashing', 'Stop sign',
               'Yield sign', 'Warning sign', 'Pedestrian crosswalk', 'Police officer',
               'School guard/flagman', 'School crossing', 'Reduced speed zone',
               'No passing zone sign', 'Road markings', 'Stopped school bus, signals flashing',
               'Stopped school bus, signals not flashing', 'Railway signals/gates',
               'Railway signs only', 'Control device not specified', 'No control present'],
}
TITLES = {'C_WTHR': 'Weather', 'C_RSUR': 'Road surface', 'C_RCFG': 'Road configuration',
          'C_RALN': 'Road alignment', 'C_TRAF': 'Traffic control'}


def classify(code):
    if code is None or code == '':
        return 'missing'
    return {'U': 'unknown', 'X': 'jurisdiction_unavailable', 'Q': 'other'}.get(
        code[0], 'stated') if len(set(code)) == 1 else 'stated'


def label(field, code):
    group = classify(code)
    if group != 'stated':
        return {'unknown': 'Unknown', 'jurisdiction_unavailable': 'Jurisdiction unavailable',
                'other': 'Other', 'missing': 'Missing'}[group]
    return LABELS[field][int(code) - 1]


def wilson(fatal, total):
    """Binomial descriptive interval, without a sampling-design or causal claim."""
    if not total:
        return math.nan, math.nan
    z = 1.959963984540054
    p = fatal / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return max(0., center-half), min(1., center+half)


def enrich(frame):
    frame = frame.copy()
    frame['fatal_collisions'] = frame['fatal_collisions'].astype('int64')
    frame['injury_collisions'] = frame['collisions'] - frame['fatal_collisions']
    frame['fatal_proportion'] = frame['fatal_collisions'] / frame['collisions']
    intervals = [wilson(f, n) for f, n in zip(frame.fatal_collisions, frame.collisions)]
    frame['wilson95_lower'] = [v[0] for v in intervals]
    frame['wilson95_upper'] = [v[1] for v in intervals]
    frame['sparse_n_lt_100_or_fatal_lt_5'] = (frame.collisions < 100) | (frame.fatal_collisions < 5)
    frame['value_class'] = frame.code.map(classify)
    frame['label'] = [label(f, c) for f, c in zip(frame.field, frame.code)]
    return frame


def run(root: Path):
    root = Path(root)
    tables = root/'reports/tables'
    figures = root/'reports/figures'
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.read_parquet(str(root/'data/derived/collisions.parquet')).create_view('collisions')
    n, fatal, excluded = connection.execute('SELECT count(*),sum(is_fatal),count(*) FILTER '
        '(WHERE NOT severity_eligible OR is_fatal IS NULL) FROM collisions').fetchone()
    if excluded:
        raise ValueError('This analysis requires the fully eligible validated cohort.')
    annual_totals = connection.execute('SELECT C_YEAR AS year,source_id,source_path,source_sha256,'
        'count(*) AS year_collisions FROM collisions GROUP BY ALL ORDER BY C_YEAR').df()
    assert annual_totals.year.is_unique
    pieces = []
    for field in LABELS:
        frame = connection.execute(f"SELECT C_YEAR AS year,'{field}' AS field,{field} AS code,"
            f'count(*) AS collisions,sum(is_fatal) AS fatal_collisions FROM collisions '
            f'GROUP BY C_YEAR,{field} ORDER BY C_YEAR,{field}').df()
        pieces.append(frame)
    annual = enrich(pd.concat(pieces, ignore_index=True))
    annual = annual.merge(annual_totals, on='year', validate='many_to_one')
    annual['share_of_year_collisions'] = annual.collisions / annual.year_collisions
    pooled = enrich(annual.groupby(['field', 'code'], as_index=False)[
        ['collisions', 'fatal_collisions']].sum())
    pooled['share_of_all_collisions'] = pooled.collisions / n
    stated_totals = pooled[pooled.value_class == 'stated'].groupby('field').collisions.sum()
    pooled['share_of_stated_collisions'] = [row.collisions/stated_totals[row.field]
        if row.value_class == 'stated' else math.nan for row in pooled.itertuples()]
    # A descriptive year-composition sensitivity: give each category the same year weights.
    # No imputation for categories absent in any year, and no adjustment for other covariates.
    weights = dict(zip(annual_totals.year, annual_totals.year_collisions/n))
    sensitivity = []
    for row in pooled.itertuples():
        group = annual[(annual.field == row.field) & (annual.code == row.code)]
        complete = set(group.year) == set(weights)
        standardized = sum(weights[r.year]*r.fatal_proportion for r in group.itertuples()) if complete else math.nan
        sensitivity.append({'field': row.field, 'code': row.code, 'label': row.label,
            'years_observed': len(group), 'all_years_supported': complete,
            'observed_sparse_years': int(group.sparse_n_lt_100_or_fatal_lt_5.sum()),
            'any_sparse_year': bool(group.sparse_n_lt_100_or_fatal_lt_5.any()),
            'pooled_fatal_proportion': row.fatal_proportion,
            'common_year_weighted_fatal_proportion': standardized,
            'difference_percentage_points': 100*(standardized-row.fatal_proportion)})
    sensitivity = pd.DataFrame(sensitivity)
    for field in LABELS:
        part = pooled[pooled.field == field]
        assert int(part.collisions.sum()) == n
        assert int(part.fatal_collisions.sum()) == fatal
        for year, expected in zip(annual_totals.year, annual_totals.year_collisions):
            assert int(annual[(annual.field == field) & (annual.year == year)].collisions.sum()) == expected
    annual.to_csv(tables/'eda_condition_by_year.csv', index=False)
    pooled.to_csv(tables/'eda_condition_pooled.csv', index=False)
    sensitivity.to_csv(tables/'eda_condition_year_standardization.csv', index=False)
    plot_conditions(pooled, figures)
    write_findings(root, pooled, annual, sensitivity, n, fatal)
    connection.close()
    return {'collisions': n, 'fatal_collisions': fatal, 'fields': len(LABELS),
            'pooled_rows': len(pooled), 'annual_rows': len(annual)}


def plot_conditions(pooled, figures):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for field in LABELS:
        part = pooled[pooled.field == field].sort_values('fatal_proportion').reset_index(drop=True)
        fig, ax = plt.subplots(figsize=(10.8, max(5, .39*len(part)+1.7)))
        y = range(len(part))
        colors = ['#196c83' if c == 'stated' else '#887755' for c in part.value_class]
        ax.barh(y, 100*part.fatal_proportion, color=colors, height=.65)
        ax.errorbar(100*part.fatal_proportion, y,
            xerr=[100*(part.fatal_proportion-part.wilson95_lower),
                  100*(part.wilson95_upper-part.fatal_proportion)], fmt='none',
            ecolor='#26343a', capsize=2, linewidth=.8)
        ax.set_yticks(list(y), [f'{r.label}{" *" if r.sparse_n_lt_100_or_fatal_lt_5 else ""} '
            f'(n={int(r.collisions):,})' for r in part.itertuples()], fontsize=9)
        ax.set_xlabel('Fatal collisions / recorded fatal or injury collisions (%)')
        ax.set_xlim(left=0)
        ax.set_title(f'{TITLES[field]} and recorded collision severity, 1999–2021', loc='left', fontsize=12)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
        fig.text(.02, .015, '95% Wilson descriptive intervals; * n<100 or fatal<5. Unknown/other retained. '
                 'Unadjusted associations; no traffic-exposure denominator.', fontsize=8)
        fig.tight_layout(rect=[0, .045, 1, 1])
        fig.savefig(figures/f'conditions_{field.lower()}.png', dpi=170)
        plt.close(fig)


def write_findings(root, pooled, annual, sensitivity, n, fatal):
    def measure(field, code):
        row = pooled[(pooled.field == field) & (pooled.code == code)].iloc[0]
        return f'{int(row.fatal_collisions):,}/{int(row.collisions):,} ({100*row.fatal_proportion:.3f}%)'
    clear = pooled[(pooled.field == 'C_WTHR') & (pooled.code == '1')].iloc[0]
    lines = ['# Condition–severity descriptive findings', '',
        f'The cohort contains **{n:,} candidate collisions**, including **{fatal:,} fatal collisions** '
        f'({100*fatal/n:.4f}%), from the selected 1999–2021 NCDB releases. '
        'These are fatal/injury collisions, not all crashes or traffic exposure.', '',
        '## Methods and denominators', '',
        'Each candidate collision contributes once to every condition table. Fatal proportion is '
        '`fatal_collisions / collisions` within that exact field/category/year; injury collisions are '
        'the complement. This measures recorded severity conditional on a collision being in the '
        'fatal/injury extract. It does not measure the chance of having a crash in a condition. '
        'No weighting by source person records, deletion of unknowns, or significance tests are used.', '',
        'Code labels were checked against the archived official NCDB data dictionary, English pages '
        '4–6. Sand/gravel/dirt means debris, not pavement construction. Visibility limitation includes '
        'drifting snow, fog, smog, dust, smoke and mist. Icy includes packed snow. `Q/QQ` means other; '
        '`U/UU` means unknown; `X/XX` means jurisdiction unavailable. Each is distinct. '
        'No unavailable or blank values occur in these five fields in this cohort.', '',
        '95% Wilson intervals provide a familiar binomial precision description, not design-based '
        'confidence intervals for the complete Canadian collision population. Administrative coverage, '
        'coding changes, selection and dependence can dominate that precision. Sparse groups are '
        'flagged when n<100 or fatal collisions<5, without removing them. Absent year/category '
        'combinations have no observed collisions and are absent from the annual condition table; '
        'they are not zero fatal-proportion observations.', '',
        '## Main descriptive signals', '',
        f'Clear/sunny conditions account for {measure("C_WTHR", "1")} fatal/total collisions '
        f'and {100*clear.fatal_collisions/fatal:.2f}% of the cohort’s fatal collisions. Visibility '
        f'limitation has {measure("C_WTHR", "6")}; strong wind has {measure("C_WTHR", "7")}. '
        f'Rain has {measure("C_WTHR", "3")} and snowing has {measure("C_WTHR", "4")}. '
        'These comparisons are not evidence that precipitation reduces '
        'crash likelihood or mortality.', '',
        f'Dry/normal surfaces have {measure("C_RSUR", "1")}; wet surfaces have '
        f'{measure("C_RSUR", "2")}. Sand/gravel/dirt debris has {measure("C_RSUR", "6")}, '
        f'muddy surfaces {measure("C_RSUR", "7")}, and flooding {measure("C_RSUR", "9")}. '
        f'Flooding’s small denominator and oil’s low fatal count ({measure("C_RSUR", "8")}) '
        'make extreme rankings fragile. Oil is explicitly flagged sparse.', '',
        f'Curved/gradient alignment has {measure("C_RALN", "4")}, compared '
        f'with {measure("C_RALN", "1")} on straight/level alignments. This is a hypothesis '
        'for later multivariable severity modeling, not an isolated effect of curvature or gradient.', '',
        '## Pooled comparisons', '']
    for field in LABELS:
        lines += [f'### {TITLES[field]} (`{field}`)', '',
            '| Code | Category | Collisions | Fatal | Injury | Fatal % | Wilson 95% % | Sparse |',
            '|---|---|---:|---:|---:|---:|---:|---|']
        for row in pooled[pooled.field == field].sort_values('fatal_proportion', ascending=False).itertuples():
            lines.append(f'| {row.code} | {row.label} | {int(row.collisions):,} | '
                f'{int(row.fatal_collisions):,} | {int(row.injury_collisions):,} | '
                f'{100*row.fatal_proportion:.3f} | {100*row.wilson95_lower:.3f}–'
                f'{100*row.wilson95_upper:.3f} | {"Yes" if row.sparse_n_lt_100_or_fatal_lt_5 else "No"} |')
        lines += ['']
    lines += ['## Year composition and stability sensitivity', '',
        'The year-standardization table applies the same annual weights to every category: each '
        'year’s share of all cohort collisions. It averages within-year category fatal proportions. '
        'This is a descriptive check of changing year composition only; it does not control weather, '
        'speed, road type, location or road-user mix. Estimates are withheld when a category is absent '
        'in any year. The pooled estimate remains the primary observed cohort proportion. '
        'Observed sparse years count annual cells with n<100 or fatal<5, even when the pooled '
        'group is not sparse. The largest shifts below include railway signs only and '
        'passing/climbing lanes, both sparse in 23/23 years, and reduced speed zones, sparse '
        'in 22/23 years. These shifts are '
        'fragile descriptive sensitivities, not evidence of reliable year-composition effects.', '',
        '| Field | Category | Pooled % | Common-year-weighted % | Difference, percentage points | Sparse years / observed | Any sparse year |',
        '|---|---|---:|---:|---:|---:|---|']
    for row in sensitivity[sensitivity.all_years_supported].sort_values(
            'difference_percentage_points', key=abs, ascending=False).head(12).itertuples():
        lines.append(f'| {row.field} | {row.label} | {100*row.pooled_fatal_proportion:.3f} | '
            f'{100*row.common_year_weighted_fatal_proportion:.3f} | {row.difference_percentage_points:+.3f} | '
            f'{row.observed_sparse_years}/{row.years_observed} | {"Yes" if row.any_sparse_year else "No"} |')
    lines += ['', f'{int(annual.sparse_n_lt_100_or_fatal_lt_5.sum()):,} of {len(annual):,} '
        'observed year/category cells meet the sparse rule. These include supporting road configuration '
        'and traffic-control groups, so small annual cells should not be ranked as stable risk factors.', '',
        '## Interpretation and limitations', '',
        'Condition comparisons are observational and unadjusted. Higher fatal proportions can reflect '
        'speed, urban/rural mix, crash type, participants, time of day, emergency response, or selective '
        'reporting rather than an independent condition effect. A common condition can contribute '
        'many fatal collisions while having a lower conditional fatal proportion. The analysis cannot '
        'justify a claim that snow, wet pavement, traffic signals or other recorded conditions prevent '
        'or cause deaths. Policy proposals require adjustment, exposure and local evidence.', '',
        'The candidate collision identity is release-scoped; source key semantics remain undocumented. '
        'The selected historic releases do not reconcile exactly to the newer national publication '
        'series, so these results describe the prepared microdata cohort. No precise geographic '
        'mapping is possible from its released fields. See the main descriptive analysis for source-year '
        'missingness and temporal patterns.', '',
        '## Reproduction and checks', '',
        'Run `.venv/bin/python -m road_to_safety.analyze_conditions` from the project directory. '
        'Outputs: `reports/tables/eda_condition_pooled.csv`, `eda_condition_by_year.csv`, '
        '`eda_condition_year_standardization.csv`; five `reports/figures/conditions_*.png` figures. '
        'The producer asserts that every field reconciles to the complete collision and fatal totals '
        'and that every field/year reconciles to that year’s collision denominator. '
        'Inputs are read-only; the preparation data and validation outputs are unchanged.', '']
    (root/'docs/condition_findings.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    print(run(parser.parse_args().root))
