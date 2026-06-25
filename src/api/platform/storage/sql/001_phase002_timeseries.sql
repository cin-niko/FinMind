CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS market_instruments (
    instrument_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    exchange TEXT,
    display_name TEXT NOT NULL,
    currency TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    sub_industry TEXT,
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS market_collections (
    collection_id TEXT NOT NULL,
    market TEXT NOT NULL,
    name TEXT NOT NULL,
    collection_type TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER,
    PRIMARY KEY (market, collection_id)
);

CREATE TABLE IF NOT EXISTS market_collection_memberships (
    collection_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL REFERENCES market_instruments(instrument_id),
    weight DOUBLE PRECISION,
    effective_from DATE NOT NULL,
    effective_to DATE,
    PRIMARY KEY (collection_id, instrument_id, effective_from)
);

CREATE TABLE IF NOT EXISTS stock_1h_bars (
    market TEXT NOT NULL,
    instrument_id TEXT NOT NULL REFERENCES market_instruments(instrument_id),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    interval_start TIMESTAMPTZ NOT NULL,
    interval_end TIMESTAMPTZ NOT NULL,
    open NUMERIC NOT NULL CHECK (open >= 0),
    high NUMERIC NOT NULL CHECK (high >= 0),
    low NUMERIC NOT NULL CHECK (low >= 0),
    close NUMERIC NOT NULL CHECK (close >= 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    value NUMERIC,
    currency TEXT NOT NULL,
    adjusted_close NUMERIC,
    corporate_action_flag BOOLEAN,
    collected_at TIMESTAMPTZ NOT NULL,
    source_id TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    PRIMARY KEY (market, instrument_id, interval_start),
    CHECK (high >= open AND high >= low AND high >= close),
    CHECK (low <= open AND low <= high AND low <= close)
);

SELECT create_hypertable('stock_1h_bars', 'interval_start', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS stock_daily_bars (
    market TEXT NOT NULL,
    instrument_id TEXT NOT NULL REFERENCES market_instruments(instrument_id),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    trading_date DATE NOT NULL,
    open NUMERIC NOT NULL CHECK (open >= 0),
    high NUMERIC NOT NULL CHECK (high >= 0),
    low NUMERIC NOT NULL CHECK (low >= 0),
    close NUMERIC NOT NULL CHECK (close >= 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    value NUMERIC,
    currency TEXT NOT NULL,
    adjusted_close NUMERIC,
    corporate_action_flag BOOLEAN,
    collected_at TIMESTAMPTZ NOT NULL,
    source_id TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    PRIMARY KEY (market, instrument_id, trading_date),
    CHECK (high >= open AND high >= low AND high >= close),
    CHECK (low <= open AND low <= high AND low <= close)
);

SELECT create_hypertable('stock_daily_bars', 'trading_date', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS xauusd_1h_bars (
    instrument_id TEXT NOT NULL REFERENCES market_instruments(instrument_id),
    symbol TEXT NOT NULL,
    interval_start TIMESTAMPTZ NOT NULL,
    interval_end TIMESTAMPTZ NOT NULL,
    open NUMERIC NOT NULL CHECK (open >= 0),
    high NUMERIC NOT NULL CHECK (high >= 0),
    low NUMERIC NOT NULL CHECK (low >= 0),
    close NUMERIC NOT NULL CHECK (close >= 0),
    unit TEXT NOT NULL,
    currency TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    source_id TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    PRIMARY KEY (instrument_id, interval_start),
    CHECK (high >= open AND high >= low AND high >= close),
    CHECK (low <= open AND low <= high AND low <= close)
);

SELECT create_hypertable('xauusd_1h_bars', 'interval_start', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS xauusd_daily_bars (
    instrument_id TEXT NOT NULL REFERENCES market_instruments(instrument_id),
    symbol TEXT NOT NULL,
    trading_date DATE NOT NULL,
    open NUMERIC NOT NULL CHECK (open >= 0),
    high NUMERIC NOT NULL CHECK (high >= 0),
    low NUMERIC NOT NULL CHECK (low >= 0),
    close NUMERIC NOT NULL CHECK (close >= 0),
    unit TEXT NOT NULL,
    currency TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    source_id TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    PRIMARY KEY (instrument_id, trading_date),
    CHECK (high >= open AND high >= low AND high >= close),
    CHECK (low <= open AND low <= high AND low <= close)
);

SELECT create_hypertable('xauusd_daily_bars', 'trading_date', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS sjc_gold_daily_quotes (
    instrument_id TEXT NOT NULL REFERENCES market_instruments(instrument_id),
    symbol TEXT NOT NULL,
    quote_type TEXT NOT NULL,
    quote_date DATE NOT NULL,
    buy_price NUMERIC CHECK (buy_price >= 0),
    sell_price NUMERIC CHECK (sell_price >= 0),
    price NUMERIC CHECK (price >= 0),
    unit TEXT NOT NULL,
    currency TEXT NOT NULL,
    location TEXT,
    collected_at TIMESTAMPTZ NOT NULL,
    source_id TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    PRIMARY KEY (instrument_id, quote_type, quote_date),
    CHECK (price IS NOT NULL OR (buy_price IS NOT NULL AND sell_price IS NOT NULL)),
    CHECK (sell_price IS NULL OR buy_price IS NULL OR sell_price >= buy_price)
);

SELECT create_hypertable('sjc_gold_daily_quotes', 'quote_date', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS source_documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL,
    url_or_reference TEXT NOT NULL,
    content_excerpt TEXT,
    market_scope TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    trigger TEXT NOT NULL,
    period TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    record_count INTEGER NOT NULL DEFAULT 0,
    diagnostics JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ingestion_jobs_overlap_idx
ON ingestion_jobs (source_id, dataset_id, period, status);

CREATE TABLE IF NOT EXISTS execution_logs (
    log_id TEXT PRIMARY KEY,
    run_id TEXT,
    job_id TEXT,
    event TEXT NOT NULL,
    status TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS evidence_objects (
    evidence_id TEXT PRIMARY KEY,
    claim_ref TEXT NOT NULL,
    source_refs JSONB NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    freshness_status TEXT NOT NULL,
    summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS citations (
    citation_id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL REFERENCES evidence_objects(evidence_id),
    label TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    timestamp TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    title TEXT NOT NULL,
    inputs JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb
);
