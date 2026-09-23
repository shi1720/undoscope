# Literature and novelty audit

Search date: 23 September 2026. Primary sources were prioritized. Searches covered agent compensation, recovery security, selective undo, same-value/ABA conflicts, provenance, capability-bound recovery, commit-time authorization, and checkpoint replay. This is a scoped review, not proof that no related system exists. No patent-priority claim is made.

## Topic rejected before implementation

A broad proposal for approval tokens, state witnesses, and commit-time authorization would substantially overlap OpenPort (arXiv:2602.20196), Intent-Governed Access Control (2606.22916), Temporary Authority, Permanent Effects (2607.10487), and Mind the Gap (2508.17155). These results caused selection of recovery-effect isolation instead. There is also an existing NDC proposal on approvals in the account; the current proposal addresses recovery and compensating writes.

## Closest antecedents and exact distinction

| Primary source | Established contribution / relevant fact | Relationship to this artifact |
|---|---|---|
| Garcia-Molina & Salem, Sagas, SIGMOD 1987. https://doi.org/10.1145/38713.38742 ; technical report https://www.cs.princeton.edu/techreports/1987/070.pdf | Long-running transactions can use compensating actions. | Foundational antecedent. UndoScope does not invent compensation or its concurrency problem. |
| Microsoft Azure, Compensating Transaction pattern. https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction | Explicitly warns that restoring original state can overwrite concurrent work; calls for application-specific logic, resumability and idempotence. | Direct prior art for the motivating concurrency hazard. The paper must credit this, not claim discovery of the hazard. |
| Yjs, UndoManager. https://docs.yjs.dev/api/undo-manager | Selective undo can be scoped to transaction origins. | Direct antecedent for origin-scoped undo. The study adds an agent-facing recovery contract and explicit scope/revocation/incarnation/atomicity tests, not a new selective-undo algorithm. |
| Perera, Hapuarachchi, Leymann & Khalaf, Robust Agent Compensation, ACM CAIS 2026, DOI 10.1145/3786335.3813141; https://arxiv.org/html/2605.03409v1 | Log-based compensation manager, tool-pair/input mappings, MCP annotations, LangGraph implementation; evaluation emphasizes recovery success, latency and token usage. Discussion explicitly identifies compensation scope as future work. | Closest agent-recovery system. Our implemented mapped-inverse baseline is a mechanism control, NOT the unmodified RAC code. We do not report a RAC vulnerability or an empirical win against RAC. Our oracle specifically measures preservation of independently committed peer effects. |
| Chang, SagaLLM, https://arxiv.org/abs/2503.11951 | Context management, validation and transaction-oriented agent planning. | Upstream planning is compatible with a trusted operation-specific recovery adapter. No end-to-end performance comparison is claimed. |
| Zheng, Yang, Zhang & Quinn, ACRFence, https://arxiv.org/html/2603.20625v1 | Action replay and authority resurrection when agent checkpoints rewind but external effects do not; replay-or-fork enforcement. | Different protected transition: re-execution after checkpoint restore versus a new compensating write against interleaved external state. Deduplication and monotone authority are shared concerns. Its related-work table also mentions undoing unrelated changes; broad priority claims would be inappropriate. |
| Debenedetti et al., CaMeL, https://arxiv.org/abs/2503.18813 | Capability/data-flow enforcement independent of the language model. | Antecedent for keeping authority out of model-generated prose. No claim that prompt-independent checks are new. |
| MCP Python SDK, https://github.com/modelcontextprotocol/python-sdk | Official server/client implementation. | Transport used for the demonstrator. MCP is not assumed to provide the business-level recovery semantics. |
| Zhu et al., OpenPort, https://arxiv.org/abs/2602.20196 | Scope/ABAC, preflight impact binding, idempotency and state witnesses. | Boundary checks are adjacent established work; the distinct measured object is the compensating effect and peer-state preservation. |

## Defensible contribution

An open, bounded benchmark of recovery-effect isolation with an explicit trace oracle; an executable composition of established techniques for four supported effect types; a proof under single-store mediation and independent-peer assumptions; controlled model-generated tool decisions; durable crash/concurrency tests; and a practitioner demo. The evidence supports a research-backed industry talk. It does not support claims of an unprecedented security primitive, field prevalence, universal rollback, autonomous production-agent evaluation, or guaranteed conference acceptance.

## Research questions

1. How do inverse mapping, value checks, object checks and effect provenance trade off collateral mutation against useful recovery?
2. Which authority and state guards have distinct counterexamples, and which are redundant for an intrinsically idempotent inverse?
3. Does hardening the model prompt eliminate the need for operation-specific recovery semantics?
4. Can the reference transaction remain safe across concurrent retries and process death?

## Broader comparison discipline

No external servers are scanned or attacked. The benchmark implementations are deliberately explicit policy controls. Their failures establish counterexamples to those mechanisms, not prevalence among vendors. The workload is exhaustive only over its published four-symbol alphabets and depth bound. Enumerated histories are correlated and not a random deployment sample.
