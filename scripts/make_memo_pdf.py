"""Render a one-page decision memo from measured aggregate results."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from pypdf import PdfReader

def build():
    r=json.loads(Path('outputs/analysis/results.json').read_text())
    out=Path('outputs/reports/decision-memo.pdf');out.parent.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyMemo',fontName='Helvetica',fontSize=10.3,leading=14,textColor=colors.HexColor('#182e35'),spaceAfter=9))
    styles.add(ParagraphStyle(name='MemoTitle',fontName='Times-Roman',fontSize=28,leading=30,textColor=colors.HexColor('#182e35'),spaceAfter=12))
    styles.add(ParagraphStyle(name='MemoHeading',fontName='Helvetica-Bold',fontSize=11,leading=15,textColor=colors.HexColor('#006c64'),spaceBefore=9,spaceAfter=6))
    styles.add(ParagraphStyle(name='SmallMemo',fontSize=8,leading=11,textColor=colors.HexColor('#506268'),spaceAfter=8))
    p=lambda text,style='BodyMemo':Paragraph(text,styles[style])
    a=r['ate'];u=r['curves']['uplift']['points'][4];diff=r['paired_uplift_difference_at_20pct']['propensity'];random=r['paired_uplift_difference_at_20pct']['random']
    story=[p('INDEPENDENT PROJECT / DECISION MEMO / 23 SEPTEMBER 2026','SmallMemo'),p('Growth Incrementality<br/>&amp; Targeting Lab','MemoTitle'),p('Decision: test uplift against propensity at equal reach.','MemoHeading'),p('Advance both rankings to a fresh randomized policy comparison. This benchmark does not establish that uplift beats conversion propensity, and it does not justify production rollout on its own.'),p('Evidence','MemoHeading'),p(f"A seeded 10% sample of Criteo v2.1 contains <b>{r['provenance']['sample_rows']:,} users</b>, with <b>{r['splits']['test']['rows']:,}</b> in a final holdout. Feature groups stay within one split. The linear T-learner won validation against two boosted candidates."),p(f"Assignment to advertising increased final-holdout conversion by <b>{a['estimate']*100:.3f} percentage points</b> (95% CI {a['low']*100:.3f} to {a['high']*100:.3f}). At 20% reach, extra conversions per 1,000 eligible users were:")]
    rows=[['Policy','Estimate','95% interval']]
    for key,label in [('uplift','Selected uplift'),('propensity','Conversion propensity'),('random','Random targeting')]:
        x=r['curves'][key]['points'][4];rows.append([label,f"{x['estimate']*1000:.2f}",f"{x['low']*1000:.2f} to {x['high']*1000:.2f}"])
    table=Table(rows,colWidths=[235,90,170],hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eee5')),('TEXTCOLOR',(0,0),(-1,-1),colors.HexColor('#182e35')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d4dad4')),('ALIGN',(1,1),(-1,-1),'RIGHT')]))
    story += [table,Spacer(1,10),p(f"Paired uplift minus propensity: <b>{diff['estimate']*1000:.3f}</b> (95% CI {diff['low']*1000:.3f} to {diff['high']*1000:.3f}); superiority is not established. Uplift minus random: <b>{random['estimate']*1000:.3f}</b> ({random['low']*1000:.3f} to {random['high']*1000:.3f})."),p('Budget implication - hypothetical only','MemoHeading'),p(f"At 100,000 eligible users, 20% reach, $0.20 per treated user and $100 per extra conversion: <b>{u['estimate']*100000:.1f}</b> estimated extra conversions, <b>$4,000</b> spend, and <b>${u['estimate']*10000000-4000:,.0f}</b> net incremental value (95% sampling interval ${u['low']*10000000-4000:,.0f} to ${u['high']*10000000-4000:,.0f}). These are scenarios, not observed revenue or profit."),p('Boundaries and next step','MemoHeading'),p(f"Privacy subsampling changes incrementality. Anonymized features, pooled tests, missing experiment IDs and only {r['test_arm_conversions']['0']} control conversions limit interpretation. Pointwise intervals exclude model-selection and transport uncertainty. Prespecify the audience, conversion window, economics and meaningful policy difference; then randomize equal-reach policies with contamination and margin guardrails."),p('Source: Criteo AI Lab; Diemert et al. (2018), A Large Scale Benchmark for Uplift Modeling. Data-derived report: CC BY-NC-SA 4.0. Independent work; no Criteo endorsement. Methods and code: github.com/IamGRootMSE/growth-incrementality-lab','SmallMemo')]
    SimpleDocTemplate(str(out),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=36,bottomMargin=32,title='Growth Incrementality & Targeting Lab - Decision Memo',author='IamGRootMSE').build(story)
    assert len(PdfReader(out).pages)==1,'Memo must remain one page'
    print(out)

if __name__=='__main__':build()
