from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class IngestionFetchRequest:
    source_id: str
    mode: str = "period"
    period: str | None = None
    from_date: str | None = None
    to_date: str | None = None
    instrument_id: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, str]) -> "IngestionFetchRequest":
        mode = payload.get("mode") or ("period" if payload.get("period") else "latest")
        return cls(
            source_id=payload["source_id"],
            mode=mode,
            period=payload.get("period"),
            from_date=payload.get("from_date"),
            to_date=payload.get("to_date"),
        )

    def period_scope(self, periods: list[str]) -> str:
        if self.mode == "historical":
            base = f"{periods[0]}:{periods[-1]}"
        else:
            base = periods[0]
        if self.instrument_id:
            return f"{self.instrument_id}:{base}"
        return base


def plan_fetch_periods(request: IngestionFetchRequest, now: datetime) -> list[str]:
    if request.mode == "latest":
        return [now.date().isoformat()]
    if request.mode == "period":
        if not request.period:
            raise ValueError("period mode requires period")
        return [request.period]
    if request.mode == "historical":
        if not request.from_date or not request.to_date:
            raise ValueError("historical mode requires from_date and to_date")
        start = datetime.fromisoformat(request.from_date).date()
        end = datetime.fromisoformat(request.to_date).date()
        if end < start:
            raise ValueError("to_date must be on or after from_date")
        periods: list[str] = []
        cursor = start
        while cursor <= end:
            periods.append(cursor.isoformat())
            cursor += timedelta(days=1)
        return periods
    raise ValueError(f"Unsupported fetch mode: {request.mode}")
