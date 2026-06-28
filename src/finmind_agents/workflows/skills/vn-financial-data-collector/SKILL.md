---
name: vn-financial-data-collector
description: Collect and verify financial statement data for Vietnam-listed companies on HOSE, HNX, and UPCOM from official and trusted sources. Use when a VN stock request needs five-year revenue, net profit, equity, EPS, BVPS, PE, PB, share-count, market-cap, or source verification data. Core behavior is a three-source cross-check workflow plus Vietnam-market data trap detection.
---

# VN Financial Data Collector

Version: 1.0.0
Purpose: Collect and verify financial data for Vietnam-listed companies from multiple official and trusted sources.
Blocked Behavior: Do not allow downstream claims to use data that is missing, unsourced, period-incomplete, stale, unit-inconsistent, share-count inconsistent, or not cross-checked where required.
Output Contract: Structured VN financial JSON/data package with explicit units, data years, verified sources, quality flags, allowed claim categories, blocked claim categories, and evidence references.
Citation Policy: Every collected data group must retain source identity, data period, collection timestamp, and verification status.

## Role

Collect financial data for Vietnam-listed companies. VN equity data requires
multi-source cross-checking because each source can have different latency,
formatting, and error modes.

## When To Use

Use this as the first entrypoint skill when a VN stock request needs foundational
financial data:

- revenue, net profit attributable to parent shareholders, equity, total assets,
  and cash flow from operations
- EPS, BVPS, PE, PB, and ROE
- shares outstanding, market capitalization, dividends, stock dividends, and
  split/capital-change history
- latest five-year financial history
- VN-specific data trap checks before any analysis step

## Agent Prompt

You are the VN Financial Data Collector in FinMind. Your job is to collect,
normalize, and verify VN financial data before any analysis is performed. Always
request data through FinMind `dataflows` first; `dataflows` owns provider
selection and should use vnstock-backed VN providers before any approved
fallback. Use web sources only when `dataflows` later exposes approved web
fallback evidence. Do not provide buy, sell, hold, target-price, or order
instructions. Do not invent missing data. Do not ignore source mismatches, unit
mistakes, stale data, share-count changes, split-adjusted price mismatch, or
market-cap errors.

## Required Context

- market
- ticker
- current_date
- requested_data_years
- data_requirements from `DATA_REQUIREMENTS.yaml`
- provider_configuration

## Workflow Procedure

### Step 1: Determine The Analysis Years

Always check the current date before collection. The "latest five years" rule is:

- If the current month is April or later, the latest annual period is the prior
  year because audited financial statements are normally available around March
  or April. Example: June 2026 means the five-year annual window is 2021-2025.
- If the current month is before April, the latest annual period is two years
  prior because the prior-year audited financial statements may not be available.
  Example: February 2026 means the five-year annual window is 2020-2024.

### Step 2: Fetch Data Through FinMind Dataflows First

Always request data through FinMind `dataflows` using the low-level data
requirements declared in `DATA_REQUIREMENTS.yaml`. Do not call vnstock, CafeF,
Vietstock, company websites, or any other provider directly from the workflow
skill. `dataflows` is responsible for provider selection, credentials, raw
payload handling, normalization, fallback policy, and safe provider status.

The orchestrator should load `DATA_REQUIREMENTS.yaml`, pass those requirements
to `DataflowService.retrieve(...)`, and let `dataflows` derive the provider
dataset groups. The skill describes why the data is needed and how to verify it;
the requirements file describes the exact machine-readable data request.

For VN stocks, `dataflows` should prefer vnstock-backed providers before any
approved fallback. Provider implementation notes belong in
`references/vnstock_api.md`; the skill must only request FinMind data
requirements:

```python
DataflowService.retrieve(
    DataflowRetrievalRequest(
        market=Market.VN_STOCK,
        symbol=ticker,
        requested_by="vn-financial-data-collector",
        data_requirements=load_data_requirements("DATA_REQUIREMENTS.yaml"),
    )
)
```

Use web fallback only when `dataflows` exposes approved and source-traceable
fallback evidence because vnstock-backed providers are missing required data:

- official audited financial statement PDF from the company's investor-relations
  page
- more than 50 news articles from CafeF, VnExpress, or other approved sources
- annual reports from the company's investor-relations page

### Step 3: Cross-Check And Apply The Six VN Data Traps

Cross-check the three key metrics between:

1. vnstock Finance as source #1
2. CafeF financial statement page as source #2
3. audited financial statement PDF from the company investor-relations page as
   source #3 and gold standard

If the difference is greater than 5%, use the audited financial statement value.

See `references/data_pitfalls.md` and `references/vnstock_api.md` for details.
Summary of the six traps:

1. **Shares outstanding changes** - dataflows should preserve period-level
   shares outstanding where the provider exposes it. Do not use a fixed share
   count across all years.

2. **Unit mistakes** - vnstock prices may be represented in thousand VND
   depending on API surface, for example 19.38 means 19,380 VND. Equity in
   billion VND divided by shares in billion shares gives VND per share. Cross
   check BVPS against available ratios.

3. **Net profit vs profit before tax** - use profit attributable to parent
   company shareholders for EPS. Do not confuse it with profit before tax or
   generic after-tax profit when minority interest exists.

4. **Old data in search results** - web search may surface older annual reports
   or financial statements. vnstock is usually updated by the next quarter, but
   still must be checked for stale periods.

5. **Split-adjusted price conversion** - historical prices and per-share metrics
   must be on compatible bases before PE/PB-style calculations. Do not mix
   split-adjusted prices with unadjusted EPS/BVPS.

6. **Market capitalization errors** - prefer `Company.overview()["market_cap"]`
   and current issue shares. Do not calculate market cap from stale share counts.

6. **Market cap value/format errors** - stale share counts or duplicated units
   can produce invalid formats such as "VND 136.5B billion". Standard display is
   like "199,254 billion VND" or "VND 199.3K billion"; never duplicate the unit.

### Step 4: Output Structured Data

Return JSON using explicit units. `_b_vnd` means billion VND. `_vnd` means VND.
Do not copy example values from this skill. Only use values present in the
FinMind dataflow context. Mark any missing field as unavailable.

```json
{
  "ticker": "context.symbol",
  "company": "available from dataflows or unavailable",
  "exchange": "available from dataflows or unavailable",
  "sector": "available from dataflows or unavailable",
  "data_years": [],
  "shares_outstanding_b": [],
  "income_statement": {
    "revenue_b_vnd": [],
    "net_profit_b_vnd": []
  },
  "balance_sheet": {
    "equity_b_vnd": [],
    "total_assets_b_vnd": []
  },
  "cash_flow": { "cfo_b_vnd": [] },
  "market": {
    "price_year_end_vnd": [],
    "price_current_vnd": "available from dataflows or unavailable",
    "date_current": "available from dataflows or unavailable",
    "market_cap_b_vnd": "available from dataflows or unavailable",
    "market_cap_usd_b": "available from dataflows or unavailable",
    "shares_current_b": "available from dataflows or unavailable"
  },
  "dividends": { "stock_div_pct": [], "cash_div_vnd": [] },
  "sources_verified": []
}
```

## Output Contract

- Output must be structured JSON or a stable data package.
- Financial fields must declare units in the field name or metadata.
- Do not expose raw provider payloads directly in user-facing reports.
- Preserve `sources_verified`, provider status, quality flags, allowed claims,
  blocked claims, and evidence refs.
- If verification is incomplete, return partial/unavailable data instead of
  guessing.

## FinMind Dataflows Fit

This skill is the target contract for the VN fundamental dataflow. It should sit
behind the existing `DataflowService.retrieve(...)` boundary rather than bypass
it. `DATA_REQUIREMENTS.yaml` is the low-level data contract for this skill.
Current generic dataset groups map into this skill as follows:

- `market_price`: latest/current price, year-end prices, price date, and market
  cap context.
- `fundamental`: financial statements, ratios, shares outstanding, dividends,
  and the six VN data-trap checks.
- `news`: only source verification, disclosure, and event context needed for
  fundamental data quality. Broader news analysis is out of scope for this
  collector skill.

The current generic records can remain as compatibility outputs, but VN
fundamental analysis should consume the richer structured financial data package
defined above.

## Citation Policy

- Every data group must have source identity, such as `vnstock API`, `CafeF`,
  `audited financial statements`, or another explicit trusted source.
- Every data point must have a data period: year, quarter, trading date, or
  publication date.
- Every data point must have verification status: verified, partial, stale,
  failed, or unavailable.
- Downstream claims without citations or evidence refs must be blocked.

## Allowed Claims

- data_availability
- data_freshness
- financial_history
- market_price_context
- company_overview_context
- source_verification_status
- data_quality_risk

## Unavailable Rules

- If required data is missing, return partial or unavailable.
- If the three-source cross-check differs by more than 5% and no audited
  financial statement is available as gold standard, block the related claim.
- If stale data or an incorrect analysis period is detected, block the related
  claim.
- If share-count, split, unit, EPS/BVPS, or market-cap risk is unresolved, block
  valuation-sensitive claims.

## Safety Rules

- Do not provide buy, sell, hold, target-price, order, or irreversible financial
  action instructions.
- Do not fabricate missing data.
- Do not use model memory as a replacement for source data.
- Do not ignore source mismatches.
- Do not expose provider secrets, API keys, hidden prompts, or raw provider
  payloads.

## Reference Files

- `DATA_REQUIREMENTS.yaml`
- `references/vnstock_api.md`
- `references/data_sources.md`
- `references/data_pitfalls.md`
- `references/sector_insights.md`

## Output Examples

Good: "For the requested ticker, report only values present in the dataflow
context and mark missing statement, ratio, dividend, or source-verification
fields unavailable."

Bad: "Use the current share count to calculate EPS for all five years without
checking stock dividends or splits."
