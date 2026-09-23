"""Deterministic acquire -> sample -> audit -> train -> select -> evaluate pipeline."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '4')
import argparse
import hashlib
import json
from pathlib import Path
import time
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from .acquire import acquire, SHA256, URL, digest
from .estimators import estimate, interval, top_policy, curve

SEED = 20260923
FEATURES = [f'f{i}' for i in range(12)]
FIELDS = FEATURES + ['treatment', 'conversion', 'visit', 'exposure']

def feature_matrix(df):
    return df.loc[:, FEATURES].to_numpy(dtype=float)

def split_groups(df):
    groups = pd.util.hash_pandas_object(df[FEATURES], index=False).to_numpy()
    # Cryptographic rehash breaks correlations in anonymized feature hashes.
    unique, inv = np.unique(groups, return_inverse=True)
    buckets = np.array([int.from_bytes(hashlib.blake2b(f'{SEED}:{x}'.encode(), digest_size=8).digest(), 'little') % 100 for x in unique])[inv]
    splits = np.where(buckets < 60, 'train', np.where(buckets < 80, 'validation', 'test'))
    return groups, splits

def sample_data(path, smoke=False):
    cache = Path('data/processed') / ('smoke.csv.gz' if smoke else 'sample.csv.gz')
    metadata = cache.with_suffix('.json')
    if cache.exists() and metadata.exists():
        meta = json.loads(metadata.read_text())
        expected_probability = .004 if smoke else .10
        if meta['seed'] != SEED or meta['sampling_probability'] != expected_probability or meta['source_sha256'] != SHA256:
            raise ValueError('Sample parameters changed; remove the local sample cache before rerunning')
        if meta['sample_sha256'] == digest(cache):
            return pd.read_csv(cache), meta
        raise ValueError('Sample cache checksum mismatch')
    rng = np.random.default_rng(SEED)
    probability = .004 if smoke else .10
    parts, counts, total = [], {0: 0, 1: 0}, 0
    for chunk in pd.read_csv(path, chunksize=200000):
        if set(chunk.columns) != set(FIELDS):
            raise ValueError(f'Unexpected schema: {chunk.columns.tolist()}')
        counts = {a: counts[a]+int((chunk.treatment == a).sum()) for a in counts}
        ids = np.arange(total, total+len(chunk))
        keep = rng.random(len(chunk)) < probability
        part = chunk.loc[keep].copy()
        part['row_id'] = ids[keep]
        parts.append(part)
        total += len(chunk)
    if total != 13979592:
        raise ValueError(f'Unexpected full-source row count: {total}')
    df = pd.concat(parts, ignore_index=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False, compression={'method': 'gzip', 'mtime': 0})
    meta = {'source_url': URL, 'source_sha256': SHA256, 'source_rows': total,
            'source_arm_counts': counts, 'sampling_probability': probability,
            'seed': SEED, 'sample_rows': len(df), 'sample_sha256': digest(cache),
            'method': 'Seeded Bernoulli sampling over every source row, independent of arm, features and outcome; no prefix truncation.'}
    metadata.write_text(json.dumps(meta, indent=2))
    # Normalize through CSV so cached and first runs use identical floats.
    return pd.read_csv(cache), meta

def fit_tlearner(train, kind, leaves=7, smoke=False):
    x, y, t = feature_matrix(train), train.conversion.to_numpy(), train.treatment.to_numpy()
    models = []
    for arm in (0, 1):
        if kind == 'linear':
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=500, random_state=SEED))
        else:
            model = HistGradientBoostingClassifier(max_iter=50 if smoke else 140,
                max_leaf_nodes=leaves, min_samples_leaf=200, learning_rate=.07,
                l2_regularization=10, early_stopping=False, random_state=SEED)
        model.fit(x[t == arm], y[t == arm])
        models.append(model)
    return models

def predict(models, df):
    x = feature_matrix(df)
    p0, p1 = [m.predict_proba(x)[:, 1] for m in models]
    return p1-p0, p1

def select_model(validation, predictions):
    # This API deliberately has no final-test parameter.
    depths = np.linspace(0, 1, 21)
    scores = {}
    for name, score in predictions.items():
        c, _, _ = curve(validation.conversion.to_numpy(), validation.treatment.to_numpy(),
                         score, validation.group.to_numpy(), depths)
        scores[name] = c['auqc']['estimate']
    return max(scores, key=scores.get), scores

def audit(df):
    if df[FIELDS].isna().any().any() or not np.isfinite(feature_matrix(df)).all():
        raise ValueError('Missing or nonfinite input requires explicit handling')
    for c in ['treatment', 'conversion', 'visit', 'exposure']:
        if not df[c].isin([0, 1]).all():
            raise ValueError(f'Nonbinary field {c}')
    con = duckdb.connect()
    con.register('sample', df)
    sql = Path('sql/audit.sql').read_text()
    arms = con.execute(sql).df().to_dict('records')
    smds = {}
    for c in FEATURES:
        a, b = df.loc[df.treatment == 1, c], df.loc[df.treatment == 0, c]
        smds[c] = float((a.mean()-b.mean()) / np.sqrt((a.var()+b.var())/2))
    return {'rows': len(df), 'missing_cells': int(df[FIELDS].isna().sum().sum()),
            'exact_duplicate_rows': int(df.duplicated(FIELDS).sum()),
            'repeated_feature_rows': int(df.duplicated(FEATURES).sum()),
            'control_exposures': int(((df.treatment == 0) & (df.exposure == 1)).sum()),
            'arms': arms, 'standardized_mean_differences': smds,
            'max_absolute_smd': max(abs(x) for x in smds.values())}

def run(smoke=False, output=None):
    start = time.time()
    out = Path(output or ('work/smoke-results' if smoke else 'outputs/analysis'))
    out.mkdir(parents=True, exist_ok=True)
    df, provenance = sample_data(acquire(), smoke)
    quality = audit(df)
    df['group'], df['split'] = split_groups(df)
    train, val, test = [df[df.split == s].copy() for s in ['train', 'validation', 'test']]
    for a, b in [(train, val), (train, test), (val, test)]:
        assert set(a.group).isdisjoint(b.group)
    print('Split sizes:', len(train), len(val), len(test), flush=True)
    models, predictions = {}, {}
    for name, kind, leaves in [('linear', 'linear', 7), ('boosted_7', 'boosted', 7), ('boosted_15', 'boosted', 15)]:
        print('Fitting', name, flush=True)
        models[name] = fit_tlearner(train, kind, leaves, smoke)
        predictions[name] = predict(models[name], val)[0]
    selected, selection_scores = select_model(val, predictions)
    selection = {'selected': selected, 'validation_auqc': selection_scores,
                 'criterion': 'Maximum validation area above random targeting, 21 fixed depths; no test outcomes used.'}
    (out / 'selection.json').write_text(json.dumps(selection, indent=2))
    # Model selection is complete and persisted before final test evaluation.
    print('Frozen selection:', selected, flush=True)
    uplift, _ = predict(models[selected], test)
    baseline, _ = predict(models['linear'], test)
    # Prespecified propensity comparator: boosted_7 treated-arm outcome model.
    _, propensity = predict(models['boosted_7'], test)
    y, t, groups = test.conversion.to_numpy(), test.treatment.to_numpy(), test.group.to_numpy()
    ate, ate_if = estimate(y, t, np.ones(len(test)))
    depths = np.linspace(0, 1, 21)
    curves, infs, areas = {}, {}, {}
    for name, score in [('random', None), ('propensity', propensity), ('baseline', baseline), ('uplift', uplift)]:
        curves[name], infs[name], areas[name] = curve(y, t, score, groups, depths)
    contrasts = {}
    for comparator in ['random', 'propensity', 'baseline']:
        effect = curves['uplift']['points'][4]['estimate']-curves[comparator]['points'][4]['estimate']
        contrasts[comparator] = interval(effect, infs['uplift'][4]-infs[comparator][4], groups)
    # Assignment predictability diagnostic trained only on training features.
    assignment = make_pipeline(StandardScaler(), LogisticRegression(max_iter=300))
    assignment.fit(feature_matrix(train), train.treatment)
    assignment_auc = roc_auc_score(val.treatment, assignment.predict_proba(feature_matrix(val))[:, 1])
    results = {'schema_version': 1, 'mode': 'smoke' if smoke else 'empirical',
        'seed': SEED, 'provenance': provenance, 'quality': quality, 'selection': selection,
        'splits': {s: {'rows': len(part), 'treated': int(part.treatment.sum()), 'conversions': int(part.conversion.sum()),
                        'groups': int(part.group.nunique())} for s, part in [('train', train), ('validation', val), ('test', test)]},
        'test_arm_counts': {str(a): int((t == a).sum()) for a in [0, 1]},
        'test_arm_conversions': {str(a): int(y[t == a].sum()) for a in [0, 1]},
        'assignment_validation_auc': float(assignment_auc), 'ate': interval(ate, ate_if, groups),
        'evaluation_treatment_probability': float(t.mean()), 'curves': curves,
        'paired_uplift_difference_at_20pct': contrasts,
        'interval_method': '95% normal intervals using feature-group cluster sandwich influence functions; fixed fitted models and observed ranking. Pointwise, not simultaneous. No model-training or transport uncertainty.',
        'runtime_seconds': round(time.time()-start, 2)}
    (out / 'results.json').write_text(json.dumps(results, indent=2, allow_nan=False))
    prefix = 'smoke_' if smoke else ''
    pd.DataFrame({'row_id': test.row_id, 'group': groups, 't': t, 'y': y,
                  'uplift': uplift, 'propensity': propensity, 'baseline': baseline}).to_csv(f'data/processed/{prefix}test_predictions.csv.gz', index=False)
    pd.DataFrame({'row_id': df.row_id, 'group': df.group, 'split': df.split}).to_csv(f'data/processed/{prefix}splits.csv.gz', index=False)
    print(json.dumps({'ate': results['ate'], 'selection': selection, 'runtime_seconds': results['runtime_seconds']}, indent=2))
    return results

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--smoke', action='store_true')
    p.add_argument('--output')
    a = p.parse_args()
    run(a.smoke, a.output)
