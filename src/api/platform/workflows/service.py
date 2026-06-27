from dataclasses import dataclass
from uuid import uuid4

from api.platform.artifacts import build_chart_artifact
from api.platform.evidence import build_citation, build_evidence
from api.platform.models import (
    CanonicalMarketDataRecord,
    ExecutionRun,
    RunStatus,
    utc_now,
)
from api.platform.repositories import (
    MarketDataRepository,
    RunRepository,
    WorkflowRepository,
)
from api.platform.workflows.validation import validate_workflow_inputs
from api.platform.workflows.collector import collect_workflow_data
from api.platform.workflows.executor import (
    build_visible_execution,
    build_workflow_sections,
)
from api.platform.workflows.quality import (
    build_quality_report,
    serialize_quality_report,
)
from api.schemas import serialize_run


@dataclass(frozen=True)
class WorkflowService:
    workflows: WorkflowRepository
    market_data: MarketDataRepository
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
            market_data=self.market_data,
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
        quality = build_quality_report(
            required_datasets=workflow.required_datasets,
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
        started_at = utc_now()
        run = ExecutionRun(
            run_id=f"run_{uuid4().hex[:12]}",
            kind="workflow",
            status=RunStatus.PARTIAL if quality.blocking_issues else RunStatus.SUCCESS,
            requested_by=requested_by,
            inputs=run_inputs,
            started_at=started_at,
            completed_at=utc_now(),
            output={
                "sections": build_workflow_sections(
                    workflow=workflow,
                    records=collected.records,
                    citations=tuple(citations),
                    quality=quality,
                ),
                "quality": serialize_quality_report(quality),
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
