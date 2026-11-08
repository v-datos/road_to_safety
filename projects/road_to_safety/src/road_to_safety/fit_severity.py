"""Fit the frozen chronological severity baseline and categorical logistic model."""
from __future__ import annotations

import argparse
import json
from itertools import chain
import platform
import warnings
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                            log_loss, precision_score, recall_score, f1_score, roc_auc_score, precision_recall_curve)
from sklearn.preprocessing import OneHotEncoder

from .explore import sha256, verify_inputs
from .analyze_conditions import label as condition_label


def validation_threshold(y, probability, target=0.8):
    """Maximum precision subject to recall target; ties choose higher threshold."""
    y, probability = np.asarray(y), np.asarray(probability)
    if not np.any(y == 1):
        raise ValueError('Threshold selection requires validation positives')
    order = np.argsort(-probability, kind='stable')
    scores, labels = probability[order], y[order]
    ends = np.r_[np.flatnonzero(scores[:-1] != scores[1:]), len(scores)-1]
    tp = np.cumsum(labels)[ends]
    eligible = tp / y.sum() >= target
    precision = tp / (ends + 1)
    candidates = np.flatnonzero(eligible)
    winner = candidates[np.argmax(precision[candidates])]
    return float(scores[ends[winner]])


def calibration(y, probability):
    bins = np.minimum((np.asarray(probability) * 10).astype(int), 9)
    rows = []
    for index in range(10):
        mask = bins == index
        count = int(mask.sum())
        rows.append({'bin': index, 'left': index/10, 'right': (index+1)/10,
                     'n': count, 'fatal': int(y[mask].sum()), 'mean_prediction': float(probability[mask].mean()) if count else None,
                     'observed_fraction': float(y[mask].mean()) if count else None})
    return rows


def evaluate(y, probability, threshold):
    y, probability = np.asarray(y), np.asarray(probability)
    predicted = probability >= threshold
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    bins = calibration(y, probability)
    return {'n': len(y), 'fatal': int(y.sum()), 'fatal_proportion': float(y.mean()),
            'mean_prediction': float(probability.mean()), 'mean_predicted_probability': float(probability.mean()),
            'observed_prevalence': float(y.mean()), 'threshold': threshold,
            'roc_auc': float(roc_auc_score(y, probability)) if len(np.unique(y)) == 2 else None,
            'average_precision': float(average_precision_score(y, probability)) if len(np.unique(y)) == 2 else None,
            'log_loss': float(log_loss(y, probability, labels=[0, 1])),
            'brier_score': float(brier_score_loss(y, probability)),
            'ece': sum(row['n']/len(y)*abs(row['mean_prediction']-row['observed_fraction'])
                       for row in bins if row['n']),
            'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
            'precision': float(precision_score(y, predicted, zero_division=0)),
            'recall': float(recall_score(y, predicted, zero_division=0)),
            'f1': float(f1_score(y, predicted, zero_division=0)),
            'sparse_n_lt_100_or_fatal_lt_5': len(y) < 100 or int(y.sum()) < 5}


def feature_label(field, code):
    if field in ('C_MNTH','C_WDAY','C_HOUR'):
        if code in ('U','UU'): return 'Unknown'
        if code in ('X','XX'): return 'Jurisdiction unavailable'
        if field == 'C_MNTH':
            return ['January','February','March','April','May','June','July','August',
                    'September','October','November','December'][int(code)-1]
        if field == 'C_WDAY':
            return ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][int(code)-1]
        return f'{int(code):02d}:00–{int(code):02d}:59'
    return condition_label(field, code)


def groups(frame):
    for split in ('train','validation','test'):
        mask = frame.split.eq(split).to_numpy()
        yield 'split', split, mask
    for year in sorted(frame.C_YEAR.unique()):
        yield 'year', str(year), frame.C_YEAR.eq(year).to_numpy()
    for split in ('train','validation','test'):
        for status in ('complete_stated','contains_unknown_or_unavailable','contains_other'):
            mask = (frame.split.eq(split) & frame.feature_status.eq(status)).to_numpy()
            if mask.any(): yield 'split_feature_status', f'{split}:{status}', mask


def run(root: Path):
    root = Path(root)
    verify_inputs(root)
    protocol_path = root/'data/reference/severity_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    if protocol.get('status') != 'frozen_before_model_fitting':
        raise ValueError('Severity protocol must be frozen before fitting')
    if sha256(protocol_path) != '7684a32e919a0b73f57ed55e7c1c796c4cb5a73c1a62cdeb76a1ff8889259491':
        raise ValueError('Unexpected protocol amendment')
    for relative, expected in protocol['input_sha256'].items():
        if sha256(root/relative) != expected: raise ValueError(f'Stale protocol input: {relative}')
    contract = json.loads((root/'data/reference/modeling_contract.json').read_text())
    features = contract['features']
    domains = contract['categorical_domains']
    references = protocol['reference_levels']
    if protocol['categorical_domains'] != domains:
        raise ValueError('Protocol categorical domains differ from contract')
    if protocol['features'] != features:
        raise ValueError('Protocol features differ from the validated contract')
    connection = duckdb.connect()
    frame = connection.execute('SELECT source_id,C_YEAR,C_CASE,is_fatal,severity_eligible,'+
        ','.join(features)+" FROM read_parquet(?) ORDER BY C_YEAR,source_id,C_CASE",
        [str(root/'data/derived/collisions.parquet')]).df()
    if not frame.severity_eligible.all() or not frame.is_fatal.isin([0,1]).all():
        raise ValueError('Unexpected ineligible targets')
    if frame.duplicated(['source_id','C_YEAR','C_CASE']).any():
        raise ValueError('Duplicate collision identity')
    for field in features:
        if not frame[field].isin(domains[field]).all():
            raise ValueError(f'Null or out-of-domain values in {field}')
    year = frame.C_YEAR.astype(int)
    frame['split'] = np.select([year.between(1999,2016), year.between(2017,2019),
                              year.between(2020,2021)], ['train','validation','test'], default='invalid')
    if frame.split.eq('invalid').any(): raise ValueError('Year outside frozen periods')
    unknown = frame[features].isin(['U','UU','X','XX']).any(axis=1)
    other = frame[features].isin(['Q','QQ']).any(axis=1)
    frame['feature_status'] = np.select([unknown, other],
        ['contains_unknown_or_unavailable','contains_other'], default='complete_stated')
    frame['has_unknown_or_unavailable'] = unknown
    frame['has_other'] = other
    train = frame.split.eq('train').to_numpy()
    validation = frame.split.eq('validation').to_numpy()
    target = frame.is_fatal.to_numpy(dtype=int)
    encoder = OneHotEncoder(categories=[domains[f] for f in features],
        drop=[references[f] for f in features], handle_unknown='error',
        sparse_output=True, dtype=np.float64)
    x_train = encoder.fit_transform(frame.loc[train,features])
    model = LogisticRegression(C=1.0, penalty='l2', solver='lbfgs', max_iter=1000,
                               tol=1e-7, class_weight=None, fit_intercept=True, random_state=2026)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always', ConvergenceWarning)
        model.fit(x_train, target[train])
    if any(issubclass(w.category, ConvergenceWarning) for w in captured) or model.n_iter_[0] >= 1000:
        raise ValueError('Logistic model did not converge')
    del x_train
    probability = np.empty(len(frame), dtype=float)
    probability[validation] = model.predict_proba(encoder.transform(frame.loc[validation,features]))[:,1]
    threshold = validation_threshold(target[validation], probability[validation])
    for start in range(0,len(frame),250000):
        stop = min(start+250000,len(frame))
        probability[start:stop] = model.predict_proba(encoder.transform(frame.iloc[start:stop][features]))[:,1]
    prevalence = float(target[train].mean())
    baseline = np.full(len(frame), prevalence)
    baseline_threshold = threshold
    tables = root/'reports/tables'
    figures = root/'reports/figures'
    derived = root/'data/derived'
    for folder in (tables,figures,derived): folder.mkdir(exist_ok=True,parents=True)
    metrics, calibration_rows = [], []
    def category_groups():
        for period in ('test','2020','2021'):
            period_mask = frame.split.eq('test') if period == 'test' else frame.C_YEAR.eq(period)
            for field in features:
                for code in domains[field]:
                    mask = (period_mask & frame[field].eq(code)).to_numpy()
                    if mask.any(): yield 'feature_category',f'{period}:{field}:{code}',mask
    for kind, group, mask in chain(groups(frame),category_groups()):
        for name, scores, selected in [('prevalence',baseline,baseline_threshold),('logistic',probability,threshold)]:
            for threshold_kind, cutoff in [('fixed_0_5',0.5),('validation_recall_80',selected)]:
                metrics.append({'group_kind':kind,'group':group,'model':name,
                                'threshold_kind':threshold_kind,**evaluate(target[mask],scores[mask],cutoff)})
            for row in calibration(target[mask],scores[mask]):
                calibration_rows.append({'group_kind':kind,'group':group,'model':name,**row})
    pd.DataFrame(metrics).to_csv(tables/'severity_metrics.csv',index=False)
    pd.DataFrame(calibration_rows).to_csv(tables/'severity_calibration.csv',index=False)
    coefficient_rows, level_rows, encoded_features = [], [], []
    coefficient_index = 0
    for field in features:
        for code in domains[field]:
            n_train = int((frame.loc[train,field] == code).sum())
            level_rows.append({'feature':field,'code':code,'label':feature_label(field,code),
                'train_count':n_train,'train_unobserved':n_train == 0,
                'validation_count':int((frame.loc[validation,field] == code).sum()),
                'test_count':int((frame.loc[frame.split.eq('test'),field] == code).sum()),
                'reference':code == references[field]})
            coefficient = 0.0
            if code != references[field]:
                coefficient = float(model.coef_[0,coefficient_index])
                encoded_features.append({'feature':field,'code':code})
                coefficient_index += 1
            coefficient_rows.append({'feature':field,'code':code,'label':feature_label(field,code),
                'reference_code':references[field], 'reference_label':feature_label(field,references[field]),
                'is_reference':code == references[field], 'train_count':n_train,
                'train_unobserved':n_train == 0,'coefficient':coefficient,
                'odds_ratio':float(np.exp(coefficient)),
                'interpretation':'not estimated: absent in training' if n_train == 0 else
                    ('reference' if code == references[field] else 'conditional association; regularized')})
    distribution_rows = []
    for field in features:
        for grouping in ('split','C_YEAR'):
            counts = frame.groupby([grouping,field],observed=True).size()
            totals = frame.groupby(grouping,observed=True).size()
            for group in totals.index:
                for code in domains[field]:
                    count = int(counts.get((group,code),0))
                    distribution_rows.append({'group_kind':'split' if grouping == 'split' else 'year',
                        'group':str(group),'feature':field,'code':code,'label':feature_label(field,code),
                        'value_class': 'unknown' if code in ('U','UU') else
                            'jurisdiction_unavailable' if code in ('X','XX') else
                            'other' if code in ('Q','QQ') else 'stated',
                        'n':count,'group_n':int(totals[group]),'share':count/int(totals[group])})
    pd.DataFrame(distribution_rows).to_csv(tables/'severity_feature_distributions.csv',index=False)
    pd.DataFrame(level_rows).to_csv(tables/'severity_training_levels.csv',index=False)
    pd.DataFrame(coefficient_rows).to_csv(tables/'severity_coefficients.csv',index=False)
    prediction_frame = frame[['source_id','C_YEAR','C_CASE','is_fatal','split','feature_status',
                             'has_unknown_or_unavailable','has_other']].copy()
    unsupported = {f:[r['code'] for r in level_rows if r['feature'] == f and r['train_unobserved']] for f in features}
    prediction_frame['has_train_unobserved_level'] = np.logical_or.reduce([frame[f].isin(unsupported[f]).to_numpy() for f in features])
    prediction_frame['p_baseline'] = baseline
    prediction_frame['p_logistic'] = probability
    prediction_frame['predicted_at_0_5'] = probability >= 0.5
    prediction_frame['predicted_at_validation_threshold'] = probability >= threshold
    connection.register('predictions',prediction_frame)
    connection.execute('COPY predictions TO ? (FORMAT PARQUET, COMPRESSION ZSTD)',
                       [str(derived/'severity_predictions.parquet')])
    model_record = {'features':features,'categories':domains,'references':references,
        'encoded_features':encoded_features,'coefficients':model.coef_[0].tolist(),
        'intercept':float(model.intercept_[0]),'train_prevalence':prevalence,
        'validation_threshold':threshold,'baseline_validation_threshold':baseline_threshold,
        'classes':model.classes_.tolist(),'iterations':int(model.n_iter_[0]),'converged':True,
        'hyperparameters':model.get_params(),'protocol_sha256':sha256(protocol_path)}
    (derived/'severity_model.json').write_text(json.dumps(model_record,indent=2)+'\n')
    plot_results(pd.DataFrame(metrics),pd.DataFrame(calibration_rows),coefficient_rows,figures,frame,probability,target)
    artifact_paths = [tables/name for name in ('severity_metrics.csv','severity_calibration.csv',
        'severity_coefficients.csv','severity_training_levels.csv','severity_feature_distributions.csv')]+[
        figures/name for name in ('severity_annual_performance.png','severity_calibration.png',
        'severity_precision_recall.png','severity_coefficients.png')]+[
        derived/'severity_predictions.parquet',derived/'severity_model.json']
    manifest = {'run_notes':['Initial execution interrupted before outputs/result inspection to complete reporting and reduce mask memory; same frozen model specification was retained.','Reliability figure includes all occupied bins; no refitting or probability correction.'], 'status':'fitted_pending_independent_validation',
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'input_fingerprints':{str(p.relative_to(root)):sha256(p) for p in [protocol_path,
            root/'data/reference/modeling_contract.json',root/'data/derived/collisions.parquet',
            root/'data/derived/prepared_validation.json',Path(__file__),root/'uv.lock']},
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__,
                       'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pd.__version__},
        'counts':frame.groupby('split').is_fatal.agg(['size','sum']).to_dict(orient='index'),
        'artifacts':{str(p.relative_to(root)):sha256(p) for p in artifact_paths},
        'converged':True,'iterations':int(model.n_iter_[0]),'train_prevalence':prevalence,
        'validation_threshold':threshold,'baseline_validation_threshold':baseline_threshold}
    (derived/'severity_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def plot_results(metrics,calibration_frame,coefficient_rows,figures,frame,probability,target):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import textwrap
    colors = {'logistic':'#1f77b4','prevalence':'#ff7f0e'}
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    annual = metrics[(metrics.group_kind == 'year') & (metrics.threshold_kind == 'fixed_0_5')]
    fig,axes = plt.subplots(1,2,figsize=(13,5.2),layout='constrained')
    for name,group in annual.groupby('model'):
        axes[0].plot(group.group.astype(int),group.log_loss,marker='o',markersize=3,label=name,color=colors[name])
        axes[1].plot(group.group.astype(int),group.mean_prediction*100,label=f'{name} predicted',color=colors[name])
    observed = annual[annual.model == 'logistic']
    axes[1].plot(observed.group.astype(int),observed.fatal_proportion*100,color='black',label='Observed')
    for ax in axes:
        ax.axvline(2016.5,color='gray',ls=':'); ax.axvline(2019.5,color='gray',ls=':')
        ax.set_xlabel('Source year'); ax.set_xticks([1999,2004,2009,2014,2019,2021]); ax.tick_params(axis='x',labelrotation=30); ax.legend(fontsize=8)
    axes[0].set_ylabel('Log loss (lower is better)'); axes[1].set_ylabel('Fatal fraction among recorded collisions (%)')
    fig.suptitle('Annual probability performance and fatal prevalence\nTrain 1999–2016 | validation 2017–2019 | test 2020–2021')
    fig.savefig(figures/'severity_annual_performance.png',dpi=160); plt.close(fig)
    fig,axes = plt.subplots(1,2,figsize=(12,5.4),layout='constrained')
    for ax,split in zip(axes,['validation','test']):
        for name in ('prevalence','logistic'):
            rows = calibration_frame[(calibration_frame.group_kind == 'split') &
                (calibration_frame.group == split) & (calibration_frame.model == name) & (calibration_frame.n>0)]
            ax.plot(rows.mean_prediction,rows.observed_fraction,marker='o',label=name,color=colors[name])
        ax.plot([0,1],[0,1],color='gray',ls=':'); ax.set_xlim(0,0.3); ax.set_ylim(0,0.3)
        ax.set_title(split.capitalize()+'\nFixed 0.1-wide bins; all occupied bins shown')
        for row in rows.itertuples():
            ax.annotate(f'n={row.n:,}',(row.mean_prediction,row.observed_fraction),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8)
        ax.set_xlabel('Mean predicted probability'); ax.set_ylabel('Observed fatal fraction'); ax.legend()
    fig.suptitle('Calibration among recorded fatal/injury collisions\nNo post-fit recalibration; bin counts label logistic points')
    fig.savefig(figures/'severity_calibration.png',dpi=160); plt.close(fig)
    fig,axes = plt.subplots(1,2,figsize=(12,5.4),layout='constrained')
    for ax,split in zip(axes,['validation','test']):
        mask = frame.split.eq(split).to_numpy()
        precision,recall,_ = precision_recall_curve(target[mask],probability[mask])
        ax.plot(recall,precision,label='Logistic',color=colors['logistic'])
        ax.axhline(target[mask].mean(),color=colors['prevalence'],ls=':',label='Prevalence baseline: constant-score AP')
        ax.set(xlabel='Recall',ylabel='Precision',title=split,xlim=(0,1),ylim=(0,0.3))
        ax.legend(fontsize=8)
    fig.suptitle('Precision–recall on validation and test\nPrecision axis 0–0.30; endpoint precision 1 lies above the display')
    fig.savefig(figures/'severity_precision_recall.png',dpi=160); plt.close(fig)
    coefficients = pd.DataFrame(coefficient_rows)
    rows = coefficients[~coefficients.is_reference & ~coefficients.train_unobserved].copy()
    rows['magnitude'] = rows.coefficient.abs()
    rows = rows.nlargest(18,'magnitude').sort_values('coefficient')
    fig,ax = plt.subplots(figsize=(13,10),layout='constrained')
    ax.barh([textwrap.fill(f'{r.feature}: {r.label}',38)+f'\n(training n={r.train_count:,})' for r in rows.itertuples()],rows.odds_ratio,color='#315a77')
    ax.axvline(1,color='black',ls=':'); ax.set_xlabel('Conditional odds ratio relative to field reference')
    ax.tick_params(axis='y',labelsize=8)
    ax.set_title('18 largest absolute regularized log-odds coefficients\nAssociations, not effects; small training groups can be unstable\nNamed references and all levels: severity_coefficients.csv',fontsize=11)
    fig.savefig(figures/'severity_coefficients.png',dpi=160); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    print(json.dumps(run(parser.parse_args().root.resolve()),indent=2))


if __name__ == '__main__': main()
