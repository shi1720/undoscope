# Security scope

UndoScope is a research reference, not a production security product. The adversary may control model-visible tool prose and tool choices; it must not have direct database access, access to the embedded administrative APIs, or the ability to select an authenticated context.

Only `recover_effect(receipt_id)` is exposed over the local MCP transport. Research controls (`_research_compensate`, omission flags, crash hooks), `seed`, `peer`, `set_policy`, and `forward` are trusted test/application interfaces. Exporting them to an untrusted agent voids the model. Forward business authorization remains the host's responsibility.

Supported recovery protects independent local effects. Do not infer support for compensating dependent workflows, remote financial transactions, sent messages, or policy revocations. Do not wrap an unconditional provider write in a separate version precheck and call it atomic.

Scope/policy/expiry denial reasons are returned to the host; the reference audit table is not a complete compliance audit. Retention, key management for portable tokens, authenticated remote transport, backup rollback protection, and production concurrency tuning require deployment-specific engineering.

For a defect in this artifact, open a GitHub issue using a synthetic reproduction with no credentials or customer data. Never post API keys or production receipts.
