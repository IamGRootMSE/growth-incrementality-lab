"""Independent SQL arithmetic reconciliation against local evaluation rows."""
import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

def validate():
    r=json.loads(Path('outputs/analysis/results.json').read_text())
    con=duckdb.connect()
    con.execute("CREATE TABLE predictions AS SELECT * FROM read_csv_auto('data/processed/test_predictions.csv.gz')")
    ate=con.execute('SELECT avg(y) FILTER (WHERE t=1)-avg(y) FILTER (WHERE t=0) FROM predictions').fetchone()[0]
    assert np.isclose(ate,r['ate']['estimate'],atol=1e-12)
    n=con.execute('SELECT count(*) FROM predictions').fetchone()[0]
    assert n==r['splits']['test']['rows']
    checks=['SQL ATE equals published estimate','Evaluation row count matches manifest']
    for policy in ['uplift','baseline','propensity']:
        for i in [0,1,4,10,20]:
            k=round(n*i/20)
            value=con.execute(f'''WITH ranked AS (
                SELECT *, row_number() OVER(ORDER BY {policy} DESC,row_id ASC) AS rank FROM predictions)
                SELECT sum(CASE WHEN t=1 AND rank<=? THEN y ELSE 0 END)::DOUBLE / sum(t)
                     - sum(CASE WHEN t=0 AND rank<=? THEN y ELSE 0 END)::DOUBLE / sum(1-t)
                FROM ranked''',[k,k]).fetchone()[0]
            assert np.isclose(value,r['curves'][policy]['points'][i]['estimate'],atol=1e-12)
        checks.append(f'SQL {policy}: 0/5/20/50/100% agree')
    memberships=pd.read_csv('data/processed/splits.csv.gz')
    assert memberships.groupby('group').split.nunique().max()==1
    assert memberships.row_id.is_unique
    checks += ['No feature-group split leakage','Unique source row positions']
    for c in r['curves'].values():
        assert np.isclose(c['points'][-1]['estimate'],ate)
        assert c['points'][0]['estimate']==0
        assert all(p['low']<=p['estimate']<=p['high'] for p in c['points'])
    checks.append('Curve endpoints and interval ordering valid')
    result={'status':'passed','checks':checks,'source':'Local row-level test predictions; independent DuckDB recomputation'}
    Path('outputs/analysis/validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':validate()
