/* All evidence is precomputed. Only explicit hypothetical scenarios run here. */
'use strict';
const R = window.LAB_RESULTS;
const fmt = (n, d=0) => Number(n).toLocaleString('en-US', {maximumFractionDigits:d, minimumFractionDigits:d});
const byId = id => document.getElementById(id);
const labels = {random:'Random targeting', propensity:'Conversion propensity', baseline:'Linear uplift baseline', uplift:'Selected uplift'};
const colors = {random:'#5c6467', propensity:'#3658a1', baseline:'#9b4f27', uplift:'#006c64'};
const dash = {random:'2 5', propensity:'8 4', baseline:'9 3 2 3', uplift:''};
function chart(target, qini=false) {
  const W=510,H=330,L=54,T=22,B=52,RR=15;
  const pts = Object.values(R.curves).flatMap(c=>c.points.map(p=>qini?p.qini:p));
  const lower = Math.min(0,...pts.map(p=>p.low*1000)), upper=Math.max(...pts.map(p=>p.high*1000));
  const pad=(upper-lower)*.07, min=lower-pad,max=upper+pad;
  const x=d=>L+d*(W-L-RR), y=v=>T+(max-v)/(max-min)*(H-T-B);
  let s=`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${qini?'Qini advantage above random':'Cumulative incremental conversions'} versus targeting reach. Exact values available in the results table and aggregate download.">`;
  for(let i=0;i<=4;i++){let v=min+(max-min)*i/4;s+=`<line x1="${L}" y1="${y(v)}" x2="${W-RR}" y2="${y(v)}" stroke="#d4dad4"/><text x="${L-9}" y="${y(v)+4}" text-anchor="end">${fmt(v,1)}</text>`;}
  s+=`<line x1="${L}" y1="${y(0)}" x2="${W-RR}" y2="${y(0)}" stroke="#687b77"/>`;
  [0,.2,.4,.6,.8,1].forEach(d=>s+=`<text x="${x(d)}" y="${H-B+24}" text-anchor="middle">${Math.round(d*100)}%</text>`);
  s+=`<text x="${W/2}" y="${H-5}" text-anchor="middle">Eligible audience targeted</text><text x="${L}" y="12">Extra conversions / 1,000 eligible</text>`;
  const p=R.curves.uplift.points;
  const band=p.map(v=>`${x(v.depth)},${y((qini?v.qini:v).high*1000)}`).concat([...p].reverse().map(v=>`${x(v.depth)},${y((qini?v.qini:v).low*1000)}`)).join(' ');
  s+=`<polygon points="${band}" fill="#006c64" opacity=".10"/>`;
  ['random','baseline','propensity','uplift'].forEach(k=>{const points=R.curves[k].points.map(v=>`${x(v.depth)},${y((qini?v.qini:v).estimate*1000)}`).join(' ');s+=`<polyline points="${points}" fill="none" stroke="${colors[k]}" stroke-width="2.5" stroke-dasharray="${dash[k]}"/>`;});
  byId(target).innerHTML=s+'</svg>';
}
function renderEvidence(){
  const a=R.ate, delta=R.paired_uplift_difference_at_20pct.propensity;
  byId('recommendation').textContent=`At 20% reach, the selected uplift policy estimates ${fmt(R.curves.uplift.points[4].estimate*1000,2)} extra conversions per 1,000 eligible users. Its difference from conversion-propensity targeting is ${fmt(delta.estimate*1000,2)} (95% interval ${fmt(delta.low*1000,2)} to ${fmt(delta.high*1000,2)}). ${delta.low>0?'The holdout supports a positive advantage at this prespecified depth.':'This holdout does not establish a positive advantage at this prespecified depth.'}`;
  const metrics=[['Sampled users',fmt(R.provenance.sample_rows),'10% seeded sample across the full release'],['Final holdout',fmt(R.splits.test.rows),'Feature groups kept apart across splits'],['Conversion lift',`${fmt(a.estimate*100,3)} pp`,`95% interval ${fmt(a.low*100,3)} to ${fmt(a.high*100,3)} pp`],['Treated share',`${fmt(R.evaluation_treatment_probability*100,1)}%`,'Final holdout allocation; not assumed 50/50']];
  byId('metrics').innerHTML=metrics.map(([label,value,note])=>`<div class="metric"><span>${label}</span><strong>${value}</strong><small>${note}</small></div>`).join('');
  const rates=[0,1].map(t=>R.test_arm_conversions[t]/R.test_arm_counts[t]);
  const max=Math.max(...rates)*1.3;
  byId('arm-chart').innerHTML=`<svg class="chart" viewBox="0 0 500 205" role="img" aria-label="Control conversion rate ${fmt(rates[0]*100,3)} percent; treated conversion rate ${fmt(rates[1]*100,3)} percent">${rates.map((r,i)=>`<text x="0" y="${48+i*65}">${i?'Treated':'Control'}</text><rect x="85" y="${28+i*65}" width="${r/max*320}" height="30" fill="${i?'#006c64':'#687b77'}"/><text x="${95+r/max*320}" y="${48+i*65}">${fmt(r*100,3)}%</text>`).join('')}<text x="85" y="180">Bar length starts at zero · final holdout</text></svg>`;
  byId('ate-caption').textContent=`Intent-to-treat difference: ${fmt(a.estimate*100,3)} percentage points (95% CI ${fmt(a.low*100,3)} to ${fmt(a.high*100,3)}). Control: ${fmt(R.test_arm_conversions[0])} conversions / ${fmt(R.test_arm_counts[0])} users. Treated: ${fmt(R.test_arm_conversions[1])} / ${fmt(R.test_arm_counts[1])}.`;
  byId('quality-facts').innerHTML=[['Missing cells',fmt(R.quality.missing_cells)],['Exact duplicate rows',fmt(R.quality.exact_duplicate_rows)],['Maximum |feature SMD|',fmt(R.quality.max_absolute_smd,3)],['Assignment AUC (validation)',fmt(R.assignment_validation_auc,3)],['Selected uplift model',R.selection.selected.replace('_',' · ')]].map(([k,v])=>`<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
  byId('comparison').innerHTML=Object.entries(labels).map(([k,label])=>{let p=R.curves[k].points[4],q=R.curves[k].auqc;return `<tr><th scope="row">${label}</th><td>${fmt(p.estimate*1000,2)}</td><td>${fmt(p.low*1000,2)} to ${fmt(p.high*1000,2)}</td><td>${fmt(q.estimate*1000,2)}</td></tr>`;}).join('');
  byId('contrast').textContent=`Paired uplift minus propensity at 20%: ${fmt(delta.estimate*1000,2)} (${fmt(delta.low*1000,2)} to ${fmt(delta.high*1000,2)}). Area above random integrates the Qini curve over reach 0–1; units are extra conversions per 1,000 eligible users × reach fraction.`;
  chart('gain-chart');chart('qini-chart',true);
}
function computeScenario(r, p) {
  const {audience,cost,value,budget,depth,policy}=p;
  if(![audience,cost,value,budget,depth].every(Number.isFinite)||audience<1||cost<0||value<0||budget<0||depth<0||depth>100||!r.curves[policy])return null;
  const cap=cost===0?1:Math.min(1,budget/(audience*cost));
  const index=Math.max(0,Math.min(20,Math.floor((Math.min(depth/100,cap)+1e-10)*20)));
  const point=r.curves[policy].points[index], effective=index/20;
  const treated=Math.floor(audience*effective),spend=treated*cost;
  const increment=point.estimate*audience,low=point.low*audience,high=point.high*audience;
  return {index,effective,treated,spend,increment,low,high,net:increment*value-spend,netLow:low*value-spend,netHigh:high*value-spend,breakEven:treated?increment*value/treated:0};
}
window.computeScenario=computeScenario;
function updateScenario(){
  byId('depth-label').textContent=byId('depth').value+'%';
  const p={policy:byId('policy').value};['audience','cost','value','budget','depth'].forEach(k=>p[k]=byId(k).value===''?NaN:Number(byId(k).value));
  const s=byId('scenario-form').checkValidity()?computeScenario(R,p):null;
  if(!s){byId('scenario-error').textContent='Enter valid nonnegative assumptions and an audience of at least one.';byId('scenario-reach').textContent='Scenario unavailable';byId('scenario-conversions').textContent='—';byId('scenario-conversion-ci').textContent='';byId('scenario-financials').innerHTML='';return;}
  byId('scenario-error').textContent='';byId('scenario-reach').textContent=`${fmt(s.effective*100)}% reach · ${fmt(s.treated)} users`;
  byId('scenario-conversions').textContent=fmt(s.increment,1);byId('scenario-conversion-ci').textContent=`95% interval ${fmt(s.low,1)} to ${fmt(s.high,1)}`;
  byId('scenario-financials').innerHTML=[['Hypothetical spend',`$${fmt(s.spend,0)}`],['Net incremental value',`$${fmt(s.net,0)}`],['95% net-value interval',`$${fmt(s.netLow,0)} to $${fmt(s.netHigh,0)}`],['Break-even cost / treated user',s.treated?`$${fmt(s.breakEven,3)}`:'Not applicable']].map(([k,v])=>`<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
}
if(R&&byId('metrics')){renderEvidence();updateScenario();byId('scenario-form').addEventListener('input',updateScenario);byId('scenario-form').addEventListener('submit',e=>e.preventDefault());}
