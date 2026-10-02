# Experiment decision toolkit — review walkthrough

Independent portfolio extension, October 2, 2026. **All data in this extension is synthetic.** It is separate from the existing public Criteo benchmark. No experiment was run for Fullscript or an employer.

## Five-minute demo

```sh
python -m pip install -r requirements.lock
python -m lab.experiment
python -m pytest -q
python scripts/build_site.py
python -m http.server 8000 --directory outputs/site
```

Open `/experiment/index.html`. Alternatively open `outputs/experiment/index.html` directly; it has no external assets. Review `outputs/experiment/results.json` for exact estimates, source hashes, arm counts, assumptions and blocked-readout reasons. Seed 20261002 is fixed. The generator writes aggregates only; it never publishes user-level records.

On Windows if pytest's shared temporary directory is inaccessible, create `work/` and use `python -m pytest -q --basetemp=work/pytest-temp`.

## Decision contract

- Assignment unit: one independent user, 50/50 allocation. Retain nonbuyers and unexposed assigned users (intention to treat). Outcomes cover exactly the first 28 days; the supplied `followup_days` confirms availability, not permission to use a longer outcome window.
- Primary outcome: 28-day conversion. Design baseline 20%, absolute MDE 3 percentage points, power 80%. Normal approximation gives 3,926 users/arm at Bonferroni alpha 0.05/3. MDE is a sizing alternative, not a minimum-effect shipping threshold; shipping tests benefit above zero.
- Economic metrics: net revenue and contribution margin **per assigned user**, including intervention cost for nonbuyers. In the fixture margin is 40% of revenue minus a per-assigned-treatment cost. These are invented economics, not observed Criteo revenue.
- Integrity gates: duplicate/missing IDs, invalid/nonfinite outcomes, sample ratio mismatch (chi-square p < .001), insufficient planned sample, immature outcomes and sparse binary counts. Invalid readouts do not produce effect claims.
- Three two-sided Welch intervals at alpha/3 target approximate simultaneous 95% coverage. This is conservative, does not assume independent metrics, and accounts only for these three prespecified metrics. Binary means use a large-sample approximation with a sparse-count guard.
- Ship candidate: positive conversion lower bound and both economic lower bounds above their tolerated declines (revenue −$0.50, margin −$0.25). Reject for economic harm when either upper bound is below its floor. Otherwise inconclusive. Statistical clearance is not an automatic deployment decision.

The demo fixes 8,000 users per arm **before generating outcomes**; power's 3,926 is a minimum. At 1,000 eligible users per day, 21 whole-week enrollment days plus 28 days follow-up supports the larger demo. Do not repeatedly test, extend to significance, or stop early using this procedure. Finance must approve tolerances and size guardrails using credible historical variances; primary-metric power does not assure joint decision power.

## Executed example and interpretation

The benefit and margin-harm scenarios share identical conversion and revenue draws. Their 5.60 percentage-point conversion lift is the same, but increasing intervention cost from $0.10 to $4.00 per assigned treated user reverses the margin decision. The null scenario is inconclusive. The unequal-count scenario is blocked by SRM. Exact intervals are in the generated report, not copied into a manually maintained slide.

## What I would defend in an interview

1. **Why all assigned users?** Conditioning on purchase or exposure after assignment can bias treatment comparisons. Buyer AOV is a diagnostic, not the primary causal revenue estimand.
2. **Why reject a conversion win?** Incremental demand can fail to cover intervention expense. Discuss contribution margin and accepted loss before launch.
3. **Why not use p > .05 to say “safe”?** Failure to detect harm is not evidence of noninferiority. A lower bound must clear a business tolerance.
4. **What if practitioners affect several users?** Randomize/cluster at practitioner level, size using intracluster correlation, and consider interference. This independent-user engine is not valid unchanged.
5. **How would you handle heavy tails or refunds?** Audit extreme orders, define refund lag and observation maturity before launch, then validate coverage with unit-level simulations or an appropriate bootstrap. Do not trim only after seeing an inconvenient result.
6. **What is missing?** Sequential testing, factorial/multivariant designs, CUPED, clustered randomization, missing-outcome adjustment and guardrail power simulation. Adding these without correct design would weaken the portfolio.

## Verification and references

Tests compare Welch limits against SciPy's independent `ttest_ind(equal_var=False).confidence_interval`, test all four decisions, power direction, immature data, duplicate users, nonfinite values, zero variance and ITT arithmetic. Desktop/mobile browser checks verify report values and evidence links.

[SciPy Welch t-test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html). Original code and newly generated synthetic aggregates are covered by the repository's MIT software terms; Criteo-derived materials retain their existing CC BY-NC-SA attribution.

**Defensible resume wording:** Extended an independent Python experimentation portfolio with power planning, fixed-horizon intention-to-treat readouts, allocation/follow-up checks, and revenue/contribution-margin decision gates; validated known synthetic failure cases against statistical reference calculations.
