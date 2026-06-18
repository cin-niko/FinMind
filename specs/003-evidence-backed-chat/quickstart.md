---
id: SPEC-FEAT-003-QUICKSTART
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Quickstart: Evidence-Backed Chat Validation

1. Open the chat tab.
2. Ask a supported VN stock or gold question.
3. Ask a question outside V1 scope, such as a US stock or BTC request.
4. Ask a question that benefits from visualization.

Expected result: supported answers include citations, freshness, execution status, and inline visualization where useful. Unsupported market questions clearly state the V1 scope limitation.
