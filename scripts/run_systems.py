#!/usr/bin/env python3
"""Ablation, durable crash/concurrency trials, and local transaction timing."""
import csv
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import platform
import random
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from undoscope import Context, RecoveryStore
from undoscope.bench import CTX, setup, signature, oracle, score
from undoscope.policies import POLICIES

ROOT=Path(__file__).resolve().parents[1]

def ablations():
    cases=[("same_value","set",[{"op":"set","field":"status","value":"triage"}],None),
           ("independent_grant","grant",[{"op":"grant","member":"contractor"}],None),
           ("disjoint_field","set",[{"op":"set","field":"note","value":"peer"}],None),
           ("independent_credit","add",[{"op":"add","delta":2}],None),
           ("reused_name","create",[{"op":"recreate"}],None),
           ("business_invariant","add",[{"op":"add","delta":-4}]*3,None),
           ("wrong_run","add",[],"scope"), ("revoked","add",[],"policy"),
           ("expired","add",[],"expiry"), ("duplicate","add",[],"consumption")]
    rows=[]
    for label,kind,events,attack in cases:
        for omitted in ("none","scope","policy","expiry","incarnation","provenance","invariant","consumption"):
            s,rid=setup(kind,events)
            ctx=Context("acme","agent","other") if attack=="scope" else CTX
            now=1100 if attack=="expiry" else 101
            if attack=="policy": s.set_policy(CTX,False)
            if attack=="consumption": s._research_compensate(CTX,rid,now=101)
            before=s.inspect(CTX)
            eligible,expected=oracle(s,rid,events)
            if attack: eligible=False; expected=before
            outcome=s._research_compensate(ctx,rid,now=now,omit={omitted})
            value=score(before,s.inspect(CTX),expected,rid,eligible,outcome)
            rows.append({"case":label,"omitted":omitted,**value})
            s.close()
    with (ROOT/"results/ablations.csv").open("w") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    return {guard:sum(r["collateral"] for r in rows if r["omitted"]==guard)
            for guard in sorted({r["omitted"] for r in rows})}

def durability():
    rows=[]
    code=("from undoscope.bench import CTX; from undoscope import RecoveryStore; import sys; "
          "s=RecoveryStore(sys.argv[1]); s._research_compensate(CTX, 'effect-0', 'mapped', now=101, crash=sys.argv[2])")
    with tempfile.TemporaryDirectory() as td:
        for trial in range(30):
            for point in ("before_commit","after_commit"):
                path=Path(td)/f"{trial}-{point}.db"
                s,rid=setup("add",path=path);s.close()
                proc=subprocess.run([sys.executable,"-c",code,str(path),point],capture_output=True)
                s=RecoveryStore(path); intermediate=sum(s.inspect(CTX)["credits"].values())
                s._research_compensate(CTX,rid,"mapped",now=101)
                final=sum(s.inspect(CTX)["credits"].values())
                rows.append({"trial":trial,"kind":point,"exit":proc.returncode,"intermediate":intermediate,
                             "final":final,"passed":intermediate==(14 if point=="before_commit" else 10) and final==10})
                s.close()
            path=Path(td)/f"{trial}-parallel.db"
            s,rid=setup("add",path=path);s.close()
            def worker(i):
                s=RecoveryStore(path)
                status=s._research_compensate(CTX,rid,"mapped",now=101)["status"]
                s.close();return status
            with ThreadPoolExecutor(max_workers=16) as pool:
                answers=list(pool.map(worker,range(32)))
            s=RecoveryStore(path); final=sum(s.inspect(CTX)["credits"].values());s.close()
            rows.append({"trial":trial,"kind":"concurrent_32","accepted":answers.count("compensated"),
                         "final":final,"passed":answers.count("compensated")==1 and final==10})
    (ROOT/"results/durability.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    return {"trials":len(rows),"passed":sum(r["passed"] for r in rows),"parallel_attempts":30*32}

def latency():
    rng=random.Random(77231); rows=[]
    with tempfile.TemporaryDirectory() as td:
        s=RecoveryStore(Path(td)/"timing.db")
        for round_id in range(270):
            policies=list(POLICIES);rng.shuffle(policies)
            for policy in policies:
                name=f"{round_id}-{policy}"
                s.seed(CTX,name=name)
                rid=s.forward(CTX,"add",{"delta":4},name=name,now=100)
                start=time.perf_counter_ns()
                outcome=s._research_compensate(CTX,rid,policy,now=101)
                elapsed=time.perf_counter_ns()-start
                if round_id>=20:
                    rows.append({"round":round_id-20,"policy":policy,"microseconds":elapsed/1000,
                                 "status":outcome["status"]})
        s.close()
    with (ROOT/"results/latency.csv").open("w") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    summary={}
    for p in POLICIES:
        vals=sorted(r["microseconds"] for r in rows if r["policy"]==p)
        summary[p]={"n":len(vals),"median_us":statistics.median(vals),"p95_us":vals[int(.95*(len(vals)-1))]}
    return summary

if __name__=="__main__":
    summary={"ablations":ablations(),"durability":durability(),"latency":latency(),
             "environment":{"platform":platform.platform(),"python":platform.python_version(),
                            "sqlite":sqlite3.sqlite_version,"journal":"WAL","synchronous":"FULL"}}
    (ROOT/"results/systems-summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
