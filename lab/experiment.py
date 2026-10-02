"""Fixed-horizon, user-randomized experiment decisions. Synthetic CLI demo only."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from math import ceil, isfinite, sqrt
from pathlib import Path

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class Plan:
    baseline: float = .20
    absolute_mde: float = .03
    alpha: float = .05
    power: float = .80
    followup_days: int = 28
    daily_eligible: int = 1000
    revenue_tolerance: float = .50
    margin_tolerance: float = .25
    srm_alpha: float = .001

    def __post_init__(self):
        values = asdict(self).values()
        if not all(isfinite(v) for v in values):
            raise ValueError('Plan values must be finite')
        if not (0 < self.baseline < self.baseline + self.absolute_mde < 1
                and 0 < self.alpha < 1 and .5 < self.power < 1
                and 0 < self.srm_alpha < 1 and self.daily_eligible > 0
                and self.followup_days > 0 and self.revenue_tolerance >= 0
                and self.margin_tolerance >= 0):
            raise ValueError('Invalid plan')

    @property
    def per_arm(self):
        # Three simultaneous two-sided intervals; conservative familywise alpha.
        p0, p1 = self.baseline, self.baseline + self.absolute_mde
        pooled = (p0 + p1) / 2
        z, zb = stats.norm.ppf(1 - self.alpha / 6), stats.norm.ppf(self.power)
        return ceil((z * sqrt(2 * pooled * (1 - pooled))
                     + zb * sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
                    / self.absolute_mde ** 2)


def contrast(treatment, control, alpha):
    """Welch mean difference and t interval; independent assignment units."""
    a, b = np.asarray(treatment, dtype=float), np.asarray(control, dtype=float)
    if min(len(a), len(b)) < 2 or not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError('Need at least two finite values per arm')
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    delta, se = float(a.mean() - b.mean()), sqrt(va + vb)
    if se == 0:
        raise ValueError('Zero variance cannot establish an experiment decision')
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    half = stats.t.ppf(1 - alpha / 2, df) * se
    return dict(estimate=delta, low=float(delta-half), high=float(delta+half),
                se=se, df=float(df), control_mean=float(b.mean()),
                treatment_mean=float(a.mean()))


def evaluate(rows, plan=Plan()):
    """One row per assigned user, including nonbuyers; never filter by exposure."""
    seen, arms = set(), {0: [], 1: []}
    for r in rows:
        if not r.get('user_id') or r['user_id'] in seen:
            raise ValueError('Missing or duplicate assignment unit')
        seen.add(r['user_id'])
        if r['arm'] not in arms or r['converted'] not in (0, 1):
            raise ValueError('Invalid arm or binary outcome')
        for key in ('revenue', 'margin', 'followup_days'):
            if not isfinite(r[key]):
                raise ValueError('Nonfinite outcome or follow-up')
        if r['revenue'] < 0 or r['margin'] > r['revenue'] or r['followup_days'] < 0:
            raise ValueError('Invalid economic outcome or follow-up')
        if not r['converted'] and r['revenue'] != 0:
            raise ValueError('Nonbuyer revenue must be zero')
        arms[r['arm']].append(r)
    counts = [len(arms[a]) for a in (0, 1)]
    if min(counts) < 2:
        raise ValueError('Both assigned arms required')
    srm_p = float(stats.chisquare(counts).pvalue)
    blockers = []
    if srm_p < plan.srm_alpha:
        blockers.append('sample_ratio_mismatch')
    if min(counts) < plan.per_arm:
        blockers.append('planned_sample_not_reached')
    # The original input may be a one-shot iterator; reuse validated arm rows.
    if any(r['followup_days'] < plan.followup_days for arm in arms.values() for r in arm):
        blockers.append('incomplete_followup')
    if any(min(sum(r['converted'] for r in arm),
               len(arm)-sum(r['converted'] for r in arm)) < 20 for arm in arms.values()):
        blockers.append('sparse_binary_outcomes')
    report = dict(plan=asdict(plan), planned_per_arm=plan.per_arm,
                  enrollment_days=max(14, ceil(2*plan.per_arm/plan.daily_eligible/7)*7),
                  counts=counts, srm_p=srm_p, blockers=blockers,
                  decision='INVALID', metrics={})
    if blockers:
        return report
    for key in ('converted', 'revenue', 'margin'):
        report['metrics'][key] = contrast([r[key] for r in arms[1]],
                                           [r[key] for r in arms[0]], plan.alpha/3)
    m = report['metrics']
    thresholds = dict(revenue=-plan.revenue_tolerance, margin=-plan.margin_tolerance)
    if any(m[k]['high'] < floor for k, floor in thresholds.items()):
        report['decision'] = 'DO_NOT_SHIP_HARM'
    elif m['converted']['low'] > 0 and all(m[k]['low'] > floor for k, floor in thresholds.items()):
        report['decision'] = 'SHIP_CANDIDATE'
    else:
        report['decision'] = 'INCONCLUSIVE'
    return report


def fixture(scenario, n=8000, seed=20261002):
    """Invented commerce users, not Criteo or employer records."""
    if scenario not in ('benefit', 'margin_harm', 'null', 'srm'):
        raise ValueError('Unknown scenario')
    rng = np.random.default_rng(seed)
    rows = []
    for arm in (0, 1):
        size = n if scenario != 'srm' or arm == 0 else int(n*.65)
        for i in range(size):
            converted = int(rng.random() < .20 + (arm*.06 if scenario != 'null' else 0))
            revenue = converted * float(rng.lognormal(4.3, .3))
            margin = revenue*.40 - arm*(4.0 if scenario == 'margin_harm' else .10)
            rows.append(dict(user_id=f'{arm}-{i}', arm=arm, converted=converted,
                             revenue=revenue, margin=margin, followup_days=28))
    return rows


def normalized_input_hash(rows):
    """Hash currency at $0.0001 precision; analysis keeps full input precision."""
    canonical = [dict(r, revenue=f"{r['revenue']:.4f}", margin=f"{r['margin']:.4f}")
                 for r in rows]
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('outputs/experiment'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = {}
    for scenario in ('benefit', 'margin_harm', 'null', 'srm'):
        rows = fixture(scenario)
        result = evaluate(rows)
        result['input_sha256'] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
        result['normalized_input_sha256'] = normalized_input_hash(rows)
        results[scenario] = result
    payload = dict(source='SYNTHETIC — invented independent portfolio scenarios', seed=20261002,
                   interval='Approximate simultaneous 95% family coverage via three Bonferroni Welch intervals',
                   scenarios=results)
    (args.output/'results.json').write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    from .experiment_report import render
    (args.output/'index.html').write_text(render(payload), encoding='utf-8')
    print(json.dumps({k: v['decision'] for k, v in results.items()}, indent=2))


if __name__ == '__main__':
    main()
