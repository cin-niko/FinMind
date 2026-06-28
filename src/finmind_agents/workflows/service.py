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
from finmind_agents.evidence import build_citation, build_evidence
from finmind_agents.models import (
    CanonicalMarketDataRecord,
    ExecutionRun,
    RunStatus,
    utc_now,
)
from finmind_agents.repositories import (
    RunRepository,
    WorkflowRepository,
)
from finmind_agents.workflows.validation import validate_workflow_inputs
from finmind_agents.workflows.collector import (
    collect_workflow_data,
    data_requirements_for_workflow,
    primary_skill_id,
    required_dataset_categories_for_requirements,
)
from finmind_agents.workflows.executor import (
    build_visible_execution,
    build_workflow_sections,
)
from finmind_agents.workflows.quality import (
    build_quality_report,
    serialize_quality_report,
)
from finmind_agents.serialization import serialize_run


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
        collected = collect_workflow_data(
            workflow=workflow,
            dataflows=self.dataflows,
            market=validated_inputs.market,
            symbol=validated_inputs.symbol,
        )
        run_inputs: dict[str, object] = {
            "market": validated_inputs.market.value
        }
        if validated_inputs.symbol:
            run_inputs["symbol"] = validated_inputs.symbol

        evidence = [
            build_evidence(record, workflow.output_sections[0])
            for record in collected.records
        ]
        citations = [
            build_citation(record, evidence_item)
            for record, evidence_item in zip(collected.records, evidence, strict=True)
        ]
        data_requirements = data_requirements_for_workflow(workflow)
        quality = build_quality_report(
            required_datasets=required_dataset_categories_for_requirements(
                data_requirements
            ),
            available_datasets=_available_dataset_categories(
                records=collected.records,
                source_document_count=len(collected.source_documents),
            ),
            evidence=tuple(evidence),
        )
        chart_records = [
            record
            for record in collected.records
            if record.dataset_id.endswith("_prices")
        ]
        chart = (
            build_chart_artifact(workflow.workflow_id, chart_records, evidence)
            if workflow.chart_requirements and chart_records
            else None
        )
        agent_result = self.agent_orchestrator.run_skill(
            AgentRunRequest(
                workflow_id=workflow.workflow_id,
                skill_id=primary_skill_id(workflow),
                skill_markdown=_primary_skill_markdown(workflow.skill_refs),
                data_requirements=data_requirements,
                context={
                    "inputs": run_inputs,
                    "collection": collected.retrieval.to_output(),
                    "retrieval_plan": {
                        "status": collected.retrieval_plan.status.value,
                        "policy_id": collected.retrieval_plan.policy_id,
                        "required_requests": [
                            requirement.dataset
                            for requirement in collected.retrieval_plan.required_requests
                        ],
                        "optional_requests": [
                            requirement.dataset
                            for requirement in collected.retrieval_plan.optional_requests
                        ],
                    },
                    "quality": serialize_quality_report(quality),
                    "records": [
                        {
                            "dataset_id": record.dataset_id,
                            "record_key": record.record_key,
                            "instrument_id": record.instrument_id,
                            "market_time": record.market_time.isoformat(),
                            "source_id": record.source_id,
                            "payload": record.payload,
                            "freshness_status": record.freshness_status.value,
                        }
                        for record in collected.records
                    ],
                },
                evidence_ids=tuple(citation.citation_id for citation in citations),
            )
        )
        started_at = utc_now()
        sections = _apply_agent_result(
            sections=build_workflow_sections(
                workflow=workflow,
                records=collected.records,
                citations=tuple(citations),
                quality=quality,
            ),
            agent_result=agent_result,
        )
        run = ExecutionRun(
            run_id=f"run_{uuid4().hex[:12]}",
            kind="workflow",
            status=RunStatus.PARTIAL if quality.blocking_issues else RunStatus.SUCCESS,
            requested_by=requested_by,
            inputs=run_inputs,
            started_at=started_at,
            completed_at=utc_now(),
            output={
                "sections": sections,
                "agent": {
                    "status": agent_result.status,
                    "runtime_adapter": "langchain_litellm",
                    "policy_id": collected.retrieval_plan.policy_id,
                    "skill_id": primary_skill_id(workflow),
                    "retrieval_plan_status": collected.retrieval_plan.status.value,
                    "tool_status": collected.retrieval.status.value,
                    "allowed_claims": list(agent_result.allowed_claims),
                    "blocked_claims": list(agent_result.blocked_claims),
                    "warnings": list(agent_result.warnings),
                    "validation_errors": [],
                },
                "quality": serialize_quality_report(quality),
                "collection": collected.retrieval.to_output(),
                "citations": [
                    {
                        "citation_id": citation.citation_id,
                        "evidence_id": citation.evidence_id,
                        "label": citation.label,
                        "source_type": citation.source_type,
                        "source_reference": citation.source_reference,
                        "timestamp": citation.timestamp.isoformat(),
                    }
                    for citation in citations
                ],
                "freshness": [
                    {
                        "dataset": record.dataset_id,
                        "status": record.freshness_status.value,
                        "as_of": record.market_time.isoformat(),
                    }
                    for record in collected.records
                ],
                "artifacts": {
                    "chart": {
                        "artifact_id": chart.artifact_id,
                        "artifact_type": chart.artifact_type,
                        "title": chart.title,
                        "inputs": chart.inputs,
                        "payload": chart.payload,
                        "evidence_refs": list(chart.evidence_refs),
                    } if chart is not None else None
                },
                "visible_execution": build_visible_execution(workflow, quality),
            },
            logs=[
                {"event": "workflow_started", "stage": workflow.stages[0]},
                *(
                    [{"event": "artifact_created", "artifact_id": chart.artifact_id}]
                    if chart is not None
                    else []
                ),
                {"event": "workflow_completed", "status": "success"},
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


def _available_dataset_categories(
    records: tuple[CanonicalMarketDataRecord, ...],
    source_document_count: int,
) -> tuple[str, ...]:
    categories: set[str] = set()
    for record in records:
        dataset_id = record.dataset_id
        if dataset_id.endswith("_prices"):
            categories.add("price_series")
        if dataset_id.endswith("_fundamentals"):
            categories.add("fundamentals")
    if source_document_count:
        categories.add("source_documents")
    return tuple(sorted(categories))


def _primary_skill_markdown(skill_refs: tuple[str, ...]) -> str:
    if not skill_refs:
        return ""
    return Path(skill_refs[0]).read_text(encoding="utf-8")


def _apply_agent_result(
    sections: list[dict[str, object]],
    agent_result: AgentRunResult,
) -> list[dict[str, object]]:
    result = []
    replaced = False
    for section in sections:
        if section.get("title") == agent_result.section_title:
            result.append(
                {
                    **section,
                    "status": agent_result.status,
                    "content": agent_result.content,
                    "citations": list(agent_result.citations),
                    "warnings": [
                        *list(section.get("warnings", [])),
                        *list(agent_result.warnings),
                    ],
                }
            )
            replaced = True
        else:
            result.append(section)
    if not replaced:
        result.append(
            {
                "title": agent_result.section_title,
                "status": agent_result.status,
                "content": agent_result.content,
                "citations": list(agent_result.citations),
                "warnings": list(agent_result.warnings),
            }
        )
    return result
