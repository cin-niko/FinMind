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
allowlist, grounding, artifact, and conversation-store boundaries rather than
creating a gold-only execution path.

Rationale: market-specific collection differs, but evidence safety and user
inspection must remain consistent across markets.

Alternatives considered: a standalone gold service or raw provider payloads in
gold prompts. Rejected because both would duplicate or bypass safety controls.

## Decision: Use Daily XAUUSD OHLC Evidence

Phase 03 supports only the world-gold `XAUUSD` benchmark. The configured Gold
connector uses Twelve Data's daily time-series API and fetches one daily OHLC
price series for each workflow-created
conversation and upserts it through the same canonical price-series model used
for VN prices. It retains
the fullest daily history returned within the source's supported limit. The
normalized evidence contract has canonical UTC timestamps; volume is optional
and must not be inferred when absent. Interval selection, intraday data, and
multi-timeframe analysis are deferred.

Rationale: a generic "gold" feed does not define an auditable user-facing
instrument or safe claim boundary. UTC prevents local display time from changing
the underlying market candle or its evidence timestamp.

Alternatives considered: enabling broad commodities, domestic Gold products, or
using an unverified public source. Rejected because they make provenance and
supported claims vague or mix distinct price products.

## Decision: Mature Workflow Value, Not Only Workflow Mechanics

Phase 03 completes the value and content contracts of its fixed workflows, not
only their runtime wiring. Existing VN technical and fundamental workflows are
matured through their skill content, evidence, sections, unavailable states,
language, and safety rules. VN news digest, valuation, stock brief, and Gold
technical analysis are new workflows with equivalent bounded contracts.

Rationale: a runnable workflow without an agreed evidence and interpretation
contract is not a dependable analyst tool.

## Decision: Adapt VN Research Methodology Behind FinMind Safety Boundaries

The local `equity-research-vn` material is a research input for the VN valuation
and news-digest design. Phase 03 adopts the sector-aware valuation methods and
sensitivity framing from `../../equity-research-vn/vn-valuation-engine/SKILL.md`,
while retaining FinMind's research-only safety boundaries. It also adopts a
bounded 30-day news window and source priority only after FinMind defines
deterministic evidence contracts.

Rationale: the material contains useful domain methodology, but it also includes
external-source assumptions, recommendation language, and presentation assets
that are not automatically valid FinMind product behavior.

### VN Valuation Baseline

Valuation is a cited research range, not a target price, investment label, or
recommendation. The workflow follows the supplied valuation methodology's
sector-method baseline:

| Sector | Core methods | Conditional methods |
|---|---|---|
| Banks | P/B and ROE | DDM for regular cash-dividend payers |
| Cyclical steel | P/B and EV/EBITDA | DCF with valid cash-flow inputs |
| Real estate | P/B and NAV | RNAV when its inputs are available and cited |
| Retail, consumer, technology | P/E and PEG | DCF with valid cash-flow inputs |
| Oil and gas | EV/EBITDA and P/CF | DCF with valid cash-flow inputs |

The workflow may use Graham only when EPS and BVPS are positive. It marks P/E,
PEG, Graham, DCF, DDM, or any other method unavailable when its preconditions do
not hold. It does not manually adjust for restatements, corporate actions, unit
mismatches, or inconsistent periods; instead, it marks the affected method
unavailable.

Eligible method results produce a median and P25–P75 research range. DCF shows
downside, base, and upside cases plus discount-rate and terminal-growth
sensitivity. Each input, method result, and assumption remains cited and
distinguished from reported facts.

The supplied skill references `references/sector_insights.md`, but that file is
not present in the supplied methodology directory. Phase 03 therefore uses the
sector-method matrix embedded in the skill itself; the absent supplemental file
must not be assumed or reconstructed.

### VN News Digest Baseline

The news digest has a bounded 30-day window, declared source priority, visible
publication timestamps, and one cited source for each collected article. A
configured web-search provider searches an application-maintained publisher-
domain allowlist and returns article URL, title, publication time, and content.
The connector normalizes that provider-delivered content into a source document;
raw search responses and raw page payloads are not sent to the workflow or
model. Its useful output is a cited grouping of company, sector, macro,
disclosure, and analyst developments with their evidence and limitations. The
workflow does not deterministically deduplicate articles; the LLM may group
similar cited articles. Sentiment scores, market signals, and investment
recommendations are deferred beyond Phase 03.

## Decision: Keep Technical Output Analysis-Only

All Phase 03 technical workflows describe evidence-backed trend, momentum,
volatility, and risk context. They do not issue signals, buy/sell verdicts,
entry/exit instructions, target prices, or executable trading guidance.

Rationale: this keeps technical research within the advice-support and human-
control boundaries while still providing analyst value.

## Decision: Persist Language Selection And Capture Effective Conversation Language

Phase 03 persists the authenticated user's selection of Auto-detect, Vietnamese,
or English. The default is Auto-detect. The UI renders web copy in the effective
language: explicit `vi` or `en`, or for Auto-detect the first supported language
in the browser's ordered list after normalizing `vi-*` and `en-*`; it uses `en`
when no supported browser language is present.

At workflow submission, the UI sends only the resolved `vi` or `en` value. The
backend validates and captures it as the conversation's output language and adds it to the
model-facing system instruction, e.g. `Language: Respond in the {language}
language`. It does not rely on the model to infer language. If the generated
narrative cannot honor the captured language, it fails safely rather than
silently switching language.

Language does not alter canonical record field names/content, citation titles
or content, publisher names, URLs, source identifiers, timestamps, numeric
values, market symbols, or saved historical output. FinMind-owned UI chrome,
workflow progress, deterministic system messages, and generated narrative use
typed locale keys with English fallback; workflow and API boundaries continue
to expose stable codes rather than localized labels. An Auto-detect selection can
resolve differently in a different browser; each submitted conversation remains
pinned to the value captured when it was submitted.

Rationale: this provides a simple UI choice while sending an unambiguous,
validated language value through the workflow and preserving each conversation's
context.

## Decision: Make Market Scope Explicit At The Catalog Boundary

The catalog enables only `VN_STOCK` and `GOLD`. Other markets must not be
selectable, configured, or retained as active fixtures.

Rationale: users should see scope before submission, not learn it from a failed
request after running a workflow.

## Decision: Move Unfinished Workflow Maturity To Phase 03

The Phase 02 stock brief, field validation, conversation-history, citation reinspection,
delivery documentation, and manual validation work become Phase 03 tasks.

Rationale: these are required to make the VN stock and gold workflow experience
whole, while Phase 02 remains the already-built technical foundation.

## Decision: Keep Chatflow Fully Deferred

Phase 03 adds only workflow-created conversations. Each workflow result passes
through a conversation adapter that creates the conversation's first assistant
message; citations and artifacts attach to that message. It does not add
arbitrary follow-up messages, conversational routing, flexible tool selection,
chat-language detection, or chat streams. Those are Phase 04 responsibilities.

Rationale: bounded dataflows and repeatable workflows establish grounded market
behavior before flexible research interaction is introduced.

## Decision: Keep Workflow Results Separate From Messages

A workflow produces a transient `WorkflowResult` containing safe status, output,
stage state, citations, artifacts, and language. It does not persist a message
or own user history. A `ConversationAdapter` maps that result to the first
assistant message in the newly created workflow conversation and assigns the
citations/artifacts to that message.

Rationale: workflow execution and user conversation are different ownership
boundaries. This lets later chat create the same `Message` type without making
chat depend on a workflow result, while keeping citations/artifacts adjacent to
the answer they support.

Alternatives considered: persist `WorkflowResult` as the history root, or attach
citations/artifacts directly to the conversation. Rejected because each would
blur message ownership and make multi-message conversations ambiguous.

## Decision: Replace Legacy Run History Without Data Migration

Phase 03 removes the persisted `runs`/`run_citations` product contract and
starts conversation history empty. The database migration retains shared
canonical market data such as price-series records but does not translate legacy
run history into conversations.

Rationale: V1 is single-user and existing run history is development data. A
lossless conversion cannot reliably infer the new message ownership model.

Alternatives considered: retain run endpoints as aliases, or migrate each run
to a conversation/message pair. Rejected because aliases preserve two product
roots and migration creates unverified history semantics. This decision must be
revisited before production data requires preservation.

## Blindspot Pass: Decisions Required Before Implementation

This section records open Phase 03 planning gates discovered by reviewing the
feature against the shared contracts and the Phase 02 implementation. These are
not new scope. They must be resolved in the plan and its cross-referenced system
contracts before implementation tasks are regenerated.

### Canonical Timestamp Provenance And Status Semantics

Phase 03 uses the existing timestamp-provenance model: `market_time` is the
user-facing evidence time, and `collected_at` records when FinMind received the
evidence for audit and reinspection. It does not calculate or label a separate
fresh/stale state. Missing, invalid, or source-unavailable fields are normalized
as `None` and rendered deterministically as `Unavailable` before the LLM
receives them; the LLM preserves the limitation in its answer. Valid zero and
false values remain values. Unavailable is not a terminal conversation state and
does not change an otherwise successful conversation. Phase 03 has no `partial`
status: a conversation is successful only when every planned stage completes
safely; otherwise it is failed.

### Gold Daily Series And Timestamp Policy

Phase 03 has one Gold interval: daily OHLC. Each collection requests the
fullest daily history the configured source returns within its supported limit;
there is no interval selector, intraday source, or multi-timeframe analysis.
The provider's valid daily rows are authoritative, so correction, duplicate, and
malformed-candle reconciliation are deferred. A chart and analysis claim use the
same daily series and show its source timestamp consistently; collection time
must not be presented as the market-observation time.

The runtime selects this connector with `FINMIND_GOLD_DATA_PROVIDER=twelvedata`
and supplies its credential through `FINMIND_TWELVE_DATA_API_KEY`. Missing or
invalid configuration fails closed; it never selects another provider.

### Provider Operation, Rights, And Failure Policy

Phase 03 fetches from the configured source for every workflow-created
conversation. It makes at most two retries after an initial transient provider
collection failure, then
fails the workflow safely if all attempts fail. It does not substitute cached
evidence or a fallback provider. Invalid input, unavailable required evidence,
unsupported scope, and failed safety or language checks are not retryable.
Provider-specific rights, attribution, retention, and quota terms are validated
in the planning/source-selection gate and added only when the selected source
requires them; they are not separate Phase 03 product behavior.

### News Evidence Eligibility

The application configuration owns the publisher-domain allowlist; users do not
manage it. Each article must carry provider-delivered URL, title, publication
time, and content before it can be cited. The configured web-search provider,
exact source-document schema, provider rights, and retention rules are planning
decisions. The workflow does not deduplicate; the LLM may group similar cited
articles while preserving their separate citations.

### Valuation Evidence-Input Policy

The valuation method baseline is defined above. Planning validates that the
configured VN evidence source can supply its inputs with consistent currency,
units, reporting periods, and share counts. When it cannot, the affected method
is unavailable. This remains research support, not a target price or
recommendation.

### Claim, Citation, And Reproducibility Policy

Phase 03 reuses the Phase 02 citation contract. Material claims cite an allowed
deterministic record or are explicitly unavailable/unsupported; the existing
grounding check blocks citations outside the assistant message allowlist. Citation snapshots
persist source, dataset, timestamp, rendered evidence, payload, and methodology
version so conversation inspection can show the saved response without refetching data.

Phase 03 does not add a separate definition of citation granularity, workflow or
skill-version persistence, exact historical recomputation, or conflicting-source
resolution. Gold, news, and valuation records use the same citation model; the
LLM may describe a material difference between separately cited sources.

### Language And Preference Boundary

Planning must distinguish static web copy, deterministic system messages,
model-generated narrative, and source evidence. It must state the fallback when
narrative generation cannot honor the captured language, which language is used
for a browser's ordered language list, and how an explicit preference update
behaves when two sessions are open. Evidence identifiers, numeric formats,
timestamps, source quotations, and persisted historical output must retain their
specified immutable behavior.

### Conversation Lifecycle, Cancellation, And Performance

Every workflow-created Phase 03 conversation has a 120-second end-to-end timeout
and ends as `success` or `failed`; timeout is an inspectable failed
conversation. A closed tab or client disconnect does not cancel the accepted
conversation. Phase 03 intentionally
does not add user cancellation, submission idempotency, queue limits, or
concurrency limits; duplicate submissions create independent conversations.

When the service starts, it changes persisted `queued` or `running`
conversations left by the prior service instance to `failed`, records their completion time and a
product-facing interruption summary, and does not resume them. This avoids
mixing evidence collected before and after an interruption. The retry policy is
limited to at most two retries for a transient provider collection failure.

### Authorization And Data Retention Boundary

V1 currently has one internal account, but language preferences and conversations
are modeled as user-owned. Every conversation query is filtered to its owner;
citations and artifacts are accessed through their authorized assistant message
and its authorized conversation.
The plan must retain this boundary before any second user can exist. Conversation
retention lasts until owner deletion; deletion cascades through messages to their
citations and artifacts, but not shared canonical market data. This removes the
need for a separate retention schedule in Phase 03. Source-provider rights still
govern what citation evidence can be stored.

### Acceptance Evidence

All Phase 03 automated tests use deterministic fixtures or mocks for market-data,
news-search, and model-provider behavior. The regenerated task plan must include
fixtures for available daily series, historical-but-recently-collected evidence,
missing evidence, field-level unavailable values, and source-conflicting
evidence. No automated test makes a network call to or depends on live market
data or provider availability.

Live-provider validation is a separate, recorded operational provider-contract
check. It verifies the configured source's access, symbol mapping, schema,
timestamps, and failure behavior, but never gates the ordinary test suite.
