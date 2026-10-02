# Model design notes

## Estimand and model choice

Conversion prediction can favor users who would buy without advertising. A T-learner fits two response surfaces and ranks their difference. Individual effects are unobservable; evaluate policies using treatment/control outcomes rather than individual uplift accuracy. The linear model won validation in this benchmark, but its advantage over propensity targeting was not established on the final holdout.

## Allocation and rare outcomes

The released allocation is approximately 85/15. Equal-arm downsampling wastes information and changes the target population unless adjusted. Class weighting can distort calibrated conversion probabilities. Sampling uses the same inclusion probability in both arms and policy contrasts normalize by observed arm sizes. Few control conversions constrain model flexibility and precision; subtracting noisy predictions compounds error.

## Identification limits

The source comes from randomized experiments, but nonuniform privacy sampling and pooled experiments limit interpretation. Marginal exchangeability is an assumption for the released benchmark; original campaign lift cannot be recovered. Selection may depend on features or outcomes. Balance diagnostics can flag problems but cannot establish identification. Deployment requires a new policy-level randomized experiment in the intended population.

## Leakage and duplicates

Only anonymized covariates enter models; exposure and visit are excluded. Identical feature vectors remain in one partition. Scalers fit on training arms, model selection uses validation, and selection is persisted before final evaluation. Duplicate rows are retained because no user IDs establish whether they are repeated observations or distinct people. Feature groups define split isolation and uncertainty clusters; hidden user/advertiser clustering remains unresolved.

## Policy value and uncertainty

For a selected audience, divide treated conversions by all treated users and subtract selected control conversions divided by all controls. Full reach recovers the arm-mean contrast; zero reach is zero; random reach q has expected value q times the overall contrast. Tests verify these identities.

Clustered influence-function intervals describe evaluation-sample uncertainty conditional on fitted models and observed rankings. Paired differences retain covariance. These are pointwise intervals, not simultaneous bands or individual-effect intervals. They exclude retraining, selection, future thresholds and business economics. Bootstrap retraining and cross-fitted doubly robust alternatives require a new evaluation protocol.

## Decision boundaries and future validation

Selecting the maximum on the final-test curve would introduce optimism. The interface explores scenarios; a deployment threshold must be selected on validation and evaluated independently. Capacity, fatigue and opportunity cost belong in the policy objective. Projected covariates do not support demographic personas or causal feature explanations.

A future experiment should prespecify audience, assignment unit/probability, conversion window and spend policy. Compare equal-reach uplift and propensity policies, with a no-ad holdout where feasible. Separate assignment from exposure, prevent cross-channel contamination and retain user/experiment IDs for clustering. Size the policy contrast using pilot variance and an agreed MDE. Prespecify margin, conversion, unsubscribe and frequency guardrails and analyze intention to treat. Budget outputs use hypothetical transport and cost assumptions; this work is independent research, not a deployed commercial campaign.
