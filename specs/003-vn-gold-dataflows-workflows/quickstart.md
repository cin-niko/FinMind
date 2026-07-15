---
id: SPEC-FEAT-003-QUICKSTART
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Quickstart: VN And Gold Dataflows And Workflows Validation

## Prerequisites

- Authenticated local FinMind environment with the Phase 02 workflow foundation.
- `FINMIND_DATABASE_URL` configured for persisted conversation inspection.
- `FINMIND_GOLD_DATA_PROVIDER=twelvedata` and a locally supplied
  `FINMIND_TWELVE_DATA_API_KEY` for the production XAUUSD connector. Automated
  tests inject a mock HTTP boundary and do not use this credential.
- Deterministic mocked or fixture-based VN stock and Gold evidence; automated
  validation must not call a live provider.

## Scenario 1: Gold Evidence Collection

1. Run collection for XAUUSD daily OHLC evidence with its declared datasets.
2. Verify every returned record exposes source id, dataset id, UTC market and
   collection timestamps, daily interval, rendered context, and citation
   eligibility.
3. Use a fixture whose market timestamp precedes its collection timestamp, then
   verify both times are preserved and collection time is not shown as evidence
   time. Also simulate a missing or undeclared dataset.
4. Verify the result is warning, unavailable, or rejected rather than
   claim-ready.
5. Simulate an initial transient provider failure followed by two retry failures.
   Verify the workflow fails safely after three total attempts, with no cached or
   fallback evidence presented.

## Scenario 2: Gold Workflow

1. Open the workflow catalog and activate the Gold technical-analysis card.
2. Confirm it opens the same confirmation dialog as other workflows, shows its
   fixed XAUUSD scope, stock-only financial sections are absent, and no market,
   symbol, instrument, or interval control is shown before Run is selected.
3. Submit the workflow and observe safe progress before final output.
4. Verify each material claim has citation provenance or an unavailable marker;
   inspect chart/artifact status and the source market or publication timestamp.

## Scenario 3: VN Stock Brief

1. Select the VN stock brief workflow and a supported VN stock symbol.
2. Verify collection, grounding, fundamental, and technical stages are visible.
3. Cause a collected or derived field such as P/E to be unavailable in a
   deterministic fixture.
4. Verify the rendered evidence context marks that field unavailable before
   analysis, the final answer retains the limitation without a fabricated value,
   and the conversation remains successful when every planned stage completes
   safely.

## Scenario 4: VN News Digest

1. Run the news digest for a supported VN stock symbol.
2. Verify every cited article exposes its URL, title, publication time, and
   provider-delivered content from an allowed publisher domain.
3. Verify similar articles may appear as separate citations while the narrative
   may group them; no deterministic deduplication is expected.

## Scenario 5: VN Valuation

1. Run valuation for a supported VN stock with sector-appropriate, complete
   deterministic fixture data.
2. Verify only eligible sector methods appear, each method cites its inputs, and
   the result shows the median and P25–P75 research range without a target price
   or recommendation.
3. For a DCF-eligible fixture, verify downside, base, and upside cases plus
   discount-rate and terminal-growth sensitivity.
4. Remove or make inconsistent a required input such as EPS, BVPS, cash flow,
   reporting period, or share count. Verify the affected method is unavailable
   without an estimated replacement.

## Scenario 6: Language Selection

1. Open Settings from the authenticated left-rail footer. Confirm it offers
   Auto-detect, English, and Vietnamese, with Auto-detect as the initial saved
   selection; confirm it is not a primary navigation item.
2. With a browser language list beginning `vi-VN`, select Auto-detect and verify
   UI copy and the submitted workflow language are `vi`. Repeat with an
   unsupported browser language list and verify the effective language is `en`.
3. Select English and Vietnamese explicitly and verify each immediately controls
   UI copy. Submit one workflow under each selection and verify the backend
   receives and the saved conversation retains only the matching `en` or `vi`
   value.
4. Verify the workflow's generated title, sections, and limitations honor the
   captured language; a result that cannot do so fails safely rather than being
   silently shown in the other language.

## Scenario 7: Lifecycle And Reinspection

1. Attempt an unsupported market or asset input.
2. Verify Phase 03 blocks or visibly marks each request before a result exists.
3. Start a workflow and verify it immediately creates a new conversation. Close
   the browser tab; verify the conversation continues and can be reopened after
   it reaches a terminal status.
   Verify the stream begins with `conversation.started`, emits only
   conversation-oriented event names, and ends with an adapter-created first
   assistant message or safe failure summary.
4. Use a fixture that exceeds 120 seconds and verify an inspectable `failed`
   timeout result, not a permanently running conversation.
5. Seed queued and running conversations from a prior service instance, start
   the service, and verify each becomes an inspectable `failed` interruption
   result without being resumed.
6. Complete one VN stock and one gold workflow, then reopen each created
   conversation from history. Verify its workflow result has been mapped to the
   first assistant message.
7. Delete one conversation and verify its messages and the citations and
   artifacts owned by those messages, plus execution metadata, are removed while
   canonical market data remains available to the other conversation.
8. Verify final output or failure summary, status, citations, artifacts, and
   limitations persist for the remaining conversation.

## Verification

Run the relevant backend tests with `uv run pytest`. Build the UI using the
command in `src/finmind_ui/package.json`. Record source-specific manual
live-provider contract validation separately before enabling a gold workflow
beyond deterministic fixtures; it must not run as part of the automated suite.
