from __future__ import annotations

import math
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _pct(high: float, low: float) -> float:
    if low == 0:
        return 0.0
    return (high / low - 1) * 100


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    denom = sum((i - x_mean) ** 2 for i in range(n)) or 1.0
    return sum((i - x_mean) * (value - y_mean) for i, value in enumerate(values)) / denom


def _rsi_series(closes: list[float], period: int = 14) -> list[float | None]:
    if not closes:
        return []
    if len(closes) <= period:
        return [None] * len(closes)
    out: list[float | None] = [None] * len(closes)
    gains = []
    losses = []
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    out[period] = 100.0 if avg_loss == 0 else round(100 - 100 / (1 + avg_gain / avg_loss), 2)
    for i in range(period + 1, len(closes)):
        change = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + abs(min(change, 0.0))) / period
        out[i] = 100.0 if avg_loss == 0 else round(100 - 100 / (1 + avg_gain / avg_loss), 2)
    return out


def find_swing_points(
    series: list[dict[str, Any]],
    lookback: int = 2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    highs: list[dict[str, Any]] = []
    lows: list[dict[str, Any]] = []
    for idx in range(lookback, len(series) - lookback):
        window = series[idx - lookback: idx + lookback + 1]
        high = float(series[idx].get("high") or series[idx]["close"])
        low = float(series[idx].get("low") or series[idx]["close"])
        if all(high >= float(bar.get("high") or bar["close"]) for bar in window):
            highs.append({"index": idx, "date": series[idx]["date"], "price": round(high, 4)})
        if all(low <= float(bar.get("low") or bar["close"]) for bar in window):
            lows.append({"index": idx, "date": series[idx]["date"], "price": round(low, 4)})
    return highs, lows


def _strict_double_bottom(series: list[dict[str, Any]]) -> dict[str, Any]:
    highs, lows = find_swing_points(series)
    if len(lows) < 2:
        return {
            "pattern_id": "double_bottom",
            "pattern_name": "Double Bottom",
            "direction": "bullish",
            "verdict": "not_detected",
            "reader_note": "No two comparable swing lows are present.",
        }
    best_pair: tuple[dict[str, Any], dict[str, Any], float, float | None] | None = None
    for idx in range(len(lows) - 1):
        first = lows[idx]
        second = lows[idx + 1]
        diff_pct = abs(_pct(max(first["price"], second["price"]), min(first["price"], second["price"])))
        middle_highs = [item for item in highs if first["index"] < item["index"] < second["index"]]
        neckline = max((item["price"] for item in middle_highs), default=None)
        if neckline is None:
            continue
        if best_pair is None or diff_pct < best_pair[2]:
            best_pair = (first, second, diff_pct, neckline)
    if best_pair is None:
        return {
            "pattern_id": "double_bottom",
            "pattern_name": "Double Bottom",
            "direction": "bullish",
            "verdict": "not_detected",
            "reader_note": "No swing-low pair has a usable neckline.",
        }
    first, second, diff_pct, neckline = best_pair
    verdict = "not_detected"
    strength = None
    note = "Two comparable lows are not present."
    if diff_pct < 3 and neckline is not None:
        verdict = "detected"
        strength = "clear" if diff_pct < 1 else "potential"
        note = (
            "Two swing lows are within tolerance with a clear neckline."
            if diff_pct < 1
            else "Two swing lows are close enough to watch as a double bottom."
        )
    return {
        "pattern_id": "double_bottom",
        "pattern_name": "Double Bottom",
        "direction": "bullish",
        "verdict": verdict,
        "strength": strength,
        "confirmation_level": neckline,
        "evidence_points": {
            "first_low": first,
            "second_low": second,
            "difference_pct": round(diff_pct, 2),
            "neckline": neckline,
        },
        "reader_note": note,
    }


def _strict_channel(series: list[dict[str, Any]]) -> dict[str, Any]:
    window = series[-20:]
    highs = [float(bar.get("high") or bar["close"]) for bar in window]
    lows = [float(bar.get("low") or bar["close"]) for bar in window]
    high_slope = _slope(highs)
    low_slope = _slope(lows)
    direction = "neutral"
    name = "Trading Range"
    verdict = "not_detected"
    note = "Highs and lows are not moving in a clear shared direction."
    if high_slope < -0.1 and low_slope < -0.1:
        direction = "bearish"
        name = "Descending Channel"
        verdict = "detected"
        note = "Both swing highs and lows trend downward."
    elif high_slope > 0.1 and low_slope > 0.1:
        direction = "bullish"
        name = "Ascending Channel"
        verdict = "detected"
        note = "Both swing highs and lows trend upward."
    return {
        "pattern_id": name.lower().replace(" ", "_"),
        "pattern_name": name,
        "direction": direction,
        "verdict": verdict,
        "evidence_points": {
            "high_slope": round(high_slope, 4),
            "low_slope": round(low_slope, 4),
        },
        "reader_note": note,
    }


def _strict_candles(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(series) < 3:
        return []
    latest = series[-1]
    prev = series[-2]
    patterns: list[dict[str, Any]] = []

    def candle_metrics(bar: dict[str, Any]) -> tuple[float, float, float, float, bool]:
        open_price = float(bar.get("open") or bar["close"])
        close = float(bar["close"])
        high = float(bar.get("high") or close)
        low = float(bar.get("low") or close)
        body = abs(close - open_price)
        upper = high - max(close, open_price)
        lower = min(close, open_price) - low
        trading_range = high - low
        pct_body = (body / trading_range * 100) if trading_range else 0.0
        return body, upper, lower, pct_body, close >= open_price

    body, upper, lower, pct_body, is_up = candle_metrics(latest)
    prev_body, _prev_upper, _prev_lower, _prev_pct, prev_is_up = candle_metrics(prev)

    if lower > 2 * body and pct_body < 35 and not is_up:
        patterns.append(
            {
                "pattern_id": "hammer",
                "pattern_name": "Hammer",
                "direction": "bullish",
                "verdict": "detected",
                "evidence_points": {"lower_wick": round(lower, 4), "body": round(body, 4)},
                "reader_note": "Latest candle has a long lower wick and small body.",
            }
        )
    if upper > 2 * body and pct_body < 35:
        patterns.append(
            {
                "pattern_id": "shooting_star",
                "pattern_name": "Shooting Star",
                "direction": "bearish",
                "verdict": "detected",
                "evidence_points": {"upper_wick": round(upper, 4), "body": round(body, 4)},
                "reader_note": "Latest candle has a long upper wick and small body.",
            }
        )
    if pct_body > 70:
        patterns.append(
            {
                "pattern_id": "marubozu_bullish" if is_up else "marubozu_bearish",
                "pattern_name": "Marubozu Bullish" if is_up else "Marubozu Bearish",
                "direction": "bullish" if is_up else "bearish",
                "verdict": "detected",
                "evidence_points": {"body_pct": round(pct_body, 2)},
                "reader_note": "Latest candle closes with a dominant real body.",
            }
        )
    if not prev_is_up and is_up:
        prev_open = float(prev.get("open") or prev["close"])
        prev_close = float(prev["close"])
        latest_open = float(latest.get("open") or latest["close"])
        latest_close = float(latest["close"])
        if latest_close > prev_open and latest_open < prev_close and body > prev_body:
            patterns.append(
                {
                    "pattern_id": "bullish_engulfing",
                    "pattern_name": "Bullish Engulfing",
                    "direction": "bullish",
                    "verdict": "detected",
                    "reader_note": "Current candle engulfs the prior down candle.",
                }
            )
    if prev_is_up and not is_up:
        prev_open = float(prev.get("open") or prev["close"])
        prev_close = float(prev["close"])
        latest_open = float(latest.get("open") or latest["close"])
        latest_close = float(latest["close"])
        if latest_close < prev_open and latest_open > prev_close and body > prev_body:
            patterns.append(
                {
                    "pattern_id": "bearish_engulfing",
                    "pattern_name": "Bearish Engulfing",
                    "direction": "bearish",
                    "verdict": "detected",
                    "reader_note": "Current candle engulfs the prior up candle.",
                }
            )
    return patterns


def _strict_rsi_divergence(series: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [float(bar["close"]) for bar in series]
    rsi_values = _rsi_series(closes)
    _highs, lows = find_swing_points(series)
    if len(lows) < 2:
        return {
            "pattern_id": "rsi_divergence",
            "pattern_name": "RSI Divergence",
            "direction": "neutral",
            "verdict": "not_detected",
            "reader_note": "No two recent swing lows are available for divergence.",
        }
    candidate_pair: tuple[dict[str, Any], dict[str, Any]] | None = None
    for idx in range(len(lows) - 2, -1, -1):
        first = lows[idx]
        second = lows[idx + 1]
        if second["price"] <= first["price"]:
            candidate_pair = (first, second)
            break
    if candidate_pair is None:
        first, second = lows[-2], lows[-1]
    else:
        first, second = candidate_pair
    first_rsi = rsi_values[first["index"]]
    second_rsi = rsi_values[second["index"]]
    if first_rsi is None or second_rsi is None:
        return {
            "pattern_id": "rsi_divergence",
            "pattern_name": "RSI Divergence",
            "direction": "neutral",
            "verdict": "not_detected",
            "reader_note": "RSI history is not long enough for divergence.",
        }
    if second["price"] < first["price"] and second_rsi > first_rsi:
        return {
            "pattern_id": "rsi_bullish_divergence",
            "pattern_name": "RSI Bullish Divergence",
            "direction": "bullish",
            "verdict": "detected",
            "evidence_points": {
                "first_low": first,
                "second_low": second,
                "first_rsi": first_rsi,
                "second_rsi": second_rsi,
            },
            "reader_note": "Price made a lower low while RSI made a higher low.",
        }
    return {
        "pattern_id": "rsi_divergence",
        "pattern_name": "RSI Divergence",
        "direction": "neutral",
        "verdict": "not_detected",
        "evidence_points": {
            "first_low": first,
            "second_low": second,
            "first_rsi": first_rsi,
            "second_rsi": second_rsi,
        },
        "reader_note": "Price and RSI did not diverge at the last two swing lows.",
    }


def detect_pattern_evidence(series: list[dict[str, Any]]) -> dict[str, Any]:
    patterns = [
        _strict_double_bottom(series),
        _strict_channel(series),
        *_strict_candles(series),
        _strict_rsi_divergence(series),
    ]
    return {
        "lookback_window": f"{len(series)}_bars_daily",
        "detected_patterns": patterns,
    }


def _setup_status(score: float, distance_pct: float | None) -> str:
    if score >= 78 and distance_pct is not None and distance_pct <= 3:
        return "near_confirmation"
    if score >= 62:
        return "forming"
    return "not_clean"


def _setup_note(pattern_name: str, status: str, distance: float | None) -> str:
    if status == "near_confirmation":
        return f"{pattern_name} is near its confirmation zone and still needs a decisive close above it."
    if status == "forming":
        return f"{pattern_name} is forming but not confirmed."
    suffix = f" It remains about {distance:.2f}% below confirmation." if distance is not None else ""
    return f"{pattern_name} is not clean enough yet.{suffix}"


def _setup(
    pattern_id: str,
    pattern_name: str,
    score: float,
    confirmation_price: float | None,
    watch_low: float | None,
    watch_high: float | None,
    current_close: float,
) -> dict[str, Any] | None:
    final_score = round(_clamp(score), 2)
    if final_score < 55:
        return None
    distance = (
        max(0.0, _pct(confirmation_price, current_close))
        if confirmation_price is not None
        else None
    )
    status = _setup_status(final_score, distance)
    return {
        "pattern_id": pattern_id,
        "pattern_name": pattern_name,
        "family": pattern_family(pattern_id),
        "setup_status": status,
        "completion_score": final_score,
        "confirmation_price": round(confirmation_price, 4) if confirmation_price is not None else None,
        "watch_zone": {
            "low": round(watch_low, 4) if watch_low is not None else None,
            "high": round(watch_high, 4) if watch_high is not None else None,
        },
        "current_price": round(current_close, 4),
        "distance_to_confirmation_pct": round(distance, 2) if distance is not None else None,
        "reader_note": _setup_note(pattern_name, status, distance),
    }


def _detect_bull_flag(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    current = float(rows[-1]["close"])
    recent = rows[-14:]
    pole = rows[-44:-14]
    if len(pole) < 20:
        return None
    pole_move = _pct(max(float(r["close"]) for r in pole[-5:]), min(float(r["close"]) for r in pole[:15]))
    recent_high = max(float(r.get("high") or r["close"]) for r in recent)
    recent_low = min(float(r.get("low") or r["close"]) for r in recent)
    recent_range = _pct(recent_high, recent_low)
    pullback = _pct(recent_high, current)
    score = 30 + min(pole_move, 35) + max(0, 25 - recent_range) * 2.2 - max(0, pullback - 8) * 2
    if pole_move < 10 or recent_range > 16:
        score -= 20
    return _setup("bull_flags", "Bull Flag", score, recent_high, recent_low, recent_high, current)


def _detect_ascending_triangle(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    current = float(rows[-1]["close"])
    window = rows[-45:]
    highs = [float(r.get("high") or r["close"]) for r in window]
    lows = [float(r.get("low") or r["close"]) for r in window]
    resistance = sorted(highs)[int(len(highs) * 0.8)]
    high_spread = _pct(max(highs[-25:]), min(highs[-25:]))
    low_rise = _pct(min(lows[-10:]), min(lows[:15]))
    distance = max(0.0, _pct(resistance, current))
    score = 45 + min(max(low_rise, 0), 18) * 1.8 + max(0, 8 - high_spread) * 3 - distance * 1.5
    return _setup("triangles_ascending", "Ascending Triangle", score, resistance, min(lows[-20:]), resistance, current)


def _detect_falling_wedge(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    current = float(rows[-1]["close"])
    window = rows[-40:]
    highs = [float(r.get("high") or r["close"]) for r in window]
    lows = [float(r.get("low") or r["close"]) for r in window]
    high_slope = _slope(highs)
    low_slope = _slope(lows)
    width_start = max(highs[:10]) - min(lows[:10])
    width_end = max(highs[-10:]) - min(lows[-10:])
    narrows = 1 - width_end / width_start if width_start > 0 else 0
    upper_now = highs[0] + high_slope * (len(highs) - 1)
    distance = max(0.0, _pct(upper_now, current)) if upper_now > 0 else None
    score = 40 + _clamp(narrows * 60, 0, 35) + (12 if high_slope < 0 and low_slope < 0 else -15) - (distance or 0) * 1.2
    return _setup("wedges_falling", "Falling Wedge", score, upper_now, min(lows[-15:]), upper_now, current)


def _detect_double_bottom_setup(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    current = float(rows[-1]["close"])
    window = rows[-65:]
    lows = [float(r.get("low") or r["close"]) for r in window]
    if len(lows) < 40:
        return None
    first_i = min(range(0, 32), key=lambda idx: lows[idx])
    second_i = min(range(32, len(lows)), key=lambda idx: lows[idx])
    first_low = lows[first_i]
    second_low = lows[second_i]
    low_gap = abs(_pct(max(second_low, first_low), min(second_low, first_low)))
    neckline = max(float(r.get("high") or r["close"]) for r in window[first_i:second_i + 1])
    distance = max(0.0, _pct(neckline, current))
    separation = second_i - first_i
    score = 48 + max(0, 8 - low_gap) * 4 + min(separation, 30) * 0.5 - distance * 1.5
    if separation < 12:
        score -= 15
    return _setup("double_bottoms", "Double Bottom", score, neckline, min(first_low, second_low), neckline, current)


def pattern_family(pattern_id: str) -> str:
    if pattern_id in {"bull_flags", "bull_pennants", "measured_move_up"}:
        return "trend_following"
    if pattern_id in {"triangles_ascending", "rectangle_bottoms", "cup_with_handle"}:
        return "accumulation_breakout"
    if "bottom" in pattern_id or "wedge" in pattern_id:
        return "reversal_or_recovery"
    return "mixed"


def detect_pattern_setups(series: list[dict[str, Any]]) -> dict[str, Any]:
    detectors = (
        _detect_bull_flag,
        _detect_ascending_triangle,
        _detect_falling_wedge,
        _detect_double_bottom_setup,
    )
    setups = [candidate for detector in detectors if (candidate := detector(series)) is not None]
    setups.sort(
        key=lambda item: (
            -float(item["completion_score"]),
            float(item.get("distance_to_confirmation_pct") or 999),
            item["pattern_name"],
        )
    )
    family_counts: dict[str, int] = {}
    for setup in setups:
        family_counts[setup["family"]] = family_counts.get(setup["family"], 0) + 1
    archetype = max(family_counts, key=family_counts.get) if family_counts else None
    return {
        "lookback_window": f"{len(series)}_bars_daily",
        "setups": setups[:6],
        "archetype": archetype,
    }
