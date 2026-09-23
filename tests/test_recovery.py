from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import pytest
from undoscope import Context, RecoveryStore
from undoscope.bench import CTX, EVENTS, setup, oracle, score

@pytest.mark.parametrize("kind", ["set", "add", "grant", "create"])
def test_clean_and_retry(kind):
    s, rid = setup(kind)
    before = s.inspect(CTX)
    eligible, expected = oracle(s, rid, [])
    result = s._research_compensate(CTX, rid, now=101)
    assert score(before, s.inspect(CTX), expected, rid, eligible, result)["recovered"]
    state = s.inspect(CTX)
    assert s._research_compensate(CTX, rid, now=101)["status"] == "already_compensated"
    assert state == s.inspect(CTX)
    s.close()

@pytest.mark.parametrize("value", ["triage", "closed", "open"])
def test_same_value_and_aba_are_conflicts(value):
    s, rid = setup("set", [{"op": "set", "field": "status", "value": value},
                            {"op": "set", "field": "status", "value": "triage"}])
    original = s.inspect(CTX)
    assert s._research_compensate(CTX, rid, now=101)["status"] == "conflict"
    assert original == s.inspect(CTX)
    s.close()

@pytest.mark.parametrize("ctx", [Context("other", "agent", "run-1"), Context("acme", "other", "run-1"),
                                 Context("acme", "agent", "run-2")])
def test_scope_is_trusted_context(ctx):
    s, rid = setup("add")
    state = s.inspect(CTX)
    assert s._research_compensate(ctx, rid, now=101)["status"] == "scope_denied"
    assert state == s.inspect(CTX)
    s.close()

@pytest.mark.parametrize("kind", ["set", "add", "grant", "create"])
def test_revocation_and_expiry(kind):
    s, rid = setup(kind)
    state = s.inspect(CTX)
    assert s._research_compensate(CTX, rid, now=1100)["status"] == "expired"
    s.set_policy(CTX, False)
    assert s._research_compensate(CTX, rid, now=101)["status"] == "policy_denied"
    assert state == s.inspect(CTX)
    s.close()


def test_counter_business_invariant():
    events = [{"op": "add", "delta": -4}]*3
    s, rid = setup("add", events)
    assert sum(s.inspect(CTX)["credits"].values()) == 2
    assert s._research_compensate(CTX, rid, now=101)["status"] == "invariant_conflict"
    s.close()


def test_same_member_independent_grant_preserved():
    s, rid = setup("grant", [{"op": "grant", "member": "contractor"}])
    assert s._research_compensate(CTX, rid, now=101)["status"] == "compensated"
    assert s.inspect(CTX)["grants"] == {"peer-0": "contractor"}
    s.close()


def test_lifo_register_provenance_chain():
    s, first = setup("set")
    second = s.forward(CTX, "set", {"field": "status", "value": "closed"}, now=100)
    assert s._research_compensate(CTX, first, now=101)["status"] == "conflict"
    assert s._research_compensate(CTX, second, now=101)["status"] == "compensated"
    assert s._research_compensate(CTX, first, now=101)["status"] == "compensated"
    assert s.inspect(CTX)["fields"]["status"]["value"] == "open"
    s.close()


def test_missing_and_malformed_receipts():
    s, rid = setup("set")
    for bad in ("unknown", "' OR 1=1 --", "", "x"*10000):
        assert s._research_compensate(CTX, bad, now=101)["status"] == "unknown_receipt"
    s.close()


def test_incarnation_even_when_revision_repeats():
    s, rid = setup("create", [{"op": "recreate"}])
    assert s.inspect(CTX)["rev"] == s.receipt(rid)["after"]["rev"]
    assert s._research_compensate(CTX, rid, now=101)["status"] == "incarnation_conflict"
    s.close()


def test_persistent_concurrent_duplicates(tmp_path):
    path = tmp_path/"state.db"
    s, rid = setup("add", path=path)
    s.close()
    def worker(i):
        client = RecoveryStore(path)
        outcome = client._research_compensate(CTX, rid, "mapped", now=101)
        client.close()
        return outcome["status"]
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(worker, range(64)))
    assert results.count("compensated") == 1
    assert results.count("already_compensated") == 63
    s = RecoveryStore(path)
    assert sum(s.inspect(CTX)["credits"].values()) == 10
    s.close()


@pytest.mark.parametrize("point,expected", [("before_commit", 14), ("after_commit", 10)])
def test_real_process_exit_atomicity(tmp_path, point, expected):
    path = tmp_path/"crash.db"
    s, rid = setup("add", path=path)
    s.close()
    script = "from undoscope.bench import CTX; from undoscope import RecoveryStore; import sys; s=RecoveryStore(sys.argv[1]); s._research_compensate(CTX, 'effect-0', 'mapped', now=101, crash=sys.argv[2])"
    run = subprocess.run([sys.executable, "-c", script, str(path), point])
    assert run.returncode in (71, 72)
    s = RecoveryStore(path)
    assert sum(s.inspect(CTX)["credits"].values()) == expected
    s._research_compensate(CTX, rid, "mapped", now=101)
    assert sum(s.inspect(CTX)["credits"].values()) == 10
    s.close()


def test_peer_write_cannot_enter_check_use_gap(tmp_path):
    path = tmp_path/"race.db"
    s, rid = setup("set", path=path)
    s.close()
    entered, attempted, finished = threading.Event(), threading.Event(), threading.Event()
    def peer():
        other = RecoveryStore(path)
        entered.wait(5)
        attempted.set()
        other.peer(CTX, {"op": "set", "field": "status", "value": "admin"})
        finished.set()
        other.close()
    thread = threading.Thread(target=peer)
    thread.start()
    def hook():
        entered.set()
        assert attempted.wait(5)
        assert not finished.wait(.05)
    s = RecoveryStore(path)
    assert s._research_compensate(CTX, rid, now=101, before_transform=hook)["status"] == "compensated"
    thread.join(5)
    assert finished.is_set()
    assert s.inspect(CTX)["fields"]["status"]["value"] == "admin"
    s.close()
