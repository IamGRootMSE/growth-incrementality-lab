import json
from pathlib import Path
import numpy as np
import pandas as pd
from lab.pipeline import FEATURES, feature_matrix, split_groups, fit_tlearner, predict, select_model, audit

def fixture():
    """Synthetic randomized unit-test fixture only; never portfolio evidence."""
    rng=np.random.default_rng(42);n=2500
    df=pd.DataFrame(rng.normal(size=(n,12)),columns=FEATURES)
    df['treatment']=rng.binomial(1,.8,n)
    df['conversion']=rng.binomial(1,.15+.12*df.treatment)
    df['visit']=df.conversion
    df['exposure']=df.treatment
    df['row_id']=np.arange(n)
    return df

def test_features_exclude_labels_assignment_and_metadata():
    df=fixture();x=feature_matrix(df)
    for c in ['conversion','visit','exposure','treatment','row_id']:df[c]=999
    assert x.shape[1]==12
    assert np.array_equal(x,feature_matrix(df))

def test_identical_features_never_cross_splits_even_if_labels_differ():
    df=fixture();duplicate=df.iloc[:100].copy();duplicate.conversion=1-duplicate.conversion
    data=pd.concat([df,duplicate],ignore_index=True)
    groups,splits=split_groups(data)
    assert list(splits[:100])==list(splits[-100:])
    assert pd.DataFrame({'g':groups,'s':splits}).groupby('g').s.nunique().max()==1
    assert np.array_equal(splits,split_groups(data)[1])

def test_training_selection_and_prediction_integration():
    df=fixture();df['group'],df['split']=split_groups(df)
    train=df[df.split=='train'];validation=df[df.split=='validation'];test=df[df.split=='test']
    candidates={}
    for name in ['linear','boosted']:
        model=fit_tlearner(train,name,smoke=True)
        candidates[name]=predict(model,validation)[0]
        assert np.isfinite(predict(model,test)[0]).all()
    selected,scores=select_model(validation,candidates)
    assert selected==max(scores,key=scores.get)
    # Test-label perturbation cannot enter the selection API or change selection.
    test=test.copy();test['conversion']=1-test.conversion
    assert select_model(validation,candidates)==(selected,scores)
    assert audit(df)['missing_cells']==0

def test_committed_results_integrity():
    r=json.loads(Path('outputs/analysis/results.json').read_text())
    assert r['mode']=='empirical'
    assert sum(x['rows'] for x in r['splits'].values())==r['quality']['rows']
    assert r['provenance']['source_rows']==13979592
    assert .83<r['evaluation_treatment_probability']<.87
    for c in r['curves'].values():
        assert len(c['points'])==21
        assert abs(c['points'][-1]['estimate']-r['ate']['estimate'])<1e-12
    assert r['selection']['selected']==max(r['selection']['validation_auqc'],key=r['selection']['validation_auqc'].get)
