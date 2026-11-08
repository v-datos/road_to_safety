"""Reproducible collision-count and conditional-severity temporal descriptions."""
from __future__ import annotations

import argparse
import calendar
import json
from pathlib import Path

import duckdb
import pandas as pd


LABELS = {
    'month': {str(i): calendar.month_name[i] for i in range(1, 13)},
    'weekday': {str(i + 1): name for i, name in enumerate(calendar.day_name)},
    'hour': {str(i): f'{i:02}:00–{i:02}:59' for i in range(24)},
    'season': {'DJF': 'Winter (December–February)', 'MAM': 'Spring (March–May)',
               'JJA': 'Summer (June–August)', 'SON': 'Autumn (September–November)'},
}
FIELDS = {'month': 'C_MNTH', 'weekday': 'C_WDAY', 'hour': 'C_HOUR', 'season': 'season'}


def annotate(frame, dimension):
    """Preserve source codes; unknown and jurisdiction-unavailable are distinct."""
    frame = frame.copy()
    frame['label'] = frame['code'].map(LABELS[dimension])
    frame['value_class'] = 'stated'
    for codes, label, value_class in [
        (['U', 'UU'], 'Unknown', 'unknown'),
        (['X', 'XX'], 'Jurisdiction does not provide this element', 'unavailable'),
    ]:
        selected = frame['code'].isin(codes)
        frame.loc[selected, 'label'] = label
        frame.loc[selected, 'value_class'] = value_class
    missing = frame['label'].isna()
    frame.loc[missing, 'label'] = frame.loc[missing, 'code'].fillna('Unresolved null')
    frame.loc[missing, 'value_class'] = 'unresolved'
    return frame


def summarize(connection, group):
    frame = connection.execute(f"""SELECT {group}, count(*) collisions,
        count(*) FILTER (WHERE severity_eligible) eligible_collisions,
        count(*) FILTER (WHERE is_fatal=1) fatal_collisions,
        count(*) FILTER (WHERE is_fatal=0) injury_collisions
        FROM temporal GROUP BY ALL ORDER BY ALL""").df()
    frame['fatal_proportion'] = frame['fatal_collisions'].div(frame['eligible_collisions'].replace(0, float('nan')))
    frame['sparse_group'] = (frame['eligible_collisions'] < 100) | (frame['fatal_collisions'] < 5)
    return frame


def run(root: Path):
    root = Path(root)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    output = root / 'reports/tables'
    figures = root / 'reports/figures'
    output.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.read_parquet(str(root / 'data/derived/collisions.parquet')).create_view('collisions')
    connection.execute("""CREATE VIEW temporal AS SELECT *, CASE
        WHEN C_MNTH IN ('12','1','2') THEN 'DJF'
        WHEN C_MNTH IN ('3','4','5') THEN 'MAM'
        WHEN C_MNTH IN ('6','7','8') THEN 'JJA'
        WHEN C_MNTH IN ('9','10','11') THEN 'SON'
        ELSE C_MNTH END season FROM collisions""")
    annual = summarize(connection, 'source_id, source_path, source_sha256, C_YEAR').sort_values('C_YEAR')
    actual = (int(annual.collisions.sum()), int(annual.fatal_collisions.sum()))
    receipt = json.loads((root / 'data/derived/prepared_validation.json').read_text())
    assert receipt['status'] == 'passed' and not receipt['failures']
    assert actual == (receipt['collisions'], receipt['fatal_collisions'])
    tables = {'annual': annual}
    for dimension, field in FIELDS.items():
        tables[dimension] = annotate(summarize(connection, f'{field} code'), dimension)
        tables[f'{dimension}_by_year'] = annotate(summarize(connection,
            f'source_id, source_path, source_sha256, C_YEAR, {field} code'), dimension).sort_values(['C_YEAR', 'code'])
    tables['weekday_hour'] = summarize(connection, 'C_WDAY weekday_code, C_HOUR hour_code')
    tables['weekday_hour_by_year'] = summarize(connection,
        'source_id, source_path, source_sha256, C_YEAR, C_WDAY weekday_code, C_HOUR hour_code')
    for name, frame in tables.items():
        # Each table is a complete partition, including all unknown states.
        assert int(frame.collisions.sum()) == actual[0], name
        assert int(frame.fatal_collisions.sum()) == actual[1], name
        assert (frame.eligible_collisions == frame.fatal_collisions + frame.injury_collisions).all(), name
    paths = []
    for name, frame in tables.items():
        path = output / f'eda_temporal_{name}.csv'
        frame.to_csv(path, index=False)
        paths.append(path)

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    def save(fig, name):
        path = figures / f'temporal_{name}.png'
        fig.savefig(path, dpi=180, facecolor='white')
        plt.close(fig)
        paths.append(path)

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout='constrained')
    years = annual.C_YEAR.astype(int)
    axes[0].plot(years, annual.collisions, color='#24576C', marker='o', ms=3)
    axes[0].set_ylabel('Candidate collisions')
    axes[0].yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
    axes[1].plot(years, annual.fatal_proportion * 100, color='#A34B36', marker='o', ms=3)
    axes[1].set_ylabel('Fatal collisions / eligible (%)')
    axes[1].set_xlabel('Source collision year')
    axes[1].set_xticks(list(range(1999, 2022, 2)))
    fig.suptitle('Recorded fatal/injury collision series, 1999–2021', fontsize=13)
    fig.supxlabel('Annual release series; source revisions may differ.\nNo travel-exposure adjustment.', fontsize=9)
    save(fig, 'annual')

    for dimension in FIELDS:
        codes = list(LABELS[dimension])
        frame = tables[dimension].set_index('code').reindex(codes)
        fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout='constrained')
        x = range(len(frame))
        axes[0].bar(x, frame.collisions, color='#24576C')
        axes[1].plot(x, frame.fatal_proportion * 100, color='#A34B36', marker='o')
        axes[0].set_ylabel('Candidate collisions')
        axes[0].yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
        axes[1].set_ylabel('Fatal collisions / eligible (%)')
        labels = [str(code).zfill(2) for code in codes] if dimension == 'hour' else [LABELS[dimension][code][:3] for code in codes]
        axes[1].set_xticks(list(x), labels, rotation=0)
        axes[1].set_xlabel({'month': 'Calendar month', 'season': 'Meteorological season',
                            'weekday': 'Reported weekday', 'hour': 'Reported hour (00 = midnight)'}[dimension])
        unknown = int(tables[dimension].query("value_class != 'stated'").collisions.sum())
        fig.suptitle(f'{dimension.title()} patterns in fatal/injury collisions, 1999–2021', fontsize=13)
        fig.supxlabel(f'Stated categories shown; {unknown:,} non-stated collisions retained in tables.\n'
                      'Counts are not exposure rates; fatal proportions use eligible collisions.', fontsize=9)
        save(fig, dimension)

    heat = tables['weekday_hour']
    heat = heat[heat.weekday_code.isin(LABELS['weekday']) & heat.hour_code.isin(LABELS['hour'])]
    grid = pd.MultiIndex.from_product([list(LABELS['weekday']), list(LABELS['hour'])], names=['weekday_code','hour_code'])
    heat = heat.set_index(['weekday_code','hour_code']).reindex(grid)
    # Structural absences have zero counts and an undefined proportion.
    heat['collisions'] = heat['collisions'].fillna(0)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), layout='constrained')
    for axis, column, title, color in [
        (axes[0], 'collisions', 'Candidate collision counts', 'Blues'),
        (axes[1], 'fatal_proportion', 'Fatal-collision proportion among eligible collisions (%)', 'YlOrRd'),
    ]:
        values = heat[column].to_numpy().reshape(7,24)
        if column == 'fatal_proportion':
            values = values * 100
        picture = axis.imshow(values, aspect='auto', cmap=color)
        axis.set_yticks(range(7), [day[:3] for day in calendar.day_name])
        axis.set_xticks(range(24), [f'{hour:02}' for hour in range(24)])
        axis.set_title(title)
        fig.colorbar(picture, ax=axis, shrink=.85)
    axes[1].set_xlabel('Reported hour (00 = midnight)')
    absent = actual[0] - int(heat.collisions.sum())
    fig.suptitle('Weekday and hour, pooled 1999–2021', fontsize=13)
    fig.supxlabel(f'Both fields stated: {actual[0]-absent:,} collisions; {absent:,} retained outside heatmaps.\n'
                  'Fatal proportions use eligible collisions. No travel-exposure denominator.', fontsize=9)
    save(fig, 'weekday_hour')
    connection.close()
    return paths


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    for artifact in run(args.root):
        print(artifact)
