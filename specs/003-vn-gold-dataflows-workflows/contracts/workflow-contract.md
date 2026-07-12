---
id: SPEC-FEAT-003-CONTRACTS
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Workflow Contract: VN And Gold Dataflows And Workflows

This feature extends the shared API and evidence contracts in
`../../system/contracts.md`, `../../system/state-model.md`, and
`../../system/data-record-flow.md`.

## Catalog Contract

Each enabled catalog entry must include:

- stable `workflow_id`, title, and purpose;
- `market_scope` containing only `VN_STOCK` or `GOLD`, with `XAUUSD` as the
  sole enabled Gold instrument;
- required input schema and supported instrument selection;
- required dataset groups, ordered stage labels, expected output sections, and
  chart requirements;
- citation and timestamp-provenance expectations and unsupported claim
  categories.

The Gold catalog entry declares one fixed daily interval. It must not expose an
interval selector or multi-timeframe output in Phase 03.

Phase 03 must not serialize unsupported workflows as enabled catalog choices.

## Gold Dataflow Contract

A supported gold collection result must return:

- normalized records or source documents with `source_id`, `dataset_id`, UTC
  market time, and UTC `collected_at`;
- bounded record context plus citation allowlist identifiers;
- provider/collection status, unavailable datasets, warnings, and failure
  reasons; and
- no raw provider payloads, credentials, or unsupported claim categories in
  user-facing output.

Any missing, invalid, unavailable, mismatched, or undeclared gold dataset must
mark its affected claims unavailable or reject the workflow before answer
generation. Phase 03 does not assign a fresh/stale state: the market timestamp
is the user-facing evidence time and `collected_at` is retained in evidence
provenance for audit and reinspection.

Before evidence is supplied to the LLM, collection and derivation normalize each
missing, invalid, or source-unavailable field to `None`; deterministic record
context renders it as `Unavailable`. Generated output must preserve that
limitation without inventing a value. Valid zero and false values remain values.
Such a field does not change an otherwise safely completed workflow-created
conversation.

Gold collection fetches and upserts one XAUUSD daily OHLC price series using the
fullest history returned within the configured source's supported limit. Gold
timestamps normalize to UTC. A missing volume field remains unavailable and
must not be inferred. Phase 03 treats the configured source's valid daily rows
as authoritative; provider-row correction and reconciliation are deferred.
Collection makes at most two retries after an initial transient
configured-provider failure. If all attempts fail, the workflow fails safely
with a product-facing failure summary; it must not return cached evidence,
substitute a fallback provider, or disclose raw provider diagnostics. Invalid
input, unavailable required evidence, unsupported scope, and failed safety or
language checks are not retryable.

## News Digest Evidence Contract

The VN news digest uses a web-search provider configured with an
application-maintained publisher-domain allowlist. Each collected article source
must expose URL, title, publication time, and provider-delivered content before
it can support a cited development. The workflow retains each cited article as a
separate source; it does not deterministically deduplicate or merge articles.
The LLM may group similar cited articles in its narrative. Provider selection,
content schema, rights, and retention rules are resolved in planning.

## VN Valuation Contract

The valuation workflow applies the sector-method selection and input gates in
FR-028 through FR-030. It receives only cited, period-consistent normalized
financial inputs. A method with missing, negative, restated, unit-inconsistent,
or corporate-action-ambiguous inputs is unavailable rather than estimated. The
result presents eligible method results, their median and P25–P75 research
range, and DCF scenarios/sensitivity where DCF is eligible. It must not issue a
target price, investment label, or recommendation.

## Workflow Conversation Contract

`POST /api/workflows/{workflow_id}/conversations` creates an owned conversation
before execution and retains the Phase 02 SSE event contract for valid Phase 03
inputs. Every submission creates a new conversation. The workflow produces a
`WorkflowResult`; the conversation adapter maps that result to the new
conversation's first assistant message. Citations and artifacts are persisted on
that message. Safe progress events, terminal status, and the resulting message
must remain reconcilable with conversation inspection.

The request must reject or visibly mark:

- missing or malformed inputs;
- a market outside `VN_STOCK` or `GOLD`;
- a Gold instrument outside `XAUUSD`;
- undeclared dataset requests; and
- unsafe or unsupported claim categories.

The Gold technical-analysis workflow has no user-editable market, symbol, or
instrument input. The server binds its collection request to `GOLD` and
`XAUUSD`; client-provided overrides are rejected.

## Conversation Inspection And Retention Contract

`GET /api/conversations` and `GET /api/conversations/{conversation_id}` expose
only conversations owned by the authenticated user. Each response preserves the
initiating workflow metadata, market, instrument, stage status, first assistant
message or product-facing failure summary, and that message's artifacts,
citation provenance, and limitations without disclosing raw reasoning.
Unavailable is not a persisted conversation status; it is preserved in rendered
output as a field, claim, chart, or section limitation.

`DELETE /api/conversations/{conversation_id}` is available only to the owner and
cascade-deletes its messages and every citation snapshot and artifact owned by
those messages, plus execution metadata. There is no automatic time-based purge
in Phase 03. Shared canonical market data remains intact. Deletion is accepted
only after a conversation is `success` or `failed`; it is rejected while
`queued` or `running` because Phase 03 has no cancellation.

## Lifecycle Contract

An accepted workflow-created conversation must reach `success` or `failed`
within 120 seconds. A timeout produces an inspectable failed conversation with a
product-facing timeout summary. Closing the browser tab or disconnecting the
client does not cancel the conversation; it continues and persists its terminal
result.

Phase 03 provides no user cancellation, deduplication/idempotency, queue limit,
or concurrency-limit behavior. Each accepted submission creates an independent
conversation. At service startup, any persisted `queued` or `running`
conversation interrupted by the previous service instance is marked `failed`
with a completed timestamp and interruption summary. It is not resumed.

Phase 03 reuses the shared citation allowlist, grounding validation, and
persisted citation-snapshot model. Each cited Gold, news, or valuation record
uses the same source, dataset, timestamp, payload-snapshot, and methodology
provenance as Phase 02. Conversation inspection shows the saved response and its
citation snapshots through its assistant message; exact historical recomputation
or a new conflicting-source resolution model is out of scope.

## Language Preference Contract

The authenticated user's persisted language selection is `auto`, `vi`, or `en`.
The UI offers Auto-detect, English, and Vietnamese, and uses the selected
language for web-visible copy. `auto` resolves the browser's ordered language
list by normalizing `vi-*` to `vi` and `en-*` to `en`, selecting the first
supported entry, or using `en` if none is supported.

At submission, the UI sends the resolved `vi` or `en` value. The backend accepts
only those values, captures the accepted value on the conversation, and supplies it to the
LLM's system-language instruction (for example, `Language: Respond in the
{language} language`). A model result that cannot honor the captured language
fails safely; the system does not silently substitute the other language.

Language selection does not translate or alter evidence identifiers, citations,
timestamps, numeric values, market symbols, or prior saved conversation output.

## Safety Contract

- Material claims cite an allowed record or are marked unavailable/unsupported.
- Stock-only financial sections never appear as gold evidence.
- Gold-specific context is not silently mixed into VN stock workflows.
- Outputs provide research support only and refuse broker, order, and trade
  execution actions.
