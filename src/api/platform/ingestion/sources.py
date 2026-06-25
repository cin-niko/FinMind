from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class TimeSeriesRecord:
    dataset_id: str
    record_key: str
    instrument_id: str
    market_time: datetime
    collected_at: datetime
    source_id: str
    payload: dict[str, object]


class MarketDataSource(Protocol):
    source_id: str

    def fetch(self, period: str) -> list[TimeSeriesRecord]: ...
