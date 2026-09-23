"""Deterministic workload and trace-derived oracle, independent of recovery policies."""
from copy import deepcopy
from itertools import product
from .store import Context, RecoveryStore
from .policies import visible

CTX = Context("acme", "agent", "run-1")
ARGS = {"set": {"field": "status", "value": "triage"}, "add": {"delta": 4},
        "grant": {"member": "contractor"}, "create": {}}
EVENTS = {
    "set": [{"op": "set", "field": "status", "value": x} for x in ("triage", "closed", "open")] +
           [{"op": "set", "field": "note", "value": "peer-note"}],
    "add": [{"op": "add", "delta": 2}, {"op": "add", "delta": -4},
            {"op": "set", "field": "note", "value": "peer-note"}, {"op": "grant", "member": "peer"}],
    "grant": [{"op": "grant", "member": "contractor"}, {"op": "grant", "member": "peer"},
              {"op": "revoke", "member": "contractor"}, {"op": "set", "field": "note", "value": "peer-note"}],
    "create": [{"op": "set", "field": "note", "value": "peer-note"},
               {"op": "set", "field": "status", "value": "open"},
               {"op": "recreate"}, {"op": "delete"}]
}


def setup(kind, events=(), path=":memory:", seed=0):
    store = RecoveryStore(path)
    if kind != "create":
        store.seed(CTX, generation="generation-original")
    else:
        store.set_policy(CTX, True)
    rid = "effect-" + str(seed)
    store.forward(CTX, kind, ARGS[kind], rid=rid, now=100, ttl=1000)
    for i, event in enumerate(events):
        store.peer(CTX, event, eid=f"peer-{i}")
    return store, rid


def signature(obj, rid):
    """Observable values plus preservation of non-target provenance entries.

    An additive inverse and a contribution retraction are equivalent when they have
    the same total and preserve every independent contribution. Internal object
    revision numbers are deliberately excluded from the outcome oracle.
    """
    if obj is None:
        return None
    return {"generation": obj["generation"], "fields": obj["fields"],
            "balance": sum(obj["credits"].values()),
            "foreign_credits": {k: v for k, v in obj["credits"].items()
                                if k != rid and not k.startswith("inverse:" + rid + ":")},
            "members": sorted(set(obj["grants"].values())),
            "foreign_grants": {k: v for k, v in obj["grants"].items() if k != rid},
            "own_grant": rid in obj["grants"]}


def oracle(store, rid, events):
    """Derive permissible result from known external history, not transform()."""
    rec = store.receipt(rid)
    cur = store.inspect(CTX)
    expected = deepcopy(cur)
    if cur is None or any(e["op"] in ("recreate", "delete") for e in events):
        return False, expected
    kind = rec["kind"]
    if kind == "set":
        if any(e["op"] == "set" and e["field"] == "status" for e in events):
            return False, expected
        expected["fields"]["status"] = {"value": "open", "head": "initial"}
    elif kind == "add":
        # Expected total computed from the actual accepted independent entries.
        remaining = {k: v for k, v in cur["credits"].items() if k != rid}
        if sum(remaining.values()) < 0:
            return False, expected
        expected["credits"] = remaining
    elif kind == "grant":
        expected["grants"] = {k: v for k, v in cur["grants"].items() if k != rid}
    elif kind == "create":
        if events:
            return False, expected
        expected = None
    return True, expected


def enumerate_cases(depth=4):
    for kind, alphabet in EVENTS.items():
        for length in range(depth + 1):
            for indices in product(range(len(alphabet)), repeat=length):
                yield kind, indices, [deepcopy(alphabet[i]) for i in indices]


def score(before, after, expected, rid, eligible, result):
    start, end, target = (signature(x, rid) for x in (before, after, expected))
    changed = start != end
    collateral = changed and (not eligible or end != target)
    recovered = eligible and result["status"] == "compensated" and end == target
    return {"eligible": eligible, "collateral": collateral, "recovered": recovered,
            "changed": changed, "status": result["status"]}
