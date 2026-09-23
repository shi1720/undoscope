#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'paper'
labels={'snapshot':'Snapshot','mapped':'Mapped inverse','value':'Value guard','object':'Object guard','field':'Component guard','undoscope':'UndoScope','deny':'Deny all'}
data=json.loads((ROOT/'results/exhaustive-summary.json').read_text())['summary']
lines=[]
for p,r in data.items():
 lines.append(f"{labels[p]} & {r['collateral']:,}/{r['cases']:,} & {r['recovered']:,}/{r['eligible']:,} & {100*r['recovered']/r['eligible']:.1f}\\\\")
(OUT/'results-table.tex').write_text(r'\begin{tabular}{@{}lrrr@{}}\toprule Policy & Collateral & Recovered & \%\\\midrule'+'\n'+'\n'.join(lines)+'\n'+r'\bottomrule\end{tabular}')
model=json.loads((ROOT/'results/model-summary.json').read_text());lines=[]
for m in ['gpt-4.1-mini-2025-04-14','gpt-4.1-2025-04-14']:
 for h in [False,True]:
  a=next(g for g in model['groups'] if g['model']==m and g['hardened']==h and g['policy']=='mapped')
  b=next(g for g in model['groups'] if g['model']==m and g['hardened']==h and g['policy']=='undoscope')
  lines.append(f"{'4.1 mini' if 'mini' in m else '4.1'} & {'Hardened' if h else 'Ordinary'} & {a['wrong_receipt_selected']}/20 & {a['collateral']}/{b['collateral']} & {a['recovered']}/{b['recovered']}\\\\")
(OUT/'models-table.tex').write_text(r'\begin{tabular}{@{}llrrr@{}}\toprule Model & Prompt & Wrong receipt (injected) & Collateral M/U (of 60) & Safe recovered M/U (of 50)\\\midrule'+'\n'+'\n'.join(lines)+'\n'+r'\bottomrule\end{tabular}')
sys=json.loads((ROOT/'results/systems-summary.json').read_text());lines=[]
for p in labels:
 r=sys['latency'][p];lines.append(f"{labels[p]} & {r['median_us']:.1f} & {r['p95_us']:.1f}\\\\")
(OUT/'latency-table.tex').write_text(r'\begin{tabular}{@{}lrr@{}}\toprule Policy & Median & Empirical p95\\\midrule'+'\n'+'\n'.join(lines)+'\n'+r'\bottomrule\end{tabular}')
