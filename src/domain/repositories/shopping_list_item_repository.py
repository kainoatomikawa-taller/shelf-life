"""ShoppingListItemRepository interface.

Describes the persistence operations the domain needs, without committing to
any particular database or ORM. Implementations live in the infrastructure
layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.shopping_list_item import ShoppingListItem


class ShoppingListItemRepository(ABC):
    """Abstraction over shopping list item persistence."""

    @abstractmethod
    async def add(self, item: ShoppingListItem) -> None:
        """Persist a new shopping list item."""

    @abstractmethod
    async def get_by_id(self, item_id: str) -> ShoppingListItem | None:
        """Return the item with the given id, or None if it does not exist."""

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[ShoppingListItem]:
        """Return every shopping list item belonging to the given user."""

    @abstractmethod
    async def update(self, item: ShoppingListItem) -> None:
        """Persist changes to an existing shopping list item."""

    @abstractmethod
    async def remove(self, item_id: str) -> None:
        """Remove a shopping list item by id."""
