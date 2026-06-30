"""Deterministic technical-indicator computation from OHLCV series.

All functions are pure-Python and operate on a list of daily bars.  The
output is a flat dict of *latest* indicator values plus a short price
summary, suitable for passing to the LLM skill as a single record.
"""

from __future__ import annotations

import math
from typing import Any


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema(values: list[float], period: int) -> list[float] | None:
    if not values:
        return None
    k = 2 / (period + 1)
    out = [values[0]]
    for i in range(1, len(values)):
        out.append(values[i] * k + out[-1] * (1 - k))
    return out


def _vwma(closes: list[float], volumes: list[float], period: int = 20) -> float | None:
    if len(closes) < period:
        return None
    pv = sum(closes[-period:][k] * volumes[-period:][k] for k in range(period))
    vol_sum = sum(volumes[-period:])
    if vol_sum == 0:
        return None
    return pv / vol_sum


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) <= period:
        return None
    avg_gain = 0.0
    avg_loss = 0.0
    for i in range(1, period + 1):
        ch = closes[i] - closes[i - 1]
        if ch > 0:
            avg_gain += ch
        else:
            avg_loss += abs(ch)
    avg_gain /= period
    avg_loss /= period
    for i in range(period + 1, len(closes)):
        ch = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + (ch if ch > 0 else 0)) / period
        avg_loss = (avg_loss * (period - 1) + (abs(ch) if ch < 0 else 0)) / period
    if avg_loss == 0:
        return 100.0
    return round(100 - 100 / (1 + avg_gain / avg_loss), 2)


def _macd(closes: list[float]) -> dict[str, float | None]:
    if len(closes) < 35:
        return {"macd_line": None, "signal_line": None, "histogram": None}
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    if not ema12 or not ema26:
        return {"macd_line": None, "signal_line": None, "histogram": None}
    macd_line = [a - b for a, b in zip(ema12, ema26)]
    signal = _ema(macd_line, 9)
    if not signal:
        return {"macd_line": None, "signal_line": None, "histogram": None}
    macd_val = round(macd_line[-1], 4)
    signal_val = round(signal[-1], 4)
    return {
        "macd_line": macd_val,
        "signal_line": signal_val,
        "histogram": round(macd_val - signal_val, 4),
    }


def _bollinger(closes: list[float], period: int = 20, std_mult: float = 2.0) -> dict[str, float | None]:
    if len(closes) < period:
        return {"upper": None, "middle": None, "lower": None}
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((v - middle) ** 2 for v in window) / period
    std = math.sqrt(variance)
    return {
        "upper": round(middle + std_mult * std, 4),
        "middle": round(middle, 4),
        "lower": round(middle - std_mult * std, 4),
    }


def _atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    if len(closes) <= period:
        return None
    trs: list[float] = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    if len(trs) < period:
        return None
    return round(sum(trs[-period:]) / period, 4)


def _max_drawdown(closes: list[float]) -> dict[str, float | None]:
    if not closes:
        return {"max_drawdown_pct": None, "current_drawdown_pct": None}
    peak = closes[0]
    max_dd = 0.0
    for price in closes:
        if price > peak:
            peak = price
        dd = (peak - price) / peak * 100 if peak else 0
        if dd > max_dd:
            max_dd = dd
    current_peak = max(closes)
    current_dd = (current_peak - closes[-1]) / current_peak * 100 if current_peak else 0
    return {
        "max_drawdown_pct": round(max_dd, 2),
        "current_drawdown_pct": round(current_dd, 2),
    }


def _support_resistance(closes: list[float], highs: list[float], lows: list[float], lookback: int = 60) -> dict[str, float | None]:
    window = min(lookback, len(closes))
    if window < 5:
        return {"resistance": None, "support": None}
    return {
        "resistance": round(max(highs[-window:]), 4),
        "support": round(min(lows[-window:]), 4),
    }


def compute_indicators(series: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute technical indicators from an OHLCV series.

    ``series`` is a list of dicts with at least ``close``, ``high``, ``low``,
    ``volume`` and ``date`` keys.  Returns a flat dict of latest indicator
    values plus a price summary.
    """
    if not series:
        return {}
    closes = [float(bar["close"]) for bar in series if bar.get("close") is not None]
    highs = [float(bar.get("high") or bar["close"]) for bar in series]
    lows = [float(bar.get("low") or bar["close"]) for bar in series]
    volumes = [float(bar.get("volume") or 0) for bar in series]
    dates = [bar.get("date", "") for bar in series]

    if not closes:
        return {}

    latest_close = closes[-1]
    sma20 = _sma(closes, 20)
    sma50 = _sma(closes, 50)
    sma200 = _sma(closes, 200)
    ema10_list = _ema(closes, 10)
    ema12_list = _ema(closes, 12)
    ema26_list = _ema(closes, 26)
    vwma20 = _vwma(closes, volumes, 20)

    # 52-week high/low (~250 trading days)
    window_52w = min(250, len(closes))
    high_52w = max(highs[-window_52w:]) if window_52w else None
    low_52w = min(lows[-window_52w:]) if window_52w else None

    # 1-year return
    year_ago = max(len(closes) - 250, 0)
    return_1y_pct = (
        round((closes[-1] - closes[year_ago]) / closes[year_ago] * 100, 2)
        if year_ago > 0 and closes[year_ago]
        else None
    )

    # Volume
    avg_vol_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None
    latest_vol = volumes[-1] if volumes else None
    volume_ratio = (
        round(latest_vol / avg_vol_20, 2) if avg_vol_20 and avg_vol_20 > 0 else None
    )

    # Trend classification
    trend = "sideways"
    if sma20 and sma50:
        if latest_close > sma20 > sma50:
            trend = "uptrend"
        elif latest_close < sma20 < sma50:
            trend = "downtrend"

    dd = _max_drawdown(closes)
    bb = _bollinger(closes)
    macd = _macd(closes)
    sr = _support_resistance(closes, highs, lows)

    return {
        "latest_close": round(latest_close, 4),
        "latest_date": dates[-1] if dates else None,
        "high_52w": round(high_52w, 4) if high_52w else None,
        "low_52w": round(low_52w, 4) if low_52w else None,
        "return_1y_pct": return_1y_pct,
        "sma20": round(sma20, 4) if sma20 else None,
        "sma50": round(sma50, 4) if sma50 else None,
        "sma200": round(sma200, 4) if sma200 else None,
        "ema10": round(ema10_list[-1], 4) if ema10_list else None,
        "ema12": round(ema12_list[-1], 4) if ema12_list else None,
        "ema26": round(ema26_list[-1], 4) if ema26_list else None,
        "vwma20": round(vwma20, 4) if vwma20 else None,
        "rsi14": _rsi(closes, 14),
        "macd_line": macd["macd_line"],
        "macd_signal": macd["signal_line"],
        "macd_histogram": macd["histogram"],
        "bollinger_upper": bb["upper"],
        "bollinger_middle": bb["middle"],
        "bollinger_lower": bb["lower"],
        "atr14": _atr(highs, lows, closes, 14),
        "avg_volume_20d": round(avg_vol_20) if avg_vol_20 else None,
        "latest_volume": round(latest_vol) if latest_vol else None,
        "volume_ratio": volume_ratio,
        "trend": trend,
        "max_drawdown_pct": dd["max_drawdown_pct"],
        "current_drawdown_pct": dd["current_drawdown_pct"],
        "resistance": sr["resistance"],
        "support": sr["support"],
        "bar_count": len(closes),
        "start_date": dates[0] if dates else None,
        "end_date": dates[-1] if dates else None,
    }
