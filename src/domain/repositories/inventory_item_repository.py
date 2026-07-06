"""InventoryItemRepository interface.

Describes the persistence operations the domain needs for inventory items,
without committing to any particular database or ORM. Implementations live
in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.inventory_item import InventoryItem


class InventoryItemRepository(ABC):
    """Abstraction over inventory item persistence."""

    @abstractmethod
    async def add(self, item: InventoryItem) -> None:
        """Persist a new inventory item."""

    @abstractmethod
    async def get_by_id(self, item_id: str) -> InventoryItem | None:
        """Return the item with the given id, or None if it does not exist."""

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[InventoryItem]:
        """Return all inventory items belonging to the given user."""

    @abstractmethod
    async def update(self, item: InventoryItem) -> None:
        """Persist changes to an existing inventory item."""

    @abstractmethod
    async def delete(self, item_id: str) -> None:
        """Remove an inventory item by id."""
