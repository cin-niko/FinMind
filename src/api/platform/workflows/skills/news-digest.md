# News Digest

Version: 1.0.0
Purpose: Summarize trusted source documents with timestamps, sentiment framing, and cited evidence.
Blocked Behavior: Mark the news section unavailable when trusted source material is unavailable.
Output Contract: Data Quality and News Digest sections with citation ids for cited source documents.
Citation Policy: Material news claims require source document citations.

## Required Context
- source_documents

## Allowed Claims
- recent_news_impact
- sentiment_context
- catalyst_context

## Safety Rules
- Do not fabricate news items.
- Do not present stale source material as current.
- Keep final trading judgment with the user.
