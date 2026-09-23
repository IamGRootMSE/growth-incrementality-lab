"""Policy contrasts with unequal treatment allocation and clustered uncertainty."""
import numpy as np

def estimate(y, t, policy, groups=None):
    """Hajek contrast E[pi Y|T=1]-E[pi Y|T=0], per eligible user.

    pi can be a stochastic policy (constant depth for random targeting).
    Influence function accounts for estimating the marginal allocation rate.
    Cluster sandwich handles repeated anonymized feature vectors.
    """
    y, t, policy = (np.asarray(a, dtype=float) for a in (y, t, policy))
    if len(y) != len(t) or len(y) != len(policy):
        raise ValueError('Array lengths differ')
    if not np.isin(t, [0, 1]).all() or not np.isin(y, [0, 1]).all():
        raise ValueError('Treatment and outcome must be binary')
    if not np.isfinite(policy).all() or np.any((policy < 0) | (policy > 1)):
        raise ValueError('Policy probabilities must be in [0,1]')
    p = t.mean()
    if not 0 < p < 1:
        raise ValueError('Both assignment arms required')
    z = y * policy
    a, b = z[t == 1].mean(), z[t == 0].mean()
    influence = t / p * (z-a) - (1-t) / (1-p) * (z-b)
    return float(a-b), influence

def interval(effect, influence, groups=None):
    influence = np.asarray(influence)
    n = len(influence)
    if groups is None:
        se = influence.std(ddof=1) / np.sqrt(n)
    else:
        _, codes = np.unique(groups, return_inverse=True)
        totals = np.bincount(codes, weights=influence)
        g = len(totals)
        se = np.sqrt(np.sum(totals**2) * g / (g-1)) / n
    return {'estimate': float(effect), 'se': float(se),
            'low': float(effect-1.96*se), 'high': float(effect+1.96*se)}

def top_policy(score, depth):
    if not 0 <= depth <= 1:
        raise ValueError('Depth outside [0,1]')
    score = np.asarray(score)
    # Stable ties use source row order, never outcome or assignment.
    selected = np.zeros(len(score))
    selected[np.argsort(-score, kind='stable')[:int(round(depth*len(score)))]] = 1
    return selected

def curve(y, t, score, groups, depths):
    full, full_if = estimate(y, t, np.ones(len(y)))
    points, influences, qinfs = [], [], []
    for depth in depths:
        policy = np.full(len(y), depth) if score is None else top_policy(score, depth)
        effect, inf = estimate(y, t, policy)
        actual = float(policy.mean())
        qinf = np.zeros(len(y)) if score is None else inf - actual * full_if
        qeffect = 0.0 if score is None else effect-actual*full
        points.append({'depth': actual, **interval(effect, inf, groups),
                       'qini': interval(qeffect, qinf, groups),
                       'policy_weighted_treated_events': float(np.sum((y*policy)[t == 1])),
                       'policy_weighted_control_events': float(np.sum((y*policy)[t == 0]))})
        influences.append(inf)
        qinfs.append(qinf)
    area = np.trapezoid([p['qini']['estimate'] for p in points], depths)
    area_if = np.trapezoid(np.array(qinfs), depths, axis=0)
    return {'points': points, 'auqc': interval(area, area_if, groups)}, influences, area_if
