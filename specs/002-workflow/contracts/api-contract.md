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
    "collection": {
      "status": "partial",
      "retrieval_id": "retrieval_abc123",
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
      "started_at": "2026-06-27T00:00:00+00:00",
      "completed_at": "2026-06-27T00:00:01+00:00"
    },
    "agent": {
      "status": "partial",
      "runtime_adapter": "langchain_litellm",
      "policy_id": "workflow_strict",
      "skill_id": "vn-financial-data-collector",
      "retrieval_plan_status": "executed",
      "tool_status": "partial",
      "allowed_claims": ["price_snapshot", "company_profile"],
      "blocked_claims": ["audited_financial_trend", "recent_news_impact"],
      "warnings": ["fundamentals_missing", "news_provider_unavailable"],
      "validation_errors": []
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

Agent contract:

- `agent.status` values: `success`, `partial`, `failed`, `unavailable`.
- `runtime_adapter` is a safe runtime identity such as `langchain_litellm` or
  `langchain_agent`; it is not a provider secret or hidden prompt.
- `policy_id` identifies the runtime policy envelope. Phase 02 workflow runs use
  a strict workflow policy with fixed skills, skill-owned data requirements,
  bounded iterations, dataflows-only tool access, and fail-closed behavior.
- `skill_id` identifies the governed Agent Skill executed for the stage or run.
- `retrieval_plan_status` indicates whether the agent-derived retrieval plan was
  proposed, approved, rejected, executed, or partial. It is safe status metadata,
  not raw reasoning.
- `tool_status`, `warnings`, `blocked_claims`, and `validation_errors` are safe
  execution metadata for UI inspection.
- `agent` must never contain raw chain-of-thought, hidden prompts, provider
  secrets, raw provider payloads, or unsafe diagnostics.
- Material claims generated by an agent must pass FinMind validators for
  citations, freshness, data-quality gates, market scope, and advice-only
  framing before appearing in `sections`.

Collection contract:

- `collection.status` values: `success`, `partial`, `failed`, `fallback`.
- `collection` is produced by `src/finmind_agents/dataflows/` after a
  FinMind-validated retrieval plan, not direct workflow or agent provider calls.
- `providers` may include provider ids such as `vnstock`, `alpha_vantage`,
  `sec_edgar`, and `offline_fallback`.
- `requested_dataset_groups` values are `market_price`, `fundamental`, and
  `news` for Phase 02.
- Requested dataset groups are derived from the referenced skill's
  `DATA_REQUIREMENTS.yaml` and the agent's approved retrieval plan. Workflow YAML
  must not duplicate detailed dataset requirements.
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
