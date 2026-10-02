"""Portable, accessible report built only from executed experiment results."""
from html import escape


def render(data):
    sections = []
    for name, result in data['scenarios'].items():
        rows = ''
        for metric, m in result['metrics'].items():
            scale = 100 if metric == 'converted' else 1
            unit = 'pp' if metric == 'converted' else '$ / assigned user'
            rows += (f'<tr><th>{escape(metric)}</th><td>{m["estimate"]*scale:+.3f} {unit}</td>'
                     f'<td>[{m["low"]*scale:+.3f}, {m["high"]*scale:+.3f}]</td></tr>')
        sections.append(f'<section><h2>{escape(name.replace("_", " ").title())}</h2>'
                        f'<p class="decision">{result["decision"]}</p>'
                        f'<p>{result["counts"][0]:,} control / {result["counts"][1]:,} treatment; '
                        f'SRM p = {result["srm_p"]:.4g}</p>'
                        + (f'<div class="scroll"><table><caption>Treatment minus control; simultaneous intervals</caption>'
                           f'<thead><tr><th>Metric</th><th>Difference</th><th>Interval</th></tr></thead>'
                           f'<tbody>{rows}</tbody></table></div>' if rows else
                           f'<p>Readout blocked: {escape(", ".join(result["blockers"]))}</p>') + '</section>')
    plan = next(iter(data['scenarios'].values()))
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Experiment decision toolkit</title>
<style>body{{margin:0;background:#f3f6f7;color:#18313a;font:17px/1.6 system-ui}}main{{max-width:1060px;margin:auto;padding:32px 20px}}h1{{font-size:clamp(32px,5vw,52px);line-height:1.1}}h2{{font-size:25px}}.label{{color:#8d3900;font-weight:700}}section{{background:white;border:1px solid #ccd8db;border-radius:12px;padding:24px;margin:24px 0}}.decision{{font-weight:800;color:#126454;overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%;text-align:left}}th,td{{padding:10px;border-bottom:1px solid #dce3e6}}caption{{text-align:left;font-size:14px}}.scroll{{overflow:auto}}footer{{border-top:2px solid #126454;padding-top:20px}}code{{overflow-wrap:anywhere}}</style>
<main><p class="label">INDEPENDENT PORTFOLIO · SYNTHETIC SCENARIOS</p>
<h1>A conversion lift is only the start of a decision.</h1>
<p>Fixed-horizon experiment readouts join conversion evidence with revenue and contribution-margin guardrails. Every assigned user stays in the denominator.</p>
<section><h2>Design before results</h2><p>Baseline 20%; detectable absolute lift 3 percentage points; power 80%; familywise alpha 5%. Equal allocation requires <strong>{plan['planned_per_arm']:,} users per arm</strong>. Enrollment is planned for {plan['enrollment_days']} days, then 28 days of outcome follow-up.</p>
<p>The demo uses 8,000 users per arm, above the minimum: at 1,000 total eligible users/day, allow 21 whole-week enrollment days plus 28 days follow-up. This sample is fixed in advance, never extended after inspecting significance.</p>
<p>Revenue noninferiority floor: −$0.50 per assigned user. Contribution-margin floor: −$0.25. These are hypothetical planning choices. Conversion power alone does not guarantee guardrail power. Welch intervals are large-sample approximations; Bonferroni targets at least 95% family coverage when the individual intervals are valid.</p></section>
{''.join(sections)}
<footer><h2>What this can and cannot establish</h2><p>SHIP_CANDIDATE means the synthetic readout cleared the prespecified statistical gates; operational review and a staged rollout are still needed. Inconclusive means the data do not establish the required decision, not that the effect is zero.</p>
<p>Independent user randomization, one final look, complete 28-day outcomes, and reliable instrumentation are assumed. Clustered practitioners, interference, heavy tails, multiple variants, or sequential monitoring require a different design. SRM is an integrity alarm, not proof of randomization.</p>
<p>All scenarios were generated with seed {data['seed']}; no patient, employer, or Criteo data. Economic values are invented. Reproduce: <code>python -m lab.experiment</code>. Inspect <a href="results.json">executed JSON evidence</a>.</p></footer></main></html>'''
