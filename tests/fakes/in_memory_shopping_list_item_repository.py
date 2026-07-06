"""In-memory ShoppingListItemRepository for fast, isolated use case tests."""

from __future__ import annotations

from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)


class InMemoryShoppingListItemRepository(ShoppingListItemRepository):
    def __init__(self) -> None:
        self._items: dict[str, ShoppingListItem] = {}

    async def add(self, item: ShoppingListItem) -> None:
        self._items[item.id] = item

    async def get_by_id(self, item_id: str) -> ShoppingListItem | None:
        return self._items.get(item_id)

    async def list_by_user(self, user_id: str) -> list[ShoppingListItem]:
        return [i for i in self._items.values() if i.user_id == user_id]

    async def update(self, item: ShoppingListItem) -> None:
        self._items[item.id] = item

    async def remove(self, item_id: str) -> None:
        self._items.pop(item_id, None)
