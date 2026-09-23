# NDC Security 2027 proposal

**Title:** Your AI Agent's Undo Button Is a Security Boundary

**Format:** Regular talk, 60 minutes

**Main topic:** Securing AI

**Related topics:** Agentic AI; Application Security; Architecture; Security Testing

**Level:** Intermediate / advanced practitioner

**Language:** English

**Target audience:** Developers, security engineers, platform engineers, and architects building tool-using agents that change application state.

## Public abstract

An AI agent grants a contractor access. Its workflow fails, so it calls the obvious undo: revoke access. But another workflow has since granted that person access too. The agent has cleaned up its own work by breaking someone else's.

Recovery is a security boundary. The model can choose the correct tool and the correct receipt, and the backend can still apply an unsafe inverse.

In this session, we will break and rebuild an agent's recovery path using a live Python and MCP demo. We will reproduce same-value updates that fool value checks, independently owned permissions that disappear during cleanup, and resource names that refer to a different object by the time recovery runs. We will also show why rejecting every changed object protects safety while blocking useful recovery.

Then we will implement UndoScope: a narrow recovery API that accepts a committed-effect receipt, binds it to the authenticated workflow, and checks current authority, object identity, and operation-specific provenance in the same transaction as the inverse. We will crash the process and race duplicate requests to test the boundary.

The examples are backed by an open-source artifact, a technical report, 1,364 enumerated event histories, and 240 live model recovery tasks. One finding is especially useful: a hardened prompt eliminated wrong-receipt choices for one tested model, while the ordinary inverse backend still damaged peer state.

You will leave able to identify unsafe compensation patterns, design recovery tools with narrower authority, and add concurrency, revocation, and retry cases to your agent-security tests.

## Reviewer notes

This is a research-backed engineering talk with working local demonstrations. The evidence comes from controlled experiments, and the presentation distinguishes measured behavior from deployment assumptions. The techniques build on sagas, selective undo, provenance, and capability enforcement; the contribution is the explicit recovery-isolation contract and reproducible comparison.

Planned running order: 0-7 minutes, break a permission cleanup; 7-17, define the recovery threat model and supported effect types; 17-30, demonstrate value, snapshot, and coarse-version failures/tradeoffs; 30-44, implement the receipt-bound transactional adapter; 44-53, run crash/retry checks and explain the paired model findings; 53-60, integration checklist and questions.

Demos run locally without conference Wi-Fi or paid APIs. An offline trace viewer is included as a fallback; the CLI and MCP adapter execute the operations live. The talk will clearly explain the limits for dependent workflows, irreversible effects, and external APIs without conditional writes.

Artifact: https://github.com/shi1720/undoscope
Paper: https://github.com/shi1720/undoscope/blob/main/output/pdf/undoscope-paper.pdf

This talk has not previously been presented at a conference. No prior-talk recording is supplied.

## Speaker

**Shivam Gupta**

**Tagline:** Applied AI Engineer and Founder, Siloed

**Biography:** Shivam Gupta is an applied AI engineer and founder of Siloed, an AI product consultancy. He builds production LLM applications and operational agents, with work spanning enterprise software, structured-output validation, evaluation harnesses, and observability. His experience includes senior AI product engineering roles across enterprise and education products, and leading practical AI adoption workshops for technical and business teams. He holds a B.Tech in Computer Science and Design from IIIT Delhi. His current research focuses on making agent behavior reproducible, inspectable, and safer at the boundary between language models and application state.

**Email:** shivam1720406@gmail.com

**Travel origin:** New Delhi, India - Indira Gandhi International Airport (DEL), inferred from the supplied resume's Delhi location and current India context.

**Travel support requested:** Travel and accommodation.

## Verified event facts

CFP closes 18 October 2026 at 23:59 UTC+02:00. Event dates: 15-18 February 2027, Radisson Blu Scandinavia, Oslo. The event's Sessionize page states travel/accommodation expenses covered and free speaker attendance. The submission is for a 60-minute talk, not a research-paper proceedings track.

Sources: https://ndcsecurity.com/call-for-papers and https://sessionize.com/ndc-security-2027/ (checked 23 September 2026).
