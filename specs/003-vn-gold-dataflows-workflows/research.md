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

## Decision: Use XAUUSD OHLC Evidence From Twelve Data

Phase 03 supports only the world-gold `XAUUSD` benchmark. Twelve Data is the
selected source behind the Gold connector. The normalized evidence contract is
OHLC price history with canonical UTC timestamps; volume is optional and must
not be inferred when absent.

Rationale: a generic "gold" feed does not define an auditable user-facing
instrument or safe claim boundary. UTC prevents local display time from changing
the underlying market candle or freshness calculation.

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
and news-digest design. Phase 03 may adapt sector-aware valuation methods,
sensitivity presentation, a bounded 30-day news window, source priority, and
deduplication rules only after FinMind defines source rights and deterministic
evidence contracts.

Rationale: the material contains useful domain methodology, but it also includes
external-source assumptions, recommendation language, and presentation assets
that are not automatically valid FinMind product behavior.

### VN Valuation Baseline

Valuation is a cited research range, not a target price or recommendation. The
workflow selects sector-appropriate methods from the local research baseline,
including historical multiples, enterprise-value measures, cash-flow methods,
and intrinsic-value methods only when their required inputs are available and
period-consistent. It presents assumptions and sensitivity for model-dependent
methods and marks inapplicable methods unavailable.

### VN News Digest Baseline

The news digest has a bounded 30-day window, declared source priority, visible
publication timestamps, and one cited news record for each collected article.
It uses a domain-restricted web-search connector rather than publisher APIs.
Its useful output is a cited grouping of company, sector, macro, disclosure, and
analyst developments with their evidence and limitations. Deduplication,
sentiment scores, market signals, and investment recommendations are deferred
beyond Phase 03.

## Decision: Keep Technical Output Analysis-Only

All Phase 03 technical workflows describe evidence-backed trend, momentum,
volatility, and risk context. They do not issue signals, buy/sell verdicts,
entry/exit instructions, target prices, or executable trading guidance.

Rationale: this keeps technical research within the advice-support and human-
control boundaries while still providing analyst value.

## Decision: Persist Web Language Per Authenticated User

Phase 03 supports Vietnamese and English. The authenticated user's web-language
preference is persisted server-side and captured when a workflow is submitted.
It controls web-visible copy and workflow narrative, but not source identifiers,
citations, timestamps, numeric values, or market symbols.

On first authenticated use, a supported browser language is saved as the
preference; English is saved when the browser language is unsupported or absent.
An explicit later preference replaces that initial value.

Rationale: server ownership makes preference behavior consistent across browser
sessions and preserves the language context of historical workflow runs.

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
selection, chat-language detection, or chat streams. Those are Phase 04
responsibilities.

Rationale: bounded dataflows and repeatable workflows establish grounded market
behavior before flexible research interaction is introduced.
