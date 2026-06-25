from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json

from api.platform.factory import create_ingestion_service
from api.platform.ingestion.errors import ProviderFetchError
from api.platform.ingestion.planner import IngestionFetchRequest
from api.platform.ingestion.service import IngestionService, _serialize_job
from api.platform.ingestion.store_writer import IngestionJobRecord
from api.settings import Settings

MARKET_HISTORY_PRESET = "market-history"
MARKET_LATEST_PRESET = "market-latest"
US_DAILY_HISTORY_PRESET = "us-daily-history"
US_XAUUSD_HISTORY_PRESET = "us-xauusd-history"
VN_HISTORY_PRESET = "vn-history"
FREE_1H_WINDOW_DAYS = 60
MARKET_LATEST_SOURCES = ("us_prices", "xauusd_prices", "sjc_gold_prices")
VN_HISTORY_SOURCES = ("vn_prices_daily", "vn_prices")
ROADMAP_PRESETS: frozenset[str] = frozenset(
    {
        MARKET_HISTORY_PRESET,
        MARKET_LATEST_PRESET,
        US_DAILY_HISTORY_PRESET,
        US_XAUUSD_HISTORY_PRESET,
    }
)
ROADMAP_DISABLED_REASON = (
    "roadmap markets disabled (FINMIND_ROADMAP_MARKETS=false)"
)


@dataclass(frozen=True)
class BackfillPlanResult:
    source_id: str
    status: str
    from_date: str
    to_date: str
    job: IngestionJobRecord | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_id": self.source_id,
            "status": self.status,
            "from_date": self.from_date,
            "to_date": self.to_date,
        }
        if self.job is not None:
            payload["job"] = _serialize_job(self.job)
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def run_historical_backfill(
    service: IngestionService,
    source_id: str,
    from_date: str,
    to_date: str,
) -> IngestionJobRecord:
    return service.run_backfill_request(
        IngestionFetchRequest(
            source_id=source_id,
            mode="historical",
            from_date=from_date,
            to_date=to_date,
        )
    )


def run_market_history_backfill(
    service: IngestionService,
    from_date: str,
    to_date: str,
) -> list[BackfillPlanResult]:
    """Run the phase 002 free-source market-history operator plan."""

    results: list[BackfillPlanResult] = []
    for source_id, start, end, reason in _market_history_steps(
        from_date=from_date,
        to_date=to_date,
    ):
        if reason is not None:
            results.append(
                BackfillPlanResult(
                    source_id=source_id,
                    status="skipped",
                    from_date=start,
                    to_date=end,
                    reason=reason,
                )
            )
            continue
        if source_id not in service.sources:
            results.append(
                BackfillPlanResult(
                    source_id=source_id,
                    status="skipped",
                    from_date=start,
                    to_date=end,
                    reason=f"{source_id} is not configured in this runtime",
                )
            )
            continue
        if source_id in {"us_prices_daily", "xauusd_prices_daily"}:
            results.append(
                _run_range_source_backfill(
                    service=service,
                    source_id=source_id,
                    from_date=start,
                    to_date=end,
                )
            )
            continue
        job = run_historical_backfill(
            service=service,
            source_id=source_id,
            from_date=start,
            to_date=end,
        )
        results.append(
            BackfillPlanResult(
                source_id=source_id,
                status=job.status,
                from_date=start,
                to_date=end,
                job=job,
            )
        )
    return results


def run_market_latest_fetch(service: IngestionService) -> list[BackfillPlanResult]:
    """Run current-data fetches for the phase 002 latest-first operator plan."""

    results: list[BackfillPlanResult] = []
    for source_id in MARKET_LATEST_SOURCES:
        if source_id not in service.sources:
            results.append(
                BackfillPlanResult(
                    source_id=source_id,
                    status="skipped",
                    from_date="latest",
                    to_date="latest",
                    reason=f"{source_id} is not configured in this runtime",
                )
            )
            continue
        job = service.run_scheduled_request(
            IngestionFetchRequest(source_id=source_id, mode="latest")
        )
        results.append(
            BackfillPlanResult(
                source_id=source_id,
                status=job.status,
                from_date=job.period,
                to_date=job.period,
                job=job,
            )
        )
    return results


def run_us_daily_history_backfill(
    service: IngestionService,
    from_date: str,
    to_date: str,
) -> BackfillPlanResult:
    return _run_range_source_backfill(
        service=service,
        source_id="us_prices_daily",
        from_date=from_date,
        to_date=to_date,
    )


def run_us_xauusd_history_backfill(
    service: IngestionService,
    from_date: str,
    to_date: str,
) -> list[BackfillPlanResult]:
    results: list[BackfillPlanResult] = []
    for source_id, start, end, range_fetch in _us_xauusd_history_steps(
        from_date=from_date,
        to_date=to_date,
    ):
        if range_fetch:
            results.append(
                _run_range_source_backfill(
                    service=service,
                    source_id=source_id,
                    from_date=start,
                    to_date=end,
                )
            )
            continue
        if source_id not in service.sources:
            results.append(
                BackfillPlanResult(
                    source_id=source_id,
                    status="skipped",
                    from_date=start,
                    to_date=end,
                    reason=f"{source_id} is not configured in this runtime",
                )
            )
            continue
        job = run_historical_backfill(
            service=service,
            source_id=source_id,
            from_date=start,
            to_date=end,
        )
        results.append(
            BackfillPlanResult(
                source_id=source_id,
                status=job.status,
                from_date=start,
                to_date=end,
                job=job,
            )
        )
    return results


def run_vn_history_backfill(
    service: IngestionService,
    from_date: str,
    to_date: str,
) -> list[BackfillPlanResult]:
    """Run the phase 002 VN-only operator history plan.

    `vn_prices_daily` is the required canonical leg. `vn_prices` is a
    best-effort 1h leg whose failures are reported as ``skipped`` so they
    do not fail the overall preset.
    """

    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")
    if end < start:
        raise ValueError("to_date must be on or after from_date")

    results: list[BackfillPlanResult] = [
        _run_range_source_backfill(
            service=service,
            source_id="vn_prices_daily",
            from_date=start.isoformat(),
            to_date=end.isoformat(),
        )
    ]
    one_hour_start = max(
        start, end - timedelta(days=FREE_1H_WINDOW_DAYS - 1)
    )
    hourly_from = one_hour_start.isoformat()
    hourly_to = end.isoformat()
    if "vn_prices" not in service.sources:
        results.append(
            BackfillPlanResult(
                source_id="vn_prices",
                status="skipped",
                from_date=hourly_from,
                to_date=hourly_to,
                reason="vn_prices is not configured in this runtime",
            )
        )
        return results
    try:
        job = run_historical_backfill(
            service=service,
            source_id="vn_prices",
            from_date=hourly_from,
            to_date=hourly_to,
        )
    except ProviderFetchError as exc:
        results.append(
            BackfillPlanResult(
                source_id="vn_prices",
                status="skipped",
                from_date=hourly_from,
                to_date=hourly_to,
                reason=(
                    "vn_prices 1h best-effort skipped after provider "
                    f"failure: {exc}"
                ),
            )
        )
        return results
    if job.status == "failed":
        results.append(
            BackfillPlanResult(
                source_id="vn_prices",
                status="skipped",
                from_date=hourly_from,
                to_date=hourly_to,
                reason=(
                    "vn_prices 1h best-effort skipped after provider "
                    f"failure: {job.diagnostics.get('error', 'unknown')}"
                ),
            )
        )
        return results
    results.append(
        BackfillPlanResult(
            source_id="vn_prices",
            status=job.status,
            from_date=hourly_from,
            to_date=hourly_to,
            job=job,
        )
    )
    return results


def _run_range_source_backfill(
    service: IngestionService,
    source_id: str,
    from_date: str,
    to_date: str,
) -> BackfillPlanResult:
    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")
    if end < start:
        raise ValueError("to_date must be on or after from_date")
    period_scope = f"{start.isoformat()}:{end.isoformat()}"
    source = service.sources.get(source_id)
    if source is None:
        return BackfillPlanResult(
            source_id=source_id,
            status="skipped",
            from_date=start.isoformat(),
            to_date=end.isoformat(),
            reason=f"{source_id} is not configured in this runtime",
        )
    if service.store.has_active_job(source_id=source_id, period=period_scope):
        job = service.store.save_completed_job(
            source_id=source_id,
            period=period_scope,
            trigger="backfill",
            status="blocked",
            record_count=0,
            diagnostics={"message": f"{source_id} for {period_scope} is already running"},
        )
        return BackfillPlanResult(
            source_id=source_id,
            status=job.status,
            from_date=start.isoformat(),
            to_date=end.isoformat(),
            job=job,
        )
    try:
        records = source.fetch(period_scope)
        upserted = service.store.upsert_many(records)
    except ProviderFetchError as exc:
        job = service.store.save_completed_job(
            source_id=source_id,
            period=period_scope,
            trigger="backfill",
            status="failed",
            record_count=0,
            diagnostics={"error": str(exc)},
        )
        return BackfillPlanResult(
            source_id=source_id,
            status=job.status,
            from_date=start.isoformat(),
            to_date=end.isoformat(),
            job=job,
        )

    job = service.store.save_completed_job(
        source_id=source_id,
        period=period_scope,
        trigger="backfill",
        status="success",
        record_count=upserted,
        diagnostics={
            "upserted": upserted,
            "periods": [period_scope],
            "mode": "historical_range",
        },
    )
    return BackfillPlanResult(
        source_id=source_id,
        status=job.status,
        from_date=start.isoformat(),
        to_date=end.isoformat(),
        job=job,
    )


def _market_history_steps(
    *,
    from_date: str,
    to_date: str,
) -> list[tuple[str, str, str, str | None]]:
    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")
    if end < start:
        raise ValueError("to_date must be on or after from_date")

    xauusd_1h_start = max(start, end - timedelta(days=FREE_1H_WINDOW_DAYS - 1))
    return [
        ("us_prices_daily", start.isoformat(), end.isoformat(), None),
        ("xauusd_prices_daily", start.isoformat(), end.isoformat(), None),
        ("xauusd_prices", xauusd_1h_start.isoformat(), end.isoformat(), None),
        (
            "sjc_gold_prices",
            start.isoformat(),
            end.isoformat(),
            "Configured SJC official provider is a current quote source, not a historical archive",
        ),
    ]


def _us_xauusd_history_steps(
    *,
    from_date: str,
    to_date: str,
) -> list[tuple[str, str, str, bool]]:
    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")
    if end < start:
        raise ValueError("to_date must be on or after from_date")

    one_hour_start = max(start, end - timedelta(days=FREE_1H_WINDOW_DAYS - 1))
    return [
        ("us_prices_daily", start.isoformat(), end.isoformat(), True),
        ("us_prices", one_hour_start.isoformat(), end.isoformat(), False),
        ("xauusd_prices_daily", start.isoformat(), end.isoformat(), True),
        ("xauusd_prices", one_hour_start.isoformat(), end.isoformat(), False),
    ]


def _parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.fromisoformat(value).date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO date") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run market-data operator jobs.")
    parser.add_argument("--source-id")
    parser.add_argument(
        "--preset",
        choices=[
            MARKET_HISTORY_PRESET,
            MARKET_LATEST_PRESET,
            US_DAILY_HISTORY_PRESET,
            US_XAUUSD_HISTORY_PRESET,
            VN_HISTORY_PRESET,
        ],
        help="Run a predefined operator backfill plan.",
    )
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if (
        args.preset in ROADMAP_PRESETS
        and not settings.roadmap_markets_enabled
    ):
        print(
            json.dumps(
                {
                    "preset": args.preset,
                    "status": "skipped",
                    "reason": ROADMAP_DISABLED_REASON,
                },
                ensure_ascii=True,
            )
        )
        return 0

    service = create_ingestion_service(settings)
    if args.preset == MARKET_LATEST_PRESET:
        results = run_market_latest_fetch(service=service)
        print(
            json.dumps(
                {
                    "preset": MARKET_LATEST_PRESET,
                    "status": _overall_status(results),
                    "results": [result.to_dict() for result in results],
                },
                ensure_ascii=True,
            )
        )
        return 0 if all(result.status in {"success", "skipped"} for result in results) else 1

    if not args.from_date or not args.to_date:
        parser.error("--from-date and --to-date are required unless --preset market-latest")

    if args.preset == VN_HISTORY_PRESET:
        try:
            results = run_vn_history_backfill(
                service=service,
                from_date=args.from_date,
                to_date=args.to_date,
            )
        except ValueError as exc:
            print(
                json.dumps(
                    {"status": "failed", "error": str(exc)},
                    ensure_ascii=True,
                )
            )
            return 1
        print(
            json.dumps(
                {
                    "preset": VN_HISTORY_PRESET,
                    "status": _overall_status(results),
                    "results": [result.to_dict() for result in results],
                },
                ensure_ascii=True,
            )
        )
        return (
            0
            if all(
                result.status in {"success", "skipped"}
                for result in results
            )
            else 1
        )

    if args.preset == MARKET_HISTORY_PRESET:
        try:
            results = run_market_history_backfill(
                service=service,
                from_date=args.from_date,
                to_date=args.to_date,
            )
        except ValueError as exc:
            print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True))
            return 1
        print(
            json.dumps(
                {
                    "preset": MARKET_HISTORY_PRESET,
                    "status": _overall_status(results),
                    "results": [result.to_dict() for result in results],
                },
                ensure_ascii=True,
            )
        )
        return 0 if all(result.status in {"success", "skipped"} for result in results) else 1
    if args.preset == US_XAUUSD_HISTORY_PRESET:
        try:
            results = run_us_xauusd_history_backfill(
                service=service,
                from_date=args.from_date,
                to_date=args.to_date,
            )
        except ValueError as exc:
            print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True))
            return 1
        print(
            json.dumps(
                {
                    "preset": US_XAUUSD_HISTORY_PRESET,
                    "status": _overall_status(results),
                    "results": [result.to_dict() for result in results],
                },
                ensure_ascii=True,
            )
        )
        return 0 if all(result.status in {"success", "skipped"} for result in results) else 1
    if args.preset == US_DAILY_HISTORY_PRESET:
        try:
            result = run_us_daily_history_backfill(
                service=service,
                from_date=args.from_date,
                to_date=args.to_date,
            )
        except ValueError as exc:
            print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True))
            return 1
        print(
            json.dumps(
                {
                    "preset": US_DAILY_HISTORY_PRESET,
                    "status": result.status,
                    "results": [result.to_dict()],
                },
                ensure_ascii=True,
            )
        )
        return 0 if result.status in {"success", "skipped"} else 1

    if not args.source_id:
        parser.error("--source-id is required unless --preset is provided")

    job = run_historical_backfill(
        service=service,
        source_id=args.source_id,
        from_date=args.from_date,
        to_date=args.to_date,
    )
    print(json.dumps(_serialize_job(job), ensure_ascii=True))
    return 0 if job.status == "success" else 1


def _overall_status(results: list[BackfillPlanResult]) -> str:
    if any(result.status == "failed" for result in results):
        return "failed"
    if any(result.status == "skipped" for result in results):
        return "partial"
    return "success"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
