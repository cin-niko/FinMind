---
id: SPEC-FEAT-004-CONTRACTS
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Chatflow Contract: Agentic Chatflow

Draft contract requirements:

- Every material claim has citations or unsupported/unavailable marking.
- Every answer includes citation provenance (source id, dataset id, timestamp)
  where data is time-sensitive; cited sources must be a subset of collected sources.
- Tool, collection, citation, and artifact failures are visible to the user.
- Raw agent reasoning, hidden prompts, secrets, and unsafe diagnostics are never
  user-visible.
- Trade execution, order placement, and broker actions are not supported.
- Market scope starts from VN stocks and gold until a later spec expands scope.
