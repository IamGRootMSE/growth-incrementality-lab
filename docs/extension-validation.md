# October 2, 2026 validation

Executed on RONIN with Python 3.12.14 in a new isolated environment installed from `requirements.lock`. `pip check` found no broken requirements.

- `python -m pytest -q --basetemp=work/pytest-temp`: **24 passed**. The workspace-local temp option avoids an existing Windows shared-temp permission conflict; it does not skip tests.
- `python -m lab.experiment`: generated all four synthetic cases; decisions were SHIP_CANDIDATE, DO_NOT_SHIP_HARM, INCONCLUSIVE and INVALID respectively.
- `python scripts/check_experiment_report.py`: passed at 1440px and 390px; matched every effect estimate and decision to JSON, checked evidence links, overflow and browser errors. Screenshots in `outputs/experiment/` were visually reviewed.
- `python scripts/build_site.py` and `python scripts/browser_check.py`: passed the original seven-route, desktop/mobile, keyboard, budget-boundary and 20 scenario arithmetic checks after integrating the extension link.
- `python -m lab.pipeline`: reran the full existing analysis from the verified local official Criteo source cache. SHA-256 `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`; 311,422,618 compressed bytes; train/validation/test counts 840,310 / 279,569 / 279,824. Linear model selected again. Existing substantive results reproduced; elapsed runtime is machine-specific.
- `python scripts/validate_outputs.py`: passed independent DuckDB reconciliation of overall and policy effects, feature-group isolation, unique source positions, interval ordering and endpoint identities.

Raw/cache files remain ignored by Git. New experiment figures are synthetic; the Criteo benchmark remains separately attributed. Local validation is distinct from GitHub Actions status; review the PR checks for the published commit.

## Follow-up defensive review

A one-shot iterator previously bypassed maturity checking because the input had already been consumed. The failure was reproduced (immature list: INVALID; same rows as generator: SHIP_CANDIDATE). The gate now reads the validated arm collections. A regression verifies list/generator equivalence for mature and immature data, including empty metrics for blocked results. The published list-based fixture results are unchanged.

The full updated suite passes **26 tests**. CI and the future Pages build regenerate the experiment into a separate directory, compare against the committed JSON, and only then copy regenerated artifacts into the build. Snapshot comparisons require exact structure, strings, integer counts and input hashes; float comparisons permit only 1e-12 relative/absolute roundoff. These extension snapshots contain no runtime, timestamp or platform metadata. Comparator tests reject material numeric changes, schema drift, boolean/count substitutions, changed decisions, array-length changes and nonfinite values.
