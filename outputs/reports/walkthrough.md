# Analysis walkthrough

This is a readable companion to the executable pipeline, with results from the acquired Criteo v2.1 file. It is not a synthetic example. Run commands from the repository root after installing `requirements.lock` in Python 3.12.

## 1. Acquire and verify

```bash
python -m lab.acquire
```

`lab/acquire.py` checks SHA-256 before the file can enter analysis. The official file contains 13,979,592 rows. The pipeline scans all rows with a common inclusion probability of 10%, yielding 1,399,703. It records full-source arm counts; no prefix sample or outcome enrichment is used.

## 2. Audit data in SQL and Python

```sql
SELECT treatment, count(*) AS users, sum(conversion) AS conversions,
       avg(conversion) AS conversion_rate
FROM sample GROUP BY treatment ORDER BY treatment;
```

Executed sample: 209,613 controls with 411 conversions, and 1,190,090 treated users with 3,716 conversions. Missing cells: 0. Exact duplicate rows: 16,099. Repeated feature rows: 21,568. Controls with exposure: 0.

Maximum absolute standardized feature imbalance: 0.0478. Validation assignment-prediction AUC: 0.5097. These diagnostics reveal no large measured mean imbalance, but cannot prove randomized exchangeability after privacy selection. Retain duplicate rows and group identical feature vectors for splitting and uncertainty.

## 3. Freeze partitions and compare candidates

```bash
python -m lab.pipeline
```

Train: 840,310; validation: 279,569; final test: 279,824. No feature group crosses partitions. Only `f0`–`f11` are predictors. Two regularized logistic response models form the baseline. Two histogram-boosted T-learners allow nonlinear interactions.

| Candidate | Validation AUQC (per 1,000) |
|---|---:|
| linear | 0.464 |
| boosted_7 | 0.397 |
| boosted_15 | 0.308 |

Selection: **linear**. Persisted before final outcome evaluation. A more flexible model did not justify replacing the simple baseline.

## 4. Evaluate the frozen policies

The evaluation set includes 41,706 controls (80 conversions) and 238,118 treated users (706 conversions). Overall conversion lift is 0.105 percentage points, 95% CI 0.057 to 0.152.

Use arm-normalized policy outcomes, not a raw difference of conversion counts. At full reach all policies recover the overall effect; at zero reach all values are zero. The random policy is the depth times the overall effect. Independent SQL recomputation checks these endpoints and the 20% selected-policy estimate in `scripts/validate_outputs.py`.

See the [evidence charts](index.html#targeting) for cumulative gain, Qini and interval tables. Selected uplift equals the linear baseline because that model won validation. At 20% reach the paired difference versus propensity is -0.055 per 1,000 (95% CI -0.199 to 0.088). The correct conclusion is uncertainty about superiority, not a guaranteed uplift-model win.

## 5. Translate to a scenario

```text
100,000 eligible users × 0.001000928 gain per eligible user
= 100.1 estimated extra conversions at 20% reach
net value = extra conversions × $100 - 20,000 treated users × $0.20
```

The [budget lab](index.html#simulator) carries the measured interval into the scenario and caps reach at the requested budget. This assumes future users behave like the benchmark; it does not measure actual revenue.

## 6. Reproduce the checks and build

```bash
python -m pytest -q
python scripts/validate_outputs.py
python scripts/build_site.py
python -m http.server 8000 --directory outputs/site
```

For a faster execution check after acquisition, run `python -m lab.pipeline --smoke`. Smoke outputs go to `work/smoke-results` and never overwrite portfolio results. The first smoke sample still scans the complete compressed source; subsequent smoke runs reuse its verified cache. Browser checks are described in the README.
