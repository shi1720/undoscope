"""Recovery transforms. Baselines are research controls, not production policies."""
from copy import deepcopy

POLICIES = ("snapshot", "mapped", "value", "object", "field", "undoscope", "deny")

def visible(obj):
    if obj is None:
        return None
    return {"fields": {k: v["value"] for k, v in obj["fields"].items()},
            "balance": sum(obj["credits"].values()),
            "members": sorted(set(obj["grants"].values()))}


def transform(obj, receipt, policy="undoscope", omit=frozenset()):
    """Return (status, new object); no mutation of input. Guard+write needs a transaction."""
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    if policy == "deny":
        return "denied", obj
    if obj is None:
        return "missing", obj
    if "incarnation" not in omit and obj["generation"] != receipt["generation"]:
        return "incarnation_conflict", obj
    kind, args = receipt["kind"], receipt["args"]
    before, after = receipt["before"], receipt["after"]
    candidate = deepcopy(obj)
    if policy == "object" and obj["rev"] != after["rev"]:
        return "conflict", obj
    if policy == "field":
        if kind == "set":
            if obj["fields"][args["field"]]["head"] != receipt["id"]:
                return "conflict", obj
        elif kind == "create":
            if obj["rev"] != after["rev"]:
                return "conflict", obj
        elif obj["component_rev"][kind] != after["component_rev"][kind]:
            return "conflict", obj
    if policy == "value":
        if kind == "set":
            equal = obj["fields"][args["field"]]["value"] == args["value"]
        elif kind == "add":
            equal = sum(obj["credits"].values()) == sum(after["credits"].values())
        elif kind == "grant":
            equal = args["member"] in obj["grants"].values()
        else:
            equal = visible(obj) == visible(after)
        if not equal:
            return "conflict", obj
    if policy == "snapshot":
        candidate = deepcopy(before)
    elif kind == "set":
        field = args["field"]
        if policy == "undoscope" and "provenance" not in omit:
            if obj["fields"][field]["head"] != receipt["id"]:
                return "conflict", obj
        candidate["fields"][field] = deepcopy(before["fields"][field])
    elif kind == "add":
        if policy == "undoscope" and "provenance" not in omit:
            # Retraction of a unique contribution, not a second arbitrary debit.
            if receipt["id"] not in candidate["credits"]:
                return "effect_missing", obj
            del candidate["credits"][receipt["id"]]
        else:
            candidate["credits"]["inverse:" + receipt["id"] + ":" + str(obj["rev"])] = -args["delta"]
    elif kind == "grant":
        if policy == "undoscope" and "provenance" not in omit:
            candidate["grants"].pop(receipt["id"], None)
        else:
            candidate["grants"] = {k: v for k, v in obj["grants"].items() if v != args["member"]}
    elif kind == "create":
        if policy == "undoscope" and "provenance" not in omit and obj["rev"] != after["rev"]:
            return "conflict", obj
        candidate = None
    else:
        return "unsupported", obj
    if candidate is not None:
        if "invariant" not in omit and sum(candidate["credits"].values()) < 0:
            return "invariant_conflict", obj
        candidate["rev"] = obj["rev"] + 1
        candidate["component_rev"][kind] = obj["component_rev"][kind] + 1
    return "compensated", candidate
