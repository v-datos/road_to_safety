"""Score the frozen 2019 development model on reused 2020–2021 records; never fit."""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.special import expit
from sklearn.metrics import average_precision_score, roc_auc_score
from .explore import sha256, verify_inputs

PROTOCOL = 'data/reference/calibration_stress_v1_protocol.json'
FROZEN_HASH = 'a7c1732e8aa9348c264d8e5d118b7e93190a73604d600b405ec5ca5655eef54d'
METHODS = ('unchanged', 'sigmoid', 'prevalence')
COLORS = {'unchanged': '#2166ac', 'sigmoid': '#1b7837', 'prevalence': '#d95f02'}


def score_json(model, frame):
    """Apply archived dummy coefficients, without estimating any parameter."""
    for feature in model['features']:
        if not frame[feature].isin(model['categories'][feature]).all():
            raise ValueError(f'Unsupported categorical value: {feature}')
    if len(model['encoded_features']) != len(model['coefficients']):
        raise ValueError('Inconsistent archived coefficient dimensions')
    z = np.full(len(frame), model['intercept'], dtype=float)
    for term, coefficient in zip(model['encoded_features'], model['coefficients']):
        z += frame[term['feature']].eq(term['code']).to_numpy() * coefficient
    if not np.isfinite(z).all():
        raise ValueError('Nonfinite archived logit')
    return z


def probability_metrics(y, p):
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    n, fatal = len(y), int(y.sum())
    result = {'n': n, 'fatal': fatal, 'nonfatal': n-fatal,
              'sparse_n_lt_100_or_fatal_lt_5': n < 100 or fatal < 5}
    fields = ('observed_prevalence', 'mean_prediction', 'prediction_minus_observed',
              'observed_expected_ratio', 'log_loss', 'brier_score', 'average_precision', 'roc_auc')
    if not n:
        return {**result, **dict.fromkeys(fields)}
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid labels/probabilities')
    q = np.clip(p, np.finfo(float).eps, 1-np.finfo(float).eps)
    observed, predicted = float(y.mean()), float(p.mean())
    return {**result, 'observed_prevalence': observed, 'mean_prediction': predicted,
            'prediction_minus_observed': predicted-observed,
            'observed_expected_ratio': observed/predicted if predicted else None,
            'log_loss': float(np.mean(-y*np.log(q)-(1-y)*np.log1p(-q))),
            'brier_score': float(np.mean((y-p)**2)),
            'average_precision': float(average_precision_score(y, p)) if 0 < fatal < n else None,
            'roc_auc': float(roc_auc_score(y, p)) if 0 < fatal < n else None}


def reliability(y, p, edges):
    y, p = np.asarray(y), np.asarray(p)
    indices = np.minimum(np.searchsorted(edges, p, side='right')-1, len(edges)-2)
    rows = []
    for i, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        mask = indices == i
        n, fatal = int(mask.sum()), int(y[mask].sum())
        rows.append({'bin': i, 'left': left, 'right': right, 'n': n, 'fatal': fatal,
                     'mean_prediction': float(p[mask].mean()) if n else None,
                     'observed_fraction': float(y[mask].mean()) if n else None,
                     'sparse_n_lt_100_or_fatal_lt_5': n < 100 or fatal < 5})
    return rows


def assess_transfer(annual, tolerance=1e-10):
    """Fixed per-year directional gates; no candidate selection or replacement."""
    rows = []
    for year in ('2020', '2021'):
        a = annual[(annual.population.astype(str) == year) & annual.group.eq('all')].set_index('method')
        base, calibrated = a.loc['unchanged'], a.loc['sigmoid']
        ll = float(calibrated.log_loss-base.log_loss)
        brier = float(calibrated.brier_score-base.brier_score)
        gap = float(abs(calibrated.prediction_minus_observed)-abs(base.prediction_minus_observed))
        rows.append({'population': year, 'log_loss_difference': ll, 'brier_difference': brier,
                     'absolute_aggregate_gap_difference': gap,
                     'log_loss_improved': ll < -tolerance,
                     'brier_not_worse': brier <= tolerance,
                     'absolute_aggregate_gap_not_worse': gap <= tolerance,
                     'year_gate_passed': ll < -tolerance and brier <= tolerance})
    return {'year_results': rows, 'both_years_passed': all(r['year_gate_passed'] for r in rows),
            'assessment': 'favorable_descriptive_transfer' if all(r['year_gate_passed'] for r in rows) else 'transfer_not_demonstrated',
            'interpretation': 'Reused retrospective stress evidence only; no model replacement, selection or deployment decision.'}


def plot_tables(root):
    tables, figures = root/'reports/tables', root/'reports/figures'
    metrics = pd.read_csv(tables/'cstress_v1_metrics.csv', dtype={'population': str})
    annual = metrics[metrics.group.eq('all') & metrics.population.isin(['2020', '2021'])]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    for method in METHODS:
        rows = annual[annual.method.eq(method)].sort_values('population')
        for ax, field, label in zip(axes, ['log_loss', 'brier_score', 'prediction_minus_observed'],
                                   ['Natural-log loss (lower better)', 'Brier score (lower better)', 'Mean predicted − observed (percentage points)']):
            values = rows[field] * (100 if field == 'prediction_minus_observed' else 1)
            ax.plot(rows.population, values, marker='o', label=method, color=COLORS[method])
            ax.set_ylabel(label); ax.set_xlabel('Reused retrospective year'); ax.grid(alpha=.2)
    axes[2].axhline(0, color='gray', lw=1)
    axes[0].legend(frameon=False)
    fig.suptitle('Frozen 2019 development model: 2020–2021 stress scores (no fitting)')
    fig.tight_layout(); fig.savefig(figures/'cstress_v1_scores.png', dpi=160); plt.close(fig)
    bins = pd.read_csv(tables/'cstress_v1_reliability.csv', dtype={'population': str})
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    for i, year in enumerate(('2020', '2021')):
        for j, scheme in enumerate(('fixed_10', 'low_probability')):
            ax = axes[i, j]
            ax.plot([0, 1], [0, 1], '--', color='gray', lw=1)
            omitted = []
            for method in METHODS:
                rows = bins[(bins.population == year) & (bins.scheme == scheme) & (bins.method == method) & (bins.n > 0)]
                if j:
                    visible = rows[(rows.mean_prediction <= .1) & (rows.observed_fraction <= .1)]
                    omitted.append(f'{method}: {int(rows.loc[~rows.index.isin(visible.index), "n"].sum()):,}')
                else:
                    visible = rows
                regular = ~visible.sparse_n_lt_100_or_fatal_lt_5
                ax.scatter(visible.loc[regular, 'mean_prediction'], visible.loc[regular, 'observed_fraction'], color=COLORS[method], marker='o', label=method)
                ax.scatter(visible.loc[~regular, 'mean_prediction'], visible.loc[~regular, 'observed_fraction'], color=COLORS[method], marker='x')
                ax.plot(visible.mean_prediction, visible.observed_fraction, color=COLORS[method], alpha=.5, lw=1)
            ax.set_xlim(0, .1 if j else 1); ax.set_ylim(0, .1 if j else 1)
            ax.set_title(f'{year}: {scheme}' + ('; omitted collision n\n' + '; '.join(omitted) if j else ''))
            ax.set_xlabel('Mean predicted fatal-collision probability'); ax.set_ylabel('Observed fatal-collision fraction')
            ax.grid(alpha=.2)
    axes[0, 0].legend(frameon=False)
    fig.suptitle('Fixed-bin reliability; crosses flag n < 100 or fatal < 5\nFull range at left; 0–10% zoom at right; empty bins retained in evidence tables')
    fig.tight_layout(rect=[0, 0, 1, .94]); fig.savefig(figures/'cstress_v1_reliability.png', dpi=160); plt.close(fig)


def run(root):
    root = Path(root)
    verify_inputs(root)
    if not FROZEN_HASH or sha256(root/PROTOCOL) != FROZEN_HASH:
        raise ValueError('Protocol must match pre-scoring frozen hash')
    protocol = json.loads((root/PROTOCOL).read_text())
    for relative, expected in protocol['input_fingerprints'].items():
        if sha256(root/relative) != expected:
            raise ValueError(f'Stale frozen input {relative}')
    for relative, required in protocol['upstream_status_required'].items():
        if json.loads((root/relative).read_text())['status'] != required:
            raise ValueError(f'Unpassed upstream receipt {relative}')
    derived = root/'data/derived/calibration_stress_v1'
    if (derived/'manifest.json').exists():
        raise ValueError('Completed stress version exists; preserve it and version any new experiment')
    derived.mkdir(exist_ok=True, parents=True)
    tables, figures = root/'reports/tables', root/'reports/figures'
    tables.mkdir(exist_ok=True, parents=True); figures.mkdir(exist_ok=True, parents=True)
    model_path = root/'data/derived/temporal_calibration_v1/model_2019.json'
    model = json.loads(model_path.read_text())
    if model['eval_year'] != 2019 or model['calibrators']['sigmoid']['slope'] <= 0:
        raise ValueError('Unexpected archived development model')
    if any(model[key] != value for key, value in protocol['frozen_model_parameters'].items()):
        raise ValueError('Archived base parameters differ from frozen protocol')
    if any(model['calibrators']['sigmoid'][key] != value for key, value in protocol['frozen_sigmoid_parameters'].items()):
        raise ValueError('Archived sigmoid differs from frozen protocol')
    if json.loads((root/protocol['saved_selection_path']).read_text())['selected_method'] != 'sigmoid':
        raise ValueError('Saved selection differs from frozen comparison')
    model_copy = derived/'archived_model_2019.json'
    model_copy.write_bytes(model_path.read_bytes())
    con = duckdb.connect()
    features = model['features']
    frame = con.execute('SELECT source_id,source_path,source_sha256,C_YEAR,C_CASE,is_fatal,severity_eligible,' + ','.join(features) +
                        ' FROM read_parquet(?) WHERE CAST(C_YEAR AS INTEGER) IN (2020,2021) ORDER BY C_YEAR,source_id,C_CASE',
                        [str(root/'data/derived/collisions.parquet')]).df()
    if not len(frame) or not frame.severity_eligible.all() or not frame.is_fatal.isin([0,1]).all() or frame.duplicated(['source_id','C_YEAR','C_CASE']).any():
        raise ValueError('Invalid collision identity/target')
    z = score_json(model, frame)
    frame['raw_logit'] = z
    frame['p_unchanged'] = expit(z)
    frame['p_sigmoid'] = expit(model['calibrators']['sigmoid']['slope']*z + model['calibrators']['sigmoid']['intercept'])
    frame['p_prevalence'] = model['train_prevalence']
    for name, codes in [('unknown', ['U', 'UU']), ('other', ['Q', 'QQ']), ('unavailable', ['X', 'XX'])]:
        frame['has_'+name] = frame[features].isin(codes).any(axis=1)
    frame['has_unknown_or_unavailable'] = frame.has_unknown | frame.has_unavailable
    support = pd.read_csv(root/'reports/tables/tcal_v1_level_support.csv', dtype={'code': str})
    support = support[support.eval_year.eq(2019)]
    absent = {f: support.loc[support.feature.eq(f) & support.train_unobserved, 'code'].tolist() for f in features}
    frame['has_train_unobserved_level'] = np.logical_or.reduce([frame[f].isin(absent[f]).to_numpy() for f in features])
    con.register('new_scores', frame)
    old = con.execute('SELECT a.source_id,a.C_YEAR,a.C_CASE,a.is_fatal,a.p_logistic FROM read_parquet(?) a JOIN new_scores b USING(source_id,C_YEAR,C_CASE)',
                      [str(root/'data/derived/severity_predictions.parquet')]).df()
    joined = frame.merge(old, on=['source_id', 'C_YEAR', 'C_CASE'], suffixes=('', '_old'), validate='one_to_one')
    max_difference = float(np.max(np.abs(joined.p_unchanged-joined.p_logistic)))
    if len(joined) != len(frame) or not joined.is_fatal.eq(joined.is_fatal_old).all() or max_difference > 1e-12:
        raise ValueError('Unchanged probability does not reproduce original baseline')
    con.execute('COPY new_scores TO ? (FORMAT PARQUET, COMPRESSION ZSTD)', [str(derived/'predictions.parquet')])
    metrics_rows, bins_rows, support_rows, membership_rows = [], [], [], []
    for population in ('2020', '2021', 'pooled'):
        pop = frame if population == 'pooled' else frame[frame.C_YEAR.eq(population)]
        groups = [('all', np.ones(len(pop), dtype=bool))]
        for flag in ('has_unknown', 'has_other', 'has_unavailable', 'has_unknown_or_unavailable', 'has_train_unobserved_level'):
            for present in (False, True):
                groups.append((f'{flag}={present}', pop[flag].eq(present).to_numpy()))
        for f in features:
            for status, codes in [('unknown', ['U', 'UU']), ('other', ['Q', 'QQ']), ('unavailable', ['X', 'XX']), ('stated', None)]:
                mask = ~pop[f].isin(['U','UU','Q','QQ','X','XX']) if codes is None else pop[f].isin(codes)
                groups.append((f'{f}:{status}', mask.to_numpy()))
        for group, mask in groups:
            for method in METHODS:
                metrics_rows.append({'population': population, 'group': group, 'method': method,
                                     **probability_metrics(pop.is_fatal.to_numpy()[mask], pop['p_'+method].to_numpy()[mask])})
        for method in METHODS:
            for scheme, edges in protocol['reliability']['schemes'].items():
                bins_rows.extend({'population': population, 'method': method, 'scheme': scheme, **row}
                                 for row in reliability(pop.is_fatal.to_numpy(), pop['p_'+method].to_numpy(), edges))
        for (source_id, source_year), r in pop.groupby(['source_id','C_YEAR']).is_fatal.agg(['size','sum']).iterrows():
            membership_rows.append({'population': population, 'source_id': source_id, 'source_year': source_year,
                                    'n': int(r['size']), 'fatal': int(r['sum']), 'nonfatal': int(r['size']-r['sum'])})
        for r in support.to_dict('records'):
            mask = pop[r['feature']].eq(r['code'])
            n, fatal = int(mask.sum()), int(pop.loc[mask, 'is_fatal'].sum())
            support_rows.append({'population': population, **r, 'stress_n': n, 'stress_fatal': fatal,
                                 'stress_nonfatal': n-fatal, 'stress_prevalence': fatal/n if n else None,
                                 'stress_sparse_n_lt_100_or_fatal_lt_5': n < 100 or fatal < 5})
    metrics = pd.DataFrame(metrics_rows)
    annual = metrics[metrics.group.eq('all') & metrics.population.isin(['2020','2021'])]
    numeric = ['log_loss','brier_score','average_precision','roc_auc','mean_prediction','observed_prevalence','prediction_minus_observed','observed_expected_ratio']
    macro = annual.groupby('method')[numeric].agg(['mean','std'])
    macro.columns = ['_'.join(c) for c in macro.columns]; macro = macro.reset_index()
    bins = pd.DataFrame(bins_rows)
    ece = []
    for (population, method, scheme), group in bins.groupby(['population','method','scheme']):
        valid = group[group.n > 0]
        ece.append({'population': population, 'method': method, 'scheme': scheme,
                    'n': int(valid.n.sum()), 'ece': float((valid.n*(valid.observed_fraction-valid.mean_prediction).abs()).sum()/valid.n.sum())})
    assessment = assess_transfer(annual)
    differences = []
    for population, group in metrics[metrics.group.eq('all')].groupby('population'):
        indexed = group.set_index('method')
        for method in ('sigmoid', 'prevalence'):
            a, b = indexed.loc[method], indexed.loc['unchanged']
            differences.append({'population': population, 'method': method, **{field+'_difference': float(a[field]-b[field]) for field in numeric},
                                'relative_log_loss_difference': float((a.log_loss-b.log_loss)/b.log_loss)})
    indexed = macro.set_index('method')
    for method in ('sigmoid', 'prevalence'):
        a, b = indexed.loc[method], indexed.loc['unchanged']
        differences.append({'population': 'macro', 'method': method, **{field+'_difference': float(a[field+'_mean']-b[field+'_mean']) for field in numeric},
                            'relative_log_loss_difference': float((a.log_loss_mean-b.log_loss_mean)/b.log_loss_mean)})
    outputs = {'metrics': metrics, 'macro': macro, 'reliability': bins, 'ece': pd.DataFrame(ece),
               'level_support': pd.DataFrame(support_rows), 'membership': pd.DataFrame(membership_rows),
               'transfer_gates': pd.DataFrame(assessment['year_results']), 'differences': pd.DataFrame(differences)}
    paths = []
    for name, result in outputs.items():
        path = tables/f'cstress_v1_{name}.csv'; result.to_csv(path, index=False); paths.append(path)
    assessment_path = derived/'assessment.json'; assessment_path.write_text(json.dumps(assessment, indent=2)+'\n')
    plot_tables(root)
    card = root/'models/calibration_stress_v1_card.md'
    card.write_text('# Frozen calibration transfer stress test v1\n\n'
        'This scoring-only experiment applies the saved 2019 development fold: logistic regression fitted on 1999–2016, '
        'sigmoid calibration fitted on 2017–2018, selected using the six 2014–2019 developmental evaluations. '
        'No estimator, calibrator, prevalence, threshold or hyperparameter is fitted to 2020–2021.\n\n'
        'Population: all prepared severity-eligible candidate collisions in the 2020 and 2021 releases. '
        'Target: fatal versus injury among recorded collisions; no accident-occurrence, individual mortality, causal or deployment inference. '
        'Dictionary-supported unknown, other and unavailable categories remain separate.\n\n'
        f'Frozen protocol SHA-256: `{FROZEN_HASH}`. Original-model maximum absolute probability discrepancy: `{max_difference:.3g}`.\n\n'
        'Comparators: unchanged probabilities, saved sigmoid correction, and constant 1999–2016 training fatal prevalence. '
        'Report each year, pooled collision-weighted evidence, and macro annual mean/sample SD. Sample SD is descriptive, not uncertainty coverage. '
        'Fixed-bin reliability and ECE are diagnostic and bin-dependent. Flag n < 100 OR fatal < 5; retain empty groups with null rates.\n\n'
        f'Predeclared directional transfer gate passes in both years: **{assessment["both_years_passed"]}**. '
        'See `reports/tables/cstress_v1_transfer_gates.csv` and `docs/calibration_stress_v1_results.md` for score differences and interpretation. '
        'This is reused retrospective stress evidence: these years were previously inspected and scored in the original baseline. '
        'There is no fresh holdout, model replacement, threshold recommendation or claim of reliable transfer.\n')
    paths += [derived/'predictions.parquet', model_copy, assessment_path, card, *sorted(figures.glob('cstress_v1_*.png'))]
    for relative, expected in protocol['input_fingerprints'].items():
        if sha256(root/relative) != expected:
            raise ValueError(f'Frozen input changed during stress run: {relative}')
    manifest = {'status': 'scored_pending_independent_validation', 'created_utc': datetime.now(timezone.utc).isoformat(),
                'protocol_sha256': FROZEN_HASH, 'fitting_performed': False, 'scored_years': [2020,2021],
                'reused_retrospective_evaluation': True, 'original_baseline_max_probability_difference': max_difference,
                'input_fingerprints': {**protocol['input_fingerprints'], PROTOCOL: FROZEN_HASH,
                                       'src/road_to_safety/score_calibration_stress_v1.py': sha256(Path(__file__))},
                'artifacts': {str(p.relative_to(root)): sha256(p) for p in paths},
                'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
                                'scipy': scipy.__version__, 'duckdb': duckdb.__version__, 'matplotlib': matplotlib.__version__},
                'assessment': assessment}
    (derived/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve()), indent=2))


if __name__ == '__main__':
    main()
