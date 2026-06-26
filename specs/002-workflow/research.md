---
id: SPEC-FEAT-002-RESEARCH
feature: workflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Research: Workflow

## Decision: VN stocks and US stocks are current workflow scope

VN and US stocks prove the current equity research workflow surface while keeping
gold, BTC, and other assets out of active scope.

Rationale: The product goal is agentic financial trading research advice, but data
access and safety scope must stay bounded. Two equity markets are enough for the
current workflow contract.

Alternatives considered: VN stocks plus gold, all markets, or crypto. Rejected
because the current scope is VN stocks and US stocks only.

## Decision: Use fixed workflow execution before flexible chatflow

Fixed workflows provide predictable, testable analysis paths and make evidence,
citations, freshness, chart artifacts, and run inspection easier to verify.

Alternatives considered: production flexible agentic Q&A first. Rejected because
trusted-source retrieval and chatflow safety need a separate bounded spec.

## Decision: Use seeded/demo repositories for workflow validation

Seeded/demo canonical records allow contract-first validation before native
realtime market data and news integration are available.

Alternatives considered: live data integration in this feature. Rejected because
source rights, provider reliability, and production freshness rules need later
planning.
