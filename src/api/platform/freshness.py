from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol
from zoneinfo import ZoneInfo

from api.platform.ingestion.sources import TimeSeriesRecord

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class FreshnessKind(StrEnum):
    DAILY = "daily"
    HOURLY = "1h"


@dataclass(frozen=True)
class DatasetFreshnessRule:
    """Per-dataset freshness rule used by V1 VN-only thresholds."""

    dataset_id: str
    kind: FreshnessKind
    max_lag: timedelta


_VN_ONLY_DATASETS: tuple[str, ...] = (
    "vn_prices_daily",
    "vn_prices",
)

_ROADMAP_DATASETS: tuple[str, ...] = (
    "us_prices",
    "us_prices_daily",
    "xauusd_prices",
    "xauusd_prices_daily",
    "sjc_gold_prices",
)


DATASET_RULES: dict[str, DatasetFreshnessRule] = {
    "vn_prices_daily": DatasetFreshnessRule(
        dataset_id="vn_prices_daily",
        kind=FreshnessKind.DAILY,
        max_lag=timedelta(days=1),
    ),
    "vn_prices": DatasetFreshnessRule(
        dataset_id="vn_prices",
        kind=FreshnessKind.HOURLY,
        max_lag=timedelta(hours=6),
    ),
}


def active_freshness_dataset_ids(
    roadmap_enabled: bool,
) -> list[str]:
    """Return dataset ids to surface in the active freshness output.

    V1 default (roadmap disabled) is VN-only. When the roadmap flag
    is on, roadmap connectors are also included so operators can keep
    inspecting them; their underlying thresholds are unchanged.
    """

    if not roadmap_enabled:
        return list(_VN_ONLY_DATASETS)
    return [*_VN_ONLY_DATASETS, *_ROADMAP_DATASETS]


class FreshnessJob(Protocol):
    dataset_id: str
    status: str


def calculate_dataset_freshness(
    dataset_ids: list[str],
    list_dataset: Callable[[str], list[TimeSeriesRecord]],
    list_jobs: Callable[[], list[FreshnessJob]],
    now: datetime | None = None,
) -> list[dict[str, object]]:
    """Compute per-dataset freshness entries.

    ``now`` is an optional injection point used by tests. When omitted
    the current ``Asia/Ho_Chi_Minh`` wall clock is used.
    """

    entries: list[dict[str, object]] = []
    jobs = list_jobs()
    for dataset_id in dataset_ids:
        records = list_dataset(dataset_id)
        failed_latest = next(
            (
                job
                for job in jobs
                if job.dataset_id == dataset_id
                and job.status == "failed"
            ),
            None,
        )
        if failed_latest is not None:
            status = "failed"
        elif not records:
            status = "missing"
        else:
            status = _evaluate_status(
                dataset_id=dataset_id,
                records=records,
                now=now,
            )
        entries.append(
            {
                "dataset": dataset_id,
                "status": status,
                "as_of": (
                    records[-1].market_time.isoformat()
                    if records
                    else None
                ),
                "record_count": len(records),
            }
        )
    return entries


def _evaluate_status(
    dataset_id: str,
    records: list[TimeSeriesRecord],
    now: datetime | None,
) -> str:
    rule = DATASET_RULES.get(dataset_id)
    if rule is None:
        return "fresh"
    latest_market_time = max(
        record.market_time for record in records
    )
    if rule.kind is FreshnessKind.DAILY:
        return _daily_status(latest_market_time, now)
    return _hourly_status(latest_market_time, rule.max_lag, now)


def _vn_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(VN_TZ)
    if now.tzinfo is None:
        return now.replace(tzinfo=VN_TZ)
    return now.astimezone(VN_TZ)


def _daily_status(
    latest_market_time: datetime,
    now: datetime | None,
) -> str:
    today_vn = _vn_now(now).date()
    latest_date = latest_market_time.date()
    delta_days = (today_vn - latest_date).days
    weekend_or_monday = today_vn.weekday() in {0, 5, 6}
    max_lag_days = 3 if weekend_or_monday else 1
    return "fresh" if delta_days <= max_lag_days else "stale"


def _hourly_status(
    latest_market_time: datetime,
    max_lag: timedelta,
    now: datetime | None,
) -> str:
    now_vn = _vn_now(now)
    if latest_market_time.tzinfo is None:
        latest_vn = latest_market_time.replace(tzinfo=VN_TZ)
    else:
        latest_vn = latest_market_time.astimezone(VN_TZ)
    return "fresh" if (now_vn - latest_vn) <= max_lag else "stale"
