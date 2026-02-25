import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import users as users_api
from app.main import create_app
from app.services.user_service import UserService


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    service = UserService()
    app.dependency_overrides[users_api.get_user_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_users(client: TestClient) -> None:
    create_response = client.post("/api/v1/users/", json={"name": "Alice"})
    assert create_response.status_code == 201
    assert create_response.json() == {"id": 1, "name": "Alice"}

    list_response = client.get("/api/v1/users/")
    assert list_response.status_code == 200
    assert list_response.json() == [{"id": 1, "name": "Alice"}]


def test_call_webapp2_returns_payload(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __init__(self, data: list[dict[str, object]]) -> None:
            self._data = data

        def raise_for_status(self) -> None:
            return None

        def json(self) -> list[dict[str, object]]:
            return self._data

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            captured["follow_redirects"] = kwargs.get("follow_redirects")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str) -> FakeResponse:
            captured["url"] = url
            return FakeResponse([{"id": 1, "name": "Item 1"}])

    monkeypatch.setattr(users_api.httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/api/v1/users/call-webapp2")
    assert response.status_code == 200
    assert response.json() == {
        "from": "webapp1",
        "webapp2_response": [{"id": 1, "name": "Item 1"}],
    }
    assert captured["follow_redirects"] is True
    assert captured["url"] == "http://webapp2.default.svc.cluster.local/api/v1/items/"
