---
id: SPEC-FEAT-004-CONTRACTS
feature: extension-hardening
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Artifact Contract: Extension Hardening

Reusable artifacts must expose:

- stable artifact id
- artifact type
- title
- linked inputs
- renderable payload
- evidence references
- execution run reference
- freshness/source metadata where applicable

Workflow chart artifacts and chat inline artifacts must be consumable through the same artifact family.
