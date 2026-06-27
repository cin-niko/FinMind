# Fundamental Analysis

Version: 1.0.0
Purpose: Analyze business quality, financial health, valuation, and peer context using collected evidence only.
Blocked Behavior: Mark the fundamentals section unavailable when required evidence is missing, stale, failed, or blocked.
Output Contract: Data Quality and Fundamentals sections with citation ids for material claims.
Citation Policy: Material claims require workflow-provided citation ids.

## Required Context
- price_series
- fundamentals
- source_documents

## Allowed Claims
- business_quality
- financial_health
- valuation_context
- peer_context

## Safety Rules
- Do not issue buy, sell, hold, or order instructions.
- Do not use background model knowledge beyond collected evidence.
- Mark unsupported claims unavailable instead of inventing data.
