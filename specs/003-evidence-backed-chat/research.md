---
id: SPEC-FEAT-003-RESEARCH
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by: []
adr_refs: []
---

# Research: Evidence-Backed Chat

## Decision: Keep chat thin over shared evidence and data

Chat should answer open-ended questions and support inline visualization, but it must rely on the same canonical data, evidence, citations, chart artifacts, and execution records as fixed workflows. This avoids trust drift between app surfaces.

## Decision: Show role/tool status, not raw reasoning

Users need inspectable status and evidence, not hidden reasoning transcripts. Raw model reasoning remains internal.
