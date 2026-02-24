from typing import List

from app.models.item import Item, ItemCreate


class ItemService:
    def __init__(self) -> None:
        self._items: list[Item] = []
        self._next_id = 1

    def list_items(self) -> List[Item]:
        return self._items

    def create_item(self, item_in: ItemCreate) -> Item:
        item = Item(id=self._next_id, name=item_in.name)
        self._items.append(item)
        self._next_id += 1
        return item
