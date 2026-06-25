from collections.abc import Callable
from typing import Protocol

from api.platform.ingestion.sources import TimeSeriesRecord


class FreshnessJob(Protocol):
    dataset_id: str
    status: str


def calculate_dataset_freshness(
    dataset_ids: list[str],
    list_dataset: Callable[[str], list[TimeSeriesRecord]],
    list_jobs: Callable[[], list[FreshnessJob]],
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    jobs = list_jobs()
    for dataset_id in dataset_ids:
        records = list_dataset(dataset_id)
        failed_latest = next(
            (
                job
                for job in jobs
                if job.dataset_id == dataset_id and job.status == "failed"
            ),
            None,
        )
        if failed_latest is not None:
            status = "failed"
        elif not records:
            status = "missing"
        else:
            status = "fresh"
        entries.append(
            {
                "dataset": dataset_id,
                "status": status,
                "as_of": records[-1].market_time.isoformat() if records else None,
                "record_count": len(records),
            }
        )
    return entries
