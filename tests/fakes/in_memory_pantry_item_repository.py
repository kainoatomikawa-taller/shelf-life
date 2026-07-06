"""In-memory PantryItemRepository for fast, isolated use case tests.

Demonstrates that use cases depend only on the domain interface, not on any
concrete database.
"""

from __future__ import annotations

from src.domain.entities.pantry_item import PantryItem
from src.domain.repositories.pantry_item_repository import PantryItemRepository


class InMemoryPantryItemRepository(PantryItemRepository):
    def __init__(self) -> None:
        self._items: dict[str, PantryItem] = {}

    async def add(self, item: PantryItem) -> None:
        self._items[item.id] = item

    async def get_by_id(self, item_id: str) -> PantryItem | None:
        return self._items.get(item_id)

    async def list_by_owner(self, owner_id: str) -> list[PantryItem]:
        return [i for i in self._items.values() if i.owner_id == owner_id]

    async def update(self, item: PantryItem) -> None:
        self._items[item.id] = item

    async def delete(self, item_id: str) -> None:
        self._items.pop(item_id, None)
