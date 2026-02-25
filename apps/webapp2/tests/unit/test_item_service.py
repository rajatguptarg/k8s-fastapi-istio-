from app.models.item import ItemCreate
from app.services.item_service import ItemService


def test_create_item_assigns_incrementing_ids() -> None:
    service = ItemService()

    first = service.create_item(ItemCreate(name="Keyboard"))
    second = service.create_item(ItemCreate(name="Mouse"))

    assert first.id == 1
    assert first.name == "Keyboard"
    assert second.id == 2
    assert second.name == "Mouse"


def test_list_items_returns_created_items_in_order() -> None:
    service = ItemService()
    service.create_item(ItemCreate(name="Keyboard"))
    service.create_item(ItemCreate(name="Mouse"))

    items = service.list_items()
    assert [item.model_dump() for item in items] == [
        {"id": 1, "name": "Keyboard"},
        {"id": 2, "name": "Mouse"},
    ]
