"""Compare annual outputs with the preserved baseline, never joining event IDs."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .build import sha256


def compare(root):
    baseline = root / 'data/derived/baselines/pre_source_revision_20261015'
    output = root / 'reports/source_revision'
    output.mkdir(parents=True, exist_ok=True)
    comparisons = []
    inputs = {}
    for name, relative, keys in [
        ('events', 'data/derived/ncdb/annual_counts.csv', ('year',)),
        ('people', 'data/derived/casualties/annual_group_counts.csv',
         ('year', 'subset', 'road_user_group')),
    ]:
        paths = [baseline / relative, root / relative]
        tables = []
        for path in paths:
            with path.open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            indexed = {tuple(row[k] for k in keys): row for row in rows}
            assert len(indexed) == len(rows), path
            tables.append(indexed)
            inputs[str(path.relative_to(root))] = sha256(path)
        assert tables[0].keys() == tables[1].keys(), name
        for key in sorted(tables[0]):
            old, new = [table[key] for table in tables]
            for metric in old:
                if metric in keys or metric == 'source_id':
                    continue
                before, after = int(old[metric]), int(new[metric])
                comparisons.append(dict(dataset=name, year=old['year'],
                    subset=old.get('subset', 'observed_and_strict_columns'),
                    road_user_group=old.get('road_user_group', 'all_events'),
                    metric=metric, baseline=before, selected=after, difference=after-before))
    with (output / 'annual_metric_changes.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)
    summary = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        baseline_git_commit='c7baeb3', input_sha256=inputs,
        comparison_code_sha256=sha256(Path(__file__)),
        changed_years=sorted({int(r['year']) for r in comparisons if r['difference']}),
        compared_metric_cells=len(comparisons),
        changed_metric_cells=sum(r['difference'] != 0 for r in comparisons),
        baseline_sources=json.loads((baseline/'sources.json').read_text()),
        selected_sources=json.loads((root/'data/sources.json').read_text()),
        method='Independent annual/group aggregates only; no cross-release case/person joins')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k: summary[k] for k in ('changed_years', 'compared_metric_cells', 'changed_metric_cells')}, indent=2))
    return summary


if __name__ == '__main__':
    compare(Path.cwd())
