import pytest
from scripts.check_snapshot import compare


def test_snapshot_accepts_roundoff_but_rejects_material_and_schema_drift():
    compare({'mean':1.0,'count':3}, {'mean':1.0+1e-14,'count':3})
    for expected, actual in [({'mean':1.0},{'mean':1.01}),
                             ({'count':3},{'count':4}),
                             ({'count':1},{'count':True}),
                             ({'a':None},{}),
                             ([1,2],[1]),
                             ('SHIP_CANDIDATE','INVALID'),
                             (float('nan'),float('nan'))]:
        with pytest.raises(AssertionError):
            compare(expected, actual)
