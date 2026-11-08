"""Independent, fitting-free audit of the reused 2020–2021 calibration stress test."""
import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .validate_temporal_calibration_v1 import (
    FEATURES, KEYS, assert_values, bin_evidence, feature_quality, fingerprint,
    probability_metrics, require, score_logit, sigmoid,
)

METHODS = ['prevalence', 'unchanged', 'sigmoid']


def validate_population(frame):
    require(not frame.duplicated(KEYS).any(), 'Duplicate source key')
    require(frame.severity_eligible.all() and frame.is_fatal.isin([0,1]).all(), 'Invalid eligibility or labels')
    actual = frame.groupby(frame.C_YEAR.astype(int)).is_fatal.agg(['size','sum'])
    require(actual.to_dict('index') == {2020:{'size':79990,'sum':1602},2021:{'size':83590,'sum':1628}},
        'Unexpected stress population or source years')


def compare_metrics(row, y, p):
    y, p = np.asarray(y), np.asarray(p)
    names = ['observed_prevalence','mean_prediction','prediction_minus_observed',
        'observed_expected_ratio','log_loss','brier_score','average_precision','roc_auc']
    if len(y):
        expected = probability_metrics(y,p)
        expected['observed_prevalence'] = expected.pop('fatal_proportion')
        observed, predicted = float(y.mean()), float(p.mean())
        expected.update(nonfatal=len(y)-int(y.sum()), prediction_minus_observed=predicted-observed,
            observed_expected_ratio=observed/predicted if predicted else np.nan)
        assert_values(row,expected)
    else:
        assert_values(row, {'n':0,'fatal':0,'nonfatal':0})
        require(all(pd.isna(row[name]) for name in names), 'Empty group has defined metrics')
    require(bool(row['sparse_n_lt_100_or_fatal_lt_5']) == (len(y)<100 or y.sum()<5), 'Wrong sparse flag')


def group_masks(frame):
    quality = feature_quality(frame)
    unknown, other = quality['any_unknown_or_unavailable'], quality['any_other']
    masks = {'all': np.ones(len(frame), dtype=bool)}
    for name, values in [('has_unknown',quality['any_unknown']),('has_unavailable',quality['any_unavailable']),
            ('has_unknown_or_unavailable',unknown),('has_other',other),
            ('has_train_unobserved_level',frame.has_train_unobserved_level.to_numpy())]:
        for present in [False,True]:
            masks[f'{name}={present}'] = values == present
    for field in FEATURES:
        for status in ['stated','unknown','other','unavailable']:
            masks[f'{field}:{status}'] = quality[field] == status
    return masks


def transfer_assessment(annual):
    require(not annual.duplicated(['population','method']).any(), 'Duplicate transfer pair')
    require(set(zip(annual.population.astype(str),annual.method)) ==
        {(str(year),method) for year in [2020,2021] for method in METHODS}, 'Missing or extra transfer pair')
    loss = annual.pivot(index='population',columns='method',values='log_loss')
    brier = annual.pivot(index='population',columns='method',values='brier_score')
    favorable = ((loss.sigmoid-loss.unchanged < -1e-10) &
        (brier.sigmoid-brier.unchanged <= 1e-10)).all()
    return 'favorable_descriptive_transfer' if favorable else 'transfer_not_demonstrated'


def frozen_parameters(model, protocol):
    for key,value in protocol['frozen_model_parameters'].items():
        require(model[key]==value, f'Changed saved model parameter: {key}')
    for key,value in protocol['frozen_sigmoid_parameters'].items():
        require(model['calibrators']['sigmoid'][key]==value, f'Changed saved calibrator: {key}')
    require(protocol['selected_method']=='sigmoid', 'Changed selected development method')


def validate(root):
    root = Path(root)
    derived = root/'data/derived/calibration_stress_v1'
    tables = root/'reports/tables'
    protocol_path = root/'data/reference/calibration_stress_v1_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    manifest = json.loads((derived/'manifest.json').read_text())
    checks=[]
    def check(name, operation):
        try:
            operation()
            checks.append({'check':name,'status':'passed','error':''})
        except (ValueError,AssertionError,KeyError,TypeError,IndexError) as error:
            checks.append({'check':name,'status':'failed','error':str(error)})
    def hashes():
        require(fingerprint(protocol_path)=='a7c1732e8aa9348c264d8e5d118b7e93190a73604d600b405ec5ca5655eef54d', 'Changed frozen stress protocol')
        require(manifest['protocol_sha256']==fingerprint(protocol_path),'Producer protocol mismatch')
        for relative,digest in protocol['input_fingerprints'].items():
            require(fingerprint(root/relative)==digest,f'Changed original input: {relative}')
        for relative,status in protocol['upstream_status_required'].items():
            require(json.loads((root/relative).read_text())['status']==status,f'Unpassed upstream: {relative}')
        for key in ['input_fingerprints','artifacts']:
            for relative,digest in manifest[key].items():
                require(fingerprint(root/relative)==digest,f'Changed producer {key}: {relative}')
        require(protocol['evaluation_years']==[2020,2021] and protocol['features']==FEATURES,'Changed years/features')
    check('frozen_protocol_all_original_assets_upstream_receipts_and_producer_hashes',hashes)
    model = json.loads((root/protocol['saved_model_path']).read_text())
    check('exact_saved_development_model_and_selected_sigmoid_parameters',lambda:frozen_parameters(model,protocol))
    selection = json.loads((root/protocol['saved_selection_path']).read_text())
    check('sigmoid_was_development_selected_not_stress_selected',lambda:require(selection['selected_method']=='sigmoid','Changed saved selection'))
    connection=duckdb.connect()
    source=connection.execute('SELECT '+','.join(KEYS+FEATURES+['is_fatal','severity_eligible']+
        [f+'_conflict' for f in FEATURES])+' FROM read_parquet(?) WHERE CAST(C_YEAR AS INTEGER) IN (2020,2021)',
        [str(root/'data/derived/collisions.parquet')]).df()
    check('exact_2020_2021_source_population_unique_eligible_binary',lambda:validate_population(source))
    check('all_features_supported_nonblank_nonconflicting_categorical_states',lambda:require(
        all(source[f].isin(protocol['categorical_domains'][f]).all() for f in FEATURES)
        and not source[[f+'_conflict' for f in FEATURES]].any().any(),'Invalid feature values/conflicts'))
    prediction=connection.read_parquet(str(derived/'predictions.parquet')).df()
    joined=source.merge(prediction,on=KEYS,how='outer',validate='one_to_one',indicator=True,suffixes=('_source',''))
    check('every_source_key_exactly_once_with_unchanged_target',lambda:require(
        (joined._merge=='both').all() and joined.is_fatal.eq(joined.is_fatal_source).all(), 'Prediction source coverage or label mismatch'))
    # If producer retains feature columns, independently verify and use the source versions.
    for field in FEATURES:
        if field+'_source' in joined:
            check(f'{field}_unchanged_in_prediction',lambda f=field:require(joined[f].eq(joined[f+'_source']).all(),'Changed source category'))
            joined[field]=joined[field+'_source']
    z=score_logit(joined,model)
    expected_scores={'unchanged':sigmoid(z),'sigmoid':sigmoid(
        protocol['frozen_sigmoid_parameters']['slope']*z+protocol['frozen_sigmoid_parameters']['intercept']),
        'prevalence':np.full(len(joined),model['train_prevalence'])}
    check('saved_coefficients_reconstruct_all_raw_logits',lambda:require(
        np.allclose(joined.raw_logit,z,atol=1e-12,rtol=1e-10),'Changed raw logits'))
    for method in METHODS:
        check(f'{method}_finite_exact_immutable_score_reconstruction',lambda m=method:require(
            np.isfinite(joined['p_'+m]).all() and joined['p_'+m].between(0,1).all() and
            np.allclose(joined['p_'+m],expected_scores[m],atol=1e-13,rtol=1e-11),'Changed probability'))
    old=connection.execute('SELECT * FROM read_parquet(?) WHERE CAST(C_YEAR AS INTEGER) IN (2020,2021)',
        [str(root/'data/derived/severity_predictions.parquet')]).df()
    old_join=joined.merge(old[KEYS+['p_logistic','p_baseline','is_fatal','split']],on=KEYS,how='outer',validate='one_to_one',suffixes=('','_old'),indicator='old_merge')
    check('unchanged_and_prevalence_match_original_severity_test_scores',lambda:require(
        old_join.old_merge.eq('both').all() and old_join.split.eq('test').all() and
        old_join.is_fatal.eq(old_join.is_fatal_old).all() and
        np.allclose(old_join.p_unchanged,old_join.p_logistic,atol=1e-13,rtol=1e-11) and
        np.allclose(old_join.p_prevalence,old_join.p_baseline,atol=1e-14,rtol=0),'Original baseline changed or incompatible scores'))
    check('no_threshold_output_or_new_candidate',lambda:require(
        {col for col in prediction if col.startswith('p_')}=={'p_'+method for method in METHODS}
        and not any('threshold' in col or col.startswith('predicted_') for col in prediction),'Unexpected model or threshold output'))
    metrics=pd.read_csv(tables/'cstress_v1_metrics.csv',dtype={'population':str})
    bins=pd.read_csv(tables/'cstress_v1_reliability.csv',dtype={'population':str})
    ece=pd.read_csv(tables/'cstress_v1_ece.csv',dtype={'population':str})
    masks=group_masks(joined)
    populations={'2020':joined.C_YEAR.astype(int).eq(2020).to_numpy(),
        '2021':joined.C_YEAR.astype(int).eq(2021).to_numpy(),'pooled':np.ones(len(joined),dtype=bool)}
    def score_metrics():
        expected={(population,group,method) for population in populations for group in masks for method in METHODS}
        require(not metrics.duplicated(['population','group','method']).any() and
            set(zip(metrics.population,metrics.group,metrics.method))==expected,'Missing/extra quality metric group')
        y=joined.is_fatal.to_numpy()
        for row in metrics.to_dict('records'):
            mask=populations[row['population']] & masks[row['group']]
            compare_metrics(row,y[mask],expected_scores[row['method']][mask])
    check('independent_annual_pooled_all_quality_metrics_including_empty_groups',score_metrics)
    def reliability_check():
        expected={(population,method,scheme,index) for population in populations for method in METHODS
            for scheme,edges in protocol['reliability']['schemes'].items() for index in range(len(edges)-1)}
        require(not bins.duplicated(['population','method','scheme','bin']).any() and
            set(zip(bins.population,bins.method,bins.scheme,bins.bin))==expected,'Missing/extra reliability bin')
        expected_ece={(population,method,scheme) for population in populations for method in METHODS for scheme in protocol['reliability']['schemes']}
        require(not ece.duplicated(['population','method','scheme']).any() and set(zip(ece.population,ece.method,ece.scheme))==expected_ece,'Missing/extra ECE row')
        for population,mask in populations.items():
            y=joined.is_fatal.to_numpy()[mask]
            for method in METHODS:
                p=expected_scores[method][mask]
                for scheme,edges in protocol['reliability']['schemes'].items():
                    expected=bin_evidence(y,p,edges)
                    actual=bins[(bins.population==population)&(bins.method==method)&(bins.scheme==scheme)].sort_values('bin')
                    for row,values in zip(actual.to_dict('records'),expected,strict=True):
                        sparse=values.pop('sparse')
                        assert_values(row,values)
                        require(bool(row['sparse_n_lt_100_or_fatal_lt_5'])==sparse,'Wrong bin sparse flag')
                    expected_error=sum(row['n']/len(y)*abs(row['observed_fraction']-row['mean_prediction']) for row in expected if row['n'])
                    actual_error=ece[(ece.population==population)&(ece.method==method)&(ece.scheme==scheme)].iloc[0]
                    assert_values(actual_error,{'n':len(y),'ece':expected_error})
    check('independent_fixed_bins_boundary_counts_empty_bins_sparse_flags_and_ECE',reliability_check)
    def macro_check():
        macro=pd.read_csv(tables/'cstress_v1_macro.csv')
        require(len(macro)==3 and set(macro.method)==set(METHODS),'Wrong macro method coverage')
        annual=metrics[metrics.population.isin(['2020','2021']) & metrics.group.eq('all')]
        for method in METHODS:
            part=annual[annual.method==method]
            row=macro[macro.method==method].iloc[0]
            for name in ['log_loss','brier_score','average_precision','roc_auc','mean_prediction','observed_prevalence','prediction_minus_observed','observed_expected_ratio']:
                assert_values(row,{name+'_mean':part[name].mean(),name+'_std':part[name].std(ddof=1)})
    check('equal_annual_weight_macro_means_and_sample_SD',macro_check)
    def support_check():
        support=pd.read_csv(tables/'cstress_v1_level_support.csv',dtype={'population':str,'code':str})
        old_support=pd.read_csv(tables/'tcal_v1_level_support.csv',dtype={'code':str})
        old_support=old_support[old_support.eval_year.eq(2019)].set_index(['feature','code'])
        expected={(population,feature,code) for population in populations for feature in FEATURES
            for code in protocol['categorical_domains'][feature]}
        require(not support.duplicated(['population','feature','code']).any() and
            set(zip(support.population,support.feature,support.code))==expected,'Dictionary support missing/duplicated')
        unseen=np.zeros(len(joined),dtype=bool)
        coefficients={(term['feature'],term['code']):coefficient for term,coefficient in
            zip(model['encoded_features'],model['coefficients'],strict=True)}
        for (field,code),original in old_support.iterrows():
            if original.train_n==0:
                unseen |= joined[field].eq(code).to_numpy()
                require(abs(coefficients.get((field,code),0.))<1e-12,'Training-unseen level has nonzero coefficient')
        require(np.array_equal(joined.has_train_unobserved_level,unseen),'Wrong training support flag')
        counts={(population,field):joined.loc[mask].groupby(field).is_fatal.agg(['size','sum'])
            for population,mask in populations.items() for field in FEATURES}
        for row in support.to_dict('records'):
            field,code=row['feature'],row['code']
            original=old_support.loc[(field,code)]
            for col,value in original.items():
                if pd.api.types.is_bool(value):
                    require(bool(row[col])==bool(value),'Wrong archived support bool')
                elif isinstance(value,(float,int,np.number)):
                    assert_values(row,{col:float(value)})
                else:
                    require(row[col]==value,'Changed archived support field')
            values=counts[(row['population'],field)]
            value=values.loc[code] if code in values.index else {'size':0,'sum':0}
            n,fatal=int(value['size']),int(value['sum'])
            assert_values(row,{'stress_n':n,'stress_fatal':fatal,'stress_nonfatal':n-fatal,
                'stress_prevalence':fatal/n if n else np.nan})
            require(bool(row['stress_sparse_n_lt_100_or_fatal_lt_5'])==(n<100 or fatal<5),'Wrong support sparse flag')
        quality=feature_quality(joined)
        for flag,name in [('has_unknown','any_unknown'),('has_unavailable','any_unavailable'),
            ('has_other','any_other'),('has_unknown_or_unavailable','any_unknown_or_unavailable')]:
            require(np.array_equal(joined[flag],quality[name]),f'Wrong pure quality flag: {flag}')
    check('every_dictionary_level_stress_support_training_neutrality_and_separate_quality_flags',support_check)
    def membership_check():
        output=pd.read_csv(tables/'cstress_v1_membership.csv',dtype={'population':str,'source_year':str})
        expected={}
        for population,mask in populations.items():
            for key,values in joined.loc[mask].groupby(['source_id','C_YEAR']).is_fatal.agg(['size','sum']).iterrows():
                expected[(population,*key)]={'n':int(values['size']),'fatal':int(values['sum']),
                    'nonfatal':int(values['size']-values['sum'])}
        require(not output.duplicated(['population','source_id','source_year']).any() and
            set(zip(output.population,output.source_id,output.source_year))==set(expected),'Wrong membership coverage')
        for row in output.to_dict('records'):
            assert_values(row,expected[(row['population'],row['source_id'],row['source_year'])])
    check('annual_pooled_source_release_membership_and_target_counts',membership_check)
    def transfer_check():
        annual=metrics[metrics.group.eq('all') & metrics.population.isin(['2020','2021'])]
        expected=transfer_assessment(annual)
        assessment=json.loads((derived/'assessment.json').read_text())
        require(assessment['assessment']==expected,'Wrong fixed annual transfer assessment')
        require(assessment['both_years_passed']==(expected=='favorable_descriptive_transfer'),'Wrong both-years gate')
        require(manifest['assessment']==assessment,'Manifest transfer assessment mismatch')
        output=pd.read_csv(tables/'cstress_v1_transfer_gates.csv',dtype={'population':str})
        require(len(output)==2 and set(output.population)=={'2020','2021'} and not output.population.duplicated().any(),'Wrong annual gate coverage')
        for row in output.to_dict('records'):
            values=annual[annual.population.eq(row['population'])].set_index('method')
            base,cal=values.loc['unchanged'],values.loc['sigmoid']
            ll,bs=float(cal.log_loss-base.log_loss),float(cal.brier_score-base.brier_score)
            gap=float(abs(cal.prediction_minus_observed)-abs(base.prediction_minus_observed))
            assert_values(row,{'log_loss_difference':ll,'brier_difference':bs,'absolute_aggregate_gap_difference':gap})
            require(bool(row['log_loss_improved'])==(ll < -1e-10) and bool(row['brier_not_worse'])==(bs<=1e-10)
                and bool(row['year_gate_passed'])==(ll < -1e-10 and bs<=1e-10),'Wrong annual gate')
        require(manifest['fitting_performed'] is False and manifest['reused_retrospective_evaluation'] is True
            and manifest['scored_years']==[2020,2021],'Changed fitting/evidence provenance')
    check('predeclared_both_annual_transfer_gates_no_new_selection_or_replacement',transfer_check)
    def rank_check():
        for population,mask in populations.items():
            y=joined.is_fatal.to_numpy()[mask]
            unchanged=probability_metrics(y,expected_scores['unchanged'][mask])
            calibrated=probability_metrics(y,expected_scores['sigmoid'][mask])
            require(np.isclose(unchanged['roc_auc'],calibrated['roc_auc'],rtol=0,atol=1e-10)
                and np.isclose(unchanged['average_precision'],calibrated['average_precision'],rtol=0,atol=1e-10),
                'Positive sigmoid unexpectedly changes ranking metrics')
    check('positive_saved_sigmoid_preserves_annual_and_pooled_ranking',rank_check)
    def differences_check():
        output=pd.read_csv(tables/'cstress_v1_differences.csv',dtype={'population':str})
        expected={(population,method) for population in [*populations,'macro'] for method in ['sigmoid','prevalence']}
        require(not output.duplicated(['population','method']).any() and set(zip(output.population,output.method))==expected,
            'Missing/duplicate score difference row')
        macro=pd.read_csv(tables/'cstress_v1_macro.csv').set_index('method')
        names=['log_loss','brier_score','average_precision','roc_auc','mean_prediction','observed_prevalence','prediction_minus_observed','observed_expected_ratio']
        for row in output.to_dict('records'):
            if row['population']=='macro':
                base=macro.loc['unchanged']
                selected=macro.loc[row['method']]
                values={name+'_difference':float(selected[name+'_mean']-base[name+'_mean']) for name in names}
                denominator=float(base.log_loss_mean)
            else:
                group=metrics[metrics.population.eq(row['population']) & metrics.group.eq('all')].set_index('method')
                base,selected=group.loc['unchanged'],group.loc[row['method']]
                values={name+'_difference':float(selected[name]-base[name]) for name in names}
                denominator=float(base.log_loss)
            values['relative_log_loss_difference']=values['log_loss_difference']/denominator
            assert_values(row,values)
    check('signed_annual_pooled_macro_differences_and_relative_log_loss',differences_check)
    def code_review():
        import ast
        code=(root/'src/road_to_safety/score_calibration_stress_v1.py').read_text()
        parsed=ast.parse(code)
        prohibited={'fit','fit_transform','minimize','minimize_scalar','GridSearchCV','RandomizedSearchCV','LogisticRegression'}
        for node in ast.walk(parsed):
            if isinstance(node,ast.Call):
                name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                require(name not in prohibited,f'Forbidden fitting/search API: {name}')
        require((derived/'archived_model_2019.json').read_bytes()==(root/protocol['saved_model_path']).read_bytes(),
            'Archived model differs from original')
    check('producer_code_has_no_fit_optimization_search_API_and_archived_model_exact',code_review)
    check('all_frozen_original_inputs_still_unchanged_after_independent_audit',hashes)
    connection.close()
    output_path=tables/'cstress_v1_validation_checks.csv'
    pd.DataFrame(checks).to_csv(output_path,index=False)
    failures=[row for row in checks if row['status']!='passed']
    paths=([protocol_path,root/'data/derived/collisions.parquet',derived/'manifest.json',
        Path(__file__),root/'src/road_to_safety/validate_temporal_calibration_v1.py',
        root/'tests/test_validate_calibration_stress_v1.py']+sorted(derived.glob('*.parquet'))+
        [derived/'archived_model_2019.json',derived/'assessment.json']+sorted(tables.glob('cstress_v1_*.csv')))
    result={'status':'failed' if failures else 'passed','failures':failures,
        'checks_passed':[row['check'] for row in checks if row['status']=='passed'],
        'method':'Independent immutable-source joins, numpy coefficient/logit reconstruction and stable sigmoid; tie-aware numpy ranking, metrics, fixed reliability bins and ECE, dictionary support, exact original baseline comparisons and frozen annual transfer gates; no fitting.',
        'evidence_status':protocol['evidence_status'],
        'input_fingerprints':{str(path.relative_to(root)):fingerprint(path) for path in paths},
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
