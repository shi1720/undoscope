"""Longer random histories, with arithmetic and last-writer oracles written here."""
from hypothesis import given, settings, strategies as st
from undoscope import RecoveryStore
from undoscope.bench import CTX

@settings(max_examples=100, derandomize=True)
@given(st.lists(st.tuples(st.sampled_from(['status','note']),st.sampled_from(['open','triage','closed'])),max_size=30))
def test_register_independent_last_writer_oracle(events):
    s=RecoveryStore();s.seed(CTX)
    rid=s.forward(CTX,'set',{'field':'status','value':'triage'})
    expected={'status':'triage','note':'original'};blocked=False
    for i,(field,value) in enumerate(events):
        s.peer(CTX,{'op':'set','field':field,'value':value},eid=f'p{i}')
        expected[field]=value;blocked |= field=='status'
    result=s.compensate(CTX,rid)
    if not blocked: expected['status']='open'
    assert {k:v['value'] for k,v in s.inspect(CTX)['fields'].items()}==expected
    assert result['status']==('conflict' if blocked else 'compensated')
    s.close()

@settings(max_examples=100, derandomize=True)
@given(st.lists(st.integers(-5,7),max_size=30))
def test_counter_independent_arithmetic_oracle(deltas):
    s=RecoveryStore();s.seed(CTX)
    rid=s.forward(CTX,'add',{'delta':4});balance=14;accepted={}
    for i,d in enumerate(deltas):
        s.peer(CTX,{'op':'add','delta':d},eid=f'p{i}')
        if balance+d>=0: balance+=d;accepted[f'p{i}']=d
    expected=balance-4 if balance>=4 else balance
    result=s.compensate(CTX,rid);obj=s.inspect(CTX)
    assert sum(obj['credits'].values())==expected
    assert all(obj['credits'][k]==v for k,v in accepted.items())
    assert result['status']==('compensated' if balance>=4 else 'invariant_conflict')
    s.close()

@settings(max_examples=100, derandomize=True)
@given(st.lists(st.sampled_from(['same','other','revoke']),max_size=30))
def test_grant_independent_tag_oracle(events):
    s=RecoveryStore();s.seed(CTX)
    rid=s.forward(CTX,'grant',{'member':'contractor'});expected={}
    for i,e in enumerate(events):
        if e=='revoke':
            s.peer(CTX,{'op':'revoke','member':'contractor'},eid=f'p{i}')
            expected={k:v for k,v in expected.items() if v!='contractor'}
        else:
            member='contractor' if e=='same' else 'peer'
            s.peer(CTX,{'op':'grant','member':member},eid=f'p{i}');expected[f'p{i}']=member
    assert s.compensate(CTX,rid)['status']=='compensated'
    assert s.inspect(CTX)['grants']==expected
    s.close()
