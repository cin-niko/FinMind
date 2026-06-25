# Free Market Data Providers Design

## Goal

Define the phase 002 free-source provider profile for VN stocks, XAUUSD, and SJC gold
without weakening the provider-neutral ingestion contract.

## Provider Choices

- VN stocks use FireAnt as the preferred free provider for historical VN stock data.
- XAUUSD uses yfinance/Yahoo Finance for recent intraday `1h` bars.
- XAUUSD long-history fallback uses Alpha Vantage free gold history when daily data is
  sufficient.
- SJC gold uses the official SJC website/chart surfaces as the authoritative free
  source for daily buy/sell quotes.

## Retention Shape

- VN stock records remain `1h` OHLCV when FireAnt exposes the requested historical range.
- XAUUSD stores recent rolling `1h` OHLC bars where yfinance/Yahoo Finance exposes
  intraday history, and daily history for longer backfills.
- SJC stores daily buy/sell quotes only.

## Runtime Profile

The free profile is selected by runtime configuration rather than product-contract
changes:

- `FINMIND_PROVIDER_PROFILE=free`
- `FINMIND_VN_PROVIDER=fireant`
- `FINMIND_XAUUSD_PROVIDER=yfinance`
- `FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage`
- `FINMIND_SJC_PROVIDER=sjc_official`

Provider-specific adapters must normalize responses into the canonical dataset schemas
before persistence. API responses and diagnostics must not expose provider credentials,
tokens, raw request headers, or raw scraped pages.

## Verification

Adapter tests must cover:

- historical backfill limits and graceful degradation for unavailable intraday ranges;
- no paid API dependency for the free profile;
- idempotent writes into PostgreSQL/TimescaleDB typed tables;
- non-secret diagnostics on provider failure;
- source attribution for FireAnt, Yahoo/yfinance, Alpha Vantage fallback, and SJC.
