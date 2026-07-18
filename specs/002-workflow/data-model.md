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
  - docs/adr/ADR-002-direct-async-sse-streaming.md
---

# Data Model: Workflow

This feature uses shared entities from `../system/state-model.md` and defines
Phase 02 workflow-specific usage/extensions below.

## MarketInstrument

Represents a supported equity instrument.

Fields:

- `instrument_id`: stable symbol or index id such as `VCB` or `VNINDEX`.
- `symbol`: user-facing symbol.
- `market`: `VN_STOCK`.
- `display_name`: user-facing label.
- `currency`: quote currency.
- `status`: active, inactive, unsupported.

Validation:

- Phase 02 accepts only `VN_STOCK`.
- Other market and asset types are unsupported.

## CanonicalMarketDataRecord

Normalized market data item used by collection, charts, indicators, and evidence.

Fields:

- `dataset_id`: `vn_prices`, `us_prices`, `vn_fundamentals`,
  `us_fundamentals`, or equivalent bounded demo dataset.
- `record_key`: unique logical key.
- `instrument_id`: linked instrument.
- `market_time`: effective market timestamp.
- `collected_at`: collection timestamp.
- `source_id`: source connector or demo source identity.
- `collection_id`: optional id linking records fetched during the same dataflow
  collection attempt.
- `payload`: normalized values such as close, change percent, volume, EPS, BVPS,
  revenue, profit, valuation ratios, or peer metrics.

Validation:

- `(dataset_id, record_key)` is unique.
- Price records used in technical analysis must include enough points for the
  requested chart/indicator or the chart claim category is blocked.
- Fundamental records used in valuation must include compatible reporting period
  metadata or valuation confidence is blocked/qualified.
- Provider records must preserve market/effective timestamp and collection
  timestamp separately.
- Deterministic records used by tests are not available to product collection.

## DataRecord

Deterministic LLM-facing record produced after collection and normalization.
`CanonicalMarketDataRecord` remains the provider-normalized source layer;
`DataRecord` is the compact analysis layer used for citations and prompt
context.

Fields:

- `record_id`: deterministic id built from `record_type`, market, symbol, period,
  source ids, and `methodology_version`.
- `record_type`: one of `price_summary_record`, `indicator_record`,
  `pattern_evidence_record`, `pattern_setup_record`, `company_profile_record`,
  or `fundamental_record`.
- `market`: `VN_STOCK`.
- `symbol`
- `period`: date, reporting period, or lookback window represented.
- `source_record_ids`: canonical market data record ids used to produce this
  record.
- `citation_source_ids`: source ids that can be exposed through citations.
- `payload`: compact deterministic facts sent to the LLM when selected for the
  data bundle.
- `context`: deterministic rendered content derived from the record fields for
  LLM input and human-readable display.
- `allowed_claims`
- `blocked_claims`
- `warnings`
- `methodology_version`
- `created_at`

Validation:

- Data record generation must be deterministic for the same source records
  and methodology version.
- Raw provider payloads must not be stored inside `payload`.
- `payload` remains the canonical representation; `context` is a deterministic
  rendered projection.
- The default rendering contract is a class-owned template-backed `context`
  property. Subclasses may override the rendering logic for custom display
  needs.
- Records must be reusable across runs only when market, symbol, period,
  source ids, and methodology version match.
- Phase 02 does not define `news_record`, `risk_record`, or
  `fundamental_flags_record`.

## PatternEvidenceRecord

Specialized `DataRecord` with `record_type=pattern_evidence_record`.

Purpose:

- Store strict technical-pattern verdicts that can be claimed directly because
  the evidence rule was satisfied.
- Replace raw price-series prompting for common pattern checks.
- Feed the LLM a compact verdict table plus evidence points instead of full
  candles.

Inputs:

- `price_series_record`
- `indicator_record` when a detector needs RSI or similar confirmation

Fields:

- All `DataRecord` fields.
- `detected_patterns`: ordered list of strict evidence verdicts.
- `lookback_window`: window used for the scan, such as `6mo_daily`.

Each `detected_patterns[]` item contains:

- `pattern_id`: stable detector id such as `double_bottom`,
  `descending_channel`, `bullish_rsi_divergence`.
- `pattern_name`: human-readable label.
- `direction`: bullish, bearish, or neutral.
- `verdict`: `detected` or `not_detected`.
- `strength`: optional compact strength label when the detector provides one.
- `evidence_points`: compact numeric facts used by the verdict, such as swing
  lows, neckline, slope, or RSI comparison.
- `confirmation_level`: optional price level used to confirm or invalidate the
  pattern.
- `reader_note`: deterministic short explanation of why the verdict was given.

Validation:

- This record is built from strict detectors only; it must not include
  speculative or forming setups.
- Phase 02 ports the bounded detectors documented in
  `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md`.
- Initial detector scope is:
  `double_bottom_top`, `ascending_descending_channel`,
  `candlestick_patterns`, and `rsi_divergence`.

## PatternSetupRecord

Specialized `DataRecord` with `record_type=pattern_setup_record`.

Purpose:

- Store heuristic bullish setup candidates that are still forming or waiting
  for confirmation.
- Give the LLM a ranked setup table without exposing the full price series.

Inputs:

- `price_series_record`
- `indicator_record` when setup scoring needs derived context

Fields:

- All `DataRecord` fields.
- `setups`: ranked list of setup candidates that passed the minimum score.
- `lookback_window`: window used for the scan, such as `6mo_daily`.
- `archetype`: optional stock-behavior summary derived from the surviving
  setups.

Each `setups[]` item contains:

- `pattern_id`
- `pattern_name`
- `family`: compact classification such as `trend_following` or
  `accumulation_breakout`.
- `setup_status`: compact readiness label derived from score and distance to
  confirmation.
- `completion_score`: bounded deterministic score.
- `confirmation_price`
- `watch_zone`: object with `low` and `high`.
- `current_price`
- `distance_to_confirmation_pct`
- `reader_note`: deterministic explanation.

Validation:

- This record contains heuristic setup candidates, not hard evidence verdicts.
- Phase 02 ports the bounded setup-scoring logic documented in
  `equity-research-vn/vn-technical-analysis/references/pattern_scoring.md`.
- Initial setup scope is the documented 8 bullish setup heuristics:
  `bull_flags`, `bull_pennants`, `triangles_ascending`, `wedges_falling`,
  `cup_with_handle`, `rectangle_bottoms`, `double_bottoms`, and
  `measured_move_up`.
- Only setups meeting the configured score threshold are stored.

## FundamentalRecord

Specialized `DataRecord` with `record_type=fundamental_record`.

Fields:

- All `DataRecord` fields.
- `metrics`: normalized financial/fundamental metrics by period.
- `is_audited`: boolean; true only after deterministic audit/refinement
  completes.
- `audit_warnings`: unit, period, split/share-count, EPS/BVPS, source coverage,
  or consistency warnings.
- `data_quality_risk`: compact quality label or code derived by the audit step.

Validation:

- Confident fundamental claims require `is_audited=true`.
- If audit cannot complete, keep `is_audited=false`, populate warnings and
  blocked claims, and mark unsupported claim categories unavailable.
- Audit flags are embedded in `fundamental_record`; there is no separate
  `fundamental_flags_record`.

## PriceSeriesRecord

Stored price series used for chart rendering, downloads, reuse, and future
internal data-platform needs.

Fields:

- `record_id`
- `market`
- `symbol`
- `period`
- `source_record_ids`
- `series_payload`: OHLCV or close/volume series needed by chart renderers.
- `methodology_version`
- `created_at`

Validation:

- This record is not normally included in the LLM data bundle.
- Chart artifacts may link to this record through `source_refs` or download
  metadata.

## DataBundle

Runtime-selected compact package sent to the LLM.

Fields:

- `bundle_id`
- `run_id`
- `record_ids`: selected LLM-visible data records.
- `citation_ids`: citation allowlist generated from selected records.
- `excluded_record_ids`: records available to runtime but intentionally omitted,
  such as full price series.
- `methodology_versions`: calculation/audit versions included in the bundle.
- `created_at`

Validation:

- The bundle must include only records safe for model context.
- The bundle may use each selected record's rendered `context` as the compact
  LLM-visible form, while retaining structured record fields in memory for
  validation and citation extraction.
- The bundle must include citation ids before the model call.
- The LLM may cite only ids in `citation_ids`.

## Citation

Citation generated by the LLM from allowed data records and validated by runtime
grounding rules. Persistence is implementation detail, not a separate product
concept.

Fields:

- `citation_id`
- `run_id`
- `record_id`
- `record_type`
- `source_id`
- `dataset_id`
- `label`
- `timestamp`
- `cited_fields`: optional payload fields or paths this citation supports.
- `display_content`: optional rendered snippet or markdown derived from the
  cited record for UI display.
- `created_at`

Validation:

- `(run_id, citation_id)` is unique.
- `record_id` must point to an existing data record selected for the run's
  data bundle.
- Citation ids must be generated before the LLM call and supplied as an
  allowlist.
- Stored citations should include enough structured snapshot data and display
  content to support UI inspection even when the intermediate `DataRecord` is
  not persisted durably.
- Citations are not artifacts and must not point directly to raw provider
  payloads.

## DataflowCollectionRequest

Input contract for retrieving evidence-ready finance data.

Fields:

- `market`: `VN_STOCK`.
- `symbol`
- `dataset_groups`: `market_price`, `fundamental`.
- `lookback`: optional period/window for price history.
- `requested_by`: workflow id or future chatflow request id.

Validation:

- Dataset groups must be requested through an agent collection plan derived from
  skill-owned `DATA_REQUIREMENTS.yaml` or future chatflow collection needs.
- Unsupported markets or symbols are rejected before provider calls.
- Product collection must not substitute deterministic fixture data after a
  provider failure.

## DataflowCollectionResult

Output contract returned by `DataflowService.collect(...)`.

Fields:

- `collection_id`
- `market`: `VN_STOCK`.
- `symbol`
- `requested_dataset_groups`: `market_price`, `fundamental`.
- `provider_results`: provider status records.
- `records`: canonical market data records.
- `source_documents`: reserved for future source-document contracts; not used
  for Phase 02 standalone news records.
- `started_at`
- `completed_at`
- `status`: success, partial, or failed.
- `warnings`
- `failure_reasons`
- `records_collected`
- `documents_collected`

Validation:

- Provider failures, missing API keys, timeouts, rate limits, and unsupported
  symbols must be represented in `warnings` or `failure_reasons`.
- Failed collection must preserve safe provider warnings or failure reasons for
  user-visible unavailable states.
- Raw provider payloads and secrets must not be returned.

## DataflowProviderResult

Status for one provider attempt within a collection.

Fields:

- `provider_id`: e.g. `vnstock`.
- `dataset_groups`
- `status`: success, partial, failed, or skipped.
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

Reserved trusted source material for future source-document workflows and
fundamental source verification. Phase 02 does not define `news_record` or a
standalone news digest contract.

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
- `sentiment_hint` when available in a future source contract

Validation:

- Missing documents block current-news, catalyst, and event-impact claims.
- Source excerpts must respect source constraints.

## WorkflowStreamDisplayState

Display-ready workflow execution state used by transcript-style workflow
responses.

Fields:

- `summary_label`: `Working` while execution is incomplete, `Completed N steps`
  when complete.
- `is_complete`
- `default_expanded`
- `steps`: ordered display steps.

Validation:

- Incomplete workflow-backed assistant responses default to expanded execution
  visibility.
- Completed workflow-backed assistant responses default to collapsed execution
  visibility but remain user-expandable.
- The display state must show safe execution metadata only and must not expose
  raw reasoning, hidden prompts, or unsafe diagnostics.

## WorkflowDisplayStep

User-visible execution step in transcript-style workflow responses.

Fields:

- `step_id`
- `display_label`: product-facing main label.
- `step_type`: collection, audit, analysis, summary, or equivalent bounded step
  family.
- `status`
- `input_context`: optional secondary subtext such as symbol or symbol plus
  period.

Validation:

- `display_label` must not expose raw internal workflow or skill ids directly.
- `input_context` is optional and omitted when unavailable.
- Completed visible step lists append a terminal `Done` row after workflow
  steps.

## FinMindAgentRuntime

Shared runtime boundary for workflow agents in Phase 02 and a future separately
specified chatflow.

Fields:

- `runtime_id`: stable runtime identity.
- `adapter`: runtime adapter such as `langchain_openai` (OpenAI-compatible
  endpoints), `langchain_litellm` (provider-routed models), `langchain_agent`,
  or another approved adapter.
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

- `policy_id`: e.g. `workflow_strict`.
- `mode`: workflow for Phase 02; chatflow is not currently specified.
- `allowed_tools`: tool ids the agent may call.
- `allowed_skills`: skill ids the agent may load.
- `allowed_markets`: `VN_STOCK` for Phase 02.
- `allowed_dataset_groups`: dataset groups the policy permits.
- `allow_optional_collection`: whether optional skill data may be requested.
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
- A future chatflow policy may be broader but still must require data-driven,
  citation-backed answers.
- Policies must block unsupported assets and irreversible financial actions.
- Phase 02 model/provider adapters must support streaming through
  LangChain/LiteLLM; unsupported streaming capability fails closed during runtime
  configuration instead of selecting a weaker policy.

## AgentTool

Tool made available to the shared agent runtime.

Fields:

- `tool_id`: stable id such as `collect_dataflow`, `load_skill`,
  `validate_finmind_output`, or future approved tools.
- `description`
- `input_schema`
- `output_schema`
- `allowed_policy_ids`
- `side_effect_profile`: read_only, write_run_state, or forbidden.
- `audit_visibility`: what safe status can appear in logs/UI.

Validation:

- Provider access must go through `collect_dataflow`; tools must not expose raw
  provider clients directly.
- `collect_dataflow` must validate requests against the workflow policy,
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
- `dataset_group`: `market_price`, `fundamental`, or approved future
  groups.
- `fields`
- `lookback`
- `periods`

Validation:

- Required data requirements must be attempted during workflow runs.
- Optional data requirements may be skipped only with visible warnings or
  unavailable sections when they affect user-facing claims.
- Market scope cannot exceed the workflow YAML market scope or runtime policy.
- Provider names are implementation hints only when needed; skills must request
  data through dataset contracts, not direct provider APIs.

## AgentCollectionPlan

Concrete collection plan derived by the agent/runtime after reading an Agent Skill
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

- `sub_agent_id`: e.g. `vn_market_data_agent`, `fundamental_data_agent`, or
  `technical_data_agent`.
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
- `collection_plan`: proposed or approved `AgentCollectionPlan`.
- `collection_results`: populated after validated `collect_dataflow` calls.
- `data_bundle`: deterministic `DataBundle` produced before the LLM
  call.
- `citation_ids`: citation ids from the data bundle allowlist.
- `prior_outputs`: outputs of earlier steps in the `step_sequence`.
- `output_schema`
- `policy_id`

Validation:

- `market`, `symbol`, and `skill_id` must be compatible with the workflow YAML
  definition.
- `data_requirements` must be loaded from the referenced skill, not duplicated
  from workflow YAML.
- Workflow skill steps run after the `collect_data` step; an upstream-dependent
  skill step runs after the skill it depends on. Claim-generating synthesis must
  wait until the required collected records or upstream skill output are available.
- Runtime must derive and package data records before calling the LLM; skills
  consume `data_bundle`, not raw provider payloads.
- Missing required LLM configuration blocks execution instead of producing
  deterministic prose disguised as analysis.
- Request execution must be async. Any unavoidable sync tool/provider/model call
  must run through a bounded offload wrapper, not directly on the event loop.

## Chatflow Models

Phase 02 does not own chatflow request, conversation, message, or persistence
models. No active production-chatflow feature spec exists.

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
- `allowed_claims`
- `safe_execution_events`

Validation:

- Material claims must cite evidence or be marked unsupported/unavailable.
- Raw chain-of-thought, hidden prompts, provider secrets, and raw provider
  payloads must not appear.
- Failed or partial agent execution must preserve safe status for result
  inspection.
- Streamed deltas must reconcile to the final stored result.

## WorkflowSpecification

Machine-readable YAML workflow definition.

Fields:

- `workflow_id`: e.g. `fundamental-analysis`, `technical-analysis`,
  `stock-brief`.
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

- `skill_id`: stable id such as `vn-financial-data-auditor`,
  `vn-fundamental-analysis`, `vn-technical-analysis`.
- `skill_path`: project-relative Markdown path using
  `src/finmind_agents/workflows/skills/<skill-name>/SKILL.md`.
- `version`
- `purpose`
- `required_context`
- `data_requirements_path`: present only for skills that consume raw collected
  records.
- `allowed_claims`
- `blocked_behavior`
- `output_contract`
- `citation_policy`
- `safety_rules`

Input kinds:

- Raw-data skills include `DATA_REQUIREMENTS.yaml` and consume collected records
  directly (e.g. `vn-financial-data-auditor`, `vn-technical-analysis`).
- Upstream-dependent skills consume a prior skill's output instead of raw
  records; they state the required upstream skill and expected output schema in
  `SKILL.md` prose (e.g. `vn-fundamental-analysis` requires the
  `vn-financial-data-auditor` data package). They do not declare
  `DATA_REQUIREMENTS.yaml` and do not add to `collect_data`'s fetch list.

Validation:

- Skills never fetch data directly; `collect_data` owns collection.
- Skills must not declare supported markets or permissions broader than the
  workflow definition and runtime allow.
- Skills must instruct unavailable or blocked output when required data is
  missing, stale, or blocked by the grounding check.
- Skills are not directly executable by external clients; the guarded runtime
  invokes them through workflow definitions.

## WorkflowStep

Runtime stage within a workflow run.

Fields:

- `step_id`
- `title`
- `kind`: collector, quality_gate, analysis, artifact
- `status`: running, success, partial, failed, unavailable
- `started_at`
- `completed_at`
- `blocking_issues`
- `warnings`
- `output_refs`
- `stream_sequence_start`
- `stream_sequence_end`

Validation:

- Failed/unavailable steps must not silently produce claims.
- Partial composite workflows preserve successful step outputs.
- Step status changes must emit safe `StreamEvent` frames on the active SSE
  response.

## GroundingCheck

Deterministic post-skill audit. The skill is the judge of completeness: it runs
on the data `collect_data` returned and resolves which claims it can support,
reporting `blocked_claims` for categories it cannot ground. This check audits
the skill's output, it does not pre-block the skill.

Checks:

- Cited citation ids must be a subset of the data bundle citation allowlist.
- Cited records must be derived from sources returned by `collect_data`.
- Any agent-cited citation id not in the data bundle citation allowlist is an
  `uncited_claim` (a hallucinated or unavailable source).

Output:

- `grounding_status`: `pass` or `blocked`. `blocked` when `uncited_claims` is
  non-empty.
- `blocked_claims`: claim categories the skill reported as blocked (surfaced for
  transparency; the skill responsibly withheld them).
- `uncited_claims`: claims referencing sources not returned by `collect_data`
  (a grounding violation).

Validation:

- There is no pre-agent fail-fast gate and no competing quality gate. Run status
  is derived from skill step statuses (`failed` -> FAILED; `partial` ->
  PARTIAL; else SUCCESS); the skill decides `partial` vs `success`.
- `collect_data` is the only hard floor: if it returns no records and no source
  documents, the run fails before any skill step.
- Grounding outcomes must be visible in result output.

## ExecutionRun

Workflow run record.

Base fields:

- `run_id`
- `kind`: workflow for Phase 02; a future bounded feature may define chatflow use of the shared run
  model.
- `owner_user_id`
- `conversation_id`: optional for chat-linked workflow output.
- `status`: running, success, partial, or failed.
- `created_at`
- `started_at`
- `completed_at`
- `last_stream_sequence`
- `failure_reason`: safe user-visible reason when failed.

Additional Phase 02 output expectations:

- `sections`: generated result sections with citation ids, status, allowed
  claims, and blocked claims.
- `steps`: ordered `step_sequence` execution trace (`collect_data` and skill
  steps with status and warnings).
- `collection`: `DataflowCollectionResult` output from the `collect_data` step.
- `data_records`: deterministic records selected or produced for the run.
- `data_bundle`: compact model-visible evidence package.
- `citations`: visible persisted citation records (record id, source id, dataset
  id, timestamp).
- `artifacts`: charts/tables/computed outputs with `source_refs`.
- `grounding`: post-skill grounding check (`grounding_status`, `blocked_claims`,
  `uncited_claims`).
- `logs`: internal event summaries without raw reasoning.

State transitions:

```text
running -> success
running -> partial
running -> failed
```

Validation:

- Run ownership is scoped to the authenticated user/session.
- Streaming submission creates the run context when the request starts and
  persists the final run output before the stream closes when possible.
- Active request-scoped streams are not resumable after server restart; only
  completed/persisted final runs are inspectable.
- Final run output is the source of truth for result reinspection.
- Citation inspection may fetch persisted citation records independently, but
  run output must still carry enough citation metadata for backward-compatible
  result rendering.

## StreamEvent

Ordered, safe event emitted on the active Phase 02 workflow SSE response.

Fields:

- `event_id`: optional stable frame id for client-side ordering.
- `run_id`
- `sequence`: monotonically increasing integer scoped to one streaming response.
- `kind`: response_started, stage_status, warning, citation, artifact,
  output_delta, final_output, completed, failed, heartbeat.
- `created_at`
- `payload`: safe JSON payload.
- `visible`: whether the event can be shown directly in UI.

Validation:

- `(run_id, sequence)` is unique within the streaming response.
- Payloads must not contain raw reasoning, hidden prompts, provider secrets, raw
  provider payloads, or unsafe diagnostics.
- Output deltas must be reconcilable with `ExecutionRun` final output.
- Stream events are not a background queue and are not required to be replayable
  after disconnect.

## StreamingRequestContext

Transient request-scoped context for one Phase 02 workflow streaming response.

Fields:

- `request_id`
- `run_id`
- `owner_user_id`
- `kind`: workflow.
- `connected_at`
- `transport`: sse for Phase 02.
- `heartbeat_interval_seconds`
- `global_concurrency_limit`
- `per_user_concurrency_limit`
- `sync_offload_limit`
- `limiter_backend`: process_local for Phase 02; redis or equivalent later.

Validation:

- The request must be authenticated and authorized for the run context.
- Client disconnect cancels the request-scoped stream cooperatively where
  possible; completed partial/final output already persisted remains inspectable.
- Global and per-user stream limits apply before provider/model execution.
- Sync-offload limits apply before unavoidable synchronous provider/model/library
  calls are offloaded.
- Phase 02 concurrency limits are process-local semaphores configured by
  `FINMIND_STREAM_GLOBAL_LIMIT`, `FINMIND_STREAM_PER_USER_LIMIT`,
  `FINMIND_SYNC_OFFLOAD_LIMIT`.
- Provider/model-specific limit buckets are deferred until real usage or
  multi-worker deployment requires them.
- Single-process request-scoped streaming is acceptable for Phase 02; durable
  background jobs or replayable event queues require a later explicit spec.

## Citation / Artifact

- `Citation`: visible source reference for a material claim — `record_id`,
  `source_id`, timestamp, and `dataset_id`. Citations derive from deterministic
  data records, not raw provider payloads.
- `Artifact`: parent model for generated outputs users can open or download.
- `FileArtifact`: physical asset with `artifact_type=file`, `file_type`,
  `mime_type`, filename, status, download metadata, and source references.
- `ChartArtifact`: structured chart output with `artifact_type=chart`, chart
  intent, supported views, default view, renderable chart spec, download
  metadata, status, and source references.
- `RightPanelDisplayState`: client inspection state with artifact-viewer mode and
  citation-list mode.

Rules:

- Citations are not artifacts.
- Citations are persisted pointers to data records.
- Artifact cards open full artifact viewers.
- Inline citation chips open the full source list and jump to the clicked
  source.
- Chart artifacts do not require a price table in the main answer; raw data
  access uses downloads or a separate file artifact when needed.

## Run Model

A workflow run executes its `step_sequence` in order. Each step is either
deterministic or an agent skill step, and each step's output threads forward as
context for later steps.

Step kinds:

- `collect_data`: deterministic collection phase. Reads the raw
  `DATA_REQUIREMENTS.yaml` declared by the skill steps in the same workflow
  (union, not duplicated at the workflow level) and fulfills each requirement
  with one or more concrete collect tools selected by market, provider, and
  dataset type (for example `collect_vnstock_fundamental_data`,
  `collect_vn_balance_sheet`). Skills stay provider-agnostic: they
  declare dataset contracts, never tool or provider names. Each tool returns
  canonical records carrying `dataset_id`, `source_id`, and `market_time`.
  Collection is the only source of ground truth; skill steps never fetch
  directly. In workflow mode, tool selection is config-driven: a
  mapping from market and dataset type to a concrete tool. Provider substitution
  on failure is not implemented; a failed tool yields a
  missing dataset. Agent-driven tool selection in chatflow mode requires a
  future bounded feature.
- `build_data_bundle`: deterministic packaging phase. Converts collected
  canonical records and prior deterministic outputs into data records,
  assigns citation ids, persists records/citations, and selects the compact
  model-visible bundle.
- `skill`: agent. Receives the data bundle plus prior step outputs, writes
  its output section, cites only allowed citation ids, and declares
  `allowed_claims`/`blocked_claims`.

Guardrails:

- There is no pre-skill fail-fast gate. A skill step runs on whatever
  `collect_data` returned and resolves which claims it can support, reporting
  `blocked_claims` for categories it cannot ground on the available data.
- After each skill step, a deterministic grounding check verifies cited ids are a
  subset of the data bundle citation allowlist; agent-cited ids outside the
  allowlist become `uncited_claims` and force `grounding_status` to `blocked`.
- `collect_data` is the only hard floor: zero records and zero source documents
  fails the run before any skill step.
- Citations are record-backed source references: a citation references an
  data record plus source metadata (`record_id`, `source_id`, timestamp,
  `dataset_id`), not a tool-call graph or raw provider payload. Data age is
  conveyed by the citation `timestamp`; there is no separate freshness-status
  concept.

Example step sequences:

- `vn-financial-data-collector`: `collect_data` -> `vn-financial-data-auditor`.
- `vn-fundamental-analysis`: `collect_data` -> `vn-financial-data-auditor` ->
  `vn-fundamental-analysis`.
- `vn-technical-analysis`: `collect_data` -> `vn-technical-analysis`.
