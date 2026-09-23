#!/usr/bin/env python3
"""Audit counts, API provenance, saved-state outcomes, and paired execution replay."""
import csv
import json
from collections import Counter
from pathlib import Path
from undoscope.bench import CTX, oracle, score, signature
from undoscope.model_tasks import MODELS, fixture, inputs
ROOT=Path(__file__).resolve().parents[1]

def main():
    data=list(csv.DictReader((ROOT/'results/exhaustive.csv').open()))
    assert len(data)==9548 and len({r['case'] for r in data})==1364
    assert len({(r['case'],r['policy']) for r in data})==9548
    summary=json.loads((ROOT/'results/exhaustive-summary.json').read_text())['summary']
    for p,s in summary.items():
        rows=[r for r in data if r['policy']==p]
        for k in ('eligible','collateral','recovered'):
            assert s[k]==sum(r[k]=='True' for r in rows),(p,k)
        assert s['cases']==len(rows)
    # Every domain has the entire base-four grammar, including the empty history.
    for kind in ('set','add','grant','create'):
        rows=[r for r in data if r['policy']=='undoscope' and r['kind']==kind]
        assert Counter(len(r['history']) for r in rows)=={0:1,1:4,2:16,3:64,4:256}
    models=[json.loads(l) for l in (ROOT/'results/models.jsonl').read_text().splitlines()]
    assert len(models)==240 and len({r['id'] for r in models})==240
    response_ids=set();usage=Counter();replayed=0
    for r in models:
        assert r['request']['input']==inputs(r['kind'],r['condition'],r['seed'],r['hardened'])
        for call in [r['first']]+[b['second'] for b in r['branches']]:
            assert call['error'] is None
            response=call['response'];assert response['model']==r['model'] and response['status']=='completed'
            assert response['id'] not in response_ids;response_ids.add(response['id'])
            for k,v in response['usage'].items():
                if isinstance(v,int):usage[k]+=v
        actual=[x for x in r['first']['response']['output'] if x['type']=='function_call']
        assert len(actual)==1 and actual[0]['name']==r['selected']['name']
        assert json.loads(actual[0]['arguments'])==r['selected']['arguments']
        assert {b['policy'] for b in r['branches']}=={'mapped','undoscope'}
        for b in r['branches']:
            s,rid,alien,events=fixture(r['kind'],r['condition'],r['seed'])
            eligible,expected=oracle(s,rid,events);before=s.inspect(CTX)
            chosen=r['selected']
            result=s._research_compensate(CTX,chosen['arguments']['receipt_id'],b['policy'],now=101) if chosen['name']=='recover_effect' else {'status':'escalated'}
            assert result==b['tool_result']
            regenerated=score(before,s.inspect(CTX),expected,rid,eligible,result)
            for k,v in regenerated.items():assert b['outcome'][k]==v,(r['id'],b['policy'],k)
            # Verify stored outcomes from saved states as well as fresh execution.
            saved=score(b['before'],b['after'],b['expected'],rid,eligible,result)
            assert saved==regenerated
            s.close();replayed+=1
    ms=json.loads((ROOT/'results/model-summary.json').read_text())
    assert dict(usage)==ms['usage'] and len(response_ids)==720
    for g in ms['groups']:
        part=[b for r in models if r['model']==g['model'] and r['hardened']==g['hardened'] for b in r['branches'] if b['policy']==g['policy']]
        assert len(part)==g['branches']==60
        for k in ('collateral','eligible','recovered','wrong_receipt_selected','victim_changed'):
            assert sum(b['outcome'][k] for b in part)==g[k]
    durable=[json.loads(x) for x in (ROOT/'results/durability.jsonl').read_text().splitlines()]
    assert len(durable)==90
    for r in durable:
        assert r['final']==10 and r['passed']
        if r['kind']=='concurrent_32':assert r['accepted']==1
        elif r['kind']=='before_commit':assert r['exit']==71 and r['intermediate']==14
        else:assert r['exit']==72 and r['intermediate']==10
    result={'history_policy_rows':len(data),'model_episodes':len(models),'unique_api_responses':len(response_ids),
            'model_branches_replayed':replayed,'durable_trials':len(durable),'status':'passed'}
    (ROOT/'results/audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
