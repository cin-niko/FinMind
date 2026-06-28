from finmind_agents.models import Artifact, CanonicalMarketDataRecord, Citation


def build_chart_artifact(
    workflow_id: str,
    records: list[CanonicalMarketDataRecord],
    citations: list[Citation],
) -> Artifact:
    return Artifact(
        artifact_id=f"artifact_{workflow_id}_{records[0].dataset_id}",
        artifact_type="chart",
        title="Market price snapshot",
        inputs={
            "dataset_id": records[0].dataset_id,
            "records": [record.record_key for record in records],
        },
        payload={
            "series": [
                {
                    "time": record.market_time.isoformat(),
                    "value": record.payload["close"],
                    "change_percent": record.payload.get("change_percent"),
                }
                for record in records
            ],
            "table": [
                {
                    "record_key": record.record_key,
                    "market_time": record.market_time.isoformat(),
                    "close": record.payload["close"],
                }
                for record in records
            ],
        },
        source_refs=tuple(citation.citation_id for citation in citations),
    )
