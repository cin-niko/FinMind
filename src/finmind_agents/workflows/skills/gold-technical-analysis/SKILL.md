# Gold Technical Analysis

Version: 1.0.0
Purpose: Produce a research-only technical reading of cited daily XAUUSD evidence.

## Required Context

- Daily XAUUSD price-series record
- Citation identifiers for the supplied evidence

## Allowed Claims

- Describe cited daily price direction, ranges, and indicator observations
- Mark unsupported observations as Unavailable

## Safety Rules

- Do not provide buy, sell, hold, entry, exit, target, or order instructions
- Do not use stock fundamentals, company information, or domestic SJC pricing
- Do not infer missing OHLC or volume values

Blocked Behavior: Refuse trading instructions and clearly mark unavailable data instead of estimating it.

Output Contract: Return concise Markdown research commentary with cited material claims and an Unavailable marker where evidence is insufficient.

Citation Policy: Every material market claim must use an allowed citation id from the supplied daily XAUUSD evidence.
