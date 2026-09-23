# Implementation corrections before manuscript analysis

The initial field-version baseline incorrectly checked the creation component counter for a created object. Peer field writes do not increment that counter. A reasonable object-deletion compensator must guard the whole object's revision, so this was corrected before freezing the result tables. The initial diagnostic run is not the reported dataset. This makes the field-version comparator stronger rather than exaggerating the proposed method's advantage.

The contribution ledger makes UndoScope's additive retraction intrinsically idempotent. Therefore consumption-log ablation alone need not produce double debits. Report this redundancy; do not claim every guard is independently necessary for every operation. A mapped arithmetic inverse still needs atomic deduplication.

Two two-episode API transport pilots exposed an SDK serialization incompatibility: response `model_dump` emitted `async_`, whereas the wire API expects `async`. The primary collection stores aliases correctly and supplies only the selected function-call wire fields in the continuation. Both pilot files are retained separately and excluded from the 240-task evaluation. No attack wording or baseline changed after observing the pilot decisions.

After the primary measurements, three deterministic-seeded property tests were added for longer random register, counter, and grant histories (100 generated examples each). Their local oracles use last-writer, arithmetic, and tag-set rules directly. They validate implementation properties and do not enlarge the reported 1,364-history benchmark.

The artifact environment pins the original API transport versions (httpx2/httpcore2 2.13.0) and OpenAI SDK 3.19.0. Python 3.12 is required by the pinned research dependencies. The collector subsequently gained an explicit output-path argument; this does not change the frozen task contents or inference parameters.
