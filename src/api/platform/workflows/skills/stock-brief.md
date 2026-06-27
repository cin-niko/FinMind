# Stock Brief

Version: 1.0.0
Purpose: Compose data quality, fundamentals, technical analysis, news digest, and risk review into one cited stock brief.
Blocked Behavior: Preserve available sections and mark blocked sections unavailable when evidence is missing or failed.
Output Contract: Data Quality, Fundamentals, Technical Analysis, News Digest, and Risk Review sections.
Citation Policy: Material claims require workflow-provided citation ids.

## Required Context
- price_series
- fundamentals
- source_documents

## Allowed Claims
- business_quality
- technical_trend
- recent_news_impact
- downside_risk

## Safety Rules
- Do not issue buy, sell, hold, or order instructions.
- Do not let one unavailable section fabricate missing evidence.
- Keep outputs advice-support only.
