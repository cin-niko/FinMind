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
from api.platform.workflows.validation import (
    WorkflowValidationError,
    validate_workflow_inputs,
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
                "market_scope": [
                    market.value for market in workflow.market_scope
                ],
                "required_inputs": list(workflow.required_inputs),
                "stages": list(workflow.stages),
                "requires_citations": True,
                "chart_requirements": list(workflow.chart_requirements),
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
        records = self.market_data.list_by_market(validated_inputs.market)
        if validated_inputs.symbol:
            records = [
                record
                for record in records
                if record.instrument_id == validated_inputs.symbol
            ]
        if not records:
            raise WorkflowValidationError("Required market data is missing")
        run_inputs: dict[str, object] = {
            "market": validated_inputs.market.value
        }
        if validated_inputs.symbol:
            run_inputs["symbol"] = validated_inputs.symbol

        evidence = [
            build_evidence(record, workflow.output_sections[0])
            for record in records
        ]
        citations = [
            build_citation(record, evidence_item)
            for record, evidence_item in zip(records, evidence, strict=True)
        ]
        chart = build_chart_artifact(workflow.workflow_id, records, evidence)
        started_at = utc_now()
        run = ExecutionRun(
            run_id=f"run_{uuid4().hex[:12]}",
            kind="workflow",
            status=RunStatus.SUCCESS,
            requested_by=requested_by,
            inputs=run_inputs,
            started_at=started_at,
            completed_at=utc_now(),
            output={
                "sections": [
                    {
                        "title": workflow.output_sections[0],
                        "content": _build_summary(workflow.title, records[0]),
                        "citations": [
                            citation.citation_id for citation in citations
                        ],
                    }
                ],
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
                    for record in records
                ],
                "artifacts": {
                    "chart": {
                        "artifact_id": chart.artifact_id,
                        "artifact_type": chart.artifact_type,
                        "title": chart.title,
                        "inputs": chart.inputs,
                        "payload": chart.payload,
                        "evidence_refs": list(chart.evidence_refs),
                    }
                },
                "visible_execution": {
                    "stages": list(workflow.stages),
                    "tool_status": "completed",
                },
            },
            logs=[
                {"event": "workflow_started", "stage": workflow.stages[0]},
                {
                    "event": "artifact_created",
                    "artifact_id": chart.artifact_id,
                },
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


def _build_summary(title: str, record: CanonicalMarketDataRecord) -> str:
    close = record.payload["close"]
    change = record.payload.get("change_percent")
    return (
        f"{title}: {record.instrument_id} closed at {close} "
        f"with {change}% change."
    )
