---
id: SPEC-FEAT-002-CONTRACTS
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# API Contract: Workflow

All endpoints require an authenticated cookie-backed session.

## `GET /api/workflows`

Returns UI-runnable workflow catalog entries. Internal steps such as
`collect_data` and the data-audit skill are not primary catalog cards.

Response item shape:

```json
{
  "id": "stock-brief",
  "title": "Stock Brief",
  "description": "Combined cited stock research brief.",
  "workflow_type": "composite",
  "market_scope": ["VN_STOCK", "US_STOCK"],
  "required_inputs": [
    { "name": "market", "type": "string", "required": true },
    { "name": "symbol", "type": "string", "required": true }
  ],
  "stages": [
    "collect_data",
    "data-audit",
    "fundamental-analysis",
    "technical-analysis",
    "news-digest",
    "risk-review"
  ],
  "requires_citations": true,
  "chart_requirements": ["price_series"],
  "output_sections": [
    "Data Quality",
    "Fundamentals",
    "Technical Analysis",
    "News Digest",
    "Risk Review"
  ]
}
```

Required catalog ids:

- `fundamental-analysis`
- `technical-analysis`
- `news-digest`
- `risk-review`
- `stock-brief`

## `POST /api/workflows/{workflow_id}/run`

Runs a bounded workflow with validated inputs.

Request:

```json
{
  "market": "VN_STOCK",
  "symbol": "VCB"
}
```

Valid markets:

- `VN_STOCK`
- `US_STOCK`

Validation errors:

- Unsupported market or asset: `422`
- Unsupported symbol for market: `422`
- Missing required input: `422`
- Unknown workflow: `404`

Response shape:

```json
{
  "id": "run_abc123",
  "kind": "workflow",
  "status": "partial",
  "inputs": { "market": "VN_STOCK", "symbol": "VCB" },
  "started_at": "2026-06-27T00:00:00+00:00",
  "completed_at": "2026-06-27T00:00:02+00:00",
  "output": {
    "sections": [
      {
        "title": "Collected Data",
        "status": "success",
        "content": "Audited VCB financial data package with citations.",
        "citations": ["cite_1"],
        "warnings": [],
        "allowed_claims": ["data_availability"],
        "blocked_claims": []
      },
      {
        "title": "Fundamentals",
        "status": "partial",
        "content": "Fundamental analysis on available statements; news-dependent claims blocked.",
        "citations": ["cite_1"],
        "warnings": ["news_missing"],
        "allowed_claims": ["financial_history"],
        "blocked_claims": ["recent_news_impact"]
      }
    ],
    "steps": [
      { "id": "collect_data", "kind": "collect_data", "status": "fallback", "warnings": [] },
      { "id": "vn-financial-data-auditor", "kind": "skill", "status": "success", "warnings": [] },
      { "id": "vn-fundamental-analysis", "kind": "skill", "status": "partial", "warnings": ["news_missing"] }
    ],
    "collection": {
      "status": "partial",
      "collection_id": "collection_abc123",
      "providers": ["vnstock", "offline_fallback"],
      "requested_dataset_groups": ["market_price", "fundamental", "news"],
      "provider_results": [
        {
          "provider_id": "vnstock",
          "dataset_groups": ["market_price", "fundamental"],
          "status": "success",
          "source_ids": ["vnstock_prices", "vnstock_fundamentals"],
          "warnings": []
        },
        {
          "provider_id": "offline_fallback",
          "dataset_groups": ["news"],
          "status": "fallback",
          "source_ids": ["offline_source_documents"],
          "warnings": ["news_provider_unavailable"]
        }
      ],
      "records_collected": 2,
      "documents_collected": 1,
      "warnings": ["source_documents_fallback"],
      "failure_reasons": [],
      "started_at": "2026-06-27T00:00:00+00:00",
      "completed_at": "2026-06-27T00:00:01+00:00"
    },
    "citations": [
      {
        "citation_id": "cite_1",
        "source_id": "vnstock_prices",
        "dataset_id": "vn_prices",
        "label": "Demo VN Prices",
        "timestamp": "2026-06-18T07:00:00+00:00"
      }
    ],
    "artifacts": {
      "chart": {
        "artifact_id": "artifact_1",
        "artifact_type": "chart",
        "title": "VCB Price Series",
        "inputs": ["vn_prices"],
        "payload": {
          "series": [{ "time": "2026-06-18", "value": 58200 }],
          "table": [
            {
              "record_key": "VCB-2026-06-18",
              "market_time": "2026-06-18T07:00:00+00:00",
              "close": 58200
            }
          ]
        },
        "source_refs": ["cite_1"]
      }
    },
    "grounding": {
      "grounding_status": "pass",
      "blocked_claims": ["recent_news_impact"],
      "uncited_claims": []
    }
  },
  "logs": [
    { "event": "workflow_started", "stage": "collect_data" },
    { "event": "workflow_completed", "status": "partial" }
  ]
}
```

Raw agent reasoning must never appear in responses.

Step and grounding contract:

- `steps` is the ordered `step_sequence` execution trace. Each step has `kind`
  `collect_data` or `skill`, a `status`, and `warnings`.
- `collect_data` step status is informational only (`success`, `partial`,
  `failed`, `fallback`); run status is derived from skill steps.
- Skill step `status` values: `success`, `partial`, `failed`. There is no
  pre-skill fail-fast: a skill runs on whatever `collect_data` returned and
  resolves which claims it can support, reporting `blocked_claims` for the rest.
  Run status is `failed` if any skill step failed, else `partial` if any skill
  step is `partial`, else `success`.
- `collect_data` is the only hard floor: zero records and zero source documents
  fails the run before any skill step.
- `grounding.grounding_status` is `pass` or `blocked`. It is `blocked` only when
  claims cite sources not present in the returned citations (`uncited_claims`).
- `grounding.blocked_claims` lists claim categories the skill reported blocked
  (surfaced for transparency).
- `grounding.uncited_claims` lists claims whose citations are not a subset of the
  returned citation ids (a grounding violation).
- Raw agent reasoning must never appear in `steps`, `sections`, or `grounding`.
- Material claims generated by a skill must pass FinMind validators for
  citations, market scope, and advice-only framing before appearing in
  `sections`. Data age is conveyed by citation `timestamp`; there is no separate
  freshness field.

Collection contract:

- `collection.status` values: `success`, `partial`, `failed`, `fallback`.
- `collection` is produced by `src/finmind_agents/dataflows/` after a
  FinMind-validated collection plan, not direct workflow or agent provider calls.
- `providers` may include provider ids such as `vnstock`, `alpha_vantage`,
  `sec_edgar`, and `offline_fallback`.
- `requested_dataset_groups` values are `market_price`, `fundamental`, and
  `news` for Phase 02.
- Requested dataset groups are derived from the referenced skills'
  `DATA_REQUIREMENTS.yaml` (raw-data skills only; upstream-dependent skills have
  none and are not added to the collect fetch list). Workflow YAML must not
  duplicate detailed dataset requirements.
- `provider_results` are safe status summaries. They must not include raw
  provider payloads.
- Provider API keys, credentials, raw responses, hidden prompts, and unsafe
  diagnostics must never appear in API responses.
- If live provider collection fails and fallback data is used, the response must
  preserve the fallback provider id and quality warnings so user-facing claims
  are caveated or marked unavailable.

## `GET /api/runs`

Returns workflow runs visible to the authenticated user for history and result
reinspection. Latest runs appear first.

## `GET /api/runs/{run_id}`

Returns a completed, partial, or failed workflow run. Unknown run ids return
`404`.
