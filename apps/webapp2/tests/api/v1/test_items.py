import pytest
from fastapi.testclient import TestClient

from app.api.v1 import items as items_api
from app.main import create_app
from app.services.item_service import ItemService


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    service = ItemService()
    app.dependency_overrides[items_api.get_item_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_items(client: TestClient) -> None:
    create_response = client.post("/api/v1/items/", json={"name": "Keyboard"})
    assert create_response.status_code == 201
    assert create_response.json() == {"id": 1, "name": "Keyboard"}

    list_response = client.get("/api/v1/items/")
    assert list_response.status_code == 200
    assert list_response.json() == [{"id": 1, "name": "Keyboard"}]


def test_call_webapp1_returns_payload(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
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
            return FakeResponse([{"id": 1, "name": "Alice"}])

    monkeypatch.setattr(items_api.httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/api/v1/items/call-webapp1")
    assert response.status_code == 200
    assert response.json() == {
        "from": "webapp2",
        "webapp1_response": [{"id": 1, "name": "Alice"}],
    }
    assert captured["follow_redirects"] is True
    assert captured["url"] == "http://webapp1.default.svc.cluster.local/api/v1/users/"
