# UndoScope

**Effect-scoped compensation for tool-using agents.**

An agent can select the correct undo operation and still erase someone else's work. UndoScope is a research reference and reproducible security benchmark for recovery that preserves independent intervening effects.

[Read the paper](output/pdf/undoscope-paper.pdf) · [Open the offline demo](demo/index.html) · [Research protocol](protocol/research-plan.md) · [Literature audit](protocol/literature-review.md)

Author: **Shivam Gupta**. Technical report, 23 September 2026. The accompanying 60-minute NDC Security 2027 talk proposal was submitted on 23 September 2026 and is in evaluation. This is not an accepted conference paper. See the [submission record](submission/status.md).

## What was actually measured

- **1,364 bounded event histories × 7 policies = 9,548 evaluations.** Mapped inverses caused 521 collateral outcomes; UndoScope caused zero and completed all 678 contract-eligible recoveries. Object and component guards also caused zero collateral outcomes, while completing 4 and 42 eligible recoveries.
- **240 live model recovery tasks, 720 completed API responses.** The same selected tool calls were replayed against mapped and UndoScope backends: 60 versus zero collateral outcomes. Both backends enforced the same scope checks.
- **90 persistent SQLite schedules:** 60 real process-termination trials and 30 concurrent batches (960 attempts), all meeting their specified postconditions.
- **27 tests**, including three property tests with 100 generated examples each and a real MCP stdio exchange.

These are controlled fixtures, not vendor failure rates. The main grammar is deliberately heavy on interference. Register and creation cases have only 5 and 1 eligible histories respectively; see the per-domain figures before interpreting aggregate recovery coverage.

## Reproduce without API access

Python 3.12+ and [uv](https://docs.astral.sh/uv/) are required for the pinned research environment. The runtime core itself has no third-party dependencies.

```bash
uv sync --extra research
uv run python scripts/release_manifest.py --check
uv run pytest -q
uv run python scripts/audit_results.py
uv run undoscope-demo --scenario shared-grant
```

The release manifest verifies the versioned files before regeneration. The audit recomputes all summary counts, checks 720 unique API response records, and replays all 480 model/backend branches against saved state outcomes.

To regenerate the deterministic benchmark and figures:

```bash
uv run python scripts/run_exhaustive.py
uv run python scripts/run_systems.py
uv run python scripts/analyze_models.py
uv run python scripts/make_tables.py
uv run python scripts/make_figures.py
uv run python scripts/build_demo.py
bash scripts/build_paper.sh
```

Paper compilation additionally requires [Tectonic](https://tectonic-typesetting.github.io/). Timing changes across machines. Re-running the benchmark overwrites derived result files; the committed release preserves the reported measurements. `run_systems.py` uses and removes temporary databases automatically.

## Live model collection

The included raw data can be analyzed offline. A fresh collection incurs API charges and is optional. The original study used pinned GPT-4.1 and GPT-4.1 mini snapshots; the collector logs the returned model identifiers and usage.

```bash
uv run python scripts/run_models.py --output results/fresh-models.jsonl
```

The key is read from `OPENAI_API_KEY` or a hidden terminal prompt and is never written to the artifact. The collector resumes missing episode IDs in the selected file. It does not retry API failures automatically or discard failures. `--pilot` runs two transport probes in a separate file. The committed pilot records preserve a serializer issue fixed before the primary collection.

The clean and concurrent probes use five identifier variants per domain; the injection condition has five frozen attack texts. They are not 240 independent production tasks. First-stage decisions are paired across equivalent fixtures; fresh opaque creation IDs may differ. The follow-up response is recorded for inspection, while state integrity is scored from the tool state.

## Mechanism

A trusted adapter records an effect at forward commit. The only public recovery mutation accepts a receipt identifier. Tenant, principal, and workflow come from the authenticated host. In one SQLite write transaction, the adapter checks:

1. Receipt scope, current recovery permission, expiry, and consumption.
2. Resource incarnation and operation-specific evidence.
3. The inverse's domain invariant.
4. The inverse and consumed receipt commit together.

| Effect | Recovery semantics |
|---|---|
| Register assignment | Restore its predecessor only while the field's provenance head belongs to the effect. |
| Additive contribution | Retract its own ledger entry, preserving other contributions and a nonnegative balance. |
| Grant addition | Remove only its own grant tag; preserve independently granted membership. |
| Resource creation | Delete only the unchanged original incarnation. |

The research controls and omission flags are private Python APIs. **Do not expose them as agent tools.** The MCP adapter exports only `recover_effect(receipt_id)`; its immutable context is supplied at process startup by the host.

```bash
uv run undoscope-mcp --database /path/to/trusted.db \
  --tenant acme --principal agent --run run-1
```

The database must be populated by the trusted application adapter. `RecoveryStore.forward` is an embedded trusted API, not a replacement for forward-action authorization. The local stdio example demonstrates context binding, not multi-tenant network authentication.

## What this does not establish

This is a single-store, instrumented reference. It does not provide universal rollback, distributed exactly-once execution, recovery of sent communications, safe reversal of revocations, or preservation of downstream effects that depended on the original action. An external provider needs conditional writes or effect identifiers to support comparable guarantees. Complete mediation and provenance updates are required.

The prototype stores full snapshots and rewrites JSON state. It has no production retention, network authentication, or complete denial-audit service. Current authority changes may deliberately prevent cleanup. A created object with later edits is conservatively retained even if its own workflow later undoes those edits.

## Relation to prior work

Compensation, selective undo, contribution ledgers, and capability enforcement are established techniques. The contribution is the recovery-isolation contract, its executable benchmark/oracle, paired model study, and a tested integration pattern. The baseline mechanisms are implemented here; they are **not** measurements of unmodified RAC, SagaLLM, or commercial systems. See the [review](protocol/literature-review.md) and the paper's references.

## Artifact map

| Path | Contents |
|---|---|
| `src/undoscope/store.py` | Trusted persistent adapter and context binding |
| `src/undoscope/policies.py` | Typed inverse and explicit comparator mechanisms |
| `src/undoscope/bench.py` | History grammar and separate trace oracle |
| `src/undoscope/model_tasks.py` | Frozen prompts, tools, and model fixtures |
| `tests/` | Contract, property, crash/race, and MCP tests |
| `results/` | Raw enumeration, API records, durability trials, timing, summaries |
| `paper/` | LaTeX, generated tables, six vector figures |
| `demo/` | Offline viewer generated from actual local executions |
| `submission/` | Talk proposal, timed outline, and submission status |

MIT-licensed code and accompanying original artifact material. Cite with `CITATION.cff`. No acceptance, patentability, or production-readiness claim is made.
