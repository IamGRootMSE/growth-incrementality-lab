"""Build the portable site and evidence-derived companion documents."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parents[1]

def write_documents(r):
    a, u = r['ate'], r['curves']['uplift']['points'][4]
    p, random = r['curves']['propensity']['points'][4], r['curves']['random']['points'][4]
    diff = r['paired_uplift_difference_at_20pct']['propensity']
    vsrandom = r['paired_uplift_difference_at_20pct']['random']
    f = lambda n: f'{n:,.0f}'
    report_dir = ROOT / 'outputs/reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    memo = f'''# Decision memo

**Growth Incrementality & Targeting Lab · Independent project · 23 September 2026**

## Decision

Advance uplift and conversion-propensity targeting to a fresh randomized policy comparison at equal reach. Do not claim that uplift improves on propensity or deploy from this benchmark alone.

## Evidence

The official Criteo v2.1 release yielded a seeded 10% sample of **{f(r['provenance']['sample_rows'])} users**. Feature-group isolation reserved **{f(r['splits']['test']['rows'])}** users for final evaluation. Validation selected the **{r['selection']['selected']} T-learner** over two boosted candidates.

Advertising assignment increased final-holdout conversion by **{a['estimate']*100:.3f} percentage points** (95% CI {a['low']*100:.3f}–{a['high']*100:.3f}). At the prespecified 20% reach, additional conversions per 1,000 eligible users were:

| Policy | Estimate | 95% interval |
|---|---:|---:|
| Selected uplift | {u['estimate']*1000:.2f} | {u['low']*1000:.2f} to {u['high']*1000:.2f} |
| Conversion propensity | {p['estimate']*1000:.2f} | {p['low']*1000:.2f} to {p['high']*1000:.2f} |
| Random | {random['estimate']*1000:.2f} | {random['low']*1000:.2f} to {random['high']*1000:.2f} |

The paired uplift-minus-propensity difference was **{diff['estimate']*1000:.3f}** (95% CI {diff['low']*1000:.3f} to {diff['high']*1000:.3f}); superiority is not established. Uplift-minus-random was **{vsrandom['estimate']*1000:.3f}** ({vsrandom['low']*1000:.3f} to {vsrandom['high']*1000:.3f}).

## Budget implication — hypothetical only

For 100,000 eligible users, 20% reach, $0.20 per treated user and $100 per incremental conversion, the selected policy implies **{u['estimate']*100000:.1f}** extra conversions, **$4,000** spend and **${u['estimate']*10000000-4000:,.0f}** net incremental value (95% sampling interval **${u['low']*10000000-4000:,.0f} to ${u['high']*10000000-4000:,.0f}**). These are scenarios, not observed revenue or profit.

## Boundaries and next step

Criteo's privacy subsampling changes incrementality. Projected features, pooled tests, missing experiment IDs and only {r['test_arm_conversions']['0']} control conversions limit causal interpretation and precision. Pointwise intervals exclude model-selection and transport uncertainty. Prespecify audience, conversion window, cost assumptions and a minimum policy difference; then randomize equal-reach policies with contamination and margin guardrails before rollout.

Source: Criteo AI Lab; Diemert et al. (2018), *A Large Scale Benchmark for Uplift Modeling*. Data-derived report: CC BY-NC-SA 4.0. No Criteo endorsement.
'''
    (report_dir / 'decision-memo.md').write_text(memo, encoding='utf-8')
    walkthrough = f'''# Analysis walkthrough

This is a readable companion to the executable pipeline, with results from the acquired Criteo v2.1 file. It is not a synthetic example. Run commands from the repository root after installing `requirements.lock` in Python 3.12.

## 1. Acquire and verify

```bash
python -m lab.acquire
```

`lab/acquire.py` checks SHA-256 before the file can enter analysis. The official file contains {f(r['provenance']['source_rows'])} rows. The pipeline scans all rows with a common inclusion probability of 10%, yielding {f(r['provenance']['sample_rows'])}. It records full-source arm counts; no prefix sample or outcome enrichment is used.

## 2. Audit data in SQL and Python

```sql
SELECT treatment, count(*) AS users, sum(conversion) AS conversions,
       avg(conversion) AS conversion_rate
FROM sample GROUP BY treatment ORDER BY treatment;
```

Executed sample: {f(r['quality']['arms'][0]['users'])} controls with {f(r['quality']['arms'][0]['conversions'])} conversions, and {f(r['quality']['arms'][1]['users'])} treated users with {f(r['quality']['arms'][1]['conversions'])} conversions. Missing cells: {r['quality']['missing_cells']}. Exact duplicate rows: {f(r['quality']['exact_duplicate_rows'])}. Repeated feature rows: {f(r['quality']['repeated_feature_rows'])}. Controls with exposure: {r['quality']['control_exposures']}.

Maximum absolute standardized feature imbalance: {r['quality']['max_absolute_smd']:.4f}. Validation assignment-prediction AUC: {r['assignment_validation_auc']:.4f}. These diagnostics reveal no large measured mean imbalance, but cannot prove randomized exchangeability after privacy selection. Retain duplicate rows and group identical feature vectors for splitting and uncertainty.

## 3. Freeze partitions and compare candidates

```bash
python -m lab.pipeline
```

Train: {f(r['splits']['train']['rows'])}; validation: {f(r['splits']['validation']['rows'])}; final test: {f(r['splits']['test']['rows'])}. No feature group crosses partitions. Only `f0`–`f11` are predictors. Two regularized logistic response models form the baseline. Two histogram-boosted T-learners allow nonlinear interactions.

| Candidate | Validation AUQC (per 1,000) |
|---|---:|
''' + '\n'.join(f'| {k} | {v*1000:.3f} |' for k,v in r['selection']['validation_auqc'].items()) + f'''

Selection: **{r['selection']['selected']}**. Persisted before final outcome evaluation. A more flexible model did not justify replacing the simple baseline.

## 4. Evaluate the frozen policies

The evaluation set includes {f(r['test_arm_counts']['0'])} controls ({r['test_arm_conversions']['0']} conversions) and {f(r['test_arm_counts']['1'])} treated users ({r['test_arm_conversions']['1']} conversions). Overall conversion lift is {a['estimate']*100:.3f} percentage points, 95% CI {a['low']*100:.3f} to {a['high']*100:.3f}.

Use arm-normalized policy outcomes, not a raw difference of conversion counts. At full reach all policies recover the overall effect; at zero reach all values are zero. The random policy is the depth times the overall effect. Independent SQL recomputation checks these endpoints and the 20% selected-policy estimate in `scripts/validate_outputs.py`.

See the [evidence charts](index.html#targeting) for cumulative gain, Qini and interval tables. Selected uplift equals the linear baseline because that model won validation. At 20% reach the paired difference versus propensity is {diff['estimate']*1000:.3f} per 1,000 (95% CI {diff['low']*1000:.3f} to {diff['high']*1000:.3f}). The correct conclusion is uncertainty about superiority, not a guaranteed uplift-model win.

## 5. Translate to a scenario

```text
100,000 eligible users × {u['estimate']:.9f} gain per eligible user
= {u['estimate']*100000:.1f} estimated extra conversions at 20% reach
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
'''
    (report_dir / 'walkthrough.md').write_text(walkthrough, encoding='utf-8')
    return report_dir

def page(title, content):
    body = markdown.markdown(content, extensions=['tables', 'fenced_code', 'toc'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} · Growth Lab</title><link rel="stylesheet" href="style.css"><link rel="icon" href="favicon.svg"></head><body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="index.html"><span class="mark">↗</span> GROWTH LAB</a><nav aria-label="Main navigation"><a href="index.html#evidence">Evidence</a><a href="index.html#simulator">Budget lab</a><a href="methodology.html">Methodology</a><a href="https://github.com/IamGRootMSE/growth-incrementality-lab">Code ↗</a></nav></header><main id="main" class="document">{body}</main><footer>Independent project · Criteo / Diemert et al. (2018) · <a href="provenance.html">Data provenance</a> · Data-derived reports: <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>. No endorsement.</footer></body></html>'''

def build(destination=None):
    source = ROOT / 'outputs/analysis/results.json'
    r = json.loads(source.read_text())
    if r['mode'] != 'empirical':
        raise ValueError('Portfolio publishing requires empirical full-analysis results')
    out = Path(destination) if destination else ROOT / 'outputs/site'
    out.mkdir(parents=True, exist_ok=True)
    for p in (ROOT/'site').iterdir():
        if p.is_file():
            shutil.copy2(p, out / p.name)
    data = out/'data'
    data.mkdir(exist_ok=True)
    shutil.copy2(source, data/'results.json')
    (data/'results.js').write_text('window.LAB_RESULTS = '+json.dumps(r, allow_nan=False)+';\n', encoding='utf-8')
    report_dir = write_documents(r)
    memo_pdf = report_dir/'decision-memo.pdf'
    if memo_pdf.exists():
        shutil.copy2(memo_pdf, out/'decision-memo.pdf')
    documents = [(ROOT/'docs'/f'{name}.md',name) for name in ['methodology','provenance','design-notes']]
    documents += [(report_dir/f'{name}.md',name) for name in ['decision-memo','walkthrough']]
    for src,name in documents:
        (out/f'{name}.html').write_text(page(name.replace('-',' ').title(),src.read_text(encoding='utf-8')),encoding='utf-8')
    (out/'.nojekyll').write_text('')
    manifest = {str(p.relative_to(out)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'build-manifest.json'}
    (out/'build-manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Built {len(manifest)} static files at {out}')
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output')
    build(parser.parse_args().output)
