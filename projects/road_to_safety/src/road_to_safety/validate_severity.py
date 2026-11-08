"""Independently reconcile frozen severity-model outputs against prepared events."""
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


def expected_split(years):
    years = np.asarray(years, dtype=int)
    if ((years < 1999) | (years > 2021)).any():
        raise ValueError('Year outside frozen population')
    return np.where(years <= 2016, 'train', np.where(years <= 2019, 'validation', 'test'))


def recall_threshold(y, probability, required=0.8):
    """Maximize precision under recall constraint, breaking ties at higher score."""
    grouped = pd.DataFrame({'score': probability, 'positive': y}).groupby('score').agg(
        positive=('positive', 'sum'), n=('positive', 'size')).sort_index(ascending=False)
    total = grouped.positive.sum()
    if not total:
        raise ValueError('Recall threshold needs validation fatalities')
    cumulative = grouped.positive.cumsum()
    feasible = grouped[cumulative / total >= required].copy()
    feasible['precision'] = (cumulative / grouped.n.cumsum()).loc[feasible.index]
    return float(feasible[feasible.precision == feasible.precision.max()].index.max())


def independent_metrics(y, probability, threshold):
    """Ranking metrics use score groups, so ties receive no arbitrary row ordering."""
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    if not np.isfinite(probability).all() or ((probability < 0) | (probability > 1)).any():
        raise ValueError('Probabilities must be finite and in [0, 1]')
    n, positives = len(y), int(y.sum())
    negatives = n - positives
    ranking = pd.DataFrame({'score': probability, 'fatal': y}).groupby('score').agg(
        fatal=('fatal', 'sum'), n=('fatal', 'size')).sort_index(ascending=False)
    tp_cumulative = ranking.fatal.cumsum().to_numpy()
    fp_cumulative = (ranking.n - ranking.fatal).cumsum().to_numpy()
    ap = float(np.sum((ranking.fatal.to_numpy() / positives) *
        (tp_cumulative / (tp_cumulative + fp_cumulative)))) if positives and negatives else float('nan')
    auc = float(np.trapezoid(np.r_[0, tp_cumulative] / positives,
        np.r_[0, fp_cumulative] / negatives)) if positives and negatives else float('nan')
    predicted = probability >= threshold
    tp, fp = int((predicted & (y == 1)).sum()), int((predicted & (y == 0)).sum())
    fn, tn = positives - tp, negatives - fp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / positives if positives else 0.0
    clipped = np.clip(probability, np.finfo(float).eps, 1 - np.finfo(float).eps)
    bins = np.minimum((probability * 10).astype(int), 9)
    ece = sum(abs(probability[bins == b].mean() - y[bins == b].mean()) * (bins == b).sum()
        for b in range(10) if (bins == b).any()) / n
    return {'n': n, 'fatal': positives, 'roc_auc': auc, 'average_precision': ap,
        'log_loss': float(-np.mean(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))),
        'brier_score': float(np.mean((probability - y) ** 2)), 'ece': float(ece),
        'fatal_proportion': float(y.mean()), 'mean_prediction': float(probability.mean()),
        'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp, 'precision': precision, 'recall': recall,
        'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def assert_values(actual, expected, tolerance=1e-10):
    for key, value in expected.items():
        found = float(actual[key])
        if np.isnan(value) and np.isnan(found):
            continue
        if not np.isfinite(found) or not np.isclose(found, value, rtol=tolerance, atol=tolerance):
            raise ValueError(f'{key}: {found} != {value}')


def reconstruct_probability(frame, model):
    """Score exported additive log odds directly, independently of sklearn."""
    if model['features'] != FEATURES:
        raise ValueError('Feature list differs from frozen eight-feature allowlist')
    score = np.full(len(frame), float(model['intercept']))
    terms = {(term['feature'],term['code']):float(coefficient)
        for term,coefficient in zip(model['encoded_features'],model['coefficients'],strict=True)}
    for field in FEATURES:
        score += frame[field].map({code:coefficient for (feature,code),coefficient
            in terms.items() if feature == field}).fillna(0).to_numpy()
    return 1 / (1 + np.exp(-score))


def validate(root):
    root = Path(root)
    derived = root / 'data/derived'
    tables = root / 'reports/tables'
    protocol_path = root / 'data/reference/severity_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    model = json.loads((derived / 'severity_model.json').read_text())
    manifest = json.loads((derived / 'severity_manifest.json').read_text())
    connection = duckdb.connect()
    predictions = connection.read_parquet(str(derived / 'severity_predictions.parquet')).df()
    events = connection.read_parquet(str(derived / 'collisions.parquet')).project(
        ','.join(KEYS + ['is_fatal', 'severity_eligible'] + FEATURES)).df()
    checks = []
    def check(name, operation):
        try:
            operation()
            checks.append({'check': name, 'status': 'passed', 'error': ''})
        except (ValueError, AssertionError, KeyError, TypeError) as error:
            checks.append({'check': name, 'status': 'failed', 'error': str(error)})
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def fingerprints():
        require(fingerprint(protocol_path) == '7684a32e919a0b73f57ed55e7c1c796c4cb5a73c1a62cdeb76a1ff8889259491', 'Frozen protocol amended')
        require(model['protocol_sha256'] == fingerprint(protocol_path), 'Model protocol binding changed')
        for relative, digest in protocol['input_sha256'].items():
            require(fingerprint(root / relative) == digest, f'Frozen input changed: {relative}')
        hashes = manifest.get('input_fingerprints', manifest.get('input_sha256', {}))
        require(hashes.get('data/reference/severity_protocol.json') == fingerprint(protocol_path),
            'Manifest must bind frozen protocol hash')
        for relative, digest in hashes.items():
            require(fingerprint(root / relative) == digest, f'Manifest input changed: {relative}')
        for relative, digest in manifest.get('artifacts', manifest.get('output_fingerprints', {})).items():
            require(fingerprint(root / relative) == digest, f'Manifest output changed: {relative}')
    check('frozen_input_and_artifact_fingerprints', fingerprints)
    check('prediction_keys_unique', lambda: require(not predictions.duplicated(KEYS).any(), 'Duplicate prediction key'))
    check('source_keys_unique', lambda: require(not events.duplicated(KEYS).any(), 'Duplicate source key'))
    eligible = events[events.severity_eligible].drop(columns='severity_eligible')
    joined = eligible.merge(predictions, on=KEYS, how='outer', validate='one_to_one', indicator=True,
        suffixes=('_source', ''))
    check('exact_eligible_collision_coverage', lambda: require((joined._merge == 'both').all(), 'Missing or extra scored collision'))
    check('binary_unchanged_target', lambda: require(joined.is_fatal.isin([0, 1]).all() and
        joined.is_fatal.eq(joined.is_fatal_source).all(), 'Changed or nonbinary target'))
    check('chronological_partitions', lambda: require(np.array_equal(joined.split, expected_split(joined.C_YEAR)),
        'Incorrect chronological assignment'))
    check('frozen_allowlist', lambda: require(model['features'] == protocol['features'] == FEATURES,
        'Forbidden or changed model features'))
    def categories():
        require(model['categories'] == protocol['categorical_domains'], 'Category domains changed')
        require(model['references'] == protocol['reference_levels'], 'Reference levels changed')
        expected_terms = [{'feature': field, 'code': code} for field in FEATURES
            for code in protocol['categorical_domains'][field] if code != protocol['reference_levels'][field]]
        require(model['encoded_features'] == expected_terms, 'Encoded terms differ from declared OHE')
        for field in FEATURES:
            require(joined[field].isin(protocol['categorical_domains'][field]).all(), f'Out-of-domain {field}')
    check('dictionary_domains_references_and_design', categories)
    check('converged_training_fit', lambda: require(model['converged'] and
        max(np.atleast_1d(model['iterations'])) < protocol['logistic_regression']['max_iter'], 'Unconverged fit'))
    train = joined[joined.split == 'train']
    prevalence = train.is_fatal.mean()
    check('training_only_prevalence', lambda: require(np.isclose(model['train_prevalence'], prevalence, atol=1e-14) and
        np.allclose(joined.p_baseline, prevalence, atol=1e-14), 'Baseline not training mean'))
    def scores():
        for field in ['p_baseline', 'p_logistic']:
            require(np.isfinite(joined[field]).all() and joined[field].between(0, 1).all(), f'Invalid {field}')
        reconstructed = reconstruct_probability(joined, model)
        require(np.allclose(joined.p_logistic, reconstructed, rtol=1e-10, atol=1e-12), 'Exported coefficients do not reconstruct scores')
    check('probabilities_and_independent_coefficient_reconstruction', scores)
    def training_fit_evidence():
        require(model['classes'] == [0,1], 'Positive probability class changed')
        for parameter, expected in protocol['logistic_regression'].items():
            if parameter in model['hyperparameters']:
                require(model['hyperparameters'][parameter] == expected, f'Changed hyperparameter {parameter}')
        residual = train.p_logistic.to_numpy() - train.is_fatal.to_numpy()
        gradient = [abs(float(residual.mean()))]
        gradients = {field: pd.Series(residual).groupby(train[field].to_numpy()).agg(['sum','size'])
            for field in FEATURES}
        for term, coefficient in zip(model['encoded_features'], model['coefficients'], strict=True):
            group = gradients[term['feature']]
            observed = term['code'] in group.index
            total = float(group.loc[term['code'],'sum']) if observed else 0.
            gradient.append(abs(float((total + coefficient) / len(train))))
            if not observed:
                require(abs(coefficient) < 1e-12, 'Training-unobserved level has nonzero fitted coefficient')
        require(max(gradient) < 1e-5, f'Training-only penalized score gradient not near stationary: {max(gradient)}')
    check('training_only_penalized_likelihood_stationarity_and_parameters', training_fit_evidence)
    def training_levels():
        levels = pd.read_csv(tables / 'severity_training_levels.csv', dtype={'code': str})
        coefficients = pd.read_csv(tables / 'severity_coefficients.csv', dtype={'code': str})
        require(not levels.duplicated(['feature','code']).any(), 'Duplicate level row')
        require(len(levels) == sum(len(x) for x in protocol['categorical_domains'].values()), 'Missing dictionary level')
        unseen_mask = np.zeros(len(joined), dtype=bool)
        level_counts = {field:joined.groupby(['split',field]).size() for field in FEATURES}
        for row in levels.to_dict('records'):
            require(row['feature'] in FEATURES and row['code'] in protocol['categorical_domains'][row['feature']], 'Unsupported exported level')
            counts = {part:int(level_counts[row['feature']].get((part,row['code']),0))
                for part in ['train','validation','test']}
            assert_values(row, {f'{part}_count': value for part, value in counts.items()})
            require(row['train_unobserved'] == (counts['train'] == 0), 'Training-support flag changed')
            if counts['train'] == 0:
                unseen_mask |= joined[row['feature']].eq(row['code']).to_numpy()
        require(np.array_equal(joined.has_train_unobserved_level, unseen_mask), 'Incorrect training-unobserved score-support flag')
        terms = {(t['feature'],t['code']):float(c) for t,c in zip(model['encoded_features'],model['coefficients'],strict=True)}
        require(len(coefficients) == len(levels) and not coefficients.duplicated(['feature','code']).any(), 'Missing or duplicate coefficient table row')
        for row in coefficients.to_dict('records'):
            expected = terms.get((row['feature'],row['code']), 0.)
            assert_values(row, {'coefficient': expected, 'odds_ratio': float(np.exp(expected))})
    check('independent_training_vocabulary_support_and_coefficients', training_levels)
    def feature_status():
        unknown = joined[FEATURES].isin(['U','UU','X','XX']).any(axis=1)
        other = joined[FEATURES].isin(['Q','QQ']).any(axis=1)
        expected = np.where(unknown, 'contains_unknown_or_unavailable', np.where(other, 'contains_other', 'complete_stated'))
        require(np.array_equal(joined.feature_status, expected), 'Incorrect quality-group classification')
        require(np.array_equal(joined.has_unknown_or_unavailable, unknown) and np.array_equal(joined.has_other,other), 'Incorrect overlapping sentinel flags')
    check('independent_missingness_and_other_group_classification', feature_status)
    validation = joined[joined.split == 'validation']
    threshold = recall_threshold(validation.is_fatal, validation.p_logistic,
        protocol['thresholds']['validation_selected']['target_recall'])
    check('validation_only_precision_optimal_recall_threshold', lambda: require(
        np.isclose(threshold, model['validation_threshold'], rtol=0, atol=1e-14), 'Wrong validation threshold'))
    for column, cutoff in [('predicted_at_0_5', 0.5), ('predicted_at_validation_threshold', threshold)]:
        check(column, lambda c=column, t=cutoff: require(np.array_equal(joined[c].astype(int),
            (joined.p_logistic >= t).astype(int)), 'Confusion labels disagree with frozen score threshold'))
    metrics = pd.read_csv(tables / 'severity_metrics.csv', dtype={'group': str})
    # Store integer row indices once; repeated full string scans per metric would
    # make the exhaustive category audit needlessly slow and memory intensive.
    group_indices = {}
    for split, indices in joined.groupby('split').groups.items():
        group_indices[('split',str(split))] = np.asarray(indices)
    for year, indices in joined.groupby('C_YEAR').groups.items():
        group_indices[('year',str(year))] = np.asarray(indices)
    for (split,status), indices in joined.groupby(['split','feature_status']).groups.items():
        group_indices[('split_feature_status',f'{split}:{status}')] = np.asarray(indices)
    for period in ['test','2020','2021']:
        subset = joined[joined.split == 'test'] if period == 'test' else joined[joined.C_YEAR == period]
        for field in FEATURES:
            for code, indices in subset.groupby(field).groups.items():
                group_indices[('feature_category',f'{period}:{field}:{code}')] = np.asarray(indices)
    def group_frame(kind, group):
        try:
            return joined.iloc[group_indices[(kind,str(group))]]
        except KeyError as error:
            raise ValueError(f'Unrecognized metric group {kind}/{group}') from error
    def metrics_check():
        require(not metrics.duplicated(['group_kind','group','model','threshold_kind']).any(), 'Duplicate metric row')
        required_pairs = {('prevalence','fixed_0_5'),('prevalence','validation_recall_80'),('logistic','fixed_0_5'),('logistic','validation_recall_80')}
        for _, group in metrics.groupby(['group_kind','group']):
            require(set(zip(group.model,group.threshold_kind)) == required_pairs, 'Missing model/threshold comparison')
        for row in metrics.to_dict('records'):
            subset = group_frame(row['group_kind'], row['group'])
            require(len(subset) > 0, f'Empty metric group {row}')
            probability = subset['p_baseline' if row['model'] == 'prevalence' else 'p_' + row['model']]
            assert_values(row, independent_metrics(subset.is_fatal, probability, float(row['threshold'])))
            expected = .5 if row['threshold_kind'] in ['fixed', 'fixed_0_5', '0.5'] else threshold
            require(np.isclose(row['threshold'], expected, atol=1e-14), 'Incorrect metric threshold')
    check('independent_all_saved_metrics_and_confusion_matrices', metrics_check)
    def groups_present():
        pairs = set(zip(metrics.group_kind, metrics.group))
        require(all(('split', s) in pairs or ('partition', s) in pairs for s in ['train','validation','test']), 'Missing split metrics')
        require(all(('year', str(y)) in pairs or ('annual', str(y)) in pairs for y in range(1999,2022)), 'Missing annual metrics')
    check('all_partitions_and_annual_2020_2021_reported', groups_present)
    def subgroup_presence():
        pairs = set(zip(metrics.group_kind,metrics.group))
        for split in ['train','validation','test']:
            for status in joined.loc[joined.split == split,'feature_status'].unique():
                require(('split_feature_status', f'{split}:{status}') in pairs, 'Missing quality subgroup')
        for period in ['test','2020','2021']:
            subset = joined[joined.split == 'test'] if period == 'test' else joined[joined.C_YEAR.astype(str) == period]
            for field in FEATURES:
                for code in subset[field].unique():
                    require(('feature_category', f'{period}:{field}:{code}') in pairs, 'Missing late-period category subgroup')
        for row in metrics.to_dict('records'):
            require(row['sparse_n_lt_100_or_fatal_lt_5'] == (row['n'] < 100 or row['fatal'] < 5), 'Incorrect sparse flag')
    check('all_late_year_category_and_quality_subgroups_and_sparse_flags', subgroup_presence)

    calibration = pd.read_csv(tables / 'severity_calibration.csv', dtype={'group': str})
    def calibration_check():
        require(not calibration.duplicated(['group_kind','group','model','bin']).any(), 'Duplicate calibration bin')
        metric_groups = set(map(tuple, metrics[['group_kind','group','model']].drop_duplicates().to_numpy()))
        calibration_groups = set(map(tuple, calibration[['group_kind','group','model']].drop_duplicates().to_numpy()))
        require(metric_groups == calibration_groups, 'Missing calibration group/model')
        for (kind, group, name), output in calibration.groupby(['group_kind','group','model']):
            subset = group_frame(kind, group)
            probability = subset['p_baseline' if name == 'prevalence' else 'p_' + name].to_numpy()
            bins = np.minimum((probability * 10).astype(int), 9)
            require(len(output) == 10, 'Calibration must retain all ten bins')
            output = output.sort_values('bin')
            for i, row in enumerate(output.to_dict('records')):
                mask = bins == i
                require(int(row['n']) == int(mask.sum()), 'Calibration count mismatch')
                require(int(row['fatal']) == int(subset.is_fatal.to_numpy()[mask].sum()), 'Calibration fatal count mismatch')
                if mask.any():
                    assert_values(row, {'mean_prediction': float(probability[mask].mean()),
                        'observed_fraction': float(subset.is_fatal.to_numpy()[mask].mean()),
                        'fatal': int(subset.is_fatal.to_numpy()[mask].sum()), 'left': i/10, 'right': (i+1)/10})
                else:
                    require(pd.isna(row['mean_prediction']) and pd.isna(row['observed_fraction']), 'Empty bin average must be null')
    check('independent_calibration_bins_counts_and_averages', calibration_check)
    def distributions():
        output = pd.read_csv(tables / 'severity_feature_distributions.csv', dtype={'group':str,'code':str})
        require(not output.duplicated(['group_kind','group','feature','code']).any(), 'Duplicate distribution row')
        expected_rows = 26 * sum(len(v) for v in protocol['categorical_domains'].values())
        require(len(output) == expected_rows, 'Missing zero-support distribution levels')
        for field in FEATURES:
            for kind, column in [('split','split'),('year','C_YEAR')]:
                counts = joined.groupby([column,field]).size()
                totals = joined.groupby(column).size()
                part = output[(output.feature == field) & (output.group_kind == kind)]
                for row in part.to_dict('records'):
                    expected_n = int(counts.get((row['group'],row['code']),0))
                    denominator = int(totals[row['group']])
                    assert_values(row, {'n': expected_n, 'group_n': denominator, 'share': expected_n/denominator})
                    value_class = ('unknown' if row['code'] in ['U','UU'] else
                        'jurisdiction_unavailable' if row['code'] in ['X','XX'] else
                        'other' if row['code'] in ['Q','QQ'] else 'stated')
                    require(row['value_class'] == value_class, 'Other/unknown/unavailable categories conflated')
    check('independent_all_split_year_feature_distributions_and_sentinel_classes', distributions)
    connection.close()
    pd.DataFrame(checks).to_csv(tables / 'severity_validation_checks.csv', index=False)
    failures = [r for r in checks if r['status'] != 'passed']
    result = {'status': 'failed' if failures else 'passed', 'failures': failures,
        'checks_passed': [r['check'] for r in checks if r['status'] == 'passed'],
        'method': 'Independent source-event join, fixed split predicates, coefficient score reconstruction, grouped ranking/confusion/calibration calculations; no model refit.',
        'input_fingerprints': {str(p.relative_to(root)): fingerprint(p) for p in [protocol_path,
            derived/'collisions.parquet', derived/'severity_predictions.parquet', derived/'severity_model.json', derived/'severity_manifest.json']},
        'validator_sha256': fingerprint(Path(__file__))}
    (derived / 'severity_validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    result = validate(parser.parse_args().root)
    print(json.dumps(result, indent=2))
    if result['status'] != 'passed':
        raise SystemExit(1)
