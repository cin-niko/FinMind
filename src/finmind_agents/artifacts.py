from collections.abc import Callable
from uuid import uuid4

from finmind_agents.models import (
    Artifact,
    CanonicalMarketDataRecord,
    ChartRequirement,
    Citation,
)


ChartBuilder = Callable[
    [str, ChartRequirement, list[CanonicalMarketDataRecord], list[Citation]],
    Artifact,
]


def build_chart_artifacts(
    workflow_id: str,
    requirements: tuple[ChartRequirement, ...],
    records: list[CanonicalMarketDataRecord],
    citations: list[Citation],
) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for requirement in requirements:
        builder = CHART_BUILDERS.get(requirement.chart_id)
        if builder is None:
            if requirement.required:
                artifacts.append(
                    _unavailable_chart(
                        workflow_id,
                        requirement,
                        "unsupported_chart_requirement",
                    )
                )
            continue
        artifacts.append(builder(workflow_id, requirement, records, citations))
    return artifacts


def build_price_trend_chart(
    workflow_id: str,
    requirement: ChartRequirement,
    records: list[CanonicalMarketDataRecord],
    citations: list[Citation],
) -> Artifact:
    price_record = next(
        (r for r in records if r.dataset_id.endswith("_prices")),
        None,
    )
    if price_record is None or not price_record.payload.get("series"):
        return _unavailable_chart(workflow_id, requirement, "missing_price_series")
    series = price_record.payload["series"]
    artifact_id = _artifact_id()
    candles = [
        {
            "date": bar["date"],
            "open": _price_value(bar.get("open"), bar["close"]),
            "high": _price_value(bar.get("high"), bar["close"]),
            "low": _price_value(bar.get("low"), bar["close"]),
            "close": bar["close"],
            "volume": bar.get("volume"),
        }
        for bar in series
    ]
    return Artifact(
        artifact_id=artifact_id,
        artifact_type="chart",
        chart_intent=requirement.chart_id,
        title=requirement.title,
        inputs={
            "dataset_id": price_record.dataset_id,
            "record_key": price_record.record_key,
        },
        spec={
            "supported_views": ["line", "candlestick"],
            "default_view": "line",
            "x_axis": {"field": "date", "type": "time"},
            "series": [
                {
                    "name": "Close",
                    "type": "line",
                    "data": [
                        {
                            "date": bar["date"],
                            "value": bar["close"],
                            "change_percent": bar.get("change_percent"),
                        }
                        for bar in series
                    ],
                }
            ],
            "candles": candles,
        },
        source_refs=tuple(citation.citation_id for citation in citations),
        downloads=_chart_downloads(
            artifact_id,
            _filename_prefix(price_record.record_key, requirement.title),
        ),
    )


def _unavailable_chart(
    workflow_id: str,
    requirement: ChartRequirement,
    reason: str,
) -> Artifact:
    artifact_id = _artifact_id()
    return Artifact(
        artifact_id=artifact_id,
        artifact_type="chart",
        chart_intent=requirement.chart_id,
        title=requirement.title,
        inputs={},
        spec={
            "supported_views": ["line"],
            "default_view": "line",
            "x_axis": {"field": "date", "type": "time"},
            "series": [],
            "candles": [],
        },
        source_refs=(),
        downloads=(),
        status="unavailable",
        reason=reason,
    )


def _artifact_id() -> str:
    return f"art_{uuid4().hex}"


def _price_value(value: object, fallback: object) -> object:
    return fallback if value is None else value


def _chart_downloads(artifact_id: str, filename_prefix: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "format": "svg",
            "url": f"/api/artifacts/{artifact_id}/download?format=svg",
            "filename": f"{filename_prefix}.svg",
            "mime_type": "image/svg+xml",
        },
        {
            "format": "csv",
            "url": f"/api/artifacts/{artifact_id}/download?format=csv",
            "filename": f"{filename_prefix}.csv",
            "mime_type": "text/csv",
        },
    )


def _filename_prefix(record_key: str, title: str) -> str:
    symbol = record_key.split("-", 1)[0].lower() if record_key else title.lower()
    return f"{symbol}-price-series"


CHART_BUILDERS: dict[str, ChartBuilder] = {
    "price_trend": build_price_trend_chart,
    "gold_price_trend": build_price_trend_chart,
}
