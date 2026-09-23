"""Trusted SQLite adapter. Model inputs never supply identity or inverse parameters.

The Python API is an embedded trusted service API, not an authentication service.
The MCP adapter binds Context at process startup. For network use, bind it to an
independently authenticated session. Direct database access defeats the contract.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import os
import sqlite3
import time
import uuid
from .policies import transform, visible

@dataclass(frozen=True)
class Context:
    tenant: str
    principal: str
    run: str


def blank(generation=None, balance=10):
    return {"generation": generation or uuid.uuid4().hex, "rev": 0,
            "fields": {"status": {"value": "open", "head": "initial"},
                       "note": {"value": "original", "head": "initial"}},
            "credits": {"initial": balance}, "grants": {},
            "component_rev": {k: 0 for k in ("set", "add", "grant", "create")}}


class RecoveryStore:
    def __init__(self, path=":memory:"):
        self.path = str(path)
        self.db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS objects(tenant TEXT, name TEXT, body TEXT NOT NULL,
            PRIMARY KEY(tenant,name));
          CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY, body TEXT NOT NULL,
            consumed INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS policy(tenant TEXT, principal TEXT, allowed INTEGER,
            PRIMARY KEY(tenant,principal));
          CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt TEXT, status TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _get(self, tenant, name):
        row = self.db.execute("SELECT body FROM objects WHERE tenant=? AND name=?", (tenant, name)).fetchone()
        return json.loads(row[0]) if row else None

    def _put(self, tenant, name, obj):
        if obj is None:
            self.db.execute("DELETE FROM objects WHERE tenant=? AND name=?", (tenant, name))
        else:
            self.db.execute("INSERT INTO objects VALUES(?,?,?) ON CONFLICT(tenant,name) DO UPDATE SET body=excluded.body",
                            (tenant, name, json.dumps(obj, sort_keys=True)))

    def inspect(self, context, name="resource"):
        return deepcopy(self._get(context.tenant, name))

    def receipt(self, rid):
        # Trusted test/administrative API; not exported as an agent tool.
        row = self.db.execute("SELECT body FROM receipts WHERE id=?", (rid,)).fetchone()
        return json.loads(row[0]) if row else None

    def seed(self, context, name="resource", balance=10, generation=None):
        with self.transaction():
            if self._get(context.tenant, name) is not None:
                raise ValueError("already exists")
            self._put(context.tenant, name, blank(generation, balance))
            self.db.execute("INSERT OR IGNORE INTO policy VALUES(?,?,1)", (context.tenant, context.principal))

    def set_policy(self, context, allowed):
        with self.transaction():
            self.db.execute("INSERT INTO policy VALUES(?,?,?) ON CONFLICT(tenant,principal) DO UPDATE SET allowed=excluded.allowed",
                            (context.tenant, context.principal, int(allowed)))

    def forward(self, context, kind, args, name="resource", *, ttl=3600, now=None, rid=None):
        # Caller is a trusted application adapter with forward authorization already checked.
        # The recovery mechanism does not authorize arbitrary forward business operations.
        now = time.time() if now is None else now
        rid = rid or uuid.uuid4().hex
        with self.transaction():
            before = self._get(context.tenant, name)
            if kind == "create":
                if before is not None:
                    raise ValueError("resource exists")
                obj = blank()
            else:
                if before is None:
                    raise ValueError("missing resource")
                obj = deepcopy(before)
            if kind == "set":
                if args["field"] not in obj["fields"]:
                    raise ValueError("unknown field")
                obj["fields"][args["field"]] = {"value": args["value"], "head": rid}
            elif kind == "add":
                if type(args["delta"]) is not int:
                    raise ValueError("integer delta required")
                obj["credits"][rid] = args["delta"]
            elif kind == "grant":
                if not isinstance(args["member"], str):
                    raise ValueError("string member required")
                obj["grants"][rid] = args["member"]
            elif kind != "create":
                raise ValueError("unsupported operation")
            if sum(obj["credits"].values()) < 0:
                raise ValueError("negative balance")
            obj["rev"] += 1
            obj["component_rev"][kind] += 1
            receipt = {"id": rid, "context": asdict(context), "name": name, "kind": kind,
                       "args": deepcopy(args), "generation": obj["generation"],
                       "before": before, "after": deepcopy(obj), "expires": now + ttl}
            self.db.execute("INSERT INTO receipts VALUES(?,?,0)", (rid, json.dumps(receipt, sort_keys=True)))
            self._put(context.tenant, name, obj)
            return rid

    def peer(self, context, event, name="resource", *, eid=None):
        """Trusted peer fixture. Every write, even same-value writes, changes provenance."""
        eid = eid or uuid.uuid4().hex
        with self.transaction():
            obj = self._get(context.tenant, name)
            if event["op"] == "recreate":
                # Revision deliberately resets: generation is the protection against ABA.
                obj = blank(eid)
                obj["rev"] = 1
                obj["component_rev"]["create"] = 1
            elif event["op"] == "delete":
                obj = None
            else:
                if obj is None:
                    return
                op = event["op"]
                if op == "set":
                    obj["fields"][event["field"]] = {"value": event["value"], "head": eid}
                elif op == "add":
                    if sum(obj["credits"].values()) + event["delta"] < 0:
                        return
                    obj["credits"][eid] = event["delta"]
                elif op == "grant":
                    obj["grants"][eid] = event["member"]
                elif op == "revoke":
                    obj["grants"] = {k: v for k, v in obj["grants"].items() if v != event["member"]}
                else:
                    raise ValueError(op)
                obj["rev"] += 1
                obj["component_rev"]["grant" if op == "revoke" else op] += 1
            self._put(context.tenant, name, obj)

    def compensate(self, context, receipt_id):
        """Public recovery API. Identity is supplied by the trusted host, not the model."""
        return self._research_compensate(context, receipt_id, "undoscope")

    def _research_compensate(self, context, receipt_id, policy="undoscope", *, now=None,
                             omit=frozenset(), crash=None, before_transform=None):
        """Private research controls. Never expose policy, omit or hooks to an agent."""
        now = time.time() if now is None else now
        with self.transaction():
            row = self.db.execute("SELECT body,consumed FROM receipts WHERE id=?", (receipt_id,)).fetchone()
            if row is None:
                return {"status": "unknown_receipt"}
            r = json.loads(row[0])
            if "scope" not in omit and r["context"] != asdict(context):
                return {"status": "scope_denied"}
            # Authorize against the receipt owner even in the scope ablation.
            owner = r["context"]
            allowed = self.db.execute("SELECT allowed FROM policy WHERE tenant=? AND principal=?",
                                      (owner["tenant"], owner["principal"])).fetchone()
            if "policy" not in omit and (allowed is None or not allowed[0]):
                return {"status": "policy_denied"}
            if "expiry" not in omit and now >= r["expires"]:
                return {"status": "expired"}
            if "consumption" not in omit and row[1]:
                return {"status": "already_compensated"}
            obj = self._get(owner["tenant"], r["name"])
            if before_transform:
                before_transform()
            status, candidate = transform(obj, r, policy, omit)
            if status == "compensated":
                self._put(owner["tenant"], r["name"], candidate)
                self.db.execute("UPDATE receipts SET consumed=1 WHERE id=?", (receipt_id,))
                if crash == "before_commit":
                    os._exit(71)
            self.db.execute("INSERT INTO audit(receipt,status) VALUES(?,?)", (receipt_id, status))
        if crash == "after_commit":
            os._exit(72)
        return {"status": status}
