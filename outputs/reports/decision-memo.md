# Decision memo

**Growth Incrementality & Targeting Lab · Independent project · 23 September 2026**

## Decision

Advance uplift and conversion-propensity targeting to a fresh randomized policy comparison at equal reach. Do not claim that uplift improves on propensity or deploy from this benchmark alone.

## Evidence

The official Criteo v2.1 release yielded a seeded 10% sample of **1,399,703 users**. Feature-group isolation reserved **279,824** users for final evaluation. Validation selected the **linear T-learner** over two boosted candidates.

Advertising assignment increased final-holdout conversion by **0.105 percentage points** (95% CI 0.057–0.152). At the prespecified 20% reach, additional conversions per 1,000 eligible users were:

| Policy | Estimate | 95% interval |
|---|---:|---:|
| Selected uplift | 1.00 | 0.56 to 1.45 |
| Conversion propensity | 1.06 | 0.60 to 1.51 |
| Random | 0.21 | 0.11 to 0.30 |

The paired uplift-minus-propensity difference was **-0.055** (95% CI -0.199 to 0.088); superiority is not established. Uplift-minus-random was **0.792** (0.435 to 1.149).

## Budget implication — hypothetical only

For 100,000 eligible users, 20% reach, $0.20 per treated user and $100 per incremental conversion, the selected policy implies **100.1** extra conversions, **$4,000** spend and **$6,009** net incremental value (95% sampling interval **$1,566 to $10,453**). These are scenarios, not observed revenue or profit.

## Boundaries and next step

Criteo's privacy subsampling changes incrementality. Projected features, pooled tests, missing experiment IDs and only 80 control conversions limit causal interpretation and precision. Pointwise intervals exclude model-selection and transport uncertainty. Prespecify audience, conversion window, cost assumptions and a minimum policy difference; then randomize equal-reach policies with contamination and margin guardrails before rollout.

Source: Criteo AI Lab; Diemert et al. (2018), *A Large Scale Benchmark for Uplift Modeling*. Data-derived report: CC BY-NC-SA 4.0. No Criteo endorsement.
