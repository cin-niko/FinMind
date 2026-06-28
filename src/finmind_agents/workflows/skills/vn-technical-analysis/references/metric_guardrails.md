# Metric Dictionary & Non-Advice Guardrails

> Reference for **PROFILE mode** — `neutral_descriptive_non_advice` language. Methodology from an internal market-analysis dashboard (ported to Python, self-contained).
>
> **Supreme rule:** Every profile-mode output DESCRIBES the past; it is not a signal, forecast, or recommendation.

## Contents
1. [15-metric dictionary](#dict) — definition + guardrail per metric
2. [Evaluation thresholds](#thresholds)
3. [CONSUMER_LABELS](#labels) — map technical status → readable label
4. [scrubCopy rules](#scrub) — clean text before output
5. [Four non-conclusion points](#nonconclusion) — REQUIRED at the end of every report
6. [Standard terminology table](#translate)
7. [Forbidden language list](#forbidden)
8. [Term glossary](#glossary)

---

## 15-metric dictionary <a name="dict"></a>

Methodology: 13 metrics, each with 4 fields (label + formula + meaning + guardrail). When presenting a metric you MUST also state its guardrail.

```python
def metric_dictionary():
    return {
        "return": {
            "label": "Return",
            "formula": "close_t / close_{t-window} - 1",
            "meaning": "How much the price rose or fell over the selected window.",
            "guardrail": "Not a forecast; only describes what already happened.",
        },
        "relative_return": {
            "label": "Relative return",
            "formula": "return_object - return_benchmark",
            "meaning": "The gap in return versus VNINDEX, the sector, or the current basket.",
            "guardrail": "A positive number is not meaningful in isolation from the benchmark; it only means it did better over the window.",
        },
        "moving_average_distance": {
            "label": "Distance from moving average",
            "formula": "close_t / moving_average_n - 1",
            "meaning": "How far the current price sits above or below the recent price plane.",
            "guardrail": "Not a buy/sell signal.",
        },
        "breadth": {
            "label": "Breadth",
            "formula": "count(condition_true) / eligible_count",
            "meaning": "The share of tickers that are rising together or standing above a moving average.",
            "guardrail": "This is a count of tickers, not a measure of move size.",
        },
        "dispersion": {
            "label": "Dispersion",
            "formula": "std(cross_section_returns)",
            "meaning": "How much returns differ across tickers within the same group.",
            "guardrail": "High or low is not inherently good/bad; read it alongside breadth.",
        },
        "liquidity": {
            "label": "Liquidity",
            "formula": "close * volume; ratio = volume_t / average_volume_window",
            "meaning": "Trading activity by value or volume versus its average.",
            "guardrail": "Trading value is an estimate from close price times volume.",
        },
        "correlation": {
            "label": "Correlation",
            "formula": "corr(return_a, return_b)",
            "meaning": "How much two return series move together in rhythm.",
            "guardrail": "Does not say which series leads and does not prove causation.",
        },
        "beta_r2": {
            "label": "Responsiveness / fit",
            "formula": "beta = cov(stock, benchmark) / var(benchmark); r2 = regression_fit",
            "meaning": "Whether the ticker reacts more or less than the benchmark, plus how readable the comparison is.",
            "guardrail": "Low beta does not mean low risk; with low R² do not read too deeply into beta.",
        },
        "drawdown": {
            "label": "Drawdown from peak",
            "formula": "close_t / rolling_peak - 1",
            "meaning": "How far below the most recent peak the price currently sits.",
            "guardrail": "Sensitive to the observation window and to unadjusted corporate-action data.",
        },
        "rolling_return": {
            "label": "Rolling return",
            "formula": "close_t / close_{t-window} - 1 across all historical windows",
            "meaning": "The distribution of same-length return windows that have occurred in history.",
            "guardrail": "Overlapping windows are not independent observations and are not future probabilities.",
        },
        "historical_episode": {
            "label": "Historical episode",
            "formula": "peak/trough/recovery dates from observed close path",
            "meaning": "Down-legs, recoveries, or trough-to-peak runs within the available sample.",
            "guardrail": "Very sensitive to windowing and to data that is not point-in-time; treat as notes, not statistics.",
        },
        "rolling_percentile": {
            "label": "Rolling percentile",
            "formula": "rank(current) within rolling historical sample",
            "meaning": "Where the current metric sits versus its own full past distribution.",
            "guardrail": "A high percentile only means high relative to its own history, not high in absolute terms.",
        },
        "streak": {
            "label": "Streak",
            "formula": "consecutive up/down sessions count",
            "meaning": "How many sessions in a row the price has risen or fallen.",
            "guardrail": "A long streak is not predictive of continuation or reversal.",
        },
    }
```

---

## Evaluation thresholds <a name="thresholds"></a>

### R² threshold (benchmark fit)
From `ANALYTICS_STANDARD.md:62-71`. This is the **only numerically defined** evaluation threshold.

| R² | Level | Reading behavior |
|---|---|---|
| `< 0.40` | **low** | Beta is not worth a deep read |
| `0.40 – 0.70` | **medium** | Read moderately |
| `> 0.70` | **high** | Beta is trustworthy |

Additional rule: lead-lag/cluster findings must come with coverage/liquidity quality before being surfaced prominently.

### Time windows (4 fixed windows)
From `ANALYTICS_STANDARD.md:24-36`.

| Label | Sessions | Role |
|---|---|---|
| `20D` | 20 | Tactical state, noisy |
| `60D` | 60 | **Default operating window** |
| `120D` | 120 | Structure / relationship context |
| `252D` | 252 | Annual baseline |

> Keep internal fields as `20d/60d/120d/252d`. Display labels may be localized.

---

## CONSUMER_LABELS <a name="labels"></a>

Ported from `web/stock_profile_foundation_module.js:11-90`. Maps technical status → a readable label. Use it when rendering narrative.

```python
CONSUMER_LABELS = {
    # Data confidence status
    "usable": "readable",
    "thin_sample": "thin sample",
    "guardrailed": "needs caution",
    "verified": "verified",
    "missing": "missing data",
    "point_in_time_ready": "enough history",
    "snapshot_only": "current snapshot only",
    # Regime
    "bull": "strong uptrend",
    "bear": "strong downtrend",
    "uptrend": "uptrend",
    "recovery": "recovery",
    "stress": "under pressure",
    "sideways": "sideways",
    "unknown": "insufficient data",
    # Sample label
    "fairly_deep": "fairly deep",
    "reference_grade": "reference grade",
    "sparse": "sparse",
    "thin_sample_label": "thin sample",
    # Behavior / outcome labels
    "clean_continuation": "clean continuation",
    "tends_to_revert": "tends to revert",
    "often_fails": "often fails",
    "moderate_noise": "moderate noise",
    "target_reached": "target reached",
    "notable_counter_move": "notable counter-move",
    "reference_forming": "reference / forming",
    "stronger_than_own_history": "stronger than its own history",
    "needs_caution": "needs caution",
    "neutral": "neutral",
    "no_current_setup": "no current setup",
}

def consumer_label(value):
    """Look up CONSUMER_LABELS; fallback to the raw value."""
    if value in CONSUMER_LABELS:
        return CONSUMER_LABELS[value]
    if value is None:
        return "insufficient data"
    return str(value)
```

---

## scrubCopy rules <a name="scrub"></a>

Ported from `web/stock_history_pattern_module.js:6-17`. Cleans "control-room" phrasing that leaks out of generated data before presenting it.

```python
import re

def scrub_copy(text):
    """Remove technical/internal phrasing before presenting."""
    if not text:
        return text
    replacements = [
        (r"observation window", "20/60/120-session frame"),
        (r"currently tracking\b", "forming"),
        (r"tracking upside", "upside"),
        (r"should read as", ""),  # drop the prescriptive clause
        (r"control[- ]?room", "note"),
    ]
    out = text
    for pattern, repl in replacements:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    return out.strip()
```

---

## Four non-conclusion points <a name="nonconclusion"></a>

Ported from `web/stock_history_academic_module.js:148-163`. REQUIRED at the end of every profile-mode report (rendered into the `non_conclusion` field of the JSON schema).

```python
NON_CONCLUSION_POINTS = [
    "This is not a recommendation or a call to trade.",
    "Past ratios do not guarantee future repetition.",
    "Do not read a basket/sector comparison as complete history if it is only a current snapshot.",
    "Do not use long-horizon results without verifying corporate actions.",
]

def non_conclusion_panel():
    """Return the four points. Must appear at the end of the report."""
    return list(NON_CONCLUSION_POINTS)
```

Points 3 and 4 may be dropped if the profile has no benchmark comparison / corporate-action data — but points 1 and 2 are always present.

---

## Standard terminology table <a name="translate"></a>

When rendering narrative, use the right-hand standard term.

| Source term | Standard term |
|---|---|
| Drawdown | **Drawdown** (from peak) |
| Volume | **Volume** |
| Value | **Trading value** |
| Volatility | **Volatility** |
| Range | **Range** |
| Regime | **Market regime** |
| Outperform / Underperform | **Outperforming / Underperforming** (the benchmark) |
| Hit rate | **Hit rate** |
| Confirmation | **Confirmation** |
| Setup | **Forming setup** |
| Pattern | **Pattern** |

---

## Forbidden language list <a name="forbidden"></a>

Ported from `ANALYTICS_STANDARD.md:83-87`. **PROFILE mode MUST NOT** use these words (only ACTIVE mode uses them):

| ❌ Forbidden (profile mode) | ✅ Use instead |
|---|---|
| bullish / bearish | "rising" / "falling" (descriptive) |
| strong leader | "outperforming the group" |
| worth noting | "observable" / "read with its guardrail" |
| signal | "structure" / "observation" |
| forecast | (do not use — always "describes the past") |
| buy/sell recommendation | (do not use) |
| target price | "historical reference level" |
| imminent breakout | "near the confirmation zone" |
| overbought / oversold | (do not use — active mode only) |
| strong buy / strong sell | (do not use — active mode only) |

> **Note:** ACTIVE mode (MA/RSI/MACD/Tech Score/Verdict) still uses its own language — that is a different use-case; see the main SKILL.md.

---

## Term glossary <a name="glossary"></a>

A ported subset of the help-module glossary. These are the ~30 core terms the skill uses in narrative.

| Term | Short explanation |
|---|---|
| **Trading value** | Estimate = close price × volume (not actual matched value) |
| **Drawdown (from peak)** | How far below the most recent peak the price sits (%) |
| **Rolling return** | The distribution of returns across every same-length window in history |
| **Historical position** | Where the current metric sits versus its full past sample (percentile) |
| **Correlation** | How much two return series move together (−1 to +1) |
| **Responsiveness (beta)** | Whether the ticker moves more or less than the benchmark |
| **Fit (R²)** | How readable beta is; <0.40 = low, >0.70 = high |
| **Outperforming the benchmark** | Ticker return > benchmark return over the window |
| **Above sector median** | Ticker return > median return of same-sector tickers |
| **Above/Below MA20/50/200** | Current price above/below the 20/50/200-session moving average |
| **Dispersion** | Return spread across tickers in a group (cross-sectional std) |
| **Breadth** | Count of tickers participating in a rise/fall (not move size) |
| **Volatility** | Dispersion of historical returns (HV), annualized |
| **14-session range** | Average (high − low) / close over 14 sessions |
| **Streak** | Count of consecutive up/down sessions |
| **52-week high/low** | Highest/lowest price over 252 sessions |
| **Data confidence** | Whether a metric reads solidly or only as a reference |
| **Observation window** | Number of sessions used to compute a metric (20/60/120/252) |
| **Current snapshot** | Basket members/sub-sectors at the current point in time, not historical |
| **Point-in-time** | History by effective date (data limitation, not yet available) |
| **Forming setup** | An unconfirmed pattern; needs a closing break above a level |
| **Confirmation zone** | The price level that must be broken for the pattern to count as confirmed |
| **Completion score** | Cleanliness score of a setup (0-100, <55 = dropped) |
| **Thin sample** | Sample size < 5 events → read only as a note |
| **Post-high-volume behavior** | Average 5d/20d/60d return after a session with volume ≥ 2x avg20 |
| **Effort-result** | Effort = traded volume vs average; Result = price movement |
| **PVI / NVI** | Price index updated on up-volume / down-volume sessions (base=1000) |
| **VAP (volume-at-price)** | Volume distribution by price level (approximated from daily) |
| **VPCI** | Volume Price Confirmation Indicator — degree of price-volume agreement |
| **Money flow (OBV/VPT/CMF)** | Three money-flow-pressure indicators from OHLCV |

---

## Render narrative procedure

When emitting a PROFILE-mode narrative, in order:

1. **Look up `metric_dictionary()`** for each metric used → take `label` + `guardrail`. When presenting numbers, include the matching guardrail.
2. **Look up `CONSUMER_LABELS`** for every technical status (regime, sample_label, behavior_label...) → use the readable label.
3. **Apply `scrub_copy()`** to any text generated from a data template (especially pattern/setup narrative).
4. **Check the `forbidden` list** — do not let "bullish/bearish/signal/recommendation" leak through.
5. **Use the standard terminology** table.
6. **At the end of the report** append `non_conclusion_panel()` (four points; at least points 1 and 2).

```python
def render_profile_narrative(profile_json):
    """PROFILE-mode narrative template. Returns markdown."""
    md = []
    md.append(f"# Stock profile {profile_json['symbol']}\n")
    md.append("*Describes historical price-volume behavior. Not a trade recommendation.*\n")
    # ... render each block using CONSUMER_LABELS + scrub_copy ...
    # End: non-conclusion
    md.append("\n## Reading notes\n")
    for point in non_conclusion_panel():
        md.append(f"- {point}")
    return "\n".join(md)
```
