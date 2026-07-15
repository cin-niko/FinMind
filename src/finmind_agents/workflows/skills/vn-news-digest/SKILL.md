# VN News Digest

Version: 1.0.0
Purpose: Summarize only eligible cited VN-stock news supplied by the workflow.
Blocked Behavior: Do not infer events, sentiment, or facts from titles alone, uncited material, or unavailable fields.
Output Contract: Concise Markdown digest; each material event names its citation and unavailable news is stated as Unavailable.
Citation Policy: Every material event must cite a supplied source-document citation id.

## Required Context

- Eligible source documents with URL, title, publication time, and content

## Allowed Claims

- Cited publication-time-stamped company or market events

## Safety Rules

- No trading instructions, predictions, or uncited summaries
- Treat missing title, URL, content, or publication time as Unavailable
