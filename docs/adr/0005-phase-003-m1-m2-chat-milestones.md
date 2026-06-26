---
id: ADR-0005
title: Split Phase 003 into M1 chat-over-prices and M2 fundamentals
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/003-evidence-backed-chat/spec.md
  - specs/003-evidence-backed-chat/research.md
  - specs/README.md
---

# ADR-0005: Split Phase 003 into M1 chat-over-prices and M2 fundamentals

## Context

Phase 002 was nearing implementation complete but blocked on multi-market free
data. VN-only V1 (ADR-0001) + daily canonical prices (ADR-0002) unblock a smaller
data layer. Chat (Phase 003) was originally specified as "VN stocks and gold"
open-ended Q&A requiring citations, charts, and shared evidence contracts.

A reference architecture comparison (Bloomberg / Perplexity-style stack) highlighted
a **fundamentals layer** (`companies`, `financial_facts`, `earnings`) as the main
gap vs. price-only evidence. Two options emerged:

- **Option 1:** Expand Phase 002 to include fundamentals before chat.
- **Option 2:** Close Phase 002 on prices; add fundamentals inside Phase 003.

Fundamentals schema is easy to over-model without concrete chat use cases.

## Decision

**Option 2 with two ship milestones:**

- **003.M1 — Chat over prices:** Chat workflow over Phase 002 V1 data
  (`vn_prices_daily` canonical, `vn_prices` best-effort) using existing evidence,
  citation, artifact, and execution contracts. Proves end-to-end grounding without
  new ingestion datasets.

- **003.M2 — Fundamentals + fundamentals-cited chat:** Add typed fundamentals
  storage and vnstock-derived ingestion via the existing source connector contract.
  Extend chat to cite financial facts and earnings. **M2 must not block M1.**

**SC-010 gate:** Document ≥3 concrete chat use cases before M2 schema implementation
(recorded in `specs/003-evidence-backed-chat/research.md`).

Fundamentals layer is **not** expanded into Phase 002 scope.

## Consequences

### Positive

- Phase 002 has a finishable boundary (T041–T049).
- M1 delivers chat + lineage proof on smallest data surface.
- M2 schema driven by real use cases (VPB NII trend, VN30 bank screen, VHM
  earnings narrative).

### Negative / trade-offs

- M1 chat cannot answer earnings/ratio questions without capability-limitation
  responses until M2 ships.
- Phase 003 calendar extends across two milestones.

### Neutral

- Object storage (S3/MinIO) deferred until M2 document ingestion needs it.

## Alternatives considered

### Option 1: Fundamentals in Phase 002

- Pros: Chat lands with full data depth on day one.
- Cons: 20+ tasks; delays V1 ingestion close-out; schema without use-case pressure.
- **Rejected** on 2026-06-25.

### Option 2 plain: Single Phase 003 with fundamentals before chat UI

- Pros: One milestone.
- Cons: Longer blocking path before any chat ships.
- **Rejected**; prefer M1/M2 split.

### Option 3: Chat without evidence tables (chat-specific store)

- Pros: Faster chat prototype.
- Cons: Violates constitution III (Evidence-Backed User Surfaces); trust drift vs.
  workflows.
- **Rejected**; see ADR-0006.

## References

- [`specs/003-evidence-backed-chat/spec.md`](../../specs/003-evidence-backed-chat/spec.md) — Milestones, FR-026–029
- [`specs/003-evidence-backed-chat/research.md`](../../specs/003-evidence-backed-chat/research.md) — SC-010 use cases
- [`docs/research/perplexity-finance.md`](../../docs/research/perplexity-finance.md)
- ADR-0001, ADR-0002
