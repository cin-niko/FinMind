# Pattern Scoring — 8 setup heuristics + family + archetype

> ✅ **PORTABLE — runs 100% on pure vnstock**
>
> This file contains the pattern-scoring portion with no external dependencies. Only daily OHLCV from vnstock is needed to compute everything.
>
> The 8-setup heuristic methodology (ported to Python, self-contained).
> Philosophy: **"A structure that is still forming is only a structure to observe, not a buy/sell signal."** (non_advice_boundary)

## Contents
1. [Shared helpers](#helpers)
2. [8 setup-detection heuristics (upside)](#setups)
3. [Setup status + reader_note](#status)
4. [5 pattern-family classification](#family)
5. [Stock archetype](#archetype)

---

## Shared helpers <a name="helpers"></a>

Standard helpers (numeric handling + linear-regression slope) used by both setups and pattern scoring.

```python
import math

def finite(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None

def pct(a, b):
    """(a/b - 1) * 100. b=0 -> 0.0."""
    return (a/b - 1) * 100 if b else 0.0

def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))

def slope(values):
    """Slope (linear regression) through values."""
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    denom = sum((i - x_mean) ** 2 for i in range(n)) or 1
    return sum((i - x_mean) * (value - y_mean) for i, value in enumerate(values)) / denom
```

---

## 8 setup-detection heuristics <a name="setups"></a>

Detects **UPSIDE patterns only**. Each function returns a dict via `setup()` (see [Status](#status)).

Input: `rows` = daily OHLCV; needs ≥75 sessions for cup_with_handle, ≥65 for the others.

```python
def detect_bull_flag(rows):
    """Bull flag. Pole = prior 30 sessions, flag = last 14 sessions."""
    current = rows[-1]["close"]
    recent = rows[-14:]
    pole = rows[-44:-14]
    if len(pole) < 20:
        return None
    pole_move = pct(max(r["close"] for r in pole[-5:]), min(r["close"] for r in pole[:15]))
    recent_high = max(r["high"] for r in recent)
    recent_low = min(r["low"] for r in recent)
    recent_range = pct(recent_high, recent_low)
    pullback = pct(recent_high, current)
    compact = max(0, 25 - recent_range) * 2.2
    score = 30 + min(pole_move, 35) + compact - max(0, pullback - 8) * 2
    if pole_move < 10 or recent_range > 16:
        score -= 20
    return setup("bull_flags", "Bull flag", score, recent_high, recent_low, recent_high, current,
                 "Needs a clear prior leading leg and a rest that is not too wide.")

def detect_bull_pennant(rows):
    """Bull pennant. Range compression over the last 12 sessions."""
    current = rows[-1]["close"]
    recent = rows[-12:]
    prior = rows[-42:-12]
    if len(prior) < 20:
        return None
    prior_move = pct(max(r["close"] for r in prior[-5:]), min(r["close"] for r in prior[:15]))
    first_range = max(r["high"] for r in recent[:6]) - min(r["low"] for r in recent[:6])
    last_range = max(r["high"] for r in recent[-6:]) - min(r["low"] for r in recent[-6:])
    compression = 1 - (last_range / first_range) if first_range > 0 else 0
    recent_high = max(r["high"] for r in recent)
    recent_low = min(r["low"] for r in recent)
    score = 35 + min(prior_move, 30) + clamp(compression * 55, 0, 35) - max(0, pct(recent_high, recent_low) - 14) * 2
    if prior_move < 10:
        score -= 18
    return setup("bull_pennants", "Bull pennant", score, recent_high, recent_low, recent_high, current,
                 "Needs the range to compress, not just drift sideways wide.")

def detect_ascending_triangle(rows):
    """Ascending triangle. Flat resistance + rising lows."""
    current = rows[-1]["close"]
    window = rows[-45:]
    highs = [r["high"] for r in window]
    lows = [r["low"] for r in window]
    resistance = sorted(highs)[int(len(highs) * 0.8)]
    high_spread = pct(max(highs[-25:]), min(highs[-25:]))
    low_rise = pct(min(lows[-10:]), min(lows[:15]))
    distance = max(0.0, pct(resistance, current))
    score = 45 + min(max(low_rise, 0), 18) * 1.8 + max(0, 8 - high_spread) * 3 - distance * 1.5
    return setup("triangles_ascending", "Ascending triangle", score, resistance, min(lows[-20:]), resistance, current,
                 "Needs sufficiently flat resistance and later lows higher than earlier lows.")

def detect_falling_wedge(rows):
    """Falling wedge. Both edges slope down + converge."""
    current = rows[-1]["close"]
    window = rows[-40:]
    highs = [r["high"] for r in window]
    lows = [r["low"] for r in window]
    high_slope = slope(highs)
    low_slope = slope(lows)
    width_start = max(highs[:10]) - min(lows[:10])
    width_end = max(highs[-10:]) - min(lows[-10:])
    narrows = 1 - width_end / width_start if width_start > 0 else 0
    upper_now = highs[0] + high_slope * (len(highs) - 1)
    distance = max(0.0, pct(upper_now, current)) if upper_now > 0 else None
    score = 40 + clamp(narrows * 60, 0, 35) + (12 if high_slope < 0 and low_slope < 0 else -15) - (distance or 0) * 1.2
    return setup("wedges_falling", "Falling wedge", score, upper_now, min(lows[-15:]), upper_now, current,
                 "Needs both edges sloping down and the width narrowing.")

def detect_cup_with_handle(rows):
    """Cup and handle. Needs >=75 sessions. Cup depth ~25%, shallow handle."""
    if len(rows) < 75:
        return None
    current = rows[-1]["close"]
    window = rows[-90:]
    closes = [r["close"] for r in window]
    left_high = max(closes[:30])
    cup_low = min(closes[20:70])
    right_high = max(closes[55:])
    depth = pct(left_high, cup_low)
    recovery = pct(right_high, cup_low)
    handle = rows[-15:]
    handle_pullback = pct(max(r["high"] for r in handle), min(r["low"] for r in handle))
    confirmation = max(left_high, right_high)
    score = 35 + min(recovery, 35) + max(0, 35 - abs(depth - 25)) - max(0, handle_pullback - 16) * 2
    if depth < 12 or depth > 50:
        score -= 18
    return setup("cup_with_handle", "Cup and handle", score, confirmation,
                 min(r["low"] for r in handle), confirmation, current,
                 "Long pattern; noisy if the handle is too deep or recovery is insufficient.")

def detect_rectangle_bottom(rows):
    """Rectangle bottom. A clear sideways band after a decline."""
    current = rows[-1]["close"]
    window = rows[-35:]
    prior = rows[-75:-35]
    high = max(r["high"] for r in window)
    low = min(r["low"] for r in window)
    range_pct = pct(high, low)
    prior_drop = pct(prior[0]["close"], min(r["close"] for r in prior)) if prior else 0
    distance = max(0.0, pct(high, current))
    score = 42 + max(0, 18 - abs(range_pct - 12)) * 2 + min(max(prior_drop, 0), 18) - distance
    return setup("rectangle_bottoms", "Rectangle bottom", score, high, low, high, current,
                 "Needs a sufficiently clear sideways band after a decline or accumulation.")

def detect_double_bottom(rows):
    """Double bottom. Separation >=12 sessions, mismatch <8%."""
    current = rows[-1]["close"]
    window = rows[-65:]
    lows = [r["low"] for r in window]
    first_i = min(range(0, 32), key=lambda idx: lows[idx])
    second_i = min(range(32, len(lows)), key=lambda idx: lows[idx])
    first_low = lows[first_i]
    second_low = lows[second_i]
    low_gap = abs(pct(second_low, first_low))
    neckline = max(r["high"] for r in window[first_i:second_i + 1])
    distance = max(0.0, pct(neckline, current))
    separation = second_i - first_i
    score = 48 + max(0, 8 - low_gap) * 4 + min(separation, 30) * 0.5 - distance * 1.5
    if separation < 12:
        score -= 15
    return setup("double_bottoms", "Double bottom", score, neckline, min(first_low, second_low), neckline, current,
                 "The two lows need enough separation and must not differ too much.")

def detect_measured_move_up(rows):
    """Measured move up. Leg + measured pullback."""
    if len(rows) < 65:
        return None
    recent = rows[-65:]
    first = recent[:30]
    pullback = recent[30:50]
    leg_low = min(r["low"] for r in first)
    leg_high = max(r["high"] for r in first)
    leg_move = pct(leg_high, leg_low)
    pull_low = min(r["low"] for r in pullback)
    retrace = (leg_high - pull_low) / (leg_high - leg_low) * 100 if leg_high > leg_low else 100
    confirmation = max(r["high"] for r in recent)
    score = 38 + min(leg_move, 30) + max(0, 30 - abs(retrace - 50)) - max(0, pct(confirmation, current)) * 1.2
    if leg_move < 12 or retrace < 25 or retrace > 75:
        score -= 18
    return setup("measured_move_up", "Measured move up", score, confirmation, pull_low, confirmation, current,
                 "Needs a clear leading leg, a moderate correction, and not yet falling into a chop zone.")

DETECTORS = [detect_bull_flag, detect_bull_pennant, detect_ascending_triangle,
             detect_falling_wedge, detect_cup_with_handle, detect_rectangle_bottom,
             detect_double_bottom, detect_measured_move_up]

def scan_setups(rows):
    """Run all detectors, sort by score desc. Return top 6."""
    candidates = [d(rows) for d in DETECTORS]
    candidates = [c for c in candidates if c]  # drop None
    candidates.sort(key=lambda c: (-float(c["completion_score"]),
                                    float(c.get("distance_to_confirmation_pct") or 999),
                                    c["pattern_name"]))
    return candidates[:6]
```

---

## Setup status + reader_note <a name="status"></a>



```python
def status_from_score(score, distance_pct, noisy=False):
    """Return one of: 'near_confirmation' / 'forming' / 'not_clean' / 'noisy'."""
    if noisy:
        return "noisy"
    if score >= 78 and distance_pct is not None and distance_pct <= 3:
        return "near_confirmation"
    if score >= 62:
        return "forming"
    return "not_clean"

def setup(pattern_id, pattern_name, score, confirmation_price, watch_low, watch_high,
          current_close, caution, status=None):
    """Wrap one setup candidate. Score <55 -> None (dropped)."""
    score = round(clamp(score), 2)
    if score < 55:
        return None
    distance = max(0.0, pct(confirmation_price, current_close)) if confirmation_price else None
    final_status = status or status_from_score(score, distance)
    return {
        "pattern_id": pattern_id,
        "pattern_name": pattern_name,
        "setup_status": final_status,
        "completion_score": score,
        "confirmation_price": round(confirmation_price, 4) if confirmation_price is not None else None,
        "watch_zone": {
            "low": round(watch_low, 4) if watch_low is not None else None,
            "high": round(watch_high, 4) if watch_high is not None else None,
        },
        "distance_to_confirmation_pct": round(distance, 2) if distance is not None else None,
        "caution_reason": caution,
        "reader_note": reader_note(pattern_name, final_status, distance),
    }

def reader_note(pattern_name, status, distance):
    """Four narrative templates by status."""
    if status == "near_confirmation":
        return f"{pattern_name} is near the confirmation zone; still wait for a closing break above the watch level."
    if status == "forming":
        return f"{pattern_name} has an observable structure but does not yet meet confirmation conditions."
    if status == "noisy":
        return f"{pattern_name} has a few traits of the pattern but the price action is still noisy."
    suffix = f", about {distance:.2f}% from the confirmation zone" if distance is not None else ""
    return f"{pattern_name} is not clean enough to read strongly{suffix}."
```

**Score-threshold summary:**
| Score | Status | Meaning |
|---|---|---|
| < 55 | (dropped) | Not worth attention |
| 55-61 | not_clean | Weak structure, far from confirmation |
| 62-77 | forming | Worth observing, not confirmed |
| ≥78 & dist≤3% | near_confirmation | Near confirmation, awaiting breakout |

---

## 5 pattern-family classification <a name="family"></a>

Map pattern_id → family. **Portable** (dict lookup only).

```python
CONTINUATION_PATTERNS = {
    "bull_flags", "bull_pennants", "high_tight_flags", "measured_move_up",
    "continuation_gaps", "rising_three_methods",
}
ACCUMULATION_PATTERNS = {
    "triangles_ascending", "triangles_symmetrical", "rectangle_bottoms",
    "cup_with_handle", "double_bottoms_adam_adam", "double_bottoms_adam_eve",
    "double_bottoms_eve_adam", "double_bottoms_eve_eve", "triple_bottoms",
    "pipe_bottoms", "rounding_bottoms",
}
DOWNSIDE_PATTERNS = {
    "bear_flags", "bear_pennants", "triangles_descending", "rectangle_tops",
    "head_and_shoulders_tops", "head_and_shoulders_tops_complex",
    "measured_move_down", "pipe_tops", "horn_tops", "diamond_tops",
    "three_falling_peaks", "triple_tops", "bump_and_run_reversal_tops",
    "falling_three_methods", "cup_with_handle_inverted",
}

def pattern_family(pattern_id):
    """Return one of 5: trend_following / accumulation_breakout / defensive_caution / reversal_or_recovery / mixed."""
    if pattern_id in CONTINUATION_PATTERNS:
        return "trend_following"
    if pattern_id in ACCUMULATION_PATTERNS:
        return "accumulation_breakout"
    if pattern_id in DOWNSIDE_PATTERNS:
        return "defensive_caution"
    if "bottom" in pattern_id or "valleys" in pattern_id:
        return "reversal_or_recovery"
    if "top" in pattern_id or "peaks" in pattern_id:
        return "defensive_caution"
    return "mixed"
```

---

## Stock archetype <a name="archetype"></a>

Classify a stock by its dominant behavior tendency, inferred from the current setup + high-volume behavior. Uses OHLCV data only.

```python
def estimate_archetype(setups, high_volume_behavior):
    """Classify archetype from the current setup + high-volume behavior.
    `setups` = output of scan_setups(); `high_volume_behavior` = block B14 from stock_profile_blocks.md.
    Returns {primary, reader_note}."""
    families = [pattern_family(s["pattern_id"]) for s in setups]
    hv_label = high_volume_behavior.get("post_high_volume_label", "") if high_volume_behavior else ""
    if not setups:
        return {"primary": "no_current_setup",
                "reader_note": "No clear upside setup among the heuristic patterns; read session by session."}
    if "trend_following" in families:
        return {"primary": "trend_following",
                "reader_note": "Current setup leans continuation; read primarily by trend-retention strength."}
    if "accumulation_breakout" in families:
        return {"primary": "accumulation_breakout",
                "reader_note": "Current setup leans accumulation; read carefully at the session that confirms a base breakout."}
    if "weakening" in hv_label:
        return {"primary": "trap_prone",
                "reader_note": "Post-high-volume behavior is weakening; be cautious of false breakouts."}
    return {"primary": "mixed",
            "reader_note": "Current setup is mixed; read each specific structure on its own."}
```

**Four-archetype table:**
| Primary | When | Read as |
|---|---|---|
| `trend_following` | a setup belongs to the trend_following family | Prioritize continuation momentum and trend-retention strength |
| `accumulation_breakout` | a setup belongs to the accumulation_breakout family | Read the accumulation base + the session that confirms the base breakout |
| `trap_prone` | post-high-volume behavior is weakening | Be cautious of false breakouts |
| `mixed` | no rule matches | Read each specific structure on its own |
| `no_current_setup` | no setup at all | Read session by session |

> **Guardrail**: the archetype only describes an observable historical behavior tendency; it is not a forecast or a fixed classification label.
