# Methodology

## A decision, not just a score

The decision is who should be assigned to an advertising program at a fixed reach. The unit is a released user row; the outcome is conversion. The estimand is incremental conversions under a policy relative to assigning nobody, expressed per eligible user. Multiplying by 1,000 provides readable comparison units. Conversion propensity asks who is likely to buy when treated; uplift asks whose conversion probability changes with assignment.

## Design and leakage controls

The source is the official corrected Criteo v2.1 release. Read the [provenance and dictionary](provenance.html) before interpreting results. Covariates are strictly `f0`–`f11`. Conversion, visit, exposure, assignment and row identifiers never enter the prediction matrix. Actual exposure and visits may occur after assignment and would leak post-treatment information.

Identical feature vectors stay in a single split, independent of their outcome or treatment. The expected allocation is 60/20/20. Scalers fit within training-arm pipelines. No early stopping uses the final holdout. Three prespecified uplift candidates are trained only on training rows. Validation area above random selects one model; the selection artifact is saved before final outcome evaluation. There is no final-holdout refitting, hyperparameter search, or cutoff optimization. Descriptive data checks cover the sample but do not drive model selection.

## The candidate models

1. **Simple baseline:** T-learner with separate regularized logistic regressions for treated and control users. Each arm has a train-fitted standard scaler, `C=1` and maximum 500 iterations. Uplift is predicted treated conversion probability minus predicted control conversion probability.
2. **More flexible approach:** T-learner using scikit-learn histogram gradient boosting. Two candidate leaf limits (7 and 15), 140 iterations, learning rate 0.07, minimum 200 rows per leaf, L2 regularization 10, fixed seed and no early stopping. Nonlinear interactions are possible, but control-arm rare events constrain learning. Flexibility is not a guarantee of better ranking.
3. **Propensity comparator:** the treated-arm conversion probability from the prespecified 7-leaf boosted model. This is conversion propensity, not treatment propensity. It is not retuned on final outcomes.
4. **Random comparator:** a stochastic policy assigning every eligible user with probability equal to reach. We use its expected value rather than a noisy single random ranking.

Maintained library: [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html); the project pins 1.6.1 for reproducibility. “Stronger approach” means greater modeling flexibility, not a promised performance claim. Final results explicitly report when the simpler model wins.

## Unequal assignment and overall effect

No 50/50 assumption is imposed. The original assignment probabilities are not provided and approximately 85% of the released rows are treated. The overall estimator is the difference in arm-specific conversion means on final holdout:

```
ATE = mean(Y | T=1) - mean(Y | T=0)
```

This is an intent-to-treat benchmark contrast. It estimates the effect of assignment only under the benchmark's exchangeability, consistency, overlap and no-interference assumptions. Privacy selection prevents interpreting it as the original production effect. A treatment-on-the-treated estimate is not attempted.

## Policy value and curves

For a fixed rank-based policy π at reach q, define πᵢ=1 for selected users and 0 otherwise; for random targeting πᵢ=q. Let p=n₁/n be the observed evaluation allocation. We use the marginal Hájek/IPW contrast:

```
G(q) = sum(T × π × Y) / n1 - sum((1-T) × π × Y) / n0
     = mean[π × Y × (T/p - (1-T)/(1-p))]
Q(q) = G(q) - q × G(1)
AUQC = integral from 0 to 1 of Q(q) dq
```

The denominator is the entire eligible audience after treatment-probability adjustment, not the selected subgroup. Both policies and charts use a fixed 0%, 5%, …, 100% depth grid. Nonrandom selected counts round to the nearest row; ties break in source order, without outcomes. Curves can be nonmonotonic and negative. AUQC uses trapezoidal integration over the 21 requested depths; this is unnormalized area above random, not a normalized library-specific score. The selected linear baseline and selected uplift curves coincide when linear wins validation.

Unequal-arm adjustment corrects marginal allocation, not unknown feature-dependent selection probabilities. Small feature imbalances remain. Original experiment IDs and sampling weights are unavailable, so neither covariate-specific randomization nor transportability can be established. The result supports a benchmark comparison and a prospective test proposal.

## Uncertainty and comparisons

For z=πY and arm means μ₁, μ₀, the estimated influence value is:

```
IFᵢ = Tᵢ/p × (zᵢ-μ1) - (1-Tᵢ)/(1-p) × (zᵢ-μ0)
SE² = [K/(K-1)] × sum(cluster_sum(IF)²) / n²
95% interval = estimate ± 1.96 × SE
```

Feature-group clustering handles repeated anonymized covariates. Policy differences use paired influence differences on the same users, not overlap of separate intervals. Qini subtracts the full-population influence function times reach; AUQC integrates it. Random targeting has exactly zero Qini by definition.

These are pointwise asymptotic intervals conditional on fitted models and observed ranking, not simultaneous bands. They do not capture refitting variation, validation-selection uncertainty, estimated future quantile thresholds, unknown advertiser clusters or transport uncertainty. Rare control conversions make shallow-depth intervals fragile; avoid choosing a policy from isolated peaks. The 20% comparison is prespecified for reporting. Additional depth comparisons are exploratory and not multiplicity-adjusted.

## Quality checks

The pipeline verifies physical schema, binary domains, missingness, finite covariates, duplicate rows, repeated covariate groups, per-arm outcome/visit/exposure rates, and exposure among controls. Feature balance uses standardized mean differences, with the average of arm-specific variances in the denominator. A logistic assignment classifier is trained on training data and evaluated on validation for a predictive balance diagnostic. Neither a small SMD nor an AUC near 0.5 validates unobserved randomization. A deviation from 50/50 is not treated as a sample-ratio mismatch; the original assignment design is unavailable.

## Budget scenarios

```
affordable reach = budget / (audience × assumed cost per treated user)
effective reach = floor(min(requested reach, affordable reach) × 20) / 20
extra conversions = audience × G(effective reach)
spend = floor(audience × effective reach) × assumed cost
net incremental value = extra conversions × assumed conversion value - spend
break-even cost = extra conversions × assumed conversion value / treated users
```

Cost is per user assigned to the policy, not per impression or realized exposure. Value is per incremental conversion, not observed order value or margin. Zero-cost scenarios are permitted; a zero audience is invalid. Negative estimates and net values remain visible. The simulator reuses the exact evaluated grid without interpolating confidence bounds or optimizing on holdout outcomes. For very small hypothetical audiences, row rounding is approximate and transport remains an assumption.

## Reproducibility and scope

Python performs acquisition, sampling, modeling and estimation; DuckDB provides an independently inspectable SQL audit. Static HTML/CSS/JavaScript reads precomputed aggregate JSON. No backend, paid API, tracking or cookies is needed. Deterministic seeds, pinned dependencies, data hashes and cached sample hashes support replay. Runtime and floating point details can vary across machines. Synthetic fixtures occur only in automated estimator and training tests; portfolio findings come from the acquired source.

The portfolio complements descriptive payments analytics by demonstrating prospective intervention design. It does not invent a connection to payment records or claim production deployment, realized revenue, or validated individual treatment effects.
