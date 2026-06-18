---
id: SPEC-FEAT-001-RESEARCH
feature: mvp-workflow-platform
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by: []
adr_refs: []
---

# Research: MVP Workflow Platform

## Decision: VN stocks and gold are the V1 market scope

VN stocks and gold prove one stock research path and one non-stock market path without taking on US stock and BTC licensing, provider, and market-hours complexity.

## Decision: Use workflow-first execution

Fixed workflows provide predictable, testable research outputs and make TradingAgents-inspired roles such as fundamental, technical, macro, and risk analysis easier to validate.

## Decision: Use seeded/demo repositories first

Seeded/demo canonical records allow contract-first implementation before admin ingestion operations and provider validation are complete.

## Decision: Hide raw agent reasoning

Users should see citations, evidence, stages, tool/artifact status, and final grounded output, but not hidden reasoning transcripts.

## Decision: Use cookie-backed sessions

Cookie-backed sessions fit an internal browser app with one admin account and give a better path to logout and future permission boundaries than frontend-managed bearer token storage.
