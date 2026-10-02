import copy
import numpy as np
import pytest
from scipy import stats
from lab.experiment import Plan, contrast, evaluate, fixture


def test_power_and_planning_direction():
    assert Plan(absolute_mde=.015).per_arm > 3*Plan().per_arm
    assert Plan(power=.9).per_arm > Plan().per_arm
    with pytest.raises(ValueError):
        Plan(baseline=float('nan'))


def test_welch_matches_scipy_independent_oracle():
    a, b = [1, 3, 4, 8, 12], [0, 1, 4, 5, 6, 7]
    result = contrast(a, b, .05)
    oracle = stats.ttest_ind(a, b, equal_var=False).confidence_interval(.95)
    assert result['low'] == pytest.approx(oracle.low)
    assert result['high'] == pytest.approx(oracle.high)
    assert result['estimate'] == pytest.approx(np.mean(a)-np.mean(b))


@pytest.mark.parametrize('scenario,decision', [('benefit','SHIP_CANDIDATE'),
    ('margin_harm','DO_NOT_SHIP_HARM'), ('null','INCONCLUSIVE'), ('srm','INVALID')])
def test_synthetic_decisions(scenario, decision):
    assert evaluate(fixture(scenario))['decision'] == decision


def test_readout_integrity_and_intention_to_treat():
    rows = fixture('benefit')
    result = evaluate(rows)
    assert result['metrics']['converted']['control_mean'] == pytest.approx(
        sum(r['converted'] for r in rows if r['arm']==0)/8000)
    bad = copy.deepcopy(rows)
    bad[0]['followup_days'] = 27
    assert evaluate(bad)['blockers'] == ['incomplete_followup']
    with pytest.raises(ValueError, match='duplicate'):
        evaluate(rows + [rows[0]])
    bad[0]['revenue'] = float('nan')
    with pytest.raises(ValueError, match='Nonfinite'):
        evaluate(bad)
    assert evaluate(fixture('benefit', n=100))['decision'] == 'INVALID'


def test_zero_variance_rejected():
    with pytest.raises(ValueError, match='variance'):
        contrast([1,1], [0,0], .05)
