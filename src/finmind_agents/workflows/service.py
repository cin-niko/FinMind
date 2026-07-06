from dataclasses import dataclass
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

from finmind_agents.agents.models import (
    AgentOrchestratorProtocol,
    AgentRunRequest,
    AgentRunResult,
)
from finmind_agents.artifacts import build_chart_artifacts
from finmind_agents.dataflows.service import DataflowService
from finmind_agents.runtime.offload import run_sync
from finmind_agents.runtime.service import AgentOrchestratorError
from finmind_agents.streaming.models import (
    StreamEvent,
    StreamEventKind,
    build_stream_event,
)
from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Citation,
    ExecutionRun,
    RunStatus,
    WorkflowSpecification,
    utc_now,
)
from finmind_agents.repositories import (
    RunRepository,
    WorkflowRepository,
)
from finmind_agents.serialization import serialize_run
from finmind_agents.workflows.citations import build_citations
from finmind_agents.workflows.indicators import compute_indicators
from finmind_agents.workflows.collector import (
    collect_workflow_data,
    data_requirements_for_skill,
    primary_skill_id,
    skill_ref_for_id,
)
from finmind_agents.workflows.grounding import GroundingResult, uncited_citations
from finmind_agents.workflows.validation import validate_workflow_inputs

COLLECT_STEP = "collect_data"


@dataclass(frozen=True)
class PreparedWorkflowRun:
    workflow: WorkflowSpecification
    run_inputs: dict[str, object]
    validated_market: object
    validated_symbol: str | None


@dataclass(frozen=True)
class WorkflowService:
    workflows: WorkflowRepository
    dataflows: DataflowService
    agent_orchestrator: AgentOrchestratorProtocol
    runs: RunRepository

    def list_workflows(self) -> list[dict[str, object]]:
        return [
            {
                "id": workflow.workflow_id,
                "title": workflow.title,
                "description": workflow.description,
                "workflow_type": workflow.workflow_type.value,
                "market_scope": [
                    market.value for market in workflow.market_scope
                ],
                "required_inputs": list(workflow.required_inputs),
                "stages": list(workflow.stages),
                "requires_citations": True,
                "chart_requirements": [
                    requirement.to_output()
                    for requirement in workflow.chart_requirements
                ],
                "output_sections": list(workflow.output_sections),
            }
            for workflow in self.workflows.list()
        ]

    async def stream_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, object],
        requested_by: str,
    ) -> AsyncIterator[StreamEvent]:
        prepared = self.prepare_workflow_run(workflow_id, inputs)
        async for event in self._stream_workflow_events(prepared, requested_by):
            yield event

    def prepare_workflow_run(
        self,
        workflow_id: str,
        inputs: dict[str, object],
    ) -> PreparedWorkflowRun:
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            raise KeyError("Workflow not found")
        validated_inputs = validate_workflow_inputs(workflow, inputs)
        run_inputs: dict[str, object] = {"market": validated_inputs.market.value}
        if validated_inputs.symbol:
            run_inputs["symbol"] = validated_inputs.symbol
        return PreparedWorkflowRun(
            workflow=workflow,
            run_inputs=run_inputs,
            validated_market=validated_inputs.market,
            validated_symbol=validated_inputs.symbol,
        )

    async def _stream_workflow_events(
        self,
        prepared: PreparedWorkflowRun,
        requested_by: str,
    ) -> AsyncIterator[StreamEvent]:
        started_at = utc_now()
        run_id = f"run_{uuid4().hex[:12]}"
        sequence = 0
        steps: list[dict[str, object]] = []
        sections: list[dict[str, object]] = []
        grounding_blocked: list[str] = []
        grounding_uncited: list[str] = []

        collected = None
        citations: tuple[Citation, ...] = ()
        records: tuple[CanonicalMarketDataRecord, ...] = ()
        prior_outputs: dict[str, object] = {}
        used_citation_ids: set[str] = set()

        def emit(
            kind: StreamEventKind,
            payload: dict[str, object],
        ) -> StreamEvent:
            nonlocal sequence
            sequence += 1
            return build_stream_event(
                run_id=run_id,
                sequence=sequence,
                kind=kind,
                payload=payload,
            )

        yield emit(
            StreamEventKind.RUN_STARTED,
            {
                "workflow_id": prepared.workflow.workflow_id,
                "inputs": dict(prepared.run_inputs),
            },
        )

        try:
            for step_id in _ordered_steps(prepared.workflow):
                step_kind = "collect_data" if step_id == COLLECT_STEP else "skill"
                yield emit(
                    StreamEventKind.RUN_STAGE,
                    _stage_payload(
                        prepared.workflow,
                        step_id,
                        step_kind,
                        "running",
                    ),
                )
                if step_id == COLLECT_STEP:
                    collected = await run_sync(
                        lambda: collect_workflow_data(
                            workflow=prepared.workflow,
                            dataflows=self.dataflows,
                            market=prepared.validated_market,
                            symbol=prepared.validated_symbol,
                        )
                    )
                    records = collected.records
                    records = _enrich_with_indicators(records, prepared.workflow)
                    citations = build_citations(records)
                    collection_output = collected.collection.to_output()
                    prior_outputs[COLLECT_STEP] = collection_output
                    steps.append(
                        _step(
                            step_id,
                            "collect_data",
                            collected.collection.status.value,
                            list(collected.collection.warnings),
                        )
                    )
                    yield emit(
                        StreamEventKind.RUN_STAGE,
                        _stage_payload(
                            prepared.workflow,
                            step_id,
                            "collect_data",
                            collected.collection.status.value,
                            list(collected.collection.warnings),
                        ),
                    )
                    continue

                skill_id = step_id
                skill_ref = skill_ref_for_id(prepared.workflow, skill_id)
                skill_requirements = data_requirements_for_skill(prepared.workflow, skill_id)

                skill_record_payloads = _skill_record_payloads(skill_id, records)
                skill_citation_ids = tuple(
                    payload["citation_id"]
                    for payload in skill_record_payloads
                    if payload.get("citation_id")
                )
                request = AgentRunRequest(
                    workflow_id=prepared.workflow.workflow_id,
                    skill_id=skill_id,
                    skill_markdown=_skill_markdown(skill_ref),
                    data_requirements=skill_requirements,
                    context={
                        "inputs": prepared.run_inputs,
                        "collection": prior_outputs.get(COLLECT_STEP, {}),
                        "records": skill_record_payloads,
                        "prior_outputs": prior_outputs,
                    },
                    citation_ids=skill_citation_ids,
                )
                yield emit(
                    StreamEventKind.RUN_STAGE,
                    _stage_payload(
                        prepared.workflow,
                        skill_id,
                        "skill",
                        "running",
                        [],
                    ),
                )
                agent_result: AgentRunResult | None = None
                stream_skill = getattr(self.agent_orchestrator, "stream_skill", None)
                if not callable(stream_skill):
                    raise AgentOrchestratorError(
                        f"Agent orchestrator does not support streaming for {skill_id}"
                    )
                async for agent_event in stream_skill(request):
                    if (
                        agent_event.kind == "content_delta"
                        and agent_event.text
                        and _is_visible_output_step(prepared.workflow, skill_id)
                    ):
                        yield emit(
                            StreamEventKind.ANSWER_DELTA,
                            {
                                "section_title": _visible_output_title(
                                    prepared.workflow,
                                    skill_id,
                                ),
                                "text": agent_event.text,
                            },
                        )
                    if agent_event.kind == "result" and agent_event.result is not None:
                        agent_result = agent_event.result
                if agent_result is None:
                    raise AgentOrchestratorError(
                        f"Workflow agent stream completed without a final result for {skill_id}"
                    )
                used_citation_ids.update(skill_citation_ids)
                uncited = uncited_citations(
                    agent_result.citations,
                    tuple(citation.citation_id for citation in citations),
                )
                grounding_uncited.extend(uncited)
                grounding_blocked.extend(agent_result.blocked_claims)
                if _is_visible_output_step(prepared.workflow, skill_id):
                    sections.append(
                        {
                            "title": _visible_output_title(prepared.workflow, skill_id),
                            "status": agent_result.status,
                            "content": agent_result.content,
                            "citations": list(agent_result.citations),
                            "warnings": list(agent_result.warnings),
                            "allowed_claims": list(agent_result.allowed_claims),
                            "blocked_claims": list(agent_result.blocked_claims),
                        }
                    )
                steps.append(
                    _step(skill_id, "skill", agent_result.status, list(agent_result.warnings))
                )
                prior_outputs[skill_id] = agent_result.content
                for citation_id in agent_result.citations:
                    citation = next(
                        (item for item in citations if item.citation_id == citation_id),
                        None,
                    )
                    if citation is not None:
                        yield emit(StreamEventKind.CITATION, _citation_payload(citation))
                yield emit(
                    StreamEventKind.RUN_STAGE,
                    _stage_payload(
                        prepared.workflow,
                        skill_id,
                        "skill",
                        agent_result.status,
                        list(agent_result.warnings),
                    ),
                )

            chart_records = [
                record for record in records if record.dataset_id.endswith("_prices")
            ]
            chart_artifacts = build_chart_artifacts(
                prepared.workflow.workflow_id,
                prepared.workflow.chart_requirements,
                chart_records,
                list(citations),
            )
            chart = chart_artifacts[0] if chart_artifacts else None

            grounding = GroundingResult(
                grounding_status=("blocked" if grounding_uncited else "pass"),
                blocked_claims=tuple(grounding_blocked),
                uncited_claims=tuple(grounding_uncited),
            )

            if chart is not None:
                yield emit(StreamEventKind.ARTIFACT, _chart_payload(chart))

            run = ExecutionRun(
                run_id=run_id,
                kind="workflow",
                status=_run_status(steps),
                requested_by=requested_by,
                inputs=prepared.run_inputs,
                started_at=started_at,
                completed_at=utc_now(),
                output={
                    "sections": sections,
                    "steps": steps,
                    "collection": prior_outputs.get(COLLECT_STEP, {}),
                    "citations": [
                        _citation_payload(citation)
                        for citation in citations
                        if citation.citation_id in used_citation_ids
                    ],
                    "artifacts": [
                        _chart_payload(artifact) for artifact in chart_artifacts
                    ],
                    "grounding": {
                        "grounding_status": grounding.grounding_status,
                        "blocked_claims": list(grounding.blocked_claims),
                        "uncited_claims": list(grounding.uncited_claims),
                    },
                },
                logs=[
                    {
                        "event": "workflow_started",
                        "stage": prepared.workflow.stages[0]
                        if prepared.workflow.stages
                        else COLLECT_STEP,
                    },
                    *(
                        [{"event": "artifact_created", "artifact_id": chart.artifact_id}]
                        if chart is not None
                        else []
                    ),
                    {"event": "workflow_completed", "status": _run_status(steps).value},
                ],
            )
            self.runs.save(run)
            serialized = serialize_run(run)
            yield emit(
                StreamEventKind.RUN_COMPLETED,
                {
                    "status": run.status.value,
                    "completed_steps": len(run.output["steps"]),
                    "run": serialized,
                },
            )
        except Exception as error:
            partial_run = ExecutionRun(
                run_id=run_id,
                kind="workflow",
                status=RunStatus.FAILED,
                requested_by=requested_by,
                inputs=prepared.run_inputs,
                started_at=started_at,
                completed_at=utc_now(),
                output={
                    "sections": sections,
                    "steps": steps,
                    "collection": prior_outputs.get(COLLECT_STEP, {}),
                    "citations": [],
                    "artifacts": [],
                    "grounding": {
                        "grounding_status": "blocked",
                        "blocked_claims": list(grounding_blocked),
                        "uncited_claims": list(grounding_uncited),
                    },
                },
                logs=[{"event": "workflow_failed", "message": str(error)}],
            )
            self.runs.save(partial_run)
            yield emit(
                StreamEventKind.RUN_FAILED,
                {
                    "status": partial_run.status.value,
                    "message": str(error),
                    "run": serialize_run(partial_run),
                },
            )

    def get_run(self, run_id: str) -> dict[str, object] | None:
        run = self.runs.get(run_id)
        if run is None:
            return None
        return serialize_run(run)

    def list_runs(self) -> list[dict[str, object]]:
        return [serialize_run(run) for run in self.runs.list()]

    def delete_run(self, run_id: str) -> bool:
        return self.runs.delete(run_id)

    def rename_run(self, run_id: str, title: str) -> dict[str, object] | None:
        run = self.runs.update_title(run_id, title)
        if run is None:
            return None
        return serialize_run(run)


def _ordered_steps(workflow: WorkflowSpecification) -> tuple[str, ...]:
    if workflow.step_sequence:
        return workflow.step_sequence
    return (COLLECT_STEP, primary_skill_id(workflow))


def _run_status(steps: list[dict[str, object]]) -> RunStatus:
    skill_statuses = [
        step["status"] for step in steps if step["kind"] == "skill"
    ]
    if any(status == "failed" for status in skill_statuses):
        return RunStatus.FAILED
    if any(status in ("unavailable", "partial") for status in skill_statuses):
        return RunStatus.PARTIAL
    return RunStatus.SUCCESS


def _step(
    step_id: str,
    kind: str,
    status: str,
    warnings: list[str],
) -> dict[str, object]:
    return {"id": step_id, "kind": kind, "status": status, "warnings": list(warnings)}


def _section_title_for_skill(
    workflow: WorkflowSpecification,
    skill_id: str,
) -> str:
    skill_steps = [
        step for step in _ordered_steps(workflow) if step != COLLECT_STEP
    ]
    try:
        index = skill_steps.index(skill_id)
    except ValueError:
        index = 0
    if index < len(workflow.output_sections):
        return workflow.output_sections[index]
    return skill_id


def _is_visible_output_step(
    workflow: WorkflowSpecification,
    step_id: str,
) -> bool:
    skill_steps = [step for step in _ordered_steps(workflow) if step != COLLECT_STEP]
    return bool(skill_steps) and step_id == skill_steps[-1]


def _visible_output_title(
    workflow: WorkflowSpecification,
    skill_id: str,
) -> str:
    if workflow.output_sections:
        return workflow.output_sections[-1]
    return _section_title_for_skill(workflow, skill_id)


def _skill_markdown(skill_ref: str | None) -> str:
    if not skill_ref:
        return ""
    return Path(skill_ref).read_text(encoding="utf-8")


def _stage_payload(
    workflow: WorkflowSpecification,
    stage_id: str,
    stage_kind: str,
    status: str,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    return {
        "stage": stage_id,
        "title": _stage_title(workflow, stage_id),
        "kind": stage_kind,
        "status": status,
        "warnings": list(warnings or []),
    }


def _stage_title(workflow: WorkflowSpecification, stage_id: str) -> str:
    if stage_id == COLLECT_STEP:
        return "Collect the data"
    if stage_id.endswith("data-auditor"):
        return "Audit data"
    return _section_title_for_skill(workflow, stage_id)


def _record_payload(record: CanonicalMarketDataRecord) -> dict[str, object]:
    return {
        "citation_id": f"citation_{record.dataset_id}_{record.record_key}",
        "dataset_id": record.dataset_id,
        "record_key": record.record_key,
        "instrument_id": record.instrument_id,
        "market_time": record.market_time.isoformat(),
        "source_id": record.source_id,
        "payload": record.payload,
    }


def _enrich_with_indicators(
    records: tuple[CanonicalMarketDataRecord, ...],
    workflow: WorkflowSpecification,
) -> tuple[CanonicalMarketDataRecord, ...]:
    """Add a computed ``vn_indicators`` record when the workflow needs technical analysis."""
    if not any("technical-analysis" in step for step in workflow.step_sequence):
        return records
    price_record = next(
        (r for r in records if r.dataset_id.endswith("_prices")),
        None,
    )
    if not price_record or not price_record.payload.get("series"):
        return records
    indicator_data = compute_indicators(price_record.payload["series"])
    if not indicator_data:
        return records
    indicator_record = CanonicalMarketDataRecord(
        dataset_id="vn_indicators",
        record_key=f"{price_record.instrument_id}-indicators",
        instrument_id=price_record.instrument_id,
        market_time=price_record.market_time,
        collected_at=price_record.collected_at,
        source_id="computed_indicators",
        payload=indicator_data,
    )
    return (*records, indicator_record)


def _skill_record_payloads(
    skill_id: str,
    records: tuple[CanonicalMarketDataRecord, ...],
) -> list[dict[str, object]]:
    """Build the record context for a skill step.

    Technical-analysis receives computed indicators + company profile (no raw
    price series). Other skills (auditor, fundamental) receive a year-end price
    summary + fundamentals + company profile.
    """
    if skill_id == "vn-technical-analysis":
        return [
            _record_payload(record)
            for record in records
            if record.dataset_id in ("vn_indicators", "vn_company_profile")
        ]
    price_record = next(
        (r for r in records if r.dataset_id.endswith("_prices")),
        None,
    )
    other_records = [
        record
        for record in records
        if not record.dataset_id.endswith("_prices")
        and record.dataset_id != "vn_indicators"
    ]
    payloads = [_record_payload(record) for record in other_records]
    if price_record and price_record.payload.get("series"):
        summary = _year_end_price_summary_payload(price_record)
        if summary:
            payloads.append(summary)
    return payloads


def _year_end_price_summary_payload(
    price_record: CanonicalMarketDataRecord,
) -> dict[str, object] | None:
    """Extract one price bar per calendar year from the series."""
    series = price_record.payload.get("series", [])
    by_year: dict[int, dict[str, object]] = {}
    for bar in series:
        date_str = bar.get("date", "")
        if len(date_str) < 4:
            continue
        year = int(date_str[:4])
        existing = by_year.get(year)
        if existing is None or date_str > existing["date"]:
            by_year[year] = bar
    year_end_bars = sorted(by_year.values(), key=lambda b: b["date"])
    if not year_end_bars:
        return None
    return {
        "citation_id": f"citation_{price_record.dataset_id}_{price_record.record_key}",
        "dataset_id": price_record.dataset_id,
        "record_key": f"{price_record.instrument_id}-year-end",
        "instrument_id": price_record.instrument_id,
        "market_time": price_record.market_time.isoformat(),
        "source_id": price_record.source_id,
        "payload": {
            "year_end_prices": [
                {"date": b["date"], "close": b["close"], "volume": b.get("volume")}
                for b in year_end_bars
            ],
        },
    }


def _citation_payload(citation: Citation) -> dict[str, object]:
    return {
        "citation_id": citation.citation_id,
        "source_id": citation.source_id,
        "dataset_id": citation.dataset_id,
        "label": citation.label,
        "timestamp": citation.timestamp.isoformat(),
    }


def _chart_payload(chart: object) -> dict[str, object]:
    payload = {
        "artifact_id": chart.artifact_id,
        "artifact_type": chart.artifact_type,
        "chart_intent": chart.chart_intent,
        "title": chart.title,
        "inputs": chart.inputs,
        "spec": chart.spec,
        "downloads": list(chart.downloads),
        "source_refs": list(chart.source_refs),
        "status": chart.status,
    }
    if chart.reason is not None:
        payload["reason"] = chart.reason
    return payload
