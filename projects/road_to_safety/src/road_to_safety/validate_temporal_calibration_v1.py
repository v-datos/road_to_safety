"""Independently reconcile temporal calibration v1 without fitting estimators."""
import argparse
import hashlib
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

FEATURES = ['C_MNTH', 'C_WDAY', 'C_HOUR', 'C_RCFG', 'C_WTHR', 'C_RSUR', 'C_RALN', 'C_TRAF']
KEYS = ['source_id', 'C_YEAR', 'C_CASE']


def fingerprint(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fold_partition(years, evaluation_year):
    require(evaluation_year in range(2014, 2020), 'Evaluation year outside frozen folds')
    years = np.asarray(years, dtype=int)
    return np.where((years >= 1999) & (years <= evaluation_year - 3), 'train',
        np.where((years >= evaluation_year - 2) & (years <= evaluation_year - 1),
        'calibration', np.where(years == evaluation_year, 'evaluation', 'excluded')))


def sigmoid(score):
    score = np.asarray(score, dtype=float)
    require(np.isfinite(score).all(), 'Nonfinite log odds')
    result = np.empty_like(score)
    nonnegative = score >= 0
    result[nonnegative] = 1 / (1 + np.exp(-score[nonnegative]))
    exponential = np.exp(score[~nonnegative])
    result[~nonnegative] = exponential / (1 + exponential)
    return result


def score_logit(frame, model):
    require(model['features'] == FEATURES, 'Forbidden feature in base model')
    score = np.full(len(frame), float(model['intercept']))
    terms = {field: {} for field in FEATURES}
    for term, coefficient in zip(model['encoded_features'], model['coefficients'], strict=True):
        require(term['feature'] in FEATURES, 'Forbidden encoded feature')
        terms[term['feature']][term['code']] = float(coefficient)
    for field in FEATURES:
        score += frame[field].astype(object).map(terms[field]).fillna(0).to_numpy()
    require(np.isfinite(score).all(), 'Nonfinite reconstructed logits')
    return score


def probability_metrics(y, probability):
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    require(len(y) > 0 and len(y) == len(probability), 'Invalid metric lengths')
    require(np.isin(y, [0, 1]).all(), 'Nonbinary outcome')
    require(np.isfinite(probability).all() and ((probability >= 0) & (probability <= 1)).all(), 'Invalid probability')
    n, fatal = len(y), int(y.sum())
    clipped = np.clip(probability, np.finfo(float).eps, 1 - np.finfo(float).eps)
    order = np.argsort(-probability, kind='stable')
    ranked_y, ranked_p = y[order], probability[order]
    end = np.r_[np.flatnonzero(np.diff(ranked_p)), n - 1]
    tp = np.cumsum(ranked_y)[end]
    fp = end + 1 - tp
    auc = float(np.trapezoid(np.r_[0, tp] / fatal, np.r_[0, fp] / (n - fatal))) if 0 < fatal < n else np.nan
    ap = float(np.sum(np.diff(np.r_[0, tp]) / fatal * tp / (end + 1))) if 0 < fatal < n else np.nan
    return {'n': n, 'fatal': fatal, 'fatal_proportion': fatal / n,
        'mean_prediction': float(probability.mean()),
        'log_loss': float(-np.mean(y * np.log(clipped) + (1-y) * np.log1p(-clipped))),
        'brier_score': float(np.mean((probability-y)**2)), 'roc_auc': auc, 'average_precision': ap}


def assert_values(actual, expected, atol=1e-10):
    for key, value in expected.items():
        found = float(actual[key])
        if np.isnan(value) and np.isnan(found):
            continue
        require(np.isfinite(found) and np.isclose(found, value, atol=atol, rtol=atol), f'{key}: {found} != {value}')


def calibration_gradient(y, score, slope, intercept):
    residual = sigmoid(slope * np.asarray(score) + intercept) - np.asarray(y)
    return np.array([residual.mean(), np.mean(residual * score)])


def independent_selection(annual):
    """Apply the frozen gate to paired annual evaluation scores only."""
    tolerance = 1e-10
    expected = {(year, method) for year in range(2014,2020)
        for method in ['prevalence','unchanged','intercept_only','sigmoid']}
    require(not annual.duplicated(['evaluation_year','method']).any(), 'Duplicate selection pair')
    require(set(zip(annual.evaluation_year,annual.method)) == expected, 'Missing selection year/method pair')
    loss = annual.pivot(index='evaluation_year',columns='method',values='log_loss')
    brier = annual.pivot(index='evaluation_year',columns='method',values='brier_score')
    means = loss.mean()
    eligible = [method for method in ['intercept_only','sigmoid'] if
        means['unchanged']-means[method] > tolerance and
        ((loss['unchanged']-loss[method]) > tolerance).sum() >= 4 and
        brier[method].mean() <= brier['unchanged'].mean()+tolerance]
    if not eligible:
        return 'unchanged'
    best = min(means[method] for method in eligible)
    return next(method for method in ['intercept_only','sigmoid']
        if method in eligible and means[method] <= best+tolerance)


def training_gradient(frame, model, strength=1.):
    residual = sigmoid(score_logit(frame,model)) - frame.is_fatal.to_numpy()
    gradients = [abs(float(residual.mean()))]
    grouped = {feature:pd.Series(residual).groupby(frame[feature].to_numpy()).sum()
        for feature in FEATURES}
    for term, coefficient in zip(model['encoded_features'],model['coefficients'],strict=True):
        total = float(grouped[term['feature']].get(term['code'],0.))
        gradients.append(abs((total+float(coefficient)/strength)/len(frame)))
    return max(gradients)


def feature_quality(frame):
    result = {}
    for feature in FEATURES:
        values = frame[feature]
        result[feature] = np.where(values.isin(['U','UU']),'unknown',
            np.where(values.isin(['X','XX']),'unavailable',
            np.where(values.isin(['Q','QQ']),'other','stated')))
    result['any_unknown_or_unavailable'] = frame[FEATURES].isin(['U','UU','X','XX']).any(axis=1).to_numpy()
    result['any_other'] = frame[FEATURES].isin(['Q','QQ']).any(axis=1).to_numpy()
    result['any_unknown'] = frame[FEATURES].isin(['U','UU']).any(axis=1).to_numpy()
    result['any_unavailable'] = frame[FEATURES].isin(['X','XX']).any(axis=1).to_numpy()
    return result


def bin_evidence(y, probability, edges):
    y, probability, edges = np.asarray(y), np.asarray(probability), np.asarray(edges)
    bins = np.clip(np.searchsorted(edges,probability,side='right')-1,0,len(edges)-2)
    result=[]
    for index in range(len(edges)-1):
        mask=bins==index
        n,fatal=int(mask.sum()),int(y[mask].sum())
        result.append({'bin':index,'left':edges[index],'right':edges[index+1],
            'n':n,'fatal':fatal,'mean_prediction':float(probability[mask].mean()) if n else np.nan,
            'observed_fraction':float(y[mask].mean()) if n else np.nan,
            'sparse':n<100 or fatal<5})
    return result


def validate(root):
    root = Path(root)
    derived = root/'data/derived/temporal_calibration_v1'
    tables = root/'reports/tables'
    protocol_path = root/'data/reference/temporal_calibration_v1_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    manifest = json.loads((derived/'manifest.json').read_text())
    checks=[]
    def check(name, operation):
        try:
            operation()
            checks.append({'check':name,'status':'passed','error':''})
        except (ValueError, AssertionError, KeyError, TypeError, IndexError) as error:
            checks.append({'check':name,'status':'failed','error':str(error)})
    def hashes():
        require(fingerprint(protocol_path)=='756f5d52e79da6f6b63a5bfa576e1b814b6749165d3881a1aa34c76fc424ec73', 'Frozen protocol changed')
        require(manifest['protocol_sha256']==fingerprint(protocol_path),'Manifest protocol binding changed')
        for relative,digest in protocol['input_fingerprints'].items():
            require(fingerprint(root/relative)==digest,f'Frozen input changed: {relative}')
        for relative,status in protocol['upstream_status_required'].items():
            require(json.loads((root/relative).read_text())['status']==status,f'Upstream receipt not passed: {relative}')
        for key in ['input_fingerprints','artifacts']:
            for relative,digest in manifest[key].items():
                require(fingerprint(root/relative)==digest,f'Manifest {key} changed: {relative}')
        require(manifest['evaluated_years']==list(range(2014,2020)), 'Changed evaluation years')
        require(manifest['excluded_from_all_fitting_calibration_scoring']==[2020,2021], 'Late-year exclusion changed')
        require(protocol['features']==FEATURES,'Changed frozen feature allowlist')
    check('frozen_protocol_inputs_original_baseline_and_output_fingerprints',hashes)
    connection=duckdb.connect()
    events=connection.execute('SELECT '+','.join(KEYS+FEATURES+['is_fatal','severity_eligible'])+
        ' FROM read_parquet(?) WHERE CAST(C_YEAR AS INTEGER) BETWEEN 1999 AND 2019',
        [str(root/'data/derived/collisions.parquet')]).df()
    for feature in FEATURES:
        events[feature]=events[feature].astype('category')
    years=events.C_YEAR.astype(int).to_numpy()
    check('source_population_unique_eligible_binary_and_supported_domains',lambda: require(
        not events.duplicated(KEYS).any() and events.severity_eligible.all() and events.is_fatal.isin([0,1]).all()
        and all(events[f].isin(protocol['categorical_domains'][f]).all() for f in FEATURES),
        'Invalid source identity, target, eligibility or category'))
    metrics=pd.read_csv(tables/'tcal_v1_metrics.csv')
    bins=pd.read_csv(tables/'tcal_v1_reliability.csv')
    support=pd.read_csv(tables/'tcal_v1_level_support.csv',dtype={'code':str})
    membership=pd.read_csv(tables/'tcal_v1_membership.csv',dtype={'source_year':str})
    check('exact_six_fold_files_and_table_fold_markers',lambda: require(
        set(path.name for path in derived.glob('model_*.json'))=={f'model_{t}.json' for t in range(2014,2020)}
        and set(path.name for path in derived.glob('predictions_*.parquet'))=={f'predictions_{t}.parquet' for t in range(2014,2020)}
        and all(set(frame.eval_year)==set(range(2014,2020)) for frame in [metrics,bins,support,membership]),
        'Missing/extra fold file or table year'))
    models={}
    pooled=[]
    metric_alias={'fatal_proportion':'observed_prevalence'}
    def compare_metrics(row, y, p):
        if len(y)==0:
            assert_values(row,{'n':0,'fatal':0})
            require(all(pd.isna(row[k]) for k in ['observed_prevalence','mean_prediction',
                'prediction_minus_observed','observed_expected_ratio','log_loss','brier_score','average_precision','roc_auc']),
                'Empty group must have null metrics')
        else:
            expected=probability_metrics(y,p)
            expected={metric_alias.get(k,k):v for k,v in expected.items()}
            observed,predicted=float(np.mean(y)),float(np.mean(p))
            expected.update(prediction_minus_observed=predicted-observed,
                observed_expected_ratio=observed/predicted if predicted else np.nan)
            assert_values(row,expected)
        require(bool(row['sparse_n_lt_100_or_fatal_lt_5'])==(len(y)<100 or np.sum(y)<5),'Wrong sparse metric flag')
    for t in range(2014,2020):
        model=json.loads((derived/f'model_{t}.json').read_text())
        models[t]=model
        prediction=connection.read_parquet(str(derived/f'predictions_{t}.parquet')).df()
        assignments=fold_partition(years,t)
        selected=events.loc[np.isin(assignments,['calibration','evaluation'])]
        joined=selected.merge(prediction,on=KEYS,how='outer',validate='one_to_one',indicator=True,
            suffixes=('_source','')).reset_index(drop=True)
        def identity():
            require(not prediction.duplicated(KEYS).any(),'Duplicate fold prediction key')
            require((joined._merge=='both').all(),'Missing or extra calibration/evaluation source key')
            require(joined.is_fatal.eq(joined.is_fatal_source).all(),'Changed target')
            require(prediction.eval_year.eq(t).all(),'Wrong fold marker')
            expected=fold_partition(joined.C_YEAR,t)
            require(np.array_equal(joined.phase,expected),'Wrong phase or forbidden year')
            require(not joined.C_YEAR.astype(int).isin([2020,2021]).any(),'Late-year scoring')
            for phase in ['train','calibration','evaluation']:
                subset=events.loc[assignments==phase]
                assert_values(model['counts'][phase],{'n':len(subset),'fatal':subset.is_fatal.sum(),
                    'min_year':subset.C_YEAR.astype(int).min(),'max_year':subset.C_YEAR.astype(int).max()})
                actual=membership[(membership.eval_year==t)&(membership.phase==phase)]
                expected_counts=subset.groupby(['source_id','C_YEAR']).is_fatal.agg(['size','sum'])
                require(len(actual)==len(expected_counts) and not actual.duplicated(['source_id','source_year']).any(),'Missing/duplicate membership source/year')
                for row in actual.to_dict('records'):
                    value=expected_counts.loc[(row['source_id'],row['source_year'])]
                    assert_values(row,{'n':value['size'],'fatal':value['sum'],
                        'nonfatal':value['size']-value['sum'],'fatal_prevalence':value['sum']/value['size']})
        check(f'{t}_exact_source_keys_targets_chronology_and_membership',identity)
        def base_fit():
            require(model['eval_year']==t and model['protocol_sha256']==fingerprint(protocol_path),'Changed fold model protocol binding')
            require(model['features']==FEATURES,'Forbidden model feature')
            require(model['categories']==protocol['categorical_domains'],'Changed domain')
            require(model['references']==protocol['reference_levels'],'Changed reference')
            terms=[{'feature':feature,'code':code} for feature in FEATURES
                for code in protocol['categorical_domains'][feature] if code!=protocol['reference_levels'][feature]]
            require(model['encoded_features']==terms,'Encoded design differs from frozen design')
            require(model['converged'] and 0<model['iterations']<1000,'Base not converged')
            for parameter,value in protocol['base_logistic_regression'].items():
                if parameter not in ['sample_weight','resampling','hyperparameter_search','calibration_fit']:
                    require(model['hyperparameters'][parameter]==value,f'Changed {parameter}')
            train=events.loc[assignments=='train']
            require(training_gradient(train,model,protocol['base_logistic_regression']['C'])<1e-5,
                'Training-only L2 likelihood stationarity failed')
            prevalence=float(train.is_fatal.mean())
            assert_values(model,{'train_prevalence':prevalence})
            require(np.allclose(joined.p_prevalence,prevalence,rtol=0,atol=1e-14),'Baseline not training prevalence')
            raw=score_logit(joined,model)
            require(np.allclose(joined.raw_logit,raw,rtol=1e-10,atol=1e-12),'Coefficients do not reconstruct raw logits')
        check(f'{t}_frozen_training_only_base_parameters_stationarity_and_scores',base_fit)
        def calibrations():
            calibration=joined[joined.phase=='calibration']
            y,z=calibration.is_fatal.to_numpy(),calibration.raw_logit.to_numpy()
            for method in ['unchanged','intercept_only','sigmoid']:
                pars=model['calibrators'][method]
                a,b=float(pars['slope']),float(pars['intercept'])
                require(np.isfinite([a,b]).all() and a>=1e-6,'Nonfinite or nonmonotone calibration')
                if method=='unchanged':
                    require(a==1. and b==0. and pars['fit_n']==0,'Unchanged fitted calibration')
                else:
                    require(pars['converged'] and 0<=pars['iterations']<1000 and pars['fit_n']==len(y),'Calibration convergence or population mismatch')
                    eta=a*z+b
                    assert_values(pars,{'objective_mean_log_loss':float(np.mean(np.logaddexp(0,eta)-y*eta))})
                    gradient=calibration_gradient(y,z,a,b)
                    raw=np.array([gradient[0]]) if method=='intercept_only' else gradient[[1,0]]
                    require(np.allclose(raw,pars['raw_gradient'],rtol=1e-9,atol=1e-12),'Calibration raw gradient mismatch')
                    projected=raw.copy()
                    if method=='sigmoid' and a<=1e-6+1e-10:
                        projected[0]=min(projected[0],0.)
                    if method=='intercept_only':
                        require(a==1.,'Intercept-only changed slope')
                    maximum=float(np.abs(projected).max())
                    require(maximum<=1e-6,'Calibration two-year likelihood KKT failed')
                    assert_values(pars,{'max_abs_projected_gradient':maximum},atol=1e-9)
                expected=sigmoid(a*joined.raw_logit.to_numpy()+b)
                actual=joined['p_'+method].to_numpy()
                require(np.isfinite(actual).all() and ((actual>=0)&(actual<=1)).all(),'Invalid probability')
                require(np.allclose(actual,expected,rtol=1e-11,atol=1e-13),'Calibration scores do not reconstruct')
            require(not any('threshold' in column or column.startswith('predicted_at') for column in prediction),'Unexpected threshold result')
        check(f'{t}_two_year_calibration_likelihood_KKT_positive_slope_and_score_reconstruction',calibrations)
        def support_check():
            output=support[support.eval_year==t]
            require(len(output)==sum(len(v) for v in protocol['categorical_domains'].values()) and
                not output.duplicated(['feature','code']).any(),'Missing/duplicate dictionary support')
            level_counts={f:events.groupby([pd.Series(assignments,index=events.index),f],observed=True).is_fatal.agg(['size','sum']) for f in FEATURES}
            unseen=np.zeros(len(joined),dtype=bool)
            terms={(term['feature'],term['code']):coefficient for term,coefficient
                in zip(model['encoded_features'],model['coefficients'],strict=True)}
            for row in output.to_dict('records'):
                f,c=row['feature'],row['code']
                require(f in FEATURES and c in protocol['categorical_domains'][f],'Unsupported support level')
                require(bool(row['is_reference'])==(c==protocol['reference_levels'][f]),'Wrong reference support flag')
                for phase in ['train','calibration','evaluation']:
                    key=(phase,c)
                    counts=level_counts[f]
                    expected=counts.loc[key] if key in counts.index else {'size':0,'sum':0}
                    assert_values(row,{phase+'_n':expected['size'],phase+'_fatal':expected['sum'],
                        phase+'_nonfatal':expected['size']-expected['sum'],
                        phase+'_prevalence':expected['sum']/expected['size'] if expected['size'] else np.nan})
                absent=row['train_n']==0
                require(bool(row['train_unobserved'])==absent,'Wrong training support flag')
                if absent:
                    require(abs(terms.get((f,c),0.))<1e-12,'Nonzero unobserved coefficient')
                    unseen |= joined[f].eq(c).to_numpy()
            require(np.array_equal(joined.has_train_unobserved_level,unseen),'Wrong score support flag')
            quality=feature_quality(joined)
            unknown,other=quality['any_unknown_or_unavailable'],quality['any_other']
            require(np.array_equal(joined.has_unknown_or_unavailable,unknown) and np.array_equal(joined.has_other,other),'Wrong sentinel flags')
            require(np.array_equal(joined.has_unknown,quality['any_unknown']) and np.array_equal(joined.has_unavailable,quality['any_unavailable']),'Unknown/unavailable conflated')
            status=np.where(unknown,'contains_unknown_or_unavailable',np.where(other,'contains_other','complete_stated'))
            require(np.array_equal(joined.feature_status,status),'Wrong hierarchical quality status')
        check(f'{t}_dictionary_level_support_unobserved_neutrality_and_quality_flags',support_check)
        group_masks={}
        for phase in ['calibration','evaluation']:
            mask=joined.phase.eq(phase).to_numpy()
            group_masks[(phase,'all')]=mask
            for status in ['complete_stated','contains_unknown_or_unavailable','contains_other']:
                group_masks[(phase,status)]=mask & joined.feature_status.eq(status).to_numpy()
            for name in ['has_unknown_or_unavailable','has_other','has_train_unobserved_level']:
                for present in [False,True]:
                    group_masks[(phase,f'{name}={present}')]=mask & (joined[name].to_numpy()==present)
            if phase=='evaluation':
                for name in ['has_unknown','has_unavailable']:
                    for present in [False,True]:
                        group_masks[(phase,f'{name}={present}')]=mask & (joined[name].to_numpy()==present)
                for feature,classes in feature_quality(joined).items():
                    if feature not in FEATURES:
                        continue
                    for status in ['stated','unknown','other','unavailable']:
                        group_masks[(phase,f'{feature}:{status}')]=mask & (classes==status)
        def metrics_check():
            output=metrics[metrics.eval_year==t]
            expected={(phase,group,method) for phase,group in group_masks
                for method in ['prevalence','unchanged','intercept_only','sigmoid']}
            require(not output.duplicated(['phase','group','method']).any() and
                set(zip(output.phase,output.group,output.method))==expected,'Missing/extra metric group/method')
            for row in output.to_dict('records'):
                mask=group_masks[(row['phase'],row['group'])]
                compare_metrics(row,joined.is_fatal.to_numpy()[mask],joined['p_'+row['method']].to_numpy()[mask])
        check(f'{t}_all_annual_calibration_and_quality_metrics_independently_recomputed',metrics_check)
        def reliability_check():
            output=bins[bins.eval_year==t]
            require(not output.duplicated(['phase','method','scheme','bin']).any(),'Duplicate reliability row')
            expected_rows=2*4*sum(len(edges)-1 for edges in protocol['reliability']['schemes'].values())
            require(len(output)==expected_rows,'Missing reliability bins')
            for phase in ['calibration','evaluation']:
                part=joined[joined.phase==phase]
                for method in ['prevalence','unchanged','intercept_only','sigmoid']:
                    for scheme,edges in protocol['reliability']['schemes'].items():
                        actual=output[(output.phase==phase)&(output.method==method)&(output.scheme==scheme)].sort_values('bin')
                        expected=bin_evidence(part.is_fatal.to_numpy(),part['p_'+method].to_numpy(),edges)
                        require(len(actual)==len(expected),'Missing fixed scheme')
                        for row,evidence in zip(actual.to_dict('records'),expected,strict=True):
                            sparse=evidence.pop('sparse')
                            assert_values(row,evidence)
                            require(bool(row['sparse_n_lt_100_or_fatal_lt_5'])==sparse,'Wrong sparse bin flag')
        check(f'{t}_both_fixed_reliability_schemes_all_bins_and_denominators',reliability_check)
        pooled.append(joined.loc[joined.phase=='evaluation',KEYS+['is_fatal']+
            ['p_'+method for method in ['prevalence','unchanged','intercept_only','sigmoid']]].copy())
        del prediction,joined
    pooled=pd.concat(pooled,ignore_index=True)
    check('evaluation_each_collision_exactly_once_no_late_years',lambda: require(
        not pooled.duplicated(KEYS).any() and pooled.C_YEAR.astype(int).between(2014,2019).all()
        and len(pooled)==int(((years>=2014)&(years<=2019)).sum()),'Pooled evaluation coverage changed'))
    def aggregations():
        annual=metrics[(metrics.phase=='evaluation')&(metrics.group=='all')]
        macro=pd.read_csv(tables/'tcal_v1_macro.csv')
        pooled_output=pd.read_csv(tables/'tcal_v1_pooled.csv')
        require(set(macro.method)=={'prevalence','unchanged','intercept_only','sigmoid'} and len(macro)==4,'Missing macro methods')
        require(set(pooled_output.method)==set(macro.method) and len(pooled_output)==4,'Missing pooled methods')
        names=['log_loss','brier_score','average_precision','roc_auc','mean_prediction','observed_prevalence','prediction_minus_observed','observed_expected_ratio']
        for method in macro.method:
            subset=annual[annual.method==method]
            require(len(subset)==6 and set(subset.eval_year)==set(range(2014,2020)),'Incomplete macro fold pairing')
            row=macro[macro.method==method].iloc[0]
            for name in names:
                assert_values(row,{name+'_mean':subset[name].mean(),name+'_std':subset[name].std(ddof=1)})
            compare_metrics(pooled_output[pooled_output.method==method].iloc[0],pooled.is_fatal.to_numpy(),pooled['p_'+method].to_numpy())
    check('macro_equal_year_means_sample_SD_and_collision_weighted_pooled_scores',aggregations)
    def ece_check():
        output=pd.read_csv(tables/'tcal_v1_ece.csv')
        keys=['eval_year','phase','method','scheme']
        expected_groups=set(map(tuple,bins[keys].drop_duplicates().to_numpy()))
        require(not output.duplicated(keys).any() and set(map(tuple,output[keys].to_numpy()))==expected_groups,'ECE group coverage changed')
        for row in output.to_dict('records'):
            values=bins
            for key in keys:
                values=values[values[key]==row[key]]
            total=int(values.n.sum())
            expected=float(((values.n/total)*(values.observed_fraction-values.mean_prediction).abs()).sum())
            assert_values(row,{'n':total,'ece':expected})
    check('independent_ECE_both_fixed_schemes_all_folds_and_phases',ece_check)
    def selection_check():
        annual=metrics[(metrics.phase=='evaluation')&(metrics.group=='all')].rename(columns={'eval_year':'evaluation_year'})
        expected=independent_selection(annual)
        selection=json.loads((derived/'selection.json').read_text())
        require(selection['selected_method']==expected and selection['selection_is_retrospective'],'Frozen recommendation mismatch')
        require(manifest['selection']==selection,'Manifest recommendation differs')
        output=pd.read_csv(tables/'tcal_v1_selection.csv')
        require(len(output)==3 and not output.method.duplicated().any(),'Candidate selection rows invalid')
        pivot=annual.pivot(index='evaluation_year',columns='method',values=['log_loss','brier_score'])
        for row in output.to_dict('records'):
            method=row['method']
            ll=pivot['log_loss'][method]-pivot['log_loss']['unchanged']
            bs=pivot['brier_score'][method]-pivot['brier_score']['unchanged']
            assert_values(row,{'macro_log_loss':pivot['log_loss'][method].mean(),
                'macro_brier_score':pivot['brier_score'][method].mean(),
                'macro_log_loss_difference':ll.mean(),'macro_brier_difference':bs.mean(),
                'years_log_loss_improved':int((ll < -1e-10).sum()),
                'raw_macro_log_loss_rank':1+sorted(['unchanged','intercept_only','sigmoid'],key=lambda candidate:pivot['log_loss'][candidate].mean()).index(method)})
            eligible=method=='unchanged' or (ll.mean() < -1e-10 and (ll < -1e-10).sum()>=4 and bs.mean()<=1e-10)
            require(bool(row['eligible'])==eligible,'Wrong selection eligibility')
        require(len(selection['candidates'])==3 and {row['method'] for row in selection['candidates']}==set(output.method),
            'Selection JSON candidate evidence missing')
        for row in selection['candidates']:
            saved=output[output.method==row['method']].iloc[0]
            assert_values(saved,{key:value for key,value in row.items() if key not in ['method','eligible']})
            require(bool(saved.eligible)==row['eligible'],'Selection JSON/CSV eligibility differs')
    check('six_year_paired_selection_guardrails_and_complexity_tie_rule',selection_check)
    def calibrator_table():
        output=pd.read_csv(tables/'tcal_v1_calibrators.csv')
        require(len(output)==18 and not output.duplicated(['eval_year','method']).any(),
            'Missing or duplicate calibrator summary')
        require(set(zip(output.eval_year,output.method))=={(year,method) for year in range(2014,2020)
            for method in ['unchanged','intercept_only','sigmoid']},'Wrong calibrator summary pairing')
        for row in output.to_dict('records'):
            expected=models[row['eval_year']]['calibrators'][row['method']]
            assert_values(row,{key:expected[key] for key in ['slope','intercept','iterations','fit_n']})
            require(bool(row['converged'])==expected['converged'],'Calibrator summary convergence differs')
            if row['method']!='unchanged':
                assert_values(row,{key:expected[key] for key in ['max_abs_projected_gradient','objective_mean_log_loss']})
                require(row['optimizer_message']==expected['optimizer_message'],'Calibrator optimizer message differs')
    check('calibrator_summary_matches_independently_verified_fold_parameters',calibrator_table)
    connection.close()
    pd.DataFrame(checks).to_csv(tables/'tcal_v1_validation_checks.csv',index=False)
    failures=[row for row in checks if row['status']!='passed']
    result={'status':'failed' if failures else 'passed','failures':failures,
        'checks_passed':[row['check'] for row in checks if row['status']=='passed'],
        'method':'Independent source-key joins, fixed chronology predicates, coefficient/logit reconstruction, training L2 stationarity, two-year calibration likelihood/KKT, numpy tie-aware ranking and bin counts; no estimator refits.',
        'input_fingerprints':{str(path.relative_to(root)):fingerprint(path) for path in
            [protocol_path,root/'data/derived/collisions.parquet',derived/'manifest.json']+
            sorted(derived.glob('model_*.json'))+sorted(derived.glob('predictions_*.parquet'))+
            sorted(tables.glob('tcal_v1_*.csv')) if path.name!='tcal_v1_validation_checks.csv'},
        'validator_sha256':fingerprint(Path(__file__))}
    (derived/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    result=validate(parser.parse_args().root)
    print(json.dumps(result,indent=2))
    if result['status']!='passed':
        raise SystemExit(1)
