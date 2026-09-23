# Your AI Agent's Undo Button Is a Security Boundary

60-minute talk. Shivam Gupta. Draft speaker notes accompanying the tested artifact.

## 0-7 min — Start with a failure the model did not cause

Show the shared-grant scene. An agent grants a contractor access, another workflow adds its own grant, and the first workflow fails. Ask the audience what `revoke(contractor)` will remove. Execute the mapped inverse and show that both contributions disappear. Replay the same scene with UndoScope: the other workflow's grant remains.

Command: `uv run undoscope-demo --scenario shared-grant`.

Explain the central question: what did this workflow own, and what may its cleanup change? Describe this as a controlled reproduction, never a customer incident.

## 7-17 min — Define the boundary

Draw the agent, authenticated host, domain adapter, and database. Separate the selection of a receipt from authority to use it, and authority from correctness of its inverse. Walk through the four effect families in the paper. Cite sagas and selective undo directly. Explain why sent messages and dependent workflows need different treatment.

Use the architecture figure and one concrete receipt. Show that scope comes from trusted context, not JSON supplied by the model. Identify how a genuine receipt from another workflow is still unauthorized.

## 17-30 min — Break three plausible implementations

1. Snapshot restore erases a support engineer's unrelated note. Run `--scenario disjoint-change` and compare snapshot, object guard, and UndoScope.
2. Value guards miss the engineer deliberately confirming the same ticket status. Run `--scenario same-value`. Explain the two indistinguishable value histories and the missing provenance witness.
3. A new resource inherits an old name and revision number. Run `--scenario name-reuse`. Show why incarnation must be separate from name and version.

Acknowledge the strong comparator: an object guard is safe in these cases. Its cost is refusing recoveries that could preserve peer state. Do not call a conservative refusal a security failure.

## 30-44 min — Implement a narrow recovery API

Open `src/undoscope/store.py` and the typed transform. Start at the exposed `compensate` method, then show current-policy and scope checks, incarnation, typed evidence, and atomic consumption. For each type, identify the minimum application-specific evidence and the inverse it authorizes.

Use the real MCP test to demonstrate the transport interface: `uv run pytest tests/test_mcp.py -q`. Its tool schema contains only a receipt identifier. Mention that network authentication is outside the local demonstration.

Show the register LIFO test and the conservative created-object limit. Discuss storage overhead: full before/after snapshots are convenient for the artifact but not a storage optimization.

## 44-53 min — Test what happens after the happy path

Run `uv run pytest tests/test_recovery.py -q`. Explain the two real process-death injection points and the 32-attempt concurrency batches. Use the data from `results/durability.jsonl` rather than rerunning the full timing suite on stage.

Show the paired model table: prompt hardening removed wrong-receipt choices for the tested GPT-4.1 prompts but left mapped semantic failures intact. Clearly separate 240 recovery subtasks from autonomous end-to-end production agents. Show one raw response paired with the actual corrupted state to explain why a completion statement is not a success metric.

## 53-60 min — Apply the contract and take questions

Leave attendees with five integration questions:

- Can the adapter name the individual committed effect and bind its recovery scope?
- Does every writer update the evidence, including same-value writes?
- Does the inverse preserve independent contributions or merely reset a value?
- Are policy/state checks and inverse consumption atomic at the resource boundary?
- Is refusal surfaced as incomplete recovery, with a route for operator review?

Close with the repository and paper. Reserve at least five minutes for questions. If the discussion runs long, skip latency detail; keep the explicit limitations and integration questions.

## Demo fallback and setup

All primary demos run without an API key or internet. Serve the repository locally with `python -m http.server 8765 --bind 127.0.0.1`, then open `/demo/`. The offline viewer is explicitly labeled as generated traces; the CLI is the live execution path. Keep a PDF copy of the figures available.

Before rehearsal, run tests and the data audit. Do not regenerate the paid model experiment on stage. Use a fresh terminal with no credentials displayed. The live demonstrations use disposable local fixture databases only.
