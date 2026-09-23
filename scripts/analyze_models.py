#!/usr/bin/env python3
from collections import Counter
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[json.loads(x) for x in (ROOT/'results/models.jsonl').read_text().splitlines()]
groups=[]
for model in sorted({r['model'] for r in rows}):
    for hardened in (False,True):
        part=[r for r in rows if r['model']==model and r['hardened']==hardened]
        for policy in ('mapped','undoscope'):
            branches=[b for r in part for b in r['branches'] if b['policy']==policy]
            groups.append({'model':model,'hardened':hardened,'policy':policy,'tasks':len(part),
                           'branches':len(branches),**{k:sum(b['outcome'][k] for b in branches)
                            for k in ('eligible','collateral','recovered','wrong_receipt_selected','victim_changed')},
                           'escalated':sum(b['tool_result']['status']=='escalated' for b in branches)})
usage=Counter();errors=[];models=Counter();statuses=Counter()
for r in rows:
    for label,call in [('first',r['first'])]+[(b['policy'],b['second']) for b in r['branches']]:
        if call['error']: errors.append({'id':r['id'],'phase':label,'error':call['error']})
        else:
            response=call['response'];models[response.get('model')]+=1;statuses[response.get('status')]+=1
            for k,v in response.get('usage',{}).items():
                if isinstance(v,int):usage[k]+=v
summary={'episodes':len(rows),'groups':groups,'api_errors':errors,'returned_models':dict(models),
         'response_statuses':dict(statuses),'usage':dict(usage),
         'selected_tools':dict(Counter(r.get('selected',{}).get('name','missing') for r in rows))}
(ROOT/'results/model-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
