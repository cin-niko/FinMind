from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from finmind_agents.agents.models import (
    AgentOrchestratorProtocol,
    AgentRunRequest,
    AgentRunResult,
)
from finmind_agents.artifacts import build_chart_artifact
from finmind_agents.dataflows.service import DataflowService
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
                "chart_requirements": list(workflow.chart_requirements),
                "output_sections": list(workflow.output_sections),
            }
            for workflow in self.workflows.list()
        ]

    def run_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, object],
        requested_by: str,
    ) -> dict[str, object]:
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            raise KeyError("Workflow not found")
        validated_inputs = validate_workflow_inputs(workflow, inputs)
        run_inputs: dict[str, object] = {"market": validated_inputs.market.value}
        if validated_inputs.symbol:
            run_inputs["symbol"] = validated_inputs.symbol

        started_at = utc_now()
        steps: list[dict[str, object]] = []
        sections: list[dict[str, object]] = []
        grounding_blocked: list[str] = []
        grounding_uncited: list[str] = []

        collected = None
        citations: tuple[Citation, ...] = ()
        records: tuple[CanonicalMarketDataRecord, ...] = ()
        prior_outputs: dict[str, object] = {}

        for step_id in _ordered_steps(workflow):
            if step_id == COLLECT_STEP:
                collected = collect_workflow_data(
                    workflow=workflow,
                    dataflows=self.dataflows,
                    market=validated_inputs.market,
                    symbol=validated_inputs.symbol,
                )
                records = collected.records
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
                continue

            skill_id = step_id
            skill_ref = skill_ref_for_id(workflow, skill_id)
            skill_requirements = data_requirements_for_skill(workflow, skill_id)

            skill_record_payloads = _skill_record_payloads(skill_id, records)
            skill_citation_ids = tuple(
                payload["citation_id"]
                for payload in skill_record_payloads
                if payload.get("citation_id")
            )
            agent_result = self.agent_orchestrator.run_skill(
                AgentRunRequest(
                    workflow_id=workflow.workflow_id,
                    skill_id=skill_id,
                    skill_markdown=_skill_markdown(skill_ref),
                    data_requirements=skill_requirements,
                    context={
                        "inputs": run_inputs,
                        "collection": prior_outputs.get(COLLECT_STEP, {}),
                        "records": skill_record_payloads,
                        "prior_outputs": prior_outputs,
                    },
                    citation_ids=skill_citation_ids,
                )
            )
            uncited = uncited_citations(
                agent_result.citations,
                tuple(citation.citation_id for citation in citations),
            )
            grounding_uncited.extend(uncited)
            grounding_blocked.extend(agent_result.blocked_claims)
            sections.append(
                {
                    "title": agent_result.section_title,
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

        chart_records = [
            record for record in records if record.dataset_id.endswith("_prices")
        ]
        chart = (
            build_chart_artifact(workflow.workflow_id, chart_records, list(citations))
            if workflow.chart_requirements and chart_records
            else None
        )

        grounding = GroundingResult(
            grounding_status=(
                "blocked" if grounding_uncited else "pass"
            ),
            blocked_claims=tuple(grounding_blocked),
            uncited_claims=tuple(grounding_uncited),
        )

        run = ExecutionRun(
            run_id=f"run_{uuid4().hex[:12]}",
            kind="workflow",
            status=_run_status(steps),
            requested_by=requested_by,
            inputs=run_inputs,
            started_at=started_at,
            completed_at=utc_now(),
            output={
                "sections": sections,
                "steps": steps,
                "collection": prior_outputs.get(COLLECT_STEP, {}),
                "citations": [_citation_payload(citation) for citation in citations],
                "artifacts": {
                    "chart": _chart_payload(chart) if chart is not None else None,
                },
                "grounding": {
                    "grounding_status": grounding.grounding_status,
                    "blocked_claims": list(grounding.blocked_claims),
                    "uncited_claims": list(grounding.uncited_claims),
                },
            },
            logs=[
                {
                    "event": "workflow_started",
                    "stage": workflow.stages[0] if workflow.stages else COLLECT_STEP,
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
        return serialize_run(run)

    def get_run(self, run_id: str) -> dict[str, object] | None:
        run = self.runs.get(run_id)
        if run is None:
            return None
        return serialize_run(run)

    def list_runs(self) -> list[dict[str, object]]:
        return [serialize_run(run) for run in self.runs.list()]


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


def _skill_markdown(skill_ref: str | None) -> str:
    if not skill_ref:
        return ""
    return Path(skill_ref).read_text(encoding="utf-8")


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


def _skill_record_payloads(
    skill_id: str,
    records: tuple[CanonicalMarketDataRecord, ...],
) -> list[dict[str, object]]:
    """Build the record context for a skill step.

    The technical-analysis skill needs the full OHLCV series. Other skills
    (auditor, fundamental analysis) only need year-end prices, so daily price
    rows are summarized to one per year plus the latest to keep the LLM context
    small. The chart artifact still uses the full series.
    """
    price_records = [r for r in records if r.dataset_id.endswith("_prices")]
    other_records = [r for r in records if not r.dataset_id.endswith("_prices")]
    if skill_id == "vn-technical-analysis":
        return [_record_payload(record) for record in records]
    summary = _price_year_end_summary(price_records)
    return [_record_payload(record) for record in other_records] + [
        _record_payload(record) for record in summary
    ]


def _price_year_end_summary(
    records: list[CanonicalMarketDataRecord],
) -> list[CanonicalMarketDataRecord]:
    """One price record per calendar year (latest in that year) plus the latest."""
    if not records:
        return []
    by_year: dict[int, CanonicalMarketDataRecord] = {}
    latest = records[0]
    for record in records:
        year = record.market_time.year
        existing = by_year.get(year)
        if existing is None or record.market_time > existing.market_time:
            by_year[year] = record
        if record.market_time > latest.market_time:
            latest = record
    summary = list(by_year.values())
    if latest not in summary:
        summary.append(latest)
    summary.sort(key=lambda r: r.market_time)
    return summary


def _citation_payload(citation: Citation) -> dict[str, object]:
    return {
        "citation_id": citation.citation_id,
        "source_id": citation.source_id,
        "dataset_id": citation.dataset_id,
        "label": citation.label,
        "timestamp": citation.timestamp.isoformat(),
    }


def _chart_payload(chart: object) -> dict[str, object]:
    return {
        "artifact_id": chart.artifact_id,
        "artifact_type": chart.artifact_type,
        "title": chart.title,
        "inputs": chart.inputs,
        "payload": chart.payload,
        "source_refs": list(chart.source_refs),
    }
