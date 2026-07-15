"""Deterministic, conservative valuation eligibility gate for Phase 03."""

from typing import Any

from finmind_agents.models import CanonicalMarketDataRecord


def build_valuation_record(
    records: tuple[CanonicalMarketDataRecord, ...],
) -> CanonicalMarketDataRecord | None:
    fundamental = next((item for item in records if item.dataset_id.endswith("_fundamentals")), None)
    price = next((item for item in records if item.dataset_id.endswith("_prices")), None)
    if fundamental is None or price is None:
        return None
    payload = _valuation_payload(fundamental.payload, price.payload)
    return CanonicalMarketDataRecord(
        dataset_id="vn_valuation",
        record_key=f"{fundamental.instrument_id}-valuation",
        instrument_id=fundamental.instrument_id,
        market_time=max(fundamental.market_time, price.market_time),
        collected_at=max(fundamental.collected_at, price.collected_at),
        source_id="deterministic_valuation",
        payload=payload,
    )


def _valuation_payload(
    fundamentals: dict[str, Any], price_payload: dict[str, Any]
) -> dict[str, object]:
    latest_price = _latest_close(price_payload)
    eps = _number(fundamentals.get("eps"))
    bvps = _number(fundamentals.get("bvps"))
    period = fundamentals.get("period")
    eligible = latest_price is not None and eps is not None and eps > 0 and bvps is not None and bvps > 0
    if not eligible:
        return {
            "status": "unavailable",
            "period": period or "Unavailable",
            "methods": {"pe": "Unavailable", "pb": "Unavailable", "dcf": "Unavailable"},
            "research_range": "Unavailable",
            "reason": "Missing, negative, or unit-unverified valuation inputs.",
        }
    return {
        "status": "eligible_inputs_only",
        "period": period or "Unavailable",
        "observed_multiples": {"pe": round(latest_price / eps, 2), "pb": round(latest_price / bvps, 2)},
        "methods": {"pe": "Unavailable", "pb": "Unavailable", "dcf": "Unavailable"},
        "research_range": "Unavailable",
        "reason": "Comparable-company assumptions and DCF cash-flow inputs are not supplied; no value range is estimated.",
    }


def _latest_close(payload: dict[str, Any]) -> float | None:
    series = payload.get("series")
    if not isinstance(series, list) or not series:
        return None
    last = series[-1]
    return _number(last.get("close")) if isinstance(last, dict) else None


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
