# Data provenance & dictionary

## Authoritative source

Verified on 23 September 2026: [Criteo AI Lab dataset page](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) and the [official Criteo Hugging Face repository](https://huggingface.co/datasets/criteo/criteo-uplift). Download uses the official organization's `criteo-research-uplift-v2.1.csv.gz`. Its [Git LFS manifest](https://huggingface.co/datasets/criteo/criteo-uplift/blame/main/criteo-research-uplift-v2.1.csv.gz) supplies the expected checksum.

```
URL: https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz
SHA-256: 2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc
Compressed size: 311,422,618 bytes
Rows: 13,979,592
```

The download URL uses `main`, but the pipeline requires this exact content hash. A changed file fails closed. `python -m lab.acquire` downloads into ignored `data/raw/`; no login is required. The source page's older 25-million-row description and “11 features” prose refer to an earlier release and conflict with its enumerated fields. This project uses the revised 13,979,592-row file, verifies the physical 16-column header, and includes all 12 `f0`–`f11` features. It never combines versions.

## License and attribution

The dataset is licensed under [Creative Commons Attribution–NonCommercial–ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The original source includes a disclaimer of warranties. Data-derived aggregate results and reports here carry the same license, preserve attribution, and disclose modifications: Bernoulli sampling, feature-group partitioning, estimation and aggregation. No raw or row-level data is redistributed. Independent educational research; not sponsored or endorsed by Criteo. Separate original software is MIT licensed; that does not relicense the data. Obtain appropriate permission before commercial reuse outside the dataset license.

Cite: Eustache Diemert, Artem Betlei, Christophe Renaudin and Massih-Reza Amini (2018), *A Large Scale Benchmark for Uplift Modeling*, AdKDD & TargetAd workshop at KDD. [Paper](https://openreview.net/pdf?id=Q83-QeTB9lS) · [Authors' benchmark code](https://github.com/criteo-research/large-scale-ITE-UM-benchmark).

## Construction and limitations

The release pools incrementality tests in which control users were withheld from advertising eligibility. Treatment does not guarantee exposure. Criteo reports nonuniform privacy subsampling that prevents reconstruction of original lift, plus anonymization and random projection of features. Its erratum identifies advertiser-related leakage in the first release and introduces a corrected version. The revised release is still a benchmark, not an unmodified production experiment.

There are no user identifiers, advertiser identifiers, experiment probabilities, timestamps, geography, spending or revenue fields. We cannot verify assignment implementation, interference, outcome timing, cross-advertiser heterogeneity or longitudinal independence. Mean balance and assignment predictability do not prove randomization. Constant marginal assignment adjustment is a benchmark working assumption; it cannot undo unknown selection effects. No original-population ATE, individual causal truth, or production ROI is identified here.

## Data dictionary

| Field | Type | Meaning | Modeling use |
|---|---|---|---|
| f0–f11 | dense float | Anonymized, projected covariates; no business labels | Only allowed predictors |
| treatment | binary | Assignment: 1 eligible for advertising, 0 withheld | Arm definition, not a predictor |
| conversion | binary | Released conversion indicator | Primary outcome |
| visit | binary | Released visit indicator | Descriptive audit only; excluded from predictors |
| exposure | binary | Whether actually exposed | Audit only; post-assignment, excluded |
| row_id | generated integer | Zero-based position in immutable source | Traceability and stable ordering; never a predictor |
| group | generated uint64 | Hash of the 12-feature vector | Split isolation and variance clustering; not a user ID |
| split | generated label | Train, validation or test | Pipeline control only |

## Sampling and duplicate handling

Seed 20260923 drives a 10% Bernoulli inclusion draw for every row in the entire source, processed in fixed 200,000-row chunks. The same inclusion probability applies to both treatment arms and all outcomes. It preserves the source allocation in expectation rather than forcing 50/50 or enriching conversions. Source and sample arm counts are in the aggregate results. Smoke mode uses 0.4% with the same seed; it is for execution checks and cannot replace portfolio evidence.

Repeated released rows are not automatically deleted: anonymization can make distinct users identical. Exact duplicate counts and feature-duplicate counts are reported separately. All identical feature vectors share a split through a seeded BLAKE2b hash bucket (60% train, 20% validation, 20% test in expectation). Intervals cluster on these feature groups. This conservative grouping reduces leakage but cannot recover hidden user identities. Rates remain row-weighted, preserving the released population.

## Acquisition receipt

The executed source and sample hashes, full-source arm counts, sample probability and realized sample size are recorded in [aggregate results](data/results.json). Source schema and full row count are asserted in code. Raw downloads, cached samples, predictions and split memberships stay outside Git. All exported results are aggregate.
