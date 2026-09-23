import numpy as np
import pytest
from lab.estimators import estimate, interval, top_policy, curve

def test_unequal_assignment_recovers_hand_calculated_effect():
    y=np.array([1,0,0,0,1,1,1,0,0,0])
    t=np.array([0,0,1,1,1,1,1,1,1,1])
    effect,_=estimate(y,t,np.ones(10))
    assert effect==pytest.approx(3/8-1/2)
    # An unadjusted signed sum is not the causal contrast.
    assert effect!=pytest.approx(np.mean(y*(2*t-1)))

def test_zero_full_and_random_policy_identities():
    y=np.array([0,1,0,1,1,0]);t=np.array([0,0,1,1,1,1])
    full,fi=estimate(y,t,np.ones(6))
    zero,zi=estimate(y,t,np.zeros(6))
    random,ri=estimate(y,t,np.full(6,.2))
    assert zero==0 and np.all(zi==0)
    assert random==pytest.approx(.2*full)
    assert np.allclose(ri,.2*fi)

def test_cluster_interval_matches_manual_sandwich():
    inf=np.array([1.,2.,-1.,-2.]); groups=np.array([0,0,1,1])
    result=interval(.3,inf,groups)
    assert result['se']==pytest.approx(np.sqrt((3**2+(-3)**2)*2)/4)

def test_pairwise_identical_policy_difference_is_zero():
    y=np.array([1,0,1,0]); t=np.array([0,0,1,1])
    effect,inf=estimate(y,t,np.ones(4))
    assert interval(effect-effect,inf-inf)['se']==0

def test_ranking_ties_are_stable_and_depth_bounded():
    assert top_policy([1,1,1,0],.5).tolist()==[1,1,0,0]
    assert top_policy([3,1,2],0).sum()==0
    assert top_policy([3,1,2],1).sum()==3
    with pytest.raises(ValueError):top_policy([1,2],1.1)

@pytest.mark.parametrize('t,y,p', [([1,1],[0,1],[1,1]),([0,2],[0,1],[1,1]),([0,1],[0,2],[1,1]),([0,1],[0,1],[-1,1])])
def test_invalid_inputs_fail(t,y,p):
    with pytest.raises(ValueError):estimate(y,t,p)

def test_random_qini_is_exactly_zero():
    y=np.array([0,1,1,0,1,0]);t=np.array([0,0,1,1,1,1])
    c,_,_=curve(y,t,None,np.arange(6),np.linspace(0,1,21))
    assert c['auqc']['estimate']==0
    assert all(p['qini']['estimate']==0 for p in c['points'])

def test_randomized_known_effect_recovery():
    rng=np.random.default_rng(8);n=100000
    t=rng.binomial(1,.85,n);y=rng.binomial(1,.1+.12*t)
    effect,inf=estimate(y,t,np.ones(n));ci=interval(effect,inf)
    assert abs(effect-.12)<.01
    assert ci['low']<.12<ci['high']
