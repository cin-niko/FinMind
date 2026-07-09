# Pattern Detection — Evidence rules + verdict table

**Core principle:** Only claim a pattern when the data clearly SHOWS it. Do not "search" for a pattern because it would be nice to have — if it is not there, say so plainly.

## Contents
1. [Swing points](#swing)
2. [Double Bottom/Top](#double)
3. [Channel (Ascending/Descending)](#channel)
4. [Candlestick patterns](#candle)
5. [Divergence](#divergence)
6. [Pattern verdict table](#verdict)

---

## Swing points <a name="swing"></a>

Foundation for all chart-pattern detection. A swing high is a candle that is higher than `lookback` candles on each side; a swing low is one that is lower than `lookback` candles on each side.

- `lookback = 2` is the default (a swing point must be higher/lower than 2 candles on each side).
- Increase `lookback` to filter noise on noisy series.

---

## Double Bottom/Top <a name="double"></a>

**Double Bottom** (bullish reversal):
- Two lows (swing lows) are approximately equal (difference < 3%)
- At least 5 weeks apart
- Neckline = the swing high between the two lows

**Evidence rules:**
- Two lows differ < 3% → "POTENTIAL" (not confirmed)
- Two lows differ < 1% → "CLEAR" but still needs a breakout
- Difference > 3% → NOT a double bottom

**Status:**
- `potential`: two lows have formed, neckline not yet broken
- `confirmed`: price has broken above the neckline with volume
- `failed`: price has broken below the second low

**Target** = neckline + (neckline − min(bottom1, bottom2)).

Double Top is the mirror (two swing highs ~ equal, neckline = the swing low between them).

---

## Channel (Ascending/Descending) <a name="channel"></a>

Fit two trendlines through swing highs and swing lows over a recent lookback window (default 20 weeks). Compare the slope of the high line and the low line:

- High slope and low slope both clearly down (e.g. changing by > 100 VND) → **descending channel** (bearish continuation).
- High slope and low slope both clearly up → **ascending channel** (bullish continuation).
- Both slopes near flat (|slope| < 100 VND) → **trading range** (neutral).

**Evidence rule:** Only claim a channel when the slope is clear — highs and lows moving in the same direction by a meaningful amount.

---

## Candlestick patterns <a name="candle"></a>

Per candle, compute:
- `body = abs(close − open)`
- `upper_wick = high − max(close, open)`
- `lower_wick = min(close, open) − low`
- `range = high − low`
- `pct_body = body / range * 100` (0 if range is 0)
- `is_up = close >= open`

**Single-candle patterns:**
- **Hammer** (bullish reversal): lower_wick > 2 × body, pct_body < 35, down candle.
- **Inverted Hammer** (bullish reversal): lower_wick > 2 × body, pct_body < 35, up candle.
- **Shooting Star** (bearish): upper_wick > 2 × body, pct_body < 35.
- **Marubozu** (strong momentum): pct_body > 70 → bullish momentum if up candle, bearish momentum if down candle.
- **Doji** (indecision): pct_body < 10.

**Engulfing patterns (2 candles):**
- **Bullish Engulfing**: previous candle down, current candle up, current close > previous open AND current open < previous close.
- **Bearish Engulfing**: previous candle up, current candle down, current close < previous open AND current open > previous close.

**Three Soldiers / Three Crows (3 candles):**
- **Three White Soldiers**: last 3 candles all up, with each close higher than the previous close → strong bullish reversal.
- **Three Black Crows**: last 3 candles all down, with each close lower than the previous close → strong bearish reversal.

---

## Divergence <a name="divergence"></a>

**CORE rule — only claim it when it is genuinely present.** Compare the two most recent swing lows (need at least 2 swing lows):

- **Bullish divergence:** price fell from swing low 1 to swing low 2, but RSI rose over the same span.
- **Bearish divergence:** price rose from swing low 1 to swing low 2, but RSI fell over the same span.

If price and RSI moved in the same direction at the two most recent lows → **no divergence** — say it plainly. Do not try to manufacture a divergence.

⚠️ **Important:** This is the most abused pattern in technical analysis — many analysts "discover" a divergence on every stock just to have content. This skill commits to honesty: if the rule is not satisfied, state "NO divergence".

---

## Pattern verdict table <a name="verdict"></a>

| Pattern | Signal | Strength | Confirmation needed |
|---|---|---|---|
| Double Bottom (confirmed) | Bullish reversal | Very strong | Neckline breakout + volume |
| Double Bottom (potential) | Potential bullish | Moderate | Wait for breakout |
| Descending Channel | Bearish continuation | Strong | Break above upper trendline |
| Ascending Channel | Bullish continuation | Strong | Hold until break of lower trendline |
| Hammer | Bullish reversal | Moderate | Confirm with a green candle next week |
| Shooting Star | Bearish | Moderate | Confirm with a red candle next week |
| Marubozu bullish | Bullish momentum | Strong | Rising volume |
| Marubozu bearish | Bearish momentum | Strong | Rising volume |
| Bullish Engulfing | Strongly bullish | Strong | Rising volume |
| Three White Soldiers | Strong bullish reversal | Very strong | Gradually rising volume |
| RSI Bullish Divergence | Bullish reversal | Very strong | Confirm with MACD divergence |
| RSI Bearish Divergence | Bearish reversal | Very strong | Confirm with MACD divergence |

**Always combine patterns with:**
1. Volume (rising volume at a key point = stronger confirmation)
2. Support/Resistance (a pattern at support/resistance = stronger)
3. Larger trend (a counter-trend pattern needs stronger evidence)
4. Multiple timeframes (confirm on both weekly and daily)
