"""Versioned, frozen expanding-window calibration experiment; never scores 2020+."""
from __future__ import annotations
import argparse
import json
import platform
import warnings
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from .explore import sha256, verify_inputs

METHODS = ('unchanged', 'intercept_only', 'sigmoid')
PROTOCOL = 'data/reference/temporal_calibration_v1_protocol.json'
# Set only after the protocol owner freezes the specification, before any fit.
FROZEN_HASH = '756f5d52e79da6f6b63a5bfa576e1b814b6749165d3881a1aa34c76fc424ec73'


def fit_calibrator(z, y, method):
    z, y = np.asarray(z, dtype=float), np.asarray(y, dtype=float)
    if method == 'unchanged':
        return {'slope': 1.0, 'intercept': 0.0, 'converged': True, 'iterations': 0,
                'max_abs_gradient': 0.0, 'fit_n': 0}
    if len(np.unique(y)) != 2:
        raise ValueError('Calibration requires both classes')
    intercept_only = method == 'intercept_only'
    if method not in METHODS:
        raise ValueError('Unknown calibration method')
    def objective(parameters):
        eta = z + parameters[0] if intercept_only else parameters[0]*z + parameters[1]
        residual = expit(eta)-y
        gradient = np.array([residual.mean()]) if intercept_only else np.array([(residual*z).mean(), residual.mean()])
        return np.mean(np.logaddexp(0, eta)-y*eta), gradient
    result = minimize(objective, np.array([0.0]) if intercept_only else np.array([1.0, 0.0]),
                      method='L-BFGS-B', jac=True, bounds=[(None,None)] if intercept_only else [(1e-6,None),(None,None)],
                      options={'gtol':1e-9, 'maxiter':1000,'maxls':50,'ftol':1e-14})
    projected=np.array(result.jac,copy=True)
    if not intercept_only and result.x[0]<=1e-6+1e-10: projected[0]=min(projected[0],0.0)
    gradient = float(np.max(np.abs(projected)))
    if not result.success or not np.isfinite(result.x).all() or gradient > 1e-6 or result.nit>=1000 or not np.isfinite(result.fun):
        raise ValueError(f'Calibrator convergence failure: {result.message}; gradient={gradient}')
    slope, intercept = (1.0, float(result.x[0])) if intercept_only else tuple(map(float,result.x))
    if slope <= 0:
        raise ValueError('Non-positive sigmoid slope: ranking reversal not accepted')
    return {'slope':slope, 'intercept':intercept, 'converged':bool(result.success),
            'iterations':int(result.nit), 'max_abs_projected_gradient':gradient,'raw_gradient':result.jac.tolist(), 'fit_n':len(y),
            'optimizer_message':str(result.message), 'objective_mean_log_loss':float(result.fun)}


def probability_metrics(y, p):
    y, p = np.asarray(y,dtype=float), np.asarray(p,dtype=float)
    if not len(y):
        raise ValueError('Empty metric population')
    if not np.isfinite(p).all() or (p<0).any() or (p>1).any():
        raise ValueError('Invalid probability')
    clipped=np.clip(p,np.finfo(float).eps,1-np.finfo(float).eps)
    observed, predicted = float(y.mean()), float(p.mean())
    return {'n':len(y), 'fatal':int(y.sum()), 'observed_prevalence':observed,
            'mean_prediction':predicted, 'prediction_minus_observed':predicted-observed,
            'observed_expected_ratio':observed/predicted if predicted else None,
            'log_loss':float(np.mean(-y*np.log(clipped)-(1-y)*np.log1p(-clipped))),
            'brier_score':float(np.mean((y-p)**2)),
            'average_precision':float(average_precision_score(y,p)) if len(np.unique(y))==2 else None,
            'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
            'sparse_n_lt_100_or_fatal_lt_5':len(y)<100 or y.sum()<5}


def reliability(y, p, edges):
    indices=np.minimum(np.searchsorted(edges,p,side='right')-1,len(edges)-2)
    rows=[]
    for index,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
        mask=indices==index
        rows.append({'bin':index,'left':left,'right':right,'n':int(mask.sum()),'sparse_n_lt_100_or_fatal_lt_5':int(mask.sum())<100 or int(y[mask].sum())<5,
            'fatal':int(y[mask].sum()), 'mean_prediction':float(p[mask].mean()) if mask.any() else None,
            'observed_fraction':float(y[mask].mean()) if mask.any() else None})
    return rows


def select_method(metrics):
    evaluation=metrics[(metrics.phase=='evaluation') & (metrics.group=='all') & metrics.method.isin(METHODS)]
    pivot=evaluation.pivot(index='eval_year',columns='method',values=['log_loss','brier_score'])
    rows=[]
    for method in METHODS:
        ll=pivot['log_loss'][method]-pivot['log_loss']['unchanged']
        bs=pivot['brier_score'][method]-pivot['brier_score']['unchanged']
        rows.append({'method':method,'macro_log_loss':float(pivot['log_loss'][method].mean()),
            'macro_brier_score':float(pivot['brier_score'][method].mean()),
            'macro_log_loss_difference':float(ll.mean()),'macro_brier_difference':float(bs.mean()),
            'years_log_loss_improved':int((ll < -1e-10).sum()),
            'raw_macro_log_loss_rank':None,'eligible':bool(method=='unchanged' or (ll.mean() < -1e-10 and (ll < -1e-10).sum()>=4 and bs.mean()<=1e-10))})
    for rank,row in enumerate(sorted(rows,key=lambda r:r['macro_log_loss']),start=1): row['raw_macro_log_loss_rank']=rank
    eligible=[r for r in rows if r['eligible']]
    minimum=min(r['macro_log_loss'] for r in eligible)
    chosen=min([r for r in eligible if r['macro_log_loss']<=minimum+1e-10],key=lambda r:METHODS.index(r['method']))['method']
    return {'selected_method':chosen,'candidates':rows,'selection_is_retrospective':True}


def run(root: Path):
    root=Path(root)
    verify_inputs(root)
    protocol_path=root/PROTOCOL
    if not FROZEN_HASH or sha256(protocol_path)!=FROZEN_HASH:
        raise ValueError('Protocol must match pre-fit frozen hash')
    protocol=json.loads(protocol_path.read_text())
    for relative,expected in protocol['input_fingerprints'].items():
        if sha256(root/relative)!=expected: raise ValueError(f'Stale frozen input {relative}')
    original=json.loads((root/'data/reference/severity_protocol.json').read_text())
    features,domains,references=original['features'],original['categorical_domains'],original['reference_levels']
    derived=root/'data/derived/temporal_calibration_v1'
    if (derived/'manifest.json').exists():
        raise ValueError('Completed version exists; retain it and version a new experiment')
    derived.mkdir(parents=True,exist_ok=True)
    tables,figures=root/'reports/tables',root/'reports/figures'
    connection=duckdb.connect()
    frame=connection.execute('SELECT source_id,C_YEAR,C_CASE,is_fatal,severity_eligible,'+','.join(features)+
        " FROM read_parquet(?) WHERE CAST(C_YEAR AS INTEGER) BETWEEN 1999 AND 2019 ORDER BY C_YEAR,source_id,C_CASE",
        [str(root/'data/derived/collisions.parquet')]).df()
    if not frame.severity_eligible.all() or not frame.is_fatal.isin([0,1]).all() or frame.duplicated(['source_id','C_YEAR','C_CASE']).any():
        raise ValueError('Invalid input identity or target')
    for feature in features:
        if not frame[feature].isin(domains[feature]).all(): raise ValueError(f'Unsupported {feature}')
    year=frame.C_YEAR.astype(int).to_numpy()
    target=frame.is_fatal.to_numpy(dtype=int)
    unknown=frame[features].isin(['U','UU','X','XX']).any(axis=1).to_numpy()
    other=frame[features].isin(['Q','QQ']).any(axis=1).to_numpy()
    frame['has_unknown_or_unavailable']=unknown
    frame['has_other']=other
    frame['feature_status']=np.select([unknown,other],['contains_unknown_or_unavailable','contains_other'],default='complete_stated')
    metrics_rows,bin_rows,level_rows,membership_rows,model_paths,prediction_paths,pooled=[],[],[],[],[],[],[]
    for t in range(2014,2020):
        print(f'Fold {t}: fitting training years 1999–{t-3}',flush=True)
        masks={'train':year<=t-3,'calibration':(year>=t-2)&(year<=t-1),'evaluation':year==t}
        encoder=OneHotEncoder(categories=[domains[f] for f in features],drop=[references[f] for f in features],
                              handle_unknown='error',sparse_output=True,dtype=np.float64)
        train=masks['train']
        x=encoder.fit_transform(frame.loc[train,features])
        model=LogisticRegression(C=1.0,penalty='l2',solver='lbfgs',max_iter=1000,tol=1e-7,
                                 class_weight=None,fit_intercept=True,random_state=2026)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always',ConvergenceWarning)
            model.fit(x,target[train])
        del x
        if any(issubclass(w.category,ConvergenceWarning) for w in caught) or model.n_iter_[0]>=1000:
            raise ValueError(f'Fold {t} base model convergence failed')
        indices=np.flatnonzero(masks['calibration']|masks['evaluation'])
        prediction=frame.iloc[indices][['source_id','C_YEAR','C_CASE','is_fatal','feature_status','has_unknown_or_unavailable','has_other']].copy()
        prediction['eval_year']=t
        prediction['phase']=np.where(year[indices]==t,'evaluation','calibration')
        z=model.decision_function(encoder.transform(frame.iloc[indices][features]))
        prediction['raw_logit']=z
        cal=prediction.phase.eq('calibration').to_numpy()
        parameters={method:fit_calibrator(z[cal],target[indices][cal],method) for method in METHODS}
        for method in METHODS:
            pars=parameters[method]
            prediction['p_'+method]=expit(pars['slope']*z+pars['intercept'])
        support=[]
        for feature in features:
            for code in domains[feature]:
                counts={phase:int((frame.loc[mask,feature]==code).sum()) for phase,mask in masks.items()}
                record={'eval_year':t,'feature':feature,'code':code,'is_reference':code==references[feature],
                        'train_unobserved':counts['train']==0,**{phase+'_n':count for phase,count in counts.items()},
                        **{phase+'_fatal':int(frame.loc[mask & frame[feature].eq(code).to_numpy(),'is_fatal'].sum()) for phase,mask in masks.items()}}
                support.append(record); level_rows.append(record)
        absent={f:[r['code'] for r in support if r['feature']==f and r['train_unobserved']] for f in features}
        prediction['p_prevalence']=float(target[train].mean())
        prediction['has_train_unobserved_level']=np.logical_or.reduce([frame.iloc[indices][f].isin(absent[f]).to_numpy() for f in features])
        for phase,mask in masks.items():
            grouped=frame.loc[mask].groupby(['source_id','C_YEAR'],observed=True).is_fatal.agg(['size','sum'])
            for (source_id,source_year),r in grouped.iterrows():
                membership_rows.append({'eval_year':t,'phase':phase,'source_id':source_id,'source_year':source_year,'n':int(r['size']),'fatal':int(r['sum'])})
        for phase in ('calibration','evaluation'):
            phase_mask=prediction.phase.eq(phase).to_numpy()
            groups=[('all',phase_mask)]
            for status in ('complete_stated','contains_unknown_or_unavailable','contains_other'):
                groups.append((status,phase_mask&prediction.feature_status.eq(status).to_numpy()))
            for name in ('has_unknown_or_unavailable','has_other','has_train_unobserved_level'):
                for present in (False,True):
                    groups.append((f'{name}={present}',phase_mask&(prediction[name].to_numpy()==present)))
            if phase=='evaluation':
                for feature in features:
                    values=frame.iloc[indices][feature]
                    classes=np.select([values.isin(['U','UU']),values.isin(['Q','QQ']),values.isin(['X','XX'])],['unknown','other','unavailable'],default='stated')
                    for status in ('stated','unknown','other','unavailable'):
                        groups.append((f'{feature}:{status}',phase_mask&(classes==status)))
            for group,mask in groups:
                y=prediction.is_fatal.to_numpy()[mask]
                for method in (*METHODS,'prevalence'):
                    p=prediction['p_'+method].to_numpy()[mask]
                    metrics_rows.append({'eval_year':t,'phase':phase,'group':group,'method':method,**(probability_metrics(y,p) if len(y) else {'n':0,'fatal':0,'sparse_n_lt_100_or_fatal_lt_5':True})})
                    if group=='all':
                        for scheme,edges in protocol['reliability']['schemes'].items():
                            for row in reliability(y,p,edges):
                                bin_rows.append({'eval_year':t,'phase':phase,'method':method,'scheme':scheme,**row})
        pooled.append(prediction.loc[prediction.phase.eq('evaluation'),['is_fatal']+['p_'+m for m in (*METHODS,'prevalence')]].copy())
        pp=derived/f'predictions_{t}.parquet'
        connection.register('fold_predictions',prediction)
        connection.execute('COPY fold_predictions TO ? (FORMAT PARQUET, COMPRESSION ZSTD)',[str(pp)])
        connection.unregister('fold_predictions')
        prediction_paths.append(pp)
        record={'eval_year':t,'features':features,'categories':domains,'references':references,
            'encoded_features':[{'feature':f,'code':c} for f in features for c in domains[f] if c!=references[f]],
            'coefficients':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),
            'train_prevalence':float(target[train].mean()),'iterations':int(model.n_iter_[0]),'converged':True,
            'hyperparameters':model.get_params(),'calibrators':parameters,'protocol_sha256':FROZEN_HASH,
            'counts':{phase:{'n':int(mask.sum()),'fatal':int(target[mask].sum()),'min_year':int(year[mask].min()),'max_year':int(year[mask].max())} for phase,mask in masks.items()}}
        mp=derived/f'model_{t}.json'; mp.write_text(json.dumps(record,indent=2)+'\n'); model_paths.append(mp)
        print(f'Fold {t}: archived {len(prediction):,} calibration/evaluation predictions; iterations={model.n_iter_[0]}',flush=True)
        del model,encoder,prediction,z
    metrics=pd.DataFrame(metrics_rows)
    annual=metrics[(metrics.phase=='evaluation')&(metrics.group=='all')]
    numeric=['log_loss','brier_score','average_precision','roc_auc','mean_prediction','observed_prevalence','prediction_minus_observed','observed_expected_ratio']
    macro=annual.groupby('method')[numeric].agg(['mean','std'])
    macro.columns=['_'.join(c) for c in macro.columns]; macro=macro.reset_index()
    pooled=pd.concat(pooled,ignore_index=True)
    pooled_scores=pd.DataFrame([{'method':m,**probability_metrics(pooled.is_fatal,pooled['p_'+m])} for m in (*METHODS,'prevalence')])
    outputs={'macro':macro,'pooled':pooled_scores,'metrics':metrics,'reliability':pd.DataFrame(bin_rows),'level_support':pd.DataFrame(level_rows),'membership':pd.DataFrame(membership_rows)}
    table_paths=[]
    for name,data in outputs.items():
        path=tables/f'tcal_v1_{name}.csv'; data.to_csv(path,index=False); table_paths.append(path)
    selection=select_method(metrics)
    selection_path=derived/'selection.json'; selection_path.write_text(json.dumps(selection,indent=2)+'\n')
    pd.DataFrame(selection['candidates']).to_csv(tables/'tcal_v1_selection.csv',index=False)
    table_paths.append(tables/'tcal_v1_selection.csv')
    enrich_saved_outputs(root)
    plot_from_tables(root)
    artifacts=table_paths+[tables/'tcal_v1_ece.csv',tables/'tcal_v1_calibrators.csv']+model_paths+prediction_paths+[selection_path,root/'models/temporal_calibration_v1_card.md']+list(figures.glob('tcal_v1_*.png'))
    inputs=[protocol_path,root/'data/reference/severity_protocol.json',root/'data/reference/modeling_contract.json',root/'data/derived/collisions.parquet',root/'uv.lock',Path(__file__),root/'src/road_to_safety/explore.py']
    for relative,expected in protocol['input_fingerprints'].items():
        if sha256(root/relative)!=expected: raise ValueError(f'Input changed during run {relative}')
    manifest={'status':'fitted_pending_independent_validation','created_utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':FROZEN_HASH,'input_fingerprints':{str(p.relative_to(root)):sha256(p) for p in inputs},
        'artifacts':{str(p.relative_to(root)):sha256(p) for p in artifacts},'evaluated_years':list(range(2014,2020)),
        'excluded_from_all_fitting_calibration_scoring':[2020,2021],
        'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__,'scipy':scipy.__version__,'numpy':np.__version__,'pandas':pd.__version__},'selection':selection}
    (derived/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest



def enrich_saved_outputs(root):
    """Complete support diagnostics from saved scores; no fitting or rescoring."""
    root=Path(root); derived=root/'data/derived/temporal_calibration_v1'; tables=root/'reports/tables'
    con=duckdb.connect()
    features=json.loads((root/'data/reference/severity_protocol.json').read_text())['features']
    metrics=pd.read_csv(tables/'tcal_v1_metrics.csv')
    metrics=metrics[~metrics.group.str.startswith(('has_unknown=','has_unavailable='))]
    extra=[]
    for t in range(2014,2020):
        path=derived/f'predictions_{t}.parquet'
        prediction=con.execute('SELECT * FROM read_parquet(?)',[str(path)]).df()
        source=con.execute('SELECT source_id,C_YEAR,C_CASE,'+','.join(features)+
            ' FROM read_parquet(?) WHERE CAST(C_YEAR AS INTEGER) BETWEEN ? AND ?',
            [str(root/'data/derived/collisions.parquet'),t-2,t]).df()
        joined=prediction[['source_id','C_YEAR','C_CASE']].merge(source,on=['source_id','C_YEAR','C_CASE'],validate='one_to_one',how='left')
        if joined[features].isna().any().any(): raise ValueError('Diagnostic join lost feature records')
        prediction['has_unknown']=joined[features].isin(['U','UU']).any(axis=1).to_numpy()
        prediction['has_unavailable']=joined[features].isin(['X','XX']).any(axis=1).to_numpy()
        evaluation=prediction.phase.eq('evaluation').to_numpy()
        for name in ('has_unknown','has_unavailable'):
            for present in (False,True):
                mask=evaluation & (prediction[name].to_numpy()==present)
                y=prediction.is_fatal.to_numpy()[mask]
                for method in (*METHODS,'prevalence'):
                    p=prediction['p_'+method].to_numpy()[mask]
                    extra.append({'eval_year':t,'phase':'evaluation','group':f'{name}={present}','method':method,
                        **(probability_metrics(y,p) if len(y) else {'n':0,'fatal':0,'sparse_n_lt_100_or_fatal_lt_5':True})})
        con.register('enriched',prediction)
        temporary=path.with_suffix('.tmp.parquet')
        con.execute('COPY enriched TO ? (FORMAT PARQUET,COMPRESSION ZSTD)',[str(temporary)])
        con.unregister('enriched'); temporary.replace(path)
    pd.concat([metrics,pd.DataFrame(extra)],ignore_index=True).to_csv(tables/'tcal_v1_metrics.csv',index=False)
    membership=pd.read_csv(tables/'tcal_v1_membership.csv')
    membership['nonfatal']=membership.n-membership.fatal
    membership['fatal_prevalence']=membership.fatal/membership.n
    membership.to_csv(tables/'tcal_v1_membership.csv',index=False)
    support=pd.read_csv(tables/'tcal_v1_level_support.csv')
    for phase in ('train','calibration','evaluation'):
        support[phase+'_nonfatal']=support[phase+'_n']-support[phase+'_fatal']
        support[phase+'_prevalence']=support[phase+'_fatal']/support[phase+'_n'].replace(0,np.nan)
    support.to_csv(tables/'tcal_v1_level_support.csv',index=False)
    bins=pd.read_csv(tables/'tcal_v1_reliability.csv')
    ece=[]
    for key,group in bins.groupby(['eval_year','phase','method','scheme']):
        n=group.n.sum()
        value=float((group.n*(group.observed_fraction-group.mean_prediction).abs()).sum()/n)
        ece.append(dict(zip(['eval_year','phase','method','scheme'],key),n=int(n),ece=value))
    pd.DataFrame(ece).to_csv(tables/'tcal_v1_ece.csv',index=False)
    calibrator_rows=[]
    for t in range(2014,2020):
        model=json.loads((derived/f'model_{t}.json').read_text())
        for method,parameters in model['calibrators'].items():
            calibrator_rows.append({'eval_year':t,'method':method,**{k:v for k,v in parameters.items() if k!='raw_gradient'}})
    pd.DataFrame(calibrator_rows).to_csv(tables/'tcal_v1_calibrators.csv',index=False)
    selection=select_method(pd.read_csv(tables/'tcal_v1_metrics.csv'))
    (derived/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    pd.DataFrame(selection['candidates']).to_csv(tables/'tcal_v1_selection.csv',index=False)


def plot_from_tables(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(root); tables=root/'reports/tables'; figures=root/'reports/figures'
    metrics=pd.read_csv(tables/'tcal_v1_metrics.csv')
    annual=metrics[(metrics.phase=='evaluation')&(metrics.group=='all')&metrics.method.isin(METHODS)]
    colors={'unchanged':'#315a77','intercept_only':'#c27b2c','sigmoid':'#39755d'}
    fig,axes=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
    for method,rows in annual.groupby('method',sort=False):
        for ax,column,label in zip(axes,['log_loss','brier_score','prediction_minus_observed'],['Log loss ↓','Brier score ↓','Predicted minus observed probability']):
            ax.plot(rows.eval_year,rows[column],marker='o',label=method,color=colors[method]); ax.set_ylabel(label); ax.set_xlabel('Evaluation year'); ax.set_xticks(range(2014,2020)); ax.tick_params(axis='x',rotation=0)
    axes[2].axhline(0,color='gray',ls=':'); axes[0].legend(fontsize=8)
    fig.suptitle('Expanding-window calibration: recorded fatal/injury collisions\nBase fit through t−3; calibration t−2/t−1; evaluation t (no 2020–2021 scoring)')
    fig.savefig(figures/'tcal_v1_annual_scores.png',dpi=160); plt.close(fig)
    bins=pd.read_csv(tables/'tcal_v1_reliability.csv')
    occupied=bins[(bins.phase=='evaluation')&(bins.scheme=='low_probability')&(bins.n>0)&bins.method.isin(METHODS)]
    limit=min(1.,max(.2,float(occupied[['mean_prediction','observed_fraction']].max().max())*1.1))
    fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    for ax,t in zip(axes.flat,range(2014,2020)):
        for method in METHODS:
            rows=bins[(bins.phase=='evaluation')&(bins.eval_year==t)&(bins.method==method)&(bins.scheme=='low_probability')&(bins.n>0)]
            ax.plot(rows.mean_prediction,rows.observed_fraction,'o-',markersize=3,label=method,color=colors[method])
            sparse=rows[(rows.n<100)|(rows.fatal<5)]
            ax.scatter(sparse.mean_prediction,sparse.observed_fraction,marker='x',s=38,color=colors[method])
        ax.plot([0,1],[0,1],color='gray',ls=':'); ax.set_title(str(t)); ax.set_xlim(0,limit); ax.set_ylim(0,limit); ax.set_xlabel('Mean predicted probability'); ax.set_ylabel('Observed fatal fraction')
    axes.flat[0].legend(fontsize=8)
    fig.suptitle('Evaluation reliability, fixed low-range bins\nAll occupied bins shown; crosses flag n<100 or fatalities<5. Complete counts in reliability CSV')
    fig.savefig(figures/'tcal_v1_reliability.png',dpi=160); plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--plots-only',action='store_true')
    args=parser.parse_args()
    if args.plots_only: plot_from_tables(args.root.resolve())
    else: print(json.dumps(run(args.root.resolve()),indent=2))

if __name__=='__main__': main()
