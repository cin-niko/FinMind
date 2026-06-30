from finmind_agents.models import Artifact, CanonicalMarketDataRecord, Citation


def build_chart_artifact(
    workflow_id: str,
    records: list[CanonicalMarketDataRecord],
    citations: list[Citation],
) -> Artifact:
    price_record = next(
        (r for r in records if r.dataset_id.endswith("_prices")),
        None,
    )
    if price_record is None or not price_record.payload.get("series"):
        return Artifact(
            artifact_id=f"artifact_{workflow_id}_vn_prices",
            artifact_type="chart",
            title="Market price snapshot",
            inputs={"dataset_id": "vn_prices"},
            payload={"series": [], "table": []},
            source_refs=tuple(citation.citation_id for citation in citations),
        )
    series = price_record.payload["series"]
    return Artifact(
        artifact_id=f"artifact_{workflow_id}_{price_record.dataset_id}",
        artifact_type="chart",
        title="Market price snapshot",
        inputs={
            "dataset_id": price_record.dataset_id,
            "record_key": price_record.record_key,
        },
        payload={
            "series": [
                {
                    "time": bar["date"],
                    "value": bar["close"],
                    "change_percent": bar.get("change_percent"),
                }
                for bar in series
            ],
            "table": [
                {
                    "date": bar["date"],
                    "close": bar["close"],
                    "volume": bar.get("volume"),
                }
                for bar in series
            ],
        },
        source_refs=tuple(citation.citation_id for citation in citations),
    )
