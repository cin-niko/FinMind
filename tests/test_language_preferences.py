from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from finmind_api.app import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_language_preference_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/preferences/language").status_code == 401


def test_language_preference_defaults_updates_and_rejects_invalid_values(
    client: TestClient,
) -> None:
    login = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login.status_code == 200

    assert client.get("/api/preferences/language").json() == {"selection": "auto"}
    assert client.put(
        "/api/preferences/language",
        json={"selection": "vi"},
    ).json() == {"selection": "vi"}
    assert client.get("/api/preferences/language").json() == {"selection": "vi"}
    assert client.put(
        "/api/preferences/language",
        json={"selection": "fr"},
    ).status_code == 422
    assert client.get("/api/preferences/language").json() == {"selection": "vi"}
