"""VN100 universe seed loader.

Loads the static VN100 constituent CSV into the canonical
``market_instruments``/``market_collections``/
``market_collection_memberships`` tables in an idempotent fashion.

The CSV is refreshed quarterly out-of-band. Re-running the loader MUST
NOT create duplicate rows and MUST NOT shift ``effective_from`` for
existing memberships (the ON CONFLICT clauses handle de-duplication).
"""

from __future__ import annotations

import csv
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


VN100_COLLECTION_ID = "VN100"
VN100_MARKET = "VN_STOCK"
VN100_COLLECTION_NAME = "VN100 Index"
VN100_COLLECTION_TYPE = "index"
VN100_DESCRIPTION = (
    "Top 100 HOSE-listed equities tracked by the VN100 index."
)
VN100_EFFECTIVE_FROM = date(2026, 6, 25)
INSTRUMENT_ID_PREFIX = "vn_stock"
DEFAULT_EXCHANGE = "HOSE"
DEFAULT_CURRENCY = "VND"
DEFAULT_STATUS = "active"
ASSET_CLASS = "stock"


class _StoreLike(Protocol):
    def _connect(self) -> Any: ...


@dataclass(frozen=True, slots=True)
class SeedRow:
    """A single CSV row describing one VN100 constituent."""

    symbol: str
    display_name: str
    exchange: str
    sector: str | None
    industry: str | None
    currency: str
    status: str

    @property
    def instrument_id(self) -> str:
        return f"{INSTRUMENT_ID_PREFIX}:{self.symbol}"


@dataclass(frozen=True, slots=True)
class SeedResult:
    """Counts returned by :func:`load_vn100_seed`."""

    instruments_seen: int
    instruments_upserted: int
    collection_upserted: int
    memberships_seen: int
    memberships_upserted: int


def _normalize_optional(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def parse_vn100_csv(csv_path: Path) -> list[SeedRow]:
    """Parse the VN100 seed CSV and return validated rows.

    Raises ``ValueError`` if the CSV is missing required columns or
    contains duplicate symbols.
    """

    expected = {
        "symbol",
        "display_name",
        "exchange",
        "sector",
        "industry",
        "currency",
        "status",
    }
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Empty CSV: {csv_path}")
        missing = expected - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"VN100 CSV missing columns: {sorted(missing)}"
            )
        rows: list[SeedRow] = []
        seen: set[str] = set()
        for raw in reader:
            symbol = raw["symbol"].strip().upper()
            if not symbol:
                continue
            if symbol in seen:
                raise ValueError(
                    f"Duplicate symbol in VN100 CSV: {symbol}"
                )
            seen.add(symbol)
            rows.append(
                SeedRow(
                    symbol=symbol,
                    display_name=raw["display_name"].strip()
                    or symbol,
                    exchange=raw["exchange"].strip()
                    or DEFAULT_EXCHANGE,
                    sector=_normalize_optional(raw["sector"]),
                    industry=_normalize_optional(raw["industry"]),
                    currency=raw["currency"].strip()
                    or DEFAULT_CURRENCY,
                    status=raw["status"].strip() or DEFAULT_STATUS,
                )
            )
    return rows


def load_vn100_seed(
    csv_path: Path,
    store: _StoreLike,
    effective_from: date = VN100_EFFECTIVE_FROM,
) -> SeedResult:
    """Idempotently load the VN100 seed into Postgres.

    Uses the existing ``_connect`` factory on
    ``PostgresTimeSeriesStore`` (or any compatible store) so the loader
    inherits the same connection wiring as ingestion.
    """

    rows = parse_vn100_csv(csv_path)
    logger.info(
        "vn100_seed.parsed csv_path=%s row_count=%d",
        csv_path,
        len(rows),
    )

    connection = store._connect()  # noqa: SLF001 - shared pattern
    try:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    _UPSERT_INSTRUMENT,
                    {
                        "instrument_id": row.instrument_id,
                        "symbol": row.symbol,
                        "market": VN100_MARKET,
                        "asset_class": ASSET_CLASS,
                        "exchange": row.exchange,
                        "display_name": row.display_name,
                        "currency": row.currency,
                        "sector": row.sector,
                        "industry": row.industry,
                        "status": row.status,
                    },
                )
            cursor.execute(
                _UPSERT_COLLECTION,
                {
                    "collection_id": VN100_COLLECTION_ID,
                    "market": VN100_MARKET,
                    "name": VN100_COLLECTION_NAME,
                    "collection_type": VN100_COLLECTION_TYPE,
                    "description": VN100_DESCRIPTION,
                    "sort_order": 100,
                },
            )
            for row in rows:
                cursor.execute(
                    _INSERT_MEMBERSHIP,
                    {
                        "collection_id": VN100_COLLECTION_ID,
                        "instrument_id": row.instrument_id,
                        "effective_from": effective_from,
                    },
                )
        connection.commit()
    finally:
        connection.close()

    result = SeedResult(
        instruments_seen=len(rows),
        instruments_upserted=len(rows),
        collection_upserted=1,
        memberships_seen=len(rows),
        memberships_upserted=len(rows),
    )
    logger.info("vn100_seed.loaded %s", result)
    return result


_UPSERT_INSTRUMENT = """
INSERT INTO market_instruments (
    instrument_id, symbol, market, asset_class, exchange, display_name,
    currency, sector, industry, status
) VALUES (
    %(instrument_id)s, %(symbol)s, %(market)s, %(asset_class)s,
    %(exchange)s, %(display_name)s, %(currency)s, %(sector)s,
    %(industry)s, %(status)s
)
ON CONFLICT (instrument_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    sector = EXCLUDED.sector,
    industry = EXCLUDED.industry,
    status = EXCLUDED.status
"""

_UPSERT_COLLECTION = """
INSERT INTO market_collections (
    collection_id, market, name, collection_type, description, sort_order
) VALUES (
    %(collection_id)s, %(market)s, %(name)s, %(collection_type)s,
    %(description)s, %(sort_order)s
)
ON CONFLICT (market, collection_id) DO NOTHING
"""

_INSERT_MEMBERSHIP = """
INSERT INTO market_collection_memberships (
    collection_id, instrument_id, effective_from
) VALUES (
    %(collection_id)s, %(instrument_id)s, %(effective_from)s
)
ON CONFLICT (collection_id, instrument_id, effective_from) DO NOTHING
"""


def _build_store_from_env() -> Any:
    from api.platform.storage.postgres import PostgresTimeSeriesStore

    database_url = os.getenv("FINMIND_DATABASE_URL") or os.getenv(
        "DATABASE_URL"
    )
    if not database_url:
        raise RuntimeError(
            "FINMIND_DATABASE_URL (or DATABASE_URL) must be set to run "
            "the VN100 seed loader."
        )
    return PostgresTimeSeriesStore(database_url=database_url)


def _default_csv_path() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "data"
        / "seed"
        / "vn100.csv"
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    csv_path = Path(args[0]) if args else _default_csv_path()
    if not csv_path.exists():
        logger.error("vn100_seed.missing_csv path=%s", csv_path)
        return 1
    store = _build_store_from_env()
    result = load_vn100_seed(csv_path, store)
    print(  # noqa: T201 - operator script output
        "VN100 seed loaded: "
        f"instruments={result.instruments_upserted} "
        f"memberships={result.memberships_upserted}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
