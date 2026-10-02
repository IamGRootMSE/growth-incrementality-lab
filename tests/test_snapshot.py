import pytest
from scripts.check_snapshot import compare
from lab.experiment import normalized_input_hash


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


def test_only_raw_hash_provenance_is_excluded():
    compare('a'*64, 'b'*64, '$.scenarios.benefit.input_sha256')
    with pytest.raises(AssertionError):
        compare('broken', 'b'*64, '$.scenarios.benefit.input_sha256')
    with pytest.raises(AssertionError):
        compare('a'*64, 'b'*64, '$.scenarios.benefit.normalized_input_sha256')
    row = dict(user_id='a', arm=0, converted=1, revenue=10., margin=4., followup_days=28)
    assert normalized_input_hash([row]) == normalized_input_hash([dict(row, revenue=10.+1e-14)])
    assert normalized_input_hash([row]) != normalized_input_hash([dict(row, revenue=10.01)])
