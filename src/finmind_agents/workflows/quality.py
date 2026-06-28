from finmind_agents.models import (
    DatasetQualityReport,
    DatasetStatus,
    EvidenceObject,
    FreshnessStatus,
    QualityStatus,
)


def build_quality_report(
    required_datasets: tuple[str, ...],
    available_datasets: tuple[str, ...],
    evidence: tuple[EvidenceObject, ...],
) -> DatasetQualityReport:
    dataset_statuses: dict[str, DatasetStatus] = {}
    blocking_issues: list[str] = []
    warnings: list[str] = []
    blocked_claims: list[str] = []
    for dataset_id in required_datasets:
        if dataset_id not in available_datasets:
            dataset_statuses[dataset_id] = DatasetStatus.MISSING
            issue = f"{dataset_id}_missing"
            blocking_issues.append(issue)
            warnings.append(issue)
            blocked_claims.append(dataset_id)
            continue
        matching_evidence = [
            item
            for item in evidence
            if _evidence_matches_dataset(dataset_id, item)
        ]
        if dataset_id == "source_documents":
            dataset_statuses[dataset_id] = DatasetStatus.FRESH
            continue
        if not matching_evidence:
            dataset_statuses[dataset_id] = DatasetStatus.MISSING
            warnings.append(f"{dataset_id}_missing")
            blocked_claims.append(dataset_id)
            continue
        if any(item.freshness_status is FreshnessStatus.STALE for item in matching_evidence):
            dataset_statuses[dataset_id] = DatasetStatus.STALE
            warnings.append(f"{dataset_id}_stale")
        else:
            dataset_statuses[dataset_id] = DatasetStatus.FRESH

    quality_status = (
        QualityStatus.PARTIAL
        if blocking_issues
        else QualityStatus.WARN if warnings else QualityStatus.PASS
    )
    return DatasetQualityReport(
        quality_status=quality_status,
        dataset_statuses=dataset_statuses,
        blocking_issues=tuple(blocking_issues),
        warnings=tuple(warnings),
        allowed_claims=("technical_trend", "price_momentum"),
        blocked_claims=tuple(blocked_claims),
        freshness_summary=_freshness_summary(dataset_statuses),
        evidence_refs=tuple(item.evidence_id for item in evidence),
    )


def serialize_quality_report(report: DatasetQualityReport) -> dict[str, object]:
    return {
        "quality_status": report.quality_status.value,
        "dataset_statuses": {
            key: value.value for key, value in report.dataset_statuses.items()
        },
        "blocking_issues": list(report.blocking_issues),
        "warnings": list(report.warnings),
        "allowed_claims": list(report.allowed_claims),
        "blocked_claims": list(report.blocked_claims),
        "freshness_summary": report.freshness_summary,
        "evidence_refs": list(report.evidence_refs),
    }


def _freshness_summary(dataset_statuses: dict[str, DatasetStatus]) -> str:
    if not dataset_statuses:
        return "No datasets checked."
    parts = [
        f"{dataset_id}: {status.value}"
        for dataset_id, status in dataset_statuses.items()
    ]
    return "; ".join(parts)


def _evidence_matches_dataset(dataset_id: str, evidence: EvidenceObject) -> bool:
    if dataset_id == "price_series":
        return "_prices" in evidence.summary
    return dataset_id in evidence.summary
