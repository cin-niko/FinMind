---
title: Perplexity Finance Benchmark
status: active
last_review: 2026-06-25
related_specs:
  - specs/003-evidence-backed-chat/spec.md
  - specs/002-data-operations/spec.md
sources:
  - https://www.perplexity.ai/finance
  - https://www.perplexity.ai/hub/blog/introducing-finance-search-in-the-agent-api
  - https://docs.perplexity.ai/docs/agent-api/finance-search
---

# Perplexity Finance Benchmark

Research note distilling what [Perplexity Finance](https://www.perplexity.ai/finance)
is in 2026, how its data and citation layer works, and what FinMind should borrow
or deliberately not compete on. Example ticker surface:
[NVDA](https://www.perplexity.ai/finance/NVDA).

This is a product benchmark, not a spec. Normative FinMind behavior remains in
`specs/`.

## Summary

Perplexity Finance is a dedicated finance vertical inside Perplexity AI. It
combines a market dashboard, deep ticker pages, earnings hub, screener, filing
research, and plain-English chat over **licensed multi-provider financial data**
with inline citations. The product thesis is: one question in natural language
returns a cited, structured answer instead of a list of links.

For developers, the same retrieval layer is exposed as the Agent API
`finance_search` tool: the model routes to structured financial datasets and
returns normalized, cited results regardless of underlying provider.

FinMind cannot replicate Perplexity's licensing breadth or US-market depth on
free VN resources. The useful takeaway is **pattern adoption**: unified
retrieval contract, citation UX, workflow surfaces, and evidence lineage —
applied to VN100 on a constrained data budget.

## Product Positioning

| Dimension | Perplexity Finance |
|-----------|-------------------|
| Category | AI-native finance research terminal (read-only) |
| Launch arc | Quote lookup (Oct 2024) → near-terminal by 2026 |
| Core thesis | Synthesis over structured sources, not web search |
| Primary market | US equities (+ India screener, crypto via Coinbase) |
| Monetization | Free base tier; Pro/Max gate AI depth and quota |
| Trade execution | None |
| Broker connectivity | Portfolio via Plaid (Pro tier); no order placement |

Positioning is "Bloomberg Terminal for research," not "broker platform."

## User-Facing Surfaces

### Finance dashboard (`/finance`)

- Market summary with AI-generated commentary and cited news
- Major index charts (S&P, NASDAQ, Dow, VIX, etc.)
- Top gainers, losers, trending tickers
- Sector heatmap for at-a-glance performance
- Tabs: US Market, Crypto, Earnings
- Global search bar driving chat and ticker navigation

**FinMind analog:** `MarketPage.tsx` (VN-only V1): index mini charts, VN100
table, heatmap, watchlist, gainers/losers rail.

### Ticker pages (`/finance/{SYMBOL}`)

Example: [NVDA](https://www.perplexity.ai/finance/NVDA).

Typical layout:

- Live price, change, key stats
- Interactive price chart (volume, OHLCV tooltips, candlestick/area toggle,
  compare overlays, SMA, custom date ranges)
- Recent news
- Earnings history and analyst ratings
- Tabs on many US tickers: **Holders**, **Insiders**, **Politicians**,
  **Documents**, **Filings**

**FinMind analog:** instrument detail chart only today. No multi-tab ticker
page, no ownership, no documents hub.

### Earnings Hub

- Calendar of upcoming and past US earnings
- During live calls: near-real-time transcription, AI summary, metric extraction
  (revenue, EPS) while the call is in progress
- Post-call: slides, quarterly reports, earnings releases in a Documents view

Backed heavily by [Quartr](https://quartr.com/) for transcripts and documents.

**FinMind analog:** not planned in V1. Would require VN earnings transcript
source and document ingestion (likely Phase 003.M2+).

### Natural-language stock screener

- Plain-English filter input ("US tech stocks with revenue growth > 20% YoY and
  P/E < 30")
- Filterable columns, sorting, exportable results
- Coverage: US and Indian equities

**FinMind analog:** candidate Phase 003.M2 chat use case over fundamentals.

### SEC filing research

- Direct access to 10-K, 10-Q, S-1, S-4, 20-F, 8-K from EDGAR
- Chat/Research can answer filing questions with citation links to source pages
- Enterprise tier adds FactSet M&A and transcript depth

**FinMind analog:** `source_documents` table exists as extension point; no VN
filing ingestion in V1.

### Portfolio, alerts, and tasks

- **Portfolio:** Plaid broker linking, portfolio analytics (Pro)
- **Price alerts:** user-configured notifications
- **Tasks:** scheduled rerunning research queries with notifications (Max)

**FinMind analog:** out of V1 scope per `specs/system/runtime-config-security.md`
(no broker connectivity, no trade execution). Scheduled workflows are a closer
fit than portfolio tracking.

## Data Backend

Perplexity Finance is a **multi-source aggregator** behind one retrieval and
citation contract. The finance homepage footer and product materials name these
providers (exact mix may vary by tier and surface):

| Provider | Role |
|----------|------|
| [Financial Modeling Prep](https://site.financialmodelingprep.com/) | Core financials, fundamentals, ratios |
| [S&P Global](https://www.spglobal.com/) | Analyst estimates, consensus |
| [Morningstar](https://www.morningstar.com/) | Equity/fund classifications |
| [LSEG (Refinitiv)](https://www.lseg.com/) | Broader market data |
| [FactSet](https://www.factset.com/) | Enterprise: M&A, transcripts |
| SEC EDGAR | Raw filings |
| [Quartr](https://quartr.com/) | Earnings transcripts, audio, documents |
| [Fiscal.ai](https://fiscal.ai/) | Reported revenue/EPS history |
| [Unusual Whales](https://unusualwhales.com/) | Options flow |
| [Polymarket](https://polymarket.com/) | Prediction markets |
| [Coinbase](https://www.coinbase.com/) | Real-time crypto |
| [TradingView](https://www.tradingview.com/) | Chart rendering (Perplexity Computer) |
| [Plaid](https://plaid.com/) | Brokerage account linking |

**Architecture pattern:** licensed providers → normalized retrieval layer →
consistent schema + inline citations → UI and Agent API.

This maps to the reference architecture FinMind discussed:

```
PostgreSQL (relational)     → companies, instruments, facts, earnings, estimates
TimescaleDB / ClickHouse    → OHLCV and intraday
S3 / object store           → filings, transcripts, generated reports
```

Perplexity effectively runs all three layers, with the moat in the **unified
retrieval contract** rather than any single dataset.

## Developer Surface: Finance Search API

Announced in Perplexity's
[Finance Search blog post](https://www.perplexity.ai/hub/blog/introducing-finance-search-in-the-agent-api)
and documented in
[Finance Search API docs](https://docs.perplexity.ai/docs/agent-api/finance-search).

### Tool shape

```python
client.responses.create(
    model="perplexity/sonar",
    input="What is NVIDIA trading at right now, and what is its current P/E?",
    tools=[{"type": "finance_search"}],
)
```

The model decides which finance categories to fetch from the prompt. Results
return in a consistent schema with inline citations, independent of underlying
provider.

### Data areas exposed

| Area | Contents |
|------|----------|
| Company basics | Quotes, profiles, peers, market metadata |
| Financials | Income statement, balance sheet, cash flow (Q&A), ratios |
| Valuation/pricing | Real-time and historical OHLCV (1m–1M), pre/after-market |
| Earnings | Transcripts, filings, beat/miss, guidance |
| Segment/KPI | Revenue by segment, geography, ARPU, subscribers, GMV |
| Analyst coverage | Forward revenue/EPS, coverage count, estimate history |
| Market activity | Gainers, losers, most active |
| Ownership/actions | Insider activity, splits, corporate events |
| ETF/index | Constituents, weights, market values |

### Cost and profiles

- Billed at approximately **$5 per 1,000 invocations** (Agent API pricing)
- Pre-configured profiles trade latency vs. cost vs. depth:
  - Live quotes (fast, low cost)
  - Single-company historical (balanced)
  - Multi-step research (thorough, highest cost; often paired with Opus)

### Design principle

Retrieve structured financial data directly instead of forcing the model to
parse generic web search results. Perplexity reports better accuracy and lower
token cost on finance benchmarks (e.g. FinSearchComp) versus web-search-only
approaches.

## Access Tiers (approximate, 2026)

| Tier | Typical limits | Notable gates |
|------|----------------|---------------|
| Free | ~5 Pro searches/day | Dashboard, ticker pages, screener, documents largely accessible |
| Pro | 300+ Pro searches/day | Deep Research, larger Spaces, portfolio |
| Max | Unlimited Pro searches | Tasks, full automation |
| Enterprise Pro | Custom | FactSet M&A, Crunchbase, internal files |

Free tier still exposes substantial **data surfaces**; paywall is on AI depth
and automation, not raw quote access.

## UX Patterns Worth Borrowing

### High value for FinMind

1. **Inline citations to primary sources** — every material number footnoted.
   FinMind already has `evidence_objects` + `citations`; invest in visual
   treatment in chat and workflow surfaces.

2. **Unified retrieval contract** — user never sees provider seams. FinMind's
   source connector abstraction (`specs/002-data-operations/`) is the right
   internal analog.

3. **Plain-English screener** — NL → structured query → results. Strong Phase
   003.M2 candidate once fundamentals exist.

4. **Documents tab per ticker** — slides, releases, transcripts in one place.
   Maps to `source_documents` + object storage when VN document ingestion lands.

5. **Scheduled research tasks** — maps to FinMind fixed workflows + worker
   ingestion, not chat-only reruns.

### Distinctive but hard on free VN resources

- Live earnings call synthesis (needs Quartr-class licensing)
- Politician trades (US STOCK Act; no VN equivalent)
- Options flow (Unusual Whales)
- Prediction markets (Polymarket)

### Deliberately not in either product's core

- Trade execution
- Proprietary alpha signals
- Team collaboration workspaces (Perplexity Spaces are personal)

## FinMind Comparison (V1 after VN-only scope-down)

| Dimension | Perplexity Finance | FinMind V1 (planned) |
|-----------|-------------------|----------------------|
| Market scope | US (+ India screener, crypto) | VN100 only |
| Price data | Minute to monthly OHLCV | `vn_prices_daily` canonical; `vn_prices` 1h best-effort |
| Fundamentals | Full statements, ratios, segments | Phase 003.M2 (`financial_facts`, earnings) |
| Estimates | S&P Global consensus | Not planned V1 |
| Filings/transcripts | EDGAR + Quartr + FactSet | Extension point only |
| Data sources | 13+ licensed providers | `vnstock` (+ mock for tests) |
| Citation model | Inline footnotes to sources | Structured evidence → citation → typed DB records |
| Chat | Core product surface | Phase 003.M1 (prices), M2 (fundamentals) |
| Ticker page depth | 6+ tabs | Single chart view |
| Earnings hub | Live transcription + synthesis | Not planned |
| Screener | NL-driven, US/India | Not planned V1 |
| Portfolio | Plaid linking | Out of scope (no broker) |
| Charts | TradingView (Computer) | Lightweight Charts |
| Cost to operator | Subscription tiers | Free vnstock + internal infra |

## Strategic Read for FinMind

### Do not compete on

- Multi-provider US licensing breadth
- Live earnings transcription
- Global retail distribution
- Minute-level history at scale without paid data

### Credible differentiation

1. **VN market focus** — Perplexity barely covers Vietnam; local workflow depth
   is a real gap.

2. **Workflow-first** — repeatable fixed workflows (Phase 001) for recurring
   research patterns; Perplexity is chat-first.

3. **Lineage-first evidence** — citations trace to typed time-series rows,
   ingestion jobs, and execution logs; stronger audit story than footnotes alone.

4. **Internal tool constraints** — optimize for analyst trust and scope honesty,
   not viral free-tier growth.

## Implications for Phase 003.M2 (SC-010 gate)

Perplexity-inspired use cases that should drive fundamentals schema design
(record in `specs/003-evidence-backed-chat/research.md` before M2 implementation):

1. **Quarterly trend:** "How did VPB's net interest income trend over the last
   four quarters?" → requires `financial_facts` (income statement line items,
   fiscal period, currency).

2. **Cross-instrument screen:** "Compare VN30 banks by P/B and ROE; show the
   three cheapest on a quality basis." → requires fundamentals + computed ratios
   + multi-instrument query.

3. **Earnings narrative:** "Summarize VHM's most recent earnings — what did
   management say about Q4 guidance?" → requires earnings events +
   `source_documents` (transcript or filing excerpt) with point-in-time citation.

These three exercises cover the hardest fundamentals schema decisions: line-item
normalization, fiscal-period semantics, restatement handling, ratio computation,
and document-backed narrative claims.

## Object Storage Note

Perplexity implicitly uses blob storage for filings, transcripts, and generated
reports. FinMind currently stores excerpts in PostgreSQL JSONB (`source_documents`,
`artifacts`). Introduce S3/MinIO when:

- Artifacts exceed ~1 MB routinely
- Page-level filing citation is required
- Vector/RAG search over long transcripts is needed

Likely trigger: Phase 003.M2 document ingestion, not Phase 002 price ingestion.

## References

- [Perplexity Finance](https://www.perplexity.ai/finance)
- [NVDA ticker example](https://www.perplexity.ai/finance/NVDA)
- [Introducing Finance Search in the Agent API](https://www.perplexity.ai/hub/blog/introducing-finance-search-in-the-agent-api)
- [Finance Search API documentation](https://docs.perplexity.ai/docs/agent-api/finance-search)
- FinMind specs: `specs/003-evidence-backed-chat/spec.md`, `specs/002-data-operations/spec.md`
- FinMind system contracts: `specs/system/contracts.md`, `specs/system/state-model.md`
