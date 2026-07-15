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

An authenticated analyst can rely on Gold analysis because the system collects
and normalizes a daily XAUUSD OHLC series, preserves its timestamp provenance,
and cites it before making a Gold market claim.

**Why this priority**: Gold cannot become a safe runnable market until its
evidence path, limitations, and provenance are explicit and auditable.

**Independent Test**: Run an XAUUSD evidence collection and verify that every
returned record has source identity, dataset identity, UTC market and collection
timestamps, and citation-ready context; verify that missing or invalid evidence
is visibly unavailable.

**Acceptance Scenarios**:

1. **Given** available daily XAUUSD OHLC evidence, **When** Gold data is
   collected, **Then** the result exposes provenance, UTC market and collection
   timestamps, and citation-ready context.
2. **Given** Gold evidence has an earlier market timestamp than its collection
   timestamp, **When** collection completes, **Then** the result preserves both
   timestamps and does not represent collection time as the evidence time.
3. **Given** gold evidence is missing, invalid, or unavailable, **When**
   collection completes, **Then** the result marks the affected data unavailable
   before a claim can rely on it.
4. **Given** a Gold workflow requests an unsupported dataset or instrument,
   **When** validation runs, **Then** it is blocked or clearly marked
   unsupported before answer generation.
5. **Given** a transient Gold-provider failure, **When** the initial collection
   call and its two retries fail, **Then** the workflow fails safely without
   using a cached response or fallback source, and without exposing the provider
   error.

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
   time-stamped developments with each source's URL, title, and content without
   treating unavailable or uncited news as fact.
4. **Given** one or more datasets required by a VN workflow are missing or
   insufficient, **When** the workflow completes, **Then** only the
   affected sections are unavailable and successful sections remain inspectable.
5. **Given** a collected or derived field such as P/E is unavailable, **When**
   its deterministic evidence context is rendered before analysis, **Then** the
   normalized field is `None`, the context renders it as `Unavailable`, the
   generated answer preserves the limitation, and the conversation remains successful
   when every planned stage completes safely.
6. **Given** a supported VN stock has sector-appropriate, period-consistent
   valuation inputs, **When** the analyst runs valuation, **Then** the result
   presents eligible method results, a cited research range, and sensitivity
   context without a target price, investment label, or recommendation.
7. **Given** a valuation method requires unavailable, inconsistent, or
   inapplicable inputs, **When** the analyst runs valuation, **Then** that method
   is marked unavailable and no value is estimated for it.

---

### User Story 3 - Run Gold Technical Analysis (Priority: P1)

An authenticated analyst can run a fixed daily technical analysis workflow for
XAUUSD and inspect cited trend, momentum, volatility, and risk context without
receiving stock-only financial analysis or trading signals.

**Why this priority**: Gold needs a focused, safe first workflow that matches
the evidence available for that market.

**Independent Test**: Run XAUUSD technical analysis and verify that its output,
chart, source timestamps, citations, and unavailable states are specific to Gold
market evidence and contain no trading signal or verdict.

**Acceptance Scenarios**:

1. **Given** the analyst selects the Gold technical-analysis card, **When** the
   analyst runs it, **Then** it uses the fixed XAUUSD benchmark without a market,
   symbol, or instrument input control.
2. **Given** sufficient daily XAUUSD OHLC evidence, **When** the analyst runs
   Gold technical analysis, **Then** the result presents cited, analysis-only
   technical context and a daily chart artifact where supported.
3. **Given** insufficient, missing, or invalid Gold price history, **When** the
   workflow completes, **Then** affected technical claims and charts are marked
   unavailable rather than estimated.
4. **Given** a Gold workflow is selected, **When** output is rendered, **Then**
   stock-only sections such as company fundamentals and equity valuation do not
   appear as supported gold output.

---

### User Story 4 - Receive Language-Appropriate Output (Priority: P1)

An authenticated analyst can choose Auto-detect, Vietnamese, or English and
receive web copy and workflow-generated narratives in the effective selected
language.

**Why this priority**: Analysts need predictable language for repeatable
workflow reports across browser sessions and devices.

**Independent Test**: Set Auto-detect, Vietnamese, and English in turn; start a
new browser session; run a workflow; and verify web copy and generated narrative
follow the resolved language captured at submission while evidence fields remain
unchanged.

**Acceptance Scenarios**:

1. **Given** the analyst selects Vietnamese or English, **When** the web app
   renders and a workflow runs, **Then** web copy and the generated title,
   section text, limitation messages, and research framing use that language.
2. **Given** the analyst selects Auto-detect, **When** the web app loads,
   **Then** it uses the first supported Vietnamese or English language in the
   browser's ordered language list, or English when none is supported.
3. **Given** the analyst submits a workflow, **When** its conversation is created,
   **Then** the UI sends its resolved `vi` or `en` value, the backend captures
   it with the conversation, and the LLM receives it as a language instruction
   for the generated narrative.
4. **Given** the analyst changes the language selection, **When** a later
   workflow runs, **Then** the later output uses the new resolved language
   without changing evidence, citations, timestamps, identifiers, or saved
   output from earlier conversations.
5. **Given** an analyst starts a new browser session, **When** the web app
   loads, **Then** it restores the authenticated user's saved selection; an
   Auto-detect selection resolves against that browser's language list.

---

### User Story 5 - Inspect And Delete A Workflow Conversation (Priority: P1)

An authenticated analyst can reopen the conversation created by a workflow,
inspect its first result message, citations, and artifacts, and delete the
conversation when it is no longer wanted.

**Why this priority**: The conversation is the user-owned record of a workflow
result; it provides reinspection and the sole user-controlled retention boundary.

**Independent Test**: Start a workflow, reopen its created conversation from
History, inspect the first assistant message and evidence, then delete it and
verify its messages and their children are inaccessible while shared market data
remains available.

**Acceptance Scenarios**:

1. **Given** an analyst starts a valid workflow, **When** it is accepted,
   **Then** the system creates a new owned conversation before execution. The
   workflow produces a result, and the conversation adapter persists that result
   as its first assistant message or product-facing failure summary.
2. **Given** an analyst reopens one of their conversations, **When** it loads,
   **Then** it shows its status, output or failure summary, citations, artifacts,
   language, and unavailable limitations without raw reasoning.
3. **Given** an analyst deletes one of their conversations, **When** deletion
   completes after the conversation is terminal, **Then** its messages and the
   citations, artifacts, and execution metadata owned through those messages are
   deleted while shared canonical market data is retained.
4. **Given** a user requests another user's conversation, **When** multi-user
   support exists, **Then** the request is rejected; citations and artifacts are
   not reachable outside their owning authorized conversation.

---

### Edge Cases

- Gold data has an earlier market timestamp than the time it is collected, is
  unavailable, or comes from a benchmark that does not match the selected
  user-facing instrument.
- A transient configured provider failure remains unavailable after its two
  retries.
- A VN stock has incomplete price history, financial statements, company
  profile, valuation inputs, or eligible news evidence.
- News is available but cannot be cited, has an unclear publication timestamp, or
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
- A workflow exceeds its 120-second timeout, the browser disconnects while it
  runs, or the service restarts while it is queued or running.

## Requirements

### Functional Requirements

- **FR-001**: The Phase 03 runnable workflow scope MUST be VN stocks and gold
  only; production chatflow remains owned by Phase 04.
- **FR-002**: The system MUST provide a gold dataflow that fetches, normalizes,
  and upserts one daily XAUUSD OHLC price series per workflow-created
  conversation. It MUST
  preserve UTC market and collection timestamps and citation-prepare the
  supported gold evidence.
- **FR-003**: Gold evidence records MUST remain distinct from VN stock records
  while using the shared citation and artifact inspection model.
- **FR-004**: The system MUST provide a fixed XAUUSD Gold technical analysis
  workflow using daily OHLC evidence from the configured Gold source. It MUST
  NOT offer selectable intervals or multi-timeframe analysis in Phase 03.
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
  or unavailable inputs before user reliance. Valuation MUST select only
  sector-appropriate eligible methods, show the results as a cited research
  range with sensitivity context where a method is assumption-driven, and MUST
  NOT present a single target price, investment label, or recommendation.
- **FR-010**: The news digest MUST use only eligible, publication-time-stamped,
  cited news evidence returned by the configured web-search provider from its
  application-configured publisher-domain allowlist. Each source MUST provide a
  URL, title, publication time, and provider-delivered content. The workflow
  MUST explicitly mark unavailable or uncited developments and MUST NOT produce
  an investment signal or recommendation. It does not perform deterministic
  deduplication; the LLM may group similar cited articles in its narrative.
- **FR-011**: Gold workflows MUST NOT present stock-only financial statements,
  company fundamentals, or equity valuation as supported gold evidence.
- **FR-012**: VN stock workflows MUST NOT mix gold-specific market context
  unless the workflow explicitly declares it and cites eligible evidence.
- **FR-013**: Every material user-facing workflow claim MUST include source
  identity, dataset identity, and timestamp through a citation, or be explicitly
  marked unsupported or unavailable. Phase 03 MUST reuse the shared Phase 02
  citation allowlist, grounding, and persisted citation-snapshot contract rather
  than define a market-specific citation model.
- **FR-014**: The system MUST show each cited source's market or publication
  timestamp, retain its collection timestamp in evidence provenance for audit
  and reinspection, and show unavailable-source limitations before users can
  rely on VN stock or gold workflow output. Phase 03 MUST NOT calculate or
  label a separate fresh/stale state.
- **FR-015**: The system MUST generate chart artifacts only from available
  cited evidence and mark charts unavailable when evidence is insufficient.
- **FR-016**: VN stock workflow forms MUST render and validate every required
  input and block missing or invalid values without creating a fabricated
  result. Gold technical analysis MUST have no user-editable market, symbol, or
  instrument input and MUST run only for XAUUSD.
- **FR-017**: The workflow catalog MUST state each workflow's market scope,
  required inputs, supported sections, and unsupported categories. The Gold
  technical-analysis card MUST open the same confirmation dialog as other
  workflows, then run its fixed XAUUSD scope without editable inputs.
- **FR-018**: The web application MUST offer exactly Auto-detect, Vietnamese,
  and English as server-persisted, authenticated-user language selections. The
  initial selection MUST be Auto-detect. Auto-detect MUST resolve the first
  supported entry in the browser's ordered language list after normalizing
  `vi-*` to `vi` and `en-*` to `en`, or resolve to English when none is
  supported. The selection MUST be available from an authenticated Settings
  surface without adding a primary navigation item, and it MUST save immediately.
- **FR-019**: The resolved web language MUST control all FinMind-owned
  web-visible copy, including navigation, controls, validation and failure
  messages, workflow catalog text, deterministic workflow progress step and
  status labels, artifact chrome, and generated narrative. Presentation code
  MUST resolve stable keys or codes through a typed locale catalog rather than
  treating English display strings as API or workflow contracts. At each
  workflow submission, the UI MUST send the resolved `vi` or `en` value; the
  backend MUST reject another value, capture the accepted value with the
  conversation,
  and use it as the model-facing language instruction for generated
  user-facing narrative, including titles, sections, limitations, and research
  framing. A narrative that cannot honor that captured language MUST fail safely
  rather than silently falling back to another language.
- **FR-020**: Language selection MUST NOT translate, alter, or obscure canonical
  records or citation evidence. Record field names and content, citation titles,
  excerpts/content, publisher names, URLs, source identifiers, timestamps,
  numeric values, market symbols, and saved evidence snapshots remain in
  English or their canonical source representation. FinMind-owned controls
  surrounding those records and citations MAY be localized. Unsupported or
  missing presentation keys MUST fall back to English without changing the
  canonical evidence payload.
- **FR-021**: Starting an accepted workflow MUST always create a new
  authenticated-user-owned conversation before execution. The workflow MUST
  produce a `WorkflowResult`; a conversation adapter MUST map that result to the
  conversation's first assistant message, with successful or failed status and
  any unavailable field, claim, chart, or section limitations. Citations and
  artifacts MUST belong to that assistant message. Phase 03 MUST NOT use a
  separate workflow-run entity or a `partial` status.
- **FR-022**: Reopened conversations MUST preserve their generated output
  language, citations, artifacts, and limitation states. The owner can delete a
  conversation; deletion MUST cascade to its messages, citation snapshots,
  artifacts, and execution metadata, without deleting shared canonical market
  data.
- **FR-023**: Workflow outputs MUST NOT expose raw agent reasoning, hidden
  prompts, provider secrets, credentials, raw provider payloads, or unsafe
  diagnostics.
- **FR-024**: Workflow outputs MUST remain research support and MUST NOT
  instruct autonomous trades, orders, or irreversible financial actions.
- **FR-025**: Primary workflow submissions MUST show visible progress before
  final output is ready.
- **FR-026**: Before any workflow evidence is supplied to the LLM, deterministic
  data-record rendering MUST represent each missing, invalid, or source-
  unavailable field as `None` and render it as `Unavailable`. The generated
  answer MUST preserve those field-level limitations without fabricating a value;
  valid zero and false values MUST remain values, and field-level unavailability
  alone MUST NOT downgrade a successfully completed workflow-created
  conversation.
- **FR-027**: For a transient configured-provider collection failure, the system
  MUST make at most two retries after the initial attempt. If collection still
  fails, it MUST fail the workflow safely without substituting cached evidence
  or a fallback source, and without exposing raw provider diagnostics. It MUST
  NOT retry invalid input, unavailable required evidence, unsupported scope, or
  an output that fails a required safety or language check.
- **FR-028**: The valuation workflow MUST use the Phase 03 VN valuation
  methodology: P/B plus ROE for banks; P/B plus EV/EBITDA for cyclical steel;
  P/B plus NAV for real estate; P/E plus PEG for retail, consumer, and
  technology; and EV/EBITDA plus P/CF for oil and gas. It MAY add DCF only when
  its cash-flow inputs are available, DDM only for regular cash-dividend payers,
  and Graham only when EPS and BVPS are positive. Other methods are unavailable
  unless their required inputs are cited and period-consistent.
- **FR-029**: The valuation workflow MUST use only currency-, unit-,
  reporting-period-, and share-count-consistent inputs. It MUST mark a method
  unavailable when a restatement, corporate-action effect, negative earnings, or
  other input condition prevents a reliable calculation; it MUST NOT apply a
  manual adjustment or substitute an estimate.
- **FR-030**: The valuation workflow MUST present the median and P25–P75 range
  of eligible method results. DCF output MUST show downside, base, and upside
  cases plus sensitivity to discount-rate and terminal-growth assumptions. These
  are research ranges and assumptions, not price targets or recommendations.
- **FR-031**: Each Phase 03 workflow-created conversation MUST finish within
  120 seconds of acceptance. On timeout, it MUST stop safely, persist `failed`
  with a product-facing timeout summary, and remain inspectable.
- **FR-032**: A browser disconnect or closed tab MUST NOT cancel an accepted
  workflow-created conversation. The conversation continues and its terminal
  result is persisted for reinspection. Phase 03 provides no user cancellation,
  idempotency, queue, or concurrency-limit guarantee; separately submitted
  workflows create independent conversations.
- **FR-033**: On service startup, the system MUST mark persisted `queued` or
  `running` conversations interrupted by the prior service instance as `failed`,
  with a completed timestamp and product-facing interruption summary. It MUST
  NOT resume an interrupted workflow or combine its earlier evidence with a new
  attempt.
- **FR-034**: Phase 03 automated tests MUST use deterministic fixtures or mocks
  for market-data, news-search, and model-provider behavior. They MUST NOT
  depend on live market data, live provider availability, or changing provider
  responses. Live-provider contract validation is a separately recorded
  operational check, not an automated-suite dependency.

### Phase 02 Migration Traceability

The following unfinished Phase 02 scope belongs to this feature. Requirement
identifiers remain in `../002-workflow/spec.md` as migration history; this spec
is the authoritative implementation target.

| Phase 02 item | Phase 03 owner |
|---|---|
| Composite `stock-brief` workflow | FR-007 and User Story 2 |
| Field-level input validation and unsupported-state behavior | FR-016 |
| Workflow history, detail, and citation reinspection | FR-021 and FR-022, now as conversation history |
| Unfinished delivery, risk, safety, environment, and quickstart tasks | Phase 03 cross-cutting work |

### Key Entities

- **Workflow Catalog Entry**: A fixed user-facing workflow with market scope,
  required inputs, expected sections, citation expectations, chart expectations,
  output-language behavior, and unsupported categories.
- **Gold Dataflow**: The bounded collection and normalization path for supported
  daily XAUUSD price-series evidence, including provenance, UTC market and
  collection timestamps, warnings, and citation-ready context.
- **VN Stock Dataflow**: The bounded collection and normalization path for
  supported VN stock evidence reused by the fixed VN workflows.
- **Workflow Language Preference**: The authenticated analyst's server-persisted
  Auto-detect, Vietnamese, or English selection. Auto-detect resolves to `vi`
  or `en` from the browser; the resolved value is captured for each workflow
  narrative.
- **Workflow Conversation**: An authenticated-user-owned conversation newly
  created for a supported VN stock or XAUUSD Gold workflow. Its workflow result
  is mapped by a conversation adapter to its first assistant message. It may be
  queued or running before successful or failed terminal status. Unavailable
  applies to an evidence field, claim, chart, or section, not the conversation
  itself.
- **Evidence Record**: A canonical evidence item supporting workflow claims,
  with source identity, dataset identity, timestamps, and rendered context.
- **Citation Snapshot**: A persisted cited evidence reference owned by an
  assistant message and used for claims and later inspection.
- **Artifact**: A generated chart, file, or visual output owned by an assistant
  message and linked to cited evidence and workflow status.
- **Unsupported Claim Category**: A section or claim type that cannot be safely
  produced for the selected market or available evidence.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of accepted Gold evidence records in acceptance tests expose
  source identity, dataset identity, UTC market and collection timestamps, and
  either citation-ready context or an explicit unavailable state without reading
  logs.
- **SC-002**: Analysts can complete gold technical analysis and each fixed VN
  analysis workflow, then inspect cited output, artifacts, and execution status
  in under 5 minutes.
- **SC-003**: 100% of material VN stock and gold workflow claims in acceptance
  tests include citations or explicit unsupported or unavailable markings.
- **SC-004**: 100% of unsupported Phase 03 markets, assets, inputs, and claim
  categories are blocked or visibly marked before user reliance.
- **SC-005**: 100% of workflow result language acceptance tests render
  generated narrative in the resolved `vi` or `en` language captured at
  submission, for Auto-detect and both explicit selections.
- **SC-006**: At least 95% of completed workflow result views expose citation
  provenance and the evidence market or publication timestamp without requiring
  logs.
- **SC-007**: Users can identify successful and failed workflow-created
  conversations, plus unavailable and out-of-scope fields or sections, for 100%
  of Phase 03 workflow submissions.
- **SC-008**: Primary workflow submissions show visible progress within 1
  second in local validation scenarios.
- **SC-009**: Reopened successful or failed workflow-created conversations
  preserve the adapter-created first assistant message or product-facing failure
  summary, captured output language where available, that message's citations,
  artifacts, and limitation states.
- **SC-011**: 100% of workflow timeout and service-restart acceptance fixtures
  finish as inspectable failed conversations within the prescribed lifecycle
  handling, with no conversation left indefinitely queued or running.
- **SC-012**: 100% of conversation-deletion acceptance fixtures remove the
  selected conversation's messages and their citation snapshots, artifacts, and
  execution metadata while retaining shared canonical market data.
- **SC-010**: 100% of workflow outputs avoid autonomous buy, sell, order, or
  broker-action language.

## Assumptions

- Phase 02 remains the foundation for fixed workflow execution, evidence
  records, citations, artifacts, and streaming progress. Phase 03 replaces
  workflow run history with workflow-created conversation history.
- The active dataflow and workflow scope is VN stocks and gold before production
  chatflow work begins.
- "New digest" in the feature request means a news digest.
- Vietnamese and English are the only supported effective web output languages.
- Auto-detect is the default persisted language selection. It resolves the
  browser's first supported language for the current session, or English when
  unavailable; explicit Vietnamese or English overrides it.
- The resolved `vi` or `en` language is captured when the analyst submits a
  workflow-created conversation; changing the selection does not rewrite prior
  output.
- Phase 03 retains a conversation until its owner deletes it; there is no
  automatic time-based purge. All conversation queries are filtered to the
  authenticated owner, which is the required ownership boundary before
  multi-user support.
- Phase 03 automated acceptance tests use deterministic mocks or fixtures;
  live-provider contract validation is separately recorded and does not gate the
  automated test suite.
- XAUUSD is the sole supported Gold benchmark, quoted in USD per troy ounce.
  The configured Gold source provides daily OHLC evidence and all normalized
  Gold timestamps use UTC. Each collection retains the fullest daily history
  returned within the source's supported limit; Phase 03 does not request or
  present multiple timeframes.
- The Phase 03 plan validates configured Gold-source rights and limits, news
  web-search-provider selection, source-content schema and rights, timestamp
  provenance, and valuation evidence inputs. Phase 03 does not define freshness
  targets or a fresh/stale classification.
- Additional markets are unsupported unless a later spec explicitly introduces
  them.
- Workflows provide research support and evidence framing, not trading decisions
  or autonomous financial actions.
