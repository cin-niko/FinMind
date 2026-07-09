# Technical Indicators — Formulas + Code

Python reference implementations of the indicator formulas. Use these to compute values from collected OHLCV records and interpret the result.

## Contents
1. [Moving Averages (SMA/EMA)](#ma)
2. [RSI(14)](#rsi)
3. [MACD](#macd)
4. [Bollinger Bands](#bb)
5. [Beta & Correlation](#beta)
6. [Performance metrics](#perf)

---

## Moving Averages <a name="ma"></a>

```python
def SMA(d, p):
    out = [None] * (p - 1)
    for i in range(p-1, len(d)):
        out.append(sum(d[i-p+1:i+1]) / p)
    return out

def EMA(d, p):
    k = 2 / (p + 1)
    o = [d[0]]
    for i in range(1, len(d)):
        o.append(d[i]*k + o[i-1]*(1-k))
    return o
```

**Interpretation:**
- Price above MA10 = short-term uptrend
- Price above MA20 = medium-term uptrend
- Price above MA50 = long-term uptrend
- MA50 crossing above MA200 = **Golden Cross** (strongly bullish)
- MA50 crossing below MA200 = **Death Cross** (strongly bearish)

---

## RSI(14) <a name="rsi"></a>

```python
def RSI(d, p=14):
    out = [None] * len(d)
    if len(d) <= p:
        return out
    avg_gain = avg_loss = 0.0
    for i in range(1, p + 1):
        ch = d[i] - d[i-1]
        if ch > 0: avg_gain += ch
        else: avg_loss += abs(ch)
    avg_gain /= p; avg_loss /= p
    out[p] = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    for i in range(p + 1, len(d)):
        ch = d[i] - d[i-1]
        avg_gain = (avg_gain * (p-1) + (ch if ch > 0 else 0)) / p
        avg_loss = (avg_loss * (p-1) + (abs(ch) if ch < 0 else 0)) / p
        out[i] = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return out
```

**Interpretation:**
- RSI < 30 → **Oversold** (potential buy opportunity)
- RSI > 70 → **Overbought** (sell warning)
- RSI 30-70 → Neutral

⚠️ **Cyclical-stock trap:** a low RSI does not always mean buy. In a strong downtrend RSI can stay in the 20-30 zone for a long time. Combine with MA and MACD.

---

## MACD <a name="macd"></a>

```python
ema12 = EMA(closes, 12)
ema26 = EMA(closes, 26)
macd_line = [a - b for a, b in zip(ema12, ema26)]
signal_line = EMA(macd_line, 9)
histogram = [m - s for m, s in zip(macd_line, signal_line)]
```

**Interpretation:**
- MACD > Signal → **Bullish** (upward crossover = buy signal)
- MACD < Signal → **Bearish** (downward crossover = sell signal)
- Histogram > 0 and rising → strong bullish momentum
- Histogram < 0 and falling → strong bearish momentum

---

## Bollinger Bands <a name="bb"></a>

```python
def bollinger(d, p=20, mult=2):
    sma = SMA(d, p)
    out = []
    for i in range(len(d)):
        if i < p - 1:
            out.append((None, None, None))
            continue
        slice_ = d[i-p+1:i+1]
        mean = sma[i]
        var = sum((v - mean) ** 2 for v in slice_) / p
        sd = var ** 0.5
        out.append((mean + mult * sd, mean, mean - mult * sd))
    return out

# BB Position (where the current price sits within the band):
# bb_pos = (price - lower) / (upper - lower) * 100
# < 20% = near the lower band (oversold)
# > 80% = near the upper band (overbought)
```

---

## Beta & Correlation <a name="beta"></a>

```python
def weekly_returns(closes):
    return [(closes[i]/closes[i-1]-1)*100 for i in range(1, len(closes))]

def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    ca = [x-ma for x in a]
    cb = [x-mb for x in b]
    num = sum(x*y for x, y in zip(ca, cb))
    den = (sum(x*x for x in ca)**0.5) * (sum(y*y for y in cb)**0.5)
    return num/den if den else 0

def beta(stock, market):
    ms, mm = sum(stock)/len(stock), sum(market)/len(market)
    cs = [x-ms for x in stock]
    cm = [x-mm for x in market]
    cov = sum(x*y for x, y in zip(cs, cm)) / len(stock)
    var = sum(x*x for x in cm) / len(market)
    return cov/var if var else 0
```

**Interpretation:**
- Beta > 1: the stock moves more than the market (aggressive)
- Beta = 1: moves in line with the market
- Beta < 1: moves less than the market (defensive)
- Beta < 0: moves opposite to the market (rare)

**Alpha = stock_perf - beta × market_perf**
- Alpha > 0: outperforms the market
- Alpha < 0: underperforms the market

---

## Performance metrics <a name="perf"></a>

```python
perf_1y = (closes[-1] / closes[0] - 1) * 100
perf_from_52w_high = (current / max(closes) - 1) * 100
perf_from_52w_low = (current / min(closes) - 1) * 100

# Volatility (annualized)
returns = [closes[i]/closes[i-1] - 1 for i in range(1, len(closes))]
mean_ret = sum(returns) / len(returns)
variance = sum((v - mean_ret) ** 2 for v in returns) / len(returns)
weekly_vol = variance ** 0.5 * 100
annual_vol = weekly_vol * (52 ** 0.5)  # weekly -> annual
```

**VN benchmark volatility:**
- < 15%: low (defensive — VNM, VCB)
- 15-25%: moderate (HPG, FPT)
- 25-40%: high (MWG, VIC)
- > 40%: very high (small-cap, penny stocks)
