"""In-memory InventoryItemRepository for fast, isolated use case tests."""

from __future__ import annotations

from src.domain.entities.inventory_item import InventoryItem
from src.domain.repositories.inventory_item_repository import InventoryItemRepository


class InMemoryInventoryItemRepository(InventoryItemRepository):
    def __init__(self) -> None:
        self._items: dict[str, InventoryItem] = {}

    async def add(self, item: InventoryItem) -> None:
        self._items[item.id] = item

    async def get_by_id(self, item_id: str) -> InventoryItem | None:
        return self._items.get(item_id)

    async def list_by_user(self, user_id: str) -> list[InventoryItem]:
        return [i for i in self._items.values() if i.user_id == user_id]

    async def update(self, item: InventoryItem) -> None:
        self._items[item.id] = item

    async def delete(self, item_id: str) -> None:
        self._items.pop(item_id, None)
