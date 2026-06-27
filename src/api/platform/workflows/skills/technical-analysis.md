# Technical Analysis

Version: 1.0.0
Purpose: Analyze trend, momentum, support/resistance, and chart-backed price context from collected market records.
Blocked Behavior: Mark technical claims unavailable when price-series evidence is missing, stale, failed, or blocked.
Output Contract: Data Quality and Technical Analysis sections with chart artifact refs and citation ids.
Citation Policy: Material technical claims require market-data citation ids.

## Required Context
- price_series

## Allowed Claims
- technical_trend
- price_momentum
- support_resistance

## Safety Rules
- Do not issue buy, sell, hold, or order instructions.
- Do not infer price action without collected market records.
- Do not expose raw reasoning.
