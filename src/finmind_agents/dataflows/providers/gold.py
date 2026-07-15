"""Bounded XAUUSD daily-price connector.

The external provider is deliberately injected as a small callable.  This
keeps provider credentials, schemas, and rights behind the connector contract
and lets automated tests use fixtures without live market access.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from finmind_agents.dataflows.models import (
    CollectionStatus,
    DataflowCollectionRequest,
    DataflowProviderResult,
    DatasetGroup,
    dataflow_now,
)
from finmind_agents.dataflows.normalizers import normalize_price_record
from finmind_agents.dataflows.providers.base import ProviderCapability, ProviderFetchResult
from finmind_agents.models import Market

GoldFetcher = Callable[[], list[dict[str, Any]]]


class GoldProviderPermanentError(RuntimeError):
    """Raised when retrying the configured provider cannot fix the request."""


class TwelveDataGoldFetcher:
    """Fetch the fullest supported daily XAUUSD history from Twelve Data."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 15.0,
        base_url: str = "https://api.twelvedata.com",
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._base_url = base_url.rstrip("/")

    def __call__(self) -> list[dict[str, Any]]:
        if not self._api_key:
            raise GoldProviderPermanentError("gold provider credential is missing")
        response = httpx.get(
            f"{self._base_url}/time_series",
            params={
                "symbol": "XAU/USD",
                "interval": "1day",
                "outputsize": 5000,
                "format": "JSON",
                "apikey": self._api_key,
            },
            timeout=self._timeout_seconds,
        )
        if response.status_code == 429 or response.status_code >= 500:
            raise httpx.HTTPStatusError(
                "transient Gold provider response",
                request=response.request,
                response=response,
            )
        if response.status_code >= 400:
            raise GoldProviderPermanentError("Gold provider rejected the request")
        try:
            payload = response.json()
        except ValueError as error:
            raise GoldProviderPermanentError(
                "Gold provider returned an invalid response"
            ) from error
        if not isinstance(payload, dict):
            raise GoldProviderPermanentError("Gold provider returned an invalid response")
        if payload.get("status") == "error":
            code = payload.get("code")
            if code == 429 or (isinstance(code, int) and code >= 500):
                raise httpx.TransportError("transient Gold provider error")
            raise GoldProviderPermanentError("Gold provider rejected the request")
        values = payload.get("values")
        if not isinstance(values, list):
            raise GoldProviderPermanentError("Gold provider returned no daily series")
        return [row for row in values if isinstance(row, dict)]


class GoldPriceProvider:
    provider_id = "gold_daily"
    capabilities = (
        ProviderCapability(market=Market.GOLD, dataset_groups=(DatasetGroup.MARKET_PRICE,)),
    )

    def __init__(self, fetcher: GoldFetcher | None = None) -> None:
        self._fetcher = fetcher

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        if not _is_supported_request(request):
            return _failure("gold_request_not_supported")
        if self._fetcher is None:
            return _failure("gold_provider_not_configured")
        try:
            rows = self._fetcher()
        except GoldProviderPermanentError:
            return _failure("gold_provider_request_rejected")
        except Exception:
            return _failure("gold_provider_request_failed")
        record = _daily_record(rows)
        if record is None:
            return _failure("gold_provider_returned_no_valid_daily_prices")
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(
                provider_id=self.provider_id,
                dataset_groups=(DatasetGroup.MARKET_PRICE,),
                status=CollectionStatus.SUCCESS,
                source_ids=(record.source_id,),
            ),
            records=(record,),
        )


def _daily_record(rows: list[dict[str, Any]]):
    series: list[dict[str, Any]] = []
    for row in rows:
        timestamp = _parse_time(row.get("datetime") or row.get("time") or row.get("date"))
        close = _number(row.get("close"))
        if timestamp is None or close is None:
            continue
        series.append({
            "date": timestamp.date().isoformat(), "open": _number(row.get("open")),
            "high": _number(row.get("high")), "low": _number(row.get("low")),
            "close": close, "volume": _number(row.get("volume")),
        })
    if not series:
        return None
    series.sort(key=lambda row: str(row["date"]))
    latest = series[-1]
    now = dataflow_now()
    return normalize_price_record(
        dataset_id="gold_prices", record_key="XAUUSD-prices", instrument_id="XAUUSD",
        market_time=datetime.fromisoformat(str(latest["date"])).replace(tzinfo=UTC),
        collected_at=now, source_id="gold_daily", payload={
            "series": series, "count": len(series), "start_date": series[0]["date"],
            "end_date": latest["date"], "interval": "1D", "currency": "USD", "unit": "troy_ounce",
        },
    )


def _failure(reason: str) -> ProviderFetchResult:
    return ProviderFetchResult(
        provider_result=DataflowProviderResult(
            provider_id="gold_daily", dataset_groups=(DatasetGroup.MARKET_PRICE,),
            status=CollectionStatus.FAILED, warnings=(reason,), failure_reason=reason,
        )
    )


def _is_supported_request(request: DataflowCollectionRequest) -> bool:
    if request.market is not Market.GOLD or request.symbol != "XAUUSD":
        return False
    if set(request.dataset_groups) != {DatasetGroup.MARKET_PRICE}:
        return False
    for requirement in request.data_requirements:
        params = requirement.params
        interval = params.get("interval")
        instrument_id = params.get("instrument_id")
        if requirement.dataset not in {"market_price", "ohlcv", "price_history"}:
            return False
        if interval is not None and str(interval).upper() not in {"1D", "1DAY"}:
            return False
        if instrument_id is not None and str(instrument_id).upper() != "XAUUSD":
            return False
    return True


def _parse_time(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
        except ValueError:
            return None
    return None


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None
