---
id: SPEC-FEAT-002-DATA
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# Data Model: Workflow

This feature uses shared entities from `../system/state-model.md` and defines
Phase 02 workflow-specific usage/extensions below.

## MarketInstrument

Represents a supported equity instrument.

Fields:

- `instrument_id`: stable symbol or index id such as `VCB`, `VNINDEX`, `AAPL`.
- `symbol`: user-facing symbol.
- `market`: `VN_STOCK` or `US_STOCK`.
- `display_name`: user-facing label.
- `currency`: quote currency.
- `status`: active, inactive, unsupported.

Validation:

- Phase 02 accepts only `VN_STOCK` and `US_STOCK`.
- Gold, BTC, crypto, commodities, options, and futures are unsupported.

## CanonicalMarketDataRecord

Normalized market data item used by collection, charts, indicators, and evidence.

Fields:

- `dataset_id`: `vn_prices`, `us_prices`, `vn_fundamentals`,
  `us_fundamentals`, `source_documents`, or equivalent bounded demo dataset.
- `record_key`: unique logical key.
- `instrument_id`: linked instrument.
- `market_time`: effective market timestamp.
- `collected_at`: collection timestamp.
- `source_id`: source connector or demo source identity.
- `retrieval_id`: optional id linking records fetched during the same dataflow
  retrieval attempt.
- `payload`: normalized values such as close, change percent, volume, EPS, BVPS,
  revenue, profit, valuation ratios, or peer metrics.
- `freshness_status`: fresh, stale, missing, failed.

Validation:

- `(dataset_id, record_key)` is unique.
- Price records used in technical analysis must include enough points for the
  requested chart/indicator or the chart claim category is blocked.
- Fundamental records used in valuation must include compatible reporting period
  metadata or valuation confidence is blocked/qualified.
- Provider records must preserve market/effective timestamp and collection
  timestamp separately.
- Deterministic fallback records must use source ids that make fallback status
  visible, not pretend to be live provider data.

## DataflowRetrievalRequest

Input contract for retrieving evidence-ready finance data.

Fields:

- `market`: `VN_STOCK` or `US_STOCK`.
- `symbol`
- `dataset_groups`: `market_price`, `fundamental`, `news`.
- `lookback`: optional period/window for price history or news.
- `allow_fallback`: whether deterministic fallback may be used when live
  providers are unavailable.
- `requested_by`: workflow id or future chatflow request id.

Validation:

- Dataset groups must be requested through an agent retrieval plan derived from
  skill-owned `DATA_REQUIREMENTS.yaml` or future chatflow retrieval needs.
- Unsupported markets or symbols are rejected before provider calls.
- Fallback use must be explicit and visible in the retrieval result.

## DataflowRetrievalResult

Output contract returned by `DataflowService.retrieve(...)`.

Fields:

- `retrieval_id`
- `market`: `VN_STOCK` or `US_STOCK`.
- `symbol`
- `requested_dataset_groups`: `market_price`, `fundamental`, `news`.
- `provider_results`: provider status records.
- `records`: canonical market data records.
- `source_documents`: source documents/news records.
- `started_at`
- `completed_at`
- `status`: success, partial, failed, fallback.
- `warnings`
- `failure_reasons`
- `records_collected`
- `documents_collected`

Validation:

- Provider failures, missing API keys, timeouts, rate limits, and unsupported
  symbols must be represented in `warnings` or `failure_reasons`.
- A fallback run must not be marked as fresh live provider data.
- Raw provider payloads and secrets must not be returned.

## DataflowProviderResult

Status for one provider attempt within a retrieval.

Fields:

- `provider_id`: e.g. `vnstock`, `alpha_vantage`, `sec_edgar`,
  `offline_fallback`.
- `dataset_groups`
- `status`: success, partial, failed, skipped, fallback.
- `source_ids`
- `started_at`
- `completed_at`
- `warnings`
- `failure_reason`
- `rate_limit_hint` when available.

Validation:

- Provider status is user-visible only as safe source/status metadata.
- Provider diagnostics must not include credentials, raw responses, or unsafe
  internals.

## SourceProvider

Adapter identity and capability metadata.

Fields:

- `provider_id`
- `market_scope`
- `dataset_capabilities`
- `requires_api_key`
- `license_notes`
- `timeout_seconds`
- `enabled`

Validation:

- Provider adapters must normalize output to shared canonical records/documents.
- Provider secrets and raw responses must not appear in user-facing output.
- Product contracts should cite source identity and data timestamp without
  hardcoding implementation details into UI copy.

## SourceDocument

Trusted source material for news digest and fundamental context.

Fields:

- `document_id`
- `source_id`
- `title`
- `published_at`
- `collected_at`
- `url_or_reference`
- `content_excerpt`
- `market_scope`
- `instrument_ids`
- `sentiment_hint` when available

Validation:

- Missing or stale documents block or qualify news digest claims.
- Source excerpts must respect source constraints.

## FinMindAgentRuntime

Shared runtime boundary for workflow agents in Phase 02 and future chatflow
agents in Phase 03.

Fields:

- `runtime_id`: stable runtime identity.
- `adapter`: runtime adapter such as `langchain_litellm`, `langchain_agent`, or
  another approved adapter.
- `model_config_ref`: safe reference to configured model settings; never a
  secret value.
- `policy`: linked `AgentRuntimePolicy`.
- `tools`: approved `AgentTool` definitions.
- `skill_registry`: available governed Agent Skills.
- `sub_agents`: optional `SubAgentDefinition` records.
- `validators`: output, citation, quality, market-scope, and safety validators.

Validation:

- Runtime adapters are swappable but must produce the same FinMind result
  envelope.
- Runtime configuration must not expose provider secrets, API keys, hidden
  prompts, or raw model reasoning.
- Workflow mode must fail closed when the model is not configured or when the
  adapter cannot satisfy the workflow policy.

## AgentRuntimePolicy

Execution policy envelope for one runtime mode.

Fields:

- `policy_id`: e.g. `workflow_strict` or `chatflow_research`.
- `mode`: workflow or chatflow.
- `allowed_tools`: tool ids the agent may call.
- `allowed_skills`: skill ids the agent may load.
- `allowed_markets`: `VN_STOCK` and `US_STOCK` for Phase 02.
- `allowed_dataset_groups`: dataset groups the policy permits.
- `allow_optional_retrieval`: whether optional skill data may be requested.
- `max_iterations`
- `timeout_seconds`
- `output_schema`
- `failure_behavior`: fail_closed, partial_answer, or unavailable.
- `citation_policy`
- `raw_reasoning_policy`: must be hidden.
- `human_control_policy`: advice-only, no trade/order execution.

Validation:

- Workflow policy must restrict skills to the YAML workflow contract and
  datasets to the loaded skill's `DATA_REQUIREMENTS.yaml`.
- Chatflow policy may be broader later but still must require data-driven,
  citation-backed answers.
- Policies must block unsupported assets and irreversible financial actions.

## AgentTool

Tool made available to the shared agent runtime.

Fields:

- `tool_id`: stable id such as `retrieve_dataflow`, `load_skill`,
  `validate_finmind_output`, or future approved tools.
- `description`
- `input_schema`
- `output_schema`
- `allowed_policy_ids`
- `side_effect_profile`: read_only, write_run_state, or forbidden.
- `audit_visibility`: what safe status can appear in logs/UI.

Validation:

- Provider access must go through `retrieve_dataflow`; tools must not expose raw
  provider clients directly.
- `retrieve_dataflow` must validate requests against the workflow policy,
  workflow inputs, and skill-owned data requirements before execution.
- Tool outputs must be safe to include in the agent context after redaction.
- Tool status may be visible; raw payloads, secrets, and unsafe diagnostics may
  not be visible.

## SkillDataRequirements

Machine-readable data contract stored beside an Agent Skill as
`src/finmind_agents/skills/<skill-name>/DATA_REQUIREMENTS.yaml`.

Fields:

- `skill_id`
- `version`
- `market_scope`
- `required`: required dataset requests that must be attempted before
  claim-generating synthesis.
- `optional`: optional dataset requests the agent may request when policy and
  timeout budget allow.
- `dataset_id`
- `dataset_group`: `market_price`, `fundamental`, `news`, or approved future
  groups.
- `fields`
- `lookback`
- `periods`
- `freshness_policy`
- `fallback_policy`
- `claim_categories_supported`
- `claim_categories_blocked_when_missing`

Validation:

- Required data requirements must be attempted during workflow runs.
- Optional data requirements may be skipped only with visible warnings or
  unavailable sections when they affect user-facing claims.
- Market scope cannot exceed the workflow YAML market scope or runtime policy.
- Provider names are implementation hints only when needed; skills must request
  data through dataset contracts, not direct provider APIs.

## AgentRetrievalPlan

Concrete retrieval plan derived by the agent/runtime after reading an Agent Skill
and its `DATA_REQUIREMENTS.yaml`.

Fields:

- `plan_id`
- `skill_id`
- `market`
- `symbol`
- `required_requests`
- `optional_requests`
- `reason_code`: safe short reason such as `required_by_skill` or
  `optional_peer_context`; never raw reasoning.
- `policy_id`
- `status`: proposed, approved, rejected, executed, partial.

Validation:

- Plans are proposals until FinMind validates them.
- Required requests must map to `SkillDataRequirements.required`.
- Optional requests must map to `SkillDataRequirements.optional` and policy.
- Unsupported markets, symbols, dataset groups, direct provider access, and
  secrets are rejected before dataflows execution.

## SubAgentDefinition

Optional domain-specific agent used by the runtime for bounded delegation.

Fields:

- `sub_agent_id`: e.g. `vn_market_data_agent`, `fundamental_data_agent`,
  `technical_data_agent`, `news_source_agent`, or `risk_review_agent`.
- `purpose`
- `allowed_tools`
- `allowed_skills`
- `output_contract`
- `policy_overrides`

Validation:

- Sub-agent outputs are intermediate and cannot bypass FinMind validators.
- Sub-agents inherit the parent run's market scope, safety policy, data-quality
  status, citation policy, and no-raw-reasoning rule.

## AgentRunRequest

Input passed from workflow service to `FinMindAgentRuntime`.

Fields:

- `run_id`
- `mode`: workflow for Phase 02.
- `workflow_id`
- `skill_id`
- `market`
- `symbol`
- `data_requirements`
- `retrieval_plan`: proposed or approved `AgentRetrievalPlan`.
- `retrieval_results`: populated after validated `retrieve_dataflow` calls.
- `quality_report`: populated after FinMind quality checks.
- `evidence_refs`: populated from retrieved canonical records/documents.
- `output_schema`
- `policy_id`

Validation:

- `market`, `symbol`, and `skill_id` must be compatible with the workflow YAML
  definition.
- `data_requirements` must be loaded from the referenced skill, not duplicated
  from workflow YAML.
- Workflow agent runs may start before retrieval, but claim-generating synthesis
  must wait until validated retrieval and data-quality context are available.
- Missing required LLM configuration blocks execution instead of producing
  deterministic prose disguised as analysis.

## AgentRunResult

Structured output from `FinMindAgentRuntime` after validation.

Fields:

- `status`: success, partial, failed, unavailable.
- `adapter`
- `skill_id`
- `sections`
- `citations`
- `warnings`
- `blocked_claims`
- `tool_status`
- `validation_errors`
- `safe_execution_events`

Validation:

- Material claims must cite evidence or be marked unsupported/unavailable.
- Raw chain-of-thought, hidden prompts, provider secrets, and raw provider
  payloads must not appear.
- Failed or partial agent execution must preserve safe status for result
  inspection.

## WorkflowSpecification

Machine-readable YAML workflow definition.

Fields:

- `workflow_id`: e.g. `fundamental-analysis`, `technical-analysis`,
  `news-digest`, `risk-review`, `stock-brief`.
- `definition_path`: project-relative YAML definition path.
- `version`: workflow contract version.
- `title`
- `description`
- `workflow_type`: atomic, internal, composite.
- `market_scope`
- `required_inputs`
- `stages`
- `skill_refs`: Markdown agent skills referenced by analysis stages.
- `output_sections`
- `citation_policy`
- `chart_requirements`
- `step_sequence`: ordered step ids for composite workflows.

Validation:

- User-facing workflows must be runnable from the UI.
- Internal steps are not primary catalog cards unless diagnostics are later
  specified.
- Composite workflows reference existing workflow or internal step ids.
- Referenced Markdown agent skills must exist and declare compatible evidence,
  data requirements, and output expectations.
- Workflow YAML must not duplicate detailed dataset requirements owned by
  `SkillDataRequirements`.

## AgentSkill

Governed Markdown instruction document for one analysis capability.

Fields:

- `skill_id`: stable id such as `fundamental-analysis`.
- `skill_path`: project-relative Markdown path using
  `src/finmind_agents/skills/<skill-name>/SKILL.md`.
- `version`
- `purpose`
- `required_context`
- `data_requirements_path`
- `allowed_claims`
- `blocked_behavior`
- `output_contract`
- `citation_policy`
- `safety_rules`

Validation:

- Skills must not declare supported markets or permissions broader than the
  workflow definition and runtime allow.
- Skills with provider-backed data needs must include a valid
  `DATA_REQUIREMENTS.yaml`.
- Skills must instruct unavailable or unsupported output when evidence is stale,
  missing, failed, or blocked by `data-quality-check`.
- Skills are not directly executable by external clients; the guarded runtime
  invokes them through workflow definitions.

## WorkflowStep

Runtime stage within a workflow run.

Fields:

- `step_id`
- `title`
- `kind`: collector, quality_gate, analysis, artifact, risk
- `status`: queued, running, success, partial, failed, unavailable
- `started_at`
- `completed_at`
- `blocking_issues`
- `warnings`
- `output_refs`

Validation:

- Failed/unavailable steps must not silently produce claims.
- Partial composite workflows preserve successful step outputs.

## DatasetQualityReport

Output of `data-quality-check`.

Fields:

- `quality_status`: pass, warn, partial, fail.
- `dataset_statuses`: mapping from dataset id to fresh, stale, missing, failed,
  or partial.
- `blocking_issues`: issues preventing claim categories.
- `warnings`: issues requiring caveats.
- `allowed_claims`: claim categories safe to generate.
- `blocked_claims`: claim categories omitted or marked unavailable.
- `freshness_summary`: user-visible freshness note.
- `evidence_refs`: evidence or record references checked.

Validation:

- Claim-generating steps must inspect `allowed_claims` and `blocked_claims`.
- Quality warnings must be visible in result output.

## ExecutionRun

Workflow run record.

Additional Phase 02 output expectations:

- `sections`: generated result sections with citation ids and status.
- `quality`: dataset quality report.
- `citations`: visible citations.
- `freshness`: per-dataset freshness.
- `artifacts`: charts/tables/computed outputs.
- `visible_execution`: stage statuses, tool/artifact status, warnings, and
  unavailable sections.
- `logs`: internal event summaries without raw reasoning.

State transitions:

```text
queued -> running -> success
queued -> running -> partial
queued -> running -> failed
```

## EvidenceObject / Citation / Artifact

Reuse shared contracts:

- Evidence links claims to source records/documents/artifacts.
- Citations are visible source references for material claims.
- Artifacts are traceable chart/table/computed outputs with accessible fallback
  data.
