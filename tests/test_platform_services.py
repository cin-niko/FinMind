from datetime import UTC, datetime

import httpx

from finmind_agents.data_records import build_data_record
from finmind_agents.dataflows.models import DataRequirement, DataflowCollectionRequest, DatasetGroup
from finmind_agents.dataflows.providers.gold import GoldPriceProvider
from finmind_agents.dataflows.providers.gold import GoldProviderPermanentError
from finmind_agents.dataflows.service import DataflowService
from finmind_agents.dataflows.registry import (
    DataflowProviderRegistry,
    build_default_provider_registry,
)
from finmind_agents.memory import InMemoryConversationRepository
from finmind_agents.models import CanonicalMarketDataRecord, Conversation, ConversationStatus, Market, utc_now
from finmind_agents.agents.validators import AgentValidationError, validate_response_language
from finmind_agents.runtime.service import answer_system_prompt
from finmind_agents.conversations import _localized_failure_message
import pytest


def test_none_is_unavailable_in_prompt_context() -> None:
    record = CanonicalMarketDataRecord(
        dataset_id="gold_prices", record_key="XAUUSD-prices", instrument_id="XAUUSD",
        market_time=datetime(2026, 6, 18, tzinfo=UTC), collected_at=datetime(2026, 6, 18, 8, tzinfo=UTC),
        source_id="fixture", payload={"series": [{"date": "2026-06-18", "close": 2345.0, "volume": None}]},
    )
    prompt = build_data_record(record).to_prompt_record()
    assert prompt["fields"]["series"][0]["volume"] == "Unavailable"


def test_gold_provider_retries_twice_after_initial_failure() -> None:
    attempts = 0
    def fetcher() -> list[dict[str, object]]:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("temporary")
        return [{"date": "2026-06-18", "close": 2345.0}]
    service = DataflowService(DataflowProviderRegistry((GoldPriceProvider(fetcher),)))
    result = service.collect(DataflowCollectionRequest(market=Market.GOLD, symbol="XAUUSD", requested_by="test", dataset_groups=(DatasetGroup.MARKET_PRICE,)))
    assert attempts == 3
    assert result.status.value == "success"
    assert result.records[0].payload["interval"] == "1D"


def test_gold_provider_does_not_retry_permanent_failure() -> None:
    attempts = 0

    def fetcher() -> list[dict[str, object]]:
        nonlocal attempts
        attempts += 1
        raise GoldProviderPermanentError("invalid credential")

    service = DataflowService(DataflowProviderRegistry((GoldPriceProvider(fetcher),)))
    result = service.collect(
        DataflowCollectionRequest(
            market=Market.GOLD,
            symbol="XAUUSD",
            requested_by="test",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
        )
    )

    assert attempts == 1
    assert result.status.value == "failed"
    assert result.failure_reasons == ("gold_provider_request_rejected",)


def test_gold_provider_normalizes_twelve_data_numeric_strings() -> None:
    provider = GoldPriceProvider(
        lambda: [
            {
                "datetime": "2026-06-18",
                "open": "2330.5",
                "high": "2350.0",
                "low": "2325.25",
                "close": "2345.75",
            }
        ]
    )
    result = provider.fetch(
        DataflowCollectionRequest(
            market=Market.GOLD,
            symbol="XAUUSD",
            requested_by="test",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
        )
    )

    row = result.records[0].payload["series"][0]
    assert row["open"] == 2330.5
    assert row["close"] == 2345.75


def test_gold_provider_rejects_non_daily_requirement_without_fetching() -> None:
    called = False

    def fetcher() -> list[dict[str, object]]:
        nonlocal called
        called = True
        return []

    provider = GoldPriceProvider(fetcher)
    result = provider.fetch(
        DataflowCollectionRequest(
            market=Market.GOLD,
            symbol="XAUUSD",
            requested_by="test",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
            data_requirements=(
                DataRequirement("price_history", {"interval": "1h"}),
            ),
        )
    )

    assert called is False
    assert result.provider_result.failure_reason == "gold_request_not_supported"


def test_default_gold_registry_calls_twelve_data_daily_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> httpx.Response:
        captured.update({"url": url, "params": params, "timeout": timeout})
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(
            200,
            request=request,
            json={
                "values": [
                    {
                        "datetime": "2026-06-18",
                        "open": "2330",
                        "high": "2350",
                        "low": "2325",
                        "close": "2345",
                    }
                ]
            },
        )

    monkeypatch.setattr(
        "finmind_agents.dataflows.providers.gold.httpx.get",
        fake_get,
    )
    registry = build_default_provider_registry(
        vn_data_provider="disabled",
        gold_data_provider="twelvedata",
        twelve_data_api_key="test-key",
        provider_timeout_seconds=7.0,
    )
    service = DataflowService(registry)
    result = service.collect(
        DataflowCollectionRequest(
            market=Market.GOLD,
            symbol="XAUUSD",
            requested_by="test",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
        )
    )

    assert result.status.value == "success"
    assert captured["url"] == "https://api.twelvedata.com/time_series"
    assert captured["timeout"] == 7.0
    assert captured["params"] == {
        "symbol": "XAU/USD",
        "interval": "1day",
        "outputsize": 5000,
        "format": "JSON",
        "apikey": "test-key",
    }


def test_interrupted_conversations_are_failed_on_reconciliation() -> None:
    repository = InMemoryConversationRepository()
    now = utc_now()
    repository.save_conversation(Conversation("conv_test", "analyst", ConversationStatus.RUNNING, "Test", "workflow", {}, "en", now, now))
    assert repository.reconcile_interrupted() == 1
    restored = repository.get_conversation("conv_test", "analyst")
    assert restored is not None and restored.status is ConversationStatus.FAILED


def test_conversation_repository_owner_filters_and_blocks_active_delete() -> None:
    repository = InMemoryConversationRepository()
    now = utc_now()
    active = Conversation("conv_active", "analyst", ConversationStatus.RUNNING, "Active", "workflow", {}, "en", now, now)
    other = Conversation("conv_other", "other", ConversationStatus.SUCCESS, "Other", "workflow", {}, "en", now, now)
    repository.save_conversation(active)
    repository.save_conversation(other)
    assert repository.list_conversations("analyst") == [active]
    assert repository.get_conversation("conv_other", "analyst") is None
    assert repository.delete_conversation("conv_active", "analyst") is False


def test_workflow_response_language_is_enforced() -> None:
    assert "Vietnamese language" in answer_system_prompt("vi")
    assert "English language" in answer_system_prompt("en")
    assert "do not translate that evidence" in answer_system_prompt("vi")
    assert "120 giây" in _localized_failure_message("vi", "timeout")
    assert _localized_failure_message("fr", "failed").startswith("Workflow")
    validate_response_language("Dữ liệu tài chính hiện không khả dụng.", "vi")
    validate_response_language("Financial evidence is currently unavailable.", "en")
    with pytest.raises(AgentValidationError, match="Vietnamese"):
        validate_response_language("Financial evidence is currently unavailable.", "vi")
    with pytest.raises(AgentValidationError, match="English"):
        validate_response_language("Dữ liệu tài chính hiện không khả dụng.", "en")
