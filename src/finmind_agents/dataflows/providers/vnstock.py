from datetime import UTC, datetime, timedelta
from importlib import import_module
from typing import Any

from finmind_agents.dataflows.models import (
    DataflowProviderResult,
    DataflowCollectionRequest,
    DatasetGroup,
    CollectionStatus,
    dataflow_now,
)
from finmind_agents.dataflows.providers.base import ProviderCapability, ProviderFetchResult
from finmind_agents.dataflows.normalizers import (
    normalize_fundamental_record,
    normalize_price_record,
)
from finmind_agents.models import Market


class VnstockProvider:
    provider_id = "vnstock"
    capabilities = (
        ProviderCapability(
            market=Market.VN_STOCK,
            dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL),
        ),
    )

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key.strip()

    def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
        try:
            vnstock = import_module("vnstock")
        except ImportError:
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id,
                    dataset_groups=_supported_groups(request.dataset_groups),
                    status=CollectionStatus.SKIPPED,
                    warnings=("vnstock_unavailable",),
                    failure_reason="vnstock package is not installed",
                )
            )
        if self._api_key:
            register_user = getattr(vnstock, "register_user", None)
            if callable(register_user):
                try:
                    register_user(api_key=self._api_key)
                except Exception:
                    return ProviderFetchResult(
                        provider_result=DataflowProviderResult(
                            provider_id=self.provider_id,
                            dataset_groups=_supported_groups(request.dataset_groups),
                            status=CollectionStatus.FAILED,
                            warnings=("vnstock_registration_failed",),
                            failure_reason="vnstock API key registration failed",
                        )
                    )
        records = []
        warnings: list[str] = []
        price_failure = None
        fundamental_failure = None
        if DatasetGroup.MARKET_PRICE in request.dataset_groups:
            try:
                records.extend(_fetch_price_records(vnstock, request))
            except Exception as error:
                warnings.append("vnstock_price_fetch_failed")
                price_failure = str(error)
            else:
                price_failure = None
        if DatasetGroup.FUNDAMENTAL in request.dataset_groups:
            try:
                fundamental_records = _fetch_fundamental_records(vnstock, request)
                records.extend(fundamental_records)
                if any(
                    record.source_id == "vnstock_company_overview"
                    for record in fundamental_records
                ):
                    warnings.append("vnstock_finance_fetch_failed")
            except Exception as error:
                warnings.append("vnstock_fundamental_fetch_failed")
                fundamental_failure = str(error)
            else:
                fundamental_failure = None
        if not records:
            failure_reason = "; ".join(
                reason
                for reason in (price_failure, fundamental_failure)
                if reason
            ) or "vnstock returned no matching rows"
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id,
                    dataset_groups=_supported_groups(request.dataset_groups),
                    status=CollectionStatus.FAILED,
                    warnings=tuple(warnings or ["vnstock_empty_result"]),
                    failure_reason=failure_reason,
                )
            )
        source_ids = tuple(sorted({record.source_id for record in records}))
        return ProviderFetchResult(
            provider_result=DataflowProviderResult(
                provider_id=self.provider_id,
                dataset_groups=_supported_groups(request.dataset_groups),
                status=CollectionStatus.PARTIAL if warnings else CollectionStatus.SUCCESS,
                source_ids=source_ids,
                warnings=tuple(warnings),
            ),
            records=tuple(records),
        )


def _supported_groups(groups: tuple[DatasetGroup, ...]) -> tuple[DatasetGroup, ...]:
    return tuple(
        group
        for group in groups
        if group in {DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL}
    )


def _fetch_price_records(
    vnstock: Any,
    request: DataflowCollectionRequest,
) -> list[Any]:
    end = dataflow_now().date()
    start = end - timedelta(days=45)
    if hasattr(vnstock, "Market"):
        market = _call_or_value(vnstock.Market().equity, request.symbol)
        raw_rows = market.ohlcv(
            start=start.isoformat(),
            end=end.isoformat(),
            resolution="1D",
            source="vci",
        )
    else:
        quote = vnstock.Quote(source="VCI", symbol=request.symbol)
        raw_rows = quote.history(
            start=start.isoformat(),
            end=end.isoformat(),
            interval="1D",
        )
    rows = _rows_from_provider_payload(raw_rows)
    if not rows:
        return []
    row = rows[-1]
    market_time = _parse_datetime(row.get("time") or row.get("date") or row.get("tradingDate"))
    close = _number(row.get("close") or row.get("closePrice") or row.get("matchPrice"))
    if close is None:
        raise ValueError("vnstock price row is missing close")
    return [
        normalize_price_record(
            dataset_id="vn_prices",
            record_key=f"{request.symbol}-{market_time.date().isoformat()}",
            instrument_id=request.symbol,
            market_time=market_time,
            collected_at=dataflow_now(),
            source_id="vnstock_prices",
            payload={
                "close": close,
                "change_percent": _number(
                    row.get("change_percent")
                    or row.get("pct_change")
                    or row.get("changePercent")
                ),
                "volume": _number(row.get("volume") or row.get("matchingVolume")),
            },
        )
    ]


def _fetch_fundamental_records(
    vnstock: Any,
    request: DataflowCollectionRequest,
) -> list[Any]:
    """Fetch fundamental records from the vnstock 4.x unified API.

    Primary source is the annual income statement + balance sheet (source
    ``vci``), which give current per-year EPS, net income and equity. If the
    statements are unavailable, fall back to the company overview snapshot.
    """
    equity = _call_or_value(vnstock.Fundamental().equity, request.symbol)
    income_rows = _safe_statement_rows(equity, "income_statement")
    balance_rows = _safe_statement_rows(equity, "balance_sheet")
    overview_row = _first_overview_row(vnstock, request)

    if income_rows and balance_rows:
        record = _fundamental_record_from_statements(
            request, income_rows, balance_rows, overview_row
        )
        if record is not None:
            return [record]

    if overview_row:
        return [_fundamental_record_from_company_overview(request, overview_row)]
    return []


def _safe_statement_rows(equity: Any, method: str) -> list[dict[str, Any]]:
    try:
        payload = getattr(equity, method)(period="year", source="vci")
    except Exception:
        return []
    return _rows_from_provider_payload(payload)


def _first_overview_row(
    vnstock: Any,
    request: DataflowCollectionRequest,
) -> dict[str, Any] | None:
    try:
        rows = _fetch_company_overview_rows(vnstock, request)
    except Exception:
        return None
    return rows[-1] if rows else None


def _fundamental_record_from_statements(
    request: DataflowCollectionRequest,
    income_rows: list[dict[str, Any]],
    balance_rows: list[dict[str, Any]],
    overview_row: dict[str, Any] | None,
) -> Any | None:
    period = _latest_period_column(income_rows)
    if period is None:
        return None
    eps = _metric_value(income_rows, "eps_basic_vnd", period)
    net_income = _metric_value(income_rows, "net_profit_loss_after_tax", period)
    owners_equity = _metric_value(balance_rows, "owners_equity", period)
    total_assets = _metric_value(balance_rows, "total_assets", period)
    shares = _number(overview_row.get("issue_share")) if overview_row else None
    bvps = _ratio(owners_equity, shares)
    market_time = (
        datetime(int(period[:4]), 12, 31, tzinfo=UTC)
        if period[:4].isdigit()
        else dataflow_now()
    )
    return normalize_fundamental_record(
        dataset_id="vn_fundamentals",
        record_key=f"{request.symbol}-{period}",
        instrument_id=request.symbol,
        market_time=market_time,
        collected_at=dataflow_now(),
        source_id="vnstock_fundamentals",
        payload={
            "eps": _number(eps),
            "bvps": _number(bvps) if bvps is not None else None,
            "roe_percent": _roe_percent(_ratio(net_income, owners_equity)),
            "net_income": _number(net_income),
            "owners_equity": _number(owners_equity),
            "total_assets": _number(total_assets),
            "outstanding_shares": shares,
            "market_cap": _number(overview_row.get("market_cap")) if overview_row else None,
            "sector": overview_row.get("sector") if overview_row else None,
            "period": period,
        },
    )


def _fetch_company_overview_rows(
    vnstock: Any,
    request: DataflowCollectionRequest,
) -> list[dict[str, Any]]:
    company = vnstock.Company(source="vci", symbol=request.symbol)
    return _rows_from_provider_payload(company.overview())


def _fundamental_record_from_company_overview(
    request: DataflowCollectionRequest,
    row: dict[str, Any],
) -> Any:
    market_time = _parse_datetime(row.get("as_of_date") or row.get("date") or dataflow_now())
    return normalize_fundamental_record(
        dataset_id="vn_fundamentals",
        record_key=f"{request.symbol}-{market_time.date().isoformat()}",
        instrument_id=request.symbol,
        market_time=market_time,
        collected_at=dataflow_now(),
        source_id="vnstock_company_overview",
        payload={
            "exchange": row.get("exchange"),
            "outstanding_shares": _number(row.get("issue_share") or row.get("outstanding_shares")),
            "market_cap": _number(row.get("market_cap")),
            "free_float": _number(row.get("free_float")),
            "free_float_percentage": _number(row.get("free_float_percentage")),
            "sector": row.get("sector"),
            "period": market_time.date().isoformat(),
        },
    )


def _latest_period_column(rows: list[dict[str, Any]]) -> str | None:
    periods: list[int] = []
    for row in rows:
        for key in row:
            if isinstance(key, str) and key[:4].isdigit():
                try:
                    periods.append(int(key[:4]))
                except ValueError:
                    continue
    return str(max(periods)) if periods else None


def _metric_value(
    rows: list[dict[str, Any]],
    item_id: str,
    period: str,
) -> Any:
    for row in rows:
        if str(row.get("item_id", "")).lower() == item_id:
            return row.get(period)
    return None


def _ratio(numerator: Any, denominator: Any) -> float | None:
    top = _number(numerator)
    bottom = _number(denominator)
    if top is None or bottom is None or bottom == 0:
        return None
    return top / bottom


def _call_or_value(value: Any, symbol: str) -> Any:
    if callable(value):
        return value(symbol=symbol)
    return value


def _fundamental_row_from_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    direct_rows = [
        row
        for row in rows
        if row.get("eps")
        or row.get("EPS")
        or row.get("bvps")
        or row.get("BVPS")
    ]
    if direct_rows:
        return direct_rows[-1]

    period = _latest_report_period(rows)
    metrics = {
        str(row.get("item_id", "")).lower(): row
        for row in rows
    }
    eps_row = metrics.get("trailing_eps") or metrics.get("eps")
    bvps_row = metrics.get("book_value_per_share_bvps") or metrics.get("bvps")
    roe_row = metrics.get("roe") or metrics.get("roe_trailling")
    return {
        "period": period,
        "eps": eps_row.get(period) if eps_row else None,
        "bvps": bvps_row.get(period) if bvps_row else None,
        "roe": roe_row.get(period) if roe_row else None,
    }


def _latest_report_period(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        for key in row:
            if key not in {"item", "item_id"}:
                return key
    return str(dataflow_now().year)


def _rows_from_provider_payload(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if hasattr(payload, "to_dict"):
        records = payload.to_dict("records")
        return [dict(record) for record in records]
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, tuple):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if all(isinstance(value, list) for value in payload.values()):
            length = max((len(value) for value in payload.values()), default=0)
            return [
                {
                    key: value[index]
                    for key, value in payload.items()
                    if index < len(value)
                }
                for index in range(length)
            ]
        return [payload]
    return []


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if value is None:
        return dataflow_now()
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _number(value: object) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return value
    try:
        parsed = float(str(value).replace(",", ""))
    except ValueError:
        return None
    return int(parsed) if parsed.is_integer() else parsed


def _roe_percent(value: object) -> float | int | None:
    number = _number(value)
    if number is None:
        return None
    return number * 100 if abs(number) <= 1 else number
