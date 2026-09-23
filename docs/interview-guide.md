# Interview guide

## A 60-second explanation

“This independent project asks whom advertising persuades, rather than whom it reaches. I used Criteo's corrected uplift benchmark, separated feature groups into train, validation and final holdout, and compared random targeting, conversion propensity and two uplift model families. The linear uplift model won validation. Its final-holdout targeting beat random at the prespecified 20% depth but did not establish an advantage over conversion propensity. I built a static decision tool that carries sampling uncertainty into explicitly hypothetical budget scenarios. The right next step is a new randomized policy test, not a production revenue claim.”

## Why this is different from conversion prediction

A conversion model can favor users who would buy anyway. A T-learner estimates two response surfaces and ranks their difference. Individual causal effects cannot be observed because each user reveals one outcome. Evaluate the ranking through randomized treatment/control outcomes, not “uplift prediction accuracy.”

## Why not split 50/50 or rebalance classes?

Treatment assignment is about 85/15 in this release. Downsampling treated users to equalize arms wastes information and changes the sample target unless weighted. Class-weighting rare conversion labels can distort calibrated probabilities, so it is not used. The sample uses identical inclusion probability in both arms; estimators normalize by observed arm sizes.

## Why did the simple model win?

There are few control conversions relative to model flexibility. Smooth regularized response surfaces can yield a better difference ranking than two individually flexible models. Subtracting noisy probabilities compounds error. Validation, rather than model prestige, decides. I would investigate cross-fitted doubly robust learners and causal forests as future candidates, with a new evaluation set for honest comparison.

## Is this really causal?

The source originates from randomized incrementality experiments, but the public release has nonuniform privacy sampling and pooled experiments. The project makes an intent-to-treat benchmark comparison under marginal exchangeability; it cannot recover original campaign lift. Unknown selection could depend on features or outcomes. Balance diagnostics help identify obvious issues, not prove identification. A new policy-level randomized experiment in the deployment population is necessary.

## How was leakage controlled?

Only anonymized covariates enter models. Exposure and visit are explicitly blocked. Identical feature vectors stay together across splits. Scalers fit on training arms, candidates are scored on validation, selection is persisted before test evaluation, and no test-driven cutoff is presented as optimal. Tests perturb excluded fields and reject overlapping groups or contaminated matrices.

## Why retain duplicates?

Rows have no user IDs. Identical projected feature values and binary labels can reflect distinct people; dropping them changes the released population. I report exact-row and feature duplicates, keep feature groups together and cluster uncertainty on those groups. Hidden repeated users and advertiser clustering remain unresolved.

## Explain the estimator on a whiteboard

For the selected audience, sum converted treated users divided by all treated users and subtract converted control users divided by all control users. This is a whole-population policy contrast with unequal assignment adjustment. At full reach it becomes the difference in arm means. At zero reach it is zero. A random policy at 20% equals 20% of the overall contrast in expectation. These identities have tests.

## What do the intervals cover?

Influence-function cluster sandwich intervals describe evaluation-sample uncertainty with fixed fitted models and observed rankings. Paired differences retain covariance across competing policies. They are not individual effect intervals, not simultaneous bands, and do not cover retraining, source selection or future business economics. Bootstrap retraining and policy threshold variability would be useful extensions with more compute and a prespecified evaluation protocol.

## Why not choose the best-looking test depth?

Scanning a noisy curve and reporting its maximum introduces optimism. The interface is a scenario explorer; it does not claim an optimal depth. A real deployment rule should be chosen from validation under an agreed objective and then measured once on independent randomized data. Capacity constraints, contact fatigue and opportunity cost should enter that policy design.

## What would the next experiment look like?

Prespecify the eligible audience, treatment unit, conversion window, assignment probabilities and spend policy. Randomize users to equal-reach uplift versus propensity policies, with a no-ad holdout if feasible. Prevent cross-channel contamination, log assignment separately from exposure, and retain user/experiment IDs for clustering. Power the policy difference using pilot variance and a business-defined minimum detectable effect; do not invent a sample size from this privacy-altered benchmark. Include net margin, conversion, unsubscribe and frequency guardrails. Analyze intention to treat and commit the decision rule before outcomes mature.

## Challenges to acknowledge

- Strong targeting compared with random can occur even when conversion propensity performs just as well as uplift.
- AUC for ordinary conversion prediction is not an uplift metric.
- A positive overall average does not prove every selected user benefits.
- The projected features do not support demographic personas or causal feature explanations.
- Budget outputs assume transport of benchmark response rates and user-level costs; neither is observed.
- This is independent research and engineering, not a deployed commercial campaign.
