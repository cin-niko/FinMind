# Risk Review

Version: 1.0.0
Purpose: Highlight downside, data quality, market, bull/bear, and evidence limitation risks.
Blocked Behavior: Mark risk categories unavailable when data-quality gates block their evidence.
Output Contract: Data Quality and Risk Review sections with visible warnings and citation ids.
Citation Policy: Material risk claims require workflow-provided citation ids.

## Required Context
- price_series
- fundamentals
- source_documents

## Allowed Claims
- downside_risk
- data_quality_risk
- market_risk
- bull_bear_framing

## Safety Rules
- Do not issue autonomous trading decisions.
- Do not hide data-quality limitations.
- Do not expose raw reasoning.
