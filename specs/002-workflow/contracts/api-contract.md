---
id: SPEC-FEAT-002-CONTRACTS
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# API Contract: Workflow

All endpoints require an authenticated cookie-backed session.

## `GET /api/workflows`

Returns UI-runnable workflow catalog entries. Internal steps such as
`data-collector` and `data-quality-check` are not primary catalog cards.

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
    "data-collector",
    "data-quality-check",
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
  "status": "success",
  "inputs": { "market": "VN_STOCK", "symbol": "VCB" },
  "started_at": "2026-06-27T00:00:00+00:00",
  "completed_at": "2026-06-27T00:00:02+00:00",
  "output": {
    "sections": [
      {
        "title": "Fundamentals",
        "status": "success",
        "content": "Business quality and valuation summary.",
        "citations": ["cite_1"],
        "warnings": []
      }
    ],
    "quality": {
      "quality_status": "warn",
      "dataset_statuses": {
        "price_series": "fresh",
        "fundamentals": "stale",
        "news_docs": "missing"
      },
      "blocking_issues": ["news_digest_unavailable"],
      "warnings": ["fundamentals_stale"],
      "allowed_claims": ["technical_trend", "price_momentum"],
      "blocked_claims": ["recent_news_impact"],
      "freshness_summary": "Price data fresh; fundamentals stale; news unavailable.",
      "evidence_refs": ["evidence_1"]
    },
    "citations": [
      {
        "citation_id": "cite_1",
        "evidence_id": "evidence_1",
        "label": "Demo VN Prices",
        "source_type": "market_data",
        "source_reference": "VCB-2026-06-18",
        "timestamp": "2026-06-18T07:00:00+00:00"
      }
    ],
    "freshness": [
      {
        "dataset": "vn_prices",
        "status": "fresh",
        "as_of": "2026-06-18T07:00:00+00:00"
      }
    ],
    "artifacts": {
      "chart": {
        "artifact_id": "artifact_1",
        "artifact_type": "chart",
        "title": "VCB Price Series",
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
        "evidence_refs": ["evidence_1"]
      }
    },
    "visible_execution": {
      "stages": [
        { "id": "data-collector", "status": "success", "warnings": [] },
        { "id": "data-quality-check", "status": "partial", "warnings": ["fundamentals_stale"] },
        { "id": "news-digest", "status": "unavailable", "warnings": ["news_digest_unavailable"] }
      ],
      "tool_status": "partial"
    }
  },
  "logs": [
    { "event": "workflow_started", "stage": "data-collector" },
    { "event": "workflow_completed", "status": "partial" }
  ]
}
```

Raw agent reasoning must never appear in responses.

## `GET /api/runs`

Returns workflow runs visible to the authenticated user for history and result
reinspection. Latest runs appear first.

## `GET /api/runs/{run_id}`

Returns a completed, partial, or failed workflow run. Unknown run ids return
`404`.
