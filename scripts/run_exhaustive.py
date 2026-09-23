#!/usr/bin/env python3
import csv
import json
import platform
import time
from pathlib import Path
from undoscope.bench import CTX, enumerate_cases, oracle, setup, score
from undoscope.policies import POLICIES

ROOT = Path(__file__).resolve().parents[1]
def main():
    rows = []
    start = time.perf_counter()
    for case_id, (kind, indices, events) in enumerate(enumerate_cases()):
        for policy in POLICIES:
            store, rid = setup(kind, events)
            before = store.inspect(CTX)
            eligible, expected = oracle(store, rid, events)
            outcome = store._research_compensate(CTX, rid, policy, now=101)
            after = store.inspect(CTX)
            rows.append({"case": case_id, "kind": kind, "history": "".join(map(str, indices)),
                         "policy": policy, **score(before, after, expected, rid, eligible, outcome)})
            store.close()
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    with (out / "exhaustive.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader(); writer.writerows(rows)
    summary = {}
    for policy in POLICIES:
        part = [r for r in rows if r["policy"] == policy]
        summary[policy] = {k: sum(r[k] for r in part) for k in ("eligible", "collateral", "recovered")}
        summary[policy]["cases"] = len(part)
    meta = {"summary": summary, "seconds": time.perf_counter()-start, "python": platform.python_version(),
            "platform": platform.platform(), "depth": 4, "alphabet_size": 4}
    (out / "exhaustive-summary.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
if __name__ == "__main__":
    main()
