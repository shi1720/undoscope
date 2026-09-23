"""Network-free conference demonstration; every outcome comes from the store."""
import argparse
import json
from .bench import CTX, setup
from .policies import visible

SCENARIOS = {
    "same-value": ("set", [{"op":"set","field":"status","value":"triage"}],
                   "The agent sets triage. An operator independently confirms triage. A value-only inverse cannot see the difference."),
    "shared-grant": ("grant", [{"op":"grant","member":"contractor"}],
                     "Both the agent and an independent workflow grant the same contractor access. Recovery may remove only the agent's grant."),
    "disjoint-change": ("set", [{"op":"set","field":"note","value":"keep-this-note"}],
                        "An operator adds a note after the agent changes status. Recovery should restore status and preserve the note."),
    "name-reuse": ("create", [{"op":"recreate"}],
                  "A resource is deleted and recreated under the same name. The original creation receipt must not delete its replacement.")
}

def run(scenario):
    kind,events,description=SCENARIOS[scenario]
    results=[]
    for policy in ("snapshot","mapped","value","object","field","undoscope"):
        store,rid=setup(kind,events)
        raw_before=store.inspect(CTX)
        before=visible(raw_before)
        status=store._research_compensate(CTX,rid,policy,now=101)
        results.append({"policy":policy,"before":before,"result":status,"after":visible(store.inspect(CTX)),"raw_before":raw_before,"raw_after":store.inspect(CTX)})
        store.close()
    return {"scenario":scenario,"description":description,"results":results}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--scenario",choices=SCENARIOS,default="shared-grant")
    p.add_argument("--json",action="store_true");a=p.parse_args();result=run(a.scenario)
    if a.json: print(json.dumps(result,indent=2));return
    print("\nUndoScope | "+a.scenario+"\n"+result["description"]+"\n")
    for r in result["results"]:
        print(f"{r['policy']:>10}: {r['result']['status']:>22}  {json.dumps(r['after'],sort_keys=True)}")
    print("\nThese are local controlled examples, not tests against third-party services.")
if __name__=="__main__": main()
