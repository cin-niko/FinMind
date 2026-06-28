---
id: SPEC-FEAT-001-CONTRACTS
feature: mvp-ui
status: active
owner: solo
created: 2026-06-26
implements:
  - src/finmind_ui
validated_by: []
adr_refs: []
---

# UI Contract: MVP UI

## Protected Shell

The authenticated shell shows `New Chat`, `Workflows`, and grouped `History`.
Unsupported roadmap surfaces must not be active navigation entries.

## Mock Chat

Mock chat responses are deterministic and UI-local. They may show trusted local
inline visuals and artifact cards. They do not run tools, collect live data,
execute generated HTML, or represent production evidence-backed chatflow.

## Artifact Detail

Artifact cards open a right-side detail panel on desktop and a full-screen detail
view on mobile. Detail headers remain compact and pinned.
