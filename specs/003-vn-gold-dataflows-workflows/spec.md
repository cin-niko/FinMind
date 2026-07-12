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

**Input**: User description: "Build XAUUSD Gold dataflows from Twelve Data OHLC evidence; provide ready-to-use VN stock technical analysis, fundamental analysis, news digest, and valuation workflows; provide Gold technical analysis; and make web and workflow output follow a persisted Vietnamese or English user preference."

## User Scenarios & Testing

### User Story 1 - Build Gold Evidence Dataflows (Priority: P1)

An authenticated analyst can rely on Gold analysis because the system collects,
normalizes, freshness-checks, and cites XAUUSD OHLC evidence before making a
Gold market claim.

**Why this priority**: Gold cannot become a safe runnable market until its
evidence path, limitations, and provenance are explicit and auditable.

**Independent Test**: Run an XAUUSD evidence collection and verify that every
returned record has source identity, dataset identity, UTC timestamps, freshness
state, and citation-ready context; verify that missing evidence is visibly
unavailable.

**Acceptance Scenarios**:

1. **Given** available XAUUSD OHLC evidence, **When** Gold data is collected,
   **Then** the result exposes provenance, UTC timestamps, freshness, and
   citation-ready context.
2. **Given** gold evidence is stale, delayed, missing, or unavailable, **When**
   collection completes, **Then** the result marks the affected data unavailable
   or partial before a claim can rely on it.
3. **Given** a Gold workflow requests an unsupported dataset or instrument,
   **When** validation runs, **Then** it is blocked or clearly marked
   unsupported before answer generation.

---

### User Story 2 - Mature And Extend VN Stock Workflows (Priority: P1)

An authenticated analyst can use refined existing VN technical and fundamental
workflows, plus new news-digest, valuation, and combined stock-brief workflows,
to receive bounded, cited research output for a supported symbol.

**Why this priority**: Existing workflow runtime is only the foundation. Analysts
need reliable workflow content, evidence rules, unavailable states, and useful
research value without relying on a future open-ended chatflow.

**Independent Test**: Run each refined or new VN workflow for a supported symbol
and verify that its promised sections contain cited evidence or an explicit
unavailable state, its market-specific inputs are validated, and no output
instructs a trade or order.

**Acceptance Scenarios**:

1. **Given** a supported VN stock symbol and sufficient price evidence,
   **When** the analyst runs technical analysis, **Then** the result shows cited
   technical observations and an evidence-backed chart where available.
2. **Given** a supported VN stock symbol and sufficient financial evidence,
   **When** the analyst runs fundamental analysis or valuation, **Then** the
   result distinguishes reported facts, derived measures, and unavailable
   inputs with citations for every material claim.
3. **Given** a supported VN stock symbol and eligible news evidence, **When**
   the analyst runs the news digest, **Then** the result presents cited,
   time-stamped developments without treating unavailable or uncited news as
   fact.
4. **Given** one or more datasets required by a VN workflow are missing,
   stale, or insufficient, **When** the workflow completes, **Then** only the
   affected sections are unavailable or partial and successful sections remain
   inspectable.

---

### User Story 3 - Run Gold Technical Analysis (Priority: P1)

An authenticated analyst can run a fixed technical analysis workflow for
XAUUSD and inspect cited trend, momentum, volatility, and risk context without
receiving stock-only financial analysis or trading signals.

**Why this priority**: Gold needs a focused, safe first workflow that matches
the evidence available for that market.

**Independent Test**: Run XAUUSD technical analysis and verify that its output,
chart, freshness, citations, and unavailable states are specific to Gold market
evidence and contain no trading signal or verdict.

**Acceptance Scenarios**:

1. **Given** sufficient XAUUSD OHLC evidence, **When** the analyst runs Gold
   technical analysis, **Then** the result presents cited, analysis-only
   technical context and a chart artifact where supported.
2. **Given** insufficient Gold price history or stale evidence, **When** the
   workflow completes, **Then** affected technical claims and charts are marked
   unavailable rather than estimated.
3. **Given** a Gold workflow is selected, **When** output is rendered, **Then**
   stock-only sections such as company fundamentals and equity valuation do not
   appear as supported gold output.

---

### User Story 4 - Receive Language-Appropriate Output (Priority: P1)

An authenticated analyst can set a persisted Vietnamese or English web-language
preference and receive web copy and workflow-generated narratives in that
language.

**Why this priority**: Analysts need predictable language for repeatable
workflow reports across browser sessions and devices.

**Independent Test**: Set each supported web language, start a new browser
session, run a workflow, and verify that web copy and the generated narrative
follow the persisted setting while evidence fields remain unchanged.

**Acceptance Scenarios**:

1. **Given** the analyst selects a supported web language, **When** a workflow
   run produces user-facing narrative, **Then** its generated title, section
   text, limitation messages, and research framing use the selected language.
2. **Given** the analyst changes the web language setting, **When** a later
   workflow runs, **Then** the later output uses the new setting without
   changing the evidence, citations, timestamps, identifiers, or saved output
   from earlier runs.
3. **Given** the analyst starts a new browser session, **When** the web app
   loads, **Then** it restores the persisted language preference for that
   authenticated user.
4. **Given** an authenticated analyst has no saved preference, **When** the web
   app first loads, **Then** it persists a detected Vietnamese or English
   browser language, or English when no supported browser language is detected.

---

### User Story 5 - Compare, Validate, And Reinspect Workflows (Priority: P2)

An authenticated analyst can distinguish VN stock and gold workflows, provide
only the required inputs for each, and later reopen completed or partial runs
with their evidence, artifacts, limitations, and language-preserved output.

**Why this priority**: Market boundaries and auditable run history prevent
misuse of research outputs and support repeated analyst review.

**Independent Test**: Open the catalog, submit valid and invalid inputs for
each workflow, and reopen completed and partial runs to verify scope, evidence,
status, artifacts, and saved output remain clear.

**Acceptance Scenarios**:

1. **Given** the analyst opens the workflow catalog, **When** VN stock and gold
   workflows are listed, **Then** each clearly states its market scope,
   required inputs, expected evidence, and unavailable categories.
2. **Given** the analyst submits an unsupported market, instrument, or missing
   required input, **When** validation runs, **Then** the request is blocked
   near the relevant field or request boundary without creating a fabricated
   result.
3. **Given** a workflow completed or was partial, **When** the analyst reopens
   it, **Then** its saved output, citations, artifacts, source freshness, and
   limitation states remain inspectable in the language used for that run.

### Edge Cases

- Gold data is delayed, stale, unavailable, or from a benchmark that does not
  match the selected user-facing instrument.
- A VN stock has incomplete price history, financial statements, company
  profile, valuation inputs, or eligible news evidence.
- News is available but cannot be cited, has an unclear timestamp, is stale, or
  conflicts with another eligible source.
- A valuation workflow has insufficient or inconsistent inputs for a derived
  value.
- A user changes the web language setting while a workflow is running.
- A workflow category is meaningful for VN stocks but not for gold, or the
  inverse.
- The analyst asks for a trade, order, broker action, or other irreversible
  financial action.
- Citation snapshots exist but the underlying source is unavailable at
  reinspection time.
- A chart cannot be generated safely from the available evidence.
- Concurrent workflow runs must show progress rather than a blank state.

## Requirements

### Functional Requirements

- **FR-001**: The Phase 03 runnable workflow scope MUST be VN stocks and gold
  only; production chatflow remains owned by Phase 04.
- **FR-002**: The system MUST provide a gold dataflow that collects,
  normalizes, freshness-checks, and citation-prepares supported gold evidence.
- **FR-003**: Gold evidence records MUST remain distinct from VN stock records
  while using the shared citation and artifact inspection model.
- **FR-004**: The system MUST provide a fixed XAUUSD Gold technical analysis
  workflow using OHLC evidence from the configured Gold source.
- **FR-005**: The system MUST mature the existing VN stock technical-analysis
  and fundamental-analysis workflows by finalizing their skill content, evidence
  requirements, output sections, unavailable states, language behavior, and
  safety boundaries.
- **FR-006**: The system MUST add fixed VN stock news-digest and valuation
  workflows with bounded evidence and analyst-facing research value.
- **FR-007**: The system MUST add the Phase 02 VN stock brief as a
  composite workflow that reuses the same evidence and citation rules as its
  component analyses.
- **FR-008**: Technical analysis workflows MUST show only evidence-backed
  analysis of trend, momentum, volatility, and risk context; they MUST NOT show
  trading signals, verdicts, entry or exit instructions, or target prices, and
  MUST mark unsupported or insufficient technical claims and charts unavailable.
- **FR-009**: Fundamental analysis and valuation workflows MUST distinguish
  cited reported facts from derived measures and mark incomplete, inconsistent,
  or unavailable inputs before user reliance. Valuation MUST use only
  sector-appropriate methods with a visible range and sensitivity context, not
  a single target price or investment recommendation.
- **FR-010**: The news digest MUST use only eligible, time-stamped, cited news
  evidence from its declared web-search domain allowlist and source priority; it
  MUST explicitly mark unavailable, stale, or uncited developments and MUST NOT
  produce an investment signal or recommendation. News deduplication is deferred
  beyond Phase 03.
- **FR-011**: Gold workflows MUST NOT present stock-only financial statements,
  company fundamentals, or equity valuation as supported gold evidence.
- **FR-012**: VN stock workflows MUST NOT mix gold-specific market context
  unless the workflow explicitly declares it and cites eligible evidence.
- **FR-013**: Every material user-facing workflow claim MUST include source
  identity, dataset identity, and timestamp through a citation, or be explicitly
  marked unsupported or unavailable.
- **FR-014**: The system MUST show source freshness and unavailable-source
  limitations before users can rely on VN stock or gold workflow output.
- **FR-015**: The system MUST generate chart artifacts only from available
  cited evidence and mark charts unavailable when evidence is insufficient.
- **FR-016**: Workflow forms MUST render and validate every required VN stock
  or gold input and block unsupported markets, instruments, and missing or
  invalid values without creating a fabricated result.
- **FR-017**: The workflow catalog MUST state each workflow's market scope,
  required inputs, supported sections, and unsupported categories.
- **FR-018**: The web application MUST offer Vietnamese and English as
  server-persisted, authenticated-user language preferences. On first
  authenticated use, it MUST persist a supported browser language or English as
  the default, and a later explicit choice MUST replace that default.
- **FR-019**: The web language preference MUST control web-visible copy and each
  workflow run MUST capture its preference at submission for generated
  user-facing narrative, including titles, sections, limitations, and research
  framing.
- **FR-020**: Language selection MUST NOT translate, alter, or obscure source
  identifiers, citations, timestamps, numeric values, market symbols, or saved
  evidence snapshots.
- **FR-021**: The system MUST preserve completed, partial, failed, and
  unavailable workflow statuses for reinspection.
- **FR-022**: Reopened runs MUST preserve their generated output language,
  citations, artifacts, and limitation states.
- **FR-023**: Workflow outputs MUST NOT expose raw agent reasoning, hidden
  prompts, provider secrets, credentials, raw provider payloads, or unsafe
  diagnostics.
- **FR-024**: Workflow outputs MUST remain research support and MUST NOT
  instruct autonomous trades, orders, or irreversible financial actions.
- **FR-025**: Primary workflow submissions MUST show visible progress before
  final output is ready.

### Phase 02 Migration Traceability

The following unfinished Phase 02 scope belongs to this feature. Requirement
identifiers remain in `../002-workflow/spec.md` as migration history; this spec
is the authoritative implementation target.

| Phase 02 item | Phase 03 owner |
|---|---|
| Composite `stock-brief` workflow | FR-007 and User Story 2 |
| Field-level input validation and unsupported-state behavior | FR-016 and User Story 5 |
| Workflow history, detail, and citation reinspection | FR-021 and FR-022 and User Story 5 |
| Unfinished delivery, risk, safety, environment, and quickstart tasks | Phase 03 cross-cutting work |

### Key Entities

- **Workflow Catalog Entry**: A fixed user-facing workflow with market scope,
  required inputs, expected sections, citation expectations, chart expectations,
  output-language behavior, and unsupported categories.
- **Gold Dataflow**: The bounded collection and normalization path for supported
  gold evidence, including provenance, timestamps, freshness status, warnings,
  and citation-ready context.
- **VN Stock Dataflow**: The bounded collection and normalization path for
  supported VN stock evidence reused by the fixed VN workflows.
- **Workflow Language Preference**: The authenticated analyst's server-persisted
  Vietnamese or English preference used for web copy and workflow narratives.
- **Workflow Run**: A completed, partial, failed, or unavailable execution for
  a supported VN stock symbol or XAUUSD Gold benchmark.
- **Evidence Record**: A canonical evidence item supporting workflow claims,
  with source identity, dataset identity, timestamps, and rendered context.
- **Citation Snapshot**: A persisted cited evidence reference used for claims
  and later reinspection.
- **Artifact**: A generated chart, file, or visual output linked to cited
  evidence and workflow status.
- **Unsupported Claim Category**: A section or claim type that cannot be safely
  produced for the selected market or available evidence.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Analysts can collect supported gold evidence and inspect its
  provenance, freshness, and unavailable states without reading logs.
- **SC-002**: Analysts can complete gold technical analysis and each fixed VN
  analysis workflow, then inspect cited output, artifacts, and execution status
  in under 5 minutes.
- **SC-003**: 100% of material VN stock and gold workflow claims in acceptance
  tests include citations or explicit unsupported or unavailable markings.
- **SC-004**: 100% of unsupported Phase 03 markets, assets, inputs, and claim
  categories are blocked or visibly marked before user reliance.
- **SC-005**: 100% of workflow result language acceptance tests render
  generated narrative in the web language setting captured at submission.
- **SC-006**: At least 95% of completed workflow result views expose citation
  provenance and source freshness without requiring logs.
- **SC-007**: Users can identify completed, partial, failed, unavailable, and
  out-of-scope sections for 100% of Phase 03 workflow runs.
- **SC-008**: Primary workflow submissions show visible progress within 1
  second in local validation scenarios.
- **SC-009**: Reopened completed or partial workflow runs preserve their final
  output, captured output language, citations, artifacts, and limitation states.
- **SC-010**: 100% of workflow outputs avoid autonomous buy, sell, order, or
  broker-action language.

## Assumptions

- Phase 02 remains the foundation for fixed workflow execution, evidence
  records, citations, artifacts, streaming progress, and run history.
- The active dataflow and workflow scope is VN stocks and gold before production
  chatflow work begins.
- "New digest" in the feature request means a news digest.
- Vietnamese and English are the initial supported web output languages.
- On first authenticated use, a supported browser language is automatically
  saved as the user's preference; English is saved when detection is unsupported
  or unavailable.
- The selected workflow language is captured when the analyst submits a run;
  changing the setting does not rewrite prior output.
- XAUUSD is the sole supported Gold benchmark, quoted in USD per troy ounce.
  Twelve Data provides its OHLC evidence and all normalized Gold timestamps use
  UTC.
- The Phase 03 plan validates Twelve Data source rights and limits, news
  publisher API/feed eligibility and rights, freshness targets, and valuation
  methodology.
- Additional markets are unsupported unless a later spec explicitly introduces
  them.
- Workflows provide research support and evidence framing, not trading decisions
  or autonomous financial actions.
