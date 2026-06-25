from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from collections.abc import Callable, Mapping

from api.platform.ingestion.errors import ProviderFetchError
from api.platform.ingestion.planner import IngestionFetchRequest, plan_fetch_periods
from api.platform.ingestion.sources import MarketDataSource, TimeSeriesRecord
from api.platform.ingestion.store_writer import IngestionJobRecord, TimeSeriesStore


@dataclass
class IngestionService:
    sources: dict[str, MarketDataSource]
    store: TimeSeriesStore
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def run_manual(self, source_id: str, period: str) -> IngestionJobRecord:
        return self.run_manual_request(
            IngestionFetchRequest(source_id=source_id, mode="period", period=period)
        )

    def run_scheduled(self, source_id: str, period: str) -> IngestionJobRecord:
        return self.run_scheduled_request(
            IngestionFetchRequest(source_id=source_id, mode="period", period=period)
        )

    def run_manual_request(self, request: IngestionFetchRequest) -> IngestionJobRecord:
        return self._run_request(request=request, trigger="manual")

    def run_scheduled_request(self, request: IngestionFetchRequest) -> IngestionJobRecord:
        return self._run_request(request=request, trigger="scheduled")

    def run_backfill_request(self, request: IngestionFetchRequest) -> IngestionJobRecord:
        return self._run_request(request=request, trigger="backfill")

    def status(self) -> dict[str, object]:
        return {
            "jobs": [_serialize_job(job) for job in self.store.list_jobs()],
            "freshness": self.store.freshness(),
        }

    def market_data(self, dataset_id: str) -> dict[str, object]:
        records = self.store.list_dataset(dataset_id)
        if dataset_id == "xauusd_prices":
            records = _merge_xauusd_hourly_display_records(
                hourly_records=records,
                daily_records=self.store.list_dataset("xauusd_prices_daily"),
            )
        return {
            "dataset_id": dataset_id,
            "record_count": len(records),
            "freshness": next(
                item
                for item in self.store.freshness()
                if item["dataset"] == dataset_id
            ),
            "records": [
                {
                    "record_key": record.record_key,
                    "instrument_id": record.instrument_id,
                    "market_time": record.market_time.isoformat(),
                    "source_id": record.source_id,
                    **record.payload,
                }
                for record in records
            ],
        }

    def _run_request(
        self,
        request: IngestionFetchRequest,
        trigger: str,
    ) -> IngestionJobRecord:
        source_id = request.source_id
        source = self.sources.get(source_id)
        try:
            periods = plan_fetch_periods(request, now=self.clock())
            period_scope = request.period_scope(periods)
        except ValueError as exc:
            return self.store.save_completed_job(
                source_id=source_id,
                period=request.period or request.from_date or "latest",
                trigger=trigger,
                status="failed",
                record_count=0,
                diagnostics={"error": str(exc)},
            )
        if source is None:
            return self.store.save_completed_job(
                source_id=source_id,
                period=period_scope,
                trigger=trigger,
                status="failed",
                record_count=0,
                diagnostics={"error": "Unsupported source"},
            )
        if self.store.has_active_job(source_id=source_id, period=period_scope):
            return self.store.save_completed_job(
                source_id=source_id,
                period=period_scope,
                trigger=trigger,
                status="blocked",
                record_count=0,
                diagnostics={"message": f"{source_id} for {period_scope} is already running"},
            )
        try:
            records = [
                record
                for fetch_period in periods
                for record in source.fetch(fetch_period)
            ]
            upserted = self.store.upsert_many(records)
        except ProviderFetchError as exc:
            return self.store.save_completed_job(
                source_id=source_id,
                period=period_scope,
                trigger=trigger,
                status="failed",
                record_count=0,
                diagnostics={"error": str(exc)},
            )
        except SystemExit as exc:
            return self.store.save_completed_job(
                source_id=source_id,
                period=period_scope,
                trigger=trigger,
                status="failed",
                record_count=0,
                diagnostics={"error": _safe_provider_exit(exc)},
            )
        diagnostics: dict[str, object] = {
            "upserted": upserted,
            "periods": periods,
            "mode": request.mode,
        }
        coverage = _coverage_diagnostics(records)
        if coverage:
            diagnostics["coverage"] = coverage
        return self.store.save_completed_job(
            source_id=source_id,
            period=period_scope,
            trigger=trigger,
            status="success",
            record_count=upserted,
            diagnostics=diagnostics,
        )


def _serialize_job(job: IngestionJobRecord) -> dict[str, object]:
    return {
        "job_id": job.job_id,
        "source_id": job.source_id,
        "dataset_id": job.dataset_id,
        "period": job.period,
        "trigger": job.trigger,
        "status": job.status,
        "started_at": job.started_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "record_count": job.record_count,
        "diagnostics": job.diagnostics,
    }


def _merge_xauusd_hourly_display_records(
    hourly_records: list[TimeSeriesRecord],
    daily_records: list[TimeSeriesRecord],
) -> list[TimeSeriesRecord]:
    hourly_keys = {
        record.market_time.replace(minute=0, second=0, microsecond=0)
        for record in hourly_records
    }
    fallback_records = [
        fallback_record
        for daily_record in daily_records
        for fallback_record in _expand_xauusd_daily_record(daily_record)
        if fallback_record.market_time not in hourly_keys
    ]
    return sorted(
        [*hourly_records, *fallback_records],
        key=lambda record: record.market_time,
    )


def _expand_xauusd_daily_record(record: TimeSeriesRecord) -> list[TimeSeriesRecord]:
    close_price = record.payload.get("close")
    if close_price is None:
        return []
    day_start = record.market_time.astimezone(UTC).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    records = []
    for hour in range(24):
        interval_start = day_start + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)
        records.append(
            TimeSeriesRecord(
                dataset_id="xauusd_prices",
                record_key=f"{record.record_key}:display_1h:{hour:02d}",
                instrument_id=record.instrument_id,
                market_time=interval_start,
                collected_at=record.collected_at,
                source_id=record.source_id,
                payload={
                    "symbol": str(record.payload.get("symbol", "XAUUSD")),
                    "interval_start": interval_start.isoformat(),
                    "interval_end": interval_end.isoformat(),
                    "open": close_price,
                    "high": close_price,
                    "low": close_price,
                    "close": close_price,
                    "unit": str(record.payload.get("unit", "oz")),
                    "currency": str(record.payload.get("currency", "USD")),
                    "display_fallback": True,
                    "source_grain": "1d",
                    "fallback_record_key": record.record_key,
                },
            )
        )
    return records


def _safe_provider_exit(exc: SystemExit) -> str:
    message = str(exc)
    if "rate limit" in message.lower() or "giới hạn" in message.lower():
        return "Provider fetch failed: rate limit exceeded"
    return "Provider fetch failed: provider terminated request"


def _coverage_diagnostics(records: list[TimeSeriesRecord]) -> dict[str, object] | None:
    capabilities = [
        record.payload.get("capabilities")
        for record in records
        if isinstance(record.payload.get("capabilities"), Mapping)
    ]
    if not capabilities:
        return None

    first = capabilities[0]
    coverage_values = {
        str(item.get("coverage"))
        for item in capabilities
        if item.get("coverage") is not None
    }
    missing_ranges = sorted(
        {
            str(missing_range)
            for item in capabilities
            for missing_range in _capability_missing_ranges(item)
        }
    )
    if "partial" in coverage_values or missing_ranges:
        status = "partial"
    elif "best_effort" in coverage_values:
        status = "best_effort"
    else:
        status = "complete"
    diagnostics: dict[str, object] = {
        "status": status,
    }
    for key in (
        "provider",
        "interval",
        "requested_from",
        "requested_to",
        "covered_from",
        "covered_to",
        "history",
        "rate_limit",
    ):
        if first.get(key) is not None:
            diagnostics[key] = first[key]
    if missing_ranges:
        diagnostics["missing_ranges"] = missing_ranges
    return diagnostics


def _capability_missing_ranges(capabilities: Mapping[object, object]) -> list[object]:
    missing_ranges = capabilities.get("missing_ranges", [])
    if isinstance(missing_ranges, list):
        return missing_ranges
    return []
