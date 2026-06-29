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
                fundamental_records, company_profile = _fetch_fundamental_records(
                    vnstock, request
                )
                records.extend(fundamental_records)
                if company_profile is not None:
                    records.append(company_profile)
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


PRICE_HISTORY_COUNT = 1500
REVENUE_ITEM_IDS = ("net_sales", "total_operating_income", "total_revenue", "revenue", "sales")


def _fetch_price_records(
    vnstock: Any,
    request: DataflowCollectionRequest,
) -> list[Any]:
    """Return one price record per OHLCV row (full daily series).

    Prices are in thousand VND per vnstock convention. ``count`` pulls enough
    history (~6 years) to cover the fundamental 5-year window's year-end prices
    and the technical-analysis lookback.
    """
    end = dataflow_now().date()
    start = end - timedelta(days=45)
    if hasattr(vnstock, "Market"):
        market = _call_or_value(vnstock.Market().equity, request.symbol)
        raw_rows = market.ohlcv(
            start=start.isoformat(),
            end=end.isoformat(),
            resolution="1D",
            source="vci",
            count=PRICE_HISTORY_COUNT,
        )
    else:
        quote = vnstock.Quote(source="VCI", symbol=request.symbol)
        raw_rows = quote.history(
            start=start.isoformat(),
            end=end.isoformat(),
            interval="1D",
        )
    rows = _rows_from_provider_payload(raw_rows)
    records: list[Any] = []
    for row in rows:
        market_time = _parse_datetime(
            row.get("time") or row.get("date") or row.get("tradingDate")
        )
        close = _number(row.get("close") or row.get("closePrice") or row.get("matchPrice"))
        if market_time is None or close is None:
            continue
        records.append(
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
        )
    return records


def _fetch_fundamental_records(
    vnstock: Any,
    request: DataflowCollectionRequest,
) -> tuple[list[Any], Any | None]:
    """Return (fundamental_records, company_profile_record).

    Fundamental records are one per available annual period with eps, revenue,
    net income, equity, total assets, CFO and ROE. The company profile record is
    the current snapshot (name, sector, market cap, shares, PE/PB). Falls back to
    a single overview-based record when the statements are unavailable.
    """
    equity = _call_or_value(vnstock.Fundamental().equity, request.symbol)
    income_rows = _safe_statement_rows(equity, "income_statement")
    balance_rows = _safe_statement_rows(equity, "balance_sheet")
    cash_flow_rows = _safe_statement_rows(equity, "cash_flow")
    overview_row = _first_overview_row(vnstock, request)
    if income_rows and balance_rows:
        records, profile = _records_from_statements(
            request, income_rows, balance_rows, cash_flow_rows, overview_row
        )
        if records:
            return records, profile
    if overview_row:
        return (
            [_fundamental_record_from_company_overview(request, overview_row)],
            _company_profile_record(request, overview_row, None, None),
        )
    return [], None


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


def _records_from_statements(
    request: DataflowCollectionRequest,
    income_rows: list[dict[str, Any]],
    balance_rows: list[dict[str, Any]],
    cash_flow_rows: list[dict[str, Any]],
    overview_row: dict[str, Any] | None,
) -> tuple[list[Any], Any | None]:
    periods = _period_columns(income_rows)
    if not periods:
        return [], None
    shares = _number(overview_row.get("issue_share")) if overview_row else None
    latest_period = periods[0]
    latest_eps = _number(_metric_value(income_rows, "eps_basic_vnd", latest_period))
    latest_equity = _number(_metric_value(balance_rows, "owners_equity", latest_period))
    latest_bvps = _ratio(latest_equity, shares)
    records: list[Any] = []
    for period in periods:
        eps = _number(_metric_value(income_rows, "eps_basic_vnd", period))
        revenue = _number(_first_metric(income_rows, REVENUE_ITEM_IDS, period))
        net_income = _number(_metric_value(income_rows, "net_profit_loss_after_tax", period))
        owners_equity = _number(_metric_value(balance_rows, "owners_equity", period))
        total_assets = _number(_metric_value(balance_rows, "total_assets", period))
        cfo = (
            _number(_metric_value(cash_flow_rows, "net_cash_from_operating_activities", period))
            if cash_flow_rows
            else None
        )
        market_time = (
            datetime(int(period[:4]), 12, 31, tzinfo=UTC)
            if period[:4].isdigit()
            else dataflow_now()
        )
        records.append(
            normalize_fundamental_record(
                dataset_id="vn_fundamentals",
                record_key=f"{request.symbol}-{period}",
                instrument_id=request.symbol,
                market_time=market_time,
                collected_at=dataflow_now(),
                source_id="vnstock_fundamentals",
                payload={
                    "eps": eps,
                    "revenue": revenue,
                    "net_income": net_income,
                    "owners_equity": owners_equity,
                    "total_assets": total_assets,
                    "cfo": cfo,
                    "roe_percent": _roe_percent(_ratio(net_income, owners_equity)),
                    "outstanding_shares": shares if period == latest_period else None,
                    "period": period,
                },
            )
        )
    profile = _company_profile_record(request, overview_row, latest_eps, latest_bvps)
    return records, profile


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


def _company_profile_record(
    request: DataflowCollectionRequest,
    overview_row: dict[str, Any] | None,
    latest_eps: float | int | None,
    latest_bvps: float | int | None,
) -> Any | None:
    if overview_row is None:
        return None
    current_price = _number(overview_row.get("current_price"))
    return normalize_fundamental_record(
        dataset_id="vn_company_profile",
        record_key=f"{request.symbol}-profile",
        instrument_id=request.symbol,
        market_time=dataflow_now(),
        collected_at=dataflow_now(),
        source_id="vnstock_company_overview",
        payload={
            "company_name": overview_row.get("organ_name"),
            "short_name": overview_row.get("organ_short_name"),
            "sector": overview_row.get("sector"),
            "current_price": current_price,
            "market_cap": _number(overview_row.get("market_cap")),
            "outstanding_shares": _number(overview_row.get("issue_share")),
            "highest_price_1y": _number(overview_row.get("highest_price1_year")),
            "lowest_price_1y": _number(overview_row.get("lowest_price1_year")),
            "foreigner_percentage": _number(overview_row.get("foreigner_percentage")),
            "target_price": _number(overview_row.get("target_price")),
            "rating": overview_row.get("rating"),
            "pe": _ratio(current_price, latest_eps) if latest_eps else None,
            "pb": _ratio(current_price, latest_bvps) if latest_bvps else None,
            "period": "profile",
        },
    )


def _period_columns(rows: list[dict[str, Any]]) -> list[str]:
    periods: set[str] = set()
    for row in rows:
        for key in row:
            if isinstance(key, str) and key[:4].isdigit():
                periods.add(key)
    return sorted(periods, reverse=True)


def _latest_period_column(rows: list[dict[str, Any]]) -> str | None:
    cols = _period_columns(rows)
    return cols[0] if cols else None


def _metric_value(
    rows: list[dict[str, Any]],
    item_id: str,
    period: str,
) -> Any:
    for row in rows:
        if str(row.get("item_id", "")).lower() == item_id:
            return row.get(period)
    return None


def _first_metric(
    rows: list[dict[str, Any]],
    item_ids: tuple[str, ...],
    period: str,
) -> Any:
    for item_id in item_ids:
        value = _metric_value(rows, item_id, period)
        if value is not None:
            return value
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
