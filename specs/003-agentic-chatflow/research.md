---
id: SPEC-FEAT-003-RESEARCH
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Research: Agentic Chatflow

## Decision: Keep production chatflow separate from mock chat UI

Production chatflow needs collection, evidence, citation, safety, and evaluation
contracts that are not required by the current deterministic mock chat UI.

Alternatives considered: treating mock chat as the chatflow feature. Rejected
because it would overstate implemented behavior.

## Open Research

- Trusted source inventory for VN and US stocks.
- Data rights and licensing constraints.
- Collection and citation strategy.
- Freshness and stale-data handling.
- Evaluation set for hallucination, unsupported claims, and safety refusals.
- Latency and cost targets.
