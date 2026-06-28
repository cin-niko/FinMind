from datetime import UTC, datetime
from typing import Any

from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Market,
    SourceDocument,
)


def normalize_price_record(
    *,
    dataset_id: str,
    record_key: str,
    instrument_id: str,
    market_time: datetime,
    collected_at: datetime,
    source_id: str,
    payload: dict[str, Any],
) -> CanonicalMarketDataRecord:
    return CanonicalMarketDataRecord(
        dataset_id=dataset_id,
        record_key=record_key,
        instrument_id=instrument_id,
        market_time=market_time,
        collected_at=collected_at,
        source_id=source_id,
        payload=payload,
    )


def normalize_fundamental_record(
    *,
    dataset_id: str,
    record_key: str,
    instrument_id: str,
    market_time: datetime,
    collected_at: datetime,
    source_id: str,
    payload: dict[str, Any],
) -> CanonicalMarketDataRecord:
    return CanonicalMarketDataRecord(
        dataset_id=dataset_id,
        record_key=record_key,
        instrument_id=instrument_id,
        market_time=market_time,
        collected_at=collected_at,
        source_id=source_id,
        payload=payload,
    )


def normalize_source_document(
    *,
    document_id: str,
    source_id: str,
    title: str,
    published_at: datetime,
    collected_at: datetime,
    url_or_reference: str,
    content_excerpt: str,
    market_scope: Market,
    instrument_ids: tuple[str, ...],
    sentiment_hint: str | None = None,
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        source_id=source_id,
        title=title,
        published_at=published_at.astimezone(UTC),
        collected_at=collected_at.astimezone(UTC),
        url_or_reference=url_or_reference,
        content_excerpt=content_excerpt,
        market_scope=market_scope,
        instrument_ids=instrument_ids,
        sentiment_hint=sentiment_hint,
    )
