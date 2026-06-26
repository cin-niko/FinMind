---
id: SPEC-FEAT-003-RESEARCH
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by: []
adr_refs:
  - docs/adr/0005-phase-003-m1-m2-chat-milestones.md
---

# Research: Evidence-Backed Chat

## Benchmark: Perplexity Finance

External product benchmark for AI-native finance research surfaces, data
aggregation patterns, and citation UX. See
[`../../docs/research/perplexity-finance.md`](../../docs/research/perplexity-finance.md).

Use it when scoping Phase 003.M1 chat surfaces and Phase 003.M2 fundamentals
(SC-010 use cases below). It is not normative; behavior remains in
`spec.md`.

## Decision: Keep chat thin over shared evidence and data

Chat should answer open-ended questions and support inline visualization, but it must rely on the same canonical data, evidence, citations, chart artifacts, and execution records as fixed workflows. This avoids trust drift between app surfaces.

## Decision: Show role/tool status, not raw reasoning

Users need inspectable status and evidence, not hidden reasoning transcripts. Raw model reasoning remains internal.

## SC-010 candidate use cases (M2 fundamentals gate)

Record at least three concrete chat use cases before M2 schema work begins.
Derived from the Perplexity Finance benchmark and adapted for VN100:

1. **Quarterly trend:** "How did VPB's net interest income trend over the last
   four quarters?" Requires `financial_facts` (income statement line items,
   fiscal period, currency).

2. **Cross-instrument screen:** "Compare VN30 banks by P/B and ROE; show the
   three cheapest on a quality basis." Requires fundamentals, computed ratios,
   and multi-instrument comparison.

3. **Earnings narrative:** "Summarize VHM's most recent earnings — what did
   management say about Q4 guidance?" Requires earnings events and
   `source_documents` (transcript or filing excerpt) with point-in-time
   citation.

See [`../../docs/research/perplexity-finance.md`](../../docs/research/perplexity-finance.md)
for the full benchmark context.
