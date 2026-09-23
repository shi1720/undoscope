# UndoScope: frozen initial protocol

Date: 2026-09-23. Author: Shivam Gupta. This file is written before outcome collection. This is a local protocol, not an external preregistration.

## Question and contribution
Can a recovery tool remove a committed agent effect without overwriting independent intervening work or borrowing authority from another workflow? Study operation-specific recovery, not universal rollback. The proposed contribution is a benchmark and executable recovery-security contract combining established compensation, provenance, version checks, and runtime authorization. No claim of invention of sagas, capability security, selective undo, compare-and-swap, or at-most-once effects.

## Mechanism
Trusted adapters persist effect receipts at forward commit. A caller can request compensation by receipt identifier only. Trusted session context supplies tenant, principal, and run. Within one SQLite write transaction, recovery checks receipt scope, current recovery policy, expiry, object incarnation, and operation-specific evidence; consumes the receipt and commits the inverse atomically. Register writes require provenance-head equality; additive effects retract their own ledger entry subject to a nonnegative-balance invariant; grants remove their own tag; created resources require unchanged incarnation and revision. Unsupported or conflicting recovery is refused. This is a single-database reference design, not a distributed transaction claim.

## Threat model
An adversary can control tool-result prose, request another visible receipt, repeat requests, cause failure after forward commit, and interleave authorized peer operations. It cannot edit the trusted database/adapter, forge authenticated context, bypass the adapter, or redefine operation semantics. Recovery changes are assessed independently of natural-language success claims.

## Baselines
All non-ablation baselines share receipt authenticity, scope, current-policy checks, incarnation check, expiry, and atomic single consumption. Compare snapshot restoration, mapped inverse, value guard, object-version guard, field-version guard, typed effect-scoped recovery, and deny-all. These are explicitly implemented mechanisms, not measurements of unmodified published systems.

## Experiments
1. Bounded exhaustive event histories (depth <=4) for registers, counters, tagged grants, and created resources; deterministic oracle and raw rows. Publish exact structural counts, not population estimates or binomial confidence intervals over enumerated cases.
2. A fixed case matrix exercising disjoint updates, same-value reaffirmation, ABA, repeated independent grants, resource reuse, policy revocation, wrong scope, malformed receipt, replay, and expiry. Remove one guard at a time, preserving identical inputs. This tests necessity within the stated model, not empirical prevalence.
3. Persistent SQLite tests: concurrent duplicate recovery, true process exit before commit and after commit, and a check/use race controlled by synchronization. Count externally visible effects, not return strings.
4. Live model tool-selection study: two pinned model snapshots; four domains; clean, concurrent, and injected-receipt conditions; five parameter seeds; ordinary versus hardened prompt (240 first-stage requests total). Replay each actual selected tool decision against mapped-inverse and UndoScope backends on identical state. Follow each with a second model response so unsupported success assertions can be inspected. Record prompts, full API response metadata, token usage, tool calls, tool results, transport errors, and timestamps. Temperature zero, no success-based exclusion. This is a controlled recovery subtask, not a full autonomous production agent benchmark. Target <= USD 15 estimated spend; use small bounded outputs. If API access fails, report it and make no empirical model claim.
5. Local latency: paired persistent-database operations, warmup, randomized policy order, median/p95 and environment disclosure. No cloud-latency or throughput extrapolation.

## Outcomes
Collateral mutation: a recovery changes protected peer state or applies an unauthorized effect. Safe completed recovery: expected operation-specific inverse applied without collateral mutation, measured only over histories where the predeclared oracle permits compensation. Refusal is safe but not successful recovery. Superseded register/create histories are not counted as recoverable. Other actors' reads, dependent workflows, irreversible communications, and external APIs lacking atomic conditional writes remain outside the guarantee.

## Analysis discipline
Keep all first-stage model outputs, errors, and second-stage outputs. Do not increase sample size in response to significance or cherry-pick attack wording. Report constructed coverage separately from model behavior. Any protocol changes must be recorded in an amendment before the affected run. Verify data-derived manuscript numbers with a separate audit script. Literature absence is not a proof of priority or patentability.
