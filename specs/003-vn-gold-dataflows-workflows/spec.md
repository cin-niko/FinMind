---
id: SPEC-FEAT-003
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Feature Specification: VN And Gold Dataflows And Workflows

**Feature Branch**: `[003-vn-gold-dataflows-workflows]`

**Created**: 2026-07-11

**Status**: Draft

**Input**: User description: "Move chatflow features to later Phase 04, make Phase 03 focus on building dataflows for gold plus new workflows for VN stocks and gold, support VN stock plus gold first, and defer chatflow until after that."

## User Scenarios & Testing

### User Story 1 - Build Gold Dataflows (Priority: P1)

An authenticated analyst can rely on gold workflow outputs because the system has a bounded gold dataflow that collects, normalizes, freshness-checks, and cites gold market evidence before any gold claim is shown.

**Why this priority**: Gold cannot become a safe runnable market scope until its evidence path is explicit and auditable.

**Independent Test**: Run a gold evidence collection scenario and verify gold records include source identity, dataset identity, timestamps, freshness status, citation-ready rendered context, and unavailable markings when evidence is missing.

**Acceptance Scenarios**:

1. **Given** a supported gold instrument or benchmark and available evidence, **When** gold data is collected, **Then** the resulting records expose provenance, timestamps, freshness, and citation-ready context.
2. **Given** gold evidence is stale, delayed, or unavailable, **When** collection completes, **Then** the dataflow returns visible warning or unavailable status instead of claim-ready evidence.
3. **Given** a gold workflow requests an unsupported dataset, **When** the dataflow validates the request, **Then** collection is rejected or marked unavailable before answer generation.

---

### User Story 2 - Run Gold Workflows (Priority: P1)

An authenticated analyst runs fixed gold workflows that explain gold market context, trend, and risk signals using cited evidence and visible source freshness.

**Why this priority**: Gold is the next active market scope after VN stocks and must be specified before becoming a runnable workflow choice.

**Independent Test**: Run a supported gold workflow and verify the output identifies the gold instrument or benchmark, cites every material market claim, shows data freshness, and marks unsupported claim categories.

**Acceptance Scenarios**:

1. **Given** a supported gold instrument or benchmark is selected, **When** the analyst runs the workflow, **Then** the result shows trend/context sections, citations, chart artifacts when supported, and source timestamps.
2. **Given** gold evidence is stale, missing, or unavailable, **When** the result is generated, **Then** the limitation is visible before user reliance.
3. **Given** the analyst tries to use a gold workflow for an unsupported asset,
   **When** validation runs, **Then** the workflow is blocked or clearly marked
   unsupported.

---

### User Story 3 - Run New VN Stock Workflows (Priority: P1)

An authenticated analyst runs new fixed VN stock workflows that extend the Phase 02 foundation with additional bounded research views while preserving citations, chart artifacts, execution status, and advice-only framing.

**Why this priority**: VN stock remains the primary workflow market, and new workflows should reuse the canonical VN dataflow rather than duplicate collection or evidence rules.

**Independent Test**: Run each new VN stock workflow for a valid symbol and verify the result includes cited source-backed sections, clear unavailable states, expected artifacts, and no autonomous trading decision.

**Acceptance Scenarios**:

1. **Given** a supported VN stock symbol and available evidence, **When** the analyst runs a new VN workflow, **Then** the result presents bounded research sections with citations and source provenance for material claims.
2. **Given** a new VN workflow requires price, financial, profile, or derived evidence, **When** the selected source cannot provide enough records, **Then** the affected section is marked unavailable or partial instead of fabricated.
3. **Given** the analyst runs the VN stock brief workflow, **When** collection,
   grounding, fundamental, and technical stages execute, **Then** the result
   shows each stage and preserves successful sections when another stage is
   partial or unavailable.
4. **Given** the output includes a recommendation-style interpretation, **When** the analyst reviews it, **Then** the wording remains advice support and does not instruct an autonomous buy, sell, or order action.

---

### User Story 4 - Compare VN Stock And Gold Scope Boundaries (Priority: P2)

An authenticated analyst can distinguish which workflow types apply to VN stocks and which apply to gold, including what evidence, charts, and limitations each market supports.

**Why this priority**: Adding gold expands scope; users must not confuse stock-specific financial analysis with commodity-style market analysis.

**Independent Test**: Open the workflow catalog and verify VN stock and gold workflows expose distinct purposes, supported inputs, data freshness expectations, output sections, and unavailable claim categories.

**Acceptance Scenarios**:

1. **Given** the analyst opens the workflow catalog, **When** VN stock and gold workflows are listed, **Then** each workflow clearly states its market scope and required inputs.
2. **Given** the analyst selects a gold workflow, **When** stock-only sections such as company fundamentals are not applicable, **Then** those sections are not shown as available gold outputs.
3. **Given** the analyst selects a VN stock workflow, **When** gold-specific market context is not part of that workflow, **Then** gold outputs are not mixed into the stock result.

---

### User Story 5 - Reinspect Workflow Runs (Priority: P2)

An authenticated analyst can reopen completed VN stock and gold workflow runs from history and inspect output, citations, artifacts, limitations, and execution status.

**Why this priority**: VN stock and gold workflows must support repeated review and auditability, not only one-time streaming output.

**Independent Test**: Complete a VN stock run and a gold run, reopen each from history, and verify cited output, artifacts, and status are restored without raw reasoning.

**Acceptance Scenarios**:

1. **Given** a workflow run completed, **When** the analyst reopens it from history, **Then** the saved result, citations, artifacts, and execution status remain inspectable.
2. **Given** a run completed with partial or unavailable sections, **When** the analyst reopens it, **Then** those limitations remain visible.
3. **Given** a cited source is inspected later, **When** the analyst opens the citation panel, **Then** source identity, dataset, timestamp, and rendered evidence remain clear.

---

### Edge Cases

- Gold data is delayed, stale, unavailable, or sourced from a benchmark that does not match the selected user-facing instrument.
- VN stock financial statements, price history, or company profile records are incomplete for the selected symbol.
- A workflow category is meaningful for VN stocks but not for gold, or meaningful for gold but not for individual equities.
- The analyst asks for broker execution, autonomous trade decisions, or irreversible financial actions.
- The analyst submits an unsupported market during Phase 03.
- Citation snapshots exist but the underlying source is unavailable at reinspection time.
- A chart artifact cannot be generated safely from the available evidence.
- Concurrent workflow runs should remain responsive enough that users see progress instead of a blank state.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define Phase 03 runnable workflow scope as VN stocks and gold only.
- **FR-002**: System MUST keep chatflow behavior out of Phase 03 workflow scope; production chatflow belongs to Phase 04.
- **FR-003**: System MUST provide a gold dataflow that collects, normalizes, freshness-checks, and citation-prepares supported gold market evidence.
- **FR-004**: System MUST keep gold evidence records separate from VN stock records while exposing a consistent citation and artifact inspection model.
- **FR-005**: Users MUST be able to run fixed gold workflows with cited market context, trend, chart, and risk-signal evidence where available.
- **FR-006**: Users MUST be able to run new fixed VN stock workflows with cited business, financial, valuation, technical, and derived evidence where available.
- **FR-007**: System MUST show market-specific workflow catalog entries so VN stock workflows and gold workflows do not imply unsupported sections or inputs.
- **FR-008**: System MUST reject or clearly mark unsupported markets and assets.
- **FR-009**: Every material user-facing workflow claim MUST include citations with source identity, dataset identity, and timestamp, or be explicitly marked unsupported or unavailable.
- **FR-010**: System MUST show source freshness and unavailable-source limitations before users can rely on VN stock or gold workflow output.
- **FR-011**: System MUST generate chart artifacts only from available cited evidence and mark charts unavailable when evidence is insufficient.
- **FR-012**: System MUST preserve completed, partial, failed, and unavailable workflow statuses for reinspection.
- **FR-013**: System MUST prevent stock-only financial statement analysis from appearing as gold evidence unless a later spec defines an equivalent gold-specific source contract.
- **FR-014**: System MUST prevent gold-specific macro or commodity context from being mixed into VN stock workflow outputs unless the workflow explicitly declares that context.
- **FR-015**: User-facing workflow outputs MUST NOT expose raw agent reasoning, hidden prompts, provider secrets, credentials, raw provider payloads, or unsafe diagnostics.
- **FR-016**: Workflow outputs MUST be framed as research support, not trading decisions, executable orders, or autonomous financial actions.
- **FR-017**: System MUST keep humans in control by refusing broker actions, trade execution, order placement, and irreversible financial actions.
- **FR-018**: System MUST expose actionable failure states for stale data, missing evidence, failed collection, unavailable providers, unsafe outputs, and unsupported claim categories.
- **FR-019**: System MUST keep Phase 03 workflow outputs consistent with shared UI guidance for status, citations, artifacts, and right-panel inspection.
- **FR-020**: System MUST provide measurable responsiveness for primary workflow interaction so users receive visible progress before final output is ready.
- **FR-021**: System MUST provide a VN stock brief workflow that composes shared
  collection, grounding, fundamental, and technical steps without duplicating
  their evidence or citation rules.
- **FR-022**: System MUST preserve completed VN stock brief sections when a
  downstream step is partial, failed, or unavailable and identify the affected
  stage to the analyst.
- **FR-023**: Workflow forms MUST render and validate every required VN stock or
  gold input, reject missing or invalid values near the relevant field, and
  avoid creating a fabricated result.
- **FR-024**: The workflow catalog and validation boundary MUST allow only VN
  stocks and supported gold instruments or benchmarks as enabled runnable inputs.
- **FR-025**: System MUST persist and expose workflow-history list, detail, and
  citation-inspection behavior for completed and partial Phase 03 runs.

### Phase 02 Migration Traceability

The following unfinished Phase 02 scope now belongs to this feature. Requirement
identifiers remain in `../002-workflow/spec.md` as migration history; this spec
is the authoritative implementation target.

| Phase 02 item | Phase 03 owner |
|---|---|
| US3, FR-005, FR-006, FR-010, SC-004: composite `stock-brief` | FR-021, FR-022 and User Story 3 |
| US4, FR-012, FR-013: field-level input validation and unsupported-state behavior | FR-023, FR-024 and User Story 4 |
| US5, FR-023, FR-024, SC-008: history, run detail, and citation reinspection | FR-025 and User Story 5 |
| Unfinished Phase 02 delivery, risk, safety, environment, and quickstart tasks | Phase 03 cross-cutting tasks |

### Key Entities

- **Workflow Catalog Entry**: A user-facing fixed workflow option with market scope, required inputs, expected sections, citation expectations, chart expectations, and unsupported categories.
- **Gold Dataflow**: The bounded collection and normalization path for supported gold evidence, including source provenance, timestamps, freshness status, warnings, and citation-ready context.
- **VN Stock Dataflow**: The bounded collection and normalization path for supported VN stock evidence reused by new VN stock workflows.
- **VN Stock Workflow Run**: A completed, partial, failed, or unavailable execution for a supported VN stock symbol.
- **Gold Workflow Run**: A completed, partial, failed, or unavailable execution for a supported gold instrument or benchmark.
- **Evidence Record**: A canonical data record used to support workflow claims, including source identity, dataset identity, timestamps, and rendered context.
- **Citation Snapshot**: A persisted cited evidence reference used for inline claims and later reinspection.
- **Artifact**: A generated chart, file, or visual output linked to cited evidence and workflow status.
- **Unsupported Claim Category**: A workflow section or claim type that cannot be safely produced for the selected market or available evidence.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Analysts can collect supported gold evidence and inspect source provenance, freshness, and unavailable states without reading logs.
- **SC-002**: Analysts can complete a supported gold workflow and inspect cited output, artifacts, and execution status in under 5 minutes.
- **SC-003**: Analysts can complete each new supported VN stock workflow and inspect cited output, artifacts, and execution status in under 5 minutes.
- **SC-004**: 100% of material VN stock and gold workflow claims include citations or explicit unsupported/unavailable markings.
- **SC-005**: 100% of unsupported Phase 03 markets and assets are blocked or visibly marked before user reliance.
- **SC-006**: 100% of workflow outputs avoid autonomous buy, sell, order, or broker-action language.
- **SC-007**: At least 95% of completed workflow result views expose citation provenance and source freshness without requiring logs.
- **SC-008**: Users can identify whether a workflow section is completed, partial, failed, unavailable, or out of scope for 100% of Phase 03 workflow runs.
- **SC-009**: Primary workflow submissions show visible progress within 1 second in local validation scenarios.
- **SC-010**: Reopened workflow runs preserve final output, citations, artifacts, and limitation states for 100% of completed or partial runs.
- **SC-011**: A VN stock brief exposes collection, grounding, fundamental, and
  technical stage outcomes for 100% of completed, partial, or failed runs.
- **SC-012**: 100% of invalid or unsupported Phase 03 workflow submissions show
  a field-level or request-level limitation before a result is created.

## Assumptions

- Phase 02 remains the foundation for fixed workflow execution, evidence records, citations, artifacts, streaming progress, and run history.
- The active dataflow and workflow scope is VN stocks and gold before production
  chatflow work begins.
- Additional markets are unsupported unless a later spec explicitly introduces them.
- Gold support means a bounded gold instrument or benchmark workflow, not broad commodity coverage.
- Chatflow is deferred to `../004-agentic-chatflow/`.
- The MVP shell and deterministic mock chat UI remain owned by `../001-mvp-ui/`.
- Workflows provide advice support and evidence framing, not trading decisions or autonomous financial actions.
