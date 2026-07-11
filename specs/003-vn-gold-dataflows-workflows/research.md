---
id: SPEC-FEAT-003-RESEARCH
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Research: VN And Gold Dataflows And Workflows

## Decision: Reuse Phase 02 Evidence Boundaries

Phase 03 uses the existing collection-first, deterministic-record, citation-
allowlist, grounding, artifact, and run-store boundaries rather than creating a
gold-only execution path.

Rationale: market-specific collection differs, but evidence safety and user
inspection must remain consistent across markets.

Alternatives considered: a standalone gold service or raw provider payloads in
gold prompts. Rejected because both would duplicate or bypass safety controls.

## Decision: Treat Gold Source Selection As A Planning Gate

Phase 03 will support a bounded gold instrument or benchmark only after its
provider, licensing/usage eligibility, timezone, currency/unit, expected
freshness, fallback labeling, and available datasets are explicitly selected.

Rationale: a generic "gold" feed does not define an auditable user-facing
instrument or safe claim boundary.

Alternatives considered: enabling broad commodities or using an unverified
public source. Rejected because both make provenance and supported claims vague.

## Decision: Make Market Scope Explicit At The Catalog Boundary

The catalog enables only `VN_STOCK` and `GOLD`. Other markets must not be
selectable, configured, or retained as active fixtures.

Rationale: users should see scope before submission, not learn it from a failed
request after running a workflow.

## Decision: Move Unfinished Workflow Maturity To Phase 03

The Phase 02 stock brief, field validation, run-history, citation reinspection,
delivery documentation, and manual validation work become Phase 03 tasks.

Rationale: these are required to make the VN stock and gold workflow experience
whole, while Phase 02 remains the already-built technical foundation.

## Decision: Keep Chatflow Fully Deferred

Phase 03 does not add conversational routing, chat persistence, flexible tool
selection, or chat streams. Those are Phase 04 responsibilities.

Rationale: bounded dataflows and repeatable workflows establish grounded market
behavior before flexible research interaction is introduced.
