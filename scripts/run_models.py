#!/usr/bin/env python3
"""Live bounded API collection. Key stays in memory; full synthetic responses saved."""
import argparse
import asyncio
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import time
from openai import AsyncOpenAI
from undoscope.bench import CTX, oracle, score
from undoscope.model_tasks import MODELS, TOOLS, fixture, inputs

ROOT=Path(__file__).resolve().parents[1]

async def main(args):
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key (hidden; never saved): ")
    client = AsyncOpenAI(api_key=key, max_retries=0, timeout=60)
    target = (ROOT/args.output) if args.output else ROOT/"results"/("model-pilot.jsonl" if args.pilot else "models.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = [json.loads(x) for x in target.read_text().splitlines()] if target.exists() else []
    completed = {x["id"] for x in existing}
    cases = [(model, kind, condition, seed, hardened) for model in MODELS for kind in ("set","add","grant","create")
             for condition in ("clean","concurrent","injected") for seed in range(5) for hardened in (False,True)]
    if args.pilot:
        cases = [(m,"grant","concurrent",0,False) for m in MODELS]
    sem=asyncio.Semaphore(6)
    lock=asyncio.Lock()
    count=0
    async def call(payload):
        start=time.perf_counter()
        try:
            r=await client.responses.create(**payload)
            return {"response":r.model_dump(mode="json", by_alias=True, exclude_none=True),"seconds":time.perf_counter()-start,"error":None}
        except Exception as e:
            # No exception repr/body: these may include headers or client internals.
            return {"response":None,"seconds":time.perf_counter()-start,"error":{"type":type(e).__name__,"status":getattr(e,"status_code",None),"message":str(e).replace(key,"[REDACTED]")[:800]}}
    async def episode(case):
        nonlocal count
        model,kind,condition,seed,hardened=case
        ident=f"{model}/{kind}/{condition}/{seed}/{int(hardened)}"
        if ident in completed:
            return
        async with sem:
            inp=inputs(kind,condition,seed,hardened)
            payload={"model":model,"input":inp,"tools":TOOLS,"tool_choice":"required", "parallel_tool_calls":False,
                     "temperature":0,"max_output_tokens":240,"store":False}
            record={"id":ident,"model":model,"kind":kind,"condition":condition,"seed":seed,"hardened":hardened,
                    "timestamp_utc":datetime.now(timezone.utc).isoformat(),"request":payload}
            record["first"]=await call(payload)
            response=record["first"]["response"]
            calls=[x for x in (response or {}).get("output",[]) if x["type"]=="function_call"]
            record["branches"]=[]
            if len(calls)==1:
                chosen=calls[0]
                try:
                    arguments=json.loads(chosen["arguments"])
                except (TypeError,ValueError):
                    arguments={}
                record["selected"]={"name":chosen["name"],"arguments":arguments}
                for policy in ("mapped","undoscope"):
                    s,rid,alien,events=fixture(kind,condition,seed)
                    before=s.inspect(CTX)
                    victim_before=s.inspect(CTX,"victim")
                    eligible,expected=oracle(s,rid,events)
                    if chosen["name"]=="recover_effect" and isinstance(arguments.get("receipt_id"),str):
                        result=s._research_compensate(CTX,arguments["receipt_id"],policy,now=101)
                    else:
                        result={"status":"escalated"}
                    outcome=score(before,s.inspect(CTX),expected,rid,eligible,result)
                    outcome["victim_changed"]=victim_before!=s.inspect(CTX,"victim")
                    outcome["wrong_receipt_selected"]=(chosen["name"]=="recover_effect" and arguments.get("receipt_id")!=rid)
                    continuation=inp+[{k:chosen[k] for k in ("type","call_id","name","arguments")}]+[{"type":"function_call_output","call_id":chosen["call_id"],"output":json.dumps(result)}]
                    follow={"model":model,"input":continuation,"temperature":0,"max_output_tokens":240,"store":False}
                    second=await call(follow)
                    record["branches"].append({"policy":policy,"tool_result":result,"outcome":outcome,
                                               "before":before,"after":s.inspect(CTX),"expected":expected,"second":second})
                    s.close()
            async with lock:
                with target.open("a") as f:
                    f.write(json.dumps(record,sort_keys=True)+"\n"); f.flush()
                count+=1
                if count%10==0 or args.pilot or record["first"]["error"]:
                    print(json.dumps({"collected":count,"total":len(cases)-len(completed),"last":ident,
                                      "error":record["first"]["error"]}),flush=True)
    await asyncio.gather(*(episode(c) for c in cases))
    await client.close()
    print("Collection complete: "+str(target),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--pilot",action="store_true");p.add_argument("--output",help="New or resumable JSONL output; relative to repository root")
    asyncio.run(main(p.parse_args()))
