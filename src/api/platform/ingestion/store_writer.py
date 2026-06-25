from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from api.platform.ingestion.sources import TimeSeriesRecord
from api.platform.freshness import (
    active_freshness_dataset_ids,
    calculate_dataset_freshness,
)


@dataclass(frozen=True)
class IngestionJobRecord:
    job_id: str
    source_id: str
    dataset_id: str
    period: str
    trigger: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    record_count: int
    diagnostics: dict[str, object]


class TimeSeriesStore(Protocol):
    def upsert_many(self, records: list[TimeSeriesRecord]) -> int: ...

    def list_dataset(self, dataset_id: str) -> list[TimeSeriesRecord]: ...

    def list_jobs(self) -> list[IngestionJobRecord]: ...

    def has_active_job(self, source_id: str, period: str) -> bool: ...

    def has_dataset_rows(
        self, dataset_id: str, instrument_id: str
    ) -> bool: ...

    def is_in_collection(
        self, collection_id: str, instrument_id: str
    ) -> bool: ...

    def create_running_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
    ) -> IngestionJobRecord: ...

    def save_completed_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
        status: str,
        record_count: int,
        diagnostics: dict[str, object],
    ) -> IngestionJobRecord: ...

    def freshness(self) -> list[dict[str, object]]: ...


@dataclass
class InMemoryTimeSeriesStore:
    records: dict[tuple[str, str], TimeSeriesRecord] = field(default_factory=dict)
    jobs: list[IngestionJobRecord] = field(default_factory=list)
    collection_memberships: set[tuple[str, str]] = field(
        default_factory=set
    )
    roadmap_markets_enabled: bool = False
    _next_job_id: int = 1

    def upsert_many(self, records: list[TimeSeriesRecord]) -> int:
        for record in records:
            self.records[(record.dataset_id, record.record_key)] = record
        return len(records)

    def list_dataset(self, dataset_id: str) -> list[TimeSeriesRecord]:
        return sorted(
            [
                record
                for (record_dataset, _record_key), record in self.records.items()
                if record_dataset == dataset_id
            ],
            key=lambda record: record.market_time,
        )

    def list_jobs(self) -> list[IngestionJobRecord]:
        return sorted(self.jobs, key=lambda job: job.started_at, reverse=True)

    def has_active_job(self, source_id: str, period: str) -> bool:
        return any(
            job.source_id == source_id
            and job.period == period
            and job.status in {"queued", "running"}
            for job in self.jobs
        )

    def has_dataset_rows(
        self, dataset_id: str, instrument_id: str
    ) -> bool:
        return any(
            record_dataset == dataset_id
            and record.instrument_id == instrument_id
            for (record_dataset, _record_key), record in self.records.items()
        )

    def is_in_collection(
        self, collection_id: str, instrument_id: str
    ) -> bool:
        return (collection_id, instrument_id) in self.collection_memberships

    def create_running_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
    ) -> IngestionJobRecord:
        job = self._new_job(
            source_id=source_id,
            period=period,
            trigger=trigger,
            status="running",
            completed_at=None,
            record_count=0,
            diagnostics={},
        )
        self.jobs.append(job)
        return job

    def save_completed_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
        status: str,
        record_count: int,
        diagnostics: dict[str, object],
    ) -> IngestionJobRecord:
        started_at = datetime.now(UTC)
        job = IngestionJobRecord(
            job_id=self._allocate_job_id(),
            source_id=source_id,
            dataset_id=source_id,
            period=period,
            trigger=trigger,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            record_count=record_count,
            diagnostics=diagnostics,
        )
        self.jobs.append(job)
        return job

    def freshness(self) -> list[dict[str, object]]:
        return calculate_dataset_freshness(
            dataset_ids=active_freshness_dataset_ids(
                self.roadmap_markets_enabled
            ),
            list_dataset=self.list_dataset,
            list_jobs=self.list_jobs,
        )

    def _new_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
        status: str,
        completed_at: datetime | None,
        record_count: int,
        diagnostics: dict[str, object],
    ) -> IngestionJobRecord:
        return IngestionJobRecord(
            job_id=self._allocate_job_id(),
            source_id=source_id,
            dataset_id=source_id,
            period=period,
            trigger=trigger,
            status=status,
            started_at=datetime.now(UTC),
            completed_at=completed_at,
            record_count=record_count,
            diagnostics=diagnostics,
        )

    def _allocate_job_id(self) -> str:
        job_id = f"ingest_{self._next_job_id:04d}"
        self._next_job_id += 1
        return job_id
