from api.platform.models import (
    CanonicalMarketDataRecord,
    Citation,
    DatasetQualityReport,
    WorkflowSpecification,
)


def build_workflow_sections(
    workflow: WorkflowSpecification,
    records: tuple[CanonicalMarketDataRecord, ...],
    citations: tuple[Citation, ...],
    quality: DatasetQualityReport,
) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = [
        {
            "title": "Data Quality",
            "status": quality.quality_status.value,
            "content": quality.freshness_summary,
            "citations": [],
            "warnings": list(quality.warnings),
        }
    ]
    for section_title in workflow.output_sections:
        if section_title == "Data Quality":
            continue
        blocked_dataset = _blocked_dataset_for_section(section_title, quality)
        if blocked_dataset:
            sections.append(
                {
                    "title": section_title,
                    "status": "unavailable",
                    "content": (
                        f"{section_title} unavailable because "
                        f"{blocked_dataset} is missing or blocked."
                    ),
                    "citations": [],
                    "warnings": list(quality.warnings),
                }
            )
            continue
        sections.append(
            {
                "title": section_title,
                "status": "success",
                "content": _build_summary(workflow.title, records[0]),
                "citations": [citation.citation_id for citation in citations],
                "warnings": list(quality.warnings),
            }
        )
    return sections


def build_visible_execution(
    workflow: WorkflowSpecification,
    quality: DatasetQualityReport,
) -> dict[str, object]:
    stage_status = "partial" if quality.blocking_issues else "success"
    return {
        "stages": [_visible_stage(stage, stage_status, quality) for stage in workflow.stages],
        "tool_status": "partial" if quality.warnings else "completed",
    }


def _build_summary(title: str, record: CanonicalMarketDataRecord) -> str:
    close = record.payload["close"]
    change = record.payload.get("change_percent")
    return (
        f"{title}: {record.instrument_id} closed at {close} "
        f"with {change}% change."
    )


def _blocked_dataset_for_section(
    section_title: str,
    quality: DatasetQualityReport,
) -> str | None:
    section_requirements = {
        "Fundamentals": "fundamentals",
        "News Digest": "source_documents",
        "Risk Review": "source_documents",
    }
    required_dataset = section_requirements.get(section_title)
    if required_dataset and required_dataset in quality.blocked_claims:
        return required_dataset
    return None


def _visible_stage(
    stage: str,
    stage_status: str,
    quality: DatasetQualityReport,
) -> dict[str, object]:
    if stage == "data-quality-check" and quality.warnings:
        return {
            "id": stage,
            "status": "partial",
            "warnings": list(quality.warnings),
        }
    return {"id": stage, "status": stage_status, "warnings": []}
