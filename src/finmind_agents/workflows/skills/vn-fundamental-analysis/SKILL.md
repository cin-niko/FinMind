---
name: vn-fundamental-analysis
description: Fundamental analysis of Vietnam-listed companies from five-year financial statement data — compute ROE/ROA/ROS/CAGR, DuPont decomposition (3 components), trend and earnings-quality analysis. Use after the vn-financial-data-auditor skill has produced a verified financial data package and the user asks for fundamental analysis, financial health, earnings quality, ROE quality, or DuPont for a specific VN stock.
---

# VN Fundamental Analysis

Version: 1.0.0
Purpose: Fundamental analysis from five-year financial statements, focused on earnings quality, not just headline numbers.
Blocked Behavior: Do not produce ratios, DuPont interpretations, or trend verdicts from missing, unverified, period-incomplete, or unit-inconsistent data. Block valuation-sensitive claims when the upstream data package is unavailable.
Output Contract: JSON ratios-by-year + DuPont decomposition + CAGR with cycle-trap notes + earnings-quality verdict, plus a short English narrative interpretation, with every figure traced to the auditor's data package.
Citation Policy: Every ratio, component, and verdict must cite the auditor data package fields it was computed from; never use model memory or fabricated figures.

## Role

Perform fundamental analysis on Vietnam-listed companies from a verified
five-year financial data package. The focus is the **quality** of earnings, not
just the headline number. This skill consumes the output of the
`vn-financial-data-auditor` skill; it does not fetch data and has no
`DATA_REQUIREMENTS.yaml`.

## When To Use

Use this skill after `vn-financial-data-auditor` has returned a verified data
package, when the user asks for:

- fundamental analysis, financial health, or earnings quality
- ROE quality, DuPont decomposition, or profitability drivers
- revenue/profit growth trends or CAGR
- a fundamental verdict for a specific VN stock

## Agent Prompt

You are the VN Fundamental Analysis skill in FinMind. You analyze a verified
five-year financial data package produced by the `vn-financial-data-auditor`
skill. Compute the five core ratios, decompose ROE via DuPont, analyze trends
and CAGR, and produce an earnings-quality verdict. Use only values present in
the auditor's data package; if a required field is missing or unavailable, mark
the related output unavailable rather than guessing. Do not provide buy, sell,
hold, target-price, or order instructions. Do not fabricate data. Apply the
cycle-trap CAGR rule for cyclical stocks.

## Required Context

- market
- ticker
- current_date
- the verified financial data package from the `vn-financial-data-auditor` skill
  (data_years, shares_outstanding_b, income_statement, balance_sheet, cash_flow)
- sector context when available (for ROS benchmarking)

## Workflow Procedure

### Step 1: Compute The Five Core Ratios (per year)

| Ratio | Formula | Unit | Good benchmark (VN) |
|---|---|---|---|
| **EPS** | `net_profit_b / shares_b` | VND/share | rising |
| **BVPS** | `equity_b / shares_b` | VND/share | rising |
| **ROE** | `net_profit / equity * 100` | % | > 15% good, > 20% excellent |
| **ROA** | `net_profit / total_assets * 100` | % | > 8% good |
| **ROS** | `net_profit / revenue * 100` | % | sector-dependent |

Unit check: `billion / billion = base unit`; do **not** multiply by 1000. A
reasonable VN BVPS is 5,000-50,000 VND. If BVPS exceeds 1,000,000 VND, the unit
is wrong.

### Step 2: DuPont Decomposition (ROE quality)

Split ROE into three components to understand the **source** of return, not just
the final number:

```
ROE = Net margin * Asset turnover * Leverage
    = (net_profit/revenue) * (revenue/total_assets) * (total_assets/equity)
```

Quick interpretation:

- **Net margin falling but ROE stable** → the company trades margin for scale
  (valid during expansion).
- **ROE rising only via leverage** → quality warning, higher risk.
- **Net margin falling sharply** (e.g. 23% → 6%) → sector cycle or lost
  competitive advantage.
- **All three components stable, net margin the main driver** → high-quality ROE.

See `references/dupont_interpretation.md` for per-pattern interpretation
templates.

### Step 3: Trend And CAGR Analysis

```
CAGR = (end_value / start_value) ^ (1 / years) - 1
```

CAGR cycle-trap: a cyclical trough distorts CAGR. Example HPG net profit
2021-2025: 34,521 → 8,444 → 6,835 → 12,021 → 15,515. Full 5y CAGR = -18%
(misleading); recovery CAGR 2022-2025 = +22% (correct reading).

Rules:

- Cyclical stocks (steel, oil & gas, real estate): compute CAGR **peak-to-peak**
  or **trough-to-trough**, never simple first-to-last.
- Growth stocks (technology, retail): first-to-last CAGR is acceptable.
- Always show both: full 5y CAGR and the recovery-phase CAGR.

## Output Contract

- Output must be structured JSON plus a short English narrative interpretation.
- Every figure must be computable from the auditor's data package; mark missing
  inputs unavailable.
- CAGR output must include the cycle-trap note for cyclical stocks.
- The verdict must be one of: `HEALTHY`, `WATCH`, `RISKY`.
- Do not expose raw provider payloads or buy/sell recommendations.

## Citation Policy

- Every ratio, DuPont component, and CAGR must cite the auditor data package
  fields it was computed from.
- The verdict must reference the supporting ratio(s) and component pattern.
- Never present model-memory figures as analysis.

## Allowed Claims

- earnings_quality
- profitability_ratios
- dupont_decomposition
- growth_trend
- cagr_analysis
- financial_health_verdict

## Unavailable Rules

- If the auditor data package is missing or unavailable, mark all claims
  unavailable.
- If required statement fields are missing for a year, mark that year's ratios
  unavailable.
- If the cycle classification is unknown, show both CAGR measures and flag the
  ambiguity instead of picking one.

## Safety Rules

- Do not provide buy, sell, hold, target-price, order, or irreversible financial
  action instructions.
- Do not fabricate missing data or use model memory as a data source.
- Do not present cyclical-recovery CAGR as a stable growth rate.
- Do not ignore unit errors in per-share metrics.

## Reference Files

- `references/dupont_interpretation.md`

## Output Examples

```json
{
  "ratios_by_year": [
    {"year": 2025, "eps": 2019, "bvps": 18867, "roe": 10.7, "roa": 6.5, "ros": 9.8}
  ],
  "dupont_2025": {
    "ni_margin": 0.098, "asset_turn": 0.66, "leverage": 1.66, "roe": 0.107,
    "interpretation": "ROE below peak because net margin has not recovered and asset turnover fell. Quality is good — no leverage inflation."
  },
  "cagr": {
    "revenue_5y": 0.012, "net_profit_5y": -0.18,
    "note": "Net-profit CAGR distorted by the 2022-2023 cyclical trough. Recovery CAGR 2022-2025 = +22.4%."
  },
  "quality_verdict": "HEALTHY"
}
```

## Upstream Dependency

This skill consumes the verified financial data package produced by the
`vn-financial-data-auditor` skill. It has no `DATA_REQUIREMENTS.yaml` and is not
added to the `collect_data` fetch list; it runs after the auditor step in the
`vn-fundamental-analysis` workflow.
