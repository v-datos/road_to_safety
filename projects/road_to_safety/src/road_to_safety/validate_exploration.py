"""Independent full-cohort reconciliation of descriptive evidence tables."""
import argparse
import json
from pathlib import Path
import duckdb
import pandas as pd
from .explore import sha256, verify_inputs


def check_counts(actual, expected, keys):
    """Require identical groups, collision counts and fatal counts; reject duplicates."""
    columns = ['collisions', 'fatal_collisions']
    if actual.duplicated(keys).any():
        raise ValueError(f'Duplicate descriptive groups: {keys}')
    left = actual.set_index(keys)[columns].sort_index().astype('int64')
    right = expected.set_index(keys)[columns].sort_index().astype('int64')
    pd.testing.assert_frame_equal(left, right, check_names=False)
    if 'fatal_proportion' in actual:
        expected_rates = actual.fatal_collisions / actual.collisions
        if not ((actual.fatal_proportion - expected_rates).abs() < 1e-12).all():
            raise ValueError('Fatal proportions do not match their denominators')
    if 'injury_collisions' in actual:
        if not (actual.injury_collisions + actual.fatal_collisions == actual.collisions).all():
            raise ValueError('Fatal and injury counts do not conserve collisions')


def validate(root):
    root = Path(root)
    receipt = verify_inputs(root)
    connection = duckdb.connect()
    connection.read_parquet(str(root/'data/derived/collisions.parquet')).create_view('c')
    tables = root/'reports/tables'
    failures, checks = [], []
    def perform(name, operation):
        try:
            operation()
            checks.append(name)
        except (AssertionError, ValueError, KeyError) as error:
            failures.append({'check': name, 'error': str(error)})
    def compare(name, select, group, keys):
        actual = pd.read_csv(tables/name, dtype={key:str for key in keys}, keep_default_na=False)
        expected = connection.execute(f'SELECT {select}, count(*) collisions, '
            f'sum(is_fatal)::BIGINT fatal_collisions FROM c GROUP BY {group}').df()
        for key in keys:
            expected[key] = expected[key].astype(str)
        check_counts(actual, expected, keys)
    perform('annual', lambda:compare('eda_temporal_annual.csv','C_YEAR','C_YEAR',['C_YEAR']))
    fields = {'month':'C_MNTH','weekday':'C_WDAY','hour':'C_HOUR',
        'season':"CASE WHEN C_MNTH IN ('12','1','2') THEN 'DJF' WHEN C_MNTH IN ('3','4','5') THEN 'MAM' WHEN C_MNTH IN ('6','7','8') THEN 'JJA' WHEN C_MNTH IN ('9','10','11') THEN 'SON' ELSE C_MNTH END"}
    for dimension, expression in fields.items():
        perform(dimension, lambda d=dimension,e=expression:compare(
            f'eda_temporal_{d}.csv',f'{e} code','1',['code']))
        perform(dimension+'_by_year', lambda d=dimension,e=expression:compare(
            f'eda_temporal_{d}_by_year.csv',f'C_YEAR,{e} code','1,2',['C_YEAR','code']))
    for yearly in (False, True):
        suffix = '_by_year' if yearly else ''
        perform('weekday_hour'+suffix, lambda y=yearly,s=suffix:compare(
            f'eda_temporal_weekday_hour{s}.csv', ('C_YEAR,' if y else '')+'C_WDAY weekday_code,C_HOUR hour_code',
            '1,2,3' if y else '1,2',(['C_YEAR'] if y else [])+['weekday_code','hour_code']))
    for yearly in (False, True):
        name = 'eda_condition_by_year.csv' if yearly else 'eda_condition_pooled.csv'
        actual = pd.read_csv(tables/name, dtype={'code':str,'year':str},keep_default_na=False)
        for field in ('C_WTHR','C_RSUR','C_RCFG','C_RALN','C_TRAF'):
            part = actual[actual.field==field]
            keys = ['year','code'] if yearly else ['code']
            expected = connection.execute('SELECT '+('C_YEAR AS year,' if yearly else '')+
                f'{field} code,count(*) collisions,sum(is_fatal)::BIGINT fatal_collisions FROM c GROUP BY ALL').df()
            for key in keys:
                expected[key] = expected[key].astype(str)
            perform(name+':'+field, lambda a=part,e=expected,k=keys:check_counts(a,e,k))
    values = pd.read_csv(tables/'eda_quality_values.csv', dtype={'year':str,'code':str}, keep_default_na=False)
    contract = json.loads((root/'data/reference/modeling_contract.json').read_text())
    for field in contract['features']:
        expected = connection.execute(f'SELECT C_YEAR AS year,{field} code,count(*) collisions, '
            'sum(is_fatal)::BIGINT fatal_collisions FROM c GROUP BY ALL').df()
        expected['year'] = expected.year.astype(str)
        expected['code'] = expected.code.astype(str)
        part = values[(values.field==field) & values.observed].copy()
        part['fatal_proportion'] = pd.to_numeric(part.fatal_proportion)
        perform('quality_values:'+field, lambda a=part,e=expected:check_counts(a,e,['year','code']))
    complete = pd.read_csv(tables/'eda_quality_complete_cases.csv',dtype={'year':str})
    predicate = ' AND '.join(f"regexp_full_match({f}, '[0-9]+') AND NOT {f}_conflict" for f in contract['features'])
    expected_complete = connection.execute('SELECT C_YEAR AS year,count(*) collisions,sum(is_fatal)::BIGINT fatal_collisions,'
        f'count(*) FILTER(WHERE {predicate}) fully_stated_collisions,'
        f'sum(is_fatal) FILTER(WHERE {predicate})::BIGINT fully_stated_fatal_collisions FROM c GROUP BY ALL').df()
    expected_complete['year'] = expected_complete.year.astype(str)
    def check_complete():
        columns = ['collisions','fatal_collisions','fully_stated_collisions','fully_stated_fatal_collisions']
        pd.testing.assert_frame_equal(complete[complete.year!='ALL'].set_index('year')[columns].sort_index(),
            expected_complete.set_index('year')[columns].sort_index(),check_dtype=False)
        assert complete[complete.year=='ALL'][columns].iloc[0].tolist()==expected_complete[columns].sum().tolist()
    perform('complete_case_sensitivity',check_complete)
    sparse = pd.read_csv(tables/'eda_sparse_categories.csv')
    perform('sparse_flags',lambda:pd.testing.assert_series_equal(sparse['sparse'],
        (sparse.collisions<100)|(sparse.fatal_collisions<5),check_names=False))
    annual_conditions = pd.read_csv(tables/'eda_condition_by_year.csv',dtype={'year':str,'code':str})
    standard = pd.read_csv(tables/'eda_condition_year_standardization.csv',dtype={'code':str})
    annual_counts = expected_complete.set_index('year').collisions
    def check_standardization():
        for row in standard.itertuples():
            group = annual_conditions[(annual_conditions.field==row.field)&(annual_conditions.code==row.code)]
            assert row.all_years_supported == (set(group.year)==set(annual_counts.index))
            sparse_years = int(((group.collisions<100)|(group.fatal_collisions<5)).sum())
            assert row.observed_sparse_years == sparse_years
            assert row.any_sparse_year == bool(sparse_years)
            if row.all_years_supported:
                estimate = sum((r.fatal_collisions/r.collisions)*(annual_counts[r.year]/annual_counts.sum()) for r in group.itertuples())
                assert abs(estimate-row.common_year_weighted_fatal_proportion)<1e-12
            else:
                assert pd.isna(row.common_year_weighted_fatal_proportion)
    perform('common_year_weight_sensitivity',check_standardization)
    connection.close()
    pd.DataFrame([{'check':name,'status':'passed','error':''} for name in checks]+
        [{'check':failure['check'],'status':'failed','error':failure['error']} for failure in failures]).to_csv(
            tables/'eda_validation_checks.csv',index=False)
    paths = sorted(tables.glob('eda_*.csv'))+sorted((root/'reports/figures').glob('*.png'))
    codes = sorted((root/'src/road_to_safety').glob('analyze_*.py'))+[Path(__file__), root/'src/road_to_safety/explore.py']
    result = {'status':'failed' if failures else 'passed','failures':failures,'checks_passed':checks,
        'collisions':receipt['collisions'],'fatal_collisions':receipt['fatal_collisions'],
        'method':'Independent DuckDB full-cohort temporal, condition and feature-value counts; rates, conservation, complete-case sensitivity, sparse flags and common-year weighting. Quality preparation-evidence reconciliations also run in analyze_stability.',
        'input_fingerprints':{p:sha256(root/p) for p in ['data/derived/collisions.parquet','data/derived/prepared_validation.json','data/reference/modeling_contract.json']},
        'code_fingerprints':{str(p.relative_to(root)):sha256(p) for p in codes},
        'output_fingerprints':{str(p.relative_to(root)):sha256(p) for p in paths}}
    (root/'data/derived/exploration_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    result=validate(parser.parse_args().root)
    print(json.dumps(result,indent=2))
    if result['status']!='passed':
        raise SystemExit(1)
